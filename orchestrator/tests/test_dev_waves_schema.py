# -*- coding: utf-8 -*-
"""dev-waves shared schema tests (pytest and plain-Python dual runner)."""
from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import hashlib
import os
import sys
import traceback
import types
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


def _expect_error(fn, code=None):
    try:
        fn()
    except schema.DevWavesError as exc:
        if code is not None:
            assert exc.code is code, (exc.code, code)
        return exc
    raise AssertionError("DevWavesError が発生しなかった")


def _submit(limits=None):
    if limits is None:
        limits = {
            "per_wave_timeout_s": 10,
            "total_timeout_s": 25,
            "per_wave_budget_usd": "1.25",
            "total_budget_usd": "3.5",
            "max_wave_output_bytes": 1000,
            "max_run_bytes": 100000,
        }
    return {
        "protocol_version": 1,
        "action": "submit",
        "repo_identity": "a" * 64,
        "max_waves": 3,
        "profile": "default",
        "client_request_id": "123e4567-e89b-42d3-a456-426614174000",
        "limits": limits,
    }


def _raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def test_enums_include_v2_closed_values():
    required = {
        "fake-handshake-failed", "settings-invalid", "trust-root-changed",
        "request-conflict", "foreign-lease", "poisoned",
    }
    assert required <= {item.value for item in schema.ReasonCode}
    assert {item.value for item in schema.Outcome} == {
        "completed", "no-actionable-task", "user-ruling-required", "blocked", "failed",
    }
    assert {item.value for item in schema.RunState} == {
        "created", "preflight", "ready", "wave-prepared", "child-running",
        "child-exited", "verifying", "wave-accepted", "stopping", "completed",
        "blocked", "failed", "interrupted",
    }


def test_state_machine_accepts_exact_allowed_edge_set():
    literal_edges = {
        ("created", "preflight"), ("preflight", "ready"),
        ("ready", "wave-prepared"), ("wave-prepared", "child-running"),
        ("child-running", "child-exited"), ("child-exited", "verifying"),
        ("verifying", "wave-accepted"), ("wave-accepted", "ready"),
        ("wave-accepted", "completed"),
        ("stopping", "completed"), ("stopping", "blocked"),
        ("stopping", "failed"), ("stopping", "interrupted"),
    }
    literal_edges |= {
        (state.value, "stopping") for state in schema.NONTERMINAL_STATES
        if state is not schema.RunState.STOPPING
    }
    for current in schema.RunState:
        for target in schema.RunState:
            allowed = (current.value, target.value) in literal_edges
            if current is schema.RunState.STOPPING and target is schema.RunState.COMPLETED:
                if allowed:
                    schema.validate_transition(
                        current, target, reason=schema.ReasonCode.NO_ACTIONABLE_TASK,
                    )
                continue
            if allowed:
                schema.validate_transition(current, target)
            else:
                _expect_error(
                    lambda current=current, target=target:
                    schema.validate_transition(current, target),
                    schema.ReasonCode.INVALID_RUN,
                )


def test_stopping_completed_is_no_actionable_task_only():
    schema.validate_transition(
        schema.RunState.STOPPING, schema.RunState.COMPLETED,
        reason=schema.ReasonCode.NO_ACTIONABLE_TASK,
    )
    for reason in (None, schema.ReasonCode.MAX_WAVES_REACHED,
                   schema.ReasonCode.WAVE_COMPLETED):
        _expect_error(
            lambda reason=reason: schema.validate_transition(
                schema.RunState.STOPPING, schema.RunState.COMPLETED, reason=reason,
            ),
            schema.ReasonCode.INVALID_RUN,
        )


def test_terminal_states_have_no_outgoing_transition():
    for terminal in schema.TERMINAL_STATES:
        assert schema.ALLOWED_TRANSITIONS[terminal] == frozenset()


