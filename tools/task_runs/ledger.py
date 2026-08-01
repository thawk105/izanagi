# -*- coding: utf-8 -*-
"""task-run/v1 の create-only / append-only ledger writer。"""
from __future__ import annotations

import errno
import fcntl
import json
import os
import secrets
import stat
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

from .schema import (
    EVENT_TYPES,
    EVENT_ID_RE,
    MAX_EVENTS_BYTES,
    MAX_LINE_BYTES,
    MAX_TASK_BYTES,
    MEASUREMENT_POLICY,
    RUN_ID_RE,
    SHA_RE,
    SCHEMA_VERSION,
    DamagedRunError,
    LedgerError,
    ValidatedRun,
    ensure_regular_fd,
    load_schema,
    parse_events,
    parse_timestamp,
    strict_json_loads,
    validate_documents,
    validate_pilot,
    validate_task,
)


_LOCK_TIMEOUT_S = 2.0
FINAL_MARKER_NAME = "pilot-final.json"
_GIT_ENV_KEYS = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CEILING_DIRECTORIES",
})
_BANNED_OUTPUT_NAMESPACES = {
    "campaigns", "env", "exploration", "s1-freeze", "s8b-freeze", "s6-rounds", "runs",
}


@dataclass(frozen=True)
class DamagedEntry:
    path: Path
    reason: str


@dataclass(frozen=True)
class RootReport:
    root: Path
    published: tuple[Path, ...]
    incomplete: tuple[Path, ...]
    damaged: tuple[DamagedEntry, ...]
    unknown: tuple[Path, ...]

    @property
    def is_valid(self) -> bool:
        return (
            not self.incomplete and not self.damaged and not self.unknown
            and not self.cap_exceeded
        )

    @property
    def published_run_count(self) -> int:
        return len(self.published) + len(self.damaged)

    @property
    def max_task_runs(self) -> int:
        return int(MEASUREMENT_POLICY["max_task_runs"])

    @property
    def cap_excess(self) -> int:
        return max(0, self.published_run_count - self.max_task_runs)

    @property
    def cap_exceeded(self) -> bool:
        return self.cap_excess > 0


def _utc_now() -> datetime:
    """テストが monkeypatch する writer clock。"""

    return datetime.now(timezone.utc)


def _monotonic() -> float:
    """テストが monkeypatch できる overhead/lock clock。"""

    return time.monotonic()


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise LedgerError("writer clock が timezone-aware datetime を返さなかった")
    utc = value.astimezone(timezone.utc)
    if utc.microsecond:
        text = utc.isoformat(timespec="milliseconds")
    else:
        text = utc.isoformat(timespec="seconds")
    return text.replace("+00:00", "Z")


