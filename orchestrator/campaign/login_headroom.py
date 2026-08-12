# -*- coding: utf-8 -*-
"""Pegasus login user slice の headroom 観測と予約台帳。

``RESERVE_BYTES`` は対話セッション等へ残す暫定値であり、実測根拠は無い。
``MAX_LOCAL_BUDGET_BYTES`` も 1 コマンドへ渡す暫定上限であり、今後の
実測に応じて見直す。
``STALE_RECORD_MAX_AGE_S`` は、PID の生死も判別できない record が永久に
予約予算を占有し続けるのを防ぐための回収上限である。
観測または予約台帳を安全に扱えない場合は、すべて compute dispatch 側へ倒す。
"""
from __future__ import annotations

import contextlib
import ctypes
import errno
import fcntl
import json
import math
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import secrets
import stat
import time
from typing import Iterator


CEILING_BYTES = 14 * 1024**3
RESERVE_BYTES = 2 * 1024**3
MAX_LOCAL_BUDGET_BYTES = 4 * 1024**3
MIN_LOCAL_BUDGET_BYTES = 1 * 1024**3

ADMISSION_DIRNAME = "izanagi-admission"
LEDGER_LOCK_TIMEOUT_S = 5.0
LEDGER_LOCK_RETRY_S = 0.05
STALE_RECORD_MAX_AGE_S = 3600.0

_CGROUP_ROOT = "/sys/fs/cgroup"
_PROC_SELF_CGROUP = "/proc/self/cgroup"
_CGROUP2_SUPER_MAGIC = 0x63677270
_UINT64_MAX = (1 << 64) - 1
_READ_LIMIT = 1 << 20
_LOCK_NAME = ".lock"
_RECORD_SUFFIX = ".json"
_PEAK_SUFFIX = ".peak"
_MAX_OPERATION_LENGTH = 64

_DIRECTORY_FLAGS = (
    os.O_RDONLY
    | os.O_DIRECTORY
    | os.O_NOFOLLOW
    | getattr(os, "O_CLOEXEC", 0)
)
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


class Admission(Enum):
    LOCAL = "local"
    DISPATCH = "dispatch"


class _LedgerLockTimeout(TimeoutError):
    """予約台帳の lock deadline を超えた。"""


class ReservationLease:
    """台帳上の予約を明示的に解放する handle。"""

    def __init__(self, reservation_name: str, *, base_dir: Path | None) -> None:
        self._reservation_name = reservation_name
        self._base_dir = base_dir
        self._released = False
        self.release_reason: str | None = None
        self.scope_reason: str | None = None

    @property
    def released(self) -> bool:
        return self._released

    def bind_scope(self, scope_cgroup: str | os.PathLike[str]) -> str:
        """予約 record へ、起動後に確定した bounded scope を結び付ける。"""

        if self._released:
            self.scope_reason = "解放済みの予約 record には scope を結び付けられません。"
            return self.scope_reason
        try:
            normalized = _scope_cgroup_value(scope_cgroup)
            assert normalized is not None
            with _locked_ledger(_base_dir=self._base_dir) as directory_fd:
                record = json.loads(
                    _read_ledger_file(directory_fd, self._reservation_name)
                )
                _read_reservation(directory_fd, self._reservation_name)
                record["scope_cgroup"] = normalized
                payload = (
                    json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                ).encode("utf-8")
                _atomic_write(directory_fd, self._reservation_name, payload)
        except _LedgerLockTimeout:
            self.scope_reason = (
                "scope の記録時に台帳 lock を取得できなかったため、PID lease のままです。"
            )
        except Exception as exc:
            self.scope_reason = (
                "予約 record に scope を記録できませんでした"
                f"（{type(exc).__name__}: {exc}）。"
            )
        else:
            self.scope_reason = f"予約 record を scope {normalized} に結び付けました。"
        return self.scope_reason

    def release(self) -> str:
        """予約を解放し、成功・失敗の理由を返す。例外は漏らさない。"""

        if self._released:
            assert self.release_reason is not None
            return self.release_reason
        try:
            with _locked_ledger(_base_dir=self._base_dir) as directory_fd:
                os.unlink(self._reservation_name, dir_fd=directory_fd)
                os.fsync(directory_fd)
        except FileNotFoundError:
            self._released = True
            self.release_reason = "予約 record は既に解放されています。"
        except _LedgerLockTimeout:
            self.release_reason = (
                "予約の解放時に台帳 lock を取得できなかったため、予約 record が残っています。"
            )
        except Exception as exc:
            self.release_reason = (
                "予約 record を解放できなかったため残っています"
                f"（{type(exc).__name__}: {exc}）。"
            )
        else:
            self._released = True
            self.release_reason = "予約 record を解放しました。"
        return self.release_reason

