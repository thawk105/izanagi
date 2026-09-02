#!/usr/bin/env python3
"""Render T-2216 prediction, residence, or mechanism figures.

Usage:
    python3 tools/plotting/plot_t2216_backoff_walk.py \
        {prediction,residence,mechanism} OUT_PREFIX \
        MODEL_JSON MEASURED_JSON BACKOFF_COPY

The model and measurement documents retain raw repetitions.  Every displayed
mean and Student-t 95% interval is recomputed from those repetitions here.
The generator writes ``OUT_PREFIX.png``, ``OUT_PREFIX.pdf``, and
``OUT_PREFIX.provenance.json`` atomically after a renderer-backed layout check.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import tempfile
from typing import Any, Mapping, Sequence

import matplotlib as mpl

mpl.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


MODEL_SCHEMA = "izanagi-t2216-backoff-walk/v1"
PROVENANCE_SCHEMA = "izanagi-t2216-backoff-walk-figure-provenance/v1"
BACKOFF_COPY_SHA256 = "3e9f548507200532c79b14b94389abbfd4f87c7c03addde0099740f2df3d8cd7"
NOT_CERTIFIED_FRAGMENT = "trace-disabled performance measurements only"
WORKLOAD = "write-heavy"
UPDATES = (10, 40, 160, 640, 2560)
RESIDENCE_STEPS = (0.5, 1.0, 5.0, 25.0, 100.0)
GENERATOR = Path(__file__).resolve()

# t_(0.975, df), sufficient for observed n<=7 and frozen model n<=32.
_T975 = (
    None,
    12.7062047364, 4.30265272975, 3.18244630528, 2.7764451052,
    2.57058183564, 2.44691184879, 2.36462425101, 2.3060041352,
    2.2621571628, 2.22813885196, 2.20098516008, 2.17881282966,
    2.16036865646, 2.14478668792, 2.13144954556, 2.11990529922,
    2.10981557783, 2.10092204024, 2.09302405441, 2.08596344727,
    2.07961384473, 2.0738730679, 2.06865761042, 2.06389856163,
    2.05953855275, 2.05552943864, 2.05183051648, 2.0484071418,
    2.04522964213, 2.0422724563, 2.0395134464,
)


class FigureDataError(RuntimeError):
    """An input or raw-repetition contract is invalid."""


class FigureLayoutError(FigureDataError):
    """A rendered figure violates the fail-closed layout contract."""


def _fail(message: str) -> None:
    raise FigureDataError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise FigureDataError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def _strict_json(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant: {value}")

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=reject_constant,
            object_pairs_hook=no_duplicates,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise FigureDataError(f"strict JSON cannot be read: {path}: {exc}") from exc
    if type(value) is not dict:
        _fail(f"JSON top level must be an object: {path}")
    return value


def ci95(samples: Sequence[float]) -> tuple[float, float | None]:
    """Return raw-sample mean and Student-t 95% half-width."""
    values = [float(value) for value in samples]
    if not values or any(not math.isfinite(value) for value in values):
        _fail("raw samples must be finite and non-empty")
    center = statistics.fmean(values)
    if len(values) == 1:
        return center, None
    df = len(values) - 1
    if df >= len(_T975):
        _fail("raw sample count exceeds the frozen t-critical table")
    half = _T975[df] * statistics.stdev(values) / math.sqrt(len(values))
    return center, half


def _cells(document: Mapping[str, Any], section: str) -> Mapping[str, Any]:
    value = document.get(section)
    if type(value) is not dict:
        _fail(f"missing measurement section {section}")
    nested = value.get("cells")
    if nested is not None:
        if type(nested) is not dict:
            _fail(f"{section}.cells must be an object")
        return nested
    return value


def _raw_throughputs(cell: object, label: str) -> tuple[list[float], list[str]]:
    if type(cell) is not dict or type(cell.get("reps")) is not list:
        _fail(f"{label} must contain reps[]")
    values: list[float] = []
    jobs: list[str] = []
    for rep in cell["reps"]:
        if type(rep) is not dict or type(rep.get("throughputs")) is not list:
            _fail(f"{label} repetition must contain throughputs[]")
        values.extend(float(value) for value in rep["throughputs"])
        job = rep.get("pbs_jobid")
        if type(job) is not str or not job:
            _fail(f"{label} repetition lacks pbs_jobid")
        jobs.append(job)
    if not values or any(not math.isfinite(value) for value in values):
        _fail(f"{label} raw throughput is invalid")
    return values, jobs


def _measurement_series(
    measured: Mapping[str, Any], section: str, update_us: int,
) -> dict[float, dict[str, Any]]:
    rows: dict[float, dict[str, Any]] = {}
    for key, cell in _cells(measured, section).items():
        if not key.startswith(f"{WORKLOAD}|") or type(cell) is not dict:
            continue
        meta = cell.get("meta")
        if type(meta) is not dict or meta.get("back_off") != 1:
            continue
        if int(meta.get("update_us", 10)) != update_us:
            continue
        if float(meta.get("ceiling_us", 1000.0)) != 1000.0:
            continue
        step = float(meta["step_us"])
        values, jobs = _raw_throughputs(cell, key)
        if step in rows:
            _fail(f"duplicate measured coordinate: {section}/{step}/{update_us}")
        center, half = ci95(values)
        rows[step] = {
            "samples_tps": values, "mean_tps": center,
            "ci95_half_tps": half, "pbs_jobids": jobs,
        }
    return rows


def _static_reference(
    measured: Mapping[str, Any], name: str,
) -> dict[str, Any]:
    key = f"{WORKLOAD}|{name}"
    values, jobs = _raw_throughputs(_cells(
        measured, "static_fixed_backoff",
    ).get(key), key)
    center, half = ci95(values)
    return {
        "cell": name, "samples_tps": values, "mean_tps": center,
        "ci95_half_tps": half, "pbs_jobids": jobs,
    }


def _find_run(
    model: Mapping[str, Any], *, scenario: str, step_us: float,
    update_us: int, ceiling_us: float = 1000.0,
) -> Mapping[str, Any]:
    predictions = model.get("predictions")
    if type(predictions) is not list:
        _fail("model predictions must be a list")
    rows = [
        run for run in predictions
        if type(run) is dict and run.get("workload") == WORKLOAD
        and run.get("scenario") == scenario
        and run.get("condition", {}).get("step_us") == step_us
        and run.get("condition", {}).get("nominal_update_us") == update_us
        and run.get("condition", {}).get("ceiling_us") == ceiling_us
    ]
    if len(rows) != 1:
        _fail(
            "model coordinate must be unique: "
            f"{scenario}/{step_us}/{update_us}/{ceiling_us}"
        )
    return rows[0]


def _prediction_summary(run: Mapping[str, Any]) -> dict[str, Any]:
    reps = run.get("repetitions")
    if type(reps) is not list or not reps:
        _fail("model run must retain repetitions[]")
    values = [float(rep["throughput_tps"]) for rep in reps]
    center, half = ci95(values)
    return {"samples_tps": values, "mean_tps": center, "ci95_half_tps": half}


def load_inputs(
    mode: str, model_path: Path, measured_path: Path, backoff_path: Path,
) -> dict[str, Any]:
    if mode not in ("prediction", "residence", "mechanism"):
        _fail(f"unknown mode: {mode}")
    paths = [path.resolve() for path in (model_path, measured_path, backoff_path)]
    if len(set(paths)) != 3:
        _fail("model, measured, and backoff paths must be distinct")
    model = _strict_json(paths[0])
    measured = _strict_json(paths[1])
    if model.get("schema_version") != MODEL_SCHEMA:
        _fail(f"model schema must equal {MODEL_SCHEMA}")
    if NOT_CERTIFIED_FRAGMENT not in str(model.get("not_certified")):
        _fail("model lacks the required non-certification boundary")
    if model.get("protocol") != "Silo":
        _fail("model protocol must be Silo")
    provenance = model.get("provenance")
    if type(provenance) is not dict:
        _fail("model provenance must be an object")
    measured_provenance = provenance.get("measured_input")
    backoff_provenance = provenance.get("backoff_copy")
    if type(measured_provenance) is not dict or type(backoff_provenance) is not dict:
        _fail("model input provenance is incomplete")
    if measured_provenance.get("sha256") != _sha256(paths[1]):
        _fail("measured JSON hash differs from model provenance")
    if backoff_provenance.get("sha256") != _sha256(paths[2]):
        _fail("backoff copy hash differs from model provenance")
    if _sha256(paths[2]) != BACKOFF_COPY_SHA256:
        _fail("backoff copy is not the pinned source copy")
    configuration = model.get("configuration")
    if type(configuration) is not dict:
        _fail("model configuration must be an object")
    return {
        "mode": mode,
        "model": model,
        "measured": measured,
        "input_records": [
            {"path": str(path), "sha256": _sha256(path)} for path in paths
        ],
        "configuration": configuration,
        "none": _static_reference(measured, "none"),
        "T0": _static_reference(measured, "zero-loop"),
        "T100": _static_reference(measured, "constant-mu100"),
    }


def _style() -> None:
    mpl.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "font.family": "DejaVu Sans",
        "font.size": 7.7,
        "axes.titlesize": 8.8,
        "axes.labelsize": 8.0,
        "xtick.labelsize": 6.8,
        "ytick.labelsize": 6.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
    })


def _condition_text(data: Mapping[str, Any]) -> str:
    config = data["configuration"]
    return (
        f"Silo; 48 threads; 1,000,000 records; zipf 0.9; "
        f"{float(config['duration_us']) / 1e6:g} s; env Pegasus"
    )


def _figure_text(fig, data: Mapping[str, Any], title: str) -> None:
    fig.text(0.5, 0.997, title, ha="center", va="top", fontsize=11,
             fontweight="bold", gid="figure-heading")
    fig.text(0.5, 0.940, _condition_text(data), ha="center", va="top",
             fontsize=7.5, gid="figure-subtitle")
    fig.text(
        0.5, 0.012,
        "NOT CERTIFIED - trace-disabled performance only; no serializability check. "
        "Observed and model intervals are Student t 95% CI from raw repetitions.",
        ha="center", va="bottom", fontsize=6.8, color="#8d1f1f",
        gid="figure-footer",
    )


def _prediction_figure(data: Mapping[str, Any]):
    _style()
    fig, axes = plt.subplots(1, 5, figsize=(16.2, 4.6), squeeze=False)
    fig.subplots_adjust(left=0.055, right=0.992, top=0.80, bottom=0.20, wspace=0.27)
    model = data["model"]
    measured = data["measured"]
    plotted: list[dict[str, Any]] = [
        {
            "dataset": "reference", "label": "no backoff (BACK_OFF=0)",
            "raw": data["none"],
        },
        {
            "dataset": "reference", "label": "active zero-loop T(0)",
            "raw": data["T0"],
        },
        {
            "dataset": "reference", "label": "static backoff 100 us",
            "raw": data["T100"],
        },
    ]
    handles = labels = None
    for column, update in enumerate(UPDATES):
        axis = axes[0, column]
        stage1 = _measurement_series(
            measured, "stage1_adaptive_step_x_interval", update,
        )
        model_steps = (
            sorted(set(stage1) | {0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0})
            if update == 10 else sorted(stage1)
        )
        predicted = {
            step: _prediction_summary(_find_run(
                model, scenario="M_exact", step_us=step, update_us=update,
            ))
            for step in model_steps
        }
        x = sorted(stage1)
        obs = axis.errorbar(
            x, [stage1[step]["mean_tps"] / 1e6 for step in x],
            yerr=[(stage1[step]["ci95_half_tps"] or 0.0) / 1e6 for step in x],
            color="#111111", marker="o", linestyle="none", capsize=2.4,
            label="stage1 observed (n=7)",
        )
        pred = axis.errorbar(
            model_steps,
            [predicted[step]["mean_tps"] / 1e6 for step in model_steps],
            yerr=[
                (predicted[step]["ci95_half_tps"] or 0.0) / 1e6
                for step in model_steps
            ],
            color="#1f77b4", marker="s", linestyle="-", linewidth=1.15,
            capsize=2.4, label="event-driven model",
        )
        if update == 10:
            d1475 = _measurement_series(
                measured, "d1475_adaptive_step_grid", update,
            )
            xd = sorted(d1475)
            dline = axis.errorbar(
                xd, [d1475[step]["mean_tps"] / 1e6 for step in xd],
                yerr=[(d1475[step]["ci95_half_tps"] or 0.0) / 1e6 for step in xd],
                color="#d62728", marker="^", linestyle="none", capsize=2.4,
                label="D1475 observed (n=3)",
            )
            plotted.append({"dataset": "D1475", "update_us": update, "rows": d1475})
        else:
            dline = None
        none_line = axis.axhline(
            data["none"]["mean_tps"] / 1e6, color="#666666", linestyle="--",
            linewidth=0.9, label="no backoff (BACK_OFF=0)",
        )
        t0_line = axis.axhline(
            data["T0"]["mean_tps"] / 1e6, color="#2ca02c", linestyle="-.",
            linewidth=0.9, label="active zero-loop T(0)",
        )
        t100_line = axis.axhline(
            data["T100"]["mean_tps"] / 1e6, color="#9467bd", linestyle=":",
            linewidth=1.0, label="static backoff 100 us",
        )
        axis.set_xscale("log")
        axis.set_xticks(x, [f"{value:g}" for value in x])
        axis.minorticks_off()
        axis.set_xlabel("step (us)")
        axis.set_ylabel("throughput (M tps)" if column == 0 else "")
        axis.set_title(f"nominal update {update} us")
        axis.margins(x=0.08, y=0.16)
        plotted.extend((
            {"dataset": "stage1", "update_us": update, "rows": stage1},
            {"dataset": "model", "update_us": update, "rows": predicted},
        ))
        if column == 0:
            artists = [obs, pred]
            if dline is not None:
                artists.append(dline)
            artists.extend((none_line, t0_line, t100_line))
            handles = artists
            labels = [artist.get_label() for artist in artists]
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.895),
               ncol=6, fontsize=7.0)
    _figure_text(fig, data, "Adaptive backoff step response: observed and predicted")
    return fig, axes, plotted


def _survivor_summary(run: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    thresholds = np.asarray(run.get("residence_thresholds_us"), dtype=float)
    reps = run.get("repetitions")
    if type(reps) is not list or not reps:
        _fail("residence run lacks raw repetitions")
    matrix = np.asarray([rep["residence_survivor"] for rep in reps], dtype=float)
    if matrix.shape != (len(reps), len(thresholds)):
        _fail("residence survivor shape differs")
    centers = []
    halves = []
    for column in range(matrix.shape[1]):
        center, half = ci95(matrix[:, column])
        centers.append(center)
        halves.append(0.0 if half is None else half)
    return thresholds, np.asarray(centers), np.asarray(halves)


def _residence_figure(data: Mapping[str, Any]):
    _style()
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.6), squeeze=False)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.79, bottom=0.18, wspace=0.23)
    palette = ("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd")
    plotted: list[dict[str, Any]] = []
    for column, update in enumerate((10, 2560)):
        axis = axes[0, column]
        for color, step in zip(palette, RESIDENCE_STEPS, strict=True):
            run = _find_run(
                data["model"], scenario="M_exact", step_us=step,
                update_us=update,
            )
            x, center, half = _survivor_summary(run)
            axis.plot(x, center, color=color, linewidth=1.25, label=f"step {step:g} us")
            axis.fill_between(x, np.maximum(0.0, center - half),
                              np.minimum(1.0, center + half), color=color, alpha=0.13)
            p_values = [float(rep["p_backoff_gt_100"]) for rep in run["repetitions"]]
            p_center, p_half = ci95(p_values)
            plotted.append({
                "scenario": "M_exact", "step_us": step, "update_us": update,
                "residence_thresholds_us": x.tolist(),
                "survivor_samples": [rep["residence_survivor"] for rep in run["repetitions"]],
                "p_backoff_gt_100_samples": p_values,
                "p_backoff_gt_100_mean": p_center,
                "p_backoff_gt_100_ci95_half": p_half,
            })
            if step in (0.5, 25.0):
                label_y = 0.60 if step == 0.5 else 0.50
                axis.text(
                    105.0, label_y,
                    f"step {step:g}: P(>100)={p_center:.2f}",
                    color=color, fontsize=6.5, ha="left", va="center",
                    gid="direct-label",
                )
        axis.axvline(100.0, color="#555555", linestyle="--", linewidth=0.9)
        axis.set_xscale("symlog", linthresh=1.0)
        axis.set_xlim(0.0, 1000.0)
        axis.set_ylim(-0.02, 1.04)
        axis.set_xlabel("backoff threshold b (us)")
        axis.set_ylabel("time-weighted P(Backoff >= b)" if column == 0 else "")
        axis.set_title(f"nominal update {update} us")
        axis.legend(loc="upper right", fontsize=6.7)
    _figure_text(fig, data, "Predicted time-weighted Backoff residence")
    return fig, axes, plotted


def _metric_samples(run: Mapping[str, Any], metric: str) -> list[float]:
    if metric == "throughput":
        return [float(rep["throughput_tps"]) for rep in run["repetitions"]]
    if metric == "p100":
        return [float(rep["p_backoff_gt_100"]) for rep in run["repetitions"]]
    if metric == "correct":
        return [float(rep["gradient_sign_rates"]["correct"]) for rep in run["repetitions"]]
    _fail(f"unknown metric: {metric}")
    raise AssertionError("unreachable")


def _plot_metric_series(axis, data, *, scenarios, steps, update, metric, labels):
    palette = ("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728")
    plotted = []
    for scenario, label, color in zip(scenarios, labels, palette):
        centers = []
        halves = []
        raw = []
        for step in steps:
            run = _find_run(data["model"], scenario=scenario, step_us=step,
                            update_us=update)
            samples = _metric_samples(run, metric)
            center, half = ci95(samples)
            centers.append(center)
            halves.append(0.0 if half is None else half)
            raw.append(samples)
        scale = 1e6 if metric == "throughput" else 1.0
        axis.errorbar(
            steps, np.asarray(centers) / scale, yerr=np.asarray(halves) / scale,
            marker="o", linewidth=1.1, capsize=2.2, color=color, label=label,
        )
        plotted.append({
            "scenario": scenario, "metric": metric, "update_us": update,
            "steps_us": list(steps), "samples": raw,
        })
    axis.set_xscale("log")
    axis.set_xticks(steps, [f"{value:g}" for value in steps])
    axis.minorticks_off()
    axis.set_xlabel("step (us)")
    axis.legend(fontsize=6.7)
    return plotted


def _mechanism_figure(data: Mapping[str, Any]):
    _style()
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.1), squeeze=False)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.79, bottom=0.11,
                        wspace=0.24, hspace=0.36)
    plotted: list[dict[str, Any]] = []
    diagnostic_steps = (0.5, 1.0, 5.0, 25.0)
    plotted += _plot_metric_series(
        axes[0, 0], data, scenarios=("M_exact", "M_no_trunc"),
        steps=diagnostic_steps, update=10, metric="throughput",
        labels=("source-exact", "without uint64 truncation"),
    )
    axes[0, 0].set_ylabel("throughput (M tps)")
    axes[0, 0].set_title("Truncation counterfactual")
    plotted += _plot_metric_series(
        axes[0, 1], data, scenarios=("M_exact", "M_no_trunc"),
        steps=diagnostic_steps, update=10, metric="p100",
        labels=("source-exact", "without uint64 truncation"),
    )
    axes[0, 1].set_ylabel("P(Backoff > 100 us)")
    axes[0, 1].set_title("High-backoff residence")
    plotted += _plot_metric_series(
        axes[1, 0], data, scenarios=("M_exact",),
        steps=(0.5, 1.0, 5.0), update=10, metric="correct",
        labels=("nominal update 10 us",),
    )
    # Draw the second update explicitly so the data lookup is not disguised by
    # a condition-specific parameter inside the generic helper.
    steps = (0.5, 1.0, 5.0)
    centers = []
    halves = []
    raw = []
    for step in steps:
        run = _find_run(data["model"], scenario="M_exact", step_us=step,
                        update_us=2560)
        samples = _metric_samples(run, "correct")
        center, half = ci95(samples)
        centers.append(center)
        halves.append(0.0 if half is None else half)
        raw.append(samples)
    axes[1, 0].errorbar(steps, centers, yerr=halves, marker="s", linewidth=1.1,
                        capsize=2.2, color="#ff7f0e", label="nominal update 2560 us")
    axes[1, 0].legend(fontsize=6.7)
    axes[1, 0].set_ylabel("gradient-sign correct rate")
    axes[1, 0].set_title("Gradient-sign diagnosis")
    plotted.append({
        "scenario": "M_exact", "metric": "correct", "update_us": 2560,
        "steps_us": list(steps), "samples": raw,
    })
    all_steps = tuple(sorted({0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0}))
    plotted += _plot_metric_series(
        axes[1, 1], data,
        scenarios=("M_exact", "M_flat_tail", "M_linear_zero"),
        steps=all_steps, update=10, metric="throughput",
        labels=("log-linear tail", "flat tail", "linear-to-zero tail"),
    )
    axes[1, 1].set_ylabel("throughput (M tps)")
    axes[1, 1].set_title("Unmeasured-tail sensitivity")
    _figure_text(fig, data, "Adaptive-backoff mechanism counterfactuals")
    return fig, axes, plotted


def make_figure(data: Mapping[str, Any]):
    """Create the selected production figure without writing it."""
    with mpl.rc_context():
        if data["mode"] == "prediction":
            return _prediction_figure(data)
        if data["mode"] == "residence":
            return _residence_figure(data)
        return _mechanism_figure(data)


def _intersection_area(left, right) -> float:
    x0, y0 = max(left.x0, right.x0), max(left.y0, right.y0)
    x1, y1 = min(left.x1, right.x1), min(left.y1, right.y1)
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _contains(outer, inner, tolerance: float = 0.5) -> bool:
    return (
        inner.x0 >= outer.x0 - tolerance and inner.y0 >= outer.y0 - tolerance
        and inner.x1 <= outer.x1 + tolerance and inner.y1 <= outer.y1 + tolerance
    )


def check_figure_layout(fig, axes) -> None:
    """Fail on visible text outside the figure or inside a neighboring panel."""
    from matplotlib.text import Text

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_box = fig.bbox
    plot_axes = [axis for row in axes for axis in row]
    if len(plot_axes) not in (2, 4, 5):
        raise FigureLayoutError("production layout has an unexpected panel count")
    direct_boxes = []
    text_boxes = []
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if box.width <= 0.0 or box.height <= 0.0:
            continue
        if not _contains(figure_box, box):
            raise FigureLayoutError(f"text leaves figure: {text.get_text()!r}")
        if text.axes is not None:
            for other in fig.axes:
                if other is not text.axes and _intersection_area(box, other.bbox) > 1.0:
                    raise FigureLayoutError(
                        f"text enters neighboring panel: {text.get_text()!r}"
                    )
        if text.get_gid() == "direct-label":
            if text.axes is None or not _contains(text.axes.bbox, box):
                raise FigureLayoutError(f"direct label leaves its panel: {text.get_text()!r}")
            direct_boxes.append((text, box))
        text_boxes.append((text, box))
    for index, (left_text, left_box) in enumerate(text_boxes):
        for right_text, right_box in text_boxes[index + 1:]:
            if _intersection_area(left_box, right_box) > 1.0:
                raise FigureLayoutError(
                    f"text bbox overlap: {left_text.get_text()!r} / "
                    f"{right_text.get_text()!r}"
                )
    for index, (left_text, left_box) in enumerate(direct_boxes):
        for right_text, right_box in direct_boxes[index + 1:]:
            if _intersection_area(left_box, right_box) > 1.0:
                raise FigureLayoutError(
                    f"direct-label overlap: {left_text.get_text()!r} / "
                    f"{right_text.get_text()!r}"
                )
    for axis in fig.axes:
        tight = axis.get_tightbbox(renderer)
        if tight is not None and not _contains(figure_box, tight, tolerance=1.0):
            raise FigureLayoutError("axes decoration leaves figure boundary")


def _inputs_unchanged(input_records: Sequence[Mapping[str, Any]]) -> None:
    for row in input_records:
        if _sha256(Path(row["path"])) != row["sha256"]:
            _fail(f"input changed during figure generation: {row['path']}")


def _atomic_save_figure(
    fig, axes, prefix: Path, input_records: Sequence[Mapping[str, Any]],
) -> list[Path]:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    temporary: list[tuple[Path, Path]] = []
    try:
        for suffix, fmt in ((".png", "png"), (".pdf", "pdf")):
            descriptor, raw = tempfile.mkstemp(
                prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent,
            )
            os.close(descriptor)
            temp = Path(raw)
            destination = Path(f"{prefix}{suffix}")
            temporary.append((temp, destination))
            fig.savefig(temp, format=fmt, dpi=200)
        check_figure_layout(fig, axes)
        _inputs_unchanged(input_records)
        for temp, destination in temporary:
            os.replace(temp, destination)
        return [destination for _temp, destination in temporary]
    finally:
        for temp, _destination in temporary:
            try:
                temp.unlink()
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
    data: Mapping[str, Any], outputs: Sequence[Path], plotted: Sequence[Mapping[str, Any]],
    argv: Sequence[str],
) -> dict[str, Any]:
    _inputs_unchanged(data["input_records"])
    jobids = sorted({
        *data["none"]["pbs_jobids"], *data["T0"]["pbs_jobids"],
        *data["T100"]["pbs_jobids"],
        *data["model"]["provenance"].get("static_calibration_jobids", []),
        *data["model"]["provenance"].get("evaluation_jobids", []),
        *[
            job
            for item in plotted if item.get("dataset") in ("stage1", "D1475")
            for row in item["rows"].values()
            for job in row["pbs_jobids"]
        ],
    })
    return {
        "provenance_schema_version": PROVENANCE_SCHEMA,
        "model_schema_version": MODEL_SCHEMA,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "mode": data["mode"],
        "not_certified": data["model"]["not_certified"],
        "generator": {"path": str(GENERATOR), "sha256": _sha256(GENERATOR)},
        "inputs": data["input_records"],
        "outputs": [
            {"path": str(path.resolve()), "sha256": _sha256(path)} for path in outputs
        ],
        "pbs_jobids": jobids,
        "measurement_conditions": {
            "protocol": "Silo", "threads": 48, "records": 1_000_000,
            "zipf_skew": 0.9, "extime_s": 3, "env": "Pegasus",
        },
        "seed": data["configuration"].get("base_seed"),
        "conditions": data["configuration"].get("condition_order"),
        "ci95": {
            "center": "sample mean recomputed from raw repetitions",
            "half_width": "t_(0.975,n-1) * sample_stdev / sqrt(n)",
            "n_equals_1": "CI unavailable and not drawn",
        },
        "primary_values": list(plotted),
        "caption": (
            f"T-2216 {data['mode']} figure. Observed and model summaries are "
            "recomputed from raw repetitions. Silo, 48 threads, 1,000,000 "
            "records, zipf 0.9, 3 s, Pegasus. NOT CERTIFIED: trace-disabled "
            "performance only; no serializability check."
        ),
        "reproduction": {"argv": [str(value) for value in argv]},
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prediction", "residence", "mechanism"))
    parser.add_argument("out_prefix", type=Path)
    parser.add_argument("model_json", type=Path)
    parser.add_argument("measured_json", type=Path)
    parser.add_argument("backoff_copy", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    figure = None
    published_outputs: list[Path] = []
    try:
        data = load_inputs(
            args.mode, args.model_json, args.measured_json, args.backoff_copy,
        )
        figure, axes, plotted = make_figure(data)
        prefix = args.out_prefix.resolve()
        outputs = _atomic_save_figure(
            figure, axes, prefix, data["input_records"],
        )
        published_outputs = list(outputs)
        canonical_argv = [
            "python3", str(GENERATOR), args.mode, str(prefix),
            str(args.model_json.resolve()), str(args.measured_json.resolve()),
            str(args.backoff_copy.resolve()),
        ]
        provenance = build_provenance(data, outputs, plotted, canonical_argv)
        _atomic_json(Path(f"{prefix}.provenance.json"), provenance)
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary.
        # A late input-change/provenance failure must not leave a figure pair
        # visible without its proof-chain sidecar.
        for path in published_outputs:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        if figure is not None:
            plt.close(figure)
    print(f"wrote {prefix}.png / .pdf / .provenance.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
