#!/usr/bin/env python3
"""監査済み dev-wave tip を local main へ一度だけ fast-forward する。

この helper は協調する dev-wave manager 間の事故防止用であり、同一 UID の
非協調 writer や悪意ある Git admin 改変に対する sandbox ではない。caller が渡す
tested SHA / audited commit 列を受入証明とはみなさず、観測後の stale/race を防ぐ
operation guard として exact に再検査する。
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as _datetime
import fcntl
import hashlib
import importlib.util
import io
import json
import os
import random
import re
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import xml.etree.ElementTree as _ET
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.dev_waves.git_state import (  # noqa: E402
    FOLD_AUTHOR_IDENTITY,
    FOLD_COMMIT_MESSAGE,
    GIT_HARDENING_CONFIG,
    supervised_spool_wave_slug,
    verify_declared_fold_commit,
)
from tools import wave_land_window as _wave_land_window  # noqa: E402


RC_OK = 0
RC_STALE_MAIN = 10
RC_LOCK_BUSY = 11
RC_DIRT = 20
RC_CONTROL_PLANE = 21
RC_IDENTITY = 22
RC_AUDIT = 23
RC_NOT_LANDED = 24
RC_LANDED_POSTCONDITION_FAILED = 25
RC_FOLD_FAILED = 26
RC_FOLD_RECOVERY_FAILED = 27
RC_FOLD_ROLLBACK_FAILED = 28
RC_PROVENANCE = 29
RC_FOLD_FINALIZE_FAILED = 30
RC_FOLD_GATE = 31

_GIT_EXE = "/usr/bin/git"
_LOCK_NAME = b"dev-wave-land.lock"
_LAND_LOCK_WAIT_SECONDS = 180.0
_LAND_TURN_WAIT_SECONDS = 3600.0
_LAND_TURN_DIRECTORY = b"dev-wave-land-turn"
_LAND_TURN_REGISTRY_WAIT_SECONDS = 10.0
_LAND_TURN_MAX_BYTES = 4 * 1024 * 1024
_LAND_LOCK_INITIAL_POLL_SECONDS = 0.05
_LAND_LOCK_MAX_POLL_SECONDS = 1.0
_LAND_LOCK_RANDOM = random.SystemRandom()
_MAX_METADATA_BYTES = 16 * 1024
_MAX_ACCEPTANCE_RECEIPT_BYTES = 64 * 1024
# 最大 receipt 由来 nodeid と最長の成功 envelope を 64 KiB 通知へ同居させる。
_MAX_FORWARD_MAIN_MERGES = 8
_PROVENANCE_VIOLATION_RC = 1
_SHA_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_HOLDER_RE = re.compile(r"[0-9a-f]{12}\Z")
_MERGE_AFFECTING_CONFIG_KEYS = frozenset({
    b"core.attributesfile",
    b"diff.algorithm",
    b"diff.renamelimit",
    b"diff.renames",
    b"merge.autostash",
    b"merge.directoryrenames",
    b"merge.renamelimit",
    b"merge.renames",
    b"merge.renormalize",
    b"merge.verifysignatures",
})
_BRANCH_CONFIG_PREFIX = b"branch."
_BRANCH_MERGE_OPTIONS_SUFFIX = b".mergeoptions"
_MERGE_DRIVER_CONFIG_PREFIX = b"merge."
_MERGE_DRIVER_CONFIG_SUFFIXES = (b".driver", b".recursive")
_ACCEPTANCE_RECEIPT_SCHEMA = "dev-wave-acceptance-receipt/v5"
_ACCEPTANCE_AUTHORITY_KINDS = {
    "tested-main": "dev-wave-acceptance-launcher",
    "tested-tip-bootstrap": "dev-wave-acceptance-launcher-bootstrap-tip",
}
_ACCEPTANCE_LAUNCHER_PATH = "tools/acceptance_launcher.py"
_ACCEPTED_EFFECTIVE_SCHEDULERS = frozenset({"loadgroup", "serial"})
_RECEIPT_TEMP_PREFIX = ".dev-wave-acceptance-receipt-"
_ACCEPTANCE_RECEIPT_FIELDS = frozenset({
    "schema_version",
    "authority_kind",
    "acceptance_wave",
    "lease_holder",
    "tested_main",
    "tested_tip",
    "argv",
    "resolved_runner_path",
    "child_rc",
    "pre_fingerprint",
    "post_fingerprint",
    "waiter_blob_sha",
    "launcher_source_revision",
    "launcher_blob_sha",
    "launcher_executed_sha256",
    "waiter_executed_sha256",
    "runner_executed_sha256",
    "env_projection",
    "effective_scheduler",
    "verdict",
    "log_sha256",
    "checker_rc",
    "checker_status",
    "checker_blob_sha",
    "checker_receipt_sha256",
    "red_nodeids",
    "flake_nodeids",
})
_FINGERPRINT_FIELDS = frozenset({
    "digest",
    "head_sha",
    "status_bytes",
    "diff_bytes",
    "submodule_status_bytes",
})
_ENV_PROJECTION_FIELDS = frozenset({
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "IZANAGI_TASK_RUN_ID",
    "IZANAGI_TASK_RUNS_ROOT",
})
_SAFE_ADMIN_RE = re.compile(rb"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SAFE_CHILD_RE = re.compile(rb"(?!\.{1,2}\Z)[^/\x00]{1,128}\Z")
_CONTROL_CONTAINERS = (b".claude/worktrees", b".codex/worktrees")
_FOLD_LEDGERS = ("worklog", "decisions", "failures")
_FOLD_STATE_NAME = "izanagi-spool-fold-state.json"
_FOLD_MESSAGE = FOLD_COMMIT_MESSAGE.decode("ascii")
_FOLD_GATE_OUTCOME = "covered-families-passed"
_FOLD_GATE_ENV_REMOVE = frozenset({
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONOPTIMIZE",
    "PYTHONNOUSERSITE",
})
# この host の pytest 実体は user site にあり、user site を閉じると
# `ModuleNotFoundError: No module named 'pytest'` になるため、実子では閉じない。
_FOLD_GATE_ENV_FORCE = (
    ("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
)
_FOLD_GATE_DIAGNOSTIC_TAIL_BYTES = 500
# 母集合は fold gate registry の selected node + landing tip の全 tracked export。
# 5 node 時の login node 混雑下・dispatch 経由の同一隔離 tree/serial 実測 max 63.10 秒を 2.0 倍し 5 秒へ切上げ。
_FOLD_GATE_INNER_TIMEOUT_SECONDS = 130.0
_FOLD_GATE_TERMINATION_GRACE_SECONDS = 10.0
_FOLD_GATE_OUTER_TIMEOUT_SECONDS = 145.0
_SUPERVISED_WAVE_REF_RE = re.compile(
    r"refs/heads/dev-wave/(?P<run>dw-[0-9a-f]{32})/w(?P<wave>[0-9]{3,})\Z"
)
_GIT_CONFIG = (
    *GIT_HARDENING_CONFIG,
    "-c", "merge.autoStash=false",
    "-c", "rebase.autoStash=false",
    "-c", "merge.verifySignatures=false",
    "-c", "fetch.writeCommitGraph=false",
    "-c", "submodule.recurse=false",
    "-c", "protocol.file.allow=never",
)


@dataclass(frozen=True)
class LandRequest:
    main_worktree: Path
    wave_worktree: Path
    tested_main_sha: str
    tested_wave_tip_sha: str
    audited_commits: tuple[str, ...]
    acceptance_wave: str
    acceptance_receipt: Path
    landing_wave_tip_sha: str | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class LandResult:
    rc: int
    status: str
    reason: str
    main_before: str | None = None
    main_after: str | None = None
    wave_tip: str | None = None
    fold_commit_sha: str | None = None
    acceptance_receipt_sha256: str | None = None
    acceptance_verdict: str | None = None
    acceptance_red_nodeids: tuple[str, ...] | None = None
    acceptance_flake_nodeids: tuple[str, ...] | None = field(
        default=None,
        kw_only=True,
    )
    # 観測時間は判定の同一性に含めず、JSON で別途報告する。
    waited_s: float | None = field(default=None, kw_only=True, compare=False)
    window_elapsed_s: float | None = field(default=None, kw_only=True, compare=False)
    tested_tip_sha: str | None = field(default=None, kw_only=True)
    landing_tip_sha: str | None = field(default=None, kw_only=True)
    incorporated_main_shas: tuple[str, ...] = field(default=(), kw_only=True)
    fold_gate_uncovered_families: tuple[str, ...] | None = field(
        default=None,
        kw_only=True,
    )
    fold_gate_covered_and_failed_families: tuple[str, ...] | None = field(
        default=None,
        kw_only=True,
    )
    release_safe: bool = field(default=False, compare=False)
    retryable_same_request: bool = field(default=False, compare=False)

    def as_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "reason": self.reason,
            "main_before": self.main_before,
            "main_after": self.main_after,
            "wave_tip": self.wave_tip,
            "fold_commit_sha": self.fold_commit_sha,
            "acceptance_receipt_sha256": self.acceptance_receipt_sha256,
            "acceptance_verdict": self.acceptance_verdict,
            "acceptance_red_nodeids": (
                None
                if self.acceptance_red_nodeids is None
                else list(self.acceptance_red_nodeids)
            ),
            "acceptance_flake_nodeids": (
                None
                if self.acceptance_flake_nodeids is None
                else list(self.acceptance_flake_nodeids)
            ),
            "tested_tip_sha": self.tested_tip_sha,
            "landing_tip_sha": self.landing_tip_sha,
            "incorporated_main_shas": list(self.incorporated_main_shas),
            "release_safe": self.release_safe,
            "retryable_same_request": self.retryable_same_request,
        }
        if self.waited_s is not None:
            payload["waited_s"] = self.waited_s
            payload["window_elapsed_s"] = self.window_elapsed_s
        if self.fold_gate_uncovered_families is not None:
            payload["fold_gate_uncovered_families"] = list(
                self.fold_gate_uncovered_families
            )
        if self.fold_gate_covered_and_failed_families is not None:
            payload["fold_gate_covered_and_failed_families"] = list(
                self.fold_gate_covered_and_failed_families
            )
        return payload


class _Reject(Exception):
    def __init__(
        self,
        rc: int,
        reason: str,
        *,
        release_safe: bool = False,
        retryable_same_request: bool = False,
    ):
        super().__init__(reason)
        self.rc = rc
        self.reason = reason
        self.release_safe = release_safe
        self.retryable_same_request = retryable_same_request


@dataclass
class _LandLockHandle:
    fd: int = -1

    def close(self) -> None:
        if self.fd >= 0:
            fd = self.fd
            try:
                os.close(fd)
            finally:
                self.fd = -1


@dataclass
class _LandTurnHandle:
    started: float
    deadline: float
    directory_fd: int = -1
    registry_fd: int = -1
    fd: int = -1
    key: str = ""
    seq: int = 0
    ticket: str = ""
    waited_s: float = 0.0
    record: dict = field(default_factory=dict)
    terminal: bool = False

    def close(self) -> None:
        for name in ("fd", "registry_fd", "directory_fd"):
            fd = getattr(self, name)
            if fd >= 0:
                setattr(self, name, -1)
                os.close(fd)


@dataclass
class _Repository:
    main: Path
    wave: Path
    common: Path
    main_fd: int
    wave_fd: int
    common_fd: int
    turn: _LandTurnHandle | None = None
    land_lock: _LandLockHandle | None = None

    def close(self) -> None:
        for fd in (self.common_fd, self.wave_fd, self.main_fd):
            try:
                os.close(fd)
            except OSError:
                pass


@dataclass(frozen=True)
class _GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class _ControlSnapshot:
    handoffs: frozenset[bytes]
    worktree_prefixes: tuple[bytes, ...]
    identities: tuple[tuple[bytes, tuple[object, ...]], ...]
    observed_worktree_identities: tuple[
        tuple[bytes, tuple[object, ...]], ...
    ] = field(default=(), compare=False, repr=False)
    worktree_targets: tuple[bytes, ...] = field(
        default=(), compare=False, repr=False
    )


@dataclass(frozen=True)
class _PathSnapshot:
    relative: str
    existed: bool
    content: bytes
    mode: int


@dataclass(frozen=True)
class _ProvenanceReceipt:
    tip_sha: str
    checker_blob_sha: str
    executed_bytes_sha: str
    returncode: int


@dataclass(frozen=True)
class _FoldGateBudgets:
    inner_seconds: float
    termination_grace_seconds: float
    outer_seconds: float


@dataclass(frozen=True)
class _FoldGateSelection:
    registry_digest: str
    nodeids: tuple[str, ...]
    target_families: tuple[str, ...]
    uncovered_families: tuple[str, ...]
    node_families: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True)
class _FoldGateJUnitCounts:
    collected: int
    executed: int
    skipped: int
    failed: int
    errors: int


@dataclass(frozen=True)
class _FoldGateReceipt:
    plan: object = field(repr=False, compare=False)
    transaction_id: str
    registry_digest: str
    nodeids: tuple[str, ...]
    target_raw_digests: tuple[tuple[str, str], ...]
    outcome: str
    uncovered_families: tuple[str, ...]


class _FoldGateFailure(RuntimeError):
    """main mutation 前に fold gate が fail-closed で拒否した。"""

    def __init__(
        self,
        reason: str,
        *,
        retryable_same_request: bool = False,
        uncovered_families: tuple[str, ...] = (),
        covered_and_failed_families: tuple[str, ...] = (),
    ):
        super().__init__(reason)
        self.retryable_same_request = retryable_same_request
        self.uncovered_families = uncovered_families
        self.covered_and_failed_families = covered_and_failed_families


class _FoldGateInfrastructureFailure(_FoldGateFailure):
    """一時的な gate infrastructure failure。"""

    def __init__(
        self,
        reason: str,
        *,
        uncovered_families: tuple[str, ...] = (),
    ):
        super().__init__(
            reason,
            retryable_same_request=True,
            uncovered_families=uncovered_families,
        )


@dataclass(frozen=True)
class _AcceptanceVerification:
    receipt_sha256: str
    verdict: str
    red_nodeids: tuple[str, ...]
    flake_nodeids: tuple[str, ...]
    bootstrap: bool = False


@dataclass
class _ProvenanceCheckerBinding:
    path: Path
    tools_fd: int
    checker_fd: int

    def bytes_sha256(self) -> str:
        """束縛済み inode の現在 bytes を同じ FD から読む。"""

        digest = hashlib.sha256()
        offset = 0
        try:
            while True:
                chunk = os.pread(self.checker_fd, 1024 * 1024, offset)
                if not chunk:
                    return digest.hexdigest()
                digest.update(chunk)
                offset += len(chunk)
        except OSError as exc:
            raise _Reject(
                RC_PROVENANCE,
                f"provenance checker bound bytes read failed ({exc})",
            ) from exc

    def verify(self, repository: _Repository) -> None:
        try:
            wave = repository.wave.stat(follow_symlinks=False)
            tools = os.stat(
                b"tools",
                dir_fd=repository.wave_fd,
                follow_symlinks=False,
            )
            checker = os.stat(
                b"check_ai_provenance.py",
                dir_fd=self.tools_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise _Reject(
                RC_PROVENANCE,
                f"provenance checker binding changed ({exc})",
            ) from exc
        if (
            not _same_inode(os.fstat(repository.wave_fd), wave)
            or not _same_inode(os.fstat(self.tools_fd), tools)
            or not _same_inode(os.fstat(self.checker_fd), checker)
        ):
            raise _Reject(
                RC_PROVENANCE,
                "provenance checker path changed during the audit",
            )

    def close(self) -> None:
        """両 FD を独立に閉じる。二重呼出しは no-op。"""

        try:
            if self.checker_fd >= 0:
                checker_fd = self.checker_fd
                try:
                    os.close(checker_fd)
                finally:
                    self.checker_fd = -1
        finally:
            if self.tools_fd >= 0:
                tools_fd = self.tools_fd
                try:
                    os.close(tools_fd)
                finally:
                    self.tools_fd = -1


@dataclass(frozen=True)
class _LandFingerprint:
    main_head: str
    wave_head: str
    collision_paths: frozenset[tuple[str, bytes]]


@dataclass(frozen=True)
class _ForwardMainMerge:
    commit_sha: str
    first_parent_sha: str
    incorporated_main_sha: str
    prior_main_sha: str
    tree_sha: str


@dataclass(frozen=True)
class _LockedPreflight:
    fold: object
    active_plan: object | None
    control: _ControlSnapshot
    audited: tuple[str, ...]
    base_gitlinks: dict[bytes, str]
    target_gitlinks: dict[bytes, str]
    target_normal_entries: frozenset[bytes]
    gitlinks_changed: bool
    locked_main: str
    wave_ref: str
    fingerprint: _LandFingerprint
    forward_main_merges: tuple[_ForwardMainMerge, ...]
    fold_trusted_main_cutoff: str
    landed_commits: tuple[str, ...]


def _git_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C",
    })
    return env


def _config_inspection_env() -> dict[str, str]:
    """親 merge と同じ config origin を読むため Git override だけを除く。"""

    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
    })
    return env


def _git(repo: Path, *args: str, pass_fds: tuple[int, ...] = ()) -> _GitResult:
    try:
        completed = subprocess.run(
            [_GIT_EXE, *_GIT_CONFIG, "-C", str(repo), *args],
            env=_git_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            close_fds=True,
            pass_fds=pass_fds,
        )
    except OSError as exc:
        return _GitResult(127, b"", str(exc).encode("utf-8", "replace"))
    return _GitResult(completed.returncode, completed.stdout, completed.stderr)


def _git_config_names(repo: Path) -> _GitResult:
    """system/global/local/worktree の effective key 名を include 込みで返す。"""

    try:
        completed = subprocess.run(
            [
                _GIT_EXE,
                "-C",
                str(repo),
                "config",
                "--includes",
                "--null",
                "--name-only",
                "--list",
            ],
            env=_config_inspection_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            close_fds=True,
        )
    except OSError as exc:
        return _GitResult(127, b"", str(exc).encode("utf-8", "replace"))
    return _GitResult(completed.returncode, completed.stdout, completed.stderr)


def _detail(data: bytes) -> str:
    return data.decode("utf-8", "backslashreplace").strip().replace("\n", " ")[:500]


def _require_git(result: _GitResult, label: str, rc: int = RC_AUDIT) -> bytes:
    if result.returncode != 0:
        raise _Reject(
            rc,
            f"{label}: git failed ({_detail(result.stderr) or 'no detail'})",
            retryable_same_request=True,
        )
    return result.stdout


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        stat.S_IFMT(left.st_mode),
    ) == (
        right.st_dev,
        right.st_ino,
        stat.S_IFMT(right.st_mode),
    )


def _identity(metadata: os.stat_result) -> tuple[int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
    )


def _open_dir(path: Path, label: str, *, rc: int = RC_IDENTITY) -> int:
    raw = os.fsencode(path)
    try:
        before = os.lstat(raw)
        fd = os.open(raw, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        after = os.fstat(fd)
    except OSError as exc:
        raise _Reject(
            rc,
            f"{label}: directory open failed ({exc})",
            retryable_same_request=True,
        ) from exc
    if not stat.S_ISDIR(after.st_mode) or not _same_inode(before, after):
        os.close(fd)
        raise _Reject(rc, f"{label}: symlink/race/non-directory")
    return fd


def _openat_dir(parent_fd: int, name: bytes, label: str, *, rc: int) -> int:
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        fd = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
        after = os.fstat(fd)
    except OSError as exc:
        raise _Reject(
            rc,
            f"{label}: directory open failed ({exc})",
            retryable_same_request=True,
        ) from exc
    if not stat.S_ISDIR(after.st_mode) or not _same_inode(before, after):
        os.close(fd)
        raise _Reject(rc, f"{label}: symlink/race/non-directory")
    return fd


def _read_regular_at(
    parent_fd: int,
    name: bytes,
    label: str,
    *,
    rc: int,
    limit: int = _MAX_METADATA_BYTES,
) -> tuple[bytes, os.stat_result]:
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        fd = os.open(
            name,
            os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise _Reject(
            rc,
            f"{label}: regular file open failed ({exc})",
            retryable_same_request=True,
        ) from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or not _same_inode(before, opened):
            raise _Reject(rc, f"{label}: symlink/race/non-regular")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise _Reject(rc, f"{label}: file exceeds {limit} bytes")
        after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        final = os.fstat(fd)
        if not _same_inode(opened, after) or not _same_inode(opened, final):
            raise _Reject(rc, f"{label}: inode changed while reading")
        return b"".join(chunks), opened
    except OSError as exc:
        raise _Reject(
            rc,
            f"{label}: regular file read/stat failed ({exc})",
            retryable_same_request=True,
        ) from exc
    finally:
        os.close(fd)


def _no_duplicate_json_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def _acceptance_rejected(*, retryable_same_request: bool = False) -> _Reject:
    return _Reject(
        RC_AUDIT,
        "acceptance-receipt-rejected",
        retryable_same_request=retryable_same_request,
    )


def _read_acceptance_receipt(path: Path) -> bytes:
    try:
        if not path.is_absolute() or path.name.startswith(_RECEIPT_TEMP_PREFIX):
            raise ValueError("receipt path must be absolute")
        parent_fd = _open_dir(path.parent, "acceptance receipt parent")
        try:
            raw, _ = _read_regular_at(
                parent_fd,
                os.fsencode(path.name),
                "acceptance receipt",
                rc=RC_AUDIT,
                limit=_MAX_ACCEPTANCE_RECEIPT_BYTES,
            )
        finally:
            os.close(parent_fd)
        return raw
    except _Reject as exc:
        retryable = exc.retryable_same_request or isinstance(exc.__cause__, OSError)
        raise _acceptance_rejected(retryable_same_request=retryable) from None
    except OSError:
        raise _acceptance_rejected(retryable_same_request=True) from None
    except (UnicodeError, ValueError, TypeError):
        raise _acceptance_rejected() from None


def _receipt_object(raw: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicate_json_keys,
        )
    except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError):
        raise _acceptance_rejected() from None
    if not isinstance(value, dict) or set(value) != _ACCEPTANCE_RECEIPT_FIELDS:
        raise _acceptance_rejected()
    return value


def _release_authority_digest(path: Path, acceptance_wave: str) -> str:
    raw = _read_acceptance_receipt(path)
    receipt = _receipt_object(raw)
    try:
        expected_holder = hashlib.sha256(
            acceptance_wave.encode("utf-8")
        ).hexdigest()[:12]
    except UnicodeError:
        raise _acceptance_rejected() from None
    if (
        receipt.get("acceptance_wave") != acceptance_wave
        or receipt.get("lease_holder") != expected_holder
    ):
        raise _acceptance_rejected()
    return hashlib.sha256(raw).hexdigest()


def _valid_fingerprint(value: object, tested_tip: str) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == _FINGERPRINT_FIELDS
        and isinstance(value.get("digest"), str)
        and _SHA256_RE.fullmatch(value["digest"]) is not None
        and value.get("head_sha") == tested_tip
        and type(value.get("status_bytes")) is int
        and value["status_bytes"] == 0
        and type(value.get("diff_bytes")) is int
        and value["diff_bytes"] == 0
        and type(value.get("submodule_status_bytes")) is int
        and value["submodule_status_bytes"] >= 0
    )


def _runner_tree_entry(
    repository: _Repository,
    revision: str,
) -> tuple[str, str] | None:
    result = _git(
        repository.wave,
        "ls-tree",
        "-z",
        "--full-tree",
        revision,
        "--",
        "tools/run_tests.py",
    )
    if result.returncode != 0:
        raise _acceptance_rejected(retryable_same_request=True)
    if result.stdout == b"":
        return None
    match = re.fullmatch(
        rb"[0-7]{6} ([a-z]+) "
        rb"((?:[0-9a-f]{40}|[0-9a-f]{64}))\ttools/run_tests\.py\x00",
        result.stdout,
    )
    if match is None:
        raise _acceptance_rejected()
    try:
        return match.group(1).decode("ascii"), match.group(2).decode("ascii")
    except UnicodeError:
        raise _acceptance_rejected() from None


def _verify_forward_main_runner_blob(
    repository: _Repository,
    tested_main: str,
    forward_main_merges: Sequence[_ForwardMainMerge],
) -> None:
    """D987: final incorporated main must retain the tested-main runner blob."""

    if not forward_main_merges:
        return
    final_main_entry = _runner_tree_entry(
        repository,
        forward_main_merges[-1].incorporated_main_sha,
    )
    tested_main_entry = _runner_tree_entry(repository, tested_main)
    if (
        final_main_entry is None
        or tested_main_entry is None
        or final_main_entry[0] != "blob"
        or tested_main_entry[0] != "blob"
        or _SHA_RE.fullmatch(final_main_entry[1]) is None
        or _SHA_RE.fullmatch(tested_main_entry[1]) is None
        or final_main_entry[1] != tested_main_entry[1]
    ):
        raise _acceptance_rejected()


def _acceptance_tree_entry(
    repository: _Repository,
    revision: str,
    path: str,
) -> tuple[str, str, str] | None:
    result = _git(
        repository.wave,
        "ls-tree",
        "-z",
        "--full-tree",
        revision,
        "--",
        path,
    )
    if result.returncode != 0:
        raise _acceptance_rejected(retryable_same_request=True)
    if not result.stdout:
        return None
    try:
        header, separator, returned_path = result.stdout.partition(b"\t")
        fields = header.split(b" ")
        expected_path = path.encode("utf-8") + b"\0"
        if (
            separator != b"\t"
            or returned_path != expected_path
            or len(fields) != 3
        ):
            raise ValueError("malformed ls-tree output")
        mode, object_type, object_id = (
            field.decode("ascii") for field in fields
        )
    except (UnicodeError, ValueError):
        raise _acceptance_rejected() from None
    if _SHA_RE.fullmatch(object_id) is None:
        raise _acceptance_rejected()
    return mode, object_type, object_id


def _regular_blob_entry(entry: tuple[str, str, str] | None) -> bool:
    return (
        entry is not None
        and entry[0] in {"100644", "100755"}
        and entry[1] == "blob"
        and _SHA1_RE.fullmatch(entry[2]) is not None
    )


def _acceptance_blob_content_sha256(
    repository: _Repository,
    object_id: str,
) -> str:
    result = _git(repository.wave, "cat-file", "blob", object_id)
    if result.returncode != 0:
        raise _acceptance_rejected(retryable_same_request=True)
    return hashlib.sha256(result.stdout).hexdigest()


def _verify_acceptance_static(
    repository: _Repository,
    *,
    raw: bytes,
    acceptance_wave: str,
    tested_main: str,
    tested_tip: str,
) -> _AcceptanceVerification:
    receipt = _receipt_object(raw)
    try:
        expected_holder = hashlib.sha256(
            acceptance_wave.encode("utf-8")
        ).hexdigest()[:12]
    except UnicodeError:
        raise _acceptance_rejected() from None
    pre = receipt.get("pre_fingerprint")
    post = receipt.get("post_fingerprint")
    env_projection = receipt.get("env_projection")
    argv = receipt.get("argv")
    verdict = receipt.get("verdict")
    red_nodeids = receipt.get("red_nodeids")
    flake_nodeids = receipt.get("flake_nodeids")
    effective_scheduler = receipt.get("effective_scheduler")
    launcher_source_revision = receipt.get("launcher_source_revision")
    if not (
        receipt.get("schema_version") == _ACCEPTANCE_RECEIPT_SCHEMA
        and isinstance(launcher_source_revision, str)
        and launcher_source_revision in _ACCEPTANCE_AUTHORITY_KINDS
        and receipt.get("authority_kind")
        == _ACCEPTANCE_AUTHORITY_KINDS[launcher_source_revision]
        and isinstance(receipt.get("launcher_blob_sha"), str)
        and _SHA1_RE.fullmatch(receipt["launcher_blob_sha"]) is not None
        and isinstance(receipt.get("launcher_executed_sha256"), str)
        and _SHA256_RE.fullmatch(
            receipt["launcher_executed_sha256"]
        ) is not None
        and isinstance(receipt.get("waiter_executed_sha256"), str)
        and _SHA256_RE.fullmatch(
            receipt["waiter_executed_sha256"]
        ) is not None
        and isinstance(receipt.get("runner_executed_sha256"), str)
        and _SHA256_RE.fullmatch(
            receipt["runner_executed_sha256"]
        ) is not None
        and receipt.get("acceptance_wave") == acceptance_wave
        and isinstance(receipt.get("lease_holder"), str)
        and _HOLDER_RE.fullmatch(receipt["lease_holder"]) is not None
        and receipt["lease_holder"] == expected_holder
        and receipt.get("tested_main") == tested_main
        and receipt.get("tested_tip") == tested_tip
        and argv == ["python3", "tools/run_tests.py"]
        and receipt.get("resolved_runner_path") == "tools/run_tests.py"
        and type(receipt.get("child_rc")) is int
        and isinstance(receipt.get("log_sha256"), str)
        and _SHA256_RE.fullmatch(receipt["log_sha256"]) is not None
        and _valid_fingerprint(pre, tested_tip)
        and post == pre
        and isinstance(env_projection, dict)
        and set(env_projection) == _ENV_PROJECTION_FIELDS
        and all(
            value is None or isinstance(value, str)
            for value in env_projection.values()
        )
        and not env_projection["PYTEST_ADDOPTS"]
        and not env_projection["PYTEST_PLUGINS"]
        and isinstance(effective_scheduler, str)
        and effective_scheduler in _ACCEPTED_EFFECTIVE_SCHEDULERS
    ):
        raise _acceptance_rejected()
    if verdict == "child-green":
        if not (
            receipt["child_rc"] == 0
            and receipt.get("checker_rc") is None
            and receipt.get("checker_status") is None
            and receipt.get("checker_blob_sha") is None
            and receipt.get("checker_receipt_sha256") is None
            and red_nodeids == []
            and flake_nodeids == []
        ):
            raise _acceptance_rejected()
        accepted_red_nodeids: tuple[str, ...] = ()
        accepted_flake_nodeids: tuple[str, ...] = ()
    elif verdict == "non-attributable-only":
        if not (
            receipt["child_rc"] == 1
            and type(receipt.get("checker_rc")) is int
            and receipt["checker_rc"] == 0
            and receipt.get("checker_status") == "non-attributable-only"
            and isinstance(receipt.get("checker_blob_sha"), str)
            and _SHA_RE.fullmatch(receipt["checker_blob_sha"]) is not None
            and isinstance(receipt.get("checker_receipt_sha256"), str)
            and _SHA256_RE.fullmatch(
                receipt["checker_receipt_sha256"]
            ) is not None
            and isinstance(red_nodeids, list)
            and isinstance(flake_nodeids, list)
            and (red_nodeids or flake_nodeids)
            and all(isinstance(nodeid, str) and nodeid for nodeid in red_nodeids)
            and all(
                isinstance(nodeid, str) and nodeid
                for nodeid in flake_nodeids
            )
            and red_nodeids == sorted(set(red_nodeids))
            and flake_nodeids == sorted(set(flake_nodeids))
            and set(red_nodeids).isdisjoint(flake_nodeids)
        ):
            raise _acceptance_rejected()
        accepted_red_nodeids = tuple(red_nodeids)
        accepted_flake_nodeids = tuple(flake_nodeids)
    else:
        raise _acceptance_rejected()
    # Fixed tested objects must be verified before a turn can be registered.
    tip_runner_entry = _runner_tree_entry(repository, tested_tip)
    main_runner_entry = _runner_tree_entry(repository, tested_main)
    if (
        tip_runner_entry is None
        or main_runner_entry is None
        or main_runner_entry[0] != "blob"
        or tip_runner_entry[0] != "blob"
        or _SHA_RE.fullmatch(main_runner_entry[1]) is None
        or _SHA_RE.fullmatch(tip_runner_entry[1]) is None
        or receipt.get("runner_executed_sha256")
        != _acceptance_blob_content_sha256(repository, main_runner_entry[1])
    ):
        raise _acceptance_rejected()
    main_launcher_entry = _acceptance_tree_entry(
        repository,
        tested_main,
        _ACCEPTANCE_LAUNCHER_PATH,
    )
    if launcher_source_revision == "tested-main":
        launcher_entry = main_launcher_entry
    else:
        if main_launcher_entry is not None:
            raise _acceptance_rejected()
        launcher_entry = _acceptance_tree_entry(
            repository,
            tested_tip,
            _ACCEPTANCE_LAUNCHER_PATH,
        )
    if not _regular_blob_entry(launcher_entry):
        raise _acceptance_rejected()
    assert launcher_entry is not None
    launcher_blob_sha = launcher_entry[2]
    if (
        receipt.get("launcher_blob_sha") != launcher_blob_sha
        or receipt.get("launcher_executed_sha256")
        != _acceptance_blob_content_sha256(repository, launcher_blob_sha)
    ):
        raise _acceptance_rejected()
    waiter_result = _git(
        repository.wave,
        "rev-parse",
        f"{tested_tip}:tools/dev_wave_wait.py",
    )
    if waiter_result.returncode != 0:
        raise _acceptance_rejected(retryable_same_request=True)
    try:
        waiter_blob = waiter_result.stdout.decode("ascii").strip()
    except UnicodeError:
        raise _acceptance_rejected() from None
    waiter_entry = _acceptance_tree_entry(
        repository, tested_tip, "tools/dev_wave_wait.py",
    )
    if (
        waiter_entry is None
        or waiter_entry[1] != "blob"
        or _SHA_RE.fullmatch(waiter_entry[2]) is None
        or receipt.get("waiter_executed_sha256")
        != _acceptance_blob_content_sha256(repository, waiter_entry[2])
    ):
        raise _acceptance_rejected()
    checker_blob = ""
    checker_result: _GitResult | None = None
    main_checker_blob = ""
    main_checker_result: _GitResult | None = None
    if verdict == "non-attributable-only":
        main_checker_result = _git(
            repository.wave,
            "rev-parse",
            f"{tested_main}:tools/check_acceptance_reds.py",
        )
        checker_result = _git(
            repository.wave,
            "rev-parse",
            f"{tested_tip}:tools/check_acceptance_reds.py",
        )
        if (
            main_checker_result.returncode != 0
            or checker_result.returncode != 0
        ):
            raise _acceptance_rejected(retryable_same_request=True)
        try:
            main_checker_blob = main_checker_result.stdout.decode("ascii").strip()
            checker_blob = checker_result.stdout.decode("ascii").strip()
        except UnicodeError:
            raise _acceptance_rejected() from None
    if (
        _SHA_RE.fullmatch(waiter_blob) is None
        or receipt.get("waiter_blob_sha") != waiter_blob
        or (
            verdict == "non-attributable-only"
            and (
                main_checker_result is None
                or _SHA_RE.fullmatch(main_checker_blob) is None
                or checker_result is None
                or _SHA_RE.fullmatch(checker_blob) is None
                or main_checker_blob != checker_blob
                or receipt.get("checker_blob_sha") != checker_blob
            )
        )
    ):
        raise _acceptance_rejected()
    return _AcceptanceVerification(
        receipt_sha256=hashlib.sha256(raw).hexdigest(),
        verdict=verdict,
        red_nodeids=accepted_red_nodeids,
        flake_nodeids=accepted_flake_nodeids,
        bootstrap=launcher_source_revision == "tested-tip-bootstrap",
    )


def _verify_acceptance_locked_authority(
    repository: _Repository,
    validated: _AcceptanceVerification,
    locked_main: str,
) -> None:
    if validated.bootstrap and _acceptance_tree_entry(
        repository, locked_main, _ACCEPTANCE_LAUNCHER_PATH,
    ) is not None:
        raise _acceptance_rejected()


def _verify_acceptance_receipt(
    repository: _Repository,
    *,
    receipt_path: Path,
    acceptance_wave: str,
    tested_main: str,
    tested_tip: str,
    locked_main: str,
) -> _AcceptanceVerification:
    raw = _read_acceptance_receipt(receipt_path)
    validated = _verify_acceptance_static(
        repository,
        raw=raw,
        acceptance_wave=acceptance_wave,
        tested_main=tested_main,
        tested_tip=tested_tip,
    )
    _verify_acceptance_locked_authority(
        repository, validated, locked_main,
    )
    return validated


def _with_acceptance_verification(
    result: LandResult,
    verification: _AcceptanceVerification,
) -> LandResult:
    return replace(
        result,
        acceptance_receipt_sha256=verification.receipt_sha256,
        acceptance_verdict=verification.verdict,
        acceptance_red_nodeids=verification.red_nodeids,
        acceptance_flake_nodeids=verification.flake_nodeids,
    )


def _canonical_absolute(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise _Reject(RC_IDENTITY, f"{label}: path must be absolute")
    raw = os.fsencode(path)
    if b"\0" in raw or b"\n" in raw or os.path.normpath(raw) != raw:
        raise _Reject(RC_IDENTITY, f"{label}: path is not canonical")
    try:
        resolved = Path(os.fsdecode(os.path.realpath(raw, strict=True)))
    except OSError as exc:
        raise _Reject(
            RC_IDENTITY,
            f"{label}: path resolution failed ({exc})",
            retryable_same_request=True,
        ) from exc
    if os.fsencode(resolved) != raw:
        raise _Reject(RC_IDENTITY, f"{label}: symlinked or aliased path is unsupported")
    return resolved


def _parse_gitdir_file(data: bytes, label: str) -> bytes:
    prefix = b"gitdir: "
    if not data.startswith(prefix) or not data.endswith(b"\n"):
        raise _Reject(RC_IDENTITY, f"{label}: malformed gitdir file")
    target = data[len(prefix):-1]
    if (
        not target.startswith(b"/")
        or b"\0" in target
        or b"\n" in target
        or os.path.normpath(target) != target
    ):
        raise _Reject(RC_IDENTITY, f"{label}: gitdir target must be canonical absolute bytes")
    return target


def _validate_admin_binding(
    *,
    child_fd: int,
    child_path: bytes,
    common_fd: int,
    common_path: bytes,
    label: str,
    rc: int,
) -> tuple[object, ...]:
    child_identity = _identity(os.fstat(child_fd))
    dotgit, dotgit_stat = _read_regular_at(
        child_fd, b".git", f"{label}/.git", rc=rc
    )
    admin_path = _parse_gitdir_file(dotgit, f"{label}/.git")
    expected_prefix = common_path + b"/worktrees/"
    if not admin_path.startswith(expected_prefix):
        raise _Reject(rc, f"{label}: gitdir is outside common worktrees registry")
    admin_name = admin_path[len(expected_prefix):]
    if not _SAFE_ADMIN_RE.fullmatch(admin_name) or b"/" in admin_name:
        raise _Reject(rc, f"{label}: unsafe or nested admin name")

    worktrees_fd = _openat_dir(
        common_fd, b"worktrees", "common/worktrees", rc=rc
    )
    try:
        admin_fd = _openat_dir(
            worktrees_fd, admin_name, f"common/worktrees/{admin_name!r}", rc=rc
        )
    finally:
        os.close(worktrees_fd)
    try:
        try:
            path_stat = os.stat(admin_path, follow_symlinks=False)
        except OSError as exc:
            raise _Reject(
                rc,
                f"{label}: admin path stat failed ({exc})",
                retryable_same_request=True,
            ) from exc
        if not _same_inode(path_stat, os.fstat(admin_fd)):
            raise _Reject(rc, f"{label}: admin pathname/inode mismatch")
        admin_identity = _identity(os.fstat(admin_fd))
        backpointer, backpointer_stat = _read_regular_at(
            admin_fd, b"gitdir", f"{label} admin gitdir", rc=rc
        )
        if backpointer != child_path + b"/.git\n":
            raise _Reject(rc, f"{label}: admin gitdir backpointer mismatch")
        commondir, commondir_stat = _read_regular_at(
            admin_fd, b"commondir", f"{label} admin commondir", rc=rc
        )
        if commondir != b"../..\n":
            raise _Reject(rc, f"{label}: unsupported common-dir metadata")
        return (
            child_identity,
            _identity(dotgit_stat),
            hashlib.sha256(dotgit).digest(),
            admin_identity,
            _identity(backpointer_stat),
            hashlib.sha256(backpointer).digest(),
            _identity(commondir_stat),
            hashlib.sha256(commondir).digest(),
        )
    finally:
        os.close(admin_fd)


def _verify_repository(request: LandRequest) -> _Repository:
    main = _canonical_absolute(request.main_worktree, "main worktree")
    wave = _canonical_absolute(request.wave_worktree, "wave worktree")
    if main == wave:
        raise _Reject(RC_IDENTITY, "main and wave worktrees must differ")
    main_fd = _open_dir(main, "main worktree")
    try:
        wave_fd = _open_dir(wave, "wave worktree")
    except Exception:
        os.close(main_fd)
        raise
    common_fd = -1
    try:
        cwd = os.stat(b".", follow_symlinks=False)
        if not _same_inode(cwd, os.fstat(wave_fd)):
            raise _Reject(RC_IDENTITY, "cwd must be the exact wave worktree")

        wave_dotgit, _ = _read_regular_at(
            wave_fd, b".git", "wave .git", rc=RC_IDENTITY
        )
        admin_path = _parse_gitdir_file(wave_dotgit, "wave .git")
        if not admin_path.endswith(b"/worktrees/" + admin_path.rsplit(b"/", 1)[-1]):
            raise _Reject(RC_IDENTITY, "wave admin path is not a direct registry child")
        common_path = admin_path.rsplit(b"/worktrees/", 1)[0]
        if common_path.rsplit(b"/", 1)[-1] != b".git":
            raise _Reject(RC_IDENTITY, "common git-dir is not primary .git")
        derived_main = common_path.rsplit(b"/", 1)[0]
        if derived_main != os.fsencode(main):
            raise _Reject(RC_IDENTITY, "main worktree does not own common git-dir")
        common = Path(os.fsdecode(common_path))
        common_fd = _open_dir(common, "common git-dir")
        main_git_fd = _openat_dir(
            main_fd, b".git", "primary main .git", rc=RC_IDENTITY
        )
        try:
            if not _same_inode(os.fstat(main_git_fd), os.fstat(common_fd)):
                raise _Reject(RC_IDENTITY, "primary .git/common git-dir inode mismatch")
        finally:
            os.close(main_git_fd)
        _validate_admin_binding(
            child_fd=wave_fd,
            child_path=os.fsencode(wave),
            common_fd=common_fd,
            common_path=common_path,
            label="wave worktree",
            rc=RC_IDENTITY,
        )
        return _Repository(main, wave, common, main_fd, wave_fd, common_fd)
    except Exception:
        if common_fd >= 0:
            os.close(common_fd)
        os.close(wave_fd)
        os.close(main_fd)
        raise


def _sha(value: str, label: str) -> str:
    if _SHA_RE.fullmatch(value) is None:
        raise _Reject(RC_AUDIT, f"{label}: full lowercase object id required")
    return value


def _decode_sha(data: bytes, label: str, rc: int = RC_AUDIT) -> str:
    try:
        value = data.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise _Reject(rc, f"{label}: non-ASCII object id") from exc
    if _SHA_RE.fullmatch(value) is None:
        raise _Reject(rc, f"{label}: unexpected object id {value!r}")
    return value


def _head(repo: Path, label: str) -> str:
    return _decode_sha(
        _require_git(
            _git(repo, "rev-parse", "--verify", "HEAD"),
            f"{label} HEAD",
            RC_IDENTITY,
        ),
        f"{label} HEAD",
        RC_IDENTITY,
    )


def _symbolic_head(repo: Path, label: str) -> str:
    raw = _require_git(
        _git(repo, "symbolic-ref", "--quiet", "HEAD"),
        f"{label} symbolic HEAD",
        RC_IDENTITY,
    )
    try:
        ref = raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise _Reject(RC_IDENTITY, f"{label}: non-ASCII branch ref") from exc
    if (
        not ref.startswith("refs/heads/")
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in ref)
        or ".." in ref
        or "@{" in ref
        or ref.endswith(("/", "."))
    ):
        raise _Reject(RC_IDENTITY, f"{label}: unsafe branch ref")
    return ref


def _ref_sha(repo: Path, ref: str, label: str) -> str:
    return _decode_sha(
        _require_git(
            _git(repo, "rev-parse", "--verify", ref),
            label,
            RC_IDENTITY,
        ),
        label,
        RC_IDENTITY,
    )


def _verify_heads(
    repository: _Repository,
    landing_tip: str,
    *,
    tested_tip: str,
) -> tuple[str, str]:
    main_ref = _symbolic_head(repository.main, "main")
    if main_ref != "refs/heads/main":
        raise _Reject(RC_IDENTITY, "primary worktree HEAD must be refs/heads/main")
    main_head = _head(repository.main, "main")
    if _ref_sha(repository.main, main_ref, "main branch") != main_head:
        raise _Reject(RC_IDENTITY, "main HEAD/ref mismatch")

    wave_ref = _symbolic_head(repository.wave, "wave")
    wave_head = _head(repository.wave, "wave")
    if _ref_sha(repository.wave, wave_ref, "wave branch") != wave_head:
        raise _Reject(RC_IDENTITY, "wave HEAD/ref mismatch")
    if wave_head != landing_tip:
        reason = (
            "wave HEAD/ref moved from tested wave tip"
            if landing_tip == tested_tip
            else "wave HEAD/ref moved from landing wave tip"
        )
        raise _Reject(RC_AUDIT, reason)
    return main_head, wave_ref


def _verify_history_modifiers(repository: _Repository) -> None:
    for relative, label in (
        (b"shallow", "shallow repository"),
        (b"info/grafts", "graft file"),
    ):
        try:
            os.stat(relative, dir_fd=repository.common_fd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise _Reject(
                RC_AUDIT,
                f"{label}: cannot inspect ({exc})",
                retryable_same_request=True,
            ) from exc
        raise _Reject(RC_AUDIT, f"{label} is unsupported")
    replace = _require_git(
        _git(repository.wave, "for-each-ref", "--format=%(refname)", "refs/replace/"),
        "replace refs",
    )
    if replace.strip():
        raise _Reject(RC_AUDIT, "replace refs are unsupported")


def _verify_effective_config(repository: _Repository) -> None:
    checks = (
        (r"^filter\.", "local filter configuration"),
        (
            r"^(extensions\.partialclone|remote\..*\.promisor|"
            r"remote\..*\.partialclonefilter)$",
            "partial-clone/lazy-fetch configuration",
        ),
    )
    for pattern, label in checks:
        result = _git(
            repository.main,
            "config", "--includes", "--null", "--name-only", "--get-regexp", pattern,
        )
        if result.returncode not in (0, 1):
            raise _Reject(
                RC_AUDIT,
                f"{label}: config inspection failed ({_detail(result.stderr)})",
                retryable_same_request=True,
            )
        if result.returncode == 0 and result.stdout:
            raise _Reject(RC_AUDIT, f"{label} is unsupported")


def _verify_replay_config(repository: _Repository) -> None:
    wave_branch = _symbolic_head(repository.wave, "wave")[len("refs/heads/"):]
    wave_branch_raw = wave_branch.encode("ascii")
    for label, worktree in (("main", repository.main), ("wave", repository.wave)):
        result = _git_config_names(worktree)
        if result.returncode != 0:
            raise _Reject(
                RC_AUDIT,
                "merge-affecting configuration: config inspection failed "
                f"for {label} worktree ({_detail(result.stderr)})",
                retryable_same_request=True,
            )
        for raw_key in result.stdout.split(b"\0"):
            if not raw_key:
                continue
            key = raw_key.lower()
            is_merge_driver = (
                key.startswith(_MERGE_DRIVER_CONFIG_PREFIX)
                and any(
                    len(key) > len(_MERGE_DRIVER_CONFIG_PREFIX) + len(suffix)
                    and key.endswith(suffix)
                    for suffix in _MERGE_DRIVER_CONFIG_SUFFIXES
                )
            )
            if is_merge_driver:
                raise _Reject(
                    RC_AUDIT,
                    "external merge driver configuration is unsupported",
                )
            is_branch_merge_options = (
                key.startswith(_BRANCH_CONFIG_PREFIX)
                and len(key) > (
                    len(_BRANCH_CONFIG_PREFIX)
                    + len(_BRANCH_MERGE_OPTIONS_SUFFIX)
                )
                and key.endswith(_BRANCH_MERGE_OPTIONS_SUFFIX)
                and raw_key[
                    len(_BRANCH_CONFIG_PREFIX):
                    -len(_BRANCH_MERGE_OPTIONS_SUFFIX)
                ] == wave_branch_raw
            )
            if (
                key in _MERGE_AFFECTING_CONFIG_KEYS
                or is_branch_merge_options
            ):
                try:
                    display_key = key.decode("ascii")
                except UnicodeDecodeError as exc:
                    raise _Reject(
                        RC_AUDIT,
                        "merge-affecting configuration key is non-ASCII",
                    ) from exc
                raise _Reject(
                    RC_AUDIT,
                    "merge-affecting configuration is unsupported: "
                    f"{display_key}",
                )


def _handoff_snapshot(
    repository: _Repository,
) -> tuple[frozenset[bytes], tuple[tuple[bytes, tuple[object, ...]], ...]]:
    """foreign handoff 面は「名前集合」と「dir identity」だけを観測する。

    直下エントリの型・名前・大きさ・link 数・encoding・schema は land の
    受理集合に一切入らない (T-220 択 (a))。他セッション所有の handoff は
    incoming target と衝突するときだけ拒否され、その拒否は
    ``_verify_main_clean`` / ``_verify_target_collisions`` の
    ``_paths_overlap`` に一本化されている。
    """
    docs_fd = _openat_dir(repository.main_fd, b"docs", "main/docs", rc=RC_CONTROL_PLANE)
    try:
        handoff_fd = _openat_dir(
            docs_fd, b"handoff", "main/docs/handoff", rc=RC_CONTROL_PLANE
        )
    finally:
        os.close(docs_fd)
    try:
        directory_before = os.fstat(handoff_fd)
        try:
            names_before = sorted(os.fsencode(name) for name in os.listdir(handoff_fd))
        except OSError as exc:
            raise _Reject(
                RC_CONTROL_PLANE,
                f"main/docs/handoff: list failed ({exc})",
                retryable_same_request=True,
            ) from exc
        observed = frozenset(
            b"docs/handoff/" + name
            for name in names_before
            if name != b"README.md"
        )
        identities: tuple[tuple[bytes, tuple[object, ...]], ...] = (
            (b"docs/handoff", _identity(directory_before)),
        )
        try:
            names_after = sorted(os.fsencode(name) for name in os.listdir(handoff_fd))
        except OSError as exc:
            raise _Reject(
                RC_CONTROL_PLANE,
                f"main/docs/handoff: relist failed ({exc})",
                retryable_same_request=True,
            ) from exc
        if names_after != names_before:
            raise _Reject(RC_CONTROL_PLANE, "handoff directory changed while observing")
        return observed, identities
    finally:
        os.close(handoff_fd)


def _open_container(
    repository: _Repository, relative: bytes
) -> tuple[int, bytes] | None:
    first, second = relative.split(b"/", 1)
    try:
        first_fd = _openat_dir(
            repository.main_fd, first, f"main/{first!r}", rc=RC_CONTROL_PLANE
        )
    except _Reject as exc:
        if isinstance(exc.__cause__, FileNotFoundError):
            return None
        raise
    try:
        try:
            second_fd = _openat_dir(
                first_fd, second, f"main/{relative!r}", rc=RC_CONTROL_PLANE
            )
        except _Reject as exc:
            if isinstance(exc.__cause__, FileNotFoundError):
                return None
            raise
    finally:
        os.close(first_fd)
    return second_fd, os.fsencode(repository.main) + b"/" + relative


def _worktree_snapshot(
    repository: _Repository,
    protected_paths: Sequence[bytes] = (),
) -> tuple[
    tuple[bytes, ...],
    tuple[tuple[bytes, tuple[object, ...]], ...],
    tuple[tuple[bytes, tuple[object, ...]], ...],
]:
    """登録 child を検証し、land と重なる child だけを厳格集合へ返す。

    container 自身と無関係 child の membership は snapshot identity に入れない。
    ``observed_identities`` は比較窓で存続する同名 child の差し替えだけを
    検出する補助値で、``_ControlSnapshot`` の等価比較と fingerprint には
    参加しない。
    """

    prefixes: list[bytes] = []
    identities: list[tuple[bytes, tuple[object, ...]]] = []
    observed_identities: list[tuple[bytes, tuple[object, ...]]] = []
    common_path = os.fsencode(repository.common)
    wave_path = os.fsencode(repository.wave)
    rebound_wave_fd = _open_dir(
        repository.wave,
        "wave worktree control binding",
        rc=RC_CONTROL_PLANE,
    )
    try:
        wave_binding = _validate_admin_binding(
            child_fd=rebound_wave_fd,
            child_path=wave_path,
            common_fd=repository.common_fd,
            common_path=common_path,
            label="wave worktree control binding",
            rc=RC_CONTROL_PLANE,
        )
    finally:
        os.close(rebound_wave_fd)
    identities.append((b"wave-worktree", wave_binding))
    for relative in _CONTROL_CONTAINERS:
        opened = _open_container(repository, relative)
        if opened is None:
            continue
        container_fd, container_path = opened
        try:
            try:
                names_before = sorted(
                    os.fsencode(name) for name in os.listdir(container_fd)
                )
            except OSError as exc:
                raise _Reject(
                    RC_CONTROL_PLANE,
                    f"container {relative!r}: list failed ({exc})",
                    retryable_same_request=True,
                ) from exc
            protected_before: list[bytes] = []
            for name in names_before:
                child_relative = relative + b"/" + name
                child_path = container_path + b"/" + name
                protected = child_path == wave_path or any(
                    _paths_overlap(child_relative, path)
                    for path in protected_paths
                )
                if not protected:
                    continue
                if _SAFE_CHILD_RE.fullmatch(name) is None:
                    raise _Reject(RC_CONTROL_PLANE, "unsafe worktree child name")
                protected_before.append(name)
                child_fd = _openat_dir(
                    container_fd,
                    name,
                    f"container child {child_relative!r}",
                    rc=RC_CONTROL_PLANE,
                )
                try:
                    binding = _validate_admin_binding(
                        child_fd=child_fd,
                        child_path=child_path,
                        common_fd=repository.common_fd,
                        common_path=common_path,
                        label=f"registered child {relative + b'/' + name!r}",
                        rc=RC_CONTROL_PLANE,
                    )
                finally:
                    os.close(child_fd)
                observed_identities.append((child_relative, binding))
                if protected:
                    identities.append((child_relative, binding))
                    prefixes.append(child_relative + b"/")
            try:
                names_after = sorted(
                    os.fsencode(name) for name in os.listdir(container_fd)
                )
            except OSError as exc:
                raise _Reject(
                    RC_CONTROL_PLANE,
                    f"container {relative!r}: relist failed ({exc})",
                    retryable_same_request=True,
                ) from exc
            protected_after = [
                name
                for name in names_after
                if (
                    container_path + b"/" + name == wave_path
                    or any(
                        _paths_overlap(relative + b"/" + name, path)
                        for path in protected_paths
                    )
                )
            ]
            if any(_SAFE_CHILD_RE.fullmatch(name) is None for name in protected_after):
                raise _Reject(RC_CONTROL_PLANE, "unsafe worktree child name")
            if protected_after != protected_before:
                raise _Reject(
                    RC_CONTROL_PLANE,
                    f"protected worktree set in {relative!r} changed while validating",
                )
        finally:
            os.close(container_fd)
    return tuple(prefixes), tuple(identities), tuple(observed_identities)


def _control_snapshot(
    repository: _Repository,
    protected_paths: Sequence[bytes] = (),
) -> _ControlSnapshot:
    handoffs, handoff_identities = _handoff_snapshot(repository)
    targets = tuple(protected_paths)
    prefixes, worktree_identities, observed_identities = _worktree_snapshot(
        repository, targets
    )
    return _ControlSnapshot(
        handoffs=handoffs,
        worktree_prefixes=prefixes,
        identities=handoff_identities + worktree_identities,
        observed_worktree_identities=observed_identities,
        worktree_targets=targets,
    )


def _surviving_worktree_bindings_unchanged(
    before: _ControlSnapshot,
    after: _ControlSnapshot,
) -> bool:
    """同名 worktree の差し替えだけを検出し、起動・撤収は比較しない。"""

    before_by_path = dict(before.observed_worktree_identities)
    after_by_path = dict(after.observed_worktree_identities)
    return all(
        before_by_path[path] == after_by_path[path]
        for path in before_by_path.keys() & after_by_path.keys()
    )


def _status_records(repo: Path, label: str) -> list[bytes]:
    raw = _require_git(
        _git(
            repo,
            "status", "--porcelain=v1", "-z",
            "--untracked-files=all", "--ignore-submodules=none",
        ),
        f"{label} status",
        RC_DIRT,
    )
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise _Reject(RC_DIRT, f"{label} status is not NUL terminated")
    return raw[:-1].split(b"\0")


def _verify_main_clean(
    repository: _Repository,
    collision_paths: Sequence[bytes] | None = None,
    allowed_tracked_paths: Sequence[bytes] = (),
) -> _ControlSnapshot:
    targets = tuple(collision_paths or ())
    before = _control_snapshot(repository, targets)
    records = _status_records(repository.main, "main")
    after = _control_snapshot(repository, targets)
    if before != after or not _surviving_worktree_bindings_unchanged(
        before, after
    ):
        raise _Reject(
            RC_CONTROL_PLANE,
            "control-plane identity/binding changed around main status",
        )
    for record in records:
        if not record.startswith(b"?? "):
            relative = record[3:]
            if relative in allowed_tracked_paths:
                continue
            raise _Reject(RC_DIRT, "main tracked/index/submodule dirt is forbidden")
        # git は nested repository / linked worktree を collapsed directory として
        # `?? path/` の 1 レコードで返す (`-uall` でも同じ)。以降の成分境界比較は
        # `_ignored_paths_for_target` と同型に正規化した path で行う。
        relative = record[3:].rstrip(b"/")
        if any(
            relative == handoff or relative.startswith(handoff + b"/")
            for handoff in after.handoffs
        ):
            continue
        if any(
            relative == prefix[:-1] or relative.startswith(prefix)
            for prefix in after.worktree_prefixes
        ):
            continue
        if collision_paths is not None and any(
            _paths_overlap(relative, target) for target in collision_paths
        ):
            raise _Reject(
                RC_DIRT,
                f"main untracked path collides with land target: {relative!r}",
            )
    return after


def _verify_main_no_tracked_dirt(repository: _Repository) -> None:
    """post-land 用の縮約検査 — tracked/index/submodule dirt だけを見る。

    merge 後には守るべき後続変異が無く、control-plane の TOCTOU 監視は目的を持たない。
    他セッションの handoff 活動を自分の land の非再試行 failure へ誤帰属しないため、
    ``_verify_main_clean`` の control-plane 面をここでは観測しない。
    """
    for record in _status_records(repository.main, "main post-land"):
        if not record.startswith(b"?? "):
            raise _Reject(RC_DIRT, "main tracked/index/submodule dirt is forbidden")


def _verify_wave_clean(repository: _Repository) -> None:
    if _status_records(repository.wave, "wave"):
        raise _Reject(RC_DIRT, "wave worktree must be completely clean")


def _nul_records(raw: bytes, label: str, rc: int) -> list[bytes]:
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise _Reject(rc, f"{label} is not NUL terminated")
    return raw[:-1].split(b"\0")


def _ignored_paths_for_target(
    repository: _Repository, target: bytes
) -> tuple[bytes, ...]:
    raw = _require_git(
        _git(
            repository.main,
            "status", "--porcelain=v1", "-z",
            "--untracked-files=all", "--ignored=matching",
            "--ignore-submodules=none",
            "--", os.fsdecode(target),
        ),
        f"main ignored-path status for {target!r}",
        RC_DIRT,
    )
    return tuple(
        record[3:].rstrip(b"/")
        for record in _nul_records(
            raw, f"main ignored-path status for {target!r}", RC_DIRT
        )
        if record.startswith(b"!! ")
    )


def _target_paths(
    repository: _Repository, current: str, tested_tip: str
) -> tuple[bytes, ...]:
    raw = _require_git(
        _git(
            repository.wave,
            "diff", "--name-only", "-z", "--no-renames", current, tested_tip,
        ),
        "target path closure",
    )
    paths = tuple(_nul_records(raw, "target path closure", RC_AUDIT))
    for path in paths:
        if (
            not path
            or path.startswith(b"/")
            or b"\0" in path
            or any(part in (b"", b".", b"..") for part in path.split(b"/"))
        ):
            raise _Reject(RC_AUDIT, f"unsafe target path: {path!r}")
    return paths


def _paths_overlap(left: bytes, right: bytes) -> bool:
    return (
        left == right
        or left.startswith(right + b"/")
        or right.startswith(left + b"/")
    )


def _existing_ignored_target_or_ancestor(
    repository: _Repository, target: bytes
) -> bytes | None:
    parts = target.split(b"/")
    for index in range(1, len(parts) + 1):
        ancestor = b"/".join(parts[:index])
        try:
            metadata = os.stat(
                ancestor,
                dir_fd=repository.main_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise _Reject(
                RC_DIRT,
                f"target ancestor inspection failed for {ancestor!r} ({exc})",
                retryable_same_request=True,
            ) from exc
        if stat.S_ISDIR(metadata.st_mode) and index < len(parts):
            continue
        ignored = _git(
            repository.main,
            "check-ignore", "--quiet", "--", os.fsdecode(ancestor),
        )
        if ignored.returncode == 0:
            return ancestor
        if ignored.returncode != 1:
            raise _Reject(
                RC_DIRT,
                f"target ancestor ignore inspection failed for {ancestor!r} "
                f"({_detail(ignored.stderr) or 'no detail'})",
                retryable_same_request=True,
            )
        return None
    return None


def _verify_target_collisions(
    repository: _Repository,
    *,
    current: str,
    tested_tip: str,
    control: _ControlSnapshot,
) -> None:
    targets = _target_paths(repository, current, tested_tip)
    protected = tuple(control.handoffs) + _CONTROL_CONTAINERS + tuple(
        prefix[:-1] for prefix in control.worktree_prefixes
    )
    for target in targets:
        if any(_paths_overlap(target, path) for path in protected):
            raise _Reject(
                RC_CONTROL_PLANE,
                f"target collides with validated foreign control-plane path: {target!r}",
            )
        ignored = tuple(
            path
            for path in _ignored_paths_for_target(repository, target)
            if path == target or path.startswith(target + b"/")
        )
        ancestor = _existing_ignored_target_or_ancestor(repository, target)
        if ignored or ancestor is not None:
            collision = ignored[0] if ignored else ancestor
            raise _Reject(
                RC_DIRT,
                f"target collides with an existing ignored path: "
                f"target={target!r}, existing={collision!r}",
            )


def _land_fingerprint(
    repository: _Repository,
    *,
    current: str,
    tested_tip: str,
    wave_head: str,
    control: _ControlSnapshot,
) -> _LandFingerprint:
    """監査窓を跨いで HEAD と collision 観測集合を束縛する。

    種別を path と組にすることで、同じ target path が ignored collision として
    消えた場合も、単なる target path の残存と区別する。
    """

    targets = _target_paths(repository, current, tested_tip)
    paths: set[tuple[str, bytes]] = {
        ("target", target) for target in targets
    }
    protected = tuple(control.handoffs) + _CONTROL_CONTAINERS + tuple(
        prefix[:-1] for prefix in control.worktree_prefixes
    )
    paths.update(("protected", path) for path in protected)
    for record in _status_records(repository.main, "main fingerprint"):
        if not record.startswith(b"?? "):
            continue
        relative = record[3:].rstrip(b"/")
        if any(_paths_overlap(relative, target) for target in targets):
            paths.add(("untracked", relative))
    for target in targets:
        paths.update(
            ("ignored", path)
            for path in _ignored_paths_for_target(repository, target)
            if path == target or path.startswith(target + b"/")
        )
        ancestor = _existing_ignored_target_or_ancestor(repository, target)
        if ancestor is not None:
            paths.add(("ignored-ancestor", ancestor))
    return _LandFingerprint(
        main_head=current,
        wave_head=wave_head,
        collision_paths=frozenset(paths),
    )


def _is_ancestor(repo: Path, older: str, newer: str) -> bool:
    result = _git(repo, "merge-base", "--is-ancestor", older, newer)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise _Reject(
        RC_AUDIT,
        f"ancestry inspection failed ({_detail(result.stderr) or 'no detail'})",
        retryable_same_request=True,
    )


def _resolved_commit(repository: _Repository, revision: str, label: str) -> str:
    resolved = _decode_sha(
        _require_git(
            _git(repository.wave, "rev-parse", "--verify", f"{revision}^{{commit}}"),
            label,
        ),
        label,
    )
    if resolved != revision:
        raise _Reject(RC_AUDIT, f"{label}: object does not resolve exactly")
    return resolved


def _unique_merge_base(
    repository: _Repository,
    left: str,
    right: str,
    label: str,
) -> str:
    raw = _require_git(
        _git(repository.wave, "merge-base", "--all", left, right),
        label,
    )
    try:
        values = tuple(line for line in raw.decode("ascii").splitlines() if line)
    except UnicodeDecodeError as exc:
        raise _Reject(RC_AUDIT, f"{label}: non-ASCII object id") from exc
    if len(values) != 1:
        raise _Reject(RC_AUDIT, f"{label}: expected exactly one merge base")
    return _sha(values[0], label)


def _forward_main_merge_topology(
    repository: _Repository,
    tested_main: str,
    tested_tip: str,
    landing_tip: str,
) -> tuple[_ForwardMainMerge, ...]:
    """T..L の first-parent 列を exact な main 前方取り込み列へ畳む。"""

    _resolved_commit(repository, tested_tip, "tested wave tip")
    _resolved_commit(repository, landing_tip, "landing wave tip")
    if landing_tip == tested_tip:
        return ()
    raw = _require_git(
        _git(
            repository.wave,
            "rev-list",
            "--reverse",
            "--first-parent",
            "--parents",
            f"{tested_tip}..{landing_tip}",
        ),
        "forward main merge first-parent closure",
    )
    try:
        rows = tuple(line.split() for line in raw.decode("ascii").splitlines() if line)
    except UnicodeDecodeError as exc:
        raise _Reject(
            RC_AUDIT,
            "forward main merge first-parent closure is non-ASCII",
        ) from exc
    if not rows:
        raise _Reject(RC_AUDIT, "landing tip has no first-parent path from tested tip")
    if len(rows) > _MAX_FORWARD_MAIN_MERGES:
        raise _Reject(
            RC_AUDIT,
            "forward main merge chain exceeds the accepted maximum "
            f"of {_MAX_FORWARD_MAIN_MERGES}",
        )

    expected_parent = tested_tip
    previous_main: str | None = None
    merges: list[_ForwardMainMerge] = []
    for index, row in enumerate(rows, start=1):
        if len(row) < 2:
            raise _Reject(
                RC_AUDIT,
                "forward main merge first-parent commit must have exactly two parents",
            )
        commit = _sha(row[0], f"forward main merge {index} object")
        first_parent = _sha(row[1], f"forward main merge {index} first parent")
        if first_parent != expected_parent:
            raise _Reject(RC_AUDIT, "forward main merge first-parent chain is not exact")
        if len(row) != 3:
            _reject_non_two_parent_forward_commit()
        if len(row) == 2:
            # B-057-3: parent-count 条件を恒真化する変異でも、この通常 commit
            # を後段の添字・closure gate が重ねて拒否しないようにする。
            expected_parent = commit
            continue
        incorporated_main = _sha(
            row[2],
            f"forward main merge {index} incorporated main",
        )
        if not merges and not _is_ancestor(
            repository.wave,
            tested_main,
            incorporated_main,
        ):
            # B-057-7: この gate を外したときだけ divergent fixture が
            # land まで到達する。後段へ同じ A <= S_1 条件を重ねない。
            raise _Reject(
                RC_AUDIT,
                "first incorporated main is not a descendant of tested main",
            )
        prior_main = _unique_merge_base(
            repository,
            first_parent,
            incorporated_main,
            f"forward main merge {index} merge base",
        )
        if previous_main is not None and prior_main != previous_main:
            raise _Reject(
                RC_AUDIT,
                "forward main merge does not continue from the prior incorporated main",
            )
        if prior_main == incorporated_main or not _is_ancestor(
            repository.wave, prior_main, incorporated_main
        ):
            raise _Reject(RC_AUDIT, "incorporated main history did not advance")
        if previous_main is not None and (
            previous_main == incorporated_main
            or not _is_ancestor(repository.wave, previous_main, incorporated_main)
        ):
            raise _Reject(RC_AUDIT, "incorporated main history is not monotonic")
        tree_sha = _decode_sha(
            _require_git(
                _git(
                    repository.wave,
                    "rev-parse",
                    "--verify",
                    f"{commit}^{{tree}}",
                ),
                f"forward main merge {index} tree",
            ),
            f"forward main merge {index} tree",
        )
        merges.append(_ForwardMainMerge(
            commit_sha=commit,
            first_parent_sha=first_parent,
            incorporated_main_sha=incorporated_main,
            prior_main_sha=prior_main,
            tree_sha=tree_sha,
        ))
        expected_parent = commit
        previous_main = incorporated_main
    if merges[-1].commit_sha != landing_tip:
        raise _Reject(RC_AUDIT, "forward main merge chain does not end at landing tip")
    return tuple(merges)


def _reject_non_two_parent_forward_commit() -> None:
    raise _Reject(
        RC_AUDIT,
        "forward main merge first-parent commit must have exactly two parents",
    )


def _replay_forward_main_merges(
    repository: _Repository,
    merges: Sequence[_ForwardMainMerge],
) -> None:
    """隔離 repo で既定 strategy の merge を再演し、whole tree を照合する。"""

    if not merges:
        return
    object_format_raw = _require_git(
        _git(repository.wave, "rev-parse", "--show-object-format"),
        "repository object format",
    )
    try:
        object_format = object_format_raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise _Reject(RC_AUDIT, "repository object format is non-ASCII") from exc
    if object_format not in {"sha1", "sha256"}:
        raise _Reject(RC_AUDIT, "repository object format is unsupported")
    try:
        source_objects = (repository.common / "objects").resolve(strict=True)
    except OSError as exc:
        raise _Reject(
            RC_AUDIT,
            f"source object store cannot be resolved ({exc})",
            retryable_same_request=True,
        ) from exc
    source_objects_raw = os.fsencode(source_objects)
    if b"\n" in source_objects_raw or b"\x00" in source_objects_raw:
        raise _Reject(RC_AUDIT, "source object store path is unsafe for alternates")

    try:
        with tempfile.TemporaryDirectory(
            prefix="izanagi-dev-wave-merge-replay-",
            dir="/tmp",
        ) as raw:
            replay = Path(raw)
            _require_git(
                _git(
                    replay,
                    "init",
                    "--quiet",
                    f"--object-format={object_format}",
                    ".",
                ),
                "forward main merge replay init",
            )
            alternates = replay / ".git" / "objects" / "info" / "alternates"
            alternates.write_bytes(source_objects_raw + b"\n")
            _require_git(
                _git(replay, "symbolic-ref", "HEAD", "refs/heads/replay"),
                "forward main merge replay symbolic HEAD",
            )
            for index, merge in enumerate(merges, start=1):
                _require_git(
                    _git(
                        replay,
                        "update-ref",
                        "refs/heads/replay",
                        merge.first_parent_sha,
                    ),
                    f"forward main merge replay {index} ref",
                )
                _require_git(
                    _git(replay, "reset", "--hard", merge.first_parent_sha),
                    f"forward main merge replay {index} reset",
                )
                replayed = _git(
                    replay,
                    "-c",
                    "user.name=Izanagi Merge Replay",
                    "-c",
                    "user.email=merge-replay@izanagi.invalid",
                    "-c",
                    "commit.gpgSign=false",
                    "merge",
                    "--no-commit",
                    "--no-ff",
                    "--no-edit",
                    "--no-stat",
                    "--no-progress",
                    merge.incorporated_main_sha,
                )
                # B-057-2: 非 0 rc を見逃す変異では expected fallback が残り、
                # 後段 write-tree failure が同じ入力を重ねて拒否しないようにする。
                replay_tree = merge.tree_sha
                if replayed.returncode != 0:
                    _reject_nonclean_replay(
                        merge,
                        replayed,
                    )
                if replayed.returncode == 0:
                    replay_tree = _decode_sha(
                        _require_git(
                            _git(replay, "write-tree"),
                            f"forward main merge replay {index} tree",
                        ),
                        f"forward main merge replay {index} tree",
                    )
                if replay_tree != merge.tree_sha:
                    raise _Reject(
                        RC_AUDIT,
                        "forward main merge replay tree mismatch "
                        f"at {merge.commit_sha}",
                    )
    except _Reject:
        raise
    except OSError as exc:
        raise _Reject(
            RC_AUDIT,
            f"forward main merge replay workspace failed ({exc})",
            retryable_same_request=True,
        ) from exc


def _reject_nonclean_replay(
    merge: _ForwardMainMerge,
    replayed: _GitResult,
) -> None:
    raise _Reject(
        RC_AUDIT,
        "forward main merge replay rejected a non-clean merge "
        f"at {merge.commit_sha} "
        f"({_detail(replayed.stderr) or 'no detail'})",
        retryable_same_request=replayed.returncode not in {1},
    )


def _verify_locked_forward_main(
    repository: _Repository,
    locked_main: str,
    landing_tip: str,
    merges: Sequence[_ForwardMainMerge],
) -> None:
    if not merges:
        raise _Reject(RC_AUDIT, "forward main merge verification token is empty")
    if not _is_ancestor(
        repository.wave,
        merges[-1].incorporated_main_sha,
        locked_main,
    ):
        raise _Reject(RC_STALE_MAIN, "incorporated main is not an ancestor of locked main")
    if not _is_ancestor(repository.wave, locked_main, landing_tip):
        raise _Reject(RC_STALE_MAIN, "landing tip does not contain locked main")


def _fold_landed_closure(
    repository: _Repository,
    *,
    tested_main: str,
    landing_tip: str,
    forward_main_merges: Sequence[_ForwardMainMerge],
) -> tuple[str, tuple[str, ...]]:
    cutoff = (
        forward_main_merges[-1].incorporated_main_sha
        if forward_main_merges
        else tested_main
    )
    raw = _require_git(
        _git(repository.wave, "rev-list", "--reverse", f"{cutoff}..{landing_tip}"),
        "fold landed commit closure",
    )
    try:
        actual = tuple(
            _sha(line, "fold landed commit")
            for line in raw.decode("ascii").splitlines()
            if line
        )
    except UnicodeDecodeError as exc:
        raise _Reject(RC_AUDIT, "fold landed commit closure is non-ASCII") from exc
    # 通常形では topology gate により actual == A..T + (C_i) となる。
    # ここは fold engine 自身が永続化する exact closure の導出だけを担い、
    # B-057-3 の parent-count gate と重複する拒否面を作らない。
    return cutoff, actual


def _verify_audit(
    repository: _Repository,
    tested_main: str,
    tested_tip: str,
    audited: tuple[str, ...],
) -> tuple[str, ...]:
    for index, commit in enumerate(audited):
        _sha(commit, f"audited commit {index}")
    for value, label in (
        (tested_main, "tested main"),
        (tested_tip, "tested wave tip"),
    ):
        resolved = _decode_sha(
            _require_git(
                _git(repository.wave, "rev-parse", "--verify", f"{value}^{{commit}}"),
                label,
            ),
            label,
        )
        if resolved != value:
            raise _Reject(RC_AUDIT, f"{label}: object does not resolve exactly")
    if not _is_ancestor(repository.wave, tested_main, tested_tip):
        raise _Reject(RC_AUDIT, "tested main is not an ancestor of tested wave tip")
    raw = _require_git(
        _git(repository.wave, "rev-list", "--reverse", f"{tested_main}..{tested_tip}"),
        "audited commit closure",
    )
    try:
        actual = tuple(line for line in raw.decode("ascii").splitlines() if line)
    except UnicodeDecodeError as exc:
        raise _Reject(RC_AUDIT, "audited commit closure is non-ASCII") from exc
    if actual != audited:
        raise _Reject(RC_AUDIT, "audited commit sequence is not exact A..T closure")
    return actual


def _gitlink_map(repo: Path, commit: str) -> dict[bytes, str]:
    raw = _require_git(
        _git(repo, "ls-tree", "-r", "-z", commit),
        f"gitlink map at {commit}",
    )
    records = raw[:-1].split(b"\0") if raw.endswith(b"\0") else ([] if not raw else None)
    if records is None:
        raise _Reject(RC_AUDIT, "gitlink map is not NUL terminated")
    gitlinks: dict[bytes, str] = {}
    for record in records:
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, object_id = metadata.split(b" ", 2)
        except ValueError as exc:
            raise _Reject(RC_AUDIT, "gitlink map record is malformed") from exc
        if mode != b"160000":
            continue
        if object_type != b"commit":
            raise _Reject(RC_AUDIT, "gitlink entry has unexpected object type")
        oid = _decode_sha(object_id + b"\n", "gitlink object")
        if path in gitlinks:
            raise _Reject(RC_AUDIT, "duplicate gitlink path")
        gitlinks[path] = oid
    return gitlinks


def _normal_entry_paths(repo: Path, commit: str) -> frozenset[bytes]:
    raw = _require_git(
        _git(repo, "ls-tree", "-r", "-t", "-z", commit),
        f"normal entry map at {commit}",
    )
    records = raw[:-1].split(b"\0") if raw.endswith(b"\0") else ([] if not raw else None)
    if records is None:
        raise _Reject(RC_AUDIT, "normal entry map is not NUL terminated")
    paths: set[bytes] = set()
    for record in records:
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, _object_id = metadata.split(b" ", 2)
        except ValueError as exc:
            raise _Reject(RC_AUDIT, "normal entry map record is malformed") from exc
        if mode == b"160000":
            continue
        if object_type not in (b"blob", b"tree"):
            raise _Reject(RC_AUDIT, "normal entry has unexpected object type")
        if path in paths:
            raise _Reject(RC_AUDIT, "duplicate normal entry path")
        paths.add(path)
    return frozenset(paths)


def _validate_gitlink_path(relative: bytes) -> None:
    if (
        relative.startswith(b"/")
        or any(part in (b"", b".", b"..") for part in relative.split(b"/"))
    ):
        raise _Reject(RC_AUDIT, f"unsafe gitlink path: {relative!r}")


def _removed_gitlinks_absent(
    repository: _Repository,
    base: dict[bytes, str],
    target: dict[bytes, str],
    target_normal_entries: frozenset[bytes],
) -> bool:
    for relative in base.keys() - target.keys():
        _validate_gitlink_path(relative)
        candidates = [(repository.common_fd, b"modules/" + relative)]
        if relative in target_normal_entries:
            candidates.append((repository.main_fd, relative + b"/.git"))
        else:
            candidates.append((repository.main_fd, relative))
        for parent_fd, candidate in candidates:
            try:
                os.stat(candidate, dir_fd=parent_fd, follow_symlinks=False)
            except (FileNotFoundError, NotADirectoryError):
                continue
            except OSError:
                return False
            return False
    return True


def _gitlinks_synchronized(
    repository: _Repository,
    base: dict[bytes, str],
    target: dict[bytes, str],
    target_normal_entries: frozenset[bytes],
) -> bool:
    main_bytes = os.fsencode(repository.main)
    for relative, expected_head in target.items():
        _validate_gitlink_path(relative)
        candidate = repository.main / os.fsdecode(relative)
        try:
            canonical = _canonical_absolute(candidate, f"submodule {relative!r}")
        except _Reject:
            return False
        top = _git(canonical, "rev-parse", "--show-toplevel")
        superproject = _git(
            canonical, "rev-parse", "--show-superproject-working-tree"
        )
        head = _git(canonical, "rev-parse", "--verify", "HEAD")
        if any(result.returncode != 0 for result in (top, superproject, head)):
            return False
        if (
            os.path.normpath(top.stdout.strip()) != os.fsencode(canonical)
            or os.path.normpath(superproject.stdout.strip()) != main_bytes
        ):
            return False
        try:
            actual_head = _decode_sha(head.stdout, f"submodule {relative!r} HEAD")
        except _Reject:
            return False
        if actual_head != expected_head:
            return False
    return _removed_gitlinks_absent(
        repository,
        base,
        target,
        target_normal_entries,
    )


def _main_tracked_or_index_dirty(repository: _Repository) -> bool:
    for args, label in (
        (("diff", "--quiet", "--ignore-submodules=none"), "main worktree diff"),
        (
            ("diff", "--cached", "--quiet", "--ignore-submodules=none"),
            "main index diff",
        ),
    ):
        result = _git(repository.main, *args)
        if result.returncode == 1:
            return True
        if result.returncode != 0:
            raise _Reject(
                RC_LANDED_POSTCONDITION_FAILED,
                f"{label} inspection failed ({_detail(result.stderr) or 'no detail'})",
            )
    return False


def _main_is_allowed(
    repository: _Repository,
    current: str,
    tested_main: str,
    tested_tip: str,
    audited: tuple[str, ...],
    *,
    landing_tip: str,
    forward_main_merges: Sequence[_ForwardMainMerge],
) -> bool:
    if landing_tip != tested_tip:
        return bool(forward_main_merges)
    if current == tested_main:
        return True
    return (
        current in audited
        and _is_ancestor(repository.wave, tested_main, current)
        and _is_ancestor(repository.wave, current, tested_tip)
    )


def _land_lock_now() -> float:
    return time.monotonic()


def _land_turn_sleep(delay: float) -> None:
    time.sleep(delay)


def _turn_failure(reason: str) -> _Reject:
    return _Reject(RC_IDENTITY, "land turn: " + reason)


def _turn_file_binding(directory_fd: int, name: str, fd: int) -> None:
    held = os.fstat(fd)
    current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if not (
        _same_inode(held, current)
        and _lock_metadata_is_safe(held)
        and _lock_metadata_is_safe(current)
    ):
        raise _turn_failure(f"unsafe or replaced file {name}")


def _turn_binding(repository: _Repository, turn: _LandTurnHandle) -> None:
    common_fd = _open_dir(repository.common, "land turn common")
    try:
        held = os.fstat(turn.directory_fd)
        current = os.stat(
            _LAND_TURN_DIRECTORY, dir_fd=common_fd, follow_symlinks=False,
        )
        if not (
            _same_inode(os.fstat(repository.common_fd), os.fstat(common_fd))
            and _same_inode(held, current)
            and stat.S_ISDIR(current.st_mode)
            and current.st_uid == os.getuid()
            and not current.st_mode & 0o022
            and not held.st_mode & 0o022
        ):
            raise _turn_failure("directory binding changed")
        _turn_file_binding(turn.directory_fd, "registry.lock", turn.registry_fd)
        if turn.fd >= 0:
            _turn_file_binding(turn.directory_fd, turn.ticket, turn.fd)
    finally:
        os.close(common_fd)


def _turn_read(turn: _LandTurnHandle, name: str) -> bytes:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                 dir_fd=turn.directory_fd)
    try:
        _turn_file_binding(turn.directory_fd, name, fd)
        chunks = []
        total = 0
        while total <= _LAND_TURN_MAX_BYTES:
            chunk = os.read(fd, min(65536, _LAND_TURN_MAX_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        if len(raw) > _LAND_TURN_MAX_BYTES:
            raise _turn_failure(f"oversized file {name}")
        return raw
    finally:
        os.close(fd)


def _turn_json(raw: bytes) -> dict:
    try:
        value = json.loads(raw, object_pairs_hook=_no_duplicate_json_keys)
    except (ValueError, UnicodeError) as exc:
        raise _turn_failure("invalid registry or journal JSON") from exc
    if not isinstance(value, dict):
        raise _turn_failure("registry or journal is not an object")
    return value


def _turn_bytes(value: dict, *, sort_keys: bool = True) -> bytes:
    return json.dumps(value, sort_keys=sort_keys, separators=(",", ":")).encode("utf-8")


def _turn_write_all(fd: int, raw: bytes) -> None:
    while raw:
        count = os.write(fd, raw)
        if count <= 0:
            raise _turn_failure("short journal write")
        raw = raw[count:]
    os.fsync(fd)


def _turn_save_registry(turn: _LandTurnHandle, registry: dict) -> None:
    name = ".registry-" + os.urandom(12).hex()
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=turn.directory_fd)
    try:
        _turn_write_all(fd, _turn_bytes(registry, sort_keys=False) + b"\n")
        os.rename(name, "registry.json", src_dir_fd=turn.directory_fd,
                  dst_dir_fd=turn.directory_fd)
        os.fsync(turn.directory_fd)
    finally:
        os.close(fd)
        try:
            os.unlink(name, dir_fd=turn.directory_fd)
        except FileNotFoundError:
            pass


@contextmanager
def _turn_registry(repository: _Repository, turn: _LandTurnHandle):
    """Short registry transaction; never call Git or wait for common flock here."""
    deadline = _land_lock_now() + _LAND_TURN_REGISTRY_WAIT_SECONDS
    acquired = False
    try:
        while not acquired:
            try:
                fcntl.flock(turn.registry_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except BlockingIOError:
                now = _land_lock_now()
                if now >= deadline:
                    raise _Reject(RC_LOCK_BUSY, "land turn registry lock busy",
                                  retryable_same_request=True)
                _land_turn_sleep(min(_land_lock_jitter(0.05), deadline - now))
        _turn_binding(repository, turn)
        try:
            registry = _turn_json(_turn_read(turn, "registry.json"))
        except FileNotFoundError:
            if any(name.endswith(".jsonl") for name in os.listdir(turn.directory_fd)):
                raise _turn_failure("registry missing while journals exist")
            registry = {"next_seq": 1, "grant": None, "requests": {}}
            # Publish the empty registry durably before a caller creates a ticket.
            _turn_save_registry(turn, registry)
        if not (
            set(registry) == {"next_seq", "grant", "requests"}
            and type(registry["next_seq"]) is int and registry["next_seq"] > 0
            and isinstance(registry["requests"], dict)
            and (registry["grant"] is None or registry["grant"] in registry["requests"])
        ):
            raise _turn_failure("invalid registry schema")
        seqs = set()
        for key, entry in registry["requests"].items():
            if not (
                isinstance(key, str) and _SHA256_RE.fullmatch(key)
                and isinstance(entry, dict)
                and type(entry.get("seq")) is int
                and 0 < entry["seq"] < registry["next_seq"]
                and type(entry.get("order")) is int
                and 0 < entry["order"] and entry["order"] >= entry["seq"]
                and entry["seq"] not in seqs
                and isinstance(entry.get("binding"), dict)
                and (entry.get("ticket") is None or (
                    isinstance(entry["ticket"], str)
                    and re.fullmatch(r"[0-9]{8,}-[0-9a-f]{12}\.jsonl", entry["ticket"])
                ))
            ):
                raise _turn_failure("invalid request entry")
            seqs.add(entry["seq"])
        before = _turn_bytes(registry, sort_keys=False)
        yield registry
        _turn_binding(repository, turn)
        if _turn_bytes(registry, sort_keys=False) != before:
            _turn_save_registry(turn, registry)
    except OSError as exc:
        raise _turn_failure(f"registry I/O failed ({exc})") from exc
    finally:
        if acquired:
            fcntl.flock(turn.registry_fd, fcntl.LOCK_UN)


def _turn_live(turn: _LandTurnHandle, ticket: str | None) -> bool:
    if ticket is None:
        return False
    fd = os.open(ticket, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK,
                 dir_fd=turn.directory_fd)
    try:
        _turn_file_binding(turn.directory_fd, ticket, fd)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(fd)


def _turn_last_record(turn: _LandTurnHandle, entry: dict) -> dict:
    if entry["ticket"] is None:
        return {"phase": "waiting"}
    raw = _turn_read(turn, entry["ticket"])
    last = None
    for number, line in enumerate(raw.split(b"\n")[:-1], 1):
        envelope = _turn_json(line)
        record = envelope.get("record")
        if not (
            isinstance(record, dict) and record.get("number") == number
            and record.get("seq") == entry["seq"]
            and record.get("schema") == "dev-wave-land-turn/v1"
            and all(record.get(key) == value for key, value in entry["binding"].items())
            and record.get("phase") in {
                "waiting", "validating", "mutating", "done", "rejected", "rolled-back",
            }
            and envelope.get("sha256") == hashlib.sha256(_turn_bytes(record)).hexdigest()
        ):
            raise _turn_failure("invalid complete journal record")
        if record["phase"] == "mutating":
            commits = record.get("landed_commits")
            if not (
                all(isinstance(record.get(key), str) and _SHA_RE.fullmatch(record[key])
                    for key in ("main_before", "landing_tip", "trusted_main_cutoff"))
                and isinstance(record.get("wave_ref"), str)
                and isinstance(record.get("expected_fold"), str)
                and isinstance(commits, list)
                and all(isinstance(commit, str) and _SHA_RE.fullmatch(commit) for commit in commits)
                and record.get("audited_digest") == hashlib.sha256(
                    b"".join(commit.encode("ascii") + b"\n" for commit in commits)
                ).hexdigest()
            ):
                raise _turn_failure("incomplete mutating authority")
        last = record
    if last is None:
        raise _turn_failure("ticket has no complete record")
    return last


def _turn_append(turn: _LandTurnHandle, phase: str, **fields) -> None:
    record = {**turn.record, **fields, "seq": turn.seq, "phase": phase,
              "number": turn.record.get("number", 0) + 1}
    raw = _turn_bytes({"record": record,
                       "sha256": hashlib.sha256(_turn_bytes(record)).hexdigest()})
    _turn_write_all(turn.fd, raw + b"\n")
    turn.record = record


def _turn_select(turn: _LandTurnHandle, registry: dict) -> list[str]:
    """Keep a live grant; dead mutating records block ordinary election."""
    live = []
    recovery = []
    for key, entry in list(registry["requests"].items()):
        record = _turn_last_record(turn, entry)
        alive = _turn_live(turn, entry["ticket"])
        if record["phase"] == "mutating":
            recovery.append(key)
        elif not alive and record["phase"] in {"done", "rejected"}:
            del registry["requests"][key]
            continue
        if alive:
            live.append(key)
    grant = registry["grant"]
    if recovery:
        # Recovery must never preempt a still-live owner.
        if grant not in live:
            registry["grant"] = next((key for key in recovery if key in live), None)
        return recovery
    if grant not in live:
        registry["grant"] = min(live, key=lambda key: registry["requests"][key]["order"],
                                default=None)
    return []


def _register_land_turn(repository: _Repository, request: LandRequest,
                        verified: _AcceptanceVerification, turn: _LandTurnHandle) -> None:
    try:
        try:
            os.mkdir(_LAND_TURN_DIRECTORY, 0o700, dir_fd=repository.common_fd)
        except FileExistsError:
            pass
        turn.directory_fd = _openat_dir(repository.common_fd, _LAND_TURN_DIRECTORY,
                                       "land turn directory", rc=RC_IDENTITY)
        turn.registry_fd = os.open("registry.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
                                   0o600, dir_fd=turn.directory_fd)
        binding = {"acceptance_wave": request.acceptance_wave,
                   "tested_tip": request.tested_wave_tip_sha,
                   "receipt_sha256": verified.receipt_sha256,
                   "tested_main": request.tested_main_sha,
                   "main": str(repository.main), "wave": str(repository.wave),
                   "common": str(repository.common)}
        turn.key = hashlib.sha256(_turn_bytes({key: binding[key] for key in (
            "acceptance_wave", "tested_tip", "receipt_sha256",
        )})).hexdigest()
        with _turn_registry(repository, turn) as registry:
            _turn_select(turn, registry)
            entry = registry["requests"].get(turn.key)
            previous = {}
            if entry is not None:
                if entry["binding"] != binding:
                    raise _turn_failure("same request has different repository binding")
                if _turn_live(turn, entry["ticket"]):
                    raise _Reject(RC_LOCK_BUSY, "same request already queued " + turn.key,
                                  retryable_same_request=True)
                previous = _turn_last_record(turn, entry)
                if (previous["phase"] == "mutating" and previous.get("landing_tip") != (
                    request.landing_wave_tip_sha or request.tested_wave_tip_sha
                )):
                    raise _Reject(RC_FOLD_RECOVERY_FAILED,
                                  "unresolved land turn has a different landing_tip")
                turn.seq = entry["seq"]
            else:
                turn.seq = registry["next_seq"]
                registry["next_seq"] += 1
            turn.ticket = f"{turn.seq:08d}-{os.urandom(6).hex()}.jsonl"
            turn.fd = os.open(turn.ticket, os.O_RDWR | os.O_APPEND | os.O_CREAT
                              | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=turn.directory_fd)
            fcntl.flock(turn.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            turn.record = {**binding, "schema": "dev-wave-land-turn/v1", "pid": os.getpid(),
                           "landing_tip": request.landing_wave_tip_sha or request.tested_wave_tip_sha}
            if previous.get("phase") == "mutating":
                turn.record.update({key: value for key, value in previous.items()
                                    if key not in {"number", "pid"}})
            _turn_append(turn, "mutating" if previous.get("phase") == "mutating" else "waiting")
            registry["requests"][turn.key] = {"seq": turn.seq,
                                              "order": entry["order"] if entry else turn.seq,
                                              "binding": binding,
                                              "ticket": turn.ticket}
            _turn_select(turn, registry)
    except OSError as exc:
        raise _turn_failure(f"registration failed ({exc})") from exc


def _land_turn_owner(repository: _Repository) -> None:
    turn = repository.turn
    if turn is None:
        raise _turn_failure("mutation has no turn")
    with _turn_registry(repository, turn) as registry:
        entry = registry["requests"].get(turn.key)
        if not (entry and entry["ticket"] == turn.ticket and turn.fd >= 0
                and registry["grant"] == turn.key and _turn_live(turn, turn.ticket)):
            raise _turn_failure("grant or live ticket ownership changed")
        try:
            fcntl.flock(turn.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise _turn_failure("ticket flock belongs to a different description") from exc


def _land_turn_mutating(repository: _Repository, *, plan: object, main_before: str,
                        landing_tip: str, wave_ref: str, trusted_main_cutoff: str,
                        landed_commits: Sequence[str]) -> None:
    if repository.land_lock is None:
        raise _turn_failure("mutation has no common lock")
    _verify_land_lock_binding(repository, repository.land_lock)
    _land_turn_owner(repository)
    turn = repository.turn
    assert turn is not None
    # Existing origin remains authoritative across recovery and repeated marking.
    if turn.record.get("phase") == "mutating":
        return
    if _land_lock_now() >= turn.deadline:
        raise _Reject(RC_LOCK_BUSY, "land turn deadline reached (phase=before-mutation)",
                      retryable_same_request=True)
    _turn_append(turn, "mutating", main_before=main_before, landing_tip=landing_tip,
                 wave_ref=wave_ref, trusted_main_cutoff=trusted_main_cutoff,
                 audited_digest=hashlib.sha256(b"".join(commit.encode("ascii") + b"\n" for commit in landed_commits)).hexdigest(),
                 landed_commits=list(landed_commits), expected_fold=getattr(plan, "status"),
                 transaction_id=getattr(plan, "transaction_id", None))


def _finish_land_turn(repository: _Repository, result: LandResult) -> None:
    turn = repository.turn
    if turn is None or turn.fd < 0 or turn.terminal:
        return
    with _turn_registry(repository, turn) as registry:
        entry = registry["requests"].get(turn.key)
        if entry is None or entry["ticket"] != turn.ticket:
            raise _turn_failure("terminal ticket binding changed")
        mutating = turn.record.get("phase") == "mutating"
        rollback_complete = (
            mutating and result.rc in {RC_FOLD_FAILED, RC_FOLD_GATE}
            and result.main_after == turn.record.get("main_before")
            and not os.path.lexists(repository.common / _FOLD_STATE_NAME)
        )
        unresolved = mutating and result.rc != RC_OK and not rollback_complete
        landed_fold_pending = (
            result.status == "landed-postcondition-failed"
            and result.main_after == turn.record.get("landing_tip")
            and result.main_after is not None
            and not os.path.lexists(repository.common / _FOLD_STATE_NAME)
        )
        if result.rc == RC_OK:
            phase = "done"
        elif landed_fold_pending:
            phase = "waiting"
        elif unresolved:
            phase = "mutating"
        elif rollback_complete:
            phase = "rolled-back"
        elif result.rc in {RC_STALE_MAIN, RC_LOCK_BUSY} or result.retryable_same_request:
            phase = "waiting"
        else:
            phase = "rejected"
        _turn_append(turn, phase)
        # Close before selecting: the terminating runtime must not re-elect itself.
        os.close(turn.fd)
        turn.fd = -1
        if phase in {"done", "rejected"}:
            del registry["requests"][turn.key]
        elif registry["grant"] == turn.key or mutating:
            entry["order"] = registry["next_seq"] - 1
            # Preserve FIFO among equal orders, including across registry reloads.
            registry["requests"][turn.key] = registry["requests"].pop(turn.key)
        if registry["grant"] == turn.key:
            registry["grant"] = None
        _turn_select(turn, registry)  # Release and handoff are one registry update.
        turn.terminal = True


def _observe_dead_land_turn(repository: _Repository, lock: _LandLockHandle,
                            key: str, entry: dict, record: dict) -> None:
    """Called only with common flock, without registry flock across Git reads."""
    turn = repository.turn
    assert turn is not None
    _verify_land_lock_binding(repository, lock)
    state = repository.common / _FOLD_STATE_NAME
    if os.path.lexists(state):
        if key == turn.key:
            return  # The unchanged existing recovery path verifies state authority.
        raise _Reject(RC_FOLD_RECOVERY_FAILED,
                      "unfinished land turn requires original request recovery",
                      retryable_same_request=True)
    current = _head(repository.main, "main during dead land turn observation")
    if current == record.get("main_before"):
        phase = "rolled-back"
    elif current == record.get("landing_tip") and record.get("expected_fold") == "noop":
        phase = "done"
    else:
        parent = _git(repository.main, "rev-parse", f"{current}^1")
        declared = None
        if (parent.returncode == 0
                and parent.stdout.decode("ascii").strip() == record.get("landing_tip")):
            try:
                declared = verify_declared_fold_commit(
                    repository.main, fold_commit_sha=current,
                    trusted_main_cutoff_sha=record["trusted_main_cutoff"],
                    landed_main_sha=current,
                    landed_commits=tuple(record["landed_commits"]),
                    wave_tip=record["landing_tip"],
                )
            except (Exception, KeyboardInterrupt) as exc:
                raise _Reject(
                    RC_FOLD_RECOVERY_FAILED,
                    f"dead land turn fold observation failed: main={current}, "
                    f"landing_tip={record.get('landing_tip')}: {type(exc).__name__}: {exc}",
                    retryable_same_request=True,
                ) from exc
        if (current == record.get("landing_tip")
                and record.get("expected_fold") != "noop"
                and (parent.returncode != 0
                     or parent.stdout.decode("ascii").strip() != record.get("landing_tip"))):
            # FF completed, but fold never started. Keep the request for the
            # existing already-landed path, including its D16 synchronization gate.
            phase = "waiting"
        elif declared is None or not declared.ok:
            raise _Reject(RC_FOLD_RECOVERY_FAILED,
                          f"unresolved mutating turn: main={current}, "
                          f"main_before={record.get('main_before')}, "
                          f"landing_tip={record.get('landing_tip')}",
                          retryable_same_request=True)
        else:
            phase = "done"
    with _turn_registry(repository, turn) as registry:
        if registry["requests"].get(key) != entry:
            return
        if key != turn.key and _turn_live(turn, entry["ticket"]):
            return
        latest = _turn_last_record(turn, entry)
        # Another observer may have resolved this exact ticket while we waited
        # for common flock. Compare the complete, digest-validated record.
        if latest != record:
            _turn_select(turn, registry)
            return
        if key == turn.key:
            _turn_append(turn, "done" if phase == "done" else "waiting")
            if phase == "done":
                os.close(turn.fd)
                turn.fd = -1
                turn.terminal = True
                del registry["requests"][key]
        else:
            fd = os.open(entry["ticket"], os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW,
                         dir_fd=turn.directory_fd)
            try:
                _turn_file_binding(turn.directory_fd, entry["ticket"], fd)
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                raw = _turn_read(turn, entry["ticket"])
                os.ftruncate(fd, raw.rfind(b"\n") + 1)
                observed = _LandTurnHandle(turn.started, turn.deadline,
                                           fd=fd, seq=entry["seq"], record=record)
                _turn_append(observed, phase)
            finally:
                os.close(fd)
            if phase == "done":
                del registry["requests"][key]
        if registry["grant"] == key:
            registry["grant"] = None
        _turn_select(turn, registry)


def _wait_land_turn(repository: _Repository, lock: _LandLockHandle) -> tuple[bool, float, int]:
    turn = repository.turn
    assert turn is not None
    common_waited = 0.0
    ahead = 0
    while _land_lock_now() < turn.deadline:
        with _turn_registry(repository, turn) as registry:
            recovery = _turn_select(turn, registry)
            dead = [(key, dict(registry["requests"][key]),
                     _turn_last_record(turn, registry["requests"][key]))
                    for key in recovery
                    if key == turn.key or not _turn_live(turn, registry["requests"][key]["ticket"])]
            granted = registry["grant"] == turn.key
            ordered = sorted(registry["requests"],
                             key=lambda key: registry["requests"][key]["order"])
            ahead = sum(_turn_live(turn, registry["requests"][key]["ticket"])
                        for key in ordered[:ordered.index(turn.key)])
        if dead:
            acquired, waited = _acquire_land_lock_until_turn(
                repository, lock, max(0.0, _LAND_LOCK_WAIT_SECONDS - common_waited),
            )
            common_waited += waited
            if not acquired:
                return False, common_waited, ahead
            try:
                for key, entry, record in dead:
                    _observe_dead_land_turn(repository, lock, key, entry, record)
                if turn.terminal:
                    return True, common_waited, ahead
                # Own active state is intentionally retained and prioritized.
                with _turn_registry(repository, turn) as registry:
                    _turn_select(turn, registry)
                    granted = registry["grant"] == turn.key
            finally:
                lock.close()
        if granted:
            _land_turn_owner(repository)
            return True, common_waited, ahead
        now = _land_lock_now()
        delay = min(_land_lock_jitter(_LAND_LOCK_MAX_POLL_SECONDS),
                    max(0.0, turn.deadline - now))
        if delay:
            _land_turn_sleep(delay)
            turn.waited_s += max(0.0, _land_lock_now() - now)
    return False, common_waited, ahead


def _acquire_land_lock_until_turn(repository: _Repository, lock: _LandLockHandle,
                                  remaining_wait_s: float) -> tuple[bool, float]:
    turn = repository.turn
    deadline = (turn.deadline if turn is not None else
                _land_lock_now() + max(0.0, remaining_wait_s))
    started = _land_lock_now()
    if started >= deadline:
        return False, 0.0
    acquired, waited = _acquire_land_lock(
        repository, lock, min(deadline, started + max(0.0, remaining_wait_s)),
    )
    if acquired:
        return True, waited
    while _land_lock_now() < deadline:
        lock.close()
        _land_turn_sleep(min(_land_lock_jitter(_LAND_LOCK_MAX_POLL_SECONDS),
                             deadline - _land_lock_now()))
        if _land_lock_now() >= deadline:
            break
        acquired, _ = _acquire_land_lock(repository, lock, _land_lock_now())
        if acquired:
            return True, max(0.0, _land_lock_now() - started)
    lock.close()
    return False, max(0.0, _land_lock_now() - started)


def _land_lock_sleep(delay: float) -> None:
    time.sleep(delay)


def _land_lock_jitter(delay_cap: float) -> float:
    return _LAND_LOCK_RANDOM.uniform(delay_cap / 2.0, delay_cap)


def _lock_metadata_is_safe(metadata: os.stat_result) -> bool:
    return (
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_uid == os.getuid()
        and metadata.st_nlink == 1
        and not metadata.st_mode & 0o022
    )


def _verify_land_lock_binding(
    repository: _Repository,
    lock: _LandLockHandle,
) -> None:
    rebound: list[int] = []
    try:
        main_fd = _open_dir(repository.main, "main worktree after lock acquisition")
        rebound.append(main_fd)
        wave_fd = _open_dir(
            repository.wave,
            "wave worktree after lock acquisition",
            rc=RC_CONTROL_PLANE,
        )
        rebound.append(wave_fd)
        common_fd = _open_dir(repository.common, "common git-dir after lock acquisition")
        rebound.append(common_fd)
        try:
            lock_path = os.stat(
                _LOCK_NAME,
                dir_fd=common_fd,
                follow_symlinks=False,
            )
            lock_fd = os.fstat(lock.fd)
        except OSError as exc:
            raise _Reject(
                RC_IDENTITY,
                f"land lock binding changed after acquisition ({exc})",
                retryable_same_request=True,
            ) from exc
        if not _same_inode(os.fstat(repository.wave_fd), os.fstat(wave_fd)):
            raise _Reject(
                RC_CONTROL_PLANE,
                "wave worktree control-plane identity/binding changed "
                "after lock acquisition",
            )
        if (
            not _same_inode(os.fstat(repository.main_fd), os.fstat(main_fd))
            or not _same_inode(os.fstat(repository.common_fd), os.fstat(common_fd))
            or not _same_inode(lock_fd, lock_path)
            or not _lock_metadata_is_safe(lock_fd)
            or not _lock_metadata_is_safe(lock_path)
        ):
            raise _Reject(
                RC_IDENTITY,
                "repository or land lock binding changed after acquisition",
            )
    finally:
        for fd in reversed(rebound):
            os.close(fd)


def _acquire_land_lock(
    repository: _Repository,
    lock: _LandLockHandle,
    deadline: float,
) -> tuple[bool, float]:
    """競合時の実待ち時間を返す（取得所要ではなく、無競合成功は 0）。

    競合後の実績には実行再開・取得処理の遅延も含む。期限後も flock は
    先に試すため成功し得るが、期限後は競合待ちを追加しない。
    """
    if lock.fd >= 0:
        raise RuntimeError("land lock handle is already open")
    started = _land_lock_now()
    _open_lock(repository, lock)
    poll = _LAND_LOCK_INITIAL_POLL_SECONDS
    contended = False
    while True:
        try:
            fcntl.flock(lock.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            contended = True
            now = _land_lock_now()
            if now >= deadline:
                return False, max(0.0, now - started)
            delay_cap = min(poll, _LAND_LOCK_MAX_POLL_SECONDS)
            jittered = _land_lock_jitter(delay_cap)
            if not 0.0 < jittered <= delay_cap:
                raise RuntimeError("land lock jitter returned an invalid delay")
            delay = min(jittered, deadline - now)
            _land_lock_sleep(delay)
            poll = min(poll * 2.0, _LAND_LOCK_MAX_POLL_SECONDS)
            continue
        _verify_land_lock_binding(repository, lock)
        waited = max(0.0, _land_lock_now() - started) if contended else 0.0
        return True, waited


def _locked_preflight(
    repository: _Repository,
    *,
    tested_main: str,
    tested_tip: str,
    landing_tip: str,
    prelocked_forward_main_merges: tuple[_ForwardMainMerge, ...],
    requested_audit: tuple[str, ...],
    reported_main_before: str | None,
) -> _LockedPreflight | LandResult:
    """lock 内の cheap checks と監査窓 fingerprint を一括実行する。"""

    _verify_history_modifiers(repository)
    _verify_effective_config(repository)
    if landing_tip != tested_tip:
        _verify_replay_config(repository)
    target_paths = _target_paths(repository, tested_main, landing_tip)
    fold = None
    try:
        fold = _load_spool_fold()
        active_plan = fold.load_active_plan(repository.main)
        active_fold_paths = (
            tuple(os.fsencode(path) for path in _fold_plan_paths(active_plan))
            if active_plan is not None
            else ()
        )
    except (Exception, KeyboardInterrupt) as exc:
        gate_error = (
            fold is not None
            and isinstance(
                exc,
                getattr(fold, "FoldGateReceiptError", ()),
            )
        )
        return LandResult(
            RC_FOLD_GATE if gate_error else RC_FOLD_RECOVERY_FAILED,
            "fold-gate-failed" if gate_error else "fold-recovery-failed",
            (
                "stored fold gate receipt rejected: "
                if gate_error
                else "fold transaction inspection failed: "
            )
            + f"{type(exc).__name__}: {exc}",
            reported_main_before,
            reported_main_before,
            landing_tip,
            retryable_same_request=True,
        )
    try:
        control = _verify_main_clean(
            repository,
            collision_paths=target_paths,
            allowed_tracked_paths=active_fold_paths,
        )
        _verify_wave_clean(repository)
        audited = _verify_audit(
            repository,
            tested_main,
            tested_tip,
            requested_audit,
        )
        base_gitlinks = _gitlink_map(repository.wave, tested_main)
        target_gitlinks = _gitlink_map(repository.wave, landing_tip)
        target_normal_entries = _normal_entry_paths(repository.wave, landing_tip)
        gitlinks_changed = base_gitlinks != target_gitlinks
        locked_main, wave_ref = _verify_heads(
            repository,
            landing_tip,
            tested_tip=tested_tip,
        )
        forward_main_merges = _forward_main_merge_topology(
            repository,
            tested_main,
            tested_tip,
            landing_tip,
        )
        if forward_main_merges != prelocked_forward_main_merges:
            raise _Reject(
                RC_AUDIT,
                "forward main merge SHA closure changed before locked preflight",
            )
        fold_trusted_main_cutoff, landed_commits = _fold_landed_closure(
            repository,
            tested_main=tested_main,
            landing_tip=landing_tip,
            forward_main_merges=forward_main_merges,
        )
    except _Reject as exc:
        raise _Reject(
            exc.rc,
            exc.reason,
            release_safe=active_plan is None,
            retryable_same_request=exc.retryable_same_request,
        ) from exc
    if (
        active_plan is None
        and landing_tip != tested_tip
        and locked_main != landing_tip
    ):
        try:
            _verify_locked_forward_main(
                repository,
                locked_main,
                landing_tip,
                forward_main_merges,
            )
        except _Reject as exc:
            return LandResult(
                exc.rc,
                "stale-main",
                exc.reason,
                locked_main,
                locked_main,
                landing_tip,
                release_safe=True,
                retryable_same_request=exc.retryable_same_request,
            )
    if active_plan is None and locked_main != landing_tip and not _main_is_allowed(
        repository,
        locked_main,
        tested_main,
        tested_tip,
        audited,
        landing_tip=landing_tip,
        forward_main_merges=forward_main_merges,
    ):
        return LandResult(
            RC_STALE_MAIN,
            "stale-main",
            "main moved outside the tested audited closure while locking",
            locked_main,
            locked_main,
            landing_tip,
            release_safe=True,
        )
    fingerprint = _land_fingerprint(
        repository,
        current=locked_main,
        tested_tip=landing_tip,
        wave_head=landing_tip,
        control=control,
    )
    return _LockedPreflight(
        fold=fold,
        active_plan=active_plan,
        control=control,
        audited=audited,
        base_gitlinks=base_gitlinks,
        target_gitlinks=target_gitlinks,
        target_normal_entries=target_normal_entries,
        gitlinks_changed=gitlinks_changed,
        locked_main=locked_main,
        wave_ref=wave_ref,
        fingerprint=fingerprint,
        forward_main_merges=forward_main_merges,
        fold_trusted_main_cutoff=fold_trusted_main_cutoff,
        landed_commits=landed_commits,
    )


def _open_lock(repository: _Repository, lock: _LandLockHandle) -> None:
    try:
        lock.fd = os.open(
            _LOCK_NAME,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
            0o600,
            dir_fd=repository.common_fd,
        )
    except OSError as exc:
        raise _Reject(
            RC_IDENTITY,
            f"land lock open failed ({exc})",
            retryable_same_request=True,
        ) from exc
    metadata = os.fstat(lock.fd)
    if not _lock_metadata_is_safe(metadata):
        raise _Reject(RC_IDENTITY, "land lock has unsafe metadata")


def _provenance_checker_blob(repository: _Repository, revision: str) -> str:
    return _decode_sha(
        _require_git(
            _git(
                repository.wave,
                "rev-parse",
                "--verify",
                f"{revision}:tools/check_ai_provenance.py",
            ),
            "provenance checker blob",
            RC_PROVENANCE,
        ),
        "provenance checker blob",
        RC_PROVENANCE,
    )


def _provenance_checker_content_sha(
    repository: _Repository, revision: str
) -> str:
    content = _require_git(
        _git(
            repository.wave,
            "show",
            f"{revision}:tools/check_ai_provenance.py",
        ),
        "provenance checker content",
        RC_PROVENANCE,
    )
    return hashlib.sha256(content).hexdigest()


def _bind_provenance_checker(repository: _Repository) -> _ProvenanceCheckerBinding:
    """wave 側 checker の全 path component を symlink 非追従で束縛する。"""

    tools_fd = _openat_dir(
        repository.wave_fd,
        b"tools",
        "wave tools",
        rc=RC_PROVENANCE,
    )
    checker = _ProvenanceCheckerBinding(
        repository.wave / "tools" / "check_ai_provenance.py",
        tools_fd,
        -1,
    )
    try:
        try:
            before = os.stat(
                b"check_ai_provenance.py",
                dir_fd=tools_fd,
                follow_symlinks=False,
            )
            checker.checker_fd = os.open(
                b"check_ai_provenance.py",
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=tools_fd,
            )
            opened = os.fstat(checker.checker_fd)
        except OSError as exc:
            raise _Reject(
                RC_PROVENANCE,
                f"provenance checker open failed ({exc})",
            ) from exc
        if not stat.S_ISREG(opened.st_mode) or not _same_inode(before, opened):
            raise _Reject(
                RC_PROVENANCE,
                "provenance checker is symlink/raced/non-regular",
            )
        current = checker.path.stat(follow_symlinks=False)
        if not _same_inode(opened, current):
            raise _Reject(
                RC_PROVENANCE,
                "provenance checker pathname/inode mismatch",
            )
        return checker
    except BaseException:
        checker.close()
        raise


_PROVENANCE_AUDIT_TIMEOUT_S = 480
_PROVENANCE_OUTER_DEADLINE_ENV = "IZANAGI_PROVENANCE_OUTER_DEADLINE_MONOTONIC"


def _run_provenance_checker(
    checker: _ProvenanceCheckerBinding,
    repository: _Repository,
    env: dict[str, str],
) -> subprocess.CompletedProcess[bytes]:
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env[_PROVENANCE_OUTER_DEADLINE_ENV] = repr(time.monotonic() + _PROVENANCE_AUDIT_TIMEOUT_S)
    return subprocess.run(
        [sys.executable, str(checker.path)],
        cwd=repository.wave,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        close_fds=True,
        timeout=_PROVENANCE_AUDIT_TIMEOUT_S,
    )


def _audit_provenance_history(repository: _Repository) -> _ProvenanceReceipt:
    """lock 外で wave tip の full-history provenance 監査を実行する。

    pathname 実行の前後に、束縛 FD の bytes と commit blob 内容の SHA-256 を
    照合する。実行中だけ pathname を一時差し替えて終了前に戻す race は、実行後の
    再読でも観測できない残余窓として残る。
    """

    try:
        tip_sha = _head(repository.wave, "provenance audit wave")
        checker_blob_sha = _provenance_checker_blob(repository, tip_sha)
        committed_bytes_sha = _provenance_checker_content_sha(repository, tip_sha)
        checker = _bind_provenance_checker(repository)
        env = _git_env()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            executed_bytes_sha = checker.bytes_sha256()
            if executed_bytes_sha != committed_bytes_sha:
                raise _Reject(
                    RC_PROVENANCE,
                    "provenance checker bound bytes do not match the committed blob",
                )
            completed = _run_provenance_checker(checker, repository, env)
            checker.verify(repository)
            after_bytes_sha = checker.bytes_sha256()
            if (
                after_bytes_sha != executed_bytes_sha
                or after_bytes_sha != committed_bytes_sha
            ):
                raise _Reject(
                    RC_PROVENANCE,
                    "provenance checker bound bytes changed during the audit",
                )
        finally:
            checker.close()
        return _ProvenanceReceipt(
            tip_sha=tip_sha,
            checker_blob_sha=checker_blob_sha,
            executed_bytes_sha=executed_bytes_sha,
            returncode=completed.returncode,
        )
    except _Reject as exc:
        if exc.rc == RC_PROVENANCE:
            if exc.release_safe or exc.retryable_same_request:
                raise
            raise _Reject(
                RC_PROVENANCE,
                exc.reason,
                retryable_same_request=True,
            ) from exc
        raise _Reject(
            RC_PROVENANCE,
            f"provenance audit failed ({exc.reason})",
            retryable_same_request=True,
        ) from exc
    except BaseException as exc:
        detail = ""
        if isinstance(exc, subprocess.TimeoutExpired):
            detail = f" after {_PROVENANCE_AUDIT_TIMEOUT_S} seconds"
        raise _Reject(
            RC_PROVENANCE,
            f"provenance audit failed: {type(exc).__name__}{detail}: {exc}",
            retryable_same_request=True,
        ) from exc


def _reject_provenance_returncode(returncode: int) -> None:
    """Share the authoritative violation versus infrastructure classification."""
    if returncode == _PROVENANCE_VIOLATION_RC:
        raise _Reject(
            RC_PROVENANCE,
            f"provenance full-history audit rejected the wave (rc={returncode})",
            release_safe=True,
        )
    if returncode != 0:
        raise _Reject(
            RC_PROVENANCE,
            f"provenance full-history audit did not complete authoritatively "
            f"(rc={returncode})",
            retryable_same_request=True,
        )


def _verify_provenance_receipt(
    repository: _Repository,
    receipt: _ProvenanceReceipt,
    tested_tip: str,
) -> None:
    """lock 内で監査対象・checker blob・実行 bytes・子 rc を再照合する。"""

    try:
        if receipt.tip_sha != tested_tip:
            raise _Reject(
                RC_PROVENANCE,
                "provenance audit tip does not match the tested wave tip",
            )
        checker_blob_sha = _provenance_checker_blob(repository, tested_tip)
        if receipt.checker_blob_sha != checker_blob_sha:
            raise _Reject(
                RC_PROVENANCE,
                "provenance checker blob changed after the audit",
            )
        committed_bytes_sha = _provenance_checker_content_sha(
            repository, tested_tip
        )
        if receipt.executed_bytes_sha != committed_bytes_sha:
            raise _Reject(
                RC_PROVENANCE,
                "provenance checker executed bytes do not match the committed blob",
            )
        _reject_provenance_returncode(receipt.returncode)
    except _Reject as exc:
        if exc.rc == RC_PROVENANCE:
            if exc.release_safe or exc.retryable_same_request:
                raise
            raise _Reject(
                RC_PROVENANCE,
                exc.reason,
                retryable_same_request=True,
            ) from exc
        raise _Reject(
            RC_PROVENANCE,
            f"provenance receipt verification failed ({exc.reason})",
            retryable_same_request=True,
        ) from exc
    except BaseException as exc:
        raise _Reject(
            RC_PROVENANCE,
            f"provenance receipt verification failed: {type(exc).__name__}: {exc}",
            retryable_same_request=True,
        ) from exc


def _fold_gate_budgets() -> _FoldGateBudgets:
    budgets = _FoldGateBudgets(
        _FOLD_GATE_INNER_TIMEOUT_SECONDS,
        _FOLD_GATE_TERMINATION_GRACE_SECONDS,
        _FOLD_GATE_OUTER_TIMEOUT_SECONDS,
    )
    if (
        any(
            type(value) not in {int, float} or value <= 0
            for value in (
                budgets.inner_seconds,
                budgets.termination_grace_seconds,
                budgets.outer_seconds,
            )
        )
        or not (
            budgets.inner_seconds + budgets.termination_grace_seconds
            < budgets.outer_seconds
        )
    ):
        raise _FoldGateFailure(
            "fold gate time budget invariant failed: inner + termination "
            "grace must be smaller than outer"
        )
    return budgets


def _fold_gate_environment() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _FOLD_GATE_ENV_REMOVE
    }
    env.update(dict(_FOLD_GATE_ENV_FORCE))
    return env


def _fold_gate_environment_with_tmp(tmp_directory: Path) -> dict[str, str]:
    env = _fold_gate_environment()
    value = str(tmp_directory)
    env.update({"TMPDIR": value, "TMP": value, "TEMP": value})
    return env


def _load_fold_gate_registry(repo: Path):
    source = repo / "orchestrator" / "tests" / "fold_gate_nodes.py"
    if source.is_symlink() or not source.is_file():
        raise _FoldGateFailure("fold gate registry module is unavailable")
    name = (
        "_izanagi_fold_gate_nodes_"
        + hashlib.sha256(str(source).encode()).hexdigest()[:12]
    )
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise _FoldGateFailure("cannot create fold gate registry import spec")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    previous_sys_path = sys.path[:]
    sys.modules[name] = module
    sys.dont_write_bytecode = True
    try:
        sys.path.insert(0, str(repo))
        spec.loader.exec_module(module)
    except BaseException as exc:
        raise _FoldGateFailure(
            f"fold gate registry import failed: {type(exc).__name__}: {exc}"
        ) from exc
    finally:
        sys.path[:] = previous_sys_path
        sys.dont_write_bytecode = previous_dont_write_bytecode
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


def _fold_gate_target_raw_digests(
    plan: object,
) -> tuple[tuple[str, str], ...]:
    targets = getattr(plan, "targets", None)
    if not isinstance(targets, tuple) or not targets:
        raise _FoldGateFailure("non-noop fold plan has no target tuple")
    values: list[tuple[str, str]] = []
    for target in targets:
        relative = _fold_relative_path(getattr(target, "path", None))
        after_bytes = getattr(target, "after_bytes", None)
        after_sha256 = getattr(target, "after_sha256", None)
        if (
            type(after_bytes) is not bytes
            or type(after_sha256) is not str
            or _SHA256_RE.fullmatch(after_sha256) is None
        ):
            raise _FoldGateFailure(
                f"fold target raw payload is invalid: {relative}"
            )
        observed = hashlib.sha256(after_bytes).hexdigest()
        if observed != after_sha256:
            raise _FoldGateFailure(
                f"fold target raw digest mismatch: {relative}"
            )
        values.append((relative, observed))
    materialized = tuple(values)
    if materialized != tuple(sorted(set(materialized))):
        raise _FoldGateFailure(
            "fold target raw digest paths are not sorted and unique"
        )
    return materialized


def _expected_fold_target_paths(
    plan: object,
    *,
    repo: Path | None = None,
) -> tuple[str, ...]:
    """fragment path と rotation shape だけから必須 target を独立導出する。"""

    if getattr(plan, "status", None) == "noop":
        return ()
    expected = {"docs/spool/FOLDED.md"}
    fragments = getattr(plan, "fragments", None)
    if not isinstance(fragments, tuple) or not fragments:
        raise _FoldGateFailure("non-noop fold plan has no fragment ledger")
    for fragment in fragments:
        relative = _fold_relative_path(getattr(fragment, "path", None))
        if relative.startswith("docs/spool/worklog/"):
            expected.add("docs/worklog.md")
            fragment_path = None if repo is None else repo / relative
            if fragment_path is not None and fragment_path.is_file():
                try:
                    raw = fragment_path.read_bytes()
                    text = raw.decode("utf-8", errors="strict")
                except (OSError, UnicodeError) as exc:
                    raise _FoldGateInfrastructureFailure(
                        f"worklog fragment cannot be inspected: {relative}: {exc}"
                    ) from exc
                if hashlib.sha256(raw).hexdigest() != getattr(
                    fragment, "content_sha256", None
                ):
                    raise _FoldGateFailure(
                        f"worklog fragment digest changed: {relative}"
                    )
                if re.search(
                    r"^### (?:見送り|見送り追記)$",
                    text,
                    re.MULTILINE,
                ):
                    expected.add("docs/phase3.md")
        elif relative.startswith("docs/spool/decisions/"):
            expected.add("docs/decisions.md")
        elif relative.startswith("docs/spool/failures/"):
            expected.add("docs/failures.md")
        else:
            raise _FoldGateFailure(
                f"fold fragment is outside a known ledger: {relative}"
            )
    rotation_path = getattr(plan, "rotation_path", None)
    if rotation_path is not None:
        expected.add(_fold_relative_path(rotation_path))
        expected.add("docs/archive/README.md")
    return tuple(sorted(expected))


def _fold_gate_target_families(
    expected_targets: Sequence[str],
    *,
    rotation_path: str | None,
) -> tuple[str, ...]:
    families: set[str] = set()
    for relative in expected_targets:
        if relative == "docs/worklog.md":
            families.add("worklog")
        elif relative == "docs/decisions.md":
            families.add("decisions")
        elif relative == "docs/failures.md":
            families.add("failures")
        elif relative == "docs/phase3.md":
            families.add("phase3")
        elif relative == "docs/spool/FOLDED.md":
            families.add("folded")
        elif relative == "docs/archive/README.md":
            families.add("archive")
            if rotation_path is not None:
                families.add("rotation")
        elif rotation_path is not None and relative == rotation_path:
            families.update(("archive", "rotation"))
        else:
            raise _FoldGateFailure(
                f"fold gate cannot classify expected target family: {relative}"
            )
    return tuple(sorted(families))


def _folded_receipt_identity(record: object) -> tuple[str, str, int, str] | None:
    if not isinstance(record, dict):
        return None
    authored = record.get("authored")
    wave = record.get("wave")
    seq = record.get("seq")
    content_sha256 = record.get("content_sha256")
    if (
        type(authored) is not str
        or type(wave) is not str
        or type(seq) is not int
        or seq <= 0
        or type(content_sha256) is not str
        or _SHA256_RE.fullmatch(content_sha256) is None
    ):
        return None
    return authored, wave, seq, content_sha256


def _folded_receipt_identities(raw: bytes) -> tuple[tuple[str, str, int, str], ...]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise _FoldGateFailure("FOLDED after bytes are not UTF-8") from exc
    identities: list[tuple[str, str, int, str]] = []
    for line in text.splitlines():
        if not line.startswith("- "):
            continue
        try:
            record = json.loads(
                line[2:],
                object_pairs_hook=_no_duplicate_json_keys,
            )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise _FoldGateFailure("FOLDED receipt JSON is malformed") from exc
        identity = _folded_receipt_identity(record)
        if identity is None:
            raise _FoldGateFailure("FOLDED receipt identity is malformed")
        identities.append(identity)
    return tuple(identities)


def _verify_folded_fragment_receipts(repo: Path, plan: object) -> None:
    folded = next(
        (
            target
            for target in getattr(plan, "targets", ())
            if getattr(target, "path", None) == "docs/spool/FOLDED.md"
        ),
        None,
    )
    if folded is None:
        raise _FoldGateFailure("fold plan has no FOLDED target")
    before_path = repo / "docs/spool/FOLDED.md"
    try:
        before = before_path.read_bytes()
    except OSError as exc:
        raise _FoldGateInfrastructureFailure(
            f"FOLDED before bytes cannot be read: {exc}"
        ) from exc
    if hashlib.sha256(before).hexdigest() != getattr(
        folded, "before_sha256", None
    ):
        raise _FoldGateFailure("FOLDED before bytes do not match the plan")
    after = getattr(folded, "after_bytes", None)
    if type(after) is not bytes:
        raise _FoldGateFailure("FOLDED target has no raw after bytes")
    if not after.startswith(before):
        raise _FoldGateFailure("FOLDED existing receipt bytes changed")
    before_identities = _folded_receipt_identities(before)
    after_identities = _folded_receipt_identities(after)
    if after_identities[:len(before_identities)] != before_identities:
        raise _FoldGateFailure("FOLDED existing receipt prefix changed")
    new_identities = after_identities[len(before_identities):]
    expected: list[tuple[str, str, int, str]] = []
    for fragment in getattr(plan, "fragments", ()):
        relative = _fold_relative_path(getattr(fragment, "path", None))
        parts = relative.split("/")
        authored = getattr(fragment, "authored", None)
        wave = getattr(fragment, "wave", None)
        seq = getattr(fragment, "seq", None)
        content_sha256 = getattr(fragment, "content_sha256", None)
        if (
            len(parts) != 4
            or parts[:2] != ["docs", "spool"]
            or parts[2] not in _FOLD_LEDGERS
            or type(authored) is not str
            or type(wave) is not str
            or type(seq) is not int
            or parts[3] != f"{authored}-{wave}-{seq}.md"
            or type(content_sha256) is not str
            or _SHA256_RE.fullmatch(content_sha256) is None
        ):
            raise _FoldGateFailure(
                f"fragment path/content identity is malformed: {relative}"
            )
        expected.append((authored, wave, seq, content_sha256))
    if tuple(sorted(new_identities)) != tuple(sorted(expected)):
        raise _FoldGateFailure(
            "FOLDED new receipts do not match fragment path/content digests"
        )


def _select_fold_gate_nodes(repo: Path, plan: object) -> _FoldGateSelection:
    actual_targets = {path for path, _digest in _fold_gate_target_raw_digests(plan)}
    expected_targets = _expected_fold_target_paths(plan, repo=repo)
    missing = set(expected_targets) - actual_targets
    if missing:
        raise _FoldGateFailure(
            "fold plan omits independently expected targets: "
            + ", ".join(sorted(missing))
        )
    unexpected = actual_targets - set(expected_targets)
    if unexpected:
        raise _FoldGateFailure(
            "fold plan has targets outside the independently expected set: "
            + ", ".join(sorted(unexpected))
        )
    registry = _load_fold_gate_registry(repo)
    selected_rows = getattr(registry, "FOLD_GATE_SELECTED_NODES", None)
    registry_digest = getattr(
        registry, "FOLD_GATE_NODE_REGISTRY_SHA256", None
    )
    digest_function = getattr(
        registry, "fold_gate_node_registry_sha256", None
    )
    if (
        not isinstance(selected_rows, Mapping)
        or type(registry_digest) is not str
        or _SHA256_RE.fullmatch(registry_digest) is None
        or not callable(digest_function)
        or digest_function() != registry_digest
    ):
        raise _FoldGateFailure("fold gate registry contract is invalid")
    rotation_path = getattr(plan, "rotation_path", None)
    if rotation_path is not None:
        rotation_path = _fold_relative_path(rotation_path)
    target_families = _fold_gate_target_families(
        expected_targets,
        rotation_path=rotation_path,
    )
    target_family_set = set(target_families)
    nodeids: list[str] = []
    node_families: list[tuple[str, tuple[str, ...]]] = []
    covered: set[str] = set()
    for nodeid, row in sorted(selected_rows.items()):
        families = getattr(row, "target_family", None)
        if (
            type(nodeid) is not str
            or type(families) is not tuple
            or any(type(family) is not str for family in families)
        ):
            raise _FoldGateFailure("fold gate registry row is invalid")
        if (
            getattr(row, "requires_git_history", False)
            or getattr(row, "requires_submodules", False)
        ):
            if target_family_set.intersection(families):
                raise _FoldGateFailure(
                    f"fold gate capability mismatch for node: {nodeid}"
                )
            continue
        overlap = target_family_set.intersection(families)
        if overlap:
            nodeids.append(nodeid)
            covered.update(overlap)
            node_families.append((nodeid, tuple(sorted(overlap))))
    return _FoldGateSelection(
        registry_digest,
        tuple(nodeids),
        target_families,
        tuple(sorted(target_family_set - covered)),
        tuple(node_families),
    )


def _registered_worktree_paths(repository: _Repository) -> tuple[Path, ...]:
    raw = _require_git(
        _git(repository.wave, "worktree", "list", "--porcelain"),
        "fold gate registered worktree list",
        RC_FOLD_GATE,
    )
    paths: list[Path] = []
    for record in raw.splitlines():
        if not record.startswith(b"worktree "):
            continue
        try:
            path = Path(os.fsdecode(record.removeprefix(b"worktree ")))
            try:
                path = path.resolve(strict=True)
            except FileNotFoundError:
                path = path.absolute()
            paths.append(path)
        except (OSError, UnicodeError) as exc:
            raise _FoldGateFailure(
                f"registered worktree path cannot be resolved: {exc}"
            ) from exc
    if not paths:
        raise _FoldGateFailure("registered worktree list is empty")
    return tuple(paths)


def _paths_overlap_absolute(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _safe_archive_relative(value: str) -> Path:
    path = Path(value)
    if (
        not value
        or "\\" in value
        or "\0" in value
        or "\n" in value
        or path.is_absolute()
        or path.as_posix().rstrip("/") != value.rstrip("/")
        or any(part in {"", ".", "..", ".git"} for part in path.parts)
    ):
        raise _FoldGateFailure(f"unsafe tracked archive path: {value!r}")
    return path


def _require_real_parent(root: Path, relative: Path) -> Path:
    current = root
    for part in relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise _FoldGateFailure(
                f"tracked archive parent is a symlink: {relative.as_posix()}"
            )
        if current.exists() and not current.is_dir():
            raise _FoldGateFailure(
                f"tracked archive parent is not a directory: {relative.as_posix()}"
            )
        current.mkdir(exist_ok=True)
    return current


def _export_tracked_tree(
    repository: _Repository,
    landing_tip: str,
    destination: Path,
) -> None:
    archive_bytes = _require_git(
        _git(repository.wave, "archive", "--format=tar", landing_tip),
        "fold gate tracked tree export",
        RC_FOLD_GATE,
    )
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
            members = archive.getmembers()
            for member in members:
                relative = _safe_archive_relative(member.name)
                path = destination / relative
                if member.isdir():
                    _require_real_parent(destination, relative)
                    if path.is_symlink() or (path.exists() and not path.is_dir()):
                        raise _FoldGateFailure(
                            f"tracked archive directory collision: {member.name}"
                        )
                    path.mkdir(exist_ok=True)
                elif member.isfile():
                    _require_real_parent(destination, relative)
                    if path.exists() or path.is_symlink():
                        raise _FoldGateFailure(
                            f"tracked archive file collision: {member.name}"
                        )
                    extracted = archive.extractfile(member)
                    if extracted is None:
                        raise _FoldGateFailure(
                            f"tracked archive file has no payload: {member.name}"
                        )
                    path.write_bytes(extracted.read())
                    path.chmod(member.mode & 0o777)
                elif member.issym():
                    _require_real_parent(destination, relative)
                    if path.exists() or path.is_symlink():
                        raise _FoldGateFailure(
                            f"tracked archive symlink collision: {member.name}"
                        )
                    path.symlink_to(member.linkname)
                else:
                    raise _FoldGateFailure(
                        f"unsupported tracked archive member: {member.name}"
                    )
    except (OSError, tarfile.TarError) as exc:
        raise _FoldGateFailure(
            f"fold gate tracked tree materialization failed: {exc}"
        ) from exc
    if (destination / ".git").exists() or (destination / ".git").is_symlink():
        raise _FoldGateFailure("isolated fold gate tree unexpectedly contains .git")


def _materialize_fold_plan(tree: Path, plan: object) -> None:
    receipts = {
        getattr(fragment, "path", None): fragment
        for fragment in getattr(plan, "fragments", ())
    }
    for target in getattr(plan, "targets", ()):
        relative_text = _fold_relative_path(getattr(target, "path", None))
        relative = Path(relative_text)
        parent = _require_real_parent(tree, relative)
        path = parent / relative.name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise _FoldGateFailure(
                f"fold gate target is symlink/non-regular: {relative_text}"
            )
        after_bytes = getattr(target, "after_bytes", None)
        after_sha256 = getattr(target, "after_sha256", None)
        if type(after_bytes) is not bytes:
            raise _FoldGateFailure(
                f"fold gate target has no raw bytes: {relative_text}"
            )
        path.write_bytes(after_bytes)
        path.chmod(0o644)
        if hashlib.sha256(path.read_bytes()).hexdigest() != after_sha256:
            raise _FoldGateFailure(
                f"fold gate target write hash mismatch: {relative_text}"
            )
    for relative_text in getattr(plan, "gc_paths", ()):
        relative_text = _fold_relative_path(relative_text)
        relative = Path(relative_text)
        parent = _require_real_parent(tree, relative)
        path = parent / relative.name
        if path.is_symlink() or not path.is_file():
            raise _FoldGateFailure(
                f"fold gate GC path is missing/symlink/non-regular: {relative_text}"
            )
        receipt = receipts.get(relative_text)
        expected = getattr(receipt, "content_sha256", None)
        if (
            type(expected) is not str
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise _FoldGateFailure(
                f"fold gate GC path digest mismatch: {relative_text}"
            )
        path.unlink()


def _run_fold_gate_pytest(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    termination_grace: float,
) -> subprocess.CompletedProcess[bytes]:
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        close_fds=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=termination_grace)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        timeout_error = subprocess.TimeoutExpired(
            argv,
            timeout,
            output=stdout,
            stderr=stderr,
        )
        timeout_error.returncode = process.returncode
        raise timeout_error from exc
    return subprocess.CompletedProcess(
        argv,
        process.returncode,
        stdout,
        stderr,
    )


def _fold_gate_diagnostic_tail(data: bytes | None) -> str:
    """子出力の末尾を有界かつ byte 単位で可逆な ASCII にする。"""

    raw = data or b""
    selected_reversed: list[str] = []
    used = 0
    retained = 0
    for value in reversed(raw):
        rendered = (
            chr(value)
            if 0x20 <= value < 0x7f and value != 0x5c
            else f"\\x{value:02x}"
        )
        width = len(rendered)
        if used + width > _FOLD_GATE_DIAGNOSTIC_TAIL_BYTES:
            break
        selected_reversed.append(rendered)
        used += width
        retained += 1
    selected_reversed.reverse()
    escaped = "".join(selected_reversed)
    return (
        f"omitted_bytes={len(raw) - retained},"
        f"escaped={json.dumps(escaped, ensure_ascii=True)}"
    )


def _fold_gate_pytest_diagnostic(
    *,
    returncode: int | None,
    stdout: bytes | None,
    stderr: bytes | None,
) -> str:
    rc = "unavailable" if returncode is None else str(returncode)
    return (
        f"pytest returncode={rc}; "
        f"stdout_tail({_fold_gate_diagnostic_tail(stdout)}); "
        f"stderr_tail({_fold_gate_diagnostic_tail(stderr)})"
    )


def _parse_fold_gate_junit(
    path: Path,
    nodeids: tuple[str, ...],
    node_families: tuple[tuple[str, tuple[str, ...]], ...] = (),
) -> _FoldGateJUnitCounts:
    try:
        root = _ET.fromstring(path.read_bytes())
    except (OSError, _ET.ParseError) as exc:
        raise _FoldGateInfrastructureFailure(
            f"fold gate JUnit cannot be parsed: {exc}"
        ) from exc
    cases = list(root.iter("testcase"))
    expected_names = {nodeid.split("::", 1)[1] for nodeid in nodeids}
    observed_names = [case.attrib.get("name") for case in cases]
    if (
        len(expected_names) != len(nodeids)
        or len(observed_names) != len(set(observed_names))
        or set(observed_names) != expected_names
    ):
        raise _FoldGateInfrastructureFailure(
            "fold gate JUnit node set mismatch: "
            f"expected={sorted(expected_names)!r}, actual={sorted(observed_names)!r}"
        )
    skipped = sum(case.find("skipped") is not None for case in cases)
    failed = sum(case.find("failure") is not None for case in cases)
    errors = sum(case.find("error") is not None for case in cases)
    counts = _FoldGateJUnitCounts(
        collected=len(cases),
        executed=len(cases) - skipped,
        skipped=skipped,
        failed=failed,
        errors=errors,
    )
    if counts.errors != 0:
        raise _FoldGateInfrastructureFailure(
            f"fold gate JUnit reported test errors: {counts}"
        )
    if counts.failed != 0:
        failed_names = {
            case.attrib.get("name")
            for case in cases
            if case.find("failure") is not None
        }
        failed_nodeids = {
            nodeid
            for nodeid in nodeids
            if nodeid.split("::", 1)[1] in failed_names
        }
        failed_families = tuple(sorted({
            family
            for nodeid, families in node_families
            if nodeid in failed_nodeids
            for family in families
        }))
        raise _FoldGateFailure(
            f"fold gate JUnit assertion failure: {counts}",
            covered_and_failed_families=failed_families,
        )
    if (
        counts.collected != len(nodeids)
        or counts.executed == 0
        or counts.skipped != 0
    ):
        raise _FoldGateFailure(f"fold gate JUnit rejected: {counts}")
    return counts


def _fold_gate_now() -> float:
    return time.monotonic()


class _FoldGateOuterWatchdog:
    """materialization から cleanup までを SIGALRM で監督する。"""

    def __init__(self, seconds: float):
        self.seconds = seconds
        self.deadline = 0.0
        self.previous_handler = None
        self.previous_timer = (0.0, 0.0)

    def _alarm(self, _signum, _frame) -> None:
        if _fold_gate_now() >= self.deadline:
            raise _FoldGateInfrastructureFailure(
                "fold gate outer watchdog fired after "
                f"{self.seconds:g} seconds"
            )

    def __enter__(self):
        if not hasattr(signal, "setitimer"):
            raise _FoldGateInfrastructureFailure(
                "fold gate outer watchdog is unavailable"
            )
        self.deadline = _fold_gate_now() + self.seconds
        self.previous_handler = signal.getsignal(signal.SIGALRM)
        self.previous_timer = signal.getitimer(signal.ITIMER_REAL)
        if self.previous_timer != (0.0, 0.0):
            raise _FoldGateInfrastructureFailure(
                "fold gate outer watchdog timer is already in use"
            )
        signal.signal(signal.SIGALRM, self._alarm)
        interval = min(self.seconds, 0.1)
        signal.setitimer(signal.ITIMER_REAL, interval, interval)
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        signal.setitimer(signal.ITIMER_REAL, 0.0, 0.0)
        signal.signal(signal.SIGALRM, self.previous_handler)


def _execute_fold_gate(
    repository: _Repository,
    plan: object,
    selection: _FoldGateSelection,
    landing_tip: str,
    budgets: _FoldGateBudgets,
) -> _FoldGateJUnitCounts | None:
    registered = _registered_worktree_paths(repository)
    with tempfile.TemporaryDirectory(
        prefix="izanagi-fold-gate-",
        dir="/tmp",
    ) as raw:
        tree = Path(raw).resolve(strict=True)
        if any(_paths_overlap_absolute(tree, path) for path in registered):
            raise _FoldGateFailure(
                "fold gate isolation directory overlaps a registered worktree"
            )
        try:
            _export_tracked_tree(repository, landing_tip, tree)
            _materialize_fold_plan(tree, plan)
        except _FoldGateInfrastructureFailure:
            raise
        except BaseException as exc:
            raise _FoldGateInfrastructureFailure(
                "fold gate materialization failed: "
                f"{type(exc).__name__}: {exc}",
                uncovered_families=selection.uncovered_families,
            ) from exc
        if not selection.nodeids:
            return None
        pytest_tmp = tree / ".fold-gate-tmp"
        pytest_tmp.mkdir(mode=0o700)
        junit = tree / ".fold-gate-junit.xml"
        argv = [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "junitxml",
            f"--junitxml={junit}",
            f"--basetemp={pytest_tmp}",
            *(
                f"orchestrator/tests/{nodeid}"
                for nodeid in selection.nodeids
            ),
        ]
        try:
            completed = _run_fold_gate_pytest(
                argv,
                cwd=tree,
                env=_fold_gate_environment_with_tmp(pytest_tmp),
                timeout=budgets.inner_seconds,
                termination_grace=budgets.termination_grace_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            diagnostic = _fold_gate_pytest_diagnostic(
                returncode=getattr(exc, "returncode", None),
                stdout=exc.output,
                stderr=exc.stderr,
            )
            raise _FoldGateInfrastructureFailure(
                f"fold gate pytest timed out after {budgets.inner_seconds:g} "
                f"seconds; {diagnostic}",
                uncovered_families=selection.uncovered_families,
            ) from exc
        except OSError as exc:
            diagnostic = _fold_gate_pytest_diagnostic(
                returncode=None,
                stdout=None,
                stderr=None,
            )
            raise _FoldGateInfrastructureFailure(
                f"fold gate pytest could not start: {exc}; {diagnostic}",
                uncovered_families=selection.uncovered_families,
            ) from exc
        try:
            counts = _parse_fold_gate_junit(
                junit,
                selection.nodeids,
                selection.node_families,
            )
        except _FoldGateInfrastructureFailure as exc:
            diagnostic = _fold_gate_pytest_diagnostic(
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
            raise _FoldGateInfrastructureFailure(
                f"{exc}; {diagnostic}",
                uncovered_families=selection.uncovered_families,
            ) from exc
        except _FoldGateFailure as exc:
            raise type(exc)(
                str(exc),
                uncovered_families=selection.uncovered_families,
                **(
                    {
                        "covered_and_failed_families": (
                            exc.covered_and_failed_families
                        )
                    }
                    if type(exc) is _FoldGateFailure
                    else {}
                ),
            ) from exc
        if completed.returncode != 0:
            diagnostic = _fold_gate_pytest_diagnostic(
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
            raise _FoldGateInfrastructureFailure(
                f"fold gate pytest returned nonzero; {diagnostic}; {counts}",
                uncovered_families=selection.uncovered_families,
            )
        return counts


def _run_fold_gate(
    repository: _Repository,
    plan: object,
    landing_tip: str,
) -> _FoldGateReceipt:
    try:
        budgets = _fold_gate_budgets()
        selection = _select_fold_gate_nodes(repository.wave, plan)
        _verify_folded_fragment_receipts(repository.wave, plan)
        with _FoldGateOuterWatchdog(budgets.outer_seconds):
            _execute_fold_gate(repository, plan, selection, landing_tip, budgets)
        receipt = _FoldGateReceipt(
            plan,
            getattr(plan, "transaction_id", ""),
            selection.registry_digest,
            selection.nodeids,
            _fold_gate_target_raw_digests(plan),
            _FOLD_GATE_OUTCOME,
            selection.uncovered_families,
        )
        _verify_fold_gate_receipt(repository.wave, receipt, plan)
        return receipt
    except _FoldGateFailure:
        raise
    except _Reject as exc:
        raise _FoldGateInfrastructureFailure(
            f"fold gate infrastructure failed: {exc.reason}",
            uncovered_families=(
                selection.uncovered_families
                if "selection" in locals()
                else ()
            ),
        ) from exc
    except Exception as exc:
        raise _FoldGateInfrastructureFailure(
            f"fold gate internal failure: {type(exc).__name__}: {exc}",
            uncovered_families=(
                selection.uncovered_families
                if "selection" in locals()
                else ()
            ),
        ) from exc


def _fold_gate_receipt_from_plan(plan: object) -> _FoldGateReceipt:
    durable = getattr(plan, "gate_receipt", None)
    if durable is None:
        raise _FoldGateFailure("stored fold plan has no gate receipt")
    try:
        return _FoldGateReceipt(
            plan,
            durable.transaction_id,
            durable.registry_digest,
            tuple(durable.nodeids),
            tuple(durable.target_raw_digests),
            durable.outcome,
            tuple(durable.uncovered_families),
        )
    except (AttributeError, TypeError) as exc:
        raise _FoldGateFailure("stored fold gate receipt is malformed") from exc


def _verify_fold_gate_receipt(
    repo: Path,
    receipt: _FoldGateReceipt,
    plan: object,
) -> _FoldGateSelection:
    selection = _select_fold_gate_nodes(repo, plan)
    raw_digests = _fold_gate_target_raw_digests(plan)
    if receipt.plan is not plan:
        raise _FoldGateFailure("fold gate receipt plan object identity mismatch")
    if receipt.transaction_id != getattr(plan, "transaction_id", None):
        raise _FoldGateFailure("fold gate receipt transaction_id mismatch")
    if receipt.target_raw_digests != raw_digests:
        raise _FoldGateFailure("fold gate receipt target raw digest mismatch")
    if (
        receipt.registry_digest != selection.registry_digest
        or receipt.nodeids != selection.nodeids
        or receipt.outcome != _FOLD_GATE_OUTCOME
        or receipt.uncovered_families != selection.uncovered_families
    ):
        raise _FoldGateFailure("fold gate receipt registry/outcome mismatch")
    return selection


def _fold_gate_durable_receipt(fold: object, receipt: _FoldGateReceipt):
    receipt_type = getattr(fold, "FoldGateReceipt", None)
    if receipt_type is None:
        return receipt
    return receipt_type(
        receipt.transaction_id,
        receipt.registry_digest,
        receipt.nodeids,
        receipt.target_raw_digests,
        receipt.outcome,
        receipt.uncovered_families,
    )


def _fold_gate_failed_result(
    reason: str,
    *,
    main_before: str | None,
    main_after: str | None,
    tested_tip: str,
    retryable_same_request: bool = False,
    uncovered_families: tuple[str, ...] = (),
    covered_and_failed_families: tuple[str, ...] = (),
) -> LandResult:
    return LandResult(
        RC_FOLD_GATE,
        "fold-gate-failed",
        reason,
        main_before,
        main_after,
        tested_tip,
        fold_gate_uncovered_families=uncovered_families,
        fold_gate_covered_and_failed_families=(
            covered_and_failed_families
        ),
        release_safe=not retryable_same_request,
        retryable_same_request=retryable_same_request,
    )


def _run_outside_land_lock(
    repository: _Repository,
    lock: _LandLockHandle,
    remaining_wait_s: float,
    runner,
) -> tuple[object, bool, float]:
    """guard 完了後、残りの累積競合待機予算で再取得する。"""

    lock.close()
    payload = runner()
    if isinstance(payload, _ProvenanceReceipt) and payload.returncode != 0:
        _reject_provenance_returncode(payload.returncode)
    acquired, waited = _acquire_land_lock_until_turn(repository, lock, remaining_wait_s)
    return payload, acquired, waited


def _pending_spool_paths(repo: Path) -> tuple[str, ...]:
    """正規 spool layout から pending 候補を列挙する。"""

    spool = repo / "docs" / "spool"
    if not spool.exists() or spool.is_symlink() or not spool.is_dir():
        raise OSError("docs/spool is not a real directory")
    pending: list[str] = []
    for ledger in _FOLD_LEDGERS:
        directory = spool / ledger
        if not directory.exists() or directory.is_symlink() or not directory.is_dir():
            raise OSError(f"docs/spool/{ledger} is not a real directory")
        for member in directory.iterdir():
            if member.name != "README.md":
                pending.append(member.relative_to(repo).as_posix())
    return tuple(sorted(pending))


def _verify_main_fold_closure_before_ff(
    repository: _Repository,
    landing_tip: str,
    plan: object,
    fold: object,
) -> None:
    """FF 後も生存する main 側 archive closure 差分を事前拒否する。"""

    raw = _require_git(
        _git(
            repository.wave,
            "ls-tree",
            "-r",
            "--name-only",
            "-z",
            landing_tip,
            "--",
            "docs/archive",
        ),
        "prospective fold archive closure",
        RC_FOLD_GATE,
    )
    fixed_paths = getattr(fold, "_CLOSURE_FIXED_PATHS", None)
    if (
        type(fixed_paths) is not tuple
        or not fixed_paths
        or any(type(path) is not str for path in fixed_paths)
    ):
        raise _FoldGateInfrastructureFailure(
            "fold engine closure fixed-path contract is unavailable"
        )
    expected = set(fixed_paths) | {
        os.fsdecode(path)
        for path in _nul_records(
            raw,
            "prospective fold archive closure",
            RC_FOLD_GATE,
        )
        if re.fullmatch(rb"docs/archive/worklog-[^/]+\.md", path)
    }
    rotation_path = getattr(plan, "rotation_path", None)
    if rotation_path is not None:
        expected.add(_fold_relative_path(rotation_path))

    archive = repository.main / "docs/archive"
    try:
        candidates = tuple(sorted({
            *(
                repository.main / relative
                for relative in fixed_paths
                if (repository.main / relative).exists()
                or (repository.main / relative).is_symlink()
            ),
            *archive.glob("worklog-*.md"),
        }))
    except OSError as exc:
        raise _FoldGateInfrastructureFailure(
            f"main fold archive closure cannot be enumerated: {exc}"
        ) from exc
    unexpected: list[str] = []
    shadowing: list[str] = []
    for path in candidates:
        relative = path.relative_to(repository.main).as_posix()
        if path.is_symlink() or not path.is_file():
            raise _FoldGateFailure(
                f"main fold archive closure is symlink/non-regular: {relative}"
            )
        tracked = _git(
            repository.main,
            "ls-files",
            "--error-unmatch",
            "--",
            relative,
        )
        if tracked.returncode == 0:
            continue
        if tracked.returncode != 1:
            raise _FoldGateInfrastructureFailure(
                "main fold archive tracked-state inspection failed: "
                + (_detail(tracked.stderr) or "no detail")
            )
        if relative in expected:
            shadowing.append(relative)
        else:
            unexpected.append(relative)
    if unexpected or shadowing:
        raise _FoldGateFailure(
            "main has surviving untracked fold closure candidates: "
            f"unexpected={unexpected!r}, shadowing={shadowing!r}"
        )


def _verify_supervised_fragment_wave(wave_ref: str, plan: object) -> None:
    """daemon 生成 branch identity を計画内の全 fragment へ束縛する。"""
    if not wave_ref.startswith("refs/heads/dev-wave/dw-"):
        return
    match = _SUPERVISED_WAVE_REF_RE.fullmatch(wave_ref)
    if match is None:
        raise RuntimeError("noncanonical branch in the supervised namespace")
    wave_index = int(match.group("wave"))
    run_id = match.group("run")
    slug = supervised_spool_wave_slug(run_id, wave_index)
    expected_ref = f"refs/heads/dev-wave/{run_id}/w{wave_index:03d}"
    if wave_ref != expected_ref:
        raise RuntimeError("noncanonical branch in the supervised namespace")
    fragments = getattr(plan, "fragments", None)
    if not isinstance(fragments, tuple):
        raise RuntimeError("supervised fold plan has no closed fragment tuple")
    mismatches = [
        getattr(fragment, "wave", None)
        for fragment in fragments
        if getattr(fragment, "wave", None) != slug
    ]
    if mismatches:
        raise RuntimeError("supervised fragment wave does not match the branch-derived slug")


def _land_fold_date() -> str:
    """この land request が plan へ束縛する canonical date。"""

    return _datetime.datetime.now().astimezone().date().isoformat()


def _load_spool_fold():
    """同じ checkout の fold engine を lazy import する。"""

    source = Path(__file__).resolve().with_name("spool_fold.py")
    if source.is_symlink() or not source.is_file():
        raise RuntimeError("tools/spool_fold.py is not a regular file")
    name = f"_izanagi_land_spool_fold_{hashlib.sha256(str(source).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot create spool_fold import spec")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.modules[name] = module
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


def _fold_relative_path(value: object) -> str:
    if not isinstance(value, str):
        raise RuntimeError("fold plan path is not text")
    path = Path(value)
    if (
        path.is_absolute()
        or "\\" in value
        or "\0" in value
        or "\n" in value
        or path.as_posix() != value
        or not path.parts
        or path.parts[0] != "docs"
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise RuntimeError(f"unsafe fold plan path: {value!r}")
    return value


def _fold_plan_paths(plan: object) -> tuple[str, ...]:
    targets = getattr(plan, "targets", ())
    gc_paths = getattr(plan, "gc_paths", ())
    values = [
        *(_fold_relative_path(getattr(target, "path", None)) for target in targets),
        *(_fold_relative_path(path) for path in gc_paths),
    ]
    if len(values) != len(set(values)):
        # target と GC の重複も transaction の意味が曖昧なので拒否する。
        raise RuntimeError("fold plan contains duplicate target paths")
    return tuple(sorted(values))


def _snapshot_fold_paths(repo: Path, relatives: Sequence[str]) -> tuple[_PathSnapshot, ...]:
    snapshots: list[_PathSnapshot] = []
    for relative in relatives:
        path = repo / relative
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            snapshots.append(_PathSnapshot(relative, False, b"", 0))
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"fold path is symlink/non-regular: {relative}")
        snapshots.append(
            _PathSnapshot(
                relative,
                True,
                path.read_bytes(),
                stat.S_IMODE(metadata.st_mode),
            )
        )
    return tuple(snapshots)


def _atomic_restore(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.land-rollback.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _restore_fold_paths(repo: Path, snapshots: Sequence[_PathSnapshot]) -> None:
    for snapshot in snapshots:
        path = repo / snapshot.relative
        if snapshot.existed:
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise RuntimeError(f"rollback path is symlink/non-regular: {snapshot.relative}")
            _atomic_restore(path, snapshot.content, snapshot.mode)
        elif path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file():
                raise RuntimeError(f"new fold path became symlink/non-regular: {snapshot.relative}")
            path.unlink()


def _fold_index_tree(repository: _Repository) -> str:
    return _decode_sha(
        _require_git(
            _git(repository.main, "write-tree"),
            "fold preflight index tree",
            RC_FOLD_FAILED,
        ),
        "fold preflight index tree",
        RC_FOLD_FAILED,
    )


def _fold_ref_tree(repository: _Repository, revision: str) -> str:
    return _decode_sha(
        _require_git(
            _git(repository.main, "rev-parse", "--verify", f"{revision}^{{tree}}"),
            "fold rollback ref tree",
            RC_FOLD_RECOVERY_FAILED,
        ),
        "fold rollback ref tree",
        RC_FOLD_RECOVERY_FAILED,
    )


def _fsync_directory(path: Path) -> None:
    directory_fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _rollback_fold(
    repository: _Repository,
    *,
    rollback_ref: str,
    expected_tip: str,
    index_tree: str,
    snapshots: Sequence[_PathSnapshot],
    state_path: Path,
    expected_transaction_id: str,
) -> list[str]:
    failures: list[str] = []
    try:
        current = _head(repository.main, "main fold rollback")
        if current != expected_tip:
            parent = _git(repository.main, "rev-parse", "--verify", f"{current}^")
            observed_parent = (
                _decode_sha(parent.stdout, "fold commit parent", RC_FOLD_FAILED)
                if parent.returncode == 0
                else None
            )
            if observed_parent != expected_tip:
                failures.append("main moved beyond the fold commit; ref rollback refused")
        if not failures and current != rollback_ref:
            update = _git(
                repository.main,
                "update-ref", "refs/heads/main", rollback_ref, current,
            )
            if update.returncode != 0:
                failures.append(
                    "fold/main ref CAS rollback failed "
                    f"({_detail(update.stderr) or 'no detail'})"
                )
        if not failures:
            read_tree = _git(repository.main, "read-tree", "--reset", "-u", index_tree)
            if read_tree.returncode != 0:
                failures.append(
                    f"fold index/worktree rollback failed ({_detail(read_tree.stderr) or 'no detail'})"
                )
        if not failures:
            _restore_fold_paths(repository.main, snapshots)
        if state_path.exists() or state_path.is_symlink():
            metadata = state_path.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                failures.append("fold transaction state is symlink/non-regular")
            else:
                try:
                    state = json.loads(state_path.read_bytes().decode("utf-8", errors="strict"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    failures.append(
                        "fold transaction state transaction_id cannot be verified "
                        f"({type(exc).__name__}: {exc})"
                    )
                else:
                    observed_transaction_id = (
                        state.get("transaction_id") if type(state) is dict else None
                    )
                    if observed_transaction_id != expected_transaction_id:
                        failures.append(
                            "fold transaction state transaction_id does not match "
                            "the rollback plan; state preserved"
                        )
                    elif not failures:
                        state_path.unlink()
                        _fsync_directory(state_path.parent)
    except (OSError, RuntimeError, _Reject) as exc:
        failures.append(f"fold rollback raised {type(exc).__name__}: {exc}")
    return failures


def _validate_generated_docs(repository: _Repository, plan: object) -> None:
    """apply 済み・未 commit の canonical を既存 docs gate で検査する。"""

    checker = repository.main / "tools" / "check_docs.py"
    if checker.is_symlink() or not checker.is_file():
        raise RuntimeError("tools/check_docs.py is unavailable for generated canonical validation")
    env = _git_env()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            str(checker),
            "--expect-active-transaction",
            getattr(plan, "transaction_id"),
        ],
        cwd=repository.main,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        close_fds=True,
    )
    if completed.returncode != 0:
        detail = _detail(completed.stderr) or _detail(completed.stdout) or "no detail"
        raise RuntimeError(f"generated canonical validation failed ({detail})")


def _preflight_fold_message(repository: _Repository, message_path: Path) -> None:
    checker = repository.main / "tools" / "check_ai_provenance.py"
    if checker.is_symlink() or not checker.is_file():
        raise RuntimeError("tools/check_ai_provenance.py is unavailable for message preflight")
    completed = subprocess.run(
        [sys.executable, str(checker), "--message-file", str(message_path)],
        cwd=repository.main,
        env={**_git_env(), "PYTHONDONTWRITEBYTECODE": "1"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        close_fds=True,
    )
    if completed.returncode != 0:
        detail = _detail(completed.stderr) or _detail(completed.stdout) or "no detail"
        raise RuntimeError(f"fold commit message preflight failed ({detail})")


def _verify_fold_postconditions(
    repository: _Repository,
    *,
    fold_commit: str,
    expected_parent: str,
    trusted_main_cutoff_sha: str,
    tested_tip: str,
    landed_commits: Sequence[str],
    wave_ref: str,
) -> None:
    parent = _decode_sha(
        _require_git(
            _git(repository.main, "rev-parse", "--verify", f"{fold_commit}^"),
            "fold commit parent",
            RC_FOLD_FAILED,
        ),
        "fold commit parent",
        RC_FOLD_FAILED,
    )
    if parent != expected_parent:
        raise RuntimeError("fold commit parent is not the ff-only result")
    if _symbolic_head(repository.main, "main post-fold") != "refs/heads/main":
        raise RuntimeError("main symbolic HEAD moved during fold")
    if _ref_sha(repository.main, "refs/heads/main", "main post-fold ref") != fold_commit:
        raise RuntimeError("main ref does not equal fold commit")
    if _head(repository.wave, "wave post-fold") != tested_tip:
        raise RuntimeError("wave HEAD moved during fold")
    if _symbolic_head(repository.wave, "wave post-fold") != wave_ref:
        raise RuntimeError("wave symbolic ref moved during fold")
    if _ref_sha(repository.wave, wave_ref, "wave post-fold ref") != tested_tip:
        raise RuntimeError("wave ref moved during fold")
    _verify_main_no_tracked_dirt(repository)
    _verify_wave_clean(repository)
    if _pending_spool_paths(repository.main):
        raise RuntimeError("pending fragments reappeared after fold commit")
    declared = verify_declared_fold_commit(
        repository.main,
        fold_commit_sha=fold_commit,
        trusted_main_cutoff_sha=trusted_main_cutoff_sha,
        landed_main_sha=fold_commit,
        landed_commits=landed_commits,
        wave_tip=tested_tip,
    )
    if not declared.ok:
        raise RuntimeError(f"declared fold shape rejected: {declared.detail}")


def _fold_main_locked(
    repository: _Repository,
    successful_land: LandResult,
    *,
    fold: object,
    plan: object,
    trusted_main_cutoff_sha: str,
    tested_tip: str,
    landed_commits: Sequence[str],
    wave_ref: str,
    rollback_ref: str,
    snapshots: Sequence[_PathSnapshot],
    index_tree: str,
    state_path: Path,
    fold_gate_receipt: _FoldGateReceipt | None = None,
) -> LandResult:
    """preplanned fold を lock 内で apply・検査・commit する。"""

    fold_base = successful_land.main_after
    if fold_base is None:
        return LandResult(
            RC_FOLD_FAILED,
            "fold-failed",
            "successful land did not expose main_after",
            successful_land.main_before,
            successful_land.main_after,
            tested_tip,
        )

    apply_started = False
    message_path: Path | None = None
    try:
        if getattr(plan, "status", None) == "noop":
            return successful_land
        if getattr(getattr(plan, "origin", None), "kind", None) == "land":
            if fold_gate_receipt is None:
                raise _FoldGateFailure("land fold has no verified gate receipt")
            _verify_fold_gate_receipt(
                repository.wave,
                fold_gate_receipt,
                plan,
            )
        fold_paths = _fold_plan_paths(plan)
        _land_turn_mutating(
            repository, plan=plan, main_before=rollback_ref, landing_tip=tested_tip,
            wave_ref=wave_ref, trusted_main_cutoff=trusted_main_cutoff_sha,
            landed_commits=landed_commits,
        )
        apply_started = True
        fold.apply_fold(
            repository.main,
            plan,
            gate_receipt=(
                None
                if fold_gate_receipt is None
                else _fold_gate_durable_receipt(fold, fold_gate_receipt)
            ),
        )
        _validate_generated_docs(repository, plan)
        pending_after = _pending_spool_paths(repository.main)
        if pending_after:
            raise RuntimeError(
                "pending fragment postcondition failed: " + ", ".join(pending_after)
            )

        staged = _git(repository.main, "add", "--", *fold_paths)
        if staged.returncode != 0:
            raise RuntimeError(
                f"fold staging failed ({_detail(staged.stderr) or 'no detail'})"
            )
        cached = _git(
            repository.main,
            "diff", "--cached", "--name-only", "-z", "--no-renames",
        )
        if cached.returncode != 0:
            raise RuntimeError(
                f"fold staged path inspection failed ({_detail(cached.stderr) or 'no detail'})"
            )
        staged_paths = set(_nul_records(cached.stdout, "fold staged paths", RC_FOLD_FAILED))
        expected_paths = {os.fsencode(path) for path in fold_paths}
        if staged_paths != expected_paths:
            raise RuntimeError(
                f"fold staged path closure mismatch: expected={sorted(expected_paths)!r}, "
                f"actual={sorted(staged_paths)!r}"
            )

        fd, temporary = tempfile.mkstemp(
            prefix=".dev-wave-fold-message.",
            dir=repository.common,
        )
        message_path = Path(temporary)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_FOLD_MESSAGE)
            handle.flush()
            os.fsync(handle.fileno())
        _preflight_fold_message(repository, message_path)
        commit = _git(
            repository.main,
            "commit", "--no-gpg-sign", "-F", str(message_path),
            "--cleanup=verbatim", f"--author={FOLD_AUTHOR_IDENTITY}",
        )
        if commit.returncode != 0:
            raise RuntimeError(
                f"fold commit failed ({_detail(commit.stderr) or 'no detail'})"
            )
        fold_commit = _head(repository.main, "main post-fold")
        plan = fold.mark_fold_committed(
            repository.main,
            plan,
            fold_commit=fold_commit,
        )
        _verify_fold_postconditions(
            repository,
            fold_commit=fold_commit,
            expected_parent=fold_base,
            trusted_main_cutoff_sha=trusted_main_cutoff_sha,
            tested_tip=tested_tip,
            landed_commits=landed_commits,
            wave_ref=wave_ref,
        )
        successful_fold = LandResult(
            RC_OK,
            "landed",
            "main fast-forwarded to the tested wave tip and folded pending fragments"
            + (
                ""
                if fold_gate_receipt is None
                or not fold_gate_receipt.uncovered_families
                else "; fold gate uncovered families="
                + ",".join(fold_gate_receipt.uncovered_families)
            ),
            successful_land.main_before,
            fold_commit,
            tested_tip,
            fold_commit,
            release_safe=True,
        )
    except (Exception, KeyboardInterrupt) as exc:  # fold failure は必ず landed 以外へ畳む。
        if isinstance(exc, _Reject) and not apply_started:
            return LandResult(exc.rc, "rejected", exc.reason,
                              successful_land.main_before, fold_base, tested_tip,
                              retryable_same_request=exc.retryable_same_request)
        rollback_failures = _rollback_fold(
            repository,
            rollback_ref=rollback_ref,
            expected_tip=tested_tip,
            index_tree=index_tree,
            snapshots=snapshots,
            state_path=state_path,
            expected_transaction_id=getattr(plan, "transaction_id"),
        )
        try:
            main_after = _head(repository.main, "main after fold failure")
        except _Reject:
            main_after = None
        reason = f"fold failed: {type(exc).__name__}: {exc}"
        if rollback_failures:
            reason += "; rollback incomplete: " + "; ".join(rollback_failures)
            try:
                state_metadata = state_path.lstat()
            except OSError:
                pass
            else:
                if stat.S_ISREG(state_metadata.st_mode):
                    reason += f"; resume journal preserved at {state_path}"
                else:
                    reason += f"; non-resumable transaction state remains at {state_path}"
        return LandResult(
            RC_FOLD_ROLLBACK_FAILED if rollback_failures else RC_FOLD_FAILED,
            "fold-rollback-failed" if rollback_failures else "fold-failed",
            reason,
            successful_land.main_before,
            main_after,
            tested_tip,
        )
    finally:
        if message_path is not None:
            try:
                message_path.unlink()
            except FileNotFoundError:
                pass
    try:
        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)
    except (Exception, KeyboardInterrupt) as exc:
        return LandResult(
            RC_FOLD_FINALIZE_FAILED,
            "fold-finalize-failed",
            f"fold finalize failed after verified commit: {type(exc).__name__}: {exc}",
            successful_land.main_before,
            fold_commit,
            tested_tip,
            fold_commit,
            retryable_same_request=True,
        )
    return successful_fold


def _finalize_recovered_fold_commit(
    repository: _Repository,
    *,
    fold: object,
    plan: object,
    fold_commit: str,
    main_before: str | None,
    tested_tip: str,
    landed_commits: Sequence[str],
    wave_ref: str,
    fold_gate_receipt: _FoldGateReceipt,
) -> LandResult:
    """検証済みの形 B を再 apply / 再 commit せず完遂する。"""

    origin = getattr(plan, "origin")

    def before_mutation() -> None:
        _land_turn_mutating(
            repository, plan=plan, main_before=origin.rollback_ref, landing_tip=tested_tip,
            wave_ref=wave_ref, trusted_main_cutoff=origin.trusted_main_cutoff,
            landed_commits=landed_commits,
        )

    try:
        fold.verify_fold_commit_identity(
            repository.main,
            plan,
            fold_commit=fold_commit,
        )
        phase = getattr(plan, "phase", None)
        if phase == "applied":
            before_mutation()
            plan = fold.mark_fold_committed(
                repository.main,
                plan,
                fold_commit=fold_commit,
            )
        elif phase != "committed":
            raise RuntimeError(f"stored fold transaction phase is not recoverable: {phase!r}")
        origin = getattr(plan, "origin")
        _verify_fold_postconditions(
            repository,
            fold_commit=fold_commit,
            expected_parent=origin.tested_tip,
            trusted_main_cutoff_sha=origin.trusted_main_cutoff,
            tested_tip=tested_tip,
            landed_commits=landed_commits,
            wave_ref=wave_ref,
        )
    except (Exception, KeyboardInterrupt) as exc:
        return LandResult(
            RC_FOLD_RECOVERY_FAILED,
            "fold-recovery-failed",
            f"stored fold commit recovery failed: {type(exc).__name__}: {exc}",
            main_before,
            fold_commit,
            tested_tip,
            retryable_same_request=True,
        )
    try:
        before_mutation()
        fold.finalize_fold(repository.main, plan, fold_commit=fold_commit)
    except (Exception, KeyboardInterrupt) as exc:
        return LandResult(
            RC_FOLD_FINALIZE_FAILED,
            "fold-finalize-failed",
            f"fold finalize failed after verified commit: {type(exc).__name__}: {exc}",
            main_before,
            fold_commit,
            tested_tip,
            fold_commit,
            retryable_same_request=True,
        )
    return LandResult(
        RC_OK,
        "landed",
        "verified active fold commit finalized without reapplying or recommitting"
        + (
            ""
            if not fold_gate_receipt.uncovered_families
            else "; fold gate uncovered families="
            + ",".join(fold_gate_receipt.uncovered_families)
        ),
        main_before,
        fold_commit,
        tested_tip,
        fold_commit,
        release_safe=True,
    )


def _postcondition(
    repository: _Repository,
    *,
    tested_tip: str,
    wave_ref: str,
    merge_rc: int,
    main_before: str,
    gitlinks_changed: bool,
) -> LandResult:
    try:
        main_after = _head(repository.main, "main post-land")
    except _Reject as exc:
        return LandResult(
            RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
            f"main HEAD cannot be observed after merge: {exc.reason}",
            main_before,
            None,
            tested_tip,
        )
    if main_after != tested_tip:
        failures: list[str] = []
        if main_after != main_before:
            failures.append("main HEAD changed but did not reach tested tip")
        if merge_rc == 0:
            failures.append("merge reported success without reaching tested tip")
        try:
            if _main_tracked_or_index_dirty(repository):
                failures.append(
                    "merge left tracked/index/worktree changes without reaching tested tip"
                )
            _verify_main_no_tracked_dirt(repository)
        except _Reject as exc:
            failures.append(exc.reason)
        if failures:
            return LandResult(
                RC_LANDED_POSTCONDITION_FAILED,
                "landed-postcondition-failed",
                "; ".join(failures),
                main_before,
                main_after,
                tested_tip,
            )
        return LandResult(
            RC_NOT_LANDED,
            "not-landed",
            f"merge rc={merge_rc}; main HEAD did not reach tested tip",
            main_before,
            main_after,
            tested_tip,
        )
    failures: list[str] = []
    if merge_rc != 0:
        failures.append(f"merge returned rc={merge_rc}")
    if gitlinks_changed:
        failures.append(
            "tested range changes gitlinks; D16 post-land submodule synchronization "
            "remains required"
        )
    try:
        if _symbolic_head(repository.main, "main post-land") != "refs/heads/main":
            failures.append("main symbolic HEAD moved")
        if _ref_sha(repository.main, "refs/heads/main", "main post-land ref") != tested_tip:
            failures.append("main ref does not equal tested tip")
        if _head(repository.wave, "wave post-land") != tested_tip:
            failures.append("wave HEAD moved")
        if _symbolic_head(repository.wave, "wave post-land") != wave_ref:
            failures.append("wave symbolic ref moved")
        if _ref_sha(repository.wave, wave_ref, "wave post-land ref") != tested_tip:
            failures.append("wave ref moved")
        _verify_main_no_tracked_dirt(repository)
        _verify_wave_clean(repository)
    except _Reject as exc:
        failures.append(exc.reason)
    if failures:
        return LandResult(
            RC_LANDED_POSTCONDITION_FAILED,
            "landed-postcondition-failed",
            "; ".join(failures),
            main_before,
            main_after,
            tested_tip,
        )
    return LandResult(
        RC_OK,
        "landed",
        "main fast-forwarded to the tested wave tip",
        main_before,
        main_after,
        tested_tip,
        release_safe=True,
    )


def _lock_busy_result(
    *,
    phase: str,
    waited_s: float,
    window_started: float,
    tested_tip: str,
    budget_exhausted_before_attempt: bool = False,
) -> LandResult:
    """limit_s は絶対窓ではなく累積競合待機予算。field 名は維持する。

    waited_s は実待ち時間の累積、window_elapsed_s は lock 内外の作業を
    含む経過時間。予算は実績の厳密な上限ではなく、追加待機の判断に使う。
    """
    disposition = (
        "wait budget already exhausted; tried once without waiting"
        if budget_exhausted_before_attempt
        else "wait budget exhausted after waiting"
    )
    window_elapsed = max(0.0, _land_lock_now() - window_started)
    return LandResult(
        RC_LOCK_BUSY,
        "lock-busy",
        "another cooperative land operation holds the common lock "
        f"({disposition}; phase={phase}, waited_s={waited_s:.3f}, "
        f"window_elapsed_s={window_elapsed:.3f}, "
        f"limit_s={_LAND_LOCK_WAIT_SECONDS:.3f})",
        None,
        None,
        tested_tip,
        retryable_same_request=True,
    )


def land(request: LandRequest) -> LandResult:
    repository: _Repository | None = None
    lock = _LandLockHandle()
    main_before: str | None = None
    tested_tip: str | None = None
    landing_tip: str | None = None
    prelocked_forward_main_merges: tuple[_ForwardMainMerge, ...] = ()
    acceptance_verification: _AcceptanceVerification | None = None
    fold_gate_receipt: _FoldGateReceipt | None = None
    quiescent_rejection = False
    lock_window_started: float | None = None
    waited_s = 0.0
    turn: _LandTurnHandle | None = None
    registered_verification: _AcceptanceVerification | None = None

    def finish(result: LandResult) -> LandResult:
        if repository is not None:
            try:
                _finish_land_turn(repository, result)
            except _Reject as exc:
                result = replace(result, rc=exc.rc, status="rejected", reason=exc.reason,
                                 release_safe=False, retryable_same_request=exc.retryable_same_request)
        if result.rc == RC_LOCK_BUSY and turn is not None:
            result = replace(result, reason=result.reason + (
                f"; turn_waited_s={turn.waited_s:.3f}, "
                f"turn_elapsed_s={max(0.0, _land_lock_now() - turn.started):.3f}, "
                f"turn_limit_s={_LAND_TURN_WAIT_SECONDS:.3f}"
            ))
        decorated = replace(
            result,
            waited_s=waited_s if lock_window_started is not None else None,
            window_elapsed_s=(
                max(0.0, _land_lock_now() - lock_window_started)
                if lock_window_started is not None else None
            ),
            tested_tip_sha=tested_tip,
            landing_tip_sha=landing_tip,
            incorporated_main_shas=tuple(
                merge.incorporated_main_sha
                for merge in prelocked_forward_main_merges
            ),
            fold_gate_uncovered_families=(
                result.fold_gate_uncovered_families
                if result.fold_gate_uncovered_families is not None
                else (
                    None
                    if fold_gate_receipt is None
                    else fold_gate_receipt.uncovered_families
                )
            ),
        )
        if acceptance_verification is None:
            return decorated
        return _with_acceptance_verification(decorated, acceptance_verification)

    try:
        tested_main = _sha(request.tested_main_sha, "tested main")
        tested_tip = _sha(request.tested_wave_tip_sha, "tested wave tip")
        landing_tip = _sha(
            request.landing_wave_tip_sha or tested_tip,
            "landing wave tip",
        )
        requested_audit = tuple(
            _sha(commit, f"audited commit {index}")
            for index, commit in enumerate(request.audited_commits)
        )
        repository = _verify_repository(request)
        turn_started = _land_lock_now()
        turn = _LandTurnHandle(turn_started, turn_started + _LAND_TURN_WAIT_SECONDS)
        try:
            registered_verification = _verify_acceptance_static(
                repository, raw=_read_acceptance_receipt(request.acceptance_receipt),
                acceptance_wave=request.acceptance_wave,
                tested_main=tested_main, tested_tip=tested_tip,
            )
        except _Reject as exc:
            raise _Reject(
                exc.rc, exc.reason,
                release_safe=not exc.retryable_same_request,
                retryable_same_request=exc.retryable_same_request,
            ) from exc
        if landing_tip != tested_tip:
            _verify_history_modifiers(repository)
            _verify_effective_config(repository)
            _verify_replay_config(repository)
            prelocked_forward_main_merges = _forward_main_merge_topology(
                repository,
                tested_main,
                tested_tip,
                landing_tip,
            )
            _replay_forward_main_merges(
                repository,
                prelocked_forward_main_merges,
            )
        _register_land_turn(repository, request, registered_verification, turn)
        repository.turn = turn
        repository.land_lock = lock
        granted, waited, ahead = _wait_land_turn(repository, lock)
        waited_s += waited
        # Completion observation resolves only the ticket. Existing preflight
        # and postconditions still decide the result, including D16 gitlinks.
        if not granted:
            return finish(LandResult(
                RC_LOCK_BUSY, "lock-busy",
                f"waiting for land turn (seq={turn.seq}, ahead={ahead})",
                None, None, landing_tip, retryable_same_request=True,
            ))
        lock_window_started = _land_lock_now()
        try:
            acquired, waited = _acquire_land_lock_until_turn(
                repository, lock, max(0.0, _LAND_LOCK_WAIT_SECONDS - waited_s),
            )
            waited_s += waited
            if not acquired:
                return finish(_lock_busy_result(
                    phase="initial",
                    waited_s=waited_s,
                    window_started=lock_window_started,
                    tested_tip=landing_tip,
                ))
            preflight = _locked_preflight(
                repository,
                tested_main=tested_main,
                tested_tip=tested_tip,
                landing_tip=landing_tip,
                prelocked_forward_main_merges=prelocked_forward_main_merges,
                requested_audit=requested_audit,
                reported_main_before=main_before,
            )
            if isinstance(preflight, LandResult):
                return finish(preflight)
            main_before = preflight.locked_main
            quiescent_rejection = preflight.active_plan is None
            if preflight.forward_main_merges:
                _verify_forward_main_runner_blob(
                    repository,
                    tested_main,
                    preflight.forward_main_merges,
                )
            if preflight.locked_main != landing_tip and preflight.active_plan is None:
                initial_fingerprint = preflight.fingerprint
                receipt, acquired, waited = _run_outside_land_lock(
                    repository,
                    lock,
                    max(0.0, _LAND_LOCK_WAIT_SECONDS - waited_s),
                    lambda: _audit_provenance_history(repository),
                )
                waited_s += waited
                if not acquired:
                    return finish(_lock_busy_result(
                        phase="post-provenance",
                        budget_exhausted_before_attempt=(
                            waited_s - waited >= _LAND_LOCK_WAIT_SECONDS
                        ),
                        waited_s=waited_s,
                        window_started=lock_window_started,
                        tested_tip=landing_tip,
                    ))
                refreshed_control = _control_snapshot(
                    repository, preflight.control.worktree_targets
                )
                if (
                    refreshed_control != preflight.control
                    or not _surviving_worktree_bindings_unchanged(
                        preflight.control, refreshed_control
                    )
                ):
                    try:
                        refreshed_active_plan = preflight.fold.load_active_plan(
                            repository.main
                        )
                    except (Exception, KeyboardInterrupt) as exc:
                        return finish(LandResult(
                            RC_FOLD_RECOVERY_FAILED,
                            "fold-recovery-failed",
                            "fold transaction inspection failed: "
                            f"{type(exc).__name__}: {exc}",
                            main_before,
                            main_before,
                            landing_tip,
                            retryable_same_request=True,
                        ))
                    raise _Reject(
                        RC_CONTROL_PLANE,
                        "control-plane identity/binding changed during "
                        "the provenance audit",
                        release_safe=refreshed_active_plan is None,
                    )
                try:
                    refreshed_fingerprint = _land_fingerprint(
                        repository,
                        current=_head(repository.main, "main after provenance audit"),
                        tested_tip=landing_tip,
                        wave_head=_head(
                            repository.wave, "wave after provenance audit"
                        ),
                        control=refreshed_control,
                    )
                except _Reject as exc:
                    raise _Reject(
                        RC_PROVENANCE,
                        "provenance audit fingerprint recomputation failed "
                        f"({exc.reason})",
                    ) from exc
                if refreshed_fingerprint != initial_fingerprint:
                    raise _Reject(
                        RC_PROVENANCE,
                        "main/wave heads or collision paths changed during "
                        "the provenance audit",
                        retryable_same_request=True,
                    )
                preflight = _locked_preflight(
                    repository,
                    tested_main=tested_main,
                    tested_tip=tested_tip,
                    landing_tip=landing_tip,
                    prelocked_forward_main_merges=prelocked_forward_main_merges,
                    requested_audit=requested_audit,
                    reported_main_before=main_before,
                )
                if isinstance(preflight, LandResult):
                    return finish(preflight)
                quiescent_rejection = preflight.active_plan is None
                _verify_provenance_receipt(repository, receipt, landing_tip)
                if preflight.forward_main_merges:
                    _verify_forward_main_runner_blob(
                        repository,
                        tested_main,
                        preflight.forward_main_merges,
                    )
                main_before = preflight.locked_main
            quiescent_rejection = preflight.active_plan is None
            acceptance_verification = _verify_acceptance_receipt(
                repository,
                receipt_path=request.acceptance_receipt,
                acceptance_wave=request.acceptance_wave,
                tested_main=tested_main,
                tested_tip=tested_tip,
                locked_main=preflight.locked_main,
            )
            if acceptance_verification.receipt_sha256 != registered_verification.receipt_sha256:
                raise _acceptance_rejected()
            fold = preflight.fold
            active_plan = preflight.active_plan
            control = preflight.control
            base_gitlinks = preflight.base_gitlinks
            target_gitlinks = preflight.target_gitlinks
            target_normal_entries = preflight.target_normal_entries
            gitlinks_changed = preflight.gitlinks_changed
            locked_main = preflight.locked_main
            wave_ref = preflight.wave_ref
            fold_trusted_main_cutoff = preflight.fold_trusted_main_cutoff
            landed_commits = preflight.landed_commits
            if active_plan is not None:
                state_path = fold._state_path(repository.main)
                origin = getattr(active_plan, "origin", None)
                if getattr(origin, "kind", None) == "standalone":
                    return finish(LandResult(
                        RC_FOLD_RECOVERY_FAILED,
                        "fold-recovery-failed",
                        "standalone-origin fold transaction cannot be auto-recovered; "
                        f"state={state_path.absolute()}; "
                        "lock-aware finalize command は未実装",
                        main_before,
                        locked_main,
                        landing_tip,
                        retryable_same_request=True,
                    ))
                try:
                    if origin is None or origin.kind != "land":
                        raise RuntimeError("stored fold origin is not land")
                    if origin.wave_ref != wave_ref:
                        raise RuntimeError("stored fold origin wave_ref does not match the request")
                    if origin.tested_tip != landing_tip:
                        raise RuntimeError("stored fold origin tested_tip does not match the request")
                    transaction_id = getattr(active_plan, "transaction_id", None)
                    complete_issues = fold.validate_spool_tree(
                        repository.main,
                        expected_transaction_id=transaction_id,
                    )
                    if complete_issues:
                        raise RuntimeError(
                            "active transaction complete shape invalid: "
                            + "; ".join(issue.message for issue in complete_issues)
                        )
                    fold_paths = _fold_plan_paths(active_plan)
                    _verify_supervised_fragment_wave(wave_ref, active_plan)
                    pending_before = _pending_spool_paths(repository.main)
                    if set(pending_before) - set(fold_paths):
                        raise RuntimeError("stored fold plan does not cover every pending fragment candidate")
                except (Exception, KeyboardInterrupt) as exc:
                    return finish(LandResult(
                        RC_FOLD_RECOVERY_FAILED,
                        "fold-recovery-failed",
                        f"stored fold transaction preflight failed: {type(exc).__name__}: {exc}",
                        main_before,
                        locked_main,
                        landing_tip,
                        retryable_same_request=True,
                    ))
                try:
                    stored_gate_receipt = _fold_gate_receipt_from_plan(
                        active_plan
                    )
                    _verify_folded_fragment_receipts(
                        repository.wave,
                        active_plan,
                    )
                    _verify_fold_gate_receipt(
                        repository.wave,
                        stored_gate_receipt,
                        active_plan,
                    )
                    fold_gate_receipt = stored_gate_receipt
                except _FoldGateFailure as exc:
                    return finish(_fold_gate_failed_result(
                        f"stored fold gate receipt rejected: {exc}",
                        main_before=main_before,
                        main_after=locked_main,
                        tested_tip=landing_tip,
                        retryable_same_request=exc.retryable_same_request,
                        uncovered_families=exc.uncovered_families,
                        covered_and_failed_families=(
                            exc.covered_and_failed_families
                        ),
                    ))
                if locked_main != landing_tip:
                    return finish(_finalize_recovered_fold_commit(
                        repository,
                        fold=fold,
                        plan=active_plan,
                        fold_commit=locked_main,
                        main_before=main_before,
                        tested_tip=landing_tip,
                        landed_commits=landed_commits,
                        wave_ref=wave_ref,
                        fold_gate_receipt=fold_gate_receipt,
                    ))
                if getattr(active_plan, "phase", None) != "applied":
                    return finish(LandResult(
                        RC_FOLD_RECOVERY_FAILED,
                        "fold-recovery-failed",
                        "shape A requires an applied transaction at origin.tested_tip",
                        main_before,
                        locked_main,
                        landing_tip,
                        retryable_same_request=True,
                    ))
                try:
                    index_tree = _fold_ref_tree(repository, origin.rollback_ref)
                    # tracked before-state は stored rollback ref の tree から復元する。
                    # plan が新設する path だけを snapshot し、untracked 残骸を残さない。
                    recovery_snapshots = tuple(
                        _PathSnapshot(target.path, False, b"", 0)
                        for target in getattr(active_plan, "targets", ())
                        if not getattr(target, "before_exists", True)
                    )
                except (Exception, KeyboardInterrupt) as exc:
                    return finish(LandResult(
                        RC_FOLD_RECOVERY_FAILED,
                        "fold-recovery-failed",
                        f"stored fold rollback preflight failed: {type(exc).__name__}: {exc}",
                        main_before,
                        locked_main,
                        landing_tip,
                        retryable_same_request=True,
                    ))
                recovery = LandResult(
                    RC_OK,
                    "already-landed",
                    "main is at the tested tip with an active fold transaction",
                    main_before,
                    locked_main,
                    landing_tip,
                )
                return finish(_fold_main_locked(
                    repository,
                    recovery,
                    fold=fold,
                    plan=active_plan,
                    trusted_main_cutoff_sha=origin.trusted_main_cutoff,
                    tested_tip=landing_tip,
                    landed_commits=landed_commits,
                    wave_ref=wave_ref,
                    rollback_ref=origin.rollback_ref,
                    snapshots=recovery_snapshots,
                    index_tree=index_tree,
                    state_path=state_path,
                    fold_gate_receipt=fold_gate_receipt,
                ))

            fold_date = _land_fold_date()
            try:
                origin = fold.FoldOrigin(
                    kind="land",
                    base=locked_main,
                    tested_tip=landing_tip,
                    wave_ref=wave_ref,
                    rollback_ref=locked_main,
                    trusted_main_cutoff=fold_trusted_main_cutoff,
                    audited_digest=fold.audited_commit_digest(landed_commits),
                )
                plan = fold.plan_fold(
                    repository.wave,
                    fold_date=fold_date,
                    origin=origin,
                )
                fold_paths = _fold_plan_paths(plan)
                _verify_supervised_fragment_wave(wave_ref, plan)
                pending_candidate = _pending_spool_paths(repository.wave)
                if set(pending_candidate) - set(fold_paths):
                    raise RuntimeError("fold plan does not cover every pending fragment candidate")
            except (Exception, KeyboardInterrupt) as exc:
                interrupted = isinstance(exc, KeyboardInterrupt)
                return finish(LandResult(
                    RC_FOLD_FAILED,
                    "fold-failed",
                    f"candidate fold planning failed: {type(exc).__name__}: {exc}",
                    main_before,
                    locked_main,
                    landing_tip,
                    release_safe=not interrupted,
                    retryable_same_request=interrupted,
                ))

            if getattr(plan, "status", None) != "noop":
                initial_gate_fingerprint = preflight.fingerprint
                initial_gate_control = preflight.control
                try:
                    gate_payload, acquired, waited = _run_outside_land_lock(
                        repository,
                        lock,
                        max(0.0, _LAND_LOCK_WAIT_SECONDS - waited_s),
                        lambda: _run_fold_gate(repository, plan, landing_tip),
                    )
                except _FoldGateFailure as exc:
                    return finish(_fold_gate_failed_result(
                        f"fold gate failed: {exc}",
                        main_before=main_before,
                        main_after=locked_main,
                        tested_tip=landing_tip,
                        retryable_same_request=exc.retryable_same_request,
                        uncovered_families=exc.uncovered_families,
                        covered_and_failed_families=(
                            exc.covered_and_failed_families
                        ),
                    ))
                waited_s += waited
                assert isinstance(gate_payload, _FoldGateReceipt)
                fold_gate_receipt = gate_payload
                if not acquired:
                    return finish(_lock_busy_result(
                        phase="post-fold-gate",
                        budget_exhausted_before_attempt=(
                            waited_s - waited >= _LAND_LOCK_WAIT_SECONDS
                        ),
                        waited_s=waited_s,
                        window_started=lock_window_started,
                        tested_tip=landing_tip,
                    ))
                try:
                    refreshed_control = _control_snapshot(
                        repository,
                        initial_gate_control.worktree_targets,
                    )
                    if (
                        refreshed_control != initial_gate_control
                        or not _surviving_worktree_bindings_unchanged(
                            initial_gate_control,
                            refreshed_control,
                        )
                    ):
                        raise _FoldGateFailure(
                            "control-plane identity/binding changed during fold gate"
                        )
                    refreshed_fingerprint = _land_fingerprint(
                        repository,
                        current=_head(
                            repository.main,
                            "main after fold gate",
                        ),
                        tested_tip=landing_tip,
                        wave_head=_head(
                            repository.wave,
                            "wave after fold gate",
                        ),
                        control=refreshed_control,
                    )
                    if refreshed_fingerprint != initial_gate_fingerprint:
                        raise _FoldGateFailure(
                            "main/wave heads or collision paths changed during fold gate"
                        )
                    refreshed_preflight = _locked_preflight(
                        repository,
                        tested_main=tested_main,
                        tested_tip=tested_tip,
                        landing_tip=landing_tip,
                        prelocked_forward_main_merges=prelocked_forward_main_merges,
                        requested_audit=requested_audit,
                        reported_main_before=main_before,
                    )
                    if isinstance(refreshed_preflight, LandResult):
                        raise _FoldGateFailure(
                            "locked preflight changed after fold gate: "
                            + refreshed_preflight.reason
                        )
                    if refreshed_preflight.active_plan is not None:
                        raise _FoldGateFailure(
                            "a fold transaction appeared during fold gate"
                        )
                    fold._validate_closure(repository.wave, plan)
                    pending_wave = _pending_spool_paths(repository.wave)
                    if set(pending_wave) - set(getattr(plan, "gc_paths", ())):
                        raise _FoldGateFailure(
                            "wave pending fragment set grew outside the fold plan"
                        )
                    pending_main = _pending_spool_paths(repository.main)
                    if set(pending_main) - set(getattr(plan, "gc_paths", ())):
                        raise _FoldGateFailure(
                            "main pending fragment set grew outside the fold plan"
                        )
                    _verify_main_fold_closure_before_ff(
                        repository,
                        landing_tip,
                        plan,
                        fold,
                    )
                    _verify_fold_gate_receipt(
                        repository.wave,
                        fold_gate_receipt,
                        plan,
                    )
                    preflight = refreshed_preflight
                    control = preflight.control
                    base_gitlinks = preflight.base_gitlinks
                    target_gitlinks = preflight.target_gitlinks
                    target_normal_entries = preflight.target_normal_entries
                    gitlinks_changed = preflight.gitlinks_changed
                    locked_main = preflight.locked_main
                    wave_ref = preflight.wave_ref
                    fold_trusted_main_cutoff = preflight.fold_trusted_main_cutoff
                    landed_commits = preflight.landed_commits
                except _FoldGateFailure as exc:
                    return finish(_fold_gate_failed_result(
                        "fold gate revalidation failed: "
                        f"{type(exc).__name__}: {exc}",
                        main_before=main_before,
                        main_after=main_before,
                        tested_tip=landing_tip,
                        retryable_same_request=exc.retryable_same_request,
                        uncovered_families=(
                            fold_gate_receipt.uncovered_families
                            if fold_gate_receipt is not None
                            else exc.uncovered_families
                        ),
                        covered_and_failed_families=(
                            exc.covered_and_failed_families
                        ),
                    ))
                except (Exception, KeyboardInterrupt) as exc:
                    interrupted = isinstance(exc, KeyboardInterrupt)
                    return finish(_fold_gate_failed_result(
                        f"fold gate revalidation failed: {type(exc).__name__}: {exc}",
                        main_before=main_before,
                        main_after=main_before,
                        tested_tip=landing_tip,
                        retryable_same_request=interrupted,
                    ))

                # Receipt rejection keeps its existing rc and retryability;
                # the fold-gate exception mapper must not reclassify it.
                try:
                    refreshed_acceptance = _verify_acceptance_receipt(
                        repository, receipt_path=request.acceptance_receipt,
                        acceptance_wave=request.acceptance_wave,
                        tested_main=tested_main, tested_tip=tested_tip,
                        locked_main=refreshed_preflight.locked_main,
                    )
                    if refreshed_acceptance.receipt_sha256 != registered_verification.receipt_sha256:
                        raise _acceptance_rejected()
                except _Reject:
                    raise
                except (Exception, KeyboardInterrupt) as exc:
                    return finish(_fold_gate_failed_result(
                        f"fold gate revalidation failed: {type(exc).__name__}: {exc}",
                        main_before=main_before,
                        main_after=main_before,
                        tested_tip=landing_tip,
                        retryable_same_request=isinstance(exc, KeyboardInterrupt),
                    ))

            fold_collision_paths = tuple(os.fsencode(path) for path in fold_paths)
            if fold_collision_paths:
                _verify_main_clean(
                    repository,
                    collision_paths=fold_collision_paths,
                )
            if getattr(plan, "status", None) == "noop":
                declared = verify_declared_fold_commit(
                    repository.main if locked_main == landing_tip else repository.wave,
                    fold_commit_sha=None,
                    trusted_main_cutoff_sha=fold_trusted_main_cutoff,
                    landed_main_sha=landing_tip,
                    landed_commits=landed_commits,
                    wave_tip=landing_tip,
                )
                if not declared.ok:
                    return finish(LandResult(
                        RC_FOLD_FAILED,
                        "fold-failed",
                        f"declared no-fold shape rejected: {declared.detail}",
                        main_before,
                        locked_main,
                        landing_tip,
                        release_safe=True,
                    ))
            if locked_main == landing_tip:
                if gitlinks_changed and not _gitlinks_synchronized(
                    repository,
                    base_gitlinks,
                    target_gitlinks,
                    target_normal_entries,
                ):
                    return finish(LandResult(
                        RC_LANDED_POSTCONDITION_FAILED,
                        "landed-postcondition-failed",
                        "main is at a gitlink-changing tested tip; D16 post-land "
                        "submodule synchronization remains required",
                        main_before,
                        locked_main,
                        landing_tip,
                    ))
                already_landed = LandResult(
                    RC_OK,
                    "already-landed",
                    "another lander reached the tested tip first",
                    main_before,
                    locked_main,
                    landing_tip,
                    release_safe=True,
                )
                if getattr(plan, "status", None) == "noop":
                    return finish(already_landed)
                try:
                    snapshots = _snapshot_fold_paths(repository.main, fold_paths)
                    index_tree = _fold_index_tree(repository)
                    state_path = fold._state_path(repository.main)
                except (Exception, KeyboardInterrupt) as exc:
                    interrupted = isinstance(exc, KeyboardInterrupt)
                    return finish(LandResult(
                        RC_FOLD_FAILED,
                        "fold-failed",
                        f"fold preflight failed: {type(exc).__name__}: {exc}",
                        main_before,
                        locked_main,
                        landing_tip,
                        release_safe=not interrupted,
                        retryable_same_request=interrupted,
                    ))
                return finish(_fold_main_locked(
                    repository,
                    already_landed,
                    fold=fold,
                    plan=plan,
                    trusted_main_cutoff_sha=fold_trusted_main_cutoff,
                    tested_tip=landing_tip,
                    landed_commits=landed_commits,
                    wave_ref=wave_ref,
                    rollback_ref=landing_tip,
                    snapshots=snapshots,
                    index_tree=index_tree,
                    state_path=state_path,
                    fold_gate_receipt=fold_gate_receipt,
                ))
            collision_control = _control_snapshot(
                repository, control.worktree_targets
            )
            _verify_target_collisions(
                repository,
                current=locked_main,
                tested_tip=landing_tip,
                control=collision_control,
            )
            refreshed_collision_control = _control_snapshot(
                repository, control.worktree_targets
            )
            if (
                refreshed_collision_control != collision_control
                or not _surviving_worktree_bindings_unchanged(
                    collision_control, refreshed_collision_control
                )
            ):
                raise _Reject(
                    RC_CONTROL_PLANE,
                    "control-plane identity/binding changed before main mutation",
                )
            snapshots: tuple[_PathSnapshot, ...] = ()
            index_tree: str | None = None
            state_path: Path | None = None
            if getattr(plan, "status", None) != "noop":
                try:
                    snapshots = _snapshot_fold_paths(repository.main, fold_paths)
                    index_tree = _fold_index_tree(repository)
                    state_path = fold._state_path(repository.main)
                except (Exception, KeyboardInterrupt) as exc:
                    interrupted = isinstance(exc, KeyboardInterrupt)
                    return finish(LandResult(
                        RC_FOLD_FAILED,
                        "fold-failed",
                        f"fold preflight failed: {type(exc).__name__}: {exc}",
                        main_before,
                        locked_main,
                        landing_tip,
                        release_safe=not interrupted,
                        retryable_same_request=interrupted,
                    ))
            _land_turn_mutating(
                repository, plan=plan, main_before=locked_main, landing_tip=landing_tip,
                wave_ref=wave_ref, trusted_main_cutoff=fold_trusted_main_cutoff,
                landed_commits=landed_commits,
            )
            merge = _git(
                repository.main,
                "merge", "--ff-only", "--no-stat", "--no-progress", landing_tip,
                pass_fds=(lock.fd,),
            )
            merged = _postcondition(
                repository,
                tested_tip=landing_tip,
                wave_ref=wave_ref,
                merge_rc=merge.returncode,
                main_before=locked_main,
                gitlinks_changed=gitlinks_changed,
            )
            if merged.rc != RC_OK:
                return finish(merged)
            if getattr(plan, "status", None) == "noop":
                return finish(merged)
            assert index_tree is not None and state_path is not None
            return finish(_fold_main_locked(
                repository,
                merged,
                fold=fold,
                plan=plan,
                trusted_main_cutoff_sha=fold_trusted_main_cutoff,
                tested_tip=landing_tip,
                landed_commits=landed_commits,
                wave_ref=wave_ref,
                rollback_ref=locked_main,
                snapshots=snapshots,
                index_tree=index_tree,
                state_path=state_path,
                fold_gate_receipt=fold_gate_receipt,
            ))
        finally:
            lock.close()
    except _Reject as exc:
        return finish(LandResult(
            exc.rc,
            "rejected",
            exc.reason,
            main_before,
            main_before,
            landing_tip,
            release_safe=(
                exc.release_safe
                or (quiescent_rejection and not exc.retryable_same_request)
            ),
            retryable_same_request=exc.retryable_same_request,
        ))
    finally:
        lock.close()
        if turn is not None:
            turn.close()
        if repository is not None:
            repository.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="tested dev-wave tip を cooperative local main へ ff-only land する"
    )
    parser.add_argument("--main-worktree", type=Path, required=True)
    parser.add_argument("--wave-worktree", type=Path, required=True)
    parser.add_argument("--tested-main-sha", required=True)
    parser.add_argument("--tested-wave-tip-sha", required=True)
    parser.add_argument(
        "--landing-wave-tip-sha",
        help="実着地 tip。省略時は --tested-wave-tip-sha と同じ",
    )
    parser.add_argument("--acceptance-wave", required=True)
    parser.add_argument("--acceptance-receipt", type=Path, required=True)
    parser.add_argument(
        "--audited-commit",
        action="append",
        default=[],
        help="git rev-list --reverse A..T と同順に反復指定する",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    request = LandRequest(
        main_worktree=args.main_worktree,
        wave_worktree=args.wave_worktree,
        tested_main_sha=args.tested_main_sha,
        tested_wave_tip_sha=args.tested_wave_tip_sha,
        audited_commits=tuple(args.audited_commit),
        acceptance_wave=args.acceptance_wave,
        acceptance_receipt=args.acceptance_receipt,
        landing_wave_tip_sha=args.landing_wave_tip_sha,
    )
    try:
        authority_digest = _release_authority_digest(
            request.acceptance_receipt,
            request.acceptance_wave,
        )
    except _Reject:
        authority_digest = None

    lease_dir = os.environ.get("IZANAGI_WAVE_LEASE_DIR")
    if not lease_dir:
        renew_state = "unavailable"
        renew_reason = "lease-dir-required"
    else:
        try:
            renewed = _wave_land_window.renew(
                Path(lease_dir),
                request.acceptance_wave,
            )
            renew_state = str(renewed.get("state", "unavailable"))
            source = renewed.get("source")
            source_reason = (
                source.get("reason") if isinstance(source, dict) else None
            )
            renew_reason = (
                str(source_reason) if source_reason is not None else "none"
            )
        except (Exception, KeyboardInterrupt):
            renew_state = "unavailable"
            renew_reason = "renew-internal-error"

    result = land(request)
    print(
        json.dumps(
            result.as_json(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        flush=True,
    )

    release_state = "retained"
    release_reason = "land-result-not-release-safe"
    if result.release_safe and not result.retryable_same_request:
        if authority_digest is None:
            release_state = "unavailable"
            release_reason = "receipt-authority-unverified"
        elif (
            result.acceptance_receipt_sha256 is not None
            and result.acceptance_receipt_sha256 != authority_digest
        ):
            release_state = "unavailable"
            release_reason = "receipt-digest-mismatch"
        else:
            receipt_unchanged = result.acceptance_receipt_sha256 is not None
            if not receipt_unchanged:
                try:
                    receipt_unchanged = (
                        _release_authority_digest(
                            request.acceptance_receipt,
                            request.acceptance_wave,
                        )
                        == authority_digest
                    )
                except _Reject:
                    receipt_unchanged = False
            if not receipt_unchanged:
                release_state = "unavailable"
                release_reason = "receipt-digest-changed"
            else:
                lease_dir = os.environ.get("IZANAGI_WAVE_LEASE_DIR")
                if not lease_dir:
                    release_state = "unavailable"
                    release_reason = "lease-dir-required"
                else:
                    try:
                        released = _wave_land_window.release(
                            Path(lease_dir),
                            request.acceptance_wave,
                            expected_main_sha=request.tested_main_sha,
                        )
                        release_state = str(released.get("state", "unavailable"))
                        source = released.get("source")
                        source_reason = (
                            source.get("reason") if isinstance(source, dict) else None
                        )
                        release_reason = (
                            str(source_reason) if source_reason is not None else "none"
                        )
                    except (Exception, KeyboardInterrupt):
                        release_state = "unavailable"
                        release_reason = "release-internal-error"
    print(
        f"lease_renew state={renew_state} reason={renew_reason}",
        file=sys.stderr,
        flush=True,
    )
    print(
        f"lease_release state={release_state} reason={release_reason}",
        file=sys.stderr,
        flush=True,
    )
    return result.rc


if __name__ == "__main__":
    sys.exit(main())
