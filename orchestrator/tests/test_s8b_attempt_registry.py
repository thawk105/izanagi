"""Durability and typed-order tests for the 8b attempt adapter."""
from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
import copy
from dataclasses import replace
import hashlib
import inspect
import json
import os
import stat
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.campaign import attempt_registry_core as core  # noqa: E402
from orchestrator.campaign import s8b_attempt_profile as profile8b  # noqa: E402
from orchestrator.campaign import s8b_attempt_registry as registry  # noqa: E402
from orchestrator.campaign import s8b_holdout_admission as admission  # noqa: E402
from orchestrator.campaign import s8b_scheduler_accounting as scheduler  # noqa: E402
from orchestrator.campaign import s8b_floor_stats as floor_stats  # noqa: E402
from orchestrator.campaign import s8b_terminal_evidence as evidence  # noqa: E402
from orchestrator.campaign.s8b_holdout_freeze import (  # noqa: E402
    RMW_KEY,
    RRATIO_KEY,
    SKEW_KEY,
)
from orchestrator.tests import (  # noqa: E402
    test_s8b_holdout_admission as admission_cases,
)


_FREEZE = "1" * 64
_PROTOCOL = "2" * 64
_SCHEDULE = "3" * 64
_RUN_START = "4" * 64
_POLICY = "5" * 64
_EXTERNAL = "6" * 64
_REPORT = "7" * 64
_OBSERVATION = "8" * 64
_ACCOUNTING = "9" * 64
_RECOVERY_AUTHORITY = "adapter-test-scheduler-authority"
_CLASSIFICATION_AUTHORITY = "adapter-test-classification-authority"
_CAMPAIGN_RUN = "adapter-test-run"
_ADMISSION_MANIFEST = "a" * 64
_RUN_RELPATH = f"runs/{_CAMPAIGN_RUN}"
_PROCESS = {
    "pid": 1234,
    "starttime": "adapter-test-starttime",
    "execution_uuid": "adapter-test-execution",
}
_RECOVERER = {
    "pid": 5678,
    "starttime": "adapter-test-recoverer-starttime",
    "execution_uuid": "adapter-test-recoverer-execution",
}
_BINDING = profile8b.S8BAttemptBinding(
    freeze_sha256=_FREEZE,
    protocol_sha256=_PROTOCOL,
    schedule_sha256=_SCHEDULE,
)


def _repo(path: Path) -> Path:
    path.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "-q", str(path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return path


def _profile(*, budget: int = 64) -> core.DomainProfile[Any, Any]:
    return profile8b.make_s8b_domain_profile(
        max_consumptions_per_budget_key=budget,
        recovery_authority_id=_RECOVERY_AUTHORITY,
        recovery_authority_policy_sha256=_POLICY,
    )


def _slot(
    repetition: int = 7,
    attempt_ordinal: int = 0,
    *,
    configuration_id: str = "configuration-a",
) -> profile8b.S8BAttemptSlot:
    identity = {
        "freeze_holdout_key": "holdout-a",
        "configuration_id": configuration_id,
        "repetition": repetition,
        "attempt_ordinal": attempt_ordinal,
    }
    return profile8b.S8BAttemptSlot(
        **identity,
        schedule_row_sha256=hashlib.sha256(
            core.canonical_json_bytes(identity)
        ).hexdigest(),
    )


def _v2_slot(
    repetition: int,
    measurement_ordinal: int = 0,
    attempt_ordinal: int = 0,
    *,
    configuration_id: str = "configuration-a",
) -> profile8b.S8BV2AttemptSlot:
    identity = {
        "freeze_holdout_key": "holdout-a",
        "configuration_id": configuration_id,
        "repetition": repetition,
        "measurement_ordinal": measurement_ordinal,
        "attempt_ordinal": attempt_ordinal,
    }
    return profile8b.S8BV2AttemptSlot(
        **identity,
        schedule_row_sha256=hashlib.sha256(
            core.canonical_json_bytes(identity)
        ).hexdigest(),
    )


def _v2_authority_profile(
    *, budget: int = 10,
) -> core.DomainProfile[Any, Any]:
    return profile8b.make_s8b_v2_domain_profile(
        max_consumptions_per_budget_key=budget,
        recovery_authority_id=scheduler.AUTHORITY_ID,
        recovery_authority_policy_sha256=scheduler.AUTHORITY_POLICY_SHA256,
    )


def _write_v2_generation(
    repo: Path,
    *,
    protocol_sha256: str,
    budget: int = 10,
    start_count: int = 0,
    path_protocol_sha256: str | None = None,
    profile: core.DomainProfile[Any, Any] | None = None,
) -> tuple[
    Path,
    core.DomainProfile[Any, Any],
    profile8b.S8BAttemptBinding,
    core.RegistryRows,
]:
    generation_profile = (
        _v2_authority_profile(budget=budget) if profile is None else profile
    )
    binding = replace(_BINDING, protocol_sha256=protocol_sha256)
    slots = [_v2_slot(index) for index in range(max(1, start_count))]
    rows = core.create_attempt_registry_genesis(
        profile=generation_profile,
        slots=slots,
        binding=binding,
    )
    for slot in slots[:start_count]:
        rows = core.reserve_attempt_slot(
            rows,
            profile=generation_profile,
            freeze_id=_FREEZE,
            slot_id=generation_profile.slot_codec.slot_id(slot),
            binding=binding,
            run_start_receipt_sha256=_RUN_START,
            process_identity=_PROCESS,
            started_at="2026-08-25T00:00:00+00:00",
        )
    path = registry.registry_path(
        repo,
        freeze_sha256=_FREEZE,
        protocol_sha256=(
            protocol_sha256
            if path_protocol_sha256 is None
            else path_protocol_sha256
        ),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_bytes(rows))
    return path, generation_profile, binding, rows


def _bytes(rows: tuple[dict[str, Any], ...]) -> bytes:
    return b"".join(core.canonical_json_bytes(row) + b"\n" for row in rows)


def _create(
    repo: Path,
    profile: core.DomainProfile[Any, Any],
    slots: list[profile8b.S8BAttemptSlot],
) -> Path:
    return registry.create_attempt_registry(
        repo, profile=profile, slots=slots, binding=_BINDING,
    )


def _claim_digest(slot: profile8b.S8BAttemptSlot) -> str:
    return hashlib.sha256(
        core.canonical_json_bytes({
            "freeze_holdout_key": slot.freeze_holdout_key,
            "configuration_id": slot.configuration_id,
        })
    ).hexdigest()


def _attempt_id(slot: profile8b.S8BAttemptSlot) -> str:
    cell_id = f"{slot.freeze_holdout_key}::{slot.configuration_id}"
    return f"{cell_id}::attempt{slot.attempt_ordinal}"


def _reserve(
    repo: Path,
    profile: core.DomainProfile[Any, Any],
    slot: profile8b.S8BAttemptSlot,
    *,
    reader=lambda: b"raw-output",
) -> registry.ReservedAttempt:
    return registry.reserve_attempt_slot(
        repo,
        profile=profile,
        binding=_BINDING,
        slot_id=profile.slot_codec.slot_id(slot),
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-08-25T00:00:00+00:00",
        admission_claim_digest=_claim_digest(slot),
        attempt_id=_attempt_id(slot),
        campaign_run_id=_CAMPAIGN_RUN,
        manifest_sha256=_ADMISSION_MANIFEST,
        run_relpath=_RUN_RELPATH,
        cell_id=f"{slot.freeze_holdout_key}::{slot.configuration_id}",
        deferred_output_reader=reader,
    )


def _v2_registry_capability_case(
    tmp_path: Path,
    *,
    retry_ordinal: int = 0,
) -> tuple[
    dict[str, Any],
    core.DomainProfile[Any, Any],
    profile8b.S8BAttemptBinding,
    profile8b.S8BV2AttemptSlot,
]:
    case = admission_cases._consumed_marker_capability_case(
        tmp_path, retry_ordinal=retry_ordinal,
    )
    marker = case["marker"]
    generation_claim = admission._read_canonical_document(  # noqa: SLF001
        case["claim_path"]
    )
    generation_key = generation_claim["key"]
    assert isinstance(generation_key, Mapping)
    binding = profile8b.S8BAttemptBinding(
        freeze_sha256=str(generation_key["freeze_sha256"]),
        protocol_sha256=str(generation_claim["protocol_sha256"]),
        schedule_sha256=_SCHEDULE,
    )
    identity = {
        "freeze_holdout_key": str(marker["freeze_holdout_key"]),
        "configuration_id": str(marker["configuration_id"]),
        "repetition": int(case["use_kwargs"]["repetition"]),
        "measurement_ordinal": int(
            case["use_kwargs"]["attempt_ordinal"]
        ),
        "attempt_ordinal": 0,
    }
    slot = profile8b.S8BV2AttemptSlot(
        **identity,
        schedule_row_sha256=hashlib.sha256(
            core.canonical_json_bytes(identity)
        ).hexdigest(),
    )
    profile = _v2_authority_profile()
    registry.create_attempt_registry(
        case["repo_root"],
        profile=profile,
        slots=[slot],
        binding=binding,
    )
    return case, profile, binding, slot


def _reserve_v2(
    case: dict[str, Any],
    profile: core.DomainProfile[Any, Any],
    binding: profile8b.S8BAttemptBinding,
    slot: profile8b.S8BV2AttemptSlot,
) -> registry.ReservedAttempt:
    marker = case["marker"]
    root = admission.shared_admission_root(case["repo_root"])
    generation_claim = admission._read_canonical_document(
        admission._measurement_generation_claim_path(
            root, marker["measurement_generation_claim_digest"],
        )
    )
    assert generation_claim["measurement_generation_claim_digest"] == (
        marker["measurement_generation_claim_digest"]
    )
    return registry.reserve_attempt_slot(
        case["repo_root"],
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-08-25T00:00:00+00:00",
        admission_claim_digest=str(
            marker["measurement_generation_claim_digest"]
        ),
        attempt_id=str(marker["attempt_id"]),
        campaign_run_id=str(marker["campaign_run_id"]),
        manifest_sha256=str(marker["manifest_sha256"]),
        run_relpath=str(marker["run_relpath"]),
        cell_id=str(marker["cell_id"]),
        deferred_output_reader=lambda: b"v2-raw-output",
        consumption_marker=case["capability"],
    )


def _sealed_v2_case(
    tmp_path: Path,
    *,
    durable_identity_override: Mapping[str, object] | None = None,
    classification_external_override: str | None = None,
    capture_failure: bool = False,
    retry_ordinal: int = 0,
) -> dict[str, Any]:
    case, profile, binding, slot = _v2_registry_capability_case(
        tmp_path, retry_ordinal=retry_ordinal,
    )
    claim = admission._read_canonical_document(case["claim_path"])
    protocol_path = case["repo_root"] / "output/s8b-freeze/floor_protocol.json"
    protocol = {
        **json.loads(protocol_path.read_text(encoding="utf-8")),
        "session_cv_max": "0.10",
    }
    reps = int(protocol["reps"])
    session_cv_max = str(protocol["session_cv_max"])
    values = [100.0 for _index in range(reps)]
    observations = [
        {
            "rep_index": index,
            "returncode": 0,
            "execution_failure": False,
            "counter_status": "not_required",
            "missing_perf_events": [],
            "perf_raw": {
                event: None for event in floor_stats.PERF_EVENTS
            },
            "throughput": value,
        }
        for index, value in enumerate(values)
    ]
    probe = {"rc": 1, "stdout": "", "stderr": "", "competing": False}
    if capture_failure:
        values = []
        observations = []
    assessment = floor_stats.assess_session(
        values, reps=reps, session_cv_max=session_cv_max,
    )
    record = {
        "attempt_id": case["marker"]["attempt_id"],
        "binary_sha256_at_measure": hashlib.sha256(b"binary").hexdigest(),
        "cell_id": claim["cell_id"],
        "configuration_id": slot.configuration_id,
        "duration_s": 1.25,
        "event": "session",
        "excluded_reason": "launch_failure" if capture_failure else None,
        "exclusion_class": "launch_failure" if capture_failure else None,
        "exec_failures": reps if capture_failure else 0,
        "holdout_id": slot.freeze_holdout_key,
        "kind": "retry" if retry_ordinal else "planned",
        "notes": ["sealed adapter test"],
        "probe_after": dict(probe),
        "probe_before": dict(probe),
        "records": claim["records"],
        "rep_integrity_failures": None if capture_failure else 0,
        "rep_observations": observations,
        "reps_expected": reps,
        "retry": bool(retry_ordinal),
        "retry_ordinal": retry_ordinal or None,
        "round": slot.repetition + 1,
        "run_cmd": ["ycsb_test.exe"],
        "seq": slot.repetition,
        "session_cv": assessment.cv,
        "session_median": None if capture_failure else assessment.median,
        "threads": claim["threads"],
        "throughputs": values,
        "trigger": None,
        "valid": not capture_failure,
        "workload": claim["workload"],
    }
    evidence_mode = claim["mode"]
    if durable_identity_override is not None:
        override = dict(durable_identity_override)
        evidence_mode = override.pop("mode", evidence_mode)
        record.update(override)
    raw_output = profile8b.serialize_session_line(record)
    launcher_origin = registry._new_launcher_origin_capability()
    reserved = registry.reserve_attempt_slot(
        case["repo_root"],
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-09-08T00:00:00+00:00",
        admission_claim_digest=case["marker"][
            "measurement_generation_claim_digest"
        ],
        attempt_id=case["marker"]["attempt_id"],
        campaign_run_id=case["marker"]["campaign_run_id"],
        manifest_sha256=case["marker"]["manifest_sha256"],
        run_relpath=case["marker"]["run_relpath"],
        cell_id=case["marker"]["cell_id"],
        deferred_output_reader=lambda: raw_output,
        launcher_origin_capability=launcher_origin,
        consumption_marker=case["capability"],
    )
    failure = (
        {
            "stage": "capture",
            "exception_type": "OSError",
            "errno": 5,
            "message": "capture unavailable",
        }
        if capture_failure
        else None
    )
    external_evidence_bytes = evidence._pre_output_evidence_bytes(
        probe_before=probe,
        probe_after=probe,
        launch_failures=(),
        failure=failure,
    )
    external_evidence_sha256 = hashlib.sha256(
        external_evidence_bytes
    ).hexdigest()
    classification_extra = {}
    if classification_external_override is None:
        classification_extra["external_evidence_bytes"] = (
            external_evidence_bytes
        )
    classified = registry.classify_attempt(
        reserved,
        pre_observation_failure_reason=(
            "launch_failure" if capture_failure else None
        ),
        authority_id=_CLASSIFICATION_AUTHORITY,
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=(
            external_evidence_sha256
            if classification_external_override is None
            else classification_external_override
        ),
        classified_at="2026-09-08T00:00:01+00:00",
        **classification_extra,
    )
    if capture_failure:
        assert type(classified) is registry.ClassifiedFailure
        observation = registry.begin_classified_failure_observation(classified)
    else:
        assert type(classified) is registry.ClassifiedAttempt
        observation = registry.begin_attempt_observation(classified)
    evidence_slot_id = list(profile.slot_codec.slot_id(slot))
    if durable_identity_override is not None:
        if "holdout_id" in durable_identity_override:
            evidence_slot_id[0] = durable_identity_override["holdout_id"]
        if "configuration_id" in durable_identity_override:
            evidence_slot_id[1] = durable_identity_override[
                "configuration_id"
            ]
        if "retry_ordinal" in durable_identity_override:
            evidence_slot_id[3] = durable_identity_override["retry_ordinal"]
    reservation = SimpleNamespace(
        binding=binding,
        slot_id=tuple(evidence_slot_id),
        protocol=protocol,
        mode=evidence_mode,
        perf_preflight_receipt=None,
        admission_claim_digest=case["marker"][
            "measurement_generation_claim_digest"
        ],
        attempt_id=case["marker"]["attempt_id"],
        campaign_run_id=case["marker"]["campaign_run_id"],
        manifest_sha256=case["marker"]["manifest_sha256"],
        run_relpath=case["marker"]["run_relpath"],
        cell_id=record["cell_id"],
        schedule_row_sha256=slot.schedule_row_sha256,
        records=record["records"],
        threads=record["threads"],
        workload=record["workload"],
    )
    opened = SimpleNamespace(
        measurement=(
            None
            if capture_failure
            else SimpleNamespace(throughputs=values)
        ),
        failure=failure,
        probe_before=probe,
        probe_after=probe,
        launch_failures=(),
        pre_observation_failure_reason=(
            "launch_failure" if capture_failure else None
        ),
        external_evidence_sha256=external_evidence_sha256,
        repetition_evidence=tuple(observations),
        expected_use_perf=False,
        reps_expected=reps,
    )
    terminal = SimpleNamespace(
        raw_output_bytes=raw_output,
        terminal_status=(
            "retryable-failure" if capture_failure else "observed"
        ),
        report_sha256=hashlib.sha256(raw_output).hexdigest(),
        observation_sha256=(
            None
            if capture_failure
            else hashlib.sha256(
                core.canonical_json_bytes(observations)
            ).hexdigest()
        ),
        primary_value=(
            None if capture_failure else float(assessment.median)
        ),
        finished_at="2026-09-08T00:00:02+00:00",
        campaign_record=record,
    )
    reservation_snapshot = evidence._snapshot_reservation_source(
        reservation,
        launcher_origin_capability=launcher_origin,
    )
    opened_snapshot = evidence._snapshot_opened_source(
        reservation_snapshot, opened,
    )
    terminal_snapshot = evidence._snapshot_terminal_source(terminal)
    draft = evidence.seal_terminal_evidence(
        reservation, opened_snapshot, terminal_snapshot,
    )
    return {
        **case,
        "profile": profile,
        "binding": binding,
        "slot": slot,
        "observation": observation,
        "draft": draft,
        "record": record,
        "external_evidence_sha256": external_evidence_sha256,
        "launcher_origin": launcher_origin,
    }


def _two_clean_v2_attempt_case(tmp_path: Path) -> dict[str, Any]:
    (
        repo_root,
        _protocol_document,
        cell,
        admitted,
        first_attempt_id,
        _manifest_sha256,
    ) = admission_cases._issued_cell(tmp_path)
    state = admission._cell_state(admitted)
    schedule_rows = [
        row for row in state.schedule if row["cell_id"] == cell["cell_id"]
    ]
    assert len(schedule_rows) >= 2
    first_schedule = next(
        row
        for row in schedule_rows
        if first_attempt_id == f"{cell['cell_id']}::seq{row['seq']}"
    )
    second_schedule = next(row for row in schedule_rows if row != first_schedule)
    second_attempt_id = f"{cell['cell_id']}::seq{second_schedule['seq']}"
    admission_cases._append_journal_rows(
        admitted,
        {
            "event": "session-start",
            "seq": second_schedule["seq"],
            "round": second_schedule["round"],
            "kind": "planned",
            "cell_id": cell["cell_id"],
            "attempt_id": second_attempt_id,
            "trigger": None,
        },
    )

    attempts = []
    for schedule, attempt_id in (
        (first_schedule, first_attempt_id),
        (second_schedule, second_attempt_id),
    ):
        admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
        marker = admission_cases._floor_expected_marker(admitted, attempt_id)
        capability = admission.validate_floor_attempt_consumption_marker(
            admitted, attempt_id=attempt_id,
        )
        identity = {
            "freeze_holdout_key": marker["freeze_holdout_key"],
            "configuration_id": marker["configuration_id"],
            "repetition": int(schedule["round"]) - 1,
            "measurement_ordinal": 0,
            "attempt_ordinal": 0,
        }
        slot = profile8b.S8BV2AttemptSlot(
            **identity,
            schedule_row_sha256=hashlib.sha256(
                core.canonical_json_bytes(identity)
            ).hexdigest(),
        )
        attempts.append({
            "attempt_id": attempt_id,
            "schedule": schedule,
            "marker": marker,
            "capability": capability,
            "slot": slot,
        })

    root = admission.shared_admission_root(repo_root)
    claim_digest = attempts[0]["marker"][
        "measurement_generation_claim_digest"
    ]
    claim_path = admission._measurement_generation_claim_path(
        root, claim_digest,
    )
    claim = admission._read_canonical_document(claim_path)
    generation_key = claim["key"]
    assert isinstance(generation_key, Mapping)
    binding = profile8b.S8BAttemptBinding(
        freeze_sha256=str(generation_key["freeze_sha256"]),
        protocol_sha256=str(claim["protocol_sha256"]),
        schedule_sha256=_SCHEDULE,
    )
    profile = _v2_authority_profile()
    registry.create_attempt_registry(
        repo_root,
        profile=profile,
        slots=[attempt["slot"] for attempt in attempts],
        binding=binding,
    )
    protocol_path = repo_root / "output/s8b-freeze/floor_protocol.json"
    protocol = {
        **json.loads(protocol_path.read_text(encoding="utf-8")),
        "session_cv_max": "0.10",
    }
    return {
        "repo_root": repo_root,
        "profile": profile,
        "binding": binding,
        "claim": claim,
        "protocol": protocol,
        "attempts": attempts,
    }


def _open_clean_v2_attempt(
    case: Mapping[str, Any], attempt: Mapping[str, Any],
) -> dict[str, Any]:
    profile = case["profile"]
    binding = case["binding"]
    claim = case["claim"]
    protocol = case["protocol"]
    slot = attempt["slot"]
    marker = attempt["marker"]
    schedule = attempt["schedule"]
    reps = int(protocol["reps"])
    values = [100.0 for _index in range(reps)]
    observations = [
        {
            "rep_index": index,
            "returncode": 0,
            "execution_failure": False,
            "counter_status": "not_required",
            "missing_perf_events": [],
            "perf_raw": {event: None for event in floor_stats.PERF_EVENTS},
            "throughput": value,
        }
        for index, value in enumerate(values)
    ]
    probe = {"rc": 1, "stdout": "", "stderr": "", "competing": False}
    assessment = floor_stats.assess_session(
        values,
        reps=reps,
        session_cv_max=str(protocol["session_cv_max"]),
    )
    record = {
        "attempt_id": marker["attempt_id"],
        "binary_sha256_at_measure": hashlib.sha256(b"binary").hexdigest(),
        "cell_id": claim["cell_id"],
        "configuration_id": slot.configuration_id,
        "duration_s": 1.25,
        "event": "session",
        "excluded_reason": None,
        "exclusion_class": None,
        "exec_failures": 0,
        "holdout_id": slot.freeze_holdout_key,
        "kind": "planned",
        "notes": ["two-clean-attempt adapter test"],
        "probe_after": dict(probe),
        "probe_before": dict(probe),
        "records": claim["records"],
        "rep_integrity_failures": 0,
        "rep_observations": observations,
        "reps_expected": reps,
        "retry": False,
        "retry_ordinal": None,
        "round": schedule["round"],
        "run_cmd": ["ycsb_test.exe"],
        "seq": schedule["seq"],
        "session_cv": assessment.cv,
        "session_median": assessment.median,
        "threads": claim["threads"],
        "throughputs": values,
        "trigger": None,
        "valid": True,
        "workload": claim["workload"],
    }
    raw_output = profile8b.serialize_session_line(record)
    launcher_origin = registry._new_launcher_origin_capability()
    reserved = registry.reserve_attempt_slot(
        case["repo_root"],
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-09-09T00:00:00+00:00",
        admission_claim_digest=marker["measurement_generation_claim_digest"],
        attempt_id=marker["attempt_id"],
        campaign_run_id=marker["campaign_run_id"],
        manifest_sha256=marker["manifest_sha256"],
        run_relpath=marker["run_relpath"],
        cell_id=marker["cell_id"],
        deferred_output_reader=lambda: raw_output,
        launcher_origin_capability=launcher_origin,
        consumption_marker=attempt["capability"],
    )
    external_evidence_bytes = evidence._pre_output_evidence_bytes(
        probe_before=probe,
        probe_after=probe,
        launch_failures=(),
        failure=None,
    )
    external_evidence_sha256 = hashlib.sha256(
        external_evidence_bytes
    ).hexdigest()
    classified = registry.classify_attempt(
        reserved,
        pre_observation_failure_reason=None,
        authority_id=_CLASSIFICATION_AUTHORITY,
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=external_evidence_sha256,
        classified_at="2026-09-09T00:00:01+00:00",
        external_evidence_bytes=external_evidence_bytes,
    )
    assert type(classified) is registry.ClassifiedAttempt
    observation = registry.begin_attempt_observation(classified)
    reservation = SimpleNamespace(
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        protocol=protocol,
        mode=claim["mode"],
        perf_preflight_receipt=None,
        admission_claim_digest=marker["measurement_generation_claim_digest"],
        attempt_id=marker["attempt_id"],
        campaign_run_id=marker["campaign_run_id"],
        manifest_sha256=marker["manifest_sha256"],
        run_relpath=marker["run_relpath"],
        cell_id=record["cell_id"],
        schedule_row_sha256=slot.schedule_row_sha256,
        records=record["records"],
        threads=record["threads"],
        workload=record["workload"],
    )
    opened = SimpleNamespace(
        measurement=SimpleNamespace(throughputs=values),
        failure=None,
        probe_before=probe,
        probe_after=probe,
        launch_failures=(),
        pre_observation_failure_reason=None,
        external_evidence_sha256=external_evidence_sha256,
        repetition_evidence=tuple(observations),
        expected_use_perf=False,
        reps_expected=reps,
    )
    terminal = SimpleNamespace(
        raw_output_bytes=raw_output,
        terminal_status="observed",
        report_sha256=hashlib.sha256(raw_output).hexdigest(),
        observation_sha256=hashlib.sha256(
            core.canonical_json_bytes(observations)
        ).hexdigest(),
        primary_value=float(assessment.median),
        finished_at="2026-09-09T00:00:02+00:00",
        campaign_record=record,
    )
    reservation_snapshot = evidence._snapshot_reservation_source(
        reservation,
        launcher_origin_capability=launcher_origin,
    )
    opened_snapshot = evidence._snapshot_opened_source(
        reservation_snapshot, opened,
    )
    draft = evidence.seal_terminal_evidence(
        reservation,
        opened_snapshot,
        evidence._snapshot_terminal_source(terminal),
    )
    return {
        "reserved": reserved,
        "classified": classified,
        "observation": observation,
        "draft": draft,
    }


def _classify(
    reserved: registry.ReservedAttempt,
    *,
    reason: str | None = None,
    external_evidence_sha256: str = _EXTERNAL,
) -> registry.ClassifiedAttempt | registry.ClassifiedFailure:
    return registry.classify_attempt(
        reserved,
        pre_observation_failure_reason=reason,
        authority_id=_CLASSIFICATION_AUTHORITY,
        authority_policy_sha256=_POLICY,
        external_evidence_sha256=external_evidence_sha256,
        classified_at="2026-08-25T00:00:01+00:00",
    )


def _write_marker(repo: Path, slot: profile8b.S8BAttemptSlot) -> Path:
    root = admission.shared_admission_root(repo)
    claim_digest = _claim_digest(slot)
    attempt_id = _attempt_id(slot)
    marker_digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
    path = root / "consumed" / f"{claim_digest}-{marker_digest}.json"
    marker = {
        "schema_version": "s8b-holdout-attempt-consumption/v1",
        "event": "consume",
        "claim_digest": claim_digest,
        "attempt_id": attempt_id,
        "campaign_run_id": _CAMPAIGN_RUN,
        "manifest_sha256": _ADMISSION_MANIFEST,
        "run_relpath": _RUN_RELPATH,
        "cell_id": f"{slot.freeze_holdout_key}::{slot.configuration_id}",
        "freeze_holdout_key": slot.freeze_holdout_key,
        "configuration_id": slot.configuration_id,
        "observation_role": admission.OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    }
    path.write_bytes(core.canonical_json_bytes(marker) + b"\n")
    return path


def _observe(
    repo: Path,
    slot: profile8b.S8BAttemptSlot,
    classified: registry.ClassifiedAttempt,
) -> registry.CapturedObservation:
    _write_marker(repo, slot)
    return registry.begin_attempt_observation(classified)


def _terminal(observation: object) -> None:
    registry.record_attempt_terminal(
        observation,  # type: ignore[arg-type]
        terminal_status="observed",
        report_sha256=_REPORT,
        observation_sha256=_OBSERVATION,
        primary_value={"throughput": 1.0},
        finished_at="2026-08-25T00:00:02+00:00",
    )


def _receipt_file(repo: Path) -> Path:
    root = admission.shared_admission_root(repo)
    directory = root.joinpath(
        *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts
    )
    receipts = [path for path in directory.glob("*.json") if path.is_file()]
    assert len(receipts) == 1
    return receipts[0]


def _claim_file(repo: Path) -> Path:
    directory = _receipt_file(repo).parent / "classification-claims"
    claims = [path for path in directory.glob("*.json") if path.is_file()]
    assert len(claims) == 1
    return claims[0]


def _recovery_receipt_bytes(
    repo: Path,
    profile: core.DomainProfile[Any, Any],
    slot: profile8b.S8BAttemptSlot,
    reason: str,
    *, binding: profile8b.S8BAttemptBinding = _BINDING,
    authority_id: str = _RECOVERY_AUTHORITY, authority_policy_sha256: str = _POLICY,
) -> bytes:
    rows = registry.read_attempt_registry(
        repo, profile=profile, binding=binding,
    )
    starts = [
        row for row in rows
        if row.get("event") == "start"
        and row.get("freeze_holdout_key") == slot.freeze_holdout_key
        and row.get("configuration_id") == slot.configuration_id
        and row.get("repetition") == slot.repetition
        and row.get("attempt_ordinal") == slot.attempt_ordinal
    ]
    assert len(starts) == 1
    receipt = {
        "schema_version": profile8b.S8B_RECOVERY_RECEIPT_SCHEMA_VERSION,
        "event": profile8b.S8B_RECOVERY_RECEIPT_EVENT,
        "source": profile8b.S8B_RECOVERY_RECEIPT_SOURCE,
        "scheduler_request_id": "adapter-test-request",
        "target_start_event_sha256": starts[0]["event_sha256"],
        "raw_scheduler_accounting_record_sha256": _ACCOUNTING,
        "authority_id": authority_id,
        "authority_policy_sha256": authority_policy_sha256,
        "failure_reason": reason,
        "collected_at": "2026-08-25T00:00:03+00:00",
    }
    return core.canonical_json_bytes(receipt) + b"\n"


def test_terminal_rejects_unclassified_handle_and_accepts_full_order(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    reserved = _reserve(repo, profile, slot)

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=r"^\[s8b-attempt-registry-handle\] operation requires exact "
        r"CapturedObservation$",
    ):
        _terminal(reserved)

    classified = _classify(reserved)
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(repo, slot, classified)
    forged = registry.CapturedObservation(captured._state, object())
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="handle private seal differs",
    ):
        _terminal(forged)
    _terminal(captured)
    terminal = registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]
    assert terminal["event"] == "terminal"
    assert terminal["raw_output_sha256"] == hashlib.sha256(
        b"raw-output"
    ).hexdigest()


