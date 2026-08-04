# -*- coding: utf-8 -*-
"""Independent sentinels for the T-344 deny-only campaign overlay."""
from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from orchestrator.campaign import artifact_admission as A
from orchestrator.campaign import build_admission, pipeline
from orchestrator.campaign.build_admission import (
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
    issue_trigger_gate_receipt,
)
from orchestrator.campaign.model import Genome
from orchestrator.campaign.pin import CURRENT_PIN
from orchestrator.campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, SourceEvidence
from orchestrator.campaign import source_digest
from orchestrator.campaign.trigger_gate_language import TRIGGER_GATE_LANGUAGE
from orchestrator.campaign.trigger_gate_reinspection import (
    REINSPECTION_LEDGER_SCHEMA,
    ReinspectionVerdict,
    canonical_record_sha256,
    create_reinspection_ledger,
)


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


def _trigger_schema_campaign(tmp_path: Path, monkeypatch) -> Path:
    genome = Genome("silo", {"BACKOFF_TRIGGER_GATING": 1})
    implementation = b"  izanagi_gate_pass = true;"
    source_path = tmp_path / source_digest.TRIGGER_GATE_SOURCE_REL
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(
        b"  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating\n"
        b"#if BACKOFF_TRIGGER_GATING\n" + implementation +
        b"\n#else\n  Backoff::backoff(FLAGS_clocks_per_us);\n#endif\n"
        b"  // EVOLVE-BLOCK-END silo-backoff-trigger-gating\n"
    )
    evidence = SourceEvidence(
        schema_version=source_digest.SOURCE_EVIDENCE_SCHEMA_V2,
        source_root=str(tmp_path.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(genome.canonical().encode()).hexdigest(),
        src_token="7" * 64,
        source_bytes_sha256="8" * 64,
        tracked_clean=False,
        tracked_diff_sha256="9" * 64,
        tracked_paths=(source_digest.TRIGGER_GATE_SOURCE_REL,),
        trigger_gate_language=TRIGGER_GATE_LANGUAGE,
        trigger_gate_implementation_sha256=hashlib.sha256(implementation).hexdigest(),
    )
    monkeypatch.setattr(
        build_admission.source_digest, "resolve_evidence",
        lambda *args, **kwargs: evidence,
    )
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    capability = attest_generator_output(
        context, evidence, generator_input_sha256="1" * 64,
    )
    trigger = issue_trigger_gate_receipt(evidence, genome=genome)
    admission = derive_build_admission(
        context, evidence, generator_receipt=capability,
        trigger_gate_receipt=trigger,
    )
    receipt = admission.as_wal_receipt()
    variant = pipeline.variant_id(genome, evidence.src_token)
    attempt_id = "trigger-attempt-1"
    start = {
        "build_attempt_id": attempt_id,
        "genome": genome.canonical(),
        "src_token": evidence.src_token,
        "build_admission": receipt,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
        "trigger_gate_language": TRIGGER_GATE_LANGUAGE,
        "trigger_gate_receipt": trigger.as_receipt(),
        "trigger_gate_receipt_sha256": trigger.receipt_sha256,
    }
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256": receipt["receipt_sha256"],
        "trigger_gate_receipt_sha256": trigger.receipt_sha256,
    }
    records = [
        {**_record("build_start", start, ts=1.0), "variant": variant},
        {**_record("build_done", terminal, ts=2.0), "variant": variant},
        {**_record("commit", terminal, ts=3.0), "variant": variant},
    ]
    lock = {
        "ccbench_commit": CURRENT_PIN,
        "search_config": {
            "axis": "silo-backoff-trigger-gating",
            "build_admission": dict(context.policy.as_preimage()),
            "trigger_gate_language": TRIGGER_GATE_LANGUAGE,
        },
        "search_tag": "test", "spec_content": "test", "trial": "test",
    }
    return _write_campaign(tmp_path / "trigger-campaign", lock, records)


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


