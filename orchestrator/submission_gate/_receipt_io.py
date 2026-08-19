"""Exact-byte receipt parsing and create-only persistence.

This module is intentionally only a low-level receipt byte layer.  It does
not decide admission, validate a binding, or infer semantic correctness from
producer declarations.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from collections.abc import Mapping
from os import PathLike
from types import MappingProxyType
from typing import Any

from ._safe_io import create_only_relative_bytes, read_relative_regular_bytes


class ReceiptIOError(RuntimeError):
    """A receipt could not be parsed or represented safely."""


class ReceiptParseError(ReceiptIOError):
    """Receipt bytes are not strict UTF-8 JSON objects."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys at every object nesting level."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReceiptParseError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> None:
    raise ReceiptParseError(f"non-finite JSON number is forbidden: {token}")


def _reject_nonfinite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ReceiptParseError("non-finite JSON number is forbidden")
    if isinstance(value, Mapping):
        for child in value.values():
            _reject_nonfinite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_nonfinite(child)


def _freeze_json_value(value: object) -> Any:
    """Recursively remove mutable containers from parsed JSON values."""

    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_json_value(child) for key, child in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(child) for child in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_json_value(child) for child in value)
    if isinstance(value, bytearray):
        return bytes(value)
    return value


@dataclass(frozen=True, slots=True)
class ReceiptDocument:
    """A parsed receipt together with the exact bytes that produced it."""

    raw_bytes: bytes
    value: Mapping[str, Any]
    sha256: str

    def __post_init__(self) -> None:
        if type(self.raw_bytes) is not bytes:
            raise TypeError("ReceiptDocument.raw_bytes must be built-in bytes")
        if not isinstance(self.value, Mapping):
            raise TypeError("ReceiptDocument.value must be a mapping")
        object.__setattr__(self, "value", _freeze_json_value(self.value))
        expected = hashlib.sha256(self.raw_bytes).hexdigest()
        if type(self.sha256) is not str or self.sha256 != expected:
            raise ValueError("ReceiptDocument.sha256 does not match raw_bytes")


def parse_receipt_bytes(
    raw_bytes: bytes,
    *,
    label: str = "receipt",
) -> ReceiptDocument:
    """Parse strict UTF-8 JSON while preserving the original bytes.

    Duplicate keys are rejected recursively, JSON non-finite constants are
    rejected both lexically and after parsing, and only an object is accepted
    at the root.  No canonical re-serialization, key ordering, whitespace, or
    final newline requirement is applied.
    """

    if type(raw_bytes) is not bytes:
        raise TypeError("raw_bytes must be a built-in bytes value")
    if type(label) is not str or not label:
        raise ValueError("label must be a non-empty built-in str")
    try:
        text = raw_bytes.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
        _reject_nonfinite(value)
    except ReceiptParseError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ReceiptParseError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if type(value) is not dict:
        raise ReceiptParseError(f"{label} root must be a JSON object")
    try:
        return ReceiptDocument(
            raw_bytes=raw_bytes,
            value=value,
            sha256=hashlib.sha256(raw_bytes).hexdigest(),
        )
    except RecursionError as exc:
        raise ReceiptParseError(f"{label} is too deeply nested: {exc}") from exc


_DEFAULT_MAX_RECEIPT_BYTES = 16 * 1024 * 1024


def read_receipt(
    repository_root: str | PathLike[str],
    relative_path: str,
    *,
    max_bytes: int = _DEFAULT_MAX_RECEIPT_BYTES,
) -> ReceiptDocument:
    """Read and parse one receipt through the fd-relative safe-I/O layer."""

    raw_bytes = read_relative_regular_bytes(
        repository_root,
        relative_path,
        max_bytes=max_bytes,
    )
    return parse_receipt_bytes(raw_bytes, label=relative_path)


def create_receipt_bytes(
    repository_root: str | PathLike[str],
    relative_path: str,
    raw_bytes: bytes,
) -> None:
    """Persist exact receipt bytes through strict create-only file I/O.

    This function is low-level exact-byte create-only I/O and is not part of
    the submission gate.  The caller (the future writer entry point) is
    responsible for adding the ``PreregBinding`` comparison on top of this
    layer; this function intentionally does not accept a binding argument.
    """

    create_only_relative_bytes(repository_root, relative_path, raw_bytes)
