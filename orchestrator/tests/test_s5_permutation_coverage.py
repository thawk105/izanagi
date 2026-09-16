# -*- coding: utf-8 -*-
"""s5 permutation coverage の独立 oracle 突合せテスト。"""
from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from orchestrator.campaign import s2_verify_calibration as s2
from orchestrator.campaign import s3_lock_coverage as s3
from orchestrator.campaign import s5_permutation_coverage as coverage


def _details(*, size_changed: int, rcdptr_set_changed: int, unknown: int) -> dict:
    return {
        "counts": {
            "size-changed": size_changed,
            "rcdptr-set-changed": rcdptr_set_changed,
            "unknown": unknown,
        },
        "sample": [],
        "unknown_reason_sample": [],
    }


def test_oracle_cross_check_accepts_exact_known_and_unknown_counts():
    assert coverage._oracle_cross_check(
        {
            "size-changed": 2,
            "rcdptr-set-changed": 1,
            "opaque-reason": 3,
        },
        _details(size_changed=2, rcdptr_set_changed=1, unknown=3),
    )


def test_oracle_cross_check_rejects_any_count_mismatch_or_malformed_details():
    p_reasons = {
        "size-changed": 2,
        "rcdptr-set-changed": 1,
        "opaque-reason": 3,
    }
    assert not coverage._oracle_cross_check(
        p_reasons, _details(size_changed=1, rcdptr_set_changed=1, unknown=3),
    )
    assert not coverage._oracle_cross_check(
        p_reasons, _details(size_changed=2, rcdptr_set_changed=0, unknown=3),
    )
    assert not coverage._oracle_cross_check(
        p_reasons, _details(size_changed=2, rcdptr_set_changed=1, unknown=2),
    )
    assert not coverage._oracle_cross_check(p_reasons, {})
    assert not coverage._oracle_cross_check(p_reasons, {"counts": {}})


def test_oracle_cross_check_rejects_unexpected_count_keys():
    details = _details(size_changed=2, rcdptr_set_changed=1, unknown=3)
    details["counts"]["new-kind"] = 0

    assert not coverage._oracle_cross_check(
        {
            "size-changed": 2,
            "rcdptr-set-changed": 1,
            "opaque-reason": 3,
        },
        details,
    )


def test_oracle_cross_check_rejects_negative_non_int_and_bool_values():
    valid_p_reasons = {"size-changed": 1}
    valid_details = _details(size_changed=1, rcdptr_set_changed=0, unknown=0)

    for invalid in (-1, "1", True, False):
        bad_counts = _details(
            size_changed=invalid, rcdptr_set_changed=0, unknown=0,
        )
        assert not coverage._oracle_cross_check(valid_p_reasons, bad_counts)

        bad_p_reasons = {"size-changed": invalid}
        assert not coverage._oracle_cross_check(bad_p_reasons, valid_details)


@pytest.mark.parametrize("module", [s2, s3, coverage])
def test_condition_preflight_dominates_first_benchmark_build(module):
    source = inspect.getsource(module.main)
    assert source.index("_preflight_condition_gates") < source.index("buildcache.build")
    if module in {s2, s3, coverage}:
        gate_source = inspect.getsource(module._require_condition_gate)
        assert "declare_define_runtime_meaning(request)" in gate_source


