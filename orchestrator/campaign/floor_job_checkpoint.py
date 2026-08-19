# -*- coding: utf-8 -*-
"""Diagnostic-only durable evidence for Pegasus floor jobs.

This module deliberately has no executable entry point.  Shell callers use the
small public functions through an isolated Python snippet; campaign callers
import them directly.  Production callers use the ``*_bounded`` entry points;
transaction helpers remain non-throwing but are not a wall-clock boundary.
"""
from __future__ import annotations

import errno
import fcntl
import json
import os
import re
import select
import signal
import stat
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, MutableMapping, Sequence


CHECKPOINT_SCHEMA = "pegasus-job-checkpoint/v1"
INDEX_SCHEMA = "pegasus-job-evidence-index/v2"
INDEX_STATUS_SCHEMA = "pegasus-job-evidence-index-status/v1"
AUTHORITY = "diagnostic-only"
CHECKPOINT_ENV = "IZANAGI_FLOOR_JOB_CHECKPOINT_PATH"
EVIDENCE_ROOT_ENV = "IZANAGI_FLOOR_JOB_EVIDENCE_ROOT"
_NONCE_RE = re.compile(r"[0-9a-f]{32}")
_JOB_RE = re.compile(r"(?:0:)?[A-Za-z0-9][A-Za-z0-9._-]*")
_CHECKPOINT_MAX_BYTES = 64 * 1024
_JOURNAL_MAX_BYTES = 1024 * 1024
_LINE_MAX_BYTES = 4096
_INDEX_MAX_BYTES = 4096
_DIAGNOSTIC_IO_TIMEOUT_S = 5.0
_MAX_TIME_SHARDS = 32
_MAX_TIME_ENTRIES_PER_SHARD = 4096
_PROBE_STATUSES = frozenset({
    "default-readable",
    "default-unreadable",
    "override-readable",
    "override-unreadable-fallback",
    "override-and-default-unreadable",
})

CHECKPOINT_KEYS = frozenset({
    "schema_version",
    "authority",
    "producer",
    "env_tag",
    "pbs_jobid",
    "submission_nonce",
    "stage",
    "transition",
    "rc",
    "command",
    "durability",
    "recorded_epoch",
    "repo_root",
    "attempt_dir",
    "run_dir",
    "journal_path",
    "partial_log_path",
})
INDEX_KEYS = frozenset({
    "schema_version",
    "authority",
    "pbs_jobid",
    "normalized_pbs_jobid",
    "submitted_at",
    "submission_nonce",
    "catalog_root",
    "evidence_root",
    "checkpoint_path",
    "requested_evidence_root",
    "login_probe_status",
})
INDEX_STATUS_KEYS = frozenset({
    "schema_version",
    "authority",
    "pbs_jobid",
    "normalized_pbs_jobid",
    "submitted_at",
    "submission_nonce",
    "catalog_root",
    "evidence_root",
    "requested_evidence_root",
    "login_probe_status",
    "index_write_status",
})

class CheckpointError(ValueError):
    """External diagnostic evidence is malformed or cannot be joined."""


class _DiagnosticTimeout(TimeoutError):
    """A diagnostic filesystem operation exceeded its fail-open budget."""


@contextmanager
def _diagnostic_io_deadline(
    seconds: float | None = None,
) -> Iterator[None]:
    """Bound one complete diagnostic transaction without changing caller timers."""

    if seconds is None:
        seconds = _DIAGNOSTIC_IO_TIMEOUT_S
    if (
        seconds <= 0
        or threading.current_thread() is not threading.main_thread()
        or not hasattr(signal, "setitimer")
        or not hasattr(signal, "ITIMER_REAL")
    ):
        raise _DiagnosticTimeout("diagnostic I/O deadline is unavailable")
    previous_delay, previous_interval = signal.getitimer(signal.ITIMER_REAL)
    if previous_delay > 0 or previous_interval > 0:
        raise _DiagnosticTimeout("caller already owns the process alarm")
    previous_handler = signal.getsignal(signal.SIGALRM)

    def expire(_signum: int, _frame: object) -> None:
        raise _DiagnosticTimeout("diagnostic I/O deadline expired")

    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)


