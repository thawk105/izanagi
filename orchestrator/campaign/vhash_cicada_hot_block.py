#!/usr/bin/env python3
"""Pinned Cicada hot block experiment. All throughput is exploratory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import tempfile
import shlex
import shutil
import socket
import statistics
import subprocess
import sys
import time

from orchestrator.calibrator.benchparse import parse_bench_stdout
from orchestrator.calibrator.runner import competing_bench_pids
from . import condition_meaning_gate as condition, patchharness
from . import s3_mocc_lock_coverage as compute
from .materializer_admission import non_admissible_materializer
from .model import cmake_cache_variable_for_axis

ROOT = Path(__file__).resolve().parents[2]
PIN = "68106660686232781bca3be792a750d3e19d7a8a"
VARIANT = "patches/cicada-vhash-hot-block-variant.patch"
TRACE = "patches/instr-cicada-trace.patch"
BROKEN = {"B1": "patches/broken-cicada-vhash-stale-hot.patch",
          "B2": "patches/broken-cicada-vhash-skip-pending.patch"}
DRIVER_ID = "orchestrator.campaign.vhash_cicada_hot_block"
MATERIALIZER = DRIVER_ID + "._build_one"
KS = (0, 1, 2, 4, 8)
CELLS = {f"ro{ro}-gc{gc}": {"ro": ro, "gc": gc, "rr": 50, "rmw": 0, "max_ope": 10}
         for ro in (0, 50, 95) for gc in (10, 1000, 100000)}
CELLS.update({"rr5": {"ro": -1, "gc": 100, "rr": 5, "rmw": 0, "max_ope": 10},
              "rr50": {"ro": -1, "gc": 100, "rr": 50, "rmw": 0, "max_ope": 10},
              "rr95": {"ro": -1, "gc": 10, "rr": 95, "rmw": 0, "max_ope": 10}})
COUNT_CELLS = ("ro95-gc100000", "ro95-gc10", "ro0-gc10", "rr50")
TRACE_CELLS = {
    "T1": {"ro": 95, "gc": 100000, "rr": 50, "rmw": 0, "max_ope": 10},
    "T2": {"ro": 50, "gc": 10, "rr": 50, "rmw": 0, "max_ope": 10},
    "T3": {"ro": -1, "gc": 100, "rr": 0, "rmw": 1, "max_ope": 5},
}
GENOME = {"BACK_OFF": 0, "INLINE_VERSION_OPT": 1,
          "INLINE_VERSION_PROMOTION": 0, "REUSE_VERSION": 1,
          "WRITE_LATEST_ONLY": 0}
COUNT_PREFIX = "CICADA_VHASH_COUNT_JSON "
EVENT_RE = re.compile(r"CICADA_BREAK_EVENT slug=([a-z-]+) stage=(reached|changed|committed) tx_wts=(\d+) key=((?:[0-9a-f]{2})+) read_wts=(\d+)")
FIRED_RE = re.compile(r"CICADA_BREAK_FIRED slug=([a-z-]+) reached=(\d+) changed=(\d+) committed=(\d+)")
INTEGRITY_ZERO = ("orphan_reads", "version_dups", "dup_txids", "genesis_commits",
                  "missing_txids", "write_version_mismatch", "malformed_keys",
                  "framing_violations", "lock_coverage_violations",
                  "write_intent_violations", "permutation_violations")


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def checked(argv, *, cwd=None, timeout=900):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"command rc={result.returncode}: {argv!r}: {result.stderr[-2000:]!r}")
    return result


def compute_only():
    if re.fullmatch(r"pegasus0\d+", socket.gethostname()):
        raise RuntimeError("build and measurement require a compute node")


def probe():
    result = {"started": now(), "pids": competing_bench_pids(), "ended": now(),
              "surface": "competing_bench_pids (ycsb/bench)"}
    if result["pids"]:
        raise RuntimeError(f"competing benchmark processes: {result['pids']}")
    return result


def build_specs():
    specs = {}
    for kind in ("perf", "count", "trace"):
        for k in KS:
            name = f"{kind}-k{k}"
            patches = [VARIANT] if kind != "trace" else [TRACE, VARIANT]
            specs[name] = {"kind": kind, "k": k, "patches": patches,
                           "macros": {"CICADA_VHASH_K": k, "CICADA_VHASH_WL": 1,
                                      **({"CICADA_VHASH_COUNT": 1}
                                         if kind == "count" else {})},
                           "trace": int(kind == "trace")}
    for broken, patch in BROKEN.items():
        specs[f"broken-{broken}"] = {"kind": "broken", "k": 4,
             "patches": [TRACE, VARIANT, patch], "trace": 1,
             "macros": {"CICADA_VHASH_K": 4, "CICADA_VHASH_WL": 1}}
    return specs


def rotation(round_index, cell_index, ks=KS):
    return tuple(ks[(round_index + cell_index + offset) % len(ks)]
                 for offset in range(len(ks)))


def plan_perf(job_index, *, rounds=6, cells=None, ks=KS):
    if job_index not in (0, 1, 2):
        raise ValueError("job index must be 0, 1 or 2")
    if rounds not in (4, 6):
        raise ValueError("rounds must be 4 or 6")
    selected = list(CELLS if cells is None else cells)
    if 0 not in ks:
        raise ValueError("stock arm required")
    jobs = 2 if rounds == 4 else 3
    if job_index >= jobs:
        return []
    return [{"cell": cell, "k": k, "round": round_index,
             "order_index": order_index, "job_index": job_index, "build": f"perf-k{k}"}
            for round_index in range(job_index * 2, job_index * 2 + 2)
            for cell_index, cell in enumerate(selected)
            for order_index, k in enumerate(rotation(round_index, cell_index, ks))]


def plan_count(ks=KS):
    return [{"cell": cell, "k": k, "round": 0, "order_index": i,
             "build": f"count-k{k}"}
            for cell in COUNT_CELLS for i, k in enumerate(ks)]


def plan_trace(job_index, ks=KS):
    if job_index not in (0, 1):
        raise ValueError("trace job index must be 0 or 1")
    cells = ("T1", "T2") if job_index == 0 else ("T3",)
    runs = [{"cell": cell, "k": k, "round": 0, "order_index": i,
             "build": f"trace-k{k}"} for cell in cells for i, k in enumerate(ks)]
    if job_index == 0:
        runs += [{"cell": cell, "k": 4, "round": 0, "order_index": len(ks) + i,
                  "build": f"broken-{broken}"}
                 for cell in cells for i, broken in enumerate(BROKEN)]
    return runs


def estimate(smoke):
    """Predeclared ladder, using only smoke wall times, never throughput."""
    sharing = smoke.get("build_sharing", {})
    if sharing.get("mode") != "shared-verified":
        return {"schema": "vhash-hot-estimate/v1", "stop": True,
                "selection": None, "steps": [],
                "reason": sharing.get("reason") or "shared binaries not verified by smoke"}
    build = float(smoke["build_seconds"])
    perf_wall = float(smoke["max_perf_run_seconds"])
    trace_wall = float(smoke["trace_run_verify_seconds"])
    smoke_wall = float(smoke["smoke_seconds"])
    if min(build, perf_wall, trace_wall, smoke_wall) <= 0:
        raise ValueError("smoke durations must be positive")
    steps = []
    configs = [(6, list(CELLS), KS), (4, list(CELLS), KS),
               (4, [c for c in CELLS if c.startswith(("ro0-", "ro95-")) and
                    CELLS[c]["gc"] in (10, 100000)] + ["rr5", "rr50", "rr95"], KS),
               (4, [c for c in CELLS if c.startswith(("ro0-", "ro95-")) and
                    CELLS[c]["gc"] in (10, 100000)] + ["rr5", "rr50", "rr95"], (0, 1, 8))]
    for rounds, cells, ks in configs:
        perf_jobs = rounds // 2
        perf_runs_per_job = 2 * len(cells) * len(ks)
        perf_job = perf_runs_per_job * perf_wall + 60
        count_runs = len(COUNT_CELLS) * len(ks)
        count_job = count_runs * perf_wall + 60
        trace_jobs = [len(plan_trace(j, ks)) for j in (0, 1)]
        trace_job = max(trace_jobs) * trace_wall
        total = smoke_wall + perf_jobs * perf_job + count_job + 2 * trace_job
        entry = {"rounds": rounds, "cells": cells, "ks": list(ks), "perf_jobs": perf_jobs,
                 "perf_job_seconds": perf_job, "count_job_seconds": count_job,
                 "trace_job_seconds_upper": trace_job, "total_node_seconds": total,
                 "job_walltime_seconds": {"smoke": 2 * smoke_wall + 600,
                    "perf": 2 * perf_job + 600, "count": 2 * count_job + 600,
                    "trace": 2 * trace_job + 600}, "accepted": total < 7200}
        steps.append(entry)
        if entry["accepted"]:
            break
    return {"schema": "vhash-hot-estimate/v1", "threshold_node_seconds": 7200,
            "steps": steps, "selection": steps[-1] if steps[-1]["accepted"] else None,
            "stop": not steps[-1]["accepted"],
            "queue_rule": "overall-grace >= queue-wait-timeout"}


def _gate(source, macro, value, args, cxx):
    captured = condition.capture_define_inputs(source, configure_args=tuple(args))
    request = condition.make_define_request(driver_id=DRIVER_ID, macro=macro,
                                            requested_value=value, default_value=0)
    with condition._configured_define_compile_commands(captured, request=request,
                                                        cxx=cxx, cmake="cmake") as commands:
        supply = condition.evaluate_define_supply_effectuation(captured, request=request,
             cxx=cxx, cmake="cmake", configured_commands=commands)
        meaning = condition.evaluate_define_runtime_meaning(captured, request=request,
             declaration=condition.declare_define_runtime_meaning(request), cxx=cxx,
             cmake="cmake", configured_commands=commands)
    admission = condition.require_condition_gate_family([supply], [meaning],
                                                        use_class="raw-measurement")
    receipt = {"macro": macro, "value": value,
               "supply": json.loads(supply.canonical_json()),
               "meaning": json.loads(meaning.canonical_json()),
               "admission": json.loads(admission.canonical_json())}
    if not admission.admitted:
        raise RuntimeError(f"condition gate rejected {macro}: {receipt}")
    return receipt


def _compile_entries(build):
    entries = json.loads((build / "compile_commands.json").read_text())
    target = ("CMakeFiles/ycsb_cicada.exe.dir/", "CMakeFiles/ycsb_cicada.dir/")
    result = {}
    for name in ("transaction.cc", "util.cc", "ycsb_cicada.cc"):
        found = [e for e in entries if Path(e["file"]).name == name and
                 "/cc/cicada/" in Path(e["file"]).as_posix() and
                 any(marker in str(e.get("command", "")) + str(e.get("output", "")) +
                     " ".join(e.get("arguments", [])) for marker in target)]
        if len(found) != 1:
            raise RuntimeError(f"expected one target compile entry for {name}, got {len(found)}")
        result[name] = found[0]
    return result


def _argv_entry(entry):
    return list(entry.get("arguments") or shlex.split(entry["command"]))


def _preprocessed(entry):
    argv = _argv_entry(entry)
    clean, skip = [], False
    for arg in argv:
        if skip:
            skip = False
        elif arg == "-o":
            skip = True
        elif arg != "-c":
            clean.append(arg)
    result = checked([*clean, "-E"], cwd=Path(entry["directory"]), timeout=180)
    return hashlib.sha256(b"\n".join(x for x in result.stdout.splitlines()
        if x.strip() and not x.lstrip().startswith(b"#"))).hexdigest()


def _tuple_size(source, build, entry):
    """Compile sizeof under the exact ycsb_cicada target flags."""
    original = _argv_entry(entry)
    argv, skip = [], False
    for arg in original:
        if skip:
            skip = False
        elif arg == "-o":
            skip = True
        elif arg != "-c" and Path(arg).name != Path(entry["file"]).name:
            argv.append(arg)
    probe_source = build / "sizeof_tuple.cc"
    probe_binary = build / "sizeof_tuple.exe"
    probe_source.write_text(f'#include "{source / "cc/cicada/include/tuple.hh"}"\n'
                            '#include <cstdio>\nint main() { std::printf("%zu\\n", sizeof(Tuple)); }\n')
    result = subprocess.run([*argv, str(probe_source), "-o", str(probe_binary)],
                            cwd=entry["directory"], capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f"Tuple sizeof build failed: {result.stderr[-1000:]!r}")
    return int(checked([str(probe_binary)], timeout=30).stdout.strip())


def inert_receipt(source, dependency_build):
    before = _compile_entries(dependency_build)
    left = {name: _preprocessed(entry) for name, entry in before.items()}
    strict_patches(source, [VARIANT])
    right = {name: _preprocessed(entry) for name, entry in before.items()}
    if left != right:
        raise RuntimeError(f"macro-free -E mismatch: {left} != {right}")
    return {"pin": left, "patched": right, "matched": True,
            "normalization": "remove blank and # line-marker lines"}


def strict_patches(source, names):
    for name in names:
        patch = ROOT / name
        if not patch.is_file():
            raise FileNotFoundError(patch)
        touched = patchharness.patch_files(str(patch), str(source))
        if not touched or any(not item.startswith("cc/cicada/") for item in touched):
            raise RuntimeError(f"patch escapes Cicada owner surface: {name}: {touched}")
        checked(["git", "-C", str(source), "apply", "--check", str(patch)])
        patchharness.apply_patch(str(patch), str(source))


def _build_one(source, build, spec, dependencies, toolchain):
    non_admissible_materializer(MATERIALIZER)
    tick = time.monotonic()
    args = [a for a in compute._common_configure_args(trace=spec["trace"],
            toolchain=toolchain, dependencies=dependencies)
            if a not in compute.STOCK_G.cmake_defines()]
    args += [f"-D{cmake_cache_variable_for_axis('cicada', key)}={value}"
             for key, value in GENOME.items()]
    args += ["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCCBENCH_ADD_ANALYSIS=0"]
    gates = [_gate(source, macro, value, args, toolchain["cxx_path"])
             for macro, value in spec["macros"].items() if value != 0]
    flags = " ".join(f"-D{key}={value}" for key, value in spec["macros"].items())
    args.append("-DCMAKE_CXX_FLAGS=" + flags)
    checked(["cmake", "-S", str(source), "-B", str(build),
             "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args], timeout=600)
    commands = _compile_entries(build)
    tuple_size = _tuple_size(source, build, commands["transaction.cc"])
    for entry in commands.values():
        command = " ".join(_argv_entry(entry))
        if spec["kind"] == "perf" and re.search(r"(?:^|\s)-D(?:TRACE|CCBENCH_TRACE|CICADA_VHASH_COUNT|ADD_ANALYSIS)=1(?:\s|$)", command):
            raise RuntimeError("instrumentation leaked into performance compile command")
    checked(["cmake", "--build", str(build), "--target", "ycsb_cicada.exe", "-j", "48"], timeout=900)
    binary = build / "cc/cicada/ycsb_cicada.exe"
    if not binary.is_file():
        raise RuntimeError(f"missing binary {binary}")
    return {"sha256": sha(binary), "path": str(binary), "seconds": time.monotonic() - tick,
            "kind": spec["kind"], "k": spec["k"],
            "patch_order": list(spec["patches"]),
            "patch_sha256": {n: sha(ROOT / n) for n in spec["patches"]},
            "configure_args": args, "compile_commands": commands, "gate_receipts": gates,
            "tuple_size_bytes": tuple_size}


def runtime_dependencies(binary):
    """Require resolved shared libraries on a stable shared path; record hashes."""
    result = checked(["ldd", str(binary)], timeout=30).stdout.decode("utf-8", "replace")
    paths = []
    for line in result.splitlines():
        if "not found" in line:
            raise RuntimeError(f"unresolved binary dependency: {line}")
        match = re.search(r"=>\s+(/\S+)|^\s*(/\S+)\s+\(", line)
        if match:
            paths.append(Path(match[1] or match[2]))
    return {str(p): sha(p) for p in paths}


def verify_binary(manifest, name):
    entry = manifest["builds"][name]
    binary = Path(entry["path"])
    if sha(binary) != entry["sha256"]:
        raise RuntimeError(f"binary sha256 mismatch: {name}")
    for path, digest in entry["runtime_dependencies"].items():
        if sha(path) != digest:
            raise RuntimeError(f"runtime dependency sha256 mismatch: {path}")
    return binary


def sharing_preflight(manifest, names):
    """Verify every shared binary and its current dynamic linker resolution."""
    for name in names:
        try:
            binary = verify_binary(manifest, name)
            if runtime_dependencies(binary) != manifest["builds"][name]["runtime_dependencies"]:
                return f"ldd dependency resolution mismatch: {name}"
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            return f"shared binary verification failed: {name}: {exc}"
    return None


def _flags(cell, kind):
    trace = kind in ("trace", "broken")
    cfg = TRACE_CELLS[cell] if trace else CELLS[cell]
    return ["-thread_num=48", f"-ycsb_tuple_num={200 if trace else 1000000}",
            "-ycsb_zipf_skew=0.9", f"-ycsb_rratio={cfg['rr']}",
            f"-ycsb_max_ope={cfg['max_ope']}", f"-ycsb_rmw={cfg['rmw']}",
            f"-extime={1 if trace else 3}", "-clocks_per_us=2100",
            f"-gc_inter_us={cfg['gc']}", f"--vhash_ronly_pct={cfg['ro']}",
            *( ["-group_commit=0"] if trace else [])]


def _capture(data):
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "text": data[-65536:].decode("utf-8", "replace"),
            "truncated": len(data) > 65536}


def parse_count(stdout):
    lines = [line[len(COUNT_PREFIX):] for line in stdout.splitlines()
             if line.startswith(COUNT_PREFIX)]
    if len(lines) != 1:
        raise ValueError(f"expected one COUNT JSON line, got {len(lines)}")
    value = json.loads(lines[0])
    if not isinstance(value, dict):
        raise ValueError("COUNT JSON must be an object")
    return value


COUNT_SCALARS = ("hot", "fallback_odd", "fallback_changed", "cold",
                 "ro_commit", "ro_abort", "update_commit", "update_abort",
                 "install_wait_cycles", "install_hold_cycles", "install_count",
                 "gc_hold_cycles", "gc_count")
COUNT_BUCKETS = {"hops": 7, "snapshot_lag_ts": 18}
COUNT_DERIVED = {
    "install_hold_cycles_per_update_commit": "install_hold_cycles / update_commit (null when update_commit is zero)",
    "install_wait_cycles_per_update_commit": "install_wait_cycles / update_commit (null when update_commit is zero)",
    "gc_hold_cycles_per_update_commit": "gc_hold_cycles / update_commit (null when update_commit is zero)",
    "realized_ro_commit_fraction": "ro_commit / (ro_commit + update_commit) (null when denominator is zero)",
}


def aggregate_count(value, k):
    """Sum the patch's per-thread counters and expose defined diagnostic ratios."""
    if (not isinstance(value, dict) or value.get("schema_version") != 1 or
            value.get("k") != k or type(value.get("sizeof_tuple")) is not int or
            value["sizeof_tuple"] <= 0 or not isinstance(value.get("workers"), list) or
            len(value["workers"]) != 256):
        raise ValueError("invalid COUNT root")
    totals = {name: 0 for name in COUNT_SCALARS}
    totals.update({name: [0] * length for name, length in COUNT_BUCKETS.items()})
    for thid, worker in enumerate(value["workers"]):
        if not isinstance(worker, dict) or worker.get("thid") != thid:
            raise ValueError("invalid COUNT worker id")
        for name in COUNT_SCALARS:
            n = worker.get(name)
            if type(n) is not int or n < 0:
                raise ValueError(f"invalid COUNT counter: {name}")
            totals[name] += n
        for name, length in COUNT_BUCKETS.items():
            bucket = worker.get(name)
            if (not isinstance(bucket, list) or len(bucket) != length or
                    any(type(n) is not int or n < 0 for n in bucket)):
                raise ValueError(f"invalid COUNT bucket: {name}")
            totals[name] = [a + b for a, b in zip(totals[name], bucket)]
    updates = totals["update_commit"]
    commits = totals["ro_commit"] + updates
    totals.update({
        "install_hold_cycles_per_update_commit": totals["install_hold_cycles"] / updates if updates else None,
        "install_wait_cycles_per_update_commit": totals["install_wait_cycles"] / updates if updates else None,
        "gc_hold_cycles_per_update_commit": totals["gc_hold_cycles"] / updates if updates else None,
        "realized_ro_commit_fraction": totals["ro_commit"] / commits if commits else None,
    })
    return {"schema_version": 1, "k": k, "sizeof_tuple": value["sizeof_tuple"],
            "worker_count": len(value["workers"]), **totals}


