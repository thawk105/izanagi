#!/usr/bin/env python3
"""Recompute target-policy aggregates from raw jobs and draw diagnostic figures."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from orchestrator.campaign.vhash_forwarding_prototype import target_aggregate_jobs

COLORS = {"stock": "#444444", "C-min": "#0072B2", "C-max": "#56B4E9",
          "C-partial": "#009E73", "C-partial-once": "#CC79A7", "F": "#E69F00",
          "E-hb": "#D55E00", "E-now": "#009E73", "E-max": "#0072B2",
          "E-max-once": "#CC79A7"}


def ci95(values):
    if len(values) < 2:
        return 0
    t = {2: 12.7062047364, 3: 4.3026527299}.get(len(values), 2.0)
    return t * statistics.stdev(values) / math.sqrt(len(values))


def check_figure_layout(fig):
    """Reject clipped or overlapping text before saving."""
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
            overlap = max(0, min(box.x1, other.x1) - max(box.x0, other.x0)) * \
                      max(0, min(box.y1, other.y1) - max(box.y0, other.y0))
            if overlap > 1:
                raise ValueError("text overlap: " + prior.get_text() + " / " + item.get_text())
        boxes.append((item, box))


def _point(ax, x, values, color, *, divisor=1):
    values = [v / divisor for v in values if v is not None]
    if not values:
        return None
    ax.scatter([x + .035 * (i - (len(values) - 1) / 2) for i in range(len(values))],
               values, color=color, s=11, alpha=.55)
    ax.errorbar(x, statistics.mean(values), yerr=ci95(values), fmt="none",
                color=color, capsize=2, lw=.8)
    ax.plot(x, statistics.median(values), marker="D", color=color, markersize=4)
    return values


def _cells(data, workload):
    return [(key, cell) for key, cell in sorted(data["cells"].items())
            if cell["workload"] == workload]


def make_success(data):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    cells = _cells(data, "wait_after_reads")
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    fig.subplots_adjust(left=.08, right=.98, top=.84, bottom=.18, hspace=.9)
    fig.suptitle("Forwarding requests and outcomes · 48 threads, 1M tuples, 50% reads · diagnostic",
                 y=.97, fontsize=12)
    arms = ("E-hb", "E-now", "E-max", "E-max-once")
    fig.legend(handles=[Line2D([], [], color=COLORS[a], marker="D", label=a) for a in arms],
               loc="upper center", ncol=4, bbox_to_anchor=(.5, .92), frameon=False)
    values = {}
    for index, (key, cell) in enumerate(cells):
        values[key] = {}
        for ai, arm in enumerate(arms):
            rows = cell["arms"][arm]["count"]
            rates = [r["e"]["success_rate"] for r in rows]
            reasons = [sum(r["e"]["failure_reasons_per_request"].values())
                       if all(v is not None for v in r["e"]["failure_reasons_per_request"].values())
                       else None for r in rows]
            values[key][arm] = {"success_per_request": rates, "failure_per_request": reasons}
            x = index + (ai - 1.5) * .16
            _point(axes[0], x, rates, COLORS[arm], divisor=.01)
            _point(axes[1], x, reasons, COLORS[arm], divisor=.01)
    labels = [f"{c['wait_us']//1000}/{c['skew']:g}/{c['gc_inter_us']}" for _, c in cells]
    for ax, label in zip(axes, ("Success / requests (%)", "Attempt failures / requests (%)")):
        ax.set_ylabel(label)
        ax.set_xticks(range(len(cells)), labels, fontsize=8)
        ax.set_xlim(-.5, len(cells) - .5)
        ax.grid(axis="y", alpha=.2)
    check_figure_layout(fig)
    return fig, values


def make_gc(data):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    cells = _cells(data, "wait_after_reads")
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    fig.subplots_adjust(left=.08, right=.98, top=.84, bottom=.18, hspace=.9)
    fig.suptitle("GC boundary and live versions · 48 threads, 1M tuples, 50% reads · diagnostic",
                 y=.97, fontsize=12)
    arms = ("E-hb", "E-now", "E-max", "E-max-once")
    fig.legend(handles=[Line2D([], [], color=COLORS[a], marker="D", label=a) for a in arms],
               loc="upper center", ncol=4, bbox_to_anchor=(.5, .92), frameon=False)
    values = {}
    for index, (key, cell) in enumerate(cells):
        values[key] = {}
        for ai, arm in enumerate(arms):
            rows = cell["arms"][arm]["count"]
            lag = [r["gc"]["lag_rts_mean_us"] for r in rows]
            live = [r["gc"]["live_mean"] for r in rows]
            values[key][arm] = {"lag_rts_mean_us": lag, "live_mean": live}
            x = index + (ai - 1.5) * .16
            _point(axes[0], x, lag, COLORS[arm], divisor=1000)
            _point(axes[1], x, live, COLORS[arm], divisor=1000000)
    labels = [f"{c['wait_us']//1000}/{c['skew']:g}/{c['gc_inter_us']}" for _, c in cells]
    for ax, label in zip(axes, ("Mean MinRts lag (ms)", "Live versions (million)")):
        ax.set_ylabel(label)
        ax.set_xticks(range(len(cells)), labels, fontsize=8)
        ax.set_xlim(-.5, len(cells) - .5)
        ax.grid(axis="y", alpha=.2)
    check_figure_layout(fig)
    return fig, values


def make_failure_reasons(data):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    cells = _cells(data, "wait_after_reads")
    reasons = ("read_mismatch", "write_constraint", "conflict", "ineligible",
               "no_room", "once_skipped", "overflow")
    arms = ("E-hb", "E-now", "E-max", "E-max-once")
    fig, axes = plt.subplots(4, 2, figsize=(18, 16))
    fig.subplots_adjust(left=.07, right=.98, top=.92, bottom=.10, hspace=.75, wspace=.20)
    fig.suptitle("Failure reasons / requests · E policies · 48 threads, 1M tuples · diagnostic",
                 y=.985, fontsize=12)
    fig.legend(handles=[Line2D([], [], color=COLORS[a], marker="D", label=a) for a in arms],
               loc="upper center", ncol=4, bbox_to_anchor=(.5, .955), frameon=False)
    values = {}
    labels = [f"{c['wait_us']//1000}/{c['skew']:g}/{c['gc_inter_us']}" for _, c in cells]
    for ri, reason in enumerate(reasons):
        ax = axes.flat[ri]
        for ci, (key, cell) in enumerate(cells):
            values.setdefault(key, {})
            for ai, arm in enumerate(arms):
                points = [r["e"]["failure_reasons_per_request"][reason]
                          for r in cell["arms"][arm]["count"]]
                values[key].setdefault(arm, {})[reason] = points
                _point(ax, ci + (ai - 1.5) * .16, points, COLORS[arm], divisor=.01)
        ax.set_title(reason.replace("_", " "), fontsize=9)
        ax.set_ylabel("Requests (%)")
        ax.set_xticks(range(len(cells)), labels, fontsize=7)
        ax.set_xlim(-.5, len(cells)-.5)
        ax.grid(axis="y", alpha=.2)
    axes.flat[-1].axis("off")
    check_figure_layout(fig)
    return fig, values


def make_many_ops(data):
    import matplotlib.pyplot as plt
    cells = _cells(data, "many_ops")
    fig, axes = plt.subplots(3, 1, figsize=(13, 12))
    fig.subplots_adjust(left=.11, right=.98, top=.90, bottom=.12, hspace=.55)
    fig.suptitle("Many ops · long versus ordinary threads · 48 threads, 1M tuples · diagnostic",
                 y=.97, fontsize=12)
    values = {}
    for index, (key, cell) in enumerate(cells):
        values[key] = {}
        for ai, arm in enumerate(("C-min", "C-max", "C-partial", "C-partial-once")):
            rows = cell["arms"][arm]["count"]
            rates = {group: [r["c_by_thread"][group]["success_rate"] for r in rows]
                     for group in ("long", "normal")}
            values[key][arm] = rates
            _point(axes[0], index + (ai - 1.5) * .18, rates["long"], COLORS[arm], divisor=.01)
            _point(axes[1], index + (ai - 1.5) * .18, rates["normal"], COLORS[arm], divisor=.01)
        for arm in ("stock", "F"):
            rows = cell["arms"][arm]["performance"]
            completion = []
            for row in rows:
                long_rows = [r for r in row["longtx"]["threads"] if r["long"]]
                commits = sum(r["commits"] for r in long_rows)
                aborts = sum(r["aborts"] for r in long_rows)
                completion.append(commits / (commits + aborts) if commits + aborts else None)
            values[key][arm] = {"long_completion": completion}
            _point(axes[2], index + (-.10 if arm == "stock" else .10),
                   completion, COLORS[arm], divisor=.01)
    labels = [f"skew {c['skew']:g} / GC {c['gc_inter_us']}µs" for _, c in cells]
    for ax, label in zip(axes, ("Long thread success / triggers (%)",
                                "Ordinary thread success / triggers (%)",
                                "Long tx completion (%) · stock and F")):
        ax.set_ylabel(label)
        ax.set_xticks(range(len(cells)), labels, rotation=20, ha="right")
        ax.set_xlim(-.5, len(cells) - .5)
        ax.grid(axis="y", alpha=.2)
    check_figure_layout(fig)
    return fig, values


def make_throughput(data):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    cells = sorted(data["cells"].items())
    fig, ax = plt.subplots(figsize=(17, 7))
    fig.subplots_adjust(left=.08, right=.98, top=.83, bottom=.25)
    fig.suptitle("Throughput / stock · uninstrumented builds · descriptive only · 48 threads, 1M tuples",
                 y=.97, fontsize=12)
    arms = tuple(a for a in COLORS if a != "stock")
    fig.legend(handles=[Line2D([], [], color=COLORS[a], marker="D", label=a) for a in arms],
               loc="upper center", ncol=5, bbox_to_anchor=(.5, .91), frameon=False)
    values = {}
    for index, (key, cell) in enumerate(cells):
        stock = cell["arms"]["stock"]["throughput_median_tps"]
        values[key] = {}
        present = [arm for arm in arms if arm in cell["arms"]]
        for ai, arm in enumerate(present):
            points = [r["throughput_tps"] / stock for r in cell["arms"][arm]["performance"]]
            values[key][arm] = points
            _point(ax, index + (ai - (len(present)-1)/2) * .10, points, COLORS[arm])
    ax.axhline(1, color=COLORS["stock"], ls="--", lw=1)
    ax.set_ylabel("Throughput / stock")
    ax.set_xticks(range(len(cells)), [k.replace("/", "\n") for k, _ in cells], fontsize=7)
    ax.set_xlim(-.5, len(cells) - .5)
    ax.grid(axis="y", alpha=.2)
    check_figure_layout(fig)
    return fig, values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aggregate", type=Path)
    parser.add_argument("raw", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw = [json.loads(path.read_text()) for path in args.raw]
    data = target_aggregate_jobs(raw)
    if data != json.loads(args.aggregate.read_text()):
        raise ValueError("aggregate differs from raw recomputation")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["DejaVu Sans", "Droid Sans Fallback"]
    inputs = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (args.aggregate, *args.raw)}
    for suffix, make in (("success", make_success), ("reasons", make_failure_reasons),
                         ("gc", make_gc),
                         ("many-ops", make_many_ops), ("throughput", make_throughput)):
        fig, values = make(data)
        path = args.output.with_name(args.output.name + "-" + suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path.with_suffix(".png"), dpi=200)
        fig.savefig(path.with_suffix(".pdf"))
        plt.close(fig)
        provenance = {"campaign_id": "vhash-forwarding-target-policy-2026-09-29",
                      "inputs": inputs, "conditions": {"threads": 48, "tuples": 1000000,
                      "rratio": 50, "ccbench_pin": raw[0]["ccbench_pin"],
                      "environment": [job.get("hostname") for job in raw]},
                      "major_values": values, "verification_status": "未検証の診断値",
                      "transformations": "raw repetition values; median and 95% t CI of mean; throughput stock ratio is descriptive"}
        path.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2,
                                                ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
