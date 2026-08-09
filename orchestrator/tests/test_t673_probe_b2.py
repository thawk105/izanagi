# -*- coding: utf-8 -*-
"""T-673 B2: Hypothesis による bounded な遷移量化 property。

Hypothesis 未導入環境では collection 時の ImportError をそのまま失敗にする。
skip や pytest.importorskip への縮退は行わない。
"""
from __future__ import annotations

import hashlib
from types import MappingProxyType

import hypothesis
import pytest
from hypothesis import example, given, settings, strategies as st

from test_env_contract_activation import _chain, _validate, activation


_VERSION_REPORTED = False


def _record_hypothesis_version() -> None:
    global _VERSION_REPORTED
    if not _VERSION_REPORTED:
        print(f"T-673 B2 hypothesis-version={hypothesis.__version__}")
        _VERSION_REPORTED = True


def _catalog(env_count: int) -> MappingProxyType:
    return MappingProxyType({
        env_tag: tuple(
            (
                generation,
                hashlib.sha256(
                    f"{env_tag}:g{generation}".encode("ascii")
                ).hexdigest(),
            )
            for generation in (1, 2)
        )
        for env_tag in (f"env-{index:03d}" for index in range(env_count))
    })


@settings(
    max_examples=64,
    derandomize=True,
    database=None,
    deadline=None,
)
@example(env_count=64)
@given(env_count=st.integers(min_value=2, max_value=64))
def test_generation_quantifier_property_rejects_tail_downgrade(
    env_count: int,
):
    _record_hypothesis_version()
    catalog = _catalog(env_count)
    predecessor = (1,) * (env_count - 1) + (2,)
    successor = (2,) * (env_count - 1) + (1,)
    records, head = _chain(
        predecessor,
        successor,
        registered_contracts=catalog,
    )
    bad_env = f"env-{env_count - 1:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"exactly \+1.*{bad_env}.*g2 -> g1",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, _new: True,
        )


@settings(
    max_examples=64,
    derandomize=True,
    database=None,
    deadline=None,
)
@example(env_count=64)
@given(env_count=st.integers(min_value=2, max_value=64))
def test_successor_quantifier_property_rejects_tail_false(
    env_count: int,
):
    _record_hypothesis_version()
    catalog = _catalog(env_count)
    records, head = _chain(
        (1,) * env_count,
        (2,) * env_count,
        registered_contracts=catalog,
    )
    bad_env = f"env-{env_count - 1:03d}"

    with pytest.raises(
        activation.ActivationRecordError,
        match=rf"successor でない.*env_tag={bad_env}",
    ):
        _validate(
            records,
            head,
            registered_contracts=catalog,
            predicate=lambda _old, new: new.env_tag != bad_env,
        )


def _run() -> int:
    return pytest.main([__file__, "-q", "-s"])


if __name__ == "__main__":
    raise SystemExit(_run())
