# -*- coding: utf-8 -*-
"""T-295 autonomous trial completeness gates and positive acceptance set."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")


_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import autonomous_trial_completeness as C  # noqa: E402
from orchestrator.campaign import env_contract, ident, reflux_ir, source_digest  # noqa: E402
from orchestrator.campaign import p3_autonomous_workload_trial as A  # noqa: E402
from orchestrator.campaign import layer3_report as L3                 # noqa: E402
from orchestrator.campaign import pipeline as P                       # noqa: E402
from orchestrator.campaign import s8b_descriptor                      # noqa: E402
from orchestrator.campaign import s8b_holdout_freeze                  # noqa: E402
from orchestrator.campaign import s8c_arm_inputs                      # noqa: E402
from orchestrator.campaign import trigger_gate_binding as TGB         # noqa: E402
from orchestrator.campaign.build_admission import (                  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.pin import CURRENT_PIN                    # noqa: E402
from orchestrator.campaign.layout import CampaignLayout              # noqa: E402
from orchestrator.campaign.model import (                           # noqa: E402
    CampaignConfig,
    Genome,
)
from orchestrator.campaign.source_digest import (                    # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from orchestrator.tests.campaign_lock_test_support import build_v2_lock  # noqa: E402
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402
from orchestrator.tests import test_p3_autonomous_workload_trial as p3_test  # noqa: E402


_ROLES = ("planner", "coder", "auditor", "critic")
_TRIAL_SCHEMA_VERSION = "p3-autonomous-workload-trial/v4"
_REPORT_SCHEMA_VERSION = "p3-autonomous-workload-trial-report/v3"
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
_GENERATION_DRIVER = {
    "wrapper": "s8c-generation/v1",
    "delegate": "trigger.drive_iteration",
}
_GATING_SPEC_SHA256 = hashlib.sha256(A.GATING_SPEC.encode("utf-8")).hexdigest()

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
_CURRENT_POLICY_BOUND_CAMPAIGN_IDS = {
    ("fixture-completeness", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-4b75e24e"
    ),
    ("fixture-completeness", "ycsb-b"): (
        "p3-t178-ycsb-b-workload-conditioned-autonomous-136086b0"
    ),
    ("fixture-completeness", "ycsb-c"): (
        "p3-t178-ycsb-c-workload-conditioned-autonomous-4ac6e6a4"
    ),
    ("trial-a", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-8671d0a1"
    ),
    ("trial-b", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-19143fe1"
    ),
}
_T530_CONTRACT = A.env_contract.GENERATIONS["linux-baremetal"][0].contract
_T530_LAYER3_CONTRACT = (
    env_contract.GENERATIONS["linux-baremetal"][0].contract
)
_T530_CONTRACT_SHA256 = (
    "1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7"
)
assert _T530_CONTRACT.contract_sha256 == _T530_CONTRACT_SHA256
assert _T530_LAYER3_CONTRACT.contract_sha256 == _T530_CONTRACT_SHA256
_T530_CONTRACT_BOUND_CAMPAIGN_IDS = {
    ("fixture-completeness", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-4bf2256c"
    ),
    ("fixture-completeness", "ycsb-b"): (
        "p3-t178-ycsb-b-workload-conditioned-autonomous-add1a705"
    ),
    ("fixture-completeness", "ycsb-c"): (
        "p3-t178-ycsb-c-workload-conditioned-autonomous-03a4517a"
    ),
    ("trial-a", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-7037dbaf"
    ),
    ("trial-b", "ycsb-a"): (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-620450b7"
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
_CURRENT_WORKLOAD_CAMPAIGN_EPOCHS = (
    (
        "ycsb-a",
        "p3-t178-ycsb-a-workload-conditioned-autonomous-67a4e01c",
        "p3-t178-ycsb-a-workload-conditioned-autonomous-4b75e24e",
    ),
    (
        "ycsb-b",
        "p3-t178-ycsb-b-workload-conditioned-autonomous-1e4b78c7",
        "p3-t178-ycsb-b-workload-conditioned-autonomous-136086b0",
    ),
    (
        "ycsb-c",
        "p3-t178-ycsb-c-workload-conditioned-autonomous-c3cccc72",
        "p3-t178-ycsb-c-workload-conditioned-autonomous-4ac6e6a4",
    ),
)


def _t428_descriptor_campaign_id(trial_id: str, workload: str) -> str:
    workload_flags = A.WORKLOADS[workload]
    descriptor, descriptor_record = A._descriptor_for(workload_flags)
    cfg = A._campaign_for(
        workload=workload,
        entry=workload_flags,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=trial_id,
        generations=1,
        contract=_T530_CONTRACT,
        build_context=A.build_run_context(
            generator_id=A.GeneratorId.S8A_TRIGGER_SWEEP,
        ),
    )
    assert "environment_contract_sha256" not in cfg.search_config
    assert cfg.bound_environment_contract is _T530_CONTRACT
    return str(A.ident.campaign_id(cfg))
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
    "5a9e2696b8fba18f8f7cf01183673a1bd6f5781cc9cb1fe8641f9d667fe11549"
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
        "perf_config_scale": {"records": 100_000, "threads": 4},
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


def _fixture_payload_validation_receipt(
    event: dict, spec_key: str, workload_descriptor: dict,
) -> dict:
    role = event["role"]
    generation = event["generation"]
    fixed_literals = {
        "schema_version": _TRIAL_SCHEMA_VERSION,
        "pilot_scope": "exploratory-ycsb-abc",
        "scientific_claim": False,
        "attempt_policy": {"attempts_per_role_generation": 1, "retry": False},
        "stop_policy": {
            "performance_early_stop": False,
            "generation_budget_is_fixed": True,
        },
    }
    nested_key_sets = {
        "$": A.ROLE_PAYLOAD_KEY_SPEC[spec_key],
        "$.attempt_policy": ["attempts_per_role_generation", "retry"],
        "$.stop_policy": [
            "generation_budget_is_fixed", "performance_early_stop",
        ],
    }
    projection = {
        "role": role,
        "workload": event["workload"],
        "generation": generation,
        "descriptor_sha256": event["descriptor_sha256"],
        "workload_descriptor_sha256": hashlib.sha256(
            s8c_arm_inputs.canonical_execution_input_bytes(
                workload_descriptor
            )
        ).hexdigest(),
        "descriptor_binding_sha256": "2" * 64,
        "fixed_literals": fixed_literals,
        "nested_key_sets": nested_key_sets,
        "whiteboard_origin": [],
        "whiteboard_origin_sha256": hashlib.sha256(b"[]").hexdigest(),
    }
    if role == "planner":
        nested_key_sets.update({
            "$.current_perf": sorted(C._PERF_KEYS),
            "$.leading_indicators": [
                "IPC_overall", "cache_miss_rate_pct", "contention_level",
            ],
        })
        feedback = None
        if generation >= 2:
            feedback = {
                "source_generation": generation - 1,
                "diagnostics": [
                    {
                        "metric": metric,
                        "value_is_null": True,
                        "value_sha256": hashlib.sha256(b"null").hexdigest(),
                    }
                    for metric in C._DIAGNOSTIC_METRICS
                ],
                "uncertainty_present": True,
                "reverse_recommended": False,
            }
        projection.update({
            "current_perf_nullness": {key: True for key in sorted(C._PERF_KEYS)},
            "leading_metric_nullness": {
                key: True for key in sorted(C._LEADING_METRIC_KEYS)
            },
            "contention_level_sha256": hashlib.sha256(b'"high"').hexdigest(),
            "critic_feedback": feedback,
        })
    else:
        fixed_literals.update({
            "leakproof_context": C._LEAKPROOF_CONTEXT,
            "planner_axis": C._PLANNER_AXIS,
        })
        nested_key_sets.update({
            "$.baseline": sorted(C._PERF_KEYS),
            "$.planner_direction": ["axis", "direction", "magnitude"],
        })
        projection.update({
            "baseline_nullness": {key: True for key in sorted(C._PERF_KEYS)},
            "gating_spec_sha256": _GATING_SPEC_SHA256,
            "planner_direction_sha256": "3" * 64,
        })
    projection_sha256 = C._receipt_sha256(projection)
    seal_preimage = {
        "schema_version": C._VALIDATION_RECEIPT_SCHEMA_VERSION,
        "role": role,
        "payload_sha256": event["input_payload_sha256"],
        "payload_allowlist_sha256": A.ROLE_PAYLOAD_ALLOWLIST_SHA256,
        "safe_projection_sha256": projection_sha256,
    }
    return {
        **seal_preimage,
        "safe_projection": projection,
        "seal_sha256": C._receipt_sha256(seal_preimage),
    }


def _role_event(
    workload: str, role: str, seq: int, *, status: str = "valid",
    generation: int = 1, pre_audit: dict | None = None,
    role_query_ordinal: int | None = None,
    workload_descriptor: dict,
) -> dict:
    spec_key = (
        "planner-generation-1"
        if role == "planner" and generation == 1
        else "planner-generation-next"
        if role == "planner"
        else "auditor-skip"
        if role == "auditor" and status == "skipped"
        else role
    )
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
        "payload_exact_keys": A.ROLE_PAYLOAD_KEY_SPEC[spec_key],
        "payload_allowlist_sha256": A.ROLE_PAYLOAD_ALLOWLIST_SHA256,
        "role_query_ordinal": (
            None
            if status == "skipped"
            else seq - 1 if role_query_ordinal is None else role_query_ordinal
        ),
    }
    if role in {"planner", "coder"}:
        event["payload_validation_receipt"] = (
            _fixture_payload_validation_receipt(
                event, spec_key, workload_descriptor,
            )
        )
    if status == "invalid":
        for key in ("raw_response_path", "raw_response_sha256", "parsed", "provenance"):
            event.pop(key)
        event.update({
            "error_type": "FixtureInvalid",
            "error": "fixture invalid",
            "error_artifacts": {"failure_phase": "pre-raw-write"},
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
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "honest_accounting_authority": "supervisor-authoritative",
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
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "honest_accounting": {
            "role_query_count": 0,
            "bench_wall_seconds": 0.0,
        },
        "honest_accounting_authority": "supervisor-authoritative",
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


def _origin_binding(*, workload: str = "ycsb-a") -> dict:
    return {
        "authority_blob_sha256": "1" * 64,
        "source_closure_sha256": "2" * 64,
        "origin_id": "fixture-origin",
        "cell_key": "fixture-cell",
        "authority_workload": {
            "descriptor_sha256": "3" * 64,
            "records": 1000,
            "threads": 4,
        },
        "axis_semantics_sha256": "4" * 64,
        "verifier_policy_sha256": "5" * 64,
        "environment_contract_sha256": "6" * 64,
        "campaign_id": _PRE_T343_NO_BUILD_CAMPAIGN_IDS[
            ("fixture-completeness", "ycsb-a")
        ],
        "trial_workload": workload,
        "measurement_head": "7" * 40,
        "store_scope": "fixture",
        "issuer_seal": "launch-admission-gate/v1",
    }


def _origin_bound_launch_admission() -> dict:
    return {
        "mode": "registered-effective",
        "certifying": False,
        "reason_code": "registered-effective-non-certifying",
        "trial_id": "fixture-completeness",
        "workloads": ["ycsb-a"],
        "binding": {
            "manifest_sha256": "b" * 64,
            "prereg_commit": "c" * 40,
            "prereg_content_commit": "e" * 40,
            "prereg_effective_commit": "f" * 40,
            "measurement_head": "7" * 40,
            "trial_id": "fixture-completeness",
            "arm": "on",
            "holdout": "H1",
            "campaign_id": _PRE_T343_NO_BUILD_CAMPAIGN_IDS[
                ("fixture-completeness", "ycsb-a")
            ],
            "workload": "ycsb-a",
            "ycsb_rratio": "70",
        },
        "activation_report_digest_sha256": "d" * 64,
        "prereg_content_commit": "e" * 40,
        "prereg_effective_commit": "f" * 40,
        "origin_binding": _origin_binding(),
    }


def _origin_terminal_projection(*, rejected: bool) -> dict:
    return {
        "schema_version": "OriginTerminalProjection/v1",
        "reason_code": "FC01" if rejected else "P6Unavailable",
        "formal_receipt_sha256": None if rejected else "8" * 64,
        "evidence_root_sha256": None if rejected else "9" * 64,
        "authority_blob_sha256": "1" * 64,
        "origin_id": "fixture-origin",
        "cell_key": "fixture-cell",
        "terminal_payload_sha256": "a" * 64,
    }


def _finish(
    run: Path, status: str, seq: int, *, role_query_count: int = 0,
    bench_wall_seconds: float = 0.0,
) -> dict:
    return {
        "event": "run-finish",
        "status": status,
        "report": str(run / "report.json"),
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "honest_accounting": {
            "role_query_count": role_query_count,
            "bench_wall_seconds": bench_wall_seconds,
        },
        "honest_accounting_authority": "supervisor-authoritative",
        "seq": seq,
        "ts": f"2026-08-01T00:01:{seq:02d}+00:00",
    }


def _generation_accounting(
    workload: str, generation: int, seq: int, *, provider_invoke_count: int,
    auditor_skipped: bool = False, state: str = "generation-complete",
    bench_wall_seconds: float = 0.0,
) -> dict:
    return {
        "event": "generation-accounting",
        "workload": workload,
        "generation": generation,
        "state": state,
        "provider_invoke_count": provider_invoke_count,
        "auditor_pre_audit_skipped": auditor_skipped,
        "bench_wall_seconds": bench_wall_seconds,
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "accounting_authority": "supervisor-authoritative",
        "seq": seq,
        "ts": f"2026-08-01T00:00:{seq:02d}+00:00",
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
    ordinal = 1
    for workload in requested:
        cell_metadata = _golden_cell_metadata(run, workload)
        roles = {}
        for role in _ROLES:
            event = _role_event(
                workload, role, seq, role_query_ordinal=ordinal,
                workload_descriptor=cell_metadata["descriptor"],
            )
            events.append(event)
            roles[role] = copy.deepcopy(event)
            seq += 1
            ordinal += 1
        events.append(_generation_accounting(
            workload, 1, seq, provider_invoke_count=4,
        ))
        seq += 1
        report["cells"].append({
            "workload": workload,
            **cell_metadata,
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
                    "critic_digest_generated": False,
                },
                "outcome": "dry-pass",
                "bench_wall_seconds": 0.0,
                "generation_driver": dict(_GENERATION_DRIVER),
                "gating_spec_sha256": _GATING_SPEC_SHA256,
            }],
            "stop_reason": "fixed-generation-budget",
        })
    report["honest_accounting"]["role_query_count"] = ordinal - 1
    events.append(_finish(
        run, "complete", seq, role_query_count=ordinal - 1,
    ))
    _persist(run, events, report)
    return run, events, report


def _registered_digest_chain_trial(tmp_path: Path):
    run, events, report = _complete_trial(tmp_path)
    cell = report["cells"][0]
    holdout_high = s8b_holdout_freeze._HOLDOUT_HIGH
    fixed_skew = s8b_holdout_freeze._FIXED_SKEW
    fixed_rmw = s8b_holdout_freeze._FIXED_RMW
    workload = "rr" + holdout_high
    workload_flags = {
        s8b_holdout_freeze.SKEW_KEY: fixed_skew,
        s8b_holdout_freeze.RRATIO_KEY: holdout_high,
        s8b_holdout_freeze.RMW_KEY: fixed_rmw,
    }
    entry = A.FORMAL_WORKLOADS[workload]
    descriptor = {
        "schema_version": "8b-v1",
        "source": "campaign_search_config_projection",
        "read_write": {
            "read_ratio_percent": int(holdout_high),
            "rmw": int(fixed_rmw),
        },
        "contention": {"skew": float(fixed_skew), "label": "high"},
        "scale": {"records": 1_000_000, "threads": 48},
        "objective": "maximize_throughput_tps",
        "correctness": "serializable_legacy_and_s2",
    }
    report["workloads_requested"] = [workload]
    events[0]["workloads"] = [workload]
    cell["workload"] = workload
    cell["workload_flags"] = workload_flags
    cell["perf_config_scale"] = {
        "records": entry["records"],
        "threads": entry["threads"],
    }
    cell["descriptor"] = descriptor
    for event in events:
        if event.get("event") in {"role-attempt", "generation-accounting"}:
            event["workload"] = workload
    for event in cell["generations"][0]["roles"].values():
        event["workload"] = workload
    descriptor_bytes = s8c_arm_inputs.canonical_execution_input_bytes(
        cell["descriptor"]
    )
    content_digest = hashlib.sha256(descriptor_bytes).hexdigest()
    assert content_digest == (
        "80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843"
    )
    arm = "on"
    holdout = "H1"
    arm_digest = C._arm_binding_digest(
        holdout=holdout, arm=arm, content_digest=content_digest,
    )
    arm_execution = {
        "input_schema_version": "8b-v1",
        "content_digest_sha256": content_digest,
        "arm_binding_digest_sha256": arm_digest,
    }
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    identity_preimage = C.campaign_lock.canonical_json({
        "spec_content": C._AUTONOMOUS_SPEC_CONTENT,
        "ccbench_commit": CURRENT_PIN,
        "search_tag": "workload-conditioned-autonomous",
        "search_config": {
            "axis": "silo-backoff-trigger-gating",
            "descriptor_schema": "8b-v1",
            "descriptor_sha256": content_digest,
            "generation_budget": 1,
            "pilot_scope": "exploratory-ycsb-abc",
            "records": entry["records"],
            "reflux": "on",
            "scale": "silo",
            "stop_policy": "fixed-generations-no-performance-early-stop",
            "threads": entry["threads"],
            "trigger_gate_binding_schema": "izanagi-trigger-gate-binding/v1",
            "verify": "legacy+s2",
            "workload": workload,
            "ycsb": dict(workload_flags),
            "build_admission": dict(context.policy.as_preimage()),
            "arm_binding_digest_sha256": arm_digest,
        },
        "trial": f"fixture-completeness-{workload}",
    })
    campaign_id = (
        f"p3-t178-{workload}-workload-conditioned-autonomous-"
        + hashlib.sha256(identity_preimage.encode("utf-8")).hexdigest()[:8]
    )
    campaign_root = run / "campaigns" / campaign_id
    campaign_root.mkdir(parents=True)
    (campaign_root / "campaign.lock").write_text(
        build_v2_lock(identity_preimage), encoding="utf-8",
    )
    cell.update({
        "campaign_id": campaign_id,
        "campaign_root": str(campaign_root),
        "descriptor_binding": {
            **cell["descriptor_binding"],
            "input_sha256": content_digest,
            "output_sha256": content_digest,
            "content_digest_sha256": content_digest,
            "arm_binding_digest_sha256": arm_digest,
        },
    })
    launch_admission = {
        "mode": "registered-effective",
        "certifying": False,
        "reason_code": "registered-effective-non-certifying",
        "trial_id": "fixture-completeness",
        "workloads": [workload],
        "binding": {
            "manifest_sha256": "b" * 64,
            "prereg_commit": "c" * 40,
            "prereg_content_commit": "e" * 40,
            "prereg_effective_commit": "f" * 40,
            "measurement_head": "7" * 40,
            "trial_id": "fixture-completeness",
            "arm": arm,
            "holdout": holdout,
            "campaign_id": campaign_id,
            "workload": workload,
            "ycsb_rratio": workload_flags["ycsb_rratio"],
        },
        "activation_report_digest_sha256": "d" * 64,
        "prereg_content_commit": "e" * 40,
        "prereg_effective_commit": "f" * 40,
    }
    report["launch_admission"] = copy.deepcopy(launch_admission)
    report["arm_execution"] = copy.deepcopy(arm_execution)
    events[0]["launch_admission"] = copy.deepcopy(launch_admission)
    events[0]["arm_execution"] = copy.deepcopy(arm_execution)

    report_roles = report["cells"][0]["generations"][0]["roles"]
    journal_roles = [event for event in events if event["event"] == "role-attempt"]
    for role, report_event in report_roles.items():
        invocation_id = f"arm-{arm}.exec-{arm_digest}.{workload}.g1.{role}"
        for event in (report_event, next(
            item for item in journal_roles if item["role"] == role
        )):
            event["invocation_id"] = invocation_id
            event["descriptor_sha256"] = content_digest
            event["arm_binding_digest_sha256"] = arm_digest
            if role in {"planner", "coder"}:
                spec_key = "planner-generation-1" if role == "planner" else role
                event["payload_validation_receipt"] = (
                    _fixture_payload_validation_receipt(
                        event, spec_key, cell["descriptor"],
                    )
                )
    proposal_value = {
        "planner": {"fixture": True},
        "coder": {"fixture": True},
        "auditor": {"fixture": True},
        "prior_critic_reverse": False,
        "descriptor_sha256": content_digest,
        "arm_binding_digest_sha256": arm_digest,
    }
    proposal_path = (
        run / "proposals"
        / f"arm-{arm}.exec-{arm_digest}.{workload}.g1.json"
    )
    proposal_path.parent.mkdir()
    proposal_bytes = json.dumps(
        proposal_value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    proposal_path.write_bytes(proposal_bytes)
    cell["generations"][0]["proposal"] = {
        "path": str(proposal_path),
        "sha256": hashlib.sha256(proposal_bytes).hexdigest(),
        "digest": arm_digest,
    }
    _persist(run, events, report)
    return run, events, report, arm_execution


def _formal_noncertifying_digest_chain_trial(tmp_path: Path):
    run, events, report, arm_execution = _registered_digest_chain_trial(tmp_path)
    for admission in (
        report["launch_admission"], events[0]["launch_admission"],
    ):
        admission["mode"] = "registered-formal-non-certifying"
        admission["reason_code"] = "registered-formal-non-certifying"
        admission["activation_report_digest_sha256"] = None
    _persist(run, events, report)
    return run, events, report, arm_execution


def _verify_digest_chain(run: Path, _events: list[dict], report: dict) -> None:
    C.assert_autonomous_trial_execution_digest_chain(
        report=report, attempt_journal=run / "attempts.jsonl",
    )


def _t525_pre_fix_registered_scale_predicate_passes(
    cell: dict, registered_holdout: dict,
) -> bool:
    scale = cell.get("perf_config_scale")
    return isinstance(scale, dict) and all(
        scale.get(field) == registered_holdout.get(field)
        for field in ("records", "threads")
    )


def test_t1311_registered_digest_chain_positive_control(tmp_path) -> None:
    run, events, report, _arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    _verify_digest_chain(run, events, report)


def test_t525_registered_cell_complete_condition_is_lock_independent(
    tmp_path: Path,
) -> None:
    from orchestrator.campaign import trial_registry as registry

    cases = (
        ("workload_flags", "ycsb_zipf_skew"),
        ("workload_flags", "ycsb_rmw"),
        ("perf_config_scale", "records"),
        ("perf_config_scale", "threads"),
    )
    assert cases
    rejected_count = 0
    for section, field in cases:
        case_root = tmp_path / field
        case_root.mkdir()
        run, events, report, _arm_execution = _registered_digest_chain_trial(
            case_root
        )
        cell = report["cells"][0]
        campaign_lock_path = Path(cell["campaign_root"]) / "campaign.lock"
        campaign_lock_path.unlink()
        assert report["do_build"] is False
        assert not campaign_lock_path.exists()
        _verify_digest_chain(run, events, report)

        original = cell[section][field]
        cell[section][field] = (
            f"{original}-different" if isinstance(original, str) else original + 1
        )
        binding = report["launch_admission"]["binding"]
        flags = cell["workload_flags"]
        registered = registry.HOLDOUT_BINDINGS[binding["holdout"]]
        assert binding["holdout"] == "H1"
        assert binding["workload"] == registered["workload"]
        assert binding["ycsb_rratio"] == registered["ycsb_rratio"]
        assert report["launch_admission"]["workloads"] == [binding["workload"]]
        assert cell["workload"] == registered["workload"]
        assert flags["ycsb_rratio"] == registered["ycsb_rratio"]
        with pytest.raises(
            C.AutonomousTrialCompletenessError,
            match=(
                rf"^\[arm-digest-chain\] benchmark {section}\.{field} "
                r"differs from registered holdout$"
            ),
        ):
            _verify_digest_chain(run, events, report)
        rejected_count += 1
    assert rejected_count == len(cases)
    assert rejected_count > 0


def test_t525_no_lock_scale_must_match_frozen_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import trial_registry as registry

    cases = ("records", "threads")
    assert cases
    rejected_count = 0
    frozen_bindings = registry.HOLDOUT_BINDINGS
    for field in cases:
        case_root = tmp_path / field
        case_root.mkdir()
        run, events, report, _arm_execution = _registered_digest_chain_trial(
            case_root
        )
        cell = report["cells"][0]
        campaign_lock_path = Path(cell["campaign_root"]) / "campaign.lock"
        campaign_lock_path.unlink()
        assert report["do_build"] is False
        assert not campaign_lock_path.exists()
        _verify_digest_chain(run, events, report)

        binding = report["launch_admission"]["binding"]
        tampered_bindings = {
            holdout: dict(condition)
            for holdout, condition in frozen_bindings.items()
        }
        tampered_value = cell["perf_config_scale"][field] + 1
        tampered_bindings[binding["holdout"]][field] = tampered_value
        cell["perf_config_scale"][field] = tampered_value
        registered = tampered_bindings[binding["holdout"]]
        assert _t525_pre_fix_registered_scale_predicate_passes(
            cell, registered,
        )
        assert cell["perf_config_scale"] != cell["descriptor"]["scale"]

        with monkeypatch.context() as patch:
            patch.setattr(registry, "HOLDOUT_BINDINGS", tampered_bindings)
            with pytest.raises(
                C.AutonomousTrialCompletenessError,
                match=(
                    rf"^\[arm-digest-chain\] benchmark perf_config_scale\.{field} "
                    r"differs from cell descriptor$"
                ),
            ):
                _verify_digest_chain(run, events, report)
        rejected_count += 1
    assert rejected_count == len(cases)
    assert rejected_count > 0


@pytest.mark.parametrize("mutation", ("missing", "extra", "format"))
def test_t1311_registered_arm_execution_is_required_exact_and_sha256(
    tmp_path: Path, mutation: str,
) -> None:
    run, events, report, _arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    if mutation == "missing":
        report.pop("arm_execution")
    elif mutation == "extra":
        report["arm_execution"]["arm"] = "on"
        events[0]["arm_execution"]["arm"] = "on"
    else:
        report["arm_execution"]["content_digest_sha256"] = "not-a-digest"
        events[0]["arm_execution"]["content_digest_sha256"] = "not-a-digest"
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[arm-digest-chain\] ",
    ):
        _verify_digest_chain(run, events, report)


def test_t1311_registered_run_rejects_one_missing_digest(tmp_path: Path) -> None:
    run, events, report, _arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    report["arm_execution"].pop("arm_binding_digest_sha256")
    events[0]["arm_execution"].pop("arm_binding_digest_sha256")
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[arm-digest-chain\] "
            r"report\.arm_execution exact keys differ$"
        ),
    ):
        _verify_digest_chain(run, events, report)


def test_t1311_exploratory_shape_rejects_arm_execution(tmp_path: Path) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["arm_execution"] = {
        "input_schema_version": "8b-v1",
        "content_digest_sha256": "a" * 64,
        "arm_binding_digest_sha256": "b" * 64,
    }
    events[0]["arm_execution"] = copy.deepcopy(report["arm_execution"])
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[arm-digest-chain\] exploratory run carries arm_execution$",
    ):
        _verify(run, report)


def test_t1458_formal_noncertifying_report_passes_completeness_and_digest_chain(
    tmp_path: Path,
) -> None:
    run, _events, report, _arm_execution = (
        _formal_noncertifying_digest_chain_trial(tmp_path)
    )
    C.assert_autonomous_trial_completeness(
        report=report, attempt_journal=run / "attempts.jsonl",
    )
    C.assert_autonomous_trial_execution_digest_chain(
        report=report, attempt_journal=run / "attempts.jsonl",
    )


def test_t1458_formal_noncertifying_reason_code_is_required(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = (
        _formal_noncertifying_digest_chain_trial(tmp_path)
    )
    for admission in (
        report["launch_admission"], events[0]["launch_admission"],
    ):
        admission["reason_code"] = "registered-effective-non-certifying"
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[launch-admission\] "
            r"formal non-certifying launch projection is inconsistent$"
        ),
    ):
        _verify(run, report)


def test_t1458_formal_noncertifying_activation_digest_must_be_none(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = (
        _formal_noncertifying_digest_chain_trial(tmp_path)
    )
    for admission in (
        report["launch_admission"], events[0]["launch_admission"],
    ):
        admission["activation_report_digest_sha256"] = "d" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[launch-admission\] "
            r"formal non-certifying launch projection is inconsistent$"
        ),
    ):
        _verify(run, report)


def test_t1458_formal_noncertifying_binding_is_required(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = (
        _formal_noncertifying_digest_chain_trial(tmp_path)
    )
    for admission in (
        report["launch_admission"], events[0]["launch_admission"],
    ):
        admission["binding"] = None
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[launch-admission\] launch_admission\.binding is not an object$",
    ):
        _verify(run, report)


def test_t1458_formal_noncertifying_registered_key_shape_is_required(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = (
        _formal_noncertifying_digest_chain_trial(tmp_path)
    )
    for admission in (
        report["launch_admission"], events[0]["launch_admission"],
    ):
        admission.pop("prereg_content_commit")
        admission.pop("prereg_effective_commit")
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[launch-admission\] report launch_admission exact keys differ$",
    ):
        _verify(run, report)


def test_t1458_formal_noncertifying_arm_execution_is_required(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = (
        _formal_noncertifying_digest_chain_trial(tmp_path)
    )
    report.pop("arm_execution")
    events[0].pop("arm_execution")
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[arm-digest-chain\] report\.arm_execution is not an object$",
    ):
        C.assert_autonomous_trial_execution_digest_chain(
            report=report, attempt_journal=run / "attempts.jsonl",
        )


def test_t1458_formal_noncertifying_rejects_origin_binding(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = (
        _formal_noncertifying_digest_chain_trial(tmp_path)
    )
    binding = report["launch_admission"]["binding"]
    origin_binding = {
        "authority_blob_sha256": "1" * 64,
        "source_closure_sha256": "2" * 64,
        "origin_id": "origin-fixture",
        "cell_key": "cell-fixture",
        "authority_workload": {
            "descriptor_sha256": "3" * 64,
            "records": 1,
            "threads": 1,
        },
        "axis_semantics_sha256": "4" * 64,
        "verifier_policy_sha256": "5" * 64,
        "environment_contract_sha256": "6" * 64,
        "campaign_id": binding["campaign_id"],
        "trial_workload": binding["workload"],
        "measurement_head": binding["measurement_head"],
        "store_scope": "fixture",
        "issuer_seal": "launch-admission-gate/v1",
    }
    for admission in (
        report["launch_admission"], events[0]["launch_admission"],
    ):
        admission["origin_binding"] = copy.deepcopy(origin_binding)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[launch-admission\] "
            r"formal non-certifying launch cannot carry an origin binding$"
        ),
    ):
        _verify(run, report)


def test_t1311_persisted_file_verifier_runs_registered_digest_chain(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    report["cells"][0]["generations"][0]["proposal"]["digest"] = "e" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[arm-digest-chain\] proposal digest differs$",
    ):
        C.verify_autonomous_trial_files(
            run / "attempts.jsonl", run / "report.json",
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("descriptor", r"cell descriptor content digest differs"),
        ("descriptor-binding", r"descriptor binding digest differs"),
        ("descriptor-schema", r"descriptor binding digest differs"),
        ("campaign", r"search_config exact keys differ"),
        ("proposal", r"proposal digest differs"),
        ("invocation", r"journal invocation digest differs"),
        ("run-start", r"run-start/report arm_execution differs"),
        ("terminal-report", r"run-start/report arm_execution differs"),
    ),
)
def test_t1311_registered_digest_chain_rejects_each_bound_sink(
    tmp_path: Path, mutation: str, message: str,
) -> None:
    run, events, report, _arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    cell = report["cells"][0]
    if mutation == "descriptor":
        cell["descriptor"]["objective"] = "same-arm-label-different-bytes"
    elif mutation == "descriptor-binding":
        cell["descriptor_binding"]["arm_binding_digest_sha256"] = "e" * 64
    elif mutation == "descriptor-schema":
        cell["descriptor_binding"]["schema_sha256"] = "e" * 64
    elif mutation == "campaign":
        campaign_root = Path(cell["campaign_root"])
        decoded = C.campaign_lock.decode_campaign_lock_bytes(
            (campaign_root / "campaign.lock").read_bytes()
        )
        identity = copy.deepcopy(decoded.identity)
        assert identity["search_config"].pop("arm_binding_digest_sha256")
        (campaign_root / "campaign.lock").write_text(
            build_v2_lock(C.campaign_lock.canonical_json(identity)),
            encoding="utf-8",
        )
    elif mutation == "proposal":
        cell["generations"][0]["proposal"]["digest"] = "e" * 64
    elif mutation == "invocation":
        for event in events:
            if event.get("event") == "role-attempt":
                event["invocation_id"] = (
                    f"{event['workload']}.g{event['generation']}.{event['role']}"
                )
        for role, event in cell["generations"][0]["roles"].items():
            event["invocation_id"] = f"{event['workload']}.g1.{role}"
    elif mutation == "run-start":
        events[0]["arm_execution"]["arm_binding_digest_sha256"] = "e" * 64
    elif mutation == "terminal-report":
        report["arm_execution"]["arm_binding_digest_sha256"] = "e" * 64
    else:  # pragma: no cover - parametrization is closed
        raise AssertionError(mutation)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[(?:arm-digest-chain|campaign-chain)\].*{message}$",
    ):
        _verify_digest_chain(run, events, report)


@pytest.mark.parametrize(
    "mutation",
    ("outside", "symlink", "non-regular", "noncanonical", "hash"),
)
def test_t1311_proposal_artifact_is_run_bound_canonical_and_hashed(
    tmp_path: Path, mutation: str,
) -> None:
    run, events, report, _arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    proposal = report["cells"][0]["generations"][0]["proposal"]
    original = Path(proposal["path"])
    if mutation == "outside":
        outside = tmp_path / "outside.json"
        outside.write_bytes(original.read_bytes())
        proposal["path"] = str(outside)
    elif mutation == "symlink":
        target = original.with_suffix(".target")
        original.rename(target)
        original.symlink_to(target)
    elif mutation == "non-regular":
        original.unlink()
        original.mkdir()
    elif mutation == "noncanonical":
        value = json.loads(original.read_text("utf-8"))
        original.write_text(json.dumps(value, indent=2), encoding="utf-8")
        proposal["sha256"] = hashlib.sha256(original.read_bytes()).hexdigest()
    else:
        proposal["sha256"] = "e" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[arm-digest-chain\] ",
    ):
        _verify_digest_chain(run, events, report)


def test_t1311_origin_terminal_projection_requires_current_arm_epoch(
    tmp_path: Path,
) -> None:
    run, events, report, arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    projection = _origin_terminal_projection(rejected=True)
    projection["arm_binding_digest_sha256"] = (
        arm_execution["arm_binding_digest_sha256"]
    )
    report["origin_terminal_projection"] = projection
    _persist(run, events, report)
    _verify_digest_chain(run, events, report)
    report["origin_terminal_projection"]["arm_binding_digest_sha256"] = "e" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[arm-digest-chain\] origin terminal arm digest differs$",
    ):
        _verify_digest_chain(run, events, report)


@pytest.mark.parametrize(
    "mutation",
    (
        None,
        "payload-hash",
        "envelope-hash",
        "missing-descriptor",
        "payload-descriptor",
        "payload-arm",
        "artifact-arm",
    ),
)
def test_t1311_provider_payload_and_envelope_are_independently_reread(
    tmp_path: Path, mutation: str | None,
) -> None:
    run = tmp_path / "provider-run"
    artifact_root = run / "provider" / "planner"
    artifact_root.mkdir(parents=True)
    workload_descriptor = s8c_arm_inputs.derive_off_neutral_descriptor()
    other_arm_descriptor = s8b_descriptor.descriptor_for_holdout(
        s8b_holdout_freeze.HOLDOUTS["rr80"]
    )
    content_digest = hashlib.sha256(
        s8c_arm_inputs.canonical_execution_input_bytes(workload_descriptor)
    ).hexdigest()
    arm_digest = "b" * 64
    invocation_id = f"arm-on.exec-{arm_digest}.ycsb-a.g1.planner"
    payload = {
        "workload_descriptor": workload_descriptor,
        "descriptor_binding": {
            "output_sha256": content_digest,
            "content_digest_sha256": content_digest,
            "arm_binding_digest_sha256": arm_digest,
        },
    }
    payload_path = artifact_root / f"payload_{invocation_id}.json"
    envelope_path = artifact_root / f"envelope_{invocation_id}.json"
    payload_path.write_bytes(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8"))
    envelope_path.write_bytes(b'{"result":"fixture","type":"result"}')
    payload_sha256 = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    envelope_sha256 = hashlib.sha256(envelope_path.read_bytes()).hexdigest()
    event = {
        "invocation_id": invocation_id,
        "input_payload_sha256": payload_sha256,
        "provider_payload_sha256": payload_sha256,
        "provider_envelope_sha256": envelope_sha256,
        "provider_artifacts": {
            "payload_path": str(payload_path),
            "envelope_path": str(envelope_path),
            "arm_binding_digest_sha256": arm_digest,
        },
        "provenance": {
            "payload_sha256": payload_sha256,
            "envelope_sha256": envelope_sha256,
        },
    }
    if mutation == "payload-hash":
        event.pop("provider_payload_sha256")
    elif mutation == "envelope-hash":
        event["provider_envelope_sha256"] = "c" * 64
    elif mutation in {"missing-descriptor", "payload-descriptor"}:
        if mutation == "missing-descriptor":
            payload.pop("workload_descriptor")
        else:
            payload["workload_descriptor"] = other_arm_descriptor
        payload_path.write_bytes(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8"))
        changed = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        event["input_payload_sha256"] = changed
        event["provider_payload_sha256"] = changed
        event["provenance"]["payload_sha256"] = changed
    elif mutation == "payload-arm":
        payload["descriptor_binding"]["arm_binding_digest_sha256"] = "c" * 64
        payload_path.write_bytes(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8"))
        changed = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        event["input_payload_sha256"] = changed
        event["provider_payload_sha256"] = changed
        event["provenance"]["payload_sha256"] = changed
    elif mutation == "artifact-arm":
        event["provider_artifacts"].pop("arm_binding_digest_sha256")
    if mutation is None:
        C._check_registered_provider_artifacts(
            event=event, run_root=run,
            content_digest=content_digest, arm_binding_digest=arm_digest,
            arm="on",
        )
    else:
        with pytest.raises(
            C.AutonomousTrialCompletenessError,
            match=r"\[arm-digest-chain\] ",
        ):
            C._check_registered_provider_artifacts(
                event=event, run_root=run,
                content_digest=content_digest, arm_binding_digest=arm_digest,
                arm="on",
            )


def _off_provider_projection_fixture(tmp_path: Path, mutation: str | None):
    run = tmp_path / "off-provider-run"
    artifact_root = run / "provider" / "planner"
    artifact_root.mkdir(parents=True)
    descriptor = s8c_arm_inputs.derive_off_neutral_descriptor()
    content_digest = hashlib.sha256(
        s8c_arm_inputs.canonical_execution_input_bytes(descriptor)
    ).hexdigest()
    arm_digest = C._arm_binding_digest(
        holdout="H1", arm="off", content_digest=content_digest,
    )
    wrong_digest = "0" * 64
    if wrong_digest == content_digest:
        wrong_digest = "1" * 64
    audit_id = f"arm-off.exec-{arm_digest}.rr80.g1.planner"
    provider_id = (
        f"arm-off.exec-{content_digest}."
        f"{A.OFF_NEUTRAL_PAYLOAD_WORKLOAD}.g1.planner"
    )
    payload = {
        "workload": A.OFF_NEUTRAL_PAYLOAD_WORKLOAD,
        "workload_descriptor": descriptor,
        "descriptor_binding": {
            "input_sha256": content_digest,
            "output_sha256": content_digest,
            "projection_version": "8b-descriptor-projection/v1",
            "schema_sha256": C._DESCRIPTOR_SCHEMA_SHA256,
            "content_digest_sha256": content_digest,
        },
    }
    if mutation == "arm":
        payload["descriptor_binding"]["arm_binding_digest_sha256"] = arm_digest
    elif mutation == "workload":
        payload["workload"] = "rr80"
    elif mutation == "null-arm":
        payload["descriptor_binding"]["arm_binding_digest_sha256"] = None
    elif mutation == "input-digest":
        payload["descriptor_binding"]["input_sha256"] = wrong_digest
    elif mutation == "output-digest":
        payload["descriptor_binding"]["output_sha256"] = wrong_digest
    elif mutation == "content-digest":
        payload["descriptor_binding"]["content_digest_sha256"] = wrong_digest
    payload_raw = C._canonical_bytes(payload)
    envelope_raw = b'{"result":"fixture","type":"result"}'
    payload_path = artifact_root / f"payload_{provider_id}.json"
    envelope_path = artifact_root / f"envelope_{provider_id}.json"
    payload_path.write_bytes(payload_raw)
    envelope_path.write_bytes(envelope_raw)
    payload_sha256 = hashlib.sha256(payload_raw).hexdigest()
    envelope_sha256 = hashlib.sha256(envelope_raw).hexdigest()
    event = {
        "invocation_id": audit_id,
        "generation": 1,
        "role": "planner",
        "input_payload_sha256": payload_sha256,
        "provider_payload_sha256": payload_sha256,
        "provider_envelope_sha256": envelope_sha256,
        "provider_artifacts": {
            "payload_path": str(payload_path),
            "envelope_path": str(envelope_path),
            "arm_binding_digest_sha256": arm_digest,
        },
        "provenance": {
            "payload_sha256": payload_sha256,
            "envelope_sha256": envelope_sha256,
        },
    }
    return run, event, content_digest, arm_digest


@pytest.mark.parametrize(
    "mutation",
    [
        None, "arm", "workload", "null-arm", "input-digest", "output-digest",
        "content-digest",
    ],
    ids=[
        "positive", "arm-key", "holdout-workload", "null-arm-key",
        "input-digest", "output-digest", "content-digest",
    ],
)
def test_off_provider_payload_projection_has_exact_predicates(
    tmp_path: Path, mutation: str | None,
) -> None:
    run, event, content_digest, arm_digest = _off_provider_projection_fixture(
        tmp_path, mutation,
    )
    if mutation is None:
        C._check_registered_provider_artifacts(
            event=event,
            run_root=run,
            content_digest=content_digest,
            arm_binding_digest=arm_digest,
            arm="off",
        )
    else:
        with pytest.raises(
            C.AutonomousTrialCompletenessError,
            match=r"\[arm-digest-chain\] ",
        ):
            C._check_registered_provider_artifacts(
                event=event,
                run_root=run,
                content_digest=content_digest,
                arm_binding_digest=arm_digest,
                arm="off",
            )


def test_off_validation_receipt_safe_projection_is_exact(
    tmp_path: Path,
) -> None:
    run, _events, report, arm_execution = _registered_digest_chain_trial(
        tmp_path,
    )
    record = report["cells"][0]["generations"][0]["roles"]["planner"]
    content_digest = arm_execution["content_digest_sha256"]
    receipt = copy.deepcopy(record["payload_validation_receipt"])
    receipt["safe_projection"]["workload"] = A.OFF_NEUTRAL_PAYLOAD_WORKLOAD
    receipt["safe_projection"]["descriptor_binding_sha256"] = (
        C._off_payload_descriptor_binding_sha256(content_digest)
    )
    receipt["safe_projection_sha256"] = C._receipt_sha256(
        receipt["safe_projection"]
    )
    seal_preimage = {
        key: receipt[key]
        for key in (
            "schema_version", "role", "payload_sha256",
            "payload_allowlist_sha256", "safe_projection_sha256",
        )
    }
    receipt["seal_sha256"] = C._receipt_sha256(seal_preimage)
    record["payload_validation_receipt"] = receipt
    C._check_payload_validation_receipt(
        record,
        label="rr80.g1.planner",
        arm="off",
        content_digest=content_digest,
    )

    mutated = copy.deepcopy(record)
    mutated["payload_validation_receipt"]["safe_projection"]["workload"] = "rr80"
    projection = mutated["payload_validation_receipt"]["safe_projection"]
    mutated["payload_validation_receipt"]["safe_projection_sha256"] = (
        C._receipt_sha256(projection)
    )
    seal_preimage = {
        key: mutated["payload_validation_receipt"][key]
        for key in (
            "schema_version", "role", "payload_sha256",
            "payload_allowlist_sha256", "safe_projection_sha256",
        )
    }
    mutated["payload_validation_receipt"]["seal_sha256"] = C._receipt_sha256(
        seal_preimage
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[payload-validation-receipt\] .*safe identity differs$",
    ):
        C._check_payload_validation_receipt(
            mutated,
            label="rr80.g1.planner",
            arm="off",
            content_digest=content_digest,
        )


def test_t1311_authoritative_run_root_rejects_coordinated_tree_rebinding(
    tmp_path: Path,
) -> None:
    run, events, report, arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    cell = report["cells"][0]
    planner = cell["generations"][0]["roles"]["planner"]
    for role, event in cell["generations"][0]["roles"].items():
        if role != "planner":
            event["status"] = "skipped"
    report["provider"] = "claude-headless"
    invocation_id = planner["invocation_id"]
    provider_root = run / "provider" / "planner"
    provider_root.mkdir(parents=True)
    payload = {
        "workload_descriptor": cell["descriptor"],
        "descriptor_binding": cell["descriptor_binding"],
    }
    payload_path = provider_root / f"payload_{invocation_id}.json"
    envelope_path = provider_root / f"envelope_{invocation_id}.json"
    payload_path.write_bytes(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8"))
    envelope_path.write_bytes(b'{"result":"fixture","type":"result"}')
    payload_sha256 = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    envelope_sha256 = hashlib.sha256(envelope_path.read_bytes()).hexdigest()
    planner.update({
        "input_payload_sha256": payload_sha256,
        "provider_payload_sha256": payload_sha256,
        "provider_envelope_sha256": envelope_sha256,
        "provider_artifacts": {
            "payload_path": str(payload_path),
            "envelope_path": str(envelope_path),
            "arm_binding_digest_sha256": arm_execution[
                "arm_binding_digest_sha256"
            ],
        },
        "provenance": {
            "payload_sha256": payload_sha256,
            "envelope_sha256": envelope_sha256,
        },
    })
    _persist(run, events, report)
    _verify_digest_chain(run, events, report)

    other_run = tmp_path / "other-run"
    (other_run / "campaigns").mkdir(parents=True)
    old_campaign_root = Path(cell["campaign_root"])
    new_campaign_root = other_run / "campaigns" / old_campaign_root.name
    old_campaign_root.rename(new_campaign_root)
    cell["campaign_root"] = str(new_campaign_root)
    old_proposal = Path(cell["generations"][0]["proposal"]["path"])
    (other_run / "proposals").mkdir()
    new_proposal = other_run / "proposals" / old_proposal.name
    old_proposal.rename(new_proposal)
    cell["generations"][0]["proposal"]["path"] = str(new_proposal)
    new_provider_root = other_run / "provider" / "planner"
    new_provider_root.parent.mkdir()
    provider_root.rename(new_provider_root)
    planner["provider_artifacts"]["payload_path"] = str(
        new_provider_root / payload_path.name
    )
    planner["provider_artifacts"]["envelope_path"] = str(
        new_provider_root / envelope_path.name
    )
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[arm-digest-chain\].*(?:run root|identity/path differs)$",
    ):
        _verify_digest_chain(run, events, report)


def test_t1311_registered_build_keeps_artifacts_bound_to_trial_run_root(
    tmp_path: Path,
) -> None:
    run, events, report, _arm_execution = _registered_digest_chain_trial(
        tmp_path
    )
    report["do_build"] = True
    cell = report["cells"][0]
    old_campaign_root = Path(cell["campaign_root"])
    build_campaign_root = (
        tmp_path / "output" / "exploration" / "campaigns"
        / old_campaign_root.name
    )
    build_campaign_root.parent.mkdir(parents=True)
    old_campaign_root.rename(build_campaign_root)
    cell["campaign_root"] = str(build_campaign_root)
    _persist(run, events, report)
    _verify_digest_chain(run, events, report)


def _pending_critic_admission_failure_trial(tmp_path: Path):
    run, events, report = _complete_trial(tmp_path)
    cell = report["cells"][0]
    failure = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    report["status"] = "partial"
    report["do_build"] = True
    events[0]["do_build"] = True
    events[-1]["status"] = "partial"
    cell["admission_decision"] = failure
    cell["pending_critic_disposition"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-pending-critic-disposition/v1"
        ),
        "action": "discarded",
        "reason": "cell-admission-failure",
        "count": 1,
    }
    cell["generations"][0]["roles"].pop("critic")
    critic_event = next(
        event
        for event in events
        if event.get("event") == "role-attempt"
        and event.get("role") == "critic"
    )
    events.remove(critic_event)
    accounting = next(
        event
        for event in events
        if event.get("event") == "generation-accounting"
    )
    accounting.update({
        "state": "partial-generation",
        "provider_invoke_count": 3,
        "seq": 5,
    })
    events[-1].update({
        "seq": 6,
        "cell_admission_failures": [{
            "cell_index": 0,
            "workload": "ycsb-a",
            "admission_decision": failure,
        }],
    })
    report["honest_accounting"]["role_query_count"] = 3
    events[-1]["honest_accounting"]["role_query_count"] = 3
    _persist(run, events, report)
    return run, events, report


def _pre_audit_trial(tmp_path: Path):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    events = [_start(run, ["ycsb-a"])]
    cell_metadata = _golden_cell_metadata(run, "ycsb-a")
    roles = {}
    for seq, role in enumerate(("planner", "coder"), 2):
        event = _role_event(
            "ycsb-a", role, seq,
            workload_descriptor=cell_metadata["descriptor"],
        )
        events.append(event)
        roles[role] = copy.deepcopy(event)
    preview = {"passed": False, "forbidden_identifiers": []}
    auditor = _role_event(
        "ycsb-a", "auditor", 4, status="skipped", pre_audit=preview,
        workload_descriptor=cell_metadata["descriptor"],
    )
    events.append(auditor)
    roles["auditor"] = copy.deepcopy(auditor)
    critic = _role_event(
        "ycsb-a", "critic", 5, role_query_ordinal=3,
        workload_descriptor=cell_metadata["descriptor"],
    )
    events.append(critic)
    roles["critic"] = copy.deepcopy(critic)
    report["cells"] = [{
        "workload": "ycsb-a",
        **cell_metadata,
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
                "critic_digest_generated": False,
            },
            "outcome": "pre-audit-reject",
            "bench_wall_seconds": 0.0,
            "generation_driver": dict(_GENERATION_DRIVER),
            "gating_spec_sha256": _GATING_SPEC_SHA256,
        }],
        "stop_reason": "fixed-generation-budget",
    }]
    events.append(_generation_accounting(
        "ycsb-a", 1, 6, provider_invoke_count=3, auditor_skipped=True,
    ))
    report["honest_accounting"]["role_query_count"] = 3
    events.append(_finish(run, "complete", 7, role_query_count=3))
    _persist(run, events, report)
    return run, events, report


def _role_invalid_trial(tmp_path: Path):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    report["status"] = "partial"
    cell_metadata = _golden_cell_metadata(run, "ycsb-a")
    invalid = _role_event(
        "ycsb-a", "planner", 2, status="invalid",
        workload_descriptor=cell_metadata["descriptor"],
    )
    report["cells"] = [{
        "workload": "ycsb-a",
        **cell_metadata,
        "generations": [{
            "generation": 1,
            "roles": {"planner": copy.deepcopy(invalid)},
            "outcome": "planner-invalid",
            "bench_wall_seconds": 0.0,
            "generation_driver": dict(_GENERATION_DRIVER),
            "gating_spec_sha256": _GATING_SPEC_SHA256,
        }],
        "stop_reason": "role-invalid",
    }]
    accounting = _generation_accounting(
        "ycsb-a", 1, 3, provider_invoke_count=1,
        state="partial-generation",
    )
    report["honest_accounting"]["role_query_count"] = 1
    events = [
        _start(run, ["ycsb-a"]), invalid, accounting,
        _finish(run, "partial", 4, role_query_count=1),
    ]
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


def _generation_wall_trial(tmp_path: Path, *, budget: int = 1):
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"], budget=budget)
    report["status"] = "partial"
    report["cells"] = [{
        "workload": "ycsb-a",
        **_golden_cell_metadata(run, "ycsb-a"),
        "generations": [],
        "stop_reason": "supervisor-wall-budget",
    }]
    events = [_start(run, ["ycsb-a"], budget=budget)]
    if budget >= 2:
        report["fatal_error"] = {
            "type": "SupervisorWallBudget",
            "message": "wall budget expired before the next workload",
        }
        events.extend([
            {
                "event": "supervisor-wall-budget",
                "workload": "ycsb-a",
                "generation": 1,
                "zero_work": True,
                "role_query_count": 0,
                "bench_wall_seconds": 0.0,
                "seq": 2,
                "ts": "2026-08-01T00:00:02+00:00",
            },
        ])
    events.append(_finish(run, "partial", len(events) + 1))
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


def _transport_admission_error_trial(
    tmp_path: Path, *, do_build: bool = False,
):
    """Build the current producer's error/start/finish projection, not stale bytes."""
    run = tmp_path / "run"
    report = _report(run, ["ycsb-a"])
    report.update({
        "status": "partial",
        "provider": "claude-headless",
        "do_build": do_build,
        "fatal_error": {
            "type": "FixtureTransportError",
            "message": "fixture transport admission failed",
        },
    })
    start = _start(run, ["ycsb-a"])
    start.update({
        "provider": "claude-headless",
        "do_build": do_build,
        "seq": 2,
        "ts": "2026-08-01T00:00:02+00:00",
    })
    error = {
        "event": "transport-admission-error",
        **report["fatal_error"],
        "seq": 1,
        "ts": "2026-08-01T00:00:01+00:00",
    }
    events = [error, start, _finish(run, "partial", 3)]
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


