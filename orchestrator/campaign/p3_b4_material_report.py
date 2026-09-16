"""Build the evidence-only B-4 material report from one pre-run publication.

The command in this module is a read-only consumer of campaign evidence.  It
does not launch campaigns, build binaries, measure performance, or certify a
selection.  It resolves the authoritative floor only from preregistration §5:
the fixed-table floor cell's stripped raw sentinel preserves the legacy
``floor=None`` path, while a valid
pin supplies its exact :class:`fractions.Fraction` to the frozen evaluator.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from enum import Enum
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any, Mapping, NoReturn, Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .p3_b4_analysis_contract import B4AnalysisResult
from .p3_b4_analysis_ledgers import B4LedgerError, build_contract_binding
from .p3_b4_analysis_path import evaluate_b4_artifacts
from .p3_b4_floor_artifact_issuer import (
    B4AuthoritativeFloor,
    B4FloorArtifactError,
    resolve_preregistered_authoritative_floor,
)
from .p3_b4_prerun_issuer import (
    B4PrerunIssuerError,
    B4PrerunPublication,
    load_b4_prerun_publication,
)
from .p3_b4_raw_record_producer import (
    B4RawAnalysisAssembly,
    B4RawAnalysisRejection,
    B4RawRecordRejection,
    B4RawRecordRejectionHistory,
    B4_RAW_RECORD_NON_GUARANTEES,
    assemble_b4_raw_analysis,
)


SCHEMA_VERSION = "p3-b4-material-report/v1"
GENERATOR_IDENTITY = "orchestrator/campaign/p3_b4_material_report.py"
REPORT_JSON_NAME = "report.json"
REPORT_MARKDOWN_NAME = "report.md"
REPORT_COMMIT_NAME = "report.complete"

_ABSENT = {"availability": "absent", "value": None}
_HISTORICAL_REJECTION_NON_GUARANTEE = (
    "past_producer_rejections_are_not_fully_reconstructible_from_publication_root"
)
_CURRENT_ABSENT_REASON_NON_GUARANTEE = (
    "current_reason_for_an_absent_planned_leaf_cannot_be_determined"
)
_REJECTION_LEDGER_TRUNCATION_NON_GUARANTEE = (
    "rejection_ledger_deletion_and_complete_suffix_truncation_are_not_detected"
)
_OBSERVATION_TIME_NON_GUARANTEE = (
    "artifact_availability_and_assembly_rejection_are_observed_at_report_generation_time"
)
_RECORDED_REJECTION_COUNT_CAVEAT = (
    "This count covers events present in the observed readable ledger prefix; "
    "ledger deletion, complete suffix truncation, pre-validation rejection, "
    "deferred state, and append failure can make it an undercount."
)
_RECORDED_REJECTION_RATE_CAVEAT = (
    "This rate joins scheduled attempts only to events present in the observed "
    "readable ledger prefix; the same undetected and unrecorded cases can make "
    "the numerator an undercount."
)
_INITIAL_PROPOSAL_NON_GUARANTEE = B4_RAW_RECORD_NON_GUARANTEES[0]
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_PREREGISTRATION_RELATIVE_PATH = Path(
    "docs/phase3-b4-reflux-ablation-preregistration.md"
)


class B4MaterialReportError(ValueError):
    """One typed material-report boundary rejected an operation."""

    def __init__(self, reason: str, detail: str) -> None:
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


@dataclass(frozen=True, slots=True)
class _B4PlannedArmFrame:
    row_ordinal: int
    block_ordinal: int
    manifest_row: object
    registry_attempt: object
    planned_path: str
    artifact_availability: str
    arm: str


@dataclass(frozen=True, slots=True)
class _CampaignRootDiscovery:
    roots: tuple[Path, ...]
    status: str
    unresolved: tuple[dict[str, str], ...]


@dataclass(frozen=True, slots=True)
class B4MaterialReportInputs:
    publication: B4PrerunPublication
    planned_frames: tuple[_B4PlannedArmFrame, ...]
    assembly: B4RawAnalysisAssembly | B4RawRecordRejection
    contract_binding: object | None
    analysis_result: B4AnalysisResult | None
    campaign_root_discovery: _CampaignRootDiscovery
    authoritative_floor: B4AuthoritativeFloor | None


@dataclass(frozen=True, slots=True)
class B4MaterialReportDocument:
    json_value: dict[str, Any]
    json_bytes: bytes
    markdown_bytes: bytes
    json_sha256: str


@dataclass(frozen=True, slots=True)
class B4MaterialReportWrite:
    report_json_path: str
    report_md_path: str
    report_commit_path: str
    report_json_sha256: str


def _fail(reason: str, detail: str, *, cause: BaseException | None = None) -> NoReturn:
    error = B4MaterialReportError(reason, detail)
    if cause is None:
        raise error
    raise error from cause


def _wire_value(value: object) -> Any:
    """Convert frozen contract values to deterministic JSON values."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _wire_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            _fail("wire_value_invalid", "JSON object keys must be exact strings")
        return {key: _wire_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_wire_value(item) for item in value]
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError as exc:
            _fail("wire_value_invalid", "embedded bytes are not UTF-8", cause=exc)
    if value is None or type(value) in {str, int, float, bool}:
        return value
    _fail("wire_value_invalid", f"unsupported value type {type(value).__name__}")


def _canonical_json_bytes(value: object) -> bytes:
    def encode(item: object) -> str:
        if item is None:
            return "null"
        if type(item) is bool:
            return "true" if item else "false"
        if type(item) is int:
            return str(item)
        if isinstance(item, Decimal):
            if not item.is_finite():
                _fail("report_json_invalid", "non-finite decimal is not JSON")
            return str(item)
        if type(item) is float:
            try:
                return json.dumps(item, allow_nan=False)
            except ValueError as exc:
                _fail("report_json_invalid", "non-finite float is not JSON", cause=exc)
        if type(item) is str:
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, (list, tuple)):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, Mapping):
            if any(type(key) is not str for key in item):
                _fail("report_json_invalid", "JSON object key is not an exact string")
            return "{" + ",".join(
                json.dumps(key, ensure_ascii=False) + ":" + encode(item[key])
                for key in sorted(item)
            ) + "}"
        _fail("report_json_invalid", f"unsupported JSON type {type(item).__name__}")

    return (encode(value) + "\n").encode("utf-8")


