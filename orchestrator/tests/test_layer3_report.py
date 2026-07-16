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
YCSB = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}


def _campaign(tmp_path: Path, records, whiteboard=None, *, loop_state=True,
              ycsb=None) -> tuple[Path, Path]:
    output_root = tmp_path / "repo" / "output"
    root = output_root / "campaigns" / "campaign"
    (root / "runs").mkdir(parents=True)
    search_config = {"records": 100000, "threads": 4}
    if ycsb is not None:
        search_config["ycsb"] = ycsb
    (root / "campaign.lock").write_text(json.dumps({
        "ccbench_commit": "abc123", "search_config": search_config,
        "search_tag": "test", "spec_content": "test", "trial": "trial",
    }), encoding="utf-8")
    if loop_state:
        (root / "loop_state.json").write_text(
            json.dumps({"whiteboard": whiteboard if whiteboard is not None else []}),
            encoding="utf-8")
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
    assert report["schema_version"] == "layer3-material-report/v2"
    assert report["whiteboard_provenance"] == "loop_state"
    assert len(report["runs"]) == 2
    assert len(report["verifications"]) == 4
    assert all(row["source_ref"].startswith("wal:") for row in report["runs"] + report["verifications"])
    assert report["rejects"] == []
    assert report["aborts"] == []
    for kind in ("within_run", "between_run"):
        floor = report["noise_floor"][kind]
        assert floor["value"] is None
        assert floor["provenance"] == "no-matching-env-record"
        assert floor["source"] is None
        assert floor["search"]["campaign_has_no_ycsb"] is True
    layer3_report._validate_schema(json.loads(out.read_text(encoding="utf-8")))


def test_campaign_without_loop_state_has_empty_absent_whiteboard(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], loop_state=False)
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["whiteboard"] == []
    assert report["whiteboard_provenance"] == "absent"
    assert not any(ref.startswith("wb:") for ref in report["source_refs"])


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
def test_schema_rejects_missing_or_invalid_whiteboard_provenance(provenance):
    report = layer3_report.build_report(REAL_CAMPAIGN, generated_from_head="fixed")
    if provenance is None:
        del report["whiteboard_provenance"]
    else:
        report["whiteboard_provenance"] = provenance
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


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
        "variant": "aborted",
        "reason": "build-error",
        "source_ref": report["aborts"][0]["source_ref"],
    }]
    assert report["aborts"][0]["source_ref"] in report["source_refs"]
    assert report["rejects"][0]["variant"] == "aborted"
    assert report["rejects"][0]["reason"] == "commit-event-absent"


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


@pytest.mark.parametrize("section", ["variants", "runs", "verifications", "rejects", "aborts", "whiteboard"])
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
