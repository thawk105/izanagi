"""B-4 scheduled registry, analysis manifest, and assignment schedule.

The scheduled registry can only be sealed from one issuer-bound batch receipt.
That receipt binds the complete normalized batch, but this module does not create
or identify the authoritative producer.  Consequently it does not claim to close
the file-drawer risk while that producer is absent.

Assignment is derived reproducibly from an issuer-bound seed receipt with a
domain-separated HMAC-SHA256 bit.  This module neither proves that the seed was
uniform nor that it was issued before outcomes were observed.  Those properties
remain obligations of the receipt issuer.

No clock, environment, implicit randomness, file system, or mutable global state
is consulted.  The B-4 state machine is independent of ``attempt_registry_core``;
only its stateless canonical-JSON and chained-row primitives are reused.
"""

from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction
import hashlib
import hmac
import json
from typing import Sequence

from .attempt_registry_core import canonical_json_bytes, chained_event_row
from .p3_b4_analysis_contract import (
    B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
    B4Arm,
    B4ContractBinding,
    B4ContractBlockBinding,
    B4ExactRatio,
    B4RegistryViolationReason,
    EXPECTED_BLOCK_COUNT,
)


B4_SCHEDULE_RECEIPT_SCHEMA_VERSION = "p3-b4-schedule-receipt/v1"
B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION = "p3-b4-scheduled-attempt/v1"
B4_SCHEDULED_REGISTRY_SCHEMA_VERSION = "p3-b4-scheduled-registry/v1"
B4_REGISTRY_EVENT_SCHEMA_VERSION = "p3-b4-registry-event/v1"
B4_REGISTRY_VIOLATION_SCHEMA_VERSION = "p3-b4-registry-violation/v1"
B4_ASSIGNMENT_SEED_SCHEMA_VERSION = "p3-b4-assignment-seed/v1"
B4_ANALYSIS_MANIFEST_SCHEMA_VERSION = "p3-b4-analysis-manifest/v1"
B4_ANALYSIS_MANIFEST_ROW_SCHEMA_VERSION = "p3-b4-analysis-manifest-row/v1"
B4_DESIGN_NOT_FEASIBLE_SCHEMA_VERSION = "p3-b4-design-not-feasible/v1"
B4_MANIFEST_COMPLETENESS_SCHEMA_VERSION = "p3-b4-manifest-completeness/v1"
B4_EXECUTION_ASSIGNMENT_SCHEMA_VERSION = "p3-b4-execution-assignment/v1"

_ZERO_SHA256 = "0" * 64
_ASSIGNMENT_DOMAIN = b"p3-b4-assignment/v1\x00"
_ELIGIBLE_RED_CLASSES = frozenset(
    {
        "verify-red",
        "liveness",
        "other",
        "diff-quarantine",
    }
)


class B4LedgerError(ValueError):
    """A B-4 ledger or receipt failed its closed schema contract."""


class B4DesignNotFeasibleError(B4LedgerError):
    """A frozen manifest was infeasible or changed after generation."""


class B4ScheduledAttemptReason(str, Enum):
    """Closed vocabulary retained for every scheduled attempt."""

    SCHEDULED = "scheduled"
    GENERATION_FAILED = "generation_failed"
    RED_NOT_REPRODUCED = "red_not_reproduced"
    DUPLICATE = "duplicate"
    CORRUPT = "corrupt"
    SCREENING_ONLY_RED = "screening_only_red"


class B4WhiteboardResult(str, Enum):
    """Closed precursor whiteboard result vocabulary."""

    REJECTED = "rejected"
    SUCCESS = "success"
    FAILED = "failed"
    MISSING = "missing"


class B4DigestRedClass(str, Enum):
    """Red classes recorded before B-4 treatment assignment."""

    VERIFY_RED = "verify-red"
    LIVENESS = "liveness"
    OTHER = "other"
    DIFF_QUARANTINE = "diff-quarantine"
    SCREENING = "screening"


class B4AssignmentArmOrder(str, Enum):
    """The two possible execution-slot orders for a B-4 block."""

    ON_FIRST = "on-first"
    OFF_FIRST = "off-first"


class B4ManifestState(str, Enum):
    """Closed wire reason for a manifest that cannot be generated."""

    DESIGN_NOT_FEASIBLE = "design_not_feasible"


@dataclass(frozen=True, slots=True)
class B4ScheduleReceipt:
    """Issuer-bound commitment to one complete normalized scheduled batch."""

    schema_version: str
    issuer_sha256: str
    scheduled_inputs_sha256: str
    scheduled_attempt_count: int


@dataclass(frozen=True, slots=True)
class B4ScheduledAttemptInput:
    """One scheduled attempt, including non-eligible and failed attempts."""

    schema_version: str
    attempt_id: str
    registry_ordinal: int
    block_id: str | None
    driver: str
    reason: B4ScheduledAttemptReason
    whiteboard_result: B4WhiteboardResult
    digest_red_classes: tuple[B4DigestRedClass, ...]
    workload: str
    calibrated_workload_member: bool
    initial_proposal_sha256: str
    bootstrap_member: bool
    reference_tps: B4ExactRatio | None
    reference_snapshot_hash: str | None
    reference_receipt_hash: str | None
    reference_is_unique: bool
    arm_digest_received: bool


@dataclass(frozen=True, slots=True)
class B4RegistryViolation:
    """One append-only protocol-violation event."""

    schema_version: str
    attempt_id: str | None
    block_id: str | None
    reason: B4RegistryViolationReason
    evidence_sha256: str


@dataclass(frozen=True, slots=True)
class B4ScheduledAttemptRegistry:
    """Sealed scheduled batch plus append-only violation events."""

    schema_version: str
    schedule_receipt: B4ScheduleReceipt
    scheduled_attempts: tuple[B4ScheduledAttemptInput, ...]
    violations: tuple[B4RegistryViolation, ...]
    sealed_prefix_sha256: str
    canonical_bytes: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class B4RandomizationSeedRecord:
    """Issuer-bound external seed receipt; no implicit seed is permitted."""

    schema_version: str
    seed_hex: str
    registry_prefix_sha256: str
    issuer_sha256: str
    source_receipt_sha256: str