def test_handle_registry_rejects_constructor_and_replace_forgery(
    tmp_path: Path,
) -> None:
    profile = _profile()
    slot = _slot()

    failure_repo = _repo(tmp_path / "failure")
    _create(failure_repo, profile, [slot])
    failure = _classify(
        _reserve(failure_repo, profile, slot), reason="preflight-failure",
    )
    assert type(failure) is registry.ClassifiedFailure
    _write_marker(failure_repo, slot)
    promoted = registry.ClassifiedAttempt(failure._state, failure._seal)
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="handle was not issued for this attempt phase",
    ):
        registry.begin_attempt_observation(promoted)

    observed_repo = _repo(tmp_path / "observed")
    _create(observed_repo, profile, [slot])
    classified = _classify(_reserve(observed_repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(observed_repo, slot, classified)
    forged_state = replace(captured._state, raw_output_sha256="f" * 64)
    forged = replace(captured, _state=forged_state)
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="handle was not issued for this attempt phase",
    ):
        _terminal(forged)

    _terminal(captured)
    assert registry.read_attempt_registry(
        observed_repo, profile=profile, binding=_BINDING,
    )[-1]["raw_output_sha256"] == hashlib.sha256(b"raw-output").hexdigest()


@pytest.mark.parametrize("tamper", ("missing", "replaced"))
def test_terminal_requires_exact_stored_receipt_and_accepts_restored_bytes(
    tmp_path: Path,
    tamper: str,
) -> None:
    repo = _repo(tmp_path / tamper)
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(repo, slot, classified)
    receipt_path = _receipt_file(repo)
    original = receipt_path.read_bytes()
    if tamper == "missing":
        receipt_path.unlink()
    else:
        changed = dict(__import__("json").loads(original))
        changed["external_evidence_sha256"] = "f" * 64
        receipt_path.write_bytes(core.canonical_json_bytes(changed) + b"\n")

    with pytest.raises(registry.S8BAttemptRegistryError):
        _terminal(captured)

    receipt_path.write_bytes(original)
    _terminal(captured)
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]["event"] == "terminal"


def test_terminal_independently_rejects_changed_cached_receipt_bytes(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(repo, slot, classified)
    receipt_path = _receipt_file(repo)
    durable = receipt_path.read_bytes()
    assert receipt_path.stem == hashlib.sha256(durable).hexdigest()

    changed = dict(json.loads(durable))
    changed["external_evidence_sha256"] = "f" * 64
    changed_bytes = core.canonical_json_bytes(changed) + b"\n"
    forged_state = replace(
        captured._state,
        classification_receipt_bytes=changed_bytes,
    )
    rows = registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="stored classification receipt bytes differ from handle",
    ):
        registry._assert_classification_artifacts(
            root=admission.shared_admission_root(repo),
            rows=rows,
            profile=profile,
            binding=_BINDING,
            slot_id=profile.slot_codec.slot_id(slot),
            admission_claim_digest=forged_state.admission_claim_digest,
            attempt_id=forged_state.attempt_id,
            expected_receipt_bytes=forged_state.classification_receipt_bytes,
        )

    assert receipt_path.read_bytes() == durable
    assert receipt_path.stem == hashlib.sha256(durable).hexdigest()
    _terminal(captured)


def test_slot_classification_claim_allows_exact_retry_and_rejects_new_reason(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    reserved = _reserve(repo, profile, slot)
    first = _classify(reserved)
    after_first = path.read_bytes()
    receipt_path = _receipt_file(repo)
    assert receipt_path.stem == hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    claim_paths = list(
        receipt_path.parent.joinpath("classification-claims").glob("*.json")
    )
    assert len(claim_paths) == 1

    exact_retry = _classify(reserved)
    assert type(first) is type(exact_retry) is registry.ClassifiedAttempt
    assert path.read_bytes() == after_first

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="classification exact retry differs",
    ):
        _classify(reserved, reason="different-reason")
    assert path.read_bytes() == after_first

    failure_repo = _repo(tmp_path / "classified-failure")
    failure_path = _create(failure_repo, profile, [slot])
    failure = _classify(
        _reserve(failure_repo, profile, slot), reason="preflight-failure",
    )
    assert type(failure) is registry.ClassifiedFailure
    _write_marker(failure_repo, slot)
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="operation requires exact ClassifiedAttempt",
    ):
        registry.begin_attempt_observation(failure)  # type: ignore[arg-type]
    assert failure_path.read_bytes().count(b"\n") == 4


def test_mut_t1668_obs_after_preout_digests_actual_output(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    failure = _classify(
        _reserve(repo, profile, slot, reader=lambda: b"actual-failed-output"),
        reason="preflight-failure",
    )
    assert type(failure) is registry.ClassifiedFailure
    _write_marker(repo, slot)

    captured = registry.begin_classified_failure_observation(failure)
    registry.record_attempt_terminal(
        captured,
        terminal_status="terminal-failure",
        report_sha256=_REPORT,
        observation_sha256=None,
        primary_value=None,
        finished_at="2026-08-25T00:00:02+00:00",
    )

    terminal = registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]
    assert terminal["event"] == "terminal"
    assert terminal["raw_output_sha256"] == hashlib.sha256(
        b"actual-failed-output"
    ).hexdigest()
    assert terminal["raw_output_sha256"] != registry._ZERO_OUTPUT_SHA256
    assert terminal["observation_start_event_sha256"] is not None
    assert terminal["failure_reason"] == "preflight-failure"
    assert terminal["pre_observation_failure_reason_echo"] == (
        "preflight-failure"
    )


def test_failure_observation_without_classification_remains_rejected(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    reserved = _reserve(repo, profile, slot)
    _write_marker(repo, slot)
    forged = registry.ClassifiedFailure(reserved._state, reserved._seal)

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="handle was not issued for this attempt phase",
    ):
        registry.begin_classified_failure_observation(forged)
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]["event"] == "pre-observation-seal"


