#!/usr/bin/env python3
"""Bounded, fail-closed login-side observer for one T-362 request."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any
import uuid


SCHEMA = "t362-signal-observer/v2"
EVENT_SCHEMA = "t362-signal-event/v1"
MARKER_SCHEMA = "t362-signal-marker/v2"
INVENTORY_SCHEMA = "t362-artifact-inventory/v1"
MODES = ("default", "split-warning", "mitigation")
QUE_DEADLINE_SECONDS = 3600
EXECUTION_GRACE_SECONDS = 300
MIN_TERM_WAIT_NS = 4_500_000_000
COMMAND_TIMEOUT_SECONDS = 15
QSTAT_ATTEMPTS = 3
QSTAT_RETRY_SECONDS = 1.0
ACCOUNTING_ATTEMPTS = 5
ACCOUNTING_RETRY_SECONDS = 2.0
FINALIZATION_QSTAT_PHASES = 3  # in-flight poll, deadline recheck, tail
INVENTORY_FILE_COUNT = 2
MAX_INVENTORY_BYTES_PER_FILE = 1024 * 1024
MARKER_FILE_COUNT = 2
MAX_MARKER_BYTES_PER_FILE = 64 * 1024
MAX_CANARY_BYTES = 4096
MAX_CANARY_READ_ATTEMPTS = 32
CANARY_READ_FILE_COUNT = MAX_CANARY_READ_ATTEMPTS + 1  # ack loop + final readback
MAX_INVENTORY_RECORDS_PER_FILE = 4096
MAX_INVENTORY_RELATIVE_PATH_BYTES = 4096
EVENT_LOG_FILE_COUNT = 3
CONTROL_LOG_FILE_COUNT = 3
HEARTBEAT_LOG_FILE_COUNT = 3
SIGNAL_LOG_FILE_COUNT = (
    EVENT_LOG_FILE_COUNT + CONTROL_LOG_FILE_COUNT + HEARTBEAT_LOG_FILE_COUNT
)
MAX_SIGNAL_LOG_BYTES_PER_FILE = 1024 * 1024
MAX_SIGNAL_LOG_RECORDS_PER_FILE = 4096
MAX_WRITER_FAILURE_BYTES = 1024 * 1024
MAX_COMMAND_RAW_BYTES_PER_STREAM = 1024 * 1024
MAX_OBSERVER_QSTAT_INVOCATIONS = 2048
MAX_SCHEDULER_COMMANDS = (
    MAX_OBSERVER_QSTAT_INVOCATIONS * QSTAT_ATTEMPTS
    + 2 * ACCOUNTING_ATTEMPTS
)
MAX_COMMAND_RAW_FILE_COUNT = MAX_SCHEDULER_COMMANDS * 2
MAX_OBSERVER_EVENT_BYTES = 1024 * 1024
MAX_OBSERVER_EVENT_RECORDS = 4096
MAX_CANARY_ACK_BYTES = 64 * 1024
MAX_CLEANUP_RECEIPT_BYTES = 64 * 1024 * 1024
MAX_FINAL_OBSERVATION_BYTES = 64 * 1024 * 1024
FINAL_JSON_PUBLICATION_COUNT = 3  # canary ack, cleanup receipt, final observation
MAX_DISCOVERY_DIRECTORIES = 1024
MAX_DISCOVERY_ENTRIES = 8192
MAX_CLEANUP_TARGETS = 4096
LOCAL_IO_BYTES_PER_SECOND_FLOOR = 64 * 1024
LOCAL_RECORD_UPPER_MILLISECONDS = 20
LOCAL_DIRECTORY_ENTRY_UPPER_MILLISECONDS = 10
LOCAL_UNLINK_UPPER_MILLISECONDS = 50
FINALIZATION_COMMAND_INVOCATIONS = (
    FINALIZATION_QSTAT_PHASES * QSTAT_ATTEMPTS
    + 2 * ACCOUNTING_ATTEMPTS
)
MAX_FINALIZATION_COMMAND_RAW_FILE_COUNT = FINALIZATION_COMMAND_INVOCATIONS * 2
# Each scheduler invocation appends two inventory records, publishes two raw
# streams (file + directory durability for each), and appends one event.
# The fixed tail covers cleanup receipt, final publication, cleanup-root
# durability, and the final observer event.
LOCAL_FSYNC_COUNT = FINALIZATION_COMMAND_INVOCATIONS * 7 + 6
LOCAL_FSYNC_UPPER_SECONDS = COMMAND_TIMEOUT_SECONDS
MAX_FIXED_LOCAL_FSYNC_INVOCATIONS = 9  # canary ack + cleanup/final tail
MAX_LOCAL_FSYNC_INVOCATIONS = (
    MAX_SCHEDULER_COMMANDS * 7 + MAX_FIXED_LOCAL_FSYNC_INVOCATIONS
)
MAX_FINALIZATION_LOCAL_FSYNC_INVOCATIONS = (
    FINALIZATION_COMMAND_INVOCATIONS * 7 + MAX_FIXED_LOCAL_FSYNC_INVOCATIONS
)
MUTATED = b"MUTATED\n"
ORIGINAL = b"ORIGINAL\n"


def _bounded_command_upper_seconds(attempts: int, retry_seconds: float) -> int:
    return int(
        attempts * COMMAND_TIMEOUT_SECONDS + (attempts - 1) * retry_seconds
    )


def _bounded_local_finalization_upper_seconds() -> int:
    inventory_bytes = (
        INVENTORY_FILE_COUNT * MAX_INVENTORY_BYTES_PER_FILE + MAX_CANARY_BYTES
    )
    signal_log_bytes = (
        SIGNAL_LOG_FILE_COUNT * MAX_SIGNAL_LOG_BYTES_PER_FILE
        + MAX_WRITER_FAILURE_BYTES
    )
    raw_command_bytes = (
        FINALIZATION_COMMAND_INVOCATIONS
        * 2
        * MAX_COMMAND_RAW_BYTES_PER_STREAM
    )
    io_seconds = (
        inventory_bytes
        + signal_log_bytes
        + raw_command_bytes
        + MAX_OBSERVER_EVENT_BYTES
        + LOCAL_IO_BYTES_PER_SECOND_FLOOR
        - 1
    ) // LOCAL_IO_BYTES_PER_SECOND_FLOOR
    record_milliseconds = (
        INVENTORY_FILE_COUNT
        * MAX_INVENTORY_RECORDS_PER_FILE
        + SIGNAL_LOG_FILE_COUNT * MAX_SIGNAL_LOG_RECORDS_PER_FILE
        + MAX_OBSERVER_EVENT_RECORDS
    ) * LOCAL_RECORD_UPPER_MILLISECONDS
    discovery_milliseconds = (
        MAX_DISCOVERY_ENTRIES * LOCAL_DIRECTORY_ENTRY_UPPER_MILLISECONDS
    )
    cleanup_milliseconds = MAX_CLEANUP_TARGETS * LOCAL_UNLINK_UPPER_MILLISECONDS
    millisecond_seconds = (
        record_milliseconds
        + discovery_milliseconds
        + cleanup_milliseconds
        + 999
    ) // 1000
    return int(
        io_seconds
        + millisecond_seconds
        + LOCAL_FSYNC_COUNT * LOCAL_FSYNC_UPPER_SECONDS
    )


def _bounded_observer_termination_local_upper_seconds() -> int:
    """Conservatively bound every capped local read/write after monitor stop."""

    bounded_bytes = (
        INVENTORY_FILE_COUNT * MAX_INVENTORY_BYTES_PER_FILE
        + MARKER_FILE_COUNT * MAX_MARKER_BYTES_PER_FILE
        + CANARY_READ_FILE_COUNT * MAX_CANARY_BYTES
        + SIGNAL_LOG_FILE_COUNT * MAX_SIGNAL_LOG_BYTES_PER_FILE
        + MAX_WRITER_FAILURE_BYTES
        + MAX_FINALIZATION_COMMAND_RAW_FILE_COUNT
        * MAX_COMMAND_RAW_BYTES_PER_STREAM
        + MAX_OBSERVER_EVENT_BYTES
        + MAX_CANARY_ACK_BYTES
        + MAX_CLEANUP_RECEIPT_BYTES
        + MAX_FINAL_OBSERVATION_BYTES
    )
    bounded_records = (
        INVENTORY_FILE_COUNT * MAX_INVENTORY_RECORDS_PER_FILE
        + MARKER_FILE_COUNT
        + SIGNAL_LOG_FILE_COUNT * MAX_SIGNAL_LOG_RECORDS_PER_FILE
        + MAX_OBSERVER_EVENT_RECORDS
        + FINAL_JSON_PUBLICATION_COUNT
    )
    io_seconds = (
        bounded_bytes + LOCAL_IO_BYTES_PER_SECOND_FLOOR - 1
    ) // LOCAL_IO_BYTES_PER_SECOND_FLOOR
    local_milliseconds = (
        bounded_records * LOCAL_RECORD_UPPER_MILLISECONDS
        + MAX_DISCOVERY_ENTRIES * LOCAL_DIRECTORY_ENTRY_UPPER_MILLISECONDS
        + MAX_CLEANUP_TARGETS * LOCAL_UNLINK_UPPER_MILLISECONDS
    )
    return int(
        io_seconds
        + (local_milliseconds + 999) // 1000
        + MAX_FINALIZATION_LOCAL_FSYNC_INVOCATIONS
        * LOCAL_FSYNC_UPPER_SECONDS
    )


# At controller monitor completion the observer may still be in a poll and a
# deadline recheck can already be due; finalization also performs a tail qstat.
# All local inventory/read/unlink/fsync work is capped above and contributes to
# the same derived upper bound instead of an unrelated literal timeout.
POST_MONITOR_FINALIZATION_TIMEOUT_SECONDS = (
    FINALIZATION_QSTAT_PHASES
    * _bounded_command_upper_seconds(QSTAT_ATTEMPTS, QSTAT_RETRY_SECONDS)
    + 2
    * _bounded_command_upper_seconds(
        ACCOUNTING_ATTEMPTS, ACCOUNTING_RETRY_SECONDS
    )
    + _bounded_local_finalization_upper_seconds()
)
# A controller/observer race can leave one bounded poll in flight.  Exhausting
# that poll's retry cap now terminates the outer loop fail-closed, so deadline
# recheck and tail remain the only other qstat phases.  The production wait adds
# every capped marker/canary/log/raw/publication/fsync term that can follow them.
OBSERVER_TERMINATION_TIMEOUT_SECONDS = (
    FINALIZATION_QSTAT_PHASES
    * _bounded_command_upper_seconds(QSTAT_ATTEMPTS, QSTAT_RETRY_SECONDS)
    + 2
    * _bounded_command_upper_seconds(
        ACCOUNTING_ATTEMPTS, ACCOUNTING_RETRY_SECONDS
    )
    + _bounded_observer_termination_local_upper_seconds()
)
_REQUEST_ID_RE = re.compile(r"^(?:[0-9]+:)?[A-Za-z0-9][A-Za-z0-9._-]*$")
_REQUEST_ID_FIELD_RE = re.compile(
    r"(?im)^\s*Request\s+ID\s*[:=]\s*(\S+)\s*$"
)
_RUN_NONCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_STATE_RE = re.compile(
    r"(?im)^\s*(?:Request\s+)?State\s*=\s*(QUE|RUN|HLD|STG|EXT)\s*$"
)
_CURRENT_STATE_RE = re.compile(r"(?im)^\s*Current\s+State\s*=\s*([^\r\n]+?)\s*$")
_WALLTIME_LIMIT_CAUSE_RE = re.compile(
    r"(?im)^.*(?:elapse(?:d|stim)?|wall\s*time).*(?:limit|exceed|overrun).*$"
)
_NORMAL_COMPLETION_RE = re.compile(
    r"(?im)^.*(?:exit(?:[_ ]status)?\s*[:=]?\s*0\b|normal(?:ly)?\s+(?:exit|end|termination)).*$"
)
_GENERIC_EXIT_STATUS_RE = re.compile(
    r"(?im)^.*exit(?:[_ ]status)?\s*[:=]?\s*(-?\d+)\b.*$"
)
_DURATION_RE = re.compile(
    r"(?im)^.*(?:resources_used[.]walltime|wall\s*time|elapse(?:d|stim)?)\s*[:=]\s*"
    r"(?:(\d+):(\d{1,2}):(\d{1,2})|(\d+)\s*[sS]?).*$"
)

# Verbatim copy of tools/pegasus/dispatch_compute.py:80-99 (LB-09).
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


class ObserverError(RuntimeError):
    """Fail-closed observer configuration or evidence error."""


def _bounded_fsync(descriptor: int) -> None:
    """Run one fsync under the observer's enforced local-I/O watchdog."""

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise ObserverError(
            f"fsync exceeds {LOCAL_FSYNC_UPPER_SECONDS} second cap"
        )

    previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
    previous_timer = signal.setitimer(
        signal.ITIMER_REAL, LOCAL_FSYNC_UPPER_SECONDS
    )
    started = time.monotonic()
    try:
        os.fsync(descriptor)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            remaining = max(0.0, previous_timer[0] - (time.monotonic() - started))
            signal.setitimer(signal.ITIMER_REAL, remaining, previous_timer[1])


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        _bounded_fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_publish(path: Path, payload: bytes, *, max_bytes: int) -> None:
    if len(payload) > max_bytes:
        raise ObserverError(f"{path.name} exceeds {max_bytes} byte publish cap")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            _bounded_fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
        _fsync_directory(path.parent)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _atomic_json(path: Path, value: dict[str, Any], *, max_bytes: int) -> None:
    _atomic_publish(
        path,
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"),
        max_bytes=max_bytes,
    )