@dataclass(frozen=True, slots=True)
class B4AnalysisManifestRow:
    """One selected block with its frozen reference and execution schedule."""

    schema_version: str
    attempt_id: str
    block_id: str
    driver: str
    reference_tps: B4ExactRatio
    reference_snapshot_hash: str
    reference_receipt_hash: str
    assignment_order: B4AssignmentArmOrder

    @property
    def assignment_schedule(self) -> tuple[B4Arm, B4Arm]:
        if self.assignment_order is B4AssignmentArmOrder.ON_FIRST:
            return (B4Arm.ON, B4Arm.OFF)
        return (B4Arm.OFF, B4Arm.ON)


@dataclass(frozen=True, slots=True)
class B4AnalysisManifest:
    """The exact first 201 eligible registry rows and their assignments."""

    schema_version: str
    registry_prefix_sha256: str
    schedule_receipt_sha256: str
    seed_receipt: B4RandomizationSeedRecord
    rows: tuple[B4AnalysisManifestRow, ...]
    canonical_bytes: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class B4DesignNotFeasible:
    """Fail-closed result returned instead of a short manifest."""

    schema_version: str
    reason: B4ManifestState
    eligible_count: int
    required_count: int


@dataclass(frozen=True, slots=True)
class B4ManifestCompletenessReceipt:
    """Exact regeneration result, including the unfiltered violation count."""

    schema_version: str
    manifest_sha256: str
    registry_sha256: str
    registry_prefix_sha256: str
    schedule_issuer_sha256: str
    seed_issuer_sha256: str
    row_count: int
    registry_violation_count: int


@dataclass(frozen=True, slots=True)
class B4ExecutionAssignmentObservation:
    """Observed execution-slot order for one manifest block."""

    schema_version: str
    block_id: str
    observed_schedule: tuple[B4Arm, B4Arm]


def _fail(message: str) -> None:
    raise B4LedgerError(message)


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_text(value: object) -> bool:
    return type(value) is str and bool(value) and value.strip() == value


def _exact_ratio(value: object) -> Fraction | None:
    if type(value) is int:
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    if (
        type(value) is tuple
        and len(value) == 2
        and type(value[0]) is int
        and type(value[1]) is int
        and value[1] != 0
    ):
        return Fraction(value[0], value[1])
    return None


def _ratio_payload(value: B4ExactRatio | None) -> list[int] | None:
    if value is None:
        return None
    exact = _exact_ratio(value)
    if exact is None:
        _fail("reference_tps is not an exact rational")
    return [exact.numerator, exact.denominator]


def _ratio_from_payload(value: object) -> tuple[int, int] | None:
    if value is None:
        return None
    if (
        type(value) is not list
        or len(value) != 2
        or type(value[0]) is not int
        or type(value[1]) is not int
        or value[1] <= 0
    ):
        _fail("wire reference_tps is not a canonical ratio")
    exact = Fraction(value[0], value[1])
    if [exact.numerator, exact.denominator] != value:
        _fail("wire reference_tps is not reduced")
    return (exact.numerator, exact.denominator)


def _validate_attempt(attempt: object) -> B4ScheduledAttemptInput:
    if not isinstance(attempt, B4ScheduledAttemptInput):
        _fail("scheduled batch contains a non-B4ScheduledAttemptInput value")
    if attempt.schema_version != B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION:
        _fail("scheduled attempt schema version mismatch")
    if not _is_text(attempt.attempt_id):
        _fail("attempt_id is invalid")
    if type(attempt.registry_ordinal) is not int or attempt.registry_ordinal < 0:
        _fail("registry_ordinal is invalid")
    if attempt.block_id is not None and not _is_text(attempt.block_id):
        _fail("block_id is invalid")
    if not _is_text(attempt.driver) or not _is_text(attempt.workload):
        _fail("driver or workload is invalid")
    if not isinstance(attempt.reason, B4ScheduledAttemptReason):
        _fail("scheduled attempt reason is not recognized")
    if not isinstance(attempt.whiteboard_result, B4WhiteboardResult):
        _fail("whiteboard result is not recognized")
    if type(attempt.digest_red_classes) is not tuple:
        _fail("digest_red_classes must be a tuple")
    if any(
        not isinstance(red_class, B4DigestRedClass)
        for red_class in attempt.digest_red_classes
    ):
        _fail("digest red class is not recognized")
    if len(set(attempt.digest_red_classes)) != len(attempt.digest_red_classes):
        _fail("digest red classes contain duplicates")
    for value in (
        attempt.calibrated_workload_member,
        attempt.bootstrap_member,
        attempt.reference_is_unique,
        attempt.arm_digest_received,
    ):
        if type(value) is not bool:
            _fail("scheduled attempt predicate is not boolean")
    if not _is_sha256(attempt.initial_proposal_sha256):
        _fail("initial proposal hash is invalid")
    reference = _exact_ratio(attempt.reference_tps)
    if attempt.reference_tps is not None and (reference is None or reference <= 0):
        _fail("reference_tps is invalid")
    if reference is not None:
        denominator = reference.denominator
        while denominator % 2 == 0:
            denominator //= 2
        while denominator % 5 == 0:
            denominator //= 5
        if denominator != 1:
            _fail("reference_tps has no finite decimal expansion")
    for value in (
        attempt.reference_snapshot_hash,
        attempt.reference_receipt_hash,
    ):
        if value is not None and not _is_sha256(value):
            _fail("reference source hash is invalid")
    if attempt.reason is B4ScheduledAttemptReason.SCHEDULED:
        if (
            attempt.block_id is None
            or reference is None
            or reference <= 0
            or not _is_sha256(attempt.reference_snapshot_hash)
            or not _is_sha256(attempt.reference_receipt_hash)
        ):
            _fail("scheduled candidate lacks a complete block reference")
    return attempt


