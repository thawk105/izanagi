from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign import backoff_nonmonotonicity_analysis as analysis


def _events() -> list[dict]:
    return [
        {
            "seq": 0,
            "window_us": 10,
            "window_commits": 10,
            "backoff_before": 0.0,
            "backoff_after": 1.0,
            "gradient_sign": -1,
        },
        {
            "seq": 1,
            "window_us": 5,
            "window_commits": 10,
            "backoff_before": 1.0,
            "backoff_after": 2.0,
            "gradient_sign": 1,
        },
        {
            "seq": 2,
            "window_us": 10,
            "window_commits": 10,
            "backoff_before": 2.0,
            "backoff_after": 1.0,
            "gradient_sign": -1,
        },
        {
            "seq": 3,
            "window_us": 20,
            "window_commits": 10,
            "backoff_before": 1.0,
            "backoff_after": 1.0,
            "gradient_sign": 1,
        },
    ]


def _trace_document() -> dict:
    return {
        "trace_runs": [
            {
                "cell": "cw",
                "step_us": 1.0,
                "update_us": 2560,
                "ceiling_us": 1000,
                "count_window": 10000,
                "count_cap_us": 9_223_372_036_854_775_807,
                "threads": 48,
                "workload": "write-heavy",
                "trace_events": _events(),
                "directional_success": {
                    "scored": 3,
                    "successes": 2,
                    "rate": 2 / 3,
                },
            }
        ]
    }


def _stock_readme(*, state_zero_count: int = 1, state_100_count: int = 1) -> str:
    rows = [
        "| field | value | call比 |",
        "|---|---:|---:|",
        "| `call_count` | 11 | 100.000% |",
        "| `requested_us_sum` | 5,500 | — |",
    ]
    for state in range(0, 1001, 100):
        count = (
            state_zero_count
            if state == 0
            else state_100_count
            if state == 100
            else 1
        )
        rows.append(f"| `state_{state}_call_count` | {count} | 0.000% |")
    rows.extend(
        (
            "| `unknown_state_call_count` | 0 | 0.000% |",
            "| `counter_overflowed` | false | — |",
        )
    )
    return "\n".join(rows) + "\n"


def _static_readme() -> str:
    return """# Static tail

### 1.1 older measured curve

| b (µs) | write-heavy | balanced | read-heavy |
| --- | --- | --- | --- |
| 100 | 2,000 / 0.1000 | 1,500 / 0.2000 | 3,000 / 0.0500 |
| **150** | **1,800 / 0.0900** | **1,400 / 0.1800** | **2,800 / 0.0450** |
| **750** | **欠測** | **欠測** | **欠測** |
| **1000** | **無効** (2,100 / 0.7000) | **無効** (3,100 / 0.6000) | **無効** (8,100 / 0.1500) |

### 8.1 newer measured curve

| b (µs) | write-heavy | balanced | read-heavy |
| --- | --- | --- | --- |
| 150 | 1,801 / 0.0890 | 1,401 / 0.1790 | 2,801 / 0.0440 |
| **750** | **1,100 / 0.0490** | **800 / 0.0670** | **1,900 / 0.0270** |
| **999** | **990 / 0.0420** | **720 / 0.0580** | **1,700 / 0.0230** |
"""


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    trace_dir = tmp_path / "trace"
    nested = trace_dir / "nested"
    nested.mkdir(parents=True)
    trace_path = nested / "fixture.nqsv.json"
    trace_path.write_text(json.dumps(_trace_document()) + "\n", encoding="utf-8")
    stock = tmp_path / "stock.md"
    stock.write_text(_stock_readme(), encoding="utf-8")
    static = tmp_path / "static.md"
    static.write_text(_static_readme(), encoding="utf-8")
    return trace_dir, trace_path, stock, static


def _analyze(inputs: tuple[Path, Path, Path, Path]) -> dict:
    trace_dir, _trace_path, stock, static = inputs
    return analysis.analyze_nonmonotonicity(trace_dir, stock, static)


