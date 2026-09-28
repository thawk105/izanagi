"""Bounded finite-model checks with independent judge fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import vhash_forwarding_model as forwarding  # noqa: E402
from vhash_forwarding_model.judge import j1, j3, judge  # noqa: E402
from vhash_forwarding_model.model import Step, explore, replay, changed_step_in_trace  # noqa: E402
from vhash_forwarding_model.scenarios import handmade_j1, handmade_j3  # noqa: E402


def test_j1_handmade_positive_and_negative():
    cycle = j1(handmade_j1(True))
    assert cycle and {e["kind"] for e in cycle["edges"]} == {"rw"}
    assert j1(handmade_j1(False)) is None


def test_j3_handmade_positive_and_negative():
    before, after = handmade_j3(True)
    reason = j3(before, after, Step("GC", "reclaim", "A20"))
    assert reason and reason["reason"] == "future_read" and reason["txn"] == "T"
    before, after = handmade_j3(False)
    assert j3(before, after, Step("GC", "reclaim", "A20")) is None


def test_all_scenario_witnesses_and_v1_bounds():
    for name in forwarding.NAMES:
        initial, witness = forwarding.scenario(name)
        result = explore(initial, "v1", witness=witness)
        assert result["statistics"]["complete"], name
        assert result["witness"]["reached"], name
        assert result["verdicts"]["J1"] is None, name
        assert result["verdicts"]["J3"] is None, name
        if name == "S3":
            assert result["witness"]["steps"][-1].operation == "reclaim"


def test_v0_s8_cycle_and_replay():
    initial, witness = forwarding.scenario("S8")
    result = explore(initial, "v0", witness=witness)
    counterexample = result["counterexample"]
    assert result["statistics"]["complete"]
    assert counterexample and counterexample["judge"] == "J1"
    final = replay(initial, counterexample["steps"], "v0")
    assert j1(final) == counterexample["reason"]


def test_s4_pending_commit_and_abort_reachable():
    initial, _ = forwarding.scenario("S4")
    for operation in ("decide_committed", "decide_aborted"):
        result = explore(initial, "v1", witness=lambda b, a, x: x.thread == "W" and x.operation == operation)
        assert result["witness"]["reached"], operation


def test_single_rule_faults_detected_and_replay():
    cases = (("U1v", "S1", "J1"), ("U2", "S1", "J1"),
             ("U3a", "S3", "J3"), ("U3b", "S1", "J3"),
             ("U4", "S7", "J3"))
    for fault, name, expected in cases:
        initial, witness = forwarding.scenario(name)
        result = explore(initial, "v1", fault, witness)
        counterexample = result["counterexample"]
        assert result["statistics"]["complete"], fault
        assert counterexample and counterexample["judge"] == expected, fault
        steps = counterexample["steps"]
        assert changed_step_in_trace(steps, fault), fault
        before = replay(initial, steps[:-1], "v1", fault)
        after = replay(initial, steps, "v1", fault)
        assert judge(before, after, steps[-1])[expected] == counterexample["reason"]


def test_single_rule_faults_undetected_in_fixed_bounds():
    for fault, name in (("U1f", "S2"), ("U5", "S4"), ("U6", "S6")):
        initial, witness = forwarding.scenario(name)
        result = explore(initial, "v1", fault, witness)
        assert result["statistics"]["complete"], fault
        assert result["counterexample"] is None, fault