def test_condition_gate_rejection_stops_s5_before_build(monkeypatch):
    gate = coverage.condition_meaning_gate
    request = object()
    declaration = object()
    red = SimpleNamespace(
        terminal_status="red", reason_code="preprocess-bytes-identical",
    )
    unknown = SimpleNamespace(
        terminal_status="unestablished", reason_code="meaning-witness-undeclared",
    )
    monkeypatch.setattr(gate, "capture_define_inputs", lambda *_a, **_k: object())
    monkeypatch.setattr(gate, "make_define_request", lambda **_k: request)
    monkeypatch.setattr(
        gate, "declare_define_runtime_meaning",
        lambda observed: declaration if observed is request else pytest.fail(
            "factory did not receive the exact request",
        ),
    )
    monkeypatch.setattr(
        gate, "evaluate_define_supply_effectuation", lambda *_a, **_k: red,
    )

    def evaluate_meaning(*_args, **kwargs):
        assert kwargs["request"] is request
        assert kwargs["declaration"] is declaration
        return unknown

    monkeypatch.setattr(gate, "evaluate_define_runtime_meaning", evaluate_meaning)
    monkeypatch.setattr(
        gate, "require_condition_gate_family",
        lambda *_a, **_k: SimpleNamespace(admitted=False),
    )

    with pytest.raises(RuntimeError, match="preprocess-bytes-identical"):
        coverage._require_condition_gate("/fixture", coverage.ERASE_DEFINE)


@pytest.mark.parametrize("macro", [s2.NORW_DEFINE, s2.HIGHKEY_DEFINE])
@pytest.mark.parametrize("admitted", [True, False])
def test_s2_condition_gate_passes_factory_declaration_to_meaning_evaluator(
    monkeypatch: pytest.MonkeyPatch,
    macro: str,
    admitted: bool,
):
    gate = s2.condition_meaning_gate
    captured = object()
    calls = []
    supply_requests = []
    real = gate.declare_define_runtime_meaning
    supply_stub = SimpleNamespace(
        terminal_status="green",
        reason_code="requested-default-preprocess-different",
        canonical_json=lambda: '{"supply": 1}',
    )
    meaning_stub = SimpleNamespace(
        terminal_status="green",
        reason_code="declared-compile-time-branch-selection-observed",
        canonical_json=lambda: '{"meaning": 1}',
    )

    def capture(source_root, *, configure_args):
        assert source_root == "/fixture"
        assert "-DCCBENCH_TRACE=1" in configure_args
        return captured

    def declare(request):
        result = real(request)
        calls.append((request, result))
        return result

    def evaluate_supply(*args, **kwargs):
        assert args[0] is captured
        assert isinstance(kwargs["request"], gate.DefineRequest)
        assert kwargs["request"].macro == macro
        supply_requests.append(kwargs["request"])
        return supply_stub

    def evaluate_meaning(*args, **kwargs):
        assert args[0] is captured
        assert len(calls) == 1, "factory was not called before meaning evaluation"
        assert kwargs["request"] is calls[0][0]
        assert kwargs["request"] is supply_requests[0]
        assert kwargs["declaration"] is calls[0][1]
        return meaning_stub

    def require_family(*args, **kwargs):
        assert args == ([supply_stub], [meaning_stub])
        assert kwargs["use_class"] == "raw-measurement"
        return SimpleNamespace(
            admitted=admitted, canonical_json=lambda: '{"admission": 1}',
        )

    monkeypatch.setattr(gate, "capture_define_inputs", capture)
    monkeypatch.setattr(gate, "declare_define_runtime_meaning", declare)
    monkeypatch.setattr(gate, "evaluate_define_supply_effectuation", evaluate_supply)
    monkeypatch.setattr(gate, "evaluate_define_runtime_meaning", evaluate_meaning)
    monkeypatch.setattr(gate, "require_condition_gate_family", require_family)

    if admitted:
        assert s2._require_condition_gate("/fixture", macro) == {
            "supply": {"supply": 1},
            "meaning": {"meaning": 1},
            "admission": {"admission": 1},
        }
    else:
        with pytest.raises(RuntimeError, match=macro) as raised:
            s2._require_condition_gate("/fixture", macro)
        assert supply_stub.reason_code in str(raised.value)
        assert meaning_stub.reason_code in str(raised.value)

    assert len(calls) == 1
    request, declaration = calls[0]
    assert type(declaration) is gate.ConditionalBranchMeaningDeclaration
    assert declaration.macro == macro
    assert declaration.source_rel == "cc/silo/transaction.cc"
    assert declaration.start_directive == f"#if {macro}"
    assert request.requested_value == 1
    assert request.default_value == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
