#!/usr/bin/env python3
"""Pinned B-7 fixed 5 us material: samples and recorded floor judgments."""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import statistics
import sys
import tempfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

SCHEMA = "izanagi-b7-fixed5-regression-figure-provenance/v1"
GENERATOR_PATH = "tools/plotting/plot_b7_fixed5_regression.py"
GENERATOR = Path(__file__).resolve()
REPO_ROOT = GENERATOR.parents[2]
STUDY = "paper-story-b7-fixed5-regression"
ATTEMPT_ID = "b7f5-20260919a"
CERT_SCHEMA = "paper-story-a2-certification-result/v4"
MANIFEST_SCHEMA = "paper-story-a2-full-raw-manifest/v4"
RAW_SCHEMA = "paper-story-a2-cell-result/v3"
FLOOR_SCHEMA = "between-run-noise-floor/v1"
POLICY_SCHEMA = "paper-story-a2-certification-policy/v2"
LEAF_DIR = "output/insights/2026-09-19_t1998-b7-fixed5-three-workload"
CERT_JSON = LEAF_DIR + "/certification.json"
MANIFEST_JSON = LEAF_DIR + "/raw-manifest.json"
WORKLOADS = ("rr5", "rr50", "rr95")
LABELS = dict(zip(WORKLOADS, ("write-heavy", "balanced", "read-heavy")))
RRATIOS = dict(zip(WORKLOADS, (5, 50, 95)))
FLOOR_JSON = {w: f"output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{w}_rmw0.json" for w in WORKLOADS}
POLICY_PATH = "orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json"
PINNED_SHA256 = {
    CERT_JSON: "b6493e4eed17e23cbe10682af72e7c06b805ced1e13a329ffd13df896f4d5431",
    MANIFEST_JSON: "be8163da33416020de3bfdca136ceaff5430e0878c46abe90681e6b0d954f6ac",
    FLOOR_JSON['rr5']: "25b4d2a070ad6e5ebf44973e134d7149a9fa0ec9996b3d6ef0f37a5b7b5a34b8",
    FLOOR_JSON['rr50']: "a94dc83ed21c8f9e390b1af642487c10e551f8f6e75ee977e9bad948fd745b26",
    FLOOR_JSON['rr95']: "23c024e467559b238b58ef9c32c144f78d23cb48ad7aafd6bbc02cd108842ce7",
    POLICY_PATH: "c6b24050d17c4bc552d254ce65e328b3a6edca919387b5720b4e025ea78b0df1",
}
INPUT_KINDS = ("certification", "raw_manifest", "floor_rr5", "floor_rr50", "floor_rr95", "policy")
CAPTION_SOURCE = "docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md"
CAPTION_SCOPE = "wording of limitations and conditions only; not measurement values, effects, or the floor judgment"
STOCK_GENOME = {"BACK_OFF": 0, "BACKOFF_FIXED": -1}
ADOPTED_GENOME = {"BACK_OFF": 1, "BACKOFF_FIXED": 5}
ADOPTED_US = 5
FLOOR_GENOME = "silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0"
REPS = 5
DF = 4
T975_DF4 = 2.7764451051977987
RECORDED_JUDGMENT = {"rr5": "no-regression", "rr50": "no-regression", "rr95": "regression"}
DEFAULT_MEASUREMENT_ROOT = "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a"
RAW_REL = {f"{w}-{role}": f"jobs/{w}/raw/{w}-{role}.json" for w in WORKLOADS for role in ("stock", "fixed5")}
CONDITIONS = {"threads": 48, "records": 1000000, "skew": "0.9", "rmw": "0", "max_ope": "10", "extime": 3, "reps": REPS, "ccbench_protocol": "silo"}


class FigureDataError(ValueError):
    """Invalid or incomplete evidence."""


class FigureLayoutError(FigureDataError):
    """Rendered text violates the layout contract."""


def _require(condition, message):
    if not condition:
        raise FigureDataError(message)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _number(value):
    _require(type(value) in (int, float) and math.isfinite(value), "finite number required")
    return value


def _string(value):
    _require(type(value) is str and bool(value.strip()), "nonempty string required")
    return value


def _digest(value):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "64 hex digest required")
    return value


