#!/usr/bin/env python3
"""Four figures from the 86-condition read-only share diagnostic campaign."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.text import Text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import vhash_cicada_vlife as V

REQUIRED = {cid for cid in V.CONDITIONS if cid.startswith(("R", "S", "T"))}
REQUIRED |= {"B-none-gc10", "B-wait10ms-gc10"}
T95_3 = 4.30265273
COLORS = {10: "tab:blue", 1000: "tab:orange", 100000: "tab:green"}
STYLES = {"none": "-", "wait1msU": "--", "wait10msU": ":", "wait10msR": "-."}


def _load(paths: list[Path]):
    if not paths:
        raise ValueError("raw JSON files required")
    runs = {}
    provenance = []
    identity = None
    for path in paths:
        data = path.read_bytes()
        raw = json.loads(data)
        if raw.get("command") != "measure" or raw.get("schema_version") not in (1, 2):
            raise ValueError("measure JSON required")
        current = (raw.get("ccbench_commit"), raw.get("patch_sha256"), raw.get("records"))
        if current[:2] != (V.PIN, hashlib.sha256(V.PATCH.read_bytes()).hexdigest()):
            raise ValueError("build identity mismatch")
        if identity is None:
            identity = current
        elif identity != current:
            raise ValueError("mixed build identity or record count")
        if set(raw.get("conditions", {})) != set(raw.get("runs", {})):
            raise ValueError("condition/run mismatch")
        for cid, reps in raw["runs"].items():
            if cid in runs or cid not in REQUIRED or raw["conditions"][cid] != V.CONDITIONS[cid]:
                raise ValueError("duplicate, unknown, or changed condition")
            if not isinstance(reps, list) or len(reps) != 3:
                raise ValueError("three repetitions required")
            parsed_reps = []
            for run in reps:
                if run.get("rc") != 0 or not isinstance(run.get("stdout"), str):
                    raise ValueError("failed or missing run")
                parsed = V.parse_vlife_line(run["stdout"])
                if parsed["schema_version"] != 2 or parsed != run.get("parsed"):
                    raise ValueError("schema 2 raw/parsed mismatch")
                if len(parsed["workers"]) != 48:
                    raise ValueError("worker count mismatch")
                argv = run.get("argv")
                if argv is not None and (not isinstance(argv, list) or
                    "-extime=3" not in argv):
                    raise ValueError("raw run duration differs from 3 s")
                parsed_reps.append(parsed)
            runs[cid] = parsed_reps
        provenance.append({"path": str(path.resolve()),
                           "sha256": hashlib.sha256(data).hexdigest()})
    if set(runs) != REQUIRED:
        raise ValueError("86-condition campaign is incomplete")
    return runs, provenance, identity


def _ci(values):
    valid = np.asarray([x for x in values if x is not None], dtype=float)
    if len(valid) != 3 or not np.all(np.isfinite(valid)):
        return None
    return float(valid.mean()), float(T95_3 * valid.std(ddof=1) / np.sqrt(3))


def _metric(reps, name, index=None):
    summaries = [V.summarize(p) for p in reps]
    return _ci([s[name] if index is None else s[name][index] for s in summaries])


def _independent_difference(summaries, terms, metric="gc_boundary_mean_us"):
    """CI for a sum of independent condition means, with signs in terms."""
    coefficients = {}
    for cid, sign in terms:
        coefficients[cid] = coefficients.get(cid, 0) + sign
    samples = []
    for cid, sign in coefficients.items():
        if sign == 0:
            continue
        values = np.asarray([row[metric] for row in summaries[cid]], dtype=float)
        if len(values) != 3 or not np.all(np.isfinite(values)):
            return None
        samples.append((sign, values))
    mean = sum(sign * values.mean() for sign, values in samples)
    se = np.sqrt(sum(sign**2 * values.var(ddof=1) / 3 for sign, values in samples))
    return float(mean), float(T95_3 * se)


def _draw_tuned(ax, runs, metric, *, index=None, title, ylabel):
    for gc, color in ((10, "tab:blue"), (100000, "tab:green")):
        for delay in ("none", "wait10msU"):
            for prefix, style in (("R", "--"), ("T", "-")):
                points = []
                for rate in (0, 50, 95):
                    value = _metric(runs[f"{prefix}{rate}-{delay}-gc{gc}"], metric, index)
                    if value is not None:
                        points.append((rate, *value))
                if points:
                    x, y, e = zip(*points)
                    ax.errorbar(x, y, yerr=e, color=color, linestyle=style,
                                marker="s" if delay == "wait10msU" else "o",
                                capsize=2, label=f"{prefix} {delay} GC {gc} µs")
    ax.set(title=title, xlabel="Specified read-only procedures (%)", ylabel=ylabel)
    ax.grid(alpha=.2)
    ax.legend(fontsize=5, ncol=2, loc="upper left")


def _draw(ax, ids, runs, metric, *, index=None, multiplier=1, title, ylabel):
    for delay in STYLES:
        for gc, color in COLORS.items():
            points = []
            for rate in (0, 25, 50, 75, 95):
                cid = f"R{rate}-{delay}-gc{gc}"
                value = _metric(runs[cid], metric, index)
                if value is not None:
                    points.append((rate, value[0] * multiplier, value[1] * multiplier))
            if points:
                x, y, e = zip(*points)
                ax.errorbar(x, y, yerr=e, color=color, linestyle=STYLES[delay],
                            marker="o", capsize=2, linewidth=1,
                            label=f"GC {gc} µs; {delay}")
    ax.set(title=title, xlabel="Specified read-only procedures (%)", ylabel=ylabel)
    ax.grid(alpha=.2)


def _layout(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if (box.x0 < 0 or box.y0 < 0 or
            box.x1 > fig.bbox.width or box.y1 > fig.bbox.height):
            raise ValueError("figure text escapes canvas")
        if artist.axes is not None:
            for other in fig.axes:
                if other is not artist.axes and box.overlaps(other.bbox):
                    raise ValueError("figure text enters another panel")
        boxes.append(box)
    if any(a.overlaps(b) for i, a in enumerate(boxes) for b in boxes[i+1:]):
        raise ValueError("figure text overlaps")
    for ax in fig.axes:
        box = ax.get_tightbbox(renderer)
        if box is not None and (box.x0 < 0 or box.y0 < 0 or
                                box.x1 > fig.bbox.width or box.y1 > fig.bbox.height):
            raise ValueError("axis decoration escapes canvas")


def _save(fig, out, name, common, numbers, caption):
    fig.text(.03, .012, textwrap.fill(caption, width=105), fontsize=7)
    for ax in fig.axes:
        ax.title.set_fontsize(9)
        ax.xaxis.label.set_fontsize(8)
        ax.yaxis.label.set_fontsize(8)
    fig.tight_layout(rect=(0, .095, 1, .99), pad=3.5, h_pad=4, w_pad=4)
    _layout(fig)
    for suffix in ("png", "pdf"):
        fig.savefig(out / f"{name}.{suffix}", dpi=180)
    (out / f"{name}.provenance.json").write_text(json.dumps(
        {**common, "figure": name, "caption": caption, "numbers": numbers},
        indent=2, ensure_ascii=False) + "\n")
    plt.close(fig)


def render(paths: list[Path], out: Path):
    runs, inputs, identity = _load(paths)
    out.mkdir(parents=True, exist_ok=True)
    summaries = {cid: [{**V.summarize(p),
                        "update_commits_per_s": V.summarize(p)["update_commits"] / 3,
                        "install_per_s": V.summarize(p)["install"] / 3}
                       for p in reps] for cid, reps in runs.items()}
    common = {"campaign_id": "vhash-readonly-share", "inputs": inputs,
              "ccbench_commit": identity[0], "patch_sha256": identity[1],
              "records": identity[2], "n_reps": 3,
              "conditions": {cid: V.CONDITIONS[cid] for cid in sorted(runs)},
              "measurement": "YCSB, 10 operations, 4 B, 48 workers, 3 s; diagnostic build",
              "replicate_summaries": summaries}
    ids = sorted(runs)

    fig, axes = plt.subplots(3, 3, figsize=(24, 15))
    for col, k in enumerate((1, 4, 8)):
        index = V.K.index(k)
        _draw(axes[0, col], ids, runs, "readonly_deep_rate", index=index,
              title=f"Read-only depth ≥ {k}", ylabel="Share of selected read-only reads")
        _draw(axes[1, col], ids, runs, "readonly_share_of_deep", index=index,
              title=f"Read-only share of depth ≥ {k}", ylabel="Share of deep reads")
    axes[0, 0].legend(fontsize=5, ncol=2, loc="upper left")
    for col, k in enumerate((1, 4, 8)):
        _draw_tuned(axes[2, col], runs, "readonly_deep_rate", index=V.K.index(k),
                    title=f"T (tuned) vs R (default): depth ≥ {k}",
                    ylabel="Share of selected read-only reads")
    _save(fig, out, "depth_share", common,
          {cid: [s["readonly_deep_rate"] for s in rows] for cid, rows in summaries.items()},
          "Observed chain positions. T (tuned) vs R (default) panels use matched conditions. Error bars: 95% t CI across three runs; specified and realized rates differ.")

    fig, axes = plt.subplots(3, 3, figsize=(24, 15))
    for ax, metric, title, ylabel in (
        (axes[0, 0], "gc_boundary_mean_us", "Published boundary age", "Mean µs"),
        (axes[0, 1], "gc_boundary_p50_bucket_us", "Published boundary age p50", "Bucket upper bound (µs)"),
        (axes[0, 2], "gc_publish_mean_us", "Publication interval", "Mean µs"),
        (axes[1, 0], "ro_snapshot_age_mean_us", "Read-only snapshot age", "Mean µs"),
        (axes[1, 1], "gc_publications", "Publication frequency", "Publications / s"),
        (axes[1, 2], "same_boundary_publications", "Same-value republications", "Count / 3 s")):
        _draw(ax, ids, runs, metric, multiplier=1/3 if metric == "gc_publications" else 1,
              title=title, ylabel=ylabel)
    for col, (metric, title) in enumerate((("gc_boundary_mean_us", "Boundary age"),
                                            ("gc_publish_mean_us", "Publication interval"),
                                            ("ro_snapshot_age_mean_us", "Read-only snapshot age"))):
        _draw_tuned(axes[2, col], runs, metric,
                    title=f"T (tuned) vs R (default): {title}", ylabel="Mean µs")
    _save(fig, out, "boundary_age", common,
          {cid: [s["gc_boundary_mean_us"] for s in rows] for cid, rows in summaries.items()},
          "Boundary and snapshot ages are distinct; T (tuned) vs R (default) panels use matched conditions. Timestamp ages include clock boost. Error bars: 95% t CI.")

    fig, axes = plt.subplots(2, 2, figsize=(24, 15))
    for gc, color in COLORS.items():
        points = []
        for rate in (0, 25, 50, 75, 95):
            value = _independent_difference(summaries,
                [(f"R{rate}-none-gc{gc}", 1), (f"R0-none-gc{gc}", -1)])
            if value is not None:
                points.append((rate, value[0], value[1]))
        if points:
            x, y, e = zip(*points)
            axes[0, 0].errorbar(x, y, yerr=e, color=color, marker="o", capsize=2,
                                label=f"GC {gc} µs")
    axes[0, 0].set(title="D-F: read-only condition difference, no long tx",
                   xlabel="Specified read-only procedures (%)", ylabel="Boundary age difference (µs)")
    labels, centers, errors = [], [], []
    for gc in COLORS:
        for delay in ("wait1msU", "wait10msU"):
            value = _independent_difference(summaries,
                [(f"R0-{delay}-gc{gc}", 1), (f"R0-none-gc{gc}", -1)])
            if value is not None:
                labels.append(f"{gc} µs\n{delay}")
                centers.append(value[0]); errors.append(value[1])
    axes[0, 1].bar(range(len(labels)), centers, yerr=errors, capsize=3)
    axes[0, 1].set_xticks(range(len(labels)), labels, fontsize=8)
    axes[0, 1].set(title="D-F: long update condition difference at R=0",
                   ylabel="Boundary age difference (µs)")
    for gc, color in COLORS.items():
        for delay in ("wait1msU", "wait10msU", "wait10msR"):
            x, y, err = [], [], []
            for rate in (0, 25, 50, 75, 95):
                value = _independent_difference(summaries, [
                    (f"R{rate}-{delay}-gc{gc}", 1), (f"R{rate}-none-gc{gc}", -1),
                    (f"R0-{delay}-gc{gc}", -1), (f"R0-none-gc{gc}", 1)])
                if value is not None:
                    x.append(rate); y.append(value[0]); err.append(value[1])
            axes[1, 0].errorbar(x, y, yerr=err, color=color, linestyle=STYLES[delay],
                                marker="o", capsize=2, label=f"GC {gc} µs; {delay}")
    axes[1, 0].set(title="D-F: condition total-difference interaction",
                   xlabel="Specified read-only procedures (%)", ylabel="Boundary age difference (µs)")
    for gc, color in COLORS.items():
        for metric, style, label in (
            ("dc_cf_wait_mean_us", "-", "first flag opportunity"),
            ("dc_ro_gap_mean_us", "--", "actual flag gap"),
            ("dc_leader_wait_mean_us", ":", "last flag raise to publication detection")):
            points = []
            for rate in (0, 25, 50, 75, 95):
                value = _metric(runs[f"R{rate}-none-gc{gc}"], metric)
                if value is not None:
                    points.append((rate, value[0], value[1]))
            if points:
                x, y, e = zip(*points)
                axes[1, 1].errorbar(x, y, yerr=e, color=color, linestyle=style,
                                    marker="o", capsize=2, label=f"GC {gc} µs; {label}")
    axes[1, 1].set(title="D-C: observed flag-opportunity split, no long tx",
                   xlabel="Specified read-only procedures (%)", ylabel="Mean per valid interval (µs)")
    for ax in axes.flat:
        ax.grid(alpha=.2)
    for ax in (axes[0, 0], axes[1, 0], axes[1, 1]):
        ax.legend(fontsize=6, ncol=2, loc="upper left")
    _save(fig, out, "decompositions", common,
          {cid: [s["dc_ro_gap_mean_us"] for s in rows] for cid, rows in summaries.items()},
          "D-F is a between-condition total difference with independent-run uncertainty; D-C partitions observed timestamps. The third term ends at publication detection. Panels have separate units.")

    fig, axes = plt.subplots(1, 2, figsize=(24, 9))
    for k in (1, 4, 8):
        idx = V.K.index(k)
        for fixed in (0, .5, 1):
            points = []
            for rate in (0, 25, 50, 75, 95):
                value = _ci([None if s["readonly_candidate_rate"][idx] is None else
                             (1-fixed) * s["readonly_candidate_rate"][idx]
                             for s in summaries[f"R{rate}-none-gc10"]])
                if value is not None:
                    points.append((rate, value[0], value[1]))
            if points:
                x, y, e = zip(*points)
                axes[0].errorbar(x, y, yerr=e, marker="o", capsize=2,
                                 label=f"K={k}; fixed fraction f={fixed:g}")
    axes[0].set(title="(a) Optimistic eligibility: observed chains, first K, read interval",
                xlabel="Specified read-only procedures (%)", ylabel="Eligible share; first K versions and read interval")
    _draw(axes[1], ids, runs, "local_flag_opportunity", title="(b) Local opportunity relative to publication interval",
          ylabel="Observed read-only gap / publication interval")
    axes[0].legend(fontsize=7, ncol=2)
    _save(fig, out, "opportunities", common,
          {cid: [s["local_flag_opportunity"] for s in rows] for cid, rows in summaries.items()},
          "(a) Optimistic eligibility limited to observed chains, first K versions and read interval; assumes independence of fixed-snapshot need. (b) is a local opportunity relative to publication interval, not boundary advance.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    render(args.raw, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
