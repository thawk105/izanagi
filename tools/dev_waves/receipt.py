"""Strict Claude single-result envelope and child receipt binding."""
from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional

from .redaction import assert_sanitized, redact_value
from .schema import (
    DEFAULT_MAX_JSON_BYTES, MAX_JSON_INTEGER, DevWavesError, Outcome, ReasonCode,
    Receipt, canonical_bytes, is_run_id, is_task_id, strict_loads,
)


MAX_RECEIPT_ITEMS = 1000

# Captured from the keys of output/s6-rounds/runs/* raw.stdout result records.
# Only these compatibility fields may accompany the fields consumed here.
CLAUDE_RESULT_ALLOWED_FIELDS = frozenset({
    "api_error_status", "duration_api_ms", "duration_ms", "fast_mode_state",
    "is_error", "modelUsage", "num_turns", "permission_denials", "result",
    "session_id", "stop_reason", "structured_output", "subtype", "terminal_reason",
    "time_to_request_ms", "total_cost_usd", "ttft_ms", "ttft_stream_ms", "type",
    "usage", "uuid",
})
CLAUDE_RESULT_REQUIRED_FIELDS = frozenset({
    "type", "subtype", "is_error", "permission_denials", "result",
    "total_cost_usd", "structured_output",
})
CLAUDE_RESULT_SUBTYPES = frozenset({
    "success", "error_during_execution", "error_max_budget_usd", "error_max_turns",
    "error_max_structured_output_retries", "permission_denied",
})
PERMISSION_ABORT_SUBTYPES = frozenset({"permission_denied"})


@dataclass(frozen=True)
class ReceiptBinding:
    run_id: str
    wave_index: int
    base_sha: str
    schema_sha256: Optional[str] = None


@dataclass(frozen=True)
class ParsedChildResult:
    receipt: Receipt
    total_cost_usd: Decimal
    subtype: str
    is_error: bool
    permission_denials: tuple[Any, ...]
    permission_abort: bool


def _receipt_error(kind: str, field: str = "receipt") -> DevWavesError:
    return DevWavesError(ReasonCode.RECEIPT_INVALID, {"label": field, "kind": kind})


def _is_string(value: Any, *, minimum: int = 1, maximum: int = 128) -> bool:
    return isinstance(value, str) and minimum <= len(value) <= maximum and "\x00" not in value


def _is_lower_hex(value: Any, length: int) -> bool:
    return (_is_string(value, minimum=length, maximum=length) and
            all(ch in "0123456789abcdef" for ch in value))


