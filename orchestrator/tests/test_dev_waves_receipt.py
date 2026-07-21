# -*- coding: utf-8 -*-
"""Claude envelope/receipt tests with hermetic real-record-derived fixture."""
from __future__ import annotations

import copy
import importlib
import json
import os
import sys
import tempfile
import threading
import traceback
import types
import unittest
from decimal import Decimal
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
_PKG = "_izanagi_unit_a_dev_waves"
if _PKG not in sys.modules:
    package = types.ModuleType(_PKG)
    package.__path__ = [str(_ROOT / "tools" / "dev_waves")]
    package.__package__ = _PKG
    sys.modules[_PKG] = package
schema = importlib.import_module(f"{_PKG}.schema")
receipt_mod = importlib.import_module(f"{_PKG}.receipt")


_RUN_ID = "run-fixture-001"
_BASE = "a" * 40
_LANDED = "b" * 40
_BINDING = receipt_mod.ReceiptBinding(_RUN_ID, 1, _BASE)


def _valid_receipt():
    return {
        "schema_version": 1,
        "supervisor_run_id": _RUN_ID,
        "wave_index": 1,
        "outcome": "completed",
        "stop_reason": "wave-completed",
        "base_main_sha": _BASE,
        "landed_main_sha": _LANDED,
        "selected_task_ids": ["T-076"],
        "next_task_ids": ["T-004", "T-001"],
        "landed_commits": [_LANDED],
        "child_task_run_id": "task-run-fixture-001",
    }


def _real_record_derived_envelope():
    """Shape copied from output/s6-rounds/runs/c4-00.attempt0.json raw.stdout.

    Session/UUID values, free text, model usage, and any URL/secret-bearing data
    are replaced.  structured_output is added because that historical call did
    not request a JSON schema; all real envelope compatibility keys are retained.
    """
    return {
        "api_error_status": None,
        "duration_api_ms": 1000,
        "duration_ms": 1200,
        "fast_mode_state": "off",
        "is_error": False,
        "modelUsage": {},
        "num_turns": 1,
        "permission_denials": [],
        "result": "[natural-language-result-redacted]",
        "session_id": "[session-id-redacted]",
        "stop_reason": None,
        "structured_output": _valid_receipt(),
        "subtype": "success",
        "terminal_reason": None,
        "time_to_request_ms": 10,
        "total_cost_usd": 0.48689599999999994,
        "ttft_ms": 20,
        "ttft_stream_ms": 21,
        "type": "result",
        "usage": {},
        "uuid": "[uuid-redacted]",
    }


def _raw(envelope=None):
    if envelope is None:
        envelope = _real_record_derived_envelope()
    return json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()


def _write(temp, raw):
    path = Path(temp) / "stdout.json"
    path.write_bytes(raw)
    return path


def _expect_error(fn, code=None):
    try:
        fn()
    except schema.DevWavesError as exc:
        if code is not None:
            assert exc.code is code, (exc.code, code)
        return
    raise AssertionError("不正 envelope/receipt が拒否されなかった")


def test_real_record_derived_single_result_binds_decimal_and_receipt():
    with tempfile.TemporaryDirectory(prefix="izanagi_receipt_") as temp:
        path = _write(temp, _raw())
        parsed = receipt_mod.parse_claude_result(
            path, max_bytes=100000, binding=_BINDING,
        )
    assert parsed.receipt.supervisor_run_id == _RUN_ID
    assert parsed.receipt.landed_commits == (_LANDED,)
    assert parsed.total_cost_usd == Decimal("0.48689599999999994")
    assert parsed.subtype == "success"
    assert not parsed.is_error
    assert not parsed.permission_denials
    assert not parsed.permission_abort


def test_only_structured_output_can_supply_receipt():
    envelope = _real_record_derived_envelope()
    envelope["result"] = json.dumps(_valid_receipt())
    envelope["structured_output"] = None
    with tempfile.TemporaryDirectory(prefix="izanagi_receipt_prose_") as temp:
        path = _write(temp, _raw(envelope))
        _expect_error(
            lambda: receipt_mod.parse_claude_result(
                path, max_bytes=100000, binding=_BINDING,
            ),
            schema.ReasonCode.RECEIPT_INVALID,
        )


