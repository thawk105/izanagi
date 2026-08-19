# -*- coding: utf-8 -*-
"""task-run/v1 の create-only / append-only ledger writer。"""
from __future__ import annotations

import errno
import fcntl
import hashlib
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
GENERATION_SELF_CHECK_NAME = ".generation-selfcheck"
_GIT_ENV_KEYS = frozenset({
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CEILING_DIRECTORIES",
})
_BANNED_OUTPUT_NAMESPACES = {
    "campaigns", "env", "exploration", "s1-freeze", "s8b-freeze", "s6-rounds", "runs",
}


class PilotClosedError(LedgerError):
    """pilot の正常な閉鎖理由だけを表す型付き例外。"""

    _REASONS = frozenset({"final", "max_task_runs", "max_days"})

    def __init__(self, reason: str) -> None:
        if reason not in self._REASONS:
            raise ValueError(f"unknown pilot closure reason: {reason!r}")
        self.reason = reason
        super().__init__(f"pilot closed: {reason}")


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
        # Every task directory that reached either a publish marker, an
        # incomplete state, or a damaged state consumed pilot capacity.  A
        # damaged/incomplete directory must not be a way around the cap.
        return len(self.published) + len(self.incomplete) + len(self.damaged)

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
    if (
        not isinstance(name, str)
        or name in {"", ".", ".."}
        or "\x00" in name
        or "/" in name
    ):
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


@dataclass
class _DirectoryBinding:
    """Open directory plus the identity of every component used to reach it."""

    path: Path
    fd: int
    identities: tuple[tuple[int, int], ...]


def _directory_identity(fd: int, *, label: str) -> tuple[int, int]:
    try:
        info = os.fstat(fd)
    except OSError as exc:
        raise LedgerError(f"{label} の identity を検査できない") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise LedgerError(f"{label}: directory でない")
    return info.st_dev, info.st_ino


def _absolute_directory_path(path: Path) -> Path:
    path = Path(path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return Path(os.path.normpath(os.fspath(path)))


def _open_directory_binding(path: Path, *, label: str) -> _DirectoryBinding:
    """Open a directory by component and retain its namespace identities."""

    path = _absolute_directory_path(path)
    if path == Path(path.anchor):
        raise LedgerError(f"{label}: filesystem root は対象にできない")
    flags = os.O_RDONLY | _nofollow() | getattr(os, "O_DIRECTORY", 0)
    try:
        current_fd = os.open(path.anchor or os.sep, flags)
    except OSError as exc:
        raise LedgerError(f"{label}: filesystem root を安全に開けない") from exc
    try:
        root_identity = _directory_identity(current_fd, label=f"{label} root")
    except BaseException:
        os.close(current_fd)
        raise
    identities = [root_identity]
    try:
        for component in path.parts[1:]:
            component = _safe_component(component, label=label)
            try:
                next_fd = os.open(component, flags, dir_fd=current_fd)
            except OSError as exc:
                raise LedgerError(f"{label}: directory component を安全に開けない") from exc
            try:
                next_identity = _directory_identity(next_fd, label=label)
            except BaseException:
                os.close(next_fd)
                raise
            identities.append(next_identity)
            os.close(current_fd)
            current_fd = next_fd
        return _DirectoryBinding(path=path, fd=current_fd, identities=tuple(identities))
    except BaseException:
        os.close(current_fd)
        raise


def _verify_directory_binding(binding: _DirectoryBinding, *, label: str = "directory") -> None:
    """Reject a path whose ancestor or final directory was replaced."""

    if _directory_identity(binding.fd, label=label) != binding.identities[-1]:
        raise LedgerError(f"{label} filesystem identity が変化した")
    reopened = _open_directory_binding(binding.path, label=label)
    try:
        if reopened.identities != binding.identities:
            raise LedgerError(f"{label} ancestor filesystem identity が変化した")
        if _directory_identity(reopened.fd, label=label) != _directory_identity(binding.fd, label=label):
            raise LedgerError(f"{label} filesystem identity が変化した")
    finally:
        os.close(reopened.fd)


def _close_directory_binding(binding: _DirectoryBinding | None) -> None:
    if binding is not None:
        os.close(binding.fd)


def _assert_path_matches_fd(path: Path, expected_fd: int, *, label: str) -> None:
    """Check every path component and compare the final component to an open fd."""

    binding = _open_directory_binding(path, label=label)
    try:
        if _directory_identity(binding.fd, label=label) != _directory_identity(expected_fd, label=label):
            raise LedgerError(f"{label} filesystem identity が変化した")
    finally:
        os.close(binding.fd)


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


def _acquire_root_flock(
    fd: int,
    *,
    bounded_wait: bool,
    timeout_s: float | None = None,
) -> None:
    """root flock を手動経路は従来どおり、automatic 経路は有界で取得する。"""

    if not bounded_wait:
        fcntl.flock(fd, fcntl.LOCK_EX)
        return
    effective_timeout = _LOCK_TIMEOUT_S if timeout_s is None else timeout_s
    deadline = _monotonic() + effective_timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EACCES):
                raise LedgerError(f"root lock 取得失敗: {exc}") from exc
            if _monotonic() >= deadline:
                raise LedgerError("root lock timeout") from exc
            time.sleep(0.01)


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


