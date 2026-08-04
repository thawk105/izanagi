# -*- coding: utf-8 -*-
"""Process-local role/session isolation checks for autonomous trials.

This leaf does not provide a cross-process boundary: the tracker state exists
only for the lifetime of one Python process.  It also does not authenticate or
otherwise verify the provider executable that produced a session identifier.
Rejecting an unreserved token (the third P5 requirement) is outside this leaf
and remains unimplemented as a separate design dependency.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoleSessionEvaluation:
    """Pure result for one complete set of role/session observations."""

    accepted: bool
    reason: str


def evaluate_role_session_isolation(observations: object) -> RoleSessionEvaluation:
    """Purely require non-empty strings and distinct session IDs."""

    if type(observations) not in {list, tuple}:
        return RoleSessionEvaluation(False, "observations must be a list or tuple")
    observed_session_ids: set[str] = set()
    for index, observation in enumerate(observations):
        if type(observation) is not tuple or len(observation) != 2:
            return RoleSessionEvaluation(
                False, f"observation {index} must be an exact pair"
            )
        role_name, session_id = observation
        if type(role_name) is not str or not role_name:
            return RoleSessionEvaluation(
                False, f"observation {index} role_name must be a non-empty str"
            )
        if type(session_id) is not str or not session_id:
            return RoleSessionEvaluation(
                False, f"observation {index} session_id must be a non-empty str"
            )
        if session_id in observed_session_ids:
            return RoleSessionEvaluation(False, "session_id must be mutually distinct")
        observed_session_ids.add(session_id)
    return RoleSessionEvaluation(True, "accepted")


class RoleSessionIsolationError(RuntimeError):
    """A fail-closed role/session observation rejection."""


class CrossRoleSessionTracker:
    """Process-local observations shared by all projected role providers."""

    def __init__(self) -> None:
        self._observations: list[tuple[str, str]] = []

    def observe(self, *, role_name: str, session_id: str) -> None:
        """Record one observation after pure validation of the complete set."""

        candidate = (*self._observations, (role_name, session_id))
        evaluation = evaluate_role_session_isolation(candidate)
        if not evaluation.accepted:
            raise RoleSessionIsolationError(evaluation.reason)
        self._observations.append((role_name, session_id))
