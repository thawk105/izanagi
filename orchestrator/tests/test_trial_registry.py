# -*- coding: utf-8 -*-
"""T-325 exact trial registry gates and preregistered mutations."""
from __future__ import annotations

import ast
import copy
import dataclasses
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

import pytest

from orchestrator.campaign import p3_autonomous_workload_trial as producer
from orchestrator.campaign import autonomous_trial_completeness as completeness
from orchestrator.campaign import campaign_lock
from orchestrator.campaign import layer3_report as L3
from orchestrator.campaign import pipeline
from orchestrator.campaign import reflux_ir
from orchestrator.campaign import reflux_formal_consumer as formal
from orchestrator.campaign import reflux_origin_binding as origin_binding
from orchestrator.campaign import s8b_descriptor
from orchestrator.campaign import s8c_arm_inputs
from orchestrator.campaign import trigger_gate_binding as TGB
from orchestrator.campaign import trial_registry as R
from orchestrator.campaign.build_admission import (
    attest_generator_output,
    derive_build_admission,
)
from orchestrator.campaign.source_digest import (
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from orchestrator.campaign import source_digest, wal
from orchestrator.tests.campaign_lock_test_support import build_v2_lock
from orchestrator.tests import reflux_origin_fixture_builder as origin_fixtures
from orchestrator.tests import commit_receipt_support as receipt_support
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import Genome


_SOURCE_REPO = Path(__file__).resolve().parents[2]
_ROLES = ("planner", "coder", "auditor", "critic")
_GENERATION_DRIVER = {
    "wrapper": "s8c-generation/v1",
    "delegate": "trigger.drive_iteration",
}
_GATING_SPEC_SHA256 = hashlib.sha256(
    producer.GATING_SPEC.encode("utf-8")
).hexdigest()
_REGISTERED_FIXTURE_GENOME = Genome("fixture", {})
_REGISTERED_SOURCE_ASSIGNMENT = reflux_ir.emit_predicate(
    reflux_ir.parse_wire("00000")
)


def _registered_source_preimage() -> bytes:
    contexts = []
    for index in range(len(source_digest.CONTEXT_MACROS) + 1):
        contexts.append(b"\n".join((
            f"[ctx:{index}]".encode("ascii"),
            b"bool izanagi_gate_pass = true;",
            _REGISTERED_SOURCE_ASSIGNMENT.encode("utf-8"),
            b"if (izanagi_gate_pass) {",
        )))
    segments = [
        f"fixture-source-{index}".encode("ascii")
        for index, _path in enumerate(source_digest.EVOLVE_BLOCK_SOURCES)
    ]
    source_index = source_digest.EVOLVE_BLOCK_SOURCES.index(
        "cc/silo/transaction.cc"
    )
    segments[source_index] = b"\x02".join(contexts)
    return b"\0".join(segments)


_REGISTERED_SOURCE_PREIMAGE = _registered_source_preimage()
_REGISTERED_SOURCE_SHA256 = hashlib.sha256(
    _REGISTERED_SOURCE_PREIMAGE
).hexdigest()
_REGISTERED_FIXTURE_VARIANT = pipeline.variant_id(
    _REGISTERED_FIXTURE_GENOME, _REGISTERED_SOURCE_SHA256,
)
_T525_COMPLETE_CONDITION_CASES = (
    ("workload_flags", "ycsb_zipf_skew"),
    ("workload_flags", "ycsb_rmw"),
    ("perf_config_scale", "records"),
    ("perf_config_scale", "threads"),
)


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        env=R._git_env(),
        check=False,
        capture_output=True,
        text=True,
    )


def _head(repo: Path) -> str:
    result = _run(repo, "rev-parse", "HEAD")
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _t525_condition_cell(trial: R.TrialSpec) -> dict[str, object]:
    expected = R.HOLDOUT_BINDINGS[trial.holdout]
    return {
        "workload": expected["workload"],
        "workload_flags": {
            field: expected[field]
            for field in ("ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw")
        },
        "perf_config_scale": {
            field: expected[field]
            for field in ("records", "threads")
        },
        "campaign_id": trial.campaign_id,
    }


def _t525_legacy_ratio_only_projection_passes(
    cell: dict[str, object], trial: R.TrialSpec,
) -> bool:
    expected = R.HOLDOUT_BINDINGS[trial.holdout]
    flags = cell.get("workload_flags")
    return (
        cell.get("workload") == expected["workload"]
        and isinstance(flags, dict)
        and flags.get("ycsb_rratio") == expected["ycsb_rratio"]
        and cell.get("campaign_id") == trial.campaign_id
    )


def _commit(repo: Path, message: str, *paths: Path) -> str:
    relative = [str(path.relative_to(repo)) for path in paths]
    add = _run(repo, "add", "--", *relative)
    assert add.returncode == 0, add.stderr
    committed = _run(repo, "commit", "-q", "-m", message)
    assert committed.returncode == 0, committed.stderr
    return _head(repo)


def _init_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    init = _run(repo, "init", "-q")
    assert init.returncode == 0, init.stderr
    assert _run(repo, "config", "user.email", "fixture@example.invalid").returncode == 0
    assert _run(repo, "config", "user.name", "Fixture").returncode == 0
    seed = repo / "seed.txt"
    seed.write_text("seed\n", encoding="utf-8")
    return repo, _commit(repo, "seed", seed)


def _manifest_value(prereg_commit: str, prefix: str) -> dict:
    trials = []
    for holdout in R.HOLDOUTS:
        for arm in R.ARMS:
            token = f"{holdout.lower()}-{arm}"
            provisional = R.TrialSpec(
                trial_id=f"{prefix}-{token}",
                arm=arm,
                holdout=holdout,
                campaign_id="pending-campaign-identity",
                generations=2,
            )
            campaign_id, _identity_preimage = _fixture_campaign_identity(
                provisional
            )
            trials.append({
                "trial_id": provisional.trial_id,
                "arm": provisional.arm,
                "holdout": provisional.holdout,
                "campaign_id": campaign_id,
                "generations": provisional.generations,
            })
    return {
        "schema_version": R.MANIFEST_SCHEMA_VERSION,
        "prereg_commit": prereg_commit,
        "trials": trials,
    }


def _write_manifest(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _registration_value(manifest: R.TrialManifest) -> dict:
    return {
        "schema_version": R.REGISTRATION_SCHEMA_VERSION,
        "manifest_sha256": manifest.sha256,
        "prereg_commit": manifest.prereg_commit,
        "prereg_content_commit": manifest.prereg_commit,
        "prereg_effective_commit": manifest.prereg_commit,
        "trials": [
            {
                "trial_id": trial.trial_id,
                "arm": trial.arm,
                "holdout": trial.holdout,
                "campaign_id": trial.campaign_id,
                "generations": trial.generations,
            }
            for trial in manifest.trials
        ],
    }


def _write_registry(path: Path, *rows: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))


_FIXTURE_REGISTRATION_COMMITS: dict[tuple[str, str], tuple[str, str]] = {}


def _prepare_fixture_effective_binding(
    repo: Path,
    manifest_path: Path,
    manifest: R.TrialManifest,
) -> tuple[str, str]:
    """Create a real P/C pair and remember it for report fixtures.

    ``prereg_commit`` is the legacy activation alias in the manifest.  The
    manifest and the frozen attempt registry are introduced by P, while C is
    its direct child containing only the effective-binding record.
    """
    cached = _FIXTURE_REGISTRATION_COMMITS.get(
        (str(repo.resolve()), manifest.sha256),
    )
    if cached is not None:
        return cached
    attempt_path = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    if not attempt_path.exists():
        slots = _attempt_slots(manifest)
        R.create_attempt_registry_genesis(
            repository_root=repo,
            manifest_path=manifest_path,
            manifest_sha256=manifest.sha256,
            freeze_id=f"freeze-{manifest.sha256[:16]}",
            prereg_generation=13,
            slots=slots,
        )
    head = _head(repo)
    manifest_relative = manifest_path.relative_to(repo).as_posix()
    attempt_relative = attempt_path.relative_to(repo).as_posix()
    committed_manifest = R._blob_at_commit(
        repo, commit_id=head, relative_path=manifest_relative,
    )
    committed_attempt = R._blob_at_commit(
        repo, commit_id=head, relative_path=attempt_relative,
    )
    if committed_manifest != manifest.raw_bytes or committed_attempt != attempt_path.read_bytes():
        _commit(repo, "fixture content and attempt freeze", manifest_path, attempt_path)
    content_commit = _head(repo)
    genesis_bytes = attempt_path.read_bytes()
    genesis = json.loads(genesis_bytes.splitlines()[0])
    binding_value = {
        "schema_version": R.EFFECTIVE_BINDING_SCHEMA_VERSION,
        "prereg_content_commit": content_commit,
        "manifest_path": manifest_relative,
        "manifest_sha256": manifest.sha256,
        "freeze_id": genesis["freeze_id"],
        "attempt_registry_path": R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "attempt_registry_initial_sha256": hashlib.sha256(genesis_bytes).hexdigest(),
    }
    binding_path = repo / R.DEFAULT_EFFECTIVE_BINDING_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_bytes(R._canonical_json_bytes(binding_value))
    effective_commit = _commit(repo, "fixture effective binding", binding_path)
    _FIXTURE_REGISTRATION_COMMITS[(str(repo.resolve()), manifest.sha256)] = (
        content_commit, effective_commit,
    )
    return content_commit, effective_commit


def _fixture_registration_commits(
    repo: Path,
    manifest: R.TrialManifest,
) -> tuple[str, str]:
    return _FIXTURE_REGISTRATION_COMMITS[(str(repo.resolve()), manifest.sha256)]


def _append_fixture_registration(
    *,
    manifest_path: Path,
    repository_root: Path,
    registry_path: Path,
    prepare_binding: bool = True,
) -> R.TrialRegistration:
    manifest = R.load_trial_manifest(manifest_path)
    if prepare_binding:
        _content_commit, effective_commit = _prepare_fixture_effective_binding(
            repository_root, manifest_path, manifest,
        )
    else:
        effective_commit = manifest.prereg_commit
    return R.append_trial_registration(
        manifest_path=manifest_path,
        repository_root=repository_root,
        registry_path=registry_path,
        prereg_effective_commit=effective_commit,
    )


def _registered_repo(
    tmp_path: Path,
    *,
    prefix: str = "trial-a",
) -> tuple[Path, Path, Path, R.TrialManifest]:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / f"{prefix}-manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, prefix))
    _commit(repo, "manifest", manifest_path)
    registry_path = repo / "registry" / "registry.jsonl"
    _append_fixture_registration(
        manifest_path=manifest_path,
        repository_root=repo,
        registry_path=registry_path,
    )
    R.s8c_arm_inputs.generate_off_neutral_artifacts(repository_root=repo)
    _commit(
        repo,
        "registry and arm inputs",
        registry_path,
        repo / R.s8c_arm_inputs.OFF_DESCRIPTOR_RELATIVE_PATH,
        repo / R.s8c_arm_inputs.OFF_FREEZE_RELATIVE_PATH,
    )
    return repo, manifest_path, registry_path, R.load_trial_manifest(manifest_path)


def _payload_validation_receipt(
    event: dict,
    spec_key: str,
    workload_descriptor: dict,
    *,
    arm: str,
    content_digest: str,
) -> dict:
    role = event["role"]
    generation = event["generation"]
    fixed_literals = {
        "schema_version": producer.SCHEMA_VERSION,
        "pilot_scope": "exploratory-ycsb-abc",
        "scientific_claim": False,
        "attempt_policy": {"attempts_per_role_generation": 1, "retry": False},
        "stop_policy": {
            "performance_early_stop": False,
            "generation_budget_is_fixed": True,
        },
    }
    nested_key_sets = {
        "$": producer.ROLE_PAYLOAD_KEY_SPEC[spec_key],
        "$.attempt_policy": ["attempts_per_role_generation", "retry"],
        "$.stop_policy": [
            "generation_budget_is_fixed", "performance_early_stop",
        ],
    }
    projection_workload = event["workload"]
    descriptor_binding_sha256 = "2" * 64
    if arm == "off":
        projection_workload = producer.OFF_NEUTRAL_PAYLOAD_WORKLOAD
        descriptor_binding_sha256 = (
            completeness._off_payload_descriptor_binding_sha256(content_digest)
        )
    projection = {
        "role": role,
        "workload": projection_workload,
        "generation": generation,
        "descriptor_sha256": event["descriptor_sha256"],
        "workload_descriptor_sha256": hashlib.sha256(
            s8c_arm_inputs.canonical_execution_input_bytes(
                workload_descriptor
            )
        ).hexdigest(),
        "descriptor_binding_sha256": descriptor_binding_sha256,
        "fixed_literals": fixed_literals,
        "nested_key_sets": nested_key_sets,
        "whiteboard_origin": [],
        "whiteboard_origin_sha256": hashlib.sha256(b"[]").hexdigest(),
    }
    if role == "planner":
        nested_key_sets.update({
            "$.current_perf": sorted(completeness._PERF_KEYS),
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
                    for metric in completeness._DIAGNOSTIC_METRICS
                ],
                "uncertainty_present": True,
                "reverse_recommended": False,
            }
        projection.update({
            "current_perf_nullness": {
                key: True for key in sorted(completeness._PERF_KEYS)
            },
            "leading_metric_nullness": {
                key: True for key in sorted(completeness._LEADING_METRIC_KEYS)
            },
            "contention_level_sha256": hashlib.sha256(b'"high"').hexdigest(),
            "critic_feedback": feedback,
        })
    else:
        fixed_literals.update({
            "leakproof_context": completeness._LEAKPROOF_CONTEXT,
            "planner_axis": completeness._PLANNER_AXIS,
        })
        nested_key_sets.update({
            "$.baseline": sorted(completeness._PERF_KEYS),
            "$.planner_direction": ["axis", "direction", "magnitude"],
        })
        projection.update({
            "baseline_nullness": {
                key: True for key in sorted(completeness._PERF_KEYS)
            },
            "gating_spec_sha256": _GATING_SPEC_SHA256,
            "planner_direction_sha256": "3" * 64,
        })
    projection_sha256 = hashlib.sha256(_canonical(projection)).hexdigest()
    seal_preimage = {
        "schema_version": completeness._VALIDATION_RECEIPT_SCHEMA_VERSION,
        "role": role,
        "payload_sha256": event["input_payload_sha256"],
        "payload_allowlist_sha256": producer.ROLE_PAYLOAD_ALLOWLIST_SHA256,
        "safe_projection_sha256": projection_sha256,
    }
    return {
        **seal_preimage,
        "safe_projection": projection,
        "seal_sha256": hashlib.sha256(_canonical(seal_preimage)).hexdigest(),
    }


def _role_event(
    workload: str,
    role: str,
    seq: int,
    descriptor_hash: str,
    workload_descriptor: dict,
    *,
    arm: str,
    arm_binding_digest: str,
    generation: int = 1,
    role_query_ordinal: int | None = None,
) -> dict:
    spec_key = (
        "planner-generation-1"
        if role == "planner" and generation == 1
        else "planner-generation-next"
        if role == "planner"
        else role
    )
    event = {
        "event": "role-attempt",
        "workload": workload,
        "generation": generation,
        "role": role,
        "attempt": 1,
        "invocation_id": (
            f"arm-{arm}.exec-{arm_binding_digest}."
            f"{workload}.g{generation}.{role}"
        ),
        "seq": seq,
        "ts": f"2026-08-01T00:00:{seq:02d}+00:00",
        "status": "valid",
        "retry": False,
        "input_payload_sha256": hashlib.sha256(
            f"payload:{workload}:{generation}:{role}".encode()
        ).hexdigest(),
        "descriptor_sha256": descriptor_hash,
        "arm_binding_digest_sha256": arm_binding_digest,
        "raw_response_path": (
            f"/fixture/raw-{workload}-g{generation}-{role}.json"
        ),
        "raw_response_sha256": hashlib.sha256(
            f"response:{workload}:{generation}:{role}".encode()
        ).hexdigest(),
        "parsed": {"fixture_role": role},
        "provenance": {"fixture": True},
        "payload_exact_keys": producer.ROLE_PAYLOAD_KEY_SPEC[spec_key],
        "payload_allowlist_sha256": producer.ROLE_PAYLOAD_ALLOWLIST_SHA256,
        "role_query_ordinal": (
            seq - 1 if role_query_ordinal is None else role_query_ordinal
        ),
    }
    if role in {"planner", "coder"}:
        event["payload_validation_receipt"] = _payload_validation_receipt(
            event,
            spec_key,
            workload_descriptor,
            arm=arm,
            content_digest=descriptor_hash,
        )
    return event


def _base_start(
    trial: R.TrialSpec,
    run: Path,
    measurement_head: str,
    *,
    generation_budget: int = 2,
) -> dict:
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    return {
        "event": "run-start",
        "schema_version": producer.SCHEMA_VERSION,
        "trial_id": trial.trial_id,
        "provider": "fixture",
        "workloads": [workload],
        "generation_budget_per_workload": generation_budget,
        "max_wall_s": 60,
        "do_build": False,
        "performance_early_stop": False,
        "scientific_claim": False,
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "honest_accounting_authority": "supervisor-authoritative",
        "prereg_commit": None,
        "prereg_content_commit": None,
        "prereg_effective_commit": None,
        "slot_id": None,
        "measurement_head": measurement_head,
        "manifest_sha256": None,
        "seq": 1,
        "ts": "2026-08-01T00:00:01+00:00",
    }


def _base_report(
    trial: R.TrialSpec,
    run: Path,
    measurement_head: str,
    *,
    generation_budget: int = 2,
) -> dict:
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    return {
        "schema_version": producer.REPORT_SCHEMA_VERSION,
        "trial_id": trial.trial_id,
        "status": "complete",
        "started_at": "2026-08-01T00:00:00+00:00",
        "finished_at": "2026-08-01T00:01:00+00:00",
        "provider": "fixture",
        "do_build": False,
        "workloads_requested": [workload],
        "generation_budget_per_workload": generation_budget,
        "stop_policy": {
            "fixed_generations": True,
            "performance_early_stop": False,
            "max_wall_s": 60,
        },
        "claim_scope": {"scientific_claim": False},
        "attempt_journal": str(run / "attempts.jsonl"),
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "honest_accounting": {
            "role_query_count": 0,
            "bench_wall_seconds": 0.0,
        },
        "honest_accounting_authority": "supervisor-authoritative",
        "cells": [],
        "prereg_commit": None,
        "prereg_content_commit": None,
        "prereg_effective_commit": None,
        "slot_id": None,
        "raw_output_sha256": None,
        "observation_sha256": None,
        "primary_value": None,
        "measurement_head": measurement_head,
        "manifest_sha256": None,
    }