def _replace_role_invalid_error_artifacts(
    events: list[dict], report: dict, error_artifacts: dict,
) -> None:
    events[1]["error_artifacts"] = copy.deepcopy(error_artifacts)
    report["cells"][0]["generations"][0]["roles"]["planner"][
        "error_artifacts"
    ] = copy.deepcopy(error_artifacts)


def test_invalid_role_event_requires_failure_phase(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    _replace_role_invalid_error_artifacts(events, report, {})
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts\."
            r"failure_phase is invalid$"
        ),
    ):
        _verify(run, report)


def test_invalid_role_event_rejects_unknown_failure_phase(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    _replace_role_invalid_error_artifacts(
        events, report, {"failure_phase": "fixture-unknown"},
    )
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts\."
            r"failure_phase is invalid$"
        ),
    ):
        _verify(run, report)


def test_post_raw_failure_requires_raw_response_pointer(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    _replace_role_invalid_error_artifacts(
        events, report, {"failure_phase": "role-schema"},
    )
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts "
            r"raw response pointer is required$"
        ),
    ):
        _verify(run, report)


def test_existing_raw_rejects_pre_raw_failure_phase(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    raw_path = run / "raw" / f"raw_{events[1]['invocation_id']}.txt"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_bytes(b"fixture invalid raw response")
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts\."
            r"failure_phase contradicts an existing raw response$"
        ),
    ):
        _verify(run, report)


