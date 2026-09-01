#!/usr/bin/env python3
"""Canonical signed-v6 acceptance receipts and Ed25519 verification.

This repository had no existing cryptographic-library use or dependency
declaration when this module was introduced.  This module deliberately uses
``cryptography``'s Ed25519 implementation; an unavailable import is a hard,
fail-closed error rather than a skipped or weakened verification path.

The verification key is configured at one fixed, repository-external path.
Neither the receipt nor an argument or environment variable can select that
path.  A signature proves approval by the corresponding private key and
protects the signed bytes from later modification.  It does not prove that a
particular issuer program ran, nor does it make the waiter's self-reported
observations independently true.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError as exc:  # pragma: no cover - absence must stop module loading
    raise RuntimeError(
        "cryptography with Ed25519 support is required for receipt verification"
    ) from exc


CONFIGURED_PUBLIC_KEY_PATH = Path(
    "/work/1/SFC/tanab/dev-wave-authority/acceptance-issuer-public-key.pem"
)

V5_SCHEMA_VERSION = "dev-wave-acceptance-receipt/v5"
SIGNED_V6_SCHEMA_VERSION = "dev-wave-acceptance-receipt/signed-v6"

_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_HOLDER_RE = re.compile(r"[0-9a-f]{12}\Z")
_MAX_PUBLIC_KEY_BYTES = 16 * 1024

V5_ROOT_FIELDS = frozenset(
    {
        "schema_version",
        "authority_kind",
        "acceptance_wave",
        "lease_holder",
        "tested_main",
        "tested_tip",
        "argv",
        "resolved_runner_path",
        "child_rc",
        "pre_fingerprint",
        "post_fingerprint",
        "waiter_blob_sha",
        "launcher_source_revision",
        "launcher_blob_sha",
        "launcher_executed_sha256",
        "waiter_executed_sha256",
        "runner_executed_sha256",
        "env_projection",
        "effective_scheduler",
        "verdict",
        "log_sha256",
        "checker_rc",
        "checker_status",
        "checker_blob_sha",
        "checker_receipt_sha256",
        "red_nodeids",
        "flake_nodeids",
    }
)
SIGNED_V6_PAYLOAD_FIELDS = frozenset(
    V5_ROOT_FIELDS
    | {
        "lease_generation",
        "checker_content_sha256",
        "issuer_key_id",
    }
)
SIGNED_V6_ROOT_FIELDS = frozenset(SIGNED_V6_PAYLOAD_FIELDS | {"issuer_signature"})


class ReceiptSignatureError(Exception):
    """A fail-closed signed-receipt construction or verification error."""


@dataclass(frozen=True)
class ConfiguredPublicKey:
    """The fixed configured verification key and its derived key id."""

    key_id: str
    key: Ed25519PublicKey


def canonical_json_bytes(value: object) -> bytes:
    """Return the launcher's sorted, compact, newline-terminated JSON bytes."""

    try:
        return (
            json.dumps(
                value,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, UnicodeError, ValueError, RecursionError) as exc:
        raise ReceiptSignatureError("JSON value is not canonicalizable") from exc


def _require_sha1(value: object, label: str) -> None:
    if not isinstance(value, str) or _SHA1_RE.fullmatch(value) is None:
        raise ReceiptSignatureError(f"invalid {label}")


def _require_sha256(value: object, label: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ReceiptSignatureError(f"invalid {label}")


def _validate_v5_projection_source(receipt: Mapping[str, object]) -> None:
    if set(receipt) != V5_ROOT_FIELDS:
        raise ReceiptSignatureError("v5 receipt has unexpected root fields")
    if receipt.get("schema_version") != V5_SCHEMA_VERSION:
        raise ReceiptSignatureError("input receipt is not schema v5")
    wave = receipt.get("acceptance_wave")
    if not isinstance(wave, str) or not wave:
        raise ReceiptSignatureError("invalid acceptance_wave")
    holder = receipt.get("lease_holder")
    if not isinstance(holder, str) or _HOLDER_RE.fullmatch(holder) is None:
        raise ReceiptSignatureError("invalid lease_holder")
    for label in (
        "tested_main",
        "tested_tip",
        "waiter_blob_sha",
        "launcher_blob_sha",
    ):
        _require_sha1(receipt.get(label), label)
    checker_blob = receipt.get("checker_blob_sha")
    if checker_blob is not None:
        _require_sha1(checker_blob, "checker_blob_sha")
    for label in (
        "launcher_executed_sha256",
        "waiter_executed_sha256",
        "runner_executed_sha256",
        "log_sha256",
    ):
        _require_sha256(receipt.get(label), label)
    checker_receipt = receipt.get("checker_receipt_sha256")
    if checker_receipt is not None:
        _require_sha256(checker_receipt, "checker_receipt_sha256")
    # Canonicalizability is part of the projection boundary even though callers
    # may have obtained the mapping from a non-canonical JSON representation.
    canonical_json_bytes(dict(receipt))


def project_v5_receipt(
    receipt: Mapping[str, object],
    *,
    lease_generation: str,
    checker_content_sha256: str,
    issuer_key_id: str,
) -> dict[str, object]:
    """Build the complete signed-v6 payload (without its signature field).

    ``lease_generation`` is only a schema slot here.  The caller must supply an
    already-defined generation; this module neither reads nor changes the live
    production lease payload.
    """

    if not isinstance(receipt, Mapping):
        raise ReceiptSignatureError("v5 receipt must be an object")
    _validate_v5_projection_source(receipt)
    _require_sha256(lease_generation, "lease_generation")
    _require_sha256(checker_content_sha256, "checker_content_sha256")
    _require_sha256(issuer_key_id, "issuer_key_id")
    payload = dict(receipt)
    payload.update(
        {
            "schema_version": SIGNED_V6_SCHEMA_VERSION,
            "lease_generation": lease_generation,
            "checker_content_sha256": checker_content_sha256,
            "issuer_key_id": issuer_key_id,
        }
    )
    if set(payload) != SIGNED_V6_PAYLOAD_FIELDS:
        raise ReceiptSignatureError("signed-v6 payload field projection failed")
    return payload


def canonical_signed_payload_bytes(payload: Mapping[str, object]) -> bytes:
    """Canonicalize exactly the root fields covered by a signed-v6 signature."""

    if not isinstance(payload, Mapping) or set(payload) != SIGNED_V6_PAYLOAD_FIELDS:
        raise ReceiptSignatureError("signed-v6 payload has unexpected root fields")
    if payload.get("schema_version") != SIGNED_V6_SCHEMA_VERSION:
        raise ReceiptSignatureError("invalid signed-v6 schema")
    v5_source = {key: payload[key] for key in V5_ROOT_FIELDS}
    v5_source["schema_version"] = V5_SCHEMA_VERSION
    _validate_v5_projection_source(v5_source)
    _require_sha256(payload.get("lease_generation"), "lease_generation")
    _require_sha256(
        payload.get("checker_content_sha256"), "checker_content_sha256"
    )
    _require_sha256(payload.get("issuer_key_id"), "issuer_key_id")
    return canonical_json_bytes(dict(payload))


def attach_signature(
    payload: Mapping[str, object], signature: bytes
) -> dict[str, object]:
    """Attach a raw Ed25519 signature using canonical base64 representation."""

    canonical_signed_payload_bytes(payload)
    if not isinstance(signature, bytes) or len(signature) != 64:
        raise ReceiptSignatureError("invalid Ed25519 signature bytes")
    receipt = dict(payload)
    receipt["issuer_signature"] = base64.b64encode(signature).decode("ascii")
    return receipt


def public_key_id(key: Ed25519PublicKey) -> str:
    """Derive the stable key id from the raw 32-byte Ed25519 public key."""

    if not isinstance(key, Ed25519PublicKey):
        raise ReceiptSignatureError("public key is not Ed25519")
    raw = key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


def _read_fixed_public_key() -> bytes:
    path = CONFIGURED_PUBLIC_KEY_PATH
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        before = path.lstat()
        fd = os.open(path, flags)
    except OSError as exc:
        raise ReceiptSignatureError("configured public key is unavailable") from exc
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
            or opened.st_size <= 0
            or opened.st_size > _MAX_PUBLIC_KEY_BYTES
        ):
            raise ReceiptSignatureError("configured public key file is invalid")
        chunks: list[bytes] = []
        remaining = _MAX_PUBLIC_KEY_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(fd)
        if (
            len(raw) > _MAX_PUBLIC_KEY_BYTES
            or (opened.st_dev, opened.st_ino, opened.st_size)
            != (after.st_dev, after.st_ino, after.st_size)
        ):
            raise ReceiptSignatureError(
                "configured public key changed while reading"
            )
        return raw
    except OSError as exc:
        raise ReceiptSignatureError("configured public key is unreadable") from exc
    finally:
        os.close(fd)


def load_configured_public_key() -> ConfiguredPublicKey:
    """Load the Ed25519 key from the fixed configured path, fail-closed."""

    raw = _read_fixed_public_key()
    try:
        key = serialization.load_pem_public_key(raw)
    except (TypeError, ValueError) as exc:
        raise ReceiptSignatureError(
            "configured public key format is invalid"
        ) from exc
    if not isinstance(key, Ed25519PublicKey):
        raise ReceiptSignatureError("configured public key is not Ed25519")
    return ConfiguredPublicKey(public_key_id(key), key)


def _payload_from_signed_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(receipt, Mapping) or set(receipt) != SIGNED_V6_ROOT_FIELDS:
        raise ReceiptSignatureError("signed-v6 receipt has unexpected root fields")
    payload = {
        key: value for key, value in receipt.items() if key != "issuer_signature"
    }
    canonical_signed_payload_bytes(payload)
    return payload


def _decode_signature(value: object) -> bytes:
    if not isinstance(value, str):
        raise ReceiptSignatureError("issuer_signature is missing or invalid")
    try:
        signature = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeError, ValueError) as exc:
        raise ReceiptSignatureError("issuer_signature is not canonical base64") from exc
    if len(signature) != 64 or base64.b64encode(signature).decode("ascii") != value:
        raise ReceiptSignatureError("issuer_signature has invalid Ed25519 length")
    return signature


