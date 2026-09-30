# -*- coding: utf-8 -*-
"""D12 層3材料レポートの決定論的な完全射影を検査する。"""
from __future__ import annotations

import ast
from collections import Counter
from contextlib import nullcontext
import dataclasses
from enum import Enum
import hashlib
import inspect
import json
import os
import subprocess
import sys
import textwrap
from collections.abc import Mapping
from types import SimpleNamespace
from pathlib import Path, PurePosixPath

import jsonschema
import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from orchestrator.campaign import (  # noqa: E402
    artifact_admission,
    autonomous_trial_completeness,
    campaign_lock,
    contract_loader_binding,
    env_attestation,
    env_contract,
    execution_guard,
    knowledge_manifest,
    layer3_report,
    model,
    p3_autonomous_workload_trial,
    p3_s4_loop,
    pipeline,
    s8c_acceptance_receipt,
    trigger_gate_binding,
    wal,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import CampaignLayout  # noqa: E402
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from orchestrator.calibrator import perf_preflight  # noqa: E402
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402


ROOT = _HERE.parent.parent
REAL_CAMPAIGN = ROOT / "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"
LEGACY_TRIGGER_SWEEP_CAMPAIGN = (
    ROOT / "output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2"
)
REAL_SCREENING_CAMPAIGN = (
    ROOT / "output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90"
)
YCSB = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}
ABORTED_FIXTURE_VARIANT = "2225adf39fa3"
REJECTED_FIXTURE_VARIANT = "d85dc0fc5a6e"
_UNSET = object()


def _binding_from_recorded_head() -> contract_loader_binding.ContractLoaderBinding:
    """Build a disk-independent binding from the recorded HEAD blobs."""
    root = contract_loader_binding._validated_root()
    commit = contract_loader_binding._head_commit(root)
    digests = {
        relative: hashlib.sha256(blob).hexdigest()
        for relative, blob in contract_loader_binding._iter_blobs(
            root, commit, campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS,
        )
    }
    return contract_loader_binding.ContractLoaderBinding(commit, digests)


def build_v2_campaign_lock(
        identity_preimage: str, *,
        authorization: env_contract.AuthorizedContract | None = None,
        binding: contract_loader_binding.ContractLoaderBinding | None = None,
        contract_loader_commit: str | None = None,
) -> str:
    """Build a v2 fixture without crossing the campaign module namespace."""
    if authorization is None:
        authorization = env_contract.authorize("linux-baremetal")
    if type(authorization) is not env_contract.AuthorizedContract:
        raise TypeError("authorization は exact AuthorizedContract が必要")
    if binding is None:
        binding = _binding_from_recorded_head()
    if type(binding) is not contract_loader_binding.ContractLoaderBinding:
        raise TypeError("binding は exact ContractLoaderBinding が必要")
    return campaign_lock.encode_campaign_lock_v2(
        identity_preimage,
        campaign_lock.CampaignLockAuthority(
            environment_contract_sha256=(
                authorization.contract.contract_sha256
            ),
            activation_serial=authorization.activation_serial,
            activation_state_sha256=authorization.activation_state_sha256,
            contract_loader_commit=(
                binding.contract_loader_commit
                if contract_loader_commit is None
                else contract_loader_commit
            ),
            contract_loader_blob_sha256s=dict(
                binding.contract_loader_blob_sha256s
            ),
        ),
    )


def _admission_bound_records(
    tmp_path: Path, records: list[dict], *, protocol: str | None = None,
) -> tuple[list[dict], dict]:
    """Turn semantic Layer3 fixtures into independently generated post-policy WAL."""
    copied = json.loads(json.dumps(records))
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    labels = list(dict.fromkeys(record["variant"] for record in copied))
    by_label = {label: [record for record in copied if record["variant"] == label]
                for label in labels}
    bindings = {}
    for ordinal, label in enumerate(labels):
        group = by_label[label]
        stages = {record["stage"] for record in group}
        needs_start = bool(stages & {
            "build_start", "build_done", "verify_done", "bench_done", "commit",
        })
        if not needs_start:
            continue
        bound_protocol = (
            protocol
            if protocol is not None
            else f"fixture-{hashlib.sha256(label.encode()).hexdigest()[:8]}"
        )
        canonical = (
            f"{bound_protocol}|FIXTURE_VARIANT={ordinal}"
            if protocol is not None else f"{bound_protocol}|"
        )
        variant = hashlib.sha256(canonical.encode()).hexdigest()[:12]
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=str(tmp_path.resolve()),
            ccbench_commit=CURRENT_PIN,
            genome_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
            src_token="stock",
            source_bytes_sha256="a" * 64,
            tracked_clean=True,
            tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )
        receipt = derive_build_admission(context, evidence).as_wal_receipt()
        bindings[label] = {
            "attempt": f"fixture-attempt-{ordinal}",
            "canonical": canonical,
            "variant": variant,
            "receipt": receipt,
        }

    rendered = []
    started = set()
    for record in copied:
        label = record["variant"]
        binding = bindings.get(label)
        if binding is None:
            rendered.append(record)
            continue
        if label not in started and record["stage"] != "build_start":
            rendered.append({
                "ts": record["ts"],
                "stage": "build_start",
                "variant": binding["variant"],
                "env_tag": record["env_tag"],
                "payload": {
                    "genome": binding["canonical"],
                    "src_token": "stock",
                    "build_attempt_id": binding["attempt"],
                    "build_admission": binding["receipt"],
                    "build_admission_receipt_sha256": binding["receipt"]["receipt_sha256"],
                },
            })
            started.add(label)
        record["variant"] = binding["variant"]
        if record["stage"] == "build_start":
            record["payload"].update({
                "genome": binding["canonical"],
                "src_token": "stock",
                "build_attempt_id": binding["attempt"],
                "build_admission": binding["receipt"],
                "build_admission_receipt_sha256": binding["receipt"]["receipt_sha256"],
            })
            started.add(label)
        elif record["stage"] in {"build_done", "commit", "abort"}:
            record["payload"]["build_attempt_id"] = binding["attempt"]
            record["payload"]["build_admission_receipt_sha256"] = (
                binding["receipt"]["receipt_sha256"]
            )
        rendered.append(record)
    return rendered, dict(context.policy.as_preimage())


def _campaign(tmp_path: Path, records, whiteboard=None, *, loop_state=True,
              ycsb=None, policy_hint=_UNSET, knowledge=None,
              protocol: str | None = None,
              authorization: env_contract.AuthorizedContract | None = None,
              records_count: int = 100000,
              threads: int = 4,
              exploration_root: bool = False,
              copy_contract_calibration: bool = True) -> tuple[Path, Path]:
    output_root = tmp_path / "repo" / "output"
    if exploration_root:
        output_root = output_root / "exploration"
    effective_authorization = (
        authorization
        if authorization is not None
        else env_contract.authorize("linux-baremetal")
    )
    if authorization is None:
        fixture_env = output_root / "env/test-env"
        fixture_env.mkdir(parents=True)
        (output_root / "env/linux-baremetal").symlink_to(
            "test-env", target_is_directory=True,
        )
    records, admission_policy = _admission_bound_records(
        tmp_path, records, protocol=protocol,
    )
    search_config = {
        "records": records_count,
        "threads": threads,
        "build_admission": admission_policy,
    }
    if ycsb is not None:
        search_config["ycsb"] = ycsb
    if policy_hint is not _UNSET:
        search_config["policy_hint"] = policy_hint
    if knowledge is not None:
        search_config[wal.KNOWLEDGE_LEVEL_SEARCH_KEY] = "K2"
        search_config[wal.KNOWLEDGE_MANIFEST_SHA256_SEARCH_KEY] = (
            knowledge.knowledge_manifest_sha256
        )
    identity_preimage = campaign_lock.canonical_json({
        "ccbench_commit": CURRENT_PIN, "search_config": search_config,
        "search_tag": "test", "spec_content": "test", "trial": "trial",
    })
    cfg_hash8 = hashlib.sha256(
        identity_preimage.encode("utf-8")
    ).hexdigest()[:8]
    root = output_root / "campaigns" / (
        "campaign-test-" + cfg_hash8
    )
    (root / "runs").mkdir(parents=True)
    (root / "campaign.lock").write_text(
        build_v2_campaign_lock(
            identity_preimage, authorization=effective_authorization,
        ),
        encoding="utf-8",
    )
    if knowledge is not None:
        knowledge_manifest.write_receipt(
            root,
            knowledge,
            classification="reproduction_or_selection",
            de_novo_claim=False,
        )
    if loop_state:
        (root / "loop_state.json").write_text(
            json.dumps({"whiteboard": whiteboard if whiteboard is not None else []}),
            encoding="utf-8")
    if knowledge is None:
        (root / "runs/wal.jsonl").write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
    else:
        layout = CampaignLayout(root=str(root))
        for record in records:
            wal.log(
                layout,
                record["variant"],
                record["stage"],
                record["env_tag"],
                record["payload"],
                ts=record["ts"],
            )
    if copy_contract_calibration:
        _copy_contract_calibration(output_root, effective_authorization)
    return root, output_root


def _resolved_knowledge_fixture(tmp_path: Path):
    repo = tmp_path / "knowledge-source-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Izanagi Test"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "izanagi-test@example.invalid"],
        cwd=repo,
        check=True,
    )
    content = b"material report knowledge source\n"
    (repo / "knowledge.txt").write_bytes(content)
    subprocess.run(["git", "add", "--", "knowledge.txt"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "knowledge fixture"],
        cwd=repo,
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True,
    ).strip()
    manifest_path = tmp_path / "knowledge-manifest.json"
    manifest_path.write_text(
        json.dumps({
            "knowledge_level": "K2",
            "sources": [{
                "kind": "repo_artifact",
                "identity": {"commit": commit, "path": "knowledge.txt"},
                "sha256": hashlib.sha256(content).hexdigest(),
            }],
        }),
        encoding="utf-8",
    )
    return knowledge_manifest.load_and_resolve_manifest(
        manifest_path, repo_root=repo,
    )


def _resolved_empty_knowledge_fixture(tmp_path: Path):
    manifest = knowledge_manifest.parse_manifest_bytes(json.dumps({
        "knowledge_level": "K2",
        "declared_scope": {
            "retrieval": [{
                "kind": "repo_artifact",
                "selector": "output/insights/2026-09-03_*",
            }],
            "injection": [{
                "kind": "repo_artifact",
                "selector": "all-successfully-retrieved-sources",
            }],
        },
        "retrieval_result": {
            "status": "completed_empty",
            "result_count": 0,
        },
        "sources": [],
    }, ensure_ascii=False).encode("utf-8"))
    return knowledge_manifest.resolve_live_sources(
        manifest, repo_root=tmp_path,
    )


def _knowledge_campaign(tmp_path: Path):
    resolved = _resolved_knowledge_fixture(tmp_path)
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        knowledge=resolved,
    )
    return campaign, output_root, resolved


def _knowledge_schema_specimen() -> dict:
    """Return a schema-valid report assembled without the report producer."""
    source = {
        "kind": "repo_artifact",
        "identity": {"commit": "a" * 40, "path": "knowledge.txt"},
        "sha256": "b" * 64,
    }
    absent_floor = {
        "value": None,
        "provenance": "no-matching-env-record",
        "source": None,
        "search": {},
    }
    return {
        "schema_version": "layer3-material-report/v3",
        "meta": {
            "campaign_id": "schema-fixture",
            "campaign_path": "output/campaigns/schema-fixture",
            "ccbench_commit": "fixture",
            "generated_from_head": "fixture",
            "generator": {
                "identity": "orchestrator.campaign.layer3_report",
                "sha256": "c" * 64,
            },
        },
        "workload": {},
        "policy_hint": None,
        "knowledge_provenance": {
            "knowledge_level": "K2",
            "knowledge_manifest_sha256": "d" * 64,
            "declared_sources": [json.loads(json.dumps(source))],
            "injected_sources": [json.loads(json.dumps(source))],
        },
        "variants": [],
        "runs": [],
        "verifications": [],
        "rejects": [],
        "aborts": [],
        "noise_floor": {
            "within_run": dict(absent_floor),
            "between_run": dict(absent_floor),
        },
        "env_tags": [],
        "whiteboard": [],
        "whiteboard_provenance": "absent",
        "artifact_refs": [],
        "source_refs": [],
        "admission_decision": {
            "schema_version": "campaign-artifact-admission-decision/v1",
            "classification": "admitted-new-schema",
            "admission_status": "admitted",
            "verification_status": "not-evaluated-by-overlay",
            "campaign_id": "schema-fixture",
            "campaign_path": "output/campaigns/schema-fixture",
            "campaign_lock_sha256": "e" * 64,
            "wal_sha256": "f" * 64,
            "policy_sha256": None,
            "attempt_receipt_sha256s": [],
            "validator": {
                "identity": "orchestrator.campaign.artifact_admission",
                "sha256": "1" * 64,
            },
            "overlay": {"ledger_sha256": "2" * 64, "record_key": None},
        },
        "mechanism_hypotheses": [],
    }


def _completed_empty_knowledge_schema_specimen() -> dict:
    report = _knowledge_schema_specimen()
    report["knowledge_provenance"] = {
        "knowledge_level": "K2",
        "knowledge_manifest_sha256": "d" * 64,
        "declared_scope": {
            "retrieval": [{
                "kind": "repo_artifact",
                "selector": "output/insights/2026-09-03_*",
            }],
            "injection": [{
                "kind": "repo_artifact",
                "selector": "all-successfully-retrieved-sources",
            }],
        },
        "retrieval_result": {
            "status": "completed_empty",
            "result_count": 0,
        },
        "declared_sources": [],
        "injected_sources": [],
    }
    return report


def _certifying_campaign(tmp_path: Path) -> tuple[Path, Path]:
    start_record = _record("build_start", genome="g", src_token="s")
    start_record["env_tag"] = "linux-baremetal"
    campaign, output_root = _campaign(
        tmp_path, [start_record],
    )
    layout = CampaignLayout(root=str(campaign))
    start = wal.read_records(layout)[0]
    attempt_id = start.payload["build_attempt_id"]
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": (
            start.payload["build_admission_receipt_sha256"]
        ),
    }
    wal.log(
        layout,
        start.variant,
        "build_done",
        start.env_tag,
        terminal,
        ts=2.0,
    )
    wal.log(
        layout,
        start.variant,
        "verify_done",
        start.env_tag,
        {
            "build_attempt_id": attempt_id,
            "verdict": "serializable",
            "certified": True,
            "anomalies": 0,
            "workload": {"tag": "legacy"},
        },
        ts=3.0,
    )
    decoded = campaign_lock.decode_campaign_lock(
        Path(layout.lock_file).read_text(encoding="utf-8")
    )
    assert decoded.authority is not None
    contract_env_tag = env_contract.resolve_by_contract_sha256(
        decoded.authority.environment_contract_sha256
    ).contract.env_tag
    receipt_support.log_receipted_commit(
        layout,
        start.variant,
        contract_env_tag,
        {
            **terminal,
            model.COMMIT_CONTRACT_SHA256_KEY: (
                decoded.authority.environment_contract_sha256
            ),
        },
        operation_identity=attempt_id,
        tags=("legacy",),
        ts=4.0,
    )
    return campaign, output_root


def _assert_external_campaign_without_git_head(campaign: Path) -> None:
    resolved = campaign.resolve()
    source_repo = layer3_report._DEFAULT_OUTPUT_ROOT.parent.resolve()
    assert not resolved.is_relative_to(source_repo)
    with pytest.raises(layer3_report.Layer3ReportError):
        layer3_report._git_head(campaign)


def _copy_contract_calibration(
        output_root: Path,
        authorization: env_contract.AuthorizedContract) -> Path:
    ref = authorization.contract.calibration_ref
    source = ROOT / ref.path
    env_tag = authorization.contract.env_tag
    relative_pin = PurePosixPath(ref.path)
    calibration_prefix = PurePosixPath(
        "output", "env", env_tag, "calibration",
    )
    suffix = relative_pin.relative_to(calibration_prefix)
    target = (
        output_root / "env" / env_tag / "calibration" / Path(*suffix.parts)
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    return target


def _historical_admitted_campaign(campaign: Path):
    admitted = layer3_report.require_admitted_campaign(
        campaign,
        purpose=layer3_report.CampaignReadPurpose.HISTORICAL_RAW,
    )
    decision = dataclasses.replace(
        admitted.decision,
        classification="historical-pre-admission-schema",
        admission_status="historical-not-reclassified",
    )
    return dataclasses.replace(admitted, decision=decision)


def _historical_exact_grammar_campaign(tmp_path, monkeypatch, grammar):
    from orchestrator.campaign import build_admission as B
    from orchestrator.tests import test_artifact_admission as support

    repo = support._committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    with monkeypatch.context() as issuing:
        issuing.setattr(B, "CURRENT_PIN", "d706650")
        issuing.setattr(support, "CURRENT_PIN", "d706650")
        issuing.setattr(support.receipt_support, "CURRENT_PIN", "d706650")
        issuing.setattr(
            support.receipt_support, "_PROOF_BUILD_CONTEXT",
            B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP),
        )
        campaign = support._new_schema_campaign(tmp_path / "recorded")
    if grammar == 85:
        support._rewrite_as_t2344_exact85_lock(campaign)
    elif grammar == 63:
        support._rewrite_as_t2429_exact63_lock(campaign)
    elif grammar == 62:
        support._rewrite_as_t733_exact62_lock(campaign)
    else:
        assert grammar == 24
        support._rewrite_as_pre_t733_lock(campaign)
    return campaign


def _certifying_receipt_for(campaign: Path):
    return SimpleNamespace(
        certifying=True,
        trials=(SimpleNamespace(campaign_id=campaign.name, trial_id="trial"),),
        relative_path="acceptance/receipt.json",
        sha256="a" * 64,
    )


def _verified_non_certifying_receipt(
    campaign: Path,
    output_root: Path,
) -> s8c_acceptance_receipt.VerifiedAcceptanceReceipt:
    repo = output_root.parent
    init = subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=False,
        capture_output=True, text=True,
    )
    assert init.returncode == 0, init.stderr
    for key, value in (
        ("user.email", "fixture@example.invalid"),
        ("user.name", "Fixture"),
    ):
        assert subprocess.run(
            ["git", "-C", str(repo), "config", key, value], check=False,
        ).returncode == 0

    def write(relative: str, data: bytes) -> str:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    manifest_path = "input/manifest.json"
    manifest_sha = write(manifest_path, b'{"fixture":"manifest"}\n')
    registry_path = "output/s8c-trial-registry/registry.jsonl"
    registry_sha = write(registry_path, b'{"fixture":"registry"}\n')
    lifecycle_path = "output/s8c-trial-registry/lifecycle.jsonl"
    lifecycle_sha = write(lifecycle_path, b'{"fixture":"lifecycle"}\n')
    trial_rows = []
    for index in range(6):
        trial_id = "trial" if index == 0 else f"trial-{index}"
        report_path = f"acceptance-refs/{trial_id}/report.json"
        journal_path = f"acceptance-refs/{trial_id}/attempts.jsonl"
        trial_rows.append({
            "trial_id": trial_id,
            "arm": ("on", "off", "swapped")[index % 3],
            "holdout": "H1" if index < 3 else "H2",
            "campaign_id": campaign.name if index == 0 else f"other-{index}",
            "status": "complete",
            "measurement_head": "1" * 40,
            "report_path": report_path,
            "report_sha256": write(report_path, f"report-{index}\n".encode()),
            "attempt_journal_path": journal_path,
            "attempt_journal_sha256": write(
                journal_path, f"journal-{index}\n".encode()
            ),
        })
    assert subprocess.run(
        ["git", "-C", str(repo), "add", "-A"], check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "references"],
        check=False,
    ).returncode == 0
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True,
    ).strip()
    value = {
        "schema_version": s8c_acceptance_receipt.LEGACY_SCHEMA_VERSION,
        "manifest_path": manifest_path,
        "manifest_sha256": manifest_sha,
        "prereg_commit": head,
        "activation_report_digest_sha256": "2" * 64,
        "registry_path": registry_path,
        "registry_blob_sha256": registry_sha,
        "registry_introduction_commit": head,
        "lifecycle_path": lifecycle_path,
        "lifecycle_prefix_bytes": len((repo / lifecycle_path).read_bytes()),
        "lifecycle_prefix_sha256": lifecycle_sha,
        "certifying": False,
        "non_certifying_reason_codes": sorted(
            s8c_acceptance_receipt.LEGACY_MANDATORY_NON_CERTIFYING_REASONS
        ),
        "trials": sorted(trial_rows, key=lambda item: item["trial_id"]),
    }
    receipt_path = repo.joinpath(
        *s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR.parts,
        f"{manifest_sha}.json",
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode() + b"\n"
    )
    assert subprocess.run(
        ["git", "-C", str(repo), "add", "-A"], check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "receipt"],
        check=False,
    ).returncode == 0
    return s8c_acceptance_receipt.verify_acceptance_receipt(
        receipt_path, repository_root=repo,
    )


def test_trigger_build_start_commitment_survives_report_projection_without_raw_mask():
    commitment = "c" * 64
    records = [{
        "variant": "trigger-v",
        "stage": "build_start",
        "env_tag": "test",
        "ts": 1.0,
        "payload": {
            "genome": "silo|BACK_OFF=1",
            "src_token": "stock",
            "trigger_gate_binding_commitment": commitment,
        },
    }]
    rows = layer3_report._variant_rows(records)
    assert rows[0]["events"][0]["payload"][
        "trigger_gate_binding_commitment"
    ] == commitment
    rendered = json.dumps(rows, sort_keys=True)
    assert '"mask"' not in rendered
    assert '"trigger_gate_binding"' not in rendered


