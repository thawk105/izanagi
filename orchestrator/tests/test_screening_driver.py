# -*- coding: utf-8 -*-
"""偵察 sweep 専用 screening driver の計測なし単体テスト。"""
from __future__ import annotations

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import ident, screening_driver, wal               # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_COMMIT,     # noqa: E402
                            CampaignConfig)


WORKLOAD = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}


def _cfg():
    return CampaignConfig(
        spec_slug="screen-driver", search_tag="sweep", spec_content="fixture",
        ccbench_commit="deadbeef", search_config={"workload": "balanced"},
        trial="fixture")


def _write_floor(root, *, floor=0.03, workload=WORKLOAD):
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "between_run_noise_fixture.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"workload": workload, "between_run": {"cv": floor}}, f)
    return path


def test_prepare_screening_bakes_identity_and_uses_new_same_campaign_baseline(tmp_path):
    calibration = str(tmp_path / "calibration")
    output = str(tmp_path / "output")
    _write_floor(calibration, floor=0.03000001)
    seen = {}

    def measure(cfg, layout):
        seen["cfg"] = cfg
        seen["layout"] = layout
        assert cfg.search_config["screening"] == {
            "baseline_ref": "baseline-v1", "floor": "0.03000001", "k": "1.5",
            "high_abort_factor": "2.0"}
        wal.log(layout, "baseline-v1", STAGE_BENCH_DONE, "test", {
            "median_tps": 10000.0,
            "leading_indicators": {"abort_rate": 0.04},
        }, ts=1234.0)
        wal.log(layout, "baseline-v1", STAGE_COMMIT, "test", {
            "fitness_tps": 10000.0,
        }, ts=1235.0)

    prepared = screening_driver.prepare_screening_campaign(
        _cfg(), WORKLOAD, "baseline-v1", measure,
        calibration_dir=calibration, output_root=output)
    assert prepared.cfg is seen["cfg"] and prepared.layout is seen["layout"]
    assert prepared.screening.baseline_tps == 10000.0
    assert prepared.screening.baseline_abort_rate == 0.04
    assert prepared.screening.baseline_measured_at == 1234.0
    assert prepared.screening.floor == 0.03000001
    ident.verify_screening_preimage(
        prepared.screening, wal.read_lock(prepared.layout))


def test_prepare_screening_fails_closed_when_floor_json_missing(tmp_path):
    called = False

    def measure(_cfg, _layout):
        nonlocal called
        called = True

    with pytest.raises(ValueError, match="floor JSON"):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            calibration_dir=str(tmp_path / "missing"), output_root=str(tmp_path / "out"))
    assert called is False


@pytest.mark.parametrize("missing", ["median", "abort_rate", "commit"])
def test_prepare_screening_requires_complete_baseline_evidence(tmp_path, missing):
    calibration = str(tmp_path / f"cal-{missing}")
    _write_floor(calibration)

    def measure(_cfg, layout):
        payload = {"median_tps": 100.0,
                   "leading_indicators": {"abort_rate": 0.1}}
        if missing == "median":
            payload.pop("median_tps")
        if missing == "abort_rate":
            payload["leading_indicators"].pop("abort_rate")
        wal.log(layout, "baseline-v1", STAGE_BENCH_DONE, "test", payload, ts=10.0)
        if missing != "commit":
            wal.log(layout, "baseline-v1", STAGE_COMMIT, "test", {}, ts=11.0)

    with pytest.raises(ValueError):
        screening_driver.prepare_screening_campaign(
            _cfg(), WORKLOAD, "baseline-v1", measure,
            calibration_dir=calibration, output_root=str(tmp_path / f"out-{missing}"))
