# -*- coding: utf-8 -*-
"""Signed-v6 controls, including the recorded production-v5 projection.

The configured-key boundary controls use only runtime test keys.  They are not
a production control; the production signed-v6 positive control remains unmet.
"""

from __future__ import annotations

import copy
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

from tools import acceptance_receipt_signature as signing  # noqa: E402
from tools import acceptance_issuer_reference as issuer  # noqa: E402


_FIXTURE = _HERE / "fixtures" / "production-acceptance-receipt-v5.json"

# D431: all values below are source literals.  They are not derived from the
# environment, a production module constant, a loader, or the projection's own
# result at test runtime.
_PRODUCTION_FIXTURE_SHA256 = (
    "e4026458e2de2cd1173d214b7cdd1f000eafdc7ef328533efa440c571fd763d4"
)
_PRODUCTION_PROJECTED_SHA256 = (
    "98c37ca6618e353c457b91b113bd995799e92e136a9f3bb039b6f896a794cfde"
)
_PRODUCTION_PROJECTED_BYTES = 1919
_PRODUCTION_WAVE = "dev-wave-t1985-ratification-terminal"
_PRODUCTION_MAIN = "cb4a11b6e9c5281b4aa1feb7c7c1b67315d62aa0"
_PRODUCTION_TIP = "704ea7f1fd71974958db3855e4578f11d28838df"
_LEASE_GENERATION = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)
_OTHER_LEASE_GENERATION = (
    "1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)
_CHECKER_CONTENT_SHA256 = (
    "89abcdef0123456789abcdef0123456789abcdef0123456789abcdef01234567"
)
_PROJECTION_KEY_ID = (
    "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
)
_OTHER_TIP = "804ea7f1fd71974958db3855e4578f11d28838df"

# RFC 8032 test-vector public key.  This independent literal is never paired
# with private bytes in the repository and is deliberately different from the
# runtime-generated signing key used by the controls below.
_OTHER_PUBLIC_KEY_RAW = bytes.fromhex(
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
)

_EXPECTED_SIGNED_ROOT_FIELDS = frozenset(
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
        "lease_generation",
        "checker_content_sha256",
        "issuer_key_id",
        "issuer_signature",
    }
)


def _production_v5() -> dict[str, object]:
    value = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _signed_control(
    *,
    issuer_key_id: str | None = None,
    private_key: Ed25519PrivateKey | None = None,
) -> tuple[dict[str, object], signing.ConfiguredPublicKey]:
    signing_key = private_key or Ed25519PrivateKey.generate()
    public_key = signing_key.public_key()
    key_id = issuer_key_id or signing.public_key_id(public_key)
    payload = signing.project_v5_receipt(
        _production_v5(),
        lease_generation=_LEASE_GENERATION,
        checker_content_sha256=_CHECKER_CONTENT_SHA256,
        issuer_key_id=key_id,
    )
    signature = signing_key.sign(signing.canonical_signed_payload_bytes(payload))
    receipt = signing.attach_signature(payload, signature)
    return receipt, signing.ConfiguredPublicKey(key_id, public_key)


def _verify(
    receipt: dict[str, object],
    configured_key: signing.ConfiguredPublicKey,
    *,
    tested_tip: str = _PRODUCTION_TIP,
    lease_generation: str = _LEASE_GENERATION,
) -> dict[str, object]:
    return signing.verify_signed_receipt_signature(
        receipt,
        configured_key,
        expected_acceptance_wave=_PRODUCTION_WAVE,
        expected_tested_main=_PRODUCTION_MAIN,
        expected_tested_tip=tested_tip,
        expected_lease_generation=lease_generation,
    )


def _verify_configured_key(receipt: dict[str, object]) -> dict[str, object]:
    return signing.verify_configured_key_signed_receipt(
        receipt,
        expected_acceptance_wave=_PRODUCTION_WAVE,
        expected_tested_main=_PRODUCTION_MAIN,
        expected_tested_tip=_PRODUCTION_TIP,
        expected_lease_generation=_LEASE_GENERATION,
    )


