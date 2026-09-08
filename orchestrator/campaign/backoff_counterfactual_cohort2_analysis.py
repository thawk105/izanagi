"""Offline analysis for adaptive-backoff counterfactual cohort 2.

この解析器は count-closed な cohort 2 の固定 12 件だけを扱う。
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from pathlib import Path
from typing import Callable

__all__ = ["analyze_counterfactual"]

ANALYSIS_VERSION = "izanagi-backoff-counterfactual-cohort2-analysis/v1"
TRACE_SCHEMA_VERSION = "izanagi-dynamic-backoff-trace/v4"
MEASUREMENT_PREREGISTRATION_SHA256 = (
    "8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9"
)
ANALYSIS_PREREGISTRATION_SHA256 = (
    "8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9"
)
CCBENCH_PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
PATCH_A_SHA256 = (
    "9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b"
)
PATCH_B_SHA256 = (
    "f3fe6b7e67931775bcef0a7831dda8c6cb53dfc7fc52a74f4508360e1fedf824"
)
PATCH_C_SHA256 = (
    "b5649becded2ad62d015d94263b3e4b3e32f8c271892647e6567772c234dad5f"
)
PATCH_STACK = (
    ("patches/cicada-adaptive-params.patch", PATCH_A_SHA256),
    ("patches/cicada-adaptive-dynamic.patch", PATCH_B_SHA256),
    ("patches/cicada-adaptive-counterfactual.patch", PATCH_C_SHA256),
)
COUNTERFACTUAL_CELLS = (
    "cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0,"
    "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1,"
    "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2"
)
CELL_LITERALS = {
    0: "cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0",
    1: "cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1",
    2: "cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2",
}
CELL_LABELS = tuple(CELL_LITERALS[policy].split(":", 1)[0] for policy in range(3))
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
THREADS = (24, 48)
WORKLOAD_FLAGS = {
    "write-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "5",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "balanced": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "50",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "read-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "95",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
}
PREREGISTERED_SEEDS = frozenset(
    {
        14_481_721_328_008_317_845,
        7_453_732_891_837_486_670,
        766_609_016_836_229_506,
        14_479_507_243_158_715_447,
        3_736_279_228_254_271_919,
        6_574_519_577_559_702_715,
        15_525_319_108_568_766_040,
        13_039_315_294_558_381_935,
        16_889_140_200_793_892_447,
        15_536_816_158_447_092_057,
        13_171_317_188_614_694_465,
        3_421_410_286_381_859_835,
    }
)
PRIMARY_WORKLOAD = "write-heavy"
PRIMARY_THREADS = 48
EQUIVALENCE_MARGIN = math.log(1.03)
T90_DF11 = 1.7958848
T95_DF11 = 2.2009852
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _fail(message: str) -> None:
    raise ValueError(message)


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_int(value: object, *, field: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail(f"{field} must be an exact integer >= {minimum}")
    return value


def _matches_exact(document: dict, expected: dict) -> bool:
    return all(
        type(document.get(key)) is type(value) and document.get(key) == value
        for key, value in expected.items()
    )


def _validate_build_bindings(document: dict, *, binding: str) -> None:
    expected = {
        "ccbench_head": CCBENCH_PIN,
        "patch_sha256": PATCH_A_SHA256,
        "dynamic_patch_sha256": PATCH_B_SHA256,
        "counterfactual_patch_sha256": PATCH_C_SHA256,
        "patch_stack": [
            {"path": path, "sha256": sha256}
            for path, sha256 in PATCH_STACK
        ],
    }
    if not _matches_exact(document, expected):
        _fail(f"{binding}: ccbench pin or ordered patch stack mismatch")


def _validate_event(event: object, index: int, *, binding: str) -> dict:
    if type(event) is not dict:
        _fail(f"{binding}: trace event {index} is not an object")
    if _exact_int(event.get("seq"), field=f"{binding}.seq") != index:
        _fail(f"{binding}: trace seq is not contiguous from zero")
    _exact_int(event.get("tsc"), field=f"{binding}.tsc")
    _exact_int(event.get("window_us"), field=f"{binding}.window_us", minimum=1)
    window_commits = _exact_int(
        event.get("window_commits"), field=f"{binding}.window_commits"
    )
    terminal_flush = event.get("terminal_flush")
    if type(terminal_flush) is not int or terminal_flush not in {0, 1}:
        _fail(f"{binding}: terminal_flush must be 0 or 1")
    trigger = event.get("trigger")
    if terminal_flush:
        expected_terminal = {
            "trigger": "terminal",
            "assigned_invert": -1,
            "recommended_delta_sign": 0,
            "inversion_realized": 0,
            "both_actions_feasible": 0,
        }
        if not _matches_exact(event, expected_terminal):
            _fail(f"{binding}: terminal event sentinel contract failed")
    else:
        if trigger != "count":
            _fail(f"{binding}: normal event trigger must be count")
        if (
            type(event.get("assigned_invert")) is not int
            or event["assigned_invert"] not in {0, 1}
        ):
            _fail(f"{binding}: assigned_invert must be 0 or 1")
        if (
            type(event.get("recommended_delta_sign")) is not int
            or event["recommended_delta_sign"] not in {-1, 0, 1}
        ):
            _fail(f"{binding}: recommended_delta_sign must be -1, 0, or 1")
        for field in ("both_actions_feasible", "inversion_realized"):
            if type(event.get(field)) is not int or event[field] not in {0, 1}:
                _fail(f"{binding}: {field} must be 0 or 1")
    if 0 < window_commits < 10_000:
        _fail(f"{binding}: count-closed event must contain at least 10000 commits")
    return event


def _validate_trace(row: dict, *, binding: str) -> list[dict]:
    events_raw = row.get("trace_events")
    summary = row.get("trace_summary")
    if type(events_raw) is not list or not events_raw:
        _fail(f"{binding}: trace_events must be a nonempty list")
    events = [
        _validate_event(event, index, binding=binding)
        for index, event in enumerate(events_raw)
    ]
    if any(
        following["tsc"] < current["tsc"]
        for current, following in zip(events, events[1:])
    ):
        _fail(f"{binding}: trace tsc must be monotonic")
    terminal_indices = [
        index for index, event in enumerate(events) if event["terminal_flush"] == 1
    ]
    # Zero terminals is the preregistered non-closure outcome.  Keep that run
    # in the cohort so _run_difference can make the whole decision inconclusive.
    if len(terminal_indices) > 1:
        _fail(f"{binding}: trace must contain at most one terminal event")
    if terminal_indices and terminal_indices[0] != len(events) - 1:
        _fail(f"{binding}: terminal event must be last")
    normal_count = len(events) - len(terminal_indices)
    if normal_count == 0:
        _fail(f"{binding}: trace must contain a normal event")
    expected_summary = {
        "updates": normal_count,
        "retained": normal_count,
        "dropped": 0,
        "flushes": len(terminal_indices),
    }
    if (
        type(summary) is not dict
        or set(summary) != set(expected_summary)
        or not _matches_exact(summary, expected_summary)
    ):
        _fail(f"{binding}: trace summary/count or dropped contract failed")
    return events


def _validate_assignment_lcg(
    events: list[dict],
    *,
    seed: int,
    binding: str,
) -> None:
    """Check the recorded policy-2 assignment stream against its fixed LCG."""
    state = seed
    for index, event in enumerate(events):
        if event["terminal_flush"] == 1:
            if event["assigned_invert"] != -1:
                _fail(f"{binding}: terminal assigned_invert must be -1")
            continue
        state = (
            state * 6_364_136_223_846_793_005
            + 1_442_695_040_888_963_407
        ) % (2**64)
        expected = (state >> 63) & 1
        if event["assigned_invert"] != expected:
            _fail(
                f"{binding}: assignment-integrity check failed at event {index}"
            )


def _expected_cell_identity(policy: int) -> dict:
    return {
        "cell": CELL_LABELS[policy],
        "back_off": 1,
        "step_us": 1.0,
        "ceiling_us": 1000,
        "update_us": 2560,
        "count_window": 10000,
        "count_cap_us": 9_223_372_036_854_775_807,
        "step_adapt": 1,
        "step_min_us": 1.0,
        "step_max_us": 4.0,
        "dyn_ceiling": 1,
        "cell_format_fields": 12,
        "step_policy": policy,
    }


def _validate_genome(genome: object, *, policy: int, seed: int, binding: str) -> str:
    if type(genome) is not str or "|" not in genome:
        _fail(f"{binding}: genome is not canonical")
    protocol, encoded_flags = genome.split("|", 1)
    if protocol != "silo":
        _fail(f"{binding}: genome protocol must be silo")
    flags = {}
    for item in encoded_flags.split(","):
        if item.count("=") != 1:
            _fail(f"{binding}: genome flag encoding is malformed")
        name, value = item.split("=", 1)
        if not name or not value or name in flags:
            _fail(f"{binding}: genome flags are empty or duplicated")
        flags[name] = value
    expected_flags = {
        "NO_WAIT_LOCKING_IN_VALIDATION": "1",
        "NO_WAIT_OF_TICTOC": "0",
        "WAL": "0",
        "BACK_OFF": "1",
        "BACKOFF_INCR_MILLI": "1000",
        "BACKOFF_MAX_US": "1000",
        "BACKOFF_UPDATE_US": "2560",
        "BACKOFF_COUNT_WINDOW": "10000",
        "BACKOFF_COUNT_CAP_US": "9223372036854775807",
        "BACKOFF_STEP_ADAPT": "1",
        "BACKOFF_STEP_MIN_MILLI": "1000",
        "BACKOFF_STEP_MAX_MILLI": "4000",
        "BACKOFF_DYN_CEILING": "1",
        "BACKOFF_TRACE": "1",
        "BACKOFF_TRACE_TERMINAL_US": "5000000",
        "BACKOFF_STEP_POLICY": str(policy),
        "BACKOFF_STEP_POLICY_SEED": str(seed),
    }
    if flags != expected_flags:
        _fail(f"{binding}: genome does not bind the exact cell, trace, and seed")
    return genome


def _validate_row(
    row: object,
    *,
    artifact_seed: int,
    binding: str,
) -> dict:
    if type(row) is not dict:
        _fail(f"{binding}: trace row is not an object")
    policy = row.get("step_policy")
    if type(policy) is not int or policy not in {0, 1, 2}:
        _fail(f"{binding}: row step_policy must be 0, 1, or 2")
    identity = _expected_cell_identity(policy)
    if not _matches_exact(row, identity):
        _fail(f"{binding}: row cell identity is not the exact preregistered literal")
    workload = row.get("workload")
    threads = row.get("threads")
    if workload not in WORKLOADS or type(threads) is not int or threads not in THREADS:
        _fail(f"{binding}: row workload/threads are outside the exact axes")
    if row.get("workload_flags") != WORKLOAD_FLAGS[workload]:
        _fail(f"{binding}: row workload flags are not exact")
    if type(row.get("rep_index")) is not int or row["rep_index"] != 0:
        _fail(f"{binding}: row rep_index must be exact integer zero")
    if row.get("backoff_trace") is not True:
        _fail(f"{binding}: row must be trace enabled")
    if row.get("throughput_scope") != "diagnostic_only":
        _fail(f"{binding}: row throughput_scope must be diagnostic_only")
    if (
        row.get("counterfactual_preregistration")
        != MEASUREMENT_PREREGISTRATION_SHA256
    ):
        _fail(f"{binding}: row preregistration SHA-256 mismatch")
    _validate_build_bindings(row, binding=binding)
    if policy == 2:
        if (
            type(row.get("step_policy_seed")) is not int
            or row["step_policy_seed"] != artifact_seed
        ):
            _fail(f"{binding}: policy 2 row seed differs from artifact seed")
    elif "step_policy_seed" in row:
        _fail(f"{binding}: policy 0/1 row must not record a variable seed")
    binary_sha256 = row.get("binary_sha256")
    if type(binary_sha256) is not str or _SHA256_RE.fullmatch(binary_sha256) is None:
        _fail(f"{binding}: binary_sha256 must be lowercase hex")
    expected_seed = artifact_seed if policy == 2 else 11_400_714_819_323_198_485
    genome = _validate_genome(
        row.get("genome"), policy=policy, seed=expected_seed, binding=binding
    )
    trace_symbol_count = _exact_int(
        row.get("backoff_trace_symbol_count"),
        field=f"{binding}.backoff_trace_symbol_count",
        minimum=1,
    )
    trace_string_count = _exact_int(
        row.get("backoff_trace_string_count"),
        field=f"{binding}.backoff_trace_string_count",
        minimum=1,
    )
    events = _validate_trace(row, binding=binding)
    if policy == 2:
        _validate_assignment_lcg(events, seed=artifact_seed, binding=binding)
    return {
        "cell_literal": CELL_LITERALS[policy],
        "step_policy": policy,
        "workload": workload,
        "threads": threads,
        "step_policy_seed": artifact_seed if policy == 2 else None,
        "binary_sha256": binary_sha256,
        "genome": genome,
        "backoff_trace_symbol_count": trace_symbol_count,
        "backoff_trace_string_count": trace_string_count,
        "events": events,
    }


def _load_artifact(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid diagnostic artifact {path}: {exc}") from exc
    if type(document) is not dict:
        _fail(f"{path}: diagnostic artifact is not an object")
    exact_top_level = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "kind": "diagnostic-backoff-trace",
        "headline_eligible": False,
        "throughput_scope": "diagnostic_only",
        "grid_spec": COUNTERFACTUAL_CELLS,
        "cell_order": list(CELL_LABELS),
        "rep_index": 0,
        "records": 1_000_000,
        "extime_s": 6,
        "reps_per_job": 1,
        "counterfactual_preregistration": MEASUREMENT_PREREGISTRATION_SHA256,
    }
    if not _matches_exact(document, exact_top_level):
        _fail(f"{path}: top-level counterfactual contract mismatch")
    _validate_build_bindings(document, binding=str(path))
    seed = document.get("step_policy_seed")
    if type(seed) is not int or seed not in PREREGISTERED_SEEDS:
        _fail(f"{path}: step_policy_seed is not one preregistered uint64 seed")
    rows_raw = document.get("trace_runs")
    if type(rows_raw) is not list or len(rows_raw) != 18:
        _fail(f"{path}: exact trace grid requires 18 rows")
    rows: dict[tuple[int, str, int], dict] = {}
    for index, raw_row in enumerate(rows_raw):
        row = _validate_row(
            raw_row,
            artifact_seed=seed,
            binding=f"{path}:trace_runs[{index}]",
        )
        key = (row["step_policy"], row["workload"], row["threads"])
        if key in rows:
            _fail(f"{path}: duplicate trace row for {key}")
        rows[key] = row
    expected_keys = {
        (policy, workload, threads)
        for policy in range(3)
        for workload in WORKLOADS
        for threads in THREADS
    }
    if set(rows) != expected_keys:
        _fail(f"{path}: trace rows do not cover the exact 3 x 3 x 2 grid")
    if len(
        {
            (
                row["backoff_trace_symbol_count"],
                row["backoff_trace_string_count"],
            )
            for row in rows.values()
        }
    ) != 1:
        _fail(f"{path}: backoff trace symbol/string counts differ across rows")
    for policy in range(3):
        policy_rows = [row for key, row in rows.items() if key[0] == policy]
        if len({row["binary_sha256"] for row in policy_rows}) != 1:
            _fail(f"{path}: policy {policy} binary identity changes within one artifact")
        if len({row["genome"] for row in policy_rows}) != 1:
            _fail(f"{path}: policy {policy} genome changes within one artifact")
    trace_counts = next(
        (
            row["backoff_trace_symbol_count"],
            row["backoff_trace_string_count"],
        )
        for row in rows.values()
    )
    return {"seed": seed, "rows": rows, "trace_counts": trace_counts}


def _run_difference(
    run: dict,
    membership: Callable[[dict, int, int], bool],
) -> dict:
    events = run["events"]
    analysis_events = events[1:]
    has_terminal = bool(
        analysis_events and analysis_events[-1].get("terminal_flush") == 1
    )
    current_events = analysis_events[:-1]
    outcome_count = len(current_events)
    if any(event["window_commits"] == 0 for event in analysis_events):
        forward_count = sum(event["assigned_invert"] == 0 for event in current_events)
        invert_count = sum(event["assigned_invert"] == 1 for event in current_events)
        total = forward_count + invert_count
        return {
            "estimate_log": None,
            "reason": "window_commits_zero",
            "assigned_forward": forward_count,
            "assigned_invert": invert_count,
            "assigned_invert_rate": invert_count / total if total else None,
        }
    if not has_terminal:
        forward_count = sum(event["assigned_invert"] == 0 for event in current_events)
        invert_count = sum(event["assigned_invert"] == 1 for event in current_events)
        total = forward_count + invert_count
        return {
            "estimate_log": None,
            "reason": "terminal_not_closed",
            "assigned_forward": forward_count,
            "assigned_invert": invert_count,
            "assigned_invert_rate": invert_count / total if total else None,
        }
    selected = [
        (current, following)
        for index, (current, following) in enumerate(
            zip(current_events, analysis_events[1:])
        )
        if membership(current, index, outcome_count)
    ]
    forward_count = sum(current["assigned_invert"] == 0 for current, _ in selected)
    invert_count = sum(current["assigned_invert"] == 1 for current, _ in selected)
    total = forward_count + invert_count
    arm_values: dict[int, list[float]] = {0: [], 1: []}
    for current, following in selected:
        current_rate = current["window_commits"] / current["window_us"]
        following_rate = following["window_commits"] / following["window_us"]
        outcome = math.log(following_rate / current_rate)
        arm_values[current["assigned_invert"]].append(outcome)
    if not forward_count or not invert_count:
        return {
            "estimate_log": None,
            "reason": "missing_assignment_arm",
            "assigned_forward": forward_count,
            "assigned_invert": invert_count,
            "assigned_invert_rate": invert_count / total if total else None,
        }
    estimate = statistics.fmean(arm_values[0]) - statistics.fmean(arm_values[1])
    return {
        "estimate_log": estimate,
        "reason": None,
        "assigned_forward": forward_count,
        "assigned_invert": invert_count,
        "assigned_invert_rate": invert_count / total,
    }


def _cluster_summary(
    runs: list[dict],
    membership: Callable[[dict, int, int], bool],
    *,
    confirmatory: bool,
) -> dict:
    run_estimates = []
    assignment_rate_all_events = []
    for run in sorted(runs, key=lambda item: item["step_policy_seed"]):
        run_identity = [
            run["cell_literal"],
            run["step_policy_seed"],
            run["binary_sha256"],
        ]
        events = [
            event for event in run["events"] if event.get("terminal_flush") == 0
        ]
        assignment_rate_all_events.append(
            {
                "run_identity": run_identity,
                "assignment_rate_all_events": statistics.fmean(
                    event["assigned_invert"] for event in events
                ),
            }
        )
        estimate = _run_difference(run, membership)
        run_estimates.append(
            {
                "run_identity": run_identity,
                **estimate,
                "effect_percent": (
                    100.0 * math.expm1(estimate["estimate_log"])
                    if estimate["estimate_log"] is not None
                    else None
                ),
            }
        )
    invalid_reasons = sorted(
        {item["reason"] for item in run_estimates if item["reason"] is not None}
    )
    cluster_count = len(run_estimates)
    complete = cluster_count == 12 and not invalid_reasons
    values = [item["estimate_log"] for item in run_estimates]
    numeric_values = [value for value in values if value is not None]
    theta = statistics.fmean(numeric_values) if numeric_values else None
    cluster_sd = (
        statistics.stdev(numeric_values)
        if len(numeric_values) > 1 and len(numeric_values) == cluster_count
        else None
    )
    se = cluster_sd / math.sqrt(cluster_count) if cluster_sd is not None else None
    ci90 = None
    ci95 = None
    if complete and theta is not None and se is not None:
        half95 = T95_DF11 * se
        ci95 = {
            "lower_log": theta - half95,
            "upper_log": theta + half95,
            "half_width_log": half95,
            "critical_value": T95_DF11,
        }
        ci95.update(
            lower_percent=100.0 * math.expm1(ci95["lower_log"]),
            upper_percent=100.0 * math.expm1(ci95["upper_log"]),
        )
        if confirmatory:
            half90 = T90_DF11 * se
            ci90 = {
                "lower_log": theta - half90,
                "upper_log": theta + half90,
                "half_width_log": half90,
                "critical_value": T90_DF11,
            }
            ci90.update(
                lower_percent=100.0 * math.expm1(ci90["lower_log"]),
                upper_percent=100.0 * math.expm1(ci90["upper_log"]),
            )
    reasons = list(invalid_reasons)
    if cluster_count != 12:
        reasons.append("requires_exactly_12_clusters")
    return {
        "cluster_count": cluster_count,
        "confirmatory_complete": bool(confirmatory and complete),
        "run_estimates": run_estimates,
        "assignment_rate_all_events": assignment_rate_all_events,
        "theta_log": theta if not invalid_reasons else None,
        "effect_percent": (
            100.0 * math.expm1(theta)
            if theta is not None and not invalid_reasons
            else None
        ),
        "cluster_variance": cluster_sd**2 if cluster_sd is not None else None,
        "cluster_sd": cluster_sd,
        "standard_error": se,
        "ci90": ci90,
        "ci95": ci95,
        "reasons": reasons,
    }


def _secondary_result(summary: dict) -> dict:
    if summary["reasons"]:
        return {
            "estimate_log": None,
            "effect_percent": None,
            "reason": ";".join(summary["reasons"]),
            "details": summary,
        }
    return {
        "estimate_log": summary["theta_log"],
        "effect_percent": summary["effect_percent"],
        "reason": None,
        "details": summary,
    }


def _primary_decision(ci90: dict, ci95: dict) -> dict:
    equivalent = (
        ci90["lower_log"] > -EQUIVALENCE_MARGIN
        and ci90["upper_log"] < EQUIVALENCE_MARGIN
    )
    recommended = ci95["lower_log"] > EQUIVALENCE_MARGIN
    inverted = ci95["upper_log"] < -EQUIVALENCE_MARGIN
    decision = "inconclusive"
    if equivalent:
        decision = "equivalent"
    elif recommended:
        decision = "recommended_direction_superior"
    elif inverted:
        decision = "inverted_direction_superior"
    return {
        "tost_equivalent": equivalent,
        "recommended_practical_superiority": recommended,
        "inverted_practical_superiority": inverted,
        "decision": decision,
    }


def analyze_counterfactual(
    diagnostic_paths: list[Path],
    preregistration_path: Path,
) -> dict:
    """Validate explicit artifacts and apply the frozen cluster-level analysis."""
    if type(diagnostic_paths) is not list or not diagnostic_paths:
        _fail("diagnostic_paths must be a nonempty explicit list")
    if len(diagnostic_paths) > 12 or any(
        not isinstance(path, Path) for path in diagnostic_paths
    ):
        _fail("diagnostic_paths must contain at most 12 Path objects")
    if not isinstance(preregistration_path, Path):
        _fail("preregistration_path must be a Path")
    preregistration = preregistration_path.resolve(strict=True)
    preregistration_sha256 = _sha256(preregistration)
    if preregistration_sha256 != ANALYSIS_PREREGISTRATION_SHA256:
        _fail("preregistration file SHA-256 does not match the frozen specification")
    resolved_paths = [path.resolve(strict=True) for path in diagnostic_paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        _fail("diagnostic_paths must identify unique files")
    inputs = [
        {"path": str(path), "sha256": _sha256(path)}
        for path in sorted(resolved_paths, key=str)
    ]
    artifacts = [_load_artifact(path) for path in sorted(resolved_paths, key=str)]
    if len({artifact["trace_counts"] for artifact in artifacts}) != 1:
        _fail("backoff trace symbol/string counts differ across artifacts")
    seeds = [artifact["seed"] for artifact in artifacts]
    if len(set(seeds)) != len(seeds):
        _fail("step_policy_seed values must be unique across artifacts")
    if len(seeds) == 12 and set(seeds) != PREREGISTERED_SEEDS:
        _fail("the 12 artifacts do not contain the exact preregistered seed set")

    def runs_for(workload: str, threads: int) -> list[dict]:
        return [artifact["rows"][(2, workload, threads)] for artifact in artifacts]

    include_all = lambda _event, _index, _count: True
    primary = _cluster_summary(
        runs_for(PRIMARY_WORKLOAD, PRIMARY_THREADS),
        include_all,
        confirmatory=True,
    )
    primary.update(
        {
            "stratum": {
                "cell_literal": CELL_LITERALS[2],
                "workload": PRIMARY_WORKLOAD,
                "threads": PRIMARY_THREADS,
            },
            "equivalence_margin_log": EQUIVALENCE_MARGIN,
            "equivalence_region_percent": {
                "lower": 100.0 * math.expm1(-EQUIVALENCE_MARGIN),
                "upper": 100.0 * math.expm1(EQUIVALENCE_MARGIN),
            },
            "tost_equivalent": None,
            "recommended_practical_superiority": None,
            "inverted_practical_superiority": None,
            "decision": "inconclusive",
        }
    )
    if primary["confirmatory_complete"]:
        primary.update(_primary_decision(primary["ci90"], primary["ci95"]))

    workload_threads = []
    for workload in WORKLOADS:
        for threads in THREADS:
            if (workload, threads) == (PRIMARY_WORKLOAD, PRIMARY_THREADS):
                continue
            summary = _cluster_summary(
                runs_for(workload, threads), include_all, confirmatory=False
            )
            workload_threads.append(
                {
                    "workload": workload,
                    "threads": threads,
                    **_secondary_result(summary),
                }
            )

    primary_runs = runs_for(PRIMARY_WORKLOAD, PRIMARY_THREADS)
    recommended_delta_sign = []
    for level in (-1, 0, 1):
        summary = _cluster_summary(
            primary_runs,
            lambda event, _index, _count, level=level: event["recommended_delta_sign"] == level,
            confirmatory=False,
        )
        recommended_delta_sign.append(
            {"level": level, **_secondary_result(summary)}
        )
    both_actions_feasible = []
    for level in (0, 1):
        summary = _cluster_summary(
            primary_runs,
            lambda event, _index, _count, level=level: event["both_actions_feasible"] == level,
            confirmatory=False,
        )
        both_actions_feasible.append(
            {"level": level, **_secondary_result(summary)}
        )
    time_block = []
    for block in range(4):
        summary = _cluster_summary(
            primary_runs,
            lambda _event, index, count, block=block: (
                count > 0 and min(3, (4 * index) // count) == block
            ),
            confirmatory=False,
        )
        time_block.append(
            {"block": block + 1, **_secondary_result(summary)}
        )

    return {
        "analysis_version": ANALYSIS_VERSION,
        "preregistration": {
            "path": str(preregistration),
            "sha256": preregistration_sha256,
        },
        "inputs": inputs,
        "primary": primary,
        "secondary": {
            "workload_threads": workload_threads,
            "recommended_delta_sign": recommended_delta_sign,
            "both_actions_feasible": both_actions_feasible,
            "time_block": time_block,
        },
    }