def test_invalid_raw_response_pointer_rejects_sha256_mismatch(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    raw_path = run / "raw" / f"raw_{events[1]['invocation_id']}.txt"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_bytes(b"fixture invalid raw response")
    _replace_role_invalid_error_artifacts(events, report, {
        "failure_phase": "role-schema",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": "0" * 64,
    })
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts "
            r"raw response bytes differ from sha256$"
        ),
    ):
        _verify(run, report)


def test_invalid_raw_response_pointer_rejects_symlink(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    target = run / "raw" / "target.txt"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"fixture invalid raw response")
    raw_path = run / "raw" / f"raw_{events[1]['invocation_id']}.txt"
    raw_path.symlink_to(target)
    _replace_role_invalid_error_artifacts(events, report, {
        "failure_phase": "role-schema",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    })
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts\."
            r"raw_response_path traverses a symlink$"
        ),
    ):
        _verify(run, report)


def test_invalid_raw_response_pointer_rejects_unrelated_file(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    raw_path = run / "raw" / "unrelated.txt"
    raw_path.parent.mkdir(parents=True)
    raw_bytes = b"fixture invalid raw response"
    raw_path.write_bytes(raw_bytes)
    _replace_role_invalid_error_artifacts(events, report, {
        "failure_phase": "role-schema",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    })
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts\."
            r"raw_response_path differs from the invocation raw path$"
        ),
    ):
        _verify(run, report)