def _persist(run: Path, events: list[dict], report: dict) -> Path:
    run.mkdir(parents=True, exist_ok=True)
    journal_bytes = b"".join(_canonical(event) + b"\n" for event in events)
    (run / "attempts.jsonl").write_bytes(journal_bytes)
    report["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()
    (run / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return run / "report.json"


def _accounting_event(workload: str, generation: int, seq: int) -> dict:
    return {
        "event": "generation-accounting",
        "workload": workload,
        "generation": generation,
        "state": "generation-complete",
        "provider_invoke_count": 4,
        "auditor_pre_audit_skipped": False,
        "bench_wall_seconds": 0.0,
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "accounting_authority": "supervisor-authoritative",
        "seq": seq,
        "ts": f"2026-08-01T00:00:{seq:02d}+00:00",
    }


def _finish_event(run: Path, status: str, seq: int, queries: int) -> dict:
    return {
        "event": "run-finish",
        "status": status,
        "report": str(run / "report.json"),
        "generation_driver": dict(_GENERATION_DRIVER),
        "gating_spec_sha256": _GATING_SPEC_SHA256,
        "honest_accounting": {
            "role_query_count": queries,
            "bench_wall_seconds": 0.0,
        },
        "honest_accounting_authority": "supervisor-authoritative",
        "seq": seq,
        "ts": f"2026-08-01T00:01:{seq:02d}+00:00",
    }


def _fixture_launch_admission(
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
    *,
    prereg_content_commit: str | None = None,
    prereg_effective_commit: str | None = None,
    origin_binding_record: dict | None = None,
) -> dict:
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    content_commit = prereg_content_commit or manifest.prereg_commit
    effective_commit = prereg_effective_commit or measurement_head
    activation_digest = R.s8c_preregistration._construct_effective(
        _effective_report(manifest)
    ).report_digest_sha256
    record = {
        "mode": "registered-effective",
        "certifying": False,
        "reason_code": "registered-effective-non-certifying",
        "trial_id": trial.trial_id,
        "workloads": [workload],
        "binding": {
            "manifest_sha256": manifest.sha256,
            "prereg_commit": manifest.prereg_commit,
            "prereg_content_commit": content_commit,
            "prereg_effective_commit": effective_commit,
            "measurement_head": measurement_head,
            "trial_id": trial.trial_id,
            "arm": trial.arm,
            "holdout": trial.holdout,
            "campaign_id": trial.campaign_id,
            "workload": workload,
            "ycsb_rratio": R.HOLDOUT_BINDINGS[trial.holdout]["ycsb_rratio"],
        },
        "prereg_content_commit": content_commit,
        "prereg_effective_commit": effective_commit,
        "activation_report_digest_sha256": activation_digest,
    }
    if origin_binding_record is not None:
        record["origin_binding"] = copy.deepcopy(origin_binding_record)
    return record


_ARM_CONTENT_DIGESTS = {
    ("H1", "on"): "80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843",
    ("H1", "off"): "8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89",
    ("H1", "swapped"): "53230b8b1f0e0d82def3c384f4d8d8b050a1ce872afd2ed9e2a403c61c3c550b",
    ("H2", "on"): "53230b8b1f0e0d82def3c384f4d8d8b050a1ce872afd2ed9e2a403c61c3c550b",
    ("H2", "off"): "8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89",
    ("H2", "swapped"): "80501db0235d88314edd4a4c29a1949e67acc2b466ae426fbbb1cb3da4b7d843",
}


def _fixture_arm_execution(trial: R.TrialSpec) -> dict[str, str]:
    descriptor = _fixture_execution_descriptor(trial)
    content_digest = hashlib.sha256(_canonical(descriptor)).hexdigest()
    assert content_digest == _ARM_CONTENT_DIGESTS[(trial.holdout, trial.arm)]
    arm_binding_digest = hashlib.sha256(
        b"izanagi-s8c-arm-binding/v1\0"
        + trial.holdout.encode("ascii")
        + trial.arm.encode("ascii")
        + content_digest.encode("ascii")
    ).hexdigest()
    return {
        "input_schema_version": "8b-v1",
        "content_digest_sha256": content_digest,
        "arm_binding_digest_sha256": arm_binding_digest,
    }


def _fixture_execution_descriptor(trial: R.TrialSpec) -> dict:
    ratios = {
        ("H1", "on"): 80,
        ("H1", "off"): 50,
        ("H1", "swapped"): 20,
        ("H2", "on"): 20,
        ("H2", "off"): 50,
        ("H2", "swapped"): 80,
    }
    descriptor = {
        "schema_version": "8b-v1",
        "source": "campaign_search_config_projection",
        "read_write": {
            "read_ratio_percent": ratios[(trial.holdout, trial.arm)],
            "rmw": 0,
        },
        "contention": {"skew": 0.9, "label": "high"},
        "scale": {"records": 1_000_000, "threads": 48},
        "objective": "maximize_throughput_tps",
        "correctness": "serializable_legacy_and_s2",
    }
    return descriptor


def _fixture_descriptor_binding(
    descriptor: dict,
    arm_execution: dict[str, str],
) -> dict[str, str]:
    content_digest = hashlib.sha256(_canonical(descriptor)).hexdigest()
    assert content_digest == arm_execution["content_digest_sha256"]
    binding = s8b_descriptor.projection_record(descriptor, descriptor)
    binding.update({
        "input_sha256": content_digest,
        "output_sha256": content_digest,
        "content_digest_sha256": content_digest,
        "arm_binding_digest_sha256": arm_execution[
            "arm_binding_digest_sha256"
        ],
    })
    return binding


def _fixture_workload_flags(trial: R.TrialSpec) -> dict[str, str]:
    return {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": R.HOLDOUT_BINDINGS[trial.holdout]["ycsb_rratio"],
        "ycsb_rmw": "0",
    }


def _fixture_slot_id(trial: R.TrialSpec) -> str:
    return f"{trial.trial_id}-r0-a0"


def _fixture_schedule_row_sha256(trial: R.TrialSpec) -> str:
    schedule = {
        "trial_id": trial.trial_id,
        "arm": trial.arm,
        "holdout": trial.holdout,
        "campaign_id": trial.campaign_id,
        "replicate_index": 0,
        "attempt_index": 0,
    }
    return hashlib.sha256(_canonical(schedule)).hexdigest()


def _fixture_process_identity(trial: R.TrialSpec) -> dict[str, object]:
    return {
        "pid": 1000 + list(R.ARMS).index(trial.arm) + 10 * list(R.HOLDOUTS).index(trial.holdout),
        "starttime": "fixture-start",
        "execution_uuid": f"fixture-{trial.trial_id}",
    }


def _fixture_raw_output_sha256(trial: R.TrialSpec) -> str:
    return hashlib.sha256(f"raw-output:{trial.trial_id}".encode("ascii")).hexdigest()


def _fixture_observation_sha256(trial: R.TrialSpec) -> str:
    return hashlib.sha256(f"observation:{trial.trial_id}".encode("ascii")).hexdigest()


def _fixture_campaign_identity(trial: R.TrialSpec) -> tuple[str, str]:
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    entry = producer.resolve_workload_entry(workload)
    arm_execution = _fixture_arm_execution(trial)
    build_context = producer.build_run_context(
        generator_id=producer.GeneratorId.S8A_TRIGGER_SWEEP,
    )
    identity_preimage = campaign_lock.canonical_json({
        "spec_content": completeness._AUTONOMOUS_SPEC_CONTENT,
        "ccbench_commit": completeness._CURRENT_CCBENCH_PIN,
        "search_tag": "workload-conditioned-autonomous",
        "search_config": {
            "axis": "silo-backoff-trigger-gating",
            "descriptor_schema": arm_execution["input_schema_version"],
            "descriptor_sha256": arm_execution["content_digest_sha256"],
            "generation_budget": trial.generations,
            "pilot_scope": "exploratory-ycsb-abc",
            "records": entry["records"],
            "reflux": "on",
            "scale": "silo",
            "stop_policy": "fixed-generations-no-performance-early-stop",
            "threads": entry["threads"],
            "trigger_gate_binding_schema": (
                "izanagi-trigger-gate-binding/v1"
            ),
            "verify": "legacy+s2",
            "workload": workload,
            "ycsb": _fixture_workload_flags(trial),
            "build_admission": dict(build_context.policy.as_preimage()),
            "arm_binding_digest_sha256": arm_execution[
                "arm_binding_digest_sha256"
            ],
        },
        "trial": f"{trial.trial_id}-{workload}",
    })
    campaign_id = (
        f"p3-t178-{workload}-workload-conditioned-autonomous-"
        f"{hashlib.sha256(identity_preimage.encode('utf-8')).hexdigest()[:8]}"
    )
    return campaign_id, identity_preimage


def _fixture_origin_binding(
    trial: R.TrialSpec,
    measurement_head: str,
) -> dict:
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    return origin_fixtures.build_launch_admission_inputs(
        campaign_id=trial.campaign_id,
        trial_workload=workload,
        measurement_head=measurement_head,
        issuer_seal="launch-admission-gate/v1",
    )


def _issued_origin_binding(
    trial: R.TrialSpec,
    measurement_head: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    origin_binding_record: dict | None = None,
) -> origin_binding.OriginBindingCapability:
    wire = (
        _fixture_origin_binding(trial, measurement_head)
        if origin_binding_record is None
        else origin_binding_record
    )
    seal = object()
    capability = origin_binding.OriginBindingCapability(
        authority_blob_sha256=wire["authority_blob_sha256"],
        source_closure_sha256=wire["source_closure_sha256"],
        origin_id=wire["origin_id"],
        cell_key=wire["cell_key"],
        authority_workload=origin_binding.AuthorityWorkload(
            **wire["authority_workload"],
        ),
        axis_semantics_sha256=wire["axis_semantics_sha256"],
        verifier_policy_sha256=wire["verifier_policy_sha256"],
        environment_contract_sha256=wire["environment_contract_sha256"],
        campaign_id=wire["campaign_id"],
        trial_workload=wire["trial_workload"],
        measurement_head=wire["measurement_head"],
        store_scope="fixture",
        _seal=seal,
    )
    monkeypatch.setitem(
        origin_binding._ISSUED_CAPABILITY_FIELDS,
        seal,
        origin_binding._capability_fields(capability),
    )
    return capability


def _origin_terminal_projection(
    *,
    rejected: bool,
    origin_binding_record: dict,
    arm_binding_digest_sha256: str,
) -> formal.OriginTerminalProjection:
    return formal.OriginTerminalProjection(
        schema_version=formal.ORIGIN_TERMINAL_PROJECTION_SCHEMA_VERSION,
        reason_code=(
            formal.FormalReasonCode.FC01
            if rejected
            else formal.FormalReasonCode.P6_UNAVAILABLE
        ),
        formal_receipt_sha256=None if rejected else "7" * 64,
        evidence_root_sha256=None if rejected else "8" * 64,
        authority_blob_sha256=origin_binding_record["authority_blob_sha256"],
        origin_id=origin_binding_record["origin_id"],
        cell_key=origin_binding_record["cell_key"],
        terminal_payload_sha256="9" * 64,
        arm_binding_digest_sha256=arm_binding_digest_sha256,
    )


def _complete_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
    *,
    generation_budget: int = 2,
    repository_root: Path | None = None,
) -> Path:
    run = root / f"run-{trial.trial_id}"
    registration_root = root.parent if repository_root is None else repository_root
    content_commit, effective_commit = _fixture_registration_commits(
        registration_root, manifest,
    )
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    entry = producer.resolve_workload_entry(workload)
    workload_flags = _fixture_workload_flags(trial)
    descriptor = _fixture_execution_descriptor(trial)
    arm_execution = _fixture_arm_execution(trial)
    descriptor_hash = arm_execution["content_digest_sha256"]
    arm_binding_digest = arm_execution["arm_binding_digest_sha256"]
    descriptor_binding = _fixture_descriptor_binding(
        descriptor, arm_execution,
    )
    campaign_id, campaign_identity_preimage = _fixture_campaign_identity(trial)
    assert campaign_id == trial.campaign_id
    campaign_root = run / "campaigns" / campaign_id
    campaign_root.mkdir(parents=True, exist_ok=True)
    (campaign_root / "campaign.lock").write_text(
        build_v2_lock(campaign_identity_preimage), encoding="utf-8",
    )
    start = _base_start(
        trial, run, measurement_head, generation_budget=generation_budget,
    )
    report = _base_report(
        trial, run, measurement_head, generation_budget=generation_budget,
    )
    for target in (start, report):
        target["prereg_commit"] = manifest.prereg_commit
        target["prereg_content_commit"] = content_commit
        target["prereg_effective_commit"] = effective_commit
        target["slot_id"] = _fixture_slot_id(trial)
        target["manifest_sha256"] = manifest.sha256
        target["arm_execution"] = copy.deepcopy(arm_execution)
        target["launch_admission"] = _fixture_launch_admission(
            trial,
            manifest,
            measurement_head,
            prereg_content_commit=content_commit,
            prereg_effective_commit=effective_commit,
        )
    report["raw_output_sha256"] = _fixture_raw_output_sha256(trial)
    report["observation_sha256"] = _fixture_observation_sha256(trial)
    report["primary_value"] = 1.0
    events = [start]
    generations = []
    seq = 2
    ordinal = 1
    for generation in range(1, generation_budget + 1):
        roles: dict[str, dict] = {}
        for role in _ROLES:
            event = _role_event(
                workload,
                role,
                seq,
                descriptor_hash,
                descriptor,
                arm=trial.arm,
                arm_binding_digest=arm_binding_digest,
                generation=generation,
                role_query_ordinal=ordinal,
            )
            events.append(event)
            roles[role] = copy.deepcopy(event)
            seq += 1
            ordinal += 1
        proposal_value = {
            "planner": {
                "axis": "silo-backoff-trigger-gating",
                "direction": "increase",
                "magnitude": "small",
                "justification": "fixture",
                "uncertainty": "low",
            },
            "coder": {
                "axis": "silo-backoff-trigger-gating",
                "wire": "00000",
                "justification": "fixture",
                "confidence": "high",
            },
            "auditor": {
                "verdict": "allow",
                "diff_digest": "a" * 64,
                "violations": [],
                "nits": [],
                "proposed_tests": [],
                "uncertainty": "low",
            },
            "prior_critic_reverse": False,
            "descriptor_sha256": descriptor_hash,
            "arm_binding_digest_sha256": arm_binding_digest,
        }
        proposal_path = (
            run / "proposals"
            / (
                f"arm-{trial.arm}.exec-{arm_binding_digest}."
                f"{workload}.g{generation}.json"
            )
        )
        proposal_path.parent.mkdir(parents=True, exist_ok=True)
        proposal_bytes = _canonical(proposal_value)
        proposal_path.write_bytes(proposal_bytes)
        generations.append({
            "generation": generation,
            "roles": roles,
            "proposal": {
                "path": str(proposal_path),
                "sha256": hashlib.sha256(proposal_bytes).hexdigest(),
                "digest": arm_binding_digest,
            },
            "preview": {"passed": True, "forbidden_identifiers": []},
            "harness": {
                "outcome": "dry-pass",
                "variant": None,
                "stop_reason": "continue",
                "iteration": generation,
                "ran": True,
                "critic_digest_generated": False,
            },
            "outcome": "dry-pass",
            "bench_wall_seconds": 0.0,
            "generation_driver": dict(_GENERATION_DRIVER),
            "gating_spec_sha256": _GATING_SPEC_SHA256,
        })
        events.append(_accounting_event(workload, generation, seq))
        seq += 1
    report["cells"] = [{
        "workload": workload,
        "workload_flags": workload_flags,
        "perf_config_scale": {
            "records": entry["records"],
            "threads": entry["threads"],
        },
        "descriptor": descriptor,
        "descriptor_binding": descriptor_binding,
        "campaign_id": campaign_id,
        "campaign_root": str(campaign_root),
        "admission_decision": {"admission_status": "not-applicable"},
        "generations": generations,
        "stop_reason": "fixed-generation-budget",
    }]
    report["honest_accounting"]["role_query_count"] = ordinal - 1
    events.append(_finish_event(run, "complete", seq, ordinal - 1))
    return _persist(run, events, report)


def _build_registered_campaign(
    *, output_root: Path, trial: R.TrialSpec, proposal_paths: list[Path],
) -> tuple[Path, dict]:
    assert len(proposal_paths) == trial.generations
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    entry = producer.resolve_workload_entry(workload)
    descriptor = _fixture_execution_descriptor(trial)
    arm_execution = _fixture_arm_execution(trial)
    descriptor_record = _fixture_descriptor_binding(descriptor, arm_execution)
    context = producer.build_run_context(
        generator_id=producer.GeneratorId.S8A_TRIGGER_SWEEP,
    )
    contract = producer.env_contract.GENERATIONS["linux-baremetal"][0].contract
    config = producer._campaign_for(
        workload=workload,
        entry=entry,
        descriptor=descriptor,
        descriptor_record=descriptor_record,
        trial_id=trial.trial_id,
        generations=trial.generations,
        contract=contract,
        build_context=context,
        arm_binding_digest_sha256=arm_execution["arm_binding_digest_sha256"],
    )
    campaign_id = str(producer.ident.campaign_id(config))
    assert campaign_id == trial.campaign_id
    campaign = output_root / "campaigns" / campaign_id
    layout = CampaignLayout(root=str(campaign)).ensure()
    assert producer.ident.ensure_campaign_identity(
        config, layout, admission_policy=context.policy,
    )
    state_path = campaign / "loop_state.json"
    state_path.write_text(json.dumps({"whiteboard": []}), encoding="utf-8")
    genome = _REGISTERED_FIXTURE_GENOME.canonical()
    variant = _REGISTERED_FIXTURE_VARIANT
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(output_root.resolve()),
        ccbench_commit=completeness._CURRENT_CCBENCH_PIN,
        genome_sha256=hashlib.sha256(genome.encode("utf-8")).hexdigest(),
        src_token=_REGISTERED_SOURCE_SHA256,
        source_bytes_sha256=_REGISTERED_SOURCE_SHA256,
        tracked_clean=True,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
        tracked_paths=(),
    )
    generator_receipt = attest_generator_output(
        context,
        evidence,
        generator_input_sha256=hashlib.sha256(
            proposal_paths[0].read_bytes()
        ).hexdigest(),
    )
    admission = derive_build_admission(
        context, evidence, generator_receipt=generator_receipt,
    ).as_wal_receipt()
    records = []
    provenance_entries = {}
    for generation, proposal_path in enumerate(proposal_paths, 1):
        attempt_id = f"attempt-{generation}"
        binding = TGB.TriggerGateBinding(
            mask=0,
            predicate_sha256=TGB.expected_predicate_sha256(0),
            nonce=hashlib.sha256(attempt_id.encode("ascii")).hexdigest(),
            source=TGB.SourceBinding(
                src_token=evidence.src_token,
                source_bytes_sha256=evidence.source_bytes_sha256,
            ),
        )
        binding_commitment = TGB.commitment(binding)
        terminal = {
            "build_attempt_id": attempt_id,
            "build_admission_receipt_sha256": admission["receipt_sha256"],
        }
        base_ts = float((generation - 1) * 5)
        records.extend([
            {
                "ts": base_ts + 0.5,
                "stage": TGB.WAL_RECORD_STAGE,
                "variant": variant,
                "env_tag": contract.env_tag,
                "payload": {
                    "build_attempt_id": attempt_id,
                    "trigger_gate_binding": TGB.to_record(binding),
                },
            },
            {
                "ts": base_ts + 1.0,
                "stage": "build_start",
                "variant": variant,
                "env_tag": contract.env_tag,
                "payload": {
                    "build_attempt_id": attempt_id,
                    "genome": genome,
                    "src_token": _REGISTERED_SOURCE_SHA256,
                    "build_admission": admission,
                    "build_admission_receipt_sha256": admission["receipt_sha256"],
                    "trigger_gate_binding_commitment": binding_commitment,
                },
            },
            {
                "ts": base_ts + 2.0,
                "stage": "build_done",
                "variant": variant,
                "env_tag": contract.env_tag,
                "payload": dict(terminal),
            },
            {
                "ts": base_ts + 3.0,
                "stage": "bench_done",
                "variant": variant,
                "env_tag": contract.env_tag,
                "payload": {
                    "tps": [1.0],
                    "median_tps": 1.0,
                    "cv": 0.0,
                    "rounds": 1,
                    "bench_wall_s": 0.0,
                    "build_attempt_id": attempt_id,
                    "leading_indicators": {},
                },
            },
            *(
                {
                    "ts": base_ts + 3.0 + index / 4,
                    "stage": "verify_done",
                    "variant": variant,
                    "env_tag": contract.env_tag,
                    "payload": {
                        "build_attempt_id": attempt_id,
                        "verdict": "serializable",
                        "certified": True,
                        "anomalies": 0,
                        "workload": {"tag": tag},
                    },
                }
                for index, tag in enumerate(
                    (pipeline.LEGACY_TAG, pipeline.S2_TAG), 1,
                )
            ),
            {
                "ts": base_ts + 4.0,
                "stage": "commit",
                "variant": variant,
                "env_tag": contract.env_tag,
                "payload": {
                    **terminal,
                    "contract_sha256": contract.contract_sha256,
                },
            },
        ])
        provenance_entries[str(generation)] = {
            "proposal_path": str(proposal_path),
            "variant": variant,
            "build_attempt_id": attempt_id,
            "trigger_gate_binding_commitment": binding_commitment,
            "outcome": "certified",
        }
    for record in records:
        if record["stage"] == "commit":
            receipt_support.log_receipted_commit(
                layout,
                record["variant"],
                record["env_tag"],
                record["payload"],
                operation_identity=record["payload"]["build_attempt_id"],
                tags=(pipeline.LEGACY_TAG, pipeline.S2_TAG),
                ts=record["ts"],
            )
        else:
            wal.log(
                layout,
                record["variant"],
                record["stage"],
                record["env_tag"],
                record["payload"],
                ts=record["ts"],
            )
    (campaign / "reports" / "p3_s8a_trigger_loop_provenance.json").write_text(
        json.dumps({
            "entries": provenance_entries,
        }),
        encoding="utf-8",
    )
    for proposal_path in proposal_paths:
        proposal_sha256 = hashlib.sha256(proposal_path.read_bytes()).hexdigest()
        preimage_path = campaign / source_digest.source_preimage_artifact_relative_path(
            proposal_sha256
        )
        preimage_path.parent.mkdir(parents=True, exist_ok=True)
        if preimage_path.exists():
            assert preimage_path.read_bytes() == _REGISTERED_SOURCE_PREIMAGE
        else:
            preimage_path.write_bytes(_REGISTERED_SOURCE_PREIMAGE)
    persisted = L3.build_report(
        campaign,
        generated_from_head="a" * 40,
        output_root=output_root,
    )
    persisted_path = campaign / "reports" / "layer3_report.json"
    persisted_path.write_text(
        json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return campaign, persisted


def _prepare_registered_build_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
    *,
    repository_root: Path | None = None,
) -> Path:
    report_path = _complete_report(
        root,
        trial,
        manifest,
        measurement_head,
        repository_root=repository_root,
    )
    events, report = _load_report_bundle(report_path)
    run_root = report_path.parent
    output_root = run_root.parent.parent
    proposal_paths = [
        Path(generation["proposal"]["path"])
        for generation in report["cells"][0]["generations"]
    ]
    campaign, persisted = _build_registered_campaign(
        output_root=output_root, trial=trial, proposal_paths=proposal_paths,
    )
    report["do_build"] = True
    events[0]["do_build"] = True
    cell = report["cells"][0]
    cell["campaign_root"] = str(campaign)
    cell["admission_decision"] = copy.deepcopy(persisted["admission_decision"])
    for generation_number, generation in enumerate(cell["generations"], 1):
        attempt_id = f"attempt-{generation_number}"
        bench = persisted["runs"][generation_number - 1]
        assert bench.get("variant") == _REGISTERED_FIXTURE_VARIANT
        generation["harness"].update({
            "variant": _REGISTERED_FIXTURE_VARIANT,
            "records": {"bench_done": {
                key: value for key, value in bench.items()
                if key != "source_ref"
            }},
        })
        generation["harness"]["records"]["bench_done"].pop(
            "variant", None,
        )
        generation["harness"]["records"]["bench_done"][
            "build_attempt_id"
        ] = attempt_id
        generation["bench_wall_seconds"] = 0.0
    by_invocation = {
        event["invocation_id"]: event
        for event in events if event.get("event") == "role-attempt"
    }
    for ordinal, event in enumerate(by_invocation.values(), 1):
        role_root = run_root / "provider" / str(ordinal)
        role_root.mkdir(parents=True, exist_ok=True)
        raw_path = run_root / "raw" / f"response-{ordinal}.txt"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path = role_root / f"payload_{event['invocation_id']}.json"
        envelope_path = role_root / f"envelope_{event['invocation_id']}.json"
        raw_path.write_bytes(f"raw response {ordinal}\n".encode())
        payload_path.write_bytes(_canonical({
            "workload_descriptor": cell["descriptor"],
            "descriptor_binding": cell["descriptor_binding"],
        }))
        envelope_path.write_bytes(_canonical({
            "result": "fixture",
            "type": "result",
        }))
        payload_sha = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        envelope_sha = hashlib.sha256(envelope_path.read_bytes()).hexdigest()
        raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        update = {
            "raw_response_path": str(raw_path),
            "raw_response_sha256": raw_sha,
            "input_payload_sha256": payload_sha,
            "provider_payload_sha256": payload_sha,
            "provider_envelope_sha256": envelope_sha,
            "provider_artifacts": {
                "payload_path": str(payload_path),
                "envelope_path": str(envelope_path),
                "arm_binding_digest_sha256": report["arm_execution"][
                    "arm_binding_digest_sha256"
                ],
            },
            "provenance": {
                "payload_sha256": payload_sha,
                "envelope_sha256": envelope_sha,
            },
        }
        if event["role"] in {"planner", "coder"}:
            spec_key = (
                "planner-generation-1"
                if event["role"] == "planner" and event["generation"] == 1
                else "planner-generation-next"
                if event["role"] == "planner"
                else "coder"
            )
            update["payload_validation_receipt"] = _payload_validation_receipt(
                {**event, **update},
                spec_key,
                cell["descriptor"],
                arm=trial.arm,
                content_digest=event["descriptor_sha256"],
            )
        event.update(copy.deepcopy(update))
        for generation in cell["generations"]:
            for role_event in generation["roles"].values():
                if role_event["invocation_id"] == event["invocation_id"]:
                    role_event.update(copy.deepcopy(update))
    return _persist(run_root, events, report)


def _registered_layer3_report_path(report_path: Path) -> Path:
    report = json.loads(report_path.read_bytes())
    return (
        Path(report["cells"][0]["campaign_root"])
        / "reports"
        / "layer3_report.json"
    )


def _assert_acceptance_receipt_absent(repo: Path) -> None:
    receipt_dir = repo / R.s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR
    assert not receipt_dir.exists() or not any(receipt_dir.iterdir())


def _partial_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
) -> Path:
    run = root / f"run-{trial.trial_id}"
    repository_root = root.parent
    content_commit, effective_commit = _fixture_registration_commits(
        repository_root, manifest,
    )
    start = _base_start(trial, run, measurement_head)
    report = _base_report(trial, run, measurement_head)
    for target in (start, report):
        target["prereg_commit"] = manifest.prereg_commit
        target["prereg_content_commit"] = content_commit
        target["prereg_effective_commit"] = effective_commit
        target["slot_id"] = _fixture_slot_id(trial)
        target["manifest_sha256"] = manifest.sha256
        target["arm_execution"] = _fixture_arm_execution(trial)
        target["launch_admission"] = _fixture_launch_admission(
            trial,
            manifest,
            measurement_head,
            prereg_content_commit=content_commit,
            prereg_effective_commit=effective_commit,
        )
    report["raw_output_sha256"] = _fixture_raw_output_sha256(trial)
    report["status"] = "partial"
    report["fatal_error"] = {"type": "ProviderError", "message": "init failed"}
    events = [
        start,
        {
            "event": "provider-init-error",
            "type": "ProviderError",
            "message": "init failed",
            "seq": 2,
            "ts": "2026-08-01T00:00:02+00:00",
        },
        _finish_event(run, "partial", 3, 0),
    ]
    return _persist(run, events, report)


def _campaignless_failure_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
) -> Path:
    path = _partial_report(root, trial, manifest, measurement_head)
    events, report = _load_report_bundle(path)
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    error = {"type": "RuntimeError", "message": "fixture supervisor failure"}
    failure = {
        "schema_version": (
            "p3-autonomous-workload-trial-cell-admission-failure/v1"
        ),
        "admission_status": "failed",
        "error": {
            "type": "AutonomousTrialError",
            "message": "build cell has no campaign_root for admission validation",
        },
    }
    cell = {
        "workload": workload,
        "generations": [],
        "stop_reason": "supervisor-error",
        "error": error,
        "admission_decision": failure,
        "pending_critic_disposition": {
            "schema_version": (
                "p3-autonomous-workload-trial-pending-critic-disposition/v1"
            ),
            "action": "discarded",
            "reason": "cell-admission-failure",
            "count": 0,
        },
    }
    report["do_build"] = True
    report["status"] = "partial"
    report["fatal_error"] = error
    report["cells"] = [cell]
    events[0]["do_build"] = True
    events[1] = {
        "event": "supervisor-error",
        "workload": workload,
        **error,
        "seq": 2,
        "ts": "2026-08-01T00:00:02+00:00",
    }
    events[-1]["status"] = "partial"
    events[-1]["cell_admission_failures"] = (
        completeness.cell_admission_failure_projection([cell])
    )
    return _persist(path.parent, events, report)


def _one_cell_partial_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
) -> Path:
    path = _complete_report(
        root,
        trial,
        manifest,
        measurement_head,
        generation_budget=1,
    )
    events, report = _load_report_bundle(path)
    error = {"type": "RuntimeError", "message": "supervisor failed"}
    events[0]["generation_budget_per_workload"] = trial.generations
    report["generation_budget_per_workload"] = trial.generations
    report["status"] = "partial"
    # The cell prefix is retained for diagnosis, but a partial terminal row
    # has no observed top-level projection.
    report["observation_sha256"] = None
    report["primary_value"] = None
    report["fatal_error"] = error
    report["cells"][0]["stop_reason"] = "supervisor-error"
    report["cells"][0]["error"] = error
    finish = events.pop()
    events.append({
        "event": "supervisor-error",
        "workload": report["cells"][0]["workload"],
        **error,
        "seq": finish["seq"],
        "ts": finish["ts"],
    })
    finish["status"] = "partial"
    finish["seq"] += 1
    finish["ts"] = "2026-08-01T00:01:07+00:00"
    events.append(finish)
    return _persist(path.parent, events, report)


def _reports(
    root: Path,
    manifest: R.TrialManifest,
    measurement_head: str,
    *,
    complete: bool,
) -> list[Path]:
    builder = _complete_report if complete else _partial_report
    return [builder(root, trial, manifest, measurement_head) for trial in manifest.trials]


