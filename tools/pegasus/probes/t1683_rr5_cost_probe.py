#!/usr/bin/env python3
"""One-shot full-scale rr5 trace and verifier cost measurement."""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import buildcache, env_contract, site_policy, source_digest  # noqa: E402
from orchestrator.campaign.build_admission import GeneratorId, build_run_context, derive_build_admission  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.p2_2 import _assert_single_tenant  # noqa: E402
from orchestrator.campaign.patchharness import assert_pinned_clean  # noqa: E402
from orchestrator.campaign.s2_verify_calibration import _parse_abort_counts, _parse_commit_witness  # noqa: E402

CONTRACT = env_contract.lookup("pegasus"); ENV_TAG = CONTRACT.env_tag
CLOCKS_PER_US = CONTRACT.clocks_per_us; NUMA = list(CONTRACT.numactl)
RUN_TIMEOUT_S = 900.0; VERIFIER_TIMEOUT_S = 7200.0; MIN_FREE_DISK_GB = 60.0
DEFAULT_OUT = Path("output/env/pegasus/calibration/a2_perf_verify_cost_t48_skew0p9_rr5_rmw0.json")
WORKLOAD_ARGV = ["-thread_num=48", "-ycsb_tuple_num=1000000", "-ycsb_zipf_skew=0.9", "-ycsb_rratio=5", "-ycsb_rmw=0", "-ycsb_max_ope=10", "-extime=3", f"-clocks_per_us={CLOCKS_PER_US}"]
DEFINE_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0, "BACKOFF_NOINLINE": 0}
GENOMES = [("rr5-stock", {**DEFINE_BASE, "BACK_OFF": 0, "BACKOFF_FIXED": -1}), ("rr5-fixed10", {**DEFINE_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 10})]

