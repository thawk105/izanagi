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


def test_condition_gate_rejection_stops_s5_before_build(monkeypatch):
    gate = coverage.condition_meaning_gate
    red = SimpleNamespace(
        terminal_status="red", reason_code="preprocess-bytes-identical",
    )
    unknown = SimpleNamespace(
        terminal_status="unestablished", reason_code="meaning-witness-undeclared",
    )
    monkeypatch.setattr(gate, "capture_define_inputs", lambda *_a, **_k: object())
    monkeypatch.setattr(gate, "make_define_request", lambda **_k: object())
    monkeypatch.setattr(
        gate, "evaluate_define_supply_effectuation", lambda *_a, **_k: red,
    )
    monkeypatch.setattr(
        gate, "evaluate_define_runtime_meaning", lambda *_a, **_k: unknown,
    )
    monkeypatch.setattr(
        gate, "require_condition_gate_family",
        lambda *_a, **_k: SimpleNamespace(admitted=False),
    )

    with pytest.raises(RuntimeError, match="preprocess-bytes-identical"):
        coverage._require_condition_gate("/fixture", coverage.ERASE_DEFINE)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
