"""Render diagnostic Cicada J1 and J2 figures from raw runs and summary JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text

plt.rcParams["font.family"] = ["Droid Sans Fallback", "DejaVu Sans"]

from tools.plotting.plot_t2187_adaptive_consts import _contains, _intersection_area
from tools.vhash_cicada_tuning import model
from tools.vhash_cicada_tuning.driver import read_runs

NOTES = {"j1": "J1 探索値・正しさ未検証の診断値",
         "j2": "J2 確認値・正しさ未検証の診断値"}
TPS_PER_MTPS = 1_000_000


class FigureLayoutError(ValueError):
    pass


def check_figure_layout(fig, axes) -> None:
    """Use the existing bbox containment/intersection predicates on real artists."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    text_boxes = []
    panels = list(axes)
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if not _contains(fig.bbox, box, tolerance=1.0):
            raise FigureLayoutError(f"text leaves figure: {artist.get_text()!r}")
        if artist.axes is not None:
            for axis in panels:
                same_panel = axis.bbox.bounds == artist.axes.bbox.bounds
                if axis is not artist.axes and not same_panel and _intersection_area(box, axis.bbox) > 1.0:
                    raise FigureLayoutError(f"text enters another panel: {artist.get_text()!r}")
        text_boxes.append((artist, box))
    for i, (left, left_box) in enumerate(text_boxes):
        for right, right_box in text_boxes[i + 1:]:
            if _intersection_area(left_box, right_box) > 1.0:
                raise FigureLayoutError(f"text overlap: {left.get_text()!r} / {right.get_text()!r}")


def _estimate(values):
    if not values:
        raise ValueError("empty figure cell")
    return st.median(values)


def _groups(rows, stage):
    grouped = defaultdict(list)
    for row in rows:
        if row["stage"] != stage or row["perf"] is not False or row.get("exit_code") != 0:
            continue
        key = (row["workload"], row["genome"], row["gc_inter_us"])
        grouped[key].append(row)
    return grouped


def _missing(summary, measured):
    return {w: summary.get("workload_status", {}).get(w, {}).get("reason", "not_selected")
            for w in model.WORKLOADS if w not in measured}


def _caption(summary, measured):
    missing = _missing(summary, measured)
    return "Missing workloads: " + (", ".join(f"{w} ({reason})" for w, reason in missing.items())
                                    if missing else "none")


def _plot_data(rows, summary, stage):
    """Keep only measured conditions bound to the analyzed summary."""
    raw = _groups(rows, stage)
    listed = summary.get("condition_medians", {}).get(stage, {})
    groups = {}
    missing = []
    for (w, genome, gc), group in raw.items():
        for n in sorted({r["records"] for r in group}):
            key = f"{w}|{genome}|{gc}|{n}"
            if key in listed:
                groups[(w, genome, gc, n)] = [r for r in group if r["records"] == n]
            else:
                missing.append({"workload": w, "genome": genome, "gc_inter_us": gc,
                                "records": n, "reason": "summary_missing"})
    for (w, genome, gc, n) in list(groups):
        if stage == "j2" and n != summary.get("calibration", {}).get(w, {}).get("records"):
            del groups[(w, genome, gc, n)]
    # Summary-only cells cannot be plotted either. Keep their exact condition keys.
    available = {f"{w}|{g}|{gc}|{n}" for w, g, gc, n in groups}
    for key in listed:
        if key not in available:
            missing.append({"condition": key, "reason": "raw_missing"})
    return groups, missing


def _j1_missing(groups, measured):
    order = [model.canonical(g) for g in model.genomes()]
    present = {g for _, g, _, _ in groups}
    missing_genomes = [g for g in order if g not in present]
    missing_cells = []
    for w in measured:
        records = {n for ww, _, _, n in groups if ww == w}
        for genome in order:
            if genome not in present:
                continue
            for gc in ((10, 100, 1000) if w == "W2" else (10,)):
                if not any((w, genome, gc, n) in groups for n in records):
                    missing_cells.append({"workload": w, "genome": genome, "gc_inter_us": gc})
    return missing_genomes, missing_cells


