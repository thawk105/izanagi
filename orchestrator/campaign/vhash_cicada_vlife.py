#!/usr/bin/env python3
"""Cicada version lifetime diagnostics; throughput is diagnostic, not performance."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import condition_meaning_gate as condition
from . import s3_mocc_lock_coverage as compute
from . import s3_lock_coverage as locks
from . import site_policy
from .materializer_admission import non_admissible_materializer
from .p2_2 import _assert_single_tenant
from .patchharness import applied, checkout

ROOT = Path(__file__).resolve().parents[2]
PIN = "68106660686232781bca3be792a750d3e19d7a8a"
PATCH = ROOT / "patches/instr-cicada-version-lifetime.patch"
DRIVER_ID = "orchestrator.campaign.vhash_cicada_vlife"
MATERIALIZER = DRIVER_ID + "._build_variant"
PREFIX = "IZANAGI_CICADA_VLIFE_JSON "
K = (1, 2, 3, 4, 8)
SITES = ("read_update", "read_ronly", "blind_write", "rmw_latest",
         "precheck", "install", "readcheck", "writecheck")
POSITION_ORIGIN = ["latest"] * 6 + ["scan_start"] * 2
TIME_BOUNDS = [1 << i for i in range(41)] + [18446744073709551615]
MACROS = ("IZANAGI_CICADA_VLIFE", "IZANAGI_CICADA_LONGTX")
CONDITIONS = {
    f"{w}-{l}-gc{gc}": dict(
        ycsb_rratio=50 if w == "A" else 95,
        ycsb_zipf_skew=0 if w == "A" else 0.9,
        thread_num=47 if l == "ops1000" else 48,
        batch_th_num=1 if l == "ops1000" else 0,
        batch_max_ope=1000,
        worker1_insert_delay_rphase_us={"none": 0, "wait1ms": 1000,
                                        "wait10ms": 10000, "ops1000": 0}[l],
        gc_inter_us=gc,
    )
    for w in ("A", "B")
    for l in ("none", "wait1ms", "wait10ms", "ops1000")
    for gc in (10, 1000, 100000)
}


def select_conditions(value: str) -> tuple[str, ...]:
    ids = tuple(value.split(","))
    if not ids or any(not item or item.strip() != item for item in ids):
        raise ValueError("empty or malformed condition ID")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate condition ID")
    unknown = set(ids) - set(CONDITIONS)
    if unknown:
        raise ValueError("unknown condition ID: " + ",".join(sorted(unknown)))
    return ids


def _nonnegative(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("expected nonnegative integer")
    return value


def _vector(value: object, length: int) -> list[int]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError("vector length")
    return [_nonnegative(x) for x in value]


def parse_vlife_line(stdout: str) -> dict:
    lines = [line[len(PREFIX):] for line in stdout.splitlines()
             if line.startswith(PREFIX)]
    if len(lines) != 1:
        raise ValueError("missing or duplicate Cicada vlife JSON line")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    payload = json.loads(lines[0], object_pairs_hook=unique_pairs)
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "clocks_per_us", "bucket_bounds", "time_bucket_bounds",
        "position_origin", "sites", "build", "workers",
    }:
        raise ValueError("schema fields")
    if _nonnegative(payload["schema_version"]) != 1:
        raise ValueError("schema version")
    if not _nonnegative(payload["clocks_per_us"]):
        raise ValueError("zero clock")
    if _vector(payload["bucket_bounds"], 18) != [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 16, 32, 64, 128, 256, 512, 1024, 2048,
        18446744073709551615
    ]:
        raise ValueError("bucket bounds")
    if payload["sites"] != list(SITES):
        raise ValueError("site names")
    if _vector(payload["time_bucket_bounds"], 42) != TIME_BOUNDS:
        raise ValueError("time bucket bounds")
    if payload["position_origin"] != POSITION_ORIGIN:
        raise ValueError("position origin")
    build = payload["build"]
    if not isinstance(build, dict) or set(build) != {
        "reuse_version", "inline_version_opt", "longtx",
    }:
        raise ValueError("build fields")
    for val in build.values():
        _nonnegative(val)
    workers = payload["workers"]
    if not isinstance(workers, list) or not workers:
        raise ValueError("workers")
    scalars = {"readonly_attempt", "readonly_commit",
               "install", "detach", "gc_negative"}
    vectors = {"no_scan": 8, "deep": 5, "candidate": 5, "readonly_deep": 5,
               "deep_read_zero": 5, "candidate_read_zero": 5,
               "gc_boundary_us": 42, "gc_publish_us": 42,
               "age_create_us": 42, "age_overwrite_us": 42,
               "attempts": 2, "commits": 2, "aborts": 2,
               "operations": 2, "cycles": 2}
    for worker in workers:
        if not isinstance(worker, dict) or set(worker) != {
            "hops", "position", *scalars, *vectors
        }:
            raise ValueError("worker fields")
        for field in ("hops", "position"):
            if not isinstance(worker[field], list) or len(worker[field]) != len(SITES):
                raise ValueError("site vector")
            for row in worker[field]:
                _vector(row, 18)
        for field in scalars:
            _nonnegative(worker[field])
        for field, n in vectors.items():
            _vector(worker[field], n)
        if any(a > b for a, b in zip(worker["candidate"], worker["deep"])):
            raise ValueError("candidate exceeds deep")
        if any(a > b for a, b in zip(worker["deep_read_zero"], worker["deep"])):
            raise ValueError("zero-read exceeds deep")
        if any(a > b or a > c for a, b, c in zip(
            worker["candidate_read_zero"], worker["candidate"], worker["deep_read_zero"]
        )):
            raise ValueError("zero-read candidate exceeds denominator")
        if any(x > sum(worker["hops"][0]) for x in worker["deep"]):
            raise ValueError("deep exceeds update reads")
        if any(x > sum(worker["hops"][1]) for x in worker["readonly_deep"]):
            raise ValueError("read-only deep exceeds reads")
        if any(c + a > n for c, a, n in zip(
            worker["commits"], worker["aborts"], worker["attempts"]
        )):
            raise ValueError("transaction outcome exceeds attempts")
        if worker["readonly_commit"] > worker["readonly_attempt"]:
            raise ValueError("read-only commits exceed attempts")
    return payload


def summarize(payload: dict) -> dict:
    workers = payload["workers"]
    deep = [sum(w["deep"][i] for w in workers) for i in range(5)]
    candidate = [sum(w["candidate"][i] for w in workers) for i in range(5)]
    readonly = [sum(w["readonly_deep"][i] for w in workers) for i in range(5)]
    zero = [sum(w["deep_read_zero"][i] for w in workers) for i in range(5)]
    candidate_zero = [sum(w["candidate_read_zero"][i] for w in workers) for i in range(5)]
    return {
        "deep": deep, "candidate": candidate, "readonly_deep": readonly,
        "deep_read_zero": zero, "candidate_read_zero": candidate_zero,
        "candidate_rate": [candidate[i]/deep[i] if deep[i] else None for i in range(5)],
        "logical_version_delta": sum(w["install"]-w["detach"] for w in workers),
        "readonly_attempts": sum(w["readonly_attempt"] for w in workers),
    }


def depth_at_k(position: int, k: int) -> bool:
    if k not in K or position < 0:
        raise ValueError("position or K")
    return position >= k


def _checked(argv: list[str], *, cwd: Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"command failed rc={result.returncode}: {argv}: {result.stderr[-2000:]}")
    return result


def _gates(source: Path, macros: tuple[str, ...], args: list[str], cxx: str) -> list[dict]:
    records = []
    for macro in macros:
        captured = condition.capture_define_inputs(source, configure_args=tuple(args))
        request = condition.make_define_request(driver_id=DRIVER_ID, macro=macro,
                                                requested_value=1, default_value=0)
        with condition._configured_define_compile_commands(
            captured, request=request, cxx=cxx, cmake="cmake",
        ) as commands:
            supply = condition.evaluate_define_supply_effectuation(
                captured, request=request, cxx=cxx, cmake="cmake", configured_commands=commands)
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


def _build_variant(source: Path, build: Path, toolchain: dict, dependencies: dict,
                   macros: tuple[str, ...]) -> tuple[Path, dict]:
    admission = non_admissible_materializer(MATERIALIZER)
    args = compute._common_configure_args(trace=0, toolchain=toolchain,
                                           dependencies=dependencies)
    args = [arg for arg in args if arg not in compute.STOCK_G.cmake_defines()]
    args += ["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
    gates = _gates(source, macros, args, toolchain["cxx_path"]) if macros else []
    if macros:
        args += ["-DCMAKE_CXX_FLAGS=" + " ".join("-D" + m + "=1" for m in macros)]
    configure = ["cmake", "-S", str(source), "-B", str(build),
                 "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args]
    _checked(configure)
    _checked(["cmake", "--build", str(build), "--target", "ycsb_cicada.exe"])
    binary = build / "cc/cicada/ycsb_cicada.exe"
    if not binary.is_file():
        raise RuntimeError("Cicada binary missing")
    return binary, {
        "admission": admission, "gates": gates, "configure": configure,
        "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "macros": list(macros),
    }


def _run(binary: Path, flags: dict, *, cwd: Path, instrumented: bool = True) -> dict:
    _assert_single_tenant()
    argv = [str(binary)] + [f"-{k}={v}" for k, v in flags.items()]
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                                timeout=180, check=False)
    except subprocess.TimeoutExpired as exc:
        def decoded(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
        return {"argv": argv, "rc": None, "timeout_s": 180,
                "stdout": decoded(exc.stdout), "stderr": decoded(exc.stderr),
                "vlife_json_line": None, "parsed": None,
                "parse_error": "timeout", "summary": None,
                "throughput_interpretation": "diagnostic, not performance"}
    parsed = None
    parse_error = None
    if result.returncode == 0 and instrumented:
        try:
            parsed = parse_vlife_line(result.stdout)
            if len(parsed["workers"]) != flags["thread_num"] + flags["batch_th_num"]:
                raise ValueError("worker count differs from argv")
        except ValueError as exc:
            parse_error = str(exc)
    summary = summarize(parsed) if parsed else None
    if summary:
        summary["logical_live_versions"] = flags["tuple_num"] + summary["logical_version_delta"]
    return {"argv": argv, "rc": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr, "vlife_json_line": next(
                (line for line in result.stdout.splitlines() if line.startswith(PREFIX)), None),
            "parsed": parsed, "parse_error": parse_error,
            "summary": summary,
            "throughput_interpretation": "diagnostic, not performance"}


def _flags(condition_id: str, records: int, clocks_per_us: int) -> dict:
    return {"tuple_num": records, "ycsb_tuple_num": records,
            "thread_num": CONDITIONS[condition_id]["thread_num"],
            "batch_th_num": CONDITIONS[condition_id]["batch_th_num"],
            "batch_max_ope": 1000, "max_ope": 10, "ycsb_max_ope": 10,
            "rratio": CONDITIONS[condition_id]["ycsb_rratio"],
            "ycsb_rratio": CONDITIONS[condition_id]["ycsb_rratio"],
            "zipf_skew": CONDITIONS[condition_id]["ycsb_zipf_skew"],
            "ycsb_zipf_skew": CONDITIONS[condition_id]["ycsb_zipf_skew"],
            "gc_inter_us": CONDITIONS[condition_id]["gc_inter_us"],
            "worker1_insert_delay_rphase_us":
                CONDITIONS[condition_id]["worker1_insert_delay_rphase_us"],
            "extime": 3, "clocks_per_us": clocks_per_us}


def _normalized_disassembly(binary: Path) -> str:
    output = _checked(["objdump", "-d", str(binary)]).stdout
    output = re.sub(r"(?m)^.*: +file format .*$", "", output)
    output = re.sub(r"(?m)^ *[0-9a-f]+:", "ADDR:", output)
    output = re.sub(r"(?m)^([0-9a-f]+) <", "ADDR <", output)
    return output


def _normalized_rodata(binary: Path) -> str:
    output = _checked(["objdump", "-s", "-j", ".rodata", str(binary)]).stdout
    output = re.sub(r"(?m)^.*: +file format .*$", "", output)
    return re.sub(r"(?m)^ *[0-9a-f]+ +", "ADDR ", output)


def _smoke_records(path: Path) -> int:
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict) or raw.get("command") != "smoke" or raw.get("schema_version") != 1:
        raise ValueError("smoke JSON required")
    if raw.get("ccbench_commit") != PIN or raw.get("patch_sha256") != hashlib.sha256(PATCH.read_bytes()).hexdigest():
        raise ValueError("smoke build identity mismatch")
    witness = raw.get("witness")
    if not isinstance(witness, dict) or any(
        witness.get(key) is not True for key in
        ("normalized_objdump_equal", "normalized_rodata_equal")
    ) or any(
        not isinstance(witness.get(side), dict) or
        any(witness[side].get(tool) is not True for tool in ("nm", "strings"))
        for side in ("stock_absence", "default_absence")
    ):
        raise ValueError("smoke binary witness failed")
    short = raw.get("short_run")
    if not isinstance(short, dict) or type(short.get("rc")) is not int or short["rc"] != 0 or not isinstance(short.get("parsed"), dict):
        raise ValueError("smoke short run failed")
    calibration = raw.get("calibration")
    if not isinstance(calibration, dict):
        raise ValueError("smoke calibration missing")
    l3_bytes = calibration.get("l3_bytes")
    if type(l3_bytes) not in (int, float) or not math.isfinite(l3_bytes) or l3_bytes <= 0:
        raise ValueError("invalid L3 size")
    probes = calibration.get("probes")
    if not isinstance(probes, dict) or set(probes) != {"1000000", "2000000", "4000000"}:
        raise ValueError("incomplete calibration probes")
    for probe in probes.values():
        if not isinstance(probe, dict) or type(probe.get("rc")) is not int or probe["rc"] != 0 or type(probe.get("maxrss_kb")) is not int or probe["maxrss_kb"] <= 0:
            raise ValueError("failed calibration probe")
    eligible = [n for n in (1000000, 2000000, 4000000)
                if probes[str(n)]["maxrss_kb"] * 1024 > 4 * l3_bytes]
    expected = eligible[0] if eligible else 1000000
    records = calibration.get("selected_records")
    if type(records) is not int or records != expected:
        raise ValueError("calibrated records do not match probes")
    return records


def _absence(binary: Path) -> dict:
    outputs = {tool: _checked([tool, "-C", str(binary)] if tool == "nm"
                              else [tool, "-a", str(binary)]).stdout
               for tool in ("nm", "strings")}
    return {tool: not re.search(r"izanagi|IZANAGI_", value)
            for tool, value in outputs.items()}


def _delay_compile(source: Path, build: Path) -> dict:
    commands = json.loads((build / "compile_commands.json").read_text())
    rows = [row for row in commands
            if str(row["file"]).endswith("/cc/cicada/transaction.cc")]
    if len(rows) != 1:
        raise RuntimeError("Cicada transaction compile command not unique")
    row = rows[0]
    args = row.get("arguments") or shlex.split(row["command"])
    stripped = []
    skip = False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg == "-o":
            skip = True
            continue
        if arg == "-c":
            continue
        if arg.startswith("-DWORKER1_INSERT_DELAY_RPHASE="):
            continue
        stripped.append(arg)
    stripped += ["-fsyntax-only", "-DWORKER1_INSERT_DELAY_RPHASE=1"]
    result = subprocess.run(stripped, cwd=row["directory"], capture_output=True,
                            text=True, timeout=180, check=False)
    return {"argv": stripped, "rc": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def _calibrate(stock_binary: Path, scratch: Path) -> dict:
    cpu = _checked(["lscpu", "-J"]).stdout
    rows = json.loads(cpu).get("lscpu", [])
    l3 = next((row["data"] for row in rows
               if row.get("field", "").strip(":") == "L3 cache"), None)
    result = {"lscpu_json": cpu, "l3": l3, "probes": {}}
    for records in (1000000, 2000000, 4000000):
        _assert_single_tenant()
        flags = _flags("A-none-gc10", records, locks.CLK)
        flags.update(rratio=100, ycsb_rratio=100, extime=1)
        argv = ["/usr/bin/time", "-f", "IZANAGI_MAXRSS_KB %M",
                str(stock_binary)] + [f"-{k}={v}" for k, v in flags.items()]
        run = subprocess.run(argv, cwd=scratch, capture_output=True, text=True,
                             timeout=180, check=False)
        match = re.search(r"IZANAGI_MAXRSS_KB (\d+)", run.stderr)
        result["probes"][str(records)] = {
            "argv": argv, "rc": run.returncode, "stdout": run.stdout,
            "stderr": run.stderr, "maxrss_kb": int(match.group(1)) if match else None,
        }
    if l3 is None:
        raise RuntimeError("lscpu did not report L3")
    match = re.match(r"([0-9.]+)\s*([KMG]i?B)", l3)
    if match is None:
        raise RuntimeError("unrecognized L3 size: " + l3)
    l3_bytes = float(match.group(1)) * {
        "KB": 1000, "MB": 1000000, "GB": 1000000000,
        "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3,
    }[match.group(2)]
    result["l3_bytes"] = l3_bytes
    eligible = [n for n in (1000000, 2000000, 4000000)
                if result["probes"][str(n)]["maxrss_kb"] is not None
                and result["probes"][str(n)]["maxrss_kb"] * 1024 > 4 * l3_bytes]
    result["selected_records"] = eligible[0] if eligible else 1000000
    result["selection_reason"] = (
        "smallest N with maxrss > 4x L3" if eligible else
        "4M below 4x L3; use paper section 7.2 1M fallback"
    )
    return result


def _smoke(scratch: Path, toolchain: dict, dependencies: dict) -> dict:
    builds = {}
    binaries = {}
    with checkout(PIN, base_dir=str(ROOT / "external/ccbench")) as path:
        source = Path(path)
        binaries["stock"], builds["stock"] = _build_variant(
            source, scratch / "stock-build", toolchain, dependencies, ())
        delay = _delay_compile(source, scratch / "stock-build")
        with applied(str(PATCH), PIN, str(source)):
            binaries["default"], builds["default"] = _build_variant(
                source, scratch / "default-build", toolchain, dependencies, ())
            binaries["enabled"], builds["enabled"] = _build_variant(
                source, scratch / "enabled-build", toolchain, dependencies, MACROS)
    stock_text = _normalized_disassembly(binaries["stock"])
    default_text = _normalized_disassembly(binaries["default"])
    stock_rodata = _normalized_rodata(binaries["stock"])
    default_rodata = _normalized_rodata(binaries["default"])
    witness = {
        "normalized_objdump_equal": stock_text == default_text,
        "stock_objdump_sha256": hashlib.sha256(stock_text.encode()).hexdigest(),
        "default_objdump_sha256": hashlib.sha256(default_text.encode()).hexdigest(),
        "normalized_rodata_equal": stock_rodata == default_rodata,
        "stock_rodata_sha256": hashlib.sha256(stock_rodata.encode()).hexdigest(),
        "default_rodata_sha256": hashlib.sha256(default_rodata.encode()).hexdigest(),
        "stock_absence": _absence(binaries["stock"]),
        "default_absence": _absence(binaries["default"]),
    }
    calibration = _calibrate(binaries["stock"], scratch)
    flags = _flags("A-none-gc10", calibration["selected_records"], locks.CLK)
    flags["extime"] = 1
    short = _run(binaries["enabled"], flags, cwd=scratch)
    return {"builds": builds, "witness": witness, "delay_compile": delay,
            "calibration": calibration, "short_run": short}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "measure"))
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument("--policy", type=Path,
                        default=ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    parser.add_argument("--conditions", default="A-none-gc10")
    parser.add_argument("--smoke-json", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    ids = select_conditions(args.conditions)
    if args.command == "measure" and args.smoke_json is None:
        parser.error("measure requires --smoke-json")
    records = _smoke_records(args.smoke_json) if args.command == "measure" else None
    if args.out.exists():
        raise FileExistsError(args.out)
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        print(site_policy.heavy_work_refusal(site, "Cicada lifetime diagnostics"), file=sys.stderr)
        return 2
    _assert_single_tenant()
    policy = compute._load_policy(args.policy.resolve(strict=True))
    toolchain = compute._resolve_toolchain(policy)
    with tempfile.TemporaryDirectory(prefix="cicada-vlife-") as td:
        scratch = Path(td)
        dependencies = compute._prepare_dependencies(
            ROOT, policy, args.third_party_cache.resolve(strict=True), scratch, toolchain)
        if args.command == "smoke":
            result_body = _smoke(scratch, toolchain, dependencies)
        else:
            with checkout(PIN, base_dir=str(ROOT / "external/ccbench")) as stock_path:
                # Stock build prepares Masstree artifacts used by the enabled build.
                _, dependency_stock_build = _build_variant(
                    Path(stock_path), scratch / "dependency-stock-build",
                    toolchain, dependencies, ())
            with checkout(PIN, base_dir=str(ROOT / "external/ccbench")) as path:
                source = Path(path)
                with applied(str(PATCH), PIN, str(source)):
                    binary, build = _build_variant(source, scratch/"build", toolchain,
                                                   dependencies, MACROS)
                    runs = {id_: [
                        _run(binary, _flags(id_, records, locks.CLK), cwd=scratch)
                        for _ in range(3)
                    ] for id_ in ids}
            result_body = {"dependency_stock_build": dependency_stock_build,
                           "build": build, "runs": runs,
                           "conditions": {id_: CONDITIONS[id_] for id_ in ids},
                           "records": records}
    result = {"schema_version": 1, "command": args.command,
              "ccbench_commit": PIN, "patch_sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
              "site": site, "toolchain": toolchain, **result_body,
              "throughput_interpretation": "diagnostic, not performance"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if args.command == "smoke":
        good = (result_body["witness"]["normalized_objdump_equal"]
                and result_body["witness"]["normalized_rodata_equal"]
                and all(result_body["witness"]["stock_absence"].values())
                and all(result_body["witness"]["default_absence"].values())
                and all(probe["rc"] == 0 and probe["maxrss_kb"] is not None
                        for probe in result_body["calibration"]["probes"].values())
                and result_body["short_run"]["rc"] == 0
                and result_body["short_run"]["parsed"] is not None)
    else:
        good = all(run["rc"] == 0 and run["parsed"] is not None
                   for reps in result_body["runs"].values() for run in reps)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