def test_failure_observation_cannot_be_recorded_twice(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    failure = _classify(
        _reserve(repo, profile, slot), reason="preflight-failure",
    )
    assert type(failure) is registry.ClassifiedFailure
    _write_marker(repo, slot)
    registry.begin_classified_failure_observation(failure)

    with pytest.raises(
        core.AttemptRegistryCoreError,
        match="slot already has observation-start",
    ):
        registry.begin_classified_failure_observation(failure)


def test_failure_observation_after_terminal_remains_rejected(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    failure = _classify(
        _reserve(repo, profile, slot), reason="preflight-failure",
    )
    assert type(failure) is registry.ClassifiedFailure
    registry.record_classified_failure_terminal(
        failure,
        terminal_status="terminal-failure",
        report_sha256=None,
        finished_at="2026-08-25T00:00:02+00:00",
    )
    _write_marker(repo, slot)

    with pytest.raises(
        core.AttemptRegistryCoreError,
        match="observation-start follows terminal",
    ):
        registry.begin_classified_failure_observation(failure)


def test_failure_observation_after_recovery_remains_rejected(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    reserved = _reserve(repo, profile, slot)
    failure = _classify(reserved, reason="preflight-failure")
    assert type(failure) is registry.ClassifiedFailure
    registry.record_attempt_recovery(
        reserved,
        scheduler_accounting_receipt=_recovery_receipt_bytes(
            repo, profile, slot, "node_failure",
        ),
        recoverer_process_identity=_RECOVERER,
        recovered_at="2026-08-25T00:00:04+00:00",
    )
    _write_marker(repo, slot)

    with pytest.raises(
        core.AttemptRegistryCoreError,
        match="observation-start follows verified recovery",
    ):
        registry.begin_classified_failure_observation(failure)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        pytest.param(
            "schema_version",
            "s8b-attempt-classification-claim/v999",
            id="schema-version",
        ),
        pytest.param("event", "different-event", id="event"),
        pytest.param(
            "schedule_row_sha256",
            "f" * 64,
            id="schedule-row-sha256",
        ),
    ),
)
def test_observe_rejects_classification_claim_identity_tampering(
    tmp_path: Path,
    field: str,
    replacement: str,
) -> None:
    repo = _repo(tmp_path / field)
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    _write_marker(repo, slot)
    claim_path = _claim_file(repo)
    original = claim_path.read_bytes()
    claim = dict(json.loads(original))
    claim[field] = replacement
    claim_path.write_bytes(core.canonical_json_bytes(claim) + b"\n")

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=rf"^\[s8b-attempt-registry-classification\] "
        rf"classification claim differs: {field}$",
    ):
        registry.begin_attempt_observation(classified)

    claim_path.write_bytes(original)
    captured = registry.begin_attempt_observation(classified)
    assert type(captured) is registry.CapturedObservation


def test_observe_rejects_claim_receipt_digest_mismatch(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    _write_marker(repo, slot)
    claim_path = _claim_file(repo)
    original = claim_path.read_bytes()
    claim = dict(json.loads(original))
    other_digest = hashlib.sha256(b"different-receipt").hexdigest()
    assert other_digest != claim["classification_receipt_sha256"]
    claim["classification_receipt_sha256"] = other_digest
    claim_path.write_bytes(core.canonical_json_bytes(claim) + b"\n")

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=r"^\[s8b-attempt-registry-classification\] classification "
        r"claim cannot reconstruct its receipt digest$",
    ):
        registry.begin_attempt_observation(classified)

    claim_path.write_bytes(original)
    captured = registry.begin_attempt_observation(classified)
    assert type(captured) is registry.CapturedObservation


@pytest.mark.parametrize(
    "mutation",
    (
        pytest.param(
            lambda profile: replace(profile, statuses=profile.statuses + ("other",)),
            id="statuses",
        ),
        pytest.param(
            lambda profile: replace(
                profile, retryable_reasons=frozenset({"other"}),
            ),
            id="retryable-reasons",
        ),
        pytest.param(
            lambda profile: replace(
                profile, slot_codec=profile8b.S8BSlotCodec(),
            ),
            id="slot-codec-identity",
        ),
        pytest.param(
            lambda profile: replace(
                profile, binding_codec=profile8b.S8BBindingCodec(),
            ),
            id="binding-codec-identity",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy,
                    require_previous_terminal=False,
                ),
            ),
            id="require-previous-terminal",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy,
                    forbid_retry_after_observation=False,
                ),
            ),
            id="forbid-retry-after-observation",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy,
                    allow_recovered_abandonment=False,
                ),
            ),
            id="allow-recovered-abandonment",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy, max_series_attempts=2,
                ),
            ),
            id="max-series-attempts",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy,
                    require_terminal_reason_equals_classification=False,
                ),
            ),
            id="terminal-reason-policy",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy,
                    budget_key=lambda slot: slot.repetition,
                ),
            ),
            id="budget-key-identity",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy,
                    retryable_terminal_opens_next_attempt=False,
                ),
            ),
            id="retryable-terminal-opens-next-attempt",
        ),
        pytest.param(
            lambda profile: replace(
                profile, terminal_row_validator=lambda _row: None,
            ),
            id="terminal-row-validator-identity",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                recovery_policy=replace(
                    profile.recovery_policy,
                    receipt_schema_version="scheduler-accounting-receipt/v2",
                ),
            ),
            id="recovery-schema",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                recovery_policy=replace(
                    profile.recovery_policy, receipt_source="other-source",
                ),
            ),
            id="recovery-source",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                recovery_policy=replace(
                    profile.recovery_policy,
                    failure_reasons=frozenset({"node_failure"}),
                ),
            ),
            id="recovery-reasons",
        ),
        pytest.param(
            lambda profile: replace(
                profile,
                freeze_id_from_genesis=lambda row: row["freeze_sha256"],
            ),
            id="freeze-identity-function",
        ),
    ),
)
def test_adapter_rejects_every_mutable_frozen_profile_surface(
    tmp_path: Path,
    mutation: Any,
) -> None:
    profile = mutation(_profile())
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="domain profile differs from frozen 8b semantics",
    ):
        _create(_repo(tmp_path / "repo"), profile, [_slot()])


def test_adapter_rejects_hostile_profile_field_comparison_protocol() -> None:
    class AcceptAllStatuses:
        def __eq__(self, other: object) -> bool:
            return True

        def __ne__(self, other: object) -> bool:
            return False

        def __contains__(self, item: object) -> bool:
            return True

    forged = replace(_profile(), statuses=AcceptAllStatuses())
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="domain profile differs from frozen 8b semantics",
    ):
        registry._assert_profile(forged)


def test_adapter_allows_only_budget_and_recovery_authority_values_to_vary(
    tmp_path: Path,
) -> None:
    for name, budget, authority, policy in (
        ("first", 1, "authority-first", "a" * 64),
        ("second", 97, "authority-second", "b" * 64),
    ):
        profile = profile8b.make_s8b_domain_profile(
            max_consumptions_per_budget_key=budget,
            recovery_authority_id=authority,
            recovery_authority_policy_sha256=policy,
        )
        path = _create(_repo(tmp_path / name), profile, [_slot()])
        assert path.is_file()


@pytest.mark.parametrize(
    ("reason", "accepted"),
    (
        pytest.param("wall_timeout", False, id="closed-set-negative"),
        pytest.param("node_failure", True, id="node-failure-positive"),
        pytest.param(
            "scheduler_external_interruption",
            True,
            id="scheduler-interruption-positive",
        ),
    ),
)
def test_recovery_uses_canonical_receipt_reason_without_normalization(
    tmp_path: Path,
    reason: str,
    accepted: bool,
) -> None:
    repo = _repo(tmp_path / reason)
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    reserved = _reserve(repo, profile, slot)
    receipt = _recovery_receipt_bytes(repo, profile, slot, reason)

    if not accepted:
        with pytest.raises(
            core.AttemptRegistryCoreError,
            match="failure_reason is outside the exact closed set",
        ):
            registry.record_attempt_recovery(
                reserved,
                scheduler_accounting_receipt=receipt,
                recoverer_process_identity=_RECOVERER,
                recovered_at="2026-08-25T00:00:04+00:00",
            )
        assert registry.read_attempt_registry(
            repo, profile=profile, binding=_BINDING,
        )[-1]["event"] == "pre-observation-seal"
    else:
        registry.record_attempt_recovery(
            reserved,
            scheduler_accounting_receipt=receipt,
            recoverer_process_identity=_RECOVERER,
            recovered_at="2026-08-25T00:00:04+00:00",
        )
        row = registry.read_attempt_registry(
            repo, profile=profile, binding=_BINDING,
        )[-1]
        assert row["event"] == "recovery"
        assert row["failure_reason"] == reason
        assert row["scheduler_accounting_receipt"]["failure_reason"] == reason

    assert "failure_reason" not in inspect.signature(
        registry.record_attempt_recovery
    ).parameters


def test_observe_rejects_absent_consumed_marker_then_accepts_marker(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="durable file is absent",
    ):
        registry.begin_attempt_observation(classified)

    _write_marker(repo, slot)
    captured = registry.begin_attempt_observation(classified)
    assert type(captured) is registry.CapturedObservation


def test_marker_without_attempt_ledger_authorizes_observe(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    _write_marker(repo, slot)
    attempt_ledger = admission.shared_admission_root(repo) / "attempt-ledger.jsonl"
    assert not attempt_ledger.exists()

    captured = registry.begin_attempt_observation(classified)
    assert type(captured) is registry.CapturedObservation
    assert not attempt_ledger.exists()


def test_observe_rejects_consumed_marker_extra_key(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    marker_path = _write_marker(repo, slot)
    original = marker_path.read_bytes()
    marker = dict(json.loads(original))
    marker["unexpected_key"] = "unexpected-value"
    marker_path.write_bytes(core.canonical_json_bytes(marker) + b"\n")

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=r"^\[s8b-attempt-registry-consume\] "
        r"consumed marker exact keys differ$",
    ):
        registry.begin_attempt_observation(classified)

    marker_path.write_bytes(original)
    captured = registry.begin_attempt_observation(classified)
    assert type(captured) is registry.CapturedObservation


@pytest.mark.parametrize(
    "tamper",
    (
        "missing-key",
        "schema-version",
        "different-campaign",
        "different-run",
        "different-manifest",
        "different-cell",
    ),
)
def test_observe_requires_exact_consumed_marker_contract(
    tmp_path: Path,
    tamper: str,
) -> None:
    repo = _repo(tmp_path / tamper)
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    marker_path = _write_marker(repo, slot)
    original = marker_path.read_bytes()
    marker = dict(json.loads(original))
    if tamper == "missing-key":
        marker.pop("manifest_sha256")
    elif tamper == "schema-version":
        marker["schema_version"] = "s8b-holdout-attempt-consumption/v2"
    elif tamper == "different-campaign":
        marker["campaign_run_id"] = "different-run"
    elif tamper == "different-run":
        marker["run_relpath"] = "runs/different-run"
    elif tamper == "different-manifest":
        marker["manifest_sha256"] = "b" * 64
    else:
        marker["cell_id"] = "holdout-other::configuration-other"
    marker_path.write_bytes(core.canonical_json_bytes(marker) + b"\n")

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="consumed marker",
    ):
        registry.begin_attempt_observation(classified)

    marker_path.write_bytes(original)
    captured = registry.begin_attempt_observation(classified)
    assert type(captured) is registry.CapturedObservation


def test_genesis_is_create_only_and_rejects_alternate_or_symlinked_paths(
    tmp_path: Path,
) -> None:
    profile = _profile()
    slot = _slot()
    repo = _repo(tmp_path / "second")
    canonical = _create(repo, profile, [slot])
    shared_root = admission.shared_admission_root(repo)
    relative = profile8b.S8B_REGISTRY_LAYOUT.registry_path.as_posix().format(
        freeze_sha256=_FREEZE
    )
    assert canonical == shared_root.joinpath(*Path(relative).parts)
    assert (shared_root / "ledger.lock").is_file()
    with pytest.raises(registry.S8BAttemptRegistryError):
        _create(repo, profile, [slot])
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="alternate registry path is forbidden",
    ):
        registry.create_attempt_registry(
            repo,
            profile=profile,
            slots=[slot],
            binding=_BINDING,
            requested_registry_path=canonical.with_name("alternate.jsonl"),
        )

    parent_repo = _repo(tmp_path / "parent-symlink")
    parent_path = registry.registry_path(parent_repo, freeze_sha256=_FREEZE)
    parent_path.parent.parent.mkdir(parents=True, exist_ok=True)
    symlink_target = tmp_path / "outside-parent"
    symlink_target.mkdir()
    parent_path.parent.symlink_to(symlink_target, target_is_directory=True)
    with pytest.raises(
        (registry.S8BAttemptRegistryError, admission.HoldoutAdmissionError),
        match="symlink",
    ):
        _create(parent_repo, profile, [slot])

    destination_repo = _repo(tmp_path / "destination-symlink")
    destination = registry.registry_path(
        destination_repo, freeze_sha256=_FREEZE,
    )
    destination.parent.mkdir(parents=True)
    target = tmp_path / "outside-registry"
    target.write_bytes(b"do-not-touch\n")
    destination.symlink_to(target)
    with pytest.raises(registry.S8BAttemptRegistryError):
        _create(destination_repo, profile, [slot])
    assert target.read_bytes() == b"do-not-touch\n"


def test_relative_repo_root_is_canonicalized_before_handle_is_issued(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    monkeypatch.chdir(repo)
    reserved = _reserve(Path("."), profile, slot)
    assert reserved._state.repo_root == repo.resolve()

    monkeypatch.chdir(tmp_path)
    classified = _classify(reserved)
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(repo, slot, classified)
    _terminal(captured)
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]["event"] == "terminal"


def test_resume_classification_and_incomplete_reader_add_no_rows(
    tmp_path: Path,
) -> None:
    profile = _profile()
    slot = _slot()

    classified_repo = _repo(tmp_path / "classified")
    classified_path = _create(classified_repo, profile, [slot])
    _classify(_reserve(classified_repo, profile, slot))
    before_classified_resume = classified_path.read_bytes()
    resumed = registry.resume_attempt(
        classified_repo,
        profile=profile,
        binding=_BINDING,
        slot_id=profile.slot_codec.slot_id(slot),
        deferred_output_reader=lambda: b"resumed-output",
    )
    assert type(resumed) is registry.ClassifiedAttempt
    assert classified_path.read_bytes() == before_classified_resume

    observed_repo = _repo(tmp_path / "observed")
    observed_path = _create(observed_repo, profile, [slot])

    def incomplete_reader() -> bytes:
        raise RuntimeError("reader-incomplete")

    classified = _classify(
        _reserve(observed_repo, profile, slot, reader=incomplete_reader)
    )
    assert type(classified) is registry.ClassifiedAttempt
    _write_marker(observed_repo, slot)
    with pytest.raises(RuntimeError, match="reader-incomplete"):
        registry.begin_attempt_observation(classified)
    before_observed_resume = observed_path.read_bytes()
    assert registry.read_attempt_registry(
        observed_repo, profile=profile, binding=_BINDING,
    )[-1]["event"] == "observation-start"

    captured = registry.resume_attempt(
        observed_repo,
        profile=profile,
        binding=_BINDING,
        slot_id=profile.slot_codec.slot_id(slot),
        deferred_output_reader=lambda: b"resumed-output",
    )
    assert type(captured) is registry.CapturedObservation
    assert observed_path.read_bytes() == before_observed_resume


def test_resume_start_and_seal_without_old_handle_reaches_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])

    class InjectedCrash(RuntimeError):
        pass

    def crash_after_durable_reservation(point: str) -> None:
        if point == "after-parent-fsync":
            raise InjectedCrash(point)

    monkeypatch.setattr(
        registry, "_FAULT_HOOK", crash_after_durable_reservation,
    )
    with pytest.raises(InjectedCrash, match="after-parent-fsync"):
        _reserve(repo, profile, slot)
    monkeypatch.setattr(registry, "_FAULT_HOOK", None)
    after_reservation = path.read_bytes()
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]["event"] == "pre-observation-seal"

    resumed = registry.resume_attempt(
        repo,
        profile=profile,
        binding=_BINDING,
        slot_id=profile.slot_codec.slot_id(slot),
        deferred_output_reader=lambda: b"resumed-output",
        admission_claim_digest=_claim_digest(slot),
        attempt_id=_attempt_id(slot),
        campaign_run_id=_CAMPAIGN_RUN,
        manifest_sha256=_ADMISSION_MANIFEST,
        run_relpath=_RUN_RELPATH,
        cell_id=f"{slot.freeze_holdout_key}::{slot.configuration_id}",
    )
    assert type(resumed) is registry.ReservedAttempt
    assert path.read_bytes() == after_reservation

    classified = _classify(resumed)
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(repo, slot, classified)
    _terminal(captured)
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]["event"] == "terminal"


def test_atomic_update_fault_points_leave_only_old_or_new_complete_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    points = tuple(registry.ATOMIC_UPDATE_FAULT_POINTS)
    assert points == (
        "after-authoritative-read",
        "after-replay",
        "after-transition",
        "after-candidate-validation",
        "after-staging-fsync",
        "after-replace",
        "after-parent-fsync",
    )
    assert points
    fired = {point: 0 for point in points}

    class InjectedCrash(RuntimeError):
        pass

    for point in points:
        repo = _repo(tmp_path / point)
        profile = _profile()
        slot = _slot()
        path = _create(repo, profile, [slot])
        old_bytes = path.read_bytes()
        old_rows = core.load_attempt_registry(old_bytes, profile=profile)
        expected_rows = core.reserve_attempt_slot(
            old_rows,
            profile=profile,
            freeze_id=_FREEZE,
            slot_id=profile.slot_codec.slot_id(slot),
            binding=_BINDING,
            run_start_receipt_sha256=_RUN_START,
            process_identity=_PROCESS,
            started_at="2026-08-25T00:00:00+00:00",
        )
        new_bytes = _bytes(expected_rows)

        def fault_hook(actual: str, *, selected: str = point) -> None:
            if actual == selected:
                fired[selected] += 1
                raise InjectedCrash(selected)

        monkeypatch.setattr(registry, "_FAULT_HOOK", fault_hook)
        with pytest.raises(InjectedCrash, match=point):
            _reserve(repo, profile, slot)
        monkeypatch.setattr(registry, "_FAULT_HOOK", None)

        authoritative = path.read_bytes()
        assert authoritative in {old_bytes, new_bytes}
        assert authoritative.endswith(b"\n")
        core.load_attempt_registry(
            authoritative, profile=profile, expected_binding=_BINDING,
        )
        assert not list(path.parent.glob(f".{path.name}.staging-*"))

    assert fired == {point: 1 for point in points}


