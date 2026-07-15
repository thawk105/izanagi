# -*- coding: utf-8 -*-
"""D12 層3材料レポートの決定論的な完全射影を検査する。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from campaign import layer3_report  # noqa: E402


ROOT = _HERE.parent.parent
REAL_CAMPAIGN = ROOT / "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"


def _campaign(tmp_path: Path, records, whiteboard=None) -> tuple[Path, Path]:
    output_root = tmp_path / "repo" / "output"
    root = output_root / "campaigns" / "campaign"
    (root / "runs").mkdir(parents=True)
    (root / "campaign.lock").write_text(json.dumps({
        "ccbench_commit": "abc123", "search_config": {"records": 100000, "threads": 4},
        "search_tag": "test", "spec_content": "test", "trial": "trial",
    }), encoding="utf-8")
    (root / "loop_state.json").write_text(json.dumps({"whiteboard": whiteboard or []}), encoding="utf-8")
    (root / "runs/wal.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return root, output_root


def _record(stage, variant="v1", **payload):
    return {"ts": 1.0, "stage": stage, "variant": variant, "env_tag": "test-env", "payload": payload}


def _bench(variant="v1"):
    return _record("bench_done", variant, tps=[1.0], median_tps=1.0, cv=0.0,
                   rounds=1, leading_indicators={})


def test_real_campaign_schema_bijection_views_and_no_matching_floor(tmp_path):
    out = tmp_path / "report.json"
    report = layer3_report.render(REAL_CAMPAIGN, out, generated_from_head="fixed-head")
    assert out.is_file()
    assert len(report["source_refs"]) == 14  # WAL 12 + whiteboard 2
    assert len(report["runs"]) == 2
    assert len(report["verifications"]) == 4
    assert all(row["source_ref"].startswith("wal:") for row in report["runs"] + report["verifications"])
    assert report["rejects"] == []
    assert report["noise_floor"] is None
    assert report["noise_floor_provenance"] == "no-matching-env-record"
    assert "records=100000 threads=4" in report["noise_floor_search"]["summary"]
    layer3_report._validate_schema(json.loads(out.read_text(encoding="utf-8")))


def test_relative_and_absolute_campaign_paths_are_byte_identical(tmp_path, monkeypatch):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    monkeypatch.chdir(ROOT)
    relative = REAL_CAMPAIGN.relative_to(ROOT)
    layer3_report.render(relative, first, generated_from_head="f" * 40)
    layer3_report.render(REAL_CAMPAIGN, second, generated_from_head="f" * 40)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text())["meta"]["campaign_path"] == relative.as_posix()


def test_unknown_stage_fails_closed(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("unknown-stage")])
    with pytest.raises(layer3_report.Layer3ReportError, match="未知"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)


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
    duplicate = _record("build_start", genome="g", src_token="s")
    campaign, output_root = _campaign(tmp_path, [duplicate, duplicate])
    with pytest.raises(layer3_report.Layer3ReportError, match="完全重複"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    whiteboard = {"iteration": 1, "direction": "up", "magnitude": "small", "result": "ok", "delta_pct": None}
    campaign, output_root = _campaign(tmp_path / "whiteboard", [_record("build_start", genome="g", src_token="s")], [whiteboard, whiteboard])
    with pytest.raises(layer3_report.Layer3ReportError, match="完全重複"):
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)


def test_matching_env_floor_is_embedded_with_provenance(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    calibration = output_root / "env/test-env/calibration"
    calibration.mkdir(parents=True)
    floor = {"cv": 0.01, "median": 12.0}
    (calibration / "floor.json").write_text(json.dumps({
        "records": 100000, "threads": 4, "noise_floor": floor,
    }), encoding="utf-8")
    report = layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert report["noise_floor"] == floor
    assert report["noise_floor_provenance"] == "env-record"
    assert report["noise_floor_search"] is None


def test_existing_output_fails_closed(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    out = tmp_path / "exists.json"
    out.write_text("already here", encoding="utf-8")
    with pytest.raises(layer3_report.Layer3ReportError, match="既に存在"):
        layer3_report.render(campaign, out, generated_from_head="fixed", output_root=output_root)


def test_variant_without_commit_is_reject_with_primary_reference(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", "rejected", genome="g", src_token="s"), _bench("rejected"),
    ])
    report = layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert report["rejects"][0]["variant"] == "rejected"
    assert report["rejects"][0]["reason"] == "commit-event-absent"
    assert report["rejects"][0]["source_ref"] in report["source_refs"]


@pytest.mark.parametrize("section", ["variants", "runs", "verifications", "rejects", "whiteboard"])
def test_schema_rejects_empty_material_items(section, tmp_path):
    report = layer3_report.build_report(REAL_CAMPAIGN, generated_from_head="fixed")
    report[section] = [{}]
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_git_head_is_real_repository_head():
    head = layer3_report._git_head(ROOT)
    assert len(head) == 40
    assert all(char in "0123456789abcdef" for char in head)


def test_campaign_outside_repo_fails_closed(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(layer3_report.Layer3ReportError, match="repo 外"):
        layer3_report.build_report(outside, generated_from_head="fixed")
