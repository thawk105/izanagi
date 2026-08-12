from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from orchestrator.campaign import reflux_origin_ledger as ledger
from orchestrator.campaign import reflux_origin_topology as topology
from orchestrator.campaign.reflux_ir import TriggerGateIR, encode_wire
from orchestrator.tests.reflux_origin_fixture_builder import (
    build_recovery_envelope_inputs,
)


def _independent_canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _expected_envelope() -> dict:
    """F0 plus the planned-run identity field missing from its frozen schema."""

    value = build_recovery_envelope_inputs()
    for member in value["members"]:
        member["planned_campaign_run_identity"] = (
            f"fixture-campaign-run-{member['query_ordinal']:04d}"
        )
    return value


@dataclass(frozen=True)
class _OpaqueDigest:
    sha256: str


def _event_operation_ids(value: dict) -> topology.EventOperationIds:
    operation_ids = value["event_operation_ids"]
    return topology.EventOperationIds(**operation_ids)


def _member_materials(value: dict) -> tuple[topology.MemberRecoveryMaterial, ...]:
    return tuple(
        topology.MemberRecoveryMaterial(
            candidate_salt=member["candidate_salt"],
            result_evidence_salt=member["result_evidence_salt"],
            constraint_salt=member["constraint_salt"],
            evidence_path=member["evidence_path"],
            planned_campaign_run_identity=member["planned_campaign_run_identity"],
        )
        for member in value["members"]
    )


def _envelope() -> topology.RecoveryEnvelope:
    value = _expected_envelope()
    attempts = value["reserve_attempts"]
    source_wire = value["members"][0]["candidate_wire"]
    source_mask = sum(
        (character == "1") << bit for bit, character in enumerate(source_wire)
    )
    return topology.build_recovery_envelope(
        capability_digest=_OpaqueDigest(
            value["origin_binding_capability_sha256"]
        ),
        source_closure_digest=value["source_closure_sha256"],
        hypothesis_sha256=value["hypothesis_sha256"],
        validation_plan_sha256=value["validation_plan_sha256"],
        attempt_0_batch_id=attempts[0]["batch_id"],
        retry_1_batch_id=attempts[1]["batch_id"],
        event_operation_ids=_event_operation_ids(value),
        source_mask=source_mask,
        member_materials=_member_materials(value),
        initial_expected_state_commitment=value["expected_state_commitment"],
    )


def _reserved(attempt: topology.ReservationAttempt) -> ledger.BatchReserved:
    return ledger.BatchReserved(
        batch_id=attempt.batch_id,
        iteration_index=attempt.iteration_index,
        member_row_count=33,
        query_ordinal_start=attempt.query_ordinal_start,
    )


def test_exact_source_and_32_mask_member_allocation() -> None:
    envelope = _envelope()
    members = envelope.members

    assert len(members) == 33
    assert (
        members[0].iteration_index,
        members[0].query_ordinal,
        members[0].candidate_wire,
        members[0].replicate_ordinal,
    ) == (0, 0, encode_wire(TriggerGateIR(7)), 0)
    assert [
        (
            member.iteration_index,
            member.query_ordinal,
            member.candidate_wire,
            member.replicate_ordinal,
        )
        for member in members[1:]
    ] == [
        (0, 1 + mask, encode_wire(TriggerGateIR(mask)), 1 if mask == 7 else 0)
        for mask in range(32)
    ]


def test_topology_has_33_rows_32_candidates_and_distinct_planned_runs() -> None:
    members = _envelope().members

    assert len(members) == 33
    assert len({member.candidate_wire for member in members}) == 32
    assert len({member.planned_campaign_run_identity for member in members}) == 33


def test_duplicate_planned_campaign_run_identity_is_rejected() -> None:
    value = _expected_envelope()
    materials = list(_member_materials(value))
    duplicate = materials[0]
    second = materials[1]
    materials[1] = topology.MemberRecoveryMaterial(
        candidate_salt=second.candidate_salt,
        result_evidence_salt=second.result_evidence_salt,
        constraint_salt=second.constraint_salt,
        evidence_path=second.evidence_path,
        planned_campaign_run_identity=duplicate.planned_campaign_run_identity,
    )

    with pytest.raises(topology.TopologyError, match="distinct planned"):
        topology.build_logical_topology(source_mask=7, member_materials=materials)


def test_non_suffix_tombstones_are_rejected_for_one_reason() -> None:
    tombstones = [False] * 10 + [True] + [False] + [True] * 21

    with pytest.raises(topology.TopologyError, match="terminal suffix"):
        topology.validate_tombstone_suffix(tombstones)


