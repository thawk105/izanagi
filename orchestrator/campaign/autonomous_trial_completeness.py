# -*- coding: utf-8 -*-
"""Autonomous trial journal/report completeness verification.

The write-time entry point deliberately re-reads ``attempts.jsonl`` from
disk.  Role entries in the producer report are the same objects returned by
``AttemptJournal.append``; comparing two in-memory views would therefore not
independently verify their persisted contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import campaign_lock
from . import layer3_report as _layer3_report
from . import s8b_holdout_freeze
from . import s8b_ratified_freeze
from . import s8c_generation_projection
from . import trigger_gate_binding
from . import wal
from .artifact_admission import (
    ArtifactAdmissionError,
    CampaignReadPurpose,
    require_admitted_campaign,
)
from .layer3_report import canonical_record_ref
from .pin import CURRENT_PIN as _CURRENT_CCBENCH_PIN
from .role_session_isolation import evaluate_role_session_isolation




_EVENTS = frozenset({
    "transport-admission",
    "transport-admission-error",
    "run-start",
    "role-attempt",
    "generation-accounting",
    "supervisor-error",
    "supervisor-wall-budget",
    "provider-init-error",
    "run-finish",
})
_TERMINAL_EVENTS = frozenset({
    "supervisor-error", "supervisor-wall-budget", "provider-init-error",
    "transport-admission-error",
})
_ROLE_ORDER = ("planner", "coder", "auditor", "critic")
_ROLE_FAILURE_PHASES = frozenset({
    "pre-raw-write",
    "raw-write",
    "json-syntax",
    "json-shape",
    "role-schema",
    "parser-error",
})
_ROLE_FAILURE_PHASES_AFTER_RAW_WRITE = frozenset({
    "json-syntax",
    "json-shape",
    "role-schema",
    "parser-error",
})
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT_ID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_ADMISSION_DECISION_KEYS = frozenset({
    "schema_version", "classification", "admission_status",
    "verification_status", "campaign_id", "campaign_path",
    "campaign_lock_sha256", "wal_sha256", "policy_sha256",
    "attempt_receipt_sha256s", "validator", "overlay",
})
_ADMISSION_VALIDATOR_KEYS = frozenset({"identity", "sha256"})
_ADMISSION_OVERLAY_KEYS = frozenset({"ledger_sha256", "record_key"})
_CAMPAIGN_VERIFIER_EPOCH_KEYS = frozenset({
    "campaign_verifier_epoch", "state", "reason_code", "identity_scope",
    "excluded_scope",
})
_HISTORICAL_CAMPAIGN_VERIFIER_EPOCH_KEYS = (
    _CAMPAIGN_VERIFIER_EPOCH_KEYS | {"verifier_assessment_basis"}
)
_VERIFIER_ASSESSMENT_BASIS = "recorded-at-original-verifier-epoch"
_CELL_ADMISSION_FAILURE_SCHEMA = (
    "p3-autonomous-workload-trial-cell-admission-failure/v1"
)
LAYER3_ADMISSION_DIAGNOSIS_KEY = "layer3_admission_diagnosis"
LAYER3_ADMISSION_DIAGNOSIS_SCHEMA_VERSION = (
    "p3-autonomous-workload-trial-layer3-admission-diagnosis/v1"
)
_LAYER3_ADMISSION_DIAGNOSIS_KEYS = frozenset({
    "schema_version", "status", "validator", "validator_value",
    "absolute_instance_path", "absolute_schema_path",
    "offending_property", "degradation_reason",
})
_LAYER3_ADMISSION_DEGRADATION_REASONS = frozenset({
    "validation-error-cause-not-found",
    "validation-error-projection-failed",
})
_PENDING_CRITIC_DISPOSITION_SCHEMA = (
    "p3-autonomous-workload-trial-pending-critic-disposition/v1"
)
_PENDING_CRITIC_DISPOSITION_KEYS = frozenset({
    "schema_version", "action", "reason", "count",
})
_LAUNCH_ADMISSION_BASE_KEYS = frozenset({
    "mode", "certifying", "reason_code", "trial_id", "workloads",
    "binding", "activation_report_digest_sha256",
    "prereg_content_commit", "prereg_effective_commit",
})
_LAUNCH_ADMISSION_EXPLORATORY_KEYS = frozenset(
    _LAUNCH_ADMISSION_BASE_KEYS
    - {"prereg_content_commit", "prereg_effective_commit"}
)
_LAUNCH_ADMISSION_KEYS = frozenset({
    _LAUNCH_ADMISSION_EXPLORATORY_KEYS,
    _LAUNCH_ADMISSION_EXPLORATORY_KEYS | {"origin_binding"},
})
_LAUNCH_ADMISSION_REGISTERED_KEYS = frozenset({
    _LAUNCH_ADMISSION_BASE_KEYS,
    _LAUNCH_ADMISSION_BASE_KEYS | {"origin_binding"},
})
_REGISTERED_LAUNCH_MODES = frozenset({
    "registered-effective",
    "registered-formal-non-certifying",
})
_LAUNCH_ADMISSION_MODES = _REGISTERED_LAUNCH_MODES | {
    "explicit-unregistered-exploratory",
}
_LAUNCH_BINDING_KEYS = frozenset({
    "manifest_sha256", "prereg_commit", "prereg_content_commit",
    "prereg_effective_commit", "measurement_head", "trial_id", "arm",
    "holdout", "campaign_id", "workload", "ycsb_rratio",
})
_ORIGIN_BINDING_KEYS = frozenset({
    "authority_blob_sha256", "source_closure_sha256", "origin_id", "cell_key",
    "authority_workload", "axis_semantics_sha256", "verifier_policy_sha256",
    "environment_contract_sha256", "campaign_id", "trial_workload",
    "measurement_head", "store_scope", "issuer_seal",
})
_ORIGIN_WORKLOAD_KEYS = frozenset({"descriptor_sha256", "records", "threads"})
_ORIGIN_TERMINAL_PROJECTION_BASE_KEYS = frozenset({
    "schema_version", "reason_code", "formal_receipt_sha256",
    "evidence_root_sha256", "authority_blob_sha256", "origin_id", "cell_key",
    "terminal_payload_sha256",
})
_ORIGIN_TERMINAL_PROJECTION_KEYS = frozenset({
    _ORIGIN_TERMINAL_PROJECTION_BASE_KEYS,
    _ORIGIN_TERMINAL_PROJECTION_BASE_KEYS | {"arm_binding_digest_sha256"},
})
_ARM_EXECUTION_KEYS = frozenset({
    "input_schema_version", "content_digest_sha256",
    "arm_binding_digest_sha256",
})
_EXPLORATORY_DESCRIPTOR_BINDING_KEYS = frozenset({
    "input_sha256", "output_sha256", "projection_version", "schema_sha256",
})
_REGISTERED_DESCRIPTOR_BINDING_KEYS = frozenset({
    *_EXPLORATORY_DESCRIPTOR_BINDING_KEYS,
    "content_digest_sha256", "arm_binding_digest_sha256",
})
_DESCRIPTOR_SCHEMA_SHA256 = (
    "5a9e2696b8fba18f8f7cf01183673a1bd6f5781cc9cb1fe8641f9d667fe11549"
)
_AUTONOMOUS_SEARCH_CONFIG_KEYS = frozenset({
    "axis", "descriptor_schema", "descriptor_sha256", "generation_budget",
    "pilot_scope", "records", "reflux", "scale", "stop_policy", "threads",
    "trigger_gate_binding_schema", "verify", "workload", "ycsb",
    "build_admission",
})
_AUTONOMOUS_SPEC_CONTENT = (
    "T-178 exploratory YCSB A/B/C workload-conditioned unattended synthesis. "
    "Python invokes fresh projected planner/coder/auditor/critic roles; existing "
    "trigger-gating quarantine/correctness/performance harness remains authoritative. "
    "Fixed generations, no performance-target early stop, no formal descriptor claim."
)
_ARM_BINDING_DOMAIN_SEPARATOR_V1 = b"izanagi-s8c-arm-binding/v1\0"
_REGISTERED_PROPOSAL_KEYS = frozenset({"path", "sha256", "digest"})
_REGISTERED_PROPOSAL_VALUE_KEYS = frozenset({
    "planner", "coder", "auditor", "prior_critic_reverse",
    "descriptor_sha256", "arm_binding_digest_sha256",
})
_PROVIDER_ARTIFACT_KEYS = frozenset({
    "payload_path", "envelope_path", "arm_binding_digest_sha256",
})
_FORMAL_REASON_CODES = frozenset({
    "FC01", "FC02", "FC03", "FC04", "FC05a", "FC05b", "FC05c", "FC06",
    "FC07", "FC09", "FC10", "P6Unavailable",
})
_GENERATION_DRIVER_WRAPPER = "s8c-generation/v1"
_STANDARD_GENERATION_DRIVER = {
    "wrapper": _GENERATION_DRIVER_WRAPPER,
    "delegate": "trigger.drive_iteration",
}
_INJECTED_GENERATION_DRIVER = {
    "wrapper": _GENERATION_DRIVER_WRAPPER,
    "delegate": "caller-injected-unsupported",
}
_COMMON_PAYLOAD_KEYS = frozenset({
    "schema_version", "pilot_scope", "scientific_claim", "workload",
    "generation", "workload_descriptor", "descriptor_binding",
    "attempt_policy", "stop_policy",
})
S8C_CROSS_BINDING_SCHEMA_VERSION = "p3-8c-cross-binding-receipt/v2"
S8C_CROSS_BINDING_FIELDS = (
    "input_payload_sha256",
    "raw_response_path",
    "raw_response_sha256",
    "provider_payload_sha256",
    "provider_envelope_sha256",
    "proposal_path",
    "proposal_sha256",
    "build_records",
    "bench_records",
    "artifact_refs",
    "source_refs",
    "admission_decision",
    "proposal_build_source_bindings",
)


def is_positive_cell_admission_decision(decision: Any) -> bool:
    """Return the shared exact positive predicate for build cells."""
    return (
        isinstance(decision, Mapping)
        and decision.get("schema_version")
        == "campaign-artifact-admission-decision/v1"
        and decision.get("admission_status") == "admitted"
        and decision.get("classification") == "admitted-new-schema"
    )


def is_exact_cell_admission_failure_decision(decision: Any) -> bool:
    """Recognize only the closed diagnostic failure decision shape."""
    if not isinstance(decision, Mapping) or set(decision) != {
        "schema_version", "admission_status", "error",
    }:
        return False
    error = decision.get("error")
    return (
        decision.get("schema_version") == _CELL_ADMISSION_FAILURE_SCHEMA
        and decision.get("admission_status") == "failed"
        and isinstance(error, Mapping)
        and set(error) == {"type", "message"}
        and error.get("type") == "AutonomousTrialError"
        and type(error.get("message")) is str
        and bool(error["message"])
    )


def is_exact_layer3_admission_diagnosis(value: Any) -> bool:
    """Recognize only the closed, canonical JSON-safe diagnosis contract."""
    if not isinstance(value, Mapping) or set(value) != (
        _LAYER3_ADMISSION_DIAGNOSIS_KEYS
    ):
        return False
    plain = dict(value)
    try:
        encoded = json.dumps(
            plain,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        if json.loads(encoded.decode("utf-8")) != plain:
            return False
    except (TypeError, ValueError, UnicodeError):
        return False
    if value.get("schema_version") != (
        "p3-autonomous-workload-trial-layer3-admission-diagnosis/v1"
    ):
        return False
    instance_path = value.get("absolute_instance_path")
    schema_path = value.get("absolute_schema_path")
    if type(instance_path) is not list or type(schema_path) is not list:
        return False
    if any(
        not (
            type(component) is str
            or (type(component) is int and component >= 0)
        )
        for component in [*instance_path, *schema_path]
    ):
        return False
    offending_property = value.get("offending_property")
    if offending_property is not None and type(offending_property) is not str:
        return False
    status = value.get("status")
    if status == "validation-error":
        validator = value.get("validator")
        return (
            type(validator) is str
            and bool(validator)
            and value.get("degradation_reason") is None
        )
    if status == "degraded":
        return (
            value.get("validator") is None
            and value.get("validator_value") is None
            and instance_path == []
            and schema_path == []
            and offending_property is None
            and value.get("degradation_reason")
            in _LAYER3_ADMISSION_DEGRADATION_REASONS
        )
    return False


def _is_exact_pending_critic_disposition(value: Any) -> bool:
    if not isinstance(value, Mapping) or set(value) != (
        _PENDING_CRITIC_DISPOSITION_KEYS
    ):
        return False
    count = value.get("count")
    return (
        value.get("schema_version") == _PENDING_CRITIC_DISPOSITION_SCHEMA
        and value.get("action") == "discarded"
        and value.get("reason") == "cell-admission-failure"
        and type(count) is int
        and count in {0, 1}
    )


def _is_exact_campaignless_failure_fallback_cell(
    cell: Mapping[str, Any],
) -> bool:
    """Recognize only the producer's no-campaign supervisor fallback cell."""
    error = cell.get("error")
    return (
        set(cell) == {
            "workload", "generations", "stop_reason", "error",
            "admission_decision", "pending_critic_disposition",
        }
        and cell.get("generations") == []
        and cell.get("stop_reason") == "supervisor-error"
        and isinstance(error, Mapping)
        and set(error) == {"type", "message"}
        and type(error.get("type")) is str
        and bool(error["type"])
        and type(error.get("message")) is str
        and is_exact_cell_admission_failure_decision(
            cell.get("admission_decision")
        )
        and _is_exact_pending_critic_disposition(
            cell.get("pending_critic_disposition")
        )
        and cell["pending_critic_disposition"]["count"] == 0
    )


def is_exact_campaignless_failure_fallback_cell(
    cell: Mapping[str, Any],
) -> bool:
    """Expose the producer's campaignless failure-cell projection to consumers."""
    return _is_exact_campaignless_failure_fallback_cell(cell)


