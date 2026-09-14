# -*- coding: utf-8 -*-
"""8b oracle report の manifest 限定・物理 trial 区間復元を検査する。"""
from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest import mock

import pytest

ORCH = Path(__file__).resolve().parents[1]
ROOT = ORCH.parent
sys.path.insert(0, str(ORCH.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import s8b_v2_freeze_fixture as v2_fixture  # noqa: E402
import s8b_oracle_spec_fixture as spec_fixture  # noqa: E402
import test_s8b_ratified_freeze as ratified_fixture  # noqa: E402
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402
from orchestrator.campaign import (  # noqa: E402
    artifact_admission as admission,
    env_contract,
    execution_guard,
    layout as campaign_layout_module,
    model,
    s8b_abort_reason_contract as abort_reason_contract,
    s8b_freeze_io,
    s8b_holdout_freeze as holdout_freeze,
    s8b_outcome_stage_contract as outcome_stage_contract,
    s8b_oracle_judge as judge,
    s8b_oracle_manifest as oracle_manifest,
    s8b_oracle_spec as oracle_spec,
    s8b_oracle_report as report,
    wal,
)
from orchestrator.campaign import s8b_oracle_artifacts as artifacts  # noqa: E402
from orchestrator.campaign.layout import campaign_layout, exploration_campaign_layout  # noqa: E402
from orchestrator.calibrator import perf_preflight  # noqa: E402

pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")


# 注意: holdout の三軸 conjunction はテストへ静止させない。
# holdout ID と全 cell は freeze から実行時に組み立てる。
REAL_FREEZE = ROOT / "output/s8b-freeze/holdout_freeze.json"
CONFIGURATIONS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
GENERATOR_SOURCES = {
    "materializer": "orchestrator/campaign/s1_direct_comparison.py",
    "report": "orchestrator/campaign/s8b_oracle_report.py",
    "judge": "orchestrator/campaign/s8b_oracle_judge.py",
    "outcome_stage_contract": (
        "orchestrator/campaign/s8b_outcome_stage_contract.py"
    ),
    "artifacts": "orchestrator/campaign/s8b_oracle_artifacts.py",
}
SESSION = report.SESSION_STAGE
GENOME = "Silo|BACK_OFF=1"
SRC_TOKEN = "source-digest"
VARIANT = "same-variant"
_DEFAULT_ABORT_PAYLOAD = object()
_MISSING_RETURN_CODES = object()
_T080_ABSENT = object()
_T080_DEFAULT = object()
_ISSUER_IDENTITY_ISSUE = "oracle session record.variant が issuer と不一致"
_ENV_CONSISTENCY_ISSUE = (
    "oracle session record.env_tag が campaign 内で一意でない"
)
_MANIFEST_ENV_ISSUE = (
    "oracle session record.env_tag が manifest.run_contract.env_tag と不一致"
)
_SPEC_FIXTURES: dict[str, spec_fixture.ReviewedSpecFixture] = {}


def _mark_official(root: Path) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "namespace.json"
    marker.write_bytes(artifacts.OFFICIAL_NAMESPACE_BYTES)
    return marker


def _e1_epoch() -> admission.CampaignVerifierEpoch:
    return admission.CampaignVerifierEpoch(
        campaign_verifier_epoch=f"E1:{'e' * 64}",
        state="E1",
        reason_code="recorded-closure",
    )


@pytest.fixture(autouse=True)
def _hermetic_t080_never_issued(monkeypatch):
    """実 repository の receipt 発行状態から既存 report test を分離する。"""
    resolution = report._t080.ReceiptResolution(
        "never-issued", (), None, "0" * 40,
    )
    monkeypatch.setattr(
        report._t080, "inspect_receipt_history",
        lambda *, root, validation_head=None, check_worktree=True: resolution,
    )


@pytest.fixture(autouse=True)
def _hermetic_certified_campaign_epoch(monkeypatch):
    """Report 単体テストを中央 gate の Git/worktree 状態から分離する。"""
    monkeypatch.setattr(
        report,
        "_campaign_verifier_epoch_from_lock_bytes",
        lambda _lock_bytes: _e1_epoch(),
    )


def _canonical_sha256(value) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _t080_envelope(marker: str = "a") -> dict:
    """揮発する実 HEAD を使わない exact observation fixture。"""
    sha1 = marker * 40
    sha256 = marker * 64
    items = [{
        "artifact": spec.artifact,
        "kind": "source-repin",
        "subject": spec.json_pointer,
        "recorded": spec.recorded_sha256,
        "observed": sha256,
        "status": "repinned-to-basis-blob",
    } for spec in report._t080.SOURCE_REPIN_SPECS]
    items.extend({
        "artifact": spec.artifact,
        "kind": "generator-metadata",
        "subject": spec.json_pointer,
        "recorded": spec.recorded_sha256,
        "observed": sha256,
        "status": "metadata-only",
    } for spec in report._t080.METADATA_SPECS)
    items.extend((
        {
            "artifact": "known_axes", "kind": "ancestry",
            "subject": "/frozen_at_head",
            "recorded": report._t080.KNOWN_AXES_RECORDED_HEAD,
            "observed": None, "status": "missing-commit",
        },
        {
            "artifact": "holdout", "kind": "ancestry",
            "subject": "/frozen_at_head",
            "recorded": report._t080.HOLDOUT_RECORDED_HEAD,
            "observed": None, "status": "missing-commit",
        },
    ))
    return {
        "schema_version": report._t080.OBSERVATION_SCHEMA_VERSION,
        "migration_id": report._t080.MIGRATION_ID,
        "receipt": {
            "path": report._t080.RECEIPT_REL,
            "raw_sha256": sha256,
        },
        "migration_basis_commit": sha1,
        "validation_head": sha1,
        "items": items,
    }


def _mock_t080_resolution(monkeypatch, state: str, observation: dict | None = None):
    roots: list[Path] = []
    resolution = report._t080.ReceiptResolution(
        state, (), observation, "f" * 40,
    )

    def inspect_receipt_history(*, root, validation_head=None, check_worktree=True):
        roots.append(Path(root))
        return resolution

    monkeypatch.setattr(report._t080, "inspect_receipt_history", inspect_receipt_history)
    if observation is not None:
        monkeypatch.setattr(
            report, "_expected_historical_envelope",
            lambda _history, *, repo_root, validation_head: observation,
        )
    return roots


def _source(path: str) -> dict:
    source = ROOT / path
    return {"path": path, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


def _freeze(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    document = json.loads(REAL_FREEZE.read_text(encoding="utf-8"))
    holdout_ids = tuple(document["holdouts"])
    # strict v2: per-pair floor + budget を共有 fixture で充填する (C3-4)。
    v2_fixture.fill(document)
    path = tmp_path / "holdout-freeze-fixture.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path, holdout_ids


def _binding(holdout_id: str, configuration_id: str) -> dict:
    projected = {
        "genome_canonical": GENOME,
        "src_token": SRC_TOKEN,
        "variant_id": VARIANT,
        "entry_sha256": _canonical_sha256({
            "holdout_id": holdout_id, "configuration_id": configuration_id,
        }),
    }
    return {
        "holdout_id": holdout_id,
        "configuration_id": configuration_id,
        **projected,
        "binding_sha256": _canonical_sha256(projected),
    }


def _manifest(tmp_path: Path, *, campaign_id: str = "oracle-b0", n: int = 1) -> dict:
    freeze_path, holdout_ids = _freeze(tmp_path)
    schedule = oracle_manifest.build_schedule(
        n=n, master_seed="report-fixture", block_sizes={"b0": n},
        holdout_ids=holdout_ids, configuration_ids=CONFIGURATIONS,
    )
    contract = env_contract.lookup("linux-baremetal")
    run_contract = {
        "ccbench_pin": "pin", "env_tag": contract.env_tag,
        "clocks": contract.clocks_per_us,
        "reps": 5, "extime": 5, "verify": "legacy+s2",
        "screening": "off", "bench_max_rounds": 1,
        "contract_sha256": contract.contract_sha256,
    }
    bindings = [
        _binding(holdout_id, configuration_id)
        for holdout_id in holdout_ids
        for configuration_id in CONFIGURATIONS
    ]
    generators = {
        "materializer": _source("orchestrator/campaign/s1_direct_comparison.py"),
        "report": _source("orchestrator/campaign/s8b_oracle_report.py"),
        "judge": _source("orchestrator/campaign/s8b_oracle_judge.py"),
        "outcome_stage_contract": _source(
            "orchestrator/campaign/s8b_outcome_stage_contract.py"
        ),
        "artifacts": _source("orchestrator/campaign/s8b_oracle_artifacts.py"),
    }
    approved = spec_fixture.make_reviewed_spec(
        root=ROOT, n=n, master_seed="report-fixture",
        block_sizes={"b0": n}, holdout_ids=holdout_ids,
        configuration_ids=CONFIGURATIONS, run_contract=run_contract,
        campaign_ids={"b0": campaign_id}, binding_identity=bindings,
        allowed_excluded_reasons=["machine-fault"],
        generator_versions=generators,
    )
    _SPEC_FIXTURES[approved.sha256] = approved
    return oracle_manifest._build_manifest(
        freeze_path=freeze_path,
        spec_sha256=approved.sha256,
        schedule=schedule,
        run_contract=run_contract,
        binding_identity=bindings,
        campaign_ids={"b0": campaign_id},
        allowed_excluded_reasons=["machine-fault"],
        generator_versions=generators,
    )


def _verify_for_report(
        tmp_path: Path, manifest: artifacts.OfficialManifest,
) -> oracle_manifest.VerifiedManifest:
    """report API テスト用に production verifier から token を得る。"""
    manifest_path = (
        tmp_path
        / f"manifest-for-report-{len(tuple(tmp_path.glob('manifest-for-report-*')))}.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8",
    )
    freeze_path, _ = _freeze(tmp_path)
    verified_freeze = s8b_freeze_io.load_verified_freeze(freeze_path)
    approved = _SPEC_FIXTURES[manifest["spec_sha256"]]
    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        return oracle_manifest.verify_manifest(
            manifest_path,
            root=ROOT,
            freeze_document=verified_freeze.document,
            freeze_sha256=verified_freeze.sha256,
            approved_spec=approved.reviewed_spec,
        )


def _official_report_setup(
        output_root: Path, manifest: artifacts.OfficialManifest,
) -> oracle_manifest.VerifiedManifest:
    """Mark the root explicitly and prepare a normal report consumer token."""
    _mark_official(output_root)
    return _verify_for_report(output_root, manifest)


def _schema_less_legacy(manifest: Mapping) -> artifacts.LegacyManifest:
    document = copy.deepcopy(dict(manifest))
    document.pop("schema_version", None)
    return artifacts.load_official_manifest(
        json.dumps(document, ensure_ascii=False).encode("utf-8")
    )


def _ratified_cli_manifest(
        tmp_path: Path,
) -> tuple[
    Path, Path, artifacts.OfficialManifest, spec_fixture.ReviewedSpecFixture,
]:
    def fill_execution_snapshot(generation):
        # emitter が result.floors から独立投影した floor は保持し、
        # report fixture に必要な budget だけを追加する。
        generation["budget"] = v2_fixture.budget(
            generation, total_bench_s=1000.0, per_holdout_bench_s=1000.0,
        )

    root, ratified, topology = ratified_fixture.load_emitter_g1(
        tmp_path, mutate_g1=fill_execution_snapshot,
    )
    # Preserve the emitter's git-backed artifacts and expose an external
    # sibling as the official report output root.
    shutil.copytree(root / "output", root.parent / "output")
    _mark_official(root.parent / "output")
    freeze_path = root / topology["generation_path"]
    for role, relative_path in GENERATOR_SOURCES.items():
        source = root / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(
            f"hermetic report CLI generator fixture: {role}\n".encode("utf-8")
        )
    holdout_ids = tuple(ratified.document["holdouts"])
    schedule = oracle_manifest.build_schedule(
        n=1,
        master_seed="report-cli-fixture",
        block_sizes={"b0": 1},
        holdout_ids=holdout_ids,
        configuration_ids=CONFIGURATIONS,
    )
    contract = env_contract.lookup("linux-baremetal")
    generator_versions = {
        role: {
            "path": relative_path,
            "sha256": hashlib.sha256(
                (root / relative_path).read_bytes()
            ).hexdigest(),
        }
        for role, relative_path in GENERATOR_SOURCES.items()
    }
    run_contract = {
        "ccbench_pin": "pin",
        "env_tag": contract.env_tag,
        "clocks": contract.clocks_per_us,
        "reps": 5,
        "extime": 5,
        "verify": "legacy+s2",
        "screening": "off",
        "bench_max_rounds": 1,
        "contract_sha256": contract.contract_sha256,
    }
    bindings = [
        _binding(holdout_id, configuration_id)
        for holdout_id in holdout_ids
        for configuration_id in CONFIGURATIONS
    ]
    approved = spec_fixture.make_reviewed_spec(
        root=root, n=1, master_seed="report-cli-fixture",
        block_sizes={"b0": 1}, holdout_ids=holdout_ids,
        configuration_ids=CONFIGURATIONS, run_contract=run_contract,
        campaign_ids={"b0": "oracle-cli-b0"}, binding_identity=bindings,
        allowed_excluded_reasons=["machine-fault"],
        generator_versions=generator_versions,
    )
    spec_fixture.install_reviewed_spec(root, approved)
    with mock.patch.object(oracle_manifest, "ROOT", root):
        document = oracle_manifest._build_manifest(
            freeze_path=freeze_path,
            spec_sha256=approved.sha256,
            schedule=schedule,
            run_contract=run_contract,
            binding_identity=bindings,
            campaign_ids={"b0": "oracle-cli-b0"},
            allowed_excluded_reasons=["machine-fault"],
            generator_versions=generator_versions,
        )
    manifest_path = tmp_path / "ratified-cli-manifest.json"
    oracle_manifest._write_manifest(manifest_path, document)
    return root, manifest_path, document, approved


def _judge(observations, *, manifest_sha256=None, spec_sha256=None):
    observations = artifacts.OfficialObservations(copy.deepcopy(observations))
    if (observations.get("manifest_kind") == "official"
            and "store_reverification" not in observations):
        logical_cell_ids = sorted({
            f"{entry['holdout_id']}::{entry['configuration_id']}"
            for entry in observations.get("expected_cells", [])
        })
        observations["store_reverification"] = {
            "state": "verified",
            "cells": [{
                "cell_id": cell_id,
                "store_path": f"fixture-store/{cell_id.replace('::', '--')}",
                "expected_sha256": "c" * 64,
                "actual_sha256": "c" * 64,
                "state": "match",
            } for cell_id in logical_cell_ids],
        }
    schedule_projection = judge.ManifestScheduleProjection(
        n_per_cell=observations.get("n_per_cell", 1),
        expected_cells=frozenset(
            (
                entry["schedule_index"],
                entry["holdout_id"],
                entry["configuration_id"],
            )
            for entry in observations.get("expected_cells", [])
            if isinstance(entry, Mapping)
            and set(entry) == judge._EXPECTED_CELL_KEYS
        ),
        expected_campaign_ids=frozenset(
            entry["campaign_id"]
            for entry in observations.get("campaign_verifier_epochs", [])
            if isinstance(entry, Mapping)
            and isinstance(entry.get("campaign_id"), str)
        ),
    )
    return judge.judge_oracle(
        observations,
        schedule_projection=schedule_projection,
        verified_manifest_sha256=(
            observations.get("manifest_sha256")
            if manifest_sha256 is None else manifest_sha256
        ),
        approved_spec_sha256=(
            observations.get("spec_sha256")
            if spec_sha256 is None else spec_sha256
        ),
    )


def _reverified_store_fixture(
        verified_manifest: oracle_manifest.VerifiedManifest,
        output_root: Path,
) -> tuple[object, dict[str, dict]]:
    binaries: dict[str, dict] = {}
    for row in verified_manifest.document["schedule"]["rows"]:
        cell_id = f"{row['holdout_id']}::{row['configuration_id']}"
        if cell_id in binaries:
            continue
        raw = f"store bytes for {cell_id}\n".encode("utf-8")
        relative_path = f"fixture-store/{cell_id.replace('::', '--')}/binary"
        path = output_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        binaries[cell_id] = {
            "cell_id": cell_id,
            "store_path": relative_path,
            "binary_sha256": hashlib.sha256(raw).hexdigest(),
        }
    token = report.s8b_ratified_freeze.ReverifiedFreeze(
        ratified=SimpleNamespace(
            sha256=verified_manifest.document["freeze"]["sha256"],
        ),
        activation_head="a" * 40,
        search_digest="b" * 64,
        symlink_gitlink_inventory=(),
        floor_artifact=SimpleNamespace(),
        binaries_by_cell=MappingProxyType(binaries),
    )
    return token, binaries


def _session(layout, event: str, payload: dict) -> None:
    wal.log(
        layout, "oracle-session", SESSION, "linux-baremetal",
        {"event": event, **payload},
    )


def _rewrite_session_identity(
        layout, *, event=None, variant=None, env_tag=None) -> None:
    """完成済み valid WAL の session record identity だけを負例へ書き換える。"""
    assert variant is not None or env_tag is not None
    lines = Path(layout.wal_file).read_text(encoding="utf-8").splitlines()
    rewritten = []
    rewrite_count = 0
    for line in lines:
        record = json.loads(line)
        payload = record.get("payload")
        if (
                record.get("stage") == SESSION
                and (
                    event is None
                    or isinstance(payload, dict) and payload.get("event") == event
                )):
            if variant is not None:
                record["variant"] = variant
            if env_tag is not None:
                record["env_tag"] = env_tag
            rewrite_count += 1
        rewritten.append(
            json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        )
    assert rewrite_count > 0, (event, variant, env_tag)
    Path(layout.wal_file).write_text(
        "\n".join(rewritten) + "\n", encoding="utf-8",
    )


def _campaign_start(layout, manifest: dict, campaign_id: str = "oracle-b0",
                    *, block_id: str = "b0", receipt: dict | None = None,
                    t080_observation: object = _T080_DEFAULT,
                    measurement_manifest: dict | None = None) -> None:
    lock_path = Path(layout.lock_file)
    if not lock_path.exists():
        lock_path.write_text(
            json.dumps({"fixture": "s8b oracle report"}), encoding="utf-8",
        )
    contract = env_contract.lookup("linux-baremetal")
    payload = {
        "manifest_sha256": oracle_manifest.manifest_sha256(manifest),
        "block_id": block_id,
        "campaign_id": campaign_id,
        # C3-10: manifest run_contract の env_tag/contract_sha256 と一致する execution
        # receipt を既定で載せる (report が受理する形)。負例は receipt=<改竄> で注入。
        "execution_receipt": receipt if receipt is not None else {
            "schema": execution_guard.RECEIPT_SCHEMA,
            "env_tag": contract.env_tag,
            "contract_sha256": contract.contract_sha256,
            "attestation": {
                "hostname": "fixture-host", "boot_id": None,
                "cpuset": None, "captured_utc": "2026-07-18T00:00:00+00:00",
            },
        },
    }
    if t080_observation is _T080_DEFAULT:
        payload["t080_freeze_migration_observation"] = {
            "state": "never-issued", "validation_head": "0" * 40,
        }
    elif t080_observation is not _T080_ABSENT:
        payload["t080_freeze_migration_observation"] = t080_observation
    if measurement_manifest is not None:
        payload["measurement_manifest"] = measurement_manifest
    _session(layout, "campaign-start", payload)


def _verify(
        layout, variant: str, tag: str, certified: bool,
        build_attempt_id: str,
) -> None:
    wal.log(layout, variant, "verify_done", "fixture-env", {
        "build_attempt_id": build_attempt_id,
        "verdict": "serializable" if certified else "cycle",
        "certified": certified,
        "anomalies": 0 if certified else 1,
        "workload": {"tag": tag},
    })


def _fixture_log(layout, variant: str, stage: str, payload: object) -> None:
    """不正 payload の負例だけ writer を迂回し、raw WAL 接点へ注入する。"""
    if isinstance(payload, dict):
        if stage == "commit":
            receipt_support.append_legacy_raw_commit(
                layout, variant, "fixture-env", payload,
            )
            return
        wal.log(layout, variant, stage, "fixture-env", payload)
        return
    record = {
        "variant": variant, "stage": stage, "env_tag": "fixture-env",
        "ts": 1, "payload": payload,
    }
    with open(layout.wal_file, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def _append_receipted_commit_raw(
        layout, variant: str, env_tag: str, payload: dict, *,
        operation_identity: str, tags: tuple[str, ...],
) -> None:
    """Append a valid receipt without reparsing intentionally broken history."""
    lock_identity = receipt_support.campaign_lock_sha256_or_absent(layout)
    receipt = receipt_support.campaign_receipt(
        layout, variant, payload,
        operation_identity=operation_identity,
        tags=tags,
        lock_identity_sha256=lock_identity,
    )
    serialized = receipt_support.validate_live_receipt(
        receipt,
        sink_kind=receipt_support.CAMPAIGN_WAL_SINK,
        lock_identity_sha256=lock_identity,
        variant=variant,
        terminal_payload=payload,
    )
    receipt_support.append_legacy_raw_commit(
        layout, variant, env_tag, {
            **payload,
            receipt_support.RECEIPT_PAYLOAD_KEY: serialized,
        },
    )


def _trial(layout, item: dict, outcome: str, *, variant: str = VARIANT,
           attempt: int = 1,
           tps: tuple[float, ...] = (10.0, 11.0, 12.0, 13.0, 14.0),
           rep_returncodes: object = (0, 0, 0, 0, 0),
           screen_marker: bool = False,
           excluded_reason: str | None = None,
           verify_frontier: str = "s2",
           abort_payload: object = _DEFAULT_ABORT_PAYLOAD,
           bench_payload_extra: Mapping | None = None,
           raw_receipted_commit: bool = False) -> None:
    def selected_abort_payload(default: object) -> object:
        if abort_payload is _DEFAULT_ABORT_PAYLOAD:
            return default
        if isinstance(default, dict) and isinstance(abort_payload, dict):
            merged = dict(abort_payload)
            for key in ("workload", "build_attempt_id"):
                if key in default and key not in merged:
                    merged[key] = default[key]
            return merged
        return abort_payload

    identity = {
        "schedule_index": item["schedule_index"],
        "holdout_id": item["holdout_id"],
        "configuration_id": item["configuration_id"],
        "attempt": attempt,
    }
    build_attempt_id = f"oracle-{item['schedule_index']}-{attempt}"
    _session(layout, "trial-start", identity)
    wal.log(layout, variant, "build_start", "fixture-env", {
        "genome": GENOME, "src_token": SRC_TOKEN,
        "build_attempt_id": build_attempt_id,
    })
    if outcome == "build-failed":
        _fixture_log(
            layout, variant, "abort",
            selected_abort_payload({
                "reason": "build-error", "build_attempt_id": build_attempt_id,
            }),
        )
    else:
        wal.log(layout, variant, "build_done", "fixture-env", {
            "trace_bin": "trace", "perf_bin": "perf",
            "build_attempt_id": build_attempt_id,
        })
        if outcome == "binary-mismatch":
            # C3-5: build_done 後・verify/bench 起動前の TOCTOU abort。
            _fixture_log(
                layout, variant, "abort",
                selected_abort_payload({
                    "reason": "bench-binary-mismatch",
                    "build_attempt_id": build_attempt_id,
                }),
            )
        elif outcome == "legacy-red":
            _verify(layout, variant, "legacy", False, build_attempt_id)
            _fixture_log(layout, variant, "abort", selected_abort_payload({
                "reason": "cycle", "workload": {"tag": "legacy"},
                "build_attempt_id": build_attempt_id,
            }))
        else:
            if (outcome in {"timeout", "verify-inconclusive"}
                    and verify_frontier == "legacy"):
                _fixture_log(layout, variant, "abort", selected_abort_payload({
                    "reason": ("trace-timeout" if outcome == "timeout" else "trace-empty"),
                    "workload": {"tag": "legacy"},
                    "build_attempt_id": build_attempt_id,
                }))
            else:
                _verify(layout, variant, "legacy", True, build_attempt_id)
                if outcome in {"timeout", "verify-inconclusive"}:
                    _fixture_log(layout, variant, "abort", selected_abort_payload({
                        "reason": (
                            "trace-timeout" if outcome == "timeout" else "trace-empty"
                        ),
                        "workload": {"tag": "s2"},
                        "build_attempt_id": build_attempt_id,
                    }))
                elif outcome == "s2-red":
                    _verify(layout, variant, "s2", False, build_attempt_id)
                    _fixture_log(layout, variant, "abort", selected_abort_payload({
                        "reason": "cycle", "workload": {"tag": "s2"},
                        "build_attempt_id": build_attempt_id,
                    }))
                else:
                    _verify(layout, variant, "s2", True, build_attempt_id)
                    if outcome == "bench-failed":
                        _fixture_log(
                            layout, variant, "abort",
                            selected_abort_payload({
                                "reason": "bench-no-throughput",
                                "build_attempt_id": build_attempt_id,
                            }),
                        )
                    else:
                        payload = {
                            "tps": list(tps),
                            "median_tps": sum(tps) / len(tps),
                        }
                        if rep_returncodes is not _MISSING_RETURN_CODES:
                            payload["rep_returncodes"] = (
                                list(rep_returncodes)
                                if isinstance(rep_returncodes, tuple)
                                else rep_returncodes
                            )
                        if screen_marker:
                            payload["screening"] = True
                        if bench_payload_extra is not None:
                            payload.update(dict(bench_payload_extra))
                        payload["build_attempt_id"] = build_attempt_id
                        wal.log(layout, variant, "bench_done", "fixture-env", payload)
                        commit_payload = {
                            "build_attempt_id": build_attempt_id,
                            "fitness_tps": sum(tps) / len(tps),
                            "verify_configs": ["legacy", "s2"],
                        }
                        if raw_receipted_commit:
                            _append_receipted_commit_raw(
                                layout, variant, "fixture-env", commit_payload,
                                operation_identity=build_attempt_id,
                                tags=("legacy", "s2"),
                            )
                        else:
                            receipt_support.log_receipted_commit(
                                layout, variant, "fixture-env", commit_payload,
                                operation_identity=build_attempt_id,
                                tags=("legacy", "s2"),
                            )
    declared = {
        "legacy-red": "correctness-red",
        "s2-red": "correctness-red",
    }.get(outcome, outcome)
    _session(layout, "trial-result", {
        **identity,
        "outcome": declared,
        "excluded_reason": excluded_reason,
        "screen_outcome": "not_enabled",
    })


def _layout(tmp_path: Path, manifest: dict, campaign_id: str = "oracle-b0"):
    _mark_official(tmp_path)
    layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, campaign_id)
    return layout


def _finish_campaign(layout, manifest: dict, *, status: str = "completed",
                     fill_missing: bool = True, scheduled_rows: int | None = None,
                     completed_rows: int | None = None) -> None:
    """新 campaign-terminal 契約へ追随する WAL fixture builder。"""
    schedule = manifest["schedule"]["rows"]
    if fill_missing:
        records, line_issues, truncated_tail = wal.read_records_collected(layout)
        raw_receipted_commit = bool(line_issues or truncated_tail)
        covered = {
            record.payload.get("schedule_index") for record in records
            if record.stage == SESSION and record.payload.get("event") == "trial-result"
        }
        for item in schedule:
            if item["schedule_index"] not in covered:
                _trial(
                    layout, item, "committed",
                    raw_receipted_commit=raw_receipted_commit,
                )
    _session(layout, "campaign-terminal", {
        "status": status,
        "scheduled_rows": len(schedule) if scheduled_rows is None else scheduled_rows,
        "completed_rows": (
            len(schedule) if completed_rows is None and status == "completed"
            else (0 if completed_rows is None else completed_rows)
        ),
        "execution_identity": {
            "job": "fixture-job", "host": "fixture-host", "boot": "fixture-boot",
            "pid": 123, "starttime": 456,
        },
    })


def _finish_campaign_rows(
        layout, rows: list[dict], *, bench_payload_extra: Mapping | None = None,
) -> None:
    """複数 campaign の横断契約テスト用に、所有 row だけを完了する。"""
    for item in rows:
        _trial(
            layout, item, "committed",
            bench_payload_extra=bench_payload_extra,
        )
    _session(layout, "campaign-terminal", {
        "status": "completed",
        "scheduled_rows": len(rows),
        "completed_rows": len(rows),
        "execution_identity": {
            "job": "fixture-job", "host": "fixture-host", "boot": "fixture-boot",
            "pid": 123, "starttime": 456,
        },
    })


def _two_campaign_manifest(tmp_path: Path) -> dict:
    manifest = _manifest(tmp_path)
    rows = copy.deepcopy(manifest["schedule"]["rows"][:2])
    rows[0]["block_id"] = "b0"
    rows[1]["block_id"] = "b1"
    manifest["schedule"]["rows"] = rows
    manifest["campaign_ids"] = {"b0": "oracle-b0", "b1": "oracle-b1"}
    return _schema_less_legacy(manifest)


def _two_campaign_report_setup(tmp_path: Path) -> dict:
    """Mark the root explicitly for a two-campaign report consumer."""
    _mark_official(tmp_path)
    return _two_campaign_manifest(tmp_path)


def _manual_trial(layout, item: dict, outcome: str,
                  pipeline: list[tuple[str, object]]) -> None:
    identity = {
        "schedule_index": item["schedule_index"],
        "holdout_id": item["holdout_id"],
        "configuration_id": item["configuration_id"],
        "attempt": 1,
    }
    _session(layout, "trial-start", identity)
    for stage, payload in pipeline:
        _fixture_log(layout, VARIANT, stage, payload)
    _session(layout, "trial-result", {
        **identity,
        "outcome": outcome,
        "excluded_reason": None,
        "screen_outcome": "not_enabled",
    })


def _trial_start(layout, item: dict, attempt: int, **identity_overrides) -> None:
    identity = {
        "schedule_index": item["schedule_index"],
        "holdout_id": item["holdout_id"],
        "configuration_id": item["configuration_id"],
        "attempt": attempt,
        **identity_overrides,
    }
    _session(layout, "trial-start", identity)


def _retry(layout, item: dict, next_attempt: int = 2, **payload_overrides) -> None:
    _session(layout, "retry", {
        "schedule_index": item["schedule_index"],
        "attempt": next_attempt,
        "reason": "transient prepare failure",
        **payload_overrides,
    })


def _append_pipeline(layout, pipeline: list[tuple[str, object]] | None = None) -> None:
    for stage, payload in pipeline or _valid_committed_pipeline():
        if stage == "commit":
            receipt_support.log_receipted_commit(
                layout, VARIANT, "fixture-env", payload,
                operation_identity=payload["build_attempt_id"],
                tags=("legacy", "s2"),
            )
            continue
        wal.log(layout, VARIANT, stage, "fixture-env", payload)


def _trial_result(layout, item: dict, attempt: int,
                  outcome: str = "committed", **identity_overrides) -> None:
    identity = {
        "schedule_index": item["schedule_index"],
        "holdout_id": item["holdout_id"],
        "configuration_id": item["configuration_id"],
        "attempt": attempt,
        **identity_overrides,
    }
    _session(layout, "trial-result", {
        **identity,
        "outcome": outcome,
        "excluded_reason": None,
        "screen_outcome": "not_enabled",
    })


def _valid_committed_pipeline() -> list[tuple[str, object]]:
    build_attempt_id = "oracle-manual-attempt"
    return [
        ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN,
                         "build_attempt_id": build_attempt_id}),
        ("build_done", {"trace_bin": "trace", "perf_bin": "perf",
                        "build_attempt_id": build_attempt_id}),
        ("verify_done", {
            "verdict": "serializable", "certified": True,
            "anomalies": 0, "build_attempt_id": build_attempt_id,
            "workload": {"tag": "legacy"},
        }),
        ("verify_done", {
            "verdict": "serializable", "certified": True,
            "anomalies": 0, "build_attempt_id": build_attempt_id,
            "workload": {"tag": "s2"},
        }),
        ("bench_done", {
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0], "median_tps": 12.0,
            "rep_returncodes": [0, 0, 0, 0, 0],
            "build_attempt_id": build_attempt_id,
        }),
        ("commit", {"fitness_tps": 12.0, "verify_configs": ["legacy", "s2"],
                    "build_attempt_id": build_attempt_id}),
    ]


def test_success_uses_real_manifest_and_binds_physical_trial_intervals(tmp_path):
    manifest = _manifest(tmp_path, n=2)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    _trial(layout, schedule[0], "committed", tps=(10.0, 11.0, 12.0, 13.0, 14.0))
    _trial(layout, schedule[1], "committed", tps=(20.0, 21.0, 22.0, 23.0, 24.0))
    _finish_campaign(layout, manifest)

    observations = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)

    assert type(observations) is artifacts.OfficialObservations
    assert observations["schema_version"] == report.SCHEMA_VERSION
    assert observations["manifest_kind"] == "official"
    assert [row["status"] for row in observations["rows"][:2]] == ["completed", "completed"]
    assert all(row["lifecycle_ok"] is True for row in observations["rows"][:2])
    assert [row["bench_values"] for row in observations["rows"][:2]] == [
        [10.0, 11.0, 12.0, 13.0, 14.0],
        [20.0, 21.0, 22.0, 23.0, 24.0],
    ]
    assert all(row["binding_ok"] for row in observations["rows"][:2])
    assert len(observations["expected_cells"]) == len(schedule)


