#!/usr/bin/env python3
"""Durable compute-side recorder for the T-362 walltime signal probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time
from types import FrameType
from typing import Any, NoReturn
import uuid


SCHEMA = "t362-signal-event/v1"
MARKER_SCHEMA = "t362-signal-marker/v2"
ACK_SCHEMA = "t362-signal-observer/v2"
INVENTORY_SCHEMA = "t362-artifact-inventory/v1"
MODES = ("default", "split-warning", "mitigation")
ORIGINAL = b"ORIGINAL\n"
MUTATED = b"MUTATED\n"
HOST_RE = re.compile(r"^bnode[0-9]+(?:[.].*)?$")
REQUEST_ID_RE = re.compile(r"^(?:[0-9]+:)?[A-Za-z0-9][A-Za-z0-9._-]*$")
RUN_NONCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
STARTUP_DEADLINE_SECONDS = 30.0
_SEQUENCE = 0
_IDENTITY_CACHE: dict[Path, dict[str, str]] = {}


class ProbeError(RuntimeError):
    """Fail-closed probe setup or recording error."""


class SignalAbort(BaseException):
    """Match mutation_harness.SignalAbort's BaseException behavior."""

    def __init__(self, signum: int):
        super().__init__(signum)
        self.signum = signum


def _next_sequence() -> int:
    global _SEQUENCE
    _SEQUENCE += 1
    return _SEQUENCE


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_temporary(path: Path, payload: bytes) -> Path:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return temporary


def _atomic_publish(path: Path, payload: bytes) -> None:
    """Publish a one-shot artifact without replacing an existing producer."""

    temporary = _write_temporary(path, payload)
    try:
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
        _fsync_directory(path.parent)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _atomic_replace(path: Path, payload: bytes) -> None:
    """Durably replace the deliberately mutable canary."""

    temporary = _write_temporary(path, payload)
    try:
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_publish(
        path,
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"),
    )


