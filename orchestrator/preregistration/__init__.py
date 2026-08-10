"""T-139 の事前登録 blob 合成と追補 envelope parser。

本 module は投入 gate (admission gate) ではない。
``resolve_effective_preregistration`` / ``PreregBinding`` / ``submit_pilot`` /
``verify_receipt`` は本 wave では実装しない。
"""

from .addendum_envelope import (
    T139_EXACT_FIELDS,
    parse_addendum_fields,
    require_approved_addendum_a_fields,
    require_exact_fields,
)
from .blobref import BlobRef, read_pinned_blob
from .erratum import ComposedCore, ErratumDocument, compose_core, parse_erratum

__all__ = (
    "BlobRef",
    "ComposedCore",
    "ErratumDocument",
    "T139_EXACT_FIELDS",
    "compose_core",
    "parse_addendum_fields",
    "parse_erratum",
    "read_pinned_blob",
    "require_approved_addendum_a_fields",
    "require_exact_fields",
)