def _git_output(
    cwd: Path,
    *args: str,
    _binding: _DirectoryBinding | None = None,
) -> str:
    if _binding is not None:
        _verify_directory_binding(_binding, label="repo root")
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
    if _binding is not None:
        _verify_directory_binding(_binding, label="repo root")
    return result.stdout.strip()


def _git_head(cwd: Path, *, _binding: _DirectoryBinding | None = None) -> str:
    value = _git_output(cwd, "rev-parse", "--verify", "HEAD", _binding=_binding)
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise LedgerError("git rev-parse HEAD が lowercase 40 hex を返さなかった")
    return value


def _git_commit_exists(cwd: Path, sha: str) -> None:
    _git_output(cwd, "cat-file", "-e", f"{sha}^{{commit}}")


def _pilot_from_root_fd(root_fd: int) -> Mapping[str, Any]:
    raw = _read_file_at(root_fd, "pilot.json", limit=MAX_TASK_BYTES, label="pilot.json")
    return validate_pilot(strict_json_loads(raw, label="pilot.json", max_bytes=MAX_TASK_BYTES))


def _validate_final_marker_fd(root_fd: int) -> None:
    """存在する final marker も closure 判定前に内容まで検査する。"""

    try:
        info = os.stat(FINAL_MARKER_NAME, dir_fd=root_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise DamagedRunError("final marker を検査できない") from exc
    if not stat.S_ISREG(info.st_mode):
        raise DamagedRunError("final marker は regular file でなければならない")
    marker_fd = _open_regular_at(root_fd, FINAL_MARKER_NAME, os.O_RDONLY, label=FINAL_MARKER_NAME)
    try:
        raw = _read_fd(marker_fd, limit=MAX_TASK_BYTES, label=FINAL_MARKER_NAME)
    finally:
        os.close(marker_fd)
    marker = strict_json_loads(raw, label=FINAL_MARKER_NAME, max_bytes=MAX_TASK_BYTES)
    if not isinstance(marker, Mapping):
        raise DamagedRunError("final marker は object でなければならない")
    if set(marker) != {"schema_version", "final_report", "report_sha256"}:
        raise DamagedRunError("final marker の field 集合が不正")
    if marker["schema_version"] != SCHEMA_VERSION:
        raise DamagedRunError("final marker の schema_version が不正")
    final_report = marker["final_report"]
    if (
        not isinstance(final_report, str)
        or not final_report
        or final_report in {".", ".."}
        or "\x00" in final_report
        or "/" in final_report
        or "\\" in final_report
    ):
        raise DamagedRunError("final marker の report 名が不正")
    digest = marker["report_sha256"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise DamagedRunError("final marker の report digest が不正")

    try:
        reports_fd = _open_directory_at(root_fd, "reports", label="reports")
    except LedgerError as exc:
        raise DamagedRunError("final marker の reports directory が存在しない") from exc
    try:
        try:
            report_fd = _open_regular_at(
                reports_fd,
                final_report,
                os.O_RDONLY,
                label=f"reports/{final_report}",
            )
        except LedgerError as exc:
            raise DamagedRunError("final marker が参照する report を開けない") from exc
        try:
            report_digest = hashlib.sha256()
            offset = 0
            while True:
                chunk = os.pread(report_fd, 64 * 1024, offset)
                if not chunk:
                    break
                report_digest.update(chunk)
                offset += len(chunk)
        finally:
            os.close(report_fd)
    finally:
        os.close(reports_fd)
    if report_digest.hexdigest() != digest:
        raise DamagedRunError("final marker の report digest が一致しない")


def _generation_selfcheck_status_fd(root_fd: int) -> str | None:
    try:
        info = os.stat(GENERATION_SELF_CHECK_NAME, dir_fd=root_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise DamagedRunError("generation selfcheck marker を検査できない") from exc
    if not stat.S_ISREG(info.st_mode):
        raise DamagedRunError("generation selfcheck marker は regular file が必要")
    raw = _read_file_at(
        root_fd,
        GENERATION_SELF_CHECK_NAME,
        limit=64,
        label=GENERATION_SELF_CHECK_NAME,
    )
    if raw == b"ok\n":
        return "ok"
    if raw == b"failed\n":
        return "failed"
    raise DamagedRunError("generation selfcheck marker の値が不正")


def _write_generation_selfcheck_status_fd(root_fd: int, status: str) -> None:
    if status not in {"ok", "failed"}:
        raise LedgerError("generation selfcheck marker status が不正")
    _create_file_at(
        root_fd,
        GENERATION_SELF_CHECK_NAME,
        f"{status}\n".encode("ascii"),
        label=GENERATION_SELF_CHECK_NAME,
    )
    os.fsync(root_fd)


def _init_pilot_fd(root_fd: int, *, bounded_wait: bool, lock_timeout_s: float | None = None) -> None:
    """既に安全に open 済みの root fd へ pilot を publish する。"""

    if not stat.S_ISDIR(os.fstat(root_fd).st_mode):
        raise LedgerError("pilot root fd は directory でなければならない")
    locked = False
    try:
        _acquire_root_flock(root_fd, bounded_wait=bounded_wait, timeout_s=lock_timeout_s)
        locked = True
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
        if locked:
            fcntl.flock(root_fd, fcntl.LOCK_UN)


def init_pilot(
    root: Path,
    *,
    bounded_wait: bool = False,
    lock_timeout_s: float | None = None,
    _root_fd: int | None = None,
) -> None:
    """pilot.json を root 排他下で create-only に publish する。"""

    if _root_fd is not None:
        _init_pilot_fd(_root_fd, bounded_wait=bounded_wait, lock_timeout_s=lock_timeout_s)
        return
    root = _ensure_root(root, create=True)
    root_fd = _open_directory(root)
    try:
        _init_pilot_fd(root_fd, bounded_wait=bounded_wait, lock_timeout_s=lock_timeout_s)
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
        if name in {
            "pilot.json",
            FINAL_MARKER_NAME,
            GENERATION_SELF_CHECK_NAME,
            "README.md",
        }:
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

    own_root_fd = root_fd is None
    if own_root_fd:
        root = _ensure_root(root, create=False)
        active_root_fd = _open_directory(root)
    else:
        root = Path(root)
        try:
            if not stat.S_ISDIR(os.fstat(root_fd).st_mode):
                raise LedgerError("root fd は directory でなければならない")
        except OSError as exc:
            raise LedgerError("root fd を検査できない") from exc
        active_root_fd = root_fd
    run_fds: list[int] = []
    event_fds: list[int] = []
    try:
        pilot = _pilot_from_root_fd(active_root_fd)
        _validate_final_marker_fd(active_root_fd)
        _generation_selfcheck_status_fd(active_root_fd)
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
    repo_root: Path | None = None,
    bounded_wait: bool = False,
    lock_timeout_s: float | None = None,
    _root_fd: int | None = None,
) -> str:
    """git HEAD を実測し、events→task publish marker の順で run を生成する。"""

    operation_now = _utc_now()
    root = _ensure_root(root, create=False)
    repo_binding: _DirectoryBinding | None = None
    own_root_fd = _root_fd is None
    root_fd: int
    try:
        if repo_root is not None:
            repo_binding = _open_directory_binding(repo_root, label="repo root")
            _verify_directory_binding(repo_binding, label="repo root")
            try:
                expected_base = Path(
                    __import__("tools.task_runs.generation", fromlist=["series_base_for_repo"])
                    .series_base_for_repo(repo_root)
                ).resolve(strict=False)
                actual_parent = root.parent.resolve(strict=False)
            except (OSError, TypeError, ValueError) as exc:
                raise LedgerError("repo_root と generation root の binding を検査できない") from exc
            if actual_parent != expected_base:
                raise LedgerError("repo_root と generation root の binding が一致しない")
        if own_root_fd:
            root_fd = _open_directory(root)
        else:
            root_fd = _root_fd
            try:
                if not stat.S_ISDIR(os.fstat(root_fd).st_mode):
                    raise LedgerError("root fd は directory でなければならない")
            except OSError as exc:
                raise LedgerError("root fd を検査できない") from exc
        _assert_path_matches_fd(root, root_fd, label="generation root")
        locked = False
        try:
            _acquire_root_flock(root_fd, bounded_wait=bounded_wait, timeout_s=lock_timeout_s)
            locked = True
            pilot = _pilot_from_root_fd(root_fd)
            with _locked_root_snapshot(root, root_fd=root_fd) as (report, _runs):
                pass
            try:
                os.stat(FINAL_MARKER_NAME, dir_fd=root_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise PilotClosedError("final")
            if report.published_run_count >= int(pilot["max_task_runs"]):
                raise PilotClosedError("max_task_runs")
            pilot_started = parse_timestamp(pilot["pilot_started_at"], label="pilot_started_at")
            if operation_now >= pilot_started + timedelta(days=int(pilot["max_days"])):
                raise PilotClosedError("max_days")
            if not isinstance(slug, str) or re_full_slug(slug) is False:
                raise DamagedRunError("slug は 1..48 文字の lowercase 英数字/ハイフン")
            run_id = f"{operation_now.astimezone(timezone.utc):%Y%m%d}-{slug}-{secrets.token_hex(4)}"
            if RUN_ID_RE.fullmatch(run_id) is None:
                raise DamagedRunError("生成した task_run_id が schema に適合しない")
            base_commit = _git_head(
                repo_root if repo_root is not None else root,
                _binding=repo_binding,
            )
            if repo_binding is not None:
                _verify_directory_binding(repo_binding, label="repo root")
            _assert_path_matches_fd(root, root_fd, label="generation root")
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
                if locked:
                    fcntl.flock(root_fd, fcntl.LOCK_UN)
            finally:
                if own_root_fd:
                    os.close(root_fd)
    finally:
        _close_directory_binding(repo_binding)


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