def _bounded_boolean_child(operation: Callable[[], bool], *, timeout_s: float) -> bool:
    """Run blocking I/O out of process and never wait past the parent timeout.

    Timeout sends ``SIGALRM`` so an in-flight transaction can roll back when
    the kernel call returns; the parent deliberately does not wait for it.
    """

    if type(timeout_s) is not float or timeout_s <= 0 or not hasattr(os, "fork"):
        return False
    try:
        read_fd, write_fd = os.pipe()
    except OSError:
        return False
    try:
        child = os.fork()
    except OSError:
        os.close(read_fd)
        os.close(write_fd)
        return False
    if child == 0:  # pragma: no cover - outcome is observed through the pipe
        os.close(read_fd)
        try:
            result = operation()
        except BaseException:
            result = False
        try:
            os.write(write_fd, b"1" if result else b"0")
        except OSError:
            pass
        finally:
            os.close(write_fd)
        os._exit(0)

    os.close(write_fd)
    try:
        try:
            readable, _writable, _exceptional = select.select(
                [read_fd], [], [], timeout_s,
            )
            if readable:
                result = os.read(read_fd, 1) == b"1"
                os.waitpid(child, 0)
                return result
        except (OSError, ValueError, ChildProcessError):
            pass
        try:
            os.kill(child, signal.SIGALRM)
        except (OSError, ProcessLookupError):
            pass
        try:
            os.waitpid(child, os.WNOHANG)
        except (OSError, ChildProcessError):
            pass
        return False
    finally:
        os.close(read_fd)


def normalize_job_id(value: str) -> str:
    if type(value) is not str or _JOB_RE.fullmatch(value) is None:
        raise CheckpointError("PBS job id is malformed")
    return value[2:] if value.startswith("0:") else value


def _validate_nonce(value: str) -> str:
    if type(value) is not str or _NONCE_RE.fullmatch(value) is None:
        raise CheckpointError("submission nonce is malformed")
    return value


def checkpoint_path(root: os.PathLike[str] | str, job_id: str, nonce: str) -> Path:
    root_path = Path(root)
    if not root_path.is_absolute():
        raise CheckpointError("evidence root must be absolute")
    _validate_nonce(nonce)
    normalized = normalize_job_id(job_id)
    return root_path / "pegasus" / normalized / nonce / "checkpoint.jsonl"


def _checkpoint_coordinates(path: Path, job_id: str, nonce: str) -> Path:
    if not path.is_absolute() or path.name != "checkpoint.jsonl":
        raise CheckpointError("checkpoint path is not an absolute checkpoint leaf")
    _validate_nonce(nonce)
    normalized = normalize_job_id(job_id)
    if path.parent.name != nonce or path.parent.parent.name != normalized:
        raise CheckpointError("checkpoint path does not bind job id and nonce")
    if path.parent.parent.parent.name != "pegasus":
        raise CheckpointError("checkpoint path is outside the pegasus namespace")
    return path.parent.parent.parent.parent


def _directory_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _open_absolute_directory(path: Path) -> int:
    """Open every component from ``/`` without following a symlink."""

    if not path.is_absolute():
        raise CheckpointError("secure directory path must be absolute")
    descriptor = os.open("/", _directory_flags())
    try:
        for component in path.parts[1:]:
            if component in {"", ".", ".."}:
                raise CheckpointError("unsafe directory component")
            child = os.open(component, _directory_flags(), dir_fd=descriptor)
            try:
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    raise CheckpointError("path component is not a directory")
            except BaseException:
                os.close(child)
                raise
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_or_create_child_directory(parent_fd: int, name: str) -> tuple[int, bool]:
    if not name or name in {".", ".."} or "/" in name:
        raise CheckpointError("unsafe child directory component")
    created = False
    try:
        child = os.open(name, _directory_flags(), dir_fd=parent_fd)
    except FileNotFoundError:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
        created = True
        child = os.open(name, _directory_flags(), dir_fd=parent_fd)
    if not stat.S_ISDIR(os.fstat(child).st_mode):
        os.close(child)
        raise CheckpointError("path component is not a directory")
    return child, created


