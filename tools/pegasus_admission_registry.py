"""Pegasus login admission registry の canonical loader。"""
from __future__ import annotations

import json
import os
import stat
import unicodedata


__all__ = (
    "REGISTRY_RELATIVE_PATH",
    "AdmissionRegistryError",
    "load_admission_registry",
)

REGISTRY_RELATIVE_PATH = "tools/pegasus/admission_registry.json"

_SCHEMA_VERSION = "pegasus-admission-registry/v1"
_MAX_REGISTRY_BYTES = 1024 * 1024
_ENTRY_FIELDS = ("class", "reason", "primary_gate", "evidence")
_CLASSES = frozenset({"local-ok", "dispatch-required", "unknown"})


class AdmissionRegistryError(RuntimeError):
    """registry を安全に読み込めない場合の正規化済み例外。"""


def _object_without_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise AdmissionRegistryError(f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def _read_registry_bytes(path: str) -> bytes:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise AdmissionRegistryError("registry is not a regular file")
        if metadata.st_size > _MAX_REGISTRY_BYTES:
            raise AdmissionRegistryError("registry exceeds the 1 MiB size cap")

        chunks = []
        remaining = _MAX_REGISTRY_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > _MAX_REGISTRY_BYTES:
            raise AdmissionRegistryError("registry exceeds the 1 MiB read cap")
        return raw
    finally:
        try:
            os.close(descriptor)
        except BaseException as exc:
            # cleanup 自身の例外も raw のまま loader 外へ漏らさず fail-closed にする。
            raise AdmissionRegistryError(
                f"failed to close registry: {type(exc).__name__}: {exc}"
            ) from exc


def _is_canonical_repo_relative_path(path) -> bool:
    return (isinstance(path, str)
            and bool(path)
            and not os.path.isabs(path)
            and ".." not in path.split("/")
            and not path.endswith("/")
            and "\\" not in path
            and not any(unicodedata.category(char) == "Cc" for char in path)
            and os.path.normpath(path) == path)


def _validated_document(raw: bytes) -> tuple[dict, dict]:
    text = raw.decode("utf-8")
    document = json.loads(
        text,
        object_pairs_hook=_object_without_duplicate_keys,
    )
    if not isinstance(document, dict):
        raise AdmissionRegistryError("registry root must be an object")
    if set(document) != {"schema_version", "entries"}:
        raise AdmissionRegistryError("registry root fields are invalid")
    if document["schema_version"] != _SCHEMA_VERSION:
        raise AdmissionRegistryError("registry schema_version is invalid")

    entries = document["entries"]
    if not isinstance(entries, dict) or not entries:
        raise AdmissionRegistryError("registry entries must be a non-empty object")

    validated = {}
    for path, entry in entries.items():
        if not _is_canonical_repo_relative_path(path):
            raise AdmissionRegistryError(f"registry path is invalid: {path!r}")
        if not isinstance(entry, dict) or tuple(entry) != _ENTRY_FIELDS:
            raise AdmissionRegistryError(f"registry entry fields are invalid: {path}")
        if entry["class"] not in _CLASSES:
            raise AdmissionRegistryError(f"registry class is invalid: {path}")
        if (not path.startswith("tools/pegasus/")
                and entry["class"] == "local-ok"):
            raise AdmissionRegistryError(f"registry path is invalid: {path!r}")
        if any(not isinstance(entry[field], str) or not entry[field]
               for field in _ENTRY_FIELDS):
            raise AdmissionRegistryError(f"registry entry value is invalid: {path}")
        validated[path] = dict(entry)

    canonical_document = {
        "schema_version": _SCHEMA_VERSION,
        "entries": {path: validated[path] for path in sorted(validated)},
    }
    return canonical_document, validated


def load_admission_registry(repo_root):
    """canonical registry を全件検証し、path→entry mapping を返す。"""
    try:
        if not isinstance(repo_root, (str, bytes, os.PathLike)):
            raise AdmissionRegistryError("repo_root must be path-like")
        path = os.path.join(os.fspath(repo_root), REGISTRY_RELATIVE_PATH)
        raw = _read_registry_bytes(path)
        document, entries = _validated_document(raw)
        canonical = (json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ) + "\n").encode("utf-8")
        if raw != canonical:
            raise AdmissionRegistryError("registry bytes are not canonical")
        return entries
    except AdmissionRegistryError:
        raise
    except BaseException as exc:
        raise AdmissionRegistryError(
            f"failed to load admission registry: {type(exc).__name__}: {exc}"
        ) from exc