def _summarize_samples(samples):
    _require(type(samples) is list and len(samples) == REPS, "sample count must be five")
    _require(all(_number(v) > 0 for v in samples), "positive samples required")
    sd = statistics.stdev(samples)
    return {"samples_tps": list(samples), "median_tps": statistics.median(samples),
            "mean_tps": statistics.fmean(samples), "stdev_tps": sd,
            "ci95_half_tps": T975_DF4 * sd / math.sqrt(REPS)}


def _load_tracked(root, expected_hashes):
    hashes = PINNED_SHA256 if expected_hashes is None else expected_hashes
    _require(set(hashes) == set(PINNED_SHA256), "input hash keys mismatch")
    tracked = []
    records = {}
    for path, kind in zip(PINNED_SHA256, INPUT_KINDS):
        digest = _sha256(root / path)
        _require(digest == hashes[path], f"SHA-256 mismatch: {path}")
        tracked.append({"kind": kind, "path": path, "sha256": digest})
        records[path] = _json(root / path)
    tracked.append({"kind": "caption_source", "path": CAPTION_SOURCE,
                    "sha256": _sha256(root / CAPTION_SOURCE), "authority_scope": CAPTION_SCOPE})
    return records, tracked, hashes


def _expected_cells():
    return [{"cell_id": f"{w}-{arm}", "workload": w, "role": role, "genome": genome}
            for w in WORKLOADS for arm, role, genome in
            (("stock", "stock", STOCK_GENOME), ("fixed5", "adopted", ADOPTED_GENOME))]


def _authority_data(root, expected_hashes):
    records, tracked, hashes = _load_tracked(root, expected_hashes)
    cert, manifest, policy = (records[p] for p in (CERT_JSON, MANIFEST_JSON, POLICY_PATH))
    for record, schema in ((cert, CERT_SCHEMA), (manifest, MANIFEST_SCHEMA), (policy, POLICY_SCHEMA)):
        _require(record["schema_version"] == schema, "schema mismatch")
        _require(record["study"] == STUDY, "study mismatch")
    for record in (cert, manifest):
        _require(record["attempt_id"] == ATTEMPT_ID, "attempt mismatch")
        _digest(record["protocol_sha256"])
    _require(cert["policy_sha256"] == hashes[POLICY_PATH], "policy SHA-256 mismatch")
    _require(cert["protocol_sha256"] == manifest["protocol_sha256"], "protocol mismatch")
    _require(cert["current_pin"] == manifest["current_pin"], "current pin mismatch")
    _require(set(cert["effects"]) == set(WORKLOADS), "effect keys mismatch")
    _require(set(cert["request_ids"]) == set(WORKLOADS), "request keys mismatch")
    for value in cert["request_ids"].values():
        _string(value)
    conditions = {k: policy["performance_common"][k] for k in CONDITIONS}
    _require(conditions == CONDITIONS, "policy conditions mismatch")
    _require([(w["id"], w["adopted_backoff_us"]) for w in policy["workloads"]] ==
             [(w, ADOPTED_US) for w in WORKLOADS], "policy workloads mismatch")
    expected = _expected_cells()
    _require([{("cell_id" if k == "id" else k): c[k] for k in ("id", "workload", "role", "genome")}
              for c in policy["cells"]] == expected, "policy cells mismatch")
    _require([{k: c[k] for k in e} for c, e in zip(cert["cells"], expected)] == expected
             and len(cert["cells"]) == 6, "certification cell order/identity mismatch")
    tokens = []
    for c in cert["cells"]:
        _require(c["source_binding_status"] == "bound", "source binding mismatch")
        token = _string(c["src_token"])
        if c["role"] == "stock":
            _require(token == "stock", "stock token mismatch")
        else:
            _require(token != "stock", "adopted stock token")
            tokens.append(token)
        q = c["correctness"]
        _require(q["status"] == "certified", "uncertified cell")
        _require(all(q[k] == "pass" for k in ("disposition", "legacy", "performance")), "correctness pass mismatch")
        _require(type(q["legacy_repetitions_observed"]) is int and q["legacy_repetitions_observed"] == 1
                 and type(q["performance_repetitions_observed"]) is int and q["performance_repetitions_observed"] == REPS,
                 "correctness repetition count")
        _require(c["performance"]["status"] == "complete", "incomplete performance")
        _require(_number(c["performance"]["median_tps"]) > 0, "positive median required")
        _digest(c["perf_bin_sha256"])
        _digest(c["trace_bin_sha256"])
    _require(len(set(tokens)) == 1, "adopted source tokens differ")
    external = [{"kind": "raw_cell", "path": path, "sha256": _digest(manifest["files"][path]), "cell_id": cid}
                for cid, path in RAW_REL.items()]
    floors, judgments = {}, {}
    for w in WORKLOADS:
        f = records[FLOOR_JSON[w]]
        _require(f["schema_version"] == FLOOR_SCHEMA, "floor schema mismatch")
        _require(f["genome"] == FLOOR_GENOME, "floor genome mismatch")
        _require(f["workload"] == {"ycsb_rratio": str(RRATIOS[w]), "ycsb_zipf_skew": "0.9", "ycsb_rmw": "0"}
                 and f["threads"] == 48 and f["records"] == 1000000, "floor workload mismatch")
        b = f["between_run"]
        cv = _number(b["cv"])
        _require(cv > 0 and b["sessions"] == 8 and b["reps_per_session"] == REPS
                 and b["high_variance"] is False, "floor conditions mismatch")
        floors[w] = {"cv": cv, "sessions": b["sessions"], "reps_per_session": b["reps_per_session"], "path": FLOOR_JSON[w]}
        effect = _number(cert["effects"][w])
        computed = "regression" if effect < -cv else "no-regression"
        _require(computed == RECORDED_JUDGMENT[w], "judgment mismatch")
        judgments[w] = {"recorded": RECORDED_JUDGMENT[w], "predicate": "effect < -floor (strict)",
                        "effect": effect, "neg_floor": -cv, "computed_matches_recorded": True}
    data = {"repo_root": str(root), "tracked_inputs": tracked, "external_inputs": external,
            "study": STUDY, "attempt_id": ATTEMPT_ID, "source_commit": _string(cert["source_commit"]),
            "ccbench_pin": _string(cert["current_pin"]), "request_ids": copy.deepcopy(cert["request_ids"]),
            "outer_status": _string(cert["status"]), "a4_noise_floor_status": _string(cert["a4_noise_floor_status"]),
            "measurement_conditions": conditions, "effects": copy.deepcopy(cert["effects"]),
            "floors": floors, "judgments": judgments}
    return data, cert


