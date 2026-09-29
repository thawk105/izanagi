#!/usr/bin/env python3
"""Cicada selective forwarding diagnostic (all values: 未検証の診断値).

Compute-node submission examples::

  python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:30:00 -- python3 -m orchestrator.campaign.vhash_forwarding_prototype smoke --third-party-cache /absolute/cache
  python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:40:00 -- python3 -m orchestrator.campaign.vhash_forwarding_prototype run --workload many_ops --third-party-cache /absolute/cache
  python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:20:00 -- python3 -m orchestrator.campaign.vhash_forwarding_prototype gc-run --workload wait_after_reads --wait-us 10000 --third-party-cache /absolute/cache --output /absolute/job-dir

The module only runs inside the submitted job. Its identity is hostname and start time;
PBS_JOBID is not required. No correctness or serializability claim follows from it.
For the md_6 workload, -ycsb_zipf_skew controls both ordinary and long-thread key selection.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import tempfile
import time
import statistics
from orchestrator.campaign.model import cmake_cache_variable_for_axis

from orchestrator.calibrator.benchparse import parse_bench_stdout
from orchestrator.calibrator.runner import competing_bench_pids
from . import condition_meaning_gate as condition
from . import patchharness, pin, s3_mocc_lock_coverage as compute
from .materializer_admission import non_admissible_materializer

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "patches/cicada-forwarding-variant.patch"
DEFAULT_OUTPUT = ROOT / "output/env/pegasus/vhash-forwarding-prototype"
DRIVER_ID = "orchestrator.campaign.vhash_forwarding_prototype"
MATERIALIZER = DRIVER_ID + "._build_variant"
MACROS = {"dependency": (), "stock": ("CICADA_LONGTX",), "fwd": ("CICADA_FWD_ENABLE", "CICADA_LONGTX"),
          "count": ("CICADA_FWD_ENABLE", "CICADA_FWD_COUNT", "CICADA_LONGTX"),
          "gc-dependency": (), "gc-stock": ("CICADA_LONGTX",),
          "gc-c": ("CICADA_FWD_ENABLE", "CICADA_LONGTX"),
          "gc-e": ("CICADA_FWD_ENABLE", "CICADA_LONGTX", "CICADA_GC_SAFEPOINT", "CICADA_GC_WAIT"),
          "gc-stock-count": ("CICADA_LONGTX", "CICADA_GC_COUNT"),
          "gc-c-count": ("CICADA_FWD_ENABLE", "CICADA_LONGTX", "CICADA_FWD_COUNT", "CICADA_GC_COUNT"),
          "gc-e-count": ("CICADA_FWD_ENABLE", "CICADA_LONGTX", "CICADA_FWD_COUNT", "CICADA_GC_SAFEPOINT", "CICADA_GC_WAIT", "CICADA_GC_COUNT")}
GC_PATCH = ROOT / "patches/cicada-forwarding-gc.patch"
GC_ARMS = ("stock", "C", "E-hb", "E")
GC_GENOME = {"BACK_OFF": 0, "INLINE_VERSION_OPT": 1,
             "INLINE_VERSION_PROMOTION": 0, "REUSE_VERSION": 1,
             "WRITE_LATEST_ONLY": 0}
GC_VALUE_BYTES = 4  # external/ccbench/cmake/Options.cmake CCBENCH_VAL_SIZE default
GC_TOP = frozenset(("schema", "mode", "sample_us", "clocks_per_us", "initial_versions",
    "version_struct_bytes", "threads", "uniform", "publish", "begin", "retention", "live_end"))
GC_THREAD = frozenset(("thid", "safepoints", "requests", "attempts", "success", "read_mismatch",
    "write_constraint", "conflict", "ineligible", "overflow", "publishes", "flag_raises",
    "advance_clock_sum", "held_checks", "held_changed", "early_publishes",
    "early_publish_then_fail", "installs", "detaches"))
GC_NESTED = {"uniform": ("count", "negative", "lag_rts_hist", "lag_rts_sum_us",
    "lag_rts_max_us", "lag_wts_hist", "live_sum", "live_max", "argmin_rts_thid",
    "series", "series_stride", "max_gap_intervals"), "publish": ("count", "lag_rts_hist", "interval_hist"),
    "begin": ("count", "lag_rts_hist"), "retention": ("count", "sum_us", "hist")}
WORKLOADS = ("normal", "many_ops", "wait_after_reads")
GC_VALUES = (10, 100, 1000)
COUNTER_PREFIXES = ("CICADA_FWD_V1 ", "CICADA_LONGTX_V1 ")
FWD_FIELDS = frozenset(("thid", "triggers", "attempts", "success", "read_mismatch",
    "write_constraint", "conflict", "ineligible", "no_target", "special_after_forward",
    "f_aborts", "advance_clock_sum", "pos_before_sum", "pos_after_sum"))
LONGTX_FIELDS = frozenset(("thid", "long", "commits", "aborts"))
MAX_CAPTURE = 65536


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def checked(argv: list[str], *, timeout: int = 300, cwd: Path | None = None):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"command failed rc={result.returncode}: {argv!r}; stderr={result.stderr[-2000:]!r}")
    return result


def build_args(dependencies: dict, toolchain: dict, kind: str) -> list[str]:
    args = [a for a in compute._common_configure_args(trace=0, toolchain=toolchain,
             dependencies=dependencies) if a not in compute.STOCK_G.cmake_defines()]
    if kind.startswith("gc-"):
        args += [f"-D{cmake_cache_variable_for_axis('cicada', key)}={value}"
                 for key, value in sorted(GC_GENOME.items())]
    return [*args, "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]


def _condition_gate(source: Path, macro: str, args: list[str], cxx: str) -> dict:
    start = time.monotonic()
    captured = condition.capture_define_inputs(source, configure_args=tuple(args))
    request = condition.make_define_request(driver_id=DRIVER_ID, macro=macro,
                                            requested_value=1, default_value=0)
    with condition._configured_define_compile_commands(captured, request=request,
             cxx=cxx, cmake="cmake") as commands:
        supply = condition.evaluate_define_supply_effectuation(captured, request=request,
             cxx=cxx, cmake="cmake", configured_commands=commands)
        meaning = condition.evaluate_define_runtime_meaning(captured, request=request,
             declaration=condition.declare_define_runtime_meaning(request), cxx=cxx,
             cmake="cmake", configured_commands=commands)
    admission = condition.require_condition_gate_family([supply], [meaning],
                                                          use_class="raw-measurement")
    receipt = {"macro": macro, "evidence_scope": "compile 条件の証拠",
               "seconds": time.monotonic() - start,
               "supply": json.loads(supply.canonical_json()),
               "meaning": json.loads(meaning.canonical_json()),
               "admission": json.loads(admission.canonical_json())}
    if not admission.admitted:
        error = RuntimeError(f"condition gate rejected {macro}")
        error.condition_gate_evidence = receipt
        raise error
    return receipt


def _build_variant(source: Path, build: Path, kind: str, dependencies: dict,
                   toolchain: dict) -> tuple[Path, list[dict], float]:
    """Single Cicada build sink, including the ungated dependency build."""
    non_admissible_materializer(MATERIALIZER)
    start = time.monotonic()
    args = build_args(dependencies, toolchain, kind)
    receipts = [_condition_gate(source, macro, args, toolchain["cxx_path"])
                for macro in MACROS[kind]]
    if len(receipts) != len(MACROS[kind]) or any(
            r["admission"]["admitted"] is not True for r in receipts):
        raise RuntimeError("condition gate rejected before build")
    if MACROS[kind]:
        args.append("-DCMAKE_CXX_FLAGS=" + " ".join(
            "-D" + macro + "=1" for macro in MACROS[kind]))
    configure = ["cmake", "-S", str(source), "-B", str(build),
                 "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args]
    checked(configure, timeout=600)
    checked(["cmake", "--build", str(build), "--target", "ycsb_cicada.exe", "-j", "48"],
            timeout=900)
    binary = build / "cc/cicada/ycsb_cicada.exe"
    if not binary.is_file():
        raise RuntimeError(f"missing binary: {binary}")
    return binary, receipts, time.monotonic() - start


def _compile_entry(build: Path, filename: str) -> dict:
    entries = json.loads((build / "compile_commands.json").read_text())
    markers = ("CMakeFiles/ycsb_cicada.exe.dir/", "CMakeFiles/ycsb_cicada.dir/")
    found = []
    for entry in entries:
        if (Path(entry["file"]).name != filename or
                "/cc/cicada/" not in Path(entry["file"]).as_posix()):
            continue
        argv = entry.get("arguments") or shlex.split(entry["command"])
        output = entry.get("output")
        surface = " ".join((*argv, output if type(output) is str else ""))
        if any(marker in surface for marker in markers):
            found.append(entry)
    if len(found) != 1:
        raise RuntimeError(f"expected one compile command for {filename}, found {len(found)}")
    return found[0]


def _inert_entry(entry: dict) -> tuple[dict, list[str]]:
    """Remove forwarding defines from a stock target command, preserving other flags."""
    argv = list(entry.get("arguments") or shlex.split(entry["command"]))
    names = ("CICADA_FWD_ENABLE", "CICADA_FWD_COUNT", "CICADA_LONGTX")
    clean, removed = [], []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "-D" and index + 1 < len(argv) and any(
                argv[index + 1].split("=", 1)[0] == name for name in names):
            removed.extend(argv[index:index + 2])
            index += 2
        elif arg.startswith("-D") and any(
                arg[2:].split("=", 1)[0] == name for name in names):
            removed.append(arg)
            index += 1
        else:
            clean.append(arg)
            index += 1
    return {**entry, "arguments": clean}, removed


def _preprocess(entry: dict) -> str:
    argv = list(entry.get("arguments") or shlex.split(entry["command"]))
    clean = []
    skip = False
    for arg in argv:
        if skip:
            skip = False
            continue
        if arg in ("-o", "-c"):
            skip = arg == "-o"
            continue
        clean.append(arg)
    result = checked([*clean, "-E"], cwd=Path(entry["directory"]), timeout=180)
    return sha_bytes(b"\n".join(line for line in result.stdout.splitlines()
                     if line.strip() and not line.lstrip().startswith(b"#")))


def _inert_receipt(source: Path, stock_build: Path) -> dict:
    """Pin and patched source use the same compiler argv and build directory."""
    selected = {name: _compile_entry(stock_build, name) for name in
                ("transaction.cc", "ycsb_cicada.cc")}
    sanitized = {name: _inert_entry(entry) for name, entry in selected.items()}
    entries = {name: pair[0] for name, pair in sanitized.items()}
    removed = {name: pair[1] for name, pair in sanitized.items()}
    before = {name: _preprocess(entry) for name, entry in entries.items()}
    with patchharness.applied(str(PATCH), pin.CURRENT_PIN, str(source)):
        after = {name: _preprocess(entry) for name, entry in entries.items()}
    receipt = {"gate": False, "normalization": "remove lines beginning with # after leading whitespace and whitespace-only lines",
               "removed_macro_args": removed,
               "pin_sha256": before, "patched_sha256": after,
               "matched": before == after}
    if not receipt["matched"]:
        error = RuntimeError("inert preprocessing mismatch")
        error.inert_receipt = receipt
        raise error
    return receipt


def order_rotation(rep: int) -> tuple[str, str, str]:
    arms = ("stock", "c", "f")
    return tuple(arms[(rep + i) % 3] for i in range(3))


def plan_runs(command: str, workload: str | None, k_sweep: bool = False) -> list[dict]:
    result = []
    workloads = WORKLOADS if command == "smoke" else (workload,)
    if command == "smoke":
        for w in workloads:
            for index, policy in enumerate(("c", "f")):
                result.append(dict(workload=w, gc_inter_us=100, k=3,
                                   build_kind="count", policy=policy, rep=0,
                                   order_index=index, extime=1))
        for w in workloads:
            for index, arm in enumerate(order_rotation(0)):
                result.append(dict(workload=w, gc_inter_us=100, k=3,
                                   build_kind="stock" if arm == "stock" else "fwd",
                                   policy=arm, rep=0, order_index=index, extime=3))
        return result
    for w in workloads:
        conditions = [(gc, 3) for gc in GC_VALUES]
        if command == "run" and k_sweep and w == "many_ops":
            conditions += [(100, 1), (100, 8)]
        for gc, k in conditions:
            for rep in (0, 1, 2):
                for index, arm in enumerate(order_rotation(rep)):
                    result.append(dict(workload=w, gc_inter_us=gc, k=k,
                                       build_kind="stock" if arm == "stock" else "fwd",
                                       policy=arm, rep=rep, order_index=index, extime=3))
            for index, policy in enumerate(("c", "f")):
                result.append(dict(workload=w, gc_inter_us=gc, k=k,
                                   build_kind="count", policy=policy, rep=0,
                                   order_index=index, extime=1))
    return result


def perf_eligible(kind: str) -> bool:
    return kind != "count"


def parse_counter_lines(stdout: str, kind: str) -> tuple[dict | None, dict]:
    values = []
    for prefix in COUNTER_PREFIXES:
        lines = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
        expected = 1 if prefix == "CICADA_LONGTX_V1 " or kind == "count" else 0
        if len(lines) != expected:
            raise ValueError(f"{prefix.strip()} expected {expected} lines, found {len(lines)}")
        values.append(json.loads(lines[0]) if expected else None)
    for value, fields in zip(values, (FWD_FIELDS, LONGTX_FIELDS)):
        if value is None:
            continue
        if not isinstance(value, dict) or not isinstance(value.get("threads"), list):
            raise ValueError("counter threads missing")
        for thread in value["threads"]:
            if not isinstance(thread, dict) or thread.keys() != fields or any(
                    (type(v) is not bool if key == "long" else
                     type(v) is not int or v < 0)
                    for key, v in thread.items()):
                raise ValueError("counter thread schema invalid")
    return values[0], values[1]


def parse_gc_line(stdout: str, expected: bool) -> dict | None:
    lines = [line[len("CICADA_GC_V1 "):] for line in stdout.splitlines()
             if line.startswith("CICADA_GC_V1 ")]
    if len(lines) != int(expected):
        raise ValueError(f"CICADA_GC_V1 expected {int(expected)} lines, found {len(lines)}")
    if not expected:
        return None
    value = json.loads(lines[0])
    if type(value) is not dict or value.keys() != GC_TOP or value["schema"] != 1 or \
            value["mode"] not in ("off", "hb", "e", "none"):
        raise ValueError("CICADA_GC_V1 top schema invalid")
    for key in ("sample_us", "clocks_per_us", "initial_versions", "version_struct_bytes", "live_end"):
        if type(value[key]) is not int or value[key] < 0:
            raise ValueError(f"CICADA_GC_V1 {key} invalid")
    if type(value["threads"]) is not list:
        raise ValueError("CICADA_GC_V1 threads invalid")
    ids = []
    for row in value["threads"]:
        if type(row) is not dict or row.keys() != GC_THREAD or any(
                type(v) is not int or v < 0 for v in row.values()):
            raise ValueError("CICADA_GC_V1 thread schema invalid")
        ids.append(row["thid"])
    if len(ids) != len(set(ids)):
        raise ValueError("CICADA_GC_V1 duplicate thid")
    for name, fields in GC_NESTED.items():
        row = value[name]
        if type(row) is not dict or row.keys() != set(fields):
            raise ValueError(f"CICADA_GC_V1 {name} schema invalid")
        for key, item in row.items():
            if type(item) is list:
                if key == "series":
                    if any(type(point) is not list or len(point) != 3 or
                           any(type(v) is not int for v in point) for point in item):
                        raise ValueError("CICADA_GC_V1 series invalid")
                elif any(type(v) is not int or v < 0 for v in item):
                    raise ValueError(f"CICADA_GC_V1 {key} invalid")
                elif key.endswith("hist") and len(item) != 42:
                    raise ValueError(f"CICADA_GC_V1 {key} bucket count invalid")
            elif type(item) is not int or item < 0:
                raise ValueError(f"CICADA_GC_V1 {key} invalid")
    return value


def gc_order_rotation(rep: int) -> tuple[str, ...]:
    return GC_ARMS[rep % 4:] + GC_ARMS[:rep % 4]


def gc_plan_runs(workload: str, wait_us: int | None, *, skew=0.9, smoke=False) -> list[dict]:
    if skew not in (0.9, 0):
        raise ValueError("GC skew must be 0.9 or 0")
    if workload != "wait_after_reads" and skew != 0.9:
        raise ValueError("skew 0 only applies to wait_after_reads")
    if workload == "wait_after_reads" and wait_us not in (1000, 10000):
        raise ValueError("wait_after_reads requires wait_us 1000 or 10000")
    if workload != "wait_after_reads" and wait_us is not None:
        raise ValueError("wait_us only applies to wait_after_reads")
    specs = []
    for gc_inter_us in ((10,) if smoke else GC_VALUES):
        for counted in (False, True):
            repeats = 1 if smoke or (counted and workload != "wait_after_reads") else 3
            for rep in range(repeats):
                for order_index, arm in enumerate(gc_order_rotation(rep)):
                    build = "gc-stock" if arm == "stock" else "gc-c" if arm == "C" else "gc-e"
                    if counted:
                        build += "-count"
                    specs.append(dict(gc_job=True, workload=workload, wait_us=wait_us, skew=skew,
                                      gc_inter_us=gc_inter_us, slice_us=100 if arm.startswith("E") else 0,
                                      arm=arm, build_kind=build, rep=rep, order_index=order_index,
                                      extime=1 if smoke else 3))
    return specs


def _gc_summary(counter: dict, longtx: dict, value_bytes=GC_VALUE_BYTES) -> dict:
    uniform, retention = counter["uniform"], counter["retention"]
    def percentile(hist, fraction):
        threshold = max(1, int(sum(hist) * fraction + .999999))
        total = 0
        for index, count in enumerate(hist):
            total += count
            if total >= threshold:
                return 2 ** index if index < 41 else None
        return None
    sums = {key: sum(row[key] for row in counter["threads"])
            for key in GC_THREAD if key != "thid"}
    argmin = uniform["argmin_rts_thid"]
    long_ids = {row["thid"] for row in longtx["threads"] if row["long"]}
    return {"lag_rts_mean_us": uniform["lag_rts_sum_us"] / uniform["count"] if uniform["count"] else None,
            "lag_rts_p50_upper_us": percentile(uniform["lag_rts_hist"], .5),
            "lag_rts_p95_upper_us": percentile(uniform["lag_rts_hist"], .95),
            "lag_rts_max_us": uniform["lag_rts_max_us"],
            "lag_wts_p50_upper_us": percentile(uniform["lag_wts_hist"], .5),
            "lag_wts_p95_upper_us": percentile(uniform["lag_wts_hist"], .95),
            "max_gap_intervals": uniform["max_gap_intervals"],
            "series": uniform["series"], "series_stride": uniform["series_stride"],
            "uniform_samples": uniform["count"], "uniform_negative": uniform["negative"],
            "live_mean": uniform["live_sum"] / uniform["count"] if uniform["count"] else None,
            "live_max": uniform["live_max"], "live_end": counter["live_end"],
            "estimated_live_bytes_mean": (uniform["live_sum"] / uniform["count"] *
                (counter["version_struct_bytes"] + value_bytes)) if uniform["count"] else None,
            "estimated_live_bytes_max": uniform["live_max"] *
                (counter["version_struct_bytes"] + value_bytes),
            "estimated_live_bytes_end": counter["live_end"] *
                (counter["version_struct_bytes"] + value_bytes),
            "retention_count": retention["count"],
            "retention_sum_us": retention["sum_us"],
            "retention_p50_upper_us": percentile(retention["hist"], .5),
            "retention_p95_upper_us": percentile(retention["hist"], .95),
            "publish_count": counter["publish"]["count"],
            "publish_lag_rts_p50_upper_us": percentile(counter["publish"]["lag_rts_hist"], .5),
            "publish_lag_rts_p95_upper_us": percentile(counter["publish"]["lag_rts_hist"], .95),
            "begin_count": counter["begin"]["count"],
            "begin_lag_rts_p50_upper_us": percentile(counter["begin"]["lag_rts_hist"], .5),
            "begin_lag_rts_p95_upper_us": percentile(counter["begin"]["lag_rts_hist"], .95),
            "long_argmin_fraction": sum(argmin[i] for i in long_ids if i < len(argmin)) / sum(argmin)
                if sum(argmin) else None, **sums}


def gc_aggregate_jobs(jobs: list[dict]) -> dict:
    cells = {}
    seen_jobs = set()
    required_jobs = {("wait_after_reads", wait, skew) for wait in (1000, 10000)
                     for skew in (0.9, 0)} | {("normal", None, 0.9), ("many_ops", None, 0.9)}
    for job in jobs:
        if job.get("command") != "gc-run":
            raise ValueError("gc-aggregate requires gc-run jobs")
        if not job.get("all_pass"):
            raise ValueError("incomplete gc-run job")
        job_key = (job["workload"], job.get("wait_us"), job["skew"])
        if job_key in seen_jobs:
            raise ValueError(f"duplicate GC job: {job_key}")
        if job_key not in required_jobs:
            raise ValueError(f"unexpected GC job: {job_key}")
        seen_jobs.add(job_key)
        expected = {(s["gc_inter_us"], s["arm"], s["build_kind"], s["rep"])
                    for s in gc_plan_runs(job["workload"], job.get("wait_us"), skew=job["skew"])}
        actual = set()
        for record in job["records"]:
            if (record["workload"] != job["workload"] or
                    record.get("wait_us") != job.get("wait_us") or record["skew"] != job["skew"]):
                raise ValueError("record condition differs from job")
            key = tuple(record[k] for k in ("gc_inter_us", "arm", "build_kind", "rep"))
            if key in actual:
                raise ValueError(f"duplicate rep: {key}")
            actual.add(key)
            counted = record["build_kind"].endswith("-count")
            if not record.get("valid") or record.get("perf_eligible") is counted:
                raise ValueError("invalid or mislabeled record")
            cell_key = (f"{job['workload']}/wait={job.get('wait_us')}/skew={job['skew']:g}"
                        f"/gc={record['gc_inter_us']}")
            cell = cells.setdefault(cell_key, {"workload": job["workload"],
                "wait_us": job.get("wait_us"), "skew": job["skew"],
                "gc_inter_us": record["gc_inter_us"],
                "arms": {arm: {"performance": [], "gc": []} for arm in GC_ARMS},
                "primary_comparison": ["E", "E-hb"],
                "auxiliary_comparisons": [["stock", "E-hb"], ["C", "E-hb"]]})
            row = cell["arms"][record["arm"]]
            if counted:
                if record.get("gc_counters") is None:
                    raise ValueError("missing GC counters")
                row["gc"].append({"rep": record["rep"],
                    **_gc_summary(record["gc_counters"], record["longtx_counters"])})
            else:
                row["performance"].append({"rep": record["rep"], "throughput_tps": record["throughput"]})
        if actual != expected:
            raise ValueError(f"missing or extra cell: {sorted(expected - actual)[:1]}")
    for cell in cells.values():
        for arm in GC_ARMS:
            perf = cell["arms"][arm]["performance"]
            cell["arms"][arm]["throughput_median_tps"] = statistics.median(
                row["throughput_tps"] for row in perf)
        if cell["workload"] == "wait_after_reads":
            comparisons = {}
            for label, left, right in (("primary_E_minus_E-hb", "E", "E-hb"),
                                       ("auxiliary_E-hb_minus_stock", "E-hb", "stock"),
                                       ("auxiliary_E-hb_minus_C", "E-hb", "C")):
                left_reps = {row["rep"]: row for row in cell["arms"][left]["gc"]}
                right_reps = {row["rep"]: row for row in cell["arms"][right]["gc"]}
                if left_reps.keys() != right_reps.keys():
                    raise ValueError(f"unpaired GC reps: {label}")
                comparisons[label] = {"skew": cell["skew"]}
                for metric in ("lag_rts_mean_us", "live_mean", "retention_p50_upper_us"):
                    differences = [left_reps[rep][metric] - right_reps[rep][metric]
                                   for rep in sorted(left_reps) if left_reps[rep][metric] is not None
                                   and right_reps[rep][metric] is not None]
                    comparisons[label][metric] = statistics.median(differences) if differences else None
            cell["gc_comparisons"] = comparisons
    if seen_jobs != required_jobs:
        raise ValueError(f"missing GC jobs: {sorted(required_jobs - seen_jobs, key=str)}")
    return {"schema_version": "vhash-gc-aggregate/v1", "verification_status": "未検証の診断値",
            "cells": cells}


def _probe() -> dict:
    start = now()
    pids = competing_bench_pids()
    receipt = {"argv": ["pgrep", "-af", r"ycsb_.*\.exe"], "started": start,
               "ended": now(), "competing": pids}
    if pids:
        raise RuntimeError(f"competing benchmark: {pids}")
    return receipt


def _argv(binary: Path, spec: dict) -> list[str]:
    if spec.get("target_job"):
        return target_argv(binary, spec)
    if spec.get("gc_job"):
        flags = ["-thread_num=48", "-ycsb_tuple_num=1000000",
                 f"-ycsb_zipf_skew={spec['skew']:g}",
                 "-ycsb_rratio=50", "-ycsb_max_ope=10", "-ycsb_rmw=0",
                 f"-extime={spec['extime']}", "-clocks_per_us=2100",
                 f"-gc_inter_us={spec['gc_inter_us']}",
                 "--cicada_long_threads=" + ("0" if spec["workload"] == "normal" else "4"),
                 "--cicada_long_kind=" + (spec["workload"] if spec["workload"] != "normal" else "many_ops"),
                 "--cicada_long_ops=1000", "--cicada_long_rratio=90",
                 f"--cicada_long_wait_us={spec.get('wait_us') or 1000}", "--cicada_wait_reads=10"]
        if spec["arm"] != "stock":
            flags += ["--cicada_fwd_policy=c", "--cicada_fwd_k=3"]
        if spec["arm"] in ("E-hb", "E"):
            flags += ["--cicada_gc_mode=" + ("hb" if spec["arm"] == "E-hb" else "e"),
                      "--cicada_gc_slice_us=100"]
        if spec["build_kind"].endswith("-count"):
            flags += ["--cicada_gc_sample_us=10"]
        return [str(binary), *flags]
    workload = spec["workload"]
    flags = ["-thread_num=48", "-ycsb_tuple_num=1000000",
             f"-ycsb_zipf_skew={spec.get('skew', 0.9)}",
             "-ycsb_rratio=50", "-ycsb_max_ope=10", "-ycsb_rmw=0",
             f"-extime={spec['extime']}", "-clocks_per_us=2100",
             f"-gc_inter_us={spec['gc_inter_us']}",
             "--cicada_long_threads=" + ("0" if workload == "normal" else "4"),
             "--cicada_long_kind=" + (workload if workload != "normal" else "many_ops"),
             "--cicada_long_ops=1000", "--cicada_long_rratio=90",
             "--cicada_long_wait_us=1000", "--cicada_wait_reads=10"]
    if spec["policy"] != "stock":
        flags += ["--cicada_fwd_policy=" + spec["policy"], f"--cicada_fwd_k={spec['k']}"]
    return ["numactl", "--interleave=all", str(binary), *flags]


def _capture(data: bytes) -> dict:
    return {"sha256": sha_bytes(data), "text": data[-MAX_CAPTURE:].decode("utf-8", "replace"),
            "truncated": len(data) > MAX_CAPTURE}


def _run_binary(binary: Path, spec: dict, common: dict, gates: list[dict]) -> dict:
    """Single ycsb binary spawn site; called once per planned record."""
    probe = _probe()
    argv = _argv(binary, spec)
    start = now()
    tick = time.monotonic()
    try:
        completed = subprocess.run(argv, capture_output=True, timeout=180)
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 124, exc.stdout or b"", exc.stderr or b""
    record = {**common, **spec, "schema_version": "vhash-forwarding-record/v1",
              "thread_num": 48, "long_threads": 0 if spec["workload"] == "normal" else 4,
              "perf_eligible": (not spec["build_kind"].endswith("-count")
                                if spec.get("gc_job") or spec.get("target_job") else perf_eligible(spec["build_kind"])),
              "verification_status": "未検証の診断値", "argv": argv,
              "hostname": socket.gethostname(), "started": start, "ended": now(),
              "seconds": time.monotonic() - tick, "returncode": code,
              "stdout": _capture(stdout), "stderr": _capture(stderr),
              "competing_probe": probe, "gate_receipts": gates,
              "binary_sha256": sha_file(binary), "throughput": None,
              "fwd_counters": None, "longtx_counters": None, "valid": False}
    if spec.get("gc_job"):
        record.update(build_macros=list(MACROS[spec["build_kind"]]), gc_counters=None)
    if spec.get("target_job"):
        record.update(schema_version="vhash-target-record/v1",
                      stdout={"sha256": sha_bytes(stdout), "text": stdout.decode("utf-8", "replace")},
                      stderr={"sha256": sha_bytes(stderr), "text": stderr.decode("utf-8", "replace")},
                      gc_counters=None)
    try:
        if code:
            raise ValueError(f"binary rc={code}")
        text = stdout.decode("utf-8", "replace")
        if spec.get("target_job"):
            fwd, gc, longtx = parse_target_lines(text, spec["arm"],
                                                  spec["build_kind"].endswith("-count"))
            metric = parse_bench_stdout(text).get("throughput[tps]")
            if metric is None or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", metric):
                raise ValueError("missing throughput[tps] result line")
            record.update(throughput=float(metric), gc_counters=gc, fwd_counters=fwd,
                          longtx_counters=longtx, valid=True)
            return record
        if spec.get("gc_job"):
            gc = parse_gc_line(text, spec["build_kind"].endswith("-count"))
            fwd, longtx = parse_counter_lines(text,
                "count" if spec["build_kind"] in ("gc-c-count", "gc-e-count") else
                "fwd" if spec["arm"] != "stock" else "stock")
            metric = parse_bench_stdout(text).get("throughput[tps]")
            if metric is None or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", metric):
                raise ValueError("missing throughput[tps] result line")
            record.update(throughput=float(metric), gc_counters=gc,
                          fwd_counters=fwd, longtx_counters=longtx,
                          build_macros=list(MACROS[spec["build_kind"]]), valid=True)
            return record
        fwd, longtx = parse_counter_lines(text, spec["build_kind"])
        metric = parse_bench_stdout(text).get("throughput[tps]")
        if metric is None or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", metric):
            raise ValueError("missing throughput[tps] result line")
        record.update(throughput=float(metric), fwd_counters=fwd,
                      longtx_counters=longtx, valid=True)
    except (ValueError, json.JSONDecodeError) as exc:
        record["invalid_reason"] = str(exc)
    return record


def _sum_threads(counter: dict | None, keys: tuple[str, ...], *, long_only=False,
                 thread_num=48, long_threads=0) -> dict:
    if counter is None:
        return {}
    threads = [t for t in counter["threads"] if not long_only or
               (t["thid"] != 0 and t["thid"] >= thread_num - long_threads)]
    return {key: sum(t[key] for t in threads) for key in keys}


def _split_threads(counter: dict, keys: tuple[str, ...], record: dict) -> dict:
    long_ids = lambda t: t["thid"] != 0 and t["thid"] >= record["thread_num"] - record["long_threads"]
    return {group: {key: sum(t[key] for t in counter["threads"] if long_ids(t) == is_long)
                    for key in keys} for group, is_long in (("long", True), ("normal", False))}


def _completion(counts: dict) -> float | None:
    total = counts["commits"] + counts["aborts"]
    return counts["commits"] / total if total else None


def aggregate(raw: dict) -> dict:
    cells: dict[str, dict] = {}
    for record in raw["records"]:
        if not record.get("valid"):
            continue
        key = f"{record['workload']}/gc={record['gc_inter_us']}/k={record['k']}"
        cell = cells.setdefault(key, {"workload": record["workload"],
                 "gc_inter_us": record["gc_inter_us"], "k": record["k"],
                 "throughput": {arm: [] for arm in ("stock", "c", "f")},
                 "c_counters": [], "f_counters": [], "longtx": {arm: [] for arm in ("stock", "c", "f")},
                 "counter_by_thread": {arm: [] for arm in ("c", "f")},
                 "input_jobs": [], "skew": record.get("skew", 0.9)})
        if cell["skew"] != record.get("skew", 0.9):
            raise ValueError("mixed skew in aggregate cell")
        source = {name: record.get(name) for name in ("job_id", "hostname", "skew")}
        if source not in cell["input_jobs"]:
            cell["input_jobs"].append(source)
        arm = record["policy"]
        if record["perf_eligible"]:
            cell["throughput"][arm].append({"rep": record["rep"], "value": record["throughput"]})
            long_counts = _sum_threads(record["longtx_counters"], ("commits", "aborts"),
                 long_only=True, thread_num=record.get("thread_num", 48),
                 long_threads=record.get("long_threads", 0 if record["workload"] == "normal" else 4))
            cell["longtx"][arm].append({**long_counts, "rep": record["rep"],
                                          "completion_rate": _completion(long_counts)})
        else:
            values = _sum_threads(record["fwd_counters"],
                ("triggers", "attempts", "success", "read_mismatch", "write_constraint",
                 "conflict", "ineligible", "no_target", "special_after_forward", "f_aborts",
                 "advance_clock_sum", "pos_before_sum", "pos_after_sum"))
            cell["c_counters" if arm == "c" else "f_counters"].append(values)
            cell["counter_by_thread"][arm].append(_split_threads(record["fwd_counters"],
                ("attempts", "success", "read_mismatch", "write_constraint", "conflict",
                 "ineligible", "no_target", "f_aborts"),
                {"thread_num": record.get("thread_num", 48),
                 "long_threads": record.get("long_threads", 0 if record["workload"] == "normal" else 4)}))
    for cell in cells.values():
        for arm, source in (("c", "c_counters"), ("f", "f_counters")):
            rows = cell[source]
            cell[arm + "_summary"] = (
                {name: sum(row[name] for row in rows) for name in rows[0]}
                if rows else None
            )
        cell["longtx_summary"] = {
            arm: ({name: sum(row[name] for row in rows) for name in ("commits", "aborts")}
                  if rows else None)
            for arm, rows in cell["longtx"].items()
        }
        for arm, counts in cell["longtx_summary"].items():
            if counts is not None:
                counts["completion_rate"] = _completion(counts)
        cell["thread_summary"] = {
            arm: {group: ({key: sum(row[group][key] for row in rows) for key in rows[0][group]}
                         if rows else None) for group in ("long", "normal")}
            for arm, rows in cell["counter_by_thread"].items()}
    return {"schema_version": "vhash-forwarding-aggregate/v1",
            "verification_status": "未検証の診断値", "conditions": raw.get("conditions", {}),
            "cells": cells}


def aggregate_jobs(jobs: list[dict]) -> dict:
    seen = set()
    records = []
    conditions = None
    for job in jobs:
        if job.get("command") != "run" or job.get("all_pass") is not True:
            continue
        if conditions is None:
            conditions = job.get("conditions", {})
        elif conditions != job.get("conditions", {}):
            raise ValueError("inconsistent job conditions")
        if not job["records"]:
            raise ValueError(f"run job {job.get('job_id')} has no records")
        workloads = ({job["workload"]} if job.get("workload") else
                     {record["workload"] for record in job["records"]})
        expected = {tuple(spec[name] for name in ("workload", "gc_inter_us", "k",
                    "policy", "build_kind", "rep"))
                    for workload in workloads
                    for spec in plan_runs("run", workload, job.get("k_sweep", False))}
        actual = set()
        for record in job["records"]:
            if not record.get("valid"):
                raise ValueError("all_pass job contains invalid record")
            key = tuple(record[name] for name in ("workload", "gc_inter_us", "k",
                                            "policy", "build_kind", "rep"))
            if key in seen:
                raise ValueError(f"duplicate record: {key}")
            seen.add(key)
            actual.add(key)
            records.append({**record, "job_id": job["job_id"],
                            "hostname": job["hostname"],
                            "skew": record.get("skew", job["conditions"]["zipf"])})
        missing = expected - actual
        if missing:
            raise ValueError(f"run job {job.get('job_id')} missing planned cell: {sorted(missing)[0]}")
        extra = actual - expected
        if extra:
            raise ValueError(f"run job {job.get('job_id')} has unplanned cell: {sorted(extra)[0]}")
    return aggregate({"conditions": conditions or {}, "records": records})


def smoke_count_status(records: list[dict]) -> dict:
    counts = {"c_attempts": 0, "c_success": 0, "f_aborts": 0}
    for record in records:
        if record["workload"] != "many_ops" or record["build_kind"] != "count":
            continue
        keymap = {"c": (("attempts", "c_attempts"), ("success", "c_success")),
                  "f": (("f_aborts", "f_aborts"),)}
        for field, destination in keymap[record["policy"]]:
            counts[destination] += _sum_threads(record["fwd_counters"], (field,))[field]
    return {**counts, "accepted": counts["c_attempts"] > 0 and counts["f_aborts"] > 0}


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "run", "aggregate", "gc-smoke", "gc-run", "gc-aggregate", "target-run", "target-aggregate"))
    parser.add_argument("--third-party-cache", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workload", choices=WORKLOADS)
    parser.add_argument("--wait-us", type=int, choices=(1000, 10000))
    parser.add_argument("--skew", type=float, choices=(0, 0.6, 0.9))
    parser.add_argument("--smoke", action="store_true", help="target-run: GC 10, one rep per build, 1 s")
    parser.add_argument("--k-sweep", action="store_true")
    parser.add_argument("--raw", type=Path, action="append", help="explicit aggregate input JSON; repeat for each job")
    args = parser.parse_args(argv)
    if args.command.startswith("target-"):
        return target_main(args, parser)
    if args.smoke or args.skew == 0.6:
        parser.error("--smoke and skew 0.6 only apply to target-run")
    if args.command.startswith("gc-"):
        return gc_main(args, parser)
    if args.skew is not None:
        parser.error("--skew only applies to gc-run")
    if args.command != "aggregate" and args.third_party_cache is None:
        parser.error("smoke and run require --third-party-cache")
    if args.third_party_cache is not None and not args.third_party_cache.is_absolute():
        parser.error("--third-party-cache must be an absolute path")
    if args.command == "run" and args.workload is None:
        parser.error("run requires --workload")
    if args.k_sweep and args.workload != "many_ops":
        parser.error("--k-sweep requires --workload many_ops")
    if args.command == "aggregate":
        if not args.raw:
            parser.error("aggregate requires one or more --raw JSON files")
        _write(args.output / "aggregate.json", aggregate_jobs(
            [json.loads(path.read_text()) for path in args.raw]))
        return 0
    started = now()
    job = {"schema_version": "vhash-forwarding-job/v1", "git_head": None,
           "ccbench_pin": pin.CURRENT_PIN, "patch_sha256": sha_file(PATCH),
           "verification_status": "未検証の診断値", "command": args.command,
           "workload": args.workload, "k_sweep": args.k_sweep,
           "hostname": socket.gethostname(), "started": started, "ended": None,
           "job_id": socket.gethostname() + "-" + started,
           "conditions": {"threads": 48, "tuples": 1000000, "zipf": 0.9,
                          "rratio": 50, "max_ope": 10, "clocks_per_us": 2100},
           "records": [], "builds": {}, "inert_receipt": None,
           "competing_probe": None, "all_pass": False}
    output = args.output / ("raw-" + args.command + "-" +
             (args.workload or "all") + "-" + started.replace(":", "-") + ".json")
    try:
        job["git_head"] = checked(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.decode().strip()
        if re.fullmatch(r"pegasus0[0-9]", socket.gethostname()):
            raise RuntimeError("measurement job must run on a compute node")
        job["competing_probe"] = _probe()
        policy = compute._load_policy(ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
        toolchain = compute._resolve_toolchain(policy)
        with tempfile.TemporaryDirectory(prefix="vhash-fwd-") as temporary:
            scratch = Path(temporary)
            deps = compute._prepare_dependencies(ROOT, policy, args.third_party_cache, scratch, toolchain)
            with patchharness.checkout(pin.CURRENT_PIN) as worktree:
                source = Path(worktree)
                with patchharness.applied(str(PATCH), pin.CURRENT_PIN, str(source)):
                    binaries = {}
                    job["gate_receipts"] = {}
                    binary, gates, seconds = _build_variant(source, scratch / "build-dependency",
                                                           "dependency", deps, toolchain)
                    job["builds"]["dependency"] = {"seconds": seconds,
                                                    "binary_sha256": sha_file(binary),
                                                    "gate_receipts": gates,
                                                    "admission": non_admissible_materializer(MATERIALIZER)}
                    for kind in ("stock", "fwd", "count"):
                        binary, gates, seconds = _build_variant(source, scratch / ("build-" + kind),
                                                               kind, deps, toolchain)
                        binaries[kind] = (binary, gates)
                        job["gate_receipts"][kind] = gates
                        job["builds"][kind] = {"seconds": seconds, "binary_sha256": sha_file(binary),
                                               "gate_receipts": gates,
                                               "admission": non_admissible_materializer(MATERIALIZER)}
                if args.command == "smoke":
                    tick = time.monotonic()
                    job["inert_receipt"] = _inert_receipt(source, scratch / "build-stock")
                    job["inert_receipt"]["seconds"] = time.monotonic() - tick
                common = {"git_head": job["git_head"], "ccbench_pin": pin.CURRENT_PIN,
                          "patch_sha256": job["patch_sha256"],
                          "inert_receipt": job["inert_receipt"], "job_id": job["job_id"]}
                for spec in plan_runs(args.command, args.workload, args.k_sweep):
                    if args.command == "smoke" and spec["build_kind"] != "count" and \
                            not job.get("smoke_count_checked"):
                        many = [r for r in job["records"] if r["workload"] == "many_ops"
                                and r["build_kind"] == "count"]
                        status = smoke_count_status(many)
                        job["smoke_fallback"] = [{"k": 3, "skew": 0.9,
                             "condition": "C attempts > 0 and F f_aborts > 0", "result": status}]
                        for k, skew in ((1, 0.9), (1, 0.99)):
                            if status["accepted"]:
                                break
                            for index, policy in enumerate(("c", "f")):
                                extra = dict(workload="many_ops", gc_inter_us=100,
                                             k=k, skew=skew, build_kind="count",
                                             policy=policy, rep=0, order_index=index,
                                             extime=1)
                                binary, gates = binaries["count"]
                                result = _run_binary(binary, extra, common, gates)
                                job["records"].append(result)
                                _write(output, job)
                                if not result["valid"]:
                                    raise RuntimeError("invalid smoke fallback")
                            status = smoke_count_status(job["records"])
                            job["smoke_fallback"].append({"k": k, "skew": skew,
                                 "condition": "C attempts > 0 and F f_aborts > 0", "result": status})
                            _write(output, job)
                        job["smoke_count_checked"] = True
                        if not status["accepted"]:
                            raise RuntimeError("many_ops C attempts or F f_aborts remain zero after smoke fallback")
                    binary, gates = binaries[spec["build_kind"]]
                    record = _run_binary(binary, spec, common, gates)
                    job["records"].append(record)
                    _write(output, job)
                    if not record["valid"]:
                        raise RuntimeError("invalid run: " + record.get("invalid_reason", "unknown"))
                job["all_pass"] = True
    except Exception as exc:
        job["error"] = type(exc).__name__ + ": " + str(exc)
        for attr in ("condition_gate_evidence", "inert_receipt"):
            if hasattr(exc, attr):
                job[attr] = getattr(exc, attr)
    job["ended"] = now()
    _write(output, job)
    print(output)
    return 0 if job["all_pass"] else 1


def _gc_inert_receipt(source: Path, stock_build: Path) -> dict:
    entries = {name: _inert_entry(_compile_entry(stock_build, name))[0] for name in
               ("transaction.cc", "ycsb_cicada.cc")}
    before = {name: _preprocess(entry) for name, entry in entries.items()}
    patchharness.apply_patch(str(GC_PATCH), str(source))
    after = {name: _preprocess(entry) for name, entry in entries.items()}
    receipt = {"md6_sha256": before, "gc_sha256": after, "matched": before == after,
               "normalization": "_preprocess: remove marker and blank lines"}
    if not receipt["matched"]:
        error = RuntimeError("GC inert preprocessing mismatch")
        error.inert_receipt = receipt
        raise error
    return receipt


def gc_main(args, parser) -> int:
    if args.skew is not None and args.command != "gc-run":
        parser.error("--skew only applies to gc-run")
    if args.command == "gc-aggregate":
        if not args.raw:
            parser.error("gc-aggregate requires --raw")
        _write(args.output / "gc-aggregate.json", gc_aggregate_jobs(
            [json.loads(path.read_text()) for path in args.raw]))
        return 0
    if args.third_party_cache is None or not args.third_party_cache.is_absolute():
        parser.error("gc-smoke and gc-run require absolute --third-party-cache")
    if args.command == "gc-run" and args.workload is None:
        parser.error("gc-run requires --workload")
    workload = args.workload or "wait_after_reads"
    wait_us = args.wait_us if args.wait_us is not None else (10000 if workload == "wait_after_reads" else None)
    skew = args.skew if args.skew is not None else 0.9
    try:
        specs = gc_plan_runs(workload, wait_us, skew=skew, smoke=args.command == "gc-smoke")
    except ValueError as exc:
        parser.error(str(exc))
    started = now()
    job = {"schema_version": "vhash-gc-job/v1", "command": args.command,
           "workload": workload, "wait_us": wait_us, "skew": skew,
           "ccbench_pin": pin.CURRENT_PIN,
           "patch_sha256": {str(p.relative_to(ROOT)): sha_file(p) for p in (PATCH, GC_PATCH)},
           "genome": GC_GENOME, "value_bytes": GC_VALUE_BYTES,
           "verification_status": "未検証の診断値",
           "job_id": socket.gethostname() + "-" + started, "hostname": socket.gethostname(),
           "started": started, "records": [], "builds": {}, "all_pass": False}
    output = args.output / ("raw-" + args.command + "-" + workload +
             ("-skew" + f"{skew:g}" if args.command == "gc-run" else "") + "-" +
             started.replace(":", "-") + ".json")
    try:
        if re.fullmatch(r"pegasus0[0-9]", socket.gethostname()):
            raise RuntimeError("measurement job must run on a compute node")
        job["git_head"] = checked(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.decode().strip()
        job["competing_probe"] = _probe()
        policy = compute._load_policy(ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
        toolchain = compute._resolve_toolchain(policy)
        with tempfile.TemporaryDirectory(prefix="vhash-gc-") as temporary:
            scratch = Path(temporary)
            deps = compute._prepare_dependencies(ROOT, policy, args.third_party_cache, scratch, toolchain)
            with patchharness.checkout(pin.CURRENT_PIN) as worktree:
                source = Path(worktree)
                md6_touched = set(patchharness.patch_files(str(PATCH), str(source)))
                gc_touched = set(patchharness.patch_files(str(GC_PATCH), str(source)))
                if not gc_touched <= md6_touched:
                    raise RuntimeError("GC patch touches files outside md_6 patch; cannot safely revert stack")
                with patchharness.applied(str(PATCH), pin.CURRENT_PIN, str(source)):
                    binaries = {}
                    binary, gates, seconds = _build_variant(source, scratch / "build-gc-dependency",
                                                             "gc-dependency", deps, toolchain)
                    binaries["gc-dependency"] = (binary, gates)
                    job["builds"]["gc-dependency"] = {"binary_sha256": sha_file(binary),
                        "seconds": seconds, "gate_receipts": gates}
                    if args.command == "gc-smoke":
                        # Compile arguments come from this build; both sources use the same command.
                        _build_variant(source, scratch / "build-inert-md6", "gc-stock", deps, toolchain)
                        job["inert_receipt"] = _gc_inert_receipt(source, scratch / "build-inert-md6")
                    else:
                        patchharness.apply_patch(str(GC_PATCH), str(source))
                    for kind in ("gc-stock", "gc-c", "gc-e",
                                 "gc-stock-count", "gc-c-count", "gc-e-count"):
                        binary, gates, seconds = _build_variant(source, scratch / ("build-" + kind),
                                                                 kind, deps, toolchain)
                        binaries[kind] = (binary, gates)
                        job["builds"][kind] = {"binary_sha256": sha_file(binary), "seconds": seconds,
                                                "gate_receipts": gates}
                    common = {"job_id": job["job_id"], "ccbench_pin": pin.CURRENT_PIN,
                              "patch_sha256": job["patch_sha256"], "genome": GC_GENOME}
                    for spec in specs:
                        binary, gates = binaries[spec["build_kind"]]
                        record = _run_binary(binary, spec, common, gates)
                        job["records"].append(record)
                        _write(output, job)
                        if not record["valid"]:
                            raise RuntimeError("invalid GC run: " + record.get("invalid_reason", "unknown"))
                    if args.command == "gc-smoke":
                        successes = [sum(t["success"] for t in r["gc_counters"]["threads"])
                                     for r in job["records"] if r["arm"] == "E" and r["gc_counters"]]
                        job["e_success_total"] = sum(successes)
                        if not job["e_success_total"]:
                            raise RuntimeError("wait_after_reads E success total is zero")
                    job["all_pass"] = True
    except Exception as exc:
        job["error"] = type(exc).__name__ + ": " + str(exc)
        for attr in ("inert_receipt", "condition_gate_evidence"):
            if hasattr(exc, attr):
                job[attr] = getattr(exc, attr)
    job["ended"] = now()
    _write(output, job)
    print(output)
    return 0 if job["all_pass"] else 1


TARGET_PATCH = ROOT / "patches/cicada-forwarding-target.patch"
TARGET_STACK = (PATCH, GC_PATCH, TARGET_PATCH)
TARGET_ARMS = {
    "wait_after_reads": ("stock", "C-min", "E-hb", "E-now", "E-max", "E-max-once"),
    "many_ops": ("stock", "C-min", "C-max", "C-partial", "C-partial-once", "F"),
    "normal": ("stock", "C-min", "C-partial", "F"),
}
TARGET_DEFAULT_ARMS = frozenset(("stock", "C-min", "F", "E-hb", "E-now"))
TARGET_JOBS = frozenset({("wait_after_reads", 10000, skew) for skew in (0, .6, .9)} |
                        {("wait_after_reads", 1000, .9),
                         ("many_ops", None, .6), ("many_ops", None, .9),
                         ("normal", None, .9)})
TARGET_EXTRA = frozenset(("no_room", "once_skipped", "uncapped"))


def target_arm_flags(arm: str) -> list[str]:
    """Only policy flags; workload and instrumentation flags belong to the plan."""
    if arm not in {a for arms in TARGET_ARMS.values() for a in arms}:
        raise ValueError(f"unknown target arm: {arm}")
    flags = [] if arm == "stock" else ["--cicada_fwd_policy=" + ("f" if arm == "F" else "c"),
                                         "--cicada_fwd_k=3"]
    flags += {"C-max": ["--cicada_fwd_target=max"],
              "C-partial": ["--cicada_fwd_target=partial"],
              "C-partial-once": ["--cicada_fwd_target=partial", "--cicada_fwd_once=true"],
              "E-hb": ["--cicada_gc_mode=hb"],
              "E-now": ["--cicada_gc_mode=e"],
              "E-max": ["--cicada_gc_mode=e", "--cicada_gc_target=max"],
              "E-max-once": ["--cicada_gc_mode=e", "--cicada_gc_target=max",
                             "--cicada_gc_once=true"]}.get(arm, [])
    if arm.startswith("E-"):
        flags.append("--cicada_gc_slice_us=100")
    return flags


def target_build_kind(arm: str, counted: bool) -> str:
    base = "gc-stock" if arm == "stock" else "gc-e" if arm.startswith("E-") else "gc-c"
    return base + ("-count" if counted else "")


def target_plan_runs(workload: str, wait_us: int | None, *, skew=.9, smoke=False) -> list[dict]:
    if (workload, wait_us, skew) not in TARGET_JOBS:
        raise ValueError("unexpected target job condition")
    arms = TARGET_ARMS[workload]
    specs = []
    for gc in ((10,) if smoke else (10, 1000)):
        for counted in (False, True):
            reps = 1 if smoke or counted and workload == "normal" else 3
            for rep in range(reps):
                for order_index, arm in enumerate(arms[rep % len(arms):] + arms[:rep % len(arms)]):
                    specs.append({"target_job": True, "workload": workload, "wait_us": wait_us,
                                  "skew": skew, "gc_inter_us": gc, "arm": arm,
                                  "build_kind": target_build_kind(arm, counted), "rep": rep,
                                  "order_index": order_index, "extime": 1 if smoke else 3})
    return specs


def target_argv(binary: Path, spec: dict) -> list[str]:
    base = _argv(binary, {**spec, "target_job": False, "gc_job": True, "arm": "stock"})
    flags = target_arm_flags(spec["arm"])
    return base + flags


def _target_json_line(stdout: str, prefix: str, expected: bool) -> dict | None:
    matching = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
    if len(matching) != int(expected):
        raise ValueError(f"{prefix.strip()} expected {int(expected)} lines, found {len(matching)}")
    if not expected:
        return None
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(matching[0], object_pairs_hook=unique_pairs)


def parse_target_lines(stdout: str, arm: str, counted: bool, *, broken=False) -> tuple[dict | None, dict | None, dict]:
    """Reject every extra, missing or duplicate counter line and key."""
    fwd_default = not arm.startswith("C-") or arm == "C-min"
    gc_default = not arm.startswith("E-") or arm in ("E-hb", "E-now")
    fwd_expected = counted and arm != "stock"
    gc_expected = counted
    fwd_v1 = _target_json_line(stdout, "CICADA_FWD_V1 ", fwd_expected and fwd_default)
    fwd_v2 = _target_json_line(stdout, "CICADA_FWD_V2 ", fwd_expected and not fwd_default)
    gc_v1 = _target_json_line(stdout, "CICADA_GC_V1 ", gc_expected and gc_default)
    gc_v2 = _target_json_line(stdout, "CICADA_GC_V2 ", gc_expected and not gc_default)
    longtx = _target_json_line(stdout, "CICADA_LONGTX_V1 ", True)
    if type(longtx) is not dict or longtx.keys() != {"schema", "threads"} or \
            type(longtx["schema"]) is not int or longtx["schema"] != 1 or \
            type(longtx["threads"]) is not list:
        raise ValueError("longtx schema invalid")
    for row in longtx["threads"]:
        if type(row) is not dict or row.keys() != LONGTX_FIELDS or any(
                type(v) is not bool if k == "long" else type(v) is not int or v < 0
                for k, v in row.items()):
            raise ValueError("longtx thread schema invalid")
    if len({row["thid"] for row in longtx["threads"]}) != len(longtx["threads"]):
        raise ValueError("duplicate longtx thid")
    fwd = fwd_v1 if fwd_default else fwd_v2
    if fwd is not None:
        required = FWD_FIELDS if fwd_default else FWD_FIELDS | TARGET_EXTRA | {"short_success"}
        top = {"schema", "policy", "k", "threads"} | (set() if fwd_default else {"target", "once"})
        if type(fwd) is not dict or fwd.keys() != top or type(fwd["threads"]) is not list:
            raise ValueError("FWD top schema invalid")
        if fwd["schema"] != (1 if fwd_default else 2) or \
                fwd["policy"] != ("f" if arm == "F" else "c") or \
                type(fwd["k"]) is not int or fwd["k"] != 3:
            raise ValueError("FWD policy schema invalid")
        if not fwd_default and (fwd["target"] != ("max" if arm == "C-max" else "partial") or
                            type(fwd["once"]) is not bool or
                            fwd["once"] != (arm == "C-partial-once")):
            raise ValueError("FWD target policy mismatch")
        for row in fwd["threads"]:
            if type(row) is not dict or row.keys() != required or any(
                    type(v) is not int or v < 0 for v in row.values()):
                raise ValueError("FWD thread schema invalid")
        if len({row["thid"] for row in fwd["threads"]}) != len(fwd["threads"]):
            raise ValueError("duplicate FWD thid")
    gc = gc_v1 if gc_default else gc_v2
    if gc is not None:
        if gc_default:
            parse_gc_line("CICADA_GC_V1 " + json.dumps(gc), True)
        else:
            top = GC_TOP | {"target", "once"}
            if type(gc) is not dict or gc.keys() != top or gc["schema"] != 2 or \
                    gc["target"] != "max" or \
                    type(gc["once"]) is not bool or gc["once"] != (arm == "E-max-once"):
                raise ValueError("GC V2 top schema invalid")
            reduced = {k: v for k, v in gc.items() if k in GC_TOP}
            reduced["schema"] = 1
            fields = GC_THREAD | TARGET_EXTRA | ({"forced_success"} if broken else set())
            for row in reduced["threads"]:
                if type(row) is not dict or row.keys() != fields or any(
                        type(v) is not int or v < 0 for v in row.values()):
                    raise ValueError("GC V2 thread schema invalid")
            reduced["threads"] = [{k: v for k, v in row.items() if k in GC_THREAD}
                                  for row in reduced["threads"]]
            parse_gc_line("CICADA_GC_V1 " + json.dumps(reduced), True)
        expected_mode = "hb" if arm == "E-hb" else "e" if arm.startswith("E-") else "off"
        if gc["mode"] != expected_mode:
            raise ValueError("GC mode does not match target arm")
    return fwd, gc, longtx


def target_success_metrics(counter: dict, family: str) -> dict:
    rows = counter["threads"]
    keys = ("success", "attempts", "read_mismatch", "write_constraint", "conflict",
            "ineligible", "no_room", "once_skipped", "uncapped", "advance_clock_sum")
    totals = {key: sum(row.get(key, 0) for row in rows) for key in keys}
    if family == "E":
        for key in ("requests", "overflow", "flag_raises"):
            totals[key] = sum(row[key] for row in rows)
        denominator = totals["requests"]
        if counter["mode"] == "e" and denominator != (totals["attempts"] + totals["overflow"] +
                                                     totals["no_room"] + totals["once_skipped"]):
            raise ValueError("E request accounting mismatch")
    else:
        for key in ("triggers", "f_aborts", "no_target", "short_success", "advance_clock_sum"):
            totals[key] = sum(row.get(key, 0) for row in rows)
        denominator = totals["triggers"]
        if denominator != sum(totals[k] for k in ("f_aborts", "no_target", "no_room", "once_skipped", "attempts")):
            raise ValueError("C trigger accounting mismatch")
    attempt_failures = {k: totals[k] for k in ("read_mismatch", "write_constraint", "conflict", "ineligible")}
    if sum(attempt_failures.values()) + totals["success"] != totals["attempts"]:
        raise ValueError("attempt outcome accounting mismatch")
    failures = {**attempt_failures, "no_room": totals["no_room"],
                "once_skipped": totals["once_skipped"]}
    if family == "E":
        failures["overflow"] = totals["overflow"]
    else:
        failures.update(no_target=totals["no_target"], f_aborts=totals["f_aborts"])
    reason_key = "failure_reasons_per_request" if family == "E" else "failure_reasons_per_trigger"
    return {**totals, "denominator": denominator,
            "success_rate": (totals["success"] / denominator if denominator else None)
            if family != "E" or counter["mode"] == "e" else None,
            "attempt_success_rate": totals["success"] / totals["attempts"] if totals["attempts"] else None,
            reason_key: {k: v / denominator if denominator and
                         (family != "E" or counter["mode"] == "e") else None
                         for k, v in failures.items()},
            "advance_clock_mean_success": totals["advance_clock_sum"] / totals["success"]
            if totals["success"] else None}


def target_aggregate_jobs(jobs: list[dict]) -> dict:
    cells = {}
    seen = set()
    for job in jobs:
        if job.get("command") != "target-run" or not job.get("all_pass") or job.get("smoke"):
            raise ValueError("target-aggregate requires complete non-smoke target-run jobs")
        if job.get("ccbench_pin") != pin.CURRENT_PIN or job.get("genome") != GC_GENOME or \
                set(job.get("patch_sha256", {})) != {str(p.relative_to(ROOT)) for p in TARGET_STACK} or \
                any(not re.fullmatch(r"[0-9a-f]{64}", value)
                    for value in job["patch_sha256"].values()):
            raise ValueError("target job provenance invalid")
        condition = (job["workload"], job.get("wait_us"), job["skew"])
        if condition not in TARGET_JOBS or condition in seen:
            raise ValueError("unexpected or duplicate target job")
        seen.add(condition)
        expected = target_plan_runs(*condition[:2], skew=condition[2])
        expected_keys = {(s["gc_inter_us"], s["arm"], s["build_kind"], s["rep"], s["order_index"])
                         for s in expected}
        actual = set()
        for record in job["records"]:
            if (record["workload"], record.get("wait_us"), record["skew"]) != condition:
                raise ValueError("record condition differs from job")
            key = tuple(record[k] for k in ("gc_inter_us", "arm", "build_kind", "rep", "order_index"))
            if key in actual or key not in expected_keys:
                raise ValueError("duplicate or unexpected target record")
            actual.add(key)
            counted = record["build_kind"].endswith("-count")
            if not record.get("valid") or record.get("perf_eligible") is counted:
                raise ValueError("invalid or mislabeled record")
            if record.get("argv") != target_argv(Path(record["argv"][0]), record):
                raise ValueError("target arm flags mismatch")
            if record["stdout"].get("sha256") != sha_bytes(record["stdout"]["text"].encode("utf-8")):
                raise ValueError("raw stdout hash mismatch")
            if counted:
                fwd, gc, longtx = parse_target_lines(record["stdout"]["text"], record["arm"], True)
                if record.get("fwd_counters") != fwd or record.get("gc_counters") != gc or \
                        record.get("longtx_counters") != longtx:
                    raise ValueError("parsed counter differs from raw")
                if sum(t["held_changed"] for t in gc["threads"]):
                    raise ValueError("held version changed")
            else:
                fwd = gc = None
                _, _, parsed_longtx = parse_target_lines(record["stdout"]["text"], record["arm"], False)
                if record.get("longtx_counters") != parsed_longtx:
                    raise ValueError("longtx counter differs from raw")
                if record.get("gc_counters") is not None or record.get("fwd_counters") is not None:
                    raise ValueError("performance run contains counters")
                longtx = record["longtx_counters"]
            cell_key = f"{condition[0]}/wait={condition[1]}/skew={condition[2]:g}/gc={record['gc_inter_us']}"
            cell = cells.setdefault(cell_key, {"workload": condition[0], "wait_us": condition[1],
                "skew": condition[2], "gc_inter_us": record["gc_inter_us"],
                "arms": {arm: {"performance": [], "count": []} for arm in TARGET_ARMS[condition[0]]}})
            arm_data = cell["arms"][record["arm"]]
            if counted:
                gc_summary = _gc_summary(gc, longtx)
                gc_summary.pop("series")
                gc_summary.update({k: sum(t.get(k, 0) for t in gc["threads"]) for k in TARGET_EXTRA})
                split = None
                if fwd is not None:
                    split_input = {**fwd, "threads": [{**{k: 0 for k in TARGET_EXTRA}, **row}
                                                       for row in fwd["threads"]]}
                    split = _split_threads(split_input, ("triggers", "attempts", "success", "f_aborts", "no_target",
                                                  "no_room", "once_skipped", "advance_clock_sum"),
                                           {"thread_num": record.get("thread_num", 48),
                                            "long_threads": record.get("long_threads", 0 if condition[0] == "normal" else 4)})
                    split = {group: {**values, "success_rate": values["success"] / values["triggers"]
                        if values["triggers"] else None} for group, values in split.items()}
                completion = {}
                for group, is_long in (("long", True), ("normal", False)):
                    subset = [row for row in longtx["threads"] if row["long"] is is_long]
                    commits = sum(row["commits"] for row in subset)
                    aborts = sum(row["aborts"] for row in subset)
                    completion[group] = {"commits": commits, "aborts": aborts,
                        "rate": commits / (commits + aborts) if commits + aborts else None}
                arm_data["count"].append({"rep": record["rep"], "gc": gc_summary,
                    "e": target_success_metrics(gc, "E"),
                    "c": target_success_metrics(fwd, "C") if fwd else None,
                    "c_by_thread": split, "completion_by_thread": completion, "longtx": longtx})
            else:
                arm_data["performance"].append({"rep": record["rep"],
                    "throughput_tps": record["throughput"], "longtx": longtx})
        if actual != expected_keys:
            raise ValueError("missing or extra target record")
    if seen != TARGET_JOBS:
        raise ValueError("missing target jobs")
    for cell in cells.values():
        stock = statistics.median(r["throughput_tps"] for r in cell["arms"]["stock"]["performance"])
        for arm, data in cell["arms"].items():
            median = statistics.median(r["throughput_tps"] for r in data["performance"])
            data["throughput_median_tps"] = median
            data["throughput_stock_ratio"] = median / stock if stock else None
            if arm != "stock":
                family = "e" if arm.startswith("E-") else "c"
                data["policy_exercised"] = sum(r[family]["success"] for r in data["count"]) > 0
        pairs = (("E-max", "E-hb"), ("E-max", "E-now")) if cell["workload"] == "wait_after_reads" else \
                tuple((arm, "C-min") for arm in cell["arms"] if arm.startswith("C-") and arm != "C-min")
        cell["comparisons"] = {}
        for left, right in pairs:
            left_reps = {r["rep"]: r for r in cell["arms"][left]["count"]}
            right_reps = {r["rep"]: r for r in cell["arms"][right]["count"]}
            if left_reps.keys() != right_reps.keys():
                raise ValueError("unpaired count reps")
            family = "e" if left.startswith("E-") else "c"
            metrics = ("success_rate", "advance_clock_mean_success")
            differences = {metric: [left_reps[i][family][metric] - right_reps[i][family][metric]
                for i in left_reps if left_reps[i][family] and right_reps[i][family]
                and left_reps[i][family][metric] is not None and right_reps[i][family][metric] is not None]
                for metric in metrics}
            cell["comparisons"][left + "_minus_" + right] = {
                metric: statistics.median(values) if values else None
                for metric, values in differences.items()}
            if family == "e":
                for metric in ("lag_rts_mean_us", "live_mean", "estimated_live_bytes_mean",
                               "retention_p50_upper_us", "long_argmin_fraction"):
                    values = [left_reps[i]["gc"][metric] - right_reps[i]["gc"][metric]
                              for i in left_reps if left_reps[i]["gc"][metric] is not None
                              and right_reps[i]["gc"][metric] is not None]
                    cell["comparisons"][left + "_minus_" + right][metric] = \
                        statistics.median(values) if values else None
            else:
                for group in ("long", "normal"):
                    for source, metric in (("c_by_thread", "success_rate"),
                                           ("completion_by_thread", "rate")):
                        values = [left_reps[i][source][group][metric] -
                                  right_reps[i][source][group][metric]
                                  for i in left_reps if left_reps[i][source][group][metric] is not None
                                  and right_reps[i][source][group][metric] is not None]
                        cell["comparisons"][left + "_minus_" + right][
                            group + "_" + source + "_" + metric] = \
                            statistics.median(values) if values else None
    return {"schema_version": "vhash-target-aggregate/v1", "verification_status": "未検証の診断値",
            "cells": cells}


def target_run_binary(binary: Path, spec: dict, common: dict, gates: list[dict]) -> dict:
    return _run_binary(binary, spec, common, gates)


def target_main(args, parser) -> int:
    if args.k_sweep:
        parser.error("--k-sweep does not apply to target commands")
    if args.command == "target-aggregate":
        if not args.raw or args.smoke or args.skew is not None:
            parser.error("target-aggregate requires --raw and no run options")
        _write(args.output / "target-aggregate.json", target_aggregate_jobs(
            [json.loads(path.read_text()) for path in args.raw]))
        return 0
    if not args.third_party_cache or not args.third_party_cache.is_absolute() or args.workload is None:
        parser.error("target-run requires --workload and absolute --third-party-cache")
    wait_us = args.wait_us if args.wait_us is not None else (10000 if args.workload == "wait_after_reads" else None)
    skew = args.skew if args.skew is not None else .9
    try:
        specs = target_plan_runs(args.workload, wait_us, skew=skew, smoke=args.smoke)
    except ValueError as exc:
        parser.error(str(exc))
    started = now()
    job = {"schema_version": "vhash-target-job/v1", "command": "target-run", "smoke": args.smoke,
        "workload": args.workload, "wait_us": wait_us, "skew": skew,
        "ccbench_pin": pin.CURRENT_PIN, "patch_sha256": {}, "genome": GC_GENOME,
        "value_bytes": GC_VALUE_BYTES, "verification_status": "未検証の診断値",
        "job_id": socket.gethostname() + "-" + started, "hostname": socket.gethostname(),
        "started": started, "records": [], "builds": {}, "all_pass": False}
    output = args.output / ("raw-target-" + args.workload + "-" + started.replace(":", "-") + ".json")
    try:
        if re.fullmatch(r"pegasus0[0-9]", socket.gethostname()):
            raise RuntimeError("measurement job must run on a compute node")
        job["patch_sha256"] = {str(p.relative_to(ROOT)): sha_file(p) for p in TARGET_STACK}
        job["git_head"] = checked(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.decode().strip()
        job["competing_probe"] = _probe()
        policy = compute._load_policy(ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
        toolchain = compute._resolve_toolchain(policy)
        with tempfile.TemporaryDirectory(prefix="vhash-target-") as temporary:
            scratch = Path(temporary)
            deps = compute._prepare_dependencies(ROOT, policy, args.third_party_cache, scratch, toolchain)
            with patchharness.checkout(pin.CURRENT_PIN) as worktree:
                source = Path(worktree)
                for patch in TARGET_STACK:
                    patchharness.apply_patch(str(patch), str(source))
                binaries = {}
                for kind in ("gc-dependency", "gc-stock", "gc-c", "gc-e",
                             "gc-stock-count", "gc-c-count", "gc-e-count"):
                    binary, gates, seconds = _build_variant(source, scratch / ("build-target-" + kind),
                                                             kind, deps, toolchain)
                    binaries[kind] = (binary, gates)
                    job["builds"][kind] = {"binary_sha256": sha_file(binary), "seconds": seconds,
                                           "gate_receipts": gates}
                common = {"job_id": job["job_id"], "ccbench_pin": pin.CURRENT_PIN,
                          "patch_sha256": job["patch_sha256"], "genome": GC_GENOME}
                for spec in specs:
                    binary, gates = binaries[spec["build_kind"]]
                    record = target_run_binary(binary, spec, common, gates)
                    job["records"].append(record)
                    _write(output, job)
                    if not record["valid"]:
                        raise RuntimeError("invalid target run: " + record.get("invalid_reason", "unknown"))
                job["all_pass"] = True
    except Exception as exc:
        job["error"] = type(exc).__name__ + ": " + str(exc)
        if hasattr(exc, "condition_gate_evidence"):
            job["condition_gate_evidence"] = exc.condition_gate_evidence
    job["ended"] = now()
    _write(output, job)
    print(output)
    return 0 if job["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
