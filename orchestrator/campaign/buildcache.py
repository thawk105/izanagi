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
import inspect
import json
import os
import re
import secrets
import shutil
import socket
import stat
import subprocess
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from . import (
    s8b_compiler_input,
    s8b_expected_materialization,
    site_policy,
    sort_swo_dependency_material,
    source_digest,
)
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
_SEALED_SOURCE_CONTRACT = "sealed-source-snapshot/v1"
_V2_COMPLETION_MANIFEST = "completion.json"
_LEGACY_ADMISSION_SCHEMA = "buildcache-legacy-admission/v1"
_LEGACY_ADMISSION_SIDECAR = "admission.json"
_FETCHCONTENT_SOURCE_NAMES = ("masstree", "mimalloc", "googletest")
_FETCHCONTENT_RECEIPT_KEYS = frozenset({
    "masstree_head", "config_sha256",
})
_POST_ORACLE_DEPENDENCY_BINDING_KEYS = frozenset({
    "fetchcontent_base_dir", "oracle_dependency_root",
    "dependency_manifest_sha256",
    "masstree_head", "config_sha256", "archive_sha256",
})
_POST_ORACLE_POPULATION_POLICY_ID = (
    "post-oracle-fully-disconnected-manifest-bound/v1"
)
_FETCHCONTENT_FULLY_DISCONNECTED_DEFINE = (
    "-DFETCHCONTENT_FULLY_DISCONNECTED=ON"
)
# B-10 の PBS script が exact token を供給し、専用 driver が正式相の入口で
# 同じ token を必須化する。generic v2 caller は env 不在なら従来どおりである。
B10_BINARY_PATH_POLICY_ENV = "IZANAGI_B10_BINARY_PATH_POLICY"
B10_BINARY_PATH_POLICY = "b10-macro-prefix-map-no-rpath/v1"
B10_LOGICAL_SOURCE_ROOT = "/__izanagi_b10__/source"
B10_LOGICAL_BUILD_ROOT = "/__izanagi_b10__/build"

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
    # v2 の実効 toolchain。identity 用の短い manifest と、caller binding 用の
    # version 全文 manifest/hash は別系列として保持する。legacy build() は None。
    toolchain: Optional[Dict[str, Dict[str, str]]] = None
    toolchain_manifest: Optional[Dict[str, Dict[str, str]]] = None
    toolchain_manifest_sha256: Optional[str] = None
    # v2 compiler-input proof。legacy build() は additive default None。
    compiler_input_manifest: Optional[Dict[str, Any]] = None
    compiler_input_manifest_sha256: Optional[str] = None
    # live validation だけに使う。completion / receipt へ絶対 root を保存しない。
    compiler_input_dependency_prefix_roots: tuple[str, ...] = ()
    # Declaration gate output.  Descriptor-less callers retain None exactly.
    source_snapshot_sha256: Optional[str] = None
    expected_materialization_sha256: Optional[str] = None
    # floor sort_best 専用の runtime 診断。空の既定 caller は従来どおり。
    fetchcontent_base_dir: str = ""
    masstree_source_root_sha256: str = ""
    source_protection: Optional[s8b_expected_materialization.SealedSnapshotCapability] = None

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
    for key in ("config_sha256",):
        if not is_full_sha256(normalized[key]):
            raise BuildCacheError(f"FetchContent dependency receipt の {key} が不正")
    return normalized


def _validate_fetchcontent_archive_sha256(value: object) -> Optional[str]:
    """Validate the optional run-local archive observation.

    The two-key dependency receipt remains a compatibility surface.  Floor
    production callers additionally pass this observation so a different run
    may use different archive bytes while one run cannot silently replace them.
    """
    if value is None:
        return None
    if not is_full_sha256(value):
        raise BuildCacheError(
            "FetchContent dependency archive sha256 が不正"
        )
    return value


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


def _canonical_post_oracle_dependency_root(value: object) -> str:
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise BuildCacheError(
            "post-oracle canonical dependency root が path-like でない"
        ) from exc
    if type(raw) is not str or not raw or "\0" in raw or not os.path.isabs(raw):
        raise BuildCacheError(
            "post-oracle canonical dependency root は NUL なし絶対 path 必須"
        )
    if os.path.islink(raw) or not os.path.isdir(raw):
        raise BuildCacheError(
            "post-oracle canonical dependency root は non-symlink directory 必須"
        )
    canonical = os.path.realpath(raw)
    if canonical != os.path.abspath(raw):
        raise BuildCacheError(
            "post-oracle canonical dependency root は canonical path 必須"
        )
    return canonical


def _validate_post_oracle_dependency_binding(
        value: Optional[Mapping[str, object]],
) -> Optional[Dict[str, str]]:
    """Validate the single capability that authorizes a post-oracle build."""
    if value is None:
        return None
    if (not isinstance(value, Mapping)
            or set(value) != _POST_ORACLE_DEPENDENCY_BINDING_KEYS):
        raise BuildCacheError("post-oracle dependency binding の exact key 集合が不正")
    normalized = {
        "fetchcontent_base_dir": _canonical_fetchcontent_base(
            value["fetchcontent_base_dir"]
        ),
        "oracle_dependency_root": _canonical_post_oracle_dependency_root(
            value["oracle_dependency_root"]
        ),
        "dependency_manifest_sha256": value["dependency_manifest_sha256"],
        "masstree_head": value["masstree_head"],
        "config_sha256": value["config_sha256"],
        "archive_sha256": value["archive_sha256"],
    }
    if (type(normalized["masstree_head"]) is not str
            or re.fullmatch(
                r"[0-9a-f]{40}", normalized["masstree_head"],
            ) is None):
        raise BuildCacheError("post-oracle dependency binding の masstree HEAD が不正")
    for key in (
            "dependency_manifest_sha256", "config_sha256", "archive_sha256"):
        if not is_full_sha256(normalized[key]):
            raise BuildCacheError(
                f"post-oracle dependency binding の {key} が不正"
            )
    return normalized


def _canonical_fetchcontent_source_dir(value: object, *, name: str) -> str:
    """FetchContent SOURCE_DIR の canonical non-symlink directory を返す。"""
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise BuildCacheError(
            f"FetchContent {name} SOURCE_DIR が path-like でない"
        ) from exc
    if (type(raw) is not str or not raw or "\0" in raw
            or not os.path.isabs(raw)):
        raise BuildCacheError(
            f"FetchContent {name} SOURCE_DIR は NUL なし絶対 path 必須"
        )
    if os.path.islink(raw) or not os.path.isdir(raw):
        raise BuildCacheError(
            f"FetchContent {name} SOURCE_DIR は non-symlink directory 必須"
        )
    canonical = os.path.realpath(raw)
    if canonical != os.path.abspath(raw):
        raise BuildCacheError(
            f"FetchContent {name} SOURCE_DIR は canonical path 必須"
        )
    return canonical


def _normalize_fetchcontent_source_dirs(
        *, masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
) -> Dict[str, str]:
    """3本の SOURCE_DIR を all-or-nothing で canonicalize する。"""
    values = {
        "masstree": masstree_source_dir,
        "mimalloc": mimalloc_source_dir,
        "googletest": googletest_source_dir,
    }
    supplied = [name for name, value in values.items() if value is not None]
    if not supplied:
        return {}
    if len(supplied) != len(_FETCHCONTENT_SOURCE_NAMES):
        raise BuildCacheError(
            "FetchContent SOURCE_DIR は masstree/mimalloc/googletest の3本同時指定必須"
        )
    return {
        name: _canonical_fetchcontent_source_dir(values[name], name=name)
        for name in _FETCHCONTENT_SOURCE_NAMES
    }


def _fetchcontent_source_defines(source_dirs: Mapping[str, str]) -> List[str]:
    if not source_dirs:
        return []
    return [
        f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}={source_dirs[name]}"
        for name in _FETCHCONTENT_SOURCE_NAMES
    ]


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
    fd = -1
    try:
        entry = os.lstat(path)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(
            os, "O_CLOEXEC", 0,
        )
        fd = os.open(path, flags)
        before = os.fstat(fd)
        if (stat.S_ISLNK(entry.st_mode) or not stat.S_ISREG(entry.st_mode)
                or not stat.S_ISREG(before.st_mode)
                or _stat_identity(entry) != _stat_identity(before)):
            raise BuildCacheError(
                f"FetchContent dependency {label} が non-symlink regular file でない"
            )
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, 64 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(fd)
        if _stable_file_identity(before) != _stable_file_identity(after):
            raise BuildCacheError(
                f"FetchContent dependency {label} が hash 中に変化した"
            )
    except OSError as exc:
        raise BuildCacheError(
            f"FetchContent dependency {label} を再照合できない"
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)
    return digest.hexdigest()


def _observe_fetchcontent_archive_sha256(source_root: str) -> str:
    return _sha256_fetchcontent_file(
        os.path.join(source_root, "libkohler_masstree_json.a"),
        label="libkohler_masstree_json.a",
    )


def _observe_fetchcontent_dependency_receipt(
        source_root: str,
) -> Dict[str, str]:
    """completion publish 前に実効 masstree root の内容 receipt を再取得する。"""
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
    }


def _assert_post_oracle_dependency_material(
        binding: Mapping[str, str],
) -> None:
    """Require canonical exactness, live source equivalence, and archive hash."""
    base = _canonical_fetchcontent_base(binding["fetchcontent_base_dir"])
    source_root = os.path.join(base, "masstree-src")
    try:
        verified = sort_swo_dependency_material.assert_source_matches_canonical(
            Path(source_root),
            Path(binding["oracle_dependency_root"]),
            expected_head=binding["masstree_head"],
            expected_manifest_sha256=binding[
                "dependency_manifest_sha256"
            ],
        )
    except sort_swo_dependency_material.CanonicalDependencyMaterialError as exc:
        raise BuildCacheError(
            "FetchContent dependency canonical/source 二根検査に失敗: "
            f"{exc.detail_code}"
        ) from exc
    if verified.manifest_sha256 != binding["dependency_manifest_sha256"]:
        raise BuildCacheError(
            "FetchContent canonical SHA256SUMS が oracle receipt と不一致"
        )
    if verified.config_sha256 != binding["config_sha256"]:
        raise BuildCacheError(
            "FetchContent canonical/source config.h が oracle receipt と不一致"
        )
    if _observe_fetchcontent_archive_sha256(source_root) != binding["archive_sha256"]:
        raise BuildCacheError(
            "FetchContent dependency archive が oracle binding と不一致"
        )