def _baseline_tps() -> dict[str, float]:
    return {
        "nm-step0.5": 160.0,
        "nm-step1": 100.0,
        "nm-step2": 90.0,
        "nm-step25": 100.0,
        "nm-step100": 110.0,
    }


def _simple_new_events(*, high_count: int = 0, count: int = 61) -> list[dict]:
    return [
        {
            "window_us": 100,
            "window_commits": 10 + index % 3,
            "backoff_before": 200.0 if index < high_count else 10.0,
            "backoff_after": 201.0 if index < high_count else 11.0,
            "gradient_sign": 1 if index % 2 else -1,
            "trigger": "time",
        }
        for index in range(count)
    ]


def _edge_events(*, narrow: bool) -> list[dict]:
    per_segment = []
    positive_edge = (0.0, 1.0)
    if narrow:
        per_segment.extend(
            (positive_edge, bool(index % 2)) for index in range(50)
        )
        for edge_index in range(1, 10):
            edge = (float(edge_index * 2), float(edge_index * 2 + 1))
            per_segment.extend((edge, True) for _ in range(2))
    else:
        per_segment.extend((positive_edge, True) for _ in range(50))
        for edge_index in range(1, 10):
            edge = (float(edge_index * 2), float(edge_index * 2 + 1))
            per_segment.extend(
                (edge, bool(index % 2)) for index in range(100)
            )
    observations = per_segment * 3
    events = []
    for index in range(len(observations) + 1):
        edge = observations[index][0] if index < len(observations) else (0.0, 1.0)
        positive = False if index == 0 else observations[index - 1][1]
        events.append(
            {
                "window_us": 100,
                "window_commits": 10 + index % 3,
                "backoff_before": edge[0],
                "backoff_after": edge[1],
                "gradient_sign": 1 if positive else -1,
                "trigger": "time",
            }
        )
    return events


def _direction_sensitive_edge_events(*, narrow: bool) -> list[dict]:
    observations = []
    for segment in range(3):
        for edge_index in range(10):
            edge = (float(edge_index * 2), float(edge_index * 2 + 1))
            if not narrow:
                signs = (True, True)
            elif segment < 2 or edge_index == 0:
                signs = (False, True)
            else:
                signs = (True, True)
            observations.extend((edge, sign) for sign in signs)
    events = []
    for index in range(len(observations) + 1):
        edge = observations[index][0] if index < len(observations) else (0.0, 1.0)
        positive = False if index == 0 else observations[index - 1][1]
        events.append(
            {
                "window_us": 100,
                "window_commits": 10 + index % 3,
                "backoff_before": edge[0],
                "backoff_after": edge[1],
                "gradient_sign": 1 if positive else -1,
                "trigger": "time",
            }
        )
    return events


def _new_trace_document() -> dict:
    observed_tps = {
        "nm-step0.5": 176.0,
        "nm-step1": 110.0,
        "nm-step1-u2560": 150.0,
        "nm-step2": 99.0,
        "nm-step25": 110.0,
        "nm-step100": 121.0,
    }
    runs = []
    for cell, (step_us, update_us) in analysis._NEW_TRACE_CELL_AXES.items():
        if cell == "nm-step1":
            events = _edge_events(narrow=True)
        elif cell == "nm-step1-u2560":
            events = _edge_events(narrow=False)
        elif cell == "nm-step0.5":
            events = _simple_new_events(high_count=1)
        elif cell == "nm-step25":
            events = _simple_new_events(high_count=31)
        else:
            events = _simple_new_events(high_count=20)
        dropped = 1 if cell == "nm-step0.5" else 0
        runs.append(
            {
                "cell": cell,
                "step_us": step_us,
                "update_us": update_us,
                "threads": 48,
                "workload": "write-heavy",
                "median_tps": observed_tps[cell],
                "throughputs": [observed_tps[cell]],
                "extime": 1.0,
                "trace_summary": {
                    "updates": len(events) + dropped,
                    "retained": len(events),
                    "dropped": dropped,
                },
                "trace_events": events,
            }
        )
    return {"trace_runs": runs}