def _task_ids(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > MAX_RECEIPT_ITEMS:
        raise _receipt_error("array", field)
    result = []
    for item in value:
        if not _is_string(item, minimum=5, maximum=64):
            raise _receipt_error("task-id", field)
        if not is_task_id(item):
            raise _receipt_error("task-id", field)
        result.append(item)
    if len(set(result)) != len(result):
        raise _receipt_error("duplicate", field)
    return tuple(result)


def _commits(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > MAX_RECEIPT_ITEMS:
        raise _receipt_error("array", "landed_commits")
    if not all(_is_lower_hex(item, 40) for item in value):
        raise _receipt_error("sha", "landed_commits")
    if len(set(value)) != len(value):
        raise _receipt_error("duplicate", "landed_commits")
    return tuple(value)


_RECEIPT_V1_FIELDS = frozenset({
    "schema_version", "supervisor_run_id", "wave_index", "outcome", "stop_reason",
    "base_main_sha", "landed_main_sha", "selected_task_ids", "next_task_ids",
    "landed_commits", "child_task_run_id",
})
_RECEIPT_V2_FIELDS = _RECEIPT_V1_FIELDS | {"fold_commit_sha"}
_RECEIPT_SCHEMA_VERSIONS = frozenset({1, 2})


def load_receipt_schema(version: int = 1) -> Mapping[str, Any]:
    """receipt 固有 version で不変 schema を 1 つ読む。"""
    if version not in _RECEIPT_SCHEMA_VERSIONS or isinstance(version, bool):
        raise ValueError("unsupported receipt schema version")
    path = Path(__file__).with_name(f"schema_v{version}.json")
    raw = path.read_bytes()
    value = strict_loads(raw, label="receipt-schema", max_bytes=DEFAULT_MAX_JSON_BYTES)
    if not isinstance(value, dict):
        raise DevWavesError(ReasonCode.RECEIPT_INVALID, {
            "label": "receipt-schema", "kind": "not-object",
        })
    return value


def receipt_schema_digest(version: int = 1) -> str:
    return hashlib.sha256(canonical_bytes(load_receipt_schema(version))).hexdigest()


def _bound_schema_version(value: object, binding: Optional[ReceiptBinding]) -> int:
    if binding is not None and not isinstance(binding, ReceiptBinding):
        raise TypeError("binding must be ReceiptBinding")
    if binding is not None and binding.schema_sha256 is not None:
        matches = [
            version for version in sorted(_RECEIPT_SCHEMA_VERSIONS)
            if receipt_schema_digest(version) == binding.schema_sha256
        ]
        if len(matches) != 1:
            raise _receipt_error("schema-digest", "schema_version")
        return matches[0]
    if not isinstance(value, dict):
        raise _receipt_error("field-set")
    version = value.get("schema_version")
    if version not in _RECEIPT_SCHEMA_VERSIONS or isinstance(version, bool):
        raise _receipt_error("schema-version", "schema_version")
    return version


def validate_child_receipt(
    value: object,
    *,
    binding: Optional[ReceiptBinding] = None,
) -> Receipt:
    """wave manifest が束縛した version に対して receipt を検査する。"""
    version = _bound_schema_version(value, binding)
    expected_fields = _RECEIPT_V1_FIELDS if version == 1 else _RECEIPT_V2_FIELDS
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise _receipt_error("field-set")
    if value["schema_version"] != version or isinstance(value["schema_version"], bool):
        raise _receipt_error("schema-version", "schema_version")
    run_id = value["supervisor_run_id"]
    if not is_run_id(run_id):
        raise _receipt_error("run-id", "supervisor_run_id")
    wave_index = value["wave_index"]
    if (not isinstance(wave_index, int) or isinstance(wave_index, bool) or
            not 1 <= wave_index <= MAX_JSON_INTEGER):
        raise _receipt_error("integer", "wave_index")
    try:
        outcome = Outcome(value["outcome"])
        stop_reason = ReasonCode(value["stop_reason"])
    except (TypeError, ValueError):
        raise _receipt_error("enum") from None
    base_sha = value["base_main_sha"]
    if not _is_lower_hex(base_sha, 40):
        raise _receipt_error("sha", "base_main_sha")
    landed_sha = value["landed_main_sha"]
    if landed_sha is not None and not _is_lower_hex(landed_sha, 40):
        raise _receipt_error("sha", "landed_main_sha")
    selected = _task_ids(value["selected_task_ids"], "selected_task_ids")
    next_ids = _task_ids(value["next_task_ids"], "next_task_ids")
    commits = _commits(value["landed_commits"])
    child_run = value["child_task_run_id"]
    if not is_run_id(child_run):
        raise _receipt_error("task-run-id", "child_task_run_id")
    fold_sha = value.get("fold_commit_sha")
    if fold_sha is not None and not _is_lower_hex(fold_sha, 40):
        raise _receipt_error("sha", "fold_commit_sha")

    if outcome is Outcome.COMPLETED:
        if (stop_reason is not ReasonCode.WAVE_COMPLETED or landed_sha is None or
                not commits or not selected):
            raise _receipt_error("completed-binding")
    else:
        if landed_sha is not None or commits or fold_sha is not None:
            raise _receipt_error("noncompleted-git-fields")
    if (outcome is Outcome.NO_ACTIONABLE_TASK and
            stop_reason is not ReasonCode.NO_ACTIONABLE_TASK):
        raise _receipt_error("outcome-reason")
    if (outcome is Outcome.USER_RULING_REQUIRED and
            stop_reason is not ReasonCode.USER_RULING_REQUIRED):
        raise _receipt_error("outcome-reason")
    if binding is not None:
        if not isinstance(binding, ReceiptBinding):
            raise TypeError("binding must be ReceiptBinding")
        if run_id != binding.run_id:
            raise _receipt_error("binding", "supervisor_run_id")
        if wave_index != binding.wave_index:
            raise _receipt_error("binding", "wave_index")
        if base_sha != binding.base_sha:
            raise _receipt_error("binding", "base_main_sha")

    return Receipt(
        version, run_id, wave_index, outcome, stop_reason, base_sha, landed_sha,
        selected, next_ids, commits, child_run, fold_sha,
    )


def encode_receipt(receipt: Receipt) -> bytes:
    """v1 / v2 を互いに素な閉じた field 集合で符号化する。"""
    if not isinstance(receipt, Receipt):
        raise TypeError("receipt must be Receipt")
    fields = _RECEIPT_V1_FIELDS if receipt.schema_version == 1 else _RECEIPT_V2_FIELDS
    if receipt.schema_version not in _RECEIPT_SCHEMA_VERSIONS:
        raise ValueError("unsupported receipt schema version")
    if receipt.schema_version == 1 and receipt.fold_commit_sha is not None:
        raise ValueError("v1 receipt cannot declare a fold commit")
    wire = {
        field: getattr(receipt, field)
        for field in fields
    }
    return canonical_bytes(wire)


def _read_bounded(path: os.PathLike[str] | str, max_bytes: int) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(os.fspath(path), flags)
    except OSError:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "claude-result", "kind": "open-failed",
        }) from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
                "label": "claude-result", "kind": "not-regular",
            })
        if info.st_size > max_bytes:
            raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
                "label": "claude-result", "kind": "size-limit",
                "byte_length": info.st_size,
            })
        chunks = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > max_bytes:
            raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
                "label": "claude-result", "kind": "size-limit", "byte_length": len(raw),
            })
        return raw
    finally:
        os.close(fd)


