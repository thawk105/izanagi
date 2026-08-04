# -*- coding: utf-8 -*-
"""T419 probe の外部 oracle。/proc と subprocess は使用しない。"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import sys
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]
_DRIVER = _ROOT / "tools/pegasus/probes/t419_probe_causality.py"
_SPEC = importlib.util.spec_from_file_location("t419_probe_causality_under_test", _DRIVER)
assert _SPEC is not None and _SPEC.loader is not None
T419 = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = T419
_SPEC.loader.exec_module(T419)


def _verdict(name: str):
    fixture = T419.synthetic_fixture(name)
    return T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )


def _process(pid: int, starttime: int, ticks: int, cpu: int, ppid: int = 0):
    return {
        "utime": ticks,
        "stime": 0,
        "ticks": ticks,
        "starttime": starttime,
        "ppid": ppid,
        "public": {
            "pid": pid,
            "uid": 1,
            "comm": f"p{pid}",
            "state": "R",
            "processor": cpu,
            "starttime": starttime,
            "cgroup": ["0::/fixture"],
        },
    }


def _cpu(
    user: int,
    *,
    nice: int = 0,
    system: int = 0,
    idle: int = 100,
    iowait: int = 0,
    irq: int = 0,
    softirq: int = 0,
    steal: int = 0,
    guest: int = 0,
):
    return [user, nice, system, idle, iowait, irq, softirq, steal, guest, 0]


def test_preregistered_threshold_literals_are_pinned():
    assert T419.PINNED_HIT_RATE_MIN == 0.95
    assert T419.NONPINNED_OUT_OF_BAND_RATE_MAX == 0.05
    assert T419.POSITIVE_CONTRAST_CPU_MIN == 46


def test_child_threshold_literals_are_pinned():
    assert T419.BUSY_MIN_CPU_TICKS == 5
    assert T419.SHAM_MAX_CPU_TICKS == 1
    assert T419.INCONCLUSIVE_PAIR_INVALID_MIN == 3


def test_preregistered_primary_read_total_is_445():
    assert sum(T419.EXPECTED_PRIMARY_READS.values()) == 445
    assert T419.PREREGISTERED_PRIMARY_READS == 445


def test_default_hard_deadline_is_900_seconds():
    assert T419.DEFAULT_HARD_DEADLINE_SECONDS == 900.0


def test_no_effect_is_refuted():
    assert _verdict("no_effect")["causal_verdict"] == "REFUTED"


def test_all_out_of_band_is_not_confirmed():
    verdict = _verdict("all_out_of_band")
    assert (verdict["execution_validity"], verdict["causal_verdict"]) == (
        "VALID",
        "REFUTED",
    )


def test_paired_contrast_only_fixture_kills_m1():
    verdict = _verdict("paired_contrast_only")
    metrics = verdict["causal_metrics"]
    assert metrics["pinned_hit_rate"] == 0.95
    assert metrics["pinned_hit_rate_condition"] is True
    assert metrics["nonpinned_out_of_band_rate"] == 141 / 11280
    assert metrics["nonpinned_out_of_band_rate_condition"] is True
    assert metrics["positive_contrast_cpu_count"] == 45
    assert metrics["paired_contrast_condition"] is False
    assert verdict["causal_verdict"] == "REFUTED"


def test_pinned_hit_rate_boundary_0p95_is_inclusive():
    metrics = _verdict("paired_contrast_only")["causal_metrics"]
    assert metrics["pinned_hit_rate"] == 228 / 240 == 0.95
    assert metrics["pinned_hit_rate_condition"] is True


def test_nonpinned_rate_boundary_0p05_is_inclusive():
    observations, calibration, environment = T419._synthetic_base()
    cpus = environment["allocated_cpus"]
    reads = []
    remaining = 564
    for target in cpus:
        for _ in range(T419.PIN_REPEATS):
            vector = {cpu: 100.0 for cpu in cpus}
            vector[target] = 110.0
            for cpu in cpus:
                if cpu != target and remaining:
                    vector[cpu] = 110.0
                    remaining -= 1
            reads.append(T419._synthetic_read(cpus, vector, pin_target=target, reader_cpu=target))
    observations["arms"]["A1_pin_sweep"]["reads"] = reads
    metrics = T419.causal_metrics(observations, calibration["band"], cpus)
    assert remaining == 0
    assert metrics["nonpinned_out_of_band_rate"] == 564 / 11280 == 0.05
    assert metrics["nonpinned_out_of_band_rate_condition"] is True


def test_positive_contrast_boundary_46_is_inclusive():
    observations, calibration, environment = T419._synthetic_base()
    cpus = environment["allocated_cpus"]
    reads = []
    for target in cpus:
        vector = {cpu: 100.0 for cpu in cpus}
        if target >= 2:
            vector[target] = 110.0
        reads.extend(
            T419._synthetic_read(cpus, vector, pin_target=target, reader_cpu=target)
            for _ in range(T419.PIN_REPEATS)
        )
    observations["arms"]["A1_pin_sweep"]["reads"] = reads
    metrics = T419.causal_metrics(observations, calibration["band"], cpus)
    assert metrics["positive_contrast_cpu_count"] == 46
    assert metrics["paired_contrast_condition"] is True


def test_band_endpoints_are_inclusive():
    band = T419.calibration_band([100.0], 2.0)
    assert T419.canonical_pass([98.0, 102.0], band) is True


def test_band_formula_external_oracle_literals():
    band = T419.calibration_band([100.0], 2.0)
    assert band["lower_mhz"] == 98.0
    assert band["upper_mhz"] == 102.0
    assert T419.canonical_pass([97.999], band) is False
    assert T419.canonical_pass([102.001], band) is False
    assert T419.valid_band(band) is True


def test_band_must_equal_median_plus_or_minus_tolerance_formula():
    widened = {
        "expected_median_mhz": 100.0,
        "tolerance_pct": 2.0,
        "lower_mhz": 97.0,
        "upper_mhz": 103.0,
    }
    assert T419.valid_band(widened) is False


def test_even_length_median_is_arithmetic_middle():
    band = T419.calibration_band([98.0, 102.0], 0.0)
    assert band["expected_median_mhz"] == 100.0
    assert band["lower_mhz"] == band["upper_mhz"] == 100.0


def test_nonfinite_observed_values_fail_closed():
    band = T419.calibration_band([100.0], 2.0)
    assert T419.canonical_pass([math.nan], band) is False
    assert T419.canonical_pass([math.inf], band) is False


def test_nonfinite_calibration_values_are_rejected():
    with pytest.raises(ValueError):
        T419.calibration_band([math.nan], 2.0)
    with pytest.raises(ValueError):
        T419.calibration_band([100.0], math.inf)


def test_empty_vectors_fail_closed():
    band = T419.calibration_band([100.0], 2.0)
    assert T419.canonical_pass([], band) is False
    assert T419.alpha_cumulative([], band) == []
    with pytest.raises(ValueError):
        T419.calibration_band([], 2.0)


def test_in_band_non_nominal_uses_canonical_band():
    fixture = T419.synthetic_fixture("in_band_non_nominal")
    assert T419.canonical_pass(fixture["samples"], fixture["band"]) is True


def test_alpha_converges_by_positional_cumulative_minimum():
    fixture = T419.synthetic_fixture("alpha_converges")
    stages = T419.alpha_cumulative(fixture["vectors"], fixture["band"])
    assert stages[-1]["canonical_pass"] is True


def test_positive_paired_contrast_can_confirm():
    verdict = _verdict("confirmed")
    assert (verdict["execution_validity"], verdict["causal_verdict"]) == (
        "VALID",
        "CONFIRMED",
    )


@pytest.mark.parametrize(
    "fixture_name",
    [
        "missing_cpu",
        "child_evidence_missing",
        "child_status_mismatch",
        "exception_only",
        "band_missing",
        "parser_unavailable",
        "population_missing",
    ],
)
def test_invalid_fixtures_are_not_evaluated(fixture_name):
    verdict = _verdict(fixture_name)
    assert (verdict["execution_validity"], verdict["causal_verdict"]) == (
        "INVALID",
        "NOT_EVALUATED",
    )


def test_missing_reads_is_invalid_and_not_evaluated():
    verdict = _verdict("missing_reads")
    assert (verdict["execution_validity"], verdict["causal_verdict"]) == (
        "INVALID",
        "NOT_EVALUATED",
    )


def test_a4_primary_count_gate_has_a_single_reason_fixture():
    fixture = T419.synthetic_fixture("primary_count_only")
    reasons = T419.execution_validity_reasons(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert reasons == ["A4_migration_description:primary_read_count:29!=30"]


def test_execution_validity_is_total_for_non_string_condition_mode():
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A2_coresident"]["pairs"][0]["conditions"][0][
        "mode"
    ] = None
    assert T419.execution_validity_reasons(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    ) == ["A2_coresident:condition_mode_invalid"]


def test_execution_validity_rejects_nonfinite_mhz_with_one_reason():
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A4_migration_description"]["reads"][0][
        "mhz_by_cpu"
    ][0] = math.nan
    assert T419.execution_validity_reasons(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    ) == ["A4_migration_description:read_0:mhz_nonfinite_or_nonpositive"]


@pytest.mark.parametrize(
    "bad_field",
    ["string_cpu", "bool_cpu", "string_mhz", "bool_mhz"],
)
def test_execution_validity_rejects_coercible_vector_types_with_one_reason(bad_field):
    fixture = T419.synthetic_fixture("confirmed")
    vector = fixture["observations"]["arms"]["A4_migration_description"]["reads"][0][
        "mhz_by_cpu"
    ]
    if bad_field == "string_cpu":
        vector["0"] = vector.pop(0)
    elif bad_field == "bool_cpu":
        vector[True] = vector.pop(1)
    elif bad_field == "string_mhz":
        vector[0] = "110.0"
    else:
        vector[0] = False
    assert T419.execution_validity_reasons(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    ) == ["A4_migration_description:read_0:vector_unparseable"]


@pytest.mark.parametrize(
    "value", [None, 1, [], "bad"], ids=["none", "integer", "list", "string"]
)
def test_execution_validity_is_total_for_unexpected_top_level_types(value):
    reasons = T419.execution_validity_reasons(value, value, value)
    assert reasons == ["observations_not_mapping"]


def test_contention_invalidates_execution_and_verdict():
    verdict = _verdict("contention")
    assert (verdict["execution_validity"], verdict["causal_verdict"]) == (
        "INVALID",
        "NOT_EVALUATED",
    )


def test_a1_missing_anchor_is_invalid():
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A1_pin_sweep"]["discarded_anchors"].pop()
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_a1_pin_order_must_be_allocated_permutation():
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A1_pin_sweep"]["pin_order"][-1] = 0
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_a1_pin_order_and_flat_groups_match_seed_permutation():
    fixture = T419.synthetic_fixture("confirmed")
    arm = fixture["observations"]["arms"]["A1_pin_sweep"]
    expected = list(fixture["environment"]["allocated_cpus"])
    rng = random.Random(419)
    rng.shuffle(expected)
    assert arm["pin_order"] == expected
    assert [reading["pin_target"] for reading in arm["reads"]] == [
        cpu for cpu in expected for _ in range(5)
    ]
    assert _verdict("confirmed")["execution_validity"] == "VALID"


def test_a1_sorted_order_is_rejected_even_when_it_is_a_permutation():
    fixture = T419.synthetic_fixture("confirmed")
    arm = fixture["observations"]["arms"]["A1_pin_sweep"]
    arm["pin_order"] = sorted(arm["pin_order"])
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert "A1_pin_sweep:pin_order_seed_mismatch" in verdict["validity_reasons"]


def test_a3_flat_reads_must_equal_nested_blocks():
    fixture = T419.synthetic_fixture("confirmed")
    arm = fixture["observations"]["arms"]["A3_alpha_quiet"]
    changed = dict(arm["blocks"][0]["reads"][0])
    changed["started_monotonic_ns"] = 99
    arm["blocks"][0]["reads"][0] = changed
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_a2_flat_reads_must_equal_nested_conditions():
    fixture = T419.synthetic_fixture("confirmed")
    arm = fixture["observations"]["arms"]["A2_coresident"]
    changed = dict(arm["pairs"][0]["conditions"][0]["reads"][0])
    changed["started_monotonic_ns"] = 99
    arm["pairs"][0]["conditions"][0]["reads"][0] = changed
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_a3_block_population_must_be_complete():
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A3_alpha_contention"]["blocks"].pop()
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_quiet_block_anchor_is_required():
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A0_quiet_baseline"]["discarded_anchors"].pop()
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_a2_condition_cooldown_is_required():
    fixture = T419.synthetic_fixture("confirmed")
    del fixture["observations"]["arms"]["A2_coresident"]["pairs"][0][
        "conditions"
    ][0]["cooldown_after"]
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_child_tick_delta_must_match_start_end_arithmetic():
    evidence = T419._synthetic_child("busy", 2, 100)
    evidence["cpu_ticks_delta"] += 1
    assert T419.intervention_evidence_reasons("busy", 2, evidence) == [
        "cpu_tick_delta_arithmetic_mismatch"
    ]


def test_child_pid_starttime_identity_must_remain_stable():
    evidence = T419._synthetic_child("busy", 2, 100)
    evidence["end_starttime"] += 1
    assert T419.intervention_evidence_reasons("busy", 2, evidence) == [
        "starttime_identity_mismatch"
    ]


def test_sham_above_one_tick_is_inconclusive():
    evidence = T419._synthetic_child("sham", 2, 100)
    evidence["end_utime"] += 2
    evidence["cpu_ticks_delta"] = 2
    assert T419.intervention_evidence_reasons("sham", 2, evidence) == [
        "sham_cpu_tick_delta_above_threshold"
    ]
    assert T419.intervention_status("sham", 2, evidence) == "INCONCLUSIVE"


def test_sham_one_tick_inclusive_boundary_is_valid():
    evidence = T419._synthetic_child("sham", 2, 100)
    evidence["end_utime"] = evidence["start_utime"] + 1
    evidence["cpu_ticks_delta"] = 1
    assert T419.intervention_evidence_reasons("sham", 2, evidence) == []
    assert T419.intervention_status("sham", 2, evidence) == "VALID"


def test_busy_five_tick_inclusive_boundary_is_valid():
    evidence = T419._synthetic_child("busy", 2, 100)
    assert evidence["cpu_ticks_delta"] == 5
    assert T419.intervention_evidence_reasons("busy", 2, evidence) == []


def test_busy_four_ticks_is_inconclusive():
    evidence = T419._synthetic_child("busy", 2, 100)
    evidence["end_utime"] = evidence["start_utime"] + 4
    evidence["cpu_ticks_delta"] = 4
    assert T419.intervention_evidence_reasons("busy", 2, evidence) == [
        "busy_cpu_tick_delta_below_threshold"
    ]
    assert T419.intervention_status("busy", 2, evidence) == "INCONCLUSIVE"


def _make_pairs_inconclusive(fixture, count):
    pairs = fixture["observations"]["arms"]["A2_coresident"]["pairs"]
    for pair in pairs[:count]:
        busy = next(item for item in pair["conditions"] if item["mode"] == "busy")
        busy["child"]["end_utime"] -= 1
        busy["child"]["cpu_ticks_delta"] -= 1
        busy["status"] = "INCONCLUSIVE"
        pair["status"] = "INCONCLUSIVE"


def test_two_inconclusive_a2_pairs_keep_arm_valid():
    fixture = T419.synthetic_fixture("confirmed")
    _make_pairs_inconclusive(fixture, 2)
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "VALID"


def test_three_inconclusive_a2_pairs_invalidate_arm():
    fixture = T419.synthetic_fixture("confirmed")
    _make_pairs_inconclusive(fixture, 3)
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert "A2_coresident:inconclusive_pair_count:3>=3" in verdict["validity_reasons"]


def test_a3_contention_anchor_must_follow_busy_child_barrier():
    fixture = T419.synthetic_fixture("confirmed")
    arm = fixture["observations"]["arms"]["A3_alpha_contention"]
    arm["child"]["barrier_monotonic_ns"] = 2
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


def test_parser_crosscheck_requires_three_matching_files():
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["parser_crosscheck"]["files"].pop()
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


@pytest.mark.parametrize("status", ["unavailable", "error", "mismatch"])
def test_parser_crosscheck_nonmatch_statuses_are_invalid(status):
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["parser_crosscheck"]["status"] = status
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert verdict["execution_validity"] == "INVALID"


@pytest.mark.parametrize(
    "band",
    [
        None,
        {
            "expected_median_mhz": 100.0,
            "tolerance_pct": 2.0,
            "lower_mhz": 2.0,
            "upper_mhz": 1.0,
        },
        {
            "expected_median_mhz": math.nan,
            "tolerance_pct": 2.0,
            "lower_mhz": 98.0,
            "upper_mhz": 102.0,
        },
    ],
    ids=["none", "reversed", "nan"],
)
def test_invalid_bands_return_invalid_not_evaluated(band):
    fixture = T419.synthetic_fixture("confirmed")
    fixture["calibration"]["band"] = band
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert (verdict["execution_validity"], verdict["causal_verdict"]) == (
        "INVALID",
        "NOT_EVALUATED",
    )


def test_causal_analysis_exception_becomes_invalid(monkeypatch):
    fixture = T419.synthetic_fixture("confirmed")

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic causal failure")

    monkeypatch.setattr(T419, "causal_metrics", fail)
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert (verdict["execution_validity"], verdict["causal_verdict"]) == (
        "INVALID",
        "NOT_EVALUATED",
    )


def test_method_table_includes_a2_sham_in_should_pass_population():
    table = _verdict("confirmed")["method_table"]
    assert table["alpha"]["should_pass"]["evaluated"] == 24
    assert table["beta"]["should_pass"]["evaluated"] == 120
    assert table["gamma"]["should_pass"]["evaluated"] == 120


def test_should_pass_fixtures_are_not_overrejected():
    table = _verdict("overreject")["method_table"]
    assert all(
        table[method]["should_pass"]["false_positive_overreject_count"] == 0
        for method in ("alpha", "beta", "gamma")
    )


def test_should_reject_rows_are_not_replaced_by_constant_reject():
    table = _verdict("confirmed")["method_table"]
    assert all(
        table[method]["should_reject"]["false_negative_missed_deviation_count"] > 0
        for method in ("alpha", "beta", "gamma")
    )


def test_short_lived_competitor_is_detected_from_unattributed_ticks():
    before = {1: _process(1, 10, 5, 0)}
    after = {1: _process(1, 10, 5, 0)}
    result = T419.detect_isolation_competition(
        before, after, {0: _cpu(10)}, {0: _cpu(11)}, [0], [(1, 10)]
    )
    assert result["competition_detected"] is True
    assert result["unattributed_ticks_by_cpu"] == {0: 1}


def test_attributed_self_ticks_do_not_create_competition():
    before = {1: _process(1, 10, 5, 0)}
    after = {1: _process(1, 10, 6, 0)}
    result = T419.detect_isolation_competition(
        before, after, {0: _cpu(10)}, {0: _cpu(11)}, [0], [(1, 10)]
    )
    assert result["competition_detected"] is False


def test_released_child_pid_reuse_is_not_allowlisted():
    before = {
        1: _process(1, 10, 5, 0),
        20: _process(20, 100, 0, 0, ppid=1),
    }
    after = {
        1: _process(1, 10, 5, 0),
        20: _process(20, 200, 1, 0, ppid=999),
    }
    result = T419.detect_isolation_competition(
        before,
        after,
        {0: _cpu(10)},
        {0: _cpu(11)},
        [0],
        [(1, 10), (20, 100)],
    )
    assert result["competition_detected"] is True
    assert [item["starttime"] for item in result["competitors"]] == [200]


def test_irq_and_softirq_only_ticks_are_clean():
    result = T419.detect_isolation_competition(
        {1: _process(1, 10, 5, 0)},
        {1: _process(1, 10, 5, 0)},
        {0: _cpu(10)},
        {0: _cpu(10, irq=1, softirq=1)},
        [0],
        [(1, 10)],
    )
    assert result["isolation_attribution"] == "CLEAN"
    assert result["proc_stat_components_by_cpu"][0]["irq"] == 1
    assert result["proc_stat_components_by_cpu"][0]["softirq"] == 1


def test_unpinned_reader_migration_is_unresolved_but_valid():
    isolation = T419.detect_isolation_competition(
        {1: _process(1, 10, 5, 0)},
        {1: _process(1, 10, 6, 1)},
        {0: _cpu(10)},
        {0: _cpu(11)},
        [0],
        [(1, 10)],
    )
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A0_quiet_baseline"]["isolation"] = {
        **isolation,
        "visibility_complete": True,
    }
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert isolation["isolation_attribution"] == "ATTRIBUTION_UNRESOLVED"
    assert isolation["residual_total"] == isolation["self_unattributable_total"] == 1
    assert verdict["execution_validity"] == "VALID"
    assert T419.isolation_allows_later_arms(isolation) is True


def test_residual_above_self_unattributable_invalidates_and_stops_later_arms():
    isolation = T419.detect_isolation_competition(
        {1: _process(1, 10, 5, 0)},
        {1: _process(1, 10, 5, 0)},
        {0: _cpu(10)},
        {0: _cpu(12)},
        [0],
        [(1, 10)],
    )
    fixture = T419.synthetic_fixture("confirmed")
    fixture["observations"]["arms"]["A0_quiet_baseline"]["isolation"] = {
        **isolation,
        "visibility_complete": True,
    }
    verdict = T419.evaluate(
        fixture["observations"], fixture["calibration"], fixture["environment"]
    )
    assert isolation["residual_total"] == 2 > isolation["self_unattributable_total"]
    assert isolation["isolation_attribution"] == "COMPETITOR"
    assert verdict["execution_validity"] == "INVALID"
    assert T419.isolation_allows_later_arms(isolation) is False


def test_positive_nonself_pid_delta_is_competitor_snapshot_evidence():
    before = {
        1: _process(1, 10, 5, 0),
        2: _process(2, 20, 5, 0),
    }
    after = {
        1: _process(1, 10, 5, 0),
        2: _process(2, 20, 6, 0),
    }
    result = T419.detect_isolation_competition(
        before, after, {0: _cpu(10)}, {0: _cpu(10)}, [0], [(1, 10)]
    )
    assert result["residual_total"] == 0
    assert result["isolation_attribution"] == "COMPETITOR"
    assert [item["pid"] for item in result["competitors"]] == [2]


def test_completed_child_fork_to_reap_ticks_are_all_attributed():
    child = {
        "pid": 20,
        "starttime": 100,
        "requested_affinity": [0],
        "start_cpu_ticks": 1,
        "end_cpu_ticks": 2,
        "reap_cpu_ticks": 3,
        "cpu_ticks_delta": 1,
        "lifetime_cpu_ticks": 3,
        "end_starttime": 100,
        "reap_starttime": 100,
    }
    result = T419.detect_isolation_competition(
        {1: _process(1, 10, 5, 0)},
        {1: _process(1, 10, 5, 0)},
        {0: _cpu(10)},
        {0: _cpu(13)},
        [0],
        [(1, 10), (20, 100)],
        completed_children=[child],
    )
    assert child["start_cpu_ticks"] == 1
    assert child["reap_cpu_ticks"] - child["end_cpu_ticks"] == 1
    assert result["self_attributed_ticks_by_cpu"] == {0: 3}
    assert result["isolation_attribution"] == "CLEAN"


def test_isolation_residual_is_never_cancelled_across_cpus():
    result = T419.detect_isolation_competition(
        {1: _process(1, 10, 5, 0)},
        {1: _process(1, 10, 7, 0)},
        {0: _cpu(10), 1: _cpu(10)},
        {0: _cpu(11), 1: _cpu(11)},
        [0, 1],
        [(1, 10)],
        pinned_self_intervals=[
            {"pid": 1, "starttime": 10, "target_cpu": 0, "cpu_ticks_delta": 2}
        ],
    )
    assert result["self_attributed_ticks_by_cpu"] == {0: 2, 1: 0}
    assert result["residual_ticks_by_cpu"] == {0: 0, 1: 1}
    assert result["isolation_attribution"] == "COMPETITOR"


def test_isolation_window_order_contains_cpu_window_and_records_skew(monkeypatch):
    events = []
    timestamps = iter([10, 20, 30, 50])
    pid = os.getpid()

    def process_snapshot():
        events.append("process")
        return {pid: _process(pid, 10, 5, 0)}, []

    def cpu_snapshot(cpus):
        events.append("cpu")
        return {0: _cpu(10)}

    def monotonic_ns():
        events.append("timestamp")
        return next(timestamps)

    monkeypatch.setattr(T419, "_proc_mount_visible", lambda: (True, []))
    monkeypatch.setattr(T419, "_process_snapshot", process_snapshot)
    monkeypatch.setattr(T419, "_proc_cpu_counters", cpu_snapshot)
    monkeypatch.setattr(T419.time, "monotonic_ns", monotonic_ns)
    monkeypatch.setattr(T419.os, "sched_getaffinity", lambda ignored: {0})

    tracker = T419.IsolationTracker([0])
    tracker.start()
    result = tracker.finish()

    assert events == [
        "process", "timestamp", "cpu", "timestamp",
        "cpu", "timestamp", "process", "timestamp",
    ]
    assert result["window_boundary_timestamps"] == {
        "start_process_snapshot_monotonic_ns": 10,
        "start_cpu_counter_monotonic_ns": 20,
        "end_cpu_counter_monotonic_ns": 30,
        "end_process_snapshot_monotonic_ns": 50,
    }
    assert result["window_skew_ns"] == 30


def test_late_uses_half_read_interval_threshold():
    assert T419.lateness_record(1_000, 25_001_000, 50.0) == {
        "lateness_ns": 25_000_000,
        "late": False,
    }
    assert T419.lateness_record(1_000, 25_001_001, 50.0) == {
        "lateness_ns": 25_000_001,
        "late": True,
    }


def test_scheduler_binding_unavailable_is_recorded_not_rejected(monkeypatch):
    for key in (
        "PBS_QUEUE", "PBS_O_QUEUE", "PBS_PROJECT", "PBS_ACCOUNT",
        "PBS_O_PROJECT", "PBS_O_ACCOUNT",
    ):
        monkeypatch.delenv(key, raising=False)
    assert T419._scheduler_environment_binding("gen_S", "SFC")["status"] == "unavailable"


def test_scheduler_binding_mismatch_is_explicit(monkeypatch):
    monkeypatch.setenv("PBS_QUEUE", "other")
    monkeypatch.setenv("PBS_PROJECT", "SFC")
    assert T419._scheduler_environment_binding("gen_S", "SFC")["status"] == "mismatch"


def test_final_binding_mismatch_returns_nonzero_and_has_no_done_marker(
    tmp_path, monkeypatch
):
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    pending = {
        "environment": {"marker": {"fields": {"PBS_JOBID": "0:1.nqsv"}}},
        "execution_validity": "VALID",
        "causal_verdict": "CONFIRMED",
        "validity_reasons": [],
        "causal_metrics": {"synthetic": True},
        "provenance": {
            "submission_binding": {
                "expected_calibration_sha256": "a" * 64,
                "expected_head": "b" * 40,
                "expected_driver_sha256": "c" * 64,
                "expected_pbs_sha256": "d" * 64,
                "expected_env_attestation_sha256": "e" * 64,
            }
        },
    }
    (output_dir / ".result.pending.json").write_text(
        json.dumps(pending), encoding="utf-8"
    )
    monkeypatch.setattr(T419, "_load_calibration", lambda *args: {"path": "fixture"})
    monkeypatch.setattr(
        T419,
        "_submission_binding",
        lambda *args, **kwargs: {"attempted": True, "matched": False},
    )

    rc = T419.finalize_output(
        output_dir,
        probe_rc=0,
        wrapper_started_at_utc="2026-08-05T00:00:00Z",
        wrapper_finished_at_utc="2026-08-05T00:00:01Z",
        pbs_jobid="0:1.nqsv",
    )
    result = json.loads((output_dir / "result.json").read_text(encoding="utf-8"))
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert rc == 4
    assert (result["execution_validity"], result["causal_verdict"]) == (
        "INVALID", "NOT_EVALUATED"
    )
    assert manifest["wrapper_rc"] == 4
    assert "done-marker" not in manifest["files"]