def _open_or_create_absolute_directory(path: Path) -> tuple[int, bool]:
    """Open an absolute directory, securely creating a missing suffix."""

    try:
        return _open_absolute_directory(path), False
    except FileNotFoundError:
        pass

    if not path.is_absolute():
        raise CheckpointError("secure directory path must be absolute")
    descriptor = os.open("/", _directory_flags())
    created_any = False
    try:
        for component in path.parts[1:]:
            child, created = _open_or_create_child_directory(
                descriptor, component,
            )
            created_any = created_any or created
            os.close(descriptor)
            descriptor = child
        return descriptor, created_any
    except BaseException:
        os.close(descriptor)
        raise


def _open_namespace_parent(
    root: Path,
    components: Sequence[str],
    *,
    create: bool,
) -> tuple[int, bool]:
    if create:
        descriptor, created_any = _open_or_create_absolute_directory(root)
    else:
        descriptor = _open_absolute_directory(root)
        created_any = False
    try:
        for component in components:
            if create:
                child, created = _open_or_create_child_directory(descriptor, component)
                created_any = created_any or created
            else:
                child = os.open(component, _directory_flags(), dir_fd=descriptor)
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    os.close(child)
                    raise CheckpointError("path component is not a directory")
            os.close(descriptor)
            descriptor = child
        return descriptor, created_any
    except BaseException:
        os.close(descriptor)
        raise


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        written = os.write(descriptor, view[offset:])
        if written <= 0:
            raise OSError(errno.EIO, "zero-length diagnostic write")
        offset += written


def _append_payload(path: Path, job_id: str, nonce: str, payload: bytes) -> None:
    with _diagnostic_io_deadline():
        root = _checkpoint_coordinates(path, job_id, nonce)
        parent_fd, created_directory = _open_namespace_parent(
            root, ("pegasus", normalize_job_id(job_id), nonce), create=True,
        )
        descriptor = -1
        locked = False
        start_offset: int | None = None
        try:
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open("checkpoint.jsonl", flags, 0o600, dir_fd=parent_fd)
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise CheckpointError("checkpoint leaf is not a regular file")
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            locked = True
            start_offset = os.lseek(descriptor, 0, os.SEEK_END)
            try:
                _write_all(descriptor, payload)
                os.fsync(descriptor)
            except BaseException:
                signal.setitimer(signal.ITIMER_REAL, _DIAGNOSTIC_IO_TIMEOUT_S)
                os.ftruncate(descriptor, start_offset)
                os.fsync(descriptor)
                raise
            if created_directory:
                os.fsync(parent_fd)
        finally:
            if descriptor >= 0:
                if locked:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)
            os.close(parent_fd)


def _json_line(document: Mapping[str, object], *, limit: int) -> bytes:
    payload = (
        json.dumps(
            dict(document), ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ) + "\n"
    ).encode("utf-8")
    if len(payload) > limit:
        raise CheckpointError("diagnostic record exceeds its byte limit")
    return payload


def make_checkpoint_record(
    *,
    producer: str,
    job_id: str,
    nonce: str,
    stage: str,
    transition: str,
    rc: int | None,
    command: str | None,
    durability: str,
    path: os.PathLike[str] | str,
    repo_root: str | None = None,
    attempt_dir: str | None = None,
    run_dir: str | None = None,
    journal_path: str | None = None,
) -> dict[str, object]:
    checkpoint = Path(path)
    _checkpoint_coordinates(checkpoint, job_id, nonce)
    if type(producer) is not str or not producer:
        raise CheckpointError("checkpoint producer is invalid")
    if type(stage) is not str or not stage or type(transition) is not str or not transition:
        raise CheckpointError("checkpoint transition is invalid")
    if rc is not None and type(rc) is not int:
        raise CheckpointError("checkpoint rc must be an exact integer or null")
    if command is not None and type(command) is not str:
        raise CheckpointError("checkpoint command must be a string or null")
    if durability not in {"process-kill", "fsynced"}:
        raise CheckpointError("checkpoint durability is invalid")
    return {
        "schema_version": CHECKPOINT_SCHEMA,
        "authority": AUTHORITY,
        "producer": producer,
        "env_tag": "pegasus",
        "pbs_jobid": job_id,
        "submission_nonce": nonce,
        "stage": stage,
        "transition": transition,
        "rc": rc,
        "command": command,
        "durability": durability,
        "recorded_epoch": int(time.time()),
        "repo_root": repo_root,
        "attempt_dir": attempt_dir,
        "run_dir": run_dir,
        "journal_path": journal_path,
        "partial_log_path": str(checkpoint),
    }


