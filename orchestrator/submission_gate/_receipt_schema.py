"""Draft-07 receipt-shape loading from an approved schema reference.

The schema is a shape contract only.  Cross-field relationships, pointer
existence and digest/size agreement, B1 reject-only semantics, and all other
semantic admission rules belong to later validator/consumer units.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from collections.abc import Mapping
from os import PathLike
from typing import Any

from orchestrator.preregistration.blobref import BlobRef, read_pinned_blob

from ._receipt_io import _freeze_json_value, parse_receipt_bytes


class ReceiptSchemaError(RuntimeError):
    """A schema reference, schema document, or shape validation is invalid."""


@dataclass(frozen=True, slots=True)
class ReceiptSchema:
    """A Draft-07 schema document bound to one fixed blob digest."""

    ref: BlobRef
    sha256: str
    document: Mapping[str, Any]

    def __post_init__(self) -> None:
        if type(self.ref) is not BlobRef:
            raise TypeError("ReceiptSchema.ref must be a BlobRef")
        if type(self.sha256) is not str:
            raise TypeError("ReceiptSchema.sha256 must be a built-in str")
        if not isinstance(self.document, Mapping):
            raise TypeError("ReceiptSchema.document must be a mapping")
        object.__setattr__(self, "document", _freeze_json_value(self.document))
        if not hmac.compare_digest(self.sha256, self.ref.sha256):
            raise ValueError("ReceiptSchema.sha256 must match ref.sha256")


def _thaw_json_value(value: object) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json_value(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(child) for child in value]
    if isinstance(value, frozenset):
        return [_thaw_json_value(child) for child in value]
    return value


def _parse_schema_bytes(
    raw_bytes: bytes,
    *,
    ref: BlobRef,
) -> ReceiptSchema:
    """Parse a schema object and require its exact bytes to match ``ref``."""

    if type(ref) is not BlobRef:
        raise TypeError("ref must be a BlobRef")
    document = parse_receipt_bytes(raw_bytes, label="receipt schema")
    actual_digest = document.sha256
    if type(ref.sha256) is not str or not hmac.compare_digest(
        actual_digest, ref.sha256
    ):
        raise ReceiptSchemaError(
            "receipt schema SHA-256 mismatch: "
            f"expected={ref.sha256}, actual={actual_digest}"
        )
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:
        raise ReceiptSchemaError("jsonschema is required for receipt schemas") from exc
    try:
        Draft7Validator.check_schema(_thaw_json_value(document.value))
    except Exception as exc:  # jsonschema.SchemaError is version-specific
        raise ReceiptSchemaError(f"receipt schema is not a valid Draft-07 schema: {exc}") from exc
    return ReceiptSchema(
        ref=ref,
        sha256=actual_digest,
        document=document.value,
    )


def _load_schema_from_ref(
    repository_root: str | PathLike[str],
    ref: BlobRef,
) -> ReceiptSchema:
    """Load a schema from a fixed blob reference supplied by approved state.

    This is deliberately private.  A caller must not choose an arbitrary
    schema ``BlobRef`` through a public gate API; the eventual writer obtains
    the reference from the approved manifest/binding and then invokes this
    internal helper.
    """

    if type(ref) is not BlobRef:
        raise TypeError("ref must be a BlobRef")
    raw_bytes = read_pinned_blob(repository_root, ref)
    return _parse_schema_bytes(raw_bytes, ref=ref)


def load_schema(
    repository_root: str | PathLike[str],
    *,
    approved_manifest: object,
) -> ReceiptSchema:
    """Load only the schema reference carried by an approved manifest.

    ``ref`` is intentionally absent from this signature.  The public-shaped
    convenience entry accepts only the sealed internal ``ApprovedManifest``
    capability from unit 1 and extracts its approved ``receipt_schema`` field; an
    arbitrary caller-originated ``BlobRef`` is not an accepted substitute.
    Unit-2 fixtures that need a fixed reference use the private
    ``_load_schema_from_ref`` helper explicitly.
    """

    try:
        from ._manifest import ApprovedManifest, _is_sealed_approved_manifest
    except ImportError as exc:
        raise ReceiptSchemaError(
            "approved manifest implementation is required to load a schema"
        ) from exc
    if (
        type(approved_manifest) is not ApprovedManifest
        or not _is_sealed_approved_manifest(approved_manifest)
    ):
        raise ReceiptSchemaError(
            "load_schema requires a sealed approved manifest capability"
        )
    approved_blobs = approved_manifest.approved_blobs
    if not isinstance(approved_blobs, Mapping):
        raise ReceiptSchemaError("approved manifest has no receipt_schema reference")
    try:
        ref = approved_blobs["receipt_schema"]
    except (KeyError, TypeError) as exc:
        raise ReceiptSchemaError(
            "approved manifest has no receipt_schema reference"
        ) from exc
    if type(ref) is not BlobRef:
        raise ReceiptSchemaError(
            "approved manifest receipt_schema is not a BlobRef"
        )
    return _load_schema_from_ref(repository_root, ref)


def validate_receipt_shape(
    receipt: Mapping[str, Any],
    *,
    schema: ReceiptSchema,
) -> None:
    """Run only the repository's JSON Schema Draft-07 shape validator.

    Passing the schema does not mean the receipt is admitted.  This function
    deliberately performs no cross-field recomputation, pointer inspection,
    declared-value replacement, or semantic kill rule.
    """

    if not isinstance(receipt, Mapping):
        raise ReceiptSchemaError("receipt must be a mapping")
    if type(schema) is not ReceiptSchema:
        raise TypeError("schema must be a ReceiptSchema")
    try:
        from jsonschema import Draft7Validator
    except ImportError as exc:
        raise ReceiptSchemaError("jsonschema is required for receipt schemas") from exc
    try:
        schema_value = _thaw_json_value(schema.document)
        receipt_value = _thaw_json_value(receipt)
        errors = sorted(
            Draft7Validator(schema_value).iter_errors(receipt_value),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
    except Exception as exc:
        raise ReceiptSchemaError(f"receipt shape validation could not run: {exc}") from exc
    if errors:
        first = errors[0]
        path = list(first.absolute_path)
        raise ReceiptSchemaError(
            "receipt shape validation failed "
            f"({first.validator}) at {path}: {first.message}"
        )
