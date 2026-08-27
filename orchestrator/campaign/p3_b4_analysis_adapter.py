"""Fail-closed adapter from B-4 raw artifact JSON to contract inputs.

JSON decimal tokens are converted directly to :class:`fractions.Fraction`.
Already-decoded mappings are deliberately not accepted because they cannot prove
that a binary float was not used while decoding the artifact.  Every public
adapter operation returns ``B4AnalysisInvalid`` for malformed input instead of
letting parse, schema, or mapping exceptions escape.

The raw fields that do not yet have an authoritative producer remain mandatory.
This module never derives them from digest text, variant ids, or fallback values.
It also retains every non-executed arm as ``missing``; it never drops its block.
Raw arm, disposition, whiteboard, and terminal-stage enum failures are mapped to
``field_missing_or_ill_typed``.  ``status_domain_error`` is reserved for the
derived block ``status`` contract rather than being used as a generic enum error.
"""

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import json

from .p3_b4_analysis_contract import (
    B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
    B4AnalysisInvalid,
    B4AnalysisInvalidReason,
    B4Arm,
    B4ArmObservation,
    B4BlockObservation,
    B4BlockStatus,
    B4ContractBinding,
    B4ContractBlockBinding,
    as_b4_exact_fraction,
    b4_binding_domain_is_valid,
)


RAW_ANALYSIS_SCHEMA_VERSION = "p3-b4-raw-analysis/v1"


class B4ExecutionDisposition(str, Enum):
    """Closed disposition vocabulary for one scheduled arm execution."""

    EXECUTED = "executed"
    DUPLICATE = "duplicate"
    DRY_PASS = "dry-pass"
    STOPPED_BEFORE = "stopped-before"
    CRASH = "crash"
    TERMINAL_RECORD_ABSENT = "terminal-record-absent"


class B4RawWhiteboardResult(str, Enum):
    """Whiteboard values used only with terminal evidence for status mapping."""

    SUCCESS = "success"
    REJECTED = "rejected"
    FAIL = "fail"


class B4RawTerminalStage(str, Enum):
    """Terminal WAL stages admitted by the raw schema."""

    COMMIT = "COMMIT"
    ABORT = "ABORT"


@dataclass(frozen=True, slots=True)
class B4RawArmRecord:
    """Strictly parsed raw evidence for one arm."""

    arm: B4Arm
    execution_disposition: B4ExecutionDisposition
    whiteboard_result: B4RawWhiteboardResult | None
    terminal_stage: B4RawTerminalStage | None
    terminal_reason: str | None
    throughput: Fraction | None
    precursor_hash: str
    treatment_fired: bool
    contaminated: bool
    protocol_ok: bool
    source_artifact_sha256: str


@dataclass(frozen=True, slots=True)
class B4RawBlockRecord:
    """Strictly parsed paired raw evidence for one manifest block."""

    block_id: str
    reference_tps: Fraction
    reference_snapshot_hash: str
    reference_receipt_hash: str
    assignment_observation: tuple[B4Arm, B4Arm]
    arms: tuple[B4RawArmRecord, B4RawArmRecord]


@dataclass(frozen=True, slots=True)
class B4RawAnalysisRecords:
    """Versioned raw artifact after exact lexical parsing and schema closure."""

    schema_version: str
    blocks: tuple[B4RawBlockRecord, ...]


class _B4AdapterFailure(Exception):
    def __init__(self, reason: B4AnalysisInvalidReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


def _failure(reason: B4AnalysisInvalidReason) -> B4AnalysisInvalid:
    return B4AnalysisInvalid(
        schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
        reasons=(reason,),
    )


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_block_id(value: object) -> bool:
    return type(value) is str and bool(value) and value.strip() == value


def _exact_fraction(
    value: object,
    *,
    reason: B4AnalysisInvalidReason,
) -> Fraction:
    exact = as_b4_exact_fraction(value)
    if exact is None:
        raise _B4AdapterFailure(reason)
    return exact


def _closed_keys(value: object, expected: frozenset[str]) -> dict[str, object]:
    if type(value) is not dict or frozenset(value) != expected:
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> object:
    raise _B4AdapterFailure(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)


def _enum_value(enum_type: type[Enum], value: object) -> Enum:
    if type(value) is not str:
        raise _B4AdapterFailure(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)
    try:
        return enum_type(value)
    except ValueError as error:
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        ) from error


