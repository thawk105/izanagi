#!/usr/bin/env python3
"""dev-wave の producer と acceptance lease を安全に待つ。"""
from __future__ import annotations

import argparse
import errno
import hashlib
import importlib.abc
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Sequence


_WAITER_SOURCE_CHUNK_BYTES = 1024 * 1024
_SHA256_TEXT_RE = re.compile(r"[0-9a-f]{64}\Z")


def _exception_errno(exc: BaseException) -> int | None:
    if not isinstance(exc, OSError):
        return None
    try:
        candidate = OSError.errno.__get__(exc, type(exc))
    except Exception:
        return None
    return candidate if type(candidate) is int else None


@dataclass(frozen=True)
class _WaiterSourceUnavailable:
    exception_type: str
    errno: int | None = None


@dataclass
class _WaiterSourceBinding:
    """module 初期化直後に束縛した source inode を保持する。"""

    path: Path
    root_fd: int
    tools_fd: int
    source_fd: int
    initial_sha256: str = ""

    def bytes_sha256(self) -> str:
        if not stat.S_ISREG(os.fstat(self.source_fd).st_mode):
            raise OSError("bound waiter source is not a regular file")

        def read_once() -> tuple[str, int]:
            digest = hashlib.sha256()
            offset = 0
            while True:
                chunk = os.pread(
                    self.source_fd,
                    _WAITER_SOURCE_CHUNK_BYTES,
                    offset,
                )
                if not chunk:
                    return digest.hexdigest(), offset
                digest.update(chunk)
                offset += len(chunk)

        first = read_once()
        second = read_once()
        if first != second:
            raise OSError("bound waiter source changed while being read")
        return second[0]

    def close(self) -> None:
        """テスト用の明示 close。production binding は process lifetime 保持する。"""

        for name in ("source_fd", "tools_fd", "root_fd"):
            fd = getattr(self, name)
            if fd >= 0:
                try:
                    os.close(fd)
                finally:
                    setattr(self, name, -1)


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


def _bind_waiter_source(
    source_file: object,
    module_spec: object,
) -> _WaiterSourceBinding:
    """canonical tools path の source を root FD から非追従で束縛する。"""

    if not isinstance(source_file, str) or not source_file:
        raise ValueError("waiter __file__ is invalid")
    source_path = Path(os.path.abspath(source_file))
    if source_path.name != "dev_wave_wait.py" or source_path.parent.name != "tools":
        raise ValueError("waiter __file__ is not the canonical tools path")
    spec_origin: Path | None = None
    if module_spec is not None:
        loader = getattr(module_spec, "loader", None)
        if not isinstance(loader, importlib.abc.FileLoader):
            raise ValueError("waiter module spec does not use a file loader")
        origin = getattr(module_spec, "origin", None)
        if not isinstance(origin, str) or not origin:
            raise ValueError("waiter module spec origin is invalid")
        spec_origin = Path(os.path.abspath(origin))
    root_path = source_path.parent.parent
    directory_flags = (
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_DIRECTORY
    )
    source_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    root_fd = tools_fd = source_fd = -1
    try:
        root_before = os.stat(root_path, follow_symlinks=False)
        root_fd = os.open(root_path, directory_flags)
        root_opened = os.fstat(root_fd)
        if not stat.S_ISDIR(root_opened.st_mode) or not _same_inode(
            root_before,
            root_opened,
        ):
            raise OSError("waiter repository root is symlink/raced/non-directory")

        tools_before = os.stat(
            b"tools",
            dir_fd=root_fd,
            follow_symlinks=False,
        )
        tools_fd = os.open(
            b"tools",
            directory_flags,
            dir_fd=root_fd,
        )
        tools_opened = os.fstat(tools_fd)
        if not stat.S_ISDIR(tools_opened.st_mode) or not _same_inode(
            tools_before,
            tools_opened,
        ):
            raise OSError("waiter tools path is symlink/raced/non-directory")

        source_before = os.stat(
            b"dev_wave_wait.py",
            dir_fd=tools_fd,
            follow_symlinks=False,
        )
        source_fd = os.open(
            b"dev_wave_wait.py",
            source_flags,
            dir_fd=tools_fd,
        )
        source_opened = os.fstat(source_fd)
        if not stat.S_ISREG(source_opened.st_mode) or not _same_inode(
            source_before,
            source_opened,
        ):
            raise OSError("waiter source is symlink/raced/non-regular")
        if spec_origin is not None:
            origin_stat = os.stat(spec_origin, follow_symlinks=False)
            if not stat.S_ISREG(origin_stat.st_mode) or not _same_inode(
                origin_stat,
                source_opened,
            ):
                raise OSError("waiter module spec origin is not the bound source")
        binding = _WaiterSourceBinding(
            source_path,
            root_fd,
            tools_fd,
            source_fd,
        )
        binding.initial_sha256 = binding.bytes_sha256()
        return binding
    except BaseException:
        for fd in (source_fd, tools_fd, root_fd):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        raise


def _initialize_waiter_source_binding() -> (
    _WaiterSourceBinding | _WaiterSourceUnavailable
):
    try:
        return _bind_waiter_source(globals().get("__file__"), __spec__)
    except Exception as exc:
        return _WaiterSourceUnavailable(
            type(exc).__name__,
            _exception_errno(exc),
        )


# Python loader が source を compile した後の最初期に束縛する。compile 入力そのものの
# 証明ではなく、canonical file 起動でここから保持する source inode bytes の契約である。
_RUNNING_WAITER_SOURCE = _initialize_waiter_source_binding()


RC_OK = 0
RC_USAGE = 2
RC_FAIL_CLOSED = 70
RC_CLEANUP_FAILED = 74
RC_INTERRUPTED = 130

_PROGRAM = "dev-wave-wait"
_LEASE_ENV = "IZANAGI_WAVE_LEASE_DIR"
_PRODUCER_POLL_SECONDS = 5
_PRODUCER_GRACE_SECONDS = 30
_DEFAULT_ACCEPTANCE_POLL_SECONDS = 30
_MIN_ACCEPTANCE_POLL_SECONDS = 30
_MAX_ACCEPTANCE_POLL_SECONDS = 120
_DEFAULT_ACCEPTANCE_MAX_WAIT_SECONDS = 7200
_STAGE_TIMEOUT_SECONDS = 300
_STAGE_TERMINATION_SECONDS = 5
_LEASE_TTL_SECONDS = 2400
_RECEIPT_PUBLISH_MIN_TTL_SECONDS = _STAGE_TIMEOUT_SECONDS
_RECEIPT_SCHEMA_VERSION = "dev-wave-acceptance-receipt/v3"
_RECEIPT_AUTHORITY_KIND = "dev-wave-wait-acceptance"
_RECEIPT_TEMP_PREFIX = ".dev-wave-acceptance-receipt-"
_DETAIL_TEXT_MAX_BYTES = 256
_ATTESTATION_DETAIL_MAX_BYTES = 2048
_LOG_HASH_CHUNK_BYTES = 1024 * 1024
_EFFECTIVE_SCHEDULER_PREFIX = b"IZANAGI_EFFECTIVE_SCHEDULER_V1 "
_EFFECTIVE_SCHEDULERS = frozenset({"loadgroup", "serial", "unknown"})
_MARKER_PAYLOAD_MAX_BYTES = 4096
_RED_CHECK_SCHEMA_VERSION = "izanagi-acceptance-red-check/v1"
_RED_CHECK_RECEIPT_SUFFIX = ".acceptance-red-check.json"
_TASK_RUN_ID_ENV = "IZANAGI_TASK_RUN_ID"
_TASK_RUNS_ROOT_ENV = "IZANAGI_TASK_RUNS_ROOT"
_PYTEST_ENV_KEYS = ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")
_GIT_EXE = "/usr/bin/git"
_GIT_CONFIG = (
    "-c", "core.hooksPath=/dev/null",
    "-c", "core.fsmonitor=false",
    "-c", "core.useBuiltinFSMonitor=false",
    "-c", "maintenance.auto=false",
    "-c", "gc.auto=0",
    "-c", "protocol.file.allow=never",
)
_GIT_ENV_KEYS = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_NOSYSTEM",
    }
)
_RED_CHECKER_PATH = "tools/check_acceptance_reds.py"
_RED_CHECKER_BOOTSTRAP = (
    "import os,sys\n"
    "if os.environ.get('PYTHONDONTWRITEBYTECODE'):\n"
    "    sys.dont_write_bytecode = True\n"
    "source = sys.stdin.buffer.read()\n"
    "namespace = {\n"
    "    '__name__': '_izanagi_acceptance_red_checker',\n"
    "    '__file__': '<tested-main:tools/check_acceptance_reds.py>',\n"
    "}\n"
    "exec(compile(source, namespace['__file__'], 'exec'), namespace)\n"
    "repo = __import__('pathlib').Path(sys.argv[1])\n"
    "raise SystemExit(namespace['main'](sys.argv[2:], repo_root=repo))\n"
)
_CLEAN_STATUS_ARGV = (
    "git", "status", "--porcelain", "--untracked-files=all",
    "--ignore-submodules=none",
)
_INDEX_FLAGS_ARGV = ("git", "ls-files", "-v", "-z")
_SUBMODULE_INDEX_FLAGS_ARGV = (
    "git", "submodule", "foreach", "--recursive", "--quiet",
    "git ls-files -v -z",
)
_SUBMODULE_READY_ARGV = ("git", "submodule", "status", "--recursive")
_HANDLED_SIGNALS = (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)
_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_HOLDER_RE = re.compile(r"[0-9a-f]{12}\Z")
_CLAIM_STATES = frozenset(
    {"acquired", "held-self", "held", "queued", "stale-held", "unavailable"}
)
_ACCEPTED_CLAIM_STATES = frozenset({"acquired", "held-self"})
_POLLING_CLAIM_STATES = frozenset({"held", "queued"})
_RELEASED_STATES = frozenset({"released", "free", "not-owner"})


@dataclass(frozen=True)
class _CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class _BinaryCommandResult:
    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""


class _TipWaiterBlobError(Exception):
    def __init__(self, reason: str, returncode: int | None = None):
        super().__init__(reason)
        self.reason = reason
        self.returncode = returncode


@dataclass(frozen=True)
class _Outcome:
    rc: int
    stage: str | None = None
    source_rc: int | None = None
    detail: str | None = None


@dataclass(frozen=True)
class _TreeFingerprint:
    digest: str
    head_sha: str
    status_bytes: int
    diff_bytes: int
    submodule_status_bytes: int


@dataclass(frozen=True)
class _ClaimContext:
    state: str
    holder: str | None
    main_sha: str | None
    age_seconds: int | None


@dataclass(frozen=True)
class _AcceptanceEnvironment:
    pytest_addopts: str | None
    pytest_plugins: str | None
    task_run_id: str | None
    task_runs_root: str | None

    def as_json(self) -> dict[str, str | None]:
        return {
            "PYTEST_ADDOPTS": self.pytest_addopts,
            "PYTEST_PLUGINS": self.pytest_plugins,
            _TASK_RUN_ID_ENV: self.task_run_id,
            _TASK_RUNS_ROOT_ENV: self.task_runs_root,
        }


@dataclass(frozen=True)
class _RedCheckResult:
    checker_rc: int
    checker_status: str
    checker_blob_sha: str
    checker_receipt_sha256: str
    red_nodeids: tuple[str, ...]


@dataclass(frozen=True)
class _RedCheckerBinding:
    source: bytes
    blob_sha: str


class _PidState(Enum):
    ALIVE = "alive"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class _Effects:
    run: Callable[[Sequence[str], Path, bool], _CommandResult]
    run_unbounded: Callable[[Sequence[str], Path, bool], _CommandResult]
    sleep: Callable[[float], None]
    kill: Callable[[int, int], None]
    is_file: Callable[[Path], bool]
    read_text: Callable[[Path], str]
    getenv: Callable[[str], str | None]
    monotonic: Callable[[], float]
    write_temp: Callable[[bytes], Path]
    unlink: Callable[[Path], None]
    path_exists: Callable[[Path], bool] | None = None
    is_dir: Callable[[Path], bool] | None = None
    resolve_path: Callable[[Path], Path] | None = None
    write_receipt_temp: Callable[[Path, bytes], Path] | None = None
    rename: Callable[[Path, Path], None] | None = None
    run_logged: Callable[[Sequence[str], Path, Path], _CommandResult] | None = None
    read_bytes: Callable[[Path], bytes] | None = None
    is_symlink: Callable[[Path], bool] | None = None
    sha256_file: Callable[[Path], str] | None = None
    inspect_acceptance_log: Callable[[Path], tuple[str, str]] | None = None
    running_waiter_bytes_sha256: Callable[[], object] | None = None
    tip_waiter_bytes_sha256: Callable[[Path, str], object] | None = None
    run_with_input: (
        Callable[[Sequence[str], Path, bool, bytes], _BinaryCommandResult] | None
    ) = None