def test_permission_abort_has_independent_denial_and_subtype_paths():
    denial = _real_record_derived_envelope()
    denial["permission_denials"] = [{"tool_name": "Bash", "tool_input": "[redacted]"}]
    subtype = _real_record_derived_envelope()
    subtype["subtype"] = "permission_denied"
    subtype["is_error"] = True
    for envelope in (denial, subtype):
        with tempfile.TemporaryDirectory(prefix="izanagi_receipt_denial_") as temp:
            path = _write(temp, _raw(envelope))
            _expect_error(
                lambda path=path: receipt_mod.parse_claude_result(
                    path, max_bytes=100000, binding=_BINDING,
                )
            )
            assert receipt_mod.permission_abort_from_envelope(path, max_bytes=100000)


def test_envelope_accepts_only_success_false_empty_denials_matrix():
    for subtype in receipt_mod.CLAUDE_RESULT_SUBTYPES:
        for is_error in (False, True):
            envelope = _real_record_derived_envelope()
            envelope["subtype"] = subtype
            envelope["is_error"] = is_error
            with tempfile.TemporaryDirectory(prefix="izanagi_receipt_status_") as temp:
                path = _write(temp, _raw(envelope))
                accepted = subtype == "success" and is_error is False
                if accepted:
                    receipt_mod.parse_claude_result(path, max_bytes=100000, binding=_BINDING)
                else:
                    _expect_error(lambda path=path: receipt_mod.parse_claude_result(
                        path, max_bytes=100000, binding=_BINDING,
                    ), schema.ReasonCode.OUTPUT_INVALID)


def test_truncated_multiple_trailing_oversize_and_wrong_type_are_rejected():
    complete = _raw()
    cases = (
        (complete[:-1], 100000),
        (complete + b"\n" + complete, 200000),
        (complete + b"x", 100000),
    )
    for raw, limit in cases:
        with tempfile.TemporaryDirectory(prefix="izanagi_receipt_bad_envelope_") as temp:
            path = _write(temp, raw)
            _expect_error(lambda path=path, limit=limit: receipt_mod.parse_claude_result(
                path, max_bytes=limit, binding=_BINDING,
            ), schema.ReasonCode.OUTPUT_INVALID)

    with tempfile.TemporaryDirectory(prefix="izanagi_receipt_oversize_") as temp:
        path = _write(temp, complete)
        _expect_error(lambda: receipt_mod.parse_claude_result(
            path, max_bytes=len(complete) - 1, binding=_BINDING,
        ), schema.ReasonCode.OUTPUT_INVALID)

    wrong = _real_record_derived_envelope()
    wrong["type"] = "assistant"
    with tempfile.TemporaryDirectory(prefix="izanagi_receipt_wrong_type_") as temp:
        path = _write(temp, _raw(wrong))
        _expect_error(lambda: receipt_mod.parse_claude_result(
            path, max_bytes=100000, binding=_BINDING,
        ), schema.ReasonCode.OUTPUT_INVALID)