def try_append_checkpoint(
    *,
    attempts: int = 2,
    **fields: Any,
) -> bool:
    """Append one record without ever propagating a writer failure."""

    if type(attempts) is not int or attempts < 1 or attempts > 3:
        return False
    for _attempt in range(attempts):
        try:
            record = make_checkpoint_record(**fields)
            payload = _json_line(record, limit=_LINE_MAX_BYTES)
            _append_payload(
                Path(fields["path"]), fields["job_id"], fields["nonce"], payload,
            )
            return True
        except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
            continue
    return False


def try_append_checkpoint_bounded(
    *, timeout_s: float = _DIAGNOSTIC_IO_TIMEOUT_S, **fields: Any,
) -> bool:
    """Append through an isolated child so a stuck filesystem cannot stop work."""

    bounded_fields = dict(fields)
    bounded_fields["attempts"] = 1
    return _bounded_boolean_child(
        lambda: try_append_checkpoint(**bounded_fields), timeout_s=timeout_s,
    )


def take_checkpoint_environment(
    environ: MutableMapping[str, str],
) -> dict[str, str] | None:
    """Move diagnostic keys to private state before any measured subprocess."""

    raw_path = environ.pop(CHECKPOINT_ENV, None)
    environ.pop(EVIDENCE_ROOT_ENV, None)
    if raw_path is None:
        return None
    try:
        path = Path(raw_path)
        job_id = environ.get("IZANAGI_RESERVATION_JOB_ID", "")
        nonce = environ.get("IZANAGI_RESERVATION_NONCE", "")
        _checkpoint_coordinates(path, job_id, nonce)
    except (OSError, ValueError, TypeError):
        return None
    return {"path": str(path), "job_id": job_id, "nonce": nonce}


def index_paths(
    root: os.PathLike[str] | str, job_id: str, nonce: str, submitted_at: int,
) -> tuple[Path, Path]:
    root_path = Path(root)
    normalized = normalize_job_id(job_id)
    _validate_nonce(nonce)
    if type(submitted_at) is not int or submitted_at <= 0:
        raise CheckpointError("submitted_at is invalid")
    try:
        shard = datetime.fromtimestamp(
            submitted_at, tz=timezone.utc,
        ).strftime("%Y-%m-%d")
    except (OSError, OverflowError, ValueError) as exc:
        raise CheckpointError("submitted_at is outside the supported range") from exc
    return (
        root_path / "index" / "by-job" / normalized / f"{nonce}.json",
        root_path / "index" / "by-time" / shard / f"{submitted_at:020d}-{nonce}.json",
    )


def _ensure_payload(path: Path, root: Path, components: Sequence[str], payload: bytes) -> None:
    """Create a leaf once, or accept an existing byte-identical regular leaf."""

    parent_fd, created_directory = _open_namespace_parent(root, components, create=True)
    descriptor = -1
    created_leaf = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_fd)
            created_leaf = True
        except FileExistsError:
            read_flags = os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                read_flags |= os.O_NOFOLLOW
            descriptor = os.open(path.name, read_flags, dir_fd=parent_fd)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise CheckpointError("index leaf is not a regular file")
        if created_leaf:
            _write_all(descriptor, payload)
        else:
            observed = os.read(descriptor, len(payload) + 1)
            if observed != payload:
                raise CheckpointError("existing diagnostic index bytes differ")
        os.fsync(descriptor)
        if created_directory or created_leaf:
            os.fsync(parent_fd)
    except BaseException:
        if created_leaf:
            try:
                signal.setitimer(signal.ITIMER_REAL, _DIAGNOSTIC_IO_TIMEOUT_S)
                os.unlink(path.name, dir_fd=parent_fd)
                os.fsync(parent_fd)
            except OSError:
                pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent_fd)


