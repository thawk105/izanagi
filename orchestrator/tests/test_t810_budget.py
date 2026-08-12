from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import threading

import pytest

from tools.pegasus import t810_budget as B
from tools.pegasus import t810_harness_schema as S


REPO = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO / "tools" / "pegasus" / "policies" / "t810_admission_v1.json"
FIXTURES = Path(__file__).parent / "fixtures" / "t810"
H = "a" * 64


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ratified(*, total: int = 100, jobs: int = 2) -> B.AdmissionPolicy:
    value = _json(POLICY_PATH)
    value["budget"]["status"] = "ratified"
    value["budget"]["total_node_seconds"] = total
    for index, kind in enumerate(B.RUN_KINDS, 1):
        walltime = index * 5
        value["budget"]["estimates"][kind].update({
            "walltime_seconds": walltime,
            "jobs_per_attempt": jobs,
            "node_seconds_per_attempt": walltime * jobs,
        })
    value["budget"]["attempt_policy"].update({
        "builder_attempts": 1,
        "liveness_max_attempts": 1,
        "main_max_attempts_ref": "preregistration.terminal.retry.max_attempts",
    })
    return B.admission_policy_from_mapping(value)


def _request(
    policy: B.AdmissionPolicy, *, group="group-1", kind="liveness", attempt=1,
    requested=1, nodes=2, prereg_max=None, digest=None,
) -> dict:
    return {
        "group_id": group, "run_kind": kind, "attempt": attempt,
        "requested_attempts": requested, "node_count": nodes,
        "launch_intent_sha256": H, "policy_sha256": digest or policy.sha256,
        "preregistration_max_attempts": prereg_max,
    }


def _ledger(tmp_path: Path, *, other: bool = False) -> Path:
    name = "budget_other_genesis.json" if other else "budget_genesis.json"
    genesis = _json(FIXTURES / name)
    path = tmp_path / "budget-ledger.jsonl"
    path.write_bytes(S.canonical_json_bytes(genesis) + b"\n")
    return path


def _reserve(policy, ledger, request=None, *, stamp="2026-08-12T03:00:00Z", lock_factory=None):
    return B.reserve_budget(
        request or _request(policy), policy=policy, ledger_path=ledger,
        clock=lambda: stamp, lock_factory=lock_factory,
    )


def test_repository_policy_loads_but_all_unratified_budget_requests_are_denied(tmp_path: Path):
    policy = B.load_admission_policy(POLICY_PATH)
    receipt = _reserve(policy, tmp_path / "ledger-does-not-need-to-exist.jsonl")
    assert receipt.admitted is False
    assert receipt.reason == "budget-unratified"
    assert receipt.required_node_seconds == 0
    assert receipt.launch_intent_sha256 == H


def test_policy_matches_existing_qsub_and_hostname_consumers_exactly():
    policy = B.load_admission_policy(POLICY_PATH).document
    assert set(policy["qsub"]) == {"status", "project", "queue", "walltime_by_run_kind"}
    assert set(policy["qsub"]["walltime_by_run_kind"]) == set(B.RUN_KINDS)
    assert set(policy["approved_hostnames"]) == {"status", "hostnames"}
    assert policy["qsub"]["status"] == policy["approved_hostnames"]["status"] == "unratified"


def test_policy_rejects_unknown_missing_and_duplicate_nested_fields(tmp_path: Path):
    original = _json(POLICY_PATH)
    unknown = deepcopy(original)
    unknown["budget"]["ledger"]["surprise"] = True
    missing = deepcopy(original)
    del missing["qsub"]["queue"]
    for index, value in enumerate((unknown, missing)):
        path = tmp_path / f"invalid-{index}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        with pytest.raises(B.T810BudgetError, match="unknown or missing"):
            B.load_admission_policy(path)
    duplicate = tmp_path / "duplicate.json"
    raw = POLICY_PATH.read_text(encoding="utf-8")
    duplicate.write_text(raw.replace(
        '"schema_version": "t810-admission-policy/v1",',
        '"schema_version": "t810-admission-policy/v1",\n  "schema_version": "duplicate",', 1,
    ), encoding="utf-8")
    with pytest.raises(B.T810BudgetError, match="duplicate key"):
        B.load_admission_policy(duplicate)