class _LeaseOwnership(Enum):
    # HELD_SELF は merge abort 権限だけを持ち、lease release 権限は持たない。
    NONE = "none"
    UNKNOWN = "unknown"
    ACQUIRED = "acquired"
    HELD_SELF = "held-self"
    RETAINED = "retained"


@dataclass
class _AcceptanceLifecycle:
    ownership: _LeaseOwnership = _LeaseOwnership.NONE
    acquired_at: float | None = None
    merge_pending: bool = False
    cleanup_failure: _Outcome | None = None
    receipt_published: bool = False


class _StageFailure(Exception):
    def __init__(
        self,
        stage: str,
        rc: int = RC_FAIL_CLOSED,
        source_rc: int | None = None,
        detail: str | None = None,
    ):
        super().__init__(stage)
        self.outcome = _Outcome(rc, stage, source_rc, detail)


class _SignalReceived(BaseException):
    def __init__(self, signum: int):
        super().__init__(signum)
        self.signum = signum


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


def _run_subprocess(
    argv: Sequence[str], cwd: Path, capture: bool, *, stage_policy: bool
) -> _CommandResult:
    values = list(argv)
    kwargs: dict[str, object] = {
        "cwd": cwd,
        "text": True,
        "shell": False,
    }
    direct_git = bool(values and values[0] == "git")
    provenance_checker = (
        len(values) >= 2
        and Path(values[1]).name == "check_ai_provenance.py"
    )
    git_discovery_stage = direct_git or provenance_checker
    if git_discovery_stage:
        kwargs["env"] = {
            key: value for key, value in os.environ.items() if key not in _GIT_ENV_KEYS
        }
    bounded_stage = stage_policy and git_discovery_stage
    if (
        not bounded_stage
        and stage_policy
        and len(values) >= 2
        and Path(values[1]).name == "wave_land_window.py"
    ):
        bounded_stage = True
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if not bounded_stage:
        result = subprocess.run(values, check=False, **kwargs)
        return _CommandResult(
            result.returncode,
            result.stdout if capture else "",
            result.stderr if capture else "",
        )

    # Stage subprocess だけを専用 group に閉じる。受入 command は無制限のまま。
    process = subprocess.Popen(values, start_new_session=True, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=_STAGE_TIMEOUT_SECONDS)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=_STAGE_TERMINATION_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=_STAGE_TERMINATION_SECONDS)
            except subprocess.TimeoutExpired:
                pass
        raise
    return _CommandResult(
        process.returncode,
        stdout if capture else "",
        stderr if capture else "",
    )


def _run_subprocess_with_input(
    argv: Sequence[str],
    cwd: Path,
    capture: bool,
    content: bytes,
) -> _BinaryCommandResult:
    values = list(argv)
    kwargs: dict[str, object] = {
        "cwd": cwd,
        "shell": False,
        "text": False,
    }
    direct_git = bool(values and values[0] == _GIT_EXE)
    if direct_git:
        kwargs["env"] = _git_env()
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if not direct_git:
        # checker 内側の 5100 秒契約を外から短縮しない。
        result = subprocess.run(
            values,
            input=content,
            check=False,
            **kwargs,
        )
        return _BinaryCommandResult(
            result.returncode,
            result.stdout if capture else b"",
            result.stderr if capture else b"",
        )

    # blob 束縛に使う短い Git stage だけは既存 stage 上限で閉じる。
    process = subprocess.Popen(
        values,
        stdin=subprocess.PIPE,
        start_new_session=True,
        **kwargs,
    )
    try:
        stdout, stderr = process.communicate(
            input=content,
            timeout=_STAGE_TIMEOUT_SECONDS,
        )
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=_STAGE_TERMINATION_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=_STAGE_TERMINATION_SECONDS)
            except subprocess.TimeoutExpired:
                pass
        raise
    return _BinaryCommandResult(
        process.returncode,
        stdout if capture else b"",
        stderr if capture else b"",
    )


def _default_run_with_input(
    argv: Sequence[str],
    cwd: Path,
    capture: bool,
    content: bytes,
) -> _BinaryCommandResult:
    return _run_subprocess_with_input(argv, cwd, capture, content)


def _default_run(argv: Sequence[str], cwd: Path, capture: bool) -> _CommandResult:
    return _run_subprocess(argv, cwd, capture, stage_policy=True)


def _default_run_unbounded(
    argv: Sequence[str], cwd: Path, capture: bool
) -> _CommandResult:
    return _run_subprocess(argv, cwd, capture, stage_policy=False)


