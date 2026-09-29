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
    return sum(r[key] for r in rows)


def _maybe_sum(rows, key):
    return _sum(rows, key) if rows and all(key in r for r in rows) else None


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
    conditions = data.get("conditions", {})
    fig.suptitle("Cicada forwarding · 未検証の診断値\n"
                 f"{conditions.get('threads', 48)} threads · {conditions.get('tuples', 1000000)} tuples · "
                 f"skew {conditions.get('zipf', 'unknown')} · read ratio {conditions.get('rratio', 'unknown')} "
                 f"· max ops {conditions.get('max_ope', 'unknown')} · K=3",
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
                          "no_target": _maybe_sum(counts, "no_target"),
                          "c_ratios": _ratios(cell, "c"), "f_ratios": _ratios(cell, "f"),
                          "long_commits_c": _maybe_sum(cell.get("longtx", {}).get("c", []), "commits"),
                          "long_commits_f": _maybe_sum(cell.get("longtx", {}).get("f", []), "commits"),
                          "f_aborts_long": _maybe_sum([v["long"] for v in cell.get("counter_by_thread", {}).get("f", [])], "f_aborts"),
                          "f_aborts_normal": _maybe_sum([v["normal"] for v in cell.get("counter_by_thread", {}).get("f", [])], "f_aborts"),
                          "completion_rate": {arm: (cell.get("longtx_summary", {}).get(arm) or {}).get("completion_rate")
                                              for arm in ("stock", "c", "f")}})
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
                   for v in cells], alpha=.25, color="#6c7175")
        a2.set_ylabel("attempts", color="#6c7175")
        a2.tick_params(axis="y", colors="#6c7175")
        bottom = np.zeros(len(GC_VALUES))
        for reason in ("success", *FAILURES):
            heights = np.array([100 * v["failure_reasons"][reason] / v["attempts"]
                                if v["attempts"] and v["failure_reasons"][reason] is not None
                                else float("nan") for v in cells]) if reason != "success" else np.array([
                                    100 * v["success"] / v["attempts"] if v["attempts"] else float("nan") for v in cells])
            b.bar(x, heights, bottom=bottom, label=reason)
            bottom += heights
        b.set_ylim(0, 110)
        b.set_ylabel("share of attempts (%)")
        b2 = b.twinx()
        b2.plot(x, [v["no_target"] if v["no_target"] is not None else float("nan") for v in cells],
                "x--", color="#555555", label="no target (before attempt)")
        b2.set_ylabel("no target (count)", color="#555555")
        b2.tick_params(axis="y", colors="#555555")
        b.set_title("C attempt outcomes + pre-attempt exclusion")
        if row == 0:
            b.legend(fontsize=7, loc="upper left")
            b2.legend(fontsize=7, loc="upper right")
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
                   for v in cells], "o-", color="#177a65", label="C long commits")
        d.plot(x, [v["long_commits_f"] if v["long_commits_f"] is not None else float("nan")
                   for v in cells], "o-", color="#bd5b23", label="F long commits")
        d2 = d.twinx()
        d2.plot(x, [v["f_aborts_long"] if v["f_aborts_long"] is not None else float("nan")
                    for v in cells], "s--", color="#bd5b23", label="F abort, long")
        d2.plot(x, [v["f_aborts_normal"] if v["f_aborts_normal"] is not None else float("nan")
                    for v in cells], "x:", color="#8e6e58", label="F abort, normal")
        d.set_title("long thread progress / F abort")
        d.set_ylabel("long commits")
        d2.set_ylabel("F aborts", color="#bd5b23")
        d2.tick_params(axis="y", colors="#bd5b23")
        if row == 0:
            d.legend(fontsize=7, loc="upper left")
            d2.legend(fontsize=7, loc="upper right")
        for ax in (a, b, c, d):
            ax.set_xticks(x, [str(gc) for gc in GC_VALUES])
            ax.set_xlabel("GC interval (µs)")
    return fig, list(axs.flat), values


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("aggregate", type=Path)
    p.add_argument("raw", type=Path, nargs="+")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    aggregate = json.loads(args.aggregate.read_text())
    raw = [json.loads(path.read_text()) for path in args.raw]
    from orchestrator.campaign.vhash_forwarding_prototype import aggregate_jobs
    if aggregate_jobs(raw)["cells"] != aggregate["cells"]:
        raise ValueError("aggregate does not match supplied raw records")
    fig, axes, values = make_figure(aggregate)
    check_figure_layout(fig, axes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix(".png"), dpi=200)
    fig.savefig(args.output.with_suffix(".pdf"))
    provenance = {"inputs": {str(f.resolve()): hashlib.sha256(f.read_bytes()).hexdigest()
                             for f in (args.aggregate, *args.raw)},
                  "conditions": aggregate.get("conditions", {}), "major_values": values,
                  "jobs": [{key: job.get(key) for key in ("job_id", "hostname", "ccbench_pin", "patch_sha256")}
                           for job in raw if job.get("command") == "run" and job.get("all_pass") is True],
                  "verification_status": "未検証の診断値"}
    args.output.with_suffix(".provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