def _attempt_payload(attempt: B4ScheduledAttemptInput) -> dict[str, object]:
    _validate_attempt(attempt)
    return {
        "schema_version": attempt.schema_version,
        "attempt_id": attempt.attempt_id,
        "registry_ordinal": attempt.registry_ordinal,
        "block_id": attempt.block_id,
        "driver": attempt.driver,
        "reason": attempt.reason.value,
        "whiteboard_result": attempt.whiteboard_result.value,
        "digest_red_classes": sorted(
            red_class.value for red_class in attempt.digest_red_classes
        ),
        "workload": attempt.workload,
        "calibrated_workload_member": attempt.calibrated_workload_member,
        "initial_proposal_sha256": attempt.initial_proposal_sha256,
        "bootstrap_member": attempt.bootstrap_member,
        "reference_tps": _ratio_payload(attempt.reference_tps),
        "reference_snapshot_hash": attempt.reference_snapshot_hash,
        "reference_receipt_hash": attempt.reference_receipt_hash,
        "reference_is_unique": attempt.reference_is_unique,
        "arm_digest_received": attempt.arm_digest_received,
    }


def _attempt_from_payload(value: object) -> B4ScheduledAttemptInput:
    if type(value) is not dict:
        _fail("scheduled-attempt payload is not an object")
    expected = {
        "schema_version",
        "attempt_id",
        "registry_ordinal",
        "block_id",
        "driver",
        "reason",
        "whiteboard_result",
        "digest_red_classes",
        "workload",
        "calibrated_workload_member",
        "initial_proposal_sha256",
        "bootstrap_member",
        "reference_tps",
        "reference_snapshot_hash",
        "reference_receipt_hash",
        "reference_is_unique",
        "arm_digest_received",
    }
    if set(value) != expected:
        _fail("scheduled-attempt payload key set mismatch")
    red_classes = value["digest_red_classes"]
    if type(red_classes) is not list:
        _fail("wire digest_red_classes is not a list")
    try:
        attempt = B4ScheduledAttemptInput(
            schema_version=value["schema_version"],
            attempt_id=value["attempt_id"],
            registry_ordinal=value["registry_ordinal"],
            block_id=value["block_id"],
            driver=value["driver"],
            reason=B4ScheduledAttemptReason(value["reason"]),
            whiteboard_result=B4WhiteboardResult(value["whiteboard_result"]),
            digest_red_classes=tuple(B4DigestRedClass(item) for item in red_classes),
            workload=value["workload"],
            calibrated_workload_member=value["calibrated_workload_member"],
            initial_proposal_sha256=value["initial_proposal_sha256"],
            bootstrap_member=value["bootstrap_member"],
            reference_tps=_ratio_from_payload(value["reference_tps"]),
            reference_snapshot_hash=value["reference_snapshot_hash"],
            reference_receipt_hash=value["reference_receipt_hash"],
            reference_is_unique=value["reference_is_unique"],
            arm_digest_received=value["arm_digest_received"],
        )
    except (TypeError, ValueError) as exc:
        raise B4LedgerError("scheduled-attempt enum value is invalid") from exc
    return _validate_attempt(attempt)


def _normalize_attempts(
    scheduled_inputs: Sequence[B4ScheduledAttemptInput],
) -> tuple[B4ScheduledAttemptInput, ...]:
    if type(scheduled_inputs) not in (list, tuple):
        _fail("scheduled_inputs must be a complete list or tuple")
    canonical_attempts: list[B4ScheduledAttemptInput] = []
    for item in scheduled_inputs:
        attempt = _validate_attempt(item)
        exact_reference = _exact_ratio(attempt.reference_tps)
        canonical_attempts.append(
            replace(
                attempt,
                digest_red_classes=tuple(
                    sorted(attempt.digest_red_classes, key=lambda value: value.value)
                ),
                reference_tps=(
                    None
                    if exact_reference is None
                    else (exact_reference.numerator, exact_reference.denominator)
                ),
            )
        )
    attempts = tuple(canonical_attempts)
    attempt_ids = [item.attempt_id for item in attempts]
    if len(set(attempt_ids)) != len(attempt_ids):
        _fail("scheduled attempt ids are not unique")
    block_ids = [item.block_id for item in attempts if item.block_id is not None]
    if len(set(block_ids)) != len(block_ids):
        _fail("scheduled block ids are not unique")
    return tuple(sorted(attempts, key=lambda item: (item.registry_ordinal, item.attempt_id)))