def make_j1_figure(rows, summary):
    groups, _ = _plot_data(rows, summary, "j1")
    measured = [w for w in model.WORKLOADS if any(key[0] == w for key in groups)]
    if not measured:
        raise ValueError("no measured J1 workloads")
    missing_genomes, _ = _j1_missing(groups, measured)
    order = [model.canonical(g) for g in model.genomes()]
    fig, axes = plt.subplots(len(measured), 1, figsize=(17, 3 * len(measured) + 1), squeeze=False)
    fig.subplots_adjust(left=0.07, right=0.87, top=0.89, bottom=0.11, hspace=0.75)
    for axis, w in zip(axes[:, 0], measured):
        records = {n for ww, _, _, n in groups if ww == w}
        if len(records) != 1:
            raise ValueError(f"J1 records ambiguous for {w}")
        gcs = (10, 100, 1000) if w == "W2" else (10,)
        ratio_axis = axis.twinx()
        for gc in gcs:
            points = [(i, genome, groups[(w, genome, gc, next(iter(records)))])
                      for i, genome in enumerate(order)
                      if (w, genome, gc, next(iter(records))) in groups]
            x = [i for i, _, _ in points]
            estimates = [_estimate([r["throughput_tps"] for r in samples])
                         for _, _, samples in points]
            offset = {10: -0.22, 100: 0, 1000: 0.22}.get(gc, 0)
            width = 0.22 if len(gcs) > 1 else 0.65
            axis.bar([v + offset for v in x], [v / TPS_PER_MTPS for v in estimates],
                     width, label=f"GC {gc} µs")
            ratios = []
            ratio_x = []
            for i, genome, samples in points:
                paired = []
                for sample in samples:
                    controls = [r["throughput_tps"] for r in groups.get(
                                (w, model.canonical(model.CONTROL), gc, next(iter(records))), [])
                                if r["job_id"] == sample["job_id"]]
                    if controls:
                        paired.append(sample["throughput_tps"] / st.median(controls))
                if paired:
                    ratio_x.append(i)
                    ratios.append(_estimate(paired))
            ratio_axis.plot(ratio_x, ratios, linewidth=0.8, marker=".", markersize=2, alpha=0.6)
        control = order.index(model.canonical(model.CONTROL))
        axis.axvline(control, linestyle="--", color="black", linewidth=0.8)
        axis.set_title(f"{w}: 48 threads, N={next(iter(records)):,}, skew 0.9", fontsize=10)
        axis.set_ylabel("median throughput [Mtps]")
        ratio_axis.set_ylabel("median job control ratio", fontsize=8)
        axis.set_xlim(-0.8, 23.8)
        axis.set_xticks(list(range(0, 24, 2)), [str(i) for i in range(0, 24, 2)])
        axis.legend(loc="upper left", fontsize=8)
    axes[-1, 0].set_xlabel("canonical genome index (control dashed)")
    fig.suptitle(f"Cicada J1: absolute throughput and paired control ratios | {NOTES['j1']}", fontsize=14)
    fig.text(0.5, 0.025, f"{_caption(summary, measured)} | J1 で測れなかった genome: "
             f"{len(missing_genomes)} 件 (詳細は一次資料)", ha="center", fontsize=9)
    return fig, list(fig.axes)


def make_j2_figure(rows, summary):
    groups, _ = _plot_data(rows, summary, "j2")
    measured = [w for w in model.WORKLOADS if any(key[0] == w for key in groups)]
    if not measured:
        raise ValueError("no measured J2 workloads")
    groups = {key: group for key, group in groups.items() if key[0] in measured}
    fig, axes = plt.subplots(len(measured), 1, figsize=(12, 3 * len(measured) + 1), squeeze=False)
    fig.subplots_adjust(left=0.09, right=0.76, top=0.89, bottom=0.11, hspace=0.7)
    for axis, w in zip(axes[:, 0], measured):
        keys = sorted({(g, gc) for ww, g, gc, _ in groups if ww == w})
        if not keys:
            raise ValueError(f"J2 workload missing: {w}")
        genomes = sorted({g for g, _ in keys})
        records = {n for ww, _, _, n in groups if ww == w}
        if len(records) != 1:
            raise ValueError(f"J2 records ambiguous for {w}")
        for i, genome in enumerate(genomes):
            gcs = sorted(gc for g, gc in keys if g == genome)
            values = [_estimate([r["throughput_tps"] for r in
                                 groups[(w, genome, gc, next(iter(records)))]]) for gc in gcs]
            label = "control" if genome == model.canonical(model.CONTROL) else f"candidate {i + 1}"
            axis.plot(gcs, [v / TPS_PER_MTPS for v in values], marker="o", label=label)
        axis.set_xscale("log")
        axis.set_title(f"{w}: 48 threads, N={next(iter(records)):,}, skew 0.9", fontsize=10)
        axis.set_ylabel("median throughput [Mtps]")
        axis.set_xticks(sorted({gc for _, gc in keys}))
        axis.set_xticklabels([str(gc) for gc in sorted({gc for _, gc in keys})])
        axis.legend(loc="upper left", bbox_to_anchor=(1.22, 1), fontsize=8)
    axes[-1, 0].set_xlabel("gc_inter_us [µs], logarithmic")
    fig.suptitle(f"Cicada J2 GC response | {NOTES['j2']}", fontsize=14)
    fig.text(0.5, 0.025, _caption(summary, measured), ha="center", fontsize=9)
    return fig, list(axes[:, 0]) + [a for a in fig.axes if a not in axes[:, 0]]


