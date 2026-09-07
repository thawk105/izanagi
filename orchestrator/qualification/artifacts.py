# -*- coding: utf-8 -*-
"""Root-bound qualification artifacts and evidence admission.

The writer only accepts relative paths below the exact T-126 persistent root.
It cannot create formal campaign names and never calls the campaign WAL writer.
"""
from __future__ import annotations

import hashlib
import fcntl
import json
import math
import os
import re
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from orchestrator.calibrator import perf_preflight as _perf_preflight

from ..campaign import campaign_lock
from ..verifier.commit_receipt import (
    QUALIFICATION_SINK,
    CommitReceiptError,
    validate_live_receipt,
    validate_serialized_receipt,
)

from .contract import (
    attempt_identity,
    canonical_json_bytes,
    protocol_sha256,
    series_identity,
)
from .retry_index import RetryIndexError, validate_retry_index


_HEX64 = re.compile(r"[0-9a-f]{64}")
_ATTEMPT = re.compile(r"[0-9a-f]{64}")
_FORBIDDEN_BASENAMES = frozenset(("campaign.lock", "loop_state.json", "wal.jsonl"))
_CAP_TOKEN = object()
_LAYOUT_TOKEN = object()
QUALIFICATION_SCHEMA_RELATIVE_PATHS = frozenset({
    "orchestrator/qualification/t126_marker_schema.json",
    "orchestrator/qualification/t126_event_schema.json",
    "orchestrator/qualification/t126_evaluation_event_schema.json",
    "orchestrator/qualification/t126_series_result_schema.json",
    "orchestrator/qualification/t126_final_receipt_schema.json",
    "orchestrator/qualification/t126_failure_receipt_schema.json",
})
_QUALIFICATION_SCHEMA_BYTES: dict[str, bytes] = {}
PERMANENT_NONRETRY_FAILURES = frozenset({
    "job-result-publication-failed",
    "job-result-accounting-mismatch",
})
_EVENT_STAGE_MAP = {
    "build_start": "qualification_build_start",
    "build_done": "qualification_build_done",
    "verify_done": "qualification_verify_done",
    "bench_done": "qualification_bench_done",
    "commit": "qualification_evaluation_terminal",
    "abort": "qualification_evaluation_rejected",
}


class QualificationArtifactError(RuntimeError):
    """Qualification artifact violates path, framing, schema, or evidence rules."""


class CreateTargetExistsError(QualificationArtifactError):
    """A safe create-only target already exists after namespace preflight."""


def _reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise QualificationArtifactError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(read_regular_file(path)).hexdigest()


def read_regular_file(path: Path) -> bytes:
    """Read one stable regular-file inode without following a final symlink."""
    return read_regular_file_with_identity(path)[0]


