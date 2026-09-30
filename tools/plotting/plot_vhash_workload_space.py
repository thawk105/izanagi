#!/usr/bin/env python3
"""Fail-closed workload-space analysis of instrumented Cicada runs.

The numbers are observed opportunities, not predicted speedups. Instrumented
throughput and wall time are deliberately absent from every figure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import vhash_cicada_vlife as V

ABORT_REASONS = V.ABORT_REASONS
ABORT_SIDES = ("normal", "long_tx")
FACTORS = {
    "skew": (.6, .9, .99), "rr": (5, 50, 95),
    "records": (10000, 100000, 1000000), "ops": (10, 100, 1000),
    "long": ("none", "batchU", "batchR"), "ro": (0, 50, 95),
    "val": (4, 100, 1000), "threads": (12, 24, 48),
    "gc": (10, 1000, 100000),
}
SKEWS = (.5, .6, .7, .8, .9, .95, .97, .99)
PREDICATES = ("H1", "H2", "H4-lag", "H4-live")
THRESHOLDS = {"h1": .10, "u1": .05, "reads": 10000,
              "h2": .01, "candidates": 100, "update_commits": 1000,
              "lag_us": 1024, "live_factor": 1.1}


def design():
    """Use the driver's registered W IDs and condition values as the design."""
    result = [dict(layer=cid.split("-")[0][1:], **condition_point(condition))
              for cid, condition in V.CONDITIONS.items()
              if cid.startswith("W") and cid.endswith("-default")]
    assert len(result) == 126 and len({tuple(sorted(x.items())) for x in result}) == 126
    return result


def condition_point(condition):
    """Translate W driver condition keys to the registered design axes."""
    required = ("records", "ycsb_max_ope", "ycsb_rratio", "ycsb_zipf_skew",
                "gc_inter_us", "izanagi_ronly_pct", "izanagi_long_kind",
                "thread_num", "batch_th_num", "val_size", "genome")
    if any(k not in condition for k in required):
        raise ValueError("incomplete W condition")
    kind = condition["izanagi_long_kind"]
    if kind not in (0, 1, 2) or condition["batch_th_num"] != (kind != 0):
        raise ValueError("long transaction/batch mismatch")
    if kind and condition.get("batch_max_ope") != 1000:
        raise ValueError("long transaction length mismatch")
    return dict(records=condition["records"], ops=condition["ycsb_max_ope"],
                rr=condition["ycsb_rratio"], skew=condition["ycsb_zipf_skew"],
                gc=condition["gc_inter_us"], ro=condition["izanagi_ronly_pct"],
                long=("none", "batchU", "batchR")[kind], val=condition["val_size"],
                threads=condition["thread_num"]+condition["batch_th_num"])


def _design_key(point):
    return tuple(point[k] for k in ("layer", *FACTORS))


def _flags(argv):
    if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
        raise ValueError("argv missing")
    flags = {}
    for item in argv[1:]:
        if item.startswith("-") and "=" in item:
            k, v = item[1:].split("=", 1)
            if k in flags:
                raise ValueError("duplicate argv flag")
            flags[k] = v
    return flags


