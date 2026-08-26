from __future__ import annotations

import copy

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
                "reference_variant_id": point["variant_id"],
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
        "status": "onset_unresolved",
        "onset_grid_us": None,
        "onset_bracket_us": None,
    }


def test_mu8_plateau_contrast_and_boundary_are_never_forced_resolved():
    plateau = M.shape_decision(_normal_points({10: 1000.0, 12: 990.0}))
    assert plateau["peak"]["status"] == "noise_bounded_interval"
    assert plateau["peak"]["noise_equivalent_peak_points_us"] == [10, 12]

    boundary = M.shape_decision(_normal_points({1: 1000.0, 10: 800.0}))
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


def test_perf_unavailable_and_probe_error_have_distinct_states():
    degraded = M.shape_decision(_normal_points(), perf_preflight_status="unavailable")
    stopped = M.shape_decision(_normal_points(), perf_preflight_status="probe_error")
    assert degraded["status"] == "complete"
    assert degraded["perf_state"] == "unavailable-degraded"
    assert stopped["status"] == "preflight-error-no-verdict"
    assert stopped["peak"] is None and stopped["onset"] is None