@pytest.mark.parametrize("consumer", ["s8b"], ids=["s8b"])
def test_assess_window_requires_persisted_certification(tmp_path, consumer):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed")
    records = wal.read_records(layout)
    verify = next(record for record in records if record.stage == "verify_done")
    verify.payload["anomalies"] = 1
    Path(layout.wal_file).write_text(
        "".join(wal._record_to_line(record) + "\n" for record in records),
        encoding="utf-8",
    )
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )

    assert consumer == "s8b"
    row = observations["rows"][0]
    assert row["status"] == "protocol_violation"
    assert "persisted certification is invalid" in row["reason"]


def test_report_projects_e1_epoch_from_resolved_campaign_layout(
        tmp_path, monkeypatch):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    calls = []

    def certified(lock_bytes):
        calls.append(lock_bytes)
        return _e1_epoch()

    monkeypatch.setattr(
        report,
        "_campaign_verifier_epoch_from_lock_bytes",
        certified,
    )
    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )

    assert len(calls) == 1
    assert calls[0] == Path(layout.lock_file).read_bytes()
    assert observations["campaign_verifier_epochs"] == [{
        "campaign_id": "oracle-b0",
        "campaign_verifier_epoch": f"E1:{'e' * 64}",
        "state": "E1",
        "reason_code": "recorded-closure",
        "identity_scope": admission.CAMPAIGN_VERIFIER_EPOCH_SCOPE,
        "excluded_scope": admission.CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,
        "certified_eligible": True,
        "rejection": None,
    }]
    assert {row["campaign_id"] for row in observations["rows"]} == {
        "oracle-b0"
    }


@pytest.mark.parametrize(
    "epoch",
    [
        admission.CampaignVerifierEpoch(
            campaign_verifier_epoch="E0",
            state="E0",
            reason_code="v1-authority-absent",
        ),
        admission.CampaignVerifierEpoch(
            campaign_verifier_epoch=f"E1:{'d' * 64}",
            state="E1-stale",
            reason_code="recorded-current-closure-mismatch",
        ),
    ],
    ids=["e0", "e1-stale"],
)
def test_report_keeps_non_e1_epoch_rejection_as_structured_evidence(
        tmp_path, monkeypatch, epoch):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)

    def rejected(_lock_bytes):
        raise admission.CampaignVerifierEpochRejected(epoch)

    monkeypatch.setattr(
        report,
        "_campaign_verifier_epoch_from_lock_bytes",
        rejected,
    )
    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )

    evidence = observations["campaign_verifier_epochs"]
    assert len(evidence) == 1
    assert evidence[0]["state"] == epoch.state
    assert evidence[0]["reason_code"] == epoch.reason_code
    assert evidence[0]["certified_eligible"] is False
    assert evidence[0]["rejection"]["code"] == (
        "campaign-verifier-epoch-rejected"
    )
    assert all(row["status"] == "completed" for row in observations["rows"])
    verdict = _judge(observations)
    assert verdict["status"] == "indeterminate"
    assert {
        reason["code"] for reason in verdict["reasons"]
    } == {"campaign-verifier-epoch-rejected"}


def test_report_keeps_unreadable_epoch_as_structured_rejection(
        tmp_path, monkeypatch):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)

    def unavailable(_lock_bytes):
        raise admission.ArtifactAdmissionError("campaign.lock を読めない")

    monkeypatch.setattr(
        report,
        "_campaign_verifier_epoch_from_lock_bytes",
        unavailable,
    )
    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )

    evidence = observations["campaign_verifier_epochs"][0]
    assert evidence["campaign_verifier_epoch"] is None
    assert evidence["state"] == "unavailable"
    assert evidence["reason_code"] == "campaign-verifier-epoch-unavailable"
    assert evidence["certified_eligible"] is False
    assert evidence["rejection"]["code"] == (
        "campaign-verifier-epoch-unavailable"
    )


def test_build_observations_accepts_actual_verify_manifest_result(tmp_path):
    manifest = _manifest(tmp_path)
    verified = _official_report_setup(tmp_path, manifest)

    observations = report.build_observations(
        manifest=verified, output_root=tmp_path,
    )

    assert type(verified) is oracle_manifest.VerifiedManifest
    assert observations["manifest_kind"] == "official"
    assert observations["manifest_sha256"] == verified.sha256
    assert observations["spec_sha256"] == verified.document["spec_sha256"]


def test_legacy_manifest_cannot_launder_spec_sha256_into_observations_or_judge(
        tmp_path):
    _mark_official(tmp_path)
    official = _manifest(tmp_path)
    assert isinstance(official["spec_sha256"], str)
    legacy = _schema_less_legacy(official)

    observations = report.build_observations(
        manifest=legacy, output_root=tmp_path,
    )
    assert observations["manifest_kind"] == "legacy"
    assert "spec_sha256" not in observations

    verdict = _judge(
        observations,
        manifest_sha256=observations["manifest_sha256"],
        spec_sha256=official["spec_sha256"],
    )
    assert verdict["status"] == "indeterminate"
    assert any(reason["code"] == "spec-sha256" for reason in verdict["reasons"])


def test_build_observations_rejects_unverified_official_manifest(tmp_path):
    official = _manifest(tmp_path)

    with pytest.raises(artifacts.OracleArtifactTypeError, match="exact type"):
        report.build_observations(manifest=official, output_root=tmp_path)


@pytest.mark.parametrize(
    "drift",
    ["nested-field", "top-level-injection", "top-level-deletion"],
)
def test_build_observations_rejects_verified_document_hash_drift(
        tmp_path, drift):
    verified = _official_report_setup(tmp_path, _manifest(tmp_path))
    if drift == "nested-field":
        verified.document["allowed_excluded_reasons"].append("post-verify-drift")
    elif drift == "top-level-injection":
        verified.document["manifest_sha256"] = "x"
    else:
        verified.document.pop("generator_versions")

    with pytest.raises(report.ReportError, match="canonical hash"):
        report.build_observations(manifest=verified, output_root=tmp_path)


def test_report_reexports_outcome_and_pipeline_authorities_without_reliteralizing():
    # '-' 入り literal を CPython が自動 intern しないことに依存し、再 literal 化を検出する。
    assert report.SESSION_STAGE is model.STAGE_S8B_ORACLE_SESSION
    assert report.OUTCOMES is outcome_stage_contract.OUTCOMES
    assert report.PIPELINE_STAGES is outcome_stage_contract.PIPELINE_STAGES


@pytest.mark.parametrize("actual_reps", [3, 4, 6])
def test_committed_bench_requires_exact_manifest_reps(tmp_path, actual_reps):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", tps=tuple(float(i) for i in range(actual_reps)))
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []
    assert f"actual={actual_reps}, expected=5" in row["reason"]


def test_huge_integer_tps_is_row_level_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    pipeline = _valid_committed_pipeline()
    pipeline[4] = ("bench_done", {
        "tps": [10**400] * 5,
        "median_tps": 0.0,
        "rep_returncodes": [0, 0, 0, 0, 0],
    })
    pipeline[5] = (
        "commit", {"fitness_tps": 0.0, "verify_configs": ["legacy", "s2"]},
    )
    _manual_trial(layout, item, "committed", pipeline)
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []
    assert "bench_done.tps が空または非有限値を含む" in row["reason"]


def test_run_contract_reps_must_match_approved_leaf_even_when_tps_matches(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["run_contract"]["reps"] = 4
    manifest = _schema_less_legacy(manifest)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", tps=(1.0, 2.0, 3.0, 4.0, 5.0))
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )
    row = observations["rows"][0]
    expected_reason = (
        "manifest.run_contract.reps が APPROVED_REPS と不一致: "
        "actual=4, expected=5"
    )

    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []
    assert row["reason"] == expected_reason
    assert "bench_done.tps 件数" not in row["reason"]
    assert "bench_done.rep_returncodes 件数" not in row["reason"]
    assert observations["manifest_issues"] == [{
        "code": "run-contract-reps-not-approved",
        "campaign_id": None,
        "message": expected_reason,
    }]
    assert "campaign-start.manifest_sha256" not in row["reason"]


@pytest.mark.parametrize(
    ("damage", "expected_code", "expected_reason"),
    [
        pytest.param(
            ["not-an-object"],
            "run-contract-not-object",
            "manifest.run_contract が object でない",
            id="not-object",
        ),
        pytest.param(
            True,
            "run-contract-reps-not-positive-int",
            "manifest.run_contract.reps が非 bool の正整数でない",
            id="bool-reps",
        ),
        pytest.param(
            0,
            "run-contract-reps-not-positive-int",
            "manifest.run_contract.reps が非 bool の正整数でない",
            id="zero-reps",
        ),
    ],
)
def test_run_contract_reps_declaration_is_fail_closed(
        tmp_path, damage, expected_code, expected_reason):
    manifest = _manifest(tmp_path)
    if isinstance(damage, list):
        manifest["run_contract"] = damage
    else:
        manifest["run_contract"]["reps"] = damage
    manifest = _schema_less_legacy(manifest)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )
    rows = observations["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert {row["reason"] for row in rows} == {expected_reason}
    assert observations["manifest_issues"] == [{
        "code": expected_code,
        "campaign_id": None,
        "message": expected_reason,
    }]


@pytest.mark.parametrize(
    ("field", "damage"),
    [
        pytest.param("env_tag", "missing", id="env-tag-missing"),
        pytest.param("env_tag", "", id="env-tag-empty"),
        pytest.param("env_tag", 1, id="env-tag-non-string"),
        pytest.param("contract_sha256", "missing", id="contract-sha256-missing"),
        pytest.param("contract_sha256", "", id="contract-sha256-empty"),
        pytest.param("contract_sha256", 1, id="contract-sha256-non-string"),
    ],
)
def test_run_contract_identity_declaration_is_fail_closed_before_resolution(
        tmp_path, monkeypatch, field, damage):
    manifest = _manifest(tmp_path)
    if damage == "missing":
        manifest["run_contract"].pop(field)
    else:
        manifest["run_contract"][field] = damage
    manifest = _schema_less_legacy(manifest)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    resolver = mock.Mock(
        side_effect=AssertionError("不正宣言を resolver へ渡してはいけない"),
    )
    monkeypatch.setattr(
        report.env_contract, "resolve_by_contract_sha256", resolver,
    )

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )
    rows = observations["rows"]

    assert len(rows) == len(manifest["schedule"]["rows"]) > 0
    assert all(row["status"] == "protocol_violation" for row in rows)
    assert {row["reason"] for row in rows} == {
        f"manifest.run_contract.{field} が非空 str でない",
    }
    resolver.assert_not_called()


def test_run_contract_issue_does_not_override_missing_terminal_head_behavior(
        tmp_path):
    manifest = _manifest(tmp_path)
    manifest["run_contract"]["reps"] = 4
    manifest = _schema_less_legacy(manifest)
    _layout(tmp_path, manifest)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert [issue["code"] for issue in observations["manifest_issues"]] == [
        "run-contract-reps-not-approved",
    ]
    assert {row["status"] for row in observations["rows"]} == {
        "campaign-incomplete",
    }
    assert {row["reason"] for row in observations["rows"]} == {
        "campaign-terminal が一意でない: 0",
    }