def _durable_append(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    existed = path.exists()
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8", closefd=True) as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    if not existed:
        _fsync_directory(path.parent)


def _normalize_request_id(value: str) -> str:
    if not REQUEST_ID_RE.fullmatch(value):
        raise ProbeError(f"PBS request id is outside the closed grammar: {value!r}")
    return value.split(":", 1)[-1]


def _controller_run_nonce() -> str:
    nonce = os.environ.get("T362_RUN_NONCE", "")
    attempt_id = os.environ.get("T362_ATTEMPT_ID", "")
    if not RUN_NONCE_RE.fullmatch(nonce):
        raise ProbeError("T362_RUN_NONCE is outside the closed attempt-id grammar")
    if attempt_id != nonce:
        raise ProbeError("T362_ATTEMPT_ID and T362_RUN_NONCE must be identical")
    return nonce


def _inventory_path(run_root: Path) -> Path:
    return run_root / "artifact-inventory.jsonl"


def _register_artifact(path: Path, run_root: Path, *, purpose: str, cleanup: bool) -> None:
    try:
        relative = path.relative_to(run_root)
    except ValueError as exc:
        raise ProbeError(f"artifact is outside T362_RUN_ROOT: {path}") from exc
    if relative == Path("artifact-inventory.jsonl"):
        return
    _durable_append(
        _inventory_path(run_root),
        {
            "schema_version": INVENTORY_SCHEMA,
            "relative_path": relative.as_posix(),
            "purpose": purpose,
            "cleanup": cleanup,
            "producer": "compute",
            "pid": os.getpid(),
            "time_ns": time.time_ns(),
        },
    )


def _load_identity(run_root: Path, mode: str) -> dict[str, str]:
    cached = _IDENTITY_CACHE.get(run_root)
    if cached is not None:
        return cached
    marker_path = run_root / "run_marker.json"
    try:
        raw = marker_path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeError(f"cannot load compute identity: {exc}") from exc
    required = {
        "schema_version": MARKER_SCHEMA,
        "mode": mode,
    }
    if any(value.get(key) != expected for key, expected in required.items()):
        raise ProbeError("compute identity marker schema or mode mismatch")
    run_nonce = value.get("run_nonce")
    normalized = value.get("normalized_request_id")
    if run_nonce != _controller_run_nonce():
        raise ProbeError("compute identity run_nonce does not bind controller environment")
    if not isinstance(normalized, str) or normalized != _normalize_request_id(normalized):
        raise ProbeError("compute identity normalized_request_id is invalid")
    identity = {
        "run_nonce": run_nonce,
        "normalized_request_id": normalized,
        "compute_marker_sha256": hashlib.sha256(raw).hexdigest(),
    }
    _IDENTITY_CACHE[run_root] = identity
    return identity


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
        raise ProbeError("required environment is unset: " + ",".join(missing))
    run_root = Path(os.environ["T362_RUN_ROOT"])
    driver_root = Path(os.environ["T362_DRIVER_ROOT"])
    mode = os.environ["T362_MODE"]
    if mode not in MODES:
        raise ProbeError(f"invalid T362_MODE: {mode!r}")
    _controller_run_nonce()
    for label, path in (("T362_RUN_ROOT", run_root), ("T362_DRIVER_ROOT", driver_root)):
        if not path.is_absolute() or path.is_symlink() or not path.is_dir():
            raise ProbeError(f"{label} must be an existing absolute non-symlink directory")
    expected_driver = Path(__file__).resolve().parent
    if driver_root.resolve() != expected_driver:
        raise ProbeError("T362_DRIVER_ROOT does not identify this probe's driver directory")
    return run_root, driver_root, mode


def _checked_output_path(raw: str, run_root: Path) -> Path:
    path = Path(raw)
    if not path.is_absolute() or path.parent != run_root or path.is_symlink():
        raise ProbeError("append path must be a direct non-symlink child of T362_RUN_ROOT")
    return path


def _signal_number(name: str | None) -> int | None:
    if name is None:
        return None
    value = getattr(signal, name, None)
    if not isinstance(value, signal.Signals):
        raise ProbeError(f"unsupported signal name: {name}")
    return int(value)


def _event(mode: str, layer: str, event: str, **fields: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": SCHEMA,
        "event_id": uuid.uuid4().hex,
        "sequence": _next_sequence(),
        "mode": mode,
        "layer": layer,
        "event": event,
        "hostname": socket.gethostname(),
        "pbs_jobid": os.environ.get("PBS_JOBID", "UNKNOWN"),
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "pgid": os.getpgrp(),
        "sid": os.getsid(0),
        "monotonic_ns": time.monotonic_ns(),
        "time_ns": time.time_ns(),
    }
    value.update(fields)
    return value


def _append_named(
    path: Path, mode: str, layer: str, event: str, *, signal_name: str | None = None, **fields: Any
) -> None:
    identity = _load_identity(path.parent, mode)
    fields.update(identity)
    signum = _signal_number(signal_name)
    if signum is not None:
        fields.update(signal_name=signal_name, signal_number=signum)
    _durable_append(path, _event(mode, layer, event, **fields))


def _differences(mode: str) -> dict[str, Any]:
    return {
        "bash_trap_layer_retained": mode == "split-warning",
        "bash_topology_scope": (
            "diagnostic-only; production _job_script exec chain has no remaining Bash trap layer"
            if mode == "split-warning"
            else "no Bash trap layer remains after exec, matching the production launcher shape"
        ),
        "grandchild_scope": (
            "diagnostic TERM-resistant grandchild ignores catchable signals and continues heartbeats; "
            "this is not the production pytest exit behavior"
        ),
        "parent_non_abort_signal_scope": (
            "parent records HUP/QUIT/USR1/USR2 and continues for diagnostics; the production harness "
            "handler contract being reproduced is specifically INT/TERM ignore-then-SignalAbort"
        ),
        "canary_scope": (
            "small canary proves only that this finally path ran; restoration success MUST NOT be "
            "generalized to real mutation restoration"
        ),
        "cleanup_scope": (
            "reproduces TERM/wait-5/KILL/wait-5/restore/byte-check timing shape, but does not run "
            "the production mutation target or pycache purge"
        ),
        "mitigation_scope": (
            "positive control for --accept-sigterm=yes delivery and a T-360 mitigation candidate"
            if mode == "mitigation"
            else "not a delivery-positive-control configuration"
        ),
        "internal_total_deadline": "NOT_APPLIED: walltime overrun is the purpose of these legs",
    }


def run_bootstrap(layer: str) -> int:
    run_root, _driver_root, mode = _required_environment()
    hostname = socket.gethostname()
    if not HOST_RE.fullmatch(hostname):
        raise ProbeError(f"compute hostname is not a bnode: {hostname!r}")
    raw_pbs_jobid = os.environ.get("PBS_JOBID", "")
    normalized_request_id = _normalize_request_id(raw_pbs_jobid)
    run_nonce = _controller_run_nonce()
    marker = run_root / "run_marker.json"
    metadata = run_root / "run_metadata.json"
    inventory = _inventory_path(run_root)
    if marker.exists() or metadata.exists() or inventory.exists():
        raise ProbeError("stale run marker, metadata, or inventory already exists")
    control = run_root / f"control-{layer}.jsonl"
    events = run_root / f"events-{layer}.jsonl"
    heartbeats = run_root / f"heartbeats-{layer}.jsonl"
    for path, purpose, cleanup in (
        (marker, "compute identity marker retained for controller validation", False),
        (metadata, "compute runtime metadata", False),
        (control, f"{layer} control events", False),
        (events, f"{layer} signal events", False),
        (heartbeats, f"{layer} durable startup heartbeat", False),
    ):
        _register_artifact(path, run_root, purpose=purpose, cleanup=cleanup)
    signal_writer_failures = run_root / "signal-writer-failures.raw"
    if layer == "bash":
        _register_artifact(
            signal_writer_failures,
            run_root,
            purpose="durable Bash trap writer failure log",
            cleanup=False,
        )
    _atomic_json(
        marker,
        {
            "schema_version": MARKER_SCHEMA,
            "mode": mode,
            "hostname": hostname,
            "pbs_jobid": raw_pbs_jobid,
            "normalized_request_id": normalized_request_id,
            "run_nonce": run_nonce,
            "pid": os.getpid(),
            "monotonic_ns": time.monotonic_ns(),
            "time_ns": time.time_ns(),
        },
    )
    _load_identity(run_root, mode)
    _atomic_json(
        metadata,
        {
            "schema_version": MARKER_SCHEMA,
            "mode": mode,
            "hostname": hostname,
            "pbs_jobid": raw_pbs_jobid,
            "normalized_request_id": normalized_request_id,
            "run_nonce": run_nonce,
            "selected_interpreter": sys.executable,
            "python_version": sys.version,
            "path": os.environ.get("PATH", ""),
            "differences_from_production": _differences(mode),
        },
    )
    if layer == "bash":
        _atomic_publish(signal_writer_failures, b"")
    _append_named(control, mode, layer, "control_start", control_namespace=True)
    _append_named(control, mode, layer, "control_normal_exit", control_namespace=True)
    _append_named(events, mode, layer, "run_marker_persisted")
    _heartbeat(heartbeats, mode, layer, phase="bootstrap")
    return 0


def run_append(args: argparse.Namespace) -> int:
    run_root, _driver_root, mode = _required_environment()
    path = _checked_output_path(args.path, run_root)
    fields: dict[str, Any] = {}
    if args.detail is not None:
        fields["detail"] = args.detail
    _append_named(path, mode, args.layer, args.event, signal_name=args.signal, **fields)
    return 0


def _install_abort_handlers(event_path: Path, mode: str) -> dict[int, Any]:
    old_handlers: dict[int, Any] = {}

    def handler(signum: int, _frame: FrameType | None) -> NoReturn:
        for guarded in (signal.SIGINT, signal.SIGTERM):
            signal.signal(guarded, signal.SIG_IGN)
        _append_named(
            event_path,
            mode,
            "parent",
            "signal",
            signal_name=signal.Signals(signum).name,
            before_signal=False,
            after_signal=False,
        )
        raise SignalAbort(signum)

    def record_only_handler(signum: int, _frame: FrameType | None) -> None:
        _append_named(
            event_path,
            mode,
            "parent",
            "signal",
            signal_name=signal.Signals(signum).name,
            behavior="diagnostic record-only handler; parent continues",
        )

    for signum in (signal.SIGINT, signal.SIGTERM):
        old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, handler)
    for signum in (signal.SIGHUP, signal.SIGQUIT, signal.SIGUSR1, signal.SIGUSR2):
        old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, record_only_handler)
    return old_handlers