def _validated_run(run, point, genome):
    flags = _flags(run.get("argv"))
    if run.get("build_key") != {"genome": genome, "val_size": point["val"]}:
        raise ValueError("build key/condition mismatch")
    expected = {"tuple_num": point["records"], "ycsb_tuple_num": point["records"],
                "ycsb_max_ope": point["ops"], "ycsb_rratio": point["rr"],
                "ycsb_zipf_skew": point["skew"], "gc_inter_us": point["gc"],
                "izanagi_ronly_pct": point["ro"], "izanagi_long_kind":
                ("none", "batchU", "batchR").index(point["long"]),
                "thread_num": point["threads"]-(point["long"] != "none"),
                "batch_th_num": int(point["long"] != "none")}
    if any(flags.get(k) != str(v) for k, v in expected.items()):
        raise ValueError("argv/condition mismatch")
    if run.get("rc") != 0 or run.get("parse_error") or not isinstance(run.get("stdout"), str):
        return {"valid": False, "error": "rc/timeout/parse failure"}
    try:
        parsed = V.parse_vlife_line(run["stdout"])
    except (ValueError, KeyError, TypeError) as exc:
        if "abort reason" in str(exc):
            raise ValueError("abort reason mismatch") from exc
        if run.get("parsed") is None:
            return {"valid": False, "error": "parse failure"}
        raise ValueError("stdout/parsed mismatch")
    if parsed != run.get("parsed"):
        raise ValueError("stdout/parsed mismatch")
    if parsed.get("schema_version") != 3:
        raise ValueError("schema 3 required")
    build = parsed["build"]
    if build.get("val_size") != point["val"] or (
        build.get("inline_version_opt") != (1 if genome == "tuned" else 0)
    ) or build.get("izanagi_ronly_pct") != point["ro"] or (
        build.get("izanagi_long_kind") != expected["izanagi_long_kind"]
    ):
        raise ValueError("build key/condition mismatch")
    if any(type(build.get(k)) is not int or build[k] <= 0
           for k in ("sizeof_version", "sizeof_ycsb")):
        raise ValueError("missing build size")
    rss = run.get("maxrss_kb")
    if type(rss) is not int or rss <= 0:
        raise ValueError("maxrss missing")
    if len(parsed["workers"]) != point["threads"]:
        raise ValueError("worker count mismatch")
    reasons = {reason: {side: 0 for side in ABORT_SIDES} for reason in ABORT_REASONS}
    for worker in parsed["workers"]:
        counts = worker.get("abort_reasons")
        if not isinstance(counts, list) or len(counts) != len(ABORT_REASONS)*2 or (
            any(type(v) is not int or v < 0 for v in counts)
        ) or sum(counts) != sum(worker["aborts"]):
            raise ValueError("abort reason mismatch")
        for index, reason in enumerate(ABORT_REASONS):
            for side_index, side in enumerate(ABORT_SIDES):
                reasons[reason][side] += counts[2*index + side_index]
    summary = V.summarize(parsed)
    stored = run.get("summary")
    if not isinstance(stored, dict) or any(stored.get(k) != v for k, v in summary.items()):
        raise ValueError("summary mismatch")
    chains = parsed.get("hot_chains")
    scan = parsed.get("hot_scan_us")
    if not isinstance(chains, list) or len(chains) != 8 or (
        {item["key"] for item in chains} != set(range(8))
    ) or type(scan) is not int or scan < 0:
        raise ValueError("hot chain/scan fields missing")
    return {"valid": True, "parsed": parsed, "summary": summary,
            "reasons": reasons, "chains": chains, "scan_us": scan,
            "maxrss_kb": rss}


def load(paths):
    expected = {_design_key(p): p for p in design()}
    rows, provenance, ids = {}, [], set()
    for path in paths:
        data = Path(path).read_bytes()
        raw = json.loads(data)
        if raw.get("command") != "measure" or raw.get("schema_version") != 1:
            raise ValueError("schema 1 measure raw required")
        conditions, runs = raw.get("conditions"), raw.get("runs")
        if not isinstance(conditions, dict) or not isinstance(runs, dict) or set(conditions) != set(runs):
            raise ValueError("conditions/runs mismatch")
        for cid, condition in conditions.items():
            if cid in ids:
                raise ValueError("duplicate condition ID")
            ids.add(cid)
            genome = condition.get("genome")
            if genome not in ("default", "tuned", "best100"):
                raise ValueError("unknown genome")
            point = condition_point(condition)
            candidates = [p for p in design() if all(p[k] == v for k, v in point.items())]
            if len(candidates) != 1 or genome != ("tuned" if point["ops"] == 10 else "best100") and genome != "default":
                raise ValueError("unknown design point/genome")
            p = candidates[0]
            key = (_design_key(p), genome)
            if key in rows:
                raise ValueError("duplicate point/genome")
            if cid not in V.CONDITIONS or not cid.startswith("W") or condition != V.CONDITIONS[cid]:
                raise ValueError("condition differs from registered W ID")
            reps = runs[cid]
            if not isinstance(reps, list) or len(reps) < 2:
                raise ValueError("fewer than two repetitions")
            rows[key] = {"id": cid, "point": p, "genome": genome,
                         "reps": [_validated_run(r, p, genome) for r in reps]}
        provenance.append({"path": str(Path(path).resolve()),
                           "sha256": hashlib.sha256(data).hexdigest()})
    wanted = {(_design_key(p), g) for p in expected.values()
              for g in ("default", "tuned" if p["ops"] == 10 else "best100")}
    if set(rows) != wanted:
        raise ValueError(f"missing design point/genome: {len(wanted-set(rows))}")
    return rows, provenance