def publish(fig, axes, prefix: Path, rows_path: list[Path], summary_path: Path,
            figure: str, rows, summary) -> None:
    check_figure_layout(fig, axes)
    groups, unavailable = _plot_data(rows, summary, figure)
    measured = [w for w in model.WORKLOADS if any(key[0] == w for key in groups)]
    missing_genomes = []
    missing_cells = []
    if figure == "j1":
        missing_genomes, missing_cells = _j1_missing(groups, measured)
    else:
        for w in measured:
            genomes = {g for ww, g, _, _ in groups if ww == w}
            gcs = {gc for ww, _, gc, _ in groups if ww == w}
            records = {n for ww, _, _, n in groups if ww == w}
            for genome in sorted(genomes):
                for gc in sorted(gcs):
                    if not any((w, genome, gc, n) in groups for n in records):
                        missing_cells.append({"workload": w, "genome": genome, "gc_inter_us": gc})
    cells = {}
    for (workload, genome, gc, n), group in sorted(groups.items()):
        selected = [r["throughput_tps"] for r in group]
        cells[f"{workload}|{genome}|{gc}|{n}"] = {
            "median_tps": _estimate(selected),
            "median_maxrss_kb": st.median(r["maxrss_kb"] for r in group),
            "n_reps": len(selected)}
    provenance = {"figure": figure, "diagnostic_only": True, "correctness_verified": False,
                  "throughput_axis": {"unit": "Mtps", "source_unit": "tps",
                                      "tps_per_Mtps": TPS_PER_MTPS,
                                      "conversion": "plotted_Mtps = median_tps / tps_per_Mtps"},
                  "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in [*rows_path, summary_path]},
                  "conditions": {"threads": 48, "skew": "0.9", "workloads": measured},
                  "caption": (_caption(summary, measured) +
                              (f" | J1 で測れなかった genome: {len(missing_genomes)} 件 (詳細は一次資料)"
                               if figure == "j1" else "")),
                  "missing_workloads": _missing(summary, measured),
                  "missing_genome_count": len(missing_genomes), "missing_genomes": missing_genomes,
                  "missing_cells": missing_cells, "unavailable_conditions": unavailable,
                  "raw_run_count": len(rows), "raw_aggregates": cells, "summary": summary}
    prefix.parent.mkdir(parents=True, exist_ok=True)
    if any(Path(str(prefix) + suffix).exists() for suffix in (".png", ".pdf", ".provenance.json")):
        raise FileExistsError(prefix)
    fig.savefig(str(prefix) + ".png", dpi=180)
    fig.savefig(str(prefix) + ".pdf")
    Path(str(prefix) + ".provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, nargs="+", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--out-prefix", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = json.loads(args.summary.read_text())
    if summary.get("schema") != "vhash-cicada-diagnostic/v1":
        raise ValueError("summary schema mismatch")
    if Counter(str(p.resolve()) for p in args.runs) != Counter(
            str(Path(p).resolve()) for p in summary.get("input_runs", [])):
        raise ValueError("runs differ from analyzed summary input_runs")
    rows = read_runs(args.runs)
    for name, builder in (("j1", make_j1_figure), ("j2", make_j2_figure)):
        fig, axes = builder(rows, summary)
        try:
            publish(fig, axes, Path(str(args.out_prefix) + f"-{name}"),
                    args.runs, args.summary, name, rows, summary)
        finally:
            plt.close(fig)


if __name__ == "__main__":
    main()
