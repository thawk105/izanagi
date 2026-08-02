"""Allowlist-based sanitizing for dev-wave durable and exported artifacts.

Raw child output is deliberately outside this module's remit: it remains in a
private runtime file.  Values which cross into manifests, WAL details, errors,
or exports must first be rebuilt through the functions here.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import AbstractSet, Any, Mapping, Sequence


REDACTED = "<redacted>"

# This is intentionally an allowlist, not a list of names believed dangerous.
# Adding a new durable field therefore requires an explicit review here.
SANITIZED_FIELD_ALLOWLIST = frozenset({
    "action", "actual", "after_main_sha", "argv", "argv_digest",
    "artifact", "base_main_sha", "before_main_sha", "boot_id", "byte_length", "code",
    "child_task_run_id", "created_utc", "cwd", "detail", "digest", "elapsed_s", "expected",
    "executable_sha256", "field", "fold_commit_sha", "kind", "label", "landed_commits",
    "landed_main_sha", "length", "limits", "main_worktree", "max_run_bytes",
    "max_wave_output_bytes", "max_waves", "message", "observed", "operation",
    "outcome", "path", "per_wave_budget_usd", "per_wave_timeout_s", "profile",
    "deadline_ns", "next_task_ids", "pid", "protocol_version", "reason",
    "repo_identity", "request_digest",
    "run_id", "schema_version", "selected_task_ids", "sha256", "state", "status", "stop_reason",
    "supervisor_run_id", "target", "task_ids", "total_budget_usd",
    "start_ticks", "started_ns", "total_cost_usd", "total_timeout_s", "wave_index", "worktree",
})

DEFAULT_SENSITIVE_OPTIONS = frozenset({
    "--api-key", "--authorization", "--credential", "--password", "--secret",
    "--session-id", "--session-url", "--token",
})

# Exception detail has a narrower surface than durable artifacts.  In
# particular, observed/expected/path/message values are never copied because
# they may be raw child or OS data even when their field name looks ordinary.
ERROR_DETAIL_ALLOWLIST = frozenset({
    "action", "byte_length", "code", "digest", "field", "kind", "label",
    "length", "reason", "sha256", "state", "status", "target", "wave_index",
})

_SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|auth(?:orization)?|cookie|credential|environment|password|"
    r"secret|session(?:[_-]?(?:id|url))?|token|xdg|home)", re.IGNORECASE,
)
_SENSITIVE_TEXT = (
    re.compile(r"\b(?:https?|ssh|git)://\S+", re.IGNORECASE),
    re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
    re.compile(r"\b(?:sk|gh[opusr]|glpat)-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bsession(?:[_-]?(?:id|url))?[=:][^\s,;]+", re.IGNORECASE),
)


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Path):
        return str(value)
    return value


def _safe_string(value: str) -> str:
    if any(pattern.search(value) for pattern in _SENSITIVE_TEXT):
        return REDACTED
    return value


def redact_value(
    value: Any,
    *,
    allowed_keys: AbstractSet[str] = SANITIZED_FIELD_ALLOWLIST,
) -> Any:
    """Return a JSON-compatible value built only from reviewed field names.

    Unknown mapping fields are omitted.  Sensitive names are omitted even if a
    caller accidentally adds one to an extended allowlist.  Sequence order is
    retained, while URL/token-looking scalar strings are replaced.
    """
    value = _plain(value)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else REDACTED
    if isinstance(value, str):
        return _safe_string(value)
    if isinstance(value, Mapping):
        clean = {}
        for raw_key, raw_value in value.items():
            if not isinstance(raw_key, str):
                continue
            if raw_key not in allowed_keys or _SENSITIVE_KEY.search(raw_key):
                continue
            clean[raw_key] = redact_value(raw_value, allowed_keys=allowed_keys)
        return clean
    if isinstance(value, (list, tuple)):
        return [redact_value(item, allowed_keys=allowed_keys) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [redact_value(item, allowed_keys=allowed_keys) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True))
    return REDACTED


def redact_argv(
    argv: Sequence[str],
    sensitive_options: AbstractSet[str] = DEFAULT_SENSITIVE_OPTIONS,
) -> tuple[str, ...]:
    """Redact option values without changing argv token boundaries."""
    result = []
    hide_next = False
    for token in argv:
        if not isinstance(token, str):
            raise TypeError("argv tokens must be strings")
        if hide_next:
            result.append(REDACTED)
            hide_next = False
            continue
        matched = False
        for option in sensitive_options:
            if token == option:
                result.append(option)
                hide_next = True
                matched = True
                break
            prefix = option + "="
            if token.startswith(prefix):
                result.append(prefix + REDACTED)
                matched = True
                break
        if not matched:
            result.append(_safe_string(token))
    return tuple(result)


def safe_digest(value: Any) -> str:
    """Hash the sanitized representation, never the raw representation."""
    clean = redact_value(value)
    raw = json.dumps(
        clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sanitize_detail(value: Any) -> Any:
    """Build an exception-safe detail without copying arbitrary raw strings."""
    if isinstance(value, Mapping):
        return redact_value(value, allowed_keys=ERROR_DETAIL_ALLOWLIST)
    if value is None:
        return None
    # Free-form exception text often embeds a path, URL, token, or child bytes.
    # Keep correlation evidence without retaining the value itself.
    raw = str(value).encode("utf-8", errors="replace")
    return {
        "kind": "detail-omitted",
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def assert_sanitized(value: Any) -> None:
    """Raise ValueError if *value* is not already a sanitized allowlist view."""
    def visit(item: Any) -> None:
        item = _plain(item)
        if item is None or isinstance(item, (bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError("non-finite number in sanitized artifact")
            return
        if isinstance(item, str):
            if _safe_string(item) != item:
                raise ValueError("sensitive string in sanitized artifact")
            return
        if isinstance(item, Mapping):
            for key, child in item.items():
                if not isinstance(key, str) or key not in SANITIZED_FIELD_ALLOWLIST:
                    raise ValueError("non-allowlisted field in sanitized artifact")
                if _SENSITIVE_KEY.search(key):
                    raise ValueError("sensitive field in sanitized artifact")
                visit(child)
            return
        if isinstance(item, (list, tuple)):
            for child in item:
                visit(child)
            return
        raise ValueError("non-JSON value in sanitized artifact")

    visit(value)


__all__ = [
    "DEFAULT_SENSITIVE_OPTIONS", "ERROR_DETAIL_ALLOWLIST", "REDACTED",
    "SANITIZED_FIELD_ALLOWLIST",
    "assert_sanitized", "redact_argv", "redact_value", "safe_digest",
    "sanitize_detail",
]
