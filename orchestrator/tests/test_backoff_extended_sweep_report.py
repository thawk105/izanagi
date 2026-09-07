from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import backoff_extended_sweep as S
from orchestrator.campaign import backoff_extended_sweep_report as M
from orchestrator.campaign import backoff_overthrottle as O


def _normal_points(overrides=None):
    overrides = overrides or {}
    points = [
        {
            "variant_id": "none",
            "kind": "none",
            "backoff_us": None,
            "committed": True,
            "certified": True,
            "median_tps": 700.0,
            "tps_reps": [700.0, 700.0, 700.0],
            "cv": 0.0,
            "unstable": False,
            "abort_rate": 0.4,
            "latency_ns": 700.0,
        },
        {
            "variant_id": "adaptive",
            "kind": "adaptive",
            "backoff_us": None,
            "committed": True,
            "certified": True,
            "median_tps": 750.0,
            "tps_reps": [750.0, 750.0, 750.0],
            "cv": 0.0,
            "unstable": False,
            "abort_rate": 0.3,
            "latency_ns": 650.0,
        },
    ]
    for amount in M.EXTENDED_SWEEP_US:
        tps = float(overrides.get(amount, 1000.0 if amount == 10 else 800.0))
        points.append({
            "variant_id": f"static-{amount}",
            "kind": "static",
            "backoff_us": amount,
            "committed": True,
            "certified": True,
            "median_tps": tps,
            "tps_reps": [tps, tps, tps],
            "cv": 0.01,
            "unstable": False,
            "abort_rate": 0.2,
            "latency_ns": 500.0 + amount,
        })
    expected = {}
    for point_index, genome in enumerate(S.genomes("balanced")):
        flags = genome.flags
        if flags["BACK_OFF"] == 0:
            key = ("none", None)
        elif flags["BACKOFF_FIXED"] == -1:
            key = ("adaptive", None)
        else:
            key = ("static", S.decode_static_backoff_us(flags["BACKOFF_FIXED"]))
        expected[key] = (point_index, genome.canonical())
    for point in points:
        point_index, canonical = expected[(point["kind"], point["backoff_us"])]
        point.update({
            "workload": "balanced",
            "workload_coordinates": dict(S.WORKLOAD_BY_TAG["balanced"]),
            "campaign_id": "campaign-balanced",
            "reference_genome": canonical,
            "point_index": point_index,
        })
    return points


def _aa_records(points):
    records = []
    for point in points:
        if point["kind"] == "none":
            back_off, amount, spin = 0, -1, 0.0
        elif point["kind"] == "adaptive":
            back_off, amount, spin = 1, -1, 0.30
        else:
            back_off, amount, spin = 1, point["backoff_us"], point["backoff_us"] / 2000.0
        for rep in range(O.REPS):
            values = {
                "backoff_latency_rate": spin + rep * 0.0001,
                "abort_rate": 0.2,
                "latency_ns": 600.0,
                "tps_aa": 900.0,
                "eff_tps": 950.0,
            }
            records.append({
                "schema_version": O.JSONL_SCHEMA,
                "workload": point["workload"],
                "workload_coordinates": point["workload_coordinates"],
                "campaign_id": point["campaign_id"],
                "reference_variant_id": point["variant_id"],
                "reference_genome": point["reference_genome"],
                "aa_genome": M._aa_genome_canonical(point["reference_genome"]),
                "label": (
                    "none" if point["kind"] == "none" else
                    "adaptive" if point["kind"] == "adaptive" else
                    f"fixed-{point['backoff_us']}us"
                ),
                "point_index": point["point_index"],
                "rep": rep,
                "back_off": back_off,
                "backoff_us": amount,
                "certified": False,
                "diagnostic_only": True,
                "values": {
                    field: {
                        "value": value,
                        "source_measurement": M.ADD_ANALYSIS,
                        "certified": False,
                        "diagnostic_only": True,
                    }
                    for field, value in values.items()
                },
            })
    return records


