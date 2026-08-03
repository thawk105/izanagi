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
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH))

from campaign import p2_2_report, replay, s6_sort_sweep, s8a_trigger_sweep, wal  # noqa: E402
from campaign.artifact_admission import require_admitted_campaign                # noqa: E402
from campaign.backoff_repro import _bench_tps                              # noqa: E402
from campaign.build_admission import (                                     # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from campaign.layout import CampaignLayout                                # noqa: E402
from campaign.model import STAGE_ABORT, STAGE_BENCH_DONE, STAGE_COMMIT     # noqa: E402
from campaign.pin import CURRENT_PIN                                       # noqa: E402
from campaign.source_digest import (                                       # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from critic.digest import load_screen_rejections, load_workload            # noqa: E402

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
        if record["stage"] not in {"build_done", "commit", "abort"}:
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


def test_real_wal_critic_loaders_hide_uncertified_metrics(admitted_real_screen_layout):
    view = require_admitted_campaign(admitted_real_screen_layout)
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
def test_real_wal_sweep_report_rows_gate_on_commit(admitted_real_screen_layout, loader):
    entries = {
        "baseline": {"variant_id": _BASELINE, "category": "full-order"},
        "screened-out": {"variant_id": _REJECTED, "category": "full-order"},
    }
    rows = {r["name"]: r for r in loader(admitted_real_screen_layout, entries)}
    assert rows["baseline"]["certified"] is True
    assert rows["baseline"]["median_tps"] == 8470959.0
    screened = rows["screened-out"]
    assert screened["abort_reason"] == "screen-slower-than-floor"
    assert screened["certified"] is False
    for key in ("median_tps", "cv", "abort_rate", "ipc", "llc_miss_rate"):
        assert screened[key] is None


def test_real_wal_replay_landscape_requires_commit(tmp_path):
    root = tmp_path / "output"
    layout = CampaignLayout(str(
        root / "campaigns" / "p2-2-silo-real-screen-enumerate-fixture"
    )).ensure()
    _write_admitted_real_fixture(Path(layout.root))
    landscape = replay.load_landscape("real-screen", str(root))
    assert set(landscape) == {_BASELINE_GENOME}
    assert landscape[_BASELINE_GENOME].fitness_tps == 8470959.0
    assert _REJECTED_GENOME not in landscape


def test_real_wal_p2_2_report_ranking_requires_commit(real_screen_layout):
    rows = p2_2_report._collect(real_screen_layout)
    assert rows[_REJECTED].median == 1912074.0  # 実 WAL に数値がある正対照
    ranked = p2_2_report._ranked(rows)
    assert [r.variant for r in ranked] == [_BASELINE]
    assert all(r.median != 1912074.0 for r in ranked)


def test_real_wal_backoff_repro_bench_tps_requires_commit(real_screen_layout):
    assert _bench_tps(real_screen_layout, _BASELINE) == 8470959.0
    assert _bench_tps(real_screen_layout, _REJECTED) is None
