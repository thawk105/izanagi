# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import hashlib
import inspect
import json

import pytest

from orchestrator.campaign import s8b_sort_swo_receipt as receipt
from orchestrator.tests.s8b_floor_evidence_fixture import (
    expected_portable_sort_swo_pass_receipt,
    fake_sort_swo_pass_attempt,
)


_ENTRY_SHA = hashlib.sha256(b"entry").hexdigest()
_BINARY_SHA = hashlib.sha256(b"binary").hexdigest()
_IDENTITY = {
    "cell_id": "rr80::sort_best",
    "holdout_id": "rr80",
    "configuration_id": "sort_best",
    "entry_sha256": _ENTRY_SHA,
    "binary_sha256": _BINARY_SHA,
}


def _project() -> dict[str, object]:
    return receipt.project_sort_swo_pass_attempt(
        fake_sort_swo_pass_attempt(), **_IDENTITY,
    )


def test_projection_matches_independent_fixture_and_hashes_full_raw_receipt():
    projected = _project()
    assert projected == expected_portable_sort_swo_pass_receipt(**_IDENTITY)
    raw = fake_sort_swo_pass_attempt()["oracle_receipt"]
    canonical = json.dumps(
        raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    assert projected["receipt_sha256"] == hashlib.sha256(canonical).hexdigest()
    rendered = json.dumps(projected, ensure_ascii=False, sort_keys=True)
    assert "/fixture/" not in rendered
    assert "compiler_version" not in projected
    assert "compiler_realpath" not in projected
    assert "dependency_root_realpath" not in projected


def test_validator_accepts_exact_projection_and_binds_all_identity_fields():
    projected = _project()
    assert receipt.validate_portable_sort_swo_pass_receipt(
        projected,
        expected_cell_id=_IDENTITY["cell_id"],
        expected_holdout_id=_IDENTITY["holdout_id"],
        expected_configuration_id=_IDENTITY["configuration_id"],
        expected_entry_sha256=_ENTRY_SHA,
        expected_binary_sha256=_BINARY_SHA,
    ) == projected

    expected_names = {
        "expected_cell_id", "expected_holdout_id", "expected_configuration_id",
        "expected_entry_sha256", "expected_binary_sha256",
    }
    parameters = inspect.signature(
        receipt.validate_portable_sort_swo_pass_receipt
    ).parameters
    assert expected_names <= parameters.keys()
    assert receipt.__all__ == (
        "PORTABLE_SORT_SWO_RECEIPT_SCHEMA",
        "SortSwoReceiptError",
        "project_sort_swo_pass_attempt",
        "validate_portable_sort_swo_pass_receipt",
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("cell_id", "rr20::sort_best"),
        ("holdout_id", "rr20"),
        ("configuration_id", "stock_common"),
        ("entry_sha256", "0" * 64),
        ("binary_sha256", "1" * 64),
    ],
)
def test_validator_rejects_receipt_transplant(field: str, replacement: str):
    projected = _project()
    projected[field] = replacement
    with pytest.raises(receipt.SortSwoReceiptError, match="identity"):
        receipt.validate_portable_sort_swo_pass_receipt(
            projected,
            expected_cell_id=_IDENTITY["cell_id"],
            expected_holdout_id=_IDENTITY["holdout_id"],
            expected_configuration_id=_IDENTITY["configuration_id"],
            expected_entry_sha256=_ENTRY_SHA,
            expected_binary_sha256=_BINARY_SHA,
        )


@pytest.mark.parametrize(
    "field", ["compiler_version", "compiler_realpath", "dependency_root_realpath"],
)
def test_validator_explicitly_rejects_raw_compiler_and_path_fields(field: str):
    projected = _project()
    projected[field] = "forbidden"
    with pytest.raises(receipt.SortSwoReceiptError, match="raw compiler/path"):
        receipt.validate_portable_sort_swo_pass_receipt(
            projected,
            expected_cell_id=_IDENTITY["cell_id"],
            expected_holdout_id=_IDENTITY["holdout_id"],
            expected_configuration_id=_IDENTITY["configuration_id"],
            expected_entry_sha256=_ENTRY_SHA,
            expected_binary_sha256=_BINARY_SHA,
        )


def test_projector_rejects_nonexact_or_nonpass_raw_attempt():
    attempt = fake_sort_swo_pass_attempt()
    attempt["unexpected"] = True
    with pytest.raises(receipt.SortSwoReceiptError, match="exact key"):
        receipt.project_sort_swo_pass_attempt(attempt, **_IDENTITY)

    attempt = copy.deepcopy(fake_sort_swo_pass_attempt())
    attempt["classification"] = "attempt-infra"
    with pytest.raises(receipt.SortSwoReceiptError, match="PASS"):
        receipt.project_sort_swo_pass_attempt(attempt, **_IDENTITY)


def test_guarantee_boundary_is_documented_on_module_and_both_public_functions():
    for target in (
        receipt,
        receipt.project_sort_swo_pass_attempt,
        receipt.validate_portable_sort_swo_pass_receipt,
    ):
        doc = inspect.getdoc(target) or ""
        assert "oracle が実際に走ったことの証明ではない" in doc
        assert "private" in doc and "commitment" in doc


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
