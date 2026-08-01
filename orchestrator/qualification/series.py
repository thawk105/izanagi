# -*- coding: utf-8 -*-
"""Single-controller T-126 series FSM with a qualification-only hash ledger."""
from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .artifacts import (
    QualificationArtifactError,
    QualificationWriteCapability,
    append_jsonl,
    validate_json_schema,
)
from .contract import (
    balanced_order,
    canonical_json_bytes,
    observe_relative,
    sprt_decide,
    verify_recorded_decision,
)


_ZERO_HASH = "0" * 64
_EVENT_KEYS = {
    "schema_version", "qualification_lineage", "event_index",
    "previous_event_sha256", "identity", "event_type", "round_index",
    "wall_time_ns", "monotonic_ns", "payload", "event_sha256",
}
_IDENTITY_KEYS = {
    "qualification_series_id", "qualification_attempt_id", "pbs_job_id",
    "host", "boot_id", "controller_pid",
}
_EVENT_TYPES = {
    "series_open", "round_open", "member_terminal", "round_terminal",
    "wait_satisfied", "series_terminal", "series_rejected",
}


class SeriesStateError(QualificationArtifactError):
    """Ledger hash, identity, or transition is invalid."""


def _exact(value: object, keys: set[str], label: str) -> Mapping[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise SeriesStateError(f"{label} key set mismatch")
    return value


def _hash_event(event_without_hash: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(dict(event_without_hash))).hexdigest()


@dataclass(frozen=True)
class ReplayResult:
    state: str
    round_index: int
    bits: tuple[int, ...]
    terminal: str | None
    observations_recorded: int
    last_event_sha256: str


def replay_ledger(
        events: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any]) -> ReplayResult:
    """Replay every event and reject duplicate, missing, mixed, or suffix states."""
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise SeriesStateError("ledger events must be a sequence")
    if not events:
        return ReplayResult("new", 0, (), None, 0, _ZERO_HASH)
    identity = None
    previous = _ZERO_HASH
    prior_monotonic = -1
    state = "new"
    round_index = 0
    order: tuple[str, str] | None = None
    member_roles: list[str] = []
    member_medians: dict[str, float] = {}
    bits: list[int] = []
    terminal: str | None = None
    observations = 0

    for expected_index, original in enumerate(events):
        event = _exact(original, _EVENT_KEYS, "series event")
        if (event["schema_version"] != "t126-qualification-event/v1"
                or event["qualification_lineage"] != "t126-only"
                or event["event_index"] != expected_index
                or event["previous_event_sha256"] != previous
                or event["event_type"] not in _EVENT_TYPES
                or type(event["wall_time_ns"]) is not int or event["wall_time_ns"] < 0
                or type(event["monotonic_ns"]) is not int
                or event["monotonic_ns"] < prior_monotonic
                or type(event["payload"]) is not dict):
            raise SeriesStateError(f"series event envelope mismatch at index {expected_index}")
        ident = _exact(event["identity"], _IDENTITY_KEYS, "series event identity")
        if (type(ident["controller_pid"]) is not int or ident["controller_pid"] <= 0
                or any(type(ident[key]) is not str or not ident[key]
                       for key in _IDENTITY_KEYS - {"controller_pid"})):
            raise SeriesStateError("series event identity value mismatch")
        if identity is None:
            identity = dict(ident)
        elif dict(ident) != identity:
            raise SeriesStateError("mixed series/attempt/job/host/boot/PID identity")
        unhashed = {key: value for key, value in event.items() if key != "event_sha256"}
        computed = _hash_event(unhashed)
        if event["event_sha256"] != computed:
            raise SeriesStateError("series event hash mismatch")
        previous = computed
        prior_monotonic = event["monotonic_ns"]
        kind = event["event_type"]
        payload = event["payload"]

        if state in ("terminal", "rejected"):
            raise SeriesStateError("event suffix after terminal state")

        if kind == "series_open":
            if state != "new" or event["round_index"] is not None or payload != {
                    "allow_resume": False, "statistical_claim": "none"}:
                raise SeriesStateError("invalid series_open transition")
            state = "series_open"
            continue

        if kind == "series_rejected":
            if state == "new" or event["round_index"] not in (None, round_index):
                raise SeriesStateError("invalid series_rejected transition")
            _exact(payload, {
                "reason", "evidence_canonical_json", "evidence_sha256",
            }, "series_rejected payload")
            if (type(payload["reason"]) is not str or not payload["reason"]
                    or type(payload["evidence_canonical_json"]) is not str
                    or type(payload["evidence_sha256"]) is not str
                    or hashlib.sha256(
                        payload["evidence_canonical_json"].encode("ascii")
                    ).hexdigest() != payload["evidence_sha256"]):
                raise SeriesStateError("series rejection reason is invalid")
            state = "rejected"
            terminal = "rejected"
            continue

        if kind == "round_open":
            if state not in ("series_open", "wait_satisfied"):
                raise SeriesStateError("round_open out of order")
            if type(event["round_index"]) is not int or event["round_index"] != round_index + 1:
                raise SeriesStateError("round index is not contiguous")
            expected_order = balanced_order(protocol["order"]["seed"], event["round_index"])
            if payload != {"member_order": list(expected_order)}:
                raise SeriesStateError("round member order is not frozen alternation")
            round_index = event["round_index"]
            order = expected_order
            member_roles = []
            member_medians = {}
            state = "round_open"
            continue

        if kind == "member_terminal":
            if state not in ("round_open", "member_one") or event["round_index"] != round_index:
                raise SeriesStateError("member_terminal out of order")
            row = _exact(payload, {
                "role", "median_tps", "evidence_ref", "execution_integrity",
            }, "member_terminal payload")
            expected_role = order[len(member_roles)] if order is not None else None
            if (row["role"] != expected_role
                    or row["execution_integrity"] != "valid"
                    or type(row["evidence_ref"]) is not dict
                    or isinstance(row["median_tps"], bool)
                    or not isinstance(row["median_tps"], (int, float))
                    or not math.isfinite(float(row["median_tps"]))
                    or row["median_tps"] <= 0):
                raise SeriesStateError("member terminal evidence/role mismatch")
            member_roles.append(row["role"])
            member_medians[row["role"]] = float(row["median_tps"])
            state = "member_one" if len(member_roles) == 1 else "member_two"
            continue

        if kind == "round_terminal":
            if state != "member_two" or event["round_index"] != round_index:
                raise SeriesStateError("round_terminal requires exactly two members")
            row = _exact(payload, {
                "subject_median_tps", "reference_median_tps", "relative",
                "direction", "bit", "bits", "sprt_terminal", "llr_hex",
            }, "round_terminal payload")
            if (row["subject_median_tps"] != member_medians.get("subject")
                    or row["reference_median_tps"] != member_medians.get("reference")):
                raise SeriesStateError("round terminal median/member evidence mismatch")
            observation = observe_relative(
                row["subject_median_tps"], row["reference_median_tps"],
                protocol["threshold"]["relative"],
            )
            if (row["relative"] != observation.relative
                    or row["direction"] != observation.direction
                    or row["bit"] != observation.bit):
                raise SeriesStateError("round observation does not recompute")
            expected_bits = bits + [observation.bit]
            if row["bits"] != expected_bits:
                raise SeriesStateError("round bit prefix mismatch")
            decision = verify_recorded_decision(
                expected_bits, protocol["sprt"],
                terminal=row["sprt_terminal"], llr_hex=row["llr_hex"],
            )
            bits[:] = expected_bits
            observations += 1
            terminal = None if decision.terminal == "continuing" else decision.terminal
            state = "round_continuing" if terminal is None else "round_terminal"
            continue

        if kind == "wait_satisfied":
            if state != "round_continuing" or event["round_index"] != round_index:
                raise SeriesStateError("wait_satisfied out of order")
            row = _exact(payload, {"elapsed_s", "required_s"}, "wait payload")
            if (row["required_s"] != protocol["timing"]["round_gap_s"]
                    or isinstance(row["elapsed_s"], bool)
                    or not isinstance(row["elapsed_s"], (int, float))
                    or not math.isfinite(float(row["elapsed_s"]))
                    or row["elapsed_s"] < row["required_s"]):
                raise SeriesStateError("round gap is shorter than frozen requirement")
            state = "wait_satisfied"
            continue

        if kind == "series_terminal":
            if state != "round_terminal" or event["round_index"] != round_index:
                raise SeriesStateError("series_terminal out of order")
            decision = sprt_decide(bits, protocol["sprt"])
            expected = {
                "terminal": decision.terminal,
                "bits": list(bits),
                "llr_hex": decision.llr_hex,
                "execution_integrity": "valid",
                "expectation_match": "not-applicable-observational-smoke",
            }
            if payload != expected:
                raise SeriesStateError("series terminal payload mismatch")
            state = "terminal"
            terminal = decision.terminal
            continue

        raise SeriesStateError(f"unhandled event type: {kind}")

    return ReplayResult(state, round_index, tuple(bits), terminal, observations, previous)