@pytest.mark.parametrize("fault", ("write", "fsync"))
def test_guarded_writer_internal_fault_removes_partial_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    repo = _repo(tmp_path / fault)
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    old_bytes = path.read_bytes()
    original_write = os.write
    original_fsync = os.fsync
    injected = 0

    if fault == "write":
        def failing_write(fd: int, payload: object) -> int:
            nonlocal injected
            if injected == 0:
                injected += 1
                view = memoryview(payload)  # type: ignore[arg-type]
                return original_write(fd, view[:max(1, len(view) // 2)])
            if injected == 1:
                injected += 1
                raise OSError("injected guarded write failure")
            return original_write(fd, payload)  # type: ignore[arg-type]

        monkeypatch.setattr(admission.os, "write", failing_write)
    else:
        def failing_fsync(fd: int) -> None:
            nonlocal injected
            if injected == 0 and stat.S_ISREG(os.fstat(fd).st_mode):
                injected += 1
                raise OSError("injected guarded fsync failure")
            original_fsync(fd)

        monkeypatch.setattr(admission.os, "fsync", failing_fsync)

    with pytest.raises(OSError, match=f"injected guarded {fault} failure"):
        _reserve(repo, profile, slot)

    assert injected >= 1
    assert path.read_bytes() == old_bytes
    assert not list(path.parent.glob(f".{path.name}.staging-*"))
    monkeypatch.setattr(admission.os, "write", original_write)
    monkeypatch.setattr(admission.os, "fsync", original_fsync)
    assert type(_reserve(repo, profile, slot)) is registry.ReservedAttempt


def test_new_registry_directories_fsync_each_parent_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    root = admission.shared_admission_root(repo)
    common = repo / ".git"
    shared_parent = root.parent
    first = root / "floor-attempt-registries"
    leaf = first / _FREEZE
    assert not shared_parent.exists()
    assert not first.exists()
    calls: list[Path] = []
    real_fsync_directory = registry._fsync_directory

    def recording_fsync(path: Path) -> None:
        calls.append(path)
        real_fsync_directory(path)

    monkeypatch.setattr(registry, "_fsync_directory", recording_fsync)
    _create(repo, profile, [slot])
    assert calls[:7] == [
        common,
        shared_parent,
        root,
        first,
        root,
        leaf,
        first,
    ]


def test_classification_publish_faults_pin_slot_claim_before_exact_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    points = tuple(registry.CLASSIFICATION_PUBLISH_FAULT_POINTS)
    assert points == (
        "after-classification-claim",
        "after-classification-receipt",
    )
    assert points
    fired = {point: 0 for point in points}

    class InjectedCrash(RuntimeError):
        pass

    for point in points:
        repo = _repo(tmp_path / point)
        profile = _profile()
        slot = _slot()
        path = _create(repo, profile, [slot])
        reserved = _reserve(repo, profile, slot)
        old_bytes = path.read_bytes()

        def fault_hook(actual: str, *, selected: str = point) -> None:
            if actual == selected:
                fired[selected] += 1
                raise InjectedCrash(selected)

        monkeypatch.setattr(registry, "_FAULT_HOOK", fault_hook)
        with pytest.raises(InjectedCrash, match=point):
            _classify(reserved)
        monkeypatch.setattr(registry, "_FAULT_HOOK", None)
        assert path.read_bytes() == old_bytes
        receipt_root = admission.shared_admission_root(repo).joinpath(
            *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts
        )
        claim_paths = list(
            receipt_root.joinpath("classification-claims").glob("*.json")
        )
        assert len(claim_paths) == 1
        claim = json.loads(claim_paths[0].read_bytes())
        embedded_receipt = (
            core.canonical_json_bytes(claim["classification_receipt"]) + b"\n"
        )
        assert hashlib.sha256(embedded_receipt).hexdigest() == (
            claim["classification_receipt_sha256"]
        )
        receipt_files = [
            candidate for candidate in receipt_root.glob("*.json")
            if candidate.is_file()
        ]
        assert len(receipt_files) == (
            0 if point == "after-classification-claim" else 1
        )

        with pytest.raises(
            registry.S8BAttemptRegistryError,
            match="durable destination already exists",
        ):
            _classify(reserved, reason="replacement-reason")
        assert path.read_bytes() == old_bytes
        del reserved

        exact = registry.resume_attempt(
            repo,
            profile=profile,
            binding=_BINDING,
            slot_id=profile.slot_codec.slot_id(slot),
            deferred_output_reader=lambda: b"resumed-output",
        )
        assert type(exact) is registry.ClassifiedAttempt
        assert path.read_bytes() != old_bytes
        assert path.read_bytes().count(b"\n") == old_bytes.count(b"\n") + 1
        core.load_attempt_registry(
            path.read_bytes(), profile=profile, expected_binding=_BINDING,
        )
        captured = _observe(repo, slot, exact)
        _terminal(captured)
        assert registry.read_attempt_registry(
            repo, profile=profile, binding=_BINDING,
        )[-1]["event"] == "terminal"

    assert fired == {point: 1 for point in points}


def test_classification_preflights_claim_receipt_and_registry_before_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    reserved = _reserve(repo, profile, slot)
    old_bytes = path.read_bytes()
    seen: list[str] = []
    real_gate = admission.assert_holdout_safe_bytes

    def reject_candidate(logical_name: str, payload: bytes) -> None:
        seen.append(logical_name)
        real_gate(logical_name, payload)
        if logical_name.endswith("registry.jsonl"):
            raise admission.HoldoutAdmissionError(
                "injected candidate registry contamination"
            )

    monkeypatch.setattr(
        admission, "assert_holdout_safe_bytes", reject_candidate,
    )
    with pytest.raises(
        admission.HoldoutAdmissionError,
        match="injected candidate registry contamination",
    ):
        _classify(reserved)

    assert seen[:3] == [
        next(name for name in seen if "classification-claims" in name),
        next(
            name for name in seen
            if "floor-attempt-registry-receipts" in name
            and "classification-claims" not in name
        ),
        next(name for name in seen if name.endswith("registry.jsonl")),
    ]
    assert path.read_bytes() == old_bytes
    receipt_root = admission.shared_admission_root(repo).joinpath(
        *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts
    )
    assert not receipt_root.exists()


def test_real_holdout_scanner_rejection_leaves_no_classification_claim(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "unsafe")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    reserved = _reserve(repo, profile, slot)
    old_bytes = path.read_bytes()
    contaminated = f"{RRATIO_KEY}=80 {SKEW_KEY}=0.9 {RMW_KEY}=0"

    with pytest.raises(
        admission.HoldoutAdmissionError,
        match="holdout conjunction contamination",
    ):
        _classify(reserved, reason=contaminated)

    assert path.read_bytes() == old_bytes
    receipt_root = admission.shared_admission_root(repo).joinpath(
        *profile8b.S8B_REGISTRY_LAYOUT.classification_receipt_dir.parts
    )
    assert not receipt_root.exists()

    safe_repo = _repo(tmp_path / "safe")
    safe_slot = _slot(configuration_id="configuration-safe")
    _create(safe_repo, profile, [safe_slot])
    safe = _classify(_reserve(safe_repo, profile, safe_slot))
    assert type(safe) is registry.ClassifiedAttempt
    assert _receipt_file(safe_repo).is_file()


def test_root_lock_serializes_two_updates_after_same_old_snapshot_barrier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    old = path.read_bytes()
    barrier = threading.Barrier(2, timeout=10)
    snapshots: list[bytes] = []
    snapshots_lock = threading.Lock()

    def snapshot_hook(snapshot: bytes) -> None:
        with snapshots_lock:
            snapshots.append(snapshot)
        barrier.wait()

    monkeypatch.setattr(registry, "_PRELOCK_SNAPSHOT_HOOK", snapshot_hook)

    def worker() -> object:
        try:
            return _reserve(repo, profile, slot)
        except Exception as exc:  # the losing core transition must reject
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: worker(), range(2)))

    accepted = [value for value in results if type(value) is registry.ReservedAttempt]
    rejected = [value for value in results if isinstance(value, Exception)]
    assert len(accepted) == len(rejected) == 1
    assert len(snapshots) == 2
    assert snapshots[0] == snapshots[1] == old
    rows = registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )
    assert sum(row.get("event") == "start" for row in rows) == 1


def test_start_row_never_claims_admission_consumption(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    _reserve(repo, profile, slot)
    rows = registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )
    starts = [row for row in rows if row.get("event") == "start"]
    assert len(starts) == 1
    assert frozenset(starts[0]).isdisjoint({
        "claim_digest",
        "admission_claim_digest",
        "attempt_id",
        "consume",
        "consumed",
        "attempt_ledger_row",
    })


def _assert_production_source_has_no_attempt_adapter(source: str) -> None:
    tree = ast.parse(source)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            violations.extend(
                alias.name for alias in node.names
                if alias.name.endswith("s8b_attempt_registry")
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.endswith("s8b_attempt_registry"):
                violations.append(module)
            violations.extend(
                alias.name for alias in node.names
                if alias.name == "s8b_attempt_registry"
            )
        elif isinstance(node, ast.Name) and node.id == "s8b_attempt_registry":
            violations.append(node.id)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "s8b_attempt_registry" in node.value
        ):
            violations.append(node.value)
    if violations:
        raise AssertionError(
            f"production source imports attempt adapter: {sorted(violations)}"
        )


def test_floor_campaign_does_not_import_adapter_and_guard_has_positive_control(
) -> None:
    campaign_root = Path(__file__).parents[1] / "campaign"
    sources = [
        (campaign_root / name).read_text(encoding="utf-8")
        for name in ("s8b_floor_campaign.py", "s8b_holdout_admission.py")
    ]
    for source in sources:
        _assert_production_source_has_no_attempt_adapter(source)

    synthetic = "from . import s8b_attempt_registry\n" + sources[0]
    with pytest.raises(
        AssertionError,
        match="production source imports attempt adapter",
    ):
        _assert_production_source_has_no_attempt_adapter(synthetic)


def _assert_adapter_has_no_repetition_derivation(source: str) -> None:
    tree = ast.parse(source)
    violations: list[str] = []
    if any(
        isinstance(node, ast.Call)
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id == "S8BAttemptSlot"
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "S8BAttemptSlot"
            )
        )
        for node in ast.walk(tree)
    ):
        violations.append("slot-construction")
    if any(
        isinstance(node, ast.Call)
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id == "replace"
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "replace"
            )
        )
        and any(keyword.arg == "repetition" for keyword in node.keywords)
        for node in ast.walk(tree)
    ):
        violations.append("replace")
    if any(
        argument.arg == "round"
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
    ):
        violations.append("round-argument")

    repetition_values: list[ast.expr] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            repetition_values.extend(
                value for key, value in zip(node.keys, node.values, strict=True)
                if isinstance(key, ast.Constant) and key.value == "repetition"
            )
        elif isinstance(node, ast.Call):
            repetition_values.extend(
                keyword.value for keyword in node.keywords
                if keyword.arg == "repetition"
            )
            if isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Name,
            ) and node.func.value.id == "core":
                for keyword in node.keywords:
                    if keyword.arg != "slot_id":
                        continue
                    value = keyword.value
                    if not (
                        isinstance(value, ast.Name) and value.id == "slot_id"
                        or isinstance(value, ast.Attribute)
                        and isinstance(value.value, ast.Name)
                        and value.value.id == "state"
                        and value.attr == "slot_id"
                    ):
                        violations.append("core-slot-id")
    for value in repetition_values:
        direct = (
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id == "slot"
            and value.attr == "repetition"
        )
        if (
            not direct
            or any(isinstance(child, ast.Subscript) for child in ast.walk(value))
        ):
            violations.append("repetition-sink")
    if violations:
        raise AssertionError(f"adapter derives repetition: {sorted(set(violations))}")


def test_repetition_derivation_guard_rejects_all_known_mapping_forms() -> None:
    unsafe_sources = (
        "def f(slot):\n return {'repetition': slot.repetition + 1}\n",
        "TABLE = (3, 19, 41)\ndef f(slot):\n return {'repetition': TABLE[0]}\n",
        "TABLE = {3: 19}\ndef f(slot):\n return {'repetition': TABLE[slot.repetition]}\n",
        "def f(slot):\n for index, value in enumerate((slot,)):\n  return {'repetition': index}\n",
        "def f(slot):\n return replace(slot, repetition=3)\n",
        "import dataclasses\ndef f(slot):\n return dataclasses.replace(slot, repetition=3)\n",
    )
    for source in unsafe_sources:
        with pytest.raises(AssertionError, match="adapter derives repetition"):
            _assert_adapter_has_no_repetition_derivation(source)


def test_adapter_preserves_caller_repetition_without_derivation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinels = (3, 19, 104729)
    profile = _profile()
    observed: dict[str, list[int]] = {
        name: [] for name in (
            "capability_digest",
            "reserve_attempt_slot",
            "classify_attempt",
            "begin_attempt_observation",
            "record_attempt_terminal",
        )
    }

    for name in observed:
        original = getattr(core, name)

        def wrapper(*args: object, _name: str = name,
                    _original: Any = original, **kwargs: object) -> object:
            if "slot" in kwargs:
                repetition = kwargs["slot"].repetition  # type: ignore[union-attr]
            else:
                repetition = kwargs["slot_id"][2]  # type: ignore[index]
            observed[_name].append(repetition)
            return _original(*args, **kwargs)

        monkeypatch.setattr(core, name, wrapper)

    for sentinel in sentinels:
        repo = _repo(tmp_path / str(sentinel))
        slot = _slot(
            repetition=sentinel,
            configuration_id=f"configuration-{sentinel}",
        )
        _create(repo, profile, [slot])
        classified = _classify(_reserve(repo, profile, slot))
        assert type(classified) is registry.ClassifiedAttempt
        captured = _observe(repo, slot, classified)
        _terminal(captured)

        receipt_path = _receipt_file(repo)
        claim_paths = list(
            receipt_path.parent.joinpath("classification-claims").glob("*.json")
        )
        assert len(claim_paths) == 1
        assert json.loads(claim_paths[0].read_bytes())["repetition"] == sentinel
        rows = registry.read_attempt_registry(
            repo, profile=profile, binding=_BINDING,
        )
        assert rows[0]["slots"][0]["repetition"] == sentinel
        assert {
            row["repetition"] for row in rows[1:]
        } == {sentinel}

    for values in observed.values():
        assert set(values) == set(sentinels)
    source = Path(registry.__file__).read_text(encoding="utf-8")
    _assert_adapter_has_no_repetition_derivation(source)


def test_registry_path_adds_optional_protocol_generation_without_changing_v1(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    root = admission.shared_admission_root(repo)
    canonical = registry.registry_path(repo, freeze_sha256=_FREEZE)
    generated = registry.registry_path(
        repo,
        freeze_sha256=_FREEZE,
        protocol_sha256=_PROTOCOL,
    )
    assert canonical == (
        root / "floor-attempt-registries" / _FREEZE / "registry.jsonl"
    )
    assert generated == (
        root
        / "floor-attempt-registries"
        / _FREEZE
        / _PROTOCOL
        / "registry.jsonl"
    )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=r"^\[s8b-attempt-registry-schema\] protocol_sha256 is not a SHA-256 digest$",
    ):
        registry.registry_path(
            repo,
            freeze_sha256=_FREEZE,
            protocol_sha256="not-a-digest",
        )
    assert registry.registry_path(repo, freeze_sha256=_FREEZE) == canonical


def test_canonical_v1_lifecycle_ignores_non_generation_sibling(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    sibling = path.parent / "consumption-catalog.jsonl"
    sibling.write_bytes(b'{"event": "catalog"}\n')
    root = admission.shared_admission_root(repo)
    with admission._locked(root):
        assert registry._registry_generation_paths_locked(root, _FREEZE) == (
            path,
        )

    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(repo, slot, classified)
    _terminal(captured)
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]["event"] == "terminal"


@pytest.mark.parametrize(
    "unsafe_kind",
    ["directory-symlink", "non-directory", "missing-registry", "registry-symlink"],
)
def test_generation_enumerator_rejects_unsafe_hex_authority_and_accepts_real_one(
    tmp_path: Path,
    unsafe_kind: str,
) -> None:
    repo = _repo(tmp_path / unsafe_kind)
    profile = _profile()
    slot = _slot()
    canonical = _create(repo, profile, [slot])
    root = admission.shared_admission_root(repo)
    protocol = "a" * 64
    generation = canonical.parent / protocol
    outside = tmp_path / f"outside-{unsafe_kind}"

    if unsafe_kind == "directory-symlink":
        outside.mkdir()
        generation.symlink_to(outside, target_is_directory=True)
    elif unsafe_kind == "non-directory":
        generation.write_bytes(b"not-a-directory\n")
    else:
        generation.mkdir()
        if unsafe_kind == "registry-symlink":
            outside.write_bytes(b"not-a-registry\n")
            (generation / "registry.jsonl").symlink_to(outside)

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=(
            "generation directory is unsafe or incomplete"
            if unsafe_kind != "registry-symlink"
            else "durable path is not a regular file: registry.jsonl"
        ),
    ):
        _reserve(repo, profile, slot)

    if generation.is_symlink() or generation.is_file():
        generation.unlink()
    else:
        registry_file = generation / "registry.jsonl"
        if registry_file.is_symlink():
            registry_file.unlink()
    _write_v2_generation(repo, protocol_sha256=protocol)
    with admission._locked(root):
        assert registry._registry_generation_paths_locked(root, _FREEZE) == (
            canonical,
            generation / "registry.jsonl",
        )
    assert type(_reserve(repo, profile, slot)) is registry.ReservedAttempt


def _assert_complete_generation_symlink_rejected(
    *,
    root: Path,
    generation_directory: Path,
) -> None:
    with admission._locked(root):
        try:
            registry._registry_generation_paths_locked(root, _FREEZE)
        except registry.S8BAttemptRegistryError as exc:
            assert str(exc) == (
                "[s8b-attempt-registry-storage] "
                "generation directory is unsafe or incomplete"
            )
        except admission.HoldoutAdmissionError as exc:
            assert str(exc) == (
                f"guarded writer path is symlinked: {generation_directory}"
            )
        else:
            pytest.fail("complete generation directory symlink was enumerated")


