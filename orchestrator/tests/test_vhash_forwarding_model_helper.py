"""Helper forwarding checks against the actual transition and judgment code."""
from __future__ import annotations

import sys
import traceback
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from time import monotonic

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from vhash_forwarding_model.model import (State, Step, Txn, Version, changed_step_in_trace,
                                          enabled_steps, explore, replay)  # noqa: E402
from vhash_forwarding_model.scenarios import scenario, danger_witness  # noqa: E402
from vhash_forwarding_model.judge import _committed, j3, judge  # noqa: E402
from vhash_forwarding_model.helper import HelperState  # noqa: E402
from vhash_forwarding_model.gc_connection import reclaimable_versions, effect_snapshot  # noqa: E402

_SEARCHES = []


def _history(before, after, step):
    old = next(t for t in before.txns if t.id == "T")
    new = next(t for t in after.txns if t.id == "T")
    if step.thread == "T":
        assert new.pc >= old.pc
        if old.phase == "ops" and old.pc < len(old.ops) and old.ops[old.pc] == ("WAIT", ""):
            assert step.operation in ("end_wait", "end_wait_revert")
            assert new.pc == old.pc + 1


@lru_cache(None)
def _search(name, fault="", resume="accept", revert=False):
    initial, window = scenario(name)
    result = explore(initial, fault=fault, witness=window, danger=danger_witness(name),
                     pressure="helper", resume=resume, revert_after_confirm=revert,
                     collect_effects=not bool(fault) and name in ("H1", "H4"),
                     state_invariant=_sound if not fault else None,
                     transition_invariant=_history if name == "H1" and not fault else None)
    _SEARCHES.append((name, fault, resume, revert, result["statistics"]))
    assert result["statistics"]["complete"], (name, fault, result["statistics"])
    return initial, result


def _sound(state):
    assert all(t.gc_floor <= t.cand_ts for t in state.txns if not t.expired)


def test_representative_old_pins():
    for name, pressure, expected in (("S3", "off", 180), ("S7", "off", 1720),
                                     ("G1", "off", 330), ("G1", "self", 1444),
                                     ("G4", "self", 524)):
        initial, window = scenario(name)
        result = explore(initial, witness=window, pressure=pressure)
        assert result["statistics"]["visited"] == expected
        assert result["statistics"]["complete"] and not result["counterexample"]


def test_helper_sound_and_effect_h1():
    initial, result = _search("H1", revert=True)
    assert result["witness"]["reached"] and not result["counterexample"]
    assert result["floor_above_cand_states"] == 0
    assert result["effects"]["attributable"]["delta_B"] > 0
    assert result["effects"]["attributable"]["delta_freed"] > 0
    reached = replay(initial, result["witness"]["steps"], pressure="helper",
                     revert_after_confirm=True)
    _sound(reached)


def test_h2_cas_faults_and_replay():
    for fault, revert, unsafe in (("UH1", False, True), ("UH1g", False, False),
                                  ("UH1p", False, False), ("UH1p", True, True),
                                  ("UH4", False, True)):
        initial, result = _search("H2", fault, revert=revert)
        assert result["witness"]["reached"]
        assert result["fault_step_seen"] == (fault != "UH1g")
        assert bool(result["counterexample"]) == unsafe, fault
        if unsafe:
            ce = result["counterexample"]
            assert ce["judge"] == "J3" and changed_step_in_trace(ce["steps"], fault)
            before = replay(initial, ce["steps"][:-1], fault=fault, pressure="helper",
                            revert_after_confirm=revert)
            after = replay(initial, ce["steps"], fault=fault, pressure="helper",
                           revert_after_confirm=revert)
            assert judge(before, after, ce["steps"][-1])["J3"] == ce["reason"]


def test_h2_refs_release_fault_reaches_window_without_violation():
    _, result = _search("H2", "UH3F")
    assert result["witness"]["reached"] and result["fault_step_seen"]
    assert not result["counterexample"] and result["floor_above_cand_states"] == 0


def test_h3_early_publish_replay():
    initial, window = scenario("H3")
    result = explore(initial, fault="UH2", witness=window, danger=danger_witness("H3"),
                     pressure="helper", max_states=5000, collect_effects=False)
    _SEARCHES.append(("H3", "UH2", "accept", False, result["statistics"]))
    assert not result["statistics"]["complete"]
    assert result["witness"]["reached"] and result["danger"]["reached"]
    ce = result["counterexample"]
    assert ce and ce["judge"] == "J3" and changed_step_in_trace(ce["steps"], "UH2")
    before = replay(initial, ce["steps"][:-1], fault="UH2", pressure="helper")
    after = replay(initial, ce["steps"], fault="UH2", pressure="helper")
    assert j3(before, after, ce["steps"][-1]) == ce["reason"]


