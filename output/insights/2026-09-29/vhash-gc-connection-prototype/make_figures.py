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

COLORS = {"stock": "#444444", "C": "#0072B2", "E-hb": "#D55E00", "E": "#009E73"}
METRICS = (("lag_rts_mean_us", "MinRts lag (ms)", 1000),
           ("live_mean", "Live versions (million)", 1000000),
           ("retention_mean_us", "Mean retention (ms)", 1000),
           ("success_rate", "E success / attempts (%)", .01))


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


def rep_value(rep, metric):
    if metric == "retention_mean_us":
        return rep["retention_sum_us"] / rep["retention_count"] if rep["retention_count"] else None
    if metric == "success_rate":
        return rep["success"] / rep["attempts"] if rep["attempts"] else None
    return rep[metric]


def make_overview(data):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    cells = {(cell["wait_us"], cell["skew"], cell["gc_inter_us"]): (key, cell)
             for key, cell in data["cells"].items() if cell["workload"] == "wait_after_reads"}
    conditions = ((1000, .9), (1000, 0), (10000, .9), (10000, 0))
    intervals = (10, 100, 1000)
    if set(cells) != {(wait, skew, gc) for wait, skew in conditions for gc in intervals}:
        raise ValueError("unexpected wait_after_reads grid")
    fig, axes = plt.subplots(4, 4, figsize=(20, 16), squeeze=False)
    fig.subplots_adjust(left=.075, right=.98, bottom=.07, top=.89, wspace=.34, hspace=.57)
    fig.suptitle("GC wait diagnostics · diagnostic values (checker: 0 cycles; upper bound indeterminate; not certified)"
                 " · 48 threads, 1M tuples, 50% reads", y=.985, fontsize=12)
    handles = [Line2D([], [], color=COLORS[arm], marker="D", label=arm)
               for arm in GC_ARMS]
    fig.legend(handles=handles, loc="upper center", ncol=4, bbox_to_anchor=(.5, .955), frameon=False)
    values = {}
    for row, (wait, skew) in enumerate(conditions):
        for col, (metric, ylabel, divisor) in enumerate(METRICS):
            ax = axes[row, col]
            ax.set_title(f"wait {wait // 1000} ms · skew {skew:g} · {ylabel}", fontsize=10)
            ax.set_ylabel(ylabel)
            ax.set_xlim(-.4, 2.4)
            ax.set_xticks(range(3), [str(gc) for gc in intervals])
            if row == 3:
                ax.set_xlabel("GC interval (µs)")
            if metric == "success_rate":
                ax.set_ylim(0, 105)
            for x, gc in enumerate(intervals):
                key, cell = cells[wait, skew, gc]
                values.setdefault(key, {})
                for arm_index, arm in enumerate(GC_ARMS):
                    if metric == "success_rate" and arm != "E":
                        continue
                    reps = cell["arms"][arm]["gc"]
                    raw_points = [rep_value(rep, metric) for rep in reps]
                    if any(v is None for v in raw_points):
                        raise ValueError(f"missing {metric}: {key} {arm}")
                    points = [v / divisor for v in raw_points]
                    values[key][arm + "/" + metric] = raw_points
                    offset = (arm_index - 1.5) * .14 if metric != "success_rate" else 0
                    center = x + offset
                    ax.scatter([center + (i - (len(points)-1)/2)*.025 for i in range(len(points))],
                               points, color=COLORS[arm], s=10, alpha=.55, zorder=3)
                    ax.errorbar(center, statistics.mean(points), yerr=ci95(points),
                                color=COLORS[arm], fmt="none", capsize=2, lw=.8)
                    ax.plot(center, statistics.median(points), marker="D", markersize=4,
                            color=COLORS[arm], zorder=4)
    check_figure_layout(fig, list(axes.flat))
    return fig, values


