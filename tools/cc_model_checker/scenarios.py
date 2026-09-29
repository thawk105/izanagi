"""Deterministic L3 operation descriptors, without timestamp assignments."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterator, Literal

KEYS = ("A", "B")


@dataclass(frozen=True)
class Operation:
    kind: Literal["R", "W"]
    key: Literal["A", "B"]


@dataclass(frozen=True)
class ScenarioDescriptor:
    id: str
    txn_ops: tuple[tuple[Operation, ...], ...]
    initial_versions: tuple[int, int]


def iter_l3(transactions: int) -> Iterator[ScenarioDescriptor]:
    """Enumerate operation lists and initial-version counts, not executions."""
    if type(transactions) is not int or transactions not in (2, 3):
        raise ValueError("transactions must be 2 or 3")
    alphabet = tuple(Operation(kind, key) for kind in ("R", "W") for key in KEYS)
    operations = tuple((op,) for op in alphabet) + tuple(product(alphabet, repeat=2))
    for txn_ops in product(operations, repeat=transactions):
        for initial_versions in product((1, 2), repeat=2):
            parts = [f"l3-v1-n{transactions}", f"i{initial_versions[0]}{initial_versions[1]}"]
            parts.extend(f"t{index}" + "".join(op.kind + op.key for op in ops)
                         for index, ops in enumerate(txn_ops))
            yield ScenarioDescriptor("-".join(parts), txn_ops, initial_versions)