def test_h4_expired_refs_and_skip_check():
    for fault in ("UH3X", "UH5"):
        initial, result = _search("H4", fault, resume="expire")
        assert result["witness"]["reached"] and result["danger"]["reached"]
        ce = result["counterexample"]
        assert ce and ce["reason"]["reason"] == "use_after_free"
        assert changed_step_in_trace(ce["steps"], fault)
        before = replay(initial, ce["steps"][:-1], fault=fault, pressure="helper", resume="expire")
        after = replay(initial, ce["steps"], fault=fault, pressure="helper", resume="expire")
        assert j3(before, after, ce["steps"][-1]) == ce["reason"]
        if fault == "UH3X":
            end = next(i for i, step in enumerate(ce["steps"]) if step.thread == "T"
                       and step.operation == "end_wait")
            resumed = replay(initial, ce["steps"][:end + 1], fault=fault,
                             pressure="helper", resume="expire")
            checked, check = next((n, x) for n, x in enabled_steps(
                resumed, faults=frozenset((fault,)), pressure="helper", resume="expire")
                if x.thread == "T" and x.operation == "check_expired")
            aborted, decision = next((n, x) for n, x in enabled_steps(
                checked, faults=frozenset((fault,)), pressure="helper", resume="expire")
                if x.thread == "T" and x.operation == "decide_aborted")
            assert j3(resumed, checked, check) is None
            assert j3(checked, aborted, decision) is None
            assert next(t for t in aborted.txns if t.id == "T").phase == "release"


def test_expired_j3_keeps_only_refs_reason():
    versions = (Version("A20", "A", 20, 20), Version("A50", "A", 50, 50))
    t = Txn("T", 45, (("R", "A"),), expired=True, read_log=(("A", "A20"),))
    before = State(versions, (t,))
    after = replace(before, versions=(replace(versions[0], reclaimed=True), versions[1]))
    step = Step("GC", "reclaim", "A20")
    assert j3(before, after, step) is None
    assert j3(replace(before, txns=(replace(t, refs=("A20",)),)), after, step)["reason"] == "reference"
    assert j3(replace(before, txns=(replace(t, expired=False),)), after, step)["reason"] == "read_log"
    future = replace(t, pc=0, read_log=())
    assert j3(replace(before, txns=(future,)), after, step) is None
    assert j3(replace(before, txns=(replace(future, expired=False),)), after, step)["reason"] == "future_read"


def test_wait_own_step_and_generation():
    initial, _ = scenario("H1")
    t_read = next(n for n, x in enabled_steps(initial, pressure="helper") if x.thread == "T")
    t = t_read.txns[0]
    assert t.pc == 1
    own = [(n, x) for n, x in enabled_steps(t_read, pressure="helper") if x.thread == "T"]
    assert [x.operation for _, x in own] == ["end_wait"]
    assert own[0][0].txns[0].gen == t.gen + 1
    assert t.phase == "ops" and t.ops[t.pc] == ("WAIT", "")
    expired, step = next((n, x) for n, x in enabled_steps(
        t_read, pressure="helper", resume="expire") if x.operation == "h_expire")
    assert expired.txns[0].gen == t.gen + 1 and step.fault == ""


def test_state_hash_distinguishes_helper_and_generation():
    initial, _ = scenario("H1")
    t = initial.txns[0]
    advanced = replace(initial, txns=(replace(t, gen=1), *initial.txns[1:]))
    assert initial != advanced and len({initial, advanced}) == 2
    snapshot = next(n for n, x in enabled_steps(
        next(n for n, x in enabled_steps(initial, pressure="helper") if x.thread == "T"),
        pressure="helper") if x.operation == "h_snapshot")
    assert snapshot.helper.phase == "rts" and snapshot != initial


def test_expire_effect_and_sound():
    _, accept = _search("H4")
    assert not accept["counterexample"] and accept["effects"]["attributable"] is None
    off = explore(scenario("H4")[0], pressure="self")
    assert off["effects"]["attributable"] is None
    initial, result = _search("H4", resume="expire")
    assert result["witness"]["reached"] and not result["counterexample"]
    assert result["floor_above_cand_states"] == 0
    assert result["effects"]["attributable"]["delta_B"] > 0
    _sound(replay(initial, result["witness"]["steps"], pressure="helper", resume="expire"))


def test_expired_decision_is_not_committed():
    initial = State((Version("A20", "A", 20, 20),
                     Version("T:A", "A", 45, 45, "PENDING", "T")),
                    (Txn("T", 45, (("W", "A"),), phase="decision", pending=("T:A",),
                         expired=True),))
    decided, step = next((state, step) for state, step in enabled_steps(
        initial, pressure="helper", faults=frozenset(("UH5",)))
        if step.thread == "T")
    assert step.operation == "decide_aborted"
    assert decided.txns[0].failed and "T" not in _committed(decided)
    assert next(v for v in decided.versions if v.id == "T:A").status == "ABORTED"


def test_h5_danger_write_skew_cycle():
    versions = (Version("A10", "A", 10, 10), Version("B11", "B", 11, 11),
                Version("W:A", "A", 20, 20, owner="W"),
                Version("T:B", "B", 15, 15, owner="T"))
    t = Txn("T", 15, (), phase="done", read_log=(("A", "A10"),))
    w = Txn("W", 20, (), phase="done", read_log=(("B", "B11"),))
    state = State(versions, (t, w))
    danger = danger_witness("H5")
    step = Step("W", "decide_committed", "W:A")
    assert danger(state, state, step)
    assert not danger(state, replace(state, versions=versions[:2] + versions[3:]), step)
    assert not danger(state, replace(state, versions=versions[:3]), step)


