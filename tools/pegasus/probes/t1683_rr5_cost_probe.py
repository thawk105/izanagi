#!/usr/bin/env python3
"""One-shot full-scale trace and verifier cost measurement."""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from orchestrator.campaign import (buildcache, condition_meaning_gate, env_contract,  # noqa: E402
                                   site_policy, source_digest)
from orchestrator.campaign.build_admission import GeneratorId, build_run_context, derive_build_admission  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.p2_2 import _assert_single_tenant  # noqa: E402
from orchestrator.campaign.patchharness import applied, assert_pinned_clean, checkout  # noqa: E402
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402
from orchestrator.campaign.s2_verify_calibration import _parse_abort_counts, _parse_commit_witness  # noqa: E402

CONTRACT = env_contract.lookup("pegasus"); ENV_TAG = CONTRACT.env_tag
CLOCKS_PER_US = CONTRACT.clocks_per_us; NUMA = list(CONTRACT.numactl)
RUN_TIMEOUT_S = 900.0; VERIFIER_TIMEOUT_S = 7200.0; MIN_FREE_DISK_GB = 60.0
POLICY_PATH = ROOT / "orchestrator" / "campaign" / "paper_story_a2_certification.v2.json"
COMMON_DEFINE_NAMES = ("NO_WAIT_LOCKING_IN_VALIDATION", "NO_WAIT_OF_TICTOC", "WAL", "BACKOFF_NOINLINE")

def _required(mapping: dict, key: str, context: str):
    if key not in mapping: raise RuntimeError(f"{POLICY_PATH}: missing {context}.{key}")
    return mapping[key]

def _mapping(value, context: str) -> dict:
    if not isinstance(value, dict): raise RuntimeError(f"{POLICY_PATH}: {context} must be an object")
    return value

def _sequence(value, context: str) -> list:
    if not isinstance(value, list): raise RuntimeError(f"{POLICY_PATH}: {context} must be an array")
    return value

def _text(value, context: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)): raise RuntimeError(f"{POLICY_PATH}: {context} must be a scalar")
    return str(value)

def _integer(value, context: str) -> int:
    if isinstance(value, bool): raise RuntimeError(f"{POLICY_PATH}: {context} must be an integer")
    try: parsed = int(value)
    except (TypeError, ValueError) as exc: raise RuntimeError(f"{POLICY_PATH}: {context} must be an integer") from exc
    if str(parsed) != str(value): raise RuntimeError(f"{POLICY_PATH}: {context} must be an integer")
    return parsed

def _load_workload(workload_id: str) -> dict:
    try:
        with POLICY_PATH.open(encoding="utf-8") as stream: policy = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read workload policy {POLICY_PATH}: {exc}") from exc
    policy = _mapping(policy, "root")
    common = _mapping(_required(policy, "performance_common", "root"), "performance_common")
    controlled = _mapping(_required(policy, "controlled_define_base", "root"), "controlled_define_base")
    workloads = _sequence(_required(policy, "workloads", "root"), "workloads")
    matches = []
    for index, item in enumerate(workloads):
        item = _mapping(item, f"workloads[{index}]")
        if _required(item, "id", f"workloads[{index}]") == workload_id: matches.append(item)
    if len(matches) != 1: raise RuntimeError(f"{POLICY_PATH}: expected exactly one workload {workload_id!r}")
    workload = matches[0]; rratio = _text(_required(workload, "rratio", f"workload {workload_id}"), f"workload {workload_id}.rratio")
    workload_argv = [
        f"-thread_num={_text(_required(common, 'threads', 'performance_common'), 'performance_common.threads')}",
        f"-ycsb_tuple_num={_text(_required(common, 'records', 'performance_common'), 'performance_common.records')}",
        f"-ycsb_zipf_skew={_text(_required(common, 'skew', 'performance_common'), 'performance_common.skew')}",
        f"-ycsb_rratio={rratio}",
        f"-ycsb_rmw={_text(_required(common, 'rmw', 'performance_common'), 'performance_common.rmw')}",
        f"-ycsb_max_ope={_text(_required(common, 'max_ope', 'performance_common'), 'performance_common.max_ope')}",
        f"-extime={_text(_required(common, 'extime', 'performance_common'), 'performance_common.extime')}",
        f"-clocks_per_us={CLOCKS_PER_US}",
    ]
    define_base = {name: _integer(_required(controlled, f"CCBENCH_{name}", "controlled_define_base"), f"controlled_define_base.CCBENCH_{name}") for name in COMMON_DEFINE_NAMES}
    genomes = []
    for index, item in enumerate(_sequence(_required(policy, "cells", "root"), "cells")):
        item = _mapping(item, f"cells[{index}]")
        if _required(item, "workload", f"cells[{index}]") != workload_id: continue
        name = _text(_required(item, "id", f"cells[{index}]"), f"cells[{index}].id")
        cell_genome = _mapping(_required(item, "genome", f"cell {name}"), f"cell {name}.genome")
        defines = {**define_base, "BACK_OFF": _integer(_required(cell_genome, "BACK_OFF", f"cell {name}.genome"), f"cell {name}.genome.BACK_OFF"), "BACKOFF_FIXED": _integer(_required(cell_genome, "BACKOFF_FIXED", f"cell {name}.genome"), f"cell {name}.genome.BACKOFF_FIXED")}
        genomes.append((name, defines))
    if len(genomes) != 2 or len({name for name, _ in genomes}) != 2: raise RuntimeError(f"{POLICY_PATH}: workload {workload_id!r} must have exactly two uniquely named cells")
    return {"id": workload_id, "rratio": rratio, "common": common, "argv": workload_argv, "genomes": genomes}

