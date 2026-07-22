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
from campaign.layout import campaign_layout                     # noqa: E402
from campaign.model import (STAGE_BENCH_DONE, STAGE_COMMIT,     # noqa: E402
                            CampaignConfig, Genome)
from campaign.pipeline import EvalResult, PerfConfig             # noqa: E402


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


def test_prepare_repairs_tail_before_baseline_callback(tmp_path):
    calibration = str(tmp_path / "calibration")
    output = str(tmp_path / "output")
    _write_floor(calibration)
    policy = ident.screening_policy_search_config("baseline-v1", 0.03, 1.5, 2.0)
    cfg = CampaignConfig(
        **{**_cfg().__dict__, "search_config": {**_cfg().search_config, **policy}})
    layout = campaign_layout(str(ident.campaign_id(cfg)), output).ensure()
    wal.write_lock(layout, ident.canonical_preimage(cfg))
    wal.log(layout, "prior", STAGE_COMMIT, "test", {})
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"torn":')
    surfaced = []

    def measure(_cfg, callback_layout):
        assert callback_layout.wal_file == layout.wal_file
        records, truncated = wal.read_records_checked(callback_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"]
        wal.log(callback_layout, "baseline-v1", STAGE_BENCH_DONE, "test", {
            "median_tps": 100.0,
            "leading_indicators": {"abort_rate": 0.1},
        }, ts=10.0)
        wal.log(callback_layout, "baseline-v1", STAGE_COMMIT, "test", {}, ts=11.0)

    screening_driver.prepare_screening_campaign(
        _cfg(), WORKLOAD, "baseline-v1", measure,
        calibration_dir=calibration, output_root=output, log=surfaced.append)
    assert len(surfaced) == 1 and '"status": "repaired"' in surfaced[0]
    assert '"removed_bytes": 8' in surfaced[0]


def test_evaluate_candidate_repairs_tail_before_replay_and_evaluate(
        tmp_path, monkeypatch):
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    wal.write_lock(layout, ident.canonical_preimage(cfg))
    wal.log(layout, "prior", STAGE_COMMIT, "test", {})
    with open(layout.wal_file, "ab") as stream:
        stream.write("途中".encode("utf-8")[:4])
    genome = Genome("silo", {"BACK_OFF": 1})
    calls = []

    def evaluate(candidate, candidate_layout, *args, **kwargs):
        records, truncated = wal.read_records_checked(candidate_layout)
        assert truncated is False and [r.variant for r in records] == ["prior"]
        calls.append(candidate)
        return EvalResult(
            genome=candidate, variant="candidate", certified=True, aborted=False)

    monkeypatch.setattr(screening_driver, "evaluate", evaluate)
    result = screening_driver.evaluate_candidate(
        cfg, layout, genome, PerfConfig(records=1, threads=1), "test", 1800,
        screening=None, src_token="stock", log=lambda message: None)
    assert result is not None and result.certified and calls == [genome]


@pytest.mark.parametrize("failure_kind", ["append", "framing"])
def test_evaluate_candidate_does_not_append_abort_after_wal_io_error(
        tmp_path, monkeypatch, failure_kind):
    cfg = _cfg()
    layout = campaign_layout(str(ident.campaign_id(cfg)), str(tmp_path / "out")).ensure()
    ident.ensure_resumable_wal(cfg, layout)
    genome = Genome("silo", {"BACK_OFF": 1})
    failure = (wal.WalAppendError(
        layout.wal_file, 10, 3, "write", OSError("disk"))
        if failure_kind == "append" else wal.WalFramingError("unframed"))

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(screening_driver, "evaluate", fail)
    with pytest.raises(type(failure)) as caught:
        screening_driver.evaluate_candidate(
            cfg, layout, genome, PerfConfig(records=1, threads=1), "test", 1800,
            screening=None, src_token="stock", log=lambda message: None)
    assert caught.value is failure
    assert wal.read_records(layout) == []
