#!/usr/bin/env python3
"""Reaggregate early-abort jobs and draw the five md_31 evidence figures."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics

from orchestrator.campaign.vhash_forwarding_prototype import abort_aggregate_jobs


SKEW_JOBS = ("s06", "s08", "s09", "s095")
MAIN_ARMS = ("stock", "E-hb", "E-max", "b", "c")
DOOMED_ARMS = ("E-hb", "E-max", "b", "c")
BACKOFF_ARMS = ("stock", "E-max", "stock-bo1", "E-max-bo1")
COLORS = {"stock": "#444444", "E-hb": "#D55E00", "E-max": "#0072B2",
          "b": "#009E73", "c": "#CC79A7", "stock-bo1": "#999933",
          "E-max-bo1": "#332288"}
LABELS = {"E-hb": "E-hb (shadow)", "E-max": "E-max (shadow)",
          "stock-bo1": "stock, BACK_OFF=1", "E-max-bo1": "E-max, BACK_OFF=1"}
T975_DF2 = 4.302652729911275


def ci95(values):
    """Small-sample t interval for the mean of three independent repetitions."""
    if len(values) != 3:
        raise ValueError("each plotted series needs exactly three repetitions")
    return T975_DF2 * statistics.stdev(values) / math.sqrt(3)


def check_figure_layout(fig):
    """Fail before saving when visible text is clipped or overlaps another label."""
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
        if (box.x0 < fig.bbox.x0 - 1 or box.y0 < fig.bbox.y0 - 1 or
                box.x1 > fig.bbox.x1 + 1 or box.y1 > fig.bbox.y1 + 1):
            raise ValueError("text outside figure: " + item.get_text())
        for prior, other in boxes:
            area = max(0, min(box.x1, other.x1) - max(box.x0, other.x0)) * \
                   max(0, min(box.y1, other.y1) - max(box.y0, other.y0))
            if area > 1:
                raise ValueError("text overlap: " + prior.get_text() + " / " + item.get_text())
        boxes.append((item, box))


def point(ax, x, values, color, *, divisor=1):
    values = [v / divisor for v in values]
    if len(values) != 3 or any(v is None or not math.isfinite(v) for v in values):
        raise ValueError("missing or nonfinite repetition value")
    ax.scatter([x - .025, x, x + .025], values, s=13, color=color, alpha=.55,
               zorder=3)
    ax.errorbar(x, statistics.mean(values), yerr=ci95(values), fmt="none",
                color=color, capsize=2, lw=.9, zorder=2)
    ax.plot(x, statistics.median(values), "D", color=color, ms=4, zorder=4)


def rows(data, job, arm, kind):
    result = data["cells"][job]["arms"][arm][kind]
    if sorted(row["rep"] for row in result) != [0, 1, 2]:
        raise ValueError(f"invalid reps: {job}/{arm}/{kind}")
    return sorted(result, key=lambda row: row["rep"])


def series(data, job, arm, kind, *keys):
    return [nested(row, keys) for row in rows(data, job, arm, kind)]


def nested(row, keys):
    for key in keys:
        row = row[key]
    return row


def legend(fig, arms, *, shadow=False, y=.925):
    from matplotlib.lines import Line2D

    handles = [Line2D([], [], color=COLORS[a], marker="D", ls="none",
                      label=LABELS.get(a, a) if shadow else
                      LABELS.get(a, a) if a.endswith("-bo1") else a)
               for a in arms]
    fig.legend(handles=handles, loc="upper center", ncol=len(arms),
               bbox_to_anchor=(.5, y), frameon=False)


def style_axis(ax, labels, ylabel, *, xlabel):
    ax.set_ylabel(ylabel, labelpad=14)
    ax.set_xlabel(xlabel)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlim(-.55, len(labels) - .45)
    ax.grid(axis="y", alpha=.2)


def draw_skew(data, *, gc):
    import matplotlib.pyplot as plt

    metrics = (("count", "gc", "lag_rts_mean_us", 1000, "Mean GC boundary lag (ms)"),
               ("count", "gc", "live_mean", 1000, "Mean live versions (thousands)")) if gc else (
               ("performance", None, "long_commit_per_s", 1, "Long tx commits / s"),
               ("performance", None, "long_attempt_per_s", 1, "Long tx attempts / s"),
               ("performance", None, "long_completion_rate", .01, "Long tx completion (%)"))
    fig, axes = plt.subplots(len(metrics), 1, figsize=(13, 5.2 if gc else 7.2))
    fig.subplots_adjust(left=.105, right=.97, top=.79, bottom=.11, hspace=.72)
    kind = "計器入り build の診断値" if gc else "計器なし build、記述値"
    fig.suptitle(("GC boundary and live versions" if gc else "Long tx progress") +
                 " · " + kind + "\n48 threads, 1M tuples, 50% reads, wait 10 ms, GC 10 µs",
                 y=.985, fontsize=11)
    legend(fig, MAIN_ARMS, y=.88)
    values = {}
    for ji, job in enumerate(SKEW_JOBS):
        values[job] = {}
        for ai, arm in enumerate(MAIN_ARMS):
            values[job][arm] = {}
            for ax, (source, parent, key, divisor, _) in zip(axes, metrics):
                path = (parent, key) if parent else (key,)
                vals = series(data, job, arm, source, *path)
                values[job][arm][key] = vals
                point(ax, ji + (ai - 2) * .14, vals, COLORS[arm], divisor=divisor)
    labels = [f"{data['cells'][job]['condition'][0]:g}" for job in SKEW_JOBS]
    for ax, (_, _, _, _, ylabel) in zip(axes, metrics):
        style_axis(ax, labels, ylabel, xlabel="Skew")
    return fig, values


def draw_doomed(data):
    import matplotlib.pyplot as plt

    fig, (left, right) = plt.subplots(1, 2, figsize=(16, 6.2),
                                      gridspec_kw={"width_ratios": (1, 1.12)})
    fig.subplots_adjust(left=.07, right=.98, top=.78, bottom=.16, wspace=.21)
    fig.suptitle("D reach and first detection · 計器入り build の診断値\n"
                 "48 threads, 1M tuples, 50% reads, wait 10 ms, GC 10 µs",
                 y=.985, fontsize=11)
    legend(fig, DOOMED_ARMS, shadow=True, y=.89)
    values = {"reach": {}, "histogram_s09": {}}
    for ji, job in enumerate(SKEW_JOBS):
        values["reach"][job] = {}
        for ai, arm in enumerate(DOOMED_ARMS):
            vals = series(data, job, arm, "count", "abort", "d_reach_rate")
            values["reach"][job][arm] = vals
            point(left, ji + (ai - 1.5) * .18, vals, COLORS[arm], divisor=.01)
    style_axis(left, [f"{data['cells'][j]['condition'][0]:g}" for j in SKEW_JOBS],
               "D reached / long tx attempts (%)", xlabel="Skew")
    hist_arms = ("E-hb", "b", "c")
    hists = {arm: series(data, "s09", arm, "count", "abort", "detect_hist")
             for arm in hist_arms}
    bins = [i for i in range(42) if any(sum(rep[i] for rep in hists[a])
                                       for a in hist_arms)]
    if not bins:
        raise ValueError("empty first-detection histogram")
    for ai, arm in enumerate(hist_arms):
        h = hists[arm]
        values["histogram_s09"][arm] = {"rep_counts": h,
                                       "sum_counts": [sum(rep[i] for rep in h) for i in range(42)]}
        for index, bin_index in enumerate(bins):
            x = index + (ai - 1) * .24
            summed = sum(rep[bin_index] for rep in h)
            right.bar(x, summed, width=.20, color=COLORS[arm], alpha=.22,
                      edgecolor=COLORS[arm], linewidth=.7)
            # Repetitions and their uncertainty use the same count scale as the sum.
            point(right, x, [rep[bin_index] for rep in h], COLORS[arm])
    right.set_xticks(range(len(bins)), [f"2^{i}" for i in bins])
    right.set_xlim(-.55, len(bins) - .45)
    right.set_xlabel("First detection since hold start (µs, log2 bin)")
    right.set_ylabel("Events per bin (bar: 3-rep sum; points: rep count)")
    right.grid(axis="y", alpha=.2)
    return fig, values


def draw_throughput(data):
    import matplotlib.pyplot as plt

    jobs = (*SKEW_JOBS, "focus")
    arms = ("E-hb", "E-max", "b", "c")
    fig, ax = plt.subplots(figsize=(13, 5.5))
    fig.subplots_adjust(left=.09, right=.98, top=.76, bottom=.20)
    fig.suptitle("Throughput / same-job stock median · 計器なし build、記述値\n"
                 "48 threads, 1M tuples, 50% reads; focus: wait 1 ms, GC 1000 µs",
                 y=.985, fontsize=11)
    legend(fig, arms, y=.86)
    values = {}
    for ji, job in enumerate(jobs):
        stock = statistics.median(series(data, job, "stock", "performance", "throughput_tps"))
        if stock <= 0:
            raise ValueError("nonpositive stock throughput")
        values[job] = {"stock_median_tps": stock}
        for ai, arm in enumerate(arms):
            vals = [v / stock for v in series(data, job, arm, "performance", "throughput_tps")]
            values[job][arm] = vals
            point(ax, ji + (ai - 1.5) * .18, vals, COLORS[arm])
    ax.axhline(1, color=COLORS["stock"], ls="--", lw=1)
    labels = [f"{j}\n{data['cells'][j]['condition'][0]:g}" for j in jobs]
    style_axis(ax, labels, "Throughput / stock median (ratio)", xlabel="Job / skew")
    return fig, values


def draw_focus_backoff(data):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 2, figsize=(15, 9.3))
    fig.subplots_adjust(left=.085, right=.98, top=.80, bottom=.095,
                        hspace=.73, wspace=.24)
    fig.suptitle("Focus and BACK_OFF controls · 48 threads, 1M tuples, 50% reads\n"
                 "Focus: skew 0.9, wait 1 ms, GC 1000 µs; backoff: skew 0.9, wait 10 ms, GC 10 µs",
                 y=.99, fontsize=11)
    legend(fig, (*MAIN_ARMS, "stock-bo1", "E-max-bo1"), y=.89)
    specs = ((axes[0, 0], "focus", MAIN_ARMS, "count", ("gc", "lag_rts_mean_us"),
              1000, "Mean GC boundary lag (ms)", "計器入り build の診断値"),
             (axes[1, 0], "focus", MAIN_ARMS, "performance", ("long_completion_rate",),
              .01, "Long tx completion (%)", "計器なし build、記述値"),
             (axes[0, 1], "backoff", BACKOFF_ARMS, "performance", ("long_completion_rate",),
              .01, "Long tx completion (%)", "計器なし build、記述値"),
             (axes[1, 1], "backoff", BACKOFF_ARMS, "performance", ("long_commit_per_s",),
              1, "Long tx commits / s", "計器なし build、記述値"),
             (axes[2, 1], "backoff", BACKOFF_ARMS, "performance", ("throughput_tps",),
              1000, "Throughput (thousand tx/s)", "計器なし build、記述値"))
    values = {"focus": {}, "backoff": {}}
    for ax, job, arms, source, path, divisor, ylabel, title in specs:
        ax.set_title(title, fontsize=9)
        for ai, arm in enumerate(arms):
            vals = series(data, job, arm, source, *path)
            values[job].setdefault(arm, {})[path[-1]] = vals
            point(ax, ai, vals, COLORS[arm], divisor=divisor)
        tick_labels = [LABELS.get(a, a).replace(", BACK_OFF=1", "\nBO=1")
                       .replace(" (shadow)", "") for a in arms]
        style_axis(ax, tick_labels, ylabel, xlabel="Policy / BACK_OFF")
        ax.tick_params(axis="x", labelsize=8)
    axes[2, 0].axis("off")
    return fig, values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aggregate", type=Path)
    parser.add_argument("raw", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True, help="output stem")
    args = parser.parse_args(argv)
    raw = [json.loads(path.read_text()) for path in args.raw]
    data = abort_aggregate_jobs(raw)
    if json.loads(json.dumps(data)) != json.loads(args.aggregate.read_text()):
        raise ValueError("aggregate differs from raw recomputation")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": ["DejaVu Sans", "Droid Sans Fallback"], "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42})
    inputs = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (args.aggregate, *args.raw)}
    script = Path(__file__).resolve()
    conditions = {name: {"skew": cell["condition"][0],
                         "wait_us": cell["condition"][1],
                         "gc_inter_us": cell["condition"][2]}
                  for name, cell in data["cells"].items()}
    figures = (("early-abort-gc", lambda: draw_skew(data, gc=True)),
               ("early-abort-long", lambda: draw_skew(data, gc=False)),
               ("early-abort-doomed", lambda: draw_doomed(data)),
               ("early-abort-throughput", lambda: draw_throughput(data)),
               ("early-abort-focus-backoff", lambda: draw_focus_backoff(data)))
    for name, make in figures:
        fig, values = make()
        check_figure_layout(fig)
        stem = args.output.with_name(args.output.name + "-" + name)
        stem.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(stem.with_suffix(".png"), dpi=200)
        fig.savefig(stem.with_suffix(".pdf"))
        plt.close(fig)
        provenance = {"campaign_id": "vhash-early-abort-policy-2026-09-30",
                      "figure": name, "generated_at": datetime.now(timezone.utc).isoformat(),
                      "inputs_sha256": inputs, "generator": str(script),
                      "generator_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                      "matplotlib_version": matplotlib.__version__,
                      "conditions": {"threads": 48, "tuples": 1000000, "rratio": 50,
                                     "ccbench_pin": raw[0]["ccbench_pin"],
                                     "environments": {job["job"]: job["hostname"] for job in raw},
                                     "jobs": conditions},
                      "verification_status": data["verification_status"],
                      "statistics": "3 rep points; diamond=rep median; 95% t CI for rep mean",
                      "major_values": values}
        stem.with_suffix(".provenance.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
        print(stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
