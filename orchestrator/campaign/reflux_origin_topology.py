"""Logical reflux producer topology and its durable recovery envelope.

This module plans logical queries only.  It deliberately has no dependency on
the campaign runner and cannot start a physical campaign run.  Capability and
source-closure values cross this boundary only through opaque SHA-256 strings
or the narrow :class:`DigestReference` protocol.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, Sequence

from . import reflux_origin_ledger as ledger
from .reflux_ir import TriggerGateIR, encode_wire
from .reflux_origin_artifacts import (
    ArtifactError,
    canonical_json_bytes,
    write_json_create_only,
)


__all__ = [
    "RECOVERY_ENVELOPE_SCHEMA_VERSION",
    "SOURCE_AND_VALIDATION_MEMBER_COUNT",
    "VALIDATION_MASK_COUNT",
    "DigestReference",
    "ReceiptCommitments",
    "TopologyError",
    "MemberRecoveryMaterial",
    "TopologyMember",
    "EventOperationIds",
    "ReservationAttempt",
    "PlannedEventRequest",
    "RecoveryEnvelope",
    "build_logical_topology",
    "build_recovery_envelope",
    "canonical_recovery_envelope_bytes",
    "write_recovery_envelope_create_only",
    "validate_tombstone_suffix",
    "next_reservation_attempt",
    "expected_state_for_replay",
    "state_commitment_for_next_event",
]


RECOVERY_ENVELOPE_SCHEMA_VERSION = "reflux-recovery-envelope/v1"
VALIDATION_MASK_COUNT = 32
SOURCE_AND_VALIDATION_MEMBER_COUNT = 33
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_SALT_RE = re.compile(r"[0-9a-f]{32}\Z")


class TopologyError(ValueError):
    """Fail-closed rejection of an invalid topology or recovery plan."""


class DigestReference(Protocol):
    """The only object surface accepted for capability/closure references."""

    @property
    def sha256(self) -> str: ...


class ReceiptCommitments(Protocol):
    """Receipt surface needed to select the base for the next event."""

    @property
    def resulting_state_commitment(self) -> str: ...

    @property
    def current_state_commitment(self) -> str: ...


def _fail(message: str) -> None:
    raise TopologyError(message)


def _sha256(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{label} must be a lowercase SHA-256 digest")
    return value


def _digest(value: str | DigestReference, *, label: str) -> str:
    if type(value) is str:
        return _sha256(value, label=label)
    try:
        digest = value.sha256
    except Exception as exc:
        raise TopologyError(f"{label} must expose only an opaque sha256") from exc
    return _sha256(digest, label=label)


def _token(value: object, *, label: str) -> str:
    if (
        type(value) is not str
        or not value
        or any(character.isspace() for character in value)
    ):
        _fail(f"{label} must be a non-empty token")
    return value


def _salt(value: object, *, label: str) -> str:
    if (
        type(value) is not str
        or _SALT_RE.fullmatch(value) is None
        or not any(character != "0" for character in value)
    ):
        _fail(f"{label} must be a non-zero 128-bit lowercase hex salt")
    return value


def _relative_evidence_path(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        _fail("evidence path must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts:
        _fail("evidence path must stay beneath the evidence root")
    return value


@dataclass(frozen=True, slots=True)
class MemberRecoveryMaterial:
    """Caller-generated durable material for one logical query."""

    candidate_salt: str
    result_evidence_salt: str
    constraint_salt: str
    evidence_path: str
    planned_campaign_run_identity: str

    def __post_init__(self) -> None:
        _salt(self.candidate_salt, label="candidate salt")
        _salt(self.result_evidence_salt, label="result evidence salt")
        _salt(self.constraint_salt, label="constraint salt")
        _relative_evidence_path(self.evidence_path)
        _token(
            self.planned_campaign_run_identity,
            label="planned campaign-run identity",
        )


@dataclass(frozen=True, slots=True)
class TopologyMember:
    """One row in the exact source-plus-32-validation logical topology."""

    iteration_index: int
    query_ordinal: int
    replicate_ordinal: int
    purpose: str
    candidate_wire: str
    candidate_salt: str
    result_evidence_salt: str
    constraint_salt: str
    evidence_path: str
    planned_campaign_run_identity: str

    def __post_init__(self) -> None:
        _salt(self.candidate_salt, label="candidate salt")
        _salt(self.result_evidence_salt, label="result evidence salt")
        _salt(self.constraint_salt, label="constraint salt")
        _relative_evidence_path(self.evidence_path)
        _token(
            self.planned_campaign_run_identity,
            label="planned campaign-run identity",
        )

    def to_json_value(self) -> dict[str, object]:
        return {
            "iteration_index": self.iteration_index,
            "query_ordinal": self.query_ordinal,
            "replicate_ordinal": self.replicate_ordinal,
            "purpose": self.purpose,
            "candidate_wire": self.candidate_wire,
            "candidate_salt": self.candidate_salt,
            "result_evidence_salt": self.result_evidence_salt,
            "constraint_salt": self.constraint_salt,
            "evidence_path": self.evidence_path,
            "planned_campaign_run_identity": self.planned_campaign_run_identity,
        }


@dataclass(frozen=True, slots=True)
class EventOperationIds:
    """Stable authority-global operation IDs for every possible event."""

    reserve_attempt_0: str
    abandon_attempt_0: str
    reserve_attempt_1: str
    batch_commit: str
    results_prepare: str
    results_open: str
    origin_terminal: str

    def __post_init__(self) -> None:
        values = tuple(self.to_json_value().values())
        for name, value in self.to_json_value().items():
            _token(value, label=f"event operation ID {name}")
        if len(set(values)) != len(values):
            _fail("event operation IDs must be pairwise distinct")

    def to_json_value(self) -> dict[str, str]:
        return {
            "reserve_attempt_0": self.reserve_attempt_0,
            "abandon_attempt_0": self.abandon_attempt_0,
            "reserve_attempt_1": self.reserve_attempt_1,
            "batch_commit": self.batch_commit,
            "results_prepare": self.results_prepare,
            "results_open": self.results_open,
            "origin_terminal": self.origin_terminal,
        }


@dataclass(frozen=True, slots=True)
class ReservationAttempt:
    attempt: int
    batch_id: str
    iteration_index: int
    query_ordinal_start: int
    operation_id: str

    def __post_init__(self) -> None:
        _token(self.batch_id, label="batch ID")
        _token(self.operation_id, label="reserve operation ID")
        for label, value in (
            ("attempt", self.attempt),
            ("iteration index", self.iteration_index),
            ("query ordinal start", self.query_ordinal_start),
        ):
            if type(value) is not int or value < 0:
                _fail(f"{label} must be a non-negative integer")

    def to_json_value(self) -> dict[str, object]:
        return {
            "attempt": self.attempt,
            "batch_id": self.batch_id,
            "iteration_index": self.iteration_index,
            "query_ordinal_start": self.query_ordinal_start,
            "operation_id": self.operation_id,
        }


@dataclass(frozen=True, slots=True)
class PlannedEventRequest:
    """Original CAS base retained for byte-identical replay of one event."""

    operation_id: str
    expected_state_commitment: str

    def __post_init__(self) -> None:
        _token(self.operation_id, label="operation ID")
        _sha256(self.expected_state_commitment, label="expected state commitment")


@dataclass(frozen=True, slots=True)
class RecoveryEnvelope:
    """Create-only material written before the first ``BatchReserved``."""

    origin_binding_capability_sha256: str
    source_closure_sha256: str
    hypothesis_sha256: str
    validation_plan_sha256: str
    reserve_attempts: tuple[ReservationAttempt, ReservationAttempt]
    event_operation_ids: EventOperationIds
    members: tuple[TopologyMember, ...]
    expected_state_commitment: str
    schema_version: str = RECOVERY_ENVELOPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RECOVERY_ENVELOPE_SCHEMA_VERSION:
            _fail("invalid recovery envelope schema version")
        for label, value in (
            ("capability digest", self.origin_binding_capability_sha256),
            ("source closure digest", self.source_closure_sha256),
            ("hypothesis digest", self.hypothesis_sha256),
            ("validation plan digest", self.validation_plan_sha256),
            ("expected state commitment", self.expected_state_commitment),
        ):
            _sha256(value, label=label)
        if type(self.event_operation_ids) is not EventOperationIds:
            _fail("invalid event operation IDs")
        _validate_reservation_attempts(self.reserve_attempts, self.event_operation_ids)
        _validate_members(self.members)

    def to_json_value(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "origin_binding_capability_sha256": self.origin_binding_capability_sha256,
            "source_closure_sha256": self.source_closure_sha256,
            "hypothesis_sha256": self.hypothesis_sha256,
            "validation_plan_sha256": self.validation_plan_sha256,
            "reserve_attempts": [
                item.to_json_value() for item in self.reserve_attempts
            ],
            "event_operation_ids": self.event_operation_ids.to_json_value(),
            "members": [member.to_json_value() for member in self.members],
            "expected_state_commitment": self.expected_state_commitment,
        }


def _validate_reservation_attempts(
    attempts: tuple[ReservationAttempt, ReservationAttempt],
    operation_ids: EventOperationIds,
) -> None:
    if type(attempts) is not tuple or len(attempts) != 2:
        _fail("recovery envelope must contain exactly two reserve attempts")
    expected = (
        (0, 0, 0, operation_ids.reserve_attempt_0),
        (1, 1, 33, operation_ids.reserve_attempt_1),
    )
    for item, values in zip(attempts, expected, strict=True):
        if type(item) is not ReservationAttempt:
            _fail("invalid reservation attempt")
        attempt, iteration, query_start, operation_id = values
        if (
            item.attempt,
            item.iteration_index,
            item.query_ordinal_start,
            item.operation_id,
        ) != (attempt, iteration, query_start, operation_id):
            _fail("reserve attempt allocation differs from the fixed recovery plan")
        _token(item.batch_id, label="batch ID")
    if attempts[0].batch_id == attempts[1].batch_id:
        _fail("reserve attempts must use distinct batch IDs")


def _validate_members(members: tuple[TopologyMember, ...]) -> None:
    if type(members) is not tuple or len(members) != SOURCE_AND_VALIDATION_MEMBER_COUNT:
        _fail("topology must contain exactly 33 members")
    source = members[0]
    if (
        type(source.candidate_wire) is not str
        or len(source.candidate_wire) != 5
        or any(character not in ("0", "1") for character in source.candidate_wire)
    ):
        _fail("source candidate wire is invalid")
    source_mask = sum(
        (character == "1") << bit for bit, character in enumerate(source.candidate_wire)
    )
    expected_rows = [(0, 0, encode_wire(TriggerGateIR(source_mask)), 0, "source")]
    expected_rows.extend(
        (
            0,
            1 + mask,
            encode_wire(TriggerGateIR(mask)),
            1 if mask == source_mask else 0,
            "p6-validation",
        )
        for mask in range(VALIDATION_MASK_COUNT)
    )
    observed = [
        (
            member.iteration_index,
            member.query_ordinal,
            member.candidate_wire,
            member.replicate_ordinal,
            member.purpose,
        )
        for member in members
    ]
    if observed != expected_rows:
        _fail("members differ from the exact 33-row topology")
    if len({member.candidate_wire for member in members}) != VALIDATION_MASK_COUNT:
        _fail("topology must contain exactly 32 distinct candidates")
    run_ids = [member.planned_campaign_run_identity for member in members]
    if len(set(run_ids)) != SOURCE_AND_VALIDATION_MEMBER_COUNT:
        _fail("each logical query must have a distinct planned campaign-run identity")
    paths = [member.evidence_path for member in members]
    if len(set(paths)) != SOURCE_AND_VALIDATION_MEMBER_COUNT:
        _fail("each logical query must have a distinct deterministic evidence path")


def build_logical_topology(
    *,
    source_mask: int,
    member_materials: Sequence[MemberRecoveryMaterial],
) -> tuple[TopologyMember, ...]:
    """Build the one permitted fresh-origin source-plus-mask topology."""

    try:
        source_wire = encode_wire(TriggerGateIR(source_mask))
    except (TypeError, ValueError) as exc:
        raise TopologyError("source mask must be an integer in 0..31") from exc
    materials = tuple(member_materials)
    if len(materials) != SOURCE_AND_VALIDATION_MEMBER_COUNT or any(
        type(item) is not MemberRecoveryMaterial for item in materials
    ):
        _fail("exactly 33 member recovery materials are required")
    wires = (source_wire,) + tuple(
        encode_wire(TriggerGateIR(mask)) for mask in range(VALIDATION_MASK_COUNT)
    )
    members = []
    rows = zip(wires, materials, strict=True)
    for query_ordinal, (wire, material) in enumerate(rows):
        mask = source_mask if query_ordinal == 0 else query_ordinal - 1
        members.append(
            TopologyMember(
                iteration_index=0,
                query_ordinal=query_ordinal,
                replicate_ordinal=(
                    0 if query_ordinal == 0 else (1 if mask == source_mask else 0)
                ),
                purpose="source" if query_ordinal == 0 else "p6-validation",
                candidate_wire=wire,
                candidate_salt=material.candidate_salt,
                result_evidence_salt=material.result_evidence_salt,
                constraint_salt=material.constraint_salt,
                evidence_path=material.evidence_path,
                planned_campaign_run_identity=material.planned_campaign_run_identity,
            )
        )
    result = tuple(members)
    _validate_members(result)
    return result


def build_recovery_envelope(
    *,
    capability_digest: str | DigestReference,
    source_closure_digest: str | DigestReference,
    hypothesis_sha256: str,
    validation_plan_sha256: str,
    attempt_0_batch_id: str,
    retry_1_batch_id: str,
    event_operation_ids: EventOperationIds,
    source_mask: int,
    member_materials: Sequence[MemberRecoveryMaterial],
    initial_expected_state_commitment: str,
) -> RecoveryEnvelope:
    """Fix all logical and replay material before the first reservation."""

    attempts = (
        ReservationAttempt(
            attempt=0,
            batch_id=attempt_0_batch_id,
            iteration_index=0,
            query_ordinal_start=0,
            operation_id=event_operation_ids.reserve_attempt_0,
        ),
        ReservationAttempt(
            attempt=1,
            batch_id=retry_1_batch_id,
            iteration_index=1,
            query_ordinal_start=33,
            operation_id=event_operation_ids.reserve_attempt_1,
        ),
    )
    return RecoveryEnvelope(
        origin_binding_capability_sha256=_digest(
            capability_digest, label="capability digest"
        ),
        source_closure_sha256=_digest(
            source_closure_digest, label="source closure digest"
        ),
        hypothesis_sha256=_sha256(hypothesis_sha256, label="hypothesis digest"),
        validation_plan_sha256=_sha256(
            validation_plan_sha256, label="validation plan digest"
        ),
        reserve_attempts=attempts,
        event_operation_ids=event_operation_ids,
        members=build_logical_topology(
            source_mask=source_mask, member_materials=member_materials
        ),
        expected_state_commitment=_sha256(
            initial_expected_state_commitment,
            label="initial expected state commitment",
        ),
    )


def canonical_recovery_envelope_bytes(envelope: RecoveryEnvelope) -> bytes:
    if type(envelope) is not RecoveryEnvelope:
        _fail("invalid recovery envelope")
    return canonical_json_bytes(envelope.to_json_value())


def write_recovery_envelope_create_only(
    *,
    evidence_root: Path,
    envelope: RecoveryEnvelope,
    relative_path: Path = Path("recovery-envelope.json"),
) -> Path:
    """Persist and read back the envelope through the shared A0 primitive."""

    if type(envelope) is not RecoveryEnvelope:
        _fail("invalid recovery envelope")
    try:
        return write_json_create_only(
            root=Path(evidence_root),
            relative_path=Path(relative_path),
            value=envelope.to_json_value(),
        )
    except ArtifactError as exc:
        raise TopologyError("recovery envelope create-only write failed") from exc


def validate_tombstone_suffix(tombstones: Sequence[bool]) -> tuple[bool, ...]:
    """Accept only an exact 33-row terminal tombstone suffix."""

    values = tuple(tombstones)
    if len(values) != SOURCE_AND_VALIDATION_MEMBER_COUNT or any(
        type(value) is not bool for value in values
    ):
        _fail("tombstone vector must contain exactly 33 booleans")
    suffix_started = False
    for value in values:
        if value:
            suffix_started = True
        elif suffix_started:
            _fail("tombstones must form a terminal suffix")
    return values


def next_reservation_attempt(
    *,
    envelope: RecoveryEnvelope,
    events: Sequence[object],
) -> ReservationAttempt:
    """Return the only permitted reserve attempt after a ledger event prefix."""

    if type(envelope) is not RecoveryEnvelope:
        _fail("invalid recovery envelope")
    open_batch_id: str | None = None
    next_index = 0
    committed = False
    for event in events:
        if type(event) is ledger.BatchReserved:
            if committed or open_batch_id is not None or next_index >= 2:
                _fail("reservation event sequence is invalid")
            planned = envelope.reserve_attempts[next_index]
            if (
                event.batch_id,
                event.iteration_index,
                event.member_row_count,
                event.query_ordinal_start,
            ) != (
                planned.batch_id,
                planned.iteration_index,
                SOURCE_AND_VALIDATION_MEMBER_COUNT,
                planned.query_ordinal_start,
            ):
                _fail("reserved batch differs from the fixed recovery plan")
            open_batch_id = event.batch_id
        elif type(event) is ledger.BatchReservationAbandoned:
            if committed or open_batch_id is None or event.batch_id != open_batch_id:
                _fail("reservation abandonment is not for the open pre-commit batch")
            open_batch_id = None
            next_index += 1
            if next_index > 1:
                _fail("only one pre-commit re-reservation is permitted")
        elif type(event) is ledger.BatchCommitted:
            if committed or open_batch_id is None or event.batch_id != open_batch_id:
                _fail("batch commit is not for the open reservation")
            committed = True
            open_batch_id = None
        elif type(event) in (
            ledger.BatchResultsPrepared,
            ledger.BatchSealed,
            ledger.OriginSealed,
        ):
            committed = True
        else:
            _fail("unsupported event in reservation history")
    if committed:
        _fail("a committed batch cannot escape to another batch")
    if open_batch_id is not None:
        _fail("a reservation is already open")
    if next_index >= len(envelope.reserve_attempts):
        _fail("no reserve attempt remains")
    return envelope.reserve_attempts[next_index]


def expected_state_for_replay(request: PlannedEventRequest) -> str:
    """Reuse event E's original CAS base when E's receipt was lost."""

    if type(request) is not PlannedEventRequest:
        _fail("invalid planned event request")
    return request.expected_state_commitment


def state_commitment_for_next_event(receipt: ReceiptCommitments) -> str:
    """Use the authority-current base, including intervening origin commits."""

    return receipt.current_state_commitment
