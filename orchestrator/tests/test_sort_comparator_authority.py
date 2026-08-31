# -*- coding: utf-8 -*-
"""Tests for the closed sort name/comparator authority."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign import s6_sort_sweep
from orchestrator.campaign import sort_comparator_authority as authority


def test_all_fifteen_candidates_bind():
    assert len(s6_sort_sweep.CANDIDATES) == 15
    for name, _category, implementation in s6_sort_sweep.CANDIDATES:
        authority.require_sort_name_comparator_binding(name, implementation)


def test_duplicate_name_is_fail_closed():
    first = s6_sort_sweep.CANDIDATES[0]
    second = s6_sort_sweep.CANDIDATES[1]
    candidates = (*s6_sort_sweep.CANDIDATES, (first[0], second[1], first[2] + "\n"))
    with pytest.raises(RuntimeError, match="duplicate sort candidate name"):
        authority._build_sort_name_comparator_index(candidates)


def test_duplicate_implementation_is_fail_closed():
    first = s6_sort_sweep.CANDIDATES[0]
    second = s6_sort_sweep.CANDIDATES[1]
    candidates = (*s6_sort_sweep.CANDIDATES, (second[0] + "_copy", second[1], first[2]))
    with pytest.raises(RuntimeError, match="duplicate sort candidate implementation"):
        authority._build_sort_name_comparator_index(candidates)


def test_binding_rejects_outer_whitespace():
    name, _category, implementation = s6_sort_sweep.CANDIDATES[0]
    with pytest.raises(authority.SortComparatorAuthorityError):
        authority.require_sort_name_comparator_binding(name, implementation + "\n")


def test_binding_rejects_canonical_name_comparator_mismatch():
    first = s6_sort_sweep.CANDIDATES[0]
    second = s6_sort_sweep.CANDIDATES[1]
    with pytest.raises(authority.SortComparatorAuthorityError):
        authority.require_sort_name_comparator_binding(first[0], second[2])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