def try_create_index(
    *,
    root: os.PathLike[str] | str,
    evidence_root: os.PathLike[str] | str | None = None,
    job_id: str,
    nonce: str,
    submitted_at: int,
    requested_root: str | None,
    login_probe_status: str,
) -> bool:
    """Publish a restartable create-only pair in a known catalog root."""

    try:
        with _diagnostic_io_deadline():
            root_path = Path(root)
            effective_root = (
                root_path if evidence_root is None else Path(evidence_root)
            )
            if not root_path.is_absolute() or not effective_root.is_absolute():
                raise CheckpointError("catalog and evidence roots must be absolute")
            if (
                login_probe_status not in _PROBE_STATUSES
                or requested_root is not None
                and type(requested_root) is not str
            ):
                raise CheckpointError("login probe result is invalid")
            job_path, time_path = index_paths(root_path, job_id, nonce, submitted_at)
            checkpoint = checkpoint_path(effective_root, job_id, nonce)
            document = {
                "schema_version": INDEX_SCHEMA,
                "authority": AUTHORITY,
                "pbs_jobid": normalize_job_id(job_id),
                "normalized_pbs_jobid": normalize_job_id(job_id),
                "submitted_at": submitted_at,
                "submission_nonce": nonce,
                "catalog_root": str(root_path),
                "evidence_root": str(effective_root),
                "checkpoint_path": str(checkpoint),
                "requested_evidence_root": requested_root,
                "login_probe_status": login_probe_status,
            }
            payload = _json_line(document, limit=_INDEX_MAX_BYTES)
            _ensure_payload(
                job_path, root_path,
                ("index", "by-job", normalize_job_id(job_id)), payload,
            )
            _ensure_payload(
                time_path, root_path,
                ("index", "by-time", time_path.parent.name), payload,
            )
            return True
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        return False


def try_create_index_bounded(
    *, timeout_s: float = _DIAGNOSTIC_IO_TIMEOUT_S, **fields: Any,
) -> bool:
    """Publish an index pair through an isolated diagnostic child."""

    return _bounded_boolean_child(
        lambda: try_create_index(**fields), timeout_s=timeout_s,
    )


def _no_duplicate_pairs(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CheckpointError("duplicate JSON key")
        result[key] = value
    return result


def _read_leaf(path: Path, root: Path, components: Sequence[str], limit: int) -> bytes:
    parent_fd, _created = _open_namespace_parent(root, components, create=False)
    descriptor = -1
    try:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path.name, flags, dir_fd=parent_fd)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise CheckpointError("diagnostic leaf is not a regular file")
        payload = os.read(descriptor, limit + 1)
        if len(payload) > limit:
            raise CheckpointError("diagnostic leaf exceeds its read bound")
        return payload
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent_fd)


def _decode_jsonl_prefix(payload: bytes) -> tuple[list[dict[str, object]], bool]:
    incomplete_tail = bool(payload) and not payload.endswith(b"\n")
    complete = payload if not incomplete_tail else payload[: payload.rfind(b"\n") + 1]
    records: list[dict[str, object]] = []
    for lineno, raw in enumerate(complete.splitlines(), start=1):
        if not raw:
            raise CheckpointError(f"diagnostic JSONL line {lineno} is empty")
        try:
            value = json.loads(
                raw.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
                parse_constant=lambda token: (_ for _ in ()).throw(
                    CheckpointError(f"non-finite JSON constant: {token}")
                ),
            )
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CheckpointError(f"diagnostic JSONL line {lineno} is invalid") from exc
        if type(value) is not dict:
            raise CheckpointError(f"diagnostic JSONL line {lineno} is not an object")
        records.append(value)
    return records, incomplete_tail