def _ratio(n, d):
    return n/d if d else None


def metrics(rep, records):
    if not rep["valid"]:
        return {"status": "判定不能"}
    p, s = rep["parsed"], rep["summary"]
    workers = p["workers"]
    update = [sum(w["position"][0][i] for w in workers) for i in range(18)]
    readonly = [sum(w["position"][1][i] for w in workers) for i in range(18)]
    reads = sum(update)+sum(readonly)
    candidates = sum(w["candidate"][0] for w in workers)
    publications = s["gc_publications"]
    live = records+s["logical_version_delta"]
    out = {"h1": _ratio(sum(update[1:])+sum(readonly[1:]), reads),
           "u1": _ratio(sum(update[1:]), sum(update)),
           "depth8": _ratio(sum(update[8:])+sum(readonly[8:]), reads),
           "h2": _ratio(candidates, sum(update)),
           "abort_rate": s["abort_rate"], "update_commits": s["update_commits"],
           "candidates": candidates, "reads": reads, "update_reads": sum(update),
           "lag_us": s["gc_boundary_p50_bucket_us"],
           "publications": publications, "live_versions": live,
           "live_ratio": live/records, "local_flag_opportunity": s["local_flag_opportunity"],
           "maxrss_kb": rep["maxrss_kb"], "hot_scan_us": rep["scan_us"]}
    for site_index, site in enumerate(V.SITES):
        positions = [sum(w["position"][site_index][i] for w in workers)
                     for i in range(18)]
        for depth in (1, 4, 8):
            out[f"{site}_position_ge{depth}_rate"] = _ratio(
                sum(positions[depth:]), sum(positions))
        if site in ("read_update", "read_ronly"):
            for depth in (1, 2, 4, 8):
                out[f"{site}_beyond_k{depth}_rate"] = _ratio(
                    sum(positions[depth:]), sum(positions))
    for depth, index in ((1, 0), (2, 1), (4, 3), (8, 4)):
        count = sum(w["candidate"][index] for w in workers)
        out[f"candidate_k{depth}_count"] = count
        out[f"candidate_k{depth}_denominator"] = sum(update)
        out[f"candidate_k{depth}_rate"] = _ratio(count, sum(update))
    out["live_bytes_estimate"] = live * (
        p["build"]["sizeof_version"] + p["build"]["sizeof_ycsb"])
    chain_lengths = [chain["length"] for chain in rep["chains"]
                     if chain["status"] == "ok"]
    out["hot_chain_max"] = max(chain_lengths) if chain_lengths else None
    out["hot_chain_median"] = statistics.median(chain_lengths) if chain_lengths else None
    out["H1"] = None if reads < THRESHOLDS["reads"] else (
        out["h1"] >= THRESHOLDS["h1"] or
        (sum(update) >= THRESHOLDS["reads"] and out["u1"] >= THRESHOLDS["u1"]))
    # Candidate and commit floors are predicate requirements, not denominators:
    # below-floor observations are valid failures when read denominator is sufficient.
    out["H2"] = (out["h2"] >= THRESHOLDS["h2"] and
                 candidates >= THRESHOLDS["candidates"] and
                 s["update_commits"] >= THRESHOLDS["update_commits"]
                 ) if sum(update) >= THRESHOLDS["reads"] else None
    out["H4-lag"] = "停止" if publications == 0 else (
        None if out["lag_us"] is None else out["lag_us"] >= THRESHOLDS["lag_us"])
    out["H4-live"] = out["live_ratio"] >= THRESHOLDS["live_factor"]
    return out


