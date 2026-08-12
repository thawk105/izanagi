"""T-793 追補 P exact-key wrapper の回帰。"""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.preregistration.addendum_envelope import (
    DuplicateFieldsError,
    ExtraFieldsError,
    MissingFieldsError,
)
from orchestrator.publication.addendum_p_envelope import (
    require_addendum_p_exact_fields,
)


ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "output/insights/2026-08-11_t139-pubcore-stage2/addendum-p-draft.md"


def test_p3_exact_p01_p02_p03_envelope_is_accepted() -> None:
    assert require_addendum_p_exact_fields(DRAFT.read_bytes()) is None


def test_addendum_p_exact_key_gate_rejects_missing_p03() -> None:
    blob = DRAFT.read_bytes()
    heading = "### p03 —".encode("utf-8")
    blob = blob.replace(heading, b"p03 removed ", 1)
    with pytest.raises(MissingFieldsError):
        require_addendum_p_exact_fields(blob)


def test_addendum_p_exact_key_gate_rejects_extra_p04() -> None:
    blob = DRAFT.read_bytes()
    heading = "### p03 —".encode("utf-8")
    insertion = "### p04 — extra\n\nvalue\n\n".encode("utf-8")
    blob = blob.replace(heading, insertion + heading, 1)
    with pytest.raises(ExtraFieldsError):
        require_addendum_p_exact_fields(blob)


def test_addendum_p_exact_key_gate_rejects_duplicate_p01() -> None:
    blob = DRAFT.read_bytes()
    heading = "### p01 —".encode("utf-8")
    duplicate = "### p01 — duplicate\n\nvalue\n\n".encode("utf-8")
    blob = blob.replace(heading, duplicate + heading, 1)
    with pytest.raises(DuplicateFieldsError):
        require_addendum_p_exact_fields(blob)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
