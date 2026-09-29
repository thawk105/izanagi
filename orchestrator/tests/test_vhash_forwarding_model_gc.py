"""GC pressure connection checks using the production transition system."""
from __future__ import annotations

import sys
import traceback
from functools import lru_cache
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from vhash_forwarding_model.gc_connection import effect_snapshot  # noqa: E402
from vhash_forwarding_model.judge import j3, judge  # noqa: E402
from vhash_forwarding_model.model import (State, Txn, Version, aborted_after_fault,
                                          check_timestamp_uniqueness, changed_step_in_trace,
                                          enabled_steps, explore, replay, visible)  # noqa: E402
from vhash_forwarding_model.scenarios import scenario, danger_witness  # noqa: E402


@lru_cache(None)
def _search(name, fault="", *, o1=False, pressure="self", revert=False):
    initial, window = scenario(name)
    def monotone(before, after, step):
        assert all(new.gc_floor >= old.gc_floor for old, new in zip(before.txns, after.txns)), step
    def sound(state):
        assert all(t.cand_ts >= t.gc_floor for t in state.txns)
    result = explore(initial, "v1", fault, window, o1=o1, pressure=pressure,
                     revert_after_confirm=revert, danger=danger_witness(name),
                     transition_invariant=monotone, state_invariant=sound if not fault else None,
                     collect_effects=not fault and not revert and name in ("G1", "G2"))
    assert result["statistics"]["complete"], (name, fault, result["statistics"])
    return initial, result


def test_g1_effects_and_waiting_bounds():
    initial, off = _search("G1", pressure="off")
    _, on = _search("G1")
    assert off["effects"]["max_B"]["value"] == 45
    assert on["effects"]["max_B"]["value"] == 61
    assert on["effects"]["attributable"]["delta_B"] == 16
    assert on["effects"]["attributable"]["delta_freed"] == 2
    assert off["effects"]["attributable"] is None
    assert on["effects"]["simultaneous"] is not None
    assert on["witness"]["reached"] and danger_witness("G1") is None
    assert not on["counterexample"]
    t = next(t for t in initial.txns if t.id == "T")
    assert t.ops[1] == ("WAIT", "")
    assert effect_snapshot(initial)["reclaimable"] == 0
    reclaimed = explore(initial, "v1", pressure="self", witness=lambda b, a, x:
                        x.operation == "reclaim" and x.version == "B40")
    assert reclaimed["witness"]["reached"]
    assert next(v for v in replay(initial, reclaimed["witness"]["steps"], pressure="self").versions
                if v.id == "B40").reclaimed


def test_g2_one_waiter_does_not_move_boundary():
    _, result = _search("G2")
    assert danger_witness("G2") is None
    assert result["witness"]["reached"]
    only = result["effects"]["g2"]["T_only"]
    both = result["effects"]["g2"]["both"]
    assert only and both
    assert only["snapshot"]["B"] == 35
    assert both["snapshot"]["B"] == 61
    for row in (only, both):
        state = replay(scenario("G2")[0], row["steps"], pressure="self")
        assert all(t.phase == "ops" and t.ops[t.pc] == ("WAIT", "") for t in state.txns)


def test_g3_to_g6_unsafe_faults_have_real_shortest_replays():
    for name, fault, o1, expected, version in (
        ("G3", "UG1", False, "J3", "B40"),
        ("G4", "UG2", False, "J3", "B60"),
        ("G5", "UG3", True, "J1", ""),
        ("G6", "UF1", False, "J3", "B40"),
    ):
        initial, result = _search(name, fault, o1=o1)
        assert result["witness"]["reached"] and result["danger"]["reached"], name
        counter = result["counterexample"]
        assert counter and counter["judge"] == expected, name
        steps = counter["steps"]
        assert changed_step_in_trace(steps, fault), name
        at = next(i for i, x in enumerate(steps) if x.fault == fault)
        fault_before = replay(initial, steps[:at], "v1", fault, o1, "self")
        fault_after = replay(initial, steps[:at + 1], "v1", fault, o1, "self")
        old_t = next(t for t in fault_before.txns if t.id == "T")
        new_t = next(t for t in fault_after.txns if t.id == "T")
        if fault == "UG1":
            assert steps[at].operation == "pressure_start"
            assert old_t.gc_floor == old_t.cand_ts == old_t.start
            assert new_t.gc_floor == new_t.target > old_t.gc_floor
            assert new_t.cand_ts == old_t.start
        elif fault == "UG2":
            assert steps[at].operation == "pressure_commit"
            assert old_t.gc_floor < 10**9 and new_t.gc_floor == 10**9
        elif fault == "UF1":
            assert steps[at].operation == "pressure_fallback"
            assert old_t.gc_floor > old_t.start and old_t.cand_ts > old_t.start
            assert new_t.cand_ts == old_t.start and new_t.gc_floor == old_t.gc_floor
        else:
            assert steps[at].operation == "pressure_check"
            read = next(v for v in fault_before.versions if v.id == steps[at].version)
            selected = visible(fault_before, read.key, old_t.target)
            assert selected and selected.id != read.id
            assert not old_t.failed and not new_t.failed
        before = replay(initial, steps[:-1], "v1", fault, o1, "self")
        after = replay(initial, steps, "v1", fault, o1, "self")
        assert judge(before, after, steps[-1])[expected] == counter["reason"]
        if version:
            assert counter["reason"]["version"] == version
            v = next(v for v in initial.versions if v.id == version)
            assert v.owner == "initial"
            assert v.wts < next(t for t in before.txns if t.id == "T").cand_ts
        if name == "G5":
            assert {v.owner for v in after.versions if v.owner != "initial"} == {"T", "W"}
            assert counter["reason"]["cycle"] == ["T", "W", "T"]
        if name == "G6":
            danger = result["danger"]["steps"]
            assert j3(replay(initial, danger[:-1], "v1", fault, o1, "self"),
                      replay(initial, danger, "v1", fault, o1, "self"), danger[-1])["reason"] == "rollback"
            publish = next(i for i, x in enumerate(danger) if x.operation == "pressure_publish")
            reclaim = next(i for i, x in enumerate(danger) if x.operation == "reclaim" and x.version == "B40")
            failed = next(i for i, x in enumerate(danger) if x.operation == "pressure_check" and i > publish)
            fallback = next(i for i, x in enumerate(danger) if x.operation == "pressure_fallback" and x.fault == "UF1")
            assert publish < reclaim < failed < fallback
            pre = replay(initial, danger[:fallback], "v1", fault, o1, "self")
            post = replay(initial, danger[:fallback + 1], "v1", fault, o1, "self")
            assert next(t for t in pre.txns if t.id == "T").failed
            assert next(v for v in pre.versions if v.id == "B40").reclaimed
            assert next(t for t in post.txns if t.id == "T").cand_ts == 45
            assert j3(pre, post, danger[fallback])["reason"] == "rollback"


