#!/usr/bin/env python3
"""Render the hash-bound A-2 four-cell certification result."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
import shlex
import statistics
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = Path(__file__).resolve()
SCHEMA = "izanagi-a2-certification-figure-provenance/v1"
CERT_SCHEMA = "paper-story-a2-certification-result/v3"
MANIFEST_SCHEMA = "paper-story-a2-raw-manifest/v3"
RAW_SCHEMA = "paper-story-a2-cell-result/v2"
STUDY = "paper-story-a2-certification"
WORKLOADS = ("rr5", "rr50")
CELLS = ("rr5-stock", "rr5-fixed10", "rr50-stock", "rr50-fixed5")
CANONICAL_SHA256 = {
    "certification": "f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40",
    "raw_manifest": "12d8be7a9cabd404ab3147301c2df7998a731b310ec51a93f9a99b37705a7c35",
}
DEFAULT_ROOT = Path("/work/1/SFC/tanab/izanagi-measurements/"
                    "dev-wave-paper-story-a2-cert-20260824/t2022-20260828c")
DEFAULT_CERT = REPO_ROOT / "output/insights/2026-08-24_paper-story-a2-certification/certification.json"
DEFAULT_MANIFEST = REPO_ROOT / "output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json"
_T975 = {4: 2.7764451051977987}
GATE_NOTE = ("The D1198 measurement-condition gate family was not applied to this run; "
             "condition identity rests on recorded genomes, build-admission receipts, and source-routed evidence.")
CORRECTNESS_NOTE = ("Correctness comes from separate trace-enabled runs and does not certify "
                    "or change the trace-disabled performance verdict.")

class FigureDataError(RuntimeError):
    """The authority, raw data, or provenance contract is invalid."""


class FigureLayoutError(FigureDataError):
    """The rendered figure violates the fail-closed layout contract."""

def _fail(message: str) -> None:
    raise FigureDataError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(65536), b""):
                digest.update(block)
    except OSError as exc:
        raise FigureDataError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()

def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise FigureDataError(f"cannot read JSON {path}: {exc}") from exc
    if type(value) is not dict:
        _fail(f"JSON root must be an object: {path}")
    return value

def _number(value: object, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        _fail(f"{label} must be finite" + (" and positive" if positive else ""))
    return result

def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())

def _load_tracked_authority(
    path: Path, kind: str, expected_hashes: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = dict(CANONICAL_SHA256 if expected_hashes is None else expected_hashes)
    if kind not in ("certification", "raw_manifest"):
        _fail(f"unknown tracked authority kind: {kind}")
    actual = _sha256(path)
    if kind == "certification" and actual != expected["certification"]:
        _fail("certification canonical SHA-256 mismatch")
    if kind == "raw_manifest" and actual != expected["raw_manifest"]:
        _fail("raw-manifest canonical SHA-256 mismatch")
    document = _json(path)
    schema = CERT_SCHEMA if kind == "certification" else MANIFEST_SCHEMA
    if document.get("schema_version") != schema:
        _fail(f"{kind} schema mismatch")
    return document, {
        "kind": kind, "path": _display_path(path), "sha256": actual,
        "schema": schema, "authority_scope": "canonical frozen report bytes",
    }

def _bench_done_rows(path: Path) -> list[dict[str, Any]]:
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FigureDataError(f"cannot parse WAL {path}: {exc}") from exc
    if any(type(row) is not dict or type(row.get("payload")) is not dict for row in records):
        _fail(f"WAL records must be objects with payload objects: {path}")
    return [row for row in records if row.get("stage") == "bench_done"]

def _summarize_samples(values: object) -> dict[str, float | int | list[float]]:
    if type(values) is not list or len(values) != 5:
        _fail("each performance cell must contain exactly five samples")
    samples = [_number(value, "TPS sample", positive=True) for value in values]
    mean = statistics.fmean(samples)
    stdev = statistics.stdev(samples)
    return {
        "n": 5, "samples_tps": samples, "median_tps": statistics.median(samples),
        "mean_tps": mean, "sample_stdev_tps": stdev,
        "ci95_half_tps": _T975[4] * stdev / math.sqrt(5), "cv": stdev / mean,
    }

def _external_plan(manifest: Mapping[str, Any], certification: Mapping[str, Any]) -> list[dict[str, Any]]:
    files = manifest.get("files")
    claims = manifest.get("campaign_claims")
    if type(files) is not dict or len(files) != 10 or type(claims) is not dict:
        _fail("raw-manifest must contain the ten-file closure and campaign claims")
    plan = []
    for workload in WORKLOADS:
        claim = claims.get(workload)
        if type(claim) is not dict or not isinstance(claim.get("campaign_id"), str):
            _fail(f"campaign claim missing: {workload}")
        campaign = claim["campaign_id"]
        plan.append({"kind": "wal", "workload": workload, "campaign": campaign,
                     "path": f"jobs/{workload}/campaigns/{campaign}/runs/wal.jsonl"})
    for cell in certification.get("cells", []):
        if type(cell) is not dict:
            _fail("certification cells must be objects")
        plan.append({"kind": "raw-cell", "workload": cell.get("workload"),
                     "cell": cell.get("cell_id"),
                     "path": f"jobs/{cell.get('workload')}/raw/{cell.get('cell_id')}.json"})
    if [row.get("cell") for row in plan if row["kind"] == "raw-cell"] != list(CELLS):
        _fail("certification cell order/identity mismatch")
    closure = {row["path"] for row in plan}
    for workload in WORKLOADS:
        claim = claims[workload]
        if not isinstance(claim.get("claim_path"), str):
            _fail(f"claim path missing: {workload}")
        closure.update((claim["claim_path"], f"jobs/{workload}/campaigns/{claim['campaign_id']}/campaign.lock"))
    if set(files) != closure:
        _fail("raw-manifest ten-file closure key set mismatch")
    for row in plan:
        digest = files.get(row["path"])
        if not isinstance(digest, str):
            _fail(f"external input is not bound by raw-manifest: {row['path']}")
        row["sha256"] = digest
    return plan

def _load_external_inputs(
    root: Path, manifest: Mapping[str, Any], certification: Mapping[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    wal: dict[str, list[dict[str, Any]]] = {}
    raw: dict[str, dict[str, Any]] = {}
    rows = _external_plan(manifest, certification)
    for row in rows:
        path = root / row["path"]
        if not path.is_file():
            _fail(f"external input missing: {row['path']}")
        if _sha256(path) != row["sha256"]:
            _fail(f"external input SHA-256 mismatch: {row['path']}")
        if row["kind"] == "wal":
            selected = _bench_done_rows(path)
            if len(selected) != 2:
                _fail(f"WAL must contain exactly two bench_done rows: {row['workload']}")
            wal[str(row["workload"])] = selected
        else:
            raw[str(row["cell"])] = _json(path)
    return wal, raw, rows

def _validate_raw_cell(
    raw: Mapping[str, Any], bench: Mapping[str, Any], certified: Mapping[str, Any],
    workload: str, certification: Mapping[str, Any], manifest: Mapping[str, Any],
) -> dict[str, Any]:
    payload = bench.get("payload")
    performance = raw.get("performance")
    build = raw.get("build_evidence")
    evidence = raw.get("campaign_evidence")
    if not all(isinstance(value, Mapping) for value in (payload, performance, build, evidence)):
        _fail("raw/WAL nested evidence is missing")
    if raw.get("schema_version") != RAW_SCHEMA or raw.get("cell_id") != certified.get("cell_id"):
        _fail("raw cell schema/identity mismatch")
    if raw.get("build_attempt_id") != payload.get("build_attempt_id") or raw.get("build_attempt_id") != certified.get("build_attempt_id"):
        _fail("raw/WAL/certification build_attempt_id mismatch")
    if performance.get("build_attempt_id") != raw.get("build_attempt_id"):
        _fail("raw/performance build_attempt_id mismatch")
    if raw.get("variant") != bench.get("variant"):
        _fail("raw/WAL variant mismatch")
    if raw.get("genome") != certified.get("genome"):
        _fail("raw/certification genome mismatch")
    if list(performance.get("samples_tps", [])) != list(payload.get("tps", [])):
        _fail("WAL samples and raw samples_tps mismatch")
    if build.get("source_commit") != certification.get("current_pin"):
        _fail("raw build_evidence.source_commit does not equal current_pin")
    campaign = manifest["campaign_claims"][workload]["campaign_id"]
    if evidence.get("campaign_id") != campaign:
        _fail("raw/manifest campaign identity mismatch")
    if (bench.get("env_tag") != "pegasus"
            or raw.get("attempt_id") != certification.get("attempt_id")
            or raw.get("protocol_sha256") != certification.get("protocol_sha256")
            or raw.get("current_pin") != certification.get("current_pin")
            or build.get("performance_trace_disabled_build") is not True
            or performance.get("trace_enabled") is not False
            or performance.get("status") != "complete"):
        _fail("raw performance authority identity mismatch")
    summary = _summarize_samples(payload.get("tps"))
    if summary["median_tps"] != _number(payload.get("median_tps"), "WAL median"):
        _fail("computed median and WAL median_tps mismatch")
    if not math.isclose(float(summary["cv"]), _number(payload.get("cv"), "WAL cv"), rel_tol=0, abs_tol=1e-12):
        _fail("computed CV and WAL cv mismatch")
    indicators = payload.get("leading_indicators")
    if not isinstance(indicators, Mapping):
        _fail("WAL leading_indicators missing")
    abort = _number(indicators.get("abort_rate"), "abort rate")
    if not 0 <= abort <= 1:
        _fail("abort rate must be in [0,1]")
    condition = performance.get("workload")
    expected = {"extime": 3, "records": 1_000_000, "reps": 5, "threads": 48,
                "workload": {"ycsb_max_ope": "10", "ycsb_rmw": "0",
                             "ycsb_rratio": "5" if workload == "rr5" else "50",
                             "ycsb_zipf_skew": "0.9"}}
    if condition != expected or not build.get("toolchain"):
        _fail("structured workload conditions are missing")
    return {
        "workload": workload, "role": certified.get("role"),
        "cell_id": certified.get("cell_id"), "variant": raw.get("variant"),
        "build_attempt_id": raw.get("build_attempt_id"), "genome": dict(raw["genome"]),
        **summary, "abort_rate": abort, "raw_crosscheck": True,
        "certification_crosscheck": True, "workload_conditions": dict(condition),
        "toolchain": dict(build.get("toolchain", {})),
    }

def _crosscheck_certification(cells: Sequence[Mapping[str, Any]], certification: Mapping[str, Any]) -> dict[str, float]:
    certified = {row["cell_id"]: row for row in certification["cells"]}
    for cell in cells:
        if cell["median_tps"] != _number(certified[cell["cell_id"]]["performance"]["median_tps"], "certification median"):
            _fail(f"computed/certification median mismatch: {cell['cell_id']}")
    by_workload = {w: {row["role"]: row for row in cells if row["workload"] == w} for w in WORKLOADS}
    computed = {w: by_workload[w]["adopted"]["median_tps"] / by_workload[w]["stock"]["median_tps"] - 1 for w in WORKLOADS}
    for workload, value in computed.items():
        if not math.isclose(value, _number(certification["effects"].get(workload), "certification effect"), rel_tol=0, abs_tol=1e-12):
            _fail(f"computed/certification effect mismatch: {workload}")
    return computed

def load_measurements(
    measurement_root: Path, certification_path: Path = DEFAULT_CERT,
    raw_manifest_path: Path = DEFAULT_MANIFEST,
    expected_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    certification, cert_row = _load_tracked_authority(Path(certification_path), "certification", expected_hashes)
    manifest, manifest_row = _load_tracked_authority(Path(raw_manifest_path), "raw_manifest", expected_hashes)
    identity = ("study", "attempt_id", "protocol_sha256", "current_pin")
    if any(certification.get(k) != manifest.get(k) for k in identity) or certification.get("study") != STUDY:
        _fail("tracked authority identity mismatch")
    if not isinstance(certification.get("status"), str) or not isinstance(certification.get("effects"), Mapping):
        _fail("certification status/effects are missing")
    wal, raw, external = _load_external_inputs(Path(measurement_root), manifest, certification)
    cells = []
    for certified in certification["cells"]:
        workload = str(certified["workload"])
        matches = [row for row in wal[workload] if row["payload"].get("build_attempt_id") == certified["build_attempt_id"]]
        if len(matches) != 1:
            _fail(f"bench_done/build attempt mapping is not unique: {certified['cell_id']}")
        cells.append(_validate_raw_cell(raw[certified["cell_id"]], matches[0], certified, workload, certification, manifest))
    if any(row["toolchain"] != cells[0]["toolchain"] for row in cells):
        _fail("toolchain differs across cells")
    effects = _crosscheck_certification(cells, certification)
    conditions = cells[0]["workload_conditions"]
    common = {key: conditions[key] for key in ("threads", "records", "reps", "extime")}
    common["zipf_skew"] = conditions["workload"]["ycsb_zipf_skew"]
    common["rmw"] = conditions["workload"]["ycsb_rmw"]
    common["max_ope"] = conditions["workload"]["ycsb_max_ope"]
    workload_rows = []
    for workload in WORKLOADS:
        claim = manifest["campaign_claims"][workload]
        sample = next(row for row in cells if row["workload"] == workload)
        wc = sample["workload_conditions"]["workload"]
        request = certification["request_ids"][workload]
        if not str(claim["claim"].get("job_id", "")).endswith(request):
            _fail(f"request/campaign claim mismatch: {workload}")
        workload_rows.append({"id": workload, "label": "write-heavy" if workload == "rr5" else "balanced",
                              "rratio": wc["ycsb_rratio"], "host": claim["claim"]["host"],
                              "request_id": request,
                              "campaign_id": claim["campaign_id"], "created_utc": claim["claim"]["created_utc"]})
    if len({row["request_id"] for row in workload_rows}) != 2 or len({row["created_utc"] for row in workload_rows}) != 2:
        _fail("workload campaigns must have distinct requests and recorded times")
    correctness = {row["cell_id"]: dict(row["correctness"]) for row in certification["cells"]}
    legacy_reps = {row["legacy_repetitions_observed"] for row in correctness.values()}; performance_reps = {row["performance_repetitions_observed"] for row in correctness.values()}
    if legacy_reps != {1} or performance_reps != {5} or any(row.get("status") != "certified" for row in correctness.values()):
        _fail("certification correctness projection mismatch")
    return {
        "tracked_inputs": [cert_row, manifest_row], "external_inputs": external,
        "external_root": str(Path(measurement_root).resolve()), "cells": cells,
        "measurement_conditions": {"attempt": certification["attempt_id"],
            "protocol_sha256": certification["protocol_sha256"],
            "izanagi_source_commit": certification["source_commit"],
            "ccbench_pin": certification["current_pin"], **common,
            "trace_disabled_performance": True, "perf_used": False, "environment": "pegasus",
            "toolchain": cells[0]["toolchain"], "workloads": workload_rows},
        "outer_status": certification["status"], "effects": dict(certification["effects"]),
        "effect_crosschecks": {w: {"computed": effects[w], "authority_matches": True} for w in WORKLOADS},
        "correctness": {"cells": correctness, "legacy_repetitions": next(iter(legacy_reps)),
            "performance_repetitions": next(iter(performance_reps)),
            "argv_observation_limit": certification["independent_observation_limits"]["correctness_run_argv"]},
    }

def _caption(data: Mapping[str, Any]) -> str:
    c = data["measurement_conditions"]
    w = {row["id"]: row for row in c["workloads"]}
    return (
        f"Figure 5. A-2 formal certification attempt {c['attempt']} (outer status: {data['outer_status']}). "
        f"The two independent workload campaigns were requests {w['rr5']['request_id']} on {w['rr5']['host']} "
        f"at {w['rr5']['created_utc']} and {w['rr50']['request_id']} on {w['rr50']['host']} at "
        f"{w['rr50']['created_utc']}, at distinct recorded times; the outer status is their logical conjunction. The top row shows all five "
        "trace-disabled performance samples per cell; short bars are medians, and diamonds with error bars are "
        "sample means with t-distribution 95% confidence intervals. The gray dashed line is the workload's no-backoff "
        f"median and the effect denominator. Median effects copied from certification are rr5 fixed 10 us "
        f"{100*data['effects']['rr5']:.4f}% and rr50 fixed 5 us {100*data['effects']['rr50']:.4f}%. M tps means "
        "million transactions per second. Mean confidence intervals describe samples; they are not confidence "
        "intervals for effects, decisions, or medians, and this artifact makes no significance decision. Reject is "
        "the protocol status based on the predefined median ratio. The bottom row is a descriptive leading indicator: "
        "one aggregate abort-rate point per cell, no confidence interval, and no causal mechanism claim. Correctness "
        "comes from separate trace-enabled runs: all four cells were certified, but this is not a performance "
        "certification. L01 limits that evidence to point-key traces; under D1257 the correctness argv was not "
        "independently recorded. The D1198 gate family was not applied to this run. Conditions: 48 threads, "
        "1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s, five repetitions, "
        f"CCBench pin {c['ccbench_pin']}, no perf, trace-disabled performance. Top-row y axes are scaled independently by workload; "
        "do not compare panel heights. The older series is not a comparator, and the cause of the sign difference "
        "has not been identified."
    )

def _artist_series(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for workload in WORKLOADS:
        selected = [row for row in data["cells"] if row["workload"] == workload]
        stock = next(row for row in selected if row["role"] == "stock")
        for x, cell in enumerate(selected):
            base = {"workload": workload, "cell_id": cell["cell_id"], "role": cell["role"], "genome": cell["genome"]}
            rows.extend([
                {**base, "kind": "sample-points", "label": f"{cell['cell_id']} samples", "x": x, "values_tps": cell["samples_tps"]},
                {**base, "kind": "mean-ci95", "label": f"{cell['cell_id']} mean and t95 CI", "x": x, "mean_tps": cell["mean_tps"], "ci95_half_tps": cell["ci95_half_tps"]},
                {**base, "kind": "median", "label": f"{cell['cell_id']} median", "x": x, "value_tps": cell["median_tps"]},
                {**base, "kind": "abort-point", "label": f"{cell['cell_id']} abort rate", "x": x, "value": cell["abort_rate"]},
            ])
        rows.append({"workload": workload, "cell_id": stock["cell_id"], "role": "stock", "genome": stock["genome"],
                     "kind": "baseline", "label": "no-backoff median", "value_tps": stock["median_tps"]})
        rows.append({"workload": workload, "cell_id": selected[1]["cell_id"], "role": "adopted", "genome": selected[1]["genome"],
                     "kind": "effect-label", "label": f"{100*data['effects'][workload]:.4f}%", "value": data["effects"][workload]})
    return rows

def make_figure(data: Mapping[str, Any]):
    mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.grid": True,
                         "grid.alpha": .18, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 7.6), squeeze=False)
    fig.subplots_adjust(left=.075, right=.98, top=.78, bottom=.12, wspace=.24, hspace=.48)
    colors = {"stock": "#666666", "adopted": "#b24a00"}
    jitter = (-.12, -.06, 0, .06, .12)
    for column, workload in enumerate(WORKLOADS):
        cells = [row for row in data["cells"] if row["workload"] == workload]
        stock = next(row for row in cells if row["role"] == "stock")
        top, bottom = axes[0, column], axes[1, column]
        for x, cell in enumerate(cells):
            color = colors[cell["role"]]
            top.scatter([x + value for value in jitter], [v / 1e6 for v in cell["samples_tps"]], s=20, color=color, zorder=3)
            top.errorbar([x], [cell["mean_tps"] / 1e6], yerr=[cell["ci95_half_tps"] / 1e6], fmt="D", color=color, capsize=4, zorder=4)
            top.hlines(cell["median_tps"] / 1e6, x - .20, x + .20, color=color, linewidth=2.0, zorder=4)
            bottom.scatter([x], [cell["abort_rate"]], marker="o" if x == 0 else "s", s=38, color=color, zorder=3)
        top.axhline(stock["median_tps"] / 1e6, color="#777777", linestyle="--", linewidth=1.1)
        adopted = next(row for row in cells if row["role"] == "adopted")
        label = top.text(1, adopted["median_tps"] / 1e6 + .08 * max(v["mean_tps"] for v in cells) / 1e6,
                         f"{100*data['effects'][workload]:.4f}%", ha="center", va="bottom", color=colors["adopted"], gid="direct-label")
        label.set_clip_on(True)
        meta = next(row for row in data["measurement_conditions"]["workloads"] if row["id"] == workload)
        top.set_title(f"{meta['label']} (rratio {meta['rratio']})")
        top.set_ylabel("throughput (M tps)")
        top.set_ylim(0, max(max(c["samples_tps"]) / 1e6 for c in cells) * 1.28)
        bottom.set_ylabel("abort rate (fraction)")
        bottom.set_ylim(0, 1)
        bottom.text(.5, .88, "descriptive; 1 aggregate/cell\nno CI; no causal claim", transform=bottom.transAxes,
                    ha="center", va="top", fontsize=7, gid="cell-label")
        for axis in (top, bottom):
            axis.set_xticks((0, 1), ("no backoff", f"fixed {adopted['genome']['BACKOFF_FIXED']} us"))
        bottom.set_xlabel("performance arm")
    fig.suptitle("A-2 four-cell certification — trace-disabled performance", y=.975, fontsize=11, fontweight="bold")
    fig.text(.5, .91, f"outer status: {data['outer_status']} (protocol status, median ratio)", ha="center", fontsize=9)
    fig.text(.5, .865, "correctness: separate trace-enabled runs, all 4 cells certified — not a performance certification",
             ha="center", fontsize=8)
    fig.text(.5, .025, "Throughput axes are scaled independently by workload; abort axes share 0-1. Mean t95 CI is descriptive.",
             ha="center", fontsize=7)
    fig._a2_artist_series = _artist_series(data)
    fig._a2_caption = _caption(data)
    return fig, axes

def _intersection(left, right) -> float:
    return max(0, min(left.x1, right.x1) - max(left.x0, right.x0)) * max(0, min(left.y1, right.y1) - max(left.y0, right.y0))

def _contains(outer, inner, tolerance: float = 1.0) -> bool:
    return inner.x0 >= outer.x0 - tolerance and inner.y0 >= outer.y0 - tolerance and inner.x1 <= outer.x1 + tolerance and inner.y1 <= outer.y1 + tolerance

def check_figure_layout(fig, axes) -> None:
    from matplotlib.text import Text
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    plot_axes = [axis for row in axes for axis in row]
    if len(plot_axes) != 4 or len(fig.axes) != 4:
        raise FigureLayoutError("production layout must contain four axes")
    boxes = []
    for text in fig.findobj(Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if box.width <= 0 or box.height <= 0:
            continue
        if not _contains(fig.bbox, box):
            raise FigureLayoutError(f"text leaves figure: {text.get_text()!r}")
        if text.get_gid() in ("direct-label", "cell-label") and (text.axes is None or not _contains(text.axes.bbox, box)):
            raise FigureLayoutError(f"annotation leaves owner axis: {text.get_text()!r}")
        if text.axes is not None:
            for other in fig.axes:
                if other is not text.axes and _intersection(box, other.bbox) > 1:
                    raise FigureLayoutError(f"text enters neighboring panel: {text.get_text()!r}")
        boxes.append((text, box))
    for index, (left, left_box) in enumerate(boxes):
        for right, right_box in boxes[index + 1:]:
            if _intersection(left_box, right_box) > 1:
                raise FigureLayoutError(f"text bbox overlap: {left.get_text()!r} / {right.get_text()!r}")
    for axis in fig.axes:
        tight = axis.get_tightbbox(renderer)
        if tight is not None and not _contains(fig.bbox, tight):
            raise FigureLayoutError("axis decoration leaves figure")

def build_provenance(
    data: Mapping[str, Any], outputs: Sequence[Path], argv: Sequence[str],
    *, hash_paths: Sequence[Path] | None = None, generated_utc: str | None = None,
) -> dict[str, Any]:
    hashes = outputs if hash_paths is None else hash_paths
    return {
        "schema": SCHEMA,
        "generated_utc": generated_utc or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generator": {"path": "tools/plotting/plot_a2_certification.py", "sha256": _sha256(GENERATOR)},
        "outputs": [{"path": _display_path(path), "sha256": _sha256(source)} for path, source in zip(outputs, hashes)],
        "tracked_inputs": list(data["tracked_inputs"]),
        "external_source_locator": {"root_at_generation": data["external_root"], "validation_key": "root-relative-path-plus-sha256"},
        "external_inputs": list(data["external_inputs"]),
        "measurement_conditions": dict(data["measurement_conditions"]),
        "cells": list(data["cells"]), "artist_series": _artist_series(data),
        "outer_status": data["outer_status"], "effects": dict(data["effects"]),
        "effect_crosschecks": dict(data["effect_crosschecks"]),
        "correctness": dict(data["correctness"]),
        "correctness_performance_note": CORRECTNESS_NOTE, "gate_note": GATE_NOTE,
        "caption": _caption(data),
        "reproduction": {"cwd": "repository-root", "argv": list(argv), "command": shlex.join(argv)},
    }

def _publish_outputs(fig, axes, prefix: Path, data: Mapping[str, Any], argv: Sequence[str]) -> list[Path]:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    destinations = [Path(f"{prefix}.png"), Path(f"{prefix}.pdf"), Path(f"{prefix}.provenance.json")]
    temporary: list[Path] = []
    try:
        check_figure_layout(fig, axes)  # required before the first save
        for suffix, fmt in ((".png", "png"), (".pdf", "pdf")):
            descriptor, raw = tempfile.mkstemp(prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent)
            os.close(descriptor)
            temp = Path(raw)
            temporary.append(temp)
            fig.savefig(temp, format=fmt, dpi=200)
        provenance = build_provenance(data, destinations[:2], argv, hash_paths=temporary)
        descriptor, raw = tempfile.mkstemp(prefix=f".{prefix.name}.", suffix=".provenance.json", dir=prefix.parent)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(provenance, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        temporary.append(Path(raw))
        for temp, destination in zip(temporary, destinations):
            os.replace(temp, destination)
        return destinations
    finally:
        for path in temporary:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

def validate_external_sources(provenance: Mapping[str, Any], measurement_root: Path) -> None:
    for row in provenance.get("external_inputs", []):
        path = Path(measurement_root) / row["path"]
        if not path.is_file() or _sha256(path) != row["sha256"]:
            _fail(f"external closure mismatch: {row['path']}")

def validate_repo_closure(provenance: Mapping[str, Any], repo_root: Path) -> None:
    if provenance.get("schema") != SCHEMA or provenance.get("generator", {}).get("path") != "tools/plotting/plot_a2_certification.py":
        _fail("landed provenance schema/generator path mismatch")
    # generator.sha256 is the generation-time record, not a live-source pin.
    for row in list(provenance.get("tracked_inputs", [])) + list(provenance.get("outputs", [])):
        path = Path(row["path"])
        resolved = path if path.is_absolute() else Path(repo_root) / path
        if not resolved.is_file() or _sha256(resolved) != row["sha256"]:
            _fail(f"landed repo closure mismatch: {row['path']}")
    manifest_rows = [row for row in provenance.get("tracked_inputs", []) if row.get("kind") == "raw_manifest"]
    if len(manifest_rows) != 1:
        _fail("landed provenance must track exactly one raw manifest")
    manifest_path = Path(manifest_rows[0]["path"])
    manifest = _json(manifest_path if manifest_path.is_absolute() else Path(repo_root) / manifest_path)
    files = manifest.get("files", {})
    for row in provenance.get("external_inputs", []):
        path, digest = row.get("path"), row.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str) or files.get(path) != digest:
            _fail(f"landed external input manifest mismatch: {path}")
    if provenance.get("artist_series") != _artist_series(provenance) or provenance.get("caption") != _caption(provenance):
        _fail("landed artist/caption projection mismatch")

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurement-root")
    parser.add_argument("--certification", default=str(DEFAULT_CERT))
    parser.add_argument("--raw-manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("out_prefix")
    return parser

def main(argv: Sequence[str] | None = None, *, expected_hashes: Mapping[str, str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.measurement_root or os.environ.get("IZANAGI_A2_CERTIFICATION_MEASUREMENT_ROOT", DEFAULT_ROOT)).resolve()
    cert, manifest, prefix = Path(args.certification).resolve(), Path(args.raw_manifest).resolve(), Path(args.out_prefix).resolve()
    expanded = ["python3", "tools/plotting/plot_a2_certification.py", "--measurement-root", str(root),
                "--certification", _display_path(cert), "--raw-manifest", _display_path(manifest),
                _display_path(prefix)]
    figure = None
    try:
        data = load_measurements(root, cert, manifest, expected_hashes)
        figure, axes = make_figure(data)
        _publish_outputs(figure, axes, prefix, data, expanded)
    except Exception as exc:  # noqa: BLE001 - the CLI must fail closed.
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if figure is not None:
            plt.close(figure)
    print(f"wrote {prefix}.png / .pdf / .provenance.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
