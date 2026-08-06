# -*- coding: utf-8 -*-
"""Pegasus login user slice の headroom 観測と予約台帳。

``RESERVE_BYTES`` は対話セッション等へ残す暫定値であり、実測根拠は無い。
``MAX_LOCAL_BUDGET_BYTES`` も 1 コマンドへ渡す暫定上限であり、今後の
実測に応じて見直す。
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
import time
from typing import Iterator


CEILING_BYTES = 14 * 1024**3
RESERVE_BYTES = 2 * 1024**3
MAX_LOCAL_BUDGET_BYTES = 4 * 1024**3
MIN_LOCAL_BUDGET_BYTES = 1 * 1024**3

ADMISSION_DIRNAME = "izanagi-admission"
ADMISSION_BASE_DIR_ENV = "IZANAGI_ADMISSION_BASE_DIR"

_CGROUP_ROOT = "/sys/fs/cgroup"
_PROC_SELF_CGROUP = "/proc/self/cgroup"
_CGROUP2_SUPER_MAGIC = 0x63677270
_UINT64_MAX = (1 << 64) - 1
_READ_LIMIT = 1 << 20
_LOCK_NAME = ".lock"
_RECORD_SUFFIX = ".json"

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


@dataclass(frozen=True)
class LoginHeadroom:
    """user slice の観測値。判定上の占有量は ``memory_current_bytes``。"""

    cgroup_path: Path
    memory_max_bytes: int
    effective_ceiling_bytes: int
    memory_current_bytes: int
    headroom_bytes: int
    anon_bytes: int
    file_bytes: int
    shmem_bytes: int
    file_dirty_bytes: int
    file_writeback_bytes: int

    @property
    def ceiling_bytes(self) -> int:
        return self.effective_ceiling_bytes

    @property
    def current_bytes(self) -> int:
        return self.memory_current_bytes

    @property
    def occupied_bytes(self) -> int:
        return self.memory_current_bytes


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
        return LoginHeadroom(
            cgroup_path=Path(_CGROUP_ROOT) / "user.slice" / slice_name,
            memory_max_bytes=memory_max,
            effective_ceiling_bytes=effective_ceiling,
            memory_current_bytes=current,
            headroom_bytes=max(0, effective_ceiling - current),
            anon_bytes=stats["anon"],
            file_bytes=stats["file"],
            shmem_bytes=stats["shmem"],
            file_dirty_bytes=stats["file_dirty"],
            file_writeback_bytes=stats["file_writeback"],
        )
    except Exception:
        return None
    finally:
        for fd in reversed(directory_fds):
            try:
                os.close(fd)
            except Exception:
                pass


def _admission_directory() -> Path:
    override = os.environ.get(ADMISSION_BASE_DIR_ENV)
    if override is not None:
        if not override:
            raise ValueError("empty admission base directory")
        base = Path(override)
    else:
        base = Path("/run/user") / str(os.getuid())
    return base / ADMISSION_DIRNAME


@contextlib.contextmanager
def _locked_ledger() -> Iterator[int]:
    directory = _admission_directory()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory_fd = os.open(directory, _DIRECTORY_FLAGS)
    lock_fd = -1
    try:
        lock_fd = os.open(
            _LOCK_NAME,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory_fd,
        )
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield directory_fd
    finally:
        if lock_fd >= 0:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)
        os.close(directory_fd)


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        if exc.errno == errno.EPERM:
            return True
        raise
    return True


def _read_reservation(directory_fd: int, name: str) -> tuple[int, int]:
    raw = _read_at(directory_fd, name)
    record = json.loads(raw)
    if not isinstance(record, dict) or set(record) != {"pid", "estimate_bytes", "acquired_at"}:
        raise ValueError("invalid reservation record shape")
    pid = record["pid"]
    estimate = record["estimate_bytes"]
    acquired_at = record["acquired_at"]
    if type(pid) is not int or pid <= 0:
        raise ValueError("invalid reservation pid")
    if type(estimate) is not int or estimate <= 0:
        raise ValueError("invalid reservation estimate")
    if type(acquired_at) not in {int, float} or not math.isfinite(acquired_at) or acquired_at < 0:
        raise ValueError("invalid reservation timestamp")
    return pid, estimate


def _collect_live_reservations(directory_fd: int) -> int:
    total = 0
    for name in os.listdir(directory_fd):
        if not name.endswith(_RECORD_SUFFIX):
            continue
        pid, estimate = _read_reservation(directory_fd, name)
        if _pid_is_alive(pid):
            total += estimate
        else:
            os.unlink(name, dir_fd=directory_fd)
    return total


def _create_reservation(directory_fd: int, estimate_bytes: int) -> str:
    token = secrets.token_hex(16)
    final_name = f"{os.getpid()}-{token}{_RECORD_SUFFIX}"
    temporary_name = f".{final_name}.tmp"
    record = {
        "pid": os.getpid(),
        "estimate_bytes": estimate_bytes,
        "acquired_at": time.time(),
    }
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    fd = -1
    replaced = False
    try:
        fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory_fd,
        )
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(errno.EIO, "short reservation write")
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
        replaced = True
        os.fsync(directory_fd)
        return final_name
    except Exception:
        if replaced:
            try:
                os.unlink(final_name, dir_fd=directory_fd)
            except OSError:
                pass
        raise
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass


def _decision_locked(
    directory_fd: int,
    estimate_bytes: int,
    *,
    acquire: bool,
) -> tuple[tuple[Admission, str], str | None]:
    observed = login_headroom()
    if observed is None:
        return (
            Admission.DISPATCH,
            "ログインノードのメモリ余裕を安全に観測できないため、計算ノードへ dispatch します。",
        ), None

    reserved = _collect_live_reservations(directory_fd)
    required = observed.memory_current_bytes + reserved + estimate_bytes + RESERVE_BYTES
    if required > observed.effective_ceiling_bytes:
        return (
            Admission.DISPATCH,
            "ログインノードのメモリ余裕が不足するため、計算ノードへ dispatch します。",
        ), None
    if not acquire:
        return (
            Admission.LOCAL,
            "ログインノードのメモリ余裕と予約枠を確認できたため、local 実行できます。",
        ), None

    reservation_name = _create_reservation(directory_fd, estimate_bytes)
    return (
        Admission.LOCAL,
        "ログインノードのメモリ余裕を予約したため、local 実行できます。",
    ), reservation_name


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


def grant_budget(
    *,
    max_bytes: int = MAX_LOCAL_BUDGET_BYTES,
    min_bytes: int = MIN_LOCAL_BUDGET_BYTES,
) -> tuple[Admission, int | None, str]:
    """``(判定, 与える予算 bytes, 日本語の理由)`` を返す。

    ``MAX_LOCAL_BUDGET_BYTES`` は 1 コマンドへ渡す暫定上限であり、実測を
    蓄積して再評価する。予算の確定と予約 record の作成は同じ台帳 lock の
    中で行い、別プロセスがその間へ割り込めないようにする。
    """

    if _invalid_budget_limits(max_bytes, min_bytes):
        return (
            Admission.DISPATCH,
            None,
            "予算の上限または下限が安全な整数でないため、計算ノードへ dispatch します。",
        )

    try:
        with _locked_ledger() as directory_fd:
            observed = login_headroom()
            if observed is None:
                return (
                    Admission.DISPATCH,
                    None,
                    "ログインノードの観測余裕=不明 bytes のため、"
                    "計算ノードへ dispatch します。",
                )

            reserved = _collect_live_reservations(directory_fd)
            available = (
                observed.effective_ceiling_bytes
                - observed.memory_current_bytes
                - reserved
                - RESERVE_BYTES
            )
            budget = min(max_bytes, available)
            detail = (
                f"予約控除後の観測余裕={available} bytes、算出予算={budget} bytes、現在使用量="
                f"{observed.memory_current_bytes} bytes、実効天井="
                f"{observed.effective_ceiling_bytes} bytes、"
                f"生存中の予約={reserved} bytes"
            )
            if budget <= 0 or budget < min_bytes:
                return (
                    Admission.DISPATCH,
                    None,
                    f"ログインノードの観測余裕が不足しています（{detail}）。",
                )

            _create_reservation(directory_fd, budget)
            return (
                Admission.LOCAL,
                budget,
                f"ログインノードで {budget} bytes の予算を予約しました（{detail}）。",
            )
    except Exception:
        return (
            Admission.DISPATCH,
            None,
            "予約台帳を安全に更新できないため、計算ノードへ dispatch します。",
        )


def admit(estimate_bytes: int) -> tuple[Admission, str]:
    """``(判定, 日本語の理由)`` を返す。実行時の予約には :func:`reserve` を使う。"""

    if _invalid_estimate(estimate_bytes):
        return (
            Admission.DISPATCH,
            "メモリ推定量が正の整数でないため、計算ノードへ dispatch します。",
        )
    try:
        with _locked_ledger() as directory_fd:
            decision, _ = _decision_locked(directory_fd, estimate_bytes, acquire=False)
            return decision
    except Exception:
        return (
            Admission.DISPATCH,
            "予約台帳を安全に確認できないため、計算ノードへ dispatch します。",
        )


@contextlib.contextmanager
def reserve(estimate_bytes: int) -> Iterator[tuple[Admission, str]]:
    """同一 lock 内で判定・予約し、context 終了時に予約を解放する。

    例外や SIGINT のように Python stack を unwind する signal でも ``finally`` で
    解放する。強制終了で unwind できない場合は、次回判定時の dead-pid 回収が
    残留 record を取り除く。
    """

    reservation_name: str | None = None
    if _invalid_estimate(estimate_bytes):
        yield (
            Admission.DISPATCH,
            "メモリ推定量が正の整数でないため、計算ノードへ dispatch します。",
        )
        return
    try:
        with _locked_ledger() as directory_fd:
            decision, reservation_name = _decision_locked(
                directory_fd,
                estimate_bytes,
                acquire=True,
            )
    except Exception:
        decision = (
            Admission.DISPATCH,
            "予約台帳を安全に更新できないため、計算ノードへ dispatch します。",
        )

    try:
        yield decision
    finally:
        if reservation_name is not None:
            try:
                with _locked_ledger() as directory_fd:
                    os.unlink(reservation_name, dir_fd=directory_fd)
                    os.fsync(directory_fd)
            except Exception:
                # 残留予約は次回 admission で生存 pid として数えられ、安全側に倒れる。
                pass


__all__ = [
    "ADMISSION_BASE_DIR_ENV",
    "ADMISSION_DIRNAME",
    "Admission",
    "CEILING_BYTES",
    "LoginHeadroom",
    "MAX_LOCAL_BUDGET_BYTES",
    "MIN_LOCAL_BUDGET_BYTES",
    "RESERVE_BYTES",
    "admit",
    "grant_budget",
    "login_headroom",
    "reserve",
]
