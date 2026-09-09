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
from typing import Sequence

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
    return {
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


def write_nonmonotonicity_analysis(
    trace_dir: Path,
    stock_readme: Path,
    static_tail_readme: Path,
    output: Path,
) -> dict:
    """Analyze the inputs and create ``output`` without replacing any file."""
    if not isinstance(output, Path):
        _fail("output must be a Path")
    if output.exists():
        raise FileExistsError(output)
    result = analyze_nonmonotonicity(trace_dir, stock_readme, static_tail_readme)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reanalyze recorded adaptive-backoff artifacts for T-2188."
    )
    parser.add_argument("--trace-dir", required=True, type=Path)
    parser.add_argument("--stock-readme", required=True, type=Path)
    parser.add_argument("--static-tail-readme", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    write_nonmonotonicity_analysis(
        args.trace_dir,
        args.stock_readme,
        args.static_tail_readme,
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
