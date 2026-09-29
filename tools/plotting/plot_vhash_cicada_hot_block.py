#!/usr/bin/env python3
"""Render exploratory Cicada hot block figures from an aggregate JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics


def _layout(fig):
    from matplotlib.text import Text

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for label in fig.findobj(Text):
        if not label.get_visible() or not label.get_text().strip():
            continue
        box = label.get_window_extent(renderer)
        if box.width == 0 or box.height == 0:
            continue
        if box.x0 < fig.bbox.x0 - 1 or box.y0 < fig.bbox.y0 - 1 or \
           box.x1 > fig.bbox.x1 + 1 or box.y1 > fig.bbox.y1 + 1:
            raise ValueError(f"figure text outside canvas: {label.get_text()}")
        for other, prior in boxes:
            x = min(box.x1, prior.x1) - max(box.x0, prior.x0)
            y = min(box.y1, prior.y1) - max(box.y0, prior.y0)
            if x > 1 and y > 1:
                raise ValueError(f"figure text overlap: {label.get_text()} / {other}")
        boxes.append((label.get_text(), box))
    for axis in fig.axes:
        box = axis.get_tightbbox(renderer)
        if box.x0 < fig.bbox.x0 - 1 or box.y0 < fig.bbox.y0 - 1 or \
           box.x1 > fig.bbox.x1 + 1 or box.y1 > fig.bbox.y1 + 1:
            raise ValueError("axes decoration outside canvas")


def _save(fig, path, payload, source):
    _layout(fig)
    for suffix in (".png", ".pdf"):
        fig.savefig(path.with_suffix(suffix), dpi=180)
    path.with_suffix(".provenance.json").write_text(json.dumps({
        "schema": "vhash-hot-figure-provenance/v1", "aggregate": str(source.resolve()),
        "aggregate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "pin": payload["pin"], "conditions": payload["conditions"],
        "figure": path.name, "plotted_values": payload["cells"],
        "disqualified_ks": payload["disqualified_ks"],
        "caption": "Exploratory same-time comparison; short YCSB transactions; "
                   "48 threads, 1M tuples, skew 0.9, extime 3 s. "
                   "Bars show 95% Student t confidence intervals for the paired-round mean."
    }, indent=2, ensure_ascii=False) + "\n")


def _series(data, cells, k):
    x, y, low, high = [], [], [], []
    for index, cell in enumerate(cells):
        value = data["cells"].get(cell, {}).get(str(k))
        if value:
            points = [float(item["ratio"]) for item in value["points"]]
            critical = {4: 3.182446, 6: 2.570582}.get(len(points))
            if critical is None:
                raise ValueError("expected four or six paired rounds for confidence interval")
            center = statistics.mean(points)
            radius = critical * statistics.stdev(points) / len(points) ** .5
            x.append(index)
            y.append(center)
            low.append(radius)
            high.append(radius)
    return x, y, [low, high]


def make_figures(data, source, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if data.get("schema") != "vhash-hot-aggregate/v1":
        raise ValueError("unsupported aggregate schema")
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42})
    cell_names = list(data["cells"])
    ks = sorted({int(k) for cells in data["cells"].values() for k in cells})
    if not ks:
        raise ValueError("no qualified performance arms")

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    for k in ks:
        x, y, err = _series(data, cell_names, k)
        ax.errorbar(x, y, yerr=err, marker="o", linewidth=1, capsize=2, label=f"K={k}")
    ax.axhline(1, linestyle="--", color="black", linewidth=.8, label="Cicada stock")
    ax.set(xticks=range(len(cell_names)), xticklabels=cell_names,
           ylabel="Throughput / same-round stock", title="Hot block size by workload")
    ax.tick_params(axis="x", rotation=50)
    ax.legend(ncol=len(ks) + 1, fontsize=7, loc="upper right")
    _save(fig, output / "fig-k", data, source)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for gc in (10, 1000, 100000):
        for k in ks:
            names = [f"ro{ro}-gc{gc}" for ro in (0, 50, 95)]
            x, y, err = _series(data, names, k)
            ax.errorbar([int(names[i].split("-")[0][2:]) for i in x], y,
                        yerr=err, marker="o", linewidth=1, capsize=2,
                        label=f"K={k}, GC {gc} us")
    ax.axhline(1, linestyle="--", color="black", linewidth=.8)
    ax.set(xlabel="Requested read-only transactions (%)", ylabel="Throughput / stock",
           title="Gain by GC interval")
    ax.legend(fontsize=6, ncol=2)
    _save(fig, output / "fig-ro", data, source)
    plt.close(fig)

    fig, (ax, counter_ax) = plt.subplots(2, 1, figsize=(8, 8), constrained_layout=True)
    write_cells = [name for name in ("ro0-gc10", "ro0-gc1000", "ro0-gc100000", "rr5")
                   if name in data["cells"]]
    for k in ks:
        x, y, err = _series(data, write_cells, k)
        ax.errorbar(x, y, yerr=err, marker="o", capsize=2, label=f"K={k}")
    ax.axhline(1, linestyle="--", color="black", linewidth=.8)
    ax.set(xticks=range(len(write_cells)), xticklabels=write_cells,
           ylabel="Throughput / stock", title="Update-heavy cells")
    ax.legend()
    # The COUNT schema is owned by the patch. A missing counter is explicit.
    bars = []
    for row in data.get("count", []):
        value = row.get("count") or {}
        cycles = value.get("install_hot_hold_cycles_per_commit")
        if cycles is not None and row.get("cell") in write_cells:
            bars.append((row["cell"], row["k"], float(cycles)))
    if bars:
        counter_ax.bar(range(len(bars)), [v for _, _, v in bars])
        counter_ax.set(xticks=range(len(bars)),
                       xticklabels=[f"{c} K{k}" for c, k, _ in bars],
                       ylabel="Hot interval cycles / commit")
        counter_ax.tick_params(axis="x", rotation=50)
    else:
        counter_ax.text(.5, .5, "COUNT hot interval cycles / commit unavailable",
                        ha="center", va="center", transform=counter_ax.transAxes)
        counter_ax.set(xticks=[], yticks=[])
    _save(fig, output / "fig-write", data, source)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aggregate", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    make_figures(json.loads(args.aggregate.read_text()), args.aggregate, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