def _current_pin(submodule: Path) -> str:
    return subprocess.run(["git", "-C", str(submodule), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()

def _assert_free_disk(path: str) -> float:
    free_gb = shutil.disk_usage(path).free / 2**30
    if free_gb < MIN_FREE_DISK_GB: raise RuntimeError(f"free disk {free_gb:.1f}GB < {MIN_FREE_DISK_GB:.1f}GB at {path}")
    return free_gb

def _run_argv(binary: str) -> list[str]:
    return NUMA + [binary] + list(WORKLOAD_ARGV)

def _trace_stats(trace_dir: str) -> dict[str, int]:
    files = sorted(Path(trace_dir).glob("trace_*.log")); lines = 0
    for path in files:
        with path.open("rb") as stream: lines += sum(1 for _ in stream)
    return {"files": len(files), "bytes": sum(p.stat().st_size for p in files), "lines": lines}

def _run_once(binary: str) -> tuple[dict, str]:
    trace_dir = tempfile.mkdtemp(prefix="izanagi_t1683_rr5_trace_"); env = dict(os.environ)
    env["IZANAGI_TRACE_DIR"] = trace_dir; os.makedirs(os.path.join(trace_dir, "log"), exist_ok=True); started = time.monotonic()
    try:
        proc = subprocess.run(_run_argv(binary), cwd=trace_dir, env=env, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
        wall = time.monotonic() - started
        if proc.returncode != 0: raise RuntimeError(f"trace run rc={proc.returncode}: {proc.stderr[-400:]}")
        commits, batch_commits = _parse_commit_witness(proc.stdout); aborts = _parse_abort_counts(proc.stdout)
        if commits is None or batch_commits is None or aborts is None: raise RuntimeError("trace run stdout lacks valid commit/abort witnesses")
        if batch_commits != 0: raise RuntimeError("batch_commit_counts_ is nonzero")
        stats = _trace_stats(trace_dir)
        if stats["files"] == 0: raise RuntimeError("trace run produced no trace_*.log files")
        run = {"exit_code": proc.returncode, "wall_seconds": wall, "commits": commits, "batch_commits": batch_commits, "aborts": aborts, "abort_rate": aborts / (commits + aborts) if commits + aborts else None, "trace": stats}
        return run, trace_dir
    except BaseException:
        shutil.rmtree(trace_dir, ignore_errors=True); raise

def _verifier_run(trace_dir: str, expected_commits: int) -> dict:
    argv = ["/usr/bin/time", "-v", sys.executable, "-m", "verifier", trace_dir, "--json", "--quiet", "--expected-commits", str(expected_commits)]
    env = dict(os.environ); env["LC_ALL"] = "C"; started = time.monotonic()
    proc = subprocess.run(argv, cwd=ROOT / "orchestrator", env=env, capture_output=True, text=True, timeout=VERIFIER_TIMEOUT_S); wall = time.monotonic() - started
    rss = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", proc.stderr)
    if rss is None: raise RuntimeError(f"verifier peak RSS is missing: {proc.stderr[-400:]}")
    try:
        result = json.loads(proc.stdout)["results"][0]
        return {"exit_code": proc.returncode, "wall_seconds": wall, "peak_rss_kb": int(rss.group(1)), "verdict": result["verdict"], "certified": result["certified"], "total_cycles": result["total_cycles"], "txns": result["stats"]["txns"], "edges": result["stats"]["edges"]}
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"cannot parse verifier output rc={proc.returncode}: {proc.stdout[:300]}") from exc

def _dry_run(out: Path, pin: str, cc: str, cxx: str) -> dict:
    genomes = [{"id": name, "defines": defines, "run_argv": _run_argv("<trace-enabled-ycsb_silo.exe>")} for name, defines in GENOMES]
    verifier = ["/usr/bin/time", "-v", sys.executable, "-m", "verifier", "<trace-dir>", "--json", "--quiet", "--expected-commits", "<commits>"]
    return {"mode": "dry-run", "env_tag": ENV_TAG, "ccbench_commit": pin, "cc": cc, "cxx": cxx, "output": str(out), "output_exists": out.exists(), "timeouts_seconds": {"run": RUN_TIMEOUT_S, "verifier": VERIFIER_TIMEOUT_S}, "minimum_free_disk_gb": MIN_FREE_DISK_GB, "numactl": NUMA, "workload_argv": WORKLOAD_ARGV, "genomes": genomes, "verifier_argv": verifier}

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--out", default=str(DEFAULT_OUT)); parser.add_argument("--dry-run", action="store_true"); args = parser.parse_args()
    out = Path(args.out); out = out if out.is_absolute() else ROOT / out
    submodule = ROOT / "external" / "ccbench"; pin = _current_pin(submodule)
    cc, cxx = buildcache.compilers_for_current_site()
    if args.dry_run: print(json.dumps(_dry_run(out, pin, cc, cxx), indent=2, ensure_ascii=False)); return 0
    if out.exists(): raise FileExistsError(f"refusing to overwrite existing output: {out}")
    site = site_policy.current_site()
    if site_policy.refuses_heavy_work(site): raise RuntimeError(site_policy.heavy_work_refusal(site, "rr5 cost measurement"))
    _assert_single_tenant(); free_gb = _assert_free_disk(tempfile.gettempdir()); assert_pinned_clean(str(submodule), pin)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    payload = {"schema_version": "a2-perf-verify-cost/v1", "env_tag": ENV_TAG, "ccbench_commit": pin, "cc": cc, "cxx": cxx, "clocks_per_us": CLOCKS_PER_US, "workload_argv": WORKLOAD_ARGV, "timeouts_seconds": {"run": RUN_TIMEOUT_S, "verifier": VERIFIER_TIMEOUT_S}, "minimum_free_disk_gb": MIN_FREE_DISK_GB, "free_disk_gb_at_start": free_gb, "genomes": []}
    for name, defines in GENOMES:
        genome = Genome("silo", defines); evidence = source_digest.resolve_evidence(genome, pin, cxx=cxx); admission = derive_build_admission(build_context, evidence)
        build = buildcache.build(genome, ccbench_commit=pin, trace=True, cc=cc, cxx=cxx, admission=admission, build_context=build_context, source_evidence=evidence)
        run, trace_dir = _run_once(build.binary)
        try: verifier = _verifier_run(trace_dir, run["commits"])
        finally: shutil.rmtree(trace_dir, ignore_errors=True)
        payload["genomes"].append({"id": name, "defines": defines, "genome": genome.canonical(), "build": {"binary_sha256": build.bin_sha256, "cache_hit": build.cached}, "run": run, "verifier": verifier})
    payload["measured_at_utc"] = datetime.now(timezone.utc).isoformat(); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as stream: json.dump(payload, stream, indent=2, ensure_ascii=False); stream.write("\n")
    print(out); return 0

if __name__ == "__main__": sys.exit(main())