def _default_run_logged(
    argv: Sequence[str], cwd: Path, log_file: Path
) -> _CommandResult:
    with log_file.open("xb") as stream:
        result = subprocess.run(
            list(argv),
            cwd=cwd,
            shell=False,
            check=False,
            stdin=None,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    return _CommandResult(result.returncode)


def _default_read_text(path: Path) -> str:
    # newline translation を無効にし、検査した UTF-8 bytes を一時 file へ再現する。
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _default_sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(_LOG_HASH_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _default_running_waiter_bytes_sha256() -> object:
    binding = _RUNNING_WAITER_SOURCE
    if isinstance(binding, _WaiterSourceUnavailable):
        return binding
    current = binding.bytes_sha256()
    if current != binding.initial_sha256:
        raise OSError("bound waiter source changed since module initialization")
    return current


def _default_tip_waiter_bytes_sha256(repo: Path, tip_sha: str) -> object:
    argv = (
        "git",
        "cat-file",
        "blob",
        f"{tip_sha}:tools/dev_wave_wait.py",
    )
    try:
        process = subprocess.Popen(
            argv,
            cwd=repo,
            shell=False,
            text=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            env={
                key: value
                for key, value in os.environ.items()
                if key not in _GIT_ENV_KEYS
            },
        )
    except (OSError, ValueError) as exc:
        raise _TipWaiterBlobError(
            f"git-cat-file-start:{type(exc).__name__}",
        ) from exc
    try:
        stdout, _stderr = process.communicate(timeout=_STAGE_TIMEOUT_SECONDS)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=_STAGE_TERMINATION_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=_STAGE_TERMINATION_SECONDS)
            except subprocess.TimeoutExpired:
                pass
        raise
    if process.returncode != 0:
        raise _TipWaiterBlobError("git-cat-file", process.returncode)
    if not isinstance(stdout, bytes):
        raise _TipWaiterBlobError("git-cat-file-output-type")
    return hashlib.sha256(stdout).hexdigest()


def _scan_acceptance_log_chunks(
    chunks: Iterable[bytes],
) -> tuple[str, list[bytes]]:
    digest = hashlib.sha256()
    marker_payloads: list[bytes] = []
    prefixes = (
        _EFFECTIVE_SCHEDULER_PREFIX,
        b"| " + _EFFECTIVE_SCHEDULER_PREFIX,
    )
    at_line_start = True
    candidate: bytes | None = None
    candidate_offset = 0
    payload: bytearray | None = None
    payload_overflow = False

    def finish_line() -> None:
        nonlocal at_line_start, candidate, candidate_offset
        nonlocal payload, payload_overflow
        if payload is not None and len(marker_payloads) < 2:
            if not payload_overflow and payload.endswith(b"\r"):
                del payload[-1:]
            if payload_overflow:
                payload.append(0)
            marker_payloads.append(bytes(payload))
        at_line_start = True
        candidate = None
        candidate_offset = 0
        payload = None
        payload_overflow = False

    for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise TypeError("acceptance log chunk must be bytes")
        digest.update(chunk)
        offset = 0
        chunk_size = len(chunk)
        while offset < chunk_size:
            if len(marker_payloads) >= 2:
                newline = chunk.find(b"\n", offset)
                if newline < 0:
                    break
                offset = newline + 1
                continue
            if payload is not None:
                newline = chunk.find(b"\n", offset)
                end = chunk_size if newline < 0 else newline
                available = _MARKER_PAYLOAD_MAX_BYTES - len(payload)
                if available > 0:
                    payload.extend(chunk[offset:min(end, offset + available)])
                if end - offset > max(available, 0):
                    payload_overflow = True
                if newline < 0:
                    break
                finish_line()
                offset = newline + 1
                continue
            if candidate is not None:
                byte = chunk[offset]
                if byte == candidate[candidate_offset]:
                    candidate_offset += 1
                    offset += 1
                    if candidate_offset == len(candidate):
                        payload = bytearray()
                    continue
                at_line_start = False
                candidate = None
                candidate_offset = 0
            if at_line_start:
                byte = chunk[offset]
                candidate = next(
                    (prefix for prefix in prefixes if prefix[0] == byte),
                    None,
                )
                if candidate is not None:
                    candidate_offset = 1
                    offset += 1
                    if candidate_offset == len(candidate):
                        payload = bytearray()
                    continue
                at_line_start = False
            newline = chunk.find(b"\n", offset)
            if newline < 0:
                break
            finish_line()
            offset = newline + 1
    if candidate is not None or payload is not None or not at_line_start:
        finish_line()
    return digest.hexdigest(), marker_payloads


def _bounded_detail_text(value: object) -> str:
    if not isinstance(value, str):
        value = type(value).__name__
    escaped = bytearray()
    for byte in value.encode("utf-8", "backslashreplace"):
        if 0x20 <= byte <= 0x7E:
            escaped.append(byte)
        else:
            escaped.extend(f"\\x{byte:02x}".encode("ascii"))
        if len(escaped) > _DETAIL_TEXT_MAX_BYTES:
            return (
                escaped[: _DETAIL_TEXT_MAX_BYTES - 3].decode("ascii") + "..."
            )
    return escaped.decode("ascii")


def _normalized_detail_value(value: object, *, depth: int = 0) -> object:
    if value is None or type(value) in {bool, int}:
        return value
    if isinstance(value, str):
        return _bounded_detail_text(value)
    if depth >= 4:
        return type(value).__name__
    if type(value) is dict:
        normalized: dict[str, object] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 32:
                normalized["detail_items_truncated"] = True
                break
            normalized[_bounded_detail_text(key)] = _normalized_detail_value(
                item,
                depth=depth + 1,
            )
        return normalized
    if type(value) in {list, tuple}:
        normalized_items = [
            _normalized_detail_value(item, depth=depth + 1)
            for item in value[:32]
        ]
        if len(value) > 32:
            normalized_items.append("detail_items_truncated")
        return normalized_items
    return _bounded_detail_text(value)


def _attestation_detail(reason: str, observed: object) -> str:
    try:
        normalized_reason = _bounded_detail_text(reason)
        payload = {
            "reason": normalized_reason,
            "observed": _normalized_detail_value(observed),
        }
        serialized = json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        serialized_bytes = len(serialized.encode("ascii"))
        if serialized_bytes <= _ATTESTATION_DETAIL_MAX_BYTES:
            return serialized
        return json.dumps(
            {
                "reason": normalized_reason,
                "observed": {
                    "detail_truncated": True,
                    "serialized_bytes": serialized_bytes,
                },
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except Exception:
        fallback_reason = (
            reason
            if type(reason) is str and reason.isascii() and len(reason) <= 64
            else "detail"
        )
        return json.dumps(
            {
                "reason": fallback_reason,
                "observed": {"detail_generation_failed": True},
            },
            separators=(",", ":"),
            sort_keys=True,
        )


def _exception_observed(exc: BaseException) -> dict[str, object]:
    return {
        "exception_type": type(exc).__name__,
        "errno": _exception_errno(exc),
    }


def _malformed_sha_observed(value: str) -> dict[str, object]:
    try:
        stdout_bytes = len(str.encode(value, "utf-8", "surrogatepass"))
        if not str.isascii(value):
            stdout_class = "non-ascii"
        elif len(value) != 40:
            stdout_class = "wrong-length"
        else:
            stdout_class = "non-hex"
    except Exception:
        stdout_bytes = None
        stdout_class = "unclassifiable"
    return {
        "failure_kind": "invalid-sha",
        "stdout_bytes": stdout_bytes,
        "stdout_class": stdout_class,
    }


def _diagnostic_bool(check: Callable[[], object]) -> bool | None:
    try:
        return bool(check())
    except Exception:
        return None


def _detail_observed(detail: str | None) -> dict[str, object]:
    if detail is None:
        return {}
    try:
        payload = json.loads(detail)
        observed = payload.get("observed") if type(payload) is dict else None
        if type(observed) is dict:
            return observed
    except Exception:
        pass
    return {}


def _detail_failure_kind(detail: str | None) -> str:
    failure_kind = _detail_observed(detail).get("failure_kind")
    return (
        _bounded_detail_text(failure_kind)
        if isinstance(failure_kind, str)
        else "unknown"
    )


def _nested_detail(detail: str | None) -> object:
    if detail is None:
        return None
    try:
        payload = json.loads(detail)
        if type(payload) is dict:
            return payload
    except Exception:
        pass
    return _bounded_detail_text(detail)


def _scheduler_from_marker_payloads(payloads: Sequence[bytes]) -> str:
    stage = "acceptance-scheduler-attestation"
    observed = [
        payload[:256].decode("utf-8", "backslashreplace")
        for payload in payloads
    ]
    if len(payloads) != 1:
        raise _StageFailure(
            stage,
            detail=_attestation_detail("marker-count", observed),
        )
    try:
        text = payloads[0].decode("utf-8")
    except UnicodeError:
        raise _StageFailure(
            stage,
            detail=_attestation_detail("marker-encoding", observed[0]),
        ) from None
    try:
        payload = _parse_json_object(text, stage=stage)
    except _StageFailure:
        raise _StageFailure(
            stage,
            detail=_attestation_detail("marker-json", observed[0]),
        ) from None
    if set(payload) != {"effective_scheduler"}:
        raise _StageFailure(
            stage,
            detail=_attestation_detail("marker-fields", payload),
        )
    scheduler = payload["effective_scheduler"]
    if not isinstance(scheduler, str) or scheduler not in _EFFECTIVE_SCHEDULERS:
        raise _StageFailure(
            stage,
            detail=_attestation_detail("scheduler-value", scheduler),
        )
    return scheduler


def _default_inspect_acceptance_log(path: Path) -> tuple[str, str]:
    stage = "acceptance-scheduler-attestation"
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except (OSError, TypeError, ValueError):
        raise _StageFailure(
            stage,
            detail=_attestation_detail("log-open", os.fspath(path)),
        ) from None
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise _StageFailure(
                stage,
                detail=_attestation_detail("log-type", before.st_mode),
            )

        total_read = 0

        def chunks():
            nonlocal total_read
            while True:
                chunk = os.read(fd, _LOG_HASH_CHUNK_BYTES)
                if not chunk:
                    return
                total_read += len(chunk)
                yield chunk

        log_sha256, payloads = _scan_acceptance_log_chunks(chunks())
        after = os.fstat(fd)
    except _StageFailure:
        raise
    except (OSError, TypeError, ValueError):
        raise _StageFailure(
            stage,
            detail=_attestation_detail("log-read", os.fspath(path)),
        ) from None
    finally:
        os.close(fd)
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ) or total_read != before.st_size:
        raise _StageFailure(
            stage,
            detail=_attestation_detail(
                "log-changed",
                {
                    "before": [
                        before.st_dev,
                        before.st_ino,
                        before.st_size,
                        before.st_mtime_ns,
                    ],
                    "after": [
                        after.st_dev,
                        after.st_ino,
                        after.st_size,
                        after.st_mtime_ns,
                    ],
                    "total_read": total_read,
                },
            ),
        )
    return log_sha256, _scheduler_from_marker_payloads(payloads)


def _default_write_temp(content: bytes) -> Path:
    fd, raw_path = tempfile.mkstemp(prefix="dev-wave-wait-message-", suffix=".txt")
    path = Path(raw_path)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _default_write_receipt_temp(final_path: Path, content: bytes) -> Path:
    fd, raw_path = tempfile.mkstemp(
        prefix=_RECEIPT_TEMP_PREFIX,
        suffix=".tmp",
        dir=final_path.parent,
    )
    path = Path(raw_path)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _default_effects() -> _Effects:
    return _Effects(
        run=_default_run,
        run_unbounded=_default_run_unbounded,
        sleep=time.sleep,
        kill=os.kill,
        is_file=Path.is_file,
        read_text=_default_read_text,
        getenv=os.environ.get,
        monotonic=time.monotonic,
        write_temp=_default_write_temp,
        unlink=lambda path: path.unlink(missing_ok=True),
        path_exists=lambda path: os.path.lexists(path),
        is_dir=Path.is_dir,
        resolve_path=lambda path: path.resolve(strict=False),
        write_receipt_temp=_default_write_receipt_temp,
        rename=os.rename,
        run_logged=_default_run_logged,
        read_bytes=Path.read_bytes,
        is_symlink=Path.is_symlink,
        sha256_file=_default_sha256_file,
        inspect_acceptance_log=_default_inspect_acceptance_log,
        running_waiter_bytes_sha256=_default_running_waiter_bytes_sha256,
        tip_waiter_bytes_sha256=_default_tip_waiter_bytes_sha256,
        run_with_input=_default_run_with_input,
    )


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _StageFailure("cli-usage", RC_USAGE)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError:
        raise argparse.ArgumentTypeError("positive integer required") from None
    if parsed <= 0:
        raise argparse.ArgumentTypeError("positive integer required")
    return parsed


def _poll_seconds(value: str) -> int:
    parsed = _positive_int(value)
    if not _MIN_ACCEPTANCE_POLL_SECONDS <= parsed <= _MAX_ACCEPTANCE_POLL_SECONDS:
        raise argparse.ArgumentTypeError("poll outside policy range")
    return parsed


def _producer_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog=f"{_PROGRAM} producer", add_help=True)
    parser.add_argument("--done-file", type=Path, required=True)
    parser.add_argument("--artifact-file", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pid")
    source.add_argument("--pid-file", type=Path)
    parser.add_argument("--max-wait-seconds", type=_positive_int)
    return parser


def _acceptance_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog=f"{_PROGRAM} acceptance", add_help=True)
    parser.add_argument("--wave", required=True)
    parser.add_argument("--lease-dir", type=Path)
    parser.add_argument("--receipt-file", type=Path, required=True)
    parser.add_argument("--log-file", type=Path, required=True)
    parser.add_argument("--merge-message-file", type=Path)
    parser.add_argument("--owned-path", type=Path, action="append", default=[])
    parser.add_argument(
        "--poll-seconds",
        type=_poll_seconds,
        default=_DEFAULT_ACCEPTANCE_POLL_SECONDS,
    )
    parser.add_argument(
        "--max-wait-seconds",
        type=_positive_int,
        default=_DEFAULT_ACCEPTANCE_MAX_WAIT_SECONDS,
    )
    return parser


def _parse_cli(argv: Sequence[str]) -> tuple[str, argparse.Namespace, list[str]]:
    values = list(argv)
    if not values:
        raise _StageFailure("cli-usage", RC_USAGE)
    command = values[0]
    if command == "producer":
        args = _producer_parser().parse_args(values[1:])
        return command, args, []
    if command != "acceptance":
        raise _StageFailure("cli-usage", RC_USAGE)
    try:
        delimiter = values.index("--", 1)
    except ValueError:
        raise _StageFailure("cli-usage", RC_USAGE) from None
    command_argv = values[delimiter + 1 :]
    if not command_argv:
        raise _StageFailure("cli-usage", RC_USAGE)
    args = _acceptance_parser().parse_args(values[1:delimiter])
    return command, args, command_argv


def _parse_pid(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise _StageFailure("pid-input", RC_USAGE)
    pid = int(value, 10)
    if pid <= 0:
        raise _StageFailure("pid-input", RC_USAGE)
    return pid


def _resolve_pid(
    direct: str | None,
    pid_file: Path | None,
    effects: _Effects,
) -> int:
    if (direct is None) == (pid_file is None):
        raise _StageFailure("pid-input", RC_USAGE)
    if direct is not None:
        return _parse_pid(direct)
    assert pid_file is not None
    try:
        raw = effects.read_text(pid_file)
    except (OSError, UnicodeError):
        raise _StageFailure("pid-file", RC_USAGE) from None
    return _parse_pid(raw.strip())


def _parse_process_identity(value: str, pid: int) -> tuple[str, int]:
    prefix = f"{pid} ("
    if not value.startswith(prefix):
        raise ValueError("pid mismatch")
    close = value.rfind(")")
    if close < len(prefix):
        raise ValueError("malformed stat")
    remaining = value[close + 1 :].split()
    if (
        len(remaining) <= 19
        or len(remaining[0]) != 1
        or not remaining[19].isascii()
        or not remaining[19].isdecimal()
    ):
        raise ValueError("missing starttime")
    return remaining[0], int(remaining[19], 10)


def _parse_start_time(value: str, pid: int) -> int:
    return _parse_process_identity(value, pid)[1]


def _read_start_time(pid: int, effects: _Effects) -> int:
    return _parse_start_time(effects.read_text(Path(f"/proc/{pid}/stat")), pid)


def _read_process_identity(pid: int, effects: _Effects) -> tuple[str, int]:
    return _parse_process_identity(
        effects.read_text(Path(f"/proc/{pid}/stat")), pid
    )


def _initial_start_time(pid: int, effects: _Effects) -> int | None:
    try:
        return _read_start_time(pid, effects)
    except (OSError, UnicodeError, ValueError):
        print(
            f"producer: /proc/{pid}/stat を読めないため pid-only へ縮退します",
            file=sys.stderr,
        )
        return None


def _pid_state(pid: int, start_time: int | None, effects: _Effects) -> _PidState:
    try:
        effects.kill(pid, 0)
    except ProcessLookupError:
        return _PidState.DEAD
    except PermissionError:
        return _PidState.UNKNOWN
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return _PidState.DEAD
        return _PidState.UNKNOWN
    if start_time is None:
        return _PidState.ALIVE
    try:
        process_state, current = _read_process_identity(pid, effects)
    except (OSError, UnicodeError, ValueError):
        return _PidState.UNKNOWN
    if process_state == "Z":
        return _PidState.DEAD
    return _PidState.ALIVE if current == start_time else _PidState.DEAD


def wait_for_producer(
    *,
    done_file: Path,
    artifact_file: Path,
    pid: int,
    max_wait_seconds: int | None,
    effects: _Effects,
) -> _Outcome:
    started = effects.monotonic()
    start_time = _initial_start_time(pid, effects)
    while True:
        state = _pid_state(pid, start_time, effects)
        if state is _PidState.UNKNOWN:
            return _Outcome(RC_FAIL_CLOSED, "producer-liveness")
        if state is _PidState.DEAD:
            break
        if max_wait_seconds is not None:
            try:
                elapsed = effects.monotonic() - started
            except Exception:
                return _Outcome(RC_FAIL_CLOSED, "producer-clock")
            if elapsed + _PRODUCER_POLL_SECONDS > max_wait_seconds:
                return _Outcome(RC_FAIL_CLOSED, "producer-timeout")
        effects.sleep(_PRODUCER_POLL_SECONDS)

    grace_elapsed = 0
    while True:
        if effects.is_file(done_file) and effects.is_file(artifact_file):
            return _Outcome(RC_OK)
        if grace_elapsed >= _PRODUCER_GRACE_SECONDS:
            return _Outcome(RC_FAIL_CLOSED, "producer-files")
        effects.sleep(_PRODUCER_POLL_SECONDS)
        grace_elapsed += _PRODUCER_POLL_SECONDS


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _parse_json_object(value: str, *, stage: str) -> dict[str, object]:
    try:
        parsed = json.loads(value, object_pairs_hook=_no_duplicate_keys)
    except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError):
        raise _StageFailure(stage) from None
    if not isinstance(parsed, dict):
        raise _StageFailure(stage)
    return parsed


def _run_capture(
    effects: _Effects,
    argv: Sequence[str],
    repo: Path,
    stage: str,
    *,
    diagnostic_reason: str | None = None,
    diagnostic_observed: dict[str, object] | None = None,
) -> _CommandResult:
    try:
        result = effects.run(tuple(argv), repo, True)
    except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
        detail = None
        if diagnostic_reason is not None:
            detail = _attestation_detail(
                diagnostic_reason,
                {
                    **({} if diagnostic_observed is None else diagnostic_observed),
                    "failure_kind": "command",
                    "source_rc": None,
                    "exception_type": type(exc).__name__,
                },
            )
        raise _StageFailure(stage, detail=detail) from None
    if result.returncode != 0:
        detail = None
        if diagnostic_reason is not None:
            detail = _attestation_detail(
                diagnostic_reason,
                {
                    **({} if diagnostic_observed is None else diagnostic_observed),
                    "failure_kind": "command",
                    "source_rc": result.returncode,
                    "exception_type": None,
                },
            )
        raise _StageFailure(
            stage,
            source_rc=result.returncode,
            detail=detail,
        )
    return result


def _main_sha(
    effects: _Effects,
    repo: Path,
    stage: str,
    *,
    diagnostic_reason: str | None = None,
) -> str:
    result = _run_capture(
        effects,
        ("git", "rev-parse", "main"),
        repo,
        stage,
        diagnostic_reason=diagnostic_reason,
    )
    value = result.stdout.strip()
    if _SHA_RE.fullmatch(value) is None:
        detail = (
            None
            if diagnostic_reason is None
            else _attestation_detail(
                diagnostic_reason,
                _malformed_sha_observed(value),
            )
        )
        raise _StageFailure(stage, detail=detail)
    return value


def _head_sha(effects: _Effects, repo: Path, stage: str) -> str:
    result = _run_capture(effects, ("git", "rev-parse", "HEAD"), repo, stage)
    value = result.stdout.strip()
    if _SHA_RE.fullmatch(value) is None:
        raise _StageFailure(stage)
    return value


def _check_index_flags(effects: _Effects, repo: Path, stage: str) -> None:
    for argv in (_INDEX_FLAGS_ARGV, _SUBMODULE_INDEX_FLAGS_ARGV):
        result = _run_capture(effects, argv, repo, stage)
        for record in result.stdout.split("\0"):
            if not record:
                continue
            if len(record) < 3 or record[1] != " ":
                raise _StageFailure(stage)
            tag = record[0]
            if tag == "S" or tag.islower():
                raise _StageFailure(stage)


def _tree_fingerprint(
    effects: _Effects,
    repo: Path,
    stage: str,
    status_output: str,
) -> _TreeFingerprint:
    head_sha = _head_sha(effects, repo, stage)
    diff_output = _run_capture(
        effects,
        ("git", "diff", "--binary", "--no-ext-diff", "HEAD", "--"),
        repo,
        stage,
    ).stdout
    submodule_output = _run_capture(
        effects,
        ("git", "submodule", "status", "--recursive"),
        repo,
        stage,
    ).stdout
    try:
        elements = (
            (b"head-sha", head_sha.encode("ascii")),
            (b"clean-status", status_output.encode("utf-8")),
            (b"head-diff", diff_output.encode("utf-8")),
            (b"submodule-status", submodule_output.encode("utf-8")),
        )
    except UnicodeError:
        raise _StageFailure(stage) from None
    digest = hashlib.sha256()
    lengths: dict[bytes, int] = {}
    for label, payload in elements:
        digest.update(label)
        digest.update(b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
        lengths[label] = len(payload)
    return _TreeFingerprint(
        digest=digest.hexdigest(),
        head_sha=head_sha,
        status_bytes=lengths[b"clean-status"],
        diff_bytes=lengths[b"head-diff"],
        submodule_status_bytes=lengths[b"submodule-status"],
    )


def _fingerprint_json(fingerprint: _TreeFingerprint) -> dict[str, object]:
    return {
        "digest": fingerprint.digest,
        "head_sha": fingerprint.head_sha,
        "status_bytes": fingerprint.status_bytes,
        "diff_bytes": fingerprint.diff_bytes,
        "submodule_status_bytes": fingerprint.submodule_status_bytes,
    }


def _waiter_source_gate_failure(
    *,
    tested_tip: str,
    reason: str,
    running_sha256: object = None,
    tip_sha256: object = None,
    diagnostic_observed: dict[str, object] | None = None,
    source_rc: int | None = None,
) -> _StageFailure:
    def diagnostic_value(value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            if _SHA256_TEXT_RE.fullmatch(value) is not None:
                return value
            try:
                text_bytes = len(value.encode("utf-8", "surrogatepass"))
                if not value.isascii():
                    text_class = "non-ascii"
                elif len(value) != 64:
                    text_class = "wrong-length"
                else:
                    text_class = "non-hex"
            except Exception:
                text_bytes = None
                text_class = "unclassifiable"
            return {
                "type": "str",
                "text_bytes": text_bytes,
                "text_class": text_class,
            }
        return {"type": _bounded_detail_text(type(value).__name__)}

    observed: dict[str, object] = {
        "actual_sha256": diagnostic_value(running_sha256),
        "expected_sha256": diagnostic_value(tip_sha256),
        "tested_tip": tested_tip,
    }
    if diagnostic_observed is not None:
        observed.update(diagnostic_observed)
    return _StageFailure(
        "restart-required",
        source_rc=source_rc,
        detail=_attestation_detail(
            "receipt-waiter-" + _bounded_detail_text(reason),
            observed,
        ),
    )


def _verify_waiter_source_bytes(
    effects: _Effects,
    repo: Path,
    tested_tip: str,
) -> None:
    running_sha256: object = None
    tip_sha256: object = None
    try:
        running_sha256 = (
            effects.running_waiter_bytes_sha256
            or _default_running_waiter_bytes_sha256
        )()
    except Exception as exc:
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="running-source-read-failed",
            diagnostic_observed=_exception_observed(exc),
        ) from None
    if isinstance(running_sha256, _WaiterSourceUnavailable):
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="running-source-binding-unavailable",
            diagnostic_observed={
                "exception_type": running_sha256.exception_type,
                "errno": running_sha256.errno,
            },
        )
    if not isinstance(running_sha256, str):
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="running-sha256-type",
            running_sha256=running_sha256,
        )
    if _SHA256_TEXT_RE.fullmatch(running_sha256) is None:
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="running-sha256-format",
            running_sha256=running_sha256,
        )

    try:
        tip_sha256 = (
            effects.tip_waiter_bytes_sha256
            or _default_tip_waiter_bytes_sha256
        )(repo, tested_tip)
    except _TipWaiterBlobError as exc:
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason=exc.reason,
            running_sha256=running_sha256,
            source_rc=exc.returncode,
        ) from None
    except Exception as exc:
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="tip-blob-read-failed",
            running_sha256=running_sha256,
            diagnostic_observed=_exception_observed(exc),
        ) from None
    if not isinstance(tip_sha256, str):
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="tip-sha256-type",
            running_sha256=running_sha256,
            tip_sha256=tip_sha256,
        )
    if _SHA256_TEXT_RE.fullmatch(tip_sha256) is None:
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="tip-sha256-format",
            running_sha256=running_sha256,
            tip_sha256=tip_sha256,
        )
    if running_sha256 != tip_sha256:
        raise _waiter_source_gate_failure(
            tested_tip=tested_tip,
            reason="sha256-mismatch",
            running_sha256=running_sha256,
            tip_sha256=tip_sha256,
        )