def _write_new_trace(tmp_path: Path, document: dict | None = None) -> Path:
    path = tmp_path / "new-trace.json"
    path.write_text(
        json.dumps(document or _new_trace_document()) + "\n", encoding="utf-8"
    )
    return path


def _new_run(document: dict, cell: str) -> dict:
    return next(run for run in document["trace_runs"] if run["cell"] == cell)


def _analyze_new(
    inputs: tuple[Path, Path, Path, Path],
    new_trace: Path,
) -> dict:
    trace_dir, _trace_path, stock, static = inputs
    return analysis.analyze_nonmonotonicity(
        trace_dir,
        stock,
        static,
        new_trace_json=new_trace,
        baseline_tps=_baseline_tps(),
        static_low_b={0: 1000, 100: 500},
    )["new_trace_analysis"]


def test_poisson_verdict_is_not_adjudicated_for_low_and_high_dispersion(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    positive = _analyze(inputs)
    positive_dispersion = positive["window_count_dispersion"]
    assert positive_dispersion["poisson_verdict"] == "not_adjudicated"
    assert positive_dispersion["not_adjudicated_reason"] == (
        "The accepted trace inventory can mix count-triggered and time-triggered "
        "cells, while both window_us and Backoff_ may vary within a run; the "
        "recorded window-count dispersion is therefore descriptive and does not "
        "adjudicate a Poisson mechanism."
    )
    assert positive_dispersion["runs"][0]["window_commits"][
        "variance_over_mean"
    ] == 0.0

    document = _trace_document()
    document["trace_runs"][0]["trace_events"][3]["window_commits"] = 1_000
    inputs[1].write_text(json.dumps(document) + "\n", encoding="utf-8")
    negative = _analyze(inputs)["window_count_dispersion"]
    assert negative["runs"][0]["window_commits"]["variance_over_mean"] > 100
    assert negative["poisson_verdict"] == "not_adjudicated"
    assert negative["not_adjudicated_reason"] == (
        "The accepted trace inventory can mix count-triggered and time-triggered "
        "cells, while both window_us and Backoff_ may vary within a run; the "
        "recorded window-count dispersion is therefore descriptive and does not "
        "adjudicate a Poisson mechanism."
    )


def test_decision_labels_and_stock_rechecks_survive_one_broken_bucket(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    positive = _analyze(inputs)
    assert positive["schema_version"] == (
        "izanagi-t2188-nonmonotonicity-analysis/v1"
    )
    assert positive["certified"] is False
    assert positive["headline_eligible"] is False
    assert positive["throughput_scope"] == "diagnostic_only"
    assert positive["stock_residence_t1941"]["estimand"] == "call_weighted"
    assert positive["stock_residence_t1941"]["workload"] == "balanced"
    assert positive["stock_residence_t1941"]["decision_eligible"] is False
    assert positive["stock_residence_t1941"][
        "bucket_call_count_matches_call_count"
    ] is True
    assert positive["stock_residence_t1941"][
        "weighted_sum_matches_requested_us_sum"
    ] is True
    assert positive["static_curve"]["mixture_assumption_required"] is True
    assert positive["static_curve"]["decision_eligible"] is False

    inputs[2].write_text(_stock_readme(state_zero_count=2), encoding="utf-8")
    negative = _analyze(inputs)
    assert negative["stock_residence_t1941"][
        "bucket_call_count_matches_call_count"
    ] is False
    assert negative["stock_residence_t1941"][
        "weighted_sum_matches_requested_us_sum"
    ] is True
    assert negative["stock_residence_t1941"]["decision_eligible"] is False
    assert negative["static_curve"]["mixture_assumption_required"] is True
    assert negative["static_curve"]["decision_eligible"] is False


def test_nonzero_bucket_breaks_weighted_sum_recheck(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    inputs[2].write_text(_stock_readme(state_100_count=2), encoding="utf-8")
    negative = _analyze(inputs)["stock_residence_t1941"]
    assert negative["bucket_call_count_matches_call_count"] is False
    assert negative["weighted_sum_matches_requested_us_sum"] is False


def test_static_curve_selects_newer_of_two_matching_tables(tmp_path: Path) -> None:
    static_curve = _analyze(_write_inputs(tmp_path))["static_curve"]
    assert static_curve["source_table"] == {
        "selection_rule": "last_matching_header",
        "identifier": "8.1 newer measured curve",
        "header_line": 14,
    }
    assert [point["backoff_us"] for point in static_curve["points"]] == [
        150,
        750,
        999,
    ]
    assert static_curve["points"][1]["measurements"]["write-heavy"] == {
        "status": "measured",
        "throughput_tps": 1100,
        "abort_rate": 0.049,
    }


def test_directional_success_is_recomputed_after_saved_value_is_changed(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    result = _analyze(inputs)
    assert "directional_success_identity" not in result
    positive = result["directional_success_recomputation"]
    assert positive["ground_truth_independent"] is False
    assert positive["dependency_note"] == (
        "This is not accuracy against independent ground truth: recomputed "
        "success and the following event's gradient_sign use the same throughput "
        "difference; the following gradient is that difference divided by the "
        "preceding action."
    )
    assert positive["mismatch_pair_count"] == 0
    assert positive["runs"][0]["stored_directional_successes"] == 2
    assert positive["runs"][0]["recomputed_directional_successes"] == 2
    assert positive["runs"][0]["stored_total_matches_recomputed"] is True
    assert positive["runs"][0]["terminal_pair_count"] == 0

    changed = _trace_document()
    changed["trace_runs"][0]["directional_success"]["successes"] = 3
    inputs[1].write_text(json.dumps(changed) + "\n", encoding="utf-8")
    negative = _analyze(inputs)["directional_success_recomputation"]
    assert negative["runs"][0]["stored_directional_successes"] == 3
    assert negative["runs"][0]["recomputed_directional_successes"] == 2
    assert negative["runs"][0]["stored_total_matches_recomputed"] is False


def test_directional_success_recomputation_detects_offsetting_pair_mismatches(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    changed = _trace_document()
    changed_events = changed["trace_runs"][0]["trace_events"]
    changed_events[1]["gradient_sign"] = -1
    changed_events[2]["gradient_sign"] = 1
    changed_events[3]["terminal_flush"] = 1
    inputs[1].write_text(json.dumps(changed) + "\n", encoding="utf-8")
    negative = _analyze(inputs)["directional_success_recomputation"]
    assert negative["stored_successes_total"] == 2
    assert negative["recomputed_directional_successes_total"] == 2
    assert negative["mismatch_pair_count"] == 2
    assert negative["mismatch_pairs"] == [
        {
            "run": negative["runs"][0]["run"],
            "current_seq": 0,
            "following_seq": 1,
        },
        {
            "run": negative["runs"][0]["run"],
            "current_seq": 1,
            "following_seq": 2,
        },
    ]
    assert negative["runs"][0]["terminal_pair_count"] == 1
    assert negative["runs"][0]["pairs"][2]["contains_terminal_event"] is True
    assert negative["cross_tab"] == [
        {
            "recomputed_success": False,
            "next_gradient_positive": False,
            "pair_count": 0,
        },
        {
            "recomputed_success": False,
            "next_gradient_positive": True,
            "pair_count": 1,
        },
        {
            "recomputed_success": True,
            "next_gradient_positive": False,
            "pair_count": 1,
        },
        {
            "recomputed_success": True,
            "next_gradient_positive": True,
            "pair_count": 1,
        },
    ]


def test_time_triggered_cell_count_uses_count_window_only(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    positive = _analyze(inputs)["trace_inventory"]
    assert positive["file_count"] == 1
    assert positive["trace_run_count"] == 1
    assert positive["cell_count"] == 1
    assert positive["time_triggered_cell_count"] == 0

    changed = _trace_document()
    changed["trace_runs"][0]["count_window"] = 0
    inputs[1].write_text(json.dumps(changed) + "\n", encoding="utf-8")
    negative = _analyze(inputs)
    assert negative["trace_inventory"]["cell_count"] == 1
    assert negative["trace_inventory"]["time_triggered_cell_count"] == 1
    assert negative["window_count_dispersion"]["not_adjudicated_reason"] == (
        "The accepted trace inventory can mix count-triggered and time-triggered "
        "cells, while both window_us and Backoff_ may vary within a run; the "
        "recorded window-count dispersion is therefore descriptive and does not "
        "adjudicate a Poisson mechanism."
    )


def test_j0_shape_control_passes_and_each_registered_check_fails_independently(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    document = _new_trace_document()
    positive = _analyze_new(inputs, _write_new_trace(tmp_path, document))["J0"]
    assert positive["passed"] is True
    assert positive["verdict"] == "passed"
    assert positive["common_factor"] == pytest.approx(1.1)
    assert positive["cliff_ratio_step0.5_over_step1"] == pytest.approx(1.6)
    assert positive["recovery_ratio_step100_over_step25"] == pytest.approx(1.1)
    assert all(
        residual == pytest.approx(0.0)
        for residual in positive["normalized_residuals"].values()
    )

    mutations = (
        (
            "nm-step1",
            118.2,
            "a_step0.5_to_step1_cliff_at_least_1.5",
        ),
        (
            "nm-step100",
            114.0,
            "b_step25_to_step100_recovery_at_least_1.05",
        ),
        (
            "nm-step2",
            140.0,
            "c_all_normalized_residuals_within_0.25",
        ),
    )
    for cell, value, failed_check in mutations:
        changed = copy.deepcopy(document)
        _new_run(changed, cell)["median_tps"] = value
        negative = _analyze_new(inputs, _write_new_trace(tmp_path, changed))["J0"]
        assert negative["passed"] is False
        assert negative["verdict"] == "observer_control_failed"
        assert negative["checks"][failed_check] is False
        assert sum(not passed for passed in negative["checks"].values()) == 1


def test_j1_uses_previous_unordered_edge_fixed_common_weights_and_three_segments(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    result = _analyze_new(inputs, _write_new_trace(tmp_path))["J1"]
    assert result["verdict"] == "supported"
    assert result["estimator_specified_after_data"] is True
    assert result["overall"]["common_edge_count"] == 10
    assert result["overall"]["fixed_weight_sum"] == 204
    assert result["overall"][
        "difference_update10_minus_update2560"
    ] == pytest.approx(48 / 204)
    assert result["direction_stable_across_all_three_segments"] is True
    assert all(segment["update10_higher"] for segment in result["segments"])
    assert result["terminal_slice_association_only"] is True

    edges = result["overall"]["edges"]
    independently_weighted_10 = sum(
        row["update10"]["count"] * row["update10"]["sign_disagreement"]
        for row in edges
    ) / sum(row["update10"]["count"] for row in edges)
    independently_weighted_2560 = sum(
        row["update2560"]["count"]
        * row["update2560"]["sign_disagreement"]
        for row in edges
    ) / sum(row["update2560"]["count"] for row in edges)
    assert independently_weighted_10 - independently_weighted_2560 < 0
    assert result["overall"]["difference_update10_minus_update2560"] > 0.10

    changed = _new_trace_document()
    _new_run(changed, "nm-step1")["trace_events"][1]["gradient_sign"] = 2
    with pytest.raises(ValueError, match="gradient_sign must be -1, 0, or 1"):
        _analyze_new(inputs, _write_new_trace(tmp_path, changed))


def test_j1_assigns_sign_to_previous_unordered_edge_and_excludes_zero() -> None:
    events = _simple_new_events(count=3)
    events[0]["backoff_before"] = 2.0
    events[0]["backoff_after"] = 1.0
    events[1]["backoff_before"] = 4.0
    events[1]["backoff_after"] = 3.0
    events[1]["gradient_sign"] = 1
    events[2]["gradient_sign"] = 0
    assert analysis._edge_observations(events) == [
        {"edge": (1.0, 2.0), "positive": True, "segment": 1}
    ]


def test_j1_reports_insufficient_common_support(
    tmp_path: Path,
) -> None:
    changed = _new_trace_document()
    wide = _new_run(changed, "nm-step1-u2560")
    for event in wide["trace_events"]:
        if event["backoff_before"] >= 10:
            event["backoff_before"] += 100
            event["backoff_after"] += 100
    result = _analyze_new(
        _write_inputs(tmp_path), _write_new_trace(tmp_path, changed)
    )["J1"]
    assert result["verdict"] == "insufficient_common_support"
    assert result["overall"]["common_edge_count"] == 5


def test_j1_one_gradient_field_can_make_segment_direction_unstable(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    document = _new_trace_document()
    narrow = _new_run(document, "nm-step1")
    wide = _new_run(document, "nm-step1-u2560")
    narrow["trace_events"] = _direction_sensitive_edge_events(narrow=True)
    wide["trace_events"] = _direction_sensitive_edge_events(narrow=False)
    for run in (narrow, wide):
        run["trace_summary"]["updates"] = len(run["trace_events"])
        run["trace_summary"]["retained"] = len(run["trace_events"])
        run["trace_summary"]["dropped"] = 0
    positive = _analyze_new(inputs, _write_new_trace(tmp_path, document))["J1"]
    assert positive["verdict"] == "supported"
    assert positive["direction_stable_across_all_three_segments"] is True

    changed = copy.deepcopy(document)
    _new_run(changed, "nm-step1")["trace_events"][41]["gradient_sign"] = 1
    negative = _analyze_new(inputs, _write_new_trace(tmp_path, changed))["J1"]
    assert negative["verdict"] == "not_supported"
    assert negative["direction_stable_across_all_three_segments"] is False
    assert negative["segments"][2]["update10_higher"] is False
    assert "direction_unstable" in negative["qualifiers"]


def test_j2_reports_both_weightings_quantiles_and_one_field_weight_sensitivity(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    document = _new_trace_document()
    positive = _analyze_new(inputs, _write_new_trace(tmp_path, document))["J2"]
    assert positive["verdict"] == "supported"
    assert positive["same_direction_for_both_weightings"] is True
    assert positive["qualifiers"] == []
    assert positive["terminal_slice_association_only"] is True
    valley = next(row for row in positive["cells"] if row["cell"] == "nm-step25")
    assert valley["probabilities"]["above_50"]["event_weighted"] == pytest.approx(
        31 / 61
    )
    assert valley["backoff_before_quantiles"] == {
        "p50": 200.0,
        "p90": 200.0,
        "p99": 200.0,
        "max": 200.0,
    }

    changed = copy.deepcopy(document)
    _new_run(changed, "nm-step0.5")["trace_events"][0]["window_us"] = 100_000
    negative = _analyze_new(inputs, _write_new_trace(tmp_path, changed))["J2"]
    assert negative["verdict"] == "not_supported"
    assert negative["same_direction_for_both_weightings"] is False
    assert negative["qualifiers"] == ["weight_sensitive"]
    assert negative["valley_vs_best"]["time_weighted"]["above_100"][
        "valley_higher"
    ] is False
    assert negative["valley_vs_best"]["event_weighted"]["above_100"][
        "valley_higher"
    ] is True


def test_j3_is_descriptive_without_verdict_and_rejects_one_bad_commit_field(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    document = _new_trace_document()
    positive = _analyze_new(inputs, _write_new_trace(tmp_path, document))["J3"]
    assert positive["descriptive_only"] is True
    assert positive["walking_model_fano_values"] == [2.0, 4.0]
    assert "verdict" not in positive
    assert len(positive["cells"]) == 6
    assert positive["cells"][0]["trigger_counts"] == {
        "time": len(_new_run(document, "nm-step0.5")["trace_events"])
    }
    assert positive["cells"][0]["window_us"]["median"] == 100
    assert positive["cells"][0]["window_us"]["mean"] == 100

    changed = copy.deepcopy(document)
    _new_run(changed, "nm-step2")["trace_events"][0]["window_commits"] = "10"
    with pytest.raises(ValueError, match="window_commits must be an exact integer"):
        _analyze_new(inputs, _write_new_trace(tmp_path, changed))


def test_j4_uses_all_run_updates_and_marks_incomplete_coverage(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    document = _new_trace_document()
    positive = _analyze_new(inputs, _write_new_trace(tmp_path, document))["J4"]
    assert positive["all_run_quantity"] is True
    assert "verdict" not in positive
    best = next(row for row in positive["cells"] if row["cell"] == "nm-step0.5")
    assert best["updates"] == 62
    assert best["retained"] == 61
    assert best["dropped"] == 1
    assert best["effective_update_us"] == pytest.approx(1_000_000 / 62)
    assert best["effective_to_nominal_ratio"] == pytest.approx(100_000 / 62)
    assert best["retained_coverage"] == pytest.approx(6_100 / 1_000_000)
    assert best["terminal_slice_only"] is True

    changed = copy.deepcopy(document)
    _new_run(changed, "nm-step2")["trace_summary"]["updates"] += 1
    with pytest.raises(
        ValueError, match=r"retained \+ dropped must equal updates"
    ):
        _analyze_new(inputs, _write_new_trace(tmp_path, changed))


def test_mechanism_mixture_interpolates_and_flattens_unmeasured_endpoint(
    tmp_path: Path,
) -> None:
    inputs = _write_inputs(tmp_path)
    document = _new_trace_document()
    positive = _analyze_new(inputs, _write_new_trace(tmp_path, document))[
        "mechanism_mixture"
    ]
    assert positive["mixture_assumption_required"] is True
    assert positive["descriptive_only"] is True
    assert "verdict" not in positive
    assert all(row["unmeasured_time_fraction"] == 0 for row in positive["cells"])

    changed = copy.deepcopy(document)
    _new_run(changed, "nm-step25")["trace_events"][0]["backoff_before"] = 1_200.0
    negative = _analyze_new(inputs, _write_new_trace(tmp_path, changed))[
        "mechanism_mixture"
    ]
    valley = next(row for row in negative["cells"] if row["cell"] == "nm-step25")
    assert valley["unmeasured_time_fraction"] == pytest.approx(1 / 61)
    assert negative["measured_curve"][-1] == {
        "backoff_us": 999.0,
        "throughput_tps": 990.0,
    }


def test_cli_output_is_create_only(tmp_path: Path) -> None:
    inputs = _write_inputs(tmp_path)
    trace_dir, _trace_path, stock, static = inputs
    output = tmp_path / "analysis.json"
    argv = [
        "--trace-dir",
        str(trace_dir),
        "--stock-readme",
        str(stock),
        "--static-tail-readme",
        str(static),
        "--output",
        str(output),
    ]
    assert analysis.main(argv) == 0
    positive_bytes = output.read_bytes()
    written = json.loads(positive_bytes)
    assert written["schema_version"] == analysis.SCHEMA_VERSION
    assert "new_trace_analysis" not in written
    explicit_none = analysis.analyze_nonmonotonicity(
        trace_dir,
        stock,
        static,
        new_trace_json=None,
        baseline_tps=None,
        static_low_b=None,
    )
    assert explicit_none == written

    changed_argv = copy.copy(argv)
    with pytest.raises(FileExistsError):
        analysis.main(changed_argv)
    assert output.read_bytes() == positive_bytes


def test_cli_accepts_new_trace_baseline_json_and_static_low_b_assignments(
    tmp_path: Path,
) -> None:
    trace_dir, _trace_path, stock, static = _write_inputs(tmp_path)
    new_trace = _write_new_trace(tmp_path)
    output = tmp_path / "new-analysis.json"
    argv = [
        "--trace-dir",
        str(trace_dir),
        "--stock-readme",
        str(stock),
        "--static-tail-readme",
        str(static),
        "--new-trace-json",
        str(new_trace),
        "--baseline-tps",
        json.dumps(_baseline_tps()),
        "--static-low-b",
        "0=1000",
        "--static-low-b",
        "100=500",
        "--output",
        str(output),
    ]
    assert analysis.main(argv) == 0
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["certified"] is False
    assert written["headline_eligible"] is False
    assert written["throughput_scope"] == "diagnostic_only"
    assert written["new_trace_analysis"]["J0"]["passed"] is True


def _run() -> int:
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
