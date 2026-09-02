#!/usr/bin/env python3
"""Plot T-2187 adaptive-backoff constant measurements.

Usage:
    python3 tools/plotting/plot_t2187_adaptive_consts.py \
        {grid,threads} OUT_PREFIX INPUT_JSON [INPUT_JSON ...]

Each input is one node and one repetition of schema
``izanagi-cicada-adaptive-3const-probe/v1``.  The generator always writes
``OUT_PREFIX.png``, ``OUT_PREFIX.pdf``, and
``OUT_PREFIX.provenance.json``.  Input strings are data and are never passed
to a shell.
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import json
import math
import os
import statistics
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
import numpy as np  # noqa: E402


SOURCE_SCHEMA = "izanagi-cicada-adaptive-3const-probe/v1"
PROVENANCE_SCHEMA = "izanagi-t2187-adaptive-const-figure-provenance/v1"
NOT_CERTIFIED = (
    "trace-disabled performance runs only; no serializability check was run"
)
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
STOCK = {"step_us": 100.0, "ceiling_us": 1000.0, "update_us": 10.0}
GENERATOR = Path(__file__).resolve()


class FigureDataError(RuntimeError):
    """An input or aggregation contract is invalid."""


class FigureLayoutError(FigureDataError):
    """The rendered figure violates the fail-closed layout contract."""


def _fail(message: str) -> None:
    raise FigureDataError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise FigureDataError(f"cannot hash input: {path}: {exc}") from exc
    return digest.hexdigest()


def _strict_json(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant: {value}")

    def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=no_duplicate_keys,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise FigureDataError(f"strict JSON cannot be read: {path}: {exc}") from exc
    if type(value) is not dict:
        _fail(f"JSON top level must be an object: {path}")
    return value


def _string(value: object, label: str) -> str:
    if type(value) is not str or not value:
        _fail(f"{label} must be a non-empty string")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(f"{label} must be an integer >= {minimum}")
    return value


def _number(
    value: object, label: str, *, positive: bool = False,
    lower: float | None = None, upper: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label} must be numeric")
    clean = float(value)
    if not math.isfinite(clean) or (positive and clean <= 0.0):
        _fail(f"{label} must be finite" + (" and positive" if positive else ""))
    if lower is not None and clean < lower:
        _fail(f"{label} must be >= {lower}")
    if upper is not None and clean > upper:
        _fail(f"{label} must be <= {upper}")
    return clean


def _same_number(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Continued fraction used by the regularized incomplete beta function."""
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    result = d
    for index in range(1, 301):
        twice = 2 * index
        coefficient = (
            index * (b - index) * x
            / ((qam + twice) * (a + twice))
        )
        d = 1.0 + coefficient * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + coefficient / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        result *= d * c
        coefficient = (
            -(a + index) * (qab + index) * x
            / ((a + twice) * (qap + twice))
        )
        d = 1.0 + coefficient * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + coefficient / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) < 3e-14:
            return result
    _fail("regularized incomplete beta did not converge")
    raise AssertionError("unreachable")


def _regularized_incomplete_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    factor = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return factor * _beta_continued_fraction(a, b, x) / a
    return 1.0 - factor * _beta_continued_fraction(b, a, 1.0 - x) / b


def _student_t_cdf(value: float, df: int) -> float:
    if value == 0.0:
        return 0.5
    x = df / (df + value * value)
    tail = 0.5 * _regularized_incomplete_beta(x, df / 2.0, 0.5)
    return 1.0 - tail if value > 0.0 else tail


@functools.lru_cache(maxsize=None)
def student_t_critical_975(df: int) -> float:
    """Return t_(0.975, df) from the Student t CDF, without a stats package."""
    if isinstance(df, bool) or not isinstance(df, int) or df < 1:
        _fail(f"Student t degrees of freedom must be positive: {df!r}")
    low, high = 0.0, 1.0
    while _student_t_cdf(high, df) < 0.975:
        high *= 2.0
    for _ in range(100):
        middle = (low + high) / 2.0
        if _student_t_cdf(middle, df) < 0.975:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def ci95(samples: Sequence[float]) -> tuple[float, float | None, float | None]:
    """Return sample mean, Student-t 95% CI half-width, and critical value."""
    if not samples:
        _fail("raw sample set must not be empty")
    center = statistics.fmean(samples)
    if len(samples) == 1:
        return center, None, None
    critical = student_t_critical_975(len(samples) - 1)
    half = critical * statistics.stdev(samples) / math.sqrt(len(samples))
    return center, half, critical