def test_invalid_raw_response_pointer_rejects_cwd_relative_path(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    raw_path = run / "raw" / f"raw_{events[1]['invocation_id']}.txt"
    raw_path.parent.mkdir(parents=True)
    raw_bytes = b"fixture invalid raw response"
    raw_path.write_bytes(raw_bytes)
    _replace_role_invalid_error_artifacts(events, report, {
        "failure_phase": "role-schema",
        "raw_response_path": str(Path("raw") / raw_path.name),
        "raw_response_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    })
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"raw_response_path differs from the invocation raw path$",
    ):
        _verify(run, report)


def test_invalid_raw_response_pointer_rejects_parent_symlink(tmp_path) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    raw_path = run / "raw" / f"raw_{events[1]['invocation_id']}.txt"
    raw_bytes = b"fixture invalid raw response"
    (outside / raw_path.name).write_bytes(raw_bytes)
    (run / "raw").symlink_to(outside, target_is_directory=True)
    _replace_role_invalid_error_artifacts(events, report, {
        "failure_phase": "role-schema",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    })
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"raw_response_path traverses a symlink$",
    ):
        _verify(run, report)


def test_invalid_raw_response_pointer_rejects_directory_after_binding(
    tmp_path, monkeypatch,
) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    raw_path = run / "raw" / f"raw_{events[1]['invocation_id']}.txt"
    raw_path.parent.mkdir(parents=True)
    raw_bytes = b"fixture invalid raw response"
    raw_path.write_bytes(raw_bytes)
    _replace_role_invalid_error_artifacts(events, report, {
        "failure_phase": "role-schema",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    })
    _persist(run, events, report)
    original = C._bound_regular_bytes

    def swap_to_directory_after_binding(value, *, run_root, gate, label):
        result = original(value, run_root=run_root, gate=gate, label=label)
        Path(value).unlink()
        Path(value).mkdir()
        return result

    monkeypatch.setattr(C, "_bound_regular_bytes", swap_to_directory_after_binding)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[role-event-shape\] journal role attempt\.error_artifacts\."
            r"raw_response_path is not a regular file$"
        ),
    ):
        _verify(run, report)


def test_invalid_raw_response_pointer_rejects_swap_after_binding(
    tmp_path, monkeypatch,
) -> None:
    run, events, report = _role_invalid_trial(tmp_path)
    raw_path = run / "raw" / f"raw_{events[1]['invocation_id']}.txt"
    raw_path.parent.mkdir(parents=True)
    raw_bytes = b"fixture invalid raw response"
    raw_path.write_bytes(raw_bytes)
    outside = tmp_path / "outside.txt"
    outside.write_bytes(raw_bytes)
    _replace_role_invalid_error_artifacts(events, report, {
        "failure_phase": "role-schema",
        "raw_response_path": str(raw_path),
        "raw_response_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    })
    _persist(run, events, report)
    original = C._bound_regular_bytes

    def swap_after_binding(value, *, run_root, gate, label):
        result = original(value, run_root=run_root, gate=gate, label=label)
        Path(value).unlink()
        Path(value).symlink_to(outside)
        return result

    monkeypatch.setattr(C, "_bound_regular_bytes", swap_after_binding)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"cannot be read from a no-follow file descriptor$",
    ):
        _verify(run, report)


def test_role_failure_phase_enums_match_producer() -> None:
    assert C._ROLE_FAILURE_PHASES == A.FAILURE_PHASES
    assert (
        C._ROLE_FAILURE_PHASES_AFTER_RAW_WRITE
        == A.FAILURE_PHASES_AFTER_RAW_WRITE
    )


def test_valid_role_event_passes_failure_phase_gate(tmp_path) -> None:
    run, _events, report = _complete_trial(tmp_path)
    _verify(run, report)


def test_p4_provider_init_error_with_empty_cells_passes(tmp_path) -> None:
    run, _events, report = _provider_init_trial(tmp_path)
    _verify(run, report)


def test_p5_generation_boundary_wall_budget_empty_generations_passes(tmp_path) -> None:
    run, _events, report = _generation_wall_trial(tmp_path)
    _verify(run, report)


def test_multigeneration_in_cell_zero_work_wall_budget_is_accepted(
    tmp_path,
) -> None:
    run, _events, report = _generation_wall_trial(tmp_path, budget=2)
    _verify(run, report)


def test_multigeneration_zero_work_wall_requires_terminal_accounting(
    tmp_path,
) -> None:
    run, events, report = _generation_wall_trial(tmp_path, budget=2)
    events[-2].pop("zero_work")
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[generation-accounting\] zero-work wall terminal fields differ$",
    ):
        _verify(run, report)


def test_multigeneration_in_cell_wall_budget_requires_its_cell(tmp_path) -> None:
    run, events, report = _generation_wall_trial(tmp_path, budget=2)
    report["cells"] = []
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[workload-coverage\] requested workload suffix is unexplained$",
    ):
        _verify(run, report)


def test_transport_admission_bound_shape_and_projection_passes(tmp_path) -> None:
    run, _events, report = _transport_admitted_trial(tmp_path)
    _verify(run, report)


def test_transport_admission_error_before_run_start_with_empty_cells_passes(
    tmp_path,
) -> None:
    run, events, report = _transport_admission_error_trial(
        tmp_path, do_build=True,
    )
    _verify(run, report)
    C.verify_autonomous_trial_files(run / "attempts.jsonl", run / "report.json")
    assert [event["event"] for event in events] == [
        "transport-admission-error", "run-start", "run-finish",
    ]
    assert report["cells"] == []
    assert report["honest_accounting"] == {
        "role_query_count": 0,
        "bench_wall_seconds": 0.0,
    }
    assert all("transport_receipt" not in event for event in events)
    assert "transport_receipt" not in report


def test_transport_admission_error_accepts_empty_string_message(tmp_path) -> None:
    run, events, report = _transport_admission_error_trial(tmp_path)
    events[0]["message"] = ""
    report["fatal_error"]["message"] = ""
    _persist(run, events, report)
    _verify(run, report)


def test_build_file_verification_with_cells_still_requires_campaign_root(
    tmp_path,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["do_build"] = True
    events[0]["do_build"] = True
    report["cells"][0]["admission_decision"] = {
        "schema_version": "campaign-artifact-admission-decision/v1",
        "admission_status": "admitted",
        "classification": "admitted-new-schema",
    }
    _persist(run, events, report)
    _verify(run, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[campaign-chain\] build trial verification requires "
            r"campaign_output_root$"
        ),
    ):
        C.verify_autonomous_trial_files(
            run / "attempts.jsonl", run / "report.json",
        )


def test_query_ordinals_must_be_contiguous_and_exclude_skips(tmp_path) -> None:
    run, events, report = _pre_audit_trial(tmp_path)
    critic = next(
        event for event in events
        if event.get("event") == "role-attempt" and event.get("role") == "critic"
    )
    critic["role_query_ordinal"] = 4
    report["cells"][0]["generations"][0]["roles"]["critic"][
        "role_query_ordinal"
    ] = 4
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[query-ordinal\] provider query ordinals are not contiguous$",
    ):
        _verify(run, report)


def test_generation_accounting_must_be_bijective(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    events.pop(-2)
    events[-1]["seq"] = 6
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[generation-accounting\] missing accounting pair",
    ):
        _verify(run, report)


@pytest.mark.parametrize(
    "mutated_state",
    ["generation-complete", "pending-pre-invoke-failure"],
)
def test_discarded_final_critic_requires_partial_generation_accounting(
    tmp_path, mutated_state,
) -> None:
    run, events, report = _pending_critic_admission_failure_trial(tmp_path)
    _verify(run, report)
    accounting = next(
        event
        for event in events
        if event.get("event") == "generation-accounting"
    )
    accounting["state"] = mutated_state
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[generation-accounting\] discarded final critic requires "
            r"partial-generation accounting$"
        ),
    ):
        _verify(run, report)


def test_report_accounting_must_equal_journal_derived_totals(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["honest_accounting"]["role_query_count"] = 5
    events[-1]["honest_accounting"]["role_query_count"] = 5
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[generation-accounting\] report role query total differs$",
    ):
        _verify(run, report)


def test_accounting_rejects_negative_bench_values(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    accounting = events[-2]
    accounting["bench_wall_seconds"] = -1.0
    report["cells"][0]["generations"][0]["bench_wall_seconds"] = -1.0
    report["honest_accounting"]["bench_wall_seconds"] = -1.0
    events[-1]["honest_accounting"]["bench_wall_seconds"] = -1.0
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[run-envelope\] bench_wall_seconds is not finite and nonnegative$",
    ):
        _verify(run, report)


def test_large_consistent_bench_time_is_not_a_budget_gate(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    large = 10_000_000.0
    events[-2]["bench_wall_seconds"] = large
    report["cells"][0]["generations"][0]["bench_wall_seconds"] = large
    report["honest_accounting"]["bench_wall_seconds"] = large
    events[-1]["honest_accounting"]["bench_wall_seconds"] = large
    _persist(run, events, report)
    _verify(run, report)


@pytest.mark.parametrize("field", ["generation_driver", "gating_spec_sha256"])
def test_generation_driver_and_gating_spec_digest_must_be_stable(
    tmp_path, field,
) -> None:
    run, events, report = _complete_trial(tmp_path / field)
    events[-2][field] = (
        {"wrapper": "wrong", "delegate": "trigger.drive_iteration"}
        if field == "generation_driver"
        else "0" * 64
    )
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[generation-accounting\].*{'driver identity' if field == 'generation_driver' else 'GATING_SPEC digest'} differs$",
    ):
        _verify(run, report)


