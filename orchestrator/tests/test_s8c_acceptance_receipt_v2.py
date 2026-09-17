# -*- coding: utf-8 -*-
"""T-822 receipt-v2 descriptor proof and reason-drop controls."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

import pytest

from orchestrator.campaign import attempt_registry_core as attempt_core
from orchestrator.campaign import autonomous_trial_completeness as completeness
from orchestrator.campaign import s8c_acceptance_receipt as receipt


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_line(value: object) -> bytes:
    return _canonical(value) + b"\n"


def _plain_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain_json(item) for item in value]
    if isinstance(value, list):
        return [_plain_json(item) for item in value]
    return value


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _commit_all(repo: Path, message: str) -> str:
    assert _run(repo, "add", "-A").returncode == 0
    committed = _run(repo, "commit", "-q", "-m", message)
    assert committed.returncode == 0, committed.stderr
    head = _run(repo, "rev-parse", "HEAD")
    assert head.returncode == 0, head.stderr
    return head.stdout.strip()


def _write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _binding_digest(*, holdout: str, arm: str, content_digest: str) -> str:
    return hashlib.sha256(
        b"izanagi-s8c-arm-binding/v1\0"
        + holdout.encode("ascii")
        + arm.encode("ascii")
        + content_digest.encode("ascii")
    ).hexdigest()


def _assert_resolved_descriptor_matches_ratified_literals(
    *, holdout: str, arm: str, descriptor: dict,
) -> None:
    """Pin resolver output to the literal H1/H2 legacy-freeze conditions."""
    expected_descriptors = {
        ("H1", "on"): {
            "schema_version": "8b-v1",
            "source": "campaign_search_config_projection",
            "read_write": {"read_ratio_percent": 80, "rmw": 0},
            "contention": {"skew": 0.9, "label": "high"},
            "scale": {"records": 1_000_000, "threads": 48},
            "objective": "maximize_throughput_tps",
            "correctness": "serializable_legacy_and_s2",
        },
        ("H1", "swapped"): {
            "schema_version": "8b-v1",
            "source": "campaign_search_config_projection",
            "read_write": {"read_ratio_percent": 20, "rmw": 0},
            "contention": {"skew": 0.9, "label": "high"},
            "scale": {"records": 1_000_000, "threads": 48},
            "objective": "maximize_throughput_tps",
            "correctness": "serializable_legacy_and_s2",
        },
        ("H1", "off"): {
            "schema_version": "8b-v1",
            "source": "campaign_search_config_projection",
            "read_write": {"read_ratio_percent": 50, "rmw": 0},
            "contention": {"skew": 0.9, "label": "high"},
            "scale": {"records": 1_000_000, "threads": 48},
            "objective": "maximize_throughput_tps",
            "correctness": "serializable_legacy_and_s2",
        },
        ("H2", "on"): {
            "schema_version": "8b-v1",
            "source": "campaign_search_config_projection",
            "read_write": {"read_ratio_percent": 20, "rmw": 0},
            "contention": {"skew": 0.9, "label": "high"},
            "scale": {"records": 1_000_000, "threads": 48},
            "objective": "maximize_throughput_tps",
            "correctness": "serializable_legacy_and_s2",
        },
        ("H2", "swapped"): {
            "schema_version": "8b-v1",
            "source": "campaign_search_config_projection",
            "read_write": {"read_ratio_percent": 80, "rmw": 0},
            "contention": {"skew": 0.9, "label": "high"},
            "scale": {"records": 1_000_000, "threads": 48},
            "objective": "maximize_throughput_tps",
            "correctness": "serializable_legacy_and_s2",
        },
        ("H2", "off"): {
            "schema_version": "8b-v1",
            "source": "campaign_search_config_projection",
            "read_write": {"read_ratio_percent": 50, "rmw": 0},
            "contention": {"skew": 0.9, "label": "high"},
            "scale": {"records": 1_000_000, "threads": 48},
            "objective": "maximize_throughput_tps",
            "correctness": "serializable_legacy_and_s2",
        },
    }
    assert descriptor == expected_descriptors[(holdout, arm)]


def _attempt_slots(trials: list[dict], *, prereg_generation: int) -> list[dict]:
    slots = []
    for row in trials:
        for attempt_index in range(2):
            identity = {
                "trial_id": row["trial_id"],
                "arm": row["arm"],
                "holdout": row["holdout"],
                "campaign_id": row["campaign_id"],
                "prereg_generation": prereg_generation,
                "replicate_index": 0,
                "attempt_index": attempt_index,
            }
            slots.append({
                "slot_id": f"{row['trial_id']}-r0-a{attempt_index}",
                **identity,
                "schedule_row_sha256": hashlib.sha256(
                    _canonical(identity)
                ).hexdigest(),
            })
    return slots


def _fixture(
    tmp_path: Path,
    *,
    attempt_manifest_sha256: str | None = None,
    track_attempt_genesis: bool = True,
) -> tuple[Path, Path, dict]:
    from orchestrator.campaign import s8c_arm_inputs

    repo = tmp_path / "repo"
    repo.mkdir()
    assert _run(repo, "init", "-q").returncode == 0
    assert _run(repo, "config", "user.email", "fixture@example.invalid").returncode == 0
    assert _run(repo, "config", "user.name", "Fixture").returncode == 0

    manifest_path = repo / "input" / "manifest.json"
    manifest_sha = _write(manifest_path, b'{"fixture":"manifest"}\n')
    registry_path = repo / "output" / "s8c-trial-registry" / "registry.jsonl"
    registry_sha = _write(registry_path, b'{"fixture":"registry"}\n')
    lifecycle_path = repo / "output" / "s8c-trial-registry" / "lifecycle.jsonl"
    lifecycle_sha = _write(lifecycle_path, b'{"fixture":"lifecycle"}\n')
    s8c_arm_inputs.generate_off_neutral_artifacts(repository_root=repo)
    genesis_trials = [
        {
            "trial_id": f"trial-{holdout.lower()}-{arm}",
            "arm": arm,
            "holdout": holdout,
            "campaign_id": f"campaign-{holdout.lower()}-{arm}",
        }
        for holdout in ("H1", "H2")
        for arm in ("on", "off", "swapped")
    ]
    if track_attempt_genesis:
        genesis_rows = attempt_core.create_attempt_registry_genesis(
            profile=receipt._RECEIPT_ATTEMPT_PROFILE,
            freeze_id="receipt-v5-fixture",
            manifest_path=PurePosixPath(manifest_path.relative_to(repo).as_posix()),
            manifest_sha256=(attempt_manifest_sha256 or manifest_sha),
            slots=_attempt_slots(genesis_trials, prereg_generation=13),
        )
        attempt_path = repo.joinpath(
            *receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.parts
        )
        _write(attempt_path, _canonical_line(genesis_rows[0]))
    introduction = _commit_all(repo, "receipt references and off artifacts")

    trial_rows = []
    for holdout in ("H1", "H2"):
        for arm in ("on", "off", "swapped"):
            trial_id = f"trial-{holdout.lower()}-{arm}"
            campaign_id = f"campaign-{holdout.lower()}-{arm}"
            workload = f"workload-{holdout.lower()}"
            resolved = s8c_arm_inputs.resolve_arm_input(
                arm=arm,
                holdout=holdout,
                repository_root=repo,
                commit=introduction,
            )
            descriptor = json.loads(resolved.canonical_input_bytes)
            _assert_resolved_descriptor_matches_ratified_literals(
                holdout=holdout,
                arm=arm,
                descriptor=descriptor,
            )
            arm_execution = {
                "input_schema_version": resolved.input_schema_version,
                "content_digest_sha256": resolved.content_digest_sha256,
                "arm_binding_digest_sha256": resolved.arm_binding_digest_sha256,
            }
            report = {
                "trial_id": trial_id,
                "measurement_head": introduction,
                "status": "complete",
                "do_build": False,
                "arm_execution": arm_execution,
                "launch_admission": {
                    "binding": {
                        "arm": arm,
                        "holdout": holdout,
                        "campaign_id": campaign_id,
                        "measurement_head": introduction,
                        "workload": workload,
                        "ycsb_rratio": {"H1": "80", "H2": "20"}[holdout],
                    },
                },
                "cells": [{"workload": workload, "descriptor": descriptor}],
            }
            journal = _canonical_line({
                "event": "run-start",
                "trial_id": trial_id,
                "arm_execution": arm_execution,
            })
            run = repo / "runs" / trial_id
            report_path = run / "report.json"
            journal_path = run / "attempts.jsonl"
            report_sha = _write(report_path, _canonical(report))
            journal_sha = _write(journal_path, journal)
            trial_rows.append({
                "trial_id": trial_id,
                "arm": arm,
                "holdout": holdout,
                "campaign_id": campaign_id,
                "status": "complete",
                "measurement_head": introduction,
                "report_path": report_path.relative_to(repo).as_posix(),
                "report_sha256": report_sha,
                "attempt_journal_path": journal_path.relative_to(repo).as_posix(),
                "attempt_journal_sha256": journal_sha,
                "arm_execution": copy.deepcopy(arm_execution),
            })

    _commit_all(repo, "trial reports and attempt journals")
    value = {
        "schema_version": receipt.PREVIOUS_SCHEMA_VERSION,
        "manifest_path": manifest_path.relative_to(repo).as_posix(),
        "manifest_sha256": manifest_sha,
        "prereg_commit": introduction,
        "activation_report_digest_sha256": "2" * 64,
        "registry_path": registry_path.relative_to(repo).as_posix(),
        "registry_blob_sha256": registry_sha,
        "registry_introduction_commit": introduction,
        "lifecycle_path": lifecycle_path.relative_to(repo).as_posix(),
        "lifecycle_prefix_bytes": len(lifecycle_path.read_bytes()),
        "lifecycle_prefix_sha256": lifecycle_sha,
        "certifying": False,
        "non_certifying_reason_codes": ["t468-approval-authority-absent"],
        "trials": sorted(trial_rows, key=lambda row: row["trial_id"]),
    }
    receipt_path = repo.joinpath(
        *receipt.DEFAULT_RECEIPT_DIR.parts, f"{manifest_sha}.json",
    )
    _write(receipt_path, _canonical_line(value))
    _commit_all(repo, "receipt v2")
    return repo, receipt_path, value


def _rewrite_receipt(repo: Path, path: Path, value: dict, message: str) -> None:
    path.write_bytes(_canonical_line(value))
    _commit_all(repo, message)


def _trial(value: dict, holdout: str, arm: str) -> dict:
    return next(
        row for row in value["trials"]
        if row["holdout"] == holdout and row["arm"] == arm
    )


def _cross_binding_aggregate_for_schema(value: dict, schema_version: str) -> str:
    leaves = [
        {
            "trial_id": row["trial_id"],
            "receipt_sha256": row["cross_binding_receipt_sha256"],
        }
        for row in value["trials"]
    ]
    payload = {
        "schema_version": schema_version,
        "trials": sorted(leaves, key=lambda leaf: leaf["trial_id"]),
    }
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _install_attempt_registry_binding(
    repo: Path,
    value: dict,
    *,
    terminal_failure_trials: frozenset[str] = frozenset(),
    retry_trial_id: str | None = None,
    binding_prereg_content_commit: str | None = None,
    binding_prereg_effective_commit: str | None = None,
) -> None:
    prereg_generation = 13
    slots = _attempt_slots(value["trials"], prereg_generation=prereg_generation)
    profile = receipt._RECEIPT_ATTEMPT_PROFILE
    attempt_path = repo.joinpath(*receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.parts)
    if attempt_path.is_file():
        rows = attempt_core.load_attempt_registry(
            attempt_path.read_bytes(), profile=profile,
        )
        assert sorted(
            rows[0]["slots"], key=lambda slot: slot["slot_id"],
        ) == sorted(slots, key=lambda slot: slot["slot_id"])
    else:
        rows = attempt_core.create_attempt_registry_genesis(
            profile=profile,
            freeze_id="receipt-v5-fixture",
            manifest_path=PurePosixPath(value["manifest_path"]),
            manifest_sha256=value["manifest_sha256"],
            slots=slots,
        )
    binding = (
        binding_prereg_content_commit or value["prereg_content_commit"],
        binding_prereg_effective_commit or value["prereg_effective_commit"],
    )
    trial_rows = {row["trial_id"]: row for row in value["trials"]}

    def consume(slot: dict, *, terminal_status: str, report_sha256: str) -> None:
        nonlocal rows
        failure_reason = (
            "wall-timeout"
            if terminal_status == "retryable-failure"
            else "fixture-terminal-failure"
            if terminal_status == "terminal-failure"
            else None
        )
        rows = attempt_core.reserve_attempt_slot(
            rows,
            profile=profile,
            freeze_id="receipt-v5-fixture",
            slot_id=slot["slot_id"],
            binding=binding,
            run_start_receipt_sha256="3" * 64,
            process_identity={
                "pid": 101,
                "starttime": f"start-{slot['slot_id']}",
                "execution_uuid": f"execution-{slot['slot_id']}",
            },
            started_at="2026-09-02T00:00:00+00:00",
        )
        capability_digest = attempt_core.capability_digest(
            profile=profile,
            schema_version=receipt._ATTEMPT_SCHEMA_VERSION,
            freeze_id="receipt-v5-fixture",
            slot=slot,
            binding=binding,
        )
        rows, _classification_receipt = attempt_core.classify_attempt(
            rows,
            profile=profile,
            freeze_id="receipt-v5-fixture",
            slot_id=slot["slot_id"],
            binding=binding,
            capability_digest_sha256=capability_digest,
            pre_observation_failure_reason=failure_reason,
            authority_id="receipt-v5-fixture-authority",
            authority_policy_sha256="4" * 64,
            external_evidence_sha256="5" * 64,
            classified_at="2026-09-02T00:00:01+00:00",
        )
        if terminal_status != "retryable-failure":
            rows = attempt_core.begin_attempt_observation(
                rows,
                profile=profile,
                freeze_id="receipt-v5-fixture",
                slot_id=slot["slot_id"],
            )
        rows = attempt_core.record_attempt_terminal(
            rows,
            profile=profile,
            freeze_id="receipt-v5-fixture",
            slot_id=slot["slot_id"],
            binding=binding,
            terminal_status=terminal_status,
            raw_output_sha256="6" * 64,
            report_sha256=report_sha256,
            observation_sha256=("7" * 64 if terminal_status == "observed" else None),
            primary_value=(1 if terminal_status == "observed" else None),
            failure_reason=failure_reason,
            finished_at="2026-09-02T00:00:02+00:00",
        )

    for row in value["trials"]:
        trial_id = row["trial_id"]
        if trial_id in terminal_failure_trials:
            row["status"] = "partial"
            report_path = repo / row["report_path"]
            report = json.loads(report_path.read_bytes())
            report["status"] = "partial"
            report_bytes = _canonical(report)
            report_path.write_bytes(report_bytes)
            row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
        initial = next(
            slot for slot in slots
            if slot["trial_id"] == trial_id and slot["attempt_index"] == 0
        )
        if trial_id == retry_trial_id:
            consume(
                initial,
                terminal_status="retryable-failure",
                report_sha256="8" * 64,
            )
            final_slot = next(
                slot for slot in slots
                if slot["trial_id"] == trial_id and slot["attempt_index"] == 1
            )
            consume(
                final_slot,
                terminal_status="observed",
                report_sha256=trial_rows[trial_id]["report_sha256"],
            )
        else:
            consume(
                initial,
                terminal_status=(
                    "terminal-failure"
                    if trial_id in terminal_failure_trials else "observed"
                ),
                report_sha256=trial_rows[trial_id]["report_sha256"],
            )

    attempt_bytes = b"".join(_canonical_line(row) for row in rows)
    _write(attempt_path, attempt_bytes)
    initial_slots = sorted(
        (slot for slot in slots if slot["attempt_index"] == 0),
        key=lambda slot: slot["slot_id"],
    )
    value.update({
        "attempt_registry_path": receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        "attempt_registry_prefix_bytes": len(attempt_bytes),
        "attempt_registry_prefix_sha256": hashlib.sha256(attempt_bytes).hexdigest(),
        "attempt_slot_projection": {
            "prereg_generation": prereg_generation,
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
    })


def _upgrade_to_current(
    repo: Path,
    value: dict,
    *,
    terminal_failure_trials: frozenset[str] = frozenset(),
    retry_trial_id: str | None = None,
    binding_prereg_content_commit: str | None = None,
    binding_prereg_effective_commit: str | None = None,
) -> None:
    value["schema_version"] = receipt.SCHEMA_VERSION
    value.setdefault("prereg_content_commit", value["prereg_commit"])
    effective = _run(repo, "rev-parse", "HEAD")
    assert effective.returncode == 0, effective.stderr
    value.setdefault("prereg_effective_commit", effective.stdout.strip())
    for row in value["trials"]:
        report_path = repo / row["report_path"]
        report = json.loads(report_path.read_bytes())
        journal_path = repo / row["attempt_journal_path"]
        events = [
            json.loads(line) for line in journal_path.read_bytes().splitlines()
        ]
        projection = completeness.verify_s8c_cross_binding(
            report=report,
            events=events,
            run_root=journal_path.parent,
            output_root=None,
        )
        row["cross_binding_receipt_sha256"] = projection["receipt_sha256"]
    value["cross_binding_receipt_sha256"] = (
        receipt.cross_binding_aggregate_sha256([
            {
                "trial_id": row["trial_id"],
                "receipt_sha256": row["cross_binding_receipt_sha256"],
            }
            for row in value["trials"]
        ])
    )
    _install_attempt_registry_binding(
        repo,
        value,
        terminal_failure_trials=terminal_failure_trials,
        retry_trial_id=retry_trial_id,
        binding_prereg_content_commit=binding_prereg_content_commit,
        binding_prereg_effective_commit=binding_prereg_effective_commit,
    )


def _synchronize_arm_execution(
    repo: Path,
    row: dict,
    *,
    descriptor: dict | None = None,
) -> None:
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["arm_execution"] = copy.deepcopy(row["arm_execution"])
    if descriptor is not None:
        report["cells"][0]["descriptor"] = copy.deepcopy(descriptor)
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()

    journal_path = repo / row["attempt_journal_path"]
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
    run_start = next(event for event in events if event.get("event") == "run-start")
    run_start["arm_execution"] = copy.deepcopy(row["arm_execution"])
    journal_bytes = b"".join(_canonical_line(event) for event in events)
    journal_path.write_bytes(journal_bytes)
    row["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()


def _origin_projection(*, arm_binding_digest: str) -> dict:
    return {
        "schema_version": "OriginTerminalProjection/v1",
        "reason_code": "P6Unavailable",
        "formal_receipt_sha256": "7" * 64,
        "evidence_root_sha256": "8" * 64,
        "authority_blob_sha256": "9" * 64,
        "origin_id": "fixture-origin",
        "cell_key": "fixture-cell",
        "terminal_payload_sha256": "a" * 64,
        "arm_binding_digest_sha256": arm_binding_digest,
    }


def test_verifier_keeps_registry_and_layer3_import_independence() -> None:
    tree = ast.parse(Path(receipt.__file__).read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for name in (node.module or "", *(alias.name for alias in node.names))
    }
    assert not any(
        name.endswith("trial_registry") or name.endswith("layer3_report")
        for name in imported
    )


def test_receipt_import_is_cold_for_arm_authority_modules() -> None:
    watched = (
        "orchestrator.campaign.s8b_ratified_freeze",
        "orchestrator.campaign.s8c_arm_inputs",
        "orchestrator.campaign.s8b_holdout_freeze",
        "orchestrator.campaign.s8b_descriptor",
    )
    probe = "\n".join((
        "import sys",
        "import orchestrator.campaign.s8c_acceptance_receipt",
        f"watched = {watched!r}",
        "sys.stdout.write('\\n'.join(name for name in watched if name in sys.modules))",
    ))
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=Path(receipt.__file__).resolve().parents[2],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""


def test_arm_authority_imports_are_function_local() -> None:
    target_modules = {
        "s8b_ratified_freeze",
        "s8c_arm_inputs",
        "s8b_holdout_freeze",
        "s8b_descriptor",
    }
    tree = ast.parse(Path(receipt.__file__).read_text(encoding="utf-8"))
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

    def target_names(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Import):
            names = {alias.name.rsplit(".", 1)[-1] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            names = {alias.name.rsplit(".", 1)[-1] for alias in node.names}
            if node.module:
                names.add(node.module.rsplit(".", 1)[-1])
        else:
            return set()
        return names & target_modules

    targeted_imports = [
        (node, target_names(node))
        for node in ast.walk(tree)
        if target_names(node)
    ]
    assert {
        name for _node, names in targeted_imports for name in names
    } >= {
        "s8b_ratified_freeze",
        "s8c_arm_inputs",
        "s8b_holdout_freeze",
    }
    for node, _names in targeted_imports:
        ancestors = []
        current = node
        while current in parents:
            current = parents[current]
            ancestors.append(current)
        assert any(
            isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef))
            for ancestor in ancestors
        )


def test_lazy_authority_import_failure_is_acceptance_receipt_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    original_import = builtins.__import__

    def reject_authority_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if "s8b_holdout_freeze" in (fromlist or ()):
            raise ModuleNotFoundError("injected cold authority import failure")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", reject_authority_import)
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-freeze-arm-binding\] ratified legacy freeze "
            r"cannot be loaded$"
        ),
    ) as caught:
        receipt._require_ratified_legacy_arm_authority()
    assert isinstance(caught.value.__cause__, ModuleNotFoundError)


def test_resolver_exception_contract_is_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from orchestrator.campaign import s8c_arm_inputs

    def raise_oserror(**_kwargs: object) -> object:
        raise OSError("injected resolver failure")

    monkeypatch.setattr(s8c_arm_inputs, "resolve_arm_input", raise_oserror)
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-freeze-arm-binding\] trial arm input cannot be "
            r"rederived$"
        ),
    ) as caught:
        receipt._expected_arm_content_digest(tmp_path, "H1", "on", "1" * 40)
    assert isinstance(caught.value.__cause__, OSError)

    sentinel = receipt.AcceptanceReceiptError("[receipt-specific] sentinel")

    def raise_acceptance_error(**_kwargs: object) -> object:
        raise sentinel

    monkeypatch.setattr(s8c_arm_inputs, "resolve_arm_input", raise_acceptance_error)
    with pytest.raises(receipt.AcceptanceReceiptError) as propagated:
        receipt._expected_arm_content_digest(tmp_path, "H1", "on", "1" * 40)
    assert propagated.value is sentinel


def test_v2_producer_equivalent_full_verify_drops_only_c02(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.PREVIOUS_SCHEMA_VERSION
    assert verified.receipt.certifying is False
    assert verified.receipt.non_certifying_reason_codes == (
        "t468-approval-authority-absent",
    )
    assert all(trial.arm_execution is not None for trial in verified.trials)
    value["certifying"] = True
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-certifying\] receipts are structurally non-certifying$",
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical_line(value))


def test_self_consistent_wrong_descriptor_is_rejected_by_freeze_rederivation(
    tmp_path: Path,
) -> None:
    """M1 keeps the old gates coherent and changes only the frozen condition."""
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H1", "on")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    descriptor = report["cells"][0]["descriptor"]
    assert type(descriptor["read_write"]["read_ratio_percent"]) is int
    assert descriptor["read_write"]["read_ratio_percent"] == 80
    descriptor["read_write"]["read_ratio_percent"] = 79
    report["launch_admission"]["binding"]["ycsb_rratio"] = "79"
    report_path.write_bytes(_canonical(report))

    content_digest = hashlib.sha256(_canonical(descriptor)).hexdigest()
    row["arm_execution"]["content_digest_sha256"] = content_digest
    row["arm_execution"]["arm_binding_digest_sha256"] = _binding_digest(
        holdout=row["holdout"],
        arm=row["arm"],
        content_digest=content_digest,
    )
    _synchronize_arm_execution(repo, row, descriptor=descriptor)
    _rewrite_receipt(repo, path, value, "self-consistent wrong descriptor")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"\[receipt-freeze-arm-binding\] content digest differs from "
            r"ratified legacy freeze rederivation$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_legacy_holdout_entry_key_drift_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M2 injects loader drift because the fixed artifact hash prevents byte mutation."""
    from orchestrator.campaign import s8b_ratified_freeze

    repo, path, _value = _fixture(tmp_path)
    legacy = s8b_ratified_freeze.load_legacy_freeze()
    document = _plain_json(legacy.document)
    assert isinstance(document, dict)
    document["holdouts"]["rr80"]["future_field"] = "drift"
    doctored = s8b_ratified_freeze.LegacyFreeze(
        document=document,
        sha256=legacy.sha256,
    )
    monkeypatch.setattr(
        s8b_ratified_freeze,
        "load_legacy_freeze",
        lambda: doctored,
    )

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"\[receipt-freeze-arm-binding\] ratified legacy holdout entry "
            r"key set differs: rr80$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_in_source_derangement_drift_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M3 injects source drift because the fixed artifact hash prevents byte mutation."""
    from orchestrator.campaign import s8b_holdout_freeze

    repo, path, _value = _fixture(tmp_path)
    monkeypatch.setattr(
        s8b_holdout_freeze,
        "DERANGEMENT",
        {"rr80": "rr20", "rr20": "rr80", "future": "future"},
    )

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"\[receipt-freeze-arm-binding\] ratified legacy derangement "
            r"differs from in-source authority$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_binding_measurement_head_mismatch_is_rejected(tmp_path: Path) -> None:
    """M4 changes only the serialized binding head and its enclosing report hash."""
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "swapped")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["launch_admission"]["binding"]["measurement_head"] = "f" * 40
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "binding measurement head mismatch")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"\[receipt-freeze-arm-binding\] trial report binding "
            r"measurement_head differs from receipt$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_pairwise_collision_is_rejected_after_binding_recalculation(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    source = _trial(value, "H1", "on")
    target = _trial(value, "H1", "off")
    collided = source["arm_execution"]["content_digest_sha256"]
    target["arm_execution"]["content_digest_sha256"] = collided
    target["arm_execution"]["arm_binding_digest_sha256"] = _binding_digest(
        holdout="H1", arm="off", content_digest=collided,
    )
    source_report = json.loads((repo / source["report_path"]).read_bytes())
    _synchronize_arm_execution(
        repo,
        target,
        descriptor=source_report["cells"][0]["descriptor"],
    )
    _rewrite_receipt(repo, path, value, "coherent pairwise collision")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-arm-binding\] H1 content digests are not "
               r"pairwise distinct$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_receipt_digest_divergence_is_attributed_to_report_descriptor(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H1", "on")
    row["arm_execution"]["content_digest_sha256"] = "f" * 64
    row["arm_execution"]["arm_binding_digest_sha256"] = _binding_digest(
        holdout="H1", arm="on", content_digest="f" * 64,
    )
    _synchronize_arm_execution(repo, row)
    _rewrite_receipt(repo, path, value, "coherent digest descriptor divergence")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-arm-binding\] cell descriptor content digest "
               r"differs from receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    assert all(set(row["arm_execution"]) == {
        "input_schema_version",
        "content_digest_sha256",
        "arm_binding_digest_sha256",
    } for row in value["trials"])
    row = _trial(value, "H2", "off")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["cells"] = []
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "partial receipt without descriptor proof")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-mandatory-reasons\] c02-arm-binding-unproven "
               r"was dropped without descriptor proof$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


