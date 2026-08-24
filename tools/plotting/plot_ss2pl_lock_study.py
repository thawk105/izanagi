#!/usr/bin/env python3
"""Render three core figures and two optional control figures for the SS2PL lock study.

Inputs are the single-occasion JSON receipts emitted by
``tools/pegasus/run_ss2pl_lock_study.py``.  Sweep and replication receipts are
never pooled.  The optional replication input contributes only a separately
reported B/D sign check to provenance.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import statistics
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


np = mpl = plt = None
SCHEMA_VERSION = "ss2pl-lock-study/v1"
ARMS = ("S", "C", "A", "B", "D")
THREADS = (1, 2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48)
PAIRINGS = (("B", "D"), ("A", "B"), ("S", "C"), ("A", "C"))
COLORS = {
    "S": "#4d4d4d", "C": "#1f77b4", "A": "#e68613",
    "B": "#b33c2e", "D": "#2b8c5a",
}
MARKERS = {"S": "o", "C": "s", "A": "^", "B": "D", "D": "v"}
ARM_LABELS = {
    "S": "stock reader-writer No-Wait",
    "C": "study reader-writer No-Wait",
    "A": "exclusive No-Wait",
    "B": "exclusive Wound-Wait",
    "D": "reader-writer Wound-Wait",
}
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}


class PlotContractError(RuntimeError):
    pass


def ensure_plot_host_allowed(hostname: str | None = None) -> None:
    observed = hostname or socket.gethostname()
    if observed.lower().startswith("bnode"):
        raise PlotContractError(f"plotting is forbidden on measurement host {observed}")


def _load_deps() -> None:
    global np, mpl, plt
    if np is not None:
        return
    import numpy as _np
    import matplotlib as _mpl
    _mpl.use("Agg")
    import matplotlib.pyplot as _plt
    np, mpl, plt = _np, _mpl, _plt


def _style() -> None:
    mpl.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 220,
        "font.family": "sans-serif",
        "font.size": 8.5,
        "axes.titlesize": 9,
        "axes.labelsize": 8.5,
        "xtick.labelsize": 7.2,
        "ytick.labelsize": 7.2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.27,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
        "lines.linewidth": 1.5,
        "figure.constrained_layout.use": True,
    })


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, indent=2, ensure_ascii=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _driver_module():
    path = Path(__file__).resolve().parents[1] / "pegasus" / "run_ss2pl_lock_study.py"
    spec = importlib.util.spec_from_file_location("ss2pl_lock_study_driver_for_plot", path)
    if spec is None or spec.loader is None:
        raise PlotContractError(f"cannot load driver contract from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_receipt(path: Path, expected_mode: str) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != SCHEMA_VERSION:
        raise PlotContractError(f"unsupported schema: {document.get('schema_version')}")
    if document.get("status") != "complete" or document.get("mode") != expected_mode:
        raise PlotContractError(
            f"input must be a complete {expected_mode} receipt: status={document.get('status')}, mode={document.get('mode')}"
        )
    driver = _driver_module()
    try:
        driver.validate_completed_receipt(document, expected_mode)
        environment = document.get("environment")
        if not isinstance(environment, Mapping) or not environment:
            raise PlotContractError("measurement environment is missing")
        warmup = document.get("process_internal_warmup")
        if not isinstance(warmup, Mapping) or warmup.get("present") is not False:
            raise PlotContractError("process-internal warmup absence is not recorded")
    except Exception as exc:
        raise PlotContractError(str(exc)) from exc
    return document


def _metric(run: Mapping[str, Any], name: str) -> float:
    value = float(run["metrics"][name])
    if name == "throughput_tps" and (not math.isfinite(value) or value <= 0):
        raise PlotContractError(f"throughput must be finite and positive: {value}")
    return value


def _runs_for(
    document: Mapping[str, Any], *, arm: str, thread: int,
    experiment: str, workload: Mapping[str, Any] | None = None,
) -> list[Mapping[str, Any]]:
    result = []
    for run in document["performance_runs"]:
        if run["arm"] != arm or int(run["thread_num"]) != thread or run["experiment"] != experiment:
            continue
        if workload is not None and any(
            str(run["workload"].get(key)) != str(value) for key, value in workload.items()
        ):
            continue
        result.append(run)
    return sorted(result, key=lambda run: int(run["block_id"]))


def mean_ci95(values: Sequence[float]) -> tuple[float, float]:
    if len(values) < 2:
        raise PlotContractError("95% CI requires at least two repetitions")
    mean = statistics.fmean(values)
    critical = T975.get(len(values) - 1, 1.96)
    half = critical * statistics.stdev(values) / math.sqrt(len(values))
    return mean, half


def saturation_point(runs: Sequence[Mapping[str, Any]], arm: str) -> dict[str, Any]:
    medians: dict[int, float] = {}
    for thread in THREADS:
        values = [_metric(run, "throughput_tps") for run in runs if run["arm"] == arm and int(run["thread_num"]) == thread]
        if not values:
            raise PlotContractError(f"missing throughput values for {arm}/{thread}")
        medians[thread] = statistics.median(values)
    point = THREADS[-1]
    for current, following in zip(THREADS, THREADS[1:]):
        if medians[following] <= medians[current] * 1.030:
            point = current
            break
    maximum_thread = max(medians, key=medians.get)
    return {
        "n_star": point,
        "scales_to_48": point == 48,
        "median_tps": {str(key): value for key, value in medians.items()},
        "maximum_tps": medians[maximum_thread],
        "maximum_tps_thread": maximum_thread,
    }


def parallel_efficiency_from_medians(
    runs: Sequence[Mapping[str, Any]], arm: str, thread: int
) -> float:
    base = [
        _metric(run, "throughput_tps")
        for run in runs if run["arm"] == arm and int(run["thread_num"]) == 1
    ]
    selected = [
        _metric(run, "throughput_tps")
        for run in runs if run["arm"] == arm and int(run["thread_num"]) == thread
    ]
    if not base or not selected or thread <= 0:
        raise PlotContractError(f"parallel efficiency inputs are incomplete for {arm}/{thread}")
    return statistics.median(selected) / statistics.median(base) / thread


def paired_log_effect(
    runs: Sequence[Mapping[str, Any]], arm_x: str, arm_y: str, thread: int
) -> dict[str, Any]:
    by_cell: dict[tuple[str, int], float] = {}
    for run in runs:
        if int(run["thread_num"]) == thread and run["arm"] in {arm_x, arm_y}:
            key = (str(run["arm"]), int(run["block_id"]))
            if key in by_cell:
                raise PlotContractError(f"duplicate paired cell {key}/{thread}")
            by_cell[key] = _metric(run, "throughput_tps")
    blocks_x = {block for arm, block in by_cell if arm == arm_x}
    blocks_y = {block for arm, block in by_cell if arm == arm_y}
    if blocks_x != blocks_y or len(blocks_x) < 2:
        raise PlotContractError(f"unpaired blocks for {arm_x}/{arm_y}/{thread}")
    logs = [math.log(by_cell[(arm_y, block)] / by_cell[(arm_x, block)]) for block in sorted(blocks_x)]
    mean, half = mean_ci95(logs)
    ratio = math.exp(mean)
    return {
        "arm_x": arm_x, "arm_y": arm_y, "thread_num": thread,
        "blocks": sorted(blocks_x), "log_ratios": logs,
        "mean_log_ratio": mean, "ci95_log_half_width": half,
        "ratio": ratio, "ci95_ratio_low": math.exp(mean - half),
        "ci95_ratio_high": math.exp(mean + half),
        "floor_verdict": floor_verdict(ratio),
    }


def floor_verdict(ratio: float) -> str:
    if ratio <= 0 or not math.isfinite(ratio):
        raise PlotContractError("effect ratio must be finite and positive")
    if abs(ratio - 1.0) < 0.030:
        return "below_floor_no_reproducible_difference_established"
    return "above_floor_positive" if ratio > 1.0 else "above_floor_negative"


def validate_provenance(provenance: Mapping[str, Any], inputs: Sequence[Path]) -> None:
    rows = provenance.get("inputs")
    if not isinstance(rows, list) or len(rows) != len(inputs):
        raise PlotContractError("provenance input list is missing or incomplete")
    expected = {str(path.resolve()): sha256_file(path) for path in inputs}
    observed = {str(Path(row["path"]).resolve()): row.get("sha256") for row in rows}
    if observed != expected:
        raise PlotContractError(f"provenance SHA256 mismatch: {observed} != {expected}")
    for field in ("conditions", "figure_values"):
        if field not in provenance:
            raise PlotContractError(f"provenance lacks {field}")
    conditions = provenance["conditions"]
    if not isinstance(conditions, Mapping) or not isinstance(conditions.get("environment"), Mapping):
        raise PlotContractError("provenance lacks measurement environment")
    caption_fields = provenance.get("caption_fields")
    if (
        not isinstance(caption_fields, Mapping)
        or caption_fields.get("process_internal_warmup_present") is not False
    ):
        raise PlotContractError("provenance lacks process-internal warmup absence")


def find_non_tick_overlaps(
    boxes: Sequence[tuple[str, tuple[float, float, float, float], bool]]
) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    for index, (label_a, a, tick_a) in enumerate(boxes):
        ax0, ay0, ax1, ay1 = a
        for label_b, b, tick_b in boxes[index + 1:]:
            if tick_a and tick_b:
                continue
            bx0, by0, bx1, by1 = b
            width = min(ax1, bx1) - max(ax0, bx0)
            height = min(ay1, by1) - max(ay0, by0)
            if width > 0.5 and height > 0.5:
                overlaps.append((label_a, label_b))
    return overlaps


def _figure_overlap_check(fig: Any) -> None:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    tick_objects = set()
    for axis in fig.axes:
        tick_objects.update(axis.get_xticklabels())
        tick_objects.update(axis.get_yticklabels())
    boxes = []
    figure_box = fig.bbox
    axes_boxes = {axis: axis.get_window_extent(renderer) for axis in fig.axes}
    for text in fig.findobj(mpl.text.Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if (
            box.x0 < figure_box.x0 - 0.5 or box.y0 < figure_box.y0 - 0.5
            or box.x1 > figure_box.x1 + 0.5 or box.y1 > figure_box.y1 + 0.5
        ):
            raise PlotContractError(f"text leaves final figure canvas: {text.get_text()!r}")
        owner = getattr(text, "axes", None)
        if owner in axes_boxes and text not in tick_objects:
            for other, other_box in axes_boxes.items():
                if other is owner:
                    continue
                width = min(box.x1, other_box.x1) - max(box.x0, other_box.x0)
                height = min(box.y1, other_box.y1) - max(box.y0, other_box.y0)
                if width > 0.5 and height > 0.5:
                    raise PlotContractError(
                        f"text crosses into another panel: {text.get_text()!r}"
                    )
        boxes.append((text.get_text(), (box.x0, box.y0, box.x1, box.y1), text in tick_objects))
    overlaps = find_non_tick_overlaps(boxes)
    if overlaps:
        raise PlotContractError(f"non-tick text bbox overlap: {overlaps}")


def _save_checked(fig: Any, prefix: Path) -> None:
    fig.canvas.draw()
    for axis in fig.axes:
        lower, upper = sorted(axis.get_ylim())
        tolerance = max(1.0, upper - lower) * 1e-9
        visible_ticks = [
            tick for tick in axis.get_yticks()
            if lower - tolerance <= tick <= upper + tolerance
        ]
        if visible_ticks:
            axis.set_yticks(visible_ticks)
    _figure_overlap_check(fig)
    temporary_paths: list[Path] = []
    installed_paths: list[Path] = []
    final_paths = [prefix.with_suffix(suffix) for suffix in (".png", ".pdf")]
    if any(path.exists() for path in final_paths):
        raise PlotContractError(f"refusing to replace existing figure outputs: {final_paths}")
    try:
        for suffix in (".png", ".pdf"):
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent,
            )
            os.close(descriptor)
            temporary_path = Path(temporary)
            temporary_paths.append(temporary_path)
            fig.savefig(temporary_path)
        for final_path, temporary_path in zip(final_paths, temporary_paths):
            os.replace(temporary_path, final_path)
            installed_paths.append(final_path)
        temporary_paths.clear()
        installed_paths.clear()
    finally:
        for temporary_path in temporary_paths:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
        for installed_path in installed_paths:
            try:
                installed_path.unlink()
            except FileNotFoundError:
                pass


def _conditions(document: Mapping[str, Any]) -> dict[str, Any]:
    runs = document["performance_runs"]
    workloads = [run["workload"] for run in runs]
    environment = document.get("environment")
    if not isinstance(environment, Mapping) or not environment:
        raise PlotContractError("measurement environment is required")
    return {
        "records": sorted({int(workload["ycsb_tuple_num"]) for workload in workloads}),
        "read_ratios": sorted({int(workload["ycsb_rratio"]) for workload in workloads}),
        "rmw": sorted({int(workload["ycsb_rmw"]) for workload in workloads}),
        "skews": sorted({float(workload["ycsb_zipf_skew"]) for workload in workloads}),
        "max_operations": sorted({int(workload["ycsb_max_ope"]) for workload in workloads}),
        "payload_bytes": 8,
        "threads": sorted({int(run["thread_num"]) for run in runs}),
        "node": document["occasion"]["node"],
        "occasion_id": document["occasion"]["occasion_id"],
        "campaign_id": document["occasion"]["occasion_id"],
        "environment": dict(environment),
    }


def _compact_values(values: Sequence[Any]) -> str:
    return ",".join(format(value, "g") if isinstance(value, float) else str(value) for value in values)


def _condition_caption(
    document: Mapping[str, Any], *, blocks: int, warmup: bool = True,
    records: Sequence[int] | None = None, skews: Sequence[float] | None = None,
    read_ratios: Sequence[int] | None = None, threads: Sequence[int] | None = None,
) -> str:
    conditions = _conditions(document)
    items = [
        f"records={_compact_values(records or conditions['records'])}",
        f"skew={_compact_values(skews or conditions['skews'])}",
        f"rratio={_compact_values(read_ratios or conditions['read_ratios'])}",
        f"threads={_compact_values(threads or conditions['threads'])}",
        f"env={conditions['environment'].get('node', conditions['node'])}",
        f"blocks={blocks}",
    ]
    if warmup:
        items.append("process-internal warmup=none")
    return "; ".join(items[:4]) + "\n" + "; ".join(items[4:])


def _base_provenance(
    generator: str, inputs: Sequence[Path], conditions: Mapping[str, Any], values: Mapping[str, Any]
) -> dict[str, Any]:
    provenance = {
        "schema_version": "ss2pl-lock-study-figure-provenance/v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generator": generator,
        "inputs": [{"path": str(path.resolve()), "sha256": sha256_file(path)} for path in inputs],
        "conditions": dict(conditions),
        "figure_values": dict(values),
        "caption_fields": {
            "process_internal_warmup_present": False,
            "process_internal_warmup_statement": (
                "No process-internal warmup interval exists; startup transient is part of each run."
            ),
        },
        "claim_scope": (
            "descriptive study outside pipeline.evaluate; not certified fitness, floor, "
            "oracle, or variant-selection evidence"
        ),
    }
    validate_provenance(provenance, inputs)
    return provenance


def scalability_figure(sweep: Mapping[str, Any], prefix: Path) -> dict[str, Any]:
    _load_deps(); _style()
    runs = sweep["performance_runs"]
    fig, axes = plt.subplots(2, 1, figsize=(7.4, 6.7), sharex=True, height_ratios=(2.0, 1.0))
    values: dict[str, Any] = {"arms": {}, "saturation": {}}
    for arm in ARMS:
        means, halfs, efficiencies = [], [], []
        for thread in THREADS:
            selected = sorted(
                [run for run in runs if run["arm"] == arm and int(run["thread_num"]) == thread],
                key=lambda run: int(run["block_id"]),
            )
            reps = [_metric(run, "throughput_tps") for run in selected]
            mean, half = mean_ci95(reps)
            means.append(mean / 1e6); halfs.append(half / 1e6)
            efficiencies.append(parallel_efficiency_from_medians(runs, arm, thread))
        axes[0].errorbar(
            THREADS, means, yerr=halfs, label=ARM_LABELS[arm], color=COLORS[arm],
            marker=MARKERS[arm], ms=4.2, capsize=2.5,
        )
        axes[1].plot(
            THREADS, efficiencies, label=ARM_LABELS[arm],
            color=COLORS[arm], marker=MARKERS[arm], ms=3.8,
        )
        values["arms"][arm] = {
            str(thread): {
                "mean_tps": mean * 1e6,
                "ci95_half_tps": half * 1e6,
                "parallel_efficiency_from_medians": efficiency,
            }
            for thread, mean, half, efficiency
            in zip(THREADS, means, halfs, efficiencies)
        }
        values["saturation"][arm] = saturation_point(runs, arm)
    axes[0].set_ylabel("throughput (M tps)")
    axes[0].set_ylim(bottom=0)
    axes[0].legend(ncol=2, title="lock implementation", loc="upper center")
    saturation_text = "\n".join(
        f"{ARM_LABELS[arm]}: n*={values['saturation'][arm]['n_star']}" for arm in ARMS
    )
    axes[0].text(
        0.985, 0.04, saturation_text, transform=axes[0].transAxes,
        ha="right", va="bottom", fontsize=7,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "alpha": 0.82, "edgecolor": "#aaaaaa"},
    )
    axes[1].axhline(1.0, color="#777777", linestyle="--", linewidth=1.0)
    axes[1].set_ylabel("parallel efficiency")
    axes[1].set_xlabel("threads")
    axes[1].set_ylim(bottom=0)
    axes[1].set_xticks(THREADS)
    fig.suptitle(
        "SS2PL scalability\n" + _condition_caption(sweep, blocks=5), fontsize=8.5,
    )
    _save_checked(fig, prefix)
    plt.close(fig)
    return values


def abort_figure(sweep: Mapping[str, Any], prefix: Path) -> dict[str, Any]:
    _load_deps(); _style()
    runs = sweep["performance_runs"]
    fig, axis = plt.subplots(figsize=(7.4, 4.4))
    values: dict[str, Any] = {}
    for arm in ARMS:
        means, halfs = [], []
        for thread in THREADS:
            reps = [_metric(run, "abort_rate") for run in runs if run["arm"] == arm and int(run["thread_num"]) == thread]
            mean, half = mean_ci95(reps)
            means.append(100 * mean); halfs.append(100 * half)
        axis.errorbar(
            THREADS, means, yerr=halfs, label=ARM_LABELS[arm], color=COLORS[arm],
            marker=MARKERS[arm], ms=4.2, capsize=2.5,
        )
        values[arm] = {
            str(thread): {"mean_abort_rate": mean / 100, "ci95_half": half / 100}
            for thread, mean, half in zip(THREADS, means, halfs)
        }
    axis.set_xlabel("threads"); axis.set_ylabel("abort rate (%)")
    axis.set_ylim(bottom=0); axis.set_xticks(THREADS)
    axis.legend(ncol=2, title="lock implementation", loc="upper center")
    axis.set_title(
        "SS2PL abort rate: single workload-owned abort accounting\n"
        + _condition_caption(sweep, blocks=5), fontsize=8.5,
    )
    _save_checked(fig, prefix)
    plt.close(fig)
    return values


def paired_figure(sweep: Mapping[str, Any], prefix: Path) -> dict[str, Any]:
    _load_deps(); _style()
    runs = sweep["performance_runs"]
    fig, axis = plt.subplots(figsize=(8.4, 6.0))
    axis.axhspan(0.97, 1.03, color="#bbbbbb", alpha=0.35, label="3.0% between-run floor")
    axis.axhline(1.0, color="#555555", linestyle="--", linewidth=1.0)
    values: dict[str, Any] = {}
    for index, (arm_x, arm_y) in enumerate(PAIRINGS):
        effects = [paired_log_effect(runs, arm_x, arm_y, thread) for thread in THREADS]
        ratios = [item["ratio"] for item in effects]
        lower = [item["ratio"] - item["ci95_ratio_low"] for item in effects]
        upper = [item["ci95_ratio_high"] - item["ratio"] for item in effects]
        color = ("#2b8c5a", "#b33c2e", "#1f77b4", "#e68613")[index]
        axis.errorbar(
            THREADS, ratios, yerr=np.array([lower, upper]),
            label=f"{ARM_LABELS[arm_y]} / {ARM_LABELS[arm_x]}",
            color=color, marker=("o", "s", "^", "D")[index], ms=4.0, capsize=2.4,
        )
        values[f"{arm_x}_vs_{arm_y}"] = effects
    axis.set_xlabel("threads"); axis.set_ylabel("paired throughput ratio")
    axis.set_xticks(THREADS)
    axis.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    axis.set_title(
        "Paired effects from blockwise log ratios (95% t(4) CI)\n"
        + _condition_caption(sweep, blocks=5), fontsize=8.5,
    )
    _save_checked(fig, prefix)
    plt.close(fig)
    return values


def controls_figure(controls: Mapping[str, Any], prefix: Path) -> dict[str, Any]:
    _load_deps(); _style()
    runs = controls["performance_runs"]
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.4), sharex=True, sharey=True)
    values: dict[str, Any] = {"E1": {}, "E2": {}}
    for row, skew in enumerate((0, 0.9)):
        for column, thread in enumerate((24, 48)):
            axis = axes[row, column]
            for arm in ARMS:
                means, halfs = [], []
                for ratio in (0, 50, 100):
                    selected = [
                        run for run in runs
                        if run["experiment"] == "E1" and run["arm"] == arm
                        and int(run["thread_num"]) == thread
                        and float(run["workload"]["ycsb_zipf_skew"]) == skew
                        and int(run["workload"]["ycsb_rratio"]) == ratio
                    ]
                    mean, half = mean_ci95([_metric(run, "throughput_tps") for run in selected])
                    means.append(mean / 1e6); halfs.append(half / 1e6)
                    values["E1"][f"skew={skew},threads={thread},rratio={ratio},arm={arm}"] = {
                        "mean_tps": mean, "ci95_half_tps": half,
                    }
                axis.errorbar(
                    (0, 50, 100), means, yerr=halfs, color=COLORS[arm], label=ARM_LABELS[arm],
                    marker=MARKERS[arm], ms=3.8, capsize=2.2,
                )
            axis.set_title(f"skew={skew:g}, threads={thread}")
            axis.set_xticks((0, 50, 100))
    for axis in axes[-1, :]: axis.set_xlabel("read ratio (%)")
    for axis in axes[:, 0]: axis.set_ylabel("throughput (M tps)")
    axes[0, 0].legend(ncol=2, title="lock implementation", loc="upper center")
    for thread in (1, 24, 48):
        values["E2"][str(thread)] = paired_log_effect(
            [run for run in runs if run["experiment"] == "E2"], "B", "D", thread
        )
    fig.suptitle(
        "E1 mechanism control: read ratio by skew\n"
        + _condition_caption(controls, blocks=3), fontsize=8.5,
    )
    _save_checked(fig, prefix)
    plt.close(fig)
    return values


def _cycle_nodes_edges(cycle: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    snapshot = cycle.get("snapshot")
    if not isinstance(snapshot, Mapping):
        raise PlotContractError("accepted cycle lacks snapshot")
    nodes, edges = snapshot.get("nodes"), snapshot.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise PlotContractError("accepted cycle snapshot is malformed")
    return nodes, edges


def deadlock_figure(controls: Mapping[str, Any], prefix: Path) -> dict[str, Any]:
    _load_deps(); _style()
    phase1_trials = [run for run in controls["phase_runs"] if run["phase"] == "phase1"]
    phase1 = [run for run in phase1_trials if run.get("accepted_cycle")]
    phase2 = [run for run in controls["phase_runs"] if run["phase"] == "phase2"]
    if not phase1_trials or not phase2:
        raise PlotContractError("deadlock figure requires phase1 and phase2 observations")
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.1))
    graph = axes[0]
    if phase1:
        nodes, edges = _cycle_nodes_edges(phase1[0]["accepted_cycle"])
        angles = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
        positions = {
            node["thread_id"]: (math.cos(angle), math.sin(angle))
            for node, angle in zip(nodes, angles)
        }
        for node in nodes:
            x, y = positions[node["thread_id"]]
            graph.scatter([x], [y], s=680, color="#d9e8f5", edgecolor="#326891", zorder=3)
            graph.text(x, y, f"T{node['thread_id']}\na{node['attempt']}", ha="center", va="center", fontsize=7)
        for edge in edges:
            start = positions[edge["waiter_thread_id"]]
            end = positions[edge["holder_thread_id"]]
            graph.annotate(
                "", xy=end, xytext=start,
                arrowprops={"arrowstyle": "->", "color": "#b33c2e", "lw": 1.5, "shrinkA": 25, "shrinkB": 25},
            )
        graph.set_title("phase1: accepted persistent WFG cycle")
        graph.set_aspect("equal")
    else:
        graph.text(
            0.5, 0.5,
            f"No persistent WFG cycle observed\n0 of {len(phase1_trials)} phase1 trials",
            ha="center", va="center", transform=graph.transAxes, fontsize=8,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f2f2f2", "edgecolor": "#777777"},
        )
        graph.set_title("phase1: bounded cycle observation")
    graph.axis("off")
    conflicts = sum(int(run["phase2_counters"]["conflict_count"]) for run in phase2)
    failures = sum(int(run["phase2_counters"]["no_wait_failure_count"]) for run in phase2)
    paths: dict[str, int] = {}
    for run in phase2:
        for name, count in run["phase2_counters"]["acquisition_paths"].items():
            paths[str(name)] = paths.get(str(name), 0) + int(count)
    axes[1].axis("off")
    axes[1].text(
        0.5, 0.56,
        "phase2: no accepted cycle\n"
        f"6 bounded runs exited normally\nconflicts: {conflicts:,}\nNo-Wait failures: {failures:,}\n"
        f"acquisition paths: {json.dumps(paths, sort_keys=True)}",
        ha="center", va="center", transform=axes[1].transAxes, fontsize=8,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "#e8f3e8", "edgecolor": "#4d8b4d"},
    )
    axes[1].set_title("phase2: bounded No-Wait observation")
    fig.suptitle(
        "Instrumented deadlock observation at preregistered operating points\n"
        + _condition_caption(
            controls, blocks=3, records=(100, 1_000_000), skews=(0.0, 0.9),
            read_ratios=(50,), threads=(48,),
        ),
        fontsize=8.5,
    )
    _save_checked(fig, prefix)
    plt.close(fig)
    return {
        "phase1_source": ({
            "point": phase1[0]["point"], "trial": phase1[0]["trial"],
            "accepted_cycle": phase1[0]["accepted_cycle"],
        } if phase1 else None),
        "phase1_observation": {
            "trials": len(phase1_trials),
            "cycles_observed": len(phase1),
            "cycle_observation": f"{len(phase1)} of {len(phase1_trials)} phase1 trials",
        },
        "phase2": {"runs": len(phase2), "conflicts": conflicts, "no_wait_failures": failures, "paths": paths},
    }


def replication_signs(replication: Mapping[str, Any]) -> dict[str, Any]:
    runs = replication["performance_runs"]
    effects = {str(thread): paired_log_effect(runs, "B", "D", thread) for thread in THREADS}
    return {
        "effects": effects,
        "signs": {thread: (1 if value["mean_log_ratio"] > 0 else -1 if value["mean_log_ratio"] < 0 else 0) for thread, value in effects.items()},
        "claim_scope": "sign check only; no node variance estimate and no pooling",
    }


def validate_replication_independence(
    sweep: Mapping[str, Any], replication: Mapping[str, Any]
) -> None:
    primary = sweep.get("occasion")
    repeated = replication.get("occasion")
    if not isinstance(primary, Mapping) or not isinstance(repeated, Mapping):
        raise PlotContractError("sweep and replication occasion identities are required")
    equal_fields = [
        field for field in ("occasion_id", "pbs_jobid", "node")
        if primary.get(field) == repeated.get(field)
    ]
    if equal_fields:
        raise PlotContractError(
            f"replication must use a different occasion, PBS job, and node: equal={equal_fields}"
        )


def generate(
    sweep_path: Path, controls_path: Path | None, output_dir: Path,
    replication_path: Path | None = None,
) -> list[Path]:
    ensure_plot_host_allowed()
    sweep = load_receipt(sweep_path, "sweep")
    controls = load_receipt(controls_path, "controls") if controls_path else None
    replication = load_receipt(replication_path, "replication") if replication_path else None
    if replication is not None:
        validate_replication_independence(sweep, replication)
    output_dir.mkdir(parents=True, exist_ok=True)
    inputs = (
        [sweep_path]
        + ([controls_path] if controls_path else [])
        + ([replication_path] if replication_path else [])
    )
    outputs = []
    common_summary = {
        "saturation": {
            arm: saturation_point(sweep["performance_runs"], arm) for arm in ARMS
        },
        "paired_effects": {
            f"{arm_x}_vs_{arm_y}": {
                str(thread): paired_log_effect(
                    sweep["performance_runs"], arm_x, arm_y, thread
                )
                for thread in THREADS
            }
            for arm_x, arm_y in PAIRINGS
        },
    }
    makers = [
        ("ss2pl_scalability", scalability_figure, sweep),
        ("ss2pl_abort_rate", abort_figure, sweep),
        ("ss2pl_paired_effects", paired_figure, sweep),
    ]
    if controls is not None:
        makers.extend((
            ("ss2pl_controls", controls_figure, controls),
            ("ss2pl_deadlock", deadlock_figure, controls),
        ))
    replication_values = replication_signs(replication) if replication is not None else None
    if replication_values is not None:
        sweep_signs = {
            str(thread): (
                1 if common_summary["paired_effects"]["B_vs_D"][str(thread)]["mean_log_ratio"] > 0
                else -1 if common_summary["paired_effects"]["B_vs_D"][str(thread)]["mean_log_ratio"] < 0
                else 0
            )
            for thread in THREADS
        }
        replication_values["sweep_signs"] = sweep_signs
        replication_values["sign_matches_sweep"] = {
            thread: replication_values["signs"][thread] == sign
            for thread, sign in sweep_signs.items()
        }
    for stem, maker, document in makers:
        prefix = output_dir / stem
        values = maker(document, prefix)
        provenance_values = {"plot": values, "study_summary": common_summary}
        provenance_values["control_experiment_input"] = {
            "provided": controls is not None,
            "statement": (
                "Control experiment input was provided."
                if controls is not None
                else "Control experiment input was not provided; control figures were not generated."
            ),
        }
        if stem == "ss2pl_paired_effects" and replication_values is not None:
            provenance_values["replication_sign_check"] = replication_values
        conditions = _conditions(document)
        if stem == "ss2pl_deadlock":
            conditions.update({
                "records": [100, 1_000_000], "skews": [0.0, 0.9],
                "read_ratios": [50], "threads": [48],
            })
        if replication is not None:
            conditions["replication"] = {
                "occasion_id": replication["occasion"]["occasion_id"],
                "pbs_jobid": replication["occasion"]["pbs_jobid"],
                "node": replication["occasion"]["node"],
                "combination_rule": "not pooled",
            }
        provenance = _base_provenance(
            Path(__file__).name, inputs, conditions, provenance_values,
        )
        provenance_path = output_dir / f"{stem}.provenance.json"
        _atomic_json(provenance_path, provenance)
        outputs.extend([prefix.with_suffix(".png"), prefix.with_suffix(".pdf"), provenance_path])
    return outputs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", required=True, type=Path)
    parser.add_argument("--controls", type=Path)
    parser.add_argument("--replication", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        outputs = generate(
            args.sweep.resolve(strict=True),
            args.controls.resolve(strict=True) if args.controls else None,
            args.output_dir.resolve(),
            args.replication.resolve(strict=True) if args.replication else None,
        )
    except (OSError, ValueError, KeyError, PlotContractError) as exc:
        print(f"plot_ss2pl_lock_study: {exc}", file=sys.stderr)
        return 1
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
