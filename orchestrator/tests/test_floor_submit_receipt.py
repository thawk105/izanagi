# -*- coding: utf-8 -*-
"""Floor submitter receipt authority leaf tests."""
from __future__ import annotations

import ast
import inspect
import socket
from copy import deepcopy
from pathlib import Path

import pytest

from orchestrator.campaign import env_contract, floor_submit_receipt, reservation
from orchestrator.qualification.contract import canonical_json_bytes


REPO_ROOT = Path(__file__).resolve().parents[2]
LEAF_PATH = REPO_ROOT / "orchestrator/campaign/floor_submit_receipt.py"
FLOOR_CAMPAIGN_PATH = REPO_ROOT / "orchestrator/campaign/s8b_floor_campaign.py"
NONCE = "a" * 32
SCRIPT_SHA256 = "b" * 64


def _receipt() -> dict:
    return {
        "schema_version": "pegasus-floor-submit-receipt/v1",
        "source_commit": "c" * 40,
        "job_script_path": "tools/pegasus/floor_campaign.sh",
        "job_script_sha256": SCRIPT_SHA256,
        "job_id": "0:873225.nqsv",
        "nonce": NONCE,
        "submitted_at": 1,
        "request": {},
        "preflight": {},
        "dry_run": False,
    }


def _write(path: Path, value: dict) -> None:
    path.write_bytes(canonical_json_bytes(value) + b"\n")


def test_receipt_path_is_canonical_and_has_no_environment_literal():
    root = Path("/repo")
    assert floor_submit_receipt.receipt_path(
        root, env_tag="fixture-env", nonce=NONCE,
    ) == (
        root / "output/env/fixture-env/floor/attempts/submissions"
        / NONCE / "submit-receipt.json"
    )


@pytest.mark.parametrize("field,value", [
    ("env_tag", ""),
    ("env_tag", "."),
    ("env_tag", "../escape"),
    ("env_tag", "nested/value"),
    ("env_tag", "nested\\value"),
    ("nonce", ""),
    ("nonce", ".."),
    ("nonce", "nested/value"),
])
def test_receipt_path_rejects_unsafe_components(field: str, value: str):
    arguments = {"env_tag": "fixture-env", "nonce": NONCE}
    arguments[field] = value
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="safe path component",
    ):
        floor_submit_receipt.receipt_path(Path("/repo"), **arguments)


def test_pos6_valid_receipt_ignores_callers_hostname(tmp_path, monkeypatch):
    receipt_path = tmp_path / "submit-receipt.json"
    _write(receipt_path, _receipt())
    receipt = floor_submit_receipt.load_floor_submit_receipt(receipt_path)

    monkeypatch.setattr(socket, "gethostname", lambda: "untrusted-host")
    floor_submit_receipt.require_floor_submit_receipt_binding(
        receipt,
        expected_job_id="873225.nqsv",
        expected_job_script_sha256=SCRIPT_SHA256,
        expected_nonce=NONCE,
    )
    assert "hostname" not in inspect.signature(
        floor_submit_receipt.require_floor_submit_receipt_binding
    ).parameters


def _binding_arguments() -> dict[str, str]:
    return {
        "expected_job_id": "873225.nqsv",
        "expected_job_script_sha256": SCRIPT_SHA256,
        "expected_nonce": NONCE,
    }


def test_job_id_mismatch_is_rejected_after_normalization():
    arguments = _binding_arguments()
    arguments["expected_job_id"] = "other.123"
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError, match="job id mismatch",
    ):
        floor_submit_receipt.require_floor_submit_receipt_binding(
            _receipt(), **arguments,
        )


def test_mut_l8_script_sha_mismatch_is_rejected():
    arguments = _binding_arguments()
    arguments["expected_job_script_sha256"] = "d" * 64
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="script hash mismatch",
    ):
        floor_submit_receipt.require_floor_submit_receipt_binding(
            _receipt(), **arguments,
        )


def test_mut_l9_nonce_mismatch_is_rejected():
    arguments = _binding_arguments()
    arguments["expected_nonce"] = "e" * 32
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError, match="nonce mismatch",
    ):
        floor_submit_receipt.require_floor_submit_receipt_binding(
            _receipt(), **arguments,
        )


def test_mut_l10_missing_receipt_is_rejected_without_side_effects(tmp_path):
    receipt_path = tmp_path / "missing" / "submit-receipt.json"
    before = list(tmp_path.rglob("*"))
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="strict read failed",
    ):
        floor_submit_receipt.load_floor_submit_receipt(receipt_path)
    assert list(tmp_path.rglob("*")) == before


def test_empty_receipt_is_rejected_independently(tmp_path):
    receipt_path = tmp_path / "submit-receipt.json"
    receipt_path.write_bytes(b"")
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="strict read failed",
    ):
        floor_submit_receipt.load_floor_submit_receipt(receipt_path)