def _load_report_bundle(path: Path) -> tuple[list[dict], dict]:
    events = [
        json.loads(line)
        for line in path.with_name("attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    report = json.loads(path.read_text(encoding="utf-8"))
    return events, report


def test_p1_exact_six_trial_manifest_passes(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    value = _manifest_value(prereg, "p1")
    value["trials"].reverse()
    _write_manifest(path, value)
    manifest = R.load_trial_manifest(path)
    assert [(trial.holdout, trial.arm) for trial in manifest.trials] == [
        (holdout, arm) for holdout in R.HOLDOUTS for arm in R.ARMS
    ]
    assert {trial.generations for trial in manifest.trials} == {2}


def test_t1185_m1_manifest_generation_one_is_rejected_at_exact_path(
    tmp_path: Path,
) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    value = _manifest_value(prereg, "m1-generation")
    value["trials"][4]["generations"] = 1
    _write_manifest(path, value)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"manifest\.trials\[4\]\.generations",
    ):
        R.load_trial_manifest(path)


def test_manifest_generations_rejects_bool_at_exact_path(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    value = _manifest_value(prereg, "bool-generation")
    value["trials"][2]["generations"] = True
    _write_manifest(path, value)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"manifest\.trials\[2\]\.generations",
    ):
        R.load_trial_manifest(path)


def test_p2_first_and_second_registration_append_pass(tmp_path: Path) -> None:
    repo, manifest_a_path, registry, _manifest_a = _registered_repo(tmp_path)
    before = registry.read_bytes()
    inode = registry.stat().st_ino
    prereg = _run(repo, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_b_path, _manifest_value(prereg, "trial-b"))
    _commit(repo, "manifest-b", manifest_b_path)
    _append_fixture_registration(
        manifest_path=manifest_b_path,
        repository_root=repo,
        registry_path=registry,
    )
    after = registry.read_bytes()
    assert registry.stat().st_ino == inode
    assert len(after) > len(before)
    assert after.startswith(before)
    assert len(R.load_trial_registry(registry)) == 2
    assert manifest_a_path.is_file()


def test_p3_each_registered_trial_resolves_launch_binding(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    for trial in manifest.trials:
        workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
        binding = R.load_launch_binding(
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[workload],
            repository_root=repo,
            registry_path=registry,
        )
        assert binding.trial_id == trial.trial_id
        assert binding.campaign_id == trial.campaign_id
        assert binding.measurement_head == _head(repo)


def test_p4_prereg_equal_to_measurement_commit_passes(tmp_path: Path) -> None:
    repo, _prereg = _init_repo(tmp_path)
    head = _head(repo)
    R.assert_prereg_ancestor(
        repo, prereg_commit=head, measurement_commit=head,
    )


def test_p5_six_complete_terminal_reports_pass_acceptance(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    reports.reverse()
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert summary.certifying is False
    assert summary.arm_binding == "execution-bound"
    assert {trial.status for trial in summary.trials} == {"complete"}
    receipt_bytes = (repo / summary.receipt_path).read_bytes()
    receipt = json.loads(receipt_bytes)
    assert receipt_bytes == _canonical(receipt) + b"\n"
    reports_by_id = {
        json.loads(path.read_bytes())["trial_id"]: path for path in reports
    }
    expected_trials = []
    for trial in sorted(manifest.trials, key=lambda item: item.trial_id):
        report_path = reports_by_id[trial.trial_id]
        report_bytes = report_path.read_bytes()
        report = json.loads(report_bytes)
        journal_path = report_path.with_name("attempts.jsonl")
        journal_bytes = journal_path.read_bytes()
        events = [json.loads(line) for line in journal_bytes.splitlines()]
        cross_binding = completeness.verify_s8c_cross_binding(
            report=report,
            events=events,
            run_root=report_path.parent,
        )
        expected_trials.append({
            "trial_id": trial.trial_id,
            "arm": trial.arm,
            "holdout": trial.holdout,
            "campaign_id": trial.campaign_id,
            "status": report["status"],
            "measurement_head": report["measurement_head"],
            "report_path": report_path.relative_to(repo).as_posix(),
            "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
            "attempt_journal_path": journal_path.relative_to(repo).as_posix(),
            "attempt_journal_sha256": hashlib.sha256(journal_bytes).hexdigest(),
            "arm_execution": report["arm_execution"],
            "cross_binding_receipt_sha256": cross_binding["receipt_sha256"],
        })
    lifecycle_bytes = (repo / R.DEFAULT_LIFECYCLE_PATH).read_bytes()
    registry_bytes = registry.read_bytes()
    attempt_registry_path = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    attempt_registry_bytes = attempt_registry_path.read_bytes()
    attempt_genesis = json.loads(attempt_registry_bytes.splitlines()[0])
    initial_slots = sorted(
        (
            slot for slot in attempt_genesis["slots"]
            if slot["attempt_index"] == 0
        ),
        key=lambda slot: slot["slot_id"],
    )
    first_report = json.loads(reports[0].read_bytes())
    expected_receipt = {
        "schema_version": "p3-8c-trial-acceptance-receipt/v5",
        "manifest_path": manifest_path.relative_to(repo).as_posix(),
        "manifest_sha256": manifest.sha256,
        "prereg_commit": manifest.prereg_commit,
        "prereg_content_commit": first_report[
            "launch_admission"
        ]["prereg_content_commit"],
        "prereg_effective_commit": first_report[
            "launch_admission"
        ]["prereg_effective_commit"],
        "activation_report_digest_sha256": first_report[
            "launch_admission"
        ]["activation_report_digest_sha256"],
        "registry_path": registry.relative_to(repo).as_posix(),
        "registry_blob_sha256": hashlib.sha256(registry_bytes).hexdigest(),
        "registry_introduction_commit": _head(repo),
        "lifecycle_path": R.DEFAULT_LIFECYCLE_PATH.as_posix(),
        "lifecycle_prefix_bytes": len(lifecycle_bytes),
        "lifecycle_prefix_sha256": hashlib.sha256(lifecycle_bytes).hexdigest(),
        "attempt_registry_path": R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "attempt_registry_prefix_bytes": len(attempt_registry_bytes),
        "attempt_registry_prefix_sha256": hashlib.sha256(
            attempt_registry_bytes
        ).hexdigest(),
        "attempt_slot_projection": {
            "prereg_generation": 13,
            "unit_count": len(initial_slots),
            "units": [
                {
                    "slot_id": slot["slot_id"],
                    "trial_id": slot["trial_id"],
                    "arm": slot["arm"],
                    "holdout": slot["holdout"],
                    "campaign_id": slot["campaign_id"],
                    "replicate_index": slot["replicate_index"],
                }
                for slot in initial_slots
            ],
        },
        "certifying": False,
        "non_certifying_reason_codes": [
            "no-build", "t468-approval-authority-absent",
        ],
        "cross_binding_receipt_sha256": (
            R.s8c_acceptance_receipt.cross_binding_aggregate_sha256([
                {
                    "trial_id": row["trial_id"],
                    "receipt_sha256": row["cross_binding_receipt_sha256"],
                }
                for row in expected_trials
            ])
        ),
        "trials": expected_trials,
    }
    # No volatile leaf is omitted: commit-dependent leaves are rederived from
    # the fixture repository and every key, leaf, and trial-array position is
    # compared.
    assert receipt == expected_receipt
    assert receipt["prereg_commit"] != receipt["prereg_content_commit"]
    assert (
        receipt["prereg_content_commit"]
        != receipt["prereg_effective_commit"]
    )
    receipt_path = repo / summary.receipt_path
    _commit(repo, "track acceptance receipt v2", receipt_path)
    verified = R.s8c_acceptance_receipt.verify_acceptance_receipt(
        receipt_path, repository_root=repo,
    )
    assert verified.receipt.non_certifying_reason_codes == (
        "no-build",
        "t468-approval-authority-absent",
    )


def test_s8c_acceptance_no_build_verifier_leaf_is_independently_recomputed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    original = completeness.verify_s8c_cross_binding
    observed: dict[str, dict] = {}

    def wrapped(**kwargs):
        leaf = original(**kwargs)
        observed[kwargs["report"]["trial_id"]] = leaf
        return leaf

    monkeypatch.setattr(R, "verify_s8c_cross_binding", wrapped)
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    receipt = json.loads((repo / summary.receipt_path).read_bytes())
    assert len(observed) == 6
    for row in receipt["trials"]:
        report_path = repo / row["report_path"]
        report = json.loads(report_path.read_bytes())
        journal_path = report_path.with_name("attempts.jsonl")
        events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
        independent = original(
            report=report, events=events, run_root=report_path.parent,
        )
        assert row["cross_binding_receipt_sha256"] == independent["receipt_sha256"]
        assert observed[row["trial_id"]]["receipt_sha256"] == independent[
            "receipt_sha256"
        ]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    observed_workloads = {}
    observed_ccbench_commits = set()
    observed_env_tags = set()
    for report_path in reports:
        report = json.loads(report_path.read_bytes())
        observed_workloads[report["trial_id"]] = report["cells"][0]["workload"]
        layer3 = json.loads(_registered_layer3_report_path(report_path).read_bytes())
        observed_ccbench_commits.add(layer3["meta"]["ccbench_commit"])
        observed_env_tags.add(tuple(layer3["env_tags"]))
    expected_workloads = {
        trial.trial_id: R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
        for trial in manifest.trials
    }
    assert observed_workloads == expected_workloads
    assert observed_ccbench_commits == {completeness._CURRENT_CCBENCH_PIN}
    assert observed_env_tags == {("linux-baremetal",)}

    real_chain = completeness.assert_campaign_layer3_chain
    real_fresh = completeness._fresh_layer3_for_comparison
    observed_chain_trial_ids: list[str] = []
    observed_fresh_campaign_roots: list[Path] = []

    def wrapped_chain(**kwargs):
        result = real_chain(**kwargs)
        observed_chain_trial_ids.append(kwargs["report"]["trial_id"])
        return result

    def wrapped_fresh(**kwargs):
        result = real_fresh(**kwargs)
        observed_fresh_campaign_roots.append(kwargs["campaign_root"])
        return result

    monkeypatch.setattr(R, "assert_campaign_layer3_chain", wrapped_chain)
    monkeypatch.setattr(
        completeness, "_fresh_layer3_for_comparison", wrapped_fresh,
    )
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert len(summary.trials) == len(manifest.trials) == 6
    receipt_bytes = (repo / summary.receipt_path).read_bytes()
    receipt = json.loads(receipt_bytes)
    assert receipt_bytes == _canonical(receipt) + b"\n"
    assert summary.receipt_sha256 == hashlib.sha256(receipt_bytes).hexdigest()
    assert set(receipt) == R.s8c_acceptance_receipt._TOP_LEVEL_KEYS
    assert len(receipt["trials"]) == 6
    assert all(
        set(row) == R.s8c_acceptance_receipt._V3_TRIAL_KEYS
        for row in receipt["trials"]
    )
    assert {
        row["trial_id"] for row in receipt["trials"]
    } == {trial.trial_id for trial in manifest.trials}
    assert len(observed_chain_trial_ids) == 6
    assert observed_chain_trial_ids == [
        trial.trial_id for trial in manifest.trials
    ]
    expected_campaign_roots = {
        Path(json.loads(report_path.read_bytes())["cells"][0]["campaign_root"])
        for report_path in reports
    }
    assert len(observed_fresh_campaign_roots) == 6
    assert set(observed_fresh_campaign_roots) == expected_campaign_roots
    receipt_path = repo / summary.receipt_path
    _commit(repo, "track materialized build acceptance receipt", receipt_path)
    verified = R.s8c_acceptance_receipt.verify_acceptance_receipt(
        receipt_path, repository_root=repo,
    )
    assert verified.sha256 == summary.receipt_sha256


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_t822_acceptance_rejects_one_layer3_ccbench_commit_mismatch(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    layer3_path = _registered_layer3_report_path(reports[0])
    baseline_trial_id = json.loads(reports[0].read_bytes())["trial_id"]
    differing_trial_id = json.loads(reports[1].read_bytes())["trial_id"]
    differing_path = _registered_layer3_report_path(reports[1])
    layer3 = json.loads(layer3_path.read_bytes())
    layer3["meta"]["ccbench_commit"] = "different-ccbench-commit"
    layer3_path.write_bytes(_canonical(layer3) + b"\n")

    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[measurement-target] layer3 reports do not share one "
        "meta.ccbench_commit; "
        f"baseline trial {baseline_trial_id!r} "
        f"value={'different-ccbench-commit'!r} path={str(layer3_path)!r}; "
        f"differing trial {differing_trial_id!r} "
        f"value={completeness._CURRENT_CCBENCH_PIN!r} "
        f"path={str(differing_path)!r}"
    )
    _assert_acceptance_receipt_absent(repo)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_t822_acceptance_rejects_one_layer3_env_tag_mismatch(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    layer3_path = _registered_layer3_report_path(reports[0])
    baseline_trial_id = json.loads(reports[0].read_bytes())["trial_id"]
    differing_trial_id = json.loads(reports[1].read_bytes())["trial_id"]
    differing_path = _registered_layer3_report_path(reports[1])
    layer3 = json.loads(layer3_path.read_bytes())
    layer3["env_tags"] = ["different-environment"]
    layer3_path.write_bytes(_canonical(layer3) + b"\n")

    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[measurement-target] layer3 reports do not share one env_tag; "
        f"baseline trial {baseline_trial_id!r} "
        f"value={'different-environment'!r} path={str(layer3_path)!r}; "
        f"differing trial {differing_trial_id!r} "
        f"value={'linux-baremetal'!r} path={str(differing_path)!r}"
    )
    _assert_acceptance_receipt_absent(repo)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_t822_acceptance_rejects_missing_layer3_in_complete_build_bundle(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    missing_path = _registered_layer3_report_path(reports[0])
    missing_trial_id = json.loads(reports[0].read_bytes())["trial_id"]
    reference_trial_id = json.loads(reports[1].read_bytes())["trial_id"]
    missing_path.unlink()

    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[measurement-target] complete build bundle requires exactly 6 "
        f"readable layer3 reports; found 5; reference trial {reference_trial_id!r}; "
        f"missing=[trial {missing_trial_id!r} value=<missing> "
        f"path={str(missing_path)!r}]"
    )
    _assert_acceptance_receipt_absent(repo)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_t822_acceptance_rejects_zero_layer3_reports_in_complete_build_bundle(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    missing = [
        (
            json.loads(report_path.read_bytes())["trial_id"],
            _registered_layer3_report_path(report_path),
        )
        for report_path in reports
    ]
    for _trial_id, layer3_path in missing:
        layer3_path.unlink()
    missing_detail = ", ".join(
        f"trial {trial_id!r} value=<missing> path={str(path)!r}"
        for trial_id, path in missing
    )

    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[measurement-target] complete build bundle requires exactly 6 "
        f"readable layer3 reports; found 0; reference trial {missing[0][0]!r}; "
        f"missing=[{missing_detail}]"
    )
    _assert_acceptance_receipt_absent(repo)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_t822_acceptance_strictly_rejects_duplicate_layer3_json_key(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    layer3_path = _registered_layer3_report_path(reports[0])
    layer3 = json.loads(layer3_path.read_bytes())
    duplicate_meta_members = []
    for key, value in sorted(layer3["meta"].items()):
        member = _canonical(key) + b":" + _canonical(value)
        duplicate_meta_members.append(member)
        if key == "ccbench_commit":
            duplicate_meta_members.append(member)
    duplicate_meta = b"{" + b",".join(duplicate_meta_members) + b"}"
    layer3_members = [
        _canonical(key)
        + b":"
        + (duplicate_meta if key == "meta" else _canonical(value))
        for key, value in sorted(layer3.items())
    ]
    layer3_path.write_bytes(b"{" + b",".join(layer3_members) + b"}\n")

    written_objects = []

    def capture_object_pairs(pairs):
        written_objects.append(pairs)
        return dict(pairs)

    written_bytes = layer3_path.read_bytes()
    json.loads(written_bytes, object_pairs_hook=capture_object_pairs)
    ccbench_counts = [
        sum(key == "ccbench_commit" for key, _value in pairs)
        for pairs in written_objects
    ]
    assert [count for count in ccbench_counts if count > 1] == [2]

    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == "[json] duplicate object key: 'ccbench_commit'"
    _assert_acceptance_receipt_absent(repo)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_t822_acceptance_reports_changed_layer3_snapshot_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    baseline_trial_id = json.loads(reports[0].read_bytes())["trial_id"]
    baseline_path = _registered_layer3_report_path(reports[0])
    baseline_bytes = baseline_path.read_bytes()
    changed_trial_id = json.loads(reports[1].read_bytes())["trial_id"]
    changed_path = _registered_layer3_report_path(reports[1])
    expected_bytes = changed_path.read_bytes()
    observed_bytes = expected_bytes + b" "
    original = R._receipt_lifecycle_snapshot

    def mutate_after_lifecycle_snapshot(**kwargs):
        result = original(**kwargs)
        changed_path.write_bytes(observed_bytes)
        return result

    monkeypatch.setattr(
        R,
        "_receipt_lifecycle_snapshot",
        mutate_after_lifecycle_snapshot,
    )

    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[measurement-target-snapshot] layer3 report changed during acceptance; "
        f"baseline trial {baseline_trial_id!r} "
        f"sha256={hashlib.sha256(baseline_bytes).hexdigest()} "
        f"path={str(baseline_path)!r}; differing trial {changed_trial_id!r} "
        f"expected_sha256={hashlib.sha256(expected_bytes).hexdigest()} "
        f"observed_sha256={hashlib.sha256(observed_bytes).hexdigest()} "
        f"path={str(changed_path)!r}"
    )
    _assert_acceptance_receipt_absent(repo)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (
            "ccbench-type",
            "[measurement-target] trial 'trial-0' layer3 "
            "meta.ccbench_commit is not a non-empty string",
        ),
        (
            "env-tags-type",
            "[measurement-target] trial 'trial-0' layer3 "
            "env_tags is not a list",
        ),
        (
            "env-tags-cardinality",
            "[measurement-target] trial 'trial-0' layer3 env_tags must "
            "contain exactly one non-empty string",
        ),
    ),
)
def test_t822_measurement_target_field_types_are_strict(
    tmp_path: Path,
    mutation: str,
    expected: str,
) -> None:
    loaded = []
    for index in range(6):
        campaign_root = tmp_path / f"campaign-{index}"
        layer3_path = campaign_root / "reports" / "layer3_report.json"
        layer3_path.parent.mkdir(parents=True)
        layer3 = {
            "meta": {"ccbench_commit": "same-ccbench-commit"},
            "env_tags": ["linux-baremetal"],
        }
        if index == 0 and mutation == "ccbench-type":
            layer3["meta"]["ccbench_commit"] = 1
        elif index == 0 and mutation == "env-tags-type":
            layer3["env_tags"] = "linux-baremetal"
        elif index == 0 and mutation == "env-tags-cardinality":
            layer3["env_tags"] = []
        layer3_path.write_bytes(_canonical(layer3) + b"\n")
        loaded.append(
            SimpleNamespace(
                report={
                    "trial_id": f"trial-{index}",
                    "do_build": True,
                    "cells": [{"campaign_root": str(campaign_root)}],
                },
                journal_path=tmp_path / f"run-{index}" / "attempts.jsonl",
            )
        )

    with pytest.raises(R.TrialRegistryError) as exc_info:
        R._read_acceptance_measurement_targets(loaded)
    assert str(exc_info.value) == expected


def test_t822_trial_registry_test_top_level_function_names_are_unique() -> None:
    tree = ast.parse(
        Path(__file__).read_text(encoding="utf-8"),
        filename=__file__,
    )
    names = [
        statement.name
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    assert duplicates == []


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_s8c_acceptance_registered_build_reports_remain_fail_closed_for_unknown_workload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """producer が特定 workload の対応を打ち切った場合、Layer 3 gate で fail-closed にする。"""
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    rejected_workload = R.HOLDOUT_BINDINGS[manifest.trials[0].holdout]["workload"]
    original_resolve = producer.resolve_workload_entry

    def reject_one_workload(workload):
        if workload == rejected_workload:
            raise producer.AutonomousTrialError(
                f"deliberately unsupported for test: {workload!r}"
            )
        return original_resolve(workload)

    report = json.loads(reports[0].read_bytes())
    output_root = Path(report["cells"][0]["campaign_root"]).parent.parent
    monkeypatch.setattr(producer, "resolve_workload_entry", reject_one_workload)
    with pytest.raises(completeness.AutonomousTrialCompletenessError) as exc_info:
        completeness.assert_campaign_layer3_chain(
            report=report,
            output_root=output_root,
        )
    assert str(exc_info.value) == (
        "[campaign-chain] "
        "cells[0].workload is not producer-supported"
    )
    with pytest.raises(R.TrialRegistryError) as acceptance_exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert type(acceptance_exc_info.value) is R.TrialRegistryError
    receipt_dir = repo / R.s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR
    assert not receipt_dir.exists() or not any(receipt_dir.iterdir())


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_s8c_acceptance_does_not_swallow_unexpected_workload_resolver_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _manifest_path, _registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    report_path = _prepare_registered_build_report(
        build_root,
        manifest.trials[0],
        manifest,
        _head(repo),
        repository_root=repo,
    )
    report = json.loads(report_path.read_bytes())
    output_root = Path(report["cells"][0]["campaign_root"]).parent.parent

    def raise_unexpected_resolver_error(_workload: str):
        raise RuntimeError("unexpected workload resolver failure")

    monkeypatch.setattr(
        producer, "resolve_workload_entry", raise_unexpected_resolver_error,
    )
    with pytest.raises(
        RuntimeError, match="unexpected workload resolver failure",
    ) as exc_info:
        completeness.assert_campaign_layer3_chain(
            report=report,
            output_root=output_root,
        )
    assert type(exc_info.value) is RuntimeError
    assert not isinstance(
        exc_info.value, completeness.AutonomousTrialCompletenessError,
    )


def test_s8c_acceptance_build_with_empty_cells_fails_closed_before_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    first = reports[0]
    events, report = _load_report_bundle(first)
    report["do_build"] = True
    events[0]["do_build"] = True
    _persist(first.parent, events, report)
    monkeypatch.setattr(
        R,
        "verify_s8c_cross_binding",
        lambda **_: {"receipt_sha256": "a" * 64},
    )
    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[campaign-chain] do_build=True requires a non-empty report.cells list"
    )
    receipt_dir = repo / R.s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR
    assert not receipt_dir.exists() or not any(receipt_dir.iterdir())


def test_s8c_acceptance_rejects_campaignless_failure_layer3_bypass_after_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    reports[0] = _campaignless_failure_report(
        repo / "reports-failure", manifest.trials[0], manifest, _head(repo),
    )
    real_chain = completeness.assert_campaign_layer3_chain
    observed_chain_trial_ids: list[str] = []

    def wrapped_chain(**kwargs):
        result = real_chain(**kwargs)
        observed_chain_trial_ids.append(kwargs["report"]["trial_id"])
        return result

    monkeypatch.setattr(R, "assert_campaign_layer3_chain", wrapped_chain)
    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[campaign-chain] campaignless failure fallback bypassed Layer-3 "
        "validation for cells [0]"
    )
    assert observed_chain_trial_ids == [manifest.trials[0].trial_id]
    _assert_acceptance_receipt_absent(repo)


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_s8c_acceptance_rejects_campaign_from_different_output_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    build_root = repo / "output" / "exploration" / "autonomous-trials"
    reports = [
        _prepare_registered_build_report(
            build_root,
            trial,
            manifest,
            _head(repo),
            repository_root=repo,
        )
        for trial in manifest.trials
    ]
    first = reports[0]
    events, report = _load_report_bundle(first)
    original_campaign = Path(report["cells"][0]["campaign_root"])
    alternate_campaign = repo / "output" / "alternate" / "campaigns" / original_campaign.name
    alternate_campaign.parent.mkdir(parents=True, exist_ok=True)
    original_campaign.rename(alternate_campaign)
    report["cells"][0]["campaign_root"] = str(alternate_campaign)
    _persist(first.parent, events, report)

    monkeypatch.setattr(R, "assert_execution_digest_chain", lambda **_: None)
    monkeypatch.setattr(R, "assert_campaign_layer3_chain", lambda **_: None)
    monkeypatch.setattr(
        R,
        "verify_s8c_cross_binding",
        lambda **_: {"receipt_sha256": "a" * 64},
    )
    with pytest.raises(R.TrialRegistryError) as exc_info:
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert str(exc_info.value) == (
        "[campaign-chain] campaign output root differs from report run root"
    )


def test_t822_acceptance_allows_coherent_past_measurement_head(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement_head = _head(repo)
    later = repo / "later.txt"
    later.write_text("later\n", encoding="utf-8")
    assert _commit(repo, "later unrelated commit", later) != measurement_head
    reports = _reports(
        repo / "reports", manifest, measurement_head, complete=True,
    )

    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )

    assert {trial.measurement_head for trial in summary.trials} == {
        measurement_head
    }


def test_t822_acceptance_rejects_mixed_measurement_heads(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    first_head = _head(repo)
    later = repo / "later.txt"
    later.write_text("later\n", encoding="utf-8")
    second_head = _commit(repo, "later unrelated commit", later)
    assert first_head != second_head
    reports = [
        _complete_report(
            repo / "reports",
            trial,
            manifest,
            first_head if index < 3 else second_head,
        )
        for index, trial in enumerate(manifest.trials)
    ]

    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[measurement-head-coherence\] "
            r"reports do not share one measurement_head$"
        ),
    ):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_t1185_pa_all_six_generation_two_reports_pass_acceptance(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    for path in reports:
        report = json.loads(path.read_bytes())
        assert report["generation_budget_per_workload"] == 2
        assert len(report["cells"]) == 1
        assert len(report["cells"][0]["generations"]) == 2
        assert report["cells"][0]["stop_reason"] == "fixed-generation-budget"
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert {trial.status for trial in summary.trials} == {"complete"}


def test_t1185_m3_m4_acceptance_checks_last_report_generation_budget(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    reports = [
        _complete_report(
            repo / "reports",
            trial,
            manifest,
            measurement,
            generation_budget=(1 if index == len(manifest.trials) - 1 else 2),
        )
        for index, trial in enumerate(manifest.trials)
    ]
    last_report = json.loads(reports[-1].read_bytes())
    assert last_report["generation_budget_per_workload"] == 1
    assert len(last_report["cells"][0]["generations"]) == 1
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[generation-binding\].*generation_budget_per_workload",
    ):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


@pytest.mark.parametrize("rejected", [True, False])
def test_acceptance_projects_identical_terminal_bytes_in_all_json_boundaries(
    tmp_path: Path,
    rejected: bool,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    manifest_by_id = {trial.trial_id: trial for trial in manifest.trials}
    expected_by_id: dict[str, dict] = {}
    for report_path in reports:
        events, report = _load_report_bundle(report_path)
        trial = manifest_by_id[report["trial_id"]]
        binding_record = _fixture_origin_binding(trial, report["measurement_head"])
        for target in (events[0], report):
            target["launch_admission"]["origin_binding"] = copy.deepcopy(
                binding_record
            )
        projection = formal.origin_terminal_projection_record(
            _origin_terminal_projection(
                rejected=rejected,
                origin_binding_record=binding_record,
                arm_binding_digest_sha256=_fixture_arm_execution(trial)[
                    "arm_binding_digest_sha256"
                ],
            )
        )
        report.update(copy.deepcopy(projection))
        expected_by_id[trial.trial_id] = projection
        _persist(report_path.parent, events, report)

    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    receipt_bytes = (repo / summary.receipt_path).read_bytes()
    receipt = json.loads(receipt_bytes)
    parsed_receipt = R.s8c_acceptance_receipt.parse_acceptance_receipt_bytes(
        receipt_bytes
    )
    assert parsed_receipt.schema_version == R.s8c_acceptance_receipt.SCHEMA_VERSION
    lifecycle = [
        json.loads(line)
        for line in (repo / R.DEFAULT_LIFECYCLE_PATH).read_bytes().splitlines()
    ]
    terminals = {
        row["trial_id"]: row for row in lifecycle if row["event"] == "terminal"
    }
    parsed_trials = {trial.trial_id: trial for trial in parsed_receipt.trials}
    for receipt_trial in receipt["trials"]:
        trial_id = receipt_trial["trial_id"]
        expected = expected_by_id[trial_id]
        expected_bytes = _canonical(expected)
        assert _canonical({
            "origin_terminal_projection": terminals[trial_id][
                "origin_terminal_projection"
            ],
        }) == expected_bytes
        assert _canonical({
            "origin_terminal_projection": receipt_trial[
                "origin_terminal_projection"
            ],
        }) == expected_bytes
        assert parsed_trials[trial_id].origin_terminal_projection == (
            receipt_trial["origin_terminal_projection"]
        )
        if rejected:
            assert receipt_trial["origin_terminal_projection"][
                "formal_receipt_sha256"
            ] is None
            assert receipt_trial["origin_terminal_projection"][
                "evidence_root_sha256"
            ] is None


@pytest.mark.parametrize("report_has_origin_binding", [True, False])
def test_acceptance_lifecycle_requires_origin_binding_and_run_plan_digest_iff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    report_has_origin_binding: bool,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    trial = manifest.trials[0]
    binding_record = _fixture_origin_binding(trial, _head(repo))
    projection = formal.origin_terminal_projection_record(
        _origin_terminal_projection(
            rejected=True,
            origin_binding_record=binding_record,
            arm_binding_digest_sha256=_fixture_arm_execution(trial)[
                "arm_binding_digest_sha256"
            ],
        )
    )
    if report_has_origin_binding:
        events, report = _load_report_bundle(reports[0])
        for target in (events[0], report):
            target["launch_admission"]["origin_binding"] = copy.deepcopy(
                binding_record
            )
        report.update(copy.deepcopy(projection))
        _persist(reports[0].parent, events, report)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    rows = [json.loads(line) for line in lifecycle.read_bytes().splitlines()]
    start = next(
        row for row in rows
        if row["event"] == "start" and row["trial_id"] == trial.trial_id
    )
    terminal = next(
        row for row in rows
        if row["event"] == "terminal" and row["trial_id"] == trial.trial_id
    )
    if report_has_origin_binding:
        start.pop("origin_run_plan_sha256")
        terminal.pop("origin_terminal_projection")
    else:
        start["origin_run_plan_sha256"] = "e" * 64
        terminal.update(copy.deepcopy(projection))
    lifecycle.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))

    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[acceptance-lifecycle\] trial .* launch origin binding and "
            r"lifecycle run-plan digest presence differ$"
        ),
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )


@pytest.mark.parametrize("mutation", ["missing-report", "run-start-mismatch"])
def test_acceptance_independently_requires_exact_rederived_launch_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    events, report = _load_report_bundle(reports[0])
    if mutation == "missing-report":
        report.pop("launch_admission")
    else:
        events[0]["launch_admission"] = copy.deepcopy(
            events[0]["launch_admission"]
        )
        events[0]["launch_admission"]["trial_id"] = "foreign-trial"
    _persist(reports[0].parent, events, report)
    monkeypatch.setattr(
        R,
        "assert_autonomous_trial_completeness",
        lambda **_kwargs: None,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[acceptance-launch-admission\] ",
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )


@pytest.mark.parametrize("mutation", ["missing", "wrong-digest"])
def test_acceptance_independently_rederives_historical_arm_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    capability = _effective_capability(manifest, monkeypatch)
    events, report = _load_report_bundle(reports[0])
    if mutation == "missing":
        report.pop("arm_execution")
        events[0].pop("arm_execution")
        expected = (
            "report and run-start arm_execution must exist and match exactly"
        )
    else:
        report["arm_execution"]["arm_binding_digest_sha256"] = "f" * 64
        events[0]["arm_execution"] = copy.deepcopy(report["arm_execution"])
        expected = "arm_execution differs from historical input derivation"
    _persist(reports[0].parent, events, report)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    monkeypatch.setattr(
        R,
        "assert_autonomous_trial_completeness",
        lambda **_kwargs: None,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=rf"\[acceptance-arm-execution\] {expected}",
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )


def test_acceptance_rejects_cell_descriptor_that_differs_from_arm_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    capability = _effective_capability(manifest, monkeypatch)
    events, report = _load_report_bundle(reports[0])
    report["cells"][0]["descriptor"]["read_write"]["read_ratio_percent"] = 79
    _persist(reports[0].parent, events, report)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    monkeypatch.setattr(
        R,
        "assert_autonomous_trial_completeness",
        lambda **_kwargs: None,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[acceptance-arm-execution\] cell descriptor differs",
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )


def test_acceptance_registered_run_rejects_one_missing_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    capability = _effective_capability(manifest, monkeypatch)
    events, report = _load_report_bundle(reports[0])
    report["cells"][0]["descriptor_binding"].pop(
        "arm_binding_digest_sha256"
    )
    _persist(reports[0].parent, events, report)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[terminal-completeness\] \[arm-digest-chain\] "
            r"descriptor binding digest differs$"
        ),
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )


def test_acceptance_runs_digest_chain_once_per_registered_trial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    calls: list[str] = []
    original = R.assert_execution_digest_chain

    def record_digest_chain(**kwargs) -> None:
        calls.append(kwargs["report"]["trial_id"])
        original(**kwargs)

    monkeypatch.setattr(
        R, "assert_execution_digest_chain", record_digest_chain,
    )
    R.assert_trial_registry_acceptance(
        effective_preregistration=capability,
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
    )
    assert calls == [trial.trial_id for trial in manifest.trials]


@pytest.mark.parametrize("origin_binding_record", [None, {"unexpected": True}])
def test_acceptance_rejects_null_or_open_origin_binding_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    origin_binding_record: object,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    capability = _effective_capability(manifest, monkeypatch)
    events, report = _load_report_bundle(reports[0])
    for target in (events[0], report):
        target["launch_admission"]["origin_binding"] = copy.deepcopy(
            origin_binding_record
        )
    _persist(reports[0].parent, events, report)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    monkeypatch.setattr(R, "assert_autonomous_trial_completeness", lambda **_kw: None)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[acceptance-launch-admission\] ",
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )


@pytest.mark.parametrize(
    ("field", "forged_value"),
    [
        ("manifest_sha256", "0" * 64),
        ("arm", "forged-arm"),
        ("campaign_id", "forged-campaign"),
        ("holdout", "forged-holdout"),
        ("measurement_head", "0" * 40),
    ],
)
def test_acceptance_rederives_each_self_consistent_launch_binding_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    forged_value: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    report_path = reports[0]
    events, report = _load_report_bundle(report_path)
    forged_admission = copy.deepcopy(report["launch_admission"])
    forged_admission["binding"][field] = forged_value
    report["launch_admission"] = copy.deepcopy(forged_admission)
    events[0]["launch_admission"] = copy.deepcopy(forged_admission)
    _persist(report_path.parent, events, report)

    rows = [json.loads(line) for line in lifecycle.read_text().splitlines()]
    trial_id = report["trial_id"]
    start = next(
        row for row in rows
        if row["event"] == "start" and row["trial_id"] == trial_id
    )
    terminal = next(
        row for row in rows
        if row["event"] == "terminal" and row["trial_id"] == trial_id
    )
    start["launch_admission_sha256"] = hashlib.sha256(
        _canonical(forged_admission)
    ).hexdigest()
    terminal["report_sha256"] = hashlib.sha256(report_path.read_bytes()).hexdigest()
    terminal["attempt_journal_sha256"] = hashlib.sha256(
        report_path.with_name("attempts.jsonl").read_bytes()
    ).hexdigest()
    lifecycle.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))

    completeness_bypasses: list[None] = []
    monkeypatch.setattr(
        R,
        "assert_autonomous_trial_completeness",
        lambda **_kwargs: completeness_bypasses.append(None),
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[acceptance-launch-admission\] launch_admission differs from "
            r"the accepted binding derivation$"
        ),
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )
    assert completeness_bypasses == [None]


def test_p6_partial_terminal_outcomes_are_reported_not_dropped(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    reports = [
        (_complete_report if index == 0 else _partial_report)(
            repo / "reports", trial, manifest, measurement,
        )
        for index, trial in enumerate(manifest.trials)
    ]
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert [trial.status for trial in summary.trials].count("partial") == 5


def test_p6_one_cell_partial_terminal_outcome_passes_acceptance(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    reports = [
        (_one_cell_partial_report if index == 0 else _partial_report)(
            repo / "reports", trial, manifest, measurement,
        )
        for index, trial in enumerate(manifest.trials)
    ]
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert [trial.status for trial in summary.trials].count("partial") == 6
    receipt_value = json.loads((repo / summary.receipt_path).read_bytes())
    assert receipt_value["non_certifying_reason_codes"] == [
        "c02-arm-binding-unproven",
        "no-build",
        "t468-approval-authority-absent",
    ]
    parsed = R.s8c_acceptance_receipt.parse_acceptance_receipt_bytes(
        (repo / summary.receipt_path).read_bytes()
    )
    assert parsed.schema_version == R.s8c_acceptance_receipt.SCHEMA_VERSION


def test_p6_indeterminate_not_consumed_partial_fails_formal_acceptance(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    reports = [
        _partial_report(repo / "reports", trial, manifest, measurement)
        for trial in manifest.trials
    ]

    target_path = reports[0]
    events, report = _load_report_bundle(target_path)
    report["lifecycle_terminal_status"] = "indeterminate"
    assert report["status"] == "partial"
    assert report["lifecycle_terminal_status"] == "indeterminate"
    _persist(target_path.parent, events, report)
    _ensure_fixture_attempt_rows(repo, manifest, reports)

    with pytest.raises(R.TrialRegistryError, match=r"\[attempt-terminal\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_t1185_pb_partial_one_generation_with_budget_two_passes_acceptance(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    reports = [
        (_one_cell_partial_report if index == len(manifest.trials) - 1
         else _complete_report)(
            repo / "reports", trial, manifest, measurement,
        )
        for index, trial in enumerate(manifest.trials)
    ]
    partial = json.loads(reports[-1].read_bytes())
    assert partial["generation_budget_per_workload"] == 2
    assert len(partial["cells"][0]["generations"]) == 1
    assert partial["cells"][0]["stop_reason"] == "supervisor-error"
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert [trial.status for trial in summary.trials].count("partial") == 1


def test_p7_later_registry_rows_do_not_hide_older_manifest(tmp_path: Path) -> None:
    repo, manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    prereg = manifest_a.prereg_commit
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_b_path, _manifest_value(prereg, "trial-b"))
    _commit(repo, "manifest-b", manifest_b_path)
    _append_fixture_registration(
        manifest_path=manifest_b_path, repository_root=repo, registry_path=registry,
    )
    _commit(repo, "registry-b", registry)
    reports = _reports(repo / "reports", manifest_a, _head(repo), complete=False)
    summary = _accept(
        manifest_path=manifest_a_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert summary.manifest_sha256 == manifest_a.sha256


def test_p9_prime_existing_registry_unregistered_exploratory_id_passes(
    tmp_path: Path,
) -> None:
    repo, _manifest_path, registry, _manifest = _registered_repo(tmp_path)
    admission = R.admit_unregistered_exploratory(
        trial_id="fresh-exploratory",
        workloads=["ycsb-a"],
        allow_unregistered_exploratory=True,
        repository_root=repo,
        registry_path=registry,
    )
    assert admission.certifying is False


def _effective_capability(
    manifest: R.TrialManifest,
    monkeypatch: pytest.MonkeyPatch,
):
    module = R.s8c_preregistration
    report = _effective_report(manifest)
    capability = module._construct_effective(report)
    monkeypatch.setattr(
        module,
        "activation_report_at",
        lambda repo_root, commit: report,
    )
    return capability


def _effective_report(manifest: R.TrialManifest):
    module = R.s8c_preregistration
    return module.ActivationReport(
        commit=manifest.prereg_commit,
        condition_freeze_valid=True,
        freeze_generation=1,
        protected_sha256="1" * 64,
        freeze_reason_code="valid",
        decider_version=module.DECIDER_VERSION,
        decider_version_matches=True,
        decider_version_reason_code="decider-version-match",
        section5_findings=(),
        predicates=(),
        core_module_blob_sha256="2" * 64,
        evaluator_module_blob_sha256="3" * 64,
        projection_module_blob_sha256="4" * 64,
        effective=True,
    )


def _ensure_fixture_attempt_rows(
    repo: Path,
    manifest: R.TrialManifest,
    reports: list[Path],
) -> None:
    attempt_registry = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    rows = list(R.load_attempt_registry(repo, registry_path=attempt_registry))
    terminal_by_slot = {
        row["slot_id"]: row
        for row in rows
        if row.get("event") == "terminal"
    }
    genesis = rows[0]
    slots_by_trial = {
        slot["trial_id"]: slot
        for slot in genesis["slots"]
        if slot["attempt_index"] == 0
    }
    content_commit, effective_commit = _fixture_registration_commits(
        repo, manifest,
    )
    for report_path in reports:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        trial = next(
            (
                item for item in manifest.trials
                if item.trial_id == report.get("trial_id")
            ),
            None,
        )
        if trial is None:
            continue
        slot = slots_by_trial[trial.trial_id]
        if slot["slot_id"] in terminal_by_slot:
            continue
        capability = _reserve_attempt(
            repo,
            attempt_registry,
            content_commit,
            effective_commit,
            genesis["freeze_id"],
            slot,
            run_start_receipt_sha256=hashlib.sha256(
                _canonical(report["launch_admission"])
            ).hexdigest(),
        )
        indeterminate = (
            report.get("lifecycle_terminal_status") == "indeterminate"
        )
        observed = report["status"] == "complete"
        failure_reason = (
            None if observed or indeterminate else "provider-failure"
        )
        R.classify_attempt(
            capability,
            pre_observation_failure_reason=failure_reason,
            authority_id="fixture-authority",
            authority_policy_sha256="a" * 64,
            external_evidence_sha256="b" * 64,
            classified_at="2026-08-18T00:00:01+00:00",
        )
        if observed or report_path.is_file():
            R.begin_attempt_observation(capability)
        R.record_attempt_terminal(
            capability,
            terminal_status=(
                "not-consumed"
                if indeterminate
                else "observed" if observed else "terminal-failure"
            ),
            raw_output_sha256=report["raw_output_sha256"],
            report_sha256=(
                None
                if indeterminate
                else hashlib.sha256(report_path.read_bytes()).hexdigest()
            ),
            observation_sha256=(
                None
                if indeterminate
                else report["observation_sha256"] if observed else None
            ),
            primary_value=(
                None
                if indeterminate
                else report["primary_value"] if observed else None
            ),
            finished_at="2026-08-18T00:00:02+00:00",
        )
        terminal_by_slot[slot["slot_id"]] = {"slot_id": slot["slot_id"]}


def _write_acceptance_lifecycle(
    repo: Path,
    manifest: R.TrialManifest,
    reports: list[Path],
    activation_digest: str,
    *,
    omit_terminal_trial_id: str | None = None,
) -> Path:
    _ensure_fixture_attempt_rows(repo, manifest, reports)
    attempt_rows = R.load_attempt_registry(
        repo, registry_path=repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH,
    )
    attempt_starts = {
        row["slot_id"]: row
        for row in attempt_rows
        if row.get("event") == "start"
    }
    attempt_terminals = {
        row["slot_id"]: row
        for row in attempt_rows
        if row.get("event") == "terminal"
    }
    reports_by_id: dict[str, tuple[Path, dict]] = {}
    for path in reports:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        trial_id = report.get("trial_id")
        if isinstance(trial_id, str):
            reports_by_id[trial_id] = (path, report)
    rows: list[dict] = []
    for trial in manifest.trials:
        matched = reports_by_id.get(trial.trial_id)
        content_commit, effective_commit = _fixture_registration_commits(
            repo, manifest,
        )
        if matched is None:
            measurement_head = _head(repo)
            path = repo / "absent-report.json"
            report = {
                "measurement_head": measurement_head,
                "status": "partial",
                "launch_admission": _fixture_launch_admission(
                    trial,
                    manifest,
                    measurement_head,
                    prereg_content_commit=content_commit,
                    prereg_effective_commit=effective_commit,
                ),
            }
        else:
            path, report = matched
        slot_id = report.get("slot_id", _fixture_slot_id(trial))
        attempt_start = attempt_starts.get(slot_id)
        attempt_terminal = attempt_terminals.get(slot_id)
        start = {
            "schema_version": R.LIFECYCLE_SCHEMA_VERSION,
            "event": "start",
            "trial_id": trial.trial_id,
            "run_root": str(path.parent.resolve()),
            "mode": "registered-effective",
            "manifest_sha256": manifest.sha256,
            "prereg_commit": manifest.prereg_commit,
            "prereg_content_commit": content_commit,
            "prereg_effective_commit": report.get(
                "prereg_effective_commit", effective_commit
            ),
            "measurement_head": report["measurement_head"],
            "activation_report_digest_sha256": activation_digest,
            "launch_admission_sha256": hashlib.sha256(
                _canonical(report["launch_admission"])
            ).hexdigest(),
            "slot_id": slot_id,
            "schedule_row_sha256": (
                attempt_start["schedule_row_sha256"]
                if attempt_start is not None
                else _fixture_schedule_row_sha256(trial)
            ),
            "process_identity": copy.deepcopy(
                attempt_start["process_identity"]
                if attempt_start is not None
                else _fixture_process_identity(trial)
            ),
        }
        if "origin_binding" in report["launch_admission"]:
            start["origin_run_plan_sha256"] = "e" * 64
        rows.append(start)
        if trial.trial_id == omit_terminal_trial_id:
            continue
        journal = path.with_name("attempts.jsonl")
        terminal = {
            "schema_version": R.LIFECYCLE_SCHEMA_VERSION,
            "event": "terminal",
            "trial_id": trial.trial_id,
            "terminal_status": report["status"],
            "report_sha256": (
                hashlib.sha256(path.read_bytes()).hexdigest()
                if path.is_file() else "a" * 64
            ),
            "attempt_journal_sha256": (
                hashlib.sha256(journal.read_bytes()).hexdigest()
                if journal.is_file() else "b" * 64
            ),
            "prereg_commit": content_commit,
            "prereg_content_commit": content_commit,
            "prereg_effective_commit": report.get(
                "prereg_effective_commit", effective_commit
            ),
            "slot_id": slot_id,
            "classification_receipt_sha256": (
                attempt_terminal["classification_receipt_sha256"]
                if attempt_terminal is not None else "c" * 64
            ),
            "raw_output_sha256": (
                attempt_terminal["raw_output_sha256"]
                if attempt_terminal is not None
                else report.get("raw_output_sha256", _fixture_raw_output_sha256(trial))
            ),
        }
        if "origin_terminal_projection" in report:
            terminal["origin_terminal_projection"] = copy.deepcopy(
                report["origin_terminal_projection"]
            )
        rows.append(terminal)
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    lifecycle.parent.mkdir(parents=True, exist_ok=True)
    lifecycle.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))
    return lifecycle


def _accept(
    *,
    manifest_path: Path,
    report_paths,
    repository_root: Path,
    registry_path: Path,
    lifecycle_path: Path | None = None,
):
    manifest = R.load_trial_manifest(manifest_path)
    reports = list(report_paths)
    with pytest.MonkeyPatch.context() as monkeypatch:
        capability = _effective_capability(manifest, monkeypatch)
        lifecycle = lifecycle_path or _write_acceptance_lifecycle(
            repository_root,
            manifest,
            reports,
            capability.report_digest_sha256,
        )
        return R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repository_root,
            registry_path=registry_path,
            lifecycle_path=lifecycle,
        )