def _relative_half(center: float, half: float | None) -> float | None:
    if half is None:
        return None
    if center == 0.0:
        if half == 0.0:
            return 0.0
        _fail("relative CI is undefined for a zero center with nonzero half-width")
    return 100.0 * half / abs(center)


def _stock_mapping(value: object, path: Path) -> None:
    if not isinstance(value, Mapping):
        _fail(f"stock must be an object: {path}")
    observed = {
        "step_us": _number(value.get("step_us"), "stock.step_us", positive=True),
        "ceiling_us": _number(value.get("ceiling_us"), "stock.ceiling_us", positive=True),
        "update_us": _number(value.get("update_us"), "stock.update_us", positive=True),
    }
    if observed != STOCK:
        _fail(f"stock constants differ: {path}: {observed!r}")


def _parse_cell(cell: object, path: Path) -> tuple[tuple[str, str, int], dict, dict]:
    if type(cell) is not dict:
        _fail(f"cells[] entry must be an object: {path}")
    name = _string(cell.get("cell"), "cell")
    workload = _string(cell.get("workload"), "workload")
    if workload not in WORKLOADS:
        _fail(f"unknown workload {workload!r}; expected {WORKLOADS!r}")
    threads = _integer(cell.get("threads"), "threads", minimum=1)
    back_off = _integer(cell.get("back_off"), "back_off", minimum=0)
    if back_off not in (0, 1):
        _fail("back_off must be 0 or 1")
    step = _number(cell.get("step_us"), "step_us", positive=True)
    ceiling = _number(cell.get("ceiling_us"), "ceiling_us", positive=True)
    update = _number(cell.get("update_us"), "update_us", positive=True)
    stock = cell.get("is_stock_control")
    if type(stock) is not bool:
        _fail("is_stock_control must be bool")
    expected_stock = (
        _same_number(step, STOCK["step_us"])
        and _same_number(ceiling, STOCK["ceiling_us"])
        and _same_number(update, STOCK["update_us"])
        and back_off == 1
    )
    if stock is not expected_stock:
        _fail(f"is_stock_control does not match constants: {name}/{workload}")
    if (back_off == 0) != (name == "none"):
        _fail("back_off=0 must be exactly the cell named 'none'")
    if back_off == 0 and not (
        _same_number(step, STOCK["step_us"])
        and _same_number(ceiling, STOCK["ceiling_us"])
        and _same_number(update, STOCK["update_us"])
    ):
        _fail("the no-backoff cell must carry stock constant values")
    repetitions = cell.get("throughputs")
    if type(repetitions) is not list or len(repetitions) != 1:
        _fail("throughputs must contain exactly one raw value per input file")
    throughput = _number(repetitions[0], "throughputs[0]", positive=True)
    abort = _number(cell.get("abort_rate"), "abort_rate", lower=0.0, upper=1.0)
    flags = cell.get("workload_flags")
    if not isinstance(flags, Mapping):
        _fail("workload_flags must be an object")
    skew = _number(
        float(_string(flags.get("ycsb_zipf_skew"), "ycsb_zipf_skew")),
        "ycsb_zipf_skew",
        lower=0.0,
    )
    configuration = {
        "cell": name,
        "workload": workload,
        "threads": threads,
        "back_off": back_off,
        "step_us": step,
        "ceiling_us": ceiling,
        "update_us": update,
        "is_stock_control": stock,
        "workload_flags": dict(flags),
        "zipf_skew": skew,
    }
    observation = {"throughput_tps": throughput, "abort_rate": abort}
    return (name, workload, threads), configuration, observation


def _single(values: set[Any], label: str) -> Any:
    if len(values) != 1:
        _fail(f"{label} must be identical across inputs: {sorted(values)!r}")
    return next(iter(values))


