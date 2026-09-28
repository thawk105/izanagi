#!/usr/bin/env python3
"""Render three Cicada lifetime figures from raw diagnostic JSON only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import vhash_cicada_vlife as V

T95 = {2: 12.706204736, 3: 4.30265273, 4: 3.1824463,
       5: 2.7764451, 6: 2.5705818}


def _ci(values):
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or len(values) not in T95:
        raise ValueError("2..6 repetitions required for a t confidence interval")
    mean = float(values.mean())
    half = T95[len(values)] * float(values.std(ddof=1)) / np.sqrt(len(values))
    return mean, half


def _hist(run, field, site=None):
    workers = run["parsed"]["workers"]
    if site is None:
        return np.sum([w[field] for w in workers], axis=0)
    return np.sum([w[field][site] for w in workers], axis=0)


def _bucket_quantile(hist, bounds, q):
    count = int(np.sum(hist))
    if not count:
        return 0.0
    return float(bounds[np.searchsorted(np.cumsum(hist), q * count, side="left")])


def _condition_caption(raw):
    rows = raw["conditions"].values()
    workloads = sorted({(x["ycsb_rratio"], x["ycsb_zipf_skew"]) for x in rows})
    longtx = sorted({cid.split("-")[1] for cid in raw["conditions"]})
    gc = sorted({x["gc_inter_us"] for x in rows})
    return (f"YCSB 10 ops, payload 4 B; read ratio/skew {workloads}; "
            f"long tx {longtx}; gc_inter_us {gc}; N={raw['records']:,}; "
            f"3 s, {len(next(iter(raw['runs'].values())))} repetitions; "
            "read positions start at latest; validation positions start at scan start")


def _validate(raw):
    if raw.get("schema_version") != 1 or raw.get("command") != "measure":
        raise ValueError("measure raw JSON required")
    if set(raw.get("conditions", {})) != set(raw.get("runs", {})):
        raise ValueError("condition/run mismatch")
    for cid, runs in raw["runs"].items():
        if cid not in V.CONDITIONS or len(runs) != 3:
            raise ValueError("unknown condition or repetition count")
        for run in runs:
            if run.get("rc") != 0:
                raise ValueError("failed run")
            line = run.get("vlife_json_line")
            if not isinstance(line, str):
                raise ValueError("missing JSON line")
            parsed = V.parse_vlife_line(run["stdout"])
            if line != next(x for x in run["stdout"].splitlines()
                            if x.startswith(V.PREFIX)):
                raise ValueError("line binding")
            if parsed != run.get("parsed"):
                raise ValueError("parsed/raw mismatch")
    return raw


def _layout(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    text_boxes = []
    for ax in fig.axes:
        box = ax.get_window_extent(renderer)
        if box.x0 < 0 or box.y0 < 0 or box.x1 > fig.bbox.width or box.y1 > fig.bbox.height:
            raise ValueError("axis escapes figure")
        for label in (ax.title, ax.xaxis.label, ax.yaxis.label):
            if label.get_text():
                bb = label.get_window_extent(renderer)
                if bb.x0 < 0 or bb.y0 < 0 or bb.x1 > fig.bbox.width or bb.y1 > fig.bbox.height:
                    raise ValueError("label escapes figure")
                text_boxes.append((label.get_text(), bb))
    for i, (left_text, left) in enumerate(text_boxes):
        for right_text, right in text_boxes[i+1:]:
            if left.overlaps(right):
                raise ValueError(f"layout text overlap: {left_text} / {right_text}")


def _save(fig, out, stem, provenance):
    fig.text(0.01, 0.01, provenance["condition_caption"], fontsize=8, wrap=True)
    fig.tight_layout(rect=(0, 0.06, 1, 1), pad=2)
    _layout(fig)
    for extension in (".png", ".pdf"):
        fig.savefig(out / (stem + extension), dpi=180)
    (out / (stem + ".provenance.json")).write_text(
        json.dumps({**provenance, "figure": stem}, indent=2) + "\n")
    plt.close(fig)


def render(raw_path: Path, out: Path):
    raw_bytes = raw_path.read_bytes()
    raw = _validate(json.loads(raw_bytes))
    out.mkdir(parents=True, exist_ok=True)
    provenance = {
        "campaign_id": "vhash-cicada-version-measure",
        "input_path": str(raw_path.resolve()),
        "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "records": raw["records"], "conditions": raw["conditions"],
        "n_reps": 3, "throughput_interpretation": "diagnostic, not performance",
        "condition_caption": _condition_caption(raw),
        "replicate_summaries": {
            cid: [V.summarize(run["parsed"]) for run in runs]
            for cid, runs in raw["runs"].items()
        },
    }
    conditions = sorted(raw["runs"])
    # Figure 1: representative read, write, and validation sites.
    fig, axes = plt.subplots(3, 2, figsize=(14, 13))
    for ax, (field, site) in zip(axes.flat,
                                 (("hops", 0), ("hops", 1), ("hops", 2),
                                  ("hops", 6), ("position", 0), ("position", 1))):
        for cid in conditions:
            shares = []
            for run in raw["runs"][cid]:
                h = _hist(run, field, site)
                shares.append(h / h.sum() if h.sum() else np.zeros_like(h, dtype=float))
            means, errors = zip(*(_ci([row[i] for row in shares]) for i in range(18)))
            ax.errorbar(range(18), means, yerr=errors, label=cid,
                        alpha=0.7, linewidth=1)
        ax.set(xlabel=f"{field} bucket (0–8 exact; final overflow)",
               ylabel="Site share", title=f"{V.SITES[site]} {field}")
    axes[0, 0].legend(fontsize=5, ncol=4)
    _save(fig, out, "search_length", provenance)

    # Figure 2: each K has deep share and optimistic forwarding candidate rate.
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    for cid in conditions:
        deep_rows, candidate_rows = [], []
        for run in raw["runs"][cid]:
            total = _hist(run, "hops", 0).sum()
            deep = _hist(run, "deep")
            candidate = _hist(run, "candidate")
            deep_rows.append(deep / total if total else np.zeros(5))
            candidate_rows.append(np.divide(candidate, deep, out=np.zeros(5, dtype=float),
                                            where=deep != 0))
        for ax, rows in zip(axes, (deep_rows, candidate_rows)):
            values, errors = zip(*(_ci([r[i] for r in rows]) for i in range(5)))
            ax.errorbar(V.K, values, yerr=errors, marker="o", label=cid, alpha=0.7)
    axes[0].set(ylabel="Deep read share", title="K depth and observed optimistic candidates")
    axes[1].set(xlabel="K", ylabel="Candidate / deep update reads")
    axes[0].legend(fontsize=6, ncol=4)
    _save(fig, out, "k_candidates", provenance)

    # Figure 3: time bucket upper bounds and connected logical versions.
    fig, axes = plt.subplots(5, 1, figsize=(11, 16), sharex=True)
    metrics = ("gc_boundary_us", "gc_publish_us", "age_create_us",
               "age_overwrite_us", "logical_versions")
    groups = {}
    for cid in conditions:
        prefix, gc = cid.rsplit("-gc", 1)
        groups.setdefault(prefix, []).append((int(gc), cid))
    for ax, metric, ylabel in zip(axes, metrics,
        ("Boundary age (ts space), µs", "Publish interval (rdtscp), µs",
         "Reclaim age from creation (ts space), µs",
         "Reclaim age from overwrite (ts space), µs",
         "Connected logical versions")):
        for group, rows in sorted(groups.items()):
            rows.sort()
            quantiles = (None,) if metric == "logical_versions" else (0.5, 0.9)
            for quantile in quantiles:
                def value(run):
                    if quantile is None:
                        return float(raw["records"] + sum(
                            w["install"]-w["detach"] for w in run["parsed"]["workers"]))
                    return _bucket_quantile(_hist(run, metric), V.TIME_BOUNDS, quantile)
                values, errors = zip(*(_ci([value(r) for r in raw["runs"][cid]])
                                       for _, cid in rows))
                ax.errorbar([gc for gc, _ in rows], values, yerr=errors,
                            marker="o", label=f"{group} p{int(quantile*100)}" if quantile else group)
        ax.set_ylabel(ylabel)
        if metric != "logical_versions":
            ax.set_yscale("symlog", linthresh=1)
    axes[0].set_title("Cicada GC and logical version lifetime")
    axes[0].legend(fontsize=6, ncol=4)
    axes[-1].set_xscale("log")
    axes[-1].set_xticks((10, 1000, 100000), ("10", "1,000", "100,000"))
    axes[-1].set_xlabel("gc_inter_us")
    _save(fig, out, "gc_lifetime", provenance)


def selftest():
    from orchestrator.tests.test_vhash_cicada_vlife import _payload
    conditions = {cid: V.CONDITIONS[cid] for cid in V.CONDITIONS}
    runs = {}
    for cid in conditions:
        rows = []
        for rep in range(3):
            p = _payload()
            p["workers"][0]["hops"][0][rep] = 10
            p["workers"][0]["deep"][0] = 2
            p["workers"][0]["candidate"][0] = 1
            p["workers"][0]["hops"][0][0] += 2
            p["workers"][0]["install"] = rep
            p["workers"][0]["gc_boundary_us"][rep] = 1
            p["workers"][0]["gc_publish_us"][rep] = 1
            p["workers"][0]["age_create_us"][rep] = 1
            p["workers"][0]["age_overwrite_us"][rep] = 1
            line = V.PREFIX + json.dumps(p)
            rows.append({"rc": 0, "stdout": line, "vlife_json_line": line, "parsed": p})
        runs[cid] = rows
    with tempfile.TemporaryDirectory(prefix="cvl-plot-test-") as td:
        path = Path(td) / "raw.json"
        path.write_text(json.dumps({"schema_version": 1, "command": "measure",
                                    "records": 1000000, "conditions": conditions,
                                    "runs": runs}))
        out = Path(td) / "figures"
        render(path, out)
        assert len(list(out.glob("*.png"))) == 3
        assert len(list(out.glob("*.pdf"))) == 3
        assert len(list(out.glob("*.provenance.json"))) == 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path, nargs="?")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.raw or not args.out:
        parser.error("raw and --out required")
    render(args.raw, args.out)


if __name__ == "__main__":
    main()