def test_mu7_single_tail_drop_does_not_establish_onset():
    values = {amount: 1000.0 for amount in M.EXTENDED_SWEEP_US}
    values[1000] = 900.0
    verdict = M.shape_decision(_normal_points(values))
    assert verdict["onset"] == {
        "status": "right_censored",
        "source_measurements": [M.TRACE_DISABLED],
        "onset_grid_us": None,
        "onset_bracket_us": [900, 1000],
        "observed_lower_bound_us": 1000,
    }


def test_single_mid_grid_drop_then_recovery_keeps_onset_unresolved():
    values = {amount: 1000.0 for amount in M.EXTENDED_SWEEP_US}
    dip_index = M.EXTENDED_SWEEP_US.index(150)
    values[M.EXTENDED_SWEEP_US[dip_index]] = 900.0
    for amount in M.EXTENDED_SWEEP_US[dip_index + 2:]:
        values[amount] = 900.0

    verdict = M.shape_decision(_normal_points(values))

    assert verdict["peak"]["status"] == "noncontiguous_noise_plateau"
    assert verdict["onset"]["status"] == "onset_unresolved"


def test_mu8_plateau_contrast_and_boundary_are_never_forced_resolved():
    plateau = M.shape_decision(_normal_points({10: 1000.0, 12: 990.0}))
    assert plateau["peak"]["status"] == "noise_bounded_interval"
    assert plateau["peak"]["noise_equivalent_peak_points_us"] == [10, 12]

    boundary = M.shape_decision(_normal_points({0: 1000.0, 10: 800.0}))
    assert boundary["peak"]["status"] == "boundary_censored"

    contrast_points = _normal_points({10: 1000.0, 12: 950.0})
    candidate = next(point for point in contrast_points if point["backoff_us"] == 12)
    candidate["tps_reps"] = [940.0, 970.0, 990.0]
    contrast = M.shape_decision(contrast_points)
    assert 12 in contrast["peak"]["noise_equivalent_peak_points_us"]


def test_mu10_claim_boundary_is_fixed_and_contains_no_inverse_d496_field():
    verdict = M.shape_decision(_normal_points())
    assert {key: verdict[key] for key in M.CLAIM_BOUNDARY} == {
        "paper_gain_eligible": False,
        "same_campaign_contrast": True,
        "prereg_frozen_comparison_rule": False,
        "estimand_matches_paper_headline": False,
        "claim_scope": "descriptive_backoff_shape_only",
    }
    assert "paired_under_D496" not in verdict


def test_mu14_aa_tps_cannot_change_peak_onset_or_gain_fields():
    normal = _normal_points()
    aa = _aa_records(normal)
    first = M.evaluate_workload(normal, aa)
    mutated = copy.deepcopy(aa)
    for index, row in enumerate(mutated, 1):
        row["values"]["tps_aa"]["value"] = float(index * 100000)
        row["values"]["eff_tps"]["value"] = float(index * 200000)
        row["values"]["abort_rate"]["value"] = float(index % 2)
        row["values"]["backoff_latency_rate"]["value"] = float(index) / 1000.0
        row["values"]["latency_ns"]["value"] = float(index * 300000)
    second = M.evaluate_workload(normal, mutated)
    for field in (
        "peak", "onset", "paper_gain_eligible", "same_campaign_contrast",
        "prereg_frozen_comparison_rule", "estimand_matches_paper_headline", "claim_scope",
    ):
        assert first[field] == second[field]


