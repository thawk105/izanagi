#!/usr/bin/env python3
"""Plot paired Cicada ceiling ratios from raw JSONL on a non-measurement node."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics

from orchestrator.campaign import vhash_ceiling_vs_sota as C

T975 = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
        7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.228,
        12: 2.201, 13: 2.179, 14: 2.160, 15: 2.145, 16: 2.131,
        17: 2.120, 18: 2.110, 19: 2.101, 20: 2.093, 21: 2.086,
        22: 2.080, 23: 2.074, 24: 2.069, 25: 2.064, 26: 2.060,
        27: 2.056, 28: 2.052, 29: 2.048, 30: 2.045}


def ci95(values: list[float]) -> tuple[float, float]:
    if not values: raise ValueError("empty sample")
    center = statistics.median(values)
    if len(values) == 1: return center, center
    t = T975[len(values)] if len(values) <= 30 else 1.96
    half = t * statistics.stdev(values) / len(values) ** 0.5
    return center - half, center + half


def check_layout(fig) -> None:
    """Reject colliding text and text outside the saved canvas."""
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for item in fig.findobj(Text):
        if not item.get_visible() or not item.get_text().strip(): continue
        box = item.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0: continue
        if box.x0 < 0 or box.y0 < 0 or box.x1 > fig.bbox.width or box.y1 > fig.bbox.height:
            raise ValueError("figure text outside canvas")
        boxes.append((item, box))
    for i, (_, a) in enumerate(boxes):
        for _, b in boxes[i+1:]:
            if min(a.x1, b.x1) - max(a.x0, b.x0) > 1 and \
                    min(a.y1, b.y1) - max(a.y0, b.y0) > 1:
                raise ValueError("figure text overlap")


def make_figure(rows: list[dict], witnesses: dict | None = None):
    import matplotlib.pyplot as plt

    summary = C.aggregate(rows, witnesses)
    points = tuple(p for p in ("P1", "P2", "P3", "P4") if p in summary["gc"])
    arms = ("S", "R-noLR", "hot1", "hot8", "fwd", "igc1", "igc3")
    has_compare = any(r["mode"] == "compare" for r in rows)
    fig, axes = plt.subplots(3 if has_compare else 2, 1,
                            figsize=(13, 10.5 if has_compare else 8.5),
                            gridspec_kw={"height_ratios": [3, 2, 1.4] if has_compare else [3, 1.4]})
    ax, table_ax = axes[0], axes[-1]
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.06, hspace=0.55)
    ax.axhline(1, linestyle="--", color="black", linewidth=1, label="R (read-only GC fix)")
    table_rows = []
    metrics = {}
    offsets = {arm: (i-3) * 0.095 for i, arm in enumerate(arms)}
    for point_index, point in enumerate(points):
        interval = summary["gc"][point]
        for arm in arms:
            pairs = C.paired([r for r in rows if r["mode"] == "prelim"], arm,
                             point, interval, "prelim")
            if not pairs: continue
            values = [p["ratio"] for p in pairs]
            low, high = ci95(values)
            median = statistics.median(values)
            x = point_index + offsets[arm]
            ax.errorbar(x, median, yerr=[[max(0, median-low)], [max(0, high-median)]],
                        marker="o", capsize=2, label=arm if point_index == 0 else None)
            completion = [p["completion_ratio"] for p in pairs
                          if p["completion_ratio"] is not None]
            cmedian = statistics.median(completion) if completion else None
            table_rows.append([point, arm, str(interval),
                               "—" if cmedian is None else f"{cmedian:.2f}"])
            metrics[f"{point}/{arm}"] = {"median_ratio": median, "t_spread_ci95": [low, high],
                                          "completion_median": cmedian, "n": len(values)}
    ax.set_xticks(range(len(points)), points)
    ax.set_xlim(-0.6, len(points)-0.4)
    ax.set_ylabel("Normal worker commits / R (paired)")
    ax.set_title("Cicada ceiling: paired preliminary ratios")
    ax.legend(loc="upper left", ncol=4, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    compare_metrics = {}
    if has_compare:
        compare_ax = axes[1]
        compare_ax.axhline(1, linestyle="--", color="black", linewidth=1)
        compare_ax.axhline(1.5, linestyle=":", color="gray", linewidth=1)
        compare_points = (summary["representative"]["point"], summary["neighbor"])
        for i, point in enumerate(compare_points):
            for j, arm in enumerate(C.M_ARMS):
                item = summary["compare"].get(point, {}).get(arm)
                if not item:
                    continue
                values = [pair["ratio"] for pair in item["pairs"]]
                low, high = ci95(values)
                median = statistics.median(values)
                compare_ax.errorbar(i + (j-1)*0.13, median,
                                    yerr=[[max(0, median-low)], [max(0, high-median)]],
                                    marker="o", capsize=2, label=arm if i == 0 else None)
                compare_metrics[f"{point}/{arm}"] = {"median_ratio": median,
                    "t_spread_ci95": [low, high], "completion_median": item["completion_ratio"],
                    "eligible": item["eligible"], "n": len(values)}
        compare_ax.set_xticks(range(len(compare_points)), compare_points)
        compare_ax.set_xlim(-0.5, len(compare_points)-0.5)
        compare_ax.set_title("30-second paired comparison (same M arm)")
        compare_ax.set_ylabel("Normal worker commits / R")
        compare_ax.legend(loc="upper left", ncol=3, fontsize=8)
        compare_ax.grid(axis="y", alpha=0.25)
    table_ax.axis("off")
    table_ax.set_title("Batch completion ratio (arm / R); 0.80 minimum", fontsize=10)
    table = table_ax.table(cellText=table_rows, colLabels=["Point", "Arm", "GC µs", "Completion"],
                           cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 0.65 if len(table_rows) > 15 else 1)
    fig.text(0.08, 0.91, "1M records · 4 B values · 10 operations · tuned B0 O1 P0 R1 W0; "
             "P1–P3: 47 normal + 1 batch; P4: 12 normal", fontsize=9)
    check_layout(fig)
    return fig, {"gc": summary["gc"], "metrics": metrics,
                 "compare_metrics": compare_metrics, "conditions": C.POINTS}


def render(raw: Path, out: Path, witnesses: Path | None = None) -> dict:
    import matplotlib.pyplot as plt
    rows = [json.loads(line) for line in raw.read_text().splitlines() if line.strip()]
    witness_data = json.loads(witnesses.read_text()) if witnesses else {}
    if isinstance(witness_data, list):
        witness_data = {item["arm"]: item for item in witness_data}
    fig, details = make_figure(rows, witness_data)
    provenance = {"campaign_id": "vhash-ceiling-vs-sota", "input": str(raw.resolve()),
                  "input_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
                  "witness_input": str(witnesses.resolve()) if witnesses else None,
                  "witness_sha256": hashlib.sha256(witnesses.read_bytes()).hexdigest()
                  if witnesses else None,
                  "nodes": sorted({r["node"] for r in rows}),
                  "record_counts": sorted({r["flags"]["tuple_num"] for r in rows}),
                  "environment": sorted({json.dumps(r.get("environment", {}), sort_keys=True)
                                          for r in rows}), **details}
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out.with_suffix(".png"), dpi=180)
    fig.savefig(out.with_suffix(".pdf"))
    out.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True)+"\n")
    plt.close(fig)
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--witness", type=Path)
    args = parser.parse_args()
    render(args.raw, args.out, args.witness)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