def test_role_payload_exact_keys_are_independently_rechecked(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    planner = events[1]
    planner["payload_exact_keys"] = sorted(
        [*planner["payload_exact_keys"], "unlisted-performance-channel"]
    )
    report["cells"][0]["generations"][0]["roles"]["planner"][
        "payload_exact_keys"
    ] = list(planner["payload_exact_keys"])
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[payload-allowlist\].*exact payload keys differ$",
    ):
        _verify(run, report)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing", "is not a Mapping"),
        ("payload-digest", "receipt payload digest differs"),
        ("workload-descriptor", "workload descriptor digest differs"),
        ("fixed-literal", "fixed literals differ"),
        ("whiteboard-origin", "whiteboard origin digest differs"),
        ("seal", "receipt seal differs"),
    ],
)
def test_payload_validation_receipt_is_independently_rechecked(
    tmp_path, mutation, message,
) -> None:
    run, events, report = _complete_trial(tmp_path / mutation)
    planner = events[1]
    report_planner = report["cells"][0]["generations"][0]["roles"]["planner"]
    if mutation == "missing":
        planner.pop("payload_validation_receipt")
        report_planner.pop("payload_validation_receipt")
    else:
        for target in (planner, report_planner):
            receipt = target["payload_validation_receipt"]
            if mutation == "payload-digest":
                receipt["payload_sha256"] = "0" * 64
            elif mutation == "workload-descriptor":
                receipt["safe_projection"][
                    "workload_descriptor_sha256"
                ] = "0" * 64
                receipt["safe_projection_sha256"] = C._receipt_sha256(
                    receipt["safe_projection"]
                )
                seal_preimage = {
                    key: receipt[key]
                    for key in (
                        "schema_version", "role", "payload_sha256",
                        "payload_allowlist_sha256", "safe_projection_sha256",
                    )
                }
                receipt["seal_sha256"] = C._receipt_sha256(seal_preimage)
            elif mutation == "fixed-literal":
                receipt["safe_projection"]["fixed_literals"][
                    "scientific_claim"
                ] = True
                receipt["safe_projection_sha256"] = C._receipt_sha256(
                    receipt["safe_projection"]
                )
            elif mutation == "whiteboard-origin":
                receipt["safe_projection"]["whiteboard_origin_sha256"] = "0" * 64
                receipt["safe_projection_sha256"] = C._receipt_sha256(
                    receipt["safe_projection"]
                )
            else:
                receipt["seal_sha256"] = "0" * 64
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[payload-validation-receipt\].*{message}$",
    ):
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


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("duplicate-error", r"transport admission outcome may occur at most once"),
        ("success-and-error", r"transport admission outcome may occur at most once"),
        (
            "after-run-start",
            r"transport-admission-error must occur immediately before run-start",
        ),
        (
            "extra-field",
            r"transport-admission-error fields must match the producer exact set",
        ),
        (
            "empty-type",
            r"transport-admission-error\.type must be a non-empty string",
        ),
        (
            "non-string-type",
            r"transport-admission-error\.type must be a non-empty string",
        ),
        (
            "non-string-message",
            r"transport-admission-error\.message must be a string",
        ),
        (
            "wrong-provider",
            r"transport-admission-error requires the claude-headless provider",
        ),
        (
            "forged-report-receipt",
            r"transport-admission-error outcome forbids transport_receipt",
        ),
        (
            "forged-run-start-receipt",
            r"transport-admission-error outcome forbids transport_receipt",
        ),
        (
            "forged-run-finish-receipt",
            r"transport-admission-error outcome forbids transport_receipt",
        ),
        (
            "fatal-mismatch",
            r"transport-admission-error projection is inconsistent",
        ),
        (
            "nonempty-cells",
            r"transport-admission-error projection is inconsistent",
        ),
        (
            "complete-status",
            r"terminal supervisor event requires partial status",
        ),
    ],
    ids=[
        "duplicate-error",
        "success-and-error",
        "after-run-start",
        "extra-field",
        "empty-type",
        "non-string-type",
        "non-string-message",
        "wrong-provider",
        "forged-report-receipt",
        "forged-run-start-receipt",
        "forged-run-finish-receipt",
        "fatal-mismatch",
        "nonempty-cells",
        "complete-status",
    ],
)
def test_transport_admission_error_mutations_are_rejected(
    tmp_path, mutation, expected,
) -> None:
    run, events, report = _transport_admission_error_trial(tmp_path)
    if mutation == "duplicate-error":
        events.insert(1, copy.deepcopy(events[0]))
    elif mutation == "success-and-error":
        events.insert(1, {
            "event": "transport-admission",
            "transport_receipt": copy.deepcopy(_TRANSPORT_RECEIPT),
            "seq": 2,
            "ts": "2026-08-01T00:00:02+00:00",
        })
    elif mutation == "after-run-start":
        events[0], events[1] = events[1], events[0]
    elif mutation == "extra-field":
        events[0]["unexpected"] = True
    elif mutation == "empty-type":
        events[0]["type"] = ""
    elif mutation == "non-string-type":
        events[0]["type"] = 1
    elif mutation == "non-string-message":
        events[0]["message"] = None
    elif mutation == "wrong-provider":
        report["provider"] = "fixture"
        events[1]["provider"] = "fixture"
    elif mutation == "forged-report-receipt":
        report["transport_receipt"] = copy.deepcopy(_TRANSPORT_RECEIPT)
    elif mutation == "forged-run-start-receipt":
        events[1]["transport_receipt"] = copy.deepcopy(_TRANSPORT_RECEIPT)
    elif mutation == "forged-run-finish-receipt":
        events[-1]["transport_receipt"] = copy.deepcopy(_TRANSPORT_RECEIPT)
    elif mutation == "fatal-mismatch":
        report["fatal_error"]["message"] = "different failure"
    elif mutation == "nonempty-cells":
        report["cells"] = [{
            "admission_decision": {"admission_status": "not-applicable"},
        }]
    else:
        report["status"] = "complete"
        events[-1]["status"] = "complete"
    for seq, event in enumerate(events, 1):
        event["seq"] = seq
    _persist(run, events, report)
    gate = (
        "terminal-projection"
        if mutation in {"fatal-mismatch", "nonempty-cells", "complete-status"}
        else "transport-admission"
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=rf"\[{gate}\] {expected}$",
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
    invalid_planner = _role_event(
        "ycsb-a", "planner", 2, status="invalid",
        workload_descriptor=report["cells"][0]["descriptor"],
    )
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
    if target == "report":
        with pytest.raises(
            C.AutonomousTrialCompletenessError,
            match=r"\[run-envelope\] report\.schema_version does not match producer version$",
        ):
            _verify(run, report)
    else:
        with pytest.raises(C.AutonomousTrialCompletenessError) as exc:
            _verify(run, report)
        assert str(exc.value) == (
            "[run-envelope] run-start.schema_version unsupported: recorded=None; "
            "generation=unknown; consumer_supported='p3-autonomous-workload-trial/v4'"
        )


def test_role_schema_v4_and_report_schema_v3_are_required(tmp_path) -> None:
    assert A.SCHEMA_VERSION == "p3-autonomous-workload-trial/v4"
    assert A.REPORT_SCHEMA_VERSION == "p3-autonomous-workload-trial-report/v3"
    assert _TRIAL_SCHEMA_VERSION == "p3-autonomous-workload-trial/v4"
    assert _REPORT_SCHEMA_VERSION == "p3-autonomous-workload-trial-report/v3"
    for target in ("start", "report"):
        run, events, report = _complete_trial(tmp_path / target)
        if target == "start":
            events[0]["schema_version"] = "p3-autonomous-workload-trial/v3"
        else:
            report["schema_version"] = "p3-autonomous-workload-trial-report/v2"
        _persist(run, events, report)
        if target == "report":
            with pytest.raises(
                C.AutonomousTrialCompletenessError,
                match=r"\[run-envelope\] report.schema_version does not match producer version$",
            ):
                _verify(run, report)
        else:
            with pytest.raises(C.AutonomousTrialCompletenessError) as exc:
                _verify(run, report)
            assert str(exc.value) == (
                "[run-envelope] run-start.schema_version unsupported: "
                "recorded='p3-autonomous-workload-trial/v3'; generation=legacy; "
                "consumer_supported='p3-autonomous-workload-trial/v4'"
            )


def test_run_start_v4_without_binding_is_accepted(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    start = events[0]
    assert start["schema_version"] == "p3-autonomous-workload-trial/v4"
    assert {"generation_driver", "gating_spec_sha256", "honest_accounting_authority"} <= start.keys()
    assert {
        "prereg_commit", "prereg_content_commit", "prereg_effective_commit",
        "slot_id", "measurement_head", "manifest_sha256", "arm_execution",
    }.isdisjoint(start)
    _verify(run, report)


def test_run_start_v3_legacy_shape_is_rejected(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    start = events[0]
    start["schema_version"] = "p3-autonomous-workload-trial/v3"
    for key in ("generation_driver", "gating_spec_sha256", "honest_accounting_authority"):
        del start[key]
    assert set(start) == {
        "event", "schema_version", "trial_id", "provider", "workloads",
        "generation_budget_per_workload", "max_wall_s", "do_build",
        "performance_early_stop", "scientific_claim", "launch_admission", "seq", "ts",
    }
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError) as exc:
        _verify(run, report)
    assert str(exc.value) == (
        "[run-envelope] run-start.schema_version unsupported: "
        "recorded='p3-autonomous-workload-trial/v3'; generation=legacy; "
        "consumer_supported='p3-autonomous-workload-trial/v4'"
    )


def test_run_start_unknown_schema_version_is_rejected(tmp_path) -> None:
    run, events, report = _complete_trial(tmp_path)
    events[0]["schema_version"] = "p3-autonomous-workload-trial/v99"
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError) as exc:
        _verify(run, report)
    assert str(exc.value) == (
        "[run-envelope] run-start.schema_version unsupported: "
        "recorded='p3-autonomous-workload-trial/v99'; generation=unknown; "
        "consumer_supported='p3-autonomous-workload-trial/v4'"
    )


def test_run_start_schema_version_is_independent_of_producer(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(A, "SCHEMA_VERSION", "p3-autonomous-workload-trial/v5-fixture")
    run, events, report = _complete_trial(tmp_path)
    assert events[0]["schema_version"] == "p3-autonomous-workload-trial/v4"
    _verify(run, report)
    events[0]["schema_version"] = "p3-autonomous-workload-trial/v5-fixture"
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError) as exc:
        _verify(run, report)
    assert str(exc.value) == (
        "[run-envelope] run-start.schema_version unsupported: "
        "recorded='p3-autonomous-workload-trial/v5-fixture'; generation=unknown; "
        "consumer_supported='p3-autonomous-workload-trial/v4'"
    )


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
    events[0]["generation_budget_per_workload"] = 3
    report["generation_budget_per_workload"] = 3
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
    cell_metadata = _golden_cell_metadata(run, "ycsb-a")
    roles = {}
    for seq, role in enumerate(_ROLES, 2):
        event = _role_event(
            "ycsb-a", role, seq, generation=1,
            workload_descriptor=cell_metadata["descriptor"],
        )
        events.append(event)
        roles[role] = copy.deepcopy(event)
    invalid = _role_event(
        "ycsb-a", "planner", 6, status="invalid", generation=2,
        workload_descriptor=cell_metadata["descriptor"],
    )
    events.append(invalid)
    report["cells"] = [{
        "workload": "ycsb-a",
        **cell_metadata,
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
                    "critic_digest_generated": False,
                },
                "outcome": "fixture-terminal",
                "bench_wall_seconds": 0.0,
                "generation_driver": dict(_GENERATION_DRIVER),
                "gating_spec_sha256": _GATING_SPEC_SHA256,
            },
            {
                "generation": 2,
                "roles": {"planner": copy.deepcopy(invalid)},
                "outcome": "planner-invalid",
                "bench_wall_seconds": 0.0,
                "generation_driver": dict(_GENERATION_DRIVER),
                "gating_spec_sha256": _GATING_SPEC_SHA256,
            },
        ],
        "stop_reason": "role-invalid",
    }]
    events.append(_generation_accounting(
        "ycsb-a", 1, 7, provider_invoke_count=4,
    ))
    events.append(_generation_accounting(
        "ycsb-a", 2, 8, provider_invoke_count=1,
        state="partial-generation",
    ))
    report["honest_accounting"]["role_query_count"] = 5
    events.append(_finish(run, "partial", 9, role_query_count=5))
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
            "critic_digest_generated": False,
            "trigger_gate_binding_commitment": "b" * 64,
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
    assert auditor["role_query_ordinal"] is None
    assert report["honest_accounting"]["role_query_count"] == 3
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
    events[-1]["seq"] = 8
    events.insert(-1, {"event": "unknown-event", "seq": 7, "ts": "fixture"})
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[closed-event-set\] journal event 6 has unknown kind: 'unknown-event'$",
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
    cell_metadata = _golden_cell_metadata(run, "ycsb-a")
    report_roles = {}
    for seq, role in enumerate(roles, 2):
        event = _role_event(
            "ycsb-a", role, seq, generation=generation,
            workload_descriptor=cell_metadata["descriptor"],
        )
        events.append(event)
        report_roles[role] = copy.deepcopy(event)
    report["cells"] = [{
        "workload": "ycsb-a",
        **cell_metadata,
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


def test_launch_admission_keys_are_closed_seven_or_eight_key_alternatives(
    tmp_path: Path,
) -> None:
    base_keys = frozenset(_launch_admission(["ycsb-a"]))
    assert C._LAUNCH_ADMISSION_KEYS == frozenset({
        base_keys,
        base_keys | {"origin_binding"},
    })

    run, events, report = _complete_trial(tmp_path)
    launch_admission = _origin_bound_launch_admission()
    events[0]["launch_admission"] = copy.deepcopy(launch_admission)
    report["launch_admission"] = copy.deepcopy(launch_admission)
    _persist(run, events, report)
    _verify(run, report)


@pytest.mark.parametrize("value", [None, {"unexpected": True}])
def test_origin_binding_null_or_unknown_shape_is_rejected(
    tmp_path: Path,
    value: object,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    events[0]["launch_admission"]["origin_binding"] = copy.deepcopy(value)
    report["launch_admission"]["origin_binding"] = copy.deepcopy(value)
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[launch-admission\] ",
    ):
        _verify(run, report)


def test_launch_admission_unknown_top_level_key_remains_rejected(
    tmp_path: Path,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    events[0]["launch_admission"]["future_key"] = "not-admitted"
    report["launch_admission"]["future_key"] = "not-admitted"
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[launch-admission\] report launch_admission exact keys differ$",
    ):
        _verify(run, report)


@pytest.mark.parametrize("rejected", [True, False])
def test_origin_terminal_projection_has_the_formal_consumer_shape(
    tmp_path: Path,
    rejected: bool,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["origin_terminal_projection"] = _origin_terminal_projection(
        rejected=rejected,
    )
    _persist(run, events, report)
    _verify(run, report)


def test_rejected_origin_terminal_projection_rejects_non_null_receipt(
    tmp_path: Path,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    projection = _origin_terminal_projection(rejected=True)
    projection["formal_receipt_sha256"] = "8" * 64
    report["origin_terminal_projection"] = projection
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[origin-terminal-projection\] ",
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
    first = _role_event(
        "ycsb-a", "planner", 2,
        workload_descriptor=_golden_cell_metadata(
            Path("/fixture"), "ycsb-a",
        )["descriptor"],
    )
    duplicate = copy.deepcopy(first)
    duplicate["seq"] = 3
    duplicate["ts"] = "2026-08-01T00:00:03+00:00"
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[logical-id\] journal has a duplicate logical role attempt ID$",
    ):
        C._require_unique_attempts(
            [first, duplicate], side="journal", run_root=Path("/fixture"),
        )


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


def _cross_binding_source_preimage(
    assignment: str, *, extra_gate_line: str | None = None,
) -> bytes:
    contexts = []
    for index in range(len(source_digest.CONTEXT_MACROS) + 1):
        lines = [
            f"[ctx:{index}]".encode("ascii"),
            b"bool izanagi_gate_pass = true;",
            assignment.encode("utf-8"),
            b"if (izanagi_gate_pass) {",
        ]
        if extra_gate_line is not None:
            lines.append(extra_gate_line.encode("utf-8"))
        contexts.append(b"\n".join(lines))
    segments = [
        f"fixture-source-{index}".encode("ascii")
        for index, _path in enumerate(source_digest.EVOLVE_BLOCK_SOURCES)
    ]
    source_index = source_digest.EVOLVE_BLOCK_SOURCES.index(
        "cc/silo/transaction.cc"
    )
    segments[source_index] = b"\x02".join(contexts)
    return b"\0".join(segments)


def _layer3_campaign(
    tmp_path: Path, *, trial_id: str = "fixture-completeness",
    workload: str = "ycsb-a", output_root: Path | None = None,
    include_trigger_binding: bool = True, include_bench_wall_s: bool = True,
    include_bench_done: bool = True,
    proposal_path: Path | None = None,
    source_preimage_bytes: bytes | None = None,
    source_src_token: str | None = None,
):
    output_root = output_root or tmp_path / "output"
    metadata = _golden_cell_metadata(output_root, workload, trial_id=trial_id)
    workload_flags = metadata["workload_flags"]
    descriptor = metadata["descriptor"]
    descriptor_binding = metadata["descriptor_binding"]
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    search_config = {
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
    }
    if not include_trigger_binding:
        # Layer 3 intentionally projects trigger_binding WAL records out of
        # variants.  This dedicated cross-binding fixture therefore models a
        # non-trigger campaign so the verifier's full WAL coverage has no
        # excluded record to account for.
        search_config["axis"] = "fixture"
        search_config.pop("reflux")
        search_config.pop("trigger_gate_binding_schema")
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
        search_config=search_config,
        trial=f"{trial_id}-{workload}",
    )
    campaign_cfg = ident.bind_environment_contract(
        campaign_cfg, _T530_LAYER3_CONTRACT,
    )
    campaign_id = str(ident.campaign_id(campaign_cfg))
    # T-671 で H が identity から外れ、current は policy-bound 値になる。
    if include_trigger_binding:
        assert campaign_id == _CURRENT_POLICY_BOUND_CAMPAIGN_IDS[(trial_id, workload)]
    metadata["campaign_id"] = campaign_id
    metadata["campaign_root"] = str(output_root / "campaigns" / campaign_id)
    campaign = output_root / "campaigns" / campaign_id
    layout = CampaignLayout(root=str(campaign)).ensure()
    assert ident.ensure_campaign_identity(
        campaign_cfg, layout, admission_policy=context.policy,
    )
    assert Path(layout.lock_file).read_text(encoding="utf-8") == build_v2_lock(
        ident.canonical_preimage(campaign_cfg)
    )
    state_path = campaign / "loop_state.json"
    state_path.write_text(
        json.dumps({"whiteboard": []}), encoding="utf-8",
    )
    genome_value = Genome("fixture", {})
    genome = genome_value.canonical()
    source_bytes_sha256 = (
        hashlib.sha256(source_preimage_bytes).hexdigest()
        if source_preimage_bytes is not None else "a" * 64
    )
    src_token = "stock"
    if source_preimage_bytes is not None:
        src_token = source_src_token or source_bytes_sha256
    variant = P.variant_id(genome_value, src_token)
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(tmp_path.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(genome.encode()).hexdigest(),
        src_token=src_token,
        source_bytes_sha256=source_bytes_sha256,
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )
    generator_receipt = None
    if source_preimage_bytes is not None:
        generator_receipt = attest_generator_output(
            context,
            evidence,
            generator_input_sha256=(
                hashlib.sha256(proposal_path.read_bytes()).hexdigest()
                if proposal_path is not None else "d" * 64
            ),
        )
    receipt = derive_build_admission(
        context, evidence, generator_receipt=generator_receipt,
    ).as_wal_receipt()
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
    build_start = {
        "ts": 1.0, "stage": "build_start", "variant": variant,
        "env_tag": _T530_LAYER3_CONTRACT.env_tag, "payload": {
            "build_attempt_id": attempt_id,
            "genome": genome,
            "src_token": src_token,
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        },
    }
    if include_trigger_binding:
        records = [{
            "ts": 0.5, "stage": TGB.WAL_RECORD_STAGE, "variant": variant,
            "env_tag": _T530_LAYER3_CONTRACT.env_tag, "payload": {
                "build_attempt_id": attempt_id,
                "trigger_gate_binding": TGB.to_record(binding),
            },
        }]
        build_start["payload"]["trigger_gate_binding_commitment"] = binding_commitment
    else:
        records = []
    bench_payload = {
        "tps": [1.0], "median_tps": 1.0, "cv": 0.0, "rounds": 1,
        "build_attempt_id": attempt_id,
    }
    if include_bench_wall_s:
        bench_payload["bench_wall_s"] = 0.0
    bench_payload["leading_indicators"] = {}
    records.append(build_start)
    if include_bench_done:
        records.extend([
            {
                "ts": 2.0, "stage": "build_done", "variant": variant,
                "env_tag": _T530_LAYER3_CONTRACT.env_tag, "payload": dict(terminal),
            },
            {
                "ts": 3.0, "stage": "bench_done", "variant": variant,
                "env_tag": _T530_LAYER3_CONTRACT.env_tag,
                "payload": bench_payload,
            },
        ])
        for index, tag in enumerate((P.LEGACY_TAG, P.S2_TAG), 1):
            records.append({
                "ts": 3.0 + index / 4,
                "stage": "verify_done",
                "variant": variant,
                "env_tag": _T530_LAYER3_CONTRACT.env_tag,
                "payload": {
                    "build_attempt_id": attempt_id,
                    "verdict": "serializable",
                    "certified": True,
                    "anomalies": 0,
                    "workload": {"tag": tag},
                },
            })
    else:
        records.append({
            "ts": 2.0, "stage": "abort", "variant": variant,
            "env_tag": _T530_LAYER3_CONTRACT.env_tag,
            "payload": {**terminal, "reason": "build-error"},
        })
    wal_path = campaign / "runs" / "wal.jsonl"
    wal_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    if include_bench_done:
        receipt_support.log_receipted_commit(
            layout,
            variant,
            _T530_LAYER3_CONTRACT.env_tag,
            {
                **terminal,
                "contract_sha256": _T530_CONTRACT_SHA256,
            },
            operation_identity=attempt_id,
            tags=(P.LEGACY_TAG, P.S2_TAG),
            ts=4.0,
        )
    if include_trigger_binding:
        provenance_entry = {
            "variant": variant,
            "build_attempt_id": attempt_id,
            "trigger_gate_binding_commitment": binding_commitment,
            "outcome": "certified" if include_bench_done else "aborted",
        }
        if proposal_path is not None:
            provenance_entry["proposal_path"] = str(proposal_path)
        (campaign / "reports" / "p3_s8a_trigger_loop_provenance.json").write_text(
            json.dumps({
                "entries": {
                    "fixture": provenance_entry,
                },
            }),
            encoding="utf-8",
        )
    if proposal_path is not None and source_preimage_bytes is not None:
        proposal_sha256 = hashlib.sha256(proposal_path.read_bytes()).hexdigest()
        relative = source_digest.source_preimage_artifact_relative_path(
            proposal_sha256
        )
        artifact_path = campaign / relative
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(source_preimage_bytes)
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


def _cross_binding_fixture(
    tmp_path: Path, *, include_bench_wall_s: bool = True,
    include_bench_done: bool = True, proposal_wire: str = "00000",
    preimage_wire: str | None = None,
    preimage_assignment: str | None = None,
    extra_gate_line: str | None = None,
    source_src_token: str | None = None,
):
    run_root = tmp_path / "cross-binding-run"
    (run_root / "raw").mkdir(parents=True)
    (run_root / "provider").mkdir()
    (run_root / "proposals").mkdir()
    raw_path = run_root / "raw" / "response.txt"
    payload_path = run_root / "provider" / "payload_invocation.json"
    envelope_path = run_root / "provider" / "envelope_invocation.json"
    proposal_path = run_root / "proposals" / "proposal.json"
    raw_path.write_bytes(b"fixture raw response\n")
    payload_path.write_bytes(b"fixture provider payload\n")
    envelope_path.write_bytes(b"fixture provider envelope\n")
    proposal_value = {
        "planner": {
            "axis": "silo-backoff-trigger-gating", "direction": "increase",
            "magnitude": "small", "justification": "fixture", "uncertainty": "low",
        },
        "coder": {
            "axis": "silo-backoff-trigger-gating", "wire": proposal_wire,
            "justification": "fixture", "confidence": "high",
        },
        "auditor": {
            "verdict": "allow", "diff_digest": "a" * 64,
            "violations": [], "nits": [], "proposed_tests": [], "uncertainty": "low",
        },
        "prior_critic_reverse": False,
        "descriptor_sha256": "b" * 64,
        "arm_binding_digest_sha256": "c" * 64,
    }
    proposal_path.write_bytes(C._canonical_bytes(proposal_value))
    assignment = preimage_assignment or reflux_ir.emit_predicate(
        reflux_ir.parse_wire(preimage_wire or proposal_wire)
    )
    source_preimage = _cross_binding_source_preimage(
        assignment, extra_gate_line=extra_gate_line,
    )
    output_root, campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path, include_bench_wall_s=include_bench_wall_s,
        include_bench_done=include_bench_done,
        proposal_path=proposal_path, source_preimage_bytes=source_preimage,
        source_src_token=source_src_token,
    )

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    event = {
        "event": "role-attempt",
        "invocation_id": "fixture.invocation",
        "raw_response_path": str(raw_path.relative_to(run_root)),
        "raw_response_sha256": digest(raw_path),
        "input_payload_sha256": digest(payload_path),
        "provider_payload_sha256": digest(payload_path),
        "provider_envelope_sha256": digest(envelope_path),
        "provider_artifacts": {
            "payload_path": str(payload_path.relative_to(run_root)),
            "envelope_path": str(envelope_path.relative_to(run_root)),
            "arm_binding_digest_sha256": "a" * 64,
        },
    }
    wal_lines = [
        json.loads(line)
        for line in (campaign / "runs" / "wal.jsonl").read_text().splitlines()
    ]
    bench = next(
        (row for row in wal_lines if row["stage"] == "bench_done"), None,
    )
    proposal = {
        "path": str(proposal_path.relative_to(run_root)),
        "sha256": digest(proposal_path),
        "digest": "b" * 64,
    }
    cell = copy.deepcopy(cell)
    bench_payload = copy.deepcopy(bench["payload"]) if bench is not None else {}
    cell["generations"] = [{
        "generation": 1,
        "proposal": proposal,
        "harness": {
            "variant": bench["variant"] if bench is not None else None,
            "records": ({"bench_done": bench_payload} if bench is not None else {}),
        },
        "bench_wall_seconds": bench_payload.get("bench_wall_s", 0.0),
    }]
    report = {
        "trial_id": "fixture-completeness",
        "do_build": True,
        "generation_driver": dict(C._STANDARD_GENERATION_DRIVER),
        "cells": [cell],
    }
    return {
        "output_root": output_root,
        "campaign": campaign,
        "persisted_path": persisted_path,
        "persisted": persisted,
        "run_root": run_root,
        "report": report,
        "events": [event],
    }


def _write_cross_binding_layer3(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _refresh_cross_binding_layer3(fixture: dict) -> None:
    fixture["persisted_path"].unlink()
    persisted = L3.build_report(
        fixture["campaign"], generated_from_head="a" * 40,
        output_root=fixture["output_root"],
    )
    _write_cross_binding_layer3(fixture["persisted_path"], persisted)
    fixture["persisted"] = persisted
    fixture["report"]["cells"][0]["admission_decision"] = copy.deepcopy(
        persisted["admission_decision"]
    )


def _rewrite_cross_binding_proposal(
    fixture: dict, mutate,
) -> tuple[str, str]:
    record = fixture["report"]["cells"][0]["generations"][0]["proposal"]
    path = fixture["run_root"] / record["path"]
    old_sha256 = record["sha256"]
    value = json.loads(path.read_bytes())
    mutate(value)
    path.write_bytes(C._canonical_bytes(value))
    new_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    record["sha256"] = new_sha256
    return old_sha256, new_sha256


def _add_cross_binding_abort_attempt(fixture: dict) -> None:
    proposal_one = fixture["run_root"] / "proposals/proposal.json"
    proposal_value = json.loads(proposal_one.read_bytes())
    proposal_value["coder"]["wire"] = "10000"
    proposal_two = fixture["run_root"] / "proposals/proposal-abort.json"
    proposal_two.write_bytes(C._canonical_bytes(proposal_value))
    proposal_sha256 = hashlib.sha256(proposal_two.read_bytes()).hexdigest()
    genome_value = Genome("fixture", {})
    genome = genome_value.canonical()
    variant = "diffq-" + hashlib.sha256(
        (genome + "|impl=fixture-abort").encode("utf-8")
    ).hexdigest()[:12]
    attempt_id = "attempt-abort"
    binding = TGB.TriggerGateBinding(
        mask=1,
        predicate_sha256=TGB.expected_predicate_sha256(1),
        nonce="2" * 64,
        source=None,
    )
    binding_commitment = TGB.commitment(binding)
    wal_path = fixture["campaign"] / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_bytes().splitlines()]
    records.extend([
        {
            "ts": 5.0, "stage": TGB.WAL_RECORD_STAGE, "variant": variant,
            "env_tag": _T530_LAYER3_CONTRACT.env_tag,
            "payload": {
                "build_attempt_id": attempt_id,
                "trigger_gate_binding": TGB.to_record(binding),
            },
        },
        {
            "ts": 6.0, "stage": "build_start", "variant": variant,
            "env_tag": _T530_LAYER3_CONTRACT.env_tag,
            "payload": {
                "build_attempt_id": attempt_id,
                "genome": genome,
                "src_token": "",
                "trigger_gate_binding_commitment": binding_commitment,
            },
        },
        {
            "ts": 7.0, "stage": "abort", "variant": variant,
            "env_tag": _T530_LAYER3_CONTRACT.env_tag,
            "payload": {
                "build_attempt_id": attempt_id,
                "genome": genome,
                "reason": "diff-quarantine",
            },
        },
    ])
    wal_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    provenance_path = (
        fixture["campaign"] / "reports/p3_s8a_trigger_loop_provenance.json"
    )
    provenance = json.loads(provenance_path.read_bytes())
    provenance["entries"]["2"] = {
        "proposal_path": str(proposal_two),
        "variant": variant,
        "build_attempt_id": attempt_id,
        "trigger_gate_binding_commitment": binding_commitment,
        "outcome": "rejected",
    }
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    fixture["report"]["cells"][0]["generations"].append({
        "generation": 2,
        "proposal": {
            "path": proposal_two.relative_to(fixture["run_root"]).as_posix(),
            "sha256": proposal_sha256,
            "digest": "b" * 64,
        },
        "harness": {
            "outcome": "rejected",
            "variant": variant,
            "records": {},
        },
        "bench_wall_seconds": 0.0,
    })
    _refresh_cross_binding_layer3(fixture)


def test_read_and_verify_bytes_rejects_changed_bytes(tmp_path: Path) -> None:
    root = tmp_path / "bytes"
    root.mkdir()
    path = root / "value.bin"
    path.write_bytes(b"original")
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    resolved, raw = C.read_and_verify_bytes(
        "value.bin", root=root, expected_sha256=expected,
        gate="cross-binding-bytes", label="fixture bytes",
    )
    assert resolved == path
    assert raw == b"original"
    path.write_bytes(b"mutated")
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[cross-binding-bytes\] fixture bytes bytes differ",
    ):
        C.read_and_verify_bytes(
            "value.bin", root=root, expected_sha256=expected,
            gate="cross-binding-bytes", label="fixture bytes",
        )


