# -*- coding: utf-8 -*-
"""Closed trigger-gate binding schema and signature-stub tests."""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
_ROOT = _ORCH.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ORCH))

from campaign import loop, p3_s4_loop, pipeline  # noqa: E402
from campaign import reflux_ir as IR  # noqa: E402
from campaign import trigger_gate_binding as BINDING  # noqa: E402

_NONCE = "a5" * 32
_SOURCE_SHA256 = hashlib.sha256(b"source bytes").hexdigest()


def _binding(mask: int, *, source=True) -> BINDING.TriggerGateBinding:
    source_binding = None
    if source:
        source_binding = BINDING.SourceBinding(
            src_token="stock",
            source_bytes_sha256=_SOURCE_SHA256,
        )
    return BINDING.TriggerGateBinding(
        mask=mask,
        predicate_sha256=BINDING.expected_predicate_sha256(mask),
        nonce=_NONCE,
        source=source_binding,
    )


def _capture_rejection(function) -> BINDING.TriggerGateBindingError:
    try:
        function()
    except Exception as exc:  # noqa: BLE001 - exact public rejection is asserted
        assert type(exc) is BINDING.TriggerGateBindingError
        assert str(exc) == "invalid trigger gate binding"
        assert exc.args == ("invalid trigger gate binding",)
        assert exc.__context__ is None
        assert exc.__cause__ is None
        return exc
    raise AssertionError("TriggerGateBindingError expected")


def test_schema_and_wal_stage_constants_are_exact():
    assert BINDING.SCHEMA_VERSION == "izanagi-trigger-gate-binding/v1"
    assert BINDING.WAL_RECORD_STAGE == "trigger_binding"
    record = BINDING.to_record(_binding(0, source=False))
    assert set(record) == {
        "schema_version",
        "ir_schema",
        "mask",
        "predicate_sha256",
        "nonce",
        "source",
    }
    assert record["ir_schema"] == IR.SCHEMA_ID


def test_all_masks_construct_and_commit_deterministically():
    bindings = [_binding(mask) for mask in range(32)]
    assert [binding.mask for binding in bindings] == list(range(32))
    for binding in bindings:
        expected = hashlib.sha256(BINDING.canonical_json(binding)).hexdigest()
        assert BINDING.commitment(binding) == expected
        assert BINDING.commitment(binding) == BINDING.commitment(binding)
        assert BINDING.validate_record(
            BINDING.to_record(binding), require_source=True
        ) == binding


@pytest.mark.parametrize(
    "mask",
    [-1, 32, True, False, 1.0, "1", None],
)
def test_mask_rejects_non_exact_int_and_out_of_range(mask):
    _capture_rejection(
        lambda: BINDING.TriggerGateBinding(
            mask=mask,
            predicate_sha256="0" * 64,
            nonce=_NONCE,
            source=None,
        )
    )


def test_predicate_digest_must_match_mask():
    _capture_rejection(
        lambda: BINDING.TriggerGateBinding(
            mask=0,
            predicate_sha256=BINDING.expected_predicate_sha256(1),
            nonce=_NONCE,
            source=None,
        )
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("predicate_sha256", "0" * 63),
        ("predicate_sha256", "A" * 64),
        ("predicate_sha256", "g" * 64),
        ("predicate_sha256", b"0" * 64),
        ("nonce", "0" * 63),
        ("nonce", "A" * 64),
        ("nonce", "g" * 64),
        ("nonce", b"0" * 64),
    ],
)
def test_binding_sha_and_nonce_require_lowercase_hex(field, value):
    values = {
        "mask": 0,
        "predicate_sha256": BINDING.expected_predicate_sha256(0),
        "nonce": _NONCE,
        "source": None,
    }
    values[field] = value
    _capture_rejection(lambda: BINDING.TriggerGateBinding(**values))


@pytest.mark.parametrize(
    "src_token,source_sha256",
    [
        (1, _SOURCE_SHA256),
        ("stock", "0" * 63),
        ("stock", "A" * 64),
        ("stock", "g" * 64),
        ("stock", b"0" * 64),
    ],
)
def test_source_binding_fields_are_strict(src_token, source_sha256):
    _capture_rejection(
        lambda: BINDING.SourceBinding(
            src_token=src_token,
            source_bytes_sha256=source_sha256,
        )
    )