def state(values):
    if len(values) < 2 or any(v is None for v in values):
        return "判定不能"
    passed = sum(v is True or v == "停止" for v in values)
    if passed == len(values):
        return "停止" if all(v == "停止" for v in values) else "通過"
    return "境界" if passed else "不通過"


def _h4_any(values):
    lag, live = values.get("H4-lag"), values.get("H4-live")
    if lag == "停止":
        return "停止"
    if lag is True or live is True:
        return True
    if lag is None or live is None:
        return None
    return False


def evaluate(rows):
    for row in rows.values():
        row["values"] = [metrics(r, row["point"]["records"]) for r in row["reps"]]
        row["states"] = {h: state([v.get(h) for v in row["values"]]) for h in PREDICATES}
        row["states"]["H4"] = state([_h4_any(v) for v in row["values"]])
    return rows


def _passing(row, h):
    return row["states"][h] in ("通過", "停止")


def regions(rows):
    """Apply both blocks and both genomes before ranking opportunities."""
    candidates = []
    for h in ("H1", "H2", "H4"):
        definitions = []
        for n in (1, 2):
            for axes in itertools.combinations(FACTORS, n):
                for levels in itertools.product(*(FACTORS[a] for a in axes)):
                    definitions.append(("O", dict(zip(axes, levels))))
        for rr, long in itertools.product(FACTORS["rr"], FACTORS["long"]):
            for lo in range(len(SKEWS)):
                for hi in range(lo+1, len(SKEWS)):
                    definitions.append(("S", {"rr": rr, "long": long,
                                               "skew_interval": SKEWS[lo:hi+1]}))
        for layer, spec in definitions:
            groups = []
            if layer == "O":
                for block in ("O1", "O2"):
                    groups.append([v for v in rows.values() if v["point"]["layer"] == block
                                   and all(v["point"][k] == x for k, x in spec.items())])
            else:
                for skew in spec["skew_interval"]:
                    groups.append([v for v in rows.values() if v["point"]["layer"] == "S"
                                   and v["point"]["skew"] == skew and
                                   v["point"]["rr"] == spec["rr"] and
                                   v["point"]["long"] == spec["long"]])
            need = 6 if layer == "O" and len(spec) == 1 else 2 if layer == "O" else 1
            counts = []
            eligible = True
            for group in groups:
                for side in ("default", "best"):
                    subset = [v for v in group if (v["genome"] == "default") == (side == "default")]
                    if len(subset) != (9 if need == 6 else 3 if layer == "O" else 1):
                        eligible = False
                    count = sum(_passing(v, h) for v in subset)
                    counts.append(count)
                    if count < need:
                        eligible = False
            selected = [v for group in groups for v in group]
            if not selected:
                continue
            # Every point's best genome must pass its own block/level threshold.
            rate = sum(_passing(v, h) for v in selected)/len(selected)
            metric = {"H1": "h1", "H2": "h2", "H4": "lag_us"}[h]
            observations = [(math.inf if h == "H4" and v.get("publications") == 0 else v.get(metric))
                            for row in selected for v in row["values"]
                            if v.get(metric) is not None or h == "H4" and v.get("publications") == 0]
            med = statistics.median(observations) if observations else 0
            live_values = [v["live_ratio"] for row in selected for v in row["values"]
                           if v.get("live_ratio") is not None] if h == "H4" else []
            live_med = statistics.median(live_values) if live_values else 0
            candidates.append({"hypothesis": h, "layer": layer, "region": spec,
                               "eligible": eligible, "pass_rate": rate,
                               "median": med, "live_median": live_med, "counts": counts,
                               "condition_ids": sorted({v["id"] for v in selected})})
    chosen = []
    for h in ("H1", "H2", "H4"):
        pool = sorted((x for x in candidates if x["hypothesis"] == h and x["eligible"]),
                      key=lambda x: (-x["pass_rate"], -x["median"],
                                     -x["live_median"], str(x["region"])))
        chosen.extend(pool[:2])
    chosen = chosen[:5]
    if len(chosen) < 3:
        near = sorted((x for x in candidates if not x["eligible"]),
                      key=lambda x: (-x["pass_rate"], -x["median"], -x["live_median"]))
        for x in near[:3-len(chosen)]:
            chosen.append({**x, "label": "未達"})
    for x in chosen:
        x.setdefault("label", "採用")
    return chosen, len([x for x in chosen if x["label"] == "採用"]) < 3


