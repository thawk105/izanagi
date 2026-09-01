# -*- coding: utf-8 -*-
"""Closed authority for exact sort candidate name/comparator bindings."""
from __future__ import annotations

from typing import Iterable, Tuple

from . import s6_sort_sweep

__all__ = [
    "SortComparatorAuthorityError",
    "require_sort_name_comparator_binding",
]

_REJECTION_MESSAGE = "invalid sort name/comparator binding"


class SortComparatorAuthorityError(ValueError):
    """Uniform rejection for values outside the closed sort authority."""


def _reject() -> None:
    raise SortComparatorAuthorityError(_REJECTION_MESSAGE) from None


def _build_sort_name_comparator_index(
        candidates: Iterable[Tuple[str, str, str]]) -> dict[str, str]:
    """Build an exact binding index, rejecting either kind of ambiguity."""
    index: dict[str, str] = {}
    implementation_names: dict[str, str] = {}
    for candidate in candidates:
        try:
            name, _category, implementation = candidate
        except (TypeError, ValueError) as exc:
            raise RuntimeError("malformed sort candidate record") from exc
        if type(name) is not str:
            raise RuntimeError(
                "sort candidate name is not str: "
                f"type={type(name).__name__}")
        if type(implementation) is not str:
            raise RuntimeError(
                "sort candidate implementation is not str: "
                f"type={type(implementation).__name__}")
        if name in index:
            raise RuntimeError(f"duplicate sort candidate name: {name!r}")
        if implementation in implementation_names:
            raise RuntimeError(
                "duplicate sort candidate implementation: "
                f"names={(implementation_names[implementation], name)!r}")
        index[name] = implementation
        implementation_names[implementation] = name
    return index


_SORT_NAME_COMPARATOR_INDEX = _build_sort_name_comparator_index(
    s6_sort_sweep.CANDIDATES
)


def require_sort_name_comparator_binding(
        name: object, comparator: object) -> None:
    """Require one exact candidate name/comparator byte-for-byte binding."""
    if type(name) is not str or type(comparator) is not str:
        _reject()
    if _SORT_NAME_COMPARATOR_INDEX.get(name) != comparator:
        _reject()