def test_delayed_partial_file_is_rejected_without_waiting_for_append():
    complete = _raw()
    ready = threading.Event()
    release = threading.Event()
    with tempfile.TemporaryDirectory(prefix="izanagi_receipt_partial_") as temp:
        path = Path(temp) / "stdout.json"

        def writer():
            with path.open("wb") as stream:
                stream.write(complete[:len(complete) // 2])
                stream.flush()
                os.fsync(stream.fileno())
                ready.set()
                release.wait(2)
                stream.write(complete[len(complete) // 2:])

        thread = threading.Thread(target=writer)
        thread.start()
        assert ready.wait(1)
        try:
            _expect_error(lambda: receipt_mod.parse_claude_result(
                path, max_bytes=100000, binding=_BINDING,
            ), schema.ReasonCode.OUTPUT_INVALID)
        finally:
            release.set()
            thread.join(2)
        assert not thread.is_alive()


def test_receipt_strict_json_rejects_duplicate_unknown_nul_invalid_utf8_nan_and_oversize():
    valid = _raw()
    duplicate = valid.replace(b'"wave_index":1', b'"wave_index":1,"wave_index":2', 1)
    unknown_envelope = _real_record_derived_envelope()
    unknown_envelope["new_secret_field"] = "x"
    raws = (
        duplicate,
        _raw(unknown_envelope),
        valid.replace(b'"result":"', b'"result":"x\\u0000', 1),
        valid.replace(b'"result":"', b'"result":"\xff', 1),
        valid.replace(b'"total_cost_usd":0.48689599999999994', b'"total_cost_usd":NaN', 1),
    )
    for raw in raws:
        with tempfile.TemporaryDirectory(prefix="izanagi_receipt_strict_") as temp:
            path = _write(temp, raw)
            _expect_error(lambda path=path: receipt_mod.parse_claude_result(
                path, max_bytes=100000, binding=_BINDING,
            ), schema.ReasonCode.OUTPUT_INVALID)


def test_completed_and_noncompleted_fields_are_mutually_closed():
    assert receipt_mod.validate_child_receipt(_valid_receipt(), binding=_BINDING)
    completed_no_sha = _valid_receipt()
    completed_no_sha["landed_main_sha"] = None
    _expect_error(lambda: receipt_mod.validate_child_receipt(completed_no_sha))

    for outcome, reason in (
        ("no-actionable-task", "no-actionable-task"),
        ("user-ruling-required", "user-ruling-required"),
        ("blocked", "check-failed"),
        ("failed", "nonzero-exit"),
    ):
        value = _valid_receipt()
        value.update(
            outcome=outcome, stop_reason=reason, landed_main_sha=None, landed_commits=[],
        )
        assert receipt_mod.validate_child_receipt(value)
        value["landed_commits"] = [_LANDED]
        _expect_error(lambda value=value: receipt_mod.validate_child_receipt(value))


def test_binding_rejects_run_wave_and_base_independently():
    mutations = (
        ("supervisor_run_id", "other-run"),
        ("wave_index", 2),
        ("base_main_sha", "c" * 40),
    )
    for field, new_value in mutations:
        value = _valid_receipt()
        value[field] = new_value
        _expect_error(
            lambda value=value: receipt_mod.validate_child_receipt(value, binding=_BINDING),
            schema.ReasonCode.RECEIPT_INVALID,
        )


def test_manual_validator_and_schema_v1_acceptance_match_mutation_matrix():
    try:
        import jsonschema
    except ImportError:
        raise unittest.SkipTest("jsonschema is not installed; optional cross-check skipped")
    document = receipt_mod.load_receipt_schema()
    validator = jsonschema.Draft7Validator(document)
    fixtures = [_valid_receipt()]
    mutations = []
    for field in _valid_receipt():
        value = _valid_receipt()
        value.pop(field)
        mutations.append(value)
    value = _valid_receipt(); value["unknown"] = 1; mutations.append(value)
    value = _valid_receipt(); value["wave_index"] = True; mutations.append(value)
    value = _valid_receipt(); value["base_main_sha"] = "A" * 40; mutations.append(value)
    value = _valid_receipt(); value["outcome"] = "other"; mutations.append(value)
    value = _valid_receipt(); value["landed_commits"] = []; mutations.append(value)
    value = _valid_receipt(); value["selected_task_ids"] = ["T-076", "T-076"]; mutations.append(value)
    value = _valid_receipt(); value["selected_task_ids"] = []; mutations.append(value)
    value = _valid_receipt(); value["selected_task_ids"] = ["T-１２３"]; mutations.append(value)
    value = _valid_receipt(); value["supervisor_run_id"] = "run-１２３"; mutations.append(value)
    fixtures.extend(mutations)
    for index, value in enumerate(fixtures):
        schema_accepts = not list(validator.iter_errors(value))
        try:
            receipt_mod.validate_child_receipt(value)
            manual_accepts = True
        except schema.DevWavesError:
            manual_accepts = False
        assert manual_accepts == schema_accepts, (index, manual_accepts, schema_accepts)


def test_schema_reason_enum_matches_python_closed_enum():
    document = receipt_mod.load_receipt_schema()
    assert set(document["properties"]["stop_reason"]["enum"]) == {
        reason.value for reason in schema.ReasonCode
    }
    digest = receipt_mod.receipt_schema_digest()
    assert len(digest) == 64 and set(digest) <= set("0123456789abcdef")


def test_persist_sanitized_receipt_is_create_only():
    parsed = receipt_mod.validate_child_receipt(_valid_receipt())
    with tempfile.TemporaryDirectory(prefix="izanagi_receipt_persist_") as temp:
        path = Path(temp) / "receipt.json"
        receipt_mod.persist_sanitized_receipt(path, parsed)
        assert json.loads(path.read_text()) == _valid_receipt()
        try:
            receipt_mod.persist_sanitized_receipt(path, parsed)
        except FileExistsError:
            pass
        else:
            raise AssertionError("既存 receipt が置換された")


def _run():
    fns = [value for name, value in sorted(globals().items())
           if name.startswith("test_") and callable(value)]
    passed = failed = errors = skipped = 0
    for fn in fns:
        try:
            fn()
            passed += 1
        except unittest.SkipTest as exc:
            skipped += 1
            print(f"SKIP {fn.__name__}: {exc}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(
        f"\n{passed} passed, {skipped} skipped, {failed} failed, "
        f"{errors} errors (of {len(fns)})"
    )
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