def verify_signed_receipt_signature(
    receipt: Mapping[str, object],
    configured_key: ConfiguredPublicKey,
    *,
    expected_acceptance_wave: str,
    expected_tested_main: str,
    expected_tested_tip: str,
    expected_lease_generation: str,
) -> dict[str, object]:
    """Verify a signed receipt against an already selected public-key record.

    This lower-level entry point exists for reviewed issuer code and tests.  A
    receipt boundary must call :func:`verify_configured_key_signed_receipt`,
    whose configured-key record cannot be selected by receipt, argv, or
    environment input.
    """

    if not isinstance(configured_key, ConfiguredPublicKey):
        raise ReceiptSignatureError("invalid configured public key record")
    if configured_key.key_id != public_key_id(configured_key.key):
        raise ReceiptSignatureError(
            "configured public key record is inconsistent"
        )
    _require_sha1(expected_tested_main, "expected_tested_main")
    _require_sha1(expected_tested_tip, "expected_tested_tip")
    _require_sha256(expected_lease_generation, "expected_lease_generation")
    if (
        not isinstance(expected_acceptance_wave, str)
        or not expected_acceptance_wave
    ):
        raise ReceiptSignatureError("invalid expected_acceptance_wave")
    payload = _payload_from_signed_receipt(receipt)
    if (
        payload.get("acceptance_wave") != expected_acceptance_wave
        or payload.get("tested_main") != expected_tested_main
        or payload.get("tested_tip") != expected_tested_tip
        or payload.get("lease_generation") != expected_lease_generation
    ):
        raise ReceiptSignatureError("signed receipt context mismatch")
    if payload.get("issuer_key_id") != configured_key.key_id:
        raise ReceiptSignatureError("signed receipt issuer key id mismatch")
    signature = _decode_signature(receipt.get("issuer_signature"))
    try:
        configured_key.key.verify(
            signature,
            canonical_signed_payload_bytes(payload),
        )
    except InvalidSignature as exc:
        raise ReceiptSignatureError("signed receipt signature is invalid") from exc
    return payload


def verify_configured_key_signed_receipt(
    receipt: Mapping[str, object],
    *,
    expected_acceptance_wave: str,
    expected_tested_main: str,
    expected_tested_tip: str,
    expected_lease_generation: str,
) -> dict[str, object]:
    """Load the fixed configured key, verify its signature, and bind context."""

    configured_key = load_configured_public_key()
    return verify_signed_receipt_signature(
        receipt,
        configured_key,
        expected_acceptance_wave=expected_acceptance_wave,
        expected_tested_main=expected_tested_main,
        expected_tested_tip=expected_tested_tip,
        expected_lease_generation=expected_lease_generation,
    )