def make_mechanism(data):
    import matplotlib.pyplot as plt
    key = "wait_after_reads/wait=10000/skew=0/gc=10"
    cell = data["cells"][key]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    fig.subplots_adjust(left=.10, right=.98, bottom=.22, top=.76)
    fig.suptitle("GC boundary lag · diagnostic values (checker: 0 cycles; upper bound indeterminate; not certified)\n"
                 "wait 10 ms, skew 0, GC 10 µs", y=.97, fontsize=12)
    ax.set_xlabel("Time from first stored sample (ms)")
    ax.set_ylabel("MinRts lag (ms)")
    reps = {}
    first_below = {}
    for arm in ("stock", "E-hb", "E"):
        rep = next(r for r in cell["arms"][arm]["gc"] if r["rep"] == 0)
        series = rep["series"]
        if not series or rep["series_stride"] < 1:
            raise ValueError(f"missing sampled series: {arm}")
        first_below[arm] = next((t - series[0][0] for t, lag, _ in series if lag < 100000), None)
        if first_below[arm] is None:
            raise ValueError(f"lag never below 100 ms: {arm}")
        reps[arm] = rep
    start_us = max(first_below.values())
    end_us = start_us + 200000
    ax.set_xlim(start_us / 1000, end_us / 1000)
    ax.set_xticks(range(25, 201, 25))
    fig.text(.10, .045, "Startup samples outside the common 200 ms steady-state window are omitted.",
             fontsize=8)
    values = {}
    for arm in ("stock", "E-hb", "E"):
        rep = reps[arm]
        series = rep["series"]
        # t_us is the actual timestamp of each stored sample; the stride only
        # describes thinning and must never be multiplied into elapsed time.
        t0 = series[0][0]
        window = [(t - t0, lag) for t, lag, _live in series if start_us <= t - t0 <= end_us]
        if not window:
            raise ValueError(f"empty steady-state window: {arm}")
        values[arm] = {"series_stride": rep["series_stride"], "points_in_window": len(window),
                       "first_t_us": t0, "first_below_100ms_elapsed_us": first_below[arm],
                       "window_start_elapsed_us": start_us, "window_end_elapsed_us": end_us,
                       "first_window_elapsed_us": window[0][0], "last_elapsed_us": window[-1][0],
                       "first_lag_rts_us": window[0][1],
                       "window_lag_rts_us_min": min(lag for _, lag in window),
                       "window_lag_rts_us_max": max(lag for _, lag in window)}
        ax.plot([t / 1000 for t, _ in window], [lag / 1000 for _, lag in window],
                color=COLORS[arm], lw=1, label=arm)
    ax.legend(loc="upper right", ncol=3, frameon=False)
    check_figure_layout(fig, [ax])
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
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["DejaVu Sans", "Droid Sans Fallback"]
    figures = ((args.output, *make_overview(recomputed)),
               (args.output.with_name(args.output.name + "-mechanism"), *make_mechanism(recomputed)))
    inputs = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (args.aggregate, *args.raw)}
    for path, fig, values in figures:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path.with_suffix(".png"), dpi=200)
        fig.savefig(path.with_suffix(".pdf"))
        plt.close(fig)
        provenance = {"campaign_id": "vhash-gc-connection-prototype-2026-09-29",
                      "inputs": inputs, "conditions": {"threads": 48, "tuples": 1000000,
                      "skew": [0, .9], "rratio": 50, "environment": "not captured in raw jobs",
                      "ccbench_pin": raw[0]["ccbench_pin"], "value_bytes": raw[0]["value_bytes"]},
                      "major_values": values,
                      "verification_status": "diagnostic values; checker: 0 cycles; upper bound indeterminate; not certified",
                      "throughput": "omitted: instrumented build values are diagnostic, not throughput measurements",
                      "transformations": {
                          "overview": "rep values and median; 95% t CI of rep mean; lag and retention µs / 1000 = ms; live count / 1000000 = million; E success / attempts * 100 = percent",
                          "mechanism": "rep 0; for each arm find first stored sample with lag_rts_us < 100000; common start is maximum of those elapsed times; inclusive 200000 µs window from common start; actual stored t_us minus first stored t_us, divided by 1000 = ms; lag_rts_us / 1000 = ms; series_stride is thinning metadata, not a time multiplier"}}
        path.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