def test_healthy_h2_h3_complete():
    for name in ("H2", "H3"):
        _, result = _search(name)
        assert result["witness"]["reached"] and not result["danger"]["reached"]
        assert not any(result["verdicts"].values())
        assert result["floor_above_cand_states"] == 0
    initial, window = scenario("H3")
    for pressure, resume in (("off", "accept"), ("self", "accept")):
        result = explore(initial, witness=window, danger=danger_witness("H3"),
                         pressure=pressure, resume=resume, collect_effects=False)
        _SEARCHES.append(("H3", "", resume + ":" + pressure, False, result["statistics"]))
        assert result["statistics"]["complete"]
        assert not result["danger"]["reached"] and not any(result["verdicts"].values())


def test_wait_history_and_healthy_floor():
    for name, kwargs in (("H1", {"revert": True}), ("H2", {}),
                         ("H4", {}), ("H4", {"resume": "expire"})):
        _, result = _search(name, **kwargs)
        assert result["statistics"]["complete"] and not any(result["verdicts"].values())


def test_helper_refs_and_uh6_replay():
    initial, healthy = _search("H4")
    assert not any(healthy["verdicts"].values())
    _, expired = _search("H4", resume="expire")
    assert not any(expired["verdicts"].values())
    h1, _ = scenario("H1")
    read = next(n for n, x in enabled_steps(h1, pressure="helper") if x.thread == "T")
    snapshot = next(n for n, x in enabled_steps(read, pressure="helper")
                    if x.operation == "h_snapshot")
    assert snapshot.helper.refs == ("A20",)
    assert next(n for n, x in enabled_steps(snapshot, pressure="helper")
                if x.operation == "h_rts").helper.refs == ("A20",)
    state = snapshot
    for operation in ("end_wait", "h_rts", "h_pass", "h_check", "h_pass", "h_commit_fail"):
        state = next(n for n, x in enabled_steps(state, pressure="helper")
                     if x.operation == operation)
    assert state.helper.phase == "idle" and not state.helper.refs
    initial, unsafe = _search("H4", "UH6")
    ce = unsafe["counterexample"]
    assert ce and ce["judge"] == "J3" and ce["reason"]["reason"] == "use_after_free"
    assert changed_step_in_trace(ce["steps"], "UH6")
    before = replay(initial, ce["steps"][:-1], pressure="helper", fault="UH6")
    after = replay(initial, ce["steps"], pressure="helper", fault="UH6")
    assert j3(before, after, ce["steps"][-1]) == ce["reason"]


def test_helper_reclaimed_contacts_and_reference_reason():
    versions = (Version("A20", "A", 20, 20, reclaimed=True),)
    t = Txn("T", 45, (("R", "A"), ("WAIT", "")), pc=1,
            read_log=(("A", "A20"),))
    for phase in ("rts", "check"):
        state = State(versions, (t,), helper=HelperState(
            phase, "T", 0, 61, t.read_log))
        after, step = next((n, x) for n, x in enabled_steps(state, pressure="helper")
                           if x.thread == "H" and x.operation == "touch_reclaimed")
        assert after == state and step.version == "A20"
        assert j3(state, after, step)["reason"] == "use_after_free"
    selected = State((replace(versions[0], reclaimed=False),
                      Version("A50", "A", 50, 50, reclaimed=True)), (t,),
                     helper=HelperState("check", "T", 0, 61, t.read_log))
    after, step = next((n, x) for n, x in enabled_steps(selected, pressure="helper")
                       if x.thread == "H" and x.operation == "touch_reclaimed")
    assert after == selected and step.version == "A50"
    before = State((replace(versions[0], reclaimed=False),), (t,),
                   helper=HelperState(refs=("A20",)))
    after = replace(before, versions=versions)
    assert j3(before, after, Step("GC", "reclaim", "A20"))["txn"] == "H"
    protected = replace(before, versions=(before.versions[0], Version("A50", "A", 50, 50)),
                        txns=(replace(t, expired=True),))
    unprotected = replace(protected, helper=HelperState())
    assert "A20" not in reclaimable_versions(protected)
    assert "A20" in reclaimable_versions(unprotected)
    assert effect_snapshot(protected)["freed"] + 1 == effect_snapshot(unprotected)["freed"]


if __name__ == "__main__":
    failures = 0
    for name in sorted(name for name, value in globals().items()
                       if name.startswith("test_") and callable(value)):
        began = monotonic()
        try:
            globals()[name]()
        except Exception:
            failures += 1
            print(f"FAIL {name}", flush=True)
            traceback.print_exc()
        else:
            print(f"PASS {name} {monotonic() - began:.3f}s", flush=True)
    for name, fault, resume, revert, stats in _SEARCHES:
        print(f"SEARCH {name} {fault or '-'} {resume} revert={revert} "
              f"visited={stats['visited']} complete={stats['complete']} "
              f"seconds={stats['seconds']:.3f}", flush=True)
    sys.exit(1 if failures else 0)