def test_staged_legacy_manifest_still_requires_five_bench_values(tmp_path):
    document = dict(_manifest(tmp_path))
    document.pop("run_contract")
    legacy = artifacts.load_official_manifest(json.dumps(document).encode())
    item = legacy["schedule"]["rows"][0]
    layout = _layout(tmp_path, legacy)
    _trial(layout, item, "committed", tps=(1.0, 2.0, 3.0, 4.0))
    _finish_campaign(layout, legacy)

    row = report.build_observations(manifest=legacy, output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []
    assert "actual=4, expected=5" in row["reason"]


def test_report_rejects_valid_raw_and_exploration_manifest_types(tmp_path):
    official = _manifest(tmp_path)
    class VerifiedManifestSubclass(oracle_manifest.VerifiedManifest):
        pass

    for untyped in (
        dict(official),
        official,
        artifacts.ExplorationArtifact(official),
        object.__new__(VerifiedManifestSubclass),
    ):
        with pytest.raises(artifacts.OracleArtifactTypeError, match="exact type"):
            report.build_observations(manifest=untyped, output_root=tmp_path)


def test_staged_legacy_v1_without_run_contract_remains_accepted(tmp_path):
    _mark_official(tmp_path)
    document = dict(_manifest(tmp_path))
    document.pop("run_contract")
    legacy = artifacts.load_official_manifest(json.dumps(document).encode())

    observations = report.build_observations(manifest=legacy, output_root=tmp_path)

    assert type(legacy) is artifacts.LegacyManifest
    assert type(observations) is artifacts.OfficialObservations
    assert observations["manifest_kind"] == "legacy"


def test_completed_legacy_without_run_contract_or_receipt_skips_contract_checks(
        tmp_path, monkeypatch):
    _mark_official(tmp_path)
    document = dict(_manifest(tmp_path))
    document.pop("run_contract")
    legacy = artifacts.load_official_manifest(json.dumps(document).encode())
    assert type(legacy) is artifacts.LegacyManifest
    assert "run_contract" not in legacy
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    start_payload = {
        "manifest_sha256": oracle_manifest.manifest_sha256(legacy),
        "block_id": "b0",
        "campaign_id": "oracle-b0",
        "t080_freeze_migration_observation": {
            "state": "never-issued", "validation_head": "0" * 40,
        },
    }
    assert "execution_receipt" not in start_payload
    _session(layout, "campaign-start", start_payload)
    _finish_campaign(layout, legacy)
    resolver = mock.Mock(
        side_effect=AssertionError("legacy manifest を resolver へ渡してはいけない"),
    )
    calibration_loader = mock.Mock(
        side_effect=AssertionError("legacy manifest で calibration を読んではいけない"),
    )
    monkeypatch.setattr(
        report.env_contract, "resolve_by_contract_sha256", resolver,
    )
    monkeypatch.setattr(
        report.env_attestation, "load_verified_calibration", calibration_loader,
    )

    observations = report.build_observations(
        manifest=legacy, output_root=tmp_path,
    )
    rows = observations["rows"]

    assert len(rows) == len(legacy["schedule"]["rows"]) > 0
    assert all(row["status"] == "completed" for row in rows)
    resolver.assert_not_called()
    calibration_loader.assert_not_called()


def test_session_identity_wrong_issuer_rejects_completed_campaign_only_for_issuer(
        tmp_path):
    manifest = _manifest(tmp_path, n=2)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    _rewrite_session_identity(
        layout, event="campaign-start", variant="tampered-session",
    )

    rows = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"]

    assert {row["status"] for row in rows} == {"protocol_violation"}
    assert all(row["bench_values"] == [] for row in rows)
    assert all(row["reason"].startswith(_ISSUER_IDENTITY_ISSUE) for row in rows)
    assert all("'tampered-session'" in row["reason"] for row in rows)
    assert all("; " not in row["reason"] for row in rows)


def test_session_identity_checks_non_boundary_trial_record(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    _rewrite_session_identity(
        layout, event="trial-result", variant="tampered-session",
    )

    rows = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"]

    assert {row["status"] for row in rows} == {"protocol_violation"}
    assert all(row["bench_values"] == [] for row in rows)
    assert all(row["reason"].startswith(_ISSUER_IDENTITY_ISSUE) for row in rows)
    assert all("'tampered-session'" in row["reason"] for row in rows)
    assert all("; " not in row["reason"] for row in rows)


def test_session_identity_wrong_v2_env_rejects_only_manifest_mismatch(tmp_path):
    manifest = _manifest(tmp_path, n=2)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    _rewrite_session_identity(layout, env_tag="tampered-env")

    records = wal.read_records(layout)
    campaign_start = next(
        record for record in records
        if record.stage == SESSION
        and record.payload.get("event") == "campaign-start"
    )
    assert campaign_start.payload["execution_receipt"]["env_tag"] == "linux-baremetal"

    rows = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"]

    assert {row["status"] for row in rows} == {"protocol_violation"}
    assert all(row["bench_values"] == [] for row in rows)
    assert all(row["reason"].startswith(_MANIFEST_ENV_ISSUE) for row in rows)
    assert all("'tampered-env'" in row["reason"] for row in rows)
    assert all("; " not in row["reason"] for row in rows)


def test_session_identity_mixed_legacy_env_rejects_only_inconsistency(tmp_path):
    document = dict(_manifest(tmp_path, n=2))
    document.pop("run_contract")
    legacy = artifacts.load_official_manifest(json.dumps(document).encode())
    layout = _layout(tmp_path, legacy)
    _finish_campaign(layout, legacy)
    _rewrite_session_identity(
        layout, event="campaign-terminal", env_tag="tampered-env",
    )

    rows = report.build_observations(
        manifest=legacy, output_root=tmp_path,
    )["rows"]

    assert {row["status"] for row in rows} == {"protocol_violation"}
    assert all(row["bench_values"] == [] for row in rows)
    assert all(row["reason"].startswith(_ENV_CONSISTENCY_ISSUE) for row in rows)
    assert all("'tampered-env'" in row["reason"] for row in rows)
    assert all("; " not in row["reason"] for row in rows)


def test_session_identity_issuer_is_only_protocol_trigger_without_terminal(tmp_path):
    manifest = _manifest(tmp_path, n=2)
    layout = _layout(tmp_path, manifest)

    baseline = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"]
    assert {row["status"] for row in baseline} == {"campaign-incomplete"}

    _rewrite_session_identity(
        layout, event="campaign-start", variant="tampered-session",
    )
    damaged = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"]

    assert {row["status"] for row in damaged} == {"protocol_violation"}
    assert all(row["bench_values"] == [] for row in damaged)
    assert all(row["reason"].startswith(_ISSUER_IDENTITY_ISSUE) for row in damaged)
    assert all("'tampered-session'" in row["reason"] for row in damaged)
    assert all(
        row["reason"].endswith("campaign-terminal が一意でない: 0")
        for row in damaged
    )


def test_session_identity_rejection_taints_t080_report_observation(
        tmp_path, monkeypatch):
    envelope = _t080_envelope()
    _mock_t080_resolution(monkeypatch, "active-valid", envelope)
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=envelope)
    _finish_campaign(layout, manifest)

    baseline = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path, repo_root=tmp_path / "repo",
    )
    assert baseline["t080_freeze_migration_observation"] == envelope

    _rewrite_session_identity(
        layout, event="campaign-start", variant="tampered-session",
    )
    damaged = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path, repo_root=tmp_path / "repo",
    )

    assert damaged["t080_freeze_migration_observation"] is None
    assert {row["status"] for row in damaged["rows"]} == {"protocol_violation"}
    assert all(
        row["reason"].startswith(_ISSUER_IDENTITY_ISSUE)
        for row in damaged["rows"]
    )
    assert all("'tampered-session'" in row["reason"] for row in damaged["rows"])
    assert all("; " not in row["reason"] for row in damaged["rows"])


def test_session_identity_rejection_preserves_malformed_t080_issue(
        tmp_path, monkeypatch):
    envelope = _t080_envelope()
    malformed = copy.deepcopy(envelope)
    malformed["schema_version"] = "unknown/v1"
    _mock_t080_resolution(monkeypatch, "active-valid", envelope)
    manifest = _manifest(tmp_path, n=2)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=malformed)
    _finish_campaign(layout, manifest)
    _rewrite_session_identity(
        layout, event="campaign-start", variant="tampered-session",
    )

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest),
        output_root=tmp_path, repo_root=tmp_path / "repo",
    )

    t080_issue = (
        "t080-freeze-migration-observation: malformed envelope: "
        "schema_version が不正"
    )
    assert observations["t080_freeze_migration_observation"] is None
    assert {row["status"] for row in observations["rows"]} == {
        "protocol_violation",
    }
    assert all(row["bench_values"] == [] for row in observations["rows"])
    assert all(
        _ISSUER_IDENTITY_ISSUE in row["reason"]
        for row in observations["rows"]
    )
    assert all(
        "'tampered-session'" in row["reason"]
        for row in observations["rows"]
    )
    assert all(t080_issue in row["reason"] for row in observations["rows"])
    assert all(row["reason"].count("; ") == 1 for row in observations["rows"])


def test_session_identity_legacy_accepts_consistent_unregistered_env(tmp_path):
    document = dict(_manifest(tmp_path))
    document.pop("run_contract")
    legacy = artifacts.load_official_manifest(json.dumps(document).encode())
    layout = _layout(tmp_path, legacy)
    _finish_campaign(layout, legacy)
    _rewrite_session_identity(layout, env_tag="legacy-fixture-env")

    records = wal.read_records(layout)

    assert {
        record.env_tag for record in records if record.stage == SESSION
    } == {"legacy-fixture-env"}
    assert report._session_identity_issues(records, legacy) == []


def test_report_session_issuer_alias_and_identity_use_model_authority(
        tmp_path, monkeypatch):
    sentinel = "".join(("sentinel", "-session-issuer"))
    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(model, "S8B_ORACLE_SESSION_ISSUER", sentinel)
            importlib.reload(report)
            assert report.SESSION_ISSUER is model.S8B_ORACLE_SESSION_ISSUER

            manifest = _manifest(tmp_path)
            layout = _layout(tmp_path, manifest)
            _finish_campaign(layout, manifest)
            rows = report.build_observations(
                manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
            )["rows"]

            assert {row["status"] for row in rows} == {"protocol_violation"}
            assert all(
                row["reason"].startswith(_ISSUER_IDENTITY_ISSUE) for row in rows
            )
            assert all(repr(sentinel) in row["reason"] for row in rows)
            assert all("; " not in row["reason"] for row in rows)
    finally:
        importlib.reload(report)


def _install_scan_neutral_earlier_eligible_result(
        root: Path, selected_rel: str, monkeypatch,
) -> tuple[str, list[str]]:
    earlier_rel = selected_rel.replace(
        "20260718T120000Z", "20260718T115959Z",
    )
    assert earlier_rel != selected_rel
    earlier_path = root / earlier_rel
    earlier_path.parent.mkdir(parents=True, exist_ok=True)
    earlier_path.write_bytes(b"{}")
    ratified_fixture._commit_exact(
        root,
        [earlier_rel],
        subject="scan-neutral earlier official result",
        agent="fixture",
    )
    eligibility_calls: list[str] = []

    def derive_eligibility(**kwargs):
        eligibility_calls.append(kwargs["result_rel"])
        return kwargs["result_rel"] == earlier_rel

    monkeypatch.setattr(
        holdout_freeze,
        "_derive_floor_selection_eligibility",
        derive_eligibility,
    )
    return earlier_rel, eligibility_calls


def test_cli_official_resolves_ratified_freeze_and_verifies(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_cli_official_resolves_ratified_freeze_and_verifies"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_cli_official_resolves_ratified_freeze_and_verifies(tmp_path):
    root, manifest_path, _document, approved = _ratified_cli_manifest(tmp_path)
    output = tmp_path / "official-cli-observations.json"
    real_selection = (
        report.s8b_ratified_freeze.assert_g1_floor_selection_identity
    )
    real_reverify = report.s8b_ratified_freeze.reverify_published_freeze
    real_verify = oracle_manifest.verify_manifest
    real_build = report.build_observations
    recorded: dict[str, object] = {}
    call_order = mock.Mock()

    def reverify_recording_wrapper(ratified, reverify_root):
        reverified = real_reverify(ratified, reverify_root)
        recorded["reverified"] = reverified
        return reverified

    def verify_recording_wrapper(
            path, *, root, freeze_document, freeze_sha256, approved_spec):
        recorded["freeze_document"] = freeze_document
        recorded["freeze_sha256"] = freeze_sha256
        return real_verify(
            path,
            root=root,
            freeze_document=freeze_document,
            freeze_sha256=freeze_sha256,
            approved_spec=approved_spec,
        )

    def build_recording_wrapper(**kwargs):
        recorded["build_reverified_freeze"] = kwargs.get("reverified_freeze")
        return real_build(**kwargs)

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256,
    ), mock.patch.object(
            report.s8b_ratified_freeze,
            "assert_g1_floor_selection_identity",
            wraps=real_selection,
    ) as selection_spy, mock.patch.object(
            report.s8b_ratified_freeze,
            "reverify_published_freeze",
            side_effect=reverify_recording_wrapper,
    ) as reverify_spy:
        call_order.attach_mock(selection_spy, "selection")
        call_order.attach_mock(reverify_spy, "reverify")
        with mock.patch.object(
                oracle_manifest,
                "verify_manifest",
                side_effect=verify_recording_wrapper,
        ) as verify_spy, mock.patch.object(
                report, "build_observations",
                side_effect=build_recording_wrapper,
        ) as build_spy:
            rc = report.main([
                "report",
                "--manifest", str(manifest_path),
                "--output-root", str(root.parent / "output"),
                "--out", str(output),
                "--repo-root", str(root),
            ])

    assert rc == 0
    assert output.exists()
    assert selection_spy.call_count == 1
    assert reverify_spy.call_count == 1
    assert [entry[0] for entry in call_order.mock_calls] == [
        "selection", "reverify",
    ]
    assert verify_spy.call_count == 1
    assert build_spy.call_count == 1
    reverified = recorded["reverified"]
    assert type(reverified) is report.s8b_ratified_freeze.ReverifiedFreeze
    assert recorded["freeze_document"] is reverified.ratified.document
    assert recorded["freeze_sha256"] == reverified.ratified.sha256
    assert recorded["build_reverified_freeze"] is reverified
    receipt = json.loads(output.read_text(encoding="utf-8"))["store_reverification"]
    assert receipt == {
        "state": "verified",
        "cells": [{
            "cell_id": cell_id,
            "store_path": reverified.binaries_by_cell[cell_id]["store_path"],
            "expected_sha256": reverified.binaries_by_cell[cell_id]["binary_sha256"],
            "actual_sha256": reverified.binaries_by_cell[cell_id]["binary_sha256"],
            "state": "match",
        } for cell_id in sorted(reverified.binaries_by_cell)],
    }


