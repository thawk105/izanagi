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
from vhash_forwarding_model.judge import j3, judge  # noqa: E402

_SEARCHES = []


@lru_cache(None)
def _search(name, fault="", resume="accept", revert=False):
    initial, window = scenario(name)
    result = explore(initial, fault=fault, witness=window, danger=danger_witness(name),
                     pressure="helper", resume=resume, revert_after_confirm=revert,
                     collect_effects=not bool(fault))
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
        assert result["witness"]["reached"] and result["fault_step_seen"]
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
                     pressure="helper", max_states=10000, collect_effects=False)
    _SEARCHES.append(("H3", "UH2", "accept", False, result["statistics"]))
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


def test_wait_own_step_and_generation():
    initial, _ = scenario("H1")
    t_read = next(n for n, x in enabled_steps(initial, pressure="helper") if x.thread == "T")
    t = t_read.txns[0]
    assert t.pc == 1
    own = [(n, x) for n, x in enabled_steps(t_read, pressure="helper") if x.thread == "T"]
    assert [x.operation for _, x in own] == ["end_wait"]
    assert own[0][0].txns[0].gen == t.gen + 1
    assert t.phase == "ops" and t.ops[t.pc] == ("WAIT", "")


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
