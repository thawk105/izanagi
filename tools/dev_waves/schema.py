"""Closed wire types and the single strict JSON decoder for dev-waves v1."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Collection, Mapping, Optional, Sequence, Union

from .redaction import assert_sanitized, sanitize_detail


PROTOCOL_VERSION = 1
SCHEMA_VERSION = 1
DEFAULT_MAX_JSON_BYTES = 1 << 20
MAX_JSON_DEPTH = 32
MAX_JSON_STRING_CHARS = 1 << 20
MAX_JSON_INTEGER = (1 << 63) - 1
MAX_JSON_DECIMAL = Decimal("1e100")


class RunState(str, Enum):
    CREATED = "created"
    PREFLIGHT = "preflight"
    READY = "ready"
    WAVE_PREPARED = "wave-prepared"
    CHILD_RUNNING = "child-running"
    CHILD_EXITED = "child-exited"
    VERIFYING = "verifying"
    WAVE_ACCEPTED = "wave-accepted"
    STOPPING = "stopping"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class Outcome(str, Enum):
    COMPLETED = "completed"
    NO_ACTIONABLE_TASK = "no-actionable-task"
    USER_RULING_REQUIRED = "user-ruling-required"
    BLOCKED = "blocked"
    FAILED = "failed"


class ReasonCode(str, Enum):
    INVALID_ARGS = "invalid-args"
    DAEMON_BUSY = "daemon-busy"
    NESTED_LAUNCH_ENVIRONMENT = "nested-launch-environment"
    MAIN_NOT_FOUND = "main-not-found"
    MAIN_NOT_CLEAN = "main-not-clean"
    MAIN_MOVED = "main-moved"
    CODE_DIRTY = "code-dirty"
    CLAUDE_UNAVAILABLE = "claude-unavailable"
    FLAG_UNAVAILABLE = "flag-unavailable"
    FAKE_HANDSHAKE_FAILED = "fake-handshake-failed"
    SETTINGS_INVALID = "settings-invalid"
    TRUST_ROOT_CHANGED = "trust-root-changed"
    BUDGET_INVALID = "budget-invalid"
    RUNTIME_IO_FAILURE = "runtime-io-failure"
    REQUEST_CONFLICT = "request-conflict"
    FOREIGN_LEASE = "foreign-lease"
    POISONED = "poisoned"
    INVALID_RUN = "invalid-run"
    SPAWN_FAILED = "spawn-failed"
    PERMISSION_ABORT = "permission-abort"
    TIMEOUT = "timeout"
    NONZERO_EXIT = "nonzero-exit"
    LOG_LIMIT = "log-limit"
    OUTPUT_INVALID = "output-invalid"
    RECEIPT_INVALID = "receipt-invalid"
    MAIN_UNCHANGED = "main-unchanged"
    MAIN_DIRTY = "main-dirty"
    MAIN_NOT_FF = "main-not-ff"
    COMMIT_MISMATCH = "commit-mismatch"
    TASK_RUN_INCOMPLETE = "task-run-incomplete"
    WORKLOG_INVALID = "worklog-invalid"
    HANDOFF_LEAKED = "handoff-leaked"
    CHECK_FAILED = "check-failed"
    PROVENANCE_FAILED = "provenance-failed"
    SUBMODULE_DIRTY = "submodule-dirty"
    REMOTE_REF_CHANGED = "remote-ref-changed"
    WAVE_COMPLETED = "wave-completed"
    MAX_WAVES_REACHED = "max-waves-reached"
    NO_ACTIONABLE_TASK = "no-actionable-task"
    USER_RULING_REQUIRED = "user-ruling-required"
    SIGNAL_RECEIVED = "signal-received"
    AMBIGUOUS_RECOVERY = "ambiguous-recovery"


class DevWavesError(Exception):
    """Closed domain error whose detail is sanitized at construction time."""

    def __init__(self, code: ReasonCode, detail: Any = None):
        if not isinstance(code, ReasonCode):
            raise TypeError("code must be a ReasonCode")
        self.code = code
        self.detail = sanitize_detail(detail)
        super().__init__(code.value)


TERMINAL_STATES = frozenset({
    RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED, RunState.INTERRUPTED,
})
NONTERMINAL_STATES = frozenset(set(RunState) - TERMINAL_STATES)

_LINEAR_TRANSITIONS = {
    RunState.CREATED: frozenset({RunState.PREFLIGHT}),
    RunState.PREFLIGHT: frozenset({RunState.READY}),
    RunState.READY: frozenset({RunState.WAVE_PREPARED}),
    RunState.WAVE_PREPARED: frozenset({RunState.CHILD_RUNNING}),
    RunState.CHILD_RUNNING: frozenset({RunState.CHILD_EXITED}),
    RunState.CHILD_EXITED: frozenset({RunState.VERIFYING}),
    RunState.VERIFYING: frozenset({RunState.WAVE_ACCEPTED}),
    RunState.WAVE_ACCEPTED: frozenset({RunState.READY, RunState.COMPLETED}),
    RunState.STOPPING: frozenset({
        RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED, RunState.INTERRUPTED,
    }),
}
ALLOWED_TRANSITIONS = {
    state: frozenset(set(_LINEAR_TRANSITIONS.get(state, ())) |
                     ({RunState.STOPPING} if state in NONTERMINAL_STATES and
                      state is not RunState.STOPPING else set()))
    for state in RunState
}


def validate_transition(
    current: RunState,
    target: RunState,
    *,
    reason: Optional[ReasonCode] = None,
) -> None:
    """Validate one durable state edge; return None or fail closed."""
    if not isinstance(current, RunState) or not isinstance(target, RunState):
        raise TypeError("current and target must be RunState values")
    if reason is not None and not isinstance(reason, ReasonCode):
        raise TypeError("reason must be a ReasonCode or None")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise DevWavesError(ReasonCode.INVALID_RUN, {
            "kind": "state-transition", "state": current.value,
            "target": target.value, "reason": reason.value if reason else None,
        })
    if current is RunState.STOPPING and target is RunState.COMPLETED:
        if reason is not ReasonCode.NO_ACTIONABLE_TASK:
            raise DevWavesError(ReasonCode.INVALID_RUN, {
                "kind": "completed-stop-reason", "state": current.value,
                "target": target.value, "reason": reason.value if reason else None,
            })


@dataclass(frozen=True)
class ResourceLimits:
    per_wave_timeout_s: Optional[int]
    total_timeout_s: Optional[int]
    per_wave_budget_usd: Optional[Decimal]
    total_budget_usd: Optional[Decimal]
    max_wave_output_bytes: Optional[int]
    max_run_bytes: Optional[int]


@dataclass(frozen=True)
class SubmitRequest:
    protocol_version: int
    action: str
    repo_identity: str
    max_waves: int
    profile: str
    client_request_id: str
    limits: ResourceLimits


@dataclass(frozen=True)
class StatusRequest:
    protocol_version: int
    action: str
    repo_identity: str
    run_id: str


@dataclass(frozen=True)
class CancelRequest:
    protocol_version: int
    action: str
    repo_identity: str
    run_id: str
    client_request_id: str


@dataclass(frozen=True)
class SubmitResponse:
    protocol_version: int
    ok: bool
    run_id: str
    state: RunState
    reason: Optional[ReasonCode]


@dataclass(frozen=True)
class StatusResponse:
    protocol_version: int
    ok: bool
    run_id: str
    state: RunState
    wave_index: int
    elapsed_s: Decimal
    reason: Optional[ReasonCode]


@dataclass(frozen=True)
class CancelResponse:
    protocol_version: int
    ok: bool
    run_id: str
    state: RunState
    reason: Optional[ReasonCode]


@dataclass(frozen=True)
class ErrorResponse:
    protocol_version: int
    ok: bool
    reason: ReasonCode
    detail: Any


@dataclass(frozen=True)
class Response:
    """Closed general response used at the socket boundary."""
    protocol_version: int
    action: str
    ok: bool
    run_id: Optional[str]
    state: Optional[RunState]
    wave_index: Optional[int]
    elapsed_s: Optional[Decimal]
    reason: Optional[ReasonCode]
    detail: Any


@dataclass(frozen=True)
class RunManifest:
    schema_version: int
    run_id: str
    repo_identity: str
    profile: str
    max_waves: int
    limits: ResourceLimits
    created_utc: str
    executable_sha256: str
    supervisor_code_sha256: str
    request_digest: str


@dataclass(frozen=True)
class WaveManifest:
    schema_version: int
    supervisor_run_id: str
    wave_index: int
    worktree: str
    main_worktree: str
    base_main_sha: str
    receipt_schema_sha256: str


@dataclass(frozen=True)
class WorkerSpec:
    schema_version: int
    supervisor_run_id: str
    wave_index: int
    executable_path: str
    executable_sha256: str
    cwd: str
    environment: tuple[tuple[str, str], ...]
    model: str
    effort: str
    main_worktree: str
    wave_manifest_path: str
    receipt_schema_json: str
    receipt_schema_sha256: str
    per_wave_budget_usd: Decimal
    per_wave_timeout_s: int
    max_wave_output_bytes: int
    max_run_bytes: int
    stdout_path: str
    stderr_path: str
    child_start_path: str
    worker_exit_path: str


@dataclass(frozen=True)
class Receipt:
    schema_version: int
    supervisor_run_id: str
    wave_index: int
    outcome: Outcome
    stop_reason: ReasonCode
    base_main_sha: str
    landed_main_sha: Optional[str]
    selected_task_ids: tuple[str, ...]
    next_task_ids: tuple[str, ...]
    landed_commits: tuple[str, ...]
    child_task_run_id: str


Request = Union[SubmitRequest, StatusRequest, CancelRequest]


_DECIMAL_RE = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z")
_HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z"
)
_PROFILE_RE = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
_TASK_ID_RE = re.compile(r"T-[0-9]{3,}\Z")


def is_run_id(value: object) -> bool:
    """Return whether *value* is in the public ASCII run-id grammar."""
    return isinstance(value, str) and _ID_RE.fullmatch(value) is not None


def is_task_id(value: object) -> bool:
    """Return whether *value* is in the public ASCII task-id grammar."""
    return isinstance(value, str) and _TASK_ID_RE.fullmatch(value) is not None


def parse_decimal_string(value: Any, *, label: str) -> Decimal:
    if not isinstance(value, str) or not _DECIMAL_RE.fullmatch(value):
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {
            "label": label, "kind": "noncanonical-decimal",
        })
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {
            "label": label, "kind": "invalid-decimal",
        })
    if not result.is_finite() or result > MAX_JSON_DECIMAL:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {
            "label": label, "kind": "decimal-range",
        })
    return result


def canonical_decimal(value: Decimal) -> str:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError("decimal must be finite and non-negative")
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        text = "0"
    if not _DECIMAL_RE.fullmatch(text):
        raise ValueError("decimal is outside canonical grammar")
    return text


def _reject_constant(_value: str) -> Any:
    raise ValueError("non-finite JSON number")


def _parse_int(value: str) -> int:
    number = int(value)
    if abs(number) > MAX_JSON_INTEGER:
        raise ValueError("JSON integer out of range")
    return number


def _parse_float(value: str) -> Decimal:
    number = Decimal(value)
    if not number.is_finite() or abs(number) > MAX_JSON_DECIMAL:
        raise ValueError("JSON decimal out of range")
    return number


def _unique_pairs(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _validate_json_tree(value: Any, *, depth: int = 1) -> None:
    if depth > MAX_JSON_DEPTH:
        raise ValueError("JSON nesting depth exceeded")
    if isinstance(value, str):
        if len(value) > MAX_JSON_STRING_CHARS:
            raise ValueError("JSON string too long")
        if "\x00" in value or any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise ValueError("JSON string contains NUL or lone surrogate")
        return
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if abs(value) > MAX_JSON_INTEGER:
            raise ValueError("JSON integer out of range")
        return
    if isinstance(value, Decimal):
        if not value.is_finite() or abs(value) > MAX_JSON_DECIMAL:
            raise ValueError("JSON decimal out of range")
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_tree(item, depth=depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_json_tree(key, depth=depth + 1)
            _validate_json_tree(item, depth=depth + 1)
        return
    raise ValueError("unsupported JSON value")


def _scan_json_depth(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValueError("JSON nesting depth exceeded")
        elif character in "]}":
            depth -= 1


def strict_loads(
    raw: bytes,
    *,
    label: str,
    max_bytes: int,
    allowed_fields: Optional[Collection[str]] = None,
) -> object:
    """Decode one UTF-8 JSON value with every v2 strictness check enabled."""
    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer")
    if len(raw) > max_bytes:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": label, "kind": "size-limit", "byte_length": len(raw),
        })
    if not raw:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": label, "kind": "empty-json",
        })
    if b"\x00" in raw:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": label, "kind": "nul-byte",
        })
    try:
        text = raw.decode("utf-8", errors="strict")
        _scan_json_depth(text)
        value = json.loads(
            text, object_pairs_hook=_unique_pairs, parse_int=_parse_int,
            parse_float=_parse_float, parse_constant=_reject_constant,
        )
        _validate_json_tree(value)
        if allowed_fields is not None:
            if not isinstance(value, dict):
                raise ValueError("top-level JSON value must be an object")
            unknown = set(value) - set(allowed_fields)
            if unknown:
                raise ValueError("unknown top-level JSON field")
        return value
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise DevWavesError(ReasonCode.OUTPUT_INVALID, {
            "label": label, "kind": type(exc).__name__,
        }) from None


def _strict_argument_loads(
    raw: bytes,
    *,
    label: str,
    allowed_fields: Optional[Collection[str]] = None,
) -> object:
    """Map strict syntax rejection to the caller-facing invalid-args domain."""
    try:
        return strict_loads(
            raw, label=label, max_bytes=DEFAULT_MAX_JSON_BYTES,
            allowed_fields=allowed_fields,
        )
    except DevWavesError as exc:
        if exc.code is not ReasonCode.OUTPUT_INVALID:
            raise
        raise DevWavesError(ReasonCode.INVALID_ARGS, {
            "label": label, "kind": "strict-json",
        }) from None


def _wire_value(value: Any, *, field_name: Optional[str] = None) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if dataclasses.is_dataclass(value):
        return {
            field.name: _wire_value(getattr(value, field.name), field_name=field.name)
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _wire_value(item) for key, item in value.items()}
    if isinstance(value, tuple) and field_name == "environment":
        return {key: item for key, item in value}
    if isinstance(value, (list, tuple)):
        return [_wire_value(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite float")
        raise TypeError("float is not canonical; use Decimal")
    raise TypeError("value is not JSON serializable")


def canonical_bytes(value: object) -> bytes:
    wire = _wire_value(value)
    _validate_json_tree(wire)
    return json.dumps(
        wire, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _closed_object(value: Any, required: Collection[str], *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": label, "kind": "not-object"})
    expected = set(required)
    if set(value) != expected:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": label, "kind": "field-set"})
    return value


def _required_int(value: Any, *, label: str, minimum: int = 1) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": label, "kind": "integer"})
    return value


def _required_string(value: Any, pattern: re.Pattern[str], *, label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": label, "kind": "string"})
    return value


_LIMIT_FIELDS = (
    "per_wave_timeout_s", "total_timeout_s", "per_wave_budget_usd",
    "total_budget_usd", "max_wave_output_bytes", "max_run_bytes",
)


def _parse_limits(value: Any) -> ResourceLimits:
    item = _closed_object(value, _LIMIT_FIELDS, label="limits")
    for key in _LIMIT_FIELDS:
        if item[key] is not None:
            continue
        # Null is retained so daemon preflight can record budget-invalid without
        # inventing a numeric default.
    def optional_int(key: str) -> Optional[int]:
        return None if item[key] is None else _required_int(item[key], label=key)
    def optional_decimal(key: str) -> Optional[Decimal]:
        return None if item[key] is None else parse_decimal_string(item[key], label=key)
    return ResourceLimits(
        optional_int("per_wave_timeout_s"), optional_int("total_timeout_s"),
        optional_decimal("per_wave_budget_usd"), optional_decimal("total_budget_usd"),
        optional_int("max_wave_output_bytes"), optional_int("max_run_bytes"),
    )


def parse_request(raw: bytes) -> Request:
    value = _strict_argument_loads(raw, label="request")
    if not isinstance(value, dict) or not isinstance(value.get("action"), str):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "request", "kind": "action"})
    action = value["action"]
    common = {"protocol_version", "action", "repo_identity"}
    if action == "submit":
        item = _closed_object(value, common | {
            "max_waves", "profile", "client_request_id", "limits",
        }, label="submit")
        if item["protocol_version"] != PROTOCOL_VERSION:
            raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "protocol_version", "kind": "version"})
        return SubmitRequest(
            PROTOCOL_VERSION, action,
            _required_string(item["repo_identity"], _HEX64_RE, label="repo_identity"),
            _required_int(item["max_waves"], label="max_waves"),
            _required_string(item["profile"], _PROFILE_RE, label="profile"),
            _required_string(item["client_request_id"], _UUID_RE, label="client_request_id"),
            _parse_limits(item["limits"]),
        )
    if action == "status":
        item = _closed_object(value, common | {"run_id"}, label="status")
        if item["protocol_version"] != PROTOCOL_VERSION:
            raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "protocol_version", "kind": "version"})
        return StatusRequest(
            PROTOCOL_VERSION, action,
            _required_string(item["repo_identity"], _HEX64_RE, label="repo_identity"),
            _required_string(item["run_id"], _ID_RE, label="run_id"),
        )
    if action == "cancel":
        item = _closed_object(value, common | {"run_id", "client_request_id"}, label="cancel")
        if item["protocol_version"] != PROTOCOL_VERSION:
            raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "protocol_version", "kind": "version"})
        return CancelRequest(
            PROTOCOL_VERSION, action,
            _required_string(item["repo_identity"], _HEX64_RE, label="repo_identity"),
            _required_string(item["run_id"], _ID_RE, label="run_id"),
            _required_string(item["client_request_id"], _UUID_RE, label="client_request_id"),
        )
    raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "action", "kind": "unknown"})


def validate_limits(request: SubmitRequest) -> ResourceLimits:
    if not isinstance(request, SubmitRequest):
        raise TypeError("request must be SubmitRequest")
    limits = request.limits
    values = dataclasses.astuple(limits)
    if any(value is None for value in values):
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {"label": "limits", "kind": "missing"})
    assert limits.per_wave_timeout_s is not None
    assert limits.total_timeout_s is not None
    assert limits.per_wave_budget_usd is not None
    assert limits.total_budget_usd is not None
    assert limits.max_wave_output_bytes is not None
    assert limits.max_run_bytes is not None
    if limits.total_timeout_s < limits.per_wave_timeout_s:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {"label": "total_timeout_s", "kind": "below-wave"})
    if limits.total_timeout_s > request.max_waves * limits.per_wave_timeout_s:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {"label": "total_timeout_s", "kind": "above-capacity"})
    if limits.per_wave_budget_usd <= 0 or limits.total_budget_usd <= 0:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {"label": "budget", "kind": "non-positive"})
    if not (limits.per_wave_budget_usd <= limits.total_budget_usd <=
            request.max_waves * limits.per_wave_budget_usd):
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {"label": "total_budget_usd", "kind": "range"})
    if limits.max_run_bytes < limits.max_wave_output_bytes:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {"label": "max_run_bytes", "kind": "below-wave"})
    if limits.max_run_bytes < 64 * 1024:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {
            "label": "max_run_bytes", "kind": "below-control-reserve",
        })
    return limits


def encode_response(response: Response) -> bytes:
    if not isinstance(response, (Response, SubmitResponse, StatusResponse, CancelResponse, ErrorResponse)):
        raise TypeError("response must be a response dataclass")
    return canonical_bytes(response)


_RESPONSE_FIELDS = frozenset({
    "protocol_version", "action", "ok", "run_id", "state", "wave_index",
    "elapsed_s", "reason", "detail",
})


def parse_response(raw: bytes) -> Response:
    item = _strict_argument_loads(raw, label="response", allowed_fields=_RESPONSE_FIELDS)
    item = _closed_object(item, _RESPONSE_FIELDS, label="response")
    if item["protocol_version"] != PROTOCOL_VERSION:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "protocol_version", "kind": "version"})
    if item["action"] not in ("submit", "status", "cancel", "error"):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "action", "kind": "unknown"})
    if not isinstance(item["ok"], bool):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "ok", "kind": "boolean"})
    run_id = item["run_id"]
    if run_id is not None:
        run_id = _required_string(run_id, _ID_RE, label="run_id")
    try:
        state = None if item["state"] is None else RunState(item["state"])
        reason = None if item["reason"] is None else ReasonCode(item["reason"])
    except (TypeError, ValueError):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "response", "kind": "enum"}) from None
    wave = item["wave_index"]
    if wave is not None:
        wave = _required_int(wave, label="wave_index", minimum=0)
    elapsed = item["elapsed_s"]
    if elapsed is not None:
        elapsed = parse_decimal_string(elapsed, label="elapsed_s")
    try:
        assert_sanitized(item["detail"])
    except ValueError:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "detail", "kind": "unsanitized"}) from None
    if item["action"] == "error" and (item["ok"] or reason is None):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "response", "kind": "error-binding"})
    return Response(
        PROTOCOL_VERSION, item["action"], item["ok"], run_id, state, wave,
        elapsed, reason, item["detail"],
    )


def _absolute_path(value: Any, *, label: str) -> str:
    if (not isinstance(value, str) or not value or "\x00" in value or
            not os.path.isabs(value)):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": label, "kind": "absolute-path"})
    return value


_RUN_MANIFEST_FIELDS = frozenset(field.name for field in dataclasses.fields(RunManifest))
_WAVE_MANIFEST_FIELDS = frozenset(field.name for field in dataclasses.fields(WaveManifest))
_WORKER_SPEC_FIELDS = frozenset(field.name for field in dataclasses.fields(WorkerSpec))
WORKER_ENV_ALLOWED_KEYS = frozenset({
    "GIT_CONFIG_GLOBAL", "GIT_TERMINAL_PROMPT", "GIT_TRACE2_EVENT", "HOME", "LANG",
    "LC_ALL", "PATH", "PYTHONDONTWRITEBYTECODE", "TMPDIR", "TZ",
    "XDG_CACHE_HOME", "XDG_CONFIG_HOME",
})


def parse_run_manifest(raw: bytes) -> RunManifest:
    item = _strict_argument_loads(
        raw, label="run-manifest", allowed_fields=_RUN_MANIFEST_FIELDS,
    )
    item = _closed_object(item, _RUN_MANIFEST_FIELDS, label="run-manifest")
    if item["schema_version"] != SCHEMA_VERSION:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "schema_version", "kind": "version"})
    limits = _parse_limits(item["limits"])
    created = item["created_utc"]
    if not isinstance(created, str) or len(created) > 64 or "T" not in created:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "created_utc", "kind": "timestamp"})
    return RunManifest(
        SCHEMA_VERSION,
        _required_string(item["run_id"], _ID_RE, label="run_id"),
        _required_string(item["repo_identity"], _HEX64_RE, label="repo_identity"),
        _required_string(item["profile"], _PROFILE_RE, label="profile"),
        _required_int(item["max_waves"], label="max_waves"), limits, created,
        _required_string(item["executable_sha256"], _HEX64_RE, label="executable_sha256"),
        _required_string(item["supervisor_code_sha256"], _HEX64_RE, label="supervisor_code_sha256"),
        _required_string(item["request_digest"], _HEX64_RE, label="request_digest"),
    )


def parse_wave_manifest(raw: bytes) -> WaveManifest:
    item = _strict_argument_loads(
        raw, label="wave-manifest", allowed_fields=_WAVE_MANIFEST_FIELDS,
    )
    item = _closed_object(item, _WAVE_MANIFEST_FIELDS, label="wave-manifest")
    if item["schema_version"] != SCHEMA_VERSION:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "schema_version", "kind": "version"})
    return WaveManifest(
        SCHEMA_VERSION,
        _required_string(item["supervisor_run_id"], _ID_RE, label="supervisor_run_id"),
        _required_int(item["wave_index"], label="wave_index"),
        _absolute_path(item["worktree"], label="worktree"),
        _absolute_path(item["main_worktree"], label="main_worktree"),
        _required_string(item["base_main_sha"], _HEX40_RE, label="base_main_sha"),
        _required_string(item["receipt_schema_sha256"], _HEX64_RE, label="receipt_schema_sha256"),
    )


def parse_worker_spec(raw: bytes) -> WorkerSpec:
    item = _strict_argument_loads(
        raw, label="worker-spec", allowed_fields=_WORKER_SPEC_FIELDS,
    )
    item = _closed_object(item, _WORKER_SPEC_FIELDS, label="worker-spec")
    if item["schema_version"] != SCHEMA_VERSION:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "schema_version", "kind": "version"})
    environment = item["environment"]
    if not isinstance(environment, dict) or not set(environment) <= WORKER_ENV_ALLOWED_KEYS:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "environment", "kind": "field-set"})
    for key, value in environment.items():
        if not isinstance(value, str) or "\x00" in value or len(value) > MAX_JSON_STRING_CHARS:
            raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "environment", "kind": "value"})
    schema_text = item["receipt_schema_json"]
    if not isinstance(schema_text, str):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "receipt_schema_json", "kind": "string"})
    schema_value = _strict_argument_loads(
        schema_text.encode("utf-8"), label="worker-receipt-schema",
    )
    if canonical_bytes(schema_value).decode("utf-8") != schema_text:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "receipt_schema_json", "kind": "noncanonical"})
    schema_digest = _required_string(
        item["receipt_schema_sha256"], _HEX64_RE, label="receipt_schema_sha256",
    )
    if hashlib.sha256(schema_text.encode("utf-8")).hexdigest() != schema_digest:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "receipt_schema_sha256", "kind": "digest"})
    budget = parse_decimal_string(item["per_wave_budget_usd"], label="per_wave_budget_usd")
    if budget <= 0:
        raise DevWavesError(ReasonCode.BUDGET_INVALID, {"label": "per_wave_budget_usd", "kind": "non-positive"})
    model = _required_string(item["model"], _MODEL_RE, label="model")
    effort = _required_string(item["effort"], _EFFORT_RE, label="effort")
    return WorkerSpec(
        SCHEMA_VERSION,
        _required_string(item["supervisor_run_id"], _ID_RE, label="supervisor_run_id"),
        _required_int(item["wave_index"], label="wave_index"),
        _absolute_path(item["executable_path"], label="executable_path"),
        _required_string(item["executable_sha256"], _HEX64_RE, label="executable_sha256"),
        _absolute_path(item["cwd"], label="cwd"), tuple(sorted(environment.items())),
        model, effort, _absolute_path(item["main_worktree"], label="main_worktree"),
        _absolute_path(item["wave_manifest_path"], label="wave_manifest_path"),
        schema_text, schema_digest, budget,
        _required_int(item["per_wave_timeout_s"], label="per_wave_timeout_s"),
        _required_int(item["max_wave_output_bytes"], label="max_wave_output_bytes"),
        _required_int(item["max_run_bytes"], label="max_run_bytes"),
        _absolute_path(item["stdout_path"], label="stdout_path"),
        _absolute_path(item["stderr_path"], label="stderr_path"),
        _absolute_path(item["child_start_path"], label="child_start_path"),
        _absolute_path(item["worker_exit_path"], label="worker_exit_path"),
    )


CHILD_ARGV_REQUIRED_TOKENS = (
    "-p", "--model=", "--effort=", "--permission-mode=auto",
    "--output-format=json", "--json-schema=", "--max-budget-usd=", "--add-dir=",
)
CHILD_ARGV_FORBIDDEN_TOKENS = frozenset({
    "--continue", "--resume", "--no-session-persistence",
    "--dangerously-skip-permissions", "bypassPermissions", "dontAsk",
    "--permission-mode=bypassPermissions", "--permission-mode=dontAsk",
})
_MODEL_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+\Z")
_EFFORT_RE = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")


def validate_child_argv(argv: Sequence[str]) -> None:
    """Validate the one exact fake-child argv grammar (prompt is final token)."""
    if isinstance(argv, (str, bytes)) or len(argv) != len(CHILD_ARGV_REQUIRED_TOKENS) + 1:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "length"})
    if not all(isinstance(token, str) and token and "\x00" not in token for token in argv):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "token"})
    if any(token in CHILD_ARGV_FORBIDDEN_TOKENS for token in argv):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "forbidden"})
    if argv[0] != "-p" or argv[3] != "--permission-mode=auto" or argv[4] != "--output-format=json":
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "fixed-token"})
    for index in (1, 2, 5, 6, 7):
        if not argv[index].startswith(CHILD_ARGV_REQUIRED_TOKENS[index]):
            raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "option-order"})
    model = argv[1].split("=", 1)[1]
    effort = argv[2].split("=", 1)[1]
    schema_text = argv[5].split("=", 1)[1]
    budget = argv[6].split("=", 1)[1]
    main_worktree = argv[7].split("=", 1)[1]
    if not _MODEL_RE.fullmatch(model) or not _EFFORT_RE.fullmatch(effort):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "model-effort"})
    schema_value = _strict_argument_loads(
        schema_text.encode("utf-8"), label="argv-json-schema",
    )
    if canonical_bytes(schema_value).decode("utf-8") != schema_text:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "noncanonical-schema"})
    parse_decimal_string(budget, label="max-budget-usd")
    if not os.path.isabs(main_worktree):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "add-dir"})
    prompt_prefix = "/dev-wave --supervised-manifest "
    prompt = argv[8]
    if not prompt.startswith(prompt_prefix) or not os.path.isabs(prompt[len(prompt_prefix):]):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "prompt"})


__all__ = [
    "ALLOWED_TRANSITIONS", "CHILD_ARGV_FORBIDDEN_TOKENS", "CHILD_ARGV_REQUIRED_TOKENS",
    "CancelRequest", "CancelResponse", "DEFAULT_MAX_JSON_BYTES", "DevWavesError",
    "ErrorResponse", "MAX_JSON_DECIMAL", "MAX_JSON_DEPTH", "MAX_JSON_INTEGER",
    "MAX_JSON_STRING_CHARS", "NONTERMINAL_STATES", "Outcome", "PROTOCOL_VERSION",
    "ReasonCode", "Receipt", "Request", "ResourceLimits", "Response", "RunManifest",
    "RunState", "SCHEMA_VERSION", "StatusRequest", "StatusResponse", "SubmitRequest",
    "SubmitResponse", "TERMINAL_STATES", "WORKER_ENV_ALLOWED_KEYS", "WaveManifest",
    "WorkerSpec", "canonical_bytes", "canonical_decimal", "encode_response",
    "parse_decimal_string", "parse_request", "parse_response", "parse_run_manifest",
    "parse_wave_manifest", "parse_worker_spec", "strict_loads", "validate_child_argv",
    "is_run_id", "is_task_id", "validate_limits", "validate_transition",
]
