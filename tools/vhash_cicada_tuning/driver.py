"""Compute-node diagnostic Cicada runner and deterministic job planner.

Cicada does not print ShowOptParameters. Compile commands and the binary SHA256
bind each build; FLAGS lines bind each run's runtime arguments. These runs are
not correctness certified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import concurrent.futures
import hashlib
import json
import math
import os
import random
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from orchestrator.campaign import patchharness, pin, site_policy
from orchestrator.campaign.model import cmake_cache_variable_for_axis
from orchestrator.calibrator import benchparse, perfparse, runner
from orchestrator.holdout_observation import assert_holdout_observation_admitted

from . import analysis, model

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output/env/pegasus/vhash-cicada-baseline-tuning"
SCHEMA = "vhash-cicada-diagnostic/v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _check_site() -> None:
    if site_policy.current_site(require_evidence=True) != site_policy.PEGASUS_COMPUTE:
        raise RuntimeError("Cicada measurement requires evidenced Pegasus compute node")


def _check_solo() -> None:
    competitors = runner.competing_bench_pids()
    if competitors:
        raise RuntimeError(f"competing benchmark processes: {competitors}")


def check_compile_commands(commands: list[dict], genome: dict, wait: bool) -> dict:
    """Check every Cicada TU command in the exported ycsb_cicada build."""
    expected = {"TRACE": 0, "ADD_ANALYSIS": 0, **genome,
                "WORKER1_INSERT_DELAY_RPHASE": int(wait)}
    if wait:
        expected["WORKER1_INSERT_DELAY_RPHASE_US"] = 1000
    checked = []
    for entry in commands:
        path = Path(entry.get("file", "")).as_posix()
        if not re.search(r"/cc/cicada/(transaction|util|ycsb_cicada)\.cc$", path):
            continue
        argv = entry.get("arguments") or shlex.split(entry.get("command", ""))
        defines = {}
        for token in argv:
            if token.startswith("-D"):
                key, sep, value = token[2:].partition("=")
                if key in defines:
                    raise ValueError(f"duplicate compile define: {key}")
                defines[key] = value if sep else "1"
        for key, value in expected.items():
            if defines.get(key) != str(value):
                raise ValueError(f"compile command mismatch: {path} {key}")
        if not wait and defines.get("WORKER1_INSERT_DELAY_RPHASE_US") not in (None, "0"):
            raise ValueError("normal build contains wait duration")
        checked.append(path)
    if {Path(path).name for path in checked} != {"transaction.cc", "util.cc", "ycsb_cicada.cc"}:
        raise ValueError("Cicada translation units missing from compile_commands")
    return {"checked_tus": checked, "expected_defines": expected, "valid": True}


def check_flags(stdout: str, argv: list[str]) -> list[str]:
    expected = {arg[1:].split("=", 1)[0]: arg.split("=", 1)[1] for arg in argv}
    required = {"thread_num", "gc_inter_us", "extime", "clocks_per_us",
                "ycsb_tuple_num", "ycsb_zipf_skew", "ycsb_rratio",
                "ycsb_rmw", "ycsb_max_ope"}
    lines = [line for line in stdout.splitlines() if line.startswith("#FLAGS_")]
    observed = {}
    for line in lines:
        match = re.fullmatch(r"#FLAGS_([a-z0-9_]+):\s*(\S+)\s*", line)
        if match:
            if match[1] in observed:
                raise ValueError(f"duplicate FLAGS field: {match[1]}")
            observed[match[1]] = match[2]
    for key in required:
        if key not in observed or key not in expected:
            raise ValueError(f"missing FLAGS field: {key}")
        if float(observed[key]) != float(expected[key]):
            raise ValueError(f"FLAGS mismatch: {key}")
    return lines


def make_spec(stage: str, records: dict[str, int], *, seed: int = 20260929,
              k: int = 3, gc_grid: tuple[int, ...] = (1, 10, 100, 1000, 10000),
              reps: int = 3, workloads: tuple[str, ...] = ("W1", "W2", "W3", "W4", "W5"),
              selected: dict[str, list[dict]] | None = None,
              build_parallelism: int = 1, job_prefix: str = "cicada") -> list[dict]:
    if stage not in {"j1", "j2"} or reps < 1 or k < 1 or build_parallelism < 1:
        raise ValueError("invalid spec controls")
    if any(w not in model.WORKLOADS for w in workloads) or any(records.get(w, 0) <= 0 for w in workloads):
        raise ValueError("all selected workloads need calibrated records")
    if any(gc <= 0 for gc in gc_grid) or 10 not in gc_grid:
        raise ValueError("GC grid must contain positive GC=10")
    all_genomes = model.genomes()
    jobs = []
    if stage == "j1":
        for index in range(4):
            subset = all_genomes[index * 6:(index + 1) * 6]
            conditions = []
            for g in dict.fromkeys(model.canonical(x) for x in [*subset, model.CONTROL]):
                flags = next(x for x in [*subset, model.CONTROL] if model.canonical(x) == g)
                for w in workloads:
                    if w not in {"W1", "W2", "W3", "W4"}:
                        continue
                    for gc in ((10, 100, 1000) if w == "W2" else (10,)):
                        conditions.append({"genome": flags, "workload": w, "records": records[w], "gc_inter_us": gc})
            jobs.append(_assemble_job(f"{job_prefix}-j1-{index}", "j1", conditions, reps,
                                      seed + index, build_parallelism))
    else:
        if selected is None:
            raise ValueError("J2 needs J1-selected genomes")
        for index, w in enumerate(workloads):
            source = "W2" if w == "W5" else w
            candidates = selected.get(source)
            if candidates is None:
                raise ValueError(f"missing selected genomes for {source}")
            candidates = [model.parse_canonical(g) if isinstance(g, str) else g for g in candidates]
            for g in candidates:
                model.validate_genome(g)
            genomes = list({model.canonical(g): g for g in [*candidates[:k], model.CONTROL]}.values())
            grid = (10, 100, 1000) if w == "W5" else gc_grid
            conditions = [{"genome": g, "workload": w, "records": records[w], "gc_inter_us": gc}
                          for g in genomes for gc in grid]
            if w == "W2" and records[w] != 1_000_000:
                conditions += [{"genome": g, "workload": w, "records": 1_000_000, "gc_inter_us": gc}
                               for g in genomes for gc in (10, 100, 1000)]
            jobs.append(_assemble_job(f"{job_prefix}-j2-{index}", "j2", conditions, reps,
                                      seed + index, build_parallelism))
    return jobs


def _assemble_job(job_id: str, stage: str, conditions: list[dict], reps: int,
                  seed: int, build_parallelism: int) -> dict:
    runs = []
    for rep in range(reps):
        batch = [dict(condition, stage=stage, rep=rep, perf=False) for condition in conditions]
        random.Random(seed + rep * 1009).shuffle(batch)
        runs.extend(batch)
    builds = list({(model.canonical(c["genome"]), model.WORKLOADS[c["workload"]].wait):
                   {"genome": c["genome"], "wait": model.WORKLOADS[c["workload"]].wait}
                  for c in conditions}.values())
    return {"schema": SCHEMA, "job_id": job_id, "stage": stage,
            "build_parallelism": build_parallelism, "builds": builds, "runs": runs}


def _prepare_toolchain(cache_root: Path, scratch: Path) -> tuple[dict, dict]:
    """Keep the two mocc private helpers in one boundary.

    Pegasus policy owns third-party pins; the existing mocc policy supplies
    only compiler-version digests. Its older CCBench pin is never used here.
    """
    from orchestrator.campaign import s3_mocc_lock_coverage as helpers

    policy = json.loads((ROOT / "tools/pegasus/policy.json").read_text())
    compiler_policy = json.loads((ROOT / "tools/pegasus/mocc_trace_v1_policy.json").read_text())
    expected = compiler_policy.get("expected_compiler_version_body_sha256")
    if not isinstance(expected, dict) or set(expected) != {"gcc", "g++"}:
        raise RuntimeError("compiler policy missing")
    dependencies = (policy.get("silo_ladder_rung1") or {}).get("dependency_pins")
    if dependencies != {"gflags": policy.get("gflags_expected_head"),
                        "glog": policy.get("glog_expected_head")}:
        raise RuntimeError("third-party pin policy mismatch")
    toolchain = helpers._resolve_toolchain({**policy,
                                           "expected_compiler_version_body_sha256": expected})
    sources = helpers._prepare_dependencies(ROOT, policy, cache_root, scratch, toolchain)
    return toolchain, sources


def _build(source: Path, scratch: Path, dependency: dict, toolchain: dict,
           build_spec: dict, jobs: int) -> tuple[dict, Path]:
    genome = build_spec["genome"]
    model.validate_genome(genome)
    wait = build_spec["wait"]
    label = digest((model.canonical(genome) + str(wait)).encode())[:12]
    build_dir = scratch / f"build-{label}"
    args = ["cmake", "-S", str(source), "-B", str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
            "-DCCBENCH_CCACHE=OFF", "-DCCBENCH_TRACE=0", "-DCCBENCH_ADD_ANALYSIS=0",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            f"-DCMAKE_C_COMPILER={toolchain['cc_path']}",
            f"-DCMAKE_CXX_COMPILER={toolchain['cxx_path']}",
            "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
            "-DCMAKE_TOOLCHAIN_FILE=",
            f"-DCMAKE_PREFIX_PATH={dependency['gflags']};{dependency['glog']}",
            *(f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}={dependency[name]}"
              for name in ("masstree", "mimalloc", "googletest")),
            *(f"-D{cmake_cache_variable_for_axis('cicada', key)}={value}"
              for key, value in sorted(genome.items())),
            f"-DCCBENCH_WORKER1_INSERT_DELAY_RPHASE={int(wait)}",
            "-DCMAKE_CXX_FLAGS=-DWORKER1_INSERT_DELAY_RPHASE_US=1000" if wait
            else "-DCMAKE_CXX_FLAGS="]
    start = time.monotonic()
    subprocess.run(args, check=True, capture_output=True, text=True, timeout=600)
    subprocess.run(["cmake", "--build", str(build_dir), "--target", "ycsb_cicada.exe",
                    "-j", str(jobs)], check=True, capture_output=True, text=True,
                   timeout=900)
    seconds = time.monotonic() - start
    commands = json.loads((build_dir / "compile_commands.json").read_text())
    binding = check_compile_commands(commands, genome, wait)
    binary = build_dir / "cc/cicada/ycsb_cicada.exe"
    if not binary.is_file():
        found = list(build_dir.rglob("ycsb_cicada.exe"))
        if len(found) != 1:
            raise RuntimeError("built binary missing or ambiguous")
        binary = found[0]
    record = {"genome": model.canonical(genome), "wait": wait,
              "binary_sha256": digest(binary.read_bytes()), "build_seconds": seconds,
              "compile_command_binding": binding, "configure_argv": args,
              "build_jobs": jobs}
    return record, binary


def _run_one(run: dict, binary: Path, binary_sha: str, output_dir: Path,
             job_id: str, previous: str | None, host: str) -> dict:
    _check_site()
    _check_solo()
    workload = model.WORKLOADS[run["workload"]]
    if run["stage"] not in {"j0_smoke", "j0_calibration", "j0_within", "j1", "j2"}:
        raise ValueError("unknown run stage")
    if run["perf"] and run["stage"] != "j0_calibration":
        raise ValueError("perf is calibration-only")
    gflags = model.runtime_argv(workload, run["records"], run["gc_inter_us"],
                                threads=run.get("threads", model.THREADS))
    assert_holdout_observation_admitted(gflags=gflags, admission=None, use_perf=run["perf"])
    run_id = f"{len(list(output_dir.glob('run-*.stdout'))):05d}"
    argv = [str(binary), *gflags]
    perf_path = output_dir / f"run-{run_id}.perf.csv"
    if run["perf"]:
        argv = ["perf", "stat", "-x,", "-e", "LLC-loads,LLC-load-misses",
                "-o", str(perf_path), "--", *argv]
    started = now()
    load = os.getloadavg()
    start = time.monotonic()
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=180, check=False)
    elapsed = time.monotonic() - start
    stdout, stderr = completed.stdout, completed.stderr
    (output_dir / f"run-{run_id}.stdout").write_text(stdout)
    (output_dir / f"run-{run_id}.stderr").write_text(stderr)
    if completed.returncode:
        raise RuntimeError(f"run {run_id} returned {completed.returncode}")
    flags = check_flags(stdout, gflags)
    metrics = benchparse.parse_bench_stdout(stdout)
    if "throughput[tps]" not in metrics:
        raise ValueError("throughput[tps] missing")
    tps = float(metrics["throughput[tps]"])
    if not math.isfinite(tps) or tps <= 0:
        raise ValueError("nonfinite or nonpositive throughput[tps]")
    aborts, commits = benchparse.integer_abort_commit_counts(metrics)
    rss = metrics.get("maxrss") or metrics.get("maxrss_kb")
    if rss is None:
        raise ValueError("maxrss missing")
    miss_rate = None
    perf_raw = None
    if run["perf"]:
        perf_raw = perf_path.read_text()
        miss_rate = perfparse.parse_perf_stat(perf_raw).llc_miss_rate
    return {"schema": SCHEMA, "job_id": job_id, "run_id": run_id,
            "stage": run["stage"], "rep": run["rep"],
            "genome": model.canonical(run["genome"]), "genome_flags": run["genome"],
            "workload": workload.name, "workload_flags": {
                "ycsb_rratio": workload.rratio, "ycsb_max_ope": workload.max_ope,
                "ycsb_zipf_skew": model.SKEW, "ycsb_rmw": model.RMW,
                "thread_num": run.get("threads", model.THREADS),
                "extime": model.EXTIME, "clocks_per_us": model.CLOCKS_PER_US,
                "wait": workload.wait},
            "records": run["records"], "gc_inter_us": run["gc_inter_us"],
            "perf": run["perf"], "perf_raw": perf_raw, "miss_rate": miss_rate,
            "throughput_tps": tps, "abort_rate": aborts / (aborts + commits),
            "commit_count": commits, "abort_count": aborts, "maxrss_kb": int(float(rss.split()[0])),
            "host": host, "started_utc": started, "elapsed_seconds": elapsed,
            "submission_cluster": run.get("submission_cluster", job_id),
            "load_average": load, "previous_run_id": previous,
            "binary_sha256": binary_sha, "argv": argv, "exit_code": completed.returncode,
            "show_opt_raw": None, "flags_raw": flags,
            "stdout_sha256": digest(stdout.encode()), "stderr_sha256": digest(stderr.encode())}


def _validate_spec(spec: dict) -> None:
    if spec.get("schema") != SCHEMA or spec.get("stage") not in {"j0", "j1", "j2"}:
        raise ValueError("invalid job schema/stage")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,80}", spec.get("job_id", "")):
        raise ValueError("unsafe job id")
    if not isinstance(spec.get("builds"), list) or not isinstance(spec.get("runs"), list):
        raise ValueError("builds and runs required")
    if not 1 <= spec.get("build_parallelism", 0) <= 8:
        raise ValueError("invalid build parallelism")
    for build in spec["builds"]:
        model.validate_genome(build["genome"])
        if type(build["wait"]) is not bool:
            raise ValueError("wait must be bool")
    for run in spec["runs"]:
        model.validate_genome(run["genome"])
        if spec["stage"] != "j0" and run["stage"] != spec["stage"]:
            raise ValueError("run stage differs from job stage")
        if run["workload"] not in model.WORKLOADS:
            raise ValueError("unknown workload")
        if spec["stage"] == "j1" and run["workload"] == "W5":
            raise ValueError("W5 is not screened in J1")
        if type(run["perf"]) is not bool or (run["perf"] and run["stage"] != "j0_calibration"):
            raise ValueError("perf run outside J0 calibration")
        model.runtime_argv(model.WORKLOADS[run["workload"]], run["records"], run["gc_inter_us"],
                           threads=run.get("threads", model.THREADS))
    if spec["stage"] != "j0":
        built = {(model.canonical(b["genome"]), b["wait"]) for b in spec["builds"]}
        if len(built) != len(spec["builds"]):
            raise ValueError("duplicate build")
        for run in spec["runs"]:
            key = (model.canonical(run["genome"]), model.WORKLOADS[run["workload"]].wait)
            if key not in built:
                raise ValueError(f"missing build for run: {key}")


def _l3_bytes() -> int:
    paths = sorted(Path("/sys/devices/system/cpu/cpu0/cache").glob("index*/size"))
    for path in paths:
        if (path.parent / "level").read_text().strip() == "3":
            match = re.fullmatch(r"(\d+)([KMG])", path.read_text().strip())
            if match:
                return int(match[1]) * {"K": 1024, "M": 1024**2, "G": 1024**3}[match[2]]
    raise RuntimeError("L3 cache size unavailable")


def _j0_runs() -> list[dict]:
    return [{"stage": "j0_smoke", "rep": rep, "genome": model.CONTROL,
             "workload": "W5" if wait else "W2", "records": 1_000_000,
             "gc_inter_us": 10, "threads": 2, "perf": False}
            for rep in range(3) for wait in (False, True)]


def execute(spec_path: Path, cache_root: Path, scratch_root: Path) -> Path:
    _check_site()
    _check_solo()
    spec_bytes = spec_path.read_bytes()
    spec = json.loads(spec_bytes)
    _validate_spec(spec)
    output_dir = Path(spec.get("out_dir", OUTPUT / spec["job_id"]))
    if output_dir.resolve() != (OUTPUT / spec["job_id"]).resolve():
        raise ValueError("out_dir must be the job's diagnostic output path")
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "runs.jsonl").open("x").close()
    started = now()
    host = socket.gethostname()
    manifest = {"schema": SCHEMA, "job_id": spec["job_id"], "stage": spec["stage"],
                "spec_sha256": digest(spec_bytes), "host": host, "started_utc": started,
                "status": "failed", "builds": []}
    rows = []
    try:
        with tempfile.TemporaryDirectory(dir=scratch_root, prefix="cicada-") as tmp:
            scratch = Path(tmp)
            prep_start = time.monotonic()
            toolchain, dependencies = _prepare_toolchain(cache_root, scratch)
            manifest["dependencies_seconds"] = time.monotonic() - prep_start
            manifest["toolchain"] = toolchain
            with patchharness.checkout(pin.CURRENT_PIN,
                                       base_dir=str(ROOT / "external/ccbench")) as checkout:
                source = Path(checkout)
                head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                                      capture_output=True, text=True, check=True).stdout.strip()
                manifest["ccbench_head"] = head
                builds = list(spec["builds"])
                if spec["stage"] == "j0":
                    builds = [{"genome": model.CONTROL, "wait": False},
                              {"genome": model.CONTROL, "wait": True}]
                build_jobs = max(1, (os.cpu_count() or 1) // spec["build_parallelism"])
                with concurrent.futures.ThreadPoolExecutor(max_workers=spec["build_parallelism"]) as pool:
                    results = list(pool.map(lambda b: _build(source, scratch, dependencies, toolchain,
                                                              b, build_jobs), builds))
                binaries = {}
                for build, (record, binary) in zip(builds, results):
                    manifest["builds"].append(record)
                    binaries[(model.canonical(build["genome"]), build["wait"])] = (binary, record["binary_sha256"])
                settled = runner.settle(timeout_s=180.0)
                manifest["settle"] = settled

                def take(run: dict) -> dict:
                    run = {**run, "submission_cluster": spec.get("submission_cluster", spec["job_id"])}
                    key = (model.canonical(run["genome"]), model.WORKLOADS[run["workload"]].wait)
                    if key not in binaries:
                        raise ValueError(f"run build missing: {key}")
                    binary, sha = binaries[key]
                    row = _run_one(run, binary, sha, output_dir, spec["job_id"],
                                   rows[-1]["run_id"] if rows else None, host)
                    rows.append(row)
                    with (output_dir / "runs.jsonl").open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(row, sort_keys=True) + "\n")
                    return row

                if spec["stage"] != "j0":
                    for run in spec["runs"]:
                        take(run)
                else:
                    _execute_j0(take, manifest)
        manifest["status"] = "complete"
    finally:
        manifest["finished_utc"] = now()
        (output_dir / "job-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return output_dir


def _execute_j0(take, manifest: dict) -> None:
    from orchestrator.calibrator.perf_preflight import probe_perf_availability

    for run in _j0_runs():
        take(run)
    rows_path = OUTPUT / manifest["job_id"] / "runs.jsonl"
    smoke = [json.loads(line) for line in rows_path.read_text().splitlines()]
    normal = [r["throughput_tps"] for r in smoke if r["workload"] == "W2"]
    delayed = [r["throughput_tps"] for r in smoke if r["workload"] == "W5"]
    manifest["wait_smoke"] = analysis.wait_alive(normal, delayed)
    policy = json.loads((ROOT / "tools/pegasus/policy.json").read_text())
    preflight = probe_perf_availability(perf_candidates=policy.get("perf_candidates", []))
    manifest["perf_preflight"] = preflight
    perf = bool(preflight.get("available"))
    l3 = _l3_bytes()
    manifest["l3_bytes"] = l3
    manifest["l3_expected_bytes"] = model.L3_BYTES_EXPECTED
    chosen = {}
    for workload in ("W1", "W2", "W3", "W4"):
        points = []
        for records in (1_000_000, 2_000_000, 4_000_000, 8_000_000):
            reps = [take({"stage": "j0_calibration", "rep": rep,
                          "genome": model.CONTROL, "workload": workload,
                          "records": records, "gc_inter_us": 10, "perf": perf})
                    for rep in range(3)]
            miss = [r["miss_rate"] for r in reps if r["miss_rate"] is not None]
            points.append({"records": records, "maxrss_kb": max(r["maxrss_kb"] for r in reps),
                           "miss_rate": (sorted(miss)[len(miss)//2] if len(miss) == 3 else None)})
            if len(points) >= 3:
                choice = analysis.choose_records(points, l3)
                if choice["reason"] == "observed_saturation_candidate" and choice["records"] < records:
                    break
                if choice["reason"].startswith("D15_RSS") and choice["records"] is not None:
                    break
        chosen[workload] = analysis.choose_records(points, l3)
        if chosen[workload]["records"] is None:
            raise RuntimeError(f"J0 records undetermined for {workload}")
    chosen["W5"] = dict(chosen["W2"])
    manifest["chosen_records"] = chosen
    for workload in model.WORKLOADS:
        if workload == "W5" and not manifest["wait_smoke"]["alive"]:
            continue
        for rep in range(10):
            take({"stage": "j0_within", "rep": rep, "genome": model.CONTROL,
                  "workload": workload, "records": chosen[workload]["records"],
                  "gc_inter_us": 10, "perf": False})
    rows = [json.loads(line) for line in rows_path.read_text().splitlines()]
    manifest["run_seconds_by_workload"] = {
        w: sorted(r["elapsed_seconds"] for r in rows if r["workload"] == w
                  and r["stage"] == "j0_within")[
            len([r for r in rows if r["workload"] == w and r["stage"] == "j0_within"]) // 2]
        for w in model.WORKLOADS if any(r["workload"] == w and r["stage"] == "j0_within" for r in rows)}


def read_runs(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row.get("schema") != SCHEMA:
                raise ValueError(f"unknown run schema in {path}")
            rows.append(row)
    keys = [(r["job_id"], r["run_id"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate run id")
    return rows


def _require_planned_runs(rows: list[dict], specs: list[Path]) -> None:
    if not any(r["stage"] in {"j1", "j2"} for r in rows):
        return
    if not specs:
        raise ValueError("J1/J2 analysis requires job specs for missing-run detection")
    def key(run, job_id):
        genome = run["genome"] if isinstance(run["genome"], str) else model.canonical(run["genome"])
        return (job_id, run["stage"], run["rep"], genome, run["workload"],
                run["records"], run["gc_inter_us"], run["perf"])
    planned = Counter(key(run, spec["job_id"])
                      for path in specs for spec in [json.loads(path.read_text())]
                      for run in spec["runs"] if run["stage"] in {"j1", "j2"})
    actual = Counter(key(run, run["job_id"]) for run in rows if run["stage"] in {"j1", "j2"})
    if planned != actual:
        raise ValueError("J1/J2 runs differ from preregistered job specs")


def analyze(paths: list[Path], k: int = 3, costs_path: Path | None = None,
            specs: list[Path] = ()) -> dict:
    rows = read_runs(paths)
    _require_planned_runs(rows, specs)
    j0_manifests = [p.parent / "job-manifest.json" for p in paths
                    if any(r["stage"].startswith("j0_") and r["job_id"] == p.parent.name
                           for r in rows)]
    l3 = model.L3_BYTES_EXPECTED
    for path in j0_manifests:
        if path.is_file():
            l3 = json.loads(path.read_text()).get("l3_bytes", l3)
            break
    j0 = [r for r in rows if r["stage"].startswith("j0_")]
    summary = {"schema": SCHEMA, "diagnostic_only": True,
               "correctness_verified": False, "official_cicada_floor": "not_obtained",
               "l3_bytes": l3,
               "input_runs": [str(p) for p in paths], "calibration": {},
               "selected_j1": analysis.select_j1(rows, k), "control_cv": {},
               "within_run_cv": {}, "j2": {}}
    for workload in model.WORKLOADS:
        points = []
        for n in sorted({r["records"] for r in j0 if r["stage"] == "j0_calibration" and r["workload"] == workload}):
            reps = [r for r in j0 if r["stage"] == "j0_calibration" and
                    r["workload"] == workload and r["records"] == n]
            miss = [r["miss_rate"] for r in reps if r["miss_rate"] is not None]
            points.append({"records": n, "maxrss_kb": max(r["maxrss_kb"] for r in reps),
                           "miss_rate": sorted(miss)[len(miss)//2] if len(miss) == 3 else None})
        if workload == "W5":
            summary["calibration"][workload] = summary["calibration"].get("W2", {})
        else:
            summary["calibration"][workload] = analysis.choose_records(points, l3)
        n = summary["calibration"][workload].get("records")
        if n:
            within = [r["throughput_tps"] for r in j0 if r["stage"] == "j0_within"
                      and r["workload"] == workload and r["records"] == n and not r["perf"]]
            if within:
                summary["within_run_cv"][workload] = analysis.sample_cv(within)
            cv = analysis.control_cv(rows, workload, n)
            summary["control_cv"][workload] = cv
            planned = [json.loads(p.read_text()) for p in specs]
            expected = {(model.canonical(r["genome"]), r["gc_inter_us"])
                        for spec in planned for r in spec["runs"]
                        if spec["stage"] == "j2" and r["workload"] == workload
                        and r["records"] == n}
            planned_reps = {r["rep"] for spec in planned for r in spec["runs"]
                            if spec["stage"] == "j2" and r["workload"] == workload
                            and r["records"] == n}
            observed = sorted(expected or {(r["genome"], r["gc_inter_us"]) for r in rows
                                           if r["stage"] == "j2" and r["workload"] == workload
                                           and r["records"] == n})
            if observed:
                summary["j2"][workload] = analysis.j2_best(rows, workload, cv["cv"],
                                                               observed, cv["session_count"], records=n,
                                                               expected_reps=len(planned_reps) or 3)
    normal = [r["throughput_tps"] for r in j0 if r["stage"] == "j0_smoke" and r["workload"] == "W2"]
    delayed = [r["throughput_tps"] for r in j0 if r["stage"] == "j0_smoke" and r["workload"] == "W5"]
    if normal and delayed:
        summary["wait_smoke"] = analysis.wait_alive(normal, delayed)
    rr50_n = summary["calibration"].get("W2", {}).get("records")
    if rr50_n and rr50_n != 1_000_000:
        common = {}
        for r in rows:
            if (r["stage"] == "j2" and r["workload"] == "W2" and
                    r["records"] == 1_000_000 and r["perf"] is False):
                common.setdefault(f"{r['genome']}|{r['gc_inter_us']}", []).append(r["throughput_tps"])
        if common:
            import statistics
            summary["rr50_common_1m_diagnostic_tps"] = {
                key: statistics.median(values) for key, values in common.items()}
    costs = json.loads(costs_path.read_text()) if costs_path else None
    if costs is None:
        for manifest_path in j0_manifests:
            if manifest_path.is_file():
                manifest = json.loads(manifest_path.read_text())
                builds = {"build_wait_s" if b["wait"] else "build_normal_s": b["build_seconds"]
                          for b in manifest["builds"]}
                costs = {"dependencies_s": manifest["dependencies_seconds"],
                         "run_s": manifest["run_seconds_by_workload"], **builds}
                break
    if costs and specs:
        summary["estimated_walltime_minutes"] = {
            json.loads(p.read_text())["job_id"]: analysis.estimate_walltime(json.loads(p.read_text()), costs)
            for p in specs}
    if costs:
        summary["j0_unit_costs_seconds"] = costs
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "j0"):
        command = sub.add_parser(name)
        command.add_argument("--spec", type=Path, required=True)
        command.add_argument("--third-party-cache", type=Path, required=True)
        command.add_argument("--scratch-root", type=Path, required=True)
    make = sub.add_parser("make-spec")
    make.add_argument("--stage", choices=("j1", "j2"), required=True)
    make.add_argument("--records", type=Path, required=True)
    make.add_argument("--selected", type=Path)
    make.add_argument("--out-dir", type=Path, required=True)
    make.add_argument("--seed", type=int, default=20260929)
    make.add_argument("--k", type=int, default=3)
    make.add_argument("--gc-grid", type=int, nargs="+", default=(1, 10, 100, 1000, 10000))
    make.add_argument("--reps", type=int, default=3)
    make.add_argument("--workloads", nargs="+", default=("W1", "W2", "W3", "W4", "W5"))
    make.add_argument("--build-parallelism", type=int, default=1)
    make.add_argument("--job-prefix", default="cicada")
    report = sub.add_parser("analyze")
    report.add_argument("--runs", nargs="+", type=Path, required=True)
    report.add_argument("--summary", type=Path, required=True)
    report.add_argument("--k", type=int, default=3)
    report.add_argument("--costs", type=Path)
    report.add_argument("--specs", nargs="*", type=Path, default=[])
    args = parser.parse_args(argv)
    if args.command in {"run", "j0"}:
        spec = json.loads(args.spec.read_text())
        allowed = {"j0"} if args.command == "j0" else {"j1", "j2"}
        if spec.get("stage") not in allowed:
            parser.error("subcommand and spec stage differ")
        print(execute(args.spec, args.third_party_cache, args.scratch_root))
    elif args.command == "make-spec":
        records = json.loads(args.records.read_text())
        selected = json.loads(args.selected.read_text()) if args.selected else None
        if selected and "selected_j1" in selected:
            selected = selected["selected_j1"]
        jobs = make_spec(args.stage, records, seed=args.seed, k=args.k,
                         gc_grid=tuple(args.gc_grid), reps=args.reps,
                         workloads=tuple(args.workloads), selected=selected,
                         build_parallelism=args.build_parallelism, job_prefix=args.job_prefix)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for spec in jobs:
            path = args.out_dir / f"{spec['job_id']}.json"
            with path.open("x", encoding="utf-8") as handle:
                json.dump(spec, handle, indent=2, sort_keys=True)
                handle.write("\n")
            print(path)
    else:
        summary = analyze(args.runs, args.k, args.costs, args.specs)
        with args.summary.open("x", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
