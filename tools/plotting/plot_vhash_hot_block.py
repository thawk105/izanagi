#!/usr/bin/env python3
"""Plot the VHash hot-block microbenchmark from raw per-repetition JSON."""
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
from matplotlib.ticker import FuncFormatter
import numpy as np

plt.rcParams["font.family"] = ["Droid Sans Fallback", "DejaVu Sans"]

SCHEMA = "izanagi-vhash-hot-block-microbench/v2"
PERF_EVENTS = ("cycles:u", "instructions:u", "cache-references:u", "cache-misses:u", "branch-misses:u")
K_VALUES = (1, 2, 3, 4, 8, 16)
DEPTH_VALUES = tuple(range(8)) + (8, 10, 12)
KEYSETS = ("in", "out")
READ_ARMS = ("linked_scattered", "linked_local", "contig_scalar", "contig_simd")
WRITE_ARMS = ("shift", "ring", "block", "linked_prepend")
VALUE_ROWS = (("external", 64), ("inline", 16), ("inline", 256))
STATE_PATTERNS = ("candidate_pending", "pending_newer_than_ts", "aborted_then_committed", "candidate_deleted")
BOOT_SEED = 20260929
BOOT_SAMPLES = 4000

class InputError(ValueError):
    pass

class FigureLayoutError(ValueError):
    pass