def _durable_append(
    path: Path,
    value: dict[str, Any],
    *,
    max_bytes: int,
) -> None:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    payload_bytes = payload.encode("utf-8")
    existing_size = path.stat().st_size if path.exists() else 0
    if existing_size > max_bytes or len(payload_bytes) > max_bytes - existing_size:
        raise ObserverError(f"{path.name} exceeds {max_bytes} byte append cap")
    existed = path.exists()
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8", closefd=True) as stream:
        stream.write(payload)
        stream.flush()
        _bounded_fsync(stream.fileno())
    if not existed:
        _fsync_directory(path.parent)


def _ensure_new_directory(path: Path) -> None:
    path.mkdir(mode=0o700)
    _fsync_directory(path.parent)


def _normalize_request_id(value: str) -> str:
    if not _REQUEST_ID_RE.fullmatch(value):
        raise ObserverError(f"request id is outside the closed NQSV grammar: {value!r}")
    return value.split(":", 1)[-1]


def _controller_run_nonce() -> str:
    nonce = os.environ.get("T362_RUN_NONCE", "")
    attempt_id = os.environ.get("T362_ATTEMPT_ID", "")
    if not _RUN_NONCE_RE.fullmatch(nonce):
        raise ObserverError("T362_RUN_NONCE is outside the closed attempt-id grammar")
    if attempt_id != nonce:
        raise ObserverError("T362_ATTEMPT_ID and T362_RUN_NONCE must be identical")
    return nonce


def _scheduler_state(stdout: str) -> str | None:
    """Exact full/abbreviated parser contract from dispatch_compute._scheduler_state."""

    match = _STATE_RE.search(stdout)
    if match is not None:
        abbreviated = match.group(1).upper()
        if abbreviated == "STG":
            return "QUE"
        if abbreviated == "EXT":
            return "END"
        return abbreviated
    match = _CURRENT_STATE_RE.search(stdout)
    if match is None:
        return None
    value = match.group(1).strip().lower()
    if value in {"running", "pre-running", "run"}:
        return "RUN"
    if value in {"queued", "queue", "waiting", "wait", "staging", "stg"}:
        return "QUE"
    if value in {"held", "hold", "holding"}:
        return "HLD"
    if value in {
        "completed", "complete", "finished", "ended", "exited", "exit",
        "terminated", "exiting", "post-running", "ext",
    }:
        return "END"
    return None


def _qstat_mentions_request(stdout: str, normalized_request_id: str) -> bool:
    token = re.compile(
        rf"(?<![A-Za-z0-9._-])(?:[0-9]+:)?{re.escape(normalized_request_id)}"
        r"(?![A-Za-z0-9._-])"
    )
    return token.search(stdout) is not None


