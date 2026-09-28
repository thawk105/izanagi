#!/usr/bin/env python3
"""One shard of the isolated VHash layout experiment (Python 3.9 compatible)."""
import argparse
import datetime
import glob
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

SCHEMA = "izanagi-vhash-hot-block-microbench/v2"
READ_ARMS = ("linked_scattered", "linked_local", "contig_scalar", "contig_simd")
WRITE_ARMS = ("shift", "ring", "block", "linked_prepend")
KS = (1, 2, 3, 4, 8, 16)
DEPTHS = tuple(range(8)) + (8, 10, 12)
EVENTS = "cycles:u,instructions:u,cache-references:u,cache-misses:u,L1-dcache-load-misses:u,dTLB-load-misses:u,branch-misses:u"
FLAGS = ("-O3", "-DNDEBUG", "-std=c++20", "-Wall", "-Wextra", "-Werror",
         "-fno-tree-vectorize", "-mavx2", "-mbmi", "-mbmi2", "-mpopcnt")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def make_manifest():
    cells = []
    def add(group, side, k, depth, keyset, value_mode="none", value_bytes=0, state_pattern=None):
        parts = (group, str(k), str(depth), keyset, value_mode, str(value_bytes), str(state_pattern))
        cells.append(dict(cell_id="-".join(parts), group=group, side=side, K=k,
                          depth=depth, keyset=keyset, value_mode=value_mode,
                          value_bytes=value_bytes, state_pattern=state_pattern,
                          pilot_multiple=None))
    for k in KS:
        for depth in (0, k + 2):
            for keyset in ("in", "out"):
                add("k", "read", k, depth, keyset)
    for depth in DEPTHS:
        for keyset in ("in", "out"):
            add("depth", "read", 8, depth, keyset)
    for k in (3, 8):
        for keyset in ("in", "out"):
            for pattern in ("candidate_pending", "pending_newer_than_ts", "aborted_then_committed", "candidate_deleted"):
                add("state", "read", k, 1, keyset, state_pattern=pattern)
    for k in (3, 8):
        for depth in (0, k - 1):
            for keyset in ("in", "out"):
                for mode in ("external", "inline"):
                    for n in (16, 64, 256):
                        add("value", "read", k, depth, keyset, mode, n)
    for k in KS:
        for keyset in ("in", "out"):
            for mode, n in (("external", 64), ("inline", 16), ("inline", 256)):
                add("write", "write", k, None, keyset, mode, n)
    validate_manifest(cells)
    return cells


def make_pilot_manifest(llc_bytes, footprint, mem_bytes):
    cells = []
    for m in (.5, 1, 2, 4, 8):
        c = dict(cell_id="pilot-%s" % m, group="pilot", side="read", K=4,
                 depth=0, keyset="out", value_mode="none", value_bytes=0,
                 state_pattern=None, pilot_multiple=m)
        per_key = min(footprint(c, arm) for arm in ("linked_scattered", "contig_scalar"))
        n = max(64, (int(m * llc_bytes) + per_key - 1) // per_key)
        total = sum(footprint(c, arm) for arm in ("linked_scattered", "contig_scalar"))
        limit = mem_bytes // (2 * total)
        if limit < 64:
            raise RuntimeError("pilot memory cap cannot fit 64 keys")
        c["capped"] = n > limit
        c["n_keys"] = min(n, limit)
        cells.append(c)
    validate_manifest(cells)
    return cells


def validate_manifest(cells):
    seen = set()
    identities = set()
    for c in cells:
        identity = (c["group"], c["side"], c["K"], c["depth"], c["keyset"],
                    c["value_mode"], c["value_bytes"], c["state_pattern"],
                    c.get("pilot_multiple"))
        if c["cell_id"] in seen or identity in identities:
            raise ValueError("duplicate cell: " + c["cell_id"])
        seen.add(c["cell_id"])
        identities.add(identity)


def check_objdump(disassembly):
    sections = {}
    current = None
    for line in disassembly.splitlines():
        symbol = re.search(r"<([^>]+)>:\s*$", line)
        if symbol:
            current = symbol.group(1)
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line.lower())
    scalar = "\n".join(sections.get("select_contig_scalar", []))
    simd = "\n".join(sections.get("select_contig_simd", []))
    vector_ops = re.findall(r"\b(?:vpcmp\w*|v?movdqa\w*|v?movdqu\w*|v?movap\w*|v?movup\w*|vpmovmskb|vmovmskpd)\b|%[xy]mm\d+", scalar)
    cmp_ops = re.findall(r"\bvpcmpgtq\b", simd)
    mask_ops = re.findall(r"\b(?:vpmovmskb|vmovmskpd)\b", simd)
    return {"scalar_vector_ops": len(vector_ops), "simd_cmp_ops": len(cmp_ops),
            "simd_mask_ops": len(mask_ops), "passed": bool(scalar and simd and not vector_ops and cmp_ops and mask_ops)}


