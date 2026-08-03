#!/usr/bin/env python3
"""Bounded, fail-closed login-side observer for one T-362 request."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
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
MUTATED = b"MUTATED\n"
_REQUEST_ID_RE = re.compile(r"^(?:[0-9]+:)?[A-Za-z0-9][A-Za-z0-9._-]*$")
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


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_publish(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        temporary.unlink()
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


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None, bytes | None]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
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
        )

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
        _durable_append(self.events, value)

    def command(self, argv: list[str], purpose: str) -> dict[str, Any]:
        self.command_sequence += 1
        sequence = self.command_sequence
        started = time.monotonic_ns()
        try:
            result = subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
                check=False,
            )
            returncode, stdout, stderr = result.returncode, result.stdout, result.stderr
            timed_out, launch_error = False, None
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            timed_out, launch_error = True, "TimeoutExpired"
        except (FileNotFoundError, OSError) as exc:
            returncode, stdout, stderr = 127, "", str(exc)
            timed_out, launch_error = False, type(exc).__name__
        classification = _classification(returncode, stdout, stderr)
        if launch_error is not None and not timed_out:
            classification = "MISSING_COMMAND" if launch_error == "FileNotFoundError" else "OS_ERROR"
        stem = f"{sequence:04d}-{purpose}"
        stdout_path = self.raw_root / f"{stem}.stdout.raw"
        stderr_path = self.raw_root / f"{stem}.stderr.raw"
        self.register(stdout_path, purpose=f"{purpose} stdout", cleanup=False)
        self.register(stderr_path, purpose=f"{purpose} stderr", cleanup=False)
        _atomic_publish(stdout_path, stdout.encode("utf-8", errors="replace"))
        _atomic_publish(stderr_path, stderr.encode("utf-8", errors="replace"))
        value = {
            "argv": argv,
            "purpose": purpose,
            "sequence": sequence,
            "returncode": returncode,
            "classification": classification,
            "timed_out": timed_out,
            "launch_error": launch_error,
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

    def qstat(self, purpose: str, attempts: int = 3) -> dict[str, Any]:
        result = self.bounded_command(
            ["qstat", "-J", "-f", self.request_id],
            purpose,
            attempts=attempts,
            retry_seconds=1.0,
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
        value, error, raw = _read_json(path)
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
        try:
            payload = (self.run_root / "canary.txt").read_bytes()
        except FileNotFoundError:
            return
        except OSError as exc:
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
        )
        self.record("canary_mutated_readback_ack_persisted", canary_sha256=digest)

    def collect_scheduler_tail(self) -> dict[str, dict[str, Any]]:
        return {
            "qstat": self.qstat("final-qstat", attempts=3),
            "racctjob": self.bounded_command(
                ["racctjob", "-I", self.request_id],
                "final-racctjob",
                attempts=5,
                retry_seconds=2.0,
            ),
            "racctreq": self.bounded_command(
                ["racctreq", "-I", self.request_id],
                "final-racctreq",
                attempts=5,
                retry_seconds=2.0,
            ),
        }

    def _read_jsonl(self, relative: str) -> tuple[list[dict[str, Any]], list[str]]:
        path = self.run_root / relative
        errors: list[str] = []
        records: list[dict[str, Any]] = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            return [], [f"{relative}: {type(exc).__name__}: {exc}"]
        if not lines:
            errors.append(f"{relative}: empty")
        for index, line in enumerate(lines, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{relative}:{index}: JSONDecodeError: {exc}")
                continue
            if not isinstance(value, dict):
                errors.append(f"{relative}:{index}: not an object")
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
        return records, errors

    @staticmethod
    def _event_names(records: list[dict[str, Any]]) -> list[str]:
        return [value.get("event") for value in records if isinstance(value.get("event"), str)]

    def validate_layers(self) -> dict[str, Any]:
        launch_layer = "bash" if self.mode == "split-warning" else "job-script"
        layers = [launch_layer, "parent", "grandchild"]
        errors: list[str] = []
        signals: dict[str, list[str] | str] = {}
        event_records: dict[str, list[dict[str, Any]]] = {}
        for layer in layers:
            records, parse_errors = self._read_jsonl(f"events-{layer}.jsonl")
            event_records[layer] = records
            errors.extend(parse_errors)
            event_names = self._event_names(records)
            required_start = {
                launch_layer: "run_marker_persisted",
                "parent": "parent_started",
                "grandchild": "grandchild_started",
            }[layer]
            if required_start not in event_names:
                errors.append(f"events-{layer}.jsonl: required start event {required_start} missing")
            names = [
                value["signal_name"]
                for value in records
                if value.get("event") == "signal" and isinstance(value.get("signal_name"), str)
            ]
            signals[layer] = list(dict.fromkeys(names)) if names else "UNKNOWN"
            control, control_errors = self._read_jsonl(f"control-{layer}.jsonl")
            errors.extend(control_errors)
            control_names = self._event_names(control)
            if "control_start" not in control_names or "control_normal_exit" not in control_names:
                errors.append(f"control-{layer}.jsonl: incomplete D4 control")
            heartbeat, heartbeat_errors = self._read_jsonl(f"heartbeats-{layer}.jsonl")
            errors.extend(heartbeat_errors)
            if "heartbeat" not in self._event_names(heartbeat):
                errors.append(f"heartbeats-{layer}.jsonl: durable heartbeat missing")
        if self.mode == "split-warning":
            try:
                writer_failures = (self.run_root / "signal-writer-failures.raw").read_bytes()
            except OSError as exc:
                errors.append(f"signal-writer-failures.raw: {type(exc).__name__}: {exc}")
            else:
                if writer_failures:
                    errors.append("signal-writer-failures.raw is non-empty")
        return {
            "valid": not errors,
            "errors": errors,
            "signals": signals,
            "parent_events": event_records.get("parent", []),
            "required_layers": layers,
        }

    def validate_cleanup_order(self, parent_events: list[dict[str, Any]]) -> dict[str, Any]:
        errors: list[str] = []
        if any(value.get("event") == "grandchild_already_stopped" for value in parent_events):
            errors.append("grandchild_already_stopped shortcut observed")

        def find_after(event: str, start: int, *, signal_name: str | None = None) -> int:
            for index in range(start, len(parent_events)):
                value = parent_events[index]
                if value.get("event") == event and (
                    signal_name is None or value.get("signal_name") == signal_name
                ):
                    return index
            return -1

        ordered = [
            ("grandchild_alive_immediately_before_ready", None),
            ("ready_after_login_readback_ack", None),
            ("cleanup_signal_sent", "SIGTERM"),
            ("cleanup_term_wait_timeout", None),
            ("cleanup_signal_sent", "SIGKILL"),
            ("cleanup_kill_wait_finished", None),
            ("canary_restore_verified", None),
            ("finally_exit", None),
        ]
        cursor = 0
        matched: list[dict[str, Any]] = []
        for event, signal_name in ordered:
            index = find_after(event, cursor, signal_name=signal_name)
            if index < 0:
                errors.append(f"cleanup sequence missing {event}/{signal_name or '-'}")
                continue
            matched.append(parent_events[index])
            cursor = index + 1
        timeout = next(
            (value for value in matched if value.get("event") == "cleanup_term_wait_timeout"),
            None,
        )
        if timeout is None or not isinstance(timeout.get("waited_ns"), int) or timeout["waited_ns"] < MIN_TERM_WAIT_NS:
            errors.append("TERM TimeoutExpired wait was shorter than approximately five seconds")
        restored = next(
            (value for value in matched if value.get("event") == "canary_restore_verified"),
            None,
        )
        final = next((value for value in matched if value.get("event") == "finally_exit"), None)
        if restored is None or restored.get("byte_match") is not True:
            errors.append("canary restore byte verification absent or false")
        if final is None or final.get("canary_byte_match") is not True:
            errors.append("finally_exit byte verification absent or false")
        return {"valid": not errors, "errors": errors, "matched_events": matched}

    def validate_accounting(self, tail: dict[str, dict[str, Any]]) -> dict[str, Any]:
        errors: list[str] = []
        for name in ("racctjob", "racctreq"):
            result = tail[name]
            if result["classification"] != "OK":
                errors.append(f"{name} did not complete successfully: {result['classification']}")
            if not _qstat_mentions_request(result["stdout"], self.normalized_request_id):
                errors.append(f"{name} output does not bind the request id")
        combined = "\n".join(
            tail[name][stream]
            for name in ("qstat", "racctjob", "racctreq")
            for stream in ("stdout", "stderr")
        )
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
        return {
            "valid": not errors,
            "errors": errors,
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
                raw_inventory = inventory.read_bytes()
                lines = raw_inventory.decode("utf-8").splitlines()
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"{inventory.name} unreadable: {exc}")
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
        for path in self.run_root.rglob("*"):
            if not path.is_file() and not path.is_symlink():
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
        removed: list[str] = []
        for relative, value in sorted(deduplicated.items()):
            if value.get("cleanup") is not True:
                continue
            path = self.run_root / relative
            try:
                path.unlink()
                removed.append(relative)
            except FileNotFoundError:
                errors.append(f"cleanup target missing: {relative}")
            except OSError as exc:
                errors.append(f"cleanup failed {relative}: {type(exc).__name__}: {exc}")
        try:
            _fsync_directory(self.run_root)
        except OSError as exc:
            errors.append(f"run root fsync after cleanup failed: {exc}")
        remaining = sorted(relative for relative in removed if (self.run_root / relative).exists())
        if remaining:
            errors.append("cleanup targets remain: " + ",".join(remaining))
        receipt = {
            "schema_version": SCHEMA,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "inventory_sha256_before_cleanup": inventory_hashes,
            "inventory_record_count": len(records),
            "discovered_owned_files_before_cleanup": sorted(discovered),
            "removed": removed,
            "errors": errors,
            "time_ns": time.time_ns(),
        }
        _atomic_json(self.cleanup_receipt_path, receipt)
        return {"valid": not errors, **receipt}

    def write_final(self, value: dict[str, Any]) -> None:
        _atomic_json(self.final_path, value)

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
        initial = self.qstat("initial-visibility", attempts=3)
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
                    current = self.qstat("poll", attempts=3)
                    next_qstat = now + (1.0 if self.scheduler_run_seen else 5.0)
                    if current["classification"] == "PERMISSION":
                        terminal_reason, permission_error = "PERMISSION_ERROR", True
                        break
                    if current["classification"] in {"MISSING_COMMAND", "OS_ERROR"}:
                        terminal_reason = f"QSTAT_{current['classification']}"
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
                if execution_deadline is not None and now >= execution_deadline:
                    final_check = self.qstat("execution-deadline-recheck", attempts=3)
                    active_at_stop = final_check["state"] == "RUN"
                    terminal_reason = (
                        "EXECUTION_DEADLINE_REQUEST_STILL_RUN"
                        if active_at_stop
                        else "EXECUTION_DEADLINE_REQUEST_NOT_RUN"
                    )
                    break
                if execution_deadline is None and now >= queue_deadline:
                    transition = self.qstat("que-deadline-transition-recheck", attempts=3)
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
        layer_validation = self.validate_layers()
        cleanup_order = self.validate_cleanup_order(layer_validation["parent_events"])
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
            not active_at_stop
            and (qstat_terminal_end or qstat_visible_disappearance)
        )
        tail_classifications = {name: result["classification"] for name, result in tail.items()}
        identity_valid = (
            self.run_marker is not None
            and self.ready_marker is not None
            and not self.marker_errors
        )
        pre_cleanup_conditions = {
            "ready_identity_valid": identity_valid,
            "walltime_accounting_confirmed": accounting["valid"],
            "scheduler_terminal_non_run": terminal_non_run,
            "scheduler_terminal_state_conclusive": tail_qstat["classification"] == "OK",
            "all_required_layers_and_logs_valid": layer_validation["valid"],
            "signal_log_parse_error_free": not layer_validation["errors"],
            "cleanup_order_valid": cleanup_order["valid"],
            "permission_error_absent": not permission_error,
            "scheduler_tail_permission_error_absent": "PERMISSION" not in tail_classifications.values(),
            "scheduler_commands_present": not any(
                value in {"MISSING_COMMAND", "OS_ERROR"} for value in tail_classifications.values()
            ),
            "controller_qdel_not_required": terminal_reason != "QUE_DEADLINE_CONTROLLER_QDEL_REQUIRED",
        }
        cleanup_receipt = self.cleanup_inventory()
        acceptance_conditions = {
            **pre_cleanup_conditions,
            "artifact_inventory_cleanup_valid": cleanup_receipt["valid"],
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
            "valid_for_safety_conclusion": valid,
            "signal_observations": layer_validation["signals"],
            "signal_log_errors": layer_validation["errors"],
            "cleanup_order": cleanup_order,
            "accounting_confirmation": accounting,
            "cleanup_receipt_file": str(self.cleanup_receipt_path.relative_to(self.run_root)),
            "unobserved_signal_vocabulary": "UNKNOWN",
            "qwait_code_9_scope": (
                "resource-limit termination only; never evidence of the delivered signal kind"
            ),
            "diagnostic_scope": "raw observations and validity only; no safety verdict is embedded",
            "time_ns": time.time_ns(),
        }
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