def _restore_handlers(old_handlers: dict[int, Any]) -> None:
    for signum, old_handler in old_handlers.items():
        signal.signal(signum, old_handler)


def _parent_control_self_test(run_root: Path, mode: str) -> None:
    control = run_root / "control-parent.jsonl"
    _append_named(control, mode, "parent", "control_start", control_namespace=True)
    handlers = _install_abort_handlers(control, mode)
    try:
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except SignalAbort as exc:
            _append_named(
                control,
                mode,
                "parent",
                "control_signal_caught",
                signal_name=signal.Signals(exc.signum).name,
                control_namespace=True,
            )
    finally:
        _restore_handlers(handlers)
    _append_named(control, mode, "parent", "control_normal_exit", control_namespace=True)


def _heartbeat(path: Path, mode: str, layer: str, **fields: Any) -> None:
    _append_named(path, mode, layer, "heartbeat", **fields)


def _wait_for_grandchild(run_root: Path, process: subprocess.Popen[bytes], mode: str) -> None:
    marker = run_root / "grandchild_started.json"
    heartbeats = run_root / "heartbeats-parent.jsonl"
    deadline = time.monotonic() + STARTUP_DEADLINE_SECONDS
    while not marker.is_file():
        if process.poll() is not None:
            raise ProbeError(f"grandchild exited before its start marker: rc={process.returncode}")
        if time.monotonic() >= deadline:
            raise ProbeError("grandchild start marker deadline expired")
        _heartbeat(heartbeats, mode, "parent", phase="waiting_grandchild")
        time.sleep(0.2)


