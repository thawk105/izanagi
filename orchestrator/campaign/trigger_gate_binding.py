# -*- coding: utf-8 -*-
"""Canonical binding between trigger-gate IR, predicate, and source evidence."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Iterable

from .reflux_ir import SCHEMA_ID, TriggerGateIR, emit_predicate

__all__ = [
    "SCHEMA_VERSION",
    "WAL_RECORD_STAGE",
    "CANONICAL_PREDICATES",
    "SourceBinding",
    "TriggerGateBinding",
    "TriggerGateBindingError",
    "canonicalize_predicate",
    "expected_predicate_sha256",
    "is_canonical_predicate",
    "mask_for_canonical_predicate",
    "new_nonce",
    "canonical_json",
    "commitment",
    "validate_record",
    "to_record",
]

SCHEMA_VERSION = "izanagi-trigger-gate-binding/v1"
WAL_RECORD_STAGE = "trigger_binding"

_REJECTION_MESSAGE = "invalid trigger gate binding"
_RECORD_KEYS = frozenset({
    "schema_version",
    "ir_schema",
    "mask",
    "predicate_sha256",
    "nonce",
    "source",
})
_SOURCE_KEYS = frozenset({"src_token", "source_bytes_sha256"})
_LOWER_HEX = frozenset("0123456789abcdef")


class TriggerGateBindingError(Exception):
    """Uniform, disclosure-free rejection for trigger-gate bindings."""


def _reject() -> None:
    raise TriggerGateBindingError(_REJECTION_MESSAGE) from None


def _validate_mask(mask: object) -> int:
    if type(mask) is not int or not 0 <= mask <= 31:
        _reject()
    return mask


def _is_lower_hex_64(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in _LOWER_HEX for character in value)
    )


def _has_exact_keys(value: object, expected: frozenset[str]) -> bool:
    return (
        type(value) is dict
        and len(value) == len(expected)
        and all(type(key) is str for key in value)
        and frozenset(value) == expected
    )


def expected_predicate_sha256(mask: int) -> str:
    """Return the digest of the canonical predicate for one exact mask."""
    validated = _validate_mask(mask)
    predicate = emit_predicate(TriggerGateIR(validated))
    return hashlib.sha256(predicate.encode()).hexdigest()


def _build_canonical_predicate_index(emitted: Iterable[str]) -> dict[str, str]:
    """Index emitter bytes by their accepted outer-whitespace equivalent."""
    index: dict[str, str] = {}
    for predicate in emitted:
        key = predicate.strip()
        if key in index:
            raise RuntimeError(
                "duplicate canonical trigger predicate after outer strip"
            )
        index[key] = predicate
    return index


_CANONICAL_PREDICATES_BY_MASK = tuple(
    emit_predicate(TriggerGateIR(mask)) for mask in range(32)
)
_CANONICAL_PREDICATE_INDEX = _build_canonical_predicate_index(
    _CANONICAL_PREDICATES_BY_MASK
)
_CANONICAL_PREDICATE_MASK_INDEX = {
    predicate.strip(): mask
    for mask, predicate in enumerate(_CANONICAL_PREDICATES_BY_MASK)
}
CANONICAL_PREDICATES: frozenset[str] = frozenset(_CANONICAL_PREDICATE_INDEX)


def canonicalize_predicate(text: object) -> str:
    """Resolve an accepted predicate spelling to its canonical emitter bytes."""
    if type(text) is not str:
        _reject()
    key = text.strip()
    if key not in _CANONICAL_PREDICATE_INDEX:
        _reject()
    return _CANONICAL_PREDICATE_INDEX[key]


def mask_for_canonical_predicate(text: object) -> int:
    """Recover the mask encoded by one accepted canonical predicate."""
    if type(text) is not str:
        _reject()
    key = text.strip()
    if key not in _CANONICAL_PREDICATE_MASK_INDEX:
        _reject()
    return _CANONICAL_PREDICATE_MASK_INDEX[key]


def is_canonical_predicate(text: object) -> bool:
    """Return membership in the closed canonical predicate language."""
    return type(text) is str and text.strip() in CANONICAL_PREDICATES


@dataclass(frozen=True)
class SourceBinding:
    src_token: str
    source_bytes_sha256: str

    def __post_init__(self) -> None:
        if type(self.src_token) is not str:
            _reject()
        if not _is_lower_hex_64(self.source_bytes_sha256):
            _reject()


@dataclass(frozen=True)
class TriggerGateBinding:
    mask: int
    predicate_sha256: str
    nonce: str
    source: SourceBinding | None

    def __post_init__(self) -> None:
        mask = _validate_mask(self.mask)
        if not _is_lower_hex_64(self.predicate_sha256):
            _reject()
        if self.predicate_sha256 != expected_predicate_sha256(mask):
            _reject()
        if not _is_lower_hex_64(self.nonce):
            _reject()
        if self.source is not None and type(self.source) is not SourceBinding:
            _reject()


def new_nonce() -> str:
    """Create a fresh 32-byte nonce encoded as lowercase hexadecimal."""
    return os.urandom(32).hex()


def to_record(binding: TriggerGateBinding) -> dict[str, object]:
    """Convert a validated binding to its closed WAL record payload."""
    if type(binding) is not TriggerGateBinding:
        _reject()
    source = binding.source
    return {
        "schema_version": SCHEMA_VERSION,
        "ir_schema": SCHEMA_ID,
        "mask": binding.mask,
        "predicate_sha256": binding.predicate_sha256,
        "nonce": binding.nonce,
        "source": None if source is None else {
            "src_token": source.src_token,
            "source_bytes_sha256": source.source_bytes_sha256,
        },
    }


def canonical_json(binding: TriggerGateBinding) -> bytes:
    """Serialize a binding to deterministic canonical UTF-8 JSON bytes."""
    return json.dumps(
        to_record(binding),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def commitment(binding: TriggerGateBinding) -> str:
    """Commit to every canonical binding field, including its nonce."""
    return hashlib.sha256(canonical_json(binding)).hexdigest()


def validate_record(
    payload: object, *, require_source: bool
) -> TriggerGateBinding:
    """Validate and reconstruct one raw ``trigger_binding`` WAL payload."""
    if type(require_source) is not bool:
        _reject()
    if not _has_exact_keys(payload, _RECORD_KEYS):
        _reject()
    if (
        type(payload["schema_version"]) is not str
        or payload["schema_version"] != SCHEMA_VERSION
        or type(payload["ir_schema"]) is not str
        or payload["ir_schema"] != SCHEMA_ID
    ):
        _reject()

    raw_source = payload["source"]
    if raw_source is None:
        if require_source:
            _reject()
        source = None
    else:
        if not _has_exact_keys(raw_source, _SOURCE_KEYS):
            _reject()
        source = SourceBinding(
            src_token=raw_source["src_token"],
            source_bytes_sha256=raw_source["source_bytes_sha256"],
        )

    return TriggerGateBinding(
        mask=payload["mask"],
        predicate_sha256=payload["predicate_sha256"],
        nonce=payload["nonce"],
        source=source,
    )
