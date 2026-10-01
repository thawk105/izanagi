#!/usr/bin/env python3
"""C2 motivation: smoke grid, paired measurements, and offline aggregation.

Correctness ceiling: indeterminate (existing md_22/md_42 evidence).
The pinned patch forces long updates only with VLIFE; LONGTX alone extends
the natural YCSB procedure. Record that limitation, without changing the patch.
"""
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
import socket
import statistics
import tempfile
import time

from . import vhash_cicada_vlife as V
from . import condition_meaning_gate as condition
from .materializer_admission import non_admissible_materializer
from .patchharness import apply_patch

ROOT, PIN = V.ROOT, V.PIN
DRIVER_ID = "orchestrator.campaign.vhash_c2_motivation"
MATERIALIZER = DRIVER_ID + "._build_variant"
R_PATCH = ROOT / "patches/cicada-ro-gcflag-variant.patch"
ARMS = ("S", "R", "S-noLT", "R-noLT")
POINTS = {f"skew{s:g}-ops{o}-rr{r}": {"skew": s, "ops": o, "rr": r}
          for s in (0, .3, .6) for o in (100, 300, 1000) for r in (50, 70, 90)}
MIN_COMPLETION_RATE = 0.10
MIN_LONG_COMMITS = 100
MIN_BOUNDARY_RATIO = 4
MIN_BOUNDARY_US = 1_000
LIMITATION = ("indeterminate; LONGTX-only perf extends natural YCSB procedures; "
              "izanagi_long_kind=1 forces updates only in VLIFE diagnostics")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def macros(kind: str, arm: str) -> tuple[str, ...]:
    if kind not in ("perf", "diag") or arm not in ARMS:
        raise ValueError("unknown build")
    result = ("IZANAGI_CICADA_LONGTX",)
    if kind == "diag":
        result += ("IZANAGI_CICADA_VLIFE",)
    if arm.startswith("R"):
        result += ("IZANAGI_CICADA_RO_GCFLAG",)
    return result


def _definitions(row: dict) -> dict:
    argv = row.get("arguments") or shlex.split(row["command"])
    result = {}
    for i, token in enumerate(argv):
        if token == "-D":
            token += argv[i + 1]
        if token.startswith("-D") and token != "-D":
            key, _, value = token[2:].partition("=")
            if key in result and result[key] != (value or "1"):
                raise ValueError("conflicting compile definitions")
            result[key] = value or "1"
    return result


def check_perf_defines(commands: list[dict], arm: str) -> None:
    # CMake supplies TRACE=0 and Boost definitions even without instrumentation.
    expected = {"ADD_ANALYSIS": "0", "KEY_SIZE": "8", "VAL_SIZE": "4",
                "MASSTREE_USE": "1", "TRACE": "0", "SINGLE_EXEC": "0",
                "WORKER1_INSERT_DELAY_RPHASE": "0", "PARTITION_TABLE": "0",
                "Linux": "1", "NDEBUG": "1", "BOOST_ALL_NO_LIB": "1",
                "BOOST_FILESYSTEM_DYN_LINK": "1",
                **{k: str(v) for k, v in V.TUNED_GENOME.items()},
                **{m: "1" for m in macros("perf", arm)}}
    rows = [r for r in commands if "CMakeFiles/ycsb_cicada.exe.dir/" in
            (r.get("command") or " ".join(r.get("arguments", [])))]
    if len(rows) != 3 or {Path(r["file"]).name for r in rows} != {
            "transaction.cc", "util.cc", "ycsb_cicada.cc"}:
        raise ValueError("incomplete Cicada compile commands")
    for row in rows:
        actual = _definitions(row)
        if actual != expected:
            raise ValueError(f"perf -D mismatch: {actual} != {expected}")


def define_request(macro: str):
    return condition.make_define_request(driver_id=DRIVER_ID, macro=macro,
                                         requested_value=1, default_value=0)


def _gates(source: Path, enabled: tuple[str, ...], args: list[str], cxx: str) -> list:
    records = []
    for macro in enabled:
        captured = condition.capture_define_inputs(source, configure_args=tuple(args))
        request = define_request(macro)
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
            raise RuntimeError(f"condition gate rejected {macro}")
    return records