def _cell_summary(c, samples):
    summary = _summarize_samples(samples)
    _require(summary["median_tps"] == c["performance"]["median_tps"], "median mismatch")
    return {**{k: copy.deepcopy(c[k]) for k in ("cell_id", "workload", "role", "genome", "src_token", "perf_bin_sha256", "trace_bin_sha256")},
            "label": LABELS[c["workload"]], **summary,
            "correctness": {"status": c["correctness"]["status"], "legacy_records": 1,
                            "performance_records": REPS, "verdicts_all_serializable": True}}


def _effect_crosschecks(data):
    checks = {}
    for i, w in enumerate(WORKLOADS):
        computed = data["cells"][2*i+1]["median_tps"] / data["cells"][2*i]["median_tps"] - 1
        _require(math.isclose(computed, data["effects"][w], rel_tol=0, abs_tol=1e-12), "effect mismatch")
        checks[w] = {"computed": computed, "authority_matches": True}
    return checks


def load_evidence(repo_root, measurement_root, *, expected_hashes=None):
    """Read bound samples; check, rather than create, the recorded judgments."""
    try:
        root = Path(repo_root).resolve()
        data, cert = _authority_data(root, expected_hashes)
        cells = []
        for c, entry in zip(cert["cells"], data["external_inputs"]):
            path = Path(measurement_root) / entry["path"]
            _require(path.is_file(), f"raw missing: {entry['path']}")
            _require(_sha256(path) == entry["sha256"], "raw SHA-256 mismatch")
            raw = _json(path)
            _require(raw["schema_version"] == RAW_SCHEMA and raw["attempt_id"] == ATTEMPT_ID, "raw schema/attempt mismatch")
            _require(all(raw[k] == c[k] for k in ("cell_id", "src_token", "genome")), "raw identity mismatch")
            p, b = raw["performance"], raw["build_evidence"]
            _require(p["trace_enabled"] is False, "trace-enabled performance samples")
            _require(p["unstable"] is False, "unstable samples")
            _require(p["status"] == "complete", "raw incomplete performance")
            _require(p["perf_bin_sha256"] == c["perf_bin_sha256"], "performance binary mismatch")
            _require(b["performance_trace_disabled_build"] is True, "trace-disabled build required")
            _require(b["trace_bin_sha256"] == c["trace_bin_sha256"], "trace binary mismatch")
            cond = data["measurement_conditions"]
            expected_workload = {k: cond[k] for k in ("threads", "records", "reps", "extime")}
            expected_workload["workload"] = {"ycsb_rratio": str(RRATIOS[c["workload"]]),
                                             "ycsb_rmw": cond["rmw"], "ycsb_max_ope": cond["max_ope"], "ycsb_zipf_skew": cond["skew"]}
            _require(p["workload"] == expected_workload, "raw workload mismatch")
            for kind, count in (("legacy", 1), ("performance", REPS)):
                rows = raw["correctness"][kind]
                _require(type(rows) is list and len(rows) == count, "raw correctness count")
                for row in rows:
                    _require(row["verdict"] == "serializable", "raw verdict mismatch")
                    _require(row["certified"] is True and row["trace_enabled"] is True
                             and row["status"] == "pass" and row["integrity"] == "ok"
                             and row["trace_binary_sha256"] == c["trace_bin_sha256"], "raw correctness mismatch")
            cells.append(_cell_summary(c, p["samples_tps"]))
        data["cells"] = cells
        data["effect_crosschecks"] = _effect_crosschecks(data)
        return data
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        raise FigureDataError(f"invalid evidence: {exc}") from exc


