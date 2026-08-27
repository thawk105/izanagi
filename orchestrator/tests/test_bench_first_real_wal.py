# -*- coding: utf-8 -*-
"""初回 positive control の実 WAL 由来 consumer 回帰 (設計 §5-5 / F15)。

fixture 出所: campaign
`backoff-sweep-silo-read-heavy-sweep-6f169f90` の runs/wal.jsonl 全 9 レコード。
既存の合成 fixture と併存させ、実出力 schema で uncertified TPS の遮断を固定する。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH.parent))

from orchestrator.campaign import (                                                   # noqa: E402
    campaign_lock,
    contract_loader_binding,
    p2_2_report,
    replay,
    s6_sort_sweep,
    s8a_trigger_sweep,
    wal,
)
from orchestrator.campaign.artifact_admission import (                                      # noqa: E402
    CampaignReadPurpose,
    CampaignVerifierEpochRejected,
    require_admitted_campaign,
)
from orchestrator.campaign.backoff_repro import _bench_tps                              # noqa: E402
from orchestrator.campaign.build_admission import (                                     # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.layout import CampaignLayout                                # noqa: E402
from orchestrator.campaign.model import (                                               # noqa: E402
    COMMIT_CONTRACT_SHA256_KEY,
    STAGE_ABORT,
    STAGE_BENCH_DONE,
    STAGE_COMMIT,
)
from orchestrator.campaign.pin import CURRENT_PIN                                       # noqa: E402
from orchestrator.campaign.source_digest import (                                       # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from orchestrator.critic.digest import load_screen_rejections, load_workload            # noqa: E402
from campaign_lock_test_support import build_v2_lock                                    # noqa: E402

_FIXTURE = _HERE / "fixtures" / "bench_first_screen_reject_6f169f90.jsonl"
_BASELINE = "84319b1127a6"
_REJECTED = "610e879931c4"
_BASELINE_GENOME = (
    "silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,"
    "NO_WAIT_OF_TICTOC=0,WAL=0"
)
_REJECTED_GENOME = (
    "silo|BACKOFF_FIXED=100,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,"
    "NO_WAIT_OF_TICTOC=0,WAL=0"
)
_REAL_E0_CAMPAIGN = (
    Path(__file__).resolve().parents[2]
    / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
)


@pytest.fixture
def real_screen_layout(tmp_path) -> CampaignLayout:
    layout = CampaignLayout(str(tmp_path / "campaign")).ensure()
    shutil.copyfile(_FIXTURE, layout.wal_file)
    Path(layout.lock_file).write_text(
        json.dumps({"search_config": {}}), encoding="utf-8",
    )
    return layout


def _write_admitted_real_fixture(root: Path) -> CampaignLayout:
    """Copy the real WAL shape and add only the post-policy proof-chain fields."""
    layout = CampaignLayout(str(root)).ensure()
    records = [json.loads(line) for line in _FIXTURE.read_text().splitlines()]
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    attempts = {}
    for ordinal, record in enumerate(records):
        if record["stage"] != "build_start":
            continue
        genome = record["payload"]["genome"]
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=str(root.resolve()),
            ccbench_commit=CURRENT_PIN,
            genome_sha256=hashlib.sha256(genome.encode()).hexdigest(),
            src_token="stock",
            source_bytes_sha256="a" * 64,
            tracked_clean=True,
            tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )
        receipt = derive_build_admission(context, evidence).as_wal_receipt()
        attempts[record["variant"]] = (
            f"fixture-attempt-{ordinal}", receipt,
        )
        record["payload"].update({
            "build_attempt_id": attempts[record["variant"]][0],
            "build_admission": receipt,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        })

    for record in records:
        if record["stage"] not in {
            "build_done", "verify_done", "bench_done", "commit", "abort",
        }:
            continue
        attempt_id, receipt = attempts[record["variant"]]
        record["payload"].update({
            "build_attempt_id": attempt_id,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        })

    Path(layout.wal_file).write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    Path(layout.lock_file).write_text(json.dumps({
        "ccbench_commit": CURRENT_PIN,
        "search_config": {
            "build_admission": dict(context.policy.as_preimage()),
        },
    }), encoding="utf-8")
    return layout


def _fixture_git(repo: Path, *args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        pytest.fail("git is required for verifier epoch fixtures")
    completed = subprocess.run(
        [executable, "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        pytest.fail(
            "git fixture command failed: "
            f"args={args!r} rc={completed.returncode} "
            f"stderr={completed.stderr.decode('utf-8', errors='replace')!r}"
        )
    return completed.stdout


def _upgrade_to_fixed_e1(
    layout: CampaignLayout, root: Path, monkeypatch: pytest.MonkeyPatch,
) -> CampaignLayout:
    """固定 bytes の closure repo に束縛した E1 campaign へ移行する。"""
    repo = root / "closure-repo"
    repo.mkdir()
    _fixture_git(repo, "init", "-q")
    for index, relative in enumerate(
        campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS, start=1,
    ):
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"epoch closure fixture {index}\n".encode("ascii"))
    _fixture_git(
        repo, "add", "--", *campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS,
    )
    _fixture_git(
        repo,
        "-c", "user.email=epoch-fixture@example.invalid",
        "-c", "user.name=epoch fixture",
        "commit", "-q", "-m", "record closure A",
    )
    monkeypatch.setattr(contract_loader_binding, "_REPO_ROOT", repo)

    lock_path = Path(layout.lock_file)
    legacy_identity = campaign_lock.decode_campaign_lock(
        lock_path.read_text(encoding="utf-8")
    ).identity
    identity_preimage = campaign_lock.canonical_json({
        "ccbench_commit": legacy_identity["ccbench_commit"],
        "search_config": legacy_identity["search_config"],
        "search_tag": "real-screen",
        "spec_content": "test",
        "trial": "test",
    })
    lock_text = build_v2_lock(identity_preimage)
    decoded = campaign_lock.decode_campaign_lock(lock_text)
    assert decoded.authority is not None
    lock_path.write_text(lock_text, encoding="utf-8")

    records = [
        json.loads(line)
        for line in Path(layout.wal_file).read_text(encoding="utf-8").splitlines()
    ]
    for record in records:
        if record["stage"] == "commit":
            record["payload"][COMMIT_CONTRACT_SHA256_KEY] = (
                decoded.authority.environment_contract_sha256
            )
    Path(layout.wal_file).write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    return layout


@pytest.fixture
def admitted_real_screen_layout(tmp_path) -> CampaignLayout:
    return _write_admitted_real_fixture(tmp_path / "campaign")


def test_real_wal_fixture_preserves_positive_control_shape(real_screen_layout):
    """実走 schema 自体を正対照にし、verify 非交差と終端状態を固定する。"""
    records = wal.read_records(real_screen_layout)
    assert len(records) == 9
    abort = next(r for r in records if r.variant == _REJECTED and r.stage == STAGE_ABORT)
    assert abort.payload == {
        "reason": "screen-slower-than-floor",
        "screen": {
            "median_tps": 1912074.0,
            "cv": 0.009266208528432952,
            "baseline_tps": 8470959.0,
            "baseline_ref": _BASELINE,
            "floor": 0.0010979692594382789,
            "k": 1.5,
            "margin": -0.7742789216663662,
        },
    }
    assert "verify" not in abort.payload
    states = wal.replay(real_screen_layout)
    assert states[_BASELINE].committed and not states[_BASELINE].aborted
    assert states[_REJECTED].aborted and not states[_REJECTED].committed


def test_real_wal_critic_loaders_hide_uncertified_metrics(
    admitted_real_screen_layout, tmp_path, monkeypatch,
):
    historical = require_admitted_campaign(
        _REAL_E0_CAMPAIGN,
        purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    assert historical.campaign_verifier_epoch.state == "E0"
    assert historical.records
    with pytest.raises(CampaignVerifierEpochRejected, match="state=E0"):
        require_admitted_campaign(
            _REAL_E0_CAMPAIGN,
            purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        )

    e1_layout = _upgrade_to_fixed_e1(
        admitted_real_screen_layout, tmp_path, monkeypatch,
    )
    view = require_admitted_campaign(
        e1_layout,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    assert view.campaign_verifier_epoch.state == "E1"
    workload = load_workload(view)
    assert len(workload) == 1 and workload[0].genome == _BASELINE_GENOME
    assert workload[0].li["throughput_tps"] == 8470959.0

    rejected = load_screen_rejections(view)
    assert len(rejected) == 1
    assert rejected[0].genome == _REJECTED_GENOME
    projected = vars(rejected[0])
    for hidden in ("median_tps", "cv", "baseline_tps", "floor", "k", "margin"):
        assert hidden not in projected


@pytest.mark.parametrize("loader", [s6_sort_sweep._load_rows, s8a_trigger_sweep._load_rows])
def test_real_wal_sweep_report_rows_gate_on_commit(
    admitted_real_screen_layout, loader, tmp_path, monkeypatch,
):
    entries = {
        "baseline": {"variant_id": _BASELINE, "category": "full-order"},
        "screened-out": {"variant_id": _REJECTED, "category": "full-order"},
    }
    historical = require_admitted_campaign(
        _REAL_E0_CAMPAIGN,
        purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    assert historical.campaign_verifier_epoch.state == "E0"
    assert historical.records
    with pytest.raises(CampaignVerifierEpochRejected, match="state=E0"):
        loader(_REAL_E0_CAMPAIGN, entries)

    e1_layout = _upgrade_to_fixed_e1(
        admitted_real_screen_layout, tmp_path, monkeypatch,
    )
    rows = {r["name"]: r for r in loader(e1_layout, entries)}
    assert rows["baseline"]["certified"] is True
    assert rows["baseline"]["median_tps"] == 8470959.0
    screened = rows["screened-out"]
    assert screened["abort_reason"] == "screen-slower-than-floor"
    assert screened["certified"] is False
    for key in ("median_tps", "cv", "abort_rate", "ipc", "llc_miss_rate"):
        assert screened[key] is None


@pytest.mark.parametrize("loader", [s6_sort_sweep._load_rows, s8a_trigger_sweep._load_rows])
def test_real_e0_sweep_selection_is_rejected_by_epoch(loader):
    campaign = (
        Path(__file__).resolve().parents[2]
        / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
    )
    with pytest.raises(CampaignVerifierEpochRejected, match="state=E0"):
        loader(campaign, {})


def test_real_wal_replay_landscape_requires_commit(tmp_path, monkeypatch):
    root = tmp_path / "output"
    layout = CampaignLayout(str(
        root / "campaigns" / "p2-2-silo-real-screen-enumerate-fixture"
    )).ensure()
    _write_admitted_real_fixture(Path(layout.root))
    historical = require_admitted_campaign(
        _REAL_E0_CAMPAIGN,
        purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    assert historical.campaign_verifier_epoch.state == "E0"
    assert historical.records
    with pytest.raises(CampaignVerifierEpochRejected, match="state=E0"):
        replay.load_landscape("read-heavy")

    _upgrade_to_fixed_e1(layout, tmp_path, monkeypatch)
    landscape = replay.load_landscape("real-screen", str(root))
    assert set(landscape) == {_BASELINE_GENOME}
    assert landscape[_BASELINE_GENOME].fitness_tps == 8470959.0
    assert _REJECTED_GENOME not in landscape


def test_real_wal_p2_2_report_ranking_requires_commit(admitted_real_screen_layout):
    view = require_admitted_campaign(
        admitted_real_screen_layout,
        purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    rows = p2_2_report._collect(view)
    assert rows[_REJECTED].median == 1912074.0  # 実 WAL に数値がある正対照
    ranked = p2_2_report._ranked(rows)
    assert [r.variant for r in ranked] == [_BASELINE]
    assert all(r.median != 1912074.0 for r in ranked)


def test_real_e0_replay_landscape_is_rejected_for_certified_selection():
    with pytest.raises(CampaignVerifierEpochRejected, match="state=E0"):
        replay.load_landscape("read-heavy")


def test_real_e0_p2_report_provenance_names_historical_epoch():
    campaign = (
        Path(__file__).resolve().parents[2]
        / "output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad"
    )
    view = require_admitted_campaign(
        campaign, purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    provenance = p2_2_report._epoch_provenance(view)
    assert provenance["read_purpose"] == "HISTORICAL_RAW"
    assert provenance["verifier_assessment_basis"] == (
        "recorded-at-original-verifier-epoch"
    )
    assert provenance["campaign_verifier_epoch"] == "E0"
    assert provenance["campaign_verifier_epoch_state"] == "E0"
    assert "certified" not in repr(provenance).lower()


def test_p2_summary_serializes_and_requires_historical_marker(tmp_path):
    view = require_admitted_campaign(
        _REAL_E0_CAMPAIGN, purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    ranked = p2_2_report._ranked(p2_2_report._collect(view))
    winner = p2_2_report._winner(ranked)
    result = {
        "tag": "read-heavy",
        "winner": winner,
        "ranked": ranked,
        "verdicts": {},
        "report": str(tmp_path / "detail.md"),
        **p2_2_report._epoch_provenance(view),
    }
    summary = tmp_path / "summary.md"

    p2_2_report.write_summary([result], str(summary))

    text = summary.read_text(encoding="utf-8")
    assert "`HISTORICAL_RAW`" in text
    assert "`recorded-at-original-verifier-epoch`" in text
    assert "| read-heavy |" in text

    missing_marker = dict(result)
    del missing_marker["verifier_assessment_basis"]
    with pytest.raises(ValueError, match="lacks exact historical verifier"):
        p2_2_report.write_summary([missing_marker], str(summary))

    certified_label = dict(result, read_purpose="CERTIFIED_ACCEPTANCE")
    with pytest.raises(ValueError, match="is not HISTORICAL_RAW"):
        p2_2_report.write_summary([certified_label], str(summary))


def test_p2_report_declares_historical_purpose(monkeypatch):
    class PurposeObserved(RuntimeError):
        pass

    def observe(_tag, *, purpose):
        assert purpose is CampaignReadPurpose.HISTORICAL_RAW
        raise PurposeObserved

    monkeypatch.setattr(p2_2_report.replay, "discover_p2_2_dir", observe)
    with pytest.raises(PurposeObserved):
        p2_2_report.report_workload("fixture", {})


def test_real_wal_backoff_repro_bench_tps_requires_commit(real_screen_layout):
    assert _bench_tps(real_screen_layout, _BASELINE) == 8470959.0
    assert _bench_tps(real_screen_layout, _REJECTED) is None
