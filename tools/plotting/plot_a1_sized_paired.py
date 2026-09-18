#!/usr/bin/env python3
"""Pinned descriptive A-1 sized paired differences, attempt-0001."""
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
from matplotlib.patches import Patch

SCHEMA = "izanagi-a1-sized-paired-figure-provenance/v1"
GENERATOR_PATH = "tools/plotting/plot_a1_sized_paired.py"
GENERATOR = Path(__file__).resolve()
REPO_ROOT = GENERATOR.parents[2]
STUDY_ID = "paper-story-a1-20260901-balanced5-sized-v1"
RESULT_SCHEMA = "paper-story-a1-paired-result/v3"
RECEIPT_SCHEMA = "paper-story-a1-paired-receipt/v3"
COMPLETE_SCHEMA = "paper-story-a1-paired-materialization-complete/v1"
PAIRING_DESIGN = "balanced-a5b5-b5a5-v1"
CONTRAST = "variant-minus-baseline"
LEAF_DIR = "output/insights/2026-09-13/paper-story-a1-balanced5-sized"
RESULT_JSON = LEAF_DIR + "/result.json"
RECEIPT_JSON = LEAF_DIR + "/receipt.json"
COMPLETE_JSON = LEAF_DIR + "/.complete.json"
POLICY_PATH = "orchestrator/campaign/paper_story_a1_paired.v3-sized.json"
PINNED_SHA256 = {
    RESULT_JSON: "372f199e674cce28d46e2aeeed90b0f5b6c06e894bca63bcb779b580a8bb75a0",
    RECEIPT_JSON: "a2039dc1457cf34828714a98955faf3df68d335c0442d144122686f4e177e930",
    COMPLETE_JSON: "0b1f177944f6cab5c5eed5aa94a34beda11a06fcd8e94c1018d35c4e5e212a1e",
    POLICY_PATH: "a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a",
}
INPUT_KINDS = ("result", "receipt", "completion", "policy")
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
RRATIOS = {"write-heavy": 5, "balanced": 50, "read-heavy": 95}
VARIANT_ARMS = {"write-heavy": "fixed10", "balanced": "fixed5", "read-heavy": "fixed2"}
BASELINE_ARM = "no-backoff"
REPS = 30
DF = 29
FLOOR_FRACTION = 0.03
CAPTION_SOURCE = "docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md"
CAPTION_SCOPE = "wording of limitations and conditions only; not measurement values or classification"
COMPARISON_WARNING = "Panel y scales are workload-local and must not be compared across panels."
FIXED_LANE = "formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only"
FIXED_SCOPE = "This figure reports a single attempt of a non-certified lane: it is not a headline value, no cross-workload conclusion is drawn (preregistration section 7.2), it is not a reproduction of C1, and one attempt does not speak to stability across repeated attempts."
AUTHORITY = {"formal": False, "promotion_prohibited": True,
             "result_authority": "sized-preregistered-descriptive-only"}
STAT_FIELDS = {
    "mean": "mean_signed_positional_difference_tps",
    "variance": "sample_variance_positional_difference_tps2",
    "sd": "sample_sd_positional_difference_tps",
    "h": "descriptive_half_width_tps",
    "baseline_mean": "baseline_mean_tps", "B": "floor_boundary_tps",
}


class FigureDataError(ValueError):
    """Invalid or incomplete evidence."""


class FigureLayoutError(FigureDataError):
    """Rendered text violates the layout contract."""


def _require(condition, message):
    if not condition:
        raise FigureDataError(message)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _number(value):
    _require(type(value) in (int, float) and math.isfinite(value), "finite number required")
    return value


def _integer(value, expected):
    _require(type(value) is int and value == expected, "integer mismatch")


def _string(value):
    _require(type(value) is str and bool(value), "nonempty string required")
    return value


def _close(actual, expected):
    _require(math.isclose(_number(actual), _number(expected), rel_tol=1e-9, abs_tol=1e-6),
             f"numeric crosscheck mismatch: {actual} != {expected}")


def _lane(record):
    _require(record["formal"] is False, "formal must be false")
    _require(record["promotion_prohibited"] is True, "promotion_prohibited must be true")