@pytest.mark.parametrize("schema_version", [
    receipt.PREVIOUS_SCHEMA_VERSION,
    receipt.SCHEMA_VERSION,
], ids=["v2", "v5"])
def test_partial_receipt_cannot_claim_complete_without_descriptor_proof_even_with_c02(
    tmp_path: Path, schema_version: str,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "off")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    assert report["status"] == row["status"] == "complete"
    assert report["do_build"] is False
    report["cells"] = []
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    value["non_certifying_reason_codes"] = sorted({
        *value["non_certifying_reason_codes"], receipt.C02_ARM_BINDING_UNPROVEN,
    })
    if schema_version == receipt.SCHEMA_VERSION:
        _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "complete receipt without descriptor proof")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"^\[receipt-arm-binding\] complete trial lacks descriptor proof$",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_partial_receipt_cannot_hide_conflicting_descriptor_by_dropping_cells(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H1", "on")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    descriptor = report["cells"][0]["descriptor"]
    assert type(descriptor["read_write"]["read_ratio_percent"]) is int
    assert descriptor["read_write"]["read_ratio_percent"] == 80
    descriptor["read_write"]["read_ratio_percent"] = 79
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "conflicting descriptor with original digest")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"^\[receipt-arm-binding\] cell descriptor content digest "
               r"differs from receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)

    report["cells"] = []
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    value["non_certifying_reason_codes"] = sorted({
        *value["non_certifying_reason_codes"], receipt.C02_ARM_BINDING_UNPROVEN,
    })
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "conflicting descriptor dropped from cells")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"^\[receipt-arm-binding\] complete trial lacks descriptor proof$",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_partial_receipt_with_c02_and_no_cells_passes_current_capability(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "off")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["cells"] = []
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    value["non_certifying_reason_codes"] = sorted({
        *value["non_certifying_reason_codes"], receipt.C02_ARM_BINDING_UNPROVEN,
    })
    _upgrade_to_current(
        repo, value, terminal_failure_trials=frozenset({row["trial_id"]}),
    )
    _rewrite_receipt(repo, path, value, "partial receipt retains c02 without cells")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    trial = next(
        trial for trial in verified.trials if trial.trial_id == row["trial_id"]
    )
    assert trial.status == "partial"
    assert receipt.C02_ARM_BINDING_UNPROVEN in verified.receipt.non_certifying_reason_codes
    assert verified.certifying is False
    assert receipt.require_current_verified_receipt(verified).sha256 == verified.sha256


