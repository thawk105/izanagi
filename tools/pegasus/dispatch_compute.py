#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pytest runner を Pegasus gen_S 計算ノードへ同期 dispatch する。

dev harness 専用の薄い submitter であり、certification submitter は置き換えない。
親は scheduler 状態と永続 receipt を確定してから、会計照合済みの子 rc だけを返す。
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
import re
import secrets
import select
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.scheduler_nqsv import (  # noqa: E402
    GATE_STATE_FIELD_RE as _GATE_STATE_FIELD_RE,
    gate_state_value as _gate_state_value,
    target_bound_qstat_state as _target_bound_qstat_state,
)
from orchestrator.campaign import mutation_attempt_marker  # noqa: E402


INFRA_RC = 16
_DISPATCH_OUTCOME_PREFIX = "IZANAGI_DISPATCH_OUTCOME_V1 "
_DISPATCH_INFRA_REASONS = frozenset({
    "compute-marker-not-observed",
    "dispatch-error",
    "immediate-qstat-unavailable-after-retries",
    "malformed-request-id",
    "orphan-hold",
    "orphan-hold-promote-failed",
    "orphan-hold-release-failed",
    "orphan-hold-write-failed",
    "overall-timeout",
    "qstat-permission-or-ownership-error",
    "qstat-success-request-not-visible",
    "queue-wait-timeout",
    "receipt-persist-failed",
    "result/log/accounting-grace-expired",
    "setup-failure",
    "signal-abort",
    "submission-disabled",
    "unexpected-error",
})
DEFAULT_PROJECT = "SFC"
DEFAULT_QUEUE = "gen_S"
DEFAULT_WALLTIME = "01:00:00"
DEFAULT_QUEUE_WAIT_TIMEOUT_S = 900.0
DEFAULT_OVERALL_GRACE_S = 300.0
DEFAULT_ACCOUNTING_GRACE_S = 60.0
DEFAULT_POLL_INTERVAL_S = 5.0
DEFAULT_LOG_LIMIT_BYTES = 2 * 1024 * 1024
DEFAULT_SUCCESS_RELAY_LIMIT_BYTES = 4 * 1024
DEFAULT_FAILURE_RELAY_LIMIT_BYTES = 64 * 1024
DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS = 3
DEFAULT_CLEANUP_BUDGET_S = 90.0

_TASK_RUN_ENV = "IZANAGI_TASK_RUN_ID"
_TASK_RUN_ROOT_ENV = "IZANAGI_TASK_RUNS_ROOT"
_TASK_RUN_SIDECAR_ENV = "IZANAGI_TASK_RUN_SIDECAR"
_TASK_RUN_AUTO_RECORD_ENV = "IZANAGI_TASK_RUN_AUTO_RECORD"
_COMPUTE_MARKER_NAME = mutation_attempt_marker.COMPUTE_MARKER_NAME
_ORPHAN_HOLD_NAME = "orphan-hold.json"
_ORPHAN_HOLD_DIR_NAME = "orphan-holds"
_ORPHAN_HOLD_SCHEMA = "pegasus-orphan-hold/v1"
_CONTROL_LOCK_NAME = "submission.lock"
_INTENT_SCHEMA = "pegasus-dispatch-intent/v1"
_INTENT_CONFIRM_SCHEMA = "pegasus-dispatch-intent-confirm/v1"
_INTENT_HANDLED_SCHEMA = "pegasus-dispatch-intent-handled/v1"
_INTENT_RECOVERY_SCHEMA = "pegasus-dispatch-intent-recovery/v1"


class _DispatchResult(int):
    """整数 rc と child 起動証拠を同時に返す親向け dispatcher receipt。"""

    def __new__(cls, value: int, *, child_started: bool):
        result = int.__new__(cls, value)
        result.child_started = child_started
        return result


@dataclass(frozen=True)
class _TaskSpec:
    """1 task 種別が計算ノードで必要とする実体・環境・interpreter 条件。"""

    child_script: tuple[str, ...]
    env_allowlist: frozenset[str]
    probe_imports: tuple[str, ...]
    env_mode: str
    argv_policy: str


# 閉じた task enum。generic も login で直接 exec せず、既存の job script / _job_run
# 二重 compute gate の内側だけで argv を実行する。
TASKS = {
    "tests": _TaskSpec(
        child_script=("tools", "run_tests.py"),
        env_allowlist=frozenset({
            "PYTEST_ADDOPTS",
            "IZANAGI_TEST_NPROC",
            "IZANAGI_TEST_TRIGGER",
            # Parent-owned automatic observation transport.  The marker keeps
            # a compute-side run_tests.py from creating a second generation.
            _TASK_RUN_SIDECAR_ENV,
            _TASK_RUN_AUTO_RECORD_ENV,
            # 計算ノードに bytecode を書かせない指定を伝える。
            "PYTHONDONTWRITEBYTECODE",
            # 成長比例テストの明示 opt-in を計算ノードへ伝える。
            "IZANAGI_RUN_GROWTH_HELD_TESTS",
        }),
        probe_imports=("pytest", "xdist", "packaging"),
        env_mode="inherit",
        argv_policy="passthrough",
    ),
    # provenance 履歴監査は stdlib + git だけで動き、GIT_* は checker 自身が隔離するので
    # 親の環境値を 1 つも必要としない。
    "provenance": _TaskSpec(
        child_script=("tools", "check_ai_provenance.py"),
        env_allowlist=frozenset(),
        probe_imports=(),
        env_mode="inherit",
        argv_policy="passthrough",
    ),
    # wrapper は同じ interpreter で harness と run_tests.py を起動する。後者は
    # packaging を import し、Pegasus compute では pytest / xdist を要求する。
    "mutation": _TaskSpec(
        child_script=("tools", "mutation_worktree.py"),
        env_allowlist=frozenset(),
        probe_imports=("pytest", "xdist", "packaging"),
        env_mode="clean",
        argv_policy="mutation-worktree-v1",
    ),
    # <argv> は argv 自体を shell=False で実行する静的 inventory 用 sentinel。
    "generic": _TaskSpec(
        child_script=("<argv>",),
        env_allowlist=frozenset(),
        probe_imports=(),
        env_mode="clean",
        argv_policy="generic-v1",
    ),
}
DEFAULT_TASK = "tests"
_REQUEST_SCHEMA = "pegasus-dispatch-request/v2"
# v1 も受理する: queue 待ちの in-flight job は投入時点の request を、起動時点の live repo の
# _job_run で読む。一方向 bump は待ち中に land した job を殺すので互換受理を持つ。
_LEGACY_REQUEST_SCHEMA = "pegasus-dispatch-request/v1"
_REQUEST_BINDING = "sha256-job-script/v1"
_REQUEST_SHA256_ENV = "IZANAGI_DISPATCH_REQUEST_SHA256"
_JOB_SESSION_SWEEP_ENV = "IZANAGI_DISPATCH_JOB_SESSION_SWEEP"
_SESSION_SWEEP_TERM_GRACE_S = 5.0
_SESSION_SWEEP_KILL_GRACE_S = 1.0
_SESSION_SWEEP_ROUNDS = 2
_ACCEPTANCE_SHARDS_ENV = "IZANAGI_ACCEPTANCE_SHARDS"
_RUNNER_BINDING_FD_ENV = "IZANAGI_ACCEPTANCE_RUNNER_BINDING_FD"
_RUNNER_BINDING_NONCE_ENV = "IZANAGI_ACCEPTANCE_RUNNER_BINDING_NONCE"
_RUNNER_BINDING_TESTED_MAIN_ENV = (
    "IZANAGI_ACCEPTANCE_RUNNER_BINDING_TESTED_MAIN"
)
_RUNNER_BINDING_ENV_KEYS = frozenset(
    {
        _RUNNER_BINDING_FD_ENV,
        _RUNNER_BINDING_NONCE_ENV,
        _RUNNER_BINDING_TESTED_MAIN_ENV,
    }
)
_RUNNER_BINDING_FIELDS = frozenset(
    {"tested_main", "nonce", "shard_count", "shard_index"}
)
_RUNNER_BINDING_REPORT_SCHEMA = "dev-wave-runner-binding-report/v1"
_BOUND_XDIST_ROOT_RESULT_FIELD = "bound_xdist_distribution_root"
_RUNNER_BINDING_REPORT_FIELDS = frozenset(
    {
        "schema_version",
        "tested_main",
        "nonce",
        "runner_executed_sha256",
        "shard_count",
        "shard_index",
    }
)
_BOUND_RUNNER_BOOTSTRAP = (
    "import sys\n"
    "sys.dont_write_bytecode = True\n"
    "sys.path.append(sys.argv[2])\n"
    "source = sys.stdin.buffer.read()\n"
    "namespace = {\n"
    "    '__name__': '_izanagi_acceptance_runner',\n"
    "    '__file__': sys.argv[1],\n"
    "}\n"
    "exec(compile(source, namespace['__file__'], 'exec'), namespace)\n"
    "raise SystemExit(namespace['main'](sys.argv[3:]))\n"
)
_RESULT_GUARD_STAGE = "result-guard"
_ISOLATION_UNSHARE_COMMAND = "/usr/bin/unshare"
_ISOLATION_MOUNT_COMMAND = "/usr/bin/mount"
_ISOLATED_CHILD_STATUS_LIMIT = 64 * 1024
_ISOLATED_CHILD_EXEC_ERROR_LIMIT = 4 * 1024
_ISOLATED_CHILD_BOOTSTRAP = r'''
import ctypes
import json
import os
import subprocess
import sys
import time

status_fd = int(sys.argv[1])
exec_error_fd = int(sys.argv[2])
mount_command = sys.argv[3]
submission_dir = sys.argv[4]
real_uid = int(sys.argv[5])
real_gid = int(sys.argv[6])
child_argv = sys.argv[7:]
os.set_inheritable(status_fd, False)
os.set_inheritable(exec_error_fd, False)


def emit(event, **fields):
    payload = {"event": event, **fields}
    pending = memoryview(
        (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        .encode("ascii")
    )
    while pending:
        written = os.write(status_fd, pending)
        if written <= 0:
            raise OSError("short isolation status write")
        pending = pending[written:]


def trace(event, **fields):
    try:
        print("IZANAGI_DISPATCH_JOB_TRACE " + json.dumps({
            "event": event, "time_ns": time.time_ns(), "pid": os.getpid(),
            **fields,
        }, sort_keys=True), file=sys.stderr, flush=True)
    except OSError:
        pass


def mount(*args):
    subprocess.run(
        [mount_command, *args],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def write_mapping(path, text):
    with open(path, "w", encoding="ascii") as handle:
        handle.write(text)


try:
    mount("--make-rprivate", "/")
    ancestor = os.path.dirname(submission_dir)
    ancestors = []
    while ancestor != "/":
        ancestors.append(ancestor)
        ancestor = os.path.dirname(ancestor)
    for ancestor in reversed(ancestors):
        mount("--bind", ancestor, ancestor)
    mount("--bind", submission_dir, submission_dir)
    mount("-o", "remount,bind,ro", submission_dir)
    child_pid = os.fork()
except BaseException:
    try:
        emit("setup-failure", phase="outer-mount")
    finally:
        raise SystemExit(16)

if child_pid == 0:
    phase = "inner-userns"
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.unshare(0x10000000) != 0:
            error_number = ctypes.get_errno()
            raise OSError(error_number, os.strerror(error_number))
        write_mapping("/proc/self/setgroups", "deny\n")
        write_mapping("/proc/self/uid_map", f"{real_uid} 0 1\n")
        write_mapping("/proc/self/gid_map", f"{real_gid} 0 1\n")
        os.setresgid(real_gid, real_gid, real_gid)
        os.setresuid(real_uid, real_uid, real_uid)
        phase = "exec"
        emit("setup-complete")
        try:
            os.execvpe(child_argv[0], child_argv, os.environ)
        except BaseException as exc:
            pending = memoryview(
                (f"{type(exc).__name__}: {exc}\n").encode(
                    "ascii", errors="backslashreplace"
                )
            )
            while pending:
                written = os.write(exec_error_fd, pending)
                if written <= 0:
                    raise OSError("short exec error write")
                pending = pending[written:]
            raise
    except BaseException:
        try:
            emit("setup-failure", phase=phase)
        except BaseException:
            pass
        os._exit(16)

os.close(exec_error_fd)
trace("direct-child-wait-start", child_pid=child_pid)
while True:
    try:
        waited_pid, wait_status = os.waitpid(child_pid, 0)
        break
    except InterruptedError:
        continue
if waited_pid != child_pid:
    emit("status-failure", phase="waitpid")
    raise SystemExit(16)
trace("direct-child-wait-complete", child_pid=child_pid)
emit("wait-status", status=wait_status)
trace("supervisor-return", rc=0)
raise SystemExit(0)
'''
# v1 を生成していた a34266d2 の正規 request overlay 集合。現行 tests の
# allowlist と混ぜると、queue 待ち中の正規 v1 request を過剰拒否する。
_LEGACY_V1_ENV_ALLOWLIST = frozenset({
    "PYTEST_ADDOPTS",
    "IZANAGI_TEST_NPROC",
    "IZANAGI_TEST_TRIGGER",
    "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS",
})
_LEGACY_UNBOUND_TASKS = frozenset({"tests", "provenance"})
_CLEAN_CHILD_ENV_KEYS = frozenset({
    "HOME",
    "LANG",
    "LANGUAGE",
    "LC_ALL",
    "LC_CTYPE",
    "LOGNAME",
    "PATH",
    "TZ",
    "USER",
})
_RECEIPT_SCHEMA = "pegasus-dispatch-receipt/v2"
_QSTAT_ERROR_MARKERS = {
    "permission": (
        "not permitted",
        "permission",
        "eacces",
        "not authorized",
        "unauthorized",
        "access denied",
        "not owner",
        "ownership",
    ),
    "transient": (
        "connection",
        "cannot connect",
        "timeout",
        "timed out",
        "server busy",
        "temporarily unavailable",
        "try again",
    ),
}
_NQSV_REQUEST_ID_RE = re.compile(
    r"(?m)^[ \t]*Request ID:[ \t]*(\S+)[ \t]*$"
)
_NQSV_GROUP_NAME_RE = re.compile(
    r"(?m)^[ \t]*Group Name:[ \t]*(\S+)[ \t]*$"
)
_NQSV_STARTED_RE = re.compile(
    r"(?m)^[ \t]*Started Request Time:[ \t]*\S.*$"
)
_NQSV_ENDED_RE = re.compile(
    r"(?m)^[ \t]*Ended Request Time:[ \t]*\S.*$"
)
_NQSV_ELAPSE_RE = re.compile(r"(?m)^[ \t]*Elapse:[ \t]*\S.*$")
_STATE_RE = re.compile(
    r"(?im)^\s*(?:Request\s+)?State\s*=\s*(QUE|RUN|HLD|STG|EXT)\s*$"
)
_CURRENT_STATE_RE = re.compile(r"(?im)^\s*Current\s+State\s*=\s*([^\r\n]+?)\s*$")
_REQUEST_RE = re.compile(r"Request\s+(\S+)\s+submitted")
_QSTAT_REQUEST_ID_RE = re.compile(
    r"(?im)^\s*Request\s+ID\s*[:=]\s*(\S+)\s*$"
)
_QSTAT_REQUEST_NAME_RE = re.compile(
    r"(?im)^\s*Request\s+Name\s*[:=]\s*(\S+)\s*$"
)
_GATE_REQUEST_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_QDEL_CLEANUP_POLICY = "fresh-qstat-gate/v1"
_INTERPRETER_CANDIDATES = (
    "python3.10",
    "/usr/bin/python3.10",
    "/bin/python3.10",
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
Clock = Callable[[], float]
Sleeper = Callable[[float], None]


class DispatchError(RuntimeError):
    """scheduler / receipt infrastructure が成立しない。"""


class _ChildIsolationError(DispatchError):
    """被検査 argv の起動前または親所有 status 経路が成立しない。"""


class _OrphanHoldError(DispatchError):
    """orphan hold の create/promote/release を fail-closed にする。"""

    def __init__(
        self,
        reason: str,
        *,
        operation: str,
        path: Path,
        detail: Optional[str] = None,
    ):
        super().__init__(reason)
        self.reason = reason
        self.operation = operation
        self.path = path
        self.detail = detail


class _SignalAbort(DispatchError):
    def __init__(self, signum: int):
        super().__init__(f"signal {signum}")
        self.signum = signum


def _infra_attestation_reason(exc: BaseException) -> str:
    """例外を外部文字列を含まない closed vocabulary へ射影する。"""

    if isinstance(exc, _SignalAbort):
        return "signal-abort"
    if isinstance(exc, DispatchError):
        reason = str(exc)
        if reason in _DISPATCH_INFRA_REASONS:
            return reason
        return "dispatch-error"
    return "unexpected-error"


def _return_infra(
    reason: str,
    *,
    child_started: bool,
    child_rc: Optional[int] = None,
    allow_unstarted: bool = False,
) -> int:
    """dispatcher 自身の infra 終端を 1 行 attest して既存 rc を返す。"""

    normalized_reason = (
        reason if reason in _DISPATCH_INFRA_REASONS else "unexpected-error"
    )
    normalized_child_rc = child_rc if type(child_rc) is int else None
    normalized_started = child_started if type(child_started) is bool else True
    if not normalized_started and not allow_unstarted and (
        normalized_reason != "queue-wait-timeout"
        or normalized_child_rc is not None
    ):
        normalized_started = True
    payload = {
        "child_rc": normalized_child_rc,
        "child_started": normalized_started,
        "kind": "infra",
        "reason": normalized_reason,
    }
    print(
        _DISPATCH_OUTCOME_PREFIX + json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ),
        file=sys.stderr,
        flush=True,
    )
    return _DispatchResult(INFRA_RC, child_started=normalized_started)


def _walltime_seconds(value: str) -> int:
    match = re.fullmatch(r"([0-9]+):([0-5][0-9]):([0-5][0-9])", value)
    if match is None:
        raise ValueError("walltime は HH:MM:SS 形式で指定してください")
    hours, minutes, seconds = (int(part) for part in match.groups())
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ValueError("walltime は 0 より大きくしてください")
    return total


def _normalize_request_id(value: str) -> str:
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        raise DispatchError("request ID が空です")
    return normalized


def _parse_request_id(stdout: str) -> str:
    match = _REQUEST_RE.search(stdout)
    if match is not None:
        return match.group(1).rstrip(".")
    tokens = stdout.split()
    if len(tokens) == 1:
        return tokens[0].rstrip(".")
    raise DispatchError("qsub 成功出力から request ID を一意に抽出できません")


def _qstat_mentions_request(stdout: str, request_id: str) -> bool:
    """qstat 成功応答が対象 request の構造化 ID field を含むか検査する。"""

    expected = _normalize_request_id(request_id)
    for observed in _QSTAT_REQUEST_ID_RE.findall(stdout):
        try:
            if _normalize_request_id(observed) == expected:
                return True
        except DispatchError:
            continue
    return False