class SeriesFSM:
    """Only this controller appends the series ledger."""

    def __init__(
            self, capability: QualificationWriteCapability, relative_path: str,
            identity: Mapping[str, Any], protocol: Mapping[str, Any], *,
            wall_clock_ns: Callable[[], int] = time.time_ns,
            monotonic_ns: Callable[[], int] = time.monotonic_ns):
        self._capability = capability
        self._relative_path = relative_path
        self._identity = dict(_exact(identity, _IDENTITY_KEYS, "series identity"))
        self._protocol = protocol
        self._wall_clock_ns = wall_clock_ns
        self._monotonic_ns = monotonic_ns
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    @property
    def replay(self) -> ReplayResult:
        return replay_ledger(self._events, self._protocol)

    def _append(
            self, event_type: str, *, round_index: int | None,
            payload: Mapping[str, Any]) -> dict[str, Any]:
        event = {
            "schema_version": "t126-qualification-event/v1",
            "qualification_lineage": "t126-only",
            "event_index": len(self._events),
            "previous_event_sha256": (
                self._events[-1]["event_sha256"] if self._events else _ZERO_HASH
            ),
            "identity": dict(self._identity),
            "event_type": event_type,
            "round_index": round_index,
            "wall_time_ns": self._wall_clock_ns(),
            "monotonic_ns": self._monotonic_ns(),
            "payload": dict(payload),
        }
        event["event_sha256"] = _hash_event(event)
        trial = [*self._events, event]
        replay_ledger(trial, self._protocol)
        validate_json_schema("t126_event_schema.json", event)
        append_jsonl(self._capability, self._relative_path, event)
        self._events.append(event)
        return dict(event)

    def open(self) -> None:
        self._append(
            "series_open", round_index=None,
            payload={"allow_resume": False, "statistical_claim": "none"},
        )

    def open_round(self, round_index: int) -> tuple[str, str]:
        order = balanced_order(self._protocol["order"]["seed"], round_index)
        self._append(
            "round_open", round_index=round_index,
            payload={"member_order": list(order)},
        )
        return order

    def member_terminal(
            self, round_index: int, role: str, median_tps: float,
            evidence_ref: Mapping[str, Any]) -> None:
        self._append(
            "member_terminal", round_index=round_index,
            payload={
                "role": role,
                "median_tps": median_tps,
                "evidence_ref": dict(evidence_ref),
                "execution_integrity": "valid",
            },
        )

    def round_terminal(
            self, round_index: int, *, subject_median_tps: float,
            reference_median_tps: float) -> str:
        observation = observe_relative(
            subject_median_tps, reference_median_tps,
            self._protocol["threshold"]["relative"],
        )
        bits = [*self.replay.bits, observation.bit]
        decision = sprt_decide(bits, self._protocol["sprt"])
        self._append(
            "round_terminal", round_index=round_index,
            payload={
                "subject_median_tps": subject_median_tps,
                "reference_median_tps": reference_median_tps,
                "relative": observation.relative,
                "direction": observation.direction,
                "bit": observation.bit,
                "bits": bits,
                "sprt_terminal": decision.terminal,
                "llr_hex": decision.llr_hex,
            },
        )
        return decision.terminal

    def wait_satisfied(self, round_index: int, elapsed_s: float) -> None:
        self._append(
            "wait_satisfied", round_index=round_index,
            payload={
                "elapsed_s": elapsed_s,
                "required_s": self._protocol["timing"]["round_gap_s"],
            },
        )

    def terminal(self, round_index: int) -> None:
        replay = self.replay
        decision = sprt_decide(replay.bits, self._protocol["sprt"])
        self._append(
            "series_terminal", round_index=round_index,
            payload={
                "terminal": decision.terminal,
                "bits": list(replay.bits),
                "llr_hex": decision.llr_hex,
                "execution_integrity": "valid",
                "expectation_match": "not-applicable-observational-smoke",
            },
        )

    def reject(
            self, reason: str, evidence: Mapping[str, Any],
            *, round_index: int | None = None) -> None:
        evidence_json = canonical_json_bytes(dict(evidence)).decode("ascii")
        self._append(
            "series_rejected", round_index=round_index,
            payload={
                "reason": reason,
                "evidence_canonical_json": evidence_json,
                "evidence_sha256": hashlib.sha256(
                    evidence_json.encode("ascii")).hexdigest(),
            },
        )