def load_measurements(mode: str, input_paths: Sequence[os.PathLike[str] | str]) -> dict:
    """Strictly parse files, then aggregate raw observations by rep axis."""
    if mode not in ("grid", "threads"):
        _fail(f"unknown figure mode: {mode}")
    if not input_paths:
        _fail("at least one input JSON is required")
    paths = [Path(value).resolve() for value in input_paths]
    if len(set(paths)) != len(paths):
        _fail("the same input path was supplied more than once")
    inputs: list[dict[str, Any]] = []
    observations: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    configurations: dict[tuple[str, str, int], dict[str, Any]] = {}
    seen_reps: set[tuple[str, str, int, int]] = set()
    records_values: set[int] = set()
    extime_values: set[float] = set()
    env_values: set[str] = set()
    commit_values: set[str] = set()
    patch_values: set[str] = set()
    stage_values: set[int] = set()
    flags_by_workload: dict[str, dict[str, Any]] = {}

    for path in paths:
        document = _strict_json(path)
        if document.get("schema_version") != SOURCE_SCHEMA:
            _fail(
                f"schema_version must exactly equal {SOURCE_SCHEMA!r}: {path}"
            )
        if document.get("kind") != "performance-only-probe":
            _fail(f"kind must be performance-only-probe: {path}")
        if document.get("not_certified") != NOT_CERTIFIED:
            _fail(f"not_certified text differs: {path}")
        if document.get("use_perf") is not False:
            _fail(f"use_perf must be false: {path}")
        if _integer(document.get("reps_per_job"), "reps_per_job", minimum=1) != 1:
            _fail("reps_per_job must be exactly 1")
        rep_index = _integer(document.get("rep_index"), "rep_index", minimum=0)
        stage = _integer(document.get("stage"), "stage", minimum=1)
        if mode == "grid" and stage != 1:
            _fail("grid mode accepts stage 1 inputs only")
        if mode == "threads" and stage not in (2, 3):
            _fail("threads mode accepts stage 2 or 3 inputs only")
        _stock_mapping(document.get("stock"), path)
        records = _integer(document.get("records"), "records", minimum=1)
        extime = _number(document.get("extime_s"), "extime_s", positive=True)
        env_tag = _string(document.get("env_tag"), "env_tag")
        commit = _string(document.get("ccbench_commit"), "ccbench_commit")
        patch = _string(document.get("patch_sha256"), "patch_sha256")
        if len(patch) != 64 or any(ch not in "0123456789abcdef" for ch in patch):
            _fail("patch_sha256 must be 64 lowercase hexadecimal characters")
        pbs_jobid = _string(document.get("pbs_jobid"), "pbs_jobid")
        cells = document.get("cells")
        if type(cells) is not list or not cells:
            _fail(f"cells must be a non-empty list: {path}")
        local_keys: set[tuple[str, str, int]] = set()
        for raw_cell in cells:
            key, configuration, observation = _parse_cell(raw_cell, path)
            if key in local_keys:
                _fail(f"duplicate (cell, workload, threads) in one input: {key!r}")
            local_keys.add(key)
            rep_key = (*key, rep_index)
            if rep_key in seen_reps:
                _fail(
                    "duplicate (cell, workload, threads, rep_index): "
                    f"{rep_key!r}"
                )
            seen_reps.add(rep_key)
            previous = configurations.get(key)
            if previous is not None and previous != configuration:
                _fail(f"cell configuration changed across repetitions: {key!r}")
            configurations[key] = configuration
            workload = key[1]
            flags = configuration["workload_flags"]
            if workload in flags_by_workload and flags_by_workload[workload] != flags:
                _fail(f"workload_flags changed across cells: {workload}")
            flags_by_workload[workload] = flags
            observations.setdefault(key, []).append({
                **observation,
                "rep_index": rep_index,
                "input_path": str(path),
            })
        inputs.append({
            "path": str(path),
            "sha256": _sha256(path),
            "rep_index": rep_index,
            "stage": stage,
            "pbs_jobid": pbs_jobid,
        })
        records_values.add(records)
        extime_values.add(extime)
        env_values.add(env_tag)
        commit_values.add(commit)
        patch_values.add(patch)
        stage_values.add(stage)

    if set(flags_by_workload) != set(WORKLOADS):
        _fail(f"exactly three workloads are required: {sorted(flags_by_workload)!r}")
    aggregates = []
    for key in sorted(
        observations,
        key=lambda item: (WORKLOADS.index(item[1]), item[0], item[2]),
    ):
        rows = sorted(observations[key], key=lambda row: row["rep_index"])
        throughput_samples = [row["throughput_tps"] for row in rows]
        abort_samples = [row["abort_rate"] for row in rows]
        t_mean, t_half, t_critical = ci95(throughput_samples)
        a_mean, a_half, a_critical = ci95(abort_samples)
        if t_critical != a_critical:
            _fail("metric CI critical values unexpectedly differ")
        aggregates.append({
            **configurations[key],
            "n": len(rows),
            "rep_indices": [row["rep_index"] for row in rows],
            "throughput": {
                "samples_tps": throughput_samples,
                "mean_tps": t_mean,
                "ci95_half_tps": t_half,
                "relative_ci95_half_percent": _relative_half(t_mean, t_half),
            },
            "abort_rate": {
                "samples_fraction": abort_samples,
                "mean_fraction": a_mean,
                "ci95_half_fraction": a_half,
                "relative_ci95_half_percent": _relative_half(a_mean, a_half),
            },
            "student_t_critical_975": t_critical,
        })
    data = {
        "mode": mode,
        "inputs": inputs,
        "aggregates": aggregates,
        "measurement_conditions": {
            "stages": sorted(stage_values),
            "threads": sorted({row["threads"] for row in aggregates}),
            "records": _single(records_values, "records"),
            "extime_s": _single(extime_values, "extime_s"),
            "zipf_skew_by_workload": {
                workload: float(flags_by_workload[workload]["ycsb_zipf_skew"])
                for workload in WORKLOADS
            },
            "workload_flags": flags_by_workload,
            "rep_counts": sorted({row["n"] for row in aggregates}),
            "reps_per_job": 1,
            "env_tag": _single(env_values, "env_tag"),
        },
        "ccbench_commit": _single(commit_values, "ccbench_commit"),
        "patch_sha256": _single(patch_values, "patch_sha256"),
    }
    _validate_mode_contract(data)
    return data