def _registered_admission(
    repo: Path,
    manifest_path: Path,
    registry: Path,
    manifest: R.TrialManifest,
    monkeypatch: pytest.MonkeyPatch,
    *,
    trial_index: int = 0,
) -> R.TrialLaunchAdmission:
    trial = manifest.trials[trial_index]
    return R.admit_registered_launch(
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )


def _lifecycle_attempt_slot(
    repo: Path,
    manifest: R.TrialManifest,
    admission: R.TrialLaunchAdmission,
    *,
    origin_binding=None,
) -> R.AttemptSlotCapability:
    content_commit, effective_commit = _fixture_registration_commits(
        repo, manifest,
    )
    attempt_registry = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    genesis = json.loads(attempt_registry.read_text(encoding="utf-8").splitlines()[0])
    slot = next(
        item for item in genesis["slots"]
        if item["trial_id"] == admission.trial_id
    )
    receipt_sha256 = hashlib.sha256(
        _canonical(R.launch_admission_record(
            admission, origin_binding=origin_binding,
        ))
    ).hexdigest()
    return _reserve_attempt(
        repo,
        attempt_registry,
        content_commit,
        effective_commit,
        genesis["freeze_id"],
        slot,
        run_start_receipt_sha256=receipt_sha256,
    )


def _finish_lifecycle_attempt(
    capability: R.AttemptSlotCapability,
    *,
    terminal_status: str,
) -> None:
    _classify_and_terminal(
        capability,
        failure_reason=None,
        terminal_status=terminal_status,
    )


def test_u4_holdout_set_is_derived_from_registry_bindings() -> None:
    assert R.HOLDOUT_WORKLOADS == frozenset({"rr80", "rr20"})
    source = Path(R.__file__).read_text(encoding="utf-8")
    definition = source.split("HOLDOUT_WORKLOADS =", 1)[1].split("\n\n", 1)[0]
    assert "WORKLOADS" not in definition


def test_manifestless_unregistered_launch_is_rejected_by_default(
    tmp_path: Path,
) -> None:
    repo, _head_commit = _init_repo(tmp_path)
    with pytest.raises(R.TrialRegistryError, match=r"\[u4-exploratory-opt-in\] "):
        R.admit_unregistered_exploratory(
            trial_id="default-denied",
            workloads=["ycsb-a"],
            allow_unregistered_exploratory=False,
            repository_root=repo,
            registry_path=repo / R.DEFAULT_REGISTRY_PATH,
        )


def test_holdout_exploratory_opt_in_is_unconditionally_rejected(
    tmp_path: Path,
) -> None:
    repo, _head_commit = _init_repo(tmp_path)
    with pytest.raises(R.TrialRegistryError, match=r"\[u4-holdout-workload\] "):
        R.admit_unregistered_exploratory(
            trial_id="holdout-denied",
            workloads=["rr80"],
            allow_unregistered_exploratory=True,
            repository_root=repo,
            registry_path=repo / R.DEFAULT_REGISTRY_PATH,
        )


def test_explicit_non_holdout_exploration_is_sealed_and_non_certifying(
    tmp_path: Path,
) -> None:
    repo, _head_commit = _init_repo(tmp_path)
    admission = R.admit_unregistered_exploratory(
        trial_id="explicit-exploration",
        workloads=["ycsb-a"],
        allow_unregistered_exploratory=True,
        repository_root=repo,
        registry_path=repo / R.DEFAULT_REGISTRY_PATH,
    )
    assert R.launch_admission_record(admission) == {
        "mode": "explicit-unregistered-exploratory",
        "certifying": False,
        "reason_code": "explicit-unregistered-exploratory",
        "trial_id": "explicit-exploration",
        "workloads": ["ycsb-a"],
        "binding": None,
        "activation_report_digest_sha256": None,
    }
    forged = dataclasses.replace(admission, _seal=object())
    with pytest.raises(R.TrialRegistryError, match=r"\[launch-admission\] "):
        R.assert_issued_trial_launch_admission(forged)


def test_originless_launch_record_and_canonical_bytes_are_exactly_unchanged(
    tmp_path: Path,
) -> None:
    repo, _head_commit = _init_repo(tmp_path)
    admission = R.admit_unregistered_exploratory(
        trial_id="explicit-exploration",
        workloads=["ycsb-a"],
        allow_unregistered_exploratory=True,
        repository_root=repo,
        registry_path=repo / R.DEFAULT_REGISTRY_PATH,
    )
    expected = {
        "mode": "explicit-unregistered-exploratory",
        "certifying": False,
        "reason_code": "explicit-unregistered-exploratory",
        "trial_id": "explicit-exploration",
        "workloads": ["ycsb-a"],
        "binding": None,
        "activation_report_digest_sha256": None,
    }
    default_record = R.launch_admission_record(admission)
    explicit_originless = R.launch_admission_record(
        admission,
        origin_binding=None,
    )
    assert default_record == expected == explicit_originless
    assert _canonical(default_record) == _canonical(expected)
    assert hashlib.sha256(_canonical(default_record)).hexdigest() == hashlib.sha256(
        _canonical(expected)
    ).hexdigest()
    assert "origin_binding" not in default_record


def test_launch_record_projects_the_same_issued_capability_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    capability = _issued_origin_binding(trial, _head(repo), monkeypatch)
    seen: list[object] = []
    original = origin_binding.origin_binding_capability_record

    def capture(value):
        seen.append(value)
        return original(value)

    monkeypatch.setattr(
        origin_binding,
        "origin_binding_capability_record",
        capture,
    )
    R.assert_rederived_launch_admission(
        admission,
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        allow_unregistered_exploratory=False,
        repository_root=repo,
        registry_path=registry,
        origin_binding=capability,
    )
    record = R.launch_admission_record(
        admission,
        origin_binding=capability,
    )
    assert seen and all(value is capability for value in seen)
    assert record["origin_binding"] == _fixture_origin_binding(trial, _head(repo))


def test_launch_record_rejects_an_issued_capability_for_another_trial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    foreign = _issued_origin_binding(manifest.trials[1], _head(repo), monkeypatch)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[launch-admission\] origin capability differs ",
    ):
        R.launch_admission_record(admission, origin_binding=foreign)


def test_registered_admission_does_not_implicitly_resolve_arm_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    monkeypatch.setattr(
        R,
        "bind_trial_arm",
        lambda *_args, **_kwargs: pytest.fail("implicit arm resolution"),
    )
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    assert admission.binding is not None


def test_bind_trial_arm_issues_exact_three_field_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    assert admission.binding is not None
    arm_execution = R.bind_trial_arm(admission.binding, repository_root=repo)
    record = R.arm_execution_record(arm_execution)
    assert set(record) == {
        "input_schema_version",
        "content_digest_sha256",
        "arm_binding_digest_sha256",
    }
    assert "arm" not in record
    assert "holdout" not in record
    R.assert_rederived_trial_arm_execution(arm_execution, repository_root=repo)
    forged = dataclasses.replace(
        arm_execution, arm_binding_digest_sha256="f" * 64,
    )
    with pytest.raises(R.TrialRegistryError, match=r"\[arm-input-resolution\] "):
        R.assert_issued_trial_arm_execution(forged)


@pytest.mark.parametrize(
    ("trial_id", "workloads", "match"),
    [
        ("INVALID", ["ycsb-a"], r"\[field\] "),
        ("duplicate-workload", ["ycsb-a", "ycsb-a"], r"\[workloads\] "),
    ],
)
def test_exploratory_admission_rejects_invalid_lexical_inputs(
    tmp_path: Path,
    trial_id: str,
    workloads: list[str],
    match: str,
) -> None:
    repo, _head_commit = _init_repo(tmp_path)
    with pytest.raises(R.TrialRegistryError, match=match):
        R.admit_unregistered_exploratory(
            trial_id=trial_id,
            workloads=workloads,
            allow_unregistered_exploratory=True,
            repository_root=repo,
            registry_path=repo / R.DEFAULT_REGISTRY_PATH,
        )


def test_exploratory_admission_rejects_invalid_repository(tmp_path: Path) -> None:
    with pytest.raises(R.TrialRegistryError, match=r"\[repo-path\] "):
        R.admit_unregistered_exploratory(
            trial_id="invalid-repository",
            workloads=["ycsb-a"],
            allow_unregistered_exploratory=True,
            repository_root=tmp_path / "missing-repository",
            registry_path=Path("registry.jsonl"),
        )


def test_admit_registered_launch_requires_manifest_commit_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    capability = _effective_capability(manifest, monkeypatch)
    wrong_report = dataclasses.replace(capability.report, commit=_head(repo))
    wrong_capability = R.s8c_preregistration._construct_effective(wrong_report)
    trial = manifest.trials[0]
    with pytest.raises(R.TrialRegistryError, match=r"\[effective-preregistration\] "):
        R.admit_registered_launch(
            effective_preregistration=wrong_capability,
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_admit_registered_formal_noncertifying_requires_explicit_opt_in(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[formal-noncertifying-opt-in\] ",
    ):
        R.admit_registered_formal_noncertifying(
            allow_formal_noncertifying=False,
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_a1_registered_noncertifying_projection_shares_load_bearing_mode() -> None:
    projection = R.issue_a1_registered_noncertifying_projection(
        study_id="paper-story-a1-20260826-sized-v1",
        policy_sha256="a" * 64,
        preregistration_sha256="b" * 64,
        source_commit="c" * 40,
        workloads=R.A1_NON_CERTIFYING_WORKLOADS,
        campaign_ids=("campaign-a", "campaign-b", "campaign-c"),
    )
    R.assert_issued_a1_registered_noncertifying_projection(projection)
    record = R.a1_registered_noncertifying_record(projection)
    assert record["mode"] == R.REGISTERED_FORMAL_NON_CERTIFYING_MODE
    assert record["certifying"] is False
    assert record["campaign_ids"] == [
        "campaign-a", "campaign-b", "campaign-c",
    ]
    forged = dataclasses.replace(projection, _seal=object())
    with pytest.raises(R.TrialRegistryError, match="not issued"):
        R.assert_issued_a1_registered_noncertifying_projection(forged)
    for changed in (
        dataclasses.replace(projection, mode="registered-effective"),
        dataclasses.replace(projection, certifying=True),
        dataclasses.replace(projection, policy_sha256="invalid"),
    ):
        with pytest.raises(R.TrialRegistryError):
            R.assert_issued_a1_registered_noncertifying_projection(changed)


def test_admit_registered_formal_noncertifying_validates_freeze_and_returns_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    freeze_calls: list[tuple[Path, str]] = []

    def observe_freeze(repo_root, commit="HEAD"):
        freeze_calls.append((Path(repo_root), commit))
        return object()

    monkeypatch.setattr(
        R.s8c_preregistration,
        "validate_condition_freeze_at",
        observe_freeze,
    )
    monkeypatch.setattr(
        R.s8c_preregistration,
        "effective_at",
        lambda *_args, **_kwargs: pytest.fail(
            "formal non-certifying admission must not compute effective_at"
        ),
    )
    admission = R.admit_registered_formal_noncertifying(
        allow_formal_noncertifying=True,
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )
    assert freeze_calls == [(repo.resolve(), manifest.prereg_commit)]
    assert admission.mode == "registered-formal-non-certifying"
    assert admission.certifying is False
    assert admission.reason_code == "registered-formal-non-certifying"
    assert admission.binding is not None
    assert admission.activation_report_digest_sha256 is None
    R.assert_issued_trial_launch_admission(admission)

    with pytest.raises(R.TrialRegistryError, match=r"activation digest"):
        R.assert_issued_trial_launch_admission(
            dataclasses.replace(admission, activation_report_digest_sha256="a" * 64)
        )


def test_admit_registered_formal_noncertifying_rejects_condition_freeze_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]

    def reject_freeze(*_args, **_kwargs):
        raise R.s8c_preregistration.PreregistrationError(
            "fixture-freeze", "condition freeze is invalid"
        )

    monkeypatch.setattr(
        R.s8c_preregistration,
        "validate_condition_freeze_at",
        reject_freeze,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[formal-noncertifying-condition-freeze\] fixture-freeze",
    ):
        R.admit_registered_formal_noncertifying(
            allow_formal_noncertifying=True,
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_rederived_launch_admission_accepts_formal_noncertifying_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    monkeypatch.setattr(
        R.s8c_preregistration,
        "validate_condition_freeze_at",
        lambda *_args, **_kwargs: object(),
    )
    admission = R.admit_registered_formal_noncertifying(
        allow_formal_noncertifying=True,
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )
    monkeypatch.setattr(
        R,
        "admit_registered_launch",
        lambda **_kwargs: pytest.fail(
            "formal non-certifying rederivation used the effective admission"
        ),
    )
    R.assert_rederived_launch_admission(
        admission,
        effective_preregistration=None,
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        allow_unregistered_exploratory=False,
        allow_formal_noncertifying=True,
        repository_root=repo,
        registry_path=registry,
    )


def test_rederived_registered_effective_still_requires_effective_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[effective-preregistration\] ",
    ):
        R.assert_rederived_launch_admission(
            admission,
            effective_preregistration=None,
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            allow_unregistered_exploratory=False,
            repository_root=repo,
            registry_path=registry,
        )


def test_formal_noncertifying_lifecycle_start_consumes_reserved_attempt_slot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    monkeypatch.setattr(
        R.s8c_preregistration,
        "validate_condition_freeze_at",
        lambda *_args, **_kwargs: object(),
    )
    admission = R.admit_registered_formal_noncertifying(
        allow_formal_noncertifying=True,
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )
    attempt_slot = _lifecycle_attempt_slot(repo, manifest, admission)
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    token = R.record_trial_start_once(
        admission=admission,
        effective_preregistration=None,
        manifest_path=manifest_path,
        run_root=repo / "formal-noncertifying-run",
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
        attempt_slot=attempt_slot,
    )
    assert token.slot_id == attempt_slot.slot_id
    row = json.loads(lifecycle.read_text(encoding="utf-8").splitlines()[0])
    assert row["mode"] == "registered-formal-non-certifying"
    assert row["activation_report_digest_sha256"] is None
    assert R._load_lifecycle_rows(lifecycle.read_bytes())[0] == row
    assert len(R._LIFECYCLE_START_BASE_KEYS) == 15
    assert R._LIFECYCLE_START_KEYS == frozenset({
        R._LIFECYCLE_START_BASE_KEYS,
        R._LIFECYCLE_START_BASE_KEYS | {"origin_run_plan_sha256"},
    })
    origin_digest_parameter = inspect.signature(
        R.record_trial_start_once
    ).parameters["origin_run_plan_sha256"]
    assert origin_digest_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert origin_digest_parameter.default is None
    assert sum(
        item.get("event") == "start" and item.get("slot_id") == attempt_slot.slot_id
        for item in R.load_attempt_registry(repo)
    ) == 1


@pytest.mark.parametrize(
    ("with_origin", "origin_run_plan_sha256"),
    [
        (True, None),
        (False, "a" * 64),
        (True, "not-a-sha256"),
    ],
    ids=["binding-without-digest", "digest-without-binding", "invalid-digest"],
)
def test_lifecycle_start_requires_origin_binding_and_run_plan_digest_iff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    with_origin: bool,
    origin_run_plan_sha256: str | None,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    capability = (
        _issued_origin_binding(trial, _head(repo), monkeypatch)
        if with_origin else None
    )
    attempt_slot = _lifecycle_attempt_slot(
        repo, manifest, admission, origin_binding=capability,
    )
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH

    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-origin\] "):
        R.record_trial_start_once(
            admission=admission,
            effective_preregistration=_effective_capability(manifest, monkeypatch),
            manifest_path=manifest_path,
            run_root=repo / "rejected-origin-run",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
            origin_binding=capability,
            origin_run_plan_sha256=origin_run_plan_sha256,
            attempt_slot=attempt_slot,
        )
    assert not lifecycle.exists()


def test_m07_outer_manifest_capability_commit_check_is_unmasked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    valid = _effective_capability(manifest, monkeypatch)
    wrong = R.s8c_preregistration._construct_effective(
        dataclasses.replace(valid.report, commit=_head(repo))
    )
    monkeypatch.setattr(
        R.s8c_preregistration,
        "require_effective_preregistration",
        lambda *_args, **_kwargs: pytest.fail("lower helper masked outer check"),
    )
    trial = manifest.trials[0]
    with pytest.raises(
        R.TrialRegistryError,
        match=(r"\[effective-preregistration\] manifest prereg_commit requires "
               r"an exact EffectivePreregistration capability$"),
    ):
        R.admit_registered_launch(
            effective_preregistration=wrong,
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_admit_registered_launch_rejects_ancestor_commit_capability(
    tmp_path: Path,
) -> None:
    repo, ancestor = _init_repo(tmp_path)
    prereg_marker = repo / "prereg.txt"
    prereg_marker.write_text("prereg\n", encoding="utf-8")
    prereg_commit = _commit(repo, "prereg", prereg_marker)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg_commit, "ancestor-cap"))
    _commit(repo, "manifest", manifest_path)
    registry = repo / "registry.jsonl"
    _append_fixture_registration(
        manifest_path=manifest_path,
        repository_root=repo,
        registry_path=registry,
    )
    _commit(repo, "registry", registry)
    manifest = R.load_trial_manifest(manifest_path)
    module = R.s8c_preregistration
    ancestor_report = module.ActivationReport(
        commit=ancestor,
        condition_freeze_valid=True,
        freeze_generation=1,
        protected_sha256="1" * 64,
        freeze_reason_code="valid",
        decider_version=module.DECIDER_VERSION,
        decider_version_matches=True,
        decider_version_reason_code="decider-version-match",
        section5_findings=(),
        predicates=(),
        core_module_blob_sha256="2" * 64,
        evaluator_module_blob_sha256="3" * 64,
        projection_module_blob_sha256="4" * 64,
        effective=True,
    )
    ancestor_capability = module._construct_effective(ancestor_report)
    trial = manifest.trials[0]
    with pytest.raises(R.TrialRegistryError, match=r"\[effective-preregistration\] "):
        R.admit_registered_launch(
            effective_preregistration=ancestor_capability,
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_registered_admission_and_lifecycle_are_non_certifying_and_start_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    first_attempt = _lifecycle_attempt_slot(repo, manifest, admission)
    terminal_parameters = inspect.signature(R.record_trial_terminal).parameters
    assert "report_sha256" not in terminal_parameters
    assert "attempt_journal_sha256" not in terminal_parameters
    assert admission.mode == "registered-effective"
    assert admission.certifying is False
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    copied_admission = dataclasses.replace(
        admission, activation_report_digest_sha256="f" * 64,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[launch-admission\] supplied admission differs from fresh derivation$",
    ):
        R.record_trial_start_once(
            admission=copied_admission,
            effective_preregistration=_effective_capability(manifest, monkeypatch),
            manifest_path=manifest_path,
            run_root=repo / "copied-admission-run",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
            attempt_slot=first_attempt,
        )
    alternate_lifecycle = repo / "alternate-lifecycle.jsonl"
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[lifecycle-path\] lifecycle_path must name the canonical "
            r"repository ledger$"
        ),
    ):
        R.record_trial_start_once(
            admission=admission,
            effective_preregistration=_effective_capability(manifest, monkeypatch),
            manifest_path=manifest_path,
            run_root=repo / "alternate-ledger-run",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=alternate_lifecycle,
            attempt_slot=first_attempt,
        )
    assert not alternate_lifecycle.exists()
    R.reject_started_trial(
        trial_id=admission.trial_id,
        repository_root=repo,
        lifecycle_path=lifecycle,
    )
    first = R.record_trial_start_once(
        admission=admission,
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        run_root=repo / "run-one",
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
        attempt_slot=first_attempt,
    )
    attempt_start_row = next(
        row for row in R.load_attempt_registry(repo)
        if row.get("event") == "start"
        and row.get("slot_id") == first_attempt.slot_id
    )
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-start-once\] "):
        R.record_trial_start_once(
            admission=admission,
            effective_preregistration=_effective_capability(manifest, monkeypatch),
            manifest_path=manifest_path,
            run_root=repo / "different-run-root",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
            attempt_slot=first_attempt,
        )
    second_admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch, trial_index=1,
    )
    second_attempt = _lifecycle_attempt_slot(repo, manifest, second_admission)
    second = R.record_trial_start_once(
        admission=second_admission,
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        run_root=repo / "run-two",
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
        attempt_slot=second_attempt,
    )
    lifecycle_before_reject = lifecycle.read_bytes()
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-start-once\] "):
        R.reject_started_trial(
            trial_id=first.trial_id,
            repository_root=repo,
            lifecycle_path=lifecycle,
        )
    assert lifecycle.read_bytes() == lifecycle_before_reject
    R.forbid_trial_restart(second)
    second_state = R._TRIAL_LIFECYCLE_CAPABILITIES[id(second)]
    assert second_state.started_once is True
    assert second_state.restart_forbidden is True
    lifecycle_before_forbidden_reject = lifecycle.read_bytes()
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[lifecycle-restart-forbidden\] ",
    ):
        R.record_trial_start_once(
            admission=second_admission,
            effective_preregistration=_effective_capability(manifest, monkeypatch),
            manifest_path=manifest_path,
            run_root=repo / "forbidden-rerun-root",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
            attempt_slot=second_attempt,
        )
    assert lifecycle.read_bytes() == lifecycle_before_forbidden_reject
    full_field_replacement = dataclasses.replace(
        first,
        repository_root=second.repository_root,
        lifecycle_path=second.lifecycle_path,
        trial_id=second.trial_id,
        run_root=second.run_root,
        start_row_sha256=second.start_row_sha256,
        launch_admission_sha256=second.launch_admission_sha256,
    )
    forged_tokens = (
        dataclasses.replace(first),
        dataclasses.replace(first, lifecycle_path=repo / "alternate-ledger.jsonl"),
        full_field_replacement,
    )
    for forged in forged_tokens:
        with pytest.raises(
            R.TrialRegistryError,
            match=(
                r"\[lifecycle-token\] terminal requires the exact object "
                r"issued at lifecycle start$"
            ),
        ):
            R.record_trial_terminal(
                forged,
                terminal_status="indeterminate",
            )

    first_run = Path(first.run_root)
    first_run.mkdir()
    report_bytes = b'{"status":"complete"}\n'
    journal_bytes = b'{"event":"run-start"}\n'
    (first_run / "report.json").write_bytes(report_bytes)
    (first_run / "attempts.jsonl").write_bytes(journal_bytes)
    _finish_lifecycle_attempt(first_attempt, terminal_status="observed")
    attempt_terminal_row = next(
        row for row in R.load_attempt_registry(repo)
        if row.get("event") == "terminal"
        and row.get("slot_id") == first_attempt.slot_id
    )
    R.record_trial_terminal(
        first,
        terminal_status="complete",
    )
    _finish_lifecycle_attempt(second_attempt, terminal_status="not-consumed")
    R.record_trial_terminal(second, terminal_status="indeterminate")
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[lifecycle-token\] lifecycle capability was already consumed$",
    ):
        R.record_trial_terminal(
            first,
            terminal_status="indeterminate",
        )
    rows = [json.loads(line) for line in lifecycle.read_text().splitlines()]
    assert [row["event"] for row in rows] == [
        "start", "start", "terminal", "terminal",
    ]
    assert rows[0] == {
        "schema_version": R.LIFECYCLE_SCHEMA_VERSION,
        "event": "start",
        "trial_id": admission.trial_id,
        "run_root": str((repo / "run-one").resolve()),
        "mode": "registered-effective",
        "manifest_sha256": admission.binding.manifest_sha256,
        "measurement_head": admission.binding.measurement_head,
        "activation_report_digest_sha256": (
            admission.activation_report_digest_sha256
        ),
        "prereg_commit": admission.binding.prereg_commit,
        "prereg_content_commit": admission.binding.prereg_content_commit,
        "prereg_effective_commit": admission.binding.prereg_effective_commit,
        "slot_id": first_attempt.slot_id,
        "schedule_row_sha256": attempt_start_row["schedule_row_sha256"],
        "process_identity": attempt_start_row["process_identity"],
        "launch_admission_sha256": hashlib.sha256(
            _canonical(R.launch_admission_record(admission))
        ).hexdigest(),
    }
    first_terminal = next(
        row for row in rows
        if row["event"] == "terminal" and row["trial_id"] == first.trial_id
    )
    assert first_terminal["report_sha256"] == hashlib.sha256(
        report_bytes
    ).hexdigest()
    assert first_terminal["attempt_journal_sha256"] == hashlib.sha256(
        journal_bytes
    ).hexdigest()
    assert first_terminal == {
        "schema_version": R.LIFECYCLE_SCHEMA_VERSION,
        "event": "terminal",
        "trial_id": first.trial_id,
        "terminal_status": "complete",
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "attempt_journal_sha256": hashlib.sha256(journal_bytes).hexdigest(),
        "prereg_commit": first_attempt.prereg_commit,
        "prereg_content_commit": first_attempt.prereg_content_commit,
        "prereg_effective_commit": first_attempt.prereg_effective_commit,
        "slot_id": first_attempt.slot_id,
        "classification_receipt_sha256": (
            attempt_terminal_row["classification_receipt_sha256"]
        ),
        "raw_output_sha256": attempt_terminal_row["raw_output_sha256"],
    }