def test_origin_terminal_projection_is_retained_and_reverified(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "on")
    projection = _origin_projection(
        arm_binding_digest=row["arm_execution"]["arm_binding_digest_sha256"],
    )
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["origin_terminal_projection"] = copy.deepcopy(projection)
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    row["origin_terminal_projection"] = copy.deepcopy(projection)
    _rewrite_receipt(repo, path, value, "matching origin terminal projection")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    parsed_row = next(
        trial for trial in verified.trials if trial.trial_id == row["trial_id"]
    )
    assert parsed_row.origin_terminal_projection == projection

    row["origin_terminal_projection"]["formal_receipt_sha256"] = "b" * 64
    _rewrite_receipt(repo, path, value, "divergent origin terminal projection")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-origin-projection\] trial report "
               r"origin_terminal_projection differs from receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_run_start_mismatch_is_rejected_after_reference_hashes_match(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "swapped")
    journal_path = repo / row["attempt_journal_path"]
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
    events[0]["arm_execution"]["content_digest_sha256"] = "e" * 64
    journal_bytes = b"".join(_canonical_line(event) for event in events)
    journal_path.write_bytes(journal_bytes)
    row["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "run-start mismatch")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"\[receipt-arm-binding\] run-start arm_execution differs "
               r"from report and receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_trial_report_arm_execution_mismatch_is_rejected_after_reference_hashes_match(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "swapped")
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["arm_execution"]["content_digest_sha256"] = "e" * 64
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "trial report arm_execution mismatch")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(r"^\[receipt-arm-binding\] trial report arm_execution differs "
               r"from receipt$"),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v2_never_routes_through_v1_mandatory_reason_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, path, _value = _fixture(tmp_path)

    def reject_legacy_path(_reasons: object) -> None:
        raise AssertionError("v2 bytes reached the v1 mandatory-reason path")

    monkeypatch.setattr(
        receipt, "_require_legacy_mandatory_reason_codes", reject_legacy_path,
    )
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.PREVIOUS_SCHEMA_VERSION


