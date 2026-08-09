# -*- coding: utf-8 -*-
"""T-673 A-prime: 手書きの 8-env fixture だけを増量した対抗案。"""
from __future__ import annotations

from types import MappingProxyType

import pytest

from test_env_contract_activation import _chain, _validate, activation


EIGHT_ENV_CATALOG = MappingProxyType({
    "env-000": (
        (1, "0000000000000000000000000000000000000000000000000000000000000000"),
        (2, "1111111111111111111111111111111111111111111111111111111111111111"),
    ),
    "env-001": (
        (1, "2222222222222222222222222222222222222222222222222222222222222222"),
        (2, "3333333333333333333333333333333333333333333333333333333333333333"),
    ),
    "env-002": (
        (1, "4444444444444444444444444444444444444444444444444444444444444444"),
        (2, "5555555555555555555555555555555555555555555555555555555555555555"),
    ),
    "env-003": (
        (1, "6666666666666666666666666666666666666666666666666666666666666666"),
        (2, "7777777777777777777777777777777777777777777777777777777777777777"),
    ),
    "env-004": (
        (1, "8888888888888888888888888888888888888888888888888888888888888888"),
        (2, "9999999999999999999999999999999999999999999999999999999999999999"),
    ),
    "env-005": (
        (1, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
        (2, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
    ),
    "env-006": (
        (1, "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"),
        (2, "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"),
    ),
    "env-007": (
        (1, "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"),
        (2, "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),
    ),
})


def test_generation_quantifier_rejects_eighth_env_downgrade():
    records, head = _chain(
        (1, 1, 1, 1, 1, 1, 1, 2),
        (2, 2, 2, 2, 2, 2, 2, 1),
        registered_contracts=EIGHT_ENV_CATALOG,
    )
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exactly \+1.*env-007.*g2 -> g1",
    ):
        _validate(
            records,
            head,
            registered_contracts=EIGHT_ENV_CATALOG,
            predicate=lambda _old, _new: True,
        )


def test_successor_quantifier_rejects_eighth_env_false():
    records, head = _chain(
        (1, 1, 1, 1, 1, 1, 1, 1),
        (2, 2, 2, 2, 2, 2, 2, 2),
        registered_contracts=EIGHT_ENV_CATALOG,
    )
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-007",
    ):
        _validate(
            records,
            head,
            registered_contracts=EIGHT_ENV_CATALOG,
            predicate=lambda _old, new: new.env_tag != "env-007",
        )


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