def _layout(fig):
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = []
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if box.x0 < 0 or box.y0 < 0 or box.x1 > fig.bbox.width or box.y1 > fig.bbox.height:
            raise ValueError(f"figure text escapes canvas: {artist.get_text()!r}")
        if artist.axes is not None:
            for other in fig.axes:
                if other is not artist.axes and box.overlaps(other.bbox):
                    raise ValueError("figure text enters another panel")
        boxes.append((box, artist.get_text()))
    for i, (a, aname) in enumerate(boxes):
        for b, bname in boxes[i+1:]:
            if a.overlaps(b):
                raise ValueError(f"figure text overlaps: {aname!r} / {bname!r}")
    for ax in fig.axes:
        box = ax.get_tightbbox(renderer)
        if box is not None and (box.x0 < 0 or box.y0 < 0 or
                                box.x1 > fig.bbox.width or box.y1 > fig.bbox.height):
            raise ValueError("axis decoration escapes canvas")


def _save_figure(fig, stem, provenance):
    _layout(fig)
    for suffix in ("png", "pdf"):
        fig.savefig(stem.with_suffix("."+suffix), dpi=180)
    stem.with_suffix(".provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True)+"\n")


def _series(rows, layer, rr, long, side):
    return sorted((r for r in rows.values() if r["point"]["layer"] == layer and
                   r["point"]["rr"] == rr and r["point"]["long"] == long and
                   (r["genome"] == "default") == (side == "default")),
                  key=lambda r: r["point"]["skew"])


def draw_skew(rows, output, inputs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for title, names in (("depth", ("h1", "depth8")),
                         ("candidate", ("h2",)), ("abort", ("abort_rate",))):
        fig, axes = plt.subplots(3, 3, figsize=(17, 11), sharex=True, sharey=True)
        manifest = []
        for i, rr in enumerate(FACTORS["rr"]):
            for j, long in enumerate(FACTORS["long"]):
                ax = axes[i, j]
                for side, color in (("default", "tab:blue"), ("best", "tab:orange")):
                    series = _series(rows, "S", rr, long, side)
                    for metric, marker, style in ((names[0], "o", "-"),) + (
                        ((names[1], "s", "--"),) if len(names) == 2 else ()):
                        xys = [(r["point"]["skew"], [v.get(metric) for v in r["values"]], r["id"])
                               for r in series]
                        x = [x for x, ys, _ in xys if all(y is not None for y in ys)]
                        y = [statistics.mean(ys) for _, ys, _ in xys if all(y is not None for y in ys)]
                        if x:
                            ax.plot(x, y, marker=marker, linestyle=style, color=color,
                                    linewidth=1, markersize=3)
                            for xv, ys, cid in xys:
                                for k, value in enumerate(ys):
                                    if value is not None:
                                        ax.scatter(xv + (-.001 if k%2 else .001), value,
                                                   color=color, s=8, alpha=.5)
                                manifest.append({"id": cid, "metric": metric, "repetitions": ys})
                ax.set_title(f"rr {rr}% · {long}", fontsize=10)
                ax.set_xlim(.48, 1.01)
                ax.set_ylim(0, 1)
                ax.set_xticks((.5, .7, .9, .99))
                ax.grid(alpha=.2)
                if i == 2:
                    ax.set_xlabel("Zipf skew")
                if j == 0:
                    ax.set_ylabel("Observed fraction")
        fig.suptitle(f"S layer: {title} · 1M records, 10 ops, ro 0%, val 4 B, 48 threads, GC 100 µs\nBlue default; orange best. Circles ≥1; squares ≥8; small dots are repetitions.",
                     fontsize=11)
        fig.subplots_adjust(left=.07, right=.98, bottom=.08, top=.89, hspace=.34, wspace=.24)
        stem = output / f"skew_{title}"
        _save_figure(fig, stem, {"inputs": inputs, "campaign": "vhash-workload-space",
                                  "conditions": "S layer, each rr/long/genome; two repetitions",
                                  "metric": names, "plotted": manifest})
        plt.close(fig)


def draw_axes(rows, output, inputs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    axes_names = tuple(FACTORS)
    for h, metric in (("H1", "h1"), ("H2", "h2"),
                      ("H4-lag", "lag_us"), ("H4-live", "live_ratio")):
        fig, axes = plt.subplots(3, 3, figsize=(16, 11))
        manifest = []
        for ax, name in zip(axes.flat, axes_names):
            levels = FACTORS[name]
            for idx, level in enumerate(levels):
                selected = [r for r in rows.values() if r["point"]["layer"].startswith("O")
                            and r["point"][name] == level]
                for side, color, dx in (("default", "tab:blue", -.08),
                                        ("best", "tab:orange", .08)):
                    vals = [(r["id"], v.get(metric)) for r in selected
                            if (r["genome"] == "default") == (side == "default")
                            for v in r["values"] if v.get(metric) is not None]
                    if vals:
                        ax.scatter([idx+dx]*len(vals), [v for _, v in vals], color=color,
                                   s=5, alpha=.35)
                        ax.plot(idx+dx, statistics.median(v for _, v in vals),
                                marker="D", color=color, markersize=4)
                        manifest.extend({"id": cid, "axis": name, "level": level,
                                         "value": v} for cid, v in vals)
            ax.set_title(name, fontsize=10)
            ax.set_xticks(range(3), [str(x) for x in levels], fontsize=8)
            ax.grid(alpha=.2)
            if h in ("H1", "H2"):
                ax.set_ylim(0, 1)
            if h == "H4-live":
                ax.set_ylim(bottom=0)
            ax.yaxis.set_major_locator(plt.MaxNLocator(5))
            if h == "H4-lag":
                ax.set_yscale("log")
                ax.set_yticks((1, 1024, 1048576))
                ax.set_yticklabels(("1", "1k", "1M"))
        fig.suptitle(f"O layer main effects: {h} · O1+O2, two repetitions\nBlue default; orange best. Small dots: runs; diamonds: medians. Lag 0 publication is censored.", fontsize=11)
        fig.subplots_adjust(left=.10, right=.98, bottom=.06, top=.89, hspace=.35, wspace=.25)
        _save_figure(fig, output / f"axes_{h.lower().replace('-', '_')}",
                     {"inputs": inputs, "campaign": "vhash-workload-space",
                      "conditions": "O1/O2; all axis levels and both genomes",
                      "metric": metric, "plotted": manifest})
        plt.close(fig)


def _csv(path, rows, fields):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _md(path, rows, fields):
    def clean(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    with path.open("w") as f:
        f.write("|"+"|".join(fields)+"|\n|"+"|".join("---" for _ in fields)+"|\n")
        for row in rows:
            f.write("|"+"|".join(clean(row.get(k, "")) for k in fields)+"|\n")


def write_tables(rows, candidates, insufficient, output, inputs):
    full, hot, abort = [], [], []
    harmonic_cache = {}
    for row in sorted(rows.values(), key=lambda r: r["id"]):
        p = row["point"]
        base = {"id": row["id"], "layer": p["layer"], "genome": row["genome"],
                **{k: p[k] for k in FACTORS}}
        numeric_keys = sorted({k for v in row["values"] for k, value in v.items()
                               if type(value) in (int, float) and k not in PREDICATES})
        averages = {f"{k}_mean": statistics.mean(v[k] for v in row["values"]
                     if type(v.get(k)) in (int, float)) for k in numeric_keys
                    if any(type(v.get(k)) in (int, float) for v in row["values"])}
        repetitions = {f"{k}_rep{i}": value for i, values in enumerate(row["values"], 1)
                       for k, value in values.items()
                       if type(value) in (int, float) or value is None and k in numeric_keys}
        full.append({**base, **{h: row["states"][h] for h in (*PREDICATES, "H4")},
                     **averages, **repetitions,
                     "repetitions": json.dumps(row["values"], ensure_ascii=False,
                                               sort_keys=True)})
        norm_key = (p["records"], p["skew"])
        if norm_key not in harmonic_cache:
            harmonic = sum(1/(k+1)**p["skew"] for k in range(p["records"]))
            cumulative = 0.0
            hot_count = 0
            while cumulative < harmonic/2:
                hot_count += 1
                cumulative += hot_count**(-p["skew"])
            harmonic_cache[norm_key] = (harmonic, hot_count)
        harmonic, hot_count = harmonic_cache[norm_key]
        for i, rep in enumerate(row["reps"]):
            if not rep["valid"]:
                continue
            for chain in rep["chains"]:
                key = chain["key"]
                hot.append({**base, "repetition": i+1, "key": key,
                            "chain_status": chain["status"],
                            "chain_length": chain["length"], "scan_us": rep["scan_us"],
                            "zipf_analytic_probability": (key+1)**(-p["skew"])/harmonic,
                            "zipf_analytic_keys_for_half_mass": hot_count,
                            "note": "Zipf formula, not realized key frequency"})
            for reason, sides in rep["reasons"].items():
                abort.append({**base, "repetition": i+1, "reason": reason,
                              **sides, "total": sum(sides.values())})
    mean_fields = sorted({key for record in full for key in record if key.endswith("_mean")})
    rep_fields = sorted({key for record in full for key in record if "_rep" in key})
    fields = ["id", "layer", "genome", *FACTORS, *PREDICATES, "H4", *mean_fields,
              *rep_fields,
              "repetitions"]
    _csv(output/"all_points.csv", full, fields)
    _md(output/"all_points.md", full, fields)
    candidate_rows = [{**{k: v for k, v in c.items() if k not in ("region", "condition_ids")},
                       "region": json.dumps(c["region"], ensure_ascii=False),
                       "condition_ids": ",".join(c["condition_ids"])} for c in candidates]
    _md(output/"candidates.md", candidate_rows,
        ["hypothesis", "layer", "region", "label", "pass_rate", "median",
         "live_median", "counts", "condition_ids"])
    (output/"candidate_status.json").write_text(json.dumps(
        {"insufficient": insufficient, "eligible_count": sum(c["label"] == "採用" for c in candidates)},
        ensure_ascii=False, indent=2)+"\n")
    _csv(output/"hot_chains.csv", hot, [*base, "repetition", "key", "chain_status", "chain_length",
                                         "scan_us", "zipf_analytic_probability",
                                         "zipf_analytic_keys_for_half_mass", "note"])
    _csv(output/"abort_reasons.csv", abort, [*base, "repetition", "reason",
                                              *ABORT_SIDES, "total"])
    h4 = [{"id": r["id"], "genome": r["genome"],
           "H4_lag": r["states"]["H4-lag"], "H4_live": r["states"]["H4-live"],
           "H4_any": r["states"]["H4"],
           "stock_observation": [{k: v.get(k) for k in ("publications", "lag_us",
                                                         "live_versions", "live_ratio",
                                                         "maxrss_kb")} for v in r["values"]],
           "local_flag_opportunity": [v.get("local_flag_opportunity") for v in r["values"]]}
          for r in sorted(rows.values(), key=lambda x: x["id"])]
    _md(output/"h4_stock_local_flag.md", h4, list(h4[0]))
    (output/"provenance.json").write_text(json.dumps({
        "inputs": inputs, "campaign": "vhash-workload-space",
        "condition_count": len(rows), "thresholds": THRESHOLDS,
        "conditions": {r["id"]: r["point"] for r in rows.values()},
        "states": {r["id"]: r["states"] for r in rows.values()},
        "summary_values": {r["id"]: r["values"] for r in rows.values()},
        "instrumented_throughput_is_performance": False,
    }, ensure_ascii=False, indent=2, sort_keys=True)+"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        rows, inputs = load(args.raw)
        evaluate(rows)
        candidates, insufficient = regions(rows)
        args.output.mkdir(parents=True, exist_ok=True)
        write_tables(rows, candidates, insufficient, args.output, inputs)
        draw_skew(rows, args.output, inputs)
        draw_axes(rows, args.output, inputs)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"workload-space: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
