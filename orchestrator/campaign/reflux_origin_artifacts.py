"""Strict JSON and create-only writes for reflux-origin artifacts.

``O_EXCL`` prevents an existing false record from being overwritten; it does
not authenticate the first writer.  Another process able to write the evidence
root, including one running as the same UID, can place a consistent record at a
deterministic path before the honest producer, and an honest consumer may then
accept it.  This wiring is sound only under the operational assumption that the
trusted harness is the only writer to the evidence root.
"""
from __future__ import annotations

import json
import math
import os
import stat
from pathlib import Path
from typing import Any


__all__ = [
    "ArtifactError",
    "canonical_json_bytes",
    "strict_json_loads",
    "write_create_only",
    "write_json_create_only",
]


class ArtifactError(ValueError):
    """Fail-closed rejection of an artifact encoding or write operation."""


def _validate_json_value(value: object) -> None:
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ArtifactError("canonical JSON forbids non-finite numbers")
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_json_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ArtifactError("canonical JSON object keys must be strings")
            _validate_json_value(item)
        return
    raise ArtifactError(
        f"canonical JSON cannot encode value of type {type(value).__name__}"
    )


def canonical_json_bytes(value: object) -> bytes:
    """Return sorted, compact UTF-8 JSON bytes without a trailing LF."""

    try:
        _validate_json_value(value)
        text = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        return text.encode("utf-8")
    except ArtifactError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ArtifactError("canonical JSON encoding failed") from exc


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ArtifactError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def _reject_json_constant(token: str) -> None:
    raise ArtifactError(f"non-finite JSON number is forbidden: {token}")


def strict_json_loads(raw: bytes | str) -> object:
    """Parse exact canonical UTF-8 JSON with no duplicate or non-finite value."""

    try:
        if type(raw) is bytes:
            text = raw.decode("utf-8")
        elif type(raw) is str:
            raw.encode("utf-8")
            text = raw
        else:
            raise ArtifactError("strict JSON input must be bytes or str")
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
        _validate_json_value(value)
        if canonical_json_bytes(value) != text.encode("utf-8"):
            raise ArtifactError("strict JSON input is not canonical")
        return value
    except ArtifactError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ArtifactError("strict JSON parsing failed") from exc


def _normalized_target(
    root: Path,
    relative_path: Path,
) -> tuple[Path, Path]:
    try:
        root_input = Path(root)
        relative = Path(relative_path)
    except (TypeError, ValueError) as exc:
        raise ArtifactError("root and relative path must be path-like") from exc

    if relative.is_absolute() or relative == Path(".") or ".." in relative.parts:
        raise ArtifactError("artifact target must be a confined relative path")
    if not relative.name or "\x00" in os.fspath(relative):
        raise ArtifactError("artifact target must be a confined relative path")

    root_absolute = Path(os.path.abspath(root_input))
    try:
        root_info = os.lstat(root_absolute)
        if stat.S_ISLNK(root_info.st_mode):
            raise ArtifactError("artifact root is a symlink ancestor")
        if not stat.S_ISDIR(root_info.st_mode):
            raise ArtifactError("artifact root is not a directory")
        normalized_root = root_absolute.resolve(strict=True)
    except ArtifactError:
        raise
    except OSError as exc:
        raise ArtifactError("artifact root cannot be resolved") from exc

    target = Path(os.path.normpath(normalized_root / relative))
    if not target.is_relative_to(normalized_root) or target == normalized_root:
        raise ArtifactError("artifact target escapes its root")
    return normalized_root, target


def _check_no_symlink_ancestors(root: Path, target: Path) -> None:
    relative = target.relative_to(root)
    current = root
    for component in relative.parent.parts:
        current /= component
        try:
            info = os.lstat(current)
        except OSError as exc:
            raise ArtifactError("artifact parent directory does not exist") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ArtifactError(f"artifact has a symlink ancestor: {current}")
        if not stat.S_ISDIR(info.st_mode):
            raise ArtifactError("artifact ancestor is not a directory")


def _write_all(fd: int, raw: bytes) -> None:
    remaining = memoryview(raw)
    while remaining:
        written = os.write(fd, remaining)
        if written <= 0:
            raise OSError("artifact write did not advance")
        remaining = remaining[written:]


def _read_back(path: Path, identity: tuple[int, int]) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ArtifactError("O_NOFOLLOW is required for artifact read-back")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ArtifactError("cannot open artifact for read-back") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != identity:
            raise ArtifactError("artifact identity changed before read-back")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    except OSError as exc:
        raise ArtifactError("artifact read-back failed") from exc
    finally:
        os.close(fd)


def write_create_only(
    *,
    root: Path,
    relative_path: Path,
    raw: bytes,
) -> Path:
    """Create one confined artifact, persist it, and verify exact read-back."""

    if type(raw) is not bytes:
        raise ArtifactError("artifact payload must be immutable bytes")
    normalized_root, target = _normalized_target(root, relative_path)
    _check_no_symlink_ancestors(normalized_root, target)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ArtifactError("O_NOFOLLOW is required for artifact creation")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | nofollow
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        fd = os.open(target, flags, 0o600)
    except OSError as exc:
        raise ArtifactError("cannot create artifact exclusively") from exc
    try:
        _write_all(fd, raw)
        os.fsync(fd)
        info = os.fstat(fd)
        identity = (info.st_dev, info.st_ino)
    except OSError as exc:
        raise ArtifactError("artifact write or file fsync failed") from exc
    finally:
        os.close(fd)

    _check_no_symlink_ancestors(normalized_root, target)
    directory_flags = (
        os.O_RDONLY
        | nofollow
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        directory_fd = os.open(target.parent, directory_flags)
    except OSError as exc:
        raise ArtifactError("cannot open artifact parent directory") from exc
    try:
        os.fsync(directory_fd)
    except OSError as exc:
        raise ArtifactError("artifact parent directory fsync failed") from exc
    finally:
        os.close(directory_fd)

    if _read_back(target, identity) != raw:
        raise ArtifactError("artifact read-back mismatch")
    return target


def write_json_create_only(
    *,
    root: Path,
    relative_path: Path,
    value: object,
) -> Path:
    """Canonicalize a JSON value and create it with :func:`write_create_only`."""

    return write_create_only(
        root=root,
        relative_path=relative_path,
        raw=canonical_json_bytes(value),
    )
