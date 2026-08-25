"""Shared, stdlib-only NQSV qstat state parsing.

The target-bound parser is deliberately stricter than a monitoring parser.  It
only returns a state when one request ID and one mutually consistent set of
state fields can be bound to the requested scheduler object.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


QSTAT_REQUEST_ID_RE = re.compile(
    r"(?im)^\s*Request\s+ID\s*[:=]\s*(\S+)\s*$"
)
GATE_STATE_FIELD_RE = re.compile(
    r"(?im)^(\s*)(Request\s+State|Current\s+State|State)"
    r"\s*=\s*([^\r\n]+?)\s*$"
)


@dataclass(frozen=True)
class TargetBoundQstatState:
    """Canonical state plus a stable parse signature for fail-closed callers."""

    state: Optional[str]
    reason: str


def _normalize_request_id(value: str) -> str:
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        raise ValueError("empty request ID")
    return normalized


def gate_state_value(field: str, value: str) -> Optional[str]:
    """Normalize only the field-specific vocabulary accepted by NQSV gates."""

    key = " ".join(field.casefold().split())
    if key in {"request state", "state"}:
        abbreviated = value.strip().upper()
        if abbreviated in {"QUE", "RUN", "HLD"}:
            return abbreviated
        if abbreviated == "STG":
            return "QUE"
        if abbreviated == "EXT":
            return "END"
        return None
    if key != "current state":
        return None
    full = value.strip().casefold()
    if full in {"running", "pre-running", "run"}:
        return "RUN"
    if full in {"queued", "queue", "waiting", "wait", "staging", "stg"}:
        return "QUE"
    if full in {"held", "hold", "holding"}:
        return "HLD"
    if full in {
        "completed", "complete", "finished", "ended", "exited", "exit",
        "terminated", "exiting", "post-running", "ext",
    }:
        return "END"
    return None


def target_bound_qstat_state_result(
    stdout: str,
    request_id: str,
) -> TargetBoundQstatState:
    """Parse one uniquely target-bound state without widening legacy inputs."""

    try:
        expected = _normalize_request_id(request_id)
    except ValueError:
        return TargetBoundQstatState(None, "invalid-target-request-id")
    id_matches = list(QSTAT_REQUEST_ID_RE.finditer(stdout))
    if len(id_matches) != 1:
        return TargetBoundQstatState(None, "request-id-count")
    try:
        observed = _normalize_request_id(id_matches[0].group(1))
    except ValueError:
        return TargetBoundQstatState(None, "invalid-observed-request-id")
    if observed != expected:
        return TargetBoundQstatState(None, "request-id-mismatch")

    request_match = id_matches[0]
    for state_match in GATE_STATE_FIELD_RE.finditer(
        stdout[:request_match.start()],
    ):
        leading, field, value = state_match.groups()
        line_leading = leading.rsplit("\n", 1)[-1].rsplit("\r", 1)[-1]
        if any(character not in " \t" for character in line_leading):
            return TargetBoundQstatState(None, "noncanonical-state-whitespace")
        key = " ".join(field.casefold().split())
        if gate_state_value(key, value) is not None:
            return TargetBoundQstatState(None, "state-before-target-request-id")

    fields: dict[str, list[str]] = {}
    for state_match in GATE_STATE_FIELD_RE.finditer(
        stdout[request_match.end():],
    ):
        leading, field, value = state_match.groups()
        line_leading = leading.rsplit("\n", 1)[-1].rsplit("\r", 1)[-1]
        if any(character not in " \t" for character in line_leading):
            return TargetBoundQstatState(None, "noncanonical-state-whitespace")
        key = " ".join(field.casefold().split())
        fields.setdefault(key, []).append(value)
    if not fields:
        return TargetBoundQstatState(None, "state-field-missing")
    if any(len(values) != 1 for values in fields.values()):
        return TargetBoundQstatState(None, "state-field-duplicated")

    states = {
        gate_state_value(field, values[0])
        for field, values in fields.items()
    }
    if None in states:
        return TargetBoundQstatState(None, "state-vocabulary-unknown")
    if len(states) != 1:
        return TargetBoundQstatState(None, "state-fields-conflict")
    return TargetBoundQstatState(states.pop(), "ok")


def target_bound_qstat_state(stdout: str, request_id: str) -> Optional[str]:
    """Return the canonical target-bound state, or ``None`` on ambiguity."""

    return target_bound_qstat_state_result(stdout, request_id).state
