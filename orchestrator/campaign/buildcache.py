# -*- coding: utf-8 -*-
"""genome → バイナリ。内容キーのビルドキャッシュ (orchestrator-design.md D の思想)。

同じ最適化組合せ (genome) を再ビルドしない。キャッシュキー = (protocol, genome 正準,
ccbench-commit, trace 有無)。**trace と perf は別ビルド** (絶対規律1): verify は
trace-enabled (`-DCCBENCH_TRACE=1`)、bench は trace-disabled (`=0`)。

ビルドキャッシュは campaign 非依存 (同じ genome は全 campaign で共有) なので、
ccbench submodule 下の固定キャッシュ root に置く。compiler wrapper 経由の ccache は利用できるが、
wrapper の実体だけを束縛すると背後の実 compiler 差替えを見逃し得る既知限界がある。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import stat
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from . import site_policy, source_digest
from .build_admission import (
    BuildAdmission,
    BuildRunContext,
    require_build_admission,
    validate_build_admission_receipt,
)
from .env_contract import ExecutionEnvironmentContract
from .model import Genome
from .source_digest import SourceEvidence

# バイナリ digest の二系列契約 (敵対相談 A-6 裁定):
#   - 16 文字系列 = `sha256-prefix-16 / legacy-display-only`。WAL の `trace_bin`/`perf_bin`、
#     calibration の `binary_hash`、`BuildResult.bin_hash` が該当。provenance 表示専用で、
#     identity 照合には使わない。full 値の接頭辞であって identity ではない。
#   - 64 文字系列 = `exact 64 lowercase hex`。`BuildResult.bin_sha256`、WAL の
#     `*_bin_sha256`、`full_sha256()`/`assert_binary_sha256()` が該当。照合はこの系列だけで
#     行い、prefix 照合・prefix fallback・現在 disk からの遡及 backfill は禁止する。
_SHA256_HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
_V2_SCHEMA = "buildcache/v2"
_V2_COMPLETION_MANIFEST = "completion.json"
_LEGACY_ADMISSION_SCHEMA = "buildcache-legacy-admission/v1"
_LEGACY_ADMISSION_SIDECAR = "admission.json"
_FETCHCONTENT_RECEIPT_KEYS = frozenset({
    "masstree_head", "config_sha256", "archive_sha256",
})

_SECURE_FLAG_NAMES = (
    "O_CLOEXEC", "O_DIRECTORY", "O_EXCL", "O_NOFOLLOW", "O_NONBLOCK",
)
_SECURE_DIR_FD_FUNCTIONS = ("open", "stat", "mkdir", "rename", "unlink", "rmdir")
_ORIGINAL_SECURE_DIR_FD_CALLABLES = {
    name: getattr(os, name, None) for name in _SECURE_DIR_FD_FUNCTIONS
}
_ORIGINAL_OS_STAT = os.stat
_PROC_SELF_FD_ROOT = "/proc/self/fd"


def _close_fds_best_effort(fds) -> None:
    """全 fd の close を一度ずつ試み、最初の例外だけを再送出する。"""
    first_error: Optional[Exception] = None
    for fd in fds:
        if fd < 0:
            continue
        try:
            os.close(fd)
        except Exception as exc:
            if first_error is None:
                first_error = exc
    if first_error is not None:
        raise first_error


def _probe_proc_self_fd() -> bool:
    """Return whether a held regular-file fd can be reopened through procfs."""
    source_fd = reopened_fd = -1
    try:
        probe_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        source_fd = os.open(__file__, probe_flags)
        reopened_fd = os.open(
            f"{_PROC_SELF_FD_ROOT}/{source_fd}", probe_flags,
        )
        source_info = os.fstat(source_fd)
        reopened_info = os.fstat(reopened_fd)
        return (
            source_info.st_dev, source_info.st_ino, stat.S_IFMT(source_info.st_mode),
        ) == (
            reopened_info.st_dev, reopened_info.st_ino,
            stat.S_IFMT(reopened_info.st_mode),
        )
    except OSError:
        return False
    finally:
        _close_fds_best_effort([reopened_fd, source_fd])


_PROC_SELF_FD_AVAILABLE = _probe_proc_self_fd()


class BuildError(RuntimeError):
    """v2 build/toolchain の取得・実行が完遂できなかった。"""


class BuildCacheError(RuntimeError):
    """build cache の namespace・claim・完成 entry・metadata が信用できない。"""


class MasstreeFetchContentError(BuildError):
    """floor 用 masstree prebuild の閉じた実行段を保持する。"""

    def __init__(self, stage: str, message: str):
        if stage not in {"configure", "target"}:
            raise ValueError("未知の masstree FetchContent prebuild stage")
        super().__init__(message)
        self.stage = stage


class BinaryDigestError(RuntimeError):
    """バイナリ digest の計算不能・期待値不正など (path/cause を保持, 規律3)。"""

    def __init__(self, path, *, cause=None, message: str = ""):
        self.path = str(path)
        self.cause = cause
        super().__init__(message or f"binary digest error: {self.path}")


class BinaryDigestMismatch(BinaryDigestError):
    """記録済み 64 文字 sha256 と実測が食い違った (path/expected/actual を保持)。"""

    def __init__(self, path, expected: str, actual: str, *, cause=None):
        self.expected = expected
        self.actual = actual
        super().__init__(
            path, cause=cause,
            message=(f"binary sha256 不一致: {path} "
                     f"(expected={expected} actual={actual})"))


def _require_secure_fs_contract() -> None:
    """copy-out が必要とする POSIX/Linux platform capability を検査する。

    これは platform capability の検査であり、in-process の関数差し替えに対する
    防壁ではない。import 時に保存した original callable を capability set と照合し、
    観測用 wrapper の現在 identity を platform 欠如と誤認しない。
    """
    if os.name != "posix":
        raise BuildCacheError("secure build-cache copy-out は POSIX 環境を必要とする")
    missing = [name for name in _SECURE_FLAG_NAMES if not hasattr(os, name)]
    if missing:
        raise BuildCacheError(
            "secure build-cache copy-out に必要な os constant がない: "
            + ", ".join(missing)
        )
    if not hasattr(os, "supports_dir_fd") or not hasattr(os, "supports_follow_symlinks"):
        raise BuildCacheError("secure build-cache copy-out の os capability set が存在しない")
    unsupported = [
        name for name in _SECURE_DIR_FD_FUNCTIONS
        if _ORIGINAL_SECURE_DIR_FD_CALLABLES[name] not in os.supports_dir_fd
    ]
    if unsupported:
        raise BuildCacheError(
            "secure build-cache copy-out に必要な dir_fd API がない: "
            + ", ".join(unsupported)
        )
    if _ORIGINAL_OS_STAT not in os.supports_follow_symlinks:
        raise BuildCacheError(
            "secure build-cache copy-out は stat(..., follow_symlinks=False) を必要とする"
        )
    if not _PROC_SELF_FD_AVAILABLE:
        raise BuildCacheError(
            "secure build-cache copy-out は /proc/self/fd 経由の held-fd reopen を必要とする"
        )


def _secure_dir_flags() -> int:
    _require_secure_fs_contract()
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _secure_read_flags() -> int:
    _require_secure_fs_contract()
    return os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC


def _stat_identity(info: os.stat_result) -> tuple[int, int, int]:
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def _stable_file_identity(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
        info.st_ctime_ns, info.st_nlink,
    )


def _validated_relpath(relpath: str) -> tuple[str, ...]:
    if type(relpath) is not str or not relpath or "\x00" in relpath:
        raise BuildCacheError("cache member path は NUL のない非空 str でなければならない")
    if os.path.isabs(relpath):
        raise BuildCacheError(f"cache member path は relative でなければならない: {relpath!r}")
    parts = tuple(relpath.split(os.sep))
    if any(not part or part in {".", ".."} for part in parts):
        raise BuildCacheError(f"cache member path component が不正: {relpath!r}")
    separators = tuple(dict.fromkeys(item for item in (os.sep, os.altsep, "\\") if item))
    if any(any(separator in part for separator in separators) for part in parts):
        raise BuildCacheError(f"cache member path component に separator が混入: {relpath!r}")
    return parts


def _open_checked_directory_at(parent_fd: int, name: str, *, label: str) -> int:
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        child_fd = os.open(name, _secure_dir_flags(), dir_fd=parent_fd)
    except OSError as exc:
        raise BuildCacheError(f"{label} directory を no-follow open できない: {name}: {exc}") from exc
    try:
        after = os.fstat(child_fd)
        if (not stat.S_ISDIR(before.st_mode) or not stat.S_ISDIR(after.st_mode)
                or _stat_identity(before) != _stat_identity(after)):
            raise BuildCacheError(f"{label} directory identity が open 中に変化した: {name}")
        return child_fd
    except Exception:
        os.close(child_fd)
        raise


def _open_or_create_directory_path(path: str) -> int:
    """absolute directory path を `/` の held fd から no-follow で作成・走査する。"""
    _require_secure_fs_contract()
    absolute = os.path.abspath(path)
    parts = tuple(part for part in absolute.split(os.sep) if part)
    current_fd = os.open(os.sep, _secure_dir_flags())
    try:
        for part in parts:
            try:
                os.mkdir(part, 0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            except OSError as exc:
                raise BuildCacheError(
                    f"cache parent component を mkdir できない: {absolute}: {part}: {exc}"
                ) from exc
            child_fd = _open_checked_directory_at(
                current_fd, part, label="cache parent component",
            )
            # child の所有権を先に current_fd へ移す。親 close が失敗しても、
            # outer cleanup が直前に開いた child を失わない。
            parent_fd = current_fd
            current_fd = child_fd
            os.close(parent_fd)
        return current_fd
    except Exception:
        try:
            _close_fds_best_effort([current_fd])
        except Exception:
            # traversal/close の最初の例外を保持する。child close は試行済み。
            pass
        raise


def _open_directory_path_nofollow(path: str, *, label: str) -> int:
    try:
        fd = os.open(path, _secure_dir_flags())
    except OSError as exc:
        raise BuildCacheError(f"{label} を final-component no-follow open できない: {path}: {exc}") from exc
    try:
        info = os.fstat(fd)
    except Exception:
        os.close(fd)
        raise
    if not stat.S_ISDIR(info.st_mode):
        os.close(fd)
        raise BuildCacheError(f"{label} が directory でない: {path}")
    return fd


def _open_relative_parent(root_fd: int, parts: tuple[str, ...], *, label: str) -> tuple[int, list[int]]:
    current_fd = os.dup(root_fd)
    opened = [current_fd]
    try:
        for part in parts[:-1]:
            child_fd = _open_checked_directory_at(current_fd, part, label=label)
            opened.append(child_fd)
            current_fd = child_fd
        return current_fd, opened
    except Exception:
        _close_fds_best_effort(reversed(opened))
        raise


def _create_relative_parent(root_fd: int, parts: tuple[str, ...], *, label: str) -> tuple[int, list[int]]:
    current_fd = os.dup(root_fd)
    opened = [current_fd]
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, 0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            except OSError as exc:
                raise BuildCacheError(f"{label} directory を mkdir できない: {part}: {exc}") from exc
            child_fd = _open_checked_directory_at(current_fd, part, label=label)
            opened.append(child_fd)
            os.fchmod(child_fd, 0o700)
            current_fd = child_fd
        return current_fd, opened
    except Exception:
        _close_fds_best_effort(reversed(opened))
        raise


def _validate_regular_file(info: os.stat_result, *, label: str) -> None:
    if not stat.S_ISREG(info.st_mode):
        raise BuildCacheError(f"{label} は通常ファイルでなければならない")
    if info.st_nlink != 1:
        raise BuildCacheError(f"{label} は hard link であってはならない (nlink={info.st_nlink})")
    if info.st_mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX):
        raise BuildCacheError(f"{label} に setuid/setgid/sticky bit がある")


def _open_regular_at(root_fd: int, relpath: str, *, label: str) -> tuple[int, os.stat_result]:
    parts = _validated_relpath(relpath)
    parent_fd, opened = _open_relative_parent(root_fd, parts, label=label)
    fd = -1
    try:
        before = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        fd = os.open(parts[-1], _secure_read_flags(), dir_fd=parent_fd)
        after = os.fstat(fd)
        _validate_regular_file(before, label=label)
        _validate_regular_file(after, label=label)
        if _stat_identity(before) != _stat_identity(after):
            raise BuildCacheError(f"{label} identity が open 中に変化した")
    except OSError as exc:
        try:
            _close_fds_best_effort([fd, *reversed(opened)])
        except Exception:
            pass
        raise BuildCacheError(f"{label} を no-follow open できない: {relpath}: {exc}") from exc
    except Exception:
        try:
            _close_fds_best_effort([fd, *reversed(opened)])
        except Exception:
            pass
        raise
    # Parent cleanup が完了するまでは leaf を caller 所有へ移さない。
    try:
        _close_fds_best_effort(reversed(opened))
    except Exception:
        try:
            _close_fds_best_effort([fd])
        except Exception:
            pass
        raise
    return fd, after


def _open_source_regular_at(
        root_fd: int, relpath: str, *, label: str,
) -> tuple[int, os.stat_result]:
    """source leaf は O_NOFOLLOW open 後の fstat だけを判定基準にする (M1 anchor)。"""
    parts = _validated_relpath(relpath)
    parent_fd, opened = _open_relative_parent(root_fd, parts, label=label)
    fd = -1
    try:
        fd = os.open(parts[-1], _secure_read_flags(), dir_fd=parent_fd)
        info = os.fstat(fd)
        _validate_regular_file(info, label=label)
    except OSError as exc:
        try:
            _close_fds_best_effort([fd, *reversed(opened)])
        except Exception:
            pass
        raise BuildCacheError(f"{label} を no-follow open できない: {relpath}: {exc}") from exc
    except Exception:
        try:
            _close_fds_best_effort([fd, *reversed(opened)])
        except Exception:
            pass
        raise
    # Parent cleanup が完了するまでは leaf を caller 所有へ移さない。
    try:
        _close_fds_best_effort(reversed(opened))
    except Exception:
        try:
            _close_fds_best_effort([fd])
        except Exception:
            pass
        raise
    return fd, info


def _relative_entry_lexists(root_fd: int, relpath: str, *, label: str) -> bool:
    parts = _validated_relpath(relpath)
    try:
        parent_fd, opened = _open_relative_parent(root_fd, parts, label=label)
    except BuildCacheError as exc:
        if isinstance(exc.__cause__, FileNotFoundError):
            return False
        raise
    try:
        try:
            os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise BuildCacheError(f"{label} を no-follow stat できない: {relpath}: {exc}") from exc
    finally:
        _close_fds_best_effort(reversed(opened))


def _read_stable_fd(fd: int, *, label: str) -> bytes:
    before = os.fstat(fd)
    _validate_regular_file(before, label=label)
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    while True:
        chunk = os.read(fd, 1 << 20)
        if not chunk:
            break
        chunks.append(chunk)
    after = os.fstat(fd)
    if _stable_file_identity(before) != _stable_file_identity(after):
        raise BuildCacheError(f"{label} が read 中に変化した")
    return b"".join(chunks)


def _full_sha256_fd(fd: int, display_path: str) -> str:
    before = os.fstat(fd)
    _validate_regular_file(before, label=f"binary {display_path}")
    try:
        digest = full_sha256(f"/proc/self/fd/{fd}")
    except BinaryDigestError as exc:
        raise BuildCacheError(f"held fd の binary sha256 を取得できない: {display_path}: {exc}") from exc
    after = os.fstat(fd)
    if _stable_file_identity(before) != _stable_file_identity(after):
        raise BuildCacheError(f"binary が sha256 中に変化した: {display_path}")
    return digest


@dataclass
class _CopiedBinary:
    source_fd: int
    destination_fd: int
    destination_parent_fd: int
    destination_name: str
    directory_fds: list[int]
    destination_path: str

    def verify_destination_entry(self) -> None:
        entry = os.stat(
            self.destination_name, dir_fd=self.destination_parent_fd,
            follow_symlinks=False,
        )
        held = os.fstat(self.destination_fd)
        _validate_regular_file(entry, label=f"published binary {self.destination_path}")
        if (_stat_identity(entry) != _stat_identity(held)
                or _stable_file_identity(entry) != _stable_file_identity(held)):
            raise BuildCacheError(
                f"clean destination entry が held binary fd と不一致: {self.destination_path}"
            )

    def fsync_directories(self) -> None:
        for fd in reversed(self.directory_fds):
            os.fsync(fd)

    def _owned_fds(self) -> list[int]:
        return [
            self.source_fd,
            self.destination_fd,
            *reversed(self.directory_fds),
        ]

    def close(self) -> None:
        _close_fds_best_effort(self._owned_fds())


def _secure_copy_binary(
        staging_fd: int, clean_fd: int, relpath: str, clean_path: str,
) -> _CopiedBinary:
    """held staging fd から allowlisted binary 1 本だけを clean root へ copy する。

    CMake subprocess 自体には pathname を渡すため staging 全体の anchor は主張しない。
    held fd は copy-out destination の inode binding に使う source 選択だけを固定する。
    """
    _require_secure_fs_contract()
    parts = _validated_relpath(relpath)
    source_fd = -1
    destination_fd = -1
    destination_dirs: list[int] = []
    try:
        source_fd, source_before = _open_source_regular_at(
            staging_fd, relpath, label=f"staging binary {relpath}",
        )
        destination_parent_fd, destination_dirs = _create_relative_parent(
            clean_fd, parts, label="clean binary parent",
        )
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            destination_fd = os.open(
                parts[-1], flags, 0o600, dir_fd=destination_parent_fd,
            )
        except OSError as exc:
            raise BuildCacheError(f"clean destination を create-only open できない: {relpath}: {exc}") from exc
        destination_created = os.fstat(destination_fd)
        _validate_regular_file(destination_created, label=f"clean destination {relpath}")
        os.lseek(source_fd, 0, os.SEEK_SET)
        while True:
            chunk = os.read(source_fd, 1 << 20)
            if not chunk:
                break
            view = memoryview(chunk)
            while view:
                written = os.write(destination_fd, view)
                if written <= 0:
                    raise BuildCacheError(f"clean destination への copy が進まない: {relpath}")
                view = view[written:]
        os.fchmod(destination_fd, 0o500)
        source_after = os.fstat(source_fd)
        if _stable_file_identity(source_before) != _stable_file_identity(source_after):
            raise BuildCacheError(f"staging binary が copy 中に変化した: {relpath}")
        result = _CopiedBinary(
            source_fd=source_fd,
            destination_fd=destination_fd,
            destination_parent_fd=destination_parent_fd,
            destination_name=parts[-1],
            directory_fds=destination_dirs,
            destination_path=os.path.join(clean_path, relpath),
        )
        result.verify_destination_entry()
        source_fd = destination_fd = -1
        destination_dirs = []
        return result
    except OSError as exc:
        raise BuildCacheError(f"secure binary copy に失敗: {relpath}: {exc}") from exc
    finally:
        _close_fds_best_effort([
            source_fd, destination_fd, *reversed(destination_dirs),
        ])


def is_full_sha256(value) -> bool:
    """`value` が exact 64 lowercase hex (照合系列の正規形) かを判定する。

    prefix 照合・大文字許容・fallback はしない (A-6)。"""
    return isinstance(value, str) and bool(_SHA256_HEX64.match(value))


def full_sha256(path) -> str:
    """バイナリ内容の **full** sha256 hexdigest (64 文字, truncate しない)。

    1MB チャンク読み。読取不能は握りつぶさず `BinaryDigestError` (cause 保持) に倒す
    (規律3)。返り値は exact 64 lowercase hex 系列 (上記契約)。"""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    except OSError as exc:
        raise BinaryDigestError(
            path, cause=exc,
            message=f"バイナリ sha256 を計算できない: {path}: {exc}") from exc
    return h.hexdigest()


def assert_binary_sha256(path, expected: str) -> None:
    """`path` の full sha256 が `expected` (exact 64 lowercase hex) と一致することを assert。

    成功時のみ復帰する (bool を返さない, A-5)。`expected` が 64 桁 lowercase hex 以外
    (15/16/63/65 桁・非 hex・大文字を含む) は即 `BinaryDigestError` で拒否し、prefix 照合・
    prefix fallback は一切しない (A-6, fail-closed)。不一致は `BinaryDigestMismatch`。"""
    if not is_full_sha256(expected):
        raise BinaryDigestError(
            path,
            message=(f"expected が exact 64 lowercase hex でない: {expected!r} "
                     "(prefix 照合・fallback はしない, A-6)"))
    actual = full_sha256(path)
    if actual != expected:
        raise BinaryDigestMismatch(path, expected, actual)


def _ccbench_dir() -> str:
    # buildcache.py = <repo>/orchestrator/campaign/buildcache.py → repo は dirname×2
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    repo = os.path.dirname(os.path.dirname(here))         # <repo>
    return os.path.join(repo, "external", "ccbench")


DEFAULT_CC, DEFAULT_CXX = "gcc-13", "g++-13"


def cache_key(genome: Genome, ccbench_commit: str, trace: bool,
              src_token: str = source_digest.STOCK,
              cc: str = DEFAULT_CC, cxx: str = DEFAULT_CXX, *,
              admission: BuildAdmission) -> str:
    """内容キー。Phase 3 で coder がコードを書き換えるので src_token (preprocess 後
    ハッシュ, D23) を pre-image に織り込み、同 genome 別ソースの偽 hit を防ぐ。
    stock (working-tree==HEAD) は src を省き旧キーを温存 (後方互換)。
    ツールチェーン (cc/cxx) も pre-image に織り込む — コンパイラを替えて再計測すると
    既評価 genome だけ旧コンパイラのバイナリで偽 hit し、同一 campaign 内で baseline と
    variant のビルド条件が食い違う (コンパイラ差はバックオフ級の差を容易に上回る)。
    既定ツールチェーンは省いて旧キーを温存 (src_token と同型の後方互換規則)。"""
    if type(admission) is not BuildAdmission:
        raise TypeError("admission は derive_build_admission() 由来の exact value が必要")
    src = "" if src_token == source_digest.STOCK else f"|src={src_token}"
    tc = "" if (cc, cxx) == (DEFAULT_CC, DEFAULT_CXX) else f"|cc={cc}|cxx={cxx}"
    raw = (f"{genome.canonical()}|{ccbench_commit}|trace={int(trace)}{src}{tc}"
           f"|adm={admission.receipt_sha256}")
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"{genome.protocol}_{h}_t{int(trace)}"


def _validate_request_evidence(
        genome: Genome, ccbench_commit: str, sub: str,
        source_evidence: SourceEvidence,
) -> None:
    genome_sha256 = hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()
    if source_evidence.genome_sha256 != genome_sha256:
        raise BuildCacheError("SourceEvidence genome digest が build request と不一致")
    if source_evidence.ccbench_commit != ccbench_commit:
        raise BuildCacheError("SourceEvidence ccbench commit が build request と不一致")
    expected_root = os.path.realpath(os.path.abspath(sub))
    if source_evidence.source_root != expected_root:
        raise BuildCacheError("SourceEvidence source root が build request と不一致")


@dataclass(frozen=True)
class BuildResult:
    genome: Genome
    trace: bool
    binary: str             # ycsb_<protocol>.exe の絶対パス
    bin_sha256: str         # バイナリ内容の full sha256 (exact 64 lowercase hex, 単一ソース)
    build_dir: str
    cached: bool            # キャッシュヒットで再ビルドを省いたか
    configure_cmd: str = ""  # このバイナリを作る cmake configure (実験再現用)
    build_cmd: str = ""      # cmake --build (実験再現用)
    # campaign artifact が shell 文字列を再解析せず portable 表示を作るための additive API。
    # 既存 configure_cmd/build_cmd は互換維持し、実行・cache 挙動には使わない。
    configure_argv: tuple[str, ...] = ()
    build_argv: tuple[str, ...] = ()
    cache_root: str = ""
    ccbench_root: str = ""
    # v2 build namespace の provenance。legacy build() は additive default None を保つ。
    contract_sha256: Optional[str] = None
    # floor sort_best 専用の runtime 診断。空の既定 caller は従来どおり。
    fetchcontent_base_dir: str = ""
    masstree_source_root_sha256: str = ""

    @property
    def bin_hash(self) -> str:
        """provenance / WAL 用の 16 文字表示 (= `bin_sha256[:16]`)。

        `bin_sha256` の read-only 派生であり、独立フィールドとして格納しない (A-3/D-7:
        「二つの真実」排除)。sha256-prefix-16 / legacy-display-only 系列 — 照合には使わない。"""
        return self.bin_sha256[:16]


@dataclass(frozen=True)
class MasstreeFetchContentPreparation:
    fetchcontent_base_dir: str
    build_dir: str
    configure_argv: tuple[str, ...]
    build_argv: tuple[str, ...]


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


def _validate_fetchcontent_dependency_receipt(
        receipt: Optional[Mapping[str, object]],
) -> Optional[Dict[str, str]]:
    if receipt is None:
        return None
    if not isinstance(receipt, Mapping) or set(receipt) != _FETCHCONTENT_RECEIPT_KEYS:
        raise BuildCacheError("FetchContent dependency receipt の exact key 集合が不正")
    normalized = {key: receipt[key] for key in sorted(_FETCHCONTENT_RECEIPT_KEYS)}
    if (type(normalized["masstree_head"]) is not str
            or re.fullmatch(r"[0-9a-f]{40}", normalized["masstree_head"]) is None):
        raise BuildCacheError("FetchContent dependency receipt の masstree HEAD が不正")
    for key in ("config_sha256", "archive_sha256"):
        if not is_full_sha256(normalized[key]):
            raise BuildCacheError(f"FetchContent dependency receipt の {key} が不正")
    return normalized


def _canonical_fetchcontent_base(value: object) -> str:
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise BuildCacheError("FETCHCONTENT_BASE_DIR が path-like でない") from exc
    if type(raw) is not str or not raw or "\0" in raw or not os.path.isabs(raw):
        raise BuildCacheError("FETCHCONTENT_BASE_DIR は NUL なし絶対 path 必須")
    if os.path.islink(raw) or not os.path.isdir(raw):
        raise BuildCacheError("FETCHCONTENT_BASE_DIR は non-symlink directory 必須")
    canonical = os.path.realpath(raw)
    if canonical != os.path.abspath(raw):
        raise BuildCacheError("FETCHCONTENT_BASE_DIR は canonical path 必須")
    return canonical


def _fetchcontent_git_environment() -> Dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _sha256_fetchcontent_file(path: str, *, label: str) -> str:
    try:
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise BuildCacheError(
                f"FetchContent dependency {label} が non-symlink regular file でない"
            )
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BuildCacheError(
            f"FetchContent dependency {label} を再照合できない"
        ) from exc
    return digest.hexdigest()


def _observe_fetchcontent_dependency_receipt(
        fetchcontent_base_dir: str,
) -> Dict[str, str]:
    """completion publish 前に現在の masstree 内容 receipt を再取得する。"""
    source_root = os.path.join(fetchcontent_base_dir, "masstree-src")
    try:
        info = os.lstat(source_root)
        canonical_source = os.path.realpath(source_root)
    except OSError as exc:
        raise BuildCacheError(
            "FetchContent dependency source root を再照合できない"
        ) from exc
    if (stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)
            or canonical_source != os.path.abspath(source_root)):
        raise BuildCacheError(
            "FetchContent dependency source root が canonical directory でない"
        )
    try:
        completed = subprocess.run(
            [
                "git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
                "-c", "core.useReplaceRefs=false", "-C", canonical_source,
                "rev-parse", "--show-toplevel", "--verify", "HEAD",
            ],
            env=_fetchcontent_git_environment(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildCacheError(
            "FetchContent dependency HEAD を再照合できない"
        ) from exc
    lines = completed.stdout.splitlines()
    if (completed.returncode != 0 or len(lines) != 2
            or os.path.realpath(lines[0]) != canonical_source
            or re.fullmatch(r"[0-9a-f]{40}", lines[1]) is None):
        raise BuildCacheError(
            "FetchContent dependency HEAD を一意に再取得できない"
        )
    return {
        "masstree_head": lines[1],
        "config_sha256": _sha256_fetchcontent_file(
            os.path.join(canonical_source, "config.h"), label="config.h",
        ),
        "archive_sha256": _sha256_fetchcontent_file(
            os.path.join(canonical_source, "libkohler_masstree_json.a"),
            label="libkohler_masstree_json.a",
        ),
    }


def _masstree_source_root_from_cmake_cache(build_dir: str) -> str:
    """build 自身の CMakeCache から実効 masstree source root を一意に読む。"""
    cache = os.path.join(build_dir, "CMakeCache.txt")
    try:
        info = os.lstat(cache)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise BuildCacheError("CMakeCache.txt が non-symlink regular file でない")
        with open(cache, encoding="utf-8", errors="strict") as handle:
            matches = []
            for line in handle:
                match = re.fullmatch(r"masstree_SOURCE_DIR(?::[^=\r\n]*)?=([^\r\n]+)\r?\n?", line)
                if match is not None:
                    matches.append(match.group(1))
    except (OSError, UnicodeError) as exc:
        raise BuildCacheError(f"CMakeCache.txt から masstree source root を読めない: {cache}") from exc
    if len(matches) != 1 or not os.path.isabs(matches[0]) or "\0" in matches[0]:
        raise BuildCacheError("CMakeCache.txt の masstree_SOURCE_DIR が一意な絶対 path でない")
    return os.path.realpath(matches[0])


def _tool_version(requested: str, role: str) -> Dict[str, str]:
    """PATH 上の tool 実体と ``--version`` 先頭行を取得する (v2 identity)。"""
    try:
        found = shutil.which(requested)
    except (OSError, TypeError) as exc:
        raise BuildError(f"toolchain {role} の探索に失敗: {requested!r}: {exc}") from exc
    if not found:
        raise BuildError(
            f"toolchain {role} が PATH に存在しない: {requested!r} (fails-closed)"
        )
    realpath = os.path.realpath(found)
    if not os.path.isfile(realpath) or not os.access(realpath, os.X_OK):
        raise BuildError(
            f"toolchain {role} の実体が実行可能な通常ファイルでない: {realpath!r}"
        )
    try:
        result = subprocess.run(
            [realpath, "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildError(
            f"toolchain {role} --version を実行できない: {realpath}: {exc}"
        ) from exc
    lines = result.stdout.splitlines()
    if result.returncode != 0 or not lines or not lines[0].strip():
        detail = result.stderr[-300:] if result.stderr else "stdout 先頭行なし"
        raise BuildError(
            f"toolchain {role} --version の取得に失敗 "
            f"(rc={result.returncode}): {realpath}: {detail}"
        )
    return {
        "requested": requested,
        "realpath": realpath,
        "version_first_line": lines[0],
    }


def _toolchain_manifest(cc: str, cxx: str) -> Dict[str, Dict[str, str]]:
    """compiler 2 本と cmake の構造化 manifest。1 項でも取れなければ停止。"""
    return {
        "cc": _tool_version(cc, "cc"),
        "cxx": _tool_version(cxx, "cxx"),
        "cmake": _tool_version("cmake", "cmake"),
    }


def _tool_version_full(realpath: str, role: str) -> str:
    """Caller binding 用に ``--version`` の stdout + stderr 全文を再観測する。"""
    try:
        result = subprocess.run(
            [realpath, "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildError(
            f"toolchain {role} --version 全文を再観測できない: {realpath}: {exc}"
        ) from exc
    lines = result.stdout.splitlines()
    version = (result.stdout + result.stderr).strip()
    if (result.returncode != 0 or not lines or not lines[0].strip()
            or not version):
        raise BuildError(
            f"toolchain {role} --version 全文の再観測に失敗 "
            f"(rc={result.returncode}): {realpath}"
        )
    return version


def _split_expected_toolchain_manifest(
        expected: Mapping[str, object],
) -> tuple[Dict[str, Dict[str, str]], Dict[str, str]]:
    """Caller の期待値を identity 投影と全文投影へ fail-closed に分ける。"""
    roles = ("cc", "cxx", "cmake")
    identity_keys = ("requested", "realpath", "version_first_line")
    expected_keys = {*identity_keys, "version"}
    if not isinstance(expected, Mapping) or set(expected) != set(roles):
        raise BuildCacheError("v2 expected toolchain manifest の role 集合が不正")
    identity: Dict[str, Dict[str, str]] = {}
    versions: Dict[str, str] = {}
    for role in roles:
        entry = expected[role]
        if not isinstance(entry, Mapping) or set(entry) != expected_keys:
            raise BuildCacheError(
                f"v2 expected toolchain manifest の {role} key 集合が不正"
            )
        values = {key: entry[key] for key in expected_keys}
        if any(type(value) is not str or not value for value in values.values()):
            raise BuildCacheError(
                f"v2 expected toolchain manifest の {role} 値が非空 str でない"
            )
        identity[role] = {key: values[key] for key in identity_keys}
        versions[role] = values["version"]
    return identity, versions


def _v2_identity(
        genome: Genome, ccbench_commit: str, trace: bool, src_token: str,
        cc: str, cxx: str, toolchain: Dict[str, Dict[str, str]],
        *, site: str, dependency_prefix: List[str],
        admission: Dict[str, Any],
        fetchcontent_dependency_receipt: Optional[Mapping[str, object]] = None,
) -> tuple[Dict[str, Any], str]:
    """完全 pre-image と full build digest (64hex) を返す。"""
    toolchain_sha256 = hashlib.sha256(_canonical_json_bytes(toolchain)).hexdigest()
    preimage: Dict[str, Any] = {
        "genome_canonical": genome.canonical(),
        "ccbench_commit": ccbench_commit,
        "trace": trace,
        "src_token": src_token,
        "cc": cc,
        "cxx": cxx,
        "toolchain_manifest_sha256": toolchain_sha256,
        "site": site,
        "dependency_prefix": dependency_prefix,
        "admission": admission,
    }
    receipt = _validate_fetchcontent_dependency_receipt(
        fetchcontent_dependency_receipt,
    )
    if receipt is not None:
        preimage["fetchcontent_dependency_receipt"] = receipt
    return preimage, hashlib.sha256(_canonical_json_bytes(preimage)).hexdigest()


def _fsync_dir(path: str) -> None:
    """directory entry の永続化を要求する。失敗は握りつぶさない。"""
    fd = os.open(path, _secure_dir_flags())
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_file(path: str) -> None:
    fd = os.open(path, _secure_read_flags())
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_fsynced_json(path: str, value: Any) -> None:
    payload = _canonical_json_bytes(value) + b"\n"
    with open(path, "xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _write_fsynced_json_at(directory_fd: int, name: str, value: Any) -> None:
    """host-generated metadata を held directory fd 内へ create-only で永続化する。"""
    if type(name) is not str or not name or name in {".", ".."} or os.sep in name:
        raise BuildCacheError(f"metadata leaf name が不正: {name!r}")
    payload = _canonical_json_bytes(value) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
    except OSError as exc:
        raise BuildCacheError(f"host-generated metadata を create-only open できない: {name}: {exc}") from exc
    try:
        info = os.fstat(fd)
        _validate_regular_file(info, label=f"metadata {name}")
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise BuildCacheError(f"metadata write が進まない: {name}")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _reject_duplicate_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key: {key}")
        value[key] = item
    return value


def _decode_json_object(raw: bytes, path: str, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise BuildCacheError(f"{label} を厳密に読めない: {path}: {exc}") from exc
    if type(value) is not dict:
        raise BuildCacheError(f"{label} の top-level が object でない: {path}")
    return value


def _read_json_member(root_fd: int, relpath: str, *, path: str, label: str) -> Dict[str, Any]:
    fd = -1
    try:
        fd, _ = _open_regular_at(root_fd, relpath, label=label)
        raw = _read_stable_fd(fd, label=label)
        return _decode_json_object(raw, path, label)
    finally:
        if fd >= 0:
            os.close(fd)


def _read_completion_manifest(path: str, *, directory_fd: Optional[int] = None) -> Dict[str, Any]:
    owned_fd = -1
    try:
        if directory_fd is None:
            owned_fd = _open_directory_path_nofollow(os.path.dirname(path), label="v2 cache entry")
            directory_fd = owned_fd
        return _read_json_member(
            directory_fd, os.path.basename(path), path=path,
            label="v2 completion manifest",
        )
    finally:
        if owned_fd >= 0:
            os.close(owned_fd)


def _read_legacy_admission_sidecar(
        path: str, *, directory_fd: Optional[int] = None,
) -> Dict[str, Any]:
    owned_fd = -1
    try:
        if directory_fd is None:
            owned_fd = _open_directory_path_nofollow(
                os.path.dirname(path), label="legacy cache entry",
            )
            directory_fd = owned_fd
        value = _read_json_member(
            directory_fd, os.path.basename(path), path=path,
            label="legacy admission sidecar",
        )
    finally:
        if owned_fd >= 0:
            os.close(owned_fd)
    if type(value) is not dict or set(value) != {"schema_version", "admission"}:
        actual = sorted(value) if type(value) is dict else type(value).__name__
        raise BuildCacheError(
            f"legacy admission sidecar field 集合が不一致: {path}: actual={actual}"
        )
    return value


def _validate_legacy_admission_sidecar(
        bdir: str, *, admission: BuildAdmission,
        build_context: BuildRunContext, source_evidence: SourceEvidence,
        directory_fd: Optional[int] = None,
) -> None:
    path = os.path.join(bdir, _LEGACY_ADMISSION_SIDECAR)
    sidecar = _read_legacy_admission_sidecar(path, directory_fd=directory_fd)
    if sidecar["schema_version"] != _LEGACY_ADMISSION_SCHEMA:
        raise BuildCacheError(f"legacy admission sidecar schema 不一致: {path}")
    try:
        checked = validate_build_admission_receipt(
            sidecar["admission"],
            expected_policy=build_context.policy,
            expected_source=source_evidence,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        raise BuildCacheError(
            f"legacy admission sidecar receipt 検証失敗: {path}: {exc}"
        ) from exc
    if (checked != admission.as_cache_identity()
            or checked.get("receipt_sha256") != admission.receipt_sha256):
        raise BuildCacheError(
            f"legacy admission sidecar/current admission 完全一致検査に失敗: {path}"
        )


def _validate_v2_entry(
        bdir: str, *, preimage: Dict[str, Any], digest: str,
        toolchain: Dict[str, Dict[str, str]], binary_relpath: str,
        contract_sha256: str, admission: Dict[str, Any],
        build_context: BuildRunContext, source_evidence: SourceEvidence,
        parent_fd: Optional[int] = None, bdir_name: Optional[str] = None,
) -> tuple[str, str, int, str]:
    """完成 entry の host metadata と binary を held fd beneath-only で検証する。

    cache contract は ``binary + host-generated metadata`` である。旧実装が発行した
    entry の extra member は互換性のため hit 時に拒否しない、という残余を意図的に保つ。
    """
    if parent_fd is None:
        bdir_fd = _open_directory_path_nofollow(bdir, label="v2 cache publish 先")
    else:
        bdir_fd = _open_checked_directory_at(
            parent_fd, bdir_name or os.path.basename(bdir), label="v2 cache publish 先",
        )
    binary_fd = result_fd = -1
    manifest_path = os.path.join(bdir, _V2_COMPLETION_MANIFEST)
    try:
        manifest = _read_completion_manifest(manifest_path, directory_fd=bdir_fd)
        expected_keys = {
            "schema_version", "completion_marker", "full_build_digest",
            "contract_sha256", "preimage", "toolchain", "binary", "admission",
        }
        dependency_receipt = preimage.get("fetchcontent_dependency_receipt")
        if dependency_receipt is not None:
            expected_keys.add("fetchcontent_dependency")
        if set(manifest) != expected_keys:
            raise BuildCacheError(
                f"v2 completion manifest field 集合が不一致: {manifest_path}: "
                f"actual={sorted(manifest)}"
            )
        if manifest["schema_version"] != _V2_SCHEMA:
            raise BuildCacheError(f"v2 completion manifest schema 不一致: {manifest_path}")
        if manifest["completion_marker"] != "complete":
            raise BuildCacheError(f"v2 completion marker 不一致: {manifest_path}")
        if manifest["full_build_digest"] != digest:
            raise BuildCacheError(f"v2 full build digest 不一致: {manifest_path}")
        if manifest["contract_sha256"] != contract_sha256:
            raise BuildCacheError(f"v2 contract namespace sha256 不一致: {manifest_path}")
        if manifest["preimage"] != preimage:
            raise BuildCacheError(f"v2 pre-image 完全一致検査に失敗: {manifest_path}")
        if (preimage.get("admission") != admission
                or manifest["admission"] != admission
                or manifest["admission"] != preimage.get("admission")):
            raise BuildCacheError(
                f"v2 admission の pre-image/manifest/current 完全一致検査に失敗: "
                f"{manifest_path}"
            )
        try:
            checked_admission = validate_build_admission_receipt(
                manifest["admission"],
                expected_policy=build_context.policy,
                expected_source=source_evidence,
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            raise BuildCacheError(
                f"v2 admission receipt canonicality/current evidence 検証失敗: "
                f"{manifest_path}: {exc}"
            ) from exc
        if checked_admission != admission:
            raise BuildCacheError(
                f"v2 admission receipt canonical projection 不一致: {manifest_path}"
            )
        if manifest["toolchain"] != toolchain:
            raise BuildCacheError(f"v2 toolchain manifest 完全一致検査に失敗: {manifest_path}")
        if hashlib.sha256(_canonical_json_bytes(toolchain)).hexdigest() != \
                preimage["toolchain_manifest_sha256"]:
            raise BuildCacheError(f"v2 toolchain manifest sha256 不一致: {manifest_path}")
        source_root_sha256 = ""
        if dependency_receipt is not None:
            dependency = manifest["fetchcontent_dependency"]
            if (type(dependency) is not dict
                    or set(dependency) != {"source_root_sha256", "source_subdir"}
                    or dependency.get("source_subdir") != "masstree-src"
                    or not is_full_sha256(dependency.get("source_root_sha256"))):
                raise BuildCacheError(
                    f"v2 FetchContent dependency manifest が不正: {manifest_path}"
                )
            source_root_sha256 = dependency["source_root_sha256"]
        binary_record = manifest["binary"]
        if type(binary_record) is not dict or set(binary_record) != {"relative_path", "sha256"}:
            raise BuildCacheError(f"v2 binary manifest の field 集合が不一致: {manifest_path}")
        if binary_record["relative_path"] != binary_relpath:
            raise BuildCacheError(f"v2 binary relative path 不一致: {manifest_path}")
        if not is_full_sha256(binary_record["sha256"]):
            raise BuildCacheError(f"v2 binary sha256 が正規形でない: {manifest_path}")
        binary = os.path.join(bdir, binary_relpath)
        binary_fd, _ = _open_regular_at(
            bdir_fd, binary_relpath, label=f"v2 cached binary {binary}",
        )
        actual = _full_sha256_fd(binary_fd, binary)
        if actual != binary_record["sha256"]:
            raise BuildCacheError(
                f"v2 cached binary sha256 照合失敗: {binary}: "
                f"expected={binary_record['sha256']} actual={actual}"
            )
        result_fd = binary_fd
        binary_fd = -1
        return binary, binary_record["sha256"], result_fd, source_root_sha256
    finally:
        try:
            _close_fds_best_effort([binary_fd, bdir_fd])
        except Exception:
            # return は破棄されるため、返却予定 leaf も finalizer 所有へ戻す。
            try:
                _close_fds_best_effort([result_fd])
            except Exception:
                pass
            raise


def _resolve_site(site: Optional[str]) -> str:
    """注入値を尊重し、未指定時だけ実環境の site を解決する。"""
    return site_policy.current_site() if site is None else site


def require_heavy_work_site(site: Optional[str], what: str) -> str:
    """重い producer の起動を許す site を返し、login/suspect は拒否する。

    拒否理由は subprocess を伴わない ``site_policy.heavy_work_refusal`` だけで
    組み立てる。build cache hit 後の producer も同じ gate を再利用できるよう、
    build 実行 helper から独立した入口にする。
    """
    resolved_site = _resolve_site(site)
    if site_policy.refuses_heavy_work(resolved_site):
        raise BuildError(site_policy.heavy_work_refusal(resolved_site, what))
    return resolved_site


def compilers_for_current_site() -> tuple[str, str]:
    """実 site が Pegasus compute のときだけ system compiler を選ぶ。"""
    if _resolve_site(None) == site_policy.PEGASUS_COMPUTE:
        return "gcc", "g++"
    return DEFAULT_CC, DEFAULT_CXX


def _canonical_dependency_prefix_elements(
        value: str, *, separator: str,
) -> List[str]:
    """prefix を実効 cwd に束縛した path 要素列へ正準化する。"""
    cwd = os.path.realpath(os.getcwd())
    return [
        cwd if not piece else os.path.realpath(os.path.abspath(piece))
        for piece in value.split(separator)
    ]


def _canonical_ambient_dependency_prefix(value: Optional[str]) -> List[str]:
    """環境変数の path-separator 意味論を保った identity 用 path 要素列。"""
    if value is None or value == "":
        return []
    return _canonical_dependency_prefix_elements(value, separator=os.pathsep)


def _canonical_explicit_dependency_prefix(value: str) -> tuple[List[str], str]:
    """CMake cache variable の semicolon-list を identity/argv へ同時に束縛する。"""
    if not value:
        return [], ""
    elements = _canonical_dependency_prefix_elements(value, separator=";")
    return elements, ";".join(elements)


def _resolve_build_jobs(jobs: Optional[int], site: Optional[str]) -> int:
    """明示 jobs を尊重し、未指定時だけ site policy の既定値を使う。"""
    if jobs is not None:
        return jobs
    return site_policy.default_build_jobs(_resolve_site(site))


def _v2_commands(
        genome: Genome, trace: bool, sub: str, bdir: str,
        toolchain: Dict[str, Dict[str, str]], jobs: Optional[int] = None,
        *, site: Optional[str] = None, dependency_prefix: str = "",
        fetchcontent_base_dir: str = "",
) -> tuple[List[str], List[str]]:
    resolved_jobs = _resolve_build_jobs(jobs, site)
    target = f"ycsb_{genome.protocol}.exe"
    defines = genome.cmake_defines() + [f"-DCCBENCH_TRACE={int(trace)}"]
    prefix_define = (
        [f"-DCMAKE_PREFIX_PATH={dependency_prefix}"] if dependency_prefix else []
    )
    fetchcontent_define = (
        [f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base_dir}"]
        if fetchcontent_base_dir else []
    )
    configure = [
        toolchain["cmake"]["realpath"], "-S", sub, "-B", bdir,
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_C_COMPILER={toolchain['cc']['realpath']}",
        f"-DCMAKE_CXX_COMPILER={toolchain['cxx']['realpath']}",
    ] + prefix_define + fetchcontent_define + defines
    if fetchcontent_base_dir:
        if any(
                token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
                for token in configure):
            raise BuildCacheError(
                "FetchContent floor configure に SOURCE_DIR override がある"
            )
        if sum(
                token.startswith("-DFETCHCONTENT_BASE_DIR=")
                for token in configure) != 1:
            raise BuildCacheError(
                "FetchContent floor configure の BASE_DIR define 数が不正"
            )
    build_cmd = [
        toolchain["cmake"]["realpath"], "--build", bdir,
        "--target", target, "-j", str(resolved_jobs),
    ]
    return configure, build_cmd


def prepare_masstree_fetchcontent(
        *, ccbench_dir: str, fetchcontent_base_dir: str,
        expected_toolchain_manifest: Mapping[str, object],
        configure_timeout_s: int, target_timeout_s: int,
        site: Optional[str] = None, dependency_prefix: str = "",
) -> MasstreeFetchContentPreparation:
    """floor oracle 前に共有 base の masstree target だけを一度 build する。"""
    base = _canonical_fetchcontent_base(fetchcontent_base_dir)
    if (type(ccbench_dir) is not str or not os.path.isabs(ccbench_dir)
            or not os.path.isdir(ccbench_dir)):
        raise BuildCacheError("masstree prebuild の CCBench root が実 absolute directory でない")
    if (type(configure_timeout_s) is not int or configure_timeout_s <= 0
            or type(target_timeout_s) is not int or target_timeout_s <= 0):
        raise TypeError("masstree prebuild timeout は正整数必須")
    toolchain, _versions = _split_expected_toolchain_manifest(
        expected_toolchain_manifest,
    )
    resolved_site = _resolve_site(site)
    resolved_prefix = ""
    if dependency_prefix:
        _elements, resolved_prefix = _canonical_explicit_dependency_prefix(
            dependency_prefix,
        )
    build_dir = os.path.join(base, "izanagi-masstree-prebuild")
    prefix_define = (
        [f"-DCMAKE_PREFIX_PATH={resolved_prefix}"] if resolved_prefix else []
    )
    configure = [
        toolchain["cmake"]["realpath"], "-S", os.path.realpath(ccbench_dir),
        "-B", build_dir,
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_C_COMPILER={toolchain['cc']['realpath']}",
        f"-DCMAKE_CXX_COMPILER={toolchain['cxx']['realpath']}",
        f"-DFETCHCONTENT_BASE_DIR={base}",
    ] + prefix_define
    build_cmd = [
        toolchain["cmake"]["realpath"], "--build", build_dir,
        "--target", "masstree_build", "-j",
        str(_resolve_build_jobs(None, resolved_site)),
    ]
    if any(token.startswith("-DFETCHCONTENT_SOURCE_DIR_") for token in configure):
        raise BuildCacheError("masstree prebuild configure に SOURCE_DIR override がある")
    if sum(token.startswith("-DFETCHCONTENT_BASE_DIR=") for token in configure) != 1:
        raise BuildCacheError("masstree prebuild configure の BASE_DIR define 数が不正")
    try:
        _run(configure, "configure", timeout_s=configure_timeout_s, site=resolved_site)
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        raise MasstreeFetchContentError(
            "configure", f"masstree FetchContent configure 失敗: {exc}",
        ) from exc
    try:
        _run(build_cmd, "build", timeout_s=target_timeout_s, site=resolved_site)
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        raise MasstreeFetchContentError(
            "target", f"masstree FetchContent target 失敗: {exc}",
        ) from exc
    return MasstreeFetchContentPreparation(
        fetchcontent_base_dir=base,
        build_dir=build_dir,
        configure_argv=tuple(configure),
        build_argv=tuple(build_cmd),
    )


def _v2_result(
        genome: Genome, trace: bool, binary: str, bin_sha256: str, bdir: str,
        cached: bool, sub: str, root: str,
        toolchain: Dict[str, Dict[str, str]], contract_sha256: str, site: str,
        dependency_prefix: str, fetchcontent_base_dir: str = "",
        masstree_source_root_sha256: str = "",
) -> BuildResult:
    configure, build_cmd = _v2_commands(
        genome, trace, sub, bdir, toolchain, site=site,
        dependency_prefix=dependency_prefix,
        fetchcontent_base_dir=fetchcontent_base_dir,
    )
    return BuildResult(
        genome=genome, trace=trace, binary=binary, bin_sha256=bin_sha256,
        build_dir=bdir, cached=cached,
        configure_cmd=" ".join(configure), build_cmd=" ".join(build_cmd),
        configure_argv=tuple(configure), build_argv=tuple(build_cmd),
        cache_root=os.path.abspath(root), ccbench_root=os.path.abspath(sub),
        contract_sha256=contract_sha256,
        fetchcontent_base_dir=fetchcontent_base_dir,
        masstree_source_root_sha256=masstree_source_root_sha256,
    )


def _mkdir_open_at(parent_fd: int, name: str, *, label: str) -> tuple[int, os.stat_result]:
    fd = -1
    created = False
    try:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
        created = True
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        fd = _open_checked_directory_at(parent_fd, name, label=label)
        os.fchmod(fd, 0o700)
    except FileExistsError:
        raise
    except Exception as exc:
        cleanup_errors = []
        if fd >= 0:
            try:
                _close_fds_best_effort([fd])
            except Exception as cleanup_exc:
                cleanup_errors.append(f"fd close: {cleanup_exc}")
        if created:
            try:
                os.rmdir(name, dir_fd=parent_fd)
            except OSError as cleanup_exc:
                cleanup_errors.append(f"rmdir: {cleanup_exc}")
        if cleanup_errors:
            raise BuildCacheError(
                f"{label} を create-only で作れない: {name}: {exc}; "
                f"cleanup 失敗: {'; '.join(cleanup_errors)}"
            ) from exc
        if isinstance(exc, OSError):
            raise BuildCacheError(
                f"{label} を create-only で作れない: {name}: {exc}"
            ) from exc
        raise
    return fd, before


def _verify_directory_entry(
        parent_fd: int, name: str, held_fd: int, expected: os.stat_result, *, label: str,
) -> None:
    try:
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as exc:
        raise BuildCacheError(f"{label} を rename 直前に再照合できない: {name}: {exc}") from exc
    held = os.fstat(held_fd)
    if (not stat.S_ISDIR(entry.st_mode)
            or _stat_identity(entry) != _stat_identity(expected)
            or _stat_identity(entry) != _stat_identity(held)):
        raise BuildCacheError(f"{label} identity が rename 前に変化した: {name}")


def _entry_lexists_at(parent_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise BuildCacheError(f"cache entry を no-follow stat できない: {name}: {exc}") from exc


def _acquire_v2_claim(claim: str, parent: str, nonce: str, *, parent_fd: int) -> None:
    claim_name = os.path.basename(claim)
    claim_fd = -1
    try:
        claim_fd, _ = _mkdir_open_at(parent_fd, claim_name, label="v2 build claim")
    except FileExistsError as exc:
        raise BuildCacheError(
            f"v2 build claim が既に存在する: {claim} — 他 process が build 中または stale。"
            "待機・自動 retry・stale 自動削除は行わない; 手動回収が必要"
        ) from exc
    except OSError as exc:
        raise BuildCacheError(f"v2 build claim を取得できない: {claim}: {exc}") from exc
    owner = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "starttime": time.time(),
        "nonce": nonce,
    }
    try:
        _write_fsynced_json_at(claim_fd, "owner.json", owner)
        os.fsync(claim_fd)
        os.fsync(parent_fd)
    except (OSError, ValueError) as exc:
        # 取得済み claim は stale として残す。自動削除すると別 process と区別不能になる。
        raise BuildCacheError(f"v2 build claim receipt の永続化に失敗: {claim}: {exc}") from exc
    finally:
        if claim_fd >= 0:
            os.close(claim_fd)


def _release_v2_claim(claim: str, parent: str, *, parent_fd: int) -> None:
    """正常 publish 後に限り、自 process が取得した claim を除去する。"""
    claim_name = os.path.basename(claim)
    claim_fd = -1
    try:
        claim_fd = _open_checked_directory_at(parent_fd, claim_name, label="v2 build claim")
        os.unlink("owner.json", dir_fd=claim_fd)
        os.close(claim_fd)
        claim_fd = -1
        os.rmdir(claim_name, dir_fd=parent_fd)
        os.fsync(parent_fd)
    except OSError as exc:
        raise BuildCacheError(
            f"publish 後の v2 build claim を除去できない: {claim}: {exc}; 手動回収が必要"
        ) from exc
    finally:
        if claim_fd >= 0:
            os.close(claim_fd)


def build_v2(
        genome: Genome, *, admission: BuildAdmission,
        build_context: BuildRunContext, source_evidence: SourceEvidence,
        contract: ExecutionEnvironmentContract,
        ccbench_commit: str, trace: bool, src_token: Optional[str] = None,
        cc: str, cxx: str, cache_root: str, ccbench_dir: str = "",
        timeout_s: Optional[int] = None, site: Optional[str] = None,
        dependency_prefix: str = "",
        expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
        fetchcontent_base_dir: str = "",
        fetchcontent_dependency_receipt: Optional[Mapping[str, object]] = None,
) -> BuildResult:
    """contract namespace に staging/claim/manifest 付きで build する v2 API。

    copy-out destination は held fd と directory entry の inode を publish 直前まで
    再照合する。CMake には staging pathname を渡すため、staging 全体が fd で
    anchor されるとは主張しない。

    ``admission`` は pipeline が current source evidence から導出した sealed value に限る。
    materializer 境界で context/source と再検証し、完全な receipt を cache preimage と
    completion manifest の双方へ束縛する。

    ``contract`` を省略できる legacy fallback は意図的に持たない。legacy caller は従来の
    :func:`build` / :func:`cache_key` namespace に隔離したまま、floor/oracle の v2 consumer
    だけが本 API を明示引数で呼ぶ。``ccbench_dir`` は cache preimage へは入れず、選択した
    tree の内容を ``src_token`` が束縛する。allowlist/commit/src-token/trace-diff 検査は
    すべてその tree に対して発火する。``timeout_s=None`` は既存どおり無制限である。
    ``site=None`` は実環境から解決し、build command と起動 gate は同じ注入 seam を使う。
    identity の site は注入値でなく実環境から独立に解決する。非空の
    ``dependency_prefix`` は configure argv へ明示し、subprocess 環境の同名変数を除く。
    空なら argv と環境継承を変えず、ambient 値の正準形だけを identity に束縛する。
    ``expected_toolchain_manifest`` が指定された場合だけ、identity 用 manifest に加えて
    ``version`` 全文を別に再観測し、双方の完全一致を要求する。既定 ``None`` は従来の
    受理集合と実行順を変えない。

    fresh publish は untrusted staging から binary だけを clean candidate へ copy し、
    host-generated ``completion.json`` とともに完成名へ rename する。Python 3.10 stdlib
    には ``renameat2(RENAME_NOREPLACE)`` がないため、directory publish の create-only
    原子性は保証しない。cache publish 時点の inode 厳格化に限定した境界である。
    """
    _require_secure_fs_contract()
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    if type(source_evidence) is not SourceEvidence:
        raise TypeError("source_evidence は resolve_evidence() 由来の exact value が必要")
    admission = require_build_admission(
        admission,
        expected_policy=build_context.policy,
        expected_source=source_evidence,
    )
    admission_identity = dict(admission.as_cache_identity())
    if src_token is not None and src_token != source_evidence.src_token:
        raise BuildCacheError("src_token が current SourceEvidence と不一致")
    src_token = source_evidence.src_token
    if not isinstance(contract, ExecutionEnvironmentContract):
        raise TypeError("contract は ExecutionEnvironmentContract の必須引数 (None/fallback 不可)")
    if type(trace) is not bool:
        raise TypeError(f"trace は bool でなければならない: {trace!r}")
    if timeout_s is not None and (type(timeout_s) is not int or timeout_s <= 0):
        raise TypeError(f"timeout_s は None または正整数でなければならない: {timeout_s!r}")
    for name, value in (
            ("ccbench_commit", ccbench_commit), ("src_token", src_token),
            ("cc", cc), ("cxx", cxx)):
        if type(value) is not str or not value:
            raise TypeError(f"{name} は非空 str でなければならない: {value!r}")
    if type(dependency_prefix) is not str or "\0" in dependency_prefix:
        raise TypeError(
            "dependency_prefix は NUL を含まない str でなければならない: "
            f"{dependency_prefix!r}"
        )
    dependency_receipt = _validate_fetchcontent_dependency_receipt(
        fetchcontent_dependency_receipt,
    )
    if bool(fetchcontent_base_dir) != (dependency_receipt is not None):
        raise BuildCacheError(
            "FETCHCONTENT_BASE_DIR と dependency receipt は同時指定必須"
        )
    canonical_fetchcontent_base = (
        _canonical_fetchcontent_base(fetchcontent_base_dir)
        if fetchcontent_base_dir else ""
    )
    try:
        root = os.fspath(cache_root)
    except TypeError as exc:
        raise TypeError(f"cache_root は path-like でなければならない: {cache_root!r}") from exc
    if type(root) is not str or not root:
        raise TypeError("cache_root は非空 str path でなければならない")
    root = os.path.abspath(root)
    actual_site = _resolve_site(None)
    resolved_site = actual_site if site is None else _resolve_site(site)
    if dependency_prefix:
        effective_dependency_prefix, configure_dependency_prefix = (
            _canonical_explicit_dependency_prefix(dependency_prefix)
        )
    else:
        effective_dependency_prefix = _canonical_ambient_dependency_prefix(
            os.environ.get("CMAKE_PREFIX_PATH")
        )
        configure_dependency_prefix = ""

    contract_sha256 = contract.contract_sha256
    if not is_full_sha256(contract_sha256):
        raise BuildCacheError(
            f"contract.contract_sha256 が full lowercase sha256 でない: {contract_sha256!r}"
        )
    sub = ccbench_dir or _ccbench_dir()
    _validate_request_evidence(genome, ccbench_commit, sub, source_evidence)
    _verify_ccbench_commit(sub, ccbench_commit)
    source_digest.assert_worktree_within_allowlist(sub)
    toolchain = _toolchain_manifest(cc, cxx)
    if expected_toolchain_manifest is not None:
        expected_identity, expected_versions = _split_expected_toolchain_manifest(
            expected_toolchain_manifest
        )
        if toolchain != expected_identity:
            raise BuildCacheError(
                "v2 toolchain manifest が caller の事前観測と不一致"
            )
        observed_versions = {
            role: _tool_version_full(entry["realpath"], role)
            for role, entry in toolchain.items()
        }
        if observed_versions != expected_versions:
            raise BuildCacheError(
                "v2 toolchain version 全文が caller の事前観測と不一致"
            )
    preimage, digest = _v2_identity(
        genome, ccbench_commit, trace, src_token, cc, cxx, toolchain,
        site=actual_site, dependency_prefix=effective_dependency_prefix,
        admission=admission_identity,
        fetchcontent_dependency_receipt=dependency_receipt,
    )
    parent = os.path.join(root, "contracts", contract_sha256)
    bdir = os.path.join(parent, digest)
    claim = os.path.join(parent, f"{digest}.building")
    binary_relpath = os.path.join(
        "cc", genome.protocol, f"ycsb_{genome.protocol}.exe",
    )
    parent_fd = _open_or_create_directory_path(parent)
    try:
        claim_name = os.path.basename(claim)
        bdir_name = os.path.basename(bdir)
        # 完成 entry より claim を先に見る。publish→claim 除去間の crash も自動回収しない。
        if _entry_lexists_at(parent_fd, claim_name):
            raise BuildCacheError(
                f"v2 build claim が既に存在する: {claim} — build 中または stale; 手動回収が必要"
            )
        if _entry_lexists_at(parent_fd, bdir_name):
            binary, bin_sha256, binary_fd, masstree_source_root_sha256 = _validate_v2_entry(
                bdir, preimage=preimage, digest=digest, toolchain=toolchain,
                binary_relpath=binary_relpath, contract_sha256=contract_sha256,
                admission=admission_identity,
                build_context=build_context, source_evidence=source_evidence,
                parent_fd=parent_fd, bdir_name=bdir_name,
            )
            try:
                _recheck_source_evidence(
                    genome, ccbench_commit, sub, cxx, source_evidence, bdir,
                    built_fresh=False,
                )
                _assert_trace_diff(
                    genome, ccbench_commit, sub, cxx, bdir, built_fresh=False,
                )
                if not trace:
                    _assert_no_trace_symbols(binary, binary_fd=binary_fd)
            finally:
                os.close(binary_fd)
            return _v2_result(
                genome, trace, binary, bin_sha256, bdir, True, sub, root, toolchain,
                contract_sha256, resolved_site, configure_dependency_prefix,
                canonical_fetchcontent_base, masstree_source_root_sha256,
            )

        nonce = secrets.token_hex(16)
        _acquire_v2_claim(claim, parent, nonce, parent_fd=parent_fd)
        staging_name = f".staging-{os.getpid()}-{nonce}"
        clean_name = f".publish-{os.getpid()}-{nonce}"
        staging = os.path.join(parent, staging_name)
        clean = os.path.join(parent, clean_name)
        staging_created = False
        clean_created = False
        staging_fd = -1
        clean_fd = -1
        copied: Optional[_CopiedBinary] = None
        try:
            if _entry_lexists_at(parent_fd, bdir_name):
                raise BuildCacheError(
                    f"v2 publish 先が claim 取得と競合して出現した: {bdir}; 上書きしない"
                )
            staging_fd, staging_identity = _mkdir_open_at(
                parent_fd, staging_name, label="v2 staging",
            )
            staging_created = True
            configure, build_cmd = _v2_commands(
                genome, trace, sub, staging, toolchain, site=resolved_site,
                dependency_prefix=configure_dependency_prefix,
                fetchcontent_base_dir=canonical_fetchcontent_base,
            )
            run_env = {}
            if configure_dependency_prefix:
                build_env = os.environ.copy()
                build_env.pop("CMAKE_PREFIX_PATH", None)
                run_env["env"] = build_env
            try:
                if site is None:
                    _run(configure, "configure", timeout_s=timeout_s, **run_env)
                    _run(build_cmd, "build", timeout_s=timeout_s, **run_env)
                else:
                    _run(
                        configure, "configure", timeout_s=timeout_s,
                        site=resolved_site, **run_env,
                    )
                    _run(
                        build_cmd, "build", timeout_s=timeout_s,
                        site=resolved_site, **run_env,
                    )
            except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                raise BuildError(f"v2 build 実行失敗 (staging={staging}): {exc}") from exc

            masstree_source_root_sha256 = ""
            if dependency_receipt is not None:
                effective_root = _masstree_source_root_from_cmake_cache(staging)
                masstree_source_root_sha256 = hashlib.sha256(
                    effective_root.encode("utf-8")
                ).hexdigest()
                observed_dependency_receipt = (
                    _observe_fetchcontent_dependency_receipt(
                        canonical_fetchcontent_base,
                    )
                )
                if observed_dependency_receipt != dependency_receipt:
                    raise BuildCacheError(
                        "FetchContent dependency 内容が build 中に変化した"
                    )

            clean_fd, clean_identity = _mkdir_open_at(
                parent_fd, clean_name, label="v2 clean publish candidate",
            )
            clean_created = True
            _verify_directory_entry(
                parent_fd, staging_name, staging_fd, staging_identity,
                label="v2 staging copy source",
            )
            copied = _secure_copy_binary(
                staging_fd, clean_fd, binary_relpath, clean,
            )

            _recheck_source_evidence(
                genome, ccbench_commit, sub, cxx, source_evidence, staging,
                built_fresh=True,
            )
            _assert_trace_diff(
                genome, ccbench_commit, sub, cxx, staging, built_fresh=True,
            )
            final_binary = os.path.join(bdir, binary_relpath)
            if not trace:
                _assert_no_trace_symbols(final_binary, binary_fd=copied.destination_fd)
            bin_sha256 = _full_sha256_fd(copied.destination_fd, final_binary)
            os.fsync(copied.destination_fd)
            copied.verify_destination_entry()
            completion = {
                "schema_version": _V2_SCHEMA,
                "completion_marker": "complete",
                "full_build_digest": digest,
                "contract_sha256": contract_sha256,
                "preimage": preimage,
                "admission": admission_identity,
                "toolchain": toolchain,
                "binary": {"relative_path": binary_relpath, "sha256": bin_sha256},
            }
            if dependency_receipt is not None:
                completion["fetchcontent_dependency"] = {
                    "source_root_sha256": masstree_source_root_sha256,
                    "source_subdir": "masstree-src",
                }
            _write_fsynced_json_at(clean_fd, _V2_COMPLETION_MANIFEST, completion)
            copied.fsync_directories()
            os.fsync(clean_fd)
            _discard_build_dir(staging)
            staging_created = False
            copied.verify_destination_entry()
            _verify_directory_entry(
                parent_fd, clean_name, clean_fd, clean_identity,
                label="v2 clean publish candidate",
            )
            if _entry_lexists_at(parent_fd, bdir_name):
                raise BuildCacheError(f"v2 publish 先が rename 直前に出現した: {bdir}")
            try:
                os.rename(
                    clean_name, bdir_name,
                    src_dir_fd=parent_fd, dst_dir_fd=parent_fd,
                )
            except OSError as exc:
                raise BuildCacheError(
                    f"v2 clean candidate publish に失敗: {clean} -> {bdir}: {exc}"
                ) from exc
            clean_created = False
            os.fsync(parent_fd)
            _release_v2_claim(claim, parent, parent_fd=parent_fd)
        except Exception:
            _discard_build_candidates(*(
                path for created, path in (
                    (staging_created, staging), (clean_created, clean),
                ) if created
            ))
            raise
        finally:
            owned_fds = [staging_fd, clean_fd]
            if copied is not None:
                owned_fds = copied._owned_fds() + owned_fds
            _close_fds_best_effort(owned_fds)

        binary = os.path.join(bdir, binary_relpath)
        return _v2_result(
            genome, trace, binary, bin_sha256, bdir, False, sub, root, toolchain,
            contract_sha256, resolved_site, configure_dependency_prefix,
            canonical_fetchcontent_base, masstree_source_root_sha256,
        )
    finally:
        os.close(parent_fd)


def build(genome: Genome, ccbench_commit: str, trace: bool,
          cache_root: str = "", cc: str = DEFAULT_CC, cxx: str = DEFAULT_CXX,
          jobs: Optional[int] = None, ccbench_dir: str = "",
          src_token: Optional[str] = None, *, admission: BuildAdmission,
          build_context: BuildRunContext, source_evidence: SourceEvidence,
          site: Optional[str] = None) -> BuildResult:
    """genome を (trace 有無で) ビルドし BuildResult を返す。キャッシュヒットなら skip。

    ``build_context`` / ``source_evidence`` / evidence-derived ``admission`` を exact
    再検証し、receipt digest を key と sidecar の両方へ束縛する。``src_token`` は互換用の
    期待値に限り、current evidence と不一致なら拒否する。

    cache contract は ``binary + host-generated admission.json``。旧 entry の extra member
    は hit 時に許容する。copy-out destination は held fd と directory entry の inode を
    publish 直前まで再照合する。一方 CMake には staging pathname を渡すため、staging
    全体が fd で anchor されるとは主張しない。fresh publish は clean candidate のみを
    完成名へ rename するが、Python 3.10 stdlib では directory publish の create-only
    原子性は保証しない。
    """
    _require_secure_fs_contract()
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    if type(source_evidence) is not SourceEvidence:
        raise TypeError("source_evidence は resolve_evidence() 由来の exact value が必要")
    admission = require_build_admission(
        admission,
        expected_policy=build_context.policy,
        expected_source=source_evidence,
    )
    if src_token is not None and src_token != source_evidence.src_token:
        raise BuildCacheError("src_token が current SourceEvidence と不一致")
    src_token = source_evidence.src_token
    sub = ccbench_dir or _ccbench_dir()
    _validate_request_evidence(genome, ccbench_commit, sub, source_evidence)
    _verify_ccbench_commit(sub, ccbench_commit)        # 偽キャッシュヒット防止 (honest)
    source_digest.assert_worktree_within_allowlist(sub)  # coder の編集面が EVOLVE-BLOCK 内か (D23)
    root = cache_root or os.path.join(sub, "build-variants")
    key = cache_key(
        genome, ccbench_commit, trace, src_token, cc=cc, cxx=cxx,
        admission=admission,
    )
    bdir = os.path.join(root, key)
    target = f"ycsb_{genome.protocol}.exe"
    binary = os.path.join(bdir, "cc", genome.protocol, target)
    resolved_site = _resolve_site(site)
    resolved_jobs = _resolve_build_jobs(jobs, resolved_site)

    # ビルドコマンドを先に組み立てる (cache hit でも実験再現用に BuildResult へ記録する)。
    defines = genome.cmake_defines() + [f"-DCCBENCH_TRACE={int(trace)}"]
    cfg = ["cmake", "-S", sub, "-B", bdir, "-DCMAKE_BUILD_TYPE=Release",
           "-DENABLE_SANITIZER=OFF", f"-DCMAKE_C_COMPILER={cc}",
           f"-DCMAKE_CXX_COMPILER={cxx}"] + defines
    build_cmd = [
        "cmake", "--build", bdir, "--target", target,
        "-j", str(resolved_jobs),
    ]
    cfg_str, build_str = " ".join(cfg), " ".join(build_cmd)

    root_fd = _open_or_create_directory_path(root)
    bdir_name = os.path.basename(bdir)
    binary_relpath = os.path.join("cc", genome.protocol, target)
    try:
        if _entry_lexists_at(root_fd, bdir_name):
            bdir_fd = _open_checked_directory_at(
                root_fd, bdir_name, label="legacy cache entry",
            )
            try:
                if _relative_entry_lexists(
                        bdir_fd, binary_relpath, label="legacy cached binary"):
                    _validate_legacy_admission_sidecar(
                        bdir, admission=admission, build_context=build_context,
                        source_evidence=source_evidence, directory_fd=bdir_fd,
                    )
                    binary_fd, _ = _open_regular_at(
                        bdir_fd, binary_relpath, label=f"legacy cached binary {binary}",
                    )
                    try:
                        _recheck_source_evidence(
                            genome, ccbench_commit, sub, cxx, source_evidence,
                            bdir, built_fresh=False,
                        )
                        _assert_trace_diff(
                            genome, ccbench_commit, sub, cxx, bdir, built_fresh=False,
                        )
                        if not trace:
                            _assert_no_trace_symbols(binary, binary_fd=binary_fd)
                        bin_sha256 = _full_sha256_fd(binary_fd, binary)
                    finally:
                        os.close(binary_fd)
                    return BuildResult(
                        genome=genome, trace=trace, binary=binary,
                        bin_sha256=bin_sha256, build_dir=bdir, cached=True,
                        configure_cmd=cfg_str, build_cmd=build_str,
                        configure_argv=tuple(cfg), build_argv=tuple(build_cmd),
                        cache_root=os.path.abspath(root), ccbench_root=os.path.abspath(sub),
                    )
            finally:
                os.close(bdir_fd)
            _clear_stale_build_dir(bdir, binary)

        nonce = secrets.token_hex(16)
        staging_name = f"{bdir_name}.staging-{os.getpid()}-{nonce}"
        clean_name = f".publish-{os.getpid()}-{nonce}"
        staging = os.path.join(root, staging_name)
        clean = os.path.join(root, clean_name)
        staging_fd, staging_identity = _mkdir_open_at(
            root_fd, staging_name, label="legacy staging",
        )
        staging_created = True
        clean_created = False
        clean_fd = -1
        copied: Optional[_CopiedBinary] = None
        bin_sha256 = ""
        try:
            staging_cfg = [
                "cmake", "-S", sub, "-B", staging, "-DCMAKE_BUILD_TYPE=Release",
                "-DENABLE_SANITIZER=OFF", f"-DCMAKE_C_COMPILER={cc}",
                f"-DCMAKE_CXX_COMPILER={cxx}",
            ] + defines
            staging_build_cmd = [
                "cmake", "--build", staging, "--target", target,
                "-j", str(resolved_jobs),
            ]
            if site is None:
                _run(staging_cfg, "configure")
                _run(staging_build_cmd, "build")
            else:
                _run(staging_cfg, "configure", site=resolved_site)
                _run(staging_build_cmd, "build", site=resolved_site)

            clean_fd, clean_identity = _mkdir_open_at(
                root_fd, clean_name, label="legacy clean publish candidate",
            )
            clean_created = True
            _verify_directory_entry(
                root_fd, staging_name, staging_fd, staging_identity,
                label="legacy staging copy source",
            )
            copied = _secure_copy_binary(
                staging_fd, clean_fd, binary_relpath, clean,
            )
            _recheck_source_evidence(
                genome, ccbench_commit, sub, cxx, source_evidence,
                staging, built_fresh=True,
            )
            _assert_trace_diff(
                genome, ccbench_commit, sub, cxx, staging, built_fresh=True,
            )
            if not trace:
                _assert_no_trace_symbols(binary, binary_fd=copied.destination_fd)
            bin_sha256 = _full_sha256_fd(copied.destination_fd, binary)
            os.fsync(copied.destination_fd)
            copied.verify_destination_entry()
            _write_fsynced_json_at(
                clean_fd, _LEGACY_ADMISSION_SIDECAR,
                {
                    "schema_version": _LEGACY_ADMISSION_SCHEMA,
                    "admission": admission.as_cache_identity(),
                },
            )
            copied.fsync_directories()
            os.fsync(clean_fd)
            _discard_build_dir(staging)
            staging_created = False
            copied.verify_destination_entry()
            _verify_directory_entry(
                root_fd, clean_name, clean_fd, clean_identity,
                label="legacy clean publish candidate",
            )
            if _entry_lexists_at(root_fd, bdir_name):
                raise BuildCacheError(
                    f"legacy publish 先が build 中に出現したため上書きしない: {bdir}"
                )
            try:
                os.rename(
                    clean_name, bdir_name, src_dir_fd=root_fd, dst_dir_fd=root_fd,
                )
            except OSError as exc:
                raise BuildCacheError(
                    f"legacy clean candidate publish に失敗: {clean} -> {bdir}: {exc}"
                ) from exc
            clean_created = False
            os.fsync(root_fd)
        except Exception:
            _discard_build_candidates(*(
                path for created, path in (
                    (staging_created, staging), (clean_created, clean),
                ) if created
            ))
            raise
        finally:
            owned_fds = [staging_fd, clean_fd]
            if copied is not None:
                owned_fds = copied._owned_fds() + owned_fds
            _close_fds_best_effort(owned_fds)

        return BuildResult(
            genome=genome, trace=trace, binary=binary,
            bin_sha256=bin_sha256, build_dir=bdir, cached=False,
            configure_cmd=" ".join(staging_cfg), build_cmd=" ".join(staging_build_cmd),
            configure_argv=tuple(staging_cfg), build_argv=tuple(staging_build_cmd),
            cache_root=os.path.abspath(root), ccbench_root=os.path.abspath(sub),
        )
    finally:
        os.close(root_fd)


def _recheck_source_evidence(
        genome: Genome, ccbench_commit: str, sub: str, cxx: str,
        expected: SourceEvidence, bdir: str, built_fresh: bool,
) -> None:
    """build 出口で current SourceEvidence 全体を exact 再照合する。

    再計算は resolve_evidence の単一窓口 —
    tree が動いて allowlist 外改変が入ったケースも同時に捕える。数十 ms で規律4 に反しない
    (phase3.md タスク定義)。新規ビルドの不一致は汚染バイナリの永続を防ぐため build dir を
    破棄する。cache hit の不一致は既存 (過去の正当な) 成果物なので破棄せず停止のみ。"""
    try:
        actual = source_digest.resolve_evidence(
            genome, ccbench_commit, ccbench_dir=sub, cxx=cxx,
        )
    except RuntimeError:
        # resolve 自体の失敗 (TOCTOU 汚染 / git・g++ の transient 障害を区別できない)。
        # identity 不明のバイナリは共有キャッシュに残さない (偽 hit 防止 > 再ビルドコスト) —
        # cache_key で次 run が再ビルドするので D25 の再評価可能性は保たれる (transient でも
        # 消すのは意図的な非対称)。破棄の成否まで確認する (下の _discard)。
        if built_fresh:
            _discard_build_dir(bdir)
        raise
    if actual != expected:
        if built_fresh:
            _discard_build_dir(bdir)
        raise RuntimeError(
            f"TOCTOU 検知: build {'後' if built_fresh else '(cache hit)'} の "
            "SourceEvidence 再計算が resolve 時と不一致 — "
            "resolve→build 間に working-tree が動いた。汚染バイナリを共有キャッシュに"
            f"永続させないため{'破棄して' if built_fresh else ''}停止する "
            "(fails-closed, phase3.md blocking / D30)")


def _assert_trace_diff(genome: Genome, ccbench_commit: str, sub: str, cxx: str,
                       bdir: str, built_fresh: bool) -> None:
    """build 出口の観測者効果二重検査 (diff-of-diffs、規律1 の一次防壁)。

    発火単位 = 毎 variant の trace/perf ビルド直後 (phase3.md タスク定義)。nm の
    name-based 検査 (_assert_no_trace_symbols) は data-structure 観測者効果と
    #ifdef TRACE 内側への挙動差隠蔽を見逃す — その補完で、述語の実体は
    source_digest.assert_trace_diff_matches_head。不一致・preprocess 失敗の variant
    バイナリは規律1 違反 (検証コードが perf ビルドに混入しうる) の疑いを晴らせないので、
    新規ビルドは build dir ごと破棄して共有キャッシュに残さない (_recheck_source_evidence と
    同じ非対称: cache hit 側は既存の正当な成果物なので破棄せず停止のみ)。"""
    try:
        source_digest.assert_trace_diff_matches_head(genome, ccbench_commit, sub, cxx)
    except RuntimeError:
        if built_fresh:
            _discard_build_dir(bdir)
        raise


def _clear_stale_build_dir(bdir: str, binary: str) -> None:
    """kill 等で中断された中途 build dir (binary 不在で dir だけ残る) を configure 前に破棄する。

    build 途中の kill では Python の例外経路 (_discard_build_dir) が走らず、
    「CMakeCache.txt あり・binary 無し」の残骸が共有キャッシュに永続する。残骸の
    CMakeCache には当時の一時 worktree パス (実行ごとランダム) が焼き付いているため、
    以後の同一 variant の configure が cmake のソースディレクトリ不一致で**毎回即死**する
    (2026-07-11 s8a sweep の stock 点が二重起動事故の kill 以降 build-error を再発し続けた
    実障害)。正当な完成品 (binary あり) は呼び手の cache hit 経路が先に扱う — ここに来る
    既存 dir は不完全と確定しているので、破棄してから新規 configure する (fails-closed 側の
    回復。破棄の成否検査は _discard_build_dir と共通)。"""
    if not os.path.lexists(bdir):
        return
    try:
        info = os.stat(bdir, follow_symlinks=False)
    except OSError as exc:
        raise BuildCacheError(f"stale build dir を no-follow stat できない: {bdir}: {exc}") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise BuildCacheError(f"stale build dir が symlink または非 directory: {bdir}")
    bdir_fd = _open_directory_path_nofollow(bdir, label="stale build dir")
    try:
        relpath = os.path.relpath(binary, bdir)
        if _relative_entry_lexists(bdir_fd, relpath, label="stale binary"):
            return
    finally:
        os.close(bdir_fd)
    _discard_build_dir(bdir)


def _discard_build_dir(bdir: str) -> None:
    """汚染 build dir を破棄し、消し残しを検査する (fails-closed)。

    rmtree(ignore_errors=True) の沈黙 (権限・使用中で消せない) を放置すると、残った汚染
    バイナリが**次 run の cache hit で再照合されず再利用**される (再照合は『今の tree の
    resolve == expected』のみで残存バイナリの由来を見ない, 2026-07-03 敵対検証 low)。破棄
    失敗を明示例外にし、汚染の永続を沈黙させない。"""
    if not os.path.lexists(bdir):
        return
    try:
        info = os.stat(bdir, follow_symlinks=False)
    except OSError as exc:
        raise BuildCacheError(f"汚染 build dir を no-follow stat できない: {bdir}: {exc}") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise BuildCacheError(f"汚染 build dir が symlink または非 directory: {bdir}")
    shutil.rmtree(bdir, ignore_errors=True)
    if os.path.lexists(bdir):
        raise RuntimeError(
            f"汚染 build dir を破棄できなかった ({bdir}) — 権限/使用中を疑え。残存すると "
            "次 run の cache hit で汚染バイナリが再利用される。手動で削除してから再実行すること "
            "(fails-closed)")


def _discard_build_candidates(*paths: str) -> None:
    """全 candidate の破棄を試み、1 件でも残れば cleanup failure として停止する。"""
    failures = []
    for path in paths:
        try:
            _discard_build_dir(path)
        except Exception as exc:
            failures.append((path, exc))
    if failures:
        detail = "; ".join(f"{path}: {exc}" for path, exc in failures)
        raise BuildCacheError(f"build failure 後の candidate cleanup に失敗: {detail}") from failures[0][1]


def _has_trace_symbols(nm_output: str) -> bool:
    """nm 出力に izanagi_trace シンボルが含まれるか (perf build への trace 漏れ判定)。"""
    return any("izanagi_trace" in ln.lower() for ln in nm_output.splitlines())


def _assert_no_trace_symbols(binary: str, *, binary_fd: Optional[int] = None) -> None:
    """perf (trace-disabled) build に trace シンボルが 1 つも無いことを assert (絶対規律1 の継続執行)。

    観測者効果分離は `#if TRACE` のソース層が一次防壁だが、誰かが `#ifdef TRACE` に書き戻す/
    CMake が常に `-DTRACE` を出す等で**サイレントに perf build へ漏れる**回帰を、ビルドごとに
    機械検出する (worklog の一度きり手動 nm を継続執行に格上げ)。nm が起動できない/失敗する
    環境では fails-closed で停止する — 「一次防壁の回帰」と「nm の欠如」が複合した瞬間だけ
    検査が沈黙するのは規律1/3 に反する (旧実装は silent pass だった、洗練検査 LOW)。
    限界: strip 済みバイナリはシンボル 0 で素通りする (ビルド直後の非 strip 前提)。"""
    inspected = binary if binary_fd is None else f"/proc/self/fd/{binary_fd}"
    run_kwargs: Dict[str, Any] = {"capture_output": True, "text": True}
    if binary_fd is not None:
        run_kwargs["pass_fds"] = (binary_fd,)
    try:
        r = subprocess.run(["nm", "-C", inspected], **run_kwargs)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"規律1 検査不能: nm を起動できない ({e})。trace シンボル漏れを検査できない"
            f"環境で perf build を採用しない (fails-closed): {binary}") from e
    if r.returncode != 0:
        raise RuntimeError(
            f"規律1 検査不能: nm が失敗 (rc={r.returncode}): {r.stderr[-200:]} "
            f"(fails-closed で停止): {binary}")
    if _has_trace_symbols(r.stdout):
        raise RuntimeError(
            f"絶対規律1 違反: perf (trace-disabled) build に izanagi_trace シンボルが漏れている: "
            f"{binary}。#if TRACE でなく #ifdef TRACE に書き戻された / CMake が -DTRACE を常に "
            "出す等を疑え (decisions D14)。")


def _run(
        cmd: List[str], what: str, timeout_s: Optional[int] = None,
        *, site: Optional[str] = None, env: Optional[Dict[str, str]] = None,
) -> None:
    if what in {"configure", "build"}:
        require_heavy_work_site(site, f"cmake {what}")
    run_kwargs: Dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": timeout_s,
    }
    if env is not None:
        run_kwargs["env"] = env
    r = subprocess.run(cmd, **run_kwargs)
    if r.returncode != 0:
        raise RuntimeError(f"{what} failed (rc={r.returncode}): "
                           f"{r.stderr[-800:]}")


def _verify_ccbench_commit(sub: str, declared: str) -> None:
    """宣言 ccbench_commit が submodule の実 HEAD と一致するか照合する。

    cache_key は宣言文字列だけで決まる (bin_hash は provenance 専用で照合に未使用)。
    宣言が実 HEAD とずれていると、別版でビルドしたバイナリを偽キャッシュヒットさせる。
    一致しなければ即停止 (ident.IdentityMismatch と同じ関所思想)。git が無い/submodule
    未 init なら照合不能なので best-effort で skip — ただし同経路では source_digest
    (source_digest.py) が git/g++ 不在時に fails-closed で先に停止するため、この skip
    単独で偽キャッシュヒットが通ることはない (実ビルドも cmake 側で失敗する)。"""
    if not declared:
        return
    try:
        r = subprocess.run(["git", "-C", sub, "rev-parse", "HEAD"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return
    head = r.stdout.strip()
    if r.returncode != 0 or not head:
        return
    if not head.startswith(declared):
        raise RuntimeError(
            f"ccbench_commit 不一致: 宣言={declared} だが submodule HEAD={head[:12]}。"
            "誤った版でのビルド/偽キャッシュヒットを防ぐため停止する "
            "(honest-by-construction)。")