def test_measurement_tables_keep_the_two_observation_surfaces_separate():
    verdict = M.evaluate_workload(_normal_points(), _aa_records(_normal_points()))
    assert verdict["mechanism"]["trace_disabled_table"]
    assert verdict["mechanism"]["add_analysis_table"]
    for row in verdict["mechanism"]["trace_disabled_table"]:
        assert row["throughput_tps"]["source_measurement"] == M.TRACE_DISABLED
        assert row["abort_rate"]["source_measurement"] == M.TRACE_DISABLED
        assert row["latency_ns"]["source_measurement"] == M.TRACE_DISABLED
    for row in verdict["mechanism"]["add_analysis_table"]:
        assert row["backoff_latency_rate_reps"]["source_measurement"] == M.ADD_ANALYSIS
    assert verdict["point_cvs"]["source_measurement"] == M.TRACE_DISABLED
    assert verdict["peak"]["tmax"]["source_measurement"] == M.TRACE_DISABLED
    assert verdict["peak"]["raw_rep_contrast_intervals"]["source_measurements"] == [
        M.TRACE_DISABLED,
    ]
    assert verdict["mechanism"][
        "spin_occupancy_static_equivalent_bracket_us"
    ]["source_measurements"] == ["configuration", M.ADD_ANALYSIS]
    assert verdict["mechanism"]["spin_range_separated"]["source_measurements"] == [
        M.TRACE_DISABLED, M.ADD_ANALYSIS,
    ]


def test_mu16_aa_consumer_rebinds_rows_and_manifest_points(tmp_path):
    normal = _normal_points()
    rows = _aa_records(normal)
    foreign = copy.deepcopy(rows)
    for row in foreign:
        row["workload"] = "read-heavy"
        row["campaign_id"] = "foreign-campaign"
        row["reference_genome"] = row["reference_genome"].replace(
            "NO_WAIT_OF_TICTOC=0", "NO_WAIT_OF_TICTOC=1",
        )
    with pytest.raises(ValueError, match="certified campaign point"):
        M.evaluate_workload(normal, foreign)
    raw = b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for row in rows
    )
    jsonl = tmp_path / "b10-backoff-overthrottle-balanced.jsonl"
    manifest_path = tmp_path / "b10-backoff-overthrottle-balanced.manifest.json"
    jsonl.write_bytes(raw)
    manifest = {
        "schema_version": O.MANIFEST_SCHEMA,
        "status": "complete",
        "workload": "balanced",
        "workload_coordinates": dict(S.WORKLOAD_BY_TAG["balanced"]),
        "campaign_id": "campaign-balanced",
        "record_count": len(rows),
        "records_sha256": hashlib.sha256(raw).hexdigest(),
        "certified": False,
        "diagnostic_only": True,
        "points": O._summaries(rows),
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    layout = SimpleNamespace(reports_dir=str(tmp_path))
    assert M.load_aa_records(layout, "balanced", normal) == rows
    manifest["points"][0]["campaign_id"] = "foreign-campaign"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest point binding mismatch"):
        M.load_aa_records(layout, "balanced", normal)


def test_mu17_markdown_claim_boundary_is_exactly_the_verdict_projection():
    verdict = M.evaluate_workload(_normal_points(), _aa_records(_normal_points()))
    rendered = M._markdown("balanced", verdict, "plot.png", "data.dat")
    line = next(
        item for item in rendered.splitlines() if item.startswith("Claim boundary JSON: `")
    )
    markdown_boundary = json.loads(line[len("Claim boundary JSON: `"):-1])
    assert markdown_boundary == {key: verdict[key] for key in M.CLAIM_BOUNDARY}
    mutated = copy.deepcopy(verdict)
    mutated["paper_gain_eligible"] = True
    changed = M._markdown("balanced", mutated, "plot.png", "data.dat")
    assert '"paper_gain_eligible":true' in changed


def test_perf_unavailable_and_probe_error_have_distinct_states():
    degraded = M.shape_decision(_normal_points(), perf_preflight_status="unavailable")
    stopped = M.shape_decision(_normal_points(), perf_preflight_status="probe_error")
    assert degraded["status"] == "complete"
    assert degraded["perf_state"] == "unavailable-degraded"
    assert stopped["status"] == "preflight-error-no-verdict"
    assert stopped["peak"] is None and stopped["onset"] is None


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