def test_v3_requires_cross_binding_receipt_sha256(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "receipt v4")
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.SCHEMA_VERSION
    assert verified.receipt.cross_binding_receipt_sha256 == value[
        "cross_binding_receipt_sha256"
    ]

    value.pop("cross_binding_receipt_sha256")
    _rewrite_receipt(repo, path, value, "receipt v4 missing aggregate")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-schema\] receipt key set differs: ",
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical_line(value))


def test_v5_attempt_binding_accepts_all_predeclared_observed_units(
    tmp_path: Path,
) -> None:
    """The positive pair for the v5 attempt-registry rejection branches."""
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "valid receipt v5 attempt binding")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    projection = verified.receipt.attempt_slot_projection
    assert projection is not None
    assert projection.prereg_generation == 13
    assert projection.unit_count == 6
    assert verified.receipt.prereg_content_commit == value[
        "prereg_content_commit"
    ]
    assert verified.receipt.prereg_effective_commit == value[
        "prereg_effective_commit"
    ]
    assert (
        receipt.require_current_verified_receipt(verified).sha256
        == verified.sha256
    )


def test_v5_rejects_reaggregated_single_cross_binding_leaf_substitution(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "valid receipt before leaf substitution")
    receipt.verify_acceptance_receipt(path, repository_root=repo)

    last_row = value["trials"][-1]
    original_leaf = last_row["cross_binding_receipt_sha256"]
    forged_leaf = hashlib.sha256(b"forged-cross-binding-leaf").hexdigest()
    assert forged_leaf != original_leaf
    last_row["cross_binding_receipt_sha256"] = forged_leaf
    value["cross_binding_receipt_sha256"] = _cross_binding_aggregate_for_schema(
        value, receipt.CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
    )
    _rewrite_receipt(repo, path, value, "reaggregated forged final trial leaf")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            rf"^\[receipt-cross-binding\] trial_id={last_row['trial_id']} leaf "
            r"differs from independently rederived projection$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_m4_downstream_capability_rejects_readable_v4_receipt(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    value["schema_version"] = receipt.CROSS_BINDING_V2_SCHEMA_VERSION
    for field in (
        "prereg_content_commit",
        "prereg_effective_commit",
        "attempt_registry_path",
        "attempt_registry_prefix_bytes",
        "attempt_registry_prefix_sha256",
        "attempt_slot_projection",
    ):
        value.pop(field)
    _rewrite_receipt(repo, path, value, "readable legacy receipt v4")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-capability\] downstream capability requires the "
            r"current receipt schema$"
        ),
    ):
        receipt.require_current_verified_receipt(verified)


