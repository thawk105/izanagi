# -*- coding: utf-8 -*-
"""Independent sentinels for the T-344 deny-only campaign overlay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.campaign import artifact_admission as A
from orchestrator.campaign.build_admission import (
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.pin import CURRENT_PIN
from orchestrator.campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, SourceEvidence


ROOT = Path(__file__).resolve().parents[2]
LEDGER_RAW_SHA256 = "d3a5d293a60bb2e87a04ca676b51adf6bba6f8ed3c2b61ac74cc384028fedf0b"
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
        "variant": "v1", "stage": stage, "env_tag": "test", "ts": ts,
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


def test_unlisted_post_policy_campaign_requires_exact_attempt_receipt(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path)
    admitted = A.require_admitted_campaign(campaign)
    assert admitted.decision.classification == "admitted-new-schema"
    assert len(admitted.decision.attempt_receipt_sha256s) == 1


def test_unlisted_post_policy_receiptless_terminal_is_denied(tmp_path: Path) -> None:
    campaign = _new_schema_campaign(tmp_path, omit_receipt=True)
    with pytest.raises(A.ArtifactAdmissionError, match="attempt admission is invalid"):
        A.require_admitted_campaign(campaign)


def test_unlisted_pre_policy_historical_campaign_is_not_blanket_denied(tmp_path: Path) -> None:
    campaign = _write_campaign(
        tmp_path / "historical",
        {
            "ccbench_commit": "historical",
            "search_config": {"records": 1, "threads": 1},
            "search_tag": "test", "spec_content": "test", "trial": "test",
        },
        [_record("build_start", {"genome": "g", "src_token": "old"}, ts=1.0)],
    )
    admitted = A.require_admitted_campaign(campaign)
    assert admitted.decision.classification == "historical-pre-admission-schema"
    assert admitted.decision.admission_status == "historical-not-reclassified"