def _validate_mode_contract(data: Mapping[str, Any]) -> None:
    rows = data["aggregates"]
    if data["mode"] == "grid":
        grid_rows = [row for row in rows if row["back_off"] == 1]
        threads = {row["threads"] for row in grid_rows}
        ceilings = {row["ceiling_us"] for row in grid_rows}
        if len(threads) != 1:
            _fail("grid mode requires one common thread count")
        if len(ceilings) != 1:
            _fail("grid mode requires one fixed ceiling_us")
        expected_coordinates = None
        for workload in WORKLOADS:
            selected = [
                row for row in grid_rows if row["workload"] == workload
            ]
            no_backoff = [
                row for row in rows
                if row["workload"] == workload and row["back_off"] == 0
            ]
            if len(no_backoff) != 1:
                _fail(f"grid must contain one no backoff reference: {workload}")
            reference = no_backoff[0]
            if reference["threads"] not in threads:
                _fail(f"no backoff reference has a different thread count: {workload}")
            if any(row["rep_indices"] != reference["rep_indices"] for row in selected):
                _fail(f"grid and no backoff must use the same reps: {workload}")
            coordinates = [(row["step_us"], row["update_us"]) for row in selected]
            if len(set(coordinates)) != len(coordinates):
                _fail(f"duplicate grid coordinate: {workload}")
            coordinate_set = set(coordinates)
            if expected_coordinates is None:
                expected_coordinates = coordinate_set
            elif coordinate_set != expected_coordinates:
                _fail("all workloads must have the same grid coordinates")
            steps = {x for x, _y in coordinates}
            updates = {y for _x, y in coordinates}
            if coordinate_set != {(x, y) for x in steps for y in updates}:
                _fail(f"grid must be a complete step/update product: {workload}")
            if sum(row["is_stock_control"] for row in selected) != 1:
                _fail(f"grid must contain one stock adaptive control: {workload}")
    else:
        expected_cells = None
        expected_threads = None
        for workload in WORKLOADS:
            selected = [row for row in rows if row["workload"] == workload]
            cell_names = {row["cell"] for row in selected}
            thread_values = {row["threads"] for row in selected}
            if expected_cells is None:
                expected_cells = cell_names
                expected_threads = thread_values
            elif cell_names != expected_cells or thread_values != expected_threads:
                _fail("all workloads must have the same cells and thread grid")
            for name in cell_names:
                cell_threads = {
                    row["threads"] for row in selected if row["cell"] == name
                }
                if cell_threads != thread_values:
                    _fail(f"thread grid is incomplete: {workload}/{name}")
            none_rows = [row for row in selected if row["cell"] == "none"]
            stock_rows = [row for row in selected if row["is_stock_control"]]
            if {row["threads"] for row in none_rows} != thread_values:
                _fail(f"no backoff series is incomplete: {workload}")
            if {row["threads"] for row in stock_rows} != thread_values:
                _fail(f"stock adaptive series is incomplete: {workload}")
            if len({row["cell"] for row in stock_rows}) != 1:
                _fail(f"stock adaptive must be one cell series: {workload}")


def _style() -> None:
    mpl.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "axes.titlesize": 9.0,
        "axes.labelsize": 8.0,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.20,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
    })