def test_verify_s8c_cross_binding_positive_binds_all_fields(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    wal_lines = [
        json.loads(line)
        for line in (fixture["campaign"] / "runs" / "wal.jsonl").read_text().splitlines()
    ]
    assert any(
        row["stage"] == TGB.WAL_RECORD_STAGE for row in wal_lines
    )
    receipt = C.verify_s8c_cross_binding(
        report=fixture["report"], events=fixture["events"],
        run_root=fixture["run_root"], output_root=fixture["output_root"],
    )
    assert receipt["mode"] == "build"
    assert set(receipt["bindings"]) == set(C.S8C_CROSS_BINDING_FIELDS)
    assert receipt["unbound_fields"] == []
    source_binding = receipt["bindings"]["proposal_build_source_bindings"][0]
    assert source_binding["predicate_rederivation_proof_kind"] == "consumer-rederived"
    assert source_binding["source_preimage_digest_proof_kind"] == "consumer-rederived"
    assert source_binding["predicate_source_association_proof_kind"] == (
        "consumer-rederived-textual-materialization"
    )
    assert source_binding["attempt_topology_proof_kind"] == "producer-self-consistency"
    assert source_binding["build_execution_proof_kind"] == "producer-execution-contract"
    assert source_binding["built_and_benched_count"] == 1
    assert source_binding["classified_source_preimage_artifact_count"] == 1
    assert source_binding["rows"][0]["predicate_assignment_count"] == 2
    assert source_binding["rows"][0]["build_execution_status"] == "built-and-benched"
    assert len(receipt["receipt_sha256"]) == 64


def test_t1749_m01_rejects_proposal_side_predicate_mutation(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    old_sha256, new_sha256 = _rewrite_cross_binding_proposal(
        fixture, lambda value: value["coder"].__setitem__("wire", "10000"),
    )
    old_artifact = fixture["campaign"] / (
        source_digest.source_preimage_artifact_relative_path(old_sha256)
    )
    new_artifact = fixture["campaign"] / (
        source_digest.source_preimage_artifact_relative_path(new_sha256)
    )
    assignment = reflux_ir.emit_predicate(reflux_ir.parse_wire("10000"))
    new_artifact.write_bytes(_cross_binding_source_preimage(assignment))
    old_artifact.unlink()
    _refresh_cross_binding_layer3(fixture)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-predicate\] trial='fixture-completeness' "
               r"value=.* path=proposals/proposal.json predicate digest differs$"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_m02_rejects_wal_side_predicate_mutation(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    wal_path = fixture["campaign"] / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_bytes().splitlines()]
    trigger = next(record for record in records if record["stage"] == TGB.WAL_RECORD_STAGE)
    source = trigger["payload"]["trigger_gate_binding"]["source"]
    changed = TGB.TriggerGateBinding(
        mask=1,
        predicate_sha256=TGB.expected_predicate_sha256(1),
        nonce=trigger["payload"]["trigger_gate_binding"]["nonce"],
        source=TGB.SourceBinding(
            src_token=source["src_token"],
            source_bytes_sha256=source["source_bytes_sha256"],
        ),
    )
    commitment = TGB.commitment(changed)
    trigger["payload"]["trigger_gate_binding"] = TGB.to_record(changed)
    next(record for record in records if record["stage"] == "build_start")[
        "payload"
    ]["trigger_gate_binding_commitment"] = commitment
    wal_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8",
    )
    provenance_path = (
        fixture["campaign"] / "reports/p3_s8a_trigger_loop_provenance.json"
    )
    provenance = json.loads(provenance_path.read_bytes())
    provenance["entries"]["fixture"][
        "trigger_gate_binding_commitment"
    ] = commitment
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    _refresh_cross_binding_layer3(fixture)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-predicate\] trial='fixture-completeness' "
               r"value=.* path=proposals/proposal.json predicate digest differs$"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_m03_rejects_source_preimage_digest_mutation(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    artifact = next((fixture["campaign"] / "source-bindings").glob("*.preimage"))
    artifact.write_bytes(artifact.read_bytes() + b"-digest-mutation")
    _refresh_cross_binding_layer3(fixture)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-source-digest\] trial='fixture-completeness' "
               r"value=.* path=.*\.preimage E2 digest equality differs$"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_e3_rejects_source_identity_only_mutation(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path, source_src_token="f" * 64)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-source-identity\] trial='fixture-completeness' "
               r"value=.* path=.*\.preimage E3 identity equality differs$"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_m04_rejects_exact_predicate_source_mismatch(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path, preimage_wire="10000")
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-source-association\] trial='fixture-completeness' "
               r"value=.* path=.*\.preimage gate-line multisets do not exactly "
               r"bind the proposal$"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_m04_rejects_duplicate_gate_line(tmp_path: Path) -> None:
    assignment = reflux_ir.emit_predicate(reflux_ir.parse_wire("00000"))
    fixture = _cross_binding_fixture(
        tmp_path, extra_gate_line=assignment,
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-source-association\].*"
               r"gate-line multisets do not exactly bind the proposal$"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_unmaterialized_skeleton_predicate_is_always_rejected(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(
        tmp_path, preimage_assignment="izanagi_gate_pass = true;",
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-source-association\].*"
               r"gate-line multisets do not exactly bind the proposal$"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


@pytest.mark.parametrize("owner", ("planner", "coder"))
def test_t1749_m05_rejects_non_trigger_axis_instead_of_skipping(
    tmp_path: Path, owner: str,
) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    _rewrite_cross_binding_proposal(
        fixture,
        lambda value: value[owner].__setitem__("axis", "silo-backoff-fixed"),
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-axis\] trial='fixture-completeness' "
               rf"value='silo-backoff-fixed' path=proposals/proposal.json\.{owner}\.axis"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_m06_rejects_caller_injected_driver(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    fixture["report"]["generation_driver"] = dict(C._INJECTED_GENERATION_DRIVER)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-driver\] trial='fixture-completeness' value=.* "
               r"path=report\.generation_driver materialized build cells require"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_m07_rejects_abort_only_materialized_cell(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path, include_bench_done=False)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(r"\[cross-binding-build-population\] trial='fixture-completeness' "
               r"value=0 path=report\.cells\[0\]\.generations materialized build cell"),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_t1749_m08_accepts_success_with_coexisting_abort_attempt(tmp_path: Path) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    _add_cross_binding_abort_attempt(fixture)
    receipt = C.verify_s8c_cross_binding(
        report=fixture["report"], events=fixture["events"],
        run_root=fixture["run_root"], output_root=fixture["output_root"],
    )
    source_binding = receipt["bindings"]["proposal_build_source_bindings"][0]
    assert source_binding["built_and_benched_count"] == 1
    assert source_binding["classified_source_preimage_artifact_count"] == 1
    assert [row["build_execution_status"] for row in source_binding["rows"]] == [
        "built-and-benched", "aborted",
    ]


def test_verify_s8c_cross_binding_projects_from_verified_wal_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _cross_binding_fixture(tmp_path)

    class Decision:
        def as_receipt(self):
            return copy.deepcopy(fixture["persisted"]["admission_decision"])

    class View:
        decision = Decision()

    def forbidden_reread(*_args, **_kwargs):
        raise AssertionError("C10 reread the WAL from disk")

    monkeypatch.setattr(C, "require_admitted_campaign", lambda *_args, **_kwargs: View())
    monkeypatch.setattr(C.wal, "read_records_checked", forbidden_reread)
    receipt = C.verify_s8c_cross_binding(
        report=fixture["report"], events=fixture["events"],
        run_root=fixture["run_root"], output_root=fixture["output_root"],
    )
    assert receipt["mode"] == "build"
    assert receipt["bindings"]["build_records"]


def test_verify_s8c_cross_binding_rejects_missing_bench_wall_s(
    tmp_path: Path,
) -> None:
    fixture = _cross_binding_fixture(tmp_path, include_bench_wall_s=False)
    report = fixture["report"]
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"\[cross-binding-bench\] WAL bench_done\.payload is missing bench_wall_s$",
    ):
        C.verify_s8c_cross_binding(
            report=report, events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_verify_s8c_cross_binding_no_build_is_explicitly_unbound(
    tmp_path: Path,
) -> None:
    report = {"trial_id": "fixture-no-build", "do_build": False, "cells": []}
    receipt = C.verify_s8c_cross_binding(
        report=report, events=[], run_root=tmp_path,
    )
    assert receipt["mode"] == "no-build"
    assert receipt["bindings"] == {}
    assert receipt["unbound_fields"] == list(C.S8C_CROSS_BINDING_FIELDS)


@pytest.mark.parametrize("mutation", C.S8C_CROSS_BINDING_FIELDS)
def test_verify_s8c_cross_binding_rejects_each_reference_mutation(
    tmp_path: Path, mutation: str,
) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    report = fixture["report"]
    events = fixture["events"]
    persisted = fixture["persisted"]
    expected_error = None
    if mutation == "input_payload_sha256":
        events[0]["input_payload_sha256"] = "c" * 64
    elif mutation == "raw_response_path":
        events[0]["raw_response_path"] = "raw/missing.txt"
    elif mutation == "raw_response_sha256":
        events[0]["raw_response_sha256"] = "c" * 64
    elif mutation == "provider_payload_sha256":
        events[0]["provider_payload_sha256"] = "c" * 64
    elif mutation == "provider_envelope_sha256":
        events[0]["provider_envelope_sha256"] = "c" * 64
    elif mutation == "proposal_path":
        report["cells"][0]["generations"][0]["proposal"]["path"] = (
            "proposals/missing.json"
        )
    elif mutation == "proposal_sha256":
        report["cells"][0]["generations"][0]["proposal"]["sha256"] = "c" * 64
    elif mutation == "build_records":
        persisted["variants"][0]["events"][0]["payload"]["genome"] = "mutated"
        _write_cross_binding_layer3(fixture["persisted_path"], persisted)
    elif mutation == "bench_records":
        persisted["runs"][0]["median_tps"] = 999.0
        _write_cross_binding_layer3(fixture["persisted_path"], persisted)
    elif mutation == "artifact_refs":
        persisted["artifact_refs"].sort(
            key=lambda ref: ref["path"] != "loop_state.json"
        )
        target_ref = next(
            ref for ref in persisted["artifact_refs"]
            if ref["path"].endswith("p3_s8a_trigger_loop_provenance.json")
        )
        assert persisted["artifact_refs"][0]["path"] == "loop_state.json"
        assert target_ref["path"] != persisted["artifact_refs"][0]["path"]
        target = fixture["campaign"] / target_ref["path"]
        target.write_bytes(target.read_bytes() + b"mutation")
    elif mutation == "source_refs":
        persisted["source_refs"].pop()
        _write_cross_binding_layer3(fixture["persisted_path"], persisted)
    elif mutation == "admission_decision":
        report["cells"][0]["admission_decision"]["classification"] = "mutated"
    elif mutation == "proposal_build_source_bindings":
        target_ref = next(
            ref for ref in persisted["artifact_refs"]
            if ref["path"].startswith("source-bindings/")
        )
        target = fixture["campaign"] / target_ref["path"]
        target.write_bytes(target.read_bytes() + b"mutation")
        _refresh_cross_binding_layer3(fixture)
        expected_error = r"\[cross-binding-source-digest\]"
    else:
        raise AssertionError(mutation)
    with pytest.raises(
        C.AutonomousTrialCompletenessError, match=expected_error,
    ):
        C.verify_s8c_cross_binding(
            report=report, events=events,
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def test_verify_s8c_cross_binding_rejects_an_unclassified_wal_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _cross_binding_fixture(tmp_path)
    persisted = copy.deepcopy(fixture["persisted"])
    extra = C.wal.WalRecord(
        variant="fixture-variant",
        stage="unclassified",
        env_tag=_T530_LAYER3_CONTRACT.env_tag,
        ts=5.0,
        payload={"fixture": "unclassified"},
    )
    original_parser = C._cross_binding_verified_wal_records

    def with_extra(raw: bytes):
        records, truncated = original_parser(raw)
        return [*records, extra], truncated

    monkeypatch.setattr(C, "_cross_binding_verified_wal_records", with_extra)
    extra_dict = C._cross_binding_wal_dict(extra)
    persisted["variants"][0]["events"].append(extra_dict)
    persisted["source_refs"].append(_test_wal_ref(extra_dict))
    _write_cross_binding_layer3(fixture["persisted_path"], persisted)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[cross-binding-wal\] build/bench WAL projection does not cover "
            r"all layer3 records$"
        ),
    ):
        C.verify_s8c_cross_binding(
            report=fixture["report"], events=fixture["events"],
            run_root=fixture["run_root"], output_root=fixture["output_root"],
        )