@pytest.mark.parametrize(
    ("total", "admitted"), [(21, True), (20, True), (19, False)],
)
def test_admission_less_equal_greater_boundaries(total: int, admitted: bool, tmp_path: Path):
    policy = _ratified(total=total)
    receipt = _reserve(policy, _ledger(tmp_path))
    assert receipt.required_node_seconds == 20
    assert receipt.admitted is admitted
    assert receipt.reason == ("admitted" if admitted else "insufficient-budget")


@pytest.mark.parametrize("requested", [0, -1, True, B.MAX_NODE_SECONDS + 1])
def test_nonpositive_bool_and_huge_attempt_counts_are_rejected(requested, tmp_path: Path):
    policy = _ratified()
    with pytest.raises(B.T810BudgetError):
        _reserve(policy, _ledger(tmp_path), _request(policy, requested=requested))


def test_required_product_overflow_is_rejected(tmp_path: Path):
    value = _json(POLICY_PATH)
    value["budget"]["status"] = "ratified"
    value["budget"]["total_node_seconds"] = B.MAX_NODE_SECONDS
    for kind in B.RUN_KINDS:
        value["budget"]["estimates"][kind].update({
            "walltime_seconds": B.MAX_NODE_SECONDS,
            "jobs_per_attempt": 2,
            "node_seconds_per_attempt": B.MAX_NODE_SECONDS,
        })
    value["budget"]["attempt_policy"].update({
        "builder_attempts": 1, "liveness_max_attempts": 2,
        "main_max_attempts_ref": "preregistration.terminal.retry.max_attempts",
    })
    with pytest.raises(B.T810BudgetError, match="mismatch or overflow"):
        B.admission_policy_from_mapping(value)


def test_policy_digest_and_jobs_per_attempt_cross_checks_deny_without_append(tmp_path: Path):
    policy = _ratified()
    ledger = _ledger(tmp_path)
    before = ledger.read_bytes()
    mismatch = _reserve(policy, ledger, _request(policy, digest="f" * 64))
    wrong_nodes = _reserve(policy, ledger, _request(policy, nodes=13))
    assert (mismatch.reason, wrong_nodes.reason) == (
        "policy-digest-mismatch", "jobs-per-attempt-mismatch",
    )
    assert ledger.read_bytes() == before


def test_main_reserves_frozen_preregistration_maximum_not_caller_smaller_value(tmp_path: Path):
    policy = _ratified(total=100)
    ledger = _ledger(tmp_path)
    denied = _reserve(
        policy, ledger, _request(policy, kind="main", attempt=1, requested=1, prereg_max=1),
    )
    admitted = _reserve(
        policy, ledger,
        _request(policy, group="group-2", kind="main", attempt=2, requested=1, prereg_max=2),
    )
    assert denied.reason == "attempt-policy-mismatch"
    assert admitted.admitted and admitted.required_node_seconds == 30


def test_different_genesis_ledger_is_rejected(tmp_path: Path):
    policy = _ratified()
    with pytest.raises(B.T810BudgetError, match="genesis digest"):
        _reserve(policy, _ledger(tmp_path, other=True))


def test_duplicate_reservation_tuple_is_denied_inside_locked_transaction(tmp_path: Path):
    policy = _ratified()
    ledger = _ledger(tmp_path)
    first = _reserve(policy, ledger)
    second = _reserve(policy, ledger, stamp="2026-08-12T03:00:01Z")
    assert first.admitted
    assert not second.admitted and second.reason == "duplicate-reservation"
    assert second.ledger_sha256_before == second.ledger_sha256_after


@pytest.mark.parametrize("corruption", ["sequence", "chain", "status", "partial"])
def test_ledger_sequence_chain_status_and_partial_line_are_fail_closed(
    corruption: str, tmp_path: Path,
):
    policy = _ratified()
    ledger = _ledger(tmp_path)
    _reserve(policy, ledger)
    lines = ledger.read_bytes().splitlines()
    if corruption == "partial":
        ledger.write_bytes(b"\n".join(lines) + b'\n{"schema_version"')
    else:
        event = json.loads(lines[1])
        if corruption == "sequence":
            event["sequence"] = 7
        elif corruption == "chain":
            event["previous_sha256"] = "f" * 64
        else:
            event["status"] = "mystery"
        ledger.write_bytes(lines[0] + b"\n" + S.canonical_json_bytes(event) + b"\n")
    with pytest.raises(B.T810BudgetError):
        _reserve(policy, ledger, _request(policy, group="group-2"))


