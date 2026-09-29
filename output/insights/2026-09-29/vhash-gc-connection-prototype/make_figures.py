#!/usr/bin/env python3
"""Recompute GC aggregates from raw jobs and draw wait-condition diagnostics."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
from orchestrator.campaign.vhash_forwarding_prototype import gc_aggregate_jobs, GC_ARMS

METRICS = (("lag_rts_mean_us", "MinRts lag (µs)"),
           ("live_mean", "Logical live versions (count)"),
           ("retention_p50_upper_us", "Retention p50 bucket upper (µs)"))


def ci95(values):
    if len(values) < 2:
        return 0.0
    t = {2: 12.7062047364, 3: 4.3026527299}.get(len(values), 2.0)
    return t * statistics.stdev(values) / math.sqrt(len(values))


def check_figure_layout(fig, axes):
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
        if box.x0 < fig.bbox.x0-1 or box.y0 < fig.bbox.y0-1 or \
                box.x1 > fig.bbox.x1+1 or box.y1 > fig.bbox.y1+1:
            raise ValueError("text outside figure: " + item.get_text())
        for prior, other in boxes:
            overlap = max(0, min(box.x1, other.x1)-max(box.x0, other.x0)) * \
                      max(0, min(box.y1, other.y1)-max(box.y0, other.y0))
            if overlap > 1:
                raise ValueError("text overlap: " + prior.get_text() + " / " + item.get_text())
        boxes.append((item, box))
    for ax in axes:
        box = ax.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            raise ValueError("empty subplot")


def make_figure(data):
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["DejaVu Sans", "Droid Sans Fallback"]
    selected = [(key, cell) for key, cell in sorted(data["cells"].items())
                if cell["workload"] == "wait_after_reads"]
    if not selected:
        raise ValueError("no wait_after_reads cells")
    fig, axes = plt.subplots(len(selected), 4, figsize=(18, max(4, 3.4 * len(selected))),
                             squeeze=False, constrained_layout=True)
    fig.suptitle("Cicada GC · 未検証の診断値 · 48 threads, 1M tuples, zipf 0.9, read 50%")
    values = {}
    for row, (key, cell) in enumerate(selected):
        values[key] = {}
        for col, (metric, ylabel) in enumerate((*METRICS, ("success", "E events (count)"))):
            ax = axes[row][col]
            for index, arm in enumerate(GC_ARMS):
                reps = cell["arms"][arm]["gc"]
                if metric == "success" and arm != "E":
                    continue
                if metric == "success":
                    for offset, field in ((-.18, "requests"), (0, "attempts"), (.18, "success")):
                        points = [v[field] for v in reps]
                        values[key]["E/" + field] = points
                        ax.scatter([index + offset + (i-1)*.025 for i in range(len(points))], points, s=12)
                        ax.errorbar(index + offset, statistics.mean(points), yerr=ci95(points),
                                    fmt="o", capsize=3, label=field)
                    continue
                points = [v[metric] for v in reps if v[metric] is not None]
                if not points:
                    continue
                values[key][arm + "/" + metric] = points
                ax.scatter([index + (i-(len(points)-1)/2)*.05 for i in range(len(points))], points, s=14)
                ax.errorbar(index, statistics.mean(points), yerr=ci95(points), fmt="D", capsize=3)
            ax.set_xticks(range(4), GC_ARMS)
            ax.set_xlim(-.5, 3.5)
            ax.set_ylabel(ylabel)
            ax.set_title(f"wait {cell['wait_us']} µs · GC {cell['gc_inter_us']} µs")
            if metric == "success":
                ax.legend(fontsize=7)
    check_figure_layout(fig, list(axes.flat))
    return fig, values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aggregate", type=Path)
    parser.add_argument("raw", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw = [json.loads(path.read_text()) for path in args.raw]
    recomputed = gc_aggregate_jobs(raw)
    stored = json.loads(args.aggregate.read_text())
    if recomputed != stored:
        raise ValueError("aggregate differs from raw recomputation")
    fig, values = make_figure(recomputed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix(".png"), dpi=200)
    fig.savefig(args.output.with_suffix(".pdf"))
    import matplotlib.pyplot as plt
    plt.close(fig)
    provenance = {"inputs": {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (args.aggregate, *args.raw)},
                  "conditions": {"threads": 48, "tuples": 1000000, "zipf": .9, "rratio": 50},
                  "major_values": values, "verification_status": "未検証の診断値"}
    args.output.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