def _campaign_report(cell: dict, *, trial_id: str = "fixture-completeness") -> dict:
    return {
        "trial_id": trial_id,
        "generation_budget_per_workload": 1,
        "status": "partial",
        "launch_admission": {"certifying": False},
        "cells": [copy.deepcopy(cell)],
    }


def _rewrite_cell_campaign_identity(
    campaign: Path, cell: dict, mutate_identity,
) -> None:
    decoded = C._campaign_lock_identity(campaign, gate="fixture")
    identity = json.loads(decoded.identity_preimage)
    mutate_identity(identity)
    identity_preimage = C.campaign_lock.canonical_json(identity)
    (campaign / "campaign.lock").write_text(
        build_v2_lock(identity_preimage), encoding="utf-8",
    )
    workload = identity["search_config"]["workload"]
    cell["campaign_id"] = (
        f"p3-t178-{workload}-workload-conditioned-autonomous-"
        f"{hashlib.sha256(identity_preimage.encode('utf-8')).hexdigest()[:8]}"
    )


def test_t1333_campaign_chain_reprojects_descriptor_scale_from_entry(
    tmp_path,
) -> None:
    _output_root, campaign, _path, _persisted, cell = _layer3_campaign(tmp_path)
    entry = A.WORKLOADS["ycsb-a"]
    C._check_cell_campaign_identity(
        cell=cell,
        cell_index=0,
        workload="ycsb-a",
        entry=entry,
        trial_id="fixture-completeness",
        budget=1,
        campaign_root=campaign,
        arm_binding_digest=None,
    )
    mutated_records = entry["records"] + 1
    cell["descriptor"]["scale"]["records"] = mutated_records
    cell["perf_config_scale"]["records"] = mutated_records
    descriptor_sha256 = hashlib.sha256(
        C._canonical_bytes(cell["descriptor"])
    ).hexdigest()
    projected_input_sha256 = hashlib.sha256(C._canonical_bytes({
        "records": mutated_records,
        "threads": entry["threads"],
        "ycsb": dict(entry["ycsb"]),
    })).hexdigest()
    cell["descriptor_binding"]["input_sha256"] = projected_input_sha256
    cell["descriptor_binding"]["output_sha256"] = descriptor_sha256

    def mutate_identity(identity):
        identity["search_config"]["records"] = mutated_records
        identity["search_config"]["descriptor_sha256"] = descriptor_sha256

    _rewrite_cell_campaign_identity(campaign, cell, mutate_identity)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"^\[campaign-chain\] cells\[0\] workload scale "
            r"differs from producer$"
        ),
    ):
        C._check_cell_campaign_identity(
            cell=cell,
            cell_index=0,
            workload="ycsb-a",
            entry=entry,
            trial_id="fixture-completeness",
            budget=1,
            campaign_root=campaign,
            arm_binding_digest=None,
        )


def test_m5_exploratory_workload_flags_are_the_only_mismatch(tmp_path) -> None:
    output_root, _campaign, _path, _persisted, cell = _layer3_campaign(tmp_path)
    key = A.s8b_holdout_freeze.SKEW_KEY
    cell["workload_flags"][key] += "0"
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"cells\[0\]\.workload_flags differs from producer$",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


def test_perf_config_scale_is_independently_bound_to_the_entry(tmp_path) -> None:
    _output_root, campaign, _path, _persisted, cell = _layer3_campaign(tmp_path)
    entry = A.WORKLOADS["ycsb-a"]
    cell["perf_config_scale"]["threads"] = entry["threads"] + 1
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"cells\[0\] workload scale differs from producer$",
    ):
        C._check_cell_campaign_identity(
            cell=cell,
            cell_index=0,
            workload="ycsb-a",
            entry=entry,
            trial_id="fixture-completeness",
            budget=1,
            campaign_root=campaign,
            arm_binding_digest=None,
        )


def test_m6_formal_campaign_scale_is_the_only_mismatch(tmp_path) -> None:
    _run, _events, report, arm_execution = _registered_digest_chain_trial(tmp_path)
    cell = report["cells"][0]
    workload = cell["workload"]
    entry = A.FORMAL_WORKLOADS[workload]
    campaign = Path(cell["campaign_root"])
    mutated_records = entry["records"] + 1

    def mutate_identity(identity):
        identity["search_config"]["records"] = mutated_records

    _rewrite_cell_campaign_identity(campaign, cell, mutate_identity)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"cells\[0\] workload scale differs from producer$",
    ):
        C._check_cell_campaign_identity(
            cell=cell,
            cell_index=0,
            workload=workload,
            entry=entry,
            trial_id="fixture-completeness",
            budget=1,
            campaign_root=campaign,
            arm_binding_digest=arm_execution["arm_binding_digest_sha256"],
        )


def test_t1310_consumer_independently_reloads_legacy_source_and_four_keys(
    monkeypatch,
) -> None:
    source_record = A._formal_profile_source_record(repository_root=A.ROOT)
    original_loader = C.s8b_ratified_freeze.load_legacy_freeze
    calls = []

    def recording_loader(root):
        calls.append(Path(root))
        return original_loader(root)

    monkeypatch.setattr(
        C.s8b_ratified_freeze, "load_legacy_freeze", recording_loader,
    )
    C.assert_legacy_workload_profile_source(
        source_record=source_record,
        producer_entries=A.FORMAL_WORKLOADS,
        repository_root=A.ROOT,
    )
    assert calls == [A.ROOT]

    tampered_source = {**source_record, "sha256": "0" * 64}
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"source record differs from fresh legacy load$",
    ):
        C.assert_legacy_workload_profile_source(
            source_record=tampered_source,
            producer_entries=A.FORMAL_WORKLOADS,
            repository_root=A.ROOT,
        )

    tampered_entries = copy.deepcopy(A.FORMAL_WORKLOADS)
    formal_name = next(iter(A.s8b_holdout_freeze.HOLDOUTS))
    tampered_entries[formal_name] = {
        **A.FORMAL_WORKLOADS[formal_name],
        "records": A.FORMAL_WORKLOADS[formal_name]["records"] + 1,
    }
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"four-key authority bytes differ$",
    ):
        C.assert_legacy_workload_profile_source(
            source_record=source_record,
            producer_entries=tampered_entries,
            repository_root=A.ROOT,
        )


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


def test_campaign_identity_is_pinned_without_producer_helper_oracle(
    tmp_path, monkeypatch,
) -> None:
    output_root, _campaign, _persisted_path, _persisted, cell = _layer3_campaign(
        tmp_path
    )
    # T-671 で契約 H が identity から外れた current golden を独立に pin する。
    assert cell["campaign_id"] == (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-4b75e24e"
    )
    assert _PRE_T343_NO_BUILD_CAMPAIGN_IDS[(
        "fixture-completeness", "ycsb-a",
    )] == "p3-t178-ycsb-a-workload-conditioned-autonomous-948f4c43"
    report = _campaign_report(cell)
    monkeypatch.setattr(
        A.env_contract, "lookup",
        lambda _env_tag: pytest.fail("offline completeness used current lookup"),
    )
    C.assert_campaign_layer3_chain(report=report, output_root=output_root)


def test_campaign_chain_declares_certified_acceptance_purpose(
    tmp_path, monkeypatch,
) -> None:
    output_root, _campaign, _persisted_path, _persisted, cell = _layer3_campaign(
        tmp_path
    )
    original = C.require_admitted_campaign
    observed = []

    def observe(campaign, *, purpose):
        observed.append(purpose)
        return original(campaign, purpose=purpose)

    monkeypatch.setattr(C, "require_admitted_campaign", observe)
    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )
    assert observed == [C.CampaignReadPurpose.CERTIFIED_ACCEPTANCE]


def test_campaign_chain_reads_legacy_layer3_without_epoch(tmp_path) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    assert persisted.pop("campaign_verifier_epoch")["state"] == "E1"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )


def test_campaign_chain_reads_legacy_historical_epoch_without_marker(
    tmp_path: Path,
) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    assert persisted["certifying_input"] is False
    assert persisted["campaign_verifier_epoch"].pop(
        "verifier_assessment_basis"
    ) == "recorded-at-original-verifier-epoch"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )


def test_campaign_chain_reads_legacy_layer3_without_current_verifier_conformance(
    tmp_path: Path,
) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    assert persisted.pop("current_verifier_conformance") == "unknown"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )


def test_campaign_chain_reads_legacy_layer3_without_knowledge_provenance(
    tmp_path: Path,
) -> None:
    """M6: fails only when legacy comparison does not normalize the missing field."""
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    assert persisted.pop("knowledge_provenance") is None
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )


def test_campaign_chain_rejects_persisted_current_verifier_conformance_mutation(
    tmp_path: Path,
) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    assert persisted["current_verifier_conformance"] == "unknown"
    persisted["current_verifier_conformance"] = "changed"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[campaign-chain\] persisted layer3 report differs "
            r"from fresh rebuild$"
        ),
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


def test_campaign_chain_accepts_historical_epoch_with_exact_marker(
    tmp_path: Path,
) -> None:
    output_root, _campaign, _persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    assert persisted["certifying_input"] is False
    assert persisted["campaign_verifier_epoch"][
        "verifier_assessment_basis"
    ] == "recorded-at-original-verifier-epoch"

    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )


def test_campaign_chain_accepts_verified_post_admission_schema(
    tmp_path, monkeypatch,
) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    decision = copy.deepcopy(persisted["admission_decision"])
    decision["classification"] = "verified-post-admission-schema"
    assert decision["admission_status"] == "admitted"
    persisted["admission_decision"] = copy.deepcopy(decision)
    persisted["certifying_input"] = True
    assert persisted["campaign_verifier_epoch"].pop(
        "verifier_assessment_basis"
    ) == "recorded-at-original-verifier-epoch"
    cell["admission_decision"] = copy.deepcopy(decision)
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    admitted = SimpleNamespace(
        decision=SimpleNamespace(as_receipt=lambda: copy.deepcopy(decision)),
        campaign_verifier_epoch=SimpleNamespace(
            **persisted["campaign_verifier_epoch"]
        ),
    )
    monkeypatch.setattr(
        C, "require_admitted_campaign", lambda *_args, **_kwargs: admitted,
    )
    monkeypatch.setattr(
        C,
        "_fresh_layer3_for_comparison",
        lambda **kwargs: kwargs["persisted"],
    )
    report = _campaign_report(cell)
    report["launch_admission"]["certifying"] = True

    C.assert_campaign_layer3_chain(report=report, output_root=output_root)


def test_campaign_chain_rejects_persisted_epoch_mutation(tmp_path) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    persisted["campaign_verifier_epoch"]["campaign_verifier_epoch"] = (
        "E1:" + "0" * 64
    )
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match="campaign verifier epoch differs from validator",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


def test_campaign_chain_rejects_persisted_epoch_marker_mutation(
    tmp_path: Path,
) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    persisted["campaign_verifier_epoch"][
        "verifier_assessment_basis"
    ] = "recorded-at-current-verifier-epoch"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match="campaign verifier epoch differs from validator",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


def test_campaign_chain_rejects_marker_on_certifying_input(
    tmp_path: Path,
) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    persisted["certifying_input"] = True
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = _campaign_report(cell)
    report["launch_admission"]["certifying"] = True

    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match="campaign verifier epoch exact keys differ",
    ):
        C.assert_campaign_layer3_chain(report=report, output_root=output_root)


def test_campaign_chain_rejects_persisted_epoch_extra_key(tmp_path) -> None:
    output_root, _campaign, persisted_path, persisted, cell = _layer3_campaign(
        tmp_path
    )
    persisted["campaign_verifier_epoch"]["unexpected"] = "value"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match="campaign verifier epoch exact keys differ",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


@pytest.mark.parametrize(
    "workload,old_campaign_id,new_campaign_id",
    _CURRENT_WORKLOAD_CAMPAIGN_EPOCHS,
)
def test_t428_workload_campaign_epoch_and_old_root_nonwrite(
    tmp_path, workload, old_campaign_id, new_campaign_id,
) -> None:
    assert _T428_POLICY_BOUND_CAMPAIGN_IDS[
        ("fixture-completeness", workload)
    ] == old_campaign_id
    assert _CURRENT_POLICY_BOUND_CAMPAIGN_IDS[
        ("fixture-completeness", workload)
    ] == new_campaign_id
    assert _t428_descriptor_campaign_id(
        "fixture-completeness", workload,
    ) == new_campaign_id
    assert old_campaign_id != new_campaign_id

    output_root, campaign, _persisted_path, _persisted, cell = _layer3_campaign(
        tmp_path, workload=workload,
    )
    old_root = output_root / "campaigns" / old_campaign_id
    current_campaign_id = _CURRENT_POLICY_BOUND_CAMPAIGN_IDS[
        ("fixture-completeness", workload)
    ]
    assert campaign == output_root / "campaigns" / current_campaign_id
    assert not old_root.exists()
    assert campaign == output_root / "campaigns" / new_campaign_id
    t530_root = output_root / "campaigns" / _T530_CONTRACT_BOUND_CAMPAIGN_IDS[
        ("fixture-completeness", workload)
    ]
    assert not t530_root.exists()

    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=output_root,
    )
    assert not old_root.exists()
    assert not t530_root.exists()


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


def test_campaign_chain_rejects_failure_decision_for_admitted_campaign(
    tmp_path,
) -> None:
    output_root, _campaign, _path, _persisted, cell = _layer3_campaign(tmp_path)
    cell["admission_decision"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "forged admission failure",
        },
    }
    cell["pending_critic_disposition"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-pending-critic-disposition/v1"
        ),
        "action": "discarded",
        "reason": "cell-admission-failure",
        "count": 0,
    }
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"failure campaign has a persisted layer3 report$",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


def test_campaign_chain_rejects_failure_when_independent_admission_passes(
    tmp_path,
) -> None:
    output_root, _campaign, persisted_path, _persisted, cell = (
        _layer3_campaign(tmp_path)
    )
    persisted_path.unlink()
    cell["admission_decision"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "forged admission failure",
        },
    }
    cell["pending_critic_disposition"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-pending-critic-disposition/v1"
        ),
        "action": "discarded",
        "reason": "cell-admission-failure",
        "count": 0,
    }
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"failure campaign remains independently admitted$",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


def _campaignless_failure_cell() -> dict:
    return {
        "workload": "ycsb-a",
        "generations": [],
        "stop_reason": "supervisor-error",
        "error": {
            "type": "RuntimeError",
            "message": "fixture supervisor failure",
        },
        "admission_decision": {
            "schema_version": (
                "p3-autonomous-workload-trial-cell-admission-failure/v1"
            ),
            "admission_status": "failed",
            "error": {
                "type": "AutonomousTrialError",
                "message": "build cell has no campaign_root for admission validation",
            },
        },
        "pending_critic_disposition": {
            "schema_version": (
                "p3-autonomous-workload-trial-pending-critic-disposition/v1"
            ),
            "action": "discarded",
            "reason": "cell-admission-failure",
            "count": 0,
        },
    }


def test_campaign_chain_accepts_failure_without_any_campaign_identity(
    tmp_path,
) -> None:
    cell = _campaignless_failure_cell()
    C.assert_campaign_layer3_chain(
        report=_campaign_report(cell), output_root=tmp_path / "output",
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        pytest.param("campaign_id", None, id="explicit-null-campaign-id"),
        pytest.param("campaign_root", None, id="explicit-null-campaign-root"),
        pytest.param("descriptor", {"extra": True}, id="extra-descriptor"),
        pytest.param(
            "pending_critic_disposition",
            {
                "schema_version": (
                    "p3-autonomous-workload-trial-"
                    "pending-critic-disposition/v1"
                ),
                "action": "discarded",
                "reason": "cell-admission-failure",
                "count": 1,
            },
            id="discarded-critic-without-generation",
        ),
    ],
)
def test_campaign_chain_rejects_nonexact_campaignless_failure_fallback(
    tmp_path, key, value,
) -> None:
    cell = _campaignless_failure_cell()
    cell[key] = value
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"campaignless failure is not the exact producer fallback$",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=tmp_path / "output",
        )


def test_campaign_chain_rejects_admitted_cell_with_identity_removed(
    tmp_path,
) -> None:
    output_root, _campaign, _path, _persisted, cell = _layer3_campaign(
        tmp_path,
    )
    cell.pop("campaign_id")
    cell.pop("campaign_root")
    cell["admission_decision"] = _campaignless_failure_cell()[
        "admission_decision"
    ]
    cell["pending_critic_disposition"] = _campaignless_failure_cell()[
        "pending_critic_disposition"
    ]
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"campaignless failure is not the exact producer fallback$",
    ):
        C.assert_campaign_layer3_chain(
            report=_campaign_report(cell), output_root=output_root,
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda decision: decision.update({"extra": True}),
        lambda decision: decision.update({"admission_status": "admitted"}),
        lambda decision: decision.update({"schema_version": "wrong/v1"}),
        lambda decision: decision["error"].update({"type": "KeyError"}),
        lambda decision: decision["error"].update({"message": ""}),
        lambda decision: decision["error"].update({"extra": True}),
    ],
)
def test_cell_admission_failure_decision_shape_is_closed(mutate) -> None:
    decision = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    mutate(decision)
    assert C.is_exact_cell_admission_failure_decision(decision) is False