def _trace_rows(directory):
    counts = {k: 0 for k in ("C", "R", "W", "E")}
    versions = {}
    for path in Path(directory).glob("trace_*.log"):
        for line in path.read_text(errors="replace").splitlines():
            fields = line.split()
            if fields and fields[0] in counts:
                counts[fields[0]] += 1
            if fields and fields[0] == "C":
                if len(fields) != 7:
                    raise ValueError(f"malformed C row: {line}")
                wts = (int(fields[3]) << 32) | int(fields[4])
                if wts in versions:
                    raise ValueError(f"duplicate commit wts: {wts}")
                versions[wts] = int(fields[1])
    return counts, versions


def _break_events(stderr, build):
    slug = "stale-hot" if build == "broken-B1" else "skip-pending"
    events, fired = [], []
    stages = {stage: 0 for stage in ("reached", "changed", "committed")}
    for line in stderr.splitlines():
        if line.startswith("CICADA_BREAK_EVENT "):
            match = EVENT_RE.fullmatch(line)
            if not match:
                raise ValueError(f"malformed break event: {line}")
            if match[1] != slug:
                raise ValueError("wrong break event slug")
            stages[match[2]] += 1
            events.append({"stage": match[2], "tx_wts": int(match[3]),
                           "key": match[4], "read_wts": int(match[5])})
        if line.startswith("CICADA_BREAK_FIRED "):
            match = FIRED_RE.fullmatch(line)
            if not match:
                raise ValueError(f"malformed break summary: {line}")
            if match[1] != slug:
                raise ValueError("wrong break summary slug")
            fired.append({"reached": int(match[2]), "changed": int(match[3]),
                          "committed": int(match[4])})
    if len(fired) != 1:
        raise ValueError(f"expected one break summary: {build}")
    if stages != fired[0]:
        raise ValueError(f"break event/summary mismatch: {stages} != {fired[0]}")
    return {"events": events, "event_stages": stages, "fired": fired[0]}