def test_complete_generation_directory_symlink_is_rejected_but_real_directory_mutates(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    canonical = _create(repo, profile, [slot])
    protocol = "a" * 64
    generation, _generation_profile, _binding, rows = _write_v2_generation(
        repo,
        protocol_sha256=protocol,
        start_count=1,
    )
    generation_directory = generation.parent
    complete_target = tmp_path / "complete-generation-target"
    generation_directory.rename(complete_target)
    generation_directory.symlink_to(complete_target, target_is_directory=True)
    assert (complete_target / "registry.jsonl").read_bytes() == _bytes(rows)

    root = admission.shared_admission_root(repo)
    _assert_complete_generation_symlink_rejected(
        root=root,
        generation_directory=generation_directory,
    )

    generation_directory.unlink()
    complete_target.rename(generation_directory)
    assert generation.read_bytes() == _bytes(rows)
    with admission._locked(root):
        assert registry._registry_generation_paths_locked(root, _FREEZE) == (
            canonical,
            generation,
        )
    assert type(_reserve(repo, profile, slot)) is registry.ReservedAttempt


def test_unchecked_generation_symlink_would_double_count_one_registry_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    canonical = _create(repo, profile, [_slot()])
    real_registry, generation_profile, binding, _rows = _write_v2_generation(
        repo,
        protocol_sha256="a" * 64,
        start_count=5,
    )
    alias_directory = canonical.parent / ("b" * 64)
    alias_directory.symlink_to(
        real_registry.parent,
        target_is_directory=True,
    )
    alias_registry = alias_directory / "registry.jsonl"
    root = admission.shared_admission_root(repo)
    _assert_complete_generation_symlink_rejected(
        root=root,
        generation_directory=alias_directory,
    )

    original_is_symlink = Path.is_symlink
    original_is_directory_mode = stat.S_ISDIR

    def hide_generation_symlink(path: Path) -> bool:
        if path == alias_directory:
            return False
        return original_is_symlink(path)

    def accept_symlink_directory_mode(mode: int) -> bool:
        return stat.S_ISLNK(mode) or original_is_directory_mode(mode)

    monkeypatch.setattr(Path, "is_symlink", hide_generation_symlink)
    monkeypatch.setattr(stat, "S_ISDIR", accept_symlink_directory_mode)
    monkeypatch.setattr(
        admission,
        "_assert_no_symlink_components",
        lambda _path: None,
    )

    with admission._locked(root):
        generations = registry._registry_generation_paths_locked(root, _FREEZE)
    assert generations == (canonical, real_registry, alias_registry)
    assert os.path.samefile(real_registry, alias_registry)

    budget_key_for = generation_profile.transition_policy.budget_key
    assert budget_key_for is not None
    budget_key = budget_key_for(_v2_slot(0))
    counts: core.BudgetCounts = {}
    observed_counts: list[int] = []
    for generation_path in (real_registry, alias_registry):
        _loaded, counts = core.load_attempt_registry_with_budget_counts(
            generation_path.read_bytes(),
            profile=generation_profile,
            expected_binding=binding,
            initial_started_budget_counts=counts,
        )
        observed_counts.append(counts[budget_key])
    assert observed_counts == [5, 10]


def test_generation_resolver_rejects_stale_recovery_policy_and_accepts_current(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    stale_profile = profile8b.make_s8b_v2_domain_profile(
        max_consumptions_per_budget_key=10,
        recovery_authority_id=_RECOVERY_AUTHORITY,
        recovery_authority_policy_sha256=_POLICY,
    )
    stale_path, _stale, _binding, _rows = _write_v2_generation(
        repo,
        protocol_sha256="a" * 64,
        profile=stale_profile,
    )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=(
            "generation recovery policy differs from current authority"
        ),
    ):
        _reserve(repo, profile, slot)

    stale_path.unlink()
    _write_v2_generation(repo, protocol_sha256="a" * 64)
    assert type(_reserve(repo, profile, slot)) is registry.ReservedAttempt


def test_generation_resolver_rejects_protocol_path_mismatch_and_accepts_match(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    declared_protocol = "a" * 64
    path_protocol = "b" * 64
    mismatched, _generation_profile, _binding, rows = _write_v2_generation(
        repo,
        protocol_sha256=declared_protocol,
        path_protocol_sha256=path_protocol,
    )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="generation protocol differs from genesis",
    ):
        _reserve(repo, profile, slot)

    mismatched.unlink()
    mismatched.parent.rmdir()
    matched = registry.registry_path(
        repo,
        freeze_sha256=_FREEZE,
        protocol_sha256=declared_protocol,
    )
    matched.parent.mkdir(parents=True)
    matched.write_bytes(_bytes(rows))
    assert type(_reserve(repo, profile, slot)) is registry.ReservedAttempt


def test_generation_resolver_rejects_unknown_schema_and_accepts_known_v2(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    path, _generation_profile, _binding, rows = _write_v2_generation(
        repo, protocol_sha256="a" * 64,
    )
    genesis_payload = {
        key: value
        for key, value in rows[0].items()
        if key not in {
            "event_index", "previous_event_sha256", "event_sha256",
        }
    }
    genesis_payload["schema_version"] = "s8b-floor-attempt-registry/v3"
    unknown = core.chained_event_row(
        genesis_payload,
        event_index=0,
        previous_event_sha256="0" * 64,
    )
    path.write_bytes(_bytes((unknown,)))
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="generation profile is not reconstructible",
    ):
        _reserve(repo, profile, slot)

    path.write_bytes(_bytes(rows))
    assert type(_reserve(repo, profile, slot)) is registry.ReservedAttempt


def test_generation_resolver_accepts_canonical_v1_current_authority(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = profile8b.make_s8b_domain_profile(
        max_consumptions_per_budget_key=10,
        recovery_authority_id=scheduler.AUTHORITY_ID,
        recovery_authority_policy_sha256=scheduler.AUTHORITY_POLICY_SHA256,
    )
    slot = _slot()
    path = _create(repo, profile, [slot])
    genesis = registry._peek_registry_genesis(path.read_bytes())
    reconstructed, binding = registry._profile_and_binding_for_generation(
        path=path, genesis=genesis,
    )
    assert reconstructed.schema is profile8b.S8B_SCHEMA_PROFILE
    assert reconstructed.layout is profile8b.S8B_REGISTRY_LAYOUT
    assert binding == _BINDING
    assert core.load_attempt_registry(
        path.read_bytes(),
        profile=reconstructed,
        expected_binding=binding,
    )[0] == genesis

    synthetic_binding = replace(_BINDING, protocol_sha256="a" * 64)
    synthetic_profile = replace(
        profile, layout=profile8b.S8B_V2_REGISTRY_LAYOUT,
    )
    synthetic_rows = core.create_attempt_registry_genesis(
        profile=synthetic_profile,
        slots=[slot],
        binding=synthetic_binding,
    )
    synthetic_path = registry.registry_path(
        repo,
        freeze_sha256=_FREEZE,
        protocol_sha256=synthetic_binding.protocol_sha256,
    )
    synthetic_path.parent.mkdir(parents=True)
    synthetic_path.write_bytes(_bytes(synthetic_rows))
    synthetic_genesis = registry._peek_registry_genesis(
        synthetic_path.read_bytes()
    )
    synthetic_reconstructed, recovered_binding = (
        registry._profile_and_binding_for_generation(
            path=synthetic_path,
            genesis=synthetic_genesis,
        )
    )
    assert synthetic_reconstructed.schema is profile8b.S8B_SCHEMA_PROFILE
    assert synthetic_reconstructed.layout is profile8b.S8B_V2_REGISTRY_LAYOUT
    assert recovered_binding == synthetic_binding
    assert core.load_attempt_registry(
        synthetic_path.read_bytes(),
        profile=synthetic_reconstructed,
        expected_binding=recovered_binding,
    ) == synthetic_rows
    v2_path, _v2_profile, _v2_binding, _v2_rows = _write_v2_generation(
        repo, protocol_sha256="b" * 64,
    )
    root = admission.shared_admission_root(repo)
    with admission._locked(root):
        assert registry._registry_generation_paths_locked(root, _FREEZE) == (
            path,
            synthetic_path,
            v2_path,
        )


def test_cross_generation_budget_accepts_tenth_and_rejects_eleventh_before_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile(budget=10)
    first = _slot(0, configuration_id="configuration-a")
    second = _slot(1, configuration_id="configuration-a")
    path = _create(repo, profile, [first, second])
    generation, _v2_profile, _binding, _rows = _write_v2_generation(
        repo,
        protocol_sha256="a" * 64,
        budget=10,
        start_count=9,
    )
    assert generation.is_file()

    assert type(_reserve(repo, profile, first)) is registry.ReservedAttempt
    replayed = core.load_attempt_registry(path.read_bytes(), profile=profile)
    assert sum(row.get("event") == "start" for row in replayed) == 1

    def forbidden_staging(*_args: object, **_kwargs: object) -> Path:
        raise AssertionError("budget rejection reached staging")

    monkeypatch.setattr(registry, "_write_staging", forbidden_staging)
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=(
            r"^\[attempt-slot-order\] attempt consumption exceeds "
            r"the profile budget$"
        ),
    ):
        _reserve(repo, profile, second)
    assert sum(
        row.get("event") == "start"
        for row in core.load_attempt_registry(path.read_bytes(), profile=profile)
    ) == 1


def test_locked_update_seam_does_not_reacquire_lock_or_run_prelock_hook(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    root = admission.shared_admission_root(repo)
    snapshots: list[bytes] = []
    monkeypatch.setattr(
        registry, "_PRELOCK_SNAPSHOT_HOOK", snapshots.append,
    )

    with admission._locked(root) as lock:
        rows, result = registry._atomic_update_locked(
            lock,
            root=root,
            path=path,
            profile=profile,
            binding=_BINDING,
                transition=lambda current, _evidence: (current, "locked"),
        )
    assert result == "locked"
    assert rows == core.load_attempt_registry(path.read_bytes(), profile=profile)
    assert snapshots == []

    _rows, outer_result = registry._atomic_update(
        root=root,
        path=path,
        profile=profile,
        binding=_BINDING,
        transition=lambda current, _evidence: (current, "outer"),
    )
    assert outer_result == "outer"
    assert snapshots == [path.read_bytes()]


def test_forged_v2_profile_is_rejected_but_slot_lookup_is_five_axis(
    tmp_path: Path,
) -> None:
    v2_profile = _v2_authority_profile()
    first = _v2_slot(0, measurement_ordinal=0)
    second = _v2_slot(0, measurement_ordinal=1)
    rows = [
        {
            "schema_version": v2_profile.schema.current,
            "event": "start",
            **v2_profile.slot_codec.to_json(first),
        },
        {
            "schema_version": v2_profile.schema.current,
            "event": "start",
            **v2_profile.slot_codec.to_json(second),
        },
    ]
    assert registry._rows_for_event(
        rows, slot=first, event="start", profile=v2_profile,
    ) == [rows[0]]
    assert registry._rows_for_event(
        rows, slot=second, event="start", profile=v2_profile,
    ) == [rows[1]]

    repo = _repo(tmp_path / "repo")
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="domain profile differs from frozen 8b semantics",
    ):
        registry.create_attempt_registry(
            repo,
            profile=replace(v2_profile, terminal_row_validator=None),
            slots=[first, second],
            binding=_BINDING,
        )
    assert _create(repo, _profile(), [_slot()]).is_file()


def test_v2_profile_opens_generation_create_and_read(
    tmp_path: Path,
) -> None:
    profile = _v2_authority_profile()
    slot = _v2_slot(0)
    repo = _repo(tmp_path / "repo")
    path = registry.create_attempt_registry(
        repo, profile=profile, slots=[slot], binding=_BINDING,
    )
    assert path == registry.registry_path(
        repo,
        freeze_sha256=_FREEZE,
        protocol_sha256=_PROTOCOL,
    )
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[0]["schema_version"] == profile8b.S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION


def test_v2_profile_exact_gate_rejects_both_new_field_mutations() -> None:
    profile = _v2_authority_profile()
    assert registry._assert_profile(profile) is profile
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="domain profile differs from frozen 8b semantics",
    ):
        registry._assert_profile(
            replace(profile, terminal_row_validator=None)
        )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="domain profile differs from frozen 8b semantics",
    ):
        registry._assert_profile(
            replace(
                profile,
                transition_policy=replace(
                    profile.transition_policy,
                    retryable_terminal_opens_next_attempt=True,
                ),
            )
        )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="domain profile schema is not a frozen 8b schema",
    ):
        registry._assert_profile(
            replace(
                profile,
                schema=core.SchemaProfile(
                    current="foreign/v1",
                    readable=frozenset({"foreign/v1"}),
                    genesis_keys={"foreign/v1": frozenset()},
                    event_keys={"foreign/v1": {}},
                ),
            )
        )


def test_generation_publish_direct_barriers_adapter_mapping_and_positive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _v2_authority_profile()
    slot = _v2_slot(0)
    rows = core.create_attempt_registry_genesis(
        profile=profile, slots=[slot], binding=_BINDING,
    )
    payload = _bytes(rows)

    symlink_repo = _repo(tmp_path / "symlink")
    symlink_path = registry.registry_path(
        symlink_repo,
        freeze_sha256=_FREEZE,
        protocol_sha256=_PROTOCOL,
    )
    symlink_path.parent.parent.mkdir(parents=True)
    outside = tmp_path / "generation-outside"
    outside.mkdir()
    (outside / "registry.jsonl").write_bytes(payload)
    symlink_path.parent.symlink_to(outside, target_is_directory=True)
    with pytest.raises(
        (registry.S8BAttemptRegistryError, admission.HoldoutAdmissionError),
        match="symlink|unsafe or incomplete",
    ):
        registry._publish_registry_generation_create_only(
            root=admission.shared_admission_root(symlink_repo),
            path=symlink_path,
            payload=payload,
        )

    incomplete_repo = _repo(tmp_path / "incomplete")
    incomplete_path = registry.registry_path(
        incomplete_repo,
        freeze_sha256=_FREEZE,
        protocol_sha256=_PROTOCOL,
    )
    incomplete_path.parent.mkdir(parents=True)
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="generation directory is unsafe or incomplete",
    ):
        registry._publish_registry_generation_create_only(
            root=admission.shared_admission_root(incomplete_repo),
            path=incomplete_path,
            payload=payload,
        )

    mapped_repo = _repo(tmp_path / "mapped")
    calls: list[tuple[Path, Path, bytes]] = []
    original = registry._publish_registry_generation_create_only

    def reject_publish(*, root: Path, path: Path, payload: bytes) -> None:
        calls.append((root, path, payload))
        raise registry.S8BAttemptRegistryError(
            "[test-generation-publish] lower publish rejected"
        )

    with monkeypatch.context() as patcher:
        patcher.setattr(
            registry,
            "_publish_registry_generation_create_only",
            reject_publish,
        )
        with pytest.raises(
            registry.S8BAttemptRegistryError,
            match=r"^\[test-generation-publish\] lower publish rejected$",
        ):
            registry.create_attempt_registry(
                mapped_repo,
                profile=profile,
                slots=[slot],
                binding=_BINDING,
            )
    assert len(calls) == 1
    path = registry.create_attempt_registry(
        mapped_repo, profile=profile, slots=[slot], binding=_BINDING,
    )
    assert path.is_file()
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="durable registry generation already exists",
    ):
        original(
            root=admission.shared_admission_root(mapped_repo),
            path=path,
            payload=payload,
        )


def test_generation_symlink_lower_layers_map_rejection_and_keep_positive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    complete = tmp_path / "complete-generation"
    complete.mkdir()
    (complete / "registry.jsonl").write_bytes(b"{}\n")
    alias = tmp_path / "generation-alias"
    alias.symlink_to(complete, target_is_directory=True)
    operations = (
        lambda: registry._read_regular_bytes(alias / "registry.jsonl"),
        lambda: registry._ensure_durable_directory(alias),
        lambda: registry._write_staging(
            alias / "candidate.json",
            b"{}\n",
            logical_name="floor-attempt-registries/direct",
        ),
        lambda: admission.write_guarded_create_bytes(
            alias / "candidate.json",
            b"{}\n",
            logical_name="floor-attempt-registries/direct",
        ),
    )
    for operation in operations:
        with pytest.raises(
            admission.HoldoutAdmissionError,
            match=r"guarded writer path is symlinked:",
        ):
            operation()

    profile = _v2_authority_profile()
    slot = _v2_slot(0)
    calls: list[Path] = []

    def reject_lower(
        path: Path, _payload: bytes, *, logical_name: str,
    ) -> str:
        calls.append(path)
        raise admission.HoldoutAdmissionError(
            "[test-symlink-lower] guarded writer rejected"
        )

    with monkeypatch.context() as patcher:
        patcher.setattr(admission, "write_guarded_create_bytes", reject_lower)
        with pytest.raises(
            admission.HoldoutAdmissionError,
            match=r"^\[test-symlink-lower\] guarded writer rejected$",
        ):
            registry.create_attempt_registry(
                _repo(tmp_path / "mapped"),
                profile=profile,
                slots=[slot],
                binding=_BINDING,
            )
    assert len(calls) == 1

    positive_repo = _repo(tmp_path / "positive")
    positive = registry.create_attempt_registry(
        positive_repo, profile=profile, slots=[slot], binding=_BINDING,
    )
    assert registry.read_attempt_registry(
        positive_repo, profile=profile, binding=_BINDING,
    ) == core.load_attempt_registry(positive.read_bytes(), profile=profile)


def test_atomic_update_locked_direct_guard_maps_upstream_and_keeps_positive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    path = _create(repo, profile, [slot])
    root = admission.shared_admission_root(repo)
    with pytest.raises(
        admission.HoldoutAdmissionError,
        match=r"^floor attempt consumption requires the live admission root lock$",
    ):
        registry._atomic_update_locked(
            admission._AdmissionRootLock(),
            root=root,
            path=path,
            profile=profile,
            binding=_BINDING,
            transition=lambda rows, _evidence: (rows, None),
        )

    calls: list[Path] = []

    def reject_guard(_lock: object, *, root: Path) -> None:
        calls.append(root)
        raise admission.HoldoutAdmissionError(
            "[test-live-lock-lower] lower lock guard rejected"
        )

    with monkeypatch.context() as patcher:
        patcher.setattr(
            admission, "_assert_active_admission_root_lock", reject_guard,
        )
        with pytest.raises(
            admission.HoldoutAdmissionError,
            match=r"^\[test-live-lock-lower\] lower lock guard rejected$",
        ):
            _reserve(repo, profile, slot)
    assert calls == [root]
    assert type(_reserve(repo, profile, slot)) is registry.ReservedAttempt