def _path_exists(effects: _Effects, path: Path) -> bool:
    if effects.path_exists is not None:
        return effects.path_exists(path)
    return os.path.lexists(path)


def _path_is_dir(effects: _Effects, path: Path) -> bool:
    if effects.is_dir is not None:
        return effects.is_dir(path)
    return path.is_dir()


def _path_is_symlink(effects: _Effects, path: Path) -> bool:
    if effects.is_symlink is not None:
        return effects.is_symlink(path)
    return path.is_symlink()


def _resolve_path(effects: _Effects, path: Path) -> Path:
    if effects.resolve_path is not None:
        return effects.resolve_path(path)
    return path.resolve(strict=False)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _external_new_file_preflight(
    effects: _Effects,
    repo: Path,
    path: Path,
    stage: str,
    *,
    reserved_prefix: str | None = None,
) -> Path:
    try:
        resolved_repo = _resolve_path(effects, repo)
        resolved_path = _resolve_path(effects, path)
        if (
            _is_within(resolved_path, resolved_repo)
            or (
                reserved_prefix is not None
                and path.name.startswith(reserved_prefix)
            )
            or not _path_is_dir(effects, path.parent)
            or _path_is_symlink(effects, path)
            or _path_exists(effects, path)
        ):
            raise _StageFailure(stage, RC_USAGE)
        return resolved_path
    except _StageFailure:
        raise
    except (OSError, RuntimeError, UnicodeError, ValueError):
        raise _StageFailure(stage, RC_USAGE) from None


def _external_probe_root_preflight(
    effects: _Effects,
    repo: Path,
    path: Path,
) -> Path:
    stage = "acceptance-red-check-preflight"
    try:
        resolved_repo = _resolve_path(effects, repo)
        resolved_path = _resolve_path(effects, path)
        if (
            _is_within(resolved_path, resolved_repo)
            or not _path_is_dir(effects, path)
            or _path_is_symlink(effects, path)
        ):
            raise _StageFailure(stage, RC_USAGE)
        return resolved_path
    except _StageFailure:
        raise
    except (OSError, RuntimeError, UnicodeError, ValueError):
        raise _StageFailure(stage, RC_USAGE) from None


def _acceptance_receipt_preflight(
    effects: _Effects,
    repo: Path,
    receipt_file: Path,
    command: Sequence[str],
) -> str:
    try:
        resolved_repo = _resolve_path(effects, repo)
        _external_new_file_preflight(
            effects,
            repo,
            receipt_file,
            "acceptance-receipt-preflight",
            reserved_prefix=_RECEIPT_TEMP_PREFIX,
        )
        if len(command) < 2:
            raise _StageFailure("acceptance-receipt-preflight", RC_USAGE)
        runner = Path(command[1])
        if not runner.is_absolute():
            runner = repo / runner
        resolved_runner = _resolve_path(effects, runner)
        if not _is_within(resolved_runner, resolved_repo):
            raise _StageFailure("acceptance-receipt-preflight", RC_USAGE)
        return resolved_runner.relative_to(resolved_repo).as_posix()
    except _StageFailure:
        raise
    except (OSError, RuntimeError, UnicodeError, ValueError):
        raise _StageFailure("acceptance-receipt-preflight", RC_USAGE) from None


def _acceptance_log_preflight(
    effects: _Effects,
    repo: Path,
    log_file: Path,
    receipt_file: Path,
) -> tuple[Path, Path, Path]:
    resolved_log = _external_new_file_preflight(
        effects,
        repo,
        log_file,
        "acceptance-log-preflight",
    )
    if resolved_log == _resolve_path(effects, receipt_file):
        raise _StageFailure("acceptance-log-preflight", RC_USAGE)
    checker_receipt = receipt_file.with_name(
        receipt_file.name + _RED_CHECK_RECEIPT_SUFFIX
    )
    resolved_checker_receipt = _external_new_file_preflight(
        effects,
        repo,
        checker_receipt,
        "acceptance-red-check-preflight",
    )
    if resolved_checker_receipt == resolved_log:
        raise _StageFailure("acceptance-red-check-preflight", RC_USAGE)
    probe_root = _external_probe_root_preflight(effects, repo, log_file.parent)
    return resolved_log, resolved_checker_receipt, probe_root


def _acceptance_environment_preflight(
    effects: _Effects,
    repo: Path,
) -> _AcceptanceEnvironment:
    try:
        pytest_addopts = effects.getenv("PYTEST_ADDOPTS")
        pytest_plugins = effects.getenv("PYTEST_PLUGINS")
        task_run_id = effects.getenv(_TASK_RUN_ID_ENV)
        task_runs_root = effects.getenv(_TASK_RUNS_ROOT_ENV)
        if pytest_addopts or pytest_plugins:
            raise _StageFailure("acceptance-env-preflight", RC_USAGE)
        if task_run_id is not None:
            raw_root = (
                Path(task_runs_root)
                if task_runs_root is not None
                else repo / "output" / "task-runs"
            )
            if not raw_root.is_absolute():
                raw_root = repo / raw_root
            if _is_within(
                _resolve_path(effects, raw_root),
                _resolve_path(effects, repo),
            ):
                raise _StageFailure("acceptance-env-preflight", RC_USAGE)
    except _StageFailure:
        raise
    except (OSError, RuntimeError, UnicodeError, ValueError):
        raise _StageFailure("acceptance-env-preflight", RC_USAGE) from None
    return _AcceptanceEnvironment(
        pytest_addopts=pytest_addopts,
        pytest_plugins=pytest_plugins,
        task_run_id=task_run_id,
        task_runs_root=task_runs_root,
    )