class BudgetGrant(tuple):
    """従来の3要素 tuple 互換を保つ、解放可能な予算 lease handle。"""

    def __new__(
        cls,
        admission: Admission,
        budget_bytes: int | None,
        reason: str,
        lease: ReservationLease | None = None,
    ):
        instance = super().__new__(cls, (admission, budget_bytes, reason))
        instance.lease = lease
        instance.release_reason = None
        return instance

    @property
    def admission(self) -> Admission:
        return self[0]

    @property
    def budget_bytes(self) -> int | None:
        return self[1]

    @property
    def reason(self) -> str:
        return self[2]

    def release(self) -> str:
        """この grant が持つ予約を解放し、理由を返す。"""

        if self.lease is None:
            self.release_reason = "解放対象の予約 record はありません。"
        else:
            self.release_reason = self.lease.release()
        return self.release_reason

    def bind_scope(self, scope_cgroup: str | os.PathLike[str]) -> str:
        if self.lease is None:
            return "scope を結び付ける予約 record はありません。"
        return self.lease.bind_scope(scope_cgroup)


class ReservationDecision(tuple):
    """従来の2要素 tuple 互換を保つ context reservation handle。"""

    def __new__(
        cls,
        admission: Admission,
        reason: str,
        lease: ReservationLease | None = None,
    ):
        instance = super().__new__(cls, (admission, reason))
        instance.lease = lease
        instance.release_reason = None
        return instance

    def release(self) -> str:
        if self.lease is None:
            self.release_reason = "解放対象の予約 record はありません。"
        else:
            self.release_reason = self.lease.release()
        return self.release_reason

    def bind_scope(self, scope_cgroup: str | os.PathLike[str]) -> str:
        if self.lease is None:
            return "scope を結び付ける予約 record はありません。"
        return self.lease.bind_scope(scope_cgroup)


@dataclass(frozen=True)
class LoginHeadroom:
    """user slice の観測値。admission の判定量は ``admission_bytes``。"""

    cgroup_path: Path
    memory_max_bytes: int
    effective_ceiling_bytes: int
    memory_current_bytes: int
    unreclaimable_base_bytes: int
    headroom_bytes: int
    anon_bytes: int
    file_bytes: int
    shmem_bytes: int
    file_dirty_bytes: int
    file_writeback_bytes: int
    slab_reclaimable_bytes: int | None = None
    unevictable_bytes: int | None = None

    @property
    def ceiling_bytes(self) -> int:
        return self.effective_ceiling_bytes

    @property
    def current_bytes(self) -> int:
        return self.memory_current_bytes

    @property
    def occupied_bytes(self) -> int:
        return self.memory_current_bytes

    @property
    def unreclaimable_bytes(self) -> int | None:
        if self.slab_reclaimable_bytes is None or self.unevictable_bytes is None:
            return None
        clean_file = max(
            0,
            self.file_bytes
            - self.shmem_bytes
            - self.file_dirty_bytes
            - self.file_writeback_bytes
            - self.unevictable_bytes,
        )
        reclaimable = clean_file + self.slab_reclaimable_bytes
        if reclaimable > self.unreclaimable_base_bytes:
            return None
        floor = self.anon_bytes + self.shmem_bytes
        value = self.unreclaimable_base_bytes - reclaimable
        return min(self.unreclaimable_base_bytes, max(value, floor))

    @property
    def admission_bytes(self) -> int:
        unreclaimable = self.unreclaimable_bytes
        if unreclaimable is None:
            return self.unreclaimable_base_bytes
        return unreclaimable


class _StatFs(ctypes.Structure):
    _fields_ = [
        ("f_type", ctypes.c_long),
        ("f_bsize", ctypes.c_long),
        ("f_blocks", ctypes.c_ulong),
        ("f_bfree", ctypes.c_ulong),
        ("f_bavail", ctypes.c_ulong),
        ("f_files", ctypes.c_ulong),
        ("f_ffree", ctypes.c_ulong),
        ("f_fsid", ctypes.c_int * 2),
        ("f_namelen", ctypes.c_long),
        ("f_frsize", ctypes.c_long),
        ("f_flags", ctypes.c_long),
        ("f_spare", ctypes.c_long * 4),
    ]


def _filesystem_magic(fd: int) -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    statfs = libc.fstatfs
    statfs.argtypes = (ctypes.c_int, ctypes.POINTER(_StatFs))
    statfs.restype = ctypes.c_int
    result = _StatFs()
    if statfs(fd, ctypes.byref(result)) != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))
    return int(result.f_type)