def _condition_subtitle(data: Mapping[str, Any]) -> str:
    conditions = data["measurement_conditions"]
    threads = ",".join(str(value) for value in conditions["threads"])
    skews = sorted(set(conditions["zipf_skew_by_workload"].values()))
    skew = str(skews[0]) if len(skews) == 1 else "/".join(map(str, skews))
    counts = conditions["rep_counts"]
    reps = str(counts[0]) if len(counts) == 1 else f"{counts[0]}-{counts[-1]}"
    return (
        f"threads {threads}; records {conditions['records']:,}; skew {skew}; "
        f"extime {conditions['extime_s']:g} s; reps {reps} per cell; "
        f"env {conditions['env_tag']}"
    )


def _caption(data: Mapping[str, Any]) -> str:
    mode_text = (
        "Step/update heat maps; panel subtitles give no backoff with its "
        "Student-t 95% CI, and each cell gives its percent of no backoff "
        "below the relative CI half-width (percentage-point difference when "
        "the no-backoff value is zero)."
        if data["mode"] == "grid"
        else "Thread scaling with Student-t 95% confidence-interval error bars."
    )
    return (
        f"{mode_text} Values are recomputed from raw per-file repetitions. "
        "For n=1, variance and a confidence interval cannot be estimated; no "
        "interval is drawn and the figure marks CI n/a. "
        "NOT CERTIFIED: trace-disabled performance runs only; no serializability "
        "check was run."
    )


def _figure_text(fig, data: Mapping[str, Any], title: str) -> None:
    fig.text(0.5, 0.985, title, ha="center", va="top", fontsize=11, fontweight="bold")
    fig.text(
        0.5, 0.952, _condition_subtitle(data),
        ha="center", va="top", fontsize=7.7,
    )
    fig.text(
        0.5, 0.012,
        "NOT CERTIFIED - trace-disabled performance only; no serializability "
        "check. Student t 95% CI; n=1: CI n/a (not drawn).",
        ha="center", va="bottom", fontsize=7.0, color="#8d1f1f",
    )