def _load_and_evaluate(publication_root: Path) -> B4MaterialReportInputs:
    """Compose the existing issuer, producer, ledger, and evaluator APIs."""

    try:
        authoritative_floor = resolve_preregistered_authoritative_floor(
            repo_root=_REPOSITORY_ROOT,
            preregistration_path=(
                _REPOSITORY_ROOT / _PREREGISTRATION_RELATIVE_PATH
            ),
        )
    except B4FloorArtifactError as exc:
        _fail(
            "authoritative_floor_rejected",
            f"{exc.code}: {exc.detail}",
            cause=exc,
        )

    try:
        publication = load_b4_prerun_publication(str(publication_root))
    except B4PrerunIssuerError as exc:
        _fail(
            "publication_rejected",
            f"{exc.reason.value}: {exc}",
            cause=exc,
        )

    planned_frames = _planned_arm_frames(publication)
    assembly = assemble_b4_raw_analysis(publication=publication)
    discovery = _discover_campaign_roots(
        publication=publication,
        planned_frames=planned_frames,
        assembly=assembly,
    )
    if isinstance(assembly, B4RawRecordRejection):
        return B4MaterialReportInputs(
            publication=publication,
            planned_frames=planned_frames,
            assembly=assembly,
            contract_binding=None,
            analysis_result=None,
            campaign_root_discovery=discovery,
            authoritative_floor=authoritative_floor,
        )
    if not isinstance(assembly, B4RawAnalysisAssembly):
        _fail("assembly_contract_error", "assembler returned an unknown result type")

    try:
        binding = build_contract_binding(
            registry=publication.registry,
            manifest=publication.manifest,
            schedule_receipt=publication.schedule_receipt,
            seed_receipt=publication.seed_receipt,
        )
    except B4LedgerError as exc:
        _fail("ledger_rejected", str(exc), cause=exc)

    result = evaluate_b4_artifacts(
        floor=(
            authoritative_floor.floor
            if authoritative_floor is not None
            else None
        ),
        contract_binding=binding,
        scheduled_registry_bytes=publication.registry.canonical_bytes,
        analysis_manifest_bytes=publication.manifest.canonical_bytes,
        raw_analysis_records_bytes=assembly.canonical_bytes,
        source_artifact_bytes=assembly.source_artifact_bytes,
    )
    return B4MaterialReportInputs(
        publication=publication,
        planned_frames=planned_frames,
        assembly=assembly,
        contract_binding=binding,
        analysis_result=result,
        campaign_root_discovery=discovery,
        authoritative_floor=authoritative_floor,
    )


