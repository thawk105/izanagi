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
MACROS = {"stock": ("CICADA_LONGTX",), "fwd": ("CICADA_FWD_ENABLE", "CICADA_LONGTX"),
          "count": ("CICADA_FWD_ENABLE", "CICADA_FWD_COUNT", "CICADA_LONGTX")}
WORKLOADS = ("normal", "many_ops", "wait_after_reads")
GC_VALUES = (10, 100, 1000)
COUNTER_PREFIXES = ("CICADA_FWD_V1 ", "CICADA_LONGTX_V1 ")
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
    return [*args, "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_CXX_FLAGS=" + " ".join("-D" + m + "=1" for m in MACROS[kind])]


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
    """Single Cicada build sink; one call for each of stock, fwd, count."""
    start = time.monotonic()
    args = build_args(dependencies, toolchain, kind)
    receipts = [_condition_gate(source, macro, args, toolchain["cxx_path"])
                for macro in MACROS[kind]]
    if len(receipts) != len(MACROS[kind]) or any(
            r["admission"]["admitted"] is not True for r in receipts):
        raise RuntimeError("condition gate rejected before build")
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
    found = [e for e in entries if Path(e["file"]).name == filename and
             "/cc/cicada/" in Path(e["file"]).as_posix()]
    if len(found) != 1:
        raise RuntimeError(f"expected one compile command for {filename}, found {len(found)}")
    return found[0]


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
                                  if not line.lstrip().startswith(b"#")))


def _inert_receipt(source: Path, scratch: Path, args: list[str], cxx: str) -> dict:
    """Pin and patched source use the same compiler argv and build directory."""
    build = scratch / "inert-build"
    checked(["cmake", "-S", str(source), "-B", str(build),
             "-DCMAKE_CXX_COMPILER=" + cxx, *args], timeout=600)
    entries = {name: _compile_entry(build, name) for name in
               ("transaction.cc", "ycsb_cicada.cc")}
    before = {name: _preprocess(entry) for name, entry in entries.items()}
    with patchharness.applied(str(PATCH), pin.CURRENT_PIN, str(source)):
        after = {name: _preprocess(entry) for name, entry in entries.items()}
    receipt = {"gate": False, "pin_sha256": before, "patched_sha256": after,
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
    for value in values:
        if value is not None and not isinstance(value.get("threads"), list):
            raise ValueError("counter threads missing")
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


def _sum_threads(counter: dict | None, keys: tuple[str, ...], *, long_only=False) -> dict:
    if counter is None:
        return {}
    threads = [t for t in counter["threads"] if not long_only or t.get("long")]
    return {key: sum(int(t.get(key, 0)) for t in threads) for key in keys}


def aggregate(raw: dict) -> dict:
    cells: dict[str, dict] = {}
    for record in raw["records"]:
        if not record.get("valid"):
            continue
        key = f"{record['workload']}/gc={record['gc_inter_us']}/k={record['k']}"
        cell = cells.setdefault(key, {"workload": record["workload"],
                 "gc_inter_us": record["gc_inter_us"], "k": record["k"],
                 "throughput": {arm: [] for arm in ("stock", "c", "f")},
                 "c_counters": [], "f_counters": [], "longtx": {arm: [] for arm in ("stock", "c", "f")}})
        arm = record["policy"]
        if record["perf_eligible"]:
            cell["throughput"][arm].append({"rep": record["rep"], "value": record["throughput"]})
            cell["longtx"][arm].append(_sum_threads(record["longtx_counters"],
                                                         ("commits", "aborts"), long_only=True))
        else:
            values = _sum_threads(record["fwd_counters"],
                ("triggers", "attempts", "success", "read_mismatch", "write_constraint",
                 "conflict", "ineligible", "special_after_forward", "f_aborts",
                 "advance_clock_sum", "pos_before_sum", "pos_after_sum"))
            cell["c_counters" if arm == "c" else "f_counters"].append(values)
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
    return {"schema_version": "vhash-forwarding-aggregate/v1",
            "verification_status": "未検証の診断値", "conditions": raw.get("conditions", {}),
            "cells": cells}


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "run", "aggregate"))
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workload", choices=WORKLOADS)
    parser.add_argument("--k-sweep", action="store_true")
    parser.add_argument("--raw", type=Path, help="aggregate input JSON")
    args = parser.parse_args(argv)
    if not args.third_party_cache.is_absolute():
        parser.error("--third-party-cache must be an absolute path")
    if args.command == "run" and args.workload is None:
        parser.error("run requires --workload")
    if args.k_sweep and args.workload != "many_ops":
        parser.error("--k-sweep requires --workload many_ops")
    if args.command == "aggregate":
        files = [args.raw] if args.raw else sorted(args.output.glob("raw-*.json"))
        if not files:
            parser.error("no raw JSON input")
        merged = {"conditions": {}, "records": []}
        for path in files:
            raw = json.loads(path.read_text())
            merged["conditions"] = raw.get("conditions", {})
            merged["records"].extend(raw["records"])
        _write(args.output / "aggregate.json", aggregate(merged))
        return 0
    started = now()
    job = {"schema_version": "vhash-forwarding-job/v1", "git_head": None,
           "ccbench_pin": pin.CURRENT_PIN, "patch_sha256": sha_file(PATCH),
           "verification_status": "未検証の診断値", "command": args.command,
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
                if args.command == "smoke":
                    tick = time.monotonic()
                    inert_args = [a for a in build_args(deps, toolchain, "stock")
                                  if not a.startswith("-DCMAKE_CXX_FLAGS=")]
                    job["inert_receipt"] = _inert_receipt(source, scratch,
                                               inert_args, toolchain["cxx_path"])
                    job["inert_receipt"]["seconds"] = time.monotonic() - tick
                with patchharness.applied(str(PATCH), pin.CURRENT_PIN, str(source)):
                    binaries = {}
                    job["gate_receipts"] = {}
                    for kind in ("stock", "fwd", "count"):
                        binary, gates, seconds = _build_variant(source, scratch / ("build-" + kind),
                                                               kind, deps, toolchain)
                        binaries[kind] = (binary, gates)
                        job["gate_receipts"][kind] = gates
                        job["builds"][kind] = {"seconds": seconds, "binary_sha256": sha_file(binary),
                                               "gate_receipts": gates}
                    common = {"git_head": job["git_head"], "ccbench_pin": pin.CURRENT_PIN,
                              "patch_sha256": job["patch_sha256"],
                              "inert_receipt": job["inert_receipt"]}
                    for spec in plan_runs(args.command, args.workload, args.k_sweep):
                        if args.command == "smoke" and spec["build_kind"] != "count" and \
                                not job.get("smoke_count_checked"):
                            many = [r for r in job["records"] if r["workload"] == "many_ops"
                                    and r["build_kind"] == "count"]
                            attempts = sum(_sum_threads(r["fwd_counters"], ("attempts",))
                                           .get("attempts", 0) for r in many)
                            for k, skew in ((1, 0.9), (1, 0.99)):
                                if attempts:
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
                                    attempts += _sum_threads(result["fwd_counters"],
                                                             ("attempts",))["attempts"]
                            job["smoke_count_checked"] = True
                            if not attempts:
                                raise RuntimeError("many_ops forwarding attempts remain zero after smoke fallback")
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