def read_regular_file_with_identity(
        path: Path) -> tuple[bytes, tuple[int, int, int, int]]:
    """Return stable bytes plus the exact inode identity used for the read."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise QualificationArtifactError(
            f"cannot open regular file {path}: {exc}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise QualificationArtifactError(
                f"artifact is not a regular file: {path}")
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
            raise QualificationArtifactError(
                f"artifact changed while reading: {path}")
        return b"".join(chunks), (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    finally:
        os.close(fd)


def file_record(path: Path, *, relative_to: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise QualificationArtifactError(f"required regular file missing: {path}")
    try:
        relative = path.relative_to(relative_to).as_posix()
    except ValueError as exc:
        raise QualificationArtifactError(f"file is outside closure root: {path}") from exc
    return {"path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)}


class QualificationWriteCapability:
    """Opaque root-bound write capability.  Issue via QualificationRoot only."""

    __slots__ = (
        "_root", "_root_identity", "_ancestor_identities", "_chain_identity",
        "_token", "_sealed",
    )

    def __init__(
            self, root: Path, root_identity: tuple[int, int],
            ancestor_identities: tuple[tuple[Path, int, int], ...],
            chain_identity: object, token: object):
        if token is not _CAP_TOKEN:
            raise TypeError("QualificationWriteCapability is issued by QualificationRoot")
        object.__setattr__(self, "_root", root)
        object.__setattr__(self, "_root_identity", root_identity)
        object.__setattr__(self, "_ancestor_identities", ancestor_identities)
        object.__setattr__(self, "_chain_identity", chain_identity)
        object.__setattr__(self, "_token", token)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False):
            raise AttributeError("QualificationWriteCapability is immutable")
        object.__setattr__(self, name, value)

    @property
    def root(self) -> Path:
        return self._root

    def assert_intact(self) -> None:
        if (type(self) is not QualificationWriteCapability
                or self._token is not _CAP_TOKEN
                or not isinstance(self._root, Path)
                or self._root.is_symlink()
                or not self._root.is_dir()):
            raise QualificationArtifactError("qualification capability is not intact")
        for path, expected_dev, expected_ino in self._ancestor_identities:
            try:
                current = path.lstat()
            except OSError as exc:
                raise QualificationArtifactError(
                    f"qualification capability ancestor is unavailable: {path}"
                ) from exc
            if (stat.S_ISLNK(current.st_mode)
                    or not stat.S_ISDIR(current.st_mode)
                    or (current.st_dev, current.st_ino)
                    != (expected_dev, expected_ino)):
                raise QualificationArtifactError(
                    f"qualification capability ancestor identity changed: {path}")
        stat_result = self._root.stat()
        if (stat_result.st_dev, stat_result.st_ino) != self._root_identity:
            raise QualificationArtifactError(
                "qualification capability root identity changed")


@dataclass(frozen=True, init=False)
class QualificationLayout:
    """Qualification layout; intentionally unrelated to CampaignLayout."""

    root: Path
    attempt_id: str
    _root_identity: tuple[int, int]
    _chain_identity: object
    _token: object

    def __init__(
            self, root: Path, attempt_id: str, root_identity: tuple[int, int],
            chain_identity: object, token: object):
        if token is not _LAYOUT_TOKEN:
            raise TypeError("QualificationLayout is issued by QualificationRoot")
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "attempt_id", attempt_id)
        object.__setattr__(self, "_root_identity", root_identity)
        object.__setattr__(self, "_chain_identity", chain_identity)
        object.__setattr__(self, "_token", token)

    def assert_bound(self, capability: QualificationWriteCapability) -> None:
        capability.assert_intact()
        if (type(self) is not QualificationLayout
                or self._token is not _LAYOUT_TOKEN
                or self.root != capability.root
                or self._root_identity != capability._root_identity
                or self._chain_identity is not capability._chain_identity):
            raise QualificationArtifactError(
                "qualification layout/capability chain mismatch")

    @property
    def attempt_dir(self) -> Path:
        return self.root / "attempts" / self.attempt_id

    def member_events_relpath(self, round_index: int, role: str) -> str:
        if type(round_index) is not int or round_index < 1:
            raise QualificationArtifactError("round index must be positive exact int")
        if role not in ("subject", "reference"):
            raise QualificationArtifactError("member role must be subject/reference")
        return (
            f"attempts/{self.attempt_id}/rounds/{round_index:04d}/"
            f"{role}/evaluation-events.jsonl"
        )

    @property
    def ledger_relpath(self) -> str:
        return f"attempts/{self.attempt_id}/series-ledger.jsonl"


class QualificationRoot:
    """Exact persistent namespace with symlink-resistant path validation."""

    def __init__(self, repo_root: Path | str, path: Path | str | None = None):
        repo = Path(repo_root)
        if repo.is_symlink() or not repo.is_dir():
            raise QualificationArtifactError("repo root must be a non-symlink directory")
        self.repo_root = repo.resolve()
        expected = self.repo_root / "output/env/pegasus/qualification/t126"
        candidate = expected if path is None else Path(path)
        if candidate.is_absolute():
            candidate_abs = candidate
        else:
            candidate_abs = self.repo_root / candidate
        if candidate_abs.absolute() != expected.absolute():
            raise QualificationArtifactError("qualification root is not the exact T-126 namespace")
        self.path = expected
        self._chain_identity = object()
        self._assert_existing_prefixes_no_symlink(self.path)

    def _assert_existing_prefixes_no_symlink(self, path: Path) -> None:
        current = self.repo_root
        try:
            parts = path.relative_to(self.repo_root).parts
        except ValueError as exc:
            raise QualificationArtifactError("path escapes repo root") from exc
        for part in parts:
            current = current / part
            if current.is_symlink():
                raise QualificationArtifactError(f"symlink path component rejected: {current}")

    def issue(self) -> QualificationWriteCapability:
        self._assert_existing_prefixes_no_symlink(self.path)
        current = self.repo_root
        for part in self.path.relative_to(self.repo_root).parts:
            current = current / part
            if current.is_symlink():
                raise QualificationArtifactError(
                    f"symlink path component rejected: {current}")
            try:
                current.mkdir(mode=0o700)
            except FileExistsError:
                if not current.is_dir() or current.is_symlink():
                    raise QualificationArtifactError(
                        f"unsafe qualification namespace: {current}")
        self._assert_existing_prefixes_no_symlink(self.path)
        root_stat = self.path.stat()
        ancestor_identities = []
        current = self.repo_root
        for part in ((), *(
                self.path.relative_to(self.repo_root).parts[:index]
                for index in range(
                    1, len(self.path.relative_to(self.repo_root).parts) + 1))):
            path = (
                self.repo_root if not part
                else self.repo_root.joinpath(*part))
            current_stat = path.lstat()
            if stat.S_ISLNK(current_stat.st_mode) or not stat.S_ISDIR(
                    current_stat.st_mode):
                raise QualificationArtifactError(
                    f"unsafe qualification namespace ancestor: {path}")
            ancestor_identities.append(
                (path, current_stat.st_dev, current_stat.st_ino))
        return QualificationWriteCapability(
            self.path, (root_stat.st_dev, root_stat.st_ino),
            tuple(ancestor_identities),
            self._chain_identity, _CAP_TOKEN,
        )

    def layout(self, attempt_id: str) -> QualificationLayout:
        if type(attempt_id) is not str or _ATTEMPT.fullmatch(attempt_id) is None:
            raise QualificationArtifactError("attempt id must be full lowercase sha256")
        if self.path.is_symlink() or not self.path.is_dir():
            raise QualificationArtifactError(
                "qualification root must be prepared before issuing a layout")
        root_stat = self.path.stat()
        return QualificationLayout(
            self.path, attempt_id, (root_stat.st_dev, root_stat.st_ino),
            self._chain_identity, _LAYOUT_TOKEN,
        )


def _validate_relative(relative: str) -> PurePosixPath:
    if type(relative) is not str or not relative or "\x00" in relative:
        raise QualificationArtifactError("artifact path must be a non-empty relative string")
    posix = PurePosixPath(relative)
    if posix.is_absolute() or any(part in ("", ".", "..") for part in posix.parts):
        raise QualificationArtifactError(f"unsafe relative artifact path: {relative!r}")
    if posix.name in _FORBIDDEN_BASENAMES:
        raise QualificationArtifactError(f"formal campaign artifact name is forbidden: {posix.name}")
    return posix


def _bound_path(capability: QualificationWriteCapability, relative: str) -> Path:
    if type(capability) is not QualificationWriteCapability:
        raise TypeError("a QualificationWriteCapability is required")
    capability.assert_intact()
    posix = _validate_relative(relative)
    path = capability.root.joinpath(*posix.parts)
    current = capability.root
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise QualificationArtifactError(f"symlink path component rejected: {current}")
    try:
        path.absolute().relative_to(capability.root.absolute())
    except ValueError as exc:
        raise QualificationArtifactError("artifact path escapes qualification root") from exc
    return path


def safe_relative_path(root: Path, relative: object, label: str) -> Path:
    """Resolve one safe relative path below ``root`` without following symlinks."""
    if type(relative) is not str:
        raise QualificationArtifactError(f"{label} path must be an exact string")
    posix = _validate_relative(relative)
    path = root.joinpath(*posix.parts)
    current = root
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise QualificationArtifactError(f"{label} path contains a symlink")
    try:
        path.absolute().relative_to(root.absolute())
    except ValueError as exc:
        raise QualificationArtifactError(f"{label} path escapes its root") from exc
    return path


def _mkdir_parents(capability: QualificationWriteCapability, path: Path) -> None:
    relative_parent = path.parent.relative_to(capability.root)
    current = capability.root
    if not current.exists():
        # The exact namespace ancestors were checked by QualificationRoot. mkdir
        # does not follow a final symlink because the final path did not exist.
        current.mkdir(parents=True, mode=0o700)
    for part in relative_parent.parts:
        current = current / part
        if current.is_symlink():
            raise QualificationArtifactError(f"symlink directory rejected: {current}")
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            if not current.is_dir() or current.is_symlink():
                raise QualificationArtifactError(f"unsafe artifact directory: {current}")


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def create_bytes(
        capability: QualificationWriteCapability, relative: str, data: bytes,
        *, fault_inject=None) -> Path:
    if type(data) is not bytes:
        raise TypeError("artifact data must be bytes")
    path = _bound_path(capability, relative)
    _mkdir_parents(capability, path)
    path = _bound_path(capability, relative)
    staging_prefix = f".{path.name}.create-"
    staging_pattern = re.compile(
        re.escape(staging_prefix) + r"[1-9][0-9]*-[0-9a-f]{16}")
    abandoned = [
        entry for entry in path.parent.iterdir()
        if entry.name.startswith(staging_prefix)]
    if (len(abandoned) > 1
            or any(staging_pattern.fullmatch(entry.name) is None
                   for entry in abandoned)):
        raise QualificationArtifactError(
            f"ambiguous abandoned create staging entries: {path}")
    stage = abandoned[0] if abandoned else None
    target_present = path.exists() or path.is_symlink()
    target_stat = path.lstat() if target_present else None
    stage_stat = stage.lstat() if stage is not None else None
    for current, expected_nlink in (
            (target_stat, 2 if stage is not None else 1),
            (stage_stat, 2 if target_present else 1)):
        if current is None:
            continue
        if (stat.S_ISLNK(current.st_mode)
                or not stat.S_ISREG(current.st_mode)
                or current.st_uid != os.getuid()
                or stat.S_IMODE(current.st_mode) != 0o600
                or current.st_nlink != expected_nlink):
            raise QualificationArtifactError(
                f"create staging owner/mode/nlink mismatch: {path}")
    if stage is not None and target_present:
        if ((stage_stat.st_dev, stage_stat.st_ino)
                != (target_stat.st_dev, target_stat.st_ino)
                or read_regular_file(stage) != read_regular_file(path)
                or read_regular_file(path) != data):
            raise QualificationArtifactError(
                f"create staging target inode/bytes mismatch: {path}")
    if stage is not None:
        if target_present:
            _fsync_dir(path.parent)
        stage.unlink()
        _fsync_dir(path.parent)
    if target_present:
        raise CreateTargetExistsError(
            f"create-only target already exists: {path}")
    capability.assert_intact()
    temporary = path.parent / (
        f".{path.name}.create-{os.getpid()}-{secrets.token_hex(8)}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(temporary, flags, 0o600)
    except OSError as exc:
        raise QualificationArtifactError(
            f"create-only staging failed: {path}: {exc}") from exc
    try:
        try:
            with os.fdopen(fd, "wb", closefd=False) as stream:
                stream.write(data)
                if fault_inject is not None:
                    fault_inject("after-write")
                stream.flush()
                os.fsync(fd)
                if fault_inject is not None:
                    fault_inject("after-fsync")
        finally:
            os.close(fd)
        capability.assert_intact()
        try:
            os.link(temporary, path, follow_symlinks=False)
            if fault_inject is not None:
                fault_inject("after-link")
            _fsync_dir(path.parent)
        except FileExistsError as exc:
            raise CreateTargetExistsError(
                f"create-only target already exists: {path}") from exc
        except OSError as exc:
            raise QualificationArtifactError(
                f"create-only publish failed: {path}: {exc}") from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    _fsync_dir(path.parent)
    return path


def create_or_verify_bytes(
        capability: QualificationWriteCapability, relative: str, data: bytes) -> Path:
    """Create once, or reuse only an existing byte-for-byte identical file."""
    try:
        return create_bytes(capability, relative, data)
    except CreateTargetExistsError:
        path = _bound_path(capability, relative)
        try:
            current = path.lstat()
        except OSError:
            raise
        if (stat.S_ISLNK(current.st_mode)
                or not stat.S_ISREG(current.st_mode)
                or current.st_uid != os.getuid()
                or stat.S_IMODE(current.st_mode) != 0o600
                or current.st_nlink != 1):
            raise QualificationArtifactError(
                f"existing create-only target is unsafe: {path}")
        if read_regular_file(path) != data:
            raise QualificationArtifactError(
                f"existing create-only artifact differs: {path}")
        return path


def create_or_verify_json(
        capability: QualificationWriteCapability, relative: str,
        value: Mapping[str, Any]) -> Path:
    return create_or_verify_bytes(
        capability, relative, canonical_json_bytes(dict(value)) + b"\n")


def create_json(
        capability: QualificationWriteCapability, relative: str,
        value: Mapping[str, Any]) -> Path:
    return create_bytes(capability, relative, canonical_json_bytes(dict(value)) + b"\n")


def append_jsonl(
        capability: QualificationWriteCapability, relative: str,
        value: Mapping[str, Any]) -> Path:
    path = _bound_path(capability, relative)
    _mkdir_parents(capability, path)
    path = _bound_path(capability, relative)
    encoded = canonical_json_bytes(dict(value)) + b"\n"
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise QualificationArtifactError(f"append failed: {path}: {exc}") from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise QualificationArtifactError("event sink is not a regular file")
        os.write(fd, encoded)
        os.fsync(fd)
    finally:
        os.close(fd)
    return path


def load_json_strict(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise QualificationArtifactError(f"JSON artifact is not a regular file: {path}")
    try:
        raw = read_regular_file(path)
        if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
            raise QualificationArtifactError(f"JSON newline framing mismatch: {path}")
        value = json.loads(raw, object_pairs_hook=_reject_duplicates)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualificationArtifactError(f"invalid JSON artifact: {path}: {exc}") from exc
    if type(value) is not dict:
        raise QualificationArtifactError(f"JSON artifact must be an object: {path}")
    if canonical_json_bytes(value) + b"\n" != raw:
        raise QualificationArtifactError(f"JSON artifact is not canonical: {path}")
    return value


def load_source_json(path: Path) -> dict[str, Any]:
    """Read immutable historical JSON bytes without imposing new framing.

    The full-file SHA-256 is checked by the caller.  Historical campaign.lock
    predates the qualification newline convention, so only duplicate keys,
    non-finite values, decoding, and object shape are enforced here.
    """
    if path.is_symlink() or not path.is_file():
        raise QualificationArtifactError(f"source JSON is not a regular file: {path}")
    try:
        value = json.loads(
            read_regular_file(path),
            object_pairs_hook=_reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                QualificationArtifactError(f"non-finite JSON constant: {token}")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualificationArtifactError(f"invalid source JSON: {path}: {exc}") from exc
    if type(value) is not dict:
        raise QualificationArtifactError(f"source JSON must be an object: {path}")
    return value


def load_jsonl_strict(path: Path) -> list[dict[str, Any]]:
    if path.is_symlink() or not path.is_file():
        raise QualificationArtifactError(f"JSONL artifact is not a regular file: {path}")
    try:
        raw = read_regular_file(path)
    except OSError as exc:
        raise QualificationArtifactError(f"cannot read JSONL artifact: {path}: {exc}") from exc
    if not raw or not raw.endswith(b"\n") or b"\n\n" in raw:
        raise QualificationArtifactError(f"JSONL framing mismatch: {path}")
    records = []
    for lineno, line in enumerate(raw.splitlines(), 1):
        try:
            value = json.loads(line, object_pairs_hook=_reject_duplicates)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise QualificationArtifactError(
                f"invalid JSONL record {path}:{lineno}: {exc}") from exc
        if type(value) is not dict or canonical_json_bytes(value) != line:
            raise QualificationArtifactError(
                f"non-canonical JSONL record {path}:{lineno}")
        records.append(value)
    return records


def load_source_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read historical JSONL with strict framing/duplicates but original key order."""
    if path.is_symlink() or not path.is_file():
        raise QualificationArtifactError(f"source JSONL is not a regular file: {path}")
    raw = read_regular_file(path)
    if not raw or not raw.endswith(b"\n") or b"\n\n" in raw:
        raise QualificationArtifactError(f"source JSONL framing mismatch: {path}")
    records = []
    for lineno, line in enumerate(raw.splitlines(), 1):
        try:
            value = json.loads(
                line,
                object_pairs_hook=_reject_duplicates,
                parse_constant=lambda token: (_ for _ in ()).throw(
                    QualificationArtifactError(f"non-finite JSON constant: {token}")
                ),
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise QualificationArtifactError(
                f"invalid source JSONL record {path}:{lineno}: {exc}") from exc
        if type(value) is not dict:
            raise QualificationArtifactError(
                f"source JSONL record must be an object: {path}:{lineno}")
        records.append(value)
    return records


def qualification_schema_bytes(schema_name: str) -> bytes:
    """Return the process-stable bytes for one bundled qualification schema."""
    if (type(schema_name) is not str
            or "/" in schema_name or not schema_name.endswith("_schema.json")):
        raise QualificationArtifactError("schema name is unsafe")
    if schema_name not in _QUALIFICATION_SCHEMA_BYTES:
        schema_path = Path(__file__).resolve().parent / schema_name
        _QUALIFICATION_SCHEMA_BYTES[schema_name] = read_regular_file(
            schema_path)
    return _QUALIFICATION_SCHEMA_BYTES[schema_name]


def validate_json_schema(schema_name: str, value: Mapping[str, Any]) -> None:
    """Validate an actual produced artifact against a bundled exact schema."""
    schema_bytes = qualification_schema_bytes(schema_name)
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:
        raise QualificationArtifactError(
            "jsonschema is required for qualification artifacts") from exc
    try:
        schema = json.loads(schema_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise QualificationArtifactError(
            f"bundled schema is invalid: {schema_name}") from exc
    errors = sorted(
        Draft7Validator(schema).iter_errors(dict(value)),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        raise QualificationArtifactError(
            f"{schema_name} validation failed at "
            f"{list(first.absolute_path)}: {first.message}")


def create_attempt(
        root: QualificationRoot, capability: QualificationWriteCapability,
        *, series_id: str, attempt_id: str) -> QualificationLayout:
    capability.assert_intact()
    if (capability.root != root.path
            or capability._chain_identity is not root._chain_identity):
        raise QualificationArtifactError("capability/root mismatch")
    if _HEX64.fullmatch(series_id) is None or _HEX64.fullmatch(attempt_id) is None:
        raise QualificationArtifactError("series/attempt IDs must be full sha256")
    layout = root.layout(attempt_id)
    attempt_relative = f"attempts/{attempt_id}"
    attempt_path = _bound_path(capability, attempt_relative)
    _mkdir_parents(capability, attempt_path / "placeholder")
    if any(attempt_path.iterdir()):
        raise QualificationArtifactError("attempt directory is not create-only/empty")
    marker = {
        "schema_version": "t126-qualification-marker/v1",
        "qualification_lineage": "t126-only",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "qualification_series_id": series_id,
        "qualification_attempt_id": attempt_id,
    }
    create_json(capability, f"{attempt_relative}/qualification-marker.json", marker)
    return layout


class QualificationEventSink:
    """Pipeline event adapter that emits a non-formal qualification schema."""

    __slots__ = (
        "_capability", "_layout", "_round_index", "_role", "_relative",
        "_source_lock_identity_sha256", "_sealed",
    )

    def __init__(
            self, capability: QualificationWriteCapability, layout: QualificationLayout,
            *, round_index: int, role: str,
            source_lock_identity_sha256: str | None = None):
        if (type(capability) is not QualificationWriteCapability
                or type(layout) is not QualificationLayout):
            raise TypeError("exact qualification capability/layout are required")
        layout.assert_bound(capability)
        object.__setattr__(self, "_capability", capability)
        object.__setattr__(self, "_layout", layout)
        object.__setattr__(self, "_round_index", round_index)
        object.__setattr__(self, "_role", role)
        if (source_lock_identity_sha256 is not None
                and (type(source_lock_identity_sha256) is not str
                     or _HEX64.fullmatch(source_lock_identity_sha256) is None)):
            raise QualificationArtifactError(
                "source campaign lock identity must be lowercase sha256")
        object.__setattr__(
            self, "_source_lock_identity_sha256", source_lock_identity_sha256)
        object.__setattr__(
            self, "_relative", layout.member_events_relpath(round_index, role))
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False):
            raise AttributeError("QualificationEventSink is immutable")
        object.__setattr__(self, name, value)

    @property
    def layout(self) -> QualificationLayout:
        return self._layout

    @property
    def capability(self) -> QualificationWriteCapability:
        return self._capability

    @property
    def commit_lock_identity_sha256(self) -> str:
        value = self._source_lock_identity_sha256
        if value is None:
            raise QualificationArtifactError(
                "qualification sink has no source campaign lock identity")
        return value

    def assert_pipeline_binding(self, layout: object) -> None:
        """Authenticate the complete qualification chain before pipeline writes."""
        if type(self) is not QualificationEventSink:
            raise QualificationArtifactError(
                "qualification sink must have exact type")
        if layout is not self._layout or type(layout) is not QualificationLayout:
            raise QualificationArtifactError(
                "pipeline layout does not match qualification sink")
        self._layout.assert_bound(self._capability)
        expected_relative = self._layout.member_events_relpath(
            self._round_index, self._role)
        if self._relative != expected_relative:
            raise QualificationArtifactError(
                "qualification sink relative path is not layout-derived")
        expected_attempt = self._capability.root / "attempts" / self._layout.attempt_id
        if (self._layout.attempt_dir != expected_attempt
                or expected_attempt.is_symlink()
                or not expected_attempt.is_dir()):
            raise QualificationArtifactError(
                "qualification attempt root identity is invalid")
        marker = load_json_strict(expected_attempt / "qualification-marker.json")
        if (marker.get("schema_version") != "t126-qualification-marker/v1"
                or marker.get("qualification_lineage") != "t126-only"
                or marker.get("qualification_attempt_id") != self._layout.attempt_id):
            raise QualificationArtifactError(
                "qualification attempt marker identity mismatch")

    def emit(
            self, layout, variant: str, stage: str, env_tag: str,
            payload: Mapping[str, Any], *, commit_receipt=None,
    ) -> None:
        self.assert_pipeline_binding(layout)
        if stage != "commit" and commit_receipt is not None:
            raise QualificationArtifactError(
                "commit receipt supplied for non-COMMIT qualification event")
        expected_relative = self._layout.member_events_relpath(
            self._round_index, self._role)
        event_path = self._capability.root.joinpath(
            *PurePosixPath(expected_relative).parts)
        try:
            evaluation_stage = _EVENT_STAGE_MAP[stage]
        except KeyError as exc:
            raise QualificationArtifactError(f"unknown pipeline stage: {stage}") from exc
        path = _bound_path(self._capability, expected_relative)
        _mkdir_parents(self._capability, path)
        path = _bound_path(self._capability, expected_relative)
        flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
        except OSError as exc:
            raise QualificationArtifactError(f"append failed: {path}: {exc}") from exc
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise QualificationArtifactError("event sink is not a regular file")
            raw = os.pread(fd, info.st_size, 0)
            if len(raw) != info.st_size:
                raise QualificationArtifactError(
                    "qualification event ledger changed during locked read")
            existing = []
            if raw:
                if not raw.endswith(b"\n"):
                    raise QualificationArtifactError(
                        "qualification event ledger is not newline terminated")
                for line in raw.splitlines():
                    try:
                        prior = json.loads(
                            line, object_pairs_hook=_reject_duplicates)
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise QualificationArtifactError(
                            "qualification event ledger JSON is invalid") from exc
                    if (type(prior) is not dict
                            or canonical_json_bytes(prior) != line):
                        raise QualificationArtifactError(
                            "qualification event ledger is not canonical JSONL")
                    existing.append(prior)
            for index, prior in enumerate(existing):
                if (prior.get("event_index") != index
                        or prior.get("round_index") != self._round_index
                        or prior.get("member_role") != self._role
                        or prior.get("qualification_lineage") != "t126-only"):
                    raise QualificationArtifactError(
                        "qualification sink existing event sequence is not exact")
            event_index = len(existing)
            serialized_receipt = None
            if stage == "commit":
                try:
                    serialized_receipt = validate_live_receipt(
                        commit_receipt,
                        sink_kind=QUALIFICATION_SINK,
                        lock_identity_sha256=self.commit_lock_identity_sha256,
                        variant=variant,
                        terminal_payload=dict(payload),
                    )
                except CommitReceiptError as exc:
                    raise QualificationArtifactError(str(exc)) from exc
                consumed = {
                    row["commit_verification_receipt"]["receipt_id"]
                    for row in existing
                    if type(row.get("commit_verification_receipt")) is dict
                    and type(row["commit_verification_receipt"].get("receipt_id")) is str
                }
                if serialized_receipt["receipt_id"] in consumed:
                    raise QualificationArtifactError(
                        "commit receipt was already consumed by this event ledger")
            payload_bytes = canonical_json_bytes(dict(payload))
            record = {
                "schema_version": "t126-qualification-evaluation-event/v1",
                "qualification_lineage": "t126-only",
                "event_index": event_index,
                "round_index": self._round_index,
                "member_role": self._role,
                "event_type": "member_evaluation_event",
                "evaluation_stage": evaluation_stage,
                "evaluation_wal_key": variant,
                "env_tag": env_tag,
                "payload": {
                    "canonical_json": payload_bytes.decode("ascii"),
                    "sha256": sha256_bytes(payload_bytes),
                },
                "commit_verification_receipt": serialized_receipt,
            }
            validate_json_schema("t126_evaluation_event_schema.json", record)
            encoded = canonical_json_bytes(record) + b"\n"
            written = 0
            while written < len(encoded):
                count = os.write(fd, encoded[written:])
                if count <= 0:
                    raise QualificationArtifactError(
                        "qualification event append made no progress")
                written += count
            os.fsync(fd)
        except OSError as exc:
            raise QualificationArtifactError(f"append failed: {path}: {exc}") from exc
        finally:
            os.close(fd)


def snapshot_source(
        capability: QualificationWriteCapability, source: Path, relative: str,
        *, expected_sha256: str) -> dict[str, Any]:
    if source.is_symlink() or not source.is_file():
        raise QualificationArtifactError(f"source snapshot input is invalid: {source}")
    data = read_regular_file(source)
    actual = sha256_bytes(data)
    if actual != expected_sha256:
        raise QualificationArtifactError(
            f"source snapshot hash mismatch: expected={expected_sha256} actual={actual}")
    path = create_bytes(capability, relative, data)
    return {"path": relative, "size": len(data), "sha256": sha256_file(path)}


def select_source_pair(repo_root: Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the historical source bytes and selected five-stage members."""
    source = protocol["source"]
    lock_path = repo_root / source["campaign_lock_path"]
    wal_path = repo_root / source["wal_path"]
    if sha256_file(lock_path) != source["campaign_lock_sha256"]:
        raise QualificationArtifactError("source campaign.lock hash mismatch")
    if sha256_file(wal_path) != source["wal_sha256"]:
        raise QualificationArtifactError("source WAL hash mismatch")
    try:
        lock_text = read_regular_file(lock_path).decode("utf-8")
        lock_identity = campaign_lock.decode_campaign_lock(lock_text).identity
    except (UnicodeDecodeError, campaign_lock.CampaignLockCodecError) as exc:
        raise QualificationArtifactError(
            "source campaign.lock schema is invalid"
        ) from exc
    records = load_source_jsonl(wal_path)
    if lock_identity.get("ccbench_commit") != source["historical_ccbench_commit"]:
        raise QualificationArtifactError("source historical CCBench commit mismatch")
    selected = {}
    for role in ("subject", "reference"):
        expected = source["members"][role]
        events = [record for record in records
                  if record.get("variant") == expected["source_wal_variant"]]
        if [event.get("stage") for event in events] != source["required_stage_order"]:
            raise QualificationArtifactError(f"{role} source stage topology mismatch")
        if events[0].get("payload", {}).get("genome") != expected["genome"]:
            raise QualificationArtifactError(f"{role} source genome mismatch")
        verify = events[2].get("payload", {})
        if (verify.get("certified") is not True
                or verify.get("anomalies") != 0
                or type(verify.get("commits")) is not int
                or verify["commits"] <= 0):
            raise QualificationArtifactError(f"{role} historical verify evidence invalid")
        bench = events[3].get("payload", {})
        tps = bench.get("tps")
        if (type(tps) is not list or len(tps) != 5
                or any(isinstance(item, bool) or not isinstance(item, (int, float))
                       or not math.isfinite(float(item)) or item <= 0 for item in tps)
                or bench.get("median_tps") != expected["historical_median_tps"]
                or bench.get("unstable") is not False):
            raise QualificationArtifactError(f"{role} historical bench evidence invalid")
        commit = events[4].get("payload", {})
        if commit.get("fitness_tps") != expected["historical_median_tps"]:
            raise QualificationArtifactError(f"{role} source commit/bench mismatch")
        selected[role] = {
            "source_wal_variant": expected["source_wal_variant"],
            "genome": expected["genome"],
            "historical_median_tps": expected["historical_median_tps"],
        }
    return {"lock": lock_identity, "members": selected}


def validate_member_evidence(
        records: Sequence[Mapping[str, Any]], *, expected_role: str,
        expected_round: int, expected_perf_observation: object,
        expected_lock_identity_sha256: str,
        expected_reps: int = 5) -> dict[str, Any]:
    """Admit one live member only with full build/verify/bench evidence."""
    if not records:
        raise QualificationArtifactError("member evaluation events are empty")
    for index, record in enumerate(records):
        required = {
            "schema_version", "qualification_lineage", "event_index",
            "round_index", "member_role", "event_type", "evaluation_stage",
            "evaluation_wal_key", "env_tag", "payload",
            "commit_verification_receipt",
        }
        if type(record) is not dict or set(record) != required:
            raise QualificationArtifactError("member event key set mismatch")
        if (record["schema_version"] != "t126-qualification-evaluation-event/v1"
                or record["qualification_lineage"] != "t126-only"
                or record["event_index"] != index
                or record["round_index"] != expected_round
                or record["member_role"] != expected_role
                or record["event_type"] != "member_evaluation_event"
                or record["env_tag"] != "pegasus"
                or type(record["payload"]) is not dict
                or set(record["payload"]) != {"canonical_json", "sha256"}
                or (index < len(records) - 1
                    and record["commit_verification_receipt"] is not None)):
            raise QualificationArtifactError("member event identity/schema mismatch")
    decoded_payloads = []
    for record in records:
        envelope = record["payload"]
        if (type(envelope["canonical_json"]) is not str
                or type(envelope["sha256"]) is not str
                or _HEX64.fullmatch(envelope["sha256"]) is None
                or sha256_bytes(envelope["canonical_json"].encode("ascii"))
                != envelope["sha256"]):
            raise QualificationArtifactError(
                "member event payload envelope hash mismatch")
        try:
            payload = json.loads(
                envelope["canonical_json"], object_pairs_hook=_reject_duplicates)
        except (UnicodeEncodeError, json.JSONDecodeError) as exc:
            raise QualificationArtifactError(
                "member event payload canonical JSON is invalid") from exc
        if (type(payload) is not dict
                or canonical_json_bytes(payload).decode("ascii")
                != envelope["canonical_json"]):
            raise QualificationArtifactError(
                "member event payload is not canonical object JSON")
        decoded_payloads.append(payload)
    stages = [record["evaluation_stage"] for record in records]
    if stages != [
            "qualification_build_start", "qualification_build_done",
            "qualification_verify_done", "qualification_verify_done",
            "qualification_bench_done", "qualification_evaluation_terminal"]:
        raise QualificationArtifactError("member evaluation stage topology mismatch")
    wal_keys = {record["evaluation_wal_key"] for record in records}
    if len(wal_keys) != 1 or not next(iter(wal_keys)):
        raise QualificationArtifactError("member evaluation identity key is not exact")
    build = decoded_payloads[1]
    trace_hash = build.get("trace_bin_sha256")
    perf_hash = build.get("perf_bin_sha256")
    if (_HEX64.fullmatch(trace_hash or "") is None
            or _HEX64.fullmatch(perf_hash or "") is None
            or trace_hash == perf_hash):
        raise QualificationArtifactError("trace/perf binary evidence missing or not distinct")
    verify_rows = [decoded_payloads[2], decoded_payloads[3]]
    if [row.get("workload", {}).get("tag") for row in verify_rows] != ["legacy", "s2"]:
        raise QualificationArtifactError("missing exact legacy+S2 evidence")
    exact_flags = {
        "legacy": [
            "-ycsb_tuple_num=200", "-ycsb_zipf_skew=0.9",
            "-ycsb_rratio=50", "-ycsb_rmw=true", "-ycsb_max_ope=5",
            "-thread_num=4", "-extime=1", "-clocks_per_us=2100",
        ],
        "s2": [
            "-ycsb_tuple_num=1000000", "-ycsb_zipf_skew=0.9",
            "-ycsb_rratio=50", "-ycsb_rmw=false", "-ycsb_max_ope=10",
            "-thread_num=48", "-extime=3", "-clocks_per_us=2100",
        ],
    }
    for row in verify_rows:
        tag = row.get("workload", {}).get("tag")
        argv = row.get("argv")
        if (row.get("certified") is not True
                or type(row.get("commits")) is not int or row["commits"] <= 0
                or type(row.get("aborts")) is not int or row["aborts"] <= 0
                or row.get("anomalies") != 0
                or type(argv) is not list or not argv
                or type(argv[0]) is not str or not argv[0]
                or argv[1:] != exact_flags.get(tag)
                or row.get("binary_sha256") != trace_hash):
            raise QualificationArtifactError("verify runtime evidence is incomplete")
    bench = decoded_payloads[4]
    if expected_perf_observation is None:
        if "perf_observation" in bench:
            raise QualificationArtifactError(
                "member bench perf observation disagrees with prologue")
    else:
        try:
            normalized_observation = _perf_preflight.validate_perf_observation(
                expected_perf_observation,
                run_cmd=bench.get("run_cmd"),
                leading_indicators=bench.get("leading_indicators"),
            )
            if (normalized_observation["use_perf"] is not False
                    or bench.get("perf_observation") != normalized_observation
                    or not _perf_preflight.perf_claim_allowed(
                        normalized_observation, "throughput",
                        run_cmd=bench.get("run_cmd"),
                        leading_indicators=bench.get("leading_indicators"),
                    )):
                raise QualificationArtifactError(
                    "member bench perf observation disagrees with prologue")
        except _perf_preflight.PerfPreflightError as exc:
            raise QualificationArtifactError(
                "member bench perf observation disagrees with prologue"
            ) from exc
    tps = bench.get("tps")
    rcs = bench.get("rep_returncodes")
    if (bench.get("settled") is not True
            or bench.get("unstable") is not False
            or bench.get("rounds") != 1
            or type(tps) is not list or len(tps) != expected_reps
            or any(isinstance(item, bool) or not isinstance(item, (int, float))
                   or not math.isfinite(float(item)) or item <= 0 for item in tps)
            or rcs != [0] * expected_reps):
        raise QualificationArtifactError("bench reps/rc/settled evidence is incomplete")
    terminal = decoded_payloads[5]
    try:
        validate_serialized_receipt(
            records[5]["commit_verification_receipt"],
            sink_kind=QUALIFICATION_SINK,
            lock_identity_sha256=expected_lock_identity_sha256,
            variant=records[5]["evaluation_wal_key"],
            terminal_payload=terminal,
        )
    except CommitReceiptError as exc:
        raise QualificationArtifactError(str(exc)) from exc
    if terminal.get("verify_configs") != ["legacy", "s2"]:
        raise QualificationArtifactError("evaluation terminal lacks legacy+S2 conjunction")
    median = bench.get("median_tps")
    if (isinstance(median, bool) or not isinstance(median, (int, float))
            or not math.isfinite(float(median)) or median <= 0
            or terminal.get("fitness_tps") != median):
        raise QualificationArtifactError("bench/terminal median evidence mismatch")
    return {
        "evaluation_wal_key": records[0]["evaluation_wal_key"],
        "median_tps": float(median),
        "trace_bin_sha256": trace_hash,
        "perf_bin_sha256": perf_hash,
        "verify_order": ["legacy", "s2"],
        "settled": True,
        "rep_returncodes": list(rcs),
    }


def verify_manifest_closure(
        root: Path, manifest: Sequence[Mapping[str, Any]], *,
        excluded_names: Iterable[str] = ()) -> None:
    """Require exact hash/size coverage of all regular files below ``root``."""
    if root.is_symlink() or not root.is_dir():
        raise QualificationArtifactError("closure root must be a non-symlink directory")
    excluded = set(excluded_names)
    expected: dict[str, tuple[int, str]] = {}
    for row in manifest:
        if type(row) is not dict or set(row) != {"path", "size", "sha256"}:
            raise QualificationArtifactError("manifest record key set mismatch")
        relative = _validate_relative(row["path"]).as_posix()
        if relative in expected:
            raise QualificationArtifactError("manifest has duplicate path")
        if (type(row["size"]) is not int or row["size"] < 0
                or type(row["sha256"]) is not str
                or _HEX64.fullmatch(row["sha256"]) is None):
            raise QualificationArtifactError("manifest size/hash is invalid")
        expected[relative] = (row["size"], row["sha256"])
    actual = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise QualificationArtifactError(f"closure contains symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        actual[relative] = (path.stat().st_size, sha256_file(path))
    if actual != expected:
        missing = sorted(set(actual) - set(expected))
        extra = sorted(set(expected) - set(actual))
        bad = sorted(key for key in set(actual) & set(expected)
                     if actual[key] != expected[key])
        raise QualificationArtifactError(
            f"manifest closure mismatch: unreferenced={missing} missing={extra} bad={bad}")


def verify_manifest_entries(
        root: Path, manifest: Sequence[Mapping[str, Any]]) -> None:
    """Verify every recorded entry without admitting an unrecorded entry.

    This is used for the in-job manifest after the immutable series result has
    been written: job-result and post-job evidence are expected to be added
    later and are covered by the phase-two closure manifest instead.
    """
    seen = set()
    for row in manifest:
        if type(row) is not dict or set(row) != {"path", "size", "sha256"}:
            raise QualificationArtifactError("manifest record key set mismatch")
        relative = _validate_relative(row["path"]).as_posix()
        if relative in seen:
            raise QualificationArtifactError("manifest has duplicate path")
        seen.add(relative)
        path = root.joinpath(*PurePosixPath(relative).parts)
        actual = file_record(path, relative_to=root)
        if actual != row:
            raise QualificationArtifactError(
                f"manifest entry hash/size mismatch: {relative}")


@dataclass(frozen=True)
class ReceiptVerification:
    integrity_status: str
    execution_integrity: str
    terminal: str | None
    errors: tuple[str, ...] = ()

    def __bool__(self):
        raise TypeError("ReceiptVerification has no truth value; inspect integrity_status explicitly")


def validate_retry_history(
        attempts: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any]) -> bool:
    """Return retry eligibility; reject outcome-dependent or excess retries."""
    retry = protocol["retry"]
    if len(attempts) > retry["max_retries"] + 1:
        raise QualificationArtifactError("attempt count exceeds retry limit")
    for index, attempt in enumerate(attempts):
        required = {"attempt_id", "observations_recorded", "terminal", "failure_reason"}
        if type(attempt) is not dict or set(attempt) != required:
            raise QualificationArtifactError("retry history record key set mismatch")
        observations = attempt["observations_recorded"]
        if type(observations) is not int or observations < 0:
            raise QualificationArtifactError("retry observation count is invalid")
        if index < len(attempts) - 1:
            if observations != 0 or attempt["terminal"] is not None:
                raise QualificationArtifactError("retry after first observation/terminal is forbidden")
            if (attempt["failure_reason"] in PERMANENT_NONRETRY_FAILURES
                    or attempt["failure_reason"]
                    not in retry["eligible_reasons"]):
                raise QualificationArtifactError("retry reason is not pre-registered")
    last = attempts[-1] if attempts else None
    return bool(
        last is not None
        and last["observations_recorded"] == 0
        and last["terminal"] is None
        and last["failure_reason"] not in PERMANENT_NONRETRY_FAILURES
        and last["failure_reason"] in retry["eligible_reasons"]
        and len(attempts) <= retry["max_retries"]
    )


def validate_failure_receipt_for_retry(
        receipt_path: Path, repo_root: Path,
        protocol: Mapping[str, Any]) -> dict[str, Any]:
    """Admit only an intact, namespace-bound, pre-observation failure receipt."""
    repo = repo_root.resolve()
    expected_attempts = (
        repo / "output/env/pegasus/qualification/t126/attempts")
    if receipt_path.is_symlink():
        raise QualificationArtifactError("retry receipt symlink is forbidden")
    receipt = receipt_path.resolve(strict=True)
    try:
        relative = receipt.relative_to(expected_attempts)
    except ValueError as exc:
        raise QualificationArtifactError(
            "retry receipt is outside qualification attempts") from exc
    if (len(relative.parts) != 2
            or relative.name != "attempt-failure-receipt.json"
            or _ATTEMPT.fullmatch(relative.parts[0]) is None):
        raise QualificationArtifactError("retry receipt path/identity mismatch")
    value = load_json_strict(receipt)
    required = {
        "schema_version", "qualification_lineage", "authority",
        "hold_enforced", "qualification_series_id",
        "qualification_attempt_id", "job_id", "retry_index",
        "scheduler_exit_status", "submission_receipt", "job_result",
        "submission_evidence_kind", "qsub_binding",
        "scheduler_stdout", "scheduler_stderr", "accounting",
        "closure_manifest", "attempt_phase", "failure_class",
        "observations_recorded", "retry_eligible",
    }
    try:
        retry_index = validate_retry_index(value.get("retry_index"))
    except RetryIndexError as exc:
        raise QualificationArtifactError(
            "failure receipt retry index is invalid") from exc
    if (set(value) != required
            or value["schema_version"]
            != "t126-qualification-attempt-failure-receipt/v1"
            or value["qualification_lineage"] != "t126-only"
            or value["authority"] != "evidence-only/no-promotion"
            or value["hold_enforced"] is not False
            or value["qualification_attempt_id"] != relative.parts[0]
            or _HEX64.fullmatch(value["qualification_series_id"]) is None
            or retry_index != 0
            or value["observations_recorded"] != 0
            or value["retry_eligible"] is not True
            or value["failure_class"] in PERMANENT_NONRETRY_FAILURES
            or value["failure_class"] not in protocol["retry"]["eligible_reasons"]):
        raise QualificationArtifactError("failure receipt is not retry-admissible")
    attempt_dir = receipt.parent
    if ((attempt_dir / "series-result.json").exists()
            or (attempt_dir / "final-qualification-receipt.json").exists()):
        raise QualificationArtifactError(
            "terminal/final attempt cannot be retried")
    marker = load_json_strict(attempt_dir / "qualification-marker.json")
    series_preimage = load_json_strict(attempt_dir / "series-identity.json")
    attempt_preimage = load_json_strict(attempt_dir / "attempt-identity.json")
    if (series_identity(series_preimage) != value["qualification_series_id"]
            or attempt_identity(attempt_preimage)
            != value["qualification_attempt_id"]
            or marker.get("qualification_series_id")
            != value["qualification_series_id"]
            or marker.get("qualification_attempt_id")
            != value["qualification_attempt_id"]
            or series_preimage.get("protocol_sha256")
            != protocol_sha256(protocol)):
        raise QualificationArtifactError(
            "retry receipt canonical identity mismatch")
    from .collector import verify_post_job_receipt
    verified = verify_post_job_receipt(receipt, repo_root=repo)
    if verified.integrity_status != "valid":
        raise QualificationArtifactError(
            "failure receipt post-job verification failed: "
            + "; ".join(verified.errors))
    from .attempt_ledger import SeriesAttemptLedger
    ledger = SeriesAttemptLedger(
        QualificationRoot(repo).issue(), value["qualification_series_id"],
        protocol["retry"]["eligible_reasons"])
    replay = ledger.replay
    if (replay.state != "initial_failed"
            or replay.last_attempt_id != value["qualification_attempt_id"]
            or replay.observations_recorded != 0
            or replay.failure_class != value["failure_class"]):
        raise QualificationArtifactError(
            "failure receipt is not the canonical initial ledger outcome")
    return value
