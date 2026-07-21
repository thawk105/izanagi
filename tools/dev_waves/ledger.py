"""Durable control WAL, runtime layout, and repository lease for dev-waves.

The WAL has exactly one mutating execution context: ``_WalWriter``.  Callers
may submit from several daemon threads, but sequence allocation, append,
``fsync``, snapshot advancement, and derived-cache replacement happen in that
writer thread in that order.  Signal handlers must use ``SignalRelay``; they
never enter the writer or acquire a Python lock.
"""
from __future__ import annotations

import errno
import fcntl
import os
import queue
import re
import socket
import stat
import threading
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from .redaction import assert_sanitized
from .schema import (
    SCHEMA_VERSION,
    TERMINAL_STATES,
    DevWavesError,
    ReasonCode,
    RunManifest,
    RunState,
    canonical_bytes,
    is_run_id,
    parse_run_manifest,
    strict_loads,
    validate_transition,
)


MAX_WAL_LINE_BYTES = 64 * 1024
MAX_WAL_BYTES = 16 * 1024 * 1024
EVENTS_NAME = "events.jsonl"
MANIFEST_NAME = "manifest.json"
STATUS_NAME = "status.json"
SUMMARY_NAME = "summary.md"
POISON_NAME = "emergency-stop.json"
LOCK_NAME = "control.lock"

EVENT_TYPES = frozenset({
    "run_created",
    "state_transition",
    "side_effect_prepared",
    "side_effect_observed",
    "observation_recorded",
    "client_request_recorded",
    "heartbeat",
    "signal_notified",
})
_EVENT_FIELDS = frozenset({
    "schema_version", "seq", "event", "state", "reason", "wave_index",
    "operation_id", "data", "recorded_utc", "boot_id", "boottime_ns",
})
_OPERATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


WriteFunction = Callable[[int, bytes], int]
FsyncFunction = Callable[[int], None]
BoottimeFunction = Callable[[], int]
UtcFunction = Callable[[], str]


def _error(reason_code: ReasonCode, kind: str, **detail: Any) -> DevWavesError:
    return DevWavesError(reason_code, {"kind": kind, **detail})


def _runtime_error(kind: str, **detail: Any) -> DevWavesError:
    return _error(ReasonCode.RUNTIME_IO_FAILURE, kind, **detail)


def _nofollow() -> int:
    value = getattr(os, "O_NOFOLLOW", None)
    if value is None:
        raise _runtime_error("nofollow-unavailable")
    return value


def _boottime_ns() -> int:
    clock = getattr(time, "CLOCK_BOOTTIME", None)
    if clock is None or not hasattr(time, "clock_gettime_ns"):
        raise _runtime_error("clock-boottime-unavailable")
    try:
        return time.clock_gettime_ns(clock)
    except OSError as exc:
        raise _runtime_error("clock-boottime-failed", code=exc.errno) from None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def read_boot_id() -> str:
    """Return the Linux boot identity used by WAL and lease bindings."""
    try:
        raw = Path("/proc/sys/kernel/random/boot_id").read_bytes()
        value = raw.decode("ascii", errors="strict").strip().lower()
    except (OSError, UnicodeError):
        raise _runtime_error("boot-id-unavailable") from None
    if not re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        value,
    ):
        raise _runtime_error("boot-id-invalid")
    return value


def _write_all(fd: int, payload: bytes, write: WriteFunction) -> None:
    view = memoryview(payload)
    while view:
        try:
            written = write(fd, view)
        except InterruptedError:
            continue
        if not isinstance(written, int) or written <= 0 or written > len(view):
            raise OSError(errno.EIO, "write made no valid progress")
        view = view[written:]


def _open_directory(path: Path) -> int:
    flags = os.O_RDONLY | _nofollow() | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise _runtime_error("open-directory", code=exc.errno) from None
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise _runtime_error("not-directory")
    return fd


def _open_directory_at(parent_fd: int, name: str) -> int:
    _safe_component(name, "directory")
    flags = os.O_RDONLY | _nofollow() | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise _runtime_error("open-directory-at", code=exc.errno) from None
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise _runtime_error("not-directory")
    return fd


def _open_regular_at(
    parent_fd: int, name: str, flags: int, *, mode: int = 0o600,
) -> int:
    _safe_component(name, "file")
    try:
        fd = os.open(name, flags | _nofollow(), mode, dir_fd=parent_fd)
    except OSError as exc:
        raise _runtime_error("open-file", code=exc.errno) from None
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        os.close(fd)
        raise _runtime_error("not-regular-file")
    return fd


def _safe_component(name: str, label: str) -> str:
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or "/" in name
        or "\x00" in name
    ):
        raise _error(ReasonCode.INVALID_RUN, "unsafe-component", label=label)
    return name


def _validate_run_id(run_id: str) -> str:
    if (
        not isinstance(run_id, str)
        or not is_run_id(run_id)
        or run_id.endswith(".staging")
        or run_id == LOCK_NAME
    ):
        raise _error(ReasonCode.INVALID_RUN, "run-id")
    return run_id


