# -*- coding: utf-8 -*-
"""task-run/v1 の strict JSON parser と schema/invariant 検査。"""
from __future__ import annotations

import hashlib
import json
import math
import re
import stat
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "task-run/v1"
MAX_TASK_BYTES = 16 * 1024
MAX_LINE_BYTES = 16 * 1024
MAX_EVENTS_BYTES = 8 * 1024 * 1024
MAX_EVENTS = 10_000
MAX_DURATION_S = 10_000_000

SAFE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
RUN_ID_RE = re.compile(r"^[0-9]{8}-[a-z0-9](?:[a-z0-9-]{0,46}[a-z0-9])?-[0-9a-f]{8}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EVENT_ID_RE = re.compile(r"^[0-9a-f]{16}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{12}$")

TASK_CLASSES = {1, 2, 3}
TASK_KINDS = {
    "implementation", "audit-review", "investigation", "documentation",
    "integration", "other",
}
STAGES = {
    "planning", "research", "implementation", "test", "review",
    "documentation", "integration", "other",
}
EVENT_TYPES = {
    "stage_start", "stage_end", "agent_run", "test_run", "wait",
    "finding_summary", "commit", "rework", "task_end",
}

MEASUREMENT_POLICY = {
    "mode": "pilot",
    "max_task_runs": 10,
    "max_days": 14,
    "writer_failure": "fail-open",
    "token_values": "actual-or-null",
    "token_estimates": "prohibited",
    "sensitive_content": "prohibited",
    "test_recording": "explicit-opt-in",
}


class LedgerError(Exception):
    """task-run 操作を安全に完遂できない。"""


class DamagedRunError(LedgerError):
    """schema または record 間 invariant に違反した run。"""


@dataclass(frozen=True)
class ValidatedRun:
    """完全検査済み task-run の読み取り view。"""

    path: Path
    task: Mapping[str, object]
    events: tuple[Mapping[str, object], ...]
    is_finished: bool
    open_stage_id: str | None
    task_bytes_sha256: str
    events_bytes_sha256: str
    final_seq: int


def _fail(message: str) -> None:
    raise DamagedRunError(message)


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    _fail(f"非有限数は禁止: {value}")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("非有限数は禁止")
    return parsed


def _check_json_domain(value: Any, *, label: str) -> None:
    stack = [value]
    while stack:
        item = stack.pop()
        if item is None or isinstance(item, (str, bool, int)):
            if isinstance(item, str) and unicodedata.normalize("NFC", item) != item:
                _fail(f"{label}: string は Unicode NFC でなければならない")
            continue
        if isinstance(item, float):
            if not math.isfinite(item):
                _fail(f"{label}: 非有限数は禁止")
            continue
        if isinstance(item, list):
            stack.extend(item)
            continue
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    _fail(f"{label}: object key は string でなければならない")
                if unicodedata.normalize("NFC", key) != key:
                    _fail(f"{label}: object key は Unicode NFC でなければならない")
                stack.append(child)
            continue
        _fail(f"{label}: JSON domain 外の型: {type(item).__name__}")


def strict_json_loads(raw: bytes, *, label: str, max_bytes: int) -> Any:
    """UTF-8/BOM/NUL/CR/NFC/duplicate/non-finite を fail-closed で検査する。"""

    if not raw or len(raw) > max_bytes:
        _fail(f"{label}: size 不正 ({len(raw)} bytes, max={max_bytes})")
    if raw.startswith(b"\xef\xbb\xbf"):
        _fail(f"{label}: BOM は禁止")
    if b"\x00" in raw:
        _fail(f"{label}: NUL は禁止")
    if b"\r" in raw:
        _fail(f"{label}: CR は禁止")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise DamagedRunError(f"{label}: UTF-8 不正: {exc}") from exc
    if unicodedata.normalize("NFC", text) != text:
        _fail(f"{label}: Unicode NFC でなければならない")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except DamagedRunError:
        raise
    except (json.JSONDecodeError, ValueError, OverflowError, RecursionError) as exc:
        raise DamagedRunError(f"{label}: JSON parse 失敗: {exc}") from exc
    _check_json_domain(value, label=label)
    return value


@lru_cache(maxsize=1)
def load_schema() -> Mapping[str, Any]:
    """同梱 Draft 7 schema を読み、利用可能なら meta-schema も検査する。"""

    path = Path(__file__).with_name("schema_v1.json")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise LedgerError(f"schema を読めない: {path}: {exc}") from exc
    document = strict_json_loads(raw, label="schema_v1.json", max_bytes=256 * 1024)
    if not isinstance(document, dict) or document.get("$schema") != "http://json-schema.org/draft-07/schema#":
        raise LedgerError("schema_v1.json は Draft 7 schema でない")
    try:
        import jsonschema  # type: ignore[import-not-found]
    except ImportError:
        # 自前検査は常に実行される。依存不在を検査縮退にはしない。
        pass
    else:
        try:
            jsonschema.Draft7Validator.check_schema(document)
        except Exception as exc:  # pragma: no cover - 壊れた同梱 schema の防壁
            raise LedgerError(f"schema_v1.json 自体が不正: {exc}") from exc
    return document


def parse_timestamp(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        _fail(f"{label}: timestamp は non-empty string でなければならない")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise DamagedRunError(f"{label}: timestamp を解釈できない: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(f"{label}: timezone 無し timestamp は禁止")
    return parsed


def _exact_keys(obj: Mapping[str, Any], required: set[str], optional: set[str], *, label: str) -> None:
    keys = set(obj)
    missing = required - keys
    extra = keys - required - optional
    if missing:
        _fail(f"{label}: required field 不足: {sorted(missing)}")
    if extra:
        _fail(f"{label}: unknown field: {sorted(extra)}")


def _string(value: Any, *, label: str, values: set[str] | None = None) -> str:
    if not isinstance(value, str):
        _fail(f"{label}: string でなければならない")
    if values is not None and value not in values:
        _fail(f"{label}: 許可外の値: {value!r}")
    return value


def _slug(value: Any, *, label: str) -> str:
    text = _string(value, label=label)
    if SAFE_SLUG_RE.fullmatch(text) is None:
        _fail(f"{label}: safe slug でない: {text!r}")
    return text


def _number(value: Any, *, label: str, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label}: number でなければならない")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        _fail(f"{label}: finite number >= {minimum} でなければならない")
    return result


def _duration(value: Any, *, label: str) -> float:
    result = _number(value, label=label)
    if result > MAX_DURATION_S:
        _fail(f"{label}: duration は {MAX_DURATION_S} 秒以下でなければならない")
    if abs(result - round(result, 3)) > 0.000_000_1:
        _fail(f"{label}: duration は ms 精度 (小数3桁以内) でなければならない")
    return result


def _integer(value: Any, *, label: str, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail(f"{label}: non-negative integer{('|null' if nullable else '')} でなければならない")
    return value


def validate_pilot(pilot: Any) -> Mapping[str, Any]:
    if not isinstance(pilot, dict):
        _fail("pilot.json: object でなければならない")
    _check_json_domain(pilot, label="pilot.json")
    _exact_keys(
        pilot,
        {"schema_version", "pilot_started_at", "max_task_runs", "max_days"},
        set(), label="pilot.json",
    )
    if pilot["schema_version"] != SCHEMA_VERSION:
        _fail("pilot.json: unknown schema_version")
    parse_timestamp(pilot["pilot_started_at"], label="pilot.json.pilot_started_at")
    if pilot["max_task_runs"] != 10 or pilot["max_days"] != 14:
        _fail("pilot.json: pilot cap は 10 runs / 14 days 固定")
    return pilot


def validate_task(task: Any, *, directory_name: str | None = None) -> Mapping[str, Any]:
    if not isinstance(task, dict):
        _fail("task.json: object でなければならない")
    _check_json_domain(task, label="task.json")
    required = {
        "schema_version", "task_run_id", "objective", "task_class", "task_kind",
        "started_at", "base_commit", "base_commit_source", "authority",
        "measurement_policy",
    }
    _exact_keys(task, required, set(), label="task.json")
    if task["schema_version"] != SCHEMA_VERSION:
        _fail("task.json: unknown schema_version")
    task_run_id = _string(task["task_run_id"], label="task.json.task_run_id")
    if RUN_ID_RE.fullmatch(task_run_id) is None:
        _fail("task.json.task_run_id: format 不正")
    try:
        datetime.strptime(task_run_id[:8], "%Y%m%d")
    except ValueError as exc:
        raise DamagedRunError("task.json.task_run_id: YYYYMMDD が実在日でない") from exc
    if directory_name is not None and task_run_id != directory_name:
        _fail("directory 名と task_run_id が一致しない")
    objective = _string(task["objective"], label="task.json.objective")
    if not 1 <= len(objective) <= 240 or "\n" in objective or "\r" in objective or "://" in objective:
        _fail("task.json.objective: 1..240 文字の単一行かつ URI 禁止")
    if (
        isinstance(task["task_class"], bool)
        or not isinstance(task["task_class"], int)
        or task["task_class"] not in TASK_CLASSES
    ):
        _fail("task.json.task_class: 1/2/3 のいずれでもない")
    _string(task["task_kind"], label="task.json.task_kind", values=TASK_KINDS)
    parse_timestamp(task["started_at"], label="task.json.started_at")
    if not isinstance(task["base_commit"], str) or SHA_RE.fullmatch(task["base_commit"]) is None:
        _fail("task.json.base_commit: lowercase 40 hex でない")
    if task["base_commit_source"] != "git-observed":
        _fail("task.json.base_commit_source: git-observed 固定")
    if task["authority"] != "development-observation-not-evidence":
        _fail("task.json.authority: 開発観測 namespace でない")
    if task["measurement_policy"] != MEASUREMENT_POLICY:
        _fail("task.json.measurement_policy: pilot policy と一致しない")
    return task


_COMMON_FIELDS = {
    "schema_version", "task_run_id", "seq", "timestamp", "event", "event_id",
    "measurement_source",
}

_EVENT_FIELDS: dict[str, set[str]] = {
    "stage_start": {"stage_id", "stage"},
    "stage_end": {"stage_id", "stage", "outcome", "duration_s"},
    "agent_run": {
        "stage_id", "agent_run_id", "product", "model", "reasoning", "role",
        "scope", "status", "duration_s", "tokens",
    },
    "test_run": {
        "stage_id", "suite_id", "suite_kind", "duration_s", "collected", "passed",
        "failed", "skipped", "exit_status", "trigger", "collected_node_digest",
    },
    "wait": {"wait_kind", "duration_s"},
    "finding_summary": {
        "stage_id", "review_id", "review_kind", "real", "refuted", "unresolved",
    },
    "commit": {"commit_sha", "relation"},
    "rework": {"stage_id", "rework_id", "cause", "duration_s"},
    "task_end": {"outcome"},
}


def _validate_source(event: str, source: Any, *, token_values: Sequence[Any] | None = None) -> None:
    if not isinstance(source, dict):
        _fail("measurement_source: object でなければならない")
    _exact_keys(source, {"timestamp", "duration", "metrics", "tokens"}, set(), label="measurement_source")
    if source["timestamp"] != "system-clock":
        _fail("measurement_source.timestamp: system-clock 固定")
    allowed: dict[str, set[tuple[str, str, str]]] = {
        "stage_start": {("not-applicable", "not-applicable", "not-applicable")},
        "stage_end": {("timestamp-delta", "not-applicable", "not-applicable")},
        "agent_run": {
            ("caller-supplied", "caller-supplied", "not-exposed"),
            ("caller-supplied", "caller-supplied", "product-reported"),
            ("monotonic-clock", "wrapper-observed", "not-exposed"),
            ("monotonic-clock", "wrapper-observed", "product-reported"),
        },
        "test_run": {
            ("caller-supplied", "caller-supplied", "not-applicable"),
            ("monotonic-clock", "wrapper-observed", "not-applicable"),
            ("monotonic-clock", "tool-reported", "not-applicable"),
        },
        "wait": {("caller-supplied", "not-applicable", "not-applicable")},
        "finding_summary": {("not-applicable", "caller-supplied", "not-applicable")},
        "commit": {("not-applicable", "git-observed", "not-applicable")},
        "rework": {("caller-supplied", "not-applicable", "not-applicable")},
        "task_end": {("not-applicable", "not-applicable", "not-applicable")},
    }
    triple = (source["duration"], source["metrics"], source["tokens"])
    if not all(isinstance(value, str) for value in triple):
        _fail(f"{event}: measurement_source の各値は string でなければならない")
    if triple not in allowed[event]:
        _fail(f"{event}: measurement_source の組合せが許可外: {triple!r}")
    if event == "agent_run" and token_values is not None:
        any_value = any(value is not None for value in token_values)
        if source["tokens"] == "not-exposed" and any_value:
            _fail("agent_run: tokens=not-exposed なのに実値がある")
        if source["tokens"] == "product-reported" and not any_value:
            _fail("agent_run: product-reported なのに token 実値がない")


def _validate_tokens(tokens: Any) -> tuple[Any, ...]:
    if not isinstance(tokens, dict):
        _fail("tokens: object でなければならない")
    names = {"input_tokens", "output_tokens", "cached_tokens", "total_tokens"}
    _exact_keys(tokens, names, set(), label="tokens")
    values = tuple(_integer(tokens[name], label=f"tokens.{name}", nullable=True) for name in sorted(names))
    input_tokens = tokens["input_tokens"]
    output_tokens = tokens["output_tokens"]
    cached_tokens = tokens["cached_tokens"]
    total_tokens = tokens["total_tokens"]
    if cached_tokens is not None and input_tokens is not None and cached_tokens > input_tokens:
        _fail("tokens.cached_tokens は input_tokens の内数でなければならない")
    if total_tokens is not None and input_tokens is not None and total_tokens < input_tokens:
        _fail("tokens.total_tokens は input_tokens 以上でなければならない")
    if total_tokens is not None and output_tokens is not None and total_tokens < output_tokens:
        _fail("tokens.total_tokens は output_tokens 以上でなければならない")
    if input_tokens is not None and output_tokens is not None and total_tokens is not None:
        if total_tokens != input_tokens + output_tokens:
            _fail("tokens.total_tokens != input_tokens + output_tokens")
    return values


def validate_event_shape(event: Any) -> Mapping[str, Any]:
    if not isinstance(event, dict):
        _fail("event record は object でなければならない")
    _check_json_domain(event, label="event record")
    event_type = event.get("event")
    if not isinstance(event_type, str) or event_type not in EVENT_TYPES:
        _fail(f"unknown event: {event_type!r}")
    _exact_keys(event, _COMMON_FIELDS | _EVENT_FIELDS[event_type], {"recording_duration_s"}, label=event_type)
    if event["schema_version"] != SCHEMA_VERSION:
        _fail(f"{event_type}: unknown schema_version")
    if not isinstance(event["task_run_id"], str) or RUN_ID_RE.fullmatch(event["task_run_id"]) is None:
        _fail(f"{event_type}: task_run_id format 不正")
    if isinstance(event["seq"], bool) or not isinstance(event["seq"], int) or event["seq"] < 1:
        _fail(f"{event_type}: seq は 1 以上の integer")
    parse_timestamp(event["timestamp"], label=f"{event_type}.timestamp")
    if not isinstance(event["event_id"], str) or EVENT_ID_RE.fullmatch(event["event_id"]) is None:
        _fail(f"{event_type}: event_id は 16 lowercase hex")
    if "recording_duration_s" in event:
        _duration(event["recording_duration_s"], label=f"{event_type}.recording_duration_s")

    tokens_values: tuple[Any, ...] | None = None
    if event_type == "stage_start":
        _slug(event["stage_id"], label="stage_start.stage_id")
        _string(event["stage"], label="stage_start.stage", values=STAGES)
    elif event_type == "stage_end":
        _slug(event["stage_id"], label="stage_end.stage_id")
        _string(event["stage"], label="stage_end.stage", values=STAGES)
        _string(event["outcome"], label="stage_end.outcome", values={"completed", "failed", "interrupted"})
        _duration(event["duration_s"], label="stage_end.duration_s")
    elif event_type == "agent_run":
        if event["stage_id"] is not None:
            _slug(event["stage_id"], label="agent_run.stage_id")
        for name in ("agent_run_id", "product", "model", "reasoning"):
            _slug(event[name], label=f"agent_run.{name}")
        _string(event["role"], label="agent_run.role", values={"author", "reviewer", "researcher", "manager", "integrator"})
        if event["scope"] is not None:
            _slug(event["scope"], label="agent_run.scope")
        _string(event["status"], label="agent_run.status", values={"completed", "failed", "cancelled", "timed-out"})
        _duration(event["duration_s"], label="agent_run.duration_s")
        tokens_values = _validate_tokens(event["tokens"])
    elif event_type == "test_run":
        if event["stage_id"] is not None:
            _slug(event["stage_id"], label="test_run.stage_id")
        _slug(event["suite_id"], label="test_run.suite_id")
        _string(event["suite_kind"], label="test_run.suite_kind", values={"targeted", "full", "docs-check", "provenance-check", "static-check"})
        _duration(event["duration_s"], label="test_run.duration_s")
        for name in ("collected", "passed", "failed", "skipped"):
            _integer(event[name], label=f"test_run.{name}", nullable=True)
        if isinstance(event["exit_status"], bool) or not isinstance(event["exit_status"], int):
            _fail("test_run.exit_status: integer でなければならない")
        _string(event["trigger"], label="test_run.trigger", values={"baseline", "after-change", "after-failure", "final", "review-fix", "unspecified"})
        digest = event["collected_node_digest"]
        if digest is not None and (not isinstance(digest, str) or DIGEST_RE.fullmatch(digest) is None):
            _fail("test_run.collected_node_digest: null または 12 lowercase hex")
    elif event_type == "wait":
        _string(event["wait_kind"], label="wait.wait_kind", values={"user", "approval", "scheduler", "resource", "tool", "external", "other"})
        _duration(event["duration_s"], label="wait.duration_s")
    elif event_type == "finding_summary":
        if event["stage_id"] is not None:
            _slug(event["stage_id"], label="finding_summary.stage_id")
        _slug(event["review_id"], label="finding_summary.review_id")
        _string(event["review_kind"], label="finding_summary.review_kind", values={"self", "independent", "user", "automated"})
        for name in ("real", "refuted", "unresolved"):
            _integer(event[name], label=f"finding_summary.{name}")
    elif event_type == "commit":
        if not isinstance(event["commit_sha"], str) or SHA_RE.fullmatch(event["commit_sha"]) is None:
            _fail("commit.commit_sha: lowercase 40 hex でない")
        _string(event["relation"], label="commit.relation", values={"authored", "integrated", "referenced"})
    elif event_type == "rework":
        if event["stage_id"] is not None:
            _slug(event["stage_id"], label="rework.stage_id")
        _slug(event["rework_id"], label="rework.rework_id")
        _string(event["cause"], label="rework.cause", values={"test-failure", "review-finding", "requirement-change", "integration-conflict", "implementation-defect", "other"})
        _duration(event["duration_s"], label="rework.duration_s")
    elif event_type == "task_end":
        _string(event["outcome"], label="task_end.outcome", values={"completed", "blocked", "abandoned", "interrupted"})
    _validate_source(event_type, event["measurement_source"], token_values=tokens_values)
    return event


def parse_events(raw: bytes) -> tuple[Mapping[str, Any], ...]:
    """0 byte の初期 stream を許容し、それ以外は完全な JSONL のみ受理する。"""

    if len(raw) > MAX_EVENTS_BYTES:
        _fail(f"events.jsonl: file size 上限超過 ({len(raw)} > {MAX_EVENTS_BYTES})")
    if raw == b"":
        return ()
    if not raw.endswith(b"\n"):
        _fail("events.jsonl: 最終 newline が無い (truncate を含む)")
    lines = raw.split(b"\n")[:-1]
    if len(lines) > MAX_EVENTS:
        _fail(f"events.jsonl: event 数上限超過 ({len(lines)} > {MAX_EVENTS})")
    events: list[Mapping[str, Any]] = []
    for lineno, line in enumerate(lines, 1):
        if not line:
            _fail(f"events.jsonl:{lineno}: 空行は禁止")
        value = strict_json_loads(line, label=f"events.jsonl:{lineno}", max_bytes=MAX_LINE_BYTES)
        events.append(validate_event_shape(value))
    return tuple(events)


def validate_documents(
    run_dir: Path,
    task: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    *,
    require_finished: bool = False,
    task_raw: bytes | None = None,
    events_raw: bytes | None = None,
) -> ValidatedRun:
    """task と全 event の record 間 invariant を検査する。"""

    validate_task(task, directory_name=run_dir.name)
    started_at = parse_timestamp(task["started_at"], label="task.json.started_at")
    previous = started_at
    seen_event_ids: set[str] = set()
    seen_stage_ids: set[str] = set()
    seen_agent_ids: set[str] = set()
    seen_review_ids: set[str] = set()
    seen_rework_ids: set[str] = set()
    open_stage: Mapping[str, Any] | None = None
    task_end_seen = False

    for index, event in enumerate(events, 1):
        validate_event_shape(event)
        if event["task_run_id"] != task["task_run_id"]:
            _fail(f"event[{index}]: task_run_id が directory/task と一致しない")
        if event["seq"] != index:
            _fail(f"event[{index}]: seq は {index} でなければならない (実値 {event['seq']!r})")
        event_id = event["event_id"]
        if event_id in seen_event_ids:
            _fail(f"event[{index}]: duplicate event_id: {event_id}")
        seen_event_ids.add(event_id)
        timestamp = parse_timestamp(event["timestamp"], label=f"event[{index}].timestamp")
        if timestamp < started_at:
            _fail(f"event[{index}]: started_at より前")
        if timestamp < previous:
            _fail(f"event[{index}]: timestamp が逆行")
        previous = timestamp
        event_type = event["event"]
        if task_end_seen and event_type != "commit":
            _fail(f"event[{index}]: task_end 後は commit 以外を記録できない")

        if event_type == "stage_start":
            stage_id = event["stage_id"]
            if open_stage is not None:
                _fail(f"event[{index}]: stage overlap")
            if stage_id in seen_stage_ids:
                _fail(f"event[{index}]: stage_id 再利用: {stage_id}")
            seen_stage_ids.add(stage_id)
            open_stage = event
        elif event_type == "stage_end":
            if open_stage is None:
                _fail(f"event[{index}]: open stage の無い stage_end")
            if event["stage_id"] != open_stage["stage_id"] or event["stage"] != open_stage["stage"]:
                _fail(f"event[{index}]: stage_end が現在の stage と一致しない")
            opened_at = parse_timestamp(open_stage["timestamp"], label="stage_start.timestamp")
            expected = round((timestamp - opened_at).total_seconds(), 3)
            if abs(float(event["duration_s"]) - expected) > 0.000_5:
                _fail(f"event[{index}]: stage duration は timestamp delta と一致しない")
            open_stage = None
        elif event_type in {"agent_run", "test_run", "finding_summary", "rework"}:
            stage_id = event["stage_id"]
            if stage_id is not None and stage_id not in seen_stage_ids:
                _fail(f"event[{index}]: 存在しない stage_id 参照: {stage_id}")

        if event_type == "agent_run":
            identity = event["agent_run_id"]
            if identity in seen_agent_ids:
                _fail(f"event[{index}]: duplicate agent_run_id: {identity}")
            seen_agent_ids.add(identity)
        elif event_type == "finding_summary":
            identity = event["review_id"]
            if identity in seen_review_ids:
                _fail(f"event[{index}]: duplicate review_id: {identity}")
            seen_review_ids.add(identity)
        elif event_type == "rework":
            identity = event["rework_id"]
            if identity in seen_rework_ids:
                _fail(f"event[{index}]: duplicate rework_id: {identity}")
            seen_rework_ids.add(identity)
        elif event_type == "task_end":
            if task_end_seen:
                _fail(f"event[{index}]: duplicate task_end")
            if open_stage is not None:
                _fail(f"event[{index}]: open stage を残して task_end できない")
            task_end_seen = True

    if require_finished and not task_end_seen:
        _fail("require_finished=True だが task_end が無い")
    if require_finished and open_stage is not None:
        _fail("require_finished=True だが open stage がある")
    return ValidatedRun(
        path=run_dir,
        task=task,
        events=tuple(events),
        is_finished=task_end_seen,
        open_stage_id=None if open_stage is None else str(open_stage["stage_id"]),
        task_bytes_sha256=hashlib.sha256(
            task_raw if task_raw is not None else (
                json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
                + "\n"
            ).encode("utf-8")
        ).hexdigest(),
        events_bytes_sha256=hashlib.sha256(
            events_raw if events_raw is not None else b"".join(
                (
                    json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    + "\n"
                ).encode("utf-8")
                for event in events
            )
        ).hexdigest(),
        final_seq=int(events[-1]["seq"]) if events else 0,
    )


def ensure_regular_fd(fd: int, *, label: str) -> None:
    """open 後の同一 fd が regular file であることを確認する。"""

    import os

    mode = os.fstat(fd).st_mode
    if not stat.S_ISREG(mode):
        _fail(f"{label}: regular file でない")