def test_v5_rejects_attempt_registry_bound_to_another_manifest(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(
        tmp_path, attempt_manifest_sha256="f" * 64,
    )
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "receipt with other-manifest registry")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-attempt-binding\] attempt registry manifest_sha256 "
            r"differs from receipt$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v5_rejects_attempt_registry_bound_to_another_content_commit(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    registry_binding_commit = value["prereg_commit"]
    value["prereg_content_commit"] = _run(
        repo, "rev-parse", "HEAD",
    ).stdout.strip()
    assert value["prereg_content_commit"] != registry_binding_commit
    _upgrade_to_current(
        repo,
        value,
        binding_prereg_content_commit=registry_binding_commit,
    )
    _rewrite_receipt(repo, path, value, "receipt with other-P registry")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-attempt-registry\] \[attempt-binding\] attempt row "
            r"content commit differs from receipt prereg_content_commit$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v5_rejects_attempt_registry_bound_to_another_effective_commit(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    registry_binding_commit = _run(repo, "rev-parse", "HEAD").stdout.strip()
    value["prereg_effective_commit"] = value["prereg_commit"]
    assert value["prereg_effective_commit"] != registry_binding_commit
    _upgrade_to_current(
        repo,
        value,
        binding_prereg_effective_commit=registry_binding_commit,
    )
    _rewrite_receipt(repo, path, value, "receipt with other-C registry")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-attempt-registry\] \[attempt-binding\] attempt row "
            r"effective commit differs from receipt prereg_effective_commit$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v5_rejects_registry_first_tracked_after_prereg_commit(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path, track_attempt_genesis=False)
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "receipt with late complete registry")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-attempt-binding\] attempt registry does not extend "
            r"the genesis at prereg_content_commit$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v5_rejects_second_registry_root_on_another_ref(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "valid receipt before alternate root")
    original_branch = _run(repo, "branch", "--show-current").stdout.strip()
    assert original_branch
    assert _run(repo, "checkout", "-q", "-b", "alternate-root").returncode == 0
    canonical = repo.joinpath(*receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.parts)
    alternate = repo / "alternate" / "attempt-registry.jsonl"
    _write(alternate, canonical.read_bytes().splitlines(keepends=True)[0])
    _commit_all(repo, "alternate attempt registry root")
    assert _run(repo, "checkout", "-q", original_branch).returncode == 0

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-history\] alternate attempt registry genesis exists "
            r"on a ref$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def _t2613_repo(tmp_path: Path, *, initial: str = "genesis"):
    source, _, value = _fixture(tmp_path)
    _upgrade_to_current(source, value)
    full = (source / receipt.DEFAULT_ATTEMPT_REGISTRY_PATH).read_bytes()
    genesis = full.splitlines(keepends=True)[0]
    rows = attempt_core.load_attempt_registry(full, profile=receipt._RECEIPT_ATTEMPT_PROFILE)
    other_rows = attempt_core.create_attempt_registry_genesis(
        profile=receipt._RECEIPT_ATTEMPT_PROFILE,
        freeze_id="independent-longer-receipt-history-fixture",
        manifest_path=PurePosixPath(rows[0]["manifest_path"]),
        manifest_sha256=rows[0]["manifest_sha256"], slots=rows[0]["slots"],
    )
    other = _canonical_line(other_rows[0])
    assert len(other) > len(genesis) and not other.startswith(genesis)
    repo = tmp_path / "history"
    repo.mkdir()
    for args in (("init", "-q"), ("config", "user.email", "test@example.invalid"),
                 ("config", "user.name", "History")):
        assert _run(repo, *args).returncode == 0
    canonical = repo / receipt.DEFAULT_ATTEMPT_REGISTRY_PATH
    if initial != "empty":
        _write(canonical, genesis if initial == "genesis" else genesis[:-1])
        _commit_all(repo, "initial canonical")
    return repo, canonical, genesis, full, other