def _submodule_readiness_preflight(effects: _Effects, repo: Path) -> None:
    try:
        result = _run_capture(
            effects,
            _SUBMODULE_READY_ARGV,
            repo,
            "preflight-submodule-ready",
        )
    except _StageFailure as exc:
        raise _StageFailure(
            "preflight-submodule-ready",
            RC_USAGE,
            exc.outcome.source_rc,
        ) from None
    if any(line.startswith(("-", "U")) for line in result.stdout.splitlines()):
        raise _StageFailure("preflight-submodule-ready", RC_USAGE)


def _blob_sha(
    effects: _Effects,
    repo: Path,
    revision: str,
    path: str,
    stage: str,
    *,
    diagnostic_reason: str | None = None,
) -> str:
    result = _run_capture(
        effects,
        ("git", "rev-parse", f"{revision}:{path}"),
        repo,
        stage,
        diagnostic_reason=diagnostic_reason,
        diagnostic_observed={
            "revision": revision,
            "path": path,
        },
    )
    value = result.stdout.strip()
    if _SHA_RE.fullmatch(value) is None:
        detail = None
        if diagnostic_reason is not None:
            detail = _attestation_detail(
                diagnostic_reason,
                {
                    "revision": revision,
                    "path": path,
                    **_malformed_sha_observed(value),
                },
            )
        raise _StageFailure(stage, detail=detail)
    return value


def _red_gate_git_argv(repo: Path, *args: str) -> tuple[str, ...]:
    return (
        _GIT_EXE,
        *_GIT_CONFIG,
        "-C",
        str(repo),
        *args,
    )


def _run_with_input(
    effects: _Effects,
    argv: Sequence[str],
    repo: Path,
    content: bytes,
    stage: str,
    *,
    capture: bool,
) -> _BinaryCommandResult:
    runner = effects.run_with_input
    if runner is None:
        raise _StageFailure(stage)
    try:
        result = runner(tuple(argv), repo, capture, content)
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
        raise _StageFailure(stage) from None
    if not isinstance(result, _BinaryCommandResult):
        raise _StageFailure(stage)
    return result


def _red_gate_git(
    effects: _Effects,
    repo: Path,
    content: bytes,
    stage: str,
    *args: str,
) -> bytes:
    result = _run_with_input(
        effects,
        _red_gate_git_argv(repo, *args),
        repo,
        content,
        stage,
        capture=True,
    )
    if result.returncode != 0:
        raise _StageFailure(stage, source_rc=result.returncode)
    if not isinstance(result.stdout, bytes):
        raise _StageFailure(stage)
    return result.stdout


def _red_gate_blob_sha(
    effects: _Effects,
    repo: Path,
    revision: str,
    stage: str,
) -> str:
    raw = _red_gate_git(
        effects,
        repo,
        b"",
        stage,
        "rev-parse",
        "--verify",
        f"{revision}:{_RED_CHECKER_PATH}",
    )
    try:
        value = raw.decode("ascii").strip()
    except UnicodeError:
        raise _StageFailure(stage) from None
    if _SHA_RE.fullmatch(value) is None:
        raise _StageFailure(stage)
    return value


def _verified_red_checker_source(
    effects: _Effects,
    repo: Path,
    tested_main: str,
    tested_tip: str,
    stage: str,
) -> _RedCheckerBinding:
    main_blob_sha = _red_gate_blob_sha(effects, repo, tested_main, stage)
    tip_blob_sha = _red_gate_blob_sha(effects, repo, tested_tip, stage)
    if main_blob_sha != tip_blob_sha:
        raise _StageFailure(stage)
    source = _red_gate_git(
        effects,
        repo,
        b"",
        stage,
        "cat-file",
        "blob",
        f"{tested_main}:{_RED_CHECKER_PATH}",
    )
    actual_raw = _red_gate_git(
        effects,
        repo,
        source,
        stage,
        "hash-object",
        "--stdin",
        "--no-filters",
    )
    try:
        actual_blob_sha = actual_raw.decode("ascii").strip()
    except UnicodeError:
        raise _StageFailure(stage) from None
    if (
        _SHA_RE.fullmatch(actual_blob_sha) is None
        or actual_blob_sha != main_blob_sha
    ):
        raise _StageFailure(stage)
    return _RedCheckerBinding(source=source, blob_sha=main_blob_sha)


def _red_checker_argv(
    *,
    repo: Path,
    log_file: Path,
    checker_receipt: Path,
    probe_root: Path,
    tested_main: str,
    tested_tip: str,
) -> tuple[str, ...]:
    return (
        sys.executable,
        "-I",
        "-c",
        _RED_CHECKER_BOOTSTRAP,
        str(repo),
        "--log",
        str(log_file),
        "--tested-main",
        tested_main,
        "--wave-tip",
        tested_tip,
        "--receipt",
        str(checker_receipt),
        "--probe-root",
        str(probe_root),
    )


def _behind_count(effects: _Effects, repo: Path, stage: str) -> int:
    result = _run_capture(
        effects,
        ("git", "rev-list", "--count", "HEAD..main"),
        repo,
        stage,
    )
    value = result.stdout.strip()
    if not value.isascii() or not value.isdecimal():
        raise _StageFailure(stage)
    return int(value, 10)


def _normalized_repo_path_parts(value: str | Path, repo: Path) -> tuple[str, ...]:
    path = Path(os.path.normpath(os.fspath(value)))
    if path.is_absolute():
        normalized_repo = Path(os.path.normpath(os.fspath(repo)))
        try:
            path = path.relative_to(normalized_repo)
        except ValueError:
            pass
    return path.parts


def _owned_path_overlap(
    effects: _Effects,
    repo: Path,
    owned_paths: Sequence[Path],
) -> bool:
    result = _run_capture(
        effects,
        ("git", "diff", "--name-only", "HEAD...main"),
        repo,
        "owned-path-diff",
    )
    owned_parts = [
        _normalized_repo_path_parts(path, repo) for path in owned_paths
    ]
    for changed_path in result.stdout.splitlines():
        if not changed_path:
            continue
        changed_parts = _normalized_repo_path_parts(changed_path, repo)
        if any(
            changed_parts == owned
            or changed_parts[: len(owned)] == owned
            for owned in owned_parts
        ):
            return True
    return False


def _identity_preflight(effects: _Effects, repo: Path, wave: str) -> None:
    def preflight_run(argv: Sequence[str], stage: str) -> _CommandResult:
        try:
            return _run_capture(effects, argv, repo, stage)
        except _StageFailure as exc:
            raise _StageFailure(stage, RC_USAGE, exc.outcome.source_rc) from None

    inside = preflight_run(
        ("git", "rev-parse", "--is-inside-work-tree"), "preflight-worktree"
    )
    if inside.stdout.strip() != "true":
        raise _StageFailure("preflight-worktree", RC_USAGE)
    top_level = preflight_run(
        ("git", "rev-parse", "--show-toplevel"), "preflight-toplevel"
    ).stdout.strip()
    try:
        if not top_level or Path(top_level).resolve() != repo.resolve():
            raise _StageFailure("preflight-toplevel", RC_USAGE)
    except OSError:
        raise _StageFailure("preflight-toplevel", RC_USAGE) from None
    branch = preflight_run(
        ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
        "preflight-branch",
    ).stdout.strip()
    if not wave or not branch or not branch.endswith(wave):
        raise _StageFailure("preflight-branch", RC_USAGE)
    status = preflight_run(
        _CLEAN_STATUS_ARGV,
        "preflight-clean",
    )
    if status.stdout:
        raise _StageFailure("preflight-clean", RC_USAGE)


def _lease_command(
    repo: Path,
    action: str,
    lease_dir: Path,
    wave: str,
    main_sha: str | None = None,
) -> tuple[str, ...]:
    argv = [
        sys.executable,
        str(repo / "tools" / "wave_land_window.py"),
        action,
        "--lease-dir",
        str(lease_dir),
        "--wave",
        wave,
    ]
    if main_sha is not None:
        argv.extend(("--main-sha", main_sha))
    return tuple(argv)


def _claim_once(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
    main_sha: str,
    lifecycle: _AcceptanceLifecycle | None = None,
    *,
    diagnostic_reason: str | None = None,
) -> _ClaimContext:
    if lifecycle is not None:
        lifecycle.ownership = _LeaseOwnership.UNKNOWN
    result = _run_capture(
        effects,
        _lease_command(repo, "claim", lease_dir, wave, main_sha),
        repo,
        "claim",
        diagnostic_reason=diagnostic_reason,
    )
    try:
        parsed = _parse_json_object(result.stdout, stage="claim-json")
    except _StageFailure as exc:
        if diagnostic_reason is None:
            raise
        raise _StageFailure(
            exc.outcome.stage or "claim-json",
            source_rc=exc.outcome.source_rc,
            detail=_attestation_detail(
                diagnostic_reason,
                {"failure_kind": "claim-json"},
            ),
        ) from None
    state = parsed.get("state")
    if not isinstance(state, str) or state not in _CLAIM_STATES:
        raise _StageFailure(
            "claim-state",
            detail=(
                None
                if diagnostic_reason is None
                else _attestation_detail(
                    diagnostic_reason,
                    {"failure_kind": "claim-state"},
                )
            ),
        )
    holder_self = parsed.get("holder_self") is True
    holder = parsed.get("holder")
    claimed_main_sha = parsed.get("main_sha")
    age_seconds = parsed.get("age_seconds")
    source = parsed.get("source")
    self_renew_failed = (
        state == "unavailable"
        and holder_self
        and isinstance(source, dict)
        and source.get("reason") == "self-renew-failed"
    )
    if lifecycle is not None:
        if state == "acquired":
            lifecycle.ownership = _LeaseOwnership.ACQUIRED
        elif state == "held-self" or self_renew_failed or holder_self:
            lifecycle.ownership = _LeaseOwnership.HELD_SELF
        else:
            lifecycle.ownership = _LeaseOwnership.NONE
            # held/queued の待ち札は 300 秒で失効するため、他 holder を release しない。
    if self_renew_failed:
        raise _StageFailure(
            "claim-self-renew-failed",
            detail=(
                None
                if diagnostic_reason is None
                else _attestation_detail(
                    diagnostic_reason,
                    {"failure_kind": "self-renew-failed"},
                )
            ),
        )
    if state in _ACCEPTED_CLAIM_STATES:
        try:
            expected_holder = hashlib.sha256(wave.encode("utf-8")).hexdigest()[:12]
        except UnicodeError:
            raise _StageFailure(
                "claim-self-unverified",
                detail=(
                    None
                    if diagnostic_reason is None
                    else _attestation_detail(
                        diagnostic_reason,
                        {"failure_kind": "holder-hash"},
                    )
                ),
            ) from None
        if not (
            holder_self
            and isinstance(holder, str)
            and _HOLDER_RE.fullmatch(holder) is not None
            and holder == expected_holder
            and claimed_main_sha == main_sha
            and type(age_seconds) is int
            and 0 <= age_seconds < _LEASE_TTL_SECONDS
            and source == {"status": "ok", "reason": None}
        ):
            failure_kind = "source"
            if not holder_self:
                failure_kind = "holder-self"
            elif not isinstance(holder, str):
                failure_kind = "holder-type"
            elif _HOLDER_RE.fullmatch(holder) is None:
                failure_kind = "holder-format"
            elif holder != expected_holder:
                failure_kind = "holder-mismatch"
            elif claimed_main_sha != main_sha:
                failure_kind = "main-sha-mismatch"
            elif type(age_seconds) is not int:
                failure_kind = "age-type"
            elif not 0 <= age_seconds < _LEASE_TTL_SECONDS:
                failure_kind = "age-range"
            raise _StageFailure(
                "claim-self-unverified",
                detail=(
                    None
                    if diagnostic_reason is None
                    else _attestation_detail(
                        diagnostic_reason,
                        {"failure_kind": failure_kind},
                    )
                ),
            )
    elif state != "acquired" and holder_self:
        raise _StageFailure(
            "claim-self-unverified",
            detail=(
                None
                if diagnostic_reason is None
                else _attestation_detail(
                    diagnostic_reason,
                    {"failure_kind": "unexpected-holder-self"},
                )
            ),
        )
    return _ClaimContext(
        state=state,
        holder=holder if isinstance(holder, str) else None,
        main_sha=claimed_main_sha if isinstance(claimed_main_sha, str) else None,
        age_seconds=age_seconds if type(age_seconds) is int else None,
    )


