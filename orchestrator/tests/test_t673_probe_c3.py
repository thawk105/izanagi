# -*- coding: utf-8 -*-
"""T-673 C3: successor_rows の slice を runtime sentinel で拒否する。

successor_rows は引数なので量化点 G へ sentinel を注入できる。一方 changed は
関数内で構築される list であり、この probe は量化点 P を閉じない。
"""
from __future__ import annotations

import pytest

from test_env_contract_activation import activation


class _SliceAccessError(AssertionError):
    pass


class _SliceForbiddenTuple(tuple):
    def __getitem__(self, index):
        if isinstance(index, slice):
            raise _SliceAccessError("successor_rows was sliced")
        return super().__getitem__(index)


def _transition_rows():
    predecessor_rows = (
        activation.ActiveContract("env-a", 1, "1" * 64),
        activation.ActiveContract("env-b", 1, "3" * 64),
    )
    successor_rows = _SliceForbiddenTuple((
        activation.ActiveContract("env-a", 2, "2" * 64),
        activation.ActiveContract("env-b", 2, "4" * 64),
    ))
    return predecessor_rows, successor_rows


def test_successor_rows_sentinel_rejects_slice_access():
    _predecessor_rows, successor_rows = _transition_rows()
    with pytest.raises(_SliceAccessError, match="successor_rows was sliced"):
        successor_rows[:1]


def test_transition_gate_iterates_successor_rows_without_slicing():
    predecessor_rows, successor_rows = _transition_rows()
    result = activation._validate_activation_transition(
        predecessor_rows,
        successor_rows,
        activation_serial=2,
        is_valid_registered_successor=lambda _old, _new: True,
    )
    assert result is None


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