def test_report_cli_real_g1_rule_mismatch_preserves_selection_reason(
        tmp_path, monkeypatch, capsys):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_report_cli_real_g1_rule_mismatch_preserves_selection_reason"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_report_cli_real_g1_rule_mismatch_preserves_selection_reason(tmp_path, monkeypatch):
    import contextlib
    import io
    from types import SimpleNamespace

    captured_stderr = io.StringIO()
    with contextlib.redirect_stderr(captured_stderr):
        root, manifest_path, _document, approved = _ratified_cli_manifest(tmp_path)
        loaded = report.s8b_ratified_freeze.load_ratified_freeze(root)
        selected_rel = loaded.document["floor_source"]["path"]
        assert isinstance(selected_rel, str)
        earlier_rel, eligibility_calls = (
            _install_scan_neutral_earlier_eligible_result(
                root, selected_rel, monkeypatch,
            )
        )
        output = tmp_path / "selection-mismatch-must-not-exist.json"

        with mock.patch.object(
                oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
            rc = report.main([
                "report",
                "--manifest", str(manifest_path),
                "--output-root", str(root.parent / "output"),
                "--out", str(output),
                "--repo-root", str(root),
            ])

        assert rc == 2
        assert "floor-selection-rule-mismatch" in captured_stderr.getvalue()
        assert eligibility_calls == [earlier_rel]
        assert not output.exists()


def test_report_cli_selection_gate_receives_loaded_ratified_and_root(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_report_cli_selection_gate_receives_loaded_ratified_and_root"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_report_cli_selection_gate_receives_loaded_ratified_and_root(tmp_path):
    root, manifest_path, _document, approved = _ratified_cli_manifest(tmp_path)
    loaded_ratified = report.s8b_ratified_freeze.load_ratified_freeze(root)
    selection_calls: list[tuple[object, Path]] = []
    output = tmp_path / "selection-arguments-observations.json"

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256,
    ), mock.patch.object(
            report.s8b_ratified_freeze,
            "load_ratified_freeze",
            return_value=loaded_ratified,
    ), mock.patch.object(
            report.s8b_ratified_freeze,
            "assert_g1_floor_selection_identity",
            side_effect=lambda candidate, candidate_root: selection_calls.append(
                (candidate, candidate_root)
            ),
    ):
        rc = report.main([
            "report",
            "--manifest", str(manifest_path),
            "--output-root", str(root.parent / "output"),
            "--out", str(output),
            "--repo-root", str(root),
        ])

    assert rc == 0
    assert output.exists()
    assert selection_calls == [(loaded_ratified, root)]
    assert selection_calls[0][0] is loaded_ratified
    assert isinstance(selection_calls[0][1], Path)
    assert selection_calls[0][1] == root


def test_report_rejects_unverifiable_floor_admission_without_output(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_report_rejects_unverifiable_floor_admission_without_output"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_report_rejects_unverifiable_floor_admission_without_output(tmp_path):
    root, manifest_path, _document, approved = _ratified_cli_manifest(tmp_path)
    _mark_official(root.parent / "report-output")
    admission_root = root / ".git/izanagi/s8b-holdout-admission-v1"
    admission_root.rename(admission_root.with_name("admission-unavailable"))
    output = tmp_path / "unverifiable-admission-must-not-exist.json"

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        rc = report.main([
            "report", "--manifest", str(manifest_path),
            "--output-root", str(root.parent / "report-output"),
            "--out", str(output), "--repo-root", str(root),
        ])

    assert rc == 2
    assert not output.exists()


def test_cli_verify_failure_returns_two_without_output(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_cli_verify_failure_returns_two_without_output"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_cli_verify_failure_returns_two_without_output(tmp_path):
    root, _manifest_path, document, approved = _ratified_cli_manifest(tmp_path)
    _mark_official(root.parent / "report-output")
    damaged = copy.deepcopy(document)
    damaged["manifest_id"] = "damaged-manifest-id"
    manifest_path = tmp_path / "damaged-ratified-cli-manifest.json"
    manifest_path.write_text(
        json.dumps(damaged, ensure_ascii=False), encoding="utf-8",
    )
    output = tmp_path / "must-not-exist.json"

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        rc = report.main([
            "report",
            "--manifest", str(manifest_path),
            "--output-root", str(root.parent / "report-output"),
            "--out", str(output),
            "--repo-root", str(root),
        ])

    assert rc == 2
    assert not output.exists()


def test_report_cli_accepts_matching_spec_then_rejects_one_other_spec_without_output(
        tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_report_cli_accepts_matching_spec_then_rejects_one_other_spec_without_output"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_report_cli_accepts_matching_spec_then_rejects_one_other_spec_without_output(tmp_path):
    root, manifest_path, _document, approved_a = _ratified_cli_manifest(tmp_path)
    _mark_official(root.parent / "report-output")
    positive_output = tmp_path / "positive-observations.json"
    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved_a.sha256):
        positive_rc = report.main([
            "report", "--manifest", str(manifest_path),
            "--output-root", str(root.parent / "report-output"),
            "--out", str(positive_output), "--repo-root", str(root),
        ])
    assert positive_rc == 0
    positive = json.loads(positive_output.read_text(encoding="utf-8"))
    assert positive["spec_sha256"] == approved_a.sha256

    parameters = approved_a.document["schedule_parameters"]
    approved_b = spec_fixture.make_reviewed_spec(
        root=root,
        n=parameters["n"],
        master_seed="report-cli-other-spec",
        block_sizes=parameters["block_sizes"],
        holdout_ids=parameters["holdout_ids"],
        configuration_ids=parameters["configuration_ids"],
        run_contract=approved_a.document["run_contract"],
        campaign_ids=approved_a.document["campaign_ids"],
        binding_identity=approved_a.document["binding_identity"],
        allowed_excluded_reasons=approved_a.document["allowed_excluded_reasons"],
        generator_versions=approved_a.document["generator_versions"],
    )
    spec_fixture.install_reviewed_spec(root, approved_b)
    negative_output = tmp_path / "must-not-exist-other-spec.json"
    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved_b.sha256):
        negative_rc = report.main([
            "report", "--manifest", str(manifest_path),
            "--output-root", str(root.parent / "report-output"),
            "--out", str(negative_output), "--repo-root", str(root),
        ])
    assert negative_rc == 2
    assert not negative_output.exists()


def test_official_marked_empty_output_root_reports_missing_and_judges_indeterminate(
        tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_official_marked_empty_output_root_reports_missing_and_judges_indeterminate"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_official_marked_empty_output_root_reports_missing_and_judges_indeterminate(tmp_path):
    root, manifest_path, _document, approved = _ratified_cli_manifest(tmp_path)
    output_root = root.parent / "missing-report-output"
    observations_path = tmp_path / "missing-store-observations.json"
    _mark_official(output_root)

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        assert report.main([
            "report", "--manifest", str(manifest_path),
            "--output-root", str(output_root),
            "--out", str(observations_path), "--repo-root", str(root),
        ]) == 0

    observations = json.loads(observations_path.read_text(encoding="utf-8"))
    receipt = observations["store_reverification"]
    assert receipt["state"] == "unverified"
    assert {cell["state"] for cell in receipt["cells"]} == {"missing"}
    assert {cell["actual_sha256"] for cell in receipt["cells"]} == {None}
    verdict = _judge(observations)
    assert verdict["status"] == "indeterminate"
    assert any(
        reason["code"] == "store-reverification-store-missing"
        for reason in verdict["reasons"]
    )


def test_official_missing_marker_cli_fails_without_output(tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_official_missing_marker_cli_fails_without_output"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_official_missing_marker_cli_fails_without_output(tmp_path):
    root, manifest_path, _document, approved = _ratified_cli_manifest(tmp_path)
    output_root = root.parent / "unmarked-report-output"
    output_root.mkdir()
    observations_path = tmp_path / "missing-marker-must-not-exist.json"

    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        rc = report.main([
            "report", "--manifest", str(manifest_path),
            "--output-root", str(output_root),
            "--out", str(observations_path), "--repo-root", str(root),
        ])

    assert rc == 2
    assert not observations_path.exists()


def test_judge_cli_reverifies_official_manifest_and_legacy_cannot_reach_verdict(
        tmp_path):
    from orchestrator.tests.test_s8b_expected_materialization import _run_sealed_case

    case = "_sealed_case_judge_cli_reverifies_official_manifest_and_legacy_cannot_reach_verdict"
    result = _run_sealed_case(
        __name__, case, tmp_path,
    )
    assert result == {"case": case, "completed": True}


def _sealed_case_judge_cli_reverifies_official_manifest_and_legacy_cannot_reach_verdict(tmp_path):
    root, manifest_path, document, approved = _ratified_cli_manifest(tmp_path)
    _mark_official(root.parent / "report-output")
    observations_path = tmp_path / "judge-input-observations.json"
    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        assert report.main([
            "report", "--manifest", str(manifest_path),
            "--output-root", str(root.parent / "report-output"),
            "--out", str(observations_path), "--repo-root", str(root),
        ]) == 0
        verdict_path = tmp_path / "official-verdict.json"
        assert judge.main([
            "judge", "--input", str(observations_path),
            "--manifest", str(manifest_path), "--out", str(verdict_path),
            "--repo-root", str(root),
        ]) == 0
    assert verdict_path.exists()

    legacy_document = copy.deepcopy(document)
    legacy_document.pop("schema_version")
    legacy_path = tmp_path / "legacy-manifest.json"
    legacy_path.write_text(
        json.dumps(legacy_document, ensure_ascii=False), encoding="utf-8",
    )
    forbidden_verdict = tmp_path / "legacy-must-not-exist-verdict.json"
    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        rc = judge.main([
            "judge", "--input", str(observations_path),
            "--manifest", str(legacy_path), "--out", str(forbidden_verdict),
            "--repo-root", str(root),
        ])
    assert rc == 2
    assert not forbidden_verdict.exists()


def test_cli_legacy_skips_freeze_resolution(tmp_path):
    manifest_path = tmp_path / "legacy-cli-manifest.json"
    manifest_path.write_text(
        json.dumps(_schema_less_legacy(_manifest(tmp_path))),
        encoding="utf-8",
    )
    output = tmp_path / "legacy-cli-observations.json"
    _mark_official(tmp_path / "legacy-output")

    with mock.patch.object(
            report.s8b_ratified_freeze,
            "load_ratified_freeze",
            side_effect=AssertionError("legacy must skip ratified resolution"),
    ) as load_spy:
        rc = report.main([
            "report",
            "--manifest", str(manifest_path),
            "--output-root", str(tmp_path / "legacy-output"),
            "--out", str(output),
            "--repo-root", str(tmp_path / "unused-root"),
        ])

    assert rc == 0
    assert output.exists()
    load_spy.assert_not_called()


def test_cli_legacy_subprocess_creates_output(tmp_path):
    repo_root = tmp_path / "subprocess-repo"
    repo_root.mkdir()
    marker = repo_root / "marker.txt"
    marker.write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "marker.txt"], cwd=repo_root, check=True)
    subprocess.run(
        [
            "git",
            "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-q", "-m", "fixture",
        ],
        cwd=repo_root,
        check=True,
    )
    manifest_path = tmp_path / "subprocess-legacy-manifest.json"
    manifest_path.write_text(
        json.dumps(_schema_less_legacy(_manifest(tmp_path))),
        encoding="utf-8",
    )
    output = tmp_path / "subprocess-observations.json"
    _mark_official(tmp_path / "subprocess-output")

    completed = subprocess.run(
        [
            sys.executable,
            "-m", "orchestrator.campaign.s8b_oracle_report",
            "report",
            "--manifest", str(manifest_path),
            "--output-root", str(tmp_path / "subprocess-output"),
            "--out", str(output),
            "--repo-root", str(repo_root),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.exists()


def test_report_cli_rejects_exploration_manifest_without_output(tmp_path):
    exploration_root = tmp_path / "isolated"
    layout = exploration_campaign_layout(
        "trial-a", output_root=str(exploration_root),
    ).ensure()
    manifest_path = Path(layout.reports_dir) / "manifest.exploration.json"
    manifest_path.write_text(json.dumps({
        "schema_version": artifacts.EXPLORATION_ARTIFACT_SCHEMA,
        "artifact_role": "manifest",
        "campaign_id": "trial-a",
        "measurement_hint": {"extime_s": 3, "reps": 3},
        "payload": {},
    }), encoding="utf-8")
    output = tmp_path / "must-not-exist.json"
    _mark_official(tmp_path)

    rc = report.main([
        "report", "--manifest", str(manifest_path),
        "--output-root", str(tmp_path), "--out", str(output),
    ])

    assert rc == 2
    assert not output.exists()


def test_report_requires_root_namespace_marker(tmp_path):
    root = tmp_path / "missing-marker"
    root.mkdir()

    with pytest.raises(report.ReportError, match="namespace marker が存在しない"):
        report._scan_official_namespace(root.resolve())


def test_manifest_helpers_do_not_create_namespace_marker(tmp_path):
    manifest = _manifest(tmp_path)

    _verify_for_report(tmp_path, manifest)
    _two_campaign_manifest(tmp_path)

    assert not (tmp_path / "namespace.json").exists()


@pytest.mark.parametrize(
    "payload",
    [
        artifacts.EXPLORATION_NAMESPACE_BYTES,
        b'{"namespace":"unknown"}\n',
        b'{"namespace":',
        b'{ "namespace": "official" }\n',
        b'{"namespace":"official"}',
    ],
    ids=["exploration", "unknown", "malformed", "whitespace", "missing-lf"],
)
def test_report_requires_official_namespace_exact_bytes(tmp_path, payload):
    root = tmp_path / "non-official-marker"
    root.mkdir()
    (root / "namespace.json").write_bytes(payload)

    with pytest.raises(report.ReportError, match="namespace"):
        report._scan_official_namespace(root.resolve())


@pytest.mark.parametrize(
    "ancestor_payload",
    [
        artifacts.EXPLORATION_NAMESPACE_BYTES,
        b'{"namespace":"unknown"}\n',
        b'{"namespace":',
    ],
    ids=["exploration", "unknown", "malformed"],
)
def test_report_rejects_distant_nonofficial_ancestor_behind_local_official_markers(
        tmp_path, ancestor_payload):
    outer = tmp_path / "outer"
    outer.mkdir()
    (outer / "namespace.json").write_bytes(ancestor_payload)
    middle = outer / "middle"
    _mark_official(middle)
    root = middle / "official-root"
    _mark_official(root)

    with pytest.raises(report.ReportError, match="namespace"):
        report._scan_official_namespace(root.resolve())


def test_report_rejects_unreadable_ancestor_marker(tmp_path):
    outer = tmp_path / "outer"
    marker = _mark_official(outer)
    root = outer / "official-root"
    _mark_official(root)
    real_open = report.os.open

    def deny_ancestor(path, flags):
        if Path(path) == marker:
            raise PermissionError(13, "fixture denies ancestor marker")
        return real_open(path, flags)

    with mock.patch.object(report.os, "open", side_effect=deny_ancestor):
        with pytest.raises(report.ReportError, match="安全に open できない"):
            report._resolve_official_output_root(root)


def test_report_accepts_external_root_with_all_marker_bearing_ancestors_official(
        tmp_path):
    outer = tmp_path / "outer"
    _mark_official(outer)
    root = outer / "official-root"
    _mark_official(root)

    admitted = report._resolve_official_output_root(root)

    assert admitted.path == root.resolve()
    assert [identity.path for identity in admitted.namespace_identities] == [
        root / "namespace.json", outer / "namespace.json",
    ]


def test_report_rejects_input_root_and_marker_symlinks(tmp_path):
    target = tmp_path / "target"
    _mark_official(target)
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(report.ReportError, match="symlink component"):
        report._resolve_official_output_root(alias)

    root = tmp_path / "marker-link"
    root.mkdir()
    marker_target = tmp_path / "official-marker-target"
    marker_target.write_bytes(artifacts.OFFICIAL_NAMESPACE_BYTES)
    (root / "namespace.json").symlink_to(marker_target)
    with pytest.raises(report.ReportError, match="marker が symlink"):
        report._resolve_official_output_root(root)


def test_report_marker_fifo_is_rejected_without_blocking(tmp_path):
    root = tmp_path / "fifo-marker"
    root.mkdir()
    marker = root / "namespace.json"
    os.mkfifo(marker)
    real_open = report.os.open
    real_open_called = False

    def guarded_open(path, flags):
        nonlocal real_open_called
        assert flags & report.os.O_NOFOLLOW
        assert flags & report.os.O_NONBLOCK
        real_open_called = True
        return real_open(path, flags)

    with mock.patch.object(report.os, "open", side_effect=guarded_open):
        with pytest.raises(report.ReportError) as caught:
            report._scan_official_namespace(root.resolve())

    assert real_open_called
    assert str(caught.value) == f"namespace marker が通常 file でない: {marker}"


def test_report_marker_device_descriptor_is_rejected_before_read(tmp_path):
    root = tmp_path / "device-marker"
    _mark_official(root)
    device_descriptor = report.os.open("/dev/null", report.os.O_RDONLY)

    with mock.patch.object(
            report.os, "open", return_value=device_descriptor), mock.patch.object(
            report.os, "read", side_effect=AssertionError("device leaf was read")):
        with pytest.raises(report.ReportError, match="通常 file でない"):
            report._resolve_official_output_root(root)


def test_report_oversized_marker_is_rejected_before_read(tmp_path):
    root = tmp_path / "oversized-marker"
    root.mkdir()
    (root / "namespace.json").write_bytes(b"x" * 4096)

    with mock.patch.object(
            report.os, "read", side_effect=AssertionError("oversized leaf was read")):
        with pytest.raises(report.ReportError, match="有界サイズ"):
            report._resolve_official_output_root(root)


def test_report_canonical_repo_exception_is_exact_and_external_root_still_passes(
        tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    canonical = repository / "output"
    _mark_official(canonical)
    monkeypatch.setattr(report, "repo_output_root", lambda: str(canonical))

    assert report._resolve_official_output_root(canonical).path == canonical.resolve()
    monkeypatch.chdir(repository)
    assert (
        report._resolve_official_output_root(Path("output")).path
        == canonical.resolve()
    )
    with pytest.raises(report.ReportError, match=r"\.\. component"):
        report._resolve_official_output_root(Path("output/../output"))

    sibling = repository / "output-sibling"
    _mark_official(sibling)
    with pytest.raises(
            report.ReportError,
            match="relative.*canonical repository output exact"):
        report._resolve_official_output_root(Path("output-sibling"))
    with pytest.raises(report.ReportError, match="repository 外"):
        report._resolve_official_output_root(sibling)

    foreign = tmp_path / "foreign-repository"
    (foreign / ".git").mkdir(parents=True)
    _mark_official(foreign / "output")
    with pytest.raises(report.ReportError, match="repository 外"):
        report._resolve_official_output_root(foreign / "output")

    worktree_output = tmp_path / ".codex" / "worktrees" / "other" / "output"
    _mark_official(worktree_output)
    external = tmp_path / "external-output"
    _mark_official(external)
    real_has_git_ancestor = campaign_layout_module._has_git_ancestor

    def admit_selected_external_fixture(path, *, label):
        if Path(path) in {worktree_output.resolve(), external.resolve()}:
            return False
        return real_has_git_ancestor(path, label=label)

    with monkeypatch.context() as admission_fixture:
        admission_fixture.setattr(
            campaign_layout_module,
            "_has_git_ancestor",
            admit_selected_external_fixture,
        )
        with pytest.raises(report.ReportError, match="worktree container"):
            report._resolve_official_output_root(worktree_output)
        assert (
            report._resolve_official_output_root(external).path
            == external.resolve()
        )


def test_report_cli_accepts_relative_canonical_output_root(
        tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    canonical = repository / "output"
    _mark_official(canonical)
    manifest_path = tmp_path / "relative-canonical-manifest.json"
    manifest_path.write_text(
        json.dumps(_schema_less_legacy(_manifest(tmp_path))), encoding="utf-8",
    )
    output = tmp_path / "relative-canonical-observations.json"
    monkeypatch.setattr(report, "repo_output_root", lambda: str(canonical))
    monkeypatch.chdir(repository)

    rc = report.main([
        "report", "--manifest", str(manifest_path),
        "--output-root", "output", "--out", str(output),
        "--repo-root", str(tmp_path / "unused-root"),
    ])

    assert rc == 0
    assert output.exists()


def test_report_canonical_tracked_root_uses_read_only_campaign_path_carrier():
    admitted = report._resolve_official_output_root(ROOT / "output")

    layout = report._resolved_campaign_layout(
        "historical-candidate", admitted.path,
    )

    assert Path(layout.root) == ROOT / "output/campaigns/historical-candidate"


def test_report_source_does_not_import_or_call_producer_campaign_layout():
    source = ORCH / "campaign/s8b_oracle_report.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    imported = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
        if alias.name.split(".")[-1] == "campaign_layout"
    ]
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == "campaign_layout"
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "campaign_layout"
        )
    ]

    assert imported == []
    assert calls == []


@pytest.mark.parametrize("swap_target", ["marker", "root"])
def test_report_rejects_root_or_marker_replacement_after_observation_scan(
        tmp_path, swap_target):
    manifest = _manifest(tmp_path)
    root = tmp_path / "volatile-output"
    marker = _mark_official(root)
    verified = _official_report_setup(tmp_path, manifest)
    original_projection = report._campaign_verifier_epoch_projection

    def replace_after_projection(campaign_id, resolved_output_root):
        projected = original_projection(campaign_id, resolved_output_root)
        if swap_target == "marker":
            marker.unlink()
            marker.write_bytes(artifacts.OFFICIAL_NAMESPACE_BYTES)
        else:
            replacement = tmp_path / "replacement-output"
            _mark_official(replacement)
            root.rename(tmp_path / "original-output")
            replacement.rename(root)
        return projected

    with mock.patch.object(
            report, "_campaign_verifier_epoch_projection",
            side_effect=replace_after_projection):
        with pytest.raises(report.ReportError, match="観測中に変化"):
            report.build_observations(manifest=verified, output_root=root)


def test_report_rejects_exploration_namespace_and_root_symlink_alias(tmp_path):
    manifest = _manifest(tmp_path)
    layout = exploration_campaign_layout("trial-a", output_root=str(tmp_path)).ensure()
    exploration_root = Path(layout.root).parents[1]
    alias = tmp_path / "exploration-alias"
    alias.symlink_to(exploration_root, target_is_directory=True)

    verified = _official_report_setup(tmp_path, manifest)
    with pytest.raises(report.ReportError, match="exploration namespace"):
        report.build_observations(manifest=verified, output_root=exploration_root)
    with pytest.raises(report.ReportError, match="symlink component"):
        report.build_observations(manifest=verified, output_root=alias)


def test_report_rejects_campaign_symlink_to_exploration_namespace(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    exploration = exploration_campaign_layout(
        "oracle-b0", output_root=str(tmp_path),
    ).ensure()
    _campaign_start(exploration, manifest)
    _trial(exploration, item, "committed")
    _finish_campaign(exploration, manifest)
    official_root = tmp_path / "official"
    _mark_official(official_root)
    campaigns = official_root / "campaigns"
    campaigns.mkdir()
    (campaigns / "oracle-b0").symlink_to(
        Path(exploration.root), target_is_directory=True,
    )

    with pytest.raises(report.ReportError, match="campaign path component が symlink"):
        report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=official_root)


def test_report_rejects_campaigns_root_symlink_and_invalid_campaign_id(tmp_path):
    root = tmp_path / "official"
    _mark_official(root)
    target = tmp_path / "campaign-target"
    target.mkdir()
    (root / "campaigns").symlink_to(target, target_is_directory=True)

    with pytest.raises(report.ReportError, match="campaign path component が symlink"):
        report._resolved_campaign_layout("oracle-b0", root.resolve())
    with pytest.raises(report.ReportError, match="campaign_id"):
        report._resolved_campaign_layout("../oracle-b0", root.resolve())


def test_report_reuses_resolved_output_root_after_namespace_check(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    trusted_root = tmp_path / "trusted"
    trusted = _layout(trusted_root, manifest)
    _trial(trusted, item, "committed", tps=(1.0, 2.0, 3.0, 4.0, 5.0))
    _finish_campaign(trusted, manifest)
    attacker_root = tmp_path / "attacker"
    attacker = _layout(attacker_root, manifest)
    _trial(attacker, item, "committed", tps=(91.0, 92.0, 93.0, 94.0, 95.0))
    _finish_campaign(attacker, manifest)
    verified = _official_report_setup(tmp_path, manifest)
    admitted = report._resolve_official_output_root(trusted_root)
    epoch_roots: list[Path] = []
    measurement_roots: list[Path] = []
    real_measurement_condition = report._measurement_condition_for_campaign
    real_lock_reader = report._read_campaign_lock_bytes

    def recording_lock_reader(layout):
        epoch_roots.append(Path(layout.root))
        return real_lock_reader(layout)

    def recording_measurement_condition(
            campaign_id, manifest_sha256, expected_block_ids, output_root):
        measurement_roots.append(Path(output_root))
        return real_measurement_condition(
            campaign_id, manifest_sha256, expected_block_ids, output_root,
        )

    with mock.patch.object(
        report, "_resolve_official_output_root", return_value=admitted,
    ), mock.patch.object(
        report, "_read_campaign_lock_bytes",
        side_effect=recording_lock_reader,
    ), mock.patch.object(
        report, "_measurement_condition_for_campaign",
        side_effect=recording_measurement_condition,
    ):
        observations = report.build_observations(
            manifest=verified, output_root=attacker_root,
        )

    assert observations["rows"][0]["bench_values"] == [1.0, 2.0, 3.0, 4.0, 5.0]
    assert epoch_roots == [
        trusted_root / "campaigns/oracle-b0",
        trusted_root / "campaigns/oracle-b0",
    ]
    assert measurement_roots == [trusted_root.resolve()]


def test_report_cli_rejects_exploration_output_root_without_output(tmp_path):
    manifest = _manifest(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(_schema_less_legacy(manifest)), encoding="utf-8",
    )
    layout = exploration_campaign_layout("trial-a", output_root=str(tmp_path)).ensure()
    output = tmp_path / "must-not-exist.json"

    rc = report.main([
        "report", "--manifest", str(manifest_path),
        "--output-root", str(Path(layout.root).parents[1]),
        "--out", str(output),
    ])

    assert rc == 2
    assert not output.exists()


@pytest.mark.parametrize(
    ("case", "expected_outcome", "legacy", "s2"),
    [
        ("build-failed", "build-failed", "missing", "missing"),
        ("legacy-red", "correctness-red", "red", "missing"),
        ("s2-red", "correctness-red", "pass", "red"),
        ("timeout", "timeout", "pass", "missing"),
        ("verify-inconclusive", "verify-inconclusive", "pass", "missing"),
        ("bench-failed", "bench-failed", "pass", "pass"),
        ("binary-mismatch", "binary-mismatch", "missing", "missing"),
    ],
)
def test_failure_outcomes_remain_as_completed_observation_rows(
        tmp_path, case, expected_outcome, legacy, s2):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, case)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "completed"
    assert row["outcome"] == expected_outcome
    assert row["legacy_verify"] == legacy
    assert row["s2_verify"] == s2


@pytest.mark.parametrize("outcome", ["timeout", "verify-inconclusive"])
@pytest.mark.parametrize("verify_frontier", ["legacy", "s2"])
def test_timeout_and_verify_inconclusive_accept_both_verify_frontiers(
        tmp_path, outcome, verify_frontier):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, outcome, verify_frontier=verify_frontier)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "completed"
    assert row["outcome"] == outcome
    if verify_frontier == "legacy":
        assert (row["legacy_verify"], row["s2_verify"]) == ("missing", "missing")
    else:
        assert (row["legacy_verify"], row["s2_verify"]) == ("pass", "missing")


@pytest.mark.parametrize(
    ("case", "outcome", "pipeline"),
    [
        pytest.param(
            "build-failed-with-verify", "build-failed",
            [
                ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN}),
                ("verify_done", {
                    "verdict": "serializable", "certified": True,
                    "workload": {"tag": "legacy"},
                }),
                ("abort", {"reason": "build-error"}),
            ],
            id="build-failed-with-verify",
        ),
        pytest.param(
            "timeout-with-bench", "timeout",
            [
                ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN}),
                ("build_done", {"trace_bin": "trace", "perf_bin": "perf"}),
                ("verify_done", {
                    "verdict": "serializable", "certified": True,
                    "workload": {"tag": "legacy"},
                }),
                ("bench_done", {
                    "tps": [1.0, 2.0, 3.0, 4.0, 5.0], "median_tps": 3.0,
                    "rep_returncodes": [0, 0, 0, 0, 0],
                }),
                ("abort", {
                    "reason": "trace-timeout", "workload": {"tag": "s2"},
                }),
            ],
            id="timeout-with-bench",
        ),
    ],
)
def test_impossible_declared_outcome_histories_are_protocol_violations(
        tmp_path, case, outcome, pipeline):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, outcome, pipeline)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation", case
    assert "段階証拠が一致しない" in row["reason"]
    assert f"outcome='{outcome}'" in row["reason"]
    assert "StageEvidence(" in row["reason"]