def test_atomic_update_with_consumption_marker_hook_precedes_root_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    root = admission.shared_admission_root(case["repo_root"])
    path = registry.registry_path(
        case["repo_root"],
        freeze_sha256=binding.freeze_sha256,
        protocol_sha256=binding.protocol_sha256,
    )
    hook_saw_unlocked: list[bool] = []
    def observe_lock_state(_snapshot: bytes) -> None:
        fd = os.open(root / admission._LOCK_NAME, os.O_RDWR)
        try:
            try:
                admission.fcntl.flock(
                    fd, admission.fcntl.LOCK_EX | admission.fcntl.LOCK_NB,
                )
            except BlockingIOError:
                pass
            else:
                hook_saw_unlocked.append(True)
                admission.fcntl.flock(fd, admission.fcntl.LOCK_UN)
        finally:
            os.close(fd)

    monkeypatch.setattr(registry, "_PRELOCK_SNAPSHOT_HOOK", observe_lock_state)
    identity = case["use_kwargs"]
    registry._atomic_update_with_consumption_marker(
        root=root, path=path,
        profile=profile, binding=binding, slot=slot,
        marker=case["capability"],
        measurement_generation_claim_digest=identity[
            "measurement_generation_claim_digest"
        ],
        attempt_id=identity["attempt_id"],
        campaign_run_id=identity["campaign_run_id"],
        manifest_sha256=identity["manifest_sha256"],
        run_relpath=identity["run_relpath"], cell_id=identity["cell_id"],
        transition=lambda rows, _evidence: (rows, None),
    )
    assert hook_saw_unlocked == [True]


def test_v2_resume_rejects_recovery_ordinal_and_accepts_zero(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    retry_slot = replace(slot, attempt_ordinal=1, schedule_row_sha256="d" * 64)
    path = registry.registry_path(
        case["repo_root"],
        freeze_sha256=binding.freeze_sha256,
        protocol_sha256=binding.protocol_sha256,
    )
    path.write_bytes(_bytes(core.create_attempt_registry_genesis(
        profile=profile, slots=[slot, retry_slot], binding=binding,
    )))
    reserved = _reserve_v2(case, profile, binding, slot)
    classified = _classify(reserved)
    assert type(registry.resume_attempt(
        case["repo_root"],
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        deferred_output_reader=lambda: b"zero-output",
        consumption_marker=case["capability"],
    )) is type(classified) is registry.ClassifiedAttempt
    registry.record_attempt_recovery(
        reserved,
        scheduler_accounting_receipt=_recovery_receipt_bytes(
            case["repo_root"], profile, slot, "node_failure",
            binding=binding,
            authority_id=scheduler.AUTHORITY_ID,
            authority_policy_sha256=scheduler.AUTHORITY_POLICY_SHA256,
        ),
        recoverer_process_identity=_RECOVERER,
        recovered_at="2026-08-25T00:00:04+00:00",
    )
    rows = registry.read_attempt_registry(
        case["repo_root"], profile=profile, binding=binding,
    )
    rows = core.reserve_attempt_slot(
        rows,
        profile=profile,
        freeze_id=binding.freeze_sha256,
        slot_id=profile.slot_codec.slot_id(retry_slot),
        binding=binding,
        run_start_receipt_sha256=_RUN_START,
        process_identity=_PROCESS,
        started_at="2026-08-25T00:00:05+00:00",
    )
    path.write_bytes(_bytes(rows))
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=(
            r"^\[s8b-attempt-registry-consume\] "
            r"v2 resume recovery ordinal is not capability-backed$"
        ),
    ):
        registry.resume_attempt(
            case["repo_root"],
            profile=profile,
            binding=binding,
            slot_id=profile.slot_codec.slot_id(retry_slot),
            deferred_output_reader=lambda: b"retry-output",
            consumption_marker=case["capability"],
        )


def test_v2_reservation_rejects_claim_from_other_protocol_generation(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    assert type(_reserve_v2(case, profile, binding, slot)) is (
        registry.ReservedAttempt
    )

    root = case["repo_root"]
    protocol, freeze = admission_cases._fixture_documents(  # noqa: SLF001
        master_seed="seed-b",
    )
    admission_cases._write_fixed_documents(  # noqa: SLF001
        root, protocol, freeze,
    )
    admission_cases._git(  # noqa: SLF001
        root, "add", "output/s8b-freeze/floor_protocol.json",
    )
    admission_cases._git(  # noqa: SLF001
        root, "-c", "user.name=fixture", "-c", "user.email=f@example.invalid",
        "commit", "-m", "change schedule seed",
    )
    cells, schedule = admission_cases._cells_and_schedule(  # noqa: SLF001
        protocol, freeze,
    )
    reservation = admission_cases._reserve(  # noqa: SLF001
        root, protocol, freeze, run_id="run-b",
    )
    admitted_by_cell = admission.finalize_floor_holdout_admissions(reservation)
    cell = cells[0]
    schedule_row = next(
        row for row in schedule if row["cell_id"] == cell["cell_id"]
    )
    attempt_id = f"{cell['cell_id']}::seq{schedule_row['seq']}"
    admitted = admitted_by_cell[cell["cell_id"]]
    state = admission._cell_state(admitted)  # noqa: SLF001
    (state.run_dir / "journal.jsonl").write_text(json.dumps({
        "event": "session-start", "seq": schedule_row["seq"],
        "round": schedule_row["round"], "kind": "planned",
        "cell_id": cell["cell_id"], "attempt_id": attempt_id,
        "trigger": None,
    }, sort_keys=True) + "\n", encoding="utf-8")
    admission.consume_attempt_ticket(admitted, attempt_id=attempt_id)
    capability = admission.validate_floor_attempt_consumption_marker(
        admitted, attempt_id=attempt_id,
    )
    marker = admission_cases._floor_expected_marker(  # noqa: SLF001
        admitted, attempt_id,
    )
    claim = admission._read_canonical_document(  # noqa: SLF001
        admission._measurement_generation_claim_path(  # noqa: SLF001
            state.root, marker["measurement_generation_claim_digest"],
        )
    )
    assert type(capability) is admission.FloorAttemptConsumptionMarker
    assert claim["protocol_sha256"] != binding.protocol_sha256
    identity = {
        "freeze_holdout_key": marker["freeze_holdout_key"],
        "configuration_id": marker["configuration_id"],
        "repetition": schedule_row["round"] - 1,
        "measurement_ordinal": 0,
        "attempt_ordinal": 0,
    }
    foreign_slot = profile8b.S8BV2AttemptSlot(
        **identity,
        schedule_row_sha256=hashlib.sha256(
            core.canonical_json_bytes(identity)
        ).hexdigest(),
    )
    path = registry.registry_path(
        root, freeze_sha256=binding.freeze_sha256,
        protocol_sha256=binding.protocol_sha256,
    )
    path.write_bytes(_bytes(core.create_attempt_registry_genesis(
        profile=profile, slots=[foreign_slot], binding=binding,
    )))
    foreign_case = {
        "repo_root": root, "marker": marker, "capability": capability,
    }
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=(
            r"^\[s8b-attempt-registry-consume\] v2 admission claim "
            r"differs from the registry generation or slot$"
        ),
    ):
        _reserve_v2(foreign_case, profile, binding, foreign_slot)


def test_v2_start_only_resume_fails_closed_and_classified_resume_stays_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    reserved = _reserve_v2(case, profile, binding, slot)

    class InjectedCrash(RuntimeError):
        pass

    def stop_after_claim(point: str) -> None:
        if point == "after-classification-claim":
            raise InjectedCrash(point)

    with monkeypatch.context() as patcher:
        patcher.setattr(registry, "_FAULT_HOOK", stop_after_claim)
        with pytest.raises(InjectedCrash, match="after-classification-claim"):
            _classify(reserved)
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=(
            r"^\[s8b-attempt-registry-resume\] "
            r"v2 start-only resume is not marker-atomic$"
        ),
    ):
        registry.resume_attempt(
            case["repo_root"],
            profile=profile,
            binding=binding,
            slot_id=profile.slot_codec.slot_id(slot),
            deferred_output_reader=lambda: b"resumed-output",
            consumption_marker=case["capability"],
        )

    assert type(_classify(reserved)) is registry.ClassifiedAttempt
    assert type(registry.resume_attempt(
        case["repo_root"],
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        deferred_output_reader=lambda: b"resumed-output",
        consumption_marker=case["capability"],
    )) is registry.ClassifiedAttempt


def test_v2_mutation_marker_binding_scope_is_exact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker_calls: list[str] = []
    plain_calls: list[str] = []
    real_marker = registry._atomic_update_with_consumption_marker
    real_plain = registry._atomic_update

    def owner(kwargs: Mapping[str, Any]) -> str:
        return kwargs["transition"].__qualname__.split(".<locals>.")[0]

    def marker_spy(**kwargs: Any) -> Any:
        marker_calls.append(owner(kwargs))
        return real_marker(**kwargs)

    def plain_spy(**kwargs: Any) -> Any:
        plain_calls.append(owner(kwargs))
        return real_plain(**kwargs)

    monkeypatch.setattr(
        registry, "_atomic_update_with_consumption_marker", marker_spy,
    )
    monkeypatch.setattr(registry, "_atomic_update", plain_spy)
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    reserved = _reserve_v2(case, profile, binding, slot)
    classified = _classify(reserved)
    assert type(classified) is registry.ClassifiedAttempt
    assert type(registry.begin_attempt_observation(classified)) is (
        registry.CapturedObservation
    )
    with pytest.raises(core.AttemptRegistryCoreError):
        registry.record_attempt_recovery(
            reserved,
            scheduler_accounting_receipt=b"{}\n",
            recoverer_process_identity=_RECOVERER,
            recovered_at="2026-08-25T00:00:04+00:00",
        )
    events = [row["event"] for row in registry.read_attempt_registry(
        case["repo_root"], profile=profile, binding=binding,
    )]
    assert "classification" in events and _claim_file(case["repo_root"]).is_file()
    assert "observation-start" in events and "recovery" not in events
    assert marker_calls == ["reserve_attempt_slot", "_begin_attempt_observation"]
    assert plain_calls == ["classify_attempt", "record_attempt_recovery"]


def test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for function in (registry.reserve_attempt_slot, registry.resume_attempt):
        parameter = inspect.signature(function).parameters[
            "consumption_marker"
        ]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    path = registry.registry_path(
        case["repo_root"],
        freeze_sha256=binding.freeze_sha256,
        protocol_sha256=binding.protocol_sha256,
    )
    missing_marker = dict(case)
    missing_marker["capability"] = None
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="v2 reservation requires a consumption marker",
    ):
        _reserve_v2(missing_marker, profile, binding, slot)

    guard_calls: list[Path] = []

    def reject_lock(_lock: object, *, root: Path) -> None:
        guard_calls.append(root)
        raise admission.HoldoutAdmissionError(
            "floor attempt consumption requires the live admission root lock"
        )

    with monkeypatch.context() as patcher:
        patcher.setattr(
            admission, "_assert_active_admission_root_lock", reject_lock,
        )
        with pytest.raises(
            admission.HoldoutAdmissionError,
            match="requires the live admission root lock",
        ):
            _reserve_v2(case, profile, binding, slot)
    assert guard_calls

    snapshots: list[bytes] = []
    monkeypatch.setattr(registry, "_PRELOCK_SNAPSHOT_HOOK", snapshots.append)
    reserved = _reserve_v2(case, profile, binding, slot)
    assert len(snapshots) == 1
    assert len(core.load_attempt_registry(snapshots[0], profile=profile)) == 1
    classified = _classify(reserved)
    assert type(classified) is registry.ClassifiedAttempt
    claim_path = _claim_file(case["repo_root"])
    claim_bytes = claim_path.read_bytes()
    claim = json.loads(claim_bytes)
    assert frozenset(claim) == registry._CLAIM_V3_KEYS
    assert claim["schema_version"] == registry._CLASSIFICATION_CLAIM_V3_SCHEMA
    assert claim["protocol_sha256"] == binding.protocol_sha256
    assert claim["schedule_sha256"] == binding.schedule_sha256
    assert claim["measurement_ordinal"] == slot.measurement_ordinal
    assert claim["admission_claim_digest"] == (
        case["marker"]["measurement_generation_claim_digest"]
    )
    tampered_claim = dict(claim)
    tampered_claim["protocol_sha256"] = "f" * 64
    claim_path.write_bytes(core.canonical_json_bytes(tampered_claim) + b"\n")
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="classification claim differs: protocol_sha256",
    ):
        registry._classification_claim(
            root=admission.shared_admission_root(case["repo_root"]),
            binding=binding,
            slot=slot,
        )
    claim_path.write_bytes(claim_bytes)

    resumed = registry.resume_attempt(
        case["repo_root"],
        profile=profile,
        binding=binding,
        slot_id=profile.slot_codec.slot_id(slot),
        deferred_output_reader=lambda: b"v2-raw-output",
        consumption_marker=case["capability"],
    )
    assert type(resumed) is registry.ClassifiedAttempt
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="v2 resume requires a consumption marker",
    ):
        registry.resume_attempt(
            case["repo_root"],
            profile=profile,
            binding=binding,
            slot_id=profile.slot_codec.slot_id(slot),
            deferred_output_reader=lambda: b"v2-raw-output",
        )

    captured = registry.begin_attempt_observation(classified)
    assert type(captured) is registry.CapturedObservation
    with pytest.raises(
        RuntimeError,
        match=(
            r"^\[s8b-v2-terminal\] v2 terminal requires "
            r"the sealed evidence API$"
        ),
    ):
        _terminal(captured)


def test_v3_claim_address_separates_measurement_ordinals() -> None:
    schedule_row_sha256 = "d" * 64
    first = replace(
        _v2_slot(0, measurement_ordinal=0),
        schedule_row_sha256=schedule_row_sha256,
    )
    second = replace(first, measurement_ordinal=1)
    first_payload = registry._slot_address_payload_v3(
        binding=_BINDING, slot=first,
    )
    second_payload = registry._slot_address_payload_v3(
        binding=_BINDING, slot=second,
    )
    assert first.schedule_row_sha256 == second.schedule_row_sha256
    assert {
        key for key in first_payload if first_payload[key] != second_payload[key]
    } == {"measurement_ordinal"}
    assert first_payload["measurement_ordinal"] == 0
    assert second_payload["measurement_ordinal"] == 1
    assert first_payload != second_payload
    root = Path("/synthetic-shared-admission-root")
    assert registry._classification_claim_path(
        root, binding=_BINDING, slot=first,
    ) != registry._classification_claim_path(
        root, binding=_BINDING, slot=second,
    )


def test_legacy_terminal_adapter_maps_core_rejection_and_keeps_v1_positive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path / "repo")
    profile = _profile()
    slot = _slot()
    _create(repo, profile, [slot])
    classified = _classify(_reserve(repo, profile, slot))
    assert type(classified) is registry.ClassifiedAttempt
    captured = _observe(repo, slot, classified)
    calls: list[core.RegistryRows] = []

    def reject_core(
        rows: core.RegistryRows, **_kwargs: object,
    ) -> core.RegistryRows:
        calls.append(rows)
        raise core.AttemptRegistryCoreError(
            "[test-core-terminal] lower terminal rejected"
        )

    with monkeypatch.context() as patcher:
        patcher.setattr(core, "record_attempt_terminal", reject_core)
        with pytest.raises(
            core.AttemptRegistryCoreError,
            match=r"^\[test-core-terminal\] lower terminal rejected$",
        ):
            _terminal(captured)
    assert len(calls) == 1
    _terminal(captured)
    assert registry.read_attempt_registry(
        repo, profile=profile, binding=_BINDING,
    )[-1]["terminal_status"] == "observed"


def _prefix_registry_path(
    repo: Path, binding: profile8b.S8BAttemptBinding,
) -> Path:
    root = admission.shared_admission_root(repo)
    relative = registry._relative_registry_path(
        binding.freeze_sha256,
        protocol_sha256=binding.protocol_sha256,
    )
    return root.joinpath(*relative.parts)


def _assert_prefix_evidence_error(
    category: str, reason: str, call: Any,
) -> None:
    with pytest.raises(admission.FloorHoldoutEvidenceError) as exc_info:
        call()
    assert exc_info.value.category == category
    assert exc_info.value.reason == reason


def _advance_v2_prefix(
    tmp_path: Path, target_row_count: int,
) -> tuple[
    dict[str, Any],
    core.DomainProfile[Any, Any],
    profile8b.S8BAttemptBinding,
    profile8b.S8BV2AttemptSlot,
]:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    reserved: registry.ReservedAttempt | None = None
    if target_row_count >= 3:
        reserved = _reserve_v2(case, profile, binding, slot)
    classified: registry.ClassifiedAttempt | registry.ClassifiedFailure | None = None
    if target_row_count >= 4:
        assert reserved is not None
        classified = _classify(reserved)
        assert type(classified) is registry.ClassifiedAttempt
    if target_row_count >= 5:
        assert type(classified) is registry.ClassifiedAttempt
        captured = registry.begin_attempt_observation(classified)
        assert type(captured) is registry.CapturedObservation
    return case, profile, binding, slot


@pytest.mark.parametrize("target_row_count", (1, 3, 4, 5))
def test_attempt_registry_prefix_capture_and_inspection_accept_reachable_v2_rows(
    tmp_path: Path, target_row_count: int,
) -> None:
    case, _profile_value, binding, _slot_value = _advance_v2_prefix(
        tmp_path, target_row_count,
    )
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    assert proof["row_count"] == target_row_count
    assert proof["schema"] == core.ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA
    assert proof["registry_schema"] == (
        profile8b.S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION
    )
    assert proof["freeze_sha256"] == binding.freeze_sha256
    assert proof["protocol_sha256"] == binding.protocol_sha256
    assert proof["schedule_sha256"] == binding.schedule_sha256
    assert frozenset(proof) == core.ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS
    inspected = registry.inspect_attempt_registry_prefix(
        case["repo_root"],
        expected_binding=binding,
        row_count=target_row_count,
        chain_head_sha256=str(proof["chain_head_sha256"]),
    )
    assert inspected == proof
    assert inspected is not proof


def test_attempt_registry_prefix_inspection_accepts_valid_later_append(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    reserved = _reserve_v2(case, profile, binding, slot)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    assert proof["row_count"] == 3
    classified = _classify(reserved)
    assert type(classified) is registry.ClassifiedAttempt
    inspected = registry.inspect_attempt_registry_prefix(
        case["repo_root"],
        expected_binding=binding,
        row_count=3,
        chain_head_sha256=str(proof["chain_head_sha256"]),
    )
    assert inspected == proof
    assert registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )["row_count"] == 4