_TOP_LEVEL_KEYS = frozenset(("schema_version", "blocks"))
_BLOCK_KEYS = frozenset(
    (
        "block_id",
        "reference_tps",
        "reference_snapshot_hash",
        "reference_receipt_hash",
        "assignment_observation",
        "arms",
    )
)
_ARM_KEYS = frozenset(
    (
        "arm",
        "execution_disposition",
        "whiteboard_result",
        "terminal_stage",
        "terminal_reason",
        "throughput",
        "precursor_hash",
        "treatment_fired",
        "contaminated",
        "protocol_ok",
        "source_artifact_sha256",
    )
)


def _parse_optional_enum(enum_type: type[Enum], value: object) -> Enum | None:
    if value is None:
        return None
    return _enum_value(enum_type, value)


def _parse_raw_arm(value: object) -> B4RawArmRecord:
    raw = _closed_keys(value, _ARM_KEYS)
    for name in ("treatment_fired", "contaminated", "protocol_ok"):
        if type(raw[name]) is not bool:
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )

    if not _is_sha256(raw["precursor_hash"]) or not _is_sha256(
        raw["source_artifact_sha256"]
    ):
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    terminal_reason = raw["terminal_reason"]
    if terminal_reason is not None and (
        type(terminal_reason) is not str
        or not terminal_reason
        or terminal_reason.strip() != terminal_reason
    ):
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    throughput_value = raw["throughput"]
    throughput = None
    if throughput_value is not None:
        throughput = _exact_fraction(
            throughput_value,
            reason=B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR,
        )

    arm = _enum_value(B4Arm, raw["arm"])
    disposition = _enum_value(
        B4ExecutionDisposition,
        raw["execution_disposition"],
    )
    whiteboard = _parse_optional_enum(
        B4RawWhiteboardResult,
        raw["whiteboard_result"],
    )
    terminal_stage = _parse_optional_enum(
        B4RawTerminalStage,
        raw["terminal_stage"],
    )
    assert isinstance(arm, B4Arm)
    assert isinstance(disposition, B4ExecutionDisposition)
    assert whiteboard is None or isinstance(whiteboard, B4RawWhiteboardResult)
    assert terminal_stage is None or isinstance(terminal_stage, B4RawTerminalStage)
    assert type(terminal_reason) is str or terminal_reason is None
    assert type(raw["precursor_hash"]) is str
    assert type(raw["source_artifact_sha256"]) is str
    return B4RawArmRecord(
        arm=arm,
        execution_disposition=disposition,
        whiteboard_result=whiteboard,
        terminal_stage=terminal_stage,
        terminal_reason=terminal_reason,
        throughput=throughput,
        precursor_hash=raw["precursor_hash"],
        treatment_fired=raw["treatment_fired"],
        contaminated=raw["contaminated"],
        protocol_ok=raw["protocol_ok"],
        source_artifact_sha256=raw["source_artifact_sha256"],
    )


def _parse_raw_block(value: object) -> B4RawBlockRecord:
    raw = _closed_keys(value, _BLOCK_KEYS)
    if not _is_block_id(raw["block_id"]):
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    reference_tps = _exact_fraction(
        raw["reference_tps"],
        reason=B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR,
    )
    if reference_tps <= 0:
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR
        )
    if not _is_sha256(raw["reference_snapshot_hash"]) or not _is_sha256(
        raw["reference_receipt_hash"]
    ):
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    assignment = raw["assignment_observation"]
    if type(assignment) is not list or len(assignment) != 2:
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    assignment_tuple = tuple(_enum_value(B4Arm, item) for item in assignment)
    if set(assignment_tuple) != {B4Arm.ON, B4Arm.OFF}:
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    arms_value = raw["arms"]
    if type(arms_value) is not list or len(arms_value) != 2:
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    arms = tuple(_parse_raw_arm(item) for item in arms_value)
    if {arm.arm for arm in arms} != {B4Arm.ON, B4Arm.OFF}:
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )

    assert type(raw["block_id"]) is str
    assert type(raw["reference_snapshot_hash"]) is str
    assert type(raw["reference_receipt_hash"]) is str
    return B4RawBlockRecord(
        block_id=raw["block_id"],
        reference_tps=reference_tps,
        reference_snapshot_hash=raw["reference_snapshot_hash"],
        reference_receipt_hash=raw["reference_receipt_hash"],
        assignment_observation=(assignment_tuple[0], assignment_tuple[1]),
        arms=(arms[0], arms[1]),
    )