def _flags(arm):
    return {"BACKOFF_FIXED": -1 if arm == BASELINE_ARM else int(arm.removeprefix("fixed")),
            "BACK_OFF": 0 if arm == BASELINE_ARM else 1,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}


def _genome(arm):
    return "silo|" + ",".join(f"{key}={value}" for key, value in _flags(arm).items())


def load_leaf(repo_root, *, expected_hashes=None):
    """Recompute statistics from pinned pairs and check recorded decisions."""
    try:
        return _load_leaf(Path(repo_root).resolve(), expected_hashes)
    except FigureDataError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        raise FigureDataError(f"malformed leaf: {exc}") from exc


def _load_leaf(root, expected_hashes):
    hashes = PINNED_SHA256 if expected_hashes is None else expected_hashes
    _require(set(hashes) == set(PINNED_SHA256), "input hash keys mismatch")
    tracked = []
    for path, kind in zip(PINNED_SHA256, INPUT_KINDS):
        digest = _sha256(root / path)
        _require(digest == hashes[path], f"SHA-256 mismatch: {path}")
        tracked.append({"kind": kind, "path": path, "sha256": digest})
    tracked.append({"kind": "caption_source", "path": CAPTION_SOURCE,
                    "sha256": _sha256(root / CAPTION_SOURCE), "authority_scope": CAPTION_SCOPE})
    result, receipt, complete, policy = [
        json.loads((root / path).read_text(encoding="utf-8")) for path in PINNED_SHA256]
    _require(complete["schema_version"] == COMPLETE_SCHEMA, "completion schema mismatch")
    _require(set(complete["files"]) == {"README.md", "receipt.json", "result.json"}, "completion files mismatch")
    for name, digest in complete["files"].items():
        _require(_sha256(root / LEAF_DIR / name) == digest, "completion file hash mismatch")
    for record, schema in ((result, RESULT_SCHEMA), (receipt, RECEIPT_SCHEMA)):
        _require(record["schema_version"] == schema, "schema mismatch")
        _require(record["study_id"] == STUDY_ID, "study mismatch")
        _lane(record)
    _lane(policy["authority"])
    _require(policy["authority"]["result_authority"] == AUTHORITY["result_authority"], "authority mismatch")
    _require(result["complete"] is True and result["all_workloads_terminal"] is True, "incomplete result")
    _require(result["measurement_error"] is None, "measurement error")
    _require(result["pairing_design"] == PAIRING_DESIGN, "pairing mismatch")
    _require(result["policy_sha256"] == _sha256(root / POLICY_PATH), "policy SHA-256 mismatch")
    _require(receipt["policy"]["sha256"] == result["policy_sha256"], "receipt policy mismatch")
    _require(set(result["workload_reps"]) == set(WORKLOADS), "workload reps keys")
    _require(tuple(w["workload"] for w in result["workloads"]) == WORKLOADS, "workload order/count")
    _require(tuple(w["name"] for w in policy["workloads"]) == WORKLOADS, "policy workload order/count")
    jobs = receipt["job_executions"]
    _require(tuple(j["workload"] for j in jobs) == WORKLOADS, "receipt jobs order/count")
    _require(policy["pairing"]["design"] == PAIRING_DESIGN and
             policy["pairing"]["contrast"] == CONTRAST, "policy pairing mismatch")
    cells = []
    for w, plan, job in zip(result["workloads"], policy["workloads"], jobs):
        name = w["workload"]
        variant = VARIANT_ARMS[name]
        for count in (result["workload_reps"][name], plan["reps"]):
            _integer(count, REPS)
        _integer(plan["df"], DF)
        _require(type(plan["k"]) is str and type(plan["planned_sigma_tps"]) is str, "policy numeric strings")
        k, sigma = _number(float(plan["k"])), _number(float(plan["planned_sigma_tps"]))
        _require(k > 0 and sigma > 0, "positive plan values")
        _require([(a["name"], a["role"]) for a in plan["arms"]] ==
                 [(variant, "variant"), (BASELINE_ARM, "baseline")], "policy arms mismatch")
        _require(w["valid"] is True and w["errors"] == [] and
                 w["terminal_result"]["status"] == "valid", "invalid workload")
        _require(set(w["arms"]) == {variant, BASELINE_ARM}, "arm set mismatch")
        correctness = {}
        for arm, arm_plan in zip((variant, BASELINE_ARM), plan["arms"]):
            _require(arm_plan["flags"] == _flags(arm) and arm_plan["protocol"] == "silo", "policy flags mismatch")
            a = w["arms"][arm]
            for key, expected in (("expected_reps", REPS), ("observed_reps", REPS),
                                  ("actual_rounds", 1), ("attempt_count", 1)):
                _integer(a[key], expected)
            _require(a["unstable"] is False and a["valid"] is True and a["errors"] == [], "invalid arm")
            _require(a["genome"] == _genome(arm), "genome mismatch")
            _require(type(a["raw_tps"]) is list and len(a["raw_tps"]) == REPS, "raw tps length")
            _require(all(_number(t) > 0 for t in a["raw_tps"]), "positive throughput required")
            evidence = a["correctness_evidence"]
            _require(type(evidence["certified"]) is list and len(evidence["certified"]) == 1
                     and evidence["certified"][0] is True, "uncertified arm")
            _require(evidence["verify_configs"] == ["legacy"], "verify config mismatch")
            _require(type(evidence["verify_done_frames"]) is list and
                     len(evidence["verify_done_frames"]) == 1, "verify frame count")
            correctness[arm] = copy.deepcopy(evidence)
        stat = w["statistics"]
        _integer(stat["n"], REPS)
        _integer(stat["df"], DF)
        _require(stat["contrast"] == CONTRAST and stat["pairing_design"] == PAIRING_DESIGN,
                 "statistics design mismatch")
        _require(_number(stat["floor_fraction"]) == FLOOR_FRACTION, "floor fraction mismatch")
        _close(stat["k"], k)
        _close(stat["planned_sigma_tps"], sigma)
        _require(type(stat["pairs"]) is list and len(stat["pairs"]) == REPS, "pair count")
        pairs = []
        for index, pair in enumerate(stat["pairs"]):
            _integer(pair["pair_index"], index)
            v, b, d = (_number(pair[f"{variant}_tps"]), _number(pair[f"{BASELINE_ARM}_tps"]),
                       _number(pair["signed_difference_tps"]))
            _require(d == v - b, "pair difference mismatch")
            _require(v == w["arms"][variant]["raw_tps"][index] and
                     b == w["arms"][BASELINE_ARM]["raw_tps"][index], "pair/raw mismatch")
            pairs.append({"pair_index": index, "variant_tps": v, "baseline_tps": b, "signed_difference": d})
        diff = [p["signed_difference"] for p in pairs]
        mean = statistics.fmean(diff)
        variance = sum((d - mean) ** 2 for d in diff) / (REPS - 1)
        sd = math.sqrt(variance)
        h = k * sd / math.sqrt(REPS)
        baseline_mean = statistics.fmean(w["arms"][BASELINE_ARM]["raw_tps"])
        B = FLOOR_FRACTION * baseline_mean
        values = dict(mean=mean, variance=variance, sd=sd, h=h, baseline_mean=baseline_mean, B=B)
        for key, field in STAT_FIELDS.items():
            _close(stat[field], values[key])
        interval = [mean - h, mean + h]
        _require(type(stat["descriptive_interval_tps"]) is list and
                 len(stat["descriptive_interval_tps"]) == 2, "interval length")
        for actual, expected in zip(stat["descriptive_interval_tps"], interval):
            _close(actual, expected)
        expected_class = ("resolved-above-floor" if abs(mean) - h > B else
                          "bounded-below-floor" if abs(mean) + h <= B else "unresolved")
        _require(stat["classification"] == expected_class, "classification mismatch")
        _require(stat["variance_plan_breach"] is (sd > sigma), "variance plan predicate mismatch")
        _require(stat["variance_plan_breach"] is False, "variance plan breach outside scope")
        cells.append({"workload": name, "rratio": RRATIOS[name], "variant_arm": variant,
                      "baseline_arm": BASELINE_ARM, "request_id": _string(job["request_id"]),
                      "host": _string(job["reservation_binding"]["host"]), "n": REPS, "df": DF, "k": k,
                      **values, "interval": interval, "classification": stat["classification"],
                      "variance_plan_breach": stat["variance_plan_breach"], "planned_sigma": sigma,
                      "pairs": pairs, "correctness": correctness})
    scale = policy["scale"]
    conditions = {"threads": scale["threads"], "records": scale["records"],
                  "skew": scale["ycsb_zipf_skew"], "rmw": scale["ycsb_rmw"],
                  "max_ope": scale["ycsb_max_ope"], "extime": scale["extime_s"],
                  "reps": REPS, "pairing_design": PAIRING_DESIGN, "contrast": CONTRAST,
                  "site": "pegasus-compute-only"}
    _require(type(result["limitations"]) is list and len(result["limitations"]) == 5 and
             all(type(v) is str for v in result["limitations"]), "limitations mismatch")
    return {"repo_root": str(root), "tracked_inputs": tracked, "study_id": STUDY_ID,
            "measurement_source_commit": _string(result["source_binding"]["measurement_source_commit"]),
            "ccbench_pin": _string(policy["ccbench_acceptance"]["canonical_pin"]),
            "measurement_conditions": conditions, "workloads": cells,
            "limitations": copy.deepcopy(result["limitations"]), "authority_note": dict(AUTHORITY)}