@pytest.mark.parametrize("unsafe_kind", ("symlink", "missing-registry"))
def test_attempt_registry_prefix_ignores_unsafe_sibling_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unsafe_kind: str,
) -> None:
    case, _profile_value, binding, _slot_value = _advance_v2_prefix(
        tmp_path, 3,
    )
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    path = _prefix_registry_path(case["repo_root"], binding)
    sibling = path.parent.parent / ("e" * 64)
    if unsafe_kind == "symlink":
        sibling.symlink_to(tmp_path, target_is_directory=True)
    else:
        sibling.mkdir()

    def reject_enumeration(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("prefix inspection enumerated sibling generations")

    monkeypatch.setattr(
        registry, "_registry_generation_paths_locked", reject_enumeration,
    )
    assert registry.inspect_attempt_registry_prefix(
        case["repo_root"],
        expected_binding=binding,
        row_count=3,
        chain_head_sha256=str(proof["chain_head_sha256"]),
    ) == proof


def test_attempt_registry_prefix_rejects_malformed_tail_after_n(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    _reserve_v2(case, profile, binding, slot)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    path = _prefix_registry_path(case["repo_root"], binding)
    path.write_bytes(path.read_bytes() + b"not-json\n")
    _assert_prefix_evidence_error(
        "mismatch",
        "attempt-registry-replay-invalid",
        lambda: registry.inspect_attempt_registry_prefix(
            case["repo_root"],
            expected_binding=binding,
            row_count=3,
            chain_head_sha256=str(proof["chain_head_sha256"]),
        ),
    )


def test_attempt_registry_prefix_rejects_broken_chain_after_n(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    reserved = _reserve_v2(case, profile, binding, slot)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    _classify(reserved)
    path = _prefix_registry_path(case["repo_root"], binding)
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[3]["previous_event_sha256"] = "e" * 64
    rows[3]["event_sha256"] = core.event_sha256(rows[3])
    path.write_bytes(_bytes(tuple(rows)))
    _assert_prefix_evidence_error(
        "mismatch",
        "attempt-registry-replay-invalid",
        lambda: registry.inspect_attempt_registry_prefix(
            case["repo_root"],
            expected_binding=binding,
            row_count=3,
            chain_head_sha256=str(proof["chain_head_sha256"]),
        ),
    )


def _rechain_v2_reservation_rows(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    previous = "0" * 64
    start_head: str | None = None
    for row in rows:
        row["previous_event_sha256"] = previous
        if row["event"] == "pre-observation-seal":
            assert start_head is not None
            row["start_event_sha256"] = start_head
        row["event_sha256"] = core.event_sha256(row)
        previous = row["event_sha256"]
        if row["event"] == "start":
            start_head = previous
    return tuple(rows)


def test_attempt_registry_prefix_rejects_reported_head_tamper(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    assert proof["row_count"] == 1
    _reserve_v2(case, profile, binding, slot)
    path = _prefix_registry_path(case["repo_root"], binding)
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0]["max_consumptions_per_budget_key"] += 1
    rechained = _rechain_v2_reservation_rows(rows)
    payload = _bytes(rechained)
    path.write_bytes(payload)
    rebuilt_profile, rebuilt_binding = (
        registry._profile_and_binding_for_generation(
            path=path, genesis=rechained[0],
        )
    )
    assert len(core.load_attempt_registry(
        payload,
        profile=rebuilt_profile,
        expected_binding=rebuilt_binding,
    )) == 3
    _assert_prefix_evidence_error(
        "mismatch",
        "attempt-registry-prefix-head-mismatch",
        lambda: registry.inspect_attempt_registry_prefix(
            case["repo_root"],
            expected_binding=binding,
            row_count=1,
            chain_head_sha256=str(proof["chain_head_sha256"]),
        ),
    )


def test_attempt_registry_prefix_unrecomputed_prefix_tamper_reaches_chain_gate(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    _reserve_v2(case, profile, binding, slot)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    path = _prefix_registry_path(case["repo_root"], binding)
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[1]["started_at"] = "2026-08-25T00:00:09+00:00"
    payload = _bytes(tuple(rows))
    path.write_bytes(payload)
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match="event_sha256 differs from its payload",
    ):
        core.load_attempt_registry(
            payload, profile=profile, expected_binding=binding,
        )
    _assert_prefix_evidence_error(
        "mismatch",
        "attempt-registry-replay-invalid",
        lambda: registry.inspect_attempt_registry_prefix(
            case["repo_root"],
            expected_binding=binding,
            row_count=3,
            chain_head_sha256=str(proof["chain_head_sha256"]),
        ),
    )


def test_attempt_registry_prefix_rejects_n_beyond_live_rows(
    tmp_path: Path,
) -> None:
    case, _profile_value, binding, _slot_value = _advance_v2_prefix(
        tmp_path, 1,
    )
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    _assert_prefix_evidence_error(
        "mismatch",
        "attempt-registry-prefix-too-short",
        lambda: registry.inspect_attempt_registry_prefix(
            case["repo_root"],
            expected_binding=binding,
            row_count=2,
            chain_head_sha256=str(proof["chain_head_sha256"]),
        ),
    )


def test_attempt_registry_prefix_rejects_synthetic_v1_at_generation_path(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    root = admission.provision_shared_admission_root(repo)
    legacy = replace(
        profile8b.make_s8b_domain_profile(
            max_consumptions_per_budget_key=64,
            recovery_authority_id=scheduler.AUTHORITY_ID,
            recovery_authority_policy_sha256=(
                scheduler.AUTHORITY_POLICY_SHA256
            ),
        ),
        layout=profile8b.S8B_V2_REGISTRY_LAYOUT,
    )
    rows = core.create_attempt_registry_genesis(
        profile=legacy, slots=[_slot()], binding=_BINDING,
    )
    path = root.joinpath(*registry._relative_registry_path(
        _FREEZE, protocol_sha256=_PROTOCOL,
    ).parts)
    path.parent.mkdir(parents=True)
    payload = _bytes(rows)
    path.write_bytes(payload)
    replay_profile, replay_binding = registry._profile_and_binding_for_generation(
        path=path, genesis=rows[0],
    )
    assert replay_binding == _BINDING
    assert core.load_attempt_registry(
        payload, profile=replay_profile, expected_binding=replay_binding,
    ) == rows
    _assert_prefix_evidence_error(
        "mismatch",
        "attempt-registry-generation-unsupported",
        lambda: registry.inspect_attempt_registry_prefix(
            repo,
            expected_binding=_BINDING,
            row_count=1,
            chain_head_sha256=rows[0]["event_sha256"],
        ),
    )


@pytest.mark.parametrize(
    "field", ("freeze_sha256", "protocol_sha256", "schedule_sha256"),
)
def test_attempt_registry_prefix_rejects_genesis_binding_substitution(
    tmp_path: Path, field: str,
) -> None:
    """診断 node: binding 拒否 reason の順序 pin。変異観測には使わない。"""

    case, _profile_value, binding, _slot_value = _advance_v2_prefix(
        tmp_path, 1,
    )
    source_path = _prefix_registry_path(case["repo_root"], binding)
    payload = source_path.read_bytes()
    rows = [json.loads(line) for line in payload.splitlines()]
    expected_binding = replace(binding, **{field: "e" * 64})
    target_path = _prefix_registry_path(case["repo_root"], expected_binding)
    if target_path != source_path:
        target_path.parent.mkdir(parents=True)
        target_path.write_bytes(payload)
    _assert_prefix_evidence_error(
        "mismatch",
        "attempt-registry-binding-mismatch",
        lambda: registry.inspect_attempt_registry_prefix(
            case["repo_root"],
            expected_binding=expected_binding,
            row_count=1,
            chain_head_sha256=rows[0]["event_sha256"],
        ),
    )


def test_attempt_registry_prefix_inspection_is_read_only_by_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    _reserve_v2(case, profile, binding, slot)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )

    def reject_write(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("prefix inspection reached a write helper")

    for target, name in (
        (admission, "provision_shared_admission_root"),
        (registry, "_entry_paths"),
        (admission, "_locked"),
        (admission, "_fsync_directory"),
        (registry, "_fsync_directory"),
        (registry, "_fsync_shared_root_chain"),
    ):
        monkeypatch.setattr(target, name, reject_write)
    assert registry.inspect_attempt_registry_prefix(
        case["repo_root"],
        expected_binding=binding,
        row_count=3,
        chain_head_sha256=str(proof["chain_head_sha256"]),
    ) == proof


def _regular_file_tree_snapshot(
    root: Path,
) -> dict[str, tuple[bytes, int, int]]:
    result: dict[str, tuple[bytes, int, int]] = {}
    for path in sorted(root.rglob("*")):
        metadata = os.lstat(path)
        if stat.S_ISREG(metadata.st_mode):
            result[path.relative_to(root).as_posix()] = (
                path.read_bytes(), metadata.st_ino, metadata.st_mtime_ns,
            )
    return result


def test_attempt_registry_prefix_inspection_preserves_file_bytes_and_inodes(
    tmp_path: Path,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    _reserve_v2(case, profile, binding, slot)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    root = admission.shared_admission_root(case["repo_root"])
    before = _regular_file_tree_snapshot(root)
    assert registry.inspect_attempt_registry_prefix(
        case["repo_root"],
        expected_binding=binding,
        row_count=3,
        chain_head_sha256=str(proof["chain_head_sha256"]),
    ) == proof
    assert _regular_file_tree_snapshot(root) == before


@pytest.mark.parametrize("missing", ("root", "lock"))
def test_attempt_registry_prefix_rejects_unavailable_root_without_provisioning(
    tmp_path: Path, missing: str,
) -> None:
    repo = _repo(tmp_path / "repo")
    root = admission.shared_admission_root(repo)
    if missing == "lock":
        root = admission.provision_shared_admission_root(repo)
        (root / admission._LOCK_NAME).unlink()
    _assert_prefix_evidence_error(
        "unverifiable",
        "attempt-registry-root-unavailable",
        lambda: registry.inspect_attempt_registry_prefix(
            repo,
            expected_binding=_BINDING,
            row_count=1,
            chain_head_sha256="e" * 64,
        ),
    )
    if missing == "root":
        assert not root.exists()
    else:
        assert root.is_dir()
        assert not (root / admission._LOCK_NAME).exists()


def test_attempt_registry_prefix_rejects_missing_current_registry_as_unverifiable(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path / "repo")
    admission.provision_shared_admission_root(repo)
    _assert_prefix_evidence_error(
        "unverifiable",
        "attempt-registry-read-unavailable",
        lambda: registry.inspect_attempt_registry_prefix(
            repo,
            expected_binding=_BINDING,
            row_count=1,
            chain_head_sha256="e" * 64,
        ),
    )


def test_attempt_registry_prefix_lower_layers_are_direct_and_mapped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, profile, binding, slot = _v2_registry_capability_case(tmp_path)
    _reserve_v2(case, profile, binding, slot)
    proof = registry.capture_attempt_registry_prefix(
        case["repo_root"], expected_binding=binding,
    )
    direct_rows = registry._replay_current_v2_attempt_registry(
        case["repo_root"], expected_binding=binding,
    )
    assert len(direct_rows) == 3
    assert core.validate_attempt_registry_prefix_proof(proof) == proof

    validator_calls: list[object] = []

    def reject_validator(value: object) -> dict[str, object]:
        validator_calls.append(value)
        raise core.AttemptRegistryCoreError(
            "[test-prefix-validator] lower validator rejected"
        )

    with monkeypatch.context() as patcher:
        patcher.setattr(
            core, "validate_attempt_registry_prefix_proof", reject_validator,
        )
        _assert_prefix_evidence_error(
            "mismatch",
            "attempt-registry-replay-invalid",
            lambda: registry.inspect_attempt_registry_prefix(
                case["repo_root"],
                expected_binding=binding,
                row_count=3,
                chain_head_sha256=str(proof["chain_head_sha256"]),
            ),
        )
    assert len(validator_calls) == 1

    replay_calls: list[profile8b.S8BAttemptBinding] = []

    def reject_replay(
        _repo_root_value: Path,
        *,
        expected_binding: profile8b.S8BAttemptBinding,
    ) -> core.RegistryRows:
        replay_calls.append(expected_binding)
        raise registry.S8BAttemptRegistryError(
            "[test-prefix-replay] lower replay rejected"
        )

    with monkeypatch.context() as patcher:
        patcher.setattr(
            registry, "_replay_current_v2_attempt_registry", reject_replay,
        )
        _assert_prefix_evidence_error(
            "mismatch",
            "attempt-registry-replay-invalid",
            lambda: registry.inspect_attempt_registry_prefix(
                case["repo_root"],
                expected_binding=binding,
                row_count=3,
                chain_head_sha256=str(proof["chain_head_sha256"]),
            ),
        )
    assert replay_calls == [binding]
    assert registry.inspect_attempt_registry_prefix(
        case["repo_root"],
        expected_binding=binding,
        row_count=3,
        chain_head_sha256=str(proof["chain_head_sha256"]),
    ) == proof


def test_sealed_v2_terminal_publishes_evidence_and_replays_old_and_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    calls: list[tuple[int, bool]] = []
    real_loader = registry._load_terminal_evidence_locked

    def count_loader(
        root: Path,
        registry_bytes: bytes,
        **kwargs: Any,
    ) -> dict[str, evidence.ValidatedTerminalEvidence]:
        rows = registry._registry_documents_for_evidence(registry_bytes)
        calls.append((
            sum(row.get("event") == "terminal" for row in rows),
            kwargs.get("evidence_overrides") is not None,
        ))
        return real_loader(root, registry_bytes, **kwargs)

    monkeypatch.setattr(registry, "_load_terminal_evidence_locked", count_loader)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    assert calls == [(0, False), (1, True)]

    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    rows = registry.read_attempt_registry(
        sealed["repo_root"],
        profile=sealed["profile"],
        binding=sealed["binding"],
    )
    terminal = rows[-1]
    digest = terminal["terminal_evidence_sha256"]
    evidence_path = registry._terminal_evidence_path(
        admission.shared_admission_root(sealed["repo_root"]), digest,
    )
    external_path = registry._external_evidence_path(
        admission.shared_admission_root(sealed["repo_root"]),
        sealed["external_evidence_sha256"],
    )
    data = evidence_path.read_bytes()
    assert evidence_path.name == f"{digest}.json"
    assert hashlib.sha256(data).hexdigest() == digest
    assert not data.endswith(b"\n")
    assert external_path.name == (
        f"{sealed['external_evidence_sha256']}.json"
    )
    assert hashlib.sha256(external_path.read_bytes()).hexdigest() == (
        sealed["external_evidence_sha256"]
    )
    assert path.read_bytes() == _bytes(rows)
    assert terminal["measurement_retry_reason"] is None
    assert terminal["terminal_status"] == "observed"


def test_durable_replay_binds_measurement_ordinal(tmp_path: Path) -> None:
    sealed = _sealed_v2_case(tmp_path, retry_ordinal=1)
    assert sealed["slot"].measurement_ordinal == 1
    assert sealed["slot"].attempt_ordinal == 0
    assert sealed["record"]["retry_ordinal"] == 1

    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )

    rows = registry.read_attempt_registry(
        sealed["repo_root"],
        profile=sealed["profile"],
        binding=sealed["binding"],
    )
    assert rows[-1]["terminal_status"] == "observed"


def test_durable_replay_rejects_recovery_ordinal_substitution(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path, retry_ordinal=1)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    root = admission.shared_admission_root(sealed["repo_root"])
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    rows = list(registry._registry_documents_for_evidence(path.read_bytes()))
    terminal = dict(rows[-1])
    old_path = registry._terminal_evidence_path(
        root, terminal["terminal_evidence_sha256"],
    )
    document = json.loads(old_path.read_text(encoding="utf-8"))
    document["campaign_record"]["retry_ordinal"] = (
        sealed["slot"].attempt_ordinal)
    payload = core.canonical_json_bytes(document)
    digest = hashlib.sha256(payload).hexdigest()
    registry._terminal_evidence_path(root, digest).write_bytes(payload)
    terminal["terminal_evidence_sha256"] = digest
    terminal["event_sha256"] = core.event_sha256(terminal)
    rows[-1] = terminal
    path.write_bytes(_bytes(tuple(rows)))

    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="campaign record differs from slot: retry_ordinal",
    ):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


def test_sealed_v2_issuer_rederives_external_component_digests(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    document = copy.deepcopy(sealed["draft"].document)
    document["probe_before_sha256"] = "f" * 64
    forged = object.__new__(evidence.SealedTerminalEvidenceDraft)
    object.__setattr__(
        forged, "_canonical_bytes", core.canonical_json_bytes(document),
    )
    object.__setattr__(
        forged,
        "_external_evidence_sha256",
        sealed["draft"]._external_evidence_sha256,
    )
    object.__setattr__(
        forged,
        "_launcher_origin_capability",
        sealed["draft"]._launcher_origin_capability,
    )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="external evidence differs from terminal: probe_before_sha256",
    ):
        registry.record_sealed_attempt_terminal(
            sealed["observation"], forged,
        )


def test_sealed_v2_replay_rederives_external_component_digests(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    root = admission.shared_admission_root(sealed["repo_root"])
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    rows = list(registry._registry_documents_for_evidence(path.read_bytes()))
    old_digest = rows[-1]["terminal_evidence_sha256"]
    old_path = registry._terminal_evidence_path(root, old_digest)
    document = json.loads(old_path.read_text(encoding="utf-8"))
    document["probe_before_sha256"] = "f" * 64
    payload = core.canonical_json_bytes(document)
    digest = hashlib.sha256(payload).hexdigest()
    registry._terminal_evidence_path(root, digest).write_bytes(payload)
    terminal = dict(rows[-1])
    terminal["terminal_evidence_sha256"] = digest
    terminal["event_sha256"] = core.event_sha256(terminal)
    rows[-1] = terminal
    path.write_bytes(_bytes(tuple(rows)))
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="external evidence differs from terminal: probe_before_sha256",
    ):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "primary_value",
        "raw_output_sha256",
        "report_sha256",
        "observation_sha256",
        "finished_at",
    ),
)
def test_sealed_v2_replay_rejects_each_unshadowed_row_projection_mismatch(
    tmp_path: Path,
    field_name: str,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    rows = list(registry._registry_documents_for_evidence(path.read_bytes()))
    terminal = dict(rows[-1])
    replacement: object = (
        999.0 if field_name == "primary_value"
        else "2099-01-01T00:00:00+00:00"
        if field_name == "finished_at"
        else "f" * 64
    )
    terminal[field_name] = replacement
    terminal["event_sha256"] = core.event_sha256(terminal)
    rows[-1] = terminal
    path.write_bytes(_bytes(tuple(rows)))
    with pytest.raises(
        (registry.S8BAttemptRegistryError, core.AttemptRegistryCoreError),
        match=rf"sealed evidence: {field_name}|terminal row differs.*{field_name}",
    ):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("outer-extra", "durable evidence is invalid"),
        ("binding-extra", "durable evidence is invalid"),
        ("trailing-lf", "LF-free canonical JSON bytes"),
        ("spaced-separator", "not one canonical object"),
    ),
)
def test_sealed_v2_replay_rejects_file_schema_and_canonical_mutations(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    root = admission.shared_admission_root(sealed["repo_root"])
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    rows = list(registry._registry_documents_for_evidence(path.read_bytes()))
    old_digest = rows[-1]["terminal_evidence_sha256"]
    old_path = registry._terminal_evidence_path(root, old_digest)
    document = json.loads(old_path.read_text(encoding="utf-8"))
    if mutation == "outer-extra":
        document["unexpected"] = True
        payload = core.canonical_json_bytes(document)
    elif mutation == "binding-extra":
        document["attempt_binding"]["unexpected"] = True
        payload = core.canonical_json_bytes(document)
    elif mutation == "trailing-lf":
        payload = old_path.read_bytes() + b"\n"
    else:
        payload = json.dumps(
            document, ensure_ascii=False, sort_keys=True, allow_nan=False,
        ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    mutated_path = registry._terminal_evidence_path(root, digest)
    mutated_path.write_bytes(payload)
    terminal = dict(rows[-1])
    terminal["terminal_evidence_sha256"] = digest
    terminal["event_sha256"] = core.event_sha256(terminal)
    rows[-1] = terminal
    path.write_bytes(_bytes(tuple(rows)))
    with pytest.raises(
        (registry.S8BAttemptRegistryError, core.AttemptRegistryCoreError),
        match=message,
    ):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


def test_sealed_v2_replay_requires_no_follow_regular_evidence_file(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    rows = registry.read_attempt_registry(
        sealed["repo_root"],
        profile=sealed["profile"],
        binding=sealed["binding"],
    )
    root = admission.shared_admission_root(sealed["repo_root"])
    path = registry._terminal_evidence_path(
        root, rows[-1]["terminal_evidence_sha256"],
    )
    target = path.with_name("evidence-target.json")
    target.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(target.name)
    with pytest.raises(
        (registry.S8BAttemptRegistryError, admission.HoldoutAdmissionError),
        match="regular file|symlink",
    ):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


def test_draft_promotion_rebuilds_bytes_and_rejects_foreign_issuer(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    draft = sealed["draft"]
    promoted = registry._promote_draft_to_validated(
        draft,
        classification_receipt_sha256="1" * 64,
        classification_event_sha256="2" * 64,
        observation_event_sha256="3" * 64,
        issuer_token=registry._TERMINAL_EVIDENCE_ISSUER_TOKEN,
    )
    assert promoted.canonical_bytes != draft.canonical_bytes
    assert len(promoted.document["attempt_binding"]) == 12
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="issuer differs",
    ):
        registry._promote_draft_to_validated(
            draft,
            classification_receipt_sha256="1" * 64,
            classification_event_sha256="2" * 64,
            observation_event_sha256="3" * 64,
            issuer_token=object(),
        )


def test_v2_profile_exact_gate_includes_retryable_reason_field() -> None:
    profile = _v2_authority_profile()
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="domain profile differs from frozen 8b semantics",
    ):
        registry._assert_profile(
            replace(profile, retryable_reason_field="failure_reason")
        )


def test_legacy_adapter_terminal_api_does_not_accept_evidence_arguments() -> None:
    parameters = inspect.signature(registry.record_attempt_terminal).parameters
    assert "measurement_retry_reason" not in parameters
    assert "terminal_evidence_sha256" not in parameters
    assert "evidence" not in parameters
    assert "evidence" in inspect.signature(
        registry.record_sealed_attempt_terminal
    ).parameters


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    (
        ("mode", "official"),
        ("cell_id", "different-cell"),
        ("records", 1),
        ("threads", 1),
        ("workload", {"wrong": True}),
    ),
)
def test_sealed_issuer_rechecks_durable_claim_identity(
    tmp_path: Path,
    field_name: str,
    replacement: object,
) -> None:
    sealed = _sealed_v2_case(
        tmp_path,
        durable_identity_override={field_name: replacement},
    )
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    before = path.read_bytes()
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=rf"durable claim.*{field_name}",
    ):
        registry.record_sealed_attempt_terminal(
            sealed["observation"], sealed["draft"],
        )
    assert path.read_bytes() == before
    assert not (
        admission.shared_admission_root(sealed["repo_root"])
        / "floor-attempt-registry-receipts/terminal-evidence"
    ).exists()


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    (
        ("holdout_id", "transplanted-holdout"),
        ("configuration_id", "transplanted-configuration"),
        ("retry_ordinal", 9),
    ),
)
def test_sealed_issuer_rejects_structural_reservation_identity_transplant(
    tmp_path: Path,
    field_name: str,
    replacement: object,
) -> None:
    sealed = _sealed_v2_case(
        tmp_path,
        durable_identity_override={field_name: replacement},
    )
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    before = path.read_bytes()
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=rf"campaign record differs from slot: {field_name}",
    ):
        registry.record_sealed_attempt_terminal(
            sealed["observation"], sealed["draft"],
        )
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    (
        ("holdout_id", "transplanted-holdout"),
        ("configuration_id", "transplanted-configuration"),
        ("retry_ordinal", 9),
    ),
)
def test_durable_replay_rejects_campaign_identity_transplant(
    tmp_path: Path,
    field_name: str,
    replacement: object,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    root = admission.shared_admission_root(sealed["repo_root"])
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    rows = list(registry._registry_documents_for_evidence(path.read_bytes()))
    old_digest = rows[-1]["terminal_evidence_sha256"]
    old_path = registry._terminal_evidence_path(root, old_digest)
    document = json.loads(old_path.read_text(encoding="utf-8"))
    document["campaign_record"][field_name] = replacement
    payload = core.canonical_json_bytes(document)
    digest = hashlib.sha256(payload).hexdigest()
    registry._terminal_evidence_path(root, digest).write_bytes(payload)
    terminal = dict(rows[-1])
    terminal["terminal_evidence_sha256"] = digest
    terminal["event_sha256"] = core.event_sha256(terminal)
    rows[-1] = terminal
    path.write_bytes(_bytes(tuple(rows)))
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match=rf"campaign record differs from slot: {field_name}",
    ):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


