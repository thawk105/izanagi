# -*- coding: utf-8 -*-
"""Pure validation leaf for floor submitter receipts."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from ..calibrator.schema_v2 import normalize_request_id
from ..qualification import artifacts


_SCHEMA_VERSION = "pegasus-floor-submit-receipt/v1"
_JOB_SCRIPT_PATH = "tools/pegasus/floor_campaign.sh"
_FLOOR_KEYS = {
    "schema_version", "source_commit", "job_script_path",
    "job_script_sha256", "job_id", "nonce", "submitted_at", "request",
    "preflight", "dry_run",
}
_SAFE_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_JOB_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class FloorSubmitReceiptError(ValueError):
    """A floor submitter receipt is unavailable, malformed, or unbound."""


def _component(value: object, *, label: str) -> str:
    if (type(value) is not str
            or _SAFE_COMPONENT.fullmatch(value) is None
            or value in {".", ".."}):
        raise FloorSubmitReceiptError(f"{label} is not a safe path component")
    return value


def receipt_path(
        repo_root: Path, *, env_tag: str, nonce: str,
) -> Path:
    """Return the canonical create-only submitter receipt path."""
    safe_env_tag = _component(env_tag, label="env_tag")
    safe_nonce = _component(nonce, label="nonce")
    return (
        Path(repo_root) / "output" / "env" / safe_env_tag / "floor"
        / "attempts" / "submissions" / safe_nonce / "submit-receipt.json"
    )


def _validate_envelope(receipt: object) -> Mapping[str, object]:
    if type(receipt) is not dict:
        raise FloorSubmitReceiptError("floor submit receipt must be an object")

    # D75: this discriminator must precede every other receipt field read.
    if receipt.get("schema_version") != _SCHEMA_VERSION:
        raise FloorSubmitReceiptError("floor submit receipt schema mismatch")

    if set(receipt) != _FLOOR_KEYS:
        raise FloorSubmitReceiptError("floor submit receipt key set mismatch")
    if receipt["dry_run"] is not False:
        raise FloorSubmitReceiptError("floor submit receipt dry_run mismatch")
    if receipt["job_script_path"] != _JOB_SCRIPT_PATH:
        raise FloorSubmitReceiptError("floor submit receipt job script path mismatch")
    if (type(receipt["submitted_at"]) is not int
            or receipt["submitted_at"] <= 0):
        raise FloorSubmitReceiptError("floor submit receipt submitted_at is invalid")
    if (type(receipt["source_commit"]) is not str
            or _HEX40.fullmatch(receipt["source_commit"]) is None):
        raise FloorSubmitReceiptError("floor submit receipt source commit is invalid")
    if (type(receipt["job_script_sha256"]) is not str
            or _HEX64.fullmatch(receipt["job_script_sha256"]) is None):
        raise FloorSubmitReceiptError("floor submit receipt script hash is invalid")
    if (type(receipt["nonce"]) is not str
            or _HEX32.fullmatch(receipt["nonce"]) is None):
        raise FloorSubmitReceiptError("floor submit receipt nonce is invalid")
    if type(receipt["job_id"]) is not str:
        raise FloorSubmitReceiptError("floor submit receipt job id is invalid")
    try:
        normalized_job_id = normalize_request_id(receipt["job_id"])
    except (TypeError, ValueError) as exc:
        raise FloorSubmitReceiptError(
            "floor submit receipt job id is invalid"
        ) from exc
    if _JOB_ID.fullmatch(normalized_job_id) is None:
        raise FloorSubmitReceiptError("floor submit receipt job id is invalid")
    return receipt


def load_floor_submit_receipt(path: Path) -> Mapping[str, object]:
    """Strictly load and validate one floor submitter receipt envelope."""
    try:
        receipt = artifacts.load_json_strict(Path(path))
    except Exception as exc:
        raise FloorSubmitReceiptError(
            "floor submit receipt strict read failed"
        ) from exc
    return _validate_envelope(receipt)


def _require_job_binding(
        receipt: Mapping[str, object], *, expected_job_id: str,
        expected_nonce: str,
) -> None:
    if receipt["nonce"] != expected_nonce:
        raise FloorSubmitReceiptError("floor submit receipt nonce mismatch")
    if type(expected_job_id) is not str:
        raise FloorSubmitReceiptError("floor submit receipt job id mismatch")
    try:
        expected = normalize_request_id(expected_job_id)
        observed = normalize_request_id(receipt["job_id"])
    except (TypeError, ValueError) as exc:
        raise FloorSubmitReceiptError(
            "floor submit receipt job id mismatch"
        ) from exc
    if observed != expected:
        raise FloorSubmitReceiptError("floor submit receipt job id mismatch")


def require_floor_submit_job_binding(
        receipt: Mapping[str, object], *, expected_job_id: str,
        expected_nonce: str,
) -> None:
    """Require normalized scheduler job identity and nonce equality."""
    row = _validate_envelope(receipt)
    _require_job_binding(
        row, expected_job_id=expected_job_id, expected_nonce=expected_nonce,
    )


def _require_script_binding(
        receipt: Mapping[str, object], *, expected_job_script_sha256: str,
) -> None:
    if receipt["job_script_sha256"] != expected_job_script_sha256:
        raise FloorSubmitReceiptError("floor submit receipt script hash mismatch")


def require_floor_submit_script_binding(
        receipt: Mapping[str, object], *, expected_job_script_sha256: str,
) -> None:
    """Require the submitter-recorded script hash to match the caller binding."""
    row = _validate_envelope(receipt)
    _require_script_binding(
        row, expected_job_script_sha256=expected_job_script_sha256,
    )


def require_floor_submit_receipt_binding(
        receipt: Mapping[str, object], *, expected_job_id: str,
        expected_job_script_sha256: str, expected_nonce: str,
) -> None:
    """Require the complete reusable authority binding for a floor receipt."""
    row = _validate_envelope(receipt)
    _require_job_binding(
        row, expected_job_id=expected_job_id, expected_nonce=expected_nonce,
    )
    _require_script_binding(
        row, expected_job_script_sha256=expected_job_script_sha256,
    )