def read_checkpoint(
    root: os.PathLike[str] | str, job_id: str, nonce: str,
) -> tuple[list[dict[str, object]], bool, Path]:
    root_path = Path(root)
    path = checkpoint_path(root_path, job_id, nonce)
    payload = _read_leaf(
        path, root_path, ("pegasus", normalize_job_id(job_id), nonce),
        _CHECKPOINT_MAX_BYTES,
    )
    records, incomplete_tail = _decode_jsonl_prefix(payload)
    for record in records:
        if set(record) != CHECKPOINT_KEYS:
            raise CheckpointError("checkpoint record key set mismatch")
        if (
            record.get("schema_version") != CHECKPOINT_SCHEMA
            or record.get("authority") != AUTHORITY
            or record.get("env_tag") != "pegasus"
            or record.get("producer") not in {
                "floor_campaign.sh", "s8b_floor_campaign.py",
            }
            or type(record.get("pbs_jobid")) is not str
            or normalize_job_id(record["pbs_jobid"]) != normalize_job_id(job_id)
            or record.get("submission_nonce") != nonce
            or record.get("partial_log_path") != str(path)
            or type(record.get("stage")) is not str
            or not record["stage"]
            or record.get("transition") not in {
                "entered", "rejected", "failed", "signalled", "run-linked",
            }
            or (
                record.get("rc") is not None
                and type(record.get("rc")) is not int
            )
            or (
                record.get("command") is not None
                and type(record.get("command")) is not str
            )
            or record.get("durability") not in {"process-kill", "fsynced"}
            or type(record.get("recorded_epoch")) is not int
            or record["recorded_epoch"] <= 0
            or any(
                record.get(field) is not None
                and type(record.get(field)) is not str
                for field in (
                    "repo_root", "attempt_dir", "run_dir", "journal_path",
                )
            )
        ):
            raise CheckpointError("checkpoint record binding mismatch")
    return records, incomplete_tail, path


