#!/usr/bin/env python3
"""Generate preregistered dynamic-backoff performance and diagnostic figures.

Usage:
    python3 tools/plotting/plot_dynamic_backoff.py OUT_PREFIX \
        --trace-json DIAGNOSTIC.json PERF_REP0.json ... PERF_REP6.json

The statistical endpoints, seven contrasts, and +/-3 percent practical region
are frozen by ``docs/dynamic-backoff-preregistration.md`` and intentionally
have no command-line overrides.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

try:  # Import works both as a repo module and as a directly executed script.
    from tools.plotting.plot_t2187_adaptive_consts import (  # noqa: E402
        FigureDataError,
        _atomic_json,
        _atomic_save_figure,
        _sha256,
        _strict_json,
        _style,
        check_figure_layout,
        ci95,
        student_t_critical_975,
    )
except ModuleNotFoundError:  # pragma: no cover - direct-script import route.
    from plot_t2187_adaptive_consts import (  # type: ignore[no-redef]  # noqa: E402
        FigureDataError,
        _atomic_json,
        _atomic_save_figure,
        _sha256,
        _strict_json,
        _style,
        check_figure_layout,
        ci95,
        student_t_critical_975,
    )


PERFORMANCE_SCHEMA = "izanagi-cicada-adaptive-3const-probe/v2"
DIAGNOSTIC_SCHEMA = "izanagi-dynamic-backoff-trace/v2"
PROVENANCE_SCHEMA = "izanagi-dynamic-backoff-figure-provenance/v1"
PERFORMANCE_KIND = "performance-only-probe"
DIAGNOSTIC_KIND = "diagnostic-backoff-trace"
NOT_CERTIFIED = "性能値は未認証"
GENERATOR = Path(__file__).resolve()
CCBENCH_COMMIT = "511c953"
PATCH_A_SHA256 = "9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b"

WORKLOADS = ("write-heavy", "balanced", "read-heavy")
THREADS = (6, 12, 18, 24, 30, 36, 42, 48)
TRACE_THREADS = (24, 48)
CELLS = (
    "none", "stock", "tuned", "tuned-u10240", "cw", "cw-as", "cw-as-dyn",
)
TRACE_CELLS = ("cw", "cw-as", "cw-as-dyn")

# (back_off, step_us, ceiling_us, update_us, count_window, count_cap_us,
#  step_adapt, step_min_us, step_max_us, dyn_ceiling, is_stock_control)
CELL_CONFIGS: dict[str, tuple[float | int | bool, ...]] = {
    "none": (0, 100, 1000, 10, 0, 0, 0, 100, 100, 0, False),
    "stock": (1, 100, 1000, 10, 0, 0, 0, 100, 100, 0, True),
    "tuned": (1, 1, 1000, 2560, 0, 0, 0, 100, 100, 0, False),
    "tuned-u10240": (1, 1, 1000, 10240, 0, 0, 0, 100, 100, 0, False),
    "cw": (1, 1, 1000, 2560, 10000, 10240, 0, 100, 100, 0, False),
    "cw-as": (1, 1, 1000, 2560, 10000, 10240, 1, 1, 4, 0, False),
    "cw-as-dyn": (1, 1, 1000, 2560, 10000, 10240, 1, 1, 4, 1, False),
}
CONFIG_FIELDS = (
    "back_off", "step_us", "ceiling_us", "update_us", "count_window",
    "count_cap_us", "step_adapt", "step_min_us", "step_max_us",
    "dyn_ceiling", "is_stock_control",
)

# The ordering is the preregistered H1--H7 ordering.
CONTRASTS = (
    ("H1", "cw-as-dyn", "tuned"),
    ("H2", "cw-as-dyn", "none"),
    ("H3", "cw", "tuned"),
    ("H4", "cw-as", "cw"),
    ("H5", "cw-as-dyn", "cw-as"),
    ("H6", "stock", "tuned"),
    ("H7", "tuned-u10240", "tuned"),
)
PRACTICAL_PERCENT = 3.0
MAX_TRAJECTORY_POINTS = 1024
EVENLY_SPACED_POINTS = 512
EXTREMA_BINS = 256


def _fail(message: str) -> None:
    raise FigureDataError(message)


def _require_dict(value: object, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail(f"{label} must be an object")
    return value


def _require_list(value: object, label: str) -> list[Any]:
    if type(value) is not list:
        _fail(f"{label} must be a list")
    return value


def _string(value: object, label: str) -> str:
    if type(value) is not str or not value:
        _fail(f"{label} must be a non-empty string")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or type(value) is not int or value < minimum:
        _fail(f"{label} must be an integer >= {minimum}")
    return value


def _number(
    value: object, label: str, *, positive: bool = False,
    lower: float | None = None, upper: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0.0):
        _fail(f"{label} must be finite" + (" and positive" if positive else ""))
    if lower is not None and result < lower:
        _fail(f"{label} must be >= {lower}")
    if upper is not None and result > upper:
        _fail(f"{label} must be <= {upper}")
    return result


def _hex(value: object, label: str, length: int = 64) -> str:
    result = _string(value, label)
    if len(result) != length or any(character not in "0123456789abcdef" for character in result):
        _fail(f"{label} must be {length} lowercase hexadecimal characters")
    return result


def _same_number(left: object, right: float | int) -> bool:
    if isinstance(left, bool) or not isinstance(left, (int, float)):
        return False
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)


def _sign(value: float) -> int:
    return 1 if value > 0.0 else (-1 if value < 0.0 else 0)


def _validate_patch_stack(document: Mapping[str, Any], label: str) -> list[dict[str, str]]:
    rows = _require_list(document.get("patch_stack"), f"{label}.patch_stack")
    if not rows:
        _fail(f"{label}.patch_stack must not be empty")
    parsed: list[dict[str, str]] = []
    digest_text = "izanagi-patch-stack/v1\n"
    seen_paths: set[str] = set()
    for index, raw in enumerate(rows):
        row = _require_dict(raw, f"{label}.patch_stack[{index}]")
        if set(row) != {"path", "sha256"}:
            _fail(f"{label}.patch_stack[{index}] must contain exactly path and sha256")
        path = _string(row.get("path"), f"{label}.patch_stack[{index}].path")
        sha = _hex(row.get("sha256"), f"{label}.patch_stack[{index}].sha256")
        if path in seen_paths:
            _fail(f"{label}.patch_stack contains duplicate path: {path}")
        seen_paths.add(path)
        parsed.append({"path": path, "sha256": sha})
        digest_text += f"{path} {sha}\n"
    import hashlib

    expected = hashlib.sha256(digest_text.encode("utf-8")).hexdigest()
    observed = _hex(document.get("patch_stack_sha256"), f"{label}.patch_stack_sha256")
    if observed != expected:
        _fail(f"{label}.patch_stack_sha256 does not match the ordered patch stack")
    return parsed


def _common_identity(document: Mapping[str, Any], label: str) -> dict[str, Any]:
    identity = {
        "repo_head": _hex(document.get("repo_head"), f"{label}.repo_head", 40),
        "prereg_sha256": _hex(document.get("prereg_sha256"), f"{label}.prereg_sha256"),
        "ccbench_commit": _string(document.get("ccbench_commit"), f"{label}.ccbench_commit"),
        "patch_sha256": _hex(document.get("patch_sha256"), f"{label}.patch_sha256"),
        "dynamic_patch_sha256": _hex(
            document.get("dynamic_patch_sha256"), f"{label}.dynamic_patch_sha256"
        ),
        "patch_stack": _validate_patch_stack(document, label),
        "patch_stack_sha256": _hex(
            document.get("patch_stack_sha256"), f"{label}.patch_stack_sha256"
        ),
        "records": _integer(document.get("records"), f"{label}.records", minimum=1),
        "extime_s": _number(document.get("extime_s"), f"{label}.extime_s", positive=True),
        "clocks_per_us": _number(
            document.get("clocks_per_us"), f"{label}.clocks_per_us", positive=True
        ),
    }
    if identity["records"] != 1_000_000:
        _fail(f"{label}.records must be exactly 1000000")
    if not _same_number(identity["extime_s"], 3):
        _fail(f"{label}.extime_s must be exactly 3")
    if identity["ccbench_commit"] != CCBENCH_COMMIT:
        _fail(f"{label}.ccbench_commit differs from the preregistered pin")
    if identity["patch_sha256"] != PATCH_A_SHA256:
        _fail(f"{label}.patch_sha256 differs from the preregistered patch A")
    expected_stack = [
        {
            "path": "patches/cicada-adaptive-params.patch",
            "sha256": identity["patch_sha256"],
        },
        {
            "path": "patches/cicada-adaptive-dynamic.patch",
            "sha256": identity["dynamic_patch_sha256"],
        },
    ]
    if identity["patch_stack"] != expected_stack:
        _fail(f"{label}.patch_stack must be the preregistered ordered A+B stack")
    return identity


def _validate_cell_configuration(row: Mapping[str, Any], cell: str, label: str) -> dict[str, Any]:
    expected = CELL_CONFIGS[cell]
    for field, wanted in zip(CONFIG_FIELDS, expected, strict=True):
        observed = row.get(field)
        if field == "is_stock_control":
            if type(observed) is not bool or observed is not wanted:
                _fail(f"{label}.{field} does not match preregistered cell {cell}")
        elif not _same_number(observed, wanted):
            _fail(f"{label}.{field} does not match preregistered cell {cell}")
    return {field: value for field, value in zip(CONFIG_FIELDS, expected, strict=True)}


def _parse_performance_cell(
    raw: object, *, path: Path, rep_index: int, row_index: int,
) -> tuple[tuple[str, str, int], dict[str, Any]]:
    label = f"{path}.cells[{row_index}]"
    row = _require_dict(raw, label)
    cell = _string(row.get("cell"), f"{label}.cell")
    if cell not in CELLS:
        _fail(f"{label}.cell must be one of {CELLS!r}")
    workload = _string(row.get("workload"), f"{label}.workload")
    if workload not in WORKLOADS:
        _fail(f"{label}.workload must be one of {WORKLOADS!r}")
    threads = _integer(row.get("threads"), f"{label}.threads", minimum=1)
    if threads not in THREADS:
        _fail(f"{label}.threads must be one of {THREADS!r}")
    configuration = _validate_cell_configuration(row, cell, label)
    _hex(row.get("binary_sha256"), f"{label}.binary_sha256")
    throughputs = _require_list(row.get("throughputs"), f"{label}.throughputs")
    if len(throughputs) != 1:
        _fail(f"{label}.throughputs must contain exactly one raw repetition")
    throughput = _number(throughputs[0], f"{label}.throughputs[0]", positive=True)
    median = _number(row.get("median_tps"), f"{label}.median_tps", positive=True)
    if not math.isclose(median, throughput, rel_tol=0.0, abs_tol=1e-9):
        _fail(f"{label}.median_tps must equal the sole raw throughput")
    abort = _number(row.get("abort_rate"), f"{label}.abort_rate", lower=0.0, upper=1.0)
    if _integer(
        row.get("backoff_trace_symbol_count"),
        f"{label}.backoff_trace_symbol_count",
    ) != 0:
        _fail(f"{label}.backoff_trace_symbol_count must be zero")
    if _integer(
        row.get("backoff_trace_string_count"),
        f"{label}.backoff_trace_string_count",
    ) != 0:
        _fail(f"{label}.backoff_trace_string_count must be zero")
    return (cell, workload, threads), {
        "rep_index": rep_index,
        "throughput_tps": throughput,
        "abort_rate": abort,
        "binary_sha256": row["binary_sha256"],
        **configuration,
    }


def _parse_performance(path: Path) -> dict[str, Any]:
    sha_before = _sha256(path)
    document = _strict_json(path)
    if document.get("schema_version") != PERFORMANCE_SCHEMA:
        _fail(f"schema_version must exactly equal {PERFORMANCE_SCHEMA!r}: {path}")
    if document.get("kind") != PERFORMANCE_KIND:
        _fail(f"kind must exactly equal {PERFORMANCE_KIND!r}: {path}")
    rep_index = _integer(document.get("rep_index"), f"{path}.rep_index")
    if rep_index not in range(7):
        _fail(f"{path}.rep_index must be in 0..6")
    hostname = _string(document.get("hostname"), f"{path}.hostname")
    pbs_jobid = _string(document.get("pbs_jobid"), f"{path}.pbs_jobid")
    order = _require_list(document.get("cell_order"), f"{path}.cell_order")
    expected_order = list(CELLS[rep_index:] + CELLS[:rep_index])
    if order != expected_order:
        _fail(f"{path}.cell_order must be the preregistered rotation {expected_order!r}")
    identity = _common_identity(document, str(path))
    cells = _require_list(document.get("cells"), f"{path}.cells")
    if len(cells) != len(CELLS) * len(WORKLOADS) * len(THREADS):
        _fail(f"{path}.cells must contain exactly 168 rows")
    parsed: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row_index, raw in enumerate(cells):
        key, value = _parse_performance_cell(
            raw, path=path, rep_index=rep_index, row_index=row_index,
        )
        if key in parsed:
            _fail(f"duplicate performance coordinate in {path}: {key!r}")
        parsed[key] = value
    expected = {
        (cell, workload, threads)
        for cell in CELLS for workload in WORKLOADS for threads in THREADS
    }
    if set(parsed) != expected:
        missing = sorted(expected - set(parsed))
        extra = sorted(set(parsed) - expected)
        _fail(f"performance grid differs in {path}: missing={missing!r}, extra={extra!r}")
    sha_after = _sha256(path)
    if sha_after != sha_before:
        _fail(f"input changed while it was being parsed: {path}")
    return {
        "path": str(path),
        "sha256": sha_after,
        "rep_index": rep_index,
        "hostname": hostname,
        "pbs_jobid": pbs_jobid,
        "cell_order": order,
        "identity": identity,
        "cells": parsed,
    }


def _parse_event(raw: object, label: str, expected_seq: int) -> dict[str, Any]:
    event = _require_dict(raw, label)
    seq = _integer(event.get("seq"), f"{label}.seq")
    if seq != expected_seq:
        _fail(f"{label}.seq must be contiguous from zero")
    tsc = _integer(event.get("tsc"), f"{label}.tsc")
    window_us = _number(event.get("window_us"), f"{label}.window_us", positive=True)
    window_commits = _integer(event.get("window_commits"), f"{label}.window_commits")
    trigger = _integer(event.get("trigger"), f"{label}.trigger")
    if trigger not in (0, 1, 2):
        _fail(f"{label}.trigger must be 0, 1, or 2")
    gradient = _integer(event.get("gradient_sign"), f"{label}.gradient_sign", minimum=-1)
    if gradient not in (-1, 0, 1):
        _fail(f"{label}.gradient_sign must be -1, 0, or 1")
    ceiling_changed = _integer(event.get("ceiling_changed"), f"{label}.ceiling_changed")
    parity_branch = _integer(event.get("parity_branch"), f"{label}.parity_branch")
    if ceiling_changed not in (0, 1) or parity_branch not in (0, 1):
        _fail(f"{label}.ceiling_changed and parity_branch must be 0 or 1")
    return {
        "seq": seq,
        "tsc": tsc,
        "window_us": window_us,
        "window_commits": window_commits,
        "trigger": trigger,
        "backoff_before": _number(
            event.get("backoff_before"), f"{label}.backoff_before", lower=0.0
        ),
        "backoff_after": _number(
            event.get("backoff_after"), f"{label}.backoff_after", lower=0.0
        ),
        "gradient_sign": gradient,
        "step_us": _number(event.get("step_us"), f"{label}.step_us", positive=True),
        "ceiling_us": _number(
            event.get("ceiling_us"), f"{label}.ceiling_us", positive=True
        ),
        "ceiling_changed": ceiling_changed,
        "parity_branch": parity_branch,
    }


def _directional_success(events: Sequence[Mapping[str, Any]]) -> tuple[int, int, float]:
    scored = hits = 0
    for current, following in zip(events, events[1:]):
        action = _sign(current["backoff_after"] - current["backoff_before"])
        if action == 0:
            continue
        current_rate = current["window_commits"] / current["window_us"]
        following_rate = following["window_commits"] / following["window_us"]
        scored += 1
        if action == _sign(following_rate - current_rate):
            hits += 1
    return scored, hits, hits / scored if scored else 0.0


def _parse_trace_run(raw: object, path: Path, index: int) -> tuple[tuple[str, str, int], dict[str, Any]]:
    label = f"{path}.trace_runs[{index}]"
    row = _require_dict(raw, label)
    cell = _string(row.get("cell"), f"{label}.cell")
    workload = _string(row.get("workload"), f"{label}.workload")
    threads = _integer(row.get("threads"), f"{label}.threads", minimum=1)
    if cell not in TRACE_CELLS or workload not in WORKLOADS or threads not in TRACE_THREADS:
        _fail(f"{label} is outside the exact 3 x 3 x 2 diagnostic grid")
    genome = _string(row.get("genome"), f"{label}.genome")
    binary_sha = _hex(row.get("binary_sha256"), f"{label}.binary_sha256")
    diagnostic_tps = _number(
        row.get("throughput_diagnostic_only"),
        f"{label}.throughput_diagnostic_only",
        positive=True,
    )
    raw_events = _require_list(row.get("events"), f"{label}.events")
    if not raw_events:
        _fail(f"{label}.events must not be empty")
    events = [_parse_event(event, f"{label}.events[{i}]", i) for i, event in enumerate(raw_events)]
    if any(right["tsc"] <= left["tsc"] for left, right in zip(events, events[1:])):
        _fail(f"{label}.events tsc values must be strictly increasing")
    summary = _require_dict(row.get("summary"), f"{label}.summary")
    updates = _integer(summary.get("updates"), f"{label}.summary.updates")
    retained = _integer(summary.get("retained"), f"{label}.summary.retained")
    dropped = _integer(summary.get("dropped"), f"{label}.summary.dropped")
    if updates != retained + dropped or retained != len(events) or dropped != 0:
        _fail(f"{label}.summary must report all events retained and none dropped")
    directional = _require_dict(row.get("directional_success"), f"{label}.directional_success")
    scored = _integer(directional.get("scored"), f"{label}.directional_success.scored")
    hits = _integer(directional.get("hits"), f"{label}.directional_success.hits")
    rate = _number(
        directional.get("rate"), f"{label}.directional_success.rate",
        lower=0.0, upper=1.0,
    )
    expected_scored, expected_hits, expected_rate = _directional_success(events)
    if (scored, hits) != (expected_scored, expected_hits) or not math.isclose(
        rate, expected_rate, rel_tol=0.0, abs_tol=1e-12,
    ):
        _fail(f"{label}.directional_success does not match the event sequence")
    return (cell, workload, threads), {
        "cell": cell,
        "workload": workload,
        "threads": threads,
        "genome": genome,
        "binary_sha256": binary_sha,
        "throughput_diagnostic_only": diagnostic_tps,
        "events": events,
        "summary": {"updates": updates, "retained": retained, "dropped": dropped},
        "directional_success": {"scored": scored, "hits": hits, "rate": rate},
    }


def _parse_diagnostic(path: Path) -> dict[str, Any]:
    sha_before = _sha256(path)
    document = _strict_json(path)
    if document.get("schema_version") != DIAGNOSTIC_SCHEMA:
        _fail(f"schema_version must exactly equal {DIAGNOSTIC_SCHEMA!r}: {path}")
    if document.get("kind") != DIAGNOSTIC_KIND:
        _fail(f"kind must exactly equal {DIAGNOSTIC_KIND!r}: {path}")
    if document.get("headline_eligible") is not False:
        _fail(f"{path}.headline_eligible must be false")
    hostname = _string(document.get("hostname"), f"{path}.hostname")
    pbs_jobid = _string(document.get("pbs_jobid"), f"{path}.pbs_jobid")
    identity = _common_identity(document, str(path))
    raw_runs = _require_list(document.get("trace_runs"), f"{path}.trace_runs")
    if len(raw_runs) != len(TRACE_CELLS) * len(WORKLOADS) * len(TRACE_THREADS):
        _fail(f"{path}.trace_runs must contain exactly 18 runs")
    runs: dict[tuple[str, str, int], dict[str, Any]] = {}
    for index, raw in enumerate(raw_runs):
        key, value = _parse_trace_run(raw, path, index)
        if key in runs:
            _fail(f"duplicate diagnostic coordinate in {path}: {key!r}")
        runs[key] = value
    expected = {
        (cell, workload, threads)
        for cell in TRACE_CELLS for workload in WORKLOADS for threads in TRACE_THREADS
    }
    if set(runs) != expected:
        _fail("diagnostic grid is incomplete")
    sha_after = _sha256(path)
    if sha_after != sha_before:
        _fail(f"input changed while it was being parsed: {path}")
    return {
        "path": str(path),
        "sha256": sha_after,
        "hostname": hostname,
        "pbs_jobid": pbs_jobid,
        "identity": identity,
        "runs": runs,
    }


def _aggregate_performance(performance: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for workload in WORKLOADS:
        for threads in THREADS:
            for cell in CELLS:
                key = (cell, workload, threads)
                observations = [document["cells"][key] for document in performance]
                throughput_samples = [row["throughput_tps"] for row in observations]
                abort_samples = [row["abort_rate"] for row in observations]
                throughput_mean, throughput_half, throughput_critical = ci95(throughput_samples)
                abort_mean, abort_half, abort_critical = ci95(abort_samples)
                if throughput_critical != abort_critical:
                    _fail("throughput and abort-rate t critical values differ")
                if throughput_critical != student_t_critical_975(len(observations) - 1):
                    _fail("performance CI does not use the Student t critical value")
                rows.append({
                    "cell": cell,
                    "workload": workload,
                    "threads": threads,
                    **{field: value for field, value in zip(
                        CONFIG_FIELDS, CELL_CONFIGS[cell], strict=True,
                    )},
                    "rep_indices": [row["rep_index"] for row in observations],
                    "n": len(observations),
                    "throughput": {
                        "samples_tps": throughput_samples,
                        "mean_tps": throughput_mean,
                        "ci95_lower_tps": (
                            None if throughput_half is None else throughput_mean - throughput_half
                        ),
                        "ci95_upper_tps": (
                            None if throughput_half is None else throughput_mean + throughput_half
                        ),
                    },
                    "abort_rate": {
                        "samples_fraction": abort_samples,
                        "mean_fraction": abort_mean,
                        "ci95_lower_fraction": (
                            None if abort_half is None else abort_mean - abort_half
                        ),
                        "ci95_upper_fraction": (
                            None if abort_half is None else abort_mean + abort_half
                        ),
                    },
                    "student_t_critical_975": throughput_critical,
                })
    return rows


def _point_verdict(lower_percent: float, upper_percent: float) -> str:
    if lower_percent > PRACTICAL_PERCENT:
        return "実用優越"
    if upper_percent < -PRACTICAL_PERCENT:
        return "実用劣化"
    if lower_percent >= -PRACTICAL_PERCENT and upper_percent <= PRACTICAL_PERCENT:
        return "等価"
    if lower_percent > -PRACTICAL_PERCENT:
        return "非劣性"
    return "inconclusive"


def _contrast_points(performance: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    contrasts: list[dict[str, Any]] = []
    for hypothesis, numerator, denominator in CONTRASTS:
        points = []
        for workload in WORKLOADS:
            for threads in THREADS:
                samples = []
                for document in performance:
                    top = document["cells"][(numerator, workload, threads)]["throughput_tps"]
                    bottom = document["cells"][(denominator, workload, threads)]["throughput_tps"]
                    samples.append(math.log(top / bottom))
                center, half, critical = ci95(samples)
                if critical != student_t_critical_975(len(samples) - 1):
                    _fail("contrast CI does not use the Student t critical value")
                if half is None:
                    lower_log = upper_log = None
                    lower_percent = upper_percent = None
                    verdict = "inconclusive"
                else:
                    lower_log, upper_log = center - half, center + half
                    lower_percent = 100.0 * math.expm1(lower_log)
                    upper_percent = 100.0 * math.expm1(upper_log)
                    verdict = _point_verdict(lower_percent, upper_percent)
                points.append({
                    "workload": workload,
                    "threads": threads,
                    "n": len(samples),
                    "log_ratio_samples": samples,
                    "mean_log_ratio": center,
                    "ci95_lower_log_ratio": lower_log,
                    "ci95_upper_log_ratio": upper_log,
                    "mean_percent": 100.0 * math.expm1(center),
                    "ci95_lower_percent": lower_percent,
                    "ci95_upper_percent": upper_percent,
                    "student_t_critical_975": critical,
                    "verdict": verdict,
                })
        contrasts.append({
            "hypothesis": hypothesis,
            "numerator": numerator,
            "denominator": denominator,
            "points": points,
        })
    return contrasts


def _all_noninferior(points: Sequence[Mapping[str, Any]]) -> bool:
    return all(point["ci95_lower_percent"] > -PRACTICAL_PERCENT for point in points)


def _robust_benefit(points: Sequence[Mapping[str, Any]]) -> str:
    endpoints = [
        point for point in points
        if point["threads"] == 48 and point["workload"] in ("write-heavy", "balanced")
    ]
    if _all_noninferior(points) and all(
        point["ci95_lower_percent"] > PRACTICAL_PERCENT for point in endpoints
    ):
        return "accepted"
    if any(point["ci95_upper_percent"] < -PRACTICAL_PERCENT for point in points) or any(
        point["ci95_upper_percent"] <= PRACTICAL_PERCENT for point in endpoints
    ):
        return "rejected"
    return "inconclusive"


def _all_noninferiority(points: Sequence[Mapping[str, Any]]) -> str:
    if _all_noninferior(points):
        return "accepted"
    if any(point["ci95_upper_percent"] < -PRACTICAL_PERCENT for point in points):
        return "rejected"
    return "inconclusive"


def _all_equivalent(points: Sequence[Mapping[str, Any]]) -> str:
    if all(
        point["ci95_lower_percent"] >= -PRACTICAL_PERCENT
        and point["ci95_upper_percent"] <= PRACTICAL_PERCENT
        for point in points
    ):
        return "accepted"
    if any(
        point["ci95_lower_percent"] > PRACTICAL_PERCENT
        or point["ci95_upper_percent"] < -PRACTICAL_PERCENT
        for point in points
    ):
        return "rejected"
    return "inconclusive"


def _all_degraded(points: Sequence[Mapping[str, Any]]) -> str:
    if all(point["ci95_upper_percent"] < -PRACTICAL_PERCENT for point in points):
        return "accepted"
    if any(point["ci95_lower_percent"] > -PRACTICAL_PERCENT for point in points):
        return "rejected"
    return "inconclusive"


def _hypotheses(contrasts: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    by_name = {row["hypothesis"]: row["points"] for row in contrasts}
    return {
        "H1": _robust_benefit(by_name["H1"]),
        "H2": _all_noninferiority([
            point for point in by_name["H2"] if point["workload"] == "read-heavy"
        ]),
        "H3": _robust_benefit(by_name["H3"]),
        "H4": _robust_benefit(by_name["H4"]),
        "H5": _all_equivalent(by_name["H5"]),
        "H6": _all_degraded([
            point for point in by_name["H6"] if point["threads"] == 48
        ]),
        "H7": _all_equivalent(by_name["H7"]),
    }


def load_inputs(
    performance_paths: Sequence[os.PathLike[str] | str],
    trace_path: os.PathLike[str] | str,
) -> dict[str, Any]:
    """Validate the exact 7+1 contract and compute frozen aggregations."""
    if len(performance_paths) != 7:
        _fail("exactly seven performance JSON files are required")
    resolved_performance = [Path(value).resolve() for value in performance_paths]
    resolved_trace = Path(trace_path).resolve()
    all_paths = [*resolved_performance, resolved_trace]
    if len(set(all_paths)) != 8:
        _fail("all eight input paths must be distinct")
    performance = [_parse_performance(path) for path in resolved_performance]
    performance.sort(key=lambda row: row["rep_index"])
    if [row["rep_index"] for row in performance] != list(range(7)):
        _fail("performance rep_index values must contain 0..6 exactly once")
    if len({row["hostname"] for row in performance}) != 7:
        _fail("the seven performance blocks must have distinct hostnames")
    if len({row["pbs_jobid"] for row in performance}) != 7:
        _fail("the seven performance blocks must have distinct pbs_jobid values")
    diagnostic = _parse_diagnostic(resolved_trace)
    identities = [row["identity"] for row in performance] + [diagnostic["identity"]]
    if any(identity != identities[0] for identity in identities[1:]):
        _fail("identity fields must be identical across all eight inputs")
    aggregates = _aggregate_performance(performance)
    contrasts = _contrast_points(performance)
    return {
        "performance": performance,
        "diagnostic": diagnostic,
        "identity": identities[0],
        "aggregates": aggregates,
        "contrasts": contrasts,
        "hypotheses": _hypotheses(contrasts),
    }


def _measurement_subtitle(data: Mapping[str, Any]) -> str:
    identity = data["identity"]
    return (
        f"Silo/YCSB; threads 6-48; records {identity['records']:,}; "
        f"extime {identity['extime_s']:g} s; 7 node blocks; zipf 0.9"
    )


def _figure_heading(fig, title: str, subtitle: str, footer: str) -> None:
    fig.text(0.5, 0.988, title, ha="center", va="top", fontsize=11, fontweight="bold")
    fig.text(0.5, 0.956, subtitle, ha="center", va="top", fontsize=7.7)
    fig.text(0.5, 0.014, footer, ha="center", va="bottom", fontsize=6.9)


def _aggregate_map(data: Mapping[str, Any]) -> dict[tuple[str, str, int], Mapping[str, Any]]:
    return {
        (row["cell"], row["workload"], row["threads"]): row
        for row in data["aggregates"]
    }


def _freeze_ticks_inside_limits(axis) -> None:
    """Keep auto-locator sentinel ticks from escaping a fail-closed canvas."""
    x0, x1 = sorted(axis.get_xlim())
    y0, y1 = sorted(axis.get_ylim())
    axis.set_xticks([tick for tick in axis.get_xticks() if x0 <= tick <= x1])
    axis.set_yticks([tick for tick in axis.get_yticks() if y0 <= tick <= y1])


def make_thread_figure(data: Mapping[str, Any]):
    """Return the preregistered 2 x 3 descriptive performance figure."""
    _style()
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 8.1), squeeze=False)
    fig.subplots_adjust(left=0.080, right=0.985, top=0.79, bottom=0.105,
                        wspace=0.27, hspace=0.38)
    by_key = _aggregate_map(data)
    colors = {
        "none": "#111111", "stock": "#7f7f7f", "tuned": "#1f4e79",
        "tuned-u10240": "#e67e22", "cw": "#2ca02c", "cw-as": "#9467bd",
        "cw-as-dyn": "#d62728",
    }
    styles = {
        "none": ("--", "x", 2.2), "stock": (":", "s", 1.2),
        "tuned": ("-.", "D", 2.2), "tuned-u10240": ("-", "v", 1.2),
        "cw": ("-", "o", 1.2), "cw-as": ("-", "^", 1.2),
        "cw-as-dyn": ("-", "P", 1.35),
    }
    labels = {
        "none": "none (baseline)", "stock": "stock (positive control)",
        "tuned": "tuned (baseline)", "tuned-u10240": "tuned-u10240",
        "cw": "cw", "cw-as": "cw-as", "cw-as-dyn": "cw-as-dyn",
    }
    handles = []
    for column, workload in enumerate(WORKLOADS):
        for cell in CELLS:
            rows = [by_key[(cell, workload, threads)] for threads in THREADS]
            linestyle, marker, linewidth = styles[cell]
            for row_index, metric in enumerate(("throughput", "abort_rate")):
                axis = axes[row_index, column]
                centers = [
                    row[metric]["mean_tps"] / 1e6
                    if metric == "throughput"
                    else 100.0 * row[metric]["mean_fraction"]
                    for row in rows
                ]
                lows = [
                    row[metric]["ci95_lower_tps"] / 1e6
                    if metric == "throughput"
                    else 100.0 * row[metric]["ci95_lower_fraction"]
                    for row in rows
                ]
                highs = [
                    row[metric]["ci95_upper_tps"] / 1e6
                    if metric == "throughput"
                    else 100.0 * row[metric]["ci95_upper_fraction"]
                    for row in rows
                ]
                line, = axis.plot(
                    THREADS, centers, color=colors[cell], linestyle=linestyle,
                    marker=marker, linewidth=linewidth, markersize=3.9,
                    label=labels[cell],
                )
                axis.errorbar(
                    THREADS, centers,
                    yerr=[
                        [center - low for center, low in zip(centers, lows)],
                        [high - center for center, high in zip(centers, highs)],
                    ],
                    fmt="none", ecolor=colors[cell], elinewidth=0.75,
                    capsize=2.0, zorder=line.get_zorder() - 0.1,
                )
                if column == 0 and row_index == 0:
                    handles.append(line)
        for row_index in range(2):
            axis = axes[row_index, column]
            axis.set_xticks(THREADS)
            axis.set_xlabel("threads")
            axis.set_ylabel("throughput (M tps)" if row_index == 0 else "abort rate (%)")
            axis.margins(x=0.04, y=0.14)
            if row_index == 0:
                axis.set_title(workload)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.905),
               ncol=4, fontsize=7.1)
    _figure_heading(
        fig,
        "Cicada-style dynamic adaptive backoff on Silo: thread axis",
        _measurement_subtitle(data),
        "Student t 95% CI from paired node blocks; n=1: CI unavailable. "
        "PERFORMANCE VALUES NOT CERTIFIED.",
    )
    return fig, axes


def _point_label(point: Mapping[str, Any]) -> str:
    short = {"write-heavy": "write", "balanced": "balanced", "read-heavy": "read"}
    return f"{short[point['workload']]} / {point['threads']:02d}"


def make_contrasts_figure(data: Mapping[str, Any]):
    """Return the seven-panel paired-log-ratio forest plot."""
    _style()
    fig, axes = plt.subplots(4, 2, figsize=(13.8, 16.5), squeeze=False)
    fig.subplots_adjust(left=0.105, right=0.98, top=0.925, bottom=0.055,
                        wspace=0.27, hspace=0.31)
    flat = list(axes.flat)
    for index, contrast in enumerate(data["contrasts"]):
        axis = flat[index]
        points = contrast["points"]
        y = np.arange(len(points), dtype=float)
        centers = np.asarray([point["mean_percent"] for point in points])
        lows = np.asarray([point["ci95_lower_percent"] for point in points])
        highs = np.asarray([point["ci95_upper_percent"] for point in points])
        axis.axvspan(-PRACTICAL_PERCENT, PRACTICAL_PERCENT, color="#d9ead3",
                     alpha=0.75, zorder=0)
        axis.axvline(0.0, color="#555555", linewidth=0.8, zorder=1)
        axis.errorbar(
            centers, y, xerr=np.vstack((centers - lows, highs - centers)),
            fmt="o", color="#1f4e79", ecolor="#1f4e79", markersize=3.0,
            elinewidth=0.8, capsize=1.8, zorder=2,
        )
        axis.set_yticks(y, [_point_label(point) for point in points], fontsize=5.4)
        axis.invert_yaxis()
        axis.set_xlabel("paired throughput difference (%)")
        axis.set_title(
            f"{contrast['hypothesis']}  {contrast['numerator']} / {contrast['denominator']}",
            fontsize=8.3,
        )
        axis.margins(x=0.10, y=0.025)
        _freeze_ticks_inside_limits(axis)
    flat[-1].set_visible(False)
    _figure_heading(
        fig,
        "Cicada-style adaptive backoff on Silo: paired log-ratio contrasts",
        _measurement_subtitle(data) + "; shaded practical-equivalence region +/-3%",
        "Points are 100*(exp(mean log ratio)-1); bars are Student t 95% CI. "
        "PERFORMANCE VALUES NOT CERTIFIED.",
    )
    # The shared checker inspects every fig.axes entry.  Its legacy public
    # contract also requires a six-axis matrix argument, so supply six real
    # panels while the seventh remains covered through fig.axes inspection.
    layout_axes = np.asarray(flat[:6], dtype=object).reshape(2, 3)
    return fig, layout_axes


def _decimate(events: Sequence[Mapping[str, Any]], clocks_per_us: float) -> dict[str, Any]:
    elapsed = np.asarray([
        (event["tsc"] - events[0]["tsc"]) / clocks_per_us / 1_000_000.0
        for event in events
    ])
    backoff = np.asarray([event["backoff_after"] for event in events])
    if len(events) <= MAX_TRAJECTORY_POINTS:
        indices = np.arange(len(events), dtype=int)
    else:
        chosen = set(np.linspace(
            0, len(events) - 1, EVENLY_SPACED_POINTS, dtype=int,
        ).tolist())
        edges = np.linspace(0, len(events), EXTREMA_BINS + 1, dtype=int)
        for left, right in zip(edges, edges[1:]):
            if right <= left:
                continue
            segment = backoff[left:right]
            chosen.add(left + int(np.argmin(segment)))
            chosen.add(left + int(np.argmax(segment)))
        indices = np.asarray(sorted(chosen), dtype=int)
    return {
        "raw_points": len(events),
        "plotted_points": len(indices),
        "elapsed_seconds": elapsed[indices].tolist(),
        "backoff_us": backoff[indices].tolist(),
    }


def _diagnostic_values(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    clocks = data["identity"]["clocks_per_us"]
    rows = []
    for workload in WORKLOADS:
        for cell in TRACE_CELLS:
            for threads in TRACE_THREADS:
                run = data["diagnostic"]["runs"][(cell, workload, threads)]
                rows.append({
                    "cell": cell,
                    "workload": workload,
                    "threads": threads,
                    "summary": run["summary"],
                    "directional_success": run["directional_success"],
                    "trajectory": _decimate(run["events"], clocks),
                })
    return rows


def make_diagnostic_figure(data: Mapping[str, Any]):
    """Return trajectories and one-run directional-success rates."""
    _style()
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 8.1), squeeze=False)
    fig.subplots_adjust(left=0.080, right=0.985, top=0.79, bottom=0.115,
                        wspace=0.27, hspace=0.40)
    colors = {"cw": "#2ca02c", "cw-as": "#9467bd", "cw-as-dyn": "#d62728"}
    line_styles = {24: "--", 48: "-"}
    markers = {24: "o", 48: "^"}
    handles = []
    values = _diagnostic_values(data)
    by_key = {(row["cell"], row["workload"], row["threads"]): row for row in values}
    for column, workload in enumerate(WORKLOADS):
        top = axes[0, column]
        bottom = axes[1, column]
        for cell in TRACE_CELLS:
            for threads in TRACE_THREADS:
                row = by_key[(cell, workload, threads)]
                trajectory = row["trajectory"]
                line, = top.plot(
                    trajectory["elapsed_seconds"], trajectory["backoff_us"],
                    color=colors[cell], linestyle=line_styles[threads],
                    linewidth=1.0, label=f"{cell} / {threads}",
                )
                if column == 0:
                    handles.append(line)
        for threads in TRACE_THREADS:
            rates = [
                100.0 * by_key[(cell, workload, threads)]["directional_success"]["rate"]
                for cell in TRACE_CELLS
            ]
            bottom.plot(
                range(len(TRACE_CELLS)), rates, color="#444444",
                linestyle="none", marker=markers[threads], markersize=5.0,
                label=f"threads {threads}",
            )
        top.set_title(workload)
        top.set_xlabel("elapsed time (s)")
        top.set_ylabel("Backoff_ (us)")
        top.margins(x=0.02, y=0.10)
        bottom.set_xticks(range(len(TRACE_CELLS)), TRACE_CELLS)
        bottom.set_ylabel("directional success (%)")
        bottom.set_ylim(-4.0, 104.0)
        bottom.set_xlabel("diagnostic arm")
        _freeze_ticks_inside_limits(top)
        _freeze_ticks_inside_limits(bottom)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.905),
               ncol=3, fontsize=7.1)
    _figure_heading(
        fig,
        "Cicada-style dynamic adaptive backoff on Silo: diagnostic trajectories",
        _measurement_subtitle(data) + "; trace threads 24/48",
        "Diagnostic build; instrumented-system trajectories; headline-ineligible. "
        "Directional success is n=1, so no CI is drawn.",
    )
    return fig, axes


def _captions() -> dict[str, str]:
    return {
        "thread_axis": (
            "Seven trace-disabled performance series; none and tuned are the two "
            "baselines, stock is a positive control. Student t 95% CI; n=1 has no CI."
        ),
        "contrasts": (
            "Within-node log throughput ratios with Student t 95% CI and the frozen "
            "+/-3% practical-equivalence region."
        ),
        "diagnostic": "診断 build 由来・計装系の軌跡・headline 不適格。方向的中率は n=1 なので CI なし。",
    }


def _input_records(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "role": "performance",
            "path": document["path"],
            "sha256": document["sha256"],
            "rep_index": document["rep_index"],
            "hostname": document["hostname"],
            "pbs_jobid": document["pbs_jobid"],
        }
        for document in data["performance"]
    ]
    diagnostic = data["diagnostic"]
    rows.append({
        "role": "diagnostic",
        "path": diagnostic["path"],
        "sha256": diagnostic["sha256"],
        "hostname": diagnostic["hostname"],
        "pbs_jobid": diagnostic["pbs_jobid"],
    })
    return rows


def _measurement_conditions(data: Mapping[str, Any]) -> dict[str, Any]:
    identity = data["identity"]
    return {
        "protocol": "Silo",
        "algorithm_origin": "Cicada-style adaptive backoff",
        "workloads": list(WORKLOADS),
        "threads": list(THREADS),
        "diagnostic_threads": list(TRACE_THREADS),
        "records": identity["records"],
        "extime_s": identity["extime_s"],
        "clocks_per_us": identity["clocks_per_us"],
        "zipf_skew": 0.9,
        "rmw": 0,
        "max_ope": 10,
        "performance_blocks": 7,
        "performance_repetitions_per_block": 1,
        "diagnostic_repetitions": 1,
    }


def build_provenance(
    data: Mapping[str, Any], staged_outputs: Sequence[tuple[Path, Path]],
    argv: Sequence[str],
) -> dict[str, Any]:
    """Build provenance after rechecking immutable inputs and staged outputs."""
    for row in _input_records(data):
        if _sha256(Path(row["path"])) != row["sha256"]:
            _fail(f"input changed during figure generation: {row['path']}")
    identity = data["identity"]
    return {
        "provenance_schema_version": PROVENANCE_SCHEMA,
        "performance_schema_version": PERFORMANCE_SCHEMA,
        "diagnostic_schema_version": DIAGNOSTIC_SCHEMA,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "generator": {"path": str(GENERATOR), "sha256": _sha256(GENERATOR)},
        "inputs": _input_records(data),
        "outputs": [
            {"path": str(destination), "sha256": _sha256(staged)}
            for staged, destination in staged_outputs
        ],
        "repo_head": identity["repo_head"],
        "prereg_sha256": identity["prereg_sha256"],
        "ccbench_commit": identity["ccbench_commit"],
        "patch_sha256": identity["patch_sha256"],
        "dynamic_patch_sha256": identity["dynamic_patch_sha256"],
        "patch_stack": identity["patch_stack"],
        "patch_stack_sha256": identity["patch_stack_sha256"],
        "pbs_jobids": [
            {"path": row["path"], "pbs_jobid": row["pbs_jobid"]}
            for row in _input_records(data)
        ],
        "hostnames": [
            {"path": row["path"], "hostname": row["hostname"]}
            for row in _input_records(data)
        ],
        "measurement_conditions": _measurement_conditions(data),
        "ci95": {
            "center": "sample mean",
            "formula": "t_(0.975,n-1) * sample_stdev / sqrt(n)",
            "contrast_scale": "within-block ln(TPS_a/TPS_b), transformed by 100*(exp(x)-1)",
            "practical_equivalence_percent": [-PRACTICAL_PERCENT, PRACTICAL_PERCENT],
            "n_equals_1": "CI unavailable and not drawn",
        },
        "performance_values_certified": False,
        "performance_certification_notice": NOT_CERTIFIED,
        "performance_aggregates": data["aggregates"],
        "contrasts": data["contrasts"],
        "hypotheses": data["hypotheses"],
        "diagnostic": {
            "headline_eligible": False,
            "throughput_plotted": False,
            "decimation": {
                "rule": "union of fixed evenly spaced indices and per-bin backoff minima/maxima",
                "maximum_points": MAX_TRAJECTORY_POINTS,
                "evenly_spaced_points": EVENLY_SPACED_POINTS,
                "extrema_bins": EXTREMA_BINS,
            },
            "values": _diagnostic_values(data),
        },
        "captions": _captions(),
        "reproduction": {"argv": [str(value) for value in argv]},
    }


def _publish_transaction(staged_outputs: Sequence[tuple[Path, Path]], backup_dir: Path) -> None:
    backups: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for _staged, destination in staged_outputs:
            if destination.exists():
                backup = backup_dir / f"backup-{len(backups)}"
                os.replace(destination, backup)
                backups.append((backup, destination))
        for staged, destination in staged_outputs:
            os.replace(staged, destination)
            published.append(destination)
    except Exception:
        for destination in published:
            try:
                destination.unlink()
            except FileNotFoundError:
                pass
        for backup, destination in backups:
            if backup.exists():
                os.replace(backup, destination)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_prefix")
    parser.add_argument("--trace-json", required=True)
    parser.add_argument("performance_json", nargs="+")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    figures = []
    try:
        data = load_inputs(args.performance_json, args.trace_json)
        thread_figure = make_thread_figure(data)
        contrast_figure = make_contrasts_figure(data)
        diagnostic_figure = make_diagnostic_figure(data)
        figures = [thread_figure, contrast_figure, diagnostic_figure]

        # All real figures pass the bbox contract before any output path is made visible.
        for figure, axes in figures:
            check_figure_layout(figure, axes)

        prefix = Path(args.out_prefix).resolve()
        prefix.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=f".{prefix.name}.stage-", dir=prefix.parent,
        ) as raw_stage:
            stage = Path(raw_stage)
            staged_outputs: list[tuple[Path, Path]] = []
            for suffix, (figure, axes) in zip(
                ("thread-axis", "contrasts", "diagnostic"), figures, strict=True,
            ):
                stage_prefix = stage / suffix
                staged = _atomic_save_figure(figure, axes, stage_prefix)
                destinations = [
                    Path(f"{prefix}-{suffix}.png"), Path(f"{prefix}-{suffix}.pdf")
                ]
                staged_outputs.extend(zip(staged, destinations, strict=True))

            canonical_argv = [
                "python3", str(GENERATOR), str(prefix), "--trace-json",
                str(Path(args.trace_json).resolve()),
                *[str(Path(value).resolve()) for value in args.performance_json],
            ]
            provenance = build_provenance(data, staged_outputs, canonical_argv)
            staged_provenance = stage / "provenance.json"
            _atomic_json(staged_provenance, provenance)
            final_provenance = Path(f"{prefix}.provenance.json")
            publication = [*staged_outputs, (staged_provenance, final_provenance)]
            _publish_transaction(publication, stage)
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary.
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        for figure, _axes in figures:
            plt.close(figure)
    print(
        f"wrote {prefix}-thread-axis.{{png,pdf}}, {prefix}-contrasts.{{png,pdf}}, "
        f"{prefix}-diagnostic.{{png,pdf}}, and {prefix}.provenance.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
