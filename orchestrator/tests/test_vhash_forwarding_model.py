"""Bounded finite-model checks with independent judge fixtures."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import vhash_forwarding_model as forwarding  # noqa: E402
from vhash_forwarding_model import model  # noqa: E402
from vhash_forwarding_model.judge import j1, j3, judge  # noqa: E402
from vhash_forwarding_model.model import (Step, explore, replay, changed_step_in_trace,
                                           enabled_steps, aborted_after_fault, txn_step,
                                           fault_changes_forward_check)  # noqa: E402
from vhash_forwarding_model.scenarios import (handmade_j1, handmade_j3,
                                               handmade_future_forward, s8_prefix,
                                               danger_witness)  # noqa: E402


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
        if name in ("S9", "S10"):
            continue  # S9 runs through the CLI; S10 has its own result pins below.
        initial, witness = forwarding.scenario(name)
        if name == "S8":
            prefix, state = s8_prefix()
            assert replay(initial, prefix, "v1") == state
            initial = state
        result = explore(initial, "v1", witness=witness,
                         danger=danger_witness(name) if name in ("S3", "S8") else None)
        assert result["statistics"]["complete"], name
        assert result["witness"]["reached"], name
        assert result["verdicts"]["J1"] is None, name
        assert result["verdicts"]["J3"] is None, name
        if name == "S3":
            assert result["witness"]["steps"][-1].operation in ("read_floor", "reclaim")
            assert not result["danger"]["reached"]
        if name == "S8":
            assert not result["danger"]["reached"]


def test_v0_s8_cycle_and_replay():
    initial, witness = forwarding.scenario("S8")
    prefix, state = s8_prefix()
    assert replay(initial, prefix, "v0") == state
    result = explore(state, "v0", witness=witness, danger=danger_witness("S8"))
    counterexample = result["counterexample"]
    assert result["statistics"]["complete"]
    assert counterexample and counterexample["judge"] == "J1"
    assert result["danger"]["reached"]
    final = replay(initial, prefix + counterexample["steps"], "v0")
    assert j1(final) == counterexample["reason"]


def test_s4_pending_commit_and_abort_reachable():
    initial, _ = forwarding.scenario("S4")
    for operation in ("decide_committed", "decide_aborted"):
        result = explore(initial, "v1", witness=lambda b, a, x: x.thread == "W" and x.operation == operation)
        assert result["witness"]["reached"], operation


def test_single_rule_faults_detected_and_replay():
    cases = (("U1v", "S1", "J1"),
             ("U3a", "S3", "J3"), ("U3b", "S1", "J3"),
             ("U4", "S7", "J3"))
    for fault, name, expected in cases:
        initial, witness = forwarding.scenario(name)
        result = explore(initial, "v1", fault, witness,
                         danger=danger_witness("S3") if name == "S3" else None)
        counterexample = result["counterexample"]
        assert result["statistics"]["complete"], fault
        assert counterexample and counterexample["judge"] == expected, fault
        if name == "S3":
            assert result["danger"]["reached"]
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


def test_s4_pending_blocks_read():
    initial, _ = forwarding.scenario("S4")
    state = initial
    for thread in ("W", "W", "W", "W"):
        state, _ = next((n, x) for n, x in enabled_steps(state) if x.thread == thread)
    assert any(v.id == "W:B" and v.status == "PENDING" and v.wts <= 45 for v in state.versions)
    assert not any(x.thread == "T" for _, x in enabled_steps(state))


def test_reclaimed_touch_is_j3_even_on_same_state():
    initial, _ = forwarding.scenario("S1")
    result = explore(initial, "v1", "U3b")
    assert result["counterexample"] and result["counterexample"]["judge"] == "J3"
    assert "use_after_free" in result["violation_kinds"]["J3"]


def test_restricted_judgment_matches_every_transition():
    for name, fault in (("S4", ""), ("S1", "U1v"), ("S3", "U3a")):
        initial, witness = forwarding.scenario(name)
        restricted = explore(initial, "v1", fault, witness)
        reference = explore(initial, "v1", fault, witness, all_transitions=True)
        assert restricted["statistics"]["complete"] and reference["statistics"]["complete"]
        assert restricted["verdicts"] == reference["verdicts"]


def test_s9_u2_after_other_reader_aborts():
    initial, _ = forwarding.scenario("S9")
    actors = ("T", "T", "W", "W", "U", "U") + ("W",) * 12 + ("U",) * 12 + ("T",) * 12
    for fault in ("", "U2"):
        state = initial
        steps = []
        after_abort = None
        for actor in actors:
            matches = [(n, x) for n, x in enabled_steps(
                state, "v1", frozenset((fault,)) if fault else frozenset()) if x.thread == actor]
            assert len(matches) == 1
            state, step = matches[0]
            steps.append(step)
            if actor == "U" and step.operation == "release_refs":
                after_abort = state
        assert replay(initial, steps, "v1", fault) == state
        assert next(t for t in state.txns if t.id == "U").failed
        assert next(v for v in state.versions if v.id == "A10").rts == 80
        assert changed_step_in_trace(steps, "U2") == bool(fault)
        assert bool(j1(state)) == bool(fault)
        assert after_abort is not None
        suffix = explore(after_abort, "v1", fault)
        assert suffix["statistics"]["complete"]
        assert bool(suffix["verdicts"]["J1"]) == bool(fault)


def test_j3_future_forward_version():
    before, after = handmade_future_forward()
    assert j3(before, after, Step("GC", "reclaim", "A30"))["reason"] == "future_read"


def test_reclaimed_version_metadata_routes():
    base, _ = forwarding.scenario("S1")
    extra = model.Version("A60", "A", 60, 60, reclaimed=True)
    t = next(t for t in base.txns if t.id == "T")
    for phase, kwargs, expected in (
        ("ops", {}, "A60"),
        ("f_check", {"target": 70, "read_log": (("A", "A10"),)}, "A60"),
        ("v_check", {"read_log": (("A", "A10"),)}, "A60"),
        ("w_check", {"index": 0}, "A60"),
    ):
        actor = replace(t, phase=phase, ops=(("W", "A"),) if phase == "w_check" else t.ops,
                        **kwargs)
        state = replace(base, versions=base.versions + (extra,), txns=(actor, base.txns[1]))
        after, step = txn_step(state, actor, "v1", frozenset())
        assert after == state and step == Step("T", "touch_reclaimed", expected)
        assert j3(state, after, step)["reason"] == "use_after_free"
    cold, _ = forwarding.scenario("S2")
    actor = replace(cold.txns[0], ops=(("R", "B"),))
    versions = tuple(replace(v, reclaimed=True) if v.id == "B60" else v for v in cold.versions)
    state = replace(cold, versions=versions, txns=(actor, cold.txns[1]))
    after, step = txn_step(state, actor, "v1", frozenset())
    assert after == state and step == Step("T", "touch_reclaimed", "B60")
    assert j3(state, after, step)["reason"] == "use_after_free"


def test_fault_then_failed_commit_validation():
    for fault, name in (("U1f", "S6"), ("U5", "S1"), ("U6", "S6")):
        initial, _ = forwarding.scenario(name)
        steps = aborted_after_fault(initial, fault)
        assert steps and changed_step_in_trace(steps, fault), fault
        assert steps[-1].operation == "decide_aborted", fault
        assert replay(initial, steps, "v1", fault).txns
        if fault == "U5":
            fault_at = next(i for i, x in enumerate(steps) if x.fault == "U5")
            assert steps[fault_at].operation == "cold_read"
            before = replay(initial, steps[:fault_at], "v1", fault)
            assert any(v.status == "PENDING" and v.key == "A" and v.wts <= 70
                       for v in before.versions)


def test_scenario_witness_order_and_s5_writer_abort():
    for name in ("S1", "S2", "S5", "S6", "S7"):
        initial, witness = forwarding.scenario(name)
        fault = "U1v" if name == "S5" else ""
        result = explore(initial, "v1", fault, witness)
        assert result["witness"]["reached"], name
        steps = result["witness"]["steps"]
        operations = [x.operation for x in steps]
        if name == "S1":
            assert operations.index("validation_rts") < next(
                i for i, x in enumerate(steps) if x.operation == "install" and x.version == "W:A")
        elif name == "S2":
            assert operations.index("forward_candidate") < next(
                i for i, x in enumerate(steps) if x.operation == "install" and x.version == "W:B")
            assert steps[-1].thread == "T" and steps[-1].operation == "forward_check"
        elif name == "S5":
            assert next(i for i, x in enumerate(steps) if x.thread == "T" and x.operation == "validate_read") < next(
                i for i, x in enumerate(steps) if x.operation == "install" and x.version == "W:A")
        elif name == "S6":
            assert operations.index("forward_candidate") < next(
                i for i, x in enumerate(steps) if x.operation == "install" and x.version == "W:A")
        else:
            state = replay(initial, steps)
            t = next(t for t in state.txns if t.id == "T")
            assert t.gc_floor > t.start and ("A", "A20") in t.read_log
    initial, _ = forwarding.scenario("S5")
    result = explore(initial, "v1", witness=lambda b, a, x: x.thread == "W" and x.operation == "decide_aborted")
    assert result["witness"]["reached"]


def _s10_search(case):
    protocol, fault, o1, _, _ = case
    initial, witness = forwarding.scenario("S10")
    return explore(initial, protocol, fault, witness, o1=o1)


def test_s10_old_target_allocation_violates_timestamp_uniqueness():
    initial, _ = forwarding.scenario("S10")

    def old_next_free(state, minimum):
        used = ({v.wts for v in state.versions} | {t.start for t in state.txns}
                | {t.cand_ts for t in state.txns})
        while minimum in used:
            minimum += 1
        return minimum

    with patch.object(model, "_next_free", old_next_free):
        try:
            explore(initial, "v1")
        except model.TimestampCollisionError as exc:
            assert "timestamp 26" in str(exc)
        else:
            raise AssertionError("old target allocation did not expose a timestamp collision")


def test_s10_write_skew_search_results():
    initial, witness = forwarding.scenario("S10")
    assert len({v.key for v in initial.versions}) == 2
    assert len(initial.txns) == 2
    assert all(len(t.ops) <= 3 for t in initial.txns)
    expected = (
        ("v0", "", False, (False, False, False), 12905),
        ("v1", "", False, (False, False, False), 12905),
        ("v1", "", True, (False, False, False), 10607),
        ("v1", "U1f", False, (False, False, False), 12939),
        ("v1", "U6", False, (False, False, False), 12281),
        ("v1", "U1f", True, (True, True, False), 10617),
        ("v1", "U6", True, (True, True, False), 9959),
    )
    results = [_s10_search(case) for case in expected]
    for (protocol, fault, o1, verdicts, visited), result in zip(expected, results):
        assert result["statistics"]["complete"]
        assert result["statistics"]["visited"] == visited
        assert tuple(bool(result["verdicts"][name]) for name in ("J1", "J2", "J3")) == verdicts
        assert result["witness"]["reached"]
        steps = result["witness"]["steps"]
        assert next(i for i, x in enumerate(steps) if x.thread == "T" and x.operation == "forward_candidate") < next(
            i for i, x in enumerate(steps) if x.operation == "install" and x.version == "W:A")
        assert steps[-1].operation == "install" and steps[-1].version == "W:A"
        reached = replay(initial, steps, protocol, fault, o1)
        t = next(t for t in reached.txns if t.id == "T")
        w_version = next(v for v in reached.versions if v.id == "W:A")
        assert ("A", "A10") in t.read_log and 10 < w_version.wts < t.target
        assert bool(result["counterexample"]) == bool(o1 and fault)
        if o1 and fault:
            assert result["counterexample"]["judge"] == "J1"
            assert fault_changes_forward_check(initial, result["counterexample"]["steps"], fault, o1)