def _wait_for_ack(run_root: Path, mode: str, process: subprocess.Popen[bytes]) -> None:
    acknowledgment = run_root / "canary_readback_ack.json"
    expected_hash = hashlib.sha256(MUTATED).hexdigest()
    identity = _load_identity(run_root, mode)
    heartbeats = run_root / "heartbeats-parent.jsonl"
    deadline = time.monotonic() + STARTUP_DEADLINE_SECONDS
    while not acknowledgment.is_file():
        if process.poll() is not None:
            raise ProbeError(f"grandchild exited while waiting for acknowledgment: rc={process.returncode}")
        if time.monotonic() >= deadline:
            raise ProbeError("login readback acknowledgment deadline expired")
        _heartbeat(heartbeats, mode, "parent", phase="waiting_login_readback_ack")
        time.sleep(0.2)
    try:
        value = json.loads(acknowledgment.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeError(f"cannot read canary acknowledgment: {exc}") from exc
    expected = {
        "schema_version": ACK_SCHEMA,
        "mode": mode,
        "canary_sha256": expected_hash,
        **identity,
    }
    if any(value.get(key) != expected_value for key, expected_value in expected.items()):
        raise ProbeError("canary acknowledgment identity or MUTATED byte binding mismatch")


def _stop_process_shape(process: subprocess.Popen[bytes], events: Path, mode: str) -> bool:
    if process.poll() is not None:
        _append_named(events, mode, "parent", "grandchild_already_stopped", returncode=process.returncode)
        return False
    term_started = time.monotonic_ns()
    try:
        os.killpg(process.pid, signal.SIGTERM)
        _append_named(events, mode, "parent", "cleanup_signal_sent", signal_name="SIGTERM")
        process.wait(timeout=5)
        _append_named(
            events,
            mode,
            "parent",
            "cleanup_term_wait_finished",
            waited_ns=time.monotonic_ns() - term_started,
            returncode=process.returncode,
        )
        return False
    except subprocess.TimeoutExpired:
        _append_named(
            events,
            mode,
            "parent",
            "cleanup_term_wait_timeout",
            waited_ns=time.monotonic_ns() - term_started,
            timeout_seconds=5,
        )
    except OSError as exc:
        _append_named(
            events,
            mode,
            "parent",
            "cleanup_sigterm_error",
            waited_ns=time.monotonic_ns() - term_started,
            error_type=type(exc).__name__,
        )
        return False
    kill_started = time.monotonic_ns()
    try:
        os.killpg(process.pid, signal.SIGKILL)
        _append_named(events, mode, "parent", "cleanup_signal_sent", signal_name="SIGKILL")
    except OSError as exc:
        _append_named(events, mode, "parent", "cleanup_sigkill_error", error_type=type(exc).__name__)
        return False
    try:
        process.wait(timeout=5)
        _append_named(
            events,
            mode,
            "parent",
            "cleanup_kill_wait_finished",
            waited_ns=time.monotonic_ns() - kill_started,
            returncode=process.returncode,
        )
        return True
    except subprocess.TimeoutExpired:
        _append_named(
            events,
            mode,
            "parent",
            "cleanup_kill_wait_incomplete",
            waited_ns=time.monotonic_ns() - kill_started,
        )
        return False


def run_parent() -> int:
    run_root, driver_root, mode = _required_environment()
    identity = _load_identity(run_root, mode)
    events = run_root / "events-parent.jsonl"
    heartbeats = run_root / "heartbeats-parent.jsonl"
    canary = run_root / "canary.txt"
    ready = run_root / "ready.json"
    grandchild_marker = run_root / "grandchild_started.json"
    acknowledgment = run_root / "canary_readback_ack.json"
    control = run_root / "control-parent.jsonl"
    for path, purpose, cleanup in (
        (events, "parent signal and cleanup events", False),
        (heartbeats, "parent durable heartbeats", False),
        (control, "parent signal-writer control", False),
        (canary, "mutable restoration canary", True),
        (ready, "ready identity marker", True),
        (grandchild_marker, "grandchild startup marker", True),
        (acknowledgment, "login readback acknowledgment", True),
    ):
        _register_artifact(path, run_root, purpose=purpose, cleanup=cleanup)
    for path in (canary, ready, grandchild_marker, acknowledgment):
        if path.exists() or path.is_symlink():
            raise ProbeError(f"stale runtime artifact exists: {path.name}")

    _parent_control_self_test(run_root, mode)
    old_handlers = _install_abort_handlers(events, mode)
    process: subprocess.Popen[bytes] | None = None
    mutation_applied = False
    cleanup_error: BaseException | None = None
    _append_named(events, mode, "parent", "parent_started", differences_from_production=_differences(mode))
    try:
        process = subprocess.Popen(
            [sys.executable, str(driver_root / "signal_probe.py"), "grandchild"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _append_named(events, mode, "parent", "grandchild_spawned", grandchild_pid=process.pid)
        _wait_for_grandchild(run_root, process, mode)

        _atomic_replace(canary, ORIGINAL)
        _atomic_replace(canary, MUTATED)
        mutation_applied = True
        mutated_readback = canary.read_bytes()
        _append_named(
            events,
            mode,
            "parent",
            "canary_mutated_persisted",
            canary_sha256=hashlib.sha256(mutated_readback).hexdigest(),
            byte_match=mutated_readback == MUTATED,
        )
        if mutated_readback != MUTATED:
            raise ProbeError("local canary readback did not match MUTATED bytes")

        _wait_for_ack(run_root, mode, process)
        if process.poll() is not None:
            raise ProbeError(f"grandchild was not alive immediately before ready: rc={process.returncode}")
        os.kill(process.pid, 0)
        _append_named(
            events,
            mode,
            "parent",
            "grandchild_alive_immediately_before_ready",
            grandchild_pid=process.pid,
        )
        _atomic_json(
            ready,
            {
                "schema_version": MARKER_SCHEMA,
                "mode": mode,
                **identity,
                "state": "READY_AFTER_LOGIN_READBACK_ACK",
                "canary_sha256": hashlib.sha256(MUTATED).hexdigest(),
                "monotonic_ns": time.monotonic_ns(),
                "time_ns": time.time_ns(),
            },
        )
        _append_named(events, mode, "parent", "ready_after_login_readback_ack")

        # Deliberately no internal total deadline: walltime termination is the measurement.
        while True:
            _heartbeat(heartbeats, mode, "parent", phase="measurement")
            time.sleep(1)
    except SignalAbort as exc:
        _append_named(
            events,
            mode,
            "parent",
            "signal_abort_caught",
            signal_name=signal.Signals(exc.signum).name,
        )
    except BaseException as exc:
        _append_named(events, mode, "parent", "parent_error", error_type=type(exc).__name__, detail=str(exc))
        cleanup_error = exc
    finally:
        _append_named(events, mode, "parent", "finally_enter")
        if process is not None:
            cleanup_shape_valid = _stop_process_shape(process, events, mode)
            if not cleanup_shape_valid and cleanup_error is None:
                cleanup_error = ProbeError("grandchild cleanup did not follow TERM-timeout-KILL-wait shape")
        byte_match: bool | None = None
        restored_hash: str | None = None
        if mutation_applied:
            try:
                _atomic_replace(canary, ORIGINAL)
                restored = canary.read_bytes()
                byte_match = restored == ORIGINAL
                restored_hash = hashlib.sha256(restored).hexdigest()
                _append_named(
                    events,
                    mode,
                    "parent",
                    "canary_restore_verified",
                    byte_match=byte_match,
                    canary_sha256=restored_hash,
                )
                if not byte_match:
                    cleanup_error = ProbeError("restored canary bytes do not match ORIGINAL")
            except BaseException as exc:
                _append_named(
                    events,
                    mode,
                    "parent",
                    "canary_restore_error",
                    error_type=type(exc).__name__,
                    detail=str(exc),
                )
                cleanup_error = exc
        _append_named(
            events,
            mode,
            "parent",
            "finally_exit",
            canary_byte_match=byte_match,
            canary_sha256=restored_hash,
        )
        _restore_handlers(old_handlers)
    if cleanup_error is not None:
        raise cleanup_error
    return 0


def run_grandchild() -> int:
    run_root, _driver_root, mode = _required_environment()
    identity = _load_identity(run_root, mode)
    events = run_root / "events-grandchild.jsonl"
    control = run_root / "control-grandchild.jsonl"
    heartbeats = run_root / "heartbeats-grandchild.jsonl"
    marker = run_root / "grandchild_started.json"
    for path, purpose, cleanup in (
        (events, "grandchild signal events", False),
        (control, "grandchild signal-writer control", False),
        (heartbeats, "grandchild durable heartbeats", False),
        (marker, "grandchild startup marker", True),
    ):
        _register_artifact(path, run_root, purpose=purpose, cleanup=cleanup)
    watched = {
        signal.SIGHUP,
        signal.SIGINT,
        signal.SIGQUIT,
        signal.SIGTERM,
        signal.SIGUSR1,
        signal.SIGUSR2,
    }
    signal.pthread_sigmask(signal.SIG_BLOCK, watched)

    _append_named(control, mode, "grandchild", "control_start", control_namespace=True)
    os.kill(os.getpid(), signal.SIGUSR2)
    control_signal = signal.sigtimedwait(watched, 1.0)
    if control_signal is None:
        raise ProbeError("grandchild control signal was not received")
    _append_named(
        control,
        mode,
        "grandchild",
        "signal",
        signal_name=signal.Signals(control_signal.si_signo).name,
        sender_pid=control_signal.si_pid,
        control_namespace=True,
    )
    _append_named(control, mode, "grandchild", "control_normal_exit", control_namespace=True)
    _append_named(
        events,
        mode,
        "grandchild",
        "grandchild_started",
        diagnostic_difference=(
            "TERM-resistant and catchable-signal-ignoring by design; not production pytest behavior"
        ),
    )
    _atomic_json(
        marker,
        {
            "schema_version": MARKER_SCHEMA,
            "mode": mode,
            **identity,
            "pid": os.getpid(),
            "pgid": os.getpgrp(),
            "sid": os.getsid(0),
            "monotonic_ns": time.monotonic_ns(),
            "time_ns": time.time_ns(),
        },
    )
    signal_seen = False
    while True:
        received = signal.sigtimedwait(watched, 0.2 if signal_seen else 1.0)
        if received is not None:
            signal_seen = True
            _append_named(
                events,
                mode,
                "grandchild",
                "signal",
                signal_name=signal.Signals(received.si_signo).name,
                sender_pid=received.si_pid,
                behavior="ignored after durable record; heartbeat continues",
            )
        _heartbeat(
            heartbeats,
            mode,
            "grandchild",
            signal_seen=signal_seen,
            behavior="continues_after_catchable_signal",
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap = subparsers.add_parser("bootstrap")
    bootstrap.add_argument("--layer", required=True, choices=("job-script", "bash"))
    append = subparsers.add_parser("append")
    append.add_argument("--path", required=True)
    append.add_argument("--layer", required=True, choices=("job-script", "bash", "parent", "grandchild"))
    append.add_argument("--event", required=True)
    append.add_argument("--signal")
    append.add_argument("--detail")
    subparsers.add_parser("parent")
    subparsers.add_parser("grandchild")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "bootstrap":
        return run_bootstrap(args.layer)
    if args.command == "append":
        return run_append(args)
    if args.command == "parent":
        return run_parent()
    if args.command == "grandchild":
        return run_grandchild()
    raise ProbeError(f"unknown command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProbeError as exc:
        print(f"signal probe failed closed: {exc}", file=sys.stderr)
        raise SystemExit(16) from exc