def _write_public_pem(path: Path, key: object) -> None:
    path.write_bytes(
        key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


@contextmanager
def _test_configured_key_files():
    """Install fixed-path test PEM A and attacker PEM B for one control."""

    configured_private_key = Ed25519PrivateKey.generate()
    attacker_private_key = Ed25519PrivateKey.generate()
    previous_path = signing.CONFIGURED_PUBLIC_KEY_PATH
    with tempfile.TemporaryDirectory(prefix="izanagi-configured-key-test-") as raw:
        root = Path(raw)
        configured_path = root / "configured-A.pem"
        attacker_path = root / "attacker-B.pem"
        _write_public_pem(configured_path, configured_private_key.public_key())
        _write_public_pem(attacker_path, attacker_private_key.public_key())
        signing.CONFIGURED_PUBLIC_KEY_PATH = configured_path
        try:
            yield (
                configured_private_key,
                attacker_private_key,
                configured_path,
                attacker_path,
                root,
            )
        finally:
            signing.CONFIGURED_PUBLIC_KEY_PATH = previous_path


def _assert_rejected(action) -> None:
    try:
        action()
    except signing.ReceiptSignatureError:
        return
    raise AssertionError("negative control unexpectedly passed")


def _assert_rejected_for(action, expected_message: str) -> None:
    try:
        action()
    except signing.ReceiptSignatureError as exc:
        assert str(exc) == expected_message
        return
    raise AssertionError("negative control unexpectedly passed")


def test_recorded_production_v5_receipt_passes_canonical_projection():
    """D431 positive: the tracked production receipt reaches this predicate."""

    raw = _FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _PRODUCTION_FIXTURE_SHA256
    receipt = _production_v5()
    assert len(receipt) == 27
    assert receipt["acceptance_wave"] == _PRODUCTION_WAVE
    assert receipt["tested_main"] == _PRODUCTION_MAIN
    assert receipt["tested_tip"] == _PRODUCTION_TIP
    payload = signing.project_v5_receipt(
        receipt,
        lease_generation=_LEASE_GENERATION,
        checker_content_sha256=_CHECKER_CONTENT_SHA256,
        issuer_key_id=_PROJECTION_KEY_ID,
    )
    canonical = signing.canonical_signed_payload_bytes(payload)
    assert len(canonical) == _PRODUCTION_PROJECTED_BYTES
    assert hashlib.sha256(canonical).hexdigest() == _PRODUCTION_PROJECTED_SHA256


def test_recorded_projection_rejects_missing_v5_root_field():
    """D431 anti-tautology pair: the projection does not accept both classes."""

    receipt = _production_v5()
    del receipt["verdict"]
    _assert_rejected(
        lambda: signing.project_v5_receipt(
            receipt,
            lease_generation=_LEASE_GENERATION,
            checker_content_sha256=_CHECKER_CONTENT_SHA256,
            issuer_key_id=_PROJECTION_KEY_ID,
        )
    )


def test_reference_issuer_parses_recorded_canonical_v5_fixture():
    receipt = issuer._parse_v5_receipt(_FIXTURE.read_bytes())
    assert receipt["acceptance_wave"] == _PRODUCTION_WAVE
    assert receipt["tested_main"] == _PRODUCTION_MAIN
    assert receipt["tested_tip"] == _PRODUCTION_TIP


def test_signed_v6_signature_covers_every_root_field_except_itself():
    receipt, _configured_key = _signed_control()
    assert set(receipt) == _EXPECTED_SIGNED_ROOT_FIELDS
    payload = json.loads(
        signing.canonical_signed_payload_bytes(
            {
                key: value
                for key, value in receipt.items()
                if key != "issuer_signature"
            }
        )
    )
    assert set(payload) == _EXPECTED_SIGNED_ROOT_FIELDS - {"issuer_signature"}
    for required in (
        "acceptance_wave",
        "tested_main",
        "tested_tip",
        "lease_holder",
        "lease_generation",
        "runner_executed_sha256",
        "checker_content_sha256",
        "verdict",
        "issuer_key_id",
    ):
        assert required in payload


def test_valid_test_signature_and_exact_context_pass():
    # This is a test-key functional control, not the unavailable production
    # signed-v6 positive control.
    receipt, configured_key = _signed_control()
    payload = _verify(receipt, configured_key)
    assert payload["tested_tip"] == _PRODUCTION_TIP
    assert payload["lease_generation"] == _LEASE_GENERATION


def test_missing_issuer_signature_is_rejected():
    receipt, configured_key = _signed_control()
    del receipt["issuer_signature"]
    _assert_rejected(lambda: _verify(receipt, configured_key))


def test_different_public_key_is_rejected():
    wrong_public_key = Ed25519PublicKey.from_public_bytes(_OTHER_PUBLIC_KEY_RAW)
    wrong_key_id = signing.public_key_id(wrong_public_key)
    receipt, _actual_key = _signed_control(issuer_key_id=wrong_key_id)
    wrong_configuration = signing.ConfiguredPublicKey(wrong_key_id, wrong_public_key)
    _assert_rejected(lambda: _verify(receipt, wrong_configuration))


def test_unsigned_tested_tip_tamper_is_rejected():
    receipt, configured_key = _signed_control()
    tampered = copy.deepcopy(receipt)
    tampered["tested_tip"] = _OTHER_TIP
    # Match the expected context to the tamper so only signature coverage can
    # reject this otherwise well-formed value.
    _assert_rejected(
        lambda: _verify(tampered, configured_key, tested_tip=_OTHER_TIP)
    )


def test_signed_receipt_replay_into_other_context_is_rejected():
    receipt, configured_key = _signed_control()
    _assert_rejected(
        lambda: _verify(
            receipt,
            configured_key,
            lease_generation=_OTHER_LEASE_GENERATION,
        )
    )


def test_signed_receipt_replay_to_other_tested_tip_context_is_rejected():
    receipt, configured_key = _signed_control()
    _assert_rejected(
        lambda: _verify(receipt, configured_key, tested_tip=_OTHER_TIP)
    )


def test_configured_key_boundary_accepts_test_key_A():
    # Test-key functional control only.  Production signed-v6 remains unmet.
    with _test_configured_key_files() as keys:
        configured_private_key, _attacker, _path_a, _path_b, _root = keys
        receipt, _configured_key = _signed_control(
            private_key=configured_private_key
        )
        payload = _verify_configured_key(receipt)
        assert payload["tested_tip"] == _PRODUCTION_TIP


def test_configured_key_boundary_rejects_attacker_key_B_signature():
    with _test_configured_key_files() as keys:
        configured_private_key, attacker_private_key, _path_a, _path_b, _root = keys
        configured_key_id = signing.public_key_id(
            configured_private_key.public_key()
        )
        receipt, _attacker_key = _signed_control(
            private_key=attacker_private_key,
            issuer_key_id=configured_key_id,
        )
        _assert_rejected_for(
            lambda: _verify_configured_key(receipt),
            "signed receipt signature is invalid",
        )


def test_configured_key_loader_ignores_environment_substitution():
    with _test_configured_key_files() as keys:
        configured_private_key, _attacker, _path_a, attacker_path, _root = keys
        receipt, _configured_key = _signed_control(
            private_key=configured_private_key
        )
        expected_key_id = signing.public_key_id(configured_private_key.public_key())
        previous = os.environ.get("IZANAGI_ACCEPTANCE_PUBLIC_KEY")
        os.environ["IZANAGI_ACCEPTANCE_PUBLIC_KEY"] = str(attacker_path)
        try:
            configured_key = signing.load_configured_public_key()
            assert configured_key.key_id == expected_key_id
            assert _verify_configured_key(receipt)["issuer_key_id"] == expected_key_id
        finally:
            if previous is None:
                os.environ.pop("IZANAGI_ACCEPTANCE_PUBLIC_KEY", None)
            else:
                os.environ["IZANAGI_ACCEPTANCE_PUBLIC_KEY"] = previous


def test_configured_key_boundary_rejects_missing_fixed_path():
    with _test_configured_key_files() as keys:
        configured_private_key, _attacker, _path_a, _path_b, root = keys
        receipt, _configured_key = _signed_control(
            private_key=configured_private_key
        )
        signing.CONFIGURED_PUBLIC_KEY_PATH = root / "missing.pem"
        _assert_rejected_for(
            lambda: _verify_configured_key(receipt),
            "configured public key is unavailable",
        )


def test_configured_key_boundary_rejects_malformed_pem():
    with _test_configured_key_files() as keys:
        configured_private_key, _attacker, _path_a, _path_b, root = keys
        receipt, _configured_key = _signed_control(
            private_key=configured_private_key
        )
        malformed_path = root / "malformed.pem"
        malformed_path.write_bytes(b"not a PEM public key\n")
        signing.CONFIGURED_PUBLIC_KEY_PATH = malformed_path
        _assert_rejected_for(
            lambda: _verify_configured_key(receipt),
            "configured public key format is invalid",
        )


def test_configured_key_boundary_rejects_non_ed25519_pem():
    with _test_configured_key_files() as keys:
        configured_private_key, _attacker, _path_a, _path_b, root = keys
        receipt, _configured_key = _signed_control(
            private_key=configured_private_key
        )
        non_ed25519_path = root / "non-ed25519.pem"
        non_ed25519_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        ).public_key()
        _write_public_pem(non_ed25519_path, non_ed25519_key)
        signing.CONFIGURED_PUBLIC_KEY_PATH = non_ed25519_path
        _assert_rejected_for(
            lambda: _verify_configured_key(receipt),
            "configured public key is not Ed25519",
        )


def _run() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001 - plain-runner result envelope
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