def _figure_number(prefix):
    match = re.match(r"fig([0-9]+)_", Path(prefix).name)
    _require(match is not None, "output prefix basename must start with fig<N>_")
    return match.group(1)


def _caption(data, prefix):
    cells = data["workloads"]
    columns = ", ".join(f"{c['workload']} (rr{c['rratio']}, {c['variant_arm']} minus {c['baseline_arm']})" for c in cells)
    jobs = ", ".join(c["request_id"] for c in cells)
    hosts = ", ".join(c["host"] for c in cells)
    values = "; ".join(f"{c['workload']} mean {c['mean']/1e6:+.3f} M tps (h {c['h']/1e6:.3f} M, B {c['B']/1e6:.3f} M, baseline mean {c['baseline_mean']/1e6:.3f} M)" for c in cells)
    classes = [c["classification"] for c in cells]
    classification = (f"{classes[0]} in all three workloads" if len(set(classes)) == 1 else
                      ", ".join(f"{c['workload']} {c['classification']}" for c in cells))
    signs = ["positive" if c["mean"] > 0 else "negative" if c["mean"] < 0 else "zero" for c in cells]
    c = data["measurement_conditions"]
    return " ".join([
        f"Figure {_figure_number(prefix)}. A-1 balanced five-rep paired comparison, sized run attempt-0001 (study {data['study_id']}; {FIXED_LANE}).",
        f"Columns: {columns}, each an independent campaign in its own job (job IDs, respectively: {jobs}; hosts {hosts}).",
        f"What is drawn: {REPS} paired differences (variant minus baseline, one per pair index under the balanced five-rep schedule, ten-pair groups in the order A^5 B^5 B^5 A^5 or B^5 A^5 A^5 B^5) as open markers; the arithmetic mean as a solid line with the registered interval mean ± h, h = k·s/√n, k = {cells[0]['k']} (t quantile at 1 − (1/120)/2 with df {DF}), s the sample standard deviation of the {REPS} differences; the zero line; and the registered floor boundary ±B, B = 3 % of the baseline-arm mean, as dashed lines. M tps means million transactions per second.",
        f"Values: {values}. The registered classification is {classification} (sign {signs[0]}, {signs[1]} and {signs[2]}, respectively); variance_plan_breach is false in all three.",
        "The interval and the classification are the descriptive outputs of the preregistered rule; they are not a hypothesis test and are not a performance certification.",
        FIXED_SCOPE,
        f"Conditions: Pegasus compute nodes, {c['threads']} threads, {c['records']:,} records, Zipf {c['skew']}, read-modify-write disabled, max operations {c['max_ope']}, {c['extime']} s per repetition, {c['reps']} pairs per workload, silo, CCBench pin {data['ccbench_pin'][:7]}, measurement source commit {data['measurement_source_commit'][:9]}, no perf, trace-disabled performance.",
        "Correctness comes from separate trace-enabled verify runs under the recorded legacy check configuration, not the performance configuration: all 6 arms are recorded as certified (result.json correctness_evidence, verify_done frames bound by SHA-256); certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification.",
        COMPARISON_WARNING,
        "Pilot observations did not enter the estimate; the estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state effect.",
    ])