def run(argv, timeout=120, **kwargs):
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=timeout, check=False, **kwargs)


def cache_bytes(core):
    root = pathlib.Path("/sys/devices/system/cpu/cpu%d/cache" % core)
    l2 = llc = 0
    for index in root.glob("index*"):
        try:
            level = int((index / "level").read_text().strip())
            size = (index / "size").read_text().strip().upper()
            match = re.fullmatch(r"([0-9]+)([KMG])", size)
            if not match:
                continue
            n = int(match.group(1)) * {"K": 1024, "M": 1024**2, "G": 1024**3}[match.group(2)]
            if level == 2:
                l2 = max(l2, n)
            if level >= 3:
                llc = max(llc, n)
        except (OSError, ValueError):
            continue
    return l2, llc


def mem_available():
    match = re.search(r"^MemAvailable:\s*(\d+) kB", pathlib.Path("/proc/meminfo").read_text(), re.M)
    return int(match.group(1)) * 1024 if match else 0


def competitors():
    found = []
    own = os.getpid()
    ancestors = {own}
    parent = os.getppid()
    while parent > 1 and parent not in ancestors:
        ancestors.add(parent)
        try:
            status = (pathlib.Path("/proc") / str(parent) / "status").read_text()
            match = re.search(r"^PPid:\s*(\d+)", status, re.M)
            parent = int(match.group(1)) if match else 1
        except OSError:
            break
    for p in pathlib.Path("/proc").glob("[0-9]*"):
        try:
            if int(p.name) in ancestors or p.stat().st_uid != os.getuid():
                continue
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
            if "hot_block_bench" in cmd or "run_hot_block.py" in cmd:
                found.append({"pid": int(p.name), "cmd": cmd[:300]})
        except (OSError, ValueError):
            pass
    return found


def preflight(raw):
    compiler = shutil.which("g++-12")
    if not compiler:
        raise RuntimeError("g++-12 absent")
    version = run([compiler, "--version"])
    if version.returncode:
        raise RuntimeError("g++-12 --version failed")
    flags = pathlib.Path("/proc/cpuinfo").read_text()
    cpu = re.search(r"^model name\s*:\s*(.+)$", flags, re.M)
    cpu_flags = re.search(r"^flags\s*:\s*(.+)$", flags, re.M)
    flagset = set(cpu_flags.group(1).split()) if cpu_flags else set()
    if "avx2" not in flagset:
        raise RuntimeError("AVX2 absent")
    affinity = sorted(os.sched_getaffinity(0))
    if not affinity:
        raise RuntimeError("no available core")
    core = affinity[0]
    os.sched_setaffinity(0, {core})
    l2, llc = cache_bytes(core)
    if not l2 or not llc:
        raise RuntimeError("cache size absent")
    perf_candidates = sorted(set(glob.glob("/usr/lib/linux-tools/*/perf") +
                                 ([shutil.which("perf")] if shutil.which("perf") else [])), reverse=True)
    paranoid_path = pathlib.Path("/proc/sys/kernel/perf_event_paranoid")
    paranoid = int(paranoid_path.read_text().strip())
    competing = competitors()
    raw["env"] = {"python": sys.version, "python_path": sys.executable, "path": os.environ.get("PATH", ""),
                  "cpu_model": cpu.group(1) if cpu else "unknown", "avx2": True,
                  "avx512f": "avx512f" in flagset, "core": core, "l2_bytes": l2,
                  "llc_bytes": llc, "mem_available_bytes": mem_available(),
                  "perf_path": "", "perf_candidates_tried": [], "perf_event_paranoid": paranoid,
                  "perf_control_ok": False, "perf_known_work_ratio": None,
                  "single_tenant": {"ok": not competing, "competitors": competing}}
    if competing:
        raise RuntimeError("competing same-user benchmark process")
    return compiler, version.stdout.strip().splitlines()[0]