@pytest.mark.parametrize(
    ("terminal_status", "attempt_status", "failure_reason", "accepted"),
    [
        ("complete", "observed", None, False),
        ("partial", "terminal-failure", "", False),
        ("indeterminate", "not-consumed", "", False),
        ("partial", "terminal-failure", "producer-failure", True),
        ("indeterminate", "not-consumed", "producer-failure", True),
    ],
    ids=[
        "complete-without-projection",
        "partial-with-empty-reason",
        "indeterminate-with-empty-reason",
        "partial-with-reason",
        "indeterminate-with-reason",
    ],
)
def test_origin_lifecycle_terminal_without_projection_is_failure_reason_gated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    terminal_status: str,
    attempt_status: str,
    failure_reason: str | None,
    accepted: bool,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    capability = _issued_origin_binding(trial, _head(repo), monkeypatch)
    attempt_slot = _lifecycle_attempt_slot(
        repo, manifest, admission, origin_binding=capability,
    )
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    run_root = repo / "origin-failure-run"
    token = R.record_trial_start_once(
        admission=admission,
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        run_root=run_root,
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
        origin_binding=capability,
        origin_run_plan_sha256="e" * 64,
        attempt_slot=attempt_slot,
    )
    if terminal_status != "indeterminate":
        run_root.mkdir()
        (run_root / "report.json").write_bytes(b"{}\n")
        (run_root / "attempts.jsonl").write_bytes(b"{}\n")
    _classify_and_terminal(
        attempt_slot,
        failure_reason=(
            "producer-failure" if attempt_status == "terminal-failure" else None
        ),
        terminal_status=attempt_status,
    )

    if not accepted:
        with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-origin\] "):
            R.record_trial_terminal(
                token,
                terminal_status=terminal_status,
                failure_reason=failure_reason,
            )
        assert len(lifecycle.read_bytes().splitlines()) == 1
        return

    R.record_trial_terminal(
        token,
        terminal_status=terminal_status,
        failure_reason=failure_reason,
    )
    rows = [json.loads(line) for line in lifecycle.read_bytes().splitlines()]
    start, terminal = rows
    assert "launch_admission" not in start
    assert "origin_terminal_projection" not in terminal
    assert terminal["failure_reason"] == failure_reason
    assert frozenset(terminal) == (
        R._LIFECYCLE_TERMINAL_BASE_KEYS | {"failure_reason"}
    )
    assert R._load_lifecycle_rows(lifecycle.read_bytes()) == tuple(rows)

    empty_reason = copy.deepcopy(rows)
    empty_reason[1]["failure_reason"] = ""
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[lifecycle-origin\] origin failure without terminal projection "
            r"requires a non-empty failure_reason$"
        ),
    ):
        R._load_lifecycle_rows(
            b"".join(_canonical(row) + b"\n" for row in empty_reason)
        )
    complete_without_projection = copy.deepcopy(rows)
    complete_without_projection[1]["terminal_status"] = "complete"
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[lifecycle-origin\] start run-plan digest and terminal origin "
            r"projection presence differ$"
        ),
    ):
        R._load_lifecycle_rows(
            b"".join(
                _canonical(row) + b"\n"
                for row in complete_without_projection
            )
        )


def test_originless_lifecycle_terminal_shape_and_projection_rejection_are_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    attempt_slot = _lifecycle_attempt_slot(repo, manifest, admission)
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    token = R.record_trial_start_once(
        admission=admission,
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        run_root=repo / "originless-indeterminate-run",
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
        attempt_slot=attempt_slot,
    )
    _finish_lifecycle_attempt(attempt_slot, terminal_status="not-consumed")
    R.record_trial_terminal(token, terminal_status="indeterminate")
    rows = [json.loads(line) for line in lifecycle.read_bytes().splitlines()]
    start, terminal = rows
    assert frozenset(start) == R._LIFECYCLE_START_BASE_KEYS
    assert frozenset(terminal) == R._LIFECYCLE_TERMINAL_BASE_KEYS
    assert R._load_lifecycle_rows(lifecycle.read_bytes()) == tuple(rows)

    with_projection = copy.deepcopy(rows)
    with_projection[1]["origin_terminal_projection"] = {}
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-origin\] "):
        R._load_lifecycle_rows(
            b"".join(_canonical(row) + b"\n" for row in with_projection)
        )
    with_failure_reason = copy.deepcopy(rows)
    with_failure_reason[1]["failure_reason"] = "producer-failure"
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-origin\] "):
        R._load_lifecycle_rows(
            b"".join(_canonical(row) + b"\n" for row in with_failure_reason)
        )


@pytest.mark.parametrize("rejected", [True, False])
def test_lifecycle_terminal_projects_the_formal_consumer_shape_by_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rejected: bool,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    binding_record = _fixture_origin_binding(trial, _head(repo))
    capability = _issued_origin_binding(
        trial,
        _head(repo),
        monkeypatch,
        origin_binding_record=binding_record,
    )
    attempt_slot = _lifecycle_attempt_slot(
        repo, manifest, admission, origin_binding=capability,
    )
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    token = R.record_trial_start_once(
        admission=admission,
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        run_root=repo / "origin-run",
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
        origin_binding=capability,
        origin_run_plan_sha256="e" * 64,
        attempt_slot=attempt_slot,
    )
    projection = _origin_terminal_projection(
        rejected=rejected,
        origin_binding_record=binding_record,
        arm_binding_digest_sha256=_fixture_arm_execution(trial)[
            "arm_binding_digest_sha256"
        ],
    )
    _finish_lifecycle_attempt(attempt_slot, terminal_status="not-consumed")
    R.record_trial_terminal(
        token,
        terminal_status="indeterminate",
        origin_terminal_projection=projection,
    )
    rows = [json.loads(line) for line in lifecycle.read_bytes().splitlines()]
    start, terminal = rows
    assert token.origin_run_plan_sha256 == "e" * 64
    assert start["origin_run_plan_sha256"] == "e" * 64
    expected_admission = R.launch_admission_record(
        admission,
        origin_binding=capability,
    )
    assert "launch_admission" not in start
    assert start["launch_admission_sha256"] == hashlib.sha256(
        _canonical(expected_admission)
    ).hexdigest()
    assert _canonical({
        "origin_terminal_projection": terminal["origin_terminal_projection"],
    }) == _canonical(formal.origin_terminal_projection_record(projection))
    if rejected:
        assert terminal["origin_terminal_projection"][
            "formal_receipt_sha256"
        ] is None
        assert terminal["origin_terminal_projection"][
            "evidence_root_sha256"
        ] is None
    without_digest = copy.deepcopy(rows)
    without_digest[0].pop("origin_run_plan_sha256")
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-origin\] "):
        R._load_lifecycle_rows(
            b"".join(_canonical(row) + b"\n" for row in without_digest)
        )
    without_projection = copy.deepcopy(rows)
    without_projection[1].pop("origin_terminal_projection")
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-origin\] "):
        R._load_lifecycle_rows(
            b"".join(_canonical(row) + b"\n" for row in without_projection)
        )
    invalid_digest = copy.deepcopy(rows)
    invalid_digest[0]["origin_run_plan_sha256"] = "not-a-sha256"
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[lifecycle-schema\] start origin_run_plan_sha256 is invalid$",
    ):
        R._load_lifecycle_rows(
            b"".join(_canonical(row) + b"\n" for row in invalid_digest)
        )


def test_lifecycle_updates_take_exclusive_flock_and_fsync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    attempt_slot = _lifecycle_attempt_slot(repo, manifest, admission)
    original_flock = R.fcntl.flock
    original_fsync = R.os.fsync
    locks: list[int] = []
    fsync_modes: list[int] = []

    def observe_flock(fd: int, operation: int) -> None:
        locks.append(operation)
        original_flock(fd, operation)

    def observe_fsync(fd: int) -> None:
        fsync_modes.append(os.fstat(fd).st_mode)
        original_fsync(fd)

    monkeypatch.setattr(R.fcntl, "flock", observe_flock)
    monkeypatch.setattr(R.os, "fsync", observe_fsync)
    R.record_trial_start_once(
        admission=admission,
        effective_preregistration=_effective_capability(manifest, monkeypatch),
        manifest_path=manifest_path,
        run_root=repo / "run",
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=repo / R.DEFAULT_LIFECYCLE_PATH,
        attempt_slot=attempt_slot,
    )
    assert locks == [R.fcntl.LOCK_EX]
    assert len(fsync_modes) == 2
    assert stat.S_ISREG(fsync_modes[0])
    assert stat.S_ISDIR(fsync_modes[1])


def test_lifecycle_rejects_noncanonical_json_before_append(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    attempt_slot = _lifecycle_attempt_slot(repo, manifest, admission)
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    lifecycle.parent.mkdir(parents=True)
    original = b'{"event":"unknown", "schema_version":"p3-8c-trial-lifecycle/v1"}\n'
    lifecycle.write_bytes(original)
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-canonical\] "):
        R.record_trial_start_once(
            admission=admission,
            effective_preregistration=_effective_capability(manifest, monkeypatch),
            manifest_path=manifest_path,
            run_root=repo / "run",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
            attempt_slot=attempt_slot,
        )
    assert lifecycle.read_bytes() == original


def test_lifecycle_rejects_canonical_unknown_event_before_append(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    admission = _registered_admission(
        repo, manifest_path, registry, manifest, monkeypatch,
    )
    attempt_slot = _lifecycle_attempt_slot(repo, manifest, admission)
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    lifecycle.parent.mkdir(parents=True)
    original = _canonical({
        "schema_version": R.LIFECYCLE_SCHEMA_VERSION,
        "event": "unknown",
    }) + b"\n"
    lifecycle.write_bytes(original)
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-schema\] "):
        R.record_trial_start_once(
            admission=admission,
            effective_preregistration=_effective_capability(manifest, monkeypatch),
            manifest_path=manifest_path,
            run_root=repo / "run",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
            attempt_slot=attempt_slot,
        )
    assert lifecycle.read_bytes() == original


@pytest.mark.parametrize("history_attack", ["delete-recreate", "modify-revert"])
def test_lifecycle_git_history_rejects_non_append_only_attacks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    history_attack: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    capability = _effective_capability(manifest, monkeypatch)
    first_trial, second_trial = manifest.trials[:2]
    first = R.admit_registered_launch(
        effective_preregistration=capability,
        manifest_path=manifest_path,
        trial_id=first_trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[first_trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )
    first_attempt = _lifecycle_attempt_slot(repo, manifest, first)
    lifecycle = repo / R.DEFAULT_LIFECYCLE_PATH
    token = R.record_trial_start_once(
        admission=first,
        effective_preregistration=capability,
        manifest_path=manifest_path,
        run_root=repo / "first-run",
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
        attempt_slot=first_attempt,
    )
    _finish_lifecycle_attempt(first_attempt, terminal_status="not-consumed")
    R.record_trial_terminal(
        token,
        terminal_status="indeterminate",
    )
    original = lifecycle.read_bytes()
    _commit(repo, "introduce lifecycle", lifecycle)
    if history_attack == "delete-recreate":
        lifecycle.unlink()
        _commit(repo, "delete lifecycle", lifecycle)
    else:
        lifecycle.write_bytes(
            original.replace(b'"terminal_status":"indeterminate"',
                             b'"terminal_status":"partial"')
        )
        _commit(repo, "modify lifecycle", lifecycle)
    lifecycle.write_bytes(original)
    _commit(repo, "restore lifecycle bytes", lifecycle)

    second = R.admit_registered_launch(
        effective_preregistration=capability,
        manifest_path=manifest_path,
        trial_id=second_trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[second_trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )
    second_attempt = _lifecycle_attempt_slot(repo, manifest, second)
    with pytest.raises(R.TrialRegistryError, match=r"\[lifecycle-history\] "):
        R.record_trial_start_once(
            admission=second,
            effective_preregistration=capability,
            manifest_path=manifest_path,
            run_root=repo / "second-run",
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
            attempt_slot=second_attempt,
        )
    assert "within one Git repository" in (R._lifecycle_history_tip.__doc__ or "")


def test_m10_acceptance_rejects_missing_lifecycle_terminal(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    with pytest.MonkeyPatch.context() as monkeypatch:
        capability = _effective_capability(manifest, monkeypatch)
        lifecycle = _write_acceptance_lifecycle(
            repo,
            manifest,
            reports,
            capability.report_digest_sha256,
            omit_terminal_trial_id=manifest.trials[0].trial_id,
        )
        with pytest.raises(
            R.TrialRegistryError,
            match=r"\[acceptance-lifecycle\].*exactly one terminal row",
        ):
            R.assert_trial_registry_acceptance(
                effective_preregistration=capability,
                manifest_path=manifest_path,
                report_paths=reports,
                repository_root=repo,
                registry_path=registry,
                lifecycle_path=lifecycle,
            )


def test_acceptance_rejects_start_run_root_outside_report_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    rows = [json.loads(line) for line in lifecycle.read_text().splitlines()]
    wrong_root = repo / "wrong-run-root"
    wrong_root.mkdir()
    first_trial_id = manifest.trials[0].trial_id
    first_start = next(
        row for row in rows
        if row["event"] == "start" and row["trial_id"] == first_trial_id
    )
    first_start["run_root"] = str(wrong_root.resolve())
    lifecycle.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[acceptance-lifecycle\] trial .* start run_root differs "
            r"from report/journal parent$"
        ),
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )


def test_m11_acceptance_receipt_is_exclusive_create(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    first = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    receipt = repo / first.receipt_path
    original = receipt.read_bytes()
    with pytest.raises(
        R.TrialRegistryError, match=r"\[receipt-exclusive-create\] "
    ):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert receipt.read_bytes() == original


def test_acceptance_v3_has_no_certifying_issuance_branch(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    summary = _accept(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    receipt_path = repo / summary.receipt_path
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    parsed = R.s8c_acceptance_receipt.parse_acceptance_receipt_bytes(
        receipt_path.read_bytes()
    )
    assert parsed.certifying is False
    assert summary.receipt_path == (
        f"output/s8c-trial-registry/receipts/{manifest.sha256}.json"
    )
    assert receipt["certifying"] is False
    assert receipt["non_certifying_reason_codes"] == [
        "no-build",
        "t468-approval-authority-absent"
    ]
    assert all("arm_execution" in trial for trial in receipt["trials"])
    assert all("cross_binding_receipt_sha256" in trial for trial in receipt["trials"])
    assert "cross_binding_receipt_sha256" in receipt
    source = Path(R.__file__).read_text(encoding="utf-8")
    receipt_block = source.split("receipt_value =", 1)[1].split(
        "_exclusive_create_acceptance_receipt", 1
    )[0]
    assert '"certifying": False' in receipt_block
    assert '"certifying": True' not in receipt_block


def test_acceptance_effective_preregistration_is_mandatory_keyword() -> None:
    parameter = inspect.signature(
        R.assert_trial_registry_acceptance
    ).parameters["effective_preregistration"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


def test_registry_introduction_is_unique_history_not_approval_authority(
    tmp_path: Path,
) -> None:
    repo, _manifest_path, registry, _manifest = _registered_repo(tmp_path)
    current = _head(repo)
    relative = registry.relative_to(repo).as_posix()
    introduction = R._registry_introduction_commit(
        repository_root=repo,
        relative_path=relative,
        current_head=current,
    )
    assert introduction == current
    original = registry.read_bytes()
    registry.unlink()
    _commit(repo, "delete registry", registry)
    registry.write_bytes(original)
    recreated = _commit(repo, "recreate registry", registry)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-introduction\] "):
        R._registry_introduction_commit(
            repository_root=repo,
            relative_path=relative,
            current_head=recreated,
        )
    assert "not an approval-authority attestation" in (
        R._registry_introduction_commit.__doc__ or ""
    )


def test_p12_accept_cli_runs_from_clean_pythonpath(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    capability = R.s8c_preregistration._construct_effective(
        _effective_report(manifest)
    )
    _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        env.pop(key, None)
    env["PYTHONPATH"] = str(_SOURCE_REPO)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from orchestrator.campaign import trial_registry as R; "
                "m=R.load_trial_manifest(R.Path(sys.argv[sys.argv.index('--manifest')+1])); "
                "p=R.s8c_preregistration; "
                "r=p.ActivationReport(commit=m.prereg_commit,"
                "condition_freeze_valid=True,freeze_generation=1,"
                "protected_sha256='1'*64,freeze_reason_code='valid',"
                "decider_version=p.DECIDER_VERSION,decider_version_matches=True,"
                "decider_version_reason_code='decider-version-match',"
                "section5_findings=(),predicates=(),"
                "core_module_blob_sha256='2'*64,"
                "evaluator_module_blob_sha256='3'*64,"
                "projection_module_blob_sha256='4'*64,effective=True); "
                "p.activation_report_at=lambda repo_root,commit:r; "
                "raise SystemExit(R.main(sys.argv[1:]))"
            ),
            "accept",
            "--manifest",
            str(manifest_path),
            "--repo-root",
            str(repo),
            "--registry",
            str(registry),
            *map(str, reports),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["certifying"] is False
    assert output["arm_binding"] == "execution-bound"
    assert output["check"] == "trial-ID completeness (registry)"


def test_m1_duplicate_json_key_is_rejected(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    valid = _manifest_value(prereg, "m1")
    raw = json.dumps(valid).replace(
        '"trial_id": "m1-h1-on"',
        '"trial_id": "decoy", "trial_id": "m1-h1-on"',
        1,
    )
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(R.TrialRegistryError, match=r"\[json\] duplicate object key: 'trial_id'$"):
        R.load_trial_manifest(path)


@pytest.mark.parametrize("mutation", ["missing", "unknown", "schema"])
def test_m2_exact_manifest_schema_is_rejected(tmp_path: Path, mutation: str) -> None:
    _repo, prereg = _init_repo(tmp_path)
    value = _manifest_value(prereg, "m2")
    if mutation == "missing":
        value.pop("trials")
    elif mutation == "unknown":
        value["unknown"] = True
    else:
        value["schema_version"] = "p3-8c-trial-manifest/v0"
    path = tmp_path / "manifest.json"
    _write_manifest(path, value)
    with pytest.raises(R.TrialRegistryError, match=r"\[schema\] "):
        R.load_trial_manifest(path)


def test_m3_cartesian_gate_rejects_duplicate_and_missing_pair(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    value = _manifest_value(prereg, "m3")
    value["trials"][-1]["holdout"] = "H1"
    path = tmp_path / "manifest.json"
    _write_manifest(path, value)
    with pytest.raises(R.TrialRegistryError, match=r"\[trial-universe\] "):
        R.load_trial_manifest(path)


@pytest.mark.parametrize("field", ["trial_id", "campaign_id"])
def test_m4_trial_and_campaign_uniqueness_is_rejected(tmp_path: Path, field: str) -> None:
    _repo, prereg = _init_repo(tmp_path)
    value = _manifest_value(prereg, "m4")
    value["trials"][1][field] = value["trials"][0][field]
    path = tmp_path / "manifest.json"
    _write_manifest(path, value)
    with pytest.raises(R.TrialRegistryError, match=r"\[uniqueness\] "):
        R.load_trial_manifest(path)


def test_m5_prereg_commit_lexical_closed_set_is_rejected(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    manifest = _manifest_value(prereg, "m5")
    manifest["prereg_commit"] = "abc123"
    path = tmp_path / "manifest.json"
    _write_manifest(path, manifest)
    with pytest.raises(R.TrialRegistryError, match=r"\[field\] "):
        R.load_trial_manifest(path)


@pytest.mark.parametrize(("field", "value"), [("arm", "blind"), ("holdout", "H3")])
def test_redundant_field_gate_rejects_before_cartesian_fallback(
    tmp_path: Path, field: str, value: str,
) -> None:
    _repo, prereg = _init_repo(tmp_path)
    manifest = _manifest_value(prereg, "field-defense")
    manifest["trials"][0][field] = value
    path = tmp_path / "manifest.json"
    _write_manifest(path, manifest)
    with pytest.raises(R.TrialRegistryError, match=r"\[field\] "):
        R.load_trial_manifest(path)


def _valid_registry_row(tmp_path: Path, prefix: str = "m6") -> dict:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    _write_manifest(path, _manifest_value(prereg, prefix))
    return _registration_value(R.load_trial_manifest(path))


def test_m6a_registry_unterminated_line_is_rejected(tmp_path: Path) -> None:
    row = _valid_registry_row(tmp_path)
    path = tmp_path / "registry.jsonl"
    path.write_bytes(_canonical(row))
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-framing\] "):
        R.load_trial_registry(path)


def test_m6b_registry_noncanonical_line_is_rejected(tmp_path: Path) -> None:
    row = _valid_registry_row(tmp_path)
    path = tmp_path / "registry.jsonl"
    path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-canonical\] "):
        R.load_trial_registry(path)


def test_registration_trials_must_use_canonical_order(tmp_path: Path) -> None:
    row = _valid_registry_row(tmp_path, prefix="registry-order")
    row["trials"].reverse()
    path = tmp_path / "registry.jsonl"
    _write_registry(path, row)
    with pytest.raises(R.TrialRegistryError, match=r"\[registration-binding\] "):
        R.load_trial_registry(path)


def test_redundant_registry_blank_line_gate_rejects_before_json_decoder(
    tmp_path: Path,
) -> None:
    row = _valid_registry_row(tmp_path)
    path = tmp_path / "registry.jsonl"
    path.write_bytes(_canonical(row) + b"\n\n")
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-framing\] "):
        R.load_trial_registry(path)


def test_redundant_registry_duplicate_key_gate_rejects_before_canonical_bytes(
    tmp_path: Path,
) -> None:
    row = _valid_registry_row(tmp_path)
    raw = _canonical(row).decode().replace(
        '"schema_version":"p3-8c-trial-registration/v2"',
        '"schema_version":"decoy","schema_version":"p3-8c-trial-registration/v2"',
        1,
    )
    path = tmp_path / "registry.jsonl"
    path.write_text(raw + "\n", encoding="utf-8")
    with pytest.raises(R.TrialRegistryError, match=r"\[json\] duplicate object key: 'schema_version'$"):
        R.load_trial_registry(path)


def test_m7_append_preserves_inode_size_and_existing_prefix(tmp_path: Path) -> None:
    repo, _manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    old_stat = registry.stat()
    old_bytes = registry.read_bytes()
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_b_path, _manifest_value(manifest_a.prereg_commit, "m7-b"))
    _commit(repo, "manifest-b", manifest_b_path)
    _append_fixture_registration(
        manifest_path=manifest_b_path, repository_root=repo, registry_path=registry,
    )
    new_stat = registry.stat()
    new_bytes = registry.read_bytes()
    assert new_stat.st_ino == old_stat.st_ino
    assert new_stat.st_size > old_stat.st_size
    assert new_bytes.startswith(old_bytes)


@pytest.mark.parametrize("reuse", ["manifest", "trial", "campaign"])
def test_m8_registry_global_reuse_is_rejected(tmp_path: Path, reuse: str) -> None:
    repo, manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    if reuse == "manifest":
        manifest_path = manifest_a_path
    else:
        value = _manifest_value(manifest_a.prereg_commit, f"m8-{reuse}")
        field = "trial_id" if reuse == "trial" else "campaign_id"
        value["trials"][0][field] = getattr(manifest_a.trials[0], field)
        manifest_path = repo / f"manifest-{reuse}.json"
        _write_manifest(manifest_path, value)
        _commit(repo, f"manifest-{reuse}", manifest_path)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-index\] "):
        _append_fixture_registration(
            manifest_path=manifest_path,
            repository_root=repo,
            registry_path=registry,
        )


@pytest.mark.parametrize("state", ["untracked", "dirty"])
def test_m9_launcher_requires_committed_exact_registry(tmp_path: Path, state: str) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "m9"))
    _commit(repo, "manifest", manifest_path)
    registry = repo / "registry.jsonl"
    _append_fixture_registration(
        manifest_path=manifest_path, repository_root=repo, registry_path=registry,
    )
    if state == "dirty":
        _commit(repo, "registry", registry)
        registry.write_bytes(registry.read_bytes() + b"{}\n")
    trial = R.load_trial_manifest(manifest_path).trials[0]
    with pytest.raises(R.TrialRegistryError, match=r"\[committed-registry\] "):
        R.load_launch_binding(
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


@pytest.mark.parametrize(
    "mutation",
    ["arm", "campaign", "prereg", "hash"],
    ids=["m10a-arm", "m10b-campaign", "m10c-prereg", "m10d-hash"],
)
def test_m10_registration_must_exactly_match_manifest(
    tmp_path: Path, mutation: str,
) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "m10"))
    _commit(repo, "manifest", manifest_path)
    manifest = R.load_trial_manifest(manifest_path)
    row = _registration_value(manifest)
    if mutation == "arm":
        row["trials"][0]["arm"], row["trials"][1]["arm"] = (
            row["trials"][1]["arm"], row["trials"][0]["arm"],
        )
    elif mutation == "campaign":
        row["trials"][0]["campaign_id"] += "-changed"
    elif mutation == "prereg":
        row["prereg_commit"] = _head(repo)
    else:
        row["manifest_sha256"] = "f" * 64
    registry = repo / "registry.jsonl"
    _write_registry(registry, row)
    _commit(repo, "registry", registry)
    trial = manifest.trials[0]
    with pytest.raises(R.TrialRegistryError, match=r"\[registration-binding\] "):
        R.load_launch_binding(
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_m11_selected_manifest_membership_is_required(tmp_path: Path) -> None:
    repo, manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_b_path, _manifest_value(manifest_a.prereg_commit, "m11-b"))
    _commit(repo, "manifest-b", manifest_b_path)
    _append_fixture_registration(
        manifest_path=manifest_b_path, repository_root=repo, registry_path=registry,
    )
    _commit(repo, "registry-b", registry)
    foreign = R.load_trial_manifest(manifest_b_path).trials[0]
    with pytest.raises(R.TrialRegistryError, match=r"\[trial-membership\] "):
        R.load_launch_binding(
            manifest_path=manifest_a_path,
            trial_id=foreign.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[foreign.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_m12_holdout_workload_binding_is_required(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    wrong = "rr20" if trial.holdout == "H1" else "rr80"
    with pytest.raises(R.TrialRegistryError, match=r"\[workload-binding\] "):
        R.load_launch_binding(
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[wrong],
            repository_root=repo,
            registry_path=registry,
        )


def test_m13_producer_campaign_derivation_is_independently_bound(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    trial = manifest.trials[0]
    binding = R.load_launch_binding(
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )
    arm_execution = R.bind_trial_arm(binding, repository_root=repo)
    with pytest.raises(R.TrialRegistryError, match=r"\[campaign-binding\] "):
        R.assert_campaign_binding(
            binding,
            arm_execution=arm_execution,
            actual_campaign_id=trial.campaign_id + "-derived",
        )


def test_m14_ancestry_direction_is_not_reversible(tmp_path: Path) -> None:
    repo, parent = _init_repo(tmp_path)
    child_file = repo / "child.txt"
    child_file.write_text("child\n", encoding="utf-8")
    child = _commit(repo, "child", child_file)
    with pytest.raises(R.TrialRegistryError, match=r"\[ancestry\] prereg_commit is not an ancestor"):
        R.assert_prereg_ancestor(
            repo, prereg_commit=child, measurement_commit=parent,
        )


def test_diagnostic_sensitivity_m15_git_operational_failure_is_not_non_ancestry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, head = _init_repo(tmp_path)
    original = R._git

    def fail_merge_base(repository_root: Path, args):
        if tuple(args[:2]) == ("merge-base", "--is-ancestor"):
            return subprocess.CompletedProcess([], 128, b"", b"synthetic failure")
        return original(repository_root, args)

    monkeypatch.setattr(R, "_git", fail_merge_base)
    with pytest.raises(R.TrialRegistryError, match=r"\[git-operational\].*rc=128"):
        R.assert_prereg_ancestor(repo, prereg_commit=head, measurement_commit=head)


def test_git_timeout_raises_operational_error_with_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_git = bin_dir / "git"
    fake_git.write_text("#!/bin/sh\nexec sleep 2\n", encoding="utf-8")
    fake_git.chmod(0o755)
    monkeypatch.setenv(
        "PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
    )

    with pytest.raises(R.TrialRegistryError, match=r"\[git-operational\]") as caught:
        R._git(tmp_path, ("timeout-sentinel",), timeout_s=0.25)

    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)
    assert caught.value.__cause__.timeout == 0.25


def test_git_timeout_preserves_success_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_git = bin_dir / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        "printf 'git stdout sentinel\\n'\n"
        "printf 'git stderr sentinel\\n' >&2\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv(
        "PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
    )

    result = R._git(tmp_path, ("success-sentinel",))

    assert result.returncode == 0
    assert result.stdout == b"git stdout sentinel\n"
    assert result.stderr == b"git stderr sentinel\n"


def test_git_timeout_preserves_nonzero_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_git = bin_dir / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        "printf 'git stdout sentinel\\n'\n"
        "printf 'git stderr sentinel\\n' >&2\n"
        "exit 23\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    monkeypatch.setenv(
        "PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
    )

    result = R._git(tmp_path, ("nonzero-sentinel",))

    assert result.returncode == 23
    assert result.stdout == b"git stdout sentinel\n"
    assert result.stderr == b"git stderr sentinel\n"


def test_git_timeout_default_reaches_subprocess_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def recorder(command, **kwargs):
        calls.append(kwargs)
        return subprocess.CompletedProcess(command, 0, b"", b"")

    # The production budget has no other observation seam without waiting 300s.
    monkeypatch.setattr(R.subprocess, "run", recorder)
    R._git(tmp_path, ("default-timeout-sentinel",))

    assert R._GIT_TIMEOUT_S == 300.0
    assert len(calls) == 1
    assert calls[0]["timeout"] == R._GIT_TIMEOUT_S


@pytest.mark.parametrize(
    "mutation", ["missing", "different"], ids=["m16a-missing", "m16b-different"],
)
def test_m16_report_prereg_binding_is_required(tmp_path: Path, mutation: str) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    events, report = _load_report_bundle(reports[0])
    if mutation == "missing":
        report.pop("prereg_commit")
        events[0].pop("prereg_commit")
        expected = r"\[run-start-binding\]"
    else:
        report["prereg_commit"] = "f" * 40
        events[0]["prereg_commit"] = "f" * 40
        expected = r"\[acceptance-binding\]"
    _persist(reports[0].parent, events, report)
    with pytest.raises(R.TrialRegistryError, match=expected):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_m17_measurement_registry_must_already_contain_registration(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "m17"))
    measurement = _commit(repo, "manifest", manifest_path)
    manifest = R.load_trial_manifest(manifest_path)
    registry = repo / "registry.jsonl"
    _append_fixture_registration(
        manifest_path=manifest_path, repository_root=repo, registry_path=registry,
    )
    _commit(repo, "late-registry", registry)
    reports = _reports(repo / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[historical-binding\] measurement registry blob is absent$"):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def _two_registration_measurement(
    tmp_path: Path,
) -> tuple[Path, Path, Path, R.TrialManifest, bytes, dict]:
    repo, manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_b_path, _manifest_value(manifest_a.prereg_commit, "history-b"))
    _commit(repo, "manifest-b", manifest_b_path)
    _append_fixture_registration(
        manifest_path=manifest_b_path, repository_root=repo, registry_path=registry,
    )
    _commit(repo, "registry-b", registry)
    manifest_b = R.load_trial_manifest(manifest_b_path)
    return (
        repo, manifest_a_path, registry, manifest_a,
        registry.read_bytes(), _registration_value(manifest_b),
    )


