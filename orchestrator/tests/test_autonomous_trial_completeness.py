# -*- coding: utf-8 -*-
"""T-295 autonomous trial completeness gates and positive acceptance set."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import autonomous_trial_completeness as C  # noqa: E402
from orchestrator.campaign import ident                              # noqa: E402
from orchestrator.campaign import p3_autonomous_workload_trial as A  # noqa: E402
from orchestrator.campaign import layer3_report as L3                 # noqa: E402
from orchestrator.campaign import pipeline as P                       # noqa: E402
from orchestrator.campaign import trigger_gate_binding as TGB         # noqa: E402
from orchestrator.campaign.build_admission import (                  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.pin import CURRENT_PIN                    # noqa: E402
from orchestrator.campaign.layout import CampaignLayout              # noqa: E402
from orchestrator.campaign.model import CampaignConfig, Genome       # noqa: E402
from orchestrator.campaign.source_digest import (                    # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)


_ROLES = ("planner", "coder", "auditor", "critic")
_TRIAL_SCHEMA_VERSION = "p3-autonomous-workload-trial/v2"
_REPORT_SCHEMA_VERSION = "p3-autonomous-workload-trial-report/v2"
_LAYER3_SCHEMA_VERSION = "layer3-material-report/v3"
_LAYER3_GENERATOR_IDENTITY = "orchestrator.campaign.layer3_report"
_TRANSPORT_RECEIPT = {
    "schema_version": "claude-transport-receipt/v1",
    "mode": "explicit-http-proxy-env",
    "site": "PEGASUS_COMPUTE",
    "admitted_env_keys": ["http_proxy", "https_proxy"],
    "endpoint_values": {
        "http_proxy": "http://proxy-a.example:18080",
        "https_proxy": "http://proxy-b.example:18443",
    },
    "endpoint_values_sha256": (
        "8600267e0e37ea741979c88de241b910804defdb9ea147f4d0f5200a4ece3cfb"
    ),
    "policy_path": "tools/pegasus/policies/transport_v1.json",
    "policy_sha256": (
        "279fcecffc6e0c636171799fa7744f58495730698d3c75f9fb18534e1430797c"
    ),
    "source_tls_trust_override_keys": [],
    "forwarded_tls_trust_override_keys": [],
    "pbs_jobid": "987654.pegasus",
}

_GOLDEN_WORKLOADS = {
    "ycsb-a": {
        "rratio": "50",
        "input_sha256": "16520ed3194d4281327cbd9910d8f01b37e8e81348c108a0e5440f7a4978b8ac",
        "output_sha256": "f8353a0f5bc46f0c4206c02804953677f0b18bf0bb3ff3df3645c6889030fa33",
    },
    "ycsb-b": {
        "rratio": "95",
        "input_sha256": "d9741def7686cd940c79463c692d52eee386583d4494c5f29114d1667d999872",
        "output_sha256": "a60de8992beb5607a82d73714da5f59a7c464bbe039b870412bd22c0d2cdefd2",
    },
    "ycsb-c": {
        "rratio": "100",
        "input_sha256": "f51d9813da629b04fdc0bedcc5fdfab237cd1ef90ce630de7dbcbaa70e152013",
        "output_sha256": "7744886ad2d3b1a6e5fdefe969a8b527b1dfc997aec85459596dc3c89680c664",
    },
}
_PRE_T343_NO_BUILD_CAMPAIGN_IDS = {
    ("fixture-completeness", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-948f4c43"
    ),
    ("fixture-completeness", "ycsb-b"): (
        "p3-t178-ycsb-b-workload-conditioned-autonomous-025f59b3"
    ),
    ("fixture-completeness", "ycsb-c"): (
        "p3-t178-ycsb-c-workload-conditioned-autonomous-408051f9"
    ),
    ("trial-a", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-956b0051"
    ),
    ("trial-b", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-4395f9d1"
    ),
}
_T343_POLICY_BOUND_CAMPAIGN_IDS = {
    ("fixture-completeness", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-623e929a"
    ),
    ("fixture-completeness", "ycsb-b"): (
        "p3-t178-ycsb-b-workload-conditioned-autonomous-6225b974"
    ),
    ("fixture-completeness", "ycsb-c"): (
        "p3-t178-ycsb-c-workload-conditioned-autonomous-f967c773"
    ),
    ("trial-a", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-ebcbf812"
    ),
    ("trial-b", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-cf7c34b4"
    ),
}
_T428_POLICY_BOUND_CAMPAIGN_IDS = {
    ("fixture-completeness", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-67a4e01c"
    ),
    ("fixture-completeness", "ycsb-b"): (
        "p3-t178-ycsb-b-workload-conditioned-autonomous-1e4b78c7"
    ),
    ("fixture-completeness", "ycsb-c"): (
        "p3-t178-ycsb-c-workload-conditioned-autonomous-c3cccc72"
    ),
    ("trial-a", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-d56acecb"
    ),
    ("trial-b", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-b2c81ec8"
    ),
}
_T428_WORKLOAD_CAMPAIGN_EPOCHS = (
    (
        "ycsb-a",
        "p3-t178-ycsb-a-workload-conditioned-autonomous-623e929a",
        "p3-t178-ycsb-a-workload-conditioned-autonomous-67a4e01c",
    ),
    (
        "ycsb-b",
        "p3-t178-ycsb-b-workload-conditioned-autonomous-6225b974",
        "p3-t178-ycsb-b-workload-conditioned-autonomous-1e4b78c7",
    ),
    (
        "ycsb-c",
        "p3-t178-ycsb-c-workload-conditioned-autonomous-f967c773",
        "p3-t178-ycsb-c-workload-conditioned-autonomous-c3cccc72",
    ),
)
_LITERAL_ADMISSION_DECISION = {
    "schema_version": "campaign-artifact-admission-decision/v1",
    "classification": "admitted-new-schema",
    "admission_status": "admitted",
    "verification_status": "not-evaluated-by-overlay",
    "campaign_id": "literal-campaign",
    "campaign_path": "campaigns/literal-campaign",
    "campaign_lock_sha256": "1" * 64,
    "wal_sha256": "2" * 64,
    "policy_sha256": "3" * 64,
    "attempt_receipt_sha256s": ["4" * 64],
    "validator": {
        "identity": "orchestrator.campaign.artifact_admission",
        "sha256": "5" * 64,
    },
    "overlay": {
        "ledger_sha256": "6" * 64,
        "record_key": None,
    },
}
_DESCRIPTOR_SCHEMA_SHA256 = (
    "e60203b021a77a6d5a7d09bafd59525acd4173fa1ade099ec145a2b9d3ddc653"
)


def _golden_cell_metadata(
    campaign_parent: Path, workload: str, *, trial_id: str = "fixture-completeness",
) -> dict:
    golden = _GOLDEN_WORKLOADS[workload]
    read_ratio = int(golden["rratio"])
    campaign_id = _PRE_T343_NO_BUILD_CAMPAIGN_IDS[(trial_id, workload)]
    return {
        "workload_flags": {
            "ycsb_zipf_skew": "0.9",
            "ycsb_rratio": golden["rratio"],
            "ycsb_rmw": "0",
        },
        "descriptor": {
            "schema_version": "8b-v1",
            "source": "campaign_search_config_projection",
            "contention": {"label": "high", "skew": 0.9},
            "read_write": {"read_ratio_percent": read_ratio, "rmw": 0},
            "scale": {"records": 100_000, "threads": 4},
            "correctness": "serializable_legacy_and_s2",
            "objective": "maximize_throughput_tps",
        },
        "descriptor_binding": {
            "input_sha256": golden["input_sha256"],
            "output_sha256": golden["output_sha256"],
            "projection_version": "8b-descriptor-projection/v1",
            "schema_sha256": _DESCRIPTOR_SCHEMA_SHA256,
        },
        "campaign_id": campaign_id,
        "campaign_root": str(campaign_parent / "campaigns" / campaign_id),
        "admission_decision": {"admission_status": "not-applicable"},
    }


def _role_event(
    workload: str, role: str, seq: int, *, status: str = "valid",
    generation: int = 1, pre_audit: dict | None = None,
) -> dict:
    event = {
        "event": "role-attempt",
        "workload": workload,
        "generation": generation,
        "role": role,
        "attempt": 1,
        "invocation_id": f"{workload}.g{generation}.{role}",
        "seq": seq,
        "ts": f"2026-08-01T00:00:{seq:02d}+00:00",
        "status": status,
        "retry": False,
        "input_payload_sha256": hashlib.sha256(
            f"payload:{workload}:{generation}:{role}".encode("utf-8")
        ).hexdigest(),
        "descriptor_sha256": _GOLDEN_WORKLOADS[workload]["output_sha256"],
        "raw_response_path": f"/fixture/raw_{workload}.g{generation}.{role}.txt",
        "raw_response_sha256": hashlib.sha256(
            f"{workload}:{generation}:{role}".encode("utf-8")
        ).hexdigest(),
        "parsed": {"fixture_role": role},
        "provenance": {"fixture": True},
    }
    if status == "invalid":
        for key in ("raw_response_path", "raw_response_sha256", "parsed", "provenance"):
            event.pop(key)
        event.update({
            "error_type": "FixtureInvalid",
            "error": "fixture invalid",
            "error_artifacts": {},
        })
    elif status == "skipped":
        for key in ("raw_response_path", "raw_response_sha256", "parsed", "provenance"):
            event.pop(key)
        event.update({
            "skip_reason": "machine-pre-audit-rejection",
            "pre_audit": dict(pre_audit or {
                "passed": False,
                "forbidden_identifiers": [],
            }),
        })
    return event


def _start(run: Path, workloads: list[str], *, budget: int = 1) -> dict:
    return {
        "event": "run-start",
        "schema_version": _TRIAL_SCHEMA_VERSION,
        "trial_id": "fixture-completeness",
        "provider": "fixture",
        "workloads": list(workloads),
        "generation_budget_per_workload": budget,
        "max_wall_s": 60,
        "do_build": False,
        "performance_early_stop": False,
        "scientific_claim": False,
        "launch_admission": _launch_admission(workloads),
        "seq": 1,
        "ts": "2026-08-01T00:00:01+00:00",
    }


def _report(run: Path, workloads: list[str], *, budget: int = 1) -> dict:
    return {
        "schema_version": _REPORT_SCHEMA_VERSION,
        "trial_id": "fixture-completeness",
        "status": "complete",
        "started_at": "2026-08-01T00:00:00+00:00",
        "finished_at": "2026-08-01T00:01:00+00:00",
        "provider": "fixture",
        "do_build": False,
        "workloads_requested": list(workloads),
        "generation_budget_per_workload": budget,
        "stop_policy": {
            "fixed_generations": True,
            "performance_early_stop": False,
            "max_wall_s": 60,
        },
        "claim_scope": {"scientific_claim": False},
        "attempt_journal": str(run / "attempts.jsonl"),
        "launch_admission": _launch_admission(workloads),
        "cells": [],
    }


def _launch_admission(workloads: list[str]) -> dict:
    return {
        "mode": "explicit-unregistered-exploratory",
        "certifying": False,
        "reason_code": "explicit-unregistered-exploratory",
        "trial_id": "fixture-completeness",
        "workloads": list(workloads),
        "binding": None,
        "activation_report_digest_sha256": None,
    }


def _finish(run: Path, status: str, seq: int) -> dict:
    return {
        "event": "run-finish",
        "status": status,
        "report": str(run / "report.json"),
        "seq": seq,
        "ts": f"2026-08-01T00:01:{seq:02d}+00:00",
    }


def _persist(run: Path, events: list[dict], report: dict) -> None:
    run.mkdir(parents=True, exist_ok=True)
    journal_bytes = b"".join(
        json.dumps(
            event, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8") + b"\n"
        for event in events
    )
    (run / "attempts.jsonl").write_bytes(journal_bytes)
    report["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()
    (run / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _complete_trial(
    tmp_path: Path, *, workloads: tuple[str, ...] = ("ycsb-a",),
):
    run = tmp_path / "run"
    requested = list(workloads)
    report = _report(run, requested)
    events = [_start(run, requested)]
    seq = 2
    for workload in requested:
        roles = {}
        for role in _ROLES:
            event = _role_event(workload, role, seq)
            events.append(event)
            roles[role] = copy.deepcopy(event)
            seq += 1
        report["cells"].append({
            "workload": workload,
            **_golden_cell_metadata(run, workload),
            "generations": [{
                "generation": 1,
                "roles": roles,
                "preview": {
                    "passed": True,
                    "forbidden_identifiers": [],
                },
                "harness": {
                    "outcome": "dry-pass",
                    "variant": None,
                    "stop_reason": "continue",
                    "iteration": 1,
                    "ran": True,
                },
                "outcome": "dry-pass",
            }],
            "stop_reason": "fixed-generation-budget",
        })
    events.append(_finish(run, "complete", seq))
    _persist(run, events, report)
    return run, events, report


def _pre_audit_trial(tmp_path: Path):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    events = [_start(run, ["ycsb-a"])]
    roles = {}
    for seq, role in enumerate(("planner", "coder"), 2):
        event = _role_event("ycsb-a", role, seq)
        events.append(event)
        roles[role] = copy.deepcopy(event)
    preview = {"passed": False, "forbidden_identifiers": []}
    auditor = _role_event(
        "ycsb-a", "auditor", 4, status="skipped", pre_audit=preview,
    )
    events.append(auditor)
    roles["auditor"] = copy.deepcopy(auditor)
    critic = _role_event("ycsb-a", "critic", 5)
    events.append(critic)
    roles["critic"] = copy.deepcopy(critic)
    report["cells"] = [{
        "workload": "ycsb-a",
        **_golden_cell_metadata(run, "ycsb-a"),
        "generations": [{
            "generation": 1,
            "roles": roles,
            "preview": preview,
            "harness": {
                "outcome": "pre-audit-reject",
                "variant": None,
                "stop_reason": "continue",
                "iteration": 1,
                "ran": True,
            },
            "outcome": "pre-audit-reject",
        }],
        "stop_reason": "fixed-generation-budget",
    }]
    events.append(_finish(run, "complete", 6))
    _persist(run, events, report)
    return run, events, report


def _role_invalid_trial(tmp_path: Path):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    report["status"] = "partial"
    invalid = _role_event("ycsb-a", "planner", 2, status="invalid")
    report["cells"] = [{
        "workload": "ycsb-a",
        **_golden_cell_metadata(run, "ycsb-a"),
        "generations": [{
            "generation": 1,
            "roles": {"planner": copy.deepcopy(invalid)},
            "outcome": "planner-invalid",
        }],
        "stop_reason": "role-invalid",
    }]
    events = [_start(run, ["ycsb-a"]), invalid, _finish(run, "partial", 3)]
    _persist(run, events, report)
    return run, events, report


def _provider_init_trial(tmp_path: Path):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a", "ycsb-b"])
    report["status"] = "partial"
    report["fatal_error"] = {"type": "ProviderError", "message": "init failed"}
    error = {
        "event": "provider-init-error",
        "type": "ProviderError",
        "message": "init failed",
        "seq": 2,
        "ts": "2026-08-01T00:00:02+00:00",
    }
    events = [
        _start(run, ["ycsb-a", "ycsb-b"]), error,
        _finish(run, "partial", 3),
    ]
    _persist(run, events, report)
    return run, events, report


def _generation_wall_trial(tmp_path: Path):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    report["status"] = "partial"
    report["cells"] = [{
        "workload": "ycsb-a",
        **_golden_cell_metadata(run, "ycsb-a"),
        "generations": [],
        "stop_reason": "supervisor-wall-budget",
    }]
    events = [_start(run, ["ycsb-a"]), _finish(run, "partial", 2)]
    _persist(run, events, report)
    return run, events, report


def _transport_admitted_trial(tmp_path: Path):
    run, events, report = _provider_init_trial(tmp_path)
    receipt = copy.deepcopy(_TRANSPORT_RECEIPT)
    for event in events:
        event["seq"] += 1
    admission = {
        "event": "transport-admission",
        "transport_receipt": copy.deepcopy(receipt),
        "seq": 1,
        "ts": "2026-08-01T00:00:01+00:00",
    }
    events.insert(0, admission)
    for event in events[2:]:
        event["transport_receipt"] = copy.deepcopy(receipt)
    report["provider"] = "claude-headless"
    events[1]["provider"] = "claude-headless"
    report["transport_receipt"] = copy.deepcopy(receipt)
    _persist(run, events, report)
    return run, events, report


def _verify(run: Path, report: dict) -> None:
    C.assert_autonomous_trial_completeness(
        report=report, attempt_journal=run / "attempts.jsonl",
    )


def test_p1_complete_three_cell_fixture_passes(tmp_path) -> None:
    run, _events, report = _complete_trial(
        tmp_path, workloads=("ycsb-a", "ycsb-b", "ycsb-c"),
    )
    _verify(run, report)
    C.verify_autonomous_trial_files(run / "attempts.jsonl", run / "report.json")


def test_p2_pre_audit_reject_journaled_skip_passes(tmp_path) -> None:
    run, _events, report = _pre_audit_trial(tmp_path)
    _verify(run, report)


def test_p3_role_invalid_partial_passes(tmp_path) -> None:
    run, _events, report = _role_invalid_trial(tmp_path)
    _verify(run, report)


def test_p4_provider_init_error_with_empty_cells_passes(tmp_path) -> None:
    run, _events, report = _provider_init_trial(tmp_path)
    _verify(run, report)


def test_p5_generation_boundary_wall_budget_empty_generations_passes(tmp_path) -> None:
    run, _events, report = _generation_wall_trial(tmp_path)
    _verify(run, report)


def test_transport_admission_bound_shape_and_projection_passes(tmp_path) -> None:
    run, _events, report = _transport_admitted_trial(tmp_path)
    _verify(run, report)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("duplicate", r"transport-admission may occur at most once"),
        (
            "after-run-start",
            r"transport-admission must occur immediately before run-start and role attempts",
        ),
        (
            "missing-receipt",
            r"transport-admission fields must match the producer exact set",
        ),
        (
            "wrong-receipt-type",
            r"transport-admission\.transport_receipt must be an object",
        ),
        (
            "report-mismatch",
            r"transport-admission receipt does not match report projection",
        ),
        (
            "report-missing",
            r"transport-admission and report transport_receipt must occur together",
        ),
    ],
    ids=[
        "duplicate",
        "after-run-start",
        "missing-receipt",
        "wrong-receipt-type",
        "report-mismatch",
        "report-missing",
    ],
)
def test_transport_admission_binding_mutations_are_rejected(
    tmp_path, mutation, expected,
) -> None:
    run, events, report = _transport_admitted_trial(tmp_path)
    if mutation == "duplicate":
        events.insert(1, copy.deepcopy(events[0]))
    elif mutation == "after-run-start":
        events[0], events[1] = events[1], events[0]
    elif mutation == "missing-receipt":
        events[0].pop("transport_receipt")
    elif mutation == "wrong-receipt-type":
        events[0]["transport_receipt"] = "not-an-object"
    elif mutation == "report-mismatch":
        report["transport_receipt"]["pbs_jobid"] = "987655.pegasus"
    else:
        report.pop("transport_receipt")
    for seq, event in enumerate(events, 1):
        event["seq"] = seq
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[transport-admission\] {expected}$",
    ):
        _verify(run, report)


def test_pre_workload_wall_budget_terminal_projection_passes(tmp_path) -> None:
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    report["status"] = "partial"
    report["fatal_error"] = {
        "type": "SupervisorWallBudget",
        "message": "wall budget expired before the next workload",
    }
    wall = {
        "event": "supervisor-wall-budget", "workload": "ycsb-a",
        "seq": 2, "ts": "2026-08-01T00:00:02+00:00",
    }
    events = [_start(run, ["ycsb-a"]), wall, _finish(run, "partial", 3)]
    _persist(run, events, report)
    _verify(run, report)


def test_empty_requested_complete_report_is_rejected(tmp_path) -> None:
    run = tmp_path / "run"
    report = _report(run, [])
    events = [_start(run, []), _finish(run, "complete", 2)]
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[workload-coverage\] workloads_requested is not a unique string list$",
    ):
        _verify(run, report)


@pytest.mark.parametrize(
    ("target", "field", "expected"),
    [
        ("report", "trial_id", r"report\.trial_id is not a non-empty string"),
        ("start", "provider", r"provider is outside the producer closed set"),
        ("report", "do_build", r"do_build must be a bool in report and run-start"),
        (
            "start", "max_wall_s",
            r"run-start\.max_wall_s must be a positive int",
        ),
        (
            "report", "generation_budget_per_workload",
            r"generation budget must be a positive int in report and run-start",
        ),
        (
            "role", "input_payload_sha256",
            r"journal role attempt is missing required fields: \['input_payload_sha256'\]",
        ),
        (
            "role", "raw_response_path",
            r"journal role attempt valid event is missing fields: \['raw_response_path'\]",
        ),
    ],
)
def test_missing_envelope_and_role_fields_are_rejected(
    tmp_path, target, field, expected,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    if target == "report":
        report.pop(field)
    elif target == "start":
        events[0].pop(field)
    else:
        events[1].pop(field)
        report["cells"][0]["generations"][0]["roles"]["planner"].pop(field)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[(?:run-envelope|role-event-shape)\] {expected}$",
    ):
        _verify(run, report)


@pytest.mark.parametrize("harness", [None, {}])
def test_fixed_budget_rejects_null_or_empty_harness(tmp_path, harness) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["cells"][0]["generations"][0]["harness"] = harness
    _persist(run, events, report)
    suffix = "is not an object" if harness is None else "is empty"
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[state-machine\] ycsb-a\.g1\.harness {suffix}$",
    ):
        _verify(run, report)


def test_fixed_budget_rejects_impossible_invalid_role_history(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    invalid_planner = _role_event("ycsb-a", "planner", 2, status="invalid")
    events[1] = invalid_planner
    report["cells"][0]["generations"][0]["roles"]["planner"] = copy.deepcopy(
        invalid_planner
    )
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[state-machine\] fixed-budget cell 'ycsb-a' has non-valid role history$",
    ):
        _verify(run, report)


@pytest.mark.parametrize(("field", "value", "message"), [
    ("attempt", 2, r"journal role attempt\.attempt must be exactly 1"),
    ("retry", True, r"journal role attempt\.retry must be false"),
])
def test_attempt_policy_requires_attempt_one_and_retry_false(
    tmp_path, field, value, message,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    events[1][field] = value
    report["cells"][0]["generations"][0]["roles"]["planner"][field] = value
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[attempt-policy\] {message}$",
    ):
        _verify(run, report)


def test_unknown_stop_reason_is_rejected(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["cells"][0]["stop_reason"] = "fixture-invented-success"
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[state-machine\] cell 'ycsb-a' has unknown stop_reason: "
            r"'fixture-invented-success'$"
        ),
    ):
        _verify(run, report)


@pytest.mark.parametrize("target", ["report", "start"])
def test_report_and_run_start_schema_versions_are_required(tmp_path, target) -> None:
    run, events, report = _complete_trial(tmp_path)
    value = report if target == "report" else events[0]
    value.pop("schema_version")
    _persist(run, events, report)
    expected = (
        r"report\.schema_version does not match producer version"
        if target == "report"
        else r"run-start\.schema_version does not match producer version"
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[run-envelope\] {expected}$",
    ):
        _verify(run, report)


def test_schema_version_v2_is_required_and_v1_is_rejected(tmp_path) -> None:
    assert A.SCHEMA_VERSION == "p3-autonomous-workload-trial/v2"
    assert A.REPORT_SCHEMA_VERSION == "p3-autonomous-workload-trial-report/v2"
    assert _TRIAL_SCHEMA_VERSION == "p3-autonomous-workload-trial/v2"
    assert _REPORT_SCHEMA_VERSION == "p3-autonomous-workload-trial-report/v2"
    for target in ("start", "report"):
        run, events, report = _complete_trial(tmp_path / target)
        if target == "start":
            events[0]["schema_version"] = "p3-autonomous-workload-trial/v1"
            expected = "run-start.schema_version does not match producer version"
        else:
            report["schema_version"] = "p3-autonomous-workload-trial-report/v1"
            expected = "report.schema_version does not match producer version"
        _persist(run, events, report)
        with pytest.raises(
            C.AutonomousTrialCompletenessError,
            match=rf"\[run-envelope\] {expected}$",
        ):
            _verify(run, report)


def test_producer_cell_metadata_and_descriptor_binding_are_required(
    tmp_path,
) -> None:
    run, events, report = _complete_trial(tmp_path / "missing-workload-flags")
    report["cells"][0].pop("workload_flags")
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[cell-metadata\] cells\[0\] is missing required fields: "
            r"\['workload_flags'\]$"
        ),
    ):
        _verify(run, report)

    bad_values = {
        "workload_flags": None,
        "descriptor": [],
        "descriptor_binding": "not-a-binding",
        "campaign_id": {},
        "campaign_root": 7,
    }
    for field, bad_value in bad_values.items():
        run, events, report = _complete_trial(tmp_path / field)
        report["cells"][0][field] = bad_value
        _persist(run, events, report)
        with pytest.raises(
            C.AutonomousTrialCompletenessError,
            match=r"\[cell-metadata\] ",
        ):
            _verify(run, report)

    run, events, report = _complete_trial(tmp_path / "descriptor-hash")
    events[1]["descriptor_sha256"] = "0" * 64
    report["cells"][0]["generations"][0]["roles"]["planner"][
        "descriptor_sha256"
    ] = "0" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[descriptor-binding\] ycsb-a\.g1\.planner\.descriptor_sha256 "
            r"differs from cell binding$"
        ),
    ):
        _verify(run, report)

    run, events, report = _complete_trial(tmp_path / "empty-provenance")
    events[1]["provenance"] = {}
    report["cells"][0]["generations"][0]["roles"]["planner"]["provenance"] = {}
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-event-shape\] journal role attempt\.provenance is empty$",
    ):
        _verify(run, report)


def test_cell_metadata_is_required_after_generation_started(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    for field in (
        "workload_flags", "descriptor", "descriptor_binding",
        "campaign_id", "campaign_root",
    ):
        report["cells"][0].pop(field)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[cell-metadata\] cells\[0\] is missing required fields: "
            r"\['campaign_id', 'campaign_root', 'descriptor', "
            r"'descriptor_binding', 'workload_flags'\]$"
        ),
    ):
        _verify(run, report)


def test_cell_metadata_is_required_for_non_error_empty_cell(tmp_path) -> None:
    run, events, report = _generation_wall_trial(tmp_path)
    for field in (
        "workload_flags", "descriptor", "descriptor_binding",
        "campaign_id", "campaign_root",
    ):
        report["cells"][0].pop(field)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[cell-metadata\] cells\[0\] is missing required fields: "
            r"\['campaign_id', 'campaign_root', 'descriptor', "
            r"'descriptor_binding', 'workload_flags'\]$"
        ),
    ):
        _verify(run, report)


def test_verifier_rejects_generation_budget_above_current_producer_limit(
    tmp_path,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    events[0]["generation_budget_per_workload"] = 2
    report["generation_budget_per_workload"] = 2
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[run-envelope\] generation budget exceeds the current "
            r"producer-approved limit$"
        ),
    ):
        _verify(run, report)


def test_all_producer_driver_stop_reasons_pass(tmp_path) -> None:
    assert A.DRIVER_STOP_REASONS == {
        "continue", "converged", "reverse-exhausted",
        "budget-iterations", "budget-walltime",
    }
    for reason in sorted(A.DRIVER_STOP_REASONS):
        run, events, report = _complete_trial(tmp_path / reason)
        report["cells"][0]["generations"][0]["harness"]["stop_reason"] = reason
        report["cells"][0]["stop_reason"] = (
            "fixed-generation-budget" if reason == "continue" else reason
        )
        _persist(run, events, report)
        _verify(run, report)


def test_role_invalid_rejects_prior_terminal_harness_stop(
    tmp_path, monkeypatch,
) -> None:
    monkeypatch.setattr(A, "MAX_APPROVED_GENERATIONS", 2)
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"], budget=2)
    report["status"] = "partial"
    events = [_start(run, ["ycsb-a"], budget=2)]
    roles = {}
    for seq, role in enumerate(_ROLES, 2):
        event = _role_event("ycsb-a", role, seq, generation=1)
        events.append(event)
        roles[role] = copy.deepcopy(event)
    invalid = _role_event("ycsb-a", "planner", 6, status="invalid", generation=2)
    events.append(invalid)
    report["cells"] = [{
        "workload": "ycsb-a",
        **_golden_cell_metadata(run, "ycsb-a"),
        "generations": [
            {
                "generation": 1,
                "roles": roles,
                "harness": {
                    "outcome": "fixture-terminal",
                    "variant": None,
                    "stop_reason": "converged",
                    "iteration": 1,
                    "ran": True,
                },
                "outcome": "fixture-terminal",
            },
            {
                "generation": 2,
                "roles": {"planner": copy.deepcopy(invalid)},
                "outcome": "planner-invalid",
            },
        ],
        "stop_reason": "role-invalid",
    }]
    events.append(_finish(run, "partial", 7))
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[state-machine\] role-invalid cell 'ycsb-a' has a terminal "
            r"prior harness stop$"
        ),
    ):
        _verify(run, report)


def test_auditor_skip_is_journaled_and_has_no_carve_out(tmp_path) -> None:
    def preview(_coder, *, sub):
        return {
            "passed": False,
            "working_diff": "fixture rejected diff",
            "diff_digest": hashlib.sha256(b"fixture rejected diff").hexdigest(),
            "subtype": "fixture",
            "reason": "fixture pre-audit rejection",
            "forbidden_identifiers": [],
        }

    def drive(*args, **kwargs):
        return {
            "outcome": "pre-audit-reject",
            "variant": None,
            "stop_reason": "continue",
            "iteration": 1,
            "ran": True,
        }

    run = tmp_path / "run"
    report = A.run_trial(
        trial_id="journaled-auditor-skip",
        workloads=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=run,
        sub="/unused",
        do_build=False,
        preview=preview,
        drive=drive,
        allow_unregistered_exploratory=True,
    )
    auditor = report["cells"][0]["generations"][0]["roles"]["auditor"]
    assert auditor["event"] == "role-attempt"
    assert auditor["status"] == "skipped"
    disk_events = [
        json.loads(line)
        for line in (run / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert auditor in disk_events

    report["cells"][0]["generations"][0]["roles"]["auditor"] = {
        "status": "skipped",
        "reason": "machine-pre-audit-rejection",
    }
    _persist(run, disk_events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[report-role-shape\] ycsb-a\.g1\.auditor "
            r"is not a journaled role event$"
        ),
    ):
        _verify(run, report)


def test_m1_unknown_journal_event_is_rejected_only_by_closed_set(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    events[-1]["seq"] = 7
    events.insert(-1, {"event": "unknown-event", "seq": 6, "ts": "fixture"})
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[closed-event-set\] journal event 5 has unknown kind: 'unknown-event'$",
    ):
        _verify(run, report)


def test_m2_full_role_record_mismatch_is_rejected_by_multiset(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["cells"][0]["generations"][0]["roles"]["planner"][
        "raw_response_sha256"
    ] = "f" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-bijection\] journal/report role-attempt multisets differ$",
    ):
        _verify(run, report)


def test_m3_journal_is_reread_from_disk_not_report_memory(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    events[1]["raw_response_sha256"] = "e" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[role-bijection\] journal/report role-attempt multisets differ$",
    ):
        _verify(run, report)


def test_m4a_producer_supervisor_error_preserves_constructed_generation(
    tmp_path, monkeypatch,
) -> None:
    def broken_preview(coder, *, sub):
        raise RuntimeError("preview fixture failure")

    monkeypatch.setattr(A, "assert_autonomous_trial_completeness", lambda **kwargs: None)
    run = tmp_path / "run"
    report = A.run_trial(
        trial_id="partial-generation",
        workloads=["ycsb-a", "ycsb-b"],
        generations=1,
        provider_kind="fixture",
        run_root=run,
        sub="/unused",
        do_build=False,
        preview=broken_preview,
        allow_unregistered_exploratory=True,
    )
    generation = report["cells"][0]["generations"][0]
    assert generation["generation"] == 1
    assert set(generation["roles"]) == {"planner", "coder"}
    assert report["fatal_error"] == {
        "type": "RuntimeError", "message": "preview fixture failure",
    }


def _supervisor_error_trial(
    tmp_path: Path, *, roles: tuple[str, ...] = ("planner", "coder"),
    generation: int = 1,
):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    report["status"] = "partial"
    error_value = {"type": "FixtureError", "message": "fixture supervisor error"}
    report["fatal_error"] = dict(error_value)
    events = [_start(run, ["ycsb-a"])]
    report_roles = {}
    for seq, role in enumerate(roles, 2):
        event = _role_event("ycsb-a", role, seq, generation=generation)
        events.append(event)
        report_roles[role] = copy.deepcopy(event)
    report["cells"] = [{
        "workload": "ycsb-a",
        **_golden_cell_metadata(run, "ycsb-a"),
        "generations": [{
            "generation": generation,
            "roles": report_roles,
        }],
        "stop_reason": "supervisor-error",
        "error": dict(error_value),
    }]
    next_seq = len(events) + 1
    events.append({
        "event": "supervisor-error",
        "workload": "ycsb-a",
        **error_value,
        "seq": next_seq,
        "ts": f"2026-08-01T00:00:{next_seq:02d}+00:00",
    })
    events.append(_finish(run, "partial", next_seq + 1))
    _persist(run, events, report)
    return run, events, report


def test_m4b_verifier_rejects_omitted_constructed_generation(tmp_path) -> None:
    run, events, report = _supervisor_error_trial(tmp_path)
    report["cells"][0]["generations"] = []
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[state-machine\] journal role attempts do not follow "
            r"report role state order$"
        ),
    ):
        _verify(run, report)


def test_m5_run_start_workload_order_mismatch_is_rejected(tmp_path) -> None:
    run, events, report = _complete_trial(
        tmp_path, workloads=("ycsb-a", "ycsb-b"),
    )
    events[0]["workloads"] = ["ycsb-b", "ycsb-a"]
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[run-envelope\] run-start workloads do not match report order$",
    ):
        _verify(run, report)


@pytest.mark.parametrize("mutation", ["missing-report", "start-mismatch"])
def test_launch_admission_is_required_and_exact_between_start_and_report(
    tmp_path: Path,
    mutation: str,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    if mutation == "missing-report":
        report.pop("launch_admission")
    else:
        events[0]["launch_admission"]["trial_id"] = "other-trial"
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[launch-admission\] ",
    ):
        _verify(run, report)


def test_m6_unexplained_zero_attempt_cell_omission_is_rejected(tmp_path) -> None:
    run, events, report = _generation_wall_trial(tmp_path)
    report["cells"] = []
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[workload-coverage\] requested workload suffix is unexplained$",
    ):
        _verify(run, report)


def test_m7_journaled_auditor_skip_requires_pre_audit_evidence(tmp_path) -> None:
    run, events, report = _pre_audit_trial(tmp_path)
    no_reject = {"passed": True, "forbidden_identifiers": []}
    events[3]["pre_audit"] = copy.deepcopy(no_reject)
    report["cells"][0]["generations"][0]["preview"] = copy.deepcopy(no_reject)
    report["cells"][0]["generations"][0]["roles"]["auditor"][
        "pre_audit"
    ] = copy.deepcopy(no_reject)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.pre_audit "
            r"does not prove rejection$"
        ),
    ):
        _verify(run, report)


def test_eventless_non_auditor_role_is_rejected(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["cells"][0]["generations"][0]["roles"]["planner"] = {
        "status": "skipped", "reason": "not-a-role-attempt",
    }
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[report-role-shape\] ycsb-a\.g1\.planner "
            r"is not a journaled role event$"
        ),
    ):
        _verify(run, report)


def test_state_machine_rejects_noncontiguous_generations(tmp_path) -> None:
    run, events, report = _supervisor_error_trial(tmp_path, generation=2)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[state-machine\] cell 'ycsb-a' generations are not contiguous from 1$",
    ):
        _verify(run, report)


def test_state_machine_rejects_nonprefix_roles(tmp_path) -> None:
    run, events, report = _supervisor_error_trial(
        tmp_path, roles=("planner", "auditor"),
    )
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[state-machine\] cell 'ycsb-a' generation 1 roles are not an "
            r"allowed prefix$"
        ),
    ):
        _verify(run, report)


def test_m9_logical_id_diagnostic_pin_has_no_coverage_failure() -> None:
    first = _role_event("ycsb-a", "planner", 2)
    duplicate = copy.deepcopy(first)
    duplicate["seq"] = 3
    duplicate["ts"] = "2026-08-01T00:00:03+00:00"
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[logical-id\] journal has a duplicate logical role attempt ID$",
    ):
        C._require_unique_attempts([first, duplicate], side="journal")


def _test_wal_ref(record: dict) -> str:
    canonical = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return "wal:" + hashlib.sha256(canonical).hexdigest()


def _file_ref(path: Path, root: Path) -> dict:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _layer3_campaign(
    tmp_path: Path, *, trial_id: str = "fixture-completeness",
    workload: str = "ycsb-a", output_root: Path | None = None,
):
    output_root = output_root or tmp_path / "output"
    metadata = _golden_cell_metadata(output_root, workload, trial_id=trial_id)
    workload_flags = metadata["workload_flags"]
    descriptor = metadata["descriptor"]
    descriptor_binding = metadata["descriptor_binding"]
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    campaign_cfg = CampaignConfig(
        spec_slug=f"p3-t178-{workload}",
        search_tag="workload-conditioned-autonomous",
        spec_content=(
            "T-178 exploratory YCSB A/B/C workload-conditioned unattended synthesis. "
            "Python invokes fresh projected planner/coder/auditor/critic roles; existing "
            "trigger-gating quarantine/correctness/performance harness remains authoritative. "
            "Fixed generations, no performance-target early stop, no formal descriptor claim."
        ),
        ccbench_commit=CURRENT_PIN,
        search_config={
            "axis": "silo-backoff-trigger-gating",
            "descriptor_schema": "8b-v1",
            "descriptor_sha256": descriptor_binding["output_sha256"],
            "generation_budget": 1,
            "pilot_scope": "exploratory-ycsb-abc",
            "records": 100_000,
            "reflux": "on",
            "scale": "silo",
            "stop_policy": "fixed-generations-no-performance-early-stop",
            "threads": 4,
            "trigger_gate_binding_schema": TGB.SCHEMA_VERSION,
            "verify": "legacy+s2",
            "workload": workload,
            "ycsb": workload_flags,
            "build_admission": dict(context.policy.as_preimage()),
        },
        trial=f"{trial_id}-{workload}",
    )
    campaign_id = str(ident.campaign_id(campaign_cfg))
    assert campaign_id == _T428_POLICY_BOUND_CAMPAIGN_IDS[(trial_id, workload)]
    metadata["campaign_id"] = campaign_id
    metadata["campaign_root"] = str(output_root / "campaigns" / campaign_id)
    campaign = output_root / "campaigns" / campaign_id
    layout = CampaignLayout(root=str(campaign)).ensure()
    assert ident.ensure_campaign_identity(
        campaign_cfg, layout, admission_policy=context.policy,
    )
    assert Path(layout.lock_file).read_bytes() == \
        ident.canonical_preimage(campaign_cfg).encode("utf-8")
    state_path = campaign / "loop_state.json"
    state_path.write_text(
        json.dumps({"whiteboard": []}), encoding="utf-8",
    )
    genome_value = Genome("fixture", {})
    genome = genome_value.canonical()
    variant = P.variant_id(genome_value)
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(tmp_path.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(genome.encode()).hexdigest(),
        src_token="stock",
        source_bytes_sha256="a" * 64,
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )
    receipt = derive_build_admission(context, evidence).as_wal_receipt()
    attempt_id = "attempt-1"
    binding = TGB.TriggerGateBinding(
        mask=0,
        predicate_sha256=TGB.expected_predicate_sha256(0),
        nonce="1" * 64,
        source=TGB.SourceBinding(
            src_token=evidence.src_token,
            source_bytes_sha256=evidence.source_bytes_sha256,
        ),
    )
    binding_commitment = TGB.commitment(binding)
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    }
    records = [
        {
            "ts": 0.5, "stage": TGB.WAL_RECORD_STAGE, "variant": variant,
            "env_tag": "fixture-env", "payload": {
                "build_attempt_id": attempt_id,
                "trigger_gate_binding": TGB.to_record(binding),
            },
        },
        {
            "ts": 1.0, "stage": "build_start", "variant": variant,
            "env_tag": "fixture-env", "payload": {
                "build_attempt_id": attempt_id,
                "genome": genome,
                "src_token": "stock",
                "build_admission": receipt,
                "build_admission_receipt_sha256": receipt["receipt_sha256"],
                "trigger_gate_binding_commitment": binding_commitment,
            },
        },
        {
            "ts": 2.0, "stage": "build_done", "variant": variant,
            "env_tag": "fixture-env", "payload": dict(terminal),
        },
        {
            "ts": 3.0, "stage": "bench_done", "variant": variant,
            "env_tag": "fixture-env",
            "payload": {
                "tps": [1.0], "median_tps": 1.0, "cv": 0.0, "rounds": 1,
                "leading_indicators": {},
            },
        },
        {
            "ts": 4.0, "stage": "commit", "variant": variant,
            "env_tag": "fixture-env", "payload": dict(terminal),
        },
    ]
    wal_path = campaign / "runs" / "wal.jsonl"
    wal_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    (campaign / "reports" / "p3_s8a_trigger_loop_provenance.json").write_text(
        json.dumps({
            "entries": {
                "fixture": {
                    "variant": variant,
                    "build_attempt_id": attempt_id,
                    "trigger_gate_binding_commitment": binding_commitment,
                },
            },
        }),
        encoding="utf-8",
    )
    persisted = L3.build_report(
        campaign, generated_from_head="a" * 40, output_root=output_root,
    )
    persisted_path = campaign / "reports" / "layer3_report.json"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    cell = {
        "workload": workload,
        **metadata,
        "admission_decision": copy.deepcopy(persisted["admission_decision"]),
        "generations": [],
        "stop_reason": "supervisor-error",
    }
    return output_root, campaign, persisted_path, persisted, cell


def _campaign_report(cell: dict, *, trial_id: str = "fixture-completeness") -> dict:
    return {
        "trial_id": trial_id,
        "generation_budget_per_workload": 1,
        "status": "partial",
        "launch_admission": {"certifying": False},
        "cells": [copy.deepcopy(cell)],
    }


def test_m10_campaign_chain_rejects_persisted_performance_mutation(tmp_path) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(tmp_path)
    persisted["runs"][0]["median_tps"] = 125_162_981
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = _campaign_report(cell)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[campaign-chain\] persisted layer3 report differs from fresh rebuild$",
    ):
        C.assert_campaign_layer3_chain(report=report, output_root=output_root)


def test_campaign_identity_is_pinned_without_producer_helper_oracle(tmp_path) -> None:
    output_root, _campaign, _persisted_path, _persisted, cell = _layer3_campaign(
        tmp_path
    )
    assert cell["campaign_id"] == (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-67a4e01c"
    )
    assert _PRE_T343_NO_BUILD_CAMPAIGN_IDS[(
        "fixture-completeness", "ycsb-a",
    )] == "p3-t178-ycsb-a-workload-conditioned-autonomous-948f4c43"
    report = _campaign_report(cell)
    C.assert_campaign_layer3_chain(report=report, output_root=output_root)


@pytest.mark.parametrize(
    "workload,old_campaign_id,new_campaign_id",
    _T428_WORKLOAD_CAMPAIGN_EPOCHS,
)
def test_t428_workload_campaign_epoch_and_old_root_nonwrite(
    tmp_path, workload, old_campaign_id, new_campaign_id,
) -> None:
    assert _T343_POLICY_BOUND_CAMPAIGN_IDS[
        ("fixture-completeness", workload)
    ] == old_campaign_id
    assert _T428_POLICY_BOUND_CAMPAIGN_IDS[
        ("fixture-completeness", workload)
    ] == new_campaign_id
    assert old_campaign_id != new_campaign_id

    output_root, campaign, _persisted_path, _persisted, cell = _layer3_campaign(
        tmp_path, workload=workload,
    )
    old_root = output_root / "campaigns" / old_campaign_id
    assert campaign == output_root / "campaigns" / new_campaign_id
    assert not old_root.exists()

    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )
    assert not old_root.exists()


def test_independent_literal_layer3_admission_decision_is_accepted() -> None:
    """Layer3 producer を呼ばず、独立 literal receipt を consumer へ与える。"""
    report = {
        "schema_version": _LAYER3_SCHEMA_VERSION,
        "admission_decision": copy.deepcopy(_LITERAL_ADMISSION_DECISION),
    }
    assert C._require_exact_layer3_admission_decision(
        report,
        expected=_LITERAL_ADMISSION_DECISION,
        label="literal layer3 report",
    ) == _LITERAL_ADMISSION_DECISION


@pytest.mark.parametrize("path,replacement", [
    (("schema_version",), "campaign-artifact-admission-decision/v0"),
    (("classification",), "historical-pre-admission-schema"),
    (("admission_status",), "legacy-unclassified"),
    (("verification_status",), "historically-certified"),
    (("campaign_id",), "other-campaign"),
    (("campaign_path",), "campaigns/other-campaign"),
    (("campaign_lock_sha256",), "a" * 64),
    (("wal_sha256",), "b" * 64),
    (("policy_sha256",), "c" * 64),
    (("attempt_receipt_sha256s",), ["d" * 64]),
    (("validator", "identity"), "other.validator"),
    (("validator", "sha256"), "e" * 64),
    (("overlay", "ledger_sha256"), "f" * 64),
    (("overlay", "record_key"), "other-record"),
])
def test_independent_literal_admission_receipt_field_mutations_are_rejected(
    path, replacement,
) -> None:
    mutated = copy.deepcopy(_LITERAL_ADMISSION_DECISION)
    target = mutated
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match="admission decision differs from validator",
    ):
        C._require_exact_layer3_admission_decision(
            {"admission_decision": mutated},
            expected=_LITERAL_ADMISSION_DECISION,
            label="literal layer3 report",
        )


def test_campaign_chain_rejects_missing_persisted_report(tmp_path) -> None:
    output_root, _campaign, persisted_path, _persisted, cell = _layer3_campaign(tmp_path)
    persisted_path.unlink()
    report = _campaign_report(cell)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[campaign-chain\] persisted layer3 report cannot be read: "
            r".*layer3_report\.json$"
        ),
    ):
        C.assert_campaign_layer3_chain(report=report, output_root=output_root)


def test_campaign_chain_rejects_cross_trial_campaign_substitution(tmp_path) -> None:
    output_root = tmp_path / "output"
    _layer3_campaign(tmp_path, trial_id="trial-a", output_root=output_root)
    _root, _campaign, _path, _persisted, trial_b_cell = _layer3_campaign(
        tmp_path, trial_id="trial-b", output_root=output_root,
    )
    report = _campaign_report(trial_b_cell, trial_id="trial-a")
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[campaign-chain\] cells\[0\] campaign_id differs from producer derivation$",
    ):
        C.assert_campaign_layer3_chain(report=report, output_root=output_root)


def test_generated_from_head_mutation_is_rejected(tmp_path) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(tmp_path)
    persisted["meta"]["generated_from_head"] = "not-a-git-object-id"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[campaign-chain\] persisted layer3 generated_from_head "
            r"is not a git object ID$"
        ),
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


def test_terminal_projection_and_journal_hash_are_independent_gates(tmp_path) -> None:
    run, events, report = _provider_init_trial(tmp_path)
    report["fatal_error"]["message"] = "changed"
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[terminal-projection\] provider-init-error projection is inconsistent$",
    ):
        _verify(run, report)
    report["fatal_error"]["message"] = "init failed"
    _persist(run, events, report)
    report["attempt_journal_sha256"] = "0" * 64
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[journal-hash\] attempt_journal_sha256 does not match bytes read$",
    ):
        _verify(run, report)


@pytest.mark.parametrize(
    ("report_path", "replacement", "expected"),
    [
        (("trial_id",), "other-trial", r"run-start/report mismatch: trial_id"),
        (("provider",), "other-provider", r"provider is outside the producer closed set"),
        (
            ("generation_budget_per_workload",),
            2,
            r"run-start/report mismatch: generation_budget_per_workload",
        ),
        (("do_build",), True, r"run-start/report mismatch: do_build"),
        (("stop_policy", "max_wall_s"), 61, r"run-start/report mismatch: max_wall_s"),
    ],
)
def test_run_start_scalar_envelope_fields_are_bound(
    tmp_path, report_path, replacement, expected,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    target = report
    for key in report_path[:-1]:
        target = target[key]
    target[report_path[-1]] = replacement
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[run-envelope\] {expected}$",
    ):
        _verify(run, report)


def test_report_attempt_journal_path_is_bound_to_verified_file(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["attempt_journal"] = str(run / "other-attempts.jsonl")
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[run-envelope\] report\.attempt_journal cannot be resolved$",
    ):
        _verify(run, report)


def test_journal_seq_gap_is_rejected(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    report_roles = report["cells"][0]["generations"][0]["roles"]
    for event in events[2:]:
        event["seq"] += 1
        if event["event"] == "role-attempt":
            report_roles[event["role"]]["seq"] = event["seq"]
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[journal-sequence\] journal seq must be contiguous 1\.\.N; expected 3$",
    ):
        _verify(run, report)


def test_role_append_io_failure_cannot_publish_incomplete_report(
    tmp_path, monkeypatch,
) -> None:
    real_open = A.os.open
    journal_open_count = 0

    def fail_second_journal_open(path, flags, mode=0o777):
        nonlocal journal_open_count
        if Path(path).name == "attempts.jsonl":
            journal_open_count += 1
            if journal_open_count == 2:
                raise OSError("fixture role append failure")
        return real_open(path, flags, mode)

    monkeypatch.setattr(A.os, "open", fail_second_journal_open)
    run = tmp_path / "run"
    with pytest.raises(
        A.AutonomousTrialError,
        match=(
            r"attempt journal の過去の append 失敗後は"
            r"追記・report 公開を継続できない$"
        ),
    ):
        A.run_trial(
            trial_id="role-append-io-failure",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run,
            sub="/unused",
            do_build=False,
            allow_unregistered_exploratory=True,
        )
    assert not (run / "report.json").exists()
    events = [
        json.loads(line)
        for line in (run / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["event"] for event in events] == ["run-start"]


def test_journal_change_after_verifier_read_is_fail_closed(
    tmp_path, monkeypatch,
) -> None:
    original = A.assert_autonomous_trial_completeness

    def mutate_after_verification(*, report, attempt_journal):
        original(report=report, attempt_journal=attempt_journal)
        with Path(attempt_journal).open("ab") as stream:
            stream.write(b"fixture-race\n")

    monkeypatch.setattr(
        A, "assert_autonomous_trial_completeness", mutate_after_verification,
    )
    run = tmp_path / "run"
    with pytest.raises(
        A.AutonomousTrialError,
        match=r"completeness 検査後に attempt journal bytes が変化した$",
    ):
        A.run_trial(
            trial_id="journal-post-read-change",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run,
            sub="/unused",
            do_build=False,
            drive=lambda *args, **kwargs: {
                "outcome": "dry-pass",
                "variant": None,
                "stop_reason": "continue",
                "iteration": 1,
                "ran": True,
            },
            preview=lambda _coder, sub: {
                "passed": True,
                "working_diff": "fixture",
                "diff_digest": hashlib.sha256(b"fixture").hexdigest(),
                "subtype": None,
                "reason": "",
                "forbidden_identifiers": [],
            },
            allow_unregistered_exploratory=True,
        )
    assert not (run / "report.json").exists()


def test_completeness_failure_is_not_caught_and_report_is_not_written(
    tmp_path, monkeypatch,
) -> None:
    def broken_preview(coder, *, sub):
        raise RuntimeError("preview fixture failure")

    def reject(**kwargs):
        raise C.AutonomousTrialCompletenessError("fixture completeness rejection")

    monkeypatch.setattr(A, "assert_autonomous_trial_completeness", reject)
    run = tmp_path / "run"
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"fixture completeness rejection$",
    ):
        A.run_trial(
            trial_id="fail-closed-report",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="fixture",
            run_root=run,
            sub="/unused",
            do_build=False,
            preview=broken_preview,
            allow_unregistered_exploratory=True,
        )
    assert not (run / "report.json").exists()
    events = [
        json.loads(line)
        for line in (run / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert events[-1]["event"] == "run-finish"


def test_direct_cli_starts_with_clean_pythonpath(tmp_path) -> None:
    run, _events, _report_value = _complete_trial(tmp_path)
    proc = subprocess.run(
        [
            sys.executable,
            str(_ROOT / "orchestrator/campaign/autonomous_trial_completeness.py"),
            str(run / "attempts.jsonl"),
            str(run / "report.json"),
        ],
        cwd=tmp_path,
        env={"PATH": str(Path(sys.executable).parent)},
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("run_start_has_fields", [False, True])
def test_t325_optional_commit_fields_preserve_existing_completeness_acceptance(
    tmp_path, run_start_has_fields,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    commit_fields = {
        "prereg_commit": "fixture-prereg-commit",
        "measurement_head": "fixture-measurement-head",
        "manifest_sha256": "fixture-manifest-sha256",
    }
    report.update(commit_fields)
    if run_start_has_fields:
        events[0].update(commit_fields)
    _persist(run, events, report)

    _verify(run, report)


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-x"]))
