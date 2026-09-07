from __future__ import annotations

import copy
import hashlib
import json
import math
import statistics
from pathlib import Path

import pytest

from orchestrator.campaign import backoff_counterfactual_analysis as analysis


ROOT = Path(__file__).resolve().parents[2]
PREREGISTRATION = ROOT / "docs" / "backoff-counterfactual-preregistration.md"
SEEDS = sorted(analysis.PREREGISTERED_SEEDS)


def _events(effect: float, outcomes: int = 24) -> list[dict]:
    commits = [10**12]
    for index in range(outcomes):
        outcome = effect / 2 if index % 2 == 0 else -effect / 2
        commits.append(round(commits[-1] * math.exp(outcome)))
    events = []
    for index, value in enumerate(commits):
        events.append(
            {
                "seq": index,
                "tsc": 1000 + index,
                "window_us": 1,
                "window_commits": value,
                "assigned_invert": index % 2,
                "recommended_delta_sign": (-1, 0, 1)[index % 3],
                "both_actions_feasible": (index // 2) % 2,
                "inversion_realized": 0,
                "backoff_before": 0,
                "backoff_after": 0,
            }
        )
    return events


def _row(
    policy: int,
    workload: str,
    threads: int,
    seed: int,
    preregistration_sha256: str,
    events: list[dict],
) -> dict:
    default_seed = 11_400_714_819_323_198_485
    build_seed = seed if policy == 2 else default_seed
    binary_key = f"policy-{policy}-seed-{seed if policy == 2 else 'fixed'}"
    genome_flags = {
        "BACK_OFF": 1,
        "BACKOFF_INCR_MILLI": 1000,
        "BACKOFF_MAX_US": 1000,
        "BACKOFF_UPDATE_US": 2560,
        "BACKOFF_COUNT_WINDOW": 10000,
        "BACKOFF_COUNT_CAP_US": 10240,
        "BACKOFF_STEP_ADAPT": 1,
        "BACKOFF_STEP_MIN_MILLI": 1000,
        "BACKOFF_STEP_MAX_MILLI": 4000,
        "BACKOFF_DYN_CEILING": 1,
        "BACKOFF_TRACE": 1,
        "BACKOFF_STEP_POLICY": policy,
        "BACKOFF_STEP_POLICY_SEED": build_seed,
    }
    row = {
        **analysis._expected_cell_identity(policy),
        "workload": workload,
        "workload_flags": analysis.WORKLOAD_FLAGS[workload],
        "threads": threads,
        "rep_index": 0,
        "backoff_trace": True,
        "throughput_scope": "diagnostic_only",
        "counterfactual_preregistration": preregistration_sha256,
        "binary_sha256": hashlib.sha256(binary_key.encode()).hexdigest(),
        "genome": "silo|" + ",".join(
            f"{name}={value}" for name, value in sorted(genome_flags.items())
        ),
        "trace_events": copy.deepcopy(events),
        "trace_summary": {
            "updates": len(events),
            "retained": len(events),
            "dropped": 0,
        },
    }
    if policy == 2:
        row["step_policy_seed"] = seed
    return row


def _write_artifacts(
    directory: Path,
    *,
    effects: list[float] | None = None,
    outcome_counts: list[int] | None = None,
) -> list[Path]:
    directory.mkdir()
    preregistration_sha256 = hashlib.sha256(PREREGISTRATION.read_bytes()).hexdigest()
    effects = effects or [0.005 + index * 0.0002 for index in range(12)]
    outcome_counts = outcome_counts or [24] * 12
    paths = []
    for slot, (seed, effect, count) in enumerate(
        zip(SEEDS, effects, outcome_counts, strict=True)
    ):
        rows = []
        for policy in range(3):
            for workload in analysis.WORKLOADS:
                for threads in analysis.THREADS:
                    rows.append(
                        _row(
                            policy,
                            workload,
                            threads,
                            seed,
                            preregistration_sha256,
                            _events(effect, count),
                        )
                    )
        document = {
            "schema_version": analysis.TRACE_SCHEMA_VERSION,
            "kind": "diagnostic-backoff-trace",
            "headline_eligible": False,
            "throughput_scope": "diagnostic_only",
            "grid_spec": analysis.COUNTERFACTUAL_CELLS,
            "cell_order": list(analysis.CELL_LABELS),
            "rep_index": 0,
            "records": 1_000_000,
            "extime_s": 3,
            "reps_per_job": 1,
            "counterfactual_preregistration": preregistration_sha256,
            "step_policy_seed": seed,
            "trace_runs": rows,
        }
        path = directory / f"slot-{slot:02d}.json"
        path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def _rewrite(path: Path, mutate) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")


def _primary_row(document: dict) -> dict:
    return next(
        row
        for row in document["trace_runs"]
        if row["step_policy"] == 2
        and row["workload"] == "write-heavy"
        and row["threads"] == 48
    )


def test_public_analysis_pairs_next_window_and_uses_equal_run_clusters(
    tmp_path: Path,
) -> None:
    effects = [0.016] + [0.004 + index * 0.0002 for index in range(11)]
    paths = _write_artifacts(
        tmp_path / "artifacts",
        effects=effects,
        outcome_counts=[48] + [24] * 11,
    )
    result = analysis.analyze_counterfactual(paths, PREREGISTRATION)
    primary = result["primary"]
    estimates = [row["estimate_log"] for row in primary["run_estimates"]]

    assert estimates == pytest.approx(effects, abs=1e-10)
    assert primary["theta_log"] == pytest.approx(statistics.fmean(estimates))
    assert primary["theta_log"] > 0
    event_weighted = sum(
        estimate * count for estimate, count in zip(estimates, [48] + [24] * 11)
    ) / sum([48] + [24] * 11)
    assert primary["theta_log"] != pytest.approx(event_weighted)
    assert primary["cluster_sd"] == pytest.approx(statistics.stdev(estimates))
    assert primary["ci90"]["critical_value"] == analysis.T90_DF11
    assert primary["ci95"]["critical_value"] == analysis.T95_DF11
    assert primary["ci90"]["half_width_log"] == pytest.approx(
        analysis.T90_DF11 * primary["cluster_sd"] / math.sqrt(12)
    )
    assert primary["ci95"]["half_width_log"] == pytest.approx(
        analysis.T95_DF11 * primary["cluster_sd"] / math.sqrt(12)
    )
    assert primary["decision"] == "equivalent"
    assert len(result["inputs"]) == 12
    assert all(len(item["sha256"]) == 64 for item in result["inputs"])
    assert len(result["secondary"]["workload_threads"]) == 5
    assert len(result["secondary"]["recommended_delta_sign"]) == 3
    assert len(result["secondary"]["both_actions_feasible"]) == 2
    assert len(result["secondary"]["time_block"]) == 4
    assert "median_tps" not in json.dumps(result)
    assert result == analysis.analyze_counterfactual(list(reversed(paths)), PREREGISTRATION)


def test_only_final_assignment_is_dropped_and_post_treatment_fields_do_not_filter(
    tmp_path: Path,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    baseline = analysis.analyze_counterfactual(paths, PREREGISTRATION)["primary"]
    seed = json.loads(paths[0].read_text())["step_policy_seed"]

    def final_assignment_only(document: dict) -> None:
        events = _primary_row(document)["trace_events"]
        events[-1]["assigned_invert"] = 1 - events[-1]["assigned_invert"]

    _rewrite(paths[0], final_assignment_only)
    changed_final = analysis.analyze_counterfactual(paths, PREREGISTRATION)["primary"]
    before = next(row for row in baseline["run_estimates"] if row["run_identity"][1] == seed)
    after = next(row for row in changed_final["run_estimates"] if row["run_identity"][1] == seed)
    assert after == before

    def extreme_included(document: dict) -> None:
        events = _primary_row(document)["trace_events"]
        events[0].update(
            recommended_delta_sign=0,
            both_actions_feasible=0,
            inversion_realized=0,
            backoff_before=0,
            backoff_after=0,
        )
        events[1]["window_commits"] = 10**15

    _rewrite(paths[0], extreme_included)
    included = analysis.analyze_counterfactual(paths, PREREGISTRATION)["primary"]
    extreme = next(row for row in included["run_estimates"] if row["run_identity"][1] == seed)
    assert extreme["assigned_forward"] == 12
    assert extreme["assigned_invert"] == 12
    assert abs(extreme["estimate_log"] - before["estimate_log"]) > 1


def test_binding_seed_and_input_count_fail_closed_or_become_inconclusive(
    tmp_path: Path,
) -> None:
    paths = _write_artifacts(tmp_path / "artifacts")
    incomplete = analysis.analyze_counterfactual(paths[:-1], PREREGISTRATION)
    assert incomplete["primary"]["decision"] == "inconclusive"
    assert "requires_exactly_12_clusters" in incomplete["primary"]["reasons"]

    def duplicate_seed(document: dict) -> None:
        replacement = json.loads(paths[0].read_text())
        seed = replacement["step_policy_seed"]
        document["step_policy_seed"] = seed
        for row in document["trace_runs"]:
            if row["step_policy"] == 2:
                source = next(
                    item
                    for item in replacement["trace_runs"]
                    if item["step_policy"] == 2
                    and item["workload"] == row["workload"]
                    and item["threads"] == row["threads"]
                )
                row["step_policy_seed"] = seed
                row["genome"] = source["genome"]
                row["binary_sha256"] = source["binary_sha256"]

    _rewrite(paths[1], duplicate_seed)
    with pytest.raises(ValueError, match="must be unique"):
        analysis.analyze_counterfactual(paths, PREREGISTRATION)

    fresh = _write_artifacts(tmp_path / "sha-artifacts")
    _rewrite(
        fresh[0],
        lambda document: _primary_row(document).__setitem__(
            "counterfactual_preregistration", "0" * 64
        ),
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        analysis.analyze_counterfactual(fresh, PREREGISTRATION)


def test_missing_arm_and_zero_commit_make_whole_primary_inconclusive(
    tmp_path: Path,
) -> None:
    missing_paths = _write_artifacts(tmp_path / "missing")

    def remove_arm(document: dict) -> None:
        events = _primary_row(document)["trace_events"]
        for event in events[:-1]:
            event["assigned_invert"] = 0

    for path in missing_paths:
        _rewrite(path, remove_arm)
    missing_result = analysis.analyze_counterfactual(
        missing_paths, PREREGISTRATION
    )
    missing = missing_result["primary"]
    assert missing["decision"] == "inconclusive"
    assert missing["theta_log"] is None
    assert "missing_assignment_arm" in missing["reasons"]
    assert len(missing["run_estimates"]) == 12
    sign_layer = missing_result["secondary"]["recommended_delta_sign"][0]
    assert sign_layer["estimate_log"] is None
    assert "missing_assignment_arm" in sign_layer["reason"]

    zero_paths = _write_artifacts(tmp_path / "zero")
    _rewrite(
        zero_paths[0],
        lambda document: _primary_row(document)["trace_events"][3].__setitem__(
            "window_commits", 0
        ),
    )
    zero = analysis.analyze_counterfactual(zero_paths, PREREGISTRATION)["primary"]
    assert zero["decision"] == "inconclusive"
    assert zero["theta_log"] is None
    assert "window_commits_zero" in zero["reasons"]
    assert len(zero["run_estimates"]) == 12


def test_tost_and_practical_superiority_boundaries_are_strict() -> None:
    margin = analysis.EQUIVALENCE_MARGIN
    inside = analysis._primary_decision(
        {"lower_log": -margin + 1e-12, "upper_log": margin - 1e-12},
        {"lower_log": -0.01, "upper_log": 0.01},
    )
    assert inside["tost_equivalent"] is True
    at_tost_boundary = analysis._primary_decision(
        {"lower_log": -margin, "upper_log": margin - 1e-12},
        {"lower_log": -0.01, "upper_log": 0.01},
    )
    assert at_tost_boundary["decision"] == "inconclusive"
    at_superiority_boundary = analysis._primary_decision(
        {"lower_log": -1, "upper_log": 1},
        {"lower_log": margin, "upper_log": margin + 0.01},
    )
    assert at_superiority_boundary["recommended_practical_superiority"] is False
    recommended = analysis._primary_decision(
        {"lower_log": -1, "upper_log": 1},
        {"lower_log": margin + 1e-12, "upper_log": margin + 0.01},
    )
    assert recommended["decision"] == "recommended_direction_superior"
    inverted = analysis._primary_decision(
        {"lower_log": -1, "upper_log": 1},
        {"lower_log": -margin - 0.01, "upper_log": -margin - 1e-12},
    )
    assert inverted["decision"] == "inverted_direction_superior"