@pytest.mark.parametrize(
    ("outcome", "pipeline"),
    [
        pytest.param(
            "committed",
            [
                ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN}),
                ("build_done", {}),
                ("verify_done", {
                    "verdict": "serializable", "certified": True,
                    "workload": {"tag": "s2"},
                }),
                ("verify_done", {
                    "verdict": "serializable", "certified": True,
                    "workload": {"tag": "legacy"},
                }),
                ("bench_done", {
                    "tps": [1, 2, 3, 4, 5],
                    "rep_returncodes": [0, 0, 0, 0, 0],
                }),
                ("commit", {}),
            ],
            id="reversed-committed",
        ),
        pytest.param(
            "correctness-red",
            [
                ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN}),
                ("build_done", {}),
                ("verify_done", {
                    "verdict": "cycle", "certified": False,
                    "workload": {"tag": "s2"},
                }),
                ("verify_done", {
                    "verdict": "serializable", "certified": True,
                    "workload": {"tag": "legacy"},
                }),
                ("abort", {"reason": "cycle", "workload": {"tag": "s2"}}),
            ],
            id="reversed-s2-red",
        ),
        pytest.param(
            "timeout",
            [
                ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN}),
                ("build_done", {}),
                ("verify_done", {
                    "verdict": "serializable", "certified": True,
                    "workload": {"tag": "s2"},
                }),
                ("verify_done", {
                    "verdict": "serializable", "certified": True,
                    "workload": {"tag": "legacy"},
                }),
                ("abort", {"reason": "trace-timeout", "workload": {"tag": "s2"}}),
            ],
            id="legacy-after-s2-timeout",
        ),
    ],
)
def test_reversed_verify_sequences_are_protocol_violations(tmp_path, outcome, pipeline):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, outcome, pipeline)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "verify_sequence=" in row["reason"]


def test_verify_done_attempt_id_mismatch_is_a_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, "committed", [
        ("build_start", {
            "genome": GENOME,
            "src_token": SRC_TOKEN,
            "build_attempt_id": "attempt-committed",
        }),
        ("build_done", {
            "trace_bin": "trace",
            "perf_bin": "perf",
            "build_attempt_id": "attempt-committed",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "legacy"},
            "build_attempt_id": "attempt-stale",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "s2"},
            "build_attempt_id": "attempt-committed",
        }),
        ("bench_done", {
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0],
            "median_tps": 12.0,
            "rep_returncodes": [0, 0, 0, 0, 0],
            "build_attempt_id": "attempt-committed",
        }),
        ("commit", {
            "fitness_tps": 12.0,
            "verify_configs": ["legacy", "s2"],
            "build_attempt_id": "attempt-committed",
        }),
    ])
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["legacy_verify"] == "missing"
    assert row["s2_verify"] == "pass"
    assert row["status"] == "protocol_violation"
    assert "build_attempt_id" in row["reason"]


def test_build_done_attempt_id_mismatch_is_a_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, "committed", [
        ("build_start", {
            "genome": GENOME,
            "src_token": SRC_TOKEN,
            "build_attempt_id": "attempt-committed",
        }),
        ("build_done", {
            "trace_bin": "trace",
            "perf_bin": "perf",
            "build_attempt_id": "attempt-stale",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "legacy"},
            "build_attempt_id": "attempt-committed",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "s2"},
            "build_attempt_id": "attempt-committed",
        }),
        ("bench_done", {
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0],
            "median_tps": 12.0,
            "rep_returncodes": [0, 0, 0, 0, 0],
            "build_attempt_id": "attempt-committed",
        }),
        ("commit", {
            "fitness_tps": 12.0,
            "verify_configs": ["legacy", "s2"],
            "build_attempt_id": "attempt-committed",
        }),
    ])
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "build_done.build_attempt_id" in row["reason"]
    assert "; " not in row["reason"]


def test_bench_done_attempt_id_mismatch_is_a_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, "committed", [
        ("build_start", {
            "genome": GENOME,
            "src_token": SRC_TOKEN,
            "build_attempt_id": "attempt-committed",
        }),
        ("build_done", {
            "trace_bin": "trace",
            "perf_bin": "perf",
            "build_attempt_id": "attempt-committed",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "legacy"},
            "build_attempt_id": "attempt-committed",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "s2"},
            "build_attempt_id": "attempt-committed",
        }),
        ("bench_done", {
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0],
            "median_tps": 12.0,
            "rep_returncodes": [0, 0, 0, 0, 0],
            "build_attempt_id": "attempt-stale",
        }),
        ("commit", {
            "fitness_tps": 12.0,
            "verify_configs": ["legacy", "s2"],
            "build_attempt_id": "attempt-committed",
        }),
    ])
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "bench_done.build_attempt_id" in row["reason"]
    assert "; " not in row["reason"]


def test_commit_attempt_id_mismatch_is_a_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, "committed", [
        ("build_start", {
            "genome": GENOME,
            "src_token": SRC_TOKEN,
            "build_attempt_id": "attempt-committed",
        }),
        ("build_done", {
            "trace_bin": "trace",
            "perf_bin": "perf",
            "build_attempt_id": "attempt-committed",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "legacy"},
            "build_attempt_id": "attempt-committed",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "s2"},
            "build_attempt_id": "attempt-committed",
        }),
        ("bench_done", {
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0],
            "median_tps": 12.0,
            "rep_returncodes": [0, 0, 0, 0, 0],
            "build_attempt_id": "attempt-committed",
        }),
        ("commit", {
            "fitness_tps": 12.0,
            "verify_configs": ["legacy", "s2"],
            "build_attempt_id": "attempt-stale",
        }),
    ])
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "commit.build_attempt_id" in row["reason"]
    assert "; " not in row["reason"]


def test_abort_attempt_id_mismatch_is_a_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, "correctness-red", [
        ("build_start", {
            "genome": GENOME,
            "src_token": SRC_TOKEN,
            "build_attempt_id": "attempt-committed",
        }),
        ("build_done", {
            "trace_bin": "trace",
            "perf_bin": "perf",
            "build_attempt_id": "attempt-committed",
        }),
        ("verify_done", {
            "verdict": "cycle",
            "certified": False,
            "workload": {"tag": "legacy"},
            "build_attempt_id": "attempt-committed",
        }),
        ("abort", {
            "reason": "cycle",
            "workload": {"tag": "legacy"},
            "build_attempt_id": "attempt-stale",
        }),
    ])
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["legacy_verify"] == "red"
    assert row["outcome"] == "correctness-red"
    assert row["status"] == "protocol_violation"
    assert "abort.build_attempt_id" in row["reason"]
    assert "; " not in row["reason"]


def test_stray_attempt_id_without_committed_binding_is_not_flagged(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _manual_trial(layout, item, "committed", [
        ("build_start", {
            "genome": GENOME,
            "src_token": SRC_TOKEN,
        }),
        ("build_done", {
            "trace_bin": "trace",
            "perf_bin": "perf",
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "legacy"},
        }),
        ("verify_done", {
            "verdict": "serializable",
            "certified": True,
            "workload": {"tag": "s2"},
        }),
        ("bench_done", {
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0],
            "median_tps": 12.0,
            "rep_returncodes": [0, 0, 0, 0, 0],
            "build_attempt_id": "stray-id",
        }),
        ("commit", {
            "fitness_tps": 12.0,
            "verify_configs": ["legacy", "s2"],
        }),
    ])
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )["rows"][0]

    assert row["status"] != "protocol_violation"


def test_pipeline_physical_order_remains_an_independent_guard(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    pipeline = _valid_committed_pipeline()
    pipeline[0], pipeline[1] = pipeline[1], pipeline[0]
    _manual_trial(layout, item, "committed", pipeline)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "pipeline event の物理順序が不正" in row["reason"]
    assert "段階証拠が一致しない" not in row["reason"]


@pytest.mark.parametrize("abort_workload", [{"tag": "legacy"}, None])
def test_abort_workload_tag_must_match_verify_frontier(
        tmp_path, abort_workload):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    abort_payload = {"reason": "trace-timeout"}
    if abort_workload is not None:
        abort_payload["workload"] = abort_workload
    _manual_trial(layout, item, "timeout", [
        ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN}),
        ("build_done", {}),
        ("verify_done", {
            "verdict": "serializable", "certified": True,
            "workload": {"tag": "legacy"},
        }),
        ("abort", abort_payload),
    ])
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "段階証拠が一致しない" in row["reason"]


@pytest.mark.parametrize(
    "workload",
    [
        pytest.param(["s2"], id="list"),
        pytest.param({"tag": None}, id="none-tag"),
        pytest.param({"tag": "s2", "extra": True}, id="extra-key"),
    ],
)
def test_invalid_nested_abort_workload_is_an_independent_issue(tmp_path, workload):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "timeout", abort_payload={
        "reason": "trace-timeout", "workload": workload,
    })
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "abort.workload は exact {tag: legacy|s2} object" in row["reason"]


def test_correctness_red_abort_reason_must_equal_sole_red_verdict(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "s2-red", abort_payload={"reason": "different"})
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "sole red verify verdict/abort reason 連鎖" in row["reason"]


def test_report_reads_outcome_stage_contract_leaf(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    matcher = mock.Mock(return_value=False)

    with mock.patch.object(report._outcome_stage_contract, "matches", matcher):
        observations = report.build_observations(
            manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
        )

    assert matcher.call_count == len(manifest["schedule"]["rows"])
    assert all(
        type(call.args[1]) is outcome_stage_contract.StageEvidence
        for call in matcher.call_args_list
    )
    assert all(row["status"] == "protocol_violation" for row in observations["rows"])


def test_bench_failed_abort_reason_contract_is_closed_literal_set():
    assert abort_reason_contract.BENCH_FAILED_ABORT_REASONS == frozenset({
        "bench-competing-tenant",
        "bench-no-throughput",
        "bench-cv-undefined",
    })


def test_other_abort_reason_contracts_are_closed_literal_sets():
    assert abort_reason_contract.TIMEOUT_ABORT_REASONS == frozenset({
        "trace-timeout",
    })
    assert abort_reason_contract.BUILD_FAILED_ABORT_REASONS == frozenset({
        "build-error",
        "identity-error",
    })
    assert abort_reason_contract.VERIFY_INCONCLUSIVE_ABORT_REASONS == frozenset({
        "trace-run-nonzero-exit",
        "trace-empty",
        "trace-no-abort-counts",
        "trace-no-commit-witness",
        "trace-batch-commits-unattributed",
        "trace-witness-unsupported-workload",
        "trace-parse-error",
        "verify-competing-tenant",
    })


@pytest.mark.parametrize(
    ("outcome", "abort_payload", "expected_reason"),
    [
        pytest.param(
            "timeout", {"reason": "bench-no-throughput"},
            "timeout 宣言と abort reason 証拠が一致しない",
            id="timeout-outside-closed-set",
        ),
        pytest.param(
            "timeout", {},
            "timeout 宣言と abort reason 証拠が一致しない",
            id="timeout-missing-reason",
        ),
        pytest.param(
            "timeout", {"reason": None},
            "timeout 宣言と abort reason 証拠が一致しない",
            id="timeout-none-reason",
        ),
        pytest.param(
            "timeout", {"reason": ["trace-timeout"]},
            "timeout 宣言と abort reason 証拠が一致しない",
            id="timeout-reason-list",
        ),
        pytest.param(
            "build-failed", {"reason": "trace-timeout"},
            "build-failed 宣言と abort reason 証拠が一致しない",
            id="build-failed-outside-closed-set",
        ),
        pytest.param(
            "build-failed", ["not-a-mapping"],
            "build-failed 宣言と abort reason 証拠が一致しない",
            id="build-failed-payload-list",
        ),
        pytest.param(
            "verify-inconclusive", {"reason": ["trace-empty"]},
            "verify-inconclusive 宣言と missing verify/abort 証拠が一致しない",
            id="verify-inconclusive-reason-list",
        ),
    ],
)
def test_terminal_outcomes_reject_invalid_abort_reason_without_crashing(
        tmp_path, outcome, abort_payload, expected_reason):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, outcome, abort_payload=abort_payload)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert expected_reason in row["reason"]


@pytest.mark.parametrize(
    ("outcome", "reason"),
    [
        pytest.param("timeout", "trace-timeout", id="timeout-trace-timeout"),
        pytest.param("build-failed", "build-error", id="build-failed-build-error"),
        pytest.param("build-failed", "identity-error", id="build-failed-identity-error"),
        pytest.param(
            "verify-inconclusive", "trace-run-nonzero-exit",
            id="verify-inconclusive-trace-run-nonzero-exit",
        ),
        pytest.param(
            "verify-inconclusive", "trace-empty",
            id="verify-inconclusive-trace-empty",
        ),
        pytest.param(
            "verify-inconclusive", "trace-no-abort-counts",
            id="verify-inconclusive-trace-no-abort-counts",
        ),
        pytest.param(
            "verify-inconclusive", "trace-no-commit-witness",
            id="verify-inconclusive-trace-no-commit-witness",
        ),
        pytest.param(
            "verify-inconclusive", "trace-batch-commits-unattributed",
            id="verify-inconclusive-trace-batch-commits-unattributed",
        ),
        pytest.param(
            "verify-inconclusive", "trace-witness-unsupported-workload",
            id="verify-inconclusive-trace-witness-unsupported-workload",
        ),
        pytest.param(
            "verify-inconclusive", "trace-parse-error",
            id="verify-inconclusive-trace-parse-error",
        ),
        pytest.param(
            "verify-inconclusive", "verify-competing-tenant",
            id="verify-inconclusive-verify-competing-tenant",
        ),
    ],
)
def test_terminal_outcomes_accept_closed_abort_reason(tmp_path, outcome, reason):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, outcome, abort_payload={"reason": reason})
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "completed"
    assert row["reason"] is None


@pytest.mark.parametrize(
    "abort_payload",
    [
        pytest.param({"reason": "trace-timeout"}, id="outside-closed-set"),
        pytest.param({}, id="missing-reason"),
        pytest.param({"reason": None}, id="none-reason"),
        pytest.param({"reason": ""}, id="empty-reason"),
        pytest.param(["not-a-mapping"], id="payload-list"),
        pytest.param({"reason": ["bench-no-throughput"]}, id="reason-list"),
    ],
)
def test_bench_failed_rejects_invalid_abort_reason_without_crashing(
        tmp_path, abort_payload):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "bench-failed", abort_payload=abort_payload)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "bench-failed 宣言と abort reason 証拠が一致しない" in row["reason"]


@pytest.mark.parametrize(
    "reason",
    [
        "bench-competing-tenant",
        "bench-no-throughput",
        "bench-cv-undefined",
    ],
)
def test_bench_failed_accepts_closed_abort_reason(tmp_path, reason):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "bench-failed", abort_payload={"reason": reason})
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "completed"
    assert row["reason"] is None


def test_bench_failed_duplicate_abort_remains_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "bench-failed")
    wal.log(layout, VARIANT, "abort", "fixture-env", {
        "reason": "bench-no-throughput",
    })
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "terminal pipeline event が重複" in row["reason"]


def test_verify_inconclusive_wal_stays_observable_and_judges_indeterminate(tmp_path):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    inconclusive_item = schedule[0]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        _trial(
            layout, item,
            "verify-inconclusive" if item is inconclusive_item else "committed",
        )
    _finish_campaign(layout, manifest, fill_missing=False)

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )
    row = observations["rows"][0]
    verdict = _judge(observations)

    assert row["status"] == "completed"
    assert row["outcome"] == "verify-inconclusive"
    assert row["legacy_verify"] == "pass"
    assert row["s2_verify"] == "missing"
    assert verdict["status"] == "indeterminate"
    cell = verdict["holdouts"][row["holdout_id"]]["configurations"][
        row["configuration_id"]
    ]
    assert cell["status"] == "unknown"


def test_binary_mismatch_wal_stays_observable_and_judges_indeterminate(tmp_path):
    """C3-5: binary-mismatch trial が report で observable outcome になり、judge の
    eligibility へ unknown 伝播する (cell=unknown / overall=indeterminate)。"""
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    mismatch_item = schedule[0]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        _trial(
            layout, item,
            "binary-mismatch" if item is mismatch_item else "committed",
        )
    _finish_campaign(layout, manifest, fill_missing=False)

    observations = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)
    row = observations["rows"][0]
    verdict = _judge(observations)

    assert row["status"] == "completed"
    assert row["outcome"] == "binary-mismatch"
    assert row["legacy_verify"] == "missing" and row["s2_verify"] == "missing"
    assert verdict["status"] == "indeterminate"
    cell = verdict["holdouts"][row["holdout_id"]]["configurations"][
        row["configuration_id"]
    ]
    assert cell["status"] == "unknown"


def test_receipt_mismatch_is_protocol_violation(tmp_path):
    """manifest run_contract (v2) が宣言する env_tag/contract_sha256 と campaign-start の
    execution_receipt が食い違えば全行 protocol_violation (report が receipt を照合する)。"""
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    # contract_sha256 が manifest と不一致な receipt を載せる。
    _campaign_start(layout, manifest, "oracle-b0", receipt={
        "schema": execution_guard.RECEIPT_SCHEMA,
        "env_tag": "fixture-env",
        "contract_sha256": "1" * 64,
        "attestation": {
            "hostname": "h", "boot_id": None, "cpuset": None,
            "captured_utc": "2026-07-18T00:00:00+00:00",
        },
    })
    for item in schedule:
        _trial(layout, item, "committed")
    _finish_campaign(layout, manifest, fill_missing=False)

    observations = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)
    assert all(row["status"] == "protocol_violation" for row in observations["rows"])
    assert any("execution_receipt" in (row.get("reason") or "")
               for row in observations["rows"])


def test_build_observations_accepts_recorded_g1_under_g2_current(tmp_path):
    """public report 経路が production historical resolver を明示配線する正例。"""
    manifest = _schema_less_legacy(_manifest(tmp_path))
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    g1 = env_contract.lookup("linux-baremetal")
    g2 = dataclasses.replace(
        g1,
        calibration_ref=env_contract.CalibrationRef(
            path=g1.calibration_ref.path + ".successor",
            sha256="f" * 64,
        ),
    )
    assert env_contract.is_valid_successor(g1, g2)
    resolver = mock.Mock(wraps=env_contract.resolve_by_contract_sha256)
    calibration_loader = mock.Mock(
        wraps=report.env_attestation.load_verified_calibration,
    )

    with mock.patch.object(report.env_contract, "lookup", return_value=g2), \
            mock.patch.object(
                report.env_contract, "resolve_by_contract_sha256", resolver,
            ), mock.patch.object(
                report.env_attestation, "load_verified_calibration",
                calibration_loader,
            ):
        observations = report.build_observations(
            manifest=manifest, output_root=tmp_path,
        )

    rows = observations["rows"]
    expected_count = len(manifest["schedule"]["rows"])
    assert len(rows) == len(observations["expected_cells"]) == expected_count > 0
    assert all(row["status"] == "completed" for row in rows)
    assert resolver.call_count == 1
    assert resolver.call_args.args == (g1.contract_sha256,)
    assert resolver.call_args.kwargs == {"expected_env_tag": g1.env_tag}
    assert calibration_loader.call_count == 1
    assert calibration_loader.call_args.args[0] is g1


def test_build_observations_resolves_contract_once_across_two_campaigns(tmp_path):
    """manifest 単位の contract/calibration snapshot を2 campaign で共有する。"""
    manifest = _two_campaign_report_setup(tmp_path)
    rows = manifest["schedule"]["rows"]
    for campaign_id, block_id, item in (
        ("oracle-b0", "b0", rows[0]),
        ("oracle-b1", "b1", rows[1]),
    ):
        layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
        _campaign_start(layout, manifest, campaign_id, block_id=block_id)
        _finish_campaign_rows(layout, [item])
    resolver = mock.Mock(wraps=env_contract.resolve_by_contract_sha256)
    calibration_loader = mock.Mock(
        wraps=report.env_attestation.load_verified_calibration,
    )

    with mock.patch.object(
            report.env_contract, "resolve_by_contract_sha256", resolver,
    ), mock.patch.object(
            report.env_attestation, "load_verified_calibration", calibration_loader,
    ):
        observations = report.build_observations(
            manifest=manifest, output_root=tmp_path,
        )

    observed_rows = observations["rows"]
    assert len(observed_rows) == len(observations["expected_cells"]) == 2
    assert [row["status"] for row in observed_rows] == ["completed", "completed"]
    assert resolver.call_count == 1
    assert calibration_loader.call_count == 1


