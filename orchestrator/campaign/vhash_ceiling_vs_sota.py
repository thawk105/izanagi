#!/usr/bin/env python3
"""Paired Cicada ceiling experiment. All measurement jobs run on one isolated node."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import uuid

from . import vhash_ro_gc_publish as base
from . import vhash_cicada_vlife as V
from . import condition_meaning_gate as condition
from . import site_policy
from .materializer_admission import non_admissible_materializer
from .p2_2 import _assert_single_tenant

ROOT = base.ROOT
PIN = base.PIN
DRIVER_ID = "orchestrator.campaign.vhash_ceiling_vs_sota"
MATERIALIZER = DRIVER_ID + "._build_variant"
PATCH = ROOT / "patches"
V_PATCH = PATCH / "cicada-ro-gcflag-variant.patch"
W_PATCH = PATCH / "cicada-ceiling-workload.patch"
TRACE = PATCH / "instr-cicada-trace.patch"
VLIFE = PATCH / "instr-cicada-version-lifetime.patch"
HOT = (PATCH / "cicada-vhash-hot-block-variant.patch",
       PATCH / "cicada-vhash-hot-block-post.patch")
FWD = PATCH / "cicada-forwarding-variant.patch"
IGC = PATCH / "cicada-interval-gc-variant.patch"
BROKEN = PATCH / "broken-cicada-interval-gc-overprune.patch"
HOT_COUNT = PATCH / "cicada-vhash-hot-block-count-v2.patch"
WORKLOAD_PREFIX = "IZANAGI_CICADA_CEILING_WORKLOAD_V1 "
WORKLOAD_FIELDS = {"schema", "thread_num", "batch_threads", "batch_ops", "ronly_pct",
                   "normal_commits", "batch_commits"}
POINTS = {
    "P1": {"rr": 5, "ro": 0, "workers": 47, "batch": 1, "skew": 0.6},
    "P2": {"rr": 5, "ro": 0, "workers": 47, "batch": 1, "skew": 0.9},
    "P3": {"rr": 5, "ro": 0, "workers": 47, "batch": 1, "skew": 0.97},
    "P4": {"rr": 50, "ro": 95, "workers": 12, "batch": 0, "skew": 0.9},
    "P4prime": {"rr": 50, "ro": 95, "workers": 12, "batch": 0, "skew": 0.97},
}
M_ARMS = ("hot1", "hot8", "fwd")
ARMS = ("S", "R", "R-noLR", "hot1", "hot8", "fwd", "igc1", "igc3")
TREES = ("base", "hot", "fwd", "igc", "diag-base", "diag-hot", "diag-fwd",
         "diag-igc", "trace-base", "trace-hot", "trace-fwd", "trace-igc",
         "trace-igc-broken")
TREE_PATCHES = {
    "base": (V_PATCH, W_PATCH),
    "hot": (V_PATCH, *HOT, W_PATCH),
    "fwd": (V_PATCH, FWD, W_PATCH),
    "igc": (V_PATCH, IGC, W_PATCH),
    "diag-base": (VLIFE, V_PATCH, W_PATCH),
    "diag-hot": (V_PATCH, *HOT, HOT_COUNT, W_PATCH),
    "diag-fwd": (V_PATCH, FWD, W_PATCH),
    "diag-igc": (V_PATCH, IGC, W_PATCH),
    "trace-base": (TRACE, V_PATCH, W_PATCH),
    "trace-hot": (TRACE, V_PATCH, *HOT, HOT_COUNT, W_PATCH),
    "trace-fwd": (TRACE, V_PATCH, FWD, W_PATCH),
    "trace-igc": (TRACE, V_PATCH, IGC, W_PATCH),
    "trace-igc-broken": (TRACE, V_PATCH, IGC, W_PATCH, BROKEN),
}


def variants(tree: str) -> dict[str, tuple[str, ...]]:
    w = ("IZANAGI_CICADA_CEILING_WORKLOAD",)
    r = w + ("IZANAGI_CICADA_RO_GCFLAG",)
    if tree.endswith("base") or tree == "base":
        suffix = ("IZANAGI_CICADA_VLIFE",) if tree == "diag-base" else ()
        prefix = ("TRACE", "IZANAGI_CICADA_RO_GCFLAG_COUNT") if tree == "trace-base" else ()
        diag_count = ("IZANAGI_CICADA_RO_GCFLAG_COUNT",) if tree == "diag-base" else ()
        return {"S": w + suffix + (("TRACE",) if tree == "trace-base" else ()),
                "R": r + suffix + diag_count + prefix}
    if "hot" in tree:
        count = ("CICADA_VHASH_COUNT",) if tree.startswith(("diag", "trace")) else ()
        trace = ("TRACE", "IZANAGI_CICADA_RO_GCFLAG_COUNT") if tree.startswith("trace") else ()
        return {f"hot{k}": r + (f"CICADA_VHASH_K={k}",) + count + trace for k in (1, 8)}
    if "fwd" in tree:
        count = ("CICADA_FWD_COUNT",) if tree.startswith(("diag", "trace")) else ()
        trace = ("TRACE", "IZANAGI_CICADA_RO_GCFLAG_COUNT") if tree.startswith("trace") else ()
        return {"fwd": r + ("CICADA_FWD_ENABLE",) + count + trace}
    count = ("CICADA_INTERVAL_COUNT",) if tree.startswith(("diag", "trace")) else ()
    trace = ("TRACE", "IZANAGI_CICADA_RO_GCFLAG_COUNT") if tree.startswith("trace") else ()
    return {"igc": r + ("CICADA_INTERVAL_GC",) + count + trace}


def _definitions(row: dict) -> dict[str, str]:
    argv = row.get("arguments") or shlex.split(row["command"])
    result = {}
    for i, token in enumerate(argv):
        if token == "-D":
            token = "-D" + argv[i + 1]
        if token.startswith("-D") and token != "-D":
            key, _, value = token[2:].partition("=")
            if key in result and result[key] != (value or "1"):
                raise ValueError("conflicting compile definitions")
            result[key] = value or "1"
    return result


def expected_perf_defines(arm: str) -> dict[str, str]:
    tree = {"S": "base", "R": "base", "R-noLR": "base", "hot1": "hot",
            "hot8": "hot", "fwd": "fwd", "igc1": "igc", "igc3": "igc"}[arm]
    key = "R" if arm == "R-noLR" else "igc" if arm.startswith("igc") else arm
    result = {"ADD_ANALYSIS": "0", "BACK_OFF": "0", "KEY_SIZE": "8",
              "BOOST_ALL_NO_LIB": "1", "BOOST_FILESYSTEM_DYN_LINK": "1",
              "MASSTREE_USE": "1", "VAL_SIZE": "4", "TRACE": "0",
              "INLINE_VERSION_OPT": "1", "INLINE_VERSION_PROMOTION": "0",
              "REUSE_VERSION": "1", "SINGLE_EXEC": "0", "WRITE_LATEST_ONLY": "0",
              "WORKER1_INSERT_DELAY_RPHASE": "0", "PARTITION_TABLE": "0",
              "Linux": "1", "NDEBUG": "1"}
    for macro in variants(tree)[key]:
        name, _, value = macro.partition("=")
        result[name] = value or "1"
    return result


def check_perf_defines(commands: list[dict], arm: str) -> None:  # M1
    expected = expected_perf_defines(arm)
    expected.update({axis: str(value) for axis, value in V.TUNED_GENOME.items()})
    rows = [row for row in commands if "CMakeFiles/ycsb_cicada.exe.dir/" in
            (row.get("command") or " ".join(row.get("arguments", [])))]
    if len(rows) != 3 or {Path(row["file"]).name for row in rows} != {
            "transaction.cc", "util.cc", "ycsb_cicada.cc"}:
        raise ValueError("incomplete Cicada compile commands")
    for row in rows:
        actual = _definitions(row)
        if actual != expected:
            raise ValueError(f"perf -D mismatch: {actual} != {expected}")


def parse_workload(stdout: str, flags: dict | None = None) -> dict:
    row = base.parse_line(stdout, WORKLOAD_PREFIX, WORKLOAD_FIELDS)
    if row["ronly_pct"] > 100 or row["batch_threads"] > 1 or row["batch_ops"] != 1000:
        raise ValueError("workload field out of range")
    if flags is not None:
        expected = {"thread_num": "thread_num", "batch_threads": "batch_th_num",
                    "batch_ops": "batch_max_ope", "ronly_pct": "izanagi_ceiling_ronly_pct"}
        if any(row[key] != int(flags[flag]) for key, flag in expected.items()):
            raise ValueError("workload flags disagree with run")
    return row


def patch_manifest(tree: str) -> list[dict]:
    check_patch_order(tree)
    return [{"name": path.name, "sha256": base.sha(path)} for path in TREE_PATCHES[tree]]


def check_patch_order(tree: str) -> None:  # M18
    patches = TREE_PATCHES[tree]
    if tree in ("diag-hot", "trace-hot") and not (
            patches.index(HOT_COUNT) < patches.index(W_PATCH)):
        raise ValueError("hot count patch must precede ceiling workload patch")


def _gates(source: Path, macros: tuple[str, ...], args: list[str], cxx: str) -> list[dict]:
    records = []
    for macro in macros:
        if macro == "TRACE":
            continue
        name = macro.partition("=")[0]
        captured = condition.capture_define_inputs(source, configure_args=tuple(args))
        requested = int(macro.partition("=")[2] or "1")
        request = condition.make_define_request(
            driver_id=DRIVER_ID, macro=name, requested_value=requested, default_value=0)
        with condition._configured_define_compile_commands(
                captured, request=request, cxx=cxx, cmake="cmake") as commands:
            supply = condition.evaluate_define_supply_effectuation(
                captured, request=request, cxx=cxx, cmake="cmake",
                configured_commands=commands)
            meaning = condition.evaluate_define_runtime_meaning(
                captured, request=request,
                declaration=condition.declare_define_runtime_meaning(request),
                cxx=cxx, cmake="cmake", configured_commands=commands)
        admission = condition.require_condition_gate_family(
            [supply], [meaning], use_class="raw-measurement")
        records.append({"macro": name, "supply": json.loads(supply.canonical_json()),
                        "meaning": json.loads(meaning.canonical_json()),
                        "admission": json.loads(admission.canonical_json())})
        if not admission.admitted:
            raise RuntimeError(f"condition gate rejected {name}")
    return records


def check_manifest(manifest: dict, binary: Path, tree: str, arm: str) -> None:  # M8
    expected = {"schema": 1, "pin": PIN, "tree": tree, "arm": arm,
                "patches": patch_manifest(tree), "macros": list(variants(tree)[arm]),
                "binary_sha256": base.sha(binary)}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("manifest provenance mismatch")
    for key in ("compile_commands_sha256", "compiler_version_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get(key, ""))):
            raise ValueError(f"invalid manifest {key}")


def _build_variant(source: Path, build: Path, genome: str, macros: tuple[str, ...],
                   *, trace: bool, toolchain: dict, dependencies: dict,
                   arm: str | None = None) -> tuple[Path, dict]:
    non_admissible_materializer(MATERIALIZER)
    started = time.monotonic()
    args = V.compute._common_configure_args(trace=int(trace), toolchain=toolchain,
                                            dependencies=dependencies)
    args = [arg for arg in args if arg not in V.compute.STOCK_G.cmake_defines()]
    args += ["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", *V.genome_args(genome)]
    gates = _gates(source, macros, args, toolchain["cxx_path"])
    args.append("-DCMAKE_CXX_FLAGS=" + " ".join("-D" + (m if "=" in m else m + "=1")
                                            for m in macros if m != "TRACE"))
    configure = ["cmake", "-S", str(source), "-B", str(build),
                 "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args]
    base._checked(configure)
    witness = V.verify_genome_commands(build / "compile_commands.json", genome)
    commands = json.loads((build / "compile_commands.json").read_text())
    if arm is not None and not trace and "VLIFE" not in " ".join(macros):
        check_perf_defines(commands, arm)
    base._checked(["cmake", "--build", str(build), "--target", "ycsb_cicada.exe"])
    binary = build / "cc/cicada/ycsb_cicada.exe"
    if not binary.is_file():
        raise RuntimeError("Cicada binary missing")
    return binary, {"gates": gates, "genome": witness, "elapsed_s": time.monotonic()-started,
                    "compile_commands_sha256": base.sha(build / "compile_commands.json"),
                    "compiler_version_sha256": hashlib.sha256(base._checked(
                        [toolchain["cxx_path"], "--version"]).stdout.encode()).hexdigest()}


def flags(point: str, arm: str, gc: int, extime: int, records: int = 1_000_000) -> dict:
    p = POINTS[point]
    result = {"tuple_num": records, "ycsb_tuple_num": records,
              "thread_num": p["workers"], "batch_th_num": 0 if arm == "R-noLR" else p["batch"],
              "batch_max_ope": 1000, "max_ope": 10, "ycsb_max_ope": 10,
              "rratio": p["rr"], "ycsb_rratio": p["rr"],
              "zipf_skew": p["skew"], "ycsb_zipf_skew": p["skew"],
              "gc_inter_us": gc, "izanagi_ceiling_ronly_pct": p["ro"],
              "extime": extime, "clocks_per_us": 2100, "group_commit": 0}
    if arm == "fwd":
        result.update(cicada_fwd_k=1, cicada_fwd_policy="c")
    if arm.startswith("igc"):
        result["cicada_igc_debug_mode"] = 1 if arm == "igc-broken" else int(arm[-1])  # M13
    return result


def arm_order(arms: tuple[str, ...], round_no: int) -> tuple[str, ...]:  # M9
    if round_no < 1:
        raise ValueError("round must be positive")
    rotated = arms[(round_no-1) % len(arms):] + arms[:(round_no-1) % len(arms)]
    return tuple(reversed(rotated)) if round_no % 2 == 0 else rotated


def _build_for_arm(arm: str, purpose: str = "perf") -> tuple[str, str]:
    tree = "hot" if arm.startswith("hot") else "fwd" if arm == "fwd" else "igc" if arm.startswith("igc") else "base"
    key = "igc" if arm.startswith("igc") else "R" if arm == "R-noLR" else arm
    return (tree if purpose == "perf" else purpose + "-" + tree, key)


def _load_binary(bin_dir: Path, tree: str, arm: str, local: Path) -> tuple[Path, dict]:
    src = bin_dir / f"{tree}-{arm}.exe"
    manifest = json.loads((bin_dir / f"{tree}-{arm}.manifest.json").read_text())
    local.mkdir(parents=True, exist_ok=True)
    dst = local / src.name
    shutil.copy2(src, dst)
    check_manifest(manifest, dst, tree, arm)
    commands_src = bin_dir / f"{tree}-{arm}.compile_commands.json"
    commands_dst = local / commands_src.name
    shutil.copy2(commands_src, commands_dst)
    if base.sha(commands_dst) != manifest["compile_commands_sha256"]:
        raise ValueError("compile commands SHA mismatch")
    compiler = manifest.get("compiler_path")
    if not compiler or hashlib.sha256(base._checked([compiler, "--version"]).stdout.encode()).hexdigest() != \
            manifest["compiler_version_sha256"]:
        raise ValueError("compiler version SHA mismatch")
    if tree in ("base", "hot", "fwd", "igc"):
        check_perf_defines(json.loads(commands_dst.read_text()), arm)
    return dst, manifest


def _processes() -> list[dict]:
    result = base._checked(["ps", "-eo", "user=,args="]).stdout
    return [{"user": line.split(None, 1)[0], "cmdline": line.split(None, 1)[1]}
            for line in result.splitlines() if len(line.split(None, 1)) == 2]


def _run_one(binary: Path, run_flags: dict, scratch: Path, trace_dir: Path | None = None) -> dict:
    _assert_single_tenant()
    return base._run(binary, run_flags, cwd=scratch, trace_dir=trace_dir)


def _record(run: dict, *, mode: str, point: str, arm: str, gc: int, round_no: int,
            order: int, job_id: str, processes: list, manifest: dict, flags_used: dict,
            run_id: str) -> dict:
    if run["rc"]:
        raise RuntimeError(f"benchmark rc={run['rc']}: {run['stderr'][-1000:]}")
    tree = manifest["tree"]
    if mode in ("prelim", "compare", "rtune") and tree.startswith(("diag", "trace")):
        raise ValueError("instrumented build in performance data")
    workload = parse_workload(run["stdout"], flags_used)
    if point in ("P1", "P2", "P3") and arm != "R-noLR" and workload["batch_commits"] == 0:
        raise ValueError("long reader did not complete")
    return {"schema": 1, "mode": mode, "command": run["argv"], "point": point,
            "gc_inter_us": gc, "arm": arm, "round": round_no, "order": order,
            "duration_s": flags_used["extime"], "flags": flags_used,
            "genome_witness": manifest["genome"], "build_macro": manifest["macros"],
            "binary_sha256": manifest["binary_sha256"], "patch_sha256": manifest["patches"],
            "node": socket.gethostname(), "job_id": job_id, "run_id": run_id,
            "co_resident_processes": processes, "started_at": run["started_at"],
            "ended_at": run["ended_at"], "rc": run["rc"],
            "stdout": run["stdout"], "stderr": run["stderr"],
            "stdout_path": None, "stderr_path": None,
            "throughput_tps": workload["normal_commits"] / flags_used["extime"],
            "normal_commits": workload["normal_commits"],
            "batch_commits": workload["batch_commits"], "manifest": manifest,
            "verifier": None}


def _eligible_raw(row: dict) -> None:
    if row["mode"] not in ("prelim", "compare", "rtune"):
        raise ValueError("non-perf raw in performance aggregate")
    if row["duration_s"] != (30 if row["mode"] == "compare" else 10):
        raise ValueError("wrong performance duration")
    if row["round"] not in (range(1, 7) if row["mode"] == "compare" else range(1, 4)):
        raise ValueError("round outside preregistered schedule")
    tree, key = _build_for_arm(row["arm"])
    if row["manifest"]["tree"] != tree or row["manifest"]["arm"] != key:
        raise ValueError("performance manifest mismatch")
    patches = row["manifest"].get("patches", [])
    if row["manifest"].get("pin") != PIN or \
            [p.get("name") for p in patches] != [p.name for p in TREE_PATCHES[tree]] or \
            any(not re.fullmatch(r"[0-9a-f]{64}", str(p.get("sha256", ""))) for p in patches):
        raise ValueError("performance patch provenance mismatch")
    if row["manifest"].get("binary_sha256") != row["binary_sha256"] or \
            row["patch_sha256"] != row["manifest"]["patches"]:
        raise ValueError("raw and manifest disagree")
    if row["build_macro"] != list(variants(tree)[key]):
        raise ValueError("performance macro mismatch")
    if row["throughput_tps"] != row["normal_commits"] / row["duration_s"]:
        raise ValueError("throughput mismatch")


def _unique_runs(rows: list[dict]) -> None:  # M11
    ids = [row["run_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate run ID across prelim and comparison")


def paired(rows: list[dict], arm: str, point: str, gc: int, mode: str) -> list[dict]:  # M2
    groups = defaultdict(dict)
    for row in rows:
        _eligible_raw(row)
        if row["point"] == point and row["gc_inter_us"] == gc and row["mode"] == mode:
            key = (row["round"], row["node"], row["job_id"])
            if row["arm"] in groups[key]:
                raise ValueError("duplicate arm in one paired job")
            groups[key][row["arm"]] = row
    result = []
    for key, group in groups.items():
        if arm in group:
            if "R" not in group:
                raise ValueError("missing paired R")
            r, a = group["R"], group[arm]
            if r["throughput_tps"] <= 0 or r["batch_commits"] <= 0 and point in ("P1", "P2", "P3"):
                raise ValueError("invalid R denominator")
            result.append({"round": key[0], "node": key[1], "job_id": key[2],
                           "ratio": a["throughput_tps"] / r["throughput_tps"],
                           "completion_ratio": a["batch_commits"] / r["batch_commits"]
                           if r["batch_commits"] else None})
    if not result and any(r["point"] == point and r["mode"] == mode and
                          r["arm"] == arm for r in rows):
        raise ValueError("arm has no matching R at selected GC interval")
    return sorted(result, key=lambda item: (item["round"], item["node"]))


def select_gc(rows: list[dict], point: str) -> int:  # M3
    medians = {}
    for gc in (10, 100):
        selected = [r for r in rows if r["mode"] == "prelim"
                    and r["point"] == point and r["arm"] == "R" and r["gc_inter_us"] == gc]
        if len(selected) != 3 or {r["round"] for r in selected} != {1, 2, 3}:
            raise ValueError("need three R rounds at each GC interval")
        medians[gc] = statistics.median(r["throughput_tps"] for r in selected)
    return 10 if medians[10] >= medians[100] else 100


def completion_ok(pairs: list[dict], point: str) -> bool:  # M5
    if point in ("P1", "P2", "P3"):
        return bool(pairs) and all(p["completion_ratio"] is not None for p in pairs) and \
            statistics.median(p["completion_ratio"] for p in pairs) >= 0.8
    return bool(pairs)


def witness_ok(arm: str, counts: dict) -> bool:  # M6
    required = ["batch_c_lines"]
    if arm == "R": required += ["flag_raises"]
    if arm.startswith("hot"): required += ["hot_hits"]
    if arm == "fwd": required += ["forward_success"]
    if arm == "igc1": required += ["pruned"]
    return all(type(counts.get(key)) is int and counts[key] > 0 for key in required)


def certified_witness(arm: str, witness: dict) -> bool:
    return witness.get("status") == "certified" and witness_ok(arm, witness.get("counts", {}))


def accepted_witness(arm: str, witness: dict) -> bool:
    """Selection accepts an integrity-clean rc 0 or 3 and exercised mechanism."""
    return witness.get("accepted") is True and witness.get("verifier_rc") in (0, 3) and \
        witness_ok(arm, witness.get("counts", {}))


def check_c_lines(all_commits: int, c_lines: int, batch_commits: int,
                  batch_c_lines: int) -> None:  # M7
    if all_commits != c_lines:
        raise ValueError("all commits differ from all C lines")
    if batch_commits != batch_c_lines:
        raise ValueError("batch commits differ from batch worker C lines")


def verdict_label(rc: int) -> str:  # M12
    return {0: "certified", 3: "no-cycle (upper bound indeterminate)"}.get(rc, "rejected")


def choose_representative(summary: dict) -> tuple[str, str]:  # M4
    candidates = [(summary.get(point, {}).get(arm, {}).get("ratio", 0), point, arm)
                  for point in ("P2", "P3", "P1") for arm in M_ARMS
                  if summary.get(point, {}).get(arm, {}).get("eligible")]
    if not candidates:  # M17
        return "P2", max(M_ARMS, key=lambda arm: summary.get("P2", {}).get(arm, {}).get("ratio", 0))
    return max(candidates, key=lambda item: (item[0], -("P2", "P3", "P1").index(item[1]),
                                             -M_ARMS.index(item[2])))[1:]


def continuation(compare: dict, representative: str, neighbor: str,
                 arm: str) -> str:  # M10
    if neighbor not in compare or representative not in compare:
        return "判定不能"
    a, b = compare[representative].get(arm), compare[neighbor].get(arm)
    if not a or not b or not a["eligible"] or not b["eligible"]:
        return "判定不能"
    return "継続の材料" if a["ratio"] >= 1.5 and b["ratio"] >= 1.3 else "基準未達"


def aggregate(rows: list[dict], witnesses: dict | None = None) -> dict:
    _unique_runs(rows)
    witnesses = witnesses or {}
    prelim = [r for r in rows if r["mode"] == "prelim"]
    gc = {point: select_gc(prelim, point) for point in ("P1", "P2", "P3", "P4")
          if any(r["point"] == point for r in prelim)}
    summary = defaultdict(dict)
    for point, interval in gc.items():
        for arm in ARMS:
            if arm == "R": continue
            pairs = paired(prelim, arm, point, interval, "prelim")
            if pairs:
                summary[point][arm] = {"ratio": statistics.median(p["ratio"] for p in pairs),
                    "completion_ratio": statistics.median(p["completion_ratio"] for p in pairs
                        if p["completion_ratio"] is not None) if point != "P4" else None,
                    "eligible": len(pairs) == 3 and {p["round"] for p in pairs} == {1, 2, 3}
                        and completion_ok(pairs, point) and
                        (arm not in M_ARMS or accepted_witness(arm, witnesses.get(arm, {}))),
                    "pairs": pairs}
    rep, arm = choose_representative(summary)
    neighbor = {"P1": "P2", "P2": "P3", "P3": "P2"}[rep]
    needs_retune = summary.get(rep, {}).get(arm, {}).get("ratio", 0) >= 1.5
    compare = defaultdict(dict)
    retune = {}
    retune_rows = [r for r in rows if r["mode"] == "rtune" and r["point"] == rep and r["arm"] == "R"]
    if retune_rows:
        for interval in (1, 10, 100, 1000):
            selected = [r for r in retune_rows if r["gc_inter_us"] == interval]
            if len(selected) != 3 or {r["round"] for r in selected} != {1, 2, 3}:
                raise ValueError("R retune requires three rounds at all four intervals")
            retune[interval] = statistics.median(r["throughput_tps"] for r in selected)
    if needs_retune and not retune and any(r["mode"] == "compare" for r in rows):
        raise ValueError("R retune required before comparison")
    comparison_gc = max(retune, key=lambda interval: (retune[interval], -interval)) if retune else gc.get(rep)
    for point in (rep, neighbor, "P4", "P4prime"):
        if not any(r["mode"] == "compare" and r["point"] == point for r in rows): continue
        interval = comparison_gc if point in (rep, neighbor) else gc.get(point, gc.get("P4"))
        for candidate in M_ARMS:
            pairs = paired(rows, candidate, point, interval, "compare")
            if pairs:
                compare[point][candidate] = {"ratio": statistics.median(p["ratio"] for p in pairs),
                    "completion_ratio": statistics.median(
                        p["completion_ratio"] for p in pairs if p["completion_ratio"] is not None)
                        if point in ("P1", "P2", "P3") else None,
                    "eligible": len(pairs) == 6 and {p["round"] for p in pairs} == set(range(1, 7))
                        and completion_ok(pairs, point) and
                        accepted_witness(candidate, witnesses.get(candidate, {})),
                    "pairs": pairs}
    p4_add = any(summary.get("P4", {}).get(a, {}).get("ratio", 0) >= 1.3
                 for a in ("hot1", "hot8"))
    next_candidates = [a for a in M_ARMS if a != arm and
                       summary.get(rep, {}).get(a, {}).get("eligible")]  # M16
    next_arm = max(next_candidates, key=lambda a: (summary[rep][a]["ratio"], -M_ARMS.index(a))) \
        if next_candidates else None
    diagnostics = aggregate_diagnostics(rows)
    fallback = not summary.get(rep, {}).get(arm, {}).get("eligible", False)
    research_decision = ("判定不能 (代表腕が不適格)" if fallback else
                         final_recommendation(compare, rep, neighbor, arm, diagnostics))  # M14
    return {"gc": gc, "compare_gc": comparison_gc, "retune_R_medians": retune,
            "prelim": dict(summary), "representative": {"point": rep, "arm": arm},
            "neighbor": neighbor, "compare": dict(compare),
            "continuation": ("判定不能" if fallback else continuation(compare, rep, neighbor, arm)),
            "research_decision": research_decision, "diagnostics": diagnostics,
            "representative_usable_for_continuation": not fallback,
            "representative_note": ("継続判定に使えない (適格候補なし)" if fallback else None),
            "comparison_note": ("適格な次点 M 腕なし: S・R・代表の 3 腕" if next_arm is None else None),
            "decision_scope": "R (md_11 の観測最良設定 + 修正) に対する研究継続判断。lock なし区間 GC の SOTA は未比較",
            "retune_R": needs_retune,
            "add_P4_and_P4prime": p4_add,
            "comparison_arms": ["S", "R", arm] + ([next_arm] if next_arm else [])}


def final_recommendation(compare: dict, representative: str, neighbor: str,
                         arm: str, diagnostics: dict) -> str:  # M14
    """Apply the preregistered 30-second thresholds to the same M arm."""
    if not compare:
        return "予備のみ (暫定): 30 秒比較待ち"
    if representative not in compare or neighbor not in compare:
        return "判定不能 (隣接点の 30 秒比較なし)"
    a, b = compare[representative].get(arm), compare[neighbor].get(arm)
    if not a or not b or not a["eligible"] or not b["eligible"]:
        return "判定不能 (完了比または正しさ・機構 witness 不適格)"
    if a["ratio"] >= 1.5 and b["ratio"] >= 1.3:
        return "継続の材料"
    if a["ratio"] < 1.2:
        return "今の VHash を主論文候補から外す推奨"
    if a["ratio"] < 1.5:
        return "残存費用の実測次第 (追加試作 1 度の条件)"
    return "基準未達 (隣接点)"


def _json_counter_line(stdout: str, prefix: str) -> dict:
    lines = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise ValueError(f"{prefix.strip()}: expected one diagnostic line")
    value = json.loads(lines[0])
    if not isinstance(value, dict):
        raise ValueError("diagnostic JSON must be an object")
    return value


def aggregate_diagnostics(rows: list[dict]) -> dict:
    """Summarize only separately built diagnostic runs, never their throughput."""
    from . import vhash_cicada_hot_block as hot
    from . import vhash_interval_gc as igc
    result = {}
    for row in rows:
        if row["mode"] != "diag":
            continue
        arm, point, stdout = row["arm"], row["point"], row["stdout"]
        if arm in ("S", "R"):
            payload = V.parse_vlife_line(stdout)
            summary = V.summarize(payload)
            data = {key: summary.get(key) for key in (
                "gc_publications", "gc_boundary_mean_us", "gc_boundary_p50_bucket_us",
                "logical_version_delta")}
            data["logical_live_versions"] = row["flags"]["tuple_num"] + summary["logical_version_delta"]
            if arm == "R":
                data["ro_gcflag_raises"] = _counter(stdout, base.COUNT_PREFIX, "flag_raises")
        elif arm.startswith("hot"):
            counts = hot.parse_count(stdout, "post-" + arm)["variant"]
            totals = hot.aggregate_count(counts, "post-k" + arm[-1])
            data = {key: totals[key] for key in ("hot", "cold", "fallback_odd", "fallback_changed")}
        elif arm == "fwd":
            from . import vhash_forwarding_prototype as fwd
            payload, _ = fwd.parse_counter_lines(stdout, "count")
            data = {key: sum(thread[key] for thread in payload["threads"])
                    for key in ("attempts", "success")}
        elif arm.startswith("igc"):
            payload = _json_counter_line(stdout, "CICADA_INTERVAL_V1 ")
            if arm == "igc1":
                metrics = igc.interval_metrics(payload)
                data = {key: metrics[key] for key in ("pruned", "chain_versions")}
            else:
                if payload.get("debug_mode") != 3 or type(payload.get("chain_versions")) is not int or \
                        payload["chain_versions"] < 0:
                    raise ValueError("invalid mode 3 interval diagnostic")
                data = {"pruned": igc.counter_total(payload, "pruned"),
                        "chain_versions": payload["chain_versions"]}
        else:
            continue
        result.setdefault(point, {})[arm] = data
    return result


def job_estimate(build_seconds: dict, wall_seconds: float) -> dict:
    if wall_seconds <= 0 or not build_seconds or any(value <= 0 for value in build_seconds.values()):
        raise ValueError("positive smoke timings required")
    grouped = defaultdict(list)
    for name, seconds in build_seconds.items():
        grouped[name.split(":", 1)[0]].append((name, seconds))
    jobs, oversized = [], []
    for tree, binaries in grouped.items():
        shard, total = [], 0.0
        for name, seconds in binaries:
            if shard and total + seconds > 300:
                jobs.append({"kind": "build", "tree": tree, "binaries": shard,
                             "conditions": len(shard), "estimated_s": total})
                shard, total = [], 0.0
            if seconds > 300:
                oversized.append(name)
                jobs.append({"kind": "build", "tree": tree, "binaries": [name],
                             "conditions": 1, "estimated_s": seconds})
            else:
                shard.append(name)
                total += seconds
        if shard:
            jobs.append({"kind": "build", "tree": tree, "binaries": shard,
                         "conditions": len(shard), "estimated_s": total})
    for point in ("P1", "P2", "P3", "P4"):
        n = len(prelim_arms(point)) * 2
        jobs += [{"kind": "prelim", "point": point, "round": r, "conditions": n,
                  "estimated_s": n * wall_seconds} for r in range(1, 4)]
        jobs.append({"kind": "diag", "point": point, "conditions": len(prelim_arms(point)),
                     "estimated_s": len(prelim_arms(point)) * max(1, wall_seconds-9)})
    for arm in ("S", "R", "hot1", "hot8", "fwd", "igc1", "igc3", "igc-broken"):
        jobs.append({"kind": "verify", "arm": arm, "conditions": 2,
                     "estimated_s": 2 * max(1, wall_seconds-9)})
    jobs += [{"kind": "compare", "point": point, "round": r, "conditions": 4,
              "estimated_s": 4 * (20 + wall_seconds)} for point in ("representative", "neighbor")
              for r in range(1, 7)]
    conditional = [{"kind": "R-retune", "round": r, "conditions": 4,
                    "estimated_s": 4 * wall_seconds} for r in range(1, 4)]
    conditional += [{"kind": "P4-plus-P4prime-compare", "point": point, "round": r,
                     "conditions": 4, "estimated_s": 4 * (20 + wall_seconds)}
                    for point in ("P4", "P4prime") for r in range(1, 7)]
    base_seconds = sum(j["estimated_s"] for j in jobs)
    full_seconds = base_seconds + sum(j["estimated_s"] for j in conditional)
    return {"jobs": jobs, "conditional_jobs": conditional,
            "node_seconds": base_seconds, "node_seconds_with_conditionals": full_seconds,
            "over_2_node_hours": full_seconds > 7200,
            "build_over_5_minutes": oversized}


def require_budget(plan: dict, allow_over_budget: bool = False) -> dict:  # M15
    if plan["over_2_node_hours"] and not allow_over_budget:
        raise ValueError("estimated plan exceeds 7,200 node seconds; use --allow-over-budget")
    return plan


def prelim_arms(point: str) -> tuple[str, ...]:
    arms = ("S", "R", "R-noLR", "hot1", "hot8", "igc1", "igc3")
    return ("S", "R", "hot1", "hot8") if point.startswith("P4") else \
        arms + (("fwd",) if point in ("P2", "P3") else ())


def _do_build(args, smoke: bool = False) -> dict:
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(site_policy.heavy_work_refusal(site, DRIVER_ID))
    policy = V.compute._load_policy(args.policy.resolve(strict=True))
    toolchain = V.compute._resolve_toolchain(policy)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    receipts = {}
    selected = set(args.build_binaries.split(",")) if args.build_binaries else None
    available = {f"{tree}:{arm}" for tree in args.trees.split(",") if tree in TREES
                 for arm in variants(tree)}
    if selected is not None and (not selected or not selected <= available):
        raise ValueError("--build-binaries must name binaries in --trees")
    with tempfile.TemporaryDirectory(prefix="vceil-build-") as td:
        scratch = Path(td)
        deps = V.compute._prepare_dependencies(ROOT, policy,
            args.third_party_cache.resolve(strict=True), scratch, toolchain)
        if smoke:
            from . import vhash_cicada_hot_block as hot_block
            inert_source = base._source_copy(scratch / "src-inert")
            inert_build = scratch / "build-inert-pin"
            base._prepare_build_dependencies(inert_source, inert_build, toolchain, deps)
            entry = hot_block._compile_entries(inert_build)["ycsb_cicada.cc"]
            pin_sha = hot_block._preprocessed(entry)
            base._apply(inert_source, (V_PATCH, W_PATCH))
            patched_sha = hot_block._preprocessed(entry)
            zero_entry = dict(entry)
            if "arguments" in zero_entry:
                zero_entry["arguments"] = [*zero_entry["arguments"],
                    "-DIZANAGI_CICADA_CEILING_WORKLOAD=0"]
            else:
                zero_entry["command"] += " -DIZANAGI_CICADA_CEILING_WORKLOAD=0"
            zero_sha = hot_block._preprocessed(zero_entry)
            if pin_sha != patched_sha or pin_sha != zero_sha:
                raise ValueError("ceiling macro 0 is not pin-inert on owner TU")
            receipts["inert"] = {"owner": "cc/cicada/ycsb_cicada.cc",
                                  "pin_sha256": pin_sha, "patched_sha256": patched_sha,
                                  "explicit_zero_sha256": zero_sha}
        for tree in args.trees.split(","):
            if tree not in TREES: raise ValueError(f"unknown tree {tree}")
            check_patch_order(tree)
            source = base._source_copy(scratch / f"src-{tree}")
            base._apply(source, TREE_PATCHES[tree])
            base._prepare_build_dependencies(source, scratch / f"deps-{tree}", toolchain, deps)
            for arm, macros in variants(tree).items():
                if selected is not None and f"{tree}:{arm}" not in selected:
                    continue
                build = scratch / f"build-{tree}-{arm}"
                binary, receipt = _build_variant(source, build, "tuned", macros,
                    trace=tree.startswith("trace"), toolchain=toolchain, dependencies=deps,
                    arm=arm if tree in ("base", "hot", "fwd", "igc") else None)
                output = args.out_dir / f"{tree}-{arm}.exe"
                shutil.copy2(binary, output)
                shutil.copy2(build / "compile_commands.json",
                             args.out_dir / f"{tree}-{arm}.compile_commands.json")
                manifest = {"schema": 1, "pin": PIN, "tree": tree, "arm": arm,
                    "patches": patch_manifest(tree), "macros": list(macros),
                    "compile_commands_sha256": receipt["compile_commands_sha256"],
                    "compiler_version_sha256": receipt["compiler_version_sha256"],
                    "compiler_path": toolchain["cxx_path"],
                    "binary_sha256": base.sha(output), "genome": receipt["genome"]}
                (args.out_dir / f"{tree}-{arm}.manifest.json").write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n")
                receipts[f"{tree}-{arm}"] = receipt
    return receipts


def _do_smoke(args, receipts: dict) -> dict:
    """Exercise the workload output for every built, non-broken binary."""
    runs = {}
    with tempfile.TemporaryDirectory(prefix="vceil-smoke-", dir=os.getenv("TMPDIR", "/tmp")) as td:
        scratch = Path(td)
        for tree in args.trees.split(","):
            if tree == "trace-igc-broken":
                continue
            for arm in variants(tree):
                binary, manifest = _load_binary(args.out_dir, tree, arm, scratch)
                point = "P2"
                flags_used = flags(point, "igc1" if arm == "igc" else arm, 10, 1, 200)
                flags_used["thread_num"] = 4
                trace_dir = scratch / f"trace-{tree}-{arm}" if tree.startswith("trace") else None
                run = _run_one(binary, flags_used, scratch, trace_dir)
                if run["rc"]:
                    raise RuntimeError(f"smoke failed for {tree}/{arm}: {run['stderr'][-1000:]}")
                workload = parse_workload(run["stdout"], flags_used)
                runs[f"{tree}-{arm}"] = {"wall_s": run["wall_s"], "workload": workload,
                                          "binary_sha256": manifest["binary_sha256"]}
    wall = statistics.median(item["wall_s"] for item in runs.values())
    build = {key.rsplit("-", 1)[0] + ":" + key.rsplit("-", 1)[1]: item["elapsed_s"]
             for key, item in receipts.items() if "elapsed_s" in item}
    return {"runs": runs, "builds": receipts,
            "timings": {"build_seconds": build, "wall_seconds": wall,
                        "run_wall_seconds": {key: item["wall_s"] for key, item in runs.items()}},
            "job_estimate": require_budget(job_estimate(build, wall), args.allow_over_budget)}


def _do_run(args) -> list[dict]:
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(site_policy.heavy_work_refusal(site, DRIVER_ID))
    if args.point not in POINTS or args.round < 1:
        raise ValueError("unknown point or round")
    if args.mode == "prelim": arms = prelim_arms(args.point); intervals = (10, 100)
    elif args.mode == "compare":
        arms = tuple(args.arms.split(",")); intervals = (args.gc,)
        if len(arms) not in (3, 4) or set(arms[:2]) != {"S", "R"} or \
                len(set(arms)) != len(arms) or any(arm not in M_ARMS for arm in arms[2:]):
            raise ValueError("compare requires S,R and one or two distinct M arms")
    elif args.mode == "rtune": arms = ("R",); intervals = (1, 10, 100, 1000)
    else: arms = tuple(args.arms.split(",")); intervals = (args.gc,)
    if any(arm not in ARMS for arm in arms): raise ValueError("unknown arm")
    extime = 30 if args.mode == "compare" else 10 if args.mode in ("prelim", "rtune") else 1
    job_id = os.getenv("SLURM_JOB_ID", "local-" + str(uuid.uuid4()))
    rows = []
    log_dir = args.out.parent / (args.out.stem + "-logs") if args.out else None
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="vceil-run-", dir=os.getenv("TMPDIR", "/tmp")) as td:
        scratch = Path(td)
        binaries = {}
        for arm in arms:
            tree, key = _build_for_arm(arm, "diag" if args.mode == "diag" else "perf")
            if (tree, key) not in binaries:
                binaries[tree, key] = _load_binary(args.bin_dir, tree, key, scratch)
        order = arm_order(arms, args.round)
        for gc in intervals:
            for position, arm in enumerate(order):
                tree, key = _build_for_arm(arm, "diag" if args.mode == "diag" else "perf")
                binary, manifest = binaries[tree, key]
                run_flags = flags(args.point, arm, gc, extime, args.records)
                processes = _processes()
                run = _run_one(binary, run_flags, scratch)
                record = _record(run, mode=args.mode, point=args.point, arm=arm,
                    gc=gc, round_no=args.round, order=position, job_id=job_id,
                    processes=processes, manifest=manifest, flags_used=run_flags,
                    run_id=str(uuid.uuid4()))
                if log_dir:
                    for kind in ("stdout", "stderr"):
                        path = log_dir / f"{record['run_id']}.{kind}"
                        path.write_text(run[kind])
                        record[kind + "_path"] = str(path.resolve())
                rows.append(record)
    return rows


def _trace_counts(trace_dir: Path, workers: int) -> tuple[int, int]:
    total = batch = 0
    for path in trace_dir.glob("trace_*.log"):
        for line in path.read_text(errors="replace").splitlines():
            if line.startswith("C "):
                total += 1
                fields = line.split()
                if len(fields) >= 3 and fields[2].isdigit() and int(fields[2]) >= workers:
                    batch += 1
    return total, batch


def _counter(stdout: str, prefix: str, field: str) -> int:
    lines = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
    if len(lines) != 1: return 0
    try:
        payload = json.loads(lines[0])
        if "workers" in payload:
            values = [worker.get(field, 0) for worker in payload["workers"]]
        elif "threads" in payload:
            values = [worker.get(field, 0) for worker in payload["threads"]]
        else:
            values = [payload.get(field, 0)]
        return sum(values) if all(type(v) is int and v >= 0 for v in values) else 0
    except json.JSONDecodeError:
        return 0


def _verify_once(source: Path, binary: Path, manifest: dict, arm: str,
                 scratch: Path, seconds: int) -> dict:
    trace_dir = scratch / f"trace-{arm}-{seconds}"
    run_flags = flags("P2", arm, 10, seconds, 200)
    run_flags["thread_num"] = 4
    run = _run_one(binary, run_flags, scratch, trace_dir)
    workload = parse_workload(run["stdout"], run_flags)
    c_lines, batch_c_lines = _trace_counts(trace_dir, 4)
    check_c_lines(workload["normal_commits"] + workload["batch_commits"], c_lines,
                  workload["batch_commits"], batch_c_lines)
    count = {"batch_c_lines": batch_c_lines,
             "flag_raises": _counter(run["stdout"], base.COUNT_PREFIX, "flag_raises"),
             "hot_hits": _counter(run["stdout"], "CICADA_VHASH_COUNT_JSON ", "hot"),
             "forward_success": _counter(run["stdout"], "CICADA_FWD_V1 ", "success"),
             "pruned": _counter(run["stdout"], "CICADA_INTERVAL_V1 ", "pruned")}
    command = [sys.executable, "-m", "orchestrator.verify", str(trace_dir), "--json",
        "--protocol", "cicada", "--ccbench-root", str(source), "--expected-commits",
        str(c_lines)]
    verdict = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                             timeout=180, check=False)
    report = json.loads(verdict.stdout) if verdict.returncode in (0, 1, 3) else {}
    result = report.get("results", [{}])[0] if report.get("results") else {}
    mismatch = base.MISMATCH.findall(run["stderr"])
    accepted = verdict.returncode in (0, 3) and report.get("runs") == 1 and \
        report.get("indeterminate", 0) <= 1 and \
        result.get("total_cycles") == 0 and report.get("non_serializable") == 0 and all(
            type(result.get("integrity", {}).get(key)) is int and
            result["integrity"][key] == 0 for key in base.INTEGRITY_NUMERIC) and \
        type(result.get("integrity", {}).get("existence_violations", 0)) is int and \
        result.get("integrity", {}).get("existence_violations", 0) == 0 and \
        type(result.get("stats", {}).get("txns")) is int and \
        result["stats"]["txns"] == c_lines and len(mismatch) == 1 and mismatch[0] == "0"
    return {"arm": arm, "seconds": seconds, "counts": count,
            "verifier_rc": verdict.returncode, "verdict_label": verdict_label(verdict.returncode),
            "report": report, "accepted": accepted, "manifest": manifest,
            "read_wts_mismatch": mismatch,
            "trace_files": [{"path": str(p), "sha256": base.sha(p)}
                            for p in sorted(trace_dir.glob("trace_*.log"))]}


def _do_verify(args) -> list[dict]:
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(site_policy.heavy_work_refusal(site, DRIVER_ID))
    results = []
    with tempfile.TemporaryDirectory(prefix="vceil-verify-", dir=os.getenv("TMPDIR", "/tmp")) as td:
        scratch = Path(td)
        for arm in tuple(args.arms.split(",")):
            if arm == "igc-broken": tree, key = "trace-igc-broken", "igc"
            else: tree, key = _build_for_arm(arm, "trace")
            binary, manifest = _load_binary(args.bin_dir, tree, key, scratch)
            source = base._source_copy(scratch / f"source-{arm}")
            base._apply(source, TREE_PATCHES[tree])
            if arm == "igc-broken":
                try:
                    result = _verify_once(source, binary, manifest, arm, scratch, 1)
                except (ValueError, RuntimeError) as exc:
                    result = {"arm": arm, "status": "正例不成立", "error": str(exc)}
                    results.append(result)
                    continue
                result["status"] = "壊し正例" if result["report"].get("non_serializable", 0) > 0 else "正例不成立"
            else:
                result = _verify_once(source, binary, manifest, arm, scratch, 1)
                if not witness_ok(arm, result["counts"]):
                    result = _verify_once(source, binary, manifest, arm, scratch, 3)
                result["status"] = ("未検証 (機構未行使)" if not witness_ok(arm, result["counts"])
                                    else result["verdict_label"] if result["accepted"] else "rejected")
            results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "build", "run", "verify", "aggregate"))
    parser.add_argument("--mode", choices=("prelim", "diag", "compare", "rtune"), default="prelim")
    parser.add_argument("--point", default="P2")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--gc", type=int, default=10)
    parser.add_argument("--arms", default="S,R,hot1,hot8")
    parser.add_argument("--trees", default=",".join(TREES))
    parser.add_argument("--build-binaries", help="comma-separated tree:arm names from plan")
    parser.add_argument("--records", type=int, default=1_000_000)
    parser.add_argument("--bin-dir", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--witness", type=Path)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--allow-over-budget", action="store_true")
    parser.add_argument("--smoke-timings", type=Path)
    parser.add_argument("--third-party-cache", type=Path)
    parser.add_argument("--policy", type=Path, default=ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    args = parser.parse_args(argv)
    if args.out and args.out.resolve().is_relative_to(ROOT):
        parser.error("--out must be outside the shared repository")
    if args.out_dir and args.out_dir.resolve().is_relative_to(ROOT):
        parser.error("--out-dir must be outside the shared repository")
    if args.command in ("build", "smoke"):
        if not args.out_dir or not args.third_party_cache: parser.error("build needs --out-dir and --third-party-cache")
        result = _do_build(args, args.command == "smoke")
        if args.command == "smoke":
            result = _do_smoke(args, result)
    elif args.command == "run":
        if not args.bin_dir: parser.error("run needs --bin-dir")
        if not args.out: parser.error("run needs --out for JSONL and per-run logs")
        result = _do_run(args)
    elif args.command == "verify":
        if not args.bin_dir: parser.error("verify needs --bin-dir")
        result = _do_verify(args)
    else:
        if args.plan:
            if not args.smoke_timings: parser.error("--plan needs --smoke-timings")
            timing = json.loads(args.smoke_timings.read_text())
            timing = timing.get("timings", timing)
            result = require_budget(job_estimate(timing["build_seconds"], timing["wall_seconds"]),
                                    args.allow_over_budget)
        else:
            if not args.raw: parser.error("aggregate needs --raw")
            rows = [json.loads(line) for line in args.raw.read_text().splitlines() if line.strip()]
            witness_data = json.loads(args.witness.read_text()) if args.witness else {}
            witnesses = ({item["arm"]: item for item in witness_data}
                         if isinstance(witness_data, list) else witness_data)
            result = aggregate(rows, witnesses)
    if args.command == "run":
        payload = "".join(json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n"
                          for item in result)
    else:
        payload = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        if args.out.exists(): raise FileExistsError(args.out)
        args.out.write_text(payload)
    else: print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