def _required_environment() -> tuple[Path, Path, str]:
    missing = [
        name
        for name in (
            "T362_RUN_ROOT",
            "T362_DRIVER_ROOT",
            "T362_MODE",
            "T362_RUN_NONCE",
            "T362_ATTEMPT_ID",
        )
        if not os.environ.get(name)
    ]
    if missing:
        raise ObserverError("required environment is unset: " + ",".join(missing))
    run_root = Path(os.environ["T362_RUN_ROOT"])
    driver_root = Path(os.environ["T362_DRIVER_ROOT"])
    mode = os.environ["T362_MODE"]
    if mode not in MODES:
        raise ObserverError(f"invalid T362_MODE: {mode!r}")
    _controller_run_nonce()
    for label, path in (("T362_RUN_ROOT", run_root), ("T362_DRIVER_ROOT", driver_root)):
        if not path.is_absolute() or path.is_symlink() or not path.is_dir():
            raise ObserverError(f"{label} must be an existing absolute non-symlink directory")
    if driver_root.resolve() != Path(__file__).resolve().parent:
        raise ObserverError("T362_DRIVER_ROOT does not identify this observer's driver directory")
    return run_root, driver_root, mode


def _classification(returncode: int, stdout: str, stderr: str) -> str:
    combined = f"{stdout}\n{stderr}".lower()
    if any(marker in combined for marker in _QSTAT_ERROR_MARKERS["permission"]):
        return "PERMISSION"
    if any(marker in combined for marker in _QSTAT_ERROR_MARKERS["transient"]):
        return "TRANSIENT"
    if returncode == 0:
        return "OK"
    return "OTHER_ERROR"


def _bounded_read_bytes(path: Path, *, max_bytes: int, purpose: str) -> bytes:
    if path.is_symlink():
        raise ObserverError(f"{purpose} is a symlink")
    try:
        with path.open("rb") as stream:
            payload = stream.read(max_bytes + 1)
    except OSError as exc:
        raise ObserverError(f"{purpose}: {type(exc).__name__}: {exc}") from exc
    if len(payload) > max_bytes:
        raise ObserverError(f"{purpose} exceeds {max_bytes} byte cap")
    return payload


def _read_json(
    path: Path, *, max_bytes: int
) -> tuple[dict[str, Any] | None, str | None, bytes | None]:
    try:
        raw = _bounded_read_bytes(
            path, max_bytes=max_bytes, purpose=path.name
        )
        value = json.loads(raw)
    except (ObserverError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}", None
    if not isinstance(value, dict):
        return None, "JSON root is not an object", raw
    return value, None, raw


