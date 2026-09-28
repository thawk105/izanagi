#!/usr/bin/env python3
"""Cicada selective forwarding diagnostic (all values: 未検証の診断値).

Compute-node submission examples::

  python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:30:00 -- python3 -m orchestrator.campaign.vhash_forwarding_prototype smoke --third-party-cache /absolute/cache
  python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:40:00 -- python3 -m orchestrator.campaign.vhash_forwarding_prototype run --workload many_ops --third-party-cache /absolute/cache

The module only runs inside the submitted job. Its identity is hostname and start time;
PBS_JOBID is not required. No correctness or serializability claim follows from it.
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

from orchestrator.calibrator.benchparse import parse_bench_stdout
from orchestrator.calibrator.runner import competing_bench_pids
from . import condition_meaning_gate as condition
from . import patchharness, pin, s3_mocc_lock_coverage as compute

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "patches/cicada-forwarding-variant.patch"
DEFAULT_OUTPUT = ROOT / "output/env/pegasus/vhash-forwarding-prototype"
DRIVER_ID = "orchestrator.campaign.vhash_forwarding_prototype"
MACROS = {"dependency": (), "stock": ("CICADA_LONGTX",), "fwd": ("CICADA_FWD_ENABLE", "CICADA_LONGTX"),
          "count": ("CICADA_FWD_ENABLE", "CICADA_FWD_COUNT", "CICADA_LONGTX")}
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


def _probe() -> dict:
    start = now()
    pids = competing_bench_pids()
    receipt = {"argv": ["pgrep", "-af", r"ycsb_.*\.exe"], "started": start,
               "ended": now(), "competing": pids}
    if pids:
        raise RuntimeError(f"competing benchmark: {pids}")
    return receipt


def _argv(binary: Path, spec: dict) -> list[str]:
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
              "perf_eligible": perf_eligible(spec["build_kind"]),
              "verification_status": "未検証の診断値", "argv": argv,
              "hostname": socket.gethostname(), "started": start, "ended": now(),
              "seconds": time.monotonic() - tick, "returncode": code,
              "stdout": _capture(stdout), "stderr": _capture(stderr),
              "competing_probe": probe, "gate_receipts": gates,
              "binary_sha256": sha_file(binary), "throughput": None,
              "fwd_counters": None, "longtx_counters": None, "valid": False}
    try:
        if code:
            raise ValueError(f"binary rc={code}")
        text = stdout.decode("utf-8", "replace")
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
    parser.add_argument("command", choices=("smoke", "run", "aggregate"))
    parser.add_argument("--third-party-cache", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workload", choices=WORKLOADS)
    parser.add_argument("--k-sweep", action="store_true")
    parser.add_argument("--raw", type=Path, action="append", help="explicit aggregate input JSON; repeat for each job")
    args = parser.parse_args(argv)
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
                                                    "gate_receipts": gates}
                    for kind in ("stock", "fwd", "count"):
                        binary, gates, seconds = _build_variant(source, scratch / ("build-" + kind),
                                                               kind, deps, toolchain)
                        binaries[kind] = (binary, gates)
                        job["gate_receipts"][kind] = gates
                        job["builds"][kind] = {"seconds": seconds, "binary_sha256": sha_file(binary),
                                               "gate_receipts": gates}
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


if __name__ == "__main__":
    raise SystemExit(main())
