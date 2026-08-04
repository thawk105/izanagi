# -*- coding: utf-8 -*-
"""Independent sentinels for the T-344 deny-only campaign overlay."""
from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from orchestrator.campaign import artifact_admission as A
from orchestrator.campaign import trigger_gate_binding, wal
from orchestrator.campaign.build_admission import (
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.pin import CURRENT_PIN
from orchestrator.campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, SourceEvidence


ROOT = Path(__file__).resolve().parents[2]
LEDGER_RAW_SHA256 = "f08ed2d0b265710286752cad74c12d1136ea0af7684e810b00e10867a71cef93"
EXPECTED_RECORDS = (
    (
        "output/campaigns/p3-s4-loop-s4-autonomous-0b53a387",
        "p3-s4-loop-s4-autonomous-0b53a387",
        "0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9",
        "2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611",
        3,
    ),
    (
        "output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d",
        "p3-s5-sort-loop-s5-sort-autonomous-3be89e0d",
        "3be89e0ddad8e8b2b37d35168c49affe7889ea580831973dc0d6d9706aaa4f97",
        "b901f23a502e4d3843454de807ca01666c145ee7d9d424a957bb366ef3e793a5",
        1,
    ),
    (
        "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5",
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5",
        "3f72ecd58a6df4018d136bcbb8abb276114ba8d302c64aaf792c473ae4b1de0c",
        "a539648d29afce9be036eba519b53f21fd1f8e1fb7bfe24549f4ec3ceac31ea3",
        2,
    ),
)
KNOWN_HISTORICAL = (
    "output/campaigns/p2-2-silo-balanced-enumerate-f1588056",
    "f15880560640c76223fb7c20ed4f8b1e6d4596ae80c94bdbc55c95d5201a180f",
    "d6e98161d8cc3a011688316c3a180a532c0374c87fbbcc30934106f51f95f34c",
)


def _write_campaign(root: Path, lock: dict, records: list[dict]) -> Path:
    (root / "runs").mkdir(parents=True)
    (root / "campaign.lock").write_text(
        json.dumps(lock, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    (root / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    return root


def _record(stage: str, payload: dict, *, ts: float) -> dict:
    return {
        "variant": "6a803ba39f7b", "stage": stage, "env_tag": "test", "ts": ts,
        "payload": payload,
    }


def _new_schema_campaign(tmp_path: Path, *, omit_receipt: bool = False) -> Path:
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    genome = "silo|BACK_OFF=0"
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
    admission = derive_build_admission(context, evidence)
    receipt = admission.as_wal_receipt()
    attempt_id = "attempt-1"
    start = {
        "build_attempt_id": attempt_id,
        "genome": genome,
        "src_token": "stock",
    }
    if not omit_receipt:
        start.update({
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        })
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
    }
    records = [
        _record("build_start", start, ts=1.0),
        _record("build_done", terminal, ts=2.0),
        _record("commit", terminal, ts=3.0),
    ]
    lock = {
        "ccbench_commit": CURRENT_PIN,
        "search_config": {
            "records": 1,
            "threads": 1,
            "build_admission": dict(context.policy.as_preimage()),
        },
        "search_tag": "test",
        "spec_content": "test",
        "trial": "test",
    }
    return _write_campaign(tmp_path / "campaign", lock, records)


def _classify_as_trigger(
        campaign: Path, *, marker: bool, proposal: bool, binding: bool,
        axis: str = wal.TRIGGER_AXIS,
) -> Path:
    lock_path = campaign / "campaign.lock"
    lock = json.loads(lock_path.read_text())
    search = lock["search_config"]
    search["axis"] = axis
    if proposal:
        search["reflux"] = "on"
    else:
        search.update({
            "generator": "reason-subset-v1",
            "space": "reason-subsets(effective)+identall+stock",
        })
    if marker:
        search[wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY] = trigger_gate_binding.SCHEMA_VERSION
    lock_path.write_text(
        json.dumps(lock, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    if not binding:
        return campaign

    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    start = next(record for record in records if record["stage"] == "build_start")
    source = start["payload"]["build_admission"]["source"]
    value = trigger_gate_binding.TriggerGateBinding(
        mask=9,
        predicate_sha256=trigger_gate_binding.expected_predicate_sha256(9),
        nonce="9" * 64,
        source=trigger_gate_binding.SourceBinding(
            src_token=source["src_token"],
            source_bytes_sha256=source["source_bytes_sha256"],
        ),
    )
    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY] = \
        trigger_gate_binding.commitment(value)
    raw = _record(trigger_gate_binding.WAL_RECORD_STAGE, {
        "build_attempt_id": start["payload"]["build_attempt_id"],
        wal.TRIGGER_BINDING_PAYLOAD_KEY: trigger_gate_binding.to_record(value),
    }, ts=start["ts"] - 0.5)
    raw["variant"] = start["variant"]
    records.insert(records.index(start), raw)
    wal_path.write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    reports = campaign / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "p3_s8a_trigger_loop_provenance.json").write_text(json.dumps({
        "entries": {
            "1": {
                "variant": start["variant"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY:
                    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY],
            },
        },
    }), encoding="utf-8")
    return campaign


def test_overlay_raw_sha_and_exact_membership_are_independently_pinned() -> None:
    raw = A.LEDGER_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == LEDGER_RAW_SHA256
    ledger = json.loads(raw)
    assert len(ledger["records"]) == 3
    actual = tuple(
        (
            record["path"], record["campaign_id"],
            record["campaign_lock_sha256"], record["wal_sha256"],
            record["build_start_count"],
        )
        for record in ledger["records"]
    )
    assert actual == EXPECTED_RECORDS


def test_three_legacy_campaigns_are_denied() -> None:
    for path, campaign_id, lock_sha, wal_sha, count in EXPECTED_RECORDS:
        campaign = ROOT / path
        decision = A.classify_campaign(campaign)
        assert decision.classification == "overlay-denied"
        assert decision.admission_status == "legacy-unclassified"
        assert decision.verification_status == "historically-certified"
        assert decision.campaign_id == campaign_id
        assert decision.campaign_lock_sha256 == lock_sha
        assert decision.wal_sha256 == wal_sha
        assert decision.overlay_ledger_sha256 == LEDGER_RAW_SHA256
        assert count == sum(
            '"stage":"build_start"' in line
            for line in (campaign / "runs/wal.jsonl").read_text().splitlines()
        )
        with pytest.raises(A.CampaignNotAdmitted, match="legacy-unclassified"):
            A.require_admitted_campaign(campaign)


def test_overlay_named_campaign_with_changed_hash_is_tampering_not_fallthrough(
    tmp_path: Path,
) -> None:
    source = ROOT / EXPECTED_RECORDS[2][0]
    copied = tmp_path / EXPECTED_RECORDS[2][1]
    (copied / "runs").mkdir(parents=True)
    (copied / "campaign.lock").write_bytes((source / "campaign.lock").read_bytes())
    (copied / "runs/wal.jsonl").write_bytes(
        (source / "runs/wal.jsonl").read_bytes() + b"\n"
    )
    with pytest.raises(A.OverlayMutationError, match="known overlay campaign"):
        A.classify_campaign(copied)


def test_overlay_exact_bytes_remain_denied_after_relocation(tmp_path: Path) -> None:
    source = ROOT / EXPECTED_RECORDS[0][0]
    copied = tmp_path / "renamed-campaign"
    (copied / "runs").mkdir(parents=True)
    (copied / "campaign.lock").write_bytes((source / "campaign.lock").read_bytes())
    (copied / "runs/wal.jsonl").write_bytes(
        (source / "runs/wal.jsonl").read_bytes()
    )

    decision = A.classify_campaign(copied)
    assert decision.classification == "overlay-denied"
    assert decision.overlay_record_key is not None
    with pytest.raises(A.CampaignNotAdmitted, match="legacy-unclassified"):
        A.require_admitted_campaign(copied)


@pytest.mark.parametrize("mutated_file", ["campaign.lock", "runs/wal.jsonl"])
def test_overlay_invariant_tuple_partial_match_is_tampering(
    tmp_path: Path, mutated_file: str,
) -> None:
    source = ROOT / EXPECTED_RECORDS[1][0]
    copied = tmp_path / "relocated-and-mutated"
    (copied / "runs").mkdir(parents=True)
    (copied / "campaign.lock").write_bytes((source / "campaign.lock").read_bytes())
    (copied / "runs/wal.jsonl").write_bytes(
        (source / "runs/wal.jsonl").read_bytes()
    )
    target = copied / mutated_file
    target.write_bytes(target.read_bytes() + b"\n")

    with pytest.raises(A.OverlayMutationError, match="known overlay campaign"):
        A.classify_campaign(copied)


def test_unlisted_post_policy_campaign_requires_exact_attempt_receipt(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    admitted = A.require_admitted_campaign(campaign)
    assert admitted.decision.classification == "admitted-new-schema"
    assert len(admitted.decision.attempt_receipt_sha256s) == 1


def test_post_policy_trigger_proposal_requires_marker_and_complete_binding(tmp_path: Path) -> None:
    canonical = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "canonical"),
        marker=True, proposal=True, binding=True,
    )
    assert A.classify_campaign(canonical).classification == "admitted-new-schema"

    marker_without_binding = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "missing-binding"),
        marker=True, proposal=True, binding=False,
    )
    with pytest.raises(A.ArtifactAdmissionError, match="一対一"):
        A.classify_campaign(marker_without_binding)

    proposal_without_marker = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "missing-marker"),
        marker=False, proposal=True, binding=False,
    )
    with pytest.raises(A.ArtifactAdmissionError, match="binding marker"):
        A.classify_campaign(proposal_without_marker)


