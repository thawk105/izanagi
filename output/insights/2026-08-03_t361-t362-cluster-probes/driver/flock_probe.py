#!/usr/bin/env python3
"""T-361 cross-node fcntl.flock probe.

The probe writes raw, fsync'd observations under T361_RUN_ROOT.  Its compute-side
result remains provisional until the login-side controller validates qstat -J -f
Execution Hosts.  Every later verdict must remain reconstructible from per-job
events, nodefile/mount snapshots, and per-attempt observation files.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import platform
import re
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "izanagi-t361-flock-probe/v1"
EVENT_SCHEMA = "izanagi-t361-flock-event/v1"
OBSERVATION_SCHEMA = "izanagi-t361-flock-observation/v1"
RESULT_SCHEMA = "izanagi-t361-flock-result/v1"
EXECUTION_HOST_VALIDATION = "PENDING_CONTROLLER_QSTAT_J_F_VALIDATION"
BARRIER_TIMEOUT_SECONDS = 120.0
TOTAL_DEADLINE_SECONDS = 180.0
POLL_SECONDS = 0.20
TRIALS = (0, 1, 2)
INFRA_RC = 16
PENDING_VALIDATION_RC = 17
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
MOUNT_ESCAPE = re.compile(rb"\\([0-7]{3})")


class Verdict:
    BLOCKED_EXPECTED = "BLOCKED_EXPECTED"
    ACQUIRED_SILENT_FAIL_OPEN = "ACQUIRED_SILENT_FAIL_OPEN"
    ERROR = "ERROR"
    INVALID_CONTROL = "INVALID_CONTROL"
    INFRA_ERROR = "INFRA_ERROR"
    MIXED = "MIXED"
    DANGEROUS_LOCALFLOCK = "DANGEROUS_LOCALFLOCK"
    PENDING_EXECUTION_HOST_VALIDATION = "PENDING_EXECUTION_HOST_VALIDATION"


class ProbeInfraError(RuntimeError):
    """An infrastructure or self-check failure; never a safe flock result."""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _new_publish_temporary(path: Path) -> Path:
    return path.parent / f".{path.name}.tmp.{os.getpid()}.{secrets.token_hex(24)}"


def _write_exclusive_bytes(
    path: Path, payload: bytes, *, temporary: Path | None = None
) -> None:
    """Durably publish *path* without a partial final name or replacement."""

    temporary = temporary or _new_publish_temporary(path)
    if temporary.parent != path.parent or temporary.exists() or temporary.is_symlink():
        raise ProbeInfraError(f"unsafe atomic-publish temporary path: {temporary}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.link(temporary, path, follow_symlinks=False)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists() or temporary.is_symlink():
            temporary.unlink()
        _fsync_directory(path.parent)


def _write_exclusive_json(
    path: Path, value: Any, *, temporary: Path | None = None
) -> None:
    _write_exclusive_bytes(path, _json_bytes(value), temporary=temporary)


def _append_jsonl(path: Path, value: Any) -> None:
    flags = os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        payload = _json_bytes(value)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short append")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProbeInfraError(f"unreadable or corrupt JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProbeInfraError(f"JSON object required: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ProbeInfraError(f"unreadable JSONL: {path}: {exc}") from exc
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line:
            raise ProbeInfraError(f"blank JSONL record: {path}:{line_number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProbeInfraError(
                f"corrupt JSONL: {path}:{line_number}: {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise ProbeInfraError(f"JSONL object required: {path}:{line_number}")
        records.append(value)
    return records


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_name(value: str, label: str) -> str:
    if not SAFE_COMPONENT.fullmatch(value):
        raise ProbeInfraError(f"unsafe {label}: {value!r}")
    return value


def _ensure_safe_directory(path: Path, label: str) -> Path:
    if ".." in path.parts:
        raise ProbeInfraError(f"{label} must not contain '..'")
    if not path.is_absolute() or not path.is_dir() or path.is_symlink():
        raise ProbeInfraError(f"{label} must be an existing absolute non-symlink dir")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.is_symlink():
            raise ProbeInfraError(f"{label} contains a symlink component: {current}")
    return path


def _ensure_subdirectory(parent: Path, name: str) -> Path:
    child = parent / name
    child.mkdir(mode=0o700, exist_ok=True)
    if not child.is_dir() or child.is_symlink():
        raise ProbeInfraError(f"unsafe runtime directory: {child}")
    return child


def _remaining_timeout(deadline_monotonic: float, label: str) -> float:
    remaining = deadline_monotonic - time.monotonic()
    if remaining <= 0:
        raise ProbeInfraError(f"deadline exhausted before {label}")
    return remaining


def _hostname_command(
    arguments: list[str], deadline_monotonic: float
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            arguments,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=_remaining_timeout(deadline_monotonic, "hostname subprocess"),
        )
    except subprocess.TimeoutExpired as exc:
        raise ProbeInfraError(
            f"hostname subprocess timed out and was reaped: {arguments!r}"
        ) from exc
    return {
        "argv": arguments,
        "returncode": completed.returncode,
        "stdout_raw": completed.stdout,
        "stderr_raw": completed.stderr,
    }


def _normalize_hostname(value: str) -> dict[str, str]:
    normalized = value.strip().rstrip(".").lower()
    return {
        "input": value,
        "fqdn_normalized": normalized,
        "short_normalized": normalized.split(".", 1)[0],
    }


def _host_snapshot(deadline_monotonic: float) -> dict[str, Any]:
    commands = {
        "hostname": _hostname_command(["hostname"], deadline_monotonic),
        "hostname_fqdn": _hostname_command(["hostname", "-f"], deadline_monotonic),
        "hostname_short": _hostname_command(["hostname", "-s"], deadline_monotonic),
    }
    raw_candidates = [socket.gethostname(), socket.getfqdn()]
    raw_candidates.extend(item["stdout_raw"] for item in commands.values())
    normalized = [_normalize_hostname(item) for item in raw_candidates if item.strip()]
    shorts = sorted({item["short_normalized"] for item in normalized})
    fqdns = sorted({item["fqdn_normalized"] for item in normalized})
    if len(shorts) != 1:
        raise ProbeInfraError(f"ambiguous local short hostname: {shorts}")
    return {
        "commands": commands,
        "socket_gethostname_raw": socket.gethostname(),
        "socket_getfqdn_raw": socket.getfqdn(),
        "normalized_candidates": normalized,
        "short_normalized": shorts[0],
        "fqdn_normalized": fqdns,
        "uname": list(platform.uname()),
    }


def _nodefile_entries(raw: bytes) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for token in raw.decode("utf-8", errors="surrogateescape").split():
        entries.append(_normalize_hostname(token))
    return entries


def _decode_mount_field(raw: bytes) -> str:
    decoded = MOUNT_ESCAPE.sub(lambda match: bytes([int(match.group(1), 8)]), raw)
    return decoded.decode("utf-8", errors="surrogateescape")


def _parse_mountinfo(raw: bytes) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for mount_order, raw_line in enumerate(raw.splitlines(keepends=True)):
        fields = raw_line.rstrip(b"\n").split()
        try:
            separator = fields.index(b"-")
        except ValueError as exc:
            raise ProbeInfraError("mountinfo line has no field separator") from exc
        if separator < 6 or len(fields) < separator + 4:
            raise ProbeInfraError("mountinfo line is structurally incomplete")
        mount_options = _decode_mount_field(fields[5]).split(",")
        super_options = _decode_mount_field(fields[separator + 3]).split(",")
        effective_options = sorted(set(mount_options + super_options))
        entries.append(
            {
                "raw_line_sha256": _sha256_bytes(raw_line),
                "mountinfo_order": mount_order,
                "mount_id": _decode_mount_field(fields[0]),
                "parent_id": _decode_mount_field(fields[1]),
                "major_minor": _decode_mount_field(fields[2]),
                "root": _decode_mount_field(fields[3]),
                "mountpoint": _decode_mount_field(fields[4]),
                "mount_options": mount_options,
                "optional_fields": [
                    _decode_mount_field(field) for field in fields[6:separator]
                ],
                "filesystem_type": _decode_mount_field(fields[separator + 1]),
                "source": _decode_mount_field(fields[separator + 2]),
                "super_options": super_options,
                "effective_options": effective_options,
                "has_flock": "flock" in effective_options,
                "has_localflock": "localflock" in effective_options,
            }
        )
    if not entries:
        raise ProbeInfraError("/proc/self/mountinfo contained no entries")
    return entries


def _deepest_mount(path: Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    absolute = Path(os.path.abspath(path))
    candidates = [
        entry
        for entry in entries
        if absolute.is_relative_to(Path(str(entry["mountpoint"])))
    ]
    if not candidates:
        raise ProbeInfraError(f"no effective mount found for lock path: {path}")
    return max(
        candidates,
        key=lambda entry: (
            len(Path(str(entry["mountpoint"])).parts),
            int(entry["mountinfo_order"]),
        ),
    )


def _mount_snapshot(
    lock_paths: dict[str, list[Path]],
) -> tuple[bytes, bytes, dict[str, Any]]:
    mountinfo_raw = Path("/proc/self/mountinfo").read_bytes()
    proc_mounts_raw = Path("/proc/mounts").read_bytes()
    entries = _parse_mountinfo(mountinfo_raw)
    resolved: dict[str, Any] = {}
    for filesystem, paths in lock_paths.items():
        path_entries = []
        for path in paths:
            entry = _deepest_mount(path, entries)
            path_entries.append({"lock_path": str(path), "effective_mount": entry})
        resolved[filesystem] = {
            "lock_paths": path_entries,
            "effective_mount_signatures": sorted(
                {
                    json.dumps(
                        {
                            "filesystem_type": item["effective_mount"]["filesystem_type"],
                            "source": item["effective_mount"]["source"],
                            "effective_options": item["effective_mount"]["effective_options"],
                        },
                        sort_keys=True,
                    )
                    for item in path_entries
                }
            ),
        }
    return mountinfo_raw, proc_mounts_raw, {
        "proc_self_mountinfo_sha256": _sha256_bytes(mountinfo_raw),
        "proc_mounts_sha256": _sha256_bytes(proc_mounts_raw),
        **resolved,
    }


def _fd_identity(descriptor: int) -> dict[str, int]:
    stat_result = os.fstat(descriptor)
    return {
        "pid": os.getpid(),
        "fd": descriptor,
        "st_dev": stat_result.st_dev,
        "st_ino": stat_result.st_ino,
        "st_mode": stat_result.st_mode,
        "st_nlink": stat_result.st_nlink,
        "st_uid": stat_result.st_uid,
        "st_gid": stat_result.st_gid,
        "st_size": stat_result.st_size,
    }


def _open_lock_stream(lock_path: Path) -> Any:
    descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_RDWR | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    return os.fdopen(descriptor, "a+", encoding="utf-8")


def _acquire_nonblocking(stream: Any) -> None:
    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _write_lock_nonce(stream: Any, lock_path: Path, nonce: str) -> dict[str, int]:
    before = _fd_identity(stream.fileno())
    if before["st_size"] != 0:
        raise ProbeInfraError(f"lock file was not fresh: {lock_path}")
    stream.write(nonce + "\n")
    stream.flush()
    os.fsync(stream.fileno())
    _fsync_directory(lock_path.parent)
    return _fd_identity(stream.fileno())


def _read_nonce_through_fd(descriptor: int) -> tuple[bytes, str]:
    raw = os.pread(descriptor, 4096, 0)
    return raw, raw.decode("utf-8", errors="surrogateescape").rstrip("\n")


def _attempt_lock(
    *,
    lock_path: Path,
    expected_nonce: str,
    binding: dict[str, Any],
    kind: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": OBSERVATION_SCHEMA,
        **binding,
        "kind": kind,
        "open_flags_contract": "O_CREAT|O_RDWR|O_APPEND|getattr(O_NOFOLLOW,0);mode=0600",
        "flock_contract": "fcntl.flock(fd, LOCK_EX|LOCK_NB)",
        "harness_compatibility_note": (
            "mutation_harness treats every flock OSError as lock contention; "
            "this probe preserves errno and separates BLOCKED from ERROR"
        ),
        "attempt_monotonic_ns": time.monotonic_ns(),
        "attempt_time_ns": time.time_ns(),
    }
    stream = None
    try:
        stream = _open_lock_stream(lock_path)
        raw_nonce, observed_nonce = _read_nonce_through_fd(stream.fileno())
        result["nonce_read_via"] = "os.pread(opened_fd, 4096, 0)"
        result["nonce_raw_sha256"] = _sha256_bytes(raw_nonce)
        result["observed_nonce"] = observed_nonce
        result["expected_nonce"] = expected_nonce
        result["nonce_matches"] = observed_nonce == expected_nonce
        result["fstat_immediately_before_attempt"] = _fd_identity(stream.fileno())
        try:
            _acquire_nonblocking(stream)
        except OSError as exc:
            blocked_errnos = {errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK}
            result["raw_errno"] = exc.errno
            result["raw_errno_name"] = errno.errorcode.get(exc.errno or -1, "UNKNOWN")
            result["raw_error_text"] = str(exc)
            result["outcome"] = "BLOCKED" if exc.errno in blocked_errnos else "ERROR"
            result["harness_classification"] = "HARNESS_WOULD_REPORT_LOCK_CONTENTION"
        else:
            result["outcome"] = "ACQUIRED"
            result["raw_errno"] = None
            result["raw_errno_name"] = None
            result["raw_error_text"] = None
            result["harness_classification"] = "HARNESS_WOULD_ACQUIRE"
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        result["fstat_immediately_after_attempt"] = _fd_identity(stream.fileno())
    except OSError as exc:
        result["outcome"] = "ERROR"
        result["raw_errno"] = exc.errno
        result["raw_errno_name"] = errno.errorcode.get(exc.errno or -1, "UNKNOWN")
        result["raw_error_text"] = str(exc)
        result["harness_classification"] = "HARNESS_OPEN_ERROR"
    finally:
        if stream is not None:
            stream.close()
    result["completed_monotonic_ns"] = time.monotonic_ns()
    result["completed_time_ns"] = time.time_ns()
    return result


class RunContext:
    def __init__(self) -> None:
        self.started_monotonic = time.monotonic()
        self.total_deadline_monotonic = self.started_monotonic + TOTAL_DEADLINE_SECONDS
        self.run_root = _ensure_safe_directory(
            Path(os.environ["T361_RUN_ROOT"]), "T361_RUN_ROOT"
        )
        self.home_root = _ensure_safe_directory(
            Path(os.environ["T361_HOME_ROOT"]), "T361_HOME_ROOT"
        )
        self.driver_root = _ensure_safe_directory(
            Path(os.environ["T361_DRIVER_ROOT"]), "T361_DRIVER_ROOT"
        )
        if not self.run_root.is_relative_to(Path("/work")):
            raise ProbeInfraError("T361_RUN_ROOT must be below /work")
        if not self.home_root.is_relative_to(Path("/home")):
            raise ProbeInfraError("T361_HOME_ROOT must be below /home")
        run_nonce_source = os.environ.get("T361_RUN_NONCE", self.run_root.name)
        self.run_nonce = _safe_name(run_nonce_source, "run nonce")
        self.recon_only = os.environ.get("T361_RECON_ONLY", "0") == "1"
        self.pbs_jobid = _safe_name(os.environ.get("PBS_JOBID", ""), "PBS_JOBID")
        self.nodefile_path = Path(os.environ.get("PBS_NODEFILE", ""))
        if (
            not self.nodefile_path.is_absolute()
            or not self.nodefile_path.is_file()
            or self.nodefile_path.is_symlink()
        ):
            raise ProbeInfraError("PBS_NODEFILE is not a safe absolute regular file")
        self.process_nonce = secrets.token_hex(24)
        try:
            self.host = _host_snapshot(self.total_deadline_monotonic)
        except (OSError, ProbeInfraError, subprocess.SubprocessError) as exc:
            bootstrap_error_path = (
                self.run_root / f"infra-error.bootstrap.{self.process_nonce}.json"
            )
            try:
                _write_exclusive_json(
                    bootstrap_error_path,
                    {
                        "schema": RESULT_SCHEMA,
                        "run_nonce": self.run_nonce,
                        "pbs_jobid_raw": self.pbs_jobid,
                        "pid": os.getpid(),
                        "process_nonce": self.process_nonce,
                        "verdict": Verdict.INFRA_ERROR,
                        "valid_for_safety_conclusion": False,
                        "dangerous": None,
                        "exception_type": type(exc).__name__,
                        "error": str(exc),
                        "evidence_scope": "bootstrap before per-process inventory creation",
                    },
                )
            except OSError as evidence_exc:
                raise ProbeInfraError(
                    f"hostname probe failed ({exc}); durable bootstrap evidence also "
                    f"failed ({evidence_exc})"
                ) from exc
            raise
        self.job_token = hashlib.sha256(
            _json_bytes(
                {
                    "pbs_jobid_raw": self.pbs_jobid,
                    "hostname_short_normalized": self.host["short_normalized"],
                    "pid": os.getpid(),
                    "process_nonce": self.process_nonce,
                }
            )
        ).hexdigest()[:20]
        self.logical_token = "UNASSIGNED_UNTIL_TWO_MARKERS_ARE_VALIDATED"
        self.role = "unassigned"
        self.recon_dir = _ensure_subdirectory(self.run_root, "recon")
        self.nodefile_dir = _ensure_subdirectory(self.recon_dir, "nodefiles")
        self.mount_dir = _ensure_subdirectory(self.recon_dir, "mounts")
        self.marker_dir = _ensure_subdirectory(self.recon_dir, "job-markers")
        if self.recon_only:
            # Recon mode intentionally creates only marker/nodefile/mount evidence.
            self.event_dir = self.run_root / "events"
            self.observation_dir = self.run_root / "observations"
            self.coord_dir = self.run_root / "coord-transient"
            self.work_lock_dir = self.run_root / "locks-transient"
            self.home_lock_dir = self.home_root / "locks-transient"
            self.inventory_dir = self.run_root / "artifact-inventory"
            self.event_path: Path | None = None
            self.inventory_path: Path | None = None
        else:
            self.event_dir = _ensure_subdirectory(self.run_root, "events")
            self.observation_dir = _ensure_subdirectory(self.run_root, "observations")
            self.coord_dir = _ensure_subdirectory(self.run_root, "coord-transient")
            self.work_lock_dir = _ensure_subdirectory(self.run_root, "locks-transient")
            self.home_lock_dir = _ensure_subdirectory(self.home_root, "locks-transient")
            self.inventory_dir = _ensure_subdirectory(self.run_root, "artifact-inventory")
            self.event_path = self.event_dir / f"events.{self.process_nonce}.jsonl"
            self.inventory_path = (
                self.inventory_dir / f"inventory.{self.process_nonce}.jsonl"
            )
            _write_exclusive_bytes(self.inventory_path, b"")
            self.inventory(
                self.inventory_path,
                "artifact-inventory",
                False,
                lifecycle="published",
            )
            self.publish_bytes(
                self.event_path, b"", "durable-event-log", False
            )
        self.sequence = 0
        self.markers: list[dict[str, Any]] = []
        self.marker_by_token: dict[str, dict[str, Any]] = {}

    def binding(
        self, filesystem: str, trial: int | str, path: Path
    ) -> dict[str, Any]:
        return {
            "run_nonce": self.run_nonce,
            "filesystem": filesystem,
            "trial": trial,
            "path": str(path),
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "fd_identity": None,
            "pbs_jobid_raw": self.pbs_jobid,
            "job_token": self.job_token,
            "process_nonce": self.process_nonce,
            "logical_token": self.logical_token,
            "hostname_short_normalized": self.host["short_normalized"],
            "hostname_fqdn_normalized": self.host["fqdn_normalized"],
        }

    def event(
        self,
        name: str,
        *,
        filesystem: str = "__run__",
        trial: int | str = -1,
        path: Path | None = None,
        **details: Any,
    ) -> None:
        if self.recon_only:
            return
        if self.event_path is None:
            raise ProbeInfraError("event path is unavailable")
        self.sequence += 1
        value = {
            "schema": EVENT_SCHEMA,
            **self.binding(filesystem, trial, path or self.run_root),
            "event_sequence": self.sequence,
            "event": name,
            "role": self.role,
            "fd_identity": details.pop("fd_identity", None),
            "monotonic_ns": time.monotonic_ns(),
            "time_ns": time.time_ns(),
            **details,
        }
        _append_jsonl(self.event_path, value)

    def inventory(
        self,
        path: Path,
        artifact_kind: str,
        transient: bool,
        *,
        lifecycle: str = "planned",
    ) -> None:
        if self.recon_only:
            return
        if self.inventory_path is None:
            raise ProbeInfraError("inventory path is unavailable")
        _append_jsonl(
            self.inventory_path,
            {
                "schema": SCHEMA,
                **self.binding("__run__", -1, path),
                "artifact_kind": artifact_kind,
                "transient": transient,
                "lifecycle": lifecycle,
                "time_ns": time.time_ns(),
            },
        )

    def publish_bytes(
        self, path: Path, payload: bytes, artifact_kind: str, transient: bool
    ) -> None:
        temporary = self.plan_publish(path, artifact_kind, transient)
        _write_exclusive_bytes(path, payload, temporary=temporary)
        self.complete_publish(path, temporary, artifact_kind, transient)

    def plan_publish(
        self, path: Path, artifact_kind: str, transient: bool
    ) -> Path:
        temporary = _new_publish_temporary(path)
        self.inventory(temporary, "atomic-publish-temp", True)
        self.inventory(path, artifact_kind, transient)
        return temporary

    def complete_publish(
        self,
        path: Path,
        temporary: Path,
        artifact_kind: str,
        transient: bool,
    ) -> None:
        self.inventory(path, artifact_kind, transient, lifecycle="published")
        self.inventory(
            temporary, "atomic-publish-temp", True, lifecycle="removed"
        )

    def publish_json(
        self, path: Path, value: Any, artifact_kind: str, transient: bool
    ) -> None:
        self.publish_bytes(path, _json_bytes(value), artifact_kind, transient)

    def register_published(
        self, path: Path, artifact_kind: str, transient: bool
    ) -> None:
        self.inventory(path, artifact_kind, transient, lifecycle="published")

    def lock_paths_for_mount_resolution(self) -> dict[str, list[Path]]:
        return {
            "work": [
                self.work_lock_dir / "long-hold.lock",
                self.work_lock_dir / f"control.{self.process_nonce}.lock",
                *(self.work_lock_dir / f"cross.trial-{trial}.lock" for trial in TRIALS),
            ],
            "home": [
                self.home_lock_dir / "long-hold.lock",
                self.home_lock_dir / f"control.{self.process_nonce}.lock",
                *(self.home_lock_dir / f"cross.trial-{trial}.lock" for trial in TRIALS),
            ],
        }

    def observation_path(self, label: str) -> Path:
        return self.observation_dir / f"{_safe_name(label, 'observation')}.json"

    def write_observation(self, label: str, value: dict[str, Any]) -> Path:
        path = self.observation_path(label)
        self.publish_json(path, value, "raw-observation", False)
        return path

    def coord_path(self, label: str, token: str) -> Path:
        return self.coord_dir / f"{_safe_name(label, 'barrier label')}.{token}.json"

    def write_coord(self, label: str, value: dict[str, Any]) -> Path:
        path = self.coord_path(label, self.job_token)
        payload = {
            "schema": SCHEMA,
            **self.binding("__coord__", label, path),
            "role": self.role,
            **value,
        }
        self.publish_json(path, payload, "barrier-marker", True)
        return path

    def wait_coord(self, label: str, tokens: Iterable[str]) -> list[dict[str, Any]]:
        token_list = list(tokens)
        deadline = min(
            time.monotonic() + BARRIER_TIMEOUT_SECONDS,
            self.total_deadline_monotonic,
        )
        paths = [self.coord_path(label, token) for token in token_list]
        while time.monotonic() < deadline:
            if all(path.is_file() and not path.is_symlink() for path in paths):
                return [_read_json(path) for path in paths]
            time.sleep(POLL_SECONDS)
        missing = [str(path) for path in paths if not path.is_file()]
        self.event(
            "barrier_timeout",
            filesystem="__coord__",
            trial=label,
            path=self.coord_dir,
            timeout_seconds=BARRIER_TIMEOUT_SECONDS,
            missing=missing,
            verdict=Verdict.INFRA_ERROR,
        )
        raise ProbeInfraError(f"barrier timeout ({BARRIER_TIMEOUT_SECONDS}s): {label}")

    def check_total_deadline(self, label: str) -> None:
        if time.monotonic() >= self.total_deadline_monotonic:
            self.event(
                "total_deadline_exceeded",
                filesystem="__run__",
                trial=label,
                path=self.run_root,
                total_deadline_seconds=TOTAL_DEADLINE_SECONDS,
                verdict=Verdict.INFRA_ERROR,
            )
            raise ProbeInfraError(
                f"internal total deadline exceeded ({TOTAL_DEADLINE_SECONDS}s): {label}"
            )

    def barrier(self, label: str) -> None:
        self.write_coord(label, {"kind": "two-job-barrier"})
        self.wait_coord(label, sorted(self.marker_by_token))


def _create_recon_evidence(ctx: RunContext) -> dict[str, Any]:
    nodefile_raw = ctx.nodefile_path.read_bytes()
    mountinfo_raw, proc_mounts_raw, mount_parsed = _mount_snapshot(
        ctx.lock_paths_for_mount_resolution()
    )
    nodefile_path = ctx.nodefile_dir / f"nodefile.{ctx.process_nonce}.raw"
    mountinfo_path = (
        ctx.mount_dir / f"proc-self-mountinfo.{ctx.process_nonce}.raw"
    )
    proc_mounts_path = ctx.mount_dir / f"proc-mounts.{ctx.process_nonce}.raw"
    ctx.publish_bytes(nodefile_path, nodefile_raw, "pbs-nodefile-raw", False)
    ctx.publish_bytes(
        mountinfo_path, mountinfo_raw, "proc-self-mountinfo-raw", False
    )
    ctx.publish_bytes(proc_mounts_path, proc_mounts_raw, "proc-mounts-raw", False)
    marker = {
        "schema": SCHEMA,
        **ctx.binding("__recon__", -1, ctx.run_root),
        "physical_identity": {
            "process_nonce": ctx.process_nonce,
            "pbs_jobid_raw": ctx.pbs_jobid,
            "hostname_short_normalized": ctx.host["short_normalized"],
            "pid": os.getpid(),
        },
        "marker_publish_contract": "temp -> fsync -> link(no-replace) -> dir fsync",
        "host": ctx.host,
        "pbs_environment_raw": {
            name: os.environ.get(name)
            for name in (
                "PBS_JOBID",
                "PBS_SUBREQNO",
                "PBS_NODEFILE",
                "PBS_JOBNAME",
                "PBS_O_HOST",
                "PBS_O_HOME",
                "PBS_O_WORKDIR",
                "NQSV_JOBID",
            )
        },
        "nodefile": {
            "source_path_raw": str(ctx.nodefile_path),
            "saved_path": str(nodefile_path),
            "raw_sha256": _sha256_bytes(nodefile_raw),
            "raw_size": len(nodefile_raw),
            "normalized_entries": _nodefile_entries(nodefile_raw),
        },
        "mounts": {
            **mount_parsed,
            "saved_mountinfo_raw_path": str(mountinfo_path),
            "saved_proc_mounts_raw_path": str(proc_mounts_path),
            "mountinfo_raw_size": len(mountinfo_raw),
            "proc_mounts_raw_size": len(proc_mounts_raw),
        },
        "python": {
            "executable": sys.executable,
            "version": list(sys.version_info),
            "path_env_raw": os.environ.get("PATH"),
        },
        "scope_limitations": [
            "This run measures the Lustre flock primitive, not the unfrozen T-360 lock contract.",
            "The long-hold leg spans recon through all trials within one five-minute job only.",
            "It does not reproduce a multi-hour mutation-harness lock lifetime.",
            "Any result is limited to the exact host pair, kernel, and effective mounts recorded here.",
        ],
    }
    marker_path = ctx.marker_dir / f"marker.{ctx.process_nonce}.json"
    ctx.publish_json(marker_path, marker, "compute-job-marker", False)
    return marker


def _wait_and_validate_recon(ctx: RunContext) -> tuple[str, str]:
    deadline = min(
        time.monotonic() + BARRIER_TIMEOUT_SECONDS,
        ctx.total_deadline_monotonic,
    )
    paths: list[Path] = []
    while time.monotonic() < deadline:
        paths = sorted(ctx.marker_dir.glob("marker.*.json"))
        if len(paths) > 2:
            raise ProbeInfraError(f"more than two job markers: {len(paths)}")
        if len(paths) == 2:
            break
        time.sleep(POLL_SECONDS)
    if len(paths) != 2:
        ctx.event(
            "job_marker_timeout",
            filesystem="__recon__",
            trial=-1,
            path=ctx.marker_dir,
            timeout_seconds=BARRIER_TIMEOUT_SECONDS,
            marker_count=len(paths),
            verdict=Verdict.INFRA_ERROR,
        )
        raise ProbeInfraError("job missing: exactly two O_EXCL markers were not observed")
    markers = [_read_json(path) for path in paths]
    for marker in markers:
        physical_identity = marker.get("physical_identity")
        if not isinstance(physical_identity, dict):
            raise ProbeInfraError("marker lacks physical identity binding")
        if (
            physical_identity.get("process_nonce") != marker.get("process_nonce")
            or physical_identity.get("pbs_jobid_raw") != marker.get("pbs_jobid_raw")
            or physical_identity.get("hostname_short_normalized")
            != marker.get("hostname_short_normalized")
            or physical_identity.get("pid") != marker.get("pid")
        ):
            raise ProbeInfraError("marker physical identity fields are inconsistent")
    tokens = [str(marker.get("job_token")) for marker in markers]
    if len(set(tokens)) != 2 or ctx.job_token not in tokens:
        raise ProbeInfraError(f"invalid job marker identity set: {tokens}")
    shorts = [str(marker["host"]["short_normalized"]) for marker in markers]
    if len(set(shorts)) != 2:
        raise ProbeInfraError(f"same-host placement is invalid: {shorts}")
    nodefile_hashes = {marker["nodefile"]["raw_sha256"] for marker in markers}
    if len(nodefile_hashes) != 1:
        raise ProbeInfraError("the two raw PBS_NODEFILE byte streams differ")
    marker_hosts = set(shorts)
    for marker in markers:
        entries = marker["nodefile"]["normalized_entries"]
        nodefile_hosts = {str(item["short_normalized"]) for item in entries}
        if nodefile_hosts != marker_hosts:
            raise ProbeInfraError(
                f"normalized nodefile hosts {sorted(nodefile_hosts)} != markers {sorted(marker_hosts)}"
            )
        for filesystem in ("work", "home"):
            mount_data = marker["mounts"].get(filesystem)
            if not isinstance(mount_data, dict) or not mount_data.get("lock_paths"):
                raise ProbeInfraError(
                    f"missing effective mount resolution for /{filesystem} lock paths"
                )
    ordered = sorted(markers, key=lambda item: (item["host"]["short_normalized"], item["job_token"]))
    holder_token = str(ordered[0]["job_token"])
    contender_token = str(ordered[1]["job_token"])
    ctx.markers = markers
    ctx.marker_by_token = {str(marker["job_token"]): marker for marker in markers}
    logical_tokens = {holder_token: "logical-job-0", contender_token: "logical-job-1"}
    ctx.logical_token = logical_tokens[ctx.job_token]
    ctx.role = "holder" if ctx.job_token == holder_token else "contender"
    ctx.event(
        "recon_validated",
        filesystem="__recon__",
        trial=-1,
        path=ctx.marker_dir,
        raw_nodefile_sha256=next(iter(nodefile_hashes)),
        exact_host_pair=sorted(marker_hosts),
        holder_token=holder_token,
        contender_token=contender_token,
        logical_tokens_by_physical_token=logical_tokens,
        qstat_execution_host_comparison=EXECUTION_HOST_VALIDATION,
    )
    return holder_token, contender_token


def _child_binding(
    ctx: RunContext, filesystem: str, trial: int | str, path: Path
) -> dict[str, Any]:
    return ctx.binding(filesystem, trial, path)


def _run_try_child(
    ctx: RunContext,
    *,
    filesystem: str,
    trial: int | str,
    path: Path,
    expected_nonce: str,
    kind: str,
    label: str,
) -> dict[str, Any]:
    output = ctx.observation_path(label)
    output_temporary = ctx.plan_publish(output, "raw-lock-attempt", False)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "try-lock",
        "--run-nonce",
        ctx.run_nonce,
        "--job-token",
        ctx.job_token,
        "--process-nonce",
        ctx.process_nonce,
        "--filesystem",
        filesystem,
        "--trial",
        str(trial),
        "--path",
        str(path),
        "--expected-nonce",
        expected_nonce,
        "--kind",
        kind,
        "--output",
        str(output),
        "--output-temporary",
        str(output_temporary),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            timeout=_remaining_timeout(
                ctx.total_deadline_monotonic, f"try-lock helper {label}"
            ),
        )
    except subprocess.TimeoutExpired as exc:
        raise ProbeInfraError(
            f"try-lock helper timed out and was reaped: {label}"
        ) from exc
    if completed.returncode != 0 or not output.is_file() or output.is_symlink():
        raise ProbeInfraError(
            f"try-lock helper failed rc={completed.returncode}: {label}"
        )
    ctx.complete_publish(
        output, output_temporary, "raw-lock-attempt", False
    )
    result = _read_json(output)
    ctx.event(
        "lock_attempt_recorded",
        filesystem=filesystem,
        trial=trial,
        path=path,
        observation_path=str(output),
        observation_sha256=_sha256_bytes(output.read_bytes()),
        kind=kind,
        outcome=result.get("outcome"),
        raw_errno=result.get("raw_errno"),
    )
    return result


def _new_locked_file(path: Path, nonce: str) -> Any:
    if path.exists() or path.is_symlink():
        raise ProbeInfraError(f"fresh lock path already exists: {path}")
    stream = _open_lock_stream(path)
    try:
        _acquire_nonblocking(stream)
        _write_lock_nonce(stream, path, nonce)
    except BaseException:
        stream.close()
        raise
    return stream


def _run_local_controls(ctx: RunContext, filesystem: str, lock_dir: Path) -> None:
    path = lock_dir / f"control.{ctx.process_nonce}.lock"
    nonce = secrets.token_hex(24)
    ctx.inventory(path, "control-lock", True)
    stream = _new_locked_file(path, nonce)
    ctx.register_published(path, "control-lock", True)
    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    stream.close()
    _run_try_child(
        ctx,
        filesystem=filesystem,
        trial="control",
        path=path,
        expected_nonce=nonce,
        kind="unlocked_control",
        label=f"control-unlocked-{filesystem}-{ctx.job_token}",
    )
    holder = _open_lock_stream(path)
    _acquire_nonblocking(holder)
    raw_nonce, observed_nonce = _read_nonce_through_fd(holder.fileno())
    before = _fd_identity(holder.fileno())
    blocked = _run_try_child(
        ctx,
        filesystem=filesystem,
        trial="control",
        path=path,
        expected_nonce=nonce,
        kind="same_node_block_control",
        label=f"control-blocked-{filesystem}-{ctx.job_token}",
    )
    after = _fd_identity(holder.fileno())
    witness = {
        "schema": OBSERVATION_SCHEMA,
        **ctx.binding(filesystem, "control", path),
        "kind": "same_node_holder_witness",
        "holder_nonce": nonce,
        "nonce_read_via": "os.pread(opened_fd, 4096, 0)",
        "nonce_raw_sha256": _sha256_bytes(raw_nonce),
        "nonce_matches": observed_nonce == nonce,
        "fstat_immediately_before_attempt": before,
        "fstat_immediately_after_attempt": after,
        "child_pid": blocked.get("pid"),
        "child_outcome": blocked.get("outcome"),
    }
    ctx.write_observation(f"control-witness-{filesystem}-{ctx.job_token}", witness)
    fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
    holder.close()


def _perform_cross_trial(
    ctx: RunContext,
    *,
    filesystem: str,
    trial: int,
    lock_dir: Path,
    holder_token: str,
    contender_token: str,
) -> None:
    path = lock_dir / f"cross.trial-{trial}.lock"
    base = f"cross-{filesystem}-{trial}"
    if ctx.role == "holder":
        nonce = secrets.token_hex(24)
        ctx.inventory(path, "cross-node-lock", True)
        holder = _new_locked_file(path, nonce)
        ctx.register_published(path, "cross-node-lock", True)
        ready_identity = _fd_identity(holder.fileno())
        ctx.write_coord(
            f"{base}-holder-ready",
            {"nonce": nonce, "holder_fstat": ready_identity, "lock_path": str(path)},
        )
        ctx.wait_coord(f"{base}-about-to-try", [contender_token])
        before = _fd_identity(holder.fileno())
        ctx.write_coord(
            f"{base}-holder-pre-ack", {"holder_fstat_immediately_before": before}
        )
        done = ctx.wait_coord(f"{base}-attempt-done", [contender_token])[0]
        after = _fd_identity(holder.fileno())
        witness = {
            "schema": OBSERVATION_SCHEMA,
            **ctx.binding(filesystem, trial, path),
            "kind": "cross_holder_witness",
            "holder_nonce": nonce,
            "holder_ready_fstat": ready_identity,
            "fstat_immediately_before_attempt": before,
            "fstat_immediately_after_attempt": after,
            "contender_observation_path": done.get("observation_path"),
            "fd_remained_open_until_attempt_done": True,
        }
        ctx.write_observation(f"{base}-holder-witness", witness)
        fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
        holder.close()
        ctx.write_coord(f"{base}-holder-released", {"released": True})
        ctx.wait_coord(f"{base}-post-release-done", [contender_token])
    else:
        ready = ctx.wait_coord(f"{base}-holder-ready", [holder_token])[0]
        if ready.get("lock_path") != str(path):
            raise ProbeInfraError("holder and contender derived different cross lock paths")
        nonce = str(ready["nonce"])
        ctx.write_coord(f"{base}-about-to-try", {"lock_path": str(path)})
        ctx.wait_coord(f"{base}-holder-pre-ack", [holder_token])
        attempt = _run_try_child(
            ctx,
            filesystem=filesystem,
            trial=trial,
            path=path,
            expected_nonce=nonce,
            kind="cross_node_attempt",
            label=f"{base}-attempt-{ctx.job_token}",
        )
        attempt_path = ctx.observation_path(f"{base}-attempt-{ctx.job_token}")
        ctx.write_coord(
            f"{base}-attempt-done",
            {
                "observation_path": str(attempt_path),
                "observation_sha256": _sha256_bytes(attempt_path.read_bytes()),
                "outcome": attempt.get("outcome"),
            },
        )
        ctx.wait_coord(f"{base}-holder-released", [holder_token])
        post = _run_try_child(
            ctx,
            filesystem=filesystem,
            trial=trial,
            path=path,
            expected_nonce=nonce,
            kind="cross_node_post_release_control",
            label=f"{base}-post-release-{ctx.job_token}",
        )
        post_path = ctx.observation_path(f"{base}-post-release-{ctx.job_token}")
        ctx.write_coord(
            f"{base}-post-release-done",
            {
                "observation_path": str(post_path),
                "observation_sha256": _sha256_bytes(post_path.read_bytes()),
                "outcome": post.get("outcome"),
            },
        )
    ctx.barrier(f"{base}-complete")


def _perform_long_hold_attempt(
    ctx: RunContext,
    *,
    filesystem: str,
    trial: int,
    path: Path,
    holder_stream: Any | None,
    nonce: str,
    holder_token: str,
    contender_token: str,
) -> None:
    base = f"long-{filesystem}-{trial}"
    if ctx.role == "holder":
        if holder_stream is None:
            raise ProbeInfraError("holder lost long-hold stream")
        ctx.wait_coord(f"{base}-about-to-try", [contender_token])
        before = _fd_identity(holder_stream.fileno())
        ctx.write_coord(
            f"{base}-holder-pre-ack", {"holder_fstat_immediately_before": before}
        )
        done = ctx.wait_coord(f"{base}-attempt-done", [contender_token])[0]
        after = _fd_identity(holder_stream.fileno())
        witness = {
            "schema": OBSERVATION_SCHEMA,
            **ctx.binding(filesystem, trial, path),
            "kind": "long_hold_holder_witness",
            "holder_nonce": nonce,
            "fstat_immediately_before_attempt": before,
            "fstat_immediately_after_attempt": after,
            "contender_observation_path": done.get("observation_path"),
            "fd_remained_open_from_recon_through_trial": True,
        }
        ctx.write_observation(f"{base}-holder-witness", witness)
    else:
        ctx.write_coord(f"{base}-about-to-try", {"lock_path": str(path)})
        ctx.wait_coord(f"{base}-holder-pre-ack", [holder_token])
        attempt = _run_try_child(
            ctx,
            filesystem=filesystem,
            trial=trial,
            path=path,
            expected_nonce=nonce,
            kind="long_hold_attempt",
            label=f"{base}-attempt-{ctx.job_token}",
        )
        attempt_path = ctx.observation_path(f"{base}-attempt-{ctx.job_token}")
        ctx.write_coord(
            f"{base}-attempt-done",
            {
                "observation_path": str(attempt_path),
                "observation_sha256": _sha256_bytes(attempt_path.read_bytes()),
                "outcome": attempt.get("outcome"),
            },
        )
    ctx.barrier(f"{base}-complete")


def _same_fd(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return (
        first.get("st_dev") == second.get("st_dev")
        and first.get("st_ino") == second.get("st_ino")
        and first.get("pid") == second.get("pid")
        and first.get("fd") == second.get("fd")
    )


def _one(records: list[dict[str, Any]], kind: str, filesystem: str, trial: Any = None) -> dict[str, Any]:
    selected = [
        item
        for item in records
        if item.get("kind") == kind
        and item.get("filesystem") == filesystem
        and (trial is None or str(item.get("trial")) == str(trial))
    ]
    if len(selected) != 1:
        raise ProbeInfraError(
            f"expected one {kind}/{filesystem}/{trial}, found {len(selected)}"
        )
    return selected[0]


def _validate_effective_mounts(
    ctx: RunContext, filesystem: str
) -> tuple[bool, list[dict[str, Any]], list[str], list[str]]:
    valid = True
    entries: list[dict[str, Any]] = []
    reasons: list[str] = []
    node_signatures: list[str] = []
    for marker in ctx.markers:
        token = str(marker.get("job_token"))
        mount_data = marker.get("mounts", {}).get(filesystem)
        if not isinstance(mount_data, dict):
            valid = False
            reasons.append(f"missing effective mount data on {token}")
            continue
        path_entries = mount_data.get("lock_paths")
        if not isinstance(path_entries, list) or not path_entries:
            valid = False
            reasons.append(f"missing resolved lock paths on {token}")
            continue
        signatures: set[str] = set()
        for path_entry in path_entries:
            if not isinstance(path_entry, dict) or not isinstance(
                path_entry.get("effective_mount"), dict
            ):
                valid = False
                reasons.append(f"malformed effective mount entry on {token}")
                continue
            entry = path_entry["effective_mount"]
            entries.append(
                {
                    "job_token": token,
                    "process_nonce": marker.get("process_nonce"),
                    "lock_path": path_entry.get("lock_path"),
                    "effective_mount": entry,
                }
            )
            signature = json.dumps(
                {
                    "filesystem_type": entry.get("filesystem_type"),
                    "source": entry.get("source"),
                    "effective_options": entry.get("effective_options"),
                },
                sort_keys=True,
            )
            signatures.add(signature)
            if entry.get("filesystem_type") != "lustre":
                valid = False
                reasons.append(
                    f"effective filesystem is not Lustre on {token}: "
                    f"{entry.get('filesystem_type')!r}"
                )
            if not entry.get("has_flock"):
                valid = False
                reasons.append(f"flock mount option is absent on {token}")
            if entry.get("has_localflock"):
                valid = False
                reasons.append(f"localflock invalidates the trial on {token}")
        if len(signatures) != 1:
            valid = False
            reasons.append(
                f"lock paths resolve to different mounts on {token}: {sorted(signatures)}"
            )
        elif signatures:
            node_signatures.append(next(iter(signatures)))
    if len(node_signatures) != 2 or len(set(node_signatures)) != 1:
        valid = False
        reasons.append(
            "effective fs type/source/options differ between nodes: "
            f"{node_signatures}"
        )
    return valid, entries, node_signatures, reasons


def _aggregate_filesystem(
    ctx: RunContext, records: list[dict[str, Any]], filesystem: str
) -> dict[str, Any]:
    reasons: list[str] = []
    mount_valid, mount_entries, mount_signatures, mount_reasons = (
        _validate_effective_mounts(ctx, filesystem)
    )
    reasons.extend(mount_reasons)
    controls_valid = True
    for marker in ctx.markers:
        token = marker["job_token"]
        candidates = [
            item
            for item in records
            if item.get("kind") == "unlocked_control"
            and item.get("filesystem") == filesystem
            and item.get("job_token") == token
        ]
        blocked = [
            item
            for item in records
            if item.get("kind") == "same_node_block_control"
            and item.get("filesystem") == filesystem
            and item.get("job_token") == token
        ]
        witnesses = [
            item
            for item in records
            if item.get("kind") == "same_node_holder_witness"
            and item.get("filesystem") == filesystem
            and item.get("job_token") == token
        ]
        if (
            len(candidates) != 1
            or candidates[0].get("outcome") != "ACQUIRED"
            or not candidates[0].get("nonce_matches")
            or not _same_fd(
                candidates[0].get("fstat_immediately_before_attempt", {}),
                candidates[0].get("fstat_immediately_after_attempt", {}),
            )
        ):
            controls_valid = False
            reasons.append(f"unlocked control failed on {token}")
        if (
            len(blocked) != 1
            or blocked[0].get("outcome") != "BLOCKED"
            or not blocked[0].get("nonce_matches")
            or not _same_fd(
                blocked[0].get("fstat_immediately_before_attempt", {}),
                blocked[0].get("fstat_immediately_after_attempt", {}),
            )
        ):
            controls_valid = False
            reasons.append(f"same-node block control failed on {token}")
        if len(witnesses) != 1 or not witnesses[0].get("nonce_matches"):
            controls_valid = False
            reasons.append(f"same-node holder witness failed on {token}")
        elif not _same_fd(
            witnesses[0]["fstat_immediately_before_attempt"],
            witnesses[0]["fstat_immediately_after_attempt"],
        ):
            controls_valid = False
            reasons.append(f"same-node holder fd identity changed on {token}")
        elif blocked and (
            blocked[0].get("fstat_immediately_before_attempt", {}).get("st_dev")
            != witnesses[0]["fstat_immediately_before_attempt"].get("st_dev")
            or blocked[0].get("fstat_immediately_before_attempt", {}).get("st_ino")
            != witnesses[0]["fstat_immediately_before_attempt"].get("st_ino")
        ):
            controls_valid = False
            reasons.append(f"same-node control backing object mismatch on {token}")
    outcomes: list[str] = []
    proof_valid = True
    long_start = _one(records, "long_hold_start", filesystem, "all-trials")
    long_end = _one(records, "long_hold_end", filesystem, "all-trials")
    long_lifetime_valid = _same_fd(
        long_start["holder_fstat"], long_end["holder_fstat"]
    )
    if not long_lifetime_valid:
        proof_valid = False
        reasons.append("long-hold fd identity changed between recon and final release")
    for trial in TRIALS:
        attempt = _one(records, "cross_node_attempt", filesystem, trial)
        post = _one(records, "cross_node_post_release_control", filesystem, trial)
        witness = _one(records, "cross_holder_witness", filesystem, trial)
        long_attempt = _one(records, "long_hold_attempt", filesystem, trial)
        long_witness = _one(records, "long_hold_holder_witness", filesystem, trial)
        outcomes.extend([str(attempt.get("outcome")), str(long_attempt.get("outcome"))])
        if post.get("outcome") != "ACQUIRED":
            proof_valid = False
            reasons.append(f"post-release acquisition failed trial {trial}")
        for label, contender, holder in (
            ("cross", attempt, witness),
            ("long", long_attempt, long_witness),
        ):
            before = contender.get("fstat_immediately_before_attempt", {})
            after = contender.get("fstat_immediately_after_attempt", {})
            holder_before = holder.get("fstat_immediately_before_attempt", {})
            holder_after = holder.get("fstat_immediately_after_attempt", {})
            if not contender.get("nonce_matches"):
                proof_valid = False
                reasons.append(f"{label} nonce mismatch trial {trial}")
            if contender.get("expected_nonce") != holder.get("holder_nonce"):
                proof_valid = False
                reasons.append(f"{label} holder/contender nonce binding mismatch trial {trial}")
            if not _same_fd(before, after) or not _same_fd(holder_before, holder_after):
                proof_valid = False
                reasons.append(f"{label} fd identity changed trial {trial}")
            if label == "long" and not _same_fd(
                long_start["holder_fstat"], holder_before
            ):
                long_lifetime_valid = False
                proof_valid = False
                reasons.append(f"long-hold fd was not continuous through trial {trial}")
            if (
                before.get("st_dev") != holder_before.get("st_dev")
                or before.get("st_ino") != holder_before.get("st_ino")
            ):
                proof_valid = False
                reasons.append(f"{label} backing object mismatch trial {trial}")
    long_post = _one(records, "long_hold_post_release_control", filesystem, "post-release")
    if long_post.get("outcome") != "ACQUIRED":
        proof_valid = False
        reasons.append("long-hold post-release acquisition failed")
    observed_set = sorted(set(outcomes))
    if not controls_valid:
        observed_verdict = Verdict.INVALID_CONTROL
    elif not proof_valid:
        observed_verdict = Verdict.INFRA_ERROR
    elif not mount_valid:
        observed_verdict = Verdict.INFRA_ERROR
    elif observed_set == ["BLOCKED"]:
        observed_verdict = Verdict.BLOCKED_EXPECTED
    elif observed_set == ["ACQUIRED"]:
        observed_verdict = Verdict.ACQUIRED_SILENT_FAIL_OPEN
    elif observed_set == ["ERROR"]:
        observed_verdict = Verdict.ERROR
    else:
        observed_verdict = Verdict.MIXED
    self_checks_valid = controls_valid and proof_valid and mount_valid
    verdict = (
        Verdict.PENDING_EXECUTION_HOST_VALIDATION
        if self_checks_valid
        else observed_verdict
    )
    if self_checks_valid:
        reasons.append(
            "qstat -J -f Execution Host validation is pending; no safety conclusion is valid"
        )
    return {
        "filesystem": filesystem,
        "verdict": verdict,
        "observed_flock_verdict_before_execution_host_validation": observed_verdict,
        "valid_for_safety_conclusion": False,
        "dangerous": None,
        "probe_self_checks_valid_before_execution_host_validation": self_checks_valid,
        "execution_host_validation": EXECUTION_HOST_VALIDATION,
        "safety_derivation_policy": (
            "dangerous may be false only after all self-checks and Execution Host "
            "validation pass and the observed verdict is BLOCKED_EXPECTED; invalid or "
            "pending evidence maps to null"
        ),
        "effective_mounts_valid_on_both_bnodes": mount_valid,
        "effective_mount_signatures_by_node": mount_signatures,
        "controls_valid_on_both_bnodes": controls_valid,
        "backing_object_proof_valid": proof_valid,
        "long_hold_one_fd_from_recon_through_all_trials": long_lifetime_valid,
        "raw_attempt_outcomes": outcomes,
        "raw_attempt_outcome_set": observed_set,
        "reasons": reasons,
        "mount_entries_from_both_jobs": mount_entries,
    }


def _aggregate(ctx: RunContext) -> dict[str, Any]:
    records = [_read_json(path) for path in sorted(ctx.observation_dir.glob("*.json"))]
    filesystems: dict[str, Any] = {}
    try:
        for filesystem in ("work", "home"):
            filesystems[filesystem] = _aggregate_filesystem(ctx, records, filesystem)
    except (KeyError, TypeError, ValueError, ProbeInfraError) as exc:
        filesystems = {
            filesystem: {
                "filesystem": filesystem,
                "verdict": Verdict.INFRA_ERROR,
                "valid_for_safety_conclusion": False,
                "dangerous": None,
                "probe_self_checks_valid_before_execution_host_validation": False,
                "execution_host_validation": EXECUTION_HOST_VALIDATION,
                "reasons": [f"aggregation self-check failed: {exc}"],
            }
            for filesystem in ("work", "home")
        }
    all_self_checks_valid = all(
        value.get("probe_self_checks_valid_before_execution_host_validation") is True
        for value in filesystems.values()
    )
    overall = (
        Verdict.PENDING_EXECUTION_HOST_VALIDATION
        if all_self_checks_valid
        else Verdict.INFRA_ERROR
    )
    return {
        "schema": RESULT_SCHEMA,
        "run_nonce": ctx.run_nonce,
        "overall_verdict": overall,
        "result_state": "PROVISIONAL_NOT_AUTHORITATIVE",
        "valid_for_safety_conclusion": False,
        "dangerous": None,
        "probe_self_checks_valid_before_execution_host_validation": all_self_checks_valid,
        "filesystem_results": filesystems,
        "exact_host_pair": sorted(
            marker["host"]["short_normalized"] for marker in ctx.markers
        ),
        "pbs_jobids_raw": [marker["pbs_jobid_raw"] for marker in ctx.markers],
        "barrier_timeout_seconds": BARRIER_TIMEOUT_SECONDS,
        "internal_total_deadline_seconds": TOTAL_DEADLINE_SECONDS,
        "trial_count": len(TRIALS),
        "raw_observation_files": [
            {
                "path": str(path),
                "sha256": _sha256_bytes(path.read_bytes()),
                "size": path.stat().st_size,
            }
            for path in sorted(ctx.observation_dir.glob("*.json"))
        ],
        "raw_event_files": [str(path) for path in sorted(ctx.event_dir.glob("*.jsonl"))],
        "raw_nodefile_files": [str(path) for path in sorted(ctx.nodefile_dir.glob("*.raw"))],
        "raw_mount_files": [str(path) for path in sorted(ctx.mount_dir.glob("*.raw"))],
        "qstat_execution_host_comparison": EXECUTION_HOST_VALIDATION,
        "controller_completion_required": (
            "The login-side controller must bind raw qstat -J -f Execution Host records "
            "one-to-one to both marker PBS_JOBID/host/process-nonce identities before "
            "deriving a final verdict. This provisional result never authorizes safety."
        ),
        "scope_limitations": [
            "Primitive-only: this does not freeze or validate the T-360 shared/legacy migration contract.",
            "Long-hold means one fd per filesystem from post-recon through all trials in this job.",
            "A multi-hour fd lifetime, client recovery, and reconnect behavior are not reproduced.",
            "Conclusions cannot be generalized beyond the recorded host pair, kernel, and mount snapshot.",
        ],
        "reconstruction_note": (
            "Derived verdicts must be checked against raw attempt outcomes, errno, nonce reads, "
            "pre/post fstat identities, barriers, nodefiles, and mount lines."
        ),
    }


def _scan_files(roots: Iterable[Path]) -> set[Path]:
    found: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() or path.is_symlink():
                found.add(path)
    return found


def _inventory_union(ctx: RunContext) -> tuple[list[Path], list[dict[str, Any]]]:
    inventory_paths = sorted(ctx.inventory_dir.glob("inventory.*.jsonl"))
    if len(inventory_paths) != 2:
        raise ProbeInfraError(
            f"expected two per-process inventories, found {len(inventory_paths)}"
        )
    marker_nonces = {str(marker.get("process_nonce")) for marker in ctx.markers}
    records: list[dict[str, Any]] = []
    for inventory_path in inventory_paths:
        for record in _read_jsonl(inventory_path):
            if record.get("run_nonce") != ctx.run_nonce:
                raise ProbeInfraError(
                    f"inventory run nonce mismatch: {inventory_path}"
                )
            if str(record.get("process_nonce")) not in marker_nonces:
                raise ProbeInfraError(
                    f"inventory process nonce is not bound to a marker: {inventory_path}"
                )
            if record.get("lifecycle") not in {"planned", "published", "removed"}:
                raise ProbeInfraError(
                    f"invalid inventory lifecycle: {inventory_path}"
                )
            records.append(record)
    observed_nonces = {str(record.get("process_nonce")) for record in records}
    if observed_nonces != marker_nonces:
        raise ProbeInfraError(
            f"inventory/marker process nonce mismatch: {sorted(observed_nonces)} "
            f"!= {sorted(marker_nonces)}"
        )
    return inventory_paths, records


def _wait_for_inventory_publication(ctx: RunContext, path: Path) -> None:
    deadline = min(
        time.monotonic() + BARRIER_TIMEOUT_SECONDS,
        ctx.total_deadline_monotonic,
    )
    last_error: ProbeInfraError | None = None
    while time.monotonic() < deadline:
        try:
            records = [
                record
                for inventory_path in sorted(
                    ctx.inventory_dir.glob("inventory.*.jsonl")
                )
                for record in _read_jsonl(inventory_path)
            ]
        except ProbeInfraError as exc:
            last_error = exc
            time.sleep(POLL_SECONDS)
            continue
        if any(
            record.get("path") == str(path)
            and record.get("lifecycle") == "published"
            for record in records
        ):
            return
        time.sleep(POLL_SECONDS)
    suffix = f": last parse error: {last_error}" if last_error is not None else ""
    raise ProbeInfraError(
        f"published inventory record not observed for {path}{suffix}"
    )


def _cleanup_transients(ctx: RunContext) -> None:
    removed: list[str] = []
    missing: list[str] = []
    errors: list[dict[str, str]] = []
    inventory_paths, inventory_records = _inventory_union(ctx)
    allowed_roots = (ctx.coord_dir, ctx.work_lock_dir, ctx.home_lock_dir)
    scan_roots = (
        ctx.marker_dir,
        ctx.nodefile_dir,
        ctx.mount_dir,
        ctx.event_dir,
        ctx.observation_dir,
        ctx.inventory_dir,
        *allowed_roots,
    )
    targets: list[Path] = []
    for record in inventory_records:
        if record.get("transient") is not True:
            continue
        path = Path(str(record.get("path", "")))
        ordinary_transient = any(
            path.is_relative_to(root) for root in allowed_roots
        )
        atomic_temporary = (
            record.get("artifact_kind") == "atomic-publish-temp"
            and ".tmp." in path.name
            and (
                path.is_relative_to(ctx.run_root)
                or path.is_relative_to(ctx.home_root)
            )
        )
        if not path.is_absolute() or not (ordinary_transient or atomic_temporary):
            raise ProbeInfraError(f"unsafe transient inventory target: {path}")
        targets.append(path)
    target_set = set(targets)
    registered_paths = {
        Path(str(record.get("path", ""))) for record in inventory_records
    }
    before_scan = _scan_files(scan_roots)
    unexpected_before = sorted(before_scan - registered_paths, key=str)
    for path in unexpected_before:
        errors.append(
            {"path": str(path), "error": "not registered in either job inventory"}
        )
    targets = sorted(target_set, key=str)
    for path in targets:
        try:
            path.unlink()
            removed.append(str(path))
            _fsync_directory(path.parent)
        except FileNotFoundError:
            missing.append(str(path))
        except OSError as exc:
            errors.append({"path": str(path), "error": str(exc)})
    after_scan = _scan_files(scan_roots)
    remaining_after = sorted(after_scan & target_set, key=str)
    unexpected_after = sorted(after_scan - registered_paths, key=str)
    for path in remaining_after:
        errors.append({"path": str(path), "error": "remained after cleanup"})
    for path in unexpected_after:
        if path not in unexpected_before:
            errors.append(
                {"path": str(path), "error": "unregistered artifact appeared during cleanup"}
            )
    receipt = {
        "schema": SCHEMA,
        **ctx.binding("__cleanup__", -1, ctx.run_root),
        "removed_transient_artifacts": removed,
        "already_missing": missing,
        "errors": errors,
        "inventory_union": [str(path) for path in inventory_paths],
        "inventory_record_count": len(inventory_records),
        "directory_scan_before": [str(path) for path in sorted(before_scan, key=str)],
        "unexpected_before_cleanup": [str(path) for path in unexpected_before],
        "directory_scan_after": [str(path) for path in sorted(after_scan, key=str)],
        "remaining_transient_artifacts": [str(path) for path in remaining_after],
        "unexpected_after_cleanup": [str(path) for path in unexpected_after],
        "persistent_evidence_directories": [
            str(ctx.marker_dir),
            str(ctx.nodefile_dir),
            str(ctx.mount_dir),
            str(ctx.event_dir),
            str(ctx.observation_dir),
            str(ctx.inventory_dir),
        ],
        "abnormal_exit_note": (
            "On abnormal exit, planned or published transient paths and atomic-publish "
            "temp names may remain; preserve the inventories plus a directory scan before "
            "deleting exact paths."
        ),
    }
    ctx.publish_json(
        ctx.run_root / "cleanup-receipt.json",
        receipt,
        "cleanup-receipt",
        False,
    )
    if errors:
        raise ProbeInfraError(f"transient cleanup failed: {errors}")


def _node_main() -> int:
    ctx: RunContext | None = None
    long_streams: dict[str, Any] = {}
    try:
        ctx = RunContext()
        _create_recon_evidence(ctx)
        holder_token, contender_token = _wait_and_validate_recon(ctx)
        if ctx.recon_only:
            return 0
        ctx.check_total_deadline("post-recon")
        lock_dirs = {"work": ctx.work_lock_dir, "home": ctx.home_lock_dir}
        long_nonces: dict[str, str] = {}
        for filesystem, lock_dir in lock_dirs.items():
            path = lock_dir / "long-hold.lock"
            if ctx.role == "holder":
                nonce = secrets.token_hex(24)
                ctx.inventory(path, "long-hold-lock", True)
                stream = _new_locked_file(path, nonce)
                long_streams[filesystem] = stream
                long_nonces[filesystem] = nonce
                ctx.register_published(path, "long-hold-lock", True)
                ctx.write_observation(
                    f"long-{filesystem}-hold-start",
                    {
                        "schema": OBSERVATION_SCHEMA,
                        **ctx.binding(filesystem, "all-trials", path),
                        "kind": "long_hold_start",
                        "holder_nonce": nonce,
                        "holder_fstat": _fd_identity(stream.fileno()),
                        "lifetime_scope": "post-recon through every trial in this job",
                        "multi_hour_lifetime_reproduced": False,
                    },
                )
                ctx.write_coord(
                    f"long-{filesystem}-holder-ready",
                    {
                        "nonce": nonce,
                        "lock_path": str(path),
                        "holder_fstat_at_recon_end": _fd_identity(stream.fileno()),
                        "lifetime_scope": "post-recon through every trial in this job",
                        "multi_hour_lifetime_reproduced": False,
                    },
                )
            else:
                ready = ctx.wait_coord(
                    f"long-{filesystem}-holder-ready", [holder_token]
                )[0]
                if ready.get("lock_path") != str(path):
                    raise ProbeInfraError("different long-hold paths derived by the jobs")
                long_nonces[filesystem] = str(ready["nonce"])
        for filesystem, lock_dir in lock_dirs.items():
            ctx.check_total_deadline(f"controls-{filesystem}")
            _run_local_controls(ctx, filesystem, lock_dir)
        ctx.barrier("controls-on-both-bnodes-complete")
        for filesystem, lock_dir in lock_dirs.items():
            for trial in TRIALS:
                ctx.check_total_deadline(f"cross-{filesystem}-{trial}")
                _perform_cross_trial(
                    ctx,
                    filesystem=filesystem,
                    trial=trial,
                    lock_dir=lock_dir,
                    holder_token=holder_token,
                    contender_token=contender_token,
                )
                _perform_long_hold_attempt(
                    ctx,
                    filesystem=filesystem,
                    trial=trial,
                    path=lock_dir / "long-hold.lock",
                    holder_stream=long_streams.get(filesystem),
                    nonce=long_nonces[filesystem],
                    holder_token=holder_token,
                    contender_token=contender_token,
                )
        ctx.check_total_deadline("release-long-hold")
        for filesystem, lock_dir in lock_dirs.items():
            path = lock_dir / "long-hold.lock"
            if ctx.role == "holder":
                stream = long_streams.pop(filesystem)
                final_identity = _fd_identity(stream.fileno())
                ctx.write_observation(
                    f"long-{filesystem}-hold-end",
                    {
                        "schema": OBSERVATION_SCHEMA,
                        **ctx.binding(filesystem, "all-trials", path),
                        "kind": "long_hold_end",
                        "holder_nonce": long_nonces[filesystem],
                        "holder_fstat": final_identity,
                        "released_after_all_trials": True,
                        "multi_hour_lifetime_reproduced": False,
                    },
                )
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                stream.close()
                ctx.write_coord(
                    f"long-{filesystem}-released",
                    {
                        "released_after_all_trials": True,
                        "holder_fstat_before_release": final_identity,
                    },
                )
            else:
                ctx.wait_coord(f"long-{filesystem}-released", [holder_token])
                _run_try_child(
                    ctx,
                    filesystem=filesystem,
                    trial="post-release",
                    path=path,
                    expected_nonce=long_nonces[filesystem],
                    kind="long_hold_post_release_control",
                    label=f"long-{filesystem}-post-release-{ctx.job_token}",
                )
        ctx.barrier("all-measurements-complete")
        if ctx.role == "holder":
            result = _aggregate(ctx)
            result_path = ctx.run_root / "flock-result.json"
            ctx.publish_json(result_path, result, "derived-provisional-result", False)
            compute_rc = (
                PENDING_VALIDATION_RC
                if result.get("overall_verdict")
                == Verdict.PENDING_EXECUTION_HOST_VALIDATION
                else INFRA_RC
            )
            ctx.write_coord(
                "aggregate-ready",
                {
                    "result_path": str(result_path),
                    "compute_phase_returncode": compute_rc,
                    "execution_host_validation": EXECUTION_HOST_VALIDATION,
                },
            )
            ctx.wait_coord("aggregate-consumed", [contender_token])
            ctx.wait_coord("cleanup-inventory-ready", [contender_token])
            _wait_for_inventory_publication(
                ctx, ctx.coord_path("cleanup-inventory-ready", contender_token)
            )
            _cleanup_transients(ctx)
            return compute_rc
        else:
            aggregate_ready = ctx.wait_coord("aggregate-ready", [holder_token])[0]
            ctx.write_coord("aggregate-consumed", {"consumed": True})
            ctx.write_coord(
                "cleanup-inventory-ready",
                {"no_more_transient_artifacts_will_be_created": True},
            )
            compute_rc = aggregate_ready.get("compute_phase_returncode")
            if compute_rc not in {INFRA_RC, PENDING_VALIDATION_RC}:
                raise ProbeInfraError(
                    f"invalid aggregate compute returncode: {compute_rc!r}"
                )
            return int(compute_rc)
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        ProbeInfraError,
        subprocess.SubprocessError,
    ) as exc:
        if ctx is not None and not ctx.recon_only:
            evidence_errors: list[str] = []
            try:
                ctx.event(
                    "infra_error",
                    filesystem="__run__",
                    trial=-1,
                    path=ctx.run_root,
                    verdict=Verdict.INFRA_ERROR,
                    exception_type=type(exc).__name__,
                    error=str(exc),
                )
            except (OSError, ProbeInfraError) as evidence_exc:
                evidence_errors.append(f"event write failed: {evidence_exc}")
            try:
                error_path = ctx.run_root / f"infra-error.{ctx.process_nonce}.json"
                ctx.publish_json(
                    error_path,
                    {
                        "schema": RESULT_SCHEMA,
                        **ctx.binding("__run__", -1, ctx.run_root),
                        "verdict": Verdict.INFRA_ERROR,
                        "valid_for_safety_conclusion": False,
                        "dangerous": None,
                        "barrier_timeout_seconds": BARRIER_TIMEOUT_SECONDS,
                        "exception_type": type(exc).__name__,
                        "error": str(exc),
                    },
                    "infra-error",
                    False,
                )
            except (OSError, ProbeInfraError) as evidence_exc:
                evidence_errors.append(f"infra-error evidence write failed: {evidence_exc}")
            for evidence_error in evidence_errors:
                print(f"T361 EVIDENCE_ERROR: {evidence_error}", file=sys.stderr)
        print(f"T361 INFRA_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return INFRA_RC
    finally:
        for stream in long_streams.values():
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                stream.close()
            except OSError as close_exc:
                print(
                    f"T361 STREAM_CLEANUP_ERROR: {type(close_exc).__name__}: "
                    f"{close_exc}",
                    file=sys.stderr,
                )


def _try_lock_main(arguments: argparse.Namespace) -> int:
    output = Path(arguments.output)
    path = Path(arguments.path)
    host = _host_snapshot(time.monotonic() + TOTAL_DEADLINE_SECONDS)
    binding = {
        "run_nonce": arguments.run_nonce,
        "filesystem": arguments.filesystem,
        "trial": arguments.trial,
        "path": str(path),
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "pbs_jobid_raw": os.environ.get("PBS_JOBID"),
        "job_token": arguments.job_token,
        "process_nonce": arguments.process_nonce,
        "hostname_short_normalized": host["short_normalized"],
        "hostname_fqdn_normalized": host["fqdn_normalized"],
    }
    result = _attempt_lock(
        lock_path=path,
        expected_nonce=arguments.expected_nonce,
        binding=binding,
        kind=arguments.kind,
    )
    _write_exclusive_json(
        output, result, temporary=Path(arguments.output_temporary)
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("node")
    attempt = subparsers.add_parser("try-lock")
    attempt.add_argument("--run-nonce", required=True)
    attempt.add_argument("--job-token", required=True)
    attempt.add_argument("--process-nonce", required=True)
    attempt.add_argument("--filesystem", choices=("work", "home"), required=True)
    attempt.add_argument("--trial", required=True)
    attempt.add_argument("--path", required=True)
    attempt.add_argument("--expected-nonce", required=True)
    attempt.add_argument("--kind", required=True)
    attempt.add_argument("--output", required=True)
    attempt.add_argument("--output-temporary", required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    if arguments.command == "node":
        return _node_main()
    if arguments.command == "try-lock":
        return _try_lock_main(arguments)
    raise AssertionError(arguments.command)


if __name__ == "__main__":
    raise SystemExit(main())
