# -*- coding: utf-8 -*-
"""D12 層3材料レポートの決定論的な完全射影を検査する。"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from types import SimpleNamespace
from pathlib import Path

import jsonschema
import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from orchestrator.campaign import (  # noqa: E402
    artifact_admission,
    autonomous_trial_completeness,
    campaign_lock,
    contract_loader_binding,
    env_contract,
    layer3_report,
    model,
    p3_autonomous_workload_trial,
    p3_s4_loop,
    s8c_acceptance_receipt,
    trigger_gate_binding,
    wal,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402
from orchestrator.campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from orchestrator.calibrator import perf_preflight  # noqa: E402


ROOT = _HERE.parent.parent
REAL_CAMPAIGN = ROOT / "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"
LEGACY_TRIGGER_SWEEP_CAMPAIGN = (
    ROOT / "output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2"
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
        relative: hashlib.sha256(
            contract_loader_binding._blob(root, commit, relative)
        ).hexdigest()
        for relative in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
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


def _admission_bound_records(tmp_path: Path, records: list[dict]) -> tuple[list[dict], dict]:
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
        protocol = f"fixture-{hashlib.sha256(label.encode()).hexdigest()[:8]}"
        canonical = f"{protocol}|"
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
              ycsb=None, policy_hint=_UNSET) -> tuple[Path, Path]:
    output_root = tmp_path / "repo" / "output"
    records, admission_policy = _admission_bound_records(tmp_path, records)
    search_config = {
        "records": 100000,
        "threads": 4,
        "build_admission": admission_policy,
    }
    if ycsb is not None:
        search_config["ycsb"] = ycsb
    if policy_hint is not _UNSET:
        search_config["policy_hint"] = policy_hint
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
        build_v2_campaign_lock(identity_preimage), encoding="utf-8",
    )
    if loop_state:
        (root / "loop_state.json").write_text(
            json.dumps({"whiteboard": whiteboard if whiteboard is not None else []}),
            encoding="utf-8")
    (root / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return root, output_root


def _assert_external_campaign_without_git_head(campaign: Path) -> None:
    resolved = campaign.resolve()
    source_repo = layer3_report._DEFAULT_OUTPUT_ROOT.parent.resolve()
    assert not resolved.is_relative_to(source_repo)
    with pytest.raises(layer3_report.Layer3ReportError):
        layer3_report._git_head(campaign)


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


def _record(stage, variant="v1", **payload):
    return {"ts": 1.0, "stage": stage, "variant": variant, "env_tag": "test-env", "payload": payload}


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
    }
    assert report["certifying_input"] is False


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
        authorization=env_contract.authorize("pegasus"),
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


def test_legacy_v2_report_schema_remains_readable(tmp_path):
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
    layer3_report._validate_schema(legacy)


def test_legacy_v2_without_policy_hint_remains_readable(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    legacy = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    legacy["schema_version"] = "layer3-material-report/v2"
    legacy.pop("policy_hint", None)
    del legacy["admission_decision"]
    del legacy["acceptance_receipt"]
    del legacy["certifying_input"]

    layer3_report._validate_schema(legacy)


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
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = _verified_non_certifying_receipt(campaign, output_root)
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


def test_render_accepted_rejects_non_certifying_receipt_before_write(
    tmp_path: Path,
) -> None:
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    verified = _verified_non_certifying_receipt(campaign, output_root)
    out = tmp_path / "accepted-report.json"

    with pytest.raises(
        layer3_report.Layer3ReportError,
        match="certifying=true でない",
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
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
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
    assert report["acceptance_receipt"] == {
        "path": verified.relative_path,
        "sha256": verified.sha256,
    }


def test_render_accepted_persists_certifying_report(
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
        tmp_path, [_record("build_start", genome="g", src_token="s")], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
    within = {"cv": 0.01, "median": 12.0}
    between = {"max_delta_pct": 2.0}
    (calibration / "within.json").write_text(json.dumps({
        "threads": 4, "saturation": {"records": 100000}, "workload": YCSB,
        "noise_floor": within,
    }), encoding="utf-8")
    (calibration / "between.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
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
        calibration, 100000, 4, YCSB)
    for kind in ("within_run", "between_run"):
        assert search_details[kind]["skipped_no_floor_block"] == ["frequency.json"]


def test_between_run_schema_version_does_not_change_floor_classification(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
    between = {"max_delta_pct": 2.0}
    (calibration / "between.json").write_text(json.dumps({
        "schema_version": "between-run-noise-floor/v1",
        "records": 100000, "threads": 4, "workload": YCSB,
        "between_run": between,
    }), encoding="utf-8")

    floors, details = layer3_report._calibration_floors(
        calibration, 100000, 4, YCSB)
    assert details["between_run"]["candidate_files"] == ["between.json"]
    assert floors["between_run"]["provenance"] == "env-record"
    assert floors["between_run"]["value"] == between

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["noise_floor"]["between_run"]["value"] == between


def test_duplicate_matching_floor_of_same_kind_fails_closed(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
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
        tmp_path, [_record("build_start", genome="g", src_token="s")], ycsb=YCSB)
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
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
    calibration.mkdir(parents=True)
    (calibration / "within.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
        "noise_floor": {"cv": 0.01},
    }), encoding="utf-8")
    (calibration / "between.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "workload": YCSB,
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
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
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
