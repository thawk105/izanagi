# -*- coding: utf-8 -*-
"""s5 permutation coverage の独立 oracle 突合せテスト。"""
from __future__ import annotations

import pytest

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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