def _attribute(record, versions, events, initial_wts):
    tx_wts = {tx: wts for wts, tx in versions.items()}
    matching = []
    for anomaly in record.get("anomalies", []):
        matches = []
        for edge in anomaly.get("edges", []):
            for reason in edge.get("reasons", []):
                if str(reason.get("type", "")).lower() != "rw":
                    continue
                for event in events:
                    if event["stage"] != "committed":
                        continue
                    if tx_wts.get(edge.get("from")) != event["tx_wts"] or reason.get("key") != event["key"]:
                        continue
                    read_wts = event["read_wts"]
                    version = [1, 0] if read_wts == initial_wts else [read_wts >> 32, read_wts & 0xffffffff]
                    if reason.get("u_ver") == version:
                        matches.append({"edge": edge, "event": event})
        if matches:
            matching.append({"cycle": anomaly.get("cycle"), "matches": matches[:3]})
    return {"witness_count": len(matching), "examples": matching[:3]}


def _verify_trace(trace_dir, source, commits, stderr, build):
    counts, versions = _trace_rows(trace_dir)
    argv = [sys.executable, "-m", "verifier", str(trace_dir), "--json", "--quiet",
            "--protocol", "cicada", "--ccbench-root", str(source),
            "--expected-commits", str(commits)]
    tick = time.monotonic()
    completed = subprocess.run(argv, cwd=ROOT / "orchestrator", capture_output=True, timeout=900)
    if completed.returncode not in (0, 1, 3):
        raise RuntimeError(f"verifier usage/infra rc={completed.returncode}: {completed.stderr[-1000:]!r}")
    record = json.loads(completed.stdout)["results"][0]
    integrity = record.get("integrity") or {}
    clean = counts["C"] == commits and all(integrity.get(k) == 0 for k in INTEGRITY_ZERO)
    if not clean:
        raise RuntimeError(f"trace integrity failed: commits={commits} rows={counts} integrity={integrity}")
    result = {"argv": argv, "rc": completed.returncode,
              "seconds": time.monotonic() - tick, "verdict": record.get("verdict"),
              "total_cycles": record.get("total_cycles"), "integrity": integrity,
              "rows": counts, "expected_commits": commits, "clean": clean,
              "json_sha256": hashlib.sha256(completed.stdout).hexdigest()}
    if not _valid_trace_verdict(result):
        raise RuntimeError(f"verifier rc/verdict/cycles contract violation: {result['rc']}, "
                           f"{result['verdict']}, {result['total_cycles']}")
    if build.startswith("broken-"):
        event = _break_events(stderr, build)
        match = re.search(r"^CICADA_TRACE_INITIAL_WTS=(\d+)$", stderr, re.MULTILINE)
        if not match:
            raise ValueError("initial trace wts missing")
        result["break"] = {**event, **_attribute(record, versions, event["events"], int(match[1]))}
    return result