def _wait_until_acquired(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
    poll_seconds: int,
    max_wait_seconds: int,
    lifecycle: _AcceptanceLifecycle,
) -> tuple[float, _ClaimContext]:
    started = effects.monotonic()
    while True:
        sha = _main_sha(effects, repo, "preclaim-rev-parse")
        claim_started_at = effects.monotonic()
        claim = _claim_once(effects, repo, lease_dir, wave, sha, lifecycle)
        if claim.state in _ACCEPTED_CLAIM_STATES:
            lifecycle.acquired_at = claim_started_at
            return claim_started_at, claim
        if claim.state not in _POLLING_CLAIM_STATES:
            raise _StageFailure("claim-state")
        if effects.monotonic() - started + poll_seconds > max_wait_seconds:
            raise _StageFailure("claim-timeout")
        effects.sleep(poll_seconds)


def _message_has_ai_agent(content: str) -> bool:
    return bool(content.strip()) and any(
        line.startswith("AI-Agent:") for line in content.splitlines()
    )


def _validated_message_copy(path: Path, effects: _Effects) -> Path | None:
    if not effects.is_file(path):
        return None
    try:
        content = effects.read_text(path)
    except (OSError, UnicodeError):
        return None
    if not _message_has_ai_agent(content):
        return None
    try:
        return effects.write_temp(content.encode("utf-8"))
    except (OSError, UnicodeError):
        return None


def _release_once(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
) -> _Outcome:
    try:
        result = effects.run(
            _lease_command(repo, "release", lease_dir, wave), repo, True
        )
    except BaseException:
        return _Outcome(RC_CLEANUP_FAILED, "release")
    if result.returncode != 0:
        return _Outcome(RC_CLEANUP_FAILED, "release", result.returncode)
    try:
        parsed = _parse_json_object(result.stdout, stage="release-json")
    except _StageFailure:
        return _Outcome(RC_CLEANUP_FAILED, "release-json", result.returncode)
    state = parsed.get("state")
    if not isinstance(state, str) or state not in _RELEASED_STATES:
        return _Outcome(RC_CLEANUP_FAILED, "release-state", result.returncode)
    return _Outcome(RC_OK)


def _abort_pending_merge(effects: _Effects, repo: Path) -> _Outcome:
    failure: _Outcome | None = None
    try:
        result = effects.run(("git", "merge", "--abort"), repo, True)
    except BaseException:
        failure = _Outcome(RC_CLEANUP_FAILED, "merge-abort")
    else:
        if result.returncode != 0:
            failure = _Outcome(
                RC_CLEANUP_FAILED, "merge-abort", result.returncode
            )

    try:
        merge_head = effects.run(
            ("git", "rev-parse", "-q", "--verify", "MERGE_HEAD"),
            repo,
            True,
        )
    except BaseException:
        merge_head = None
    if (merge_head is None or merge_head.returncode != 1) and failure is None:
        failure = _Outcome(RC_CLEANUP_FAILED, "merge-abort-state")

    try:
        status = effects.run(
            ("git", "status", "--porcelain", "--untracked-files=no"),
            repo,
            True,
        )
    except BaseException:
        status = None
    if (
        (status is None or status.returncode != 0 or status.stdout)
        and failure is None
    ):
        failure = _Outcome(RC_CLEANUP_FAILED, "merge-abort-clean")
    return _Outcome(RC_OK) if failure is None else failure


def _normalize_child_rc(returncode: int) -> int:
    if returncode >= 0:
        return returncode
    return 128 + (-returncode)


def _cleanup_after_claim(
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
    *,
    merge_pending: bool,
    release_lease: bool,
) -> _Outcome | None:
    cleanup_failure: _Outcome | None = None
    previous_mask: set[signal.Signals] | None = None
    pthread_sigmask = getattr(signal, "pthread_sigmask", None)
    if pthread_sigmask is not None:
        try:
            previous_mask = pthread_sigmask(signal.SIG_BLOCK, _HANDLED_SIGNALS)
        except (OSError, ValueError):
            previous_mask = None
    try:
        if merge_pending:
            abort_outcome = _abort_pending_merge(effects, repo)
            if abort_outcome.rc != RC_OK:
                cleanup_failure = abort_outcome
        if release_lease:
            release_outcome = _release_once(effects, repo, lease_dir, wave)
            if release_outcome.rc != RC_OK:
                if cleanup_failure is not None:
                    _print_outcome(release_outcome)
                else:
                    cleanup_failure = release_outcome
    finally:
        if previous_mask is not None:
            try:
                pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            except _SignalReceived:
                # cleanup 中に届いた再 signal は cleanup 完了後まで遅延できた。
                pass
    return cleanup_failure


def _cleanup_lifecycle(
    lifecycle: _AcceptanceLifecycle,
    effects: _Effects,
    repo: Path,
    lease_dir: Path,
    wave: str,
) -> _Outcome | None:
    if lifecycle.ownership not in {
        _LeaseOwnership.UNKNOWN,
        _LeaseOwnership.ACQUIRED,
        _LeaseOwnership.HELD_SELF,
    }:
        return lifecycle.cleanup_failure
    ownership = lifecycle.ownership
    merge_pending = lifecycle.merge_pending
    # cleanup 権限を実処理より先に消費し、signal/finally の再入を no-op にする。
    lifecycle.ownership = _LeaseOwnership.NONE
    lifecycle.merge_pending = False
    lifecycle.cleanup_failure = _cleanup_after_claim(
        effects,
        repo,
        lease_dir,
        wave,
        merge_pending=merge_pending,
        release_lease=ownership in {
            _LeaseOwnership.UNKNOWN,
            _LeaseOwnership.ACQUIRED,
        },
    )
    if ownership is _LeaseOwnership.HELD_SELF:
        print(
            "acceptance: held-self lease retained; "
            "this invocation has no release authority",
            file=sys.stderr,
        )
    return lifecycle.cleanup_failure