@pytest.mark.parametrize(
    "case_id,reason_fragment",
    [
        ("malformed", "64 桁"),
        ("unknown", "未知"),
        ("ambiguous", "一意"),
        ("cross-env", "expected_env_tag"),
        ("dishonest-resolver", "返却 entry"),
        ("missing-calibration", "manifest env contract を検証できない"),
        ("calibration-hash-mismatch", "manifest env contract を検証できない"),
    ],
    ids=[
        "malformed", "unknown", "ambiguous", "cross-env",
        "dishonest-resolver", "missing-calibration", "calibration-hash-mismatch",
    ],
)
def test_build_observations_historical_resolver_fails_closed_without_current_fallback(
        tmp_path, case_id, reason_fragment):
    """public report の resolver/calibration 拒否 matrix は current へ fallback しない。

    ambiguous / dishonest は patch-only の構造防御であり production artifact から
    到達しない。
    """
    manifest = _manifest(tmp_path)
    base = env_contract.lookup("linux-baremetal")
    production_resolver = env_contract.resolve_by_contract_sha256

    if case_id == "malformed":
        manifest["run_contract"]["contract_sha256"] = "not-a-sha256"
        resolver = production_resolver
    elif case_id == "unknown":
        manifest["run_contract"]["contract_sha256"] = "f" * 64
        resolver = production_resolver
    elif case_id == "ambiguous":
        duplicate = env_contract.GenerationEntry(generation=1, contract=base)
        duplicate_index = MappingProxyType({
            base.contract_sha256: (duplicate, duplicate),
        })
        def resolver(recorded, *, expected_env_tag=None):
            with mock.patch.object(
                    env_contract, "_CONTRACT_SHA256_INDEX", duplicate_index):
                return production_resolver(
                    recorded, expected_env_tag=expected_env_tag,
                )
    elif case_id == "cross-env":
        foreign = env_contract.lookup("pegasus")
        manifest["run_contract"]["contract_sha256"] = foreign.contract_sha256
        resolver = production_resolver
    elif case_id == "dishonest-resolver":
        manifest["run_contract"]["contract_sha256"] = "e" * 64
        def resolver(_recorded, *, expected_env_tag=None):
            return env_contract.GenerationEntry(generation=1, contract=base)
    elif case_id == "missing-calibration":
        contract = dataclasses.replace(
            base,
            calibration_ref=env_contract.CalibrationRef(
                path="orchestrator/tests/nonexistent-historical-calibration.json",
                sha256="d" * 64,
            ),
        )
        manifest["run_contract"]["contract_sha256"] = contract.contract_sha256
        def resolver(_recorded, *, expected_env_tag=None):
            return env_contract.GenerationEntry(generation=1, contract=contract)
    else:
        contract = dataclasses.replace(
            base,
            calibration_ref=env_contract.CalibrationRef(
                path=base.calibration_ref.path,
                sha256="0" * 64,
            ),
        )
        manifest["run_contract"]["contract_sha256"] = contract.contract_sha256
        def resolver(_recorded, *, expected_env_tag=None):
            return env_contract.GenerationEntry(generation=1, contract=contract)

    manifest = _schema_less_legacy(manifest)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    resolver_spy = mock.Mock(side_effect=resolver)
    current_fallback = mock.Mock(
        side_effect=AssertionError("historical report が current lookup へ fallback した"),
    )

    with mock.patch.object(report.env_contract, "lookup", current_fallback), \
            mock.patch.object(
                report.env_contract, "resolve_by_contract_sha256", resolver_spy,
            ):
        observations = report.build_observations(
            manifest=manifest, output_root=tmp_path,
        )

    rows = observations["rows"]
    expected_count = len(manifest["schedule"]["rows"])
    assert len(rows) == len(observations["expected_cells"]) == expected_count > 0
    assert all(row["status"] == "protocol_violation" for row in rows)
    assert all(reason_fragment in (row.get("reason") or "")
               for row in rows)
    assert resolver_spy.call_count == 1
    assert resolver_spy.call_args.kwargs == {"expected_env_tag": base.env_tag}
    current_fallback.assert_not_called()


def test_manifest_contract_sha256_mismatch_with_registry_is_protocol_violation(
        tmp_path):
    """R8: env_tag は実在するが manifest contract hash だけが registry と違う。"""
    manifest = _manifest(tmp_path)
    contract = env_contract.lookup("linux-baremetal")
    manifest["run_contract"]["env_tag"] = contract.env_tag
    manifest["run_contract"]["contract_sha256"] = "f" * 64
    manifest = _schema_less_legacy(manifest)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert all(row["status"] == "protocol_violation"
               for row in observations["rows"])
    assert {
        re.sub(r"[0-9a-f]{64}$", "<sha256>", row["reason"])
        for row in observations["rows"]
    } == {
        "manifest env contract を検証できない: "
        "未知の contract_sha256: <sha256>",
    }


def test_required_receipt_consumer_derives_mode_and_passes_verified_calibration(tmp_path):
    manifest = _manifest(tmp_path)
    _mark_official(tmp_path)
    base = env_contract.lookup("linux-baremetal")
    required = env_contract.ExecutionEnvironmentContract(
        env_tag=base.env_tag, clocks_per_us=base.clocks_per_us,
        numactl=base.numactl, attestation_mode="required",
        isolation_policy=env_contract.IsolationPolicy(
            single_process=True, allow_resume=False,
        ),
        calibration_ref=base.calibration_ref,
    )
    manifest["run_contract"]["contract_sha256"] = required.contract_sha256
    manifest = _schema_less_legacy(manifest)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, receipt=execution_guard.build_receipt(required))
    _finish_campaign(layout, manifest)
    verified = object()
    receipt_spy = mock.Mock(return_value=False)

    entry = env_contract.GenerationEntry(generation=1, contract=required)
    with mock.patch.object(
            report.env_contract, "resolve_by_contract_sha256", return_value=entry), \
            mock.patch.object(report.env_attestation, "load_verified_calibration",
                              return_value=verified), \
            mock.patch.object(report.execution_guard, "receipt_matches_contract",
                              receipt_spy):
        observations = report.build_observations(
            manifest=manifest, output_root=tmp_path,
        )

    assert all(row["status"] == "protocol_violation" for row in observations["rows"])
    assert receipt_spy.call_args.kwargs["attestation_mode"] == "required"
    assert receipt_spy.call_args.kwargs["verified_calibration"] is verified
    assert {row["reason"] for row in observations["rows"]} == {
        "campaign-start.execution_receipt が manifest run_contract の "
        "env_tag/contract_sha256/attestation と不一致 (または欠落)",
    }


@pytest.mark.parametrize("damage", ["missing", "partial"])
def test_missing_or_partial_expected_binding_is_protocol_violation(tmp_path, damage):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    if damage == "missing":
        manifest["binding_identity"] = [
            entry for entry in manifest["binding_identity"]
            if (entry["holdout_id"], entry["configuration_id"])
            != (item["holdout_id"], item["configuration_id"])
        ]
    else:
        entry = next(entry for entry in manifest["binding_identity"]
                     if entry["holdout_id"] == item["holdout_id"]
                     and entry["configuration_id"] == item["configuration_id"])
        entry.pop("src_token")
    manifest = _schema_less_legacy(manifest)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed")
    _finish_campaign(layout, manifest)

    row = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )["rows"][0]

    assert row["binding_ok"] is False
    assert row["status"] == "protocol_violation"
    assert "binding" in row["reason"]
    assert "campaign-start.manifest_sha256" not in row["reason"]


def _assert_single_lifecycle_reason(row: dict, expected: str) -> None:
    assert row["status"] == "protocol_violation"
    assert row["lifecycle_ok"] is False
    assert row["reason"] == expected
    assert row["bench_values"] == []


def test_valid_prepare_retry_uses_attempt_two_and_records_retried_summary(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _retry(layout, item)
    _trial(layout, item, "committed", attempt=2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "completed"
    assert row["lifecycle_ok"] is True
    assert row["attempt"] == 2
    assert [summary["status"] for summary in row["attempt_verify_outcomes"]] == [
        "retried", "completed",
    ]
    assert [summary["attempt"] for summary in row["attempt_verify_outcomes"]] == [1, 2]


def test_retry_absent_double_attempt_has_one_lifecycle_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", attempt=1)
    _trial(layout, item, "committed", attempt=2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(row, "attempt 1 retry record が一意でない: 0")


def test_duplicate_retry_has_one_lifecycle_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _retry(layout, item)
    _retry(layout, item)
    _trial(layout, item, "committed", attempt=2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(row, "attempt 1 retry record が一意でない: 2")


def test_resultful_window_retry_is_unbound_for_one_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _append_pipeline(layout)
    _retry(layout, item)
    _trial_result(layout, item, 1)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "retry が正当な attempt lifecycle に束縛されない",
    )


def test_retry_before_first_start_is_unbound_for_one_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _retry(layout, item)
    _trial(layout, item, "committed")
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "retry が正当な attempt lifecycle に束縛されない",
    )


def test_retry_after_terminal_result_is_row_scoped_tail_for_one_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed")
    _retry(layout, item)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "trial-result 後に row-scoped session event がある",
    )


def test_attempt_gap_has_one_lifecycle_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _retry(layout, item, next_attempt=3)
    _trial(layout, item, "committed", attempt=3)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row,
        "attempt lifecycle の attempt 集合が {1} / {1,2} と厳密一致しない: [1, 3]",
    )


def test_attempt_physical_order_must_match_numeric_order(tmp_path):
    """集合・retry・terminal は正しく、attempt window の物理順だけを壊す。"""
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", attempt=2)
    _trial_start(layout, item, 1)
    _retry(layout, item)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "attempt lifecycle の物理順が 1→2 でない: [2, 1]",
    )


def test_single_attempt_99_is_not_aliased_to_schedule_default(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", attempt=99)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row,
        "attempt lifecycle の attempt 集合が {1} / {1,2} と厳密一致しない: [99]",
    )


def test_retry_attempt_one_rejects_pipeline_record_for_one_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    wal.log(layout, VARIANT, "build_start", "fixture-env", {
        "genome": GENOME, "src_token": SRC_TOKEN,
    })
    _retry(layout, item)
    _trial(layout, item, "committed", attempt=2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "attempt 1 retry window に pipeline record が混在",
    )


def test_attempt_one_two_three_chain_has_one_lifecycle_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _retry(layout, item, next_attempt=2)
    _trial_start(layout, item, 2)
    _retry(layout, item, next_attempt=3)
    _trial(layout, item, "committed", attempt=3)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row,
        "attempt lifecycle の attempt 集合が {1} / {1,2} と厳密一致しない: [1, 2, 3]",
    )


def test_retry_successor_must_be_physically_adjacent(tmp_path):
    manifest = _manifest(tmp_path)
    first, interleaved = manifest["schedule"]["rows"][:2]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, first, 1)
    _retry(layout, first)
    _trial(layout, interleaved, "committed")
    _trial(layout, first, "committed", attempt=2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "attempt 2 が attempt 1 の物理的直後でない",
    )


def test_retry_successor_identity_must_match_predecessor(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _retry(layout, item)
    mixed_configuration = f"{item['configuration_id']}-mixed"
    _trial_start(layout, item, 2, configuration_id=mixed_configuration)
    _append_pipeline(layout)
    _trial_result(layout, item, 2, configuration_id=mixed_configuration)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row,
        "trial-start.configuration_id が schedule と不一致",
    )


def test_retry_payload_schedule_index_must_match_row(tmp_path):
    manifest = _manifest(tmp_path)
    first, other = manifest["schedule"]["rows"][:2]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, first, 1)
    _retry(layout, first, schedule_index=other["schedule_index"])
    _trial(layout, first, "committed", attempt=2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(row, "retry.schedule_index が schedule と不一致")


def test_retry_payload_next_attempt_must_be_exactly_two(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _retry(layout, item, next_attempt=3)
    _trial(layout, item, "committed", attempt=2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "retry.attempt が next attempt=2 と不一致",
    )


def test_orphan_retry_for_schedule_outside_is_global_lifecycle_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    orphan_index = max(row["schedule_index"] for row in manifest["schedule"]["rows"]) + 1
    _retry(layout, item, schedule_index=orphan_index)
    _trial(layout, item, "committed")
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row,
        f"schedule 外の retry が attempt lifecycle に束縛されない: {orphan_index!r}",
    )


def test_trial_result_before_first_start_is_not_silently_ignored(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_result(layout, item, 2)
    _trial(layout, item, "committed", attempt=1)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "trial-result が正当な attempt lifecycle に束縛されない",
    )
    assert row["outcome"] == "committed"
    assert [summary["attempt"] for summary in row["attempt_verify_outcomes"]] == [1]


def test_trial_result_attempt_must_match_owning_start(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _append_pipeline(layout)
    _trial_result(layout, item, 2)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "trial-result.attempt が trial-start と不一致",
    )


def test_duplicate_trial_result_is_not_bijective(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _append_pipeline(layout)
    _trial_result(layout, item, 1)
    _trial_result(layout, item, 1)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(row, "trial-result が一意でない: 2")


def test_trial_result_must_follow_all_pipeline_evidence(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial_start(layout, item, 1)
    _trial_result(layout, item, 1)
    _append_pipeline(layout)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "trial-result が全 pipeline evidence より物理的に後ろでない",
    )


def test_row_scoped_session_event_after_trial_result_is_rejected(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed")
    _session(layout, "trial-skipped", {
        "schedule_index": item["schedule_index"], "reason": "late duplicate",
    })
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    _assert_single_lifecycle_reason(
        row, "trial-result 後に row-scoped session event がある",
    )


def test_global_issue_does_not_mask_definitive_correctness_red(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red")
    _session(layout, "deviation", {"message": "fixture deviation"})
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["lifecycle_ok"] is True
    assert row["outcome"] == "correctness-red"
    assert row["legacy_verify"] == "red"
    assert row["bench_values"] == []
    assert row["reason"].split("; ") == [
        "deviation: 'fixture deviation'",
        "definitive correctness-red を検出: attempt=1",
    ]
    assert [summary["outcome"] for summary in row["attempt_verify_outcomes"]] == [
        "correctness-red",
    ]


def test_foreign_known_stage_is_inert_record_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    wal.log(layout, "foreign-session", model.STAGE_S1_SESSION, "fixture-env", {
        "event": "session-start",
    })
    _trial(layout, item, "committed")
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []
    assert row["reason"].split("; ") == [
        ("WAL record が session event / pipeline stage のどちらにも分類されない: "
         "ordinal=1 stage='s1-session'"),
    ]


def test_global_issue_composes_row_local_assessment_reason(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", rep_returncodes=[0, 0, 9, 0, 0])
    _session(layout, "deviation", {"message": "fixture deviation"})
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["lifecycle_ok"] is True
    assert row["bench_values"] == []
    assert row["reason"].split("; ") == [
        "deviation: 'fixture deviation'",
        "bench_done.rep_returncodes に非ゼロがある",
    ]
    assert [summary["attempt"] for summary in row["attempt_verify_outcomes"]] == [1]


def test_global_orphan_retry_does_not_mask_other_definitive_red(tmp_path):
    """schedule 外 retry と別 row の correctness-red を同じ reason に残す。"""
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    orphan_index = max(row["schedule_index"] for row in manifest["schedule"]["rows"]) + 1
    _retry(layout, item, schedule_index=orphan_index)
    _trial(layout, item, "legacy-red")
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["lifecycle_ok"] is False
    assert row["outcome"] == "correctness-red"
    assert row["legacy_verify"] == "red"
    assert row["bench_values"] == []
    assert row["reason"].split("; ") == [
        f"schedule 外の retry が attempt lifecycle に束縛されない: {orphan_index!r}",
        "definitive correctness-red を検出: attempt=1",
    ]
    assert [summary["outcome"] for summary in row["attempt_verify_outcomes"]] == [
        "correctness-red",
    ]


def test_definitive_red_survives_later_committed_retry_as_protocol_violation(tmp_path):
    """Malformed retry でも lifecycle を白化せず、anti-masking の red も同時に残す。"""
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red", attempt=1)
    _session(layout, "retry", {
        "schedule_index": item["schedule_index"], "attempt": 2,
        "reason": "transient retry",
    })
    _trial(
        layout, item, "committed", attempt=2,
        tps=(1000.0, 1001.0, 1002.0, 1003.0, 1004.0),
    )
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["lifecycle_ok"] is False
    assert row["outcome"] == "correctness-red"
    assert row["legacy_verify"] == "red"
    assert row["bench_values"] == []
    assert row["reason"].split("; ") == [
        "attempt 1 retry window が result-less でない",
        "definitive correctness-red を検出: attempt=1",
    ]
    assert [attempt["outcome"] for attempt in row["attempt_verify_outcomes"]] == [
        "correctness-red", "committed",
    ]


@pytest.mark.parametrize(
    ("rep_returncodes", "expected_reason"),
    [
        pytest.param(
            _MISSING_RETURN_CODES,
            "bench_done.rep_returncodes が array でない",
            id="missing",
        ),
        pytest.param(
            [0, 0, 9, 0, 0],
            "bench_done.rep_returncodes に非ゼロがある",
            id="nonzero",
        ),
        pytest.param(
            [0, 0, 0, 0],
            "bench_done.rep_returncodes 件数が official reps と不一致: actual=4, expected=5",
            id="short",
        ),
        pytest.param(
            [0, 0, True, 0, 0],
            "bench_done.rep_returncodes に非 int または bool がある",
            id="bool",
        ),
    ],
)
def test_bench_returncodes_are_strict_and_do_not_publish_tps(
        tmp_path, rep_returncodes, expected_reason):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", rep_returncodes=rep_returncodes)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["lifecycle_ok"] is True
    assert row["reason"] == expected_reason
    assert row["bench_values"] == []


@pytest.mark.parametrize("phantom_outcome", ["legacy-red", "committed"])
def test_trial_window_with_phantom_schedule_index_is_protocol_violation(
        tmp_path, phantom_outcome):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    phantom = dict(schedule[0], schedule_index=len(schedule) + 100)
    _trial(layout, phantom, phantom_outcome)
    for item in schedule:
        _trial(layout, item, "committed")
    _finish_campaign(layout, manifest, fill_missing=False)

    observations = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)

    assert all(row["status"] == "protocol_violation"
               for row in observations["rows"])
    assert "schedule 外" in observations["rows"][0]["reason"]
    assert _judge(observations)["status"] == "indeterminate"


def test_allowed_excluded_reason_row_stays_reported_and_judges_unknown(tmp_path):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    excluded_item = schedule[0]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        if item is excluded_item:
            _trial(layout, item, "timeout", excluded_reason="machine-fault")
        else:
            _trial(layout, item, "committed")
    _finish_campaign(layout, manifest, fill_missing=False)

    observations = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)
    row = observations["rows"][0]
    verdict = _judge(observations)

    assert row["status"] == "completed"
    assert row["outcome"] == "timeout"
    assert row["excluded_reason"] == "machine-fault"
    assert verdict["status"] == "indeterminate"
    cell = verdict["holdouts"][row["holdout_id"]]["configurations"][
        row["configuration_id"]
    ]
    assert cell["status"] == "unknown"
    assert any(reason["code"] == "excluded" for reason in cell["reasons"])


def test_excluded_reason_outside_allowed_list_is_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "timeout", excluded_reason="power-outage")
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "許可一覧外" in row["reason"]


def test_correctness_red_with_excluded_reason_is_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red", excluded_reason="machine-fault")
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "correctness-red に excluded_reason" in row["reason"]


def test_unverified_official_manifest_is_rejected_immediately_after_tampering(
        tmp_path):
    manifest = _manifest(tmp_path)
    tampered = copy.deepcopy(manifest)
    tampered["allowed_excluded_reasons"].append("tampered")
    tampered["manifest_sha256"] = oracle_manifest.manifest_sha256(manifest)

    with pytest.raises(artifacts.OracleArtifactTypeError, match="exact type"):
        report.build_observations(manifest=tampered, output_root=tmp_path)


def test_legacy_manifest_hash_is_recomputed_independently_after_tampering(tmp_path):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed")
    _finish_campaign(layout, manifest)

    baseline = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )["rows"][0]
    tampered_document = copy.deepcopy(dict(manifest))
    tampered_document["allowed_excluded_reasons"].append("tampered")
    tampered = artifacts.load_official_manifest(
        json.dumps(tampered_document, ensure_ascii=False).encode("utf-8")
    )
    row = report.build_observations(
        manifest=tampered, output_root=tmp_path,
    )["rows"][0]

    assert baseline["status"] == "completed"
    assert row["status"] == "protocol_violation"
    assert row["reason"] == "campaign-start.manifest_sha256 が manifest と不一致"


def test_expected_cells_keep_deleted_holdout_indeterminate(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    for item in manifest["schedule"]["rows"]:
        _trial(layout, item, "committed")
    _finish_campaign(layout, manifest, fill_missing=False)
    observations = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)
    assert _judge(observations)["status"] == "determinate"
    holdouts = {entry["holdout_id"] for entry in observations["expected_cells"]}
    removed = next(iter(holdouts))
    observations["rows"] = [
        row for row in observations["rows"] if row["holdout_id"] != removed
    ]

    assert removed in {entry["holdout_id"] for entry in observations["expected_cells"]}
    assert _judge(observations)["status"] == "indeterminate"


@pytest.mark.parametrize(
    ("stage", "outcome"),
    [
        pytest.param("build_start", "committed", id="build-start"),
        pytest.param("build_done", "committed", id="build-done"),
        pytest.param("verify_done", "committed", id="verify-done"),
        pytest.param("bench_done", "committed", id="bench-done"),
        pytest.param("commit", "committed", id="commit"),
        pytest.param("abort", "build-failed", id="abort"),
    ],
)
def test_non_mapping_pipeline_payload_is_shared_wal_protocol_violation(
        tmp_path, stage, outcome):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    if stage == "abort":
        pipeline = [
            ("build_start", {"genome": GENOME, "src_token": SRC_TOKEN}),
            ("abort", ["not-a-mapping"]),
        ]
    else:
        pipeline = _valid_committed_pipeline()
        index = next(i for i, (candidate, _) in enumerate(pipeline)
                     if candidate == stage)
        pipeline[index] = (stage, ["not-a-mapping"])
    _manual_trial(layout, item, outcome, pipeline)
    _finish_campaign(layout, manifest)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert all("WalLineError: WAL payload must be a JSON object" in row["reason"]
               for row in rows)
    if stage == "bench_done":
        assert all(row["bench_values"] == [] for row in rows)


def test_cli_non_mapping_pipeline_payload_emits_observation(tmp_path):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    pipeline = _valid_committed_pipeline()
    pipeline[4] = ("bench_done", ["not-a-mapping"])
    _manual_trial(layout, item, "committed", pipeline)
    _finish_campaign(layout, manifest)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "observations.json"

    rc = report.main([
        "report", "--manifest", str(manifest_path),
        "--output-root", str(tmp_path), "--out", str(output),
    ])

    assert rc == 0
    observations = json.loads(output.read_text(encoding="utf-8"))
    row = observations["rows"][0]
    assert row["status"] == "protocol_violation"
    assert "WalLineError: WAL payload must be a JSON object" in row["reason"]
    assert "campaign-start.manifest_sha256" not in row["reason"]
    assert row["bench_values"] == []


def test_non_mapping_payload_and_missing_terminal_are_both_reported(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    pipeline = _valid_committed_pipeline()
    pipeline[0] = ("build_start", ["not-a-mapping"])
    _manual_trial(layout, item, "committed", pipeline)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert all("WalLineError: WAL payload must be a JSON object" in row["reason"]
               for row in rows)
    assert all("campaign-terminal が一意でない: 0" in row["reason"] for row in rows)


def test_terminal_missing_makes_every_row_campaign_incomplete(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _session(layout, "budget-refused", {
        "schedule_index": item["schedule_index"], "reason": "budget exhausted",
    })

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "campaign-incomplete" for row in rows)
    assert all(row["bench_values"] == [] for row in rows)
    assert all("campaign-terminal" in row["reason"] for row in rows)


def test_aborted_terminal_status_alone_hides_fully_covered_completed_rows(tmp_path):
    """R5: counts/coverage/deviation が全て正常でも status=aborted 単独で全数を隠す。"""
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        _trial(layout, item, "committed", tps=(100.0, 101.0, 102.0, 103.0, 104.0))
    _finish_campaign(
        layout, manifest, status="aborted", fill_missing=False,
        scheduled_rows=len(schedule), completed_rows=len(schedule),
    )

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]
    assert all(row["status"] == "campaign-incomplete" for row in rows)
    assert all(row["bench_values"] == [] for row in rows)
    assert all("status='aborted'" in row["reason"] for row in rows)


def test_terminal_scheduled_rows_mismatch_alone_hides_all_rows(tmp_path):
    """R2: completed_rows/coverage/status は正常で scheduled_rows だけが違う。"""
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        _trial(layout, item, "committed", tps=(100.0, 101.0, 102.0, 103.0, 104.0))
    _finish_campaign(
        layout, manifest, fill_missing=False,
        scheduled_rows=len(schedule) + 1, completed_rows=len(schedule),
    )

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]
    assert all(row["status"] == "campaign-incomplete" for row in rows)
    assert all(row["bench_values"] == [] for row in rows)
    assert all("scheduled_rows" in row["reason"] for row in rows)


