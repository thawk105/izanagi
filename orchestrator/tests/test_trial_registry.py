# -*- coding: utf-8 -*-
"""T-325 exact trial registry gates and preregistered mutations."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.campaign import p3_autonomous_workload_trial as producer
from orchestrator.campaign import trial_registry as R


_SOURCE_REPO = Path(__file__).resolve().parents[2]
_ROLES = ("planner", "coder", "auditor", "critic")


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
            trials.append({
                "trial_id": f"{prefix}-{token}",
                "arm": arm,
                "holdout": holdout,
                "campaign_id": f"campaign-{prefix}-{token}",
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
        "trials": [
            {
                "trial_id": trial.trial_id,
                "arm": trial.arm,
                "holdout": trial.holdout,
                "campaign_id": trial.campaign_id,
            }
            for trial in manifest.trials
        ],
    }


def _write_registry(path: Path, *rows: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(_canonical(row) + b"\n" for row in rows))


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
    R.append_trial_registration(
        manifest_path=manifest_path,
        repository_root=repo,
        registry_path=registry_path,
    )
    _commit(repo, "registry", registry_path)
    return repo, manifest_path, registry_path, R.load_trial_manifest(manifest_path)


def _role_event(workload: str, role: str, seq: int, descriptor_hash: str) -> dict:
    return {
        "event": "role-attempt",
        "workload": workload,
        "generation": 1,
        "role": role,
        "attempt": 1,
        "invocation_id": f"{workload}.g1.{role}",
        "seq": seq,
        "ts": f"2026-08-01T00:00:{seq:02d}+00:00",
        "status": "valid",
        "retry": False,
        "input_payload_sha256": hashlib.sha256(
            f"payload:{workload}:{role}".encode()
        ).hexdigest(),
        "descriptor_sha256": descriptor_hash,
        "raw_response_path": f"/fixture/raw-{workload}-{role}.json",
        "raw_response_sha256": hashlib.sha256(
            f"response:{workload}:{role}".encode()
        ).hexdigest(),
        "parsed": {"fixture_role": role},
        "provenance": {"fixture": True},
    }


def _base_start(trial: R.TrialSpec, run: Path, measurement_head: str) -> dict:
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    return {
        "event": "run-start",
        "schema_version": producer.SCHEMA_VERSION,
        "trial_id": trial.trial_id,
        "provider": "fixture",
        "workloads": [workload],
        "generation_budget_per_workload": 1,
        "max_wall_s": 60,
        "do_build": False,
        "performance_early_stop": False,
        "scientific_claim": False,
        "prereg_commit": None,
        "measurement_head": measurement_head,
        "manifest_sha256": None,
        "seq": 1,
        "ts": "2026-08-01T00:00:01+00:00",
    }


def _base_report(trial: R.TrialSpec, run: Path, measurement_head: str) -> dict:
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
        "generation_budget_per_workload": 1,
        "stop_policy": {
            "fixed_generations": True,
            "performance_early_stop": False,
            "max_wall_s": 60,
        },
        "claim_scope": {"scientific_claim": False},
        "attempt_journal": str(run / "attempts.jsonl"),
        "cells": [],
        "prereg_commit": None,
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


def _complete_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
) -> Path:
    run = root / f"run-{trial.trial_id}"
    workload = R.HOLDOUT_BINDINGS[trial.holdout]["workload"]
    ratio = R.HOLDOUT_BINDINGS[trial.holdout]["ycsb_rratio"]
    descriptor_hash = hashlib.sha256(f"descriptor:{workload}".encode()).hexdigest()
    start = _base_start(trial, run, measurement_head)
    report = _base_report(trial, run, measurement_head)
    for target in (start, report):
        target["prereg_commit"] = manifest.prereg_commit
        target["manifest_sha256"] = manifest.sha256
    roles: dict[str, dict] = {}
    events = [start]
    for seq, role in enumerate(_ROLES, 2):
        event = _role_event(workload, role, seq, descriptor_hash)
        events.append(event)
        roles[role] = copy.deepcopy(event)
    report["cells"] = [{
        "workload": workload,
        "workload_flags": {"ycsb_rratio": ratio},
        "descriptor": {"fixture": workload},
        "descriptor_binding": {"output_sha256": descriptor_hash},
        "campaign_id": trial.campaign_id,
        "campaign_root": str(run / "campaigns" / trial.campaign_id),
        "admission_decision": {"admission_status": "not-applicable"},
        "generations": [{
            "generation": 1,
            "roles": roles,
            "preview": {"passed": True, "forbidden_identifiers": []},
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
    }]
    events.append({
        "event": "run-finish",
        "status": "complete",
        "report": str(run / "report.json"),
        "seq": 6,
        "ts": "2026-08-01T00:01:06+00:00",
    })
    return _persist(run, events, report)


def _partial_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
) -> Path:
    run = root / f"run-{trial.trial_id}"
    start = _base_start(trial, run, measurement_head)
    report = _base_report(trial, run, measurement_head)
    for target in (start, report):
        target["prereg_commit"] = manifest.prereg_commit
        target["manifest_sha256"] = manifest.sha256
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
        {
            "event": "run-finish",
            "status": "partial",
            "report": str(run / "report.json"),
            "seq": 3,
            "ts": "2026-08-01T00:01:03+00:00",
        },
    ]
    return _persist(run, events, report)


def _one_cell_partial_report(
    root: Path,
    trial: R.TrialSpec,
    manifest: R.TrialManifest,
    measurement_head: str,
) -> Path:
    path = _complete_report(root, trial, manifest, measurement_head)
    events, report = _load_report_bundle(path)
    error = {"type": "RuntimeError", "message": "supervisor failed"}
    report["status"] = "partial"
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


def test_p2_first_and_second_registration_append_pass(tmp_path: Path) -> None:
    repo, manifest_a_path, registry, _manifest_a = _registered_repo(tmp_path)
    before = registry.read_bytes()
    inode = registry.stat().st_ino
    prereg = _run(repo, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_b_path, _manifest_value(prereg, "trial-b"))
    _commit(repo, "manifest-b", manifest_b_path)
    R.append_trial_registration(
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
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=True)
    reports.reverse()
    summary = R.assert_trial_registry_acceptance(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert summary.certifying is False
    assert summary.arm_binding == "declared-only"
    assert {trial.status for trial in summary.trials} == {"complete"}


def test_p6_partial_terminal_outcomes_are_reported_not_dropped(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    measurement = _head(repo)
    reports = [
        (_complete_report if index == 0 else _partial_report)(
            tmp_path / "reports", trial, manifest, measurement,
        )
        for index, trial in enumerate(manifest.trials)
    ]
    summary = R.assert_trial_registry_acceptance(
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
            tmp_path / "reports", trial, manifest, measurement,
        )
        for index, trial in enumerate(manifest.trials)
    ]
    summary = R.assert_trial_registry_acceptance(
        manifest_path=manifest_path,
        report_paths=reports,
        repository_root=repo,
        registry_path=registry,
    )
    assert [trial.status for trial in summary.trials].count("partial") == 6


def test_p7_later_registry_rows_do_not_hide_older_manifest(tmp_path: Path) -> None:
    repo, manifest_a_path, registry, manifest_a = _registered_repo(tmp_path)
    prereg = manifest_a.prereg_commit
    manifest_b_path = repo / "manifest-b.json"
    _write_manifest(manifest_b_path, _manifest_value(prereg, "trial-b"))
    _commit(repo, "manifest-b", manifest_b_path)
    R.append_trial_registration(
        manifest_path=manifest_b_path, repository_root=repo, registry_path=registry,
    )
    _commit(repo, "registry-b", registry)
    reports = _reports(tmp_path / "reports", manifest_a, _head(repo), complete=False)
    summary = R.assert_trial_registry_acceptance(
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
    R.assert_unregistered_for_exploratory("fresh-exploratory", registry, repo)


def test_p12_accept_cli_runs_from_clean_pythonpath(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        env.pop(key, None)
    env["PYTHONPATH"] = str(_SOURCE_REPO)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestrator.campaign.trial_registry",
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
    assert output["arm_binding"] == "declared-only"
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
        '"schema_version":"p3-8c-trial-registration/v1"',
        '"schema_version":"decoy","schema_version":"p3-8c-trial-registration/v1"',
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
    R.append_trial_registration(
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
        R.append_trial_registration(
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
    R.append_trial_registration(
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
    R.append_trial_registration(
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
    with pytest.raises(R.TrialRegistryError, match=r"\[campaign-binding\] "):
        R.assert_campaign_binding(binding, actual_campaign_id=trial.campaign_id + "-derived")


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


@pytest.mark.parametrize(
    "mutation", ["missing", "different"], ids=["m16a-missing", "m16b-different"],
)
def test_m16_report_prereg_binding_is_required(tmp_path: Path, mutation: str) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
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
        R.assert_trial_registry_acceptance(
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
    R.append_trial_registration(
        manifest_path=manifest_path, repository_root=repo, registry_path=registry,
    )
    _commit(repo, "late-registry", registry)
    reports = _reports(tmp_path / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[historical-binding\] measurement registry blob is absent$"):
        R.assert_trial_registry_acceptance(
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
    R.append_trial_registration(
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
    reports = _reports(tmp_path / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-prefix\] "):
        R.assert_trial_registry_acceptance(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_redundant_six_report_argument_count_defense_is_required(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[report-count\] acceptance requires exactly 6"):
        R.assert_trial_registry_acceptance(
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
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
    if mutation == "duplicate":
        reports[-1] = reports[0]
    else:
        events, report = _load_report_bundle(reports[-1])
        report["trial_id"] = "foreign-trial"
        events[0]["trial_id"] = "foreign-trial"
        _persist(reports[-1].parent, events, report)
    with pytest.raises(R.TrialRegistryError, match=r"\[trial-set\] "):
        R.assert_trial_registry_acceptance(
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
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=True)
    events, report = _load_report_bundle(reports[0])
    if mutation == "ratio":
        report["cells"][0]["workload_flags"]["ycsb_rratio"] = "999"
    else:
        report["cells"][0]["campaign_id"] += "-changed"
    _persist(reports[0].parent, events, report)
    with pytest.raises(R.TrialRegistryError, match=r"\[terminal-projection\] report cell differs"):
        R.assert_trial_registry_acceptance(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_m22_existing_completeness_verifier_is_mandatory(tmp_path: Path) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=True)
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
        R.assert_trial_registry_acceptance(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_m28_report_only_binding_without_run_start_binding_is_rejected(
    tmp_path: Path,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
    events, report = _load_report_bundle(reports[0])
    for field in ("prereg_commit", "measurement_head", "manifest_sha256"):
        events[0].pop(field)
    _persist(reports[0].parent, events, report)
    with pytest.raises(R.TrialRegistryError, match=r"\[run-start-binding\] "):
        R.assert_trial_registry_acceptance(
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
    R.append_trial_registration(
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
    reports = _reports(tmp_path / "reports", manifest_a, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry history is not a strict prefix extension$"):
        R.assert_trial_registry_acceptance(
            manifest_path=manifest_a_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )


def test_registered_trial_is_rejected_without_manifest_for_unit_b(tmp_path: Path) -> None:
    repo, _manifest_path, registry, manifest = _registered_repo(tmp_path)
    with pytest.raises(R.TrialRegistryError, match=r"\[exploratory-registry\] "):
        R.assert_unregistered_for_exploratory(manifest.trials[0].trial_id, registry, repo)


def test_registry_parent_real_path_must_stay_inside_repository(tmp_path: Path) -> None:
    repo, prereg = _init_repo(tmp_path)
    manifest_path = repo / "manifest.json"
    _write_manifest(manifest_path, _manifest_value(prereg, "path-parent"))
    _commit(repo, "manifest", manifest_path)
    outside = tmp_path / "outside" / "registry.jsonl"
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-path\] "):
        R.append_trial_registration(
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
    R.append_trial_registration(
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
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
    alias = reports[0].with_name("renamed-report.json")
    alias.write_bytes(reports[0].read_bytes())
    reports[0] = alias
    with pytest.raises(R.TrialRegistryError, match=r"\[report-path\] "):
        R.assert_trial_registry_acceptance(
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
    reports = _reports(tmp_path / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry path was deleted"):
        R.assert_trial_registry_acceptance(
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
        R.assert_unregistered_for_exploratory(
            manifest.trials[0].trial_id,
            registry,
            repo,
        )


def test_m31_journal_snapshot_swap_cannot_compose_binding_and_completeness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, manifest_path, registry, manifest = _registered_repo(tmp_path)
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
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
        R.assert_trial_registry_acceptance(
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
    reports = _reports(tmp_path / "reports", manifest, _head(repo), complete=False)
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
        R.assert_trial_registry_acceptance(
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
    R.append_trial_registration(
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
    reports = _reports(tmp_path / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] "):
        R.assert_trial_registry_acceptance(
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
        R.append_trial_registration(
            manifest_path=manifest_path,
            repository_root=repo,
            registry_path=repo / "registry.jsonl",
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
        R.append_trial_registration(
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
        R.append_trial_registration(
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
        R.append_trial_registration(
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
        R.append_trial_registration(
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
    reports = _reports(tmp_path / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry path was deleted"):
        R.assert_trial_registry_acceptance(
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
    reports = _reports(tmp_path / "reports", manifest, measurement, complete=False)
    with pytest.raises(R.TrialRegistryError, match=r"\[registry-history\] registry path was deleted"):
        R.assert_trial_registry_acceptance(
            manifest_path=manifest_path,
            report_paths=reports,
            repository_root=repo,
            registry_path=registry,
        )