def test_trigger_campaign_report_keeps_commitment_and_excludes_raw_binding(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [
            _record("build_start", genome="fixture|", src_token="stock"),
            _record("abort", reason="fixture-abort"),
        ],
    )
    lock_path = campaign / "campaign.lock"
    identity = json.loads(
        campaign_lock.decode_campaign_lock(
            lock_path.read_text(encoding="utf-8")
        ).identity_preimage
    )
    identity["search_config"].update({
        "axis": wal.TRIGGER_AXIS,
        "reflux": "on",
        wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY: trigger_gate_binding.SCHEMA_VERSION,
    })
    identity_preimage = campaign_lock.canonical_json(identity)
    lock_path.write_text(
        build_v2_campaign_lock(identity_preimage), encoding="utf-8",
    )
    canonical_campaign = campaign.with_name(
        f"campaign-{identity['search_tag']}-"
        f"{hashlib.sha256(identity_preimage.encode('utf-8')).hexdigest()[:8]}"
    )
    campaign.rename(canonical_campaign)
    campaign = canonical_campaign

    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    start = next(record for record in records if record["stage"] == "build_start")
    source = start["payload"]["build_admission"]["source"]
    binding = trigger_gate_binding.TriggerGateBinding(
        mask=4,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(4),
        nonce="4" * 64,
        source=trigger_gate_binding.SourceBinding(
            src_token=source["src_token"],
            source_bytes_sha256=source["source_bytes_sha256"],
        ),
    )
    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY] = \
        trigger_gate_binding.commitment(binding)
    raw = {
        "variant": start["variant"],
        "stage": trigger_gate_binding.WAL_RECORD_STAGE,
        "env_tag": start["env_tag"],
        "ts": start["ts"] - 0.5,
        "payload": {
            "build_attempt_id": start["payload"]["build_attempt_id"],
            wal.TRIGGER_BINDING_PAYLOAD_KEY: trigger_gate_binding.to_record(binding),
        },
    }
    records.insert(records.index(start), raw)
    wal_path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    reports = campaign / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "p3_s8a_trigger_loop_provenance.json").write_text(json.dumps({
        "entries": {
            "1": {
                "variant": start["variant"],
                "build_attempt_id": start["payload"]["build_attempt_id"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY:
                    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY],
            },
        },
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    rendered = json.dumps(report, sort_keys=True)
    assert start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY] in rendered
    assert '"trigger_gate_binding"' not in rendered
    assert '"mask"' not in rendered


def _record(stage, variant="v1", *, env_tag="linux-baremetal", **payload):
    return {"ts": 1.0, "stage": stage, "variant": variant, "env_tag": env_tag, "payload": payload}


def _bench(variant="v1", **extra):
    leading_indicators = {}
    observation = extra.get("perf_observation")
    if isinstance(observation, Mapping) and observation.get("use_perf") is False:
        leading_indicators = {"llc_miss_rate": None, "ipc": None}
        extra.setdefault("run_cmd", "./benchmark")
    return _record("bench_done", variant, tps=[1.0], median_tps=1.0, cv=0.0,
                   rounds=1, leading_indicators=leading_indicators, **extra)


def _perf_observation(
        *, available=False, missing=(), unavailable_reason="perf-not-found"):
    if available:
        def runner(argv, **_kwargs):
            Path(argv[argv.index("-o") + 1]).write_text(
                "1,,LLC-load-misses,0,100.00,,\n"
                "2,,LLC-loads,0,100.00,,\n"
                "3,,instructions,0,100.00,,\n"
                "4,,cycles,0,100.00,,\n",
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=0, stdout="", stderr="")
    elif unavailable_reason == "nonzero-rc":
        def runner(*_args, **_kwargs):
            return SimpleNamespace(returncode=2, stdout="", stderr="denied")
    elif unavailable_reason == "requested-events-missing":
        def runner(argv, **_kwargs):
            Path(argv[argv.index("-o") + 1]).write_text(
                "4,,cycles,0,100.00,,\n", encoding="utf-8",
            )
            return SimpleNamespace(returncode=0, stdout="", stderr="")
    else:
        if unavailable_reason != "perf-not-found":
            raise ValueError("unknown unavailable perf fixture reason")

        def runner(*_args, **_kwargs):
            raise FileNotFoundError("fixture perf not found")

    receipt = perf_preflight.probe_perf_availability(
        perf_candidates=("/opt/perf",), subprocess_runner=runner,
    )
    use_perf = perf_preflight.use_perf_from_receipt(receipt)
    missing_indicators = list(missing)
    observation = {
        "use_perf": use_perf,
        "counter_status": (
            "not_required" if not use_perf
            else "incomplete" if missing_indicators
            else "complete"
        ),
        "missing_leading_indicators": missing_indicators,
        "preflight": receipt,
    }
    if not use_perf:
        observation["claim_scope"] = {
            "throughput": "eligible",
            "perf_required": "unsupported",
        }
    return observation


def _contains_bench_payload(node: ast.AST | None) -> bool:
    return node is not None and any(
        isinstance(child, ast.Name) and child.id == "bench_payload"
        for child in ast.walk(node)
    )


def _bench_payload_subscript_key(target: ast.AST) -> str | None:
    if not (
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Name)
        and target.value.id == "bench_payload"
        and isinstance(target.slice, ast.Constant)
        and isinstance(target.slice.value, str)
    ):
        return None
    return target.slice.value


def _direct_named_call(statement: ast.stmt, name: str) -> ast.Call | None:
    if not (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == name
    ):
        return None
    return statement.value


def _is_bench_emit(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return False
    call = statement.value
    return (
        isinstance(call.func, ast.BoolOp)
        and isinstance(call.func.op, ast.Or)
        and len(call.func.values) == 2
        and isinstance(call.func.values[0], ast.Name)
        and call.func.values[0].id == "emit"
        and isinstance(call.func.values[1], ast.Attribute)
        and isinstance(call.func.values[1].value, ast.Name)
        and call.func.values[1].value.id == "wal"
        and call.func.values[1].attr == "log"
        and len(call.args) == 5
        and not call.keywords
        and isinstance(call.args[4], ast.Name)
        and call.args[4].id == "bench_payload"
    )


def _bench_payload_contract(function: ast.FunctionDef):
    """Derive the producer keys while rejecting every undeclared mutation route."""
    parents = {
        child: parent
        for parent in ast.walk(function)
        for child in ast.iter_child_nodes(parent)
    }

    def ancestors(node: ast.AST):
        current = parents.get(node)
        while current is not None and current is not function:
            yield current
            current = parents.get(current)

    def direct_top_level_if(node: ast.AST) -> ast.If | None:
        parent = parents.get(node)
        if not isinstance(parent, ast.If) or parent not in function.body:
            return None
        return parent

    forbidden_control = tuple(
        node_type
        for node_type in (
            ast.Try,
            getattr(ast, "TryStar", None),
            ast.With,
            ast.AsyncWith,
            ast.For,
            ast.AsyncFor,
            ast.While,
        )
        if node_type is not None
    )
    unconditional: set[str] = set()
    conditional: set[str] = set()
    initializations: list[ast.Assign] = []
    extra_routes: list[str] = []

    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            name_targets = [
                target for target in node.targets
                if isinstance(target, ast.Name) and target.id == "bench_payload"
            ]
            if name_targets:
                assert len(node.targets) == 1 and len(name_targets) == 1
                assert node in function.body
                assert isinstance(node.value, ast.Dict)
                assert all(
                    isinstance(key, ast.Constant) and isinstance(key.value, str)
                    for key in node.value.keys
                ), "bench_payload の ** 展開は禁止"
                initializations.append(node)
                unconditional.update(key.value for key in node.value.keys)
                continue

            if _contains_bench_payload(node.value):
                raise AssertionError("bench_payload の alias または再束縛は禁止")
            for target in node.targets:
                key = _bench_payload_subscript_key(target)
                if key is None:
                    assert not _contains_bench_payload(target), (
                        "bench_payload の非 literal target mutation は禁止"
                    )
                    continue
                assert not any(
                    isinstance(parent, forbidden_control) for parent in ancestors(node)
                ), "try/with/for/while 内の payload mutation は禁止"
                enclosing_if = direct_top_level_if(node)
                assert node in function.body or enclosing_if is not None
                (conditional if enclosing_if is not None else unconditional).add(key)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            if _contains_bench_payload(node):
                raise AssertionError("bench_payload の AnnAssign/AugAssign/NamedExpr は禁止")
        elif isinstance(node, ast.Delete) and _contains_bench_payload(node):
            raise AssertionError("bench_payload key の削除は禁止")
        elif isinstance(node, forbidden_control) and _contains_bench_payload(node):
            raise AssertionError(
                "try/with/for/while を介した payload mutation/alias は禁止"
            )

    assert len(initializations) == 1

    extra_guards: list[ast.Call] = []
    final_guards: list[ast.Call] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "bench_payload"
        ):
            assert node.func.attr == "update", "update 以外の payload mutator は禁止"
            assert (
                len(node.args) == 1
                and not node.keywords
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "bench_payload_extra"
            ), "payload update は exact extra route だけを許可"
            statement = parents.get(node)
            assert isinstance(statement, ast.Expr)
            enclosing_if = direct_top_level_if(statement)
            assert enclosing_if is not None
            assert statement in enclosing_if.body
            assert enclosing_if.body.index(statement) == 1
            extra_guard = _direct_named_call(
                enclosing_if.body[0], "_assert_bench_payload_extra_keys"
            )
            assert extra_guard is not None
            assert len(extra_guard.args) == 2 and not extra_guard.keywords
            assert [
                argument.id if isinstance(argument, ast.Name) else None
                for argument in extra_guard.args
            ] == ["bench_payload", "bench_payload_extra"]
            extra_routes.append(node.args[0].id)
            continue

        if not any(_contains_bench_payload(arg) for arg in node.args) and not any(
            _contains_bench_payload(keyword.value) for keyword in node.keywords
        ):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in {
            "_assert_bench_payload_extra_keys",
            "_assert_bench_done_payload_keys",
        }:
            statement = parents.get(node)
            assert isinstance(statement, ast.Expr)
            assert not node.keywords
            if node.func.id == "_assert_bench_payload_extra_keys":
                assert [
                    argument.id if isinstance(argument, ast.Name) else None
                    for argument in node.args
                ] == ["bench_payload", "bench_payload_extra"]
                enclosing_if = direct_top_level_if(statement)
                assert enclosing_if is not None and enclosing_if.body[0] is statement
                extra_guards.append(node)
            else:
                assert [
                    argument.id if isinstance(argument, ast.Name) else None
                    for argument in node.args
                ] == ["bench_payload"]
                assert statement in function.body
                final_guards.append(node)
            continue
        statement = parents.get(node)
        assert isinstance(statement, ast.Expr) and _is_bench_emit(statement), (
            "bench_payload を alias/mutator call へ渡すことは禁止"
        )

    final_guard_indexes = [
        index for index, statement in enumerate(function.body)
        if _direct_named_call(statement, "_assert_bench_done_payload_keys") is not None
    ]
    assert len(extra_guards) == 1
    assert len(final_guards) == 1
    emit_indexes = [
        index for index, statement in enumerate(function.body)
        if _is_bench_emit(statement)
    ]
    assert len(final_guard_indexes) == 1
    assert emit_indexes == [final_guard_indexes[0] + 1], (
        "final payload guard と emit は同一 block で隣接しなければならない"
    )
    return unconditional, conditional, extra_routes


def _bench_run_schema():
    schema = json.loads(
        (ROOT / "orchestrator/campaign/layer3_schema.json").read_text(
            encoding="utf-8",
        )
    )
    run_schema = dict(schema["properties"]["runs"]["items"])
    run_schema["definitions"] = schema["definitions"]
    return run_schema


def _screening_disabled_payload(**extra):
    payload = {
        "reason": "stale-baseline",
        "age_s": 1900.0,
        "threshold_s": 1800.0,
        "baseline_ref": "baseline.json",
    }
    payload.update(extra)
    return payload


_LEGACY_BENCH_PAYLOAD_KEYS = frozenset({
    "build_attempt_id", "median_tps", "cv", "bench_wall_s", "high_variance",
    "unstable", "rounds", "cv_history", "tps", "settled", "leading_indicators",
    "rep_notes", "run_cmd", "perf_observation", "screening", "rep_returncodes",
    "screening_disabled",
})


def test_run_bench_ast_assignments_exactly_match_declared_payload_keys():
    """Close only pipeline._run_bench; guided.py's producer stays out of scope."""
    source = textwrap.dedent(inspect.getsource(pipeline._run_bench))
    function = ast.parse(source).body[0]
    assert isinstance(function, ast.FunctionDef)
    unconditional, conditional, extra_routes = _bench_payload_contract(function)

    assert unconditional == pipeline._BENCH_DONE_REQUIRED_PAYLOAD_KEYS
    assert conditional == pipeline._BENCH_DONE_CONDITIONAL_PAYLOAD_KEYS
    assert extra_routes == ["bench_payload_extra"]
    assert len(unconditional) == 13
    assert len(conditional) == 4
    assert pipeline._BENCH_PAYLOAD_EXTRA_KEYS == {"screening_disabled"}
    assert pipeline._BENCH_DONE_PAYLOAD_KEYS == _LEGACY_BENCH_PAYLOAD_KEYS | {"reps"}
    assert pipeline._BENCH_DONE_PAYLOAD_KEYS == (
        unconditional
        | conditional
        | pipeline._BENCH_PAYLOAD_EXTRA_KEYS
    )


@pytest.mark.parametrize(
    "bypass",
    [
        "post-guard-update",
        "setdefault",
        "alias",
        "augassign",
        "annassign",
        "dict-unpack",
        "try",
        "with",
        "for-alias",
        "while",
        "guard-emit-control-block",
    ],
)
def test_run_bench_ast_contract_rejects_known_bypass_routes(bypass):
    source = textwrap.dedent(inspect.getsource(pipeline._run_bench))
    guard = "    _assert_bench_done_payload_keys(bench_payload)\n"
    emit = (
        "    (emit or wal.log)(layout, variant, STAGE_BENCH_DONE, env_tag, "
        "bench_payload)\n"
    )
    assert source.count(guard) == 1
    assert source.count(emit) == 1

    before_guard = {
        "setdefault": 'bench_payload.setdefault("unknown", True)',
        "alias": 'alias = bench_payload\nalias["unknown"] = True',
        "augassign": 'bench_payload |= {"unknown": True}',
        "annassign": 'bench_payload: dict = bench_payload',
        "try": (
            'try:\n    bench_payload["unknown"] = True\n'
            'finally:\n    pass'
        ),
        "with": (
            'with nullcontext():\n    bench_payload["unknown"] = True'
        ),
        "for-alias": (
            'for alias in (bench_payload,):\n    alias["unknown"] = True'
        ),
        "while": (
            'while False:\n    bench_payload["unknown"] = True'
        ),
    }
    if bypass in before_guard:
        injected = textwrap.indent(before_guard[bypass] + "\n", "    ")
        source = source.replace(guard, injected + guard)
    elif bypass == "post-guard-update":
        source = source.replace(
            emit,
            '    bench_payload.update({"post_gate_unknown": True})\n' + emit,
        )
    elif bypass == "dict-unpack":
        marker = "    bench_payload = {\n"
        assert source.count(marker) == 1
        source = source.replace(marker, marker + "        **{},\n")
    else:
        assert bypass == "guard-emit-control-block"
        source = source.replace(
            guard + emit,
            "    if True:\n"
            "        _assert_bench_done_payload_keys(bench_payload)\n"
            "        (emit or wal.log)(layout, variant, STAGE_BENCH_DONE, "
            "env_tag, bench_payload)\n",
        )

    function = ast.parse(source).body[0]
    assert isinstance(function, ast.FunctionDef)
    with pytest.raises(AssertionError):
        _bench_payload_contract(function)


def test_run_bench_emits_exact_declared_payload_key_set(monkeypatch):
    point = SimpleNamespace(
        throughputs=[100.0],
        notes=[],
        run_cmd="./fixture-bench",
        leading_indicators=lambda: {"abort_rate": 0.0},
    )

    def measure_point(*_args, rep_returncodes=None, **_kwargs):
        assert rep_returncodes is not None
        rep_returncodes.append(0)
        return point

    def remeasure(measure, **_kwargs):
        measured = measure()
        assert measured is point
        return SimpleNamespace(
            point=measured,
            nf=SimpleNamespace(
                median=100.0, cv=0.01, high_variance=False,
            ),
            unstable=False,
            rounds=1,
            cv_history=[0.01],
        )

    monkeypatch.setattr(pipeline, "_require_measurement_site", lambda _what: "fixture")
    monkeypatch.setattr(pipeline, "bench_lock", lambda: nullcontext())
    monkeypatch.setattr(pipeline, "competing_bench_pids", lambda: [])
    monkeypatch.setattr(pipeline, "settle", lambda: {"settled": True})
    monkeypatch.setattr(pipeline, "measure_point", measure_point)
    monkeypatch.setattr(pipeline, "remeasure_until_stable", remeasure)
    monkeypatch.setattr(
        pipeline._perf_preflight,
        "build_perf_observation",
        lambda _receipt, **_kwargs: {"fixture": True},
    )
    emitted = []

    def abort(*_args, **_kwargs):
        raise AssertionError("successful bench fixture must not abort")

    result, bench = pipeline._run_bench(
        "/fixture/bench",
        pipeline.PerfConfig(records=1, threads=1),
        1,
        None,
        True,
        SimpleNamespace(),
        "fixture-variant",
        "fixture-env",
        abort,
        log=lambda _message: None,
        screening=True,
        bench_payload_extra={
            "screening_disabled": _screening_disabled_payload(),
        },
        bench_max_rounds=1,
        record_rep_returncodes=True,
        emit=lambda *args: emitted.append(args),
        perf_preflight_receipt={"fixture": True},
        build_attempt_id="fixture-attempt",
    )

    assert result is None
    assert bench is not None
    assert len(emitted) == 1
    assert emitted[0][2] == model.STAGE_BENCH_DONE
    assert set(emitted[0][4]) == _LEGACY_BENCH_PAYLOAD_KEYS


def test_formal_reps_are_conditional_and_rejected_by_legacy_layer3_schema():
    payload = {key: None for key in pipeline._BENCH_DONE_REQUIRED_PAYLOAD_KEYS}
    pipeline._assert_bench_done_payload_keys(payload)
    payload["reps"] = [{
        "rep_index": 0, "abort_counts_": 1, "commit_counts_": 2,
        "throughput_tps": 100,
    }]
    pipeline._assert_bench_done_payload_keys(payload)
    row = layer3_report._view_row(_bench())
    row["reps"] = payload["reps"]
    with pytest.raises(jsonschema.ValidationError) as caught:
        jsonschema.Draft7Validator(_bench_run_schema()).validate(row)
    assert caught.value.validator == "additionalProperties"


def test_bench_done_runtime_allowlist_reports_missing_and_unexpected_separately():
    payload = {
        key: None for key in pipeline._BENCH_DONE_REQUIRED_PAYLOAD_KEYS
        if key != "tps"
    }
    payload["unknown_diagnostic"] = None

    with pytest.raises(ValueError) as exc_info:
        pipeline._assert_bench_done_payload_keys(payload)

    message = str(exc_info.value)
    assert "'missing': ['tps']" in message
    assert "'unexpected': ['unknown_diagnostic']" in message


def test_bench_payload_extra_accepts_only_its_exact_key_set_without_overlap():
    pipeline._assert_bench_payload_extra_keys(
        {}, {"screening_disabled": _screening_disabled_payload()},
    )

    with pytest.raises(ValueError, match="missing"):
        pipeline._assert_bench_payload_extra_keys({}, {})

    with pytest.raises(ValueError, match="unexpected"):
        pipeline._assert_bench_payload_extra_keys(
            {},
            {
                "screening_disabled": _screening_disabled_payload(),
                "future_extra": {},
            },
        )


def test_bench_payload_extra_rejects_measurement_overwrite_before_merge():
    assembled = {"median_tps": 100.0}
    extra = {
        "screening_disabled": _screening_disabled_payload(),
        "median_tps": 0.0,
    }

    with pytest.raises(ValueError, match=r"overlap.*median_tps"):
        pipeline._assert_bench_payload_extra_keys(assembled, extra)
    assert assembled == {"median_tps": 100.0}


def test_bench_payload_extra_rejects_overlap_even_when_key_is_extra_owned():
    assembled = {"screening_disabled": _screening_disabled_payload()}

    with pytest.raises(ValueError, match=r"overlap.*screening_disabled"):
        pipeline._assert_bench_payload_extra_keys(
            assembled,
            {"screening_disabled": _screening_disabled_payload()},
        )


@pytest.mark.parametrize(
    "field",
    [
        "baseline_tps", "baseline_measured_at", "floor", "k",
        "baseline_abort_rate", "high_abort_factor", "reanchor_threshold_s",
    ],
)
def test_screening_config_rejects_bool_for_every_numeric_field(field):
    values = {
        "baseline_tps": 100.0,
        "baseline_ref": "baseline.json",
        "baseline_measured_at": 1.0,
        "floor": 0.1,
        "k": 1.5,
        "baseline_abort_rate": 0.0,
        "high_abort_factor": 2.0,
        "reanchor_threshold_s": 1800.0,
    }
    values[field] = True

    with pytest.raises(ValueError, match=field):
        pipeline.ScreeningConfig(**values)


@pytest.mark.parametrize("baseline_ref", ["", False, 1])
def test_screening_config_requires_nonempty_exact_string_baseline_ref(
    baseline_ref,
):
    with pytest.raises(ValueError, match="baseline_ref"):
        pipeline.ScreeningConfig(
            baseline_tps=100.0,
            baseline_ref=baseline_ref,
            baseline_measured_at=1.0,
            floor=0.1,
            baseline_abort_rate=0.0,
        )


def test_pipeline_bench_payload_closure_uses_real_view_row():
    """Close pipeline._run_bench only; guided.py bench_done remains out of scope."""
    payload = {
        "build_attempt_id": "attempt-1",
        "build_admission_receipt_sha256": "a" * 64,
        "median_tps": 1.0,
        "cv": 0.0,
        "bench_wall_s": 1.0,
        "high_variance": False,
        "unstable": False,
        "rounds": 1,
        "cv_history": [0.0],
        "tps": [1.0],
        "settled": True,
        "leading_indicators": {},
        "rep_notes": [],
        "run_cmd": "./benchmark",
        "perf_observation": _perf_observation(),
        "screening": True,
        "rep_returncodes": [0],
        "screening_disabled": _screening_disabled_payload(),
    }
    row = layer3_report._view_row(_record("bench_done", **payload))

    assert "build_attempt_id" not in row
    assert "build_admission_receipt_sha256" not in row
    assert set(row) == (
        (_LEGACY_BENCH_PAYLOAD_KEYS - {"build_attempt_id"})
        | {"variant", "source_ref"}
    )
    assert set(row) == set(_bench_run_schema()["properties"])


@pytest.mark.parametrize("settled", [True, False, None])
def test_settled_accepts_exact_forensic_value_domain(settled):
    row = layer3_report._view_row(_bench(settled=settled))

    jsonschema.Draft7Validator(_bench_run_schema()).validate(row)


@pytest.mark.parametrize("settled", ["unknown", 0, {}])
def test_settled_rejects_values_outside_exact_forensic_domain(settled):
    row = layer3_report._view_row(_bench(settled=settled))

    with pytest.raises(jsonschema.ValidationError) as caught:
        jsonschema.Draft7Validator(_bench_run_schema()).validate(row)
    assert caught.value.validator == "type"
    assert list(caught.value.absolute_path) == ["settled"]


def test_named_screening_artifact_builds_layer3_report_end_to_end():
    report = layer3_report.build_report(
        REAL_SCREENING_CAMPAIGN,
        generated_from_head="fixed",
        output_root=ROOT / "output",
    )

    assert any(
        run.get("screening") is True and run.get("settled") is None
        for run in report["runs"]
    )


def test_named_screening_abort_preserves_complete_screen_payload():
    records = [
        json.loads(line)
        for line in (REAL_SCREENING_CAMPAIGN / "runs/wal.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
        if line.strip()
    ]
    events = [
        event for event in records
        if event["variant"] == "610e879931c4" and event["stage"] == "abort"
    ]
    assert len(events) == 1
    event = events[0]
    report = layer3_report.build_report(
        REAL_SCREENING_CAMPAIGN,
        generated_from_head="fixed",
        output_root=ROOT / "output",
    )
    rows = [
        row for row in report["aborts"] if row["variant"] == event["variant"]
    ]

    assert len(rows) == 1
    assert set(event["payload"]["screen"]) == {
        "median_tps", "cv", "baseline_tps", "baseline_ref", "floor", "k", "margin",
    }
    assert rows[0]["screen"] == event["payload"]["screen"]
    assert rows[0]["reason"] == "screen-slower-than-floor"
    assert rows[0]["source_ref"] == layer3_report.canonical_record_ref("wal", event)


def test_screening_abort_variant_is_listed_in_rejects(tmp_path):
    screen = {
        "median_tps": 1912074.0,
        "cv": 0.009266208528432952,
        "baseline_tps": 8470959.0,
        "baseline_ref": "84319b1127a6",
        "floor": 0.0010979692594382789,
        "k": 1.5,
        "margin": -0.7742789216663662,
    }
    start = _record("build_start", "screened", genome="g", src_token="s")
    bench = _bench("screened", screening=True, settled=None)
    abort = _record(
        "abort", "screened", reason="screen-slower-than-floor", screen=screen,
    )
    start["ts"], bench["ts"], abort["ts"] = 1.0, 2.0, 3.0
    campaign, output_root = _campaign(tmp_path, [start, bench, abort])
    records = [
        json.loads(line)
        for line in (campaign / "runs/wal.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
        if line.strip()
    ]
    abort_event, = [event for event in records if event["stage"] == "abort"]
    assert not any(
        event["variant"] == abort_event["variant"] and event["stage"] == "commit"
        for event in records
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert [
        row for row in report["rejects"]
        if row["variant"] == abort_event["variant"]
    ] == [{
        "variant": abort_event["variant"],
        "reason": "commit-event-absent",
        "source_ref": layer3_report.canonical_record_ref("wal", abort_event),
    }]


def test_screening_abort_participates_in_input_ref_multiset(tmp_path):
    screen = {
        "median_tps": 1912074.0,
        "cv": 0.009266208528432952,
        "baseline_tps": 8470959.0,
        "baseline_ref": "84319b1127a6",
        "floor": 0.0010979692594382789,
        "k": 1.5,
        "margin": -0.7742789216663662,
    }
    start = _record("build_start", "screened", genome="g", src_token="s")
    bench = _bench("screened", screening=True, settled=None)
    abort = _record(
        "abort", "screened", reason="screen-slower-than-floor", screen=screen,
    )
    start["ts"], bench["ts"], abort["ts"] = 1.0, 2.0, 3.0
    campaign, output_root = _campaign(tmp_path, [start, bench, abort])
    records = [
        json.loads(line)
        for line in (campaign / "runs/wal.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
        if line.strip()
    ]
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    expected = Counter(
        layer3_report.canonical_record_ref("wal", event) for event in records
    )
    abort_event, = [event for event in records if event["stage"] == "abort"]
    abort_ref = layer3_report.canonical_record_ref("wal", abort_event)

    assert expected[abort_ref] == 1
    assert Counter(report["source_refs"]) == expected
    assert layer3_report._report_primary_refs(report) == expected
    layer3_report._assert_bijection(records, [], report)


def test_screening_abort_primary_mutation_fails_bijection_at_equal_count(tmp_path):
    screen = {
        "median_tps": 1912074.0,
        "cv": 0.009266208528432952,
        "baseline_tps": 8470959.0,
        "baseline_ref": "84319b1127a6",
        "floor": 0.0010979692594382789,
        "k": 1.5,
        "margin": -0.7742789216663662,
    }
    start = _record("build_start", "screened", genome="g", src_token="s")
    bench = _bench("screened", screening=True, settled=None)
    abort = _record(
        "abort", "screened", reason="screen-slower-than-floor", screen=screen,
    )
    start["ts"], bench["ts"], abort["ts"] = 1.0, 2.0, 3.0
    campaign, output_root = _campaign(tmp_path, [start, bench, abort])
    records = [
        json.loads(line)
        for line in (campaign / "runs/wal.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
        if line.strip()
    ]
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    layer3_report._assert_bijection(records, [], report)
    mutated = json.loads(json.dumps(report))
    abort_events = [
        event for row in mutated["variants"] for event in row["events"]
        if event["stage"] == "abort"
    ]
    assert len(abort_events) == 1
    abort_events[0]["ts"] += 1.0
    assert sum(len(row["events"]) for row in mutated["variants"]) == sum(
        len(row["events"]) for row in report["variants"]
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="source-ref multiset が入力 WAL/whiteboard と report 本体で一致しない",
    ):
        layer3_report._assert_bijection(records, [], mutated)
    layer3_report._assert_bijection(records, [], report)


def test_screening_abort_without_verify_done_builds_without_verification(tmp_path):
    screen = {
        "median_tps": 1912074.0,
        "cv": 0.009266208528432952,
        "baseline_tps": 8470959.0,
        "baseline_ref": "84319b1127a6",
        "floor": 0.0010979692594382789,
        "k": 1.5,
        "margin": -0.7742789216663662,
    }
    start = _record("build_start", "screened", genome="g", src_token="s")
    bench = _bench("screened", screening=True, settled=None)
    abort = _record(
        "abort", "screened", reason="screen-slower-than-floor", screen=screen,
    )
    start["ts"], bench["ts"], abort["ts"] = 1.0, 2.0, 3.0
    campaign, output_root = _campaign(tmp_path, [start, bench, abort])
    records = [
        json.loads(line)
        for line in (campaign / "runs/wal.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
        if line.strip()
    ]
    abort_event, = [event for event in records if event["stage"] == "abort"]
    variant = abort_event["variant"]
    assert not any(
        event["variant"] == variant and event["stage"] == "verify_done"
        for event in records
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    runs = [row for row in report["runs"] if row["variant"] == variant]
    assert len(runs) == 1
    assert runs[0]["screening"] is True
    assert runs[0]["settled"] is None
    assert not any(row["variant"] == variant for row in report["verifications"])
    layer3_report._validate_schema(report)


def test_historical_v1_run_row_without_screening_fields_remains_valid():
    """Pin only the v1 runs-item shape, not full-v1 report readability."""
    event = _bench(
        build_attempt_id="attempt-1",
        build_admission_receipt_sha256="a" * 64,
    )
    row = layer3_report._view_row(event)

    assert "screening" not in row
    assert "screening_disabled" not in row
    jsonschema.Draft7Validator(_bench_run_schema()).validate(row)


def test_v2_and_v3_reports_with_legacy_run_without_screening_remain_valid(
    tmp_path,
):
    campaign, output_root = _campaign(tmp_path, [_bench()])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert len(report["runs"]) == 1
    assert "screening" not in report["runs"][0]
    assert "screening_disabled" not in report["runs"][0]
    layer3_report._validate_schema(report)

    report["schema_version"] = "layer3-material-report/v2"
    del report["knowledge_provenance"]
    del report["admission_decision"]
    del report["acceptance_receipt"]
    del report["certifying_input"]
    layer3_report._validate_schema(report)


def test_v2_report_rejects_invalid_screening_value_with_legacy_schema():
    report = layer3_report.build_report(
        REAL_SCREENING_CAMPAIGN,
        generated_from_head="fixed",
        output_root=ROOT / "output",
    )
    report["schema_version"] = "layer3-material-report/v2"
    del report["knowledge_provenance"]
    del report["admission_decision"]
    del report["acceptance_receipt"]
    del report["certifying_input"]
    report["runs"][0]["screening"] = False

    with pytest.raises(layer3_report.Layer3ReportError) as caught:
        layer3_report._validate_schema(report)
    cause = caught.value.__cause__
    assert isinstance(cause, jsonschema.ValidationError)
    assert cause.validator == "const"
    assert list(cause.absolute_path) == ["runs", 0, "screening"]


@pytest.mark.parametrize(
    "new_fields",
    [
        {"screening": True},
        {"screening_disabled": _screening_disabled_payload()},
    ],
)
def test_new_screening_fields_pass_real_view_and_run_schema(
    tmp_path, new_fields,
):
    campaign, output_root = _campaign(
        tmp_path, [_bench(**new_fields)],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert len(report["runs"]) == 1
    for key, value in new_fields.items():
        assert report["runs"][0][key] == value


def test_screening_and_screening_disabled_are_mutually_exclusive():
    row = layer3_report._view_row(_bench(
        build_attempt_id="attempt-1",
        build_admission_receipt_sha256="a" * 64,
        screening=True,
        screening_disabled=_screening_disabled_payload(),
    ))

    with pytest.raises(jsonschema.ValidationError) as caught:
        jsonschema.Draft7Validator(_bench_run_schema()).validate(row)
    assert caught.value.validator == "not"
    assert list(caught.value.absolute_path) == []


def test_screening_disabled_rejects_nested_unknown_key():
    row = layer3_report._view_row(_bench(
        build_attempt_id="attempt-1",
        build_admission_receipt_sha256="a" * 64,
        screening_disabled=_screening_disabled_payload(unknown=True),
    ))

    with pytest.raises(jsonschema.ValidationError) as caught:
        jsonschema.Draft7Validator(_bench_run_schema()).validate(row)
    assert caught.value.validator == "additionalProperties"
    assert list(caught.value.absolute_path) == ["screening_disabled"]


def test_screening_disabled_rejects_non_stale_baseline_reason():
    row = layer3_report._view_row(_bench(
        build_attempt_id="attempt-1",
        build_admission_receipt_sha256="a" * 64,
        screening_disabled=_screening_disabled_payload(
            reason="something-else",
        ),
    ))

    with pytest.raises(jsonschema.ValidationError) as caught:
        jsonschema.Draft7Validator(_bench_run_schema()).validate(row)
    assert caught.value.validator == "const"
    assert list(caught.value.absolute_path) == [
        "screening_disabled", "reason",
    ]


@pytest.mark.parametrize(
    "new_fields, expected_validator, expected_absolute_path",
    [
        ({"screening": False}, "const", ["screening"]),
        (
            {"screening_disabled": _screening_disabled_payload(baseline_ref="")},
            "minLength",
            ["screening_disabled", "baseline_ref"],
        ),
        (
            {"screening_disabled": _screening_disabled_payload(age_s=True)},
            "type",
            ["screening_disabled", "age_s"],
        ),
        (
            {"screening_disabled": _screening_disabled_payload(threshold_s=True)},
            "type",
            ["screening_disabled", "threshold_s"],
        ),
        (
            {
                "screening_disabled": {
                    "age_s": 1900.0,
                    "threshold_s": 1800.0,
                    "baseline_ref": "baseline.json",
                },
            },
            "required",
            ["screening_disabled"],
        ),
    ],
)
def test_screening_fields_reject_nonproducer_values(
    new_fields, expected_validator, expected_absolute_path,
):
    row = layer3_report._view_row(_bench(**new_fields))

    with pytest.raises(jsonschema.ValidationError) as caught:
        jsonschema.Draft7Validator(_bench_run_schema()).validate(row)
    assert caught.value.validator == expected_validator
    assert list(caught.value.absolute_path) == expected_absolute_path


def test_layer3_schema_version_and_run_required_keys_remain_frozen():
    schema = json.loads(
        (ROOT / "orchestrator/campaign/layer3_schema.json").read_text(
            encoding="utf-8",
        )
    )

    assert schema["properties"]["schema_version"] == {
        "const": "layer3-material-report/v3",
    }
    assert schema["properties"]["runs"]["items"]["required"] == [
        "variant", "source_ref", "tps", "median_tps", "cv", "rounds",
        "leading_indicators",
    ]
    screening_disabled = schema["properties"]["runs"]["items"][
        "properties"
    ]["screening_disabled"]
    assert screening_disabled["additionalProperties"] is False
    assert screening_disabled["required"] == [
        "reason", "age_s", "threshold_s", "baseline_ref",
    ]


def test_real_legacy_s8a_campaign_is_rejected(tmp_path):
    out = tmp_path / "report.json"
    with pytest.raises(layer3_report.Layer3ReportError, match="legacy-unclassified"):
        layer3_report.render(REAL_CAMPAIGN, out, generated_from_head="fixed-head")
    assert not out.exists()


def test_legacy_trigger_sweep_cannot_issue_new_report(tmp_path):
    out = tmp_path / "report.json"
    with pytest.raises(layer3_report.Layer3ReportError, match="legacy-unclassified"):
        layer3_report.render(
            LEGACY_TRIGGER_SWEEP_CAMPAIGN,
            out,
            generated_from_head="fixed-head",
        )
    assert not out.exists()


def test_campaign_without_loop_state_has_empty_absent_whiteboard(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], loop_state=False)
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["whiteboard"] == []
    assert report["whiteboard_provenance"] == "absent"
    assert not any(ref.startswith("wb:") for ref in report["source_refs"])
    assert report["schema_version"] == "layer3-material-report/v3"
    assert report["acceptance_receipt"] is None
    assert report["certifying_input"] is False
    decision = report["admission_decision"]
    assert decision["classification"] == "admitted-new-schema"
    assert decision["admission_status"] == "admitted"
    assert decision["overlay"]["record_key"] is None


def test_historical_build_report_remains_non_certifying(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    historical = _historical_admitted_campaign(campaign)
    monkeypatch.setattr(
        layer3_report, "require_admitted_campaign",
        lambda _path, *, purpose: historical,
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["admission_decision"]["admission_status"] == (
        "historical-not-reclassified"
    )
    assert report["acceptance_receipt"] is None
    assert report["certifying_input"] is False


def test_historical_build_report_projects_unknown_current_verifier_conformance(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["current_verifier_conformance"] == "unknown"


@pytest.mark.parametrize("grammar", [85, 63, 62, 24])
def test_historical_exact_grammar_build_report(tmp_path, monkeypatch, grammar):
    campaign = _historical_exact_grammar_campaign(tmp_path, monkeypatch, grammar)
    paths = [campaign / "campaign.lock", campaign / "runs/wal.jsonl"]
    before = [path.read_bytes() for path in paths]

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=tmp_path,
    )

    assert report["certifying_input"] is False
    assert report["acceptance_receipt"] is None
    assert report["current_verifier_conformance"] == "unknown"
    epoch = report["campaign_verifier_epoch"]
    assert epoch["state"] == "E1"
    assert epoch["reason_code"] == "recorded-closure"
    # exact-24 was observed through real HISTORICAL_RAW admission of this fixture.
    expected_epochs = {
        85: "E1:bc8a6c8c6fd792ab6f21f22107f5313fb64ef0be1d6f8c97a15065998c423dc7",
        63: "E1:73f334f62ec13c394aae3d4787b80117562187984b6e0e372f2c0f7058b8ced2",
        62: "E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9",
        24: "E1:e1e397737e509b550482d3e815bcb69b87c0b5c42f6ac7feb6fccb657856cfc7",
    }
    assert epoch["campaign_verifier_epoch"] == expected_epochs[grammar]
    assert report["workload"]["records"] == 1
    assert report["workload"]["threads"] == 1
    assert [path.read_bytes() for path in paths] == before
    layer3_report._validate_schema(report)


@pytest.mark.parametrize("grammar", [85, 63, 62, 24])
def test_accepted_report_rejects_historical_exact_grammar_at_lock(
    tmp_path, monkeypatch, grammar,
):
    campaign = _historical_exact_grammar_campaign(tmp_path, monkeypatch, grammar)
    verified = _certifying_receipt_for(campaign)
    verified.trials[0].trial_id = "test"
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt", lambda _receipt: verified,
    )
    before = {path for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(layer3_report.Layer3ReportError) as caught:
        layer3_report.build_accepted_report(
            campaign, acceptance_receipt=object(),
            generated_from_head="fixed", output_root=tmp_path,
        )
    assert str(caught.value) == "campaign.lock schema が不正"
    assert type(caught.value.__cause__) is campaign_lock.CampaignLockCodecError
    assert {path for path in tmp_path.rglob("*") if path.is_file()} == before


def test_read_campaign_lock_requires_purpose(tmp_path):
    campaign, _ = _campaign(tmp_path, [])
    with pytest.raises(TypeError):
        layer3_report._read_campaign_lock(campaign / "campaign.lock")


def test_read_campaign_lock_rejects_non_exact_purpose(tmp_path):
    class S(str):
        pass

    class OtherPurpose(str, Enum):
        HISTORICAL_RAW = "HISTORICAL_RAW"
        CERTIFIED_ACCEPTANCE = "CERTIFIED_ACCEPTANCE"

    campaign, _ = _campaign(tmp_path, [])
    for path in (campaign / "campaign.lock", tmp_path / "missing.lock"):
        for value in (
            "HISTORICAL_RAW", "CERTIFIED_ACCEPTANCE",
            S("HISTORICAL_RAW"), S("CERTIFIED_ACCEPTANCE"),
            OtherPurpose.HISTORICAL_RAW, OtherPurpose.CERTIFIED_ACCEPTANCE,
        ):
            with pytest.raises(TypeError) as caught:
                layer3_report._read_campaign_lock(path, purpose=value)
            assert str(caught.value) == (
                "purpose は exact CampaignReadPurpose.CERTIFIED_ACCEPTANCE "
                "または HISTORICAL_RAW が必要"
            )


@pytest.mark.parametrize("grammar", [96, "v1"])
@pytest.mark.parametrize("purpose", list(layer3_report.CampaignReadPurpose))
def test_read_campaign_lock_current_and_v1_by_purpose(tmp_path, grammar, purpose):
    identity = {
        "ccbench_commit": "fixed", "search_config": {"records": 1, "threads": 2},
        "search_tag": "fixture", "spec_content": "fixture", "trial": "fixture",
    }
    text = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    if grammar == 96:
        text = build_v2_campaign_lock(text)
    path = tmp_path / "campaign.lock"
    path.write_text(text, encoding="utf-8")
    result = layer3_report._read_campaign_lock(path, purpose=purpose)
    expected_type = (
        campaign_lock.DecodedHistoricalCampaignLock
        if purpose is layer3_report.CampaignReadPurpose.HISTORICAL_RAW
        else campaign_lock.DecodedCampaignLock
    )
    assert type(result) is expected_type
    assert result.identity == identity
    canonical_member = layer3_report.CampaignReadPurpose("HISTORICAL_RAW")
    positive = layer3_report._read_campaign_lock(path, purpose=canonical_member)
    assert type(positive) is campaign_lock.DecodedHistoricalCampaignLock
    assert positive.identity == identity


@pytest.mark.parametrize("grammar", [85, 63, 62, 24])
def test_historical_exact_grammar_uses_authority_head_fallback(
    tmp_path, monkeypatch, grammar,
):
    campaign = _historical_exact_grammar_campaign(tmp_path, monkeypatch, grammar)
    _assert_external_campaign_without_git_head(campaign)
    recorded = layer3_report._read_campaign_lock(
        campaign / "campaign.lock",
        purpose=layer3_report.CampaignReadPurpose.HISTORICAL_RAW,
    )
    report = layer3_report.build_report(campaign, output_root=tmp_path)
    assert report["meta"]["generated_from_head"] == recorded.authority.contract_loader_commit
    # Exercise the real reader and fallback with a fixed recorded authority.
    # A fictitious Git commit cannot be admitted by the real blob verifier.
    expected = "b" * 40
    path = campaign / "campaign.lock"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["authority"]["contract_loader_commit"] = expected
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    decoded = layer3_report._read_campaign_lock(
        path, purpose=layer3_report.CampaignReadPurpose.HISTORICAL_RAW,
    )
    assert layer3_report._resolve_generated_from_head(campaign, decoded, None) == expected


@pytest.mark.parametrize("grammar", [96, "v1"])
def test_material_knowledge_identity_argument_preserves_current_and_v1(
    tmp_path, grammar,
):
    campaign, _, _resolved = _knowledge_campaign(tmp_path)
    decoded = campaign_lock.decode_campaign_lock(
        (campaign / "campaign.lock").read_text(encoding="utf-8"),
    )
    if grammar == "v1":
        decoded = campaign_lock.decode_campaign_lock(decoded.identity_preimage)
    layout = CampaignLayout(root=str(campaign))
    records = wal.read_records(layout)
    helper = wal.knowledge_provenance_and_receipt_sha256_for_material_report
    object_result = helper(layout, records, campaign_lock=decoded)
    identity_result = helper(layout, records, campaign_lock=decoded.identity)
    assert object_result is not None
    assert identity_result == object_result
    assert object_result[1] == hashlib.sha256(
        (campaign / knowledge_manifest.RECEIPT_FILENAME).read_bytes(),
    ).hexdigest()

    # Both representations must reject a one-sided knowledge binding identically.
    identity = json.loads(json.dumps(decoded.identity))
    del identity["search_config"]["knowledge_manifest_sha256"]
    invalid_object = dataclasses.replace(decoded, identity=identity)
    errors = []
    for lock_value in (invalid_object, identity):
        with pytest.raises(wal.AttemptTopologyError) as caught:
            helper(layout, records, campaign_lock=lock_value)
        assert type(caught.value) is wal.AttemptTopologyError
        errors.append(str(caught.value))
    assert errors[0] == errors[1]


def test_historical_policy_version_report_schema(tmp_path, monkeypatch):
    from orchestrator.campaign import build_admission as B
    from orchestrator.tests import test_artifact_admission as support

    repo = support._committed_closure_repo(tmp_path)
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)
    with monkeypatch.context() as issuing:
        issuing.setattr(B, "CURRENT_PIN", "d706650")
        issuing.setattr(support, "CURRENT_PIN", "d706650")
        issuing.setattr(support.receipt_support, "CURRENT_PIN", "d706650")
        # Recreate the cached proof policy only for this campaign's issuance.
        issuing.setattr(
            support.receipt_support, "_PROOF_BUILD_CONTEXT",
            B.build_run_context(generator_id=B.GeneratorId.BACKOFF_SWEEP),
        )
        campaign = support._new_schema_campaign(tmp_path / "recorded")
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=tmp_path,
    )
    assert report["admission_decision"]["classification"] == "historical-policy-version"
    assert report["admission_decision"]["admission_status"] == "historical-not-reclassified"
    assert report["current_verifier_conformance"] == "unknown"
    assert report["certifying_input"] is False
    layer3_report._validate_schema(report)

    # Isolate classification from every other historical marker.
    report.pop("current_verifier_conformance")
    report.pop("campaign_verifier_epoch", None)
    report["admission_decision"]["admission_status"] = "admitted"
    report["acceptance_receipt"] = {"path": "acceptance/test.json", "sha256": "a" * 64}
    report["certifying_input"] = True
    report["admission_decision"]["classification"] = "admitted-new-schema"
    layer3_report._validate_schema(report)
    report["admission_decision"]["classification"] = "historical-policy-version"
    with pytest.raises(layer3_report.Layer3ReportError, match="layer3 schema 検証に失敗$"):
        layer3_report._validate_schema(report)


def test_historical_build_report_displays_e0_without_rejection(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    historical = _historical_admitted_campaign(campaign)
    e0 = artifact_admission.CampaignVerifierEpoch(
        campaign_verifier_epoch="E0",
        state="E0",
        reason_code="v1-authority-absent",
    )
    historical_e0 = dataclasses.replace(
        historical,
        campaign_verifier_epoch=e0,
    )

    def historical_only(_path, *, purpose):
        assert purpose is layer3_report.CampaignReadPurpose.HISTORICAL_RAW
        return historical_e0

    monkeypatch.setattr(
        layer3_report, "require_admitted_campaign", historical_only,
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["campaign_verifier_epoch"] == {
        "campaign_verifier_epoch": "E0",
        "state": "E0",
        "reason_code": "v1-authority-absent",
        "identity_scope": e0.identity_scope,
        "excluded_scope": e0.excluded_scope,
        "verifier_assessment_basis": (
            "recorded-at-original-verifier-epoch"
        ),
    }
    assert report["certifying_input"] is False


def test_historical_layer3_schema_accepts_legacy_recorded_current_closure_mismatch(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["campaign_verifier_epoch"] = {
        "campaign_verifier_epoch": f"E1:{'a' * 64}",
        "state": "E1-stale",
        "reason_code": "recorded-current-closure-mismatch",
        "identity_scope": "legacy recorded identity scope",
        "excluded_scope": "legacy recorded excluded scope",
    }

    layer3_report._validate_schema(report)


def test_v2_lock_projects_only_inner_identity_without_authority_or_new_source_refs(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    admitted = layer3_report.require_admitted_campaign(
        campaign,
        purpose=layer3_report.CampaignReadPurpose.HISTORICAL_RAW,
    )
    baseline_report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    lock_path = campaign / "campaign.lock"
    identity_preimage = campaign_lock.decode_campaign_lock(
        lock_path.read_text(encoding="utf-8")
    ).identity_preimage
    v2_text = build_v2_campaign_lock(
        identity_preimage,
        authorization=env_contract.authorize("linux-baremetal"),
    )
    lock_path.write_text(v2_text, encoding="utf-8")
    v2_admitted = dataclasses.replace(
        admitted,
        decision=dataclasses.replace(
            admitted.decision,
            campaign_lock_sha256=hashlib.sha256(v2_text.encode("utf-8")).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        layer3_report, "require_admitted_campaign",
        lambda _path, *, purpose: v2_admitted,
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["schema_version"] == "layer3-material-report/v3"
    assert report["workload"] == baseline_report["workload"]
    assert report["meta"]["ccbench_commit"] == (
        baseline_report["meta"]["ccbench_commit"]
    )
    assert report["source_refs"] == baseline_report["source_refs"]
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True)
    assert '"authority"' not in rendered
    assert '"environment_contract_sha256"' not in rendered


def test_report_records_present_policy_hint_at_top_level_and_workload(tmp_path):
    hint = "prefer stable behavior; do not infer a winner"
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
        policy_hint=hint,
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["policy_hint"] == hint
    assert report["workload"]["policy_hint"] == hint


def test_report_uses_null_for_absent_policy_hint(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["policy_hint"] is None
    assert "policy_hint" not in report["workload"]


def test_nonknowledge_report_emits_null_knowledge_provenance(tmp_path):
    """Fails only when the producer omits or populates the nonknowledge field."""
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert "knowledge_provenance" in report
    assert report["knowledge_provenance"] is None


def test_knowledge_report_projects_verified_receipt_sources(tmp_path):
    """M1: fails only when a knowledge-aware report does not expose provenance."""
    campaign, output_root, resolved = _knowledge_campaign(tmp_path)

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    expected_sources = [
        item.source.canonical_value() for item in resolved.sources
    ]

    assert report["knowledge_provenance"] == {
        "knowledge_level": "K2",
        "knowledge_manifest_sha256": resolved.knowledge_manifest_sha256,
        "declared_sources": expected_sources,
        "injected_sources": expected_sources,
    }


def test_knowledge_report_projects_completed_empty_retrieval(tmp_path):
    """Rejects a report path that drops the v2 scope or retrieval result while retaining empty sources. Accepts the complete empty retrieval projection without fabricating declared or injected sources."""
    resolved = _resolved_empty_knowledge_fixture(tmp_path)
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        knowledge=resolved,
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    expected = {
        "knowledge_level": "K2",
        "knowledge_manifest_sha256": resolved.knowledge_manifest_sha256,
        "declared_scope": resolved.manifest.declared_scope.canonical_value(),
        "retrieval_result": resolved.manifest.retrieval_result.canonical_value(),
        "declared_sources": [],
        "injected_sources": [],
    }
    assert report["knowledge_provenance"] == expected

    del report["knowledge_provenance"]["retrieval_result"]
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_schema_accepts_independent_knowledge_provenance_specimen():
    """FX4/FX5 positive: the standalone exact-shape specimen is schema-valid."""
    layer3_report._validate_schema(_knowledge_schema_specimen())


def test_schema_accepts_completed_empty_knowledge_provenance_specimen():
    """Rejects the legacy four-key provenance object when either source array is empty. Accepts an independent tagged extended specimen with completed_empty, count zero, and both source arrays empty."""
    legacy = _knowledge_schema_specimen()
    legacy["knowledge_provenance"]["declared_sources"] = []
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(legacy)

    layer3_report._validate_schema(
        _completed_empty_knowledge_schema_specimen()
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "missing-scope",
        "missing-result",
        "completed-nonempty",
        "positive-empty-count",
        "only-declared-empty",
    ),
)
def test_extended_schema_rejects_empty_sources_without_completed_empty_result(
    mutation,
):
    """Rejects partial, contradictory, or one-sided empty extended provenance. Accepts the unchanged legacy nonempty shape and the complete extended completed-empty shape."""
    report = _completed_empty_knowledge_schema_specimen()
    provenance = report["knowledge_provenance"]
    if mutation == "missing-scope":
        del provenance["declared_scope"]
    elif mutation == "missing-result":
        del provenance["retrieval_result"]
    elif mutation == "completed-nonempty":
        provenance["retrieval_result"] = {
            "status": "completed_nonempty", "result_count": 1,
        }
    elif mutation == "positive-empty-count":
        provenance["retrieval_result"]["result_count"] = 1
    else:
        provenance["injected_sources"] = [
            _knowledge_schema_specimen()["knowledge_provenance"]
            ["injected_sources"][0]
        ]
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)

    layer3_report._validate_schema(_knowledge_schema_specimen())
    layer3_report._validate_schema(
        _completed_empty_knowledge_schema_specimen()
    )


def test_schema_rejects_unknown_nested_knowledge_key():
    """M3: fails only when the nested provenance object permits an unknown key."""
    report = _knowledge_schema_specimen()
    layer3_report._validate_schema(report)
    report["knowledge_provenance"]["unexpected"] = True

    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_schema_rejects_missing_injected_sources():
    """M4: fails only when injected_sources is not nested-required."""
    report = _knowledge_schema_specimen()
    layer3_report._validate_schema(report)
    del report["knowledge_provenance"]["injected_sources"]

    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


@pytest.mark.parametrize(
    "case",
    (
        "source-unknown-key",
        "identity-unknown-key",
        "empty-array",
        "duplicate-array",
    ),
)
def test_schema_rejects_invalid_knowledge_source_shapes(case):
    """FX5: each case fails only at its named existing schema constraint."""
    report = _knowledge_schema_specimen()
    layer3_report._validate_schema(report)
    provenance = report["knowledge_provenance"]
    if case == "source-unknown-key":
        provenance["declared_sources"][0]["unexpected"] = True
    elif case == "identity-unknown-key":
        provenance["declared_sources"][0]["identity"]["unexpected"] = True
    elif case == "empty-array":
        provenance["declared_sources"] = []
    else:
        duplicate = json.loads(json.dumps(provenance["injected_sources"][0]))
        provenance["injected_sources"].append(duplicate)

    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_report_rejects_receipt_replaced_after_build_start(tmp_path):
    """M7: fails only if verified WAL projection replaces the live receipt read."""
    campaign, output_root, _resolved = _knowledge_campaign(tmp_path)
    receipt_path = campaign / knowledge_manifest.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_bytes())
    receipt["knowledge_manifest_sha256"] = "0" * 64
    receipt_path.write_bytes(
        knowledge_manifest.canonical_json_bytes(receipt) + b"\n"
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="knowledge provenance 検証に失敗",
    ):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )


def test_artifact_refs_accept_validated_knowledge_receipt_digest(tmp_path):
    """FX3 positive: the real artifact scan accepts the same receipt bytes."""
    campaign, _output_root, _resolved = _knowledge_campaign(tmp_path)
    checked = (
        wal.knowledge_provenance_and_receipt_sha256_for_material_report(
            CampaignLayout(root=str(campaign)),
            wal.read_records(CampaignLayout(root=str(campaign))),
            campaign_lock=layer3_report._read_campaign_lock(
                campaign / "campaign.lock",
                purpose=layer3_report.CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
            ),
        )
    )
    assert checked is not None
    _projection, receipt_sha256 = checked

    assert {
        "path": knowledge_manifest.RECEIPT_FILENAME,
        "sha256": receipt_sha256,
    } in layer3_report._artifact_refs(
        campaign, knowledge_receipt_sha256=receipt_sha256,
    )


def test_artifact_refs_reject_receipt_changed_after_provenance_read(tmp_path):
    """FX3: only the validated-read/artifact-ref digest mismatch rejects."""
    campaign, _output_root, _resolved = _knowledge_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    records = wal.read_records(layout)
    decoded_lock = layer3_report._read_campaign_lock(
        campaign / "campaign.lock",
        purpose=layer3_report.CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    checked = (
        wal.knowledge_provenance_and_receipt_sha256_for_material_report(
            layout, records, campaign_lock=decoded_lock,
        )
    )
    assert checked is not None
    projection, receipt_sha256 = checked

    receipt_path = campaign / knowledge_manifest.RECEIPT_FILENAME
    receipt = json.loads(receipt_path.read_bytes())
    receipt["claim_boundary"]["classification"] = "alternate-valid-claim"
    receipt_path.write_bytes(
        knowledge_manifest.canonical_json_bytes(receipt) + b"\n"
    )
    assert wal.knowledge_provenance_for_material_report(
        layout, records, campaign_lock=decoded_lock,
    ) == projection

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="knowledge receipt bytes changed after provenance validation",
    ):
        layer3_report._artifact_refs(
            campaign, knowledge_receipt_sha256=receipt_sha256,
        )


def test_legacy_v2_report_schema_remains_readable(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    legacy = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    legacy["schema_version"] = "layer3-material-report/v2"
    del legacy["knowledge_provenance"]
    del legacy["admission_decision"]
    del legacy["acceptance_receipt"]
    del legacy["certifying_input"]
    layer3_report._validate_schema(legacy)


@pytest.mark.parametrize(
    "schema_version",
    ("layer3-material-report/v2", "layer3-material-report/v3"),
    ids=("v2", "v3"),
)
def test_saved_report_without_current_verifier_conformance_remains_readable(
    tmp_path: Path, schema_version: str,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    del report["current_verifier_conformance"]
    if schema_version == "layer3-material-report/v2":
        report["schema_version"] = schema_version
        del report["knowledge_provenance"]
        del report["admission_decision"]
        del report["acceptance_receipt"]
        del report["certifying_input"]

    layer3_report._validate_schema(report)


def test_legacy_v2_without_policy_hint_remains_readable(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    legacy = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    legacy["schema_version"] = "layer3-material-report/v2"
    legacy.pop("knowledge_provenance")
    legacy.pop("policy_hint", None)
    del legacy["admission_decision"]
    del legacy["acceptance_receipt"]
    del legacy["certifying_input"]

    layer3_report._validate_schema(legacy)


def test_legacy_v2_rejects_forward_knowledge_provenance_property(tmp_path):
    """Fails only when the legacy v2 schema accidentally admits the forward field."""
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    legacy = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    legacy["schema_version"] = "layer3-material-report/v2"
    del legacy["admission_decision"]
    del legacy["acceptance_receipt"]
    del legacy["certifying_input"]

    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(legacy)


def test_saved_v3_without_knowledge_provenance_remains_readable(tmp_path):
    """Fails only when the optional top-level field breaks legacy v3 reading."""
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    del report["knowledge_provenance"]

    layer3_report._validate_schema(report)


def test_report_policy_hint_rejects_non_string_top_level(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["policy_hint"] = False

    with pytest.raises(layer3_report.Layer3ReportError):
        layer3_report._validate_schema(report)


def test_existing_v3_missing_new_admission_fields_remains_readable(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    assert report["acceptance_receipt"] is None
    del report["acceptance_receipt"]
    del report["certifying_input"]
    del report["campaign_verifier_epoch"]["verifier_assessment_basis"]
    layer3_report._validate_schema(report)


def test_existing_certifying_v3_missing_epoch_remains_readable(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["acceptance_receipt"] = {
        "path": "acceptance/legacy.json",
        "sha256": "a" * 64,
    }
    report["certifying_input"] = True
    del report["campaign_verifier_epoch"]
    del report["current_verifier_conformance"]

    layer3_report._validate_schema(report)


def test_generic_generators_have_no_certifying_input_parameter(
    tmp_path: Path,
) -> None:
    import inspect

    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign,
        generated_from_head="fixed",
        output_root=output_root,
    )
    assert report["certifying_input"] is False
    assert "certifying_input" not in inspect.signature(
        layer3_report.build_report
    ).parameters
    assert "certifying_input" not in inspect.signature(
        layer3_report.render
    ).parameters
    with pytest.raises(TypeError, match="certifying_input"):
        layer3_report.build_report(
            campaign,
            generated_from_head="fixed",
            output_root=output_root,
            certifying_input=True,
        )
    with pytest.raises(TypeError, match="certifying_input"):
        layer3_report.render(
            campaign,
            tmp_path / "forbidden-certifying-report.json",
            generated_from_head="fixed",
            output_root=output_root,
            certifying_input=True,
        )


def test_reader_rejects_certifying_input_without_acceptance_receipt(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["certifying_input"] = True
    assert report["acceptance_receipt"] is None
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying_input=true と acceptance_receipt 非 null は同値必須$",
    ):
        layer3_report._validate_schema(report)


def test_reader_rejects_acceptance_receipt_without_certifying_input(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["acceptance_receipt"] = {"path": "receipt.json", "sha256": "a" * 64}
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying_input=true と acceptance_receipt 非 null は同値必須$",
    ):
        layer3_report._validate_schema(report)


def test_reader_rejects_historical_marker_on_certifying_input(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["acceptance_receipt"] = {
        "path": "acceptance/fixture.json",
        "sha256": "a" * 64,
    }
    report["certifying_input"] = True
    report["admission_decision"]["admission_status"] = "admitted"

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="layer3 schema 検証に失敗$",
    ):
        layer3_report._validate_schema(report)


def test_reader_rejects_certifying_historical_admission(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    historical = _historical_admitted_campaign(campaign)
    monkeypatch.setattr(
        layer3_report, "require_admitted_campaign",
        lambda _path, *, purpose: historical,
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["acceptance_receipt"] = {"path": "receipt.json", "sha256": "a" * 64}
    report["certifying_input"] = True

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying_input=true には admission_status=admitted が必須$",
    ):
        layer3_report._validate_schema(report)


def test_m14_non_certifying_receipt_is_rejected_downstream(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = SimpleNamespace(certifying=False)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying=true でない",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=verified,
            generated_from_head="fixed",
            output_root=output_root,
        )


def test_render_accepted_rejects_legacy_receipt_before_write(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = _verified_non_certifying_receipt(campaign, output_root)
    out = tmp_path / "accepted-report.json"

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="downstream capability requires the current receipt schema",
    ):
        layer3_report.render_accepted(
            campaign,
            out,
            acceptance_receipt=verified,
            generated_from_head="fixed",
            output_root=output_root,
        )

    assert not out.exists()


def test_accepted_report_api_has_no_return_code_or_stdout_parameter() -> None:
    import inspect

    parameters = inspect.signature(layer3_report.build_accepted_report).parameters
    assert "acceptance_receipt" in parameters
    assert not ({"rc", "return_code", "stdout"} & set(parameters))


def test_accepted_report_rejects_unsealed_receipt_capability(tmp_path: Path) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = _verified_non_certifying_receipt(campaign, output_root)
    forged = dataclasses.replace(verified, _seal=object())
    with pytest.raises(
        layer3_report.Layer3ReportError, match="receipt-capability",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=forged,
            output_root=output_root,
        )


def test_accepted_report_rejects_historical_before_certifying_fields_are_set(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    historical = _historical_admitted_campaign(campaign)
    monkeypatch.setattr(
        layer3_report, "require_admitted_campaign",
        lambda _path, *, purpose: historical,
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )
    monkeypatch.setattr(
        layer3_report, "build_report", lambda *_args, **_kwargs: report,
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying Layer3 report には admission_status=admitted が必須$",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=object(),
            generated_from_head="fixed",
            output_root=output_root,
        )

    assert report["acceptance_receipt"] is None
    assert report["certifying_input"] is False


def test_accepted_report_requires_e1_and_records_epoch(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _certifying_campaign(tmp_path)
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )

    report = layer3_report.build_accepted_report(
        campaign,
        acceptance_receipt=object(),
        generated_from_head="fixed",
        output_root=output_root,
    )

    assert report["certifying_input"] is True
    assert report["campaign_verifier_epoch"]["state"] == "E1"
    assert report["campaign_verifier_epoch"][
        "campaign_verifier_epoch"
    ].startswith("E1:")
    assert (
        "verifier_assessment_basis"
        not in report["campaign_verifier_epoch"]
    )
    assert report["acceptance_receipt"] == {
        "path": verified.relative_path,
        "sha256": verified.sha256,
    }


def test_accepted_report_rejects_no_commit_campaign(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="at least one persisted COMMIT",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=object(),
            generated_from_head="fixed",
            output_root=output_root,
        )


def test_certified_report_omits_current_verifier_conformance(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _certifying_campaign(tmp_path)
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )

    report = layer3_report.build_accepted_report(
        campaign,
        acceptance_receipt=object(),
        generated_from_head="fixed",
        output_root=output_root,
    )

    assert "current_verifier_conformance" not in report


def test_certified_schema_forbids_current_verifier_conformance(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = {
        key: value
        for key, value in layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        ).items()
        if key != "current_verifier_conformance"
    }
    report["acceptance_receipt"] = {
        "path": "acceptance/legacy.json",
        "sha256": "a" * 64,
    }
    report["certifying_input"] = True
    del report["campaign_verifier_epoch"]
    layer3_report._validate_schema(report)

    report["current_verifier_conformance"] = "unknown"
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="layer3 schema 検証に失敗$",
    ):
        layer3_report._validate_schema(report)


def test_render_accepted_persists_certifying_report(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _certifying_campaign(tmp_path)
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )
    out = tmp_path / "accepted-report.json"

    report = layer3_report.render_accepted(
        campaign,
        out,
        acceptance_receipt=object(),
        generated_from_head="fixed",
        output_root=output_root,
    )

    assert report["certifying_input"] is True
    assert report["campaign_verifier_epoch"]["state"] == "E1"
    assert report["campaign_verifier_epoch"][
        "campaign_verifier_epoch"
    ].startswith("E1:")
    assert report["acceptance_receipt"] == {
        "path": verified.relative_path,
        "sha256": verified.sha256,
    }
    assert out.is_file()
    assert json.loads(out.read_text(encoding="utf-8")) == report


def test_accepted_report_rejects_external_v2_campaign_without_git_head(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    _assert_external_campaign_without_git_head(campaign)
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="git HEAD を取得できない$",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=object(),
            output_root=output_root,
        )


def test_accepted_report_rejects_e0_after_historical_projection(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    historical = _historical_admitted_campaign(campaign)
    e0 = artifact_admission.CampaignVerifierEpoch(
        campaign_verifier_epoch="E0",
        state="E0",
        reason_code="v1-authority-absent",
    )
    historical_e0 = dataclasses.replace(
        historical,
        campaign_verifier_epoch=e0,
        decision=dataclasses.replace(
            historical.decision,
            classification="admitted-new-schema",
            admission_status="admitted",
        ),
    )
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )

    def purpose_gate(_path, *, purpose):
        if purpose is layer3_report.CampaignReadPurpose.HISTORICAL_RAW:
            return historical_e0
        raise artifact_admission.CampaignVerifierEpochRejected(e0)

    monkeypatch.setattr(
        layer3_report, "require_admitted_campaign", purpose_gate,
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match=r"certifying campaign admission 検証に失敗:.*state=E0",
    ):
        layer3_report.build_accepted_report(
            campaign,
            acceptance_receipt=object(),
            generated_from_head="fixed",
            output_root=output_root,
        )


@pytest.fixture
def certifying_completeness_chain(tmp_path: Path, monkeypatch):
    """Build a full campaign-chain fixture with admission as the only variable."""
    output_root = tmp_path / "output"
    workload = "ycsb-a"
    workload_flags = dict(YCSB)
    descriptor = {
        "schema_version": "8b-v1",
        "source": "campaign_search_config_projection",
        "contention": {"label": "high", "skew": 0.9},
        "read_write": {"read_ratio_percent": 50, "rmw": 0},
        "scale": {"records": 100_000, "threads": 4},
        "correctness": "serializable_legacy_and_s2",
        "objective": "maximize_throughput_tps",
    }
    descriptor_sha256 = hashlib.sha256(
        json.dumps(
            descriptor, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    descriptor_binding = {
        "input_sha256": descriptor_sha256,
        "output_sha256": descriptor_sha256,
        "projection_version": "8b-descriptor-projection/v1",
        "schema_sha256": (
            "5a9e2696b8fba18f8f7cf01183673a1bd6f5781cc9cb1fe8641f9d667fe11549"
        ),
    }
    identity_preimage = campaign_lock.canonical_json({
        "spec_content": autonomous_trial_completeness._AUTONOMOUS_SPEC_CONTENT,
        "ccbench_commit": CURRENT_PIN,
        "search_tag": "workload-conditioned-autonomous",
        "search_config": {
            "axis": "silo-backoff-trigger-gating",
            "descriptor_schema": "8b-v1",
            "descriptor_sha256": descriptor_sha256,
            "generation_budget": 1,
            "pilot_scope": "exploratory-ycsb-abc",
            "records": 100_000,
            "reflux": "on",
            "scale": "silo",
            "stop_policy": "fixed-generations-no-performance-early-stop",
            "threads": 4,
            "trigger_gate_binding_schema": "izanagi-trigger-gate-binding/v1",
            "verify": "legacy+s2",
            "workload": workload,
            "ycsb": workload_flags,
            "build_admission": {"fixture": True},
        },
        "trial": "fixture-trial-ycsb-a",
    })
    campaign_id = (
        "p3-t178-ycsb-a-workload-conditioned-autonomous-"
        + hashlib.sha256(identity_preimage.encode("utf-8")).hexdigest()[:8]
    )
    campaign_root = output_root / "campaigns" / campaign_id
    persisted_path = campaign_root / "reports" / "layer3_report.json"
    persisted_path.parent.mkdir(parents=True)
    (campaign_root / "campaign.lock").write_text(
        build_v2_campaign_lock(identity_preimage), encoding="utf-8",
    )

    producer = SimpleNamespace(
        MAX_APPROVED_GENERATIONS=2,
        WORKLOADS={
            workload: {
                "ycsb": workload_flags,
                "records": 100_000,
                "threads": 4,
            }
        },
    )
    producer.resolve_workload_entry = lambda name: producer.WORKLOADS[name]
    monkeypatch.setattr(
        autonomous_trial_completeness, "_producer_module", lambda: producer,
    )
    monkeypatch.setattr(
        autonomous_trial_completeness,
        "_environment_contract_from_campaign_lock",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        autonomous_trial_completeness,
        "_fresh_layer3_for_comparison",
        lambda **kwargs: kwargs["persisted"],
    )

    decision_ref: dict[str, dict] = {}
    monkeypatch.setattr(
        autonomous_trial_completeness,
        "require_admitted_campaign",
        lambda _path, **_kwargs: SimpleNamespace(
            decision=SimpleNamespace(
                as_receipt=lambda: decision_ref["value"],
            ),
        ),
    )
    persisted = {
        "meta": {
            "campaign_id": campaign_id,
            "generated_from_head": "a" * 40,
        },
        "certifying_input": True,
    }
    cell = {
        "campaign_id": campaign_id,
        "campaign_root": str(campaign_root),
        "workload": workload,
        "workload_flags": workload_flags,
        "perf_config_scale": {"records": 100_000, "threads": 4},
        "descriptor": descriptor,
        "descriptor_binding": descriptor_binding,
    }
    report = {
        "trial_id": "fixture-trial",
        "generation_budget_per_workload": 1,
        "launch_admission": {"certifying": True},
        "cells": [cell],
    }

    def set_admission(*, classification: str, admission_status: str) -> None:
        decision = {
            "schema_version": "campaign-artifact-admission-decision/v1",
            "classification": classification,
            "admission_status": admission_status,
            "verification_status": "verified",
            "campaign_id": campaign_id,
            "campaign_path": f"campaigns/{campaign_id}",
            "campaign_lock_sha256": "b" * 64,
            "wal_sha256": "c" * 64,
            "policy_sha256": "d" * 64,
            "attempt_receipt_sha256s": [],
            "validator": {"identity": "fixture", "sha256": "e" * 64},
            "overlay": {"ledger_sha256": None, "record_key": None},
        }
        decision_ref["value"] = decision
        persisted["admission_decision"] = decision
        cell["admission_decision"] = decision
        persisted_path.write_text(
            json.dumps(persisted, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return output_root, report, set_admission


def test_completeness_rejects_certifying_historical_admission(
    certifying_completeness_chain,
) -> None:
    output_root, report, set_admission = certifying_completeness_chain
    set_admission(
        classification="verified-post-admission-schema",
        admission_status="admitted",
    )
    autonomous_trial_completeness.assert_campaign_layer3_chain(
        report=report, output_root=output_root,
    )

    set_admission(
        classification="historical-pre-admission-schema",
        admission_status="historical-not-reclassified",
    )
    with pytest.raises(
        autonomous_trial_completeness.AutonomousTrialCompletenessError,
        match=(
            r"\[campaign-chain\] persisted layer3 report certifying input "
            r"requires admission_status=admitted$"
        ),
    ):
        autonomous_trial_completeness.assert_campaign_layer3_chain(
            report=report, output_root=output_root,
        )


def test_completeness_reads_contract_from_v2_authority_and_identity_excludes_it(
    tmp_path: Path,
) -> None:
    producer = p3_autonomous_workload_trial
    identity_preimage = campaign_lock.canonical_json({
        "spec_content": "fixture",
        "ccbench_commit": CURRENT_PIN,
        "search_tag": "fixture",
        "search_config": {"build_admission": {"fixture": True}},
        "trial": "fixture",
    })
    contracts = []
    for env_tag in ("linux-baremetal", "pegasus"):
        campaign_root = tmp_path / env_tag
        campaign_root.mkdir()
        authorization = env_contract.authorize(env_tag)
        (campaign_root / "campaign.lock").write_text(
            build_v2_campaign_lock(
                identity_preimage, authorization=authorization,
            ),
            encoding="utf-8",
        )
        contract = (
            autonomous_trial_completeness
            ._environment_contract_from_campaign_lock(
                campaign_root, producer=producer,
            )
        )
        assert contract == authorization.contract
        contracts.append(contract)

    workload = "ycsb-a"
    workload_flags = producer.WORKLOADS[workload]
    descriptor, descriptor_binding = producer._descriptor_for(workload_flags)
    context = producer.build_run_context(
        generator_id=producer.GeneratorId.S8A_TRIGGER_SWEEP,
    )
    campaign_ids = {
        str(producer.ident.campaign_id(producer._campaign_for(
            workload=workload,
            entry=workload_flags,
            descriptor=descriptor,
            descriptor_record=descriptor_binding,
            trial_id="fixture",
            generations=1,
            contract=contract,
            build_context=context,
        )))
        for contract in contracts
    }
    assert len(campaign_ids) == 1


def test_completeness_rejects_v1_lock_without_authority(tmp_path: Path) -> None:
    campaign_root = tmp_path / "campaign"
    campaign_root.mkdir()
    identity_preimage = campaign_lock.canonical_json({
        "spec_content": "fixture",
        "ccbench_commit": CURRENT_PIN,
        "search_tag": "fixture",
        "search_config": {},
        "trial": "fixture",
    })
    (campaign_root / "campaign.lock").write_text(
        identity_preimage, encoding="utf-8",
    )
    with pytest.raises(
        autonomous_trial_completeness.AutonomousTrialCompletenessError,
        match=(
            r"\[campaign-chain\] campaign.lock v2 authority is required "
            r"for completeness proof$"
        ),
    ):
        autonomous_trial_completeness._environment_contract_from_campaign_lock(
            campaign_root, producer=p3_autonomous_workload_trial,
        )


def test_bench_rep_returncodes_passes_real_view_and_schema(tmp_path):
    """M-P10: bench event の新 key が _view_row を経ても実 schema 検証を通る。"""
    campaign, output_root = _campaign(
        tmp_path, [_bench(rep_returncodes=[0, 0, 0, 0, 0])],
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["runs"][0]["rep_returncodes"] == [0, 0, 0, 0, 0]


def test_perf_observation_survives_render_and_legacy_run_remains_valid(tmp_path):
    unavailable = _perf_observation()
    unavailable_nonzero = _perf_observation(unavailable_reason="nonzero-rc")
    unavailable_missing = _perf_observation(
        unavailable_reason="requested-events-missing",
    )
    available_complete = _perf_observation(available=True)
    available_incomplete = _perf_observation(
        available=True, missing=("llc_miss_rate", "ipc"),
    )
    campaign, output_root = _campaign(
        tmp_path,
        [
            _bench("without-perf", perf_observation=unavailable),
            _bench("without-perf-nonzero", perf_observation=unavailable_nonzero),
            _bench("without-perf-events", perf_observation=unavailable_missing),
            _bench("with-complete-perf", perf_observation=available_complete),
            _bench("with-incomplete-perf", perf_observation=available_incomplete),
            _bench("legacy-without-perf-observation"),
        ],
    )
    out = tmp_path / "layer3-report.json"

    report = layer3_report.render(
        campaign, out, generated_from_head="fixed", output_root=output_root,
    )

    runs_with_observation = [
        row for row in report["runs"] if "perf_observation" in row
    ]
    legacy_runs = [
        row for row in report["runs"] if "perf_observation" not in row
    ]

    def observation_sort_key(observation):
        return json.dumps(observation, sort_keys=True)

    assert sorted(
        [row["perf_observation"] for row in runs_with_observation],
        key=observation_sort_key,
    ) == sorted(
        [
            unavailable,
            unavailable_nonzero,
            unavailable_missing,
            available_complete,
            available_incomplete,
        ],
        key=observation_sort_key,
    )
    assert len(legacy_runs) == 1
    assert json.loads(out.read_text(encoding="utf-8"))["runs"] == report["runs"]


@pytest.mark.parametrize(
    "target_path, expected_absolute_path",
    [
        ((), ["runs", 0, "perf_observation"]),
        (("preflight",), ["runs", 0, "perf_observation", "preflight"]),
        (
            ("preflight", "candidates", 0),
            ["runs", 0, "perf_observation", "preflight", "candidates", 0],
        ),
    ],
    ids=("observation", "preflight", "candidate"),
)
def test_perf_observation_rejects_unknown_key(
        tmp_path, target_path, expected_absolute_path):
    observation = _perf_observation()
    target = observation
    for component in target_path:
        target = target[component]
    target["unexpected"] = "must-be-rejected"
    campaign, output_root = _campaign(
        tmp_path, [_bench(perf_observation=observation)],
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match=r"^layer3 schema 検証に失敗$",
    ) as caught:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )
    cause = caught.value.__cause__
    assert isinstance(cause, jsonschema.ValidationError)
    assert cause.validator == "additionalProperties"
    assert list(cause.absolute_path) == expected_absolute_path


def test_perf_observation_rejects_schema_valid_noncanonical_receipt(tmp_path):
    """M13: layer3 は JSON Schema だけでなく canonical receipt を検証する。"""
    observation = _perf_observation()
    observation["preflight"]["probe_argv"] = ["perf", "stat"]
    campaign, output_root = _campaign(
        tmp_path, [_bench(perf_observation=observation)],
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match=r"^layer3 perf observation 共有検証に失敗$",
    ) as caught:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )
    assert isinstance(
        caught.value.__cause__, perf_preflight.PerfPreflightError,
    )


@pytest.mark.parametrize(
    "contradiction",
    [
        "perf-required-but-counter-not-required",
        "use-perf-false-disagrees-with-available",
        "use-perf-true-disagrees-with-unavailable",
        "no-perf-counter-complete",
        "perf-complete-reports-missing-indicators",
        "perf-incomplete-reports-no-missing-indicators",
        "probe-error-reaches-layer3",
        "unavailable-status-claims-available",
        "no-perf-reports-missing-indicators",
        "available-status-has-unavailable-reason",
        "unavailable-status-has-probe-error-reason",
    ],
)
def test_perf_observation_rejects_producer_impossible_combinations(
        tmp_path, contradiction):
    if contradiction in {
        "perf-required-but-counter-not-required",
        "use-perf-false-disagrees-with-available",
        "perf-complete-reports-missing-indicators",
        "perf-incomplete-reports-no-missing-indicators",
        "unavailable-status-claims-available",
        "available-status-has-unavailable-reason",
    }:
        observation = _perf_observation(available=True)
    else:
        observation = _perf_observation()

    if contradiction == "perf-required-but-counter-not-required":
        observation["counter_status"] = "not_required"
    elif contradiction == "use-perf-false-disagrees-with-available":
        observation["use_perf"] = False
        observation["counter_status"] = "not_required"
        observation["claim_scope"] = {
            "throughput": "eligible",
            "perf_required": "unsupported",
        }
    elif contradiction == "use-perf-true-disagrees-with-unavailable":
        observation["use_perf"] = True
        observation["counter_status"] = "complete"
    elif contradiction == "no-perf-counter-complete":
        observation["counter_status"] = "complete"
    elif contradiction == "perf-complete-reports-missing-indicators":
        observation["missing_leading_indicators"] = ["ipc"]
    elif contradiction == "perf-incomplete-reports-no-missing-indicators":
        observation["counter_status"] = "incomplete"
    elif contradiction == "probe-error-reaches-layer3":
        observation["preflight"].update({
            "status": "probe_error", "reason": "probe-os-error",
        })
    elif contradiction == "unavailable-status-claims-available":
        observation["preflight"].update({
            "status": "unavailable", "reason": "perf-not-found",
        })
    elif contradiction == "no-perf-reports-missing-indicators":
        observation["missing_leading_indicators"] = ["ipc"]
    elif contradiction == "available-status-has-unavailable-reason":
        observation["preflight"]["reason"] = "nonzero-rc"
    else:
        observation["preflight"]["reason"] = "probe-timeout"

    campaign, output_root = _campaign(
        tmp_path, [_bench(perf_observation=observation)],
    )
    with pytest.raises(
        layer3_report.Layer3ReportError,
        match=r"^layer3 schema 検証に失敗$",
    ) as caught:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )
    assert isinstance(caught.value.__cause__, jsonschema.ValidationError)


@pytest.mark.parametrize("state", ["not-json", json.dumps({"whiteboard": {}})])
def test_existing_invalid_loop_state_fails_closed(tmp_path, state):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "loop_state.json").write_text(state, encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_existing_empty_loop_state_keeps_loop_state_provenance(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], whiteboard=[])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["whiteboard"] == []
    assert report["whiteboard_provenance"] == "loop_state"
    assert not any(ref.startswith("wb:") for ref in report["source_refs"])


@pytest.mark.parametrize("provenance", [None, "unknown"])
def test_schema_rejects_missing_or_invalid_whiteboard_provenance(provenance, tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    if provenance is None:
        del report["whiteboard_provenance"]
    else:
        report["whiteboard_provenance"] = provenance
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_relative_and_absolute_campaign_paths_are_byte_identical(tmp_path, monkeypatch):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    monkeypatch.chdir(output_root.parent)
    relative = campaign.relative_to(output_root.parent)
    layer3_report.render(relative, first, generated_from_head="f" * 40, output_root=output_root)
    layer3_report.render(campaign, second, generated_from_head="f" * 40, output_root=output_root)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text())["meta"]["campaign_path"] == relative.as_posix()


def test_unknown_stage_fails_closed(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("unknown-stage")])
    with pytest.raises(layer3_report.Layer3ReportError, match="unknown WAL stage") as exc_info:
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalLineError)


def test_shared_known_session_stage_is_outside_layer3_semantic_subset(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record(model.STAGE_S1_SESSION, event="session-start")],
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="未知の WAL stage"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )


def test_nested_duplicate_wal_key_fails_closed_for_one_reason(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "runs/wal.jsonl").write_bytes(
        b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
        b'"ts":1,"payload":{"genome":"g","src_token":"s",'
        b'"details":{"fitness_tps":1,"fitness_tps":2}}}\n',
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="WAL record が不正") as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalDuplicateKeyError)
    assert "duplicate key" in str(exc_info.value)


@pytest.mark.parametrize(
    ("raw_line", "expected_cause"),
    [
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env","ts":1}\n',
            "missing=['payload']", id="missing-key",
        ),
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
            b'"ts":1,"payload":{},"extra":true}\n',
            "unknown=['extra']", id="unknown-key",
        ),
        pytest.param(
            b'{"variant":"v1","stage":1,"env_tag":"test-env",'
            b'"ts":1,"payload":{}}\n',
            "WAL stage must be a string", id="wrong-type",
        ),
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
            b'"ts":1,"payload":["bad"]}\n',
            "WAL payload must be a JSON object", id="non-object-payload",
        ),
    ],
)
def test_wal_wrapper_preserves_specific_parser_diagnosis(
        tmp_path, raw_line, expected_cause):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "runs/wal.jsonl").write_bytes(raw_line)

    with pytest.raises(layer3_report.Layer3ReportError) as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)

    assert expected_cause in str(exc_info.value)


def test_wal_blank_between_records_uses_shared_strict_contract(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", variant="v1", genome="g", src_token="s"),
        _record("build_start", variant="v2", genome="h", src_token="t"),
    ])
    wal_path = campaign / "runs/wal.jsonl"
    lines = wal_path.read_text(encoding="utf-8").splitlines(keepends=True)
    wal_path.write_text(lines[0] + "\n" + lines[1], encoding="utf-8")

    with pytest.raises(
            layer3_report.Layer3ReportError, match="WAL line must not be empty",
    ) as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalLineError)


@pytest.mark.parametrize("tail_kind", ["complete-json", "multibyte-partial"])
def test_unframed_wal_tail_is_translated_with_framing_cause(tmp_path, tail_kind):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    wal_path = campaign / "runs/wal.jsonl"
    if tail_kind == "complete-json":
        wal_path.write_bytes(wal_path.read_bytes()[:-1])
    else:
        with wal_path.open("ab") as stream:
            stream.write(b'{"variant":"broken-\xe3\x81')

    with pytest.raises(layer3_report.Layer3ReportError, match="WAL framing") as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )

    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalFramingError)


def test_direct_script_starts_with_clean_pythonpath(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(Path(layer3_report.__file__).resolve()), "--help"],
        cwd=tmp_path, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "campaign_dir" in completed.stdout


def test_body_event_omission_is_detected(tmp_path, monkeypatch):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", genome="g", src_token="s"), _bench(),
    ])
    original = layer3_report._variant_rows

    def drop_one(records):
        rows = original(records)
        rows[0]["events"].pop()
        return rows

    monkeypatch.setattr(layer3_report, "_variant_rows", drop_one)
    with pytest.raises(layer3_report.Layer3ReportError, match="report 本体"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)


def test_duplicate_wal_and_whiteboard_fail_closed(tmp_path):
    duplicate = _bench()
    campaign, output_root = _campaign(tmp_path, [duplicate, duplicate])
    with pytest.raises(layer3_report.Layer3ReportError, match="完全重複"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    whiteboard = {
        "iteration": 1,
        "direction": "increase",
        "magnitude": "small",
        "result": "success",
        "delta_pct": None,
    }
    campaign, output_root = _campaign(tmp_path / "whiteboard", [_record("build_start", genome="g", src_token="s")], [whiteboard, whiteboard])
    with pytest.raises(layer3_report.Layer3ReportError, match="完全重複"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)


def test_layer3_report_rejects_out_of_domain_whiteboard_value(tmp_path):
    whiteboard = {
        "iteration": 1,
        "direction": "up",
        "magnitude": "small",
        "result": "success",
        "delta_pct": None,
    }
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        [whiteboard],
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match=r"whiteboard entry\[0\]\.direction",
    ):
        layer3_report.build_report(
            campaign,
            generated_from_head="fixed",
            output_root=output_root,
        )


def test_layer3_report_uses_shared_whiteboard_value_domain_validator(
        tmp_path, monkeypatch):
    assert (
        layer3_report.p3_s4_loop.assert_whiteboard_value_domains
        is p3_s4_loop.assert_whiteboard_value_domains
    )
    whiteboard = {
        "iteration": 1,
        "direction": "increase",
        "magnitude": "small",
        "result": "success",
        "delta_pct": None,
    }
    whiteboard_second = {
        "iteration": 2,
        "direction": "decrease",
        "magnitude": "small",
        "result": "success",
        "delta_pct": None,
    }
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        [whiteboard, whiteboard_second],
    )
    calls = []
    real_validator = p3_s4_loop.assert_whiteboard_value_domains

    def spy(entry, index):
        calls.append((entry, index))
        return real_validator(entry, index)

    monkeypatch.setattr(
        p3_s4_loop, "assert_whiteboard_value_domains", spy,
    )
    layer3_report.build_report(
        campaign,
        generated_from_head="fixed",
        output_root=output_root,
    )
    assert len(calls) == 2
    assert calls[0][0] == whiteboard
    assert calls[0][1] == 0
    assert calls[1][0] == whiteboard_second
    assert calls[1][1] == 1
    assert calls == [(whiteboard, 0), (whiteboard_second, 1)]


def test_layer3_report_wraps_missing_whiteboard_value_with_keyerror_cause(
        tmp_path):
    whiteboard = {
        "iteration": 1,
        "magnitude": "small",
        "result": "success",
        "delta_pct": None,
    }
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        [whiteboard],
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match=r"whiteboard entry\[0\] の値域検査に失敗",
    ) as caught:
        layer3_report.build_report(
            campaign,
            generated_from_head="fixed",
            output_root=output_root,
        )
    assert isinstance(caught.value.__cause__, KeyError)