def _figure_number(prefix):
    match = re.match(r"fig([0-9]+)_", Path(prefix).name)
    _require(match is not None, "output prefix basename must start with fig<N>_")
    return match.group(1)


def _judgment_label(recorded):
    return {"no-regression": "no regression", "regression": "regression (below -floor)"}[recorded]


def _caption(data, prefix):
    c = data["measurement_conditions"]
    columns = ", ".join(f"{LABELS[w]} ({w}, request {data['request_ids'][w]})" for w in WORKLOADS)
    effects = ", ".join(f"{LABELS[w]} {100*data['effects'][w]:+.4f}%" for w in WORKLOADS)
    floors = ", ".join(f"{LABELS[w]} {-100*data['floors'][w]['cv']:.4f}%" for w in WORKLOADS)
    judgments = ", ".join(f"{LABELS[w]} {_judgment_label(data['judgments'][w]['recorded'])}" for w in WORKLOADS)
    return " ".join([
        f"Figure {_figure_number(prefix)}. B-7 material: static backoff fixed 5 us versus stock (no backoff) in three workloads, attempt {data['attempt_id']} (study {data['study']}; outer status {data['outer_status']}; a4_noise_floor_status {data['a4_noise_floor_status']}).",
        f"Columns: {columns}, each an independent campaign in its own request, with the stock control measured in the same campaign immediately before the adopted cell.",
        "Top row: all five trace-disabled performance samples per cell; short bars are medians; diamonds with error bars are sample means with t-distribution 95% confidence intervals (df 4); the gray dashed line is the workload's stock median and the effect denominator.",
        f"Bottom row: median effects copied from certification (adopted median / stock median - 1): {effects}; dashed ticks mark -floor per workload: {floors}.",
        "The rule fixed before the results were seen classifies a workload as regression when effect < -floor (strict), floor being the D1639 between-run noise floor (coefficient of variation of the stock genome across 8 sessions of 5 repetitions, measured earlier under the same settings).",
        f"Result of that rule: {judgments}.",
        "No regression is neither superiority nor proof of no difference; the floor is not the standard error of the effect, and no significance decision is made.",
        "The outer status is the protocol's conjunction over the three workloads and follows from the negative read-heavy effect; it is not a research verdict.",
        "This is B-7 material, not a B-7 satisfaction decision (D2044 item 3).",
        "This figure reports a single attempt of five samples per cell; it does not promote the certification and does not speak to repeated attempts.",
        "Correctness comes from separate trace-enabled verify runs under the recorded check configuration, not the performance configuration: all 6 cells are recorded as certified with serializable verdicts (1 legacy and 5 performance records each); certified means serializability of the observed traces under that check configuration and nothing beyond, and this is not a performance certification.",
        f"Conditions: Pegasus compute nodes, {c['threads']} threads, {c['records']:,} records, Zipf {c['skew']}, read-modify-write disabled, max operations {c['max_ope']}, {c['extime']} s per repetition, {c['reps']} repetitions, silo, CCBench pin {data['ccbench_pin']}, source commit {data['source_commit'][:9]}, no perf, trace-disabled performance; the adopted cells share one source bytes digest across workloads but each workload is a separate build (binaries differ).",
        "M tps means million transactions per second.",
        "Mean confidence intervals describe samples; they are not confidence intervals for effects, medians, or the floor judgment.",
        "Top-row y axes are workload-local and must not be compared across panels.",
        "Existing materials with other adopted values are neither pooled nor compared.",
    ])