def footprint_per_key(binary, c, arm):
    argv = [str(binary), "--footprint", json.dumps(c, separators=(",", ":")), "--arm", arm]
    result = run(argv, timeout=30)
    if result.returncode:
        raise RuntimeError("footprint failed: " + result.stderr[:500])
    value = json.loads(result.stdout)["footprint_per_key_bytes"]
    if not isinstance(value, int) or value <= 0:
        raise RuntimeError("invalid footprint")
    return value


def set_key_count(binary, c, env, multiple):
    arms = READ_ARMS if c["side"] == "read" else WRITE_ARMS
    footprints = [footprint_per_key(binary, c, a) for a in arms]
    if c["keyset"] == "in":
        n = max(64, env["l2_bytes"] // (2 * max(footprints)))
    else:
        n = max(64, (int(multiple * env["llc_bytes"]) + min(footprints) - 1) // min(footprints))
    limit = env["mem_available_bytes"] // (2 * sum(footprints))
    if limit < 64:
        raise RuntimeError("memory cap cannot fit 64 keys: " + c["cell_id"])
    capped = n > limit
    n = min(n, limit)
    c["n_keys"] = n
    c["capped"] = capped


def latin_order(arms, rep):
    return tuple(arms[(rep + j) % 4] for j in range(4))


def invoke_cell(binary, c, arms, reps, ops=None, control=None, ack=None):
    argv = [str(binary), "--cell", json.dumps(c, separators=(",", ":")),
            "--arms", ",".join(arms), "--reps", str(reps)]
    if ops is not None:
        argv += ["--ops", str(ops)]
    if control:
        argv += ["--perf-ctl-fifo", control, "--perf-ack-fifo", ack]
    result = run(argv, timeout=300)
    if result.returncode:
        raise RuntimeError("cell failed: " + result.stderr[:500] + result.stdout[:500])
    return json.loads(result.stdout)


def parse_perf_csv(stderr, requested):
    events = {}
    for line in stderr.splitlines():
        fields = [x.strip() for x in line.split(",")]
        if len(fields) < 5 or fields[2] not in requested:
            continue
        try:
            count = float(fields[0].replace(" ", ""))
            run_time_ns = int(float(fields[3]))
            running_pct = float(fields[4].rstrip("%"))
        except (ValueError, OverflowError):
            continue
        if not (math.isfinite(count) and count >= 0 and run_time_ns > 0 and
                math.isfinite(running_pct) and 99.5 <= running_pct <= 100.0):
            raise RuntimeError("perf event multiplexed or invalid: " + fields[2])
        if fields[2] in events:
            raise RuntimeError("duplicate perf event: " + fields[2])
        events[fields[2]] = dict(count=count, run_time_ns=run_time_ns,
                                 running_pct=running_pct)
    if set(events) != set(requested):
        raise RuntimeError("perf events missing: " + ",".join(sorted(set(requested) - set(events))))
    return events


def perf_measure(perf, binary, c, arm, ops, raw_dir, tag, save=True):
    groups = (EVENTS.split(",")[:4], EVENTS.split(",")[4:])
    events, paths = {}, []
    for group_no, group in enumerate(groups):
        with tempfile.TemporaryDirectory(prefix="vhash-perf-") as local:
            control, ack = (str(pathlib.Path(local) / suffix) for suffix in ("ctl", "ack"))
            os.mkfifo(control)
            os.mkfifo(ack)
            argv = [perf, "stat", "-x", ",", "-D", "-1", "--control",
                    "fifo:%s,%s" % (control, ack), "-e", ",".join(group), "--",
                    str(binary), "--cell", json.dumps(c, separators=(",", ":")),
                    "--arms", arm, "--reps", "1", "--ops", str(ops),
                    "--perf-ctl-fifo", control, "--perf-ack-fifo", ack]
            result = run(argv, timeout=300)
        if save:
            stderr_path = raw_dir / (tag + "-group%d.perf.txt" % group_no)
            stderr_path.write_text(result.stderr)
            paths.append(str(stderr_path))
        if result.returncode:
            raise RuntimeError("perf control failed: " + result.stderr[-500:])
        events.update(parse_perf_csv(result.stderr, group))
    return {"ops": ops, "events": events, "raw_stderr_paths": paths}


def select_perf(raw, binary, raw_dir):
    smoke = dict(K=4, depth=0, n_keys=64, side="read", value_mode="none",
                 value_bytes=0, state_pattern=None)
    candidates = sorted(set(glob.glob("/usr/lib/linux-tools/*/perf") +
                            ([shutil.which("perf")] if shutil.which("perf") else [])), reverse=True)
    for candidate in candidates:
        try:
            first = perf_measure(candidate, binary, smoke, "contig_scalar", 200000,
                                 raw_dir, "smoke", save=False)
            second = perf_measure(candidate, binary, smoke, "contig_scalar", 400000,
                                  raw_dir, "smoke", save=False)
            ratio = second["events"]["instructions:u"]["count"] / first["events"]["instructions:u"]["count"]
            if not 1.8 <= ratio <= 2.2:
                raise RuntimeError("known-work ratio outside 1.8..2.2")
            raw["env"]["perf_candidates_tried"].append(candidate + ": passed")
            raw["env"]["perf_path"] = candidate
            raw["env"]["perf_known_work_ratio"] = ratio
            raw["env"]["perf_control_ok"] = True
            return candidate
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            raw["env"]["perf_candidates_tried"].append(candidate + ": " + str(exc)[:200])
    raise RuntimeError("no perf candidate passed smoke")


def build(raw, compiler, version, directory):
    source = pathlib.Path(__file__).with_name("hot_block_bench.cc")
    binary = directory / "hot_block_bench"
    argv = [compiler] + list(FLAGS) + [str(source), "-o", str(binary)]
    p = run(argv, timeout=120)
    if p.returncode:
        raise RuntimeError("build failed: " + p.stderr[-2000:])
    dis = run(["objdump", "-drC", str(binary)])
    check = check_objdump(dis.stdout)
    raw["build"] = {"compiler_path": compiler, "compiler_version": version, "argv": argv,
                    "binary_sha256": sha256(binary), "objdump_check": check}
    if dis.returncode or not check["passed"]:
        raise RuntimeError("objdump check failed")
    p = run([str(binary), "--selfcheck"], timeout=30)
    raw["selfcheck"] = json.loads(p.stdout) if p.stdout else {"passed": False, "stderr": p.stderr}
    if p.returncode or not raw["selfcheck"]["passed"]:
        raise RuntimeError("selfcheck failed")
    return binary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", required=True, choices=("pilot", "read-k", "read-depth-state", "read-value", "write"))
    ap.add_argument("--raw-root", required=True)
    ap.add_argument("--pilot-raw")
    ap.add_argument("--max-wall-s", type=float, default=2400.0)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.raw_root)
    if not root.is_absolute():
        ap.error("--raw-root must be absolute")
    if args.shard != "pilot" and (not args.pilot_raw or not pathlib.Path(args.pilot_raw).is_absolute()):
        ap.error("non-pilot shard needs --pilot-raw with an absolute path")
    if not 0 < args.max_wall_s < float("inf"):
        ap.error("--max-wall-s must be finite and positive")
    root.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    source = pathlib.Path(__file__).with_name("hot_block_bench.cc")
    repo = pathlib.Path(__file__).resolve().parents[2]
    head = run(["git", "rev-parse", "HEAD"], cwd=str(repo))
    raw = {"schema": SCHEMA, "run_id": run_id, "shard": args.shard,
           "host": socket.gethostname(),
           "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "source": {"bench_cc_sha256": sha256(source), "driver_sha256": sha256(__file__),
                      "repo_head": head.stdout.strip() if head.returncode == 0 else None},
           "build": {}, "env": {}, "selfcheck": {}, "keyset_multiple": None,
           "pilot_ref": None, "cells": []}
    outfile = root / (run_id + ".json")
    try:
        if re.fullmatch(r"pegasus0[0-9]+", raw["host"]):
            raise RuntimeError("timed benchmark requires a compute node")
        if args.shard != "pilot":
            pilot = json.loads(pathlib.Path(args.pilot_raw).read_text())
            multiple = pilot.get("keyset_multiple")
            if ("failure" in pilot or pilot.get("schema") != SCHEMA or
                    pilot.get("shard") != "pilot" or not isinstance(pilot.get("run_id"), str) or
                    not isinstance(multiple, (int, float)) or isinstance(multiple, bool) or
                    not 0 < multiple < float("inf")):
                raise RuntimeError("invalid pilot raw")
            raw["keyset_multiple"] = multiple
            raw["pilot_ref"] = pilot["run_id"]
        compiler, version = preflight(raw)
        with tempfile.TemporaryDirectory(prefix="vhash-hot-block-") as tmp:
            binary = build(raw, compiler, version, pathlib.Path(tmp))
            select_perf(raw, binary, root)
            groups = {"read-k": ("k",), "read-depth-state": ("depth", "state"),
                      "read-value": ("value",), "write": ("write",)}
            manifest = [c for c in make_manifest() if c["group"] in groups.get(args.shard, ())]
            if args.shard == "pilot":
                manifest = make_pilot_manifest(raw["env"]["llc_bytes"],
                    lambda c, a: footprint_per_key(binary, c, a), raw["env"]["mem_available_bytes"])
            else:
                for c in manifest:
                    set_key_count(binary, c, raw["env"], raw["keyset_multiple"])
            for c in manifest:
                if time.monotonic() - started > args.max_wall_s:
                    raise RuntimeError("shard max-wall-s exceeded before " + c["cell_id"])
                cell_started = time.monotonic()
                arms = (("linked_scattered", "contig_scalar") if args.shard == "pilot" else
                        (READ_ARMS if c["side"] == "read" else WRITE_ARMS))
                bench_cell = dict(c, memory_limit_bytes=raw["env"]["mem_available_bytes"] // 2)
                result = invoke_cell(binary, bench_cell, arms, 8)
                c["ops"] = result["ops"]
                c["expected_checksum"] = result["expected_checksum"]
                c["shared_value_pool_bytes"] = result["shared_value_pool_bytes"]
                c["arms"] = result["arms"]
                expected_shared = (c["n_keys"] * max(c["K"] + 4, (c["depth"] or 0) + 2)
                                   * c["value_bytes"] if c["side"] == "read" and
                                   c["value_mode"] == "external" else 0)
                if c["shared_value_pool_bytes"] != expected_shared:
                    raise RuntimeError("shared value pool mismatch: " + c["cell_id"])
                for arm_result in c["arms"]:
                    arm = arm_result["arm"]
                    expected_size = footprint_per_key(binary, c, arm)
                    if (arm_result["footprint_per_key_bytes"] != expected_size or
                            arm_result["footprint_bytes"] != expected_size * c["n_keys"]):
                        raise RuntimeError("footprint mismatch: " + c["cell_id"] + ":" + arm)
                    if len(arm_result["reps"]) != 8 or any(rep["checksum"] != c["expected_checksum"]
                            for rep in arm_result["reps"]):
                        raise RuntimeError("checksum mismatch: " + c["cell_id"] + ":" + arm)
                    tag = run_id + "-" + c["cell_id"].replace("/", "_") + "-" + arm
                    arm_result["perf"] = perf_measure(raw["env"]["perf_path"], binary, c,
                        arm, c["ops"], root, tag)
                c["wall_s"] = time.monotonic() - cell_started
                raw["cells"].append(c)
            if args.shard == "pilot":
                chosen = 8.0
                for prior, current in zip(raw["cells"], raw["cells"][1:]):
                    ratios = []
                    for a, b in zip(prior["arms"], current["arms"]):
                        x = sorted(r["ns_per_op"] for r in a["reps"])[4]
                        y = sorted(r["ns_per_op"] for r in b["reps"])[4]
                        ratios.append(abs(y - x) / x)
                    if all(r <= .05 for r in ratios):
                        chosen = current["pilot_multiple"]
                        break
                raw["keyset_multiple"] = chosen
                pilot_seconds = sum(c["wall_s"] for c in raw["cells"])
                counts = {"read-k": 24, "read-depth-state": 38,
                          "read-value": 48, "write": 36}
                per_cell = pilot_seconds / len(raw["cells"])
                raw["estimate"] = {"formula": "sum(pilot cell wall_s)/5 * shard cell count",
                                   "pilot_cell_mean_s": per_cell,
                                   "shard_wall_s": {k: per_cell * v for k, v in counts.items()},
                                   "total_node_hours": per_cell * sum(counts.values()) / 3600}
    except Exception as exc:
        raw["failure"] = str(exc)
    raw["wall_s"] = time.monotonic() - started
    raw["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    outfile.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    if "failure" in raw:
        print(raw["failure"], file=sys.stderr)
        return 1
    print(outfile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