def run_one(manifest, spec, *, scratch, source=None):
    entry = manifest["builds"][spec["build"]]
    binary = verify_binary(manifest, spec["build"])
    probe_result = probe()
    trace = entry["kind"] in ("trace", "broken")
    trace_dir = scratch / (spec["build"] + "-" + spec["cell"])
    if trace:
        trace_dir.mkdir(parents=True, exist_ok=False)
    argv = [str(binary), *_flags(spec["cell"], entry["kind"])]
    start, tick = now(), time.monotonic()
    env = os.environ.copy()
    if trace:
        env["IZANAGI_TRACE_DIR"] = str(trace_dir)
    # wait4 provides the RSS of this exact child, not a process-wide cumulative max.
    with tempfile.TemporaryFile() as out_file, tempfile.TemporaryFile() as err_file:
        child = subprocess.Popen(argv, stdout=out_file, stderr=err_file, env=env)
        usage = None
        while True:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                rc = os.waitstatus_to_exitcode(status)
                child.returncode = rc
                break
            if time.monotonic() - tick > 180:
                child.kill()
                _, _, usage = os.wait4(child.pid, 0)
                child.returncode = -signal.SIGKILL
                rc = 124
                break
            time.sleep(0.05)
        out_file.seek(0)
        err_file.seek(0)
        stdout, stderr = out_file.read(), err_file.read()
    wall = time.monotonic() - tick
    parsed = parse_bench_stdout(stdout.decode("utf-8", "replace"))
    record = {"schema": "vhash-hot-run/v1", "node": socket.gethostname(),
        "started": start, "ended": now(), "pbs_job_id": os.environ.get("PBS_JOBID"),
        "job_id": manifest.get("job_id"), "job_index": spec.get("job_index"),
        "pin": PIN, "patch_sha256": entry["patch_sha256"], "binary_sha256": entry["sha256"],
        "compile_commands": entry["compile_commands"], "build": spec["build"],
        "gate_receipts": entry["gate_receipts"],
        "tuple_size_bytes": entry["tuple_size_bytes"],
        "build_kind": entry["kind"], "cell": spec["cell"], "k": spec["k"],
        "round": spec["round"], "order_index": spec["order_index"],
        "argv": argv, "rc": rc, "elapsed_seconds": wall,
        "stdout": _capture(stdout), "stderr": _capture(stderr),
        "throughput": float(parsed["throughput[tps]"]) if "throughput[tps]" in parsed else None,
        "commits": int(parsed["commit_counts_"]) if "commit_counts_" in parsed else None,
        "aborts": int(parsed["abort_counts_"]) if "abort_counts_" in parsed else None,
        "maxrss_kb": usage.ru_maxrss, "count": None, "trace": None,
        "perf_eligible": entry["kind"] == "perf" and rc == 0,
        "competing_probe": probe_result}
    if rc == 0 and entry["kind"] == "count":
        record["count"] = parse_count(stdout.decode("utf-8", "replace"))
    if rc == 0 and trace:
        if source is None or record["commits"] is None:
            raise RuntimeError("trace verification requires source and commit count")
        record["trace"] = _verify_trace(trace_dir, source, record["commits"],
                                         stderr.decode("utf-8", "replace"), spec["build"])
    return record