def test_redundant_registry_prefix_defense_rejects_before_history_walk(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest, measurement_bytes, _row_b = (
        _two_registration_measurement(tmp_path)
    )
    measurement = _head(repo)
    rows = [json.loads(line) for line in measurement_bytes.splitlines()]
    _write_registry(registry, *reversed(rows))
    _commit(repo, "reorder-registry", registry)
    reports = _reports(repo / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-prefix\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_redundant_six_report_argument_count_defense_is_required(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[report-count\] acceptance requires exactly 6"):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports[:-1],
            repository_root=repo,
            registry_path=registry,
        )


@pytest.mark.parametrize("mutation", ["duplicate", "foreign"])
def test_m20_report_trial_set_rejects_duplicate_or_foreign(
    tmp_path: Path, mutation: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    if mutation == "duplicate":
        reports[-1] = reports[0]
    else:
        events, report = _load_report_bundle(reports[-1])
        report["trial_id"] = "foreign-trial"
        events[0]["trial_id"] = "foreign-trial"
        _persist(reports[-1].parent, events, report)
    with pytest.raises(R.TrialRegistryError, match=r"\[trial-set\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


@pytest.mark.parametrize("mutation", ["ratio", "campaign"])
def test_m21_terminal_ratio_and_campaign_projection_is_bound(
    tmp_path: Path, mutation: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    events, report = _load_report_bundle(reports[0])
    if mutation == "ratio":
        report["cells"][0]["workload_flags"]["ycsb_rratio"] = "999"
    else:
        report["cells"][0]["campaign_id"] += "-changed"
    _persist(reports[0].parent, events, report)
    with pytest.raises(R.TrialRegistryError, match=r"\[terminal-projection\] report cell differs"):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_t525_runtime_cell_rejects_each_complete_condition_drift() -> None:
    cases = _T525_COMPLETE_CONDITION_CASES
    assert cases
    rejected_count = 0
    trial = R.TrialSpec(
        trial_id="t525-runtime-h1",
        arm="on",
        holdout="H1",
        campaign_id="t525-runtime-campaign",
        generations=1,
    )
    for section, field in cases:
        cell = _t525_condition_cell(trial)
        report = {"cells": [cell]}
        assert R._assert_runtime_report_cells(report, trial=trial) == [cell]
        section_value = cell[section]
        assert isinstance(section_value, dict)
        original = section_value[field]
        section_value[field] = (
            f"{original}-different" if isinstance(original, str) else original + 1
        )
        assert _t525_legacy_ratio_only_projection_passes(cell, trial)
        with pytest.raises(
            R.TrialRegistryError,
            match=(
                r"^\[runtime-cell-set\] runtime cell differs from its trial "
                rf"projection: {section}\.{field} differs$"
            ),
        ):
            R._assert_runtime_report_cells(report, trial=trial)
        rejected_count += 1
    assert rejected_count == len(cases)
    assert rejected_count > 0


def test_t525_holdout_bindings_are_deeply_immutable() -> None:
    mutations = (
        (R.HOLDOUT_BINDINGS, "H3", {"workload": "not-a-holdout"}),
        (R.HOLDOUT_BINDINGS["H1"], "records", 1),
    )
    assert mutations
    rejected_count = 0
    for mapping, key, value in mutations:
        with pytest.raises(TypeError):
            mapping[key] = value
        rejected_count += 1
    assert rejected_count == len(mutations)
    assert rejected_count > 0


@pytest.mark.parametrize(
    ("section", "field"),
    _T525_COMPLETE_CONDITION_CASES,
    ids=("skew", "rmw", "records", "threads"),
)
def test_t525_terminal_projection_rejects_each_complete_condition_drift(
    tmp_path: Path, section: str, field: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    events, report = _load_report_bundle(reports[0])
    trial = manifest.trials[0]
    assert trial.holdout == "H1"
    cell = report["cells"][0]
    R._assert_holdout_cell_condition(
        cell,
        expected=R.HOLDOUT_BINDINGS[trial.holdout],
        campaign_id=trial.campaign_id,
        gate="terminal-projection",
        message="report cell differs from manifest projection",
    )
    original = cell[section][field]
    cell[section][field] = (
        f"{original}-different" if isinstance(original, str) else original + 1
    )
    assert _t525_legacy_ratio_only_projection_passes(cell, trial)
    _persist(reports[0].parent, events, report)
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"^\[terminal-projection\] report cell differs from manifest "
            rf"projection: {section}\.{field} differs$"
        ),
    ):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_m22_existing_completeness_verifier_is_mandatory(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=True)
    events, report = _load_report_bundle(reports[0])
    events[1]["raw_response_sha256"] = "e" * 64
    _persist(reports[0].parent, events, report)
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"\[terminal-completeness\] \[role-bijection\] "
            r"journal/report role-attempt multisets differ$"
        ),
    ):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_m28_report_only_binding_without_run_start_binding_is_rejected(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    events, report = _load_report_bundle(reports[0])
    for field in ("prereg_commit", "measurement_head", "manifest_sha256"):
        events[0].pop(field)
    _persist(reports[0].parent, events, report)
    with pytest.raises(R.TrialRegistryError, match=r"\[run-start-binding\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_m29_intermediate_committed_rewrite_is_rejected_by_history_walk(
    tmp_path: Path,
) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_a_path = repo / "manifest-a.json"
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_a_path, _manifest_value(prereg, "m29-a"))
    _write_manifest(manifest_b_path, _manifest_value(prereg, "m29-b"))
    _commit(repo, "manifests", manifest_a_path, manifest_b_path)
    manifest_a = R.load_trial_manifest(manifest_a_path)
    manifest_b = R.load_trial_manifest(manifest_b_path)
    registry = repo / "registry.jsonl"
    _append_fixture_registration(
        manifest_path=manifest_a_path, repository_root=repo, registry_path=registry,
    )
    measurement = _commit(repo, "registry-a", registry)
    original = registry.read_bytes()
    rewritten = _registration_value(manifest_a)
    rewritten["trials"][0]["arm"], rewritten["trials"][1]["arm"] = (
        rewritten["trials"][1]["arm"], rewritten["trials"][0]["arm"],
    )
    _write_registry(registry, rewritten)
    _commit(repo, "rewrite-history", registry)
    registry.write_bytes(
        original + _canonical(_registration_value(manifest_b)) + b"\n"
    )
    _commit(repo, "restore-and-append", registry)
    reports = _reports(repo / "reports", manifest_a, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry history is not a strict prefix extension$"):
        _accept(
            manifest_path=manifest_a_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_registered_trial_is_rejected_without_manifest_for_unit_b(tmp_path: Path) -> None:
    repo, _manifest_path, registry, manifest = _registered_repo(tmp_path)
    with pytest.raises(R.TrialRegistryError, match=r"\[exploratory-registry\] "):
        R.admit_unregistered_exploratory(
            trial_id=manifest.trials[0].trial_id,
            workloads=["ycsb-a"],
            allow_unregistered_exploratory=True,
            repository_root=repo,
            registry_path=registry,
        )


def test_registry_parent_real_path_must_stay_inside_repository(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "path-parent"))
    _commit(repo, "manifest", manifest_path)
    outside = tmp_path / "outside" / "registry.jsonl"
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-path\] "):
        _append_fixture_registration(
            manifest_path=manifest_path,
            repository_root=repo,
            registry_path=outside,
        )
    assert not outside.parent.exists()


def test_append_uses_nofollow_append_flags_and_fsyncs_file_then_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "append-contract"))
    _commit(repo, "manifest", manifest_path)
    registry = repo / "nested" / "registry.jsonl"
    _prepare_fixture_effective_binding(
        repo, manifest_path, R.load_trial_manifest(manifest_path),
    )
    original_open = R.os.open
    original_fsync = R.os.fsync
    registry_flags: list[int] = []
    fsync_modes: list[int] = []

    def observe_open(path, flags, mode=0o777, *, dir_fd=None):
        if path == registry.name and dir_fd is not None:
            registry_flags.append(flags)
        if dir_fd is None:
            return original_open(path, flags, mode)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    def observe_fsync(fd: int) -> None:
        fsync_modes.append(os.fstat(fd).st_mode)
        original_fsync(fd)

    monkeypatch.setattr(R.os, "open", observe_open)
    monkeypatch.setattr(R.os, "fsync", observe_fsync)
    _append_fixture_registration(
        manifest_path=manifest_path,
        repository_root=repo,
        registry_path=registry,
    )
    assert len(registry_flags) == 1
    assert registry_flags[0] & os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        assert registry_flags[0] & os.O_NOFOLLOW
    assert len(fsync_modes) == 2
    assert stat.S_ISREG(fsync_modes[0])
    assert stat.S_ISDIR(fsync_modes[1])


def test_git_repository_switching_environment_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    wanted_root = tmp_path / "wanted"
    foreign_root = tmp_path / "foreign"
    wanted_root.mkdir()
    foreign_root.mkdir()
    repo, expected = _init_repo(wanted_root)
    foreign, _foreign_head = _init_repo(foreign_root)
    monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(foreign))
    assert R.resolve_measurement_commit(repo) == expected


def test_shallow_repository_is_rejected_for_ancestry(tmp_path: Path) -> None:
    repo, head = _init_repo(tmp_path)
    (repo / ".git" / "shallow").write_text(head + "\n", encoding="ascii")
    with pytest.raises(R.TrialRegistryError, match=r"\[ancestry\] shallow repositories"):
        R.assert_prereg_ancestor(
            repo, prereg_commit=head, measurement_commit=head,
        )


def test_launch_resolves_measurement_head_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    original = R.resolve_measurement_commit
    calls = 0

    def count(repository_root: Path) -> str:
        nonlocal calls
        calls += 1
        return original(repository_root)

    monkeypatch.setattr(R, "resolve_measurement_commit", count)
    trial = manifest.trials[0]
    R.load_launch_binding(
        manifest_path=manifest_path,
        trial_id=trial.trial_id,
        workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
        repository_root=repo,
        registry_path=registry,
    )
    assert calls == 1


def test_acceptance_report_argument_must_be_sibling_report_json(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    alias = reports[0].with_name("renamed-report.json")
    alias.write_bytes(reports[0].read_bytes())
    reports[0] = alias
    with pytest.raises(R.TrialRegistryError, match=r"\[report-path\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_registry_history_rejects_delete_then_recreate_commit(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    original = registry.read_bytes()
    registry.unlink()
    _commit(repo, "delete-registry", registry)
    registry.write_bytes(original)
    _commit(repo, "recreate-registry", registry)
    reports = _reports(repo / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry path was deleted"):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_exploratory_gate_uses_head_registry_when_working_file_is_missing(
    tmp_path: Path,
) -> None:
    repo, _manifest_path, registry, manifest = _registered_repo(tmp_path)
    registry.rename(repo / "temporarily-hidden-registry.jsonl")
    with pytest.raises(R.TrialRegistryError, match=r"\[exploratory-registry\] "):
        R.admit_unregistered_exploratory(
            trial_id=manifest.trials[0].trial_id,
            workloads=["ycsb-a"],
            allow_unregistered_exploratory=True,
            repository_root=repo,
            registry_path=registry,
        )


def test_m31_journal_snapshot_swap_cannot_compose_binding_and_completeness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    journal = reports[0].with_name("attempts.jsonl")
    events, report = _load_report_bundle(reports[0])
    swapped_events = copy.deepcopy(events)
    for field in ("prereg_commit", "measurement_head", "manifest_sha256"):
        swapped_events[0].pop(field)
    swapped_bytes = b"".join(_canonical(event) + b"\n" for event in swapped_events)
    report["attempt_journal_sha256"] = hashlib.sha256(swapped_bytes).hexdigest()
    reports[0].write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    original = R.assert_autonomous_trial_completeness
    swapped = False

    def replace_before_completeness(**kwargs):
        nonlocal swapped
        if not swapped:
            replacement = journal.with_name("attempts-swapped.jsonl")
            replacement.write_bytes(swapped_bytes)
            os.replace(replacement, journal)
            swapped = True
        return original(**kwargs)

    monkeypatch.setattr(
        R, "assert_autonomous_trial_completeness", replace_before_completeness,
    )
    with pytest.raises(R.TrialRegistryError, match=r"\[terminal-completeness\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert swapped is True


def test_m31_same_inode_journal_rewrite_restore_cannot_compose_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    journal = reports[0].with_name("attempts.jsonl")
    original_bytes = journal.read_bytes()
    original_inode = journal.stat().st_ino
    events, report = _load_report_bundle(reports[0])
    swapped_events = copy.deepcopy(events)
    for field in ("prereg_commit", "measurement_head", "manifest_sha256"):
        swapped_events[0].pop(field)
    swapped_bytes = b"".join(_canonical(event) + b"\n" for event in swapped_events)
    report["attempt_journal_sha256"] = hashlib.sha256(swapped_bytes).hexdigest()
    reports[0].write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    original = R.assert_autonomous_trial_completeness
    rewritten = False

    def rewrite_same_inode_before_completeness(**kwargs):
        nonlocal rewritten
        with journal.open("r+b") as stream:
            stream.seek(0)
            stream.truncate()
            stream.write(swapped_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        rewritten = True
        try:
            assert Path(kwargs["attempt_journal"]) != journal
            return original(**kwargs)
        finally:
            with journal.open("r+b") as stream:
                stream.seek(0)
                stream.truncate()
                stream.write(original_bytes)
                stream.flush()
                os.fsync(stream.fileno())

    monkeypatch.setattr(
        R,
        "assert_autonomous_trial_completeness",
        rewrite_same_inode_before_completeness,
    )
    with pytest.raises(R.TrialRegistryError, match=r"\[terminal-completeness\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
    assert rewritten is True
    assert journal.stat().st_ino == original_inode
    assert journal.read_bytes() == original_bytes


def test_literal_pathspec_registry_history_cannot_be_hidden(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "literal-manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "literal"))
    _commit(repo, "literal manifest", manifest_path)
    registry = repo / ":(glob)does-not-match"
    _append_fixture_registration(
        manifest_path=manifest_path,
        repository_root=repo,
        registry_path=registry,
    )
    measurement = _commit(repo, "literal registry", registry)
    manifest = R.load_trial_manifest(manifest_path)
    original = registry.read_bytes()
    rewritten = _registration_value(manifest)
    rewritten["trials"][0]["campaign_id"] += "-rewritten"
    _write_registry(registry, rewritten)
    _commit(repo, "rewrite literal registry", registry)
    registry.write_bytes(original)
    _commit(repo, "restore literal registry", registry)
    reports = _reports(repo / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] "):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_git_environment_is_allowlisted_and_literal_pathspec_is_forced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    hostile = {
        "GIT_DIR": "/foreign/git-dir",
        "GIT_GRAFT_FILE": "/foreign/grafts",
        "GIT_SHALLOW_FILE": "/foreign/shallow",
        "GIT_CONFIG": "/foreign/config",
        "GIT_CONFIG_PARAMETERS": "'core.filemode=false'",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.filemode",
        "GIT_CONFIG_VALUE_0": "false",
        "GIT_DEFAULT_HASH": "sha256",
    }
    for key, value in hostile.items():
        monkeypatch.setenv(key, value)
    env = R._git_env()
    assert not (set(hostile) & set(env))
    assert env["GIT_LITERAL_PATHSPECS"] == "1"
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    _repo, head = _init_repo(tmp_path)
    assert R._COMMIT_RE.fullmatch(head) is not None


def test_manifest_committed_symlink_mode_is_rejected(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    target = repo / "manifest-target.json"
    _write_manifest(target, _manifest_value(prereg, "symlink-manifest"))
    manifest_path = repo / "manifest.json"
    manifest_path.symlink_to(target.name)
    _commit(repo, "symlink manifest", target, manifest_path)
    manifest_bytes = target.read_bytes()
    manifest_path.unlink()
    manifest_path.write_bytes(manifest_bytes)
    with pytest.raises(R.TrialRegistryError, match=r"\[committed-mode\] "):
        _append_fixture_registration(
            manifest_path=manifest_path,
            repository_root=repo,
            registry_path=repo / "registry.jsonl",
            prepare_binding=False,
        )


def test_registry_committed_symlink_mode_is_rejected(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "symlink-registry"))
    _commit(repo, "manifest", manifest_path)
    manifest = R.load_trial_manifest(manifest_path)
    target = repo / "registry-target.jsonl"
    _write_registry(target, _registration_value(manifest))
    registry = repo / "registry.jsonl"
    registry.symlink_to(target.name)
    _commit(repo, "symlink registry", target, registry)
    registry_bytes = target.read_bytes()
    registry.unlink()
    registry.write_bytes(registry_bytes)
    trial = manifest.trials[0]
    with pytest.raises(R.TrialRegistryError, match=r"\[committed-mode\] "):
        R.load_launch_binding(
            manifest_path=manifest_path,
            trial_id=trial.trial_id,
            workloads=[R.HOLDOUT_BINDINGS[trial.holdout]["workload"]],
            repository_root=repo,
            registry_path=registry,
        )


def test_registry_git_component_is_rejected_before_file_creation(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "git-component"))
    _commit(repo, "manifest", manifest_path)
    registry = repo / ".git" / "info" / "trial-registry.jsonl"
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-path\] "):
        _append_fixture_registration(
            manifest_path=manifest_path,
            repository_root=repo,
            registry_path=registry,
        )
    assert not registry.exists()


def test_append_componentwise_open_rejects_parent_symlink_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "parent-swap"))
    _commit(repo, "manifest", manifest_path)
    inner = repo / "safe" / "inner"
    inner.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    registry = inner / "registry.jsonl"
    original_open = R.os.open
    swapped = False

    def swap_parent(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if path == "inner" and dir_fd is not None and not swapped:
            inner.rename(inner.with_name("inner-held"))
            inner.symlink_to(outside, target_is_directory=True)
            swapped = True
        if dir_fd is None:
            return original_open(path, flags, mode)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(R.os, "open", swap_parent)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-path\] "):
        _append_fixture_registration(
            manifest_path=manifest_path,
            repository_root=repo,
            registry_path=registry,
        )
    assert swapped is True
    assert not (outside / "registry.jsonl").exists()


def test_append_rebinds_target_inode_after_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(
        manifest_b_path,
        _manifest_value(manifest_a.prereg_commit, "rebind-b"),
    )
    _commit(repo, "manifest-b", manifest_b_path)
    original_bytes = registry.read_bytes()
    original_flock = R.fcntl.flock
    replaced = False

    def replace_after_lock(fd: int, operation: int) -> None:
        nonlocal replaced
        original_flock(fd, operation)
        replacement = registry.with_name("registry-replacement.jsonl")
        replacement.write_bytes(original_bytes)
        os.replace(replacement, registry)
        replaced = True

    monkeypatch.setattr(R.fcntl, "flock", replace_after_lock)
    with pytest.raises(R.TrialRegistryError, match=r"\[append-state\] registry path changed"):
        _append_fixture_registration(
            manifest_path=manifest_b_path,
            repository_root=repo,
            registry_path=registry,
        )
    assert replaced is True
    assert registry.read_bytes() == original_bytes


def test_append_rebinds_parent_inode_after_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    manifest_b_path = repo / "manifest-parent-rebind.json"
    _write_manifest(
        manifest_b_path,
        _manifest_value(manifest_a.prereg_commit, "parent-rebind-b"),
    )
    _commit(repo, "manifest-parent-rebind", manifest_b_path)
    original_bytes = registry.read_bytes()
    moved_parent = tmp_path / "registry-parent-moved-outside"
    original_flock = R.fcntl.flock
    moved = False

    def move_parent_after_lock(fd: int, operation: int) -> None:
        nonlocal moved
        original_flock(fd, operation)
        registry.parent.rename(moved_parent)
        registry.parent.mkdir()
        moved = True

    monkeypatch.setattr(R.fcntl, "flock", move_parent_after_lock)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"\[append-state\] registry parent changed",
    ):
        _append_fixture_registration(
            manifest_path=manifest_b_path,
            repository_root=repo,
            registry_path=registry,
        )
    assert moved is True
    assert not registry.exists()
    assert (moved_parent / registry.name).read_bytes() == original_bytes