@pytest.mark.parametrize(
    "diagnosis",
    [
        pytest.param("not-a-mapping", id="non-mapping"),
        pytest.param(
            {
                "schema_version": (
                    "p3-autonomous-workload-trial-"
                    "layer3-admission-diagnosis/v1"
                ),
                "status": "degraded",
                "validator": None,
                "validator_value": None,
                "absolute_instance_path": [],
                "absolute_schema_path": [],
                "offending_property": None,
                "degradation_reason": "validation-error-cause-not-found",
                "extra": True,
            },
            id="mapping-with-extra-key",
        ),
    ],
)
def test_completeness_rejects_present_invalid_layer3_diagnosis(
    tmp_path, diagnosis,
) -> None:
    run, events, report = _complete_trial(tmp_path)
    report["cells"][0]["layer3_admission_diagnosis"] = diagnosis
    _persist(run, events, report)

    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[artifact-admission\] cells\[0\] Layer-3 admission "
            r"diagnosis is not exact$"
        ),
    ):
        _verify(run, report)


def test_workload_suffix_rejects_failure_cell_that_is_not_final(tmp_path) -> None:
    run, events, report = _complete_trial(
        tmp_path, workloads=("ycsb-a", "ycsb-b"),
    )
    requested = ["ycsb-a", "ycsb-b", "ycsb-c"]
    report["status"] = "partial"
    report["do_build"] = True
    report["workloads_requested"] = requested
    report["launch_admission"]["workloads"] = requested
    events[0]["do_build"] = True
    events[0]["workloads"] = requested
    events[0]["launch_admission"]["workloads"] = requested
    events[-1]["status"] = "partial"
    failure = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    report["cells"][0]["admission_decision"] = failure
    report["cells"][0]["pending_critic_disposition"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-pending-critic-disposition/v1"
        ),
        "action": "discarded",
        "reason": "cell-admission-failure",
        "count": 0,
    }
    report["cells"][1]["admission_decision"] = {
        "schema_version": "campaign-artifact-admission-decision/v1",
        "admission_status": "admitted",
        "classification": "admitted-new-schema",
    }
    events[-1]["cell_admission_failures"] = [{
        "cell_index": 0,
        "workload": "ycsb-a",
        "admission_decision": failure,
    }]
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"requested workload suffix is unexplained$",
    ):
        _verify(run, report)


def test_completeness_rejects_nonfinal_failure_with_full_workload_coverage(
    tmp_path,
) -> None:
    run, events, report = _complete_trial(
        tmp_path, workloads=("ycsb-a", "ycsb-b"),
    )
    report["status"] = "partial"
    report["do_build"] = True
    events[0]["do_build"] = True
    events[-1]["status"] = "partial"
    failure = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    report["cells"][0]["admission_decision"] = failure
    report["cells"][0]["pending_critic_disposition"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-pending-critic-disposition/v1"
        ),
        "action": "discarded",
        "reason": "cell-admission-failure",
        "count": 0,
    }
    report["cells"][1]["admission_decision"] = {
        "schema_version": "campaign-artifact-admission-decision/v1",
        "admission_status": "admitted",
        "classification": "admitted-new-schema",
    }
    events[-1]["cell_admission_failures"] = [{
        "cell_index": 0,
        "workload": "ycsb-a",
        "admission_decision": failure,
    }]
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=(
            r"\[artifact-admission\] cell admission failure must be the "
            r"final cell$"
        ),
    ):
        _verify(run, report)


def test_completeness_rejects_multiple_cell_admission_failures(tmp_path) -> None:
    run, events, report = _complete_trial(
        tmp_path, workloads=("ycsb-a", "ycsb-b"),
    )
    report["status"] = "partial"
    report["do_build"] = True
    events[0]["do_build"] = True
    events[-1]["status"] = "partial"
    projections = []
    for index, cell in enumerate(report["cells"]):
        decision = {
            "schema_version": (
                "p3-autonomous-workload-trial-cell-admission-failure/v1"
            ),
            "admission_status": "failed",
            "error": {
                "type": "AutonomousTrialError",
                "message": f"fixture admission failure {index}",
            },
        }
        cell["admission_decision"] = decision
        cell["pending_critic_disposition"] = {
            "schema_version": (
                "p3-autonomous-workload-trial-pending-critic-disposition/v1"
            ),
            "action": "discarded",
            "reason": "cell-admission-failure",
            "count": 0,
        }
        projections.append({
            "cell_index": index,
            "workload": cell["workload"],
            "admission_decision": decision,
        })
    events[-1]["cell_admission_failures"] = projections
    _persist(run, events, report)
    with pytest.raises(
        C.AutonomousTrialCompletenessError,
        match=r"multiple cell admission failures are forbidden$",
    ):
        _verify(run, report)


def test_campaign_chain_failed_peer_does_not_exempt_missing_admitted_report(
    tmp_path,
) -> None:
    output_root, _campaign, admitted_path, _persisted, admitted_cell = (
        _layer3_campaign(tmp_path, workload="ycsb-a")
    )
    (
        _same_root,
        failed_campaign,
        failed_path,
        _failed_persisted,
        failed_cell,
    ) = _layer3_campaign(
        tmp_path, workload="ycsb-b", output_root=output_root,
    )
    admitted_path.unlink()
    failed_path.unlink()
    (failed_campaign / "campaign.lock").unlink()
    failed_cell["admission_decision"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "fixture admission failure",
        },
    }
    failed_cell["pending_critic_disposition"] = {
        "schema_version": (
            "p3-autonomous-workload-trial-pending-critic-disposition/v1"
        ),
        "action": "discarded",
        "reason": "cell-admission-failure",
        "count": 0,
    }
    report = _campaign_report(admitted_cell)
    report["cells"] = [admitted_cell, failed_cell]
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
                "critic_digest_generated": False,
                "trigger_gate_binding_commitment": "b" * 64,
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
        env={
            "PATH": str(Path(sys.executable).parent),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
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


def _failure_only_producer(tmp_path, monkeypatch, *, mode="partial"):
    """Inject producer faults, leaving finalization and all verifiers real."""
    authority = p3_test._coder_authority()
    factory = A.exploration_campaign_layout
    monkeypatch.setattr(A, "exploration_campaign_layout",
                        lambda cid: factory(cid, str(tmp_path / "output")))
    monkeypatch.setattr(A.trigger, "_current_site", lambda: A.trigger.site_policy.OTHER)
    metric_payloads = A._role_metric_payloads

    def fail_before_roles(*args, **kwargs):
        raise RuntimeError("injected before first role")

    def expire_inside_cell(*args, **kwargs):
        result = metric_payloads(*args, **kwargs)
        real_time = A.time
        monkeypatch.setattr(A, "time", SimpleNamespace(
            monotonic=lambda: real_time.monotonic() + 10000,
            monotonic_ns=real_time.monotonic_ns, time_ns=real_time.time_ns,
        ))
        return result

    def broken_preview(*args, **kwargs):
        raise RuntimeError("injected after valid role raw writes")

    if mode == "partial":
        monkeypatch.setattr(A, "_role_metric_payloads", fail_before_roles)
    elif mode == "normal":
        monkeypatch.setattr(A, "_role_metric_payloads", expire_inside_cell)
    providers = None
    if mode in {"invalid-pre-raw", "invalid-post-raw"}:
        class FaultyPlanner:
            def invoke(self, **kwargs):
                if mode == "invalid-pre-raw":
                    raise RuntimeError("injected provider failure before response")
                return A.ProviderResponse(raw_response="{}", provenance={"child_id": "fault-injection"})
        providers = {role: A.FixtureRoleProvider(role) for role in _ROLES}
        providers["planner"] = FaultyPlanner()
    run = tmp_path / "run"
    report = A.run_trial(
        trial_id="rootless-failure", workloads=["ycsb-a", "ycsb-b"], generations=1,
        provider_kind="fixture", run_root=run, sub="/unused", do_build=True,
        preview=broken_preview, coder_authority=authority, providers=providers,
        allow_unregistered_exploratory=True,
    )
    events = [json.loads(line) for line in (run / "attempts.jsonl").read_text().splitlines()]
    assert report["cells"][0]["admission_decision"]["admission_status"] == "failed"
    assert json.loads((run / "report.json").read_bytes()) == report
    return run, events, report


def _diagnostic_verify(run, **kwargs):
    return C.verify_autonomous_trial_files(
        run / "attempts.jsonl", run / "report.json",
        failure_only_diagnostic=True, **kwargs,
    )


def test_failure_only_diagnostic_accepts_producer_partial_cell(tmp_path, monkeypatch):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch)
    assert report["cells"][0]["stop_reason"] == "supervisor-error"
    assert not [e for e in events if e["event"] == "role-attempt"]
    assert report["honest_accounting"]["role_query_count"] == 0
    assert _diagnostic_verify(run)["certifying"] is False


def test_failure_only_diagnostic_accepts_producer_normal_return_failure(tmp_path, monkeypatch):
    run, _, report = _failure_only_producer(tmp_path, monkeypatch, mode="normal")
    assert report["cells"][0]["stop_reason"] == "supervisor-wall-budget"
    assert "error" not in report["cells"][0]
    assert _diagnostic_verify(run)["s8c_cross_binding"] == "not-established"


def test_failure_only_diagnostic_accepts_producer_valid_roles(tmp_path, monkeypatch):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch, mode="roles")
    roles = [e for e in events if e["event"] == "role-attempt"]
    assert len(roles) == report["honest_accounting"]["role_query_count"] == 2
    assert all(e["status"] == "valid" for e in roles)
    assert _diagnostic_verify(run)["certifying"] is False


def test_failure_only_diagnostic_rejects_declared_proposal(tmp_path, monkeypatch):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch, mode="roles")
    assert _diagnostic_verify(run)["certifying"] is False
    proposal_bytes = json.dumps({
        "planner": {"axis": "silo-backoff-trigger-gating"},
        "coder": {
            "axis": "silo-backoff-trigger-gating", "wire": "00000",
            "justification": "unrelated proposal", "confidence": 0.5,
        },
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")
    proposal_path = run / "proposals" / "injected.json"
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_bytes(proposal_bytes)
    report["cells"][0]["generations"][0]["proposal"] = {
        "path": str(proposal_path),
        "sha256": hashlib.sha256(proposal_bytes).hexdigest(),
    }
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[failure-only-proposal\] exploratory generation declares proposal$"):
        _diagnostic_verify(run)


def test_failure_only_diagnostic_requires_explicit_opt_in(tmp_path, monkeypatch):
    run, _, _ = _failure_only_producer(tmp_path, monkeypatch)
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[campaign-chain\] build trial verification requires campaign_output_root$"):
        C.verify_autonomous_trial_files(run / "attempts.jsonl", run / "report.json")


@pytest.mark.parametrize("kind", ["file", "dangling-symlink"])
def test_failure_only_diagnostic_rejects_persisted_layer3(tmp_path, monkeypatch, kind):
    run, _, report = _failure_only_producer(tmp_path, monkeypatch)
    path = Path(report["cells"][0]["campaign_root"]) / "reports" / "layer3_report.json"
    path.parent.mkdir(parents=True)
    if kind == "file":
        path.write_text("{}")
    else:
        path.symlink_to("absent.json")
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[campaign-chain\] cells\[0\] failure campaign has a persisted layer3 report$"):
        _diagnostic_verify(run)


def test_failure_only_diagnostic_preserves_supplied_root_checks(tmp_path, monkeypatch):
    run, _, _ = _failure_only_producer(tmp_path, monkeypatch)
    with pytest.raises(C.AutonomousTrialCompletenessError, match=r"\[cross-binding") as before:
        C.verify_autonomous_trial_files(run / "attempts.jsonl", run / "report.json",
                                       campaign_output_root=tmp_path / "wrong")
    with pytest.raises(C.AutonomousTrialCompletenessError) as after:
        _diagnostic_verify(run, campaign_output_root=tmp_path / "wrong")
    assert str(before.value) == str(after.value)


def test_failure_only_diagnostic_cli_emits_noncertifying_receipt(tmp_path, monkeypatch):
    run, _, _ = _failure_only_producer(tmp_path, monkeypatch)
    result = subprocess.run([
        sys.executable, "-m", "orchestrator.campaign.autonomous_trial_completeness",
        str(run / "attempts.jsonl"), str(run / "report.json"), "--failure-only-diagnostic",
    ], cwd=_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt == _diagnostic_verify(run)
    assert receipt["schema_version"] == "autonomous-trial-failure-only-diagnostic/v1"
    assert receipt["certifying"] is False
    assert receipt["campaign_output_root_binding"] == "not-verified"
    assert receipt["s8c_cross_binding"] == "not-established"
    assert receipt["attempt_journal_sha256"] == hashlib.sha256((run / "attempts.jsonl").read_bytes()).hexdigest()
    assert receipt["report_json_sha256"] == hashlib.sha256((run / "report.json").read_bytes()).hexdigest()


@pytest.mark.parametrize("kind", ["cell-extra", "error-extra", "decision-extra", "disposition-extra", "diagnosis"])
def test_failure_only_diagnostic_rejects_nonexact_shape(tmp_path, monkeypatch, kind):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch)
    cell = report["cells"][0]
    expected = r"\[failure-only-diagnostic\] report is not an exact supported failure-only shape$"
    if kind == "cell-extra":
        cell["extra"] = True
    elif kind == "error-extra":
        cell["error"]["extra"] = True
        expected = r"\[terminal-projection\] supervisor-error cell projection is inconsistent$"
    elif kind == "decision-extra":
        cell["admission_decision"]["extra"] = True
        expected = r"\[run-envelope\] run-finish has a cell admission failure absent from report$"
    elif kind == "disposition-extra":
        cell["pending_critic_disposition"]["extra"] = True
        expected = r"\[artifact-admission\] cells\[0\] failure disposition is not exact$"
    else:
        cell["layer3_admission_diagnosis"] = {
            "schema_version": "p3-autonomous-workload-trial-layer3-admission-diagnosis/v1",
            "status": "degraded", "validator": None, "validator_value": None,
            "absolute_instance_path": [], "absolute_schema_path": [],
            "offending_property": None, "degradation_reason": "validation-error-cause-not-found",
        }
        events[-1]["cell_admission_failures"][0]["layer3_admission_diagnosis"] = cell["layer3_admission_diagnosis"]
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError, match=expected):
        _diagnostic_verify(run)


def test_failure_only_diagnostic_rejects_role_count_drift(tmp_path, monkeypatch):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch)
    report["honest_accounting"]["role_query_count"] = 1
    events[-1]["honest_accounting"]["role_query_count"] = 1
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[generation-accounting\] report role query total differs$"):
        _diagnostic_verify(run)


def test_failure_only_diagnostic_preserves_raw_binding(tmp_path, monkeypatch):
    run, events, _ = _failure_only_producer(tmp_path, monkeypatch, mode="roles")
    role = next(e for e in events if e["event"] == "role-attempt")
    Path(role["raw_response_path"]).write_text("tampered")
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[failure-only-raw\].*sha256"):
        _diagnostic_verify(run)


@pytest.mark.parametrize("mixed", [False, True], ids=["admitted", "mixed"])
def test_failure_only_diagnostic_rejects_admitted_or_mixed_cells(tmp_path, mixed):
    workloads = ("ycsb-a", "ycsb-b") if mixed else ("ycsb-a",)
    run, events, report = _complete_trial(tmp_path, workloads=workloads)
    report["do_build"] = events[0]["do_build"] = True
    for cell in report["cells"]:
        cell["admission_decision"] = {
            "schema_version": "campaign-artifact-admission-decision/v1",
            "admission_status": "admitted", "classification": "admitted-new-schema",
        }
    if mixed:
        report["status"] = events[-1]["status"] = "partial"
        cell = report["cells"][-1]
        fallback = _campaignless_failure_cell()
        cell["admission_decision"] = fallback["admission_decision"]
        cell["pending_critic_disposition"] = fallback["pending_critic_disposition"]
        events[-1]["cell_admission_failures"] = [{
            "cell_index": 1, "workload": "ycsb-b",
            "admission_decision": cell["admission_decision"],
        }]
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[failure-only-diagnostic\] report is not an exact supported failure-only shape$"):
        _diagnostic_verify(run)


@pytest.mark.parametrize("kind", ["fatal-empty", "campaignless"])
def test_failure_only_diagnostic_does_not_change_existing_exemptions(tmp_path, monkeypatch, kind):
    if kind == "fatal-empty":
        run, events, report = _provider_init_trial(tmp_path)
        report["do_build"] = events[0]["do_build"] = True
    else:
        run, events, report = _failure_only_producer(tmp_path, monkeypatch)
        cell = report["cells"][0]
        report["cells"] = [{key: cell[key] for key in _campaignless_failure_cell()}]
    _persist(run, events, report)
    assert C.verify_autonomous_trial_files(run / "attempts.jsonl", run / "report.json") is None
    assert _diagnostic_verify(run) is None


def test_failure_only_diagnostic_rejects_independently_admitted_campaign(tmp_path, monkeypatch):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch)
    output, campaign, persisted, _, admitted_cell = _layer3_campaign(tmp_path / "admitted")
    persisted.unlink()
    # Bind the failure report to the real admitted campaign, without replacing
    # either admission checker or Layer-3 chain.
    report["cells"][0]["campaign_id"] = admitted_cell["campaign_id"]
    report["cells"][0]["campaign_root"] = admitted_cell["campaign_root"]
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[campaign-chain\] cells\[0\] failure campaign remains independently admitted$"):
        _diagnostic_verify(run)


def test_failure_only_diagnostic_rejects_exploratory_provider_claim(tmp_path, monkeypatch):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch, mode="roles")
    event = next(e for e in events if e["event"] == "role-attempt")
    event["provider_artifacts"] = {"payload_path": "absent"}
    report["cells"][0]["generations"][0]["roles"][event["role"]]["provider_artifacts"] = event["provider_artifacts"]
    _persist(run, events, report)
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[failure-only-provider\] exploratory role declares arm-bound artifacts$"):
        _diagnostic_verify(run)


@pytest.mark.parametrize("mode", ["invalid-pre-raw", "invalid-post-raw"])
def test_failure_only_diagnostic_rejects_unproven_error_artifact_absence(tmp_path, monkeypatch, mode):
    run, events, report = _failure_only_producer(tmp_path, monkeypatch, mode=mode)
    assert "fatal_error" not in report
    event = next(e for e in events if e["event"] == "role-attempt")
    assert event["status"] == "invalid"
    assert ("raw_response_path" in event["error_artifacts"]) == (mode == "invalid-post-raw")
    with pytest.raises(C.AutonomousTrialCompletenessError,
                       match=r"\[failure-only-diagnostic\] report is not an exact supported failure-only shape$"):
        _diagnostic_verify(run)


if __name__ == "__main__":  # pragma: no cover - plain-runner false-green guard
    raise SystemExit(pytest.main([__file__, "-x"]))