def _artist_series(data):
    rows = []
    for i, w in enumerate(WORKLOADS):
        cells = data["cells"][2*i:2*i+2]
        for x, c in enumerate(cells):
            for kind, values in (("sample-points", c["samples_tps"]), ("median", [c["median_tps"]]),
                                 ("mean-ci95", [c["mean_tps"], c["ci95_half_tps"]])):
                rows.append({"cell_id": c["cell_id"], "kind": kind, "x": x, "values": values})
        rows.append({"workload": w, "kind": "stock-median", "value": cells[0]["median_tps"]})
        rows.append({"workload": w, "kind": "effect-label", "label": f"{100*data['effects'][w]:+.4f}%"})
        rows.append({"workload": w, "kind": "effect-floor", "effect_pct": 100*data["effects"][w],
                     "neg_floor_pct": -100*data["floors"][w]["cv"], "judgment": data["judgments"][w]["recorded"], "zero": 0})
    return rows


def make_figure(data):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(12, 6.4))
    grid = fig.add_gridspec(2, 3, height_ratios=[1.0, .85])
    axes = np.array([fig.add_subplot(grid[0, i]) for i in range(3)] + [fig.add_subplot(grid[1, :])])
    fig.subplots_adjust(left=.075, right=.985, bottom=.12, top=.87, wspace=.30, hspace=.43)
    color = "#2166ac"
    for i, w in enumerate(WORKLOADS):
        ax = axes[i]
        cells = data["cells"][2*i:2*i+2]
        maximum = max(max(c["samples_tps"]) for c in cells) / 1e6
        for x, c in enumerate(cells):
            shade = "#666666" if x == 0 else color
            ax.scatter([x+j for j in (-.12, -.06, 0, .06, .12)], [v/1e6 for v in c["samples_tps"]],
                       s=20, color=shade, zorder=3, gid=f"{c['cell_id']}-samples")
            ax.hlines(c["median_tps"]/1e6, x-.20, x+.20, color=shade, linewidth=2, gid=f"{c['cell_id']}-median")
            ax.errorbar([x], [c["mean_tps"]/1e6], yerr=[c["ci95_half_tps"]/1e6], fmt="D", color=shade, capsize=4)
        ax.axhline(cells[0]["median_tps"]/1e6, color="#777777", linestyle="--", gid="stock-median")
        ax.text(1, max(c["median_tps"] for c in cells)/1e6 + .10*maximum, f"{100*data['effects'][w]:+.4f}%",
                ha="center", va="bottom", gid="direct-label")
        ax.set_title(f"{LABELS[w]} ({w})")
        ax.set_xticks([0, 1], ["stock", "fixed 5 us"])
        ax.set_xlim(-.5, 1.5)
        ax.set_ylim(0, maximum*1.28)
    axes[0].set_ylabel("throughput (M tps)")
    ax = axes[3]
    effects = [100*data["effects"][w] for w in WORKLOADS]
    floors = [-100*data["floors"][w]["cv"] for w in WORKLOADS]
    low, high = min(effects+floors+[0]), max(effects+floors+[0])
    span = high-low
    ax.set_ylim(low-.12*span, high+.12*span)
    ax.set_xlim(-.6, 2.6)
    ax.axhline(0, color="#555555", linewidth=.6, gid="zero")
    for i, w in enumerate(WORKLOADS):
        effect, floor = effects[i], floors[i]
        recorded = data["judgments"][w]["recorded"]
        ax.plot(i, effect, "o", color=color, markerfacecolor=color if recorded == "regression" else "white", gid=f"{w}-effect")
        ax.plot([i-.3, i+.3], [floor]*2, color="#b35806", linestyle="--", gid=f"{w}-floor")
        ax.annotate(f"{effect:+.4f}%", (i, effect), xytext=(8, 0), textcoords="offset points", va="center", gid="direct-label")
        # Separate the three text lanes horizontally so close effects and floors remain readable.
        ax.text(i-.30, floor+.035*span, f"-floor {floor:.4f}%", ha="left", va="bottom", gid="direct-label")
        ax.text(i, high+.075*span, _judgment_label(recorded), ha="center", va="center", fontsize=7, gid="direct-label")
    ax.set_xticks(range(3), [f"{LABELS[w]} ({w})" for w in WORKLOADS])
    ax.set_ylabel("median effect vs stock (%)")
    fig.legend(handles=[
        Line2D([], [], marker="o", linestyle="none", color=color, label="samples"),
        Line2D([], [], color=color, linewidth=2, label="median"),
        Line2D([], [], marker="D", color=color, label="mean ± t95 CI"),
        Line2D([], [], color="#777777", linestyle="--", label="stock median"),
        Line2D([], [], marker="o", markerfacecolor="white", linestyle="none", color=color, label="effect"),
        Line2D([], [], color="#b35806", linestyle="--", label="-floor")],
        loc="upper center", ncol=6, frameon=False)
    fig.text(.5, .015, "Top-row y axes are workload-local; do not compare panel heights. Mean t95 CI describes samples, not effects.", ha="center")
    fig._b7_artist_series = _artist_series(data)
    return fig, axes