def _source_object(data: bytes) -> dict[str, Any]:
    def reject_constant(token: str) -> NoReturn:
        raise ValueError(f"non-standard JSON constant: {token}")

    try:
        value = json.loads(
            data.decode("utf-8"),
            parse_float=Decimal,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        _fail("source_object_invalid", "assembled source is not strict UTF-8 JSON", cause=exc)
    if type(value) is not dict:
        _fail("source_object_invalid", "assembled source object is not an object")
    return value


def _attempts_by_id(publication: B4PrerunPublication) -> dict[str, object]:
    attempts = {
        attempt.attempt_id: attempt
        for attempt in publication.registry.scheduled_attempts
    }
    if len(attempts) != len(publication.registry.scheduled_attempts):
        _fail("projection_invalid", "registry attempt ids are not unique")
    return attempts


def _planned_by_id(publication: B4PrerunPublication) -> dict[str, str]:
    planned = {
        item.attempt_id: item.artifact_path
        for item in publication.planned_result_artifacts
    }
    if len(planned) != len(publication.planned_result_artifacts):
        _fail("projection_invalid", "planned artifact attempt ids are not unique")
    return planned


def _observe_artifact_availability(path: str) -> str:
    return "present" if os.path.lexists(path) else "absent"


def _planned_arm_frames(
    publication: B4PrerunPublication,
) -> tuple[_B4PlannedArmFrame, ...]:
    """Freeze the 201-block/402-arm report frame before assembly is attempted."""

    attempts = _attempts_by_id(publication)
    planned = _planned_by_id(publication)
    frames: list[_B4PlannedArmFrame] = []
    for block_index, manifest_row in enumerate(publication.manifest.rows, start=1):
        registry_attempt = attempts.get(manifest_row.attempt_id)
        planned_path = planned.get(manifest_row.attempt_id)
        if registry_attempt is None or planned_path is None:
            _fail("projection_invalid", "manifest row lacks registry or planned binding")
        artifact_availability = _observe_artifact_availability(planned_path)
        for arm_index, arm in enumerate(("on", "off")):
            frames.append(_B4PlannedArmFrame(
                row_ordinal=(block_index - 1) * 2 + arm_index + 1,
                block_ordinal=block_index,
                manifest_row=manifest_row,
                registry_attempt=registry_attempt,
                planned_path=planned_path,
                artifact_availability=artifact_availability,
                arm=arm,
            ))
    return tuple(frames)


def _artifact_presence(path: str, availability: str) -> dict[str, Any]:
    return {
        "availability": availability,
        "observed_path": path,
    }


def _unavailable_field(reason: str) -> dict[str, Any]:
    return {"availability": "absent", "reason": reason, "value": None}


def _successful_row(
    *,
    inputs: B4MaterialReportInputs,
    row_ordinal: int,
    block_ordinal: int,
    manifest_row: object,
    registry_attempt: object,
    planned_path: str,
    artifact_availability: str,
    arm: str,
    source_bytes: bytes,
) -> dict[str, Any]:
    source = _source_object(source_bytes)
    identity = source.get("identity")
    raw = source.get("raw")
    receipt = source.get("receipt_projection")
    evidence = source.get("evidence")
    binding = source.get("binding")
    if not all(type(item) is dict for item in (identity, raw, receipt, evidence, binding)):
        _fail("projection_invalid", "source object sections are not exact objects")
    wal_value = evidence.get("wal")
    if type(wal_value) is not dict:
        _fail("projection_invalid", "source WAL descriptor is not an object")
    result = inputs.analysis_result
    if result is None:
        _fail("projection_invalid", "successful assembly has no analysis result")
    source_utf8 = source_bytes.decode("utf-8")
    initial_snapshot = {
        "availability": "present",
        "binding": "transcribed",
        "non_guarantee": _INITIAL_PROPOSAL_NON_GUARANTEE,
        "source": "registry.initial_proposal_sha256",
        "value": registry_attempt.initial_proposal_sha256,
    }
    return {
        "row_ordinal": row_ordinal,
        "block_ordinal": block_ordinal,
        "attempt_id": manifest_row.attempt_id,
        "block_id": manifest_row.block_id,
        "arm": arm,
        "campaign_id": identity.get("campaign_id"),
        "initial_snapshot_hash": initial_snapshot,
        "initial_proposal_sha256": registry_attempt.initial_proposal_sha256,
        "model_prompt_projection_hash": {
            "availability": "partial",
            "model_hash": dict(_ABSENT),
            "model_snapshot": receipt.get("model_snapshot"),
            "prompt_sha256": receipt.get("effective_prompt_sha256"),
            "projection_sha256": receipt.get("projection_sha256"),
        },
        "wal": {"path": wal_value.get("path"), "sha256": wal_value.get("sha256")},
        "stop_reason": {
            "execution_disposition": raw.get("execution_disposition"),
            "terminal_stage": raw.get("terminal_stage"),
            "terminal_reason": raw.get("terminal_reason"),
        },
        "budget_consumption": dict(_ABSENT),
        "verdict": {
            "availability": "present",
            "scope": "experiment",
            "value": result.verdict.value,
        },
        "anomaly_class": dict(_ABSENT),
        "performance_value_present": raw.get("throughput") is not None,
        "precursor_digest_red_classes": [
            item.value for item in registry_attempt.digest_red_classes
        ],
        "evidence_issues": source.get("evidence_issues"),
        "planned_attempt_artifact_path": planned_path,
        "planned_attempt_artifact": _artifact_presence(
            planned_path,
            artifact_availability,
        ),
        "source_artifact_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_artifact_utf8": source_utf8,
        "source_object": source,
        "reference_snapshot_hash": manifest_row.reference_snapshot_hash,
        "reference_receipt_hash": manifest_row.reference_receipt_hash,
        "precursor_hash": binding.get("precursor_hash"),
        "driver": manifest_row.driver,
    }


def _rejected_row(
    *,
    row_ordinal: int,
    block_ordinal: int,
    manifest_row: object,
    registry_attempt: object,
    planned_path: str,
    artifact_availability: str,
    arm: str,
) -> dict[str, Any]:
    unavailable = "assembly_rejected"
    return {
        "row_ordinal": row_ordinal,
        "block_ordinal": block_ordinal,
        "attempt_id": manifest_row.attempt_id,
        "block_id": manifest_row.block_id,
        "arm": arm,
        "campaign_id": _unavailable_field(unavailable),
        "initial_snapshot_hash": {
            "availability": "present",
            "binding": "transcribed",
            "non_guarantee": _INITIAL_PROPOSAL_NON_GUARANTEE,
            "source": "registry.initial_proposal_sha256",
            "value": registry_attempt.initial_proposal_sha256,
        },
        "initial_proposal_sha256": registry_attempt.initial_proposal_sha256,
        "model_prompt_projection_hash": _unavailable_field(unavailable),
        "wal": _unavailable_field(unavailable),
        "stop_reason": _unavailable_field(unavailable),
        "budget_consumption": dict(_ABSENT),
        "verdict": _unavailable_field("assembly_rejected_not_evaluated"),
        "anomaly_class": dict(_ABSENT),
        "performance_value_present": _unavailable_field(unavailable),
        "precursor_digest_red_classes": [
            item.value for item in registry_attempt.digest_red_classes
        ],
        "evidence_issues": _unavailable_field(unavailable),
        "planned_attempt_artifact_path": planned_path,
        "planned_attempt_artifact": _artifact_presence(
            planned_path,
            artifact_availability,
        ),
        "source_artifact_sha256": _unavailable_field(unavailable),
        "source_artifact_utf8": _unavailable_field(unavailable),
        "source_object": _unavailable_field(unavailable),
        "reference_snapshot_hash": manifest_row.reference_snapshot_hash,
        "reference_receipt_hash": manifest_row.reference_receipt_hash,
        "precursor_hash": _unavailable_field(unavailable),
        "driver": manifest_row.driver,
    }


def _rows_from_inputs(inputs: B4MaterialReportInputs) -> tuple[dict[str, Any], ...]:
    successful = isinstance(inputs.assembly, B4RawAnalysisAssembly)
    source_bytes = inputs.assembly.source_artifact_bytes if successful else ()
    expected_frame_count = 2 * len(inputs.publication.manifest.rows)
    if len(inputs.planned_frames) != expected_frame_count:
        _fail("projection_invalid", "planned arm frame count differs from publication")
    if successful and len(source_bytes) != expected_frame_count:
        _fail("projection_invalid", "assembled source count differs from planned frame")
    rows: list[dict[str, Any]] = []
    for frame in inputs.planned_frames:
        if successful:
            row = _successful_row(
                inputs=inputs,
                row_ordinal=frame.row_ordinal,
                block_ordinal=frame.block_ordinal,
                manifest_row=frame.manifest_row,
                registry_attempt=frame.registry_attempt,
                planned_path=frame.planned_path,
                artifact_availability=frame.artifact_availability,
                arm=frame.arm,
                source_bytes=source_bytes[frame.row_ordinal - 1],
            )
        else:
            row = _rejected_row(
                row_ordinal=frame.row_ordinal,
                block_ordinal=frame.block_ordinal,
                manifest_row=frame.manifest_row,
                registry_attempt=frame.registry_attempt,
                planned_path=frame.planned_path,
                artifact_availability=frame.artifact_availability,
                arm=frame.arm,
            )
        rows.append(row)
    return tuple(rows)


def _project_rows(inputs: B4MaterialReportInputs) -> tuple[dict[str, Any], ...]:
    """Project all manifest blocks before any report bytes are built."""

    return _rows_from_inputs(inputs)


def _assert_complete_projection(
    inputs: B4MaterialReportInputs,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Independently compare every row field with frozen authoritative inputs."""

    required_count = 2 * len(inputs.publication.manifest.rows)
    if len(rows) != required_count:
        _fail("projection_incomplete", f"expected {required_count} arm rows, got {len(rows)}")
    identities = tuple((row.get("attempt_id"), row.get("arm")) for row in rows)
    if len(set(identities)) != required_count:
        _fail("projection_not_bijective", "attempt/arm identities are duplicated")
    attempts = _attempts_by_id(inputs.publication)
    planned = _planned_by_id(inputs.publication)
    expected_frames: list[tuple[object, object, str, str]] = []
    for manifest_row in inputs.publication.manifest.rows:
        attempt = attempts.get(manifest_row.attempt_id)
        planned_path = planned.get(manifest_row.attempt_id)
        if attempt is None or planned_path is None:
            _fail("projection_invalid", "manifest row lacks registry or planned binding")
        for arm in ("on", "off"):
            expected_frames.append((manifest_row, attempt, planned_path, arm))

    row_fields = {
        "row_ordinal", "block_ordinal", "attempt_id", "block_id", "arm",
        "campaign_id", "initial_snapshot_hash", "initial_proposal_sha256",
        "model_prompt_projection_hash", "wal", "stop_reason",
        "budget_consumption", "verdict", "anomaly_class",
        "performance_value_present", "precursor_digest_red_classes",
        "evidence_issues", "planned_attempt_artifact_path",
        "planned_attempt_artifact", "source_artifact_sha256",
        "source_artifact_utf8", "source_object", "reference_snapshot_hash",
        "reference_receipt_hash", "precursor_hash", "driver",
    }
    successful = isinstance(inputs.assembly, B4RawAnalysisAssembly)
    if successful and inputs.analysis_result is None:
        _fail("projection_invalid", "successful assembly has no analysis result")
    source_bytes = inputs.assembly.source_artifact_bytes if successful else ()
    embedded: list[bytes] = []

    for index, (row, frame, authoritative) in enumerate(
        zip(rows, inputs.planned_frames, expected_frames),
        start=1,
    ):
        manifest_row, attempt, planned_path, arm = authoritative
        if set(row) != row_fields:
            _fail("projection_value_mismatch", f"derived row {index} field set differs")
        if (
            frame.row_ordinal != index
            or frame.block_ordinal != (index + 1) // 2
            or frame.manifest_row is not manifest_row
            or frame.registry_attempt is not attempt
            or frame.planned_path != planned_path
            or frame.arm != arm
            or frame.artifact_availability not in {"present", "absent"}
        ):
            _fail("projection_invalid", f"planned arm frame {index} differs from publication")

        common_expected = {
            "row_ordinal": index,
            "block_ordinal": (index + 1) // 2,
            "attempt_id": manifest_row.attempt_id,
            "block_id": manifest_row.block_id,
            "arm": arm,
            "initial_snapshot_hash": {
                "availability": "present",
                "binding": "transcribed",
                "non_guarantee": _INITIAL_PROPOSAL_NON_GUARANTEE,
                "source": "registry.initial_proposal_sha256",
                "value": attempt.initial_proposal_sha256,
            },
            "initial_proposal_sha256": attempt.initial_proposal_sha256,
            "budget_consumption": dict(_ABSENT),
            "anomaly_class": dict(_ABSENT),
            "precursor_digest_red_classes": [
                item.value for item in attempt.digest_red_classes
            ],
            "planned_attempt_artifact_path": planned_path,
            "planned_attempt_artifact": {
                "availability": frame.artifact_availability,
                "observed_path": planned_path,
            },
            "reference_snapshot_hash": manifest_row.reference_snapshot_hash,
            "reference_receipt_hash": manifest_row.reference_receipt_hash,
            "driver": manifest_row.driver,
        }
        for field, wanted in common_expected.items():
            if row[field] != wanted:
                _fail("projection_value_mismatch", f"derived row {index} field {field} differs")

        if successful:
            data = source_bytes[index - 1]
            embedded.append(row["source_artifact_utf8"].encode("utf-8"))
            source = _source_object(data)
            identity = source.get("identity")
            raw = source.get("raw")
            receipt = source.get("receipt_projection")
            evidence = source.get("evidence")
            binding = source.get("binding")
            if not all(
                type(item) is dict
                for item in (identity, raw, receipt, evidence, binding)
            ):
                _fail("projection_invalid", f"source object {index} sections are invalid")
            wal_value = evidence.get("wal")
            if type(wal_value) is not dict:
                _fail("projection_invalid", f"source object {index} WAL is invalid")
            successful_expected = {
                "campaign_id": identity.get("campaign_id"),
                "model_prompt_projection_hash": {
                    "availability": "partial",
                    "model_hash": dict(_ABSENT),
                    "model_snapshot": receipt.get("model_snapshot"),
                    "prompt_sha256": receipt.get("effective_prompt_sha256"),
                    "projection_sha256": receipt.get("projection_sha256"),
                },
                "wal": {
                    "path": wal_value.get("path"),
                    "sha256": wal_value.get("sha256"),
                },
                "stop_reason": {
                    "execution_disposition": raw.get("execution_disposition"),
                    "terminal_stage": raw.get("terminal_stage"),
                    "terminal_reason": raw.get("terminal_reason"),
                },
                "verdict": {
                    "availability": "present",
                    "scope": "experiment",
                    "value": inputs.analysis_result.verdict.value,
                },
                "performance_value_present": raw.get("throughput") is not None,
                "evidence_issues": source.get("evidence_issues"),
                "source_artifact_sha256": hashlib.sha256(data).hexdigest(),
                "source_artifact_utf8": data.decode("utf-8"),
                "source_object": source,
                "precursor_hash": binding.get("precursor_hash"),
            }
            for field, wanted in successful_expected.items():
                if row[field] != wanted:
                    _fail("projection_value_mismatch", f"derived row {index} field {field} differs")
        else:
            unavailable = "assembly_rejected"
            rejected_expected = {
                "campaign_id": _unavailable_field(unavailable),
                "model_prompt_projection_hash": _unavailable_field(unavailable),
                "wal": _unavailable_field(unavailable),
                "stop_reason": _unavailable_field(unavailable),
                "verdict": _unavailable_field("assembly_rejected_not_evaluated"),
                "performance_value_present": _unavailable_field(unavailable),
                "evidence_issues": _unavailable_field(unavailable),
                "source_artifact_sha256": _unavailable_field(unavailable),
                "source_artifact_utf8": _unavailable_field(unavailable),
                "source_object": _unavailable_field(unavailable),
                "precursor_hash": _unavailable_field(unavailable),
            }
            for field, wanted in rejected_expected.items():
                if row[field] != wanted:
                    _fail("projection_value_mismatch", f"derived row {index} field {field} differs")

    if successful:
        if tuple(embedded) != source_bytes:
            _fail("projection_source_mismatch", "source UTF-8 bytes do not round-trip")
        hashes = tuple(hashlib.sha256(item).hexdigest() for item in embedded)
        if len(set(hashes)) != required_count:
            _fail("projection_not_bijective", "source artifacts are not one-to-one")


def _artifact_projection(path: str, data: bytes) -> dict[str, Any]:
    return {
        "path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "utf8": data.decode("utf-8"),
    }


def _rejection_history(inputs: B4MaterialReportInputs) -> B4RawRecordRejectionHistory:
    assembly = inputs.assembly
    if isinstance(assembly, (B4RawAnalysisAssembly, B4RawAnalysisRejection)):
        return assembly.rejection_history
    _fail(
        "assembly_contract_error",
        "assembler result lacks an independent rejection-history snapshot",
    )


def _rejection_wire(rejection: B4RawRecordRejection) -> dict[str, Any]:
    return {
        "schema_version": rejection.schema_version,
        "attempt_id": rejection.attempt_id,
        "issues": _wire_value(rejection.issues),
    }


def _assembly_projection(inputs: B4MaterialReportInputs) -> dict[str, Any]:
    if isinstance(inputs.assembly, B4RawRecordRejection):
        return {
            "status": "rejected",
            "reason": _rejection_wire(inputs.assembly),
            "analysis_status": "not_evaluated",
            "analysis_reason": "assembly_rejected",
        }
    return {
        "status": "assembled",
        "raw_analysis_sha256": inputs.assembly.sha256,
        "planned_attempt_artifact_paths": list(
            inputs.assembly.planned_attempt_artifact_paths
        ),
        "source_artifact_count": len(inputs.assembly.source_artifact_bytes),
    }


def _producer_rejections_projection(
    inputs: B4MaterialReportInputs,
) -> dict[str, Any]:
    publication = inputs.publication
    history = _rejection_history(inputs)
    scheduled_ids = {
        attempt.attempt_id for attempt in publication.registry.scheduled_attempts
    }
    manifest_ids = {row.attempt_id for row in publication.manifest.rows}
    frame_availability = {
        frame.manifest_row.attempt_id: frame.artifact_availability
        for frame in inputs.planned_frames
    }
    event_attempt_ids = (
        {
            event.attempt_id
            for event in history.events
            if event.attempt_id is not None
        }
        if history.status == "readable"
        else set()
    )
    unresolved = [
        {
            "attempt_id": planned.attempt_id,
            "planned_result_artifact_path": planned.artifact_path,
            "reason": "absent_without_recorded_rejection_event",
        }
        for planned in publication.planned_result_artifacts
        if planned.attempt_id in manifest_ids
        and frame_availability.get(planned.attempt_id) == "absent"
        and planned.attempt_id not in event_attempt_ids
    ]
    not_selected = [
        {
            "attempt_id": planned.attempt_id,
            "planned_result_artifact_path": planned.artifact_path,
            "status": "not_selected",
        }
        for planned in publication.planned_result_artifacts
        if planned.attempt_id not in manifest_ids
    ]
    scoped_recorded_attempts = event_attempt_ids & scheduled_ids
    scheduled_count = len(publication.registry.scheduled_attempts)
    return {
        "events": _wire_value(history.events),
        "scheduled_attempt_count": scheduled_count,
        "planned_result_artifact_count": len(
            publication.planned_result_artifacts
        ),
        "manifest_selected_block_count": len(publication.manifest.rows),
        "not_selected": not_selected,
        "unresolved_absent_attempts": unresolved,
        "rejection_history_status": {
            "path": history.path,
            "status": history.status,
            "readable": history.status in {"absent", "readable"},
            "fragment_discarded": history.fragment_discarded,
            "detail": history.detail,
        },
        "recorded_rejection_event_count": {
            "value": len(history.events),
            "population": "events_in_observed_readable_ledger_prefix",
            "caveat": _RECORDED_REJECTION_COUNT_CAVEAT,
        },
        "recorded_scheduled_attempt_rejection_rate": {
            "numerator": len(scoped_recorded_attempts),
            "denominator": scheduled_count,
            "population": "issuer_scheduled_attempts_joined_to_recorded_events",
            "caveat": _RECORDED_REJECTION_RATE_CAVEAT,
        },
    }


def _report_non_guarantees(
    history: B4RawRecordRejectionHistory,
) -> list[str]:
    values = [
        _CURRENT_ABSENT_REASON_NON_GUARANTEE,
        _REJECTION_LEDGER_TRUNCATION_NON_GUARANTEE,
        _OBSERVATION_TIME_NON_GUARANTEE,
    ]
    if history.status != "readable":
        values.insert(0, _HISTORICAL_REJECTION_NON_GUARANTEE)
    return values


def _build_report_value(
    inputs: B4MaterialReportInputs,
    rows: Sequence[Mapping[str, Any]],
    reproduction_argv: Sequence[str],
) -> dict[str, Any]:
    publication = inputs.publication
    rejection_history = _rejection_history(inputs)
    report_non_guarantees = _report_non_guarantees(rejection_history)
    raw_projection: dict[str, Any]
    analysis_projection: dict[str, Any]
    if isinstance(inputs.assembly, B4RawAnalysisAssembly):
        raw_projection = _artifact_projection(
            "assembled-in-memory:b4-raw-analysis",
            inputs.assembly.canonical_bytes,
        )
        analysis_projection = {
            "status": "evaluated",
            "floor_argument": None,
            "result": _wire_value(inputs.analysis_result),
        }
    else:
        raw_projection = _unavailable_field("assembly_rejected")
        analysis_projection = {
            "status": "not_evaluated",
            "floor_argument": None,
            "reason": "assembly_rejected",
            "result": None,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "generator_identity": GENERATOR_IDENTITY,
        "report_scope": {
            "kind": "evidence-only",
            "preregistration_section_5": "not_in_effect",
            "floor_availability": "absent",
            "expected_analysis_verdict": "protocol_violation",
            "expected_analysis_reason": "floor_domain_error",
            "section_7_1_four_classifications_operationalized": False,
        },
        "certification_scope": {
            "certifying": False,
            "closed_world": False,
            "checked": [
                "publication_loader",
                "producer_source_rederivation_when_assembly_succeeds",
                "analysis_byte_binding_when_assembly_succeeds",
                "report_projection_bijection",
            ],
            "not_guaranteed": [
                "research_success_or_novelty",
                "certified_selection_connection",
                "authoritative_floor_artifact",
                *report_non_guarantees,
            ],
        },
        "floor": {
            "availability": "absent",
            "reason": "preregistration_section_5_unfilled",
            "source": None,
            "value": None,
        },
        "provenance": {
            "publication_root": publication.publication_root,
            "issuer_commitment_sha256": publication.issuer_commitment_sha256,
            "contract_binding": (
                _wire_value(inputs.contract_binding)
                if inputs.contract_binding is not None
                else _unavailable_field("assembly_rejected")
            ),
            "artifacts": {
                "registry": _artifact_projection(
                    publication.registry_path,
                    publication.registry.canonical_bytes,
                ),
                "manifest": _artifact_projection(
                    publication.manifest_path,
                    publication.manifest.canonical_bytes,
                ),
                "issuer_receipt": _artifact_projection(
                    publication.receipt_path,
                    publication.receipt_canonical_bytes,
                ),
                "raw_analysis": raw_projection,
            },
            "issuer_non_guarantees": list(publication.non_guarantees),
            "producer_non_guarantees": list(B4_RAW_RECORD_NON_GUARANTEES),
            "report_non_guarantees": report_non_guarantees,
            "reproduction_argv": list(reproduction_argv),
        },
        "campaign_disjointness": {
            "status": inputs.campaign_root_discovery.status,
            "expanded_partial_rejection_applied": (
                inputs.campaign_root_discovery.status == "partial"
            ),
            "campaign_roots": [
                str(root) for root in inputs.campaign_root_discovery.roots
            ],
            "unresolved": list(inputs.campaign_root_discovery.unresolved),
        },
        "producer_rejections": _producer_rejections_projection(inputs),
        "assembly": _assembly_projection(inputs),
        "analysis": analysis_projection,
        "block_count": len(publication.manifest.rows),
        "arm_row_count": len(rows),
        "rows": list(rows),
    }


def _authoritative_floor_source(
    authoritative_floor: B4AuthoritativeFloor,
) -> dict[str, str]:
    return {
        "artifact_path": authoritative_floor.artifact_path,
        "artifact_sha256": authoritative_floor.artifact_sha256,
        "schema_version": authoritative_floor.schema_version,
        "generator_identity": authoritative_floor.generator_identity,
    }


def _apply_authoritative_floor_projection(
    inputs: B4MaterialReportInputs,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Overlay only the present-floor fields on the unchanged absent report."""

    authoritative_floor = inputs.authoritative_floor
    if authoritative_floor is None:
        return report

    ratio = [
        authoritative_floor.floor.numerator,
        authoritative_floor.floor.denominator,
    ]
    report["floor"] = {
        "availability": "present",
        "reason": None,
        "source": _authoritative_floor_source(authoritative_floor),
        "value": ratio,
    }
    report_scope = report["report_scope"]
    report_scope["floor_availability"] = "present"
    report_scope["expected_analysis_verdict"] = None
    report_scope["expected_analysis_reason"] = None

    not_guaranteed = report["certification_scope"]["not_guaranteed"]
    not_guaranteed.remove("authoritative_floor_artifact")
    not_guaranteed.extend(authoritative_floor.non_guarantees)
    report["provenance"]["report_non_guarantees"].extend(
        authoritative_floor.non_guarantees
    )

    analysis = report["analysis"]
    if analysis["status"] == "evaluated":
        analysis["floor_argument"] = ratio
    return report


def _assert_report_provenance(
    inputs: B4MaterialReportInputs,
    report: Mapping[str, Any],
) -> None:
    expected_binding = (
        _wire_value(inputs.contract_binding)
        if inputs.contract_binding is not None
        else _unavailable_field("assembly_rejected")
    )
    if report["provenance"]["contract_binding"] != expected_binding:
        _fail("provenance_mismatch", "contract binding differs")
    if report["producer_rejections"] != _producer_rejections_projection(inputs):
        _fail("provenance_mismatch", "producer rejection history differs")
    artifacts = report["provenance"]["artifacts"]
    expected = (
        ("registry", inputs.publication.registry.canonical_bytes),
        ("manifest", inputs.publication.manifest.canonical_bytes),
        ("issuer_receipt", inputs.publication.receipt_canonical_bytes),
    )
    for name, data in expected:
        item = artifacts[name]
        if item["utf8"].encode("utf-8") != data:
            _fail("provenance_mismatch", f"{name} UTF-8 does not round-trip")
        if item["sha256"] != hashlib.sha256(data).hexdigest():
            _fail("provenance_mismatch", f"{name} SHA-256 differs")
    if isinstance(inputs.assembly, B4RawAnalysisAssembly):
        raw = artifacts["raw_analysis"]
        if raw["utf8"].encode("utf-8") != inputs.assembly.canonical_bytes:
            _fail("provenance_mismatch", "raw analysis UTF-8 does not round-trip")
        if raw["sha256"] != inputs.assembly.sha256:
            _fail("provenance_mismatch", "raw analysis SHA-256 differs")


def _assert_authoritative_floor_projection(
    inputs: B4MaterialReportInputs,
    report: Mapping[str, Any],
) -> None:
    authoritative_floor = inputs.authoritative_floor
    if authoritative_floor is None:
        return

    ratio = [
        authoritative_floor.floor.numerator,
        authoritative_floor.floor.denominator,
    ]
    expected_floor = {
        "availability": "present",
        "reason": None,
        "source": _authoritative_floor_source(authoritative_floor),
        "value": ratio,
    }
    if report["floor"] != expected_floor:
        _fail("authoritative_floor_projection_mismatch", "floor projection differs")

    report_scope = report["report_scope"]
    expected_scope = {
        "kind": "evidence-only",
        "preregistration_section_5": "not_in_effect",
        "floor_availability": "present",
        "expected_analysis_verdict": None,
        "expected_analysis_reason": None,
        "section_7_1_four_classifications_operationalized": False,
    }
    if report_scope != expected_scope:
        _fail(
            "authoritative_floor_projection_mismatch",
            "report scope differs",
        )

    analysis = report["analysis"]
    expected_floor_argument = ratio if analysis["status"] == "evaluated" else None
    if analysis["floor_argument"] != expected_floor_argument:
        _fail(
            "authoritative_floor_projection_mismatch",
            "analysis floor argument differs from evaluator reachability",
        )


def _display(value: object) -> str:
    if type(value) is dict and value.get("availability") == "absent":
        return "不在"
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    else:
        text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", " ")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _render_markdown(report: Mapping[str, Any], json_sha256: str) -> bytes:
    analysis = report["analysis"]
    result = analysis.get("result")
    verdict = None if result is None else result.get("verdict")
    provenance = report["provenance"]
    artifacts = provenance["artifacts"]
    assembly_reason = report["assembly"].get("reason")
    producer_rejections = report.get("producer_rejections")
    lines = [
        "# B-4 evidence-only material report",
        "",
        f"- schema: `{report['schema_version']}`",
        f"- report JSON SHA-256: `{json_sha256}`",
        "- preregistration section 5: not in effect",
        "- floor: unavailable",
        f"- assembly status: `{report['assembly']['status']}`",
        f"- assembly rejection reason: `{_display(assembly_reason)}`",
        f"- analysis status: `{analysis['status']}`",
        f"- analysis verdict: `{verdict if verdict is not None else 'not_evaluated'}`",
        f"- campaign disjointness: `{report['campaign_disjointness']['status']}`",
        f"- publication root: `{_display(provenance['publication_root'])}`",
    ]
    if producer_rejections is not None:
        history_status = producer_rejections["rejection_history_status"]
        event_count = producer_rejections["recorded_rejection_event_count"]
        rejection_rate = producer_rejections[
            "recorded_scheduled_attempt_rejection_rate"
        ]
        lines.extend([
            f"- rejection history status: `{_display(history_status)}`",
            f"- recorded rejection event count: `{event_count['value']}`",
            "- recorded rejection event count caveat: "
            f"`{_display(event_count['caveat'])}`",
            "- recorded scheduled-attempt rejection rate: "
            f"`{rejection_rate['numerator']}/{rejection_rate['denominator']}`",
            "- recorded rejection rate caveat: "
            f"`{_display(rejection_rate['caveat'])}`",
            "- unresolved absent attempts: "
            f"`{len(producer_rejections['unresolved_absent_attempts'])}`",
            "- manifest-non-selected scheduled attempts: "
            f"`{len(producer_rejections['not_selected'])}`",
        ])
    lines.extend([
        f"- reproduction argv (JSON): `{_display(provenance['reproduction_argv'])}`",
        "- certification: this report does not certify a selection",
        "",
        "## Provenance artifact hashes",
        "",
        "| artifact | path | SHA-256 |",
        "|---|---|---|",
    ])
    for name in ("registry", "manifest", "issuer_receipt", "raw_analysis"):
        artifact = artifacts[name]
        lines.append(
            "| "
            + " | ".join((
                _display(name),
                _display(artifact.get("path")),
                _display(artifact.get("sha256")),
            ))
            + " |"
        )
    lines.extend([
        "",
        "## Complete arm projection",
        "",
        "The machine-readable JSON is the complete projection. This Markdown is its deterministic table view.",
        "",
        "| row | block | arm | campaign | initial snapshot | model/prompt/projection | WAL path/hash | artifact | stop reason | budget | verdict | anomaly class | performance value | precursor red classes | evidence issues |",
        "|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    for row in report["rows"]:
        lines.append(
            "| "
            + " | ".join(
                (
                    str(row["row_ordinal"]),
                    _display(row["block_id"]),
                    _display(row["arm"]),
                    _display(row["campaign_id"]),
                    _display(row["initial_snapshot_hash"]),
                    _display(row["model_prompt_projection_hash"]),
                    _display(row["wal"]),
                    _display(row["planned_attempt_artifact"]["availability"]),
                    _display(row["stop_reason"]),
                    _display(row["budget_consumption"]),
                    _display(row["verdict"]),
                    _display(row["anomaly_class"]),
                    _display(row["performance_value_present"]),
                    _display(row["precursor_digest_red_classes"]),
                    _display(row["evidence_issues"]),
                )
            )
            + " |"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _render_markdown_with_authoritative_floor(
    report: Mapping[str, Any],
    json_sha256: str,
    authoritative_floor: B4AuthoritativeFloor | None,
) -> bytes:
    rendered = _render_markdown(report, json_sha256)
    if authoritative_floor is None:
        return rendered

    needle = b"- floor: unavailable\n"
    if rendered.count(needle) != 1:
        _fail(
            "authoritative_floor_projection_mismatch",
            "legacy floor Markdown row is not unique",
        )
    ratio = [
        authoritative_floor.floor.numerator,
        authoritative_floor.floor.denominator,
    ]
    replacement = (
        f"- floor: `{_display(ratio)}`\n"
        f"- floor artifact path: `{_display(authoritative_floor.artifact_path)}`\n"
        f"- floor artifact SHA-256: `{authoritative_floor.artifact_sha256}`\n"
    ).encode("utf-8")
    return rendered.replace(needle, replacement)


def build_material_report_document(
    publication_root: str | Path,
    *,
    reproduction_argv: Sequence[str] | None = None,
) -> B4MaterialReportDocument:
    """Build and validate report bytes without writing an output file."""

    publication_path = Path(publication_root)
    inputs = _load_and_evaluate(publication_path)
    rows = _project_rows(inputs)
    _assert_complete_projection(inputs, rows)
    argv = tuple(reproduction_argv or (
        "python3",
        GENERATOR_IDENTITY,
        inputs.publication.publication_root,
    ))
    report = _apply_authoritative_floor_projection(
        inputs,
        _build_report_value(inputs, rows, argv),
    )
    _assert_report_provenance(inputs, report)
    _assert_authoritative_floor_projection(inputs, report)
    json_bytes = _canonical_json_bytes(report)
    json_sha256 = hashlib.sha256(json_bytes).hexdigest()
    markdown_bytes = _render_markdown_with_authoritative_floor(
        report,
        json_sha256,
        inputs.authoritative_floor,
    )
    return B4MaterialReportDocument(
        json_value=report,
        json_bytes=json_bytes,
        markdown_bytes=markdown_bytes,
        json_sha256=json_sha256,
    )


def _assert_no_symlink_components(path: Path) -> None:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current /= component
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            return
        except OSError as exc:
            _fail("output_path_inspection_failed", str(exc), cause=exc)
        if stat.S_ISLNK(mode):
            _fail("output_symlink_component", f"symlink component rejected: {current}")


def _resolve_output_root(
    publication_root: str | Path,
    output_root: str | Path | None,
) -> Path:
    publication = Path(publication_root)
    candidate = publication / "reports" if output_root is None else Path(output_root)
    _assert_no_symlink_components(candidate)
    absolute_candidate = candidate if candidate.is_absolute() else Path.cwd() / candidate
    try:
        mode = os.lstat(absolute_candidate).st_mode
    except FileNotFoundError:
        pass
    except OSError as exc:
        _fail("output_path_inspection_failed", str(exc), cause=exc)
    else:
        if not stat.S_ISDIR(mode):
            _fail("output_root_invalid", "existing output root is not a directory")
    return candidate.resolve(strict=False)


def _assert_output_absent(output_root: Path) -> None:
    targets = (
        output_root / REPORT_JSON_NAME,
        output_root / REPORT_MARKDOWN_NAME,
        output_root / REPORT_COMMIT_NAME,
    )
    existing = [str(path) for path in targets if os.path.lexists(path)]
    if existing:
        _fail("output_exists", "refusing to overwrite: " + ", ".join(existing))


def _campaign_root_from_source(source: Mapping[str, Any]) -> Path | None:
    evidence = source.get("evidence")
    if type(evidence) is not dict:
        return None
    campaign_lock = evidence.get("campaign_lock")
    lock_path = campaign_lock.get("path") if type(campaign_lock) is dict else None
    if type(lock_path) is str and lock_path:
        return Path(lock_path).resolve(strict=False).parent
    wal_value = evidence.get("wal")
    wal_path = wal_value.get("path") if type(wal_value) is dict else None
    if type(wal_path) is str and wal_path:
        resolved_wal = Path(wal_path).resolve(strict=False)
        if len(resolved_wal.parents) >= 2:
            return resolved_wal.parents[1]
    return None


def _discover_campaign_roots(
    *,
    publication: B4PrerunPublication,
    planned_frames: Sequence[_B4PlannedArmFrame],
    assembly: B4RawAnalysisAssembly | B4RawRecordRejection,
) -> _CampaignRootDiscovery:
    """Recover campaign roots while retaining every unresolved source."""

    labelled_sources: list[tuple[str, Mapping[str, Any]]] = []
    unresolved: list[dict[str, str]] = []
    if isinstance(assembly, B4RawAnalysisAssembly):
        labelled_sources.extend(
            (f"assembled_source:{index}", _source_object(data))
            for index, data in enumerate(assembly.source_artifact_bytes, start=1)
        )
    else:
        frames_by_attempt = {
            frame.manifest_row.attempt_id: frame
            for frame in planned_frames
        }
        for planned in publication.planned_result_artifacts:
            frame = frames_by_attempt.get(planned.attempt_id)
            if frame is None:
                continue
            label = f"planned_attempt:{planned.attempt_id}"
            if frame.artifact_availability == "absent":
                unresolved.append({
                    "source": label,
                    "path": planned.artifact_path,
                    "reason": "artifact_absent_at_frozen_observation",
                })
                continue
            try:
                value = _source_object(Path(planned.artifact_path).read_bytes())
            except (OSError, B4MaterialReportError) as exc:
                unresolved.append({
                    "source": label,
                    "path": planned.artifact_path,
                    "reason": f"artifact_unreadable_or_invalid:{type(exc).__name__}",
                })
                continue
            arm_sources = value.get("arm_sources")
            if type(arm_sources) is not list or len(arm_sources) != 2:
                unresolved.append({
                    "source": label,
                    "path": planned.artifact_path,
                    "reason": "arm_sources_not_exact_pair",
                })
                continue
            for arm_index, source in enumerate(arm_sources, start=1):
                if type(source) is not dict:
                    unresolved.append({
                        "source": f"{label}:arm:{arm_index}",
                        "path": planned.artifact_path,
                        "reason": "arm_source_not_object",
                    })
                else:
                    labelled_sources.append((f"{label}:arm:{arm_index}", source))

    roots: set[Path] = set()
    for label, source in labelled_sources:
        root = _campaign_root_from_source(source)
        if root is None:
            unresolved.append({
                "source": label,
                "path": "",
                "reason": "campaign_root_not_derivable",
            })
        else:
            roots.add(root)
    return _CampaignRootDiscovery(
        roots=tuple(sorted(roots, key=str)),
        status="complete" if not unresolved else "partial",
        unresolved=tuple(unresolved),
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _assert_output_disjoint_from_campaigns(
    output_root: Path,
    discovery: _CampaignRootDiscovery,
) -> None:
    resolved_output = output_root.resolve(strict=False)
    for campaign_root in discovery.roots:
        resolved_campaign = campaign_root.resolve(strict=False)
        if resolved_output == resolved_campaign:
            _fail("output_campaign_intersection", "output root equals an arm campaign root")
        if _is_relative_to(resolved_output, resolved_campaign):
            _fail("output_campaign_intersection", "output root is below an arm campaign root")
        if _is_relative_to(resolved_campaign, resolved_output):
            _fail("output_campaign_intersection", "output root is above an arm campaign root")
    if discovery.status == "partial":
        parts = resolved_output.parts
        has_campaigns_component = "campaigns" in parts
        intersects_campaign_parent = False
        for campaign_root in discovery.roots:
            campaign_parent = campaign_root.resolve(strict=False).parent
            if (
                resolved_output == campaign_parent
                or _is_relative_to(resolved_output, campaign_parent)
                or _is_relative_to(campaign_parent, resolved_output)
            ):
                intersects_campaign_parent = True
                break
        if has_campaigns_component or intersects_campaign_parent:
            _fail(
                "output_campaign_disjointness_unproven",
                "partial campaign-root discovery rejects campaigns-component "
                "or recovered-campaign-parent intersection",
            )


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            _fail("output_io_error", "short write while staging report")
        offset += written


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError as exc:
        _fail("output_io_error", f"cannot open directory for fsync: {path}: {exc}", cause=exc)
    try:
        os.fsync(fd)
    except OSError as exc:
        _fail("output_io_error", f"cannot fsync directory: {path}: {exc}", cause=exc)
    finally:
        os.close(fd)


def _publish_pair_no_overwrite(
    output_root: Path,
    json_bytes: bytes,
    markdown_bytes: bytes,
) -> None:
    output_root_existed = output_root.exists()
    try:
        output_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _fail("output_io_error", f"cannot create output root: {exc}", cause=exc)
    _assert_no_symlink_components(output_root)
    if output_root.resolve(strict=True) != output_root:
        _fail("output_path_changed", "resolved output root changed before write")
    if not output_root_existed:
        _fsync_directory(output_root.parent)
    _assert_output_absent(output_root)
    commit_bytes = _canonical_json_bytes({
        "schema_version": "p3-b4-material-report-commit/v1",
        "report_json_sha256": hashlib.sha256(json_bytes).hexdigest(),
        "report_markdown_sha256": hashlib.sha256(markdown_bytes).hexdigest(),
    })
    staged: list[Path] = []
    published: list[Path] = []
    try:
        for name, data in (
            (REPORT_JSON_NAME, json_bytes),
            (REPORT_MARKDOWN_NAME, markdown_bytes),
            (REPORT_COMMIT_NAME, commit_bytes),
        ):
            fd, temporary_name = tempfile.mkstemp(prefix=f".{name}.", dir=output_root)
            temporary = Path(temporary_name)
            staged.append(temporary)
            try:
                _write_all(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
        for temporary, name in zip(staged[:2], (REPORT_JSON_NAME, REPORT_MARKDOWN_NAME)):
            target = output_root / name
            try:
                os.link(temporary, target, follow_symlinks=False)
            except FileExistsError as exc:
                _fail("output_exists", f"refusing to overwrite: {target}", cause=exc)
            except OSError as exc:
                _fail("output_io_error", f"cannot publish {target}: {exc}", cause=exc)
            published.append(target)
        _fsync_directory(output_root)
        commit_target = output_root / REPORT_COMMIT_NAME
        try:
            os.link(staged[2], commit_target, follow_symlinks=False)
        except FileExistsError as exc:
            _fail("output_exists", f"refusing to overwrite: {commit_target}", cause=exc)
        except OSError as exc:
            _fail("output_io_error", f"cannot publish {commit_target}: {exc}", cause=exc)
        published.append(commit_target)
        _fsync_directory(output_root)
    except BaseException as original:
        rollback_errors: list[str] = []
        for target in reversed(published):
            try:
                target.unlink()
            except OSError as exc:
                rollback_errors.append(f"unlink {target}: {exc}")
        try:
            _fsync_directory(output_root)
        except B4MaterialReportError as exc:
            rollback_errors.append(str(exc))
        if rollback_errors:
            _fail(
                "output_rollback_error",
                "; ".join(rollback_errors),
                cause=original,
            )
        raise
    finally:
        cleanup_errors: list[str] = []
        for temporary in staged:
            try:
                temporary.unlink()
            except FileNotFoundError:
                continue
            except OSError as exc:
                cleanup_errors.append(f"unlink {temporary}: {exc}")
        if cleanup_errors and sys.exc_info()[0] is None:
            _fail("output_cleanup_error", "; ".join(cleanup_errors))
    _fsync_directory(output_root)


def write_material_report(
    publication_root: str | Path,
    *,
    output_root: str | Path | None = None,
) -> B4MaterialReportWrite:
    """Build and create the JSON/Markdown pair without overwriting either file."""

    publication_path = Path(publication_root)
    resolved_output = _resolve_output_root(publication_path, output_root)
    _assert_output_absent(resolved_output)
    inputs = _load_and_evaluate(publication_path)
    argv = ["python3", GENERATOR_IDENTITY, inputs.publication.publication_root]
    if output_root is not None:
        argv.extend(("--output-root", str(resolved_output)))
    rows = _project_rows(inputs)
    _assert_complete_projection(inputs, rows)
    report = _apply_authoritative_floor_projection(
        inputs,
        _build_report_value(inputs, rows, argv),
    )
    _assert_report_provenance(inputs, report)
    _assert_authoritative_floor_projection(inputs, report)
    json_bytes = _canonical_json_bytes(report)
    json_sha256 = hashlib.sha256(json_bytes).hexdigest()
    markdown_bytes = _render_markdown_with_authoritative_floor(
        report,
        json_sha256,
        inputs.authoritative_floor,
    )

    _assert_output_disjoint_from_campaigns(
        resolved_output,
        inputs.campaign_root_discovery,
    )
    _publish_pair_no_overwrite(resolved_output, json_bytes, markdown_bytes)
    return B4MaterialReportWrite(
        report_json_path=str(resolved_output / REPORT_JSON_NAME),
        report_md_path=str(resolved_output / REPORT_MARKDOWN_NAME),
        report_commit_path=str(resolved_output / REPORT_COMMIT_NAME),
        report_json_sha256=json_sha256,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an evidence-only B-4 material report.",
    )
    parser.add_argument("publication_root")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args(argv)
    if not args.publication_root:
        parser.error("publication_root must not be empty")
    if args.output_root == "":
        parser.error("--output-root must not be empty")
    try:
        result = write_material_report(
            args.publication_root,
            output_root=args.output_root,
        )
    except B4MaterialReportError as exc:
        parser.error(str(exc))
    print(result.report_json_path)
    print(result.report_md_path)
    return 0


__all__ = [
    "B4MaterialReportDocument",
    "B4MaterialReportError",
    "B4MaterialReportInputs",
    "B4MaterialReportWrite",
    "GENERATOR_IDENTITY",
    "REPORT_COMMIT_NAME",
    "REPORT_JSON_NAME",
    "REPORT_MARKDOWN_NAME",
    "SCHEMA_VERSION",
    "build_material_report_document",
    "main",
    "write_material_report",
]


if __name__ == "__main__":  # pragma: no cover - exercised by clean subprocess
    raise SystemExit(main())
