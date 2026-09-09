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

    changed_argv = copy.copy(argv)
    with pytest.raises(FileExistsError):
        analysis.main(changed_argv)
    assert output.read_bytes() == positive_bytes


def _run() -> int:
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