def test_floor_kinds_match_independently_and_classification_records_skips(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB, protocol="silo")
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    within = {"cv": 0.01, "median": 12.0}
    between = {"max_delta_pct": 2.0}
    (calibration / "within.json").write_text(json.dumps({
        "threads": 4, "saturation": {"records": 100000}, "workload": YCSB,
        "noise_floor": within,
    }), encoding="utf-8")
    (calibration / "between.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "between_run": between,
    }), encoding="utf-8")
    (calibration / "frequency.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "frequency_hz": 10,
    }), encoding="utf-8")
    (calibration / "wrong-workload.json").write_text(json.dumps({
        "records": 100000, "threads": 4,
        "workload": {**YCSB, "ycsb_rratio": "95"},
        "noise_floor": {"cv": 0.02},
    }), encoding="utf-8")
    report = layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert report["noise_floor"]["within_run"]["value"] == within
    assert report["noise_floor"]["between_run"]["value"] == between
    for kind in ("within_run", "between_run"):
        assert report["noise_floor"][kind]["provenance"] == "env-record"
        assert report["noise_floor"][kind]["source"]["path"].startswith(
            "env/test-env/calibration/")
        assert report["noise_floor"][kind]["search"] is None

    _, search_details = layer3_report._calibration_floors(
        calibration, 100000, 4, YCSB, protocol="silo")
    for kind in ("within_run", "between_run"):
        assert search_details[kind]["skipped_no_floor_block"] == ["frequency.json"]