def _intersection(left, right):
    return max(0, min(left.x1, right.x1) - max(left.x0, right.x0)) * max(0, min(left.y1, right.y1) - max(left.y0, right.y0))


def _contains(outer, inner):
    return inner.x0 >= outer.x0 - 1 and inner.y0 >= outer.y0 - 1 and inner.x1 <= outer.x1 + 1 and inner.y1 <= outer.y1 + 1


def check_figure_layout(fig, axes):
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    plot_axes = list(np.asarray(axes).flat)
    if len(plot_axes) != 4 or set(plot_axes) != set(fig.axes):
        raise FigureLayoutError("production layout must contain exactly four axes")
    boxes = []
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if not _contains(fig.bbox, box):
            raise FigureLayoutError(f"text leaves figure: {text.get_text()!r}")
        if text.get_gid() == "direct-label" and (text.axes is None or not _contains(text.axes.bbox, box)):
            raise FigureLayoutError("annotation leaves owner axis")
        if text.axes is not None:
            for other in fig.axes:
                if other is not text.axes and _intersection(box, other.bbox) > 1:
                    raise FigureLayoutError("text enters neighboring panel")
        boxes.append((text, box))
    for index, (left, box) in enumerate(boxes):
        for right, other in boxes[index + 1:]:
            if _intersection(box, other) > 1:
                raise FigureLayoutError(f"text bbox overlap: {left.get_text()!r} / {right.get_text()!r}")
    for axis in fig.axes:
        if not _contains(fig.bbox, axis.get_tightbbox(renderer)):
            raise FigureLayoutError("axis decoration leaves figure")


def build_provenance(data, outputs, argv, *, hash_paths=None, generated_utc=None, artist_series=None):
    hashes = outputs if hash_paths is None else hash_paths
    _require(len(outputs) == len(hashes) == 2, "two figure outputs required")
    return {
        **{key: copy.deepcopy(value) for key, value in data.items() if key not in ("repo_root", "tracked_inputs")},
        "tracked_inputs": copy.deepcopy(data["tracked_inputs"]),
        "schema": SCHEMA,
        "generated_utc": generated_utc or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generator": {"path": GENERATOR_PATH, "sha256": _sha256(GENERATOR)},
        "outputs": [{"path": os.path.relpath(Path(p).resolve(), data["repo_root"]), "sha256": _sha256(h)}
                    for p, h in zip(outputs, hashes)],
        "artist_series": copy.deepcopy(_artist_series(data) if artist_series is None else artist_series),
        "caption": _caption(data, Path(outputs[0]).with_suffix("")),
        "reproduction": {"cwd": "repository-root", "argv": list(argv), "command": shlex.join(argv)},
    }


