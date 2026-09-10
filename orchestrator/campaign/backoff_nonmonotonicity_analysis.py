"""Descriptive reanalysis of recorded adaptive-backoff artifacts for T-2188.

The static curve and T-1941 residence distribution are deliberately kept as
separate, decision-ineligible summaries.  This module performs no new
measurement and makes no mechanism decision.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Sequence

__all__ = [
    "analyze_nonmonotonicity",
    "write_nonmonotonicity_analysis",
]

SCHEMA_VERSION = "izanagi-t2188-nonmonotonicity-analysis/v1"
POISSON_NOT_ADJUDICATED_REASON = (
    "The accepted trace inventory can mix count-triggered and time-triggered "
    "cells, while both window_us and Backoff_ may vary within a run; the "
    "recorded window-count dispersion is therefore descriptive and does not "
    "adjudicate a Poisson mechanism."
)
DIRECTIONAL_RECOMPUTATION_DEPENDENCY = (
    "This is not accuracy against independent ground truth: recomputed success "
    "and the following event's gradient_sign use the same throughput difference; "
    "the following gradient is that difference divided by the preceding action."
)
_INVENTORY_FIELDS = (
    "cell",
    "step_us",
    "update_us",
    "ceiling_us",
    "count_window",
    "count_cap_us",
    "threads",
    "workload",
)
_STATIC_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
_STOCK_STATES_US = tuple(range(0, 1001, 100))
_NEW_TRACE_CELL_AXES = {
    "nm-step0.5": (0.5, 10),
    "nm-step1": (1.0, 10),
    "nm-step1-u2560": (1.0, 2560),
    "nm-step2": (2.0, 10),
    "nm-step25": (25.0, 10),
    "nm-step100": (100.0, 10),
}
_J0_CELLS = (
    "nm-step0.5",
    "nm-step1",
    "nm-step2",
    "nm-step25",
    "nm-step100",
)


def _fail(message: str) -> None:
    raise ValueError(message)


def _exact_int(value: object, *, field: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail(f"{field} must be an exact integer >= {minimum}")
    return value


def _finite_number(value: object, *, field: str) -> int | float:
    if type(value) not in {int, float} or not math.isfinite(value):
        _fail(f"{field} must be a finite number")
    return value


def _markdown_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _strip_markdown(value: str) -> str:
    result = value.strip()
    changed = True
    while changed:
        changed = False
        for marker in ("**", "`"):
            if result.startswith(marker) and result.endswith(marker):
                result = result[len(marker) : -len(marker)].strip()
                changed = True
    return result


def _markdown_int(value: str, *, field: str) -> int:
    cleaned = _strip_markdown(value).replace(",", "")
    try:
        parsed = int(cleaned)
    except ValueError as exc:
        raise ValueError(f"{field} must contain an integer") from exc
    if parsed < 0:
        _fail(f"{field} must be nonnegative")
    return parsed


def _parse_stock_residence(path: Path) -> dict:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read T-1941 README {path}: {exc}") from exc

    values: dict[str, str] = {}
    wanted = {
        "call_count",
        "requested_us_sum",
        "unknown_state_call_count",
        "counter_overflowed",
        *(f"state_{state}_call_count" for state in _STOCK_STATES_US),
    }
    for line in lines:
        cells = _markdown_cells(line)
        if cells is None or len(cells) < 2:
            continue
        field = _strip_markdown(cells[0])
        if field in wanted:
            if field in values:
                _fail(f"{path}: duplicate stock field {field}")
            values[field] = _strip_markdown(cells[1])
    missing = sorted(wanted - set(values))
    if missing:
        _fail(f"{path}: T-1941 table is missing fields: {', '.join(missing)}")

    call_count = _markdown_int(values["call_count"], field="call_count")
    requested_us_sum = _markdown_int(
        values["requested_us_sum"], field="requested_us_sum"
    )
    unknown_count = _markdown_int(
        values["unknown_state_call_count"],
        field="unknown_state_call_count",
    )
    overflow_text = values["counter_overflowed"].lower()
    if overflow_text not in {"true", "false"}:
        _fail("counter_overflowed must be true or false")
    buckets = [
        {
            "backoff_us": state,
            "call_count": _markdown_int(
                values[f"state_{state}_call_count"],
                field=f"state_{state}_call_count",
            ),
        }
        for state in _STOCK_STATES_US
    ]
    recomputed_call_count = sum(bucket["call_count"] for bucket in buckets)
    recomputed_requested_us_sum = sum(
        bucket["backoff_us"] * bucket["call_count"] for bucket in buckets
    )
    return {
        "estimand": "call_weighted",
        "workload": "balanced",
        "decision_eligible": False,
        "call_count": call_count,
        "requested_us_sum": requested_us_sum,
        "unknown_state_call_count": unknown_count,
        "counter_overflowed": overflow_text == "true",
        "bucket_count": len(buckets),
        "buckets": buckets,
        "recomputed_bucket_call_count": recomputed_call_count,
        "bucket_call_count_matches_call_count": recomputed_call_count == call_count,
        "recomputed_requested_us_sum": recomputed_requested_us_sum,
        "weighted_sum_matches_requested_us_sum": (
            recomputed_requested_us_sum == requested_us_sum
        ),
        "mean_requested_us_per_call": (
            requested_us_sum / call_count if call_count else None
        ),
    }


def _static_measurement(value: str, *, field: str) -> dict:
    cleaned = value.replace("**", "").strip()
    if "欠測" in cleaned:
        return {
            "status": "missing",
            "throughput_tps": None,
            "abort_rate": None,
        }
    status = "invalid" if "無効" in cleaned else "measured"
    numeric = cleaned
    if status == "invalid":
        left = cleaned.find("(")
        right = cleaned.rfind(")")
        if left == -1 or right <= left:
            _fail(f"{field}: invalid entry lacks its observed numeric pair")
        numeric = cleaned[left + 1 : right]
    pieces = [piece.strip() for piece in numeric.split("/")]
    if len(pieces) != 2:
        _fail(f"{field}: expected 'throughput / abort_rate'")
    throughput = _markdown_int(pieces[0], field=f"{field}.throughput_tps")
    try:
        abort_rate = float(pieces[1])
    except ValueError as exc:
        raise ValueError(f"{field}.abort_rate must be numeric") from exc
    if not math.isfinite(abort_rate) or not 0.0 <= abort_rate <= 1.0:
        _fail(f"{field}.abort_rate must be between zero and one")
    return {
        "status": status,
        "throughput_tps": throughput,
        "abort_rate": abort_rate,
    }


def _parse_static_curve(path: Path) -> dict:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read static-tail README {path}: {exc}") from exc

    header_indexes = []
    for index, line in enumerate(lines):
        cells = _markdown_cells(line)
        if cells is None or len(cells) != 4:
            continue
        header = tuple(_strip_markdown(cell) for cell in cells)
        if header[0] == "b (µs)" and header[1:] == _STATIC_WORKLOADS:
            header_indexes.append(index)
    if not header_indexes:
        _fail(f"{path}: static T(b) table header is missing")
    header_index = header_indexes[-1]
    heading = None
    for line in reversed(lines[:header_index]):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            break
    table_identifier = heading or f"header at line {header_index + 1}"

    points = []
    seen_backoffs = set()
    for line in lines[header_index + 2 :]:
        cells = _markdown_cells(line)
        if cells is None or len(cells) != 4:
            break
        backoff_us = _markdown_int(cells[0], field="static_curve.backoff_us")
        if backoff_us in seen_backoffs:
            _fail(f"{path}: duplicate static backoff coordinate {backoff_us}")
        seen_backoffs.add(backoff_us)
        measurements = {
            workload: _static_measurement(
                cell,
                field=f"static_curve[{backoff_us}].{workload}",
            )
            for workload, cell in zip(_STATIC_WORKLOADS, cells[1:])
        }
        points.append(
            {
                "backoff_us": backoff_us,
                "measurements": measurements,
            }
        )
    if not points:
        _fail(f"{path}: static T(b) table contains no points")
    return {
        "mixture_assumption_required": True,
        "decision_eligible": False,
        "source_table": {
            "selection_rule": "last_matching_header",
            "identifier": table_identifier,
            "header_line": header_index + 1,
        },
        "points": points,
    }


def _positive_number(value: object, *, field: str) -> float:
    parsed = float(_finite_number(value, field=field))
    if parsed <= 0:
        _fail(f"{field} must be greater than zero")
    return parsed


def _new_trace_extime(document: dict, run: dict, *, binding: str) -> float:
    candidates = []
    for owner, prefix in ((run, binding), (document, "new_trace")):
        for field in ("extime", "extime_s"):
            if field in owner:
                candidates.append(
                    _positive_number(owner[field], field=f"{prefix}.{field}")
                )
    metadata = document.get("metadata")
    if type(metadata) is dict:
        for field in ("extime", "extime_s"):
            if field in metadata:
                candidates.append(
                    _positive_number(
                        metadata[field], field=f"new_trace.metadata.{field}"
                    )
                )
    if not candidates:
        _fail(f"{binding} requires extime (seconds) in the run or document")
    if any(value != candidates[0] for value in candidates[1:]):
        _fail(f"{binding} has conflicting extime values")
    return candidates[0]


def _load_new_trace(path: Path) -> tuple[Path, dict[str, dict]]:
    try:
        resolved = path.resolve(strict=True)
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid new trace artifact {path}: {exc}") from exc
    if type(document) is not dict or type(document.get("trace_runs")) is not list:
        _fail(f"{resolved}: trace_runs must be a list")

    runs = {}
    for index, raw in enumerate(document["trace_runs"]):
        binding = f"{resolved}:trace_runs[{index}]"
        if type(raw) is not dict:
            _fail(f"{binding} must be an object")
        cell = raw.get("cell")
        if cell not in _NEW_TRACE_CELL_AXES:
            _fail(f"{binding}.cell is not a registered nonmonotonic trace cell")
        if cell in runs:
            _fail(f"{resolved}: duplicate new trace cell {cell}")
        expected_step, expected_update = _NEW_TRACE_CELL_AXES[cell]
        step = float(_finite_number(raw.get("step_us"), field=f"{binding}.step_us"))
        update = _exact_int(raw.get("update_us"), field=f"{binding}.update_us")
        if step != expected_step or update != expected_update:
            _fail(f"{binding} does not match the registered step/update axes")
        threads = _exact_int(raw.get("threads"), field=f"{binding}.threads")
        workload = raw.get("workload")
        if threads != 48 or workload != "write-heavy":
            _fail(f"{binding} must be write-heavy at 48 threads")
        median_tps = _positive_number(
            raw.get("median_tps"), field=f"{binding}.median_tps"
        )
        throughputs = raw.get("throughputs")
        if type(throughputs) is not list or not throughputs:
            _fail(f"{binding}.throughputs must be a nonempty list")
        parsed_throughputs = [
            _positive_number(value, field=f"{binding}.throughputs[{item_index}]")
            for item_index, value in enumerate(throughputs)
        ]
        summary = raw.get("trace_summary")
        if type(summary) is not dict:
            _fail(f"{binding}.trace_summary must be an object")
        updates = _exact_int(
            summary.get("updates"),
            field=f"{binding}.trace_summary.updates",
            minimum=1,
        )
        retained = _exact_int(
            summary.get("retained"), field=f"{binding}.trace_summary.retained"
        )
        dropped = _exact_int(
            summary.get("dropped"), field=f"{binding}.trace_summary.dropped"
        )
        if retained + dropped != updates:
            _fail(f"{binding}.trace_summary retained + dropped must equal updates")
        events = raw.get("trace_events")
        if type(events) is not list or not events:
            _fail(f"{binding}.trace_events must be a nonempty list")
        if len(events) != retained:
            _fail(f"{binding}.trace_events length must equal retained")
        parsed_events = []
        for event_index, event in enumerate(events):
            event_binding = f"{binding}.trace_events[{event_index}]"
            if type(event) is not dict:
                _fail(f"{event_binding} must be an object")
            gradient = event.get("gradient_sign")
            if type(gradient) is not int or gradient not in {-1, 0, 1}:
                _fail(f"{event_binding}.gradient_sign must be -1, 0, or 1")
            trigger = event.get("trigger")
            if type(trigger) is not str or not trigger:
                _fail(f"{event_binding}.trigger must be a nonempty string")
            parsed_events.append(
                {
                    "window_us": _exact_int(
                        event.get("window_us"),
                        field=f"{event_binding}.window_us",
                        minimum=1,
                    ),
                    "window_commits": _exact_int(
                        event.get("window_commits"),
                        field=f"{event_binding}.window_commits",
                    ),
                    "backoff_before": float(
                        _finite_number(
                            event.get("backoff_before"),
                            field=f"{event_binding}.backoff_before",
                        )
                    ),
                    "backoff_after": float(
                        _finite_number(
                            event.get("backoff_after"),
                            field=f"{event_binding}.backoff_after",
                        )
                    ),
                    "gradient_sign": gradient,
                    "trigger": trigger,
                }
            )
        runs[cell] = {
            "cell": cell,
            "step_us": step,
            "update_us": update,
            "threads": threads,
            "workload": workload,
            "median_tps": median_tps,
            "throughputs": parsed_throughputs,
            "updates": updates,
            "retained": retained,
            "dropped": dropped,
            "extime_s": _new_trace_extime(document, raw, binding=binding),
            "events": parsed_events,
        }
    missing = sorted(set(_NEW_TRACE_CELL_AXES) - set(runs))
    if missing:
        _fail(f"{resolved}: missing registered new trace cells: {', '.join(missing)}")
    return resolved, runs


def _validated_baseline_tps(values: Mapping[str, object]) -> dict[str, float]:
    if not isinstance(values, Mapping):
        _fail("baseline_tps must be a cell-to-throughput mapping")
    missing = sorted(set(_J0_CELLS) - set(values))
    extra = sorted(set(values) - set(_J0_CELLS))
    if missing or extra:
        _fail(
            "baseline_tps must contain exactly the five 10-us cells; "
            f"missing={missing}, extra={extra}"
        )
    return {
        cell: _positive_number(values[cell], field=f"baseline_tps[{cell}]")
        for cell in _J0_CELLS
    }


def _validated_static_low_b(values: Mapping[object, object]) -> dict[float, float]:
    if not isinstance(values, Mapping) or not values:
        _fail("static_low_b must be a nonempty backoff-to-throughput mapping")
    result = {}
    for raw_backoff, raw_tps in values.items():
        try:
            backoff = float(raw_backoff)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"static_low_b coordinate {raw_backoff!r} is invalid"
            ) from exc
        if not math.isfinite(backoff) or backoff < 0:
            _fail("static_low_b coordinates must be finite and nonnegative")
        if backoff in result:
            _fail(f"duplicate static_low_b coordinate {backoff}")
        result[backoff] = _positive_number(
            raw_tps, field=f"static_low_b[{raw_backoff}]"
        )
    return result


def _j0_observer_control(runs: dict[str, dict], baseline_tps: dict[str, float]) -> dict:
    ratios = [runs[cell]["median_tps"] / baseline_tps[cell] for cell in _J0_CELLS]
    common_factor = statistics.median(ratios)
    points = []
    residuals = {}
    for cell, ratio in zip(_J0_CELLS, ratios):
        residual = ratio / common_factor - 1.0
        residuals[cell] = residual
        points.append(
            {
                "cell": cell,
                "baseline_tps": baseline_tps[cell],
                "observed_tps": runs[cell]["median_tps"],
                "observed_to_baseline_ratio": ratio,
                "normalized_residual": residual,
            }
        )
    cliff_ratio = runs["nm-step0.5"]["median_tps"] / runs["nm-step1"][
        "median_tps"
    ]
    recovery_ratio = runs["nm-step100"]["median_tps"] / runs["nm-step25"][
        "median_tps"
    ]
    checks = {
        "a_step0.5_to_step1_cliff_at_least_1.5": cliff_ratio >= 1.5,
        "b_step25_to_step100_recovery_at_least_1.05": recovery_ratio >= 1.05,
        "c_all_normalized_residuals_within_0.25": all(
            abs(value) <= 0.25 for value in residuals.values()
        ),
    }
    passed = all(checks.values())
    return {
        "passed": passed,
        "verdict": "passed" if passed else "observer_control_failed",
        "common_factor": common_factor,
        "points": points,
        "normalized_residuals": residuals,
        "cliff_ratio_step0.5_over_step1": cliff_ratio,
        "recovery_ratio_step100_over_step25": recovery_ratio,
        "checks": checks,
    }


def _edge_observations(events: list[dict]) -> list[dict]:
    observations = []
    event_count = len(events)
    for index in range(1, event_count):
        gradient = events[index]["gradient_sign"]
        if gradient == 0:
            continue
        previous = events[index - 1]
        edge = tuple(
            sorted((previous["backoff_before"], previous["backoff_after"]))
        )
        observations.append(
            {
                "edge": edge,
                "positive": gradient == 1,
                "segment": min(2, index * 3 // event_count),
            }
        )
    return observations


def _edge_counts(observations: list[dict], segment: int | None = None) -> dict:
    counts = {}
    for observation in observations:
        if segment is not None and observation["segment"] != segment:
            continue
        bucket = counts.setdefault(observation["edge"], [0, 0])
        bucket[0] += 1
        bucket[1] += observation["positive"]
    return counts


def _fixed_edge_comparison(left: dict, right: dict) -> dict:
    common = sorted(set(left) & set(right))
    rows = []
    weighted_left = 0.0
    weighted_right = 0.0
    total_weight = 0
    for edge in common:
        left_count, left_positive = left[edge]
        right_count, right_positive = right[edge]
        left_p = left_positive / left_count
        right_p = right_positive / right_count
        weight = min(left_count, right_count)
        left_instability = 2.0 * left_p * (1.0 - left_p)
        right_instability = 2.0 * right_p * (1.0 - right_p)
        weighted_left += weight * left_instability
        weighted_right += weight * right_instability
        total_weight += weight
        rows.append(
            {
                "unordered_edge": list(edge),
                "update10": {
                    "count": left_count,
                    "positive_count": left_positive,
                    "positive_fraction": left_p,
                    "sign_disagreement": left_instability,
                },
                "update2560": {
                    "count": right_count,
                    "positive_count": right_positive,
                    "positive_fraction": right_p,
                    "sign_disagreement": right_instability,
                },
                "fixed_weight": weight,
            }
        )
    left_value = weighted_left / total_weight if total_weight else None
    right_value = weighted_right / total_weight if total_weight else None
    return {
        "common_edge_count": len(common),
        "fixed_weight_sum": total_weight,
        "update10_sign_disagreement": left_value,
        "update2560_sign_disagreement": right_value,
        "difference_update10_minus_update2560": (
            left_value - right_value
            if left_value is not None and right_value is not None
            else None
        ),
        "edges": rows,
    }


def _j1_sign_instability(runs: dict[str, dict], coverages: dict[str, float]) -> dict:
    left_observations = _edge_observations(runs["nm-step1"]["events"])
    right_observations = _edge_observations(runs["nm-step1-u2560"]["events"])
    overall = _fixed_edge_comparison(
        _edge_counts(left_observations), _edge_counts(right_observations)
    )
    segments = []
    segment_directions = []
    for segment in range(3):
        comparison = _fixed_edge_comparison(
            _edge_counts(left_observations, segment),
            _edge_counts(right_observations, segment),
        )
        difference = comparison["difference_update10_minus_update2560"]
        same_direction = difference is not None and difference > 0.0
        segment_directions.append(same_direction)
        segments.append(
            {
                "segment": segment + 1,
                **comparison,
                "update10_higher": same_direction,
            }
        )
    enough_support = overall["common_edge_count"] >= 10
    direction_stable = all(segment_directions)
    threshold_met = (
        overall["difference_update10_minus_update2560"] is not None
        and overall["difference_update10_minus_update2560"] >= 0.10
    )
    qualifiers = []
    if not direction_stable:
        qualifiers.append("direction_unstable")
    if not enough_support:
        verdict = "insufficient_common_support"
    elif threshold_met and direction_stable:
        verdict = "supported"
    else:
        verdict = "not_supported"
    relevant_cells = ("nm-step1", "nm-step1-u2560")
    terminal_only = any(coverages[cell] < 1.0 for cell in relevant_cells)
    result = {
        "verdict": verdict,
        "estimator_specified_after_data": True,
        "estimator": "2p(1-p), excluding gradient_sign == 0",
        "common_support_minimum": 10,
        "support_threshold": 0.10,
        "terminal_slice_only": terminal_only,
        "overall": overall,
        "segments": segments,
        "direction_stable_across_all_three_segments": direction_stable,
        "qualifiers": qualifiers,
    }
    if terminal_only:
        result["terminal_slice_association_only"] = True
    return result


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _residence_row(run: dict, coverage: float) -> dict:
    events = run["events"]
    total_time = sum(event["window_us"] for event in events)
    values = [event["backoff_before"] for event in events]
    probabilities = {}
    for threshold in (50, 100):
        probabilities[f"above_{threshold}"] = {
            "time_weighted": sum(
                event["window_us"]
                for event in events
                if event["backoff_before"] > threshold
            )
            / total_time,
            "event_weighted": sum(value > threshold for value in values)
            / len(values),
        }
    return {
        "cell": run["cell"],
        "probabilities": probabilities,
        "backoff_before_quantiles": {
            "p50": _quantile(values, 0.50),
            "p90": _quantile(values, 0.90),
            "p99": _quantile(values, 0.99),
            "max": max(values),
        },
        "retained_coverage": coverage,
        "terminal_slice_only": coverage < 1.0,
    }


def _j2_high_residence(runs: dict[str, dict], coverages: dict[str, float]) -> dict:
    rows = [_residence_row(runs[cell], coverages[cell]) for cell in _J0_CELLS]
    by_cell = {row["cell"]: row for row in rows}
    comparisons = {}
    weight_directions = {}
    for weighting in ("time_weighted", "event_weighted"):
        threshold_rows = {}
        for threshold in (50, 100):
            valley = by_cell["nm-step25"]["probabilities"][f"above_{threshold}"][
                weighting
            ]
            best = by_cell["nm-step0.5"]["probabilities"][f"above_{threshold}"][
                weighting
            ]
            threshold_rows[f"above_{threshold}"] = {
                "nm-step25": valley,
                "nm-step0.5": best,
                "difference_valley_minus_best": valley - best,
                "valley_higher": valley > best,
            }
        comparisons[weighting] = threshold_rows
        weight_directions[weighting] = {
            threshold: row["valley_higher"]
            for threshold, row in threshold_rows.items()
        }
    weight_sensitive = any(
        weight_directions["time_weighted"][threshold]
        != weight_directions["event_weighted"][threshold]
        for threshold in ("above_50", "above_100")
    )
    supported = all(
        direction
        for directions in weight_directions.values()
        for direction in directions.values()
    )
    relevant_cells = ("nm-step0.5", "nm-step25")
    terminal_only = any(coverages[cell] < 1.0 for cell in relevant_cells)
    qualifiers = ["weight_sensitive"] if weight_sensitive else []
    result = {
        "verdict": "supported" if supported else "not_supported",
        "terminal_slice_only": terminal_only,
        "cells": rows,
        "valley_vs_best": comparisons,
        "same_direction_for_both_weightings": not weight_sensitive,
        "qualifiers": qualifiers,
    }
    if terminal_only:
        result["terminal_slice_association_only"] = True
    return result


def _j3_time_trigger_fano(runs: dict[str, dict], coverages: dict[str, float]) -> dict:
    rows = []
    for cell in _NEW_TRACE_CELL_AXES:
        run = runs[cell]
        commits = [event["window_commits"] for event in run["events"]]
        windows = [event["window_us"] for event in run["events"]]
        mean = statistics.fmean(commits)
        variance = statistics.pvariance(commits)
        trigger_counts = {}
        for event in run["events"]:
            trigger = event["trigger"]
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        rows.append(
            {
                "cell": cell,
                "window_commits": {
                    "mean": mean,
                    "variance": variance,
                    "variance_over_mean": variance / mean if mean else None,
                },
                "window_us": {
                    "median": statistics.median(windows),
                    "mean": statistics.fmean(windows),
                },
                "trigger_counts": trigger_counts,
                "terminal_slice_only": coverages[cell] < 1.0,
            }
        )
    return {
        "descriptive_only": True,
        "walking_model_fano_values": [2.0, 4.0],
        "cells": rows,
    }


def _j4_effective_update_interval(
    runs: dict[str, dict],
) -> tuple[dict, dict[str, float]]:
    rows = []
    coverages = {}
    for cell in _NEW_TRACE_CELL_AXES:
        run = runs[cell]
        effective_us = run["extime_s"] * 1_000_000.0 / run["updates"]
        coverage = sum(event["window_us"] for event in run["events"]) / (
            run["extime_s"] * 1_000_000.0
        )
        coverages[cell] = coverage
        row = {
            "cell": cell,
            "updates": run["updates"],
            "extime_s": run["extime_s"],
            "nominal_update_us": run["update_us"],
            "effective_update_us": effective_us,
            "effective_to_nominal_ratio": effective_us / run["update_us"],
            "retained": run["retained"],
            "dropped": run["dropped"],
            "retained_coverage": coverage,
        }
        if coverage < 1.0:
            row["terminal_slice_only"] = True
        rows.append(row)
    return {"all_run_quantity": True, "cells": rows}, coverages


def _mixture_curve(
    static_curve: dict, static_low_b: dict[float, float]
) -> list[tuple[float, float]]:
    points = dict(static_low_b)
    for point in static_curve["points"]:
        measurement = point["measurements"]["write-heavy"]
        if measurement["status"] != "measured":
            continue
        backoff = float(point["backoff_us"])
        throughput = float(measurement["throughput_tps"])
        if backoff in points and points[backoff] != throughput:
            _fail(f"static curve has conflicting throughput at b={backoff}")
        points[backoff] = throughput
    if len(points) < 2:
        _fail("mechanism mixture requires at least two measured static T(b) points")
    return sorted(points.items())


def _flat_linear_interpolation(
    curve: list[tuple[float, float]], backoff: float
) -> tuple[float, bool]:
    if backoff < curve[0][0]:
        return curve[0][1], True
    if backoff > curve[-1][0]:
        return curve[-1][1], True
    for (left_b, left_tps), (right_b, right_tps) in zip(curve, curve[1:]):
        if left_b <= backoff <= right_b:
            if backoff == left_b or right_b == left_b:
                return left_tps, False
            fraction = (backoff - left_b) / (right_b - left_b)
            return left_tps + fraction * (right_tps - left_tps), False
    return curve[-1][1], False


def _mechanism_mixture(
    runs: dict[str, dict],
    static_curve: dict,
    static_low_b: dict[float, float],
    coverages: dict[str, float],
) -> dict:
    curve = _mixture_curve(static_curve, static_low_b)
    rows = []
    for cell in _NEW_TRACE_CELL_AXES:
        run = runs[cell]
        weighted_sum = 0.0
        unmeasured_time = 0
        total_time = sum(event["window_us"] for event in run["events"])
        for event in run["events"]:
            throughput, unmeasured = _flat_linear_interpolation(
                curve, event["backoff_before"]
            )
            weighted_sum += event["window_us"] * throughput
            if unmeasured:
                unmeasured_time += event["window_us"]
        prediction = weighted_sum / total_time
        rows.append(
            {
                "cell": cell,
                "observed_tps": run["median_tps"],
                "mixture_tps": prediction,
                "mixture_to_observed_ratio": prediction / run["median_tps"],
                "unmeasured_time_fraction": unmeasured_time / total_time,
                "terminal_slice_only": coverages[cell] < 1.0,
            }
        )
    return {
        "mixture_assumption_required": True,
        "descriptive_only": True,
        "interpolation": "linear_with_flat_endpoints_and_no_extrapolation",
        "measured_curve": [
            {"backoff_us": backoff, "throughput_tps": throughput}
            for backoff, throughput in curve
        ],
        "cells": rows,
    }


def _analyze_new_trace(
    path: Path,
    baseline_tps: Mapping[str, object],
    static_low_b: Mapping[object, object],
    static_curve: dict,
) -> dict:
    resolved, runs = _load_new_trace(path)
    baseline = _validated_baseline_tps(baseline_tps)
    low_curve = _validated_static_low_b(static_low_b)
    j4, coverages = _j4_effective_update_interval(runs)
    return {
        "source": str(resolved),
        "J0": _j0_observer_control(runs, baseline),
        "J1": _j1_sign_instability(runs, coverages),
        "J2": _j2_high_residence(runs, coverages),
        "J3": _j3_time_trigger_fano(runs, coverages),
        "J4": j4,
        "mechanism_mixture": _mechanism_mixture(
            runs, static_curve, low_curve, coverages
        ),
    }


def _load_trace_runs(trace_dir: Path) -> tuple[list[Path], list[dict]]:
    if not trace_dir.is_dir():
        raise NotADirectoryError(trace_dir)
    paths = sorted(trace_dir.rglob("*.nqsv.json"), key=lambda path: str(path))
    if not paths:
        _fail(f"{trace_dir}: no *.nqsv.json files found recursively")
    runs = []
    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid trace artifact {path}: {exc}") from exc
        if type(document) is not dict or type(document.get("trace_runs")) is not list:
            _fail(f"{path}: trace_runs must be a list")
        relative_path = path.relative_to(trace_dir).as_posix()
        for index, raw_run in enumerate(document["trace_runs"]):
            if type(raw_run) is not dict:
                _fail(f"{path}: trace_runs[{index}] must be an object")
            inventory = {}
            for field in _INVENTORY_FIELDS:
                value = raw_run.get(field)
                binding = f"{path}:trace_runs[{index}].{field}"
                if field in {"cell", "workload"}:
                    if type(value) is not str or not value:
                        _fail(f"{binding} must be a nonempty string")
                elif field in {
                    "update_us",
                    "count_window",
                    "count_cap_us",
                    "threads",
                }:
                    value = _exact_int(value, field=binding)
                else:
                    value = _finite_number(value, field=binding)
                inventory[field] = value
            events = raw_run.get("trace_events")
            if type(events) is not list or not events:
                _fail(f"{path}:trace_runs[{index}].trace_events must be nonempty")
            directional = raw_run.get("directional_success")
            if type(directional) is not dict:
                _fail(
                    f"{path}:trace_runs[{index}].directional_success "
                    "must be an object"
                )
            stored_successes = _exact_int(
                directional.get("successes"),
                field=f"{path}:trace_runs[{index}].directional_success.successes",
            )
            runs.append(
                {
                    "identity": {
                        "source_file": relative_path,
                        "trace_run_index": index,
                        **inventory,
                    },
                    "inventory": inventory,
                    "events": events,
                    "stored_successes": stored_successes,
                }
            )
    if not runs:
        _fail(f"{trace_dir}: trace artifacts contain no trace runs")
    return paths, runs


def _inventory_summary(paths: list[Path], runs: list[dict]) -> dict:
    unique: dict[str, dict] = {}
    for run in runs:
        cell = run["inventory"]
        key = json.dumps(cell, ensure_ascii=False, sort_keys=True)
        unique[key] = cell
    cells = [unique[key] for key in sorted(unique)]
    return {
        "file_count": len(paths),
        "trace_run_count": len(runs),
        "cell_count": len(cells),
        "cells": cells,
        "time_triggered_cell_count": sum(
            cell["count_window"] == 0 for cell in cells
        ),
    }


def _empty_directional_cross_tab() -> list[dict]:
    return [
        {
            "recomputed_success": success,
            "next_gradient_positive": positive,
            "pair_count": 0,
        }
        for success in (False, True)
        for positive in (False, True)
    ]


def _add_to_directional_cross_tab(
    cross_tab: list[dict], *, recomputed_success: bool, next_gradient_positive: bool
) -> None:
    for cell in cross_tab:
        if (
            cell["recomputed_success"] is recomputed_success
            and cell["next_gradient_positive"] is next_gradient_positive
        ):
            cell["pair_count"] += 1
            return
    raise AssertionError("directional cross-tab is missing a boolean cell")


def _event_is_terminal(event: dict) -> bool:
    return event.get("terminal_flush") == 1 or event.get("trigger") == "terminal"


def _recomputed_directional_pairs(run: dict) -> list[dict]:
    pairs = []
    for index, (current, following) in enumerate(
        zip(run["events"], run["events"][1:])
    ):
        binding = f"{run['identity']['source_file']}:event_pair[{index}]"
        if type(current) is not dict or type(following) is not dict:
            _fail(f"{binding} events must be objects")
        current_seq = _exact_int(current.get("seq"), field=f"{binding}.current.seq")
        following_seq = _exact_int(
            following.get("seq"), field=f"{binding}.following.seq"
        )
        before = _finite_number(
            current.get("backoff_before"), field=f"{binding}.backoff_before"
        )
        after = _finite_number(
            current.get("backoff_after"), field=f"{binding}.backoff_after"
        )
        gradient = following.get("gradient_sign")
        if type(gradient) is not int or gradient not in {-1, 0, 1}:
            _fail(f"{binding}.following.gradient_sign must be -1, 0, or 1")
        action = Decimal(str(after)) - Decimal(str(before))
        if action == 0:
            continue
        current_commits = _exact_int(
            current.get("window_commits"), field=f"{binding}.current.window_commits"
        )
        following_commits = _exact_int(
            following.get("window_commits"),
            field=f"{binding}.following.window_commits",
        )
        current_window = _exact_int(
            current.get("window_us"),
            field=f"{binding}.current.window_us",
            minimum=1,
        )
        following_window = _exact_int(
            following.get("window_us"),
            field=f"{binding}.following.window_us",
            minimum=1,
        )
        current_throughput = Decimal(current_commits) / Decimal(current_window)
        following_throughput = Decimal(following_commits) / Decimal(
            following_window
        )
        throughput_delta = following_throughput - current_throughput
        recomputed_success = (
            (action > 0) - (action < 0)
            == (throughput_delta > 0) - (throughput_delta < 0)
        )
        next_gradient_positive = gradient == 1
        pairs.append(
            {
                "current_seq": current_seq,
                "following_seq": following_seq,
                "recomputed_success": recomputed_success,
                "next_gradient_positive": next_gradient_positive,
                "contains_terminal_event": (
                    _event_is_terminal(current) or _event_is_terminal(following)
                ),
                "matches": recomputed_success == next_gradient_positive,
            }
        )
    return pairs


def _directional_recomputation_summary(runs: list[dict]) -> dict:
    rows = []
    overall_cross_tab = _empty_directional_cross_tab()
    mismatch_pairs = []
    for run in runs:
        pairs = _recomputed_directional_pairs(run)
        cross_tab = _empty_directional_cross_tab()
        for pair in pairs:
            _add_to_directional_cross_tab(
                cross_tab,
                recomputed_success=pair["recomputed_success"],
                next_gradient_positive=pair["next_gradient_positive"],
            )
            _add_to_directional_cross_tab(
                overall_cross_tab,
                recomputed_success=pair["recomputed_success"],
                next_gradient_positive=pair["next_gradient_positive"],
            )
        mismatches = [pair for pair in pairs if not pair["matches"]]
        mismatch_identifiers = [
            {
                "current_seq": pair["current_seq"],
                "following_seq": pair["following_seq"],
            }
            for pair in mismatches
        ]
        mismatch_pairs.extend(
            {"run": run["identity"], **identifier}
            for identifier in mismatch_identifiers
        )
        stored = run["stored_successes"]
        recomputed = sum(pair["recomputed_success"] for pair in pairs)
        rows.append(
            {
                "run": run["identity"],
                "nonzero_action_pair_count": len(pairs),
                "stored_directional_successes": stored,
                "recomputed_directional_successes": recomputed,
                "stored_total_matches_recomputed": stored == recomputed,
                "cross_tab": cross_tab,
                "mismatch_pair_count": len(mismatches),
                "mismatch_pair_seqs": mismatch_identifiers,
                "terminal_pair_count": sum(
                    pair["contains_terminal_event"] for pair in pairs
                ),
                "pairs": pairs,
            }
        )
    return {
        "ground_truth_independent": False,
        "dependency_note": DIRECTIONAL_RECOMPUTATION_DEPENDENCY,
        "run_count": len(rows),
        "nonzero_action_pair_count": sum(
            row["nonzero_action_pair_count"] for row in rows
        ),
        "cross_tab": overall_cross_tab,
        "mismatch_pair_count": len(mismatch_pairs),
        "mismatch_pairs": mismatch_pairs,
        "stored_successes_total": sum(
            row["stored_directional_successes"] for row in rows
        ),
        "recomputed_directional_successes_total": sum(
            row["recomputed_directional_successes"] for row in rows
        ),
        "runs": rows,
    }


def _window_dispersion_summary(runs: list[dict]) -> dict:
    rows = []
    for run in runs:
        commits = []
        windows = []
        for index, event in enumerate(run["events"]):
            if type(event) is not dict:
                _fail(
                    f"{run['identity']['source_file']}:event[{index}] "
                    "must be an object"
                )
            commits.append(
                _exact_int(
                    event.get("window_commits"),
                    field=(
                        f"{run['identity']['source_file']}:event[{index}]"
                        ".window_commits"
                    ),
                )
            )
            windows.append(
                _exact_int(
                    event.get("window_us"),
                    field=f"{run['identity']['source_file']}:event[{index}].window_us",
                    minimum=1,
                )
            )
        commits_mean = statistics.fmean(commits)
        commits_variance = statistics.pvariance(commits)
        rows.append(
            {
                "identity": run["identity"],
                "window_commits": {
                    "count": len(commits),
                    "mean": commits_mean,
                    "variance": commits_variance,
                    "variance_over_mean": (
                        commits_variance / commits_mean if commits_mean else None
                    ),
                },
                "window_us": {
                    "median": statistics.median(windows),
                    "mean": statistics.fmean(windows),
                    "max": max(windows),
                },
            }
        )
    return {
        "poisson_verdict": "not_adjudicated",
        "not_adjudicated_reason": POISSON_NOT_ADJUDICATED_REASON,
        "runs": rows,
    }


def analyze_nonmonotonicity(
    trace_dir: Path,
    stock_readme: Path,
    static_tail_readme: Path,
    *,
    new_trace_json: Path | None = None,
    baseline_tps: Mapping[str, object] | None = None,
    static_low_b: Mapping[object, object] | None = None,
) -> dict:
    """Return descriptive T-2188 summaries from existing artifacts only."""
    inputs = (trace_dir, stock_readme, static_tail_readme)
    if not all(isinstance(path, Path) for path in inputs):
        _fail("trace_dir and README inputs must be Path objects")
    resolved_trace_dir = trace_dir.resolve(strict=True)
    resolved_stock = stock_readme.resolve(strict=True)
    resolved_static = static_tail_readme.resolve(strict=True)
    if not resolved_stock.is_file() or not resolved_static.is_file():
        _fail("stock_readme and static_tail_readme must be files")
    paths, runs = _load_trace_runs(resolved_trace_dir)
    result = {
        "schema_version": SCHEMA_VERSION,
        "certified": False,
        "headline_eligible": False,
        "throughput_scope": "diagnostic_only",
        "inputs": {
            "trace_dir": str(resolved_trace_dir),
            "trace_files": [
                path.relative_to(resolved_trace_dir).as_posix() for path in paths
            ],
            "stock_readme": str(resolved_stock),
            "static_tail_readme": str(resolved_static),
        },
        "trace_inventory": _inventory_summary(paths, runs),
        "directional_success_recomputation": _directional_recomputation_summary(
            runs
        ),
        "window_count_dispersion": _window_dispersion_summary(runs),
        "stock_residence_t1941": _parse_stock_residence(resolved_stock),
        "static_curve": _parse_static_curve(resolved_static),
    }
    if new_trace_json is not None:
        if not isinstance(new_trace_json, Path):
            _fail("new_trace_json must be a Path")
        if baseline_tps is None or static_low_b is None:
            _fail("new_trace_json requires baseline_tps and static_low_b")
        result["new_trace_analysis"] = _analyze_new_trace(
            new_trace_json,
            baseline_tps,
            static_low_b,
            result["static_curve"],
        )
    elif baseline_tps is not None or static_low_b is not None:
        _fail("baseline_tps and static_low_b require new_trace_json")
    return result


def write_nonmonotonicity_analysis(
    trace_dir: Path,
    stock_readme: Path,
    static_tail_readme: Path,
    output: Path,
    *,
    new_trace_json: Path | None = None,
    baseline_tps: Mapping[str, object] | None = None,
    static_low_b: Mapping[object, object] | None = None,
) -> dict:
    """Analyze the inputs and create ``output`` without replacing any file."""
    if not isinstance(output, Path):
        _fail("output must be a Path")
    if output.exists():
        raise FileExistsError(output)
    result = analyze_nonmonotonicity(
        trace_dir,
        stock_readme,
        static_tail_readme,
        new_trace_json=new_trace_json,
        baseline_tps=baseline_tps,
        static_low_b=static_low_b,
    )
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    return result


def _json_or_assignments(values: list[str] | None, *, field: str) -> dict:
    if not values:
        return {}
    result = {}
    for value in values:
        if "=" in value:
            key, raw_number = value.split("=", 1)
            if not key or key in result:
                _fail(f"{field} contains an empty or duplicate key {key!r}")
            try:
                result[key] = float(raw_number)
            except ValueError as exc:
                raise ValueError(f"{field}[{key}] must be numeric") from exc
            continue
        try:
            candidate = Path(value)
            if candidate.is_file():
                parsed = json.loads(candidate.read_text(encoding="utf-8"))
            else:
                parsed = json.loads(value)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"{field} must be key=value or a JSON object: {exc}"
            ) from exc
        if type(parsed) is not dict:
            _fail(f"{field} JSON must be an object")
        for key, number in parsed.items():
            key = str(key)
            if key in result:
                _fail(f"{field} contains duplicate key {key!r}")
            result[key] = number
    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reanalyze recorded adaptive-backoff artifacts for T-2188."
    )
    parser.add_argument("--trace-dir", required=True, type=Path)
    parser.add_argument("--stock-readme", required=True, type=Path)
    parser.add_argument("--static-tail-readme", required=True, type=Path)
    parser.add_argument("--new-trace-json", type=Path)
    parser.add_argument(
        "--baseline-tps",
        action="append",
        metavar="CELL=TPS_OR_JSON",
        help="repeat cell=tps or pass a JSON object/path",
    )
    parser.add_argument(
        "--static-low-b",
        action="append",
        metavar="BACKOFF=TPS_OR_JSON",
        help="repeat backoff=tps or pass a JSON object/path",
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    baseline_tps = _json_or_assignments(args.baseline_tps, field="baseline_tps")
    static_low_b = _json_or_assignments(args.static_low_b, field="static_low_b")
    write_nonmonotonicity_analysis(
        args.trace_dir,
        args.stock_readme,
        args.static_tail_readme,
        args.output,
        new_trace_json=args.new_trace_json,
        baseline_tps=baseline_tps if args.baseline_tps is not None else None,
        static_low_b=static_low_b if args.static_low_b is not None else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