def _log_edges(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(sorted(values), dtype=float)
    if np.any(array <= 0.0):
        _fail("log-grid coordinates must be positive")
    if len(array) == 1:
        factor = math.sqrt(2.0)
        return np.asarray([array[0] / factor, array[0] * factor])
    middle = np.sqrt(array[:-1] * array[1:])
    return np.concatenate(([array[0] * array[0] / middle[0]], middle,
                           [array[-1] * array[-1] / middle[-1]]))


def _metric_center(metric: str, row: Mapping[str, Any]) -> float:
    return (
        row[metric]["mean_tps"] / 1e6
        if metric == "throughput"
        else row[metric]["mean_fraction"] * 100.0
    )


def _metric_half(metric: str, row: Mapping[str, Any]) -> float | None:
    half = row[metric][
        "ci95_half_tps" if metric == "throughput" else "ci95_half_fraction"
    ]
    if half is None:
        return None
    return half / 1e6 if metric == "throughput" else half * 100.0


def _grid_reference_title(metric: str, row: Mapping[str, Any]) -> str:
    center = _metric_center(metric, row)
    half = _metric_half(metric, row)
    if metric == "throughput":
        value_text = f"{center:.3f} M tps"
        ci_text = "95% CI n/a" if half is None else f"95% CI +/-{half:.3f} M tps"
    else:
        value_text = f"{center:.2f}%"
        ci_text = "95% CI n/a" if half is None else f"95% CI +/-{half:.2f} pp"
    return f"no backoff {value_text}\n{ci_text}"


def _grid_annotation(
    metric: str, row: Mapping[str, Any], reference: Mapping[str, Any],
) -> str:
    if metric == "throughput":
        first = f"{row[metric]['mean_tps'] / 1e6:.3f}"
    else:
        first = f"{100.0 * row[metric]['mean_fraction']:.2f}%"
    relative = row[metric]["relative_ci95_half_percent"]
    second = "CI n/a" if relative is None else f"+/-{relative:.1f}%"
    reference_center = _metric_center(metric, reference)
    if reference_center == 0.0:
        difference = _metric_center(metric, row) - reference_center
        third = f"{difference:+.2f} pp"
    else:
        ratio = 100.0 * _metric_center(metric, row) / reference_center
        third = f"{ratio:.0f}%"
    return f"{first}\n{second}\n{third}"


def _grid_figure_size(data: Mapping[str, Any]) -> tuple[float, float]:
    grid_rows = [row for row in data["aggregates"] if row["back_off"] == 1]
    step_count = len({row["step_us"] for row in grid_rows})
    update_count = len({row["update_us"] for row in grid_rows})
    # The annotations carry three independent facts and must remain readable:
    # value, relative CI half-width, and comparison with no backoff.  Reserve
    # physical space per grid coordinate instead of relying on a fixed canvas
    # that only happened to fit small fixtures.
    return max(14.4, 3.5 * step_count), max(8.8, 1.76 * update_count)


def _make_grid_figure(data: Mapping[str, Any]):
    _style()
    fig, axes = plt.subplots(
        2, 3, figsize=_grid_figure_size(data), squeeze=False,
    )
    fig.subplots_adjust(left=0.065, right=0.88, top=0.79, bottom=0.105,
                        wspace=0.31, hspace=0.62)
    metrics = (
        ("throughput", "throughput (M tps)"),
        ("abort_rate", "abort rate (%)"),
    )
    for row_index, (metric, colorbar_label) in enumerate(metrics):
        values = []
        for row in data["aggregates"]:
            if row["back_off"] != 1:
                continue
            values.append(
                _metric_center(metric, row)
            )
        normalization = Normalize(vmin=min(values), vmax=max(values))
        meshes = []
        for column, workload in enumerate(WORKLOADS):
            axis = axes[row_index, column]
            selected = [
                item for item in data["aggregates"]
                if item["workload"] == workload and item["back_off"] == 1
            ]
            reference = next(
                item for item in data["aggregates"]
                if item["workload"] == workload and item["back_off"] == 0
            )
            steps = sorted({item["step_us"] for item in selected})
            updates = sorted({item["update_us"] for item in selected})
            by_coordinate = {
                (item["step_us"], item["update_us"]): item for item in selected
            }
            matrix = np.asarray([
                [
                    by_coordinate[(step, update)][metric]["mean_tps"] / 1e6
                    if metric == "throughput"
                    else by_coordinate[(step, update)][metric]["mean_fraction"] * 100.0
                    for step in steps
                ]
                for update in updates
            ])
            x_edges = _log_edges(steps)
            y_edges = _log_edges(updates)
            mesh = axis.pcolormesh(
                x_edges, y_edges, matrix, shading="flat", cmap="viridis",
                norm=normalization, rasterized=False,
            )
            meshes.append(mesh)
            for y_index, update in enumerate(updates):
                for x_index, step in enumerate(steps):
                    item = by_coordinate[(step, update)]
                    rgba = mesh.cmap(mesh.norm(matrix[y_index, x_index]))
                    luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
                    annotation = axis.text(
                        step, update, _grid_annotation(metric, item, reference),
                        ha="center", va="center", fontsize=4.3,
                        color="black" if luminance > 0.56 else "white",
                        gid="cell-value",
                    )
                    annotation.set_clip_on(True)
                    if item["is_stock_control"]:
                        axis.add_patch(Rectangle(
                            (x_edges[x_index], y_edges[y_index]),
                            x_edges[x_index + 1] - x_edges[x_index],
                            y_edges[y_index + 1] - y_edges[y_index],
                            fill=False, edgecolor="#d62728", linewidth=2.0,
                            zorder=5,
                        ))
            axis.set_xscale("log")
            axis.set_yscale("log")
            axis.set_xticks(steps, [f"{value:g}" for value in steps])
            axis.set_yticks(updates, [f"{value:g}" for value in updates])
            axis.minorticks_off()
            axis.set_xlabel("step (us)")
            axis.set_ylabel("update interval (us)")
            title = _grid_reference_title(metric, reference)
            axis.set_title(
                f"{workload}\n{title}" if row_index == 0 else title,
                fontsize=7.8,
            )
        fig.colorbar(
            meshes[-1], ax=list(axes[row_index, :]), pad=0.025, fraction=0.035,
            label=colorbar_label,
        )
    fig.legend(
        handles=[Patch(facecolor="none", edgecolor="#d62728", linewidth=2.0,
                       label="stock adaptive")],
        loc="upper center", bbox_to_anchor=(0.5, 0.895), fontsize=7.2,
    )
    _figure_text(fig, data, "Adaptive backoff: step x update interval")
    return fig, axes


def _series_order(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    names = {row["cell"] for row in rows}
    stock_names = {row["cell"] for row in rows if row["is_stock_control"]}
    if len(stock_names) != 1:
        _fail("threads figure requires one stock adaptive cell name")
    stock_name = next(iter(stock_names))
    return ["none", stock_name] + sorted(names - {"none", stock_name})


def _series_label(name: str, rows: Sequence[Mapping[str, Any]]) -> str:
    selected = [row for row in rows if row["cell"] == name]
    if name == "none":
        return "no backoff"
    if selected and all(row["is_stock_control"] for row in selected):
        return "stock adaptive"
    return name


def _make_threads_figure(data: Mapping[str, Any]):
    _style()
    fig, axes = plt.subplots(2, 3, figsize=(12.2, 7.6), squeeze=False)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.80, bottom=0.105,
                        wspace=0.28, hspace=0.36)
    order = _series_order(data["aggregates"])
    palette = ["#555555", "#111111", "#1f77b4", "#ff7f0e", "#2ca02c",
               "#9467bd", "#8c564b", "#e377c2"]
    handles = []
    labels = []
    for column, workload in enumerate(WORKLOADS):
        workload_rows = [
            row for row in data["aggregates"] if row["workload"] == workload
        ]
        for series_index, name in enumerate(order):
            selected = sorted(
                (row for row in workload_rows if row["cell"] == name),
                key=lambda row: row["threads"],
            )
            label = _series_label(name, workload_rows)
            color = palette[series_index % len(palette)]
            linestyle = "--" if name == "none" else (
                ":" if selected[0]["is_stock_control"] else "-"
            )
            marker = "x" if name == "none" else (
                "s" if selected[0]["is_stock_control"] else "o"
            )
            for row_index, metric in enumerate(("throughput", "abort_rate")):
                axis = axes[row_index, column]
                xs = [row["threads"] for row in selected]
                ys = [
                    row[metric]["mean_tps"] / 1e6
                    if metric == "throughput"
                    else row[metric]["mean_fraction"] * 100.0
                    for row in selected
                ]
                line, = axis.plot(
                    xs, ys, marker=marker, linestyle=linestyle, color=color,
                    linewidth=1.25, markersize=4.2, label=label,
                )
                ci_rows = [row for row in selected if row[metric][
                    "ci95_half_tps" if metric == "throughput" else "ci95_half_fraction"
                ] is not None]
                if ci_rows:
                    ci_x = [row["threads"] for row in ci_rows]
                    ci_y = [
                        row[metric]["mean_tps"] / 1e6
                        if metric == "throughput"
                        else row[metric]["mean_fraction"] * 100.0
                        for row in ci_rows
                    ]
                    ci_half = [
                        row[metric]["ci95_half_tps"] / 1e6
                        if metric == "throughput"
                        else row[metric]["ci95_half_fraction"] * 100.0
                        for row in ci_rows
                    ]
                    axis.errorbar(
                        ci_x, ci_y, yerr=ci_half, fmt="none", ecolor=color,
                        elinewidth=0.9, capsize=2.5, zorder=line.get_zorder() - 0.1,
                    )
                if column == 0 and row_index == 0:
                    handles.append(line)
                    labels.append(label)
        for row_index in range(2):
            axis = axes[row_index, column]
            axis.set_xticks(data["measurement_conditions"]["threads"])
            axis.set_xlabel("threads")
            axis.set_ylabel(
                "throughput (M tps)" if row_index == 0 else "abort rate (%)"
            )
            axis.margins(x=0.06, y=0.14)
            if row_index == 0:
                axis.set_title(workload)
    if len(set(labels)) != len(labels):
        _fail(f"series display labels collide: {labels!r}")
    fig.legend(
        handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.915),
        ncol=min(4, len(labels)), fontsize=7.2,
    )
    _figure_text(fig, data, "Adaptive backoff thread scaling")
    return fig, axes