def _acceptance_receipt_bytes(
    *,
    wave: str,
    holder: str,
    tested_main: str,
    tested_tip: str,
    command: Sequence[str],
    resolved_runner_path: str,
    pre_fingerprint: _TreeFingerprint,
    post_fingerprint: _TreeFingerprint,
    waiter_blob_sha: str,
    environment: _AcceptanceEnvironment,
    child_rc: int,
    verdict: str,
    log_sha256: str,
    effective_scheduler: str,
    red_check: _RedCheckResult | None,
) -> bytes:
    if not (
        _SHA_RE.fullmatch(tested_main) is not None
        and _SHA_RE.fullmatch(tested_tip) is not None
        and re.fullmatch(r"[0-9a-f]{64}", log_sha256) is not None
        and isinstance(effective_scheduler, str)
        and effective_scheduler in _EFFECTIVE_SCHEDULERS
    ):
        tested_main_valid = _diagnostic_bool(
            lambda: _SHA_RE.fullmatch(tested_main) is not None
        )
        tested_tip_valid = (
            _diagnostic_bool(lambda: _SHA_RE.fullmatch(tested_tip) is not None)
            if tested_main_valid
            else None
        )
        log_sha256_valid = (
            _diagnostic_bool(
                lambda: re.fullmatch(r"[0-9a-f]{64}", log_sha256) is not None
            )
            if tested_tip_valid is True
            else None
        )
        scheduler_is_str = (
            _diagnostic_bool(lambda: isinstance(effective_scheduler, str))
            if log_sha256_valid is True
            else None
        )
        scheduler_in_allowed = (
            _diagnostic_bool(
                lambda: effective_scheduler in _EFFECTIVE_SCHEDULERS
            )
            if scheduler_is_str is True
            else None
        )
        raise _StageFailure(
            "acceptance-receipt",
            detail=_attestation_detail(
                "receipt-fields",
                {
                    "tested_main": tested_main,
                    "tested_main_valid": tested_main_valid,
                    "tested_tip": (
                        tested_tip
                        if tested_tip_valid is not None
                        else None
                    ),
                    "tested_tip_valid": tested_tip_valid,
                    "log_sha256": (
                        log_sha256
                        if log_sha256_valid is not None
                        else None
                    ),
                    "log_sha256_valid": log_sha256_valid,
                    "effective_scheduler": (
                        effective_scheduler
                        if scheduler_is_str is True
                        else (
                            type(effective_scheduler).__name__
                            if scheduler_is_str is False
                            else None
                        )
                    ),
                    "scheduler_is_str": scheduler_is_str,
                    "scheduler_in_allowed": scheduler_in_allowed,
                },
            ),
        )
    if verdict == "child-green":
        if child_rc != 0 or red_check is not None:
            raise _StageFailure(
                "acceptance-receipt",
                detail=_attestation_detail(
                    "receipt-child-green",
                    {
                        "child_rc": child_rc,
                        "red_check_present": (
                            red_check is not None if child_rc == 0 else None
                        ),
                    },
                ),
            )
    elif verdict == "non-attributable-only":
        if child_rc != 1 or red_check is None or not red_check.red_nodeids:
            red_check_present = red_check is not None if child_rc == 1 else None
            red_nodeid_count = (
                len(red_check.red_nodeids)
                if red_check_present is True
                else None
            )
            raise _StageFailure(
                "acceptance-receipt",
                detail=_attestation_detail(
                    "receipt-non-attributable",
                    {
                        "child_rc": child_rc,
                        "red_check_present": red_check_present,
                        "red_nodeid_count": red_nodeid_count,
                    },
                ),
            )
    else:
        raise _StageFailure(
            "acceptance-receipt",
            detail=_attestation_detail(
                "receipt-verdict",
                {"verdict": verdict},
            ),
        )
    receipt = {
        "schema_version": _RECEIPT_SCHEMA_VERSION,
        "authority_kind": _RECEIPT_AUTHORITY_KIND,
        "acceptance_wave": wave,
        "lease_holder": holder,
        "tested_main": tested_main,
        "tested_tip": tested_tip,
        "argv": list(command),
        "resolved_runner_path": resolved_runner_path,
        "child_rc": child_rc,
        "pre_fingerprint": _fingerprint_json(pre_fingerprint),
        "post_fingerprint": _fingerprint_json(post_fingerprint),
        "waiter_blob_sha": waiter_blob_sha,
        "env_projection": environment.as_json(),
        "verdict": verdict,
        "log_sha256": log_sha256,
        "effective_scheduler": effective_scheduler,
        "checker_rc": None if red_check is None else red_check.checker_rc,
        "checker_status": None if red_check is None else red_check.checker_status,
        "checker_blob_sha": None if red_check is None else red_check.checker_blob_sha,
        "checker_receipt_sha256": (
            None if red_check is None else red_check.checker_receipt_sha256
        ),
        "red_nodeids": [] if red_check is None else list(red_check.red_nodeids),
    }
    try:
        return (
            json.dumps(
                receipt,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("ascii")
    except (TypeError, UnicodeError, ValueError, RecursionError) as exc:
        raise _StageFailure(
            "acceptance-receipt",
            detail=_attestation_detail(
                "receipt-encode",
                _exception_observed(exc),
            ),
        ) from None


def _read_bytes(effects: _Effects, path: Path, stage: str) -> bytes:
    reader = effects.read_bytes or Path.read_bytes
    try:
        value = reader(path)
    except (OSError, UnicodeError, ValueError):
        raise _StageFailure(stage) from None
    if not isinstance(value, bytes):
        raise _StageFailure(stage)
    return value


def _sha256_file(effects: _Effects, path: Path, stage: str) -> str:
    hasher = effects.sha256_file
    try:
        if hasher is not None:
            value = hasher(path)
        else:
            value = hashlib.sha256(_read_bytes(effects, path, stage)).hexdigest()
    except _StageFailure:
        raise
    except (OSError, UnicodeError, ValueError):
        raise _StageFailure(stage) from None
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise _StageFailure(stage)
    return value


def _inspect_acceptance_log(
    effects: _Effects,
    path: Path,
) -> tuple[str, str]:
    inspector = effects.inspect_acceptance_log or _default_inspect_acceptance_log
    try:
        value = inspector(path)
    except _StageFailure:
        raise
    except (OSError, UnicodeError, TypeError, ValueError):
        raise _StageFailure(
            "acceptance-scheduler-attestation",
            detail=_attestation_detail("log-inspection", os.fspath(path)),
        ) from None
    if not (
        isinstance(value, tuple)
        and len(value) == 2
        and isinstance(value[0], str)
        and re.fullmatch(r"[0-9a-f]{64}", value[0]) is not None
        and isinstance(value[1], str)
        and value[1] in _EFFECTIVE_SCHEDULERS
    ):
        raise _StageFailure(
            "acceptance-scheduler-attestation",
            detail=_attestation_detail("inspection-result", repr(value)),
        )
    return value


def _verify_red_check_receipt(
    *,
    effects: _Effects,
    repo: Path,
    log_file: Path,
    checker_receipt: Path,
    probe_root: Path,
    tested_main: str,
    tested_tip: str,
    log_sha256: str,
) -> _RedCheckResult:
    stage = "acceptance-red-check"
    binding = _verified_red_checker_source(
        effects,
        repo,
        tested_main,
        tested_tip,
        stage,
    )
    checker = _run_with_input(
        effects,
        _red_checker_argv(
            repo=repo,
            log_file=log_file,
            checker_receipt=checker_receipt,
            probe_root=probe_root,
            tested_main=tested_main,
            tested_tip=tested_tip,
        ),
        repo,
        binding.source,
        stage,
        capture=False,
    )
    checker_rc = _normalize_child_rc(checker.returncode)
    if checker_rc != 0:
        raise _StageFailure(stage, source_rc=checker.returncode)
    raw = _read_bytes(effects, checker_receipt, stage)
    try:
        receipt = _parse_json_object(raw.decode("utf-8"), stage=stage)
    except UnicodeError:
        raise _StageFailure(stage) from None
    expected_fields = {
        "collections", "log_path", "log_sha256", "nodes", "schema_version",
        "status", "submodules", "tested_main", "wave_tip",
    }
    expected_collection_fields = {
        "deleted_receipt_path", "path", "request_id", "source",
        "stdout_sha256", "submission_nonce",
    }
    collections = receipt.get("collections")
    nodes = receipt.get("nodes")
    if not (
        set(receipt) == expected_fields
        and receipt.get("schema_version") == _RED_CHECK_SCHEMA_VERSION
        and receipt.get("status") == "non-attributable-only"
        and receipt.get("log_sha256") == log_sha256
        and receipt.get("wave_tip") == tested_tip
        and receipt.get("tested_main") == tested_main
        and isinstance(collections, list)
        and isinstance(nodes, list)
        and nodes
    ):
        raise _StageFailure(stage)
    for collection in collections:
        if not (
            isinstance(collection, dict)
            and set(collection) == expected_collection_fields
            and isinstance(collection.get("path"), str)
            and isinstance(collection.get("source"), str)
            and all(
                collection.get(field) is None
                or isinstance(collection.get(field), str)
                for field in (
                    "deleted_receipt_path",
                    "request_id",
                    "stdout_sha256",
                    "submission_nonce",
                )
            )
        ):
            raise _StageFailure(stage)
    red_nodeids: list[str] = []
    for node in nodes:
        if not (
            isinstance(node, dict)
            and set(node) == {"classification", "nodeid", "rerun_rc"}
            and node.get("classification") == "non-attributable"
            and isinstance(node.get("nodeid"), str)
            and node["nodeid"]
            and type(node.get("rerun_rc")) is int
        ):
            raise _StageFailure(stage)
        red_nodeids.append(node["nodeid"])
    if red_nodeids != sorted(set(red_nodeids)):
        raise _StageFailure(stage)
    return _RedCheckResult(
        checker_rc=checker_rc,
        checker_status="non-attributable-only",
        checker_blob_sha=binding.blob_sha,
        checker_receipt_sha256=hashlib.sha256(raw).hexdigest(),
        red_nodeids=tuple(red_nodeids),
    )


def _prepare_acceptance_receipt(
    *,
    effects: _Effects,
    receipt_file: Path,
    content: bytes,
) -> Path:
    write_temp = effects.write_receipt_temp or _default_write_receipt_temp
    try:
        temp_path = write_temp(receipt_file, content)
    except (_SignalReceived, KeyboardInterrupt):
        raise
    except BaseException as exc:
        raise _StageFailure(
            "acceptance-receipt",
            detail=_attestation_detail(
                "receipt-temp-write",
                _exception_observed(exc),
            ),
        ) from None
    if temp_path.parent != receipt_file.parent or not temp_path.name.startswith(
        _RECEIPT_TEMP_PREFIX
    ):
        parent_matches = _diagnostic_bool(
            lambda: temp_path.parent == receipt_file.parent
        )
        prefix_matches = (
            _diagnostic_bool(
                lambda: temp_path.name.startswith(_RECEIPT_TEMP_PREFIX)
            )
            if parent_matches is True
            else None
        )
        try:
            effects.unlink(temp_path)
        except OSError:
            pass
        raise _StageFailure(
            "acceptance-receipt",
            detail=_attestation_detail(
                "receipt-temp-contract",
                {
                    "parent_matches": parent_matches,
                    "prefix_matches": prefix_matches,
                },
            ),
        )
    return temp_path


def _publish_acceptance_receipt(
    *,
    effects: _Effects,
    lifecycle: _AcceptanceLifecycle,
    receipt_file: Path,
    temp_path: Path,
) -> None:
    rename = effects.rename or os.rename
    prior_ownership = lifecycle.ownership
    previous_mask: set[signal.Signals] | None = None
    pthread_sigmask = getattr(signal, "pthread_sigmask", None)
    publish_failure: tuple[str, BaseException] | None = None
    mask_restore_failure: BaseException | None = None
    failure_reason = "receipt-publish-sigblock"
    try:
        if pthread_sigmask is None:
            raise _StageFailure(
                "acceptance-receipt",
                detail=_attestation_detail(
                    "receipt-sigmask",
                    {"pthread_sigmask_available": False},
                ),
            )
        lifecycle.ownership = _LeaseOwnership.RETAINED
        previous_mask = pthread_sigmask(signal.SIG_BLOCK, _HANDLED_SIGNALS)
        failure_reason = "receipt-publish-rename"
        try:
            rename(temp_path, receipt_file)
        except BaseException:
            lifecycle.ownership = prior_ownership
            raise
        lifecycle.receipt_published = True
    except (_SignalReceived, KeyboardInterrupt):
        if not lifecycle.receipt_published:
            lifecycle.ownership = prior_ownership
        raise
    except _StageFailure:
        if not lifecycle.receipt_published:
            lifecycle.ownership = prior_ownership
        raise
    except BaseException as exc:
        if not lifecycle.receipt_published:
            lifecycle.ownership = prior_ownership
        publish_failure = (failure_reason, exc)
    finally:
        if previous_mask is not None:
            try:
                pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            except BaseException as exc:
                if publish_failure is None and not lifecycle.receipt_published:
                    raise _StageFailure(
                        "acceptance-receipt",
                        detail=_attestation_detail(
                            "receipt-publish-mask-restore",
                            _exception_observed(exc),
                        ),
                    ) from None
                if publish_failure is not None:
                    mask_restore_failure = exc
    if publish_failure is not None:
        reason, exc = publish_failure
        observed = _exception_observed(exc)
        if mask_restore_failure is not None:
            restore_observed = _exception_observed(mask_restore_failure)
            observed.update(
                {
                    "mask_restore_failed": True,
                    "mask_restore_exception_type": restore_observed[
                        "exception_type"
                    ],
                    "mask_restore_errno": restore_observed["errno"],
                }
            )
        raise _StageFailure(
            "acceptance-receipt",
            detail=_attestation_detail(reason, observed),
        ) from None


def run_acceptance(
    *,
    wave: str,
    lease_dir: Path,
    merge_message_file: Path | None,
    poll_seconds: int,
    max_wait_seconds: int,
    command: Sequence[str],
    repo: Path,
    effects: _Effects,
    receipt_file: Path,
    log_file: Path,
    lifecycle: _AcceptanceLifecycle | None = None,
    owned_paths: Sequence[Path] = (),
) -> _Outcome:
    active_lifecycle = lifecycle or _AcceptanceLifecycle()
    primary = _Outcome(RC_FAIL_CLOSED, "internal")
    cleanup_failure: _Outcome | None = None
    validated_message: Path | None = None
    committed_sha: str | None = None
    claim_context: _ClaimContext | None = None
    receipt_temp: Path | None = None
    resolved_log_file: Path | None = None
    checker_receipt: Path | None = None
    probe_root: Path | None = None
    try:
        _identity_preflight(effects, repo, wave)
        _check_index_flags(effects, repo, "preflight-index-flags")
        _submodule_readiness_preflight(effects, repo)
        resolved_runner_path = _acceptance_receipt_preflight(
            effects,
            repo,
            receipt_file,
            command,
        )
        resolved_log_file, checker_receipt, probe_root = _acceptance_log_preflight(
            effects,
            repo,
            log_file,
            receipt_file,
        )
        acceptance_environment = _acceptance_environment_preflight(effects, repo)
        if merge_message_file is not None and not effects.is_file(merge_message_file):
            raise _StageFailure("merge-message-preflight", RC_USAGE)
        if not owned_paths:
            print(
                "acceptance: --owned-path 未指定のため所有実装面 overlap 判定を省略します",
                file=sys.stderr,
            )
        _, claim_context = _wait_until_acquired(
            effects,
            repo,
            lease_dir,
            wave,
            poll_seconds,
            max_wait_seconds,
            active_lifecycle,
        )
        _main_sha(effects, repo, "postclaim-rev-parse")
        behind = _behind_count(effects, repo, "behind-count")
        if behind > 0:
            if owned_paths and _owned_path_overlap(effects, repo, owned_paths):
                raise _StageFailure("owned-path-overlap")
            if merge_message_file is None:
                raise _StageFailure("merge-message")
            validated_message = _validated_message_copy(merge_message_file, effects)
            if validated_message is None:
                raise _StageFailure("merge-message")
            active_lifecycle.merge_pending = True
            _run_capture(
                effects,
                ("git", "merge", "--no-ff", "--no-commit", "main"),
                repo,
                "merge",
            )
            _run_capture(
                effects,
                (
                    sys.executable,
                    str(repo / "tools" / "check_ai_provenance.py"),
                    "--message-file",
                    str(validated_message),
                ),
                repo,
                "merge-message-provenance",
            )
            _run_capture(
                effects,
                ("git", "commit", "--dry-run", "-F", str(validated_message)),
                repo,
                "commit-dry-run",
            )
            _run_capture(
                effects,
                ("git", "commit", "-F", str(validated_message)),
                repo,
                "commit",
            )
            active_lifecycle.merge_pending = False
            committed_sha = _head_sha(effects, repo, "commit-rev-parse")
            committed_message = _run_capture(
                effects,
                ("git", "log", "-1", "--format=%B", committed_sha),
                repo,
                "commit-message-postcheck",
            ).stdout
            if not _message_has_ai_agent(committed_message):
                raise _StageFailure("commit-message-postcheck")
        if _behind_count(effects, repo, "postcheck") != 0:
            raise _StageFailure("postcheck")
        if (
            committed_sha is not None
            and _head_sha(effects, repo, "commit-head-postcheck") != committed_sha
        ):
            raise _StageFailure("commit-head-postcheck")
        prerun_status = _run_capture(
            effects,
            _CLEAN_STATUS_ARGV,
            repo,
            "prerun-clean",
        )
        if prerun_status.stdout:
            print(
                prerun_status.stdout,
                end="" if prerun_status.stdout.endswith("\n") else "\n",
                file=sys.stderr,
            )
            raise _StageFailure("prerun-clean")
        prerun_fingerprint = _tree_fingerprint(
            effects,
            repo,
            "prerun-fingerprint",
            prerun_status.stdout,
        )
        _verify_waiter_source_bytes(
            effects,
            repo,
            prerun_fingerprint.head_sha,
        )
        print(
            "acceptance-command argv=" + json.dumps(list(command), ensure_ascii=True),
            file=sys.stderr,
        )
        print(
            "acceptance-command timeout=none (long-running acceptance is intentional)",
            file=sys.stderr,
        )
        assert resolved_log_file is not None
        try:
            # 受入 command 自身は正当に長時間走るため、stage timeout を適用しない。
            run_logged = effects.run_logged or _default_run_logged
            child = run_logged(tuple(command), repo, resolved_log_file)
        except (OSError, UnicodeError, subprocess.SubprocessError):
            raise _StageFailure("acceptance-command") from None
        child_rc = _normalize_child_rc(child.returncode)
        postrun_status = _run_capture(
            effects,
            _CLEAN_STATUS_ARGV,
            repo,
            "postrun-clean",
        )
        if postrun_status.stdout:
            print(
                postrun_status.stdout,
                end="" if postrun_status.stdout.endswith("\n") else "\n",
                file=sys.stderr,
            )
            raise _StageFailure("postrun-clean")
        _check_index_flags(effects, repo, "postrun-index-flags")
        postrun_fingerprint = _tree_fingerprint(
            effects,
            repo,
            "postrun-fingerprint",
            postrun_status.stdout,
        )
        if postrun_fingerprint != prerun_fingerprint:
            raise _StageFailure("postrun-fingerprint")
        if child_rc not in (0, 1):
            raise _StageFailure(
                "acceptance-command",
                source_rc=child.returncode,
            )
        log_sha256, effective_scheduler = _inspect_acceptance_log(
            effects,
            resolved_log_file,
        )
        assert claim_context is not None and claim_context.holder is not None
        red_check: _RedCheckResult | None = None
        verdict = "child-green"
        if child_rc == 1:
            assert checker_receipt is not None and probe_root is not None
            red_check = _verify_red_check_receipt(
                effects=effects,
                repo=repo,
                log_file=resolved_log_file,
                checker_receipt=checker_receipt,
                probe_root=probe_root,
                tested_main=claim_context.main_sha,
                tested_tip=postrun_fingerprint.head_sha,
                log_sha256=log_sha256,
            )
            verdict = "non-attributable-only"
        waiter_blob_sha = _blob_sha(
            effects,
            repo,
            postrun_fingerprint.head_sha,
            "tools/dev_wave_wait.py",
            "acceptance-receipt",
            diagnostic_reason="receipt-waiter-blob",
        )
        receipt_content = _acceptance_receipt_bytes(
            wave=wave,
            holder=claim_context.holder,
            tested_main=claim_context.main_sha,
            tested_tip=postrun_fingerprint.head_sha,
            command=command,
            resolved_runner_path=resolved_runner_path,
            pre_fingerprint=prerun_fingerprint,
            post_fingerprint=postrun_fingerprint,
            waiter_blob_sha=waiter_blob_sha,
            environment=acceptance_environment,
            child_rc=child_rc,
            verdict=verdict,
            log_sha256=log_sha256,
            effective_scheduler=effective_scheduler,
            red_check=red_check,
        )
        receipt_temp = _prepare_acceptance_receipt(
            effects=effects,
            receipt_file=receipt_file,
            content=receipt_content,
        )
        final_main_sha = _main_sha(
            effects,
            repo,
            "acceptance-receipt",
            diagnostic_reason="receipt-main-resolve",
        )
        if final_main_sha != claim_context.main_sha:
            raise _StageFailure(
                "acceptance-receipt",
                detail=_attestation_detail(
                    "receipt-main-moved",
                    {
                        "claimed_main_sha": claim_context.main_sha,
                        "final_main_sha": final_main_sha,
                    },
                ),
            )
        confirmation_lifecycle = _AcceptanceLifecycle()
        try:
            confirmed = _claim_once(
                effects,
                repo,
                lease_dir,
                wave,
                final_main_sha,
                confirmation_lifecycle,
                diagnostic_reason="receipt-reclaim",
            )
        except _StageFailure as exc:
            if confirmation_lifecycle.ownership is _LeaseOwnership.ACQUIRED:
                active_lifecycle.ownership = _LeaseOwnership.ACQUIRED
            raise _StageFailure(
                "acceptance-receipt",
                source_rc=exc.outcome.source_rc,
                detail=_attestation_detail(
                    "receipt-reclaim",
                    {
                        "failure_kind": _detail_failure_kind(
                            exc.outcome.detail
                        ),
                        "exception_type": _detail_observed(
                            exc.outcome.detail
                        ).get("exception_type"),
                        "source_stage": exc.outcome.stage,
                        "source_rc": exc.outcome.source_rc,
                        "confirmation_ownership": (
                            confirmation_lifecycle.ownership.value
                        ),
                    },
                ),
            ) from None
        if confirmed.state == "acquired":
            active_lifecycle.ownership = _LeaseOwnership.ACQUIRED
        confirmed_remaining = (
            _LEASE_TTL_SECONDS - confirmed.age_seconds
            if confirmed.age_seconds is not None
            else -1
        )
        if not (
            confirmed.state == "held-self"
            and confirmed.holder == claim_context.holder
            and confirmed.main_sha == claim_context.main_sha
            and confirmed_remaining >= _RECEIPT_PUBLISH_MIN_TTL_SECONDS
        ):
            state_is_held_self = confirmed.state == "held-self"
            holder_matches = (
                confirmed.holder == claim_context.holder
                if state_is_held_self
                else None
            )
            main_sha_matches = (
                confirmed.main_sha == claim_context.main_sha
                if holder_matches is True
                else None
            )
            ttl_sufficient = (
                confirmed_remaining >= _RECEIPT_PUBLISH_MIN_TTL_SECONDS
                if main_sha_matches is True
                else None
            )
            raise _StageFailure(
                "acceptance-receipt",
                detail=_attestation_detail(
                    "receipt-lease-check",
                    {
                        "state": confirmed.state,
                        "holder_matches": holder_matches,
                        "main_sha_matches": main_sha_matches,
                        "claimed_main_sha": confirmed.main_sha,
                        "final_main_sha": final_main_sha,
                        "remaining_seconds": (
                            confirmed_remaining
                            if ttl_sufficient is not None
                            else None
                        ),
                        "required_seconds": (
                            _RECEIPT_PUBLISH_MIN_TTL_SECONDS
                            if ttl_sufficient is not None
                            else None
                        ),
                        "ttl_sufficient": ttl_sufficient,
                    },
                ),
            )
        _publish_acceptance_receipt(
            effects=effects,
            lifecycle=active_lifecycle,
            receipt_file=receipt_file,
            temp_path=receipt_temp,
        )
        receipt_temp = None
        print(
            "acceptance succeeded; lease is held; "
            f"TTL remaining at most {confirmed_remaining} seconds; "
            "exclusivity is lost after expiry"
        )
        print("known limitation: no fencing token is provided")
        primary = _Outcome(RC_OK)
    except _StageFailure as exc:
        primary = exc.outcome
    except KeyboardInterrupt:
        if active_lifecycle.receipt_published:
            primary = _Outcome(RC_OK)
        else:
            primary = _Outcome(RC_INTERRUPTED, "keyboard-interrupt")
    except _SignalReceived as exc:
        if active_lifecycle.receipt_published:
            primary = _Outcome(RC_OK)
        else:
            primary = _Outcome(128 + exc.signum, f"signal-{exc.signum}")
    except BaseException:
        if active_lifecycle.receipt_published:
            primary = _Outcome(RC_OK)
        else:
            primary = _Outcome(RC_FAIL_CLOSED, "unexpected-error")
    finally:
        if receipt_temp is not None:
            try:
                effects.unlink(receipt_temp)
            except OSError:
                pass
        if validated_message is not None:
            try:
                effects.unlink(validated_message)
            except OSError:
                pass
        cleanup_failure = _cleanup_lifecycle(
            active_lifecycle,
            effects,
            repo,
            lease_dir,
            wave,
        )
    if cleanup_failure is not None:
        cleanup_failure = _Outcome(
            cleanup_failure.rc,
            cleanup_failure.stage,
            cleanup_failure.source_rc,
            _attestation_detail(
                "cleanup-overrode-primary",
                {
                    "cleanup_detail": _nested_detail(cleanup_failure.detail),
                    "primary": {
                        "stage": primary.stage,
                        "detail": _nested_detail(primary.detail),
                    },
                },
            ),
        )
    return cleanup_failure if cleanup_failure is not None else primary


def _lease_dir(argument: Path | None, effects: _Effects) -> Path:
    if argument is not None:
        return argument
    value = effects.getenv(_LEASE_ENV)
    if not value:
        raise _StageFailure("lease-dir", RC_USAGE)
    return Path(value)


def _install_signal_handlers() -> dict[int, object]:
    # SIGKILL と host 停止は unwind 不能なので既存 lease TTL に委ねる。
    previous: dict[int, object] = {}

    def handler(signum: int, frame: object) -> None:
        del frame
        raise _SignalReceived(signum)

    try:
        for signum in _HANDLED_SIGNALS:
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handler)
    except BaseException:
        _restore_signal_handlers(previous)
        raise
    return previous


def _restore_signal_handlers(previous: dict[int, object]) -> None:
    previous_mask: set[signal.Signals] | None = None
    pthread_sigmask = getattr(signal, "pthread_sigmask", None)
    if pthread_sigmask is not None:
        previous_mask = pthread_sigmask(signal.SIG_BLOCK, _HANDLED_SIGNALS)
    failure: BaseException | None = None
    try:
        for signum, handler in previous.items():
            try:
                signal.signal(signum, handler)
            except BaseException as exc:
                if failure is None:
                    failure = exc
    finally:
        if previous_mask is not None:
            pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    if failure is not None:
        raise failure


def _print_outcome(outcome: _Outcome) -> None:
    if outcome.rc == 0:
        return
    suffix = f" source_rc={outcome.source_rc}" if outcome.source_rc is not None else ""
    if outcome.detail is not None:
        suffix += " detail=" + outcome.detail
    print(f"error: stage={outcome.stage or 'unknown'} rc={outcome.rc}{suffix}", file=sys.stderr)
    if outcome.detail is not None:
        print(
            f"diagnostic: stage={outcome.stage or 'unknown'} "
            f"rc={outcome.rc} detail={outcome.detail}"
        )


def main(
    argv: Sequence[str] | None = None,
    *,
    effects: _Effects | None = None,
    repo: Path | None = None,
) -> int:
    active_effects = _default_effects() if effects is None else effects
    try:
        command, args, child_argv = _parse_cli(
            list(sys.argv[1:] if argv is None else argv)
        )
        if command == "producer":
            pid = _resolve_pid(args.pid, args.pid_file, active_effects)
            outcome = wait_for_producer(
                done_file=args.done_file,
                artifact_file=args.artifact_file,
                pid=pid,
                max_wait_seconds=args.max_wait_seconds,
                effects=active_effects,
            )
        else:
            active_repo = Path.cwd() if repo is None else repo
            lease_dir = _lease_dir(args.lease_dir, active_effects)
            lifecycle = _AcceptanceLifecycle()
            previous = _install_signal_handlers()
            try:
                outcome = run_acceptance(
                    wave=args.wave,
                    lease_dir=lease_dir,
                    merge_message_file=args.merge_message_file,
                    poll_seconds=args.poll_seconds,
                    max_wait_seconds=args.max_wait_seconds,
                    command=child_argv,
                    repo=active_repo,
                    effects=active_effects,
                    receipt_file=args.receipt_file,
                    log_file=args.log_file,
                    lifecycle=lifecycle,
                    owned_paths=args.owned_path,
                )
            except BaseException as exc:
                if lifecycle.receipt_published:
                    outcome = _Outcome(RC_OK)
                elif isinstance(exc, _SignalReceived):
                    outcome = _Outcome(128 + exc.signum, f"signal-{exc.signum}")
                elif isinstance(exc, KeyboardInterrupt):
                    outcome = _Outcome(RC_INTERRUPTED, "keyboard-interrupt")
                else:
                    outcome = _Outcome(RC_FAIL_CLOSED, "internal")
                cleanup = _cleanup_lifecycle(
                    lifecycle,
                    active_effects,
                    active_repo,
                    lease_dir,
                    args.wave,
                )
                if cleanup is not None:
                    outcome = cleanup
            finally:
                restored = False
                while not restored:
                    try:
                        _restore_signal_handlers(previous)
                        restored = True
                    except BaseException as exc:
                        if lifecycle.receipt_published and isinstance(
                            exc, (_SignalReceived, KeyboardInterrupt)
                        ):
                            outcome = _Outcome(RC_OK)
                        elif lifecycle.receipt_published:
                            outcome = _Outcome(RC_OK)
                            restored = True
                        elif isinstance(exc, _SignalReceived):
                            outcome = _Outcome(
                                128 + exc.signum, f"signal-{exc.signum}"
                            )
                        elif isinstance(exc, KeyboardInterrupt):
                            outcome = _Outcome(
                                RC_INTERRUPTED, "keyboard-interrupt"
                            )
                        else:
                            outcome = _Outcome(
                                RC_FAIL_CLOSED, "signal-restore"
                            )
                            restored = True
                        cleanup = _cleanup_lifecycle(
                            lifecycle,
                            active_effects,
                            active_repo,
                            lease_dir,
                            args.wave,
                        )
                        if cleanup is not None:
                            outcome = cleanup
    except _StageFailure as exc:
        outcome = exc.outcome
    except (Exception, KeyboardInterrupt):
        outcome = _Outcome(RC_FAIL_CLOSED, "internal")
    _print_outcome(outcome)
    return outcome.rc


if __name__ == "__main__":
    sys.exit(main())