def broken_verdict(record):
    trace = record["trace"]
    event = trace["break"]
    fired = event["fired"]
    if record["build"] == "broken-B1":
        detected = (fired["committed"] >= 1 and trace["verdict"] == "non-serializable"
                    and trace["total_cycles"] > 0 and event["witness_count"] >= 1)
        return {"status": "detected" if detected else "undetected",
                "needs_B3": fired["committed"] >= 1 and event["witness_count"] == 0}
    predicted = fired["committed"] == 0 and not (
        trace["verdict"] == "non-serializable" and trace["total_cycles"] > 0)
    if record.get("cell") == "T1":
        predicted = predicted and fired["reached"] == 0
    elif record.get("cell") == "T2":
        predicted = predicted and fired["reached"] == fired["changed"]
    return {"status": "validation-stopped" if predicted and fired["changed"] else
            "unreached" if predicted else "prediction-failed",
            "prediction_met": predicted, "attributed_cycles": event["witness_count"]}


def _valid_trace_verdict(trace):
    cycles = trace.get("total_cycles")
    return (type(cycles) is int and cycles >= 0 and
            ((cycles == 0 and trace.get("rc") == 3 and
              trace.get("verdict") == "indeterminate") or
             (cycles > 0 and trace.get("rc") == 1 and
              trace.get("verdict") == "non-serializable")))


