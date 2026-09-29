"""GC pressure connection checks using the production transition system."""
from __future__ import annotations

import sys
import traceback
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from vhash_forwarding_model.gc_connection import effect_snapshot  # noqa: E402
from vhash_forwarding_model.judge import j3, judge  # noqa: E402
from vhash_forwarding_model.model import (State, Step, Txn, Version, aborted_after_fault,
                                          changed_step_in_trace, enabled_steps, explore, replay)  # noqa: E402
from vhash_forwarding_model.scenarios import scenario, danger_witness  # noqa: E402


def _search(name, fault="", *, o1=False, pressure="self", revert=False):
    initial, window = scenario(name)
    result = explore(initial, "v1", fault, window, o1=o1, pressure=pressure,
                     revert_after_confirm=revert, danger=danger_witness(name))
    assert result["statistics"]["complete"], (name, fault, result["statistics"])
    return initial, result


def test_gc_effects_and_waiting_bounds():
    initial, off = _search("G1", pressure="off")
    _, on = _search("G1")
    assert off["effects"]["max_B"]["value"] == 45
    assert on["effects"]["max_B"]["value"] == 61
    assert on["effects"]["max_delta_B"]["value"] > 0
    assert on["effects"]["simultaneous"] is not None
    assert on["witness"]["reached"] and not on["danger"]["reached"]
    assert not on["counterexample"]
    t = next(t for t in initial.txns if t.id == "T")
    assert t.ops[1] == ("WAIT", "")
    assert effect_snapshot(initial)["reclaimable"] == 0


def test_g2_one_waiter_does_not_move_boundary():
    _, result = _search("G2")
    assert result["witness"]["reached"]
    only = result["effects"]["g2"]["T_only"]
    both = result["effects"]["g2"]["both"]
    assert only and both
    assert only["snapshot"]["B"] == 35
    assert both["snapshot"]["B"] > 35


def test_unsafe_gc_faults_have_real_shortest_replays():
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


def test_rollback_j3_positive_and_safe_negative():
    versions = (Version("A20", "A", 20, 20), Version("B40", "B", 40, 40, reclaimed=True),
                Version("B60", "B", 60, 60))
    old = Txn("T", 45, (("WAIT", ""), ("R", "B")), cand_ts=61,
              gc_floor=61, published_max=61, pc=0)
    before = State(versions, (old,))
    unsafe = replace(before, txns=(replace(old, cand_ts=45),))
    assert j3(before, unsafe, Step("T", "pressure_fallback"))["reason"] == "rollback"
    safe = replace(before, txns=(replace(old, cand_ts=60),))
    assert j3(before, safe, Step("T", "pressure_fallback")) is None


def test_refs_are_counted_and_pressure_stays_in_wait():
    versions = (Version("B40", "B", 40, 40), Version("B60", "B", 60, 60))
    t = Txn("T", 45, (("R", "B"), ("WAIT", "")), gc_floor=61,
            refs=("B40",))
    state = State(versions, (t,))
    assert effect_snapshot(state)["reclaimable"] == 0
    assert effect_snapshot(replace(state, txns=(replace(t, refs=()),)))["reclaimable"] == 1
    assert not any(step.operation in ("request_pressure", "pressure_start")
                   for _, step in enabled_steps(state, pressure="self"))


def test_sound_all_reachable_floors_and_revert():
    def invariant(state):
        assert all(t.cand_ts >= t.published_max for t in state.txns)
    for name in ("G1", "G2", "G3", "G4", "G5", "G6"):
        initial, window = scenario(name)
        for revert in (False, True):
            result = explore(initial, "v1", witness=window, danger=danger_witness(name),
                             pressure="self", revert_after_confirm=revert,
                             state_invariant=invariant)
            assert result["statistics"]["complete"], (name, revert)
            assert result["witness"]["reached"], (name, revert)
            assert not result["danger"]["reached"], (name, revert)
            assert not result["counterexample"], (name, revert)


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