def _t2613_gate(repo: Path, current: bytes, **kwargs):
    return receipt._assert_attempt_registry_history_append_only(
        repo, receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        current_bytes=current, **kwargs,
    )


def _t2613_index_blob(repo: Path, path: str, data: bytes, mode: str) -> str:
    result = receipt._git(repo, ("hash-object", "-w", "--stdin"), input_bytes=data)
    assert result.returncode == 0, result.stderr
    oid = result.stdout.decode().strip()
    result = _run(repo, "update-index", "--add", "--cacheinfo", f"{mode},{oid},{path}")
    assert result.returncode == 0, result.stderr
    assert _run(repo, "commit", "-q", "-m", "index blob").returncode == 0
    return oid


def _t2613_merge(repo: Path, *, alternate: bytes | None = None) -> None:
    branch = _run(repo, "branch", "--show-current").stdout.strip()
    assert _run(repo, "checkout", "-q", "-b", "side").returncode == 0
    _write(repo / "side", b"side")
    _commit_all(repo, "side")
    assert _run(repo, "checkout", "-q", branch).returncode == 0
    _write(repo / "main", b"main")
    _commit_all(repo, "main")
    assert _run(repo, "merge", "--no-ff", "--no-commit", "side").returncode == 0
    if alternate is not None:
        _write(repo / "alternate", alternate)
    _commit_all(repo, "merge")


@pytest.mark.parametrize("case", ["append-merge", "gitlink", "symlink-target", "unusual-path"])
def test_t2613_history_accepts(tmp_path: Path, case: str) -> None:
    repo, canonical, genesis, full, _ = _t2613_repo(tmp_path)
    current = genesis
    if case == "append-merge":
        lines = full.splitlines(keepends=True)
        for prefix in (b"".join(lines[:2]), full):
            attempt_core.load_attempt_registry(prefix, profile=receipt._RECEIPT_ATTEMPT_PROFILE)
            canonical.write_bytes(prefix)
            _commit_all(repo, "valid append")
        current = full
        _t2613_merge(repo)
    elif case == "gitlink":
        assert _run(repo, "update-index", "--add", "--cacheinfo",
                    "160000," + "a" * 40 + ",alternate").returncode == 0
        assert _run(repo, "commit", "-q", "-m", "missing gitlink").returncode == 0
    elif case == "symlink-target":
        (repo / "alternate").symlink_to(receipt.DEFAULT_ATTEMPT_REGISTRY_PATH)
        _commit_all(repo, "symlink path text")
    else:
        unusual = repo / "tab\tline\n日本語:entry"
        _write(unusual, b"harmless\0bytes\n")
        _commit_all(repo, "unusual path")
        unusual.chmod(0o755)
        _commit_all(repo, "mode only")
    assert _t2613_gate(repo, current) == current