def make_figure(data: Mapping[str, Any]):
    """Create, but do not save, the selected production figure."""
    with mpl.rc_context():
        return (
            _make_grid_figure(data)
            if data["mode"] == "grid"
            else _make_threads_figure(data)
        )


def _intersection_area(left, right) -> float:
    x0 = max(left.x0, right.x0)
    y0 = max(left.y0, right.y0)
    x1 = min(left.x1, right.x1)
    y1 = min(left.y1, right.y1)
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _contains(outer, inner, tolerance: float = 0.5) -> bool:
    return (
        inner.x0 >= outer.x0 - tolerance
        and inner.y0 >= outer.y0 - tolerance
        and inner.x1 <= outer.x1 + tolerance
        and inner.y1 <= outer.y1 + tolerance
    )


def check_figure_layout(fig, axes) -> None:
    """Fail on text overlap, spine overflow, or neighboring-panel intrusion."""
    from matplotlib.text import Text

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_box = fig.bbox
    plot_axes = [axis for row in axes for axis in row]
    all_axes = list(fig.axes)
    text_boxes = []
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if box.width <= 0.0 or box.height <= 0.0:
            continue
        if not _contains(figure_box, box):
            raise FigureLayoutError(f"text leaves figure: {text.get_text()!r}")
        if text.get_gid() == "cell-value":
            if text.axes is None or not _contains(text.axes.bbox, box):
                raise FigureLayoutError(
                    f"cell annotation leaves its spine: {text.get_text()!r}"
                )
        owner = text.axes
        if owner is not None:
            for other in all_axes:
                if other is not owner and _intersection_area(box, other.bbox) > 1.0:
                    raise FigureLayoutError(
                        f"text enters neighboring panel: {text.get_text()!r}"
                    )
        text_boxes.append((text, box))
    for index, (left_text, left_box) in enumerate(text_boxes):
        for right_text, right_box in text_boxes[index + 1:]:
            if _intersection_area(left_box, right_box) > 1.0:
                raise FigureLayoutError(
                    f"text bbox overlap: {left_text.get_text()!r} / "
                    f"{right_text.get_text()!r}"
                )
    for axis in all_axes:
        tight = axis.get_tightbbox(renderer)
        if tight is not None and not _contains(figure_box, tight, tolerance=1.0):
            raise FigureLayoutError("axes decoration leaves figure spine boundary")
    if len(plot_axes) != 6:
        raise FigureLayoutError("production layout must contain six plot panels")


