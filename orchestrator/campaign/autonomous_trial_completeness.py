# -*- coding: utf-8 -*-
"""Autonomous trial journal/report completeness verification.

The write-time entry point deliberately re-reads ``attempts.jsonl`` from
disk.  Role entries in the producer report are the same objects returned by
``AttemptJournal.append``; comparing two in-memory views would therefore not
independently verify their persisted contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    _ROOT_FOR_IMPORT = Path(__file__).resolve().parents[2]
    if str(_ROOT_FOR_IMPORT) not in sys.path:
        sys.path.insert(0, str(_ROOT_FOR_IMPORT))
    from orchestrator.campaign import campaign_lock
    from orchestrator.campaign import layer3_report as _layer3_report
    from orchestrator.campaign.artifact_admission import (ArtifactAdmissionError,
                                                           require_admitted_campaign)
    from orchestrator.campaign.layer3_report import canonical_record_ref
    from orchestrator.campaign.role_session_isolation import (
        evaluate_role_session_isolation,
    )
else:
    from . import campaign_lock
    from . import layer3_report as _layer3_report
    from .artifact_admission import ArtifactAdmissionError, require_admitted_campaign
    from .layer3_report import canonical_record_ref
    from .role_session_isolation import evaluate_role_session_isolation


_EVENTS = frozenset({
    "transport-admission",
    "run-start",
    "role-attempt",
    "supervisor-error",
    "supervisor-wall-budget",
    "provider-init-error",
    "run-finish",
})
_TERMINAL_EVENTS = frozenset({
    "supervisor-error", "supervisor-wall-budget", "provider-init-error",
})
_ROLE_ORDER = ("planner", "coder", "auditor", "critic")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT_ID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_ADMISSION_DECISION_KEYS = frozenset({
    "schema_version", "classification", "admission_status",
    "verification_status", "campaign_id", "campaign_path",
    "campaign_lock_sha256", "wal_sha256", "policy_sha256",
    "attempt_receipt_sha256s", "validator", "overlay",
})
_ADMISSION_VALIDATOR_KEYS = frozenset({"identity", "sha256"})
_ADMISSION_OVERLAY_KEYS = frozenset({"ledger_sha256", "record_key"})
_LAUNCH_ADMISSION_KEYS = frozenset({
    "mode", "certifying", "reason_code", "trial_id", "workloads",
    "binding", "activation_report_digest_sha256",
})
_LAUNCH_BINDING_KEYS = frozenset({
    "manifest_sha256", "prereg_commit", "measurement_head", "trial_id",
    "arm", "holdout", "campaign_id", "workload", "ycsb_rratio",
})


class AutonomousTrialCompletenessError(RuntimeError):
    """Autonomous trial journal/report completeness violation."""


def _fail(gate: str, message: str) -> None:
    raise AutonomousTrialCompletenessError(f"[{gate}] {message}")


def _reject_constant(value: str) -> None:
    _fail("json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes, *, label: str) -> Any:
    try:
        text = data.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except AutonomousTrialCompletenessError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("json", f"{label} is not strict UTF-8 JSON: {exc}")


def _read_journal(path: Path) -> tuple[bytes, list[dict[str, Any]]]:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            f"[journal-read] attempt journal cannot be read: {path}"
        ) from exc
    if not data or not data.endswith(b"\n"):
        _fail("journal-framing", "attempt journal must be non-empty and newline terminated")
    events: list[dict[str, Any]] = []
    for lineno, line in enumerate(data.splitlines(), 1):
        if not line:
            _fail("journal-framing", f"blank journal line: {lineno}")
        value = _decode_json(line, label=f"journal line {lineno}")
        if not isinstance(value, dict):
            _fail("journal-framing", f"journal line {lineno} is not an object")
        events.append(value)
    return data, events


def _read_report(path: Path) -> dict[str, Any]:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            f"[report-read] report cannot be read: {path}"
        ) from exc
    value = _decode_json(data, label="report")
    if not isinstance(value, dict):
        _fail("report-shape", "report root is not an object")
    return value


def _mapping(value: Any, *, gate: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(gate, f"{label} is not an object")
    return value


def _list(value: Any, *, gate: str, label: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(gate, f"{label} is not a list")
    return value


def _path_identity(path: Any, *, gate: str, label: str) -> Path:
    if not isinstance(path, str) or not path:
        _fail(gate, f"{label} is not a non-empty path string")
    return Path(path).resolve()


def _environment_contract_from_campaign_lock(
    campaign_root: Path, *, producer: Any,
) -> Any:
    lock_path = campaign_root / "campaign.lock"
    try:
        raw = lock_path.read_bytes()
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            f"[campaign-chain] campaign.lock cannot be read: {lock_path}"
        ) from exc
    try:
        decoded = campaign_lock.decode_campaign_lock_bytes(raw)
    except campaign_lock.CampaignLockCodecError as exc:
        raise AutonomousTrialCompletenessError(
            "[campaign-chain] campaign.lock schema is invalid"
        ) from exc
    authority = decoded.authority
    if decoded.is_v1 or authority is None:
        _fail(
            "campaign-chain",
            "campaign.lock v2 authority is required for completeness proof",
        )
    contract_sha256 = authority.environment_contract_sha256
    try:
        return producer.env_contract.resolve_by_contract_sha256(
            contract_sha256
        ).contract
    except producer.env_contract.EnvContractError as exc:
        raise AutonomousTrialCompletenessError(
            "[campaign-chain] campaign.lock environment contract is not ever-active"
        ) from exc


def _canonical_ref(record: Mapping[str, Any]) -> str:
    try:
        return canonical_record_ref("wal", record)
    except (TypeError, ValueError, _layer3_report.Layer3ReportError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[role-bijection] role attempt is not canonical JSON: {exc}"
        ) from exc


def _producer_module() -> Any:
    if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
        from orchestrator.campaign import p3_autonomous_workload_trial as producer
    else:
        from . import p3_autonomous_workload_trial as producer
    return producer


def _sha256_field(value: Any, *, label: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _fail("role-event-shape", f"{label} is not a lowercase SHA-256")


def _check_role_event_shape(record: Mapping[str, Any], *, label: str) -> None:
    required = {
        "event", "workload", "generation", "role", "status", "seq", "ts",
        "invocation_id", "input_payload_sha256", "descriptor_sha256",
        "attempt", "retry",
    }
    missing = sorted(required - set(record))
    if missing:
        _fail("role-event-shape", f"{label} is missing required fields: {missing}")
    if record.get("event") != "role-attempt":
        _fail("role-event-shape", f"{label}.event is not 'role-attempt'")
    if type(record.get("seq")) is not int or record["seq"] < 1:
        _fail("role-event-shape", f"{label}.seq is not a positive int")
    if not isinstance(record.get("ts"), str) or not record["ts"]:
        _fail("role-event-shape", f"{label}.ts is not a non-empty string")
    _sha256_field(record.get("input_payload_sha256"), label=f"{label}.input_payload_sha256")
    _sha256_field(record.get("descriptor_sha256"), label=f"{label}.descriptor_sha256")
    if record.get("attempt") != 1 or type(record.get("attempt")) is not int:
        _fail("attempt-policy", f"{label}.attempt must be exactly 1")
    if record.get("retry") is not False:
        _fail("attempt-policy", f"{label}.retry must be false")

    status = record.get("status")
    if status == "valid":
        status_required = {
            "parsed", "provenance", "raw_response_path", "raw_response_sha256",
        }
        missing = sorted(status_required - set(record))
        if missing:
            _fail("role-event-shape", f"{label} valid event is missing fields: {missing}")
        _mapping(record["parsed"], gate="role-event-shape", label=f"{label}.parsed")
        _mapping(
            record["provenance"], gate="role-event-shape", label=f"{label}.provenance",
        )
        if not record["provenance"]:
            _fail("role-event-shape", f"{label}.provenance is empty")
        if not isinstance(record["raw_response_path"], str) or not record["raw_response_path"]:
            _fail("role-event-shape", f"{label}.raw_response_path is not a non-empty string")
        _sha256_field(record["raw_response_sha256"], label=f"{label}.raw_response_sha256")
    elif status == "invalid":
        status_required = {"error_type", "error", "error_artifacts"}
        missing = sorted(status_required - set(record))
        if missing:
            _fail("role-event-shape", f"{label} invalid event is missing fields: {missing}")
        if not isinstance(record["error_type"], str) or not record["error_type"]:
            _fail("role-event-shape", f"{label}.error_type is not a non-empty string")
        if not isinstance(record["error"], str):
            _fail("role-event-shape", f"{label}.error is not a string")
        _mapping(
            record["error_artifacts"], gate="role-event-shape",
            label=f"{label}.error_artifacts",
        )
    elif status == "skipped":
        if record.get("role") != "auditor":
            _fail("role-event-shape", f"{label} non-auditor role cannot be skipped")
        if record.get("skip_reason") != "machine-pre-audit-rejection":
            _fail("role-event-shape", f"{label}.skip_reason is invalid")
        evidence = _mapping(
            record.get("pre_audit"), gate="role-event-shape",
            label=f"{label}.pre_audit",
        )
        if not _is_pre_audit_reject(evidence):
            _fail("role-event-shape", f"{label}.pre_audit does not prove rejection")
    else:
        _fail("role-event-shape", f"{label}.status is unknown: {status!r}")


def _logical_id(record: Mapping[str, Any], *, label: str) -> tuple[Any, ...]:
    _check_role_event_shape(record, label=label)
    keys = ("workload", "generation", "role", "attempt", "invocation_id")
    missing = [key for key in keys if key not in record]
    if missing:
        _fail("logical-id", f"{label} is missing logical ID fields: {missing}")
    workload, generation, role, attempt, invocation_id = (
        record[key] for key in keys
    )
    if not isinstance(workload, str) or not workload:
        _fail("logical-id", f"{label}.workload is invalid")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        _fail("logical-id", f"{label}.generation is invalid")
    if role not in _ROLE_ORDER:
        _fail("logical-id", f"{label}.role is invalid")
    if type(attempt) is not int or attempt != 1:
        _fail("attempt-policy", f"{label}.attempt must be exactly 1")
    if not isinstance(invocation_id, str) or not invocation_id:
        _fail("logical-id", f"{label}.invocation_id is invalid")
    return workload, generation, role, attempt, invocation_id


def _require_unique_attempts(
    records: Sequence[Mapping[str, Any]], *, side: str,
) -> None:
    refs = [_canonical_ref(record) for record in records]
    if len(refs) != len(set(refs)):
        _fail("canonical-duplicate", f"{side} has an exact canonical duplicate")
    logical = [_logical_id(record, label=f"{side} role attempt") for record in records]
    if len(logical) != len(set(logical)):
        _fail("logical-id", f"{side} has a duplicate logical role attempt ID")


def _check_role_session_isolation(
    *, provider: object, records: Sequence[Mapping[str, Any]],
) -> None:
    if provider != "claude-headless":
        return
    observations = tuple(
        (
            record.get("role"),
            record.get("provenance", {}).get("child_id")
            if isinstance(record.get("provenance"), Mapping)
            else None,
        )
        for record in records
        if record.get("status") == "valid"
    )
    evaluation = evaluate_role_session_isolation(observations)
    if not evaluation.accepted:
        _fail("role-session-isolation", evaluation.reason)


def _check_closed_events(events: Sequence[Mapping[str, Any]]) -> None:
    for index, event in enumerate(events):
        kind = event.get("event")
        if not isinstance(kind, str) or kind not in _EVENTS:
            _fail("closed-event-set", f"journal event {index} has unknown kind: {kind!r}")


def _check_journal_sequence(events: Sequence[Mapping[str, Any]]) -> None:
    for expected, event in enumerate(events, 1):
        if type(event.get("seq")) is not int or event.get("seq") != expected:
            _fail("journal-sequence", f"journal seq must be contiguous 1..N; expected {expected}")
        if not isinstance(event.get("ts"), str) or not event.get("ts"):
            _fail("journal-sequence", f"journal event seq={expected} has no timestamp")


def _check_transport_admission(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
) -> None:
    admissions = [
        event for event in events if event.get("event") == "transport-admission"
    ]
    if len(admissions) > 1:
        _fail("transport-admission", "transport-admission may occur at most once")
    report_has_receipt = "transport_receipt" in report
    if bool(admissions) != report_has_receipt:
        _fail(
            "transport-admission",
            "transport-admission and report transport_receipt must occur together",
        )
    if not admissions:
        return

    admission = admissions[0]
    required = {"event", "transport_receipt", "seq", "ts"}
    if set(admission) != required:
        _fail(
            "transport-admission",
            "transport-admission fields must match the producer exact set",
        )
    starts = [event for event in events if event.get("event") == "run-start"]
    if (
        len(events) < 2
        or events[0] is not admission
        or len(starts) != 1
        or events[1] is not starts[0]
    ):
        _fail(
            "transport-admission",
            "transport-admission must occur immediately before run-start and role attempts",
        )
    if report.get("provider") != "claude-headless":
        _fail(
            "transport-admission",
            "transport-admission requires the claude-headless provider",
        )
    receipt = admission.get("transport_receipt")
    if type(receipt) is not dict:
        _fail(
            "transport-admission",
            "transport-admission.transport_receipt must be an object",
        )
    producer = _producer_module()
    try:
        validated = producer._validate_transport_receipt(receipt)
        report_receipt = producer._validate_transport_receipt(
            report.get("transport_receipt")
        )
    except producer.AutonomousTrialError as exc:
        _fail("transport-admission", f"transport receipt is invalid: {exc}")
    if validated != report_receipt:
        _fail(
            "transport-admission",
            "transport-admission receipt does not match report projection",
        )


def _check_launch_admission_projection(
    *,
    report: Mapping[str, Any],
    start: Mapping[str, Any],
) -> None:
    report_admission = _mapping(
        report.get("launch_admission"),
        gate="launch-admission",
        label="report.launch_admission",
    )
    start_admission = _mapping(
        start.get("launch_admission"),
        gate="launch-admission",
        label="run-start.launch_admission",
    )
    if set(report_admission) != _LAUNCH_ADMISSION_KEYS:
        _fail("launch-admission", "report launch_admission exact keys differ")
    if dict(start_admission) != dict(report_admission):
        _fail("launch-admission", "run-start/report launch_admission differs")
    mode = report_admission.get("mode")
    if mode not in {
        "registered-effective", "explicit-unregistered-exploratory",
    }:
        _fail("launch-admission", "launch mode is outside the closed set")
    if report_admission.get("certifying") is not False:
        _fail("launch-admission", "this producer cannot emit certifying input")
    if report_admission.get("trial_id") != report.get("trial_id"):
        _fail("launch-admission", "launch trial_id differs from report")
    if report_admission.get("workloads") != report.get("workloads_requested"):
        _fail("launch-admission", "launch workloads differ from report")
    binding = report_admission.get("binding")
    activation_digest = report_admission.get("activation_report_digest_sha256")
    if mode == "registered-effective":
        binding = _mapping(
            binding, gate="launch-admission", label="launch_admission.binding",
        )
        if set(binding) != _LAUNCH_BINDING_KEYS:
            _fail("launch-admission", "registered launch binding exact keys differ")
        if (
            report_admission.get("reason_code")
            != "registered-effective-non-certifying"
            or binding.get("trial_id") != report.get("trial_id")
            or [binding.get("workload")] != report.get("workloads_requested")
            or not isinstance(activation_digest, str)
            or _SHA256_RE.fullmatch(activation_digest) is None
        ):
            _fail("launch-admission", "registered launch projection is inconsistent")
    elif (
        report_admission.get("reason_code")
        != "explicit-unregistered-exploratory"
        or binding is not None
        or activation_digest is not None
    ):
        _fail("launch-admission", "exploratory launch projection is inconsistent")


def _check_run_envelope(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
    attempt_journal: Path,
) -> None:
    starts = [event for event in events if event.get("event") == "run-start"]
    finishes = [event for event in events if event.get("event") == "run-finish"]
    if len(starts) != 1 or len(finishes) != 1:
        _fail("run-envelope", "run-start and run-finish must each occur exactly once")
    first_run_event = 1 if events[0].get("event") == "transport-admission" else 0
    if events[first_run_event] is not starts[0] or events[-1] is not finishes[0]:
        _fail(
            "run-envelope",
            "run-start/run-finish must bound the run after any transport admission",
        )
    start, finish = starts[0], finishes[0]
    producer = _producer_module()
    if report.get("schema_version") != producer.REPORT_SCHEMA_VERSION:
        _fail("run-envelope", "report.schema_version does not match producer version")
    if start.get("schema_version") != producer.SCHEMA_VERSION:
        _fail("run-envelope", "run-start.schema_version does not match producer version")

    trial_id = report.get("trial_id")
    if not isinstance(trial_id, str) or not trial_id:
        _fail("run-envelope", "report.trial_id is not a non-empty string")
    if not isinstance(start.get("trial_id"), str) or not start.get("trial_id"):
        _fail("run-envelope", "run-start.trial_id is not a non-empty string")
    provider = report.get("provider")
    start_provider = start.get("provider")
    if (
        not isinstance(provider, str)
        or not isinstance(start_provider, str)
        or provider not in producer.PROVIDER_KINDS
        or start_provider not in producer.PROVIDER_KINDS
    ):
        _fail("run-envelope", "provider is outside the producer closed set")
    if type(report.get("do_build")) is not bool or type(start.get("do_build")) is not bool:
        _fail("run-envelope", "do_build must be a bool in report and run-start")
    budget = report.get("generation_budget_per_workload")
    start_budget = start.get("generation_budget_per_workload")
    if type(budget) is not int or budget < 1 or type(start_budget) is not int or start_budget < 1:
        _fail("run-envelope", "generation budget must be a positive int in report and run-start")
    stop_policy = _mapping(
        report.get("stop_policy"), gate="run-envelope", label="report.stop_policy",
    )
    max_wall_s = stop_policy.get("max_wall_s")
    if type(max_wall_s) is not int or max_wall_s < 1:
        _fail("run-envelope", "report.stop_policy.max_wall_s must be a positive int")
    if type(start.get("max_wall_s")) is not int or start["max_wall_s"] < 1:
        _fail("run-envelope", "run-start.max_wall_s must be a positive int")
    comparisons = (
        ("trial_id", start.get("trial_id"), report.get("trial_id")),
        ("provider", start.get("provider"), report.get("provider")),
        (
            "generation_budget_per_workload",
            start.get("generation_budget_per_workload"),
            report.get("generation_budget_per_workload"),
        ),
        ("do_build", start.get("do_build"), report.get("do_build")),
        (
            "max_wall_s",
            start.get("max_wall_s"),
            max_wall_s,
        ),
    )
    for label, journal_value, report_value in comparisons:
        if type(journal_value) is not type(report_value) or journal_value != report_value:
            _fail("run-envelope", f"run-start/report mismatch: {label}")
    if budget > producer.MAX_APPROVED_GENERATIONS:
        _fail(
            "run-envelope",
            "generation budget exceeds the current producer-approved limit",
        )
    workloads = report.get("workloads_requested")
    if start.get("workloads") != workloads:
        _fail("run-envelope", "run-start workloads do not match report order")
    if finish.get("status") != report.get("status"):
        _fail("run-envelope", "run-finish status does not match report")
    journal_ref = _path_identity(
        report.get("attempt_journal"), gate="run-envelope",
        label="report.attempt_journal",
    )
    try:
        same_journal = journal_ref.samefile(Path(attempt_journal))
    except OSError as exc:
        raise AutonomousTrialCompletenessError(
            "[run-envelope] report.attempt_journal cannot be resolved"
        ) from exc
    if not same_journal:
        _fail("run-envelope", "report.attempt_journal names a different journal")
    finish_report = _path_identity(
        finish.get("report"), gate="run-envelope", label="run-finish.report",
    )
    expected_report = Path(attempt_journal).resolve().parent / "report.json"
    if finish_report != expected_report:
        _fail("run-envelope", "run-finish.report names a different report")
    _check_launch_admission_projection(report=report, start=start)


def _terminal_events(events: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [event for event in events if event.get("event") in _TERMINAL_EVENTS]


def _check_terminal_projection(
    *, report: Mapping[str, Any], events: Sequence[Mapping[str, Any]],
    cells: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    terminals = _terminal_events(events)
    if len(terminals) > 1:
        _fail("terminal-projection", "more than one terminal supervisor event")
    fatal = report.get("fatal_error")
    if not terminals:
        if "fatal_error" in report:
            _fail("terminal-projection", "fatal_error has no terminal journal event")
        if any(cell.get("stop_reason") == "supervisor-error" for cell in cells):
            _fail("terminal-projection", "supervisor-error cell has no terminal journal event")
        return None
    terminal = terminals[0]
    if len(events) < 2 or events[-2] is not terminal:
        _fail("terminal-projection", "terminal supervisor event must precede run-finish")
    if report.get("status") != "partial":
        _fail("terminal-projection", "terminal supervisor event requires partial status")
    fatal_map = _mapping(fatal, gate="terminal-projection", label="fatal_error")
    kind = terminal["event"]
    if kind == "provider-init-error":
        expected = {"type": terminal.get("type"), "message": terminal.get("message")}
        if dict(fatal_map) != expected or cells:
            _fail("terminal-projection", "provider-init-error projection is inconsistent")
    elif kind == "supervisor-error":
        expected = {"type": terminal.get("type"), "message": terminal.get("message")}
        if dict(fatal_map) != expected:
            _fail("terminal-projection", "supervisor-error fatal projection is inconsistent")
        workload = terminal.get("workload")
        matches = [cell for cell in cells if cell.get("workload") == workload]
        if len(matches) != 1:
            _fail("terminal-projection", "supervisor-error cell is missing or duplicated")
        cell = matches[0]
        if cell.get("stop_reason") != "supervisor-error" or cell.get("error") != expected:
            _fail("terminal-projection", "supervisor-error cell projection is inconsistent")
    else:
        expected = {
            "type": "SupervisorWallBudget",
            "message": "wall budget expired before the next workload",
        }
        if dict(fatal_map) != expected:
            _fail("terminal-projection", "supervisor-wall-budget fatal projection is inconsistent")
    return terminal


def _is_pre_audit_reject(evidence: Mapping[str, Any]) -> bool:
    forbidden = evidence.get("forbidden_identifiers")
    return evidence.get("passed") is False or (
        isinstance(forbidden, list) and bool(forbidden)
    )


def _completion_status_is_valid(
    entry: Mapping[str, Any], *, generation: Mapping[str, Any], label: str,
) -> bool:
    if entry.get("status") == "valid":
        return True
    if entry.get("status") != "skipped" or entry.get("role") != "auditor":
        return False
    preview = generation.get("preview")
    if not isinstance(preview, Mapping) or dict(entry.get("pre_audit", {})) != dict(preview):
        _fail("state-machine", f"{label} skipped auditor evidence differs from generation.preview")
    return _is_pre_audit_reject(preview)


def _check_harness(generation: Mapping[str, Any], *, label: str) -> Mapping[str, Any]:
    harness = _mapping(generation.get("harness"), gate="state-machine", label=f"{label}.harness")
    if not harness:
        _fail("state-machine", f"{label}.harness is empty")
    required = {"outcome", "variant", "stop_reason", "iteration", "ran"}
    missing = sorted(required - set(harness))
    if missing:
        _fail("state-machine", f"{label}.harness is missing required fields: {missing}")
    if not isinstance(harness["outcome"], str) or not harness["outcome"]:
        _fail("state-machine", f"{label}.harness.outcome is invalid")
    if harness["variant"] is not None and (
        not isinstance(harness["variant"], str) or not harness["variant"]
    ):
        _fail("state-machine", f"{label}.harness.variant is invalid")
    if (
        not isinstance(harness["stop_reason"], str)
        or harness["stop_reason"] not in _producer_module().DRIVER_STOP_REASONS
    ):
        _fail("state-machine", f"{label}.harness.stop_reason is unknown")
    if type(harness["iteration"]) is not int or harness["iteration"] < 0:
        _fail("state-machine", f"{label}.harness.iteration is invalid")
    if type(harness["ran"]) is not bool:
        _fail("state-machine", f"{label}.harness.ran is not a bool")
    if generation.get("outcome") != harness["outcome"]:
        _fail("state-machine", f"{label}.outcome differs from harness.outcome")
    return harness


def _role_prefix_length(roles: Mapping[str, Any], *, label: str) -> int:
    unknown = sorted(set(roles) - set(_ROLE_ORDER))
    if unknown:
        _fail("state-machine", f"{label} has unknown role keys: {unknown}")
    present = set(roles)
    for length in range(len(_ROLE_ORDER) + 1):
        if present == set(_ROLE_ORDER[:length]):
            return length
    _fail("state-machine", f"{label} roles are not an allowed prefix")


def _check_cell_metadata(
    cell: Mapping[str, Any], *, cell_index: int, generations: Sequence[Any],
) -> str | None:
    required = {
        "workload_flags", "descriptor", "descriptor_binding",
        "campaign_id", "campaign_root",
    }
    early_error_without_work = (
        not generations
        and cell.get("stop_reason") in {"supervisor-error", "provider-init-error"}
    )
    if early_error_without_work:
        required = set()
    missing = sorted(required - set(cell))
    if missing:
        _fail("cell-metadata", f"cells[{cell_index}] is missing required fields: {missing}")
    if "workload_flags" in cell:
        workload_flags = _mapping(
            cell["workload_flags"], gate="cell-metadata",
            label=f"cells[{cell_index}].workload_flags",
        )
        if not workload_flags:
            _fail("cell-metadata", f"cells[{cell_index}].workload_flags is empty")
    if "descriptor" in cell:
        descriptor = _mapping(
            cell["descriptor"], gate="cell-metadata",
            label=f"cells[{cell_index}].descriptor",
        )
        if not descriptor:
            _fail("cell-metadata", f"cells[{cell_index}].descriptor is empty")
    descriptor_sha256 = None
    if "descriptor_binding" in cell:
        descriptor_binding = _mapping(
            cell["descriptor_binding"], gate="cell-metadata",
            label=f"cells[{cell_index}].descriptor_binding",
        )
        descriptor_sha256 = descriptor_binding.get("output_sha256")
        if (
            not isinstance(descriptor_sha256, str)
            or _SHA256_RE.fullmatch(descriptor_sha256) is None
        ):
            _fail(
                "cell-metadata",
                f"cells[{cell_index}].descriptor_binding.output_sha256 is not a lowercase SHA-256",
            )
    if "campaign_id" in cell and (
        not isinstance(cell["campaign_id"], str) or not cell["campaign_id"]
    ):
        _fail("cell-metadata", f"cells[{cell_index}].campaign_id is not a non-empty string")
    if "campaign_root" in cell and (
        not isinstance(cell["campaign_root"], str) or not cell["campaign_root"]
    ):
        _fail("cell-metadata", f"cells[{cell_index}].campaign_root is not a non-empty string")
    return descriptor_sha256


def _scan_report_attempts(
    *, cells: Sequence[Mapping[str, Any]], journal_attempts: Sequence[Mapping[str, Any]],
    budget: int,
) -> list[Mapping[str, Any]]:
    report_attempts: list[Mapping[str, Any]] = []
    for cell_index, cell in enumerate(cells):
        workload = cell.get("workload")
        generations = _list(
            cell.get("generations"), gate="state-machine",
            label=f"cells[{cell_index}].generations",
        )
        descriptor_sha256 = _check_cell_metadata(
            cell, cell_index=cell_index, generations=generations,
        )
        generation_numbers: list[int] = []
        prefix_lengths: list[int] = []
        generation_entries: list[list[Mapping[str, Any]]] = []
        for generation_index, raw_generation in enumerate(generations):
            generation = _mapping(
                raw_generation, gate="state-machine",
                label=f"cell {workload!r} generation {generation_index}",
            )
            number = generation.get("generation")
            if isinstance(number, bool) or not isinstance(number, int):
                _fail("state-machine", f"cell {workload!r} has invalid generation number")
            generation_numbers.append(number)
            roles = _mapping(
                generation.get("roles"), gate="state-machine",
                label=f"cell {workload!r} generation {number} roles",
            )
            prefix_lengths.append(_role_prefix_length(
                roles, label=f"cell {workload!r} generation {number}",
            ))
            entries: list[Mapping[str, Any]] = []
            for role in _ROLE_ORDER:
                if role not in roles:
                    continue
                raw_entry = roles[role]
                entry = _mapping(
                    raw_entry, gate="report-role-shape",
                    label=f"{workload}.g{number}.{role}",
                )
                if entry.get("event") != "role-attempt":
                    _fail("report-role-shape", f"{workload}.g{number}.{role} is not a journaled role event")
                if (
                    entry.get("workload") != workload
                    or entry.get("generation") != number
                    or entry.get("role") != role
                ):
                    _fail("role-placement", f"{workload}.g{number}.{role} is misplaced")
                _check_role_event_shape(entry, label=f"{workload}.g{number}.{role}")
                if entry.get("descriptor_sha256") != descriptor_sha256:
                    _fail(
                        "descriptor-binding",
                        f"{workload}.g{number}.{role}.descriptor_sha256 differs from cell binding",
                    )
                entries.append(entry)
                report_attempts.append(entry)
            generation_entries.append(entries)
        if generation_numbers != list(range(1, len(generations) + 1)):
            _fail("state-machine", f"cell {workload!r} generations are not contiguous from 1")
        if len(generations) > budget:
            _fail("state-machine", f"cell {workload!r} exceeds generation budget")
        stop_reason = cell.get("stop_reason")
        producer = _producer_module()
        driver_terminal_reasons = producer.DRIVER_STOP_REASONS - {"continue"}
        known_stop_reasons = {
            "fixed-generation-budget", "role-invalid",
            "supervisor-wall-budget", "supervisor-error",
        } | set(driver_terminal_reasons)
        if not isinstance(stop_reason, str) or stop_reason not in known_stop_reasons:
            _fail("state-machine", f"cell {workload!r} has unknown stop_reason: {stop_reason!r}")
        full = len(_ROLE_ORDER)
        if stop_reason == "fixed-generation-budget":
            if len(generations) != budget or any(length != full for length in prefix_lengths):
                _fail("state-machine", f"fixed-budget cell {workload!r} is incomplete")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"fixed-budget cell {workload!r} has non-valid role history")
                if _check_harness(generation, label=f"{workload}.g{index}")["stop_reason"] != "continue":
                    _fail("state-machine", f"fixed-budget cell {workload!r} has terminal harness stop")
        elif stop_reason == "role-invalid":
            if not generations or any(length != full for length in prefix_lengths[:-1]):
                _fail("state-machine", f"role-invalid cell {workload!r} has invalid history")
            last_roles = generations[-1]["roles"]
            last_role = _ROLE_ORDER[prefix_lengths[-1] - 1] if prefix_lengths[-1] else None
            last_entry = last_roles.get(last_role) if last_role is not None else None
            if not isinstance(last_entry, Mapping) or last_entry.get("status") != "invalid":
                _fail("state-machine", f"role-invalid cell {workload!r} has no invalid final role")
            for index, (generation, entries) in enumerate(
                zip(generations[:-1], generation_entries[:-1]), 1,
            ):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"role-invalid cell {workload!r} has invalid prior role")
                if _check_harness(
                    generation, label=f"{workload}.g{index}",
                )["stop_reason"] != "continue":
                    _fail(
                        "state-machine",
                        f"role-invalid cell {workload!r} has a terminal prior harness stop",
                    )
            final_generation = generations[-1]
            for entry in generation_entries[-1][:-1]:
                if not _completion_status_is_valid(
                    entry, generation=final_generation,
                    label=f"{workload}.g{generation_numbers[-1]}.{entry.get('role')}",
                ):
                    _fail("state-machine", f"role-invalid cell {workload!r} has early invalid role")
            if last_role == "critic":
                _check_harness(final_generation, label=f"{workload}.g{generation_numbers[-1]}")
        elif stop_reason == "supervisor-wall-budget":
            if any(length != full for length in prefix_lengths):
                _fail("state-machine", f"wall-budget cell {workload!r} has partial role state")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"wall-budget cell {workload!r} has non-valid role history")
                if _check_harness(
                    generation, label=f"{workload}.g{index}",
                )["stop_reason"] != "continue":
                    _fail(
                        "state-machine",
                        f"wall-budget cell {workload!r} has a terminal prior harness stop",
                    )
        elif stop_reason == "supervisor-error":
            if any(length != full for length in prefix_lengths[:-1]):
                _fail("state-machine", f"supervisor-error cell {workload!r} has invalid history")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"supervisor-error cell {workload!r} has invalid role history")
                if index < len(generations) or "harness" in generation:
                    harness = _check_harness(generation, label=f"{workload}.g{index}")
                    if index < len(generations) and harness["stop_reason"] != "continue":
                        _fail(
                            "state-machine",
                            f"supervisor-error cell {workload!r} has a terminal prior harness stop",
                        )
        else:
            if not generations or any(length != full for length in prefix_lengths):
                _fail("state-machine", f"stopped cell {workload!r} is incomplete")
            for index, (generation, entries) in enumerate(zip(generations, generation_entries), 1):
                if not all(_completion_status_is_valid(
                    entry, generation=generation, label=f"{workload}.g{index}.{entry.get('role')}"
                ) for entry in entries):
                    _fail("state-machine", f"stopped cell {workload!r} has non-valid role history")
                harness = _check_harness(generation, label=f"{workload}.g{index}")
                expected_stop = stop_reason if index == len(generations) else "continue"
                if harness["stop_reason"] != expected_stop:
                    _fail("state-machine", f"stopped cell {workload!r} harness stop projection differs")
    return report_attempts


def _check_attempt_sequence(
    journal_attempts: Sequence[Mapping[str, Any]],
    report_attempts: Sequence[Mapping[str, Any]],
) -> None:
    keys = ("workload", "generation", "role")
    journal_order = [tuple(event.get(key) for key in keys) for event in journal_attempts]
    report_order = [tuple(event.get(key) for key in keys) for event in report_attempts]
    if journal_order != report_order:
        _fail("state-machine", "journal role attempts do not follow report role state order")


def _check_workload_coverage(
    *, report: Mapping[str, Any], cells: Sequence[Mapping[str, Any]],
    terminal: Mapping[str, Any] | None,
) -> None:
    requested = report.get("workloads_requested")
    if (
        not isinstance(requested, list)
        or not requested
        or not all(isinstance(item, str) and item for item in requested)
        or len(requested) != len(set(requested))
    ):
        _fail("workload-coverage", "workloads_requested is not a unique string list")
    actual = [cell.get("workload") for cell in cells]
    if len(actual) != len(set(actual)) or actual != requested[:len(actual)]:
        _fail("workload-coverage", "cell workloads are not a unique requested prefix")
    terminal_kind = terminal.get("event") if terminal is not None else None
    if len(actual) == len(requested):
        if terminal_kind == "supervisor-wall-budget":
            _fail("workload-coverage", "wall-budget terminal event has no missing workload")
        if (
            terminal_kind == "supervisor-error"
            and (not actual or terminal.get("workload") != actual[-1])
        ):
            _fail("workload-coverage", "supervisor-error cell is not the final cell")
        return
    if terminal is None:
        _fail("workload-coverage", "requested workload suffix is unexplained")
    kind = terminal_kind
    if kind == "provider-init-error" and not actual:
        return
    if kind == "supervisor-wall-budget" and terminal.get("workload") == requested[len(actual)]:
        return
    if (
        kind == "supervisor-error"
        and actual
        and terminal.get("workload") == actual[-1]
    ):
        return
    _fail("workload-coverage", "terminal event does not explain requested workload suffix")


def _check_status_projection(
    report: Mapping[str, Any], cells: Sequence[Mapping[str, Any]],
) -> None:
    requested = report.get("workloads_requested")
    complete = (
        isinstance(requested, list)
        and len(cells) == len(requested)
        and report.get("fatal_error") is None
        and all(
            cell.get("stop_reason")
            not in {"role-invalid", "supervisor-error", "supervisor-wall-budget"}
            for cell in cells
        )
    )
    expected = "complete" if complete else "partial"
    if report.get("status") != expected:
        _fail("terminal-projection", f"report status must be {expected!r}")


def assert_autonomous_trial_completeness(
    *, report: Mapping[str, Any], attempt_journal: Path,
) -> None:
    """Re-read *attempt_journal* and verify its complete report projection."""
    report = _mapping(report, gate="report-shape", label="report")
    journal_bytes, events = _read_journal(Path(attempt_journal))
    expected_hash = hashlib.sha256(journal_bytes).hexdigest()
    if report.get("attempt_journal_sha256") != expected_hash:
        _fail("journal-hash", "attempt_journal_sha256 does not match bytes read")
    _check_closed_events(events)
    _check_journal_sequence(events)
    _check_transport_admission(report=report, events=events)
    _check_run_envelope(
        report=report, events=events, attempt_journal=Path(attempt_journal),
    )
    raw_cells = _list(report.get("cells"), gate="report-shape", label="report.cells")
    cells = [
        _mapping(cell, gate="report-shape", label=f"cells[{index}]")
        for index, cell in enumerate(raw_cells)
    ]
    do_build = report.get("do_build")
    for index, cell in enumerate(cells):
        decision = cell.get("admission_decision")
        if do_build is False:
            if decision != {"admission_status": "not-applicable"}:
                _fail(
                    "artifact-admission",
                    f"cells[{index}] no-build admission decision is not exact",
                )
        elif do_build is True:
            decision = _mapping(
                decision, gate="artifact-admission",
                label=f"cells[{index}].admission_decision",
            )
            if (
                decision.get("schema_version")
                != "campaign-artifact-admission-decision/v1"
                or decision.get("admission_status") != "admitted"
                or decision.get("classification") != "admitted-new-schema"
            ):
                _fail(
                    "artifact-admission",
                    f"cells[{index}] build admission decision is not positive",
                )
    terminal = _check_terminal_projection(report=report, events=events, cells=cells)
    budget = report.get("generation_budget_per_workload")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        _fail("state-machine", "generation budget is not a positive int")
    journal_attempts = [event for event in events if event.get("event") == "role-attempt"]
    _require_unique_attempts(journal_attempts, side="journal")
    _check_role_session_isolation(
        provider=report.get("provider"), records=journal_attempts,
    )
    report_attempts = _scan_report_attempts(
        cells=cells, journal_attempts=journal_attempts, budget=budget,
    )
    _require_unique_attempts(report_attempts, side="report")
    _check_attempt_sequence(journal_attempts, report_attempts)
    if Counter(map(_canonical_ref, journal_attempts)) != Counter(
        map(_canonical_ref, report_attempts)
    ):
        _fail("role-bijection", "journal/report role-attempt multisets differ")
    _check_workload_coverage(report=report, cells=cells, terminal=terminal)
    _check_status_projection(report, cells)


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=False,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AutonomousTrialCompletenessError(
            f"[campaign-chain] layer3 report is not canonical JSON: {exc}"
        ) from exc


def _fresh_layer3_for_comparison(
    *, campaign_root: Path, persisted_path: Path,
    persisted: Mapping[str, Any], output_root: Path,
) -> Mapping[str, Any]:
    meta = persisted.get("meta")
    generated_from_head = (
        meta.get("generated_from_head") if isinstance(meta, Mapping) else None
    )
    if (
        not isinstance(generated_from_head, str)
        or _GIT_OBJECT_ID_RE.fullmatch(generated_from_head) is None
    ):
        _fail("campaign-chain", "persisted layer3 generated_from_head is not a git object ID")
    try:
        fresh = _layer3_report.build_report(
            campaign_root,
            generated_from_head="0" * 40,
            output_root=output_root,
        )
    except _layer3_report.Layer3ReportError as exc:
        raise AutonomousTrialCompletenessError(
            f"[campaign-chain] fresh layer3 rebuild failed: {exc}"
        ) from exc
    relative_persisted = persisted_path.relative_to(campaign_root).as_posix()
    artifacts = fresh.get("artifact_refs")
    if not isinstance(artifacts, list):
        _fail("campaign-chain", "fresh layer3 artifact_refs is not a list")
    fresh = dict(fresh)
    fresh["artifact_refs"] = [
        item for item in artifacts
        if not isinstance(item, Mapping) or item.get("path") != relative_persisted
    ]
    return fresh


def _without_generated_from_head(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized.setdefault("acceptance_receipt", None)
    normalized.setdefault("certifying_input", False)
    meta = _mapping(
        report.get("meta"), gate="campaign-chain", label="layer3 report.meta",
    )
    normalized_meta = dict(meta)
    normalized_meta.pop("generated_from_head", None)
    normalized["meta"] = normalized_meta
    return normalized


def _require_exact_layer3_admission_decision(
    report: Mapping[str, Any], *, expected: Mapping[str, Any], label: str,
) -> Mapping[str, Any]:
    """Validate Layer3's detached decision independently of a fresh Layer3 rebuild."""
    report = _mapping(report, gate="campaign-chain", label=label)
    decision = _mapping(
        report.get("admission_decision"), gate="campaign-chain",
        label=f"{label}.admission_decision",
    )
    if set(decision) != _ADMISSION_DECISION_KEYS:
        _fail("campaign-chain", f"{label} admission decision exact keys differ")
    validator = _mapping(
        decision.get("validator"), gate="campaign-chain",
        label=f"{label}.admission_decision.validator",
    )
    overlay = _mapping(
        decision.get("overlay"), gate="campaign-chain",
        label=f"{label}.admission_decision.overlay",
    )
    if set(validator) != _ADMISSION_VALIDATOR_KEYS:
        _fail("campaign-chain", f"{label} admission validator exact keys differ")
    if set(overlay) != _ADMISSION_OVERLAY_KEYS:
        _fail("campaign-chain", f"{label} admission overlay exact keys differ")
    if _canonical_bytes(decision) != _canonical_bytes(expected):
        _fail("campaign-chain", f"{label} admission decision differs from validator")
    return decision