def test_post_policy_trigger_machine_sweep_does_not_require_binding(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=False, proposal=False, binding=False,
    )
    decision = A.classify_campaign(campaign)
    assert decision.classification == "admitted-new-schema"
    assert decision.admission_status == "admitted"


def test_post_policy_trigger_binding_tamper_is_rejected_by_shared_validator(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    raw = next(record for record in records
               if record["stage"] == trigger_gate_binding.WAL_RECORD_STAGE)
    raw["payload"][wal.TRIGGER_BINDING_PAYLOAD_KEY]["mask"] = 10
    wal_path.write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    with pytest.raises(A.ArtifactAdmissionError, match="binding record"):
        A.classify_campaign(campaign)


def test_post_policy_trigger_provenance_must_copy_wal_commitment(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    path = campaign / "reports/p3_s8a_trigger_loop_provenance.json"
    provenance = json.loads(path.read_text())
    provenance["entries"]["1"][wal.TRIGGER_BINDING_COMMITMENT_KEY] = "0" * 64
    path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(A.ArtifactAdmissionError, match="WAL build_start と不一致"):
        A.classify_campaign(campaign)


def test_trigger_binding_marker_on_nontrigger_axis_is_mixed_and_rejected(tmp_path: Path) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=False, binding=False,
        axis="silo-writeset-sort",
    )
    with pytest.raises(A.ArtifactAdmissionError, match="binding marker"):
        A.classify_campaign(campaign)


def test_post_policy_trigger_unknown_marker_or_unclassified_shape_is_rejected(
    tmp_path: Path,
) -> None:
    unknown_marker = _classify_as_trigger(
        _new_schema_campaign(tmp_path / "unknown-marker"),
        marker=True, proposal=True, binding=False,
    )
    lock_path = unknown_marker / "campaign.lock"
    lock = json.loads(lock_path.read_text())
    lock["search_config"][wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY] = "unknown/v9"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(A.ArtifactAdmissionError, match="binding marker"):
        A.classify_campaign(unknown_marker)

    unknown_shape = _new_schema_campaign(tmp_path / "unknown-shape")
    lock_path = unknown_shape / "campaign.lock"
    lock = json.loads(lock_path.read_text())
    lock["search_config"]["axis"] = wal.TRIGGER_AXIS
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(A.ArtifactAdmissionError, match="classification is unknown|分類が unknown"):
        A.classify_campaign(unknown_shape)


def test_post_policy_variant_is_rederived_from_genome_and_source(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    for record in records:
        record["variant"] = "ffffffffffff"
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )

    with pytest.raises(A.ArtifactAdmissionError, match="variant differs"):
        A.require_admitted_campaign(campaign)


def test_post_policy_variant_without_build_start_remains_admissible(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    records.insert(2, {
        "variant": "ffffffffffff",
        "stage": "verify_done",
        "env_tag": "test",
        "ts": 2.5,
        "payload": {"certified": True},
    })
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )

    admitted = A.require_admitted_campaign(campaign)
    assert admitted.decision.classification == "admitted-new-schema"
    assert any(
        record.variant == "ffffffffffff" and record.stage == "verify_done"
        for record in admitted.records
    )


def test_admitted_view_is_deeply_immutable(tmp_path: Path) -> None:
    admitted = A.require_admitted_campaign(_new_schema_campaign(tmp_path))
    start = admitted.records[0]
    with pytest.raises(FrozenInstanceError):
        start.stage = "commit"
    with pytest.raises(TypeError):
        start.payload["genome"] = "silo|BACK_OFF=1"
    with pytest.raises(TypeError):
        start.payload["build_admission"]["source"]["src_token"] = "mutated"


def test_unlisted_post_policy_receiptless_terminal_is_denied(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path, omit_receipt=True)
    with pytest.raises(A.ArtifactAdmissionError, match="attempt admission is invalid"):
        A.require_admitted_campaign(campaign)


def test_unlisted_receiptless_campaign_cannot_self_declare_history(tmp_path: Path) -> None:
    campaign = _write_campaign(
        tmp_path / "historical",
        {
            "ccbench_commit": "historical",
            "search_config": {"records": 1, "threads": 1},
            "search_tag": "test", "spec_content": "test", "trial": "test",
        },
        [_record("build_start", {"genome": "g", "src_token": "old"}, ts=1.0)],
    )
    with pytest.raises(A.ArtifactAdmissionError, match="historicity is not proven"):
        A.require_admitted_campaign(campaign)


def test_exact_pre_policy_git_snapshot_artifact_remains_readable() -> None:
    path, lock_sha, wal_sha = KNOWN_HISTORICAL
    campaign = ROOT / path
    assert hashlib.sha256((campaign / "campaign.lock").read_bytes()).hexdigest() == lock_sha
    assert hashlib.sha256((campaign / "runs/wal.jsonl").read_bytes()).hexdigest() == wal_sha
    admitted = A.require_admitted_campaign(campaign)
    assert admitted.decision.classification == "historical-pre-admission-schema"
    assert admitted.decision.admission_status == "historical-not-reclassified"


def _run() -> int:
    """pytest fixtures/parametrize を含む全 node を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