def test_complete_invalid_raw_final_line_is_rejected(tmp_path):
    """完全な JSON だが必須 key がない raw 最終行を crash prefix 扱いしない。"""
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    with open(layout.wal_file, "ab") as stream:
        stream.write(
            b'{"variant":"late","stage":"build_start",'
            b'"env_tag":"fixture-env","ts":1}\n'
        )

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert len({row["reason"] for row in rows}) == 1
    assert all("WalLineError" in row["reason"] for row in rows)
    assert all("keys must be exactly" in row["reason"] for row in rows)


def test_session_non_object_payload_before_terminal_is_unconditional_violation(tmp_path):
    """F1: pipeline guard 対象外の session record でも共有 payload gate が発火する。"""
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    for item in manifest["schedule"]["rows"]:
        _trial(layout, item, "committed")
    with open(layout.wal_file, "ab") as stream:
        stream.write(
            b'{"variant":"oracle-session","stage":"s8b-oracle-session",'
            b'"env_tag":"fixture-env","ts":1,"payload":["bad"]}\n'
        )
    _finish_campaign(layout, manifest, fill_missing=False)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert len({row["reason"] for row in rows}) == 1
    assert all("WalLineError: WAL payload must be a JSON object" in row["reason"]
               for row in rows)


def test_invalid_line_after_terminal_cannot_hide_its_physical_position(tmp_path):
    """F3: 不正行を valid 列から除外しても line issue 自体が必ず赤を立てる。"""
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    with open(layout.wal_file, "ab") as stream:
        stream.write(
            b'{"variant":"late","stage":"build_start","stage":"commit",'
            b'"env_tag":"fixture-env","ts":1,"payload":{}}\n'
        )

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert all("WalDuplicateKeyError" in row["reason"] for row in rows)
    assert all(len(row["reason"].split("; ")) == 1 for row in rows)
    assert all(row["bench_values"] == [] for row in rows)


def test_invalid_line_does_not_mask_definitive_correctness_red(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red")
    with open(layout.wal_file, "ab") as stream:
        stream.write(
            b'{"variant":"oracle-session","stage":"s8b-oracle-session",'
            b'"env_tag":"fixture-env","ts":1,"payload":{"event":"deviation",'
            b'"message":"first","message":"second"}}\n'
        )
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["outcome"] == "correctness-red"
    assert row["legacy_verify"] == "red"
    assert "WalDuplicateKeyError" in row["reason"]
    assert "definitive correctness-red を検出: attempt=1" in row["reason"]
    assert row["bench_values"] == []


def test_terminated_json_syntax_issue_does_not_mask_definitive_correctness_red(
        tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red")
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"variant":}\n')
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["outcome"] == "correctness-red"
    assert row["legacy_verify"] == "red"
    assert "JSONDecodeError" in row["reason"]
    assert "definitive correctness-red を検出: attempt=1" in row["reason"]
    assert "末尾 record が途中" not in row["reason"]
    assert row["bench_values"] == []


def test_truncated_tail_does_not_mask_definitive_correctness_red(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red")
    _finish_campaign(layout, manifest)
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"variant":"late","stage":"build_start"')

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert row["outcome"] == "correctness-red"
    assert row["legacy_verify"] == "red"
    assert "WAL の末尾 record が途中で切れている" in row["reason"]
    assert "definitive correctness-red を検出: attempt=1" in row["reason"]
    assert row["bench_values"] == []


def test_blank_line_between_valid_records_is_unconditional_violation(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    for item in manifest["schedule"]["rows"]:
        _trial(layout, item, "committed")
    with open(layout.wal_file, "a", encoding="utf-8") as stream:
        stream.write("\n")
    _finish_campaign(layout, manifest, fill_missing=False)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert all("WalLineError: WAL line must not be empty" in row["reason"]
               for row in rows)
    assert all(row["bench_values"] == [] for row in rows)


def test_truncated_raw_tail_after_completed_terminal_is_one_protocol_reason(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    with open(layout.wal_file, "ab") as stream:
        stream.write(
            b'{"variant":"oracle-session","stage":"s8b-oracle-session",'
            b'"env_tag":"fixture-env","ts":1,"payload":{"event":"deviation"'
        )

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert {row["reason"] for row in rows} == {
        "WAL の末尾 record が途中で切れている",
    }
    assert all(row["bench_values"] == [] for row in rows)


def test_complete_json_without_newline_after_terminal_is_one_protocol_reason(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    tail = json.dumps({
        "variant": "oracle-session", "stage": SESSION,
        "env_tag": "fixture-env", "ts": 1,
        "payload": {"event": "deviation", "message": "unframed"},
    }, separators=(",", ":")).encode("utf-8")
    with open(layout.wal_file, "ab") as stream:
        stream.write(tail)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert {row["reason"] for row in rows} == {
        "WAL の末尾 record が途中で切れている",
    }
    assert all(row["bench_values"] == [] for row in rows)


def test_campaign_start_after_completed_terminal_is_one_position_reason(tmp_path):
    """campaign-start の件数・内容を正常に保ち、物理位置だけを壊す。"""
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _finish_campaign(layout, manifest)
    _campaign_start(layout, manifest)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert {row["reason"] for row in rows} == {
        "campaign-terminal が WAL の最終 record でない",
    }
    assert all(row["bench_values"] == [] for row in rows)


def test_aborted_terminal_with_later_record_keeps_position_and_status_reasons(tmp_path):
    """A02 は受理集合 kill でなく、位置と意味の anti-masking 回帰 pin とする。"""
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _finish_campaign(layout, manifest, status="aborted")
    _campaign_start(layout, manifest)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert {row["reason"] for row in rows} == {
        "campaign-terminal が WAL の最終 record でない; "
        "campaign-terminal.status='aborted'",
    }
    assert all(row["bench_values"] == [] for row in rows)


def test_trial_result_after_campaign_terminal_remains_rejected_regression_pin(tmp_path):
    """旧部分 gate でも捕捉済みの順序違反は、変異 kill に数えない回帰 pin。"""
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    _trial_result(layout, item, attempt=1)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    assert all(row["status"] == "protocol_violation" for row in rows)
    assert all(row["bench_values"] == [] for row in rows)


def test_campaign_terminal_rejects_extra_top_level_key(tmp_path):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    for item in schedule:
        _trial(layout, item, "committed")
    _session(layout, "campaign-terminal", {
        "status": "completed", "scheduled_rows": len(schedule),
        "completed_rows": len(schedule),
        "execution_identity": {
            "job": "j", "host": "h", "boot": "b", "pid": 1, "starttime": 2,
        },
        "unexpected": "must-fail",
    })

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]
    assert all(row["status"] == "campaign-incomplete" for row in rows)
    assert all(row["bench_values"] == [] for row in rows)
    assert all("top-level key" in row["reason"] for row in rows)


@pytest.mark.parametrize("damage", ["aborted", "double", "under-covered", "coverage"])
def test_terminal_all_or_nothing_rejects_every_row_and_hides_all_numbers(
        tmp_path, damage):
    manifest = _manifest(tmp_path)
    schedule = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    for item in (schedule[:1] if damage == "coverage" else schedule):
        _trial(layout, item, "committed", tps=(100.0, 101.0, 102.0, 103.0, 104.0))
    if damage == "aborted":
        _finish_campaign(layout, manifest, status="aborted", fill_missing=False,
                         completed_rows=len(schedule) - 1)
    elif damage == "under-covered":
        _finish_campaign(layout, manifest, fill_missing=False,
                         completed_rows=len(schedule) - 1)
    elif damage == "double":
        _finish_campaign(layout, manifest, fill_missing=False)
        _finish_campaign(layout, manifest, status="aborted", fill_missing=False)
    else:
        _finish_campaign(layout, manifest, fill_missing=False)

    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]

    if damage == "double":
        assert all(row["status"] == "protocol_violation" for row in rows)
        assert {row["reason"] for row in rows} == {
            "campaign-terminal が WAL の最終 record でない; "
            "campaign-terminal が一意でない: 2",
        }
    else:
        assert all(row["status"] == "campaign-incomplete" for row in rows)
    assert all(row["bench_values"] == [] for row in rows)


def test_screen_marker_is_protocol_violation(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "committed", screen_marker=True)
    _finish_campaign(layout, manifest)

    row = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]

    assert row["status"] == "protocol_violation"
    assert "screen marker" in row["reason"]


def test_declared_campaign_without_schedule_row_is_structured_and_taints_all_real_rows(
        tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = manifest["schedule"]["rows"][:1]
    real_row = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _finish_campaign_rows(layout, [real_row])

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    ghost_message = (
        "manifest.campaign_ids の宣言に schedule row がない: "
        "block_id='b1', campaign_id='oracle-b1'"
    )
    assert observations["manifest_issues"] == [{
        "code": "campaign-without-schedule-row",
        "campaign_id": "oracle-b1",
        "message": ghost_message,
    }]
    assert len(observations["rows"]) == 1
    assert all(
        row["status"] == "protocol_violation"
        and row["bench_values"] == []
        and ghost_message in row["reason"]
        for row in observations["rows"]
    )


def test_mapping_ghost_is_detected_per_block_before_campaign_id_collapse(
        tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = manifest["schedule"]["rows"][:1]
    manifest["campaign_ids"] = {
        "b0": "oracle-shared",
        "b1": "oracle-shared",
    }
    item = manifest["schedule"]["rows"][0]
    layout = campaign_layout(
        "oracle-shared", output_root=str(tmp_path),
    ).ensure()
    _campaign_start(
        layout, manifest, "oracle-shared", block_id="b0",
    )
    _finish_campaign_rows(layout, [item])

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert observations["manifest_issues"] == [{
        "code": "campaign-without-schedule-row",
        "campaign_id": "oracle-shared",
        "message": (
            "manifest.campaign_ids の宣言に schedule row がない: "
            "block_id='b1', campaign_id='oracle-shared'"
        ),
    }]
    assert observations["rows"][0]["status"] == "protocol_violation"


def test_string_list_campaign_declaration_detects_ghost_per_campaign_id(
        tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = manifest["schedule"]["rows"][:1]
    manifest["schedule"]["rows"][0]["campaign_id"] = "oracle-b0"
    manifest["campaign_ids"] = ["oracle-b0", "oracle-ghost"]
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _finish_campaign_rows(layout, [item])

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert observations["manifest_issues"] == [{
        "code": "campaign-without-schedule-row",
        "campaign_id": "oracle-ghost",
        "message": (
            "manifest.campaign_ids の宣言に schedule row がない: "
            "campaign_id='oracle-ghost'"
        ),
    }]
    assert observations["rows"][0]["status"] == "protocol_violation"


def test_single_string_campaign_declaration_is_rejected(tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = []
    manifest["campaign_ids"] = "oracle-ghost"

    with pytest.raises(
            report.ReportError,
            match="campaign_ids は mapping または array でなければならない"):
        report.build_observations(
            manifest=manifest, output_root=tmp_path,
        )


def test_only_ghost_campaign_is_visible_without_synthetic_row(tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = []
    manifest["campaign_ids"] = {"ghost-block": "oracle-ghost"}

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert observations["rows"] == []
    assert observations["expected_cells"] == []
    assert observations["manifest_issues"] == [{
        "code": "campaign-without-schedule-row",
        "campaign_id": "oracle-ghost",
        "message": (
            "manifest.campaign_ids の宣言に schedule row がない: "
            "block_id='ghost-block', campaign_id='oracle-ghost'"
        ),
    }]
    assert _judge(observations)["status"] == "indeterminate"


def test_ghost_campaign_extends_existing_manifest_issues(tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = manifest["schedule"]["rows"][:1]
    manifest["run_contract"]["reps"] = 4
    real_row = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _finish_campaign_rows(layout, [real_row])

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )
    row = observations["rows"][0]

    assert [issue["code"] for issue in observations["manifest_issues"]] == [
        "run-contract-reps-not-approved",
        "campaign-without-schedule-row",
    ]
    assert all(
        issue["message"] in row["reason"]
        for issue in observations["manifest_issues"]
    )
    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []


def test_ghost_campaign_does_not_mask_definitive_correctness_red(tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = manifest["schedule"]["rows"][:1]
    item = manifest["schedule"]["rows"][0]
    layout = _layout(tmp_path, manifest)
    _trial(layout, item, "legacy-red")
    _finish_campaign(layout, manifest, fill_missing=False)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )
    row = observations["rows"][0]
    ghost_message = observations["manifest_issues"][0]["message"]

    assert row["status"] == "protocol_violation"
    assert row["outcome"] == "correctness-red"
    assert row["bench_values"] == []
    assert ghost_message in row["reason"]
    assert row["reason"].count(ghost_message) == 1
    assert row["reason"] == ghost_message


def test_ghost_issue_reaches_early_return_rows(tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    manifest["schedule"]["rows"] = manifest["schedule"]["rows"][:1]
    _layout(tmp_path, manifest)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )
    row = observations["rows"][0]
    ghost_message = observations["manifest_issues"][0]["message"]

    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []
    assert row["outcome"] is None
    # 基準 HEAD の未 assessment sentinel を保ち、ghost 後処理で window
    # assessment を捏造しない。
    assert row["legacy_verify"] == "missing"
    assert "campaign-terminal が一意でない: 0" in row["reason"]
    assert ghost_message in row["reason"]
    assert row["reason"].count(ghost_message) == 1


def test_t080_sibling_metamorphic(tmp_path, monkeypatch):
    envelope = _t080_envelope()
    _mock_t080_resolution(monkeypatch, "active-valid", envelope)
    manifest = _schema_less_legacy(_manifest(tmp_path))
    _mark_official(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=envelope)
    _finish_campaign(layout, manifest)

    baseline = report.build_observations(
        manifest=manifest, output_root=tmp_path, repo_root=tmp_path / "repo",
    )
    assert baseline["manifest_issues"] == []
    assert baseline[report._T080_KEY] == envelope

    manifest["campaign_ids"]["b1"] = "oracle-ghost"
    lines = Path(layout.wal_file).read_text(encoding="utf-8").splitlines()
    rewritten = []
    for line in lines:
        record = json.loads(line)
        if record.get("payload", {}).get("event") == "campaign-start":
            record["payload"]["manifest_sha256"] = (
                oracle_manifest.manifest_sha256(manifest)
            )
        rewritten.append(
            json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        )
    Path(layout.wal_file).write_text(
        "\n".join(rewritten) + "\n", encoding="utf-8",
    )

    with_ghost = report.build_observations(
        manifest=manifest, output_root=tmp_path, repo_root=tmp_path / "repo",
    )
    assert [issue["code"] for issue in with_ghost["manifest_issues"]] == [
        "campaign-without-schedule-row",
    ]
    assert with_ghost[report._T080_KEY] is None


def test_all_declared_campaigns_with_rows_keep_completed_result_and_no_manifest_issues(
        tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    rows = manifest["schedule"]["rows"]
    for campaign_id, block_id, item in (
        ("oracle-b0", "b0", rows[0]),
        ("oracle-b1", "b1", rows[1]),
    ):
        layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
        _campaign_start(layout, manifest, campaign_id, block_id=block_id)
        _finish_campaign_rows(layout, [item])

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert observations["manifest_issues"] == []
    assert [row["status"] for row in observations["rows"]] == [
        "completed", "completed",
    ]
    assert all(row["bench_values"] for row in observations["rows"])


def test_only_manifest_campaign_is_read_and_missing_owned_campaign_is_reported(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["schedule"]["rows"][0]
    owned = _layout(tmp_path, manifest)
    _trial(owned, item, "committed", tps=(7.0, 7.5, 8.0, 8.5, 9.0))
    _finish_campaign(owned, manifest)
    external = _layout(tmp_path, manifest, "outside-manifest")
    _trial(
        external, item, "committed",
        tps=(9000.0, 9000.5, 9001.0, 9001.5, 9002.0),
    )
    _finish_campaign(external, manifest)
    rows = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"]
    assert rows[0]["bench_values"] == [7.0, 7.5, 8.0, 8.5, 9.0]

    shutil.rmtree(Path(owned.root))
    missing = report.build_observations(manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path)["rows"][0]
    assert missing["status"] == "campaign-incomplete"
    assert missing["reason"]


@pytest.mark.parametrize(
    "t080_value",
    [
        pytest.param(_T080_ABSENT, id="historical-absent"),
        pytest.param(
            {"state": "never-issued", "validation_head": "0" * 40},
            id="null",
        ),
    ],
)
def test_pre_r_campaign_start_absent_or_null_is_allowed(tmp_path, t080_value):
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=t080_value)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest),
        output_root=tmp_path, repo_root=tmp_path / "repo",
    )

    assert observations["t080_freeze_migration_observation"] is None
    if t080_value is _T080_ABSENT:
        assert {row["status"] for row in observations["rows"]} == {"protocol_violation"}
        assert all(
            "t080-freeze-migration-observation: campaign-start に T-080 key がない"
            in (row.get("reason") or "")
            for row in observations["rows"]
        )
    else:
        assert {row["status"] for row in observations["rows"]} == {"completed"}
        assert all(
            not (row.get("reason") or "").startswith(
                "t080-freeze-migration-observation: "
            )
            for row in observations["rows"]
        )


def test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate(
    tmp_path, monkeypatch,
):
    envelope = _t080_envelope()
    repo_root = tmp_path / "temporary-repo"
    roots = _mock_t080_resolution(monkeypatch, "active-valid", envelope)
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=envelope)
    _finish_campaign(layout, manifest)

    baseline = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path, repo_root=repo_root,
    )
    assert baseline["t080_freeze_migration_observation"] == envelope
    assert _judge(baseline)["status"] == "determinate"

    lines = Path(layout.wal_file).read_text(encoding="utf-8").splitlines()
    rewritten = []
    for line in lines:
        record = json.loads(line)
        if record.get("payload", {}).get("event") == "campaign-start":
            record["payload"].pop("t080_freeze_migration_observation")
        rewritten.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
    Path(layout.wal_file).write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    damaged = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path, repo_root=repo_root,
    )
    assert roots == [repo_root, repo_root, repo_root]
    assert damaged["t080_freeze_migration_observation"] is None
    assert {row["status"] for row in damaged["rows"]} == {"protocol_violation"}
    assert all(
        (row.get("reason") or "").count(
            "t080-freeze-migration-observation: campaign-start に T-080 key がない"
        ) == 1
        for row in damaged["rows"]
    )
    assert _judge(damaged)["status"] == "indeterminate"


def test_historical_receipt_derivation_failure_invalidates_all_campaign_rows_g2(
    tmp_path, monkeypatch,
):
    envelope = _t080_envelope()
    history = report._t080.ReceiptResolution(
        "invalid", (), None, envelope["validation_head"],
        "d" * 40, {"migration_basis_commit": envelope["migration_basis_commit"]}, b"{}",
    )
    monkeypatch.setattr(
        report._t080, "inspect_receipt_history", lambda **_kwargs: history,
    )
    monkeypatch.setattr(
        report._t080, "_verify_historical_receipt_derivation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            report._t080.MigrationError("receipt.derivation_mismatch", "tampered R")
        ),
    )
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=envelope)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest),
        output_root=tmp_path, repo_root=tmp_path / "repo",
    )

    assert observations["t080_freeze_migration_observation"] is None
    assert {row["status"] for row in observations["rows"]} == {"protocol_violation"}
    assert all(
        "receipt.derivation_mismatch" in (row.get("reason") or "")
        for row in observations["rows"]
    )


def test_post_r_null_is_protocol_violation_for_every_campaign_row(
    tmp_path, monkeypatch,
):
    envelope = _t080_envelope()
    _mock_t080_resolution(monkeypatch, "active-valid", envelope)
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=None)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path, repo_root=tmp_path / "repo",
    )

    assert {row["status"] for row in observations["rows"]} == {"protocol_violation"}
    assert {row["reason"] for row in observations["rows"]} == {
        "t080-freeze-migration-observation: bare null は現行 grammar で禁止",
    }


def test_malformed_t080_envelope_is_fail_closed(tmp_path, monkeypatch):
    envelope = _t080_envelope()
    malformed = copy.deepcopy(envelope)
    malformed["schema_version"] = "unknown/v1"
    _mock_t080_resolution(monkeypatch, "active-valid", envelope)
    manifest = _manifest(tmp_path)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path)).ensure()
    _campaign_start(layout, manifest, t080_observation=malformed)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path, repo_root=tmp_path / "repo",
    )

    assert observations["t080_freeze_migration_observation"] is None
    assert {row["status"] for row in observations["rows"]} == {"protocol_violation"}
    assert {row["reason"] for row in observations["rows"]} == {
        "t080-freeze-migration-observation: malformed envelope: "
        "schema_version が不正",
    }