def test_simultaneous_reservations_use_injected_serializing_lock_not_real_flock_competition(
    tmp_path: Path,
):
    policy = _ratified()
    ledger = _ledger(tmp_path)
    mutex = threading.Lock()
    barrier = threading.Barrier(2)
    receipts = []

    @contextmanager
    def fake_lock(path: Path):
        with mutex:
            with path.open("r+b") as handle:
                yield handle

    def worker(stamp: str):
        barrier.wait()
        receipts.append(_reserve(policy, ledger, stamp=stamp, lock_factory=fake_lock))

    threads = [threading.Thread(target=worker, args=(f"2026-08-12T03:01:0{i}Z",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(receipt.admitted for receipt in receipts) == [False, True]
    assert {receipt.reason for receipt in receipts} == {"admitted", "duplicate-reservation"}


@pytest.mark.parametrize(
    ("outcome", "status"),
    [
        ("scheduler-reachability-unknown", "consumed"),
        ("submission-accepted", "consumed"),
        ("pre-submission-aborted", "released"),
        ("qdel-confirmed-before-start", "released"),
        ("unused-retry", "released"),
    ],
)
def test_exact_finalization_transition_table(outcome: str, status: str, tmp_path: Path):
    policy = _ratified()
    ledger = _ledger(tmp_path)
    request = _request(
        policy, kind="main", attempt=2, prereg_max=2,
    ) if outcome == "unused-retry" else None
    receipt = _reserve(policy, ledger, request)
    event = B.finalize_budget(
        receipt.reservation_id, policy=policy, ledger_path=ledger, outcome=outcome,
        witness_sha256="c" * 64, clock=lambda: "2026-08-12T03:02:00Z",
    )
    assert event.document["status"] == status
    assert event.document["finalization_reason"] == outcome
    assert event.document["witness_sha256"] == "c" * 64


def test_finalize_replay_is_rejected(tmp_path: Path):
    policy = _ratified()
    ledger = _ledger(tmp_path)
    receipt = _reserve(policy, ledger)
    kwargs = {
        "policy": policy, "ledger_path": ledger, "outcome": "pre-submission-aborted",
        "witness_sha256": "c" * 64, "clock": lambda: "2026-08-12T03:02:00Z",
    }
    B.finalize_budget(receipt.reservation_id, **kwargs)
    with pytest.raises(B.T810BudgetError, match="replay"):
        B.finalize_budget(receipt.reservation_id, **kwargs)


def test_released_reservation_returns_capacity_but_consumed_one_does_not(tmp_path: Path):
    policy = _ratified(total=20)
    ledger = _ledger(tmp_path)
    first = _reserve(policy, ledger)
    B.finalize_budget(
        first.reservation_id, policy=policy, ledger_path=ledger,
        outcome="qdel-confirmed-before-start", witness_sha256="c" * 64,
        clock=lambda: "2026-08-12T03:03:00Z",
    )
    second = _reserve(policy, ledger, _request(policy, group="group-2"))
    assert second.admitted
    B.finalize_budget(
        second.reservation_id, policy=policy, ledger_path=ledger,
        outcome="scheduler-reachability-unknown", witness_sha256="d" * 64,
        clock=lambda: "2026-08-12T03:03:01Z",
    )
    third = _reserve(policy, ledger, _request(policy, group="group-3"))
    assert not third.admitted and third.reason == "insufficient-budget"


def test_receipt_exact_fields_bind_launch_intent_and_frozen_estimates(tmp_path: Path):
    policy = _ratified()
    receipt = _reserve(policy, _ledger(tmp_path)).to_dict()
    assert set(receipt) == {
        "schema_version", "launch_intent_sha256", "policy_sha256", "estimates_sha256",
        "ledger_path", "ledger_sha256_before", "ledger_sha256_after", "reservation_id",
        "run_kind", "requested_attempts", "estimate_per_attempt_node_seconds",
        "required_node_seconds", "total_node_seconds", "counted_node_seconds",
        "remaining_node_seconds", "admitted", "reason", "created_at",
    }
    assert receipt["launch_intent_sha256"] == H
    assert receipt["estimates_sha256"] == S.canonical_sha256(
        policy.document["budget"]["estimates"]
    )