def _atomic_save_figure(fig, axes, prefix: Path) -> list[Path]:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    temporary: list[tuple[Path, Path]] = []
    try:
        for suffix, fmt in ((".png", "png"), (".pdf", "pdf")):
            descriptor, raw = tempfile.mkstemp(
                prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent,
            )
            os.close(descriptor)
            temp_path = Path(raw)
            destination = Path(f"{prefix}{suffix}")
            temporary.append((temp_path, destination))
            fig.savefig(temp_path, format=fmt, dpi=200)
        # Required post-save renderer-backed inspection.  Destinations become
        # visible only after the check succeeds.
        check_figure_layout(fig, axes)
        for temporary_path, destination in temporary:
            os.replace(temporary_path, destination)
        return [destination for _temporary, destination in temporary]
    finally:
        for temporary_path, _destination in temporary:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(raw, path)
    finally:
        try:
            os.unlink(raw)
        except FileNotFoundError:
            pass


def build_provenance(
    data: Mapping[str, Any], outputs: Sequence[Path], argv: Sequence[str],
) -> dict[str, Any]:
    for row in data["inputs"]:
        if _sha256(Path(row["path"])) != row["sha256"]:
            _fail(f"input changed during figure generation: {row['path']}")
    return {
        "provenance_schema_version": PROVENANCE_SCHEMA,
        "schema_version": SOURCE_SCHEMA,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "generator": {
            "path": str(GENERATOR),
            "sha256": _sha256(GENERATOR),
        },
        "mode": data["mode"],
        "not_certified": NOT_CERTIFIED,
        "inputs": data["inputs"],
        "outputs": [
            {"path": str(path.resolve()), "sha256": _sha256(path)} for path in outputs
        ],
        "env_tag": data["measurement_conditions"]["env_tag"],
        "ccbench_commit": data["ccbench_commit"],
        "patch_sha256": data["patch_sha256"],
        "pbs_jobids": [
            {
                "path": row["path"],
                "rep_index": row["rep_index"],
                "pbs_jobid": row["pbs_jobid"],
            }
            for row in data["inputs"]
        ],
        "measurement_conditions": data["measurement_conditions"],
        "ci95": {
            "center": "sample mean",
            "half_width": "t_(0.975,n-1) * sample_stdev / sqrt(n)",
            "quantile_source": (
                "Student t CDF via the regularized incomplete-beta identity; "
                "quantile obtained by bisection in this generator"
            ),
            "n_equals_1": "CI unavailable and not drawn",
        },
        "primary_values": data["aggregates"],
        "caption": _caption(data),
        "reproduction": {"argv": [str(value) for value in argv]},
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("grid", "threads"))
    parser.add_argument("out_prefix")
    parser.add_argument("input_json", nargs="+")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    figure = None
    try:
        data = load_measurements(args.mode, args.input_json)
        figure, axes = make_figure(data)
        prefix = Path(args.out_prefix).resolve()
        outputs = _atomic_save_figure(figure, axes, prefix)
        canonical_argv = [
            "python3", str(GENERATOR), args.mode, str(prefix),
            *[str(Path(value).resolve()) for value in args.input_json],
        ]
        provenance = build_provenance(data, outputs, canonical_argv)
        provenance_path = Path(f"{prefix}.provenance.json")
        _atomic_json(provenance_path, provenance)
    except Exception as exc:  # noqa: BLE001 - CLI fails closed with nonzero rc.
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if figure is not None:
            plt.close(figure)
    print(f"wrote {prefix}.png / .pdf / .provenance.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