def aggregate_jobs(jobs, *, rounds=6, cells=None, ks=KS):
    selected = list(CELLS if cells is None else cells)
    expected_jobs = set(range(rounds // 2))
    records = [r for job in jobs for r in job["records"]]
    perf = [r for r in records if r["build_kind"] == "perf"]
    traces = [r for r in records if r["build_kind"] in ("trace", "broken")]
    counts = [r for r in records if r["build_kind"] == "count"]
    count_keys = {(r["cell"], r["k"]) for r in counts}
    required_count = {(cell, k) for cell in COUNT_CELLS for k in ks}
    if count_keys != required_count or len(counts) != len(required_count):
        raise ValueError(f"COUNT coverage mismatch: missing={required_count-count_keys}")
    if any(r["rc"] != 0 or r.get("count") is None or
           r.get("build") != f"count-k{r['k']}" for r in counts):
        raise ValueError("invalid COUNT run")
    keys = [(j, round_index, cell, k) for j in expected_jobs
            for round_index in range(j * 2, j * 2 + 2)
            for cell in selected for k in ks]
    by_key = {}
    hashes = {}
    for r in perf:
        key = (r["job_index"], r["round"], r["cell"], r["k"])
        if key in by_key or key not in keys:
            raise ValueError(f"duplicate or unexpected perf run: {key}")
        by_key[key] = r
        if r["build"] != f"perf-k{r['k']}" or r["pin"] != PIN:
            raise ValueError(f"wrong perf build/pin: {key}")
        if type(r.get("tuple_size_bytes")) is not int or r["tuple_size_bytes"] <= 0:
            raise ValueError(f"missing measured Tuple size: {key}")
        signature = (r["binary_sha256"], json.dumps(r["patch_sha256"], sort_keys=True))
        if r["k"] in hashes and hashes[r["k"]] != signature:
            raise ValueError(f"sha256 mismatch for K={r['k']}")
        hashes[r["k"]] = signature
    if set(by_key) != set(keys):
        raise ValueError(f"missing perf runs: {sorted(set(keys)-set(by_key))[:3]}")
    failed = {r["k"] for r in traces if r["build_kind"] == "trace" and
              r.get("trace") and (r["trace"].get("rc") == 1 or
                                   r["trace"].get("total_cycles", 0) > 0)}
    trace_rows = [r for r in traces if r["build_kind"] == "trace"]
    trace_keys = {(r["cell"], r["k"]) for r in trace_rows}
    required_trace = {(cell, k) for cell in TRACE_CELLS for k in ks}
    if trace_keys != required_trace or len(trace_rows) != len(required_trace):
        raise ValueError(f"trace coverage mismatch: missing={required_trace-trace_keys}")
    broken_rows = [r for r in traces if r["build_kind"] == "broken"]
    broken_keys = {(r["build"], r["cell"]) for r in broken_rows}
    required_broken = {(f"broken-{name}", cell) for name in BROKEN
                       for cell in ("T1", "T2")}
    if broken_keys != required_broken or len(broken_rows) != len(required_broken):
        raise ValueError(f"broken trace coverage mismatch: missing={required_broken-broken_keys}")
    for r in traces:
        if r["build_kind"] == "trace" and (r["rc"] != 0 or not r.get("trace") or
              not r["trace"].get("clean") or
              not _valid_trace_verdict(r["trace"])):
            raise ValueError("invalid trace run")
        if r["build_kind"] == "broken" and (r["rc"] != 0 or
              not r.get("trace") or not r["trace"].get("clean") or
              not _valid_trace_verdict(r["trace"]) or
              not r["trace"].get("break")):
            raise ValueError("invalid broken trace run")
    if 0 in failed:
        raise ValueError("stock trace cycle invalidates every throughput ratio")
    ratios = {cell: {str(k): [] for k in ks if k != 0 and k not in failed}
              for cell in selected}
    rss = {cell: {str(k): [] for k in ks if k != 0 and k not in failed}
           for cell in selected}
    for j in expected_jobs:
        for round_index in range(j * 2, j * 2 + 2):
            for cell in selected:
                stock = by_key[j, round_index, cell, 0]
                if (not stock["perf_eligible"] or stock["rc"] != 0 or
                        not isinstance(stock["throughput"], (int, float)) or
                        not math.isfinite(stock["throughput"]) or stock["throughput"] <= 0):
                    raise ValueError("ineligible stock performance run")
                for k in ks:
                    if k == 0 or k in failed:
                        continue
                    r = by_key[j, round_index, cell, k]
                    if (not r.get("job_id") or r["job_id"] != stock.get("job_id") or
                            r.get("node") != stock.get("node")):
                        raise ValueError("K/stock pair crosses job or node")
                    if (not r["perf_eligible"] or r["rc"] != 0 or
                            not isinstance(r["throughput"], (int, float)) or
                            not math.isfinite(r["throughput"]) or r["throughput"] <= 0):
                        raise ValueError("ineligible performance run")
                    ratios[cell][str(k)].append({"job_index": j, "round": round_index,
                                                  "ratio": r["throughput"] / stock["throughput"]})
                    if r.get("maxrss_kb") is not None and stock.get("maxrss_kb") is not None:
                        rss[cell][str(k)].append(r["maxrss_kb"] - stock["maxrss_kb"])
    result_cells = {cell: {k: {"points": values,
       "median": statistics.median(v["ratio"] for v in values),
       "min": min(v["ratio"] for v in values), "max": max(v["ratio"] for v in values),
       "rss_delta_kb": rss[cell][k],
       "tuple_delta_bytes_for_1m": 1000000 * (
           by_key[0, 0, cell, int(k)]["tuple_size_bytes"] -
           by_key[0, 0, cell, 0]["tuple_size_bytes"])}
       for k, values in data.items()}
       for cell, data in ratios.items()}
    breaks = {r["build"] + ":" + r["cell"]: broken_verdict(r)
              for r in traces if r["build_kind"] == "broken"}
    count_rows = [{**r, "count_raw": r["count"],
                   "count": aggregate_count(r["count"], r["k"])} for r in counts]
    return {"schema": "vhash-hot-aggregate/v1", "pin": PIN, "cells": result_cells,
            "disqualified_ks": sorted(failed), "broken": breaks,
            "count": count_rows, "count_derived_definitions": COUNT_DERIVED,
            "trace": traces, "conditions": {"threads": 48,
            "tuples": 1000000, "zipf": 0.9, "max_ope": 10, "extime": 3},
            "interpretation": "exploratory same-time comparison of short YCSB transactions"}


def _manifest_path(output):
    return output / "manifest.json"


def _load_manifest(output):
    manifest = json.loads(_manifest_path(output).read_text())
    if manifest["pin"] != PIN:
        raise ValueError("manifest pin mismatch")
    return manifest


def _build_all(args):
    compute_only()
    head_probe = probe()
    policy = compute._load_policy(ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    toolchain = compute._resolve_toolchain(policy)
    scratch = args.scratch_root.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    deps = compute._prepare_dependencies(ROOT, policy, args.third_party_cache, scratch, toolchain)
    manifest = {"schema": "vhash-hot-manifest/v1", "pin": PIN,
                "node": socket.gethostname(), "pbs_job_id": os.environ.get("PBS_JOBID"),
                "started": now(), "job_probe": head_probe, "builds": {},
                "dependency_build_seconds": None, "inert": None,
                "sharing": {"mode": "requires shared path and dependency hashes"}}
    specs = build_specs()
    with patchharness.checkout(PIN) as source_name:
        source = Path(source_name)
        dependency = {"trace": 0, "kind": "dependency", "k": 0, "macros": {}, "patches": []}
        dep = _build_one(source, scratch / "build-dependency", dependency, deps, toolchain)
        manifest["dependency_build_seconds"] = dep["seconds"]
        manifest["inert"] = inert_receipt(source, scratch / "build-dependency")
    for name, spec in specs.items():
        with patchharness.checkout(PIN) as source_name:
            source = Path(source_name)
            strict_patches(source, spec["patches"])
            entry = _build_one(source, scratch / ("build-" + name), spec, deps, toolchain)
            binary = args.output / "bin" / name
            binary.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry["path"], binary)
            entry["path"] = str(binary.resolve())
            entry["sha256"] = sha(binary)
            entry["runtime_dependencies"] = runtime_dependencies(binary)
            manifest["builds"][name] = entry
            write_json(_manifest_path(args.output), manifest)
    manifest["ended"] = now()
    write_json(_manifest_path(args.output), manifest)
    return manifest


def _run_job(args):
    compute_only()
    job_probe = probe()
    manifest = _load_manifest(args.output)
    if args.command == "perf":
        selection = json.loads(args.selection.read_text())["selection"] if args.selection else None
        specs = plan_perf(args.job_index, rounds=selection["rounds"] if selection else 6,
                          cells=selection["cells"] if selection else None,
                          ks=tuple(selection["ks"]) if selection else KS)
    elif args.command == "count":
        selection = json.loads(args.selection.read_text())["selection"] if args.selection else None
        specs = plan_count(tuple(selection["ks"]) if selection else KS)
    elif args.command == "trace":
        selection = json.loads(args.selection.read_text())["selection"] if args.selection else None
        specs = plan_trace(args.job_index, tuple(selection["ks"]) if selection else KS)
    else:
        specs = [{"cell": cell, "k": k, "round": 0, "order_index": i,
                  "build": f"perf-k{k}"}
                 for cell in ("ro95-gc100000", "rr5") for i, k in enumerate(KS)]
        specs += [{"cell": "T1", "k": 8, "round": 0, "order_index": 0,
                   "build": "trace-k8"}]
    if not specs:
        raise ValueError("job index has no rounds in selected budget")
    required_builds = (set(manifest["builds"]) if args.command == "smoke" else
                       {s["build"] for s in specs})
    sharing_reason = sharing_preflight(manifest, required_builds)
    job = {"schema": "vhash-hot-job/v1", "command": args.command,
           "job_index": args.job_index, "job_id": os.environ.get("PBS_JOBID") or
           socket.gethostname() + ":" + now(), "node": socket.gethostname(),
           "started": now(), "job_probe": job_probe, "records": [],
           "build_sharing": {"mode": "unavailable" if sharing_reason else "shared-verified",
                             "reason": sharing_reason}}
    if sharing_reason:
        job["failure"] = sharing_reason
        args.output.mkdir(parents=True, exist_ok=True)
        write_json(args.output / f"raw-{args.command}-{args.job_index or 0}.json", job)
        if args.command == "smoke":
            job["smoke_seconds"] = time.monotonic() - args._smoke_tick
            job["build_seconds"] = args._build_seconds
            write_json(args.output / "smoke.json", job)
        raise RuntimeError(sharing_reason)
    manifest["job_id"] = job["job_id"]
    scratch = args.scratch_root.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        if spec["build"].startswith("trace-") or spec["build"].startswith("broken-"):
            with patchharness.checkout(PIN) as source_name:
                source = Path(source_name)
                entry = manifest["builds"][spec["build"]]
                order = entry["patch_order"]
                if len(order) != len(set(order)) or set(order) != set(entry["patch_sha256"]):
                    raise ValueError("manifest patch order/hash mismatch")
                if any(sha(ROOT / patch) != entry["patch_sha256"][patch] for patch in order):
                    raise ValueError("manifest patch sha256 mismatch")
                strict_patches(source, order)
                job["records"].append(run_one(manifest, spec, scratch=scratch, source=source))
        else:
            job["records"].append(run_one(manifest, spec, scratch=scratch))
        write_json(args.output / f"raw-{args.command}-{args.job_index or 0}.json", job)
    job["ended"] = now()
    if args.command == "smoke":
        job["smoke_seconds"] = time.monotonic() - args._smoke_tick
        job["build_seconds"] = args._build_seconds
        job["max_perf_run_seconds"] = max(r["elapsed_seconds"] for r in job["records"]
                                          if r["build_kind"] == "perf")
        job["trace_run_verify_seconds"] = max(r["elapsed_seconds"] + r["trace"]["seconds"]
                                               for r in job["records"] if r["build_kind"] == "trace")
        write_json(args.output / "smoke.json", job)
    write_json(args.output / f"raw-{args.command}-{args.job_index or 0}.json", job)
    return job


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "smoke", "perf", "count", "trace", "aggregate", "estimate"))
    parser.add_argument("--job-index", type=int)
    parser.add_argument("--third-party-cache", type=Path)
    parser.add_argument("--scratch-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--raw", type=Path, nargs="+")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--smoke", type=Path)
    parser.add_argument("--selection", type=Path)
    args = parser.parse_args(argv)
    if args.command == "estimate":
        if args.smoke is None:
            parser.error("estimate requires --smoke")
        print(json.dumps(estimate(json.loads(args.smoke.read_text())), indent=2))
        return 0
    if args.command == "aggregate":
        if not args.raw or not args.out:
            parser.error("aggregate requires --raw and --out")
        jobs = [json.loads(path.read_text()) for path in args.raw]
        selection = json.loads(args.selection.read_text())["selection"] if args.selection else None
        write_json(args.out / "aggregate.json", aggregate_jobs(jobs,
            rounds=selection["rounds"] if selection else 6,
            cells=selection["cells"] if selection else None,
            ks=tuple(selection["ks"]) if selection else KS))
        return 0
    if not all((args.third_party_cache, args.scratch_root, args.output)):
        parser.error("compute jobs require --third-party-cache, --scratch-root, --output")
    if args.command == "perf" and args.job_index not in (0, 1, 2):
        parser.error("perf requires --job-index 0, 1, or 2")
    if args.command == "trace" and args.job_index not in (0, 1):
        parser.error("trace requires --job-index 0 or 1")
    if args.command == "build":
        _build_all(args)
    elif args.command == "smoke":
        args._smoke_tick = time.monotonic()
        built = _build_all(args)
        args._build_seconds = sum(entry["seconds"] for entry in built["builds"].values()) + \
                              built["dependency_build_seconds"]
        _run_job(args)
    else:
        _run_job(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