def _classify_qstat_response(
    result: subprocess.CompletedProcess[str],
    request_id: str,
) -> str:
    """qstat 応答を F47 権限系・一時系・成功可視性へ分類する。"""

    if result.returncode == 0:
        return (
            "success-request-visible"
            if _qstat_mentions_request(result.stdout or "", request_id)
            else "success-request-absent"
        )
    response = "\n".join((result.stdout or "", result.stderr or "")).casefold()
    if any(marker in response for marker in _QSTAT_ERROR_MARKERS["permission"]):
        return "permission"
    if any(marker in response for marker in _QSTAT_ERROR_MARKERS["transient"]):
        return "transient"
    # 誤ラッチは harness を恒久停止するため、未知の非ゼロも一時系へ倒す。
    return "transient"


def _scheduler_state(stdout: str) -> Optional[str]:
    match = _STATE_RE.search(stdout)
    if match is not None:
        return _gate_state_value("State", match.group(1))
    match = _CURRENT_STATE_RE.search(stdout)
    if match is None:
        return None
    return _gate_state_value("Current State", match.group(1))


def _progress(message: str) -> None:
    print(f"[Pegasus dispatch] {message}", flush=True)


def _emit(text: str, *, stream: Any) -> None:
    """親 process の指定 stream へ relay text を書く注入 seam。"""

    print(text, end="", file=stream, flush=True)


def _capture(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "returncode": int(result.returncode),
        "stdout": (result.stdout or "")[-65536:],
        "stderr": (result.stderr or "")[-65536:],
    }