def test_campaign_canonical_envelope_mismatch_is_protocol_violation(
    tmp_path, monkeypatch,
):
    first = _t080_envelope("a")
    second = _t080_envelope("b")
    _mock_t080_resolution(monkeypatch, "active-valid", first)
    manifest = _two_campaign_report_setup(tmp_path)
    by_campaign = {
        "oracle-b0": ("b0", [manifest["schedule"]["rows"][0]], first),
        "oracle-b1": ("b1", [manifest["schedule"]["rows"][1]], second),
    }
    for campaign_id, (block_id, rows, envelope) in by_campaign.items():
        layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
        _campaign_start(
            layout, manifest, campaign_id, block_id=block_id,
            t080_observation=envelope,
        )
        _finish_campaign_rows(layout, rows)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
        repo_root=tmp_path / "repo",
    )

    assert observations["t080_freeze_migration_observation"] is None
    assert [row["status"] for row in observations["rows"]] == [
        "completed", "protocol_violation",
    ]
    assert observations["rows"][1]["reason"] == (
        "t080-freeze-migration-observation: "
        "malformed envelope: envelope が R blob/Git 再導出値と不一致"
    )


def test_matching_canonical_envelopes_are_copied_to_report_sibling(
    tmp_path, monkeypatch,
):
    envelope = _t080_envelope()
    reordered = json.loads(json.dumps(envelope, sort_keys=True))
    _mock_t080_resolution(monkeypatch, "active-valid", envelope)
    manifest = _two_campaign_report_setup(tmp_path)
    by_campaign = {
        "oracle-b0": ("b0", [manifest["schedule"]["rows"][0]], envelope),
        "oracle-b1": ("b1", [manifest["schedule"]["rows"][1]], reordered),
    }
    for campaign_id, (block_id, rows, value) in by_campaign.items():
        layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
        _campaign_start(
            layout, manifest, campaign_id, block_id=block_id,
            t080_observation=value,
        )
        _finish_campaign_rows(layout, rows)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
        repo_root=tmp_path / "repo",
    )

    assert observations["schema_version"] == "8b-oracle-observations/v1"
    assert observations["t080_freeze_migration_observation"] == envelope
    assert {row["status"] for row in observations["rows"]} == {"completed"}


def test_pre_r_null_and_object_mixture_is_protocol_violation(tmp_path):
    never_issued = {"state": "never-issued", "validation_head": "0" * 40}
    manifest = _two_campaign_report_setup(tmp_path)
    by_campaign = {
        "oracle-b0": ("b0", [manifest["schedule"]["rows"][0]], never_issued),
        "oracle-b1": ("b1", [manifest["schedule"]["rows"][1]], None),
    }
    for campaign_id, (block_id, rows, value) in by_campaign.items():
        layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
        _campaign_start(
            layout, manifest, campaign_id, block_id=block_id,
            t080_observation=value,
        )
        _finish_campaign_rows(layout, rows)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
        repo_root=tmp_path / "repo",
    )

    assert observations["t080_freeze_migration_observation"] is None
    assert [row["status"] for row in observations["rows"]] == [
        "completed", "protocol_violation",
    ]
    assert observations["rows"][1]["reason"] == (
        "t080-freeze-migration-observation: bare null は現行 grammar で禁止"
    )


def _degraded_perf_observation() -> dict:
    receipt = {
        "schema": perf_preflight.SCHEMA,
        "status": "unavailable",
        "available": False,
        "probe_argv": list(perf_preflight._BASE_PROBE_ARGV),
        "rc": None,
        "parsed_events": [],
        "reason": "perf-not-found",
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }
    observation = perf_preflight.build_perf_observation(
        receipt,
        run_cmd=["ccbench"],
        leading_indicators={"ipc": None, "llc_miss_rate": None},
    )
    assert observation is not None
    return observation


def _degraded_campaign(
        tmp_path: Path, manifest: dict, campaign_id: str, block_id: str,
        rows: list[dict], *, observation: dict | None = None,
) -> None:
    _mark_official(tmp_path)
    selected = _degraded_perf_observation() if observation is None else observation
    layout = campaign_layout(campaign_id, output_root=str(tmp_path)).ensure()
    sidecar = Path(layout.root) / "measurement-manifest.json"
    artifacts.write_measurement_manifest(
        sidecar,
        oracle_manifest_sha256=oracle_manifest.manifest_sha256(manifest),
        campaign_id=campaign_id,
        block_id=block_id,
        perf_observation=selected,
        run_cmd=["ccbench"],
        leading_indicators={"ipc": None, "llc_miss_rate": None},
    )
    _campaign_start(
        layout,
        manifest,
        campaign_id,
        block_id=block_id,
        measurement_manifest={
            "path": sidecar.name,
            "sha256": artifacts.measurement_manifest_sha256(sidecar),
        },
    )
    _finish_campaign_rows(
        layout,
        rows,
        bench_payload_extra={
            "run_cmd": ["ccbench"],
            "leading_indicators": {"ipc": None, "llc_miss_rate": None},
            "perf_observation": selected,
        },
    )


def test_degraded_report_emits_bound_measurement_conditions(tmp_path):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    rows = manifest["schedule"]["rows"]
    _degraded_campaign(tmp_path, manifest, "oracle-b0", "b0", rows)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    conditions = observations["measurement_conditions"]
    assert len(conditions) == 1
    assert conditions[0]["campaign_id"] == "oracle-b0"
    assert conditions[0]["measurement_manifest_sha256"] is not None
    assert conditions[0]["perf_observation"] == _degraded_perf_observation()
    assert all(row["bench_values"] for row in observations["rows"])


def test_measurement_conditions_cover_every_expected_campaign(tmp_path):
    manifest = _two_campaign_report_setup(tmp_path)
    rows = manifest["schedule"]["rows"]
    _degraded_campaign(tmp_path, manifest, "oracle-b0", "b0", [rows[0]])
    perf_layout = campaign_layout("oracle-b1", output_root=str(tmp_path)).ensure()
    _campaign_start(perf_layout, manifest, "oracle-b1", block_id="b1")
    _finish_campaign_rows(perf_layout, [rows[1]])

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    conditions = observations["measurement_conditions"]
    assert [entry["campaign_id"] for entry in conditions] == [
        "oracle-b0", "oracle-b1",
    ]
    assert conditions[1] == {
        "campaign_id": "oracle-b1",
        "measurement_manifest_sha256": None,
        "perf_observation": None,
    }


def test_report_rejects_sidecar_bench_observation_mismatch(tmp_path):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    rows = manifest["schedule"]["rows"]
    observation = _degraded_perf_observation()
    _degraded_campaign(
        tmp_path, manifest, "oracle-b0", "b0", rows,
        observation=observation,
    )
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path))
    lines = Path(layout.wal_file).read_text(encoding="utf-8").splitlines()
    rewritten = []
    for line in lines:
        record = json.loads(line)
        if record.get("stage") == "bench_done":
            record["payload"]["perf_observation"]["claim_scope"]["throughput"] = (
                "unsupported"
            )
        rewritten.append(json.dumps(record, separators=(",", ":")))
    Path(layout.wal_file).write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    with pytest.raises(report.ReportError, match="sidecar と bench"):
        report.build_observations(manifest=manifest, output_root=tmp_path)


def test_degraded_campaign_condition_rejects_omitted_bench_observation(
        tmp_path, monkeypatch):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    rows = manifest["schedule"]["rows"]
    layout = _layout(tmp_path, manifest)
    _finish_campaign_rows(layout, rows)
    observation = _degraded_perf_observation()
    monkeypatch.setattr(
        report,
        "_measurement_condition_for_campaign",
        lambda campaign_id, *_args, **_kwargs: {
            "campaign_id": campaign_id,
            "measurement_manifest_sha256": "0" * 64,
            "perf_observation": observation,
        },
    )

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    row = observations["rows"][0]
    assert row["status"] == "protocol_violation"
    assert row["bench_values"] == []
    assert "campaign 測定条件と不一致" in row["reason"]


def test_report_rejects_campaign_start_sidecar_hash_mismatch(tmp_path):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    rows = manifest["schedule"]["rows"]
    _degraded_campaign(tmp_path, manifest, "oracle-b0", "b0", rows)
    layout = campaign_layout("oracle-b0", output_root=str(tmp_path))
    lines = Path(layout.wal_file).read_text(encoding="utf-8").splitlines()
    rewritten = []
    for line in lines:
        record = json.loads(line)
        payload = record.get("payload", {})
        if payload.get("event") == "campaign-start":
            payload["measurement_manifest"]["sha256"] = "f" * 64
        rewritten.append(json.dumps(record, separators=(",", ":")))
    Path(layout.wal_file).write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    with pytest.raises(report.ReportError, match="raw hash"):
        report.build_observations(manifest=manifest, output_root=tmp_path)


def test_report_throughput_projection_calls_claim_gate(tmp_path, monkeypatch):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    rows = manifest["schedule"]["rows"]
    _degraded_campaign(tmp_path, manifest, "oracle-b0", "b0", rows)
    calls = []
    monkeypatch.setattr(
        report._perf_preflight,
        "perf_claim_allowed",
        lambda *args, **kwargs: calls.append((args, kwargs)) or False,
    )

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert calls
    assert all(row["bench_values"] == [] for row in observations["rows"])
    assert all(row["status"] == "protocol_violation" for row in observations["rows"])


def test_all_perf_report_preserves_exact_legacy_keys(tmp_path):
    manifest = _schema_less_legacy(_manifest(tmp_path))
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=manifest, output_root=tmp_path,
    )

    assert set(observations) == {
        "schema_version", "manifest_kind", "manifest_sha256", "n_per_cell",
        "expected_cells", "rows", "manifest_issues", "campaign_verifier_epochs",
        "t080_freeze_migration_observation",
    }


def test_all_perf_report_preserves_exact_official_keys(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)
    verified = _official_report_setup(tmp_path, manifest)
    reverified, _binaries = _reverified_store_fixture(verified, tmp_path)

    observations = report.build_observations(
        manifest=verified, output_root=tmp_path,
        reverified_freeze=reverified,
    )

    assert set(observations) == {
        "schema_version", "manifest_kind", "manifest_sha256", "spec_sha256",
        "n_per_cell", "expected_cells", "rows", "manifest_issues",
        "campaign_verifier_epochs", "t080_freeze_migration_observation",
        "store_reverification",
    }


def test_official_direct_api_without_reverified_freeze_is_non_certifying(tmp_path):
    manifest = _manifest(tmp_path)
    layout = _layout(tmp_path, manifest)
    _finish_campaign(layout, manifest)

    observations = report.build_observations(
        manifest=_official_report_setup(tmp_path, manifest), output_root=tmp_path,
    )

    assert "store_reverification" not in observations


def test_store_reverification_rejects_empty_binary_authority(tmp_path):
    verified = _official_report_setup(tmp_path, _manifest(tmp_path))
    reverified, _binaries = _reverified_store_fixture(verified, tmp_path)
    empty = dataclasses.replace(
        reverified, binaries_by_cell=MappingProxyType({}),
    )

    with pytest.raises(report.ReportError, match="binaries_by_cell.*空"):
        report.build_observations(
            manifest=verified, output_root=tmp_path,
            reverified_freeze=empty,
        )


@pytest.mark.parametrize("coverage", ["missing", "extra"])
def test_store_reverification_rejects_binary_cell_coverage(tmp_path, coverage):
    verified = _official_report_setup(tmp_path, _manifest(tmp_path))
    reverified, binaries = _reverified_store_fixture(verified, tmp_path)
    damaged = copy.deepcopy(binaries)
    if coverage == "missing":
        damaged.pop(next(iter(damaged)))
    else:
        damaged["outside::schedule"] = {
            "cell_id": "outside::schedule",
            "store_path": "fixture-store/outside--schedule/binary",
            "binary_sha256": "d" * 64,
        }
    forged = dataclasses.replace(
        reverified, binaries_by_cell=MappingProxyType(damaged),
    )

    with pytest.raises(report.ReportError, match="完全被覆"):
        report.build_observations(
            manifest=verified, output_root=tmp_path,
            reverified_freeze=forged,
        )


@pytest.mark.parametrize("path_kind", ["absolute", "parent", "control", "backslash"])
def test_store_reverification_rejects_out_of_root_store_path(tmp_path, path_kind):
    verified = _official_report_setup(tmp_path, _manifest(tmp_path))
    reverified, binaries = _reverified_store_fixture(verified, tmp_path)
    damaged = copy.deepcopy(binaries)
    victim = damaged[next(iter(sorted(damaged)))]
    victim["store_path"] = {
        "absolute": str(tmp_path / "absolute-store"),
        "parent": "../outside-store",
        "control": "fixture-store/control\x01store",
        "backslash": "fixture-store\\outside-store",
    }[path_kind]
    forged = dataclasses.replace(
        reverified, binaries_by_cell=MappingProxyType(damaged),
    )

    with pytest.raises(report.ReportError, match="store_path"):
        report.build_observations(
            manifest=verified, output_root=tmp_path,
            reverified_freeze=forged,
        )


@pytest.mark.parametrize("symlink_kind", ["parent", "leaf"])
def test_store_reverification_rejects_out_of_root_symlink(tmp_path, symlink_kind):
    output_root = tmp_path / "output"
    store_path = "fixture-store/cell/binary"
    victim_path = output_root / store_path
    victim_path.parent.mkdir(parents=True)
    victim_path.write_bytes(b"store symlink fixture\n")
    outside = tmp_path / "outside"
    outside.mkdir()
    if symlink_kind == "parent":
        outside_binary = outside / "binary"
        outside_binary.write_bytes(victim_path.read_bytes())
        victim_path.unlink()
        victim_path.parent.rmdir()
        victim_path.parent.symlink_to(outside, target_is_directory=True)
    else:
        outside_binary = outside / "binary"
        outside_binary.write_bytes(victim_path.read_bytes())
        victim_path.unlink()
        victim_path.symlink_to(outside_binary)

    with pytest.raises(report.ReportError, match="store_path|symlink"):
        report._store_sha256_nofollow(
            output_root=output_root, store_path=store_path,
        )


def test_store_reverification_parent_nofollow_blocks_stat_open_race(tmp_path):
    """O_NOFOLLOW を消すと raced parent open は hash 成功側へ転び、この対照が落ちる。"""
    output_root = tmp_path / "output"
    victim_parent = output_root / "store" / "cell"
    victim_parent.mkdir(parents=True)
    victim = victim_parent / "binary"
    raw = b"parent race control\n"
    victim.write_bytes(raw)
    outside = tmp_path / "outside-parent"
    outside.mkdir()
    (outside / "binary").write_bytes(raw)
    real_open = report.os.open
    exchanged = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal exchanged
        if path == "cell" and dir_fd is not None and not exchanged:
            exchanged = True
            victim.unlink()
            victim_parent.rmdir()
            victim_parent.symlink_to(outside, target_is_directory=True)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    with mock.patch.object(report.os, "open", side_effect=racing_open):
        with pytest.raises(report.ReportError, match="parent component.*no-follow"):
            report._store_sha256_nofollow(
                output_root=output_root, store_path="store/cell/binary",
            )
    assert exchanged


def test_store_reverification_leaf_nofollow_blocks_stat_open_race(tmp_path):
    """O_NOFOLLOW を消すと raced leaf open は hash 成功側へ転び、この対照が落ちる。"""
    output_root = tmp_path / "output"
    victim_parent = output_root / "store" / "cell"
    victim_parent.mkdir(parents=True)
    victim = victim_parent / "binary"
    raw = b"leaf race control\n"
    victim.write_bytes(raw)
    outside = tmp_path / "outside-leaf"
    outside.write_bytes(raw)
    real_open = report.os.open
    exchanged = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal exchanged
        if path == "binary" and dir_fd is not None and not exchanged:
            exchanged = True
            victim.unlink()
            victim.symlink_to(outside)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    with mock.patch.object(report.os, "open", side_effect=racing_open):
        with pytest.raises(report.ReportError, match="leaf.*no-follow"):
            report._store_sha256_nofollow(
                output_root=output_root, store_path="store/cell/binary",
            )
    assert exchanged


def test_store_reverification_requires_exact_token_and_manifest_freeze_binding(
        tmp_path):
    verified = _official_report_setup(tmp_path, _manifest(tmp_path))
    reverified, _binaries = _reverified_store_fixture(verified, tmp_path)
    with pytest.raises(report.ReportError, match="exact type"):
        report.build_observations(
            manifest=verified, output_root=tmp_path,
            reverified_freeze=SimpleNamespace(
                ratified=reverified.ratified,
                binaries_by_cell=reverified.binaries_by_cell,
            ),
        )

    wrong_freeze = dataclasses.replace(
        reverified, ratified=SimpleNamespace(sha256="f" * 64),
    )
    with pytest.raises(report.ReportError, match="manifest.freeze.sha256"):
        report.build_observations(
            manifest=verified, output_root=tmp_path,
            reverified_freeze=wrong_freeze,
        )


def test_legacy_manifest_rejects_reverified_freeze(tmp_path):
    manifest = _manifest(tmp_path)
    verified = _official_report_setup(tmp_path, manifest)
    reverified, _binaries = _reverified_store_fixture(verified, tmp_path)

    with pytest.raises(report.ReportError, match="legacy manifest"):
        report.build_observations(
            manifest=_schema_less_legacy(manifest), output_root=tmp_path,
            reverified_freeze=reverified,
        )


def test_store_reverification_expected_sha_comes_from_reverified_freeze(tmp_path):
    verified = _official_report_setup(tmp_path, _manifest(tmp_path))
    reverified, binaries = _reverified_store_fixture(verified, tmp_path)
    damaged = copy.deepcopy(binaries)
    victim_id = next(iter(sorted(damaged)))
    damaged[victim_id]["binary_sha256"] = "f" * 64
    forged = dataclasses.replace(
        reverified, binaries_by_cell=MappingProxyType(damaged),
    )

    observations = report.build_observations(
        manifest=verified, output_root=tmp_path,
        reverified_freeze=forged,
    )
    victim = next(
        cell for cell in observations["store_reverification"]["cells"]
        if cell["cell_id"] == victim_id
    )
    assert victim["expected_sha256"] == "f" * 64
    assert victim["actual_sha256"] == binaries[victim_id]["binary_sha256"]
    assert victim["state"] == "mismatch"
    assert observations["store_reverification"]["state"] == "unverified"


def test_store_reverification_requires_regular_leaf_fstat(tmp_path):
    output_root = tmp_path / "output"
    store_path = "fixture-store/cell/binary"
    leaf = output_root / store_path
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"regular leaf fixture\n")

    with mock.patch.object(report.os, "fstat", return_value=tmp_path.stat()):
        with pytest.raises(report.ReportError, match="regular file"):
            report._store_sha256_nofollow(
                output_root=output_root, store_path=store_path,
            )


def test_store_reverification_hashes_store_in_bounded_chunks(tmp_path):
    output_root = tmp_path / "output"
    store_path = "fixture-store/cell/binary"
    raw = b"x" * (1024 * 1024 + 1)
    leaf = output_root / store_path
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(raw)
    real_read = report.os.read
    requested_sizes = []

    def recording_read(descriptor, size):
        requested_sizes.append(size)
        return real_read(descriptor, size)

    with mock.patch.object(report.os, "read", side_effect=recording_read):
        actual_sha256 = report._store_sha256_nofollow(
            output_root=output_root, store_path=store_path,
        )

    assert actual_sha256 == hashlib.sha256(raw).hexdigest()
    assert requested_sizes
    assert set(requested_sizes) == {1024 * 1024}
    assert len(requested_sizes) == 3


def test_build_observations_production_caller_is_main_only():
    target_module = "orchestrator.campaign.s8b_oracle_report"
    callers = []
    function_types = (ast.FunctionDef, ast.AsyncFunctionDef)

    def dotted_name(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = dotted_name(node.value)
            if prefix is not None:
                return f"{prefix}.{node.attr}"
        return None

    for source_path in sorted(ORCH.rglob("*.py")):
        relative_path = source_path.relative_to(ORCH)
        if "tests" in relative_path.parts:
            continue
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), filename=str(source_path),
        )
        module_parts = ["orchestrator", *relative_path.with_suffix("").parts]
        if module_parts[-1] == "__init__":
            module_parts.pop()
        module_name = ".".join(module_parts)
        package_parts = module_parts.copy()
        if source_path.name != "__init__.py":
            package_parts.pop()
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }

        def function_chain(node):
            chain = []
            parent = parents.get(node)
            while parent is not None:
                if isinstance(parent, function_types):
                    chain.append(parent)
                parent = parents.get(parent)
            return list(reversed(chain))

        direct_bindings = {None: set()}
        module_bindings = {None: set()}
        if module_name == target_module:
            direct_bindings[None].add("build_observations")

        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            chain = function_chain(node)
            scope = chain[-1] if chain else None
            direct_bindings.setdefault(scope, set())
            module_bindings.setdefault(scope, set())
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == target_module:
                        module_bindings[scope].add(
                            alias.asname if alias.asname else target_module
                        )
                continue
            if node.level:
                keep = len(package_parts) - node.level + 1
                if keep < 0:
                    continue
                imported_parts = package_parts[:keep]
            else:
                imported_parts = []
            if node.module:
                imported_parts.extend(node.module.split("."))
            imported_module = ".".join(imported_parts)
            for alias in node.names:
                bound_name = alias.asname if alias.asname else alias.name
                if (imported_module == target_module
                        and alias.name == "build_observations"):
                    direct_bindings[scope].add(bound_name)
                elif ".".join(
                        part for part in (imported_module, alias.name) if part
                ) == target_module:
                    module_bindings[scope].add(bound_name)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            chain = function_chain(node)
            visible_scopes = [None, *chain]
            visible_direct = set().union(*(
                direct_bindings.get(scope, set()) for scope in visible_scopes
            ))
            visible_modules = set().union(*(
                module_bindings.get(scope, set()) for scope in visible_scopes
            ))
            called_name = dotted_name(node.func)
            direct_call = (
                isinstance(node.func, ast.Name)
                and node.func.id in visible_direct
            )
            module_call = any(
                called_name == f"{binding}.build_observations"
                for binding in visible_modules
            )
            if direct_call or module_call:
                scope_name = chain[-1].name if chain else "<module>"
                callers.append((source_path.name, scope_name))

    assert callers == [("s8b_oracle_report.py", "main")]