class Observer:
    def __init__(self, run_root: Path, mode: str, request_id: str, requested_seconds: int):
        self.run_root = run_root
        self.mode = mode
        self.request_id = request_id
        self.normalized_request_id = _normalize_request_id(request_id)
        self.expected_run_nonce = _controller_run_nonce()
        self.requested_seconds = requested_seconds
        self.session_id = uuid.uuid4().hex
        observer_root = run_root / "observer"
        try:
            observer_root.mkdir(mode=0o700)
            _fsync_directory(run_root)
        except FileExistsError:
            if observer_root.is_symlink() or not observer_root.is_dir():
                raise ObserverError("observer root is not a safe directory")
        self.session_root = observer_root / f"session-{self.session_id}"
        _ensure_new_directory(self.session_root)
        self.raw_root = self.session_root / "raw"
        _ensure_new_directory(self.raw_root)
        self.events = self.session_root / "events.jsonl"
        self.final_path = observer_root / "final_observation.json"
        self.cleanup_receipt_path = observer_root / "cleanup_receipt.json"
        self.command_sequence = 0
        self.qstat_invocations = 0
        self.canary_read_attempts = 0
        self.canary_read_cap_reported = False
        self.run_marker: dict[str, Any] | None = None
        self.run_marker_hash: str | None = None
        self.ready_marker: dict[str, Any] | None = None
        self.ready_marker_hash: str | None = None
        self.marker_errors: list[str] = []
        self.run_marker_attempted = False
        self.ready_marker_attempted = False
        self.last_state: str | None = None
        self.request_ever_visible = False
        self.scheduler_run_seen = False
        self.local_io_cap_errors: list[str] = []
        self.observer_inventory_records = 0
        self.observer_event_records = 0
        for path, purpose in (
            (self.events, "observer events"),
            (self.final_path, "final raw-observation validity record"),
            (self.cleanup_receipt_path, "artifact cleanup receipt"),
        ):
            self.register(path, purpose=purpose, cleanup=False)

    def register(self, path: Path, *, purpose: str, cleanup: bool) -> None:
        try:
            relative = path.relative_to(self.run_root).as_posix()
        except ValueError as exc:
            raise ObserverError(f"observer artifact outside run root: {path}") from exc
        if self.observer_inventory_records >= MAX_INVENTORY_RECORDS_PER_FILE:
            self.local_io_cap_errors.append(
                "observer artifact inventory record cap exceeded"
            )
            return
        try:
            _durable_append(
                self.run_root / "observer-artifact-inventory.jsonl",
                {
                "schema_version": INVENTORY_SCHEMA,
                "relative_path": relative,
                "purpose": purpose,
                "cleanup": cleanup,
                "producer": "observer",
                "session_id": self.session_id,
                "pid": os.getpid(),
                "time_ns": time.time_ns(),
                },
                max_bytes=MAX_INVENTORY_BYTES_PER_FILE,
            )
            self.observer_inventory_records += 1
        except ObserverError as exc:
            self.local_io_cap_errors.append(str(exc))

    def record(self, event: str, **fields: Any) -> None:
        value: dict[str, Any] = {
            "schema_version": SCHEMA,
            "event": event,
            "mode": self.mode,
            "request_id": self.request_id,
            "normalized_request_id": self.normalized_request_id,
            "session_id": self.session_id,
            "observer_pid": os.getpid(),
            "monotonic_ns": time.monotonic_ns(),
            "time_ns": time.time_ns(),
        }
        value.update(fields)
        if self.observer_event_records >= MAX_OBSERVER_EVENT_RECORDS:
            self.local_io_cap_errors.append("observer event record cap exceeded")
            return
        try:
            _durable_append(
                self.events,
                value,
                max_bytes=MAX_OBSERVER_EVENT_BYTES,
            )
            self.observer_event_records += 1
        except ObserverError as exc:
            self.local_io_cap_errors.append(str(exc))

    def command(self, argv: list[str], purpose: str) -> dict[str, Any]:
        self.command_sequence += 1
        sequence = self.command_sequence
        started = time.monotonic_ns()
        if sequence > MAX_SCHEDULER_COMMANDS:
            returncode, stdout_bytes, stderr_bytes = 125, b"", b""
            timed_out, launch_error = False, "CommandCountCapExceeded"
        else:
            with tempfile.TemporaryFile() as stdout_capture, tempfile.TemporaryFile() as stderr_capture:
                def limit_child_output_files() -> None:
                    limit = MAX_COMMAND_RAW_BYTES_PER_STREAM + 1
                    resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))

                try:
                    result = subprocess.run(
                        argv,
                        stdin=subprocess.DEVNULL,
                        stdout=stdout_capture,
                        stderr=stderr_capture,
                        timeout=COMMAND_TIMEOUT_SECONDS,
                        check=False,
                        preexec_fn=limit_child_output_files,
                    )
                    returncode = result.returncode
                    timed_out, launch_error = False, None
                except subprocess.TimeoutExpired:
                    returncode = 124
                    timed_out, launch_error = True, "TimeoutExpired"
                except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
                    returncode = 127
                    timed_out, launch_error = False, type(exc).__name__
                    stderr_capture.write(str(exc).encode("utf-8", errors="replace"))
                stdout_capture.seek(0)
                stderr_capture.seek(0)
                stdout_bytes = stdout_capture.read(
                    MAX_COMMAND_RAW_BYTES_PER_STREAM + 1
                )
                stderr_bytes = stderr_capture.read(
                    MAX_COMMAND_RAW_BYTES_PER_STREAM + 1
                )
        output_cap_exceeded = (
            len(stdout_bytes) > MAX_COMMAND_RAW_BYTES_PER_STREAM
            or len(stderr_bytes) > MAX_COMMAND_RAW_BYTES_PER_STREAM
        )
        original_stdout_bytes = len(stdout_bytes)
        original_stderr_bytes = len(stderr_bytes)
        stdout_bytes = stdout_bytes[:MAX_COMMAND_RAW_BYTES_PER_STREAM]
        stderr_bytes = stderr_bytes[:MAX_COMMAND_RAW_BYTES_PER_STREAM]
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        try:
            classification = _classification(returncode, stdout, stderr)
        except (UnicodeError, ValueError):
            classification = "OUTPUT_CAP_EXCEEDED"
        if launch_error is not None and not timed_out:
            classification = "MISSING_COMMAND" if launch_error == "FileNotFoundError" else "OS_ERROR"
        if output_cap_exceeded or launch_error == "CommandCountCapExceeded":
            classification = "OUTPUT_CAP_EXCEEDED"
            self.local_io_cap_errors.append(
                f"{purpose}: scheduler raw output/count cap exceeded"
            )
        stem = f"{sequence:04d}-{purpose}"
        stdout_path = self.raw_root / f"{stem}.stdout.raw"
        stderr_path = self.raw_root / f"{stem}.stderr.raw"
        self.register(stdout_path, purpose=f"{purpose} stdout", cleanup=False)
        self.register(stderr_path, purpose=f"{purpose} stderr", cleanup=False)
        _atomic_publish(
            stdout_path,
            stdout_bytes,
            max_bytes=MAX_COMMAND_RAW_BYTES_PER_STREAM,
        )
        _atomic_publish(
            stderr_path,
            stderr_bytes,
            max_bytes=MAX_COMMAND_RAW_BYTES_PER_STREAM,
        )
        value = {
            "argv": argv,
            "purpose": purpose,
            "sequence": sequence,
            "returncode": returncode,
            "classification": classification,
            "timed_out": timed_out,
            "launch_error": launch_error,
            "output_cap_exceeded": output_cap_exceeded,
            "stdout_bytes_before_cap": original_stdout_bytes,
            "stderr_bytes_before_cap": original_stderr_bytes,
            "duration_ns": time.monotonic_ns() - started,
            "stdout_file": str(stdout_path.relative_to(self.session_root)),
            "stderr_file": str(stderr_path.relative_to(self.session_root)),
        }
        self.record("scheduler_command", **value)
        return value | {"stdout": stdout, "stderr": stderr}

    def bounded_command(
        self, argv: list[str], purpose: str, *, attempts: int, retry_seconds: float
    ) -> dict[str, Any]:
        latest: dict[str, Any] | None = None
        for attempt in range(1, attempts + 1):
            latest = self.command(argv, f"{purpose}-attempt-{attempt}")
            if latest["classification"] in ("OK", "PERMISSION", "MISSING_COMMAND"):
                break
            if attempt < attempts:
                time.sleep(retry_seconds)
        assert latest is not None
        return latest

    def qstat(self, purpose: str, attempts: int = QSTAT_ATTEMPTS) -> dict[str, Any]:
        self.qstat_invocations += 1
        if self.qstat_invocations > MAX_OBSERVER_QSTAT_INVOCATIONS:
            message = (
                f"qstat invocation count exceeds "
                f"{MAX_OBSERVER_QSTAT_INVOCATIONS} cap"
            )
            self.local_io_cap_errors.append(message)
            result = {
                "argv": ["qstat", "-J", "-f", self.request_id],
                "purpose": purpose,
                "returncode": 125,
                "classification": "OUTPUT_CAP_EXCEEDED",
                "timed_out": False,
                "launch_error": "CommandCountCapExceeded",
                "output_cap_exceeded": True,
                "stdout": "",
                "stderr": "",
            }
        else:
            result = self.bounded_command(
                ["qstat", "-J", "-f", self.request_id],
                purpose,
                attempts=attempts,
                retry_seconds=QSTAT_RETRY_SECONDS,
            )
        state = _scheduler_state(result["stdout"])
        visible = _qstat_mentions_request(result["stdout"], self.normalized_request_id)
        if visible:
            self.request_ever_visible = True
        if state is not None:
            self.last_state = state
        result.update(state=state, visible=visible)
        self.record(
            "qstat_observation",
            purpose=purpose,
            state=state,
            visible=visible,
            returncode=result["returncode"],
            classification=result["classification"],
        )
        return result

    def _validate_identity_marker(self, name: str, *, ready: bool) -> tuple[dict[str, Any], str]:
        path = self.run_root / name
        value, error, raw = _read_json(
            path, max_bytes=MAX_MARKER_BYTES_PER_FILE
        )
        if error is not None or value is None or raw is None:
            raise ObserverError(f"{name}: {error or 'missing object'}")
        required: dict[str, Any] = {
            "schema_version": MARKER_SCHEMA,
            "mode": self.mode,
            "normalized_request_id": self.normalized_request_id,
        }
        for key, expected in required.items():
            if value.get(key) != expected:
                raise ObserverError(f"{name}: {key} mismatch")
        nonce = value.get("run_nonce")
        if nonce != self.expected_run_nonce:
            raise ObserverError(f"{name}: run_nonce does not bind controller environment")
        if not ready:
            raw_pbs_jobid = value.get("pbs_jobid")
            if not isinstance(raw_pbs_jobid, str):
                raise ObserverError(f"{name}: pbs_jobid missing")
            try:
                marker_request_id = _normalize_request_id(raw_pbs_jobid)
            except ObserverError as exc:
                raise ObserverError(f"{name}: invalid pbs_jobid") from exc
            if marker_request_id != self.normalized_request_id:
                raise ObserverError(f"{name}: pbs_jobid does not bind CLI request id")
            if not isinstance(value.get("hostname"), str) or not isinstance(value.get("pid"), int):
                raise ObserverError(f"{name}: hostname or pid missing")
        if ready:
            if self.run_marker is None or self.run_marker_hash is None:
                raise ObserverError("ready marker appeared before validated run marker")
            expected_ready = {
                "run_nonce": self.run_marker["run_nonce"],
                "compute_marker_sha256": self.run_marker_hash,
                "canary_sha256": hashlib.sha256(MUTATED).hexdigest(),
                "state": "READY_AFTER_LOGIN_READBACK_ACK",
            }
            for key, expected in expected_ready.items():
                if value.get(key) != expected:
                    raise ObserverError(f"{name}: {key} binding mismatch")
        return value, hashlib.sha256(raw).hexdigest()

    def inspect_markers(self) -> None:
        if not self.run_marker_attempted and (self.run_root / "run_marker.json").is_file():
            self.run_marker_attempted = True
            try:
                self.run_marker, self.run_marker_hash = self._validate_identity_marker(
                    "run_marker.json", ready=False
                )
                self.record(
                    "run_marker_validated",
                    run_nonce=self.run_marker["run_nonce"],
                    compute_marker_sha256=self.run_marker_hash,
                )
            except ObserverError as exc:
                self.marker_errors.append(str(exc))
                self.record("run_marker_invalid", detail=str(exc))
        if not self.ready_marker_attempted and (self.run_root / "ready.json").is_file():
            self.ready_marker_attempted = True
            try:
                self.ready_marker, self.ready_marker_hash = self._validate_identity_marker(
                    "ready.json", ready=True
                )
                self.record("ready_marker_validated", ready_marker_sha256=self.ready_marker_hash)
            except ObserverError as exc:
                self.marker_errors.append(str(exc))
                self.record("ready_marker_invalid", detail=str(exc))

    def acknowledge_canary(self) -> None:
        acknowledgment = self.run_root / "canary_readback_ack.json"
        if acknowledgment.exists() or self.run_marker is None or self.run_marker_hash is None:
            return
        if self.canary_read_attempts >= MAX_CANARY_READ_ATTEMPTS:
            if not self.canary_read_cap_reported:
                self.local_io_cap_errors.append(
                    f"canary read attempt count exceeds {MAX_CANARY_READ_ATTEMPTS} cap"
                )
                self.canary_read_cap_reported = True
            return
        self.canary_read_attempts += 1
        try:
            payload = _bounded_read_bytes(
                self.run_root / "canary.txt",
                max_bytes=MAX_CANARY_BYTES,
                purpose="canary readback",
            )
        except ObserverError as exc:
            if "FileNotFoundError" in str(exc):
                return
            self.local_io_cap_errors.append(str(exc))
            self.record("canary_readback_error", error_type=type(exc).__name__, detail=str(exc))
            return
        if payload != MUTATED:
            return
        digest = hashlib.sha256(payload).hexdigest()
        _atomic_json(
            acknowledgment,
            {
                "schema_version": SCHEMA,
                "mode": self.mode,
                "request_id": self.request_id,
                "normalized_request_id": self.normalized_request_id,
                "run_nonce": self.run_marker["run_nonce"],
                "compute_marker_sha256": self.run_marker_hash,
                "observer_session_id": self.session_id,
                "canary_bytes_hex": payload.hex(),
                "canary_sha256": digest,
                "monotonic_ns": time.monotonic_ns(),
                "time_ns": time.time_ns(),
            },
            max_bytes=MAX_CANARY_ACK_BYTES,
        )
        self.record("canary_mutated_readback_ack_persisted", canary_sha256=digest)

    def collect_scheduler_tail(self) -> dict[str, dict[str, Any]]:
        return {
            "qstat": self.qstat("final-qstat", attempts=QSTAT_ATTEMPTS),
            "racctjob": self.bounded_command(
                ["racctjob", "-I", self.request_id],
                "final-racctjob",
                attempts=ACCOUNTING_ATTEMPTS,
                retry_seconds=ACCOUNTING_RETRY_SECONDS,
            ),
            "racctreq": self.bounded_command(
                ["racctreq", "-I", self.request_id],
                "final-racctreq",
                attempts=ACCOUNTING_ATTEMPTS,
                retry_seconds=ACCOUNTING_RETRY_SECONDS,
            ),
        }

    def _read_jsonl_detailed(
        self, relative: str
    ) -> tuple[list[dict[str, Any]], list[str], list[str]]:
        path = self.run_root / relative
        errors: list[str] = []
        parse_errors: list[str] = []
        records: list[dict[str, Any]] = []
        try:
            raw = _bounded_read_bytes(
                path,
                max_bytes=MAX_SIGNAL_LOG_BYTES_PER_FILE,
                purpose=relative,
            )
            lines = raw.decode("utf-8").splitlines()
        except UnicodeError as exc:
            message = f"{relative}: {type(exc).__name__}: {exc}"
            return [], [], [message]
        except ObserverError as exc:
            return [], [str(exc)], []
        if len(lines) > MAX_SIGNAL_LOG_RECORDS_PER_FILE:
            return [], [
                f"{relative}: exceeds {MAX_SIGNAL_LOG_RECORDS_PER_FILE} record cap"
            ], []
        if not lines:
            errors.append(f"{relative}: empty")
        for index, line in enumerate(lines, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                message = f"{relative}:{index}: JSONDecodeError: {exc}"
                parse_errors.append(message)
                continue
            if not isinstance(value, dict):
                message = f"{relative}:{index}: not an object"
                parse_errors.append(message)
                continue
            if value.get("schema_version") != EVENT_SCHEMA or value.get("mode") != self.mode:
                errors.append(f"{relative}:{index}: schema or mode mismatch")
            if self.run_marker is not None:
                for key, expected in (
                    ("run_nonce", self.run_marker["run_nonce"]),
                    ("normalized_request_id", self.normalized_request_id),
                    ("compute_marker_sha256", self.run_marker_hash),
                ):
                    if value.get(key) != expected:
                        errors.append(f"{relative}:{index}: {key} mismatch")
            records.append(value)
        return records, errors, parse_errors

    def _read_jsonl(self, relative: str) -> tuple[list[dict[str, Any]], list[str]]:
        records, errors, parse_errors = self._read_jsonl_detailed(relative)
        return records, errors + parse_errors

    @staticmethod
    def _event_names(records: list[dict[str, Any]]) -> list[str]:
        return [value.get("event") for value in records if isinstance(value.get("event"), str)]

    def validate_layers(self) -> dict[str, Any]:
        """Return independent non-parse validity and parse-freedom predicates.

        Parse/root-shape failures are retained in ``errors`` for diagnostics but
        are excluded from ``valid``.  The production final conjunction includes
        both predicates, so the overall accepted observation set is unchanged.
        """

        launch_layer = "bash" if self.mode == "split-warning" else "job-script"
        layers = [launch_layer, "parent", "grandchild"]
        errors: list[str] = []
        all_parse_errors: list[str] = []
        structure_errors: list[str] = []
        signals: dict[str, list[str] | str] = {}
        event_records: dict[str, list[dict[str, Any]]] = {}
        for layer in layers:
            records, event_errors, event_parse_errors = self._read_jsonl_detailed(
                f"events-{layer}.jsonl"
            )
            event_records[layer] = records
            errors.extend(event_errors)
            parse_errors_for_layer = list(event_parse_errors)
            event_names = self._event_names(records)
            required_start = {
                launch_layer: "run_marker_persisted",
                "parent": "parent_started",
                "grandchild": "grandchild_started",
            }[layer]
            if required_start not in event_names:
                message = f"events-{layer}.jsonl: required start event {required_start} missing"
                errors.append(message)
                structure_errors.append(message)
            names = [
                value["signal_name"]
                for value in records
                if value.get("event") == "signal" and isinstance(value.get("signal_name"), str)
            ]
            signals[layer] = list(dict.fromkeys(names)) if names else "UNKNOWN"
            control, control_errors, control_parse_errors = self._read_jsonl_detailed(
                f"control-{layer}.jsonl"
            )
            errors.extend(control_errors)
            parse_errors_for_layer.extend(control_parse_errors)
            control_names = self._event_names(control)
            if "control_start" not in control_names or "control_normal_exit" not in control_names:
                message = f"control-{layer}.jsonl: incomplete D4 control"
                errors.append(message)
                structure_errors.append(message)
            heartbeat, heartbeat_errors, heartbeat_parse_errors = (
                self._read_jsonl_detailed(f"heartbeats-{layer}.jsonl")
            )
            errors.extend(heartbeat_errors)
            parse_errors_for_layer.extend(heartbeat_parse_errors)
            if "heartbeat" not in self._event_names(heartbeat):
                message = f"heartbeats-{layer}.jsonl: durable heartbeat missing"
                errors.append(message)
                structure_errors.append(message)
            all_parse_errors.extend(parse_errors_for_layer)
        if self.mode == "split-warning":
            try:
                writer_path = self.run_root / "signal-writer-failures.raw"
                writer_failures = _bounded_read_bytes(
                    writer_path,
                    max_bytes=MAX_WRITER_FAILURE_BYTES,
                    purpose="signal-writer-failures.raw",
                )
            except ObserverError as exc:
                message = str(exc)
                errors.append(message)
            else:
                if writer_failures:
                    message = "signal-writer-failures.raw is non-empty"
                    errors.append(message)
                    structure_errors.append(message)
        return {
            # Parse freedom is intentionally derived only from decoding/root-shape
            # errors. Missing logs, schema/identity mismatches, and required-event
            # failures remain independent structural validity inputs.
            "valid": not errors,
            "errors": errors + all_parse_errors,
            "parse_errors": all_parse_errors,
            "structure_errors": structure_errors,
            "parse_error_free": not all_parse_errors,
            "signals": signals,
            "parent_events": event_records.get("parent", []),
            "required_layers": layers,
        }

    def validate_cleanup_order(self, parent_events: list[dict[str, Any]]) -> dict[str, Any]:
        control_errors: list[str] = []
        restore_errors: list[str] = []
        if any(value.get("event") == "grandchild_already_stopped" for value in parent_events):
            control_errors.append("grandchild_already_stopped shortcut observed")

        def find_after(event: str, start: int, *, signal_name: str | None = None) -> int:
            for index in range(start, len(parent_events)):
                value = parent_events[index]
                if value.get("event") == event and (
                    signal_name is None or value.get("signal_name") == signal_name
                ):
                    return index
            return -1

        control_prefix = [
            ("grandchild_alive_immediately_before_ready", None),
            ("ready_after_login_readback_ack", None),
        ]
        restore_suffix = [
            ("cleanup_signal_sent", "SIGTERM"),
            ("cleanup_term_wait_timeout", None),
            ("cleanup_signal_sent", "SIGKILL"),
            ("cleanup_kill_wait_finished", None),
            ("canary_restore_verified", None),
            ("finally_exit", None),
        ]
        cursor = 0
        matched: list[dict[str, Any]] = []
        for event, signal_name in control_prefix:
            index = find_after(event, cursor, signal_name=signal_name)
            if index < 0:
                control_errors.append(
                    f"cleanup control prefix missing {event}/{signal_name or '-'}"
                )
                continue
            matched.append(parent_events[index])
            cursor = index + 1
        control_cursor = cursor
        for event, signal_name in restore_suffix:
            index = find_after(event, cursor, signal_name=signal_name)
            if index < 0:
                restore_errors.append(
                    f"cleanup restore suffix missing {event}/{signal_name or '-'}"
                )
                continue
            matched.append(parent_events[index])
            cursor = index + 1
        timeout = next(
            (value for value in matched if value.get("event") == "cleanup_term_wait_timeout"),
            None,
        )
        if timeout is None or not isinstance(timeout.get("waited_ns"), int) or timeout["waited_ns"] < MIN_TERM_WAIT_NS:
            restore_errors.append(
                "TERM TimeoutExpired wait was shorter than approximately five seconds"
            )
        restored = next(
            (value for value in matched if value.get("event") == "canary_restore_verified"),
            None,
        )
        final = next((value for value in matched if value.get("event") == "finally_exit"), None)
        if restored is None or restored.get("byte_match") is not True:
            restore_errors.append("canary restore byte verification absent or false")
        if final is None or final.get("canary_byte_match") is not True:
            restore_errors.append("finally_exit byte verification absent or false")
        errors = control_errors + restore_errors
        return {
            "valid": not errors,
            "errors": errors,
            "control_prefix_valid": not control_errors,
            "control_prefix_errors": control_errors,
            "restore_outcome_valid": not restore_errors and control_cursor > 0,
            "restore_outcome_errors": restore_errors,
            "matched_events": matched,
        }

    @staticmethod
    def classify_probe_cleanup(
        cleanup_order: dict[str, Any], post_restore_canary: dict[str, Any]
    ) -> tuple[str, str | None]:
        if not cleanup_order["control_prefix_valid"]:
            return "unknown", None
        if post_restore_canary["outcome"] == "unknown":
            return "unknown", None
        if post_restore_canary["outcome"] == "unsafe":
            return "unsafe", "post_restore_canary_mismatch"
        if not cleanup_order["restore_outcome_valid"]:
            return "unsafe", "cleanup_order_invalid"
        if post_restore_canary["outcome"] == "safe":
            return "safe", None
        return "unknown", None

    def readback_restored_canary(self) -> dict[str, Any]:
        """Independently bind the post-restore bytes before inventory cleanup."""

        path = self.run_root / "canary.txt"
        try:
            payload = _bounded_read_bytes(
                path,
                max_bytes=MAX_CANARY_BYTES,
                purpose="post-restore canary",
            )
        except ObserverError as exc:
            return {
                "outcome": "unknown",
                "error": f"{type(exc).__name__}: {exc}",
                "request_id": self.request_id,
                "normalized_request_id": self.normalized_request_id,
                "run_nonce": self.expected_run_nonce,
                "observed_bytes_hex": None,
                "observed_sha256": None,
                "expected_bytes_hex": ORIGINAL.hex(),
                "expected_sha256": hashlib.sha256(ORIGINAL).hexdigest(),
            }
        matches = payload == ORIGINAL
        return {
            "outcome": "safe" if matches else "unsafe",
            "error": None,
            "request_id": self.request_id,
            "normalized_request_id": self.normalized_request_id,
            "run_nonce": self.expected_run_nonce,
            "observed_bytes_hex": payload.hex(),
            "observed_sha256": hashlib.sha256(payload).hexdigest(),
            "expected_bytes_hex": ORIGINAL.hex(),
            "expected_sha256": hashlib.sha256(ORIGINAL).hexdigest(),
        }

    def validate_accounting(self, tail: dict[str, dict[str, Any]]) -> dict[str, Any]:
        errors: list[str] = []
        integrity_errors: list[str] = []
        provenance_bound_texts: list[str] = []
        for name in ("racctjob", "racctreq"):
            result = tail[name]
            if result["classification"] != "OK":
                errors.append(f"{name} did not complete successfully: {result['classification']}")
            expected_records = 1
            observed_by_stream: dict[str, list[str]] = {
                "stdout": [],
                "stderr": [],
            }
            invalid_by_stream: dict[str, list[str]] = {
                "stdout": [],
                "stderr": [],
            }
            for stream_name in ("stdout", "stderr"):
                for raw_id in _REQUEST_ID_FIELD_RE.findall(result[stream_name]):
                    try:
                        observed_by_stream[stream_name].append(
                            _normalize_request_id(raw_id.rstrip("."))
                        )
                    except ObserverError:
                        invalid_by_stream[stream_name].append(raw_id)
            observed_ids = observed_by_stream["stdout"]
            invalid_ids = [
                raw for values in invalid_by_stream.values() for raw in values
            ]
            all_observed_ids = [
                value for values in observed_by_stream.values() for value in values
            ]
            if invalid_ids:
                integrity_errors.append(f"{name} contains malformed request ids")
            if len(observed_ids) != expected_records:
                integrity_errors.append(
                    f"{name} expected {expected_records} request records, observed {len(observed_ids)}"
                )
            if any(
                value != self.normalized_request_id for value in all_observed_ids
            ):
                integrity_errors.append(f"{name} contains a foreign request id")
            if observed_ids.count(self.normalized_request_id) != expected_records:
                integrity_errors.append(
                    f"{name} does not contain the exact expected request record count"
                )
            for stream_name in ("stdout", "stderr"):
                current_request: str | None = None
                bound_lines: list[str] = []
                causes_bound = True
                for line in result[stream_name].splitlines():
                    id_match = _REQUEST_ID_FIELD_RE.search(line)
                    if id_match is not None:
                        try:
                            current_request = _normalize_request_id(
                                id_match.group(1).rstrip(".")
                            )
                        except ObserverError:
                            current_request = None
                    if current_request == self.normalized_request_id:
                        bound_lines.append(line)
                    if (
                        _WALLTIME_LIMIT_CAUSE_RE.search(line)
                        or _NORMAL_COMPLETION_RE.search(line)
                    ) and current_request != self.normalized_request_id:
                        causes_bound = False
                if not causes_bound:
                    integrity_errors.append(
                        f"{name} {stream_name} termination cause is not bound to "
                        "an exact request record"
                    )
                provenance_bound_texts.extend(bound_lines)
        errors.extend(integrity_errors)
        combined = "\n".join(provenance_bound_texts)
        cause_lines = _WALLTIME_LIMIT_CAUSE_RE.findall(combined)
        explicit_cause = bool(cause_lines)
        normal_completion_indicators = _NORMAL_COMPLETION_RE.findall(combined)
        generic_exit_statuses = [
            int(match.group(1)) for match in _GENERIC_EXIT_STATUS_RE.finditer(combined)
        ]
        termination_cause = (
            "WALLTIME_RESOURCE_LIMIT"
            if explicit_cause
            else (
                "NORMAL_COMPLETION"
                if normal_completion_indicators
                else "UNKNOWN_NOT_RESOURCE_LIMIT"
            )
        )
        durations: list[int] = []
        for match in _DURATION_RE.finditer(combined):
            if match.group(1) is not None:
                durations.append(
                    int(match.group(1)) * 3600 + int(match.group(2)) * 60 + int(match.group(3))
                )
            elif match.group(4) is not None:
                durations.append(int(match.group(4)))
        termination_threshold = self.requested_seconds
        elapsed_reached_limit = bool(durations) and max(durations) >= termination_threshold
        if not explicit_cause:
            errors.append("accounting has no explicit walltime/resource-limit termination cause")
        if not elapsed_reached_limit:
            errors.append("accounting elapsed time does not reach the registered limit event")
        available = all(
            tail[name]["classification"] == "OK"
            and bool(tail[name]["stdout"].strip())
            for name in ("racctjob", "racctreq")
        )
        return {
            "valid": not errors,
            "available": available,
            "integrity_valid": available and not integrity_errors,
            "errors": errors,
            "integrity_errors": integrity_errors,
            "explicit_walltime_cause": explicit_cause,
            "termination_cause_classification": termination_cause,
            "normal_completion_indicator_present": bool(normal_completion_indicators),
            "generic_exit_statuses_ignored_as_walltime_cause": generic_exit_statuses,
            "elapsed_seconds_candidates": durations,
            "requested_seconds": self.requested_seconds,
            "registered_limit_event_seconds": termination_threshold,
        }

    def cleanup_inventory(self) -> dict[str, Any]:
        inventory_paths = [
            self.run_root / "artifact-inventory.jsonl",
            self.run_root / "observer-artifact-inventory.jsonl",
        ]
        records: list[dict[str, Any]] = []
        errors: list[str] = []
        inventory_hashes: dict[str, str] = {}
        for inventory in inventory_paths:
            try:
                raw_inventory = _bounded_read_bytes(
                    inventory,
                    max_bytes=MAX_INVENTORY_BYTES_PER_FILE,
                    purpose=inventory.name,
                )
                lines = raw_inventory.decode("utf-8").splitlines()
            except (ObserverError, UnicodeDecodeError) as exc:
                errors.append(f"{inventory.name} unreadable: {exc}")
                continue
            if len(lines) > MAX_INVENTORY_RECORDS_PER_FILE:
                errors.append(
                    f"{inventory.name} exceeds {MAX_INVENTORY_RECORDS_PER_FILE} record cap"
                )
                continue
            inventory_hashes[inventory.name] = hashlib.sha256(raw_inventory).hexdigest()
            for index, line in enumerate(lines, 1):
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{inventory.name}:{index}: JSONDecodeError: {exc}")
                    continue
                if not isinstance(value, dict) or value.get("schema_version") != INVENTORY_SCHEMA:
                    errors.append(f"{inventory.name}:{index}: schema mismatch")
                    continue
                relative = value.get("relative_path")
                if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
                    errors.append(f"{inventory.name}:{index}: unsafe relative path")
                    continue
                if len(relative.encode("utf-8")) > MAX_INVENTORY_RELATIVE_PATH_BYTES:
                    errors.append(f"{inventory.name}:{index}: relative path exceeds byte cap")
                    continue
                records.append(value)
        deduplicated: dict[str, dict[str, Any]] = {}
        for value in records:
            previous = deduplicated.get(value["relative_path"])
            if previous is not None and previous.get("cleanup") != value.get("cleanup"):
                errors.append(f"inventory cleanup policy conflict: {value['relative_path']}")
            deduplicated[value["relative_path"]] = value
        pending = {
            str(self.final_path.relative_to(self.run_root)),
            str(self.cleanup_receipt_path.relative_to(self.run_root)),
        }
        missing_before = sorted(
            relative
            for relative in deduplicated
            if relative not in pending and not (self.run_root / relative).exists()
        )
        if missing_before:
            errors.append("registered artifacts missing before cleanup: " + ",".join(missing_before))
        owned_names = {
            "artifact-inventory.jsonl", "observer-artifact-inventory.jsonl",
            "run_marker.json", "run_metadata.json", "canary.txt",
            "ready.json", "grandchild_started.json", "canary_readback_ack.json",
            "signal-writer-failures.raw",
        }
        discovered: set[str] = set()
        pending_directories = [self.run_root]
        visited_directories = 0
        visited_entries = 0
        discovery_capped = False
        while pending_directories and not discovery_capped:
            directory = pending_directories.pop()
            visited_directories += 1
            if visited_directories > MAX_DISCOVERY_DIRECTORIES:
                errors.append(
                    f"artifact discovery exceeds {MAX_DISCOVERY_DIRECTORIES} directory cap"
                )
                break
            try:
                iterator = os.scandir(directory)
            except OSError as exc:
                errors.append(f"artifact discovery failed for {directory}: {exc}")
                continue
            with iterator:
                for entry in iterator:
                    visited_entries += 1
                    if visited_entries > MAX_DISCOVERY_ENTRIES:
                        errors.append(
                            f"artifact discovery exceeds {MAX_DISCOVERY_ENTRIES} entry cap"
                        )
                        discovery_capped = True
                        break
                    path = Path(entry.path)
                    if entry.is_dir(follow_symlinks=False):
                        pending_directories.append(path)
                        continue
                    if not entry.is_file(follow_symlinks=False) and not entry.is_symlink():
                        continue
                    relative = path.relative_to(self.run_root).as_posix()
                    first = Path(relative).parts[0]
                    if (
                        first in owned_names
                        or first.startswith(("events-", "control-", "heartbeats-"))
                        or first == "observer"
                        or first.startswith(".")
                    ):
                        discovered.add(relative)
        unregistered = sorted(
            discovered
            - set(deduplicated)
            - {"artifact-inventory.jsonl", "observer-artifact-inventory.jsonl"}
        )
        if unregistered:
            errors.append("unregistered T362 artifacts: " + ",".join(unregistered))
        evidence_errors = list(errors)
        cleanup_errors: list[str] = []
        removed: list[str] = []
        cleanup_targets = [
            (relative, value)
            for relative, value in sorted(deduplicated.items())
            if value.get("cleanup") is True
        ]
        if len(cleanup_targets) > MAX_CLEANUP_TARGETS:
            cleanup_errors.append(
                f"cleanup target count exceeds {MAX_CLEANUP_TARGETS} cap"
            )
            cleanup_targets = []
        for relative, value in cleanup_targets:
            path = self.run_root / relative
            try:
                path.unlink()
                removed.append(relative)
            except FileNotFoundError:
                cleanup_errors.append(f"cleanup target missing: {relative}")
            except OSError as exc:
                cleanup_errors.append(
                    f"cleanup failed {relative}: {type(exc).__name__}: {exc}"
                )
        try:
            _fsync_directory(self.run_root)
        except OSError as exc:
            cleanup_errors.append(f"run root fsync after cleanup failed: {exc}")
        remaining = sorted(relative for relative in removed if (self.run_root / relative).exists())
        if remaining:
            cleanup_errors.append("cleanup targets remain: " + ",".join(remaining))
        errors = evidence_errors + cleanup_errors
        receipt = {
            "schema_version": SCHEMA,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "inventory_sha256_before_cleanup": inventory_hashes,
            "inventory_record_count": len(records),
            "discovered_owned_files_before_cleanup": sorted(discovered),
            "removed": removed,
            "errors": errors,
            "evidence_errors": evidence_errors,
            "cleanup_errors": cleanup_errors,
            "time_ns": time.time_ns(),
        }
        _atomic_json(
            self.cleanup_receipt_path,
            receipt,
            max_bytes=MAX_CLEANUP_RECEIPT_BYTES,
        )
        return {
            "valid": not errors,
            "evidence_valid": not evidence_errors,
            "cleanup_valid": not cleanup_errors,
            **receipt,
        }

    def write_final(self, value: dict[str, Any]) -> None:
        _atomic_json(
            self.final_path,
            value,
            max_bytes=MAX_FINAL_OBSERVATION_BYTES,
        )

    def build_final_observation(
        self,
        *,
        tail: dict[str, dict[str, Any]],
        terminal_reason: str,
        permission_error: bool,
        active_at_stop: bool,
    ) -> tuple[dict[str, Any], bool]:
        """Classify raw logs and scheduler fixtures into the production final payload."""

        layer_validation = self.validate_layers()
        cleanup_order = self.validate_cleanup_order(layer_validation["parent_events"])
        python_parent_sigterm_caught = any(
            value.get("event") == "signal_abort_caught"
            and value.get("signal_name") == "SIGTERM"
            for value in layer_validation["parent_events"]
        )
        post_restore_canary = self.readback_restored_canary()
        accounting = self.validate_accounting(tail)
        tail_qstat = tail["qstat"]
        qstat_terminal_end = (
            tail_qstat["classification"] == "OK" and tail_qstat["state"] == "END"
        )
        qstat_visible_disappearance = (
            tail_qstat["classification"] == "OK"
            and self.request_ever_visible
            and tail_qstat["visible"] is False
        )
        terminal_non_run = (
            not active_at_stop and (qstat_terminal_end or qstat_visible_disappearance)
        )
        tail_classifications = {
            name: result["classification"] for name, result in tail.items()
        }
        identity_valid = (
            self.run_marker is not None
            and self.ready_marker is not None
            and not self.marker_errors
        )
        scheduler_commands_present = not any(
            value in {"MISSING_COMMAND", "OS_ERROR", "OUTPUT_CAP_EXCEEDED"}
            for value in tail_classifications.values()
        ) and not self.local_io_cap_errors
        pre_cleanup_conditions = {
            "ready_identity_valid": identity_valid,
            "walltime_accounting_confirmed": accounting["valid"],
            "scheduler_terminal_non_run": terminal_non_run,
            "scheduler_terminal_state_conclusive": tail_qstat["classification"] == "OK",
            "all_required_layers_and_logs_valid": layer_validation["valid"],
            "signal_log_parse_error_free": layer_validation["parse_error_free"],
            "cleanup_order_valid": cleanup_order["valid"],
            "cleanup_control_prefix_valid": cleanup_order["control_prefix_valid"],
            "cleanup_restore_outcome_valid": cleanup_order["restore_outcome_valid"],
            "post_restore_canary_safe": post_restore_canary["outcome"] == "safe",
            "python_parent_sigterm_caught": python_parent_sigterm_caught,
            "permission_error_absent": not permission_error,
            "scheduler_tail_permission_error_absent": (
                "PERMISSION" not in tail_classifications.values()
            ),
            "scheduler_commands_present": scheduler_commands_present,
            "controller_qdel_not_required": (
                terminal_reason != "QUE_DEADLINE_CONTROLLER_QDEL_REQUIRED"
            ),
        }
        cleanup_receipt = self.cleanup_inventory()
        acceptance_conditions = {
            **pre_cleanup_conditions,
            "artifact_inventory_cleanup_valid": cleanup_receipt["valid"],
            "artifact_inventory_evidence_valid": cleanup_receipt["evidence_valid"],
            "artifact_inventory_cleanup_outcome_valid": cleanup_receipt[
                "cleanup_valid"
            ],
        }
        probe_cleanup_outcome, unsafe_reason = self.classify_probe_cleanup(
            cleanup_order, post_restore_canary
        )
        observation_conditions = {
            "ready_identity_valid": identity_valid,
            "scheduler_terminal_state_conclusive": tail_qstat["classification"] == "OK",
            "all_required_layers_and_logs_valid": layer_validation["valid"],
            "signal_log_parse_error_free": layer_validation["parse_error_free"],
            "permission_error_absent": not permission_error,
            "scheduler_tail_permission_error_absent": (
                "PERMISSION" not in tail_classifications.values()
            ),
            "scheduler_commands_present": scheduler_commands_present,
            "cleanup_control_prefix_valid": cleanup_order["control_prefix_valid"],
            "artifact_inventory_evidence_valid": cleanup_receipt["evidence_valid"],
            "accounting_integrity_valid_or_unavailable": (
                not accounting["available"] or accounting["integrity_valid"]
            ),
        }
        valid = all(acceptance_conditions.values())
        final = {
            "schema_version": SCHEMA,
            "mode": self.mode,
            "request_id": self.request_id,
            "normalized_request_id": self.normalized_request_id,
            "session_id": self.session_id,
            "terminal_reason": terminal_reason,
            "last_qstat_state": self.last_state,
            "run_marker": self.run_marker,
            "run_marker_sha256": self.run_marker_hash,
            "ready_marker": self.ready_marker,
            "ready_marker_sha256": self.ready_marker_hash,
            "marker_errors": self.marker_errors,
            "acceptance_conditions": acceptance_conditions,
            "observation_conditions": observation_conditions,
            "valid_for_safety_conclusion": valid,
            "signal_observations": layer_validation["signals"],
            "signal_log_errors": layer_validation["errors"],
            "local_io_cap_errors": list(self.local_io_cap_errors),
            "cleanup_order": cleanup_order,
            "post_restore_canary_readback": post_restore_canary,
            "probe_cleanup_outcome": probe_cleanup_outcome,
            "unsafe_reason": unsafe_reason,
            "accounting_confirmation": accounting,
            "artifact_inventory_validation": {
                "evidence_valid": cleanup_receipt["evidence_valid"],
                "cleanup_outcome_valid": cleanup_receipt["cleanup_valid"],
            },
            "cleanup_receipt_file": str(
                self.cleanup_receipt_path.relative_to(self.run_root)
            ),
            "unobserved_signal_vocabulary": "UNKNOWN",
            "qwait_code_9_scope": (
                "resource-limit termination only; never evidence of the delivered signal kind"
            ),
            "diagnostic_scope": (
                "raw observations and validity only; no safety verdict is embedded"
            ),
            "time_ns": time.time_ns(),
        }
        return final, valid

    def run(self) -> int:
        observer_started = time.monotonic()
        queue_deadline = observer_started + QUE_DEADLINE_SECONDS
        execution_deadline: float | None = None
        next_qstat = observer_started
        terminal_reason = "UNKNOWN"
        permission_error = False
        active_at_stop = False
        self.record(
            "observer_started",
            que_deadline_seconds=QUE_DEADLINE_SECONDS,
            execution_deadline_rule=(
                f"first qstat RUN + requested {self.requested_seconds}s + {EXECUTION_GRACE_SECONDS}s"
            ),
        )
        initial = self.qstat("initial-visibility", attempts=QSTAT_ATTEMPTS)
        if initial["classification"] == "PERMISSION":
            terminal_reason, permission_error = "PERMISSION_ERROR", True
        elif initial["classification"] != "OK":
            terminal_reason = f"INITIAL_QSTAT_{initial['classification']}"
        elif not initial["visible"]:
            terminal_reason = "RC0_REQUEST_NOT_VISIBLE"
        else:
            if initial["state"] == "END":
                terminal_reason = "QSTAT_TERMINAL_END"
            elif initial["state"] == "RUN":
                self.scheduler_run_seen = True
                execution_deadline = time.monotonic() + self.requested_seconds + EXECUTION_GRACE_SECONDS
                self.record("execution_deadline_started_at_first_qstat_run")
            while terminal_reason == "UNKNOWN":
                now = time.monotonic()
                self.inspect_markers()
                self.acknowledge_canary()
                if now >= next_qstat:
                    current = self.qstat("poll", attempts=QSTAT_ATTEMPTS)
                    next_qstat = now + (1.0 if self.scheduler_run_seen else 5.0)
                    if current["classification"] == "PERMISSION":
                        terminal_reason, permission_error = "PERMISSION_ERROR", True
                        break
                    if current["classification"] == "OK":
                        if current["state"] == "RUN" and not self.scheduler_run_seen:
                            self.scheduler_run_seen = True
                            execution_deadline = now + self.requested_seconds + EXECUTION_GRACE_SECONDS
                            self.record("execution_deadline_started_at_first_qstat_run")
                        if current["state"] == "END":
                            terminal_reason = "QSTAT_TERMINAL_END"
                            break
                        if self.request_ever_visible and not current["visible"]:
                            terminal_reason = "REQUEST_DISAPPEARED_AFTER_VISIBILITY"
                            break
                    elif (
                        current["classification"] == "OTHER_ERROR"
                        and self.request_ever_visible
                        and not current["visible"]
                    ):
                        terminal_reason = "REQUEST_DISAPPEARED_AFTER_VISIBILITY"
                        break
                    else:
                        # bounded_command already exhausted its retry cap.  Do
                        # not let the outer poll loop manufacture an unbounded
                        # second retry layer after controller monitor stop.
                        terminal_reason = f"QSTAT_{current['classification']}"
                        break
                if execution_deadline is not None and now >= execution_deadline:
                    final_check = self.qstat(
                        "execution-deadline-recheck", attempts=QSTAT_ATTEMPTS
                    )
                    active_at_stop = final_check["state"] == "RUN"
                    terminal_reason = (
                        "EXECUTION_DEADLINE_REQUEST_STILL_RUN"
                        if active_at_stop
                        else "EXECUTION_DEADLINE_REQUEST_NOT_RUN"
                    )
                    break
                if execution_deadline is None and now >= queue_deadline:
                    transition = self.qstat(
                        "que-deadline-transition-recheck", attempts=QSTAT_ATTEMPTS
                    )
                    if transition["state"] == "RUN":
                        self.scheduler_run_seen = True
                        execution_deadline = now + self.requested_seconds + EXECUTION_GRACE_SECONDS
                        self.record("queue_deadline_raced_with_run_observation_continues")
                    else:
                        terminal_reason = "QUE_DEADLINE_CONTROLLER_QDEL_REQUIRED"
                        active_at_stop = transition["state"] in {"QUE", "HLD"}
                        break
                time.sleep(0.2)

        self.inspect_markers()
        tail = self.collect_scheduler_tail()
        if tail["qstat"]["state"] == "RUN":
            active_at_stop = True
        final, valid = self.build_final_observation(
            tail=tail,
            terminal_reason=terminal_reason,
            permission_error=permission_error,
            active_at_stop=active_at_stop,
        )
        self.write_final(final)
        self.record("observer_finished", terminal_reason=terminal_reason, valid=valid)
        return 0 if valid else 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--requested-walltime-seconds", type=int, default=180)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if not _REQUEST_ID_RE.fullmatch(args.request_id):
        raise ObserverError("request id is outside the closed NQSV identifier grammar")
    if not 1 <= args.requested_walltime_seconds <= 86400:
        raise ObserverError("requested walltime seconds is out of range")
    run_root, _driver_root, mode = _required_environment()
    return Observer(run_root, mode, args.request_id, args.requested_walltime_seconds).run()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ObserverError as exc:
        print(f"signal observer failed closed: {exc}", file=sys.stderr)
        raise SystemExit(16) from exc
