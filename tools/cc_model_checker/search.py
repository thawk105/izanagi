"""Breadth-first exploration of immutable, hashable model states."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import isfinite
from time import monotonic
from typing import Callable, Generic, Hashable, Iterable, Literal, Mapping, Sequence, TypeVar

S = TypeVar("S", bound=Hashable)
E = TypeVar("E")
R = TypeVar("R")


@dataclass(frozen=True)
class Judgment(Generic[S, E, R]):
    id: str
    applies: Callable[[S, S, E], bool]
    check: Callable[[S, S, E], R | None]


@dataclass(frozen=True)
class Violation(Generic[E, R]):
    judgment_id: str
    reason: R
    steps: tuple[E, ...]


@dataclass(frozen=True)
class SearchStats:
    visited: int
    transitions_checked: int
    terminal: int
    elapsed_seconds: float
    complete: bool
    stop_reason: Literal["exhausted", "max_states", "max_seconds"]


@dataclass(frozen=True)
class SearchResult(Generic[E, R]):
    statistics: SearchStats
    first_by_judgment: Mapping[str, Violation[E, R] | None]
    first_violation: Violation[E, R] | None
    witness_steps: tuple[E, ...] | None


class ModelInvariantError(RuntimeError):
    """A model invariant failed; the original exception is in __cause__."""

    def __init__(self, invariant_id: str, before: object, after: object,
                 step: object, partial_steps: tuple[object, ...]):
        self.invariant_id = invariant_id
        self.before = before
        self.after = after
        self.step = step
        self.partial_steps = partial_steps
        super().__init__(f"{invariant_id} failed after {len(partial_steps)} steps")


def explore(
    initial: S,
    transitions: Callable[[S], Iterable[tuple[S, E]]],
    judgments: Sequence[Judgment[S, E, R]],
    *,
    state_invariant: Callable[[S], None] | None = None,
    transition_invariant: Callable[[S, S, E], None] | None = None,
    witness: Callable[[S, S, E, Callable[[], tuple[E, ...]]], bool] | None = None,
    max_states: int | None = None,
    max_seconds: float | None = None,
) -> SearchResult[E, R]:
    """Explore every edge in BFS order.

    Adapter states must be immutable. Equality and hash must include every
    fact affecting future transitions and all judgments. Transition order is
    supplied by the adapter and resolves equal-length witness ties.
    """
    if max_states is not None and (type(max_states) is not int or max_states < 1):
        raise ValueError("max_states must be a positive integer")
    if max_seconds is not None and (type(max_seconds) not in (int, float) or max_seconds < 0):
        raise ValueError("max_seconds must be nonnegative")
    if type(max_seconds) is float and not isfinite(max_seconds):
        raise ValueError("max_seconds must be finite")
    ids = [item.id for item in judgments]
    if len(ids) != len(set(ids)):
        raise ValueError("judgment IDs must be unique")
    began = monotonic()
    queue = deque([initial])
    parent: dict[S, tuple[S, E] | None] = {initial: None}
    first: dict[str, Violation[E, R] | None] = {item.id: None for item in judgments}
    first_violation = None
    witness_steps = None
    checked = terminal = 0

    def path(state: S) -> tuple[E, ...]:
        steps = []
        while parent[state] is not None:
            previous, step = parent[state]
            steps.append(step)
            state = previous
        return tuple(reversed(steps))

    def check_state(state: S, before: S | None, step: E | None, steps: tuple[E, ...]) -> None:
        if state_invariant is not None:
            try:
                state_invariant(state)
            except Exception as exc:
                raise ModelInvariantError("state", before, state, step, steps) from exc

    check_state(initial, None, None, ())
    stop_reason: Literal["exhausted", "max_states", "max_seconds"] = "exhausted"
    # A deque keeps the first recorded violation at minimum transition depth.
    while queue:
        if max_seconds is not None and monotonic() - began >= max_seconds:
            stop_reason = "max_seconds"
            break
        if max_states is not None and len(parent) >= max_states:
            stop_reason = "max_states"
            break
        state = queue.popleft()
        had_edge = False
        for next_state, step in transitions(state):
            had_edge = True
            checked += 1
            steps = path(state) + (step,)
            if transition_invariant is not None:
                try:
                    transition_invariant(state, next_state, step)
                except Exception as exc:
                    raise ModelInvariantError("transition", state, next_state, step, steps) from exc
            if next_state not in parent:
                check_state(next_state, state, step, steps)
            for item in judgments:
                if item.applies(state, next_state, step):
                    reason = item.check(state, next_state, step)
                    if reason is not None and first[item.id] is None:
                        violation = Violation(item.id, reason, steps)
                        first[item.id] = violation
                        if first_violation is None:
                            first_violation = violation
            if witness is not None and witness_steps is None:
                if witness(state, next_state, step, lambda: steps):
                    witness_steps = steps
            if next_state not in parent:
                parent[next_state] = (state, step)
                queue.append(next_state)
        if not had_edge:
            terminal += 1
    return SearchResult(SearchStats(len(parent), checked, terminal,
                                    monotonic() - began, stop_reason == "exhausted",
                                    stop_reason), first, first_violation, witness_steps)
