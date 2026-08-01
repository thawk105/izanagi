# -*- coding: utf-8 -*-
"""Create-only, series-global submission and attempt ledger for T-126."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .artifacts import (
    PERMANENT_NONRETRY_FAILURES,
    QualificationArtifactError,
    QualificationWriteCapability,
    create_json,
    load_json_strict,
)
from .contract import canonical_json_bytes
from .retry_index import RetryIndexError, validate_retry_index


_HEX64 = re.compile(r"[0-9a-f]{64}")
_NONCE = re.compile(r"[0-9a-f]{32}")
_ZERO = "0" * 64
_EVENT_KEYS = {
    "schema_version", "qualification_lineage", "event_index",
    "previous_event_sha256", "qualification_series_id", "event_type",
    "payload", "event_sha256",
}
_EVENT_TYPES = {
    "initial_intent", "initial_submitted", "attempt_outcome",
    "attempt_outcome_pending", "retry_intent", "retry_submitted",
}


class AttemptLedgerError(QualificationArtifactError):
    """Series-global attempt history is missing, partial, or contradictory."""


@dataclass(frozen=True)
class AttemptLedgerState:
    state: str
    attempt_count: int
    last_attempt_id: str | None
    last_retry_index: int | None
    observations_recorded: int | None
    terminal: str | None
    failure_class: str | None
    last_nonce: str | None
    last_job_id: str | None
    last_submission_intent_sha256: str | None
    last_qsub_invocation_sha256: str | None
    last_submission_evidence_sha256: str | None
    last_event_sha256: str


def _hash_event(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(dict(value))).hexdigest()


def _exact(value: object, keys: set[str], label: str) -> Mapping[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise AttemptLedgerError(f"{label} key set mismatch")
    return value


def _valid_id(value: object, label: str) -> str:
    if type(value) is not str or _HEX64.fullmatch(value) is None:
        raise AttemptLedgerError(f"{label} must be full lowercase sha256")
    return value


def _validate_intent(payload: object, retry_index: int) -> Mapping[str, Any]:
    try:
        validate_retry_index(retry_index)
    except RetryIndexError as exc:
        raise AttemptLedgerError(
            "attempt intent expected index is invalid") from exc
    keys = {"nonce", "retry_index", "submission_intent_sha256"}
    if retry_index == 1:
        keys |= {"retry_from_attempt_id", "retry_from_receipt_sha256"}
    row = _exact(payload, keys, "attempt intent payload")
    try:
        payload_retry_index = validate_retry_index(row["retry_index"])
    except RetryIndexError as exc:
        raise AttemptLedgerError("attempt intent retry index is invalid") from exc
    if (type(row["nonce"]) is not str or _NONCE.fullmatch(row["nonce"]) is None
            or payload_retry_index != retry_index):
        raise AttemptLedgerError("attempt intent nonce/index mismatch")
    _valid_id(row["submission_intent_sha256"], "submission intent hash")
    if retry_index == 1:
        _valid_id(row["retry_from_attempt_id"], "retry source attempt")
        _valid_id(row["retry_from_receipt_sha256"], "retry source receipt")
    return row


def _validate_submitted(payload: object, retry_index: int) -> Mapping[str, Any]:
    try:
        validate_retry_index(retry_index)
    except RetryIndexError as exc:
        raise AttemptLedgerError(
            "submitted expected retry index is invalid") from exc
    row = _exact(payload, {
        "nonce", "retry_index", "job_id", "qualification_attempt_id",
        "qsub_invocation_sha256", "submission_evidence_sha256",
    }, "submitted payload")
    try:
        payload_retry_index = validate_retry_index(row["retry_index"])
    except RetryIndexError as exc:
        raise AttemptLedgerError("submitted retry index is invalid") from exc
    if (type(row["nonce"]) is not str or _NONCE.fullmatch(row["nonce"]) is None
            or payload_retry_index != retry_index
            or type(row["job_id"]) is not str or not row["job_id"]
            or "\n" in row["job_id"]):
        raise AttemptLedgerError("submitted nonce/index/job mismatch")
    _valid_id(row["qualification_attempt_id"], "submitted attempt id")
    _valid_id(row["qsub_invocation_sha256"], "qsub invocation hash")
    _valid_id(row["submission_evidence_sha256"], "submission evidence hash")
    return row


def _validate_outcome(payload: object) -> Mapping[str, Any]:
    row = _exact(payload, {
        "qualification_attempt_id", "retry_index", "observations_recorded",
        "terminal", "failure_class", "receipt_sha256", "job_id", "nonce",
        "submission_intent_sha256", "qsub_invocation_sha256",
        "submission_evidence_sha256",
    }, "attempt outcome payload")
    _valid_id(row["qualification_attempt_id"], "outcome attempt id")
    _valid_id(row["receipt_sha256"], "outcome receipt hash")
    _valid_id(row["submission_intent_sha256"], "outcome intent hash")
    _valid_id(row["qsub_invocation_sha256"], "outcome invocation hash")
    _valid_id(row["submission_evidence_sha256"], "outcome submission evidence hash")
    try:
        validate_retry_index(row["retry_index"])
    except RetryIndexError as exc:
        raise AttemptLedgerError("outcome retry index is invalid") from exc
    if (type(row["observations_recorded"]) is not int
            or row["observations_recorded"] < 0
            or row["terminal"] not in (
                None, "lower_boundary", "upper_boundary", "indeterminate")
            or type(row["failure_class"]) is not str
            or not row["failure_class"]
            or type(row["nonce"]) is not str
            or _NONCE.fullmatch(row["nonce"]) is None
            or type(row["job_id"]) is not str or not row["job_id"]
            or "\n" in row["job_id"]):
        raise AttemptLedgerError("attempt outcome fields are invalid")
    if row["terminal"] is not None and row["failure_class"] != "none":
        raise AttemptLedgerError("terminal outcome cannot carry a failure class")
    if row["terminal"] is None and row["failure_class"] == "none":
        raise AttemptLedgerError("failure outcome must carry a failure class")
    return row


def _require_retry_admission(
        *, last_retry_index: int | None, observations_recorded: int | None,
        terminal: str | None, failure_class: str | None,
        eligible_reasons: Sequence[str]) -> None:
    """Single effective predicate for all observation/terminal retry gates."""
    if last_retry_index != 0:
        raise AttemptLedgerError("retry requires exactly one closed initial failure")
    if (observations_recorded != 0 or terminal is not None
            or failure_class in PERMANENT_NONRETRY_FAILURES
            or failure_class not in eligible_reasons):
        raise AttemptLedgerError(
            "retry is not an eligible pre-observation initial failure")


def replay_attempt_ledger(
        events: Sequence[Mapping[str, Any]], *, series_id: str,
        eligible_reasons: Sequence[str],
) -> AttemptLedgerState:
    """Replay the one initial + at most one retry state machine."""
    _valid_id(series_id, "series id")
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise AttemptLedgerError("attempt ledger must be a sequence")
    state = "new"
    previous = _ZERO
    nonce = None
    last_attempt_id = None
    last_retry_index = None
    observations = None
    terminal = None
    failure_class = None
    attempt_count = 0
    last_nonce = None
    last_job_id = None
    last_intent = None
    last_invocation = None
    last_evidence = None
    pending_outcome = None
    for index, original in enumerate(events):
        event = _exact(original, _EVENT_KEYS, "attempt ledger event")
        if (event["schema_version"] != "t126-series-attempt-ledger-event/v1"
                or event["qualification_lineage"] != "t126-only"
                or event["event_index"] != index
                or event["previous_event_sha256"] != previous
                or event["qualification_series_id"] != series_id
                or event["event_type"] not in _EVENT_TYPES
                or type(event["payload"]) is not dict):
            raise AttemptLedgerError(f"attempt ledger envelope mismatch at {index}")
        unhashed = {key: value for key, value in event.items()
                    if key != "event_sha256"}
        actual = _hash_event(unhashed)
        if event["event_sha256"] != actual:
            raise AttemptLedgerError("attempt ledger event hash mismatch")
        previous = actual
        kind = event["event_type"]
        payload = event["payload"]

        if state in {"terminal", "retry_failed"} and kind != "retry_intent":
            raise AttemptLedgerError("attempt ledger has a suffix after closure")
        if kind == "initial_intent":
            if state != "new":
                raise AttemptLedgerError("duplicate initial submission")
            row = _validate_intent(payload, 0)
            nonce = row["nonce"]
            last_nonce = nonce
            last_intent = row["submission_intent_sha256"]
            state = "initial_intent"
        elif kind == "initial_submitted":
            if state != "initial_intent":
                raise AttemptLedgerError("initial submission is missing its intent")
            row = _validate_submitted(payload, 0)
            if row["nonce"] != nonce:
                raise AttemptLedgerError("initial nonce changed")
            last_attempt_id = row["qualification_attempt_id"]
            last_retry_index = 0
            last_nonce = row["nonce"]
            last_job_id = row["job_id"]
            last_invocation = row["qsub_invocation_sha256"]
            last_evidence = row["submission_evidence_sha256"]
            attempt_count = 1
            state = "initial_submitted"
        elif kind == "attempt_outcome_pending":
            if state not in {"initial_submitted", "retry_submitted"}:
                raise AttemptLedgerError("outcome has no exact submitted attempt")
            row = _validate_outcome(payload)
            if (row["qualification_attempt_id"] != last_attempt_id
                    or row["retry_index"] != last_retry_index
                    or row["nonce"] != last_nonce
                    or row["job_id"] != last_job_id
                    or row["submission_intent_sha256"] != last_intent
                    or row["qsub_invocation_sha256"] != last_invocation
                    or row["submission_evidence_sha256"] != last_evidence):
                raise AttemptLedgerError("outcome submitted binding mismatch")
            pending_outcome = dict(row)
            state = "outcome_pending"
        elif kind == "attempt_outcome":
            if state != "outcome_pending":
                raise AttemptLedgerError("final outcome has no exact pending event")
            row = _validate_outcome(payload)
            if dict(row) != pending_outcome:
                raise AttemptLedgerError("final outcome differs from pending outcome")
            observations = row["observations_recorded"]
            terminal = row["terminal"]
            failure_class = row["failure_class"]
            if terminal is not None:
                state = "terminal"
            elif last_retry_index == 1:
                state = "retry_failed"
            else:
                state = "initial_failed"
        elif kind == "retry_intent":
            if state not in {"initial_failed", "terminal", "retry_failed"}:
                raise AttemptLedgerError(
                    "retry requires exactly one closed initial failure")
            row = _validate_intent(payload, 1)
            _require_retry_admission(
                last_retry_index=last_retry_index,
                observations_recorded=observations, terminal=terminal,
                failure_class=failure_class, eligible_reasons=eligible_reasons)
            if row["retry_from_attempt_id"] != last_attempt_id:
                raise AttemptLedgerError(
                    "retry source attempt does not match the closed initial")
            nonce = row["nonce"]
            last_nonce = nonce
            last_intent = row["submission_intent_sha256"]
            state = "retry_intent"
        elif kind == "retry_submitted":
            if state != "retry_intent":
                raise AttemptLedgerError("retry submission is missing its intent")
            row = _validate_submitted(payload, 1)
            if row["nonce"] != nonce:
                raise AttemptLedgerError("retry nonce changed")
            last_attempt_id = row["qualification_attempt_id"]
            last_retry_index = 1
            last_nonce = row["nonce"]
            last_job_id = row["job_id"]
            last_invocation = row["qsub_invocation_sha256"]
            last_evidence = row["submission_evidence_sha256"]
            attempt_count = 2
            observations = None
            terminal = None
            failure_class = None
            state = "retry_submitted"
        else:  # pragma: no cover - protected by _EVENT_TYPES
            raise AttemptLedgerError(f"unhandled attempt ledger event: {kind}")
    return AttemptLedgerState(
        state=state, attempt_count=attempt_count,
        last_attempt_id=last_attempt_id, last_retry_index=last_retry_index,
        observations_recorded=observations, terminal=terminal,
        failure_class=failure_class, last_nonce=last_nonce,
        last_job_id=last_job_id,
        last_submission_intent_sha256=last_intent,
        last_qsub_invocation_sha256=last_invocation,
        last_submission_evidence_sha256=last_evidence,
        last_event_sha256=previous,
    )


class SeriesAttemptLedger:
    """Create-only numbered event files for one canonical qualification series."""

    def __init__(
            self, capability: QualificationWriteCapability, series_id: str,
            eligible_reasons: Sequence[str]):
        capability.assert_intact()
        _valid_id(series_id, "series id")
        self._capability = capability
        self.series_id = series_id
        self._eligible_reasons = tuple(eligible_reasons)
        self._prefix = f"series/{series_id}/attempt-ledger"

    def load(self) -> list[dict[str, Any]]:
        directory = self._capability.root / self._prefix
        if not directory.exists():
            return []
        if directory.is_symlink() or not directory.is_dir():
            raise AttemptLedgerError("attempt ledger directory is unsafe")
        paths = sorted(directory.glob("*.json"))
        if [path.name for path in paths] != [
                f"{index:04d}.json" for index in range(len(paths))]:
            raise AttemptLedgerError("attempt ledger is missing or non-contiguous")
        return [load_json_strict(path) for path in paths]

    @property
    def replay(self) -> AttemptLedgerState:
        return replay_attempt_ledger(
            self.load(), series_id=self.series_id,
            eligible_reasons=self._eligible_reasons,
        )

    def append(
            self, event_type: str, payload: Mapping[str, Any], *,
            idempotent: bool = False) -> dict[str, Any]:
        events = self.load()
        event = {
            "schema_version": "t126-series-attempt-ledger-event/v1",
            "qualification_lineage": "t126-only",
            "event_index": len(events),
            "previous_event_sha256": (
                events[-1]["event_sha256"] if events else _ZERO),
            "qualification_series_id": self.series_id,
            "event_type": event_type,
            "payload": dict(payload),
        }
        event["event_sha256"] = _hash_event(event)
        replay_attempt_ledger(
            [*events, event], series_id=self.series_id,
            eligible_reasons=self._eligible_reasons,
        )
        relative = f"{self._prefix}/{len(events):04d}.json"
        try:
            create_json(self._capability, relative, event)
        except QualificationArtifactError:
            if not idempotent:
                raise
            existing = load_json_strict(self._capability.root / relative)
            if existing != event:
                raise AttemptLedgerError(
                    "existing attempt ledger event is not exact-idempotent")
        return event

    def claim_initial(
            self, *, nonce: str, submission_intent_sha256: str) -> dict[str, Any]:
        return self.append("initial_intent", {
            "nonce": nonce,
            "retry_index": 0,
            "submission_intent_sha256": submission_intent_sha256,
        })

    def claim_retry(
            self, *, nonce: str, submission_intent_sha256: str,
            retry_from_attempt_id: str,
            retry_from_receipt_sha256: str) -> dict[str, Any]:
        return self.append("retry_intent", {
            "nonce": nonce,
            "retry_index": 1,
            "submission_intent_sha256": submission_intent_sha256,
            "retry_from_attempt_id": retry_from_attempt_id,
            "retry_from_receipt_sha256": retry_from_receipt_sha256,
        })

    def bind_submitted(
            self, *, retry_index: int, nonce: str, job_id: str,
            attempt_id: str, qsub_invocation_sha256: str,
            submission_evidence_sha256: str) -> dict[str, Any]:
        try:
            retry_index = validate_retry_index(retry_index)
        except RetryIndexError as exc:
            raise AttemptLedgerError("submitted retry index is invalid") from exc
        kind = "initial_submitted" if retry_index == 0 else "retry_submitted"
        return self.append(kind, {
            "nonce": nonce,
            "retry_index": retry_index,
            "job_id": job_id,
            "qualification_attempt_id": attempt_id,
            "qsub_invocation_sha256": qsub_invocation_sha256,
            "submission_evidence_sha256": submission_evidence_sha256,
        }, idempotent=True)

    def record_outcome(
            self, *, attempt_id: str, retry_index: int,
            observations_recorded: int, terminal: str | None,
            failure_class: str, receipt_sha256: str) -> dict[str, Any]:
        try:
            retry_index = validate_retry_index(retry_index)
        except RetryIndexError as exc:
            raise AttemptLedgerError("outcome retry index is invalid") from exc
        state = self.replay
        payload = {
            "qualification_attempt_id": attempt_id,
            "retry_index": retry_index,
            "observations_recorded": observations_recorded,
            "terminal": terminal,
            "failure_class": failure_class,
            "receipt_sha256": receipt_sha256,
            "job_id": state.last_job_id,
            "nonce": state.last_nonce,
            "submission_intent_sha256": state.last_submission_intent_sha256,
            "qsub_invocation_sha256": state.last_qsub_invocation_sha256,
            "submission_evidence_sha256": state.last_submission_evidence_sha256,
        }
        if state.state in {"initial_submitted", "retry_submitted"}:
            self.append("attempt_outcome_pending", payload, idempotent=True)
        return self.append("attempt_outcome", payload, idempotent=True)

    def prepare_outcome(
            self, *, attempt_id: str, retry_index: int,
            observations_recorded: int, terminal: str | None,
            failure_class: str, receipt_sha256: str) -> dict[str, Any]:
        try:
            retry_index = validate_retry_index(retry_index)
        except RetryIndexError as exc:
            raise AttemptLedgerError("outcome retry index is invalid") from exc
        state = self.replay
        payload = {
            "qualification_attempt_id": attempt_id,
            "retry_index": retry_index,
            "observations_recorded": observations_recorded,
            "terminal": terminal,
            "failure_class": failure_class,
            "receipt_sha256": receipt_sha256,
            "job_id": state.last_job_id,
            "nonce": state.last_nonce,
            "submission_intent_sha256": state.last_submission_intent_sha256,
            "qsub_invocation_sha256": state.last_qsub_invocation_sha256,
            "submission_evidence_sha256": state.last_submission_evidence_sha256,
        }
        if state.state == "outcome_pending":
            events = self.load()
            if events[-1]["payload"] != payload:
                raise AttemptLedgerError("pending outcome is bound to different bytes")
            return events[-1]
        return self.append("attempt_outcome_pending", payload, idempotent=True)

    def finalize_outcome(self) -> dict[str, Any]:
        events = self.load()
        if not events or events[-1]["event_type"] != "attempt_outcome_pending":
            raise AttemptLedgerError("no pending outcome to finalize")
        return self.append(
            "attempt_outcome", events[-1]["payload"], idempotent=True)
