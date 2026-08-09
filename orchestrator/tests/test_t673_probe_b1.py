# -*- coding: utf-8 -*-
"""T-673 B1: stdlib 生成器による bounded な遷移量化 probe。"""
from __future__ import annotations

import hashlib
from types import MappingProxyType

import pytest

from test_env_contract_activation import _chain, _validate, activation


ENV_COUNTS = (2, 4, 8, 16, 32, 64)


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


@pytest.mark.parametrize(
    "env_count",
    ENV_COUNTS,
    ids=["M2", "M4", "M8", "M16", "M32", "M64"],
)
def test_generation_quantifier_rejects_tail_downgrade(env_count: int):
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


@pytest.mark.parametrize(
    "env_count",
    ENV_COUNTS,
    ids=["M2", "M4", "M8", "M16", "M32", "M64"],
)
def test_successor_quantifier_rejects_tail_false(env_count: int):
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


@pytest.mark.parametrize(
    "bad_index",
    (0, 4, 7),
    ids=["first", "middle", "last"],
)
def test_generation_quantifier_rejects_downgrade_at_varied_position(
    bad_index: int,
):
    catalog = _catalog(8)
    predecessor = [1] * 8
    successor = [2] * 8
    predecessor[bad_index] = 2
    successor[bad_index] = 1
    records, head = _chain(
        tuple(predecessor),
        tuple(successor),
        registered_contracts=catalog,
    )
    bad_env = f"env-{bad_index:03d}"

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


@pytest.mark.parametrize(
    "bad_index",
    (0, 4, 7),
    ids=["first", "middle", "last"],
)
def test_successor_quantifier_rejects_false_at_varied_position(
    bad_index: int,
):
    catalog = _catalog(8)
    records, head = _chain(
        (1, 1, 1, 1, 1, 1, 1, 1),
        (2, 2, 2, 2, 2, 2, 2, 2),
        registered_contracts=catalog,
    )
    bad_env = f"env-{bad_index:03d}"

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
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