def validate_repo_closure(provenance, repo_root, *, expected_hashes=None):
    """Check tracked authority and projections without consulting the durable root."""
    try:
        root = Path(repo_root).resolve()
        data, cert = _authority_data(root, expected_hashes)
        _require(provenance["schema"] == SCHEMA, "provenance schema mismatch")
        _require(provenance["generator"]["path"] == GENERATOR_PATH, "generator path mismatch")
        _digest(provenance["generator"]["sha256"])  # generation-time record, not a live-source pin
        _require(len(provenance["cells"]) == 6, "cells closure count")
        data["cells"] = [_cell_summary(c, row["samples_tps"]) for c, row in zip(cert["cells"], provenance["cells"])]
        data["effect_crosschecks"] = _effect_crosschecks(data)
        for key, value in data.items():
            if key != "repo_root":
                _require(provenance[key] == value, f"{key} closure mismatch")
        outputs = provenance["outputs"]
        _require(len(outputs) == 2 and [Path(r["path"]).suffix for r in outputs] == [".png", ".pdf"], "output paths mismatch")
        prefix = Path(outputs[0]["path"]).with_suffix("")
        _require(Path(outputs[1]["path"]).with_suffix("") == prefix, "output prefix mismatch")
        for row in outputs:
            _require(_sha256(root / row["path"]) == row["sha256"], "output closure mismatch")
        _require(provenance["artist_series"] == _artist_series(data), "artist closure mismatch")
        _require(provenance["caption"] == _caption(data, prefix), "caption closure mismatch")
    except (OSError, KeyError, TypeError, IndexError, ValueError) as exc:
        raise FigureDataError(f"invalid repo closure: {exc}") from exc


def validate_external_sources(provenance, measurement_root):
    try:
        rows = provenance["external_inputs"]
        _require([(r["cell_id"], r["path"], r["kind"]) for r in rows] ==
                 [(cid, path, "raw_cell") for cid, path in RAW_REL.items()], "external input set mismatch")
        for row in rows:
            _require(_sha256(Path(measurement_root) / row["path"]) == row["sha256"], "external closure mismatch")
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise FigureDataError(f"invalid external sources: {exc}") from exc


def _publish_outputs(fig, axes, prefix, data, argv):
    _figure_number(prefix)
    check_figure_layout(fig, axes)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    destinations = [Path(f"{prefix}{suffix}") for suffix in (".png", ".pdf", ".provenance.json")]
    temporary, published = [], []
    try:
        for suffix in (".png", ".pdf", ".provenance.json"):
            fd, name = tempfile.mkstemp(prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent)
            os.close(fd)
            temporary.append(Path(name))
        for path, fmt in zip(temporary[:2], ("png", "pdf")):
            fig.savefig(path, format=fmt, dpi=200)
        provenance = build_provenance(data, destinations[:2], argv, hash_paths=temporary[:2],
                                      artist_series=fig._b7_artist_series)
        temporary[2].write_text(json.dumps(provenance, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        previous = {p: p.read_bytes() if p.exists() else None for p in destinations}
        try:
            for source, destination in zip(temporary, destinations):
                os.replace(source, destination)
                published.append(destination)
        except OSError:
            for path in published:
                if previous[path] is None:
                    path.unlink()
                else:
                    path.write_bytes(previous[path])
            raise
        return destinations
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def main(argv=None, *, expected_hashes=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--measurement-root", type=Path, default=Path(DEFAULT_MEASUREMENT_ROOT))
    parser.add_argument("out_prefix", type=Path)
    args = parser.parse_args(argv)
    root, prefix = args.repo_root.resolve(), args.out_prefix.resolve()
    figure = None
    try:
        _figure_number(prefix)
        data = load_evidence(root, args.measurement_root.resolve(), expected_hashes=expected_hashes)
        figure, axes = make_figure(data)
        expanded = ["python3", GENERATOR_PATH, "--repo-root", str(root), "--measurement-root", str(args.measurement_root.resolve()), os.path.relpath(prefix, root)]
        _publish_outputs(figure, axes, prefix, data, expanded)
    except Exception as exc:
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if figure is not None:
            plt.close(figure)
    print(f"wrote {prefix}.png / .pdf / .provenance.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