def _validate_typed_records(value: B4RawAnalysisRecords) -> None:
    if (
        type(value.schema_version) is not str
        or value.schema_version != RAW_ANALYSIS_SCHEMA_VERSION
        or type(value.blocks) is not tuple
    ):
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    seen: set[str] = set()
    for block in value.blocks:
        if not isinstance(block, B4RawBlockRecord):
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        if not _is_block_id(block.block_id):
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        if block.block_id in seen:
            raise _B4AdapterFailure(B4AnalysisInvalidReason.DUPLICATE_BLOCK_ID)
        seen.add(block.block_id)
        if not isinstance(block.reference_tps, Fraction) or block.reference_tps <= 0:
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.REFERENCE_VALUE_DOMAIN_ERROR
            )
        if not _is_sha256(block.reference_snapshot_hash) or not _is_sha256(
            block.reference_receipt_hash
        ):
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        if (
            type(block.assignment_observation) is not tuple
            or len(block.assignment_observation) != 2
            or not all(
                isinstance(arm, B4Arm)
                for arm in block.assignment_observation
            )
            or block.assignment_observation
            not in ((B4Arm.ON, B4Arm.OFF), (B4Arm.OFF, B4Arm.ON))
        ):
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        if type(block.arms) is not tuple or len(block.arms) != 2:
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        for arm in block.arms:
            _validate_raw_arm_record(arm)
        if {arm.arm for arm in block.arms} != {B4Arm.ON, B4Arm.OFF}:
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )


def parse_raw_analysis_records(
    value: object,
) -> B4RawAnalysisRecords | B4AnalysisInvalid:
    """Parse exact JSON lexicals into the closed raw schema without raising."""

    try:
        if isinstance(value, B4RawAnalysisRecords):
            _validate_typed_records(value)
            return value
        if type(value) not in (str, bytes, bytearray):
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        decoded = json.loads(
            value,
            parse_float=Fraction,
            parse_constant=_reject_json_constant,
            object_pairs_hook=_object_without_duplicate_keys,
        )
        raw = _closed_keys(decoded, _TOP_LEVEL_KEYS)
        if raw["schema_version"] != RAW_ANALYSIS_SCHEMA_VERSION:
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        blocks_value = raw["blocks"]
        if type(blocks_value) is not list:
            raise _B4AdapterFailure(
                B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
            )
        blocks = tuple(_parse_raw_block(item) for item in blocks_value)
        seen: set[str] = set()
        for block in blocks:
            if block.block_id in seen:
                raise _B4AdapterFailure(B4AnalysisInvalidReason.DUPLICATE_BLOCK_ID)
            seen.add(block.block_id)
        return B4RawAnalysisRecords(
            schema_version=RAW_ANALYSIS_SCHEMA_VERSION,
            blocks=blocks,
        )
    except _B4AdapterFailure as error:
        return _failure(error.reason)
    except Exception:
        return _failure(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)


def _validate_raw_arm_record(record: object) -> None:
    if not isinstance(record, B4RawArmRecord):
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )
    if (
        not isinstance(record.arm, B4Arm)
        or not isinstance(record.execution_disposition, B4ExecutionDisposition)
        or (
            record.whiteboard_result is not None
            and not isinstance(record.whiteboard_result, B4RawWhiteboardResult)
        )
        or (
            record.terminal_stage is not None
            and not isinstance(record.terminal_stage, B4RawTerminalStage)
        )
        or (
            record.terminal_reason is not None
            and (
                type(record.terminal_reason) is not str
                or not record.terminal_reason
                or record.terminal_reason.strip() != record.terminal_reason
            )
        )
        or (
            record.throughput is not None
            and not isinstance(record.throughput, Fraction)
        )
        or not _is_sha256(record.precursor_hash)
        or type(record.treatment_fired) is not bool
        or type(record.contaminated) is not bool
        or type(record.protocol_ok) is not bool
        or not _is_sha256(record.source_artifact_sha256)
    ):
        raise _B4AdapterFailure(
            B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED
        )


def block_status_from_raw_arm(
    record: object,
) -> B4BlockStatus | B4AnalysisInvalid:
    """Map every admitted raw terminal combination without raising."""

    try:
        _validate_raw_arm_record(record)
        assert isinstance(record, B4RawArmRecord)
        if record.execution_disposition is not B4ExecutionDisposition.EXECUTED:
            return B4BlockStatus.MISSING

        if (
            record.terminal_stage is B4RawTerminalStage.COMMIT
            and record.whiteboard_result is B4RawWhiteboardResult.SUCCESS
        ):
            if record.throughput is None or record.throughput <= 0:
                return _failure(
                    B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR
                )
            return B4BlockStatus.CERTIFIED

        if record.throughput is not None:
            return _failure(B4AnalysisInvalidReason.THROUGHPUT_CONTRACT_ERROR)
        if (
            record.terminal_stage is B4RawTerminalStage.ABORT
            and record.terminal_reason == "diff-quarantine"
            and record.whiteboard_result is B4RawWhiteboardResult.REJECTED
        ):
            return B4BlockStatus.REJECTED
        if (
            record.terminal_stage is B4RawTerminalStage.ABORT
            and record.terminal_reason != "diff-quarantine"
            and record.whiteboard_result is B4RawWhiteboardResult.FAIL
        ):
            return B4BlockStatus.ABORTED
        return _failure(B4AnalysisInvalidReason.STATUS_DOMAIN_ERROR)
    except _B4AdapterFailure as error:
        return _failure(error.reason)
    except Exception:
        return _failure(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)