def test_registry_history_rejects_git_mv_then_restore(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    moved = registry.with_name("registry-moved.jsonl")
    assert _run(
        repo, "mv", "--", str(registry.relative_to(repo)), str(moved.relative_to(repo)),
    ).returncode == 0
    assert _run(repo, "commit", "-q", "-m", "move registry").returncode == 0
    assert _run(
        repo, "mv", "--", str(moved.relative_to(repo)), str(registry.relative_to(repo)),
    ).returncode == 0
    assert _run(repo, "commit", "-q", "-m", "restore registry path").returncode == 0
    reports = _reports(repo / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry path was deleted"):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_registry_history_rejects_merge_dag_with_deleted_parent(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    original = registry.read_bytes()
    main_branch = _run(repo, "branch", "--show-current").stdout.strip()
    assert _run(repo, "checkout", "-q", "-b", "delete-side").returncode == 0
    assert _run(repo, "rm", "-q", "--", str(registry.relative_to(repo))).returncode == 0
    assert _run(repo, "commit", "-q", "-m", "delete registry on side").returncode == 0
    assert _run(repo, "checkout", "-q", main_branch).returncode == 0
    main_anchor = repo / "main-anchor.txt"
    main_anchor.write_text("main\n", encoding="utf-8")
    _commit(repo, "main anchor", main_anchor)
    merge = _run(repo, "merge", "-q", "--no-ff", "-m", "merge deletion", "delete-side")
    assert merge.returncode == 0, merge.stderr
    assert not registry.exists()
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_bytes(original)
    _commit(repo, "restore registry after merge", registry)
    reports = _reports(repo / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry path was deleted"):
        _accept(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def _attempt_slots(manifest: R.TrialManifest, *, repeats_for_first: int = 1) -> list[dict]:
    slots: list[dict] = []
    for trial_index, trial in enumerate(manifest.trials):
        repeats = repeats_for_first if trial_index == 0 else 1
        for attempt_index in range(repeats):
            identity = {
                "trial_id": trial.trial_id,
                "arm": trial.arm,
                "holdout": trial.holdout,
                "campaign_id": trial.campaign_id,
                "prereg_generation": 13,
                "replicate_index": 0,
                "attempt_index": attempt_index,
            }
            slots.append({
                "slot_id": f"{trial.trial_id}-r0-a{attempt_index}",
                **identity,
                "schedule_row_sha256": hashlib.sha256(_canonical(identity)).hexdigest(),
            })
    return slots


def _attempt_fixture(
    tmp_path: Path,
    *,
    repeats_for_first: int = 1,
    extra_replicate: bool = False,
    legacy_genesis: bool = False,
) -> tuple[Path, Path, R.TrialManifest, Path, str, str, str, list[dict]]:
    repo, seed = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(seed, "attempt-fixture"))
    _commit(repo, "attempt manifest", manifest_path)
    manifest = R.load_trial_manifest(manifest_path)
    slots = _attempt_slots(manifest, repeats_for_first=repeats_for_first)
    if extra_replicate:
        base = dict(slots[0])
        base.update({
            "slot_id": f"{base['trial_id']}-r1-a0",
            "replicate_index": 1,
            "attempt_index": 0,
        })
        base["schedule_row_sha256"] = hashlib.sha256(
            _canonical({
                key: base[key]
                for key in (
                    "trial_id", "arm", "holdout", "campaign_id",
                    "prereg_generation", "replicate_index", "attempt_index",
                )
            })
        ).hexdigest()
        slots.append(base)
    registry = R.create_attempt_registry_genesis(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest_sha256=manifest.sha256,
        freeze_id="freeze-attempt-fixture",
        prereg_generation=13,
        slots=slots,
    )
    if legacy_genesis:
        legacy_rows = [json.loads(line) for line in registry.read_text().splitlines()]
        legacy_genesis_row = legacy_rows[0]
        legacy_genesis_row["schema_version"] = "p3-8c-attempt-registry/v1"
        for field in ("event_index", "previous_event_sha256", "event_sha256"):
            legacy_genesis_row.pop(field, None)
        for slot in legacy_genesis_row["slots"]:
            slot.pop("prereg_generation")
        registry.write_bytes(_canonical(legacy_genesis_row) + b"\n")
    content_commit = _commit(repo, "attempt genesis", registry)
    genesis_bytes = registry.read_bytes()
    genesis = json.loads(genesis_bytes.splitlines()[0])
    binding_path = repo / R.DEFAULT_EFFECTIVE_BINDING_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_bytes(R._canonical_json_bytes({
        "schema_version": R.EFFECTIVE_BINDING_SCHEMA_VERSION,
        "prereg_content_commit": content_commit,
        "manifest_path": "manifest.json",
        "manifest_sha256": manifest.sha256,
        "freeze_id": genesis["freeze_id"],
        "attempt_registry_path": R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "attempt_registry_initial_sha256": hashlib.sha256(
            genesis_bytes
        ).hexdigest(),
    }))
    effective_commit = _commit(repo, "effective binding parent", binding_path)
    return (
        repo,
        manifest_path,
        manifest,
        registry,
        content_commit,
        effective_commit,
        "freeze-attempt-fixture",
        slots,
    )


def _reserve_attempt(
    repo: Path,
    registry: Path,
    content_commit: str,
    effective_commit: str,
    freeze_id: str,
    slot: dict,
    *,
    run_start_receipt_sha256: str | None = None,
) -> R.AttemptSlotCapability:
    return R.reserve_attempt_slot(
        repository_root=repo,
        registry_path=registry,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        prereg_content_commit=content_commit,
        prereg_effective_commit=effective_commit,
        run_start_receipt_sha256=(
            run_start_receipt_sha256
            or hashlib.sha256(
                f"run-start:{slot['slot_id']}".encode("ascii")
            ).hexdigest()
        ),
        process_identity={
            "pid": 101,
            "starttime": "fixture-start",
            "execution_uuid": f"exec-{slot['slot_id']}",
        },
        started_at="2026-08-18T00:00:00+00:00",
    )


def _reserve_formal_attempt(
    repo: Path,
    registry: Path,
    content_commit: str,
    effective_commit: str,
    freeze_id: str,
    slot: dict,
) -> R.AttemptSlotCapability:
    return R.reserve_formal_attempt_slot(
        repository_root=repo,
        registry_path=registry,
        freeze_id=freeze_id,
        slot_id=slot["slot_id"],
        prereg_content_commit=content_commit,
        prereg_effective_commit=effective_commit,
        run_start_receipt_sha256=hashlib.sha256(
            f"formal-run-start:{slot['slot_id']}".encode("ascii")
        ).hexdigest(),
        process_identity={
            "pid": 101,
            "starttime": "formal-fixture-start",
            "execution_uuid": f"formal-exec-{slot['slot_id']}",
        },
        started_at="2026-08-18T00:00:00+00:00",
    )


def _classify_and_terminal(
    capability: R.AttemptSlotCapability,
    *,
    failure_reason: str | None,
    terminal_status: str,
    report_sha256: str | None = None,
    raw_output_sha256: str | None = None,
    begin_observation: bool = False,
) -> None:
    R.classify_attempt(
        capability,
        pre_observation_failure_reason=failure_reason,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    effective_report_sha256 = (
        report_sha256
        if report_sha256 is not None
        else (
            hashlib.sha256(f"report:{capability.slot_id}".encode("ascii")).hexdigest()
            if terminal_status != "not-consumed" else None
        )
    )
    if (
        begin_observation
        or terminal_status == "observed"
        or (terminal_status == "terminal-failure" and effective_report_sha256 is not None)
    ):
        R.begin_attempt_observation(capability)
    R.record_attempt_terminal(
        capability,
        terminal_status=terminal_status,
        raw_output_sha256=raw_output_sha256 or hashlib.sha256(
            f"raw:{capability.slot_id}".encode("ascii")
        ).hexdigest(),
        report_sha256=effective_report_sha256,
        observation_sha256=(
            hashlib.sha256(f"observation:{capability.slot_id}".encode("ascii")).hexdigest()
            if terminal_status == "observed" else None
        ),
        primary_value=1.0 if terminal_status == "observed" else None,
        finished_at="2026-08-18T00:00:02+00:00",
    )


def _rechain_attempt_rows(rows: list[dict]) -> list[dict]:
    """Recompute v2/v3 chain fields after an intentional semantic mutation."""
    previous = "0" * 64
    for index, row in enumerate(rows):
        if row.get("schema_version") not in {
            "p3-8c-attempt-registry/v2",
            R.ATTEMPT_REGISTRY_SCHEMA_VERSION,
        }:
            if index == 0:
                previous = "0" * 64
            continue
        rebuilt = R._attempt_v2_event_row(
            row,
            event_index=index,
            previous_event_sha256=previous,
        )
        row.clear()
        row.update(rebuilt)
        previous = row["event_sha256"]
    return rows


def _rewrite_attempt_rows(registry: Path, rows: list[dict]) -> None:
    _rechain_attempt_rows(rows)
    _write_attempt_rows(registry, rows)


def _write_attempt_rows(registry: Path, rows: list[dict]) -> None:
    registry.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))


def _append_legacy_v1_attempt_rows(
    repo: Path,
    registry: Path,
    *,
    content_commit: str,
    effective_commit: str,
    freeze_id: str,
    slot: dict,
) -> None:
    """Build a complete pre-v2 registry for the v2 reader compatibility test."""
    schema_version = "p3-8c-attempt-registry/v1"
    process_identity = {
        "pid": 101,
        "starttime": "fixture-start",
        "execution_uuid": f"exec-{slot['slot_id']}",
    }
    run_start_receipt_sha256 = "c" * 64
    start = {
        "schema_version": schema_version,
        "event": "start",
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "prereg_content_commit": content_commit,
        "prereg_effective_commit": effective_commit,
        "run_start_receipt_sha256": run_start_receipt_sha256,
        "process_identity": process_identity,
        "schedule_row_sha256": slot["schedule_row_sha256"],
        "started_at": "2026-08-18T00:00:00+00:00",
    }
    capability_digest_sha256 = R._attempt_capability_digest(
        freeze_id=freeze_id,
        slot=slot,
        prereg_content_commit=content_commit,
        prereg_effective_commit=effective_commit,
        schema_version=schema_version,
    )
    receipt = {
        "schema_version": schema_version,
        "event": "classification-receipt",
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "capability_digest_sha256": capability_digest_sha256,
        "authority_id": "fixture-authority",
        "authority_policy_sha256": "a" * 64,
        "external_evidence_sha256": "b" * 64,
        "classified_at": "2026-08-18T00:00:01+00:00",
        "failure_reason": None,
        "performance_output_read": False,
    }
    receipt_bytes = _canonical(receipt) + b"\n"
    receipt_digest = hashlib.sha256(receipt_bytes).hexdigest()
    receipt_path = (
        repo / "output/s8c-trial-registry/classification-receipts"
        / f"{receipt_digest}.json"
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(receipt_bytes)
    classification = {
        **receipt,
        "event": "classification",
        "prereg_content_commit": content_commit,
        "prereg_effective_commit": effective_commit,
        "classification_receipt_sha256": receipt_digest,
    }
    terminal = {
        "schema_version": schema_version,
        "event": "terminal",
        "freeze_id": freeze_id,
        "slot_id": slot["slot_id"],
        "prereg_content_commit": content_commit,
        "prereg_effective_commit": effective_commit,
        "classification_receipt_sha256": receipt_digest,
        "terminal_status": "observed",
        "raw_output_sha256": "d" * 64,
        "report_sha256": "e" * 64,
        "observation_sha256": "f" * 64,
        "primary_value": 1.0,
        "failure_reason": None,
        "finished_at": "2026-08-18T00:00:02+00:00",
        "schedule_row_sha256": slot["schedule_row_sha256"],
        "process_identity": process_identity,
    }
    existing = [json.loads(line) for line in registry.read_text().splitlines()]
    _write_attempt_rows(registry, existing + [start, classification, terminal])


def test_manifest_has_no_commit_self_reference(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    _write_manifest(path, _manifest_value(prereg, "manifest-binding"))
    manifest = R.load_trial_manifest(path)
    assert "prereg_commit" in R._MANIFEST_KEYS
    assert manifest.prereg_commit == prereg


def test_effective_binding_requires_manifest_blob_at_content_commit(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "binding-missing"))
    with pytest.raises(R.TrialRegistryError, match=r"\[effective-binding\]"):
        R.load_effective_binding_at_commit(repo, prereg, manifest_path)


def test_effective_commit_requires_exact_single_parent(tmp_path: Path) -> None:
    repo, root = _init_repo(tmp_path)
    child_marker = repo / "child.txt"
    child_marker.write_text("child\n", encoding="utf-8")
    child = _commit(repo, "child", child_marker)
    with pytest.raises(R.TrialRegistryError, match=r"\[ancestry\]"):
        R.assert_effective_commit_exact_parent(
            repo, content_commit=child, effective_commit=root,
        )


def test_effective_commit_rejects_root_commit(tmp_path: Path) -> None:
    repo, root = _init_repo(tmp_path)
    with pytest.raises(R.TrialRegistryError, match=r"root commit"):
        R.assert_effective_commit_exact_parent(
            repo, content_commit=root, effective_commit=root,
        )


def test_effective_commit_rejects_other_parent(tmp_path: Path) -> None:
    repo, root = _init_repo(tmp_path)
    first_marker = repo / "first.txt"
    first_marker.write_text("first\n", encoding="utf-8")
    first = _commit(repo, "first", first_marker)
    second_marker = repo / "second.txt"
    second_marker.write_text("second\n", encoding="utf-8")
    second = _commit(repo, "second", second_marker)
    with pytest.raises(R.TrialRegistryError, match=r"exact content commit"):
        R.assert_effective_commit_exact_parent(
            repo, content_commit=root, effective_commit=second,
        )
    assert first != second


def test_effective_commit_rejects_merge_commit(tmp_path: Path) -> None:
    repo, root = _init_repo(tmp_path)
    main_marker = repo / "main.txt"
    main_marker.write_text("main\n", encoding="utf-8")
    main = _commit(repo, "main", main_marker)
    branch = _run(repo, "branch", "side")
    assert branch.returncode == 0, branch.stderr
    assert _run(repo, "checkout", "-q", "side").returncode == 0
    side_marker = repo / "side.txt"
    side_marker.write_text("side\n", encoding="utf-8")
    _commit(repo, "side", side_marker)
    assert _run(repo, "checkout", "-q", "-").returncode == 0
    merge = _run(repo, "merge", "--no-ff", "-q", "-m", "merge", "side")
    assert merge.returncode == 0, merge.stderr
    merge_commit = _head(repo)
    with pytest.raises(R.TrialRegistryError, match=r"merge commit"):
        R.assert_effective_commit_exact_parent(
            repo, content_commit=main, effective_commit=merge_commit,
        )
    assert root != merge_commit


def _effective_binding_fixture(
    tmp_path: Path,
    *,
    manifest_sha256: str | None = None,
    working_manifest_mismatch: bool = False,
) -> tuple[Path, Path, R.TrialManifest, str, str]:
    repo, seed = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(seed, "effective-fixture"))
    _commit(repo, "effective manifest", manifest_path)
    manifest = R.load_trial_manifest(manifest_path)
    slots = _attempt_slots(manifest)
    genesis = R.create_attempt_registry_genesis(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest_sha256=manifest.sha256,
        freeze_id="freeze-effective-fixture",
        prereg_generation=13,
        slots=slots,
    )
    content = _commit(repo, "content and genesis", manifest_path, genesis)
    binding_value = {
        "schema_version": R.EFFECTIVE_BINDING_SCHEMA_VERSION,
        "prereg_content_commit": content,
        "manifest_path": "manifest.json",
        "manifest_sha256": manifest_sha256 or manifest.sha256,
        "freeze_id": "freeze-effective-fixture",
        "attempt_registry_path": R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "attempt_registry_initial_sha256": hashlib.sha256(
            genesis.read_bytes()
        ).hexdigest(),
    }
    binding_path = repo / R.DEFAULT_EFFECTIVE_BINDING_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_bytes(R._canonical_json_bytes(binding_value))
    effective = _commit(repo, "effective binding", binding_path)
    if working_manifest_mismatch:
        changed = json.loads(manifest_path.read_text(encoding="utf-8"))
        changed["trials"][0]["campaign_id"] += "-working-mismatch"
        _write_manifest(manifest_path, changed)
    return repo, manifest_path, manifest, content, effective


def test_effective_binding_parent_fixture_rejects_manifest_content_mismatch(
    tmp_path: Path,
) -> None:
    repo, manifest_path, _manifest, content, effective = _effective_binding_fixture(
        tmp_path, working_manifest_mismatch=True,
    )
    with pytest.raises(R.TrialRegistryError, match=r"loaded manifest differs"):
        R.load_effective_binding_at_commit(repo, effective, manifest_path)
    R.assert_effective_commit_exact_parent(
        repo, content_commit=content, effective_commit=effective,
    )


def test_effective_binding_rejects_manifest_sha256_mismatch(tmp_path: Path) -> None:
    repo, manifest_path, _manifest, _content, effective = _effective_binding_fixture(
        tmp_path, manifest_sha256="f" * 64,
    )
    with pytest.raises(R.TrialRegistryError, match=r"manifest blob differs"):
        R.load_effective_binding_at_commit(repo, effective, manifest_path)


def test_effective_commit_rejects_noncanonical_commit_arguments(tmp_path: Path) -> None:
    repo, root = _init_repo(tmp_path)
    for bad in ("HEAD", root[:8], root.upper()):
        with pytest.raises(R.TrialRegistryError, match=r"40-digit lowercase"):
            R.assert_effective_commit_exact_parent(
                repo, content_commit=root, effective_commit=bad,
            )


def test_effective_commit_rejects_parent_query_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, root = _init_repo(tmp_path)
    marker = repo / "query-failure.txt"
    marker.write_text("query\n", encoding="utf-8")
    child = _commit(repo, "query failure child", marker)
    original_git = R._git

    def fail_parent_query(repository_root: Path, args):
        if tuple(args) == ("rev-list", "--parents", "-n", "1", child):
            return subprocess.CompletedProcess(
                args=["git"], returncode=2, stdout=b"", stderr=b"broken"
            )
        return original_git(repository_root, args)

    monkeypatch.setattr(R, "_git", fail_parent_query)
    with pytest.raises(R.TrialRegistryError, match=r"rev-list --parents failed"):
        R.assert_effective_commit_exact_parent(
            repo, content_commit=root, effective_commit=child,
        )


def test_effective_commit_rejects_graft_file(tmp_path: Path) -> None:
    repo, root = _init_repo(tmp_path)
    graft_result = _run(repo, "rev-parse", "--git-path", "info/grafts")
    assert graft_result.returncode == 0
    graft = Path(graft_result.stdout.strip())
    if not graft.is_absolute():
        graft = repo / graft
    graft.parent.mkdir(parents=True, exist_ok=True)
    graft.write_text("", encoding="ascii")
    with pytest.raises(R.TrialRegistryError, match=r"graft"):
        R.assert_effective_commit_exact_parent(
            repo, content_commit=root, effective_commit=root,
        )


def test_effective_commit_rejects_replace_ref(tmp_path: Path) -> None:
    repo, root = _init_repo(tmp_path)
    marker = repo / "replace.txt"
    marker.write_text("replace\n", encoding="utf-8")
    child = _commit(repo, "replace child", marker)
    replaced = _run(repo, "replace", child, root)
    assert replaced.returncode == 0, replaced.stderr
    with pytest.raises(R.TrialRegistryError, match=r"replace refs"):
        R.assert_effective_commit_exact_parent(
            repo, content_commit=root, effective_commit=child,
        )


def test_effective_commit_must_ancestor_measurement_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, root = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(root, "ancestor-check"))
    marker = repo / "effective.txt"
    marker.write_text("effective\n", encoding="utf-8")
    effective = _commit(repo, "effective", marker)
    binding = R.PreregEffectiveBinding(
        schema_version=R.EFFECTIVE_BINDING_SCHEMA_VERSION,
        prereg_content_commit=root,
        manifest_path="manifest.json",
        manifest_sha256="a" * 64,
        freeze_id="freeze",
        attempt_registry_path=R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        attempt_registry_initial_sha256="b" * 64,
        raw_bytes=b"{}",
    )
    monkeypatch.setattr(R, "load_effective_binding_at_commit", lambda *args, **kwargs: binding)
    with pytest.raises(R.TrialRegistryError, match=r"effective_commit.*ancestor"):
        R.validate_preregistration_binding(
            repo,
            manifest_path=manifest_path,
            effective_commit=effective,
            measurement_commit=root,
        )


def _registration_with_trials(
    manifest: R.TrialManifest,
    trials: tuple[R.TrialSpec, ...],
    *,
    effective_commit: str = "e" * 40,
) -> R.TrialRegistration:
    return R.TrialRegistration(
        schema_version=R.REGISTRATION_SCHEMA_VERSION,
        manifest_sha256=manifest.sha256,
        prereg_commit=manifest.prereg_commit,
        prereg_content_commit=manifest.prereg_commit,
        prereg_effective_commit=effective_commit,
        trials=trials,
    )


def test_acceptance_rejects_missing_registry_trial(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    _write_manifest(path, _manifest_value(prereg, "set-missing"))
    manifest = R.load_trial_manifest(path)
    registration = _registration_with_trials(manifest, manifest.trials[:-1])
    with pytest.raises(R.TrialRegistryError, match=r"trial sets differ"):
        R._assert_manifest_registry_trial_set(manifest, registration)


def test_acceptance_rejects_extra_registry_trial(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    _write_manifest(path, _manifest_value(prereg, "set-extra"))
    manifest = R.load_trial_manifest(path)
    extra = dataclasses.replace(manifest.trials[-1], trial_id="extra-trial")
    registration = _registration_with_trials(manifest, manifest.trials[:-1] + (extra,))
    with pytest.raises(R.TrialRegistryError, match=r"trial sets differ"):
        R._assert_manifest_registry_trial_set(manifest, registration)


@pytest.mark.parametrize("field", ["arm", "holdout", "campaign_id", "generations"])
def test_acceptance_rejects_registry_canonical_tuple_mutation(
    tmp_path: Path, field: str,
) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / f"manifest-{field}.json"
    _write_manifest(path, _manifest_value(prereg, f"tuple-{field}"))
    manifest = R.load_trial_manifest(path)
    trial = manifest.trials[0]
    replacement = {
        "arm": "off" if trial.arm == "on" else "on",
        "holdout": "H2" if trial.holdout == "H1" else "H1",
        "campaign_id": trial.campaign_id + "-changed",
        "generations": 3,
    }[field]
    mutated = dataclasses.replace(trial, **{field: replacement})
    registration = _registration_with_trials(manifest, (mutated,) + manifest.trials[1:])
    with pytest.raises(R.TrialRegistryError, match=r"trial sets differ"):
        R._assert_manifest_registry_trial_set(manifest, registration)


def test_acceptance_rejects_content_or_effective_commit_mismatch(tmp_path: Path) -> None:
    _repo, prereg = _init_repo(tmp_path)
    path = tmp_path / "manifest.json"
    _write_manifest(path, _manifest_value(prereg, "commit-mismatch"))
    manifest = R.load_trial_manifest(path)
    registration = dataclasses.replace(
        _registration_with_trials(manifest, manifest.trials),
        prereg_content_commit="f" * 40,
    )
    with pytest.raises(R.TrialRegistryError, match=r"no single exact"):
        R._find_registration_for_manifest((registration,), manifest)


def test_acceptance_rejects_content_commit_without_manifest_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, _manifest, _content, effective = _effective_binding_fixture(
        tmp_path,
    )
    binding = R.load_effective_binding_at_commit(repo, effective, manifest_path)
    tree = _run(repo, "rev-parse", f"{effective}^{{tree}}")
    assert tree.returncode == 0, tree.stderr
    unrelated = _run(
        repo,
        "commit-tree",
        tree.stdout.strip(),
        "-m",
        "unrelated content root",
    )
    assert unrelated.returncode == 0, unrelated.stderr
    invalid_binding = dataclasses.replace(
        binding,
        prereg_content_commit=unrelated.stdout.strip(),
    )
    monkeypatch.setattr(
        R,
        "load_effective_binding_at_commit",
        lambda *args, **kwargs: invalid_binding,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"manifest prereg_commit is not an ancestor of prereg_content_commit",
    ):
        R.validate_preregistration_binding(
            repo,
            manifest_path=manifest_path,
            effective_commit=effective,
            measurement_commit=effective,
        )


def test_attempt_registry_genesis_is_closed_before_first_performance_observation(
    tmp_path: Path,
) -> None:
    repo, _manifest_path, manifest, registry, _p, _c, _freeze, slots = _attempt_fixture(tmp_path)
    with pytest.raises(R.TrialRegistryError, match=r"create-only"):
        R.create_attempt_registry_genesis(
            repository_root=repo,
            manifest_path=repo / "manifest.json",
            manifest_sha256=manifest.sha256,
            freeze_id="freeze-attempt-fixture",
            prereg_generation=13,
            slots=slots,
        )
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    rows[0]["slots"].append(dict(rows[0]["slots"][0], slot_id="late-slot"))
    _rechain_attempt_rows(rows)
    with pytest.raises(R.TrialRegistryError, match=r"trial registry|slot"):
        R._load_attempt_registry_bytes(
            b"".join(_canonical(row) + b"\n" for row in rows)
        )


def _genesis_cli_fixture(
    tmp_path: Path,
) -> tuple[Path, Path, R.TrialManifest, Path, list[dict], list[str]]:
    repo, seed = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(seed, "genesis-cli"))
    _commit(repo, "genesis CLI manifest", manifest_path)
    manifest = R.load_trial_manifest(manifest_path)
    prereg_generation = 2
    slots = _attempt_slots(manifest)
    for slot in slots:
        slot["prereg_generation"] = prereg_generation
        slot["schedule_row_sha256"] = hashlib.sha256(_canonical({
            key: slot[key]
            for key in (
                "trial_id", "arm", "holdout", "campaign_id",
                "prereg_generation", "replicate_index", "attempt_index",
            )
        })).hexdigest()
    slots_path = repo / "slots.json"
    slots_path.write_bytes(_canonical(slots) + b"\n")
    argv = [
        "genesis",
        "--manifest", str(manifest_path),
        "--repo-root", str(repo),
        "--freeze-id", "freeze-genesis-cli",
        "--prereg-generation", str(prereg_generation),
        "--slots-file", str(slots_path),
    ]
    return repo, manifest_path, manifest, slots_path, slots, argv


def test_genesis_cli_derives_manifest_digest_and_creates_canonical_registry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _manifest_path, manifest, _slots_path, slots, argv = (
        _genesis_cli_fixture(tmp_path)
    )

    assert R.main(argv) == 0

    registry = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    registry_lines = registry.read_bytes().splitlines()
    assert len(registry_lines) == 1
    genesis = json.loads(registry_lines[0])
    assert genesis["event"] == "freeze"
    assert genesis["freeze_id"] == "freeze-genesis-cli"
    assert genesis["manifest_sha256"] == hashlib.sha256(
        manifest.raw_bytes
    ).hexdigest()
    assert genesis["slots"] == slots
    assert capsys.readouterr().out.encode("utf-8") == (
        _canonical({
            "attempt_registry_path": R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
            "manifest_sha256": manifest.sha256,
            "slot_count": len(slots),
        })
        + b"\n"
    )


def test_genesis_cli_rejects_second_creation_without_changing_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _manifest_path, _manifest, _slots_path, _slots, argv = (
        _genesis_cli_fixture(tmp_path)
    )
    assert R.main(argv) == 0
    capsys.readouterr()
    registry = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    original = registry.read_bytes()

    with pytest.raises(SystemExit) as excinfo:
        R.main(argv)

    assert excinfo.value.code == 2
    assert "create-only path already exists" in capsys.readouterr().err
    assert registry.read_bytes() == original


def test_genesis_cli_rejects_slot_generation_mismatch_before_creation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _manifest_path, _manifest, slots_path, slots, argv = (
        _genesis_cli_fixture(tmp_path)
    )
    for slot in slots:
        slot["prereg_generation"] = 3
        slot["schedule_row_sha256"] = hashlib.sha256(_canonical({
            key: slot[key]
            for key in (
                "trial_id", "arm", "holdout", "campaign_id",
                "prereg_generation", "replicate_index", "attempt_index",
            )
        })).hexdigest()
    slots_path.write_bytes(_canonical(slots) + b"\n")

    with pytest.raises(SystemExit) as excinfo:
        R.main(argv)

    assert excinfo.value.code == 2
    assert (
        "prereg_generation differs from slots[0].prereg_generation"
        in capsys.readouterr().err
    )
    assert not (repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH).exists()


@pytest.mark.parametrize(
    ("case", "expected_error"),
    [
        (
            "object",
            "[attempt-registry-genesis] slots file root must be an array",
        ),
        ("duplicate-key", "[json] duplicate object key: 'slot_id'"),
        ("non-utf8", "[json] slots file is not strict UTF-8 JSON"),
        ("non-finite", "[json] non-finite JSON number is forbidden: NaN"),
    ],
    ids=("object", "duplicate-key", "non-utf8", "non-finite"),
)
def test_genesis_cli_rejects_non_strict_slots_without_creating_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: str,
    expected_error: str,
) -> None:
    repo, _manifest_path, _manifest, slots_path, slots, argv = (
        _genesis_cli_fixture(tmp_path)
    )
    valid_slots_bytes = _canonical(slots)
    if case == "object":
        slots_bytes = b"{}\n"
    elif case == "duplicate-key":
        first_slot = _canonical(slots[0])
        duplicated_first_slot = (
            first_slot[:-1]
            + b',"slot_id":'
            + _canonical(slots[0]["slot_id"])
            + b"}"
        )
        slots_bytes = (
            b"["
            + duplicated_first_slot
            + b","
            + b",".join(_canonical(slot) for slot in slots[1:])
            + b"]\n"
        )
        assert json.loads(slots_bytes) == slots
    elif case == "non-utf8":
        slot_id_field = b'"slot_id":' + _canonical(slots[0]["slot_id"])
        assert valid_slots_bytes.count(slot_id_field) == 1
        slots_bytes = valid_slots_bytes.replace(
            slot_id_field, b'"slot_id":"\xff"', 1,
        ) + b"\n"
        permissive_slots = json.loads(slots_bytes.decode("latin-1"))
        assert permissive_slots[0] == {**slots[0], "slot_id": "ÿ"}
        assert permissive_slots[1:] == slots[1:]
    else:
        replicate_field = b'"replicate_index":0'
        assert replicate_field in valid_slots_bytes
        slots_bytes = valid_slots_bytes.replace(
            replicate_field, b'"replicate_index":NaN', 1,
        ) + b"\n"
        permissive_slots = json.loads(slots_bytes)
        assert permissive_slots[0]["replicate_index"] != permissive_slots[0][
            "replicate_index"
        ]
        assert {
            key: value
            for key, value in permissive_slots[0].items()
            if key != "replicate_index"
        } == {
            key: value
            for key, value in slots[0].items()
            if key != "replicate_index"
        }
        assert permissive_slots[1:] == slots[1:]
    slots_path.write_bytes(slots_bytes)

    with pytest.raises(SystemExit) as excinfo:
        R.main(argv)

    assert excinfo.value.code == 2
    assert expected_error in capsys.readouterr().err
    assert not (repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH).exists()


def test_genesis_cli_requires_prereg_generation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    _repo, _manifest_path, _manifest, _slots_path, _slots, argv = (
        _genesis_cli_fixture(tmp_path)
    )
    option_index = argv.index("--prereg-generation")
    del argv[option_index:option_index + 2]

    with pytest.raises(SystemExit) as excinfo:
        R.main(argv)

    assert excinfo.value.code == 2
    assert (
        "the following arguments are required: --prereg-generation"
        in capsys.readouterr().err
    )


def test_m1_v3_reader_accepts_single_generation_and_rejects_mixed_generation(
    tmp_path: Path,
) -> None:
    """M1 changes only the root-wide single-generation predicate."""
    repo, _manifest, _loaded, registry, _p, _c, _freeze, _slots = (
        _attempt_fixture(tmp_path)
    )
    valid_bytes = registry.read_bytes()
    assert R._load_attempt_registry_bytes(valid_bytes)[0]["slots"][0][
        "prereg_generation"
    ] == 13

    rows = [json.loads(line) for line in valid_bytes.splitlines()]
    rows[0]["slots"][-1]["prereg_generation"] = 14
    _rechain_attempt_rows(rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"^\[attempt-prereg-generation\] v3 genesis slots do not share "
            r"one positive prereg_generation$"
        ),
    ):
        R._load_attempt_registry_bytes(
            b"".join(_canonical(row) + b"\n" for row in rows)
        )


def test_attempt_registry_v2_reader_remains_explicitly_mapped(
    tmp_path: Path,
) -> None:
    repo, _manifest, _loaded, registry, _p, _c, _freeze, _slots = (
        _attempt_fixture(tmp_path)
    )
    rows = [json.loads(line) for line in registry.read_bytes().splitlines()]
    rows[0]["schema_version"] = "p3-8c-attempt-registry/v2"
    for slot in rows[0]["slots"]:
        slot.pop("prereg_generation")
    _rechain_attempt_rows(rows)

    checked = R._load_attempt_registry_bytes(
        b"".join(_canonical(row) + b"\n" for row in rows)
    )
    assert checked[0]["schema_version"] == "p3-8c-attempt-registry/v2"
    assert all("prereg_generation" not in slot for slot in checked[0]["slots"])


def test_v3_capability_digest_binds_generation_without_receipt_duplication() -> None:
    slot = {
        "slot_id": "generation-binding-r0-a0",
        "trial_id": "generation-binding",
        "arm": "on",
        "holdout": "H1",
        "campaign_id": "generation-binding-campaign",
        "prereg_generation": 13,
        "replicate_index": 0,
        "attempt_index": 0,
        "schedule_row_sha256": "a" * 64,
    }
    generation_13 = R._attempt_capability_digest(
        freeze_id="generation-binding-freeze",
        slot=slot,
        prereg_content_commit="1" * 40,
        prereg_effective_commit="2" * 40,
    )
    generation_14 = R._attempt_capability_digest(
        freeze_id="generation-binding-freeze",
        slot={**slot, "prereg_generation": 14},
        prereg_content_commit="1" * 40,
        prereg_effective_commit="2" * 40,
    )
    assert generation_13 != generation_14
    assert "prereg_generation" not in R._ATTEMPT_RECEIPT_KEYS


def test_m2_genesis_creator_requires_exact_slot_generation(
    tmp_path: Path,
) -> None:
    """M2 changes only the required argument-to-slot exact-match predicate."""
    repo, seed = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(seed, "m2-generation"))
    _commit(repo, "m2 manifest", manifest_path)
    manifest = R.load_trial_manifest(manifest_path)
    slots = _attempt_slots(manifest)
    with pytest.raises(
        R.TrialRegistryError,
        match=(
            r"^\[attempt-prereg-generation\] prereg_generation differs from "
            r"slots\[0\]\.prereg_generation$"
        ),
    ):
        R.create_attempt_registry_genesis(
            repository_root=repo,
            manifest_path=manifest_path,
            manifest_sha256=manifest.sha256,
            freeze_id="m2-generation",
            prereg_generation=14,
            slots=slots,
        )

    created = R.create_attempt_registry_genesis(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest_sha256=manifest.sha256,
        freeze_id="m2-generation",
        prereg_generation=13,
        slots=slots,
    )
    assert created.is_file()