def test_between_run_schema_version_does_not_change_floor_classification(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB, protocol="silo")
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    between = {"max_delta_pct": 2.0}
    (calibration / "between.json").write_text(json.dumps({
        "schema_version": "between-run-noise-floor/v1",
        "records": 100000, "threads": 4, "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "between_run": between,
    }), encoding="utf-8")

    floors, details = layer3_report._calibration_floors(
        calibration, 100000, 4, YCSB, protocol="silo")
    assert details["between_run"]["candidate_files"] == ["between.json"]
    assert floors["between_run"]["provenance"] == "env-record"
    assert floors["between_run"]["value"] == between

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["noise_floor"]["between_run"]["value"] == between


def test_floor_match_uses_protocol_records_threads_and_workload(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB,
        protocol="mocc",
    )
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    for protocol, cv in (("silo", 0.02), ("mocc", 0.07)):
        (calibration / f"between-{protocol}.json").write_text(json.dumps({
            "records": 100000,
            "threads": 4,
            "workload": YCSB,
            "genome": f"{protocol}|BACK_OFF=0",
            "between_run": {"cv": cv},
        }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    floor = report["noise_floor"]["between_run"]
    assert floor["value"] == {"cv": 0.07}
    assert floor["protocol"] == "mocc"
    assert floor["source"]["path"].endswith("between-mocc.json")


def test_wrong_protocol_floor_is_reported_as_mismatch(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB,
        protocol="mocc",
    )
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    (calibration / "between-silo.json").write_text(json.dumps({
        "records": 100000,
        "threads": 4,
        "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "between_run": {"cv": 0.02},
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    floor = report["noise_floor"]["between_run"]
    assert floor["value"] is None
    assert floor["protocol"] == "mocc"
    assert floor["search"]["criteria"]["protocol"] == "mocc"
    assert floor["search"]["mismatches"][0]["protocol"] == "silo"


def test_mixed_protocol_campaign_cannot_receive_report_level_floor(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", variant="v1", genome="g", src_token="s"),
        _record("build_start", variant="v2", genome="h", src_token="t"),
    ], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    (calibration / "within.json").write_text(json.dumps({
        "threads": 4,
        "saturation": {"records": 100000},
        "workload": YCSB,
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")
    (calibration / "between.json").write_text(json.dumps({
        "records": 100000,
        "threads": 4,
        "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "between_run": {"cv": 0.02},
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    for kind in ("within_run", "between_run"):
        floor = report["noise_floor"][kind]
        assert floor["value"] is None
        assert "protocol" not in floor
        assert floor["search"]["criteria"]["protocol"] is None
        assert floor["search"]["campaign_protocol_resolution"] == (
            "campaign-protocol-missing-invalid-or-multiple"
        )


def test_campaign_protocol_rejects_missing_malformed_and_multiple_canonical_values():
    def start(genome=_UNSET):
        payload = {} if genome is _UNSET else {"genome": genome}
        return {"stage": "build_start", "payload": payload}

    assert layer3_report._campaign_protocol([start()]) is None
    assert layer3_report._campaign_protocol([start(7)]) is None
    assert layer3_report._campaign_protocol([start("silo")]) is None
    assert layer3_report._campaign_protocol([start("|BACK_OFF=0")]) is None
    for malformed_body in (
        "mocc|garbage",
        "silo|B=x",
        "silo|Z=1,A=0",
        "silo|A=1,A=2",
        "silo|",
    ):
        assert layer3_report._campaign_protocol([start(malformed_body)]) is None
    assert layer3_report._campaign_protocol([
        start("silo|BACK_OFF=0"), start("mocc|BACK_OFF=0"),
    ]) is None


def test_legacy_silo_within_floor_without_genome_states_match_basis(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB,
        protocol="silo",
    )
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    (calibration / "within.json").write_text(json.dumps({
        "threads": 4,
        "saturation": {"records": 100000},
        "workload": YCSB,
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    floor = report["noise_floor"]["within_run"]
    assert floor["value"] == {"cv": 0.01}
    assert floor["protocol"] == "silo"
    assert floor["protocol_match_basis"] == "genome-absent-legacy-record"


def test_legacy_within_floor_without_genome_does_not_match_mocc(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB,
        protocol="mocc",
    )
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    (calibration / "within.json").write_text(json.dumps({
        "threads": 4,
        "saturation": {"records": 100000},
        "workload": YCSB,
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    floor = report["noise_floor"]["within_run"]
    assert floor["value"] is None
    assert floor["protocol"] == "mocc"
    assert floor["search"]["mismatches"][0]["protocol_match_basis"] == (
        "genome-absent-legacy-record"
    )


def test_pegasus_v2_adds_only_contract_pin_not_registered_glob(tmp_path):
    authorization = env_contract.authorize("pegasus")
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s", env_tag="pegasus",
        )],
        ycsb=YCSB,
        protocol="silo",
        authorization=authorization,
        records_count=1_000_000,
        threads=48,
    )
    _copy_contract_calibration(output_root, authorization)
    second_relative = Path(
        "output/env/pegasus/calibration/registered/"
        "calibration-94a4b79fa31bba3c.json"
    )
    second_target = output_root.parent / second_relative
    second_target.parent.mkdir(parents=True, exist_ok=True)
    second_target.write_bytes((ROOT / second_relative).read_bytes())

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    floor = report["noise_floor"]["within_run"]
    assert floor["value"] is None
    assert floor["provenance"] == "no-matching-env-record"
    assert floor["source"] is None
    assert floor["search"]["candidate_files"] == []
    assert floor["search"]["scanned_files"] == 1
    assert floor["search"]["contract_pin"] == {
        "status": "validated",
        "path": authorization.contract.calibration_ref.path,
        "sha256": authorization.contract.calibration_ref.sha256,
        "within_run_exclusion": "self-inconsistent-calibration",
    }
    between_pin = report["noise_floor"]["between_run"]["search"][
        "contract_pin"
    ]
    assert between_pin["status"] == "validated"
    assert "within_run_exclusion" not in between_pin


def test_pegasus_g1_direct_copy_does_not_restore_within_run_match(tmp_path):
    """Fails if exclusion regresses from the g1 series to only its pinned path."""
    authorization = env_contract.authorize("pegasus")
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s", env_tag="pegasus",
        )],
        ycsb=YCSB,
        protocol="silo",
        authorization=authorization,
        records_count=1_000_000,
        threads=48,
        copy_contract_calibration=False,
    )
    pin_path = _copy_contract_calibration(output_root, authorization)
    direct_copy = pin_path.parents[1] / "direct-copy.json"
    direct_copy.write_bytes(
        (ROOT / authorization.contract.calibration_ref.path).read_bytes()
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    floor = report["noise_floor"]["within_run"]
    assert floor["value"] is None
    assert floor["provenance"] == "no-matching-env-record"
    assert floor["source"] is None
    assert floor["search"]["candidate_files"] == []


def test_pegasus_g1_series_excludes_direct_within_but_keeps_between(tmp_path):
    """Fails if g1 admits a direct within floor or suppresses between-run too."""
    authorization = env_contract.authorize("pegasus")
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s", env_tag="pegasus",
        )],
        ycsb=YCSB,
        protocol="silo",
        authorization=authorization,
        records_count=1_000_000,
        threads=48,
    )
    calibration = output_root / "env/pegasus/calibration"
    (calibration / "within.json").write_text(json.dumps({
        "records": 1_000_000,
        "threads": 48,
        "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")
    between = {"max_delta_pct": 2.0}
    (calibration / "between.json").write_text(json.dumps({
        "records": 1_000_000,
        "threads": 48,
        "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "between_run": between,
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    within = report["noise_floor"]["within_run"]
    assert within["value"] is None
    assert within["provenance"] == "no-matching-env-record"
    assert within["search"]["candidate_files"] == []
    assert within["search"]["contract_pin"]["status"] == "validated"
    assert within["search"]["contract_pin"]["within_run_exclusion"] == (
        "self-inconsistent-calibration"
    )
    between_floor = report["noise_floor"]["between_run"]
    assert between_floor["value"] == between
    assert between_floor["provenance"] == "env-record"
    assert between_floor["source"]["path"].endswith("/between.json")


def test_registered_healthy_pegasus_g2_pin_remains_selectable(tmp_path):
    g2 = env_contract.GENERATIONS["pegasus"][1]
    ref = g2.contract.calibration_ref
    output_root = tmp_path / "repo/output"
    calibration = output_root / "env/pegasus/calibration"
    target = calibration / Path(*PurePosixPath(ref.path).parts[4:])
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT / ref.path).read_bytes())

    floors, search_details = layer3_report._calibration_floors(
        calibration,
        1_000_000,
        48,
        YCSB,
        protocol="silo",
        contract_pin=ref,
    )

    floor = floors["within_run"]
    assert floor["provenance"] == "env-record"
    assert floor["value"] is not None
    assert floor["source"]["path"] == ref.path.removeprefix("output/")
    assert floor["source"]["sha256"] == ref.sha256
    pin_search = search_details["within_run"]["contract_pin"]
    assert pin_search["status"] == "validated"
    assert "within_run_exclusion" not in pin_search


def test_within_run_exclusion_declaration_matches_real_self_failures():
    self_failures = set()
    for sequence in env_contract.GENERATIONS.values():
        for entry in sequence:
            contract = entry.contract
            if contract.attestation_mode != "required":
                continue
            verified = env_attestation.load_verified_calibration(contract, ROOT)
            assert verified.calibration is not None
            profile = verified.calibration.attestation_profile
            expected = env_attestation.expected_comparison_values(profile)[
                "effective_clock.samples_mhz"
            ]
            observed = {"samples_mhz": list(expected["samples_mhz"])}
            if not execution_guard.effective_clock_comparison_passes(
                expected, observed,
            ):
                self_failures.add((
                    contract.calibration_ref.path,
                    contract.calibration_ref.sha256,
                ))

    assert layer3_report.SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS == (
        frozenset(self_failures)
    )


def test_contract_pin_resolution_keeps_v1_none_and_marks_v2_env_mismatch():
    identity_preimage = campaign_lock.canonical_json({
        "ccbench_commit": CURRENT_PIN,
        "search_config": {"records": 1_000_000, "threads": 48},
        "search_tag": "test",
        "spec_content": "test",
        "trial": "trial",
    })
    decoded_v1 = campaign_lock.decode_campaign_lock(identity_preimage)
    assert layer3_report._contract_calibration_pin(
        decoded_v1, "unregistered-v1-env",
    ) == (None, None)

    decoded_v2 = campaign_lock.decode_campaign_lock(build_v2_campaign_lock(
        identity_preimage,
        authorization=env_contract.authorize("pegasus"),
    ))
    pin, search = layer3_report._contract_calibration_pin(
        decoded_v2, "linux-baremetal",
    )
    assert pin is None
    assert search == {
        "status": "authority-env-tag-mismatch",
        "authority_env_tag": "pegasus",
        "campaign_env_tag": "linux-baremetal",
    }


def test_contract_pin_env_mismatch_is_recorded_without_blocking_report(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s", env_tag="test-env",
        )],
        ycsb=YCSB,
        protocol="silo",
        authorization=env_contract.authorize("linux-baremetal"),
        copy_contract_calibration=False,
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    for floor in report["noise_floor"].values():
        assert floor["value"] is None
        assert floor["search"]["contract_pin"] == {
            "status": "authority-env-tag-mismatch",
            "authority_env_tag": "linux-baremetal",
            "campaign_env_tag": "test-env",
        }


def test_contract_pin_sha_mismatch_fails_closed_before_floor_use(tmp_path):
    authorization = env_contract.authorize("pegasus")
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s", env_tag="pegasus",
        )],
        ycsb=YCSB,
        protocol="silo",
        authorization=authorization,
        records_count=1_000_000,
        threads=48,
    )
    pin_path = _copy_contract_calibration(output_root, authorization)
    pin_path.write_bytes(pin_path.read_bytes() + b"\n")

    with pytest.raises(
        layer3_report.Layer3ReportError, match="SHA-256.*不一致",
    ):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )


def test_contract_pin_rejects_other_env_directory_and_nonfile(tmp_path):
    repo_root = tmp_path / "repo"
    calibration = repo_root / "output/env/pegasus/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    other_env = repo_root / "output/env/linux-baremetal/calibration/pin.json"
    other_env.parent.mkdir(parents=True)
    other_env.write_text("{}\n", encoding="utf-8")
    other_ref = env_contract.CalibrationRef(
        path="output/env/linux-baremetal/calibration/pin.json",
        sha256=hashlib.sha256(other_env.read_bytes()).hexdigest(),
    )

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="当該 env の calibration directory 外",
    ):
        layer3_report._validated_pin_path(calibration, other_ref)

    directory_ref = env_contract.CalibrationRef(
        path="output/env/pegasus/calibration",
        sha256="0" * 64,
    )
    with pytest.raises(
        layer3_report.Layer3ReportError, match="通常 file",
    ):
        layer3_report._validated_pin_path(calibration, directory_ref)

    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    escape = calibration / "escape.json"
    escape.symlink_to(outside)
    escape_ref = env_contract.CalibrationRef(
        path="output/env/pegasus/calibration/escape.json",
        sha256=hashlib.sha256(outside.read_bytes()).hexdigest(),
    )
    with pytest.raises(
        layer3_report.Layer3ReportError, match="calibration directory 外",
    ):
        layer3_report._validated_pin_path(calibration, escape_ref)

    parent_ref = env_contract.CalibrationRef(
        path="output/env/pegasus/calibration/../pin.json",
        sha256="0" * 64,
    )
    with pytest.raises(layer3_report.Layer3ReportError, match=r"\.\. 成分"):
        layer3_report._validated_pin_path(calibration, parent_ref)

    absolute_ref = env_contract.CalibrationRef(
        path="/output/env/pegasus/calibration/pin.json",
        sha256="0" * 64,
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="repo 相対"):
        layer3_report._validated_pin_path(calibration, absolute_ref)


def test_linux_v2_keeps_direct_skew_zero_floor_in_addition_to_pin(tmp_path):
    authorization = env_contract.authorize("linux-baremetal")
    skew_zero = {
        "ycsb_zipf_skew": "0", "ycsb_rratio": "50", "ycsb_rmw": "0",
    }
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s",
            env_tag="linux-baremetal",
        )],
        ycsb=skew_zero,
        protocol="silo",
        authorization=authorization,
        records_count=1_000_000,
        threads=48,
    )
    _copy_contract_calibration(output_root, authorization)
    skew_zero_relative = Path(
        "output/env/linux-baremetal/calibration/"
        "calibration_t48_skew0_rr50_rmw0.json"
    )
    skew_zero_target = output_root.parent / skew_zero_relative
    skew_zero_target.write_bytes((ROOT / skew_zero_relative).read_bytes())

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    floor = report["noise_floor"]["within_run"]
    assert floor["value"]["cv"] == 0.004726195977018071
    assert floor["source"]["path"] == (
        "env/linux-baremetal/calibration/"
        "calibration_t48_skew0_rr50_rmw0.json"
    )
    assert floor["protocol_match_basis"] == "genome-absent-legacy-record"


def test_nested_exploration_root_resolves_contract_pin_by_suffix(tmp_path):
    authorization = env_contract.authorize("pegasus")
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s", env_tag="pegasus",
        )],
        ycsb=YCSB,
        protocol="silo",
        authorization=authorization,
        records_count=1_000_000,
        threads=48,
        exploration_root=True,
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert output_root == tmp_path / "repo/output/exploration"
    floor = report["noise_floor"]["within_run"]
    assert floor["value"] is None
    assert floor["provenance"] == "no-matching-env-record"
    assert floor["source"] is None
    assert floor["search"]["candidate_files"] == []
    assert floor["search"]["contract_pin"]["status"] == "validated"
    assert floor["search"]["contract_pin"]["within_run_exclusion"] == (
        "self-inconsistent-calibration"
    )


def test_nested_exploration_root_uses_direct_floor_when_pin_file_is_missing(
        tmp_path):
    authorization = env_contract.authorize("pegasus")
    campaign, output_root = _campaign(
        tmp_path,
        [_record(
            "build_start", genome="g", src_token="s", env_tag="pegasus",
        )],
        ycsb=YCSB,
        protocol="silo",
        authorization=authorization,
        exploration_root=True,
        copy_contract_calibration=False,
    )
    calibration = output_root / "env/pegasus/calibration"
    calibration.mkdir(parents=True)
    (calibration / "within.json").write_text(json.dumps({
        "threads": 4,
        "saturation": {"records": 100000},
        "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    within = report["noise_floor"]["within_run"]
    assert within["value"] is None
    assert within["provenance"] == "no-matching-env-record"
    assert within["source"] is None
    assert within["search"]["candidate_files"] == []
    assert within["search"]["contract_pin"]["status"] == "pin-file-missing"
    assert within["search"]["contract_pin"]["within_run_exclusion"] == (
        "self-inconsistent-calibration"
    )
    missing_search = report["noise_floor"]["between_run"]["search"][
        "contract_pin"
    ]
    assert missing_search["status"] == "pin-file-missing"
    assert missing_search["path"] == authorization.contract.calibration_ref.path
    assert missing_search["sha256"] == (
        authorization.contract.calibration_ref.sha256
    )


def test_floor_protocol_basis_distinguishes_receipt_from_producer_genome():
    receipt_protocol, receipt_basis = layer3_report._floor_protocol_and_basis(
        {
            "genome": "mocc|BACK_OFF=0,KEY_SORT=1,TEMPERATURE_RESET_OPT=0",
            "acquisition_receipt": {"ccbench": {"build_argv": []}},
        },
        "within_run",
        Path("certified-mocc.json"),
    )
    producer_protocol, producer_basis = layer3_report._floor_protocol_and_basis(
        {"genome": "silo|BACK_OFF=0,WAL=0"},
        "between_run",
        Path("between-run-silo.json"),
    )

    assert receipt_protocol == "mocc"
    assert receipt_basis == "receipt-derived-build-argv"
    assert producer_protocol == "silo"
    assert producer_basis == "canonical-floor-genome"


def test_report_projects_both_nonlegacy_protocol_match_bases(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB,
        protocol="mocc",
    )
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    (calibration / "certified-mocc.json").write_text(json.dumps({
        "records": 100000,
        "threads": 4,
        "workload": YCSB,
        "genome": "mocc|BACK_OFF=0,KEY_SORT=1,TEMPERATURE_RESET_OPT=0",
        "acquisition_receipt": {"ccbench": {"build_argv": []}},
        "noise_floor": {"cv": 0.03},
    }), encoding="utf-8")
    (calibration / "between-mocc.json").write_text(json.dumps({
        "schema_version": "between-run-noise-floor/v1",
        "records": 100000,
        "threads": 4,
        "workload": YCSB,
        "genome": "mocc|BACK_OFF=0,KEY_SORT=1,TEMPERATURE_RESET_OPT=0",
        "between_run": {"cv": 0.04},
    }), encoding="utf-8")

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["noise_floor"]["within_run"]["value"] == {"cv": 0.03}
    assert report["noise_floor"]["within_run"]["protocol_match_basis"] == (
        "receipt-derived-build-argv"
    )
    assert report["noise_floor"]["between_run"]["value"] == {"cv": 0.04}
    assert report["noise_floor"]["between_run"]["protocol_match_basis"] == (
        "canonical-floor-genome"
    )


@pytest.mark.parametrize("genome", [
    pytest.param(_UNSET, id="missing"),
    pytest.param(None, id="null"),
    pytest.param(7, id="non-string"),
    pytest.param("mocc", id="missing-separator"),
    pytest.param("|BACK_OFF=0", id="empty-protocol"),
    pytest.param("mocc|garbage", id="missing-assignment"),
    pytest.param("silo|B=x", id="non-integer"),
    pytest.param("silo|Z=1,A=0", id="unsorted"),
    pytest.param("silo|A=1,A=2", id="duplicate-name"),
    pytest.param("silo|", id="empty-body"),
])
def test_between_run_floor_rejects_missing_or_malformed_genome(tmp_path, genome):
    calibration = tmp_path / "calibration"
    calibration.mkdir()
    document = {
        "records": 100000,
        "threads": 4,
        "workload": YCSB,
        "between_run": {"cv": 0.02},
    }
    if genome is not _UNSET:
        document["genome"] = genome
    (calibration / "between.json").write_text(
        json.dumps(document), encoding="utf-8",
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="genome"):
        layer3_report._calibration_floors(
            calibration, 100000, 4, YCSB, protocol="mocc",
        )


def test_existing_report_without_floor_protocol_remains_schema_valid(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        protocol="silo",
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    for floor in report["noise_floor"].values():
        floor.pop("protocol", None)
    layer3_report._validate_schema(report)


def test_schema_rejects_non_string_floor_protocol(tmp_path):
    campaign, output_root = _campaign(
        tmp_path,
        [_record("build_start", genome="g", src_token="s")],
        protocol="silo",
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["noise_floor"]["within_run"]["protocol"] = False
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_duplicate_matching_floor_of_same_kind_fails_closed(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB, protocol="silo")
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    for name, cv in (("first.json", 0.01), ("second.json", 0.02)):
        (calibration / name).write_text(json.dumps({
            "records": 100000, "threads": 4, "workload": YCSB,
            "noise_floor": {"cv": cv},
        }), encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="within_run.*複数"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_floor_candidate_without_workload_fails_closed(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
        ycsb=YCSB, protocol="silo")
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    (calibration / "broken.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="workload dict"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)


def test_campaign_without_ycsb_has_honest_null_for_both_floor_kinds(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True, exist_ok=True)
    (calibration / "within.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")
    (calibration / "between.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "genome": "silo|BACK_OFF=0",
        "between_run": {"max_delta_pct": 2.0},
    }), encoding="utf-8")
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    for kind in ("within_run", "between_run"):
        floor = report["noise_floor"][kind]
        assert floor["value"] is None
        assert floor["provenance"] == "no-matching-env-record"
        assert floor["source"] is None
        assert floor["search"]["campaign_has_no_ycsb"] is True


def test_schema_rejects_inconsistent_floor_result_correlation(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    report["noise_floor"]["within_run"]["search"] = None
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_abort_event_renders_abort_view_and_commit_absent_reject(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", "aborted", genome="g", src_token="s"),
        _record("abort", "aborted", reason="build-error"),
    ])
    out = tmp_path / "report.json"
    report = layer3_report.render(
        campaign, out, generated_from_head="fixed", output_root=output_root)
    assert out.is_file()
    assert report["aborts"] == [{
        "variant": ABORTED_FIXTURE_VARIANT,
        "reason": "build-error",
        "source_ref": report["aborts"][0]["source_ref"],
    }]
    assert report["aborts"][0]["source_ref"] in report["source_refs"]
    assert report["rejects"][0]["variant"] == ABORTED_FIXTURE_VARIANT
    assert report["rejects"][0]["reason"] == "commit-event-absent"


def test_existing_output_fails_closed(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    out = tmp_path / "exists.json"
    out.write_text("already here", encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="既に存在"):
        layer3_report.render(campaign, out, generated_from_head="fixed", output_root=output_root)


def test_write_report_atomic_converts_existing_output_link_collision(
    tmp_path: Path,
) -> None:
    out = tmp_path / "already-exists.json"
    original = b"already here\n"
    out.write_bytes(original)

    with pytest.raises(layer3_report.Layer3ReportError) as exc_info:
        layer3_report._write_report_atomic(out, {"kind": "collision"})

    assert str(exc_info.value) == f"出力先が既に存在する: {out}"
    assert out.read_bytes() == original


def test_write_report_atomic_rejects_missing_parent_directory(
    tmp_path: Path,
) -> None:
    out = tmp_path / "missing-parent" / "report.json"

    with pytest.raises(layer3_report.Layer3ReportError) as exc_info:
        layer3_report._write_report_atomic(out, {"kind": "missing-parent"})

    assert str(exc_info.value) == (
        f"出力先 parent directory が存在しない: {out.parent}"
    )
    assert not out.exists()
    assert not out.parent.exists()


def test_render_accepted_existing_output_fails_before_builder(
    tmp_path: Path, monkeypatch,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    out = tmp_path / "exists-accepted.json"
    out.write_text("already here", encoding="utf-8")
    called = False

    def fail_builder(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("builder must not run for an existing output")

    monkeypatch.setattr(layer3_report, "build_accepted_report", fail_builder)
    with pytest.raises(layer3_report.Layer3ReportError, match="既に存在"):
        layer3_report.render_accepted(
            campaign,
            out,
            acceptance_receipt=object(),
            generated_from_head="fixed",
            output_root=output_root,
        )

    assert called is False
    assert out.read_text(encoding="utf-8") == "already here"


@pytest.mark.parametrize("first", ["render", "render_accepted"])
def test_render_and_render_accepted_race_rejects_second_writer(
    tmp_path: Path, monkeypatch, first: str,
) -> None:
    campaign, output_root = _certifying_campaign(tmp_path)
    verified = _certifying_receipt_for(campaign)
    monkeypatch.setattr(
        layer3_report.s8c_acceptance_receipt,
        "require_current_verified_receipt",
        lambda _receipt: verified,
    )
    out = tmp_path / "shared-report.json"

    if first == "render":
        layer3_report.render(
            campaign, out, generated_from_head="fixed", output_root=output_root,
        )
    else:
        layer3_report.render_accepted(
            campaign,
            out,
            acceptance_receipt=object(),
            generated_from_head="fixed",
            output_root=output_root,
        )
    original = out.read_bytes()

    with pytest.raises(layer3_report.Layer3ReportError, match="出力先が既に存在する"):
        if first == "render":
            layer3_report.render_accepted(
                campaign,
                out,
                acceptance_receipt=object(),
                generated_from_head="fixed",
                output_root=output_root,
            )
        else:
            layer3_report.render(
                campaign,
                out,
                generated_from_head="fixed",
                output_root=output_root,
            )

    assert out.read_bytes() == original


def test_variant_without_commit_is_reject_with_primary_reference(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", "rejected", genome="g", src_token="s"), _bench("rejected"),
    ])
    report = layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert report["rejects"][0]["variant"] == REJECTED_FIXTURE_VARIANT
    assert report["rejects"][0]["reason"] == "commit-event-absent"
    assert report["rejects"][0]["source_ref"] in report["source_refs"]


@pytest.mark.parametrize("section", ["variants", "runs", "verifications", "rejects", "aborts", "whiteboard"])
def test_schema_rejects_empty_material_items(section, tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report[section] = [{}]
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_git_head_is_real_repository_head():
    head = layer3_report._git_head(ROOT)
    assert len(head) == 40
    assert all(char in "0123456789abcdef" for char in head)


def test_external_v2_campaign_uses_lock_authority_for_build_and_render(
    tmp_path, monkeypatch,
):
    expected = "b" * 40
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    _assert_external_campaign_without_git_head(campaign)
    assert layer3_report._git_head(
        layer3_report._DEFAULT_OUTPUT_ROOT.parent,
    ) != expected
    admitted = layer3_report.require_admitted_campaign(
        campaign,
        purpose=layer3_report.CampaignReadPurpose.HISTORICAL_RAW,
    )
    lock_path = campaign / "campaign.lock"
    identity_preimage = campaign_lock.decode_campaign_lock(
        lock_path.read_text(encoding="utf-8")
    ).identity_preimage
    v2_text = build_v2_campaign_lock(
        identity_preimage, contract_loader_commit=expected,
    )
    lock_path.write_text(v2_text, encoding="utf-8")
    admitted = dataclasses.replace(
        admitted,
        decision=dataclasses.replace(
            admitted.decision,
            campaign_lock_sha256=hashlib.sha256(
                v2_text.encode("utf-8")
            ).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        layer3_report,
        "require_admitted_campaign",
        lambda _path, *, purpose: admitted,
    )
    decoded_lock = campaign_lock.decode_campaign_lock(
        lock_path.read_text(encoding="utf-8")
    )
    assert decoded_lock.authority is not None
    assert decoded_lock.authority.contract_loader_commit == expected

    built = layer3_report.build_report(campaign, output_root=output_root)
    out = tmp_path / "external-v2-layer3.json"
    rendered = layer3_report.render(campaign, out, output_root=output_root)

    assert built["meta"]["generated_from_head"] == expected
    assert rendered["meta"]["generated_from_head"] == expected


def test_git_backed_campaign_head_precedes_v2_lock_authority(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    repo = output_root.parent
    assert subprocess.run(
        ["git", "-C", str(repo), "init", "-q"], check=False,
    ).returncode == 0
    for key, value in (
        ("user.email", "fixture@example.invalid"),
        ("user.name", "Fixture"),
    ):
        assert subprocess.run(
            ["git", "-C", str(repo), "config", key, value], check=False,
        ).returncode == 0
    assert subprocess.run(
        ["git", "-C", str(repo), "add", "-A"], check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "campaign"],
        check=False,
    ).returncode == 0
    head = subprocess.check_output(
        ["git", "-C", str(campaign), "rev-parse", "HEAD"], text=True,
    ).strip()
    decoded_lock = campaign_lock.decode_campaign_lock(
        (campaign / "campaign.lock").read_text(encoding="utf-8")
    )
    assert decoded_lock.authority is not None
    assert head != decoded_lock.authority.contract_loader_commit

    report = layer3_report.build_report(campaign, output_root=output_root)

    assert report["meta"]["generated_from_head"] == head


def test_source_repo_internal_git_failure_does_not_use_lock_authority(
    tmp_path, monkeypatch,
):
    campaign, _output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    decoded_lock = campaign_lock.decode_campaign_lock(
        (campaign / "campaign.lock").read_text(encoding="utf-8")
    )
    assert decoded_lock.authority is not None
    original = layer3_report.Layer3ReportError("git failure sentinel")

    def fail_git_head(_campaign_dir):
        raise original

    monkeypatch.setattr(layer3_report, "_git_head", fail_git_head)
    source_campaign = layer3_report._DEFAULT_OUTPUT_ROOT.parent / "campaign"
    with pytest.raises(layer3_report.Layer3ReportError) as caught:
        layer3_report._resolve_generated_from_head(
            source_campaign, decoded_lock, None,
        )
    assert caught.value is original


def test_source_repo_external_v1_without_authority_stays_fail_closed(
    tmp_path, monkeypatch,
):
    campaign, _output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    _assert_external_campaign_without_git_head(campaign)
    decoded_v2 = campaign_lock.decode_campaign_lock(
        (campaign / "campaign.lock").read_text(encoding="utf-8")
    )
    decoded_v1 = campaign_lock.decode_campaign_lock(decoded_v2.identity_preimage)
    assert decoded_v1.authority is None
    original = layer3_report.Layer3ReportError("git failure sentinel")

    def fail_git_head(_campaign_dir):
        raise original

    monkeypatch.setattr(layer3_report, "_git_head", fail_git_head)
    with pytest.raises(layer3_report.Layer3ReportError) as caught:
        layer3_report._resolve_generated_from_head(campaign, decoded_v1, None)
    assert caught.value is original


def test_explicit_generated_from_head_still_wins(tmp_path, monkeypatch):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )

    def unexpected_git_head(_campaign_dir):
        raise AssertionError("explicit generated_from_head must bypass Git")

    monkeypatch.setattr(layer3_report, "_git_head", unexpected_git_head)
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["meta"]["generated_from_head"] == "fixed"


def test_campaign_outside_repo_fails_closed(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(layer3_report.Layer3ReportError, match="repo 外"):
        layer3_report.build_report(outside, generated_from_head="fixed")


def test_main_accepts_external_campaign_with_output_root(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    out_cli = tmp_path / "cli-report.json"
    out_api = tmp_path / "api-report.json"
    generated_from_head = "f" * 40

    result = layer3_report.main([
        str(campaign),
        str(out_cli),
        "--generated-from-head",
        generated_from_head,
        "--output-root",
        str(output_root),
    ])

    assert result == 0
    assert out_cli.is_file()
    cli_report = json.loads(out_cli.read_text(encoding="utf-8"))
    assert cli_report["meta"]["campaign_path"] == (
        campaign.relative_to(output_root.parent).as_posix()
    )

    layer3_report.render(
        campaign,
        out_api,
        generated_from_head=generated_from_head,
        output_root=output_root,
    )
    assert out_cli.read_bytes() == out_api.read_bytes()


def test_main_without_output_root_preserves_external_campaign_rejection(
    tmp_path, capsys,
):
    campaign, _output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    out = tmp_path / "rejected-report.json"

    with pytest.raises(SystemExit) as exc_info:
        layer3_report.main([
            str(campaign),
            str(out),
            "--generated-from-head",
            "f" * 40,
        ])

    assert exc_info.value.code == 2
    assert "repo 外" in capsys.readouterr().err
    assert not out.exists()


def test_main_forwards_output_root_and_keeps_none_default(monkeypatch):
    calls = []

    def fake_render(
        campaign_dir, out_json, generated_from_head=None, *, output_root=None,
    ):
        calls.append((campaign_dir, out_json, generated_from_head, output_root))
        return {}

    monkeypatch.setattr(layer3_report, "render", fake_render)

    assert layer3_report.main([
        "campaign",
        "report.json",
        "--generated-from-head",
        "head",
    ]) == 0
    assert layer3_report.main([
        "campaign-2",
        "report-2.json",
        "--generated-from-head",
        "head-2",
        "--output-root",
        "relative-root",
    ]) == 0

    assert calls == [
        (Path("campaign"), Path("report.json"), "head", None),
        (Path("campaign-2"), Path("report-2.json"), "head-2", Path("relative-root")),
    ]


def test_main_rejects_external_campaign_with_nonmatching_output_root(
    tmp_path, capsys,
):
    campaign, _output_root = _campaign(
        tmp_path / "source",
        [_record("build_start", genome="g", src_token="s")],
    )
    output_root = tmp_path / "different" / "output"
    out = tmp_path / "nonmatching-report.json"

    with pytest.raises(SystemExit) as exc_info:
        layer3_report.main([
            str(campaign),
            str(out),
            "--generated-from-head",
            "f" * 40,
            "--output-root",
            str(output_root),
        ])

    assert exc_info.value.code == 2
    assert "repo 外" in capsys.readouterr().err
    assert not out.exists()


def test_output_root_relative_path_is_cwd_dependent(tmp_path, monkeypatch):
    calls = []

    def fake_render(
        campaign_dir, out_json, generated_from_head=None, *, output_root=None,
    ):
        calls.append((Path.cwd(), campaign_dir, out_json, output_root))
        return {}

    monkeypatch.setattr(layer3_report, "render", fake_render)
    first_cwd = tmp_path / "first-cwd"
    second_cwd = tmp_path / "second-cwd"
    first_cwd.mkdir()
    second_cwd.mkdir()

    for cwd in (first_cwd, second_cwd):
        monkeypatch.chdir(cwd)
        assert layer3_report.main([
            "campaign",
            "report.json",
            "--generated-from-head",
            "f" * 40,
            "--output-root",
            "output",
        ]) == 0

    assert [call[0] for call in calls] == [first_cwd, second_cwd]
    assert [call[3] for call in calls] == [Path("output"), Path("output")]
    assert [call[0] / call[3] for call in calls] == [
        first_cwd / "output",
        second_cwd / "output",
    ]


def test_output_root_does_not_shrink_qualification_ancestry_walk(
    tmp_path, monkeypatch,
):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    fake_repo_root = output_root.parent
    monkeypatch.setattr(
        layer3_report, "_DEFAULT_OUTPUT_ROOT", output_root,
    )
    (fake_repo_root / "qualification-marker.json").write_text(
        json.dumps({
            "schema_version": "t126-qualification-marker/v1",
            "qualification_lineage": "t126-only",
        }),
        encoding="utf-8",
    )

    with pytest.raises(layer3_report.Layer3ReportError, match="qualification"):
        layer3_report.build_report(
            campaign,
            generated_from_head="fixed",
            output_root=output_root / "campaigns",
        )


def test_external_campaign_qualification_ancestry_still_checked(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    _assert_external_campaign_without_git_head(campaign)
    (output_root.parent / "qualification-marker.json").write_text(
        json.dumps({
            "schema_version": "t126-qualification-marker/v1",
            "qualification_lineage": "t126-only",
        }),
        encoding="utf-8",
    )

    with pytest.raises(layer3_report.Layer3ReportError, match="qualification"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )


def test_output_root_inside_campaign_is_rejected(tmp_path):
    campaign, _output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    _assert_external_campaign_without_git_head(campaign)

    with pytest.raises(
        layer3_report.Layer3ReportError, match="qualification-ancestry",
    ):
        layer3_report.build_report(
            campaign,
            generated_from_head="fixed",
            output_root=campaign / "runs",
        )


def test_main_rejects_empty_output_root(tmp_path, monkeypatch):
    campaign, _output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    out = tmp_path / "empty-root-report.json"
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        layer3_report.main([
            str(campaign),
            str(out),
            "--generated-from-head",
            "f" * 40,
            "--output-root",
            "",
        ])

    assert exc_info.value.code == 2
    assert not out.exists()


# AO material reporting: all fixtures are temporary campaigns, never output/.
def _ao_envelope(stage, *, variant=None, refs=(), label="one"):
    output = {"proposal": label}
    if stage == "critic_attributed":
        sections = {"attribution": "帰属 " + label, "recommend": "retain",
                    "avoid": "infer", "uncertainty": "unknown"}
        output = {"raw_markdown": "\n\n".join(
            "## " + name + "\n" + value for name, value in sections.items()
        ) + "\n", **sections}
    payload = {"output": output, "input_sha256": "1" * 64,
               "provenance": {"mode": "ingested", "source_path": "role.json",
                              "source_sha256": "2" * 64, "input_path": "input.json",
                              "input_file_sha256": "3" * 64}, "refs": list(refs)}
    if stage == "critic_attributed":
        payload["digest_sha256"] = "4" * 64
    return {"ts": 1.0, "stage": stage, "variant": variant,
            "env_tag": "linux-baremetal", "payload": payload}


def _ao_campaign(tmp_path, *, second_critic=False):
    from orchestrator.campaign import agent_outputs
    campaign, output_root = _certifying_campaign(tmp_path)
    records = layer3_report._read_wal(campaign / "runs/wal.jsonl")
    commit = next(record for record in records if record["stage"] == "commit")
    envelopes = [_ao_envelope(stage) for stage in agent_outputs.STAGES[:2]]
    for label in (["one", "two"] if second_critic else ["one"]):
        envelopes.append(_ao_envelope(
            "critic_attributed", variant=commit["variant"], label=label,
            refs=[layer3_report.canonical_record_ref("wal", commit)],
        ))
    for env in envelopes:
        agent_outputs.append_agent_output(campaign / "runs/agent_outputs.jsonl", env)
    report = layer3_report.build_report(campaign, "fixed", output_root=output_root)
    return campaign, output_root, records, envelopes, report


def _ao_check(records, envelopes, report):
    layer3_report._assert_bijection(records, [], report, agent_outputs=envelopes)


def _ao_resync_refs(report):
    report["source_refs"] = sorted(layer3_report._report_primary_refs(report).elements())


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_ao_cli_critic_sections_render(tmp_path, fence):
    from orchestrator.campaign import agent_outputs, p3_s4_loop as loop
    campaign, output_root = _certifying_campaign(tmp_path)
    record = layer3_report._read_wal(campaign / "runs/wal.jsonl")[0]
    digest = campaign / "s4_loop_digest.txt"
    digest.write_bytes(b"fixture digest\n")
    declared = tmp_path / "critic-input.json"
    declared.write_text(json.dumps({"digest_sha256": hashlib.sha256(digest.read_bytes()).hexdigest()}))
    body = "exact text\r\n" + fence + "python\r\n## attribution\r\n" + fence + "\r\nline two"
    raw = ("## attribution  \r\n\r\n  " + body + "  \r\n## \r\nother\r\n"
           "## recommend\r\nnext\r\n## avoid\r\nnone\r\n## uncertainty\r\nunknown\r\n")
    source = tmp_path / "critic.md"
    source.write_bytes(raw.encode())
    # CLI invokes the real _critic_agent_output and durable AO writer.
    assert loop.main(["--record-agent-output", "critic_attributed", str(source),
                      "--agent-campaign-dir", str(campaign), "--agent-input", str(declared),
                      "--agent-variant", record["variant"], "--agent-digest", str(digest)]) == 0
    saved = agent_outputs.read_agent_outputs(campaign / "runs/agent_outputs.jsonl")[0]
    assert saved["payload"]["output"] == {"raw_markdown": raw, "attribution": body,
                                         "recommend": "next", "avoid": "none", "uncertainty": "unknown"}
    report = layer3_report.build_report(campaign, "fixed", output_root=output_root)
    assert report["mechanism_hypotheses"][0]["attribution"] == body


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_ao_fenced_only_critic_rejected(tmp_path, fence):
    from orchestrator.campaign import agent_outputs
    campaign, output_root = _certifying_campaign(tmp_path)
    record = layer3_report._read_wal(campaign / "runs/wal.jsonl")[0]
    env = _ao_envelope("critic_attributed", variant=record["variant"])
    output = env["payload"]["output"]
    output["raw_markdown"] = fence + "\n" + output["raw_markdown"] + fence + "\n"
    agent_outputs.append_agent_output(campaign / "runs/agent_outputs.jsonl", env)
    with pytest.raises(layer3_report.Layer3ReportError, match="heading"):
        layer3_report.build_report(campaign, "fixed", output_root=output_root)


@pytest.mark.parametrize("stage", ["planner_proposed", "coder_proposed", "critic_attributed"])
def test_ao_all_stages_accept_abort_variant(stage):
    envelope = _ao_envelope(stage, variant="aborted")
    view = layer3_report._mechanism_view([_record("abort", "aborted")], [envelope])
    assert len(view) == (1 if stage == "critic_attributed" else 0)


def test_ao_ingested_abort_variant_render(tmp_path):
    from orchestrator.campaign import p3_s4_loop as loop
    campaign, output_root = _campaign(tmp_path, [_record("abort", reason="fixture abort")])
    source = tmp_path / "planner.json"
    source.write_text(json.dumps({"proposal": {"axis": "a", "direction": "increase",
        "magnitude": "small", "justification": "j", "uncertainty": "u"}}))
    declared = tmp_path / "planner-input.json"
    declared.write_text(json.dumps({"current_perf": {}, "leading_indicators": {}, "whiteboard": []}))
    assert loop.main(["--record-agent-output", "planner_proposed", str(source),
                      "--agent-campaign-dir", str(campaign), "--agent-input", str(declared),
                      "--agent-variant", "v1"]) == 0
    report = layer3_report.build_report(campaign, "fixed", output_root=output_root)
    assert report["agent_outputs"][0]["variant"] == "v1"


def test_ao_canonical_bytes_and_three_stage_report(tmp_path):
    from orchestrator.campaign import agent_outputs
    campaign, _, records, envelopes, report = _ao_campaign(tmp_path)
    for env in envelopes:
        assert layer3_report._canonical_bytes(env) == agent_outputs.canonical_bytes(env)
        assert layer3_report.canonical_record_ref("ao", env) == agent_outputs.envelope_ref(env)
    assert len(report["agent_outputs"]) == 3
    assert len(report["mechanism_hypotheses"]) == 1
    assert len([ref for ref in report["source_refs"] if ref.startswith("ao:")]) == 3
    assert report["agent_outputs"] == sorted(envelopes, key=agent_outputs.envelope_ref)
    critic = envelopes[-1]
    assert report["mechanism_hypotheses"] == [{
        "variant": critic["variant"], "attribution": critic["payload"]["output"]["attribution"],
        "source_ref": agent_outputs.envelope_ref(critic),
        "refs": critic["payload"]["refs"], "digest_sha256": "4" * 64,
    }]
    assert report["mechanism_hypotheses_provenance"] == "agent_outputs"
    artifact = next(ref for ref in report["artifact_refs"] if ref["path"] == "runs/agent_outputs.jsonl")
    assert artifact["sha256"] == hashlib.sha256((campaign / artifact["path"]).read_bytes()).hexdigest()
    layer3_report._validate_schema(report)
    _ao_check(records, envelopes, report)


@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("loop_state", [False, True])
def test_ao_absent_and_empty_independent_of_whiteboard(tmp_path, empty, loop_state):
    campaign, output_root = _campaign(tmp_path, [_bench()], loop_state=loop_state)
    if empty:
        (campaign / "runs/agent_outputs.jsonl").touch()
    report = layer3_report.build_report(campaign, "fixed", output_root=output_root)
    assert report["agent_outputs"] == report["mechanism_hypotheses"] == []
    assert report["mechanism_hypotheses_provenance"] == ("agent_outputs" if empty else "absent")
    layer3_report._validate_schema(report)
    _ao_check(layer3_report._read_wal(campaign / "runs/wal.jsonl"), [] if empty else None, report)


@pytest.mark.parametrize("bad", ["symlink", "directory", "partial", "invalid", "stage", "duplicate"])
def test_ao_bad_file_rejected(tmp_path, bad):
    from orchestrator.campaign import agent_outputs
    campaign, output_root = _campaign(tmp_path, [_bench()], loop_state=False)
    path = campaign / "runs/agent_outputs.jsonl"
    env = _ao_envelope("planner_proposed")
    if bad == "symlink":
        path.symlink_to("absent.jsonl")
    elif bad == "directory":
        path.mkdir()
    else:
        agent_outputs.append_agent_output(path, env)
        if bad == "stage":
            env["stage"] = "unknown"
        suffix = {"partial": b'{', "invalid": b'{bad}\n',
                  "stage": agent_outputs.canonical_bytes(env) + b'\n',
                  "duplicate": agent_outputs.canonical_bytes(env) + b'\n'}[bad]
        with path.open("ab") as stream:
            stream.write(suffix)
    with pytest.raises(layer3_report.Layer3ReportError):
        layer3_report.build_report(campaign, "fixed", output_root=output_root)


def test_ao_missing_planner_coder_even_with_source_refs_removed(tmp_path):
    _, _, records, envelopes, report = _ao_campaign(tmp_path)
    report["agent_outputs"] = [env for env in report["agent_outputs"] if env["stage"] == "critic_attributed"]
    _ao_resync_refs(report)
    with pytest.raises(layer3_report.Layer3ReportError, match="multiset"):
        _ao_check(records, envelopes, report)


def test_ao_view_counted_as_primary_is_rejected(tmp_path, monkeypatch):
    _, _, records, envelopes, report = _ao_campaign(tmp_path)
    original = layer3_report._report_primary_refs
    def polluted(value):
        refs = original(value)
        refs.update(row["source_ref"] for row in value["mechanism_hypotheses"])
        return refs
    monkeypatch.setattr(layer3_report, "_report_primary_refs", polluted)
    _ao_resync_refs(report)
    with pytest.raises(layer3_report.Layer3ReportError, match="multiset"):
        _ao_check(records, envelopes, report)


def test_ao_equal_count_valid_replacement_is_rejected(tmp_path):
    from orchestrator.campaign import agent_outputs
    _, _, records, envelopes, report = _ao_campaign(tmp_path)
    replacement = _ao_envelope("planner_proposed", label="replacement")
    agent_outputs.validate_envelope(replacement)
    report["agent_outputs"] = [replacement if env["stage"] == "planner_proposed" else env
                               for env in report["agent_outputs"]]
    _ao_resync_refs(report)
    layer3_report._validate_schema(report)
    with pytest.raises(layer3_report.Layer3ReportError, match="multiset"):
        _ao_check(records, envelopes, report)


def test_ao_two_critic_view_ref_swap_rejected(tmp_path):
    _, _, records, envelopes, report = _ao_campaign(tmp_path, second_critic=True)
    a, b = report["mechanism_hypotheses"]
    a["source_ref"], b["source_ref"] = b["source_ref"], a["source_ref"]
    report["mechanism_hypotheses"].sort(key=lambda row: row["source_ref"])
    with pytest.raises(layer3_report.Layer3ReportError, match="独立再射影"):
        _ao_check(records, envelopes, report)


def test_ao_attribution_one_character_change_rejected(tmp_path):
    _, _, records, envelopes, report = _ao_campaign(tmp_path)
    report["mechanism_hypotheses"][0]["attribution"] += "!"
    with pytest.raises(layer3_report.Layer3ReportError, match="独立再射影"):
        _ao_check(records, envelopes, report)


@pytest.mark.parametrize("mutation", ["missing", "duplicate"])
def test_ao_view_missing_or_duplicate_rejected(tmp_path, mutation):
    _, _, records, envelopes, report = _ao_campaign(tmp_path)
    report["mechanism_hypotheses"] *= 0 if mutation == "missing" else 2
    with pytest.raises(layer3_report.Layer3ReportError, match="独立再射影"):
        _ao_check(records, envelopes, report)


def test_ao_absent_provenance_lie_rejected(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_bench()])
    report = layer3_report.build_report(campaign, "fixed", output_root=output_root)
    report["mechanism_hypotheses_provenance"] = "agent_outputs"
    with pytest.raises(layer3_report.Layer3ReportError, match="provenance"):
        _ao_check(layer3_report._read_wal(campaign / "runs/wal.jsonl"), None, report)


@pytest.mark.parametrize("mutation", ["refs", "variant", "planner_variant", "coder_variant",
                                      "raw", "missing_heading", "duplicate_heading"])
def test_ao_invalid_attribution_input_rejected(tmp_path, mutation):
    from orchestrator.campaign import agent_outputs
    campaign, output_root, _, envelopes, _ = _ao_campaign(tmp_path)
    critic = envelopes[-1]
    if mutation == "refs":
        critic["payload"]["refs"] = ["wal:" + "f" * 64]
    elif mutation == "variant":
        critic["variant"] = "absent"
    elif mutation in {"planner_variant", "coder_variant"}:
        envelopes[0 if mutation == "planner_variant" else 1]["variant"] = "absent"
    elif mutation == "raw":
        critic["payload"]["output"]["attribution"] += "!"
    elif mutation == "missing_heading":
        critic["payload"]["output"]["raw_markdown"] = critic["payload"]["output"]["raw_markdown"].replace("## avoid", "## other")
    else:
        critic["payload"]["output"]["raw_markdown"] += "\n## attribution\nextra\n"
    path = campaign / "runs/agent_outputs.jsonl"
    path.unlink()
    for env in envelopes:
        agent_outputs.append_agent_output(path, env)
    with pytest.raises(layer3_report.Layer3ReportError):
        layer3_report.build_report(campaign, "fixed", output_root=output_root)


def test_ao_artifact_snapshot_change_rejected(tmp_path, monkeypatch):
    from orchestrator.campaign import agent_outputs
    campaign, output_root, _, _, _ = _ao_campaign(tmp_path)
    original = layer3_report._artifact_refs
    def changed(*args, **kwargs):
        agent_outputs.append_agent_output(campaign / "runs/agent_outputs.jsonl",
                                         _ao_envelope("planner_proposed", label="later"))
        return original(*args, **kwargs)
    monkeypatch.setattr(layer3_report, "_artifact_refs", changed)
    with pytest.raises(layer3_report.Layer3ReportError, match="bytes changed"):
        layer3_report.build_report(campaign, "fixed", output_root=output_root)


def _verification_producer_payload():
    from orchestrator.verifier.model import ProofSurfaceAssessment
    result = SimpleNamespace(verdict="serializable", certified=True, anomalies=[],
                             integrity=SimpleNamespace(proof_surfaces=ProofSurfaceAssessment()))
    outcome = pipeline._execute_verification_repetition(
        "fixture", "fixture-trace", {}, 1000, timeout_s=1, numactl=None,
        genome=None, source_evidence=None, build_admission=None,
        receipt_sink_kind="fixture", receipt_lock_identity_sha256="0" * 64,
        receipt_variant="v1", receipt_operation_identity="fixture",
        receipt_workload_tag="legacy", build_attempt_id="fixture-attempt-0",
        trace_binary_sha256="0" * 64, include_qualification_evidence=False,
        trace_runner=lambda *a, **kw: SimpleNamespace(
            trace_c_lines=1, returncode=0, abort_counts=0,
            commit_count_witness=1, batch_commit_count_witness=0),
        verifier_runner=lambda *a, **kw: (result, object()),
    )
    assert outcome.abort is None
    return outcome.verify_payload


def _literal_dict_keys(node):
    assert isinstance(node, ast.Dict), "unknown non-literal dictionary"
    assert all(isinstance(key, ast.Constant) and isinstance(key.value, str)
               for key in node.keys), "unknown dynamic key or unpack"
    return {key.value for key in node.keys}


def _verification_mutation_keys(function):
    """Fail closed on every use of verify_payload except known writes/export."""
    parents = {child: node for node in ast.walk(function)
               for child in ast.iter_child_nodes(node)}
    declarations = []
    keys = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Name) or node.id != "verify_payload":
            continue
        parent = parents[node]
        if isinstance(parent, ast.AnnAssign) and parent.target is node:
            declarations.append(parent)
            keys.update(_literal_dict_keys(parent.value))
        elif isinstance(parent, ast.Attribute) and parent.value is node:
            call = parents[parent]
            assert (parent.attr == "update" and isinstance(call, ast.Call)
                    and call.func is parent and len(call.args) == 1
                    and not call.keywords
                    and isinstance(parents[call], ast.Expr)), "unknown mutator"
            keys.update(_literal_dict_keys(call.args[0]))
        elif isinstance(parent, ast.Subscript) and parent.value is node:
            assignment = parents[parent]
            assert (isinstance(assignment, ast.Assign)
                    and assignment.targets == [parent]), "unknown subscript use"
            key = parent.slice
            assert isinstance(key, ast.Constant) and isinstance(key.value, str)
            keys.add(key.value)
        elif isinstance(parent, ast.keyword) and parent.arg == "verify_payload":
            call = parents[parent]
            assert (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "_RepetitionExecutionOutcome"
                    and isinstance(parents[call], ast.Return)), "unknown export"
        else:
            raise AssertionError("unknown alias, rebinding or mutation of verify_payload")
    assert len(declarations) == 1
    return keys


def test_verification_producer_keys_and_schema_closure(tmp_path):
    from orchestrator.verifier.model import ProofSurfaceAssessment
    function = ast.parse(textwrap.dedent(inspect.getsource(
        pipeline._execute_verification_repetition)))
    # _reject_qualification_ancestry / _contains_qualification_lineage exclude
    # qualification lineage from renderer input. Do not widen its acceptance.
    qualification_branches = [node for node in ast.walk(function)
                              if isinstance(node, ast.If)
                              and isinstance(node.test, ast.Name)
                              and node.test.id == "include_qualification_evidence"]
    assert len(qualification_branches) == 1
    assert not qualification_branches[0].orelse
    # Reuse the fail-closed write collector with an empty initial payload.
    qualification_only = _verification_mutation_keys(ast.Module(
        body=[ast.parse("verify_payload: dict = {}").body[0],
              *qualification_branches[0].body], type_ignores=[]))
    assert qualification_only == {"argv", "binary_sha256"}
    gate_branches = [node for node in ast.walk(function)
                     if isinstance(node, ast.If)
                     and isinstance(node.test, ast.Name)
                     and node.test.id == "require_gate_witness"]
    assert len(gate_branches) == 1
    assert not gate_branches[0].orelse
    gate_only = _verification_mutation_keys(ast.Module(
        body=[ast.parse("verify_payload: dict = {}").body[0],
              *gate_branches[0].body], type_ignores=[]))
    assert gate_only == {"gate_witness"}
    view = ast.parse(textwrap.dedent(inspect.getsource(layer3_report._view_row)))
    exclusions = [node for node in ast.walk(view)
                  if isinstance(node, ast.Compare)
                  and isinstance(node.left, ast.Name) and node.left.id == "key"
                  and len(node.ops) == 1 and isinstance(node.ops[0], ast.NotIn)]
    assert len(exclusions) == 1
    literal = exclusions[0].comparators[0]
    assert isinstance(literal, ast.Set)
    assert all(isinstance(key, ast.Constant) and isinstance(key.value, str)
               for key in literal.elts)
    view_only = {key.value for key in literal.elts}
    assert view_only == {"build_attempt_id", "build_admission_receipt_sha256"}
    producer_keys = _verification_mutation_keys(function)
    keys = producer_keys - view_only - qualification_only - gate_only
    payload = _verification_producer_payload()
    assert set(payload) == producer_keys - qualification_only - gate_only
    row = layer3_report._view_row(_record("verify_done", **payload))
    schema = json.loads(layer3_report._SCHEMA_PATH.read_text())
    properties = schema["properties"]["verifications"]["items"]["properties"]
    assert keys <= set(properties)
    assert gate_only <= set(properties)
    assert set(payload) - view_only - qualification_only <= set(properties)
    assert set(row) <= set(properties)
    witness = [node.value for node in ast.walk(function)
               if isinstance(node, ast.Assign) and any(
                   isinstance(target, ast.Name) and target.id == "commit_witness"
                   for target in node.targets)]
    assert len(witness) == 1
    assert _literal_dict_keys(witness[0]) == set(properties["commit_witness"]["properties"])
    proof = ast.parse(textwrap.dedent(inspect.getsource(ProofSurfaceAssessment.as_record)))
    returns = [node.value for node in ast.walk(proof) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    assert _literal_dict_keys(returns[0]) == set(properties["proof_surfaces"]["properties"])
    assert row["commit_witness"] == payload["commit_witness"]
    assert row["proof_surfaces"] == payload["proof_surfaces"]
    records = [_record("build_start"), _record("build_done"),
               _record("verify_done", **payload),
               _bench(build_attempt_id=payload["build_attempt_id"])]
    for ts, record in enumerate(records, 1):
        record["ts"] = float(ts)
    campaign, output_root = _campaign(tmp_path, records)
    report = layer3_report.build_report(campaign, "fixed", output_root=output_root)
    layer3_report._validate_schema(report)
    gated_payload = dict(payload, gate_witness={
        "meaning_version": 2,
        "required": True,
        "counts": {
            "unreachable": 0, "D1a": 0, "D1b1": 0, "D1b2": 0,
            "D1c": 0, "D2a": 0, "D2b_i": 0, "D2b_ii": 0,
        },
        "occurrence": {
            "own_write_read_transactions": 0,
            "written_transactions": 0,
            "repeated_write_key_transactions": 0,
            "external_reads_checked": 0,
        },
        "D5": "pass",
    })
    gated_row = layer3_report._view_row(_record("verify_done", **gated_payload))
    assert gated_row["gate_witness"] == gated_payload["gate_witness"]
    gated_records = [_record("build_start"), _record("build_done"),
                     _record("verify_done", **gated_payload),
                     _bench(build_attempt_id=payload["build_attempt_id"])]
    for ts, record in enumerate(gated_records, 1):
        record["ts"] = float(ts)
    gated_campaign, gated_output_root = _campaign(tmp_path / "with-gate", gated_records)
    gated_report = layer3_report.build_report(
        gated_campaign, "fixed", output_root=gated_output_root)
    assert gated_report["verifications"][0]["gate_witness"] == gated_payload["gate_witness"]
    layer3_report._validate_schema(gated_report)


@pytest.mark.parametrize("mutation", [
    "alias = verify_payload", "verify_payload = {}",
    "verify_payload.clear()", "verify_payload.update(other)",
    "verify_payload[key] = 1", "verify_payload |= {'new': 1}",
    "consume(verify_payload)",
])
def test_verification_closure_unknown_mutation_rejected(mutation):
    tree = ast.parse("verify_payload: dict = {'initial': 1}\n" + mutation)
    with pytest.raises(AssertionError):
        _verification_mutation_keys(tree)


def test_verification_closure_collects_conditional_writes():
    tree = ast.parse("verify_payload: dict = {'initial': 1}\n"
                     "if condition:\n    verify_payload.update({'later': 2})\n"
                     "    verify_payload['last'] = 3\n")
    assert _verification_mutation_keys(tree) == {"initial", "later", "last"}


@pytest.mark.parametrize("mutation", ["null_count", "proof_enum"])
def test_verification_witness_and_proof_invalid_schema(mutation):
    payload = _verification_producer_payload()
    if mutation == "null_count":
        payload["commit_witness"]["commit_counts"] = None
    else:
        payload["proof_surfaces"]["X"] = "invalid"
    report = _knowledge_schema_specimen()
    report["verifications"] = [layer3_report._view_row(_record("verify_done", **payload))]
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_ao_snapshot_change_during_shared_read_rejected(tmp_path, monkeypatch):
    from orchestrator.campaign import agent_outputs
    campaign, output_root, _, _, _ = _ao_campaign(tmp_path)
    original = agent_outputs.read_agent_outputs

    def changed(path):
        result = original(path)
        agent_outputs.append_agent_output(path, _ao_envelope("coder_proposed", label="later"))
        return result

    monkeypatch.setattr(agent_outputs, "read_agent_outputs", changed)
    with pytest.raises(layer3_report.Layer3ReportError, match="bytes changed during read"):
        layer3_report.build_report(campaign, "fixed", output_root=output_root)


def test_ao_read_failure_is_not_absence(tmp_path, monkeypatch):
    from orchestrator.campaign import agent_outputs
    campaign, output_root = _campaign(tmp_path, [_bench()])
    (campaign / "runs/agent_outputs.jsonl").touch()

    def denied(path):
        raise PermissionError("fixture read denied")

    monkeypatch.setattr(agent_outputs, "read_agent_outputs", denied)
    with pytest.raises(layer3_report.Layer3ReportError, match="agent outputs を読めない"):
        layer3_report.build_report(campaign, "fixed", output_root=output_root)
