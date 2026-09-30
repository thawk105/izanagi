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
    off_view_ticks = set()
    for axis in fig.axes:
        for coordinate in (axis.xaxis, axis.yaxis):
            lo, hi = sorted(coordinate.get_view_interval())
            for tick in coordinate.get_major_ticks() + coordinate.get_minor_ticks():
                if not lo <= tick.get_loc() <= hi:
                    off_view_ticks.update((tick.label1, tick.label2))
    for label in fig.findobj(Text):
        if label in off_view_ticks or not label.get_visible() or not label.get_text().strip():
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
        "disqualified_ks": payload.get("disqualified_arms", payload.get("disqualified_ks", [])),
        "caption": "Exploratory same-time comparison; short YCSB transactions; "
                   "48 threads, 1M tuples, skew 0.9, extime 3 s. "
                   "Dots show every paired-round ratio; bars show minimum to maximum; "
                   "markers show medians. No significance claim."
    }, indent=2, ensure_ascii=False) + "\n")


def _series(data, cells, arm):
    x, y, low, high, all_points = [], [], [], [], []
    for index, cell in enumerate(cells):
        value = data["cells"].get(cell, {}).get(str(arm))
        if value:
            points = [float(item["ratio"]) for item in value["points"]]
            center = statistics.median(points)
            x.append(index)
            y.append(center)
            low.append(center - min(points))
            high.append(max(points) - center)
            all_points.extend((index, point) for point in points)
    return x, y, [low, high], all_points


def _draw_series(ax, data, cells, arm, positions=None, **kwargs):
    x, y, err, points = _series(data, cells, arm)
    locate = (lambda i: positions[i]) if positions is not None else (lambda i: i)
    marker = {"B-k1": "D", "B-k8": "o", "post-k1": "s",
              "post-k8": "^", "stock": "x"}.get(str(arm).split("/")[0], "v")
    line = ax.errorbar([locate(i) for i in x], y, yerr=err,
                       marker=marker, linewidth=1, capsize=2, **kwargs)
    color = line[0].get_color()
    ax.scatter([locate(i) for i, _ in points], [value for _, value in points],
               color=color, s=9, alpha=.65, zorder=3)


def make_figures(data, source, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if data.get("schema") not in ("vhash-hot-aggregate/v1", "vhash-hot-aggregate/v2"):
        raise ValueError("unsupported aggregate schema")
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42})
    cell_names = list(data["cells"])
    arms = sorted({arm for cells in data["cells"].values() for arm in cells})
    if not arms:
        raise ValueError("no qualified performance arms")
    palette = {"B-k1": "tab:blue", "B-k8": "tab:cyan",
               "post-k1": "tab:orange", "post-k8": "tab:red",
               "stock": "black"}
    colors = {arm: palette.get(arm.split("/")[0], "tab:purple") for arm in arms}

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    for arm in arms:
        _draw_series(ax, data, cell_names, arm, label=arm, color=colors[arm])
    ax.axhline(1, linestyle="--", color="black", linewidth=.8, label="Cicada stock")
    ax.set(xticks=range(len(cell_names)), xticklabels=cell_names,
           ylabel="Throughput / same-round stock", title="Hot block size by workload")
    ax.tick_params(axis="x", rotation=50)
    ax.legend(ncol=len(arms) + 1, fontsize=7, loc="upper right")
    _save(fig, output / "fig-k", data, source)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for gc, line_style in ((10, "-"), (1000, "--"), (100000, ":")):
        for arm in arms:
            names = [f"ro{ro}-gc{gc}" for ro in (0, 50, 95)]
            _draw_series(ax, data, names, arm,
                         positions=[int(name.split("-")[0][2:]) for name in names],
                         label=f"{arm}, GC {gc} us", color=colors[arm],
                         linestyle=line_style)
    ax.axhline(1, linestyle="--", color="black", linewidth=.8)
    ax.set(xlabel="Requested read-only transactions (%)", ylabel="Throughput / stock",
           title="Gain by GC interval")
    ax.legend(fontsize=6, ncol=2)
    _save(fig, output / "fig-ro", data, source)
    plt.close(fig)

    fig, (ax, counter_ax) = plt.subplots(2, 1, figsize=(8, 8), constrained_layout=True)
    write_cells = [name for name in ("ro0-gc10", "ro0-gc1000", "ro0-gc100000", "rr5")
                   if name in data["cells"]]
    for arm in arms:
        _draw_series(ax, data, write_cells, arm, label=arm, color=colors[arm])
    ax.axhline(1, linestyle="--", color="black", linewidth=.8)
    ax.set(xticks=range(len(write_cells)), xticklabels=write_cells,
           ylabel="Throughput / stock", title="Update-heavy cells")
    ax.legend()
    # The COUNT schema is owned by the patch. A missing counter is explicit.
    bars = []
    for row in data.get("count", []):
        value = row.get("count") or {}
        if row.get("cell") not in write_cells:
            continue
        arm = row.get("arm", f"B-k{row.get('k')}")
        if arm == "stock":
            continue
        counters = row.get("post_count") if arm.startswith("post-") else value
        counters = counters or {}
        prefix = "publish" if arm.startswith("post-") else "install"
        wait = counters.get(prefix + "_wait_cycles_per_update_commit")
        hold = counters.get(prefix + "_hold_cycles_per_update_commit")
        bars.append((row["cell"], arm, wait, hold))
    if bars:
        positions = list(range(len(bars)))
        counter_ax.bar([x - .2 for x in positions],
                       [float(wait) if wait is not None else 0 for _, _, wait, _ in bars],
                       width=.4, label="wait", color="tab:purple")
        counter_ax.bar([x + .2 for x in positions],
                       [float(hold) if hold is not None else 0 for _, _, _, hold in bars],
                       width=.4, label="hold", color="tab:green")
        for x, (_, _, wait, hold) in enumerate(bars):
            for offset, value in ((-.2, wait), (.2, hold)):
                if value is None:
                    counter_ax.text(x + offset, 0, "NA", ha="center", va="bottom")
        counter_ax.set(xticks=range(len(bars)),
                       xticklabels=[f"{c} {arm}" for c, arm, _, _ in bars],
                       ylabel="Cycles / update commit")
        counter_ax.tick_params(axis="x", rotation=50)
        counter_ax.legend()
    else:
        counter_ax.text(.5, .5, "COUNT hot interval cycles / update commit unavailable",
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
