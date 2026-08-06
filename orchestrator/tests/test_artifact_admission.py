# -*- coding: utf-8 -*-
"""Independent sentinels for the T-344 deny-only campaign overlay."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from orchestrator.campaign import artifact_admission as A
from orchestrator.campaign import trigger_gate_binding, wal
from orchestrator.campaign.build_admission import (
    GeneratorId,
    add_coder_build_authority_argument,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import Genome
from orchestrator.campaign.layout import CampaignLayout
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
LEGACY_TRIGGER_CAMPAIGNS = (
    (
        "output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2",
        "b8f4a4e25158d0d9e6a5839da9a837d3d41af3af198e9da25ef76ae3b6557b88",
        "3e447c7dd44d6daf35105e0db0acfc02afc20c295016a60e763f3f3f5d0eca41",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8",
        "c2d838b89009ed499ac6e1f19990ad5653c0dde337859a012d934675bdd9b688",
        "d5ec15db79957e44f7d10a5adbcc7d069db2f587f170fd83ae0dfcfe56df428d",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7",
        "654d5cd73c0418e5cc6ce8924854528d35921d2ab7e850c7c2f1ea69eeeb3c41",
        "6c519d85c5704dcdf040a37e01eba6d86f0f4a4b535561880d6af6f905590f4c",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c",
        "8a237e8c48a3ed154840a167d8a6e43d843ebe1849bbadda885d8cb06a7b87f1",
        "aa04b36a3a48d006664589a5bc71242ebbd5c7ea9ea3c46ac171266f1516847e",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8",
        "a81ec3d876775cdee547c558d77fb4bc19515b89f76849acdd38f3d91bdd6be4",
        "d218f4e47685b6c3bb25e47119aa3ef509022d2dbf29e2a4acd2e294b0924bbd",
    ),
    (
        "output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb",
        "dcd2bbfbd08942af7e2d49fd5c510ec657e89a630b2917ab55ed54d20619a55c",
        "194746d89f1c92ef72e24daf83620ff179c386819b86b91be8159740f01c9225",
    ),
)
ADMITTED_HISTORICAL_CAMPAIGNS = (
    "output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50",
    "output/campaigns/backoff-repro-silo-write-heavy-repro-181607af",
    "output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e",
    "output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9",
    "output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90",
    "output/campaigns/backoff-sweep-silo-read-heavy-sweep-8ff95955",
    "output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7",
    "output/campaigns/p2-2-silo-balanced-enumerate-f1588056",
    "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad",
    "output/campaigns/p2-2-silo-write-heavy-enumerate-8967bed6",
    "output/campaigns/p3-kickoff-coder-wiring-cba40400",
    "output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4",
    "output/campaigns/p3-s6-sort-sweep-balanced-sweep-1b39095e",
    "output/campaigns/p3-s6-sort-sweep-balanced-sweep-dd25aa8c",
    "output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef",
    "output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-d4552403",
    "output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2",
    "output/campaigns/s1-direct-block2-direct-comparison-9645b16a",
    "output/campaigns/s1-direct-develop-direct-comparison-7bccdf1a",
    "output/campaigns/s1-direct-develop-direct-comparison-d0f495bf",
    "output/campaigns/s1-direct-floor-direct-comparison-b82b9229",
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


def _record(
        stage: str, payload: dict, *, ts: float,
        variant: str = "6a803ba39f7b",
) -> dict:
    return {
        "variant": variant, "stage": stage, "env_tag": "test", "ts": ts,
        "payload": payload,
    }


def _campaign_id_for_lock(lock: dict, *, slug: str = "campaign") -> str:
    encoded = json.dumps(
        lock, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return f"{slug}-{lock['search_tag']}-{hashlib.sha256(encoded).hexdigest()[:8]}"


def _rename_for_lock(campaign: Path) -> Path:
    lock = json.loads((campaign / "campaign.lock").read_text())
    expected = campaign.parent / _campaign_id_for_lock(lock)
    if expected != campaign:
        campaign.rename(expected)
    return expected


def _new_schema_campaign(
        tmp_path: Path, *, omit_receipt: bool = False,
        coder_authored: bool = False,
) -> Path:
    if coder_authored:
        parser = argparse.ArgumentParser(add_help=False)
        add_coder_build_authority_argument(parser)
        authority = parser.parse_args(
            ["--allow-coder-derived-build"]
        ).coder_build_authority
        context = build_run_context(
            generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
            coder_authority=authority,
        )
    else:
        context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    genome_value = Genome("silo", {"BACK_OFF": 0})
    genome = genome_value.canonical()
    src_token = "b" * 64 if coder_authored else "stock"
    evidence = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=str(tmp_path.resolve()),
        ccbench_commit=CURRENT_PIN,
        genome_sha256=hashlib.sha256(genome.encode()).hexdigest(),
        src_token=src_token,
        source_bytes_sha256="a" * 64,
        tracked_clean=not coder_authored,
        tracked_diff_sha256=("c" * 64 if coder_authored
                             else EMPTY_TRACKED_DIFF_SHA256),
        tracked_paths=(("cc/silo/transaction.cc",) if coder_authored else ()),
    )
    admission = derive_build_admission(context, evidence)
    receipt = admission.as_wal_receipt()
    attempt_id = "attempt-1"
    start = {
        "build_attempt_id": attempt_id,
        "genome": genome,
        "src_token": src_token,
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
    variant = A.pipeline.variant_id(genome_value, src_token)
    records = [
        _record("build_start", start, ts=1.0, variant=variant),
        _record("build_done", terminal, ts=2.0, variant=variant),
        _record("commit", terminal, ts=3.0, variant=variant),
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
    return _write_campaign(tmp_path / _campaign_id_for_lock(lock), lock, records)


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
        return _rename_for_lock(campaign)

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
                "build_attempt_id": start["payload"]["build_attempt_id"],
                "variant": start["variant"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY:
                    start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY],
            },
        },
    }), encoding="utf-8")
    return _rename_for_lock(campaign)


def test_recovered_attempt_then_retry_is_admitted_without_read_mutation(tmp_path):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    original = wal.read_records(layout)
    start = original[0]
    (campaign / "runs/wal.jsonl").write_text(
        json.dumps({
            "variant": start.variant,
            "stage": start.stage,
            "env_tag": start.env_tag,
            "ts": start.ts,
            "payload": start.payload,
        }, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    crash_prefix = (campaign / "runs/wal.jsonl").read_bytes()
    policy = build_run_context(
        generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
    ).policy
    recovered = wal.recover_interrupted_attempts(
        layout, admission_policy=policy,
    )
    assert len(recovered) == 1
    retry_payload = dict(start.payload)
    retry_payload["build_attempt_id"] = "attempt-2"
    terminal_payload = {
        "build_attempt_id": "attempt-2",
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
    }
    wal.log(layout, start.variant, "build_start", start.env_tag, retry_payload)
    wal.log(layout, start.variant, "build_done", start.env_tag, terminal_payload)
    wal.log(layout, start.variant, "commit", start.env_tag, terminal_payload)
    before_admission = (campaign / "runs/wal.jsonl").read_bytes()

    admitted = A.require_admitted_campaign(campaign)
    assert admitted.decision.admitted
    assert before_admission.startswith(crash_prefix)
    assert (campaign / "runs/wal.jsonl").read_bytes() == before_admission


@pytest.mark.parametrize("extra_key,extra_value", [
    ("build_admission", {"forged": "body"}),
    ("fitness_tps", 999999999),
    ("verify", {"verdict": "forged"}),
], ids=["build-admission", "fitness-tps", "verify"])
def test_recovery_abort_extra_keys_are_rejected_by_replay_and_admission(
        tmp_path, extra_key, extra_value):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    start = wal.read_records(layout)[0]
    payload = {
        "reason": "recovery-abort-incomplete-attempt",
        "build_attempt_id": start.payload["build_attempt_id"],
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
        extra_key: extra_value,
    }
    records = [
        _record("build_start", start.payload, ts=1.0, variant=start.variant),
        _record("abort", payload, ts=2.0, variant=start.variant),
    ]
    (campaign / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    with pytest.raises(wal.AttemptTopologyError, match="exact key"):
        wal.replay(layout, admission_policy=policy)
    with pytest.raises(A.ArtifactAdmissionError, match="exact key"):
        A.require_admitted_campaign(campaign)


@pytest.mark.parametrize("schema_key,schema_value", [
    ("build_attempt_id", "orphan-attempt"),
    ("build_admission", {"schema": "marker-only"}),
    ("build_admission_receipt_sha256", "a" * 64),
    (wal.TRIGGER_BINDING_COMMITMENT_KEY, "b" * 64),
], ids=[
    "build-attempt-id", "build-admission", "receipt-sha256",
    "trigger-commitment",
])
def test_each_attempt_schema_key_independently_enables_strict_recovery_validation(
        tmp_path, schema_key, schema_value):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    malformed = _record(
        "build_done", {schema_key: schema_value}, ts=1.0,
        variant="schema-marker-v",
    )
    wal_path = campaign / "runs/wal.jsonl"
    wal_path.write_text(
        json.dumps(malformed, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    before = wal_path.read_bytes()
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    with pytest.raises(wal.InterruptedAttemptRecoveryError) as excinfo:
        wal.recover_interrupted_attempts(layout, admission_policy=policy)
    assert excinfo.value.condition == "existing-topology-violation"
    assert wal_path.read_bytes() == before


def _append_committed_retry(layout, start, attempt_id: str) -> None:
    retry_start = dict(start.payload)
    retry_start["build_attempt_id"] = attempt_id
    terminal = {
        "build_attempt_id": attempt_id,
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
    }
    wal.log(layout, start.variant, "build_start", start.env_tag, retry_start)
    wal.log(layout, start.variant, "build_done", start.env_tag, terminal)
    wal.log(layout, start.variant, "commit", start.env_tag, terminal)


def test_historical_signal_does_not_overreject_later_start_only_recovery(tmp_path):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    start = wal.read_records(layout)[0]
    first_terminal = {
        "build_attempt_id": "historical-attempt",
        "build_admission_receipt_sha256":
            start.payload["build_admission_receipt_sha256"],
    }
    first_start = dict(start.payload)
    first_start["build_attempt_id"] = "historical-attempt"
    active_start = dict(start.payload)
    active_start["build_attempt_id"] = "active-attempt"
    records = [
        _record("build_start", first_start, ts=1.0, variant=start.variant),
        _record("build_done", first_terminal, ts=2.0, variant=start.variant),
        _record("verify_done", {"verdict": "red"}, ts=3.0, variant=start.variant),
        _record("abort", {**first_terminal, "reason": "verify-failed"},
                ts=4.0, variant=start.variant),
        _record("build_start", active_start, ts=5.0, variant=start.variant),
    ]
    (campaign / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    recovered = wal.recover_interrupted_attempts(layout, admission_policy=policy)
    assert len(recovered) == 1
    assert recovered[0].payload["build_attempt_id"] == "active-attempt"
    _append_committed_retry(layout, start, "retry-attempt")
    before_admission = (campaign / "runs/wal.jsonl").read_bytes()
    assert A.require_admitted_campaign(campaign).decision.admitted
    assert (campaign / "runs/wal.jsonl").read_bytes() == before_admission


def test_other_variant_recovery_limit_does_not_overreject_first_recovery(tmp_path):
    campaign = _new_schema_campaign(tmp_path)
    layout = CampaignLayout(root=str(campaign))
    start = wal.read_records(layout)[0]
    records = []
    for index in range(wal.INCOMPLETE_ATTEMPT_RECOVERY_LIMIT):
        attempt_id = f"variant-a-attempt-{index}"
        records.extend([
            _record("build_start", {"build_attempt_id": attempt_id},
                    ts=float(index * 2 + 1), variant="variant-a"),
            _record("abort", {
                "reason": "recovery-abort-incomplete-attempt",
                "build_attempt_id": attempt_id,
            }, ts=float(index * 2 + 2), variant="variant-a"),
        ])
    active_start = dict(start.payload)
    active_start["build_attempt_id"] = "variant-b-active"
    records.append(_record(
        "build_start", active_start, ts=10.0, variant=start.variant,
    ))
    (campaign / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    policy = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP).policy

    recovered = wal.recover_interrupted_attempts(layout, admission_policy=policy)
    assert len(recovered) == 1
    assert recovered[0].variant == start.variant
    assert recovered[0].payload["build_attempt_id"] == "variant-b-active"
    _append_committed_retry(layout, start, "variant-b-retry")
    before_admission = (campaign / "runs/wal.jsonl").read_bytes()
    assert A.require_admitted_campaign(campaign).decision.admitted
    assert (campaign / "runs/wal.jsonl").read_bytes() == before_admission


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


def test_trusted_snapshot_campaign_corpus_is_fully_enumerated() -> None:
    ledger = json.loads(A.LEDGER_PATH.read_bytes())
    completed = subprocess.run(
        [
            "git", "-C", str(ROOT), "ls-tree", "-r", "--name-only",
            ledger["created_from_commit"], "--", "output/campaigns",
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    actual = {
        path.removesuffix("/campaign.lock")
        for path in completed.stdout.splitlines()
        if path.endswith("/campaign.lock")
    }
    overlay = {path for path, *_rest in EXPECTED_RECORDS}
    legacy_trigger = {path for path, _lock_sha, _wal_sha in LEGACY_TRIGGER_CAMPAIGNS}
    admitted_historical = set(ADMITTED_HISTORICAL_CAMPAIGNS)

    assert actual == overlay | legacy_trigger | admitted_historical


@pytest.mark.parametrize(
    ("lock", "expected"),
    [
        pytest.param(
            {
                "search_config": {
                    "axis": wal.TRIGGER_AXIS,
                    "generator": "reason-subset-v1",
                    "space": "reason-subsets(effective)+identall+stock",
                },
            },
            True,
            id="trigger-machine-shape",
        ),
        pytest.param(
            {"search_config": {"axis": wal.TRIGGER_AXIS, "reflux": "on"}},
            True,
            id="trigger-proposal-shape",
        ),
        pytest.param(
            {"search_config": {"axis": wal.TRIGGER_AXIS, "unknown": "shape"}},
            True,
            id="trigger-unknown-shape",
        ),
        pytest.param(
            {"search_config": {"axis": "silo-writeset-sort"}},
            False,
            id="non-trigger-axis",
        ),
        pytest.param(
            {"search_config": []}, False, id="search-config-not-dict",
        ),
        pytest.param({}, False, id="search-config-absent"),
        pytest.param([], False, id="lock-not-dict"),
    ],
)
def test_is_legacy_trigger_lock_truth_table(lock: object, expected: bool) -> None:
    assert A._is_legacy_trigger_lock(lock) is expected


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


@pytest.mark.parametrize(
    ("path", "lock_sha", "wal_sha"),
    LEGACY_TRIGGER_CAMPAIGNS,
    ids=[Path(path).name for path, _lock_sha, _wal_sha in LEGACY_TRIGGER_CAMPAIGNS],
)
def test_legacy_trigger_campaigns_are_not_admitted(
    path: str, lock_sha: str, wal_sha: str,
) -> None:
    campaign = ROOT / path
    assert (
        hashlib.sha256((campaign / "campaign.lock").read_bytes()).hexdigest()
        == lock_sha
    )
    assert (
        hashlib.sha256((campaign / "runs/wal.jsonl").read_bytes()).hexdigest()
        == wal_sha
    )

    decision = A.classify_campaign(campaign)
    assert decision.classification == "historical-pre-admission-schema"
    assert decision.admission_status == "legacy-unclassified"
    with pytest.raises(A.CampaignNotAdmitted, match="legacy-unclassified"):
        A.require_admitted_campaign(campaign)


@pytest.mark.parametrize(
    "path",
    ADMITTED_HISTORICAL_CAMPAIGNS,
    ids=[Path(path).name for path in ADMITTED_HISTORICAL_CAMPAIGNS],
)
def test_nontrigger_historical_campaigns_remain_admitted(path: str) -> None:
    admitted = A.require_admitted_campaign(ROOT / path)
    assert admitted.decision.classification == "historical-pre-admission-schema"
    assert admitted.decision.admission_status == "historical-not-reclassified"


@pytest.mark.parametrize("schema", ["historical", "post-policy"])
def test_lock_read_snapshot_is_rechecked_against_terminal_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, schema: str,
) -> None:
    if schema == "historical":
        campaign = _write_campaign(
            tmp_path / "historical",
            {
                "ccbench_commit": "historical",
                "search_config": {"records": 1, "threads": 1},
                "search_tag": "test", "spec_content": "test", "trial": "test",
            },
            [_record("build_start", {"genome": "g", "src_token": "old"}, ts=1.0)],
        )
        monkeypatch.setattr(
            A, "_is_proven_pre_policy_artifact", lambda **_kwargs: True,
        )
    else:
        campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    original_read_bytes = Path.read_bytes
    replacement_raw = original_read_bytes(lock_path) + b"\n"
    replaced = False

    def read_then_replace(path: Path) -> bytes:
        nonlocal replaced
        raw = original_read_bytes(path)
        if path == lock_path and not replaced:
            lock_path.write_bytes(replacement_raw)
            replaced = True
        return raw

    monkeypatch.setattr(Path, "read_bytes", read_then_replace)

    with pytest.raises(A.ArtifactAdmissionError, match="bytes changed"):
        A.require_admitted_campaign(campaign)
    assert replaced
    assert original_read_bytes(lock_path) == replacement_raw


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
    lock_path = campaign / "campaign.lock"
    lock_path.write_text(json.dumps(json.loads(lock_path.read_text())), encoding="utf-8")
    arbitrary_layout = campaign.parent / "machine-sweep-layout"
    campaign.rename(arbitrary_layout)
    campaign = arbitrary_layout
    decision = A.classify_campaign(campaign)
    assert decision.classification == "admitted-new-schema"
    assert decision.admission_status == "admitted"


def test_nontrigger_post_policy_preserves_default_json_and_arbitrary_layout(
    tmp_path: Path,
) -> None:
    campaign = _new_schema_campaign(tmp_path)
    lock_path = campaign / "campaign.lock"
    lock_path.write_text(json.dumps(json.loads(lock_path.read_text())), encoding="utf-8")
    arbitrary_layout = campaign.parent / "formal-shaped"
    campaign.rename(arbitrary_layout)

    decision = A.classify_campaign(arbitrary_layout)
    assert decision.classification == "admitted-new-schema"
    assert decision.campaign_id == "formal-shaped"


def test_post_policy_campaign_directory_id_must_match_lock_preimage(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    renamed = campaign.parent / "campaign-test-deadbeef"
    campaign.rename(renamed)
    with pytest.raises(A.ArtifactAdmissionError, match="directory ID"):
        A.classify_campaign(renamed)


def test_post_policy_trigger_proposal_requires_canonical_lock_bytes(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    lock_path = campaign / "campaign.lock"
    lock_path.write_text(json.dumps(json.loads(lock_path.read_text())), encoding="utf-8")

    with pytest.raises(A.ArtifactAdmissionError, match="canonical preimage"):
        A.classify_campaign(campaign)


def test_proposal_cannot_be_rewritten_as_machine_sweep_with_coder_receipt(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path, coder_authored=True),
        marker=True, proposal=True, binding=True,
    )
    lock_path = campaign / "campaign.lock"
    lock = json.loads(lock_path.read_text())
    search = lock["search_config"]
    search.pop(wal.TRIGGER_BINDING_SCHEMA_MARKER_KEY)
    search.pop("reflux")
    search.update({
        "generator": "reason-subset-v1",
        "space": "reason-subsets(effective)+identall+stock",
    })
    lock_path.write_text(
        json.dumps(lock, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )

    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    records = [
        record for record in records
        if record["stage"] != trigger_gate_binding.WAL_RECORD_STAGE
    ]
    start = next(record for record in records if record["stage"] == "build_start")
    assert start["payload"]["build_admission"]["class"] == "coder-authored"
    start["payload"].pop(wal.TRIGGER_BINDING_COMMITMENT_KEY)
    wal_path.write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
                for record in records),
        encoding="utf-8",
    )
    provenance_path = campaign / "reports/p3_s8a_trigger_loop_provenance.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["entries"]["1"].pop(wal.TRIGGER_BINDING_COMMITMENT_KEY)
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    campaign = _rename_for_lock(campaign)

    with pytest.raises(A.ArtifactAdmissionError, match="coder-authored receipt"):
        A.classify_campaign(campaign)


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


def test_trigger_provenance_requires_each_abort_retry_attempt(
    tmp_path: Path,
) -> None:
    campaign = _classify_as_trigger(
        _new_schema_campaign(tmp_path),
        marker=True, proposal=True, binding=True,
    )
    wal_path = campaign / "runs/wal.jsonl"
    records = [json.loads(line) for line in wal_path.read_text().splitlines()]
    raw = next(record for record in records
               if record["stage"] == trigger_gate_binding.WAL_RECORD_STAGE)
    start = next(record for record in records if record["stage"] == "build_start")
    receipt_sha = start["payload"]["build_admission_receipt_sha256"]
    first_attempt = start["payload"]["build_attempt_id"]
    second_attempt = "attempt-2"
    raw_retry = json.loads(json.dumps(raw))
    raw_retry["ts"] = 3.0
    raw_retry["payload"]["build_attempt_id"] = second_attempt
    start_retry = json.loads(json.dumps(start))
    start_retry["ts"] = 4.0
    start_retry["payload"]["build_attempt_id"] = second_attempt
    abort_first = _record(
        "abort", {
            "build_attempt_id": first_attempt,
            "build_admission_receipt_sha256": receipt_sha,
            "reason": "build-error",
        }, ts=2.0, variant=start["variant"],
    )
    abort_retry = _record(
        "abort", {
            "build_attempt_id": second_attempt,
            "build_admission_receipt_sha256": receipt_sha,
            "reason": "build-error",
        }, ts=5.0, variant=start["variant"],
    )
    wal_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in [raw, start, abort_first, raw_retry, start_retry, abort_retry]
        ),
        encoding="utf-8",
    )

    path = campaign / "reports/p3_s8a_trigger_loop_provenance.json"
    provenance = json.loads(path.read_text())
    provenance["entries"]["2"] = {
        "build_attempt_id": second_attempt,
        "variant": start["variant"],
        wal.TRIGGER_BINDING_COMMITMENT_KEY:
            start["payload"][wal.TRIGGER_BINDING_COMMITMENT_KEY],
    }
    path.write_text(json.dumps(provenance), encoding="utf-8")
    assert A.classify_campaign(campaign).classification == "admitted-new-schema"

    del provenance["entries"]["2"]
    path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(A.ArtifactAdmissionError, match="attempt/commitment"):
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
    lock_path.write_text(
        json.dumps(lock, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    unknown_marker = _rename_for_lock(unknown_marker)
    with pytest.raises(A.ArtifactAdmissionError, match="binding marker"):
        A.classify_campaign(unknown_marker)

    unknown_shape = _new_schema_campaign(tmp_path / "unknown-shape")
    lock_path = unknown_shape / "campaign.lock"
    lock = json.loads(lock_path.read_text())
    lock["search_config"]["axis"] = wal.TRIGGER_AXIS
    lock_path.write_text(
        json.dumps(lock, sort_keys=True, separators=(",", ":")), encoding="utf-8",
    )
    unknown_shape = _rename_for_lock(unknown_shape)
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