def parse_claude_result(
    path: os.PathLike[str] | str,
    *,
    max_bytes: int,
    binding: ReceiptBinding,
) -> ParsedChildResult:
    """Parse exactly one complete result envelope; never inspect prose result."""
    raw = _read_bounded(path, max_bytes)
    envelope = strict_loads(
        raw, label="claude-result", max_bytes=max_bytes,
        allowed_fields=CLAUDE_RESULT_ALLOWED_FIELDS,
    )
    if not isinstance(envelope, dict) or not CLAUDE_RESULT_REQUIRED_FIELDS <= set(envelope):
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "claude-result", "kind": "field-set",
        })
    if envelope["type"] != "result":
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "type", "kind": "wrong-type",
        })
    subtype = envelope["subtype"]
    if subtype not in CLAUDE_RESULT_SUBTYPES:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "subtype", "kind": "unknown",
        })
    is_error = envelope["is_error"]
    if not isinstance(is_error, bool):
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "is_error", "kind": "boolean",
        })
    if subtype != "success" or is_error:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "result-status", "kind": "not-success",
        })
    if not isinstance(envelope["result"], str):
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "result", "kind": "string",
        })
    denials = envelope["permission_denials"]
    if not isinstance(denials, list):
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "permission_denials", "kind": "array",
        })
    if denials:
        raise DevWavesError(ReasonCode.PERMISSION_ABORT, {
            "label": "permission_denials", "kind": "nonempty",
        })
    cost_value = envelope["total_cost_usd"]
    if isinstance(cost_value, bool) or not isinstance(cost_value, (int, Decimal)):
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "total_cost_usd", "kind": "number",
        })
    cost = Decimal(cost_value)
    if not cost.is_finite() or cost < 0:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": "total_cost_usd", "kind": "range",
        })
    receipt = validate_child_receipt(envelope["structured_output"], binding=binding)
    clean_denials = redact_value(denials)
    assert isinstance(clean_denials, list)
    return ParsedChildResult(
        receipt=receipt,
        total_cost_usd=cost,
        subtype=subtype,
        is_error=is_error,
        permission_denials=tuple(clean_denials),
        permission_abort=bool(denials) or subtype in PERMISSION_ABORT_SUBTYPES,
    )


def permission_abort_from_envelope(
    path: os.PathLike[str] | str, *, max_bytes: int,
) -> bool:
    """Classify permission abort without depending on receipt validity."""
    raw = _read_bounded(path, max_bytes)
    envelope = strict_loads(
        raw, label="claude-result", max_bytes=max_bytes,
        allowed_fields=CLAUDE_RESULT_ALLOWED_FIELDS,
    )
    if not isinstance(envelope, dict):
        return False
    denials = envelope.get("permission_denials")
    subtype = envelope.get("subtype")
    return bool(isinstance(denials, list) and denials) or subtype in PERMISSION_ABORT_SUBTYPES


def persist_sanitized_receipt(path: os.PathLike[str] | str, receipt: Receipt) -> None:
    """Create a sanitized receipt durably; never replace an existing record."""
    if not isinstance(receipt, Receipt):
        raise TypeError("receipt must be Receipt")
    wire = strict_loads(
        encode_receipt(receipt), label="receipt-persist", max_bytes=DEFAULT_MAX_JSON_BYTES,
    )
    clean = redact_value(wire)
    assert_sanitized(clean)
    raw = canonical_bytes(clean) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(os.fspath(path), flags, 0o600)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short receipt write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    parent_fd = os.open(os.path.dirname(os.path.abspath(os.fspath(path))), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


__all__ = [
    "CLAUDE_RESULT_ALLOWED_FIELDS", "CLAUDE_RESULT_REQUIRED_FIELDS",
    "CLAUDE_RESULT_SUBTYPES", "PERMISSION_ABORT_SUBTYPES", "ParsedChildResult",
    "Receipt", "ReceiptBinding", "encode_receipt", "load_receipt_schema", "parse_claude_result",
    "permission_abort_from_envelope", "persist_sanitized_receipt",
    "receipt_schema_digest", "validate_child_receipt",
]