def _assert_fetchcontent_fully_disconnected_effective(build_dir: str) -> None:
    cache = os.path.join(build_dir, "CMakeCache.txt")
    try:
        info = os.lstat(cache)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise BuildCacheError(
                "CMakeCache.txt が non-symlink regular file でない"
            )
        with open(cache, encoding="utf-8", errors="strict") as handle:
            matches = []
            for line in handle:
                match = re.fullmatch(
                    r"FETCHCONTENT_FULLY_DISCONNECTED:BOOL=([^\r\n]*)\r?\n?",
                    line,
                )
                if match is not None:
                    matches.append(match.group(1))
    except (OSError, UnicodeError) as exc:
        raise BuildCacheError(
            f"CMakeCache.txt から FetchContent disconnected 実効値を読めない: {cache}"
        ) from exc
    if matches != ["ON"]:
        raise BuildCacheError(
            "CMakeCache.txt の FETCHCONTENT_FULLY_DISCONNECTED 実効値が "
            "exact ON でない"
        )


def _masstree_source_root_from_cmake_cache(build_dir: str) -> str:
    """cache 入力と生成済み build system から masstree root を読む。

    この cache / DependInfo の形は CMake 3.22.1 と 3.25.0、CCBench pin
    ``511c9538e4e8efa54b45cda62e72389ed3b706ec``、Unix Makefiles 生成器で
    同一と実測された。base-only では空値の
    ``FETCHCONTENT_SOURCE_DIR_MASSTREE`` 行が常に 1 行存在する。
    CCBench pin 更新時は生成物の形を再実測すること。
    """
    cache = os.path.join(build_dir, "CMakeCache.txt")
    cache_keys = (
        "CMAKE_GENERATOR",
        "FETCHCONTENT_SOURCE_DIR_MASSTREE",
        "FETCHCONTENT_BASE_DIR",
    )
    try:
        info = os.lstat(cache)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise BuildCacheError("CMakeCache.txt が non-symlink regular file でない")
        with open(cache, encoding="utf-8", errors="strict") as handle:
            matches = {key: [] for key in cache_keys}
            for line in handle:
                for key in cache_keys:
                    match = re.fullmatch(
                        rf"{re.escape(key)}(?::[^=\r\n]*)?=([^\r\n]*)\r?\n?",
                        line,
                    )
                    if match is not None:
                        matches[key].append(match.group(1))
    except (OSError, UnicodeError) as exc:
        raise BuildCacheError(f"CMakeCache.txt から masstree source root を読めない: {cache}") from exc

    if (len(matches["CMAKE_GENERATOR"]) != 1
            or matches["CMAKE_GENERATOR"][0] != "Unix Makefiles"):
        raise BuildCacheError(
            "CMakeCache.txt の CMAKE_GENERATOR が一意な Unix Makefiles でない"
        )
    fetchcontent_keys = (
        "FETCHCONTENT_SOURCE_DIR_MASSTREE",
        "FETCHCONTENT_BASE_DIR",
    )
    if any(len(matches[key]) > 1 for key in fetchcontent_keys):
        raise BuildCacheError(
            "CMakeCache.txt の FetchContent masstree 解決 key が一意でない"
        )
    if (matches["FETCHCONTENT_SOURCE_DIR_MASSTREE"]
            and matches["FETCHCONTENT_SOURCE_DIR_MASSTREE"][0] != ""):
        selected_key = "FETCHCONTENT_SOURCE_DIR_MASSTREE"
        recorded = matches[selected_key][0]
        cache_root = recorded
    elif matches["FETCHCONTENT_BASE_DIR"]:
        selected_key = "FETCHCONTENT_BASE_DIR"
        recorded = matches[selected_key][0]
        cache_root = os.path.join(recorded, "masstree-src")
    else:
        raise BuildCacheError(
            "CMakeCache.txt に FetchContent masstree 解決 key がない"
        )
    if not os.path.isabs(recorded) or "\0" in recorded:
        raise BuildCacheError(
            f"CMakeCache.txt の {selected_key} が NUL なし絶対 path でない"
        )

    depend_info = os.path.join(
        build_dir, "CMakeFiles", "masstree_build.dir", "DependInfo.cmake",
    )
    try:
        info = os.lstat(depend_info)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise BuildCacheError(
                "masstree DependInfo.cmake が non-symlink regular file でない"
            )
        with open(depend_info, encoding="utf-8", errors="strict") as handle:
            depend_text = handle.read()
    except (OSError, UnicodeError) as exc:
        raise BuildCacheError(
            f"masstree DependInfo.cmake から実効 source root を読めない: "
            f"{depend_info}"
        ) from exc

    blocks = re.findall(
        r"(?ms)^[ \t]*set\([ \t]*CMAKE_MULTIPLE_OUTPUT_PAIRS[ \t]*\r?\n"
        r"(.*?)"
        r"^[ \t]*\)[ \t]*(?:#[^\r\n]*)?\r?$",
        depend_text,
    )
    if len(blocks) != 1:
        raise BuildCacheError(
            "masstree DependInfo.cmake の CMAKE_MULTIPLE_OUTPUT_PAIRS が一意でない"
        )
    pair = re.fullmatch(
        r"[ \t\r\n]*\"([^\"\r\n]*)\"[ \t\r\n]+"
        r"\"([^\"\r\n]*)\"[ \t\r\n]*",
        blocks[0],
    )
    if pair is None:
        raise BuildCacheError(
            "masstree DependInfo.cmake の multiple-output 対がちょうど 1 組でない"
        )
    generated_paths = pair.groups()
    if any(not os.path.isabs(path) or "\0" in path for path in generated_paths):
        raise BuildCacheError(
            "masstree DependInfo.cmake の multiple-output 対が NUL なし絶対 path でない"
        )
    outputs = {os.path.basename(path): path for path in generated_paths}
    expected_outputs = {"config.h", "libkohler_masstree_json.a"}
    if set(outputs) != expected_outputs:
        raise BuildCacheError(
            "masstree DependInfo.cmake の multiple-output 対が期待した生成物でない"
        )
    generated_roots = {os.path.dirname(path) for path in generated_paths}
    if len(generated_roots) != 1:
        raise BuildCacheError(
            "masstree DependInfo.cmake の multiple-output 対の親 directory が一致しない"
        )

    cache_root = os.path.realpath(cache_root)
    generated_root = os.path.realpath(generated_roots.pop())
    if cache_root != generated_root:
        raise BuildCacheError(
            "CMakeCache.txt と masstree DependInfo.cmake の source root が一致しない"
        )
    return cache_root


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


def observed_toolchain_manifest(cc: str, cxx: str) -> Dict[str, Dict[str, str]]:
    """現在の compiler/cmake を full version 付き manifest として一度観測する。

    campaign caller が開始時に得た値を各 variant へ配るための窓口であり、site ごとの
    compiler名をここで決めない。requested path の解決と version 全文の取得は既存の
    fails-closed helper に委譲する。
    """
    identity = _toolchain_manifest(cc, cxx)
    return {
        role: {
            **entry,
            "version": _tool_version_full(entry["realpath"], role),
        }
        for role, entry in identity.items()
    }


def toolchain_compilers_from_manifest(
        expected: Mapping[str, object],
) -> tuple[str, str]:
    """validated expected manifest から requested cc/cxx を取り出す。"""
    identity, _versions = _split_expected_toolchain_manifest(expected)
    return identity["cc"]["requested"], identity["cxx"]["requested"]


def _v2_identity(
        genome: Genome, ccbench_commit: str, trace: bool, src_token: str,
        cc: str, cxx: str, toolchain: Dict[str, Dict[str, str]],
        *, source_snapshot_sha256: Optional[str] = None, site: str,
        dependency_prefix: List[str],
        admission: Dict[str, Any],
        binary_path_policy: Optional[str] = None,
        fetchcontent_dependency_receipt: Optional[Mapping[str, object]] = None,
        fetchcontent_archive_sha256: Optional[object] = None,
        fetchcontent_transport_mode: Optional[str] = None,
        fetchcontent_population_policy: Optional[str] = None,
        fetchcontent_dependency_manifest_sha256: Optional[object] = None,
        compiler_input_policy: Optional[str] = None,
        expected_materialization_sha256: Optional[str] = None,
) -> tuple[Dict[str, Any], str]:
    """完全 pre-image と full build digest (64hex) を返す。"""
    if (source_snapshot_sha256 is not None
            and not is_full_sha256(source_snapshot_sha256)):
        raise BuildCacheError("source snapshot sha256 が不正")
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
    if expected_materialization_sha256 is not None:
        if not is_full_sha256(expected_materialization_sha256) or source_snapshot_sha256 is None:
            raise BuildCacheError("sealed source identity requires both snapshot digests")
        preimage["source_protection_contract"] = _SEALED_SOURCE_CONTRACT
        preimage["expected_materialization_sha256"] = expected_materialization_sha256
    if source_snapshot_sha256 is not None:
        preimage["source_snapshot_sha256"] = source_snapshot_sha256
        preimage["compiler_input_manifest_schema"] = (
            s8b_compiler_input.MANIFEST_SCHEMA
        )
    if binary_path_policy is not None:
        if binary_path_policy != B10_BINARY_PATH_POLICY:
            raise BuildCacheError("binary path policy が不正")
        preimage["binary_path_policy"] = binary_path_policy
    if compiler_input_policy is not None:
        if compiler_input_policy != "snapshot-and-external-hashes/v1":
            raise BuildCacheError("compiler input policy が不正")
        if source_snapshot_sha256 is None:
            raise BuildCacheError(
                "compiler input policy は source snapshot と同時指定必須"
            )
        preimage["compiler_input_policy"] = compiler_input_policy
    receipt = _validate_fetchcontent_dependency_receipt(
        fetchcontent_dependency_receipt,
    )
    if receipt is not None:
        preimage["fetchcontent_dependency_receipt"] = receipt
    archive_sha256 = _validate_fetchcontent_archive_sha256(
        fetchcontent_archive_sha256,
    )
    if archive_sha256 is not None:
        if receipt is None:
            raise BuildCacheError(
                "FetchContent archive sha256 は dependency receipt と同時指定必須"
            )
        preimage["fetchcontent_archive_sha256"] = archive_sha256
    if fetchcontent_transport_mode is not None:
        if fetchcontent_transport_mode not in {"base-only", "source-dir"}:
            raise BuildCacheError(
                "FetchContent transport mode は base-only/source-dir のいずれか"
            )
        preimage["fetchcontent_transport_mode"] = fetchcontent_transport_mode
    if fetchcontent_population_policy is not None:
        if fetchcontent_population_policy != _POST_ORACLE_POPULATION_POLICY_ID:
            raise BuildCacheError("FetchContent population policy ID が不正")
        if receipt is None or archive_sha256 is None:
            raise BuildCacheError(
                "FetchContent population policy は dependency receipt/archive と同時指定必須"
            )
        if not is_full_sha256(fetchcontent_dependency_manifest_sha256):
            raise BuildCacheError(
                "FetchContent population policy の dependency manifest sha256 が不正"
            )
        preimage["fetchcontent_population_policy"] = (
            fetchcontent_population_policy
        )
        preimage["fetchcontent_dependency_manifest_sha256"] = (
            fetchcontent_dependency_manifest_sha256
        )
    elif fetchcontent_dependency_manifest_sha256 is not None:
        raise BuildCacheError(
            "FetchContent dependency manifest sha256 は population policy と同時指定必須"
        )
    return preimage, hashlib.sha256(_canonical_json_bytes(preimage)).hexdigest()