def _require_certifying_layer3_admission(
    report: Mapping[str, Any], *, label: str,
) -> None:
    """certifying Layer3 入力は明示的に admitted のものだけへ閉じる。"""
    if report.get("certifying_input", False) is not True:
        return
    decision = _mapping(
        report.get("admission_decision"), gate="campaign-chain",
        label=f"{label}.admission_decision",
    )
    if decision.get("admission_status") != "admitted":
        _fail(
            "campaign-chain",
            f"{label} certifying input requires admission_status=admitted",
        )


def assert_campaign_layer3_chain(
    *, report: Mapping[str, Any], output_root: Path,
) -> None:
    """Deep-compare each persisted layer3 report with a fresh WAL rebuild."""
    report = _mapping(report, gate="campaign-chain", label="report")
    cells = _list(report.get("cells"), gate="campaign-chain", label="report.cells")
    output_root = Path(output_root).resolve()
    seen: set[str] = set()
    producer = _producer_module()
    trial_id = report.get("trial_id")
    budget = report.get("generation_budget_per_workload")
    if not isinstance(trial_id, str) or not trial_id:
        _fail("campaign-chain", "report.trial_id is not a non-empty string")
    if type(budget) is not int or budget < 1:
        _fail("campaign-chain", "report generation budget is not a positive int")
    if budget > producer.MAX_APPROVED_GENERATIONS:
        _fail("campaign-chain", "report generation budget exceeds producer limit")
    launch_admission = _mapping(
        report.get("launch_admission"),
        gate="campaign-chain",
        label="report.launch_admission",
    )
    certifying_input = launch_admission.get("certifying")
    if type(certifying_input) is not bool:
        _fail("campaign-chain", "launch admission certifying is not a bool")
    for index, raw_cell in enumerate(cells):
        cell = _mapping(raw_cell, gate="campaign-chain", label=f"cells[{index}]")
        campaign_id = cell.get("campaign_id")
        campaign_root_value = cell.get("campaign_root")
        if campaign_id is None and campaign_root_value is None:
            _fail("campaign-chain", f"cells[{index}] has no campaign identity")
        if not isinstance(campaign_id, str) or not campaign_id or campaign_id in seen:
            _fail("campaign-chain", f"cells[{index}] campaign_id is invalid or duplicated")
        seen.add(campaign_id)
        workload = cell.get("workload")
        if not isinstance(workload, str) or workload not in producer.WORKLOADS:
            _fail("campaign-chain", f"cells[{index}].workload is not producer-supported")
        workload_flags = producer.WORKLOADS[workload]
        expected_descriptor, expected_binding = producer._descriptor_for(workload_flags)
        if cell.get("workload_flags") != workload_flags:
            _fail("campaign-chain", f"cells[{index}].workload_flags differs from producer")
        if cell.get("descriptor") != expected_descriptor:
            _fail("campaign-chain", f"cells[{index}].descriptor differs from producer")
        if cell.get("descriptor_binding") != expected_binding:
            _fail("campaign-chain", f"cells[{index}].descriptor_binding differs from producer")
        campaign_root = _path_identity(
            campaign_root_value, gate="campaign-chain",
            label=f"cells[{index}].campaign_root",
        )
        expected_root = (output_root / "campaigns" / campaign_id).resolve()
        if campaign_root != expected_root:
            _fail("campaign-chain", f"cells[{index}] campaign identity/path mismatch")
        contract = _environment_contract_from_campaign_lock(
            campaign_root, producer=producer,
        )
        context = producer.build_run_context(
            generator_id=producer.GeneratorId.S8A_TRIGGER_SWEEP,
        )
        expected_cfg = producer._campaign_for(
            workload=workload,
            workload_flags=workload_flags,
            descriptor=expected_descriptor,
            descriptor_record=expected_binding,
            trial_id=trial_id,
            generations=budget,
            contract=contract,
            build_context=context,
        )
        expected_campaign_id = str(producer.ident.campaign_id(expected_cfg))
        if campaign_id != expected_campaign_id:
            _fail("campaign-chain", f"cells[{index}] campaign_id differs from producer derivation")
        persisted_path = campaign_root / "reports" / "layer3_report.json"
        try:
            persisted = _read_report(persisted_path)
        except AutonomousTrialCompletenessError as exc:
            raise AutonomousTrialCompletenessError(
                f"[campaign-chain] persisted layer3 report cannot be read: {persisted_path}"
            ) from exc
        meta = persisted.get("meta")
        if not isinstance(meta, Mapping) or meta.get("campaign_id") != campaign_id:
            _fail("campaign-chain", "persisted layer3 campaign identity mismatch")
        if persisted.get("certifying_input", False) is not certifying_input:
            _fail(
                "campaign-chain",
                "persisted layer3 certifying_input differs from launch admission",
            )
        _require_certifying_layer3_admission(
            persisted, label="persisted layer3 report",
        )
        try:
            expected_decision = require_admitted_campaign(
                campaign_root,
            ).decision.as_receipt()
        except ArtifactAdmissionError as exc:
            raise AutonomousTrialCompletenessError(
                "[campaign-chain] independent campaign admission validation failed"
            ) from exc
        _require_exact_layer3_admission_decision(
            persisted, expected=expected_decision, label="persisted layer3 report",
        )
        _require_exact_layer3_admission_decision(
            {"admission_decision": cell.get("admission_decision")},
            expected=expected_decision, label=f"cells[{index}]",
        )
        fresh = _fresh_layer3_for_comparison(
            campaign_root=campaign_root,
            persisted_path=persisted_path,
            persisted=persisted,
            output_root=output_root,
        )
        if _canonical_bytes(_without_generated_from_head(persisted)) != _canonical_bytes(
            _without_generated_from_head(fresh)
        ):
            _fail("campaign-chain", "persisted layer3 report differs from fresh rebuild")


