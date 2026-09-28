#!/usr/bin/env python3
"""Render three Cicada lifetime figures from raw diagnostic JSON only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from matplotlib.lines import Line2D

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import vhash_cicada_vlife as V

T95 = {2: 12.706204736, 3: 4.30265273, 4: 3.1824463,
       5: 2.7764451, 6: 2.5705818}
BUCKET_LABELS = [str(x) for x in range(9)] + [str(2**x) for x in range(4, 12)] + [">2048"]
GC_COLORS = {10: "tab:blue", 1000: "tab:orange", 100000: "tab:green"}
LONG_STYLES = {"none": "-", "wait1ms": "--", "wait10ms": ":", "ops1000": "-."}


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
    return (f"Instrumented build; throughput is not a performance result. "
            f"YCSB 10 ops, payload 4 B; read ratio/skew {workloads}; "
            f"long tx {longtx}; gc_inter_us {gc}; N={raw['records']:,}; "
            f"3 s, {len(next(iter(raw['runs'].values())))} repetitions; "
            "timestamp space includes clock boost; read position starts at latest, "
            "validation position at scan start")


def _validate(raw):
    if raw.get("schema_version") != 1 or raw.get("command") != "measure":
        raise ValueError("measure raw JSON required")
    if set(raw.get("conditions", {})) != set(raw.get("runs", {})):
        raise ValueError("condition/run mismatch")
    if not raw["runs"] or type(raw.get("records")) is not int or raw["records"] <= 0:
        raise ValueError("missing conditions or invalid records")
    if not isinstance(raw.get("ccbench_commit"), str) or not isinstance(raw.get("patch_sha256"), str):
        raise ValueError("missing build identity")
    for cid, runs in raw["runs"].items():
        if cid not in V.CONDITIONS or len(runs) != 3:
            raise ValueError("unknown condition or repetition count")
        if raw["conditions"][cid] != V.CONDITIONS[cid]:
            raise ValueError("condition definition mismatch")
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


def _load_raw(paths):
    if not paths:
        raise ValueError("at least one raw file required")
    merged = None
    inputs = []
    for path in paths:
        data = path.read_bytes()
        raw = _validate(json.loads(data))
        inputs.append({"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest()})
        if merged is None:
            merged = {**raw, "conditions": dict(raw["conditions"]), "runs": dict(raw["runs"])}
            continue
        for key in ("ccbench_commit", "patch_sha256", "records"):
            if raw[key] != merged[key]:
                raise ValueError(f"{key} mismatch across raw files")
        duplicate = set(raw["conditions"]) & set(merged["conditions"])
        if duplicate:
            raise ValueError("duplicate condition ID: " + ", ".join(sorted(duplicate)))
        merged["conditions"].update(raw["conditions"])
        merged["runs"].update(raw["runs"])
    return merged, inputs


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
    fig.text(0.01, 0.01, provenance["figure_caption"], fontsize=8, wrap=True)
    fig.tight_layout(rect=(0, 0.09, 1, 1), pad=2)
    _layout(fig)
    for extension in (".png", ".pdf"):
        fig.savefig(out / (stem + extension), dpi=180)
    (out / (stem + ".provenance.json")).write_text(
        json.dumps({**provenance, "figure": stem}, indent=2) + "\n")
    plt.close(fig)


def _series_style(cid):
    workload, longtx, gc = cid.split("-")
    return GC_COLORS[int(gc[2:])], LONG_STYLES[longtx], "o" if workload == "A" else "s"


def _legend(ax, raw, *, workload_marker=False):
    ids = raw["conditions"]
    gc_values = sorted({raw["conditions"][cid]["gc_inter_us"] for cid in ids})
    long_values = [x for x in LONG_STYLES if any(cid.split("-")[1] == x for cid in ids)]
    handles = [Line2D([], [], color=GC_COLORS[gc], label=f"GC {gc:,} µs") for gc in gc_values]
    handles += [Line2D([], [], color="black", linestyle=LONG_STYLES[x], label=x) for x in long_values]
    if workload_marker:
        handles += [Line2D([], [], color="black", marker="o" if w == "A" else "s",
                           linestyle="None", label=f"workload {w}")
                    for w in sorted({cid[0] for cid in ids})]
    ax.legend(handles=handles, fontsize=7, ncol=4, loc="upper right")


def _nonnegative_error(values):
    center, half = _ci(values)
    return center, (min(center, half), half)


def _fraction_error(values):
    center, half = _ci(values)
    return center, (min(center, half), min(1 - center, half))


def _range(values):
    values = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("quantile range requires finite nonnegative values")
    center = float(values.mean())
    return center, (center - float(values.min()), float(values.max()) - center)


def render(raw_paths, out: Path):
    raw, inputs = _load_raw(raw_paths)
    out.mkdir(parents=True, exist_ok=True)
    provenance = {
        "campaign_id": "vhash-cicada-version-measure",
        "inputs": inputs,
        "records": raw["records"], "conditions": raw["conditions"],
        "n_reps": 3, "throughput_interpretation": "diagnostic, not performance",
        "condition_caption": _condition_caption(raw),
        "replicate_summaries": {
            cid: [V.summarize(run["parsed"]) for run in runs]
            for cid, runs in raw["runs"].items()
        },
    }
    conditions = sorted(raw["runs"])
    # Figure 1: one workload per column; color is GC and line style is long tx.
    sites = (("hops", 0), ("hops", 1), ("hops", 2),
             ("hops", 6), ("position", 0), ("position", 1))
    workloads = sorted({cid[0] for cid in conditions})
    fig, axes = plt.subplots(6, len(workloads), figsize=(7 * len(workloads), 18),
                             squeeze=False)
    for row, (field, site) in enumerate(sites):
      for col, workload in enumerate(workloads):
        ax = axes[row, col]
        for cid in (x for x in conditions if x[0] == workload):
            shares = []
            for run in raw["runs"][cid]:
                h = _hist(run, field, site)
                shares.append(h / h.sum() if h.sum() else np.zeros_like(h, dtype=float))
            means, errors = zip(*(_fraction_error([share[i] for share in shares])
                                  for i in range(18)))
            color, style, _ = _series_style(cid)
            ax.errorbar(range(18), means, yerr=np.array(errors).T, color=color,
                        linestyle=style, alpha=0.8, linewidth=1)
        ax.set(xlabel="Bucket upper bound", ylabel="Site share",
               title=f"{workload}: {V.SITES[site]} {field}")
        ax.set_yscale("symlog", linthresh=1e-6)
        ax.set_xticks(range(18), BUCKET_LABELS, rotation=55, fontsize=7)
    _legend(axes[0, 0], raw)
    provenance["figure_caption"] = "Shares: repetition means with 95% t confidence intervals; zero retained by symlog. " + provenance["condition_caption"]
    _save(fig, out, "search_length", provenance)

    # Figure 2: update and read-only depth, then conditional candidate rate.
    fig, axes = plt.subplots(3, 1, figsize=(14, 13), sharex=True)
    denominators = {}
    for cid in conditions:
        deep_rows, readonly_rows, candidate_rows, count_rows = [], [], [], []
        for run in raw["runs"][cid]:
            total = int(_hist(run, "hops", 0).sum())
            readonly_total = int(_hist(run, "hops", 1).sum())
            deep = _hist(run, "deep")
            readonly = _hist(run, "readonly_deep")
            candidate = _hist(run, "candidate")
            deep_rows.append(deep / total if total else np.zeros(5))
            readonly_rows.append(readonly / readonly_total if readonly_total else np.zeros(5))
            candidate_rows.append(np.divide(candidate, deep,
                out=np.full(5, np.nan), where=deep != 0))
            count_rows.append(deep)
        color, style, marker = _series_style(cid)
        for ax, rows in zip(axes[:2], (deep_rows, readonly_rows)):
            values, errors = zip(*(_fraction_error([r[i] for r in rows]) for i in range(5)))
            ax.errorbar(V.K, values, yerr=np.array(errors).T, marker=marker,
                        color=color, linestyle=style, alpha=0.75, markersize=4)
        candidate_values, candidate_errors, counts = [], [], []
        for i in range(5):
            valid = [r[i] for r in candidate_rows if np.isfinite(r[i])]
            count = int(sum(r[i] for r in count_rows))
            counts.append(count)
            if len(valid) >= 2:
                mean, err = _fraction_error(valid)
                candidate_values.append(mean)
                candidate_errors.append(err)
            elif valid:
                candidate_values.append(float(valid[0]))
                candidate_errors.append((0, 0))
            else:
                candidate_values.append(np.nan)
                candidate_errors.append((0, 0))
        denominators[cid] = dict(zip(map(str, V.K), counts))
        axes[2].errorbar(V.K, candidate_values, yerr=np.array(candidate_errors).T,
                         marker=marker, color=color, linestyle=style, alpha=0.7,
                         markersize=4)
        for k, value, count in zip(V.K, candidate_values, counts):
            if np.isfinite(value):
                axes[2].annotate(str(count), (k, value), xytext=(2, 3),
                                 textcoords="offset points", fontsize=5, color=color)
            if count < 30 and np.isfinite(value):
                axes[2].plot(k, value, marker=marker, markerfacecolor="white",
                             markeredgecolor=color, linestyle="None", markersize=6)
    axes[0].set(ylabel="Update reads ≥ K / all update reads", title="Depth and forwarding candidates")
    axes[1].set(ylabel="Read-only reads ≥ K / all read-only reads",
                title="Read-only: fixed snapshot, outside forwarding")
    axes[2].set(xlabel="K", ylabel="Candidates / deep update reads",
                title="Observed optimistic candidates (labels: deep-read count; open: <30)")
    for ax in axes[:2]:
        ax.set_yscale("symlog", linthresh=1e-7)
    axes[2].set_ylim(bottom=0)
    _legend(axes[0], raw, workload_marker=True)
    provenance["candidate_denominators"] = denominators
    provenance["denominator_annotations"] = len(axes[2].texts)
    provenance["figure_caption"] = "Means with 95% t confidence intervals; undefined candidate rates omitted. Labels give summed deep-update-read denominators across repetitions. " + provenance["condition_caption"]
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
        ("Boundary age, µs", "Publish interval, µs",
         "Reclaim age: creation, µs",
         "Reclaim age: overwrite, µs",
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
                values, errors = zip(*((_nonnegative_error if quantile is None else _range)(
                    [value(r) for r in raw["runs"][cid]]) for _, cid in rows))
                workload, longtx = group.split("-")
                color = f"C{list(LONG_STYLES).index(longtx)}"
                ax.errorbar([gc for gc, _ in rows], values, yerr=np.array(errors).T,
                            color=color, linestyle="-" if quantile != 0.9 else "--",
                            marker="o" if workload == "A" else "s",
                            label=f"{group} p{int(quantile*100)}" if quantile else group)
        ax.set_ylabel(ylabel)
        if metric != "logical_versions":
            ax.set_yscale("symlog", linthresh=1)
    axes[0].set_title("Cicada GC and logical version lifetime")
    axes[0].legend(fontsize=7, ncol=4)
    axes[-1].set_xscale("log")
    axes[-1].set_xticks((10, 1000, 100000), ("10", "1,000", "100,000"))
    axes[-1].set_xlabel("gc_inter_us")
    provenance["figure_caption"] = "Time-bucket quantiles: repetition mean with min–max range (no t interval); logical versions: mean with 95% t confidence interval. Color denotes long tx; p50 solid, p90 dashed. " + provenance["condition_caption"]
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
        paths = []
        for i, ids in enumerate((list(conditions)[:12], list(conditions)[12:])):
            path = Path(td) / f"raw-{i}.json"
            path.write_text(json.dumps({"schema_version": 1, "command": "measure",
                "ccbench_commit": "fixture-commit", "patch_sha256": "fixture-patch",
                "records": 1000000, "conditions": {cid: conditions[cid] for cid in ids},
                "runs": {cid: runs[cid] for cid in ids}}))
            paths.append(path)
        merged, inputs = _load_raw(paths)
        assert len(merged["conditions"]) == len(conditions) and len(inputs) == 2
        for mutation, expected in ((lambda x: x["conditions"].update(
            {list(conditions)[0]: conditions[list(conditions)[0]]}), "duplicate condition ID"),
            (lambda x: x.update(patch_sha256="wrong"), "patch_sha256 mismatch")):
            bad = json.loads(paths[1].read_text())
            mutation(bad)
            if expected == "duplicate condition ID":
                bad["runs"][list(conditions)[0]] = runs[list(conditions)[0]]
            bad_path = Path(td) / "bad.json"
            bad_path.write_text(json.dumps(bad))
            try:
                _load_raw((paths[0], bad_path))
            except ValueError as exc:
                assert expected in str(exc), str(exc)
            else:
                raise AssertionError(f"failed to reject {expected}")
        assert _range([0, 1, 10])[0] - _range([0, 1, 10])[1][0] == 0
        out = Path(td) / "figures"
        render(paths, out)
        assert len(list(out.glob("*.png"))) == 3
        assert len(list(out.glob("*.pdf"))) == 3
        assert len(list(out.glob("*.provenance.json"))) == 3
        provenance = json.loads((out / "k_candidates.provenance.json").read_text())
        assert set(provenance["candidate_denominators"]) == set(conditions)
        assert all(set(row) == set(map(str, V.K)) for row in provenance["candidate_denominators"].values())
        assert provenance["denominator_annotations"] > 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path, nargs="*")
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