def test_truncated_receipt_is_rejected_independently(tmp_path):
    receipt_path = tmp_path / "submit-receipt.json"
    receipt_path.write_bytes(b'{"schema_version":')
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="strict read failed",
    ):
        floor_submit_receipt.load_floor_submit_receipt(receipt_path)


def test_unreadable_receipt_is_rejected(tmp_path, monkeypatch):
    receipt_path = tmp_path / "submit-receipt.json"
    receipt_path.write_bytes(b"unused")

    def unreadable(_path):
        raise OSError("injected unreadable receipt")

    monkeypatch.setattr(floor_submit_receipt.artifacts, "load_json_strict", unreadable)
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="strict read failed",
    ):
        floor_submit_receipt.load_floor_submit_receipt(receipt_path)


def test_schema_mismatch_is_rejected_independently(tmp_path):
    receipt_path = tmp_path / "submit-receipt.json"
    receipt = _receipt()
    receipt["schema_version"] = "pegasus-submit-receipt/v1"
    _write(receipt_path, receipt)
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="schema mismatch",
    ):
        floor_submit_receipt.load_floor_submit_receipt(receipt_path)


def test_schema_is_checked_before_nonce_field():
    """diagnostic sensitivity pin (kill に数えない): schema precedes nonce."""
    calibration_receipt = {
        "schema_version": "pegasus-submit-receipt/v1",
        "submission_nonce": NONCE,
    }
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError,
        match="^floor submit receipt schema mismatch$",
    ):
        floor_submit_receipt.require_floor_submit_receipt_binding(
            calibration_receipt,
            expected_job_id="873225.nqsv",
            expected_job_script_sha256=SCRIPT_SHA256,
            expected_nonce=NONCE,
        )


@pytest.mark.parametrize("field,value,error", [
    ("dry_run", True, "dry_run mismatch"),
    ("submitted_at", 0, "submitted_at is invalid"),
    ("source_commit", "c" * 39, "source commit is invalid"),
    ("job_script_sha256", "b" * 63, "script hash is invalid"),
    ("nonce", "a" * 31, "nonce is invalid"),
    ("job_script_path", "other.sh", "job script path mismatch"),
])
def test_envelope_preserves_existing_scalar_rejections(field, value, error):
    receipt = deepcopy(_receipt())
    receipt[field] = value
    with pytest.raises(
        floor_submit_receipt.FloorSubmitReceiptError, match=error,
    ):
        floor_submit_receipt.require_floor_submit_receipt_binding(
            receipt,
            expected_job_id="873225.nqsv",
            expected_job_script_sha256=SCRIPT_SHA256,
            expected_nonce=NONCE,
        )


def test_envelope_rejects_missing_and_extra_keys():
    missing = _receipt()
    del missing["preflight"]
    extra = {**_receipt(), "unexpected": None}
    for receipt in (missing, extra):
        with pytest.raises(
            floor_submit_receipt.FloorSubmitReceiptError,
            match="key set mismatch",
        ):
            floor_submit_receipt.require_floor_submit_receipt_binding(
                receipt,
                expected_job_id="873225.nqsv",
                expected_job_script_sha256=SCRIPT_SHA256,
                expected_nonce=NONCE,
            )


def test_leaf_has_no_site_environment_or_subprocess_authority():
    tree = ast.parse(LEAF_PATH.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not imports.intersection({"os", "subprocess", "socket"})
    assert not any(
        name and ("site_policy" in name or "calibration" in name)
        for name in imported_from
    )
    called_names = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not called_names.intersection({"current_site", "getenv", "run", "Popen"})


def test_pos7_non_single_process_contract_has_a_receipt_free_path():
    """The non-reservation branch must remain independent of this receipt leaf."""
    contract = env_contract.lookup("linux-baremetal")
    assert contract.isolation_policy.single_process is False
    assert reservation.is_reservation_required(contract.isolation_policy) is False

    tree = ast.parse(FLOOR_CAMPAIGN_PATH.read_text(encoding="utf-8"))
    core = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_campaign_core"
    )
    guard = next(
        node for node in ast.walk(core)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Call)
        and isinstance(node.test.func, ast.Attribute)
        and node.test.func.attr == "is_reservation_required"
    )
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "read_binding"
        for statement in guard.body for node in ast.walk(statement)
    )
    receipt_calls = [
        node for node in ast.walk(core)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_floor_submit_receipt_binding"
    ]
    guarded_nodes = {
        node for statement in guard.body for node in ast.walk(statement)
    }
    assert all(call in guarded_nodes for call in receipt_calls)


def test_certified_writer_admission_delegates_floor_envelope_to_leaf():
    admission_path = (
        REPO_ROOT / "orchestrator/campaign/certified_writer_admission.py"
    )
    tree = ast.parse(admission_path.read_text(encoding="utf-8"))
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_admit_floor"
    )
    calls = {
        node.func.attr
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert {
        "load_floor_submit_receipt", "require_floor_submit_job_binding",
    } <= calls
    assert "_FLOOR_KEYS" not in admission_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