def verify_autonomous_trial_files(
    attempt_journal: Path,
    report_json: Path,
    *,
    campaign_output_root: Path | None = None,
) -> None:
    """Independently verify persisted journal/report files and optional campaigns."""
    report = _read_report(Path(report_json))
    expected_report = Path(attempt_journal).resolve().parent / "report.json"
    if Path(report_json).resolve() != expected_report:
        _fail("run-envelope", "report_json is not the journal sibling report.json")
    assert_autonomous_trial_completeness(
        report=report, attempt_journal=Path(attempt_journal),
    )
    if report.get("do_build") is True and campaign_output_root is None:
        _fail("campaign-chain", "build trial verification requires campaign_output_root")
    if campaign_output_root is not None:
        assert_campaign_layer3_chain(
            report=report, output_root=Path(campaign_output_root),
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify autonomous trial journal/report completeness",
    )
    parser.add_argument("attempt_journal")
    parser.add_argument("report_json")
    parser.add_argument("--campaign-output-root")
    args = parser.parse_args(argv)
    try:
        verify_autonomous_trial_files(
            Path(args.attempt_journal),
            Path(args.report_json),
            campaign_output_root=(
                Path(args.campaign_output_root)
                if args.campaign_output_root is not None else None
            ),
        )
    except AutonomousTrialCompletenessError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