def _validate_wal_limits(max_line_bytes: int, max_total_bytes: int) -> None:
    for label, value in (
        ("max-line-bytes", max_line_bytes), ("max-total-bytes", max_total_bytes),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{label} must be a positive integer")


def _read_fd(fd: int, limit: int, label: str) -> bytes:
    chunks = []
    offset = 0
    while True:
        remaining = limit + 1 - offset
        if remaining <= 0:
            raise _error(ReasonCode.INVALID_RUN, "size-limit", label=label)
        try:
            chunk = os.pread(fd, min(64 * 1024, remaining), offset)
        except OSError as exc:
            raise _runtime_error("read", code=exc.errno, label=label) from None
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        offset += len(chunk)
        if offset > limit:
            raise _error(ReasonCode.INVALID_RUN, "size-limit", label=label)


def _lock_wal(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise _error(ReasonCode.DAEMON_BUSY, "wal-writer-busy") from None
    except OSError as exc:
        raise _runtime_error("wal-lock", code=exc.errno) from None


def _poison_at(run_fd: int) -> bool:
    try:
        info = os.stat(POISON_NAME, dir_fd=run_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise _runtime_error("poison-stat", code=exc.errno) from None
    if not stat.S_ISREG(info.st_mode):
        raise _error(ReasonCode.INVALID_RUN, "poison-not-regular")
    return True


def _path_is_poisoned(path: Path) -> bool:
    run_fd = _open_directory(path)
    try:
        return _poison_at(run_fd)
    finally:
        os.close(run_fd)


def _create_file_at(
    parent_fd: int,
    name: str,
    payload: bytes,
    *,
    write: WriteFunction,
    fsync: FsyncFunction,
) -> None:
    fd = _open_regular_at(
        parent_fd, name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode=0o600,
    )
    try:
        _write_all(fd, payload, write)
        fsync(fd)
    finally:
        os.close(fd)


def _atomic_cache_at(
    run_fd: int,
    name: str,
    payload: bytes,
    *,
    write: WriteFunction,
    fsync: FsyncFunction,
) -> None:
    suffix = f".tmp.{os.getpid()}.{threading.get_ident()}"
    temporary = name + suffix
    fd = _open_regular_at(
        run_fd, temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode=0o600,
    )
    try:
        _write_all(fd, payload, write)
        fsync(fd)
    except BaseException:
        try:
            os.unlink(temporary, dir_fd=run_fd)
        except OSError:
            pass
        raise
    finally:
        os.close(fd)
    try:
        os.replace(temporary, name, src_dir_fd=run_fd, dst_dir_fd=run_fd)
        fsync(run_fd)
    except OSError:
        try:
            os.unlink(temporary, dir_fd=run_fd)
        except OSError:
            pass
        raise


@dataclass(frozen=True)
class RuntimeLayout:
    """Secure names below one private repository-local runtime directory."""

    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))

    @classmethod
    def create(
        cls, root: os.PathLike[str] | str, *, fsync: Optional[FsyncFunction] = None,
    ) -> "RuntimeLayout":
        path = Path(root)
        sync = os.fsync if fsync is None else fsync
        created = False
        try:
            path.mkdir(mode=0o700)
            created = True
        except FileExistsError:
            pass
        except OSError as exc:
            raise _runtime_error("create-runtime", code=exc.errno) from None
        layout = cls(path)
        fd = _open_directory(path)
        try:
            info = os.fstat(fd)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise _runtime_error("runtime-permissions")
            sync(fd)
        except OSError as exc:
            raise _runtime_error("runtime-fsync", code=exc.errno) from None
        finally:
            os.close(fd)
        if created:
            parent_fd = _open_directory(path.parent)
            try:
                sync(parent_fd)
            except OSError as exc:
                raise _runtime_error("runtime-parent-fsync", code=exc.errno) from None
            finally:
                os.close(parent_fd)
        return layout

    @property
    def control_lock(self) -> Path:
        return self.root / LOCK_NAME

    @property
    def socket_path(self) -> Path:
        return self.root / ".s"

    def run_dir(self, run_id: str) -> Path:
        return self.root / _validate_run_id(run_id)

    def staging_dir(self, run_id: str) -> Path:
        return self.root / (_validate_run_id(run_id) + ".staging")


@dataclass(frozen=True)
class BoottimeDeadline:
    """An active deadline that cannot be extended by wall-clock rollback.

    Wave subprocess bounds remain integer seconds.  When converting this
    absolute deadline for such a bound, sub-second remaining time is treated
    as expired; that deliberate truncation is fail-closed.
    """

    boot_id: str
    started_ns: int
    deadline_ns: int

    @classmethod
    def start(
        cls,
        timeout_s: int,
        *,
        boot_id: Optional[str] = None,
        boottime: Optional[BoottimeFunction] = None,
    ) -> "BoottimeDeadline":
        if not isinstance(timeout_s, int) or isinstance(timeout_s, bool) or timeout_s < 1:
            raise ValueError("timeout_s must be a positive integer")
        clock = _boottime_ns if boottime is None else boottime
        started = clock()
        return cls(
            read_boot_id() if boot_id is None else boot_id,
            started,
            started + timeout_s * 1_000_000_000,
        )

    def remaining_ns(
        self,
        *,
        boot_id: Optional[str] = None,
        boottime: Optional[BoottimeFunction] = None,
    ) -> int:
        current_boot = read_boot_id() if boot_id is None else boot_id
        if current_boot != self.boot_id:
            raise _error(ReasonCode.AMBIGUOUS_RECOVERY, "boot-id-changed")
        clock = _boottime_ns if boottime is None else boottime
        return max(0, self.deadline_ns - clock())

    def expired(
        self,
        *,
        boot_id: Optional[str] = None,
        boottime: Optional[BoottimeFunction] = None,
    ) -> bool:
        return self.remaining_ns(boot_id=boot_id, boottime=boottime) == 0


@dataclass(frozen=True)
class SideEffectIntent:
    """A non-idempotent operation that must be prepared before execution."""

    operation_id: str
    operation: str
    argv_digest: str
    expected: Mapping[str, Any]

    def __post_init__(self) -> None:
        if _OPERATION_ID_RE.fullmatch(self.operation_id) is None:
            raise ValueError("invalid operation_id")
        if not isinstance(self.operation, str) or not self.operation:
            raise ValueError("operation must be non-empty")
        if not re.fullmatch(r"[0-9a-f]{64}", self.argv_digest):
            raise ValueError("argv_digest must be lowercase SHA-256")
        assert_sanitized({"operation": self.operation, "argv_digest": self.argv_digest,
                          "expected": self.expected})


@dataclass(frozen=True)
class Observation:
    """An idempotent check; unlike SideEffectIntent it needs no prepare event."""

    operation_id: str
    operation: str
    observed: Mapping[str, Any]

    def __post_init__(self) -> None:
        if _OPERATION_ID_RE.fullmatch(self.operation_id) is None:
            raise ValueError("invalid operation_id")
        if not isinstance(self.operation, str) or not self.operation:
            raise ValueError("operation must be non-empty")
        assert_sanitized({"operation": self.operation, "observed": self.observed})


@dataclass(frozen=True)
class ReplaySnapshot:
    run_id: str
    state: RunState
    reason: Optional[ReasonCode]
    wave_index: Optional[int]
    last_seq: int
    event_count: int
    boot_id: str
    started_boottime_ns: int
    last_boottime_ns: int
    prepared_operations: frozenset[str]
    observed_operations: frozenset[str]
    poisoned: bool = False


@dataclass(frozen=True)
class DiscoveredRun:
    run_id: str
    path: Path
    reason: Optional[ReasonCode]
    snapshot: Optional[ReplaySnapshot]

    @property
    def valid(self) -> bool:
        return self.reason is None


def _new_snapshot(run_id: str, record: Mapping[str, Any]) -> ReplaySnapshot:
    return ReplaySnapshot(
        run_id=run_id,
        state=RunState.CREATED,
        reason=None,
        wave_index=record["wave_index"],
        last_seq=1,
        event_count=1,
        boot_id=record["boot_id"],
        started_boottime_ns=record["boottime_ns"],
        last_boottime_ns=record["boottime_ns"],
        prepared_operations=frozenset(),
        observed_operations=frozenset(),
    )


def _validate_record_shape(record: object, expected_seq: int) -> Mapping[str, Any]:
    if not isinstance(record, dict) or set(record) != _EVENT_FIELDS:
        raise _error(ReasonCode.INVALID_RUN, "event-fields")
    if record["schema_version"] != SCHEMA_VERSION:
        raise _error(ReasonCode.INVALID_RUN, "event-version")
    if record["seq"] != expected_seq or isinstance(record["seq"], bool):
        raise _error(ReasonCode.INVALID_RUN, "event-seq")
    if record["event"] not in EVENT_TYPES:
        raise _error(ReasonCode.INVALID_RUN, "event-type")
    if not isinstance(record["recorded_utc"], str) or "T" not in record["recorded_utc"]:
        raise _error(ReasonCode.INVALID_RUN, "event-time")
    if not isinstance(record["boot_id"], str) or len(record["boot_id"]) > 64:
        raise _error(ReasonCode.INVALID_RUN, "event-boot-id")
    if (
        not isinstance(record["boottime_ns"], int)
        or isinstance(record["boottime_ns"], bool)
        or record["boottime_ns"] < 0
    ):
        raise _error(ReasonCode.INVALID_RUN, "event-boottime")
    wave = record["wave_index"]
    if wave is not None and (
        not isinstance(wave, int) or isinstance(wave, bool) or wave < 1
    ):
        raise _error(ReasonCode.INVALID_RUN, "event-wave")
    operation_id = record["operation_id"]
    operation_event = record["event"] in {
        "side_effect_prepared", "side_effect_observed", "observation_recorded",
    }
    if operation_event:
        if not isinstance(operation_id, str) or _OPERATION_ID_RE.fullmatch(operation_id) is None:
            raise _error(ReasonCode.INVALID_RUN, "event-operation-id")
    elif operation_id is not None:
        raise _error(ReasonCode.INVALID_RUN, "unexpected-operation-id")
    if not isinstance(record["data"], dict):
        raise _error(ReasonCode.INVALID_RUN, "event-data")
    try:
        assert_sanitized(record["data"])
    except ValueError:
        raise _error(ReasonCode.INVALID_RUN, "unsanitized-event") from None
    if record["event"] in {"run_created", "state_transition"}:
        try:
            state = RunState(record["state"])
        except (TypeError, ValueError):
            raise _error(ReasonCode.INVALID_RUN, "event-state") from None
        if record["event"] == "run_created" and state is not RunState.CREATED:
            raise _error(ReasonCode.INVALID_RUN, "initial-state")
    elif record["state"] is not None:
        raise _error(ReasonCode.INVALID_RUN, "unexpected-state")
    if record["reason"] is not None:
        try:
            ReasonCode(record["reason"])
        except (TypeError, ValueError):
            raise _error(ReasonCode.INVALID_RUN, "event-reason") from None
    if record["event"] != "state_transition" and record["reason"] is not None:
        raise _error(ReasonCode.INVALID_RUN, "unexpected-reason")
    return record


def _apply_record(snapshot: ReplaySnapshot, record: Mapping[str, Any]) -> ReplaySnapshot:
    if snapshot.state in TERMINAL_STATES:
        raise _error(ReasonCode.INVALID_RUN, "event-after-terminal")
    if record["boot_id"] != snapshot.boot_id:
        raise _error(ReasonCode.AMBIGUOUS_RECOVERY, "boot-id-changed")
    if record["boottime_ns"] < snapshot.last_boottime_ns:
        raise _error(ReasonCode.INVALID_RUN, "boottime-regressed")
    state = snapshot.state
    reason = snapshot.reason
    if record["event"] == "run_created":
        raise _error(ReasonCode.INVALID_RUN, "duplicate-run-created")
    if record["event"] == "state_transition":
        target = RunState(record["state"])
        event_reason = None
        if record["reason"] is not None:
            event_reason = ReasonCode(record["reason"])
        # schema.py is deliberately the only transition edge table.
        validate_transition(state, target, reason=event_reason)
        if target in TERMINAL_STATES and event_reason is None:
            raise _error(ReasonCode.INVALID_RUN, "terminal-reason-missing")
        state = target
        reason = event_reason
    prepared = set(snapshot.prepared_operations)
    observed = set(snapshot.observed_operations)
    operation_id = record["operation_id"]
    if record["event"] == "side_effect_prepared":
        if operation_id in prepared or operation_id in observed:
            raise _error(ReasonCode.INVALID_RUN, "duplicate-side-effect")
        prepared.add(operation_id)
    elif record["event"] == "side_effect_observed":
        if operation_id not in prepared or operation_id in observed:
            raise _error(ReasonCode.INVALID_RUN, "unprepared-side-effect")
        observed.add(operation_id)
    return replace(
        snapshot,
        state=state,
        reason=reason,
        wave_index=(record["wave_index"] if record["wave_index"] is not None
                    else snapshot.wave_index),
        last_seq=record["seq"],
        event_count=snapshot.event_count + 1,
        last_boottime_ns=record["boottime_ns"],
        prepared_operations=frozenset(prepared),
        observed_operations=frozenset(observed),
    )


def replay_run(
    run_dir: os.PathLike[str] | str,
    *,
    max_line_bytes: int = MAX_WAL_LINE_BYTES,
    max_total_bytes: int = MAX_WAL_BYTES,
) -> ReplaySnapshot:
    """Strictly replay one complete canonical JSONL WAL."""
    _validate_wal_limits(max_line_bytes, max_total_bytes)
    path = Path(run_dir)
    run_id = path.name
    _validate_run_id(run_id)
    run_fd = _open_directory(path)
    try:
        wal_fd = _open_regular_at(run_fd, EVENTS_NAME, os.O_RDONLY)
        try:
            raw = _read_fd(wal_fd, max_total_bytes, EVENTS_NAME)
        finally:
            os.close(wal_fd)
        poisoned = _poison_at(run_fd)
    finally:
        os.close(run_fd)
    return _replay_bytes(
        run_id, raw, poisoned=poisoned,
        max_line_bytes=max_line_bytes, max_total_bytes=max_total_bytes,
    )


def _replay_bytes(
    run_id: str,
    raw: bytes,
    *,
    poisoned: bool,
    max_line_bytes: int,
    max_total_bytes: int,
) -> ReplaySnapshot:
    if len(raw) > max_total_bytes:
        raise _error(ReasonCode.INVALID_RUN, "size-limit", label=EVENTS_NAME)
    if not raw or not raw.endswith(b"\n"):
        raise _error(ReasonCode.INVALID_RUN, "partial-wal-tail")
    lines = raw.splitlines(keepends=True)
    snapshot: Optional[ReplaySnapshot] = None
    for index, line in enumerate(lines, 1):
        if len(line) > max_line_bytes:
            raise _error(ReasonCode.INVALID_RUN, "wal-line-limit")
        body = line[:-1]
        try:
            record = strict_loads(
                body, label="dev-waves-event", max_bytes=max_line_bytes,
            )
        except DevWavesError as exc:
            if exc.code is ReasonCode.OUTPUT_INVALID:
                raise _error(ReasonCode.INVALID_RUN, "strict-event-json") from None
            raise
        if canonical_bytes(record) != body:
            raise _error(ReasonCode.INVALID_RUN, "noncanonical-event")
        item = _validate_record_shape(record, index)
        if snapshot is None:
            if item["event"] != "run_created":
                raise _error(ReasonCode.INVALID_RUN, "first-event")
            snapshot = _new_snapshot(run_id, item)
        else:
            snapshot = _apply_record(snapshot, item)
    if snapshot is None:
        raise _error(ReasonCode.INVALID_RUN, "empty-wal")
    return replace(snapshot, poisoned=poisoned)


def _status_bytes(snapshot: ReplaySnapshot) -> bytes:
    value = {
        "schema_version": SCHEMA_VERSION,
        "run_id": snapshot.run_id,
        "state": snapshot.state,
        "reason": snapshot.reason,
        "wave_index": snapshot.wave_index,
        "seq": snapshot.last_seq,
    }
    return canonical_bytes(value) + b"\n"


def _summary_bytes(snapshot: ReplaySnapshot) -> bytes:
    reason = snapshot.reason.value if snapshot.reason is not None else "-"
    wave = str(snapshot.wave_index) if snapshot.wave_index is not None else "-"
    text = (
        "# dev-wave run summary\n\n"
        f"- run: {snapshot.run_id}\n"
        f"- state: {snapshot.state.value}\n"
        f"- wave: {wave}\n"
        f"- reason: {reason}\n"
        f"- durable sequence: {snapshot.last_seq}\n"
    )
    return text.encode("utf-8")


@dataclass
class _AppendRequest:
    event: str
    state: Optional[RunState]
    reason: Optional[ReasonCode]
    wave_index: Optional[int]
    operation_id: Optional[str]
    data: Mapping[str, Any]
    done: threading.Event
    snapshot: Optional[ReplaySnapshot] = None
    error: Optional[BaseException] = None


@dataclass
class _RebuildRequest:
    done: threading.Event
    snapshot: Optional[ReplaySnapshot] = None
    error: Optional[BaseException] = None


class _WalWriter:
    def __init__(
        self,
        *,
        run_fd: int,
        wal_fd: int,
        snapshot: Optional[ReplaySnapshot],
        run_id: str,
        boot_id: str,
        write: WriteFunction,
        fsync: FsyncFunction,
        boottime: BoottimeFunction,
        utc: UtcFunction,
        max_line_bytes: int,
        max_total_bytes: int,
        initial_size: int,
    ) -> None:
        self.run_fd = run_fd
        self.wal_fd = wal_fd
        self.snapshot = snapshot
        self.run_id = run_id
        self.boot_id = boot_id
        self.write = write
        self.fsync = fsync
        self.boottime = boottime
        self.utc = utc
        self.max_line_bytes = max_line_bytes
        self.max_total_bytes = max_total_bytes
        self.total_bytes = initial_size
        self.requests: "queue.Queue[object]" = queue.Queue()
        self.fatal: Optional[BaseException] = None
        self.thread = threading.Thread(
            target=self._run, name=f"dev-waves-wal-{run_id}", daemon=True,
        )
        self.thread.start()

    def submit(self, request: _AppendRequest) -> ReplaySnapshot:
        if self.fatal is not None:
            raise self.fatal
        self.requests.put(request)
        request.done.wait()
        if request.error is not None:
            raise request.error
        assert request.snapshot is not None
        return request.snapshot

    def rebuild(self) -> ReplaySnapshot:
        if self.fatal is not None:
            raise self.fatal
        request = _RebuildRequest(done=threading.Event())
        self.requests.put(request)
        request.done.wait()
        if request.error is not None:
            raise request.error
        assert request.snapshot is not None
        return request.snapshot

    def close(self) -> None:
        if self.thread.is_alive():
            self.requests.put(None)
            self.thread.join()
        try:
            fcntl.flock(self.wal_fd, fcntl.LOCK_UN)
        finally:
            os.close(self.wal_fd)
        os.close(self.run_fd)

    def _poison(self, source: BaseException) -> None:
        payload = canonical_bytes({
            "schema_version": SCHEMA_VERSION,
            "reason": ReasonCode.POISONED,
            "state": self.snapshot.state if self.snapshot is not None else RunState.CREATED,
            "seq": self.snapshot.last_seq if self.snapshot is not None else 0,
        }) + b"\n"
        try:
            _create_file_at(
                self.run_fd, POISON_NAME, payload, write=self.write, fsync=self.fsync,
            )
            self.fsync(self.run_fd)
        except BaseException:
            # Best effort by design: the original WAL failure remains primary.
            pass
        self.fatal = _runtime_error(
            "wal-durability-failed",
            code=(source.errno if isinstance(source, OSError) else None),
        )

    def _make_record(self, request: _AppendRequest) -> Mapping[str, Any]:
        seq = 1 if self.snapshot is None else self.snapshot.last_seq + 1
        return {
            "schema_version": SCHEMA_VERSION,
            "seq": seq,
            "event": request.event,
            "state": request.state,
            "reason": request.reason,
            "wave_index": request.wave_index,
            "operation_id": request.operation_id,
            "data": dict(request.data),
            "recorded_utc": self.utc(),
            "boot_id": self.boot_id,
            "boottime_ns": self.boottime(),
        }

    def _append(self, request: _AppendRequest) -> ReplaySnapshot:
        record = self._make_record(request)
        _validate_record_shape(record, record["seq"])
        if self.snapshot is None:
            if record["event"] != "run_created":
                raise _error(ReasonCode.INVALID_RUN, "first-event")
            next_snapshot = _new_snapshot(self.run_id, record)
        else:
            next_snapshot = _apply_record(self.snapshot, record)
        payload = canonical_bytes(record) + b"\n"
        if len(payload) > self.max_line_bytes:
            raise _error(ReasonCode.INVALID_RUN, "wal-line-limit")
        if self.total_bytes + len(payload) > self.max_total_bytes:
            raise _error(ReasonCode.INVALID_RUN, "wal-total-limit")
        try:
            _write_all(self.wal_fd, payload, self.write)
            self.fsync(self.wal_fd)
        except OSError as exc:
            self._poison(exc)
            assert self.fatal is not None
            raise self.fatal
        self.total_bytes += len(payload)
        try:
            durable_raw = _read_fd(self.wal_fd, self.max_total_bytes, EVENTS_NAME)
            durable_snapshot = _replay_bytes(
                self.run_id, durable_raw, poisoned=False,
                max_line_bytes=self.max_line_bytes,
                max_total_bytes=self.max_total_bytes,
            )
            if durable_snapshot != next_snapshot:
                raise _error(ReasonCode.INVALID_RUN, "post-fsync-replay-mismatch")
        except BaseException as exc:
            self._poison(exc)
            assert self.fatal is not None
            raise self.fatal
        self.snapshot = durable_snapshot
        try:
            _atomic_cache_at(
                self.run_fd, STATUS_NAME, _status_bytes(durable_snapshot),
                write=self.write, fsync=self.fsync,
            )
            _atomic_cache_at(
                self.run_fd, SUMMARY_NAME, _summary_bytes(durable_snapshot),
                write=self.write, fsync=self.fsync,
            )
        except OSError as exc:
            raise _runtime_error("cache-rebuild", code=exc.errno) from None
        return durable_snapshot

    def _rebuild(self) -> ReplaySnapshot:
        raw = _read_fd(self.wal_fd, self.max_total_bytes, EVENTS_NAME)
        snapshot = _replay_bytes(
            self.run_id, raw, poisoned=False,
            max_line_bytes=self.max_line_bytes,
            max_total_bytes=self.max_total_bytes,
        )
        try:
            _atomic_cache_at(
                self.run_fd, STATUS_NAME, _status_bytes(snapshot),
                write=self.write, fsync=self.fsync,
            )
            _atomic_cache_at(
                self.run_fd, SUMMARY_NAME, _summary_bytes(snapshot),
                write=self.write, fsync=self.fsync,
            )
        except OSError as exc:
            raise _runtime_error("cache-rebuild", code=exc.errno) from None
        self.snapshot = snapshot
        return snapshot

    def _run(self) -> None:
        while True:
            request = self.requests.get()
            if request is None:
                return
            if self.fatal is not None:
                assert isinstance(request, (_AppendRequest, _RebuildRequest))
                request.error = self.fatal
                request.done.set()
                continue
            if isinstance(request, _RebuildRequest):
                try:
                    request.snapshot = self._rebuild()
                except BaseException as exc:
                    request.error = exc
                finally:
                    request.done.set()
                continue
            assert isinstance(request, _AppendRequest)
            try:
                request.snapshot = self._append(request)
            except BaseException as exc:
                request.error = exc
            finally:
                request.done.set()


class ControlLedger:
    """One open run WAL and its single serial writer queue."""

    def __init__(self, path: Path, writer: _WalWriter) -> None:
        self.path = path
        self._writer = writer
        self._closed = False

    @classmethod
    def create(
        cls,
        layout: RuntimeLayout | os.PathLike[str] | str,
        run_id: str,
        manifest: RunManifest | Mapping[str, Any],
        *,
        max_line_bytes: int = MAX_WAL_LINE_BYTES,
        max_total_bytes: int = MAX_WAL_BYTES,
        write: Optional[WriteFunction] = None,
        fsync: Optional[FsyncFunction] = None,
        boottime: Optional[BoottimeFunction] = None,
        utc: Optional[UtcFunction] = None,
        boot_id: Optional[str] = None,
    ) -> "ControlLedger":
        _validate_wal_limits(max_line_bytes, max_total_bytes)
        active_layout = layout if isinstance(layout, RuntimeLayout) else RuntimeLayout.create(layout)
        _validate_run_id(run_id)
        writer_fn = os.write if write is None else write
        sync_fn = os.fsync if fsync is None else fsync
        clock_fn = _boottime_ns if boottime is None else boottime
        utc_fn = _utc_now if utc is None else utc
        active_boot_id = read_boot_id() if boot_id is None else boot_id
        manifest_raw = canonical_bytes(manifest)
        parsed = parse_run_manifest(manifest_raw)
        if parsed.run_id != run_id:
            raise _error(ReasonCode.INVALID_RUN, "manifest-run-id")
        root_fd = _open_directory(active_layout.root)
        staging_name = run_id + ".staging"
        try:
            try:
                os.mkdir(staging_name, mode=0o700, dir_fd=root_fd)
                sync_fn(root_fd)
            except OSError as exc:
                raise _runtime_error("create-staging", code=exc.errno) from None
            staging_fd = _open_directory_at(root_fd, staging_name)
            try:
                _create_file_at(
                    staging_fd, MANIFEST_NAME, manifest_raw + b"\n",
                    write=writer_fn, fsync=sync_fn,
                )
                sync_fn(staging_fd)
                wal_fd = _open_regular_at(
                    staging_fd, EVENTS_NAME,
                    os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_EXCL,
                )
                try:
                    _lock_wal(wal_fd)
                except BaseException:
                    os.close(wal_fd)
                    raise
                wal_writer = _WalWriter(
                    run_fd=staging_fd,
                    wal_fd=wal_fd,
                    snapshot=None,
                    run_id=run_id,
                    boot_id=active_boot_id,
                    write=writer_fn,
                    fsync=sync_fn,
                    boottime=clock_fn,
                    utc=utc_fn,
                    max_line_bytes=max_line_bytes,
                    max_total_bytes=max_total_bytes,
                    initial_size=0,
                )
                ledger = cls(active_layout.staging_dir(run_id), wal_writer)
                ledger.append(
                    "run_created",
                    state=RunState.CREATED,
                    data={"run_id": run_id, "request_digest": parsed.request_digest},
                )
                sync_fn(staging_fd)
                try:
                    os.rename(staging_name, run_id, src_dir_fd=root_fd, dst_dir_fd=root_fd)
                except OSError as exc:
                    ledger.close()
                    raise _runtime_error("publish-run", code=exc.errno) from None
                ledger.path = active_layout.run_dir(run_id)
                try:
                    sync_fn(root_fd)
                except OSError as exc:
                    ledger._writer._poison(exc)
                    ledger.close()
                    raise _runtime_error("publish-parent-fsync", code=exc.errno) from None
                return ledger
            except BaseException:
                # A failed bootstrap intentionally leaves staging evidence.
                if "ledger" in locals() and not ledger._closed:
                    ledger.close()
                else:
                    try:
                        os.close(staging_fd)
                    except OSError:
                        pass
                raise
        finally:
            os.close(root_fd)

    @classmethod
    def open(
        cls,
        run: RuntimeLayout | os.PathLike[str] | str,
        run_id: Optional[str] = None,
        *,
        max_line_bytes: int = MAX_WAL_LINE_BYTES,
        max_total_bytes: int = MAX_WAL_BYTES,
        write: Optional[WriteFunction] = None,
        fsync: Optional[FsyncFunction] = None,
        boottime: Optional[BoottimeFunction] = None,
        utc: Optional[UtcFunction] = None,
        boot_id: Optional[str] = None,
    ) -> "ControlLedger":
        _validate_wal_limits(max_line_bytes, max_total_bytes)
        if run_id is None:
            if isinstance(run, RuntimeLayout):
                raise TypeError("run_id is required with RuntimeLayout")
            path = Path(run)
        else:
            root = run.root if isinstance(run, RuntimeLayout) else Path(run)
            path = root / _validate_run_id(run_id)
        if _path_is_poisoned(path):
            raise _error(ReasonCode.POISONED, "poison-record")
        snapshot = replay_run(
            path, max_line_bytes=max_line_bytes, max_total_bytes=max_total_bytes,
        )
        if snapshot.poisoned:
            raise _error(ReasonCode.POISONED, "poison-record")
        current_boot = read_boot_id() if boot_id is None else boot_id
        if snapshot.state not in TERMINAL_STATES and current_boot != snapshot.boot_id:
            raise _error(ReasonCode.AMBIGUOUS_RECOVERY, "boot-id-changed")
        run_fd = _open_directory(path)
        try:
            manifest_fd = _open_regular_at(run_fd, MANIFEST_NAME, os.O_RDONLY)
            try:
                manifest_raw = _read_fd(manifest_fd, 1024 * 1024, MANIFEST_NAME)
            finally:
                os.close(manifest_fd)
            if not manifest_raw.endswith(b"\n"):
                raise _error(ReasonCode.INVALID_RUN, "manifest-tail")
            manifest = parse_run_manifest(manifest_raw[:-1])
            if manifest.run_id != path.name:
                raise _error(ReasonCode.INVALID_RUN, "manifest-run-id")
            wal_fd = _open_regular_at(run_fd, EVENTS_NAME, os.O_RDWR | os.O_APPEND)
            try:
                _lock_wal(wal_fd)
            except BaseException:
                os.close(wal_fd)
                raise
            size = os.fstat(wal_fd).st_size
        except BaseException:
            os.close(run_fd)
            raise
        writer = _WalWriter(
            run_fd=run_fd,
            wal_fd=wal_fd,
            snapshot=snapshot,
            run_id=path.name,
            boot_id=current_boot,
            write=os.write if write is None else write,
            fsync=os.fsync if fsync is None else fsync,
            boottime=_boottime_ns if boottime is None else boottime,
            utc=_utc_now if utc is None else utc,
            max_line_bytes=max_line_bytes,
            max_total_bytes=max_total_bytes,
            initial_size=size,
        )
        return cls(path, writer)

    @property
    def snapshot(self) -> ReplaySnapshot:
        snapshot = self._writer.snapshot
        if snapshot is None:
            raise _error(ReasonCode.INVALID_RUN, "missing-snapshot")
        return snapshot

    @property
    def poisoned(self) -> bool:
        return self._writer.fatal is not None or (self.path / POISON_NAME).exists()

    def replay(self) -> ReplaySnapshot:
        if self._closed:
            raise _runtime_error("ledger-closed")
        return self._writer.rebuild()

    def append(
        self,
        event: str,
        *,
        state: Optional[RunState] = None,
        reason: Optional[ReasonCode] = None,
        wave_index: Optional[int] = None,
        operation_id: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ReplaySnapshot:
        if event in {
            "side_effect_prepared", "side_effect_observed", "observation_recorded",
        }:
            raise TypeError("typed operation events require their dedicated API")
        return self._append_event(
            event,
            state=state,
            reason=reason,
            wave_index=wave_index,
            operation_id=operation_id,
            data=data,
        )

    def _append_event(
        self,
        event: str,
        *,
        state: Optional[RunState] = None,
        reason: Optional[ReasonCode] = None,
        wave_index: Optional[int] = None,
        operation_id: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> ReplaySnapshot:
        if self._closed:
            raise _runtime_error("ledger-closed")
        if event not in EVENT_TYPES:
            raise _error(ReasonCode.INVALID_RUN, "event-type")
        if state is not None and not isinstance(state, RunState):
            raise TypeError("state must be RunState or None")
        if reason is not None and not isinstance(reason, ReasonCode):
            raise TypeError("reason must be ReasonCode or None")
        clean_data = {} if data is None else dict(data)
        try:
            assert_sanitized(clean_data)
        except ValueError:
            raise _error(ReasonCode.INVALID_RUN, "unsanitized-event") from None
        # Detach nested mutable mappings before crossing the queue boundary.
        try:
            detached = strict_loads(
                canonical_bytes(clean_data),
                label="dev-waves-event-data",
                max_bytes=self._writer.max_line_bytes,
            )
        except DevWavesError as exc:
            if exc.code is ReasonCode.OUTPUT_INVALID:
                raise _error(ReasonCode.INVALID_RUN, "event-data-limit") from None
            raise
        assert isinstance(detached, dict)
        request = _AppendRequest(
            event=event,
            state=state,
            reason=reason,
            wave_index=wave_index,
            operation_id=operation_id,
            data=detached,
            done=threading.Event(),
        )
        return self._writer.submit(request)

    def transition(
        self,
        target: RunState,
        *,
        reason: Optional[ReasonCode] = None,
        wave_index: Optional[int] = None,
    ) -> ReplaySnapshot:
        return self.append(
            "state_transition", state=target, reason=reason, wave_index=wave_index,
        )

    def prepare_side_effect(
        self, intent: SideEffectIntent, *, wave_index: Optional[int] = None,
    ) -> ReplaySnapshot:
        if not isinstance(intent, SideEffectIntent):
            raise TypeError("intent must be SideEffectIntent")
        return self._append_event(
            "side_effect_prepared",
            wave_index=wave_index,
            operation_id=intent.operation_id,
            data={
                "operation": intent.operation,
                "argv_digest": intent.argv_digest,
                "expected": intent.expected,
            },
        )

    def observe_side_effect(
        self,
        intent: SideEffectIntent,
        observed: Mapping[str, Any],
        *,
        wave_index: Optional[int] = None,
    ) -> ReplaySnapshot:
        if not isinstance(intent, SideEffectIntent):
            raise TypeError("intent must be SideEffectIntent")
        return self._append_event(
            "side_effect_observed",
            wave_index=wave_index,
            operation_id=intent.operation_id,
            data={"operation": intent.operation, "observed": dict(observed)},
        )

    def record_observation(
        self, observation: Observation, *, wave_index: Optional[int] = None,
    ) -> ReplaySnapshot:
        if not isinstance(observation, Observation):
            raise TypeError("observation must be Observation")
        return self._append_event(
            "observation_recorded",
            wave_index=wave_index,
            operation_id=observation.operation_id,
            data={
                "operation": observation.operation,
                "observed": observation.observed,
            },
        )

    def rebuild_status(self) -> ReplaySnapshot:
        if self._closed:
            raise _runtime_error("ledger-closed")
        return self._writer.rebuild()

    def finish(
        self,
        target: Optional[RunState] = None,
        *,
        reason: Optional[ReasonCode] = None,
        wave_index: Optional[int] = None,
    ) -> Optional[ReplaySnapshot]:
        snapshot = None
        if target is not None:
            if target not in TERMINAL_STATES:
                raise ValueError("finish target must be terminal")
            snapshot = self.transition(target, reason=reason, wave_index=wave_index)
        self.close()
        return snapshot

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._writer.close()

    def __enter__(self) -> "ControlLedger":
        return self

    def __exit__(self, _kind: object, _value: object, _tb: object) -> None:
        self.close()


def discover_runs(
    layout: RuntimeLayout | os.PathLike[str] | str,
    *,
    max_line_bytes: int = MAX_WAL_LINE_BYTES,
    max_total_bytes: int = MAX_WAL_BYTES,
) -> tuple[DiscoveredRun, ...]:
    """List published runs and staging remnants without repairing either."""
    root = layout.root if isinstance(layout, RuntimeLayout) else Path(layout)
    root_fd = _open_directory(root)
    try:
        try:
            names = sorted(os.listdir(root_fd))
        except OSError as exc:
            raise _runtime_error("discover-list", code=exc.errno) from None
    finally:
        os.close(root_fd)
    result = []
    for name in names:
        if name in {
            LOCK_NAME, ".s", "invalid-requests.jsonl", "server-profile.json",
        }:
            continue
        if name.endswith(".staging"):
            run_id = name[:-len(".staging")]
            if is_run_id(run_id):
                result.append(DiscoveredRun(
                    run_id, root / name, ReasonCode.INVALID_RUN, None,
                ))
            continue
        if not is_run_id(name):
            continue
        path = root / name
        try:
            snapshot = replay_run(
                path, max_line_bytes=max_line_bytes, max_total_bytes=max_total_bytes,
            )
        except DevWavesError:
            try:
                poisoned = _path_is_poisoned(path)
            except DevWavesError:
                poisoned = False
            reason = ReasonCode.POISONED if poisoned else ReasonCode.INVALID_RUN
            result.append(DiscoveredRun(name, path, reason, None))
        else:
            reason = ReasonCode.POISONED if snapshot.poisoned else None
            result.append(DiscoveredRun(name, path, reason, snapshot))
    return tuple(result)


class SignalRelay:
    """Async-signal-safe self-pipe adapter; ``notify`` only calls ``os.write``."""

    def __init__(self) -> None:
        flags = getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
        if hasattr(os, "pipe2"):
            self._read_fd, self._write_fd = os.pipe2(flags)
        else:  # pragma: no cover - Linux production has pipe2
            self._read_fd, self._write_fd = os.pipe()
            os.set_blocking(self._read_fd, False)
            os.set_blocking(self._write_fd, False)
        self._closed = False

    def fileno(self) -> int:
        return self._read_fd

    def notify(self, signum: int, _frame: object = None) -> None:
        """Suitable as a signal handler: no lock, queue, allocation, or fsync."""
        try:
            os.write(self._write_fd, bytes((signum & 0xFF,)))
        except OSError as exc:
            if exc.errno not in {errno.EAGAIN, errno.EWOULDBLOCK, errno.EBADF}:
                raise

    def drain(self) -> tuple[int, ...]:
        values = []
        while True:
            try:
                chunk = os.read(self._read_fd, 4096)
            except OSError as exc:
                if exc.errno in {errno.EAGAIN, errno.EWOULDBLOCK}:
                    break
                raise
            if not chunk:
                break
            values.extend(chunk)
        return tuple(values)

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            os.close(self._read_fd)
            os.close(self._write_fd)

    def __enter__(self) -> "SignalRelay":
        return self

    def __exit__(self, _kind: object, _value: object, _tb: object) -> None:
        self.close()


class RepositoryLease:
    """Single-host repository lease bound to hostname and Linux boot id."""

    def __init__(
        self, path: Path, directory_fd: int, fd: int, hostname: str, boot_id: str,
    ) -> None:
        self.path = path
        self._directory_fd = directory_fd
        self._fd = fd
        self.hostname = hostname
        self.boot_id = boot_id
        self._released = False

    @classmethod
    def acquire(
        cls,
        layout: RuntimeLayout | os.PathLike[str] | str,
        *,
        timeout_s: float = 0.0,
        hostname: Optional[str] = None,
        boot_id: Optional[str] = None,
        boottime: Optional[BoottimeFunction] = None,
        fsync: Optional[FsyncFunction] = None,
    ) -> "RepositoryLease":
        if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)) or timeout_s < 0:
            raise ValueError("timeout_s must be non-negative")
        active_layout = layout if isinstance(layout, RuntimeLayout) else RuntimeLayout.create(layout)
        host = socket.gethostname() if hostname is None else hostname
        active_boot = read_boot_id() if boot_id is None else boot_id
        if not host or len(host) > 255 or "\x00" in host:
            raise _runtime_error("hostname-invalid")
        clock = _boottime_ns if boottime is None else boottime
        sync = os.fsync if fsync is None else fsync
        root_fd = _open_directory(active_layout.root)
        created = False
        try:
            try:
                fd = _open_regular_at(
                    root_fd, LOCK_NAME,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL,
                )
                created = True
                sync(root_fd)
            except DevWavesError as exc:
                if exc.detail.get("code") != errno.EEXIST:
                    raise
                fd = _open_regular_at(root_fd, LOCK_NAME, os.O_RDWR)
            deadline = clock() + int(timeout_s * 1_000_000_000)
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if clock() >= deadline:
                        raise _error(ReasonCode.DAEMON_BUSY, "lease-busy")
                    time.sleep(0.01)
            lease = cls(active_layout.control_lock, root_fd, fd, host, active_boot)
            lease._revalidate_inode()
            if created:
                record = canonical_bytes({
                    "schema_version": SCHEMA_VERSION,
                    "hostname": host,
                    "boot_id": active_boot,
                }) + b"\n"
                _write_all(fd, record, os.write)
                sync(fd)
                sync(root_fd)
            else:
                raw = _read_fd(fd, 4096, LOCK_NAME)
                if not raw.endswith(b"\n"):
                    raise _error(ReasonCode.FOREIGN_LEASE, "lease-record-invalid")
                value = strict_loads(raw[:-1], label="repository-lease", max_bytes=4096)
                if (
                    not isinstance(value, dict)
                    or set(value) != {"schema_version", "hostname", "boot_id"}
                    or value["schema_version"] != SCHEMA_VERSION
                    or canonical_bytes(value) != raw[:-1]
                ):
                    raise _error(ReasonCode.FOREIGN_LEASE, "lease-record-invalid")
                if value["hostname"] != host or value["boot_id"] != active_boot:
                    raise _error(ReasonCode.FOREIGN_LEASE, "lease-binding")
            lease._revalidate_inode()
            return lease
        except BaseException:
            try:
                os.close(fd)
            except (OSError, UnboundLocalError):
                pass
            os.close(root_fd)
            raise

    def _revalidate_inode(self) -> None:
        try:
            fd_info = os.fstat(self._fd)
            path_info = os.stat(
                LOCK_NAME, dir_fd=self._directory_fd, follow_symlinks=False,
            )
        except OSError as exc:
            raise _error(ReasonCode.FOREIGN_LEASE, "lease-revalidate",
                         code=exc.errno) from None
        if (
            not stat.S_ISREG(path_info.st_mode)
            or (fd_info.st_dev, fd_info.st_ino) != (path_info.st_dev, path_info.st_ino)
        ):
            raise _error(ReasonCode.FOREIGN_LEASE, "lease-inode-changed")

    def assert_valid(self) -> None:
        self._revalidate_inode()
        if read_boot_id() != self.boot_id or socket.gethostname() != self.hostname:
            raise _error(ReasonCode.FOREIGN_LEASE, "lease-binding-changed")

    def release(self) -> None:
        if not self._released:
            self._released = True
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                os.close(self._directory_fd)

    def __enter__(self) -> "RepositoryLease":
        return self

    def __exit__(self, _kind: object, _value: object, _tb: object) -> None:
        self.release()


__all__ = [
    "BoottimeDeadline", "ControlLedger", "DiscoveredRun", "EVENT_TYPES", "MAX_WAL_BYTES",
    "MAX_WAL_LINE_BYTES", "Observation", "ReplaySnapshot", "RepositoryLease",
    "RuntimeLayout", "SideEffectIntent", "SignalRelay", "discover_runs",
    "read_boot_id", "replay_run", "validate_transition",
]