def _artist_series(data):
    return [{"workload": c["workload"], "mean": c["mean"] / 1e6,
             "interval": [v / 1e6 for v in c["interval"]],
             "floor": [-c["B"] / 1e6, c["B"] / 1e6], "zero": 0.0,
             "x": [p["pair_index"] for p in c["pairs"]],
             "y": [p["signed_difference"] / 1e6 for p in c["pairs"]]}
            for c in data["workloads"]]


def make_figure(data):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), squeeze=False)
    fig.subplots_adjust(left=.075, right=.985, bottom=.18, top=.78, wspace=.30)
    series = _artist_series(data)
    color = "#2166ac"
    for ax, c, s in zip(axes.flat, data["workloads"], series):
        ax.plot(s["x"], s["y"], "o", linestyle="none", markerfacecolor="none",
                markersize=3.5, color=color, gid="pairs")
        ax.axhspan(*s["interval"], color=color, alpha=.18, gid="interval")
        ax.axhline(s["mean"], color=color, linewidth=1.3, gid="mean")
        ax.axhline(s["zero"], color="#555555", linewidth=.6, gid="zero")
        for y in s["floor"]:
            ax.axhline(y, color="#b35806", linestyle="--", linewidth=1, gid="floor")
        bounds = s["y"] + s["interval"] + s["floor"] + [s["zero"]]
        low, high = min(bounds), max(bounds)
        margin = .08 * (high - low)
        ax.set_ylim(low - margin, high + margin)
        ax.set_xlim(-1, REPS)
        ax.set_xticks(range(0, REPS, 5))
        ax.set_xlabel("pair index")
        ax.set_title(f"{c['workload']} (rr{c['rratio']}): {c['variant_arm']} - {c['baseline_arm']}", fontsize=8)
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    axes[0, 0].set_ylabel("paired difference (M tps)")
    fig.legend(handles=[
        Line2D([], [], marker="o", markerfacecolor="none", linestyle="none", color=color, label="pairs"),
        Line2D([], [], color=color, label="mean"),
        Patch(facecolor=color, alpha=.18, label="mean ± h"),
        Line2D([], [], color="#b35806", linestyle="--", label="±B floor"),
        Line2D([], [], color="#555555", linewidth=.6, label="zero")],
        loc="upper center", ncol=5, frameon=False)
    fig._a1_artist_series = series
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
    if len(plot_axes) != 3 or set(plot_axes) != set(fig.axes):
        raise FigureLayoutError("production layout must contain exactly three axes")
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
    """Bind landed images, caption source, cells, and projections to the current leaf."""
    try:
        root = Path(repo_root).resolve()
        data = load_leaf(root, expected_hashes=expected_hashes)
        _require(provenance["schema"] == SCHEMA, "provenance schema mismatch")
        _require(provenance["generator"] == {"path": GENERATOR_PATH, "sha256": _sha256(root / GENERATOR_PATH)},
                 "generator closure mismatch")
        for key, value in data.items():
            if key != "repo_root":
                _require(provenance[key] == value, f"{key} closure mismatch")
        outputs = provenance["outputs"]
        _require(len(outputs) == 2 and [Path(r["path"]).suffix for r in outputs] == [".png", ".pdf"],
                 "output paths mismatch")
        prefix = Path(outputs[0]["path"]).with_suffix("")
        _require(Path(outputs[1]["path"]).with_suffix("") == prefix, "output prefix mismatch")
        for row in outputs:
            _require(_sha256(root / row["path"]) == row["sha256"], "output closure mismatch")
        _require(provenance["artist_series"] == _artist_series(data), "artist closure mismatch")
        _require(provenance["caption"] == _caption(data, prefix), "caption closure mismatch")
    except (OSError, KeyError, TypeError, IndexError, ValueError) as exc:
        raise FigureDataError(f"invalid repo closure: {exc}") from exc


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
                                      artist_series=fig._a1_artist_series)
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
    parser.add_argument("out_prefix", type=Path)
    args = parser.parse_args(argv)
    root, prefix = args.repo_root.resolve(), args.out_prefix.resolve()
    figure = None
    try:
        _figure_number(prefix)
        data = load_leaf(root, expected_hashes=expected_hashes)
        figure, axes = make_figure(data)
        expanded = ["python3", GENERATOR_PATH, "--repo-root", str(root), os.path.relpath(prefix, root)]
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