def load_bound_index(
    root: os.PathLike[str] | str,
    *,
    job_id: str,
    nonce: str,
    submitted_at: int,
) -> dict[str, object]:
    root_path = Path(root)
    job_path, _time_path = index_paths(root_path, job_id, nonce, submitted_at)
    payload = _read_leaf(
        job_path, root_path,
        ("index", "by-job", normalize_job_id(job_id)), _INDEX_MAX_BYTES,
    )
    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CheckpointError(f"non-finite JSON constant: {token}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointError("external evidence index is invalid JSON") from exc
    stored_job_id = value.get("pbs_jobid") if type(value) is dict else None
    effective_root = (
        Path(value["evidence_root"])
        if type(value) is dict and type(value.get("evidence_root")) is str
        else Path()
    )
    expected_checkpoint = (
        checkpoint_path(effective_root, stored_job_id, nonce)
        if type(stored_job_id) is str and effective_root.is_absolute()
        else None
    )
    if (
        type(value) is not dict
        or set(value) != INDEX_KEYS
        or value.get("schema_version") != INDEX_SCHEMA
        or value.get("authority") != AUTHORITY
        or type(stored_job_id) is not str
        or normalize_job_id(stored_job_id) != normalize_job_id(job_id)
        or value.get("normalized_pbs_jobid") != normalize_job_id(job_id)
        or value.get("submitted_at") != submitted_at
        or value.get("submission_nonce") != nonce
        or value.get("catalog_root") != str(root_path)
        or not effective_root.is_absolute()
        or value.get("checkpoint_path") != str(expected_checkpoint)
        or value.get("login_probe_status") not in _PROBE_STATUSES
        or (
            value.get("requested_evidence_root") is not None
            and type(value.get("requested_evidence_root")) is not str
        )
    ):
        raise CheckpointError("external evidence index binding mismatch")
    return value


def resolve_indices_by_job(
    root: os.PathLike[str] | str,
    *,
    job_id: str,
    max_entries: int = 32,
) -> list[dict[str, object]]:
    """Resolve at most ``max_entries`` nonce records for one normalized job ID."""

    if type(max_entries) is not int or not 1 <= max_entries <= 1024:
        raise CheckpointError("job index query bound is invalid")
    root_path = Path(root)
    normalized = normalize_job_id(job_id)
    directory_fd, _created = _open_namespace_parent(
        root_path, ("index", "by-job", normalized), create=False,
    )
    names: list[str] = []
    try:
        with os.scandir(directory_fd) as entries:
            for entry in entries:
                if re.fullmatch(r"[0-9a-f]{32}\.json", entry.name) is None:
                    continue
                names.append(entry.name)
                if len(names) > max_entries:
                    raise CheckpointError("job index query exceeded its result bound")
    finally:
        os.close(directory_fd)
    resolved: list[dict[str, object]] = []
    for name in sorted(names):
        nonce = name[:-5]
        job_path = root_path / "index" / "by-job" / normalized / name
        payload = _read_leaf(
            job_path, root_path, ("index", "by-job", normalized), _INDEX_MAX_BYTES,
        )
        try:
            value = json.loads(
                payload.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
            )
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CheckpointError("job index entry is invalid JSON") from exc
        submitted_at = value.get("submitted_at") if type(value) is dict else None
        if type(submitted_at) is not int:
            raise CheckpointError("job index submitted_at is invalid")
        resolved.append(load_bound_index(
            root_path, job_id=job_id, nonce=nonce, submitted_at=submitted_at,
        ))
    return resolved


def resolve_indices_by_time(
    root: os.PathLike[str] | str,
    *,
    earliest: int,
    latest: int,
    max_entries: int = 128,
) -> list[dict[str, object]]:
    """Resolve a bounded interval.

    ``max_entries`` limits matching results, not unrelated lifetime history.
    UTC-day shards bound discovery to at most 32 directories and 4096 directory
    entries per selected day.
    """

    if (
        type(earliest) is not int
        or type(latest) is not int
        or earliest <= 0
        or latest < earliest
        or type(max_entries) is not int
        or max_entries < 1
        or max_entries > 1024
    ):
        raise CheckpointError("time index query bounds are invalid")
    root_path = Path(root)
    try:
        first_day = datetime.fromtimestamp(earliest, tz=timezone.utc).date()
        last_day = datetime.fromtimestamp(latest, tz=timezone.utc).date()
    except (OSError, OverflowError, ValueError) as exc:
        raise CheckpointError("time index query is outside the supported range") from exc
    shard_count = (last_day - first_day).days + 1
    if shard_count > _MAX_TIME_SHARDS:
        raise CheckpointError("time index query exceeded its shard bound")
    candidates: list[tuple[int, str]] = []
    for day_offset in range(shard_count):
        day = first_day.fromordinal(first_day.toordinal() + day_offset)
        shard = day.isoformat()
        try:
            directory_fd, _created = _open_namespace_parent(
                root_path, ("index", "by-time", shard), create=False,
            )
        except FileNotFoundError:
            continue
        try:
            examined = 0
            with os.scandir(directory_fd) as entries:
                for entry in entries:
                    examined += 1
                    if examined > _MAX_TIME_ENTRIES_PER_SHARD:
                        raise CheckpointError(
                            "time index shard exceeded its scan bound"
                        )
                    match = re.fullmatch(
                        r"([0-9]{20})-([0-9a-f]{32})\.json", entry.name,
                    )
                    if match is None:
                        continue
                    submitted_at = int(match.group(1))
                    if earliest <= submitted_at <= latest:
                        candidates.append((submitted_at, entry.name))
                        if len(candidates) > max_entries:
                            raise CheckpointError(
                                "time index query exceeded its result bound"
                            )
        finally:
            os.close(directory_fd)
    resolved: list[dict[str, object]] = []
    for submitted_at, name in sorted(candidates):
        nonce = name[-37:-5]
        shard = datetime.fromtimestamp(submitted_at, tz=timezone.utc).strftime(
            "%Y-%m-%d"
        )
        time_path = root_path / "index" / "by-time" / shard / name
        payload = _read_leaf(
            time_path, root_path, ("index", "by-time", shard), _INDEX_MAX_BYTES,
        )
        try:
            value = json.loads(
                payload.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
            )
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise CheckpointError("time index entry is invalid JSON") from exc
        if (
            type(value) is not dict
            or set(value) != INDEX_KEYS
            or value.get("schema_version") != INDEX_SCHEMA
            or value.get("authority") != AUTHORITY
            or value.get("submitted_at") != submitted_at
            or value.get("submission_nonce") != nonce
            or type(value.get("pbs_jobid")) is not str
            or value.get("normalized_pbs_jobid")
            != normalize_job_id(value["pbs_jobid"])
            or value.get("catalog_root") != str(root_path)
            or type(value.get("evidence_root")) is not str
            or not Path(value["evidence_root"]).is_absolute()
            or value.get("checkpoint_path") != str(checkpoint_path(
                Path(value["evidence_root"]), value["pbs_jobid"], nonce,
            ))
            or value.get("login_probe_status") not in _PROBE_STATUSES
        ):
            raise CheckpointError("time index entry binding mismatch")
        resolved.append(value)
    return resolved


def try_create_index_status(
    path: os.PathLike[str] | str,
    *,
    catalog_root: os.PathLike[str] | str,
    evidence_root: os.PathLike[str] | str,
    job_id: str,
    nonce: str,
    submitted_at: int,
    requested_root: str | None,
    login_probe_status: str,
    index_write_status: str,
) -> bool:
    """Persist probe/index outcome beside the immutable submission receipt."""

    try:
        with _diagnostic_io_deadline():
            target = Path(path)
            catalog = Path(catalog_root)
            effective = Path(evidence_root)
            if (
                not target.is_absolute()
                or target.name != "evidence-index-status.json"
                or not catalog.is_absolute()
                or not effective.is_absolute()
                or login_probe_status not in _PROBE_STATUSES
                or index_write_status not in {"published", "failed"}
                or requested_root is not None and type(requested_root) is not str
            ):
                raise CheckpointError("evidence index status binding is invalid")
            document = {
                "schema_version": INDEX_STATUS_SCHEMA,
                "authority": AUTHORITY,
                "pbs_jobid": normalize_job_id(job_id),
                "normalized_pbs_jobid": normalize_job_id(job_id),
                "submitted_at": submitted_at,
                "submission_nonce": _validate_nonce(nonce),
                "catalog_root": str(catalog),
                "evidence_root": str(effective),
                "requested_evidence_root": requested_root,
                "login_probe_status": login_probe_status,
                "index_write_status": index_write_status,
            }
            payload = _json_line(document, limit=_INDEX_MAX_BYTES)
            _ensure_payload(target, target.parent, (), payload)
            return True
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        return False


def try_create_index_status_bounded(
    path: os.PathLike[str] | str,
    *,
    timeout_s: float = _DIAGNOSTIC_IO_TIMEOUT_S,
    **fields: Any,
) -> bool:
    """Publish a submission sidecar through an isolated diagnostic child."""

    return _bounded_boolean_child(
        lambda: try_create_index_status(path, **fields), timeout_s=timeout_s,
    )


def load_index_status(
    path: os.PathLike[str] | str,
    *,
    job_id: str,
    nonce: str,
    submitted_at: int,
) -> dict[str, object]:
    target = Path(path)
    payload = _read_leaf(target, target.parent, (), _INDEX_MAX_BYTES)
    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointError("evidence index status is invalid JSON") from exc
    if (
        type(value) is not dict
        or set(value) != INDEX_STATUS_KEYS
        or value.get("schema_version") != INDEX_STATUS_SCHEMA
        or value.get("authority") != AUTHORITY
        or type(value.get("pbs_jobid")) is not str
        or normalize_job_id(value["pbs_jobid"]) != normalize_job_id(job_id)
        or value.get("normalized_pbs_jobid") != normalize_job_id(job_id)
        or value.get("submitted_at") != submitted_at
        or value.get("submission_nonce") != nonce
        or type(value.get("catalog_root")) is not str
        or not Path(value["catalog_root"]).is_absolute()
        or type(value.get("evidence_root")) is not str
        or not Path(value["evidence_root"]).is_absolute()
        or value.get("login_probe_status") not in _PROBE_STATUSES
        or value.get("index_write_status") not in {"published", "failed"}
        or value.get("requested_evidence_root") is not None
        and type(value.get("requested_evidence_root")) is not str
    ):
        raise CheckpointError("evidence index status binding mismatch")
    return value


def read_journal_prefix(path: os.PathLike[str] | str) -> tuple[list[dict[str, object]], bool]:
    journal = Path(path)
    if not journal.is_absolute():
        raise CheckpointError("journal path must be absolute")
    root = journal.parent
    payload = _read_leaf(journal, root, (), _JOURNAL_MAX_BYTES)
    return _decode_jsonl_prefix(payload)