def test_classification_receipt_rechecks_terminal_source_digest(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(
        tmp_path,
        classification_external_override="f" * 64,
    )
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="classification external evidence differs from terminal sources",
    ):
        registry.record_sealed_attempt_terminal(
            sealed["observation"], sealed["draft"],
        )


def test_capture_failure_zero_launch_count_issues_and_replays(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path, capture_failure=True)
    assert sealed["draft"].document["launch_failures_count"] == 0
    assert sealed["draft"].document["failure"]["stage"] == "capture"
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    rows = registry.read_attempt_registry(
        sealed["repo_root"],
        profile=sealed["profile"],
        binding=sealed["binding"],
    )
    assert rows[-1]["terminal_status"] == "retryable-failure"


def test_durable_replay_rejects_capture_failure_with_nonzero_launch_count(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path, capture_failure=True)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    root = admission.shared_admission_root(sealed["repo_root"])
    path = registry.registry_path(
        sealed["repo_root"],
        freeze_sha256=sealed["binding"].freeze_sha256,
        protocol_sha256=sealed["binding"].protocol_sha256,
    )
    rows = list(registry._registry_documents_for_evidence(path.read_bytes()))
    old_digest = rows[-1]["terminal_evidence_sha256"]
    old_path = registry._terminal_evidence_path(root, old_digest)
    document = json.loads(old_path.read_text(encoding="utf-8"))
    document["launch_failures_count"] = 1
    document["launch_failures_sha256"] = hashlib.sha256(
        core.canonical_json_bytes([{
            "exception_type": "OSError",
            "errno": 5,
            "message": "contradictory launch failure",
        }])
    ).hexdigest()
    payload = core.canonical_json_bytes(document)
    digest = hashlib.sha256(payload).hexdigest()
    registry._terminal_evidence_path(root, digest).write_bytes(payload)
    terminal = dict(rows[-1])
    terminal["terminal_evidence_sha256"] = digest
    terminal["event_sha256"] = core.event_sha256(terminal)
    rows[-1] = terminal
    path.write_bytes(_bytes(tuple(rows)))
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="durable evidence is invalid",
    ):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


def test_sealed_profile_directly_checks_all_eleven_row_equalities(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    validated = registry._promote_draft_to_validated(
        sealed["draft"],
        classification_receipt_sha256="1" * 64,
        classification_event_sha256="2" * 64,
        observation_event_sha256="3" * 64,
        issuer_token=registry._TERMINAL_EVIDENCE_ISSUER_TOKEN,
    )
    projection = validated.projection
    binding = validated.document["attempt_binding"]
    row = {
        "terminal_status": projection.terminal_status,
        "failure_reason": projection.failure_reason,
        "measurement_retry_reason": projection.measurement_retry_reason,
        "primary_value": projection.primary_value,
        "raw_output_sha256": projection.raw_output_sha256,
        "report_sha256": projection.report_sha256,
        "observation_sha256": projection.observation_sha256,
        "classification_receipt_sha256": binding[
            "classification_receipt_sha256"
        ],
        "observation_start_event_sha256": binding[
            "observation_event_sha256"
        ],
        "finished_at": projection.finished_at,
        "terminal_evidence_sha256": validated.sha256,
    }
    profile8b._require_sealed_s8b_v2_terminal(row, validated)
    replacements = {
        "terminal_status": "retryable-failure",
        "failure_reason": "different-classification",
        "measurement_retry_reason": "measurement_execution_unavailable",
        "primary_value": 999.0,
        "raw_output_sha256": "4" * 64,
        "report_sha256": "5" * 64,
        "observation_sha256": "6" * 64,
        "classification_receipt_sha256": "7" * 64,
        "observation_start_event_sha256": "8" * 64,
        "finished_at": "2099-01-01T00:00:00+00:00",
        "terminal_evidence_sha256": "9" * 64,
    }
    for field_name, replacement in replacements.items():
        with pytest.raises(
            core.AttemptRegistryCoreError,
            match=rf"terminal row differs from sealed evidence: {field_name}$",
        ):
            profile8b._require_sealed_s8b_v2_terminal(
                {**row, field_name: replacement}, validated,
            )


@pytest.mark.parametrize("mutation", ("missing", "digest"))
def test_sealed_v2_replay_rejects_missing_or_digest_changed_file(
    tmp_path: Path,
    mutation: str,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    registry.record_sealed_attempt_terminal(
        sealed["observation"], sealed["draft"],
    )
    rows = registry.read_attempt_registry(
        sealed["repo_root"],
        profile=sealed["profile"],
        binding=sealed["binding"],
    )
    evidence_path = registry._terminal_evidence_path(
        admission.shared_admission_root(sealed["repo_root"]),
        rows[-1]["terminal_evidence_sha256"],
    )
    if mutation == "missing":
        evidence_path.unlink()
        message = "durable file is absent"
    else:
        evidence_path.write_bytes(evidence_path.read_bytes() + b" ")
        message = "bytes digest differs"
    with pytest.raises(registry.S8BAttemptRegistryError, match=message):
        registry.read_attempt_registry(
            sealed["repo_root"],
            profile=sealed["profile"],
            binding=sealed["binding"],
        )


def test_orphan_terminal_evidence_file_without_row_is_permitted(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    state = registry._require_handle(
        sealed["observation"], registry.CapturedObservation,
    )
    validated = registry._promote_draft_to_validated(
        sealed["draft"],
        classification_receipt_sha256=str(
            state.classification_receipt_sha256
        ),
        classification_event_sha256=str(state.classification_event_sha256),
        observation_event_sha256=str(state.observation_event_sha256),
        issuer_token=registry._TERMINAL_EVIDENCE_ISSUER_TOKEN,
    )
    root = admission.shared_admission_root(sealed["repo_root"])
    path = registry._terminal_evidence_path(root, validated.sha256)
    registry._publish_create_only(
        path,
        validated.canonical_bytes,
        logical_name=Path(*path.relative_to(root).parts).as_posix(),
        allow_exact_retry=True,
    )
    rows = registry.read_attempt_registry(
        sealed["repo_root"],
        profile=sealed["profile"],
        binding=sealed["binding"],
    )
    assert rows[-1]["event"] == "observation-start"
    assert path.is_file()


def test_terminal_evidence_publish_precedes_registry_staging_and_orphan_is_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    real_write = registry._write_staging
    writes: list[str] = []

    class StopBeforeRegistryReplace(RuntimeError):
        pass

    def stop_registry_staging(
        destination: Path,
        payload: bytes,
        *,
        logical_name: str,
    ) -> Path:
        writes.append(logical_name)
        if logical_name.endswith("registry.jsonl"):
            raise StopBeforeRegistryReplace(logical_name)
        return real_write(destination, payload, logical_name=logical_name)

    monkeypatch.setattr(registry, "_write_staging", stop_registry_staging)
    with pytest.raises(StopBeforeRegistryReplace):
        registry.record_sealed_attempt_terminal(
            sealed["observation"], sealed["draft"],
        )
    assert "terminal-evidence" in writes[0]
    assert writes[1].endswith("registry.jsonl")
    rows = registry.read_attempt_registry(
        sealed["repo_root"],
        profile=sealed["profile"],
        binding=sealed["binding"],
    )
    assert rows[-1]["event"] == "observation-start"
    evidence_root = (
        admission.shared_admission_root(sealed["repo_root"])
        / "floor-attempt-registry-receipts/terminal-evidence"
    )
    assert len(tuple(evidence_root.glob("*.json"))) == 1


def test_two_clean_v2_attempts_reserve_classify_and_begin_observation(
    tmp_path: Path,
) -> None:
    case = _two_clean_v2_attempt_case(tmp_path)
    transitions = []
    for index, attempt in enumerate(case["attempts"]):
        transition = _open_clean_v2_attempt(case, attempt)
        transitions.append(transition)
        if index == 0:
            registry.record_sealed_attempt_terminal(
                transition["observation"], transition["draft"],
            )

    assert all(
        type(transition["reserved"]) is registry.ReservedAttempt
        and type(transition["classified"]) is registry.ClassifiedAttempt
        and type(transition["observation"]) is registry.CapturedObservation
        for transition in transitions
    )
    rows = registry.read_attempt_registry(
        case["repo_root"],
        profile=case["profile"],
        binding=case["binding"],
    )
    assert [row["event"] for row in rows].count("start") == 2
    assert [row["event"] for row in rows].count("classification") == 2
    assert [row["event"] for row in rows].count("observation-start") == 2
    assert [row["event"] for row in rows].count("terminal") == 1


def test_second_clean_reservation_rejects_tampered_terminal_evidence(
    tmp_path: Path,
) -> None:
    case = _two_clean_v2_attempt_case(tmp_path)
    first = _open_clean_v2_attempt(case, case["attempts"][0])
    registry.record_sealed_attempt_terminal(
        first["observation"], first["draft"],
    )
    rows = registry.read_attempt_registry(
        case["repo_root"],
        profile=case["profile"],
        binding=case["binding"],
    )
    terminal = next(row for row in rows if row["event"] == "terminal")
    evidence_path = registry._terminal_evidence_path(
        admission.shared_admission_root(case["repo_root"]),
        terminal["terminal_evidence_sha256"],
    )
    path = registry.registry_path(
        case["repo_root"],
        freeze_sha256=case["binding"].freeze_sha256,
        protocol_sha256=case["binding"].protocol_sha256,
    )
    before = path.read_bytes()
    evidence_path.write_bytes(evidence_path.read_bytes() + b" ")
    with pytest.raises(
        registry.S8BAttemptRegistryError,
        match="terminal evidence bytes digest differs",
    ):
        _open_clean_v2_attempt(case, case["attempts"][1])
    assert path.read_bytes() == before


def test_plain_v2_profile_rejects_transition_after_sealed_terminal(
    tmp_path: Path,
) -> None:
    case = _two_clean_v2_attempt_case(tmp_path)
    first = _open_clean_v2_attempt(case, case["attempts"][0])
    registry.record_sealed_attempt_terminal(
        first["observation"], first["draft"],
    )
    path = registry.registry_path(
        case["repo_root"],
        freeze_sha256=case["binding"].freeze_sha256,
        protocol_sha256=case["binding"].protocol_sha256,
    )
    rows = registry._registry_documents_for_evidence(path.read_bytes())
    second_slot = case["attempts"][1]["slot"]
    with pytest.raises(
        core.AttemptRegistryCoreError,
        match=(
            r"^\[s8b-v2-terminal\] v2 terminal requires "
            r"the sealed evidence API$"
        ),
    ):
        core.reserve_attempt_slot(
            rows,
            profile=case["profile"],
            freeze_id=case["binding"].freeze_sha256,
            slot_id=case["profile"].slot_codec.slot_id(second_slot),
            binding=case["binding"],
            run_start_receipt_sha256=_RUN_START,
            process_identity=_PROCESS,
            started_at="2026-09-09T00:00:00+00:00",
        )


def test_private_validating_profile_rejects_capability_with_foreign_issuer(
    tmp_path: Path,
) -> None:
    sealed = _sealed_v2_case(tmp_path)
    validated = registry._promote_draft_to_validated(
        sealed["draft"],
        classification_receipt_sha256="1" * 64,
        classification_event_sha256="2" * 64,
        observation_event_sha256="3" * 64,
        issuer_token=registry._TERMINAL_EVIDENCE_ISSUER_TOKEN,
    )
    object.__setattr__(validated, "_issuer_token", object())
    private_profile = registry._terminal_validating_profile(
        sealed["profile"], {validated.sha256: validated},
    )
    with pytest.raises(registry.S8BAttemptRegistryError, match="issuer differs"):
        assert private_profile.terminal_row_validator is not None
        private_profile.terminal_row_validator({
            "terminal_evidence_sha256": validated.sha256,
        })


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))
