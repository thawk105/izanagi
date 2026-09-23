"""Fixed 16-point Silo policy reconnaissance; diagnostic, non-admissible builds."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import socket
import statistics
import sys
import tempfile

from . import silo_policy_coverage as C
from . import silo_policy_ir as IR
from . import source_digest, site_policy
from .materializer_admission import non_admissible_materializer
from .model import Genome
from .pipeline import PerfConfig, performance_correctness_workload

SCHEMA = "silo-function-policy-recon/v1"
SCOPE = ("固定 16 点のテンプレート部分空間で、両 verify certified・非 high-abort の点が、"
         "同 job の abort0 に対して 5 rep 中央値で 3% 超を示し、それが別 job の再測でも再現したか")
PERF = PerfConfig(1_000_000, 48, {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5",
                                   "ycsb_rmw": "false", "ycsb_max_ope": "10"}, extime=3, reps=5)
FLAGS = performance_correctness_workload(PERF).flags


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cases(phase: str, job: int | None, candidate: str | None) -> list[tuple[str, str, object | None]]:
    cases = IR.enumerate_recon()
    if phase == "initial":
        if job not in range(8):
            raise ValueError("initial job must be 0..7")
        result = [("ir", c.case_id, c) for c in cases if IR.job_of(c.case_id) == job]
        if job == 0:
            result.append(("stock", "stock", None))
        if job == 1:
            result.append(("b0_l_w0", "B0-L-W0", None))
        return result + [("abort0", "abort0", None)]
    if candidate not in {c.case_id for c in cases}:
        raise ValueError("candidate must be a four-bit enumerated ID")
    return [("abort0", "abort0", None), ("ir", candidate, cases[int(candidate, 2)])]


def _trace0(build: Path, source: Path) -> dict:
    command = C._owner_command(build, source)
    result = C._preprocess(command)
    args = C._command_arguments(command)
    fragments = (C.PROBE_DEFINE, C.BREAK_DEFINE, "izanagi_silo_probe", "DELIBERATELY BROKEN")
    clean = result.returncode == 0 and not any("IZANAGI_" in a for a in args) and not any(
        fragment in result.stdout for fragment in fragments)
    return {"clean": clean, "command": command, "preprocess_sha256": C.sha(result.stdout),
            "owner_tu_only": True}


def _one(role: str, case_id: str, case: object | None, work: Path,
         toolchain: dict, dependencies: dict) -> dict:
    stock = role in {"stock", "b0_l_w0"}
    ir = IR.degenerate_policy() if role == "abort0" else case.ir if role == "ir" else None
    body = IR.render_policy(ir) if ir is not None else None
    genome = (Genome("silo", {**C.locks._BASE, "BACK_OFF": 0 if role == "b0_l_w0" else 1})
              if stock else C.GENOME)
    row = {"role": role, "case_id": case_id,
           "factors": list(case.factors) if case is not None else None,
           "ir": repr(ir) if ir is not None else None,
           "body_sha256": C.sha(body) if body is not None else None,
           "genome": {"protocol": genome.protocol, "flags": genome.flags},
           "status": "incomplete", "bench": [], "builds": {}}
    work.mkdir()
    try:
        with C._source("stock" if stock else case_id, body=body,
                       compiler=toolchain["cxx_path"], scratch=work) as (source, contract):
            row["contract"] = contract
            evidence = source_digest.resolve_evidence(genome, C.PIN, ccbench_dir=str(source),
                                                      cxx=toolchain["cxx_path"])
            row["src_token"] = evidence.src_token
            row["source_evidence"] = evidence.as_receipt()
            trace, receipt = C._build_variant(source, work / "trace", trace=1,
                toolchain=toolchain, dependencies=dependencies, stock=stock,
                stock_backoff=0 if role == "b0_l_w0" else 1)
            row["builds"]["trace1"] = receipt
            row["verify"] = {
                "legacy": C._run(trace, C.LEGACY, source=source, trace=True),
                "performance": C._run(trace, FLAGS, source=source, trace=True, numa=True),
            }
            if not all(C._certified(v) for v in row["verify"].values()):
                row["status"] = "verify-not-certified"
            else:
                binary, receipt = C._build_variant(source, work / "perf", trace=0,
                    toolchain=toolchain, dependencies=dependencies, stock=stock,
                    stock_backoff=0 if role == "b0_l_w0" else 1)
                row["builds"]["trace0"] = receipt
                row["trace0"] = _trace0(work / "perf", source)
                if not row["trace0"]["clean"]:
                    row["status"] = "trace0-not-clean"
                else:
                    for _ in range(5):
                        run = C._run(binary, FLAGS, source=source, trace=False, numa=True)
                        run.pop("preliminary_same_job_stock_control", None)
                        commits, aborts = run.get("commits"), run.get("aborts")
                        run["abort_rate"] = (aborts / (commits + aborts)
                            if type(commits) is int and type(aborts) is int and commits + aborts > 0 else None)
                        row["bench"].append(run)
                    row["status"] = "complete" if _reps(row) is not None else "bench-invalid"
            after = source_digest.resolve_evidence(genome, C.PIN, ccbench_dir=str(source),
                                                   cxx=toolchain["cxx_path"])
            row["source_evidence_after"] = after.as_receipt()
            if after != evidence:
                row["status"] = "source-identity-changed"
    except Exception as exc:
        row["status"] = type(exc).__name__ + ": " + str(exc)
    return row


def _reps(row: dict) -> tuple[float, float] | None:
    if row.get("status") not in {"complete", "incomplete"} or len(row.get("bench", [])) != 5:
        return None
    tps, rates = [], []
    for rep in row["bench"]:
        t, a = rep.get("throughput"), rep.get("abort_rate")
        if (type(t) not in (float, int) or not math.isfinite(t) or t <= 0 or
                type(a) not in (float, int) or not math.isfinite(a) or not 0 <= a <= 1 or
                type(rep.get("commits")) is not int or rep["commits"] <= 0 or
                type(rep.get("aborts")) is not int or rep["aborts"] < 0):
            return None
        if abs(a - rep["aborts"] / (rep["commits"] + rep["aborts"])) > 1e-12:
            return None
        tps.append(t)
        rates.append(a)
    return statistics.median(tps), statistics.median(rates)


def _eligible(row: dict) -> bool:
    return (row.get("status") == "complete" and
            all(C._certified(row.get("verify", {}).get(k, {})) for k in ("legacy", "performance")) and
            row.get("trace0", {}).get("clean") is True and _reps(row) is not None and
            row.get("source_evidence") == row.get("source_evidence_after"))


def _comparison(row: dict, baseline: dict) -> tuple[float | None, str]:
    if not _eligible(baseline):
        return None, "incomplete"
    if row.get("status") == "verify-not-certified":
        return None, "verify-not-certified"
    if row.get("status") == "trace0-not-clean":
        return None, "trace0-not-clean"
    if not _eligible(row):
        return None, "incomplete"
    rt, ra = _reps(row)
    bt, ba = _reps(baseline)
    if ba == 0:
        return None, "zero-baseline-abort-rate"
    if ra > 2 * ba:
        return None, "high-abort"
    return rt / bt, "evaluated"


def run(args: argparse.Namespace) -> int:
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(site_policy.heavy_work_refusal(site, "Silo policy recon"))
    C._assert_single_tenant()
    if not args.third_party_cache.is_absolute():
        raise ValueError("--third-party-cache must be absolute")
    sequence = _cases(args.phase, args.job, args.candidate)
    policy = C.compute._load_policy(C.ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    toolchain = C.compute._resolve_toolchain(policy)
    result = {"schema_version": SCHEMA, "phase": args.phase,
              "job": args.job if args.phase == "initial" else args.candidate,
              "pbs_jobid": os.environ.get("PBS_JOBID"), "hostname": socket.gethostname(),
              "started_at": _now(), "repo_commit": C.compute._run_checked(
                  ["git", "rev-parse", "HEAD"], cwd=C.ROOT).stdout.strip(),
              "pin": C.PIN, "toolchain": toolchain,
              "workload": {"legacy": C.LEGACY, "performance": FLAGS,
                           "bench_reps": 5, "numa": True},
              "case_order": [case_id for _, case_id, _ in sequence], "cases": [],
              "diagnostic_build_admission": non_admissible_materializer(C.MATERIALIZER)}
    try:
        with tempfile.TemporaryDirectory(prefix="silo-policy-recon-") as temporary:
            scratch = Path(temporary)
            dependencies = C.compute._prepare_dependencies(C.ROOT, policy,
                args.third_party_cache, scratch, toolchain)
            result["dependency_preparation"] = C._prepare_build_dependencies(scratch, toolchain, dependencies)
            for role, case_id, case in sequence:
                row = _one(role, case_id, case, scratch / case_id, toolchain, dependencies)
                row["same_job_controls"] = [cid for kind, cid, _ in sequence
                                            if kind in {"abort0", "stock", "b0_l_w0"}]
                result["cases"].append(row)
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    result["finished_at"] = _now()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
    return 1 if "error" in result or len(result["cases"]) != len(sequence) else 0


def aggregate(args: argparse.Namespace) -> int:
    def load(path):
        return json.loads(path.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    detail = {"schema_version": SCHEMA, "binary": None, "remeasure_candidates": [],
              "comparisons": [], "errors": [], "excluded": {}}
    try:
        initials = [load(p) for p in args.initial]
        rem = [load(p) for p in args.remeasure]
        if len(initials) != 8 or sorted(p.get("job") for p in initials) != list(range(8)):
            raise ValueError("exactly eight distinct initial jobs required")
        common = [(p.get("schema_version"), p.get("pin"), p.get("toolchain"), p.get("workload"))
                  for p in initials + rem]
        if len({json.dumps(x, sort_keys=True) for x in common}) != 1 or common[0][0] != SCHEMA:
            raise ValueError("schema/PIN/toolchain/workload mismatch")
        expected_workload = {"legacy": C.LEGACY, "performance": FLAGS,
                             "bench_reps": 5, "numa": True}
        if any(json.dumps(p.get("workload"), sort_keys=True) !=
               json.dumps(expected_workload, sort_keys=True) for p in initials + rem):
            raise ValueError("workload differs from fixed run configuration")
        abort0_sha = C.sha(IR.render_policy(IR.degenerate_policy()))
        control_flags = {"stock": {**C.locks._BASE, "BACK_OFF": 1},
                         "b0_l_w0": {**C.locks._BASE, "BACK_OFF": 0}}

        def check_control(row):
            role = row["role"]
            if role == "abort0" and row.get("body_sha256") != abort0_sha:
                raise ValueError("abort0 body sha256 mismatch")
            genome = row.get("genome")
            if role in control_flags and (not isinstance(genome, dict) or
                    genome.get("flags") != control_flags[role]):
                raise ValueError(role + " genome flags mismatch")

        seen = {}
        for p in initials:
            job = p["job"]
            expected = _cases("initial", job, None)
            rows = p.get("cases", [])
            if p.get("phase") != "initial" or [r.get("case_id") for r in rows] != [x[1] for x in expected]:
                raise ValueError("initial case sequence mismatch")
            if [r.get("role") for r in rows] != [x[0] for x in expected]:
                raise ValueError("initial case roles mismatch")
            for row in rows:
                check_control(row)
                if row["role"] == "ir":
                    if row["case_id"] in seen:
                        raise ValueError("duplicate IR point")
                    seen[row["case_id"]] = (row, p)
                    enumerated = IR.enumerate_recon()[int(row["case_id"], 2)]
                    expected_body = IR.render_policy(enumerated.ir)
                    if row.get("body_sha256") != C.sha(expected_body):
                        raise ValueError("IR body sha256 mismatch")
                    if row.get("factors") != list(enumerated.factors):
                        raise ValueError("IR factor mismatch")
        if set(seen) != {c.case_id for c in IR.enumerate_recon()}:
            raise ValueError("IR points missing")
        candidates = []
        uncertain = False
        for case_id in sorted(seen):
            row, p = seen[case_id]
            baseline = p["cases"][-1]
            ratio, status = _comparison(row, baseline)
            detail["comparisons"].append({"case_id": case_id, "initial_ratio": ratio, "status": status})
            if status != "evaluated":
                detail["excluded"][status] = detail["excluded"].get(status, 0) + 1
            if status == "incomplete" or status == "zero-baseline-abort-rate":
                uncertain = True
            if ratio is not None and ratio > 1.03:
                candidates.append(case_id)
        detail["remeasure_candidates"] = candidates
        rem_by_id = {}
        initial_keys = {(p.get("pbs_jobid"), p.get("hostname"), p.get("started_at")) for p in initials}
        initial_ids = {p.get("pbs_jobid") for p in initials}
        if None in initial_ids or len(initial_ids) != 8:
            raise ValueError("initial PBS_JOBID missing or duplicated")
        rem_ids = set()
        for p in rem:
            cid = p.get("job")
            if (p.get("phase") != "remeasure" or cid not in candidates or cid in rem_by_id or
                    not p.get("pbs_jobid") or p.get("pbs_jobid") in initial_ids or
                    p.get("pbs_jobid") in rem_ids or
                    (p.get("pbs_jobid"), p.get("hostname"), p.get("started_at")) in initial_keys):
                raise ValueError("invalid or same-job remeasurement")
            rows = p.get("cases", [])
            if ([r.get("case_id") for r in rows] != ["abort0", cid] or
                    [r.get("role") for r in rows] != ["abort0", "ir"]):
                raise ValueError("remeasure sequence mismatch")
            if rows[1].get("body_sha256") != seen[cid][0]["body_sha256"]:
                raise ValueError("remeasure body sha256 mismatch")
            check_control(rows[0])
            rem_by_id[cid] = p
            rem_ids.add(p["pbs_jobid"])
        reproduced = False
        for cid in candidates:
            if cid not in rem_by_id:
                uncertain = True
                continue
            rows = rem_by_id[cid]["cases"]
            ratio, status = _comparison(rows[1], rows[0])
            detail["comparisons"][int(cid, 2)]["remeasure_ratio"] = ratio
            detail["comparisons"][int(cid, 2)]["remeasure_status"] = status
            if status != "evaluated":
                key = "remeasure:" + status
                detail["excluded"][key] = detail["excluded"].get(key, 0) + 1
            if status in {"incomplete", "zero-baseline-abort-rate"}:
                uncertain = True
            if ratio is not None and ratio > 1.03:
                reproduced = True
        detail["binary"] = True if reproduced else None if uncertain else False
    except (ValueError, KeyError, TypeError, IndexError, OSError) as exc:
        detail["errors"].append(type(exc).__name__ + ": " + str(exc))
    projection = {"binary": detail["binary"], "scope": SCOPE, "excluded": detail["excluded"]}
    for path, payload in ((args.out, detail), (args.projection_out, projection)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return 0 if not detail["errors"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    r.add_argument("--phase", choices=("initial", "remeasure"), required=True)
    r.add_argument("--job", type=int)
    r.add_argument("--candidate")
    r.add_argument("--third-party-cache", type=Path, required=True)
    r.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("aggregate")
    a.add_argument("--initial", type=Path, nargs=8, required=True)
    a.add_argument("--remeasure", type=Path, nargs="*", default=[])
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--projection-out", type=Path, required=True)
    args = parser.parse_args(argv)
    return run(args) if args.command == "run" else aggregate(args)


if __name__ == "__main__":
    sys.exit(main())