@pytest.mark.parametrize("case", [
    "alternate-ref", "delete-recreate", "non-prefix", "copy-same-oid",
    "symlink-bytes", "root-only", "merge-only", "type-change", "invalid-utf8",
    "working-prefix", "canonical-schema", "canonical-gitlink-mode",
])
def test_t2613_history_rejects(tmp_path: Path, case: str) -> None:
    initial = "empty" if case == "root-only" else "schema" if case == "canonical-schema" else "genesis"
    repo, canonical, genesis, _, other = _t2613_repo(tmp_path, initial=initial)
    current = genesis
    message = "alternate attempt registry genesis exists on a ref"
    if case == "alternate-ref":
        branch = _run(repo, "branch", "--show-current").stdout.strip()
        assert _run(repo, "checkout", "-q", "-b", "unmerged").returncode == 0
        _write(repo / "alternate", other)
        _commit_all(repo, "alternate on unmerged ref")
        assert _run(repo, "checkout", "-q", branch).returncode == 0
    elif case == "delete-recreate":
        canonical.unlink()
        _commit_all(repo, "delete")
        canonical.write_bytes(genesis)
        _commit_all(repo, "recreate")
        message = "attempt registry was deleted"
    elif case == "non-prefix":
        canonical.write_bytes(other)
        _commit_all(repo, "valid but divergent")
        current = other
        message = "is not a strict prefix extension"
    elif case == "copy-same-oid":
        _write(repo / "alternate", genesis)
        _commit_all(repo, "identical blob copy")
        assert _run(repo, "rev-parse", "HEAD:alternate").stdout == _run(
            repo, "rev-parse", "HEAD:" + receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(),
        ).stdout
    elif case == "symlink-bytes":
        _t2613_index_blob(repo, "alternate", other, "120000")
    elif case == "root-only":
        assert _run(repo, "config", "log.showRoot", "false").returncode == 0
        _write(repo / "alternate", other)
        _commit_all(repo, "root alternate")
        (repo / "alternate").unlink()
        _write(repo / "ordinary", b"ordinary")
        _commit_all(repo, "remove alternate")
    elif case == "merge-only":
        _t2613_merge(repo, alternate=other)
    elif case == "type-change":
        (repo / "alternate").symlink_to("ordinary")
        _commit_all(repo, "harmless symlink")
        (repo / "alternate").unlink()
        _write(repo / "alternate", other)
        _commit_all(repo, "type change to genesis")
    elif case == "invalid-utf8":
        _write(repo / b"invalid-\xff".decode("utf-8", "surrogateescape"), b"ordinary")
        _commit_all(repo, "non UTF-8 path")
        message = "attempt tree entry is not valid UTF-8"
    elif case == "working-prefix":
        current = other
        message = "working attempt registry does not extend committed history"
    elif case == "canonical-schema":
        message = r"\[receipt-attempt-registry\]"
    else:
        _t2613_index_blob(repo, receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix(), genesis, "160000")
        message = "attempt registry was deleted"
    with pytest.raises(receipt.AcceptanceReceiptError, match=message):
        _t2613_gate(repo, current)


@pytest.mark.parametrize("first", ["alternate", "canonical", "same-commit", "path"])
def test_t2613_history_error_order(tmp_path: Path, first: str) -> None:
    repo, canonical, genesis, _, other = _t2613_repo(tmp_path)
    if first == "alternate":
        _write(repo / "alternate", other)
        _commit_all(repo, "alternate first")
    if first == "path":
        _write(repo / b"bad-\xff".decode("utf-8", "surrogateescape"), b"ordinary")
    canonical.write_bytes(other)
    if first == "same-commit":
        _write(repo / "alternate", other)
    _commit_all(repo, "canonical violation")
    if first == "canonical":
        _write(repo / "alternate", other)
        _commit_all(repo, "alternate later")
    expected = ("alternate attempt" if first == "alternate" else
                "not valid UTF-8" if first == "path" else "is not a strict prefix")
    with pytest.raises(receipt.AcceptanceReceiptError, match=expected):
        _t2613_gate(repo, other)


def test_t2613_batch_rejects_last_chunk_genesis(tmp_path: Path) -> None:
    repo, _, genesis, _, other = _t2613_repo(tmp_path)
    _write(repo / "a-ordinary", b"ordinary")
    _commit_all(repo, "ordinary blob")
    _write(repo / "z-genesis", other)
    _commit_all(repo, "last chunk alternate")
    with pytest.raises(receipt.AcceptanceReceiptError, match="alternate attempt"):
        _t2613_gate(repo, genesis, batch_max_bytes=1)


@pytest.mark.parametrize("case", ["boundary", "last-single", "oversize-single"])
def test_t2613_batch_chunks(tmp_path: Path, case: str) -> None:
    repo, _, genesis, _, _ = _t2613_repo(tmp_path)
    for name, data in (("a", b"a\0\n"), ("b", b""), ("c", b"ccc")):
        _write(repo / name, data)
    _commit_all(repo, "chunk bodies")
    oids = [receipt._git(repo, ("rev-parse", "HEAD:" + path)).stdout.strip()
            for path in ("a", "b", "c")]
    entries = receipt._attempt_batch_check(repo, oids)
    sizes = [len(b" ".join(entry)) + 2 + int(entry[2]) for entry in entries]
    cap = sizes[0] if case == "boundary" else sum(sizes[:2]) if case == "last-single" else 1
    chunks = list(receipt._attempt_batch_chunks(entries, cap))
    assert [len(chunk) for chunk in chunks] == ([2, 1] if case == "last-single" else [1, 1, 1])
    assert [data for chunk in chunks for _, data in receipt._attempt_read_batch(repo, chunk)] == [b"a\0\n", b"", b"ccc"]
    assert _t2613_gate(repo, genesis, batch_max_bytes=cap) == genesis


def test_t2613_batch_rejects_truncated_body(tmp_path: Path) -> None:
    repo, _, _, _, _ = _t2613_repo(tmp_path)
    oid = receipt._git(repo, ("rev-parse", "HEAD:" + receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix())).stdout.strip()
    entries = receipt._attempt_batch_check(repo, [oid])
    result = receipt._git(repo, ("cat-file", "--batch"), input_bytes=oid + b"\n")
    assert result.returncode == 0
    for truncated in (result.stdout[:-1], result.stdout[:-10], b""):
        with pytest.raises(receipt.AcceptanceReceiptError, match="blob cannot be read"):
            list(receipt._attempt_parse_batch(truncated, entries))


def test_t2613_batch_rejects_missing_check_line(tmp_path: Path) -> None:
    repo, _, _, _, _ = _t2613_repo(tmp_path)
    oid = receipt._git(repo, ("rev-parse", "HEAD:" + receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.as_posix())).stdout.strip()
    requests = [oid, oid]
    result = receipt._git(repo, ("cat-file", "--batch-check"), input_bytes=b"\n".join(requests) + b"\n")
    assert result.returncode == 0
    with pytest.raises(receipt.AcceptanceReceiptError, match="blob cannot be read"):
        receipt._attempt_parse_batch_check(result.stdout.splitlines(keepends=True)[0], requests)


def test_t2613_raw_argv_disables_signature_output() -> None:
    assert "--no-show-signature" in receipt._ATTEMPT_HISTORY_RAW_ARGS


def test_t2613_batch_default_cap_is_256_mib() -> None:
    assert receipt._ATTEMPT_BATCH_MAX_BYTES == 256 * 1024 * 1024


@pytest.mark.parametrize("valid", [True, False], ids=["success", "nonzero"])
def test_t2613_git_stdin(tmp_path: Path, valid: bool) -> None:
    repo, _, _, _, _ = _t2613_repo(tmp_path)
    data = b"binary\0payload\n"
    result = receipt._git(repo, ("hash-object", "--stdin", "-t", "blob" if valid else "tree"), input_bytes=data)
    if valid:
        assert result.returncode == 0
        assert result.stdout.strip().decode() == hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    else:
        assert result.returncode != 0