def scheduled_attempts_sha256(
    scheduled_inputs: Sequence[B4ScheduledAttemptInput],
) -> str:
    """Hash the complete normalized batch independently of caller permutation."""

    normalized = _normalize_attempts(scheduled_inputs)
    payload = {
        "schema_version": B4_SCHEDULE_RECEIPT_SCHEMA_VERSION,
        "scheduled_attempts": [_attempt_payload(item) for item in normalized],
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _validate_schedule_receipt(
    receipt: object,
    attempts: Sequence[B4ScheduledAttemptInput],
) -> B4ScheduleReceipt:
    if not isinstance(receipt, B4ScheduleReceipt):
        _fail("an issuer-bound schedule receipt is required")
    if receipt.schema_version != B4_SCHEDULE_RECEIPT_SCHEMA_VERSION:
        _fail("schedule receipt schema version mismatch")
    if not _is_sha256(receipt.issuer_sha256):
        _fail("schedule receipt issuer hash is invalid")
    if not _is_sha256(receipt.scheduled_inputs_sha256):
        _fail("schedule receipt batch hash is invalid")
    if (
        type(receipt.scheduled_attempt_count) is not int
        or receipt.scheduled_attempt_count < 0
    ):
        _fail("schedule receipt count is invalid")
    normalized = _normalize_attempts(attempts)
    if receipt.scheduled_attempt_count != len(normalized):
        _fail("schedule receipt count does not match the sealed batch")
    if receipt.scheduled_inputs_sha256 != scheduled_attempts_sha256(normalized):
        _fail("schedule receipt does not bind the sealed batch")
    return receipt


def _schedule_receipt_payload(receipt: B4ScheduleReceipt) -> dict[str, object]:
    return {
        "schema_version": receipt.schema_version,
        "issuer_sha256": receipt.issuer_sha256,
        "scheduled_inputs_sha256": receipt.scheduled_inputs_sha256,
        "scheduled_attempt_count": receipt.scheduled_attempt_count,
    }


def _schedule_receipt_from_payload(value: object) -> B4ScheduleReceipt:
    if type(value) is not dict or set(value) != {
        "schema_version",
        "issuer_sha256",
        "scheduled_inputs_sha256",
        "scheduled_attempt_count",
    }:
        _fail("schedule receipt payload key set mismatch")
    return B4ScheduleReceipt(
        schema_version=value["schema_version"],
        issuer_sha256=value["issuer_sha256"],
        scheduled_inputs_sha256=value["scheduled_inputs_sha256"],
        scheduled_attempt_count=value["scheduled_attempt_count"],
    )


def _schedule_receipt_sha256(receipt: B4ScheduleReceipt) -> str:
    return hashlib.sha256(canonical_json_bytes(_schedule_receipt_payload(receipt))).hexdigest()


def _validate_violation(value: object) -> B4RegistryViolation:
    if not isinstance(value, B4RegistryViolation):
        _fail("registry violation has the wrong type")
    if value.schema_version != B4_REGISTRY_VIOLATION_SCHEMA_VERSION:
        _fail("registry violation schema version mismatch")
    if value.attempt_id is not None and not _is_text(value.attempt_id):
        _fail("violation attempt_id is invalid")
    if value.block_id is not None and not _is_text(value.block_id):
        _fail("violation block_id is invalid")
    if not isinstance(value.reason, B4RegistryViolationReason):
        _fail("registry violation reason is not recognized")
    if not _is_sha256(value.evidence_sha256):
        _fail("registry violation evidence hash is invalid")
    return value


def _violation_payload(value: B4RegistryViolation) -> dict[str, object]:
    _validate_violation(value)
    return {
        "schema_version": value.schema_version,
        "attempt_id": value.attempt_id,
        "block_id": value.block_id,
        "reason": value.reason.value,
        "evidence_sha256": value.evidence_sha256,
    }


def _violation_from_payload(value: object) -> B4RegistryViolation:
    if type(value) is not dict or set(value) != {
        "schema_version",
        "attempt_id",
        "block_id",
        "reason",
        "evidence_sha256",
    }:
        _fail("registry violation payload key set mismatch")
    try:
        violation = B4RegistryViolation(
            schema_version=value["schema_version"],
            attempt_id=value["attempt_id"],
            block_id=value["block_id"],
            reason=B4RegistryViolationReason(value["reason"]),
            evidence_sha256=value["evidence_sha256"],
        )
    except (TypeError, ValueError) as exc:
        raise B4LedgerError("registry violation reason is not recognized") from exc
    return _validate_violation(violation)


def _registry_rows(
    *,
    receipt: B4ScheduleReceipt,
    attempts: tuple[B4ScheduledAttemptInput, ...],
    violations: tuple[B4RegistryViolation, ...],
) -> tuple[dict[str, object], ...]:
    bases: list[dict[str, object]] = [
        {
            "schema_version": B4_REGISTRY_EVENT_SCHEMA_VERSION,
            "event": "registry-genesis",
            "registry_schema_version": B4_SCHEDULED_REGISTRY_SCHEMA_VERSION,
            "schedule_receipt": _schedule_receipt_payload(receipt),
        }
    ]
    bases.extend(
        {
            "schema_version": B4_REGISTRY_EVENT_SCHEMA_VERSION,
            "event": "scheduled-attempt",
            "attempt": _attempt_payload(attempt),
        }
        for attempt in attempts
    )
    bases.extend(
        {
            "schema_version": B4_REGISTRY_EVENT_SCHEMA_VERSION,
            "event": "protocol-violation",
            "violation": _violation_payload(violation),
        }
        for violation in violations
    )
    rows: list[dict[str, object]] = []
    previous = _ZERO_SHA256
    for event_index, base in enumerate(bases):
        row = chained_event_row(
            base,
            event_index=event_index,
            previous_event_sha256=previous,
        )
        rows.append(row)
        previous = row["event_sha256"]
    return tuple(rows)


def _registry_bytes(rows: Sequence[dict[str, object]]) -> bytes:
    return b"".join(canonical_json_bytes(row) + b"\n" for row in rows)


def _build_registry(
    *,
    receipt: B4ScheduleReceipt,
    attempts: Sequence[B4ScheduledAttemptInput],
    violations: Sequence[B4RegistryViolation],
) -> B4ScheduledAttemptRegistry:
    normalized = _normalize_attempts(attempts)
    _validate_schedule_receipt(receipt, normalized)
    violation_tuple = tuple(_validate_violation(item) for item in violations)
    rows = _registry_rows(
        receipt=receipt,
        attempts=normalized,
        violations=violation_tuple,
    )
    prefix_rows = rows[: 1 + len(normalized)]
    prefix_bytes = _registry_bytes(prefix_rows)
    data = _registry_bytes(rows)
    return B4ScheduledAttemptRegistry(
        schema_version=B4_SCHEDULED_REGISTRY_SCHEMA_VERSION,
        schedule_receipt=receipt,
        scheduled_attempts=normalized,
        violations=violation_tuple,
        sealed_prefix_sha256=hashlib.sha256(prefix_bytes).hexdigest(),
        canonical_bytes=data,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def seal_scheduled_attempt_registry(
    *,
    scheduled_inputs: Sequence[B4ScheduledAttemptInput],
    schedule_receipt: B4ScheduleReceipt,
) -> B4ScheduledAttemptRegistry:
    """Normalize one complete batch and seal it; no single-attempt API exists."""

    normalized = _normalize_attempts(scheduled_inputs)
    _validate_schedule_receipt(schedule_receipt, normalized)
    return _build_registry(
        receipt=schedule_receipt,
        attempts=normalized,
        violations=(),
    )


def assert_scheduled_registry_complete(
    *,
    registry: B4ScheduledAttemptRegistry,
    schedule_receipt: B4ScheduleReceipt,
) -> None:
    """Check the registry against its issuer receipt, never a caller list."""

    if not isinstance(registry, B4ScheduledAttemptRegistry):
        _fail("scheduled registry has the wrong type")
    if registry.schema_version != B4_SCHEDULED_REGISTRY_SCHEMA_VERSION:
        _fail("scheduled registry schema version mismatch")
    if not isinstance(schedule_receipt, B4ScheduleReceipt):
        _fail("an issuer-bound schedule receipt is required")
    if registry.schedule_receipt != schedule_receipt:
        _fail("registry is bound to a different schedule receipt")
    rebuilt = _build_registry(
        receipt=schedule_receipt,
        attempts=registry.scheduled_attempts,
        violations=registry.violations,
    )
    if rebuilt != registry:
        _fail("scheduled registry is not its exact canonical regeneration")


def load_scheduled_attempt_registry(data: bytes) -> B4ScheduledAttemptRegistry:
    """Strictly load canonical JSONL and verify every chained event."""

    if type(data) is not bytes or not data or not data.endswith(b"\n"):
        _fail("registry bytes must be non-empty canonical JSONL")
    lines = data.splitlines()
    parsed: list[dict[str, object]] = []
    for line in lines:
        try:
            row = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B4LedgerError("registry row is not strict UTF-8 JSON") from exc
        if type(row) is not dict or canonical_json_bytes(row) != line:
            _fail("registry row is not canonical JSON")
        parsed.append(row)
    if not parsed:
        _fail("registry has no genesis row")
    genesis = parsed[0]
    base_keys = {
        "schema_version",
        "event",
        "event_index",
        "previous_event_sha256",
        "event_sha256",
    }
    if set(genesis) != base_keys | {
        "registry_schema_version",
        "schedule_receipt",
    }:
        _fail("registry genesis key set mismatch")
    if (
        genesis["schema_version"] != B4_REGISTRY_EVENT_SCHEMA_VERSION
        or genesis["event"] != "registry-genesis"
        or genesis["registry_schema_version"] != B4_SCHEDULED_REGISTRY_SCHEMA_VERSION
    ):
        _fail("registry genesis value mismatch")
    receipt = _schedule_receipt_from_payload(genesis["schedule_receipt"])
    attempts: list[B4ScheduledAttemptInput] = []
    violations: list[B4RegistryViolation] = []
    violation_phase = False
    for row in parsed[1:]:
        if row.get("event") == "scheduled-attempt":
            if violation_phase or set(row) != base_keys | {"attempt"}:
                _fail("scheduled-attempt row is out of phase or malformed")
            attempts.append(_attempt_from_payload(row["attempt"]))
        elif row.get("event") == "protocol-violation":
            violation_phase = True
            if set(row) != base_keys | {"violation"}:
                _fail("protocol-violation row is malformed")
            violations.append(_violation_from_payload(row["violation"]))
        else:
            _fail("registry event is not recognized")
    rebuilt = _build_registry(
        receipt=receipt,
        attempts=attempts,
        violations=violations,
    )
    if rebuilt.canonical_bytes != data:
        _fail("registry chain, row order, or canonical bytes do not regenerate")
    return rebuilt


def append_registry_violation(
    registry: B4ScheduledAttemptRegistry,
    *,
    schedule_receipt: B4ScheduleReceipt,
    attempt_id: str | None,
    block_id: str | None,
    reason: B4RegistryViolationReason,
    evidence_sha256: str,
) -> B4ScheduledAttemptRegistry:
    """Append one violation while preserving the sealed scheduled prefix."""

    assert_scheduled_registry_complete(
        registry=registry,
        schedule_receipt=schedule_receipt,
    )
    attempt_ids = {item.attempt_id for item in registry.scheduled_attempts}
    block_ids = {
        item.block_id for item in registry.scheduled_attempts if item.block_id is not None
    }
    if attempt_id is not None and attempt_id not in attempt_ids:
        _fail("violation attempt_id is not in the sealed registry")
    if block_id is not None and block_id not in block_ids:
        _fail("violation block_id is not in the sealed registry")
    violation = _validate_violation(
        B4RegistryViolation(
            schema_version=B4_REGISTRY_VIOLATION_SCHEMA_VERSION,
            attempt_id=attempt_id,
            block_id=block_id,
            reason=reason,
            evidence_sha256=evidence_sha256,
        )
    )
    result = _build_registry(
        receipt=schedule_receipt,
        attempts=registry.scheduled_attempts,
        violations=registry.violations + (violation,),
    )
    if not result.canonical_bytes.startswith(registry.canonical_bytes):
        _fail("registry violation append did not preserve the canonical prefix")
    return result


def derive_registry_violation_count(
    *,
    registry: B4ScheduledAttemptRegistry,
    schedule_receipt: B4ScheduleReceipt,
) -> int:
    """Count recognized violations across the full registry, before filtering."""

    assert_scheduled_registry_complete(
        registry=registry,
        schedule_receipt=schedule_receipt,
    )
    for violation in registry.violations:
        _validate_violation(violation)
    contaminated_attempts = {
        attempt.attempt_id
        for attempt in registry.scheduled_attempts
        if attempt.arm_digest_received
    }
    recorded_contamination = {
        violation.attempt_id
        for violation in registry.violations
        if violation.reason
        is B4RegistryViolationReason.ARM_DIGEST_CONTAMINATED_PRECURSOR
    }
    if not contaminated_attempts <= recorded_contamination:
        _fail("arm-digest contaminated precursor lacks its violation row")
    return len(registry.violations)


def _validate_seed_receipt(
    seed_receipt: object,
    *,
    registry_prefix_sha256: str | None = None,
) -> B4RandomizationSeedRecord:
    if not isinstance(seed_receipt, B4RandomizationSeedRecord):
        _fail("an issuer-bound randomization seed receipt is required")
    if seed_receipt.schema_version != B4_ASSIGNMENT_SEED_SCHEMA_VERSION:
        _fail("assignment seed receipt schema version mismatch")
    if not _is_sha256(seed_receipt.seed_hex):
        _fail("assignment seed is not lowercase 256-bit hex")
    for label, value in (
        ("registry prefix", seed_receipt.registry_prefix_sha256),
        ("seed issuer", seed_receipt.issuer_sha256),
        ("seed source receipt", seed_receipt.source_receipt_sha256),
    ):
        if not _is_sha256(value):
            _fail(f"{label} hash is invalid")
    if (
        registry_prefix_sha256 is not None
        and seed_receipt.registry_prefix_sha256 != registry_prefix_sha256
    ):
        _fail("assignment seed receipt is bound to a different registry prefix")
    return seed_receipt


def _seed_payload(seed_receipt: B4RandomizationSeedRecord) -> dict[str, object]:
    _validate_seed_receipt(seed_receipt)
    return {
        "schema_version": seed_receipt.schema_version,
        "seed_hex": seed_receipt.seed_hex,
        "registry_prefix_sha256": seed_receipt.registry_prefix_sha256,
        "issuer_sha256": seed_receipt.issuer_sha256,
        "source_receipt_sha256": seed_receipt.source_receipt_sha256,
    }


def _seed_from_payload(value: object) -> B4RandomizationSeedRecord:
    if type(value) is not dict or set(value) != {
        "schema_version",
        "seed_hex",
        "registry_prefix_sha256",
        "issuer_sha256",
        "source_receipt_sha256",
    }:
        _fail("seed receipt payload key set mismatch")
    return _validate_seed_receipt(
        B4RandomizationSeedRecord(
            schema_version=value["schema_version"],
            seed_hex=value["seed_hex"],
            registry_prefix_sha256=value["registry_prefix_sha256"],
            issuer_sha256=value["issuer_sha256"],
            source_receipt_sha256=value["source_receipt_sha256"],
        )
    )


def derive_assignment(
    *,
    seed_receipt: B4RandomizationSeedRecord,
    block_id: str,
) -> B4AssignmentArmOrder:
    """Derive one reproducible HMAC bit from an explicit seed receipt."""

    seed = _validate_seed_receipt(seed_receipt)
    if not _is_text(block_id):
        _fail("assignment block_id is invalid")
    message = _ASSIGNMENT_DOMAIN + canonical_json_bytes(
        {
            "block_id": block_id,
            "registry_prefix_sha256": seed.registry_prefix_sha256,
        }
    )
    bit = hmac.new(bytes.fromhex(seed.seed_hex), message, hashlib.sha256).digest()[0] & 1
    if bit == 0:
        return B4AssignmentArmOrder.ON_FIRST
    return B4AssignmentArmOrder.OFF_FIRST


def _attempt_is_eligible(attempt: B4ScheduledAttemptInput) -> bool:
    red_classes = {item.value for item in attempt.digest_red_classes}
    return (
        attempt.reason is B4ScheduledAttemptReason.SCHEDULED
        and attempt.whiteboard_result is B4WhiteboardResult.REJECTED
        and bool(red_classes & _ELIGIBLE_RED_CLASSES)
        and attempt.calibrated_workload_member
        and attempt.bootstrap_member
        and attempt.reference_is_unique
        and not attempt.arm_digest_received
        and attempt.block_id is not None
        and _exact_ratio(attempt.reference_tps) is not None
        and _is_sha256(attempt.reference_snapshot_hash)
        and _is_sha256(attempt.reference_receipt_hash)
    )


def _manifest_row_payload(row: B4AnalysisManifestRow) -> dict[str, object]:
    if row.schema_version != B4_ANALYSIS_MANIFEST_ROW_SCHEMA_VERSION:
        _fail("manifest row schema version mismatch")
    if not _is_text(row.attempt_id) or not _is_text(row.block_id):
        _fail("manifest row identity is invalid")
    if not _is_text(row.driver):
        _fail("manifest row driver is invalid")
    reference = _exact_ratio(row.reference_tps)
    if reference is None or reference <= 0:
        _fail("manifest row reference_tps is invalid")
    if not _is_sha256(row.reference_snapshot_hash) or not _is_sha256(
        row.reference_receipt_hash
    ):
        _fail("manifest row reference hash is invalid")
    if not isinstance(row.assignment_order, B4AssignmentArmOrder):
        _fail("manifest row assignment order is invalid")
    return {
        "schema_version": row.schema_version,
        "attempt_id": row.attempt_id,
        "block_id": row.block_id,
        "driver": row.driver,
        "reference_tps": _ratio_payload(row.reference_tps),
        "reference_snapshot_hash": row.reference_snapshot_hash,
        "reference_receipt_hash": row.reference_receipt_hash,
        "assignment_order": row.assignment_order.value,
        "assignment_schedule": [arm.value for arm in row.assignment_schedule],
    }


def _manifest_row_from_payload(value: object) -> B4AnalysisManifestRow:
    if type(value) is not dict or set(value) != {
        "schema_version",
        "attempt_id",
        "block_id",
        "driver",
        "reference_tps",
        "reference_snapshot_hash",
        "reference_receipt_hash",
        "assignment_order",
        "assignment_schedule",
    }:
        _fail("manifest row payload key set mismatch")
    try:
        row = B4AnalysisManifestRow(
            schema_version=value["schema_version"],
            attempt_id=value["attempt_id"],
            block_id=value["block_id"],
            driver=value["driver"],
            reference_tps=_ratio_from_payload(value["reference_tps"]),
            reference_snapshot_hash=value["reference_snapshot_hash"],
            reference_receipt_hash=value["reference_receipt_hash"],
            assignment_order=B4AssignmentArmOrder(value["assignment_order"]),
        )
    except (TypeError, ValueError) as exc:
        raise B4LedgerError("manifest row enum value is invalid") from exc
    payload = _manifest_row_payload(row)
    if payload["assignment_schedule"] != value["assignment_schedule"]:
        _fail("manifest row schedule does not match its assignment order")
    return row


def _manifest_payload(
    *,
    registry_prefix_sha256: str,
    schedule_receipt_sha256: str,
    seed_receipt: B4RandomizationSeedRecord,
    rows: tuple[B4AnalysisManifestRow, ...],
) -> dict[str, object]:
    return {
        "schema_version": B4_ANALYSIS_MANIFEST_SCHEMA_VERSION,
        "registry_prefix_sha256": registry_prefix_sha256,
        "schedule_receipt_sha256": schedule_receipt_sha256,
        "seed_receipt": _seed_payload(seed_receipt),
        "rows": [_manifest_row_payload(row) for row in rows],
    }


def _build_manifest(
    *,
    registry_prefix_sha256: str,
    schedule_receipt_sha256: str,
    seed_receipt: B4RandomizationSeedRecord,
    rows: Sequence[B4AnalysisManifestRow],
) -> B4AnalysisManifest:
    if not _is_sha256(registry_prefix_sha256):
        _fail("manifest registry prefix hash is invalid")
    if not _is_sha256(schedule_receipt_sha256):
        _fail("manifest schedule receipt hash is invalid")
    _validate_seed_receipt(
        seed_receipt,
        registry_prefix_sha256=registry_prefix_sha256,
    )
    row_tuple = tuple(rows)
    payload = _manifest_payload(
        registry_prefix_sha256=registry_prefix_sha256,
        schedule_receipt_sha256=schedule_receipt_sha256,
        seed_receipt=seed_receipt,
        rows=row_tuple,
    )
    data = canonical_json_bytes(payload)
    return B4AnalysisManifest(
        schema_version=B4_ANALYSIS_MANIFEST_SCHEMA_VERSION,
        registry_prefix_sha256=registry_prefix_sha256,
        schedule_receipt_sha256=schedule_receipt_sha256,
        seed_receipt=seed_receipt,
        rows=row_tuple,
        canonical_bytes=data,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def generate_analysis_manifest(
    *,
    registry: B4ScheduledAttemptRegistry,
    schedule_receipt: B4ScheduleReceipt,
    seed_receipt: B4RandomizationSeedRecord,
) -> B4AnalysisManifest | B4DesignNotFeasible:
    """Regenerate the exact first 201 eligible rows or fail without truncating n."""

    assert_scheduled_registry_complete(
        registry=registry,
        schedule_receipt=schedule_receipt,
    )
    seed = _validate_seed_receipt(
        seed_receipt,
        registry_prefix_sha256=registry.sealed_prefix_sha256,
    )
    # This full-registry derivation deliberately precedes eligibility filtering.
    derive_registry_violation_count(
        registry=registry,
        schedule_receipt=schedule_receipt,
    )
    eligible = tuple(
        attempt
        for attempt in registry.scheduled_attempts
        if _attempt_is_eligible(attempt)
    )
    if len(eligible) < EXPECTED_BLOCK_COUNT:
        return B4DesignNotFeasible(
            schema_version=B4_DESIGN_NOT_FEASIBLE_SCHEMA_VERSION,
            reason=B4ManifestState.DESIGN_NOT_FEASIBLE,
            eligible_count=len(eligible),
            required_count=EXPECTED_BLOCK_COUNT,
        )
    selected = eligible[:EXPECTED_BLOCK_COUNT]
    rows = tuple(
        B4AnalysisManifestRow(
            schema_version=B4_ANALYSIS_MANIFEST_ROW_SCHEMA_VERSION,
            attempt_id=attempt.attempt_id,
            block_id=attempt.block_id,
            driver=attempt.driver,
            reference_tps=attempt.reference_tps,
            reference_snapshot_hash=attempt.reference_snapshot_hash,
            reference_receipt_hash=attempt.reference_receipt_hash,
            assignment_order=derive_assignment(
                seed_receipt=seed,
                block_id=attempt.block_id,
            ),
        )
        for attempt in selected
    )
    return _build_manifest(
        registry_prefix_sha256=registry.sealed_prefix_sha256,
        schedule_receipt_sha256=_schedule_receipt_sha256(schedule_receipt),
        seed_receipt=seed,
        rows=rows,
    )


def load_analysis_manifest(data: bytes) -> B4AnalysisManifest:
    """Strictly load a canonical manifest without treating its hash as proof."""

    if type(data) is not bytes or not data:
        _fail("manifest bytes must be non-empty bytes")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B4LedgerError("manifest is not strict UTF-8 JSON") from exc
    if type(value) is not dict or set(value) != {
        "schema_version",
        "registry_prefix_sha256",
        "schedule_receipt_sha256",
        "seed_receipt",
        "rows",
    }:
        _fail("manifest payload key set mismatch")
    if value["schema_version"] != B4_ANALYSIS_MANIFEST_SCHEMA_VERSION:
        _fail("manifest schema version mismatch")
    if type(value["rows"]) is not list:
        _fail("manifest rows are not a list")
    manifest = _build_manifest(
        registry_prefix_sha256=value["registry_prefix_sha256"],
        schedule_receipt_sha256=value["schedule_receipt_sha256"],
        seed_receipt=_seed_from_payload(value["seed_receipt"]),
        rows=tuple(_manifest_row_from_payload(row) for row in value["rows"]),
    )
    if manifest.canonical_bytes != data:
        _fail("manifest bytes are not canonical")
    return manifest


def assert_analysis_manifest_complete(
    *,
    registry: B4ScheduledAttemptRegistry,
    manifest: B4AnalysisManifest,
    schedule_receipt: B4ScheduleReceipt,
    seed_receipt: B4RandomizationSeedRecord,
) -> B4ManifestCompletenessReceipt:
    """Compare regenerated row set, order, and canonical bytes exactly."""

    if not isinstance(manifest, B4AnalysisManifest):
        raise B4DesignNotFeasibleError("design_not_feasible: manifest type is invalid")
    regenerated = generate_analysis_manifest(
        registry=registry,
        schedule_receipt=schedule_receipt,
        seed_receipt=seed_receipt,
    )
    if isinstance(regenerated, B4DesignNotFeasible):
        raise B4DesignNotFeasibleError(
            "design_not_feasible: fewer than 201 eligible registry rows"
        )
    if manifest.rows != regenerated.rows:
        raise B4DesignNotFeasibleError(
            "design_not_feasible: manifest row set or order changed"
        )
    if manifest.canonical_bytes != regenerated.canonical_bytes:
        raise B4DesignNotFeasibleError(
            "design_not_feasible: manifest canonical bytes changed"
        )
    if manifest != regenerated:
        raise B4DesignNotFeasibleError(
            "design_not_feasible: manifest binding or hash changed"
        )
    violation_count = derive_registry_violation_count(
        registry=registry,
        schedule_receipt=schedule_receipt,
    )
    return B4ManifestCompletenessReceipt(
        schema_version=B4_MANIFEST_COMPLETENESS_SCHEMA_VERSION,
        manifest_sha256=manifest.sha256,
        registry_sha256=registry.sha256,
        registry_prefix_sha256=registry.sealed_prefix_sha256,
        schedule_issuer_sha256=schedule_receipt.issuer_sha256,
        seed_issuer_sha256=seed_receipt.issuer_sha256,
        row_count=len(manifest.rows),
        registry_violation_count=violation_count,
    )


def verify_assignment_schedule(
    *,
    manifest: B4AnalysisManifest,
    seed_receipt: B4RandomizationSeedRecord,
) -> None:
    """Recompute every manifest assignment with its required seed receipt."""

    if not isinstance(manifest, B4AnalysisManifest):
        _fail("analysis manifest has the wrong type")
    seed = _validate_seed_receipt(
        seed_receipt,
        registry_prefix_sha256=manifest.registry_prefix_sha256,
    )
    if manifest.seed_receipt != seed:
        _fail("manifest is bound to a different seed receipt")
    for row in manifest.rows:
        expected = derive_assignment(seed_receipt=seed, block_id=row.block_id)
        if row.assignment_order is not expected:
            _fail("manifest assignment schedule does not regenerate")


def build_contract_binding(
    *,
    registry: B4ScheduledAttemptRegistry,
    manifest: B4AnalysisManifest,
    schedule_receipt: B4ScheduleReceipt,
    seed_receipt: B4RandomizationSeedRecord,
) -> B4ContractBinding:
    """Build the unit-A binding only after exact manifest regeneration."""

    assert_analysis_manifest_complete(
        registry=registry,
        manifest=manifest,
        schedule_receipt=schedule_receipt,
        seed_receipt=seed_receipt,
    )
    return B4ContractBinding(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        manifest_sha256=manifest.sha256,
        registry_sha256=registry.sha256,
        blocks=tuple(
            B4ContractBlockBinding(
                schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
                block_id=row.block_id,
                reference_tps=row.reference_tps,
                reference_snapshot_hash=row.reference_snapshot_hash,
                reference_receipt_hash=row.reference_receipt_hash,
                assignment_schedule=row.assignment_schedule,
            )
            for row in manifest.rows
        ),
        expected_block_count=EXPECTED_BLOCK_COUNT,
    )


def assignment_followed(
    *,
    manifest: B4AnalysisManifest,
    observation: B4ExecutionAssignmentObservation,
) -> bool:
    """Compare a two-slot observation with the one frozen manifest row."""

    if not isinstance(manifest, B4AnalysisManifest):
        _fail("analysis manifest has the wrong type")
    if not isinstance(observation, B4ExecutionAssignmentObservation):
        _fail("assignment observation has the wrong type")
    if observation.schema_version != B4_EXECUTION_ASSIGNMENT_SCHEMA_VERSION:
        _fail("assignment observation schema version mismatch")
    if not _is_text(observation.block_id):
        _fail("assignment observation block_id is invalid")
    if (
        type(observation.observed_schedule) is not tuple
        or observation.observed_schedule
        not in ((B4Arm.ON, B4Arm.OFF), (B4Arm.OFF, B4Arm.ON))
    ):
        _fail("assignment observation schedule is invalid")
    matches = [row for row in manifest.rows if row.block_id == observation.block_id]
    if len(matches) != 1:
        _fail("assignment observation block_id is not unique in the manifest")
    return observation.observed_schedule == matches[0].assignment_schedule


def assert_manifest_unchanged_before_run(
    *,
    frozen_manifest_bytes: bytes,
    observed_manifest_bytes: bytes,
) -> None:
    """Reject any post-generation byte change as design_not_feasible."""

    if type(frozen_manifest_bytes) is not bytes or type(observed_manifest_bytes) is not bytes:
        raise B4DesignNotFeasibleError(
            "design_not_feasible: manifest inputs must be bytes"
        )
    try:
        load_analysis_manifest(frozen_manifest_bytes)
        load_analysis_manifest(observed_manifest_bytes)
    except B4LedgerError as exc:
        raise B4DesignNotFeasibleError(
            "design_not_feasible: manifest bytes are not a valid frozen manifest"
        ) from exc
    if frozen_manifest_bytes != observed_manifest_bytes:
        raise B4DesignNotFeasibleError(
            "design_not_feasible: manifest changed after generation"
        )


__all__ = [
    "B4_ANALYSIS_MANIFEST_ROW_SCHEMA_VERSION",
    "B4_ANALYSIS_MANIFEST_SCHEMA_VERSION",
    "B4_ASSIGNMENT_SEED_SCHEMA_VERSION",
    "B4_DESIGN_NOT_FEASIBLE_SCHEMA_VERSION",
    "B4_EXECUTION_ASSIGNMENT_SCHEMA_VERSION",
    "B4_MANIFEST_COMPLETENESS_SCHEMA_VERSION",
    "B4_REGISTRY_EVENT_SCHEMA_VERSION",
    "B4_REGISTRY_VIOLATION_SCHEMA_VERSION",
    "B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION",
    "B4_SCHEDULED_REGISTRY_SCHEMA_VERSION",
    "B4_SCHEDULE_RECEIPT_SCHEMA_VERSION",
    "B4AnalysisManifest",
    "B4AnalysisManifestRow",
    "B4AssignmentArmOrder",
    "B4DesignNotFeasible",
    "B4DesignNotFeasibleError",
    "B4DigestRedClass",
    "B4ExecutionAssignmentObservation",
    "B4LedgerError",
    "B4ManifestCompletenessReceipt",
    "B4ManifestState",
    "B4RandomizationSeedRecord",
    "B4RegistryViolation",
    "B4ScheduleReceipt",
    "B4ScheduledAttemptInput",
    "B4ScheduledAttemptReason",
    "B4ScheduledAttemptRegistry",
    "B4WhiteboardResult",
    "append_registry_violation",
    "assert_analysis_manifest_complete",
    "assert_manifest_unchanged_before_run",
    "assert_scheduled_registry_complete",
    "assignment_followed",
    "build_contract_binding",
    "derive_assignment",
    "derive_registry_violation_count",
    "generate_analysis_manifest",
    "load_analysis_manifest",
    "load_scheduled_attempt_registry",
    "scheduled_attempts_sha256",
    "seal_scheduled_attempt_registry",
    "verify_assignment_schedule",
]
