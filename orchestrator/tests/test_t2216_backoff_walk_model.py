# -*- coding: utf-8 -*-
"""Exact transition, event timing, frozen-rule, and figure tests for T-2216."""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import matplotlib.pyplot as plt
import pytest


REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools"
MODEL_SCRIPT = TOOLS / "t2216_backoff_walk_model.py"
PLOT_SCRIPT = TOOLS / "plotting" / "plot_t2216_backoff_walk.py"
PINNED_BACKOFF = REPO / "external" / "ccbench" / "include" / "backoff.hh"
sys.path.insert(0, str(TOOLS))

import t2216_backoff_walk_model as model  # noqa: E402


def _load_t2216_plot_module():
    spec = importlib.util.spec_from_file_location(
        "plot_t2216_backoff_walk_test_target", PLOT_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _t2216_rep(values, *, abort_rate: float, job: str) -> dict:
    return {
        "source_file": f"fixture-{job}.json",
        "pbs_jobid": job,
        "throughputs": [float(value) for value in values],
        "median_tps": -1.0,
        "abort_rate": abort_rate,
        "latency_ns": 1000.0,
    }


def _t2216_static_cell(
    workload: str, name: str, fixed: int, values, abort_rate: float,
) -> dict:
    active = name != "none"
    return {
        "reps": [
            _t2216_rep(values[:2], abort_rate=abort_rate, job=f"0:{workload}-{name}-a"),
            _t2216_rep(values[2:], abort_rate=abort_rate, job=f"0:{workload}-{name}-b"),
        ],
        "meta": {
            "cell": name,
            "threads": 48,
            "genome": (
                f"silo|BACKOFF_FIXED={fixed},BACK_OFF={1 if active else 0},WAL=0"
            ),
            "workload": workload,
            "patch": "fixture-data-not-an-instruction",
            "ccbench_head": model.SOURCE_PIN,
        },
    }


def _t2216_adaptive_cell(
    workload: str, *, step: float, update: int, ceiling: int,
    values, section: str,
) -> dict:
    return {
        "reps": [
            _t2216_rep(values, abort_rate=0.2,
                       job=f"0:{section}-{workload}-s{step:g}-u{update}-c{ceiling}"),
        ],
        "meta": {
            "cell": f"s{step:g}-u{update}-c{ceiling}",
            "step_us": float(step),
            "ceiling_us": ceiling,
            "update_us": update,
            "back_off": 1,
            "genome": "silo|BACK_OFF=1,WAL=0",
            "workload": workload,
            "patch": "fixture-data-not-an-instruction",
            "ccbench_head": model.SOURCE_PIN,
        },
    }


def _t2216_measured_document() -> dict:
    static = {}
    # The stored median is deliberately nonsense; raw throughputs are the only
    # admissible calibration and plotting samples.
    specs = (
        ("zero-loop", 0, (1_900_000, 2_000_000, 2_100_000, 2_000_000), 0.80),
        ("constant-mu2", 2, (2_900_000, 3_000_000, 3_100_000, 3_000_000), 0.60),
        ("constant-mu5", 5, (3_900_000, 4_000_000, 4_100_000, 4_000_000), 0.50),
        ("constant-mu10", 10, (3_700_000, 3_800_000, 3_900_000, 3_800_000), 0.40),
        ("constant-mu25", 25, (2_900_000, 3_000_000, 3_100_000, 3_000_000), 0.25),
        ("constant-mu50", 50, (2_400_000, 2_500_000, 2_600_000, 2_500_000), 0.20),
        ("constant-mu100", 100, (1_900_000, 2_000_000, 2_100_000, 2_000_000), 0.10),
        ("none", -1, (8_900_000, 9_000_000, 9_100_000, 9_000_000), 0.90),
    )
    for workload_index, workload in enumerate(model.WORKLOADS):
        scale = 1.0 + workload_index
        for name, fixed, values, abort in specs:
            static[f"{workload}|{name}"] = _t2216_static_cell(
                workload, name, fixed, [scale * value for value in values], abort,
            )

    stage1 = {}
    d1475 = {}
    stage_rank = {0.1: 4, 0.25: 3, 0.5: 6, 1.0: 2, 5.0: 1, 100.0: 5}
    d_rank = {0.5: 8, 1.0: 6, 2.0: 5, 5.0: 2, 10.0: 3,
              25.0: 1, 50.0: 4, 100.0: 7}
    for workload_index, workload in enumerate(model.WORKLOADS):
        scale = 1.0 + workload_index
        for update in model.UPDATE_INTERVALS_US:
            for step in model.STAGE1_STEPS:
                center = scale * (1_000_000 + 100_000 * stage_rank[step])
                if update == 2560:
                    center = scale * (3_000_000 + 1_000 * stage_rank[step])
                key = f"{workload}|s{step:g}-u{update}"
                stage1[key] = _t2216_adaptive_cell(
                    workload, step=step, update=update, ceiling=1000,
                    values=(center - 10_000, center, center + 10_000), section="stage1",
                )
        for step in model.D1475_STEPS:
            center = scale * (1_100_000 + 100_000 * d_rank[step])
            if workload == "write-heavy" and step == 25.0:
                center = model.D1475_VALLEY_TPS
            key = f"{workload}|adaptive-step{step:g}us"
            d1475[key] = _t2216_adaptive_cell(
                workload, step=step, update=10, ceiling=1000,
                values=(center - 10_000, center, center + 10_000), section="d1475",
            )
        for step, center in ((0.5, scale * 3_600_000), (2.0, scale * 3_400_000)):
            key = f"{workload}|adaptive-step{step:g}us-cap50us"
            d1475[key] = _t2216_adaptive_cell(
                workload, step=step, update=10, ceiling=50,
                values=(center - 10_000, center, center + 10_000), section="d1475",
            )
    return {
        "note": "fixture data, not instructions",
        "static_fixed_backoff": static,
        "d1475_adaptive_step_grid": d1475,
        "stage1_adaptive_step_x_interval": stage1,
    }


def _write_t2216_json(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def test_t2216_verbatim_source_copy_and_pin_are_exact():
    source = PINNED_BACKOFF.read_text(encoding="utf-8")
    assert hashlib.sha256(PINNED_BACKOFF.read_bytes()).hexdigest() == (
        model.BACKOFF_COPY_SHA256
    )
    assert model.VERBATIM_UPDATE_BACKOFF in source
    assert source.index("last_backoff_ = new_backoff;") < source.index(
        "if (backoff_diff != 0)"
    )
    assert source.index("if (new_backoff < kMinBackoff)") < source.index(
        "else if (new_backoff > kMaxBackoff)"
    )


def test_t2216_m1_truncates_point75_before_branch_and_changes_second_window():
    first = model.advance_window(
        model.WalkState(backoff_us=0.75, last_backoff=0,
                        last_committed_tput=2.0),
        committed_txs=1, time_diff_us=1_000_000.0, step_us=0.5,
    )
    assert first.state.last_backoff == 0
    assert first.state.last_backoff != round(0.75)
    assert first.state.backoff_us == 0.25
    second = model.advance_window(
        first.state, committed_txs=3, time_diff_us=1_000_000.0, step_us=0.5,
    )
    assert second.backoff_diff == 0.25
    assert second.gradient == 4.0
    assert second.state.backoff_us == 0.75


def test_t2216_m2_saved_state_is_prebranch_not_candidate_or_clamped_value():
    first = model.advance_window(
        model.WalkState(backoff_us=999.75, last_backoff=999,
                        last_committed_tput=1.0),
        committed_txs=2, time_diff_us=1_000_000.0, step_us=0.5,
    )
    assert first.state.backoff_us == 1000.0
    assert first.state.last_backoff == 999
    second = model.advance_window(
        first.state, committed_txs=5, time_diff_us=1_000_000.0, step_us=0.5,
    )
    assert second.backoff_diff == 1.0
    assert second.gradient == 1.0
    assert second.state.backoff_us == 1000.0


def test_t2216_m3_parity_uses_cumulative_uint64_not_window_diff():
    odd_cumulative = model.advance_window(
        model.WalkState(backoff_us=10.0, last_backoff=10,
                        last_committed_txs=1, last_committed_tput=2.0),
        committed_txs=3, time_diff_us=1_000_000.0, step_us=1.0,
    )
    assert odd_cumulative.committed_diff == 2
    assert odd_cumulative.gradient == 0.0
    assert odd_cumulative.branch == "parity_increase"
    assert odd_cumulative.state.backoff_us == 11.0
    even_cumulative = model.advance_window(
        model.WalkState(backoff_us=10.0, last_backoff=10,
                        last_committed_txs=1, last_committed_tput=3.0),
        committed_txs=4, time_diff_us=1_000_000.0, step_us=1.0,
    )
    assert even_cumulative.branch == "parity_decrease"
    assert even_cumulative.state.backoff_us == 9.0


def test_t2216_m4_lower_clamp_controls_exact_next_window_backoff_diff():
    first = model.advance_window(
        model.WalkState(backoff_us=0.25, last_backoff=0,
                        last_committed_tput=2.0),
        committed_txs=1, time_diff_us=1_000_000.0, step_us=0.5,
    )
    assert first.state.backoff_us == 0.0
    assert first.state.last_backoff == 0
    second = model.advance_window(
        first.state, committed_txs=2, time_diff_us=1_000_000.0, step_us=0.5,
    )
    assert second.backoff_diff == 0.0
    assert second.branch == "parity_decrease"
    assert second.state.backoff_us == 0.0


def test_t2216_m5_upper_clamp_delete_boundary_and_save_order_are_observable():
    transition = model.advance_window(
        model.WalkState(backoff_us=999.75, last_backoff=999,
                        last_committed_tput=1.0),
        committed_txs=2, time_diff_us=1_000_000.0, step_us=0.5,
        k_max_backoff=1000.0,
    )
    assert transition.state.backoff_us == 1000.0
    assert transition.state.backoff_us != 1000.25
    assert transition.state.last_backoff == 999


def test_t2216_m6_zero_gradient_at_max_decreases_but_positive_gradient_stays():
    zero = model.advance_window(
        model.WalkState(backoff_us=1000.0, last_backoff=1000,
                        last_committed_tput=3.0),
        committed_txs=3, time_diff_us=1_000_000.0, step_us=100.0,
    )
    assert zero.gradient == 0.0
    assert zero.branch == "parity_decrease"
    assert zero.state.backoff_us == 900.0
    positive = model.advance_window(
        model.WalkState(backoff_us=1000.0, last_backoff=999,
                        last_committed_tput=2.0),
        committed_txs=3, time_diff_us=1_000_000.0, step_us=100.0,
    )
    assert positive.gradient == 1.0
    assert positive.branch == "gradient_positive"
    assert positive.state.backoff_us == 1000.0


def test_t2216_uint64_subtraction_wrap_is_preserved():
    transition = model.advance_window(
        model.WalkState(last_committed_txs=(1 << 64) - 2),
        committed_txs=1, time_diff_us=1_000_000.0, step_us=1.0,
    )
    assert transition.committed_diff == 3
    assert transition.committed_tput == 3.0


def test_t2216_m7_event_time_uses_measured_leader_period_not_nominal_window():
    calibration = model.build_calibration(_t2216_measured_document(), "write-heavy")
    # T(0)=2M and a(0)=0.8, so 48*(1-a)/T = 4.8 us.  The first leader
    # attempt at or beyond 10 us is event 3, at 14.4 us.
    period = float(model.leader_period_us(calibration, 0.0))
    actual = float(model.effective_update_interval_us(calibration, 0.0, 10.0))
    assert math.isclose(period, 4.8, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(actual, 14.4, rel_tol=0.0, abs_tol=1e-12)
    fixed = float(model.effective_update_interval_us(
        calibration, 0.0, 10.0, model.NO_P4,
    ))
    assert fixed == 10.0
    transition = model.advance_window(
        model.WalkState(), committed_txs=30, time_diff_us=actual, step_us=1.0,
    )
    assert transition.time_diff_us == actual
    assert math.isclose(
        transition.committed_tput, 30 / 14.4 * 1_000_000.0,
        rel_tol=0.0, abs_tol=1e-9,
    )


def test_t2216_m8_t0_is_zero_loop_raw_mean_and_none_is_reference_only():
    document = _t2216_measured_document()
    calibration = model.build_calibration(document, "write-heavy")
    assert calibration.throughput_tps[0] == 2_000_000.0
    assert calibration.none_reference["throughput_mean_tps"] == 9_000_000.0
    assert calibration.none_reference["use"] == "normalization and reference line only"
    assert calibration.raw_cells[0]["cell"] == "zero-loop"
    assert calibration.raw_cells[0]["throughputs_tps"] == [
        1_900_000.0, 2_000_000.0, 2_100_000.0, 2_000_000.0,
    ]


def test_t2216_m9_target_only_mutation_cannot_change_predictions():
    original = _t2216_measured_document()
    mutated = json.loads(json.dumps(original))
    for section in (
        "stage1_adaptive_step_x_interval", "d1475_adaptive_step_grid",
    ):
        for cell in mutated[section].values():
            for rep in cell["reps"]:
                rep["throughputs"] = [value * 17.0 for value in rep["throughputs"]]
    original_cal = model.build_calibration(original, "write-heavy")
    mutated_cal = model.build_calibration(mutated, "write-heavy")
    assert original_cal == mutated_cal
    original_run = model.simulate_condition(
        original_cal, model.EXACT, step_us=0.5, update_us=10,
        repetitions=3, duration_us=100.0,
    )
    mutated_run = model.simulate_condition(
        mutated_cal, model.EXACT, step_us=0.5, update_us=10,
        repetitions=3, duration_us=100.0,
    )
    assert original_run == mutated_run
    assert json.dumps(original_run, sort_keys=True, separators=(",", ":")) == (
        json.dumps(mutated_run, sort_keys=True, separators=(",", ":"))
    )
    assert tuple(inspect.signature(model.predict_all).parameters) == (
        "calibrations", "repetitions", "duration_us",
    )


def test_t2216_vector_repetition_transition_matches_real_scalar_entity():
    import numpy as np

    scalar = model.advance_window(
        model.WalkState(backoff_us=10.75, last_backoff=10,
                        last_committed_txs=2, last_committed_tput=4.0,
                        committed_txs=2),
        committed_txs=5, time_diff_us=500_000.0, step_us=0.5,
    )
    vector = model._advance_vector(
        backoff=np.asarray([10.75]), last_committed=np.asarray([2], dtype=np.uint64),
        last_tput=np.asarray([4.0]), last_backoff=np.asarray([10.0]),
        committed=np.asarray([5], dtype=np.uint64),
        time_diff=np.asarray([500_000.0]), step_us=0.5,
        ceiling_us=1000.0, truncate=True,
    )
    assert vector[0][0] == scalar.state.backoff_us
    assert vector[1][0] == scalar.state.last_committed_txs
    assert vector[2][0] == scalar.state.last_committed_tput
    assert vector[3][0] == scalar.state.last_backoff
    assert vector[4][0] == scalar.gradient


def test_t2216_batched_main_path_matches_single_condition_without_count_noise():
    calibration = model.build_calibration(_t2216_measured_document(), "write-heavy")
    single = model.simulate_condition(
        calibration, model.NO_COUNT_NOISE, step_us=0.5, update_us=10,
        repetitions=2, duration_us=200.0,
    )
    batched = model.simulate_condition_batch(
        calibration, model.NO_COUNT_NOISE, ((0.5, 10, 1000.0),),
        repetitions=2, duration_us=200.0,
    )[0]
    for expected, actual in zip(
        single["repetitions"], batched["repetitions"], strict=True,
    ):
        assert actual["throughput_tps"] == expected["throughput_tps"]
        assert actual["update_count"] == expected["update_count"]
        assert actual["final_backoff_us"] == expected["final_backoff_us"]
        assert actual["gradient_sign_rates"] == expected["gradient_sign_rates"]
        assert actual["branch_rates"] == expected["branch_rates"]


def test_t2216_intermediate_outputs_name_residence_interval_sign_and_parity():
    calibration = model.build_calibration(_t2216_measured_document(), "write-heavy")
    run = model.simulate_condition(
        calibration, model.EXACT, step_us=0.5, update_us=10,
        repetitions=2, duration_us=200.0,
    )
    assert len(run["repetitions"]) == 2
    assert len(run["effective_update_interval_histogram"]["edges_us"]) == 129
    for repetition in run["repetitions"]:
        assert 0.0 <= repetition["p_backoff_gt_100"] <= 1.0
        assert set(repetition["backoff_quantiles_us"]) == {"p50", "p90", "p99"}
        assert set(repetition["effective_update_interval_quantiles_us"]) == {
            "p50", "p90", "p99",
        }
        rates = repetition["gradient_sign_rates"]
        assert math.isclose(sum(rates.values()), 1.0, abs_tol=1e-12)
        branches = repetition["branch_rates"]
        assert math.isclose(
            branches["parity_total"],
            branches["parity_decrease"] + branches["parity_increase"],
            abs_tol=1e-12,
        )


def test_t2216_counterfactual_matrix_contains_real_2x2_and_count_noise_entity():
    scenarios = {
        scenario.name: scenario
        for scenario in (
            model.EXACT, model.NO_TRUNC, model.NO_P4,
            model.NO_TRUNC_NO_P4, model.NO_COUNT_NOISE,
        )
    }
    assert set(scenarios) == {
        "M_exact", "M_no_trunc", "M_no_P4", "M_no_trunc_no_P4",
        "M_no_count_noise",
    }
    assert scenarios["M_exact"].truncate_last_backoff is True
    assert scenarios["M_exact"].event_driven is True
    assert scenarios["M_no_trunc"].truncate_last_backoff is False
    assert scenarios["M_no_trunc"].event_driven is True
    assert scenarios["M_no_P4"].truncate_last_backoff is True
    assert scenarios["M_no_P4"].event_driven is False
    assert scenarios["M_no_trunc_no_P4"].truncate_last_backoff is False
    assert scenarios["M_no_trunc_no_P4"].event_driven is False
    assert scenarios["M_no_count_noise"].count_law == "deterministic"


def test_t2216_repetition_limit_is_literal_and_rejects_33():
    calibration = model.build_calibration(_t2216_measured_document(), "write-heavy")
    assert model.REPETITIONS == 8
    assert model.MAX_REPETITIONS == 32
    with pytest.raises(model.ModelError, match=r"\[1,32\]"):
        model.simulate_condition_batch(
            calibration, model.EXACT, ((0.5, 10, 1000.0),),
            repetitions=33, duration_us=100.0,
        )


def test_t2216_only_indirect_evidence_statuses_are_reachable():
    assert model.derive_status(False, False) is None
    assert model.derive_status(True, False) == "shape_match"
    assert model.derive_status(True, True) == "mechanism_supported"
    with pytest.raises(model.ModelError, match="requires the shape gate"):
        model.derive_status(False, True)
    forbidden = "mechanism_" + "confirmed"
    assert forbidden not in MODEL_SCRIPT.read_text(encoding="utf-8")


def _stage1_rank_fixture() -> dict[float, float]:
    return {5.0: 0.0, 100.0: 1.0, 1.0: 2.0, 0.25: 3.0,
            0.1: 4.0, 0.5: 5.0}


def test_t2216_rule_a_kendall_maximum_and_minimum_are_independent_clauses():
    observed = _stage1_rank_fixture()
    passed = model.rule_a_stage1(observed, observed)
    assert passed["passed"] is True
    assert passed["kendall_distance"] == 0
    wrong_max = dict(observed)
    wrong_max[0.5], wrong_max[1.0] = wrong_max[1.0], wrong_max[0.5]
    result = model.rule_a_stage1(wrong_max, wrong_max)
    assert result["kendall_distance"] == 0
    assert result["maximum_is_0.5"] is False
    assert result["minimum_is_5_to_25"] is True
    wrong_min_observed = {
        0.5: 8.0, 1.0: 6.0, 2.0: 5.0, 5.0: 2.0,
        10.0: 3.0, 25.0: 4.0, 50.0: 1.0, 100.0: 7.0,
    }
    wrong_min = model.rule_a_d1475(wrong_min_observed, wrong_min_observed)
    assert wrong_min["kendall_distance"] == 0
    assert wrong_min["maximum_is_0.5"] is True
    assert wrong_min["minimum_is_5_to_25"] is False


def test_t2216_kendall_distance_limits_are_literal_and_dataset_local():
    observed_stage1 = _stage1_rank_fixture()
    predicted_stage1 = dict(observed_stage1)
    predicted_stage1[100.0], predicted_stage1[1.0] = (
        predicted_stage1[1.0], predicted_stage1[100.0]
    )
    predicted_stage1[0.25], predicted_stage1[0.1] = (
        predicted_stage1[0.1], predicted_stage1[0.25]
    )
    assert model.kendall_distance(observed_stage1, predicted_stage1) == 2
    assert model.rule_a_stage1(observed_stage1, predicted_stage1)["passed"] is True
    predicted_stage1 = dict(observed_stage1)
    predicted_stage1[100.0], predicted_stage1[0.25] = (
        predicted_stage1[0.25], predicted_stage1[100.0]
    )
    assert model.kendall_distance(observed_stage1, predicted_stage1) > 2
    assert model.rule_a_stage1(observed_stage1, predicted_stage1)["passed"] is False
    assert model.STAGE1_MAX_KENDALL_DISTANCE == 2
    assert model.D1475_MAX_KENDALL_DISTANCE == 3


def test_t2216_rule_b_strict_boundary_and_every_candidate_participates():
    steps = (0.1, 0.25, 0.5, 1.0, 5.0)
    below = {step: 1.0 for step in steps}
    below[0.1] = 1.4999
    assert model.rule_b(below)["passed"] is True
    equal = dict(below)
    equal[0.1] = 1.5
    assert model.rule_b(equal)["passed"] is False
    for omitted in steps:
        incomplete = dict(below)
        del incomplete[omitted]
        assert model.rule_b(incomplete)["passed"] is False


def test_t2216_rule_c_is_quantitative_valley_match_not_t100_threshold():
    boundary = model.D1475_VALLEY_TPS * (
        1.0 + model.D1475_VALLEY_RELATIVE_TOLERANCE
    )
    assert model.rule_c(boundary)["passed"] is True
    assert model.rule_c(boundary + 1.0)["passed"] is False
    assert model.rule_c(2_000_000.0)["passed"] is False


def test_t2216_h1_rule_names_real_cap50_positive_and_negative_entities():
    observed = {0.5: 1.01, 2.0: 2.06}
    positive = model.rule_h1({0.5: 1.01, 2.0: 2.06}, observed)
    negative = model.rule_h1({0.5: 1.40, 2.0: 1.10}, observed)
    assert positive["passed"] is True
    assert negative["passed"] is False
    assert positive["kind"].startswith("parameter-independent")
    assert positive["inclusive_relative_tolerance"] == 0.20


@pytest.mark.parametrize("flag", ["--tail", "--fano", "--condition-seed"])
def test_t2216_cli_has_no_tail_fano_or_condition_seed_override(flag: str):
    with pytest.raises(SystemExit):
        model._parser().parse_args(["m.json", "b.hh", "o.json", flag, "9"])


def _t2216_fake_run(
    *, scenario: str, step: float, update: int, ceiling: float = 1000.0,
) -> dict:
    base = 2_000_000.0 + 10_000.0 * math.log10(step + 1.0) + update
    thresholds = list(model.RESIDENCE_THRESHOLDS_US)
    repetitions = []
    for rep in range(3):
        survivor = [max(0.0, 1.0 - index / (len(thresholds) - 1))
                    for index in range(len(thresholds))]
        repetitions.append({
            "rep_index": rep,
            "throughput_tps": base + (rep - 1) * 10_000.0,
            "total_commits": int(base * 3),
            "p_backoff_gt_100": 0.1 + 0.01 * rep,
            "backoff_quantiles_us": {"p50": 10.0, "p90": 100.0, "p99": 500.0},
            "effective_update_interval_quantiles_us": {
                "p50": float(update), "p90": float(update + 10),
                "p99": float(update + 20),
            },
            "residence_survivor": survivor,
            "branch_rates": {
                "gradient_negative": 0.2, "gradient_positive": 0.3,
                "parity_decrease": 0.25, "parity_increase": 0.25,
                "parity_total": 0.5,
            },
            "gradient_sign_rates": {"correct": 0.6, "incorrect": 0.2, "zero": 0.2},
            "update_count": 10,
            "final_backoff_us": step,
            "final_backoff_hex": float(step).hex(),
        })
    return {
        "workload": "write-heavy",
        "scenario": scenario,
        "condition": {
            "step_us": step, "nominal_update_us": update,
            "ceiling_us": ceiling, "duration_us": 3_000_000.0,
        },
        "seed_sequence": [model.BASE_SEED, 0, 0, int(step * 1000), update, int(ceiling)],
        "repetitions": repetitions,
        "residence_thresholds_us": thresholds,
        "effective_update_interval_histogram": {"edges_us": [0.0, 10.0], "counts": [30]},
    }


def _t2216_fake_model(measured_path: Path) -> dict:
    runs = []
    union = tuple(sorted(set(model.STAGE1_STEPS) | set(model.D1475_STEPS)))
    for update in model.UPDATE_INTERVALS_US:
        steps = union if update == 10 else model.STAGE1_STEPS
        if update == 2560:
            steps = tuple(sorted(set(steps) | {25.0}))
        for step in steps:
            runs.append(_t2216_fake_run(scenario="M_exact", step=step, update=update))
    for step in (0.5, 1.0, 5.0, 25.0):
        runs.append(_t2216_fake_run(scenario="M_no_trunc", step=step, update=10))
    for scenario in ("M_flat_tail", "M_linear_zero"):
        for step in union:
            runs.append(_t2216_fake_run(scenario=scenario, step=step, update=10))
    return {
        "schema_version": model.SCHEMA,
        "not_certified": model.NOT_CERTIFIED,
        "protocol": "Silo",
        "configuration": {
            "duration_us": 3_000_000.0,
            "base_seed": model.BASE_SEED,
            "condition_order": [list(row) for row in model.prediction_conditions()],
        },
        "provenance": {
            "measured_input": {
                "path": str(measured_path.resolve()),
                "sha256": hashlib.sha256(measured_path.read_bytes()).hexdigest(),
            },
            "backoff_copy": {
                "path": str(PINNED_BACKOFF.resolve()),
                "sha256": hashlib.sha256(PINNED_BACKOFF.read_bytes()).hexdigest(),
                "source_pin": model.SOURCE_PIN,
            },
            "static_calibration_jobids": ["0:static-fixture"],
        },
        "predictions": runs,
        "evaluation": {"status": None},
    }


def _run_t2216_plot(
    tmp_path: Path, mode_name: str, model_path: Path, measured_path: Path,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    prefix = tmp_path / f"figure-{mode_name}"
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["MPLCONFIGDIR"] = str(tmp_path / "mpl-config")
    result = subprocess.run(
        [sys.executable, "-B", str(PLOT_SCRIPT), mode_name, str(prefix),
         str(model_path), str(measured_path), str(PINNED_BACKOFF)],
        cwd=REPO, env=environment, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False, timeout=60,
    )
    return result, prefix


def test_t2216_plot_ci_uses_raw_student_t_not_stored_aggregate_or_196():
    plot = _load_t2216_plot_module()
    center, half = plot.ci95([
        1_000_000.0, 2_000_000.0, 3_000_000.0, 4_000_000.0,
        5_000_000.0, 6_000_000.0, 7_000_000.0,
    ])
    assert center == 4_000_000.0
    assert math.isclose(half, 1_997_895.15837, rel_tol=0.0, abs_tol=0.01)
    assert not math.isclose(half, 1_600_333.29862, rel_tol=0.0, abs_tol=1.0)


@pytest.mark.parametrize("mode_name", ["prediction", "residence", "mechanism"])
def test_t2216_plot_modes_write_png_pdf_and_hash_bound_provenance(
    tmp_path: Path, mode_name: str,
):
    measured_path = _write_t2216_json(
        tmp_path / "measured.json", _t2216_measured_document(),
    )
    model_path = _write_t2216_json(
        tmp_path / "model.json", _t2216_fake_model(measured_path),
    )
    result, prefix = _run_t2216_plot(tmp_path, mode_name, model_path, measured_path)
    assert result.returncode == 0, result.stderr
    outputs = [Path(f"{prefix}.{suffix}") for suffix in ("png", "pdf", "provenance.json")]
    assert all(path.is_file() and path.stat().st_size > 0 for path in outputs)
    provenance = json.loads(outputs[-1].read_text(encoding="utf-8"))
    assert provenance["provenance_schema_version"].endswith("/v1")
    assert provenance["mode"] == mode_name
    assert provenance["seed"] == model.BASE_SEED
    assert provenance["pbs_jobids"]
    assert provenance["primary_values"]
    if mode_name == "prediction":
        assert {
            row["label"] for row in provenance["primary_values"]
            if row.get("dataset") == "reference"
        } == {
            "no backoff (BACK_OFF=0)", "active zero-loop T(0)",
            "static backoff 100 us",
        }
    expected_inputs = {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (model_path, measured_path, PINNED_BACKOFF)
    }
    assert {row["path"]: row["sha256"] for row in provenance["inputs"]} == expected_inputs
    assert {
        row["path"]: row["sha256"] for row in provenance["outputs"]
    } == {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in outputs[:2]
    }
    assert "NOT CERTIFIED" in provenance["caption"]


def test_t2216_layout_check_rejects_real_excessive_text_entity():
    plot = _load_t2216_plot_module()
    figure, axes = plt.subplots(1, 2, figsize=(4.0, 2.0), squeeze=False)
    try:
        figure.text(0.5, 0.5, "x" * 1000)
        with pytest.raises(plot.FigureLayoutError, match="text leaves figure"):
            plot.check_figure_layout(figure, axes)
    finally:
        plt.close(figure)


def test_t2216_plot_input_change_publishes_no_png_or_pdf(tmp_path: Path):
    plot = _load_t2216_plot_module()
    measured_path = _write_t2216_json(
        tmp_path / "measured-change.json", _t2216_measured_document(),
    )
    model_path = _write_t2216_json(
        tmp_path / "model-change.json", _t2216_fake_model(measured_path),
    )
    data = plot.load_inputs(
        "prediction", model_path, measured_path, PINNED_BACKOFF,
    )
    figure, axes, _plotted = plot.make_figure(data)
    prefix = tmp_path / "must-not-publish"
    try:
        measured_path.write_text(
            measured_path.read_text(encoding="utf-8") + " ", encoding="utf-8",
        )
        with pytest.raises(plot.FigureDataError, match="input changed"):
            plot._atomic_save_figure(
                figure, axes, prefix, data["input_records"],
            )
    finally:
        plot.plt.close(figure)
    assert not Path(f"{prefix}.png").exists()
    assert not Path(f"{prefix}.pdf").exists()


def test_t2216_dependency_backend_harness_and_unicode_contracts_are_explicit():
    model_source = MODEL_SCRIPT.read_text(encoding="utf-8")
    plot_source = PLOT_SCRIPT.read_text(encoding="utf-8")
    test_source = Path(__file__).read_text(encoding="utf-8")
    assert 'mpl.use("Agg", force=True)' in plot_source
    assert plot_source.index('mpl.use("Agg", force=True)') < plot_source.index(
        "import matplotlib.pyplot"
    )
    for source in (model_source, plot_source):
        for forbidden_dependency in ("scipy", "pandas", "seaborn"):
            assert forbidden_dependency not in source.lower()
    assert 'if __name__ == "__main__":' in test_source
    assert "pytest.main" in test_source.split("__main__", 1)[1]
    for source in (model_source, plot_source, test_source):
        assert not any("\u0300" <= character <= "\u036f" for character in source)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
