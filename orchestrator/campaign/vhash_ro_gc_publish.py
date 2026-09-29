#!/usr/bin/env python3
"""Paired Cicada read-only GC publication diagnostic on a compute node."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from orchestrator.calibrator.benchparse import parse_bench_stdout
from . import site_policy
from . import vhash_cicada_vlife as V
from . import condition_meaning_gate as condition
from .materializer_admission import non_admissible_materializer
from .p2_2 import _assert_single_tenant

ROOT = Path(__file__).resolve().parents[2]
PIN = V.PIN
VARIANT = ROOT / "patches/cicada-ro-gcflag-variant.patch"
WORKLOAD = ROOT / "patches/cicada-ro-gcflag-workload.patch"
TRACE = ROOT / "patches/instr-cicada-trace.patch"
VLIFE = V.PATCH
DRIVER_ID = "orchestrator.campaign.vhash_ro_gc_publish"
MATERIALIZER = DRIVER_ID + "._build_variant"
ORDER = (("stock", "variant"), ("variant", "stock")) * 3
CONDITIONS = {
    f"{series}{rate}-{delay}-gc10": {
        "series": series, "genome": "default" if series == "S" else "tuned",
        "skew": 0.0 if series == "S" else 0.9,
        "ro_pct": rate, "delay": delay, "wait_us": 10000 if delay == "wait10msR" else 0,
        "gc_inter_us": 10,
    }
    for series in ("S", "T") for rate in (0, 50, 95)
    for delay in ("none", "wait10msR")
}
COUNT_PREFIX = "IZANAGI_CICADA_RO_GCFLAG_COUNT_V1 "
WORKLOAD_PREFIX = "IZANAGI_CICADA_ROGC_WORKLOAD_V1 "
MISMATCH = re.compile(r"(?m)^CICADA_TRACE_READ_WTS_MISMATCH n=(\d+)$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checked(argv: list[str], *, cwd: Path | None = None, timeout: int = 900,
             env: dict | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=cwd, env=env, text=True,
                            capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"rc={result.returncode} argv={argv!r}: {result.stderr[-2000:]}")
    return result


def parse_line(stdout: str, prefix: str, fields: set[str]) -> dict:
    lines = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise ValueError(f"expected exactly one {prefix.strip()} line")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    payload = json.loads(lines[0], object_pairs_hook=unique)
    if not isinstance(payload, dict) or set(payload) != fields or payload["schema"] != 1:
        raise ValueError("counter schema")
    if any(type(value) is not int or value < 0 for value in payload.values()):
        raise ValueError("counter value")
    return payload


def parse_workload(stdout: str) -> dict:
    row = parse_line(stdout, WORKLOAD_PREFIX,
                     {"schema", "attempts", "ro_attempts", "commits", "long_ro_attempts"})
    if row["attempts"] < row["ro_attempts"] or row["attempts"] < row["commits"] or (
        row["ro_attempts"] < row["long_ro_attempts"]):
        raise ValueError("workload counters inconsistent")
    row["realized_ro_attempt_rate"] = (
        row["ro_attempts"] / row["attempts"] if row["attempts"] else None)
    return row


def parse_count(stdout: str) -> dict:
    row = parse_line(stdout, COUNT_PREFIX, {"schema", "ro_commits", "flag_raises"})
    if row["flag_raises"] > row["ro_commits"]:
        raise ValueError("flag raises exceed ro commits")
    return row


def pair_plan(condition_ids: tuple[str, ...]) -> tuple[dict, ...]:
    if not condition_ids or len(set(condition_ids)) != len(condition_ids):
        raise ValueError("empty or duplicate conditions")
    if set(condition_ids) - set(CONDITIONS):
        raise ValueError("unknown condition")
    return tuple({"condition": cid, "rep": rep + 1, "order": list(order)}
                 for cid in condition_ids for rep, order in enumerate(ORDER))


def check_throughput_macros(macros: tuple[str, ...]) -> None:
    if any(m in macros for m in ("IZANAGI_CICADA_VLIFE", "TRACE",
                                "IZANAGI_CICADA_RO_GCFLAG_COUNT")):
        raise ValueError("throughput build forbids VLIFE, TRACE, and COUNT")


def verify_acceptance(verifier_rc: int, report: dict, mismatch: int,
                      count: dict, *, max_indeterminate: int = 1) -> bool:
    return (verifier_rc in (0, 3) and report.get("runs") == 1
            and report.get("non_serializable") == 0
            and report.get("indeterminate", 0) <= max_indeterminate
            and len(report.get("results", [])) == 1
            and report["results"][0].get("total_cycles") == 0
            and report["results"][0].get("integrity", {}).get("clean") is True
            and mismatch == 0 and count["ro_commits"] > 0
            and count["flag_raises"] > 0)


def verdict_label(verifier_rc: int) -> str:
    return {0: "certified", 3: "no-cycle (upper bound indeterminate)"}.get(
        verifier_rc, "rejected")


def _source_copy(dest: Path) -> Path:
    source = ROOT / "external/ccbench"
    observed = _checked(["git", "-C", str(source), "rev-parse", "HEAD"]).stdout.strip()
    if observed != PIN:
        raise ValueError("CCBench pin mismatch")
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns(".git", "build*"))
    return dest


def _apply(source: Path, patches: tuple[Path, ...]) -> None:
    for patch in patches:
        _checked(["git", "apply", "--check", str(patch)], cwd=source)
        _checked(["git", "apply", str(patch)], cwd=source)


def _gates(source: Path, macros: tuple[str, ...], args: list[str], cxx: str) -> list[dict]:
    records = []
    for macro in macros:
        captured = condition.capture_define_inputs(source, configure_args=tuple(args))
        request = condition.make_define_request(
            driver_id=DRIVER_ID, macro=macro, requested_value=1, default_value=0)
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
        records.append({"macro": macro, "supply": json.loads(supply.canonical_json()),
                        "meaning": json.loads(meaning.canonical_json()),
                        "admission": json.loads(admission.canonical_json())})
        if not admission.admitted:
            raise RuntimeError(f"condition gate rejected {macro}: {records[-1]}")
    return records


def _build_variant(source: Path, build: Path, genome: str, macros: tuple[str, ...],
                   *, trace: bool, toolchain: dict, dependencies: dict) -> tuple[Path, dict]:
    non_admissible_materializer(MATERIALIZER)
    started = time.monotonic()
    args = V.compute._common_configure_args(trace=int(trace), toolchain=toolchain,
                                            dependencies=dependencies)
    args = [arg for arg in args if arg not in V.compute.STOCK_G.cmake_defines()]
    args += ["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", *V.genome_args(genome)]
    gates = _gates(source, macros, args, toolchain["cxx_path"])
    args.append("-DCMAKE_CXX_FLAGS=" + " ".join(f"-D{m}=1" for m in macros))
    configure = ["cmake", "-S", str(source), "-B", str(build),
                 "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args]
    _checked(configure)
    genome_witness = V.verify_genome_commands(build / "compile_commands.json", genome)
    commands = json.loads((build / "compile_commands.json").read_text())
    ycsb_rows = [row for row in commands if
                 "CMakeFiles/ycsb_cicada.exe.dir/" in
                 (row.get("command") or " ".join(row.get("arguments", [])))]
    if len(ycsb_rows) != 3 or {Path(row["file"]).name for row in ycsb_rows} != {
            "transaction.cc", "util.cc", "ycsb_cicada.cc"}:
        raise ValueError("ycsb_cicada compile_commands target is not three TUs")
    _checked(["cmake", "--build", str(build), "--target", "ycsb_cicada.exe"])
    binary = build / "cc/cicada/ycsb_cicada.exe"
    if not binary.is_file():
        raise RuntimeError("Cicada binary missing")
    return binary, {"macro": list(macros), "trace": trace, "vlife":
                    "IZANAGI_CICADA_VLIFE" in macros, "sha256": sha(binary),
                    "gates": gates, "configure": configure, "genome": genome_witness,
                    "compile_commands_target_rows": len(ycsb_rows),
                    "elapsed_s": time.monotonic() - started}


def _prepare_build_dependencies(source: Path, build: Path, toolchain: dict,
                                dependencies: dict) -> dict:
    # Fresh source copies lack Masstree's generated config.h until a stock build.
    _, receipt = _build_variant(source, build, "default", (), trace=False,
                                toolchain=toolchain, dependencies=dependencies)
    return receipt


def _flags(cell: dict, *, records: int, extime: int, clocks_per_us: int,
           workers: int = 48, seed: int = 0) -> dict:
    return {"tuple_num": records, "ycsb_tuple_num": records,
            "thread_num": workers, "batch_th_num": 0, "batch_max_ope": 1000,
            "max_ope": 10, "ycsb_max_ope": 10, "rratio": 50, "ycsb_rratio": 50,
            "zipf_skew": cell["skew"], "ycsb_zipf_skew": cell["skew"],
            "gc_inter_us": 10, "worker1_insert_delay_rphase_us": 0,
            "izanagi_rogc_ronly_pct": cell["ro_pct"],
            "izanagi_rogc_wait_us": cell["wait_us"],
            "izanagi_rogc_seed": seed,
            "extime": extime, "clocks_per_us": clocks_per_us,
            "group_commit": 0,
            **({"izanagi_ronly_pct": -1, "izanagi_long_kind": 0} if
               cell.get("vlife") else {})}


def _run(binary: Path, flags: dict, *, cwd: Path, trace_dir: Path | None = None) -> dict:
    _assert_single_tenant()
    argv = [str(binary), *(f"-{key}={value}" for key, value in flags.items())]
    env = os.environ.copy()
    if trace_dir is not None:
        trace_dir.mkdir()
        env["IZANAGI_TRACE_DIR"] = str(trace_dir)
    started_at = now()
    start = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                            text=True, timeout=180, check=False)
    return {"argv": argv, "rc": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr, "started_at": started_at, "ended_at": now(),
            "wall_s": time.monotonic() - start}


def _record(run: dict, *, condition: str, arm: str, rep: int, order: list[str],
            build: dict, command: str) -> dict:
    if command == "throughput" and (build["trace"] or build["vlife"] or
            "IZANAGI_CICADA_RO_GCFLAG_COUNT" in build["macro"]):
        raise ValueError("instrumented build cannot label throughput")
    if command == "measure" and (not build["vlife"] or build["trace"]):
        raise ValueError("measure requires VLIFE without TRACE")
    if command == "verify" and (not build["trace"] or
            "IZANAGI_CICADA_RO_GCFLAG_COUNT" not in build["macro"]):
        raise ValueError("verify requires TRACE and COUNT")
    if run["rc"] != 0:
        raise RuntimeError(f"Cicada run failed: {run['rc']} {run['stderr'][-1000:]}")
    result = {**run, "condition": condition, "arm": arm, "rep": rep,
              "order": order, "build": build, "command": command,
              "genome": build["genome"]["genome"],
              "flags": dict(arg[1:].split("=", 1) for arg in run["argv"][1:]),
              "build_macro": build["macro"],
              "instrumented": {"trace": build["trace"], "vlife": build["vlife"],
                               "count": "IZANAGI_CICADA_RO_GCFLAG_COUNT" in build["macro"]},
              "hostname": socket.gethostname(), "ccbench_commit": PIN,
              "patch_sha256": {p.name: sha(p) for p in (VARIANT, WORKLOAD,
                                  *((VLIFE,) if command == "measure" else ()),
                                  *((TRACE,) if command == "verify" else ()))}}
    result["workload"] = parse_workload(run["stdout"])
    if "IZANAGI_CICADA_RO_GCFLAG_COUNT" in build["macro"]:
        result["count"] = parse_count(run["stdout"])
    if command == "measure":
        payload = V.parse_vlife_line(run["stdout"])
        if payload["schema_version"] != 2:
            raise ValueError("VLIFE schema 2 required")
        result["vlife"] = payload
        result["summary"] = V.summarize(payload)
    elif command == "throughput":
        result["throughput_tps"] = parse_bench_stdout(run["stdout"])["throughput[tps]"]
    return result


def _verify(source: Path, binary: Path, cell: dict, *, scratch: Path,
            trace_root: Path,
            build: dict, seed: int, clocks_per_us: int) -> dict:
    trace_dir = trace_root / f"trace-{cell['series']}-{cell['ro_pct']}-{cell['delay']}-{seed}"
    flags = _flags(cell, records=200, extime=1, clocks_per_us=clocks_per_us,
                   workers=4, seed=seed)
    run = _run(binary, flags, cwd=scratch, trace_dir=trace_dir)
    record = _record(run, condition="verify", arm="variant", rep=seed,
                     order=["variant"], build=build, command="verify")
    matches = MISMATCH.findall(run["stderr"])
    if len(matches) != 1:
        raise ValueError("missing or duplicate READ_WTS_MISMATCH")
    record["read_wts_mismatch"] = int(matches[0])
    argv = [sys.executable, "-m", "orchestrator.verify", str(trace_dir),
            "--json", "--protocol", "cicada", "--ccbench-root", str(source),
            "--expected-commits", str(record["workload"]["commits"])]
    verdict = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True,
                             timeout=180, check=False)
    record["verifier"] = {"argv": argv, "rc": verdict.returncode,
                          "stdout": verdict.stdout, "stderr": verdict.stderr}
    report = json.loads(verdict.stdout) if verdict.returncode in (0, 1, 3) else {}
    record["verifier"]["report"] = report
    record["trace_files"] = [
        {"path": str(path.resolve()), "sha256": sha(path)}
        for path in sorted(trace_dir.glob("trace_*.log"))]
    record["verdict_label"] = verdict_label(verdict.returncode)
    record["no_cycle_upper_bound_indeterminate"] = verify_acceptance(
        verdict.returncode, report, record["read_wts_mismatch"], record["count"])
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "verify", "measure", "throughput"))
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument("--policy", type=Path,
                        default=ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--conditions", default=",".join(CONDITIONS))
    parser.add_argument("--records", type=int, default=1000000)
    parser.add_argument("--extime", type=int, default=3)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    if args.records <= 0 or args.extime <= 0:
        parser.error("records and extime must be positive")
    ids = tuple(args.conditions.split(","))
    plan = pair_plan(ids)
    if args.command == "smoke" and "S95-wait10msR-gc10" not in ids:
        parser.error("smoke requires S95-wait10msR-gc10")
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(site_policy.heavy_work_refusal(site, DRIVER_ID))
    mode = args.command
    raw = {"schema_version": 1, "command": mode, "ccbench_commit": PIN,
           "hostname": socket.gethostname(), "site": site,
           "records": args.records, "extime": args.extime, "workers": 48,
           "measurement_env": {"records": args.records, "extime": args.extime,
                               "workers": 48, "site": site},
           "started_at": now(),
           "patch_sha256": {p.name: sha(p) for p in (VARIANT, WORKLOAD, VLIFE, TRACE)},
           "conditions": {cid: CONDITIONS[cid] for cid in ids}, "plan": plan,
           "runs": [], "builds": {}, "dependency_builds": {}, "trace_genome_coverage":
           "tuned OPT=1/PROM=0 awaiting md_20"}
    try:
        _assert_single_tenant()
        policy = V.compute._load_policy(args.policy.resolve(strict=True))
        toolchain = V.compute._resolve_toolchain(policy)
        with tempfile.TemporaryDirectory(prefix="rogc-publish-") as td:
            scratch = Path(td)
            dependencies = V.compute._prepare_dependencies(
                ROOT, policy, args.third_party_cache.resolve(strict=True), scratch, toolchain)
            source = _source_copy(scratch / "ccbench")
            patches = ((TRACE,) if mode == "verify" else
                       (VLIFE,) if mode == "measure" else ()) + (WORKLOAD, VARIANT)
            _apply(source, patches)
            raw["dependency_builds"]["primary"] = _prepare_build_dependencies(
                source, scratch / "build-dependency", toolchain, dependencies)
            genomes = (["default"] if mode == "smoke" else
                       sorted({CONDITIONS[cid]["genome"] for cid in ids}))
            arms = ("variant",) if mode == "verify" else ("stock", "variant")
            binaries = {}
            for genome in genomes:
                for arm in arms:
                    macros = ("IZANAGI_CICADA_ROGC_WORKLOAD",)
                    if mode == "measure":
                        macros += ("IZANAGI_CICADA_VLIFE",)
                    if arm == "variant":
                        macros += ("IZANAGI_CICADA_RO_GCFLAG",)
                    if mode in ("smoke", "verify") and arm == "variant":
                        macros += ("IZANAGI_CICADA_RO_GCFLAG_COUNT",)
                    if mode == "throughput":
                        check_throughput_macros(macros)
                    binary, receipt = _build_variant(
                        source, scratch / f"build-{genome}-{arm}", genome, macros,
                        trace=mode == "verify", toolchain=toolchain,
                        dependencies=dependencies)
                    binaries[genome, arm] = binary
                    raw["builds"][f"{genome}-{arm}"] = receipt
            if mode == "verify":
                trace_root = args.out.parent / (args.out.stem + "-traces")
                trace_root.mkdir(parents=True, exist_ok=False)
                for genome in genomes:
                    for rate in (50, 95):
                        for delay in ("none", "wait10msR"):
                            cid = f"{'S' if genome == 'default' else 'T'}{rate}-{delay}-gc10"
                            if cid not in ids:
                                continue
                            for seed in range(1, 4):
                                cell = CONDITIONS[cid]
                                record = _verify(source, binaries[genome, "variant"], cell,
                                    scratch=scratch,
                                    trace_root=trace_root,
                                    build=raw["builds"][f"{genome}-variant"],
                                    seed=seed, clocks_per_us=V.locks.CLK)
                                record["condition"] = cid
                                raw["runs"].append(record)
            else:
                selected = (next(item for item in plan if item["condition"] ==
                            "S95-wait10msR-gc10" and item["rep"] == 1),) if mode == "smoke" else plan
                for item in selected:
                    cell = dict(CONDITIONS[item["condition"]])
                    cell["vlife"] = mode == "measure"
                    flags = _flags(cell, records=args.records, extime=args.extime,
                                   clocks_per_us=V.locks.CLK)
                    for arm in item["order"]:
                        run = _run(binaries[cell["genome"], arm], flags, cwd=scratch)
                        record = _record(run, condition=item["condition"], arm=arm,
                            rep=item["rep"], order=item["order"],
                            build=raw["builds"][f"{cell['genome']}-{arm}"], command=mode)
                        raw["runs"].append(record)
                        if mode == "smoke" and arm == "variant" and (
                                record["count"]["flag_raises"] == 0):
                            raise ValueError("smoke did not exercise ro GC flag raise")
                if mode == "smoke":
                    cell = dict(CONDITIONS["S95-wait10msR-gc10"])
                    for kind, extra in (("trace", TRACE), ("vlife", VLIFE)):
                        other = _source_copy(scratch / f"ccbench-{kind}")
                        _apply(other, (extra, WORKLOAD, VARIANT))
                        raw["dependency_builds"][kind] = _prepare_build_dependencies(
                            other, scratch / f"smoke-{kind}-dependency", toolchain,
                            dependencies)
                        macros = ("IZANAGI_CICADA_ROGC_WORKLOAD",
                                  "IZANAGI_CICADA_RO_GCFLAG",
                                  "IZANAGI_CICADA_RO_GCFLAG_COUNT")
                        if kind == "vlife":
                            macros += ("IZANAGI_CICADA_VLIFE",)
                            cell["vlife"] = True
                        binary, receipt = _build_variant(
                            other, scratch / f"smoke-{kind}-build", "default", macros,
                            trace=kind == "trace", toolchain=toolchain,
                            dependencies=dependencies)
                        raw["builds"][f"smoke-{kind}"] = receipt
                        flags = _flags(cell, records=200, extime=1,
                                       clocks_per_us=V.locks.CLK, workers=4)
                        run = _run(binary, flags, cwd=scratch)
                        record = _record(run, condition="S95-wait10msR-gc10",
                            arm="variant", rep=1, order=["variant"],
                            build=receipt, command="measure" if kind == "vlife" else "smoke")
                        record["smoke_preimage"] = kind
                        if record["count"]["flag_raises"] == 0:
                            raise ValueError(f"smoke {kind} flag raise count is zero")
                        raw["runs"].append(record)
    except Exception as exc:
        raw["error"] = f"{type(exc).__name__}: {exc}"
    raw["ended_at"] = now()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    return 0 if "error" not in raw and raw["runs"] and all(
        row.get("no_cycle_upper_bound_indeterminate", True) for row in raw["runs"]) else 1


if __name__ == "__main__":
    sys.exit(main())
