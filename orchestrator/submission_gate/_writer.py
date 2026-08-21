"""認可済み受領証の exact-byte publish 境界 (T-338 unit 5)。"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import NoReturn

from ._binding import _CAPABILITY_TOKEN, _PreregBinding
from ._manifest import ApprovedManifest
from ._receipt_io import ReceiptDocument, create_receipt_bytes, parse_receipt_bytes
from ._receipt_schema import _load_schema_from_ref
from ._semantic_validator import _validate_receipt_semantics


_STUDY_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
_SERIES_ID_RE = re.compile(r"[0-9a-f]{64}\Z")
_RECEIPT_NAMESPACE = "output/receipts/t139"


class VectorAuthorityUnavailableError(RuntimeError):
    """現行 ApprovedManifest から conformance vector authority を得られない。"""

    reason_code = "vector_authority_unavailable"
    code = reason_code


def _assert_vector_authority() -> NoReturn:
    if "vector_index" not in getattr(ApprovedManifest, "__annotations__", {}):
        raise VectorAuthorityUnavailableError(
            "vector_authority_unavailable: ApprovedManifest has no vector index field"
        )
    raise VectorAuthorityUnavailableError(
        "vector_authority_unavailable: vector authority resolver is not available"
    )


def _destination(receipt: ReceiptDocument) -> str:
    value: Mapping[str, object] = receipt.value
    study_id = value.get("study_id")
    series_id = value.get("series_id")
    study_stage = value.get("study_stage")
    if type(study_id) is not str or _STUDY_ID_RE.fullmatch(study_id) is None:
        raise ValueError("receipt study_id is not a destination-safe identifier")
    if type(series_id) is not str or _SERIES_ID_RE.fullmatch(series_id) is None:
        raise ValueError("receipt series_id is not a destination-safe identifier")
    if study_stage not in {"pilot", "main_run"}:
        raise ValueError("receipt study_stage is not a destination-safe stage")
    return f"{_RECEIPT_NAMESPACE}/{study_id}--{series_id}--{study_stage}.json"


def _publish_receipt(
    *,
    repository_root: str | os.PathLike[str],
    raw_bytes: bytes,
    binding: _PreregBinding,
) -> None:
    """Validate and create exactly one receipt in the fixed receipt namespace."""

    if type(raw_bytes) is not bytes:
        raise TypeError("raw_bytes must be a built-in bytes value")
    receipt = parse_receipt_bytes(raw_bytes)
    if type(binding) is not _PreregBinding or getattr(binding, "_seal", None) is not _CAPABILITY_TOKEN:
        raise TypeError("binding must be a sealed _PreregBinding capability")
    binding.assert_intact(repository_root)
    schema = _load_schema_from_ref(repository_root, binding.record.receipt_schema)
    _validate_receipt_semantics(
        repository_root,
        receipt,
        schema=schema,
        binding=binding,
    )
    _assert_vector_authority()
    binding.assert_intact(repository_root)
    create_receipt_bytes(repository_root, _destination(receipt), raw_bytes)


__all__ = ()
