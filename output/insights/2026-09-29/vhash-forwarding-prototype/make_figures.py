#!/usr/bin/env python3
"""Plot raw Cicada forwarding diagnostics with input-bound provenance."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

WORKLOADS = ("normal", "many_ops", "wait_after_reads")
GC_VALUES = (10, 100, 1000)
FAILURES = ("read_mismatch", "write_constraint", "conflict", "ineligible")


def _area(a, b):
    return max(0, min(a.x1, b.x1)-max(a.x0, b.x0))*max(0, min(a.y1, b.y1)-max(a.y0, b.y0))


def _contains(a, b):
    return b.x0 >= a.x0-1 and b.y0 >= a.y0-1 and b.x1 <= a.x1+1 and b.y1 <= a.y1+1


def check_figure_layout(fig, axes):
    """Renderer-backed text and panel checks before either save."""
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for item in fig.findobj(Text):
        if not item.get_visible() or not item.get_text().strip():
            continue
        box = item.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if not _contains(fig.bbox, box):
            raise ValueError("text outside figure: " + item.get_text())
        if item.axes is not None and any(
                other is not item.axes
                and _area(item.axes.bbox, other.bbox) < .9 * item.axes.bbox.width * item.axes.bbox.height
                and _area(box, other.bbox) > 1 for other in fig.axes):
            raise ValueError("text enters neighboring panel: " + item.get_text())
        boxes.append((item, box))
    for i, (left, a) in enumerate(boxes):
        for right, b in boxes[i+1:]:
            if _area(a, b) > 1:
                raise ValueError("text overlap: " + left.get_text() + " / " + right.get_text())
    for ax in axes:
        if not _contains(fig.bbox, ax.get_tightbbox(renderer)):
            raise ValueError("axis decoration outside figure")


def _sum(rows, key):
    return sum(int(r.get(key, 0)) for r in rows)


def _maybe_sum(rows, key):
    return _sum(rows, key) if rows else None


def _ratios(cell, arm):
    series = cell.get("throughput", {})
    stock = {r["rep"]: r["value"] for r in series.get("stock", [])}
    other = {r["rep"]: r["value"] for r in series.get(arm, [])}
    return [other[n]/stock[n] for n in sorted(stock.keys() & other.keys()) if stock[n] > 0]


def _ci(values):
    if len(values) < 2:
        return None
    t = {1: 12.7062047364, 2: 4.3026527299}.get(len(values)-1)
    return t*statistics.stdev(values)/math.sqrt(len(values)) if t else None


def make_figure(data):
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams["font.family"] = ["DejaVu Sans", "Droid Sans Fallback"]
    fig, axs = plt.subplots(3, 4, figsize=(24, 15), constrained_layout=True)
    fig.get_layout_engine().set(h_pad=0.24, w_pad=0.18)
    fig.suptitle("Cicada forwarding · 未検証の診断値\n"
                 "48 threads · 1M tuples · skew 0.9 · read ratio 50 · max ops 10 · K=3",
                 fontsize=15)
    values = {}
    for row, workload in enumerate(WORKLOADS):
        cells = []
        for gc in GC_VALUES:
            cell = data["cells"].get(f"{workload}/gc={gc}/k=3", {})
            counts = cell.get("c_counters", [])
            attempts = _maybe_sum(counts, "attempts")
            cells.append({"attempts": attempts, "success": _maybe_sum(counts, "success"),
                          "failure_reasons": {key: _maybe_sum(counts, key) for key in FAILURES},
                          "c_ratios": _ratios(cell, "c"), "f_ratios": _ratios(cell, "f"),
                          "long_commits_c": _maybe_sum(cell.get("longtx", {}).get("c", []), "commits"),
                          "long_commits_f": _maybe_sum(cell.get("longtx", {}).get("f", []), "commits"),
                          "f_aborts": _maybe_sum(cell.get("f_counters", []), "f_aborts")})
        values[workload] = dict(zip(map(str, GC_VALUES), cells))
        x = np.arange(len(GC_VALUES))
        a, b, c, d = axs[row]
        rates = [v["success"]/v["attempts"] if v["attempts"] else float("nan") for v in cells]
        a.plot(x, rates, "o-", color="#177a65")
        a.set_ylim(0, 1.05)
        a.set_title(workload + " · C success / attempts")
        a.set_ylabel("success rate")
        a2 = a.twinx()
        a2.bar(x, [v["attempts"] if v["attempts"] is not None else float("nan")
                   for v in cells], alpha=.15, color="#177a65")
        a2.set_ylabel("attempts")
        bottom = np.zeros(len(GC_VALUES))
        for reason in FAILURES:
            heights = np.array([v["failure_reasons"][reason] if v["failure_reasons"][reason] is not None
                                else float("nan") for v in cells])
            b.bar(x, heights, bottom=bottom, label=reason)
            bottom += heights
        b.set_title("C failure reasons")
        if row == 0:
            b.legend(fontsize=7)
        c.axhline(1, color="black", linestyle="--", linewidth=1)
        for offset, arm, color in ((-.12, "c", "#177a65"), (.12, "f", "#bd5b23")):
            for j, v in enumerate(cells):
                points = v[arm + "_ratios"]
                if points:
                    c.scatter([j+offset+(n-1)*.025 for n in range(len(points))], points, s=12, color=color)
                    c.errorbar([j+offset], [statistics.mean(points)], yerr=_ci(points),
                               marker="D", color=color, capsize=3)
        c.set_title("throughput / stock · 3 rep")
        c.set_ylabel("paired ratio, 95% t CI")
        d.plot(x, [v["long_commits_c"] if v["long_commits_c"] is not None else float("nan")
                   for v in cells], "o-", label="C long commits")
        d.plot(x, [v["long_commits_f"] if v["long_commits_f"] is not None else float("nan")
                   for v in cells], "o-", label="F long commits")
        d2 = d.twinx()
        d2.plot(x, [v["f_aborts"] if v["f_aborts"] is not None else float("nan")
                    for v in cells], "s--", color="#bd5b23")
        d.set_title("long thread progress / F abort")
        d.set_ylabel("long commits")
        d2.set_ylabel("F aborts")
        if row == 0:
            d.legend(fontsize=7)
        for ax in (a, b, c, d):
            ax.set_xticks(x, [str(gc) for gc in GC_VALUES])
            ax.set_xlabel("GC interval (µs)")
    return fig, list(axs.flat), values


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("aggregate", type=Path)
    p.add_argument("raw", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    aggregate = json.loads(args.aggregate.read_text())
    raw = json.loads(args.raw.read_text())
    from orchestrator.campaign.vhash_forwarding_prototype import aggregate as aggregate_raw
    if aggregate_raw(raw)["cells"] != aggregate["cells"]:
        raise ValueError("aggregate does not match supplied raw records")
    fig, axes, values = make_figure(aggregate)
    check_figure_layout(fig, axes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix(".png"), dpi=200)
    fig.savefig(args.output.with_suffix(".pdf"))
    provenance = {"inputs": {str(f.resolve()): hashlib.sha256(f.read_bytes()).hexdigest()
                             for f in (args.aggregate, args.raw)},
                  "conditions": raw.get("conditions", {}), "major_values": values,
                  "verification_status": "未検証の診断値"}
    args.output.with_suffix(".provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
