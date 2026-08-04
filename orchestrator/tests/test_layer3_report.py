# -*- coding: utf-8 -*-
"""D12 層3材料レポートの決定論的な完全射影を検査する。"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from campaign import layer3_report, model  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from campaign.pin import CURRENT_PIN  # noqa: E402
from campaign.source_digest import (  # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)


ROOT = _HERE.parent.parent
REAL_CAMPAIGN = ROOT / "output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"
YCSB = {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"}
ABORTED_FIXTURE_VARIANT = "2225adf39fa3"
REJECTED_FIXTURE_VARIANT = "d85dc0fc5a6e"


def _admission_bound_records(tmp_path: Path, records: list[dict]) -> tuple[list[dict], dict]:
    """Turn semantic Layer3 fixtures into independently generated post-policy WAL."""
    copied = json.loads(json.dumps(records))
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    labels = list(dict.fromkeys(record["variant"] for record in copied))
    by_label = {label: [record for record in copied if record["variant"] == label]
                for label in labels}
    bindings = {}
    for ordinal, label in enumerate(labels):
        group = by_label[label]
        stages = {record["stage"] for record in group}
        needs_start = bool(stages & {
            "build_start", "build_done", "verify_done", "bench_done", "commit",
        })
        if not needs_start:
            continue
        protocol = f"fixture-{hashlib.sha256(label.encode()).hexdigest()[:8]}"
        canonical = f"{protocol}|"
        variant = hashlib.sha256(canonical.encode()).hexdigest()[:12]
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=str(tmp_path.resolve()),
            ccbench_commit=CURRENT_PIN,
            genome_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
            src_token="stock",
            source_bytes_sha256="a" * 64,
            tracked_clean=True,
            tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )
        receipt = derive_build_admission(context, evidence).as_wal_receipt()
        bindings[label] = {
            "attempt": f"fixture-attempt-{ordinal}",
            "canonical": canonical,
            "variant": variant,
            "receipt": receipt,
        }

    rendered = []
    started = set()
    for record in copied:
        label = record["variant"]
        binding = bindings.get(label)
        if binding is None:
            rendered.append(record)
            continue
        if label not in started and record["stage"] != "build_start":
            rendered.append({
                "ts": record["ts"],
                "stage": "build_start",
                "variant": binding["variant"],
                "env_tag": record["env_tag"],
                "payload": {
                    "genome": binding["canonical"],
                    "src_token": "stock",
                    "build_attempt_id": binding["attempt"],
                    "build_admission": binding["receipt"],
                    "build_admission_receipt_sha256": binding["receipt"]["receipt_sha256"],
                },
            })
            started.add(label)
        record["variant"] = binding["variant"]
        if record["stage"] == "build_start":
            record["payload"].update({
                "genome": binding["canonical"],
                "src_token": "stock",
                "build_attempt_id": binding["attempt"],
                "build_admission": binding["receipt"],
                "build_admission_receipt_sha256": binding["receipt"]["receipt_sha256"],
            })
            started.add(label)
        elif record["stage"] in {"build_done", "commit", "abort"}:
            record["payload"]["build_attempt_id"] = binding["attempt"]
            record["payload"]["build_admission_receipt_sha256"] = (
                binding["receipt"]["receipt_sha256"]
            )
        rendered.append(record)
    return rendered, dict(context.policy.as_preimage())


def _campaign(tmp_path: Path, records, whiteboard=None, *, loop_state=True,
              ycsb=None) -> tuple[Path, Path]:
    output_root = tmp_path / "repo" / "output"
    root = output_root / "campaigns" / "campaign"
    (root / "runs").mkdir(parents=True)
    records, admission_policy = _admission_bound_records(tmp_path, records)
    search_config = {
        "records": 100000,
        "threads": 4,
        "build_admission": admission_policy,
    }
    if ycsb is not None:
        search_config["ycsb"] = ycsb
    (root / "campaign.lock").write_text(json.dumps({
        "ccbench_commit": CURRENT_PIN, "search_config": search_config,
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


def _bench(variant="v1", **extra):
    return _record("bench_done", variant, tps=[1.0], median_tps=1.0, cv=0.0,
                   rounds=1, leading_indicators={}, **extra)


def test_real_legacy_s8a_campaign_is_rejected(tmp_path):
    out = tmp_path / "report.json"
    with pytest.raises(layer3_report.Layer3ReportError, match="legacy-unclassified"):
        layer3_report.render(REAL_CAMPAIGN, out, generated_from_head="fixed-head")
    assert not out.exists()


def test_campaign_without_loop_state_has_empty_absent_whiteboard(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")], loop_state=False)
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root)
    assert report["whiteboard"] == []
    assert report["whiteboard_provenance"] == "absent"
    assert not any(ref.startswith("wb:") for ref in report["source_refs"])
    assert report["schema_version"] == "layer3-material-report/v4"
    decision = report["admission_decision"]
    assert decision["classification"] == "admitted-new-schema"
    assert decision["admission_status"] == "admitted"
    assert decision["overlay"]["record_key"] is None
    assert "claim_boundaries" not in report


def test_v4_trigger_claim_boundaries_are_required_and_fixed(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    lock_path = campaign / "campaign.lock"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["search_config"]["axis"] = "silo-backoff-trigger-gating"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    assert report["claim_boundaries"] == {
        "scope": "trigger-gating",
        "classification": "finite-policy-selection",
        "headline_synthesis_evidence": False,
    }
    broken = json.loads(json.dumps(report))
    del broken["claim_boundaries"]
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(broken)


def test_reinspection_ledger_path_is_propagated_to_shared_admission(tmp_path, monkeypatch):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    ledger_path = tmp_path / "detached-reinspection.json"
    original = layer3_report.require_admitted_campaign
    observed = []

    def checked(campaign_value, *, reinspection_ledger=None):
        observed.append(reinspection_ledger)
        return original(campaign_value, reinspection_ledger=reinspection_ledger)

    monkeypatch.setattr(layer3_report, "require_admitted_campaign", checked)
    layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
        reinspection_ledger=ledger_path,
    )
    assert observed == [ledger_path]


def test_schema_accepts_overlay_historical_trigger_receipt_and_requires_proofs(
        tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    decision = report["admission_decision"]
    decision.update({
        "classification": "historical-trigger-reinspected",
        "admission_status": "admitted-reinspected",
        "verification_status": "historically-certified",
        "policy_sha256": None,
        "attempt_receipt_sha256s": [],
        "reinspection": {
            "ledger_sha256": "a" * 64,
            "record_sha256s": ["b" * 64],
        },
    })
    layer3_report._validate_schema(report)

    for mutation in ("missing", "null-ledger", "empty-records"):
        broken = json.loads(json.dumps(report))
        if mutation == "missing":
            broken["admission_decision"].pop("reinspection")
        elif mutation == "null-ledger":
            broken["admission_decision"]["reinspection"]["ledger_sha256"] = None
        else:
            broken["admission_decision"]["reinspection"]["record_sha256s"] = []
        with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
            layer3_report._validate_schema(broken)


def test_schema_rejects_reinspection_overlay_on_nontrigger_classification(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    report["admission_decision"]["reinspection"] = {
        "ledger_sha256": "a" * 64,
        "record_sha256s": ["b" * 64],
    }
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_legacy_v2_report_schema_remains_readable(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    legacy = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    legacy["schema_version"] = "layer3-material-report/v2"
    del legacy["admission_decision"]
    layer3_report._validate_schema(legacy)


def test_legacy_v3_report_schema_remains_readable(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    legacy = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    legacy["schema_version"] = "layer3-material-report/v3"
    legacy.pop("claim_boundaries", None)
    legacy["admission_decision"]["schema_version"] = (
        "campaign-artifact-admission-decision/v1"
    )
    legacy["admission_decision"].pop("reinspection", None)
    layer3_report._validate_schema(legacy)


def test_bench_rep_returncodes_passes_real_view_and_schema(tmp_path):
    """M-P10: bench event の新 key が _view_row を経ても実 schema 検証を通る。"""
    campaign, output_root = _campaign(
        tmp_path, [_bench(rep_returncodes=[0, 0, 0, 0, 0])],
    )

    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )

    assert report["runs"][0]["rep_returncodes"] == [0, 0, 0, 0, 0]


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
def test_schema_rejects_missing_or_invalid_whiteboard_provenance(provenance, tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
    if provenance is None:
        del report["whiteboard_provenance"]
    else:
        report["whiteboard_provenance"] = provenance
    with pytest.raises(layer3_report.Layer3ReportError, match="schema"):
        layer3_report._validate_schema(report)


def test_relative_and_absolute_campaign_paths_are_byte_identical(tmp_path, monkeypatch):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    monkeypatch.chdir(output_root.parent)
    relative = campaign.relative_to(output_root.parent)
    layer3_report.render(relative, first, generated_from_head="f" * 40, output_root=output_root)
    layer3_report.render(campaign, second, generated_from_head="f" * 40, output_root=output_root)
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text())["meta"]["campaign_path"] == relative.as_posix()


def test_unknown_stage_fails_closed(tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("unknown-stage")])
    with pytest.raises(layer3_report.Layer3ReportError, match="unknown WAL stage") as exc_info:
        layer3_report.build_report(campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalLineError)


def test_shared_known_session_stage_is_outside_layer3_semantic_subset(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record(model.STAGE_S1_SESSION, event="session-start")],
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="未知の WAL stage"):
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )


def test_nested_duplicate_wal_key_fails_closed_for_one_reason(tmp_path):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "runs/wal.jsonl").write_bytes(
        b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
        b'"ts":1,"payload":{"genome":"g","src_token":"s",'
        b'"details":{"fitness_tps":1,"fitness_tps":2}}}\n',
    )
    with pytest.raises(layer3_report.Layer3ReportError, match="WAL record が不正") as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalDuplicateKeyError)
    assert "duplicate key" in str(exc_info.value)


@pytest.mark.parametrize(
    ("raw_line", "expected_cause"),
    [
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env","ts":1}\n',
            "missing=['payload']", id="missing-key",
        ),
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
            b'"ts":1,"payload":{},"extra":true}\n',
            "unknown=['extra']", id="unknown-key",
        ),
        pytest.param(
            b'{"variant":"v1","stage":1,"env_tag":"test-env",'
            b'"ts":1,"payload":{}}\n',
            "WAL stage must be a string", id="wrong-type",
        ),
        pytest.param(
            b'{"variant":"v1","stage":"build_start","env_tag":"test-env",'
            b'"ts":1,"payload":["bad"]}\n',
            "WAL payload must be a JSON object", id="non-object-payload",
        ),
    ],
)
def test_wal_wrapper_preserves_specific_parser_diagnosis(
        tmp_path, raw_line, expected_cause):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")])
    (campaign / "runs/wal.jsonl").write_bytes(raw_line)

    with pytest.raises(layer3_report.Layer3ReportError) as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)

    assert expected_cause in str(exc_info.value)


def test_wal_blank_between_records_uses_shared_strict_contract(tmp_path):
    campaign, output_root = _campaign(tmp_path, [
        _record("build_start", variant="v1", genome="g", src_token="s"),
        _record("build_start", variant="v2", genome="h", src_token="t"),
    ])
    wal_path = campaign / "runs/wal.jsonl"
    lines = wal_path.read_text(encoding="utf-8").splitlines(keepends=True)
    wal_path.write_text(lines[0] + "\n" + lines[1], encoding="utf-8")

    with pytest.raises(
            layer3_report.Layer3ReportError, match="WAL line must not be empty",
    ) as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root)
    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalLineError)


@pytest.mark.parametrize("tail_kind", ["complete-json", "multibyte-partial"])
def test_unframed_wal_tail_is_translated_with_framing_cause(tmp_path, tail_kind):
    campaign, output_root = _campaign(
        tmp_path, [_record("build_start", genome="g", src_token="s")],
    )
    wal_path = campaign / "runs/wal.jsonl"
    if tail_kind == "complete-json":
        wal_path.write_bytes(wal_path.read_bytes()[:-1])
    else:
        with wal_path.open("ab") as stream:
            stream.write(b'{"variant":"broken-\xe3\x81')

    with pytest.raises(layer3_report.Layer3ReportError, match="WAL framing") as exc_info:
        layer3_report.build_report(
            campaign, generated_from_head="fixed", output_root=output_root,
        )

    assert isinstance(exc_info.value.__cause__, layer3_report.wal.WalFramingError)


def test_direct_script_starts_with_clean_pythonpath(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(Path(layer3_report.__file__).resolve()), "--help"],
        cwd=tmp_path, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "campaign_dir" in completed.stdout


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
    duplicate = _bench()
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
        "variant": ABORTED_FIXTURE_VARIANT,
        "reason": "build-error",
        "source_ref": report["aborts"][0]["source_ref"],
    }]
    assert report["aborts"][0]["source_ref"] in report["source_refs"]
    assert report["rejects"][0]["variant"] == ABORTED_FIXTURE_VARIANT
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
    assert report["rejects"][0]["variant"] == REJECTED_FIXTURE_VARIANT
    assert report["rejects"][0]["reason"] == "commit-event-absent"
    assert report["rejects"][0]["source_ref"] in report["source_refs"]


@pytest.mark.parametrize("section", ["variants", "runs", "verifications", "rejects", "aborts", "whiteboard"])
def test_schema_rejects_empty_material_items(section, tmp_path):
    campaign, output_root = _campaign(tmp_path, [_record("build_start", genome="g", src_token="s")])
    report = layer3_report.build_report(
        campaign, generated_from_head="fixed", output_root=output_root,
    )
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