def test_m3_v5_rejects_predeclared_unit_without_final_terminal(
    tmp_path: Path,
) -> None:
    """M3 removes only one final terminal before the first tracked prefix."""
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    attempt_path = repo.joinpath(*receipt.DEFAULT_ATTEMPT_REGISTRY_PATH.parts)
    rows = attempt_path.read_bytes().splitlines()
    assert json.loads(rows[-1])["event"] == "terminal"
    truncated = b"\n".join(rows[:-1]) + b"\n"
    attempt_path.write_bytes(truncated)
    value["attempt_registry_prefix_bytes"] = len(truncated)
    value["attempt_registry_prefix_sha256"] = hashlib.sha256(truncated).hexdigest()
    _rewrite_receipt(repo, path, value, "receipt v5 missing one final terminal")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-attempt-consumption\] predeclared unit does not have "
            r"exactly one final terminal$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_m3b_v5_rejects_receipt_projection_divergent_from_registry(
    tmp_path: Path,
) -> None:
    """All terminals remain valid; only one receipt-side slot_id is changed."""
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    units = value["attempt_slot_projection"]["units"]
    units[0]["slot_id"] = "a-receipt-only-slot"
    assert units == sorted(units, key=lambda unit: unit["slot_id"])
    _rewrite_receipt(repo, path, value, "receipt-only projection divergence")

    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"^\[receipt-attempt-projection\] attempt registry slot projection "
            r"differs from receipt$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_p1_v5_accepts_observed_and_terminal_failure_mix(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    failure_trials = frozenset({
        value["trials"][1]["trial_id"],
        value["trials"][4]["trial_id"],
    })
    _upgrade_to_current(
        repo, value, terminal_failure_trials=failure_trials,
    )
    _rewrite_receipt(repo, path, value, "receipt v5 mixed final statuses")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert {trial.status for trial in verified.trials} == {"complete", "partial"}


def test_p2_v5_accepts_retryable_failure_followed_by_next_attempt(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    retry_trial_id = value["trials"][0]["trial_id"]
    _upgrade_to_current(repo, value, retry_trial_id=retry_trial_id)
    _rewrite_receipt(repo, path, value, "receipt v5 retry then final")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.attempt_slot_projection is not None
    assert verified.receipt.attempt_slot_projection.unit_count == 6


@pytest.mark.parametrize(
    "schema_version",
    [
        receipt.LEGACY_SCHEMA_VERSION,
        receipt.PREVIOUS_SCHEMA_VERSION,
        receipt.CROSS_BINDING_V1_SCHEMA_VERSION,
        receipt.CROSS_BINDING_V2_SCHEMA_VERSION,
        receipt.SCHEMA_VERSION,
    ],
)
def test_missing_schema_version_is_acceptance_receipt_error(
    tmp_path: Path, schema_version: str,
) -> None:
    _repo, _path, value = _fixture(tmp_path)
    value["schema_version"] = schema_version
    value.pop("schema_version")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"^\[receipt-schema\] receipt\.schema_version is missing$",
    ):
        receipt.parse_acceptance_receipt_bytes(_canonical_line(value))


def test_v3_aggregate_is_recomputed_from_trial_leaves(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    _rewrite_receipt(repo, path, value, "receipt v4 aggregate")
    value["cross_binding_receipt_sha256"] = "f" * 64
    _rewrite_receipt(repo, path, value, "receipt v4 forged aggregate")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=(
            r"\[receipt-cross-binding\] top-level cross-binding aggregate "
            r"differs from trial leaves$"
        ),
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v3_remains_bound_to_cross_binding_v1_domain(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    value["schema_version"] = receipt.CROSS_BINDING_V1_SCHEMA_VERSION
    for index, row in enumerate(value["trials"]):
        row["cross_binding_receipt_sha256"] = hashlib.sha256(
            f"legacy-cross-binding-leaf-{index}".encode("ascii")
        ).hexdigest()
    legacy_aggregate = _cross_binding_aggregate_for_schema(
        value, receipt.LEGACY_CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
    )
    current_aggregate = _cross_binding_aggregate_for_schema(
        value, receipt.CROSS_BINDING_RECEIPT_SCHEMA_VERSION,
    )
    assert legacy_aggregate != current_aggregate
    value["cross_binding_receipt_sha256"] = legacy_aggregate
    _rewrite_receipt(repo, path, value, "legacy receipt v3 domain")
    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.CROSS_BINDING_V1_SCHEMA_VERSION

    value["cross_binding_receipt_sha256"] = current_aggregate
    _rewrite_receipt(repo, path, value, "legacy receipt v3 with v2 domain")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-cross-binding\] top-level cross-binding aggregate differs",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


def test_v4_remains_readable_without_v5_attempt_binding(tmp_path: Path) -> None:
    repo, path, value = _fixture(tmp_path)
    _upgrade_to_current(repo, value)
    value["schema_version"] = receipt.CROSS_BINDING_V2_SCHEMA_VERSION
    for field in (
        "prereg_content_commit",
        "prereg_effective_commit",
        "attempt_registry_path",
        "attempt_registry_prefix_bytes",
        "attempt_registry_prefix_sha256",
        "attempt_slot_projection",
    ):
        value.pop(field)
    _rewrite_receipt(repo, path, value, "legacy receipt v4 remains readable")

    verified = receipt.verify_acceptance_receipt(path, repository_root=repo)
    assert verified.receipt.schema_version == receipt.CROSS_BINDING_V2_SCHEMA_VERSION
    assert verified.receipt.attempt_slot_projection is None


def test_binding_digest_is_rederived_from_self_consistent_three_way_claim(
    tmp_path: Path,
) -> None:
    repo, path, value = _fixture(tmp_path)
    row = _trial(value, "H2", "off")
    forged = "d" * 64
    row["arm_execution"]["arm_binding_digest_sha256"] = forged
    report_path = repo / row["report_path"]
    report = json.loads(report_path.read_bytes())
    report["arm_execution"]["arm_binding_digest_sha256"] = forged
    report_bytes = _canonical(report)
    report_path.write_bytes(report_bytes)
    row["report_sha256"] = hashlib.sha256(report_bytes).hexdigest()
    journal_path = repo / row["attempt_journal_path"]
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
    events[0]["arm_execution"]["arm_binding_digest_sha256"] = forged
    journal_bytes = b"".join(_canonical_line(event) for event in events)
    journal_path.write_bytes(journal_bytes)
    row["attempt_journal_sha256"] = hashlib.sha256(journal_bytes).hexdigest()
    _rewrite_receipt(repo, path, value, "self-consistent forged binding")
    with pytest.raises(
        receipt.AcceptanceReceiptError,
        match=r"\[receipt-arm-binding\] arm binding digest differs from receipt inputs$",
    ):
        receipt.verify_acceptance_receipt(path, repository_root=repo)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