def _build_variant(source: Path, build: Path, toolchain: dict, dependencies: dict,
                   kind: str, arm: str) -> tuple[Path, dict]:
    admission = non_admissible_materializer(MATERIALIZER)
    started = time.monotonic()
    enabled = macros(kind, arm)
    args = V.compute._common_configure_args(trace=0, toolchain=toolchain,
                                            dependencies=dependencies)
    args = [a for a in args if a not in V.compute.STOCK_G.cmake_defines()]
    args += ["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCCBENCH_VAL_SIZE=4",
             *V.genome_args("tuned")]
    gates = _gates(source, enabled, args, toolchain["cxx_path"])
    args += ["-DCMAKE_CXX_FLAGS=" + " ".join("-D" + m + "=1" for m in enabled)]
    configure = ["cmake", "-S", str(source), "-B", str(build),
                 "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args]
    V._checked(configure)
    witness = V.verify_genome_commands(build / "compile_commands.json", "tuned", 4)
    if kind == "perf":
        check_perf_defines(json.loads((build / "compile_commands.json").read_text()), arm)
    V._checked(["cmake", "--build", str(build), "--target", "ycsb_cicada.exe"])
    binary = build / "cc/cicada/ycsb_cicada.exe"
    return binary, {"admission": admission, "gates": gates, "configure": configure,
                    "macros": list(enabled), "genome": witness, "val_size": 4,
                    "binary_sha256": sha(binary), "elapsed_s": time.monotonic() - started,
                    "compile_commands_sha256": sha(build / "compile_commands.json")}


def flags(point: str, arm: str, kind: str, gc: int, extime: int) -> dict:
    p = POINTS[point]
    macros(kind, arm)  # Validate the build key before constructing its flags.
    if gc not in (10, 100) or type(extime) is not int or not 0 < extime < 180:
        raise ValueError("invalid GC interval or duration (runner timeout is 180s)")
    result = dict(tuple_num=1_000_000, ycsb_tuple_num=1_000_000,
                  thread_num=47, batch_th_num=0 if arm.endswith("-noLT") else 1,
                  batch_max_ope=p["ops"], max_ope=10, ycsb_max_ope=10,
                  rratio=p["rr"], ycsb_rratio=p["rr"], zipf_skew=p["skew"],
                  ycsb_zipf_skew=p["skew"], gc_inter_us=gc, extime=extime,
                  clocks_per_us=V.locks.CLK, group_commit=0,
                  worker1_insert_delay_rphase_us=0, izanagi_long_kind=1)
    # common.hh defines worker1_insert_delay_rphase_us unconditionally.
    # transaction.cc defines these two only under IZANAGI_CICADA_VLIFE.
    if kind == "diag":
        result.update(izanagi_ronly_pct=-1, izanagi_vlife_schema=3)
    return result


def arm_order(round_no: int) -> tuple[str, ...]:
    if round_no < 1:
        raise ValueError("round must be positive")
    offset = (round_no - 1) % len(ARMS)
    rotated = ARMS[offset:] + ARMS[:offset]
    return tuple(reversed(rotated)) if round_no % 2 == 0 else rotated


def smoke_plan(skew: float) -> list[tuple]:
    if skew not in (0, .3, .6):
        raise ValueError("unknown skew")
    points = [p for p, v in POINTS.items() if v["skew"] == skew]
    diag = [(p, a, "diag", 10, 3, 1) for p in points for a in ARMS[:2]]
    diag += [(p, a, "diag", 10, 3, 1) for p in points if POINTS[p]["ops"] == 100
             for a in ARMS[2:]]
    return diag + [(points[0], a, "perf", 10, 1, 1) for a in ARMS[:2]]


def measure_plan(point: str, kind: str, gc: int, rounds: int, extime: int) -> list[tuple]:
    flags(point, "S", kind, gc, extime)
    if type(rounds) is not int or rounds < 1:
        raise ValueError("rounds must be positive")
    return [(point, arm, kind, gc, extime, r) for r in range(1, rounds + 1)
            for arm in arm_order(r)]


def job_estimate(build_s: float, rounds: int, extime: int, startup_load_s: float) -> dict:
    """Informational one-job estimate; never a smoke worst-case admission gate."""
    return {"build_s": build_s, "runs": 4 * rounds, "extime_s": extime,
            "startup_load_s": startup_load_s,
            "estimated_s": build_s + 4 * rounds * (extime + startup_load_s)}


def scratch_directory():
    return tempfile.TemporaryDirectory(prefix="vhash-c2-",
                                       dir=os.getenv("TMPDIR") or tempfile.gettempdir())


def parse_throughput(stdout: str) -> int:
    # common/result.cc::displayTps emits an integer including batch commits.
    rows = re.findall(r"(?m)^throughput\[tps\]:[ \t]*([0-9]+)[ \t]*$", stdout)
    if len(rows) != 1:
        raise ValueError("expected one throughput[tps] line")
    return int(rows[0])


def summarize_run(run: dict) -> dict:
    result = {"rc": run["rc"], "valid": False}
    if run["rc"] != 0 or run.get("parse_error"):
        return result
    if run["kind"] == "perf":
        return {**result, "valid": True, "throughput_tps": parse_throughput(run["stdout"])}
    payload = V.parse_vlife_line(run["stdout"])
    V._validate_run_echo(payload, run["flags"], "tuned", 4)
    summary = V.summarize(payload)
    attempts = sum(w["attempts"][1] for w in payload["workers"])
    commits = sum(w["commits"][1] for w in payload["workers"])
    chains = [c["length"] for c in payload["hot_chains"] if c["status"] == "ok"]
    return {**result, "valid": True, "long_attempts": attempts, "long_commits": commits,
            "long_completion_rate": commits / attempts if attempts else None,
            "normal_commits": sum(w["commits"][0] for w in payload["workers"]),
            **{k: summary[k] for k in ("gc_boundary_mean_us", "gc_boundary_p50_bucket_us",
                                      "gc_publications")},
            "logical_live_versions": run["flags"]["tuple_num"] + summary["logical_version_delta"],
            "hot_chain_max": max(chains) if chains else None,
            "hot_chain_median": statistics.median(chains) if chains else None,
            "hot_chain_ok_count": len(chains)}


def _run_one(binary: Path, item: tuple, scratch: Path, job_started_at: str, order: int) -> dict:
    point, arm, kind, gc, extime, round_no = item
    run_flags = flags(point, arm, kind, gc, extime)
    started_at, binary_sha256 = now(), sha(binary)
    run = V._run(binary, run_flags, cwd=scratch, instrumented=kind == "diag",
                 genome="tuned", val_size=4)
    run.update(point=point, arm=arm, kind=kind, gc=gc, extime=extime,
               round=round_no, order=order, flags=run_flags,
               hostname=socket.gethostname(), started_at=started_at,
               job_started_at=job_started_at, binary_sha256=binary_sha256,
               macros=list(macros(kind, arm)))
    run["throughput_interpretation"] = ("performance: total transactions/s"
                                        if kind == "perf" else "diagnostic, not performance")
    try:
        run["summary"] = summarize_run(run)
    except ValueError as exc:
        run["parse_error"] = str(exc)
        run["summary"] = {"rc": run["rc"], "valid": False}
    return run


def established(long: dict, control: dict) -> bool:
    rate, age, baseline = (long.get("long_completion_rate"),
                           long.get("gc_boundary_mean_us"), control.get("gc_boundary_mean_us"))
    return (long.get("valid", False) and control.get("valid", False)
            and rate is not None and rate >= MIN_COMPLETION_RATE
            and long["long_commits"] >= MIN_LONG_COMMITS
            and age is not None and baseline is not None
            and age >= MIN_BOUNDARY_RATIO * baseline and age >= MIN_BOUNDARY_US)


def choose_points(grid: list[dict]) -> dict:
    eligible = sorted((p for p in grid if p["established"]), key=lambda p: p["point"])
    if not eligible:
        return {"A": None, "B": None}
    # A zero control mean gives an infinite ratio; encode it as a separate bit.
    a = max(eligible, key=lambda p: (p["zero_control_mean"], p["boundary_ratio"] or 0))
    b = max(eligible, key=lambda p: p["long_completion_rate"])
    return {"A": a["point"], "B": b["point"] if b != a else None}


def _rows(documents: list[dict], command: str) -> list[dict]:
    rows = []
    for doc in documents:
        if doc.get("command") != command or doc.get("schema_version") != 1:
            raise ValueError("wrong input command or schema")
        for run in doc["runs"]:
            expected = flags(run["point"], run["arm"], run["kind"], run["gc"], run["extime"])
            if run["flags"] != expected or run["macros"] != list(macros(run["kind"], run["arm"])):
                raise ValueError("run flags or macros disagree with build")
            rows.append({**run, "summary": summarize_run(run)})
    return rows


def aggregate_smoke(documents: list[dict]) -> dict:
    rows = _rows(documents, "smoke")
    lookup, liveness = {}, set()
    for row in rows:
        if row["gc"] != 10 or row["extime"] != (3 if row["kind"] == "diag" else 1):
            raise ValueError("wrong smoke duration or GC interval")
        if row["kind"] != "diag":
            key = (POINTS[row["point"]]["skew"], row["arm"])
            if key in liveness or row["arm"] not in ARMS[:2]:
                raise ValueError("duplicate or unknown perf liveness arm")
            liveness.add(key)
            continue
        p = POINTS[row["point"]]
        key = (p["skew"], p["rr"], 0 if row["arm"].endswith("-noLT") else p["ops"], row["arm"])
        if key in lookup:
            raise ValueError("duplicate smoke condition")
        lookup[key] = row["summary"]
    grid = []
    for point, p in POINTS.items():
        key = (p["skew"], p["rr"])
        long = lookup.get((*key, p["ops"], "R"), {})
        control = lookup.get((*key, 0, "R-noLT"), {})
        age, baseline = long.get("gc_boundary_mean_us"), control.get("gc_boundary_mean_us")
        grid.append({"point": point, "R": long, "R_noLT": control,
                     "established": established(long, control),
                     "long_completion_rate": long.get("long_completion_rate"),
                     "zero_control_mean": baseline == 0,
                     "boundary_ratio": age / baseline if age is not None and baseline else None})
    selected = choose_points(grid)
    complete = len(lookup) == 72 and len(liveness) == 6
    successful = all(r["summary"]["valid"] for r in rows) and not any("error" in d for d in documents)
    return {"grid": grid, "grid_complete": complete, "selected": selected,
            "measure_allowed": complete and successful and selected["A"] is not None,
            "established_count": sum(p["established"] for p in grid), "runs": rows}


def _median(values) -> float | None:
    present = [v for v in values if v is not None]
    return statistics.median(present) if present else None


def aggregate_measure(documents: list[dict]) -> dict:
    rows = _rows(documents, "measure")
    groups, pairs = defaultdict(list), defaultdict(dict)
    for row in rows:
        key = (row["point"], row["kind"], row["gc"])
        groups[(*key, row["arm"])].append(row["summary"])
        pair = pairs[(*key, row["hostname"], row["job_started_at"], row["round"])]
        if row["arm"] in pair:
            raise ValueError("duplicate arm in round")
        pair[row["arm"]] = row["summary"]
    for point, kind, gc, arm in groups:
        if len({r["extime"] for r in rows if (r["point"], r["kind"], r["gc"], r["arm"])
                == (point, kind, gc, arm)}) != 1:
            raise ValueError("mixed durations in measurement group")
    medians = []
    for key, items in sorted(groups.items()):
        fields = set().union(*(set(s) for s in items)) - {"rc", "valid"}
        medians.append(dict(point=key[0], kind=key[1], gc=key[2], arm=key[3],
            runs=len(items), valid_runs=sum(s["valid"] for s in items),
            metrics={f: _median(s.get(f) for s in items) for f in sorted(fields)}))
    ratios = defaultdict(lambda: defaultdict(list))
    for key, group in pairs.items():
        if set(group) != set(ARMS):
            raise ValueError("incomplete paired round on one job/node")
        for numerator, denominator in (("R", "S"), ("R-noLT", "S-noLT"),
                                       ("S", "S-noLT"), ("R", "R-noLT")):
            a, b = group[numerator], group[denominator]
            for field in (a.keys() & b.keys()) - {"rc", "valid"}:
                x, y = a[field], b[field]
                ratios[(*key[:3], numerator + "/" + denominator)][field].append(
                    x / y if x is not None and y is not None and y > 0 else None)
    paired = [dict(point=k[0], kind=k[1], gc=k[2], ratio=k[3],
                   metrics={f: _median(v) for f, v in sorted(metrics.items())})
              for k, metrics in sorted(ratios.items())]
    main_gc = {}
    for point in sorted({r["point"] for r in rows}):
        candidates = {m["gc"]: m["metrics"].get("throughput_tps") for m in medians
                      if m["point"] == point and m["kind"] == "perf" and m["arm"] == "R"
                      and m["valid_runs"] == m["runs"]}
        main_gc[point] = (max(candidates, key=lambda g: (candidates[g], -g))
                          if set(candidates) == {10, 100} and
                          all(v is not None for v in candidates.values()) else None)
    return {"medians": medians, "paired_ratios": paired, "main_gc": main_gc, "runs": rows}


def aggregate(documents: list[dict], command: str) -> dict:
    body = aggregate_smoke(documents) if command == "smoke" else aggregate_measure(documents)
    return {"schema_version": 1, "command": "aggregate", "input_command": command,
            "thresholds": {"completion_rate": MIN_COMPLETION_RATE,
                           "long_commits": MIN_LONG_COMMITS, "boundary_ratio": MIN_BOUNDARY_RATIO,
                           "boundary_us": MIN_BOUNDARY_US}, "limitation": LIMITATION, **body}


def _execute(args, plan: list[tuple], result: dict) -> None:
    site = V.site_policy.current_site(require_evidence=True)
    if V.site_policy.refuses_heavy_work(site):
        raise RuntimeError(V.site_policy.heavy_work_refusal(site, DRIVER_ID))
    V._assert_single_tenant()
    policy = V.compute._load_policy(args.policy.resolve(strict=True))
    toolchain = V.compute._resolve_toolchain(policy)
    result.update(site=site, toolchain=toolchain)
    # generic dispatch clears TMPDIR and PBS_JOBID. Identity never depends on PBS.
    with scratch_directory() as td:
        scratch = Path(td)
        started = time.monotonic()
        dependencies = V.compute._prepare_dependencies(
            ROOT, policy, args.third_party_cache.resolve(strict=True), scratch, toolchain)
        source = scratch / "source"
        V._checked(["git", "clone", "--shared", "--no-checkout", str(ROOT / "external/ccbench"), str(source)])
        V._checked(["git", "checkout", "--detach", PIN], cwd=source)
        # Generate Masstree config.h before any condition-gate preprocessing.
        _, result["dependency_stock_build"] = V._build_variant(
            source, scratch / "dependency-build", toolchain, dependencies, ())
        binaries, builds = {}, result.setdefault("builds", {})
        with V.applied(str(V.PATCH), PIN, str(source)):
            for arm in ARMS[:2]:
                if arm == "R":
                    apply_patch(str(R_PATCH), str(source))  # git apply, no fuzz
                for kind in sorted({p[2] for p in plan}):
                    binary, receipt = _build_variant(source, scratch / f"{kind}-{arm}",
                                                    toolchain, dependencies, kind, arm)
                    binaries[kind, arm] = binary
                    builds[f"{kind}-{arm}"] = receipt
        build_s = time.monotonic() - started
        result["preparation_and_build_s"] = build_s
        runs = result["runs"]
        for position, (point, arm, kind, gc, extime, round_no) in enumerate(plan):
            binary = binaries[kind, arm.split("-")[0]]
            runs.append(_run_one(binary, (point, arm, kind, gc, extime, round_no),
                                 scratch, result["started_at"], position % 4))
        if args.command == "measure":
            overhead = statistics.median(max(0, r["wall_s"] - r["extime"]) for r in runs)
            result["job_estimate"] = job_estimate(build_s, args.rounds, args.extime, overhead)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    smoke = subs.add_parser("smoke")
    smoke.add_argument("--skew", type=float, choices=(0, .3, .6), required=True)
    measure = subs.add_parser("measure")
    measure.add_argument("--point", choices=tuple(POINTS), required=True)
    measure.add_argument("--kind", choices=("perf", "diag"), required=True)
    measure.add_argument("--gc", type=int, choices=(10, 100), required=True)
    measure.add_argument("--rounds", type=int, required=True)
    measure.add_argument("--extime", type=int, required=True)
    agg = subs.add_parser("aggregate")
    inputs = agg.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--smoke", type=Path, nargs="+")
    inputs.add_argument("--measure", type=Path, nargs="+")
    for sub in (smoke, measure, agg):
        sub.add_argument("--out", type=Path, required=True)
    for sub in (smoke, measure):
        sub.add_argument("--third-party-cache", type=Path,
                         default=Path("/work/1/SFC/tanab/izanagi-thirdparty-cache"))
        sub.add_argument("--policy", type=Path, default=ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    result = {"schema_version": 1, "command": args.command, "ccbench_commit": PIN,
              "hostname": socket.gethostname(), "started_at": now(), "limitation": LIMITATION,
              "patches": [{"name": p.name, "sha256": sha(p)} for p in (V.PATCH, R_PATCH)], "runs": []}
    try:
        if args.command == "aggregate":
            result = aggregate([json.loads(p.read_text()) for p in (args.smoke or args.measure)],
                               "smoke" if args.smoke else "measure")
        else:
            plan = smoke_plan(args.skew) if args.command == "smoke" else measure_plan(
                args.point, args.kind, args.gc, args.rounds, args.extime)
            _execute(args, plan, result)
            if not all(r["summary"]["valid"] for r in result["runs"]):
                result["error"] = "one or more runs failed"
    except Exception as exc:
        result.update(V._stage_error(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