def fail(message):
    raise InputError(message)

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def finite_number(value, where, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(f"non-finite or invalid number at {where}")
    if positive and value <= 0:
        fail(f"nonpositive number at {where}")
    return value

def integer(value, where, minimum=0):
    finite_number(value, where)
    if not isinstance(value, int) or value < minimum:
        fail(f"invalid integer at {where}")
    return value

def field(obj, key, typ, where):
    if not isinstance(obj, dict) or key not in obj or not isinstance(obj[key], typ):
        fail(f"schema mismatch at {where}.{key}")
    return obj[key]

def numeric_tree(value, where):
    if isinstance(value, dict):
        for k, v in value.items(): numeric_tree(v, f"{where}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value): numeric_tree(v, f"{where}[{i}]")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        finite_number(value, where)

def bootstrap(values, seed):
    data = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.choice(data, size=(BOOT_SAMPLES, len(data)), replace=True)
    medians = np.median(draws, axis=1)
    return [float(np.percentile(medians, 2.5)), float(np.percentile(medians, 97.5))]

def grid_key(cell):
    group = cell["group"]
    if group == "k": return (group, cell["K"], cell["depth"], cell["keyset"])
    if group == "depth": return (group, cell["depth"], cell["keyset"])
    if group == "write": return (group, cell["K"], cell["value_mode"], cell["value_bytes"], cell["keyset"])
    if group == "state": return (group, cell["K"], cell["keyset"], cell["state_pattern"])
    if group == "value": return (group, cell["K"], cell["depth"], cell["keyset"], cell["value_mode"], cell["value_bytes"])
    if group == "pilot": return (group, cell["pilot_multiple"])
    return (group, cell["cell_id"])

def validate_cell(cell):
    required = ("cell_id", "group", "side", "K", "depth", "keyset", "n_keys", "capped", "value_mode", "value_bytes", "state_pattern", "ops", "wall_s", "expected_checksum", "shared_value_pool_bytes", "pilot_multiple", "arms")
    for name in required:
        if name not in cell: fail(f"schema mismatch: cell.{name}")
    if not isinstance(cell["cell_id"], str) or not cell["cell_id"]: fail("schema mismatch: cell_id")
    group = cell["group"]
    if group not in ("k", "depth", "state", "value", "write", "pilot"): fail("schema mismatch: group")
    if cell["side"] != ("write" if group == "write" else "read"): fail("schema mismatch: side")
    integer(cell["K"], "K", 1)
    if cell["depth"] is not None: integer(cell["depth"], "depth")
    if cell["keyset"] not in KEYSETS or (group == "pilot" and cell["keyset"] != "out"): fail("schema mismatch: keyset")
    integer(cell["n_keys"], "n_keys", 1)
    if type(cell["capped"]) is not bool: fail("schema mismatch: capped")
    if cell["value_mode"] not in ("none", "external", "inline"): fail("schema mismatch: value_mode")
    integer(cell["value_bytes"], "value_bytes")
    if cell["state_pattern"] is not None and not isinstance(cell["state_pattern"], str): fail("schema mismatch: state_pattern")
    integer(cell["ops"], "ops", 1)
    if type(cell["shared_value_pool_bytes"]) is not int:
        fail("invalid integer at shared_value_pool_bytes")
    integer(cell["shared_value_pool_bytes"], "shared_value_pool_bytes")
    finite_number(cell["wall_s"], "cell.wall_s", True)
    integer(cell["expected_checksum"], "expected_checksum")
    if group == "pilot": finite_number(cell["pilot_multiple"], "pilot_multiple", True)
    elif cell["pilot_multiple"] is not None: fail("schema mismatch: pilot_multiple")
    arms = field(cell, "arms", list, "cell")
    expected = set(WRITE_ARMS if group == "write" else READ_ARMS)
    if group == "pilot": expected = {"linked_scattered", "contig_scalar"}
    names = [field(a, "arm", str, "arm") for a in arms]
    if len(names) != len(set(names)) or set(names) != expected: fail(f"missing or duplicate arm: {cell['cell_id']}")
    rep_sets = []
    for arm in arms:
        footprint_bytes = integer(field(arm, "footprint_bytes", int, "arm"), "footprint_bytes", 1)
        per_key = integer(field(arm, "footprint_per_key_bytes", int, "arm"), "footprint_per_key_bytes", 1)
        if footprint_bytes != cell["n_keys"] * per_key: fail(f"footprint mismatch: {cell['cell_id']} {arm['arm']}")
        reps = field(arm, "reps", list, "arm")
        ids = []
        for rep in reps:
            ids.append(integer(field(rep, "rep", int, "rep"), "rep"))
            integer(field(rep, "order_pos", int, "rep"), "order_pos")
            elapsed = finite_number(field(rep, "elapsed_ns", (int, float), "rep"), "elapsed_ns", True)
            ns_per_op = finite_number(field(rep, "ns_per_op", (int, float), "rep"), "ns_per_op", True)
            expected_ns = elapsed / cell["ops"]
            if abs(ns_per_op - expected_ns) / expected_ns > 1e-9:
                fail(f"ns_per_op mismatch: {cell['cell_id']} {arm['arm']}")
            finite_number(field(rep, "checksum", (int, float), "rep"), "checksum")
            if rep["checksum"] != cell["expected_checksum"]: fail(f"checksum mismatch: {cell['cell_id']} {arm['arm']}")
        if len(ids) != 8 or len(set(ids)) != 8: fail(f"missing or duplicate rep: {cell['cell_id']} {arm['arm']}")
        rep_sets.append(set(ids))
        perf = field(arm, "perf", dict, "arm")
        perf_ops = integer(field(perf, "ops", int, "perf"), "perf.ops", 1)
        if perf_ops != cell["ops"]: fail(f"perf.ops mismatch: {cell['cell_id']} {arm['arm']}")
        events = field(perf, "events", dict, "perf")
        if set(events) != set(PERF_EVENTS): fail(f"missing or unexpected perf event: {cell['cell_id']} {arm['arm']}")
        for name, event in events.items():
            finite_number(field(event, "count", (int, float), "perf event"), f"perf.{name}.count")
            integer(field(event, "run_time_ns", int, "perf event"), f"perf.{name}.run_time_ns", 1)
            running_pct = finite_number(field(event, "running_pct", (int, float), "perf event"), f"perf.{name}.running_pct")
            if running_pct < 99.5 or running_pct > 100: fail(f"low or invalid running_pct: {cell['cell_id']} {arm['arm']} {name}")
        paths = field(perf, "raw_stderr_paths", list, "perf")
        if not paths or any(not isinstance(path, str) for path in paths): fail("schema mismatch: perf.raw_stderr_paths")
    if any(s != rep_sets[0] for s in rep_sets): fail(f"missing paired rep: {cell['cell_id']}")

def load_raw(paths):
    rows, inputs, ids, coordinates = [], [], set(), set()
    environment = None
    pilot_id = None
    pilot_multiple = None
    nonpilot_ref = None
    nonpilot_multiple = None
    for path in paths:
        raw = Path(path).read_bytes()
        doc = json.loads(raw)
        if not isinstance(doc, dict) or doc.get("schema") != SCHEMA: fail(f"schema mismatch: {path}")
        if "failure" in doc: fail(f"failed raw: {path}")
        numeric_tree(doc, str(path))
        for key in ("run_id", "shard", "host", "started_utc", "finished_utc"):
            field(doc, key, str, str(path))
        if doc["shard"] not in ("pilot", "read-k", "read-depth-state", "read-value", "write"): fail("schema mismatch: shard")
        finite_number(field(doc, "wall_s", (int, float), str(path)), "wall_s", True)
        source = field(doc, "source", dict, str(path))
        for key in ("bench_cc_sha256", "driver_sha256", "repo_head"): field(source, key, str, "source")
        build = field(doc, "build", dict, str(path))
        for key in ("compiler_path", "compiler_version", "binary_sha256"): field(build, key, str, "build")
        field(build, "argv", list, "build")
        if field(build, "objdump_check", dict, "build").get("passed") is not True: fail("build.objdump_check.passed is not true")
        env = field(doc, "env", dict, str(path))
        for key in ("python", "python_path", "path", "cpu_model", "perf_path"): field(env, key, str, "env")
        candidates = field(env, "perf_candidates_tried", list, "env")
        if any(not isinstance(item, str) for item in candidates): fail("schema mismatch: perf_candidates_tried")
        for key in ("avx2", "avx512f", "perf_control_ok"): 
            if type(env.get(key)) is not bool: fail(f"schema mismatch: env.{key}")
        for key in ("core", "l2_bytes", "llc_bytes", "mem_available_bytes", "perf_known_work_ratio"):
            finite_number(field(env, key, (int, float), "env"), f"env.{key}")
        integer(field(env, "perf_event_paranoid", int, "env"), "perf_event_paranoid", -10)
        tenant = field(env, "single_tenant", dict, "env")
        if type(tenant.get("ok")) is not bool or not isinstance(tenant.get("competitors"), list): fail("schema mismatch: single_tenant")
        if field(doc, "selfcheck", dict, str(path)).get("passed") is not True: fail("selfcheck.passed is not true")
        field(doc["selfcheck"], "vectors", list, "selfcheck")
        integer(field(doc["selfcheck"], "random_cases", int, "selfcheck"), "random_cases")
        multiple = finite_number(field(doc, "keyset_multiple", (int, float), str(path)), "keyset_multiple", True)
        if "pilot_ref" not in doc: fail("schema mismatch: pilot_ref")
        if doc["shard"] == "pilot":
            if doc["pilot_ref"] is not None: fail("pilot_ref mismatch: pilot raw must use null")
            if pilot_id is not None: fail("duplicate pilot raw")
            pilot_id, pilot_multiple = doc["run_id"], multiple
        else:
            ref = doc["pilot_ref"]
            if not isinstance(ref, str) or not ref: fail("pilot_ref mismatch: missing reference")
            if nonpilot_ref is not None and ref != nonpilot_ref: fail("pilot_ref mismatch between raws")
            if nonpilot_multiple is not None and multiple != nonpilot_multiple: fail("keyset_multiple mismatch between raws")
            nonpilot_ref, nonpilot_multiple = ref, multiple
        signature = (env["cpu_model"], build["compiler_version"], build["binary_sha256"])
        if environment is not None and signature != environment: fail("environment mismatch: cpu_model/compiler_version/binary_sha256")
        environment = signature
        cells = field(doc, "cells", list, str(path))
        shard_coordinates = set()
        for cell in cells:
            validate_cell(cell)
            if (cell["group"] == "pilot") != (doc["shard"] == "pilot"): fail("shard/group mismatch")
            if cell["cell_id"] in ids: fail(f"duplicate cell_id: {cell['cell_id']}")
            ids.add(cell["cell_id"])
            coordinate = grid_key(cell)
            if coordinate in coordinates: fail(f"duplicate grid coordinate: {coordinate}")
            coordinates.add(coordinate)
            shard_coordinates.add(coordinate)
            rows.append(cell)
        expected_shard = {
            "pilot": {("pilot", multiple) for multiple in (.5, 1, 2, 4, 8)},
            "read-k": required_coordinates("k"),
            "read-depth-state": {("depth", d, key) for d in DEPTH_VALUES for key in KEYSETS} | {("state", k, key, pattern) for k in (3, 8) for key in KEYSETS for pattern in STATE_PATTERNS},
            "read-value": {("value", k, depth, key, mode, size) for k in (3, 8) for depth in (0, k - 1) for key in KEYSETS for mode in ("external", "inline") for size in (16, 64, 256)},
            "write": required_coordinates("write"),
        }[doc["shard"]]
        if shard_coordinates != expected_shard: fail(f"missing grid cell or unexpected shard cell: {doc['shard']}")
        inputs.append({"path": str(Path(path).resolve()), "sha256": hashlib.sha256(raw).hexdigest()})
    if pilot_id is not None and nonpilot_ref is not None:
        if pilot_id != nonpilot_ref: fail("pilot_ref mismatch: pilot run_id")
        if pilot_multiple != nonpilot_multiple: fail("keyset_multiple mismatch: pilot raw")
    return rows, inputs, environment

def summarise(cells):
    result = []
    for cell in cells:
        baseline = "linked_prepend" if cell["side"] == "write" else "linked_scattered"
        rep_map = {a["arm"]: {r["rep"]: r["ns_per_op"] for r in a["reps"]} for a in cell["arms"]}
        arm_rows = []
        for arm in cell["arms"]:
            values = [r["ns_per_op"] for r in sorted(arm["reps"], key=lambda r: r["rep"])]
            ratios = [rep_map[arm["arm"]][rep] / rep_map[baseline][rep] for rep in sorted(rep_map[baseline])]
            perf = arm["perf"]
            per_op = {name: event["count"] / perf["ops"] for name, event in perf["events"].items()}
            miss_rate = perf["events"]["cache-misses:u"]["count"] / perf["events"]["cache-references:u"]["count"] if perf["events"]["cache-references:u"]["count"] else None
            arm_rows.append({"arm": arm["arm"], "median_ns_per_op": float(np.median(values)), "ci95_ns_per_op": bootstrap(values, BOOT_SEED), "paired_ratio_median": float(np.median(ratios)), "paired_ratio_ci95": bootstrap(ratios, BOOT_SEED), "perf_per_op": per_op, "cache_miss_rate": miss_rate, "perf_events": {name: {"run_time_ns": event["run_time_ns"], "running_pct": event["running_pct"]} for name, event in perf["events"].items()}, "footprint_bytes": arm["footprint_bytes"], "footprint_per_key_bytes": arm["footprint_per_key_bytes"]})
        result.append({"cell_id": cell["cell_id"], "group": cell["group"], "K": cell["K"], "depth": cell["depth"], "keyset": cell["keyset"], "n_keys": cell["n_keys"], "value_mode": cell["value_mode"], "value_bytes": cell["value_bytes"], "state_pattern": cell["state_pattern"], "pilot_multiple": cell["pilot_multiple"], "arms": arm_rows})
    return result

def required_coordinates(mode):
    if mode == "k": return {("k", k, d, key) for k in K_VALUES for d in (0, k + 2) for key in KEYSETS}
    if mode == "depth": return {("depth", d, key) for d in DEPTH_VALUES for key in KEYSETS}
    return {("write", k, value, size, key) for k in K_VALUES for value, size in VALUE_ROWS for key in KEYSETS}

def _intersection_area(left, right):
    return max(0, min(left.x1, right.x1) - max(left.x0, right.x0)) * max(0, min(left.y1, right.y1) - max(left.y0, right.y0))

def _contains(outer, inner, tolerance=0.5):
    return inner.x0 >= outer.x0 - tolerance and inner.y0 >= outer.y0 - tolerance and inner.x1 <= outer.x1 + tolerance and inner.y1 <= outer.y1 + tolerance

def check_figure_layout(fig, axes):
    """Fail on text overlap, figure overflow, and neighboring-panel intrusion."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    all_axes = list(fig.axes)
    hidden_ticks = set()
    for ax in all_axes:
        for axis in (ax.xaxis, ax.yaxis):
            low, high = sorted(axis.get_view_interval())
            for tick in (*axis.get_major_ticks(), *axis.get_minor_ticks()):
                if not low <= tick.get_loc() <= high:
                    hidden_ticks.update((tick.label1, tick.label2))
    text_boxes = []
    for label in fig.findobj(Text):
        if label in hidden_ticks or not label.get_visible() or not label.get_text().strip(): continue
        box = label.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0: continue
        if not _contains(fig.bbox, box): raise FigureLayoutError(f"text leaves figure: {label.get_text()!r}")
        if label.get_gid() == "cell-value" and (label.axes is None or not _contains(label.axes.bbox, box)):
            raise FigureLayoutError(f"cell annotation leaves its spine: {label.get_text()!r}")
        if label.axes is not None:
            for other in all_axes:
                if other is not label.axes and _intersection_area(box, other.bbox) > 1:
                    raise FigureLayoutError(f"text enters neighboring panel: {label.get_text()!r}")
        text_boxes.append((label, box))
    for i, (left_label, left_box) in enumerate(text_boxes):
        for right_label, right_box in text_boxes[i + 1:]:
            if _intersection_area(left_box, right_box) > 1:
                raise FigureLayoutError(f"text bbox overlap: {left_label.get_text()!r} / {right_label.get_text()!r}")
    for ax in all_axes:
        tight = ax.get_tightbbox(renderer)
        if tight is not None and not _contains(fig.bbox, tight, 1): raise FigureLayoutError("axes decoration leaves figure spine boundary")
    if len(axes) not in (2, 4, 6): raise FigureLayoutError("unexpected panel count")

def make_figure(mode, summary, cpu_model, compiler_version):
    lookup = {grid_key(row): row for row in summary}
    nrows = {"k": 2, "depth": 1, "write": 3}[mode]
    fig, grid = plt.subplots(nrows, 2, figsize=(18, 7 * nrows), squeeze=False)
    fig.subplots_adjust(left=.10, right=.98, top=.84, bottom=.10, hspace=.48, wspace=.30)
    title = {"k": "Hot-block capacity", "depth": "Version depth", "write": "Prepend cost"}[mode]
    fig.suptitle(title, y=.985, fontsize=17)
    subtitle = f"1 thread; fixed core; CPU {cpu_model}; compiler {compiler_version}; key counts per panel/cell; percentile bootstrap 95% CI (8 reps, descriptive); this AVX2 implementation"
    fig.text(.5, .935, subtitle, ha="center", va="center", fontsize=9)
    labels = {"linked_scattered": "Scattered linked", "linked_local": "Local linked", "contig_scalar": "Contiguous scalar", "contig_simd": "Contiguous AVX2", "shift": "Shift", "ring": "Ring", "block": "New block", "linked_prepend": "Linked prepend"}
    axes = []
    points = []
    for row in range(nrows):
        for col, keyset in enumerate(KEYSETS):
            ax = grid[row, col]
            axes.append(ax)
            if mode == "k":
                keys = [("k", k, (0 if row == 0 else k + 2), keyset) for k in K_VALUES]
                xs = K_VALUES
                heading = f"{'Newest' if row == 0 else 'Cold depth K+2'}; {'L2 resident' if keyset == 'in' else 'Beyond LLC'}"
            elif mode == "depth":
                keys = [("depth", d, keyset) for d in DEPTH_VALUES]
                xs = DEPTH_VALUES
                heading = "L2 resident" if keyset == "in" else "Beyond LLC"
                ax.axvline(8, color="0.45", linestyle=":", linewidth=1)
            else:
                value, size = VALUE_ROWS[row]
                keys = [("write", k, value, size, keyset) for k in K_VALUES]
                xs = K_VALUES
            cell_rows = [lookup[k] for k in keys]
            if mode == "write":
                counts = [cell["n_keys"] for cell in cell_rows]
                span = str(min(counts)) if min(counts) == max(counts) else f"{min(counts)}–{max(counts)}"
                heading = f"{value.capitalize()} {size} B; {span} keys"
            arms = WRITE_ARMS if mode == "write" else READ_ARMS
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _position: f"{value:g}"))
            for arm_name in arms:
                arm_rows = [next(a for a in cell["arms"] if a["arm"] == arm_name) for cell in cell_rows]
                y = [a["median_ns_per_op"] for a in arm_rows]
                for arm in arm_rows:
                    if arm["median_ns_per_op"] <= 0 or arm["ci95_ns_per_op"][0] <= 0 or arm["ci95_ns_per_op"][1] <= 0:
                        fail(f"nonpositive interval lower bound: {arm_name}")
                lower = [max(0, v - a["ci95_ns_per_op"][0]) for v, a in zip(y, arm_rows)]
                upper = [max(0, a["ci95_ns_per_op"][1] - v) for v, a in zip(y, arm_rows)]
                ax.errorbar(xs, y, yerr=[lower, upper], marker="o", capsize=2, linewidth=1.5, linestyle="--" if arm_name == "linked_prepend" else "-", label=labels[arm_name])
                for x, cell, arm in zip(xs, cell_rows, arm_rows):
                    points.append({"cell_id": cell["cell_id"], "arm": arm_name, "x": x, "median_ns_per_op": arm["median_ns_per_op"], "ci95_ns_per_op": arm["ci95_ns_per_op"], "paired_ratio_median": arm["paired_ratio_median"], "paired_ratio_ci95": arm["paired_ratio_ci95"]})
            ax.set_title(heading)
            ax.set_xticks(xs)
            ax.set_xlabel("Version capacity K" if mode != "depth" else "Version depth")
            ax.set_ylabel("ns/insert (対数軸)" if mode == "write" else "依存連鎖下の ns/selection (対数軸)")
            ax.grid(alpha=.20)
            ax.legend(loc="upper left", fontsize=8, frameon=False)
            ax.text(.98, .02, f"n_keys: {min(c['n_keys'] for c in cell_rows)}–{max(c['n_keys'] for c in cell_rows)}", transform=ax.transAxes, ha="right", va="bottom", fontsize=8)
    return fig, axes, points, subtitle

def run(mode, prefix, paths):
    cells, inputs, environment = load_raw(paths)
    actual = {grid_key(c) for c in cells}
    missing = required_coordinates(mode) - actual
    if missing: fail(f"missing grid cell: {sorted(missing, key=str)[0]}")
    summary = summarise(cells)
    fig, axes, points, caption = make_figure(mode, summary, environment[0], environment[1])
    try:
        check_figure_layout(fig, axes)
        outputs = {}
        for suffix in ("png", "pdf"):
            import io
            buffer = io.BytesIO()
            fig.savefig(buffer, format=suffix, dpi=160)
            outputs[suffix] = buffer.getvalue()
        for row in inputs:
            if sha256(row["path"]) != row["sha256"]: fail(f"input changed: {row['path']}")
        provenance = {"schema": "izanagi-vhash-hot-block-plot/v1", "mode": mode, "inputs": inputs, "generator": {"path": str(Path(__file__).resolve()), "sha256": sha256(__file__)}, "binary_sha256": environment[2], "cpu_model": environment[0], "compiler_version": environment[1], "caption": caption + "; scattered linked comparison; linked prepend has no cold migration", "points": points, "outputs": {suffix: {"path": str(Path(f'{prefix}.{suffix}').resolve()), "sha256": hashlib.sha256(data).hexdigest()} for suffix, data in outputs.items()}}
        summary_doc = {"schema": "izanagi-vhash-hot-block-summary/v1", "ci_method": "percentile bootstrap of medians, 95%, 4000 resamples, seed 20260929; repetition variation is descriptive", "cells": summary}
        payloads = {"png": outputs["png"], "pdf": outputs["pdf"], "provenance.json": (json.dumps(provenance, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode(), "summary.json": (json.dumps(summary_doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()}
        import os, tempfile
        parent = Path(prefix).parent
        parent.mkdir(parents=True, exist_ok=True)
        staged = []
        replaced = []
        try:
            for suffix, data in payloads.items():
                fd, name = tempfile.mkstemp(prefix=f".{Path(prefix).name}.", dir=parent)
                with os.fdopen(fd, "wb") as stream: stream.write(data)
                staged.append((Path(name), Path(f"{prefix}.{suffix}")))
            for source, target in staged:
                os.replace(source, target)
                replaced.append(target)
        except Exception:
            for target in replaced:
                target.unlink(missing_ok=True)
            raise
        finally:
            for source, _ in staged: source.unlink(missing_ok=True)
    finally:
        plt.close(fig)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("k", "depth", "write"))
    parser.add_argument("out_prefix")
    parser.add_argument("raw_json", nargs="+")
    args = parser.parse_args(argv)
    try:
        run(args.mode, args.out_prefix, args.raw_json)
    except (InputError, FigureLayoutError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"plot_vhash_hot_block: {error}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