def test_strict_json_rejects_each_syntax_or_resource_boundary():
    cases = (
        b'{"a":1,"a":2}',
        b'{"a":"x\x00y"}',
        b'{"a":"\xff"}',
        b'{"a":NaN}',
        b'{"a":9223372036854775808}',
        b'{"a":1e101}',
        b'{"a":"\\ud800"}',
        (b'[' * schema.MAX_JSON_DEPTH + b'0' + b']' * schema.MAX_JSON_DEPTH),
        json.dumps({"a": "x" * (schema.MAX_JSON_STRING_CHARS + 1)}).encode(),
    )
    for raw in cases:
        _expect_error(
            lambda raw=raw: schema.strict_loads(raw, label="fixture", max_bytes=len(raw) + 1),
            schema.ReasonCode.OUTPUT_INVALID,
        )
    _expect_error(
        lambda: schema.strict_loads(b"{}", label="fixture", max_bytes=1),
        schema.ReasonCode.OUTPUT_INVALID,
    )


def test_strict_json_unknown_field_is_closed_when_boundary_supplies_allowlist():
    assert schema.strict_loads(
        b'{"known":1}', label="fixture", max_bytes=64, allowed_fields={"known"},
    ) == {"known": 1}
    _expect_error(
        lambda: schema.strict_loads(
            b'{"known":1,"extra":2}', label="fixture", max_bytes=64,
            allowed_fields={"known"},
        ),
        schema.ReasonCode.OUTPUT_INVALID,
    )


def test_parse_submit_converts_only_canonical_decimal_strings():
    request = schema.parse_request(_raw(_submit()))
    assert isinstance(request, schema.SubmitRequest)
    assert request.limits.per_wave_budget_usd == Decimal("1.25")
    assert request.limits.total_budget_usd == Decimal("3.5")
    assert schema.validate_limits(request) is request.limits
    assert json.loads(schema.canonical_bytes(request))["limits"]["per_wave_budget_usd"] == "1.25"
    for bad in ("01", "+1", "1.0", "1e0", "-1", 1.25):
        value = _submit()
        value["limits"]["per_wave_budget_usd"] = bad
        _expect_error(lambda value=value: schema.parse_request(_raw(value)))


def test_parse_request_rejects_duplicate_unknown_nul_invalid_utf8_nan_and_oversize():
    valid = _submit()
    mutations = []
    unknown = dict(valid)
    unknown["prompt"] = "do something"
    mutations.append(_raw(unknown))
    mutations.extend((
        b'{"action":"status","action":"cancel"}',
        b'{"action":"status","run_id":"x\x00y"}',
        b'{"action":"\xff"}',
        b'{"action":NaN}',
    ))
    for raw in mutations:
        _expect_error(lambda raw=raw: schema.parse_request(raw))
    huge = b" " * schema.DEFAULT_MAX_JSON_BYTES + b"{}"
    _expect_error(lambda: schema.parse_request(huge), schema.ReasonCode.INVALID_ARGS)


def test_budget_reservation_uses_decimal_and_never_exceeds_total():
    too_much_time = _submit()
    too_much_time["limits"]["total_timeout_s"] = 31
    req = schema.parse_request(_raw(too_much_time))
    _expect_error(lambda: schema.validate_limits(req), schema.ReasonCode.BUDGET_INVALID)

    too_much_cost = _submit()
    too_much_cost["limits"]["total_budget_usd"] = "3.76"
    req = schema.parse_request(_raw(too_much_cost))
    _expect_error(lambda: schema.validate_limits(req), schema.ReasonCode.BUDGET_INVALID)

    below_wave = _submit()
    below_wave["limits"]["total_budget_usd"] = "1"
    req = schema.parse_request(_raw(below_wave))
    _expect_error(lambda: schema.validate_limits(req), schema.ReasonCode.BUDGET_INVALID)


def test_missing_limits_remain_null_and_fail_preflight_without_defaults():
    value = _submit({key: None for key in (
        "per_wave_timeout_s", "total_timeout_s", "per_wave_budget_usd",
        "total_budget_usd", "max_wave_output_bytes", "max_run_bytes",
    )})
    request = schema.parse_request(_raw(value))
    assert all(item is None for item in dataclasses.astuple(request.limits))
    _expect_error(lambda: schema.validate_limits(request), schema.ReasonCode.BUDGET_INVALID)


def test_limit_signatures_have_no_numeric_defaults():
    for cls in (schema.ResourceLimits, schema.SubmitRequest):
        for parameter in inspect.signature(cls).parameters.values():
            assert parameter.default is inspect.Parameter.empty