def test_one_precommit_rereservation_is_allowed_but_second_is_rejected() -> None:
    envelope = _envelope()
    attempt_0, attempt_1 = envelope.reserve_attempts
    first_abandonment = [
        _reserved(attempt_0),
        ledger.BatchReservationAbandoned(batch_id=attempt_0.batch_id),
    ]

    assert topology.next_reservation_attempt(
        envelope=envelope, events=first_abandonment
    ) == attempt_1

    second_abandonment = first_abandonment + [
        _reserved(attempt_1),
        ledger.BatchReservationAbandoned(batch_id=attempt_1.batch_id),
    ]
    with pytest.raises(topology.TopologyError, match="only one pre-commit"):
        topology.next_reservation_attempt(
            envelope=envelope, events=second_abandonment
        )


def test_rereservation_after_batch_committed_is_rejected() -> None:
    envelope = _envelope()
    attempt = envelope.reserve_attempts[0]
    events = [
        _reserved(attempt),
        ledger.BatchCommitted(
            batch_id=attempt.batch_id,
            iteration_index=attempt.iteration_index,
            members=(),
        ),
    ]

    with pytest.raises(topology.TopologyError, match="cannot escape"):
        topology.next_reservation_attempt(envelope=envelope, events=events)


def test_lost_receipt_replay_keeps_original_event_expected_state() -> None:
    envelope = _envelope()
    request = topology.PlannedEventRequest(
        operation_id=envelope.event_operation_ids.reserve_attempt_0,
        expected_state_commitment=envelope.expected_state_commitment,
    )

    assert topology.expected_state_for_replay(request) == (
        envelope.expected_state_commitment
    )


@dataclass(frozen=True)
class _CrossOriginReceipt:
    resulting_state_commitment: str
    current_state_commitment: str


def test_replayed_receipt_uses_current_state_after_cross_origin_commit() -> None:
    receipt = _CrossOriginReceipt(
        resulting_state_commitment="2" * 64,
        current_state_commitment="3" * 64,
    )

    assert topology.state_commitment_for_next_event(receipt) == "3" * 64
    assert topology.state_commitment_for_next_event(receipt) != "2" * 64


def test_recovery_envelope_create_only_write_and_second_write_rejection(
    tmp_path: Path,
) -> None:
    envelope = _envelope()

    target = topology.write_recovery_envelope_create_only(
        evidence_root=tmp_path, envelope=envelope
    )

    assert target == tmp_path / "recovery-envelope.json"
    assert target.read_bytes() == _independent_canonical(_expected_envelope())
    with pytest.raises(topology.TopologyError, match="create-only"):
        topology.write_recovery_envelope_create_only(
            evidence_root=tmp_path, envelope=envelope
        )


def test_recovery_envelope_exact_section_7_1_content() -> None:
    envelope = _envelope()
    actual = envelope.to_json_value()
    expected = _expected_envelope()

    assert set(actual) == {
        "schema_version",
        "origin_binding_capability_sha256",
        "source_closure_sha256",
        "hypothesis_sha256",
        "validation_plan_sha256",
        "reserve_attempts",
        "event_operation_ids",
        "members",
        "expected_state_commitment",
    }
    assert actual == expected
    assert topology.canonical_recovery_envelope_bytes(envelope) == (
        _independent_canonical(expected)
    )
    assert [item["iteration_index"] for item in actual["reserve_attempts"]] == [
        0,
        1,
    ]
    assert [item["query_ordinal_start"] for item in actual["reserve_attempts"]] == [
        0,
        33,
    ]
    assert set(actual["event_operation_ids"]) == {
        "reserve_attempt_0",
        "abandon_attempt_0",
        "reserve_attempt_1",
        "batch_commit",
        "results_prepare",
        "results_open",
        "origin_terminal",
    }
    assert all(
        set(member) == {
            "iteration_index",
            "query_ordinal",
            "replicate_ordinal",
            "purpose",
            "candidate_wire",
            "candidate_salt",
            "result_evidence_salt",
            "constraint_salt",
            "evidence_path",
            "planned_campaign_run_identity",
        }
        for member in actual["members"]
    )


def test_tombstone_suffix_positive_boundaries() -> None:
    assert topology.validate_tombstone_suffix([False] * 33) == (False,) * 33
    assert topology.validate_tombstone_suffix([True] * 33) == (True,) * 33
    assert topology.validate_tombstone_suffix([False] * 8 + [True] * 25) == (
        (False,) * 8 + (True,) * 25
    )


def test_retry_allocation_is_exact_33_through_65() -> None:
    retry = _envelope().reserve_attempts[1]

    assert retry.iteration_index == 1
    assert retry.query_ordinal_start == 33
    assert tuple(range(retry.query_ordinal_start, retry.query_ordinal_start + 33)) == (
        tuple(range(33, 66))
    )
