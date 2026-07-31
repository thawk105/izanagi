#!/usr/bin/env python3
"""Hash-bound source snapshots and synchronous Pegasus test dispatch.

The module is intentionally stdlib-only.  Its scheduler, clock, and filesystem
edges are explicit so unit tests can drive every transition without invoking
PBS or executing tests.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Protocol

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
import pegasus_policy


class DispatchError(RuntimeError):
    """A dispatch invariant could not be established."""


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    output_limited: bool = False
    signal: int | None = None
    completion_unknown: bool = False


class Scheduler(Protocol):
    def run(
        self,
        argv: Sequence[str],
        *,
        timeout: float,
        environment: Mapping[str, str] | None = None,
    ) -> CommandResult:
        """Run one bounded scheduler command."""


class MonitorFilesystem(Protocol):
    def exists(self, path: Path) -> bool: ...
    def receipt(self, path: Path) -> Mapping[str, object] | None: ...
    def load_object(self, path: Path) -> Mapping[str, object]: ...
    def publish_final(
        self, snapshot: "Snapshot", document: Mapping[str, object],
    ) -> None: ...
    def stage_final(
        self, snapshot: "Snapshot", document: Mapping[str, object],
    ) -> None: ...
    def replay(self, path: Path, destination: Any, byte_limit: int) -> int: ...
    def read_bytes(self, path: Path, byte_limit: int) -> bytes: ...
    def size(self, path: Path) -> int | None: ...
    def record_command(
        self,
        directory: Path,
        label: str,
        sequence: int,
        result: CommandResult,
    ) -> Mapping[str, object]: ...
    def next_sequence(self, directory: Path) -> int: ...


class SubprocessScheduler:
    """Run scheduler commands with bounded disk and memory output."""

    def __init__(
        self,
        *,
        max_output_bytes: int = 1024 * 1024,
        poll_interval_s: float = 0.05,
    ) -> None:
        if max_output_bytes <= 0 or poll_interval_s <= 0:
            raise ValueError("scheduler bounds must be positive")
        self.max_output_bytes = max_output_bytes
        self.poll_interval_s = poll_interval_s

    def run(
        self,
        argv: Sequence[str],
        *,
        timeout: float,
        environment: Mapping[str, str] | None = None,
    ) -> CommandResult:
        command = tuple(argv)
        timed_out = False
        output_limited = False
        process: Any | None = None
        try:
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen(
                    list(command),
                    stdout=stdout_file,
                    stderr=stderr_file,
                    env=(dict(environment) if environment is not None else None),
                )
                deadline = time.monotonic() + timeout
                try:
                    while process.poll() is None:
                        output_size = (
                            os.fstat(stdout_file.fileno()).st_size
                            + os.fstat(stderr_file.fileno()).st_size
                        )
                        if output_size > self.max_output_bytes:
                            output_limited = True
                            process.kill()
                            break
                        if time.monotonic() >= deadline:
                            timed_out = True
                            process.kill()
                            break
                        time.sleep(self.poll_interval_s)
                    raw_returncode = process.wait()
                except BaseException:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
                    raise
                stdout_file.seek(0)
                stderr_file.seek(0)
                stdout_raw = stdout_file.read(self.max_output_bytes + 1)
                stderr_raw = stderr_file.read(self.max_output_bytes + 1)
        except OSError as exc:
            started = process is not None
            if process is not None:
                try:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
                except OSError:
                    pass
            return CommandResult(
                command,
                126 if started else 127,
                "",
                str(exc),
                completion_unknown=started,
            )
        if len(stdout_raw) + len(stderr_raw) > self.max_output_bytes:
            output_limited = True
        stdout = stdout_raw[: self.max_output_bytes].decode("utf-8", "replace")
        remaining = max(0, self.max_output_bytes - len(stdout_raw))
        stderr = stderr_raw[:remaining].decode("utf-8", "replace")
        process_signal = (
            -raw_returncode
            if raw_returncode < 0 and not timed_out and not output_limited
            else None
        )
        if timed_out:
            returncode = 124
        elif output_limited:
            returncode = 125
        elif process_signal is not None:
            returncode = 128 + process_signal
        else:
            returncode = raw_returncode
        return CommandResult(
            command,
            returncode,
            stdout,
            stderr,
            timed_out=timed_out,
            output_limited=output_limited,
            signal=process_signal,
            completion_unknown=(
                timed_out or output_limited or process_signal is not None
            ),
        )


@dataclass(frozen=True)
class DispatchPolicy:
    policy_path: Path
    policy_sha256: str
    account: str
    queue: str
    nodes: int
    walltime: str
    walltime_s: int
    command_timeout_s: int
    poll_interval_s: float
    visibility_grace_s: int
    queue_timeout_s: int
    held_timeout_s: int
    prerun_timeout_s: int
    run_timeout_s: int
    global_deadline_s: int
    log_grace_s: int
    accounting_grace_s: int
    stderr_stable_polls: int
    qstat_transient_limit: int
    qdel_attempts: int
    qdel_retry_interval_s: float
    max_files: int
    max_file_bytes: int
    max_total_bytes: int
    min_free_bytes: int
    max_scheduler_output_bytes: int
    max_spool_bytes: int
    max_retained_dispatches: int
    max_retained_bytes: int
    replay_bytes: int
    dispatch_root_name: str
    allowed_ignored_roots: tuple[str, ...]


@dataclass(frozen=True)
class Snapshot:
    dispatch_id: str
    dispatch_dir: Path
    snapshot_root: Path
    manifest_path: Path
    manifest_sha256: str
    encoded_argv: tuple[Mapping[str, str], ...]
    runner_environment: Mapping[str, str]
    execution_closure_sha256: str = ""
    policy_sha256: str = ""
    snapshot_tree_sha256: str = ""


@dataclass(frozen=True)
class PollStatus:
    state: str
    raw_state: str | None
    visible: bool
    execution_hosts: tuple[str, ...]


@dataclass(frozen=True)
class SchedulerCandidate:
    request_id_raw: str
    job_id_normalized: str
    request_name: str
    user_name: str
    group_name: str
    queue: str
    account: str
    created_epoch_s: int
    state: str
    execution_hosts: tuple[str, ...]


@dataclass(frozen=True)
class SchedulerLookup:
    request_id_raw: str | None
    job_id_normalized: str | None
    state: str | None
    execution_hosts: tuple[str, ...]
    reason: str


_DISPATCH_ID_RE = re.compile(r"[0-9]{14}-[0-9a-f]{16}\Z", re.ASCII)
_NQSV_ID_RE = re.compile(r"(?:0:)?([0-9]+)\.nqsv\Z", re.ASCII)
_SAFE_NAME_RE = re.compile(r"[A-Za-z0-9_.-]+\Z", re.ASCII)
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)

_SAFE_FLAG_OPTIONS = frozenset({
    "-q", "-v", "-s", "-x", "-h", "--exitfirst", "--lf", "--last-failed",
    "--ff", "--failed-first", "--new-first", "--nf", "--disable-warnings",
    "--strict-config", "--strict-markers", "--continue-on-collection-errors",
    "--keep-duplicates", "--no-header", "--no-summary", "--full-trace",
    "--setup-only", "--setup-show", "--setup-plan", "--collect-only", "--co",
    "--fixtures", "--fixtures-per-test", "--markers", "--trace-config",
    "--help", "--version",
})
_SAFE_VALUE_OPTIONS = frozenset({
    "-k", "-m", "-n", "--numprocesses", "--dist", "--color", "--tb",
    "--capture", "--durations", "--durations-min", "--verbosity",
    "--show-capture", "--import-mode", "--log-level", "--log-format",
    "--log-date-format", "--log-cli-level", "--log-cli-format",
    "--log-cli-date-format", "--log-file-mode", "--log-file-level",
    "--log-file-format", "--log-file-date-format", "--junit-prefix",
    "--maxfail", "--stepwise-skip",
})
_REJECT_OPTIONS = frozenset({
    "-p", "--pyargs", "--rootdir", "--confcutdir", "--basetemp",
    "--junitxml", "--log-file", "--override-ini", "-o", "--ignore",
    "--ignore-glob", "--deselect",
})
_PLUGIN_ENV = ("PYTEST_PLUGINS", "PYTHONPATH")
_RUNNER_ENV_ALLOWLIST = (
    "IZANAGI_TASK_RUN_ID",
    "IZANAGI_TASK_RUNS_ROOT",
    "IZANAGI_TEST_TRIGGER",
    "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS",
    "IZANAGI_TEST_NPROC",
    "PYTEST_ADDOPTS",
)
_TASK_RUN_ID_RE = re.compile(r"[0-9]{8}-[a-z0-9][a-z0-9-]{0,31}-[0-9a-f]{8}\Z")
_TRIGGERS = frozenset({
    "baseline", "after-change", "after-failure", "final", "review-fix",
    "unspecified",
})
_QSTAT_STATE_RE = re.compile(r"^\s*Current State\s*=\s*(.+?)\s*$", re.MULTILINE)
_QSTAT_DETAIL_ID_RE = re.compile(
    r"(?m)^[ \t]*Request ID:[ \t]*(\S+)[ \t]*$"
)
_QSTAT_DETAIL_NAME_RE = re.compile(
    r"(?m)^[ \t]*Request Name[ \t]*=[ \t]*(\S(?:.*\S)?)[ \t]*$"
)
_QSTAT_DETAIL_USER_RE = re.compile(
    r"(?m)^[ \t]*User[ \t]+Name[ \t]*=[ \t]*(\S+)[ \t]*$"
)
_QSTAT_DETAIL_GROUP_RE = re.compile(
    r"(?m)^[ \t]*Group Name[ \t]*=[ \t]*(\S+)[ \t]*$"
)
_QSTAT_DETAIL_QUEUE_RE = re.compile(
    r"(?m)^[ \t]*Queue[ \t]*=[ \t]*(\S+)(?:[ \t]+.*)?$"
)
_QSTAT_DETAIL_ACCOUNT_RE = re.compile(
    r"(?m)^[ \t]*Account Code[ \t]*=[ \t]*(\S+)[ \t]*$"
)
_QSTAT_DETAIL_CREATED_RE = re.compile(
    r"(?m)^[ \t]*Created Request Time[ \t]*=[ \t]*(\S.*\S|\S)[ \t]*$"
)
_QSTAT_HOST_RE = re.compile(r"^\s*(?:Execution Hosts\(JSVNO\)|Execution Host)\s*:\s*$")
_BNODE_RE = re.compile(r"\bbnode[0-9]{3}\b", re.ASCII)
_NQSV_REQUEST_ID_RE = re.compile(
    r"(?m)^[ \t]*Request ID:[ \t]*(\S+)[ \t]*$"
)
_NQSV_STARTED_RE = re.compile(
    r"(?m)^[ \t]*Started Request Time:[ \t]*\S.*$"
)
_NQSV_ENDED_RE = re.compile(
    r"(?m)^[ \t]*Ended Request Time:[ \t]*\S.*$"
)
_NQSV_ELAPSE_RE = re.compile(r"(?m)^[ \t]*Elapse:[ \t]*\S.*$")
_NQSV_ACCOUNTING_LINE_RE = re.compile(
    r"(?i)(nqsv|request\s*(?:id|name)|(?:started|ended)\s+request\s+time|"
    r"elap(?:se|sed|stim))"
)
_NQSV_ACCOUNTING_SEPARATOR = "=" * 60
_NQSV_CREATED_TIME_RE = re.compile(
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun) "
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[ ]+"
    r"([0-9]{1,2}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) ([0-9]{4})\Z",
    re.ASCII,
)
_MONTHS = {
    name: index for index, name in enumerate(
        ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
        start=1,
    )
}
_WEEKDAYS = {
    name: index for index, name in enumerate(
        ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    )
}
_QSTAT_STATES = {
    "q": "queued",
    "queue": "queued",
    "queued": "queued",
    "waiting": "queued",
    "hld": "held",
    "hold": "held",
    "held": "held",
    "pre-running": "pre-running",
    "prerun": "pre-running",
    "r": "running",
    "run": "running",
    "running": "running",
    "complete": "terminal",
    "completed": "terminal",
    "ended": "terminal",
    "exit": "terminal",
    "exited": "terminal",
    "finished": "terminal",
}
_FINAL_OUTCOMES = frozenset({
    "CHILD_RESULT",
    "INFRA_FAILURE",
    "LOG_INCOMPLETE",
    "ACCOUNTING_INCOMPLETE",
    "CANCELED",
    "CANCEL_FAILED",
    "SUBMIT_FAILED",
    "SUBMIT_UNKNOWN",
    "INTERRUPTED",
    "INTERRUPT_CANCEL_FAILED",
    "CONTROLLER_FAILURE",
    "CONTROLLER_CANCEL_FAILED",
})


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path, *, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(block_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _write_all(fd: int, raw: bytes) -> None:
    view = memoryview(raw)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short write")
        view = view[written:]


def create_file(path: Path, raw: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        _write_all(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _validate_journal_raw(raw: bytes) -> tuple[int, str | None]:
    if len(raw) > 16 * 1024 * 1024:
        raise DispatchError("dispatch journal exceeds validation bound")
    sequence = 0
    previous: str | None = None
    for line in raw.splitlines(keepends=True):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DispatchError(f"dispatch journal is invalid JSON: {exc}") from None
        if (
            type(record) is not dict
            or set(record) != {"schema", "sequence", "prev_sha256", "payload"}
            or record.get("schema") != "izanagi-test-dispatch-journal-v1"
            or type(record.get("sequence")) is not int
            or record["sequence"] != sequence + 1
            or record.get("prev_sha256") != previous
            or type(record.get("payload")) is not dict
            or line != _canonical_json(record)
        ):
            raise DispatchError("dispatch journal hash chain is invalid")
        sequence += 1
        previous = sha256_bytes(line)
    return sequence, previous


def journal_head_sha256(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None
    return _validate_journal_raw(raw)[1]


def _journal_payloads(path: Path) -> tuple[Mapping[str, object], ...]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise DispatchError(f"dispatch journal is unavailable: {exc}") from None
    _validate_journal_raw(raw)
    return tuple(
        json.loads(line)["payload"] for line in raw.splitlines(keepends=True)
    )


def append_journal(
    path: Path,
    event: Mapping[str, object],
    *,
    sync: Callable[[int], None] = os.fsync,
) -> str:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    existed = path.exists()
    fd = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.lseek(fd, 0, os.SEEK_SET)
        existing = bytearray()
        while True:
            block = os.read(fd, 64 * 1024)
            if not block:
                break
            existing.extend(block)
            if len(existing) > 16 * 1024 * 1024:
                raise DispatchError("dispatch journal exceeds validation bound")
        sequence, previous = _validate_journal_raw(bytes(existing))
        record = {
            "schema": "izanagi-test-dispatch-journal-v1",
            "sequence": sequence + 1,
            "prev_sha256": previous,
            "payload": dict(event),
        }
        raw = _canonical_json(record)
        os.lseek(fd, 0, os.SEEK_END)
        _write_all(fd, raw)
        # Keep this injectable durability seam: qsub/cancel transitions must
        # not become externally visible before their WAL record is durable.
        sync(fd)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    if not existed:
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    return sha256_bytes(raw)


def load_policy(path: Path | None = None) -> DispatchPolicy:
    policy_path = (
        Path(__file__).with_name("test_dispatch_policy.json")
        if path is None else path
    )
    try:
        info = policy_path.lstat()
        raw = policy_path.read_bytes()
        after = policy_path.lstat()
        value = json.loads(raw)
    except (OSError, TypeError, json.JSONDecodeError) as exc:
        raise DispatchError(f"test dispatch policy unavailable: {exc}") from None
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or after.st_dev != info.st_dev
        or after.st_ino != info.st_ino
        or after.st_size != info.st_size
        or stat.S_IMODE(after.st_mode) != stat.S_IMODE(info.st_mode)
    ):
        raise DispatchError("test dispatch policy must be a regular non-symlink file")
    if len(raw) > 1024 * 1024:
        raise DispatchError("test dispatch policy exceeds validation bound")
    if type(value) is not dict or raw != _canonical_json(value):
        raise DispatchError("test dispatch policy is not canonical JSON")
    required = {
        "schema", "account", "queue", "nodes", "walltime", "walltime_s",
        "command_timeout_s", "poll_interval_s", "visibility_grace_s",
        "queue_timeout_s", "held_timeout_s", "prerun_timeout_s",
        "run_timeout_s", "global_deadline_s", "log_grace_s",
        "accounting_grace_s", "stderr_stable_polls",
        "qstat_transient_limit", "qdel_attempts", "qdel_retry_interval_s",
        "max_files", "max_file_bytes", "max_total_bytes", "min_free_bytes",
        "max_scheduler_output_bytes", "max_spool_bytes",
        "max_retained_dispatches", "max_retained_bytes", "replay_bytes",
        "dispatch_root_name", "allowed_ignored_roots",
    }
    if type(value) is not dict or set(value) != required:
        raise DispatchError("test dispatch policy keys are not exact")
    if value["schema"] != "izanagi-test-dispatch-policy-v1":
        raise DispatchError("test dispatch policy schema is invalid")
    if not all(
        type(value[name]) is int and value[name] > 0
        for name in (
            "nodes", "walltime_s", "command_timeout_s", "visibility_grace_s",
            "queue_timeout_s", "held_timeout_s", "prerun_timeout_s",
            "run_timeout_s", "global_deadline_s", "log_grace_s",
            "accounting_grace_s", "stderr_stable_polls",
            "qstat_transient_limit", "qdel_attempts", "max_files",
            "max_file_bytes", "max_total_bytes", "min_free_bytes",
            "max_scheduler_output_bytes", "max_spool_bytes",
            "max_retained_dispatches", "max_retained_bytes", "replay_bytes",
        )
    ):
        raise DispatchError("test dispatch positive integer policy is invalid")
    for name in ("poll_interval_s", "qdel_retry_interval_s"):
        if type(value[name]) not in (int, float) or value[name] <= 0:
            raise DispatchError(f"test dispatch {name} is invalid")
    if value["nodes"] != 1:
        raise DispatchError("test dispatch requires exactly one node")
    if not all(
        isinstance(value[name], str) and _SAFE_NAME_RE.fullmatch(value[name])
        for name in ("account", "queue")
    ):
        raise DispatchError("test dispatch account/queue is unsafe")
    if not isinstance(value["walltime"], str):
        raise DispatchError("test dispatch walltime is invalid")
    walltime_match = re.fullmatch(
        r"([0-9]{2,3}):([0-5][0-9]):([0-5][0-9])", value["walltime"],
    )
    if walltime_match is None:
        raise DispatchError("test dispatch walltime is invalid")
    hours, minutes, seconds = (int(part) for part in walltime_match.groups())
    if hours * 3600 + minutes * 60 + seconds != value["walltime_s"]:
        raise DispatchError("test dispatch walltime fields are inconsistent")
    if (
        value["global_deadline_s"] < value["run_timeout_s"]
        or value["max_spool_bytes"] > value["max_total_bytes"]
        or value["max_retained_bytes"] < value["max_total_bytes"]
        or value["replay_bytes"] > value["max_spool_bytes"]
    ):
        raise DispatchError("test dispatch aggregate bounds are inconsistent")
    roots = value["allowed_ignored_roots"]
    if type(roots) is not list or not all(type(item) is str for item in roots):
        raise DispatchError("allowed ignored roots are invalid")
    if any(
        not item
        or Path(item).is_absolute()
        or ".." in Path(item).parts
        for item in roots
    ):
        raise DispatchError("allowed ignored root is unsafe")
    fields = dict(value)
    fields.pop("schema")
    fields["allowed_ignored_roots"] = tuple(roots)
    return DispatchPolicy(
        policy_path=policy_path.resolve(strict=True),
        policy_sha256=sha256_bytes(raw),
        **fields,
    )


def normalize_job_id(raw: str) -> str:
    if not isinstance(raw, str):
        raise DispatchError("scheduler job ID is not text")
    match = _NQSV_ID_RE.fullmatch(raw.strip())
    if match is None:
        raise DispatchError("scheduler job ID is not an NQSV ID")
    return f"{match.group(1)}.nqsv"


def parse_qsub_id(stdout: str) -> tuple[str, str]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise DispatchError("qsub output does not contain exactly one request ID")
    raw = lines[0]
    return raw, normalize_job_id(raw)


def new_dispatch_id(now: float | None = None, nonce: bytes | None = None) -> str:
    stamp = time.strftime("%Y%m%d%H%M%S", time.gmtime(time.time() if now is None else now))
    entropy = os.urandom(16) if nonce is None else nonce
    return f"{stamp}-{hashlib.sha256(entropy).hexdigest()[:16]}"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _repo_relative_path(raw: str, source_root: Path, caller_cwd: Path) -> str:
    lexical = Path(raw)
    if not lexical.is_absolute():
        lexical = caller_cwd / lexical
    try:
        resolved = lexical.resolve(strict=True)
        root = source_root.resolve(strict=True)
    except OSError as exc:
        raise DispatchError(f"pytest target cannot be resolved: {raw!r}: {exc}") from None
    if not _inside(resolved, root):
        raise DispatchError(f"pytest target escapes source snapshot: {raw!r}")
    try:
        relative = lexical.absolute().relative_to(root).as_posix()
    except ValueError:
        # A repo-internal symlink reached from outside is still an external argv
        # dependency and is not accepted.
        raise DispatchError(f"pytest target spelling is outside source tree: {raw!r}") from None
    if relative in ("", ".") or relative.startswith("../"):
        raise DispatchError(f"invalid repository target: {raw!r}")
    return relative


def _validated_pytest_addopts(
    raw: str,
    *,
    source_root: Path,
    caller_cwd: Path,
) -> str:
    if "\x00" in raw or len(raw.encode("utf-8")) > 64 * 1024:
        raise DispatchError("PYTEST_ADDOPTS is invalid")
    try:
        tokens = shlex.split(raw, posix=True)
    except ValueError as exc:
        raise DispatchError(f"PYTEST_ADDOPTS cannot be parsed: {exc}") from None
    encoded = encode_pytest_argv(
        tokens,
        source_root=source_root,
        caller_cwd=caller_cwd,
        environ={},
    )
    if any(item.get("kind") != "literal" for item in encoded):
        raise DispatchError("PYTEST_ADDOPTS may not inject a path")
    return raw


def encode_pytest_argv(
    raw_args: Sequence[str],
    *,
    source_root: Path,
    caller_cwd: Path,
    environ: Mapping[str, str] | None = None,
) -> tuple[Mapping[str, str], ...]:
    """Encode argv without persisting a source-worktree absolute path."""

    source_root = source_root.resolve(strict=True)
    caller_cwd = caller_cwd.resolve(strict=True)
    env = os.environ if environ is None else environ
    poisoned = [name for name in _PLUGIN_ENV if env.get(name, "").strip()]
    if poisoned:
        raise DispatchError(
            "login dispatch refuses unbound pytest/plugin environment: "
            + ", ".join(poisoned)
        )
    addopts = env.get("PYTEST_ADDOPTS")
    if addopts is not None and addopts.strip():
        _validated_pytest_addopts(
            addopts,
            source_root=source_root,
            caller_cwd=caller_cwd,
        )

    encoded: list[Mapping[str, str]] = []
    values = list(raw_args)
    i = 0
    after_separator = False
    while i < len(values):
        token = values[i]
        if not isinstance(token, str) or "\x00" in token:
            raise DispatchError("pytest argv contains invalid text")
        if token.startswith("@"):
            raise DispatchError("pytest response files are not hash-bound")
        if token == "--":
            encoded.append({"kind": "literal", "value": token})
            after_separator = True
            i += 1
            continue
        option, equals, option_value = token.partition("=")
        if not after_separator and option in _REJECT_OPTIONS:
            raise DispatchError(f"pytest option is not safely staged: {option}")
        if not after_separator and token in _SAFE_VALUE_OPTIONS:
            if i + 1 >= len(values):
                raise DispatchError(f"pytest option lacks value: {token}")
            encoded.extend((
                {"kind": "literal", "value": token},
                {"kind": "literal", "value": values[i + 1]},
            ))
            i += 2
            continue
        if not after_separator and option in _SAFE_VALUE_OPTIONS and equals:
            if not option_value:
                raise DispatchError(f"pytest option lacks value: {option}")
            encoded.append({"kind": "literal", "value": token})
            i += 1
            continue
        if not after_separator and (
            token in _SAFE_FLAG_OPTIONS
            or (len(token) >= 2 and token[0] == "-" and set(token[1:]) <= {"q", "v"})
            or (token.startswith("-n") and token != "-n" and len(token) > 2)
        ):
            encoded.append({"kind": "literal", "value": token})
            i += 1
            continue
        if not after_separator and token.startswith("-"):
            raise DispatchError(f"unknown pytest option cannot be staged: {token}")

        path_part, separator, node_part = token.partition("::")
        relative = _repo_relative_path(path_part, source_root, caller_cwd)
        item: dict[str, str] = {"kind": "repo_path", "path": relative}
        if separator:
            item["node"] = node_part
        encoded.append(item)
        i += 1
    source_spelling = str(source_root)
    if any(
        source_spelling in value
        for item in encoded
        for value in item.values()
        if isinstance(value, str) and item.get("kind") == "literal"
    ):
        raise DispatchError("literal pytest argv exposes the source worktree path")
    return tuple(encoded)


def resolve_pytest_argv(
    encoded: Sequence[Mapping[str, str]], snapshot_root: Path,
) -> list[str]:
    root = snapshot_root.resolve(strict=True)
    result: list[str] = []
    for item in encoded:
        if set(item) == {"kind", "value"} and item.get("kind") == "literal":
            value = item["value"]
            if "\x00" in value or value.startswith("@"):
                raise DispatchError("encoded literal argv is invalid")
            result.append(value)
            continue
        keys = {"kind", "path"} | ({"node"} if "node" in item else set())
        if set(item) != keys or item.get("kind") != "repo_path":
            raise DispatchError("encoded argv item has invalid schema")
        relative = item["path"]
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise DispatchError("encoded repository path is unsafe")
        candidate = root / relative
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise DispatchError(f"snapshot target is unavailable: {relative}: {exc}") from None
        if not _inside(resolved, root):
            raise DispatchError(f"snapshot target escapes root: {relative}")
        value = str(candidate)
        if "node" in item:
            value += "::" + item["node"]
        result.append(value)
    return result


def _git_directories(source_root: Path) -> tuple[Path, Path]:
    marker = source_root / ".git"
    try:
        info = marker.lstat()
    except OSError as exc:
        raise DispatchError(f"source Git marker is unavailable: {exc}") from None
    if stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode):
        git_dir = marker.resolve(strict=True)
    elif stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode):
        try:
            text = marker.read_text(encoding="utf-8")
        except OSError as exc:
            raise DispatchError(f"source Git marker cannot be read: {exc}") from None
        prefix = "gitdir: "
        if not text.endswith("\n") or not text.startswith(prefix) or "\n" in text[:-1]:
            raise DispatchError("source Git marker has an unsafe format")
        lexical = Path(text[len(prefix):-1])
        if not lexical.is_absolute():
            lexical = source_root / lexical
        git_dir = lexical.resolve(strict=True)
    else:
        raise DispatchError("source Git marker is not a real file or directory")
    common_marker = git_dir / "commondir"
    if common_marker.exists():
        try:
            common_text = common_marker.read_text(encoding="utf-8")
        except OSError as exc:
            raise DispatchError(f"Git commondir cannot be read: {exc}") from None
        if not common_text.endswith("\n") or "\n" in common_text[:-1]:
            raise DispatchError("Git commondir has an unsafe format")
        common_lexical = Path(common_text[:-1])
        if not common_lexical.is_absolute():
            common_lexical = git_dir / common_lexical
        common_dir = common_lexical.resolve(strict=True)
    else:
        common_dir = git_dir
    return git_dir, common_dir


def _assert_local_git_safe(source_root: Path) -> None:
    git_dir, common_dir = _git_directories(source_root)
    config_paths = {
        common_dir / "config",
        git_dir / "config",
        git_dir / "config.worktree",
    }
    unsafe_section = re.compile(
        rb"(?im)^[ \t]*\[[ \t]*(?:filter|include|includeif)(?:[ \t\"\]]|$)"
    )
    unsafe_key = re.compile(
        rb"(?im)^[ \t]*(?:[^#;\r\n=]*"
        rb"(?:fsmonitor|attributesfile|textconv|external|command|hook)"
        rb"[^=\r\n]*)="
    )
    for config_path in sorted(config_paths):
        if not config_path.exists() and not config_path.is_symlink():
            continue
        try:
            info = config_path.lstat()
            raw = config_path.read_bytes()
            after = config_path.lstat()
        except OSError as exc:
            raise DispatchError(f"local Git config cannot be read: {exc}") from None
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or after.st_dev != info.st_dev
            or after.st_ino != info.st_ino
            or after.st_size != info.st_size
            or stat.S_IMODE(after.st_mode) != stat.S_IMODE(info.st_mode)
        ):
            raise DispatchError("local Git config is not a stable regular file")
        if len(raw) > 1024 * 1024:
            raise DispatchError("local Git config exceeds validation bound")
        if unsafe_section.search(raw) or unsafe_key.search(raw):
            raise DispatchError(
                f"unsafe local Git configuration is not allowed: {config_path.name}"
            )
    for info_attributes in {
        common_dir / "info" / "attributes",
        git_dir / "info" / "attributes",
    }:
        if info_attributes.exists() or info_attributes.is_symlink():
            raise DispatchError("Git info/attributes is not allowed")
    alternates = common_dir / "objects" / "info" / "alternates"
    if alternates.exists() or alternates.is_symlink():
        raise DispatchError("source Git object alternates are not allowed")


def _git_env() -> dict[str, str]:
    result = {
        name: value for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }
    result.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return result


def _git(
    repo: Path,
    args: Sequence[str],
    *,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    command = [
        "git", "-c", "core.hooksPath=/dev/null",
        "-c", "core.attributesFile=/dev/null",
        "-c", "core.fsmonitor=false",
        "-c", "core.untrackedCache=false",
        "-C", str(repo), *args,
    ]
    try:
        completed = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
            check=False,
        )
    except OSError as exc:
        raise DispatchError(f"git unavailable: {exc}") from None
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise DispatchError(f"git command failed rc={completed.returncode}: {detail}")
    return completed


def _git_bytes(repo: Path, args: Sequence[str]) -> bytes:
    return _git(repo, args).stdout


def _nul_paths(raw: bytes) -> tuple[str, ...]:
    if not raw:
        return ()
    pieces = raw.split(b"\0")
    if pieces[-1] != b"":
        raise DispatchError("git path inventory lacks NUL terminator")
    try:
        return tuple(piece.decode("utf-8", "surrogateescape") for piece in pieces[:-1])
    except UnicodeDecodeError:
        raise DispatchError("git path inventory cannot be decoded") from None


def _entry(
    path: Path,
    relative: str,
    *,
    max_file_bytes: int | None = None,
) -> Mapping[str, object]:
    info = path.lstat()
    mode = stat.S_IMODE(info.st_mode)
    if stat.S_ISLNK(info.st_mode):
        target = os.readlink(path)
        raw = os.fsencode(target)
        kind = "symlink"
    elif stat.S_ISREG(info.st_mode):
        if max_file_bytes is not None and info.st_size > max_file_bytes:
            raise DispatchError(f"snapshot file exceeds size limit: {relative}")
        raw = path.read_bytes()
        after = path.lstat()
        if (
            after.st_dev != info.st_dev
            or after.st_ino != info.st_ino
            or after.st_size != info.st_size
            or stat.S_IMODE(after.st_mode) != mode
        ):
            raise DispatchError(f"filesystem entry changed while hashing: {relative}")
        kind = "file"
    else:
        raise DispatchError(f"unsupported filesystem entry: {relative}")
    if max_file_bytes is not None and len(raw) > max_file_bytes:
        raise DispatchError(f"snapshot file exceeds size limit: {relative}")
    return {
        "path": relative,
        "kind": kind,
        "mode": mode,
        "size": len(raw),
        "sha256": sha256_bytes(raw),
        "link_target": target if kind == "symlink" else None,
    }


def _tree_summary(
    root: Path,
    policy: DispatchPolicy,
) -> Mapping[str, object]:
    resolved_root = root.resolve(strict=True)
    entries: list[Mapping[str, object]] = []
    for directory, names, files in os.walk(resolved_root, followlinks=False):
        if Path(directory) == resolved_root and ".git" in names:
            # Git administration bytes are not executed and may be refreshed
            # by read-only Git commands.  They are deliberately outside the
            # execution-tree proof.
            names.remove(".git")
        names.sort()
        files.sort()
        for name in tuple(names):
            candidate = Path(directory) / name
            if candidate.is_symlink():
                files.append(name)
                names.remove(name)
        for name in sorted(files):
            path = Path(directory) / name
            try:
                relative = path.relative_to(resolved_root).as_posix()
                entry = _entry(
                    path,
                    relative,
                    max_file_bytes=policy.max_file_bytes,
                )
            except (OSError, ValueError) as exc:
                raise DispatchError(f"snapshot tree inventory failed: {exc}") from None
            if entry["kind"] == "symlink":
                try:
                    target = path.resolve(strict=True)
                except OSError as exc:
                    raise DispatchError(
                        f"snapshot tree symlink is unresolved: {relative}: {exc}"
                    ) from None
                if not _inside(target, resolved_root):
                    raise DispatchError(
                        f"snapshot tree symlink escapes root: {relative}"
                    )
            entries.append(entry)
    entries.sort(key=lambda entry: str(entry["path"]))
    total = sum(int(entry["size"]) for entry in entries)
    if len(entries) > policy.max_files:
        raise DispatchError("snapshot tree file count exceeds policy")
    if total > policy.max_total_bytes:
        raise DispatchError("snapshot tree aggregate bytes exceed policy")
    projection = [
        {
            "path": entry["path"],
            "kind": entry["kind"],
            "mode": entry["mode"],
            "size": entry["size"],
            "sha256": entry["sha256"],
            "link_target": entry["link_target"],
        }
        for entry in entries
    ]
    return {
        "file_count": len(entries),
        "total_bytes": total,
        "sha256": sha256_bytes(_canonical_json(projection)),
        "entries": projection,
    }


def _directory_usage(
    root: Path,
    *,
    max_file_bytes: int,
) -> tuple[int, int]:
    count = 0
    total = 0
    if not root.exists():
        return count, total
    for directory, names, files in os.walk(root, followlinks=False):
        for name in tuple(names):
            candidate = Path(directory) / name
            if candidate.is_symlink():
                files.append(name)
                names.remove(name)
        for name in files:
            path = Path(directory) / name
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                size = info.st_size
            elif stat.S_ISLNK(info.st_mode):
                size = len(os.fsencode(os.readlink(path)))
            else:
                raise DispatchError(f"dispatch retention has special file: {path}")
            if size > max_file_bytes:
                raise DispatchError(f"dispatch retained file exceeds policy: {path.name}")
            count += 1
            total += size
    return count, total


def _tracked_regular_paths(raw: bytes) -> tuple[str, ...]:
    paths: list[str] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3 or fields[2] != b"0":
            raise DispatchError("tracked size inventory is malformed")
        if fields[0] == b"160000":
            # Gitlinks become directories in initialized worktrees.  Their
            # worktree bytes are inventoried once through the submodule path.
            continue
        paths.append(raw_path.decode("utf-8", "surrogateescape"))
    return tuple(paths)


def _completed_dispatch(path: Path) -> bool:
    final_path = path / "final-receipt.json"
    if not final_path.is_file() or final_path.is_symlink():
        return False
    try:
        snapshot = snapshot_from_dispatch(path)
        final = load_final_receipt(final_path, snapshot=snapshot)
    except DispatchError:
        return False
    return (
        final.get("dispatch_id") == path.name
        and final.get("dispatch_outcome") in _FINAL_OUTCOMES
    )


def _prune_retention(
    dispatch_root: Path,
    policy: DispatchPolicy,
    *,
    projected_bytes: int,
) -> tuple[int, int]:
    directories: list[Path] = []
    for child in sorted(dispatch_root.iterdir(), key=lambda item: item.name):
        info = child.lstat()
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or _DISPATCH_ID_RE.fullmatch(child.name) is None
        ):
            raise DispatchError(f"dispatch retention contains unsafe entry: {child.name}")
        directories.append(child)
    count, total = _directory_usage(
        dispatch_root,
        max_file_bytes=max(policy.max_file_bytes, policy.max_spool_bytes),
    )
    while (
        len(directories) + 1 > policy.max_retained_dispatches
        or total + projected_bytes > policy.max_retained_bytes
    ):
        removable = next(
            (candidate for candidate in directories if _completed_dispatch(candidate)),
            None,
        )
        if removable is None:
            raise DispatchError("dispatch retention limit has no completed victim")
        _, removed_bytes = _directory_usage(
            removable,
            max_file_bytes=max(policy.max_file_bytes, policy.max_spool_bytes),
        )
        shutil.rmtree(removable)
        directories.remove(removable)
        total -= removed_bytes
        root_fd = os.open(dispatch_root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(root_fd)
        finally:
            os.close(root_fd)
    return count, total


def _cleanup_partial_dispatch(dispatch_dir: Path, dispatch_root: Path) -> None:
    try:
        parent = dispatch_dir.parent.resolve(strict=True)
        root = dispatch_root.resolve(strict=True)
        info = dispatch_dir.lstat()
    except (FileNotFoundError, OSError):
        return
    if (
        parent != root
        or _DISPATCH_ID_RE.fullmatch(dispatch_dir.name) is None
        or not stat.S_ISDIR(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
    ):
        raise DispatchError("partial dispatch cleanup target is unsafe")
    shutil.rmtree(dispatch_dir)
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(root_fd)
    finally:
        os.close(root_fd)


def _copy_entry(source: Path, destination: Path, entry: Mapping[str, object]) -> None:
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if entry["kind"] == "symlink":
        os.symlink(str(entry["link_target"]), destination)
    else:
        fd = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            int(entry["mode"]),
        )
        try:
            with source.open("rb") as stream:
                while True:
                    block = stream.read(1024 * 1024)
                    if not block:
                        break
                    _write_all(fd, block)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.chmod(destination, int(entry["mode"]))


def _explicit_ignored_paths(
    encoded: Sequence[Mapping[str, str]],
    source_root: Path,
    allowed_roots: Sequence[str],
) -> tuple[str, ...]:
    allowed = tuple(Path(item) for item in allowed_roots)
    paths: list[str] = []
    # Policy roots are the explicit ignored-input allowlist.  Stage an existing
    # fixture closure even for the default full-suite argv, where no positional
    # target names the fixture directly.
    for root in allowed:
        target = source_root / root
        if not target.exists() and not target.is_symlink():
            continue
        if _git(
            source_root,
            ["check-ignore", "-q", "--", root.as_posix()],
            check=False,
        ).returncode != 0:
            continue
        if target.is_dir():
            for child in sorted(target.rglob("*")):
                if child.is_file() or child.is_symlink():
                    paths.append(child.relative_to(source_root).as_posix())
        else:
            paths.append(root.as_posix())
    for item in encoded:
        if item.get("kind") != "repo_path":
            continue
        relative = str(item["path"])
        ignored = _git(
            source_root,
            ["check-ignore", "-q", "--", relative],
            check=False,
        ).returncode == 0
        if not ignored:
            continue
        rel_path = Path(relative)
        if not any(rel_path == root or root in rel_path.parents for root in allowed):
            raise DispatchError(f"ignored pytest input is not allowlisted: {relative}")
        target = source_root / rel_path
        if target.is_dir():
            for child in sorted(target.rglob("*")):
                if child.is_file() or child.is_symlink():
                    paths.append(child.relative_to(source_root).as_posix())
        else:
            paths.append(relative)
    return tuple(sorted(set(paths)))


def _inventory(
    source_root: Path,
    paths: Sequence[str],
    policy: DispatchPolicy,
) -> tuple[Mapping[str, object], ...]:
    entries: list[Mapping[str, object]] = []
    total = 0
    for relative in sorted(set(paths)):
        source_path = source_root / relative
        entry = _entry(
            source_path,
            relative,
            max_file_bytes=policy.max_file_bytes,
        )
        if entry["kind"] == "symlink":
            link_target = Path(str(entry["link_target"]))
            if link_target.is_absolute():
                raise DispatchError(
                    f"snapshot symlink has an absolute target: {relative}"
                )
            try:
                resolved_target = source_path.resolve(strict=True)
            except OSError as exc:
                raise DispatchError(
                    f"snapshot symlink target is unavailable: {relative}: {exc}"
                ) from None
            if not _inside(resolved_target, source_root.resolve(strict=True)):
                raise DispatchError(f"snapshot symlink escapes source: {relative}")
        size = int(entry["size"])
        total += size
        entries.append(entry)
    if len(entries) > policy.max_files:
        raise DispatchError("snapshot file count exceeds policy")
    if total > policy.max_total_bytes:
        raise DispatchError("snapshot total bytes exceed policy")
    return tuple(entries)


def _source_state(repo: Path) -> Mapping[str, object]:
    return {
        "head": _git_bytes(repo, ["rev-parse", "HEAD"]).decode("ascii").strip(),
        "status_v2_sha256": sha256_bytes(_git_bytes(
            repo, ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
        )),
        "cached_diff_sha256": sha256_bytes(_git_bytes(
            repo, ["diff", "--cached", "--binary", "--no-ext-diff"],
        )),
        "unstaged_diff_sha256": sha256_bytes(_git_bytes(
            repo, ["diff", "--binary", "--no-ext-diff"],
        )),
    }


def _runner_environment(
    environ: Mapping[str, str],
    source_root: Path,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in _RUNNER_ENV_ALLOWLIST:
        value = environ.get(name)
        if value is None:
            continue
        if (
            not isinstance(value, str)
            or "\x00" in value
            or (
                name != "IZANAGI_TASK_RUNS_ROOT"
                and str(source_root) in value
            )
        ):
            raise DispatchError(f"runner environment is unsafe: {name}")
        if name == "IZANAGI_TASK_RUN_ID" and _TASK_RUN_ID_RE.fullmatch(value) is None:
            raise DispatchError("task-run ID is invalid")
        if name == "IZANAGI_TASK_RUNS_ROOT":
            if "IZANAGI_TASK_RUN_ID" not in environ:
                raise DispatchError("task-run root requires a task-run ID")
            lexical = Path(value)
            if not lexical.is_absolute():
                raise DispatchError("task-run root must be absolute")
            try:
                info = lexical.lstat()
                resolved = lexical.resolve(strict=True)
            except OSError as exc:
                raise DispatchError(f"task-run root is unavailable: {exc}") from None
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise DispatchError("task-run root must be a real directory")
            value = str(resolved)
        if name == "IZANAGI_TEST_TRIGGER" and value not in _TRIGGERS:
            raise DispatchError("test trigger is invalid")
        if name == "IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS" and value != "1":
            raise DispatchError("deletion bypass value is invalid")
        if name == "IZANAGI_TEST_NPROC" and (
            len(value) > 64 or any(ord(character) < 0x20 for character in value)
        ):
            raise DispatchError("test worker environment override is invalid")
        if name == "PYTEST_ADDOPTS":
            value = _validated_pytest_addopts(
                value,
                source_root=source_root,
                caller_cwd=source_root,
            )
        result[name] = value
    if (
        "IZANAGI_TASK_RUN_ID" in result
        and "IZANAGI_TASK_RUNS_ROOT" not in result
    ):
        default_root = source_root / "output" / "task-runs"
        try:
            info = default_root.lstat()
            resolved = default_root.resolve(strict=True)
        except OSError as exc:
            raise DispatchError(
                f"default durable task-run root is unavailable: {exc}"
            ) from None
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise DispatchError("default durable task-run root is unsafe")
        result["IZANAGI_TASK_RUNS_ROOT"] = str(resolved)
    return result


def _assert_attributes_safe(source_root: Path) -> None:
    root = source_root.resolve(strict=True)
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = [
            name for name in names
            if name != ".git" and not (Path(directory) / name).is_symlink()
        ]
        if ".gitattributes" not in files:
            continue
        path = Path(directory) / ".gitattributes"
        try:
            info = path.lstat()
            raw = path.read_bytes()
            after = path.lstat()
            relative = path.relative_to(root).as_posix()
        except (OSError, ValueError) as exc:
            raise DispatchError(f"Git attributes cannot be read safely: {exc}") from None
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or after.st_dev != info.st_dev
            or after.st_ino != info.st_ino
            or after.st_size != info.st_size
            or stat.S_IMODE(after.st_mode) != stat.S_IMODE(info.st_mode)
        ):
            raise DispatchError(
                f"Git attributes must be a stable regular file: {relative}"
            )
        if len(raw) > 1024 * 1024:
            raise DispatchError(f"Git attributes exceed validation bound: {relative}")
        if re.search(
            rb"(?im)(?:^|[ \t])(?:-?filter|-?working-tree-encoding)"
            rb"(?:[ \t]|=|$)",
            raw,
        ):
            raise DispatchError(
                f"Git checkout-transform attributes are not allowed: {relative}"
            )


def _prepare_dispatch_root(source_root: Path, name: str) -> Path:
    if "/" in name or name in ("", ".", ".."):
        raise DispatchError("dispatch root name is unsafe")
    root = source_root.parent / name
    try:
        root.mkdir(mode=0o700)
    except FileExistsError:
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise DispatchError("dispatch root is not a real directory")
        if info.st_uid != os.getuid():
            raise DispatchError("dispatch root is not owned by the caller")
        if stat.S_IMODE(info.st_mode) & 0o022:
            raise DispatchError("dispatch root is group/other writable")
    return root.resolve(strict=True)


def scheduler_environment(
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    source = os.environ if environ is None else environ
    path = source.get("PATH", "")
    if (
        not isinstance(path, str)
        or not path
        or "\x00" in path
        or "\n" in path
        or "\r" in path
    ):
        raise DispatchError("scheduler PATH is unavailable or unsafe")
    return {
        "PATH": path,
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
    }


def scheduler_user_name() -> str:
    try:
        value = pwd.getpwuid(os.getuid()).pw_name
    except (KeyError, OSError) as exc:
        raise DispatchError(f"scheduler submit user is unavailable: {exc}") from None
    if not value or any(character in value for character in "\x00\r\n"):
        raise DispatchError("scheduler submit user is unsafe")
    return value


def _nqsv_created_epoch(value: str) -> int:
    match = _NQSV_CREATED_TIME_RE.fullmatch(value)
    if match is None:
        raise DispatchError("scheduler lookup created time is malformed")
    weekday, month, day, hour, minute, second, year = match.groups()
    try:
        observed = datetime(
            int(year),
            _MONTHS[month],
            int(day),
            int(hour),
            int(minute),
            int(second),
            tzinfo=timezone.utc,
        )
    except ValueError:
        raise DispatchError("scheduler lookup created time is malformed") from None
    if observed.weekday() != _WEEKDAYS[weekday]:
        raise DispatchError("scheduler lookup created weekday is inconsistent")
    return int(observed.timestamp())


def _preclone_capacity(
    source_root: Path,
    dispatch_root: Path,
    policy: DispatchPolicy,
    scheduler: Scheduler,
    encoded: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, object], ...]:
    records: list[Mapping[str, object]] = []
    command_environment = scheduler_environment()
    for name, argv in (
        ("qstat_Q", ("qstat", "-Q")),
        ("pegasusinfo", ("pegasusinfo",)),
        ("rbudgetcheck", ("rbudgetcheck",)),
        ("check_quota", ("check_quota",)),
    ):
        result = scheduler.run(
            argv,
            timeout=policy.command_timeout_s,
            environment=command_environment,
        )
        records.append({
            "name": name,
            "argv": list(argv),
            "returncode": result.returncode,
            "signal": result.signal,
            "timed_out": result.timed_out,
            "output_limited": result.output_limited,
            "stdout_sha256": sha256_bytes(result.stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(result.stderr.encode("utf-8")),
        })
        if (
            result.returncode != 0
            or result.timed_out
            or result.output_limited
            or result.signal is not None
        ):
            raise DispatchError(f"pre-dispatch {name} failed rc={result.returncode}")
        if not result.stdout.strip():
            raise DispatchError(f"pre-dispatch {name} produced no evidence")
        if name == "qstat_Q" and policy.queue not in result.stdout:
            raise DispatchError(
                f"pre-dispatch queue evidence lacks {policy.queue}"
            )
    # Count every projected category once: tracked working bytes, nonignored
    # untracked bytes, allowlisted ignored input, submodule worktrees, and Git
    # object storage.  Every regular file is checked before any clone/copy.
    tracked = _tracked_regular_paths(_git_bytes(
        source_root, ["ls-files", "-s", "-z", "--cached"],
    ))
    total = 0
    count = 0
    for relative in tracked:
        path = source_root / relative
        try:
            if path.exists() or path.is_symlink():
                entry = _entry(
                    path,
                    relative,
                    max_file_bytes=policy.max_file_bytes,
                )
                total += int(entry["size"])
                count += 1
        except OSError as exc:
            raise DispatchError(f"source size inventory failed: {relative}: {exc}") from None
    main_untracked = _inventory(
        source_root,
        _nul_paths(_git_bytes(
            source_root, ["ls-files", "-z", "--others", "--exclude-standard"],
        )),
        policy,
    )
    ignored = _inventory(
        source_root,
        _explicit_ignored_paths(
            encoded,
            source_root,
            policy.allowed_ignored_roots,
        ),
        policy,
    )
    count += len(main_untracked) + len(ignored)
    total += sum(int(entry["size"]) for entry in (*main_untracked, *ignored))
    object_total = 0
    repositories = [source_root]
    submodule_status = _git(
        source_root, ["submodule", "status", "--recursive"], check=False,
    )
    if submodule_status.returncode != 0:
        raise DispatchError("submodule size inventory is unavailable")
    for line in submodule_status.stdout.decode("utf-8", "replace").splitlines():
        if not line:
            continue
        fields = line[1:].split()
        if line[0] == "-" or len(fields) < 2:
            raise DispatchError("submodule size inventory requires initialization")
        repositories.append(source_root / fields[1])
    for repository in repositories:
        if repository != source_root:
            _assert_local_git_safe(repository)
            _assert_attributes_safe(repository)
            for relative in _nul_paths(_git_bytes(
                repository, ["ls-files", "-z", "--cached"],
            )):
                path = repository / relative
                try:
                    if path.exists() or path.is_symlink():
                        entry = _entry(
                            path,
                            relative,
                            max_file_bytes=policy.max_file_bytes,
                        )
                        total += int(entry["size"])
                        count += 1
                except OSError as exc:
                    raise DispatchError(
                        f"submodule size inventory failed: {relative}: {exc}"
                    ) from None
            submodule_untracked = _inventory(
                repository,
                _nul_paths(_git_bytes(
                    repository,
                    ["ls-files", "-z", "--others", "--exclude-standard"],
                )),
                policy,
            )
            count += len(submodule_untracked)
            total += sum(int(entry["size"]) for entry in submodule_untracked)
        raw = _git_bytes(repository, ["count-objects", "-v"]).decode("ascii")
        values: dict[str, int] = {}
        for line in raw.splitlines():
            key, separator, value = line.partition(": ")
            if separator and value.isdigit():
                values[key] = int(value)
        if "size" not in values or "size-pack" not in values:
            raise DispatchError("Git object size inventory is incomplete")
        object_total += (values["size"] + values["size-pack"]) * 1024
        _, common_dir = _git_directories(repository)
        object_root = common_dir / "objects"
        if object_root.exists():
            object_count, observed_object_bytes = _directory_usage(
                object_root,
                max_file_bytes=policy.max_file_bytes,
            )
            count += object_count
            # count-objects is the authoritative projected clone bound.  The
            # raw-file walk independently enforces per-file limits.
            if observed_object_bytes > object_total + policy.max_file_bytes:
                raise DispatchError("Git object accounting is inconsistent")
    projected_total = total + object_total
    if count > policy.max_files or projected_total > policy.max_total_bytes:
        raise DispatchError("projected snapshot aggregate exceeds dispatch policy")
    _prune_retention(
        dispatch_root,
        policy,
        projected_bytes=projected_total,
    )
    _, retained_bytes = _directory_usage(
        dispatch_root,
        max_file_bytes=max(policy.max_file_bytes, policy.max_spool_bytes),
    )
    if retained_bytes + projected_total > policy.max_retained_bytes:
        raise DispatchError("dispatch aggregate quota would be exceeded")
    usage = shutil.disk_usage(dispatch_root)
    if usage.free < policy.min_free_bytes + projected_total:
        raise DispatchError("dispatch filesystem projected free space is below policy")
    records.append({
        "name": "projected_quota",
        "file_count": count,
        "snapshot_bytes": projected_total,
        "retained_bytes": retained_bytes,
        "free_bytes": usage.free,
    })
    return tuple(records)


def _clone_without_external_git_state(source: Path, destination: Path, template: Path) -> None:
    command = [
        "git", "-c", "core.hooksPath=/dev/null",
        "-c", "core.attributesFile=/dev/null",
        "-c", "core.fsmonitor=false",
        "-c", "core.untrackedCache=false",
        "clone", "--no-local", "--no-hardlinks", "--no-checkout",
        f"--template={template}", "--", str(source), str(destination),
    ]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_env(),
            check=False,
        )
    except OSError as exc:
        raise DispatchError(f"git clone unavailable: {exc}") from None
    if result.returncode != 0:
        raise DispatchError(
            "git clone failed: " + result.stderr.decode("utf-8", "replace").strip()
        )
    _git(destination, ["checkout", "--detach", "HEAD"])
    _git(destination, ["remote", "remove", "origin"], check=False)
    _git(destination, ["config", "--local", "--unset-all", "core.hooksPath"], check=False)
    alternates = destination / ".git" / "objects" / "info" / "alternates"
    if alternates.exists() or alternates.is_symlink():
        raise DispatchError("snapshot clone retained object alternates")
    if _git_bytes(destination, ["remote"]).strip():
        raise DispatchError("snapshot clone retained a remote")


def _apply_dirty_state(source: Path, snapshot: Path) -> tuple[bytes, bytes]:
    cached = _git_bytes(source, ["diff", "--cached", "--binary", "--no-ext-diff"])
    unstaged = _git_bytes(source, ["diff", "--binary", "--no-ext-diff"])
    if cached:
        _git(snapshot, ["apply", "--index", "--binary", "-"], input_bytes=cached)
    if unstaged:
        _git(snapshot, ["apply", "--binary", "-"], input_bytes=unstaged)
    return cached, unstaged


def _submodule_records(
    source_root: Path,
    policy: DispatchPolicy,
) -> tuple[Mapping[str, object], ...]:
    result = _git(source_root, ["submodule", "status", "--recursive"], check=False)
    if result.returncode not in (0,):
        raise DispatchError("submodule status is unavailable")
    records: list[Mapping[str, object]] = []
    for raw_line in result.stdout.decode("utf-8", "replace").splitlines():
        if not raw_line:
            continue
        prefix = raw_line[0]
        fields = raw_line[1:].split()
        if prefix == "-" or len(fields) < 2:
            raise DispatchError("all registered submodules must be initialized")
        commit, relative = fields[0], fields[1]
        subroot = source_root / relative
        _assert_local_git_safe(subroot)
        _assert_attributes_safe(subroot)
        head = _git_bytes(subroot, ["rev-parse", "HEAD"]).decode("ascii").strip()
        gitlink_line = _git_bytes(
            source_root, ["ls-files", "-s", "--", relative],
        ).decode("utf-8", "strict").strip()
        gitlink_fields = gitlink_line.split(maxsplit=3)
        if (
            len(gitlink_fields) != 4
            or gitlink_fields[0] != "160000"
            or gitlink_fields[2] != "0"
            or gitlink_fields[3] != relative
        ):
            raise DispatchError(f"submodule gitlink is invalid: {relative}")
        untracked_paths = _nul_paths(_git_bytes(
            subroot, ["ls-files", "-z", "--others", "--exclude-standard"],
        ))
        records.append({
            "path": relative,
            "gitlink": gitlink_fields[1],
            "status_reported_head": commit,
            "head": head,
            "status_v2_sha256": sha256_bytes(_git_bytes(
                subroot, ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
            )),
            "cached_diff_sha256": sha256_bytes(_git_bytes(
                subroot, ["diff", "--cached", "--binary", "--no-ext-diff"],
            )),
            "unstaged_diff_sha256": sha256_bytes(_git_bytes(
                subroot, ["diff", "--binary", "--no-ext-diff"],
            )),
            "untracked": list(_inventory(subroot, untracked_paths, policy)),
        })
    return tuple(records)


def _materialize_submodules(
    source_root: Path,
    snapshot_root: Path,
    records: Sequence[Mapping[str, object]],
    template: Path,
    policy: DispatchPolicy,
) -> None:
    for record in records:
        relative = str(record["path"])
        source = source_root / relative
        destination = snapshot_root / relative
        if destination.exists():
            if any(destination.iterdir()):
                raise DispatchError(f"snapshot submodule destination is not empty: {relative}")
            destination.rmdir()
        _clone_without_external_git_state(source, destination, template)
        _git(destination, ["checkout", "--detach", str(record["head"])])
        _apply_dirty_state(source, destination)
        entries = record["untracked"]
        if type(entries) is not list:
            raise DispatchError(f"submodule inventory is invalid: {relative}")
        for entry in entries:
            _copy_entry(
                source / str(entry["path"]),
                destination / str(entry["path"]),
                entry,
            )
        observed = {
            "status_v2_sha256": sha256_bytes(_git_bytes(
                destination,
                ["status", "--porcelain=v2", "-z", "--untracked-files=all"],
            )),
            "cached_diff_sha256": sha256_bytes(_git_bytes(
                destination, ["diff", "--cached", "--binary", "--no-ext-diff"],
            )),
            "unstaged_diff_sha256": sha256_bytes(_git_bytes(
                destination, ["diff", "--binary", "--no-ext-diff"],
            )),
        }
        for name, value in observed.items():
            if value != record[name]:
                raise DispatchError(f"submodule snapshot drift: {relative}: {name}")


def _closure_paths(
    snapshot_root: Path,
    encoded: Sequence[Mapping[str, str]],
    runner_environment: Mapping[str, str],
) -> tuple[str, ...]:
    fixed = {
        "tools/run_tests.py",
        "tools/ruleops.py",
        "tools/pegasus_policy.py",
        "tools/pegasus/test_dispatch.py",
        "tools/pegasus/submit_tests.py",
        "tools/pegasus/run_tests_job.sh",
        "tools/pegasus/test_dispatch_policy.json",
    }
    if "IZANAGI_TASK_RUN_ID" in runner_environment:
        task_run_root = snapshot_root / "tools" / "task_runs"
        if task_run_root.is_dir() and not task_run_root.is_symlink():
            for child in task_run_root.rglob("*"):
                if child.is_file() or child.is_symlink():
                    fixed.add(child.relative_to(snapshot_root).as_posix())
    selected = [
        str(item["path"])
        for item in encoded
        if item.get("kind") == "repo_path"
    ]
    if not selected:
        selected = ["orchestrator/tests"]
    roots = tuple(sorted(set(selected)))
    paths = set(fixed)
    for relative in roots:
        lexical = snapshot_root / relative
        try:
            resolved = lexical.resolve(strict=True)
        except OSError as exc:
            raise DispatchError(
                f"selected test closure is unavailable: {relative}: {exc}"
            ) from None
        if not _inside(resolved, snapshot_root.resolve(strict=True)):
            raise DispatchError(f"selected test closure escapes snapshot: {relative}")
        if lexical.is_symlink():
            paths.add(relative)
        if resolved.is_dir():
            for child in resolved.rglob("*"):
                if child.is_file() or child.is_symlink():
                    paths.add(child.relative_to(snapshot_root).as_posix())
        elif resolved.is_file():
            paths.add(resolved.relative_to(snapshot_root).as_posix())
            paths.add(relative)
        else:
            raise DispatchError(f"selected test closure is not a file/directory: {relative}")
        parent = lexical.parent
        while _inside(parent.resolve(strict=True), snapshot_root.resolve(strict=True)):
            conftest = parent / "conftest.py"
            if conftest.is_file() or conftest.is_symlink():
                paths.add(conftest.relative_to(snapshot_root).as_posix())
            if parent == snapshot_root:
                break
            parent = parent.parent
    return tuple(sorted(paths))


def _execution_closure(
    snapshot_root: Path,
    encoded: Sequence[Mapping[str, str]],
    runner_environment: Mapping[str, str],
    policy: DispatchPolicy,
) -> tuple[tuple[Mapping[str, object], ...], str]:
    entries = _inventory(
        snapshot_root,
        _closure_paths(snapshot_root, encoded, runner_environment),
        policy,
    )
    by_path = {str(entry["path"]): entry for entry in entries}
    for required in (
        "tools/run_tests.py",
        "tools/pegasus_policy.py",
        "tools/pegasus/test_dispatch.py",
        "tools/pegasus/submit_tests.py",
        "tools/pegasus/run_tests_job.sh",
        "tools/pegasus/test_dispatch_policy.json",
    ):
        entry = by_path.get(required)
        if entry is None or entry["kind"] != "file":
            raise DispatchError(f"execution closure lacks regular file: {required}")
    job_entry = by_path["tools/pegasus/run_tests_job.sh"]
    if int(job_entry["mode"]) & 0o111 == 0:
        raise DispatchError("snapshot job script is not executable")
    if (
        by_path["tools/pegasus/test_dispatch_policy.json"]["sha256"]
        != policy.policy_sha256
    ):
        raise DispatchError("snapshot policy differs from loaded policy")
    return entries, sha256_bytes(_canonical_json(list(entries)))


def verify_execution_closure(snapshot: Snapshot) -> str:
    manifest, raw = _load_exact_json(snapshot.manifest_path)
    if sha256_bytes(raw) != snapshot.manifest_sha256:
        raise DispatchError("snapshot manifest hash changed")
    closure = manifest.get("execution_closure")
    if type(closure) is not list or not all(type(item) is dict for item in closure):
        raise DispatchError("snapshot execution closure schema is invalid")
    expected_keys = {"path", "kind", "mode", "size", "sha256", "link_target"}
    policy = load_policy(
        snapshot.snapshot_root / "tools" / "pegasus" / "test_dispatch_policy.json"
    )
    if policy.policy_sha256 != snapshot.policy_sha256:
        raise DispatchError("snapshot policy changed")
    observed: list[Mapping[str, object]] = []
    for expected in closure:
        if set(expected) != expected_keys or not isinstance(expected.get("path"), str):
            raise DispatchError("snapshot execution closure entry is invalid")
        relative = str(expected["path"])
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise DispatchError("snapshot execution closure path is unsafe")
        current = _entry(
            snapshot.snapshot_root / relative,
            relative,
            max_file_bytes=policy.max_file_bytes,
        )
        if current != expected:
            raise DispatchError(f"snapshot execution closure drift: {relative}")
        observed.append(current)
    digest = sha256_bytes(_canonical_json(observed))
    if (
        manifest.get("execution_closure_sha256") != digest
        or snapshot.execution_closure_sha256 != digest
    ):
        raise DispatchError("snapshot execution closure digest mismatch")
    return digest


def create_snapshot(
    *,
    source_root: Path,
    caller_cwd: Path,
    raw_args: Sequence[str],
    policy: DispatchPolicy,
    scheduler: Scheduler,
    dispatch_id: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Snapshot:
    source_root = source_root.resolve(strict=True)
    if not (source_root / ".git").exists():
        raise DispatchError("source root is not a Git worktree")
    encoded = encode_pytest_argv(
        raw_args,
        source_root=source_root,
        caller_cwd=caller_cwd,
        environ=environ,
    )
    source_environ = os.environ if environ is None else environ
    runner_environment = _runner_environment(source_environ, source_root)
    _assert_local_git_safe(source_root)
    _assert_attributes_safe(source_root)
    expected_policy_path = (
        source_root / "tools" / "pegasus" / "test_dispatch_policy.json"
    )
    source_policy = load_policy(expected_policy_path)
    if (
        policy.policy_path != expected_policy_path.resolve(strict=True)
        or policy != source_policy
    ):
        raise DispatchError("loaded test dispatch policy is not source-root bound")
    dispatch_root = _prepare_dispatch_root(source_root, policy.dispatch_root_name)
    preflight = _preclone_capacity(
        source_root,
        dispatch_root,
        policy,
        scheduler,
        encoded,
    )
    identity = new_dispatch_id() if dispatch_id is None else dispatch_id
    if _DISPATCH_ID_RE.fullmatch(identity) is None:
        raise DispatchError("dispatch ID is invalid")
    dispatch_dir = dispatch_root / identity
    try:
        dispatch_dir.mkdir(mode=0o700)
    except FileExistsError:
        raise DispatchError("dispatch directory already exists") from None
    root_fd = os.open(dispatch_root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(root_fd)
    finally:
        os.close(root_fd)
    snapshot_root = dispatch_dir / "source"
    try:
        template = dispatch_dir / "empty-git-template"
        template.mkdir(mode=0o700)

        source_before = _source_state(source_root)
        submodules_before = _submodule_records(source_root, policy)
        untracked_paths = _nul_paths(_git_bytes(
            source_root, ["ls-files", "-z", "--others", "--exclude-standard"],
        ))
        ignored_paths = _explicit_ignored_paths(
            encoded, source_root, policy.allowed_ignored_roots,
        )
        untracked = _inventory(source_root, untracked_paths, policy)
        ignored = _inventory(source_root, ignored_paths, policy)

        _clone_without_external_git_state(source_root, snapshot_root, template)
        cached, unstaged = _apply_dirty_state(source_root, snapshot_root)
        for entry in (*untracked, *ignored):
            _copy_entry(
                source_root / str(entry["path"]),
                snapshot_root / str(entry["path"]),
                entry,
            )
        _materialize_submodules(
            source_root, snapshot_root, submodules_before, template, policy,
        )

        source_after = _source_state(source_root)
        if source_after != source_before:
            raise DispatchError("source tree changed while snapshot was being copied")
        if _submodule_records(source_root, policy) != submodules_before:
            raise DispatchError("submodule changed while snapshot was being copied")
        snapshot_state = _source_state(snapshot_root)
        if snapshot_state != source_before:
            raise DispatchError("snapshot Git status/diff does not match source")
        for entry in (*untracked, *ignored):
            try:
                current = _entry(
                    source_root / str(entry["path"]),
                    str(entry["path"]),
                    max_file_bytes=policy.max_file_bytes,
                )
            except OSError as exc:
                raise DispatchError(
                    f"source inventory changed while copying: {entry['path']}: {exc}"
                ) from None
            if current != entry:
                raise DispatchError(
                    f"source inventory changed while copying: {entry['path']}"
                )
            copied = _entry(
                snapshot_root / str(entry["path"]),
                str(entry["path"]),
                max_file_bytes=policy.max_file_bytes,
            )
            if copied != entry:
                raise DispatchError(f"snapshot inventory mismatch: {entry['path']}")

        snapshot_tree = _tree_summary(snapshot_root, policy)
        closure, closure_sha = _execution_closure(
            snapshot_root,
            encoded,
            runner_environment,
            policy,
        )
        manifest = {
            "schema": "izanagi-test-snapshot-v2",
            "dispatch_id": identity,
            "head": source_before["head"],
            "source_state": source_before,
            "cached_patch_sha256": sha256_bytes(cached),
            "unstaged_patch_sha256": sha256_bytes(unstaged),
            "untracked": list(untracked),
            "ignored_inputs": list(ignored),
            "submodules": list(submodules_before),
            "pytest_argv": list(encoded),
            "runner_environment": runner_environment,
            "preflight": list(preflight),
            "policy": {
                "path": "tools/pegasus/test_dispatch_policy.json",
                "sha256": policy.policy_sha256,
            },
            "execution_closure": list(closure),
            "execution_closure_sha256": closure_sha,
            "snapshot_tree": snapshot_tree,
            "snapshot_semantics": (
                "copied manifest bytes with ordinary concurrent-change detection; "
                "not an adversarial instantaneous filesystem snapshot"
            ),
        }
        manifest_path = dispatch_dir / "snapshot-manifest.json"
        raw = _canonical_json(manifest)
        create_file(manifest_path, raw)
        _, retained_bytes = _directory_usage(
            dispatch_root,
            max_file_bytes=max(policy.max_file_bytes, policy.max_spool_bytes),
        )
        if retained_bytes > policy.max_retained_bytes:
            raise DispatchError("copy-after dispatch aggregate exceeds policy")
        snapshot = Snapshot(
            dispatch_id=identity,
            dispatch_dir=dispatch_dir,
            snapshot_root=snapshot_root,
            manifest_path=manifest_path,
            manifest_sha256=sha256_bytes(raw),
            encoded_argv=encoded,
            runner_environment=manifest["runner_environment"],
            execution_closure_sha256=closure_sha,
            policy_sha256=policy.policy_sha256,
            snapshot_tree_sha256=str(snapshot_tree["sha256"]),
        )
        verify_execution_closure(snapshot)
        return snapshot
    except BaseException:
        _cleanup_partial_dispatch(dispatch_dir, dispatch_root)
        raise


def _load_exact_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_size > 16 * 1024 * 1024
        ):
            raise DispatchError(
                f"receipt is not a bounded regular file: {path.name}"
            )
        raw = path.read_bytes()
        after = path.lstat()
        if (
            after.st_dev != info.st_dev
            or after.st_ino != info.st_ino
            or after.st_size != info.st_size
            or stat.S_IMODE(after.st_mode) != stat.S_IMODE(info.st_mode)
        ):
            raise DispatchError(f"receipt changed while reading: {path.name}")
        value = json.loads(raw)
    except DispatchError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise DispatchError(f"receipt unavailable: {path.name}: {exc}") from None
    if type(value) is not dict:
        raise DispatchError(f"receipt is not an object: {path.name}")
    if raw != _canonical_json(value):
        raise DispatchError(f"receipt is not canonical JSON: {path.name}")
    return value, raw


def _manifest_closure_entry(
    snapshot: Snapshot,
    relative: str,
) -> Mapping[str, object]:
    manifest, _ = _load_exact_json(snapshot.manifest_path)
    closure = manifest.get("execution_closure")
    if type(closure) is not list:
        raise DispatchError("snapshot execution closure is unavailable")
    matches = [
        item for item in closure
        if type(item) is dict and item.get("path") == relative
    ]
    if len(matches) != 1:
        raise DispatchError(f"snapshot execution closure path is not unique: {relative}")
    return matches[0]


def _bound_snapshot_file(
    snapshot: Snapshot,
    path: Path,
    *,
    require_executable: bool = False,
) -> Mapping[str, object]:
    root = snapshot.snapshot_root.resolve(strict=True)
    lexical = path.absolute()
    try:
        relative = lexical.relative_to(root).as_posix()
        info = lexical.lstat()
    except (OSError, ValueError) as exc:
        raise DispatchError(f"snapshot executable path is unsafe: {exc}") from None
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise DispatchError(f"snapshot executable is not a regular file: {relative}")
    current = _entry(lexical, relative)
    if current != _manifest_closure_entry(snapshot, relative):
        raise DispatchError(f"snapshot executable differs from manifest: {relative}")
    if require_executable and int(current["mode"]) & 0o111 == 0:
        raise DispatchError(f"snapshot executable lacks execute mode: {relative}")
    return current


def create_qsub_request(
    snapshot: Snapshot,
    *,
    policy: DispatchPolicy,
    argv: Sequence[str],
    environment: Mapping[str, str],
    job_script: Path,
    qsub_started_epoch_s: float,
) -> tuple[Path, str, float]:
    verify_execution_closure(snapshot)
    job_entry = _bound_snapshot_file(
        snapshot,
        job_script,
        require_executable=True,
    )
    policy_path = snapshot.snapshot_root / "tools" / "pegasus" / (
        "test_dispatch_policy.json"
    )
    policy_entry = _bound_snapshot_file(snapshot, policy_path)
    if (
        policy_entry["sha256"] != policy.policy_sha256
        or snapshot.policy_sha256 != policy.policy_sha256
    ):
        raise DispatchError("qsub policy binding mismatch")
    if (
        type(qsub_started_epoch_s) not in (int, float)
        or isinstance(qsub_started_epoch_s, bool)
        or qsub_started_epoch_s < 0
    ):
        raise DispatchError("qsub start time is invalid")
    absolute_deadline = qsub_started_epoch_s + policy.global_deadline_s
    document = {
        "schema": "izanagi-test-qsub-request-v1",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy": dict(policy_entry),
        "job_script": dict(job_entry),
        "argv": list(argv),
        "environment": dict(sorted(environment.items())),
        "submit_user": scheduler_user_name(),
        "qsub_started_epoch_s": qsub_started_epoch_s,
        "absolute_deadline_epoch_s": absolute_deadline,
    }
    _validate_qsub_request_object(document, snapshot=snapshot)
    path = snapshot.dispatch_dir / "qsub-request.json"
    raw = _canonical_json(document)
    create_file(path, raw)
    return path, sha256_bytes(raw), absolute_deadline


def create_pre_submit_authorization(
    snapshot: Snapshot,
    *,
    qsub_request_sha256: str,
) -> tuple[Path, str]:
    if _HEX64_RE.fullmatch(qsub_request_sha256) is None:
        raise DispatchError("qsub request hash is invalid")
    document = {
        "schema": "izanagi-test-pre-submit-v2",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "qsub_request_sha256": qsub_request_sha256,
        "snapshot_root": str(snapshot.snapshot_root),
    }
    _validate_authorization_object(
        document,
        snapshot=snapshot,
        qsub_request_sha256=qsub_request_sha256,
    )
    path = snapshot.dispatch_dir / "pre-submit-authorization.json"
    raw = _canonical_json(document)
    create_file(path, raw)
    return path, sha256_bytes(raw)


def create_qsub_result(
    snapshot: Snapshot,
    *,
    qsub_request_sha256: str,
    result: CommandResult,
) -> tuple[Path, str]:
    stdout_path = snapshot.dispatch_dir / "qsub.stdout"
    stderr_path = snapshot.dispatch_dir / "qsub.stderr"
    rc_path = snapshot.dispatch_dir / "qsub.rc"
    create_file(stdout_path, result.stdout.encode("utf-8"))
    create_file(stderr_path, result.stderr.encode("utf-8"))
    create_file(rc_path, f"{result.returncode}\n".encode("ascii"))
    document = {
        "schema": "izanagi-test-qsub-result-v1",
        "dispatch_id": snapshot.dispatch_id,
        "qsub_request_sha256": qsub_request_sha256,
        "argv": list(result.argv),
        "returncode": result.returncode,
        "signal": result.signal,
        "timed_out": result.timed_out,
        "output_limited": result.output_limited,
        "completion_unknown": result.completion_unknown,
        "stdout": _file_receipt(stdout_path),
        "stderr": _file_receipt(stderr_path),
        "returncode_file": _file_receipt(rc_path),
    }
    request, request_raw = _load_exact_json(
        snapshot.dispatch_dir / "qsub-request.json"
    )
    if sha256_bytes(request_raw) != qsub_request_sha256:
        raise DispatchError("qsub result request hash mismatch")
    _validate_qsub_request_object(request, snapshot=snapshot)
    _validate_qsub_result_object(
        document,
        snapshot=snapshot,
        qsub_request_sha256=qsub_request_sha256,
        request=request,
        verify_files=True,
    )
    path = snapshot.dispatch_dir / "qsub-result.json"
    raw = _canonical_json(document)
    create_file(path, raw)
    return path, sha256_bytes(raw)


def create_submit_receipt(
    snapshot: Snapshot,
    *,
    authorization_sha256: str,
    qsub_request_sha256: str,
    qsub_result_sha256: str,
    qsub_request_id_raw: str,
    job_id_normalized: str,
) -> tuple[Path, str]:
    document = {
        "schema": "izanagi-test-submit-v2",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "authorization_sha256": authorization_sha256,
        "qsub_request_sha256": qsub_request_sha256,
        "qsub_result_sha256": qsub_result_sha256,
        "qsub_request_id_raw": qsub_request_id_raw,
        "job_id_normalized": job_id_normalized,
    }
    _validate_submit_object(
        document,
        snapshot=snapshot,
        authorization_sha256=authorization_sha256,
        qsub_request_sha256=qsub_request_sha256,
        qsub_result_sha256=qsub_result_sha256,
    )
    path = snapshot.dispatch_dir / "submit-receipt.json"
    raw = _canonical_json(document)
    create_file(path, raw)
    return path, sha256_bytes(raw)


def _validate_qsub_request_object(
    request: Mapping[str, object],
    *,
    snapshot: Snapshot,
) -> DispatchPolicy:
    expected_keys = {
        "schema", "dispatch_id", "snapshot_manifest_sha256",
        "execution_closure_sha256", "policy", "job_script",
        "argv", "environment", "submit_user", "qsub_started_epoch_s",
        "absolute_deadline_epoch_s",
    }
    if (
        set(request) != expected_keys
        or request.get("schema") != "izanagi-test-qsub-request-v1"
        or request.get("dispatch_id") != snapshot.dispatch_id
        or request.get("snapshot_manifest_sha256") != snapshot.manifest_sha256
        or request.get("execution_closure_sha256")
        != snapshot.execution_closure_sha256
    ):
        raise DispatchError("qsub request schema/identity mismatch")
    policy = load_policy(
        snapshot.snapshot_root
        / "tools"
        / "pegasus"
        / "test_dispatch_policy.json"
    )
    if policy.policy_sha256 != snapshot.policy_sha256:
        raise DispatchError("qsub request policy differs from snapshot")
    expected_policy = _manifest_closure_entry(
        snapshot, "tools/pegasus/test_dispatch_policy.json"
    )
    expected_job = _manifest_closure_entry(
        snapshot, "tools/pegasus/run_tests_job.sh"
    )
    if request.get("policy") != expected_policy:
        raise DispatchError("qsub request policy file receipt mismatch")
    if request.get("job_script") != expected_job:
        raise DispatchError("qsub request job script receipt mismatch")
    job_script = (
        snapshot.snapshot_root / "tools" / "pegasus" / "run_tests_job.sh"
    )
    expected_argv = qsub_argv(
        snapshot=snapshot,
        policy=policy,
        authorization_path=(
            snapshot.dispatch_dir / "pre-submit-authorization.json"
        ),
        runner_result_path=snapshot.dispatch_dir / "runner-result.json",
        job_script=job_script,
    )
    if request.get("argv") != list(expected_argv):
        raise DispatchError("qsub request argv does not match snapshot policy")
    environment = request.get("environment")
    if (
        type(environment) is not dict
        or set(environment) != {"PATH", "LANG", "LC_ALL", "TZ"}
        or environment.get("LANG") != "C"
        or environment.get("LC_ALL") != "C"
        or environment.get("TZ") != "UTC"
        or not isinstance(environment.get("PATH"), str)
        or not environment["PATH"]
        or any(character in environment["PATH"] for character in "\x00\r\n")
    ):
        raise DispatchError("qsub request environment is not closed")
    if (
        not isinstance(request.get("submit_user"), str)
        or request.get("submit_user") != scheduler_user_name()
    ):
        raise DispatchError("qsub request submit user is invalid")
    started = request.get("qsub_started_epoch_s")
    deadline = request.get("absolute_deadline_epoch_s")
    if (
        type(started) not in (int, float)
        or isinstance(started, bool)
        or started < 0
        or type(deadline) not in (int, float)
        or isinstance(deadline, bool)
        or deadline != started + policy.global_deadline_s
    ):
        raise DispatchError("qsub request deadline is invalid")
    return policy


def _validate_authorization_object(
    authorization: Mapping[str, object],
    *,
    snapshot: Snapshot,
    qsub_request_sha256: str,
) -> None:
    if (
        set(authorization) != {
            "schema", "dispatch_id", "snapshot_manifest_sha256",
            "execution_closure_sha256", "policy_sha256",
            "qsub_request_sha256", "snapshot_root",
        }
        or authorization.get("schema") != "izanagi-test-pre-submit-v2"
        or authorization.get("dispatch_id") != snapshot.dispatch_id
        or authorization.get("snapshot_manifest_sha256")
        != snapshot.manifest_sha256
        or authorization.get("execution_closure_sha256")
        != snapshot.execution_closure_sha256
        or authorization.get("policy_sha256") != snapshot.policy_sha256
        or authorization.get("qsub_request_sha256") != qsub_request_sha256
        or authorization.get("snapshot_root") != str(snapshot.snapshot_root)
    ):
        raise DispatchError("pre-submit authorization chain mismatch")


def _validate_qsub_result_object(
    qsub_result: Mapping[str, object],
    *,
    snapshot: Snapshot,
    qsub_request_sha256: str,
    request: Mapping[str, object],
    verify_files: bool,
) -> None:
    if (
        set(qsub_result) != {
            "schema", "dispatch_id", "qsub_request_sha256", "argv",
            "returncode", "signal", "timed_out", "output_limited",
            "completion_unknown", "stdout", "stderr", "returncode_file",
        }
        or qsub_result.get("schema") != "izanagi-test-qsub-result-v1"
        or qsub_result.get("dispatch_id") != snapshot.dispatch_id
        or qsub_result.get("qsub_request_sha256") != qsub_request_sha256
        or qsub_result.get("argv") != request.get("argv")
        or type(qsub_result.get("returncode")) is not int
        or not 0 <= int(qsub_result["returncode"]) <= 255
        or type(qsub_result.get("timed_out")) is not bool
        or type(qsub_result.get("output_limited")) is not bool
        or type(qsub_result.get("completion_unknown")) is not bool
    ):
        raise DispatchError("qsub result schema/identity mismatch")
    process_signal = qsub_result.get("signal")
    if process_signal is not None and (
        type(process_signal) is not int
        or not 1 <= process_signal <= 64
        or qsub_result["returncode"] != 128 + process_signal
        or qsub_result["timed_out"]
        or qsub_result["output_limited"]
    ):
        raise DispatchError("qsub result signal domain is invalid")
    if (
        qsub_result["timed_out"]
        and (
            qsub_result["returncode"] != 124
            or process_signal is not None
        )
    ):
        raise DispatchError("qsub timeout result is invalid")
    if (
        qsub_result["output_limited"]
        and not qsub_result["timed_out"]
        and (
            qsub_result["returncode"] != 125
            or process_signal is not None
        )
    ):
        raise DispatchError("qsub output-limit result is invalid")
    required_unknown = bool(
        qsub_result["timed_out"]
        or qsub_result["output_limited"]
        or process_signal is not None
    )
    if (
        (required_unknown and not qsub_result["completion_unknown"])
        or (
            qsub_result["completion_unknown"]
            and not (
                required_unknown
                or qsub_result["returncode"] == 126
            )
        )
        or (
            qsub_result["returncode"] == 126
            and (
                qsub_result["timed_out"]
                or qsub_result["output_limited"]
                or process_signal is not None
            )
        )
    ):
        raise DispatchError("qsub completion uncertainty is invalid")
    for name, filename in (
        ("stdout", "qsub.stdout"),
        ("stderr", "qsub.stderr"),
        ("returncode_file", "qsub.rc"),
    ):
        value = qsub_result.get(name)
        if (
            type(value) is not dict
            or not _receipt_or_none_valid(
                value,
                snapshot.dispatch_dir,
                verify_files=verify_files,
            )
            or Path(str(value["path"])).name != filename
        ):
            raise DispatchError(f"qsub result file receipt is invalid: {name}")
    if verify_files:
        try:
            expected_rc = f"{qsub_result['returncode']}\n".encode("ascii")
            observed_rc = (
                snapshot.dispatch_dir / "qsub.rc"
            ).read_bytes()
        except OSError as exc:
            raise DispatchError(f"qsub result rc unavailable: {exc}") from None
        if observed_rc != expected_rc:
            raise DispatchError("qsub result rc file is inconsistent")


def _validate_submit_object(
    submit: Mapping[str, object],
    *,
    snapshot: Snapshot,
    authorization_sha256: str,
    qsub_request_sha256: str,
    qsub_result_sha256: str,
) -> None:
    if (
        set(submit) != {
            "schema", "dispatch_id", "snapshot_manifest_sha256",
            "execution_closure_sha256", "policy_sha256",
            "authorization_sha256", "qsub_request_sha256",
            "qsub_result_sha256", "qsub_request_id_raw",
            "job_id_normalized",
        }
        or submit.get("schema") != "izanagi-test-submit-v2"
        or submit.get("dispatch_id") != snapshot.dispatch_id
        or submit.get("snapshot_manifest_sha256") != snapshot.manifest_sha256
        or submit.get("execution_closure_sha256")
        != snapshot.execution_closure_sha256
        or submit.get("policy_sha256") != snapshot.policy_sha256
        or submit.get("authorization_sha256") != authorization_sha256
        or submit.get("qsub_request_sha256") != qsub_request_sha256
        or submit.get("qsub_result_sha256") != qsub_result_sha256
        or not isinstance(submit.get("qsub_request_id_raw"), str)
        or not isinstance(submit.get("job_id_normalized"), str)
        or normalize_job_id(str(submit["qsub_request_id_raw"]))
        != submit["job_id_normalized"]
    ):
        raise DispatchError("submit receipt chain mismatch")


def _validate_worker_environment_object(
    worker_environment: Mapping[str, object],
    *,
    snapshot: Snapshot,
    observation: pegasus_policy.SiteObservation,
) -> None:
    expected_keys = {
        "schema", "dispatch_id", "snapshot_manifest_sha256",
        "execution_closure_sha256", "policy_sha256",
        "python_executable", "python_realpath", "python_version",
        "python_flags", "sys_path", "pytest_plugin_autoload",
        "environment", "pytest", "pytest_xdist", "site",
    }
    if (
        set(worker_environment) != expected_keys
        or worker_environment.get("schema")
        != "izanagi-test-worker-environment-v2"
        or worker_environment.get("dispatch_id") != snapshot.dispatch_id
        or worker_environment.get("snapshot_manifest_sha256")
        != snapshot.manifest_sha256
        or worker_environment.get("execution_closure_sha256")
        != snapshot.execution_closure_sha256
        or worker_environment.get("policy_sha256") != snapshot.policy_sha256
        or worker_environment.get("python_flags") != ["-B", "-s"]
        or worker_environment.get("pytest_plugin_autoload") is not False
        or type(worker_environment.get("sys_path")) is not list
        or not all(
            isinstance(item, str) for item in worker_environment["sys_path"]
        )
    ):
        raise DispatchError("worker environment receipt schema mismatch")
    executable = worker_environment.get("python_executable")
    realpath = worker_environment.get("python_realpath")
    version_text = worker_environment.get("python_version")
    try:
        observed_realpath = str(Path(str(executable)).resolve(strict=True))
        version_parts = tuple(int(part) for part in str(version_text).split("."))
    except (OSError, ValueError):
        observed_realpath = ""
        version_parts = ()
    if (
        not isinstance(executable, str)
        or not isinstance(realpath, str)
        or not Path(executable).is_absolute()
        or not Path(realpath).is_absolute()
        or observed_realpath != realpath
        or not isinstance(version_text, str)
        or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", str(
            version_text
        )) is None
        or version_parts < (3, 10)
    ):
        raise DispatchError("worker interpreter receipt is invalid")
    environment = worker_environment.get("environment")
    base_environment = {
        "PATH", "LANG", "LC_ALL", "TZ", "PYTHONNOUSERSITE",
        "PYTHONDONTWRITEBYTECODE", "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "PIP_NO_INDEX", "PIP_DISABLE_PIP_VERSION_CHECK", "PBS_JOBID",
        "IZANAGI_TEST_DISPATCH_ID", "IZANAGI_TEST_DISPATCH_DIR",
        "IZANAGI_TEST_SNAPSHOT_ROOT", "IZANAGI_TEST_WORKER_AUTH",
        "IZANAGI_TEST_RUNNER_RESULT",
    }
    if (
        type(environment) is not dict
        or set(environment) != base_environment | set(snapshot.runner_environment)
        or not all(
            isinstance(name, str)
            and isinstance(value, str)
            and "\x00" not in name
            and "\x00" not in value
            for name, value in environment.items()
        )
        or environment.get("LANG") != "C"
        or environment.get("LC_ALL") != "C"
        or environment.get("TZ") != "UTC"
        or environment.get("PYTHONNOUSERSITE") != "1"
        or environment.get("PYTHONDONTWRITEBYTECODE") != "1"
        or environment.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1"
        or environment.get("PIP_NO_INDEX") != "1"
        or environment.get("PIP_DISABLE_PIP_VERSION_CHECK") != "1"
        or not environment.get("PATH")
        or any(
            character in environment["PATH"] for character in "\x00\r\n"
        )
        or environment.get("PBS_JOBID") != observation.pbs_job_id_raw
        or environment.get("IZANAGI_TEST_DISPATCH_ID")
        != snapshot.dispatch_id
        or environment.get("IZANAGI_TEST_DISPATCH_DIR")
        != str(snapshot.dispatch_dir)
        or environment.get("IZANAGI_TEST_SNAPSHOT_ROOT")
        != str(snapshot.snapshot_root)
        or environment.get("IZANAGI_TEST_WORKER_AUTH")
        != str(snapshot.dispatch_dir / "pre-submit-authorization.json")
        or environment.get("IZANAGI_TEST_RUNNER_RESULT")
        != str(snapshot.dispatch_dir / "runner-result.json")
        or any(
            environment.get(name) != value
            for name, value in snapshot.runner_environment.items()
        )
    ):
        raise DispatchError("worker exec environment is not closed")
    site = worker_environment.get("site")
    if (
        type(site) is not dict
        or set(site) != {
            "hostname_raw", "hostname_canonical", "pbs_job_id_raw",
            "pbs_job_id_normalized", "affinity_cpus", "site_kind",
        }
        or site.get("hostname_raw") != observation.hostname_raw
        or site.get("hostname_canonical") != observation.hostname_canonical
        or site.get("pbs_job_id_raw") != observation.pbs_job_id_raw
        or site.get("pbs_job_id_normalized")
        != observation.pbs_job_id_normalized
        or site.get("affinity_cpus") != list(observation.affinity_cpus)
        or site.get("site_kind") != observation.site_kind.value
    ):
        raise DispatchError("worker site receipt mismatch")
    for name, distribution_name in (
        ("pytest", "pytest"),
        ("pytest_xdist", "pytest-xdist"),
    ):
        receipt = worker_environment.get(name)
        if (
            type(receipt) is not dict
            or set(receipt) != {
                "name", "version", "root", "distribution_files",
                "distribution_files_sha256",
            }
            or receipt.get("name") != distribution_name
            or not isinstance(receipt.get("version"), str)
            or not isinstance(receipt.get("root"), str)
            or not Path(str(receipt["root"])).is_absolute()
            or not isinstance(receipt.get("distribution_files"), str)
            or not str(receipt["distribution_files"]).isdigit()
            or int(str(receipt["distribution_files"])) <= 0
            or _HEX64_RE.fullmatch(
                str(receipt.get("distribution_files_sha256"))
            ) is None
        ):
            raise DispatchError(f"worker dependency receipt is invalid: {name}")


def _runner_claim(marker_path: Path) -> Path:
    return marker_path.parent / "runner-claim.json"


def claim_worker(
    *,
    marker_path: Path,
    observation: pegasus_policy.SiteObservation,
    repo_root: Path,
    worker_environment_sha256: str,
) -> Mapping[str, object]:
    authorization, auth_raw = _load_exact_json(marker_path)
    submit, submit_raw = _load_exact_json(marker_path.parent / "submit-receipt.json")
    request, request_raw = _load_exact_json(marker_path.parent / "qsub-request.json")
    qsub_result, qsub_result_raw = _load_exact_json(
        marker_path.parent / "qsub-result.json"
    )
    worker_environment, worker_environment_raw = _load_exact_json(
        marker_path.parent / "worker-environment.json"
    )
    manifest, manifest_raw = _load_exact_json(marker_path.parent / "snapshot-manifest.json")
    if set(authorization) != {
        "schema", "dispatch_id", "snapshot_manifest_sha256",
        "execution_closure_sha256", "policy_sha256",
        "qsub_request_sha256", "snapshot_root",
    } or authorization.get("schema") != "izanagi-test-pre-submit-v2":
        raise DispatchError("worker authorization schema mismatch")
    if set(submit) != {
        "schema", "dispatch_id", "snapshot_manifest_sha256",
        "execution_closure_sha256", "policy_sha256",
        "authorization_sha256", "qsub_request_sha256",
        "qsub_result_sha256", "qsub_request_id_raw", "job_id_normalized",
    } or submit.get("schema") != "izanagi-test-submit-v2":
        raise DispatchError("submit receipt schema mismatch")
    if manifest.get("schema") != "izanagi-test-snapshot-v2":
        raise DispatchError("snapshot manifest schema mismatch")
    if request.get("schema") != "izanagi-test-qsub-request-v1":
        raise DispatchError("qsub request schema mismatch")
    if qsub_result.get("schema") != "izanagi-test-qsub-result-v1":
        raise DispatchError("qsub result schema mismatch")
    if worker_environment.get("schema") != "izanagi-test-worker-environment-v2":
        raise DispatchError("worker environment schema mismatch")
    dispatch_id = authorization.get("dispatch_id")
    if (
        not isinstance(dispatch_id, str)
        or _DISPATCH_ID_RE.fullmatch(dispatch_id) is None
        or submit.get("dispatch_id") != dispatch_id
        or request.get("dispatch_id") != dispatch_id
        or qsub_result.get("dispatch_id") != dispatch_id
        or worker_environment.get("dispatch_id") != dispatch_id
        or manifest.get("dispatch_id") != dispatch_id
    ):
        raise DispatchError("dispatch identity mismatch")
    manifest_sha = sha256_bytes(manifest_raw)
    if (
        authorization.get("snapshot_manifest_sha256") != manifest_sha
        or submit.get("snapshot_manifest_sha256") != manifest_sha
    ):
        raise DispatchError("snapshot identity mismatch")
    closure_sha = manifest.get("execution_closure_sha256")
    policy = manifest.get("policy")
    if (
        not isinstance(closure_sha, str)
        or _HEX64_RE.fullmatch(closure_sha) is None
        or type(policy) is not dict
        or set(policy) != {"path", "sha256"}
        or _HEX64_RE.fullmatch(str(policy.get("sha256"))) is None
        or authorization.get("execution_closure_sha256") != closure_sha
        or submit.get("execution_closure_sha256") != closure_sha
        or authorization.get("policy_sha256") != policy["sha256"]
        or submit.get("policy_sha256") != policy["sha256"]
    ):
        raise DispatchError("snapshot closure/policy identity mismatch")
    auth_sha = sha256_bytes(auth_raw)
    if submit.get("authorization_sha256") != auth_sha:
        raise DispatchError("authorization identity mismatch")
    request_sha = sha256_bytes(request_raw)
    result_sha = sha256_bytes(qsub_result_raw)
    snapshot = snapshot_from_dispatch(marker_path.parent)
    _validate_qsub_request_object(request, snapshot=snapshot)
    _validate_authorization_object(
        authorization,
        snapshot=snapshot,
        qsub_request_sha256=request_sha,
    )
    _validate_qsub_result_object(
        qsub_result,
        snapshot=snapshot,
        qsub_request_sha256=request_sha,
        request=request,
        verify_files=True,
    )
    _validate_submit_object(
        submit,
        snapshot=snapshot,
        authorization_sha256=auth_sha,
        qsub_request_sha256=request_sha,
        qsub_result_sha256=result_sha,
    )
    _validate_worker_environment_object(
        worker_environment,
        snapshot=snapshot,
        observation=observation,
    )
    if (
        authorization.get("qsub_request_sha256") != request_sha
        or submit.get("qsub_request_sha256") != request_sha
        or qsub_result.get("qsub_request_sha256") != request_sha
        or submit.get("qsub_result_sha256") != result_sha
    ):
        raise DispatchError("qsub receipt chain mismatch")
    if worker_environment_sha256 != sha256_bytes(worker_environment_raw):
        raise DispatchError("worker environment identity mismatch")
    if sha256_bytes(submit_raw) != sha256_file(marker_path.parent / "submit-receipt.json"):
        raise DispatchError("submit receipt changed while claiming")
    if (
        not isinstance(submit.get("qsub_request_id_raw"), str)
        or normalize_job_id(str(submit["qsub_request_id_raw"]))
        != submit.get("job_id_normalized")
    ):
        raise DispatchError("submit scheduler identity mismatch")
    if observation.site_kind is not pegasus_policy.PEGASUS_COMPUTE:
        raise DispatchError("worker is not on a Pegasus compute host")
    if submit.get("job_id_normalized") != observation.pbs_job_id_normalized:
        raise DispatchError("worker PBS identity mismatch")
    expected_root = Path(str(authorization.get("snapshot_root"))).resolve(strict=True)
    if repo_root.resolve(strict=True) != expected_root:
        raise DispatchError("worker source root mismatch")
    verify_execution_closure(snapshot)
    claim = {
        "schema": "izanagi-test-runner-claim-v2",
        "dispatch_id": dispatch_id,
        "snapshot_manifest_sha256": manifest_sha,
        "execution_closure_sha256": closure_sha,
        "policy_sha256": policy["sha256"],
        "authorization_sha256": auth_sha,
        "qsub_request_sha256": request_sha,
        "qsub_result_sha256": result_sha,
        "submit_receipt_sha256": sha256_bytes(submit_raw),
        "worker_environment_sha256": worker_environment_sha256,
        "pbs_job_id_raw": observation.pbs_job_id_raw,
        "job_id_normalized": observation.pbs_job_id_normalized,
        "hostname_raw": observation.hostname_raw,
        "hostname_canonical": observation.hostname_canonical,
        "affinity_cpus": list(observation.affinity_cpus),
    }
    create_file(_runner_claim(marker_path), _canonical_json(claim))
    return claim


def authorize_runner(
    *,
    marker_path: Path,
    observation: pegasus_policy.SiteObservation,
    repo_root: Path,
) -> dict[str, object]:
    claim, raw = _load_exact_json(_runner_claim(marker_path))
    expected = {
        "schema", "dispatch_id", "snapshot_manifest_sha256",
        "execution_closure_sha256", "policy_sha256",
        "authorization_sha256", "qsub_request_sha256",
        "qsub_result_sha256", "submit_receipt_sha256",
        "worker_environment_sha256", "pbs_job_id_raw", "job_id_normalized",
        "hostname_raw", "hostname_canonical", "affinity_cpus",
    }
    if (
        set(claim) != expected
        or claim.get("schema") != "izanagi-test-runner-claim-v2"
    ):
        raise DispatchError("runner claim keys mismatch")
    digest_names = (
        "snapshot_manifest_sha256", "execution_closure_sha256",
        "policy_sha256", "authorization_sha256", "qsub_request_sha256",
        "qsub_result_sha256", "submit_receipt_sha256",
        "worker_environment_sha256",
    )
    if any(
        not isinstance(claim[name], str)
        or _HEX64_RE.fullmatch(str(claim[name])) is None
        for name in digest_names
    ):
        raise DispatchError("runner claim digest is invalid")
    if observation.site_kind is not pegasus_policy.PEGASUS_COMPUTE:
        raise DispatchError("runner is not on a Pegasus compute host")
    if (
        claim["pbs_job_id_raw"] != observation.pbs_job_id_raw
        or claim["job_id_normalized"] != observation.pbs_job_id_normalized
        or claim["hostname_raw"] != observation.hostname_raw
        or claim["hostname_canonical"] != observation.hostname_canonical
        or claim["affinity_cpus"] != list(observation.affinity_cpus)
    ):
        raise DispatchError("runner site/affinity identity mismatch")
    authorization, auth_raw = _load_exact_json(marker_path)
    if claim["authorization_sha256"] != sha256_bytes(auth_raw):
        raise DispatchError("runner authorization hash mismatch")
    manifest, manifest_raw = _load_exact_json(marker_path.parent / "snapshot-manifest.json")
    if claim["snapshot_manifest_sha256"] != sha256_bytes(manifest_raw):
        raise DispatchError("runner snapshot hash mismatch")
    for name, filename in (
        ("qsub_request_sha256", "qsub-request.json"),
        ("qsub_result_sha256", "qsub-result.json"),
        ("submit_receipt_sha256", "submit-receipt.json"),
        ("worker_environment_sha256", "worker-environment.json"),
    ):
        _, receipt_raw = _load_exact_json(marker_path.parent / filename)
        if claim[name] != sha256_bytes(receipt_raw):
            raise DispatchError(f"runner receipt hash mismatch: {filename}")
    if Path(str(authorization["snapshot_root"])).resolve(strict=True) != repo_root.resolve(strict=True):
        raise DispatchError("runner source identity mismatch")
    snapshot = snapshot_from_dispatch(marker_path.parent)
    if verify_execution_closure(snapshot) != claim["execution_closure_sha256"]:
        raise DispatchError("runner execution closure mismatch")
    # A second process cannot create the claim; this read path is reached only
    # by the process exec'd immediately after claim_worker.
    result = dict(claim)
    result["runner_claim_sha256"] = sha256_bytes(raw)
    consumed = marker_path.parent / "runner-consumed.json"
    create_file(consumed, _canonical_json({
        "schema": "izanagi-test-runner-consumed-v1",
        "dispatch_id": claim["dispatch_id"],
        "runner_claim_sha256": result["runner_claim_sha256"],
        "execution_closure_sha256": claim["execution_closure_sha256"],
    }))
    return result


def parse_qstat(
    result: CommandResult,
    *,
    expected_job_id_normalized: str,
    expected_group: str,
    was_visible: bool,
) -> PollStatus:
    if (
        result.returncode != 0
        or result.timed_out
        or result.output_limited
        or result.signal is not None
    ):
        return PollStatus("transient" if was_visible else "not-visible", None, False, ())
    request_ids = _QSTAT_DETAIL_ID_RE.findall(result.stdout)
    if len(request_ids) != 1:
        raise DispatchError("per-job qstat lacks one exact Request ID")
    observed_job_id = normalize_job_id(request_ids[0])
    expected_job_id = normalize_job_id(expected_job_id_normalized)
    if observed_job_id != expected_job_id:
        raise DispatchError(
            "per-job qstat Request ID mismatch: "
            f"expected={expected_job_id!r} observed={observed_job_id!r}"
        )
    groups = _QSTAT_DETAIL_GROUP_RE.findall(result.stdout)
    if len(groups) != 1:
        raise DispatchError("per-job qstat lacks one exact Group Name")
    if groups[0] != expected_group:
        raise DispatchError(
            "per-job qstat Group Name mismatch: "
            f"expected={expected_group!r} observed={groups[0]!r}"
        )
    match = _QSTAT_STATE_RE.search(result.stdout)
    if match is None:
        raise DispatchError("qstat output has no Current State")
    raw = match.group(1).strip()
    folded = raw.lower().replace("_", "-")
    state = _QSTAT_STATES.get(folded)
    if state is None:
        raise DispatchError(f"qstat Current State is unknown: {raw!r}")
    hosts = tuple(sorted(set(_BNODE_RE.findall(result.stdout))))
    return PollStatus(state, raw, True, hosts)


def parse_qstat_candidates(
    stdout: str,
    *,
    exact_job_name: str,
    expected_user: str,
    expected_queue: str,
    expected_account: str,
    expected_group: str,
    not_before_epoch_s: float,
) -> tuple[SchedulerCandidate, ...]:
    """Parse the measured NQSV ``qstat -f`` all-request format."""
    if (
        not isinstance(stdout, str)
        or not isinstance(exact_job_name, str)
        or _SAFE_NAME_RE.fullmatch(exact_job_name) is None
        or not all(
            isinstance(value, str) and value
            for value in (
                expected_user,
                expected_queue,
                expected_account,
                expected_group,
            )
        )
        or type(not_before_epoch_s) not in (int, float)
        or isinstance(not_before_epoch_s, bool)
        or not_before_epoch_s < 0
    ):
        raise DispatchError("scheduler lookup input is unsafe")
    request_matches = list(_QSTAT_DETAIL_ID_RE.finditer(stdout))
    if not request_matches:
        if stdout.strip():
            raise DispatchError("scheduler lookup output is malformed")
        return ()
    if stdout[:request_matches[0].start()].strip():
        raise DispatchError("scheduler lookup output has an invalid prefix")
    candidates: list[SchedulerCandidate] = []
    for index, request_match in enumerate(request_matches):
        block_end = (
            request_matches[index + 1].start()
            if index + 1 < len(request_matches)
            else len(stdout)
        )
        body = stdout[request_match.end():block_end]
        names = _QSTAT_DETAIL_NAME_RE.findall(body)
        users = _QSTAT_DETAIL_USER_RE.findall(body)
        groups = _QSTAT_DETAIL_GROUP_RE.findall(body)
        queues = _QSTAT_DETAIL_QUEUE_RE.findall(body)
        accounts = _QSTAT_DETAIL_ACCOUNT_RE.findall(body)
        created_values = _QSTAT_DETAIL_CREATED_RE.findall(body)
        states = _QSTAT_STATE_RE.findall(body)
        if (
            len(names) != 1
            or len(users) != 1
            or len(groups) != 1
            or len(queues) != 1
            or len(accounts) != 1
            or len(created_values) != 1
            or len(states) != 1
        ):
            raise DispatchError(
                "scheduler lookup request block is malformed"
            )
        request_id_raw = request_match.group(1)
        normalized = normalize_job_id(request_id_raw)
        request_name = names[0].strip()
        if (
            not request_name
            or any(character in request_name for character in "\x00\r\n")
        ):
            raise DispatchError("scheduler lookup request name is malformed")
        raw_state = states[0].strip()
        state = _QSTAT_STATES.get(raw_state.lower().replace("_", "-"))
        if state is None:
            raise DispatchError(
                f"scheduler lookup Current State is unknown: {raw_state!r}"
            )
        created_epoch_s = _nqsv_created_epoch(created_values[0].strip())
        queue = queues[0].strip()
        execution_hosts = tuple(sorted(set(_BNODE_RE.findall(body))))
        identity_matches = (
            request_name == exact_job_name
            and users[0] == expected_user
            and groups[0] == expected_group
            and queue.split("@", 1)[0] == expected_queue
            and accounts[0] == expected_account
            and created_epoch_s >= int(not_before_epoch_s)
        )
        if identity_matches:
            if state == "running" and len(execution_hosts) != 1:
                raise DispatchError(
                    "scheduler lookup running candidate lacks one execution host"
                )
            candidates.append(SchedulerCandidate(
                request_id_raw=request_id_raw,
                job_id_normalized=normalized,
                request_name=request_name,
                user_name=users[0],
                group_name=groups[0],
                queue=queue,
                account=accounts[0],
                created_epoch_s=created_epoch_s,
                state=state,
                execution_hosts=execution_hosts,
            ))
    return tuple(candidates)


def _file_receipt(
    path: Path,
    *,
    byte_limit: int | None = None,
) -> Mapping[str, object] | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise DispatchError(f"spool is not a regular file: {path.name}")
    if byte_limit is not None and info.st_size > byte_limit:
        raise DispatchError(f"spool exceeds byte limit: {path.name}")
    digest = sha256_file(path)
    after = path.lstat()
    if (
        after.st_dev != info.st_dev
        or after.st_ino != info.st_ino
        or after.st_size != info.st_size
        or stat.S_IMODE(after.st_mode) != stat.S_IMODE(info.st_mode)
    ):
        raise DispatchError(f"spool changed while hashing: {path.name}")
    return {
        "path": str(path),
        "size": info.st_size,
        "sha256": digest,
    }


def replay_spool(path: Path, destination: Any, *, byte_limit: int) -> int:
    """Stream at most ``byte_limit`` bytes without loading a spool into RAM."""

    emitted = 0
    with path.open("rb") as stream:
        while emitted < byte_limit:
            block = stream.read(min(64 * 1024, byte_limit - emitted))
            if not block:
                break
            try:
                destination.write(block)
            except TypeError:
                destination.write(block.decode("utf-8", "replace"))
            emitted += len(block)
    flush = getattr(destination, "flush", None)
    if callable(flush):
        flush()
    return emitted


def validate_nqsv_accounting(
    stderr_text: str,
    job_id_normalized: str,
    *,
    expected_group: str,
) -> Mapping[str, object]:
    if type(stderr_text) is not str:
        raise DispatchError("terminal NQSV accounting must be text")
    if "\r" in stderr_text or not stderr_text.endswith("\n"):
        raise DispatchError(
            "terminal NQSV accounting footer is not newline terminated"
        )
    all_lines = stderr_text.splitlines()
    if len(all_lines) < 14 or all_lines[-1] != _NQSV_ACCOUNTING_SEPARATOR:
        raise DispatchError(
            "terminal NQSV accounting footer is not the final stderr block"
        )
    lines = tuple(all_lines[-14:])
    patterns = (
        re.compile(r"Request ID:[ \t]+(\S+)\Z", re.ASCII),
        re.compile(r"Request Name:[ \t]+\S(?:.*\S)?\Z", re.ASCII),
        re.compile(r"Queue:[ \t]+\S(?:.*\S)?\Z", re.ASCII),
        re.compile(r"Number of Jobs:[ \t]+[0-9]+\Z", re.ASCII),
        re.compile(r"User Name:[ \t]+\S+\Z", re.ASCII),
        re.compile(r"Group Name:[ \t]+(\S+)\Z", re.ASCII),
        re.compile(r"Created Request Time:[ \t]+\S(?:.*\S)?\Z", re.ASCII),
        re.compile(r"Started Request Time:[ \t]+\S(?:.*\S)?\Z", re.ASCII),
        re.compile(r"Ended Request Time:[ \t]+\S(?:.*\S)?\Z", re.ASCII),
        re.compile(r"Resources Information:\Z", re.ASCII),
        re.compile(r"[ \t]+Elapse:[ \t]+\S(?:.*\S)?\Z", re.ASCII),
        re.compile(r"[ \t]+Remaining Elapse:[ \t]+\S(?:.*\S)?\Z", re.ASCII),
    )
    if (
        lines[0] != _NQSV_ACCOUNTING_SEPARATOR
        or lines[-1] != _NQSV_ACCOUNTING_SEPARATOR
    ):
        raise DispatchError("terminal NQSV accounting separators are invalid")
    matches = [
        pattern.fullmatch(line)
        for pattern, line in zip(patterns, lines[1:-1])
    ]
    if len(matches) != len(patterns) or any(match is None for match in matches):
        raise DispatchError(
            "terminal NQSV accounting footer field order/schema is invalid"
        )
    observed = normalize_job_id(matches[0].group(1))
    expected = normalize_job_id(job_id_normalized)
    if observed != expected:
        raise DispatchError(
            "terminal NQSV accounting Request ID mismatch: "
            f"expected={expected!r} observed={observed!r}"
        )
    observed_group = matches[5].group(1)
    if observed_group != expected_group:
        raise DispatchError(
            "terminal NQSV accounting Group Name mismatch: "
            f"expected={expected_group!r} observed={observed_group!r}"
        )
    return {
        "schema": "izanagi-test-nqsv-accounting-v1",
        "job_id_normalized": expected,
        "lines": list(lines),
        "lines_sha256": sha256_bytes(("\n".join(lines) + "\n").encode("utf-8")),
    }


def validate_runner_result(
    path: Path,
    *,
    snapshot: Snapshot,
    authorization_sha256: str,
    pbs_job_id_raw: str,
    job_id_normalized: str,
    qsub_request_sha256: str | None = None,
    qsub_result_sha256: str | None = None,
    submit_receipt_sha256: str | None = None,
) -> Mapping[str, object]:
    result, _ = _load_exact_json(path)
    return validate_runner_result_object(
        result,
        snapshot=snapshot,
        authorization_sha256=authorization_sha256,
        pbs_job_id_raw=pbs_job_id_raw,
        job_id_normalized=job_id_normalized,
        qsub_request_sha256=qsub_request_sha256,
        qsub_result_sha256=qsub_result_sha256,
        submit_receipt_sha256=submit_receipt_sha256,
    )


def validate_runner_result_object(
    result: Mapping[str, object],
    *,
    snapshot: Snapshot,
    authorization_sha256: str,
    pbs_job_id_raw: str,
    job_id_normalized: str,
    qsub_request_sha256: str | None = None,
    qsub_result_sha256: str | None = None,
    submit_receipt_sha256: str | None = None,
) -> Mapping[str, object]:
    expected = {
        "schema", "dispatch_id", "snapshot_manifest_sha256",
        "execution_closure_sha256", "policy_sha256",
        "authorization_sha256", "qsub_request_sha256",
        "qsub_result_sha256", "submit_receipt_sha256",
        "runner_claim_sha256", "worker_environment_sha256",
        "pbs_job_id_raw", "job_id_normalized",
        "hostname_raw", "hostname_canonical", "affinity_cpus",
        "runner_exit_status", "runner_signal",
        "pytest_exit_status", "pytest_signal", "runner_stage",
        "task_run_attempted", "task_run_event_id", "task_run_event",
    }
    if set(result) != expected or result["schema"] != "izanagi-test-runner-result-v2":
        raise DispatchError("runner result schema mismatch")
    if (
        result["dispatch_id"] != snapshot.dispatch_id
        or result["snapshot_manifest_sha256"] != snapshot.manifest_sha256
        or result["execution_closure_sha256"]
        != snapshot.execution_closure_sha256
        or result["policy_sha256"] != snapshot.policy_sha256
        or result["authorization_sha256"] != authorization_sha256
        or result["pbs_job_id_raw"] != pbs_job_id_raw
        or result["job_id_normalized"] != job_id_normalized
    ):
        raise DispatchError("runner result identity mismatch")
    if any(
        not isinstance(result[name], str)
        or _HEX64_RE.fullmatch(str(result[name])) is None
        for name in (
            "snapshot_manifest_sha256", "execution_closure_sha256",
            "policy_sha256", "authorization_sha256",
            "qsub_request_sha256", "qsub_result_sha256",
            "submit_receipt_sha256", "runner_claim_sha256",
            "worker_environment_sha256",
        )
    ):
        raise DispatchError("runner result digest is invalid")
    for expected_value, name in (
        (qsub_request_sha256, "qsub_request_sha256"),
        (qsub_result_sha256, "qsub_result_sha256"),
        (submit_receipt_sha256, "submit_receipt_sha256"),
    ):
        if expected_value is not None and result[name] != expected_value:
            raise DispatchError(f"runner result receipt hash mismatch: {name}")
    if (
        not isinstance(result["pbs_job_id_raw"], str)
        or normalize_job_id(result["pbs_job_id_raw"]) != job_id_normalized
    ):
        raise DispatchError("runner result PBS identity mismatch")
    if (
        type(result["runner_exit_status"]) is not int
        or not 0 <= int(result["runner_exit_status"]) <= 255
    ):
        raise DispatchError("runner result child status is invalid")
    runner_signal = result["runner_signal"]
    if (
        runner_signal is not None
        and (
            type(runner_signal) is not int
            or not 1 <= runner_signal <= 64
            or result["runner_exit_status"] != 128 + runner_signal
        )
    ):
        raise DispatchError("runner result child signal is invalid")
    if (
        result["pytest_exit_status"] is not None
        and (
            type(result["pytest_exit_status"]) is not int
            or not 0 <= int(result["pytest_exit_status"]) <= 255
        )
    ):
        raise DispatchError("runner result pytest status is invalid")
    pytest_signal = result["pytest_signal"]
    if (
        (result["pytest_exit_status"] is None) != (pytest_signal is None)
        and pytest_signal is not None
    ):
        raise DispatchError("runner result pytest signal/status is inconsistent")
    if (
        pytest_signal is not None
        and (
            type(pytest_signal) is not int
            or not 1 <= pytest_signal <= 64
            or result["pytest_exit_status"] != 128 + pytest_signal
        )
    ):
        raise DispatchError("runner result pytest signal is invalid")
    if (
        not isinstance(result["runner_stage"], str)
        or result["runner_stage"] not in {
            "worker-policy", "deletion-preflight", "ruleops-preflight",
            "submodule-preflight", "xdist-environment", "pytest",
        }
        or (
            result["runner_stage"] == "pytest"
            and (
                result["pytest_exit_status"] != result["runner_exit_status"]
                or result["pytest_signal"] != result["runner_signal"]
            )
        )
        or (
            result["runner_stage"] != "pytest"
            and (
                result["pytest_exit_status"] is not None
                or result["pytest_signal"] is not None
            )
        )
    ):
        raise DispatchError("runner result stage/status mismatch")
    if type(result["task_run_attempted"]) is not bool:
        raise DispatchError("runner result task-run attempt is invalid")
    if result["task_run_event_id"] is not None and not isinstance(
        result["task_run_event_id"], str
    ):
        raise DispatchError("runner result task-run event is invalid")
    if (
        isinstance(result["task_run_event_id"], str)
        and re.fullmatch(r"[0-9a-f]{16}", result["task_run_event_id"]) is None
    ):
        raise DispatchError("runner result task-run event ID is invalid")
    event_receipt = result["task_run_event"]
    if event_receipt is not None:
        if (
            type(event_receipt) is not dict
            or set(event_receipt) != {"path", "size", "sha256", "event_id"}
            or event_receipt.get("event_id") != result["task_run_event_id"]
            or type(event_receipt.get("size")) is not int
            or int(event_receipt["size"]) < 0
            or _HEX64_RE.fullmatch(str(event_receipt.get("sha256"))) is None
            or not isinstance(event_receipt.get("path"), str)
        ):
            raise DispatchError("runner result task-run event receipt is invalid")
    if result["task_run_attempted"]:
        task_run_id = snapshot.runner_environment.get("IZANAGI_TASK_RUN_ID")
        task_run_root = snapshot.runner_environment.get(
            "IZANAGI_TASK_RUNS_ROOT"
        )
        if not isinstance(task_run_id, str) or not isinstance(task_run_root, str):
            raise DispatchError("runner task-run durable root is not bound")
    elif result["task_run_event_id"] is not None or event_receipt is not None:
        raise DispatchError("runner task-run event exists without an attempt")
    if event_receipt is not None:
        task_run_id = snapshot.runner_environment["IZANAGI_TASK_RUN_ID"]
        task_run_root = snapshot.runner_environment["IZANAGI_TASK_RUNS_ROOT"]
        expected_path = (
            Path(str(task_run_root)) / str(task_run_id) / "events.jsonl"
        ).resolve(strict=False)
        if Path(str(event_receipt["path"])).resolve(strict=False) != expected_path:
            raise DispatchError("runner task-run event path is not canonical")
        try:
            info = expected_path.lstat()
            raw = expected_path.read_bytes()
        except OSError as exc:
            raise DispatchError(
                f"runner task-run event ledger is unavailable: {exc}"
            ) from None
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or len(raw) > 8 * 1024 * 1024
            or len(raw) < int(event_receipt["size"])
        ):
            raise DispatchError("runner task-run event ledger is unsafe")
        receipt_size = int(event_receipt["size"])
        if sha256_bytes(raw[:receipt_size]) != event_receipt["sha256"]:
            raise DispatchError("runner task-run event ledger hash mismatch")
        try:
            matches = [
                item
                for line in raw.splitlines()
                for item in (json.loads(line),)
                if type(item) is dict
                and item.get("event_id") == result["task_run_event_id"]
            ]
        except json.JSONDecodeError as exc:
            raise DispatchError(
                f"runner task-run event ledger is invalid: {exc}"
            ) from None
        if len(matches) != 1:
            raise DispatchError("runner task-run durable event is not unique")
    if (
        not isinstance(result["hostname_raw"], str)
        or not isinstance(result["hostname_canonical"], str)
        or type(result["affinity_cpus"]) is not list
        or not result["affinity_cpus"]
        or any(type(cpu) is not int or cpu < 0 for cpu in result["affinity_cpus"])
    ):
        raise DispatchError("runner result host/affinity receipt is invalid")
    return result


def cancel_job(
    *,
    scheduler: Scheduler,
    job_id_normalized: str,
    policy: DispatchPolicy,
    journal_path: Path,
    clock: Callable[[], float],
    sleep: Callable[[float], None],
    reason: str,
    recovery: Mapping[str, object] | None = None,
    filesystem: MonitorFilesystem | None = None,
) -> bool:
    fs = PathMonitorFilesystem() if filesystem is None else filesystem
    command_environment = scheduler_environment()
    normalized = normalize_job_id(job_id_normalized)
    recovery_record = dict(recovery or {})
    cancel_id = sha256_bytes(_canonical_json({
        "job_id_normalized": normalized,
        "reason": reason,
        "recovery": recovery_record,
    }))[:16]
    payloads = _journal_payloads(journal_path) if journal_path.exists() else ()
    cancel_intents = [
        payload for payload in payloads
        if payload.get("event") == "cancel-intent"
        and payload.get("job_id_normalized") == normalized
    ]
    qdel_attempts = [
        payload for payload in payloads
        if payload.get("event") == "qdel-attempt"
        and payload.get("job_id_normalized") == normalized
    ]
    intent_keys = {
        "event", "cancel_id", "job_id_normalized", "reason", "recovery",
        "monotonic_s",
    }
    attempt_keys = {
        "event", "cancel_id", "job_id_normalized", "attempt", "returncode",
        "signal", "timed_out", "output_limited", "raw", "monotonic_s",
    }
    if any(
        set(payload) != intent_keys
        or not isinstance(payload.get("cancel_id"), str)
        or not isinstance(payload.get("reason"), str)
        or type(payload.get("recovery")) is not dict
        or type(payload.get("monotonic_s")) not in (int, float)
        for payload in cancel_intents
    ):
        raise DispatchError("cancel WAL intent schema is invalid")
    if any(
        set(payload) != attempt_keys
        or not isinstance(payload.get("cancel_id"), str)
        or type(payload.get("attempt")) is not int
        or int(payload["attempt"]) <= 0
        or type(payload.get("returncode")) is not int
        or type(payload.get("timed_out")) is not bool
        or type(payload.get("output_limited")) is not bool
        or (
            payload.get("signal") is not None
            and type(payload.get("signal")) is not int
        )
        or type(payload.get("raw")) is not dict
        or type(payload.get("monotonic_s")) not in (int, float)
        or len([
            intent for intent in cancel_intents
            if intent.get("cancel_id") == payload.get("cancel_id")
        ]) != 1
        for payload in qdel_attempts
    ):
        raise DispatchError("cancel WAL attempt schema/pairing is invalid")
    # A durable qdel success is global to this exact scheduler ID.  In
    # particular, an outer controller exception must not issue a second qdel
    # after monitor_job already compensated the request.
    successful = [
        payload for payload in payloads
        if payload.get("event") == "qdel-succeeded"
        and payload.get("job_id_normalized") == normalized
    ]
    success_keys = {
        "event", "cancel_id", "job_id_normalized", "attempt", "monotonic_s",
    }
    if len(successful) > 1 or any(
        set(payload) != success_keys
        or type(payload.get("attempt")) is not int
        or type(payload.get("monotonic_s")) not in (int, float)
        or len([
            attempt for attempt in qdel_attempts
            if attempt.get("cancel_id") == payload.get("cancel_id")
            and attempt.get("attempt") == payload.get("attempt")
            and attempt.get("returncode") == 0
            and attempt.get("signal") is None
            and attempt.get("timed_out") is False
            and attempt.get("output_limited") is False
        ]) != 1
        for payload in successful
    ):
        raise DispatchError("cancel WAL success latch is invalid")
    if successful:
        return True
    durable_successes = [
        payload for payload in qdel_attempts
        if payload.get("returncode") == 0
        and payload.get("signal") is None
        and payload.get("timed_out") is False
        and payload.get("output_limited") is False
    ]
    if durable_successes:
        prior_success = durable_successes[-1]
        append_journal(journal_path, {
            "event": "qdel-succeeded",
            "cancel_id": prior_success["cancel_id"],
            "job_id_normalized": normalized,
            "attempt": prior_success["attempt"],
            "monotonic_s": clock(),
        })
        return True
    intents = [
        payload for payload in payloads
        if payload.get("event") == "cancel-intent"
        and payload.get("cancel_id") == cancel_id
        and payload.get("job_id_normalized") == normalized
    ]
    if len(intents) > 1:
        raise DispatchError("cancel WAL has duplicate intent")
    if not intents:
        append_journal(journal_path, {
            "event": "cancel-intent",
            "cancel_id": cancel_id,
            "job_id_normalized": normalized,
            "reason": reason,
            "recovery": recovery_record,
            "monotonic_s": clock(),
        })
    attempts = [
        payload for payload in payloads
        if payload.get("event") == "qdel-attempt"
        and payload.get("cancel_id") == cancel_id
        and payload.get("job_id_normalized") == normalized
    ]
    attempt_numbers = [payload.get("attempt") for payload in attempts]
    if (
        any(type(value) is not int for value in attempt_numbers)
        or attempt_numbers != list(range(1, len(attempt_numbers) + 1))
        or len(attempts) > policy.qdel_attempts
    ):
        raise DispatchError("cancel WAL attempt sequence is invalid")
    for attempt in range(len(attempts) + 1, policy.qdel_attempts + 1):
        result = scheduler.run(
            ("qdel", normalized),
            timeout=policy.command_timeout_s,
            environment=command_environment,
        )
        raw_receipt = fs.record_command(
            journal_path.parent, "qdel", attempt, result,
        )
        append_journal(journal_path, {
            "event": "qdel-attempt",
            "cancel_id": cancel_id,
            "job_id_normalized": normalized,
            "attempt": attempt,
            "returncode": result.returncode,
            "signal": result.signal,
            "timed_out": result.timed_out,
            "output_limited": result.output_limited,
            "raw": raw_receipt,
            "monotonic_s": clock(),
        })
        if (
            result.returncode == 0
            and result.signal is None
            and not result.timed_out
            and not result.output_limited
        ):
            append_journal(journal_path, {
                "event": "qdel-succeeded",
                "cancel_id": cancel_id,
                "job_id_normalized": normalized,
                "attempt": attempt,
                "monotonic_s": clock(),
            })
            return True
        if attempt < policy.qdel_attempts:
            sleep(policy.qdel_retry_interval_s)
    return False


_FINAL_KEYS = {
    "schema", "dispatch_id", "snapshot_manifest_sha256",
    "execution_closure_sha256", "policy_sha256",
    "qsub_request_sha256", "authorization_sha256",
    "qsub_result_sha256", "submit_receipt_sha256",
    "qsub_request_id_raw", "pbs_job_id_raw", "job_id_normalized",
    "dispatch_outcome", "controller_exit_status", "controller_signal",
    "child_exit_status", "child_signal", "pytest_exit_status",
    "pytest_signal", "runner_stage", "runner_result",
    "worker_environment", "runner_claim", "task_run_attempted",
    "task_run_event_id", "task_run_event", "stdout", "stderr",
    "accounting", "terminal_phase", "qsub_started_epoch_s",
    "absolute_deadline_epoch_s", "journal_head_sha256", "failure_reason",
}


def _status_pair_valid(status: object, process_signal: object) -> bool:
    if type(status) is not int or not 0 <= status <= 255:
        return False
    if process_signal is None:
        return True
    return (
        type(process_signal) is int
        and 1 <= process_signal <= 64
        and status == 128 + process_signal
    )


def _receipt_matches_file(
    receipt: Mapping[str, object],
    dispatch_dir: Path,
) -> bool:
    if set(receipt) != {"path", "size", "sha256"}:
        return False
    try:
        path = Path(str(receipt["path"]))
        resolved_parent = path.parent.resolve(strict=True)
        expected_parent = dispatch_dir.resolve(strict=True)
        info = path.lstat()
    except (OSError, ValueError):
        return False
    return (
        resolved_parent == expected_parent
        and stat.S_ISREG(info.st_mode)
        and not stat.S_ISLNK(info.st_mode)
        and type(receipt["size"]) is int
        and receipt["size"] == info.st_size
        and isinstance(receipt["sha256"], str)
        and _HEX64_RE.fullmatch(str(receipt["sha256"])) is not None
        and receipt["sha256"] == sha256_file(path)
    )


def _validate_scheduler_lookup_chain(
    *,
    snapshot: Snapshot,
    policy: DispatchPolicy,
    qsub_request_sha256: str,
    qsub_result_sha256: str,
    submit: Mapping[str, object] | None,
    final: Mapping[str, object],
) -> None:
    payloads = _journal_payloads(
        snapshot.dispatch_dir / "dispatch-journal.jsonl"
    )
    request, request_raw = _load_exact_json(
        snapshot.dispatch_dir / "qsub-request.json"
    )
    qsub_result, qsub_result_raw = _load_exact_json(
        snapshot.dispatch_dir / "qsub-result.json"
    )
    if (
        sha256_bytes(request_raw) != qsub_request_sha256
        or sha256_bytes(qsub_result_raw) != qsub_result_sha256
    ):
        raise DispatchError("scheduler WAL qsub artifact hash mismatch")
    started = request["qsub_started_epoch_s"]
    deadline = request["absolute_deadline_epoch_s"]
    indexed = list(enumerate(payloads))
    qsub_intents = [
        (index, payload) for index, payload in indexed
        if payload.get("event") == "qsub-intent"
    ]
    qsub_returns = [
        (index, payload) for index, payload in indexed
        if payload.get("event") == "qsub-return"
    ]
    if (
        len(qsub_intents) != 1
        or len(qsub_returns) != 1
        or qsub_intents[0][0] >= qsub_returns[0][0]
        or set(qsub_intents[0][1]) != {
            "event", "qsub_request_sha256", "monotonic_s",
        }
        or qsub_intents[0][1].get("qsub_request_sha256")
        != qsub_request_sha256
        or set(qsub_returns[0][1]) != {
            "event", "qsub_result_sha256", "returncode", "signal",
            "timed_out", "output_limited", "completion_unknown",
            "monotonic_s",
        }
        or any(
            qsub_returns[0][1].get(name) != qsub_result.get(name)
            for name in (
                "returncode", "signal", "timed_out", "output_limited",
                "completion_unknown",
            )
        )
        or qsub_returns[0][1].get("qsub_result_sha256")
        != qsub_result_sha256
    ):
        raise DispatchError("qsub WAL intent/result pairing is invalid")
    qsub_return_index = qsub_returns[0][0]
    exact_job_name = scheduler_job_name(snapshot)
    expected_argv = ["qstat", "-f"]
    lookup_events = [
        (index, payload) for index, payload in indexed
        if payload.get("event") in {
            "scheduler-lookup-intent",
            "scheduler-lookup-result",
        }
    ]
    if lookup_events and lookup_events[0][0] <= qsub_return_index:
        raise DispatchError("scheduler lookup precedes qsub result")
    intents: list[tuple[int, Mapping[str, object]]] = []
    results: list[tuple[int, Mapping[str, object]]] = []
    for index, payload in lookup_events:
        event = payload.get("event")
        common = {
            "event", "schema", "attempt", "argv", "job_name",
            "qsub_request_sha256", "qsub_result_sha256",
            "qsub_started_epoch_s", "absolute_deadline_epoch_s",
            "monotonic_s",
        }
        if (
            payload.get("schema") != "izanagi-test-scheduler-lookup-v1"
            or type(payload.get("attempt")) is not int
            or int(payload["attempt"]) <= 0
            or int(payload["attempt"]) > policy.qstat_transient_limit + 1
            or payload.get("argv") != expected_argv
            or payload.get("job_name") != exact_job_name
            or payload.get("qsub_request_sha256")
            != qsub_request_sha256
            or payload.get("qsub_result_sha256")
            != qsub_result_sha256
            or payload.get("qsub_started_epoch_s") != started
            or payload.get("absolute_deadline_epoch_s") != deadline
            or type(payload.get("monotonic_s")) not in (int, float)
        ):
            raise DispatchError("scheduler lookup WAL identity is invalid")
        if event == "scheduler-lookup-intent":
            if set(payload) != common:
                raise DispatchError("scheduler lookup request WAL is malformed")
            intents.append((index, payload))
            continue
        result_keys = common | {
            "returncode", "signal", "timed_out", "output_limited",
            "completion_unknown", "raw", "disposition", "candidates",
            "reason",
        }
        raw = payload.get("raw")
        candidates = payload.get("candidates")
        if (
            set(payload) != result_keys
            or type(payload.get("returncode")) is not int
            or type(payload.get("timed_out")) is not bool
            or type(payload.get("output_limited")) is not bool
            or type(payload.get("completion_unknown")) is not bool
            or payload.get("disposition") not in {
                "matched", "zero", "multiple", "malformed", "transient",
            }
            or not isinstance(payload.get("reason"), str)
            or type(raw) is not dict
            or set(raw) != {"stdout", "stderr", "returncode"}
            or type(candidates) is not list
        ):
            raise DispatchError("scheduler lookup result WAL is malformed")
        results.append((index, payload))
        receipts = tuple(raw.values())
        if any(
            type(receipt) is not dict
            or not _receipt_matches_file(receipt, snapshot.dispatch_dir)
            for receipt in receipts
        ):
            raise DispatchError("scheduler lookup raw receipt is invalid")
        stdout_size = int(raw["stdout"]["size"])
        stderr_size = int(raw["stderr"]["size"])
        if stdout_size + stderr_size > policy.max_scheduler_output_bytes:
            raise DispatchError("scheduler lookup output receipt exceeds bound")
        try:
            returncode_raw = Path(
                str(raw["returncode"]["path"])
            ).read_bytes()
        except OSError as exc:
            raise DispatchError(
                f"scheduler lookup rc receipt is unavailable: {exc}"
            ) from None
        if returncode_raw != f"{payload['returncode']}\n".encode("ascii"):
            raise DispatchError("scheduler lookup rc receipt is inconsistent")
        expected_candidates: list[Mapping[str, object]] = []
        if (
            payload["returncode"] == 0
            and payload["signal"] is None
            and not payload["timed_out"]
            and not payload["output_limited"]
        ):
            try:
                stdout_raw = Path(str(raw["stdout"]["path"])).read_bytes()
                parsed_candidates = parse_qstat_candidates(
                    stdout_raw.decode("utf-8", "replace"),
                    exact_job_name=exact_job_name,
                    expected_user=str(request["submit_user"]),
                    expected_queue=policy.queue,
                    expected_account=policy.account,
                    expected_group=policy.account,
                    not_before_epoch_s=float(started),
                )
            except (OSError, DispatchError) as exc:
                if payload["disposition"] != "malformed":
                    raise DispatchError(
                        f"scheduler lookup raw candidate parse failed: {exc}"
                    ) from None
                parsed_candidates = ()
            expected_candidates = [
                {
                    "request_id_raw": candidate.request_id_raw,
                    "job_id_normalized": candidate.job_id_normalized,
                    "request_name": candidate.request_name,
                    "user_name": candidate.user_name,
                    "group_name": candidate.group_name,
                    "queue": candidate.queue,
                    "account": candidate.account,
                    "created_epoch_s": candidate.created_epoch_s,
                    "state": candidate.state,
                    "execution_hosts": list(candidate.execution_hosts),
                }
                for candidate in parsed_candidates
            ]
        if candidates != expected_candidates:
            raise DispatchError(
                "scheduler lookup candidate receipt differs from raw qstat"
            )
        disposition = payload["disposition"]
        if (
            (disposition == "matched" and len(candidates) != 1)
            or (disposition in {"zero", "malformed", "transient"} and candidates)
            or (disposition == "multiple" and len(candidates) < 2)
        ):
            raise DispatchError(
                "scheduler lookup candidate cardinality is invalid"
            )
    if len(intents) != len(results):
        raise DispatchError("scheduler lookup intent/result cardinality is invalid")
    for expected_attempt, (intent, result) in enumerate(
        zip(intents, results),
        start=1,
    ):
        if (
            intent[1]["attempt"] != expected_attempt
            or result[1]["attempt"] != expected_attempt
            or intent[0] >= result[0]
            or (
                expected_attempt < len(intents)
                and result[0] >= intents[expected_attempt][0]
            )
        ):
            raise DispatchError("scheduler lookup attempt order is invalid")
    matched = [
        (index, payload) for index, payload in results
        if payload.get("disposition") == "matched"
    ]
    if len(matched) > 1 or (
        matched and matched[0] != results[-1]
    ):
        raise DispatchError("scheduler lookup matched result is not unique/final")

    submit_events = [
        (index, payload) for index, payload in indexed
        if payload.get("event") == "submit-identified"
    ]
    if submit is None:
        if submit_events or matched:
            raise DispatchError("scheduler lookup identified an unsealed submit")
        submit_index = qsub_return_index
    else:
        if len(submit_events) != 1:
            raise DispatchError("submit identity WAL is not unique")
        submit_index, submit_event = submit_events[0]
        submit_keys = {
            "event", "identification_source", "qsub_request_sha256",
            "qsub_result_sha256", "qsub_request_id_raw",
            "job_id_normalized", "submit_receipt_sha256", "monotonic_s",
        }
        if (
            set(submit_event) != submit_keys
            or submit_index <= qsub_return_index
            or submit_event.get("qsub_request_sha256")
            != qsub_request_sha256
            or submit_event.get("qsub_result_sha256")
            != qsub_result_sha256
            or submit_event.get("qsub_request_id_raw")
            != submit.get("qsub_request_id_raw")
            or submit_event.get("job_id_normalized")
            != submit.get("job_id_normalized")
            or submit_event.get("submit_receipt_sha256")
            != final.get("submit_receipt_sha256")
            or submit_event.get("identification_source") not in {
                "qsub-result", "qsub-result-resume", "scheduler-lookup",
            }
        ):
            raise DispatchError("submit identity WAL binding is invalid")
        if submit_event["identification_source"] == "scheduler-lookup":
            if (
                len(matched) != 1
                or matched[0][0] >= submit_index
                or matched[0][1]["candidates"][0]["request_id_raw"]
                != submit["qsub_request_id_raw"]
                or matched[0][1]["candidates"][0]["job_id_normalized"]
                != submit["job_id_normalized"]
            ):
                raise DispatchError(
                    "scheduler lookup candidate is not the submitted identity"
                )
        elif matched:
            raise DispatchError("direct qsub identity has a lookup match")

    final_intents = [
        (index, payload) for index, payload in indexed
        if payload.get("event") == "final-intent"
    ]
    final_keys = {
        "event", "qsub_request_sha256", "qsub_result_sha256",
        "submit_receipt_sha256", "qsub_request_id_raw",
        "job_id_normalized", "dispatch_outcome",
        "controller_exit_status", "controller_signal", "terminal_phase",
        "document", "monotonic_s",
    }
    if (
        len(final_intents) != 1
        or final_intents[0][0] <= submit_index
        or set(final_intents[0][1]) != final_keys
        or final_intents[0][1].get("document") != {
            name: value for name, value in final.items()
            if name != "journal_head_sha256"
        }
        or any(
            final_intents[0][1].get(name) != final.get(name)
            for name in final_keys - {"event", "document", "monotonic_s"}
        )
    ):
        raise DispatchError("final intent WAL binding/order is invalid")


def _receipt_or_none_valid(
    value: object,
    dispatch_dir: Path,
    *,
    verify_files: bool,
) -> bool:
    if value is None:
        return True
    if type(value) is not dict or set(value) != {"path", "size", "sha256"}:
        return False
    if (
        type(value.get("size")) is not int
        or int(value["size"]) < 0
        or _HEX64_RE.fullmatch(str(value.get("sha256"))) is None
        or not isinstance(value.get("path"), str)
    ):
        return False
    return not verify_files or _receipt_matches_file(value, dispatch_dir)


def validate_final_receipt_object(
    final: Mapping[str, object],
    *,
    snapshot: Snapshot,
    verify_files: bool = True,
) -> Mapping[str, object]:
    if (
        set(final) != _FINAL_KEYS
        or final.get("schema") != "izanagi-test-final-v2"
        or final.get("dispatch_id") != snapshot.dispatch_id
        or final.get("snapshot_manifest_sha256") != snapshot.manifest_sha256
        or final.get("execution_closure_sha256")
        != snapshot.execution_closure_sha256
        or final.get("policy_sha256") != snapshot.policy_sha256
        or final.get("dispatch_outcome") not in _FINAL_OUTCOMES
    ):
        raise DispatchError("final receipt schema/identity mismatch")
    for name in (
        "snapshot_manifest_sha256", "execution_closure_sha256",
        "policy_sha256", "qsub_request_sha256", "authorization_sha256",
        "qsub_result_sha256", "journal_head_sha256",
    ):
        if _HEX64_RE.fullmatch(str(final.get(name))) is None:
            raise DispatchError(f"final receipt digest is invalid: {name}")
    submit_sha = final.get("submit_receipt_sha256")
    if submit_sha is not None and _HEX64_RE.fullmatch(str(submit_sha)) is None:
        raise DispatchError("final submit receipt digest is invalid")
    if not _status_pair_valid(
        final.get("controller_exit_status"),
        final.get("controller_signal"),
    ):
        raise DispatchError("final controller status domain is invalid")
    child_status = final.get("child_exit_status")
    if child_status is None:
        if final.get("child_signal") is not None:
            raise DispatchError("final child signal lacks status")
    elif not _status_pair_valid(child_status, final.get("child_signal")):
        raise DispatchError("final child status domain is invalid")
    pytest_status = final.get("pytest_exit_status")
    if pytest_status is None:
        if final.get("pytest_signal") is not None:
            raise DispatchError("final pytest signal lacks status")
    elif not _status_pair_valid(pytest_status, final.get("pytest_signal")):
        raise DispatchError("final pytest status domain is invalid")
    for name in (
        "runner_result", "worker_environment", "runner_claim",
        "stdout", "stderr",
    ):
        if not _receipt_or_none_valid(
            final.get(name),
            snapshot.dispatch_dir,
            verify_files=verify_files,
        ):
            raise DispatchError(f"final file receipt is invalid: {name}")
    task_attempted = final.get("task_run_attempted")
    task_event_id = final.get("task_run_event_id")
    task_event = final.get("task_run_event")
    if task_attempted is not None and type(task_attempted) is not bool:
        raise DispatchError("final task-run attempt field is invalid")
    if task_event_id is not None and (
        not isinstance(task_event_id, str)
        or re.fullmatch(r"[0-9a-f]{16}", task_event_id) is None
    ):
        raise DispatchError("final task-run event ID is invalid")
    if task_event is not None and (
        type(task_event) is not dict
        or set(task_event) != {"path", "size", "sha256", "event_id"}
        or task_event.get("event_id") != task_event_id
        or not isinstance(task_event.get("path"), str)
        or type(task_event.get("size")) is not int
        or int(task_event["size"]) < 0
        or _HEX64_RE.fullmatch(str(task_event.get("sha256"))) is None
    ):
        raise DispatchError("final task-run event receipt is invalid")
    if task_attempted is None:
        if task_event_id is not None or task_event is not None:
            raise DispatchError("final task-run fields lack a child result")
    elif task_attempted is False and (
        task_event_id is not None or task_event is not None
    ):
        raise DispatchError("final task-run event exists without an attempt")
    outcome = str(final["dispatch_outcome"])
    submit_outcome = outcome in {"SUBMIT_FAILED", "SUBMIT_UNKNOWN"}
    if submit_outcome:
        if (
            final["controller_exit_status"] != 125
            or final.get("submit_receipt_sha256") is not None
            or any(final.get(name) is not None for name in (
                "qsub_request_id_raw", "pbs_job_id_raw", "job_id_normalized",
                "child_exit_status", "pytest_exit_status", "runner_stage",
                "runner_result", "worker_environment", "runner_claim",
                "task_run_attempted", "task_run_event_id", "task_run_event",
                "stdout", "stderr", "accounting",
            ))
            or final.get("terminal_phase") not in {
                "qsub", "scheduler-lookup",
            }
        ):
            raise DispatchError("final submit outcome fields are inconsistent")
    else:
        if (
            not isinstance(final.get("qsub_request_id_raw"), str)
            or not isinstance(final.get("job_id_normalized"), str)
            or normalize_job_id(str(final["qsub_request_id_raw"]))
            != final["job_id_normalized"]
        ):
            raise DispatchError("final known-job identity is invalid")
        if (
            final.get("submit_receipt_sha256") is None
            and outcome not in {
                "INTERRUPTED", "INTERRUPT_CANCEL_FAILED",
                "CONTROLLER_FAILURE", "CONTROLLER_CANCEL_FAILED",
            }
        ):
            raise DispatchError("final known-job submit receipt is missing")
    if outcome == "CHILD_RESULT":
        if (
            child_status is None
            or final["controller_exit_status"] != child_status
            or final.get("runner_result") is None
            or final.get("worker_environment") is None
            or final.get("runner_claim") is None
            or final.get("stdout") is None
            or final.get("stderr") is None
            or final.get("accounting") is None
            or final.get("failure_reason") is not None
        ):
            raise DispatchError("final child outcome is incomplete")
    elif outcome == "ACCOUNTING_INCOMPLETE":
        if (
            final["controller_exit_status"] != 125
            or child_status is None
            or final.get("runner_result") is None
            or final.get("worker_environment") is None
            or final.get("runner_claim") is None
            or final.get("stdout") is None
            or final.get("stderr") is None
            or final.get("accounting") is not None
        ):
            raise DispatchError("final accounting-incomplete outcome is invalid")
    elif outcome == "LOG_INCOMPLETE":
        if (
            final["controller_exit_status"] != 125
            or child_status is None
            or final.get("runner_result") is None
            or all(
                final.get(name) is not None
                for name in (
                    "worker_environment", "runner_claim", "stdout", "stderr"
                )
            )
        ):
            raise DispatchError("final log-incomplete outcome is invalid")
    elif outcome == "INFRA_FAILURE":
        if (
            final["controller_exit_status"] != 125
            or any(final.get(name) is not None for name in (
                "child_exit_status", "child_signal", "pytest_exit_status",
                "pytest_signal", "runner_stage", "runner_result",
                "worker_environment", "runner_claim", "task_run_attempted",
                "task_run_event_id", "task_run_event",
            ))
        ):
            raise DispatchError("final infrastructure outcome is invalid")
    elif outcome in {"CANCELED", "CANCEL_FAILED"}:
        if (
            (
                outcome == "CANCELED"
                and final["controller_exit_status"] not in {124, 125}
            )
            or (
                outcome == "CANCEL_FAILED"
                and final["controller_exit_status"] != 125
            )
            or final.get("controller_signal") is not None
            or any(final.get(name) is not None for name in (
                "child_exit_status", "child_signal", "pytest_exit_status",
                "pytest_signal", "runner_stage", "runner_result",
                "worker_environment", "runner_claim", "task_run_attempted",
                "task_run_event_id", "task_run_event",
            ))
        ):
            raise DispatchError("final cancellation outcome is invalid")
    elif outcome in {
        "INTERRUPTED", "INTERRUPT_CANCEL_FAILED",
        "CONTROLLER_FAILURE", "CONTROLLER_CANCEL_FAILED",
    }:
        if (
            any(final.get(name) is not None for name in (
                "pbs_job_id_raw", "child_exit_status", "child_signal",
                "pytest_exit_status", "pytest_signal", "runner_stage",
                "runner_result", "worker_environment", "runner_claim",
                "task_run_attempted", "task_run_event_id", "task_run_event",
                "stdout", "stderr", "accounting",
            ))
            or (
                outcome == "INTERRUPTED"
                and final.get("controller_signal") is None
            )
            or (
                outcome != "INTERRUPTED"
                and (
                    final["controller_exit_status"] != 125
                    or final.get("controller_signal") is not None
                )
            )
        ):
            raise DispatchError("final controller outcome is invalid")
    accounting = final.get("accounting")
    if accounting is not None:
        accounting_lines = accounting.get("lines") if type(accounting) is dict else None
        expected_lines_sha256 = (
            sha256_bytes(
                ("\n".join(accounting_lines) + "\n").encode("utf-8")
            )
            if type(accounting_lines) is list
            and all(isinstance(line, str) for line in accounting_lines)
            else None
        )
        if (
            type(accounting) is not dict
            or set(accounting) != {
                "schema", "job_id_normalized", "lines",
                "lines_sha256", "stderr_sha256",
            }
            or accounting.get("schema") != "izanagi-test-nqsv-accounting-v1"
            or accounting.get("job_id_normalized") != final.get("job_id_normalized")
            or type(accounting.get("lines")) is not list
            or not all(isinstance(line, str) for line in accounting["lines"])
            or _HEX64_RE.fullmatch(str(accounting.get("lines_sha256"))) is None
            or accounting.get("lines_sha256") != expected_lines_sha256
            or _HEX64_RE.fullmatch(str(accounting.get("stderr_sha256"))) is None
            or (
                type(final.get("stderr")) is dict
                and accounting.get("stderr_sha256")
                != final["stderr"].get("sha256")
            )
        ):
            raise DispatchError("final accounting schema is invalid")
    if (
        type(final.get("qsub_started_epoch_s")) not in (int, float)
        or isinstance(final.get("qsub_started_epoch_s"), bool)
        or type(final.get("absolute_deadline_epoch_s")) not in (int, float)
        or isinstance(final.get("absolute_deadline_epoch_s"), bool)
    ):
        raise DispatchError("final qsub deadline fields are invalid")
    if final["absolute_deadline_epoch_s"] <= final["qsub_started_epoch_s"]:
        raise DispatchError("final qsub deadline ordering is invalid")
    if final.get("failure_reason") is not None and not isinstance(
        final.get("failure_reason"), str
    ):
        raise DispatchError("final failure reason is invalid")
    if verify_files:
        bound_receipts = {
            "qsub_request_sha256": "qsub-request.json",
            "authorization_sha256": "pre-submit-authorization.json",
            "qsub_result_sha256": "qsub-result.json",
        }
        if final.get("submit_receipt_sha256") is not None:
            bound_receipts["submit_receipt_sha256"] = "submit-receipt.json"
        loaded: dict[str, Mapping[str, object]] = {}
        for digest_name, filename in bound_receipts.items():
            document, raw = _load_exact_json(snapshot.dispatch_dir / filename)
            if sha256_bytes(raw) != final[digest_name]:
                raise DispatchError(f"final receipt chain mismatch: {filename}")
            loaded[filename] = document
        request = loaded["qsub-request.json"]
        bound_policy = _validate_qsub_request_object(
            request,
            snapshot=snapshot,
        )
        if (
            request.get("qsub_started_epoch_s")
            != final["qsub_started_epoch_s"]
            or request.get("absolute_deadline_epoch_s")
            != final["absolute_deadline_epoch_s"]
        ):
            raise DispatchError("final qsub request deadline link is invalid")
        authorization = loaded["pre-submit-authorization.json"]
        _validate_authorization_object(
            authorization,
            snapshot=snapshot,
            qsub_request_sha256=str(final["qsub_request_sha256"]),
        )
        qsub_result = loaded["qsub-result.json"]
        _validate_qsub_result_object(
            qsub_result,
            snapshot=snapshot,
            qsub_request_sha256=str(final["qsub_request_sha256"]),
            request=request,
            verify_files=True,
        )
        submit = loaded.get("submit-receipt.json")
        if submit is not None:
            _validate_submit_object(
                submit,
                snapshot=snapshot,
                authorization_sha256=str(final["authorization_sha256"]),
                qsub_request_sha256=str(final["qsub_request_sha256"]),
                qsub_result_sha256=str(final["qsub_result_sha256"]),
            )
        _validate_scheduler_lookup_chain(
            snapshot=snapshot,
            policy=bound_policy,
            qsub_request_sha256=str(final["qsub_request_sha256"]),
            qsub_result_sha256=str(final["qsub_result_sha256"]),
            submit=submit,
            final=final,
        )
        if final.get("runner_result") is not None:
            runner_result, runner_raw = _load_exact_json(
                snapshot.dispatch_dir / "runner-result.json"
            )
            if (
                sha256_bytes(runner_raw)
                != final["runner_result"]["sha256"]
            ):
                raise DispatchError("final runner-result receipt hash mismatch")
            validated_runner = validate_runner_result_object(
                runner_result,
                snapshot=snapshot,
                authorization_sha256=str(final["authorization_sha256"]),
                pbs_job_id_raw=str(final["pbs_job_id_raw"]),
                job_id_normalized=str(final["job_id_normalized"]),
                qsub_request_sha256=str(final["qsub_request_sha256"]),
                qsub_result_sha256=str(final["qsub_result_sha256"]),
                submit_receipt_sha256=str(final["submit_receipt_sha256"]),
            )
            field_links = {
                "runner_exit_status": "child_exit_status",
                "runner_signal": "child_signal",
                "pytest_exit_status": "pytest_exit_status",
                "pytest_signal": "pytest_signal",
                "runner_stage": "runner_stage",
                "task_run_attempted": "task_run_attempted",
                "task_run_event_id": "task_run_event_id",
                "task_run_event": "task_run_event",
            }
            if any(
                validated_runner[source] != final[target]
                for source, target in field_links.items()
            ):
                raise DispatchError("final runner-result fields are not exact")
            if (
                type(final.get("worker_environment")) is not dict
                or type(final.get("runner_claim")) is not dict
                or validated_runner["worker_environment_sha256"]
                != final["worker_environment"]["sha256"]
                or validated_runner["runner_claim_sha256"]
                != final["runner_claim"]["sha256"]
            ):
                raise DispatchError(
                    "final runner environment/claim chain is invalid"
                )
        if final.get("accounting") is not None:
            stderr_receipt = final.get("stderr")
            if type(stderr_receipt) is not dict:
                raise DispatchError("final accounting lacks stderr receipt")
            try:
                stderr_raw = Path(
                    str(stderr_receipt["path"])
                ).read_bytes()
            except OSError as exc:
                raise DispatchError(
                    f"final accounting stderr is unavailable: {exc}"
                ) from None
            parsed_accounting = validate_nqsv_accounting(
                stderr_raw.decode("utf-8", "replace"),
                str(final["job_id_normalized"]),
                expected_group=bound_policy.account,
            )
            expected_accounting = {
                **parsed_accounting,
                "stderr_sha256": sha256_bytes(stderr_raw),
            }
            if final["accounting"] != expected_accounting:
                raise DispatchError(
                    "final accounting is not the exact terminal stderr footer"
                )
        current_head = journal_head_sha256(
            snapshot.dispatch_dir / "dispatch-journal.jsonl"
        )
        if current_head != final["journal_head_sha256"]:
            raise DispatchError("final journal head does not match current WAL")
    return final


def load_final_receipt(
    path: Path,
    *,
    snapshot: Snapshot,
) -> Mapping[str, object]:
    final, _ = _load_exact_json(path)
    return validate_final_receipt_object(final, snapshot=snapshot)


def _publish_final(
    snapshot: Snapshot,
    document: Mapping[str, object],
) -> Path:
    validate_final_receipt_object(
        document,
        snapshot=snapshot,
        verify_files=True,
    )
    path = snapshot.dispatch_dir / "final-receipt.json"
    create_file(path, _canonical_json(document))
    return path


def _stage_and_publish_final(
    *,
    snapshot: Snapshot,
    filesystem: MonitorFilesystem,
    journal: Path,
    document: Mapping[str, object],
    clock: Callable[[], float],
) -> Mapping[str, object]:
    base = dict(document)
    base.pop("journal_head_sha256", None)
    append_journal(journal, {
        "event": "final-intent",
        "qsub_request_sha256": base.get("qsub_request_sha256"),
        "qsub_result_sha256": base.get("qsub_result_sha256"),
        "submit_receipt_sha256": base.get("submit_receipt_sha256"),
        "qsub_request_id_raw": base.get("qsub_request_id_raw"),
        "job_id_normalized": base.get("job_id_normalized"),
        "dispatch_outcome": base.get("dispatch_outcome"),
        "controller_exit_status": base.get("controller_exit_status"),
        "controller_signal": base.get("controller_signal"),
        "terminal_phase": base.get("terminal_phase"),
        "document": base,
        "monotonic_s": clock(),
    })
    journal_head = journal_head_sha256(journal)
    if journal_head is None:
        raise DispatchError("final journal head is unavailable")
    final = {**base, "journal_head_sha256": journal_head}
    filesystem.stage_final(snapshot, final)
    filesystem.publish_final(snapshot, final)
    return final


def _publish_pending_final_if_present(
    *,
    snapshot: Snapshot,
    filesystem: MonitorFilesystem,
) -> int | None:
    pending_path = snapshot.dispatch_dir / "final-pending.json"
    if filesystem.exists(pending_path):
        pending = filesystem.load_object(pending_path)
    else:
        journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
        if not journal.exists():
            return None
        final_intents = [
            payload for payload in _journal_payloads(journal)
            if payload.get("event") == "final-intent"
        ]
        if not final_intents:
            return None
        if len(final_intents) != 1 or type(
            final_intents[0].get("document")
        ) is not dict:
            raise DispatchError("final WAL intent is not uniquely resumable")
        journal_head = journal_head_sha256(journal)
        if journal_head is None:
            raise DispatchError("final WAL head is unavailable")
        pending = {
            **dict(final_intents[0]["document"]),
            "journal_head_sha256": journal_head,
        }
        filesystem.stage_final(snapshot, pending)
    validated = validate_final_receipt_object(
        pending,
        snapshot=snapshot,
        verify_files=isinstance(filesystem, PathMonitorFilesystem),
    )
    filesystem.publish_final(snapshot, validated)
    return int(validated["controller_exit_status"])


class PathMonitorFilesystem:
    def exists(self, path: Path) -> bool:
        return path.exists()

    def receipt(self, path: Path) -> Mapping[str, object] | None:
        return _file_receipt(path)

    def load_object(self, path: Path) -> Mapping[str, object]:
        value, _ = _load_exact_json(path)
        return value

    def publish_final(
        self, snapshot: Snapshot, document: Mapping[str, object],
    ) -> None:
        _publish_final(snapshot, document)

    def stage_final(
        self, snapshot: Snapshot, document: Mapping[str, object],
    ) -> None:
        validate_final_receipt_object(
            document,
            snapshot=snapshot,
            verify_files=True,
        )
        path = snapshot.dispatch_dir / "final-pending.json"
        raw = _canonical_json(document)
        if path.exists():
            current, current_raw = _load_exact_json(path)
            if current != document or current_raw != raw:
                raise DispatchError("pending final receipt conflicts with WAL")
            return
        create_file(path, raw)

    def replay(self, path: Path, destination: Any, byte_limit: int) -> int:
        return replay_spool(path, destination, byte_limit=byte_limit)

    def read_bytes(self, path: Path, byte_limit: int) -> bytes:
        receipt = _file_receipt(path, byte_limit=byte_limit)
        if receipt is None:
            raise DispatchError(f"spool is unavailable: {path.name}")
        raw = path.read_bytes()
        if len(raw) > byte_limit:
            raise DispatchError(f"spool exceeds byte limit: {path.name}")
        return raw

    def size(self, path: Path) -> int | None:
        receipt = _file_receipt(path)
        return None if receipt is None else int(receipt["size"])

    def record_command(
        self,
        directory: Path,
        label: str,
        sequence: int,
        result: CommandResult,
    ) -> Mapping[str, object]:
        stem = f"{sequence:05d}-{label}"
        stdout_path = directory / f"{stem}.stdout"
        stderr_path = directory / f"{stem}.stderr"
        rc_path = directory / f"{stem}.rc"
        create_file(stdout_path, result.stdout.encode("utf-8"))
        create_file(stderr_path, result.stderr.encode("utf-8"))
        create_file(rc_path, f"{result.returncode}\n".encode("ascii"))
        return {
            "stdout": _file_receipt(stdout_path),
            "stderr": _file_receipt(stderr_path),
            "returncode": _file_receipt(rc_path),
        }

    def next_sequence(self, directory: Path) -> int:
        maximum = 0
        for path in directory.glob("[0-9][0-9][0-9][0-9][0-9]-*.rc"):
            try:
                maximum = max(maximum, int(path.name[:5]))
            except ValueError:
                continue
        return maximum


def _bounded_scheduler_result(
    result: CommandResult,
    *,
    argv: tuple[str, ...],
    byte_limit: int,
) -> CommandResult:
    if (
        not isinstance(result, CommandResult)
        or tuple(result.argv) != argv
        or type(result.returncode) is not int
        or not 0 <= result.returncode <= 255
        or not isinstance(result.stdout, str)
        or not isinstance(result.stderr, str)
        or type(result.timed_out) is not bool
        or type(result.output_limited) is not bool
        or type(result.completion_unknown) is not bool
        or (
            result.signal is not None
            and (
                type(result.signal) is not int
                or not 1 <= result.signal <= 64
            )
        )
    ):
        raise DispatchError("scheduler lookup command result is malformed")
    stdout_raw = result.stdout.encode("utf-8")
    stderr_raw = result.stderr.encode("utf-8")
    if len(stdout_raw) + len(stderr_raw) <= byte_limit:
        return result
    bounded_stdout = stdout_raw[:byte_limit]
    remaining = max(0, byte_limit - len(bounded_stdout))
    bounded_stderr = stderr_raw[:remaining]
    return CommandResult(
        argv=argv,
        returncode=125,
        stdout=bounded_stdout.decode("utf-8", "replace"),
        stderr=bounded_stderr.decode("utf-8", "replace"),
        timed_out=False,
        output_limited=True,
        signal=None,
        completion_unknown=True,
    )


def _policy_bound_lookup_candidate(
    candidate: Mapping[str, object],
    *,
    exact_job_name: str,
    policy: DispatchPolicy,
    expected_user: str,
    qsub_started_epoch_s: float,
) -> tuple[str, str, str, tuple[str, ...]]:
    """Bind one WAL lookup candidate to the snapshot-bound policy identity.

    This is the predicate `lookup_scheduler_job` has always applied when it
    replays a `scheduler-lookup-result`.  `resume_dispatch` reads the very same
    WAL row and must not read it more weakly.  The scheduler group is reported
    on its own so a rejection cannot be confused with the other nine terms.
    """
    request_id_raw = str(candidate.get("request_id_raw"))
    normalized = normalize_job_id(request_id_raw)
    hosts = candidate.get("execution_hosts")
    if candidate.get("group_name") != policy.account:
        raise DispatchError(
            "scheduler lookup WAL candidate group is not the policy account: "
            f"expected={policy.account!r} "
            f"observed={candidate.get('group_name')!r}"
        )
    if (
        candidate.get("job_id_normalized") != normalized
        or candidate.get("request_name") != exact_job_name
        or candidate.get("user_name") != expected_user
        or str(candidate.get("queue", "")).split("@", 1)[0]
        != policy.queue
        or candidate.get("account") != policy.account
        or type(candidate.get("created_epoch_s")) is not int
        or int(candidate["created_epoch_s"]) < int(qsub_started_epoch_s)
        or candidate.get("state") not in set(_QSTAT_STATES.values())
        or type(hosts) is not list
        or not all(isinstance(host, str) for host in hosts)
    ):
        raise DispatchError("scheduler lookup WAL candidate is malformed")
    return (
        request_id_raw,
        normalized,
        str(candidate["state"]),
        tuple(hosts),
    )


def lookup_scheduler_job(
    *,
    snapshot: Snapshot,
    scheduler: Scheduler,
    policy: DispatchPolicy,
    qsub_request_sha256: str,
    qsub_result_sha256: str,
    qsub_started_epoch_s: float,
    absolute_deadline_epoch_s: float,
    clock: Callable[[], float],
    wall_clock: Callable[[], float],
    sleep: Callable[[float], None],
    filesystem: MonitorFilesystem | None = None,
) -> SchedulerLookup:
    """Recover one accepted NQSV request by its hash-bound exact job name."""
    if (
        _HEX64_RE.fullmatch(qsub_request_sha256) is None
        or _HEX64_RE.fullmatch(qsub_result_sha256) is None
    ):
        raise DispatchError("scheduler lookup qsub chain is invalid")
    fs = PathMonitorFilesystem() if filesystem is None else filesystem
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    request, request_raw = _load_exact_json(
        snapshot.dispatch_dir / "qsub-request.json"
    )
    if sha256_bytes(request_raw) != qsub_request_sha256:
        raise DispatchError("scheduler lookup request hash mismatch")
    _validate_qsub_request_object(request, snapshot=snapshot)
    if (
        request.get("qsub_started_epoch_s") != qsub_started_epoch_s
        or request.get("absolute_deadline_epoch_s")
        != absolute_deadline_epoch_s
        or absolute_deadline_epoch_s
        != qsub_started_epoch_s + policy.global_deadline_s
    ):
        raise DispatchError("scheduler lookup qsub deadline mismatch")
    exact_job_name = scheduler_job_name(snapshot)
    expected_user = str(request["submit_user"])
    argv = ("qstat", "-f")
    command_environment = scheduler_environment()
    now = clock()
    lookup_deadline = min(
        now + policy.visibility_grace_s,
        now + max(0.0, absolute_deadline_epoch_s - wall_clock()),
    )
    command_sequence = fs.next_sequence(snapshot.dispatch_dir)
    max_attempts = policy.qstat_transient_limit + 1
    payloads = _journal_payloads(journal)
    lookup_events = [
        payload for payload in payloads
        if payload.get("event") in {
            "scheduler-lookup-intent", "scheduler-lookup-result",
        }
        and payload.get("qsub_request_sha256") == qsub_request_sha256
        and payload.get("qsub_result_sha256") == qsub_result_sha256
    ]
    intents: dict[int, Mapping[str, object]] = {}
    results: dict[int, Mapping[str, object]] = {}
    for event in lookup_events:
        attempt = event.get("attempt")
        if type(attempt) is not int or not 1 <= attempt <= max_attempts:
            raise DispatchError("scheduler lookup WAL attempt is invalid")
        destination = (
            intents
            if event.get("event") == "scheduler-lookup-intent"
            else results
        )
        if attempt in destination:
            raise DispatchError("scheduler lookup WAL attempt is duplicated")
        destination[attempt] = event
    completed_attempts = sorted(results)
    if (
        sorted(intents) not in (
            completed_attempts,
            completed_attempts + [len(completed_attempts) + 1],
        )
        or completed_attempts != list(range(1, len(completed_attempts) + 1))
    ):
        raise DispatchError("scheduler lookup WAL intent/result order is invalid")
    if completed_attempts:
        previous = results[completed_attempts[-1]]
        previous_disposition = previous.get("disposition")
        previous_reason = str(previous.get("reason", "scheduler lookup failed"))
        previous_candidates = previous.get("candidates")
        if previous_disposition == "matched":
            if (
                type(previous_candidates) is not list
                or len(previous_candidates) != 1
                or type(previous_candidates[0]) is not dict
            ):
                raise DispatchError("scheduler lookup WAL match is malformed")
            (
                request_id_raw,
                normalized,
                candidate_state,
                hosts,
            ) = _policy_bound_lookup_candidate(
                previous_candidates[0],
                exact_job_name=exact_job_name,
                policy=policy,
                expected_user=expected_user,
                qsub_started_epoch_s=qsub_started_epoch_s,
            )
            return SchedulerLookup(
                request_id_raw,
                normalized,
                candidate_state,
                hosts,
                "scheduler lookup recovered exact job from WAL",
            )
        if previous_disposition in {"malformed", "multiple"}:
            return SchedulerLookup(None, None, None, (), previous_reason)
    attempts_used = len(completed_attempts)
    if attempts_used >= max_attempts:
        return SchedulerLookup(
            None,
            None,
            None,
            (),
            "scheduler lookup visibility grace/transient budget "
            "was exhausted in WAL",
        )
    for attempt in range(attempts_used + 1, max_attempts + 1):
        if clock() >= lookup_deadline or wall_clock() >= absolute_deadline_epoch_s:
            return SchedulerLookup(
                None,
                None,
                None,
                (),
                "scheduler lookup qsub absolute/visibility deadline exhausted",
            )
        if attempt not in intents:
            append_journal(journal, {
                "event": "scheduler-lookup-intent",
                "schema": "izanagi-test-scheduler-lookup-v1",
                "attempt": attempt,
                "argv": list(argv),
                "job_name": exact_job_name,
                "qsub_request_sha256": qsub_request_sha256,
                "qsub_result_sha256": qsub_result_sha256,
                "qsub_started_epoch_s": qsub_started_epoch_s,
                "absolute_deadline_epoch_s": absolute_deadline_epoch_s,
                "monotonic_s": clock(),
            })
        try:
            raw_result = scheduler.run(
                argv,
                timeout=policy.command_timeout_s,
                environment=command_environment,
            )
        except (subprocess.TimeoutExpired, TimeoutError, OSError) as exc:
            raw_result = CommandResult(
                argv,
                124,
                "",
                f"qstat lookup timeout: {exc}",
                timed_out=True,
                completion_unknown=True,
            )
        result = _bounded_scheduler_result(
            raw_result,
            argv=argv,
            byte_limit=policy.max_scheduler_output_bytes,
        )
        command_sequence += 1
        raw_receipt = fs.record_command(
            snapshot.dispatch_dir,
            "scheduler-lookup",
            command_sequence,
            result,
        )
        candidates: tuple[SchedulerCandidate, ...] = ()
        disposition = "transient"
        reason = "scheduler lookup command was transient"
        if (
            result.returncode == 0
            and not result.timed_out
            and not result.output_limited
            and result.signal is None
        ):
            try:
                candidates = parse_qstat_candidates(
                    result.stdout,
                    exact_job_name=exact_job_name,
                    expected_user=expected_user,
                    expected_queue=policy.queue,
                    expected_account=policy.account,
                    expected_group=policy.account,
                    not_before_epoch_s=qsub_started_epoch_s,
                )
            except DispatchError as exc:
                disposition = "malformed"
                reason = str(exc)
            else:
                if len(candidates) == 1:
                    disposition = "matched"
                    reason = "scheduler lookup recovered one exact job"
                elif len(candidates) == 0:
                    disposition = "zero"
                    reason = "scheduler lookup found no exact job"
                else:
                    disposition = "multiple"
                    reason = "scheduler lookup found multiple exact jobs"
        candidate_receipts = [
            {
                "request_id_raw": candidate.request_id_raw,
                "job_id_normalized": candidate.job_id_normalized,
                "request_name": candidate.request_name,
                "user_name": candidate.user_name,
                "group_name": candidate.group_name,
                "queue": candidate.queue,
                "account": candidate.account,
                "created_epoch_s": candidate.created_epoch_s,
                "state": candidate.state,
                "execution_hosts": list(candidate.execution_hosts),
            }
            for candidate in candidates
        ]
        append_journal(journal, {
            "event": "scheduler-lookup-result",
            "schema": "izanagi-test-scheduler-lookup-v1",
            "attempt": attempt,
            "argv": list(argv),
            "job_name": exact_job_name,
            "qsub_request_sha256": qsub_request_sha256,
            "qsub_result_sha256": qsub_result_sha256,
            "qsub_started_epoch_s": qsub_started_epoch_s,
            "absolute_deadline_epoch_s": absolute_deadline_epoch_s,
            "returncode": result.returncode,
            "signal": result.signal,
            "timed_out": result.timed_out,
            "output_limited": result.output_limited,
            "completion_unknown": result.completion_unknown,
            "raw": raw_receipt,
            "disposition": disposition,
            "candidates": candidate_receipts,
            "reason": reason,
            "monotonic_s": clock(),
        })
        if disposition == "matched":
            candidate = candidates[0]
            return SchedulerLookup(
                candidate.request_id_raw,
                candidate.job_id_normalized,
                candidate.state,
                candidate.execution_hosts,
                reason,
            )
        if disposition in {"malformed", "multiple"}:
            return SchedulerLookup(None, None, None, (), reason)
        if (
            attempt >= max_attempts
            or clock() >= lookup_deadline
            or wall_clock() >= absolute_deadline_epoch_s
        ):
            return SchedulerLookup(
                None,
                None,
                None,
                (),
                f"{reason}; visibility grace/transient budget exhausted",
            )
        sleep(policy.poll_interval_s)
    raise AssertionError("scheduler lookup attempt bound was not enforced")


def monitor_job(
    *,
    snapshot: Snapshot,
    scheduler: Scheduler,
    policy: DispatchPolicy,
    authorization_sha256: str,
    qsub_request_sha256: str,
    qsub_result_sha256: str,
    submit_receipt_sha256: str,
    qsub_request_id_raw: str,
    job_id_normalized: str,
    qsub_started_epoch_s: float,
    absolute_deadline_epoch_s: float,
    expected_execution_hosts: Sequence[str] = (),
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
    filesystem: MonitorFilesystem | None = None,
) -> int:
    snapshot_policy = load_policy(
        snapshot.snapshot_root
        / "tools"
        / "pegasus"
        / "test_dispatch_policy.json"
    )
    if policy != snapshot_policy or policy.policy_sha256 != snapshot.policy_sha256:
        raise DispatchError("monitor policy differs from snapshot-bound policy")
    if absolute_deadline_epoch_s != qsub_started_epoch_s + policy.global_deadline_s:
        raise DispatchError("qsub-origin absolute deadline is inconsistent")
    fs = PathMonitorFilesystem() if filesystem is None else filesystem
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    stdout_path = snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout"
    stderr_path = snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr"
    runner_result_path = snapshot.dispatch_dir / "runner-result.json"
    worker_environment_path = snapshot.dispatch_dir / "worker-environment.json"
    runner_claim_path = snapshot.dispatch_dir / "runner-claim.json"
    started = clock()
    monotonic_deadline = started + max(
        0.0,
        absolute_deadline_epoch_s - wall_clock(),
    )
    state_started = started
    visible = False
    phase = "visibility"
    transient = 0
    canceled = False
    cancel_failed = False
    failure_reason: str | None = None
    spool_policy_failed = False
    poll_sequence = fs.next_sequence(snapshot.dispatch_dir)
    command_environment = scheduler_environment()
    lookup_hosts = tuple(expected_execution_hosts)
    if (
        len(lookup_hosts) > 1
        or any(_BNODE_RE.fullmatch(host) is None for host in lookup_hosts)
    ):
        raise DispatchError("lookup execution-host identity is invalid")
    observed_running_host = lookup_hosts[0] if lookup_hosts else None

    def cancel_for(
        *,
        reason: str,
        terminal_phase: str,
        detail: str,
        timeout_status: bool = False,
    ) -> bool:
        return cancel_job(
            scheduler=scheduler,
            job_id_normalized=job_id_normalized,
            policy=policy,
            journal_path=journal,
            clock=clock,
            sleep=sleep,
            reason=reason,
            recovery={
                "success_outcome": "CANCELED",
                "failure_outcome": "CANCEL_FAILED",
                "success_status": 124 if timeout_status else 125,
                "failure_status": 125,
                "success_signal": None,
                "failure_signal": None,
                "terminal_phase": terminal_phase,
                "failure_reason": detail,
            },
            filesystem=fs,
        )

    timeouts = {
        "visibility": policy.visibility_grace_s,
        "queued": policy.queue_timeout_s,
        "held": policy.held_timeout_s,
        "pre-running": policy.prerun_timeout_s,
        "running": policy.run_timeout_s,
    }
    while True:
        now = clock()
        if (
            wall_clock() >= absolute_deadline_epoch_s
            or now >= monotonic_deadline
        ):
            cancel_succeeded = cancel_for(
                reason="global-deadline",
                terminal_phase="global-deadline",
                detail="qsub-origin absolute deadline exceeded",
                timeout_status=True,
            )
            canceled = True
            cancel_failed = not cancel_succeeded
            phase = "global-deadline"
            failure_reason = "qsub-origin absolute deadline exceeded"
            break
        spool_sizes = tuple(
            size for size in (
                fs.size(stdout_path),
                fs.size(stderr_path),
            )
            if size is not None
        )
        if any(size > policy.max_spool_bytes for size in spool_sizes) or (
            sum(spool_sizes) > policy.max_spool_bytes
        ):
            cancel_succeeded = cancel_for(
                reason="spool-limit",
                terminal_phase="spool-limit",
                detail="combined PBS spool exceeded policy",
            )
            canceled = True
            cancel_failed = not cancel_succeeded
            phase = "spool-limit"
            failure_reason = "combined PBS spool exceeded policy"
            break
        result = scheduler.run(
            ("qstat", "-f", job_id_normalized),
            timeout=policy.command_timeout_s,
            environment=command_environment,
        )
        poll_sequence += 1
        raw_receipt = fs.record_command(
            snapshot.dispatch_dir, "qstat", poll_sequence, result,
        )
        try:
            status = parse_qstat(
                result,
                expected_job_id_normalized=job_id_normalized,
                expected_group=policy.account,
                was_visible=visible,
            )
        except DispatchError as exc:
            append_journal(journal, {
                "event": "qstat-parse-failure",
                "reason": str(exc),
                "returncode": result.returncode,
                "raw": raw_receipt,
                "monotonic_s": clock(),
            })
            cancel_succeeded = cancel_for(
                reason="qstat-parse-failure",
                terminal_phase="qstat-parse-failure",
                detail=str(exc),
            )
            canceled = True
            cancel_failed = not cancel_succeeded
            phase = "qstat-parse-failure"
            failure_reason = str(exc)
            break
        append_journal(journal, {
            "event": "qstat-poll",
            "phase": phase,
            "parsed_state": status.state,
            "raw_state": status.raw_state,
            "returncode": result.returncode,
            "raw": raw_receipt,
            "monotonic_s": clock(),
        })
        now = clock()
        if status.visible:
            visible = True
            transient = 0
            if status.state == "terminal":
                phase = "terminal"
                break
            if status.state == "running" and len(status.execution_hosts) != 1:
                cancel_succeeded = cancel_for(
                    reason="running-host-identity",
                    terminal_phase="canceled",
                    detail="running qstat lacked one exact execution host",
                )
                canceled = True
                cancel_failed = not cancel_succeeded
                phase = "canceled"
                failure_reason = "running qstat lacked one exact execution host"
                break
            if status.state == "running":
                current_host = status.execution_hosts[0]
                if (
                    observed_running_host is not None
                    and current_host != observed_running_host
                ):
                    cancel_succeeded = cancel_for(
                        reason="running-host-drift",
                        terminal_phase="canceled",
                        detail="running qstat execution host changed",
                    )
                    canceled = True
                    cancel_failed = not cancel_succeeded
                    phase = "canceled"
                    failure_reason = "running qstat execution host changed"
                    break
                observed_running_host = current_host
            if status.state != phase:
                phase = status.state
                state_started = now
        else:
            transient += 1
            if visible and transient > policy.qstat_transient_limit:
                phase = "disappeared"
                break
        timeout_name = phase if phase in timeouts else "visibility"
        if now - state_started > timeouts[timeout_name]:
            cancel_succeeded = cancel_for(
                reason=f"{timeout_name}-timeout",
                terminal_phase=f"{timeout_name}-timeout",
                detail=f"{timeout_name} timeout",
                timeout_status=True,
            )
            canceled = True
            cancel_failed = not cancel_succeeded
            phase = f"{timeout_name}-timeout"
            failure_reason = f"{timeout_name} timeout"
            break
        sleep(policy.poll_interval_s)

    log_deadline = min(
        wall_clock() + policy.log_grace_s,
        absolute_deadline_epoch_s,
    )
    log_monotonic_deadline = min(
        clock() + policy.log_grace_s,
        monotonic_deadline,
    )
    stable_stderr = 0
    previous_stderr_sha256: str | None = None
    while (
        wall_clock() <= log_deadline
        and clock() <= log_monotonic_deadline
    ):
        stdout_size = fs.size(stdout_path)
        stderr_size = fs.size(stderr_path)
        sizes = tuple(
            size for size in (stdout_size, stderr_size) if size is not None
        )
        if any(size > policy.max_spool_bytes for size in sizes) or (
            sum(sizes) > policy.max_spool_bytes
        ):
            failure_reason = "combined PBS spool exceeded policy after terminal state"
            spool_policy_failed = True
            break
        current_stderr_sha256: str | None = None
        if stderr_size is not None:
            try:
                current_stderr = fs.read_bytes(
                    stderr_path,
                    policy.max_spool_bytes,
                )
            except DispatchError:
                stable_stderr = 0
            else:
                current_stderr_sha256 = sha256_bytes(current_stderr)
                stable_stderr = (
                    stable_stderr + 1
                    if current_stderr_sha256 == previous_stderr_sha256
                    else 1
                )
        else:
            stable_stderr = 0
        previous_stderr_sha256 = current_stderr_sha256
        if (
            stdout_size is not None
            and stderr_size is not None
            and stable_stderr >= policy.stderr_stable_polls
            and (fs.exists(runner_result_path) or canceled)
        ):
            break
        sleep(policy.poll_interval_s)
    stdout_receipt = fs.receipt(stdout_path)
    stderr_receipt: Mapping[str, object] | None = None
    if (
        stdout_receipt is not None
        and int(stdout_receipt["size"]) > policy.max_spool_bytes
    ):
        stdout_receipt = None
        failure_reason = "PBS stdout receipt exceeded policy"
        spool_policy_failed = True

    accounting: Mapping[str, object] | None = None
    accounting_error: str | None = None
    if not canceled and not spool_policy_failed and fs.size(stderr_path) is not None:
        accounting_deadline = min(
            wall_clock() + policy.accounting_grace_s,
            absolute_deadline_epoch_s,
        )
        accounting_monotonic_deadline = min(
            clock() + policy.accounting_grace_s,
            monotonic_deadline,
        )
        accounting_stable = 0
        accounting_previous_sha256: str | None = None
        while (
            wall_clock() <= accounting_deadline
            and clock() <= accounting_monotonic_deadline
        ):
            try:
                current_sizes = tuple(
                    size for size in (
                        fs.size(stdout_path),
                        fs.size(stderr_path),
                    )
                    if size is not None
                )
                if (
                    any(size > policy.max_spool_bytes for size in current_sizes)
                    or sum(current_sizes) > policy.max_spool_bytes
                ):
                    raise DispatchError(
                        "combined PBS spool exceeded policy after terminal state"
                    )
                stderr_raw = fs.read_bytes(
                    stderr_path,
                    policy.max_spool_bytes,
                )
                stderr_sha256 = sha256_bytes(stderr_raw)
                accounting_stable = (
                    accounting_stable + 1
                    if stderr_sha256 == accounting_previous_sha256
                    else 1
                )
                accounting_previous_sha256 = stderr_sha256
                if accounting_stable < policy.stderr_stable_polls:
                    sleep(policy.poll_interval_s)
                    continue
                parsed = validate_nqsv_accounting(
                    stderr_raw.decode("utf-8", "replace"),
                    job_id_normalized,
                    # Snapshot-bound, exactly like the `bound_policy.account`
                    # that `validate_final_receipt_object` re-checks this
                    # footer against.  Binding to the caller's `policy` would
                    # let the sealing group and the re-validating group drift
                    # apart and make the dispatch permanently unsealable.
                    expected_group=snapshot_policy.account,
                )
            except DispatchError as exc:
                accounting_error = str(exc)
                if "spool exceeded policy" in accounting_error:
                    spool_policy_failed = True
                    failure_reason = accounting_error
                    break
                sleep(policy.poll_interval_s)
                continue
            stderr_receipt = {
                "path": str(stderr_path),
                "size": len(stderr_raw),
                "sha256": stderr_sha256,
            }
            accounting = {
                **parsed,
                "stderr_sha256": stderr_sha256,
            }
            accounting_error = None
            break
    elif fs.size(stderr_path) is not None:
        stderr_receipt = fs.receipt(stderr_path)
    if (
        stderr_receipt is None
        and not spool_policy_failed
        and fs.size(stderr_path) is not None
    ):
        candidate = fs.receipt(stderr_path)
        if (
            candidate is not None
            and int(candidate["size"]) <= policy.max_spool_bytes
        ):
            stderr_receipt = candidate
    final_sizes = tuple(
        int(receipt["size"])
        for receipt in (stdout_receipt, stderr_receipt)
        if receipt is not None
    )
    if (
        any(size > policy.max_spool_bytes for size in final_sizes)
        or sum(final_sizes) > policy.max_spool_bytes
    ):
        spool_policy_failed = True
        failure_reason = "combined PBS spool exceeded policy after terminal state"
        accounting = None
    elif (
        not canceled
        and accounting is None
        and failure_reason is None
    ):
        failure_reason = (
            accounting_error
            or "terminal NQSV accounting footer did not become stable"
        )

    child_result: Mapping[str, object] | None = None
    if fs.exists(runner_result_path):
        # Worker PBS raw identity is carried by the hash-bound result; qsub raw
        # and normalized scheduler identity remain distinct fields.
        try:
            raw_candidate = fs.load_object(runner_result_path)
            pbs_raw = raw_candidate.get("pbs_job_id_raw")
            if not isinstance(pbs_raw, str):
                raise DispatchError("runner result lacks raw PBS identity")
            child_result = validate_runner_result_object(
                raw_candidate,
                snapshot=snapshot,
                authorization_sha256=authorization_sha256,
                pbs_job_id_raw=pbs_raw,
                job_id_normalized=job_id_normalized,
                qsub_request_sha256=qsub_request_sha256,
                qsub_result_sha256=qsub_result_sha256,
                submit_receipt_sha256=submit_receipt_sha256,
            )
        except DispatchError as exc:
            failure_reason = str(exc)
            append_journal(journal, {
                "event": "runner-result-invalid",
                "reason": str(exc),
                "monotonic_s": clock(),
            })
    if child_result is not None and observed_running_host is not None:
        runner_host = str(child_result["hostname_canonical"]).split(".", 1)[0]
        if runner_host != observed_running_host:
            failure_reason = (
                "runner host does not match qstat execution host: "
                f"qstat={observed_running_host!r} runner={runner_host!r}"
            )
            child_result = None
            append_journal(journal, {
                "event": "runner-host-mismatch",
                "qstat_host": observed_running_host,
                "runner_host": runner_host,
                "monotonic_s": clock(),
            })
    closure_valid = True
    try:
        verify_execution_closure(snapshot)
        verify_snapshot_tree(snapshot, policy)
    except DispatchError as exc:
        closure_valid = False
        child_result = None
        failure_reason = str(exc)
        append_journal(journal, {
            "event": "execution-tree-invalid",
            "reason": str(exc),
            "monotonic_s": clock(),
        })
    if canceled or spool_policy_failed:
        # A late child result cannot overturn a controller cancellation intent.
        child_result = None
    runner_result_receipt = (
        fs.receipt(runner_result_path) if child_result is not None else None
    )
    worker_environment_receipt = (
        fs.receipt(worker_environment_path) if child_result is not None else None
    )
    runner_claim_receipt = (
        fs.receipt(runner_claim_path) if child_result is not None else None
    )
    if child_result is not None and (
        worker_environment_receipt is None
        or runner_claim_receipt is None
        or child_result["worker_environment_sha256"]
        != worker_environment_receipt.get("sha256")
        or child_result["runner_claim_sha256"]
        != runner_claim_receipt.get("sha256")
    ):
        failure_reason = "runner environment/claim receipt hash mismatch"
        child_result = None
        runner_result_receipt = None
        worker_environment_receipt = None
        runner_claim_receipt = None
    if canceled:
        outcome = "CANCEL_FAILED" if cancel_failed else "CANCELED"
        controller_rc = (
            124
            if (
                (phase.endswith("-timeout") or phase == "global-deadline")
                and not cancel_failed
            )
            else 125
        )
    elif spool_policy_failed or child_result is None:
        outcome = "INFRA_FAILURE"
        controller_rc = 125
    elif (
        stdout_receipt is None
        or stderr_receipt is None
        or runner_result_receipt is None
        or worker_environment_receipt is None
        or runner_claim_receipt is None
        or not closure_valid
    ):
        outcome = "LOG_INCOMPLETE"
        controller_rc = 125
    elif accounting is None:
        outcome = "ACCOUNTING_INCOMPLETE"
        controller_rc = 125
    else:
        outcome = "CHILD_RESULT"
        controller_rc = int(child_result["runner_exit_status"])
        failure_reason = None
    final = {
        "schema": "izanagi-test-final-v2",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "qsub_request_sha256": qsub_request_sha256,
        "authorization_sha256": authorization_sha256,
        "qsub_result_sha256": qsub_result_sha256,
        "submit_receipt_sha256": submit_receipt_sha256,
        "qsub_request_id_raw": qsub_request_id_raw,
        "pbs_job_id_raw": (
            child_result.get("pbs_job_id_raw") if child_result is not None else None
        ),
        "job_id_normalized": job_id_normalized,
        "dispatch_outcome": outcome,
        "controller_exit_status": controller_rc,
        "controller_signal": None,
        "child_exit_status": (
            child_result.get("runner_exit_status") if child_result is not None else None
        ),
        "child_signal": (
            child_result.get("runner_signal") if child_result is not None else None
        ),
        "pytest_exit_status": (
            child_result.get("pytest_exit_status") if child_result is not None else None
        ),
        "pytest_signal": (
            child_result.get("pytest_signal") if child_result is not None else None
        ),
        "runner_stage": (
            child_result.get("runner_stage") if child_result is not None else None
        ),
        "runner_result": runner_result_receipt,
        "worker_environment": worker_environment_receipt,
        "runner_claim": runner_claim_receipt,
        "task_run_attempted": (
            child_result.get("task_run_attempted") if child_result is not None else None
        ),
        "task_run_event_id": (
            child_result.get("task_run_event_id") if child_result is not None else None
        ),
        "task_run_event": (
            child_result.get("task_run_event") if child_result is not None else None
        ),
        "stdout": stdout_receipt,
        "stderr": stderr_receipt,
        "accounting": accounting,
        "terminal_phase": phase,
        "qsub_started_epoch_s": qsub_started_epoch_s,
        "absolute_deadline_epoch_s": absolute_deadline_epoch_s,
        "failure_reason": failure_reason,
    }
    _stage_and_publish_final(
        snapshot=snapshot,
        filesystem=fs,
        journal=journal,
        document=final,
        clock=clock,
    )
    if stdout_receipt is not None:
        fs.replay(
            stdout_path,
            getattr(sys.stdout, "buffer", sys.stdout),
            policy.replay_bytes,
        )
    if stderr_receipt is not None:
        fs.replay(
            stderr_path,
            getattr(sys.stderr, "buffer", sys.stderr),
            policy.replay_bytes,
        )
    return controller_rc


def scheduler_job_name(snapshot: Snapshot) -> str:
    name = f"izt-{snapshot.dispatch_id}"
    if _SAFE_NAME_RE.fullmatch(name) is None:
        raise DispatchError("scheduler job name is unsafe")
    return name


def qsub_argv(
    *,
    snapshot: Snapshot,
    policy: DispatchPolicy,
    authorization_path: Path,
    runner_result_path: Path,
    job_script: Path,
) -> tuple[str, ...]:
    snapshot_policy = load_policy(
        snapshot.snapshot_root
        / "tools"
        / "pegasus"
        / "test_dispatch_policy.json"
    )
    if (
        policy.policy_sha256 != snapshot.policy_sha256
        or snapshot_policy.policy_sha256 != snapshot.policy_sha256
        or policy != snapshot_policy
    ):
        raise DispatchError("qsub policy differs from snapshot-bound policy")
    _bound_snapshot_file(snapshot, job_script, require_executable=True)
    stdout_path = snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stdout"
    stderr_path = snapshot.dispatch_dir / f"{snapshot.dispatch_id}.stderr"
    export_values = {
        "IZANAGI_TEST_DISPATCH_ID": snapshot.dispatch_id,
        "IZANAGI_TEST_DISPATCH_DIR": str(snapshot.dispatch_dir),
        "IZANAGI_TEST_SNAPSHOT_ROOT": str(snapshot.snapshot_root),
        "IZANAGI_TEST_WORKER_AUTH": str(authorization_path),
        "IZANAGI_TEST_RUNNER_RESULT": str(runner_result_path),
    }
    if any(
        not value or any(character in value for character in ",\r\n")
        for value in export_values.values()
    ):
        raise DispatchError("qsub export value is unsafe")
    exports = ",".join(
        f"{name}={value}" for name, value in export_values.items()
    )
    return (
        "qsub",
        "-A", policy.account,
        "-q", policy.queue,
        "-b", str(policy.nodes),
        "-l", f"elapstim_req={policy.walltime}",
        "-N", scheduler_job_name(snapshot),
        "-o", str(stdout_path),
        "-e", str(stderr_path),
        "-v", exports,
        str(job_script),
    )


class ControllerSignal(Exception):
    def __init__(self, signum: int) -> None:
        super().__init__(f"controller received signal {signum}")
        self.signum = signum


class _SignalGuard:
    def __init__(self) -> None:
        self.previous: dict[int, Any] = {}

    def __enter__(self) -> "_SignalGuard":
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            self.previous[signum] = signal.getsignal(signum)
            signal.signal(signum, self._handle)
        return self

    def _handle(self, signum: int, _frame: Any) -> None:
        raise ControllerSignal(signum)

    def __exit__(self, *_args: object) -> None:
        for signum, handler in self.previous.items():
            signal.signal(signum, handler)


def _publish_terminal_final(
    *,
    snapshot: Snapshot,
    filesystem: MonitorFilesystem,
    journal: Path,
    outcome: str,
    controller_status: int,
    controller_signal: int | None,
    qsub_request_sha256: str,
    authorization_sha256: str,
    qsub_result_sha256: str,
    submit_receipt_sha256: str | None,
    qsub_request_id_raw: str | None,
    job_id_normalized: str | None,
    qsub_started_epoch_s: float,
    absolute_deadline_epoch_s: float,
    terminal_phase: str,
    failure_reason: str,
    clock: Callable[[], float],
) -> int:
    final = {
        "schema": "izanagi-test-final-v2",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "qsub_request_sha256": qsub_request_sha256,
        "authorization_sha256": authorization_sha256,
        "qsub_result_sha256": qsub_result_sha256,
        "submit_receipt_sha256": submit_receipt_sha256,
        "qsub_request_id_raw": qsub_request_id_raw,
        "pbs_job_id_raw": None,
        "job_id_normalized": job_id_normalized,
        "dispatch_outcome": outcome,
        "controller_exit_status": controller_status,
        "controller_signal": controller_signal,
        "child_exit_status": None,
        "child_signal": None,
        "pytest_exit_status": None,
        "pytest_signal": None,
        "runner_stage": None,
        "runner_result": None,
        "worker_environment": None,
        "runner_claim": None,
        "task_run_attempted": None,
        "task_run_event_id": None,
        "task_run_event": None,
        "stdout": None,
        "stderr": None,
        "accounting": None,
        "terminal_phase": terminal_phase,
        "qsub_started_epoch_s": qsub_started_epoch_s,
        "absolute_deadline_epoch_s": absolute_deadline_epoch_s,
        "failure_reason": failure_reason,
    }
    _stage_and_publish_final(
        snapshot=snapshot,
        filesystem=filesystem,
        journal=journal,
        document=final,
        clock=clock,
    )
    return controller_status


def _recover_submission_identity(
    *,
    snapshot: Snapshot,
    scheduler: Scheduler,
    policy: DispatchPolicy,
    authorization_sha256: str,
    qsub_request_sha256: str,
    qsub_result_sha256: str,
    qsub_started_epoch_s: float,
    absolute_deadline_epoch_s: float,
    journal: Path,
    clock: Callable[[], float],
    wall_clock: Callable[[], float],
    sleep: Callable[[float], None],
    filesystem: MonitorFilesystem,
) -> tuple[SchedulerLookup, str | None]:
    lookup = lookup_scheduler_job(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        qsub_request_sha256=qsub_request_sha256,
        qsub_result_sha256=qsub_result_sha256,
        qsub_started_epoch_s=qsub_started_epoch_s,
        absolute_deadline_epoch_s=absolute_deadline_epoch_s,
        clock=clock,
        wall_clock=wall_clock,
        sleep=sleep,
        filesystem=filesystem,
    )
    if (
        lookup.request_id_raw is None
        or lookup.job_id_normalized is None
    ):
        return lookup, None
    _, submit_receipt_sha = create_submit_receipt(
        snapshot,
        authorization_sha256=authorization_sha256,
        qsub_request_sha256=qsub_request_sha256,
        qsub_result_sha256=qsub_result_sha256,
        qsub_request_id_raw=lookup.request_id_raw,
        job_id_normalized=lookup.job_id_normalized,
    )
    append_journal(journal, {
        "event": "submit-identified",
        "identification_source": "scheduler-lookup",
        "qsub_request_sha256": qsub_request_sha256,
        "qsub_result_sha256": qsub_result_sha256,
        "qsub_request_id_raw": lookup.request_id_raw,
        "job_id_normalized": lookup.job_id_normalized,
        "submit_receipt_sha256": submit_receipt_sha,
        "monotonic_s": clock(),
    })
    return lookup, submit_receipt_sha


def submit_and_monitor(
    *,
    snapshot: Snapshot,
    scheduler: Scheduler,
    policy: DispatchPolicy,
    job_script: Path,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
    filesystem: MonitorFilesystem | None = None,
) -> int:
    fs = PathMonitorFilesystem() if filesystem is None else filesystem
    journal = snapshot.dispatch_dir / "dispatch-journal.jsonl"
    verify_snapshot_tree(snapshot, policy)
    verify_execution_closure(snapshot)
    authorization_path = snapshot.dispatch_dir / "pre-submit-authorization.json"
    runner_result = snapshot.dispatch_dir / "runner-result.json"
    argv = qsub_argv(
        snapshot=snapshot,
        policy=policy,
        authorization_path=authorization_path,
        runner_result_path=runner_result,
        job_script=job_script,
    )
    qsub_environment = scheduler_environment()
    qsub_started = wall_clock()
    _, qsub_request_sha, absolute_deadline = create_qsub_request(
        snapshot,
        policy=policy,
        argv=argv,
        environment=qsub_environment,
        job_script=job_script,
        qsub_started_epoch_s=qsub_started,
    )
    authorization_path, authorization_sha = create_pre_submit_authorization(
        snapshot,
        qsub_request_sha256=qsub_request_sha,
    )
    append_journal(journal, {
        "event": "pre-submit-authorized",
        "dispatch_id": snapshot.dispatch_id,
        "snapshot_manifest_sha256": snapshot.manifest_sha256,
        "execution_closure_sha256": snapshot.execution_closure_sha256,
        "policy_sha256": snapshot.policy_sha256,
        "qsub_request_sha256": qsub_request_sha,
        "authorization_sha256": authorization_sha,
        "monotonic_s": clock(),
    })
    append_journal(journal, {
        "event": "qsub-intent",
        "qsub_request_sha256": qsub_request_sha,
        "monotonic_s": clock(),
    })
    qsub_raw: str | None = None
    normalized: str | None = None
    qsub_result_sha: str | None = None
    submit_receipt_sha: str | None = None
    lookup_hosts: tuple[str, ...] = ()
    try:
        with _SignalGuard():
            try:
                result = scheduler.run(
                    argv,
                    timeout=policy.command_timeout_s,
                    environment=qsub_environment,
                )
            except (subprocess.TimeoutExpired, TimeoutError) as exc:
                result = CommandResult(
                    tuple(argv),
                    124,
                    "",
                    f"qsub timeout: {exc}",
                    timed_out=True,
                    completion_unknown=True,
                )
            except OSError as exc:
                result = CommandResult(
                    tuple(argv),
                    126,
                    "",
                    f"qsub acceptance unknown after OSError: {exc}",
                    completion_unknown=True,
                )
            identification_error: DispatchError | None = None
            if (
                result.returncode == 0
                and not result.timed_out
                and not result.output_limited
                and result.signal is None
            ):
                try:
                    qsub_raw, normalized = parse_qsub_id(result.stdout)
                except DispatchError as exc:
                    identification_error = exc
            _, qsub_result_sha = create_qsub_result(
                snapshot,
                qsub_request_sha256=qsub_request_sha,
                result=result,
            )
            append_journal(journal, {
                "event": "qsub-return",
                "qsub_result_sha256": qsub_result_sha,
                "returncode": result.returncode,
                "signal": result.signal,
                "timed_out": result.timed_out,
                "output_limited": result.output_limited,
                "completion_unknown": result.completion_unknown,
                "monotonic_s": clock(),
            })
            unknown_completion = result.completion_unknown
            if result.returncode != 0 and not unknown_completion:
                append_journal(journal, {
                    "event": "submit-failed",
                    "monotonic_s": clock(),
                })
                return _publish_terminal_final(
                    snapshot=snapshot,
                    filesystem=fs,
                    journal=journal,
                    outcome="SUBMIT_FAILED",
                    controller_status=125,
                    controller_signal=None,
                    qsub_request_sha256=qsub_request_sha,
                    authorization_sha256=authorization_sha,
                    qsub_result_sha256=qsub_result_sha,
                    submit_receipt_sha256=None,
                    qsub_request_id_raw=None,
                    job_id_normalized=None,
                    qsub_started_epoch_s=qsub_started,
                    absolute_deadline_epoch_s=absolute_deadline,
                    terminal_phase="qsub",
                    failure_reason=f"qsub failed rc={result.returncode}",
                    clock=clock,
                )
            if unknown_completion or identification_error is not None:
                lookup, recovered_submit_sha = _recover_submission_identity(
                    snapshot=snapshot,
                    scheduler=scheduler,
                    policy=policy,
                    authorization_sha256=authorization_sha,
                    qsub_request_sha256=qsub_request_sha,
                    qsub_result_sha256=qsub_result_sha,
                    qsub_started_epoch_s=qsub_started,
                    absolute_deadline_epoch_s=absolute_deadline,
                    journal=journal,
                    clock=clock,
                    wall_clock=wall_clock,
                    sleep=sleep,
                    filesystem=fs,
                )
                if (
                    lookup.request_id_raw is None
                    or lookup.job_id_normalized is None
                    or recovered_submit_sha is None
                ):
                    reason = (
                        f"{identification_error}; {lookup.reason}"
                        if identification_error is not None
                        else lookup.reason
                    )
                    append_journal(journal, {
                        "event": "submit-unknown",
                        "reason": reason,
                        "monotonic_s": clock(),
                    })
                    return _publish_terminal_final(
                        snapshot=snapshot,
                        filesystem=fs,
                        journal=journal,
                        outcome="SUBMIT_UNKNOWN",
                        controller_status=125,
                        controller_signal=None,
                        qsub_request_sha256=qsub_request_sha,
                        authorization_sha256=authorization_sha,
                        qsub_result_sha256=qsub_result_sha,
                        submit_receipt_sha256=None,
                        qsub_request_id_raw=None,
                        job_id_normalized=None,
                        qsub_started_epoch_s=qsub_started,
                        absolute_deadline_epoch_s=absolute_deadline,
                        terminal_phase="scheduler-lookup",
                        failure_reason=reason,
                        clock=clock,
                    )
                qsub_raw = lookup.request_id_raw
                normalized = lookup.job_id_normalized
                lookup_hosts = lookup.execution_hosts
                submit_receipt_sha = recovered_submit_sha
            if unknown_completion:
                cancel_succeeded = cancel_job(
                    scheduler=scheduler,
                    job_id_normalized=normalized,
                    policy=policy,
                    journal_path=journal,
                    clock=clock,
                    sleep=sleep,
                    reason="qsub-unknown-recovered",
                    recovery={
                        "success_outcome": "CANCELED",
                        "failure_outcome": "CANCEL_FAILED",
                        "success_status": 124,
                        "failure_status": 125,
                        "success_signal": None,
                        "failure_signal": None,
                        "terminal_phase": "scheduler-lookup",
                        "failure_reason": (
                            "unknown qsub completion was reconciled and canceled"
                        ),
                    },
                    filesystem=fs,
                )
                return _publish_terminal_final(
                    snapshot=snapshot,
                    filesystem=fs,
                    journal=journal,
                    outcome=(
                        "CANCELED"
                        if cancel_succeeded else "CANCEL_FAILED"
                    ),
                    controller_status=124 if cancel_succeeded else 125,
                    controller_signal=None,
                    qsub_request_sha256=qsub_request_sha,
                    authorization_sha256=authorization_sha,
                    qsub_result_sha256=qsub_result_sha,
                    submit_receipt_sha256=submit_receipt_sha,
                    qsub_request_id_raw=qsub_raw,
                    job_id_normalized=normalized,
                    qsub_started_epoch_s=qsub_started,
                    absolute_deadline_epoch_s=absolute_deadline,
                    terminal_phase="scheduler-lookup",
                    failure_reason="unknown qsub completion was reconciled and canceled",
                    clock=clock,
                )
            if identification_error is not None:
                append_journal(journal, {
                    "event": "qsub-id-recovered",
                    "reason": str(identification_error),
                    "monotonic_s": clock(),
                })
            if qsub_raw is None or normalized is None:
                raise DispatchError("qsub success lacks an identified job")
            if submit_receipt_sha is None:
                _, submit_receipt_sha = create_submit_receipt(
                    snapshot,
                    authorization_sha256=authorization_sha,
                    qsub_request_sha256=qsub_request_sha,
                    qsub_result_sha256=qsub_result_sha,
                    qsub_request_id_raw=qsub_raw,
                    job_id_normalized=normalized,
                )
                append_journal(journal, {
                    "event": "submit-identified",
                    "identification_source": "qsub-result",
                    "qsub_request_sha256": qsub_request_sha,
                    "qsub_result_sha256": qsub_result_sha,
                    "qsub_request_id_raw": qsub_raw,
                    "job_id_normalized": normalized,
                    "submit_receipt_sha256": submit_receipt_sha,
                    "monotonic_s": clock(),
                })
            return monitor_job(
                snapshot=snapshot,
                scheduler=scheduler,
                policy=policy,
                authorization_sha256=authorization_sha,
                qsub_request_sha256=qsub_request_sha,
                qsub_result_sha256=qsub_result_sha,
                submit_receipt_sha256=submit_receipt_sha,
                qsub_request_id_raw=qsub_raw,
                job_id_normalized=normalized,
                qsub_started_epoch_s=qsub_started,
                absolute_deadline_epoch_s=absolute_deadline,
                expected_execution_hosts=lookup_hosts,
                clock=clock,
                wall_clock=wall_clock,
                sleep=sleep,
                filesystem=fs,
            )
    except (ControllerSignal, KeyboardInterrupt) as exc:
        pending_status = _publish_pending_final_if_present(
            snapshot=snapshot,
            filesystem=fs,
        )
        if pending_status is not None:
            return pending_status
        signum = exc.signum if isinstance(exc, ControllerSignal) else signal.SIGINT
        if normalized is None or qsub_raw is None:
            if qsub_result_sha is None:
                interrupted_result = CommandResult(
                    tuple(argv),
                    128 + signum,
                    "",
                    f"controller signal {signum} during qsub",
                    signal=signum,
                    completion_unknown=True,
                )
                _, qsub_result_sha = create_qsub_result(
                    snapshot,
                    qsub_request_sha256=qsub_request_sha,
                    result=interrupted_result,
                )
                append_journal(journal, {
                    "event": "qsub-return",
                    "qsub_result_sha256": qsub_result_sha,
                    "returncode": interrupted_result.returncode,
                    "signal": signum,
                    "timed_out": False,
                    "output_limited": False,
                    "completion_unknown": True,
                    "monotonic_s": clock(),
                })
            lookup, recovered_submit_sha = _recover_submission_identity(
                snapshot=snapshot,
                scheduler=scheduler,
                policy=policy,
                authorization_sha256=authorization_sha,
                qsub_request_sha256=qsub_request_sha,
                qsub_result_sha256=qsub_result_sha,
                qsub_started_epoch_s=qsub_started,
                absolute_deadline_epoch_s=absolute_deadline,
                journal=journal,
                clock=clock,
                wall_clock=wall_clock,
                sleep=sleep,
                filesystem=fs,
            )
            if (
                lookup.request_id_raw is None
                or lookup.job_id_normalized is None
                or recovered_submit_sha is None
            ):
                append_journal(journal, {
                    "event": "submit-unknown",
                    "reason": lookup.reason,
                    "monotonic_s": clock(),
                })
                return _publish_terminal_final(
                    snapshot=snapshot,
                    filesystem=fs,
                    journal=journal,
                    outcome="SUBMIT_UNKNOWN",
                    controller_status=125,
                    controller_signal=None,
                    qsub_request_sha256=qsub_request_sha,
                    authorization_sha256=authorization_sha,
                    qsub_result_sha256=qsub_result_sha,
                    submit_receipt_sha256=None,
                    qsub_request_id_raw=None,
                    job_id_normalized=None,
                    qsub_started_epoch_s=qsub_started,
                    absolute_deadline_epoch_s=absolute_deadline,
                    terminal_phase="scheduler-lookup",
                    failure_reason=(
                        f"controller signal {signum} before job identification; "
                        f"{lookup.reason}"
                    ),
                    clock=clock,
                )
            qsub_raw = lookup.request_id_raw
            normalized = lookup.job_id_normalized
            lookup_hosts = lookup.execution_hosts
            submit_receipt_sha = recovered_submit_sha
        cancel_succeeded = cancel_job(
            scheduler=scheduler,
            job_id_normalized=normalized,
            policy=policy,
            journal_path=journal,
            clock=clock,
            sleep=sleep,
            reason=f"controller-signal-{signum}",
            recovery={
                "success_outcome": "INTERRUPTED",
                "failure_outcome": "INTERRUPT_CANCEL_FAILED",
                "success_status": 128 + signum,
                "failure_status": 125,
                "success_signal": signum,
                "failure_signal": None,
                "terminal_phase": "controller",
                "failure_reason": f"controller received signal {signum}",
            },
            filesystem=fs,
        )
        if qsub_result_sha is None:
            raise DispatchError(
                "qsub job was canceled but qsub result sealing failed"
            ) from exc
        status = 128 + signum if cancel_succeeded else 125
        return _publish_terminal_final(
            snapshot=snapshot,
            filesystem=fs,
            journal=journal,
            outcome=(
                "INTERRUPTED" if cancel_succeeded else "INTERRUPT_CANCEL_FAILED"
            ),
            controller_status=status,
            controller_signal=signum if cancel_succeeded else None,
            qsub_request_sha256=qsub_request_sha,
            authorization_sha256=authorization_sha,
            qsub_result_sha256=qsub_result_sha,
            submit_receipt_sha256=submit_receipt_sha,
            qsub_request_id_raw=qsub_raw,
            job_id_normalized=normalized,
            qsub_started_epoch_s=qsub_started,
            absolute_deadline_epoch_s=absolute_deadline,
            terminal_phase="controller",
            failure_reason=f"controller received signal {signum}",
            clock=clock,
        )
    except (DispatchError, OSError, ValueError) as exc:
        pending_status = _publish_pending_final_if_present(
            snapshot=snapshot,
            filesystem=fs,
        )
        if pending_status is not None:
            return pending_status
        final_path = snapshot.dispatch_dir / "final-receipt.json"
        if final_path.exists():
            try:
                final = load_final_receipt(final_path, snapshot=snapshot)
                return int(final["controller_exit_status"])
            except DispatchError:
                pass
        if normalized is None or qsub_raw is None:
            raise
        cancel_succeeded = cancel_job(
            scheduler=scheduler,
            job_id_normalized=normalized,
            policy=policy,
            journal_path=journal,
            clock=clock,
            sleep=sleep,
            reason="controller-failure",
            recovery={
                "success_outcome": "CONTROLLER_FAILURE",
                "failure_outcome": "CONTROLLER_CANCEL_FAILED",
                "success_status": 125,
                "failure_status": 125,
                "success_signal": None,
                "failure_signal": None,
                "terminal_phase": "controller",
                "failure_reason": f"{type(exc).__name__}: {exc}",
            },
            filesystem=fs,
        )
        append_journal(journal, {
            "event": "controller-failure",
            "reason": f"{type(exc).__name__}: {exc}",
            "cancel_succeeded": cancel_succeeded,
            "monotonic_s": clock(),
        })
        if qsub_result_sha is None:
            raise DispatchError(
                "known qsub job was canceled after receipt sealing failure"
            ) from exc
        if final_path.exists():
            return 125
        return _publish_terminal_final(
            snapshot=snapshot,
            filesystem=fs,
            journal=journal,
            outcome=(
                "CONTROLLER_FAILURE"
                if cancel_succeeded else "CONTROLLER_CANCEL_FAILED"
            ),
            controller_status=125,
            controller_signal=None,
            qsub_request_sha256=qsub_request_sha,
            authorization_sha256=authorization_sha,
            qsub_result_sha256=qsub_result_sha,
            submit_receipt_sha256=submit_receipt_sha,
            qsub_request_id_raw=qsub_raw,
            job_id_normalized=normalized,
            qsub_started_epoch_s=qsub_started,
            absolute_deadline_epoch_s=absolute_deadline,
            terminal_phase="controller",
            failure_reason=f"{type(exc).__name__}: {exc}",
            clock=clock,
        )
    except BaseException as exc:
        # Once qsub yielded an exact ID, even an unexpected Python exception
        # must pass through the same compensation boundary before propagating
        # or publishing a terminal controller outcome.
        pending_status = _publish_pending_final_if_present(
            snapshot=snapshot,
            filesystem=fs,
        )
        if pending_status is not None:
            return pending_status
        final_path = snapshot.dispatch_dir / "final-receipt.json"
        if final_path.exists():
            try:
                final = load_final_receipt(final_path, snapshot=snapshot)
                return int(final["controller_exit_status"])
            except DispatchError:
                pass
        if normalized is None or qsub_raw is None:
            raise
        cancel_succeeded = cancel_job(
            scheduler=scheduler,
            job_id_normalized=normalized,
            policy=policy,
            journal_path=journal,
            clock=clock,
            sleep=sleep,
            reason="unexpected-controller-failure",
            recovery={
                "success_outcome": "CONTROLLER_FAILURE",
                "failure_outcome": "CONTROLLER_CANCEL_FAILED",
                "success_status": 125,
                "failure_status": 125,
                "success_signal": None,
                "failure_signal": None,
                "terminal_phase": "controller",
                "failure_reason": f"{type(exc).__name__}: {exc}",
            },
            filesystem=fs,
        )
        append_journal(journal, {
            "event": "controller-failure",
            "reason": f"{type(exc).__name__}: {exc}",
            "cancel_succeeded": cancel_succeeded,
            "monotonic_s": clock(),
        })
        if qsub_result_sha is None:
            raise DispatchError(
                "known qsub job was canceled after unexpected receipt failure"
            ) from exc
        return _publish_terminal_final(
            snapshot=snapshot,
            filesystem=fs,
            journal=journal,
            outcome=(
                "CONTROLLER_FAILURE"
                if cancel_succeeded else "CONTROLLER_CANCEL_FAILED"
            ),
            controller_status=125,
            controller_signal=None,
            qsub_request_sha256=qsub_request_sha,
            authorization_sha256=authorization_sha,
            qsub_result_sha256=qsub_result_sha,
            submit_receipt_sha256=submit_receipt_sha,
            qsub_request_id_raw=qsub_raw,
            job_id_normalized=normalized,
            qsub_started_epoch_s=qsub_started,
            absolute_deadline_epoch_s=absolute_deadline,
            terminal_phase="controller",
            failure_reason=f"{type(exc).__name__}: {exc}",
            clock=clock,
        )


def snapshot_from_dispatch(dispatch_dir: Path) -> Snapshot:
    try:
        dispatch_info = dispatch_dir.lstat()
        resolved_dispatch = dispatch_dir.resolve(strict=True)
    except OSError as exc:
        raise DispatchError(f"dispatch directory is unavailable: {exc}") from None
    if (
        not stat.S_ISDIR(dispatch_info.st_mode)
        or stat.S_ISLNK(dispatch_info.st_mode)
        or _DISPATCH_ID_RE.fullmatch(dispatch_dir.name) is None
    ):
        raise DispatchError("dispatch directory identity is unsafe")
    manifest, raw = _load_exact_json(dispatch_dir / "snapshot-manifest.json")
    if (
        set(manifest) != {
            "schema", "dispatch_id", "head", "source_state",
            "cached_patch_sha256", "unstaged_patch_sha256", "untracked",
            "ignored_inputs", "submodules", "pytest_argv",
            "runner_environment", "preflight", "policy",
            "execution_closure", "execution_closure_sha256",
            "snapshot_tree", "snapshot_semantics",
        }
        or manifest.get("schema") != "izanagi-test-snapshot-v2"
    ):
        raise DispatchError("snapshot manifest keys/schema are invalid")
    dispatch_id = manifest.get("dispatch_id")
    if not isinstance(dispatch_id, str) or _DISPATCH_ID_RE.fullmatch(dispatch_id) is None:
        raise DispatchError("snapshot manifest dispatch ID is invalid")
    argv = manifest.get("pytest_argv")
    if type(argv) is not list or not all(type(item) is dict for item in argv):
        raise DispatchError("snapshot manifest argv is invalid")
    runner_environment = manifest.get("runner_environment")
    if (
        type(runner_environment) is not dict
        or not all(
            key in _RUNNER_ENV_ALLOWLIST
            and isinstance(value, str)
            for key, value in runner_environment.items()
        )
    ):
        raise DispatchError("snapshot runner environment is invalid")
    closure_sha = manifest.get("execution_closure_sha256")
    snapshot_tree = manifest.get("snapshot_tree")
    policy_record = manifest.get("policy")
    if (
        not isinstance(closure_sha, str)
        or _HEX64_RE.fullmatch(closure_sha) is None
        or type(snapshot_tree) is not dict
        or set(snapshot_tree) != {
            "file_count", "total_bytes", "sha256", "entries",
        }
        or _HEX64_RE.fullmatch(str(snapshot_tree.get("sha256"))) is None
        or type(policy_record) is not dict
        or set(policy_record) != {"path", "sha256"}
        or policy_record.get("path") != "tools/pegasus/test_dispatch_policy.json"
        or _HEX64_RE.fullmatch(str(policy_record.get("sha256"))) is None
    ):
        raise DispatchError("snapshot manifest closure/policy/tree is invalid")
    tree_entries = snapshot_tree.get("entries")
    tree_keys = {"path", "kind", "mode", "size", "sha256", "link_target"}
    if (
        type(tree_entries) is not list
        or not all(
            type(entry) is dict
            and set(entry) == tree_keys
            and isinstance(entry.get("path"), str)
            and not Path(str(entry["path"])).is_absolute()
            and ".." not in Path(str(entry["path"])).parts
            and entry.get("kind") in {"file", "symlink"}
            and type(entry.get("mode")) is int
            and type(entry.get("size")) is int
            and int(entry["size"]) >= 0
            and _HEX64_RE.fullmatch(str(entry.get("sha256"))) is not None
            and (
                (
                    entry["kind"] == "file"
                    and entry.get("link_target") is None
                )
                or (
                    entry["kind"] == "symlink"
                    and isinstance(entry.get("link_target"), str)
                )
            )
            for entry in tree_entries
        )
        or [entry["path"] for entry in tree_entries]
        != sorted({entry["path"] for entry in tree_entries})
        or snapshot_tree.get("file_count") != len(tree_entries)
        or snapshot_tree.get("total_bytes")
        != sum(int(entry["size"]) for entry in tree_entries)
        or snapshot_tree.get("sha256")
        != sha256_bytes(_canonical_json(tree_entries))
    ):
        raise DispatchError("snapshot execution-tree inventory is invalid")
    snapshot_root_lexical = dispatch_dir / "source"
    try:
        snapshot_root_info = snapshot_root_lexical.lstat()
        snapshot_root = snapshot_root_lexical.resolve(strict=True)
    except OSError as exc:
        raise DispatchError(f"snapshot source root is unavailable: {exc}") from None
    if (
        not stat.S_ISDIR(snapshot_root_info.st_mode)
        or stat.S_ISLNK(snapshot_root_info.st_mode)
        or snapshot_root.parent != resolved_dispatch
    ):
        raise DispatchError("snapshot source root identity is unsafe")
    snapshot_policy = load_policy(
        snapshot_root / "tools" / "pegasus" / "test_dispatch_policy.json"
    )
    if snapshot_policy.policy_sha256 != policy_record["sha256"]:
        raise DispatchError("snapshot policy hash differs from manifest")
    return Snapshot(
        dispatch_id=dispatch_id,
        dispatch_dir=resolved_dispatch,
        snapshot_root=snapshot_root,
        manifest_path=dispatch_dir / "snapshot-manifest.json",
        manifest_sha256=sha256_bytes(raw),
        encoded_argv=tuple(argv),
        runner_environment=runner_environment,
        execution_closure_sha256=closure_sha,
        policy_sha256=str(policy_record["sha256"]),
        snapshot_tree_sha256=str(snapshot_tree["sha256"]),
    )


def verify_snapshot_tree(snapshot: Snapshot, policy: DispatchPolicy) -> str:
    manifest, _ = _load_exact_json(snapshot.manifest_path)
    expected = manifest.get("snapshot_tree")
    observed = _tree_summary(snapshot.snapshot_root, policy)
    if observed != expected or observed["sha256"] != snapshot.snapshot_tree_sha256:
        raise DispatchError("snapshot source tree drifted before worker execution")
    return str(observed["sha256"])


def _bind_resumed_submit_identity(
    *,
    dispatch_dir: Path,
    submit_events: Sequence[Mapping[str, object]],
    lookup_identity: tuple[str, str] | None,
    clean_return: bool,
    qsub_request_id_raw: str,
    job_id_normalized: str,
) -> None:
    """Bind a resumed submit receipt to every hash-bound identity witness.

    `_validate_submit_object` only checks that the receipt is internally
    consistent, so a receipt naming somebody else's NQSV request would be
    adopted verbatim and could reach qdel or monitor without a single
    scheduler round trip.  Three witnesses are hash-bound, and each of them is
    produced by one of the three writers of `submit-receipt.json`:

    * the `submit-identified` WAL row.  `_validate_scheduler_lookup_chain`
      already compares that row against the receipt when a final document is
      published, so reading it any more weakly here is exactly the asymmetry
      "rejected at publish, accepted before qdel";
    * the matched `scheduler-lookup-result` WAL candidate, which
      `lookup_scheduler_job` appends *before* `_recover_submission_identity`
      creates the receipt;
    * `qsub.stdout`, hash-bound through `qsub-result.json`, which has already
      been verified with `verify_files=True` at this point.

    Every witness that is present must agree, and at least one must be
    present.  The writers make that requirement safe on a crash between the
    receipt and its WAL row: a receipt only ever exists after a matched lookup
    row was appended (`_recover_submission_identity`) or after `parse_qsub_id`
    accepted `qsub.stdout` on a clean return, so one witness always survives.
    """
    witnessed = False
    for event in submit_events:
        event_identity = (
            event.get("qsub_request_id_raw"),
            event.get("job_id_normalized"),
        )
        if event_identity != (qsub_request_id_raw, job_id_normalized):
            raise DispatchError(
                "resume submit receipt identity differs from the "
                "submit-identified WAL receipt: "
                f"receipt={(qsub_request_id_raw, job_id_normalized)!r} "
                f"wal={event_identity!r}"
            )
        witnessed = True
    if lookup_identity is not None:
        if lookup_identity != (qsub_request_id_raw, job_id_normalized):
            raise DispatchError(
                "resume submit receipt identity differs from the matched "
                "scheduler-lookup WAL candidate: "
                f"receipt={(qsub_request_id_raw, job_id_normalized)!r} "
                f"candidate={lookup_identity!r}"
            )
        witnessed = True
    if clean_return:
        stdout_text = (dispatch_dir / "qsub.stdout").read_text(encoding="utf-8")
        try:
            stdout_identity = parse_qsub_id(stdout_text)
        except DispatchError:
            stdout_identity = None
        if stdout_identity is not None:
            if stdout_identity != (qsub_request_id_raw, job_id_normalized):
                raise DispatchError(
                    "resume submit receipt identity differs from the "
                    "qsub.stdout receipt: "
                    f"receipt={(qsub_request_id_raw, job_id_normalized)!r} "
                    f"qsub_stdout={stdout_identity!r}"
                )
            witnessed = True
    if not witnessed:
        raise DispatchError(
            "resume submit receipt identity has no hash-bound witness: "
            "no submit-identified WAL row, no matched scheduler-lookup "
            "candidate, and no parsable qsub.stdout receipt binds "
            f"{(qsub_request_id_raw, job_id_normalized)!r}"
        )


def resume_dispatch(
    *,
    dispatch_dir: Path,
    scheduler: Scheduler,
    policy: DispatchPolicy,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
    filesystem: MonitorFilesystem | None = None,
) -> int:
    fs = PathMonitorFilesystem() if filesystem is None else filesystem
    snapshot = snapshot_from_dispatch(dispatch_dir)
    snapshot_policy = load_policy(
        snapshot.snapshot_root
        / "tools"
        / "pegasus"
        / "test_dispatch_policy.json"
    )
    if policy != snapshot_policy or policy.policy_sha256 != snapshot.policy_sha256:
        raise DispatchError("resume policy differs from snapshot-bound policy")
    final_path = dispatch_dir / "final-receipt.json"
    if fs.exists(final_path):
        final = validate_final_receipt_object(
            fs.load_object(final_path),
            snapshot=snapshot,
            verify_files=isinstance(fs, PathMonitorFilesystem),
        )
        if final.get("dispatch_outcome") == "SUBMIT_UNKNOWN":
            raise DispatchError(
                "SUBMIT_UNKNOWN requires manual scheduler reconciliation; "
                "resume will not re-qsub"
            )
        return int(final["controller_exit_status"])
    pending_status = _publish_pending_final_if_present(
        snapshot=snapshot,
        filesystem=fs,
    )
    if pending_status is not None:
        return pending_status
    journal = dispatch_dir / "dispatch-journal.jsonl"
    if journal_head_sha256(journal) is None:
        raise DispatchError("resume requires a hash-chained dispatch WAL")
    request, request_raw = _load_exact_json(dispatch_dir / "qsub-request.json")
    authorization, auth_raw = _load_exact_json(
        dispatch_dir / "pre-submit-authorization.json"
    )
    request_sha = sha256_bytes(request_raw)
    auth_sha = sha256_bytes(auth_raw)
    _validate_qsub_request_object(request, snapshot=snapshot)
    _validate_authorization_object(
        authorization,
        snapshot=snapshot,
        qsub_request_sha256=request_sha,
    )
    payloads = _journal_payloads(journal)
    pre_submit_matches = [
        index for index, payload in enumerate(payloads)
        if payload.get("event") == "pre-submit-authorized"
        and payload.get("dispatch_id") == snapshot.dispatch_id
        and payload.get("snapshot_manifest_sha256") == snapshot.manifest_sha256
        and payload.get("execution_closure_sha256")
        == snapshot.execution_closure_sha256
        and payload.get("policy_sha256") == snapshot.policy_sha256
        and payload.get("qsub_request_sha256") == request_sha
        and payload.get("authorization_sha256") == auth_sha
    ]
    intent_matches = [
        index for index, payload in enumerate(payloads)
        if payload.get("event") == "qsub-intent"
        and payload.get("qsub_request_sha256") == request_sha
    ]
    if (
        len(pre_submit_matches) != 1
        or len(intent_matches) != 1
        or pre_submit_matches[0] >= intent_matches[0]
    ):
        raise DispatchError(
            "resume requires one ordered pre-submit/qsub intent"
        )
    started = request.get("qsub_started_epoch_s")
    deadline = request.get("absolute_deadline_epoch_s")
    if (
        type(started) not in (int, float)
        or isinstance(started, bool)
        or type(deadline) not in (int, float)
        or isinstance(deadline, bool)
        or deadline != started + policy.global_deadline_s
    ):
        raise DispatchError("resume qsub-origin deadline is invalid")
    result_path = dispatch_dir / "qsub-result.json"
    if result_path.exists():
        qsub_result, qsub_result_raw = _load_exact_json(result_path)
        result_sha = sha256_bytes(qsub_result_raw)
        _validate_qsub_result_object(
            qsub_result,
            snapshot=snapshot,
            qsub_request_sha256=request_sha,
            request=request,
            verify_files=True,
        )
    else:
        if any(
            payload.get("event") == "qsub-return" for payload in payloads
        ):
            raise DispatchError("resume qsub-return lacks its result artifact")
        synthetic = CommandResult(
            tuple(str(item) for item in request["argv"]),
            126,
            "",
            "controller resumed after durable qsub intent without a result",
            completion_unknown=True,
        )
        _, result_sha = create_qsub_result(
            snapshot,
            qsub_request_sha256=request_sha,
            result=synthetic,
        )
        qsub_result, _ = _load_exact_json(result_path)
    return_matches = [
        payload for payload in _journal_payloads(journal)
        if payload.get("event") == "qsub-return"
    ]
    expected_return = {
        "event": "qsub-return",
        "qsub_result_sha256": result_sha,
        "returncode": qsub_result["returncode"],
        "signal": qsub_result["signal"],
        "timed_out": qsub_result["timed_out"],
        "output_limited": qsub_result["output_limited"],
        "completion_unknown": qsub_result["completion_unknown"],
    }
    if not return_matches:
        append_journal(journal, {
            **expected_return,
            "monotonic_s": clock(),
        })
    elif (
        len(return_matches) != 1
        or any(
            return_matches[0].get(name) != value
            for name, value in expected_return.items()
        )
    ):
        raise DispatchError("resume qsub result WAL is inconsistent")
    unknown_completion = qsub_result.get("completion_unknown") is True
    clean_return = (
        qsub_result.get("returncode") == 0 and not unknown_completion
    )
    if not clean_return and not unknown_completion:
        if not any(
            payload.get("event") == "submit-failed"
            for payload in _journal_payloads(journal)
        ):
            append_journal(journal, {
                "event": "submit-failed",
                "monotonic_s": clock(),
            })
        return _publish_terminal_final(
            snapshot=snapshot,
            filesystem=fs,
            journal=journal,
            outcome="SUBMIT_FAILED",
            controller_status=125,
            controller_signal=None,
            qsub_request_sha256=request_sha,
            authorization_sha256=auth_sha,
            qsub_result_sha256=result_sha,
            submit_receipt_sha256=None,
            qsub_request_id_raw=None,
            job_id_normalized=None,
            qsub_started_epoch_s=float(started),
            absolute_deadline_epoch_s=float(deadline),
            terminal_phase="qsub",
            failure_reason=f"qsub failed rc={qsub_result['returncode']}",
            clock=clock,
        )
    qsub_raw: str | None = None
    normalized: str | None = None
    submit_sha: str | None = None
    lookup_hosts: tuple[str, ...] = ()
    submit_path = dispatch_dir / "submit-receipt.json"
    if submit_path.exists():
        submit, submit_raw = _load_exact_json(submit_path)
        submit_sha = sha256_bytes(submit_raw)
        _validate_submit_object(
            submit,
            snapshot=snapshot,
            authorization_sha256=auth_sha,
            qsub_request_sha256=request_sha,
            qsub_result_sha256=result_sha,
        )
        qsub_raw = str(submit["qsub_request_id_raw"])
        normalized = str(submit["job_id_normalized"])
        matched_results = [
            payload for payload in _journal_payloads(journal)
            if payload.get("event") == "scheduler-lookup-result"
            and payload.get("disposition") == "matched"
            and type(payload.get("candidates")) is list
            and len(payload["candidates"]) == 1
            and payload["candidates"][0].get("job_id_normalized")
            == normalized
        ]
        lookup_identity: tuple[str, str] | None = None
        if matched_results:
            (
                candidate_raw,
                candidate_normalized,
                _,
                lookup_hosts,
            ) = _policy_bound_lookup_candidate(
                matched_results[-1]["candidates"][0],
                exact_job_name=scheduler_job_name(snapshot),
                policy=policy,
                expected_user=str(request["submit_user"]),
                qsub_started_epoch_s=float(started),
            )
            lookup_identity = (candidate_raw, candidate_normalized)
        submit_matches = [
            payload
            for payload in _journal_payloads(journal)
            if payload.get("event") == "submit-identified"
        ]
        if len(submit_matches) > 1:
            raise DispatchError("resume submit identity WAL is duplicated")
        _bind_resumed_submit_identity(
            dispatch_dir=dispatch_dir,
            submit_events=submit_matches,
            lookup_identity=lookup_identity,
            clean_return=clean_return,
            qsub_request_id_raw=qsub_raw,
            job_id_normalized=normalized,
        )
        if not submit_matches:
            append_journal(journal, {
                "event": "submit-identified",
                "identification_source": (
                    "scheduler-lookup"
                    if matched_results else "qsub-result-resume"
                ),
                "qsub_request_sha256": request_sha,
                "qsub_result_sha256": result_sha,
                "qsub_request_id_raw": qsub_raw,
                "job_id_normalized": normalized,
                "submit_receipt_sha256": submit_sha,
                "monotonic_s": clock(),
            })
    elif any(
        payload.get("event") == "submit-identified"
        for payload in _journal_payloads(journal)
    ):
        raise DispatchError("resume submit WAL lacks its receipt")
    if qsub_raw is None and clean_return:
        qsub_stdout = (dispatch_dir / "qsub.stdout").read_text(
            encoding="utf-8"
        )
        try:
            qsub_raw, normalized = parse_qsub_id(qsub_stdout)
        except DispatchError:
            qsub_raw = None
            normalized = None
        else:
            _, submit_sha = create_submit_receipt(
                snapshot,
                authorization_sha256=auth_sha,
                qsub_request_sha256=request_sha,
                qsub_result_sha256=result_sha,
                qsub_request_id_raw=qsub_raw,
                job_id_normalized=normalized,
            )
            append_journal(journal, {
                "event": "submit-identified",
                "identification_source": "qsub-result-resume",
                "qsub_request_sha256": request_sha,
                "qsub_result_sha256": result_sha,
                "qsub_request_id_raw": qsub_raw,
                "job_id_normalized": normalized,
                "submit_receipt_sha256": submit_sha,
                "monotonic_s": clock(),
            })
    if qsub_raw is None or normalized is None or submit_sha is None:
        lookup, submit_sha = _recover_submission_identity(
            snapshot=snapshot,
            scheduler=scheduler,
            policy=policy,
            authorization_sha256=auth_sha,
            qsub_request_sha256=request_sha,
            qsub_result_sha256=result_sha,
            qsub_started_epoch_s=float(started),
            absolute_deadline_epoch_s=float(deadline),
            journal=journal,
            clock=clock,
            wall_clock=wall_clock,
            sleep=sleep,
            filesystem=fs,
        )
        qsub_raw = lookup.request_id_raw
        normalized = lookup.job_id_normalized
        lookup_hosts = lookup.execution_hosts
        if qsub_raw is None or normalized is None or submit_sha is None:
            if not any(
                payload.get("event") == "submit-unknown"
                for payload in _journal_payloads(journal)
            ):
                append_journal(journal, {
                    "event": "submit-unknown",
                    "reason": lookup.reason,
                    "monotonic_s": clock(),
                })
            return _publish_terminal_final(
                snapshot=snapshot,
                filesystem=fs,
                journal=journal,
                outcome="SUBMIT_UNKNOWN",
                controller_status=125,
                controller_signal=None,
                qsub_request_sha256=request_sha,
                authorization_sha256=auth_sha,
                qsub_result_sha256=result_sha,
                submit_receipt_sha256=None,
                qsub_request_id_raw=None,
                job_id_normalized=None,
                qsub_started_epoch_s=float(started),
                absolute_deadline_epoch_s=float(deadline),
                terminal_phase="scheduler-lookup",
                failure_reason=lookup.reason,
                clock=clock,
            )
    cancel_intents = [
        payload for payload in _journal_payloads(journal)
        if payload.get("event") == "cancel-intent"
        and payload.get("job_id_normalized") == normalized
    ]
    if len(cancel_intents) > 1:
        raise DispatchError("resume cancellation intent is not unique")
    if cancel_intents:
        intent = cancel_intents[0]
        recovery = intent.get("recovery")
        recovery_keys = {
            "success_outcome", "failure_outcome",
            "success_status", "failure_status",
            "success_signal", "failure_signal",
            "terminal_phase", "failure_reason",
        }
        if (
            type(recovery) is not dict
            or set(recovery) != recovery_keys
            or not isinstance(intent.get("reason"), str)
        ):
            raise DispatchError("resume cancellation recovery plan is invalid")
        cancel_succeeded = cancel_job(
            scheduler=scheduler,
            job_id_normalized=normalized,
            policy=policy,
            journal_path=journal,
            clock=clock,
            sleep=sleep,
            reason=str(intent["reason"]),
            recovery=recovery,
            filesystem=fs,
        )
        outcome_key = (
            "success_outcome" if cancel_succeeded else "failure_outcome"
        )
        status_key = (
            "success_status" if cancel_succeeded else "failure_status"
        )
        signal_key = (
            "success_signal" if cancel_succeeded else "failure_signal"
        )
        return _publish_terminal_final(
            snapshot=snapshot,
            filesystem=fs,
            journal=journal,
            outcome=str(recovery[outcome_key]),
            controller_status=int(recovery[status_key]),
            controller_signal=recovery[signal_key],
            qsub_request_sha256=request_sha,
            authorization_sha256=auth_sha,
            qsub_result_sha256=result_sha,
            submit_receipt_sha256=submit_sha,
            qsub_request_id_raw=qsub_raw,
            job_id_normalized=normalized,
            qsub_started_epoch_s=float(started),
            absolute_deadline_epoch_s=float(deadline),
            terminal_phase=str(recovery["terminal_phase"]),
            failure_reason=str(recovery["failure_reason"]),
            clock=clock,
        )
    if unknown_completion:
        recovery = {
            "success_outcome": "CANCELED",
            "failure_outcome": "CANCEL_FAILED",
            "success_status": 124,
            "failure_status": 125,
            "success_signal": None,
            "failure_signal": None,
            "terminal_phase": "resume-scheduler-lookup",
            "failure_reason": (
                "unknown qsub completion was reconciled and canceled"
            ),
        }
        cancel_succeeded = cancel_job(
            scheduler=scheduler,
            job_id_normalized=normalized,
            policy=policy,
            journal_path=journal,
            clock=clock,
            sleep=sleep,
            reason="resume-qsub-unknown-recovered",
            recovery=recovery,
            filesystem=fs,
        )
        return _publish_terminal_final(
            snapshot=snapshot,
            filesystem=fs,
            journal=journal,
            outcome="CANCELED" if cancel_succeeded else "CANCEL_FAILED",
            controller_status=124 if cancel_succeeded else 125,
            controller_signal=None,
            qsub_request_sha256=request_sha,
            authorization_sha256=auth_sha,
            qsub_result_sha256=result_sha,
            submit_receipt_sha256=submit_sha,
            qsub_request_id_raw=qsub_raw,
            job_id_normalized=normalized,
            qsub_started_epoch_s=float(started),
            absolute_deadline_epoch_s=float(deadline),
            terminal_phase="resume-scheduler-lookup",
            failure_reason="unknown qsub completion was reconciled and canceled",
            clock=clock,
        )
    return monitor_job(
        snapshot=snapshot,
        scheduler=scheduler,
        policy=policy,
        authorization_sha256=auth_sha,
        qsub_request_sha256=request_sha,
        qsub_result_sha256=result_sha,
        submit_receipt_sha256=submit_sha,
        qsub_request_id_raw=qsub_raw,
        job_id_normalized=normalized,
        qsub_started_epoch_s=float(started),
        absolute_deadline_epoch_s=float(deadline),
        expected_execution_hosts=lookup_hosts,
        clock=clock,
        wall_clock=wall_clock,
        sleep=sleep,
        filesystem=fs,
    )


__all__ = [
    "CommandResult",
    "DispatchError",
    "DispatchPolicy",
    "MonitorFilesystem",
    "PathMonitorFilesystem",
    "PollStatus",
    "SchedulerCandidate",
    "SchedulerLookup",
    "Scheduler",
    "Snapshot",
    "SubprocessScheduler",
    "append_journal",
    "authorize_runner",
    "cancel_job",
    "claim_worker",
    "create_snapshot",
    "encode_pytest_argv",
    "load_policy",
    "lookup_scheduler_job",
    "monitor_job",
    "new_dispatch_id",
    "normalize_job_id",
    "parse_qstat",
    "parse_qstat_candidates",
    "parse_qsub_id",
    "qsub_argv",
    "scheduler_job_name",
    "replay_spool",
    "resolve_pytest_argv",
    "resume_dispatch",
    "sha256_file",
    "snapshot_from_dispatch",
    "submit_and_monitor",
    "validate_runner_result",
    "validate_runner_result_object",
]