def _default_out(workload: dict) -> Path:
    common = workload["common"]
    threads = _text(_required(common, "threads", "performance_common"), "performance_common.threads")
    skew = _text(_required(common, "skew", "performance_common"), "performance_common.skew").replace(".", "p")
    rmw = _text(_required(common, "rmw", "performance_common"), "performance_common.rmw")
    if any(re.fullmatch(r"[A-Za-z0-9]+", token) is None for token in (threads, skew, rmw)): raise RuntimeError(f"{POLICY_PATH}: output path fields contain unsafe characters")
    return Path(f"output/env/pegasus/calibration/a2_perf_verify_cost_t{threads}_skew{skew}_{workload['id']}_rmw{rmw}.json")

def _current_pin(submodule: Path) -> str:
    head = subprocess.run(["git", "-C", str(submodule), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if re.fullmatch(r"[0-9a-f]{40}", head) is None or not head.startswith(CURRENT_PIN):
        raise RuntimeError(f"ccbench HEAD {head!r} does not match CURRENT_PIN {CURRENT_PIN!r}")
    return head

def _assert_free_disk(path: str) -> float:
    free_gb = shutil.disk_usage(path).free / 2**30
    if free_gb < MIN_FREE_DISK_GB: raise RuntimeError(f"free disk {free_gb:.1f}GB < {MIN_FREE_DISK_GB:.1f}GB at {path}")
    return free_gb

def _run_argv(binary: str, workload_argv: list[str]) -> list[str]:
    return NUMA + [binary] + list(workload_argv)

def _trace_stats(trace_dir: str) -> dict[str, int]:
    files = sorted(Path(trace_dir).glob("trace_*.log")); lines = 0
    for path in files:
        with path.open("rb") as stream: lines += sum(1 for _ in stream)
    return {"files": len(files), "bytes": sum(p.stat().st_size for p in files), "lines": lines}

def _run_once(binary: str, workload_id: str, workload_argv: list[str]) -> tuple[dict, str]:
    trace_dir = tempfile.mkdtemp(prefix=f"izanagi_t1683_{workload_id}_trace_"); env = dict(os.environ)
    env["IZANAGI_TRACE_DIR"] = trace_dir; os.makedirs(os.path.join(trace_dir, "log"), exist_ok=True); started = time.monotonic()
    try:
        proc = subprocess.run(_run_argv(binary, workload_argv), cwd=trace_dir, env=env, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
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

def _dry_run(out: Path, ccbench_head: str, cc: str, cxx: str, workload: dict) -> dict:
    genomes = [{"id": name, "defines": defines, "run_argv": _run_argv("<trace-enabled-ycsb_silo.exe>", workload["argv"])} for name, defines in workload["genomes"]]
    verifier = ["/usr/bin/time", "-v", sys.executable, "-m", "verifier", "<trace-dir>", "--json", "--quiet", "--expected-commits", "<commits>"]
    return {"mode": "dry-run", "env_tag": ENV_TAG, "workload": workload["id"], "rratio": workload["rratio"], "ccbench_commit": CURRENT_PIN, "ccbench_head": ccbench_head, "cc": cc, "cxx": cxx, "output": str(out), "output_exists": out.exists(), "timeouts_seconds": {"run": RUN_TIMEOUT_S, "verifier": VERIFIER_TIMEOUT_S}, "minimum_free_disk_gb": MIN_FREE_DISK_GB, "numactl": NUMA, "workload_argv": workload["argv"], "genomes": genomes, "verifier_argv": verifier}

def _condition_requests_by_genome(workload: dict) -> tuple:
    cells = []
    for cell_name, adopted in workload["genomes"]:
        requests = []
        for macro, requested, default in (
            ("BACKOFF_FIXED", int(adopted["BACKOFF_FIXED"]), -1),
            ("BACKOFF_NOINLINE", int(adopted["BACKOFF_NOINLINE"]), 0),
        ):
            inert = requested == default or (
                macro == "BACKOFF_FIXED" and requested == -1
            )
            request = condition_meaning_gate.make_define_request(
                driver_id=(
                    "tools.pegasus.probes.t1683_rr5_cost_probe:"
                    f"{cell_name}"
                ),
                macro=macro,
                requested_value=requested,
                default_value=default,
                stock_comparison=inert,
            )
            declaration = None
            if macro == "BACKOFF_FIXED" and requested == -1:
                declaration = condition_meaning_gate.MeaningWitnessDeclaration(
                    macro,
                    (condition_meaning_gate.MeaningCase(
                        -1, None, condition_meaning_gate.STOCK_ADAPTIVE_BRANCH,
                    ),),
                )
            requests.append((request, declaration))
        cells.append((cell_name, adopted, tuple(requests)))
    return tuple(cells)


def _require_condition_gates(
    source_root: Path, stock_root: Path, workload: dict, cxx: str,
) -> list[dict]:
    receipts = []
    for cell_name, adopted, requests in _condition_requests_by_genome(workload):
        configure_args = tuple(
            argument for argument in Genome("silo", adopted).cmake_defines()
            if not argument.startswith((
                "-DCCBENCH_BACKOFF_FIXED=",
                "-DCCBENCH_BACKOFF_NOINLINE=",
            ))
        )
        captured = condition_meaning_gate.capture_define_inputs(
            source_root, stock_root=stock_root, configure_args=configure_args,
        )
        supply_records = []
        meaning_records = []
        for request, declaration in requests:
            supply_records.append(
                condition_meaning_gate.evaluate_define_supply_effectuation(
                    captured, request=request, cxx=cxx, cmake="cmake",
                )
            )
            meaning_records.append(
                condition_meaning_gate.evaluate_define_runtime_meaning(
                    captured, request=request, declaration=declaration, cxx=cxx,
                )
            )
        admission = condition_meaning_gate.require_condition_gate_family(
            supply_records, meaning_records, use_class="raw-measurement",
        )
        if not admission.admitted:
            states = ", ".join(
                f"{record.macro}={record.terminal_status}/{record.reason_code}"
                for record in (*supply_records, *meaning_records)
            )
            raise RuntimeError(
                f"condition gate rejected cost probe cell {cell_name}: {states}"
            )
        receipts.extend((
            *(json.loads(record.canonical_json()) for record in supply_records),
            *(json.loads(record.canonical_json()) for record in meaning_records),
            json.loads(admission.canonical_json()),
        ))
    return receipts

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--workload", choices=("rr5", "rr50"), default="rr5"); parser.add_argument("--out"); parser.add_argument("--dry-run", action="store_true"); args = parser.parse_args()
    workload = _load_workload(args.workload); out = Path(args.out) if args.out is not None else _default_out(workload); out = out if out.is_absolute() else ROOT / out
    submodule = ROOT / "external" / "ccbench"; ccbench_head = _current_pin(submodule)
    cc, cxx = buildcache.compilers_for_current_site()
    if args.dry_run: print(json.dumps(_dry_run(out, ccbench_head, cc, cxx, workload), indent=2, ensure_ascii=False)); return 0
    if out.exists(): raise FileExistsError(f"refusing to overwrite existing output: {out}")
    site = site_policy.current_site()
    if site_policy.refuses_heavy_work(site): raise RuntimeError(site_policy.heavy_work_refusal(site, f"{workload['id']} cost measurement"))
    _assert_single_tenant(); free_gb = _assert_free_disk(tempfile.gettempdir()); assert_pinned_clean(str(submodule), CURRENT_PIN)
    backoff_patch = ROOT / "patches" / "silo-backoff-fixed.patch"
    with checkout(CURRENT_PIN, str(submodule)) as gate_stock_root:
        with applied(str(backoff_patch), CURRENT_PIN, str(submodule)):
            condition_gates = _require_condition_gates(
                submodule, Path(gate_stock_root), workload, cxx,
            )
            build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
            payload = {"schema_version": "a2-perf-verify-cost/v1", "env_tag": ENV_TAG, "workload": workload["id"], "rratio": workload["rratio"], "ccbench_commit": CURRENT_PIN, "ccbench_head": ccbench_head, "cc": cc, "cxx": cxx, "clocks_per_us": CLOCKS_PER_US, "workload_argv": workload["argv"], "timeouts_seconds": {"run": RUN_TIMEOUT_S, "verifier": VERIFIER_TIMEOUT_S}, "minimum_free_disk_gb": MIN_FREE_DISK_GB, "free_disk_gb_at_start": free_gb, "condition_gates": condition_gates, "genomes": []}
            for name, defines in workload["genomes"]:
                genome = Genome("silo", defines); evidence = source_digest.resolve_evidence(genome, CURRENT_PIN, cxx=cxx); admission = derive_build_admission(build_context, evidence)
                build = buildcache.build(genome, ccbench_commit=CURRENT_PIN, trace=True, cc=cc, cxx=cxx, admission=admission, build_context=build_context, source_evidence=evidence)
                run, trace_dir = _run_once(build.binary, workload["id"], workload["argv"])
                try: verifier = _verifier_run(trace_dir, run["commits"])
                finally: shutil.rmtree(trace_dir, ignore_errors=True)
                payload["genomes"].append({"id": name, "defines": defines, "genome": genome.canonical(), "build": {"binary_sha256": build.bin_sha256, "cache_hit": build.cached}, "run": run, "verifier": verifier})
    payload["measured_at_utc"] = datetime.now(timezone.utc).isoformat(); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as stream: json.dump(payload, stream, indent=2, ensure_ascii=False); stream.write("\n")
    print(out); return 0

if __name__ == "__main__": sys.exit(main())