def test_record_key_closure_versions_and_required_source_reject():
    record = BINDING.to_record(_binding(20, source=False))

    extra = dict(record)
    extra["extra"] = None
    missing = dict(record)
    del missing["nonce"]
    unknown_version = dict(record)
    unknown_version["schema_version"] = "izanagi-trigger-gate-binding/v2"
    unknown_ir = dict(record)
    unknown_ir["ir_schema"] = "izanagi-trigger-gate-ir/v2"

    for invalid in (extra, missing, unknown_version, unknown_ir):
        _capture_rejection(
            lambda invalid=invalid: BINDING.validate_record(
                invalid, require_source=False
            )
        )
    _capture_rejection(
        lambda: BINDING.validate_record(record, require_source=True)
    )


def test_nested_source_record_has_closed_keys():
    record = BINDING.to_record(_binding(20))
    extra = dict(record)
    extra["source"] = dict(record["source"], extra=None)
    missing = dict(record)
    missing_source = dict(record["source"])
    del missing_source["src_token"]
    missing["source"] = missing_source
    for invalid in (extra, missing):
        _capture_rejection(
            lambda invalid=invalid: BINDING.validate_record(
                invalid, require_source=True
            )
        )


def test_rejections_have_one_disclosure_free_fingerprint():
    failures = [
        lambda: BINDING.expected_predicate_sha256(True),
        lambda: BINDING.validate_record([], require_source=False),
        lambda: BINDING.validate_record({}, require_source=False),
        lambda: BINDING.validate_record(
            BINDING.to_record(_binding(0)), require_source=1
        ),
        lambda: BINDING.to_record(object()),
    ]
    fingerprints = {
        (type(exc), str(exc), exc.args, exc.__context__, exc.__cause__)
        for exc in (_capture_rejection(failure) for failure in failures)
    }
    assert fingerprints == {
        (
            BINDING.TriggerGateBindingError,
            "invalid trigger gate binding",
            ("invalid trigger gate binding",),
            None,
            None,
        )
    }


def test_canonical_predicate_membership_is_exact_after_outer_strip():
    predicates = {
        IR.emit_predicate(IR.TriggerGateIR(mask)).strip() for mask in range(32)
    }
    assert len(predicates) == 32
    assert BINDING.CANONICAL_PREDICATES == frozenset(predicates)
    for predicate in predicates:
        assert BINDING.is_canonical_predicate(predicate)
        assert BINDING.is_canonical_predicate(f" \n{predicate}\t")
    assert not BINDING.is_canonical_predicate("izanagi_gate_pass = true;")
    assert not BINDING.is_canonical_predicate("return arbitrary_cpp();")
    assert not BINDING.is_canonical_predicate(b"izanagi_gate_pass = true;")
    assert not BINDING.is_canonical_predicate(None)


def test_canonical_json_has_stable_sorted_key_order_and_source_none():
    binding = _binding(0, source=False)
    encoded = BINDING.canonical_json(binding)
    assert encoded == (
        b'{"ir_schema":"izanagi-trigger-gate-ir/v1","mask":0,'
        b'"nonce":"' + _NONCE.encode("ascii") +
        b'","predicate_sha256":"' + binding.predicate_sha256.encode("ascii") +
        b'","schema_version":"izanagi-trigger-gate-binding/v1","source":null}'
    )
    assert json.loads(encoded) == BINDING.to_record(binding)


def test_new_nonce_is_exact_lowercase_hex_and_changes_commitment():
    first = BINDING.new_nonce()
    second = BINDING.new_nonce()
    assert len(first) == len(second) == 64
    assert set(first) <= set("0123456789abcdef")
    assert set(second) <= set("0123456789abcdef")
    assert first != second
    base = _binding(7, source=False)
    changed = BINDING.TriggerGateBinding(
        mask=base.mask,
        predicate_sha256=base.predicate_sha256,
        nonce=first,
        source=base.source,
    )
    assert BINDING.commitment(base) != BINDING.commitment(changed)


def test_signature_stubs_keep_legacy_calls_valid_with_none_default():
    cases = [
        (
            loop.run_campaign,
            (object(), [], object(), "env", 1),
            {"build_context": object()},
        ),
        (
            pipeline.evaluate,
            (object(), object(), "env", "commit", object(), 1),
            {"build_context": object()},
        ),
        (
            p3_s4_loop.record_diff_reject,
            (object(), object(), "implementation", object()),
            {},
        ),
    ]
    for function, args, kwargs in cases:
        signature = inspect.signature(function)
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        parameter = signature.parameters["trigger_gate_binding"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None
        assert bound.arguments["trigger_gate_binding"] is None


def _run() -> int:
    """Keep this new test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