def _assert_source_snapshot_sha256(
        snapshot_root: str, expected_sha256: str) -> None:
    """Require one exact Unit-A tree digest without reinterpreting exclusions."""
    if not is_full_sha256(expected_sha256):
        raise BuildCacheError("source snapshot sha256 が不正")
    try:
        actual = s8b_expected_materialization.snapshot_tree_digest(
            os.path.realpath(snapshot_root),
        )
    except s8b_expected_materialization.ExpectedMaterializationError as exc:
        raise BuildCacheError(
            f"source snapshot tree digest を検証できない: {exc}"
        ) from exc
    if actual != expected_sha256:
        raise BuildCacheError(
            "source snapshot tree digest が build request と不一致"
        )


def _collect_compiler_inputs(
        build_dir: str, snapshot_root: str, *, target: str,
        allow_external_inputs: bool,
        expected_evolve_block_sources: Optional[Mapping[str, str]],
        origin_fetchcontent_masstree_root: Optional[str],
        current_fetchcontent_masstree_root: Optional[str],
        origin_dependency_prefix_roots: tuple[str, ...],
        current_dependency_prefix_roots: tuple[str, ...],
) -> s8b_compiler_input.CompilerInputManifest:
    """Call the production collector with the descriptor-bound policy.

    Older unit fakes expose only the legacy ``target`` keyword.  They remain a
    test seam when no EVOLVE-BLOCK source proof is expected; a real descriptor
    source can never silently lose its independent bytes check.
    """
    collector = s8b_compiler_input.collect_compiler_input_manifest
    kwargs: Dict[str, Any] = {"target": target}
    try:
        parameters = inspect.signature(collector).parameters
    except (TypeError, ValueError):
        parameters = {}
    supports_policy = (
        (
            "allow_external_inputs" in parameters
            and "expected_evolve_block_sources" in parameters
            and "origin_fetchcontent_masstree_root" in parameters
            and "current_fetchcontent_masstree_root" in parameters
            and "origin_dependency_prefix_roots" in parameters
            and "current_dependency_prefix_roots" in parameters
        )
        or any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in parameters.values()
        )
    )
    if supports_policy:
        kwargs.update({
            "allow_external_inputs": allow_external_inputs,
            "expected_evolve_block_sources": expected_evolve_block_sources,
            "origin_fetchcontent_masstree_root": (
                origin_fetchcontent_masstree_root
            ),
            "current_fetchcontent_masstree_root": (
                current_fetchcontent_masstree_root
            ),
            "origin_dependency_prefix_roots": (
                origin_dependency_prefix_roots
            ),
            "current_dependency_prefix_roots": (
                current_dependency_prefix_roots
            ),
        })
    elif expected_evolve_block_sources or allow_external_inputs:
        raise BuildCacheError(
            "compiler input collector does not expose current root binding"
        )
    result = collector(build_dir, snapshot_root, **kwargs)
    return result


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
        source_snapshot_root: Optional[str] = None,
        compiler_target: Optional[str] = None,
        expected_evolve_block_sources: Optional[Mapping[str, str]] = None,
        current_compiler_input_masstree_root: Optional[str] = None,
        current_compiler_input_dependency_prefix_roots: Optional[
            tuple[str, ...]
        ] = None,
        complete_toolchain_manifest: Optional[Dict[str, Dict[str, str]]] = None,
        complete_toolchain_manifest_sha256: Optional[str] = None,
        parent_fd: Optional[int] = None, bdir_name: Optional[str] = None,
) -> tuple[
        str, str, int, str, Optional[Dict[str, Any]], Optional[str],
]:
    """完成 entry の host metadata と binary を held fd beneath-only で検証する。

    cache contract は ``binary + host-generated metadata`` である。旧実装が発行した
    entry の extra member は互換性のため hit 時に拒否しない、という残余を意図的に保つ。
    ただし、許容される extra member は ``complete_toolchain_manifest`` /
    ``complete_toolchain_manifest_sha256`` の optional pair に限られる。
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
        if "source_protection_contract" in preimage:
            expected_keys.add("source_protection")
        snapshot_bound = "source_snapshot_sha256" in preimage
        if snapshot_bound:
            expected_keys.update({
                "compiler_input_manifest", "compiler_input_manifest_sha256",
            })
        dependency_receipt = preimage.get("fetchcontent_dependency_receipt")
        dependency_archive_sha256 = preimage.get(
            "fetchcontent_archive_sha256"
        )
        if dependency_receipt is not None:
            expected_keys.add("fetchcontent_dependency")
        optional_pair = {
            "complete_toolchain_manifest",
            "complete_toolchain_manifest_sha256",
        }
        actual_keys = set(manifest)
        if (
            actual_keys != expected_keys
            and actual_keys != (expected_keys | optional_pair)
        ):
            raise BuildCacheError(
                f"v2 completion manifest field 集合が不一致: {manifest_path}: "
                f"actual={sorted(actual_keys)}"
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
        compiler_input_manifest = None
        compiler_input_manifest_sha256 = None
        if snapshot_bound:
            if source_snapshot_root is None or compiler_target is None:
                raise BuildCacheError(
                    f"v2 compiler input manifest の検証 context がない: {manifest_path}"
                )
            try:
                compiler_input_manifest = (
                    s8b_compiler_input.validate_compiler_input_manifest(
                        manifest["compiler_input_manifest"],
                        manifest["compiler_input_manifest_sha256"],
                        snapshot_root=source_snapshot_root,
                        target=compiler_target,
                        expected_evolve_block_sources=(
                            expected_evolve_block_sources
                        ),
                        current_fetchcontent_masstree_root=(
                            current_compiler_input_masstree_root
                        ),
                        current_dependency_prefix_roots=(
                            current_compiler_input_dependency_prefix_roots
                        ),
                    )
                )
                if compiler_input_manifest.get("schema_version") != preimage.get(
                        "compiler_input_manifest_schema"):
                    raise s8b_compiler_input.CompilerInputError(
                        "compiler input manifest schema differs from cache preimage"
                    )
                if compiler_input_manifest.get("input_policy") != preimage.get(
                        "compiler_input_policy"):
                    raise s8b_compiler_input.CompilerInputError(
                        "compiler input policy differs from cache preimage"
                    )
            except s8b_compiler_input.CompilerInputError as exc:
                raise BuildCacheError(
                    f"v2 compiler input manifest 検証失敗: {manifest_path}: {exc}"
                ) from exc
            compiler_input_manifest_sha256 = manifest[
                "compiler_input_manifest_sha256"
            ]
        if complete_toolchain_manifest is not None:
            if manifest.get("complete_toolchain_manifest") != complete_toolchain_manifest:
                raise BuildCacheError(
                    f"v2 complete toolchain manifest 完全一致検査に失敗: {manifest_path}"
                )
            if (manifest.get("complete_toolchain_manifest_sha256")
                    != complete_toolchain_manifest_sha256):
                raise BuildCacheError(
                    f"v2 complete toolchain manifest sha256 不一致: {manifest_path}"
                )
        source_root_sha256 = ""
        if dependency_receipt is not None:
            dependency = manifest["fetchcontent_dependency"]
            dependency_keys = {"source_root_sha256", "source_subdir"}
            if dependency_archive_sha256 is not None:
                dependency_keys.add("archive_sha256")
            if (type(dependency) is not dict
                    or set(dependency) != dependency_keys
                    or dependency.get("source_subdir") != "masstree-src"
                    or not is_full_sha256(dependency.get("source_root_sha256"))):
                raise BuildCacheError(
                    f"v2 FetchContent dependency manifest が不正: {manifest_path}"
                )
            if (dependency_archive_sha256 is not None
                    and dependency.get("archive_sha256")
                    != dependency_archive_sha256):
                raise BuildCacheError(
                    f"v2 FetchContent archive sha256 が pre-image と不一致: "
                    f"{manifest_path}"
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
        if "source_protection_contract" in preimage:
            expected_protection = {
                "kind": "sealed-build",
                "source_snapshot_sha256": preimage["source_snapshot_sha256"],
                "expected_materialization_sha256": preimage["expected_materialization_sha256"],
                "binary_sha256": actual,
                "compiler_input_manifest_sha256": compiler_input_manifest_sha256,
            }
            if (preimage["source_protection_contract"] != _SEALED_SOURCE_CONTRACT
                    or manifest["source_protection"] != expected_protection):
                raise BuildCacheError("v2 sealed source protection record mismatch")
        result_fd = binary_fd
        binary_fd = -1
        return (
            binary, binary_record["sha256"], result_fd,
            source_root_sha256, compiler_input_manifest,
            compiler_input_manifest_sha256,
        )
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


def _binary_path_policy_from_environment() -> Optional[str]:
    value = os.environ.get(B10_BINARY_PATH_POLICY_ENV)
    if value is None:
        return None
    if value != B10_BINARY_PATH_POLICY:
        raise BuildCacheError(
            f"{B10_BINARY_PATH_POLICY_ENV} は exact B-10 policy token が必要"
        )
    return value


def _binary_path_cmake_defines(
        binary_path_policy: Optional[str], source_root: str,
        staging_root: Optional[str] = None,
) -> List[str]:
    if binary_path_policy is None:
        return []
    if binary_path_policy != B10_BINARY_PATH_POLICY:
        raise BuildCacheError("binary path policy が不正")
    canonical_root = os.path.realpath(os.path.abspath(source_root))
    if "\0" in canonical_root or "=" in canonical_root:
        raise BuildCacheError(
            "B-10 macro prefix map の source root に NUL/= は使えない"
        )
    macro_map = (
        f"-fmacro-prefix-map={canonical_root}={B10_LOGICAL_SOURCE_ROOT}"
    )
    cxx_flags = [macro_map]
    if staging_root is not None:
        canonical_staging_root = os.path.realpath(os.path.abspath(staging_root))
        if "\0" in canonical_staging_root or "=" in canonical_staging_root:
            raise BuildCacheError(
                "B-10 debug prefix map の staging root に NUL/= は使えない"
            )
        cxx_flags.append(
            f"-fdebug-prefix-map={canonical_staging_root}="
            f"{B10_LOGICAL_BUILD_ROOT}"
        )
    return [
        f"-DCMAKE_CXX_FLAGS={' '.join(cxx_flags)}",
        "-DCMAKE_SKIP_RPATH=ON",
    ]


def _v2_commands(
        genome: Genome, trace: bool, sub: str, bdir: str,
        toolchain: Dict[str, Dict[str, str]], jobs: Optional[int] = None,
        *, site: Optional[str] = None, dependency_prefix: str = "",
        binary_path_policy: Optional[str] = None,
        binary_path_staging_root: Optional[str] = None,
        fetchcontent_base_dir: str = "",
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
        post_oracle_dependency_binding: Optional[Mapping[str, object]] = None,
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
    if post_oracle_dependency_binding is not None and not fetchcontent_base_dir:
        raise BuildCacheError(
            "post-oracle dependency binding は FETCHCONTENT_BASE_DIR と同時指定必須"
        )
    fully_disconnected_define = (
        [_FETCHCONTENT_FULLY_DISCONNECTED_DEFINE]
        if post_oracle_dependency_binding is not None else []
    )
    source_dirs = _normalize_fetchcontent_source_dirs(
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
    )
    if source_dirs and not fetchcontent_base_dir:
        raise BuildCacheError(
            "FetchContent SOURCE_DIR は FETCHCONTENT_BASE_DIR と同時指定必須"
        )
    source_defines = _fetchcontent_source_defines(source_dirs)
    binary_path_defines = _binary_path_cmake_defines(
        binary_path_policy, sub, binary_path_staging_root,
    )
    configure = [
        toolchain["cmake"]["realpath"], "-S", sub, "-B", bdir,
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_C_COMPILER={toolchain['cc']['realpath']}",
        f"-DCMAKE_CXX_COMPILER={toolchain['cxx']['realpath']}",
    ] + prefix_define + fetchcontent_define + fully_disconnected_define \
        + source_defines + binary_path_defines + defines
    if fetchcontent_base_dir and sum(
            token.startswith("-DFETCHCONTENT_BASE_DIR=")
            for token in configure) != 1:
        raise BuildCacheError(
            "FetchContent floor configure の BASE_DIR define 数が不正"
        )
    if source_dirs:
        actual_source_defines = [
            token for token in configure
            if token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
        ]
        if actual_source_defines != source_defines:
            raise BuildCacheError(
                "FetchContent configure の SOURCE_DIR define 集合が不正"
            )
    elif fetchcontent_base_dir:
        if any(
                token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
                for token in configure):
            raise BuildCacheError(
                "FetchContent floor configure に SOURCE_DIR override がある"
            )
    expected_disconnected_count = (
        1 if post_oracle_dependency_binding is not None else 0
    )
    if configure.count(_FETCHCONTENT_FULLY_DISCONNECTED_DEFINE) != (
            expected_disconnected_count):
        raise BuildCacheError(
            "FetchContent configure の FULLY_DISCONNECTED define 数が不正"
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
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
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
    source_dirs = _normalize_fetchcontent_source_dirs(
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
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
    ] + prefix_define + _fetchcontent_source_defines(source_dirs)
    build_cmd = [
        toolchain["cmake"]["realpath"], "--build", build_dir,
        "--target", "masstree_build", "-j",
        str(_resolve_build_jobs(None, resolved_site)),
    ]
    source_defines = _fetchcontent_source_defines(source_dirs)
    actual_source_defines = [
        token for token in configure
        if token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
    ]
    if actual_source_defines != source_defines:
        raise BuildCacheError(
            "masstree prebuild configure の SOURCE_DIR define 集合が不正"
        )
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
        dependency_prefix: str, binary_path_policy: Optional[str] = None,
        fetchcontent_base_dir: str = "",
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
        masstree_source_root_sha256: str = "",
        toolchain_manifest: Optional[Dict[str, Dict[str, str]]] = None,
        toolchain_manifest_sha256: Optional[str] = None,
        compiler_input_manifest: Optional[Dict[str, Any]] = None,
        compiler_input_manifest_sha256: Optional[str] = None,
        compiler_input_dependency_prefix_roots: tuple[str, ...] = (),
        post_oracle_dependency_binding: Optional[Mapping[str, object]] = None,
) -> BuildResult:
    configure, build_cmd = _v2_commands(
        genome, trace, sub, bdir, toolchain, site=site,
        dependency_prefix=dependency_prefix,
        binary_path_policy=binary_path_policy,
        fetchcontent_base_dir=fetchcontent_base_dir,
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
        post_oracle_dependency_binding=post_oracle_dependency_binding,
    )
    return BuildResult(
        genome=genome, trace=trace, binary=binary, bin_sha256=bin_sha256,
        build_dir=bdir, cached=cached,
        configure_cmd=" ".join(configure), build_cmd=" ".join(build_cmd),
        configure_argv=tuple(configure), build_argv=tuple(build_cmd),
        cache_root=os.path.abspath(root), ccbench_root=os.path.abspath(sub),
        contract_sha256=contract_sha256,
        toolchain=toolchain,
        toolchain_manifest=toolchain_manifest,
        toolchain_manifest_sha256=toolchain_manifest_sha256,
        compiler_input_manifest=compiler_input_manifest,
        compiler_input_manifest_sha256=compiler_input_manifest_sha256,
        compiler_input_dependency_prefix_roots=(
            compiler_input_dependency_prefix_roots
        ),
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


@dataclass
class _PendingV2Publication:
    """Own the unpublished candidate until the sealed session has completed.

    This closes source replacement during compilation, not poisoned-cache reuse.
    Capabilities remain within the trusted Python producer boundary; they are
    neither kernel attestation nor signatures.
    """

    result: BuildResult
    completion: Dict[str, Any]
    parent_fd: int
    clean_fd: int
    clean_identity: os.stat_result
    copied: _CopiedBinary
    parent: str
    clean: str
    clean_name: str
    bdir_name: str
    claim: str
    published: bool = False

    def _verify_publish_entries(self) -> None:
        self.copied.verify_destination_entry()
        _verify_directory_entry(
            self.parent_fd, self.clean_name, self.clean_fd, self.clean_identity,
            label="v2 clean publish candidate",
        )
        if _entry_lexists_at(self.parent_fd, self.bdir_name):
            raise BuildCacheError(
                f"v2 publish 先が rename 直前に出現した: {self.result.build_dir}"
            )

    def publish(self, capability: s8b_expected_materialization.SealedSnapshotCapability) -> BuildResult:
        # Only build_v2 calls this, with session.issue's completed capability.
        self._verify_publish_entries()
        if _full_sha256_fd(self.copied.destination_fd, self.result.binary) != self.result.bin_sha256:
            raise BuildCacheError("v2 pending binary changed before publish")
        self.completion["source_protection"] = {
            "kind": capability.kind.value,
            "source_snapshot_sha256": capability.source_snapshot_sha256,
            "expected_materialization_sha256": capability.expected_materialization_sha256,
            "binary_sha256": capability.binary_sha256,
            "compiler_input_manifest_sha256": capability.compiler_input_manifest_sha256,
        }
        _write_fsynced_json_at(self.clean_fd, _V2_COMPLETION_MANIFEST, self.completion)
        self.copied.fsync_directories()
        os.fsync(self.clean_fd)
        self._verify_publish_entries()
        try:
            os.rename(
                self.clean_name, self.bdir_name,
                src_dir_fd=self.parent_fd, dst_dir_fd=self.parent_fd,
            )
        except OSError as exc:
            raise BuildCacheError(f"v2 clean candidate publish に失敗: {exc}") from exc
        self.published = True
        os.fsync(self.parent_fd)
        _release_v2_claim(self.claim, self.parent, parent_fd=self.parent_fd)
        return self.result

    def _discard_held_candidate(self) -> None:
        # A renamed candidate is still this directory, even outside self.parent.
        # Walk through held fds; never follow a replacement at self.clean.
        def empty(fd):
            for name in os.listdir(fd):
                entry = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISDIR(entry.st_mode):
                    child = _open_checked_directory_at(fd, name, label="discard candidate")
                    try:
                        empty(child)
                        _verify_directory_entry(fd, name, child, entry,
                                                label="discard candidate")
                        os.rmdir(name, dir_fd=fd)
                    finally:
                        os.close(child)
                else:
                    os.unlink(name, dir_fd=fd)

        empty(self.clean_fd)
        actual_parent = os.open("..", _secure_dir_flags(), dir_fd=self.clean_fd)
        try:
            for name in os.listdir(actual_parent):
                entry = os.stat(name, dir_fd=actual_parent, follow_symlinks=False)
                if _stat_identity(entry) == _stat_identity(self.clean_identity):
                    _verify_directory_entry(actual_parent, name, self.clean_fd,
                                            self.clean_identity, label="discard candidate")
                    os.rmdir(name, dir_fd=actual_parent)
                    break
            else:
                if os.fstat(self.clean_fd).st_nlink:
                    raise BuildCacheError("held candidate directory could not be removed")
        finally:
            os.close(actual_parent)

    def close(self) -> None:
        if self.clean_fd < 0:
            return
        try:
            if not self.published:
                self._discard_held_candidate()
                # Preserve the failure claim: no automatic retry of this key.
        finally:
            fds = self.copied._owned_fds() + [self.clean_fd, self.parent_fd]
            # Relinquish numbers before closing: even a failed close is not retried.
            self.clean_fd = self.parent_fd = -1
            self.copied.source_fd = self.copied.destination_fd = -1
            self.copied.destination_parent_fd = -1
            self.copied.directory_fds = []
            _close_fds_best_effort(fds)


def _build_v2_impl(
        genome: Genome, *, admission: BuildAdmission,
        build_context: BuildRunContext, source_evidence: SourceEvidence,
        source_snapshot_sha256: Optional[str] = None,
        sealed_session: Optional[s8b_expected_materialization.SealedBuildSession] = None,
        pending_publications: Optional[list[_PendingV2Publication]] = None,
        expected_materialization_sha256: Optional[str] = None,
        allow_external_compiler_inputs: bool = False,
        expected_evolve_block_sources: Optional[Mapping[str, str]] = None,
        contract: ExecutionEnvironmentContract,
        ccbench_commit: str, trace: bool, src_token: Optional[str] = None,
        cc: str, cxx: str, cache_root: str, ccbench_dir: str = "",
        backoff_grammar_version: Optional[int] = None,
        sort_oracle_contract_id: Optional[str] = None,
        timeout_s: Optional[int] = None, site: Optional[str] = None,
        dependency_prefix: str = "",
        expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
        declared_use_class: Optional[str] = None,
        fetchcontent_base_dir: str = "",
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
        fetchcontent_dependency_receipt: Optional[Mapping[str, object]] = None,
        fetchcontent_archive_sha256: Optional[object] = None,
        post_oracle_dependency_binding: Optional[Mapping[str, object]] = None,
        current_compiler_input_masstree_root: Optional[object] = None,
) -> BuildResult | _PendingV2Publication:
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
    ``version`` 全文を別に再観測し、双方の完全一致を要求する。``declared_use_class`` が
    ``official`` のときは expected の省略を build 前に拒否する。その他の caller では
    既定 ``None`` の受理集合と実行順を変えない。

    B-10 専用 policy env が exact token のときだけ、source root の macro 展開と buildcache
    staging root の debug path を論理 root へ写し、RPATH を生成しない CMake define を加える。
    policy ID は preimage に加えるが、admission の実 ``source_root`` と dependency prefix は
    投影せず従来どおり保持する。

    ``source_snapshot_sha256`` が指定されたときは Unit A の snapshot tree digest として
    build 前後で ``ccbench_dir`` の実体と exact 照合する。fresh build の成功直後、staging
    を破棄する前に compiler-input manifest を採取し、completion へ本文と digest を保存
    する。hit 側でも同じ validator を通す。未指定時は共有 API の従来 caller のため、
    preimage と completion に field を足さず、manifest の採取・照合も行わない。

    Declaration descriptor 経路は compiler-input policy と manifest schema を
    preimage に固定する。snapshot 内 input は snapshot entry bytes と一致必須、
    FetchContent masstree input は producer origin で分類・収集して、使用時の current
    canonical root に同じ relative path と hash で再束縛する。その他の filesystem input
    も root-relative path と bytes hash を記録し、snapshot 在籍を要求しない。選択された
    EVOLVE-BLOCK source がある configuration では、build 前に捕えた snapshot entry hash
    を build 後の source bytes と比較する。target dependency list への在籍だけを保証には
    しない。旧 schema の completion は別 identity のまま移行しない。

    この条件分岐は S8b の検査を外せる knob ではない。S8b 境界の receipt 発行器が
    compiler-input manifest を無条件に要求するため、snapshot 無しの binary には receipt
    を発行できない。共有 build 器が証拠を渡された場合に全検査する「条件付き検査」と、
    S8b 境界から検査を外す「検査除去」は異なる。ただし正式 S8b 経路では admission
    preimage が絶対 ``source_root`` を含み、materializer が毎回一意な worktree を作る
    ため cache hit は起きない。hit validator は proof 付き completion に proof が無ければ
    必ず拒否するために置く。

    ``post_oracle_dependency_binding`` の存在だけが post-oracle capability である。
    指定時は oracle receipt の manifest authority と HEAD/config/archive を configure
    前後で再照合し、configure の実効 disconnected 値を build 前に要求する。既存の
    FetchContent 引数を併記した場合は同じ内容だけを受理し、省略時は binding から導出する。
    binding が無い generic caller の argv と identity policy は従来どおりである。

    fresh publish は untrusted staging から binary だけを clean candidate へ copy し、
    host-generated ``completion.json`` とともに完成名へ rename する。Python 3.10 stdlib
    には ``renameat2(RENAME_NOREPLACE)`` がないため、directory publish の create-only
    原子性は保証しない。cache publish 時点の inode 厳格化に限定した境界である。
    """
    if expected_materialization_sha256 is not None:
        if sealed_session is None:
            raise BuildCacheError("descriptor build requires an exact sealed session")
        if type(sealed_session) is not s8b_expected_materialization.SealedBuildSession:
            raise BuildCacheError("descriptor build requires an exact sealed session")
        if (sealed_session.expected_materialization_sha256 != expected_materialization_sha256
                or sealed_session.source_snapshot_sha256 != source_snapshot_sha256):
            raise BuildCacheError("sealed session snapshot identity mismatch")
    elif sealed_session is not None:
        raise BuildCacheError("sealed session requires declaration identity")

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
    if (source_snapshot_sha256 is not None
            and not is_full_sha256(source_snapshot_sha256)):
        raise BuildCacheError(
            "source_snapshot_sha256 は None または exact lowercase SHA-256"
        )
    if type(allow_external_compiler_inputs) is not bool:
        raise TypeError("allow_external_compiler_inputs は exact bool が必要")
    if allow_external_compiler_inputs and source_snapshot_sha256 is None:
        raise BuildCacheError(
            "external compiler input policy は source snapshot と同時指定必須"
        )
    if expected_evolve_block_sources is not None:
        if not isinstance(expected_evolve_block_sources, Mapping):
            raise TypeError("expected_evolve_block_sources は Mapping が必要")
        expected_evolve_block_sources = dict(expected_evolve_block_sources)
    canonical_compiler_input_masstree_root = None
    if current_compiler_input_masstree_root is not None:
        try:
            canonical_compiler_input_masstree_root = str(
                s8b_compiler_input._strict_root(
                    current_compiler_input_masstree_root,
                    label="current compiler-input masstree root",
                )
            )
        except s8b_compiler_input.CompilerInputError as exc:
            raise BuildCacheError(
                f"current compiler-input masstree root が不正: {exc}"
            ) from exc
    if type(trace) is not bool:
        raise TypeError(f"trace は bool でなければならない: {trace!r}")
    if declared_use_class == "official" and expected_toolchain_manifest is None:
        raise BuildCacheError(
            "official v2 build には expected_toolchain_manifest が必須"
        )
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
    binary_path_policy = _binary_path_policy_from_environment()
    post_oracle_binding = _validate_post_oracle_dependency_binding(
        post_oracle_dependency_binding,
    )
    dependency_receipt = _validate_fetchcontent_dependency_receipt(
        fetchcontent_dependency_receipt,
    )
    dependency_archive_sha256 = _validate_fetchcontent_archive_sha256(
        fetchcontent_archive_sha256,
    )
    if post_oracle_binding is not None:
        binding_receipt = {
            "masstree_head": post_oracle_binding["masstree_head"],
            "config_sha256": post_oracle_binding["config_sha256"],
        }
        if fetchcontent_base_dir:
            if (_canonical_fetchcontent_base(fetchcontent_base_dir)
                    != post_oracle_binding["fetchcontent_base_dir"]):
                raise BuildCacheError(
                    "post-oracle binding と FETCHCONTENT_BASE_DIR が不一致"
                )
        else:
            fetchcontent_base_dir = post_oracle_binding[
                "fetchcontent_base_dir"
            ]
        if dependency_receipt is not None and dependency_receipt != binding_receipt:
            raise BuildCacheError(
                "post-oracle binding と dependency receipt が不一致"
            )
        dependency_receipt = binding_receipt
        if (dependency_archive_sha256 is not None
                and dependency_archive_sha256
                != post_oracle_binding["archive_sha256"]):
            raise BuildCacheError(
                "post-oracle binding と dependency archive sha256 が不一致"
            )
        dependency_archive_sha256 = post_oracle_binding["archive_sha256"]
    if dependency_archive_sha256 is not None and dependency_receipt is None:
        raise BuildCacheError(
            "FetchContent archive sha256 は dependency receipt と同時指定必須"
        )
    source_dirs = _normalize_fetchcontent_source_dirs(
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
    )
    if source_dirs and not fetchcontent_base_dir:
        raise BuildCacheError(
            "FetchContent SOURCE_DIR は FETCHCONTENT_BASE_DIR と同時指定必須"
        )
    if bool(fetchcontent_base_dir) != (dependency_receipt is not None):
        raise BuildCacheError(
            "FETCHCONTENT_BASE_DIR と dependency receipt は同時指定必須"
        )
    canonical_fetchcontent_base = (
        _canonical_fetchcontent_base(fetchcontent_base_dir)
        if fetchcontent_base_dir else ""
    )
    if post_oracle_binding is not None:
        _assert_post_oracle_dependency_material(post_oracle_binding)
    elif dependency_archive_sha256 is not None:
        observed_archive_sha256 = _observe_fetchcontent_archive_sha256(
            os.path.join(canonical_fetchcontent_base, "masstree-src"),
        )
        if observed_archive_sha256 != dependency_archive_sha256:
            raise BuildCacheError(
                "FetchContent dependency archive が build 前の binding と不一致"
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
    compiler_input_dependency_prefix_roots = (
        tuple(effective_dependency_prefix)
        if source_snapshot_sha256 is not None and allow_external_compiler_inputs
        else ()
    )

    fetchcontent_transport_mode = "source-dir" if source_dirs else None

    contract_sha256 = contract.contract_sha256
    if not is_full_sha256(contract_sha256):
        raise BuildCacheError(
            f"contract.contract_sha256 が full lowercase sha256 でない: {contract_sha256!r}"
        )
    sub = ccbench_dir or _ccbench_dir()
    _validate_request_evidence(genome, ccbench_commit, sub, source_evidence)
    if source_snapshot_sha256 is not None:
        _assert_source_snapshot_sha256(sub, source_snapshot_sha256)
    _verify_ccbench_commit(sub, ccbench_commit)
    source_digest.assert_worktree_within_allowlist(sub)
    toolchain = _toolchain_manifest(cc, cxx)
    complete_toolchain_manifest = None
    complete_toolchain_manifest_sha256 = None
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
        complete_toolchain_manifest = {
            role: {
                **toolchain[role],
                "version": observed_versions[role],
            }
            for role in toolchain
        }
        complete_toolchain_manifest_sha256 = hashlib.sha256(
            _canonical_json_bytes(complete_toolchain_manifest)
        ).hexdigest()
    preimage, digest = _v2_identity(
        genome, ccbench_commit, trace, src_token, cc, cxx, toolchain,
        source_snapshot_sha256=source_snapshot_sha256,
        expected_materialization_sha256=expected_materialization_sha256,
        site=actual_site, dependency_prefix=effective_dependency_prefix,
        admission=admission_identity,
        binary_path_policy=binary_path_policy,
        fetchcontent_dependency_receipt=dependency_receipt,
        fetchcontent_archive_sha256=dependency_archive_sha256,
        fetchcontent_transport_mode=fetchcontent_transport_mode,
        fetchcontent_population_policy=(
            _POST_ORACLE_POPULATION_POLICY_ID
            if post_oracle_binding is not None else None
        ),
        fetchcontent_dependency_manifest_sha256=(
            post_oracle_binding["dependency_manifest_sha256"]
            if post_oracle_binding is not None else None
        ),
        compiler_input_policy=(
            "snapshot-and-external-hashes/v1"
            if allow_external_compiler_inputs else None
        ),
    )
    parent = os.path.join(root, "contracts", contract_sha256)
    bdir = os.path.join(parent, digest)
    claim = os.path.join(parent, f"{digest}.building")
    binary_relpath = os.path.join(
        "cc", genome.protocol, f"ycsb_{genome.protocol}.exe",
    )
    parent_fd = _open_or_create_directory_path(parent)
    transferred = False
    pending = None
    try:
        claim_name = os.path.basename(claim)
        bdir_name = os.path.basename(bdir)
        # 完成 entry より claim を先に見る。publish→claim 除去間の crash も自動回収しない。
        if _entry_lexists_at(parent_fd, claim_name):
            raise BuildCacheError(
                f"v2 build claim が既に存在する: {claim} — build 中または stale; 手動回収が必要"
            )
        if _entry_lexists_at(parent_fd, bdir_name):
            (
                binary, bin_sha256, binary_fd,
                masstree_source_root_sha256,
                compiler_input_manifest,
                compiler_input_manifest_sha256,
            ) = _validate_v2_entry(
                bdir, preimage=preimage, digest=digest, toolchain=toolchain,
                binary_relpath=binary_relpath, contract_sha256=contract_sha256,
                admission=admission_identity,
                build_context=build_context, source_evidence=source_evidence,
                source_snapshot_root=(
                    sub if source_snapshot_sha256 is not None else None
                ),
                compiler_target=(
                    f"ycsb_{genome.protocol}.exe"
                    if source_snapshot_sha256 is not None else None
                ),
                expected_evolve_block_sources=expected_evolve_block_sources,
                current_compiler_input_masstree_root=(
                    canonical_compiler_input_masstree_root
                ),
                current_compiler_input_dependency_prefix_roots=(
                    compiler_input_dependency_prefix_roots
                ),
                complete_toolchain_manifest=complete_toolchain_manifest,
                complete_toolchain_manifest_sha256=complete_toolchain_manifest_sha256,
                parent_fd=parent_fd, bdir_name=bdir_name,
            )
            try:
                _recheck_source_evidence(
                    genome, ccbench_commit, sub, cxx, source_evidence, bdir,
                    built_fresh=False,
                    backoff_grammar_version=backoff_grammar_version,
                    sort_oracle_contract_id=sort_oracle_contract_id,
                )
                _assert_trace_diff(
                    genome, ccbench_commit, sub, cxx, bdir, built_fresh=False,
                )
                if not trace:
                    _assert_no_trace_symbols(binary, binary_fd=binary_fd)
                if post_oracle_binding is not None:
                    _assert_post_oracle_dependency_material(
                        post_oracle_binding
                    )
                elif dependency_archive_sha256 is not None:
                    post_hit_archive_sha256 = (
                        _observe_fetchcontent_archive_sha256(
                            os.path.join(
                                canonical_fetchcontent_base, "masstree-src",
                            )
                        )
                    )
                    if post_hit_archive_sha256 != dependency_archive_sha256:
                        raise BuildCacheError(
                            "FetchContent dependency archive が cache hit 中に変化した"
                        )
                if source_snapshot_sha256 is not None:
                    _assert_source_snapshot_sha256(
                        sub, source_snapshot_sha256,
                    )
            finally:
                os.close(binary_fd)
            return _v2_result(
                genome, trace, binary, bin_sha256, bdir, True, sub, root, toolchain,
                contract_sha256, resolved_site, configure_dependency_prefix,
                binary_path_policy,
                canonical_fetchcontent_base,
                source_dirs.get("masstree") if source_dirs else None,
                source_dirs.get("mimalloc") if source_dirs else None,
                source_dirs.get("googletest") if source_dirs else None,
                masstree_source_root_sha256,
                complete_toolchain_manifest, complete_toolchain_manifest_sha256,
                compiler_input_manifest, compiler_input_manifest_sha256,
                compiler_input_dependency_prefix_roots,
                post_oracle_binding,
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
                binary_path_policy=binary_path_policy,
                binary_path_staging_root=(
                    staging if binary_path_policy is not None else None
                ),
                fetchcontent_base_dir=canonical_fetchcontent_base,
                masstree_source_dir=(
                    source_dirs.get("masstree") if source_dirs else None
                ),
                mimalloc_source_dir=(
                    source_dirs.get("mimalloc") if source_dirs else None
                ),
                googletest_source_dir=(
                    source_dirs.get("googletest") if source_dirs else None
                ),
                post_oracle_dependency_binding=post_oracle_binding,
            )
            run_env = {}
            if sealed_session is not None:
                run_env["sealed_session"] = sealed_session
            if configure_dependency_prefix:
                build_env = os.environ.copy()
                build_env.pop("CMAKE_PREFIX_PATH", None)
                run_env["env"] = build_env
            if post_oracle_binding is not None:
                _assert_post_oracle_dependency_material(post_oracle_binding)
            try:
                if site is None:
                    _run(configure, "configure", timeout_s=timeout_s, **run_env)
                else:
                    _run(
                        configure, "configure", timeout_s=timeout_s,
                        site=resolved_site, **run_env,
                    )
            except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                raise BuildError(
                    f"v2 build 実行失敗 (staging={staging}): {exc}"
                ) from exc
            if post_oracle_binding is not None:
                _assert_fetchcontent_fully_disconnected_effective(staging)
                _assert_post_oracle_dependency_material(post_oracle_binding)

            if sealed_session is not None:
                run_env["build_output"] = os.path.join(staging, binary_relpath)

            if post_oracle_binding is not None:
                # Protection evidence is pre-build only.  Post-build checks
                # below intentionally re-read their own effective_root.
                protected_root = _masstree_source_root_from_cmake_cache(
                    staging
                )
                protection = (
                    sort_swo_dependency_material
                    .protect_post_oracle_dependency_material(
                        Path(protected_root),
                        fetchcontent_base_dir=Path(
                            post_oracle_binding["fetchcontent_base_dir"]
                        ),
                    )
                )
                with protection:
                    try:
                        if site is None:
                            _run(
                                build_cmd, "build", timeout_s=timeout_s,
                                **run_env,
                            )
                        else:
                            _run(
                                build_cmd, "build", timeout_s=timeout_s,
                                site=resolved_site, **run_env,
                            )
                    except (
                        OSError, subprocess.SubprocessError, RuntimeError,
                    ) as exc:
                        raise BuildError(
                            f"v2 build 実行失敗 (staging={staging}): {exc}"
                        ) from exc
            else:
                try:
                    if site is None:
                        _run(build_cmd, "build", timeout_s=timeout_s, **run_env)
                    else:
                        _run(
                            build_cmd, "build", timeout_s=timeout_s,
                            site=resolved_site, **run_env,
                        )
                except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                    raise BuildError(f"v2 build 実行失敗 (staging={staging}): {exc}") from exc

            compiler_input_manifest = None
            compiler_input_manifest_sha256 = None
            effective_root = None
            if source_snapshot_sha256 is not None:
                # .o.d は staging 破棄後に失われる。build 成功と同じ lifetime 内で
                # strict metadata と実効 masstree origin を同じ lifetime 内で採る。
                try:
                    effective_root = (
                        _masstree_source_root_from_cmake_cache(staging)
                        if allow_external_compiler_inputs else None
                    )
                    validation_root = (
                        canonical_compiler_input_masstree_root
                        or effective_root
                    ) if allow_external_compiler_inputs else None
                    compiler_inputs = _collect_compiler_inputs(
                        staging, sub,
                        target=f"ycsb_{genome.protocol}.exe",
                        allow_external_inputs=allow_external_compiler_inputs,
                        expected_evolve_block_sources=(
                            expected_evolve_block_sources
                        ),
                        origin_fetchcontent_masstree_root=effective_root,
                        current_fetchcontent_masstree_root=validation_root,
                        origin_dependency_prefix_roots=(
                            compiler_input_dependency_prefix_roots
                        ),
                        current_dependency_prefix_roots=(
                            compiler_input_dependency_prefix_roots
                        ),
                    )
                    if type(compiler_inputs) is not (
                            s8b_compiler_input.CompilerInputManifest):
                        raise s8b_compiler_input.CompilerInputError(
                            "compiler input collector returned an invalid value"
                        )
                    compiler_input_manifest = (
                        s8b_compiler_input.validate_compiler_input_manifest(
                            compiler_inputs.manifest,
                            compiler_inputs.manifest_sha256,
                            snapshot_root=sub,
                            target=f"ycsb_{genome.protocol}.exe",
                            expected_evolve_block_sources=(
                                expected_evolve_block_sources
                            ),
                            current_fetchcontent_masstree_root=validation_root,
                            current_dependency_prefix_roots=(
                                compiler_input_dependency_prefix_roots
                            ),
                        )
                    )
                    if compiler_input_manifest.get(
                            "schema_version") != preimage.get(
                                "compiler_input_manifest_schema"):
                        raise s8b_compiler_input.CompilerInputError(
                            "compiler input manifest schema differs from cache preimage"
                        )
                    if compiler_input_manifest.get(
                            "input_policy") != preimage.get(
                                "compiler_input_policy"):
                        raise s8b_compiler_input.CompilerInputError(
                            "compiler input policy differs from cache preimage"
                        )
                except s8b_compiler_input.CompilerInputError as exc:
                    raise BuildCacheError(
                        f"v2 compiler input manifest 採取失敗: {exc}"
                    ) from exc
                compiler_input_manifest_sha256 = (
                    compiler_inputs.manifest_sha256
                )
                _assert_source_snapshot_sha256(
                    sub, source_snapshot_sha256,
                )

            if post_oracle_binding is not None:
                _assert_post_oracle_dependency_material(post_oracle_binding)

            masstree_source_root_sha256 = ""
            if dependency_receipt is not None:
                if effective_root is None:
                    effective_root = _masstree_source_root_from_cmake_cache(
                        staging
                    )
                masstree_source_root_sha256 = hashlib.sha256(
                    effective_root.encode("utf-8")
                ).hexdigest()
                expected_root = os.path.join(
                    canonical_fetchcontent_base, "masstree-src",
                )
                if effective_root != expected_root:
                    raise BuildCacheError(
                        "FetchContent dependency の実効 source root が期待値と不一致"
                    )
                observed_dependency_receipt = (
                    _observe_fetchcontent_dependency_receipt(
                        effective_root,
                    )
                )
                if observed_dependency_receipt != dependency_receipt:
                    raise BuildCacheError(
                        "FetchContent dependency 内容が build 中に変化した"
                    )
                if dependency_archive_sha256 is not None:
                    observed_archive_sha256 = (
                        _observe_fetchcontent_archive_sha256(effective_root)
                    )
                    if observed_archive_sha256 != dependency_archive_sha256:
                        raise BuildCacheError(
                            "FetchContent dependency archive が build 中に変化した"
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
                backoff_grammar_version=backoff_grammar_version,
                sort_oracle_contract_id=sort_oracle_contract_id,
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
            if source_snapshot_sha256 is not None:
                completion["compiler_input_manifest"] = compiler_input_manifest
                completion["compiler_input_manifest_sha256"] = (
                    compiler_input_manifest_sha256
                )
            if complete_toolchain_manifest is not None:
                completion["complete_toolchain_manifest"] = complete_toolchain_manifest
                completion["complete_toolchain_manifest_sha256"] = (
                    complete_toolchain_manifest_sha256
                )
            if dependency_receipt is not None:
                completion["fetchcontent_dependency"] = {
                    "source_root_sha256": masstree_source_root_sha256,
                    "source_subdir": "masstree-src",
                }
                if dependency_archive_sha256 is not None:
                    completion["fetchcontent_dependency"]["archive_sha256"] = (
                        dependency_archive_sha256
                    )
            if sealed_session is None:
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
            if sealed_session is not None:
                binary = final_binary
                result = _v2_result(
                    genome, trace, binary, bin_sha256, bdir, False, sub, root, toolchain,
                    contract_sha256, resolved_site, configure_dependency_prefix,
                    binary_path_policy,
                    canonical_fetchcontent_base,
                    source_dirs.get("masstree") if source_dirs else None,
                    source_dirs.get("mimalloc") if source_dirs else None,
                    source_dirs.get("googletest") if source_dirs else None,
                    masstree_source_root_sha256,
                    complete_toolchain_manifest, complete_toolchain_manifest_sha256,
                    compiler_input_manifest, compiler_input_manifest_sha256,
                    compiler_input_dependency_prefix_roots,
                    post_oracle_binding,
                )
                if pending_publications is None:
                    raise BuildCacheError("sealed publication requires a caller-owned cleanup list")
                pending = _PendingV2Publication(
                    result, completion, parent_fd, clean_fd, clean_identity,
                    copied, parent, clean, clean_name, bdir_name, claim,
                )
                # Relinquish before close: close may release the descriptor and
                # still report an error. Never retry that numeric fd in finally.
                closing_staging_fd = staging_fd
                staging_fd = -1
                os.close(closing_staging_fd)
                # Register while the callee still owns cleanup. The caller's
                # finally can now recover even if return/assignment is interrupted.
                pending_publications.append(pending)
                transferred = True
                return pending
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
        except BaseException as exc:
            if sealed_session is None and not isinstance(exc, Exception):
                raise
            _discard_build_candidates(*(
                path for created, path in (
                    (staging_created, staging), (clean_created and pending is None, clean),
                ) if created
            ))
            raise
        finally:
            if pending is not None:
                try:
                    if not transferred:
                        pending.close()
                finally:
                    _close_fds_best_effort([staging_fd])
            else:
                owned_fds = [staging_fd, clean_fd]
                if copied is not None:
                    owned_fds = copied._owned_fds() + owned_fds
                _close_fds_best_effort(owned_fds)

        binary = os.path.join(bdir, binary_relpath)
        return _v2_result(
            genome, trace, binary, bin_sha256, bdir, False, sub, root, toolchain,
            contract_sha256, resolved_site, configure_dependency_prefix,
            binary_path_policy,
            canonical_fetchcontent_base,
            source_dirs.get("masstree") if source_dirs else None,
            source_dirs.get("mimalloc") if source_dirs else None,
            source_dirs.get("googletest") if source_dirs else None,
            masstree_source_root_sha256,
            complete_toolchain_manifest, complete_toolchain_manifest_sha256,
            compiler_input_manifest, compiler_input_manifest_sha256,
            compiler_input_dependency_prefix_roots,
            post_oracle_binding,
        )
    finally:
        if pending is None:
            os.close(parent_fd)


def _descriptor_shared_directories(
        sub, cache_root, shared_base, *, cc, cxx, source_dirs,
        dependency_prefix):
    """Restore the build's named inputs hidden by the private top component.

    Keep cwd semantics (including relative argv/environment paths). Source and
    its spine already exist in the private view and must never be shared back.
    Cache/base remain the first branches, including when not yet created.
    """
    root = Path(sub).resolve()
    shared = [os.path.realpath(os.path.abspath(cache_root))]
    if shared_base:
        shared.append(shared_base)
    inputs = [os.getcwd(), *source_dirs.values()]
    prefixes = (
        _canonical_explicit_dependency_prefix(dependency_prefix)[0]
        if dependency_prefix else
        _canonical_ambient_dependency_prefix(os.environ.get("CMAKE_PREFIX_PATH"))
    )
    inputs.extend(prefixes)
    # _tool_version resolves these same names; _v2_commands executes their
    # realpaths, not the PATH symlinks. Share their containing directories only.
    for requested in (cc, cxx, "cmake"):
        found = shutil.which(requested)
        if found:
            inputs.append(os.path.dirname(os.path.realpath(found)))
    for value in inputs:
        path = Path(value).resolve()
        if (path == root or root in path.parents or path in root.parents
                or path.parts[1:2] != root.parts[1:2]):
            continue
        # Absent search prefixes were ignored by CMake; don't create them.
        if not path.is_dir():
            continue
        if any(path == Path(branch).resolve()
               or Path(branch).resolve() in path.parents for branch in shared):
            continue
        shared.append(str(path))
    return shared


def build_v2(
        genome: Genome, *, admission: BuildAdmission,
        build_context: BuildRunContext, source_evidence: SourceEvidence,
        source_snapshot_sha256: Optional[str] = None,
        expected_materialization_descriptor: Optional[
            s8b_expected_materialization.ExpectedMaterializationDescriptor
        ] = None,
        contract: ExecutionEnvironmentContract,
        ccbench_commit: str, trace: bool, src_token: Optional[str] = None,
        cc: str, cxx: str, cache_root: str, ccbench_dir: str = "",
        backoff_grammar_version: Optional[int] = None,
        sort_oracle_contract_id: Optional[str] = None,
        timeout_s: Optional[int] = None, site: Optional[str] = None,
        dependency_prefix: str = "",
        expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
        declared_use_class: Optional[str] = None,
        fetchcontent_base_dir: str = "",
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
        fetchcontent_dependency_receipt: Optional[Mapping[str, object]] = None,
        fetchcontent_archive_sha256: Optional[object] = None,
        post_oracle_dependency_binding: Optional[Mapping[str, object]] = None,
        current_compiler_input_masstree_root: Optional[object] = None,
) -> BuildResult:
    """Build with a sealed compiler view when a declaration is supplied.

    The parent retains all source and D1755 checks. Only configure/build run in
    the session's child. A fresh candidate stays private until session cleanup,
    waitpid, root identity checks and permission restoration succeed; issue then
    supplies the capability before publication. Hits receive SEALED_CACHE_HIT,
    which does not assert that this process or a past process compiled safely.

    This closes build-time source replacement, not poisoned-cache reuse.
    Capabilities belong to the trusted Python producer boundary, not kernel
    attestation or signatures. Descriptor-less callers retain their previous
    argv, cache identity and completion schema, including Unit-B snapshots.
    The child's clone3/ENOSYS fallback was qualified on glibc 2.35 only;
    this does not assert compatibility with other libc implementations.
    """
    common = {
        "admission": admission,
        "build_context": build_context,
        "source_evidence": source_evidence,
        "contract": contract,
        "ccbench_commit": ccbench_commit,
        "trace": trace,
        "src_token": src_token,
        "cc": cc,
        "cxx": cxx,
        "cache_root": cache_root,
        "ccbench_dir": ccbench_dir,
        "timeout_s": timeout_s,
        "site": site,
        "dependency_prefix": dependency_prefix,
        "expected_toolchain_manifest": expected_toolchain_manifest,
        "declared_use_class": declared_use_class,
        "fetchcontent_base_dir": fetchcontent_base_dir,
        "masstree_source_dir": masstree_source_dir,
        "mimalloc_source_dir": mimalloc_source_dir,
        "googletest_source_dir": googletest_source_dir,
        "fetchcontent_dependency_receipt": fetchcontent_dependency_receipt,
        "fetchcontent_archive_sha256": fetchcontent_archive_sha256,
        "post_oracle_dependency_binding": post_oracle_dependency_binding,
        "current_compiler_input_masstree_root": (
            current_compiler_input_masstree_root
        ),
    }
    if backoff_grammar_version is not None:
        common["backoff_grammar_version"] = backoff_grammar_version
    if sort_oracle_contract_id is not None:
        common["sort_oracle_contract_id"] = sort_oracle_contract_id
    if expected_materialization_descriptor is None:
        return _build_v2_impl(
            genome,
            source_snapshot_sha256=source_snapshot_sha256,
            **common,
        )
    if type(expected_materialization_descriptor) is not (
            s8b_expected_materialization.ExpectedMaterializationDescriptor):
        raise TypeError(
            "expected_materialization_descriptor は declaration factory "
            "由来の exact value が必要"
        )
    if source_snapshot_sha256 is not None:
        raise BuildCacheError(
            "declaration descriptor と caller-supplied source snapshot SHA "
            "は同時指定できない"
        )
    if type(source_evidence) is not SourceEvidence:
        raise TypeError("source_evidence は resolve_evidence() 由来の exact value が必要")
    if type(admission) is not BuildAdmission:
        raise TypeError("admission は derive_build_admission() 由来の exact value が必要")
    descriptor = expected_materialization_descriptor
    declaration = descriptor.declaration
    if descriptor.ccbench_commit != ccbench_commit:
        raise BuildCacheError(
            "declaration descriptor の CCBench pin が build request と不一致"
        )
    try:
        expected_patch = (
            s8b_expected_materialization.template_patch_path_from_declaration(
                configuration=descriptor.configuration,
                declaration=declaration,
            )
        )
    except s8b_expected_materialization.ExpectedMaterializationError as exc:
        raise BuildCacheError(
            f"declaration descriptor を検証できない: {exc}"
        ) from exc
    if descriptor.template_patch_path != expected_patch:
        raise BuildCacheError(
            "declaration descriptor の template patch path が宣言と不一致"
        )
    if admission.as_cache_identity().get("input_sha256") != (
            descriptor.declaration_sha256):
        raise BuildCacheError(
            "declaration descriptor の freeze entry が build admission と不一致"
        )

    sub = ccbench_dir or _ccbench_dir()
    pending_publications: list[_PendingV2Publication] = []
    pending = None
    shared_base = fetchcontent_base_dir
    if not shared_base and post_oracle_dependency_binding is not None:
        shared_base = post_oracle_dependency_binding["fetchcontent_base_dir"]
    shared_directories = _descriptor_shared_directories(
        sub, cache_root, shared_base, cc=cc, cxx=cxx,
        source_dirs=_normalize_fetchcontent_source_dirs(
            masstree_source_dir=masstree_source_dir,
            mimalloc_source_dir=mimalloc_source_dir,
            googletest_source_dir=googletest_source_dir,
        ),
        dependency_prefix=dependency_prefix,
    )
    try:
        with s8b_expected_materialization.sealed_build_session(
                ccbench_commit=descriptor.ccbench_commit,
                configuration=descriptor.configuration,
                declaration=declaration,
                snapshot_root=sub,
                genome=genome,
                prepared_src_token=source_evidence.src_token,
                cxx=cxx,
                sort_oracle_contract_id=sort_oracle_contract_id,
                shared_directories=shared_directories,
        ) as admitted:
            if admitted.source_evidence != source_evidence:
                raise BuildCacheError(
                    "non-writable snapshot から再導出した SourceEvidence が "
                    "build request と不一致"
                )
            result = _build_v2_impl(
                genome,
                source_snapshot_sha256=admitted.source_snapshot_sha256,
                sealed_session=admitted,
                pending_publications=pending_publications,
                expected_materialization_sha256=admitted.expected_materialization_sha256,
                allow_external_compiler_inputs=True,
                expected_evolve_block_sources=(
                    dict(admitted.evolve_block_sources)
                    if admitted.evolve_block_sources else None
                ),
                **common,
            )
            if type(result) is _PendingV2Publication:
                pending = result
                result = pending.result
        kind = s8b_expected_materialization.SealedSnapshotProtectionKind
        capability = admitted.issue(
            kind.SEALED_CACHE_HIT if result.cached else kind.SEALED_BUILD,
            binary_sha256=result.bin_sha256,
            compiler_input_manifest_sha256=result.compiler_input_manifest_sha256,
        )
        if pending is not None:
            result = pending.publish(capability)
        return replace(
            result,
            source_snapshot_sha256=admitted.source_snapshot_sha256,
            expected_materialization_sha256=admitted.expected_materialization_sha256,
            source_protection=capability,
        )
    except s8b_expected_materialization.ExpectedMaterializationError as exc:
        raise BuildCacheError(
            "S8b build source snapshot を宣言へ束縛できない: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    finally:
        for owned in pending_publications:
            owned.close()


def build(genome: Genome, ccbench_commit: str, trace: bool,
          cache_root: str = "", cc: str = DEFAULT_CC, cxx: str = DEFAULT_CXX,
          jobs: Optional[int] = None, ccbench_dir: str = "",
          src_token: Optional[str] = None, *, admission: BuildAdmission,
          build_context: BuildRunContext, source_evidence: SourceEvidence,
          site: Optional[str] = None,
          backoff_grammar_version: Optional[int] = None,
          sort_oracle_contract_id: Optional[str] = None) -> BuildResult:
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
                            backoff_grammar_version=backoff_grammar_version,
                            sort_oracle_contract_id=sort_oracle_contract_id,
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
                backoff_grammar_version=backoff_grammar_version,
                sort_oracle_contract_id=sort_oracle_contract_id,
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
        expected: SourceEvidence, bdir: str, built_fresh: bool, *,
        backoff_grammar_version: Optional[int] = None,
        sort_oracle_contract_id: Optional[str] = None,
) -> None:
    """build 出口で current SourceEvidence 全体を exact 再照合する。

    再計算は resolve_evidence の単一窓口 —
    tree が動いて allowlist 外改変が入ったケースも同時に捕える。数十 ms で規律4 に反しない
    (phase3.md タスク定義)。新規ビルドの不一致は汚染バイナリの永続を防ぐため build dir を
    破棄する。cache hit の不一致は既存 (過去の正当な) 成果物なので破棄せず停止のみ。"""
    try:
        source_options = {}
        if backoff_grammar_version is not None:
            source_options["backoff_grammar_version"] = (
                backoff_grammar_version
            )
        if sort_oracle_contract_id is not None:
            source_options["sort_oracle_contract_id"] = (
                sort_oracle_contract_id
            )
        actual = source_digest.resolve_evidence(
            genome, ccbench_commit, ccbench_dir=sub, cxx=cxx,
            **source_options,
        )
    except RuntimeError:
        # resolve 自体の失敗 (TOCTOU 汚染 / git・g++ の transient 障害を区別できない)。
        # identity 不明のバイナリは共有キャッシュに残さない (偽 hit 防止 > 再ビルドコスト) —
        # cache_key で次 run が再ビルドするので D25 の再評価可能性は保たれる (transient でも
        # 消すのは意図的な非対称)。破棄の成否まで確認する (下の _discard)。
        if built_fresh:
            _discard_build_dir(bdir)
        raise
    if (actual != expected
            or actual.proof_source_snapshot != expected.proof_source_snapshot
            or actual.verification_variant != expected.verification_variant):
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
        sealed_session: Optional[s8b_expected_materialization.SealedBuildSession] = None,
        build_output: Optional[str] = None,
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
    if sealed_session is None:
        r = subprocess.run(cmd, **run_kwargs)
    else:
        if type(sealed_session) is not s8b_expected_materialization.SealedBuildSession:
            raise BuildCacheError("compiler execution requires an exact sealed session")
        r = sealed_session.run(
            cmd, cwd=os.getcwd(), env=os.environ.copy() if env is None else env,
            timeout_s=timeout_s,
            **({"build_output": build_output} if build_output is not None else {}),
        )
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