def _read_fd(fd: int) -> str:
    chunks = []
    size = 0
    while True:
        chunk = os.read(fd, min(65536, _READ_LIMIT + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > _READ_LIMIT:
            raise ValueError("input is too large")
    return b"".join(chunks).decode("utf-8", errors="strict")


def _read_path(path: str) -> str:
    fd = os.open(path, _FILE_FLAGS)
    try:
        return _read_fd(fd)
    finally:
        os.close(fd)


def _read_at(directory_fd: int, name: str) -> str:
    fd = os.open(name, _FILE_FLAGS, dir_fd=directory_fd)
    try:
        return _read_fd(fd)
    finally:
        os.close(fd)


def _parse_uint64(text: str) -> int:
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError("exactly one token is required")
    token = tokens[0]
    if not token.isascii() or not token.isdecimal():
        raise ValueError("unsigned decimal is required")
    value = int(token, 10)
    if value > _UINT64_MAX:
        raise ValueError("value exceeds uint64")
    return value


def _parse_limit(text: str) -> int | None:
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError("exactly one limit token is required")
    if tokens[0] == "max":
        return None
    return _parse_uint64(tokens[0])


def _read_ancestor_memory(directory_fd: int) -> tuple[int, int | None] | None:
    """祖先に memory interface が無ければ無制限階層として返さない。"""

    try:
        current_text = _read_at(directory_fd, "memory.current")
    except FileNotFoundError:
        current_text = None
    try:
        limit_text = _read_at(directory_fd, "memory.max")
    except FileNotFoundError:
        limit_text = None

    current = _parse_uint64(current_text) if current_text is not None else None
    limit = _parse_limit(limit_text) if limit_text is not None else None
    if current_text is None or limit_text is None:
        return None
    assert current is not None
    return current, limit


def _parse_memory_stat(text: str) -> dict[str, int]:
    required = {"anon", "file", "shmem", "file_dirty", "file_writeback"}
    parsed: dict[str, int] = {}
    lines = text.splitlines()
    if not lines:
        raise ValueError("memory.stat is empty")
    for line in lines:
        tokens = line.split()
        if len(tokens) != 2:
            raise ValueError("memory.stat line must contain two tokens")
        name, raw_value = tokens
        if name in parsed:
            raise ValueError("duplicate memory.stat field")
        parsed[name] = _parse_uint64(raw_value)
    if not required.issubset(parsed):
        raise ValueError("required memory.stat field is missing")
    return parsed


def _unified_cgroup_path(text: str, uid: int) -> str:
    unified = []
    for line in text.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            raise ValueError("malformed /proc/self/cgroup entry")
        hierarchy, controllers, path = parts
        if hierarchy == "0" and controllers == "":
            unified.append(path)
    if len(unified) != 1:
        raise ValueError("exactly one unified cgroup entry is required")

    path = unified[0]
    if not path.startswith("/") or "//" in path:
        raise ValueError("unified cgroup path must be absolute and normalized")
    components = path[1:].split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise ValueError("unified cgroup path is not normalized")
    expected = ["user.slice", f"user-{uid}.slice"]
    if components[:2] != expected:
        raise ValueError("process is outside the exact uid user slice")
    return path


def login_headroom() -> LoginHeadroom | None:
    """安全に観測できた headroom を返す。判断不能なら例外を漏らさず ``None``。"""

    directory_fds: list[int] = []
    try:
        uid = os.getuid()
        proc_cgroup = _read_path(_PROC_SELF_CGROUP)
        _unified_cgroup_path(proc_cgroup, uid)

        root_fd = os.open(_CGROUP_ROOT, _DIRECTORY_FLAGS)
        directory_fds.append(root_fd)
        if _filesystem_magic(root_fd) != _CGROUP2_SUPER_MAGIC:
            raise ValueError("cgroup root is not cgroup v2")

        user_fd = os.open("user.slice", _DIRECTORY_FLAGS, dir_fd=root_fd)
        directory_fds.append(user_fd)
        slice_name = f"user-{uid}.slice"
        slice_fd = os.open(slice_name, _DIRECTORY_FLAGS, dir_fd=user_fd)
        directory_fds.append(slice_fd)
        if _filesystem_magic(slice_fd) != _CGROUP2_SUPER_MAGIC:
            raise ValueError("user slice is not on cgroup v2")

        ancestor_memory = []
        for fd in directory_fds[:-1]:
            values = _read_ancestor_memory(fd)
            if values is not None:
                ancestor_memory.append(values)

        current = _parse_uint64(_read_at(slice_fd, "memory.current"))
        memory_max = _parse_limit(_read_at(slice_fd, "memory.max"))
        if memory_max is None:
            raise ValueError("the user slice must have a finite memory.max")

        finite_headrooms = [
            max(0, limit - ancestor_current)
            for ancestor_current, limit in [*ancestor_memory, (current, memory_max)]
            if limit is not None
        ]
        if not finite_headrooms:
            raise ValueError("at least one finite memory.max is required")
        effective_ceiling = min(
            CEILING_BYTES,
            current + min(finite_headrooms),
        )
        stats = _parse_memory_stat(_read_at(slice_fd, "memory.stat"))
        current_after_stat = _parse_uint64(_read_at(slice_fd, "memory.current"))
        return LoginHeadroom(
            cgroup_path=Path(_CGROUP_ROOT) / "user.slice" / slice_name,
            memory_max_bytes=memory_max,
            effective_ceiling_bytes=effective_ceiling,
            memory_current_bytes=current,
            unreclaimable_base_bytes=max(current, current_after_stat),
            headroom_bytes=max(0, effective_ceiling - current),
            anon_bytes=stats["anon"],
            file_bytes=stats["file"],
            shmem_bytes=stats["shmem"],
            file_dirty_bytes=stats["file_dirty"],
            file_writeback_bytes=stats["file_writeback"],
            slab_reclaimable_bytes=stats.get("slab_reclaimable"),
            unevictable_bytes=stats.get("unevictable"),
        )
    except Exception:
        return None
    finally:
        for fd in reversed(directory_fds):
            try:
                os.close(fd)
            except Exception:
                pass


def _admission_base_directory(*, _base_dir: Path | None = None) -> Path:
    """production の namespace は環境変数に依存させない。"""

    if _base_dir is not None:
        return Path(_base_dir)
    return Path("/run/user") / str(os.getuid())


def _admission_directory(*, _base_dir: Path | None = None) -> Path:
    return _admission_base_directory(_base_dir=_base_dir) / ADMISSION_DIRNAME


def _validate_directory_fd(fd: int) -> None:
    metadata = os.fstat(fd)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("ledger path is not a directory")
    if metadata.st_uid != os.geteuid():
        raise PermissionError("ledger directory owner differs from the current uid")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise PermissionError("ledger directory mode must be 0700")


def _validate_file_fd(fd: int) -> None:
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("ledger record is not a regular file")
    if metadata.st_uid != os.geteuid():
        raise PermissionError("ledger record owner differs from the current uid")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise PermissionError("ledger record mode must be 0600")


def _acquire_ledger_lock(lock_fd: int) -> None:
    deadline = time.monotonic() + LEDGER_LOCK_TIMEOUT_S
    while True:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                raise
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _LedgerLockTimeout("ledger lock deadline exceeded")
        time.sleep(min(LEDGER_LOCK_RETRY_S, remaining))


@contextlib.contextmanager
def _locked_ledger(*, _base_dir: Path | None = None) -> Iterator[int]:
    """安全な runtime dir から fd 相対で台帳へ入り、deadline 付きで lock する。"""

    base_fd = os.open(_admission_base_directory(_base_dir=_base_dir), _DIRECTORY_FLAGS)
    directory_fd = -1
    lock_fd = -1
    locked = False
    try:
        _validate_directory_fd(base_fd)
        try:
            os.mkdir(ADMISSION_DIRNAME, mode=0o700, dir_fd=base_fd)
            os.fsync(base_fd)
        except FileExistsError:
            pass
        directory_fd = os.open(ADMISSION_DIRNAME, _DIRECTORY_FLAGS, dir_fd=base_fd)
        _validate_directory_fd(directory_fd)
        lock_fd = os.open(
            _LOCK_NAME,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory_fd,
        )
        _validate_file_fd(lock_fd)
        _acquire_ledger_lock(lock_fd)
        locked = True
        yield directory_fd
    finally:
        if lock_fd >= 0:
            try:
                if locked:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)
        if directory_fd >= 0:
            os.close(directory_fd)
        os.close(base_fd)


def _read_ledger_file(directory_fd: int, name: str) -> str:
    fd = os.open(name, _FILE_FLAGS, dir_fd=directory_fd)
    try:
        _validate_file_fd(fd)
        return _read_fd(fd)
    finally:
        os.close(fd)


def _process_starttime(pid: int) -> int | None:
    """``/proc/<pid>/stat`` field 22。pid 欠落だけ ``None``、他の異常は例外。"""

    try:
        raw = _read_path(f"/proc/{pid}/stat").strip()
    except (FileNotFoundError, ProcessLookupError):
        return None
    close_paren = raw.rfind(")")
    if close_paren <= 0 or close_paren + 2 >= len(raw):
        raise ValueError("malformed /proc pid stat")
    fields_from_state = raw[close_paren + 2 :].split()
    if len(fields_from_state) <= 19:
        raise ValueError("starttime is missing from /proc pid stat")
    return _parse_uint64(fields_from_state[19])


def _scope_cgroup_value(scope_cgroup: str | os.PathLike[str] | None) -> str | None:
    if scope_cgroup is None:
        return None
    value = os.fspath(scope_cgroup)
    root = os.path.normpath(_CGROUP_ROOT)
    if not isinstance(value, str) or not value or not os.path.isabs(value):
        raise ValueError("scope cgroup path must be absolute")
    if os.path.normpath(value) != value or os.path.commonpath((root, value)) != root:
        raise ValueError("scope cgroup path must be normalized below cgroup root")
    relative = os.path.relpath(value, root)
    if relative == "." or any(part in {"", ".", ".."} for part in relative.split(os.sep)):
        raise ValueError("scope cgroup path must name a child cgroup")
    return value


def _scope_cgroup_is_populated(scope_cgroup: str) -> bool | None:
    directory_fds: list[int] = []
    try:
        root = os.path.normpath(_CGROUP_ROOT)
        normalized = _scope_cgroup_value(scope_cgroup)
        assert normalized is not None
        try:
            root_fd = os.open(root, _DIRECTORY_FLAGS)
        except FileNotFoundError:
            return None
        directory_fds.append(root_fd)
        if _filesystem_magic(root_fd) != _CGROUP2_SUPER_MAGIC:
            return None
        relative = os.path.relpath(normalized, root)
        current_fd = root_fd
        for component in relative.split(os.sep):
            try:
                current_fd = os.open(component, _DIRECTORY_FLAGS, dir_fd=current_fd)
            except FileNotFoundError:
                return False
            directory_fds.append(current_fd)
        if _filesystem_magic(current_fd) != _CGROUP2_SUPER_MAGIC:
            return None
        populated = []
        try:
            events_text = _read_at(current_fd, "cgroup.events")
        except FileNotFoundError:
            return None
        for line in events_text.splitlines():
            fields = line.split()
            if len(fields) != 2:
                return None
            if fields[0] == "populated":
                populated.append(fields[1])
        if populated == ["1"]:
            return True
        if populated == ["0"]:
            return False
        return None
    except Exception:
        return None
    finally:
        for fd in reversed(directory_fds):
            try:
                os.close(fd)
            except Exception:
                pass


def _parse_reservation(record: object) -> tuple[int, int, int, str | None]:
    required = {"pid", "starttime", "estimate_bytes", "acquired_at", "scope_cgroup"}
    if not isinstance(record, dict) or set(record) != required:
        raise ValueError("invalid reservation record shape")
    pid = record["pid"]
    starttime = record["starttime"]
    estimate = record["estimate_bytes"]
    acquired_at = record["acquired_at"]
    scope_cgroup = record["scope_cgroup"]
    if type(pid) is not int or pid <= 0:
        raise ValueError("invalid reservation pid")
    if type(starttime) is not int or starttime < 0:
        raise ValueError("invalid reservation starttime")
    if type(estimate) is not int or estimate <= 0:
        raise ValueError("invalid reservation estimate")
    if type(acquired_at) not in {int, float} or not math.isfinite(acquired_at) or acquired_at < 0:
        raise ValueError("invalid reservation timestamp")
    scope_cgroup = _scope_cgroup_value(scope_cgroup)
    return pid, starttime, estimate, scope_cgroup


def _read_reservation(directory_fd: int, name: str) -> tuple[int, int, int, str | None]:
    return _parse_reservation(json.loads(_read_ledger_file(directory_fd, name)))


def _reservation_is_live(pid: int, starttime: int, scope_cgroup: str | None) -> bool:
    try:
        current_starttime = _process_starttime(pid)
    except Exception:
        return True
    if current_starttime == starttime:
        return True
    if scope_cgroup is None:
        return False
    return _scope_cgroup_is_populated(scope_cgroup) is not False


def _record_exceeded_unknown_age_limit(
    directory_fd: int,
    name: str,
    record: object,
) -> bool:
    timestamps: list[float] = []
    if isinstance(record, dict):
        acquired_at = record.get("acquired_at")
        if (
            type(acquired_at) in {int, float}
            and math.isfinite(acquired_at)
            and acquired_at >= 0
        ):
            timestamps.append(float(acquired_at))
    try:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except Exception:
        pass
    else:
        timestamps.append(metadata.st_mtime)
    cutoff = time.time() - STALE_RECORD_MAX_AGE_S
    return any(timestamp < cutoff for timestamp in timestamps)


def _invalid_reservation_is_reclaimable(
    directory_fd: int,
    name: str,
    record: object,
) -> bool:
    """部分情報で死亡を確認し、判定不能なら有限の age 上限を適用する。"""

    if isinstance(record, dict):
        pid = record.get("pid")
        if type(pid) is int and pid > 0:
            try:
                current_starttime = _process_starttime(pid)
            except Exception:
                pass
            else:
                # starttime のない旧 schema でも、PID 欠落は安全に回収できる。
                # PID が生存中なら reuse を除外できないため安全側へ残す。
                return current_starttime is None
    return _record_exceeded_unknown_age_limit(directory_fd, name, record)


def _reclaim_invalid_reservation(
    directory_fd: int,
    name: str,
    issues: list[str],
) -> bool:
    try:
        os.unlink(name, dir_fd=directory_fd)
    except Exception:
        issues.append(f"失効した予約 record {name} を回収できず算入")
        return False
    return True


def _collect_live_reservations(directory_fd: int) -> tuple[int, list[str]]:
    total = 0
    issues: list[str] = []
    for name in os.listdir(directory_fd):
        if not name.endswith(_RECORD_SUFFIX):
            continue
        record: object = None
        try:
            record = json.loads(_read_ledger_file(directory_fd, name))
            pid, starttime, estimate, scope_cgroup = _parse_reservation(record)
        except Exception:
            issue = f"壊れた予約 record {name} を最大予算分として算入"
            if _invalid_reservation_is_reclaimable(directory_fd, name, record):
                if _reclaim_invalid_reservation(directory_fd, name, issues):
                    continue
            total += MAX_LOCAL_BUDGET_BYTES
            issues.append(issue)
            continue
        if _reservation_is_live(pid, starttime, scope_cgroup):
            total += estimate
            continue
        try:
            os.unlink(name, dir_fd=directory_fd)
        except Exception:
            total += estimate
            issues.append(f"失効した予約 record {name} を回収できず算入")
    return total, issues


def _atomic_write(directory_fd: int, final_name: str, payload: bytes) -> None:
    temporary_name = f".{final_name}.{secrets.token_hex(16)}.tmp"
    fd = -1
    try:
        fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory_fd,
        )
        _validate_file_fd(fd)
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(errno.EIO, "short ledger write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(
            temporary_name,
            final_name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass


def _create_reservation(
    directory_fd: int,
    estimate_bytes: int,
    *,
    scope_cgroup: str | os.PathLike[str] | None = None,
) -> str:
    pid = os.getpid()
    starttime = _process_starttime(pid)
    if starttime is None:
        raise ValueError("current process starttime is unavailable")
    final_name = f"{pid}-{secrets.token_hex(16)}{_RECORD_SUFFIX}"
    record = {
        "pid": pid,
        "starttime": starttime,
        "estimate_bytes": estimate_bytes,
        "acquired_at": time.time(),
        "scope_cgroup": _scope_cgroup_value(scope_cgroup),
    }
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    _atomic_write(directory_fd, final_name, payload)
    return final_name


def _issues_suffix(issues: list[str]) -> str:
    if not issues:
        return ""
    return "、" + "、".join(issues)


def _observation_detail(observed: LoginHeadroom) -> str:
    missing = []
    if observed.slab_reclaimable_bytes is None:
        missing.append("slab_reclaimable")
    if observed.unevictable_bytes is None:
        missing.append("unevictable")
    unreclaimable = observed.unreclaimable_bytes
    if missing:
        unreclaimable_detail = f"不明 (欠落キー={','.join(missing)})"
    elif unreclaimable is None:
        unreclaimable_detail = "不明 (snapshot 不整合)"
    else:
        unreclaimable_detail = f"{unreclaimable} bytes"
    return (
        f"現在使用量={observed.memory_current_bytes} bytes、"
        f"回収不能量={unreclaimable_detail}、"
        f"判定占有量={observed.admission_bytes} bytes"
    )


def _decision_locked(
    directory_fd: int,
    estimate_bytes: int,
    *,
    acquire: bool,
    base_dir: Path | None,
    scope_cgroup: str | os.PathLike[str] | None = None,
) -> BudgetGrant:
    observed = login_headroom()
    if observed is None:
        return BudgetGrant(
            Admission.DISPATCH,
            None,
            "ログインノードのメモリ余裕を安全に観測できないため、計算ノードへ dispatch します。",
        )

    reserved, issues = _collect_live_reservations(directory_fd)
    required = observed.admission_bytes + reserved + estimate_bytes + RESERVE_BYTES
    issue_detail = _issues_suffix(issues)
    observation_detail = _observation_detail(observed)
    if required > observed.effective_ceiling_bytes:
        return BudgetGrant(
            Admission.DISPATCH,
            None,
            "ログインノードのメモリ余裕が不足するため、計算ノードへ dispatch します"
            f"（{observation_detail}、生存中の予約={reserved} bytes{issue_detail}、"
            f"見積もり={estimate_bytes} bytes、固定予約={RESERVE_BYTES} bytes、"
            f"実効天井={observed.effective_ceiling_bytes} bytes、必要量={required} bytes）。",
        )
    if not acquire:
        return BudgetGrant(
            Admission.LOCAL,
            estimate_bytes,
            "ログインノードのメモリ余裕と予約枠を確認できたため、local 実行できます"
            f"（{observation_detail}、生存中の予約={reserved} bytes{issue_detail}）。",
        )

    reservation_name = _create_reservation(
        directory_fd,
        estimate_bytes,
        scope_cgroup=scope_cgroup,
    )
    lease = ReservationLease(reservation_name, base_dir=base_dir)
    return BudgetGrant(
        Admission.LOCAL,
        estimate_bytes,
        "ログインノードのメモリ余裕を予約したため、local 実行できます"
        f"（{observation_detail}、生存中の予約={reserved} bytes{issue_detail}）。",
        lease,
    )


def _invalid_estimate(estimate_bytes: object) -> bool:
    return type(estimate_bytes) is not int or estimate_bytes <= 0


def _invalid_budget_limits(max_bytes: object, min_bytes: object) -> bool:
    return (
        type(max_bytes) is not int
        or type(min_bytes) is not int
        or max_bytes <= 0
        or min_bytes < 0
        or min_bytes > max_bytes
    )


def _valid_operation(operation: object) -> bool:
    return (
        isinstance(operation, str)
        and 0 < len(operation) <= _MAX_OPERATION_LENGTH
        and operation.isascii()
        and operation[0].isalnum()
        and all(character.isalnum() or character in "._-" for character in operation)
    )


def _peak_name(operation: str) -> str:
    if not _valid_operation(operation):
        raise ValueError("invalid peak operation")
    return f"peak-{operation}{_PEAK_SUFFIX}"


def _remember_peak_locked(directory_fd: int, operation: str, peak_bytes: int) -> None:
    record = {
        "operation": operation,
        "peak_bytes": peak_bytes,
        "recorded_at": time.time(),
    }
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    _atomic_write(directory_fd, _peak_name(operation), payload)


def _recall_peak_locked(directory_fd: int, operation: str) -> int | None:
    try:
        record = json.loads(_read_ledger_file(directory_fd, _peak_name(operation)))
        if not isinstance(record, dict) or set(record) != {
            "operation",
            "peak_bytes",
            "recorded_at",
        }:
            return None
        peak_bytes = record["peak_bytes"]
        recorded_at = record["recorded_at"]
        if record["operation"] != operation:
            return None
        if type(peak_bytes) is not int or peak_bytes < 0:
            return None
        if type(recorded_at) not in {int, float} or not math.isfinite(recorded_at) or recorded_at < 0:
            return None
        return peak_bytes
    except Exception:
        return None


def remember_peak(
    operation: str,
    peak_bytes: int,
    *,
    _base_dir: Path | None = None,
) -> None:
    """操作ごとの観測ピークを repo 外の user runtime 台帳へ記録する。"""

    if not _valid_operation(operation) or type(peak_bytes) is not int or peak_bytes < 0:
        return
    try:
        with _locked_ledger(_base_dir=_base_dir) as directory_fd:
            _remember_peak_locked(directory_fd, operation, peak_bytes)
    except Exception:
        return


def recall_peak(
    operation: str,
    *,
    _base_dir: Path | None = None,
) -> int | None:
    """前回ピークを返す。未記録・破損・台帳異常はいずれも ``None``。"""

    if not _valid_operation(operation):
        return None
    try:
        with _locked_ledger(_base_dir=_base_dir) as directory_fd:
            return _recall_peak_locked(directory_fd, operation)
    except Exception:
        return None


def _estimate_peak_value(peak_bytes: int, margin: int | float) -> int | None:
    try:
        factor = 1.0 + margin
        if not math.isfinite(factor) or factor < 1.0:
            return None
        numerator, denominator = factor.as_integer_ratio()
        return (peak_bytes * numerator + denominator - 1) // denominator
    except Exception:
        return None


def estimate_for(
    operation: str,
    *,
    margin: float = 0.25,
    _base_dir: Path | None = None,
) -> int | None:
    """前回ピークに ``margin`` を加えた次回見積もりを返す。"""

    if (
        type(margin) not in {int, float}
        or not math.isfinite(margin)
        or margin < 0
    ):
        return None
    peak = recall_peak(operation, _base_dir=_base_dir)
    if peak is None:
        return None
    return _estimate_peak_value(peak, margin)


def grant_budget(
    *,
    max_bytes: int = MAX_LOCAL_BUDGET_BYTES,
    min_bytes: int = MIN_LOCAL_BUDGET_BYTES,
    operation: str | None = None,
    scope_cgroup: str | os.PathLike[str] | None = None,
    _base_dir: Path | None = None,
) -> BudgetGrant:
    """tuple 互換の ``BudgetGrant`` を返し、予約は ``release()`` で解放する。

    ``MAX_LOCAL_BUDGET_BYTES`` は 1 コマンドへ渡す暫定上限であり、実測を
    蓄積して再評価する。予算の確定と予約 record の作成は同じ台帳 lock の
    中で行い、別プロセスがその間へ割り込めないようにする。
    """

    if _invalid_budget_limits(max_bytes, min_bytes):
        return BudgetGrant(
            Admission.DISPATCH,
            None,
            "予算の上限または下限が安全な整数でないため、計算ノードへ dispatch します。",
        )
    if operation is not None and not _valid_operation(operation):
        return BudgetGrant(
            Admission.DISPATCH,
            None,
            "操作識別子が安全な短い文字列でないため、計算ノードへ dispatch します。",
        )
    try:
        normalized_scope = _scope_cgroup_value(scope_cgroup)
    except Exception:
        return BudgetGrant(
            Admission.DISPATCH,
            None,
            "scope cgroup path を安全に検証できないため、計算ノードへ dispatch します。",
        )

    try:
        with _locked_ledger(_base_dir=_base_dir) as directory_fd:
            observed = login_headroom()
            if observed is None:
                return BudgetGrant(
                    Admission.DISPATCH,
                    None,
                    "ログインノードの観測余裕=不明 bytes のため、"
                    "計算ノードへ dispatch します。",
                )

            reserved, issues = _collect_live_reservations(directory_fd)
            available = (
                observed.effective_ceiling_bytes
                - observed.admission_bytes
                - reserved
                - RESERVE_BYTES
            )
            peak = _recall_peak_locked(directory_fd, operation) if operation is not None else None
            estimated = _estimate_peak_value(peak, 0.25) if peak is not None else None
            if peak is not None and estimated is None:
                return BudgetGrant(
                    Admission.DISPATCH,
                    None,
                    "前回ピークから安全な次回見積もりを算出できないため、"
                    "計算ノードへ dispatch します。",
                )
            usable = min(max_bytes, available)
            if estimated is None:
                budget = usable
            else:
                budget = max(estimated, MIN_LOCAL_BUDGET_BYTES)
            detail = (
                f"予約控除後の観測余裕={available} bytes、算出予算={budget} bytes、"
                f"{_observation_detail(observed)}、実効天井="
                f"{observed.effective_ceiling_bytes} bytes、"
                f"生存中の予約={reserved} bytes{_issues_suffix(issues)}"
            )
            if estimated is not None and budget > usable:
                return BudgetGrant(
                    Admission.DISPATCH,
                    None,
                    f"前回ピーク {peak} bytes (scope の raw memory.current peak) の見積もり "
                    f"{estimated} bytes は今の余裕 "
                    f"{usable} bytes に収まらないため、計算ノードへ dispatch します"
                    f"（{detail}）。",
                )
            if budget <= 0 or budget < min_bytes:
                return BudgetGrant(
                    Admission.DISPATCH,
                    None,
                    f"ログインノードの観測余裕が不足しています（{detail}）。",
                )

            reservation_name = _create_reservation(
                directory_fd,
                budget,
                scope_cgroup=normalized_scope,
            )
            lease = ReservationLease(reservation_name, base_dir=_base_dir)
            peak_detail = (
                ""
                if peak is None
                else f"、前回ピーク={peak} bytes (scope の raw memory.current peak)、"
                f"次回見積もり={estimated} bytes"
            )
            return BudgetGrant(
                Admission.LOCAL,
                budget,
                f"ログインノードで {budget} bytes の予算を予約しました"
                f"（{detail}{peak_detail}）。",
                lease,
            )
    except _LedgerLockTimeout:
        return BudgetGrant(
            Admission.DISPATCH,
            None,
            "期限内に台帳 lock を取得できなかったため、計算ノードへ dispatch します。",
        )
    except Exception:
        return BudgetGrant(
            Admission.DISPATCH,
            None,
            "予約台帳を安全に更新できないため、計算ノードへ dispatch します。",
        )


def admit(
    estimate_bytes: int,
    *,
    _base_dir: Path | None = None,
) -> tuple[Admission, str]:
    """``(判定, 日本語の理由)`` を返す。実行時の予約には :func:`reserve` を使う。"""

    if _invalid_estimate(estimate_bytes):
        return (
            Admission.DISPATCH,
            "メモリ推定量が正の整数でないため、計算ノードへ dispatch します。",
        )
    try:
        with _locked_ledger(_base_dir=_base_dir) as directory_fd:
            decision = _decision_locked(
                directory_fd,
                estimate_bytes,
                acquire=False,
                base_dir=_base_dir,
            )
            return decision.admission, decision.reason
    except _LedgerLockTimeout:
        return (
            Admission.DISPATCH,
            "期限内に台帳 lock を取得できなかったため、計算ノードへ dispatch します。",
        )
    except Exception:
        return (
            Admission.DISPATCH,
            "予約台帳を安全に確認できないため、計算ノードへ dispatch します。",
        )


@contextlib.contextmanager
def reserve(
    estimate_bytes: int,
    *,
    scope_cgroup: str | os.PathLike[str] | None = None,
    _base_dir: Path | None = None,
) -> Iterator[ReservationDecision]:
    """同一 lock 内で判定・予約し、context 終了時に予約を解放する。

    例外や SIGINT のように Python stack を unwind する signal でも ``finally`` で
    解放する。強制終了で unwind できない場合は、次回判定時の dead-pid 回収が
    残留 record を取り除く。
    """

    if _invalid_estimate(estimate_bytes):
        yield ReservationDecision(
            Admission.DISPATCH,
            "メモリ推定量が正の整数でないため、計算ノードへ dispatch します。",
        )
        return
    try:
        normalized_scope = _scope_cgroup_value(scope_cgroup)
        with _locked_ledger(_base_dir=_base_dir) as directory_fd:
            grant = _decision_locked(
                directory_fd,
                estimate_bytes,
                acquire=True,
                base_dir=_base_dir,
                scope_cgroup=normalized_scope,
            )
        decision = ReservationDecision(grant.admission, grant.reason, grant.lease)
    except _LedgerLockTimeout:
        decision = ReservationDecision(
            Admission.DISPATCH,
            "期限内に台帳 lock を取得できなかったため、計算ノードへ dispatch します。",
        )
    except Exception:
        decision = ReservationDecision(
            Admission.DISPATCH,
            "予約台帳を安全に更新できないため、計算ノードへ dispatch します。",
        )

    try:
        yield decision
    finally:
        if decision.lease is not None:
            decision.release()


__all__ = [
    "ADMISSION_DIRNAME",
    "Admission",
    "BudgetGrant",
    "CEILING_BYTES",
    "LEDGER_LOCK_RETRY_S",
    "LEDGER_LOCK_TIMEOUT_S",
    "LoginHeadroom",
    "MAX_LOCAL_BUDGET_BYTES",
    "MIN_LOCAL_BUDGET_BYTES",
    "RESERVE_BYTES",
    "ReservationDecision",
    "ReservationLease",
    "admit",
    "estimate_for",
    "grant_budget",
    "login_headroom",
    "recall_peak",
    "remember_peak",
    "reserve",
]
