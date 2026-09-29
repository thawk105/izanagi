#!/usr/bin/env python3
"""Two paired figures from read-only GC publication raw runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import vhash_ro_gc_publish as P  # noqa: E402
from orchestrator.campaign import vhash_cicada_vlife as V  # noqa: E402

T95_5 = 2.57058184
IDS = tuple(P.CONDITIONS)


def paired_values(raw: dict, command: str, metric: str) -> dict[str, list[float | None]]:
    if raw.get("command") != command or set(raw.get("conditions", {})) != set(IDS):
        raise ValueError("complete raw condition grid required")
    if any(raw["conditions"][cid] != P.CONDITIONS[cid] for cid in IDS):
        raise ValueError("condition meaning differs from registered grid")
    if raw.get("ccbench_commit") != P.PIN or raw.get("error"):
        raise ValueError("raw identity or completion failure")
    env = raw.get("measurement_env", {})
    if (env.get("records"), env.get("extime"), env.get("workers")) != (1000000, 3, 48):
        raise ValueError("figure requires the registered 1M/3s/48-worker grid")
    groups = {(cid, rep): {} for cid in IDS for rep in range(1, 7)}
    for row in raw.get("runs", []):
        key = (row.get("condition"), row.get("rep"))
        arm = row.get("arm")
        if key not in groups or arm not in ("stock", "variant") or arm in groups[key]:
            raise ValueError("duplicate or unexpected paired run")
        if row.get("rc") != 0 or row.get("order") != list(P.ORDER[key[1] - 1]):
            raise ValueError("failed run or wrong order")
        if row.get("build", {}).get("trace") or (
                command == "throughput" and row.get("build", {}).get("vlife")):
            raise ValueError("wrong instrumentation")
        if command == "measure":
            parsed = V.parse_vlife_line(row["stdout"])
            if parsed != row.get("vlife") or parsed["schema_version"] != 2:
                raise ValueError("vlife raw mismatch")
            summary = V.summarize(parsed)
            durations = [x for x in row["argv"] if x.startswith("-extime=")]
            if len(durations) != 1 or not durations[0][8:].isdigit() or int(durations[0][8:]) <= 0:
                raise ValueError("one positive duration required")
            value = (summary["gc_publications"] / int(durations[0][8:])
                     if metric == "gc_publications_per_s" else
                     summary["gc_boundary_mean_us"])
        else:
            from orchestrator.calibrator.benchparse import parse_bench_stdout
            value = float(parse_bench_stdout(row["stdout"])["throughput[tps]"])
        groups[key][arm] = value
    if any(set(group) != {"stock", "variant"} for group in groups.values()):
        raise ValueError("missing paired run")
    result = {}
    for cid in IDS:
        values = []
        for rep in range(1, 7):
            group = groups[cid, rep]
            a, b = group["stock"], group["variant"]
            values.append(None if a is None or b is None else
                          (b / a if command == "throughput" and a > 0 else
                           b - a if command == "measure" else None))
        result[cid] = values
    return result


def boundary_context(raw: dict) -> dict:
    """Produce the (b) number table from validated, paired VLIFE runs."""
    paired_values(raw, "measure", "gc_publications_per_s")
    rows = {(row["condition"], row["rep"], row["arm"]): row
            for row in raw["runs"]}
    result = {}
    for cid in IDS:
        stock = []
        variant = []
        for rep in range(1, 7):
            s = V.summarize(V.parse_vlife_line(rows[cid, rep, "stock"]["stdout"]))
            v = V.summarize(V.parse_vlife_line(rows[cid, rep, "variant"]["stdout"]))
            publications = s["gc_publications"]
            stock.append({"publications": publications,
                          "publication_label": "公開 0 回" if publications == 0 else f"{publications} 回",
                          "boundary_age_us": s["gc_boundary_mean_us"] if publications else None,
                          "boundary_age_label": "未定義" if publications == 0 else None})
            holders = v["holder_fraction"]
            variant.append({"boundary_age_us": v["gc_boundary_mean_us"],
                            "ro_holder_fraction": None if holders[3] is None else
                            holders[3] + holders[4]})
        fractions = [point["ro_holder_fraction"] for point in variant]
        result[cid] = {"stock": stock, "variant": variant,
                       "variant_ro_holder_fraction": {
                           "repetitions": fractions,
                           "mean": None if any(x is None for x in fractions)
                           else sum(fractions) / len(fractions)}}
    for cid in IDS:
        cell = P.CONDITIONS[cid]
        if cell["delay"] != "wait10msR":
            continue
        none = next(key for key in IDS if all(
            P.CONDITIONS[key][field] == cell[field]
            for field in ("series", "ro_pct", "gc_inter_us"))
            and P.CONDITIONS[key]["delay"] == "none")
        points = []
        for rep in range(6):
            wait_age = result[cid]["variant"][rep]["boundary_age_us"]
            none_age = result[none]["variant"][rep]["boundary_age_us"]
            points.append(None if wait_age is None or none_age is None else
                          wait_age - none_age)
        result[cid]["variant_wait_minus_none_boundary_age_us"] = {
            "repetitions": points, "mean": None if any(x is None for x in points)
            else sum(points) / len(points)}
    return result


def load_raw(paths: list[Path], command: str) -> dict:
    if not paths:
        raise ValueError("raw files required")
    merged = {"command": command, "conditions": {}, "runs": [],
              "ccbench_commit": P.PIN}
    identity = None
    for path in paths:
        row = json.loads(path.read_text())
        if row.get("command") != command or row.get("error") or row.get("ccbench_commit") != P.PIN:
            raise ValueError("raw identity or completion failure")
        expected_patches = {patch.name: P.sha(patch) for patch in
                            (P.VARIANT, P.WORKLOAD, P.VLIFE, P.TRACE)}
        if row.get("patch_sha256") != expected_patches:
            raise ValueError("patch SHA differs from current source")
        if identity is None:
            identity = row.get("patch_sha256")
        elif identity != row.get("patch_sha256"):
            raise ValueError("mixed patch identities")
        if set(merged["conditions"]) & set(row.get("conditions", {})):
            raise ValueError("duplicate condition across raw files")
        merged["conditions"].update(row["conditions"])
        merged["runs"].extend(row["runs"])
        environment = row.get("measurement_env")
        if environment != {key: row.get(key) for key in
                           ("records", "extime", "workers", "site")}:
            raise ValueError("measurement environment differs from driver raw")
        if "measurement_env" not in merged:
            merged["measurement_env"] = environment
        elif merged["measurement_env"] != environment:
            raise ValueError("mixed measurement environment")
    merged["patch_sha256"] = identity
    return merged


def _mean_ci(values: list[float | None]) -> tuple[float, float] | None:
    if any(x is None or not math.isfinite(x) for x in values):
        return None
    array = np.asarray(values, dtype=float)
    return float(array.mean()), float(T95_5 * array.std(ddof=1) / np.sqrt(6))


def make_figure(publications: dict, boundary: dict, throughput: dict):
    plt.rcParams.update({"font.size": 8, "figure.dpi": 150})
    fig1, axes = plt.subplots(2, 1, figsize=(15, 8), constrained_layout=True)
    fig2, perf_ax = plt.subplots(figsize=(15, 5), constrained_layout=True)
    xs = np.arange(len(IDS))
    labels = [cid.replace("-gc10", "") for cid in IDS]
    for ax, values, title, unit in (
        (axes[0], publications, "Publication frequency: variant − stock", "publications/s"),
        (axes[1], boundary, "Boundary age: variant − stock", "µs"),
    ):
        for i, cid in enumerate(IDS):
            estimate = _mean_ci(values[cid])
            if estimate is not None:
                ax.errorbar([i], [estimate[0]], yerr=[estimate[1]], fmt="o",
                            color="tab:blue" if cid.startswith("S") else "tab:orange",
                            capsize=2)
            for rep, value in enumerate(values[cid]):
                if value is not None:
                    ax.scatter(i + (rep - 2.5) * .045, value, s=7, alpha=.35,
                               color="tab:blue" if cid.startswith("S") else "tab:orange")
        ax.axhline(0, color="black", linestyle="--", linewidth=.8)
        ax.set(title=title, ylabel=unit, xticks=xs, xticklabels=labels)
        ax.tick_params(axis="x", labelrotation=35)
        ax.grid(alpha=.2)
    for i, cid in enumerate(IDS):
        values = throughput[cid]
        estimate = _mean_ci(values)
        if estimate is not None:
            perf_ax.errorbar([i], [estimate[0]], yerr=[estimate[1]], fmt="o",
                             color="tab:blue" if cid.startswith("S") else "tab:orange",
                             capsize=2)
        for rep, value in enumerate(values):
            if value is not None:
                perf_ax.scatter(i + (rep - 2.5) * .045, value, s=9, alpha=.5,
                                color="tab:blue" if cid.startswith("S") else "tab:orange")
    perf_ax.axhline(1, color="black", linestyle="--", linewidth=.8,
                    label="same throughput as stock")
    perf_ax.set(title="Throughput: variant / stock", ylabel="ratio",
                xticks=xs, xticklabels=labels)
    perf_ax.tick_params(axis="x", labelrotation=35)
    perf_ax.grid(alpha=.2)
    fig1.suptitle("48 workers; 1M records; 3 s; GC 10 µs; S skew 0 / T skew 0.9")
    fig2.suptitle("48 workers; 1M records; 3 s; GC 10 µs; no TRACE, VLIFE or COUNT")
    return (fig1, fig2)


def check_figure_layout(fig) -> None:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.bbox
    labels = []
    for artist in fig.findobj(match=Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        if not (bounds.x0 <= box.x0 and box.x1 <= bounds.x1 and
                bounds.y0 <= box.y0 and box.y1 <= bounds.y1):
            raise ValueError("figure text outside canvas")
        labels.append((artist, box))
    # Tick labels on separate axes may align; text on the same axis may not overlap.
    for i, (left, box) in enumerate(labels):
        for right, other in labels[i + 1:]:
            if left.axes is right.axes and box.overlaps(other):
                raise ValueError("overlapping figure text")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measure", type=Path, nargs="+", required=True)
    parser.add_argument("--throughput", type=Path, nargs="+", required=True)
    parser.add_argument("--out-prefix", type=Path, required=True)
    args = parser.parse_args(argv)
    files = (*args.measure, *args.throughput)
    raw = [load_raw(args.measure, "measure"),
           load_raw(args.throughput, "throughput")]
    if raw[0].get("patch_sha256") != raw[1].get("patch_sha256"):
        raise ValueError("different patch identities")
    values = (paired_values(raw[0], "measure", "gc_publications_per_s"),
              paired_values(raw[0], "measure", "gc_boundary_mean_us"),
              paired_values(raw[1], "throughput", "throughput_tps"))
    context = boundary_context(raw[0])
    figures = make_figure(*values)
    for kind, fig in zip(("publication_boundary", "throughput"), figures):
        check_figure_layout(fig)
        stem = args.out_prefix.with_name(args.out_prefix.name + "-" + kind)
        stem.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(stem.with_suffix(".png"))
        fig.savefig(stem.with_suffix(".pdf"))
        provenance = {"campaign_id": "vhash-ro-gc-publish",
            "inputs": [{"path": str(path.resolve()),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                       for path in files],
            "conditions": raw[0]["conditions"],
            "measurement_env": [row["measurement_env"] for row in raw],
            "metric": kind,
            "boundary_context": context if kind == "publication_boundary" else None,
            "paired_values": values[:2] if kind == "publication_boundary" else values[2]}
        stem.with_suffix(".provenance.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
        plt.close(fig)
    table_path = args.out_prefix.with_name(args.out_prefix.name + "-boundary-table.json")
    table_path.write_text(json.dumps({"campaign_id": "vhash-ro-gc-publish",
        "inputs": [{"path": str(path.resolve()),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                   for path in args.measure],
        "measurement_env": raw[0]["measurement_env"], "conditions": context},
        indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