def _canonical(value: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(
                value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise DamagedRunError(f"JSON として canonical serialize できない: {exc}") from exc


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError(errno.EIO, "write が進行しない")
        view = view[written:]


def _nofollow() -> int:
    value = getattr(os, "O_NOFOLLOW", None)
    if value is None:
        raise LedgerError("O_NOFOLLOW が利用できないため fail-closed")
    return value


def _assert_safe_root(root: Path) -> Path:
    try:
        root = Path(root)
    except TypeError as exc:
        raise LedgerError("root は PathLike でなければならない") from exc
    if root.exists() and root.is_symlink():
        raise LedgerError(f"root symlink は禁止: {root}")
    resolved = root.resolve(strict=False)
    parts = resolved.parts
    for index, part in enumerate(parts[:-1]):
        if part == "output" and parts[index + 1] in _BANNED_OUTPUT_NAMESPACES:
            raise LedgerError(f"証拠 namespace 配下を task-run root にできない: {resolved}")
    return root


def _ensure_root(root: Path, *, create: bool) -> Path:
    root = _assert_safe_root(root)
    if create:
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise LedgerError(f"root を作成できない: {root}: {exc}") from exc
    try:
        mode = root.lstat().st_mode
    except OSError as exc:
        raise LedgerError(f"root が存在しない/検査できない: {root}: {exc}") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise LedgerError(f"root は symlink でない directory が必要: {root}")
    return root


def _open_directory(path: Path) -> int:
    flags = os.O_RDONLY | _nofollow() | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise LedgerError(f"directory を安全に開けない: {path}: {exc}") from exc
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise LedgerError(f"directory fd でない: {path}")
    return fd


def _safe_component(name: str, *, label: str) -> str:
    if not isinstance(name, str) or name in {"", ".", ".."} or "/" in name:
        raise LedgerError(f"{label}: unsafe path component")
    return name


def _open_directory_at(parent_fd: int, name: str, *, label: str) -> int:
    name = _safe_component(name, label=label)
    flags = os.O_RDONLY | _nofollow() | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise LedgerError(f"{label} を安全に開けない: {exc}") from exc
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise LedgerError(f"{label}: directory fd でない")
    return fd


def _open_regular(path: Path, flags: int, *, label: str, mode: int = 0o600) -> int:
    try:
        fd = os.open(path, flags | _nofollow(), mode)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise DamagedRunError(f"{label}: symlink は禁止") from exc
        raise LedgerError(f"{label} を安全に開けない: {exc}") from exc
    try:
        ensure_regular_fd(fd, label=label)
    except Exception:
        os.close(fd)
        raise
    return fd


def _open_regular_at(
    parent_fd: int, name: str, flags: int, *, label: str, mode: int = 0o600,
) -> int:
    name = _safe_component(name, label=label)
    try:
        fd = os.open(name, flags | _nofollow(), mode, dir_fd=parent_fd)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise DamagedRunError(f"{label}: symlink は禁止") from exc
        raise LedgerError(f"{label} を安全に開けない: {exc}") from exc
    try:
        ensure_regular_fd(fd, label=label)
    except Exception:
        os.close(fd)
        raise
    return fd


def _read_fd(fd: int, *, limit: int, label: str) -> bytes:
    chunks: list[bytes] = []
    offset = 0
    while True:
        chunk = os.pread(fd, min(64 * 1024, limit + 1 - offset), offset)
        if not chunk:
            break
        chunks.append(chunk)
        offset += len(chunk)
        if offset > limit:
            raise DamagedRunError(f"{label}: size 上限超過 ({offset} > {limit})")
    return b"".join(chunks)


def _read_path(path: Path, *, limit: int, label: str) -> bytes:
    fd = _open_regular(path, os.O_RDONLY, label=label)
    try:
        return _read_fd(fd, limit=limit, label=label)
    finally:
        os.close(fd)


def _read_file_at(parent_fd: int, name: str, *, limit: int, label: str) -> bytes:
    fd = _open_regular_at(parent_fd, name, os.O_RDONLY, label=label)
    try:
        return _read_fd(fd, limit=limit, label=label)
    finally:
        os.close(fd)


def _create_file(path: Path, payload: bytes, *, label: str) -> None:
    fd = _open_regular(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        label=label,
    )
    try:
        _write_all(fd, payload)
        os.fsync(fd)
    except OSError as exc:
        raise LedgerError(f"{label} の write/fsync に失敗: {exc}") from exc
    finally:
        os.close(fd)


def _create_file_at(parent_fd: int, name: str, payload: bytes, *, label: str) -> None:
    fd = _open_regular_at(
        parent_fd, name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, label=label,
    )
    try:
        _write_all(fd, payload)
        os.fsync(fd)
    except OSError as exc:
        raise LedgerError(f"{label} の write/fsync に失敗: {exc}") from exc
    finally:
        os.close(fd)


def _filesystem_repo_root(cwd: Path) -> Path:
    current = cwd.resolve(strict=True)
    if not current.is_dir():
        current = current.parent
    for candidate in (current, *current.parents):
        marker = candidate / ".git"
        if marker.exists() and not marker.is_symlink():
            return candidate
    raise LedgerError("期待する git repository root を filesystem から特定できない")


def _git_run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    clean_env = os.environ.copy()
    for name in _GIT_ENV_KEYS:
        clean_env.pop(name, None)
    try:
        return subprocess.run(
            ["git", "-C", str(cwd), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
            env=clean_env,
        )
    except (OSError, UnicodeError) as exc:
        raise LedgerError(f"git 実測を完遂できない: {exc}") from exc


def _git_output(cwd: Path, *args: str) -> str:
    expected = _filesystem_repo_root(cwd)
    toplevel = _git_run(cwd, "rev-parse", "--show-toplevel")
    if toplevel.returncode != 0:
        raise LedgerError("git toplevel 実測が失敗した (stderr は privacy のため非表示)")
    try:
        actual = Path(toplevel.stdout.strip()).resolve(strict=True)
    except OSError as exc:
        raise LedgerError("git toplevel の解決に失敗") from exc
    if actual != expected:
        raise LedgerError("git toplevel が期待する repository root と一致しない")
    result = _git_run(cwd, *args)
    if result.returncode != 0:
        raise LedgerError("git 実測が失敗した (stderr は privacy のため非表示)")
    return result.stdout.strip()


def _git_head(cwd: Path) -> str:
    value = _git_output(cwd, "rev-parse", "--verify", "HEAD")
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise LedgerError("git rev-parse HEAD が lowercase 40 hex を返さなかった")
    return value


def _git_commit_exists(cwd: Path, sha: str) -> None:
    _git_output(cwd, "cat-file", "-e", f"{sha}^{{commit}}")


def _pilot_from_root_fd(root_fd: int) -> Mapping[str, Any]:
    raw = _read_file_at(root_fd, "pilot.json", limit=MAX_TASK_BYTES, label="pilot.json")
    return validate_pilot(strict_json_loads(raw, label="pilot.json", max_bytes=MAX_TASK_BYTES))


def init_pilot(root: Path) -> None:
    """pilot.json を root 排他下で create-only に publish する。"""

    root = _ensure_root(root, create=True)
    root_fd = _open_directory(root)
    try:
        fcntl.flock(root_fd, fcntl.LOCK_EX)
        pilot = {
            "schema_version": SCHEMA_VERSION,
            "pilot_started_at": _format_timestamp(_utc_now()),
            "max_task_runs": 10,
            "max_days": 14,
        }
        validate_pilot(pilot)
        _create_file_at(root_fd, "pilot.json", _canonical(pilot), label="pilot.json")
        os.fsync(root_fd)
    finally:
        try:
            fcntl.flock(root_fd, fcntl.LOCK_UN)
        finally:
            os.close(root_fd)


def _valid_task_marker_fd(run_fd: int, run_name: str) -> bool:
    try:
        raw = _read_file_at(
            run_fd, "task.json", limit=MAX_TASK_BYTES, label=f"{run_name}/task.json",
        )
        task = strict_json_loads(raw, label=f"{run_name}/task.json", max_bytes=MAX_TASK_BYTES)
        validate_task(task, directory_name=run_name)
    except LedgerError:
        return False
    return True


def _root_candidates(
    root: Path, root_fd: int,
) -> tuple[list[tuple[Path, int]], list[Path], list[Path]]:
    candidates: list[tuple[Path, int]] = []
    incomplete: list[Path] = []
    unknown: list[Path] = []
    try:
        names = sorted(os.listdir(root_fd))
    except OSError as exc:
        raise LedgerError(f"root entry を列挙できない: {exc}") from exc
    for name in names:
        entry = root / name
        if name in {"pilot.json", FINAL_MARKER_NAME, "README.md"}:
            # README.md は文書化された layout の一部 (output/task-runs/README.md が詳細正本)。
            continue
        if name == "reports":
            try:
                info = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            except OSError:
                unknown.append(entry)
            else:
                if not stat.S_ISDIR(info.st_mode):
                    unknown.append(entry)
            continue
        if RUN_ID_RE.fullmatch(name) is None:
            unknown.append(entry)
            continue
        try:
            run_fd = _open_directory_at(root_fd, name, label=f"{name}/")
        except LedgerError:
            unknown.append(entry)
            continue
        if not _valid_task_marker_fd(run_fd, name):
            os.close(run_fd)
            incomplete.append(entry)
            continue
        candidates.append((entry, run_fd))
    return candidates, incomplete, unknown


def _damage_reason(exc: BaseException) -> str:
    if isinstance(exc, DamagedRunError):
        return "invalid-run"
    if isinstance(exc, LedgerError):
        return "run-io-error"
    return "unexpected-validation-error"


@contextmanager
def _locked_root_snapshot(
    root: Path, *, root_fd: int | None = None,
) -> Iterator[tuple[RootReport, tuple[ValidatedRun, ...]]]:
    """Lock every candidate events fd in name order and validate those exact bytes."""

    root = _ensure_root(root, create=False)
    own_root_fd = root_fd is None
    active_root_fd = _open_directory(root) if root_fd is None else root_fd
    run_fds: list[int] = []
    event_fds: list[int] = []
    try:
        pilot = _pilot_from_root_fd(active_root_fd)
        candidates, incomplete, unknown = _root_candidates(root, active_root_fd)
        run_fds = [run_fd for _, run_fd in candidates]
        opened: list[tuple[Path, int, int]] = []
        damaged: list[DamagedEntry] = []
        for (path, run_fd) in candidates:
            events_fd: int | None = None
            try:
                events_fd = _open_regular_at(
                    run_fd, "events.jsonl", os.O_RDONLY, label=f"{path.name}/events.jsonl",
                )
                _acquire_flock(events_fd)
            except LedgerError as exc:
                if events_fd is not None:
                    os.close(events_fd)
                damaged.append(DamagedEntry(path, _damage_reason(exc)))
                continue
            event_fds.append(events_fd)
            opened.append((path, run_fd, events_fd))

        published: list[Path] = []
        validated_runs: list[ValidatedRun] = []
        for path, run_fd, events_fd in opened:
            try:
                task, _events_raw, validated = _task_and_events_from_locked_fd(
                    path, run_fd, events_fd,
                )
                policy = task["measurement_policy"]
                if not isinstance(policy, Mapping) or (
                    policy.get("max_task_runs") != pilot["max_task_runs"]
                    or policy.get("max_days") != pilot["max_days"]
                ):
                    raise DamagedRunError("measurement policy mismatch")
            except Exception as exc:
                damaged.append(DamagedEntry(path, _damage_reason(exc)))
            else:
                published.append(path)
                validated_runs.append(validated)
        report = RootReport(
            root=root,
            published=tuple(published),
            incomplete=tuple(incomplete),
            damaged=tuple(sorted(damaged, key=lambda item: item.path.name)),
            unknown=tuple(unknown),
        )
        yield report, tuple(validated_runs)
    finally:
        for fd in reversed(event_fds):
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        for fd in reversed(run_fds):
            os.close(fd)
        if own_root_fd:
            os.close(active_root_fd)


def validate_root(root: Path) -> RootReport:
    """root と pilot manifest を検査し run を4分類する。"""

    with _locked_root_snapshot(root) as (report, _runs):
        return report


def discover_runs(root: Path) -> tuple[Path, ...]:
    """publish marker が valid な run (events 破損 run を含む) を安定順で返す。"""

    with _locked_root_snapshot(root) as (report, _runs):
        candidates = list(report.published) + [item.path for item in report.damaged]
        return tuple(sorted(candidates, key=lambda path: path.name))


def start_run(
    root: Path,
    *,
    slug: str,
    objective: str,
    task_class: int,
    task_kind: str,
) -> str:
    """git HEAD を実測し、events→task publish marker の順で run を生成する。"""

    operation_now = _utc_now()
    root = _ensure_root(root, create=False)
    root_fd = _open_directory(root)
    try:
        fcntl.flock(root_fd, fcntl.LOCK_EX)
        pilot = _pilot_from_root_fd(root_fd)
        try:
            os.stat(FINAL_MARKER_NAME, dir_fd=root_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise LedgerError("pilot は final report により凍結済み")
        with _locked_root_snapshot(root, root_fd=root_fd) as (report, _runs):
            pass
        if report.damaged or report.unknown:
            raise LedgerError("root に damaged/unknown entry があるため start を拒否")
        if len(report.published) >= int(pilot["max_task_runs"]):
            raise LedgerError("pilot の max_task_runs に到達")
        pilot_started = parse_timestamp(pilot["pilot_started_at"], label="pilot_started_at")
        if operation_now >= pilot_started + timedelta(days=int(pilot["max_days"])):
            raise LedgerError("pilot の max_days に到達")
        if not isinstance(slug, str) or re_full_slug(slug) is False:
            raise DamagedRunError("slug は 1..48 文字の lowercase 英数字/ハイフン")
        run_id = f"{operation_now.astimezone(timezone.utc):%Y%m%d}-{slug}-{secrets.token_hex(4)}"
        if RUN_ID_RE.fullmatch(run_id) is None:
            raise DamagedRunError("生成した task_run_id が schema に適合しない")
        base_commit = _git_head(root)
        task: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "task_run_id": run_id,
            "objective": objective,
            "task_class": task_class,
            "task_kind": task_kind,
            "started_at": _format_timestamp(operation_now),
            "base_commit": base_commit,
            "base_commit_source": "git-observed",
            "authority": "development-observation-not-evidence",
            "measurement_policy": dict(MEASUREMENT_POLICY),
        }
        validate_task(task, directory_name=run_id)
        try:
            os.mkdir(run_id, 0o700, dir_fd=root_fd)
        except FileExistsError as exc:
            raise LedgerError(f"task-run は既に存在する: {run_id}") from exc
        except OSError as exc:
            raise LedgerError(f"task-run directory を作成できない: {exc}") from exc
        # task.json が唯一の publish marker。中断時の部分物は自動削除しない。
        run_fd = _open_directory_at(root_fd, run_id, label=f"{run_id}/")
        try:
            # mkdir と events の directory entry を task publish より先に durable にする。
            # 途中停止なら task.json の無い incomplete-start として残る。
            os.fsync(root_fd)
            _create_file_at(run_fd, "events.jsonl", b"", label=f"{run_id}/events.jsonl")
            os.fsync(run_fd)
            _create_file_at(run_fd, "task.json", _canonical(task), label=f"{run_id}/task.json")
            os.fsync(run_fd)
        finally:
            os.close(run_fd)
        os.fsync(root_fd)
        return run_id
    finally:
        try:
            fcntl.flock(root_fd, fcntl.LOCK_UN)
        finally:
            os.close(root_fd)


def re_full_slug(slug: str) -> bool:
    if not 1 <= len(slug) <= 48:
        return False
    if slug[0] == "-" or slug[-1] == "-":
        return False
    return all(ch in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in slug)


def validate_run(run_dir: Path, *, require_finished: bool = False) -> ValidatedRun:
    """task/events を strict に読み、末尾 truncate を含む破損を一切許容しない。"""

    load_schema()
    run_dir = Path(run_dir)
    run_fd = _open_directory(run_dir)
    try:
        events_fd = _open_regular_at(
            run_fd, "events.jsonl", os.O_RDONLY, label="events.jsonl",
        )
        try:
            _task, _events_raw, validated = _task_and_events_from_locked_fd(
                run_dir, run_fd, events_fd, require_finished=require_finished,
            )
            return validated
        finally:
            os.close(events_fd)
    finally:
        os.close(run_fd)


def _source_for(event_type: str, payload: Mapping[str, object], *, wrapper: bool) -> dict[str, str]:
    if event_type == "stage_start" or event_type == "task_end":
        triple = ("not-applicable", "not-applicable", "not-applicable")
    elif event_type == "stage_end":
        triple = ("timestamp-delta", "not-applicable", "not-applicable")
    elif event_type == "agent_run":
        tokens = payload.get("tokens")
        values = tokens.values() if isinstance(tokens, Mapping) else ()
        token_source = "product-reported" if any(value is not None for value in values) else "not-exposed"
        triple = (
            "monotonic-clock" if wrapper else "caller-supplied",
            "wrapper-observed" if wrapper else "caller-supplied",
            token_source,
        )
    elif event_type == "test_run":
        has_tool_metrics = any(
            payload.get(name) is not None
            for name in ("collected", "passed", "failed", "skipped", "collected_node_digest")
        )
        triple = (
            "monotonic-clock" if wrapper else "caller-supplied",
            ("tool-reported" if has_tool_metrics else "wrapper-observed")
            if wrapper else "caller-supplied",
            "not-applicable",
        )
    elif event_type == "wait" or event_type == "rework":
        triple = ("caller-supplied", "not-applicable", "not-applicable")
    elif event_type == "finding_summary":
        triple = ("not-applicable", "caller-supplied", "not-applicable")
    elif event_type == "commit":
        triple = ("not-applicable", "git-observed", "not-applicable")
    else:
        raise DamagedRunError(f"unknown event: {event_type!r}")
    return {"timestamp": "system-clock", "duration": triple[0], "metrics": triple[1], "tokens": triple[2]}


def _acquire_flock(fd: int, *, timeout_s: float = _LOCK_TIMEOUT_S) -> None:
    deadline = _monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EACCES):
                raise LedgerError(f"events lock 取得失敗: {exc}") from exc
            if _monotonic() >= deadline:
                raise LedgerError("events lock timeout") from exc
            time.sleep(0.01)


def _task_and_events_from_locked_fd(
    run_dir: Path,
    run_fd: int,
    events_fd: int,
    *,
    require_finished: bool = False,
) -> tuple[Mapping[str, Any], bytes, ValidatedRun]:
    task_raw = _read_file_at(run_fd, "task.json", limit=MAX_TASK_BYTES, label="task.json")
    task = strict_json_loads(task_raw, label="task.json", max_bytes=MAX_TASK_BYTES)
    if not isinstance(task, dict):
        raise DamagedRunError("task.json は object でなければならない")
    events_raw = _read_fd(events_fd, limit=MAX_EVENTS_BYTES, label="events.jsonl")
    events = parse_events(events_raw)
    return task, events_raw, validate_documents(
        run_dir,
        task,
        events,
        require_finished=require_finished,
        task_raw=task_raw,
        events_raw=events_raw,
    )


def _fresh_event_id(events: tuple[Mapping[str, object], ...]) -> str:
    existing = {str(event["event_id"]) for event in events}
    for _ in range(32):
        candidate = secrets.token_hex(8)
        if EVENT_ID_RE.fullmatch(candidate) is not None and candidate not in existing:
            return candidate
    raise LedgerError("一意な event_id を生成できない")


def _append_event(
    root: Path,
    task_run_id: str,
    event_type: str,
    payload: Mapping[str, object],
    *,
    wrapper: bool,
) -> Mapping[str, object]:
    started = _monotonic()
    if not isinstance(event_type, str) or event_type not in EVENT_TYPES:
        raise DamagedRunError("unknown event type")
    if not isinstance(task_run_id, str) or RUN_ID_RE.fullmatch(task_run_id) is None:
        raise LedgerError("task_run_id format 不正")
    if not isinstance(payload, Mapping):
        raise DamagedRunError("payload は Mapping でなければならない")
    supplied = dict(payload)
    reserved = {
        "schema_version", "task_run_id", "seq", "timestamp", "event", "event_id",
        "measurement_source", "recording_duration_s",
    }
    collision = reserved.intersection(supplied)
    if collision:
        raise DamagedRunError(f"writer 専有 field を payload へ指定できない: {sorted(collision)}")
    root = _ensure_root(root, create=False)
    root_fd = _open_directory(root)
    try:
        pilot = _pilot_from_root_fd(root_fd)
    except Exception:
        os.close(root_fd)
        raise
    try:
        run_fd = _open_directory_at(root_fd, task_run_id, label=f"{task_run_id}/")
    except Exception:
        os.close(root_fd)
        raise
    run_dir = root / task_run_id
    try:
        events_fd = _open_regular_at(
            run_fd, "events.jsonl", os.O_RDWR | os.O_APPEND, label="events.jsonl",
        )
    except Exception:
        os.close(run_fd)
        os.close(root_fd)
        raise
    try:
        _acquire_flock(events_fd)
        task, old_raw, validated = _task_and_events_from_locked_fd(run_dir, run_fd, events_fd)
        policy = task["measurement_policy"]
        if not isinstance(policy, Mapping) or (
            policy.get("max_task_runs") != pilot["max_task_runs"]
            or policy.get("max_days") != pilot["max_days"]
        ):
            raise DamagedRunError("task measurement_policy が pilot.json と一致しない")
        now = _utc_now()
        timestamp_text = _format_timestamp(now)
        timestamp_value = parse_timestamp(timestamp_text, label="writer timestamp")
        if event_type == "stage_end":
            if "duration_s" in supplied:
                raise DamagedRunError("stage_end.duration_s は writer が timestamp 差から決める")
            if validated.open_stage_id is None:
                raise DamagedRunError("open stage の無い stage_end")
            opened = next(
                event for event in reversed(validated.events)
                if event["event"] == "stage_start" and event["stage_id"] == validated.open_stage_id
            )
            opened_at = parse_timestamp(opened["timestamp"], label="stage_start.timestamp")
            supplied["duration_s"] = round((timestamp_value - opened_at).total_seconds(), 3)
        elif event_type in {"agent_run", "test_run", "wait", "rework"}:
            duration = supplied.get("duration_s")
            if isinstance(duration, bool) or not isinstance(duration, (int, float)):
                raise DamagedRunError(f"{event_type}.duration_s は number でなければならない")
            supplied["duration_s"] = round(float(duration), 3)
        if event_type == "commit":
            sha = supplied.get("commit_sha")
            if not isinstance(sha, str) or SHA_RE.fullmatch(sha) is None:
                raise DamagedRunError("commit_sha は lowercase 40 hex でなければならない")
            _git_commit_exists(run_dir, sha)
        record: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "task_run_id": task_run_id,
            "seq": len(validated.events) + 1,
            "timestamp": timestamp_text,
            "event": event_type,
            "event_id": _fresh_event_id(validated.events),
            "measurement_source": _source_for(event_type, supplied, wrapper=wrapper),
        }
        record.update(supplied)
        # 1回目の serialize と lock 待ちを測り、fsync 後は含めない。最終 serialize 自身は
        # 自己参照になるため、直前の serialize を proxy とする。
        _canonical(record)
        record["recording_duration_s"] = round(max(0.0, _monotonic() - started), 3)
        line = _canonical(record)
        if len(line) - 1 > MAX_LINE_BYTES:
            raise DamagedRunError("candidate event が 1行上限を超える")
        virtual = old_raw + line
        if len(virtual) > MAX_EVENTS_BYTES:
            raise DamagedRunError("candidate event で events.jsonl 上限を超える")
        virtual_events = parse_events(virtual)
        validate_documents(run_dir, task, virtual_events)
        try:
            _write_all(events_fd, line)
            os.fsync(events_fd)
        except OSError as exc:
            # 曖昧な write/fsync failure は同一 fd を再読し、確定済み event_id が
            # 完全な record として存在するときだけ成功扱いにする。
            after = _read_fd(events_fd, limit=MAX_EVENTS_BYTES, label="events.jsonl")
            try:
                after_events = parse_events(after)
                validate_documents(run_dir, task, after_events)
            except LedgerError:
                raise LedgerError(f"append が曖昧に失敗し stream も破損: {exc}") from exc
            for existing in after_events:
                if existing["event_id"] == record["event_id"]:
                    return existing
            raise LedgerError(f"append write/fsync が失敗: {exc}") from exc
        return record
    finally:
        try:
            fcntl.flock(events_fd, fcntl.LOCK_UN)
        finally:
            os.close(events_fd)
            os.close(run_fd)
            os.close(root_fd)


def append_event(
    root: Path,
    task_run_id: str,
    event_type: str,
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    """汎用経路。timestamp/source/seq/event_id は writer が決定する。"""

    return _append_event(root, task_run_id, event_type, payload, wrapper=False)


def record_test_run(
    root: Path,
    task_run_id: str,
    *,
    suite_id: str,
    suite_kind: str,
    duration_s: float,
    exit_status: int,
    counts: Mapping[str, int | None] | None,
    trigger: str,
    collected_node_digest: str | None,
) -> Mapping[str, object]:
    """test wrapper duration と tool-reported sidecar metrics の記録経路。"""

    normalized = dict(counts or {})
    count_names = {"collected", "passed", "failed", "skipped"}
    if set(normalized) - count_names:
        raise DamagedRunError(f"counts に unknown field: {sorted(set(normalized) - count_names)}")
    payload: dict[str, object] = {
        "stage_id": None,
        "suite_id": suite_id,
        "suite_kind": suite_kind,
        "duration_s": duration_s,
        "collected": normalized.get("collected"),
        "passed": normalized.get("passed"),
        "failed": normalized.get("failed"),
        "skipped": normalized.get("skipped"),
        "exit_status": exit_status,
        "trigger": trigger,
        "collected_node_digest": collected_node_digest,
    }
    return _append_event(root, task_run_id, "test_run", payload, wrapper=True)


def finish_run(root: Path, task_run_id: str, outcome: str) -> Mapping[str, object]:
    """task_end を追記する。task.json は更新しない。"""

    return _append_event(root, task_run_id, "task_end", {"outcome": outcome}, wrapper=False)


def selfcheck(root: Path) -> None:
    """実 root の O_EXCL/flock/O_APPEND/fsync 前提を process 越しに実測する。"""

    root = _ensure_root(root, create=True)
    root_fd = _open_directory(root)
    name = f".task-run-selfcheck-{secrets.token_hex(8)}"
    work = root / name
    exclusive = work / "exclusive"
    lock_path = work / "lock"
    append_path = work / "append"
    created: list[Path] = []
    try:
        fcntl.flock(root_fd, fcntl.LOCK_EX)
        os.mkdir(work, 0o700)
        os.fsync(root_fd)
        created.append(exclusive)
        _create_file(exclusive, b"one\n", label="selfcheck O_EXCL")
        try:
            _create_file(exclusive, b"two\n", label="selfcheck O_EXCL collision")
        except LedgerError as exc:
            if not isinstance(exc.__cause__, FileExistsError):
                raise
        else:
            raise LedgerError("selfcheck: O_EXCL が既存 file を拒否しなかった")
        if _read_path(exclusive, limit=64, label="selfcheck exclusive") != b"one\n":
            raise LedgerError("selfcheck: O_EXCL collision で既存 bytes が変化")

        created.append(lock_path)
        _create_file(lock_path, b"", label="selfcheck lock")
        lock_fd = _open_regular(lock_path, os.O_RDWR, label="selfcheck lock")
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            pid = os.fork()
            if pid == 0:  # pragma: no cover - child の成否は exit status で親が検査
                child_fd = os.open(lock_path, os.O_RDWR | _nofollow())
                try:
                    try:
                        fcntl.flock(child_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except OSError as exc:
                        os._exit(0 if exc.errno in (errno.EAGAIN, errno.EACCES) else 2)
                    os._exit(3)
                finally:
                    os.close(child_fd)
            _, status = os.waitpid(pid, 0)
            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                raise LedgerError("selfcheck: 2 process flock 排他が成立しない")
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)

        created.append(append_path)
        _create_file(append_path, b"", label="selfcheck append")
        children: list[int] = []
        for marker in (b"a", b"b"):
            pid = os.fork()
            if pid == 0:  # pragma: no cover - child の成否は exit status で親が検査
                child_fd = os.open(append_path, os.O_WRONLY | os.O_APPEND | _nofollow())
                try:
                    for index in range(32):
                        _write_all(child_fd, marker + f"-{index:02d}\n".encode("ascii"))
                    os.fsync(child_fd)
                    os._exit(0)
                except BaseException:
                    os._exit(4)
                finally:
                    os.close(child_fd)
            children.append(pid)
        for pid in children:
            _, status = os.waitpid(pid, 0)
            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                raise LedgerError("selfcheck: O_APPEND child が失敗")
        lines = _read_path(append_path, limit=4096, label="selfcheck append").splitlines()
        expected = {marker + f"-{index:02d}".encode("ascii") for marker in (b"a", b"b") for index in range(32)}
        if len(lines) != 64 or set(lines) != expected:
            raise LedgerError("selfcheck: O_APPEND 追記が欠落/融合した")
        work_fd = _open_directory(work)
        try:
            os.fsync(work_fd)
        finally:
            os.close(work_fd)
    finally:
        try:
            for path in reversed(created):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            try:
                work.rmdir()
            except FileNotFoundError:
                pass
            os.fsync(root_fd)
        finally:
            try:
                fcntl.flock(root_fd, fcntl.LOCK_UN)
            finally:
                os.close(root_fd)