def _run(
    run_command: CommandRunner,
    command: Sequence[str],
    *,
    cwd: Path,
    environ: Mapping[str, str],
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        list(command),
        cwd=str(cwd),
        env=dict(environ),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _write_json_x(path: Path, payload: Mapping[str, Any], *, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(_canonical_json_text(payload))
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _canonical_json_text(payload: Mapping[str, Any]) -> str:
    """_write_json_x と同じ canonical JSON bytes を事前計算する。"""

    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, indent=2,
    ) + "\n"


def _write_json_atomic_replace(
    path: Path,
    payload: Mapping[str, Any],
    *,
    mode: int = 0o600,
    create_only: bool = False,
) -> None:
    """同一 directory 内で JSON を durable に公開する。"""

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_dir(path.parent)
        if create_only:
            os.link(temporary, path)
            _fsync_dir(path.parent)
            temporary.unlink()
            _fsync_dir(path.parent)
        else:
            os.replace(temporary, path)
            _fsync_dir(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _write_result_replace(path: Path, payload: Mapping[str, Any]) -> None:
    """guard を同一 directory の fsync 済み JSON から一度だけ置換する。"""

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    published = False
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            _job_trace("result-file-fsync-start")
            os.fsync(handle.fileno())
            _job_trace("result-file-fsync-complete")
        os.replace(temporary, path)
        published = True
        _job_trace("result-published")
        _job_trace("result-dir-fsync-start")
        _fsync_dir(path.parent)
        _job_trace("result-dir-fsync-complete")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if not published:
            try:
                temporary.unlink()
            except OSError:
                pass
    _job_trace("result-write-return")


def _job_trace(event: str, **fields: Any) -> None:
    """Job stderr diagnostics only; never an attestation or acceptance input."""

    try:
        print("IZANAGI_DISPATCH_JOB_TRACE " + json.dumps({
            "event": event, "time_ns": time.time_ns(), "pid": os.getpid(),
            **fields,
        }, sort_keys=True), file=sys.stderr, flush=True)
    except OSError:
        pass


def _read_session_process(pid: int) -> dict[str, Any]:
    """Read stat without splitting a comm that contains spaces or parentheses."""

    raw = Path(f"/proc/{pid}/stat").read_text()
    left, right = raw.index("("), raw.rindex(")")
    tail = raw[right + 1:].split()
    if int(raw[:left].strip()) != pid:
        raise ValueError("stat pid mismatch")
    return {
        "pid": pid, "comm": raw[left + 1:right], "state": tail[0],
        "ppid": int(tail[1]), "pgrp": int(tail[2]),
        "session": int(tail[3]), "starttime": int(tail[19]),
        "readable": True,
    }


def _list_session_residuals(
    sid: int, excluded_pids: set[int], own_user_ns: str,
) -> list[dict[str, Any]]:
    records = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal() or int(entry.name) in excluded_pids:
            continue
        pid = int(entry.name)
        try:
            record = _read_session_process(pid)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (OSError, ValueError, IndexError) as exc:
            # Session membership cannot be established: record uncertainty,
            # but never signal a process whose stat could not be read.
            record = dict.fromkeys(("comm", "state", "ppid", "pgrp",
                                    "session", "starttime"))
            record.update(pid=pid, readable=False, error=type(exc).__name__)
        if record["readable"] and record["session"] != sid:
            continue
        try:
            user_ns = os.readlink(f"/proc/{pid}/ns/user")
        except OSError:
            user_ns = None
        uid = None
        try:
            for line in Path(f"/proc/{pid}/status").read_text().splitlines():
                if line.startswith("Uid:"):
                    uid = int(line.split()[1])
                    break
        except (OSError, ValueError, IndexError):
            pass
        attributed = user_ns is not None and user_ns != own_user_ns
        record.update(user_ns=user_ns, uid=uid, attributed=attributed)
        records.append(record)
    return records


def _signal_session_process(fd: int, record: dict[str, Any], sig: int) -> bool:
    result, error_number = "sent", None
    try:
        signal.pidfd_send_signal(fd, sig)
    except ProcessLookupError as exc:
        result, error_number = "esrch", exc.errno
    except PermissionError as exc:
        result, error_number = "eperm", exc.errno
    except OSError as exc:
        result, error_number = "error", exc.errno
    _job_trace("session-signal", process=record,
               signal=signal.Signals(sig).name.removeprefix("SIG"),
               result=result, errno=error_number, time_ns=time.time_ns())
    return result == "sent"


def _poll_session_processes(
    pending: dict[int, dict[str, Any]], grace_s: float, after: str,
) -> int:
    if not pending:
        return 0
    poller = select.poll()
    for fd in pending:
        poller.register(fd, select.POLLIN)
    deadline = time.monotonic() + grace_s
    exited = 0
    while pending:
        remaining = max(0.0, deadline - time.monotonic())
        events = poller.poll(math.ceil(remaining * 1000))
        for fd, flags in events:
            if fd in pending and flags & select.POLLIN:
                record = pending.pop(fd)
                poller.unregister(fd)
                exited += 1
                _job_trace("session-process-exited", process=record,
                           after=after, time_ns=time.time_ns())
        if time.monotonic() >= deadline:
            break
    return exited


def _sweep_job_session(
    sid: int, *, own_user_ns: str, excluded_pids: set[int],
    term_grace_s: float, kill_grace_s: float, rounds: int,
) -> None:
    started = time.monotonic()
    seen: dict[tuple[int, Optional[int]], dict[str, Any]] = {}
    rounds_used = exited_after_term = exited_after_kill = 0
    for round_index in range(rounds):
        rounds_used += 1
        candidates = _list_session_residuals(sid, excluded_pids, own_user_ns)
        new = []
        for record in candidates:
            _job_trace("session-residual", round=round_index + 1, process=record)
            key = (record["pid"], record["starttime"])
            if key not in seen:
                seen[key] = record
                new.append(record)
        if not new:
            break
        opened = []
        pending: dict[int, dict[str, Any]] = {}
        try:
            for record in new:
                if (not record["readable"] or not record["attributed"]
                        or record["state"] == "Z"):
                    continue
                try:
                    fd = os.pidfd_open(record["pid"])
                except OSError as exc:
                    _job_trace("session-signal", process=record, signal="TERM",
                               result="pidfd-unavailable", errno=exc.errno)
                    continue
                opened.append(fd)
                try:
                    current = _read_session_process(record["pid"])
                    result = ("identity-changed" if current["starttime"] !=
                              record["starttime"] else "ready")
                    if result == "ready" and current["state"] == "Z":
                        result = "zombie"
                except (FileNotFoundError, ProcessLookupError):
                    result = "absent"
                except (OSError, ValueError, IndexError):
                    result = "unreadable"
                if result != "ready":
                    _job_trace("session-signal", process=record, signal="TERM",
                               result=result)
                    os.close(fd)
                    opened.remove(fd)
                    continue
                if _signal_session_process(fd, record, signal.SIGTERM):
                    pending[fd] = record
            exited_after_term += _poll_session_processes(
                pending, term_grace_s, "term",
            )
            for fd, record in pending.items():
                _signal_session_process(fd, record, signal.SIGKILL)
            exited_after_kill += _poll_session_processes(
                pending, kill_grace_s, "kill",
            )
            for record in pending.values():
                try:
                    state = _read_session_process(record["pid"])["state"]
                except (OSError, ValueError, IndexError):
                    state = None
                _job_trace("session-process-remaining", process=record, state=state)
        finally:
            for fd in opened:
                os.close(fd)
    final = _list_session_residuals(sid, excluded_pids, own_user_ns)
    attributed = [r for r in final if r["readable"] and r["attributed"]]
    session_unknown = sum(not r["readable"] for r in final)
    zombies = sum(r["state"] == "Z" for r in attributed)
    remaining = sum(r["readable"] and r["state"] != "Z" for r in attributed)
    _job_trace(
        "session-sweep-complete",
        status="remaining" if remaining or zombies else "unknown" if session_unknown else "clean",
        rounds_used=rounds_used, found_total=len(seen),
        attributed_total=sum(r["attributed"] for r in seen.values()),
        unattributed_total=sum(not r["attributed"] for r in seen.values()),
        exited_after_term=exited_after_term, exited_after_kill=exited_after_kill,
        remaining=remaining, zombies=zombies, session_unknown=session_unknown,
        elapsed_ms=(time.monotonic() - started) * 1000,
    )


def _maybe_sweep_job_session(request_sha256: Optional[str]) -> None:
    if request_sha256 is None or os.environ.get(_JOB_SESSION_SWEEP_ENV) != request_sha256:
        return
    try:
        sid = os.getsid(0)
        own_ns = os.readlink("/proc/self/ns/user")
        ancestors = []
        visited: set[int] = set()
        pid = os.getpid()
        try:
            while pid > 0 and pid not in visited:
                visited.add(pid)
                record = _read_session_process(pid)
                ancestors.append({"pid": pid, "comm": record["comm"]})
                if pid == 1:
                    break
                pid = record["ppid"]
        except (OSError, ValueError, IndexError) as exc:
            _job_trace("session-sweep-error", reason="ancestry-unreadable",
                       type=type(exc).__name__, message=str(exc))
            return
        excluded = {ancestor["pid"] for ancestor in ancestors}
        _job_trace("session-sweep-start", sid=sid, own_user_ns=own_ns,
                   ancestors=ancestors)
        _sweep_job_session(
            sid, own_user_ns=own_ns, excluded_pids=excluded,
            term_grace_s=_SESSION_SWEEP_TERM_GRACE_S,
            kill_grace_s=_SESSION_SWEEP_KILL_GRACE_S, rounds=_SESSION_SWEEP_ROUNDS,
        )
    except Exception as exc:
        _job_trace("session-sweep-error", type=type(exc).__name__, message=str(exc))


def _intent_path(registry_root: Path, shard_index: int, suffix: str) -> Path:
    return registry_root / f"shard-{shard_index}.{suffix}.json"


def _register_dispatch_intent(
    registry_root: Path,
    *,
    group_id: str,
    shard_index: int,
    job_name: str,
    submission_dir: Path,
) -> Path:
    path = _intent_path(registry_root, shard_index, "intent")
    _write_json_x(path, {
        "schema_version": _INTENT_SCHEMA,
        "group_id": group_id,
        "shard_index": shard_index,
        "job_name": job_name,
        "submission_dir": str(submission_dir),
    })
    _fsync_dir(registry_root)
    return path


def _confirm_dispatch_intent(
    registry_root: Path,
    *,
    shard_index: int,
    request_id: str,
) -> Path:
    path = _intent_path(registry_root, shard_index, "confirm")
    _write_json_x(path, {
        "schema_version": _INTENT_CONFIRM_SCHEMA,
        "shard_index": shard_index,
        "request_id": request_id,
    })
    _fsync_dir(registry_root)
    return path


def _mark_dispatch_intent_handled(
    registry_root: Path,
    *,
    shard_index: int,
    request_id: Optional[str],
) -> None:
    path = _intent_path(registry_root, shard_index, "handled")
    try:
        _write_json_x(path, {
            "schema_version": _INTENT_HANDLED_SCHEMA,
            "shard_index": shard_index,
            "request_id": request_id,
        })
        _fsync_dir(registry_root)
    except FileExistsError:
        pass


def _write_text_x(path: Path, text: str, *, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _interpreter_probe_source(task: str = DEFAULT_TASK) -> str:
    """各候補自身で版数と task 固有の importability を assert する短い probe。

    既定引数は省略できない — probe は job script 生成の外 (テスト) からも無引数で
    呼ばれる。版数検査は task に依らず常に置く (_job_run と二層冗長 gate をなす)。
    """

    spec = TASKS[task]
    head = (
        "import sys\n"
        "if sys.version_info < (3, 10):\n"
        "    raise SystemExit(1)\n"
    )
    if not spec.probe_imports:
        return head + "raise SystemExit(0)\n"
    imports = "".join(f"    import {name}\n" for name in spec.probe_imports)
    return (
        head
        + "try:\n"
        + imports
        + "except Exception:\n"
        "    raise SystemExit(1)\n"
        "raise SystemExit(0)\n"
    )


def _job_name(nonce: str) -> str:
    """submission nonce から PBS job name を一意に導く。"""

    return f"izdw-{nonce[:10]}"


def _job_script(
    *,
    repo_root: Path,
    submission_dir: Path,
    request_path: Path,
    probe_path: Path,
    request_sha256: str,
    walltime: str,
    dispatcher_path: Optional[Path] = None,
    task: str = DEFAULT_TASK,
) -> str:
    result_path = submission_dir / "result.json"
    marker_path = submission_dir / _COMPUTE_MARKER_NAME
    job_name = _job_name(submission_dir.name)
    dispatcher = (
        repo_root / "tools" / "pegasus" / "dispatch_compute.py"
        if dispatcher_path is None else Path(dispatcher_path)
    )
    task_transport_unset = (
        ""
        if task == "tests"
        else f"unset {_TASK_RUN_SIDECAR_ENV} {_TASK_RUN_AUTO_RECORD_ENV}\n"
    )
    candidates = " ".join(shlex.quote(value) for value in _INTERPRETER_CANDIDATES)
    return f"""#!/bin/bash
#PBS -A {DEFAULT_PROJECT}
#PBS -q {DEFAULT_QUEUE}
#PBS -b 1
#PBS -l elapstim_req={walltime}
#PBS -N {job_name}
set -u

RESULT={shlex.quote(str(result_path))}
PROBE={shlex.quote(str(probe_path))}
REQUEST={shlex.quote(str(request_path))}
REQUEST_SHA256={shlex.quote(request_sha256)}
REPO={shlex.quote(str(repo_root))}
DISPATCHER={shlex.quote(str(dispatcher))}
MARKER={shlex.quote(str(marker_path))}

write_failure() {{
    local stage=$1
    local tmp="${{RESULT}}.tmp.$$"
    printf '{{"schema_version":"pegasus-dispatch-result/v1","stage":"%s","child_rc":16,"pbs_jobid":"%s"}}\\n' \
        "$stage" "${{PBS_JOBID:-unknown}}" >"$tmp"
    mv "$tmp" "$RESULT"
}}

host=$(hostname 2>/dev/null || true)
if [[ ! "$host" =~ ^bnode[0-9]+([.].*)?$ ]]; then
    write_failure hostname
    exit {INFRA_RC}
fi
marker_tmp="${{MARKER}}.tmp.$$"
printf '{{"schema_version":"pegasus-compute-visible/v1","pbs_jobid":"%s","hostname":"%s"}}\\n' \
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
mv "$marker_tmp" "$MARKER"

selected=""
for candidate in {candidates}; do
    resolved=$(command -v "$candidate" 2>/dev/null || true)
    if [[ -n "$resolved" ]] && "$resolved" "$PROBE" >/dev/null 2>&1; then
        selected=$resolved
        break
    fi
done
if [[ -z "$selected" ]]; then
    write_failure interpreter
    exit {INFRA_RC}
fi

if ! cd "$REPO"; then
    write_failure cwd
    exit {INFRA_RC}
fi

export PATH="$(dirname "$selected"):$PATH"
export {_REQUEST_SHA256_ENV}="$REQUEST_SHA256"
export {_JOB_SESSION_SWEEP_ENV}="$REQUEST_SHA256"
unset {_TASK_RUN_ENV} {_TASK_RUN_ROOT_ENV}
{task_transport_unset}exec "$selected" "$DISPATCHER" --job-run "$REQUEST"
"""


def _read_json_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise DispatchError(f"required JSON がありません: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise DispatchError(f"JSON を読めません: {path}: {exc}") from exc
    if type(value) is not dict:
        raise DispatchError(f"JSON object ではありません: {path}")
    return value


def _read_request_object_and_sha256(path: Path) -> tuple[dict[str, Any], str]:
    """request bytes を 1 度だけ読み、parse 対象と SHA-256 を同じ bytes に束縛する。"""

    if path.is_symlink() or not path.is_file():
        raise DispatchError(f"required JSON がありません: {path}")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DispatchError(f"JSON を読めません: {path}: {exc}") from exc
    if type(value) is not dict:
        raise DispatchError(f"JSON object ではありません: {path}")
    return value, hashlib.sha256(raw).hexdigest()


def _resolve_request(request: Mapping[str, Any]) -> tuple[str, Any]:
    """request payload を (task, argv) へ解決する。schema v1 / v2 の両方を受理する。

    v1 には task 概念が無く、投入できた唯一の task は ``tests`` であった。未知の
    schema_version だけを拒否することで、queue 待ち中に新 schema が land しても
    in-flight job を殺さない。
    """

    schema = request.get("schema_version")
    if schema == _LEGACY_REQUEST_SCHEMA:
        return DEFAULT_TASK, request["pytest_args"]
    if schema == _REQUEST_SCHEMA:
        task = request.get("task")
        if type(task) is not str:
            raise DispatchError("task は string でなければなりません")
        return task, request["args"]
    raise DispatchError(f"未知の request schema_version です: {schema!r}")


def _runner_binding_from_environment(
    command_env: Mapping[str, str],
    *,
    task: str,
    intent_shard_index: Optional[int],
) -> tuple[Optional[dict[str, Any]], Optional[int]]:
    present = {name for name in _RUNNER_BINDING_ENV_KEYS if name in command_env}
    if not present:
        return None, None
    if present != _RUNNER_BINDING_ENV_KEYS:
        raise ValueError("runner binding environment is incomplete")

    raw_fd = command_env[_RUNNER_BINDING_FD_ENV]
    nonce = command_env[_RUNNER_BINDING_NONCE_ENV]
    tested_main = command_env[_RUNNER_BINDING_TESTED_MAIN_ENV]
    raw_shard_count = command_env.get(_ACCEPTANCE_SHARDS_ENV)
    if re.fullmatch(r"(?:0|[1-9][0-9]*)", raw_fd) is None:
        raise ValueError("runner binding fd is invalid")
    if re.fullmatch(r"[0-9a-f]{64}", nonce) is None:
        raise ValueError("runner binding nonce is invalid")
    if re.fullmatch(r"[0-9a-f]{40}", tested_main) is None:
        raise ValueError("runner binding tested-main is invalid")
    if raw_shard_count not in {"1", "2", "3"}:
        raise ValueError("runner binding shard count is invalid")
    shard_count = int(raw_shard_count)
    shard_index = 0 if intent_shard_index is None else intent_shard_index
    if (
        type(shard_index) is not int
        or shard_index < 0
        or shard_index >= shard_count
    ):
        raise ValueError("runner binding shard index is invalid")
    if task != "tests":
        return None, None
    assert TASKS[task].argv_policy == "passthrough"
    assert TASKS[task].child_script == ("tools", "run_tests.py")
    return (
        {
            "tested_main": tested_main,
            "nonce": nonce,
            "shard_count": shard_count,
            "shard_index": shard_index,
        },
        int(raw_fd),
    )


def _validated_runner_binding(
    request: Mapping[str, Any], *, task: str
) -> Optional[dict[str, Any]]:
    value = request.get("runner_binding")
    if value is None:
        return None
    if task != "tests" or type(value) is not dict:
        raise DispatchError("runner_binding is only valid for tests requests")
    if set(value) != _RUNNER_BINDING_FIELDS:
        raise DispatchError("runner_binding fields are invalid")
    tested_main = value["tested_main"]
    nonce = value["nonce"]
    shard_count = value["shard_count"]
    shard_index = value["shard_index"]
    if (
        type(tested_main) is not str
        or re.fullmatch(r"[0-9a-f]{40}", tested_main) is None
        or type(nonce) is not str
        or re.fullmatch(r"[0-9a-f]{64}", nonce) is None
        or type(shard_count) is not int
        or shard_count not in {1, 2, 3}
        or type(shard_index) is not int
        or shard_index < 0
        or shard_index >= shard_count
    ):
        raise DispatchError("runner_binding values are invalid")
    return dict(value)


def _isolated_child_rc(
    raw_status: bytes,
    raw_exec_error: bytes,
    supervisor_rc: int,
) -> int:
    """親所有 pipe の exec 証明と complete/wait record から child rc を得る。"""

    if len(raw_status) > _ISOLATED_CHILD_STATUS_LIMIT:
        raise _ChildIsolationError("isolation status exceeds limit")
    if raw_exec_error:
        raise _ChildIsolationError("isolated child exec failed")
    try:
        records = [
            json.loads(line.decode("ascii"))
            for line in raw_status.splitlines()
            if line
        ]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _ChildIsolationError("isolation status is malformed") from exc
    if any(
        type(record) is dict
        and record.get("event") in {"setup-failure", "status-failure"}
        for record in records
    ):
        raise _ChildIsolationError("isolated child setup failed")
    if supervisor_rc != 0:
        raise _ChildIsolationError("isolation supervisor failed")
    if (
        len(records) != 2
        or records[0] != {"event": "setup-complete"}
        or type(records[1]) is not dict
        or set(records[1]) != {"event", "status"}
        or records[1].get("event") != "wait-status"
        or type(records[1].get("status")) is not int
    ):
        raise _ChildIsolationError("isolation status sequence is invalid")
    wait_status = records[1]["status"]
    if not (os.WIFEXITED(wait_status) or os.WIFSIGNALED(wait_status)):
        raise _ChildIsolationError("isolated child wait status is not terminal")
    return os.waitstatus_to_exitcode(wait_status)


def _run_isolated_child(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    submission_dir: Path,
    stdin_bytes: Optional[bytes] = None,
) -> int:
    """read-only submission mount と入れ子 userns 内で argv を実行する。

    境界の相手はこの argv とその子孫だけであり、namespace 外の同一 uid process
    までは保護しない。outer userns が mount を所有し、argv は descendant userns
    に置くため、自分にだけ見える mount を追加できても親が読む実体は変更できない。
    """

    status_read_fd = -1
    status_write_fd = -1
    exec_read_fd = -1
    exec_write_fd = -1
    process: Optional[subprocess.Popen[bytes]] = None
    real_uid = os.getuid()
    real_gid = os.getgid()
    try:
        try:
            status_read_fd, status_write_fd = os.pipe2(os.O_CLOEXEC)
            exec_read_fd, exec_write_fd = os.pipe2(os.O_CLOEXEC)
        except OSError as exc:
            raise _ChildIsolationError(
                "cannot create isolation status pipes"
            ) from exc
        command = [
            _ISOLATION_UNSHARE_COMMAND,
            "--user",
            "--map-root-user",
            "--mount",
            "--",
            sys.executable,
            "-I",
            "-c",
            _ISOLATED_CHILD_BOOTSTRAP,
            str(status_write_fd),
            str(exec_write_fd),
            _ISOLATION_MOUNT_COMMAND,
            str(Path(submission_dir).resolve()),
            str(real_uid),
            str(real_gid),
            *argv,
        ]
        try:
            process = subprocess.Popen(
                command,
                cwd=str(cwd),
                env=dict(env),
                stdin=(
                    subprocess.PIPE
                    if stdin_bytes is not None else subprocess.DEVNULL
                ),
                shell=False,
                pass_fds=(status_write_fd, exec_write_fd),
            )
        except OSError as exc:
            raise _ChildIsolationError(
                "cannot launch isolation supervisor"
            ) from exc
        os.close(status_write_fd)
        status_write_fd = -1
        os.close(exec_write_fd)
        exec_write_fd = -1
        _job_trace("supervisor-wait-start")
        process.communicate(input=stdin_bytes)
        _job_trace("supervisor-wait-complete", rc=process.returncode)
        with os.fdopen(status_read_fd, "rb") as status_handle:
            status_read_fd = -1
            raw_status = status_handle.read(_ISOLATED_CHILD_STATUS_LIMIT + 1)
        with os.fdopen(exec_read_fd, "rb") as exec_handle:
            exec_read_fd = -1
            raw_exec_error = exec_handle.read(
                _ISOLATED_CHILD_EXEC_ERROR_LIMIT + 1
            )
        assert process.returncode is not None
        return _isolated_child_rc(
            raw_status,
            raw_exec_error,
            int(process.returncode),
        )
    except _ChildIsolationError:
        raise
    except Exception as exc:
        raise _ChildIsolationError("isolation status path failed") from exc
    finally:
        if status_write_fd >= 0:
            try:
                os.close(status_write_fd)
            except OSError:
                pass
        if status_read_fd >= 0:
            try:
                os.close(status_read_fd)
            except OSError:
                pass
        if exec_write_fd >= 0:
            try:
                os.close(exec_write_fd)
            except OSError:
                pass
        if exec_read_fd >= 0:
            try:
                os.close(exec_read_fd)
            except OSError:
                pass
        if process is not None and process.returncode is None:
            _job_trace("supervisor-final-wait-start")
            process.wait()
            _job_trace("supervisor-final-wait-complete", rc=process.returncode)


def _run_bound_tests_child(
    repo_root: Path,
    argv: Sequence[str],
    child_env: Mapping[str, str],
    runner_binding: Mapping[str, Any],
    xdist_distribution_root: Path,
    submission_dir: Path,
) -> tuple[int, str]:
    canonical_runner_path = repo_root / "tools" / "run_tests.py"
    child_argv = [
        sys.executable,
        "-I",
        "-c",
        _BOUND_RUNNER_BOOTSTRAP,
        str(canonical_runner_path),
        str(xdist_distribution_root),
        *argv,
    ]
    blob = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "cat-file",
            "blob",
            f"{runner_binding['tested_main']}:tools/run_tests.py",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_env,
    )
    if blob.returncode != 0:
        raise DispatchError("cannot read tested-main runner blob")
    source = blob.stdout
    actual_digest = hashlib.sha256(source).hexdigest()
    child_rc = _run_isolated_child(
        child_argv,
        cwd=repo_root,
        env=child_env,
        submission_dir=submission_dir,
        stdin_bytes=source,
    )
    return child_rc, actual_digest


def _resolve_xdist_distribution_root() -> Path:
    """import 済み xdist を包含する distribution root だけを受理する。"""

    try:
        located = importlib.metadata.distribution(
            "pytest-xdist"
        ).locate_file("")
        root = Path(located)
    except Exception as exc:
        raise DispatchError("cannot resolve pytest-xdist distribution root") from exc
    if not root.is_absolute():
        raise DispatchError("pytest-xdist distribution root is not absolute")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise DispatchError("cannot resolve pytest-xdist distribution root") from exc
    if not resolved_root.is_dir():
        raise DispatchError("pytest-xdist distribution root is not a directory")

    xdist_module = sys.modules.get("xdist")
    module_file = getattr(xdist_module, "__file__", None)
    if not isinstance(module_file, str):
        raise DispatchError("imported xdist has no file path")
    module_path = Path(module_file)
    if not module_path.is_absolute():
        raise DispatchError("imported xdist file path is not absolute")
    try:
        resolved_module_path = module_path.resolve(strict=True)
        resolved_module_path.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise DispatchError(
            "imported xdist is outside pytest-xdist distribution root"
        ) from exc
    if not resolved_module_path.is_file():
        raise DispatchError("imported xdist file path is not a file")
    return resolved_root


def _runner_binding_report(
    runner_binding: Mapping[str, Any], actual_digest: str
) -> dict[str, Any]:
    return {
        "schema_version": _RUNNER_BINDING_REPORT_SCHEMA,
        "tested_main": runner_binding["tested_main"],
        "nonce": runner_binding["nonce"],
        "runner_executed_sha256": actual_digest,
        "shard_count": runner_binding["shard_count"],
        "shard_index": runner_binding["shard_index"],
    }


def _validated_runner_binding_report(
    result: Mapping[str, Any], runner_binding: Mapping[str, Any]
) -> dict[str, Any]:
    report = result.get("runner_binding")
    if type(report) is not dict or set(report) != _RUNNER_BINDING_REPORT_FIELDS:
        raise DispatchError("result runner_binding report is missing or invalid")
    if report.get("schema_version") != _RUNNER_BINDING_REPORT_SCHEMA:
        raise DispatchError("result runner_binding schema is invalid")
    for field in ("tested_main", "nonce", "shard_count", "shard_index"):
        if report.get(field) != runner_binding[field]:
            raise DispatchError(f"result runner_binding {field} mismatch")
    digest = report.get("runner_executed_sha256")
    if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise DispatchError("result runner_binding digest is invalid")
    return dict(report)


def _write_runner_binding_report(fd: int, report: Mapping[str, Any]) -> None:
    try:
        mode = os.fstat(fd).st_mode
    except OSError as exc:
        raise DispatchError("cannot inspect runner binding report fd") from exc
    if not stat.S_ISFIFO(mode):
        raise DispatchError("runner binding report fd is not a pipe")
    pending = memoryview(
        (
            json.dumps(
                report,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("ascii")
    )
    while pending:
        try:
            written = os.write(fd, pending)
        except OSError as exc:
            raise DispatchError("cannot write runner binding report") from exc
        if written <= 0:
            raise DispatchError("short runner binding report write")
        pending = pending[written:]


def _import_probe_modules(spec: _TaskSpec) -> None:
    """task が要求する module だけを子起動前に import 検査する。"""

    for name in spec.probe_imports:
        __import__(name)


def _validate_task_argv(task: str, spec: _TaskSpec, argv: Any) -> None:
    """親と compute 子の双方で task 固有 argv 契約を同じ実装から検査する。"""

    if type(argv) is not list or not all(type(value) is str for value in argv):
        raise DispatchError("args は string list でなければなりません")
    if spec.argv_policy == "passthrough":
        return
    if spec.argv_policy == "generic-v1":
        if not argv or not argv[0]:
            raise DispatchError("generic args は空にできません")
        return
    if spec.argv_policy != "mutation-worktree-v1":
        raise DispatchError(
            f"task {task!r} の argv policy が未知です: {spec.argv_policy!r}"
        )

    try:
        runner_separator = argv.index("--")
    except ValueError as exc:
        raise DispatchError("mutation args に runner separator -- がありません") from exc
    wrapper_argv = argv[:runner_separator]
    runner_argv = argv[runner_separator + 1:]
    runner_modes: list[str] = []
    for index, value in enumerate(wrapper_argv):
        option_name = value.split("=", 1)[0]
        if (
            option_name != "--runner-mode"
            and len(option_name) > 2
            and "--runner-mode".startswith(option_name)
        ):
            raise DispatchError("mutation --runner-mode の省略形は使えません")
        if value == "--runner-mode":
            if index + 1 >= len(wrapper_argv):
                raise DispatchError("mutation --runner-mode に値がありません")
            runner_modes.append(wrapper_argv[index + 1])
        elif value.startswith("--runner-mode="):
            runner_modes.append(value.split("=", 1)[1])
    if runner_modes != ["local"]:
        raise DispatchError("mutation task は --runner-mode local を 1 回要求します")
    if "--detached" not in wrapper_argv:
        raise DispatchError("mutation task は --detached を要求します")
    if len(runner_argv) < 2:
        raise DispatchError("mutation runner argv が不足しています")
    if Path(runner_argv[0]).resolve() != Path(sys.executable).resolve():
        raise DispatchError("mutation runner は dispatcher と同じ Python を要求します")
    runner_script = Path(runner_argv[1])
    if not runner_script.is_absolute():
        runner_script = _REPO_ROOT / runner_script
    if runner_script.resolve() != (_REPO_ROOT / "tools" / "run_tests.py").resolve():
        raise DispatchError("mutation runner は tools/run_tests.py を要求します")

    # argparse は nargs=0 の短 option 後を cluster として再解釈する。
    # pytest の selector/plugin/config option へ到達できる cluster だけを閉じる。
    cluster_prefix_flags = frozenset("lqsvx")
    forbidden_cluster_flags = frozenset("ckmop")
    for value in argv:
        if value.startswith("@"):
            raise DispatchError("mutation args に pytest @argfile は使えません")
        if "::" in value:
            raise DispatchError("mutation args に pytest nodeid selector は使えません")
        if value.startswith("-") and not value.startswith("--"):
            short_body = value[1:]
            for option in short_body:
                if option in forbidden_cluster_flags:
                    raise DispatchError(
                        f"mutation args に pytest -{option} option は使えません"
                    )
                if option not in cluster_prefix_flags:
                    break
        long_option = value.split("=", 1)[0]
        if value.startswith("--deselect") or (
            len(long_option) > 2 and "--deselect".startswith(long_option)
        ):
            raise DispatchError("mutation args に pytest --deselect は使えません")
        if value.startswith("--ignore") or (
            len(long_option) > 2 and "--ignore".startswith(long_option)
        ):
            raise DispatchError("mutation args に pytest --ignore* は使えません")
        if value.startswith("--override-ini") or (
            len(long_option) > 2 and "--override-ini".startswith(long_option)
        ):
            raise DispatchError("mutation args に pytest --override-ini は使えません")
        if value.startswith("--config-file") or (
            len(long_option) > 2 and "--config-file".startswith(long_option)
        ):
            raise DispatchError("mutation args に pytest --config-file は使えません")
        if value.startswith("--force-dispatch") or (
            len(long_option) > 2 and "--force-dispatch".startswith(long_option)
        ):
            raise DispatchError("mutation args に --force-dispatch は使えません")
        env_name = value.split("=", 1)[0]
        if env_name in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}:
            raise DispatchError(f"mutation args に {env_name} は使えません")


def _child_environment(spec: _TaskSpec) -> dict[str, str]:
    """request overlay 適用前の task 固有 base environment を作る。"""

    if spec.env_mode == "inherit":
        return os.environ.copy()
    if spec.env_mode == "clean":
        return {
            name: os.environ[name]
            for name in _CLEAN_CHILD_ENV_KEYS
            if name in os.environ
        }
    raise DispatchError(f"未知の env mode です: {spec.env_mode!r}")


def _is_regular_pbs_jobid(pbs_jobid: str) -> bool:
    """PBS が設定する request ID の既知の文字集合だけを受理する。"""

    if pbs_jobid == "unknown":
        return False
    try:
        normalized = _normalize_request_id(pbs_jobid)
    except DispatchError:
        return False
    return re.fullmatch(
        r"[0-9]+(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)+",
        normalized,
    ) is not None


def _is_legacy_unbound_job_envelope(request_path: Path, pbs_jobid: str) -> bool:
    """pre-binding job script の既存 submission envelope だけを grandfather する。"""

    if not _is_regular_pbs_jobid(pbs_jobid) or request_path.name != "request.json":
        return False
    script_path = request_path.parent / "dispatch.sh"
    probe_path = request_path.parent / "interpreter_probe.py"
    if (
        script_path.is_symlink()
        or not script_path.is_file()
        or probe_path.is_symlink()
        or not probe_path.is_file()
    ):
        return False
    try:
        script = script_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return (
        f"REQUEST={shlex.quote(str(request_path))}\n" in script
        and '--job-run "$REQUEST"' in script
        and _REQUEST_SHA256_ENV not in script
        and "REQUEST_SHA256=" not in script
    )


def _is_bound_job_envelope(
    request_path: Path,
    expected_request_sha256: str,
    pbs_jobid: str,
) -> bool:
    """現行 job script が request path と hash を保持することを検査する。"""

    if not _is_regular_pbs_jobid(pbs_jobid) or request_path.name != "request.json":
        return False
    script_path = request_path.parent / "dispatch.sh"
    probe_path = request_path.parent / "interpreter_probe.py"
    if (
        script_path.is_symlink()
        or not script_path.is_file()
        or probe_path.is_symlink()
        or not probe_path.is_file()
    ):
        return False
    try:
        script = script_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return (
        f"REQUEST={shlex.quote(str(request_path))}\n" in script
        and f"REQUEST_SHA256={shlex.quote(expected_request_sha256)}\n" in script
        and (
            f'export {_REQUEST_SHA256_ENV}="$REQUEST_SHA256"\n'
            in script
        )
        and 'exec "$selected" "$DISPATCHER" --job-run "$REQUEST"' in script
    )


def _job_run(
    request_path: Path,
    expected_request_sha256: Optional[str] = None,
) -> int:
    """計算ノード内でだけ呼ばれる child launcher。"""

    result_path = request_path.parent / "result.json"
    stage = "bootstrap"
    child_rc = INFRA_RC
    pbs_jobid = os.environ.get("PBS_JOBID", "unknown")
    interpreter = str(Path(sys.executable).resolve())
    hostname = ""
    request_sha256: Optional[str] = None
    runner_report: Optional[dict[str, Any]] = None
    bound_xdist_root: Optional[Path] = None
    guard_payload = {
        "schema_version": "pegasus-dispatch-result/v1",
        "stage": _RESULT_GUARD_STAGE,
        "child_rc": INFRA_RC,
        "pbs_jobid": pbs_jobid,
        "hostname": hostname,
        "interpreter": interpreter,
        "error": "result guard active",
        "request_sha256": request_sha256,
    }
    try:
        _write_json_x(result_path, guard_payload)
        _fsync_dir(result_path.parent)
    except Exception:
        _job_trace("job-return", rc=INFRA_RC, phase="guard-failed")
        return INFRA_RC
    isolation_failed = False
    try:
        if sys.version_info < (3, 10):
            raise DispatchError("interpreter version < 3.10")

        request, request_sha256 = _read_request_object_and_sha256(request_path)
        task, argv = _resolve_request(request)
        # 親 (_dispatch_impl) と独立に子でも閉集合照合する二層 fail-closed。
        if task not in TASKS:
            raise DispatchError(f"未知の task です: {task!r}")
        spec = TASKS[task]
        runner_binding = _validated_runner_binding(request, task=task)
        if expected_request_sha256 is None:
            # 旧 script は hash 引数を持たない。queue 内の v1/v2 を一方向 bump で
            # 殺さないため歴史的 2 task だけを grandfather するが、新規 request
            # marker と新規 task は無束縛の公開 --job-run から起動させない。
            if (
                request.get("request_binding") is not None
                or task not in _LEGACY_UNBOUND_TASKS
                or not _is_legacy_unbound_job_envelope(request_path, pbs_jobid)
            ):
                raise DispatchError("request SHA-256 束縛がありません")
        else:
            if re.fullmatch(r"[0-9a-f]{64}", expected_request_sha256) is None:
                raise DispatchError("request SHA-256 の形式が不正です")
            if request_sha256 != expected_request_sha256:
                raise DispatchError("request SHA-256 が job script と不一致です")
            if request.get("request_binding") != _REQUEST_BINDING:
                raise DispatchError("request binding が現行契約と不一致です")
            if not _is_bound_job_envelope(
                request_path,
                expected_request_sha256,
                pbs_jobid,
            ):
                raise DispatchError("bound job envelope または PBS_JOBID が不正です")
        _import_probe_modules(spec)
        if runner_binding is not None:
            bound_xdist_root = _resolve_xdist_distribution_root()

        repo_root = Path(request["repo_root"]).resolve()
        requested_env = request.get("environment", {})
        _validate_task_argv(task, spec, argv)
        if type(requested_env) is not dict or not all(
            type(key) is str and type(value) is str
            for key, value in requested_env.items()
        ):
            raise DispatchError("environment は string mapping でなければなりません")
        env_allowlist = (
            _LEGACY_V1_ENV_ALLOWLIST
            if request.get("schema_version") == _LEGACY_REQUEST_SCHEMA
            else spec.env_allowlist
        )
        unexpected_env = set(requested_env) - env_allowlist
        if unexpected_env:
            raise DispatchError(
                "environment に task allowlist 外 key があります: "
                + ", ".join(sorted(unexpected_env))
            )
        hostname = os.uname().nodename
        if re.fullmatch(r"bnode[0-9]+(?:\..*)?", hostname) is None:
            raise DispatchError(f"計算ノード hostname ではありません: {hostname}")
        os.chdir(repo_root)
        child_env = _child_environment(spec)
        child_env.update(requested_env)
        child_env.pop(_TASK_RUN_ENV, None)
        child_env.pop(_TASK_RUN_ROOT_ENV, None)
        child_env.pop(_REQUEST_SHA256_ENV, None)
        child_env.pop(_JOB_SESSION_SWEEP_ENV, None)
        for name in (_TASK_RUN_SIDECAR_ENV, _TASK_RUN_AUTO_RECORD_ENV):
            if name not in spec.env_allowlist:
                child_env.pop(name, None)
        executable_dir = str(Path(sys.executable).resolve().parent)
        child_env["PATH"] = executable_dir + os.pathsep + child_env.get("PATH", "")
        child_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
        if task == "mutation":
            assert request_sha256 is not None
            binding = mutation_attempt_marker.build_binding(
                dispatch_root=repo_root / "output" / "pegasus-dispatch",
                submission_dir=request_path.parent,
                pbs_jobid=pbs_jobid,
                hostname=hostname,
                request_sha256=request_sha256,
                is_regular_pbs_jobid=_is_regular_pbs_jobid,
            )
            child_env[mutation_attempt_marker.MARKER_ENV] = (
                mutation_attempt_marker.encode_binding(binding)
            )
        stage = "child"
        if runner_binding is not None:
            assert bound_xdist_root is not None
            child_rc, actual_digest = _run_bound_tests_child(
                repo_root,
                argv,
                child_env,
                runner_binding,
                bound_xdist_root,
                request_path.parent,
            )
            runner_report = _runner_binding_report(runner_binding, actual_digest)
        else:
            child_argv = (
                list(argv)
                if spec.argv_policy == "generic-v1"
                else [
                    sys.executable,
                    str(repo_root.joinpath(*spec.child_script)),
                    *argv,
                ]
            )
            child_rc = _run_isolated_child(
                child_argv,
                cwd=repo_root,
                env=child_env,
                submission_dir=request_path.parent,
            )
    except _ChildIsolationError:
        isolation_failed = True
        child_rc = INFRA_RC
    except Exception as exc:
        stage = stage if stage != "child" else "child-launch"
        error = f"{type(exc).__name__}: {exc}"
        child_rc = INFRA_RC
    else:
        error = None

    if stage in ("child", "child-launch"):
        _maybe_sweep_job_session(request_sha256)

    if isolation_failed:
        _job_trace("job-return", rc=INFRA_RC, phase="isolation-failed")
        return INFRA_RC

    payload = {
        "schema_version": "pegasus-dispatch-result/v1",
        "stage": stage,
        "child_rc": int(child_rc),
        "pbs_jobid": pbs_jobid,
        "hostname": hostname,
        "interpreter": interpreter,
        "error": error,
        "request_sha256": request_sha256,
    }
    if error is None and runner_report is not None:
        payload["runner_binding"] = runner_report
        assert bound_xdist_root is not None
        payload[_BOUND_XDIST_ROOT_RESULT_FIELD] = str(bound_xdist_root)
    try:
        _write_result_replace(result_path, payload)
    except Exception as exc:
        _job_trace("result-write-failed", error_type=type(exc).__name__)
        _job_trace("job-return", rc=INFRA_RC, phase="result-write-failed")
        return INFRA_RC
    _job_trace("job-return", rc=int(child_rc), phase="result-durable")
    return int(child_rc)


def _log_candidates(
    submission_dir: Path,
    *,
    stream: str,
    request_id: str,
) -> list[Path]:
    marker = ".o" if stream == "stdout" else ".e"
    raw = request_id.rstrip(".")
    normalized = _normalize_request_id(raw)
    forms = list(dict.fromkeys((
        normalized.split(".", 1)[0],
        normalized,
        raw.split(".", 1)[0],
        raw,
    )))
    stems = (_job_name(submission_dir.name), "dispatch.sh")
    return [
        submission_dir / f"{stem}{marker}{form}"
        for stem in stems
        for form in forms
        if form
    ]


def _find_log(
    submission_dir: Path,
    *,
    stream: str,
    request_id: str,
) -> Optional[Path]:
    found: list[Path] = []
    for path in _log_candidates(
        submission_dir, stream=stream, request_id=request_id,
    ):
        try:
            if path.is_file() and not path.is_symlink():
                resolved = path.resolve()
                if resolved not in found:
                    found.append(resolved)
        except OSError:
            continue
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        raise DispatchError(f"scheduler {stream} log が複数あります: {found}")
    return None


def _bounded_log(path: Path, *, limit: int) -> dict[str, Any]:
    if limit <= 0:
        raise ValueError("log limit は正でなければなりません")
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            omitted = max(0, size - limit)
            if omitted:
                handle.seek(omitted)
            raw = handle.read(limit)
    except OSError as exc:
        raise DispatchError(f"scheduler log を読めません: {path}: {exc}") from exc
    text = raw.decode("utf-8", errors="replace")
    if omitted:
        text = f"[先頭 {omitted} bytes を省略。末尾 {limit} bytes を収集]\\n" + text
    return {
        "path": str(path),
        "size": size,
        "omitted_bytes": omitted,
        "tail": text,
    }


def _utf8_tail(text: str, *, limit: int) -> str:
    """decode 済み text の末尾を UTF-8 byte 枠内の部分文字列にする。"""

    remaining = limit
    start = len(text)
    while start:
        width = len(text[start - 1].encode("utf-8"))
        if width > remaining:
            break
        remaining -= width
        start -= 1
    return text[start:]


def _prefix_relay_lines(text: str) -> str:
    """信頼できない child text の各行を dispatcher 行から識別可能にする。"""

    return "".join(f"| {line}" for line in text.splitlines(keepends=True))


def _redirect_broken_stream_to_devnull(stream: Any) -> None:
    """終了時 flush が同じ broken pipe で process rc を 120 に変えるのを防ぐ。"""

    devnull_fd: Optional[int] = None
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, stream.fileno())
    except _SignalAbort:
        raise
    except Exception:
        pass
    finally:
        if devnull_fd is not None:
            try:
                os.close(devnull_fd)
            except _SignalAbort:
                raise
            except Exception:
                pass


def _emit_relay_abort_notice(text: str, *, stream: Any) -> None:
    """relay 打ち切りを告知し、壊れた告知先も終了時 flush から外す。"""

    try:
        _emit(text, stream=stream)
    except BrokenPipeError:
        _redirect_broken_stream_to_devnull(stream)
    except _SignalAbort:
        raise
    except Exception:
        pass


def _relay_scheduler_logs(
    stdout_record: Optional[Mapping[str, Any]],
    stderr_record: Optional[Mapping[str, Any]],
    *,
    request_id: Optional[str],
    successful: bool,
) -> None:
    """収集済み scheduler log を元 stream へ best-effort で中継する。"""

    streams = (
        ("stdout", stdout_record, sys.stdout),
        ("stderr", stderr_record, sys.stderr),
    )
    displayed_request_id = (
        request_id
        if type(request_id) is str and re.fullmatch(r"\S+", request_id)
        else "unknown"
    )
    relay_limit = (
        DEFAULT_SUCCESS_RELAY_LIMIT_BYTES
        if successful
        else DEFAULT_FAILURE_RELAY_LIMIT_BYTES
    )
    for index, (label, record, stream) in enumerate(streams):
        try:
            if record is None:
                continue
            tail = record.get("tail")
            if type(tail) is not str or not tail:
                continue
            relayed_tail = _utf8_tail(tail, limit=relay_limit)
            relayed_size = len(relayed_tail.encode("utf-8"))
            source_size = record.get("size")
            source_omitted = record.get("omitted_bytes")
            truncated = (
                relayed_tail != tail
                or (type(source_omitted) is int and source_omitted > 0)
            )
            detail = ""
            if truncated and type(source_size) is int:
                omitted_bytes = max(
                    source_omitted if type(source_omitted) is int else 0,
                    source_size - relayed_size,
                )
                detail = (
                    f" (size={source_size} bytes, "
                    f"omitted_bytes={omitted_bytes})"
                )
            frame = (
                f"[Pegasus dispatch] request {displayed_request_id} "
                f"child {label}"
            )
            _emit(
                f"{frame} begin{detail}\n",
                stream=stream,
            )
            prefixed_tail = _prefix_relay_lines(relayed_tail)
            _emit(prefixed_tail, stream=stream)
            if not prefixed_tail.endswith("\n"):
                _emit("\n", stream=stream)
            _emit(
                f"{frame} end\n",
                stream=stream,
            )
        except BrokenPipeError:
            _redirect_broken_stream_to_devnull(stream)
            notice_stream = streams[1 - index][2]
            _emit_relay_abort_notice(
                f"[Pegasus dispatch] request {displayed_request_id} "
                f"child log relay aborted after broken pipe on {label}\n",
                stream=notice_stream,
            )
            break
        except _SignalAbort:
            raise
        except Exception:
            _emit_relay_abort_notice(
                f"[Pegasus dispatch] request {displayed_request_id} "
                f"child {label} relay aborted after relay error\n",
                stream=stream,
            )
            continue


def _accounting_present(
    stderr_record: Mapping[str, Any],
    request_id: str,
) -> bool:
    """NQSV 会計サマリを submit ID・policy account・必須 field の連言で束縛する。"""

    tail = stderr_record.get("tail")
    if type(tail) is not str:
        return False
    request_ids = _NQSV_REQUEST_ID_RE.findall(tail)
    if len(request_ids) != 1:
        return False
    if _NQSV_GROUP_NAME_RE.findall(tail) != [DEFAULT_PROJECT]:
        return False
    try:
        observed = _normalize_request_id(request_ids[0])
        expected = _normalize_request_id(request_id)
    except DispatchError:
        return False
    return (
        observed == expected
        and _NQSV_STARTED_RE.search(tail) is not None
        and _NQSV_ENDED_RE.search(tail) is not None
        and _NQSV_ELAPSE_RE.search(tail) is not None
    )


def _compute_marker_evidence(
    submission_dir: Path,
    request_id: str,
) -> tuple[bool, dict[str, Any]]:
    """計算ノードが共有 submission dir へ書いた marker を検証する。"""

    marker = submission_dir / _COMPUTE_MARKER_NAME
    try:
        payload = _read_json_object(marker)
        observed_id = payload.get("pbs_jobid")
        hostname = payload.get("hostname")
        valid = (
            payload.get("schema_version") == "pegasus-compute-visible/v1"
            and type(observed_id) is str
            and _normalize_request_id(observed_id)
            == _normalize_request_id(request_id)
            and type(hostname) is str
            and re.fullmatch(r"bnode[0-9]+(?:\..*)?", hostname) is not None
        )
        return valid, {
            "path": str(marker),
            "present": True,
            "valid": valid,
            "pbs_jobid": observed_id,
            "hostname": hostname,
        }
    except (DispatchError, OSError) as exc:
        try:
            present = marker.is_file() and not marker.is_symlink()
        except OSError:
            present = False
        return False, {
            "path": str(marker),
            "present": present,
            "valid": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _discover_request_id(
    run_command: CommandRunner,
    *,
    job_name: str,
    submission_dir: Path,
    environ: Mapping[str, str],
) -> tuple[Optional[str], dict[str, Any]]:
    """qsub 応答解析不能時に、一意な job name から request ID を回収する。"""

    try:
        result = _run(
            run_command,
            ["qstat", "-f"],
            cwd=submission_dir,
            environ=environ,
        )
    except BaseException as exc:
        return None, {
            "attempted": True,
            "job_name": job_name,
            "submission_dir": str(submission_dir),
            "exception": f"{type(exc).__name__}: {exc}",
        }
    record = {
        "attempted": True,
        "job_name": job_name,
        "submission_dir": str(submission_dir),
        **_capture(result),
    }
    if result.returncode != 0:
        return None, record

    text = result.stdout or ""
    id_matches = list(_QSTAT_REQUEST_ID_RE.finditer(text))
    candidates: list[tuple[str, str]] = []
    for index, match in enumerate(id_matches):
        end = id_matches[index + 1].start() if index + 1 < len(id_matches) else len(text)
        block = text[match.start():end]
        names = _QSTAT_REQUEST_NAME_RE.findall(block)
        name_matched = names == [job_name]
        submission_dir_matched = str(submission_dir) in block
        if name_matched or submission_dir_matched:
            matched_by = "+".join(
                label for label, matched in (
                    ("request-name", name_matched),
                    ("submission-dir", submission_dir_matched),
                )
                if matched
            )
            candidates.append((match.group(1).rstrip("."), matched_by))
    unique = sorted({candidate for candidate, _ in candidates})
    record["candidates"] = unique
    if len(unique) == 1:
        record["matched_by"] = "+".join(sorted({
            matched_by
            for candidate, matched_by in candidates
            if candidate == unique[0]
        }))
        return unique[0], record
    return None, record


def _latch_submission_disabled(
    output_root: Path,
    *,
    reason: str,
    submission_dir: Path,
    request_id: Optional[str],
    lock_fd: Optional[int] = None,
) -> Path:
    owned_lock = None
    try:
        if lock_fd is None:
            owned_lock = _acquire_control_lock(output_root)
        path = output_root / "submission-disabled.json"
        payload = {
            "schema_version": "pegasus-submission-disabled/v1",
            "reason": reason,
            "submission_dir": str(submission_dir),
            "request_id": request_id,
            "recovery": "ユーザー自身の端末から qsub し、有効性を確認してください",
        }
        try:
            _write_json_x(path, payload)
        except FileExistsError:
            pass
        return path
    finally:
        if owned_lock is not None:
            _release_control_lock(owned_lock)


def _acquire_control_lock(output_root: Path) -> int:
    output_root.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        output_root / _CONTROL_LOCK_NAME,
        os.O_RDWR | os.O_CREAT,
        0o600,
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _release_control_lock(descriptor: int) -> None:
    try:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _orphan_hold_path(output_root: Path) -> Path:
    return output_root / _ORPHAN_HOLD_NAME


def _orphan_hold_request_path(
    output_root: Path,
    *,
    request_id: Optional[str],
    job_name: str,
    submission_dir: Path,
) -> Path:
    leaf: Optional[str] = None
    if request_id is not None:
        try:
            candidate = _normalize_request_id(request_id)
        except DispatchError:
            candidate = ""
        if _GATE_REQUEST_ID_RE.fullmatch(candidate) is not None:
            leaf = candidate
    if leaf is None:
        material = f"{job_name}\0{submission_dir}".encode("utf-8", errors="strict")
        leaf = "unknown-" + hashlib.sha256(material).hexdigest()[:24]
    return output_root / _ORPHAN_HOLD_DIR_NAME / f"{leaf}.json"


def _orphan_hold_present(output_root: Path) -> bool:
    """request 別 hold または互換 marker の判定不能も成立側へ倒す。"""

    path = _orphan_hold_path(output_root)
    try:
        os.lstat(path)
    except FileNotFoundError:
        pass
    except OSError:
        return True
    else:
        return True
    directory = output_root / _ORPHAN_HOLD_DIR_NAME
    try:
        with os.scandir(directory) as entries:
            return any(True for _entry in entries)
    except FileNotFoundError:
        return False
    except OSError:
        return True


def _orphan_hold_required(qdel: Mapping[str, Any]) -> bool:
    """既存 receipt field だけから保守的な hold 署名を判定する。"""

    return qdel.get("job_may_remain") is True


def _orphan_hold_payload(
    *,
    qdel: Mapping[str, Any],
    submission_dir: Path,
    request_id: Optional[str],
    job_name: str,
    phase: Optional[str] = None,
) -> dict[str, Any]:
    gate = qdel.get("gate")
    gate_reason = gate.get("reason") if isinstance(gate, Mapping) else None
    returncode = qdel.get("returncode")
    exception = qdel.get("exception")
    payload: dict[str, Any] = {
        "schema_version": _ORPHAN_HOLD_SCHEMA,
        "reason": "job-may-remain-without-terminal-evidence",
        "submission_dir": str(submission_dir),
        "request_id": request_id,
        "job_name": job_name,
        "qdel": {
            "job_may_remain": True,
            "attempted": qdel.get("attempted") is True,
            "returncode": returncode if type(returncode) is int else None,
            "exception": exception if type(exception) is str else None,
            "gate": {"reason": gate_reason if type(gate_reason) is str else None},
        },
        "recovery": {
            "request-visible-active": (
                "request_id を qstat で確認し、終端まで待つかユーザー自身が手動で対処する"
            ),
            "request-absent-or-terminal": (
                "qstat で対象の不在または終端を確認してから dirty source を復元する"
            ),
            "qstat-unavailable": (
                "scheduler を確認できるまで source と worktree と hold を保全する"
            ),
            "manual-qdel-warning": (
                "手動 qdel は F47 の submission-disabled.json を武装させ、"
                "その解除もユーザー手番になる"
            ),
            "final-step": "source の clean/HEAD を確認した後だけ hold を手動削除する",
        },
    }
    if phase is not None:
        payload["phase"] = phase
    return payload


def _orphan_hold_error_record(exc: _OrphanHoldError) -> dict[str, Any]:
    return {
        "reason": exc.reason,
        "operation": exc.operation,
        "path": str(exc.path),
        "detail": exc.detail,
    }


def _orphan_hold_error(
    reason: str,
    *,
    operation: str,
    path: Path,
    exc: BaseException,
) -> _OrphanHoldError:
    return _OrphanHoldError(
        reason,
        operation=operation,
        path=path,
        detail=f"{type(exc).__name__}: {exc}",
    )


def _orphan_hold_is_owned(
    payload: Mapping[str, Any],
    *,
    submission_dir: Path,
    job_name: str,
) -> bool:
    return (
        payload.get("submission_dir") == str(submission_dir)
        and payload.get("job_name") == job_name
    )


def _read_orphan_hold_optional(path: Path) -> Optional[dict[str, Any]]:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return None
    return _read_json_object(path)


def _arm_pending_orphan_hold(
    output_root: Path,
    *,
    submission_dir: Path,
    job_name: str,
    lock_fd: Optional[int] = None,
) -> Path:
    """qsub 直前に request 別 ledger と互換 marker を durable 化する。"""

    path = _orphan_hold_request_path(
        output_root,
        request_id=None,
        job_name=job_name,
        submission_dir=submission_dir,
    )
    compatibility_path = _orphan_hold_path(output_root)
    payload = _orphan_hold_payload(
        qdel={
            "attempted": False,
            "job_may_remain": True,
            "gate": {"reason": "pending-qsub"},
        },
        submission_dir=submission_dir,
        request_id=None,
        job_name=job_name,
        phase="pending-qsub",
    )
    owned_lock = None
    try:
        if lock_fd is None:
            owned_lock = _acquire_control_lock(output_root)
        _write_json_atomic_replace(
            compatibility_path,
            payload,
            create_only=True,
        )
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _write_json_atomic_replace(path, payload, create_only=True)
        _fsync_dir(path.parent)
        _fsync_dir(output_root)
    except _SignalAbort:
        raise
    except BaseException as exc:
        if isinstance(exc, _OrphanHoldError):
            raise
        error = _orphan_hold_error(
            "orphan-hold-write-failed",
            operation="create",
            path=path,
            exc=exc,
        )
        raise error from exc
    finally:
        if owned_lock is not None:
            _release_control_lock(owned_lock)
    print(
        f"Pegasus pending orphan hold を create-only で保存しました: {path}",
        file=sys.stderr,
        flush=True,
    )
    return path


def _promote_pending_orphan_hold(
    output_root: Path,
    *,
    qdel: Mapping[str, Any],
    submission_dir: Path,
    request_id: Optional[str],
    job_name: str,
    lock_fd: Optional[int] = None,
) -> Path:
    """自分の pending ledger だけを request 別 final hold へ昇格する。"""

    pending_path = _orphan_hold_request_path(
        output_root,
        request_id=None,
        job_name=job_name,
        submission_dir=submission_dir,
    )
    final_path = _orphan_hold_request_path(
        output_root,
        request_id=request_id,
        job_name=job_name,
        submission_dir=submission_dir,
    )
    compatibility_path = _orphan_hold_path(output_root)
    final_payload = _orphan_hold_payload(
        qdel=qdel,
        submission_dir=submission_dir,
        request_id=request_id,
        job_name=job_name,
    )
    owned_lock = None
    try:
        if lock_fd is None:
            owned_lock = _acquire_control_lock(output_root)
        pending = _read_json_object(pending_path)
        if pending.get("phase") not in {None, "pending-qsub"}:
            raise ValueError("hold phase is not promotable")
        if not _orphan_hold_is_owned(
            pending,
            submission_dir=submission_dir,
            job_name=job_name,
        ):
            raise ValueError("pending hold ownership mismatch")

        if final_path == pending_path:
            _write_json_atomic_replace(final_path, final_payload)
        else:
            try:
                _write_json_atomic_replace(
                    final_path,
                    final_payload,
                    create_only=True,
                )
            except FileExistsError:
                existing_final = _read_json_object(final_path)
                if not _orphan_hold_is_owned(
                    existing_final,
                    submission_dir=submission_dir,
                    job_name=job_name,
                ):
                    raise ValueError("request hold ownership mismatch")

        compatibility = _read_json_object(compatibility_path)
        if _orphan_hold_is_owned(
            compatibility,
            submission_dir=submission_dir,
            job_name=job_name,
        ):
            if compatibility.get("phase") not in {None, "pending-qsub"}:
                raise ValueError("compatibility hold phase is not promotable")
            _write_json_atomic_replace(compatibility_path, final_payload)
        if final_path != pending_path:
            pending_path.unlink()
            _fsync_dir(pending_path.parent)
        _fsync_dir(output_root)
    except _SignalAbort:
        raise
    except BaseException as exc:
        if isinstance(exc, _OrphanHoldError):
            raise
        error = _orphan_hold_error(
            "orphan-hold-promote-failed",
            operation="promote",
            path=pending_path,
            exc=exc,
        )
        raise error from exc
    finally:
        if owned_lock is not None:
            _release_control_lock(owned_lock)
    print(
        f"Pegasus orphan hold を pending から昇格しました: {final_path}",
        file=sys.stderr,
        flush=True,
    )
    return final_path


def _release_pending_orphan_hold(
    output_root: Path,
    *,
    submission_dir: Path,
    job_name: str,
    request_id: Optional[str] = None,
    expect_phase: Optional[str] = "pending-qsub",
    require_present: bool = True,
    lock_fd: Optional[int] = None,
) -> Optional[Path]:
    """終端証拠を得た request 所有の hold だけを durable に削除する。"""

    pending_path = _orphan_hold_request_path(
        output_root,
        request_id=None,
        job_name=job_name,
        submission_dir=submission_dir,
    )
    candidates = [pending_path]
    if request_id is not None:
        final_path = _orphan_hold_request_path(
            output_root,
            request_id=request_id,
            job_name=job_name,
            submission_dir=submission_dir,
        )
        if final_path != pending_path:
            candidates.append(final_path)
    compatibility_path = _orphan_hold_path(output_root)
    owned_lock = None
    owned_payloads: list[tuple[Path, dict[str, Any]]] = []
    compatibility: Optional[dict[str, Any]] = None
    compatibility_owned = False
    release_started = False

    def restore_release_state() -> None:
        """途中失敗前の blocking state を control lock 内で durable に戻す。"""

        failures: list[BaseException] = []
        blocking_restored = compatibility is not None and not compatibility_owned
        restoration_payload: Optional[dict[str, Any]] = None
        if compatibility_owned and compatibility is not None:
            restoration_payload = compatibility
        elif compatibility is None and owned_payloads:
            restoration_payload = owned_payloads[0][1]
        if restoration_payload is not None:
            # aggregate を最初に戻し、ledger directory の再作成中にも consumer から
            # blocking marker が消えないようにする。
            try:
                _write_json_atomic_replace(
                    compatibility_path,
                    restoration_payload,
                )
                blocking_restored = True
            except _SignalAbort:
                raise
            except BaseException as exc:
                failures.append(exc)
        if owned_payloads:
            ledger_published = False
            try:
                pending_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                for path, payload in owned_payloads:
                    try:
                        _write_json_atomic_replace(path, payload)
                        ledger_published = True
                    except _SignalAbort:
                        raise
                    except BaseException as exc:
                        failures.append(exc)
                _fsync_dir(pending_path.parent)
                _fsync_dir(output_root)
                blocking_restored = blocking_restored or ledger_published
            except _SignalAbort:
                raise
            except BaseException as exc:
                failures.append(exc)
        elif blocking_restored:
            try:
                _fsync_dir(output_root)
            except _SignalAbort:
                raise
            except BaseException as exc:
                failures.append(exc)
        if not blocking_restored:
            if failures:
                raise failures[0]
            raise OSError("release rollback did not restore a blocking marker")

    try:
        if lock_fd is None:
            owned_lock = _acquire_control_lock(output_root)
        for path in candidates:
            payload = _read_orphan_hold_optional(path)
            if payload is None:
                continue
            if not _orphan_hold_is_owned(
                payload,
                submission_dir=submission_dir,
                job_name=job_name,
            ):
                raise ValueError(f"hold ownership mismatch: {path.name}")
            if expect_phase is not None and payload.get("phase") != expect_phase:
                raise ValueError(f"hold phase mismatch: {path.name}")
            owned_payloads.append((path, payload))

        compatibility = _read_orphan_hold_optional(compatibility_path)
        if compatibility is not None and _orphan_hold_is_owned(
            compatibility,
            submission_dir=submission_dir,
            job_name=job_name,
        ):
            if (
                expect_phase is not None
                and compatibility.get("phase") != expect_phase
            ):
                raise ValueError("compatibility hold phase mismatch")
            compatibility_owned = True

        if not owned_payloads and not compatibility_owned:
            if require_present:
                raise FileNotFoundError(pending_path)
            return None
        if require_present and not compatibility_owned:
            raise ValueError("compatibility hold ownership mismatch")
        replacement_payload: Optional[dict[str, Any]] = None
        if compatibility_owned:
            excluded = {path for path, _payload in owned_payloads}
            for other_path in sorted(pending_path.parent.glob("*.json")):
                if other_path not in excluded:
                    replacement_payload = _read_json_object(other_path)
                    break
        for path, _payload in owned_payloads:
            release_started = True
            path.unlink()
        if owned_payloads:
            _fsync_dir(pending_path.parent)
            with os.scandir(pending_path.parent) as entries:
                ledger_empty = not any(True for _entry in entries)
            if ledger_empty:
                pending_path.parent.rmdir()
                _fsync_dir(output_root)
        if compatibility_owned:
            if replacement_payload is None:
                release_started = True
                compatibility_path.unlink()
            else:
                release_started = True
                _write_json_atomic_replace(
                    compatibility_path,
                    replacement_payload,
                )
            _fsync_dir(output_root)
        _fsync_dir(output_root)
    except BaseException as exc:
        restoration_error: Optional[BaseException] = None
        if release_started:
            try:
                restore_release_state()
            except BaseException as rollback_exc:
                restoration_error = rollback_exc
        if isinstance(restoration_error, _SignalAbort):
            raise restoration_error from exc
        if isinstance(exc, _SignalAbort):
            raise
        if isinstance(exc, _OrphanHoldError):
            raise
        error = _orphan_hold_error(
            "orphan-hold-release-failed",
            operation="release",
            path=pending_path,
            exc=exc,
        )
        if restoration_error is not None:
            error.detail += (
                "; release rollback failed: "
                f"{type(restoration_error).__name__}: {restoration_error}"
            )
        raise error from exc
    finally:
        if owned_lock is not None:
            _release_control_lock(owned_lock)
    print(
        f"Pegasus orphan hold を削除しました: {pending_path}",
        file=sys.stderr,
        flush=True,
    )
    return pending_path


def _latch_orphan_hold(
    output_root: Path,
    *,
    qdel: dict[str, Any],
    submission_dir: Path,
    request_id: Optional[str],
    job_name: str,
    lock_fd: Optional[int] = None,
) -> Optional[Path]:
    """job が残り得る証拠を request 別 ledger と互換 marker に保存する。"""

    if not _orphan_hold_required(qdel):
        return None
    path = _orphan_hold_request_path(
        output_root,
        request_id=request_id,
        job_name=job_name,
        submission_dir=submission_dir,
    )
    compatibility_path = _orphan_hold_path(output_root)
    payload = _orphan_hold_payload(
        qdel=qdel,
        submission_dir=submission_dir,
        request_id=request_id,
        job_name=job_name,
    )
    owned_lock = None
    try:
        if lock_fd is None:
            owned_lock = _acquire_control_lock(output_root)
        pending_path = _orphan_hold_request_path(
            output_root,
            request_id=None,
            job_name=job_name,
            submission_dir=submission_dir,
        )
        pending = _read_orphan_hold_optional(pending_path)
        if pending is not None:
            promoted = _promote_pending_orphan_hold(
                output_root,
                qdel=qdel,
                submission_dir=submission_dir,
                request_id=request_id,
                job_name=job_name,
                lock_fd=lock_fd if lock_fd is not None else owned_lock,
            )
            qdel["hold_promoted"] = True
            return promoted
        try:
            _write_json_atomic_replace(
                compatibility_path,
                payload,
                create_only=True,
            )
        except FileExistsError:
            pass
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            _write_json_atomic_replace(path, payload, create_only=True)
        except FileExistsError:
            existing = _read_json_object(path)
            if not _orphan_hold_is_owned(
                existing,
                submission_dir=submission_dir,
                job_name=job_name,
            ):
                raise ValueError("request hold ownership mismatch")
        _fsync_dir(path.parent)
        _fsync_dir(output_root)
    except _SignalAbort:
        raise
    except BaseException as exc:
        if isinstance(exc, _OrphanHoldError):
            error = exc
        else:
            error = _orphan_hold_error(
                "orphan-hold-write-failed",
                operation="create",
                path=path,
                exc=exc,
            )
        qdel["hold_error"] = error.detail
        print(
            f"Pegasus orphan hold を {path} へ保存できませんでした: {error.detail}",
            file=sys.stderr,
            flush=True,
        )
        if error is exc:
            raise
        raise error from exc
    finally:
        if owned_lock is not None:
            _release_control_lock(owned_lock)
    print(
        f"Pegasus orphan hold を create-only で保存しました: {path}",
        file=sys.stderr,
        flush=True,
    )
    # 既存 consumer はこの aggregate marker を表示用 path として使う。
    # request の完全な台帳は orphan-holds/ 以下であり、二本目以降も失わない。
    return compatibility_path


def _print_terminal_handoff(latch: Path, reason: str) -> None:
    print(
        f"Pegasus 自動投入を停止しました ({reason})。"
        f"ラッチ: {latch}。ユーザー自身の端末から qsub し、"
        "出力の永続・qstat 可視性・終了後会計を確認してください。",
        file=sys.stderr,
        flush=True,
    )


def _best_effort_qdel(
    run_command: CommandRunner,
    *,
    request_id: str,
    cwd: Path,
    environ: Mapping[str, str],
    record: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """qdel 起動を要求し、その成否を改変せず返す低水準 primitive。"""

    normalized = _normalize_request_id(request_id)
    qdel = {} if record is None else record
    qdel.update({"attempted": True, "request_id": normalized})
    try:
        result = _run(
            run_command,
            ["qdel", normalized],
            cwd=cwd,
            environ=environ,
        )
    except BaseException as exc:
        qdel["exception"] = f"{type(exc).__name__}: {exc}"
        qdel["job_may_remain"] = True
        if isinstance(exc, _SignalAbort):
            raise
        return qdel
    try:
        captured = _capture(result)
    except BaseException:
        # qdel は既に戻っている。非同期例外を再送出する前に最初の結果を固定する。
        qdel.update({
            "returncode": int(result.returncode),
            "stdout": (result.stdout or "")[-65536:],
            "stderr": (result.stderr or "")[-65536:],
            "job_may_remain": True,
        })
        raise
    qdel.update(captured)
    qdel["job_may_remain"] = result.returncode != 0
    return qdel


def _fresh_qstat_gated_qdel(
    run_command: CommandRunner,
    *,
    request_id: Optional[str],
    cwd: Path,
    environ: Mapping[str, str],
    qstat_attempts: int = DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS,
    cleanup_budget_s: float = DEFAULT_CLEANUP_BUDGET_S,
    retry_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    terminal_history_end: bool = False,
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
    job_name: Optional[str] = None,
    submission_dir: Optional[Path] = None,
    record: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """直前 snapshot が取消可能だったときだけ qdel 起動を要求する。

    qstat と qdel は別 scheduler command であり atomic ではない。したがって保証は
    fresh snapshot が QUE/HLD だったことまでで、qdel 時点まで RUN へ遷移しない
    ことは保証しない。対象 request に束縛された fresh END は qdel 不要の終端証拠
    とする。既存 terminal history との矛盾は、その後の fresh snapshot
    が QUE/HLD に戻った場合だけ閉じる。

    qstat/parse の判定例外境界を qdel primitive と分離する。qdel の結果を得た後は
    cleanup 時刻の再取得を含む gate 側の例外でその結果を上書きしない。
    ``attempted`` は qdel command の起動を要求したことを表す。
    """

    qdel = {} if record is None else record
    gate: dict[str, Any] = {
        "qstat": {"attempted": False},
        "qstat_attempts": [],
        "classification": None,
        "request_present": None,
        "scheduler_state": "UNKNOWN",
        "allowed": False,
        "reason": "gate-not-evaluated",
    }
    qdel.update({
        "attempted": False,
        "cleanup_policy": _QDEL_CLEANUP_POLICY,
        "job_may_remain": True,
        "gate": gate,
    })
    if request_id is None:
        # request ID discovery 失敗は cleanup clock を読む前に確定できる。
        # 注入 clock / host clock の初回取得が失敗する場合も、旧診断と metadata を保つ。
        gate["reason"] = "request-id-unavailable"
        qdel.update({
            "cleanup_elapsed_s": 0.0,
            "reason": "qsub accepted but request ID discovery failed",
        })
        if job_name is not None:
            qdel["job_name"] = job_name
        if submission_dir is not None:
            qdel["submission_dir"] = str(submission_dir)
        return qdel
    cleanup_started = 0.0
    last_elapsed = 0.0
    try:
        cleanup_started = clock()
    except BaseException as exc:
        gate["reason"] = "gate-exception"
        gate["exception"] = f"{type(exc).__name__}: {exc}"
        qdel.update({
            "attempted": False,
            "cleanup_policy": _QDEL_CLEANUP_POLICY,
            "cleanup_elapsed_s": None,
            "cleanup_elapsed_exception": gate["exception"],
            "job_may_remain": True,
            "reason": "fresh-qstat-gate-denied",
            "gate": gate,
        })
        return qdel

    def elapsed() -> float:
        nonlocal last_elapsed
        last_elapsed = max(last_elapsed, max(0.0, clock() - cleanup_started))
        return last_elapsed

    def denied(reason: str, *, normalized: Optional[str] = None) -> dict[str, Any]:
        gate["reason"] = reason
        cleanup_elapsed: Optional[float]
        cleanup_elapsed_exception: Optional[str] = None
        try:
            cleanup_elapsed = elapsed()
        except BaseException as exc:
            cleanup_elapsed = None
            cleanup_elapsed_exception = f"{type(exc).__name__}: {exc}"
            gate["reason"] = "gate-exception"
            gate["exception"] = cleanup_elapsed_exception
        job_may_remain = not (
            reason == "request-absent"
            and terminal_history_end is True
            and cleanup_elapsed_exception is None
        )
        qdel.update({
            "attempted": False,
            "cleanup_policy": _QDEL_CLEANUP_POLICY,
            "cleanup_elapsed_s": cleanup_elapsed,
            "job_may_remain": job_may_remain,
            "reason": (
                "qsub accepted but request ID discovery failed"
                if reason == "request-id-unavailable"
                else "fresh-qstat-gate-denied"
            ),
            "gate": gate,
        })
        if cleanup_elapsed_exception is not None:
            qdel["cleanup_elapsed_exception"] = cleanup_elapsed_exception
        if normalized is not None:
            qdel["request_id"] = normalized
        if job_name is not None:
            qdel["job_name"] = job_name
        if submission_dir is not None:
            qdel["submission_dir"] = str(submission_dir)
        return qdel

    normalized: Optional[str] = None
    try:
        normalized = _normalize_request_id(request_id)
        if _GATE_REQUEST_ID_RE.fullmatch(normalized) is None:
            return denied("malformed-request-id", normalized=normalized)
        if qstat_attempts <= 0:
            return denied("qstat-attempt-limit-invalid", normalized=normalized)

        for attempt in range(1, qstat_attempts + 1):
            if elapsed() >= cleanup_budget_s:
                return denied("cleanup-budget-exhausted", normalized=normalized)
            try:
                result = _run(
                    run_command,
                    ["qstat", "-f", normalized],
                    cwd=cwd,
                    environ=environ,
                )
            except _SignalAbort:
                raise
            except BaseException as exc:
                gate["qstat"] = {
                    "attempted": True,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
                gate["qstat_attempts"].append({
                    "attempt": attempt,
                    **gate["qstat"],
                })
                return denied("qstat-exception", normalized=normalized)

            classification = _classify_qstat_response(result, normalized)
            qstat_record = {
                "attempted": True,
                "attempt": attempt,
                "classification": classification,
                **_capture(result),
            }
            gate["qstat"] = dict(qstat_record)
            gate["qstat_attempts"].append(qstat_record)
            gate["classification"] = classification
            if elapsed() >= cleanup_budget_s:
                return denied("cleanup-budget-exhausted", normalized=normalized)
            if classification == "transient":
                if attempt == qstat_attempts:
                    return denied(
                        "qstat-transient-retries-exhausted",
                        normalized=normalized,
                    )
                if elapsed() >= cleanup_budget_s:
                    return denied("cleanup-budget-exhausted", normalized=normalized)
                remaining_budget = max(0.0, cleanup_budget_s - elapsed())
                sleep(min(retry_interval_s, remaining_budget))
                continue
            if classification == "permission":
                return denied("qstat-permission", normalized=normalized)
            if classification == "success-request-absent":
                response = result.stdout or ""
                if (
                    _QSTAT_REQUEST_ID_RE.search(response) is not None
                    or _GATE_STATE_FIELD_RE.search(response) is not None
                ):
                    # target ID を含まない ID/state field は absent の
                    # 証拠ではない。wrong/no-ID の END も terminal
                    # history で救済せず target binding 不能として閉じる。
                    gate["request_present"] = None
                    return denied(
                        "target-binding-ambiguous",
                        normalized=normalized,
                    )
                gate["request_present"] = False
                return denied("request-absent", normalized=normalized)

            gate["request_present"] = True
            state = _target_bound_qstat_state(result.stdout or "", normalized)
            gate["scheduler_state"] = state or "UNKNOWN"
            if state == "END":
                terminal = denied(
                    "state-not-cancellable",
                    normalized=normalized,
                )
                if "cleanup_elapsed_exception" not in terminal:
                    gate["terminal_evidence"] = "target-bound-end-before-qdel"
                    terminal["job_may_remain"] = False
                return terminal
            if state not in {"QUE", "HLD"}:
                return denied(
                    "target-state-unknown"
                    if state is None else "state-not-cancellable",
                    normalized=normalized,
                )
            if terminal_history_end:
                return denied("terminal-history-conflict", normalized=normalized)
            gate["allowed"] = True
            gate["reason"] = "fresh-cancellable-snapshot"
            break
    except _SignalAbort:
        raise
    except BaseException as exc:
        gate["reason"] = "gate-exception"
        gate["exception"] = f"{type(exc).__name__}: {exc}"
        return denied("gate-exception", normalized=normalized)

    # qdel 起動要求より前に receipt と同じ mutable record へ claim を固定する。
    # 以後の非同期例外でも caller はこの record を失わない。
    try:
        pre_qdel_elapsed = elapsed()
    except BaseException as exc:
        gate["reason"] = "gate-exception"
        gate["exception"] = f"{type(exc).__name__}: {exc}"
        return denied("gate-exception", normalized=normalized)
    qdel.update({
        "attempted": False,
        "request_id": normalized,
        "cleanup_policy": _QDEL_CLEANUP_POLICY,
        "cleanup_elapsed_s": pre_qdel_elapsed,
        "gate": gate,
        "job_may_remain": True,
    })
    _best_effort_qdel(
        run_command,
        request_id=normalized,
        cwd=cwd,
        environ=environ,
        record=qdel,
    )
    if "exception" in qdel or qdel.get("returncode") != 0:
        qdel["job_may_remain"] = True
        try:
            qdel["cleanup_elapsed_s"] = elapsed()
        except BaseException as exc:
            qdel["cleanup_elapsed_s"] = None
            qdel["cleanup_elapsed_exception"] = f"{type(exc).__name__}: {exc}"
        return qdel

    post_qstat_attempts: list[dict[str, Any]] = []
    qdel["post_qstat_attempts"] = post_qstat_attempts
    post_terminal = False
    post_reason = "post-qstat-not-evaluated"

    def post_retry(attempt: int) -> bool:
        nonlocal post_reason
        if attempt >= qstat_attempts:
            qdel["post_qstat_hard_cap_exhausted"] = True
            return False
        try:
            remaining_budget = max(0.0, cleanup_budget_s - elapsed())
        except BaseException as exc:
            post_reason = "post-qstat-clock-exception"
            qdel["cleanup_elapsed_s"] = None
            qdel["cleanup_elapsed_exception"] = (
                f"{type(exc).__name__}: {exc}"
            )
            return False
        if remaining_budget <= 0:
            post_reason = "post-qstat-budget-exhausted"
            return False
        try:
            sleep(min(max(0.0, retry_interval_s), remaining_budget))
        except _SignalAbort:
            raise
        except BaseException as exc:
            post_reason = "post-qstat-sleep-exception"
            qdel["post_qstat_exception"] = f"{type(exc).__name__}: {exc}"
            return False
        return True

    try:
        for attempt in range(1, qstat_attempts + 1):
            try:
                if elapsed() >= cleanup_budget_s:
                    post_reason = "post-qstat-budget-exhausted"
                    break
            except BaseException as exc:
                post_reason = "post-qstat-clock-exception"
                qdel["cleanup_elapsed_s"] = None
                qdel["cleanup_elapsed_exception"] = (
                    f"{type(exc).__name__}: {exc}"
                )
                break
            try:
                result = _run(
                    run_command,
                    ["qstat", "-f", normalized],
                    cwd=cwd,
                    environ=environ,
                )
                classification = _classify_qstat_response(result, normalized)
                post_record = {
                    "attempted": True,
                    "attempt": attempt,
                    "classification": classification,
                    **_capture(result),
                }
            except _SignalAbort:
                raise
            except BaseException as exc:
                post_record = {
                    "attempted": True,
                    "attempt": attempt,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
                post_qstat_attempts.append(post_record)
                qdel["post_qstat"] = post_record
                post_reason = "post-qstat-exception"
                break
            post_qstat_attempts.append(post_record)
            qdel["post_qstat"] = post_record

            try:
                if elapsed() >= cleanup_budget_s:
                    post_reason = "post-qstat-budget-exhausted"
                    break
            except BaseException as exc:
                post_reason = "post-qstat-clock-exception"
                qdel["cleanup_elapsed_s"] = None
                qdel["cleanup_elapsed_exception"] = (
                    f"{type(exc).__name__}: {exc}"
                )
                break
            if classification == "permission":
                post_reason = "post-qstat-permission"
                break
            if classification == "transient":
                post_reason = "post-qstat-transient-retries-exhausted"
                if post_retry(attempt):
                    continue
                break
            if classification == "success-request-absent":
                post_record["request_present"] = False
                # qdel rc=0 は取消要求の受理にすぎず、対象 request の独立した
                # 終端証拠ではないため absent 単体では hold を解除しない。
                post_reason = "post-qstat-request-absent-unconfirmed"
                if post_retry(attempt):
                    continue
                break

            post_record["request_present"] = True
            state = _target_bound_qstat_state(result.stdout or "", normalized)
            post_record["scheduler_state"] = state or "UNKNOWN"
            if state == "END":
                post_terminal = True
                post_reason = "target-end-after-qdel"
                break
            post_reason = (
                "post-qstat-target-state-unknown"
                if state is None else "post-qstat-nonterminal"
            )
            if post_retry(attempt):
                continue
            break
    except _SignalAbort:
        raise
    except BaseException as exc:
        post_reason = "post-qstat-exception"
        qdel["post_qstat_exception"] = f"{type(exc).__name__}: {exc}"

    qdel["post_qstat_reason"] = post_reason
    qdel["job_may_remain"] = not post_terminal
    try:
        qdel["cleanup_elapsed_s"] = elapsed()
    except BaseException as exc:
        qdel["cleanup_elapsed_s"] = None
        qdel["cleanup_elapsed_exception"] = f"{type(exc).__name__}: {exc}"
        qdel["job_may_remain"] = True
    return qdel


def recover_dispatch_intents(
    registry_root: Path,
    control_root: Path,
    *,
    deadline_at: float,
    run_command: CommandRunner = subprocess.run,
    environ: Optional[Mapping[str, str]] = None,
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
) -> tuple[dict[str, Any], ...]:
    """異常死した shard worker の未処理 intent を deadline 内で回収する。"""

    registry = Path(registry_root).resolve()
    controls = Path(control_root).resolve()
    command_env = dict(os.environ if environ is None else environ)
    outcomes: list[dict[str, Any]] = []
    try:
        intent_paths = sorted(registry.glob("shard-*.intent.json"))
    except OSError as exc:
        return ({"error": f"{type(exc).__name__}: {exc}"},)
    for intent_path in intent_paths:
        try:
            intent = _read_json_object(intent_path)
            if set(intent) != {
                "schema_version", "group_id", "shard_index", "job_name",
                "submission_dir",
            } or intent["schema_version"] != _INTENT_SCHEMA:
                raise DispatchError("intent-schema")
            shard_index = intent["shard_index"]
            job_name = intent["job_name"]
            submission_dir = Path(intent["submission_dir"]).resolve()
            expected_artifact_root = (
                registry.parent / f"shard-{shard_index}" / "dispatch"
            ).resolve()
            if (
                type(shard_index) is not int
                or shard_index < 0
                or type(job_name) is not str
                or not job_name
                or not submission_dir.is_dir()
                or intent.get("group_id") != registry.parent.name
                or intent_path != _intent_path(registry, shard_index, "intent")
            ):
                raise DispatchError("intent-value")
            try:
                submission_dir.relative_to(expected_artifact_root)
            except ValueError as exc:
                raise DispatchError("intent-submission-dir") from exc
            if job_name != _job_name(submission_dir.name):
                raise DispatchError("intent-job-name")
            handled_path = _intent_path(registry, shard_index, "handled")
            if handled_path.exists():
                continue

            request_id: Optional[str] = None
            confirm_path = _intent_path(registry, shard_index, "confirm")
            if confirm_path.exists():
                confirm = _read_json_object(confirm_path)
                if set(confirm) != {
                    "schema_version", "shard_index", "request_id",
                } or confirm["schema_version"] != _INTENT_CONFIRM_SCHEMA:
                    raise DispatchError("intent-confirm-schema")
                if confirm["shard_index"] != shard_index:
                    raise DispatchError("intent-confirm-index")
                request_id = confirm["request_id"]
                if type(request_id) is not str:
                    raise DispatchError("intent-confirm-request-id")

            def bounded_run(command: Sequence[str], **kwargs: Any):
                remaining = deadline_at - clock()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, 0)
                requested = float(kwargs.get("timeout", remaining))
                kwargs["timeout"] = min(requested, remaining)
                return run_command(command, **kwargs)

            discovery: Optional[dict[str, Any]] = None
            if request_id is None and clock() < deadline_at:
                discovery_attempts: list[dict[str, Any]] = []
                for attempt in range(1, DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS + 1):
                    request_id, discovery = _discover_request_id(
                        bounded_run,
                        job_name=job_name,
                        submission_dir=submission_dir,
                        environ=command_env,
                    )
                    discovery_attempts.append({
                        "attempt": attempt,
                        **({} if discovery is None else discovery),
                    })
                    if request_id is not None or clock() >= deadline_at:
                        break
                    remaining_before_retry = max(0.0, deadline_at - clock())
                    sleep(min(DEFAULT_POLL_INTERVAL_S, remaining_before_retry))
                discovery = {"attempts": discovery_attempts}
            remaining = max(0.0, deadline_at - clock())
            qdel = _fresh_qstat_gated_qdel(
                bounded_run,
                request_id=request_id,
                cwd=submission_dir,
                environ=command_env,
                cleanup_budget_s=remaining,
                retry_interval_s=min(DEFAULT_POLL_INTERVAL_S, remaining),
                job_name=job_name,
                submission_dir=submission_dir,
                clock=clock,
                sleep=sleep,
            )
            outcome = {
                "schema_version": _INTENT_RECOVERY_SCHEMA,
                "shard_index": shard_index,
                "request_id": request_id,
                "discovery": discovery,
                "qdel": qdel,
            }
            transition_error: Optional[_OrphanHoldError] = None
            try:
                if qdel.get("job_may_remain") is True:
                    _latch_orphan_hold(
                        controls,
                        qdel=qdel,
                        submission_dir=submission_dir,
                        request_id=request_id,
                        job_name=job_name,
                    )
                else:
                    _release_pending_orphan_hold(
                        controls,
                        submission_dir=submission_dir,
                        request_id=request_id,
                        job_name=job_name,
                        expect_phase=None,
                        require_present=False,
                    )
            except _OrphanHoldError as exc:
                transition_error = exc
                qdel["hold_error"] = exc.detail
                outcome["orphan_hold_error"] = _orphan_hold_error_record(exc)
            recovery_path = _intent_path(registry, shard_index, "recovery")
            _write_json_atomic_replace(recovery_path, outcome)
            _fsync_dir(registry)
            outcomes.append(outcome)
            if transition_error is None and qdel.get("job_may_remain") is False:
                _mark_dispatch_intent_handled(
                    registry,
                    shard_index=shard_index,
                    request_id=request_id,
                )
        except BaseException as exc:
            outcomes.append({
                "intent_path": str(intent_path),
                "error": f"{type(exc).__name__}: {exc}",
            })
    return tuple(outcomes)


def _print_qdel_remaining_warning(
    qdel: Mapping[str, Any],
    *,
    request_id: Optional[str],
    job_name: str,
) -> None:
    """gate 拒否または qdel 失敗で job が残り得ることを人間へ示す。"""

    if qdel.get("job_may_remain") is not True:
        return
    displayed = request_id if request_id is not None else job_name
    gate = qdel.get("gate")
    gate_reason = gate.get("reason") if isinstance(gate, Mapping) else None
    print(
        f"Pegasus request {displayed}: fresh qstat gate / qdel の結果、"
        f"ジョブが残っている可能性があります (reason={gate_reason})。"
        "ユーザー自身の端末で qstat を確認してください。",
        file=sys.stderr,
        flush=True,
    )


def _persist_receipt(
    submission_dir: Path,
    output_root: Path,
    payload: Mapping[str, Any],
) -> Optional[Path]:
    preferred = submission_dir / "receipt.json"
    try:
        _write_json_x(preferred, payload)
        return preferred
    except (FileExistsError, OSError):
        fallback = output_root / f"receipt-fallback-{submission_dir.name}.json"
        try:
            _write_json_x(fallback, payload)
            return fallback
        except (FileExistsError, OSError):
            return None


def _dispatch_impl(
    args: Sequence[str],
    *,
    task: str = DEFAULT_TASK,
    repo_root: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    output_root: Optional[Path] = None,
    artifact_root: Optional[Path] = None,
    control_root: Optional[Path] = None,
    intent_registry_root: Optional[Path] = None,
    intent_group_id: Optional[str] = None,
    intent_shard_index: Optional[int] = None,
    deadline_at: Optional[float] = None,
    walltime: str = DEFAULT_WALLTIME,
    queue_wait_timeout_s: float = DEFAULT_QUEUE_WAIT_TIMEOUT_S,
    overall_grace_s: float = DEFAULT_OVERALL_GRACE_S,
    accounting_grace_s: float = DEFAULT_ACCOUNTING_GRACE_S,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    log_limit_bytes: int = DEFAULT_LOG_LIMIT_BYTES,
    immediate_qstat_attempts: int = DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS,
    cleanup_budget_s: float = DEFAULT_CLEANUP_BUDGET_S,
    run_command: CommandRunner = subprocess.run,
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
    nonce: Optional[str] = None,
) -> int:
    """1 invocation を 1 batch job として投入し、会計照合済み rc を返す。"""

    # 不正 task は scheduler へ 1 度も触れずに落とす (親側)。子側の照合は _job_run。
    if task not in TASKS:
        raise ValueError(f"未知の task です: {task!r}")
    spec = TASKS[task]
    if spec.argv_policy == "generic-v1" and type(args) is not list:
        raise ValueError("generic args は string list でなければなりません")
    if isinstance(args, (str, bytes)) and spec.argv_policy != "passthrough":
        raise ValueError(f"task {task!r} は shell 文字列を受理しません")
    request_args = list(args)
    if spec.argv_policy != "passthrough":
        try:
            _validate_task_argv(task, spec, request_args)
        except DispatchError as exc:
            raise ValueError(str(exc)) from exc

    repo = (
        Path(__file__).resolve().parents[2]
        if repo_root is None else Path(repo_root).resolve()
    )
    if artifact_root is not None or control_root is not None:
        if output_root is not None or artifact_root is None or control_root is None:
            raise ValueError(
                "split dispatch requires artifact_root and control_root only"
            )
        root = Path(artifact_root).resolve()
        controls = Path(control_root).resolve()
        canonical_controls = repo / "output" / "pegasus-dispatch"
        if controls != canonical_controls or root == controls:
            raise ValueError(
                "split dispatch control_root must be repo/output/pegasus-dispatch"
            )
        try:
            root.relative_to(repo)
        except ValueError:
            pass
        else:
            raise ValueError("split dispatch artifact_root must be outside repo")
    else:
        root = (
            repo / "output" / "pegasus-dispatch"
            if output_root is None else Path(output_root).resolve()
        )
        controls = root
    intent_registry: Optional[Path] = None
    intent_enabled = any(
        value is not None
        for value in (intent_registry_root, intent_group_id, intent_shard_index)
    )
    if intent_enabled:
        if (
            artifact_root is None
            or intent_registry_root is None
            or type(intent_group_id) is not str
            or re.fullmatch(r"[A-Za-z0-9._-]+", intent_group_id) is None
            or type(intent_shard_index) is not int
            or intent_shard_index < 0
        ):
            raise ValueError("split dispatch intent registry contract is incomplete")
        intent_registry = Path(intent_registry_root).resolve()
        expected_registry = root.parent.parent / "dispatch-intents"
        if (
            intent_registry != expected_registry
            or intent_group_id != expected_registry.parent.name
        ):
            raise ValueError("split dispatch intent registry is not session-bound")
    walltime_s = _walltime_seconds(walltime)
    if min(
        queue_wait_timeout_s,
        overall_grace_s,
        accounting_grace_s,
        poll_interval_s,
        cleanup_budget_s,
    ) < 0:
        raise ValueError("timeout / interval は負にできません")
    if poll_interval_s == 0:
        raise ValueError("poll interval は 0 にできません")
    if immediate_qstat_attempts <= 0:
        raise ValueError("immediate qstat attempts は正でなければなりません")
    if deadline_at is not None:
        if not math.isfinite(deadline_at) or deadline_at <= clock():
            raise ValueError("parent deadline は将来の有限な monotonic 値が必要です")
        base_run_command = run_command
        base_sleep = sleep

        def deadline_bounded_run(command: Sequence[str], **kwargs: Any):
            remaining = deadline_at - clock()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, 0)
            requested = float(kwargs.get("timeout", remaining))
            kwargs["timeout"] = min(requested, remaining)
            return base_run_command(command, **kwargs)

        def deadline_bounded_sleep(seconds: float) -> None:
            remaining = max(0.0, deadline_at - clock())
            base_sleep(min(seconds, remaining))

        run_command = deadline_bounded_run
        sleep = deadline_bounded_sleep

    command_env = dict(os.environ if environ is None else environ)
    runner_binding, runner_binding_fd = _runner_binding_from_environment(
        command_env,
        task=task,
        intent_shard_index=intent_shard_index,
    )
    for name in _RUNNER_BINDING_ENV_KEYS:
        command_env.pop(name, None)
    request_env = {
        key: command_env[key]
        for key in spec.env_allowlist if key in command_env
    }
    command_env.pop(_TASK_RUN_ENV, None)
    command_env.pop(_TASK_RUN_ROOT_ENV, None)

    controls.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    latch = controls / "submission-disabled.json"
    orphan_hold = _orphan_hold_path(controls)
    quick_lock_fd = _acquire_control_lock(controls)
    try:
        if latch.exists():
            _print_terminal_handoff(latch, "既存の F47 型ラッチ")
            return _return_infra(
                "submission-disabled",
                child_started=False,
                allow_unstarted=True,
            )
        if _orphan_hold_present(controls):
            print(
                "Pegasus orphan hold があるため scheduler command を起動しません。"
                f"hold: {orphan_hold}。qstat で対象の不在または終端を確認し、"
                "source を復元してから hold を手動削除してください。",
                file=sys.stderr,
                flush=True,
            )
            return _return_infra(
                "orphan-hold",
                child_started=False,
                allow_unstarted=True,
            )
    finally:
        _release_control_lock(quick_lock_fd)

    nonce_value = nonce or secrets.token_hex(16)
    if re.fullmatch(r"[A-Za-z0-9._-]+", nonce_value) is None:
        raise ValueError("nonce は path separator を含まない leaf でなければなりません")
    submission_dir = root / nonce_value
    submission_dir.mkdir(mode=0o700)
    job_name = _job_name(submission_dir.name)
    receipt: dict[str, Any] = {
        "schema_version": _RECEIPT_SCHEMA,
        "submission_dir": str(submission_dir),
        "request": {
            "project": DEFAULT_PROJECT,
            "queue": DEFAULT_QUEUE,
            "nodes": 1,
            "walltime": walltime,
            "job_name": job_name,
            "task": task,
            "args": request_args,
        },
        "state_history": [],
        "qdel": {"attempted": False},
    }
    request_path = submission_dir / "request.json"
    probe_path = submission_dir / "interpreter_probe.py"
    script_path = submission_dir / "dispatch.sh"
    request_payload = {
        "schema_version": _REQUEST_SCHEMA,
        "repo_root": str(repo),
        "task": task,
        "args": request_args,
        "environment": request_env,
        "request_binding": _REQUEST_BINDING,
    }
    if runner_binding is not None:
        request_payload["runner_binding"] = runner_binding
    request_text = _canonical_json_text(request_payload)
    request_sha256 = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
    receipt["request"]["sha256"] = request_sha256
    _write_text_x(request_path, request_text, mode=0o600)
    _write_text_x(probe_path, _interpreter_probe_source(task), mode=0o600)
    _write_text_x(
        script_path,
        _job_script(
            repo_root=repo,
            submission_dir=submission_dir,
            request_path=request_path,
            probe_path=probe_path,
            request_sha256=request_sha256,
            walltime=walltime,
            task=task,
        ),
        mode=0o700,
    )
    _fsync_dir(submission_dir)
    _fsync_dir(root)
    if intent_registry is not None:
        intent_registry.mkdir(mode=0o700, parents=True, exist_ok=True)
        _register_dispatch_intent(
            intent_registry,
            group_id=intent_group_id,
            shard_index=intent_shard_index,
            job_name=job_name,
            submission_dir=submission_dir,
        )

    request_id: Optional[str] = None
    active = False
    qsub_submitted = False
    qsub_result_unknown = False
    request_was_visible = False
    run_seen = False
    queue_timeout_queued_evidence = False
    run_deadline_rebased = False
    terminal_history_end = False
    cleanup_claimed = False
    control_lock_fd: Optional[int] = None
    pending_cleanup_signal: Optional[int] = None
    pending_hold_armed = False
    pending_hold_release_blocked = False
    hold_transition_complete = True
    stdout_record: Optional[dict[str, Any]] = None
    stderr_record: Optional[dict[str, Any]] = None
    observed_child_rc: Optional[int] = None
    old_handlers: dict[int, Any] = {}

    def infra_child_started(reason: str) -> bool:
        """肯定的な未開始証拠がある queue timeout だけを false にする。"""

        if not qsub_submitted:
            return False
        return not (
            reason == "queue-wait-timeout"
            and queue_timeout_queued_evidence
        )

    def record_orphan_hold_error(
        error: _OrphanHoldError,
        *,
        qdel: Optional[dict[str, Any]] = None,
    ) -> None:
        nonlocal pending_hold_release_blocked, hold_transition_complete
        receipt["orphan_hold_error"] = _orphan_hold_error_record(error)
        if qdel is not None:
            qdel["hold_error"] = error.detail
        pending_hold_release_blocked = True
        hold_transition_complete = False

    def release_pending_after_durable_evidence(
        *,
        persisted: Optional[Path] = None,
    ) -> Optional[_OrphanHoldError]:
        nonlocal pending_hold_armed, pending_hold_release_blocked
        nonlocal hold_transition_complete
        if not pending_hold_armed or pending_hold_release_blocked:
            return None
        try:
            _release_pending_orphan_hold(
                controls,
                submission_dir=submission_dir,
                job_name=job_name,
                lock_fd=control_lock_fd,
            )
        except _SignalAbort:
            pending_hold_release_blocked = True
            hold_transition_complete = False
            raise
        except _OrphanHoldError as error:
            qdel_record = receipt.get("qdel")
            record_orphan_hold_error(
                error,
                qdel=qdel_record if isinstance(qdel_record, dict) else None,
            )
            if pending_cleanup_signal is None:
                receipt["outcome"] = {
                    "kind": "infra",
                    "reason": error.reason,
                    "rc": INFRA_RC,
                }
            if persisted is not None:
                try:
                    _write_json_atomic_replace(persisted, receipt)
                except OSError:
                    _persist_receipt(submission_dir, root, receipt)
            return error
        pending_hold_armed = False
        hold_transition_complete = True
        return None

    def persist_receipt_then_release_pending() -> tuple[
        Optional[Path], Optional[_OrphanHoldError]
    ]:
        persisted = _persist_receipt(submission_dir, root, receipt)
        if persisted is None:
            return None, None
        return persisted, release_pending_after_durable_evidence(
            persisted=persisted,
        )

    def abort_on_signal(signum, _frame):
        nonlocal pending_cleanup_signal
        if cleanup_claimed:
            # cleanup claim 後は destructive command を再入させず、最初の
            # signal を receipt に固定する。caller は現在の cleanup record を
            # 永続化した直後に INFRA 終了へ明示伝播する。
            if pending_cleanup_signal is None:
                pending_cleanup_signal = signum
                receipt["outcome"] = {
                    "kind": "infra",
                    "reason": f"_SignalAbort: signal {signum}",
                    "rc": INFRA_RC,
                }
            return
        raise _SignalAbort(signum)

    def claim_cleanup_once() -> dict[str, Any]:
        nonlocal cleanup_claimed, pending_hold_armed
        nonlocal hold_transition_complete
        if cleanup_claimed:
            return receipt["qdel"]
        qdel_record: dict[str, Any] = {
            "attempted": False,
            "cleanup_policy": _QDEL_CLEANUP_POLICY,
            "job_may_remain": True,
            "gate": {"reason": "cleanup-claimed"},
        }
        receipt["qdel"] = qdel_record
        cleanup_claimed = True
        primary: Optional[BaseException] = None
        try:
            effective_cleanup_budget = cleanup_budget_s
            if deadline_at is not None:
                effective_cleanup_budget = min(
                    effective_cleanup_budget,
                    max(0.0, deadline_at - clock()),
                )
            result = _fresh_qstat_gated_qdel(
                run_command,
                request_id=request_id,
                cwd=submission_dir if submission_dir.exists() else root,
                environ=command_env,
                qstat_attempts=immediate_qstat_attempts,
                cleanup_budget_s=effective_cleanup_budget,
                retry_interval_s=poll_interval_s,
                terminal_history_end=terminal_history_end,
                clock=clock,
                sleep=sleep,
                job_name=job_name,
                submission_dir=submission_dir,
                record=qdel_record,
            )
            return result
        except _SignalAbort as exc:
            primary = exc
            raise
        except BaseException as exc:
            primary = exc
            raise
        finally:
            try:
                _latch_orphan_hold(
                    controls,
                    qdel=qdel_record,
                    submission_dir=submission_dir,
                    request_id=request_id,
                    job_name=job_name,
                    lock_fd=control_lock_fd,
                )
                if qdel_record.get("hold_promoted") is True:
                    pending_hold_armed = False
                    hold_transition_complete = True
            except _SignalAbort:
                hold_transition_complete = False
                raise
            except _OrphanHoldError as error:
                record_orphan_hold_error(error, qdel=qdel_record)
                if pending_cleanup_signal is not None:
                    # deferred signal が論理上の一次理由で、hold failure は別証拠。
                    pass
                elif primary is not None:
                    raise primary from error
                else:
                    raise

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            old_handlers[signum] = signal.signal(signum, abort_on_signal)
        except (ValueError, OSError):
            pass

    started = 0.0
    submitted_at = 0.0
    try:
        # 既存の quick check 後に待機した peer もあるため、投入直前に mutex
        # 内で再検査し、immediate visibility の確定まで同じ lock を保持する。
        control_lock_fd = _acquire_control_lock(controls)
        if latch.exists():
            _print_terminal_handoff(latch, "既存の F47 型ラッチ")
            raise DispatchError("submission-disabled")
        if _orphan_hold_present(controls):
            raise DispatchError("orphan-hold")
        started = clock()
        preflight = _run(
            run_command,
            ["qstat", "-Q"],
            cwd=submission_dir,
            environ=command_env,
        )
        receipt["preflight"] = {"qstat_Q": _capture(preflight)}
        if preflight.returncode != 0:
            raise DispatchError(f"qstat -Q preflight rc={preflight.returncode}")

        _progress(f"job を {DEFAULT_QUEUE} へ投入します ({job_name})")
        hold_transition_complete = False
        try:
            _arm_pending_orphan_hold(
                controls,
                submission_dir=submission_dir,
                job_name=job_name,
                lock_fd=control_lock_fd,
            )
            pending_hold_armed = True
        except _SignalAbort:
            raise
        except _OrphanHoldError as error:
            record_orphan_hold_error(error)
            raise
        qsub_result_unknown = True
        qsub = _run(
            run_command,
            [
                "qsub",
                "-A", DEFAULT_PROJECT,
                "-q", DEFAULT_QUEUE,
                "-b", "1",
                "-l", f"elapstim_req={walltime}",
                "-N", job_name,
                script_path.name,
            ],
            cwd=submission_dir,
            environ=command_env,
        )
        if qsub.returncode == 0:
            # qsub 成功を観測した瞬間から cleanup 対象。receipt capture 中の
            # SIGINT/SIGTERM でも discovery + fresh-qstat gate を通し、
            # 直前 snapshot が許可した場合だけ qdel を要求する。
            active = True
            qsub_submitted = True
        qsub_result_unknown = False
        receipt["qsub"] = _capture(qsub)
        if qsub.returncode != 0:
            raise DispatchError(f"qsub rc={qsub.returncode}")
        submitted_at = clock()
        request_id = _parse_request_id(qsub.stdout or "")
        if intent_registry is not None:
            _confirm_dispatch_intent(
                intent_registry,
                shard_index=intent_shard_index,
                request_id=request_id,
            )
        normalized_id = _normalize_request_id(request_id)
        receipt["request_id"] = request_id
        receipt["normalized_request_id"] = normalized_id
        if _GATE_REQUEST_ID_RE.fullmatch(normalized_id) is None:
            raise DispatchError("malformed-request-id")
        _progress(f"request ID {normalized_id} を受理しました")

        immediate_attempt_records: list[dict[str, Any]] = []
        visible: Optional[subprocess.CompletedProcess[str]] = None
        permission_error: Optional[dict[str, Any]] = None
        qstat_succeeded_without_request = False
        for attempt in range(1, immediate_qstat_attempts + 1):
            candidate = _run(
                run_command,
                ["qstat", "-f", normalized_id],
                cwd=submission_dir,
                environ=command_env,
            )
            classification = _classify_qstat_response(candidate, normalized_id)
            attempt_record = {
                "attempt": attempt,
                "classification": classification,
                **_capture(candidate),
            }
            immediate_attempt_records.append(attempt_record)
            if classification == "permission":
                permission_error = attempt_record
                break
            if classification.startswith("success-"):
                visible = candidate
                request_was_visible = classification == "success-request-visible"
                qstat_succeeded_without_request = not request_was_visible
                break
            if attempt < immediate_qstat_attempts:
                sleep(poll_interval_s)
        receipt["immediate_qstat_attempts"] = immediate_attempt_records
        receipt["immediate_qstat"] = (
            _capture(visible) if visible is not None else immediate_attempt_records[-1]
        )
        receipt["f49_immediate"] = {
            "qstat_succeeded": visible is not None,
            "qstat_visible": request_was_visible,
        }
        if permission_error is not None:
            reason = "qstat-permission-or-ownership-error"
            receipt["outcome"] = {"kind": "f47", "reason": reason, "rc": INFRA_RC}
            receipt["qdel"] = claim_cleanup_once()
            active = False
            latched = _latch_submission_disabled(
                controls,
                reason=reason,
                submission_dir=submission_dir,
                request_id=request_id,
                lock_fd=control_lock_fd,
            )
            _, pending_release_error = persist_receipt_then_release_pending()
            if pending_cleanup_signal is not None:
                return _return_infra(
                    "signal-abort", child_started=True,
                )
            if pending_release_error is not None:
                return _return_infra(
                    pending_release_error.reason,
                    child_started=True,
                )
            _print_terminal_handoff(latched, reason)
            _print_qdel_remaining_warning(
                receipt["qdel"], request_id=request_id, job_name=job_name,
            )
            return _return_infra(reason, child_started=True)
        if visible is None:
            raise DispatchError("immediate-qstat-unavailable-after-retries")
        if qstat_succeeded_without_request:
            reason = "qstat-success-request-not-visible"
            receipt["outcome"] = {"kind": "f47", "reason": reason, "rc": INFRA_RC}
            receipt["qdel"] = claim_cleanup_once()
            active = False
            latched = _latch_submission_disabled(
                controls,
                reason=reason,
                submission_dir=submission_dir,
                request_id=request_id,
                lock_fd=control_lock_fd,
            )
            _, pending_release_error = persist_receipt_then_release_pending()
            if pending_cleanup_signal is not None:
                return _return_infra(
                    "signal-abort", child_started=True,
                )
            if pending_release_error is not None:
                return _return_infra(
                    pending_release_error.reason,
                    child_started=True,
                )
            _print_terminal_handoff(latched, reason)
            _print_qdel_remaining_warning(
                receipt["qdel"], request_id=request_id, job_name=job_name,
            )
            return _return_infra(reason, child_started=True)

        if intent_registry is not None:
            pending_release_error = release_pending_after_durable_evidence()
            if pending_release_error is not None:
                raise pending_release_error
        _release_control_lock(control_lock_fd)
        control_lock_fd = None

        current = visible
        queue_started = submitted_at
        total_deadline = submitted_at + walltime_s + overall_grace_s
        if deadline_at is not None:
            total_deadline = min(total_deadline, deadline_at)
        announced_state: Optional[str] = None
        terminal_at: Optional[float] = None
        while True:
            now = clock()
            request_absent = (
                request_was_visible
                and current.returncode == 0
                and not _qstat_mentions_request(current.stdout or "", normalized_id)
            )
            if request_absent:
                state = "END"
            else:
                computed_state = _scheduler_state(current.stdout or "")
                state = (
                    None
                    if computed_state == "END" and current.returncode != 0
                    else computed_state
                )
            shown_state = (
                "QSTAT_ERROR" if current.returncode != 0 else state or "UNKNOWN"
            )
            receipt["state_history"].append({
                "elapsed_s": max(0.0, now - started),
                "state": shown_state,
                "qstat_rc": int(current.returncode),
                "request_present": (
                    _qstat_mentions_request(current.stdout or "", normalized_id)
                    if current.returncode == 0 else None
                ),
            })
            if shown_state != announced_state:
                _progress(f"request {normalized_id} の状態: {shown_state}")
                announced_state = shown_state
            if state == "END":
                terminal_at = now
                terminal_history_end = True
                receipt["terminal_reason"] = (
                    "request-disappeared-after-visibility"
                    if request_absent else "scheduler-end-state"
                )
                break
            if state == "RUN":
                if current.returncode == 0 and not run_deadline_rebased:
                    run_deadline_rebased = True
                    # scheduler 上の実 RUN 開始ではなく、親が信頼できる
                    # RUN を初観測した時刻。
                    run_observed_at = now
                    total_deadline = (
                        run_observed_at + walltime_s + overall_grace_s
                    )
                    if deadline_at is not None:
                        total_deadline = min(total_deadline, deadline_at)
                if not run_seen:
                    run_seen = True
                    receipt["queue_wait_s"] = max(0.0, now - queue_started)
                    receipt["queue_wait_observed"] = True
            if not run_seen and now - queue_started >= queue_wait_timeout_s:
                # current はこの判定へ入る直前の qstat -f 応答である。
                # 対象 ID に一意に束縛された QUE だけを「まだ未開始」の
                # 肯定的証拠とし、HLD / RUN / END / 非ゼロ / UNKNOWN は
                # attestation を true へ倒す。
                queue_timeout_queued_evidence = (
                    current.returncode == 0
                    and _classify_qstat_response(
                        current, normalized_id,
                    ) == "success-request-visible"
                    and _target_bound_qstat_state(
                        current.stdout or "", normalized_id,
                    ) == "QUE"
                )
                raise DispatchError("queue-wait-timeout")
            if now >= total_deadline:
                raise DispatchError("overall-timeout")
            sleep(poll_interval_s)
            current = _run(
                run_command,
                ["qstat", "-f", normalized_id],
                cwd=submission_dir,
                environ=command_env,
            )

        if not run_seen:
            assert terminal_at is not None
            receipt["queue_wait_s"] = max(0.0, terminal_at - queue_started)
            receipt["queue_wait_observed"] = False
        _progress(f"request {normalized_id} の成果物収集を開始します")
        collection_deadline = clock() + accounting_grace_s
        if deadline_at is not None:
            collection_deadline = min(collection_deadline, deadline_at)
        result: Optional[dict[str, Any]] = None
        marker_valid = False
        marker_record: dict[str, Any] = {}
        while True:
            result_path = submission_dir / "result.json"
            try:
                if result_path.is_file() and not result_path.is_symlink():
                    result = _read_json_object(result_path)
                stdout_path = _find_log(
                    submission_dir, stream="stdout", request_id=request_id,
                )
                stderr_path = _find_log(
                    submission_dir, stream="stderr", request_id=request_id,
                )
                if stdout_path is not None:
                    stdout_record = _bounded_log(
                        stdout_path, limit=log_limit_bytes,
                    )
                if stderr_path is not None:
                    stderr_record = _bounded_log(
                        stderr_path, limit=log_limit_bytes,
                    )
                marker_valid, marker_record = _compute_marker_evidence(
                    submission_dir, request_id,
                )
            except DispatchError:
                raise
            if (
                result is not None
                and stdout_record is not None
                and stderr_record is not None
                and _accounting_present(stderr_record, request_id)
                and marker_valid
            ):
                break
            if clock() >= collection_deadline:
                receipt["collection"] = {
                    "result_present": result is not None,
                    "stdout": stdout_record,
                    "stderr": stderr_record,
                    "accounting_present": (
                        stderr_record is not None
                        and _accounting_present(stderr_record, request_id)
                    ),
                    "compute_marker": marker_record,
                }
                if not marker_valid:
                    reason = "compute-marker-not-observed"
                    receipt["outcome"] = {
                        "kind": "f47",
                        "reason": reason,
                        "rc": INFRA_RC,
                    }
                    receipt["qdel"] = claim_cleanup_once()
                    active = False
                    latched = _latch_submission_disabled(
                        controls,
                        reason=reason,
                        submission_dir=submission_dir,
                        request_id=request_id,
                        lock_fd=control_lock_fd,
                    )
                    _, pending_release_error = (
                        persist_receipt_then_release_pending()
                    )
                    if pending_cleanup_signal is not None:
                        return _return_infra(
                            "signal-abort", child_started=True,
                        )
                    if pending_release_error is not None:
                        return _return_infra(
                            pending_release_error.reason,
                            child_started=True,
                        )
                    _print_terminal_handoff(latched, reason)
                    _print_qdel_remaining_warning(
                        receipt["qdel"],
                        request_id=request_id,
                        job_name=job_name,
                    )
                    _relay_scheduler_logs(
                        stdout_record,
                        stderr_record,
                        request_id=request_id,
                        successful=False,
                    )
                    return _return_infra(reason, child_started=True)
                raise DispatchError("result/log/accounting-grace-expired")
            sleep(poll_interval_s)

        receipt["result"] = result
        receipt["scheduler_logs"] = {
            "stdout": stdout_record,
            "stderr": stderr_record,
            "accounting_present": True,
        }
        receipt["f49_compute_marker"] = marker_record
        result_id = result.get("pbs_jobid")
        child_rc = result.get("child_rc")
        if type(result_id) is not str or (
            _normalize_request_id(result_id) != normalized_id
        ):
            raise DispatchError("result の PBS job ID が submit receipt と不一致です")
        if result.get("stage") != "child":
            raise DispatchError(f"job bootstrap failure: stage={result.get('stage')}")
        if result.get("request_sha256") != request_sha256:
            raise DispatchError("result.request_sha256 が投入 request と不一致です")
        if type(child_rc) is not int:
            raise DispatchError("result.child_rc が int ではありません")
        observed_child_rc = child_rc
        if runner_binding is not None:
            assert runner_binding_fd is not None
            binding_report = _validated_runner_binding_report(
                result, runner_binding
            )
            _write_runner_binding_report(runner_binding_fd, binding_report)

        receipt["outcome"] = {
            "kind": "child",
            "rc": child_rc,
            "accounting_verified": True,
        }
        active = False
        persisted, pending_release_error = persist_receipt_then_release_pending()
        if persisted is None:
            print(
                "Pegasus dispatch receipt を永続化できませんでした。",
                file=sys.stderr,
                flush=True,
            )
            _relay_scheduler_logs(
                stdout_record,
                stderr_record,
                request_id=request_id,
                successful=False,
            )
            return _return_infra(
                "receipt-persist-failed",
                child_started=True,
                child_rc=child_rc,
            )
        if pending_release_error is not None:
            return _return_infra(
                "signal-abort"
                if pending_cleanup_signal is not None
                else pending_release_error.reason,
                child_started=True,
                child_rc=child_rc,
            )
        _progress(f"receipt を {persisted} へ保存しました (child rc={child_rc})")
        _relay_scheduler_logs(
            stdout_record,
            stderr_record,
            request_id=request_id,
            successful=child_rc == 0,
        )
        # Keep the child-start receipt explicit for the parent-side recording
        # gate.  _DispatchResult is an int subclass, so callers retaining the
        # historical rc-only contract see the same value.
        return _DispatchResult(child_rc, child_started=True)
    except BaseException as exc:
        primary_for_return: BaseException = exc
        if pending_cleanup_signal is None:
            receipt["outcome"] = {
                "kind": "infra",
                "reason": (
                    exc.reason
                    if isinstance(exc, _OrphanHoldError)
                    else f"{type(exc).__name__}: {exc}"
                ),
                "rc": INFRA_RC,
            }
        if isinstance(exc, _OrphanHoldError):
            record_orphan_hold_error(exc)
        if qsub_result_unknown:
            qdel_record = {
                "attempted": False,
                "cleanup_policy": _QDEL_CLEANUP_POLICY,
                "job_may_remain": True,
                "gate": {"reason": "qsub-result-unobserved"},
            }
            receipt["qdel"] = qdel_record
            try:
                _latch_orphan_hold(
                    controls,
                    qdel=qdel_record,
                    submission_dir=submission_dir,
                    request_id=request_id,
                    job_name=job_name,
                    lock_fd=control_lock_fd,
                )
                if qdel_record.get("hold_promoted") is True:
                    pending_hold_armed = False
                    hold_transition_complete = True
            except _SignalAbort as hold_signal:
                pending_hold_release_blocked = True
                hold_transition_complete = False
                primary_for_return = hold_signal
                if pending_cleanup_signal is None:
                    receipt["outcome"] = {
                        "kind": "infra",
                        "reason": f"_SignalAbort: signal {hold_signal.signum}",
                        "rc": INFRA_RC,
                    }
            except _OrphanHoldError as hold_error:
                record_orphan_hold_error(hold_error, qdel=qdel_record)
            discovered, discovery = _discover_request_id(
                run_command,
                job_name=job_name,
                submission_dir=submission_dir,
                environ=command_env,
            )
            receipt["request_id_discovery"] = discovery
            if discovered is not None:
                request_id = discovered
                receipt["request_id"] = discovered
                try:
                    receipt["normalized_request_id"] = _normalize_request_id(discovered)
                except DispatchError:
                    pass
                if not pending_hold_release_blocked:
                    try:
                        _latch_orphan_hold(
                            controls,
                            qdel=qdel_record,
                            submission_dir=submission_dir,
                            request_id=request_id,
                            job_name=job_name,
                            lock_fd=control_lock_fd,
                        )
                        if qdel_record.get("hold_promoted") is True:
                            pending_hold_armed = False
                            hold_transition_complete = True
                    except _SignalAbort as hold_signal:
                        pending_hold_release_blocked = True
                        hold_transition_complete = False
                        primary_for_return = hold_signal
                    except _OrphanHoldError as hold_error:
                        record_orphan_hold_error(hold_error, qdel=qdel_record)
        elif active:
            if request_id is None:
                discovered, discovery = _discover_request_id(
                    run_command,
                    job_name=job_name,
                    submission_dir=submission_dir,
                    environ=command_env,
                )
                receipt["request_id_discovery"] = discovery
                if discovered is not None:
                    request_id = discovered
                    receipt["request_id"] = discovered
                    try:
                        receipt["normalized_request_id"] = (
                            _normalize_request_id(discovered)
                        )
                    except DispatchError:
                        pass
            try:
                receipt["qdel"] = claim_cleanup_once()
            except BaseException as cleanup_error:
                primary_for_return = cleanup_error
                if isinstance(cleanup_error, _OrphanHoldError):
                    record_orphan_hold_error(cleanup_error)
                else:
                    receipt["qdel"]["cleanup_exception"] = (
                        f"{type(cleanup_error).__name__}: {cleanup_error}"
                    )
                if pending_cleanup_signal is None:
                    receipt["outcome"] = {
                        "kind": "infra",
                        "reason": (
                            cleanup_error.reason
                            if isinstance(cleanup_error, _OrphanHoldError)
                            else f"{type(cleanup_error).__name__}: {cleanup_error}"
                        ),
                        "rc": INFRA_RC,
                    }
        persisted, pending_release_error = persist_receipt_then_release_pending()
        if persisted is not None:
            _progress(f"receipt を {persisted} へ保存しました (child rc={INFRA_RC})")
        if pending_cleanup_signal is not None:
            return _return_infra(
                "signal-abort",
                child_started=True,
                child_rc=observed_child_rc,
            )
        if pending_release_error is not None:
            return _return_infra(
                pending_release_error.reason,
                child_started=infra_child_started(pending_release_error.reason),
                child_rc=observed_child_rc,
                allow_unstarted=True,
            )
        print(
            f"Pegasus dispatch infrastructure failure: {exc}",
            file=sys.stderr,
            flush=True,
        )
        _print_qdel_remaining_warning(
            receipt["qdel"], request_id=request_id, job_name=job_name,
        )
        _relay_scheduler_logs(
            stdout_record,
            stderr_record,
            request_id=request_id,
            successful=False,
        )
        infra_reason = _infra_attestation_reason(primary_for_return)
        return _return_infra(
            infra_reason,
            child_started=infra_child_started(infra_reason),
            child_rc=observed_child_rc,
            allow_unstarted=True,
        )
    finally:
        if intent_registry is not None:
            qdel = receipt.get("qdel")
            handled = hold_transition_complete and (
                (not qsub_submitted and not qsub_result_unknown)
                or (
                    isinstance(qdel, Mapping)
                    and qdel.get("job_may_remain") is False
                )
                or (
                    isinstance(receipt.get("outcome"), Mapping)
                    and receipt["outcome"].get("kind") == "child"
                )
            )
            if handled:
                _mark_dispatch_intent_handled(
                    intent_registry,
                    shard_index=intent_shard_index,
                    request_id=request_id,
                )
        if control_lock_fd is not None:
            _release_control_lock(control_lock_fd)
        for signum, handler in old_handlers.items():
            try:
                signal.signal(signum, handler)
            except (ValueError, OSError):
                pass


def dispatch(
    args: Sequence[str],
    *,
    task: str = DEFAULT_TASK,
    repo_root: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    output_root: Optional[Path] = None,
    artifact_root: Optional[Path] = None,
    control_root: Optional[Path] = None,
    intent_registry_root: Optional[Path] = None,
    intent_group_id: Optional[str] = None,
    intent_shard_index: Optional[int] = None,
    deadline_at: Optional[float] = None,
    walltime: str = DEFAULT_WALLTIME,
    queue_wait_timeout_s: float = DEFAULT_QUEUE_WAIT_TIMEOUT_S,
    overall_grace_s: float = DEFAULT_OVERALL_GRACE_S,
    accounting_grace_s: float = DEFAULT_ACCOUNTING_GRACE_S,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    log_limit_bytes: int = DEFAULT_LOG_LIMIT_BYTES,
    immediate_qstat_attempts: int = DEFAULT_IMMEDIATE_QSTAT_ATTEMPTS,
    cleanup_budget_s: float = DEFAULT_CLEANUP_BUDGET_S,
    run_command: CommandRunner = subprocess.run,
    clock: Clock = time.monotonic,
    sleep: Sleeper = time.sleep,
    nonce: Optional[str] = None,
) -> int:
    """setup 段の例外も含め、dispatcher infrastructure rc を 16 に畳む。"""

    old_handlers: dict[int, Any] = {}

    def abort_during_setup(signum, _frame):
        raise _SignalAbort(signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            old_handlers[signum] = signal.signal(signum, abort_during_setup)
        except (ValueError, OSError):
            pass
    try:
        return _dispatch_impl(
            args,
            task=task,
            repo_root=repo_root,
            environ=environ,
            output_root=output_root,
            artifact_root=artifact_root,
            control_root=control_root,
            intent_registry_root=intent_registry_root,
            intent_group_id=intent_group_id,
            intent_shard_index=intent_shard_index,
            deadline_at=deadline_at,
            walltime=walltime,
            queue_wait_timeout_s=queue_wait_timeout_s,
            overall_grace_s=overall_grace_s,
            accounting_grace_s=accounting_grace_s,
            poll_interval_s=poll_interval_s,
            log_limit_bytes=log_limit_bytes,
            immediate_qstat_attempts=immediate_qstat_attempts,
            cleanup_budget_s=cleanup_budget_s,
            run_command=run_command,
            clock=clock,
            sleep=sleep,
            nonce=nonce,
        )
    except (Exception, KeyboardInterrupt) as exc:
        repo = (
            Path(__file__).resolve().parents[2]
            if repo_root is None else Path(repo_root).resolve()
        )
        if artifact_root is not None:
            root = Path(artifact_root).resolve()
        else:
            root = (
                repo / "output" / "pegasus-dispatch"
                if output_root is None else Path(output_root).resolve()
            )
        try:
            root.mkdir(parents=True, exist_ok=True)
            receipt_nonce = (
                nonce
                if nonce is not None
                and re.fullmatch(r"[A-Za-z0-9._-]+", nonce) is not None
                else secrets.token_hex(8)
            )
            setup_receipt = root / f"receipt-setup-{receipt_nonce}.json"
            _write_json_x(setup_receipt, {
                "schema_version": _RECEIPT_SCHEMA,
                "outcome": {
                    "kind": "infra",
                    "reason": f"{type(exc).__name__}: {exc}",
                    "rc": INFRA_RC,
                },
                "request": {"task": task, "args": list(args)},
            })
        except (Exception, KeyboardInterrupt):
            pass
        print(
            f"Pegasus dispatch setup failure: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        # _dispatch_impl の run_seen が参照不能な setup 終端は、再試行を
        # 許さない向きへ fail-closed に倒す。
        setup_child_started = task not in TASKS
        return _return_infra(
            "setup-failure",
            child_started=setup_child_started,
            allow_unstarted=not setup_child_started,
        )
    finally:
        for signum, handler in old_handlers.items():
            try:
                signal.signal(signum, handler)
            except (ValueError, OSError):
                pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if values[:1] == ["--job-run"]:
        if len(values) == 3:
            rc = _job_run(Path(values[1]).resolve(), values[2])
            _job_trace("job-run-returned", rc=rc)
            return rc
        if len(values) == 2:
            # pre-binding in-flight v1/v2 script compatibility is decided by
            # _job_run after parsing the request; new tasks fail closed there.
            rc = _job_run(
                Path(values[1]).resolve(),
                os.environ.get(_REQUEST_SHA256_ENV),
            )
            _job_trace("job-run-returned", rc=rc)
            return rc
        print("--job-run は request path と SHA-256 を要求します", file=sys.stderr)
        return INFRA_RC

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--walltime", default=DEFAULT_WALLTIME)
    parser.add_argument(
        "--queue-wait-timeout",
        type=float,
        default=DEFAULT_QUEUE_WAIT_TIMEOUT_S,
    )
    parser.add_argument(
        "--overall-grace",
        type=float,
        default=DEFAULT_OVERALL_GRACE_S,
    )
    parser.add_argument(
        "--accounting-grace",
        type=float,
        default=DEFAULT_ACCOUNTING_GRACE_S,
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_S,
    )
    # CLI 面でも task を閉集合に固定する (親・子の二層 fail-closed の 3 点目)。
    parser.add_argument("--task", choices=tuple(TASKS), default=DEFAULT_TASK)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(values)
    child_args = list(parsed.args)
    if child_args[:1] == ["--"]:
        child_args = child_args[1:]
    return dispatch(
        child_args,
        task=parsed.task,
        walltime=parsed.walltime,
        queue_wait_timeout_s=parsed.queue_wait_timeout,
        overall_grace_s=parsed.overall_grace,
        accounting_grace_s=parsed.accounting_grace,
        poll_interval_s=parsed.poll_interval,
    )


if __name__ == "__main__":
    sys.exit(main())