def _contract_blocks_by_id(
    binding: object,
) -> dict[str, B4ContractBlockBinding]:
    if not b4_binding_domain_is_valid(binding):
        raise _B4AdapterFailure(B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR)
    assert isinstance(binding, B4ContractBinding)
    return {block.block_id: block for block in binding.blocks}


def adapt_raw_blocks(
    value: object,
    *,
    contract_binding: object,
) -> tuple[B4BlockObservation, ...] | B4AnalysisInvalid:
    """Build all contract observations from raw records as a total function."""

    try:
        parsed = parse_raw_analysis_records(value)
        if isinstance(parsed, B4AnalysisInvalid):
            return parsed
        expected_by_id = _contract_blocks_by_id(contract_binding)
        assert isinstance(contract_binding, B4ContractBinding)
        if len(parsed.blocks) != contract_binding.expected_block_count:
            return _failure(B4AnalysisInvalidReason.BLOCK_COUNT_MISMATCH)

        observations: list[B4BlockObservation] = []
        for raw_block in parsed.blocks:
            expected = expected_by_id.get(raw_block.block_id)
            if expected is None:
                return _failure(B4AnalysisInvalidReason.UNKNOWN_BLOCK_ID)
            expected_reference = _exact_fraction(
                expected.reference_tps,
                reason=B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR,
            )
            if (
                raw_block.reference_tps != expected_reference
                or raw_block.reference_snapshot_hash
                != expected.reference_snapshot_hash
                or raw_block.reference_receipt_hash
                != expected.reference_receipt_hash
            ):
                return _failure(B4AnalysisInvalidReason.REFERENCE_BINDING_MISMATCH)

            arms_by_name = {arm.arm: arm for arm in raw_block.arms}
            on_raw = arms_by_name[B4Arm.ON]
            off_raw = arms_by_name[B4Arm.OFF]
            if on_raw.precursor_hash != off_raw.precursor_hash:
                return _failure(B4AnalysisInvalidReason.PRECURSOR_HASH_MISMATCH)
            on_status = block_status_from_raw_arm(on_raw)
            if isinstance(on_status, B4AnalysisInvalid):
                return on_status
            off_status = block_status_from_raw_arm(off_raw)
            if isinstance(off_status, B4AnalysisInvalid):
                return off_status

            def observation(
                raw_arm: B4RawArmRecord,
                status: B4BlockStatus,
            ) -> B4ArmObservation:
                return B4ArmObservation(
                    schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
                    precursor_hash=raw_arm.precursor_hash,
                    status=status,
                    throughput=(
                        raw_arm.throughput
                        if status is B4BlockStatus.CERTIFIED
                        else None
                    ),
                    treatment_fired=raw_arm.treatment_fired,
                    contaminated=raw_arm.contaminated,
                    protocol_ok=raw_arm.protocol_ok,
                )

            observations.append(
                B4BlockObservation(
                    schema_version=B4_ANALYSIS_CONTRACT_SCHEMA_VERSION,
                    block_id=raw_block.block_id,
                    reference_tps=raw_block.reference_tps,
                    reference_snapshot_hash=raw_block.reference_snapshot_hash,
                    reference_receipt_hash=raw_block.reference_receipt_hash,
                    assignment_followed=(
                        raw_block.assignment_observation
                        == expected.assignment_schedule
                    ),
                    on=observation(on_raw, on_status),
                    off=observation(off_raw, off_status),
                )
            )
        return tuple(observations)
    except _B4AdapterFailure as error:
        return _failure(error.reason)
    except Exception:
        return _failure(B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED)


__all__ = [
    "RAW_ANALYSIS_SCHEMA_VERSION",
    "B4ExecutionDisposition",
    "B4RawAnalysisRecords",
    "B4RawArmRecord",
    "B4RawBlockRecord",
    "B4RawTerminalStage",
    "B4RawWhiteboardResult",
    "adapt_raw_blocks",
    "block_status_from_raw_arm",
    "parse_raw_analysis_records",
]