def _valid_argv():
    schema_text = schema.canonical_bytes({"type": "object"}).decode()
    return [
        "-p", "--model=claude-test-20260721", "--effort=high",
        "--permission-mode=auto", "--output-format=json",
        f"--json-schema={schema_text}", "--max-budget-usd=1.25",
        "--add-dir=/repo/main", "/dev-wave --supervised-manifest /run/w001/manifest.json",
    ]


def test_exact_child_argv_accepts_only_canonical_order_and_equals_tokens():
    argv = _valid_argv()
    assert schema.validate_child_argv(argv) is None
    for index in range(len(argv)):
        bad = list(argv)
        bad[index] = "wrong"
        _expect_error(lambda bad=bad: schema.validate_child_argv(bad))
    forbidden = list(argv)
    forbidden[3] = "--dangerously-skip-permissions"
    _expect_error(lambda: schema.validate_child_argv(forbidden))
    split_option = list(argv)
    split_option[1:2] = ["--model", "claude-test-20260721"]
    _expect_error(lambda: schema.validate_child_argv(split_option))


def test_wire_dataclasses_are_frozen_and_canonical():
    response = schema.SubmitResponse(
        1, True, "run-1", schema.RunState.CREATED, None,
    )
    assert schema.encode_response(response) == (
        b'{"ok":true,"protocol_version":1,"reason":null,"run_id":"run-1","state":"created"}'
    )
    try:
        response.ok = False
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("wire dataclass が mutable")


def test_general_response_boundary_rejects_unknown_and_unsanitized_fields():
    response = schema.Response(
        1, "status", True, "run-1", schema.RunState.READY, 0,
        Decimal("1.25"), None, {"label": "status", "kind": "snapshot"},
    )
    parsed = schema.parse_response(schema.canonical_bytes(response))
    assert parsed == response
    value = json.loads(schema.canonical_bytes(response))
    value["raw_output"] = "secret"
    _expect_error(lambda: schema.parse_response(_raw(value)))
    value = json.loads(schema.canonical_bytes(response))
    value["detail"]["token"] = "secret"
    _expect_error(lambda: schema.parse_response(_raw(value)))


def test_manifest_and_worker_spec_boundaries_are_closed():
    limits = schema.ResourceLimits(10, 25, Decimal("1.25"), Decimal("3.5"), 1000, 100000)
    run = schema.RunManifest(
        1, "run-1", "a" * 64, "default", 3, limits,
        "2026-07-21T00:00:00Z", "b" * 64, "c" * 64, "d" * 64,
    )
    assert schema.parse_run_manifest(schema.canonical_bytes(run)) == run
    wave = schema.WaveManifest(
        1, "run-1", 1, "/runtime/w001", "/repo/main", "e" * 40, "f" * 64,
    )
    assert schema.parse_wave_manifest(schema.canonical_bytes(wave)) == wave

    receipt_schema_text = schema.canonical_bytes({"type": "object"}).decode()
    receipt_digest = hashlib.sha256(receipt_schema_text.encode()).hexdigest()
    worker = schema.WorkerSpec(
        1, "run-1", 1, "/bin/fake", "a" * 64, "/runtime/w001",
        (("HOME", "/isolated/home"), ("PATH", "/usr/bin")),
        "claude-test-20260721", "high", "/repo/main", "/runtime/w001/manifest.json",
        receipt_schema_text, receipt_digest, Decimal("1.25"), 10, 1000, 10000,
        "/runtime/w001/stdout.json", "/runtime/w001/stderr.log",
        "/runtime/w001/child-start.json", "/runtime/w001/worker-exit.json",
    )
    assert schema.parse_worker_spec(schema.canonical_bytes(worker)) == worker
    value = json.loads(schema.canonical_bytes(worker))
    value["scenario"] = "success"
    _expect_error(lambda: schema.parse_worker_spec(_raw(value)))
    value = json.loads(schema.canonical_bytes(worker))
    value["environment"]["CLAUDECODE"] = "1"
    _expect_error(lambda: schema.parse_worker_spec(_raw(value)))


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