def test_old_trigger_campaign_requires_record_bound_reinspection(
        tmp_path: Path, monkeypatch) -> None:
    campaign_id = "historical-trigger-record-bound"
    implementation_a = "  izanagi_gate_pass = true;"
    implementation_b = (
        "  izanagi_gate_pass = "
        "(izanagi_abort_reason_ != IzanagiAbortReason::kNodeVali);"
    )
    starts = [
        {
            "variant": f"legacy-{index}",
            "stage": "build_start",
            "env_tag": "test",
            "ts": float(index),
            "payload": {
                "genome": f"silo|BACKOFF_TRIGGER_GATING={index}",
                "src_token": chr(ord("a") + index) * 64,
                "proposal": {"implementation": implementation},
            },
        }
        for index, implementation in enumerate(
            (implementation_a, implementation_b), start=1,
        )
    ]
    campaign = _write_campaign(
        tmp_path / campaign_id,
        {
            "ccbench_commit": CURRENT_PIN,
            "search_config": {"axis": "silo-backoff-trigger-gating"},
            "search_tag": "legacy", "spec_content": "legacy", "trial": "legacy",
        },
        starts,
    )
    monkeypatch.setattr(A, "_is_proven_pre_policy_artifact", lambda **kwargs: True)
    ledger_path = tmp_path / "reinspection.json"
    create_reinspection_ledger(
        str(ledger_path), campaign_id=campaign_id, records=starts,
        ccbench_commit=CURRENT_PIN,
    )

    admitted = A.require_admitted_campaign(
        campaign, reinspection_ledger=ledger_path,
    )
    assert admitted.decision.classification == "historical-trigger-reinspected"
    assert admitted.decision.admission_status == "admitted-reinspected"
    assert len(admitted.decision.reinspection_record_sha256s) == len(starts)
    assert admitted.decision.as_receipt()["reinspection"]["ledger_sha256"]
    assert len(admitted.records) == len(starts)


def test_old_trigger_campaign_rejects_self_hashed_raw_mapping() -> None:
    path, campaign_id, *_rest = EXPECTED_RECORDS[2]
    campaign = ROOT / path
    starts = [
        json.loads(line)
        for line in (campaign / "runs/wal.jsonl").read_text().splitlines()
        if '"stage":"build_start"' in line
    ]
    unsigned: dict[str, object] = {
        "schema": REINSPECTION_LEDGER_SCHEMA,
        "campaign_id": campaign_id,
        "ccbench_commit": CURRENT_PIN,
        "entries": {
            canonical_record_sha256(record): ReinspectionVerdict.PASSED.value
            for record in starts
        },
        "evidence": {
            canonical_record_sha256(record): {
                "kind": "record-provenance", "source_root": None,
            }
            for record in starts
        },
    }
    ledger = dict(unsigned)
    ledger["ledger_sha256"] = hashlib.sha256(
        json.dumps(
            unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()
    with pytest.raises(A.ArtifactAdmissionError, match="ledger"):
        A.classify_campaign(campaign, reinspection_ledger=ledger)  # type: ignore[arg-type]


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


@pytest.mark.parametrize(
    ("tail", "line_issue_count", "truncated"),
    [
        pytest.param(b'{"variant":}\n', 1, False, id="terminated-invalid-line"),
        pytest.param(b'{"variant":"tail"', 0, True, id="truncated-tail"),
    ],
)
def test_diagnostic_admitted_view_keeps_only_shared_validated_records(
        tmp_path: Path, tail: bytes, line_issue_count: int,
        truncated: bool) -> None:
    campaign = _new_schema_campaign(tmp_path)
    with (campaign / "runs/wal.jsonl").open("ab") as stream:
        stream.write(tail)

    admitted, line_issues, observed_truncated = (
        A.require_admitted_campaign_collected(campaign)
    )

    assert [record.stage for record in admitted.records] == [
        "build_start", "build_done", "commit",
    ]
    assert len(line_issues) == line_issue_count
    assert observed_truncated is truncated


def test_real_v2_trigger_campaign_is_admitted(tmp_path: Path, monkeypatch) -> None:
    admitted = A.require_admitted_campaign(
        _trigger_schema_campaign(tmp_path, monkeypatch),
    )
    assert admitted.decision.classification == "admitted-new-schema"
    assert len(admitted.decision.attempt_receipt_sha256s) == 1


def test_shared_admitted_view_rejects_tampered_build_receipt(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    records[0]["payload"]["build_admission"]["receipt_sha256"] = "f" * 64
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )
    with pytest.raises(A.ArtifactAdmissionError, match="attempt admission is invalid"):
        A.require_admitted_campaign(campaign)


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