def cell_admission_failure_projection(
    cells: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project exact failure decisions into the existing run-finish event."""
    projections: list[dict[str, Any]] = []
    for index, cell in enumerate(cells):
        if not is_exact_cell_admission_failure_decision(
            cell.get("admission_decision")
        ):
            continue
        projection = {
            "cell_index": index,
            "workload": cell.get("workload"),
            "admission_decision": dict(cell["admission_decision"]),
        }
        if LAYER3_ADMISSION_DIAGNOSIS_KEY in cell:
            diagnosis = cell[LAYER3_ADMISSION_DIAGNOSIS_KEY]
            if not is_exact_layer3_admission_diagnosis(diagnosis):
                _fail(
                    "artifact-admission",
                    f"cells[{index}] Layer-3 admission diagnosis is not exact",
                )
            projection[LAYER3_ADMISSION_DIAGNOSIS_KEY] = dict(diagnosis)
        projections.append(projection)
    return projections


_ROLE_PAYLOAD_KEY_SPEC = {
    "planner-generation-1": sorted(_COMMON_PAYLOAD_KEYS | {
        "current_perf", "leading_indicators", "whiteboard",
    }),
    "planner-generation-next": sorted(_COMMON_PAYLOAD_KEYS | {
        "current_perf", "leading_indicators", "whiteboard", "critic_feedback",
    }),
    "coder": sorted(_COMMON_PAYLOAD_KEYS | {
        "leakproof_context", "gating_spec", "planner_direction", "baseline",
        "whiteboard",
    }),
    "auditor": sorted(_COMMON_PAYLOAD_KEYS | {
        "working_diff", "diff_digest", "designated_source_context",
        "correctness_digest",
    }),
    "auditor-skip": sorted(_COMMON_PAYLOAD_KEYS | {"pre_audit"}),
    "critic": sorted(_COMMON_PAYLOAD_KEYS | {
        "harness_result", "critic_digest",
    }),
}
_ROLE_PAYLOAD_ALLOWLIST_SHA256 = hashlib.sha256(
    json.dumps(
        _ROLE_PAYLOAD_KEY_SPEC,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
).hexdigest()
_VALIDATION_RECEIPT_SCHEMA_VERSION = "s8c-role-payload-validation-receipt/v1"
_ROLE_SCHEMA_VERSION = "p3-autonomous-workload-trial/v3"
_PILOT_SCOPE = "exploratory-ycsb-abc"
_LEAKPROOF_CONTEXT = (
    "Use only this campaign's projected descriptor, metrics, planner direction, "
    "and abstract whiteboard. No prior sweep winner, candidate ranking, or "
    "unmeasured performance is available."
)
_PLANNER_AXIS = "silo-backoff-trigger-gating"
_PERF_KEYS = {
    "throughput_ops_sec", "abort_rate_pct", "latency_ns", "llc_miss_rate", "ipc",
}
_LEADING_METRIC_KEYS = {"IPC_overall", "cache_miss_rate_pct"}
_WHITEBOARD_KEYS = {"iteration", "direction", "magnitude", "result", "delta_pct"}
_DIAGNOSTIC_METRICS = ("abort_rate", "latency_ns", "llc_miss_rate", "ipc")


class AutonomousTrialCompletenessError(RuntimeError):
    """Autonomous trial journal/report completeness violation."""


def _fail(gate: str, message: str) -> None:
    raise AutonomousTrialCompletenessError(f"[{gate}] {message}")


def _reject_constant(value: str) -> None:
    _fail("json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes, *, label: str) -> Any:
    try:
        text = data.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except AutonomousTrialCompletenessError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("json", f"{label} is not strict UTF-8 JSON: {exc}")


def _read_journal(path: Path) -> tuple[bytes, list[dict[str, Any]]]:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            f"[journal-read] attempt journal cannot be read: {path}"
        ) from exc
    if not data or not data.endswith(b"\n"):
        _fail("journal-framing", "attempt journal must be non-empty and newline terminated")
    events: list[dict[str, Any]] = []
    for lineno, line in enumerate(data.splitlines(), 1):
        if not line:
            _fail("journal-framing", f"blank journal line: {lineno}")
        value = _decode_json(line, label=f"journal line {lineno}")
        if not isinstance(value, dict):
            _fail("journal-framing", f"journal line {lineno} is not an object")
        events.append(value)
    return data, events


def _read_report(path: Path) -> dict[str, Any]:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            f"[report-read] report cannot be read: {path}"
        ) from exc
    value = _decode_json(data, label="report")
    if not isinstance(value, dict):
        _fail("report-shape", "report root is not an object")
    return value


def _mapping(value: Any, *, gate: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(gate, f"{label} is not an object")
    return value


def _list(value: Any, *, gate: str, label: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(gate, f"{label} is not a list")
    return value


def _path_identity(path: Any, *, gate: str, label: str) -> Path:
    if not isinstance(path, str) or not path:
        _fail(gate, f"{label} is not a non-empty path string")
    return Path(path).resolve()


def _environment_contract_from_campaign_lock(
    campaign_root: Path, *, producer: Any,
) -> Any:
    lock_path = campaign_root / "campaign.lock"
    try:
        raw = lock_path.read_bytes()
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            f"[campaign-chain] campaign.lock cannot be read: {lock_path}"
        ) from exc
    try:
        decoded = campaign_lock.decode_campaign_lock_bytes(raw)
    except campaign_lock.CampaignLockCodecError as exc:
        raise AutonomousTrialCompletenessError(
            "[campaign-chain] campaign.lock schema is invalid"
        ) from exc
    authority = decoded.authority
    if decoded.is_v1 or authority is None:
        _fail(
            "campaign-chain",
            "campaign.lock v2 authority is required for completeness proof",
        )
    contract_sha256 = authority.environment_contract_sha256
    try:
        return producer.env_contract.resolve_by_contract_sha256(
            contract_sha256
        ).contract
    except producer.env_contract.EnvContractError as exc:
        raise AutonomousTrialCompletenessError(
            "[campaign-chain] campaign.lock environment contract is not ever-active"
        ) from exc


def _canonical_ref(record: Mapping[str, Any]) -> str:
    try:
        return canonical_record_ref("wal", record)
    except (TypeError, ValueError, _layer3_report.Layer3ReportError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[role-bijection] role attempt is not canonical JSON: {exc}"
        ) from exc


def _producer_module() -> Any:
    from . import p3_autonomous_workload_trial as producer
    return producer


def _arm_binding_digest(
    *, holdout: str, arm: str, content_digest: str,
) -> str:
    return hashlib.sha256(
        _ARM_BINDING_DOMAIN_SEPARATOR_V1
        + holdout.encode("utf-8")
        + arm.encode("utf-8")
        + content_digest.encode("ascii")
    ).hexdigest()


def _bound_regular_bytes(
    value: Any, *, run_root: Path, gate: str, label: str,
) -> tuple[Path, bytes]:
    if type(value) is not str or not value:
        _fail(gate, f"{label} is not a non-empty path string")
    root = Path(run_root).resolve(strict=True)
    declared = Path(value)
    lexical = Path(os.path.abspath(
        os.fspath(declared if declared.is_absolute() else root / declared)
    ))
    try:
        relative = lexical.relative_to(root)
    except ValueError:
        _fail(gate, f"{label} is outside the run root")
    if not relative.parts:
        _fail(gate, f"{label} is not a regular file")
    cursor = root
    try:
        for component in relative.parts:
            cursor = cursor / component
            metadata = cursor.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                _fail(gate, f"{label} traverses a symlink")
        if not stat.S_ISREG(metadata.st_mode):
            _fail(gate, f"{label} is not a regular file")
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(root)
        return resolved, resolved.read_bytes()
    except AutonomousTrialCompletenessError:
        raise
    except (OSError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[{gate}] {label} cannot be read as a run-root regular file"
        ) from exc


def _read_bound_role_raw_bytes(
    value: Any, *, run_root: Path, gate: str, label: str,
) -> tuple[Path, bytes]:
    bound_path, _preliminary_bytes = _bound_regular_bytes(
        value, run_root=run_root, gate=gate, label=label,
    )
    authority_root = Path(run_root).resolve(strict=True)
    relative = bound_path.relative_to(authority_root)
    directory_fds: list[int] = []
    file_fd: int | None = None
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        directory_fds.append(os.open(authority_root, directory_flags))
        for component in relative.parts[:-1]:
            directory_fds.append(os.open(
                component,
                directory_flags,
                dir_fd=directory_fds[-1],
            ))
        file_fd = os.open(
            relative.parts[-1], file_flags, dir_fd=directory_fds[-1],
        )
        metadata = os.fstat(file_fd)
        if not stat.S_ISREG(metadata.st_mode):
            _fail(gate, f"{label} is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return bound_path, b"".join(chunks)
    except AutonomousTrialCompletenessError:
        raise
    except (OSError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[{gate}] {label} cannot be read from a no-follow file descriptor"
        ) from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for directory_fd in reversed(directory_fds):
            os.close(directory_fd)


def read_and_verify_bytes(
    value: Any,
    *,
    root: Path,
    expected_sha256: Any,
    gate: str,
    label: str,
) -> tuple[Path, bytes]:
    """Read one declared byte stream beneath an explicit authority root.

    This helper intentionally does not delegate relative-path resolution to
    ``_bound_regular_bytes``.  The latter is retained for older producer
    checks, while this consumer must bind a relative reference to the root
    supplied by its caller rather than to the process working directory.
    """
    if type(value) is not str or not value:
        _fail(gate, f"{label} is not a non-empty path string")
    if type(expected_sha256) is not str or _SHA256_RE.fullmatch(expected_sha256) is None:
        _fail(gate, f"{label} expected_sha256 is not a lowercase SHA-256")
    try:
        authority_root = Path(root).resolve(strict=True)
        if not authority_root.is_dir():
            _fail(gate, f"{label} authority root is not a directory")
    except AutonomousTrialCompletenessError:
        raise
    except (OSError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[{gate}] {label} authority root cannot be resolved"
        ) from exc

    declared = Path(value)
    lexical = Path(os.path.abspath(
        os.fspath(declared if declared.is_absolute() else authority_root / declared)
    ))
    try:
        relative = lexical.relative_to(authority_root)
    except ValueError:
        _fail(gate, f"{label} is outside the authority root")
    if not relative.parts:
        _fail(gate, f"{label} is not a regular file")

    cursor = authority_root
    try:
        for component in relative.parts:
            cursor = cursor / component
            metadata = cursor.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                _fail(gate, f"{label} traverses a symlink")
            if component != relative.parts[-1] and not stat.S_ISDIR(metadata.st_mode):
                _fail(gate, f"{label} traverses a non-directory component")
        if not stat.S_ISREG(metadata.st_mode):
            _fail(gate, f"{label} is not a regular file")
        resolved = lexical.resolve(strict=True)
        if resolved != lexical:
            _fail(gate, f"{label} traverses a symlink")
        resolved.relative_to(authority_root)
        raw = resolved.read_bytes()
    except AutonomousTrialCompletenessError:
        raise
    except (OSError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[{gate}] {label} cannot be read as an authority-root regular file"
        ) from exc
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        _fail(gate, f"{label} bytes differ from expected_sha256")
    return resolved, raw


def _canonical_descriptor_digest(
    value: Any, *, label: str,
) -> tuple[Mapping[str, Any], bytes, str]:
    descriptor = _mapping(value, gate="arm-digest-chain", label=label)
    raw = _canonical_bytes(descriptor)
    return descriptor, raw, hashlib.sha256(raw).hexdigest()


def _decode_canonical_object(
    raw: bytes, *, gate: str, label: str,
) -> Mapping[str, Any]:
    value = _decode_json(raw, label=label)
    mapped = _mapping(value, gate=gate, label=label)
    if _canonical_bytes(mapped) != raw:
        _fail(gate, f"{label} is not canonical JSON")
    return mapped


def _campaign_lock_identity(
    campaign_root: Path, *, gate: str,
) -> campaign_lock.DecodedCampaignLock:
    lock_path = campaign_root / "campaign.lock"
    try:
        metadata = lock_path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail(gate, "campaign.lock is not a regular non-symlink file")
        raw = lock_path.read_bytes()
        decoded = campaign_lock.decode_campaign_lock_bytes(raw)
    except AutonomousTrialCompletenessError:
        raise
    except (OSError, campaign_lock.CampaignLockCodecError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[{gate}] campaign.lock cannot be decoded"
        ) from exc
    if decoded.is_v1 or decoded.authority is None:
        _fail(gate, "campaign.lock v2 authority is required")
    return decoded


def _check_cell_campaign_identity(
    *, cell: Mapping[str, Any], cell_index: int, workload: str,
    entry: Mapping[str, Any], trial_id: str, budget: int,
    campaign_root: Path, arm_binding_digest: str | None,
) -> None:
    label = f"cells[{cell_index}]"
    descriptor, _descriptor_raw, content_digest = _canonical_descriptor_digest(
        cell.get("descriptor"), label=f"{label}.descriptor",
    )
    descriptor_binding = _mapping(
        cell.get("descriptor_binding"), gate="campaign-chain",
        label=f"{label}.descriptor_binding",
    )
    expected_binding_keys = (
        _EXPLORATORY_DESCRIPTOR_BINDING_KEYS
        if arm_binding_digest is None
        else _REGISTERED_DESCRIPTOR_BINDING_KEYS
    )
    if frozenset(descriptor_binding) != expected_binding_keys:
        _fail("campaign-chain", f"{label}.descriptor_binding exact keys differ")
    if descriptor_binding.get("output_sha256") != content_digest:
        _fail("campaign-chain", f"{label}.descriptor digest differs from binding")
    if descriptor_binding.get("projection_version") != "8b-descriptor-projection/v1":
        _fail("campaign-chain", f"{label}.descriptor projection version differs")
    if descriptor_binding.get("schema_sha256") != _DESCRIPTOR_SCHEMA_SHA256:
        _fail("campaign-chain", f"{label}.descriptor schema digest differs")
    if descriptor.get("schema_version") != "8b-v1":
        _fail("campaign-chain", f"{label}.descriptor schema differs")
    descriptor_scale = _mapping(
        descriptor.get("scale"), gate="campaign-chain",
        label=f"{label}.descriptor.scale",
    )
    perf_config_scale = _mapping(
        cell.get("perf_config_scale"), gate="campaign-chain",
        label=f"{label}.perf_config_scale",
    )
    if (
        frozenset(descriptor_scale) != frozenset({"records", "threads"})
        or frozenset(perf_config_scale) != frozenset({"records", "threads"})
    ):
        _fail("campaign-chain", f"{label} workload scale keys differ")
    if arm_binding_digest is not None and (
        descriptor_binding.get("input_sha256") != content_digest
        or descriptor_binding.get("content_digest_sha256") != content_digest
        or descriptor_binding.get("arm_binding_digest_sha256")
        != arm_binding_digest
    ):
        _fail("campaign-chain", f"{label}.registered descriptor binding differs")

    decoded = _campaign_lock_identity(campaign_root, gate="campaign-chain")
    identity = decoded.identity
    search_config = identity.get("search_config")
    if type(search_config) is not dict:
        _fail("campaign-chain", f"{label} search_config is not an exact object")
    expected_search_keys = _AUTONOMOUS_SEARCH_CONFIG_KEYS | (
        {"arm_binding_digest_sha256"}
        if arm_binding_digest is not None else set()
    )
    admitted_search_key_sets = {
        frozenset(expected_search_keys),
        frozenset(expected_search_keys | {"measurement_env"}),
    }
    if frozenset(search_config) not in admitted_search_key_sets:
        _fail("campaign-chain", f"{label} search_config exact keys differ")
    if "measurement_env" in search_config and (
        search_config["measurement_env"] != "pegasus"
    ):
        _fail("campaign-chain", f"{label} search_config.measurement_env differs")
    expected_search_values = {
        "axis": "silo-backoff-trigger-gating",
        "descriptor_schema": descriptor.get("schema_version"),
        "descriptor_sha256": content_digest,
        "generation_budget": budget,
        "pilot_scope": "exploratory-ycsb-abc",
        "reflux": "on",
        "scale": "silo",
        "stop_policy": "fixed-generations-no-performance-early-stop",
        "trigger_gate_binding_schema": "izanagi-trigger-gate-binding/v1",
        "verify": "legacy+s2",
        "workload": workload,
        "ycsb": dict(entry.get("ycsb", {})),
    }
    for field, expected in expected_search_values.items():
        if search_config.get(field) != expected:
            _fail("campaign-chain", f"{label} search_config.{field} differs")
    expected_scale = {
        "records": entry.get("records"),
        "threads": entry.get("threads"),
    }
    campaign_scale = {
        "records": search_config.get("records"),
        "threads": search_config.get("threads"),
    }
    if not (
        dict(descriptor_scale)
        == dict(perf_config_scale)
        == campaign_scale
        == expected_scale
    ):
        _fail("campaign-chain", f"{label} workload scale differs from producer")
    if not isinstance(search_config.get("build_admission"), Mapping):
        _fail("campaign-chain", f"{label} search_config.build_admission is absent")
    if arm_binding_digest is not None and (
        search_config.get("arm_binding_digest_sha256") != arm_binding_digest
    ):
        _fail("campaign-chain", f"{label} campaign arm digest differs")
    if (
        identity.get("spec_content") != _AUTONOMOUS_SPEC_CONTENT
        or identity.get("search_tag") != "workload-conditioned-autonomous"
        or identity.get("trial") != f"{trial_id}-{workload}"
        or identity.get("ccbench_commit") != _CURRENT_CCBENCH_PIN
    ):
        _fail("campaign-chain", f"{label} campaign_id differs from producer derivation")
    expected_campaign_id = (
        f"p3-t178-{workload}-workload-conditioned-autonomous-"
        f"{hashlib.sha256(decoded.identity_preimage.encode('utf-8')).hexdigest()[:8]}"
    )
    if cell.get("campaign_id") != expected_campaign_id:
        _fail("campaign-chain", f"{label} campaign_id differs from producer derivation")


def _check_registered_proposal(
    *, proposal: Any, run_root: Path, workload: str, generation: int,
    arm: str, content_digest: str, arm_binding_digest: str,
) -> None:
    record = _mapping(
        proposal, gate="arm-digest-chain", label="generation.proposal",
    )
    if frozenset(record) != _REGISTERED_PROPOSAL_KEYS:
        _fail("arm-digest-chain", "proposal record exact keys differ")
    path, raw = _bound_regular_bytes(
        record.get("path"), run_root=run_root, gate="arm-digest-chain",
        label="proposal.path",
    )
    expected_name = (
        f"arm-{arm}.exec-{arm_binding_digest}.{workload}.g{generation}.json"
    )
    if path.parent != run_root / "proposals" or path.name != expected_name:
        _fail("arm-digest-chain", "proposal path differs from the bound generation")
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if (
        record.get("sha256") != actual_sha256
        or record.get("digest") != arm_binding_digest
    ):
        _fail("arm-digest-chain", "proposal digest differs")
    value = _decode_canonical_object(
        raw, gate="arm-digest-chain", label="proposal bytes",
    )
    if frozenset(value) != _REGISTERED_PROPOSAL_VALUE_KEYS:
        _fail("arm-digest-chain", "proposal bytes exact keys differ")
    if (
        value.get("descriptor_sha256") != content_digest
        or value.get("arm_binding_digest_sha256") != arm_binding_digest
    ):
        _fail("arm-digest-chain", "proposal bytes digest differs")


def _check_registered_provider_artifacts(
    *, event: Mapping[str, Any], run_root: Path, content_digest: str,
    arm_binding_digest: str, arm: str,
) -> None:
    artifacts = _mapping(
        event.get("provider_artifacts"), gate="arm-digest-chain",
        label="role-attempt.provider_artifacts",
    )
    if frozenset(artifacts) != _PROVIDER_ARTIFACT_KEYS:
        _fail("arm-digest-chain", "provider_artifacts exact keys differ")
    if artifacts.get("arm_binding_digest_sha256") != arm_binding_digest:
        _fail("arm-digest-chain", "provider artifact arm digest differs")
    payload_path, payload_raw = _bound_regular_bytes(
        artifacts.get("payload_path"), run_root=run_root,
        gate="arm-digest-chain", label="provider payload path",
    )
    envelope_path, envelope_raw = _bound_regular_bytes(
        artifacts.get("envelope_path"), run_root=run_root,
        gate="arm-digest-chain", label="provider envelope path",
    )
    invocation_id = event.get("invocation_id")
    provider_invocation_id = invocation_id
    if arm == "off":
        provider = _producer_module()
        provider_invocation_id = (
            f"arm-off.exec-{content_digest}."
            f"{provider.OFF_NEUTRAL_PAYLOAD_WORKLOAD}.g"
            f"{event.get('generation')}.{event.get('role')}"
        )
    if (
        payload_path.name != f"payload_{provider_invocation_id}.json"
        or envelope_path.name != f"envelope_{provider_invocation_id}.json"
        or payload_path.parent != envelope_path.parent
    ):
        _fail("arm-digest-chain", "provider artifact path differs from invocation")
    payload_sha256 = hashlib.sha256(payload_raw).hexdigest()
    envelope_sha256 = hashlib.sha256(envelope_raw).hexdigest()
    if (
        event.get("provider_payload_sha256") != payload_sha256
        or event.get("provider_envelope_sha256") != envelope_sha256
        or event.get("input_payload_sha256") != payload_sha256
    ):
        _fail("arm-digest-chain", "provider payload/envelope digest differs")
    payload = _decode_canonical_object(
        payload_raw, gate="arm-digest-chain", label="provider payload bytes",
    )
    _payload_descriptor, _payload_descriptor_raw, payload_descriptor_digest = (
        _canonical_descriptor_digest(
            payload.get("workload_descriptor"),
            label="provider payload workload_descriptor",
        )
    )
    if payload_descriptor_digest != content_digest:
        _fail(
            "arm-digest-chain",
            "provider payload workload descriptor digest differs",
        )
    payload_binding = _mapping(
        payload.get("descriptor_binding"), gate="arm-digest-chain",
        label="provider payload descriptor_binding",
    )
    if arm == "off":
        expected_binding_keys = _REGISTERED_DESCRIPTOR_BINDING_KEYS - {
            "arm_binding_digest_sha256",
        }
        if frozenset(payload_binding) != expected_binding_keys:
            _fail("arm-digest-chain", "off provider payload descriptor binding keys differ")
        if (
            "arm_binding_digest_sha256" in payload_binding
            or payload_binding["input_sha256"] != content_digest
            or payload_binding["output_sha256"] != content_digest
            or payload_binding["content_digest_sha256"] != content_digest
            or payload.get("workload")
            != _producer_module().OFF_NEUTRAL_PAYLOAD_WORKLOAD
        ):
            _fail("arm-digest-chain", "off provider payload projection differs")
    elif (
        payload_binding.get("output_sha256") != content_digest
        or payload_binding.get("content_digest_sha256") != content_digest
        or payload_binding.get("arm_binding_digest_sha256")
        != arm_binding_digest
    ):
        _fail("arm-digest-chain", "provider payload digest differs")
    _mapping(
        _decode_json(envelope_raw, label="provider envelope bytes"),
        gate="arm-digest-chain", label="provider envelope bytes",
    )
    provenance = event.get("provenance")
    if isinstance(provenance, Mapping) and (
        provenance.get("payload_sha256") != payload_sha256
        or provenance.get("envelope_sha256") != envelope_sha256
    ):
        _fail("arm-digest-chain", "provider provenance digest differs")


def _check_arm_digest_chain(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
    cells: Sequence[Mapping[str, Any]], run_root: Path,
) -> None:
    # ``trial_registry`` imports this module, so the registry authority must be
    # acquired lazily after both modules have finished initializing.  Registry
    # membership remains independent of the producer's exploratory table; the
    # entry itself is obtained through the producer's shared resolver below.
    from .trial_registry import HOLDOUT_BINDINGS, HOLDOUT_WORKLOADS

    launch = _mapping(
        report.get("launch_admission"), gate="arm-digest-chain",
        label="report.launch_admission",
    )
    launch_binding = launch.get("binding")
    launch_workload = (
        launch_binding.get("workload")
        if isinstance(launch_binding, Mapping)
        else None
    )
    launch_mode = launch.get("mode")
    requires_arm_digest_chain = (
        type(launch_mode) is str
        and launch_mode in _REGISTERED_LAUNCH_MODES
        and type(launch_workload) is str
        and launch_workload in HOLDOUT_WORKLOADS
    )
    starts = [event for event in events if event.get("event") == "run-start"]
    if len(starts) != 1:
        _fail("arm-digest-chain", "run-start is not unique")
    start = starts[0]
    if not requires_arm_digest_chain:
        if "arm_execution" in report or "arm_execution" in start:
            _fail("arm-digest-chain", "exploratory run carries arm_execution")
        return

    report_arm = _mapping(
        report.get("arm_execution"), gate="arm-digest-chain",
        label="report.arm_execution",
    )
    start_arm = _mapping(
        start.get("arm_execution"), gate="arm-digest-chain",
        label="run-start.arm_execution",
    )
    if frozenset(report_arm) != _ARM_EXECUTION_KEYS:
        _fail("arm-digest-chain", "report.arm_execution exact keys differ")
    if dict(start_arm) != dict(report_arm):
        _fail("arm-digest-chain", "run-start/report arm_execution differs")
    for field in ("content_digest_sha256", "arm_binding_digest_sha256"):
        value = report_arm.get(field)
        if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
            _fail("arm-digest-chain", f"arm_execution.{field} is invalid")
    if report_arm.get("input_schema_version") != "8b-v1":
        _fail("arm-digest-chain", "arm_execution input schema differs")
    content_digest = report_arm["content_digest_sha256"]
    arm_binding_digest = report_arm["arm_binding_digest_sha256"]
    binding = _mapping(
        launch.get("binding"), gate="arm-digest-chain",
        label="launch_admission.binding",
    )
    arm = binding.get("arm")
    holdout = binding.get("holdout")
    if arm not in {"on", "off", "swapped"} or type(holdout) is not str:
        _fail("arm-digest-chain", "launch arm/holdout is outside the closed set")
    if _arm_binding_digest(
        holdout=holdout, arm=arm, content_digest=content_digest,
    ) != arm_binding_digest:
        _fail("arm-digest-chain", "arm binding digest differs")
    projection = report.get("origin_terminal_projection")
    if projection is not None:
        projection = _mapping(
            projection, gate="arm-digest-chain",
            label="origin_terminal_projection",
        )
        if (
            frozenset(projection)
            != (
                _ORIGIN_TERMINAL_PROJECTION_BASE_KEYS
                | {"arm_binding_digest_sha256"}
            )
            or projection.get("arm_binding_digest_sha256")
            != arm_binding_digest
        ):
            _fail("arm-digest-chain", "origin terminal arm digest differs")

    workload = binding.get("workload")
    registered_holdout = HOLDOUT_BINDINGS.get(holdout)
    if (
        type(workload) is not str
        or workload not in HOLDOUT_WORKLOADS
        or not isinstance(registered_holdout, Mapping)
        or registered_holdout.get("workload") != workload
        or binding.get("ycsb_rratio")
        != registered_holdout.get("ycsb_rratio")
        or launch.get("workloads") != [workload]
    ):
        _fail("arm-digest-chain", "registered workload is inconsistent")
    matching_cells = [cell for cell in cells if cell.get("workload") == workload]
    if cells and len(matching_cells) != 1:
        _fail("arm-digest-chain", "registered workload cell is not unique")
    if not matching_cells:
        return
    cell = matching_cells[0]
    cell_index = cells.index(cell)
    if is_exact_cell_admission_failure_decision(
        cell.get("admission_decision")
    ):
        if not is_exact_campaignless_failure_fallback_cell(cell):
            _fail("arm-digest-chain", "cell admission failure projection is not exact")
        return
    workload_flags = _mapping(
        cell.get("workload_flags"), gate="arm-digest-chain",
        label=f"cells[{cell_index}].workload_flags",
    )
    for field in ("ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw"):
        if workload_flags.get(field) != registered_holdout.get(field):
            _fail(
                "arm-digest-chain",
                f"benchmark workload_flags.{field} differs from registered holdout",
            )
    perf_config_scale = _mapping(
        cell.get("perf_config_scale"), gate="arm-digest-chain",
        label=f"cells[{cell_index}].perf_config_scale",
    )
    for field in ("records", "threads"):
        if perf_config_scale.get(field) != registered_holdout.get(field):
            _fail(
                "arm-digest-chain",
                f"benchmark perf_config_scale.{field} differs from registered holdout",
            )
    descriptor, _raw, actual_content_digest = _canonical_descriptor_digest(
        cell.get("descriptor"), label=f"cells[{cell_index}].descriptor",
    )
    if actual_content_digest != content_digest:
        _fail("arm-digest-chain", "cell descriptor content digest differs")
    descriptor_scale = _mapping(
        descriptor.get("scale"), gate="arm-digest-chain",
        label=f"cells[{cell_index}].descriptor.scale",
    )
    expected_scale_keys = frozenset({"records", "threads"})
    if (
        frozenset(perf_config_scale) != expected_scale_keys
        or frozenset(descriptor_scale) != expected_scale_keys
    ):
        _fail("arm-digest-chain", "benchmark cell/descriptor scale keys differ")
    for field in ("records", "threads"):
        if perf_config_scale.get(field) != descriptor_scale.get(field):
            _fail(
                "arm-digest-chain",
                f"benchmark perf_config_scale.{field} differs from cell descriptor",
            )
    producer = _producer_module()
    try:
        entry = producer.resolve_workload_entry(workload)
    except producer.AutonomousTrialError:
        _fail("arm-digest-chain", "registered workload has no producer entry")
    if dict(entry.get("ycsb", {})) != dict(workload_flags):
        _fail("arm-digest-chain", "benchmark workload_flags differs from producer")
    descriptor_binding = _mapping(
        cell.get("descriptor_binding"), gate="arm-digest-chain",
        label=f"cells[{cell_index}].descriptor_binding",
    )
    if (
        frozenset(descriptor_binding) != _REGISTERED_DESCRIPTOR_BINDING_KEYS
        or descriptor_binding.get("input_sha256") != content_digest
        or descriptor_binding.get("output_sha256") != content_digest
        or descriptor_binding.get("schema_sha256") != _DESCRIPTOR_SCHEMA_SHA256
        or descriptor_binding.get("content_digest_sha256") != content_digest
        or descriptor_binding.get("arm_binding_digest_sha256")
        != arm_binding_digest
    ):
        _fail("arm-digest-chain", "descriptor binding digest differs")
    campaign_id = cell.get("campaign_id")
    campaign_root = _path_identity(
        cell.get("campaign_root"), gate="arm-digest-chain",
        label=f"cells[{cell_index}].campaign_root",
    )
    artifact_run_root = Path(run_root).resolve(strict=True)
    if report.get("do_build") is False:
        expected_root = artifact_run_root / "campaigns" / str(campaign_id)
        campaign_path_matches = campaign_root == expected_root
    else:
        campaign_path_matches = (
            campaign_root.name == str(campaign_id)
            and campaign_root.parent.name == "campaigns"
        )
    if not campaign_path_matches:
        _fail("arm-digest-chain", "campaign identity/path differs")
    if binding.get("campaign_id") != campaign_id:
        _fail("arm-digest-chain", "launch binding campaign_id differs")
    lock_path = campaign_root / "campaign.lock"
    if report.get("do_build") is True or lock_path.exists() or lock_path.is_symlink():
        _check_cell_campaign_identity(
            cell=cell, cell_index=cell_index, workload=workload,
            entry=entry, trial_id=report.get("trial_id"),
            budget=report.get("generation_budget_per_workload"),
            campaign_root=campaign_root,
            arm_binding_digest=arm_binding_digest,
        )

    for event in events:
        if event.get("event") != "role-attempt":
            continue
        role = event.get("role")
        generation = event.get("generation")
        expected_invocation = (
            f"arm-{arm}.exec-{arm_binding_digest}.{workload}."
            f"g{generation}.{role}"
        )
        if (
            event.get("workload") != workload
            or event.get("invocation_id") != expected_invocation
            or event.get("arm_binding_digest_sha256") != arm_binding_digest
            or event.get("descriptor_sha256") != content_digest
        ):
            _fail("arm-digest-chain", "journal invocation digest differs")

    for generation_record in _list(
        cell.get("generations"), gate="arm-digest-chain",
        label=f"cells[{cell_index}].generations",
    ):
        generation_record = _mapping(
            generation_record, gate="arm-digest-chain", label="generation",
        )
        generation = generation_record.get("generation")
        roles = _mapping(
            generation_record.get("roles"), gate="arm-digest-chain",
            label="generation.roles",
        )
        for role, event in roles.items():
            event = _mapping(
                event, gate="arm-digest-chain", label=f"generation.roles.{role}",
            )
            expected_invocation = (
                f"arm-{arm}.exec-{arm_binding_digest}.{workload}."
                f"g{generation}.{role}"
            )
            if (
                event.get("invocation_id") != expected_invocation
                or event.get("arm_binding_digest_sha256")
                != arm_binding_digest
                or event.get("descriptor_sha256") != content_digest
            ):
                _fail("arm-digest-chain", "role invocation digest differs")
            if (
                report.get("provider") == "claude-headless"
                and event.get("status") != "skipped"
            ):
                _check_registered_provider_artifacts(
                    event=event, run_root=artifact_run_root,
                    content_digest=content_digest,
                    arm_binding_digest=arm_binding_digest,
                    arm=arm,
                )
        auditor = roles.get("auditor")
        proposal_reached = isinstance(auditor, Mapping) and (
            auditor.get("status") != "invalid"
        )
        if proposal_reached or "proposal" in generation_record:
            _check_registered_proposal(
                proposal=generation_record.get("proposal"),
                run_root=artifact_run_root,
                workload=workload, generation=generation, arm=arm,
                content_digest=content_digest,
                arm_binding_digest=arm_binding_digest,
            )


def assert_execution_digest_chain(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
    run_root: Path,
) -> None:
    """Verify the arm execution digest chain independently of completeness."""
    report = _mapping(report, gate="report-shape", label="report")
    normalized_events = [
        _mapping(event, gate="arm-digest-chain", label=f"events[{index}]")
        for index, event in enumerate(events)
    ]
    raw_cells = _list(
        report.get("cells"), gate="report-shape", label="report.cells",
    )
    cells = [
        _mapping(cell, gate="report-shape", label=f"cells[{index}]")
        for index, cell in enumerate(raw_cells)
    ]
    _check_arm_digest_chain(
        report=report, events=normalized_events, cells=cells,
        run_root=Path(run_root),
    )


def assert_autonomous_trial_execution_digest_chain(
    *, report: Mapping[str, Any], attempt_journal: Path,
) -> None:
    """Re-read a persisted journal and verify its execution digest chain."""
    _journal_bytes, events = _read_journal(Path(attempt_journal))
    assert_execution_digest_chain(
        report=report,
        events=events,
        run_root=Path(attempt_journal).resolve().parent,
    )


def _sha256_field(value: Any, *, label: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("role-event-shape", f"{label} is not a lowercase SHA-256")


def _expected_payload_keys(record: Mapping[str, Any]) -> list[str]:
    role = record.get("role")
    if role == "planner":
        generation = record.get("generation")
        key = (
            "planner-generation-1"
            if generation == 1
            else "planner-generation-next"
        )
    elif role == "auditor" and record.get("status") == "skipped":
        key = "auditor-skip"
    else:
        key = role
    if key not in _ROLE_PAYLOAD_KEY_SPEC:
        _fail("payload-allowlist", f"unknown role payload key spec: {key!r}")
    return _ROLE_PAYLOAD_KEY_SPEC[key]


def _receipt_sha256(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        _fail("payload-validation-receipt", f"receipt is not canonical JSON: {exc}")
    return hashlib.sha256(encoded).hexdigest()


def _off_payload_descriptor_binding_sha256(content_digest: str) -> str:
    return _receipt_sha256({
        "input_sha256": content_digest,
        "output_sha256": content_digest,
        "projection_version": "8b-descriptor-projection/v1",
        "schema_sha256": _DESCRIPTOR_SCHEMA_SHA256,
        "content_digest_sha256": content_digest,
    })


def _receipt_sha256_field(value: Any, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail("payload-validation-receipt", f"{label} is not a lowercase SHA-256")
    return value


def _check_bool_map(value: Any, expected_keys: set[str], *, label: str) -> None:
    mapping = _mapping(value, gate="payload-validation-receipt", label=label)
    if set(mapping) != expected_keys or any(type(item) is not bool for item in mapping.values()):
        _fail("payload-validation-receipt", f"{label} is not the exact nullness map")


def _check_whiteboard_receipt(
    value: Any, *, generation: int, label: str,
) -> None:
    entries = _list(value, gate="payload-validation-receipt", label=label)
    if len(entries) > generation - 1:
        _fail("payload-validation-receipt", f"{label} exceeds generation bound")
    previous = 0
    for index, raw in enumerate(entries):
        entry = _mapping(
            raw,
            gate="payload-validation-receipt",
            label=f"{label}[{index}]",
        )
        if set(entry) != _WHITEBOARD_KEYS:
            _fail("payload-validation-receipt", f"{label}[{index}] keys differ")
        iteration = entry.get("iteration")
        if type(iteration) is not int or not previous < iteration <= generation - 1:
            _fail("payload-validation-receipt", f"{label} is not strictly increasing")
        previous = iteration
        if entry.get("direction") not in {"increase", "decrease", "explore_both"}:
            _fail("payload-validation-receipt", f"{label} direction is outside allowlist")
        if entry.get("magnitude") not in {"small", "medium", "large"}:
            _fail("payload-validation-receipt", f"{label} magnitude is outside allowlist")
        if entry.get("result") not in {"success", "fail", "rejected"}:
            _fail("payload-validation-receipt", f"{label} result is outside allowlist")
        if entry.get("delta_pct") is not None:
            _fail("payload-validation-receipt", f"{label} delta_pct is not null")


def _check_payload_validation_receipt(
    record: Mapping[str, Any], *, label: str, arm: str | None = None,
    content_digest: str | None = None,
) -> None:
    role = record.get("role")
    raw_receipt = record.get("payload_validation_receipt")
    if not isinstance(raw_receipt, Mapping):
        _fail(
            "payload-validation-receipt",
            f"{label}.payload_validation_receipt is not a Mapping",
        )
    receipt = _mapping(
        raw_receipt,
        gate="payload-validation-receipt",
        label=f"{label}.payload_validation_receipt",
    )
    receipt_keys = {
        "schema_version", "role", "payload_sha256", "payload_allowlist_sha256",
        "safe_projection", "safe_projection_sha256", "seal_sha256",
    }
    if set(receipt) != receipt_keys:
        _fail("payload-validation-receipt", f"{label} receipt keys differ")
    if receipt.get("schema_version") != _VALIDATION_RECEIPT_SCHEMA_VERSION:
        _fail("payload-validation-receipt", f"{label} receipt schema differs")
    if receipt.get("role") != role:
        _fail("payload-validation-receipt", f"{label} receipt role differs")
    if receipt.get("payload_sha256") != record.get("input_payload_sha256"):
        _fail("payload-validation-receipt", f"{label} receipt payload digest differs")
    if receipt.get("payload_allowlist_sha256") != _ROLE_PAYLOAD_ALLOWLIST_SHA256:
        _fail("payload-validation-receipt", f"{label} receipt allowlist digest differs")

    projection = _mapping(
        receipt.get("safe_projection"),
        gate="payload-validation-receipt",
        label=f"{label}.safe_projection",
    )
    common_projection_keys = {
        "role", "workload", "generation", "descriptor_sha256",
        "workload_descriptor_sha256", "descriptor_binding_sha256",
        "fixed_literals", "nested_key_sets", "whiteboard_origin",
        "whiteboard_origin_sha256",
    }
    role_projection_keys = (
        {
            "current_perf_nullness", "leading_metric_nullness",
            "contention_level_sha256", "critic_feedback",
        }
        if role == "planner"
        else {
            "baseline_nullness", "gating_spec_sha256",
            "planner_direction_sha256",
        }
    )
    if set(projection) != common_projection_keys | role_projection_keys:
        _fail("payload-validation-receipt", f"{label} safe projection keys differ")
    generation = record.get("generation")
    if type(generation) is not int or generation < 1:
        _fail("payload-validation-receipt", f"{label} generation is invalid")
    expected_projection_workload = record.get("workload")
    if arm == "off":
        expected_projection_workload = _producer_module().OFF_NEUTRAL_PAYLOAD_WORKLOAD
    if (
        projection.get("role") != role
        or projection.get("workload") != expected_projection_workload
        or projection.get("generation") != generation
        or projection.get("descriptor_sha256") != record.get("descriptor_sha256")
    ):
        _fail("payload-validation-receipt", f"{label} safe identity differs")
    for field in (
        "workload_descriptor_sha256", "descriptor_binding_sha256",
        "whiteboard_origin_sha256",
    ):
        _receipt_sha256_field(projection.get(field), label=f"{label}.{field}")
    if (
        projection.get("workload_descriptor_sha256")
        != record.get("descriptor_sha256")
    ):
        _fail(
            "payload-validation-receipt",
            f"{label} workload descriptor digest differs",
        )
    if arm == "off":
        if (
            type(content_digest) is not str
            or _SHA256_RE.fullmatch(content_digest) is None
            or record.get("descriptor_sha256") != content_digest
            or projection.get("descriptor_binding_sha256")
            != _off_payload_descriptor_binding_sha256(content_digest)
        ):
            _fail(
                "payload-validation-receipt",
                f"{label} off descriptor binding projection differs",
            )

    fixed = _mapping(
        projection.get("fixed_literals"),
        gate="payload-validation-receipt",
        label=f"{label}.fixed_literals",
    )
    expected_fixed = {
        "schema_version": _ROLE_SCHEMA_VERSION,
        "pilot_scope": _PILOT_SCOPE,
        "scientific_claim": False,
        "attempt_policy": dict(s8c_generation_projection.ATTEMPT_POLICY),
        "stop_policy": {
            "performance_early_stop": False,
            "generation_budget_is_fixed": True,
        },
    }
    if role == "coder":
        expected_fixed.update({
            "leakproof_context": _LEAKPROOF_CONTEXT,
            "planner_axis": _PLANNER_AXIS,
        })
    if fixed != expected_fixed:
        _fail("payload-validation-receipt", f"{label} fixed literals differ")

    nested = _mapping(
        projection.get("nested_key_sets"),
        gate="payload-validation-receipt",
        label=f"{label}.nested_key_sets",
    )
    if nested.get("$") != record.get("payload_exact_keys"):
        _fail("payload-validation-receipt", f"{label} top-level receipt keys differ")
    required_nested = {
        "$.attempt_policy": ["attempts_per_role_generation", "retry"],
        "$.stop_policy": ["generation_budget_is_fixed", "performance_early_stop"],
    }
    if role == "planner":
        required_nested.update({
            "$.current_perf": sorted(_PERF_KEYS),
            "$.leading_indicators": [
                "IPC_overall", "cache_miss_rate_pct", "contention_level",
            ],
        })
    else:
        required_nested.update({
            "$.baseline": sorted(_PERF_KEYS),
            "$.planner_direction": ["axis", "direction", "magnitude"],
        })
    for path, keys in required_nested.items():
        if nested.get(path) != keys:
            _fail("payload-validation-receipt", f"{label} nested keys differ at {path}")

    _check_whiteboard_receipt(
        projection.get("whiteboard_origin"),
        generation=generation,
        label=f"{label}.whiteboard_origin",
    )
    if _receipt_sha256(projection["whiteboard_origin"]) != projection["whiteboard_origin_sha256"]:
        _fail("payload-validation-receipt", f"{label} whiteboard origin digest differs")

    if role == "planner":
        _check_bool_map(
            projection.get("current_perf_nullness"),
            _PERF_KEYS,
            label=f"{label}.current_perf_nullness",
        )
        _check_bool_map(
            projection.get("leading_metric_nullness"),
            _LEADING_METRIC_KEYS,
            label=f"{label}.leading_metric_nullness",
        )
        _receipt_sha256_field(
            projection.get("contention_level_sha256"),
            label=f"{label}.contention_level_sha256",
        )
        feedback = projection.get("critic_feedback")
        if generation == 1:
            if feedback is not None:
                _fail("payload-validation-receipt", f"{label} generation 1 has feedback")
        else:
            feedback_map = _mapping(
                feedback,
                gate="payload-validation-receipt",
                label=f"{label}.critic_feedback",
            )
            if set(feedback_map) != {
                "source_generation", "diagnostics", "uncertainty_present",
                "reverse_recommended",
            } or feedback_map.get("source_generation") != generation - 1:
                _fail("payload-validation-receipt", f"{label} critic identity differs")
            if type(feedback_map.get("uncertainty_present")) is not bool or type(
                feedback_map.get("reverse_recommended")
            ) is not bool:
                _fail("payload-validation-receipt", f"{label} critic bool differs")
            diagnostics = _list(
                feedback_map.get("diagnostics"),
                gate="payload-validation-receipt",
                label=f"{label}.critic_feedback.diagnostics",
            )
            if len(diagnostics) != len(_DIAGNOSTIC_METRICS):
                _fail("payload-validation-receipt", f"{label} diagnostic length differs")
            for index, metric in enumerate(_DIAGNOSTIC_METRICS):
                diagnostic = _mapping(
                    diagnostics[index],
                    gate="payload-validation-receipt",
                    label=f"{label}.diagnostics[{index}]",
                )
                if set(diagnostic) != {"metric", "value_is_null", "value_sha256"}:
                    _fail("payload-validation-receipt", f"{label} diagnostic keys differ")
                if diagnostic.get("metric") != metric or type(
                    diagnostic.get("value_is_null")
                ) is not bool:
                    _fail("payload-validation-receipt", f"{label} diagnostic value differs")
                _receipt_sha256_field(
                    diagnostic.get("value_sha256"),
                    label=f"{label}.diagnostics[{index}].value_sha256",
                )
    else:
        _check_bool_map(
            projection.get("baseline_nullness"),
            _PERF_KEYS,
            label=f"{label}.baseline_nullness",
        )
        for field in ("gating_spec_sha256", "planner_direction_sha256"):
            _receipt_sha256_field(projection.get(field), label=f"{label}.{field}")

    projection_sha256 = _receipt_sha256(projection)
    if receipt.get("safe_projection_sha256") != projection_sha256:
        _fail("payload-validation-receipt", f"{label} safe projection digest differs")
    seal_preimage = {
        "schema_version": _VALIDATION_RECEIPT_SCHEMA_VERSION,
        "role": role,
        "payload_sha256": receipt["payload_sha256"],
        "payload_allowlist_sha256": receipt["payload_allowlist_sha256"],
        "safe_projection_sha256": projection_sha256,
    }
    if receipt.get("seal_sha256") != _receipt_sha256(seal_preimage):
        _fail("payload-validation-receipt", f"{label} receipt seal differs")


def _check_payload_validation_receipts(
    records: Sequence[Mapping[str, Any]], *, arm: str | None = None,
    content_digest: str | None = None,
) -> None:
    for record in records:
        label = (
            f"{record.get('workload')}.g{record.get('generation')}."
            f"{record.get('role')}"
        )
        if record.get("role") in {"planner", "coder"}:
            _check_payload_validation_receipt(
                record,
                label=label,
                arm=arm,
                content_digest=content_digest,
            )
        elif "payload_validation_receipt" in record:
            _fail(
                "payload-validation-receipt",
                f"{label} non-validated role carries a receipt",
            )


def _check_role_event_shape(
    record: Mapping[str, Any], *, label: str, run_root: Path,
) -> None:
    required = {
        "event", "workload", "generation", "role", "status", "seq", "ts",
        "invocation_id", "input_payload_sha256", "descriptor_sha256",
        "attempt", "retry",
        "payload_exact_keys", "payload_allowlist_sha256",
        "role_query_ordinal",
    }
    missing = sorted(required - set(record))
    if missing:
        _fail("role-event-shape", f"{label} is missing required fields: {missing}")
    if record.get("event") != "role-attempt":
        _fail("role-event-shape", f"{label}.event is not 'role-attempt'")
    if type(record.get("seq")) is not int or record["seq"] < 1:
        _fail("role-event-shape", f"{label}.seq is not a positive int")
    if not isinstance(record.get("ts"), str) or not record["ts"]:
        _fail("role-event-shape", f"{label}.ts is not a non-empty string")
    _sha256_field(record.get("input_payload_sha256"), label=f"{label}.input_payload_sha256")
    _sha256_field(record.get("descriptor_sha256"), label=f"{label}.descriptor_sha256")
    if record.get("attempt") != 1 or type(record.get("attempt")) is not int:
        _fail("attempt-policy", f"{label}.attempt must be exactly 1")
    if record.get("retry") is not False:
        _fail("attempt-policy", f"{label}.retry must be false")
    if record.get("payload_allowlist_sha256") != _ROLE_PAYLOAD_ALLOWLIST_SHA256:
        _fail("payload-allowlist", f"{label} allowlist digest differs")
    exact_keys = record.get("payload_exact_keys")
    if exact_keys != _expected_payload_keys(record):
        _fail("payload-allowlist", f"{label} exact payload keys differ")
    status = record.get("status")
    if status == "valid":
        status_required = {
            "parsed", "provenance", "raw_response_path", "raw_response_sha256",
        }
        missing = sorted(status_required - set(record))
        if missing:
            _fail("role-event-shape", f"{label} valid event is missing fields: {missing}")
        _mapping(record["parsed"], gate="role-event-shape", label=f"{label}.parsed")
        _mapping(
            record["provenance"], gate="role-event-shape", label=f"{label}.provenance",
        )
        if not record["provenance"]:
            _fail("role-event-shape", f"{label}.provenance is empty")
        if not isinstance(record["raw_response_path"], str) or not record["raw_response_path"]:
            _fail("role-event-shape", f"{label}.raw_response_path is not a non-empty string")
        _sha256_field(record["raw_response_sha256"], label=f"{label}.raw_response_sha256")
    elif status == "invalid":
        status_required = {"error_type", "error", "error_artifacts"}
        missing = sorted(status_required - set(record))
        if missing:
            _fail("role-event-shape", f"{label} invalid event is missing fields: {missing}")
        if not isinstance(record["error_type"], str) or not record["error_type"]:
            _fail("role-event-shape", f"{label}.error_type is not a non-empty string")
        if not isinstance(record["error"], str):
            _fail("role-event-shape", f"{label}.error is not a string")
        error_artifacts = _mapping(
            record["error_artifacts"], gate="role-event-shape",
            label=f"{label}.error_artifacts",
        )
        failure_phase = error_artifacts.get("failure_phase")
        if (
            type(failure_phase) is not str
            or failure_phase not in _ROLE_FAILURE_PHASES
        ):
            _fail(
                "role-event-shape",
                f"{label}.error_artifacts.failure_phase is invalid",
            )
        raw_keys = {"raw_response_path", "raw_response_sha256"}
        present_raw_keys = raw_keys & set(error_artifacts)
        if present_raw_keys and present_raw_keys != raw_keys:
            _fail(
                "role-event-shape",
                f"{label}.error_artifacts raw response pointer is incomplete",
            )
        if (
            failure_phase in _ROLE_FAILURE_PHASES_AFTER_RAW_WRITE
            and present_raw_keys != raw_keys
        ):
            _fail(
                "role-event-shape",
                f"{label}.error_artifacts raw response pointer is required",
            )
        expected_raw_path = (
            Path(run_root)
            / "raw"
            / f"raw_{record.get('invocation_id')}.txt"
        )
        try:
            expected_raw_exists = (
                expected_raw_path.exists() or expected_raw_path.is_symlink()
            )
        except OSError as exc:
            raise AutonomousTrialCompletenessError(
                "[role-event-shape] "
                f"{label} expected raw response path cannot be inspected"
            ) from exc
        if (
            expected_raw_exists
            and failure_phase not in _ROLE_FAILURE_PHASES_AFTER_RAW_WRITE
        ):
            _fail(
                "role-event-shape",
                f"{label}.error_artifacts.failure_phase contradicts an existing raw response",
            )
        if present_raw_keys == raw_keys:
            raw_path_value = error_artifacts["raw_response_path"]
            raw_sha256 = error_artifacts["raw_response_sha256"]
            if type(raw_path_value) is not str or not raw_path_value:
                _fail(
                    "role-event-shape",
                    f"{label}.error_artifacts.raw_response_path is not a non-empty string",
                )
            _sha256_field(
                raw_sha256,
                label=f"{label}.error_artifacts.raw_response_sha256",
            )
            if raw_path_value != str(expected_raw_path):
                _fail(
                    "role-event-shape",
                    f"{label}.error_artifacts.raw_response_path differs from the invocation raw path",
                )
            _raw_path, raw_bytes = _read_bound_role_raw_bytes(
                raw_path_value,
                run_root=Path(run_root),
                gate="role-event-shape",
                label=f"{label}.error_artifacts.raw_response_path",
            )
            if hashlib.sha256(raw_bytes).hexdigest() != raw_sha256:
                _fail(
                    "role-event-shape",
                    f"{label}.error_artifacts raw response bytes differ from sha256",
                )
    elif status == "skipped":
        if record.get("role") != "auditor":
            _fail("role-event-shape", f"{label} non-auditor role cannot be skipped")
        if record.get("skip_reason") != "machine-pre-audit-rejection":
            _fail("role-event-shape", f"{label}.skip_reason is invalid")
        evidence = _mapping(
            record.get("pre_audit"), gate="role-event-shape",
            label=f"{label}.pre_audit",
        )
        if not _is_pre_audit_reject(evidence):
            _fail("role-event-shape", f"{label}.pre_audit does not prove rejection")
    else:
        _fail("role-event-shape", f"{label}.status is unknown: {status!r}")
    ordinal = record.get("role_query_ordinal")
    if status == "skipped":
        if ordinal is not None:
            _fail("query-ordinal", f"{label} skipped attempt has an ordinal")
    elif type(ordinal) is not int or ordinal < 1:
        _fail("query-ordinal", f"{label} provider attempt lacks an ordinal")


def _logical_id(
    record: Mapping[str, Any], *, label: str, run_root: Path,
) -> tuple[Any, ...]:
    _check_role_event_shape(record, label=label, run_root=run_root)
    keys = ("workload", "generation", "role", "attempt", "invocation_id")
    missing = [key for key in keys if key not in record]
    if missing:
        _fail("logical-id", f"{label} is missing logical ID fields: {missing}")
    workload, generation, role, attempt, invocation_id = (
        record[key] for key in keys
    )
    if not isinstance(workload, str) or not workload:
        _fail("logical-id", f"{label}.workload is invalid")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        _fail("logical-id", f"{label}.generation is invalid")
    if role not in _ROLE_ORDER:
        _fail("logical-id", f"{label}.role is invalid")
    if type(attempt) is not int or attempt != 1:
        _fail("attempt-policy", f"{label}.attempt must be exactly 1")
    if not isinstance(invocation_id, str) or not invocation_id:
        _fail("logical-id", f"{label}.invocation_id is invalid")
    return workload, generation, role, attempt, invocation_id


def _require_unique_attempts(
    records: Sequence[Mapping[str, Any]], *, side: str, run_root: Path,
) -> None:
    refs = [_canonical_ref(record) for record in records]
    if len(refs) != len(set(refs)):
        _fail("canonical-duplicate", f"{side} has an exact canonical duplicate")
    logical = [
        _logical_id(
            record, label=f"{side} role attempt", run_root=run_root,
        )
        for record in records
    ]
    if len(logical) != len(set(logical)):
        _fail("logical-id", f"{side} has a duplicate logical role attempt ID")


def _check_role_session_isolation(
    *, provider: object, records: Sequence[Mapping[str, Any]],
) -> None:
    if provider != "claude-headless":
        return
    observations = tuple(
        (
            record.get("role"),
            record.get("provenance", {}).get("child_id")
            if isinstance(record.get("provenance"), Mapping)
            else None,
        )
        for record in records
        if record.get("status") == "valid"
    )
    evaluation = evaluate_role_session_isolation(observations)
    if not evaluation.accepted:
        _fail("role-session-isolation", evaluation.reason)


def _check_closed_events(events: Sequence[Mapping[str, Any]]) -> None:
    for index, event in enumerate(events):
        kind = event.get("event")
        if not isinstance(kind, str) or kind not in _EVENTS:
            _fail("closed-event-set", f"journal event {index} has unknown kind: {kind!r}")


def _check_journal_sequence(events: Sequence[Mapping[str, Any]]) -> None:
    for expected, event in enumerate(events, 1):
        if type(event.get("seq")) is not int or event.get("seq") != expected:
            _fail("journal-sequence", f"journal seq must be contiguous 1..N; expected {expected}")
        if not isinstance(event.get("ts"), str) or not event.get("ts"):
            _fail("journal-sequence", f"journal event seq={expected} has no timestamp")


def _check_transport_admission(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
) -> None:
    admissions = [
        event for event in events if event.get("event") == "transport-admission"
    ]
    errors = [
        event
        for event in events
        if event.get("event") == "transport-admission-error"
    ]
    if len(admissions) > 1 and not errors:
        _fail("transport-admission", "transport-admission may occur at most once")
    if len(admissions) + len(errors) > 1:
        _fail(
            "transport-admission",
            "transport admission outcome may occur at most once",
        )
    if errors:
        error = errors[0]
        required = {"event", "type", "message", "seq", "ts"}
        if set(error) != required:
            _fail(
                "transport-admission",
                "transport-admission-error fields must match the producer exact set",
            )
        if not isinstance(error.get("type"), str) or not error["type"]:
            _fail(
                "transport-admission",
                "transport-admission-error.type must be a non-empty string",
            )
        if not isinstance(error.get("message"), str):
            _fail(
                "transport-admission",
                "transport-admission-error.message must be a string",
            )
        starts = [event for event in events if event.get("event") == "run-start"]
        if (
            len(events) < 2
            or events[0] is not error
            or len(starts) != 1
            or events[1] is not starts[0]
        ):
            _fail(
                "transport-admission",
                "transport-admission-error must occur immediately before run-start",
            )
        if report.get("provider") != "claude-headless":
            _fail(
                "transport-admission",
                "transport-admission-error requires the claude-headless provider",
            )
        if "transport_receipt" in report or any(
            "transport_receipt" in event for event in events
        ):
            _fail(
                "transport-admission",
                "transport-admission-error outcome forbids transport_receipt",
            )
        return

    report_has_receipt = "transport_receipt" in report
    if bool(admissions) != report_has_receipt:
        _fail(
            "transport-admission",
            "transport-admission and report transport_receipt must occur together",
        )
    if not admissions:
        return

    admission = admissions[0]
    required = {"event", "transport_receipt", "seq", "ts"}
    if set(admission) != required:
        _fail(
            "transport-admission",
            "transport-admission fields must match the producer exact set",
        )
    starts = [event for event in events if event.get("event") == "run-start"]
    if (
        len(events) < 2
        or events[0] is not admission
        or len(starts) != 1
        or events[1] is not starts[0]
    ):
        _fail(
            "transport-admission",
            "transport-admission must occur immediately before run-start and role attempts",
        )
    if report.get("provider") != "claude-headless":
        _fail(
            "transport-admission",
            "transport-admission requires the claude-headless provider",
        )
    receipt = admission.get("transport_receipt")
    if type(receipt) is not dict:
        _fail(
            "transport-admission",
            "transport-admission.transport_receipt must be an object",
        )
    producer = _producer_module()
    try:
        validated = producer._validate_transport_receipt(receipt)
        report_receipt = producer._validate_transport_receipt(
            report.get("transport_receipt")
        )
    except producer.AutonomousTrialError as exc:
        _fail("transport-admission", f"transport receipt is invalid: {exc}")
    if validated != report_receipt:
        _fail(
            "transport-admission",
            "transport-admission receipt does not match report projection",
        )


def _check_launch_admission_projection(
    *,
    report: Mapping[str, Any],
    start: Mapping[str, Any],
) -> None:
    report_admission = _mapping(
        report.get("launch_admission"),
        gate="launch-admission",
        label="report.launch_admission",
    )
    start_admission = _mapping(
        start.get("launch_admission"),
        gate="launch-admission",
        label="run-start.launch_admission",
    )
    mode = report_admission.get("mode")
    uses_registered_admission_key_shape = (
        type(mode) is str and mode in _REGISTERED_LAUNCH_MODES
    )
    admission_key_sets = (
        _LAUNCH_ADMISSION_REGISTERED_KEYS
        if uses_registered_admission_key_shape
        else _LAUNCH_ADMISSION_KEYS
    )
    if frozenset(report_admission) not in admission_key_sets:
        _fail("launch-admission", "report launch_admission exact keys differ")
    if dict(start_admission) != dict(report_admission):
        _fail("launch-admission", "run-start/report launch_admission differs")
    if type(mode) is not str or mode not in _LAUNCH_ADMISSION_MODES:
        _fail("launch-admission", "launch mode is outside the closed set")
    if report_admission.get("certifying") is not False:
        _fail("launch-admission", "this producer cannot emit certifying input")
    if report_admission.get("trial_id") != report.get("trial_id"):
        _fail("launch-admission", "launch trial_id differs from report")
    if report_admission.get("workloads") != report.get("workloads_requested"):
        _fail("launch-admission", "launch workloads differ from report")
    binding = report_admission.get("binding")
    activation_digest = report_admission.get("activation_report_digest_sha256")
    origin_binding = None
    if "origin_binding" in report_admission:
        origin_binding = _mapping(
            report_admission["origin_binding"],
            gate="launch-admission",
            label="launch_admission.origin_binding",
        )
        if frozenset(origin_binding) != _ORIGIN_BINDING_KEYS:
            _fail("launch-admission", "origin binding exact keys differ")
        authority_workload = _mapping(
            origin_binding.get("authority_workload"),
            gate="launch-admission",
            label="origin_binding.authority_workload",
        )
        if frozenset(authority_workload) != _ORIGIN_WORKLOAD_KEYS:
            _fail("launch-admission", "origin authority workload exact keys differ")
        for field in (
            "authority_blob_sha256", "source_closure_sha256",
            "axis_semantics_sha256", "verifier_policy_sha256",
            "environment_contract_sha256",
        ):
            value = origin_binding.get(field)
            if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
                _fail("launch-admission", f"origin binding {field} is invalid")
        descriptor_sha256 = authority_workload.get("descriptor_sha256")
        if (
            type(descriptor_sha256) is not str
            or _SHA256_RE.fullmatch(descriptor_sha256) is None
        ):
            _fail("launch-admission", "origin authority descriptor is invalid")
        for field in ("records", "threads"):
            value = authority_workload.get(field)
            if type(value) is not int or value < 1:
                _fail("launch-admission", f"origin authority {field} is invalid")
        measurement_head = origin_binding.get("measurement_head")
        if (
            type(measurement_head) is not str
            or re.fullmatch(r"[0-9a-f]{40}", measurement_head) is None
        ):
            _fail("launch-admission", "origin measurement_head is invalid")
        for field in ("origin_id", "cell_key", "campaign_id", "trial_workload"):
            value = origin_binding.get(field)
            if type(value) is not str or not value:
                _fail("launch-admission", f"origin binding {field} is invalid")
        if (
            origin_binding.get("store_scope") != "fixture"
            or origin_binding.get("issuer_seal") != "launch-admission-gate/v1"
        ):
            _fail("launch-admission", "origin issuer projection is invalid")
        if (
            origin_binding.get("trial_workload")
            not in report.get("workloads_requested", ())
        ):
            _fail("launch-admission", "origin workload differs from report")
    if mode == "registered-effective":
        binding = _mapping(
            binding, gate="launch-admission", label="launch_admission.binding",
        )
        if set(binding) != _LAUNCH_BINDING_KEYS:
            _fail("launch-admission", "registered launch binding exact keys differ")
        if (
            report_admission.get("reason_code")
            != "registered-effective-non-certifying"
            or binding.get("trial_id") != report.get("trial_id")
            or [binding.get("workload")] != report.get("workloads_requested")
            or not isinstance(activation_digest, str)
            or _SHA256_RE.fullmatch(activation_digest) is None
        ):
            _fail("launch-admission", "registered launch projection is inconsistent")
        if origin_binding is not None and (
            origin_binding.get("campaign_id") != binding.get("campaign_id")
            or origin_binding.get("trial_workload") != binding.get("workload")
            or origin_binding.get("measurement_head")
            != binding.get("measurement_head")
        ):
            _fail("launch-admission", "origin binding differs from launch binding")
    elif mode == "registered-formal-non-certifying":
        if origin_binding is not None:
            _fail(
                "launch-admission",
                "formal non-certifying launch cannot carry an origin binding",
            )
        binding = _mapping(
            binding, gate="launch-admission", label="launch_admission.binding",
        )
        if set(binding) != _LAUNCH_BINDING_KEYS:
            _fail(
                "launch-admission",
                "formal non-certifying launch binding exact keys differ",
            )
        if (
            report_admission.get("reason_code")
            != "registered-formal-non-certifying"
            or binding.get("trial_id") != report.get("trial_id")
            or [binding.get("workload")] != report.get("workloads_requested")
            or activation_digest is not None
        ):
            _fail(
                "launch-admission",
                "formal non-certifying launch projection is inconsistent",
            )
    elif (
        report_admission.get("reason_code")
        != "explicit-unregistered-exploratory"
        or binding is not None
        or activation_digest is not None
        or origin_binding is not None
    ):
        _fail("launch-admission", "exploratory launch projection is inconsistent")


def _check_origin_terminal_projection(report: Mapping[str, Any]) -> None:
    if "origin_terminal_projection" not in report:
        return
    projection = _mapping(
        report["origin_terminal_projection"],
        gate="origin-terminal-projection",
        label="report.origin_terminal_projection",
    )
    if frozenset(projection) not in _ORIGIN_TERMINAL_PROJECTION_KEYS:
        _fail("origin-terminal-projection", "exact keys differ")
    reason = projection.get("reason_code")
    if reason not in _FORMAL_REASON_CODES:
        _fail("origin-terminal-projection", "reason_code is outside the closed set")
    rejected = reason != "P6Unavailable"
    for field in ("formal_receipt_sha256", "evidence_root_sha256"):
        value = projection.get(field)
        if rejected:
            if value is not None:
                _fail(
                    "origin-terminal-projection",
                    f"rejected projection {field} must be null",
                )
        elif type(value) is not str or _SHA256_RE.fullmatch(value) is None:
            _fail(
                "origin-terminal-projection",
                f"P6Unavailable projection {field} is invalid",
            )
    for field in (
        "authority_blob_sha256", "terminal_payload_sha256",
    ):
        value = projection.get(field)
        if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
            _fail("origin-terminal-projection", f"{field} is invalid")
    if "arm_binding_digest_sha256" in projection:
        value = projection.get("arm_binding_digest_sha256")
        if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
            _fail("origin-terminal-projection", "arm_binding_digest_sha256 is invalid")
    for field in ("origin_id", "cell_key"):
        value = projection.get(field)
        if type(value) is not str or not value:
            _fail("origin-terminal-projection", f"{field} is invalid")
    if projection.get("schema_version") != "OriginTerminalProjection/v1":
        _fail("origin-terminal-projection", "schema_version is invalid")


def _check_run_envelope(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
    attempt_journal: Path,
) -> None:
    starts = [event for event in events if event.get("event") == "run-start"]
    finishes = [event for event in events if event.get("event") == "run-finish"]
    if len(starts) != 1 or len(finishes) != 1:
        _fail("run-envelope", "run-start and run-finish must each occur exactly once")
    first_run_event = (
        1
        if events[0].get("event")
        in {"transport-admission", "transport-admission-error"}
        else 0
    )
    if events[first_run_event] is not starts[0] or events[-1] is not finishes[0]:
        _fail(
            "run-envelope",
            "run-start/run-finish must bound the run after any transport admission",
        )
    start, finish = starts[0], finishes[0]
    producer = _producer_module()
    if report.get("schema_version") != producer.REPORT_SCHEMA_VERSION:
        _fail("run-envelope", "report.schema_version does not match producer version")
    if start.get("schema_version") != producer.SCHEMA_VERSION:
        _fail("run-envelope", "run-start.schema_version does not match producer version")

    trial_id = report.get("trial_id")
    if not isinstance(trial_id, str) or not trial_id:
        _fail("run-envelope", "report.trial_id is not a non-empty string")
    if not isinstance(start.get("trial_id"), str) or not start.get("trial_id"):
        _fail("run-envelope", "run-start.trial_id is not a non-empty string")
    provider = report.get("provider")
    start_provider = start.get("provider")
    if (
        not isinstance(provider, str)
        or not isinstance(start_provider, str)
        or provider not in producer.PROVIDER_KINDS
        or start_provider not in producer.PROVIDER_KINDS
    ):
        _fail("run-envelope", "provider is outside the producer closed set")
    if type(report.get("do_build")) is not bool or type(start.get("do_build")) is not bool:
        _fail("run-envelope", "do_build must be a bool in report and run-start")
    budget = report.get("generation_budget_per_workload")
    start_budget = start.get("generation_budget_per_workload")
    if type(budget) is not int or budget < 1 or type(start_budget) is not int or start_budget < 1:
        _fail("run-envelope", "generation budget must be a positive int in report and run-start")
    stop_policy = _mapping(
        report.get("stop_policy"), gate="run-envelope", label="report.stop_policy",
    )
    max_wall_s = stop_policy.get("max_wall_s")
    if type(max_wall_s) is not int or max_wall_s < 1:
        _fail("run-envelope", "report.stop_policy.max_wall_s must be a positive int")
    if type(start.get("max_wall_s")) is not int or start["max_wall_s"] < 1:
        _fail("run-envelope", "run-start.max_wall_s must be a positive int")
    comparisons = (
        ("trial_id", start.get("trial_id"), report.get("trial_id")),
        ("provider", start.get("provider"), report.get("provider")),
        (
            "generation_budget_per_workload",
            start.get("generation_budget_per_workload"),
            report.get("generation_budget_per_workload"),
        ),
        ("do_build", start.get("do_build"), report.get("do_build")),
        (
            "max_wall_s",
            start.get("max_wall_s"),
            max_wall_s,
        ),
    )
    for label, journal_value, report_value in comparisons:
        if type(journal_value) is not type(report_value) or journal_value != report_value:
            _fail("run-envelope", f"run-start/report mismatch: {label}")
    if budget > producer.MAX_APPROVED_GENERATIONS:
        _fail(
            "run-envelope",
            "generation budget exceeds the current producer-approved limit",
        )
    workloads = report.get("workloads_requested")
    if start.get("workloads") != workloads:
        _fail("run-envelope", "run-start workloads do not match report order")
    if finish.get("status") != report.get("status"):
        _fail("run-envelope", "run-finish status does not match report")
    driver = _mapping(
        report.get("generation_driver"),
        gate="run-envelope",
        label="report.generation_driver",
    )
    if dict(driver) not in (
        _STANDARD_GENERATION_DRIVER,
        _INJECTED_GENERATION_DRIVER,
    ):
        _fail("run-envelope", "generation_driver is outside the closed set")
    if start.get("generation_driver") != driver:
        _fail("run-envelope", "run-start generation_driver differs")
    if finish.get("generation_driver") != driver:
        _fail("run-envelope", "run-finish generation_driver differs")
    gating_digest = report.get("gating_spec_sha256")
    if not isinstance(gating_digest, str) or _SHA256_RE.fullmatch(gating_digest) is None:
        _fail("run-envelope", "gating_spec_sha256 is not a lowercase SHA-256")
    if start.get("gating_spec_sha256") != gating_digest:
        _fail("run-envelope", "run-start GATING_SPEC digest differs")
    if finish.get("gating_spec_sha256") != gating_digest:
        _fail("run-envelope", "run-finish GATING_SPEC digest differs")
    expected_authority = (
        "supervisor-authoritative"
        if dict(driver) == _STANDARD_GENERATION_DRIVER
        else "excluded-caller-injected-unsupported"
    )
    if report.get("honest_accounting_authority") != expected_authority:
        _fail("run-envelope", "report accounting authority differs from driver")
    if start.get("honest_accounting_authority") != expected_authority:
        _fail("run-envelope", "run-start accounting authority differs")
    if finish.get("honest_accounting_authority") != expected_authority:
        _fail("run-envelope", "run-finish accounting authority differs")
    accounting = _mapping(
        report.get("honest_accounting"),
        gate="run-envelope",
        label="report.honest_accounting",
    )
    if set(accounting) != {"role_query_count", "bench_wall_seconds"}:
        _fail("run-envelope", "honest_accounting exact keys differ")
    role_queries = accounting.get("role_query_count")
    bench_seconds = accounting.get("bench_wall_seconds")
    if type(role_queries) is not int or role_queries < 0:
        _fail("run-envelope", "role_query_count is not a nonnegative exact int")
    if (
        isinstance(bench_seconds, bool)
        or not isinstance(bench_seconds, (int, float))
        or not isinstance(float(bench_seconds), float)
        or not math.isfinite(float(bench_seconds))
        or float(bench_seconds) < 0.0
    ):
        _fail("run-envelope", "bench_wall_seconds is not finite and nonnegative")
    if finish.get("honest_accounting") != accounting:
        _fail("run-envelope", "run-finish honest_accounting differs")
    journal_ref = _path_identity(
        report.get("attempt_journal"), gate="run-envelope",
        label="report.attempt_journal",
    )
    try:
        same_journal = journal_ref.samefile(Path(attempt_journal))
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            "[run-envelope] report.attempt_journal cannot be resolved"
        ) from exc
    if not same_journal:
        _fail("run-envelope", "report.attempt_journal names a different journal")
    finish_report = _path_identity(
        finish.get("report"), gate="run-envelope", label="run-finish.report",
    )
    expected_report = Path(attempt_journal).resolve().parent / "report.json"
    if finish_report != expected_report:
        _fail("run-envelope", "run-finish.report names a different report")
    raw_cells = report.get("cells")
    projection_cells = (
        [cell for cell in raw_cells if isinstance(cell, Mapping)]
        if isinstance(raw_cells, list)
        else []
    )
    expected_failures = cell_admission_failure_projection(projection_cells)
    if expected_failures:
        if finish.get("cell_admission_failures") != expected_failures:
            _fail(
                "run-envelope",
                "run-finish cell admission failures differ from report",
            )
    elif "cell_admission_failures" in finish:
        _fail(
            "run-envelope",
            "run-finish has a cell admission failure absent from report",
        )
    _check_launch_admission_projection(report=report, start=start)


def _terminal_events(events: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [event for event in events if event.get("event") in _TERMINAL_EVENTS]


def _check_terminal_projection(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
    cells: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    terminals = _terminal_events(events)
    if len(terminals) > 1:
        _fail("terminal-projection", "more than one terminal supervisor event")
    fatal = report.get("fatal_error")
    if not terminals:
        if "fatal_error" in report:
            _fail("terminal-projection", "fatal_error has no terminal journal event")
        if any(cell.get("stop_reason") == "supervisor-error" for cell in cells):
            _fail("terminal-projection", "supervisor-error cell has no terminal journal event")
        if (
            type(report.get("generation_budget_per_workload")) is int
            and report["generation_budget_per_workload"] >= 2
            and any(
                cell.get("stop_reason") == "supervisor-wall-budget"
                for cell in cells
            )
        ):
            _fail(
                "terminal-projection",
                "supervisor-wall-budget cell has no terminal journal event",
            )
        return None
    terminal = terminals[0]
    kind = terminal["event"]
    if kind == "transport-admission-error":
        if not events or events[0] is not terminal:
            _fail(
                "terminal-projection",
                "transport-admission-error terminal must be the first event",
            )
    elif len(events) < 2 or events[-2] is not terminal:
        _fail("terminal-projection", "terminal supervisor event must precede run-finish")
    if report.get("status") != "partial":
        _fail("terminal-projection", "terminal supervisor event requires partial status")
    fatal_map = _mapping(fatal, gate="terminal-projection", label="fatal_error")
    if kind in {"provider-init-error", "transport-admission-error"}:
        expected = {"type": terminal.get("type"), "message": terminal.get("message")}
        if dict(fatal_map) != expected or cells:
            _fail(
                "terminal-projection",
                f"{kind} projection is inconsistent",
            )
    elif kind == "supervisor-error":
        expected = {"type": terminal.get("type"), "message": terminal.get("message")}
        if dict(fatal_map) != expected:
            _fail("terminal-projection", "supervisor-error fatal projection is inconsistent")
        workload = terminal.get("workload")
        matches = [cell for cell in cells if cell.get("workload") == workload]
        if len(matches) != 1:
            _fail("terminal-projection", "supervisor-error cell is missing or duplicated")
        cell = matches[0]
        if cell.get("stop_reason") != "supervisor-error" or cell.get("error") != expected:
            _fail("terminal-projection", "supervisor-error cell projection is inconsistent")
    elif kind == "supervisor-wall-budget":
        expected = {
            "type": "SupervisorWallBudget",
            "message": "wall budget expired before the next workload",
        }
        if dict(fatal_map) != expected:
            _fail("terminal-projection", "supervisor-wall-budget fatal projection is inconsistent")
    else:  # pragma: no cover - closed-event and terminal sets are exhaustive
        _fail("terminal-projection", f"unknown terminal event: {kind!r}")
    return terminal


def _is_pre_audit_reject(evidence: Mapping[str, Any]) -> bool:
    forbidden = evidence.get("forbidden_identifiers")
    return evidence.get("passed") is False or (
        isinstance(forbidden, list) and bool(forbidden)
    )


def _completion_status_is_valid(
    entry: Mapping[str, Any], *, generation: Mapping[str, Any], label: str,
) -> bool:
    if entry.get("status") == "valid":
        return True
    if entry.get("status") != "skipped" or entry.get("role") != "auditor":
        return False
    preview = generation.get("preview")
    if not isinstance(preview, Mapping) or dict(entry.get("pre_audit", {})) != dict(preview):
        _fail("state-machine", f"{label} skipped auditor evidence differs from generation.preview")
    return _is_pre_audit_reject(preview)


def _check_harness(generation: Mapping[str, Any], *, label: str) -> Mapping[str, Any]:
    harness = _mapping(generation.get("harness"), gate="state-machine", label=f"{label}.harness")
    if not harness:
        _fail("state-machine", f"{label}.harness is empty")
    required = {
        "outcome", "variant", "stop_reason", "iteration", "ran",
        "critic_digest_generated",
    }
    missing = sorted(required - set(harness))
    if missing:
        _fail("state-machine", f"{label}.harness is missing required fields: {missing}")
    if not isinstance(harness["outcome"], str) or not harness["outcome"]:
        _fail("state-machine", f"{label}.harness.outcome is invalid")
    if harness["variant"] is not None and (
        not isinstance(harness["variant"], str) or not harness["variant"]
    ):
        _fail("state-machine", f"{label}.harness.variant is invalid")
    if (
        not isinstance(harness["stop_reason"], str)
        or harness["stop_reason"] not in _producer_module().DRIVER_STOP_REASONS
    ):
        _fail("state-machine", f"{label}.harness.stop_reason is unknown")
    if type(harness["iteration"]) is not int or harness["iteration"] < 0:
        _fail("state-machine", f"{label}.harness.iteration is invalid")
    if type(harness["ran"]) is not bool:
        _fail("state-machine", f"{label}.harness.ran is not a bool")
    if type(harness["critic_digest_generated"]) is not bool:
        _fail(
            "state-machine",
            f"{label}.harness.critic_digest_generated is not a bool",
        )
    if generation.get("outcome") != harness["outcome"]:
        _fail("state-machine", f"{label}.outcome differs from harness.outcome")
    return harness


def _role_prefix_length(roles: Mapping[str, Any], *, label: str) -> int:
    unknown = sorted(set(roles) - set(_ROLE_ORDER))
    if unknown:
        _fail("state-machine", f"{label} has unknown role keys: {unknown}")
    present = set(roles)
    for length in range(len(_ROLE_ORDER) + 1):
        if present == set(_ROLE_ORDER[:length]):
            return length
    _fail("state-machine", f"{label} roles are not an allowed prefix")


def _check_cell_metadata(
    cell: Mapping[str, Any], *, cell_index: int, generations: Sequence[Any],
) -> str | None:
    required = {
        "workload_flags", "descriptor", "descriptor_binding",
        "campaign_id", "campaign_root",
    }
    early_error_without_work = (
        not generations
        and cell.get("stop_reason") in {"supervisor-error", "provider-init-error"}
    )
    if early_error_without_work:
        required = set()
    missing = sorted(required - set(cell))
    if missing:
        _fail("cell-metadata", f"cells[{cell_index}] is missing required fields: {missing}")
    if "workload_flags" in cell:
        workload_flags = _mapping(
            cell["workload_flags"], gate="cell-metadata",
            label=f"cells[{cell_index}].workload_flags",
        )
        if not workload_flags:
            _fail("cell-metadata", f"cells[{cell_index}].workload_flags is empty")
    if "descriptor" in cell:
        descriptor = _mapping(
            cell["descriptor"], gate="cell-metadata",
            label=f"cells[{cell_index}].descriptor",
        )
        if not descriptor:
            _fail("cell-metadata", f"cells[{cell_index}].descriptor is empty")
    descriptor_sha256 = None
    if "descriptor_binding" in cell:
        descriptor_binding = _mapping(
            cell["descriptor_binding"], gate="cell-metadata",
            label=f"cells[{cell_index}].descriptor_binding",
        )
        descriptor_sha256 = descriptor_binding.get("output_sha256")
        if (
            not isinstance(descriptor_sha256, str)
            or _SHA256_RE.fullmatch(descriptor_sha256) is None
        ):
            _fail(
                "cell-metadata",
                f"cells[{cell_index}].descriptor_binding.output_sha256 is not a lowercase SHA-256",
            )
    if "campaign_id" in cell and (
        not isinstance(cell["campaign_id"], str) or not cell["campaign_id"]
    ):
        _fail("cell-metadata", f"cells[{cell_index}].campaign_id is not a non-empty string")
    if "campaign_root" in cell and (
        not isinstance(cell["campaign_root"], str) or not cell["campaign_root"]
    ):
        _fail("cell-metadata", f"cells[{cell_index}].campaign_root is not a non-empty string")
    return descriptor_sha256


def _scan_report_attempts(
    *, cells: Sequence[Mapping[str, Any]], journal_attempts: Sequence[Mapping[str, Any]],
    budget: int, run_root: Path,
) -> list[Mapping[str, Any]]:
    report_attempts: list[Mapping[str, Any]] = []
    for cell_index, cell in enumerate(cells):
        workload = cell.get("workload")
        generations = _list(
            cell.get("generations"), gate="state-machine",
            label=f"cells[{cell_index}].generations",
        )
        descriptor_sha256 = _check_cell_metadata(
            cell, cell_index=cell_index, generations=generations,
        )
        generation_numbers: list[int] = []
        prefix_lengths: list[int] = []
        generation_entries: list[list[Mapping[str, Any]]] = []
        for generation_index, raw_generation in enumerate(generations):
            generation = _mapping(
                raw_generation, gate="state-machine",
                label=f"cell {workload!r} generation {generation_index}",
            )
            number = generation.get("generation")
            if isinstance(number, bool) or not isinstance(number, int):
                _fail("state-machine", f"cell {workload!r} has invalid generation number")
            generation_numbers.append(number)
            roles = _mapping(
                generation.get("roles"), gate="state-machine",
                label=f"cell {workload!r} generation {number} roles",
            )
            prefix_lengths.append(_role_prefix_length(
                roles, label=f"cell {workload!r} generation {number}",
            ))
            entries: list[Mapping[str, Any]] = []
            for role in _ROLE_ORDER:
                if role not in roles:
                    continue
                raw_entry = roles[role]
                entry = _mapping(
                    raw_entry, gate="report-role-shape",
                    label=f"{workload}.g{number}.{role}",
                )
                if entry.get("event") != "role-attempt":
                    _fail("report-role-shape", f"{workload}.g{number}.{role} is not a journaled role event")
                if (
                    entry.get("workload") != workload
                    or entry.get("generation") != number
                    or entry.get("role") != role
                ):
                    _fail("role-placement", f"{workload}.g{number}.{role} is misplaced")
                _check_role_event_shape(
                    entry,
                    label=f"{workload}.g{number}.{role}",
                    run_root=run_root,
                )
                if entry.get("descriptor_sha256") != descriptor_sha256:
                    _fail(
                        "descriptor-binding",
                        f"{workload}.g{number}.{role}.descriptor_sha256 differs from cell binding",
                    )
                entries.append(entry)
                report_attempts.append(entry)
            generation_entries.append(entries)
        if generation_numbers != list(range(1, len(generations) + 1)):
            _fail("state-machine", f"cell {workload!r} generations are not contiguous from 1")
        if len(generations) > budget:
            _fail("state-machine", f"cell {workload!r} exceeds generation budget")
        full = len(_ROLE_ORDER)
        stop_reason = cell.get("stop_reason")
        admission_failed = is_exact_cell_admission_failure_decision(
            cell.get("admission_decision")
        )
        disposition = cell.get("pending_critic_disposition")
        disposition_count = (
            disposition.get("count")
            if isinstance(disposition, Mapping)
            else None
        )
        missing_final_critic = (
            admission_failed
            and _is_exact_pending_critic_disposition(disposition)
            and disposition_count == 1
            and bool(generations)
            and prefix_lengths[-1] == full - 1
            and "harness" in generations[-1]
        )
        if (
            admission_failed
            and disposition_count == 1
            and not missing_final_critic
        ):
            _fail(
                "state-machine",
                f"cell {workload!r} critic discard does not match role history",
            )
        producer = _producer_module()
        driver_terminal_reasons = producer.DRIVER_STOP_REASONS - {"continue"}
        known_stop_reasons = {
            "fixed-generation-budget", "role-invalid",
            "supervisor-wall-budget", "supervisor-error",
        } | set(driver_terminal_reasons)
        if not isinstance(stop_reason, str) or stop_reason not in known_stop_reasons:
            _fail("state-machine", f"cell {workload!r} has unknown stop_reason: {stop_reason!r}")
        if stop_reason == "fixed-generation-budget":
            invalid_prefix = any(
                length != full
                for length in (
                    prefix_lengths[:-1]
                    if missing_final_critic
                    else prefix_lengths
                )
            )
            if len(generations) != budget or invalid_prefix:
                _fail("state-machine", f"fixed-budget cell {workload!r} is incomplete")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"fixed-budget cell {workload!r} has non-valid role history")
                if _check_harness(generation, label=f"{workload}.g{index}")["stop_reason"] != "continue":
                    _fail("state-machine", f"fixed-budget cell {workload!r} has terminal harness stop")
        elif stop_reason == "role-invalid":
            if not generations or any(length != full for length in prefix_lengths[:-1]):
                _fail("state-machine", f"role-invalid cell {workload!r} has invalid history")
            last_roles = generations[-1]["roles"]
            last_role = _ROLE_ORDER[prefix_lengths[-1] - 1] if prefix_lengths[-1] else None
            last_entry = last_roles.get(last_role) if last_role is not None else None
            if not isinstance(last_entry, Mapping) or last_entry.get("status") != "invalid":
                _fail("state-machine", f"role-invalid cell {workload!r} has no invalid final role")
            for index, (generation, entries) in enumerate(
                zip(generations[:-1], generation_entries[:-1]), 1,
            ):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"role-invalid cell {workload!r} has invalid prior role")
                if _check_harness(
                    generation, label=f"{workload}.g{index}",
                )["stop_reason"] != "continue":
                    _fail(
                        "state-machine",
                        f"role-invalid cell {workload!r} has a terminal prior harness stop",
                    )
            final_generation = generations[-1]
            for entry in generation_entries[-1][:-1]:
                if not _completion_status_is_valid(
                    entry, generation=final_generation,
                    label=f"{workload}.g{generation_numbers[-1]}.{entry.get('role')}",
                ):
                    _fail("state-machine", f"role-invalid cell {workload!r} has early invalid role")
            if last_role == "critic":
                _check_harness(final_generation, label=f"{workload}.g{generation_numbers[-1]}")
        elif stop_reason == "supervisor-wall-budget":
            if any(length != full for length in prefix_lengths):
                _fail("state-machine", f"wall-budget cell {workload!r} has partial role state")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"wall-budget cell {workload!r} has non-valid role history")
                if _check_harness(
                    generation, label=f"{workload}.g{index}",
                )["stop_reason"] != "continue":
                    _fail(
                        "state-machine",
                        f"wall-budget cell {workload!r} has a terminal prior harness stop",
                    )
        elif stop_reason == "supervisor-error":
            if any(length != full for length in prefix_lengths[:-1]):
                _fail("state-machine", f"supervisor-error cell {workload!r} has invalid history")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"supervisor-error cell {workload!r} has invalid role history")
                if index < len(generations) or "harness" in generation:
                    harness = _check_harness(generation, label=f"{workload}.g{index}")
                    if index < len(generations) and harness["stop_reason"] != "continue":
                        _fail(
                            "state-machine",
                            f"supervisor-error cell {workload!r} has a terminal prior harness stop",
                        )
        else:
            invalid_prefix = any(
                length != full
                for length in (
                    prefix_lengths[:-1]
                    if missing_final_critic
                    else prefix_lengths
                )
            )
            if not generations or invalid_prefix:
                _fail("state-machine", f"stopped cell {workload!r} is incomplete")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"stopped cell {workload!r} has non-valid role history")
                harness = _check_harness(generation, label=f"{workload}.g{index}")
                expected_stop = stop_reason if index == len(generations) else "continue"
                if harness["stop_reason"] != expected_stop:
                    _fail("state-machine", f"stopped cell {workload!r} harness stop projection differs")
    return report_attempts


def _check_attempt_sequence(
    journal_attempts: Sequence[Mapping[str, Any]],
    report_attempts: Sequence[Mapping[str, Any]],
) -> None:
    keys = ("workload", "generation", "role")
    journal_order = [tuple(event.get(key) for key in keys) for event in journal_attempts]
    report_order = [tuple(event.get(key) for key in keys) for event in report_attempts]
    if journal_order != report_order:
        _fail("state-machine", "journal role attempts do not follow report role state order")


def _check_workload_coverage(
    *, report: Mapping[str, Any], cells: Sequence[Mapping[str, Any]],
    terminal: Mapping[str, Any] | None,
) -> None:
    requested = report.get("workloads_requested")
    if (
        not isinstance(requested, list)
        or not requested
        or not all(isinstance(item, str) and item for item in requested)
        or len(requested) != len(set(requested))
    ):
        _fail("workload-coverage", "workloads_requested is not a unique string list")
    actual = [cell.get("workload") for cell in cells]
    if len(actual) != len(set(actual)) or actual != requested[:len(actual)]:
        _fail("workload-coverage", "cell workloads are not a unique requested prefix")
    terminal_kind = terminal.get("event") if terminal is not None else None
    multigeneration = (
        type(report.get("generation_budget_per_workload")) is int
        and report["generation_budget_per_workload"] >= 2
    )
    if len(actual) == len(requested):
        if terminal_kind == "supervisor-wall-budget":
            if not multigeneration:
                _fail(
                    "workload-coverage",
                    "wall-budget terminal event has no missing workload",
                )
            if (
                not actual
                or terminal.get("workload") != actual[-1]
                or cells[-1].get("stop_reason") != "supervisor-wall-budget"
                or type(terminal.get("generation")) is not int
            ):
                _fail(
                    "workload-coverage",
                    "wall-budget terminal does not identify an in-cell zero-work stop",
                )
            return
        if (
            terminal_kind == "supervisor-error"
            and (not actual or terminal.get("workload") != actual[-1])
        ):
            _fail("workload-coverage", "supervisor-error cell is not the final cell")
        return
    failure_indices = [
        index
        for index, cell in enumerate(cells)
        if is_exact_cell_admission_failure_decision(
            cell.get("admission_decision")
        )
    ]
    if (
        failure_indices == [len(cells) - 1]
        and report.get("status") == "partial"
    ):
        return
    if terminal is None:
        _fail("workload-coverage", "requested workload suffix is unexplained")
    kind = terminal_kind
    if kind in {"provider-init-error", "transport-admission-error"} and not actual:
        return
    if kind == "supervisor-wall-budget" and terminal.get("workload") == requested[len(actual)]:
        if multigeneration and type(terminal.get("generation")) is int:
            _fail("workload-coverage", "requested workload suffix is unexplained")
        return
    if (
        multigeneration
        and kind == "supervisor-wall-budget"
        and actual
        and terminal.get("workload") == actual[-1]
        and cells[-1].get("stop_reason") == "supervisor-wall-budget"
        and type(terminal.get("generation")) is int
    ):
        return
    if (
        kind == "supervisor-error"
        and actual
        and terminal.get("workload") == actual[-1]
    ):
        return
    _fail("workload-coverage", "terminal event does not explain requested workload suffix")


def _check_status_projection(
    report: Mapping[str, Any], cells: Sequence[Mapping[str, Any]],
) -> None:
    requested = report.get("workloads_requested")
    complete = (
        isinstance(requested, list)
        and len(cells) == len(requested)
        and report.get("fatal_error") is None
        and all(
            cell.get("stop_reason")
            not in {"role-invalid", "supervisor-error", "supervisor-wall-budget"}
            for cell in cells
        )
        and (
            report.get("do_build") is not True
            or all(
                is_positive_cell_admission_decision(
                    cell.get("admission_decision")
                )
                for cell in cells
            )
        )
    )
    expected = "complete" if complete else "partial"
    if report.get("status") != expected:
        _fail("terminal-projection", f"report status must be {expected!r}")


def _check_generation_accounting(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
    cells: Sequence[Mapping[str, Any]],
    terminal: Mapping[str, Any] | None,
) -> None:
    accounting_events = [
        event for event in events
        if event.get("event") == "generation-accounting"
    ]
    attempts = [event for event in events if event.get("event") == "role-attempt"]
    ordinals = [
        event.get("role_query_ordinal")
        for event in attempts
        if event.get("status") != "skipped"
    ]
    if ordinals != list(range(1, len(ordinals) + 1)):
        _fail("query-ordinal", "provider query ordinals are not contiguous")

    driver = report["generation_driver"]
    gating_digest = report["gating_spec_sha256"]
    authority = report["honest_accounting_authority"]
    expected_event_keys = {
        "event", "workload", "generation", "state", "provider_invoke_count",
        "auditor_pre_audit_skipped", "bench_wall_seconds",
        "generation_driver", "gating_spec_sha256", "accounting_authority",
        "seq", "ts",
    }
    by_pair: dict[tuple[str, int], Mapping[str, Any]] = {}
    for index, event in enumerate(accounting_events):
        label = f"generation-accounting[{index}]"
        if set(event) != expected_event_keys:
            _fail("generation-accounting", f"{label} exact keys differ")
        workload = event.get("workload")
        generation = event.get("generation")
        if not isinstance(workload, str) or not workload:
            _fail("generation-accounting", f"{label}.workload is invalid")
        if type(generation) is not int or generation < 1:
            _fail("generation-accounting", f"{label}.generation is invalid")
        pair = (workload, generation)
        if pair in by_pair:
            _fail("generation-accounting", f"duplicate accounting pair: {pair}")
        by_pair[pair] = event
        if event.get("state") not in {
            "generation-complete", "partial-generation",
            "pending-pre-invoke-failure",
        }:
            _fail("generation-accounting", f"{label}.state is unknown")
        count = event.get("provider_invoke_count")
        if type(count) is not int or count < 0:
            _fail("generation-accounting", f"{label} provider count is invalid")
        skipped = event.get("auditor_pre_audit_skipped")
        if type(skipped) is not bool:
            _fail("generation-accounting", f"{label} auditor skip is not bool")
        bench = event.get("bench_wall_seconds")
        if (
            isinstance(bench, bool)
            or not isinstance(bench, (int, float))
            or not math.isfinite(float(bench))
            or float(bench) < 0.0
        ):
            _fail("generation-accounting", f"{label} bench time is invalid")
        if event.get("generation_driver") != driver:
            _fail("generation-accounting", f"{label} driver identity differs")
        if event.get("gating_spec_sha256") != gating_digest:
            _fail("generation-accounting", f"{label} GATING_SPEC digest differs")
        if event.get("accounting_authority") != authority:
            _fail("generation-accounting", f"{label} authority differs")
        if authority != "supervisor-authoritative" and float(bench) != 0.0:
            _fail("generation-accounting", f"{label} injected bench is nonzero")
        pair_attempts = [
            attempt for attempt in attempts
            if (attempt.get("workload"), attempt.get("generation")) == pair
        ]
        invoked = [
            attempt for attempt in pair_attempts
            if attempt.get("status") != "skipped"
        ]
        if len(invoked) != count:
            _fail("generation-accounting", f"{label} provider count differs")
        observed_skip = any(
            attempt.get("role") == "auditor"
            and attempt.get("status") == "skipped"
            for attempt in pair_attempts
        )
        if observed_skip is not skipped:
            _fail("generation-accounting", f"{label} auditor skip differs")
        if pair_attempts and event["seq"] <= max(
            attempt["seq"] for attempt in pair_attempts
        ):
            _fail("generation-accounting", f"{label} precedes its role attempts")

    recorded_pairs: set[tuple[str, int]] = set()
    for cell in cells:
        workload = cell.get("workload")
        generations = cell.get("generations", [])
        if not isinstance(generations, list):
            continue
        disposition = cell.get("pending_critic_disposition")
        if (
            _is_exact_pending_critic_disposition(disposition)
            and disposition.get("count") == 1
        ):
            final_generation = generations[-1] if generations else None
            generation_number = (
                final_generation.get("generation")
                if isinstance(final_generation, Mapping)
                else None
            )
            event = by_pair.get((workload, generation_number))
            if event is None or event.get("state") != "partial-generation":
                _fail(
                    "generation-accounting",
                    "discarded final critic requires partial-generation accounting",
                )
        for generation in generations:
            if not isinstance(generation, Mapping):
                continue
            pair = (workload, generation.get("generation"))
            recorded_pairs.add(pair)
            event = by_pair.get(pair)
            if event is None:
                _fail("generation-accounting", f"missing accounting pair: {pair}")
            if generation.get("bench_wall_seconds") != event["bench_wall_seconds"]:
                _fail("generation-accounting", f"{pair} bench projection differs")
            if generation.get("generation_driver") != driver:
                _fail("generation-accounting", f"{pair} driver projection differs")
            if generation.get("gating_spec_sha256") != gating_digest:
                _fail("generation-accounting", f"{pair} GATING_SPEC projection differs")
        if (
            cell.get("stop_reason") == "supervisor-wall-budget"
            and report.get("generation_budget_per_workload", 0) >= 2
        ):
            zero_generation = len(generations) + 1
            if (
                terminal is None
                or terminal.get("event") != "supervisor-wall-budget"
                or terminal.get("workload") != workload
                or terminal.get("generation") != zero_generation
                or terminal.get("zero_work") is not True
                or terminal.get("role_query_count") != 0
                or type(terminal.get("role_query_count")) is not int
                or terminal.get("bench_wall_seconds") != 0.0
                or isinstance(terminal.get("bench_wall_seconds"), bool)
                or not isinstance(
                    terminal.get("bench_wall_seconds"), (int, float)
                )
            ):
                _fail(
                    "generation-accounting",
                    "zero-work wall terminal fields differ",
                )
    if set(by_pair) != recorded_pairs:
        _fail("generation-accounting", "accounting/generation correspondence differs")

    honest = report["honest_accounting"]
    if honest["role_query_count"] != len(ordinals):
        _fail("generation-accounting", "report role query total differs")
    bench_total = sum(
        event["bench_wall_seconds"] for event in accounting_events
    )
    if honest["bench_wall_seconds"] != bench_total:
        _fail("generation-accounting", "report bench total differs")


def assert_autonomous_trial_completeness(
    *, report: Mapping[str, Any], attempt_journal: Path,
) -> None:
    """Re-read *attempt_journal* and verify its complete report projection."""
    report = _mapping(report, gate="report-shape", label="report")
    attempt_journal = Path(attempt_journal)
    run_root = attempt_journal.resolve().parent
    journal_bytes, events = _read_journal(attempt_journal)
    expected_hash = hashlib.sha256(journal_bytes).hexdigest()
    if report.get("attempt_journal_sha256") != expected_hash:
        _fail("journal-hash", "attempt_journal_sha256 does not match bytes read")
    _check_closed_events(events)
    _check_journal_sequence(events)
    _check_transport_admission(report=report, events=events)
    _check_run_envelope(
        report=report, events=events, attempt_journal=attempt_journal,
    )
    _check_origin_terminal_projection(report)
    launch = report.get("launch_admission")
    launch_mode = (
        launch.get("mode") if isinstance(launch, Mapping) else None
    )
    arm_execution_permitted = (
        type(launch_mode) is str
        and launch_mode in _REGISTERED_LAUNCH_MODES
    )
    if not arm_execution_permitted and (
        "arm_execution" in report
        or any(
            event.get("event") == "run-start" and "arm_execution" in event
            for event in events
        )
    ):
        _fail("arm-digest-chain", "exploratory run carries arm_execution")
    raw_cells = _list(report.get("cells"), gate="report-shape", label="report.cells")
    cells = [
        _mapping(cell, gate="report-shape", label=f"cells[{index}]")
        for index, cell in enumerate(raw_cells)
    ]
    do_build = report.get("do_build")
    failure_indices: list[int] = []
    for index, cell in enumerate(cells):
        decision = cell.get("admission_decision")
        if LAYER3_ADMISSION_DIAGNOSIS_KEY in cell:
            if not is_exact_layer3_admission_diagnosis(
                cell[LAYER3_ADMISSION_DIAGNOSIS_KEY]
            ):
                _fail(
                    "artifact-admission",
                    f"cells[{index}] Layer-3 admission diagnosis is not exact",
                )
            if not is_exact_cell_admission_failure_decision(decision):
                _fail(
                    "artifact-admission",
                    f"cells[{index}] diagnosis has no exact admission failure",
                )
        if do_build is False:
            if decision != {"admission_status": "not-applicable"}:
                _fail(
                    "artifact-admission",
                    f"cells[{index}] no-build admission decision is not exact",
                )
            if "pending_critic_disposition" in cell:
                _fail(
                    "artifact-admission",
                    f"cells[{index}] no-build cell has admission failure disposition",
                )
        elif do_build is True:
            decision = _mapping(
                decision, gate="artifact-admission",
                label=f"cells[{index}].admission_decision",
            )
            if is_positive_cell_admission_decision(decision):
                if "pending_critic_disposition" in cell:
                    _fail(
                        "artifact-admission",
                        f"cells[{index}] admitted cell has failure disposition",
                    )
            elif is_exact_cell_admission_failure_decision(decision):
                if not _is_exact_pending_critic_disposition(
                    cell.get("pending_critic_disposition")
                ):
                    _fail(
                        "artifact-admission",
                        f"cells[{index}] failure disposition is not exact",
                    )
                failure_indices.append(index)
            else:
                _fail(
                    "artifact-admission",
                    f"cells[{index}] build admission decision is neither positive nor exact failure",
                )
    if len(failure_indices) > 1:
        _fail("artifact-admission", "multiple cell admission failures are forbidden")
    if failure_indices:
        if failure_indices != [len(cells) - 1]:
            requested = report.get("workloads_requested")
            if isinstance(requested, list) and len(cells) < len(requested):
                _fail(
                    "artifact-admission",
                    "requested workload suffix is unexplained",
                )
            _fail(
                "artifact-admission",
                "cell admission failure must be the final cell",
            )
        if report.get("status") != "partial":
            _fail("artifact-admission", "cell admission failure requires partial status")
    terminal = _check_terminal_projection(report=report, events=events, cells=cells)
    budget = report.get("generation_budget_per_workload")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        _fail("state-machine", "generation budget is not a positive int")
    journal_attempts = [event for event in events if event.get("event") == "role-attempt"]
    _require_unique_attempts(
        journal_attempts, side="journal", run_root=run_root,
    )
    _check_role_session_isolation(
        provider=report.get("provider"), records=journal_attempts,
    )
    report_attempts = _scan_report_attempts(
        cells=cells,
        journal_attempts=journal_attempts,
        budget=budget,
        run_root=run_root,
    )
    _require_unique_attempts(
        report_attempts, side="report", run_root=run_root,
    )
    _check_attempt_sequence(journal_attempts, report_attempts)
    if Counter(map(_canonical_ref, journal_attempts)) != Counter(
        map(_canonical_ref, report_attempts)
    ):
        _fail("role-bijection", "journal/report role-attempt multisets differ")
    _check_workload_coverage(report=report, cells=cells, terminal=terminal)
    _check_generation_accounting(
        report=report, events=events, cells=cells, terminal=terminal,
    )
    _check_status_projection(report, cells)
    receipt_arm = None
    receipt_content_digest = None
    if arm_execution_permitted:
        launch_binding = report.get("launch_admission", {}).get("binding")
        if isinstance(launch_binding, Mapping):
            receipt_arm = launch_binding.get("arm")
        report_arm = report.get("arm_execution")
        if isinstance(report_arm, Mapping):
            receipt_content_digest = report_arm.get("content_digest_sha256")
    _check_payload_validation_receipts(
        report_attempts,
        arm=receipt_arm,
        content_digest=receipt_content_digest,
    )


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=False,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[campaign-chain] layer3 report is not canonical JSON: {exc}"
        ) from exc


def _cross_binding_wal_dict(record: Any) -> dict[str, Any]:
    if not isinstance(record, wal.WalRecord):
        _fail("cross-binding-wal", "WAL reader returned a non-record value")
    return {
        "variant": record.variant,
        "stage": record.stage,
        "env_tag": record.env_tag,
        "ts": record.ts,
        "payload": dict(record.payload),
    }


def _cross_binding_verified_wal_records(
    raw: bytes,
) -> tuple[list[wal.WalRecord], bool]:
    """Parse WAL records from the bytes already verified by the caller.

    The cross-binding consumer must not validate one WAL byte stream and then
    derive its projection from a second filesystem read.  This parser mirrors
    the checked WAL reader's framing contract while keeping the verified byte
    snapshot as the sole source of records.
    """
    if not isinstance(raw, bytes):
        _fail("cross-binding-wal", "verified WAL bytes are not bytes")
    if not raw:
        return [], False
    frames = raw.split(b"\n")
    truncated = not raw.endswith(b"\n")
    if truncated:
        frames = frames[:-1]
    else:
        frames = frames[:-1]
    records: list[wal.WalRecord] = []
    for line_number, frame in enumerate(frames, 1):
        try:
            records.append(wal.parse_line(frame.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError, wal.WalLineError) as exc:
            raise AutonomousTrialCompletenessError(
                f"[cross-binding-wal] verified WAL line {line_number} is invalid"
            ) from exc
    return records, truncated


def _cross_binding_layer3_wal_records(
    records: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Apply Layer 3's WAL normalization to an already verified projection."""
    return [
        record for record in records
        if record.get("stage") != trigger_gate_binding.WAL_RECORD_STAGE
    ]


def _cross_binding_relative_path(path: Path, root: Path, *, label: str) -> str:
    try:
        return path.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()
    except (OSError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[cross-binding] {label} is outside its authority root"
        ) from exc


def _cross_binding_regular_path(path: Path, *, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            f"[cross-binding] {label} cannot be stated"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail("cross-binding", f"{label} is not a regular non-symlink file")


def _cross_binding_campaign_files(
    campaign_root: Path, *, persisted_path: Path,
) -> set[str]:
    files: set[str] = set()
    try:
        candidates = campaign_root.rglob("*")
        for candidate in candidates:
            if candidate.is_symlink():
                _fail("cross-binding-artifacts", "campaign artifact tree traverses a symlink")
            if candidate.is_file():
                relative = candidate.relative_to(campaign_root).as_posix()
                if candidate.resolve(strict=True) != persisted_path.resolve(strict=True):
                    files.add(relative)
    except AutonomousTrialCompletenessError:
        raise
    except (OSError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            "[cross-binding-artifacts] campaign artifact tree cannot be scanned"
        ) from exc
    return files


def _cross_binding_artifact_refs(
    persisted: Mapping[str, Any], *, campaign_root: Path, persisted_path: Path,
) -> tuple[list[dict[str, str]], dict[str, bytes]]:
    raw_refs = _list(
        persisted.get("artifact_refs"), gate="cross-binding-artifacts",
        label="layer3_report.artifact_refs",
    )
    refs: list[dict[str, str]] = []
    verified_bytes: dict[str, bytes] = {}
    declared_refs: list[tuple[int, str, str]] = []
    declared_paths: set[str] = set()
    seen: set[str] = set()
    for index, raw_ref in enumerate(raw_refs):
        ref = _mapping(
            raw_ref, gate="cross-binding-artifacts",
            label=f"layer3_report.artifact_refs[{index}]",
        )
        if set(ref) != {"path", "sha256"}:
            _fail(
                "cross-binding-artifacts",
                f"artifact_refs[{index}] exact keys differ",
            )
        path_value = ref.get("path")
        if type(path_value) is not str or not path_value:
            _fail("cross-binding-artifacts", "artifact ref path is invalid")
        path = Path(path_value)
        if (
            path.is_absolute()
            or path.as_posix() != path_value
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            _fail("cross-binding-artifacts", "artifact ref path is not canonical")
        expected = ref.get("sha256")
        if type(expected) is not str or _SHA256_RE.fullmatch(expected) is None:
            _fail("cross-binding-artifacts", "artifact ref sha256 is invalid")
        declared_paths.add(path_value)
        if path_value in seen:
            _fail("cross-binding-artifacts", "artifact_refs contain a duplicate path")
        seen.add(path_value)
        declared_refs.append((index, path_value, expected))
    if declared_paths != _cross_binding_campaign_files(
        campaign_root, persisted_path=persisted_path,
    ):
        _fail(
            "cross-binding-artifacts",
            "artifact_refs do not enumerate exactly the campaign artifact files",
        )
    for index, path_value, expected in declared_refs:
        resolved, raw = read_and_verify_bytes(
            path_value,
            root=campaign_root,
            expected_sha256=expected,
            gate="cross-binding-artifacts",
            label=f"artifact_refs[{index}]",
        )
        relative = _cross_binding_relative_path(
            resolved, campaign_root, label=f"artifact_refs[{index}]",
        )
        if resolved == persisted_path.resolve(strict=True):
            _fail("cross-binding-artifacts", "artifact_refs must not self-reference layer3 report")
        if relative != path_value:
            _fail("cross-binding-artifacts", "artifact ref path changed while being read")
        verified_bytes[relative] = raw
        refs.append({"path": relative, "sha256": expected})
    return refs, verified_bytes


def _cross_binding_whiteboard(
    campaign_root: Path, *, artifact_paths: set[str],
    verified_bytes: Mapping[str, bytes],
) -> list[Mapping[str, Any]]:
    state_path = campaign_root / "loop_state.json"
    if state_path.exists() or state_path.is_symlink():
        if "loop_state.json" not in artifact_paths:
            _fail("cross-binding-source", "loop_state.json is absent from artifact_refs")
        _cross_binding_regular_path(state_path, label="loop_state.json")
        state_raw = verified_bytes.get("loop_state.json")
        if state_raw is None:
            _fail("cross-binding-source", "loop_state.json bytes were not verified")
        state = _mapping(
            _decode_json(state_raw, label="loop_state.json"),
            gate="cross-binding-source", label="loop_state.json",
        )
        whiteboard = _list(
            state.get("whiteboard"), gate="cross-binding-source",
            label="loop_state.whiteboard",
        )
        return [
            _mapping(
                item, gate="cross-binding-source",
                label="loop_state.whiteboard item",
            )
            for item in whiteboard
        ]
    return []


def _cross_binding_role_events(
    events: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    role_events = [
        _mapping(event, gate="cross-binding-role", label=f"events[{index}]")
        for index, event in enumerate(events)
        if isinstance(event, Mapping) and event.get("event") == "role-attempt"
    ]
    if not role_events:
        _fail("cross-binding-role", "build report has no role-attempt events")
    for index, event in enumerate(role_events):
        invocation_id = event.get("invocation_id")
        if type(invocation_id) is not str or not invocation_id:
            _fail("cross-binding-role", f"role event {index} invocation_id is invalid")
    return role_events


def _cross_binding_proposals(
    report: Mapping[str, Any], *, run_root: Path,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    from . import reflux_ir

    paths: list[str] = []
    digests: list[str] = []
    rows: list[dict[str, Any]] = []
    for cell_index, raw_cell in enumerate(
        _list(report.get("cells"), gate="cross-binding-proposal", label="report.cells")
    ):
        cell = _mapping(
            raw_cell, gate="cross-binding-proposal", label=f"cells[{cell_index}]",
        )
        generations = _list(
            cell.get("generations"), gate="cross-binding-proposal",
            label=f"cells[{cell_index}].generations",
        )
        for generation_index, raw_generation in enumerate(generations):
            generation = _mapping(
                raw_generation, gate="cross-binding-proposal",
                label=f"cells[{cell_index}].generations[{generation_index}]",
            )
            if "proposal" not in generation:
                continue
            proposal = _mapping(
                generation.get("proposal"), gate="cross-binding-proposal",
                label="generation.proposal",
            )
            path_value = proposal.get("path")
            expected = proposal.get("sha256")
            resolved, raw = read_and_verify_bytes(
                path_value,
                root=run_root,
                expected_sha256=expected,
                gate="cross-binding-proposal",
                label="generation.proposal",
            )
            proposal_root = (run_root / "proposals").resolve(strict=True)
            if resolved.parent != proposal_root:
                _fail("cross-binding-proposal", "proposal path is outside run_root/proposals")
            relative = _cross_binding_relative_path(
                resolved, run_root, label="proposal path",
            )
            value = _decode_canonical_object(
                raw, gate="cross-binding-proposal", label=relative,
            )
            coder = _mapping(
                value.get("coder"), gate="cross-binding-proposal",
                label=f"{relative}.coder",
            )
            planner = _mapping(
                value.get("planner"), gate="cross-binding-proposal",
                label=f"{relative}.planner",
            )
            if set(coder) != {"axis", "wire", "justification", "confidence"}:
                _fail(
                    "cross-binding-proposal",
                    f"trial={report.get('trial_id')!r} value={sorted(coder)} "
                    f"path={relative}.coder exact keys differ",
                )
            axis_owners = {"planner": planner, "coder": coder}
            axis_owners.update({
                name: item
                for name, item in value.items()
                if name not in axis_owners
                if isinstance(item, Mapping) and "axis" in item
            })
            if not {"planner", "coder"}.issubset(axis_owners):
                _fail(
                    "cross-binding-axis",
                    f"trial={report.get('trial_id')!r} value={sorted(axis_owners)!r} "
                    f"path={relative} planner/coder axis declarations are required",
                )
            for owner, item in axis_owners.items():
                if item.get("axis") != "silo-backoff-trigger-gating":
                    _fail(
                        "cross-binding-axis",
                        f"trial={report.get('trial_id')!r} value={item.get('axis')!r} "
                        f"path={relative}.{owner}.axis expected "
                        "'silo-backoff-trigger-gating'",
                    )
            try:
                ir = reflux_ir.parse_wire(coder.get("wire"))
                assignment = reflux_ir.emit_predicate(ir)
                predicate_sha256 = trigger_gate_binding.expected_predicate_sha256(
                    ir.mask
                )
            except reflux_ir.RefluxIRError as exc:
                raise AutonomousTrialCompletenessError(
                    f"[cross-binding-predicate] trial={report.get('trial_id')!r} "
                    f"value={coder.get('wire')!r} path={relative}.coder.wire "
                    "is not an exact trigger wire"
                ) from exc
            if assignment == "true" or assignment == "izanagi_gate_pass = true;":
                _fail(
                    "cross-binding-predicate",
                    f"trial={report.get('trial_id')!r} value={assignment!r} "
                    f"path={relative}.coder.wire emitted a skeleton predicate",
                )
            generation_number = generation.get("generation")
            if type(generation_number) is not int or generation_number < 1:
                _fail(
                    "cross-binding-proposal",
                    f"trial={report.get('trial_id')!r} value={generation_number!r} "
                    f"path=cells[{cell_index}].generations[{generation_index}].generation "
                    "is invalid",
                )
            paths.append(relative)
            digests.append(expected)
            rows.append({
                "cell_index": cell_index,
                "generation_index": generation_index,
                "generation": generation_number,
                "proposal_path": relative,
                "proposal_sha256": expected,
                "wire": coder["wire"],
                "mask": ir.mask,
                "predicate_assignment": assignment,
                "predicate_sha256": predicate_sha256,
                "harness": generation.get("harness"),
            })
    if not paths:
        _fail("cross-binding-proposal", "build report has no proposal bytes")
    return paths, digests, rows


def _cross_binding_provenance_rows(
    *, report: Mapping[str, Any], run_root: Path, campaign_root: Path,
    verified_bytes: Mapping[str, bytes],
) -> list[dict[str, Any]]:
    relative = "reports/p3_s8a_trigger_loop_provenance.json"
    raw = verified_bytes.get(relative)
    if raw is None:
        _fail(
            "cross-binding-attempt",
            f"trial={report.get('trial_id')!r} value=None "
            f"path={campaign_root / relative} provenance bytes are required",
        )
    provenance = _mapping(
        _decode_json(raw, label=relative), gate="cross-binding-attempt",
        label=relative,
    )
    entries = _mapping(
        provenance.get("entries"), gate="cross-binding-attempt",
        label=f"{relative}.entries",
    )
    rows: list[dict[str, Any]] = []
    for key, raw_entry in entries.items():
        entry = _mapping(
            raw_entry, gate="cross-binding-attempt",
            label=f"{relative}.entries[{key!r}]",
        )
        proposal_value = entry.get("proposal_path")
        if type(proposal_value) is not str or not proposal_value:
            _fail(
                "cross-binding-attempt",
                f"trial={report.get('trial_id')!r} value={proposal_value!r} "
                f"path={relative}.entries[{key!r}].proposal_path is required",
            )
        proposal_path = Path(proposal_value)
        if not proposal_path.is_absolute():
            proposal_path = run_root / proposal_path
        try:
            proposal_relative = proposal_path.resolve(strict=True).relative_to(
                run_root.resolve(strict=True)
            ).as_posix()
        except (OSError, ValueError) as exc:
            raise AutonomousTrialCompletenessError(
                f"[cross-binding-attempt] trial={report.get('trial_id')!r} "
                f"value={proposal_value!r} "
                f"path={relative}.entries[{key!r}].proposal_path is outside run_root"
            ) from exc
        rows.append({
            "entry_key": str(key),
            "proposal_path": proposal_relative,
            "variant": entry.get("variant"),
            "build_attempt_id": entry.get("build_attempt_id"),
            "trigger_gate_binding_commitment": entry.get(
                "trigger_gate_binding_commitment"
            ),
            "outcome": entry.get("outcome"),
        })
    return rows


def _cross_binding_preimage_assignment_count(
    *, report: Mapping[str, Any], preimage: bytes, expected_assignment: str,
    path: str,
) -> int:
    from . import source_digest

    segments = preimage.split(b"\0")
    expected_segments = len(source_digest.EVOLVE_BLOCK_SOURCES)
    if len(segments) != expected_segments:
        _fail(
            "cross-binding-source-association",
            f"trial={report.get('trial_id')!r} value={len(segments)!r} path={path} "
            f"preimage segment count differs from {expected_segments}",
        )
    try:
        source_index = source_digest.EVOLVE_BLOCK_SOURCES.index(
            "cc/silo/transaction.cc"
        )
    except ValueError as exc:  # pragma: no cover - checked by source registry tests
        raise AutonomousTrialCompletenessError(
            "[cross-binding-source-association] cc/silo/transaction.cc is absent "
            "from the source digest registry"
        ) from exc
    expected = expected_assignment.encode("utf-8")
    marker = b"izanagi_gate_pass"
    contexts = segments[source_index].split(b"\x02")
    expected_context_count = len(source_digest.CONTEXT_MACROS) + 1
    expected_lines = Counter((
        b"bool izanagi_gate_pass = true;",
        expected,
        b"if (izanagi_gate_pass) {",
    ))
    observed_lines = [
        [line.strip() for line in context.splitlines() if marker in line]
        for context in contexts
    ]
    unexpected_source_markers = {
        index: [line.strip() for line in segment.splitlines() if marker in line]
        for index, segment in enumerate(segments)
        if index != source_index and marker in segment
    }
    if (
        len(contexts) != expected_context_count
        or unexpected_source_markers
        or any(Counter(lines) != expected_lines for lines in observed_lines)
    ):
        _fail(
            "cross-binding-source-association",
            f"trial={report.get('trial_id')!r} "
            f"value={{'context_count': {len(contexts)!r}, "
            f"'gate_lines': {observed_lines!r}, "
            f"'other_source_gate_lines': {unexpected_source_markers!r}}} "
            f"path={path} gate-line multisets do not exactly bind the proposal",
        )
    return sum(lines.count(expected) for lines in observed_lines)


def _cross_binding_supervisor_records(
    report: Mapping[str, Any], *, bench_records: Sequence[Mapping[str, Any]],
    aborted_variants: set[str],
) -> None:
    by_attempt: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for record in bench_records:
        payload = _mapping(
            record.get("payload"), gate="cross-binding-bench",
            label="WAL bench_done.payload",
        )
        key = (str(record.get("variant")), str(payload.get("build_attempt_id")))
        by_attempt.setdefault(key, []).append(record)
    seen: set[tuple[str, str]] = set()
    for raw_cell in _list(
        report.get("cells"), gate="cross-binding-bench", label="report.cells",
    ):
        cell = _mapping(raw_cell, gate="cross-binding-bench", label="cell")
        for raw_generation in _list(
            cell.get("generations"), gate="cross-binding-bench",
            label="cell.generations",
        ):
            generation = _mapping(
                raw_generation, gate="cross-binding-bench", label="generation",
            )
            harness = _mapping(
                generation.get("harness"), gate="cross-binding-bench",
                label="generation.harness",
            )
            variant = harness.get("variant")
            if variant is None:
                continue
            if type(variant) is not str or not variant:
                _fail("cross-binding-bench", "harness.variant is invalid")
            harness_records = _mapping(
                harness.get("records"), gate="cross-binding-bench",
                label="generation.harness.records",
            )
            raw_harness_bench = harness_records.get("bench_done")
            if raw_harness_bench is None:
                if variant not in aborted_variants:
                    _fail(
                        "cross-binding-bench",
                        "unbenched harness variant is not a verified aborted attempt",
                    )
                continue
            harness_bench = _mapping(
                raw_harness_bench, gate="cross-binding-bench",
                label="generation.harness.records.bench_done",
            )
            key = (variant, str(harness_bench.get("build_attempt_id")))
            matches = by_attempt.get(key, [])
            if len(matches) != 1 or key in seen:
                _fail("cross-binding-bench", "harness attempt does not bind one bench record")
            seen.add(key)
            bench = matches[0]
            if dict(harness_bench) != dict(bench.get("payload", {})):
                _fail("cross-binding-bench", "harness bench_done payload differs from WAL")
            bench_payload = _mapping(
                bench.get("payload"), gate="cross-binding-bench",
                label="WAL bench_done.payload",
            )
            if "bench_wall_s" not in bench_payload:
                _fail(
                    "cross-binding-bench",
                    "WAL bench_done.payload is missing bench_wall_s",
                )
            expected_wall = bench_payload["bench_wall_s"]
            if (
                isinstance(expected_wall, bool)
                or not isinstance(expected_wall, (int, float))
                or not math.isfinite(float(expected_wall))
                or float(expected_wall) < 0.0
            ):
                _fail("cross-binding-bench", "WAL bench_wall_s is invalid")
            if generation.get("bench_wall_seconds") != expected_wall:
                _fail("cross-binding-bench", "generation bench_wall_seconds differs from WAL")
    if seen != set(by_attempt):
        _fail("cross-binding-bench", "a WAL bench record has no supervisor harness")


def _cross_binding_source_bindings(
    *, report: Mapping[str, Any], run_root: Path, campaign_root: Path,
    campaign_id: str, cell_index: int,
    proposal_rows: Sequence[Mapping[str, Any]],
    verified_bytes: Mapping[str, bytes], records: list[wal.WalRecord],
    lock_raw: bytes,
) -> dict[str, Any]:
    from . import source_digest

    trial_id = report.get("trial_id")
    try:
        decoded_lock = campaign_lock.decode_campaign_lock_bytes(lock_raw)
    except campaign_lock.CampaignLockCodecError as exc:
        raise AutonomousTrialCompletenessError(
            f"[cross-binding-axis] trial={trial_id!r} value='undecodable' "
            f"path={campaign_root / 'campaign.lock'} cannot be decoded"
        ) from exc
    search_config = decoded_lock.identity.get("search_config")
    axis = search_config.get("axis") if isinstance(search_config, Mapping) else None
    if axis != "silo-backoff-trigger-gating":
        _fail(
            "cross-binding-axis",
            f"trial={trial_id!r} value={axis!r} "
            f"path={campaign_root / 'campaign.lock'} search_config.axis differs",
        )
    try:
        bindings_by_attempt = wal.validate_trigger_bindings(
            records, campaign_lock=decoded_lock, require_build_start=True,
        )
    except wal.AttemptTopologyError as exc:
        raise AutonomousTrialCompletenessError(
            f"[cross-binding-attempt] trial={trial_id!r} value={str(exc)!r} "
            f"path={campaign_root / 'runs/wal.jsonl'} trigger topology is invalid"
        ) from exc

    starts_by_attempt: dict[str, wal.WalRecord] = {}
    benches_by_attempt: dict[str, list[wal.WalRecord]] = {}
    raw_source_bearing_attempts: list[str] = []
    for record in records:
        attempt_id = record.payload.get("build_attempt_id")
        if record.stage == trigger_gate_binding.WAL_RECORD_STAGE:
            try:
                raw_binding = trigger_gate_binding.validate_record(
                    record.payload.get("trigger_gate_binding"),
                    require_source=False,
                )
            except trigger_gate_binding.TriggerGateBindingError as exc:
                raise AutonomousTrialCompletenessError(
                    f"[cross-binding-attempt] trial={trial_id!r} "
                    f"value={attempt_id!r} "
                    f"path={campaign_root / 'runs/wal.jsonl'} "
                    "contains an invalid raw trigger binding"
                ) from exc
            if raw_binding.source is not None:
                if type(attempt_id) is not str or not attempt_id:
                    _fail(
                        "cross-binding-attempt",
                        f"trial={trial_id!r} value={attempt_id!r} "
                        f"path={campaign_root / 'runs/wal.jsonl'} "
                        "source-bearing trigger attempt id is invalid",
                    )
                raw_source_bearing_attempts.append(attempt_id)
        if record.stage == "build_start" and isinstance(attempt_id, str):
            starts_by_attempt[attempt_id] = record
        elif record.stage == "bench_done" and isinstance(attempt_id, str):
            benches_by_attempt.setdefault(attempt_id, []).append(record)
    validated_source_bearing_attempts = [
        attempt_id for attempt_id, binding in bindings_by_attempt.items()
        if binding.source is not None
    ]
    if Counter(raw_source_bearing_attempts) != Counter(
        validated_source_bearing_attempts
    ):
        _fail(
            "cross-binding-attempt",
            f"trial={trial_id!r} "
            f"value={{'raw_source_bearing': {raw_source_bearing_attempts!r}, "
            f"'validated_starts': {validated_source_bearing_attempts!r}}} "
            f"path={campaign_root / 'runs/wal.jsonl'} "
            "source-bearing trigger attempts are not fully classified",
        )

    cell_proposals = [
        dict(row) for row in proposal_rows if row.get("cell_index") == cell_index
    ]
    if not cell_proposals:
        _fail(
            "cross-binding-proposal",
            f"trial={trial_id!r} value=0 path=report.cells[{cell_index}].generations "
            "contains no proposal bytes",
        )
    by_proposal_path = {
        row["proposal_path"]: row for row in cell_proposals
    }
    if len(by_proposal_path) != len(cell_proposals):
        _fail(
            "cross-binding-proposal",
            f"trial={trial_id!r} value='duplicate' "
            f"path=report.cells[{cell_index}].generations proposal paths repeat",
        )

    provenance_rows = _cross_binding_provenance_rows(
        report=report, run_root=run_root, campaign_root=campaign_root,
        verified_bytes=verified_bytes,
    )
    proposal_path_counts = Counter(row["proposal_path"] for row in cell_proposals)
    provenance_path_counts = Counter(row["proposal_path"] for row in provenance_rows)
    if provenance_path_counts != proposal_path_counts:
        _fail(
            "cross-binding-attempt",
            f"trial={trial_id!r} "
            f"value={{'proposal': {dict(proposal_path_counts)!r}, "
            f"'provenance': {dict(provenance_path_counts)!r}}} "
            f"path={campaign_root / 'reports/p3_s8a_trigger_loop_provenance.json'} "
            "does not bind every proposal exactly once",
        )
    provenance_by_path = {
        row["proposal_path"]: row for row in provenance_rows
    }

    source_artifacts: dict[str, tuple[str, bytes]] = {}
    for path, raw in verified_bytes.items():
        if not path.startswith(f"{source_digest.SOURCE_BINDING_DIRECTORY}/"):
            continue
        relative = Path(path)
        if (
            len(relative.parts) != 2
            or not relative.name.endswith(".preimage")
        ):
            _fail(
                "cross-binding-source-artifact",
                f"trial={trial_id!r} value={path!r} "
                f"path={campaign_root / path} is not a canonical source preimage path",
            )
        proposal_sha256 = relative.name.removesuffix(".preimage")
        try:
            expected_path = source_digest.source_preimage_artifact_relative_path(
                proposal_sha256
            )
        except ValueError as exc:
            raise AutonomousTrialCompletenessError(
                f"[cross-binding-source-artifact] trial={trial_id!r} "
                f"value={proposal_sha256!r} path={campaign_root / path} is invalid"
            ) from exc
        if expected_path != path or proposal_sha256 in source_artifacts:
            _fail(
                "cross-binding-source-artifact",
                f"trial={trial_id!r} value={path!r} path={campaign_root / path} "
                "is duplicated or non-canonical",
            )
        source_artifacts[proposal_sha256] = (path, raw)

    proposal_digests = {row["proposal_sha256"] for row in cell_proposals}
    extra_artifacts = set(source_artifacts) - proposal_digests
    if extra_artifacts:
        extra = sorted(extra_artifacts)
        _fail(
            "cross-binding-source-artifact",
            f"trial={trial_id!r} value={extra!r} "
            f"path={campaign_root / source_digest.SOURCE_BINDING_DIRECTORY} "
            "contains source preimages with no proposal",
        )

    provenance_attempts: list[str] = []
    for row in provenance_rows:
        attempt_id = row["build_attempt_id"]
        variant = row["variant"]
        if attempt_id is None and variant is None:
            continue
        if type(attempt_id) is not str or not attempt_id:
            _fail(
                "cross-binding-attempt",
                f"trial={trial_id!r} value={attempt_id!r} "
                f"path=provenance.entries[{row['entry_key']!r}].build_attempt_id "
                "is invalid",
            )
        if type(variant) is not str or not variant:
            _fail(
                "cross-binding-attempt",
                f"trial={trial_id!r} value={variant!r} "
                f"path=provenance.entries[{row['entry_key']!r}].variant is invalid",
            )
        provenance_attempts.append(attempt_id)
    if Counter(provenance_attempts) != Counter(bindings_by_attempt.keys()):
        _fail(
            "cross-binding-attempt",
            f"trial={trial_id!r} "
            f"value={{'provenance': {provenance_attempts!r}, "
            f"'wal': {sorted(bindings_by_attempt)!r}}} "
            f"path={campaign_root / 'runs/wal.jsonl'} "
            "proposal provenance and trigger attempts are not bijective",
        )

    receipt_rows: list[dict[str, Any]] = []
    built_and_benched = 0
    for proposal in sorted(
        cell_proposals,
        key=lambda row: (row["generation"], row["proposal_path"]),
    ):
        provenance = provenance_by_path[proposal["proposal_path"]]
        attempt_id = provenance["build_attempt_id"]
        artifact = source_artifacts.get(proposal["proposal_sha256"])
        artifact_path = artifact[0] if artifact is not None else None
        preimage_sha256 = None
        assignment_count = None

        source_status = "not-attempted"
        execution_status = "not-started"
        variant = provenance["variant"]
        if attempt_id is not None:
            binding = bindings_by_attempt[attempt_id]
            start = starts_by_attempt.get(attempt_id)
            if start is None:
                _fail(
                    "cross-binding-attempt",
                    f"trial={trial_id!r} value={attempt_id!r} "
                    f"path={campaign_root / 'runs/wal.jsonl'} has no build_start",
                )
            expected_commitment = trigger_gate_binding.commitment(binding)
            if (
                provenance["trigger_gate_binding_commitment"]
                != expected_commitment
                or provenance["variant"] != start.variant
            ):
                _fail(
                    "cross-binding-attempt",
                    f"trial={trial_id!r} "
                    f"value={{'attempt': {attempt_id!r}, 'variant': {variant!r}}} "
                    f"path=provenance.entries[{provenance['entry_key']!r}] "
                    "differs from the verified WAL binding",
                )
            if binding.predicate_sha256 != proposal["predicate_sha256"]:
                _fail(
                    "cross-binding-predicate",
                    f"trial={trial_id!r} "
                    f"value={{'proposal': {proposal['predicate_sha256']!r}, "
                    f"'wal': {binding.predicate_sha256!r}}} "
                    f"path={proposal['proposal_path']} predicate digest differs",
                )
            if binding.mask != proposal["mask"]:
                _fail(
                    "cross-binding-predicate",
                    f"trial={trial_id!r} "
                    f"value={{'proposal': {proposal['mask']!r}, "
                    f"'wal': {binding.mask!r}}} path={proposal['proposal_path']} "
                    "predicate mask differs",
                )
            if binding.source is None:
                source_status = "pre-source-abort"
                execution_status = "aborted"
                if artifact is not None:
                    _fail(
                        "cross-binding-source-artifact",
                        f"trial={trial_id!r} value={artifact_path!r} "
                        f"path={campaign_root / artifact_path} pre-source abort "
                        "must not claim a source preimage",
                    )
                if benches_by_attempt.get(attempt_id):
                    _fail(
                        "cross-binding-build",
                        f"trial={trial_id!r} value={attempt_id!r} "
                        f"path={campaign_root / 'runs/wal.jsonl'} "
                        "has a bench without source binding",
                    )
            else:
                if artifact is None:
                    _fail(
                        "cross-binding-source-artifact",
                        f"trial={trial_id!r} value={proposal['proposal_sha256']!r} "
                        f"path={campaign_root / source_digest.source_preimage_artifact_relative_path(proposal['proposal_sha256'])} "
                        "is required for a source-bearing trigger attempt",
                    )
                preimage_sha256 = hashlib.sha256(artifact[1]).hexdigest()
                assignment_count = _cross_binding_preimage_assignment_count(
                    report=report, preimage=artifact[1],
                    expected_assignment=proposal["predicate_assignment"],
                    path=str(campaign_root / artifact_path),
                )
                source = binding.source
                source_status = "consumer-bound"
                if preimage_sha256 != source.source_bytes_sha256:
                    _fail(
                        "cross-binding-source-digest",
                        f"trial={trial_id!r} "
                        f"value={{'preimage': {preimage_sha256!r}, "
                        f"'source_bytes_sha256': {source.source_bytes_sha256!r}}} "
                        f"path={campaign_root / artifact_path} E2 digest equality differs",
                    )
                if (
                    preimage_sha256 != source.src_token
                    or source.src_token != start.payload.get("src_token")
                ):
                    _fail(
                        "cross-binding-source-identity",
                        f"trial={trial_id!r} "
                        f"value={{'preimage': {preimage_sha256!r}, "
                        f"'src_token': {source.src_token!r}, "
                        f"'build_start.src_token': {start.payload.get('src_token')!r}}} "
                        f"path={campaign_root / artifact_path} E3 identity equality differs",
                    )
                benches = benches_by_attempt.get(attempt_id, [])
                if len(benches) > 1:
                    _fail(
                        "cross-binding-build",
                        f"trial={trial_id!r} value={len(benches)!r} "
                        f"path={campaign_root / 'runs/wal.jsonl'} attempt={attempt_id!r} "
                        "has multiple bench records",
                    )
                if benches:
                    harness = _mapping(
                        proposal["harness"], gate="cross-binding-build",
                        label=f"generation {proposal['generation']}.harness",
                    )
                    harness_records = _mapping(
                        harness.get("records"), gate="cross-binding-build",
                        label=f"generation {proposal['generation']}.harness.records",
                    )
                    harness_bench = _mapping(
                        harness_records.get("bench_done"), gate="cross-binding-build",
                        label=f"generation {proposal['generation']}.harness.records.bench_done",
                    )
                    if (
                        harness.get("variant") != start.variant
                        or harness_bench.get("build_attempt_id") != attempt_id
                    ):
                        _fail(
                            "cross-binding-build",
                            f"trial={trial_id!r} value={attempt_id!r} "
                            f"path=report.cells[{cell_index}].generations[{proposal['generation_index']}].harness "
                            "does not bind the built-and-benched attempt",
                        )
                    execution_status = "built-and-benched"
                    built_and_benched += 1
                else:
                    execution_status = "aborted"

        receipt_rows.append({
            "campaign_id": campaign_id,
            "generation": proposal["generation"],
            "proposal_path": proposal["proposal_path"],
            "proposal_sha256": proposal["proposal_sha256"],
            "wire": proposal["wire"],
            "mask": proposal["mask"],
            "predicate_sha256": proposal["predicate_sha256"],
            "source_preimage_path": artifact_path,
            "source_preimage_sha256": preimage_sha256,
            "predicate_assignment_count": assignment_count,
            "variant": variant,
            "build_attempt_id": attempt_id,
            "attempt_outcome": provenance["outcome"],
            "source_binding_status": source_status,
            "build_execution_status": execution_status,
        })

    if built_and_benched < 1:
        _fail(
            "cross-binding-build-population",
            f"trial={trial_id!r} value={built_and_benched!r} "
            f"path=report.cells[{cell_index}].generations materialized build cell "
            "requires at least one built-and-benched proposal",
        )
    classified_artifacts = {
        row["source_preimage_path"]
        for row in receipt_rows if row["source_preimage_path"] is not None
    }
    expected_artifacts = {path for path, _raw in source_artifacts.values()}
    if classified_artifacts != expected_artifacts:
        _fail(
            "cross-binding-source-artifact",
            f"trial={trial_id!r} "
            f"value={{'classified': {sorted(classified_artifacts)!r}, "
            f"'expected': {sorted(expected_artifacts)!r}}} "
            f"path={campaign_root / source_digest.SOURCE_BINDING_DIRECTORY} "
            "source preimage classification is incomplete",
        )
    return {
        "predicate_rederivation_proof_kind": "consumer-rederived",
        "source_preimage_digest_proof_kind": "consumer-rederived",
        "predicate_source_association_proof_kind": (
            "consumer-rederived-textual-materialization"
        ),
        "attempt_topology_proof_kind": "producer-self-consistency",
        "build_execution_proof_kind": "producer-execution-contract",
        "built_and_benched_count": built_and_benched,
        "classified_source_preimage_artifact_count": len(source_artifacts),
        "rows": receipt_rows,
    }


def _cross_binding_no_build_receipt(
    report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    logical_ids: list[str] = []
    for event in events:
        if not isinstance(event, Mapping):
            continue
        if event.get("event") == "role-attempt":
            invocation = event.get("invocation_id")
            if isinstance(invocation, str):
                logical_ids.append(invocation)
    receipt: dict[str, Any] = {
        "schema_version": S8C_CROSS_BINDING_SCHEMA_VERSION,
        "trial_id": report.get("trial_id"),
        "mode": "no-build",
        "cells": len(report.get("cells", []))
        if isinstance(report.get("cells"), list) else None,
        "journal_role_attempt_ids": sorted(logical_ids),
        "bindings": {},
        "unbound_fields": list(S8C_CROSS_BINDING_FIELDS),
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        _canonical_bytes(receipt)
    ).hexdigest()
    return receipt


def _cross_binding_failure_receipt(
    report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    logical_ids = sorted(
        event["invocation_id"]
        for event in events
        if isinstance(event, Mapping)
        and event.get("event") == "role-attempt"
        and isinstance(event.get("invocation_id"), str)
    )
    receipt: dict[str, Any] = {
        "schema_version": S8C_CROSS_BINDING_SCHEMA_VERSION,
        "trial_id": report.get("trial_id"),
        "mode": "build-failure",
        "cells": len(report.get("cells", [])),
        "journal_role_attempt_ids": logical_ids,
        "bindings": {},
        "unbound_fields": list(S8C_CROSS_BINDING_FIELDS),
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        _canonical_bytes(receipt)
    ).hexdigest()
    return receipt


def verify_s8c_cross_binding(
    *,
    report: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    run_root: Path,
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Re-read every S8C build binding and return one sealed projection."""
    report = _mapping(report, gate="cross-binding", label="report")
    do_build = report.get("do_build")
    if type(do_build) is not bool:
        _fail("cross-binding", "report.do_build is not a bool")
    if do_build is False:
        return _cross_binding_no_build_receipt(report, events)

    run_root = Path(run_root).resolve(strict=True)
    if not run_root.is_dir():
        _fail("cross-binding", "run_root is not a directory")
    cells = _list(report.get("cells"), gate="cross-binding", label="report.cells")
    if not cells:
        _fail("cross-binding", "build report must contain at least one cell")
    campaign_roots: list[Path | None] = []
    normalized_cells: list[Mapping[str, Any]] = []
    for index, raw_cell in enumerate(cells):
        cell = _mapping(raw_cell, gate="cross-binding", label=f"cells[{index}]")
        if is_exact_campaignless_failure_fallback_cell(cell):
            campaign_roots.append(None)
            normalized_cells.append(cell)
            continue
        campaign_root_value = cell.get("campaign_root")
        if type(campaign_root_value) is not str or not campaign_root_value:
            _fail("cross-binding", f"cells[{index}].campaign_root is required")
        declared_campaign_root = Path(campaign_root_value)
        campaign_root = (
            declared_campaign_root
            if declared_campaign_root.is_absolute()
            else run_root / declared_campaign_root
        ).resolve()
        if not campaign_root.is_dir():
            _fail("cross-binding", f"cells[{index}].campaign_root is not a directory")
        campaign_roots.append(campaign_root)
        normalized_cells.append(cell)
    materialized_roots = [root for root in campaign_roots if root is not None]
    if not materialized_roots:
        return _cross_binding_failure_receipt(report, events)
    driver = report.get("generation_driver")
    if driver != _STANDARD_GENERATION_DRIVER:
        _fail(
            "cross-binding-driver",
            f"trial={report.get('trial_id')!r} value={driver!r} "
            "path=report.generation_driver materialized build cells require "
            f"the standard driver {_STANDARD_GENERATION_DRIVER!r}",
        )
    derived_output_root = materialized_roots[0].parent.parent
    if any(root.parent.parent != derived_output_root for root in materialized_roots):
        _fail("cross-binding", "build cells do not share one output root")
    if output_root is not None:
        supplied_output_root = Path(output_root).resolve(strict=True)
        if supplied_output_root != derived_output_root:
            _fail("cross-binding", "campaign output root differs from cell campaign roots")
        derived_output_root = supplied_output_root

    role_rows: list[dict[str, Any]] = []
    for event in _cross_binding_role_events(events):
        invocation_id = event["invocation_id"]
        artifacts = _mapping(
            event.get("provider_artifacts"), gate="cross-binding-provider",
            label=f"role {invocation_id}.provider_artifacts",
        )
        if set(artifacts) != _PROVIDER_ARTIFACT_KEYS:
            _fail("cross-binding-provider", "provider_artifacts exact keys differ")
        raw_path, _raw = read_and_verify_bytes(
            event.get("raw_response_path"),
            root=run_root,
            expected_sha256=event.get("raw_response_sha256"),
            gate="cross-binding-raw",
            label=f"role {invocation_id} raw response",
        )
        payload_path, payload_raw = read_and_verify_bytes(
            artifacts["payload_path"],
            root=run_root,
            expected_sha256=event.get("provider_payload_sha256"),
            gate="cross-binding-provider",
            label=f"role {invocation_id} provider payload",
        )
        envelope_path, _envelope_raw = read_and_verify_bytes(
            artifacts["envelope_path"],
            root=run_root,
            expected_sha256=event.get("provider_envelope_sha256"),
            gate="cross-binding-provider",
            label=f"role {invocation_id} provider envelope",
        )
        payload_sha256 = hashlib.sha256(payload_raw).hexdigest()
        if event.get("input_payload_sha256") != payload_sha256:
            _fail(
                "cross-binding-provider",
                "input_payload_sha256 differs from provider payload bytes",
            )
        role_rows.append({
            "invocation_id": invocation_id,
            "input_payload_sha256": event.get("input_payload_sha256"),
            "raw_response_path": _cross_binding_relative_path(
                raw_path, run_root, label="raw response",
            ),
            "raw_response_sha256": event.get("raw_response_sha256"),
            "provider_payload_sha256": event.get("provider_payload_sha256"),
            "provider_envelope_sha256": event.get("provider_envelope_sha256"),
            "provider_payload_path": _cross_binding_relative_path(
                payload_path, run_root, label="provider payload",
            ),
            "provider_envelope_path": _cross_binding_relative_path(
                envelope_path, run_root, label="provider envelope",
            ),
        })
    role_rows.sort(key=lambda item: item["invocation_id"])
    role_bindings = {
        field: [row[field] for row in role_rows]
        for field in (
            "input_payload_sha256",
            "raw_response_path",
            "raw_response_sha256",
            "provider_payload_sha256",
            "provider_envelope_sha256",
        )
    }
    proposal_paths, proposal_digests, proposal_rows = _cross_binding_proposals(
        report, run_root=run_root,
    )
    build_records: list[dict[str, Any]] = []
    bench_records: list[dict[str, Any]] = []
    artifact_bindings: list[dict[str, Any]] = []
    source_bindings: list[dict[str, Any]] = []
    admission_bindings: list[dict[str, Any]] = []
    proposal_source_bindings: list[dict[str, Any]] = []

    for index, (cell, campaign_root) in enumerate(
        zip(normalized_cells, campaign_roots, strict=True)
    ):
        if campaign_root is None:
            admission_bindings.append({
                "campaign_id": None,
                "cell": dict(cell.get("admission_decision", {})),
                "layer3": None,
                "independent": None,
            })
            continue
        campaign_id = cell.get("campaign_id")
        if type(campaign_id) is not str or not campaign_id:
            _fail("cross-binding", f"cells[{index}].campaign_id is invalid")
        persisted_path = campaign_root / "reports" / "layer3_report.json"
        if persisted_path.is_symlink():
            _fail("cross-binding", "layer3 report is a symlink")
        if not persisted_path.exists():
            if not is_exact_cell_admission_failure_decision(
                cell.get("admission_decision")
            ):
                _fail("cross-binding", "build cell has no persisted layer3 report")
            _fail(
                "cross-binding-build-population",
                f"trial={report.get('trial_id')!r} value=0 "
                f"path={persisted_path} materialized build cell has no "
                "built-and-benched proposal",
            )
        _cross_binding_regular_path(
            persisted_path, label=f"cells[{index}] layer3 report",
        )
        persisted_path, persisted_raw = _bound_regular_bytes(
            "reports/layer3_report.json", run_root=campaign_root,
            gate="cross-binding-layer3", label=f"cells[{index}] layer3 report",
        )
        persisted = _mapping(
            _decode_json(persisted_raw, label=f"cells[{index}] layer3 report"),
            gate="cross-binding-layer3",
            label=f"cells[{index}] layer3 report",
        )
        refs, verified_artifact_bytes = _cross_binding_artifact_refs(
            persisted, campaign_root=campaign_root, persisted_path=persisted_path,
        )
        artifact_paths = {ref["path"] for ref in refs}
        whiteboard = _cross_binding_whiteboard(
            campaign_root, artifact_paths=artifact_paths,
            verified_bytes=verified_artifact_bytes,
        )
        cell_decision = _mapping(
            cell.get("admission_decision"), gate="cross-binding-admission",
            label=f"cells[{index}].admission_decision",
        )
        persisted_decision = _mapping(
            persisted.get("admission_decision"), gate="cross-binding-admission",
            label="layer3_report.admission_decision",
        )
        if (
            dict(cell_decision) != dict(persisted_decision)
        ):
            _fail("cross-binding-admission", "cell/layer3/independent admission decisions differ")
        _lock_path, _lock_raw = read_and_verify_bytes(
            "campaign.lock", root=campaign_root,
            expected_sha256=persisted_decision["campaign_lock_sha256"],
            gate="cross-binding-admission", label="campaign.lock",
        )
        _wal_path, _wal_raw = read_and_verify_bytes(
            "runs/wal.jsonl", root=campaign_root,
            expected_sha256=persisted_decision["wal_sha256"],
            gate="cross-binding-admission", label="campaign WAL",
        )
        try:
            certified_view = require_admitted_campaign(
                campaign_root,
                purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
            )
        except ArtifactAdmissionError as exc:
            raise AutonomousTrialCompletenessError(
                "[cross-binding-admission] independent campaign admission validation failed"
            ) from exc
        expected_decision = certified_view.decision.as_receipt()
        if (
            expected_decision.get("campaign_lock_sha256")
            != hashlib.sha256(_lock_raw).hexdigest()
            or expected_decision.get("wal_sha256")
            != hashlib.sha256(_wal_raw).hexdigest()
        ):
            _fail(
                "cross-binding-admission",
                "admission reread bytes differ from verified campaign bytes",
            )
        if (
            dict(cell_decision) != dict(expected_decision)
            or dict(persisted_decision) != dict(expected_decision)
        ):
            _fail("cross-binding-admission", "cell/layer3/independent admission decisions differ")
        records, truncated = _cross_binding_verified_wal_records(_wal_raw)
        if truncated:
            _fail("cross-binding-wal", "campaign WAL has a truncated tail")
        if not records:
            _fail("cross-binding-wal", "campaign WAL is empty")
        raw_records = [_cross_binding_wal_dict(record) for record in records]
        proposal_source_binding = _cross_binding_source_bindings(
            report=report,
            run_root=run_root,
            campaign_root=campaign_root,
            campaign_id=campaign_id,
            cell_index=index,
            proposal_rows=proposal_rows,
            verified_bytes=verified_artifact_bytes,
            records=records,
            lock_raw=_lock_raw,
        )
        proposal_source_bindings.append(proposal_source_binding)
        build_stages = frozenset({
            "build_start",
            "build_done",
            "verify_done",
            "commit",
            "abort",
        })
        bench_stages = frozenset({"bench_done"})
        build_side = [
            record for record in raw_records if record["stage"] in build_stages
        ]
        bench_side = [
            record for record in raw_records if record["stage"] in bench_stages
        ]
        normalized_records = _cross_binding_layer3_wal_records(raw_records)
        if Counter(
            canonical_record_ref("wal", record) for record in build_side + bench_side
        ) != Counter(
            canonical_record_ref("wal", record) for record in normalized_records
        ):
            _fail(
                "cross-binding-wal",
                "build/bench WAL projection does not cover all layer3 records",
            )

        persisted_primary: list[Mapping[str, Any]] = []
        for row in _list(
            persisted.get("variants"), gate="cross-binding-wal",
            label="layer3_report.variants",
        ):
            variant_row = _mapping(row, gate="cross-binding-wal", label="variant row")
            for event in _list(
                variant_row.get("events"), gate="cross-binding-wal",
                label="variant.events",
            ):
                persisted_primary.append(
                    _mapping(event, gate="cross-binding-wal", label="variant event")
                )
        non_binding = _cross_binding_layer3_wal_records(raw_records)
        if Counter(
            canonical_record_ref("wal", record) for record in persisted_primary
        ) != Counter(canonical_record_ref("wal", record) for record in non_binding):
            _fail("cross-binding-wal", "layer3 variants do not cover the campaign WAL")
        expected_runs = [
            _layer3_report._view_row(record)
            for record in sorted(
                non_binding,
                key=lambda item: (
                    item["ts"], canonical_record_ref("wal", item),
                ),
            )
            if record["stage"] == "bench_done"
        ]
        persisted_runs = _list(
            persisted.get("runs"), gate="cross-binding-bench",
            label="layer3_report.runs",
        )
        if _canonical_bytes(persisted_runs) != _canonical_bytes(expected_runs):
            _fail("cross-binding-bench", "layer3 runs differ from WAL bench projection")
        expected_source = Counter(
            canonical_record_ref("wal", record) for record in non_binding
        )
        expected_source.update(canonical_record_ref("wb", item) for item in whiteboard)
        persisted_source = _list(
            persisted.get("source_refs"), gate="cross-binding-source",
            label="layer3_report.source_refs",
        )
        if Counter(persisted_source) != expected_source:
            _fail("cross-binding-source", "layer3 source_refs differ from WAL/loop-state refs")
        _cross_binding_supervisor_records(
            {"cells": [cell]}, bench_records=bench_side,
            aborted_variants={
                row["variant"]
                for row in proposal_source_binding["rows"]
                if row["build_execution_status"] == "aborted"
                and isinstance(row["variant"], str)
            },
        )
        build_records.append({
            "campaign_id": campaign_id,
            "records": build_side,
        })
        bench_records.append({
            "campaign_id": campaign_id,
            "records": expected_runs,
        })
        artifact_bindings.append({
            "campaign_id": campaign_id,
            "refs": refs,
        })
        source_bindings.append({
            "campaign_id": campaign_id,
            "refs": sorted(persisted_source),
        })
        admission_bindings.append({
            "campaign_id": campaign_id,
            "cell": dict(cell_decision),
            "layer3": dict(persisted_decision),
            "independent": dict(expected_decision),
        })

    bindings: dict[str, Any] = {
        **role_bindings,
        "proposal_path": proposal_paths,
        "proposal_sha256": proposal_digests,
        "build_records": build_records,
        "bench_records": bench_records,
        "artifact_refs": artifact_bindings,
        "source_refs": source_bindings,
        "admission_decision": admission_bindings,
        "proposal_build_source_bindings": proposal_source_bindings,
    }
    if set(bindings) != set(S8C_CROSS_BINDING_FIELDS):
        _fail("cross-binding", "cross-binding field set is incomplete")
    receipt: dict[str, Any] = {
        "schema_version": S8C_CROSS_BINDING_SCHEMA_VERSION,
        "trial_id": report.get("trial_id"),
        "mode": "build",
        "bindings": bindings,
        "unbound_fields": [],
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        _canonical_bytes(receipt)
    ).hexdigest()
    return receipt


def assert_legacy_workload_profile_source(
    *, source_record: Mapping[str, Any],
    producer_entries: Mapping[str, Mapping[str, Any]],
    repository_root: Path,
) -> None:
    """Independently reload and reproject the legacy formal source."""
    try:
        legacy = s8b_ratified_freeze.load_legacy_freeze(repository_root)
    except s8b_ratified_freeze.RatifiedFreezeError as exc:
        raise AutonomousTrialCompletenessError(
            f"[workload-profile-source] legacy source unavailable: {exc.reason}"
        ) from exc
    expected_source = {
        "schema_version": "p3-workload-profile-source/v1",
        "selector": "formal-holdout-legacy-v1",
        "source": "legacy-v1",
        "loader": "s8b_ratified_freeze.load_legacy_freeze",
        "path": s8b_ratified_freeze.V1_FREEZE_PATH,
        "sha256": legacy.sha256,
    }
    if (
        frozenset(source_record) != frozenset(expected_source)
        or _canonical_bytes(dict(source_record)) != _canonical_bytes(expected_source)
    ):
        _fail("workload-profile-source", "source record differs from fresh legacy load")
    legacy_holdouts = legacy.document.get("holdouts")
    if not isinstance(legacy_holdouts, Mapping) or set(legacy_holdouts) != set(
        s8b_holdout_freeze.HOLDOUTS
    ):
        _fail("workload-profile-source", "legacy holdout universe differs")

    def projection(entry: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return {
                "candidate_id": entry["candidate_id"],
                "records": entry["records"],
                "threads": entry["threads"],
                "ycsb": dict(entry["ycsb"]),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise AutonomousTrialCompletenessError(
                "[workload-profile-source] four-key projection is invalid"
            ) from exc

    for name, module_entry in s8b_holdout_freeze.HOLDOUTS.items():
        producer_entry = producer_entries.get(name)
        legacy_entry = legacy_holdouts.get(name)
        if not isinstance(producer_entry, Mapping) or not isinstance(
            legacy_entry, Mapping
        ):
            _fail("workload-profile-source", "formal authority entry is absent")
        values = (
            projection(module_entry),
            projection(legacy_entry),
            projection(producer_entry),
        )
        if len({_canonical_bytes(value) for value in values}) != 1:
            _fail("workload-profile-source", "four-key authority bytes differ")


def _fresh_layer3_for_comparison(
    *, campaign_root: Path, persisted_path: Path,
    persisted: Mapping[str, Any], output_root: Path,
) -> Mapping[str, Any]:
    meta = persisted.get("meta")
    generated_from_head = (
        meta.get("generated_from_head") if isinstance(meta, Mapping) else None
    )
    if (
        not isinstance(generated_from_head, str)
        or _GIT_OBJECT_ID_RE.fullmatch(generated_from_head) is None
    ):
        _fail("campaign-chain", "persisted layer3 generated_from_head is not a git object ID")
    try:
        fresh = _layer3_report.build_report(
            campaign_root,
            generated_from_head="0" * 40,
            output_root=output_root,
        )
    except _layer3_report.Layer3ReportError as exc:
        raise AutonomousTrialCompletenessError(
            f"[campaign-chain] fresh layer3 rebuild failed: {exc}"
        ) from exc
    relative_persisted = persisted_path.relative_to(campaign_root).as_posix()
    artifacts = fresh.get("artifact_refs")
    if not isinstance(artifacts, list):
        _fail("campaign-chain", "fresh layer3 artifact_refs is not a list")
    fresh = dict(fresh)
    fresh["artifact_refs"] = [
        item for item in artifacts
        if not isinstance(item, Mapping) or item.get("path") != relative_persisted
    ]
    return fresh


def _layer3_comparison_projection(
    report: Mapping[str, Any], *, include_epoch: bool,
    include_verifier_assessment_basis: bool,
    include_current_verifier_conformance: bool,
) -> dict[str, Any]:
    """Normalize volatile fields and the allowed legacy schema omissions.

    Layer3 v3 documents written before T-817 have no
    ``campaign_verifier_epoch``.  They remain readable, while a document that
    does carry the field must compare it exactly with the fresh rebuild.
    Historical documents written before D1163 have an exact five-key epoch;
    only their fresh-side assessment marker is omitted for compatibility.
    Historical documents written before D1245 have no current verifier
    conformance marker; a marker that is present must still compare exactly.
    """
    normalized = dict(report)
    normalized.setdefault("acceptance_receipt", None)
    normalized.setdefault("certifying_input", False)
    normalized.setdefault("knowledge_provenance", None)
    if not include_epoch:
        normalized.pop("campaign_verifier_epoch", None)
    elif not include_verifier_assessment_basis:
        epoch = normalized.get("campaign_verifier_epoch")
        if isinstance(epoch, Mapping):
            normalized_epoch = dict(epoch)
            normalized_epoch.pop("verifier_assessment_basis", None)
            normalized["campaign_verifier_epoch"] = normalized_epoch
    if not include_current_verifier_conformance:
        normalized.pop("current_verifier_conformance", None)
    meta = _mapping(
        report.get("meta"), gate="campaign-chain", label="layer3 report.meta",
    )
    normalized_meta = dict(meta)
    normalized_meta.pop("generated_from_head", None)
    normalized["meta"] = normalized_meta
    return normalized


def _epoch_projection(
    epoch: Any, *, verifier_assessment_basis: str | None = None,
) -> dict[str, Any]:
    projection = {
        "campaign_verifier_epoch": epoch.campaign_verifier_epoch,
        "state": epoch.state,
        "reason_code": epoch.reason_code,
        "identity_scope": epoch.identity_scope,
        "excluded_scope": epoch.excluded_scope,
    }
    if verifier_assessment_basis is not None:
        projection["verifier_assessment_basis"] = verifier_assessment_basis
    return projection


def _require_compatible_layer3_epoch(
    report: Mapping[str, Any], *, expected: Mapping[str, Any], label: str,
) -> None:
    """Validate a present epoch exactly; absence is the sole legacy projection."""
    if "campaign_verifier_epoch" not in report:
        return
    epoch = _mapping(
        report.get("campaign_verifier_epoch"), gate="campaign-chain",
        label=f"{label}.campaign_verifier_epoch",
    )
    epoch_keys = frozenset(epoch)
    accepted_keys = {_CAMPAIGN_VERIFIER_EPOCH_KEYS}
    if report.get("certifying_input", False) is not True:
        accepted_keys.add(_HISTORICAL_CAMPAIGN_VERIFIER_EPOCH_KEYS)
    if epoch_keys not in accepted_keys:
        _fail("campaign-chain", f"{label} campaign verifier epoch exact keys differ")
    if _canonical_bytes(epoch) != _canonical_bytes(expected):
        _fail("campaign-chain", f"{label} campaign verifier epoch differs from validator")


def _require_exact_layer3_admission_decision(
    report: Mapping[str, Any], *, expected: Mapping[str, Any], label: str,
) -> Mapping[str, Any]:
    """Validate Layer3's detached decision independently of a fresh Layer3 rebuild."""
    report = _mapping(report, gate="campaign-chain", label=label)
    decision = _mapping(
        report.get("admission_decision"), gate="campaign-chain",
        label=f"{label}.admission_decision",
    )
    if set(decision) != _ADMISSION_DECISION_KEYS:
        _fail("campaign-chain", f"{label} admission decision exact keys differ")
    validator = _mapping(
        decision.get("validator"), gate="campaign-chain",
        label=f"{label}.admission_decision.validator",
    )
    overlay = _mapping(
        decision.get("overlay"), gate="campaign-chain",
        label=f"{label}.admission_decision.overlay",
    )
    if set(validator) != _ADMISSION_VALIDATOR_KEYS:
        _fail("campaign-chain", f"{label} admission validator exact keys differ")
    if set(overlay) != _ADMISSION_OVERLAY_KEYS:
        _fail("campaign-chain", f"{label} admission overlay exact keys differ")
    if _canonical_bytes(decision) != _canonical_bytes(expected):
        _fail("campaign-chain", f"{label} admission decision differs from validator")
    return decision


def _require_certifying_layer3_admission(
    report: Mapping[str, Any], *, label: str,
) -> None:
    """certifying Layer3 入力は明示的に admitted のものだけへ閉じる。"""
    if report.get("certifying_input", False) is not True:
        return
    decision = _mapping(
        report.get("admission_decision"), gate="campaign-chain",
        label=f"{label}.admission_decision",
    )
    if decision.get("admission_status") != "admitted":
        _fail(
            "campaign-chain",
            f"{label} certifying input requires admission_status=admitted",
        )
    if "campaign_verifier_epoch" in report:
        epoch = _mapping(
            report.get("campaign_verifier_epoch"), gate="campaign-chain",
            label=f"{label}.campaign_verifier_epoch",
        )
        if epoch.get("state") != "E1":
            _fail(
                "campaign-chain",
                f"{label} certifying input requires verifier epoch E1",
            )


def assert_campaign_layer3_chain(
    *, report: Mapping[str, Any], output_root: Path,
) -> None:
    """Deep-compare each persisted layer3 report with a fresh WAL rebuild."""
    report = _mapping(report, gate="campaign-chain", label="report")
    cells = _list(report.get("cells"), gate="campaign-chain", label="report.cells")
    output_root = Path(output_root).resolve()
    seen: set[str] = set()
    producer = _producer_module()
    trial_id = report.get("trial_id")
    budget = report.get("generation_budget_per_workload")
    if not isinstance(trial_id, str) or not trial_id:
        _fail("campaign-chain", "report.trial_id is not a non-empty string")
    if type(budget) is not int or budget < 1:
        _fail("campaign-chain", "report generation budget is not a positive int")
    if budget > producer.MAX_APPROVED_GENERATIONS:
        _fail("campaign-chain", "report generation budget exceeds producer limit")
    launch_admission = _mapping(
        report.get("launch_admission"),
        gate="campaign-chain",
        label="report.launch_admission",
    )
    certifying_input = launch_admission.get("certifying")
    if type(certifying_input) is not bool:
        _fail("campaign-chain", "launch admission certifying is not a bool")
    failure_indices = [
        index
        for index, cell in enumerate(cells)
        if isinstance(cell, Mapping)
        and is_exact_cell_admission_failure_decision(
            cell.get("admission_decision")
        )
    ]
    if len(failure_indices) > 1:
        _fail("campaign-chain", "multiple cell admission failures are forbidden")
    if failure_indices and failure_indices != [len(cells) - 1]:
        _fail("campaign-chain", "cell admission failure must be the final cell")
    for index, raw_cell in enumerate(cells):
        cell = _mapping(raw_cell, gate="campaign-chain", label=f"cells[{index}]")
        failure_decision = is_exact_cell_admission_failure_decision(
            cell.get("admission_decision")
        )
        if LAYER3_ADMISSION_DIAGNOSIS_KEY in cell and (
            not failure_decision
            or not is_exact_layer3_admission_diagnosis(
                cell[LAYER3_ADMISSION_DIAGNOSIS_KEY]
            )
        ):
            _fail(
                "campaign-chain",
                f"cells[{index}] Layer-3 admission diagnosis is not exact",
            )
        if failure_decision and not _is_exact_pending_critic_disposition(
            cell.get("pending_critic_disposition")
        ):
            _fail("campaign-chain", f"cells[{index}] failure disposition is not exact")
        workload = cell.get("workload")
        if not isinstance(workload, str) or not workload:
            _fail("campaign-chain", f"cells[{index}].workload is invalid")
        failure_decision = is_exact_cell_admission_failure_decision(
            cell.get("admission_decision")
        )
        campaign_id = cell.get("campaign_id")
        campaign_root_value = cell.get("campaign_root")
        if campaign_id is None and campaign_root_value is None:
            if (
                failure_decision
                and is_exact_campaignless_failure_fallback_cell(cell)
            ):
                continue
            if failure_decision:
                _fail(
                    "campaign-chain",
                    f"cells[{index}] campaignless failure is not the exact producer fallback",
                )
            _fail("campaign-chain", f"cells[{index}] has no campaign identity")
        try:
            entry = producer.resolve_workload_entry(workload)
        except producer.AutonomousTrialError:
            _fail("campaign-chain", f"cells[{index}].workload is not producer-supported")
        if not isinstance(campaign_id, str) or not campaign_id or campaign_id in seen:
            _fail("campaign-chain", f"cells[{index}] campaign_id is invalid or duplicated")
        seen.add(campaign_id)
        workload_flags = entry.get("ycsb")
        if not isinstance(workload_flags, Mapping):
            _fail("campaign-chain", f"cells[{index}] producer entry has no ycsb")
        if cell.get("workload_flags") != dict(workload_flags):
            _fail("campaign-chain", f"cells[{index}].workload_flags differs from producer")
        campaign_root = _path_identity(
            campaign_root_value, gate="campaign-chain",
            label=f"cells[{index}].campaign_root",
        )
        expected_root = (output_root / "campaigns" / campaign_id).resolve()
        if campaign_root != expected_root:
            _fail("campaign-chain", f"cells[{index}] campaign identity/path mismatch")
        persisted_path = campaign_root / "reports" / "layer3_report.json"
        if failure_decision:
            if persisted_path.exists() or persisted_path.is_symlink():
                _fail(
                    "campaign-chain",
                    f"cells[{index}] failure campaign has a persisted layer3 report",
                )
            try:
                require_admitted_campaign(
                    campaign_root,
                    purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
                )
            except ArtifactAdmissionError:
                continue
            _fail(
                "campaign-chain",
                f"cells[{index}] failure campaign remains independently admitted",
            )
        arm_execution = report.get("arm_execution")
        arm_binding_digest = None
        if arm_execution is not None:
            arm_execution = _mapping(
                arm_execution, gate="campaign-chain", label="report.arm_execution",
            )
            arm_binding_digest = arm_execution.get("arm_binding_digest_sha256")
            if (
                frozenset(arm_execution) != _ARM_EXECUTION_KEYS
                or type(arm_binding_digest) is not str
                or _SHA256_RE.fullmatch(arm_binding_digest) is None
            ):
                _fail("campaign-chain", "report.arm_execution is invalid")
        _check_cell_campaign_identity(
            cell=cell, cell_index=index, workload=workload,
            entry=entry, trial_id=trial_id, budget=budget,
            campaign_root=campaign_root,
            arm_binding_digest=arm_binding_digest,
        )
        try:
            persisted = _read_report(persisted_path)
        except AutonomousTrialCompletenessError as exc:
            raise AutonomousTrialCompletenessError(
                f"[campaign-chain] persisted layer3 report cannot be read: {persisted_path}"
            ) from exc
        meta = persisted.get("meta")
        if not isinstance(meta, Mapping) or meta.get("campaign_id") != campaign_id:
            _fail("campaign-chain", "persisted layer3 campaign identity mismatch")
        if persisted.get("certifying_input", False) is not certifying_input:
            _fail(
                "campaign-chain",
                "persisted layer3 certifying_input differs from launch admission",
            )
        _require_certifying_layer3_admission(
            persisted, label="persisted layer3 report",
        )
        try:
            certified_view = require_admitted_campaign(
                campaign_root,
                purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
            )
            expected_decision = certified_view.decision.as_receipt()
        except ArtifactAdmissionError as exc:
            raise AutonomousTrialCompletenessError(
                "[campaign-chain] independent campaign admission validation failed"
            ) from exc
        _require_exact_layer3_admission_decision(
            persisted, expected=expected_decision, label="persisted layer3 report",
        )
        _require_exact_layer3_admission_decision(
            {"admission_decision": cell.get("admission_decision")},
            expected=expected_decision, label=f"cells[{index}]",
        )
        persisted_epoch: Mapping[str, Any] = {}
        if "campaign_verifier_epoch" in persisted:
            persisted_epoch = _mapping(
                persisted.get("campaign_verifier_epoch"), gate="campaign-chain",
                label="persisted layer3 report.campaign_verifier_epoch",
            )
            include_verifier_assessment_basis = (
                "verifier_assessment_basis" in persisted_epoch
            )
            expected_epoch = _epoch_projection(
                certified_view.campaign_verifier_epoch,
                verifier_assessment_basis=(
                    _VERIFIER_ASSESSMENT_BASIS
                    if include_verifier_assessment_basis else None
                ),
            )
            _require_compatible_layer3_epoch(
                persisted,
                expected=expected_epoch,
                label="persisted layer3 report",
            )
        fresh = _fresh_layer3_for_comparison(
            campaign_root=campaign_root,
            persisted_path=persisted_path,
            persisted=persisted,
            output_root=output_root,
        )
        include_epoch = "campaign_verifier_epoch" in persisted
        include_verifier_assessment_basis = (
            include_epoch
            and "verifier_assessment_basis" in persisted_epoch
        )
        include_current_verifier_conformance = (
            "current_verifier_conformance" in persisted
        )
        if _canonical_bytes(_layer3_comparison_projection(
            persisted, include_epoch=include_epoch,
            include_verifier_assessment_basis=(
                include_verifier_assessment_basis
            ),
            include_current_verifier_conformance=(
                include_current_verifier_conformance
            ),
        )) != _canonical_bytes(_layer3_comparison_projection(
            fresh, include_epoch=include_epoch,
            include_verifier_assessment_basis=(
                include_verifier_assessment_basis
            ),
            include_current_verifier_conformance=(
                include_current_verifier_conformance
            ),
        )):
            _fail("campaign-chain", "persisted layer3 report differs from fresh rebuild")


def _is_exact_failure_only_diagnostic(report: Mapping[str, Any]) -> bool:
    """Closed exploratory identity-failure shape; diagnosis is not admitted."""
    cells = report.get("cells")
    if (
        report.get("do_build") is not True
        or report.get("status") != "partial"
        or "arm_execution" in report
        or not isinstance(cells, list)
        or len(cells) != 1
        or not isinstance(cells[0], Mapping)
    ):
        return False
    cell = cells[0]
    keys = {
        "workload", "workload_flags", "perf_config_scale", "descriptor",
        "descriptor_binding", "campaign_id", "campaign_root", "generations",
        "stop_reason", "admission_decision", "pending_critic_disposition",
    }
    if not (set(cell) == keys or set(cell) == keys | {"error"}):
        return False
    # No report-side fact establishes whether an invalid invocation's
    # opportunistic error artifacts should exist. Exclude those shapes.
    if any(
        role.get("status") != "valid" or "error_artifacts" in role
        for generation in cell.get("generations", [])
        for role in generation.get("roles", {}).values()
    ):
        return False
    if "error" in cell:
        error = cell["error"]
        if not (
            cell.get("stop_reason") == "supervisor-error"
            and isinstance(error, Mapping)
            and set(error) == {"type", "message"}
            and type(error.get("type")) is str and bool(error["type"])
            and type(error.get("message")) is str
        ):
            return False
    return (
        all(type(cell.get(key)) is str and bool(cell[key])
            for key in ("campaign_id", "campaign_root"))
        and is_exact_cell_admission_failure_decision(cell.get("admission_decision"))
        and _is_exact_pending_critic_disposition(cell.get("pending_critic_disposition"))
    )


def _verify_failure_only_diagnostic(
    report: Mapping[str, Any], events: Sequence[Mapping[str, Any]], *, run_root: Path,
) -> None:
    role_events = [event for event in events if event.get("event") == "role-attempt"]
    # This includes the zero-invocation case. Completeness independently checks
    # the same total through generation-accounting ordinals.
    if len(role_events) != report["honest_accounting"]["role_query_count"]:
        _fail("failure-only-role", "role-attempt count differs from honest accounting")
    for event in role_events:
        # Producer P:2761 binds provider artifacts only with an arm digest;
        # P:4177 supplies None for exploratory runs. Refuse contradictory claims.
        if any(key in event for key in (
            "arm_binding_digest_sha256", "provider_artifacts",
            "provider_payload_sha256", "provider_envelope_sha256",
        )):
            _fail("failure-only-provider", "exploratory role declares arm-bound artifacts")
        # Invalid invocation error artifacts are opportunistic (P:2845-2858):
        # report facts cannot prove their absence. Keep that shape outside this
        # diagnostic contract instead of treating absent references as success.
        if event.get("status") != "valid" or "error_artifacts" in event:
            _fail("failure-only-role", "only completed valid invocations are supported")
        # A valid invocation necessarily completed the raw write (P:2808-2867).
        # Missing pointers therefore fail, even when no raw file was declared.
        raw_path, _raw = read_and_verify_bytes(
            event.get("raw_response_path"), root=run_root,
            expected_sha256=event.get("raw_response_sha256"),
            gate="failure-only-raw", label="valid role raw response",
        )
        expected_raw = run_root / "raw" / f"raw_{event['invocation_id']}.txt"
        if raw_path != expected_raw.resolve():
            _fail("failure-only-raw", "raw response differs from invocation path")
    generations = report["cells"][0]["generations"]
    for generation in generations:
        if "proposal" in generation:
            # P:4409 declares proposals only with arm_execution, which this
            # exploratory diagnostic shape excludes.
            _fail("failure-only-proposal", "exploratory generation declares proposal")
        # The producer reaches proposal persistence only after preview. Prove
        # each missing binding is an early stop, including mixed generations.
        if (
            "preview" in generation or "harness" in generation
            or not set(generation["roles"]).issubset({"planner", "coder"})
            or report["cells"][0]["stop_reason"] != "supervisor-error"
        ):
            _fail("failure-only-proposal", "proposal absence is not an early producer stop")
    campaign_root = _path_identity(
        report["cells"][0]["campaign_root"], gate="campaign-chain",
        label="cells[0].campaign_root",
    )
    assert_campaign_layer3_chain(report=report, output_root=campaign_root.parent.parent)


def verify_autonomous_trial_files(
    attempt_journal: Path,
    report_json: Path,
    *,
    campaign_output_root: Path | None = None,
    failure_only_diagnostic: bool = False,
) -> dict[str, Any] | None:
    """Verify files; opt-in failure diagnostics return a noncertifying receipt."""
    report = _read_report(Path(report_json))
    expected_report = Path(attempt_journal).resolve().parent / "report.json"
    if Path(report_json).resolve() != expected_report:
        _fail("run-envelope", "report_json is not the journal sibling report.json")
    assert_autonomous_trial_completeness(
        report=report, attempt_journal=Path(attempt_journal),
    )
    assert_autonomous_trial_execution_digest_chain(
        report=report, attempt_journal=Path(attempt_journal),
    )
    _journal_bytes, events = _read_journal(Path(attempt_journal))
    fatal_without_cells = (
        report.get("do_build") is True
        and isinstance(report.get("fatal_error"), Mapping)
        and report.get("cells") == []
    )
    failure_without_campaign = (
        report.get("do_build") is True
        and isinstance(report.get("cells"), list)
        and bool(report["cells"])
        and all(
            isinstance(cell, Mapping)
            and is_exact_campaignless_failure_fallback_cell(cell)
            for cell in report["cells"]
        )
    )
    if (
        failure_only_diagnostic is True
        and campaign_output_root is None
        and not fatal_without_cells
        and not failure_without_campaign
    ):
        if not _is_exact_failure_only_diagnostic(report):
            _fail("failure-only-diagnostic", "report is not an exact supported failure-only shape")
        _verify_failure_only_diagnostic(
            report, events, run_root=Path(attempt_journal).resolve().parent,
        )
        return {
            "schema_version": "autonomous-trial-failure-only-diagnostic/v1",
            "verification_mode": "failure-only-diagnostic",
            "certifying": False,
            "campaign_output_root_binding": "not-verified",
            "s8c_cross_binding": "not-established",
            "attempt_journal_sha256": hashlib.sha256(_journal_bytes).hexdigest(),
            "report_json_sha256": hashlib.sha256(Path(report_json).read_bytes()).hexdigest(),
            "checks": [
                "completeness", "execution-digest-chain", "role-accounting",
                "exploratory-provider-absence", "valid-role-raw", "proposals",
                "declared-campaign-layer3-chain",
            ],
        }
    if report.get("do_build") is True and campaign_output_root is None:
        # Completeness has already proved that fatal_error has one matching
        # terminal journal event.  A campaignless admission-failure cell also
        # has no campaign root to verify, but still goes through the chain gate.
        if not fatal_without_cells and not failure_without_campaign:
            _fail(
                "campaign-chain",
                "build trial verification requires campaign_output_root",
            )
    if not fatal_without_cells:
        verify_s8c_cross_binding(
            report=report,
            events=events,
            run_root=Path(attempt_journal).resolve().parent,
            output_root=(
                Path(campaign_output_root)
                if campaign_output_root is not None else None
            ),
        )
    if campaign_output_root is not None:
        assert_campaign_layer3_chain(
            report=report, output_root=Path(campaign_output_root),
        )
    elif failure_without_campaign:
        assert_campaign_layer3_chain(
            report=report,
            output_root=Path(attempt_journal).resolve().parent / "_no_campaign_output",
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify autonomous trial journal/report completeness",
    )
    parser.add_argument("attempt_journal")
    parser.add_argument("report_json")
    parser.add_argument("--campaign-output-root")
    parser.add_argument("--failure-only-diagnostic", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = verify_autonomous_trial_files(
            Path(args.attempt_journal),
            Path(args.report_json),
            failure_only_diagnostic=args.failure_only_diagnostic,
            campaign_output_root=(
                Path(args.campaign_output_root)
                if args.campaign_output_root is not None else None
            ),
        )
    except AutonomousTrialCompletenessError as exc:
        parser.error(str(exc))
    if receipt is not None:
        print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
