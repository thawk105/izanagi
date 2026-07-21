# -*- coding: utf-8 -*-
"""Allowlist redaction and sanitized-error tests with a plain runner."""
from __future__ import annotations

import importlib
import json
import sys
import traceback
import types
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
_PKG = "_izanagi_unit_a_dev_waves"
if _PKG not in sys.modules:
    package = types.ModuleType(_PKG)
    package.__path__ = [str(_ROOT / "tools" / "dev_waves")]
    package.__package__ = _PKG
    sys.modules[_PKG] = package
redaction = importlib.import_module(f"{_PKG}.redaction")
schema = importlib.import_module(f"{_PKG}.schema")


def test_sanitized_artifacts_remove_keys_tokens_sessions_urls_and_environment():
    raw = {
        "run_id": "run-001",
        "state": "failed",
        "reason": "output-invalid",
        "token": "sk-fixture-secret-value",
        "api_key": "api-fixture-secret",
        "password": "password-fixture-secret",
        "credential": "/private/credential",
        "session_id": "session-secret-id",
        "session_url": "https://session.invalid/private",
        "environment": {"HOME": "/private/home", "CLAUDE_API_KEY": "secret"},
        "message": "visit https://session.invalid/private",
        "detail": {
            "label": "stdout",
            "kind": "parse",
            "secret": "nested-secret",
        },
    }
    clean = redaction.redact_value(raw)
    encoded = json.dumps(clean, sort_keys=True)
    assert clean["run_id"] == "run-001"
    assert clean["message"] == redaction.REDACTED
    assert set(clean["detail"]) == {"label", "kind"}
    for forbidden in (
        "sk-fixture-secret-value", "api-fixture-secret", "password-fixture-secret",
        "/private/credential", "session-secret-id", "session.invalid", "/private/home",
        "nested-secret", "environment", "api_key", "session_id",
    ):
        assert forbidden not in encoded
    redaction.assert_sanitized(clean)


def test_allowlist_omits_unreviewed_fields_instead_of_guessing_safety():
    clean = redaction.redact_value({
        "run_id": "run-1",
        "apparently_harmless_new_field": "value",
    })
    assert clean == {"run_id": "run-1"}


def test_redact_argv_preserves_token_boundaries_and_hides_both_option_forms():
    argv = (
        "fake-child", "--token=first-secret", "--password", "second-secret",
        "--model=claude-test-20260721", "https://session.invalid/path",
    )
    clean = redaction.redact_argv(argv)
    assert clean == (
        "fake-child", "--token=<redacted>", "--password", "<redacted>",
        "--model=claude-test-20260721", "<redacted>",
    )
    assert len(clean) == len(argv)


def test_argv_digest_is_computed_from_redacted_representation():
    first = ("fake-child", "--token=secret-one", "--model=fixed")
    second = ("fake-child", "--token=secret-two", "--model=fixed")
    first_clean = redaction.redact_argv(first)
    second_clean = redaction.redact_argv(second)
    assert first_clean == second_clean
    assert redaction.safe_digest(first_clean) == redaction.safe_digest(second_clean)
    # Positive control: hashing unsanitized argv would distinguish the raw secret.
    assert redaction.safe_digest(first) != redaction.safe_digest(second)


def test_dev_waves_error_sanitizes_detail_at_construction():
    error = schema.DevWavesError(schema.ReasonCode.OUTPUT_INVALID, {
        "label": "child-output",
        "kind": "parse-failed",
        "message": "https://session.invalid/private",
        "token": "sk-fixture-secret-value",
        "unexpected": "raw-value",
        "actual": "raw-child-value-that-looks-safe",
    })
    encoded = json.dumps(error.detail, sort_keys=True)
    assert str(error) == "output-invalid"
    assert error.detail == {
        "label": "child-output",
        "kind": "parse-failed",
    }
    assert "session.invalid" not in encoded
    assert "sk-fixture" not in encoded
    assert "raw-value" not in encoded
    assert "raw-child-value-that-looks-safe" not in encoded


def test_free_form_error_detail_keeps_only_digest_and_length():
    raw = "failure at https://session.invalid/path token=secret"
    error = schema.DevWavesError(schema.ReasonCode.RUNTIME_IO_FAILURE, raw)
    assert error.detail["kind"] == "detail-omitted"
    assert error.detail["byte_length"] == len(raw.encode())
    assert len(error.detail["sha256"]) == 64
    assert raw not in json.dumps(error.detail)


def test_assert_sanitized_has_sensitive_positive_controls():
    redaction.assert_sanitized({"label": "safe", "kind": "fixture"})
    bad_values = (
        {"token": "secret"},
        {"message": "https://session.invalid/private"},
        {"unknown": "value"},
    )
    for value in bad_values:
        try:
            redaction.assert_sanitized(value)
        except ValueError:
            continue
        raise AssertionError(f"sensitive positive control が通過した: {value!r}")


def _run():
    fns = [value for name, value in sorted(globals().items())
           if name.startswith("test_") and callable(value)]
    passed = failed = errors = 0
    for fn in fns:
        try:
            fn()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed, {errors} errors (of {len(fns)})")
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