def test_attempt_registry_consumes_only_next_slot_for_same_failed_repeat(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(
        tmp_path, repeats_for_first=3,
    )
    first, second, third = slots[:3]
    cap = _reserve_attempt(repo, registry, p, c, freeze, first)
    _classify_and_terminal(cap, failure_reason="wall-timeout", terminal_status="retryable-failure")
    next_cap = _reserve_attempt(repo, registry, p, c, freeze, second)
    assert next_cap.attempt_index == 1
    with pytest.raises(R.TrialRegistryError, match=r"next slot|retryable"):
        _reserve_attempt(repo, registry, p, c, freeze, third)


def test_attempt_registry_rejects_successful_rerun_and_score_selected_slot(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(
        tmp_path, repeats_for_first=2,
    )
    first, second = slots[:2]
    cap = _reserve_attempt(repo, registry, p, c, freeze, first)
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    with pytest.raises(R.TrialRegistryError, match=r"non-retryable|retryable"):
        _reserve_attempt(repo, registry, p, c, freeze, second)


def test_attempt_registry_rejects_observation_value_replacement(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    with pytest.raises(R.TrialRegistryError, match=r"more than one terminal|already"):
        R.record_attempt_terminal(
            cap,
            terminal_status="observed",
            raw_output_sha256="c" * 64,
            report_sha256="d" * 64,
            observation_sha256="e" * 64,
            primary_value=99.0,
            finished_at="2026-08-18T00:00:03+00:00",
        )


def test_attempt_registry_requires_exact_external_failure_reason(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        cap,
        pre_observation_failure_reason="correctness-failure",
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    with pytest.raises(R.TrialRegistryError, match=r"null matrix"):
        R.record_attempt_terminal(
            cap,
            terminal_status="retryable-failure",
            raw_output_sha256="c" * 64,
            report_sha256="d" * 64,
            observation_sha256=None,
            primary_value=None,
            finished_at="2026-08-18T00:00:02+00:00",
        )


def test_attempt_registry_classification_receipt_is_create_only(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    kwargs = {
        "pre_observation_failure_reason": "wall-timeout",
        "authority_id": "fixture-authority",
        "authority_policy_sha256": "a" * 64,
        "external_evidence_sha256": "b" * 64,
        "classified_at": "2026-08-18T00:00:01+00:00",
    }
    R.classify_attempt(cap, **kwargs)
    with pytest.raises(R.TrialRegistryError, match=r"create-only path already exists"):
        R.classify_attempt(cap, **kwargs)


def test_attempt_registry_classification_row_must_match_receipt(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason="wall-timeout", terminal_status="retryable-failure")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    classification = next(row for row in rows if row.get("event") == "classification")
    classification["authority_id"] = "tampered-authority"
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"classification receipt is not capability-bound",
    ):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_capability_digest_replacement(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason="wall-timeout", terminal_status="retryable-failure")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    classification = next(row for row in rows if row.get("event") == "classification")
    classification["capability_digest_sha256"] = "f" * 64
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"classification capability digest differs",
    ):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_observed_primary_value_null(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    terminal = next(row for row in rows if row.get("event") == "terminal")
    terminal["primary_value"] = None
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"observed null matrix"):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_second_root_in_full_history(tmp_path: Path) -> None:
    repo, manifest_path, manifest, _registry, _p, _c, _freeze, slots = _attempt_fixture(tmp_path)
    branch = _run(repo, "branch", "alternate-root")
    assert branch.returncode == 0, branch.stderr
    assert _run(repo, "checkout", "-q", "alternate-root").returncode == 0
    alternate = repo / "alternate.jsonl"
    alternate_rows = [
        json.loads(line)
        for line in (repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH).read_text().splitlines()
    ]
    alternate_rows[0]["freeze_id"] = "alternate-freeze"
    # The fixed path is already occupied on this branch, so put the second
    # root at another tracked path and let the all-ref scan reject it.
    alternate.write_bytes(_canonical(alternate_rows[0]) + b"\n")
    _commit(repo, "alternate attempt root", alternate)
    assert _run(repo, "checkout", "-q", "-").returncode == 0
    with pytest.raises(R.TrialRegistryError, match=r"alternate attempt registry genesis"):
        R.load_attempt_registry(repo)


def test_attempt_registry_replays_legacy_v1_registry_after_v2_upgrade(
    tmp_path: Path,
) -> None:
    repo, _manifest_path, _manifest, registry, p, c, freeze, slots = _attempt_fixture(
        tmp_path,
        legacy_genesis=True,
    )
    _append_legacy_v1_attempt_rows(
        repo,
        registry,
        content_commit=p,
        effective_commit=c,
        freeze_id=freeze,
        slot=slots[0],
    )
    rows = R.load_attempt_registry(repo)
    assert [row["event"] for row in rows] == [
        "freeze", "start", "classification", "terminal",
    ]
    assert all(
        row["schema_version"] == "p3-8c-attempt-registry/v1"
        for row in rows
    )


def test_attempt_registry_rejects_v1_row_under_v2_genesis(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        cap,
        pre_observation_failure_reason=None,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    v2_classification = next(
        row for row in rows if row.get("event") == "classification"
    )
    v1_classification = {
        "schema_version": "p3-8c-attempt-registry/v1",
        "event": "classification",
        "freeze_id": v2_classification["freeze_id"],
        "slot_id": v2_classification["slot_id"],
        "prereg_content_commit": v2_classification["prereg_content_commit"],
        "prereg_effective_commit": v2_classification["prereg_effective_commit"],
        "classification_receipt_sha256": v2_classification[
            "classification_receipt_sha256"
        ],
        "capability_digest_sha256": R._attempt_capability_digest(
            freeze_id=freeze,
            slot=slots[0],
            prereg_content_commit=p,
            prereg_effective_commit=c,
            schema_version="p3-8c-attempt-registry/v1",
        ),
        "authority_id": v2_classification["authority_id"],
        "authority_policy_sha256": v2_classification["authority_policy_sha256"],
        "external_evidence_sha256": v2_classification[
            "external_evidence_sha256"
        ],
        "classified_at": v2_classification["classified_at"],
        "failure_reason": None,
        "performance_output_read": False,
    }
    rows[rows.index(v2_classification)] = v1_classification
    _write_attempt_rows(registry, rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"schema_version differs from genesis",
    ):
        R._load_attempt_registry_bytes(registry.read_bytes())


def test_attempt_registry_rejects_terminal_failure_report_without_observation_start(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        cap,
        pre_observation_failure_reason=None,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"terminal-failure with a report requires observation-start",
    ):
        R.record_attempt_terminal(
            cap,
            terminal_status="terminal-failure",
            raw_output_sha256="c" * 64,
            report_sha256="d" * 64,
            observation_sha256=None,
            primary_value=None,
            finished_at="2026-08-18T00:00:02+00:00",
            failure_reason="producer-failure",
        )


def test_attempt_registry_accepts_pre_observation_terminal_failure_without_report(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        cap,
        pre_observation_failure_reason="producer-failure",
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    R.record_attempt_terminal(
        cap,
        terminal_status="terminal-failure",
        raw_output_sha256="c" * 64,
        report_sha256=None,
        observation_sha256=None,
        primary_value=None,
        finished_at="2026-08-18T00:00:02+00:00",
    )
    terminal = next(
        row for row in R.load_attempt_registry(repo) if row.get("event") == "terminal"
    )
    assert terminal["terminal_status"] == "terminal-failure"
    assert terminal["report_sha256"] is None
    assert terminal["observation_start_event_sha256"] is None


def test_attempt_registry_rejects_terminal_from_copied_capability_owner(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        cap,
        pre_observation_failure_reason="producer-failure",
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    copied = dataclasses.replace(cap)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"classification executor",
    ):
        R.record_attempt_terminal(
            copied,
            terminal_status="not-consumed",
            raw_output_sha256="c" * 64,
            report_sha256=None,
            observation_sha256=None,
            primary_value=None,
            finished_at="2026-08-18T00:00:02+00:00",
        )


@pytest.mark.parametrize("malformed", [[], {}], ids=["list", "dict"])
def test_attempt_registry_rejects_non_string_schema_version(
    malformed: object,
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, _p, _c, _freeze, _slots = _attempt_fixture(tmp_path)
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    rows[0]["schema_version"] = malformed
    _write_attempt_rows(registry, rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"attempt-registry-schema.*schema_version is unsupported",
    ):
        R._load_attempt_registry_bytes(registry.read_bytes())


def test_attempt_registry_rejects_v1_second_root_in_full_history(
    tmp_path: Path,
) -> None:
    repo, manifest_path, manifest, _registry, _p, _c, _freeze, _slots = _attempt_fixture(
        tmp_path,
    )
    branch = _run(repo, "branch", "alternate-v1-root")
    assert branch.returncode == 0, branch.stderr
    assert _run(repo, "checkout", "-q", "alternate-v1-root").returncode == 0
    alternate = repo / "alternate-v1.jsonl"
    alternate_rows = [
        json.loads(line)
        for line in (repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH).read_text().splitlines()
    ]
    alternate_genesis = alternate_rows[0]
    alternate_genesis["schema_version"] = "p3-8c-attempt-registry/v1"
    for field in ("event_index", "previous_event_sha256", "event_sha256"):
        alternate_genesis.pop(field, None)
    alternate.write_bytes(_canonical(alternate_genesis) + b"\n")
    _commit(repo, "alternate v1 attempt root", alternate)
    assert _run(repo, "checkout", "-q", "-").returncode == 0
    with pytest.raises(R.TrialRegistryError, match=r"alternate attempt registry genesis"):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_retry_after_observation_start(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(
        tmp_path,
        repeats_for_first=2,
    )
    first, second = slots[:2]
    cap = _reserve_attempt(repo, registry, p, c, freeze, first)
    _classify_and_terminal(
        cap,
        failure_reason="wall-timeout",
        terminal_status="retryable-failure",
        begin_observation=True,
    )
    with pytest.raises(R.TrialRegistryError, match=r"after observation|retry"):
        _reserve_attempt(repo, registry, p, c, freeze, second)


def test_attempt_registry_rejects_terminal_echo_mutation_after_rehash(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(
        cap,
        failure_reason="wall-timeout",
        terminal_status="retryable-failure",
    )
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    terminal = next(row for row in rows if row.get("event") == "terminal")
    terminal["pre_observation_failure_reason_echo"] = "tampered-echo"
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"echo differs|pre-observation"):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_reordered_observation_start_after_rehash(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    classification_index = next(
        index for index, row in enumerate(rows) if row.get("event") == "classification"
    )
    observation_index = next(
        index for index, row in enumerate(rows) if row.get("event") == "observation-start"
    )
    rows[classification_index], rows[observation_index] = (
        rows[observation_index], rows[classification_index],
    )
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"phase-order"):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_classification_seal_from_other_slot(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(
        tmp_path,
        extra_replicate=True,
    )
    first, other = slots[0], slots[-1]
    first_cap = _reserve_attempt(repo, registry, p, c, freeze, first)
    _reserve_attempt(repo, registry, p, c, freeze, other)
    R.classify_attempt(
        first_cap,
        pre_observation_failure_reason="wall-timeout",
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    seals = {
        row["slot_id"]: row["event_sha256"]
        for row in rows
        if row.get("event") == "pre-observation-seal"
    }
    classification = next(row for row in rows if row.get("event") == "classification")
    classification["pre_observation_seal_sha256"] = seals[other["slot_id"]]
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"seal binding"):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_legacy_performance_output_field_in_v2(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        cap,
        pre_observation_failure_reason=None,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    classification = next(row for row in rows if row.get("event") == "classification")
    classification["performance_output_read"] = False
    registry.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))
    with pytest.raises(R.TrialRegistryError, match=r"key set differs"):
        R._load_attempt_registry_bytes(registry.read_bytes())


def test_attempt_registry_records_seal_observation_and_monotonic_event_index(
    tmp_path: Path,
) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = R.load_attempt_registry(repo)
    assert [row["event"] for row in rows] == [
        "freeze", "start", "pre-observation-seal", "classification",
        "observation-start", "terminal",
    ]
    assert [row["event_index"] for row in rows] == list(range(len(rows)))
    seal = next(row for row in rows if row["event"] == "pre-observation-seal")
    classification = next(row for row in rows if row["event"] == "classification")
    observation = next(row for row in rows if row["event"] == "observation-start")
    terminal = next(row for row in rows if row["event"] == "terminal")
    assert classification["pre_observation_seal_sha256"] == seal["event_sha256"]
    assert observation["classification_event_sha256"] == classification["event_sha256"]
    assert terminal["observation_start_event_sha256"] == observation["event_sha256"]


def test_attempt_event_hash_matches_golden_vector() -> None:
    """Keep the v2 vector fixed while pinning the v3 generation-bound schema."""
    previous = (
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    v2_row = {
        "schema_version": "p3-8c-attempt-registry/v2",
        "event": "classification",
        "freeze_id": "freeze-golden-vector",
        "slot_id": "trial-r0-a0",
    }
    v2_sealed = R._attempt_v2_event_row(
        v2_row,
        event_index=3,
        previous_event_sha256=previous,
    )
    assert v2_sealed["event_sha256"] == (
        "c87db9b4449f49eaea673b567d0e1e5db6b4a9bf97075ca4c4dc5f3652a4b8f7"
    )

    # Generation enters the v3 capability digest (pinned in the adjacent
    # generation-binding test), while the v3 schema token distinguishes every
    # chained row carrying that capability contract.  This reduced vector has
    # no capability field, so the schema token is the direct changed byte.
    v3_sealed = R._attempt_v2_event_row(
        {**v2_row, "schema_version": R.ATTEMPT_REGISTRY_SCHEMA_VERSION},
        event_index=3,
        previous_event_sha256=previous,
    )
    assert v3_sealed["event_sha256"] == (
        "b71bbdd5f8253c6744907e9ab7aa100fd71736c335a4129cb31fb95059c0b3ab"
    )


def test_attempt_registry_rejects_event_sha256_tampering(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    classification = next(row for row in rows if row.get("event") == "classification")
    classification["event_sha256"] = "f" * 64
    _write_attempt_rows(registry, rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"event_sha256 differs from its payload",
    ):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_previous_event_sha256_tampering(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    classification = next(row for row in rows if row.get("event") == "classification")
    classification["previous_event_sha256"] = "e" * 64
    classification["event_sha256"] = R._attempt_event_sha256(classification)
    _write_attempt_rows(registry, rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"previous_event_sha256 differs from the preceding event",
    ):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_event_index_tampering(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    classification = next(row for row in rows if row.get("event") == "classification")
    classification["event_index"] = 99
    classification["event_sha256"] = R._attempt_event_sha256(classification)
    _write_attempt_rows(registry, rows)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"event_index is not monotonic",
    ):
        R.load_attempt_registry(repo)


def _attempt_report_for_acceptance(
    repo: Path,
    manifest: R.TrialManifest,
    slot: dict,
    content_commit: str,
    effective_commit: str,
    raw_output_sha256: str,
) -> tuple[Path, R.PreregEffectiveBinding]:
    report = {
        "trial_id": slot["trial_id"],
        "slot_id": slot["slot_id"],
        "prereg_content_commit": content_commit,
        "prereg_effective_commit": effective_commit,
        "status": "complete",
        "raw_output_sha256": raw_output_sha256,
        "observation_sha256": hashlib.sha256(
            f"observation:{slot['slot_id']}".encode("ascii")
        ).hexdigest(),
        "primary_value": 1.0,
    }
    report_path = repo / "reports" / f"{slot['slot_id']}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_bytes(_canonical(report))
    initial = (repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH).read_bytes().splitlines()[0] + b"\n"
    binding = R.PreregEffectiveBinding(
        schema_version=R.EFFECTIVE_BINDING_SCHEMA_VERSION,
        prereg_content_commit=content_commit,
        manifest_path="manifest.json",
        manifest_sha256=manifest.sha256,
        freeze_id="freeze-attempt-fixture",
        attempt_registry_path=R.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        attempt_registry_initial_sha256=hashlib.sha256(initial).hexdigest(),
        raw_bytes=b"{}",
    )
    return report_path, binding


def test_formal_reserve_rejects_target_inode_rebind_before_append(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _manifest_path, _manifest, registry, p, c, freeze, slots = (
        _attempt_fixture(tmp_path)
    )
    before = registry.read_bytes()
    detached = registry.with_name("detached-attempt-registry.jsonl")
    original_flock = R.fcntl.flock
    replaced = False

    def replace_target_after_lock(fd: int, operation: int) -> None:
        nonlocal replaced
        original_flock(fd, operation)
        if replaced:
            return
        os.link(registry, detached)
        replacement = registry.with_name("replacement-attempt-registry.jsonl")
        replacement.write_bytes(before)
        os.replace(replacement, registry)
        replaced = True

    monkeypatch.setattr(R.fcntl, "flock", replace_target_after_lock)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"attempt registry path changed after exclusive lock",
    ):
        _reserve_formal_attempt(repo, registry, p, c, freeze, slots[0])

    assert replaced is True
    assert registry.read_bytes() == before
    assert detached.read_bytes() == before


def test_formal_terminal_rejects_parent_inode_rebind_before_append(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _manifest_path, _manifest, registry, p, c, freeze, slots = (
        _attempt_fixture(tmp_path)
    )
    capability = _reserve_formal_attempt(
        repo, registry, p, c, freeze, slots[0]
    )
    R.classify_attempt(
        capability,
        pre_observation_failure_reason=None,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    before = registry.read_bytes()
    original_parent = registry.parent
    detached_parent = tmp_path / "detached-attempt-parent"
    original_flock = R.fcntl.flock
    replaced = False

    def replace_parent_after_lock(fd: int, operation: int) -> None:
        nonlocal replaced
        original_flock(fd, operation)
        if replaced:
            return
        original_parent.rename(detached_parent)
        original_parent.mkdir(parents=True)
        registry.write_bytes(before)
        replaced = True

    monkeypatch.setattr(R.fcntl, "flock", replace_parent_after_lock)
    with pytest.raises(
        R.TrialRegistryError,
        match=r"attempt registry parent changed after exclusive lock",
    ):
        R.record_formal_attempt_terminal(
            capability,
            terminal_status="not-consumed",
            raw_output_sha256="c" * 64,
            report_sha256=None,
            observation_sha256=None,
            primary_value=None,
            finished_at="2026-08-18T00:00:02+00:00",
        )

    assert replaced is True
    assert registry.read_bytes() == before
    assert (detached_parent / registry.name).read_bytes() == before


def test_formal_reserve_rejects_compat_mismatch_prefix_without_append(
    tmp_path: Path,
) -> None:
    repo, _manifest_path, _manifest, registry, p, c, freeze, slots = (
        _attempt_fixture(tmp_path, repeats_for_first=2)
    )
    first = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        first,
        pre_observation_failure_reason=None,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    R.record_attempt_terminal(
        first,
        terminal_status="retryable-failure",
        raw_output_sha256="c" * 64,
        report_sha256="d" * 64,
        observation_sha256=None,
        primary_value=None,
        finished_at="2026-08-18T00:00:02+00:00",
        failure_reason="preempted",
    )
    before = registry.read_bytes()

    with pytest.raises(
        R.TrialRegistryError,
        match=r"terminal failure reason differs from classification",
    ):
        _reserve_formal_attempt(repo, registry, p, c, freeze, slots[1])
    assert registry.read_bytes() == before


def test_formal_terminal_rejects_reason_replacement_without_append(
    tmp_path: Path,
) -> None:
    repo, _manifest_path, _manifest, registry, p, c, freeze, slots = (
        _attempt_fixture(tmp_path)
    )
    capability = _reserve_formal_attempt(
        repo, registry, p, c, freeze, slots[0]
    )
    R.classify_attempt(
        capability,
        pre_observation_failure_reason=None,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    before = registry.read_bytes()

    with pytest.raises(
        R.TrialRegistryError,
        match=r"terminal failure reason differs from classification",
    ):
        R.record_formal_attempt_terminal(
            capability,
            terminal_status="retryable-failure",
            raw_output_sha256="c" * 64,
            report_sha256="d" * 64,
            observation_sha256=None,
            primary_value=None,
            finished_at="2026-08-18T00:00:02+00:00",
            failure_reason="preempted",
        )
    assert registry.read_bytes() == before


@pytest.mark.parametrize(
    ("classification_reason", "terminal_status", "begin_observation"),
    [
        pytest.param("preempted", "retryable-failure", False,
                     id="matching-retryable"),
        pytest.param(None, "observed", True, id="observed-none"),
        pytest.param(None, "not-consumed", False, id="not-consumed-none"),
    ],
)
def test_formal_terminal_accepts_exact_positive_matrix(
    classification_reason: str | None,
    terminal_status: str,
    begin_observation: bool,
    tmp_path: Path,
) -> None:
    repo, _manifest_path, _manifest, registry, p, c, freeze, slots = (
        _attempt_fixture(tmp_path)
    )
    capability = _reserve_formal_attempt(
        repo, registry, p, c, freeze, slots[0]
    )
    R.classify_attempt(
        capability,
        pre_observation_failure_reason=classification_reason,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    if begin_observation:
        R.begin_attempt_observation(capability)
    R.record_formal_attempt_terminal(
        capability,
        terminal_status=terminal_status,
        raw_output_sha256="c" * 64,
        report_sha256=(
            "d" * 64
            if terminal_status in {"observed", "retryable-failure"}
            else None
        ),
        observation_sha256=(
            "e" * 64 if terminal_status == "observed" else None
        ),
        primary_value=1.0 if terminal_status == "observed" else None,
        finished_at="2026-08-18T00:00:02+00:00",
        failure_reason=classification_reason,
    )
    terminal = next(
        row for row in R.load_attempt_registry(repo)
        if row.get("event") == "terminal"
    )
    assert terminal["terminal_status"] == terminal_status
    assert terminal["failure_reason"] == classification_reason


def test_formal_acceptance_rejects_mismatch_that_legacy_accepts(
    tmp_path: Path,
) -> None:
    repo, manifest_path, manifest, registry, p, c, freeze, slots = (
        _attempt_fixture(tmp_path)
    )
    capability = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    R.classify_attempt(
        capability,
        pre_observation_failure_reason=None,
        authority_id="fixture-authority",
        authority_policy_sha256="a" * 64,
        external_evidence_sha256="b" * 64,
        classified_at="2026-08-18T00:00:01+00:00",
    )
    R.record_attempt_terminal(
        capability,
        terminal_status="retryable-failure",
        raw_output_sha256="c" * 64,
        report_sha256="d" * 64,
        observation_sha256=None,
        primary_value=None,
        finished_at="2026-08-18T00:00:02+00:00",
        failure_reason="preempted",
    )
    _unused_report, binding = _attempt_report_for_acceptance(
        repo, manifest, slots[0], p, c, "c" * 64,
    )

    legacy_rows = R.assert_attempt_registry_acceptance(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest=manifest,
        effective_binding=binding,
        effective_commit=c,
    )
    assert legacy_rows[-1]["failure_reason"] == "preempted"
    with pytest.raises(
        R.TrialRegistryError,
        match=r"terminal failure reason differs from classification",
    ):
        R.assert_formal_attempt_registry_acceptance(
            repository_root=repo,
            manifest_path=manifest_path,
            manifest=manifest,
            effective_binding=binding,
            effective_commit=c,
        )


def test_high_level_acceptance_routes_mismatch_to_formal_once_without_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    attempt_registry = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    rows = [
        json.loads(line)
        for line in attempt_registry.read_text(encoding="utf-8").splitlines()
    ]
    terminal = rows[-1]
    assert terminal.get("event") == "terminal"
    terminal["failure_reason"] = "different-producer-failure"
    _rewrite_attempt_rows(attempt_registry, rows)

    original_formal = R.assert_formal_attempt_registry_acceptance
    formal_calls = 0

    def observe_formal(**kwargs):
        nonlocal formal_calls
        formal_calls += 1
        return original_formal(**kwargs)

    def reject_compat(**_kwargs):
        pytest.fail("high-level acceptance reached the compatibility facade")

    monkeypatch.setattr(
        R, "assert_formal_attempt_registry_acceptance", observe_formal,
    )
    monkeypatch.setattr(R, "assert_attempt_registry_acceptance", reject_compat)
    receipt = (
        repo / R.s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR
        / f"{manifest.sha256}.json"
    )

    with pytest.raises(
        R.TrialRegistryError,
        match=r"terminal failure reason differs from classification",
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )

    assert formal_calls == 1
    assert not receipt.exists()


@pytest.mark.parametrize(
    ("replacement", "identity_label"),
    [("target", "path"), ("parent", "parent")],
)
def test_formal_acceptance_rejects_noncooperating_registry_rebind_without_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replacement: str,
    identity_label: str,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    attempt_registry = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    before = attempt_registry.read_bytes()
    original_formal = R.assert_formal_attempt_registry_acceptance
    replaced = False

    def rebind_after_strict_replay(**kwargs):
        nonlocal replaced
        rows = original_formal(**kwargs)
        if replacement == "target":
            candidate = attempt_registry.with_name("replacement.jsonl")
            candidate.write_bytes(before)
            os.replace(candidate, attempt_registry)
        else:
            original_parent = attempt_registry.parent
            moved_parent = original_parent.with_name(
                original_parent.name + "-detached"
            )
            original_parent.rename(moved_parent)
            original_parent.mkdir(parents=True)
            attempt_registry.write_bytes(before)
        replaced = True
        return rows

    monkeypatch.setattr(
        R,
        "assert_formal_attempt_registry_acceptance",
        rebind_after_strict_replay,
    )
    receipt = (
        repo / R.s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR
        / f"{manifest.sha256}.json"
    )

    with pytest.raises(
        R.TrialRegistryError,
        match=rf"attempt registry {identity_label} changed during formal acceptance",
    ):
        R.assert_trial_registry_acceptance(
            effective_preregistration=capability,
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
            lifecycle_path=lifecycle,
        )

    assert replaced is True
    assert not receipt.exists()


def test_formal_acceptance_shared_lock_blocks_compat_writer_through_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The writer fd must conflict before the receipt-order guard proceeds."""
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(repo / "reports", manifest, _head(repo), complete=False)
    capability = _effective_capability(manifest, monkeypatch)
    lifecycle = _write_acceptance_lifecycle(
        repo, manifest, reports, capability.report_digest_sha256,
    )
    attempt_registry = repo / R.DEFAULT_ATTEMPT_REGISTRY_PATH
    attempt_rows = R.load_attempt_registry(repo)
    genesis = attempt_rows[0]
    slot = genesis["slots"][0]
    content_commit, effective_commit = _fixture_registration_commits(
        repo, manifest,
    )
    writer_started = threading.Event()
    writer_lock_conflict_observed = threading.Event()
    writer_done = threading.Event()
    writer_errors: list[BaseException] = []
    writer_thread_ids: set[int] = set()
    threads: list[threading.Thread] = []
    causal_trace: list[str] = []
    original_flock = R.fcntl.flock
    original_receipt = R._exclusive_create_acceptance_receipt

    def observe_flock(fd: int, operation: int) -> None:
        if (
            threading.get_ident() in writer_thread_ids
            and operation == R.fcntl.LOCK_EX
        ):
            try:
                original_flock(fd, operation | R.fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                original_flock(fd, R.fcntl.LOCK_UN)
                raise AssertionError(
                    "compat writer fd did not conflict with the acceptance reader"
                )
            causal_trace.append("writer-lock-attempt")
            writer_lock_conflict_observed.set()
        original_flock(fd, operation)

    def compat_writer() -> None:
        writer_thread_ids.add(threading.get_ident())
        writer_started.set()
        try:
            R.reserve_attempt_slot(
                repository_root=repo,
                registry_path=attempt_registry,
                freeze_id=genesis["freeze_id"],
                slot_id=slot["slot_id"],
                prereg_content_commit=content_commit,
                prereg_effective_commit=effective_commit,
                run_start_receipt_sha256="f" * 64,
                process_identity={
                    "pid": 404,
                    "starttime": "blocked-compat-writer",
                    "execution_uuid": "blocked-compat-writer",
                },
                started_at="2026-08-18T00:00:03+00:00",
            )
        except BaseException as exc:
            writer_errors.append(exc)
        finally:
            causal_trace.append("writer-done")
            writer_done.set()

    def observe_receipt(**kwargs):
        causal_trace.append("receipt-critical-before")
        thread = threading.Thread(target=compat_writer)
        threads.append(thread)
        thread.start()
        assert writer_started.wait(2.0), "compat writer thread did not start"
        assert writer_lock_conflict_observed.wait(2.0), (
            "compat writer fd did not observe a real conflict with the "
            "acceptance shared lock"
        )
        assert causal_trace == [
            "receipt-critical-before",
            "writer-lock-attempt",
        ]
        assert not writer_done.is_set()
        result = original_receipt(**kwargs)
        causal_trace.append("receipt-critical-after")
        assert not writer_done.is_set()
        return result

    monkeypatch.setattr(R.fcntl, "flock", observe_flock)
    monkeypatch.setattr(
        R, "_exclusive_create_acceptance_receipt", observe_receipt,
    )

    summary = R.assert_trial_registry_acceptance(
        effective_preregistration=capability,
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
        lifecycle_path=lifecycle,
    )
    assert (repo / summary.receipt_path).is_file()
    assert len(threads) == 1
    threads[0].join(timeout=2.0)
    assert not threads[0].is_alive(), (
        "compat writer did not finish after acceptance released the shared lock"
    )
    assert writer_done.is_set()
    assert len(writer_errors) == 1
    assert isinstance(writer_errors[0], R.TrialRegistryError)
    assert "slot was already reserved" in str(writer_errors[0])
    assert causal_trace == [
        "receipt-critical-before",
        "writer-lock-attempt",
        "receipt-critical-after",
        "writer-done",
    ]


def test_attempt_registry_accepts_correct_formal_slot_consumption(
    tmp_path: Path,
) -> None:
    repo, manifest_path, manifest, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(
        repo,
        registry,
        p,
        c,
        freeze,
        slots[0],
    )
    raw_hash = "d" * 64
    report_path, binding = _attempt_report_for_acceptance(
        repo, manifest, slots[0], p, c, raw_hash,
    )
    _classify_and_terminal(
        cap,
        failure_reason=None,
        terminal_status="observed",
        report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        raw_output_sha256=raw_hash,
    )
    rows = R.assert_attempt_registry_acceptance(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest=manifest,
        effective_binding=binding,
        effective_commit=c,
        report_paths=[report_path],
    )
    assert any(row.get("event") == "terminal" for row in rows)


def test_attempt_registry_accepts_observed_terminal_status_only(
    tmp_path: Path,
) -> None:
    repo, manifest_path, manifest, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    raw_hash = "d" * 64
    report_path, binding = _attempt_report_for_acceptance(
        repo, manifest, slots[0], p, c, raw_hash,
    )
    _classify_and_terminal(
        cap,
        failure_reason=None,
        terminal_status="observed",
        report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        raw_output_sha256=raw_hash,
    )
    rows = R.assert_attempt_registry_acceptance(
        repository_root=repo,
        manifest_path=manifest_path,
        manifest=manifest,
        effective_binding=binding,
        effective_commit=c,
        report_paths=[report_path],
    )
    assert rows[-1]["terminal_status"] == "observed"


def test_attempt_acceptance_rejects_unmanifested_replicate_slot(
    tmp_path: Path,
) -> None:
    repo, manifest_path, manifest, registry, p, c, freeze, slots = _attempt_fixture(
        tmp_path,
        extra_replicate=True,
    )
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    raw_hash = "d" * 64
    report_path, binding = _attempt_report_for_acceptance(
        repo, manifest, slots[0], p, c, raw_hash,
    )
    _classify_and_terminal(
        cap,
        failure_reason=None,
        terminal_status="observed",
        report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        raw_output_sha256=raw_hash,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"genesis initial slot set differs",
    ):
        R.assert_attempt_registry_acceptance(
            repository_root=repo,
            manifest_path=manifest_path,
            manifest=manifest,
            effective_binding=binding,
            effective_commit=c,
            report_paths=[report_path],
        )


def test_attempt_acceptance_rejects_terminal_failure_report_observed_values(
    tmp_path: Path,
) -> None:
    repo, manifest_path, manifest, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    raw_hash = "d" * 64
    report_path, binding = _attempt_report_for_acceptance(
        repo, manifest, slots[0], p, c, raw_hash,
    )
    report = json.loads(report_path.read_bytes())
    report["status"] = "partial"
    report_path.write_bytes(_canonical(report))
    _classify_and_terminal(
        cap,
        failure_reason="producer-failure",
        terminal_status="terminal-failure",
        report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        raw_output_sha256=raw_hash,
    )
    with pytest.raises(
        R.TrialRegistryError,
        match=r"non-observed terminal report carries observed values",
    ):
        R.assert_attempt_registry_acceptance(
            repository_root=repo,
            manifest_path=manifest_path,
            manifest=manifest,
            effective_binding=binding,
            effective_commit=c,
            report_paths=[report_path],
        )


def test_attempt_registry_rejects_schedule_row_hash_replacement(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    rows[-1]["schedule_row_sha256"] = "f" * 64
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"schedule row hash"):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_process_identity_replacement(tmp_path: Path) -> None:
    repo, _manifest, _m, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    _classify_and_terminal(cap, failure_reason=None, terminal_status="observed")
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    rows[-1]["process_identity"]["pid"] = 202
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"process identity"):
        R.load_attempt_registry(repo)


def test_attempt_registry_rejects_raw_output_hash_replacement(tmp_path: Path) -> None:
    repo, manifest_path, manifest, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    raw_hash = "d" * 64
    report_path, binding = _attempt_report_for_acceptance(
        repo, manifest, slots[0], p, c, raw_hash,
    )
    report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
    _classify_and_terminal(
        cap,
        failure_reason=None,
        terminal_status="observed",
        report_sha256=report_hash,
        raw_output_sha256=raw_hash,
    )
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    rows[-1]["raw_output_sha256"] = "f" * 64
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"raw output hash"):
        R.assert_attempt_registry_acceptance(
            repository_root=repo,
            manifest_path=manifest_path,
            manifest=manifest,
            effective_binding=binding,
            effective_commit=c,
            report_paths=[report_path],
        )


def test_attempt_registry_rejects_terminal_report_hash_replacement(tmp_path: Path) -> None:
    repo, manifest_path, manifest, registry, p, c, freeze, slots = _attempt_fixture(tmp_path)
    cap = _reserve_attempt(repo, registry, p, c, freeze, slots[0])
    raw_hash = "d" * 64
    report_path, binding = _attempt_report_for_acceptance(
        repo, manifest, slots[0], p, c, raw_hash,
    )
    report_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
    _classify_and_terminal(
        cap,
        failure_reason=None,
        terminal_status="observed",
        report_sha256=report_hash,
        raw_output_sha256=raw_hash,
    )
    rows = [json.loads(line) for line in registry.read_text().splitlines()]
    rows[-1]["report_sha256"] = "f" * 64
    _rewrite_attempt_rows(registry, rows)
    with pytest.raises(R.TrialRegistryError, match=r"terminal report hash"):
        R.assert_attempt_registry_acceptance(
            repository_root=repo,
            manifest_path=manifest_path,
            manifest=manifest,
            effective_binding=binding,
            effective_commit=c,
            report_paths=[report_path],
        )


if __name__ == "__main__":
    def _plain_runner_main() -> int:
        return int(pytest.main(["-q", str(Path(__file__).resolve())]))

    raise SystemExit(_plain_runner_main())
