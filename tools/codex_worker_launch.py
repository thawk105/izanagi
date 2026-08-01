#!/usr/bin/env python3
"""Codex worker launcher process を bounded に実行し receipt を残す。

wall-clock の監督範囲は launcher process 自身であり、別 session へ
``setsid()`` した子 process の封じ込めまでは保証しない。``check-receipt`` は
実行を伴わないため、記録済み ``codex_version`` を再取得せず executable hash
だけを再束縛する。
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


_LAUNCHER_PROCESS_STARTED_NS = time.monotonic_ns()
_ROOT = Path(__file__).resolve().parents[1]
if os.fspath(_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_ROOT))

from orchestrator.codex_roles.events import (  # noqa: E402
    EventValidationError,
    parse_jsonl,
    strict_json_loads,
)
from tools import check_codex_output as _validator  # noqa: E402
from tools.dev_waves.schema import (  # noqa: E402
    DevWavesError,
    canonical_bytes,
    strict_loads,
)
from tools.dev_waves.worker import (  # noqa: E402
    PidIdentity,
    read_pid_identity,
    terminate_verified_group,
)


_MAX_JSON_BYTES = 16 * 1024 * 1024
_MAX_EVENT_LINE_BYTES = 4 * 1024 * 1024
_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,128}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_LIMIT_REASONS = (
    "max_wall_clock_s",
    "max_model_calls",
    "max_cli_reported_tokens",
)
_STOP_REASONS = _LIMIT_REASONS + (
    "completed",
    "max_attempts",
    "launcher_error",
)
_USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
_ATTEMPT_FIELDS = frozenset(
    {
        "attempt_index",
        "accepted",
        "evidence_status",
        "metering_status",
        "limit_trigger",
        "wall_clock_s",
        "session_ids",
        "rollouts",
        "stdout_path",
        "stdout_sha256",
        "stdout_bytes",
        "stderr_path",
        "stderr_sha256",
        "stderr_bytes",
        "output_path",
        "output_sha256",
        "output_bytes",
        "model_calls",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens_raw",
        "cli_reported",
        "codex_exit_code",
        "validator_rc",
        "process_group_residual",
        "termination_verified",
    }
)
_ROLLOUT_FIELDS = frozenset(
    {"session_id", "path", "sha256", "bytes"}
)
_RECEIPT_FIELDS_V2 = frozenset(
    {
        "schema_version",
        "job_id",
        "prompt_sha256",
        "model",
        "reasoning",
        "sandbox",
        "cwd",
        "artifact_dir",
        "output_path",
        "output_sha256",
        "manifest_path",
        "manifest_wave_id",
        "manifest_repo_root",
        "manifest_base_commit",
        "codex_version",
        "codex_executable_path",
        "codex_executable_sha256",
        "model_calls_semantics",
        "possible_unobserved_overshoot",
        "limits_assertion",
        "wall_clock_scope",
        "retry_classification",
        "escaped_process_containment",
        "limits",
        "actuals",
        "outcome",
        "stop_reason",
        "launcher_rc",
        "codex_exit_code",
        "validator_rc",
        "attempts",
    }
)
_RECEIPT_V2_ONLY_FIELDS = frozenset(
    {
        "limits_assertion",
        "wall_clock_scope",
        "manifest_repo_root",
        "manifest_base_commit",
    }
)
_RECEIPT_FIELDS_V1 = _RECEIPT_FIELDS_V2 - _RECEIPT_V2_ONLY_FIELDS
_LIMIT_FIELDS = frozenset(
    {
        "max_wall_clock_s",
        "max_model_calls",
        "max_cli_reported_tokens",
        "max_attempts",
    }
)
_ACTUAL_FIELDS = frozenset(
    {
        "wall_clock_s",
        "attempt_count",
        "model_calls",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens_raw",
        "cli_reported",
    }
)
_MANIFEST_FIELDS = frozenset(
    {"schema_version", "wave_id", "repo_root", "base_commit", "sessions"}
)
_MANIFEST_ENTRY_FIELDS = frozenset(
    {"job_id", "attempt_index", "session_id"}
)


class LaunchError(RuntimeError):
    """Launcher integrity error (CLI rc=2)."""


class AttemptLoopError(LaunchError):
    """spawn 後の attempt failure。終了済み attempt 証拠を保持する。"""

    def __init__(self, message: str, attempt: dict[str, Any]) -> None:
        super().__init__(message)
        self.attempt = attempt


@dataclass
class RolloutState:
    session_id: str
    path: Path
    offset: int = 0
    pending: bytes = b""
    sha256: Any = field(default_factory=hashlib.sha256)
    session_meta_count: int = 0
    context_count: int = 0
    model_calls: int = 0
    usage: dict[str, int] | None = None
    latest_usage: dict[str, int] | None = None
    incomplete_usage: bool = False
    nonmonotonic_usage: bool = False
    invalid: bool = False


@dataclass
class AttemptState:
    attempt_index: int
    started_ns: int
    stdout_path: Path
    stderr_path: Path
    output_path: Path
    session_ids: list[str] = field(default_factory=list)
    rollouts: dict[str, RolloutState] = field(default_factory=dict)
    stdout_offset: int = 0
    stdout_pending: bytes = b""
    stdout_invalid: bool = False
    terminal_usage: dict[str, int] | None = None
    limit_trigger: str | None = None
    evidence_forced_stop: bool = False
    manifested_session_ids: set[str] = field(default_factory=set)


def _positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("1 以上の整数を指定すること") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("1 以上の整数を指定すること")
    return value


def _positive_decimal(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("正の有限数を指定すること") from exc
    if not value.is_finite() or value <= 0:
        raise argparse.ArgumentTypeError("正の有限数を指定すること")
    return value


def _canonical_uuid(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise LaunchError(f"{label}: UUID は文字列でなければならない")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise LaunchError(f"{label}: UUID が不正") from exc
    if str(parsed) != value:
        raise LaunchError(f"{label}: canonical lowercase UUID ではない")
    return value


def _closed_object(
    value: Any, fields: frozenset[str], *, label: str
) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise LaunchError(f"{label}: field set が不正")
    return value


def _strict_int(value: Any, *, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise LaunchError(f"{label}: int が不正")
    return value


def _strict_number(value: Any, *, label: str, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise LaunchError(f"{label}: number が不正")
    number = Decimal(value)
    if not number.is_finite() or number < 0 or (positive and number <= 0):
        raise LaunchError(f"{label}: number の範囲が不正")
    return number


def _cli_reported(usage: Mapping[str, int]) -> int:
    """T-179/T-180 で共有する CLI-reported token の唯一の定義。"""
    return (
        usage["input_tokens"]
        - usage["cached_input_tokens"]
        + usage["output_tokens"]
    )


def _absolute_path(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise LaunchError(f"{label}: absolute path が必要")
    return value


def _hash_file(path: Path, *, limit: int | None = None) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        remaining = limit
        while remaining is None or remaining:
            size = 64 * 1024 if remaining is None else min(64 * 1024, remaining)
            block = stream.read(size)
            if not block:
                break
            digest.update(block)
            count += len(block)
            if remaining is not None:
                remaining -= len(block)
    if limit is not None and count != limit:
        raise LaunchError(f"{path}: sealed byte prefix が欠損")
    return digest.hexdigest(), count


def _fsync_parent(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(path.parent, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _walk_values(value: object) -> Sequence[object]:
    pending: list[object] = [value]
    result: list[object] = []
    while pending:
        item = pending.pop()
        result.append(item)
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
    return result


def _json_bytes(value: object) -> bytes:
    def json_ready(item: Any) -> Any:
        if isinstance(item, Decimal):
            return float(item)
        if isinstance(item, dict):
            return {key: json_ready(child) for key, child in item.items()}
        if isinstance(item, list):
            return [json_ready(child) for child in item]
        return item

    if any(
        isinstance(item, Decimal)
        for item in _walk_values(value)
    ):
        raw = json.dumps(
            json_ready(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8") + b"\n"
    else:
        raw = canonical_bytes(value) + b"\n"
    return raw


def _write_json_temp(path: Path, value: object) -> Path:
    raw = _json_bytes(value)
    temporary = path.with_name(
        f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}"
    )
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(temporary, flags, 0o600)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    finally:
        os.close(fd)
    return temporary


def _atomic_replace_json(
    path: Path,
    value: object,
    *,
    before_replace: Callable[[Path], None] | None = None,
) -> None:
    """同一 directory の完全な temp を最終 path へ atomic replace する。"""
    temporary = _write_json_temp(path, value)
    try:
        if before_replace is not None:
            before_replace(temporary)
        os.replace(temporary, path)
        _fsync_parent(path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


@contextmanager
def _reserve_receipt_slot(path: Path) -> Any:
    """create-only receipt slot を確保し、完全 receipt との競合を先に決着する。"""
    lock_path = path.with_name(path.name + ".lock")
    lock_fd = os.open(
        lock_path,
        os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        replace_invalid = False
        if path.exists():
            try:
                _validate_receipt(_load_json(path, label="existing receipt"))
            except LaunchError:
                # R12: crash が残した invalid partial は恒久 DoS にしない。
                replace_invalid = True
            else:
                raise LaunchError("既存の完全な receipt は上書きできない")
        yield replace_invalid
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def _atomic_create_json_reserved(
    path: Path, value: object, *, replace_invalid: bool
) -> None:
    """予約済み slot へ完全 JSON を公開する。呼出側は receipt lock を保持する。"""
    temporary: Path | None = _write_json_temp(path, value)
    published = False
    try:
        if replace_invalid:
            os.replace(temporary, path)
            temporary = None
        else:
            os.link(temporary, path)
        published = True
        _fsync_parent(path)
    except BaseException:
        if published:
            try:
                os.unlink(path)
                _fsync_parent(path)
            except OSError:
                pass
        raise
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def _atomic_create_json(path: Path, value: object) -> None:
    """完全 JSON を atomic create-only で公開する。

    invalid な既存 partial receipt だけは lock 内で置換を許す。完全 receipt
    が既に存在する場合と、temp の ``link(2)`` が競合した場合は上書きしない。
    """
    with _reserve_receipt_slot(path) as replace_invalid:
        _atomic_create_json_reserved(
            path, value, replace_invalid=replace_invalid
        )


def _atomic_publish(path: Path, raw: bytes) -> None:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(path, flags, 0o600)
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_parent(path)


def _load_json(path: Path, *, label: str) -> object:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise LaunchError(f"{label}: 読み取れない ({exc})") from exc
    try:
        return strict_loads(
            raw, label=label, max_bytes=_MAX_JSON_BYTES
        )
    except DevWavesError as exc:
        raise LaunchError(f"{label}: strict JSON ではない") from exc


def _validate_manifest(value: object) -> dict[str, Any]:
    manifest = _closed_object(
        value, _MANIFEST_FIELDS, label="CodexWorkerSessionManifest"
    )
    if manifest["schema_version"] != 1:
        raise LaunchError("manifest.schema_version が不正")
    wave_id = manifest["wave_id"]
    if not isinstance(wave_id, str) or _ID_RE.fullmatch(wave_id) is None:
        raise LaunchError("manifest.wave_id が不正")
    _absolute_path(manifest["repo_root"], label="manifest.repo_root")
    base_commit = manifest["base_commit"]
    if not isinstance(base_commit, str) or _COMMIT_RE.fullmatch(base_commit) is None:
        raise LaunchError("manifest.base_commit が不正")
    sessions = manifest["sessions"]
    if not isinstance(sessions, list) or not 1 <= len(sessions) <= 1024:
        raise LaunchError("manifest.sessions は 1..1024 件でなければならない")
    job_attempts: set[tuple[str, int]] = set()
    session_ids: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, raw_entry in enumerate(sessions):
        entry = _closed_object(
            raw_entry, _MANIFEST_ENTRY_FIELDS, label=f"manifest.sessions[{index}]"
        )
        job_id = entry["job_id"]
        if not isinstance(job_id, str) or _ID_RE.fullmatch(job_id) is None:
            raise LaunchError(f"manifest.sessions[{index}].job_id が不正")
        attempt_index = _strict_int(
            entry["attempt_index"],
            label=f"manifest.sessions[{index}].attempt_index",
            minimum=1,
        )
        session_id = _canonical_uuid(
            entry["session_id"],
            label=f"manifest.sessions[{index}].session_id",
        )
        key = (job_id, attempt_index)
        if key in job_attempts:
            raise LaunchError("manifest の (job_id, attempt_index) が重複")
        if session_id in session_ids:
            raise LaunchError("manifest の session_id が重複")
        job_attempts.add(key)
        session_ids.add(session_id)
        validated.append(
            {
                "job_id": job_id,
                "attempt_index": attempt_index,
                "session_id": session_id,
            }
        )
    return {
        "schema_version": 1,
        "wave_id": wave_id,
        "repo_root": manifest["repo_root"],
        "base_commit": base_commit,
        "sessions": validated,
    }


def _append_manifest(
    path: Path,
    *,
    wave_id: str,
    repo_root: str,
    base_commit: str,
    entry: dict[str, Any],
    critical_section_hook: Callable[[], None] | None = None,
) -> None:
    lock_path = path.with_name(path.name + ".lock")
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | getattr(os, "O_NOFOLLOW", 0)
    )
    lock_fd = os.open(lock_path, flags, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        if path.exists():
            manifest = _validate_manifest(_load_json(path, label="manifest"))
            if manifest["wave_id"] != wave_id:
                raise LaunchError("manifest header の wave_id が異なる")
            if manifest["repo_root"] != repo_root:
                raise LaunchError("manifest header の repo_root が異なる")
            if manifest["base_commit"] != base_commit:
                raise LaunchError("manifest header の base_commit が異なる")
        else:
            manifest = {
                "schema_version": 1,
                "wave_id": wave_id,
                "repo_root": repo_root,
                "base_commit": base_commit,
                "sessions": [],
            }
        same_key = [
            item
            for item in manifest["sessions"]
            if (
                item["job_id"],
                item["attempt_index"],
            )
            == (entry["job_id"], entry["attempt_index"])
        ]
        if same_key:
            if same_key == [entry]:
                return
            raise LaunchError(
                "1 attempt から複数 session が観測され、凍結 manifest schema に表現できない"
            )
        if any(
            item["session_id"] == entry["session_id"]
            for item in manifest["sessions"]
        ):
            raise LaunchError("manifest session_id が別 job/attempt と重複")
        manifest["sessions"].append(entry)
        manifest["sessions"].sort(
            key=lambda item: (
                item["job_id"],
                item["attempt_index"],
                item["session_id"],
            )
        )
        if len(manifest["sessions"]) > 1024:
            raise LaunchError("manifest.sessions 上限 1024 件を超過")
        if critical_section_hook is not None:
            critical_section_hook()
        _atomic_replace_json(path, manifest)
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def _usage(
    value: Any, *, label: str, require_total: bool
) -> dict[str, int]:
    if not isinstance(value, dict):
        raise LaunchError(f"{label}: usage が object ではない")
    result: dict[str, int] = {}
    for field_name in ("input_tokens", "cached_input_tokens", "output_tokens"):
        result[field_name] = _strict_int(
            value.get(field_name), label=f"{label}.{field_name}"
        )
    reasoning = value.get("reasoning_output_tokens", 0)
    result["reasoning_output_tokens"] = _strict_int(
        reasoning, label=f"{label}.reasoning_output_tokens"
    )
    if result["cached_input_tokens"] > result["input_tokens"]:
        raise LaunchError(f"{label}: cached_input_tokens が input_tokens を超える")
    if require_total:
        result["total_tokens_raw"] = _strict_int(
            value.get("total_tokens"), label=f"{label}.total_tokens"
        )
    else:
        result["total_tokens_raw"] = (
            result["input_tokens"] + result["output_tokens"]
        )
    result["cli_reported"] = _cli_reported(result)
    return result


def _consume_stdout_event(state: AttemptState, event: Mapping[str, Any]) -> None:
    event_type = event.get("type")
    if event_type == "thread.started":
        try:
            session_id = _canonical_uuid(
                event.get("thread_id"), label="stdout thread_id"
            )
        except LaunchError:
            state.stdout_invalid = True
            return
        if session_id not in state.session_ids:
            state.session_ids.append(session_id)
    elif event_type == "turn.completed":
        try:
            state.terminal_usage = _usage(
                event.get("usage"),
                label="stdout turn.completed.usage",
                require_total=False,
            )
        except LaunchError:
            state.stdout_invalid = True


def _drain_stdout(state: AttemptState) -> None:
    with state.stdout_path.open("rb") as stream:
        stream.seek(state.stdout_offset)
        new = stream.read()
    if not new:
        return
    state.stdout_offset += len(new)
    combined = state.stdout_pending + new
    complete, separator, pending = combined.rpartition(b"\n")
    if not separator:
        state.stdout_pending = combined
        return
    state.stdout_pending = pending
    for raw_line in complete.splitlines():
        if not raw_line.strip():
            continue
        try:
            events = parse_jsonl(
                raw_line + b"\n",
                max_bytes=_MAX_EVENT_LINE_BYTES,
                max_line_bytes=_MAX_EVENT_LINE_BYTES,
            )
            if len(events) != 1:
                raise EventValidationError("1 行に event が 1 件でない")
        except EventValidationError:
            state.stdout_invalid = True
            continue
        _consume_stdout_event(state, events[0])


def _discover_rollouts(state: AttemptState, sessions_root: Path) -> None:
    for session_id in state.session_ids:
        if session_id in state.rollouts:
            continue
        matches = sorted(
            path
            for path in sessions_root.rglob(f"rollout-*-{session_id}.jsonl")
            if path.is_file() and not path.is_symlink()
        )
        if len(matches) > 1:
            state.stdout_invalid = True
            continue
        if len(matches) == 1:
            state.rollouts[session_id] = RolloutState(
                session_id=session_id,
                path=matches[0].resolve(),
            )


def _consume_rollout_event(
    rollout: RolloutState,
    event: Mapping[str, Any],
    *,
    model: str,
    reasoning: str,
) -> None:
    item_type = event.get("type")
    payload = event.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    if item_type == "session_meta":
        rollout.session_meta_count += 1
        try:
            meta_id = _canonical_uuid(
                payload.get("session_id"), label="rollout session_meta.session_id"
            )
        except LaunchError:
            rollout.invalid = True
            return
        if meta_id != rollout.session_id:
            rollout.invalid = True
    elif item_type == "turn_context":
        rollout.context_count += 1
        context_model = payload.get("model", event.get("model"))
        context_reasoning = payload.get("effort", event.get("effort"))
        if context_model != model or context_reasoning != reasoning:
            rollout.invalid = True
    elif item_type == "event_msg" and payload.get("type") == "token_count":
        rollout.model_calls += 1
        info = payload.get("info")
        if not isinstance(info, dict):
            rollout.incomplete_usage = True
            return
        try:
            observed = _usage(
                info.get("total_token_usage"),
                label="rollout token_count.total_token_usage",
                require_total=True,
            )
        except LaunchError:
            rollout.invalid = True
            rollout.incomplete_usage = True
            return
        previous = rollout.latest_usage
        if previous is not None and (
            any(
                observed[field_name] < previous[field_name]
                for field_name in _USAGE_FIELDS + ("total_tokens_raw",)
            )
            or observed["cli_reported"] < previous["cli_reported"]
        ):
            rollout.nonmonotonic_usage = True
        rollout.latest_usage = observed
        if (
            rollout.usage is None
            or observed["cli_reported"] > rollout.usage["cli_reported"]
        ):
            # cap と receipt actuals は一度観測した peak を巻き戻さない。
            rollout.usage = observed


def _tail_rollout(
    rollout: RolloutState, *, model: str, reasoning: str
) -> None:
    with rollout.path.open("rb") as stream:
        stream.seek(rollout.offset)
        new = stream.read()
    if not new:
        return
    rollout.offset += len(new)
    rollout.sha256.update(new)
    combined = rollout.pending + new
    complete, separator, pending = combined.rpartition(b"\n")
    if not separator:
        rollout.pending = combined
        return
    rollout.pending = pending
    for raw_line in complete.splitlines():
        if not raw_line.strip():
            continue
        try:
            event = strict_json_loads(
                raw_line.decode("utf-8"),
                label="rollout JSONL",
                max_bytes=_MAX_EVENT_LINE_BYTES,
            )
            if not isinstance(event, dict):
                raise EventValidationError("rollout event が object でない")
        except (UnicodeDecodeError, EventValidationError):
            rollout.invalid = True
            continue
        _consume_rollout_event(
            rollout, event, model=model, reasoning=reasoning
        )


def _rollout_actuals(state: AttemptState) -> dict[str, int]:
    result = {
        "model_calls": 0,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens_raw": 0,
        "cli_reported": 0,
    }
    for rollout in state.rollouts.values():
        result["model_calls"] += rollout.model_calls
        if rollout.usage is None:
            continue
        for field_name in _USAGE_FIELDS + ("total_tokens_raw", "cli_reported"):
            result[field_name] += rollout.usage[field_name]
    return result


def _metering_status(state: AttemptState) -> str:
    if not state.rollouts or not any(
        item.model_calls for item in state.rollouts.values()
    ):
        return "missing"
    if any(
        item.incomplete_usage or item.usage is None
        for item in state.rollouts.values()
    ):
        return "incomplete"
    if any(item.nonmonotonic_usage for item in state.rollouts.values()):
        return "inconsistent"
    if state.terminal_usage is None:
        return "missing"
    actuals = _rollout_actuals(state)
    if any(
        actuals[field_name] != state.terminal_usage[field_name]
        for field_name in _USAGE_FIELDS
    ):
        return "inconsistent"
    return "complete"


def _evidence_status(state: AttemptState) -> str:
    if not state.session_ids or any(
        session_id not in state.rollouts for session_id in state.session_ids
    ):
        return "missing"
    if (
        state.stdout_invalid
        or state.stdout_pending
        or any(
            rollout.invalid
            or rollout.pending
            or rollout.session_meta_count != 1
            or rollout.context_count < 1
            for rollout in state.rollouts.values()
        )
    ):
        return "invalid"
    return "complete"


def _group_member_count(identity: PidIdentity | None) -> int | None:
    if identity is None:
        return None
    count = 0
    try:
        entries = os.scandir("/proc")
    except OSError:
        return None
    with entries:
        for entry in entries:
            if not entry.name.isdigit():
                continue
            stat_path = Path(f"/proc/{entry.name}/stat")
            try:
                raw = stat_path.read_text(encoding="ascii")
                end = raw.rfind(")")
                fields = raw[end + 2 :].split()
                if end > 0 and len(fields) > 2 and int(fields[2]) == identity.pid:
                    count += 1
            except FileNotFoundError:
                # scan 後に消滅した PID は現在の residual ではない。存在が
                # 続くのに読めない場合だけ unknown とする。
                if stat_path.exists():
                    return None
                continue
            except (OSError, ValueError):
                return None
    return count


def _terminate(
    process: subprocess.Popen[bytes],
    identity: PidIdentity | None,
    *,
    grace_s: float,
) -> tuple[int | None, bool]:
    verified = False
    if identity is not None:
        try:
            verified = terminate_verified_group(identity, grace_s)
        except (OSError, ValueError):
            verified = False
    elif process.poll() is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=max(1.0, grace_s + 1.0))
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
    deadline = time.monotonic() + 1.0
    residual = _group_member_count(identity)
    while residual not in (0, None) and time.monotonic() < deadline:
        time.sleep(0.01)
        residual = _group_member_count(identity)
    return residual, bool(verified and residual == 0)


def _normal_reap(
    process: subprocess.Popen[bytes], identity: PidIdentity | None
) -> tuple[int | None, bool]:
    process.wait()
    deadline = time.monotonic() + 0.5
    residual = _group_member_count(identity)
    while residual not in (0, None) and time.monotonic() < deadline:
        time.sleep(0.01)
        residual = _group_member_count(identity)
    return residual, residual == 0


def _validator_rc(path: Path) -> int:
    failures = _validator.check_file(
        path,
        min_bytes=_validator._DEFAULT_MIN_BYTES,
        heading=re.compile(_validator._DEFAULT_HEADING, re.MULTILINE),
    )
    return 0 if not failures else 1


def _seal_attempt(
    state: AttemptState,
    *,
    process: subprocess.Popen[bytes],
    residual: int | None,
    termination_verified: bool,
    wall_clock_s: Decimal,
    job_wall_clock_s: Decimal,
    prior_actuals: Mapping[str, int],
    limits: argparse.Namespace,
    force_not_accepted: bool = False,
) -> dict[str, Any]:
    stdout_sha, stdout_bytes = _hash_file(state.stdout_path)
    stderr_sha, stderr_bytes = _hash_file(state.stderr_path)
    if state.output_path.exists():
        output_sha, output_bytes = _hash_file(state.output_path)
        validator_rc = _validator_rc(state.output_path)
    else:
        output_sha, output_bytes, validator_rc = None, 0, None
    actuals = _rollout_actuals(state)
    evidence_status = _evidence_status(state)
    metering_status = _metering_status(state)
    if state.limit_trigger is None:
        if job_wall_clock_s > limits.max_wall_clock_s:
            state.limit_trigger = "max_wall_clock_s"
        elif (
            prior_actuals["model_calls"] + actuals["model_calls"]
            > limits.max_model_calls
        ):
            state.limit_trigger = "max_model_calls"
        elif (
            prior_actuals["cli_reported"] + actuals["cli_reported"]
            > limits.max_cli_reported_tokens
        ):
            state.limit_trigger = "max_cli_reported_tokens"
    accepted = bool(
        not force_not_accepted
        and state.limit_trigger is None
        and process.returncode == 0
        and validator_rc == 0
        and evidence_status == "complete"
        and metering_status == "complete"
        and residual == 0
        and termination_verified
    )
    rollouts = []
    for rollout in sorted(
        state.rollouts.values(), key=lambda item: item.session_id
    ):
        digest, size = _hash_file(rollout.path, limit=rollout.offset)
        rollouts.append(
            {
                "session_id": rollout.session_id,
                "path": os.fspath(rollout.path),
                "sha256": digest,
                "bytes": size,
            }
        )
    return {
        "attempt_index": state.attempt_index,
        "accepted": accepted,
        "evidence_status": evidence_status,
        "metering_status": metering_status,
        "limit_trigger": state.limit_trigger,
        "wall_clock_s": wall_clock_s,
        "session_ids": list(state.session_ids),
        "rollouts": rollouts,
        "stdout_path": os.fspath(state.stdout_path),
        "stdout_sha256": stdout_sha,
        "stdout_bytes": stdout_bytes,
        "stderr_path": os.fspath(state.stderr_path),
        "stderr_sha256": stderr_sha,
        "stderr_bytes": stderr_bytes,
        "output_path": os.fspath(state.output_path),
        "output_sha256": output_sha,
        "output_bytes": output_bytes,
        **actuals,
        "codex_exit_code": process.returncode,
        "validator_rc": validator_rc,
        "process_group_residual": residual,
        "termination_verified": termination_verified,
    }


def _attempt_loop(
    args: argparse.Namespace,
    *,
    attempt_index: int,
    job_started_ns: int,
    prior_actuals: Mapping[str, int],
    codex_path: Path,
    expected_binary_sha256: str,
) -> dict[str, Any]:
    current_sha256, _ = _hash_file(codex_path)
    if current_sha256 != expected_binary_sha256:
        raise LaunchError("retry 間で codex executable が変化した")
    stdout_path = args.artifact_dir / f"attempt-{attempt_index:04d}.events.jsonl"
    stderr_path = args.artifact_dir / f"attempt-{attempt_index:04d}.stderr.log"
    attempt_output = args.artifact_dir / f"attempt-{attempt_index:04d}.output.md"
    for path in (stdout_path, stderr_path, attempt_output):
        if path.exists():
            raise LaunchError(f"attempt artifact が既に存在する: {path}")
    stdout_handle = stdout_path.open("xb", buffering=0)
    stderr_handle = stderr_path.open("xb", buffering=0)
    argv = [
        os.fspath(codex_path),
        "exec",
        "--json",
        "-m",
        args.model,
        "-c",
        f'model_reasoning_effort="{args.reasoning}"',
        "-s",
        args.sandbox,
        "-C",
        os.fspath(args.cwd),
        "-o",
        os.fspath(attempt_output),
        args.prompt_text,
    ]
    state = AttemptState(
        attempt_index=attempt_index,
        started_ns=time.monotonic_ns(),
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        output_path=attempt_output,
    )
    process: subprocess.Popen[bytes] | None = None
    identity: PidIdentity | None = None
    residual: int | None = None
    termination_verified = False
    caught: BaseException | None = None

    def observe(*, register_manifest: bool) -> None:
        _drain_stdout(state)
        _discover_rollouts(state, args.sessions_root)
        for rollout in state.rollouts.values():
            _tail_rollout(
                rollout, model=args.model, reasoning=args.reasoning
            )
        if not register_manifest:
            return
        for session_id in state.session_ids:
            rollout = state.rollouts.get(session_id)
            if (
                rollout is None
                or rollout.session_meta_count != 1
                or rollout.invalid
                or session_id in state.manifested_session_ids
            ):
                continue
            # F-P1: stdout/filename/session_meta の相関が成立した時点で記録する。
            _append_manifest(
                args.manifest,
                wave_id=args.wave_id,
                repo_root=os.fspath(args.repo_root),
                base_commit=args.base_commit,
                entry={
                    "job_id": args.job_id,
                    "attempt_index": attempt_index,
                    "session_id": session_id,
                },
            )
            state.manifested_session_ids.add(session_id)

    try:
        try:
            process = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=stdout_handle,
                stderr=stderr_handle,
                shell=False,
                close_fds=True,
                start_new_session=True,
            )
        except OSError as exc:
            raise LaunchError(f"codex spawn に失敗: {exc}") from exc
        try:
            identity = read_pid_identity(process.pid)
        except (OSError, ValueError):
            identity = None
        evidence_deadline_ns = state.started_ns + int(
            float(args.evidence_grace_s) * 1_000_000_000
        )
        forced_stop = False
        while True:
            observe(register_manifest=True)
            now_ns = time.monotonic_ns()
            current = _rollout_actuals(state)
            process_rc = process.poll()
            if process_rc is not None:
                # 終了と limit 観測が同 poll の場合は最終 drain を先に確定する。
                observe(register_manifest=True)
                current = _rollout_actuals(state)
                totals = {
                    key: prior_actuals[key] + current[key]
                    for key in (
                        "model_calls",
                        "cli_reported",
                    )
                }
                elapsed = Decimal(now_ns - job_started_ns) / Decimal(
                    1_000_000_000
                )
                if elapsed > args.max_wall_clock_s:
                    state.limit_trigger = "max_wall_clock_s"
                elif totals["model_calls"] > args.max_model_calls:
                    state.limit_trigger = "max_model_calls"
                elif (
                    totals["cli_reported"]
                    > args.max_cli_reported_tokens
                ):
                    state.limit_trigger = "max_cli_reported_tokens"
                break

            elapsed = Decimal(now_ns - job_started_ns) / Decimal(1_000_000_000)
            pending_limit: str | None = None
            if elapsed >= args.max_wall_clock_s:
                pending_limit = "max_wall_clock_s"
            elif (
                prior_actuals["model_calls"] + current["model_calls"]
                >= args.max_model_calls
            ):
                pending_limit = "max_model_calls"
            elif (
                prior_actuals["cli_reported"] + current["cli_reported"]
                >= args.max_cli_reported_tokens
            ):
                pending_limit = "max_cli_reported_tokens"
            if pending_limit is not None:
                # drain と自然終了が同じ監視周期に重なった race を確定する。
                # 待つ長さは通常の poll 1 回以下で、新しい admission を表さない。
                if pending_limit == "max_wall_clock_s":
                    state.limit_trigger = pending_limit
                else:
                    try:
                        process.wait(timeout=float(args.poll_interval_s))
                    except subprocess.TimeoutExpired:
                        state.limit_trigger = pending_limit
                    else:
                        continue
            if state.limit_trigger is not None:
                forced_stop = True
                break
            if now_ns >= evidence_deadline_ns and (
                not state.session_ids
                or any(
                    session_id not in state.rollouts
                    for session_id in state.session_ids
                )
            ):
                state.evidence_forced_stop = True
                forced_stop = True
                break
            time.sleep(float(args.poll_interval_s))

        if forced_stop:
            residual, termination_verified = _terminate(
                process,
                identity,
                grace_s=float(args.termination_grace_s),
            )
        else:
            residual, termination_verified = _normal_reap(process, identity)
        observe(register_manifest=True)
    except BaseException as exc:
        caught = exc
        if process is not None:
            try:
                residual, termination_verified = _terminate(
                    process,
                    identity,
                    grace_s=float(args.termination_grace_s),
                )
            except BaseException:
                residual, termination_verified = None, False
            try:
                observe(register_manifest=False)
            except BaseException:
                state.stdout_invalid = True
    finally:
        stdout_handle.flush()
        os.fsync(stdout_handle.fileno())
        stdout_handle.close()
        stderr_handle.flush()
        os.fsync(stderr_handle.fileno())
        stderr_handle.close()
    if caught is not None and process is None:
        if isinstance(caught, LaunchError):
            raise caught
        raise LaunchError(f"attempt 起動前に失敗: {caught}") from caught
    assert process is not None
    wall_clock_s = Decimal(time.monotonic_ns() - state.started_ns) / Decimal(
        1_000_000_000
    )
    job_wall_clock_s = Decimal(
        time.monotonic_ns() - job_started_ns
    ) / Decimal(1_000_000_000)
    attempt = _seal_attempt(
        state,
        process=process,
        residual=residual,
        termination_verified=termination_verified,
        wall_clock_s=wall_clock_s,
        job_wall_clock_s=job_wall_clock_s,
        prior_actuals=prior_actuals,
        limits=args,
        force_not_accepted=caught is not None,
    )
    if caught is not None:
        raise AttemptLoopError(
            f"spawn 後の attempt 処理に失敗: {caught}", attempt
        ) from caught
    return attempt


def _manifest_contains(
    manifest: Mapping[str, Any],
    *,
    job_id: str,
    attempt_index: int,
    session_ids: Sequence[str],
) -> bool:
    expected = {
        (job_id, attempt_index, session_id) for session_id in session_ids
    }
    actual = {
        (item["job_id"], item["attempt_index"], item["session_id"])
        for item in manifest["sessions"]
    }
    return expected <= actual


def _writer_truth(
    attempts: Sequence[Mapping[str, Any]],
    *,
    max_attempts: int,
) -> tuple[str, str, int]:
    """Writer-side truth table. Checker はこの関数を呼ばない。"""
    if attempts and attempts[-1]["accepted"]:
        if any(item["limit_trigger"] is not None for item in attempts):
            raise LaunchError("accepted job に limit_trigger がある")
        return "accepted", "completed", 0
    for attempt in attempts:
        if attempt["limit_trigger"] is not None:
            return "not_accepted", attempt["limit_trigger"], 1
    if len(attempts) >= max_attempts:
        return "not_accepted", "max_attempts", 1
    return "launcher_error", "launcher_error", 2


def _sum_attempts(attempts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    actuals: dict[str, Any] = {
        "wall_clock_s": sum(
            (item["wall_clock_s"] for item in attempts), Decimal(0)
        ),
        "attempt_count": len(attempts),
        "model_calls": 0,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "total_tokens_raw": 0,
        "cli_reported": 0,
    }
    for attempt in attempts:
        for field_name in (
            "model_calls",
            "input_tokens",
            "cached_input_tokens",
            "output_tokens",
            "reasoning_output_tokens",
            "total_tokens_raw",
            "cli_reported",
        ):
            actuals[field_name] += attempt[field_name]
    return actuals


def _receipt(
    args: argparse.Namespace,
    *,
    attempts: list[dict[str, Any]],
    job_started_ns: int,
    codex_path: Path,
    codex_sha256: str,
    codex_version: str,
    force_launcher_error: bool = False,
) -> dict[str, Any]:
    if force_launcher_error:
        if any(item["accepted"] for item in attempts):
            raise LaunchError("launcher_error receipt に accepted attempt がある")
        outcome, stop_reason, launcher_rc = (
            "launcher_error",
            "launcher_error",
            2,
        )
    else:
        outcome, stop_reason, launcher_rc = _writer_truth(
            attempts, max_attempts=args.max_attempts
        )
    actuals = _sum_attempts(attempts)
    actuals["wall_clock_s"] = Decimal(
        time.monotonic_ns() - job_started_ns
    ) / Decimal(1_000_000_000)
    last = attempts[-1] if attempts else None
    return {
        "schema_version": 2,
        "job_id": args.job_id,
        "prompt_sha256": hashlib.sha256(args.prompt_bytes).hexdigest(),
        "model": args.model,
        "reasoning": args.reasoning,
        "sandbox": args.sandbox,
        "cwd": os.fspath(args.cwd),
        "artifact_dir": os.fspath(args.artifact_dir),
        "output_path": os.fspath(args.output_file),
        "output_sha256": (
            last["output_sha256"] if outcome == "accepted" and last else None
        ),
        "manifest_path": os.fspath(args.manifest),
        "manifest_wave_id": args.wave_id,
        "manifest_repo_root": os.fspath(args.repo_root),
        "manifest_base_commit": args.base_commit,
        "codex_version": codex_version,
        "codex_executable_path": os.fspath(codex_path),
        "codex_executable_sha256": codex_sha256,
        "model_calls_semantics": "observed_token_count_events",
        "possible_unobserved_overshoot": any(
            item["metering_status"] != "complete"
            or item["limit_trigger"] is not None
            for item in attempts
        ),
        "limits_assertion": "self_asserted",
        "wall_clock_scope": "launcher_start_to_receipt_fields_finalized",
        "retry_classification": "none",
        "escaped_process_containment": "not_attempted",
        "limits": {
            "max_wall_clock_s": args.max_wall_clock_s,
            "max_model_calls": args.max_model_calls,
            "max_cli_reported_tokens": args.max_cli_reported_tokens,
            "max_attempts": args.max_attempts,
        },
        "actuals": actuals,
        "outcome": outcome,
        "stop_reason": stop_reason,
        "launcher_rc": launcher_rc,
        "codex_exit_code": last["codex_exit_code"] if last else None,
        "validator_rc": last["validator_rc"] if last else None,
        "attempts": attempts,
    }


def _resolve_executable(value: str) -> Path:
    selected = value if os.path.isabs(value) else shutil.which(value)
    if not selected:
        raise LaunchError(f"codex executable が見つからない: {value}")
    path = Path(selected).resolve(strict=True)
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or not os.access(path, os.X_OK):
        raise LaunchError("codex executable は実行可能 regular file でなければならない")
    return path


def _codex_version(path: Path) -> str:
    try:
        completed = subprocess.run(
            [os.fspath(path), "--version"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LaunchError(f"codex --version に失敗: {exc}") from exc
    raw = completed.stdout if completed.stdout.strip() else completed.stderr
    try:
        value = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise LaunchError("codex version が UTF-8 ではない") from exc
    if completed.returncode != 0 or not value or "\n" in value:
        raise LaunchError("codex version identity が不正")
    return value


def _verify_repo_binding(repo_root: Path, cwd: Path, base_commit: str) -> None:
    try:
        cwd.relative_to(repo_root)
    except ValueError as exc:
        raise LaunchError("--cwd は --repo-root 配下でなければならない") from exc
    try:
        top = subprocess.run(
            ["git", "-C", os.fspath(repo_root), "rev-parse", "--show-toplevel"],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        exists = subprocess.run(
            [
                "git",
                "-C",
                os.fspath(repo_root),
                "cat-file",
                "-e",
                f"{base_commit}^{{commit}}",
            ],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LaunchError(f"repository identity 検査に失敗: {exc}") from exc
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != repo_root:
        raise LaunchError("--repo-root は repository root でなければならない")
    if exists.returncode != 0:
        raise LaunchError("--base-commit が --repo-root の repository に存在しない")


def _preflight_run(args: argparse.Namespace) -> tuple[Path, str, str]:
    for name in ("cwd", "repo_root", "artifact_dir", "output_file", "receipt", "manifest"):
        path = getattr(args, name)
        if not path.is_absolute():
            raise LaunchError(f"--{name.replace('_', '-')} は absolute path が必要")
    if not args.cwd.is_dir() or not args.repo_root.is_dir():
        raise LaunchError("--cwd/--repo-root は既存 directory でなければならない")
    if args.max_attempts > 1 and args.sandbox != "read-only":
        raise LaunchError(
            "--max-attempts > 1 は --sandbox read-only のときだけ許可される"
        )
    if not _ID_RE.fullmatch(args.job_id) or not _ID_RE.fullmatch(args.wave_id):
        raise LaunchError("--job-id/--wave-id が不正")
    if _COMMIT_RE.fullmatch(args.base_commit) is None:
        raise LaunchError("--base-commit は lowercase hex40 でなければならない")
    if not args.prompt_file.is_absolute():
        raise LaunchError("--prompt-file は absolute path が必要")
    try:
        metadata = args.prompt_file.stat()
        prompt_bytes = args.prompt_file.read_bytes()
        prompt_text = prompt_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise LaunchError(f"prompt を読めない: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode) or not prompt_bytes:
        raise LaunchError("prompt は non-empty UTF-8 regular file でなければならない")
    args.prompt_bytes = prompt_bytes
    args.prompt_text = prompt_text
    args.cwd = args.cwd.resolve()
    args.repo_root = args.repo_root.resolve()
    _verify_repo_binding(args.repo_root, args.cwd, args.base_commit)
    if args.output_file.exists():
        raise LaunchError("--output-file は不在でなければならない")
    for parent in (
        args.artifact_dir.parent,
        args.output_file.parent,
        args.receipt.parent,
        args.manifest.parent,
    ):
        if not parent.is_dir():
            raise LaunchError(f"parent directory が存在しない: {parent}")
    args.artifact_dir.mkdir(mode=0o700, exist_ok=True)
    args.artifact_dir = args.artifact_dir.resolve()
    args.output_file = args.output_file.resolve(strict=False)
    args.receipt = args.receipt.resolve(strict=False)
    args.manifest = args.manifest.resolve(strict=False)
    args.sessions_root = args.sessions_root.resolve(strict=False)
    if args.manifest.exists():
        # structural corruption と header identity を spawn 前に止める。
        manifest = _validate_manifest(
            _load_json(args.manifest, label="existing manifest")
        )
        expected_header = (
            args.wave_id,
            os.fspath(args.repo_root),
            args.base_commit,
        )
        actual_header = (
            manifest["wave_id"],
            manifest["repo_root"],
            manifest["base_commit"],
        )
        if actual_header != expected_header:
            raise LaunchError("existing manifest header が run identity と異なる")
    if args.receipt.exists():
        try:
            _validate_receipt(_load_json(args.receipt, label="existing receipt"))
        except LaunchError:
            pass
        else:
            raise LaunchError("既存の完全な receipt は上書きできない")
    codex_path = _resolve_executable(args.codex_bin)
    codex_sha256, _ = _hash_file(codex_path)
    return codex_path, codex_sha256, _codex_version(codex_path)


def _latch_final_job_limit(
    args: argparse.Namespace,
    attempts: Sequence[dict[str, Any]],
    *,
    job_started_ns: int,
) -> None:
    if not attempts:
        return
    actuals = _sum_attempts(attempts)
    elapsed = Decimal(
        time.monotonic_ns() - job_started_ns
    ) / Decimal(1_000_000_000)
    reason: str | None = None
    if elapsed > args.max_wall_clock_s:
        reason = "max_wall_clock_s"
    elif actuals["model_calls"] > args.max_model_calls:
        reason = "max_model_calls"
    elif actuals["cli_reported"] > args.max_cli_reported_tokens:
        reason = "max_cli_reported_tokens"
    if reason is not None:
        attempts[-1]["limit_trigger"] = (
            attempts[-1]["limit_trigger"] or reason
        )
        attempts[-1]["accepted"] = False


def _publish_complete_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    """receipt writer call-site: final path へ atomic create-only 公開する。"""
    _atomic_create_json(path, receipt)


def _stage_receipt_write(path: Path, receipt: Mapping[str, Any]) -> None:
    """receipt write/fsync の費用を公開前の launcher scope に取り込む。"""
    temporary = _write_json_temp(path, receipt)
    os.unlink(temporary)


def _run_supervised(
    args: argparse.Namespace,
    *,
    codex_path: Path,
    codex_sha256: str,
    codex_version: str,
    attempts: list[dict[str, Any]],
) -> int:
    started_ns = args.launcher_started_ns
    if (
        Decimal(time.monotonic_ns() - started_ns) / Decimal(1_000_000_000)
        > args.max_wall_clock_s
    ):
        receipt = _receipt(
            args,
            attempts=attempts,
            job_started_ns=started_ns,
            codex_path=codex_path,
            codex_sha256=codex_sha256,
            codex_version=codex_version,
            force_launcher_error=True,
        )
        _publish_complete_receipt(args.receipt, receipt)
        return 2
    prior = {
        "model_calls": 0,
        "cli_reported": 0,
    }
    for attempt_index in range(1, args.max_attempts + 1):
        try:
            attempt = _attempt_loop(
                args,
                attempt_index=attempt_index,
                job_started_ns=started_ns,
                prior_actuals=prior,
                codex_path=codex_path,
                expected_binary_sha256=codex_sha256,
            )
        except AttemptLoopError as exc:
            attempts.append(exc.attempt)
            receipt = _receipt(
                args,
                attempts=attempts,
                job_started_ns=started_ns,
                codex_path=codex_path,
                codex_sha256=codex_sha256,
                codex_version=codex_version,
                force_launcher_error=True,
            )
            _validate_receipt(receipt)
            _publish_complete_receipt(args.receipt, receipt)
            return 2
        attempts.append(attempt)
        prior["model_calls"] += attempt["model_calls"]
        prior["cli_reported"] += attempt["cli_reported"]
        if attempt["accepted"] or attempt["limit_trigger"] is not None:
            break
        if (
            prior["model_calls"] >= args.max_model_calls
            or prior["cli_reported"] >= args.max_cli_reported_tokens
            or Decimal(time.monotonic_ns() - started_ns)
            / Decimal(1_000_000_000)
            >= args.max_wall_clock_s
        ):
            break
    _latch_final_job_limit(args, attempts, job_started_ns=started_ns)
    receipt = _receipt(
        args,
        attempts=attempts,
        job_started_ns=started_ns,
        codex_path=codex_path,
        codex_sha256=codex_sha256,
        codex_version=codex_version,
    )
    # sealed artifact 再計算を含む self-check を公開前に通す。
    _audit_receipt_value(
        receipt,
        args.manifest,
        expectations={},
        check_published_output=False,
    )
    _latch_final_job_limit(args, attempts, job_started_ns=started_ns)
    receipt = _receipt(
        args,
        attempts=attempts,
        job_started_ns=started_ns,
        codex_path=codex_path,
        codex_sha256=codex_sha256,
        codex_version=codex_version,
    )
    _audit_receipt_value(
        receipt,
        args.manifest,
        expectations={},
        check_published_output=False,
    )
    # N-3: receipt の create-only slot を output より先に確保する。
    with _reserve_receipt_slot(args.receipt) as replace_invalid:
        if receipt["outcome"] == "accepted":
            final_attempt = attempts[-1]
            raw = Path(final_attempt["output_path"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != final_attempt["output_sha256"]:
                raise LaunchError("公開前に attempt output が変化した")
            _atomic_publish(args.output_file, raw)
            args.output_published_by_run = True
            published_sha, _ = _hash_file(args.output_file)
            if published_sha != receipt["output_sha256"]:
                raise LaunchError("published output hash が一致しない")
            _latch_final_job_limit(args, attempts, job_started_ns=started_ns)
            receipt = _receipt(
                args,
                attempts=attempts,
                job_started_ns=started_ns,
                codex_path=codex_path,
                codex_sha256=codex_sha256,
                codex_version=codex_version,
            )
            if receipt["outcome"] != "accepted":
                args.output_file.unlink()
                args.output_published_by_run = False
        _audit_receipt_value(
            receipt,
            args.manifest,
            expectations={},
            check_published_output=receipt["outcome"] == "accepted",
        )
        # scope はこの field 確定時点まで。serialize 可能性も公開前に実証する。
        _stage_receipt_write(args.receipt, receipt)
        _atomic_create_json_reserved(
            args.receipt, receipt, replace_invalid=replace_invalid
        )
        return receipt["launcher_rc"]


def _publish_launcher_error_receipt(
    args: argparse.Namespace,
    *,
    attempts: list[dict[str, Any]],
    codex_path: Path,
    codex_sha256: str,
    codex_version: str,
) -> None:
    """内部失敗を launcher-error receipt に封じる。

    manifest entry は費消済み session の資源台帳なので、失敗時も削除しない。
    """
    if getattr(args, "output_published_by_run", False):
        try:
            args.output_file.unlink()
        except FileNotFoundError:
            pass
        args.output_published_by_run = False
    for attempt in attempts:
        attempt["accepted"] = False
    receipt = _receipt(
        args,
        attempts=attempts,
        job_started_ns=args.launcher_started_ns,
        codex_path=codex_path,
        codex_sha256=codex_sha256,
        codex_version=codex_version,
        force_launcher_error=True,
    )
    _validate_receipt(receipt)
    with _reserve_receipt_slot(args.receipt) as replace_invalid:
        _atomic_create_json_reserved(
            args.receipt, receipt, replace_invalid=replace_invalid
        )


def _run(args: argparse.Namespace) -> int:
    codex_path, codex_sha256, codex_version = _preflight_run(args)
    attempts: list[dict[str, Any]] = []
    args.output_published_by_run = False
    try:
        return _run_supervised(
            args,
            codex_path=codex_path,
            codex_sha256=codex_sha256,
            codex_version=codex_version,
            attempts=attempts,
        )
    except BaseException as exc:
        try:
            _publish_launcher_error_receipt(
                args,
                attempts=attempts,
                codex_path=codex_path,
                codex_sha256=codex_sha256,
                codex_version=codex_version,
            )
        except BaseException:
            # receipt 競合の敗者は勝者の完全 receipt を上書きしない。
            pass
        if isinstance(exc, (LaunchError, OSError, ValueError)):
            raise
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise LaunchError(f"run 最終化に失敗: {exc}") from exc


def _validate_attempt(value: Any, *, index: int) -> dict[str, Any]:
    attempt = dict(
        _closed_object(value, _ATTEMPT_FIELDS, label=f"attempts[{index}]")
    )
    if _strict_int(
        attempt["attempt_index"],
        label=f"attempts[{index}].attempt_index",
        minimum=1,
    ) != index + 1:
        raise LaunchError("attempt_index が配列位置と一致しない")
    if not isinstance(attempt["accepted"], bool):
        raise LaunchError("attempt.accepted が bool ではない")
    if attempt["evidence_status"] not in ("complete", "missing", "invalid"):
        raise LaunchError("attempt.evidence_status が不正")
    if attempt["metering_status"] not in (
        "complete",
        "missing",
        "incomplete",
        "inconsistent",
    ):
        raise LaunchError("attempt.metering_status が不正")
    if (
        attempt["limit_trigger"] is not None
        and attempt["limit_trigger"] not in _LIMIT_REASONS
    ):
        raise LaunchError("attempt.limit_trigger が不正")
    _strict_number(attempt["wall_clock_s"], label="attempt.wall_clock_s")
    session_ids = attempt["session_ids"]
    if not isinstance(session_ids, list) or len(session_ids) > 1024:
        raise LaunchError("attempt.session_ids が不正")
    normalized_ids = [
        _canonical_uuid(item, label="attempt.session_ids[]")
        for item in session_ids
    ]
    if len(set(normalized_ids)) != len(normalized_ids):
        raise LaunchError("attempt.session_ids が重複")
    rollouts = attempt["rollouts"]
    if not isinstance(rollouts, list) or len(rollouts) > 1024:
        raise LaunchError("attempt.rollouts が不正")
    rollout_ids: list[str] = []
    for rollout_index, raw_rollout in enumerate(rollouts):
        rollout = _closed_object(
            raw_rollout,
            _ROLLOUT_FIELDS,
            label=f"attempt.rollouts[{rollout_index}]",
        )
        rollout_ids.append(
            _canonical_uuid(
                rollout["session_id"], label="attempt.rollout.session_id"
            )
        )
        _absolute_path(rollout["path"], label="attempt.rollout.path")
        if (
            not isinstance(rollout["sha256"], str)
            or _SHA256_RE.fullmatch(rollout["sha256"]) is None
        ):
            raise LaunchError("attempt.rollout.sha256 が不正")
        _strict_int(rollout["bytes"], label="attempt.rollout.bytes")
    if len(set(rollout_ids)) != len(rollout_ids):
        raise LaunchError("attempt.rollouts session_id が重複")
    for field_name in (
        "stdout_path",
        "stderr_path",
        "output_path",
    ):
        _absolute_path(attempt[field_name], label=f"attempt.{field_name}")
    for field_name in ("stdout_sha256", "stderr_sha256"):
        value_hash = attempt[field_name]
        if not isinstance(value_hash, str) or _SHA256_RE.fullmatch(value_hash) is None:
            raise LaunchError(f"attempt.{field_name} が不正")
    output_sha = attempt["output_sha256"]
    if output_sha is not None and (
        not isinstance(output_sha, str)
        or _SHA256_RE.fullmatch(output_sha) is None
    ):
        raise LaunchError("attempt.output_sha256 が不正")
    for field_name in ("stdout_bytes", "stderr_bytes", "output_bytes"):
        _strict_int(attempt[field_name], label=f"attempt.{field_name}")
    for field_name in (
        "model_calls",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens_raw",
        "cli_reported",
    ):
        _strict_int(attempt[field_name], label=f"attempt.{field_name}")
    residual = attempt["process_group_residual"]
    if residual is not None:
        _strict_int(residual, label="attempt.process_group_residual")
    if attempt["cached_input_tokens"] > attempt["input_tokens"]:
        raise LaunchError("attempt cached_input_tokens が input_tokens を超える")
    expected_cli = _cli_reported(attempt)
    if attempt["cli_reported"] != expected_cli:
        raise LaunchError("attempt.cli_reported binding が不正")
    for field_name in ("codex_exit_code", "validator_rc"):
        item = attempt[field_name]
        if item is not None and (
            isinstance(item, bool) or not isinstance(item, int)
        ):
            raise LaunchError(f"attempt.{field_name} が不正")
    if not isinstance(attempt["termination_verified"], bool):
        raise LaunchError("attempt.termination_verified が bool ではない")
    if attempt["accepted"]:
        if not (
            attempt["limit_trigger"] is None
            and attempt["evidence_status"] == "complete"
            and attempt["metering_status"] == "complete"
            and attempt["codex_exit_code"] == 0
            and attempt["validator_rc"] == 0
            and attempt["process_group_residual"] == 0
            and attempt["termination_verified"]
            and attempt["output_sha256"] is not None
        ):
            raise LaunchError("attempt.accepted semantic binding が不正")
    return attempt


def _validate_receipt(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LaunchError("receipt が object ではない")
    schema_version = value.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version not in (1, 2)
    ):
        raise LaunchError("receipt.schema_version が不正")
    actual_fields = frozenset(value)
    if schema_version == 1:
        # 本 wave 中に schema_version を上げる前に生成された拡張 v1 も、
        # field set が v2 と完全一致する既知の移行形に限って後方互換で読む。
        if actual_fields == _RECEIPT_FIELDS_V1:
            expected_fields = _RECEIPT_FIELDS_V1
        elif actual_fields == _RECEIPT_FIELDS_V2:
            expected_fields = _RECEIPT_FIELDS_V2
        else:
            expected_fields = _RECEIPT_FIELDS_V1
    else:
        expected_fields = _RECEIPT_FIELDS_V2
    receipt = dict(_closed_object(value, expected_fields, label="receipt"))
    if (
        not isinstance(receipt["job_id"], str)
        or _ID_RE.fullmatch(receipt["job_id"]) is None
    ):
        raise LaunchError("receipt.job_id が不正")
    if (
        not isinstance(receipt["prompt_sha256"], str)
        or _SHA256_RE.fullmatch(receipt["prompt_sha256"]) is None
    ):
        raise LaunchError("receipt.prompt_sha256 が不正")
    for field_name in ("model", "reasoning", "codex_version"):
        if not isinstance(receipt[field_name], str) or not receipt[field_name]:
            raise LaunchError(f"receipt.{field_name} が不正")
    if receipt["sandbox"] not in ("read-only", "workspace-write"):
        raise LaunchError("receipt.sandbox が不正")
    for field_name in (
        "cwd",
        "artifact_dir",
        "output_path",
        "manifest_path",
        "codex_executable_path",
    ):
        _absolute_path(receipt[field_name], label=f"receipt.{field_name}")
    if "manifest_repo_root" in receipt:
        _absolute_path(
            receipt["manifest_repo_root"], label="receipt.manifest_repo_root"
        )
    if "manifest_base_commit" in receipt and (
        not isinstance(receipt["manifest_base_commit"], str)
        or _COMMIT_RE.fullmatch(receipt["manifest_base_commit"]) is None
    ):
        raise LaunchError("receipt.manifest_base_commit が不正")
    for field_name in ("output_sha256",):
        value_hash = receipt[field_name]
        if value_hash is not None and (
            not isinstance(value_hash, str)
            or _SHA256_RE.fullmatch(value_hash) is None
        ):
            raise LaunchError(f"receipt.{field_name} が不正")
    if (
        not isinstance(receipt["codex_executable_sha256"], str)
        or _SHA256_RE.fullmatch(receipt["codex_executable_sha256"]) is None
    ):
        raise LaunchError("receipt codex executable sha が不正")
    if (
        not isinstance(receipt["manifest_wave_id"], str)
        or _ID_RE.fullmatch(receipt["manifest_wave_id"]) is None
    ):
        raise LaunchError("receipt.manifest_wave_id が不正")
    if receipt["model_calls_semantics"] != "observed_token_count_events":
        raise LaunchError("receipt.model_calls_semantics が不正")
    if not isinstance(receipt["possible_unobserved_overshoot"], bool):
        raise LaunchError("receipt.possible_unobserved_overshoot が不正")
    if (
        "limits_assertion" in receipt
        and receipt["limits_assertion"] != "self_asserted"
    ):
        raise LaunchError("receipt.limits_assertion が不正")
    if "wall_clock_scope" in receipt:
        expected_wall_scope = (
            "launcher_start_to_receipt_fields_finalized"
            if schema_version == 2
            else "launcher_process"
        )
        if receipt["wall_clock_scope"] != expected_wall_scope:
            raise LaunchError("receipt.wall_clock_scope が不正")
    if receipt["retry_classification"] != "none":
        raise LaunchError("receipt.retry_classification が不正")
    if receipt["escaped_process_containment"] != "not_attempted":
        raise LaunchError("receipt.escaped_process_containment が不正")
    limits = _closed_object(receipt["limits"], _LIMIT_FIELDS, label="limits")
    _strict_number(
        limits["max_wall_clock_s"],
        label="limits.max_wall_clock_s",
        positive=True,
    )
    for field_name in (
        "max_model_calls",
        "max_cli_reported_tokens",
        "max_attempts",
    ):
        _strict_int(limits[field_name], label=f"limits.{field_name}", minimum=1)
    actuals = _closed_object(receipt["actuals"], _ACTUAL_FIELDS, label="actuals")
    _strict_number(actuals["wall_clock_s"], label="actuals.wall_clock_s")
    for field_name in _ACTUAL_FIELDS - {"wall_clock_s"}:
        _strict_int(actuals[field_name], label=f"actuals.{field_name}")
    if actuals["cached_input_tokens"] > actuals["input_tokens"]:
        raise LaunchError("actuals cached_input_tokens が input_tokens を超える")
    if actuals["cli_reported"] != _cli_reported(actuals):
        raise LaunchError("actuals.cli_reported binding が不正")
    attempts_raw = receipt["attempts"]
    if not isinstance(attempts_raw, list):
        raise LaunchError("receipt.attempts が配列でない")
    attempts = [
        _validate_attempt(item, index=index)
        for index, item in enumerate(attempts_raw)
    ]
    expected_actuals = _sum_attempts(attempts)
    for field_name in _ACTUAL_FIELDS - {"wall_clock_s"}:
        if actuals[field_name] != expected_actuals[field_name]:
            raise LaunchError("receipt.actuals と attempts 累積が不一致")
    if Decimal(actuals["wall_clock_s"]) < Decimal(
        expected_actuals["wall_clock_s"]
    ):
        raise LaunchError("receipt.actuals.wall_clock_s が attempt 合計未満")
    last = attempts[-1] if attempts else None
    if receipt["codex_exit_code"] != (
        last["codex_exit_code"] if last else None
    ):
        raise LaunchError("receipt.codex_exit_code terminal binding が不正")
    if receipt["validator_rc"] != (last["validator_rc"] if last else None):
        raise LaunchError("receipt.validator_rc terminal binding が不正")
    if receipt["outcome"] not in (
        "accepted",
        "not_accepted",
        "launcher_error",
    ):
        raise LaunchError("receipt.outcome が不正")
    if receipt["stop_reason"] not in _STOP_REASONS:
        raise LaunchError("receipt.stop_reason が不正")
    if receipt["launcher_rc"] not in (0, 1, 2):
        raise LaunchError("receipt.launcher_rc が不正")
    if not attempts and receipt["outcome"] != "launcher_error":
        raise LaunchError("attempts 空は launcher_error だけで許可される")
    # Checker-side truth table: writer の _writer_truth から独立に閉じる。
    accepted_count = sum(bool(item["accepted"]) for item in attempts)
    triggered = [
        item["limit_trigger"]
        for item in attempts
        if item["limit_trigger"] is not None
    ]
    if receipt["outcome"] == "accepted":
        within_limits = (
            Decimal(actuals["wall_clock_s"])
            <= Decimal(limits["max_wall_clock_s"])
            and actuals["model_calls"] <= limits["max_model_calls"]
            and actuals["cli_reported"]
            <= limits["max_cli_reported_tokens"]
            and actuals["attempt_count"] <= limits["max_attempts"]
        )
        valid_truth = (
            receipt["stop_reason"] == "completed"
            and receipt["launcher_rc"] == 0
            and accepted_count == 1
            and attempts[-1]["accepted"]
            and not triggered
            and within_limits
            and receipt["output_sha256"] == attempts[-1]["output_sha256"]
        )
    elif receipt["outcome"] == "not_accepted":
        expected_stop = triggered[0] if triggered else "max_attempts"
        valid_truth = (
            receipt["stop_reason"] == expected_stop
            and receipt["launcher_rc"] == 1
            and accepted_count == 0
            and receipt["output_sha256"] is None
        )
    else:
        valid_truth = (
            receipt["stop_reason"] == "launcher_error"
            and receipt["launcher_rc"] == 2
            and accepted_count == 0
            and receipt["output_sha256"] is None
        )
    if not valid_truth:
        raise LaunchError("receipt truth table が不正")
    expected_overshoot = any(
        item["metering_status"] != "complete"
        or item["limit_trigger"] is not None
        for item in attempts
    )
    if receipt["possible_unobserved_overshoot"] != expected_overshoot:
        raise LaunchError("possible_unobserved_overshoot binding が不正")
    receipt["attempts"] = attempts
    return receipt


def _sealed_file_matches(
    path: Path,
    *,
    expected_sha256: str,
    expected_bytes: int,
    prefix_only: bool,
) -> bool:
    try:
        digest, size = _hash_file(
            path, limit=expected_bytes if prefix_only else None
        )
        if not prefix_only and size != expected_bytes:
            return False
        return digest == expected_sha256
    except (OSError, LaunchError):
        return False


def _recompute_attempt_metering(
    attempt: Mapping[str, Any],
    *,
    model: str,
    reasoning: str,
) -> tuple[str, str, dict[str, int]]:
    state = AttemptState(
        attempt_index=attempt["attempt_index"],
        started_ns=0,
        stdout_path=Path(attempt["stdout_path"]),
        stderr_path=Path(attempt["stderr_path"]),
        output_path=Path(attempt["output_path"]),
    )
    stdout_raw = state.stdout_path.read_bytes()
    state.stdout_offset = len(stdout_raw)
    if stdout_raw and not stdout_raw.endswith(b"\n"):
        state.stdout_pending = stdout_raw.rsplit(b"\n", 1)[-1]
        closed = stdout_raw[: -len(state.stdout_pending)]
    else:
        closed = stdout_raw
    for raw_line in closed.splitlines():
        if not raw_line.strip():
            continue
        try:
            parsed = parse_jsonl(
                raw_line + b"\n",
                max_bytes=_MAX_EVENT_LINE_BYTES,
                max_line_bytes=_MAX_EVENT_LINE_BYTES,
            )
        except EventValidationError:
            state.stdout_invalid = True
            continue
        _consume_stdout_event(state, parsed[0])
    for rollout_record in attempt["rollouts"]:
        path = Path(rollout_record["path"])
        raw = path.read_bytes()[: rollout_record["bytes"]]
        rollout = RolloutState(
            session_id=rollout_record["session_id"],
            path=path,
            offset=len(raw),
        )
        state.rollouts[rollout.session_id] = rollout
        for raw_line in raw.splitlines():
            if not raw_line.strip():
                continue
            try:
                event = strict_json_loads(
                    raw_line.decode("utf-8"),
                    label="sealed rollout JSONL",
                    max_bytes=_MAX_EVENT_LINE_BYTES,
                )
                if not isinstance(event, dict):
                    raise EventValidationError("rollout event が object でない")
            except (UnicodeDecodeError, EventValidationError):
                rollout.invalid = True
                continue
            _consume_rollout_event(
                rollout, event, model=model, reasoning=reasoning
            )
    state.session_ids = list(attempt["session_ids"])
    return _evidence_status(state), _metering_status(state), _rollout_actuals(state)


def _check_external_expectations(
    receipt: Mapping[str, Any], expectations: Mapping[str, Any]
) -> list[str]:
    direct = {
        "prompt_sha256": "prompt_sha256",
        "job_id": "job_id",
        "wave_id": "manifest_wave_id",
        "repo_root": "manifest_repo_root",
        "base_commit": "manifest_base_commit",
        "output_path": "output_path",
        "model": "model",
        "reasoning": "reasoning",
        "sandbox": "sandbox",
        "cwd": "cwd",
    }
    for option_name, receipt_name in direct.items():
        expected = expectations.get(option_name)
        if (
            expected is not None
            and receipt_name in receipt
            and receipt[receipt_name] != expected
        ):
            raise LaunchError(f"external expectation {option_name} が不一致")
    limit_names = (
        "max_wall_clock_s",
        "max_model_calls",
        "max_cli_reported_tokens",
        "max_attempts",
    )
    self_asserted: list[str] = []
    for field_name in limit_names:
        expected = expectations.get(field_name)
        if expected is None:
            self_asserted.append(field_name)
            continue
        actual = receipt["limits"][field_name]
        if field_name == "max_wall_clock_s":
            matches = Decimal(actual) == Decimal(expected)
        else:
            matches = actual == expected
        if not matches:
            raise LaunchError(f"external expectation {field_name} が不一致")
    return self_asserted


def _receipt_compatibility_skips(
    receipt: Mapping[str, Any],
) -> list[str]:
    if receipt["schema_version"] != 1:
        return []
    return [
        f"v1_missing_{field_name}_check_skipped"
        for field_name in sorted(_RECEIPT_V2_ONLY_FIELDS - receipt.keys())
    ]


def _audit_receipt_value(
    receipt_value: object,
    manifest_path: Path,
    *,
    expectations: Mapping[str, Any],
    check_published_output: bool,
) -> tuple[int, bool, list[str], list[str]]:
    """sealed artifact から actuals を再計算する。

    ``codex_version`` は実行なしには安全に再取得できないため、この監査では
    executable bytes の hash だけを再束縛する。
    """
    receipt = _validate_receipt(receipt_value)
    compatibility_skips = _receipt_compatibility_skips(receipt)
    self_asserted = _check_external_expectations(receipt, expectations)
    if Path(receipt["manifest_path"]) != manifest_path:
        raise LaunchError("CLI --manifest と receipt.manifest_path が不一致")
    recorded_sessions = any(
        attempt["rollouts"] for attempt in receipt["attempts"]
    )
    if manifest_path.exists():
        manifest = _validate_manifest(
            _load_json(manifest_path, label="manifest")
        )
        if manifest["wave_id"] != receipt["manifest_wave_id"]:
            raise LaunchError("receipt と manifest の wave_id が不一致")
        if (
            "manifest_repo_root" in receipt
            and manifest["repo_root"] != receipt["manifest_repo_root"]
        ):
            raise LaunchError("receipt と manifest の repo_root が不一致")
        if (
            "manifest_base_commit" in receipt
            and manifest["base_commit"] != receipt["manifest_base_commit"]
        ):
            raise LaunchError("receipt と manifest の base_commit が不一致")
    elif recorded_sessions or receipt["outcome"] == "accepted":
        raise LaunchError("recorded session に必要な manifest が無い")
    else:
        manifest = None
    codex_path = Path(receipt["codex_executable_path"])
    codex_sha, _ = _hash_file(codex_path)
    if codex_sha != receipt["codex_executable_sha256"]:
        raise LaunchError("codex executable hash が変化")
    rollout_grew = False
    recomputed_attempts: list[dict[str, int]] = []
    for attempt in receipt["attempts"]:
        if not _sealed_file_matches(
            Path(attempt["stdout_path"]),
            expected_sha256=attempt["stdout_sha256"],
            expected_bytes=attempt["stdout_bytes"],
            prefix_only=False,
        ):
            raise LaunchError("attempt stdout seal が不一致")
        if not _sealed_file_matches(
            Path(attempt["stderr_path"]),
            expected_sha256=attempt["stderr_sha256"],
            expected_bytes=attempt["stderr_bytes"],
            prefix_only=False,
        ):
            raise LaunchError("attempt stderr seal が不一致")
        if attempt["output_sha256"] is not None and not _sealed_file_matches(
            Path(attempt["output_path"]),
            expected_sha256=attempt["output_sha256"],
            expected_bytes=attempt["output_bytes"],
            prefix_only=False,
        ):
            raise LaunchError("attempt output seal が不一致")
        for rollout in attempt["rollouts"]:
            rollout_path = Path(rollout["path"])
            if not _sealed_file_matches(
                rollout_path,
                expected_sha256=rollout["sha256"],
                expected_bytes=rollout["bytes"],
                prefix_only=True,
            ):
                raise LaunchError("attempt rollout seal が不一致")
            if rollout_path.stat().st_size > rollout["bytes"]:
                rollout_grew = True
        evidence, metering, actuals = _recompute_attempt_metering(
            attempt,
            model=receipt["model"],
            reasoning=receipt["reasoning"],
        )
        recomputed_attempts.append(actuals)
        if evidence != attempt["evidence_status"]:
            raise LaunchError("attempt evidence_status 再計算が不一致")
        if metering != attempt["metering_status"]:
            raise LaunchError("attempt metering_status 再計算が不一致")
        for field_name, expected in actuals.items():
            if attempt[field_name] != expected:
                raise LaunchError(f"attempt {field_name} 再計算が不一致")
        rollout_session_ids = [
            item["session_id"] for item in attempt["rollouts"]
        ]
        if rollout_session_ids and (
            manifest is None
            or not _manifest_contains(
                manifest,
                job_id=receipt["job_id"],
                attempt_index=attempt["attempt_index"],
                session_ids=rollout_session_ids,
            )
        ):
            raise LaunchError("attempt session が manifest に無い")
    for field_name in _ACTUAL_FIELDS - {"wall_clock_s", "attempt_count"}:
        recomputed = sum(item[field_name] for item in recomputed_attempts)
        if receipt["actuals"][field_name] != recomputed:
            raise LaunchError(f"actuals.{field_name} sealed artifact 再計算が不一致")
    if receipt["actuals"]["attempt_count"] != len(recomputed_attempts):
        raise LaunchError("actuals.attempt_count 再計算が不一致")
    expected_overshoot = any(
        attempt["metering_status"] != "complete"
        or attempt["limit_trigger"] is not None
        for attempt in receipt["attempts"]
    )
    if receipt["possible_unobserved_overshoot"] != expected_overshoot:
        raise LaunchError("possible_unobserved_overshoot 再導出が不一致")
    if receipt["outcome"] == "accepted":
        if check_published_output:
            output_path = Path(receipt["output_path"])
            output_sha, _ = _hash_file(output_path)
            if output_sha != receipt["output_sha256"]:
                raise LaunchError("published output hash が不一致")
            if _validator_rc(output_path) != 0:
                raise LaunchError("published output validator 再実行が失敗")
        return 0, rollout_grew, self_asserted, compatibility_skips
    if receipt["outcome"] == "not_accepted":
        return 1, rollout_grew, self_asserted, compatibility_skips
    return 2, rollout_grew, self_asserted, compatibility_skips


def _check_receipt_paths(
    receipt_path: Path,
    manifest_path: Path,
    *,
    expectations: Mapping[str, Any] | None = None,
    report: bool = False,
) -> int:
    try:
        rc, grew, self_asserted, compatibility_skips = _audit_receipt_value(
            _load_json(receipt_path, label="receipt"),
            manifest_path,
            expectations=expectations or {},
            check_published_output=True,
        )
        if report:
            print(
                json.dumps(
                    {
                        "compatibility_skips": compatibility_skips,
                        "limits_self_asserted": self_asserted,
                        "rollout_grew_since_seal": grew,
                        "schema_version": _load_json(
                            receipt_path, label="receipt"
                        )["schema_version"],
                    },
                    sort_keys=True,
                )
            )
        return rc
    except (LaunchError, OSError, ValueError) as exc:
        if report:
            print(f"NG: {exc}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Codex worker launcher process の wall-clock deadline と observable proxy "
            "metering receipt を提供する"
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--job-id", required=True)
    run.add_argument("--wave-id", required=True)
    run.add_argument("--repo-root", type=Path, required=True)
    run.add_argument("--base-commit", required=True)
    run.add_argument("--prompt-file", type=Path, required=True)
    run.add_argument("--cwd", type=Path, required=True)
    run.add_argument(
        "--sandbox",
        choices=("read-only", "workspace-write"),
        required=True,
    )
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument("--reasoning", required=True)
    run.add_argument(
        "--max-wall-clock-s", type=_positive_decimal, required=True
    )
    run.add_argument("--max-model-calls", type=_positive_int, required=True)
    run.add_argument(
        "--max-cli-reported-tokens", type=_positive_int, required=True
    )
    run.add_argument("--max-attempts", type=_positive_int, default=1)
    run.add_argument("--artifact-dir", type=Path, required=True)
    run.add_argument("--output-file", type=Path, required=True)
    run.add_argument("--receipt", type=Path, required=True)
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--sessions-root", type=Path, default=None)
    run.add_argument("--codex-bin", default="codex")
    run.add_argument(
        "--evidence-grace-s", type=_positive_decimal, default=Decimal("5")
    )
    run.add_argument(
        "--termination-grace-s",
        type=_positive_decimal,
        default=Decimal("2"),
    )
    run.add_argument(
        "--poll-interval-s",
        type=_positive_decimal,
        default=Decimal("0.1"),
    )
    check = subparsers.add_parser("check-receipt")
    check.add_argument("--receipt", type=Path, required=True)
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--expect-prompt-sha256")
    check.add_argument("--expect-job-id")
    check.add_argument("--expect-wave-id")
    check.add_argument("--expect-repo-root", type=Path)
    check.add_argument("--expect-base-commit")
    check.add_argument("--expect-output-path", type=Path)
    check.add_argument("--expect-model")
    check.add_argument("--expect-reasoning")
    check.add_argument(
        "--expect-sandbox", choices=("read-only", "workspace-write")
    )
    check.add_argument("--expect-cwd", type=Path)
    check.add_argument(
        "--expect-max-wall-clock-s", type=_positive_decimal
    )
    check.add_argument("--expect-max-model-calls", type=_positive_int)
    check.add_argument(
        "--expect-max-cli-reported-tokens", type=_positive_int
    )
    check.add_argument("--expect-max-attempts", type=_positive_int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    launcher_started_ns = _LAUNCHER_PROCESS_STARTED_NS
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "check-receipt":
        if not args.receipt.is_absolute() or not args.manifest.is_absolute():
            parser.error("--receipt/--manifest は absolute path が必要")
        expectations = {
            "prompt_sha256": args.expect_prompt_sha256,
            "job_id": args.expect_job_id,
            "wave_id": args.expect_wave_id,
            "repo_root": (
                os.fspath(args.expect_repo_root.resolve())
                if args.expect_repo_root is not None
                else None
            ),
            "base_commit": args.expect_base_commit,
            "output_path": (
                os.fspath(args.expect_output_path.resolve(strict=False))
                if args.expect_output_path is not None
                else None
            ),
            "model": args.expect_model,
            "reasoning": args.expect_reasoning,
            "sandbox": args.expect_sandbox,
            "cwd": (
                os.fspath(args.expect_cwd.resolve())
                if args.expect_cwd is not None
                else None
            ),
            "max_wall_clock_s": args.expect_max_wall_clock_s,
            "max_model_calls": args.expect_max_model_calls,
            "max_cli_reported_tokens": (
                args.expect_max_cli_reported_tokens
            ),
            "max_attempts": args.expect_max_attempts,
        }
        return _check_receipt_paths(
            args.receipt.resolve(strict=False),
            args.manifest.resolve(strict=False),
            expectations=expectations,
            report=True,
        )
    if args.sessions_root is None:
        codex_home = os.environ.get("CODEX_HOME")
        args.sessions_root = (
            Path(codex_home).expanduser() / "sessions"
            if codex_home
            else Path("~/.codex/sessions").expanduser()
        )
    try:
        args.launcher_started_ns = launcher_started_ns
        return _run(args)
    except (LaunchError, OSError, ValueError) as exc:
        print(f"NG: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