def test_ug2r_and_ug3_without_o1():
    _, refs = _search("G4", "UG2r")
    assert refs["witness"]["reached"] and not refs["counterexample"]
    assert not refs["danger"]["reached"]
    initial, unchecked = _search("G5", "UG3")
    assert unchecked["witness"]["reached"] and not unchecked["counterexample"]
    steps = aborted_after_fault(initial, "UG3", pressure="self")
    assert steps and changed_step_in_trace(steps, "UG3")
    assert steps[-1].operation == "decide_aborted"
    state = replay(initial, steps, "v1", "UG3", False, "self")
    assert any(t.phase == "release" and t.failed for t in state.txns)


def test_g6_rollback_j3_positive_and_safe_negative():
    initial, _ = scenario("G6")
    _, unsafe = _search("G6", "UF1")
    steps = unsafe["danger"]["steps"]
    before = replay(initial, steps[:-1], pressure="self")
    after, safe_step = next((n, x) for n, x in enabled_steps(before, pressure="self")
                            if x.thread == "T" and x.operation == "pressure_fallback")
    assert next(t for t in after.txns if t.id == "T").gc_floor > 45
    check_timestamp_uniqueness(before)
    check_timestamp_uniqueness(after)
    assert j3(before, after, safe_step) is None
    before = replay(initial, steps[:-1], "v1", "UF1", pressure="self")
    after = replay(initial, steps, "v1", "UF1", pressure="self")
    check_timestamp_uniqueness(before)
    check_timestamp_uniqueness(after)
    assert j3(before, after, steps[-1])["reason"] == "rollback"


def test_refs_are_counted_and_pressure_stays_in_wait():
    versions = (Version("B40", "B", 40, 40), Version("B60", "B", 60, 60))
    t = Txn("T", 45, (("R", "B"), ("WAIT", "")), gc_floor=61,
            refs=("B40",))
    state = State(versions, (t,))
    assert effect_snapshot(state)["reclaimable"] == 0
    assert effect_snapshot(replace(state, txns=(replace(t, refs=()),)))["reclaimable"] == 1
    assert not any(step.operation in ("request_pressure", "pressure_start")
                   for _, step in enabled_steps(state, pressure="self"))


def test_sound_g1_to_g6_fixed_scenarios_invariants():
    for name in ("G1", "G2", "G3", "G4", "G5", "G6"):
        for revert in ((False, True) if name in ("G1", "G3", "G6") else (False,)):
            _, result = _search(name, revert=revert)
            assert result["statistics"]["complete"], (name, revert)
            assert result["witness"]["reached"], (name, revert)
            if name not in ("G1", "G2"):
                assert not result["danger"]["reached"], (name, revert)
            assert not result["counterexample"], (name, revert)


def test_g1_to_g6_all_fault_floors_monotone():
    for name, fault, o1 in (("G3", "UG1", False), ("G4", "UG2", False),
                            ("G4", "UG2r", False), ("G5", "UG3", False),
                            ("G5", "UG3", True), ("G6", "UF1", False)):
        _, result = _search(name, fault, o1=o1)
        assert result["statistics"]["complete"], (name, fault)


def test_restricted_judgment_matches_reference_gc():
    initial, window = scenario("G3")
    a = explore(initial, "v1", "UG1", window, pressure="self")
    b = explore(initial, "v1", "UG1", window, pressure="self", all_transitions=True)
    assert a["statistics"]["complete"] and b["statistics"]["complete"]
    assert a["verdicts"] == b["verdicts"]


def test_old_representative_pins():
    pins = (("S3", "v1", "", False, 180, (False, False, False)),
            ("S7", "v1", "", False, 1720, (False, False, False)),
            ("S10", "v1", "", False, 12905, (False, False, False)),
            ("S8", "v0", "", False, 47448, (True, True, False)))
    for name, protocol, fault, o1, visited, verdicts in pins:
        initial, window = scenario(name)
        result = explore(initial, protocol, fault, window, o1=o1,
                         danger=danger_witness(name) if name == "S8" else None)
        assert result["statistics"]["complete"] and result["statistics"]["visited"] == visited
        assert tuple(bool(result["verdicts"][j]) for j in ("J1", "J2", "J3")) == verdicts


if __name__ == "__main__":
    failures = 0
    for name in sorted(name for name, value in globals().items()
                       if name.startswith("test_") and callable(value)):
        try:
            globals()[name]()
        except Exception:
            failures += 1
            print(f"FAIL {name}", flush=True)
            traceback.print_exc()
        else:
            print(f"PASS {name}", flush=True)
    sys.exit(1 if failures else 0)
