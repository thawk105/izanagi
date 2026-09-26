# 集計スクリプトの逐語 (repo 外で実行、Codex author = s5-author-agg)

- 実行時の所在: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-known-best-recheck/agg/recheck_aggregate.py`
- sha256: `829da2eabdad3af38acf05be7be438097c8f5647e3331a4fa99c58449ae46e0f`
- repo の実装面に入れないため `.md` に逐語で置く (実行可能資材として commit しない)。

```python
"""Aggregate the three separately scheduled Silo compare rechecks."""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


TARGETS = {"1111": 0, "1110": 1, "1001": 6}
R = C = IR = None


def load(path: Path) -> dict:
    return json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def common(p: dict) -> tuple:
    return tuple(p.get(k) for k in ("schema_version", "pin", "toolchain", "workload"))


def evaluate_job(p: dict, expected_pin: str) -> dict:
    """Validate one complete job and reproduce _compare_detail's per-job loop."""
    if p.get("schema_version") != R.SCHEMA or p.get("pin") != expected_pin:
        raise ValueError("schema/PIN mismatch")
    expected_workload = {"legacy": C.LEGACY, "performance": R.FLAGS,
                         "bench_reps": 5, "numa": True}
    if p.get("workload") != expected_workload:
        raise ValueError("workload differs from fixed run configuration")
    job = p.get("job")
    expected = R._cases("compare", job, None)
    rows = p.get("cases", [])
    ids = [entry[1] for entry in expected]
    # silo_policy_recon._compare_detail: compare case sequence/roles and row bindings.
    if p.get("phase") != "compare" or [r.get("case_id") for r in rows] != ids or p.get("case_order") != ids:
        raise ValueError("compare case sequence mismatch")
    if [r.get("role") for r in rows] != [entry[0] for entry in expected]:
        raise ValueError("compare case roles mismatch")
    controls = {"stock": {**C.locks._BASE, "BACK_OFF": 1},
                "b0_l_w0": {**C.locks._BASE, "BACK_OFF": 0},
                "fixed10": {**C.locks._BASE, "BACK_OFF": 1, "BACKOFF_FIXED": 10}}
    abort0_sha = C.sha(IR.render_policy(IR.degenerate_policy()))
    by_id = {row["case_id"]: row for row in rows}
    for row in rows:
        role = row["role"]
        if role == "ir":
            case = IR.enumerate_recon()[int(row["case_id"], 2)]
            if row.get("body_sha256") != C.sha(IR.render_policy(case.ir)):
                raise ValueError("IR body sha256 mismatch")
            if row.get("factors") != list(case.factors):
                raise ValueError("IR factor mismatch")
        elif role == "abort0":
            if row.get("body_sha256") != abort0_sha:
                raise ValueError("abort0 body sha256 mismatch")
        elif row.get("genome", {}).get("flags") != controls[role]:
            raise ValueError(role + " genome flags mismatch")
        if role == "fixed10" and row.get("status") == "complete":
            receipt = row.get("backoff_fixed_define", {})
            if not all(receipt.get(trace, {}).get("effective") is True and
                       R._backoff_fixed_defines_effective(receipt[trace].get("defines", []))
                       for trace in ("trace1", "trace0")):
                raise ValueError("fixed10 backoff fixed define mismatch")

    # silo_policy_recon._compare_detail: usable, reason, references and comparison loop.
    def usable(row):
        before = row.get("source_evidence")
        return bool(before) and before == row.get("source_evidence_after") and R._eligible(row)

    def reason(row):
        status = row.get("status")
        if status in {"verify-not-certified", "trace0-not-clean", "backoff-fixed-not-effective"}:
            return status
        return "incomplete"

    refs = {role: by_id[cid] for role, cid in (("abort0", "abort0"), ("stock", "stock"),
                                              ("b0_l_w0", "B0-L-W0"), ("fixed10", "fixed10"))}
    references = {role: {"median_throughput": R._reps(row)[0] if R._reps(row) else None,
                         "median_abort_rate": R._reps(row)[1] if R._reps(row) else None,
                         "status": row.get("status")} for role, row in refs.items()}
    comparisons = []
    for role, cid, _ in R._cases("compare", job, None):
        if role != "ir":
            continue
        row = by_id[cid]
        ratio_vs = {ref: (R._reps(row)[0] / R._reps(refs[ref])[0]
                          if usable(row) and usable(refs[ref]) else None)
                    for ref in ("stock", "b0_l_w0", "fixed10")}
        if not usable(row):
            why = reason(row)
        elif not usable(refs["abort0"]):
            why = "reference-ineligible"
        elif refs["fixed10"].get("status") == "backoff-fixed-not-effective":
            why = "backoff-fixed-not-effective"
        elif not all(usable(refs[ref]) for ref in ("stock", "b0_l_w0", "fixed10")):
            why = "reference-ineligible"
        elif R._reps(row)[1] > 2 * R._reps(refs["abort0"])[1]:
            why = "high-abort"
        else:
            why = None
        ratio = (None if why else R._reps(row)[0] /
                 max(R._reps(refs[ref])[0] for ref in ("stock", "b0_l_w0", "fixed10")))
        exceeds = None if ratio is None else ratio > 1.03
        comparisons.append({"case_id": cid, "job": job, "ratio_vs": ratio_vs,
                            "best_ref_ratio": ratio, "reason": why, "exceeds": exceeds})
    return {"comparisons": comparisons, "references": references}


def originals(directory: Path) -> tuple[list[dict], dict]:
    jobs = [load(directory / f"compare-{job}.json") for job in range(8)]
    aggregate = load(directory / "compare-aggregate.json")
    if sorted(p.get("job") for p in jobs) != list(range(8)):
        raise ValueError("original job numbers mismatch")
    if len({json.dumps(common(p), sort_keys=True) for p in jobs}) != 1:
        raise ValueError("original schema/PIN/toolchain/workload mismatch")
    return jobs, aggregate


def target_result(p: dict, cid: str, expected_pin: str, original: dict | None = None,
                  forbidden_keys: set | None = None) -> dict:
    job = TARGETS[cid]
    result = {"case_id": cid, "job": job, "verdict": "indeterminate",
              "verdict_reason": None, "best_ref_ratio": None, "ratio_vs": None,
              "fixed10_ratio": None, "target_rep_min_throughput": None,
              "fixed10_rep_max_throughput": None, "target_min_exceeds_fixed10_max": None,
              "original_best_ref_ratio": None, "references": None,
              "other_ir": None}
    if not any(row.get("case_id") == cid for row in p.get("cases", [])):
        result["verdict_reason"] = "missing-row"
        return result
    errors = []
    if p.get("job") != job:
        errors.append("target job mismatch")
    try:
        detail = evaluate_job(p, expected_pin)
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        errors.append(str(exc))
    if forbidden_keys is not None and (p.get("hostname"), p.get("started_at")) in forbidden_keys:
        errors.append("hostname/started_at duplicated")
    if original is not None:
        try:
            old_row = next(row for row in original["cases"] if row["case_id"] == cid)
            new_row = next(row for row in p["cases"] if row["case_id"] == cid)
            if new_row.get("body_sha256") != old_row.get("body_sha256"):
                errors.append("target body sha256 differs from original")
        except (KeyError, StopIteration, TypeError) as exc:
            errors.append("target body binding unavailable: " + str(exc))
    if errors:
        result["verdict_reason"] = "binding:" + "; ".join(errors)
        return result
    comp = next(item for item in detail["comparisons"] if item["case_id"] == cid)
    result.update(best_ref_ratio=comp["best_ref_ratio"], ratio_vs=comp["ratio_vs"],
                  fixed10_ratio=comp["ratio_vs"]["fixed10"], references=detail["references"],
                  other_ir=next(item for item in detail["comparisons"] if item["case_id"] != cid))
    rows = {row["case_id"]: row for row in p["cases"]}
    target_reps = rows[cid].get("bench", [])
    fixed_reps = rows["fixed10"].get("bench", [])
    if R._reps(rows[cid]) and R._reps(rows["fixed10"]):
        low = min(rep["throughput"] for rep in target_reps)
        high = max(rep["throughput"] for rep in fixed_reps)
        result.update(target_rep_min_throughput=low, fixed10_rep_max_throughput=high,
                      target_min_exceeds_fixed10_max=low > high)
    status = rows[cid].get("status")
    if status in {"verify-not-certified", "trace0-not-clean"}:
        result.update(verdict="disqualified", verdict_reason=status)
    elif comp["reason"] is not None:
        result["verdict_reason"] = comp["reason"]
    elif comp["best_ref_ratio"] > 1.03:
        result.update(verdict="reproduced", verdict_reason=None)
    else:
        result.update(verdict="not-reproduced", verdict_reason=None)
    return result


def self_check_original(directory: Path) -> int:
    jobs, aggregate = originals(directory)
    actual = sorted((c for p in jobs for c in evaluate_job(p, jobs[0]["pin"])["comparisons"]),
                    key=lambda c: c["case_id"])
    expected = sorted(aggregate["comparisons"], key=lambda c: c["case_id"])
    if actual != expected:
        for index in range(max(len(actual), len(expected))):
            a = actual[index] if index < len(actual) else None
            e = expected[index] if index < len(expected) else None
            if a != e:
                print(f"mismatch {index}: actual={a!r} expected={e!r}", file=sys.stderr)
        return 1
    print("original: 8 jobs, 16 comparisons match exactly")
    return 0


def self_check_negatives(directory: Path) -> int:
    jobs, _ = originals(directory)
    checks = []
    altered = copy.deepcopy(jobs[0])
    next(r for r in altered["cases"] if r["case_id"] == "1111").pop("source_evidence_after")
    result = target_result(altered, "1111", jobs[0]["pin"])
    checks.append(("source evidence", result["verdict"] == "indeterminate" and result["verdict_reason"] == "incomplete"))
    altered = copy.deepcopy(jobs[1])
    next(r for r in altered["cases"] if r["case_id"] == "fixed10")["backoff_fixed_define"]["trace0"]["effective"] = False
    result = target_result(altered, "1110", jobs[0]["pin"])
    checks.append(("fixed10 define", result["verdict"] == "indeterminate" and
                   result["verdict_reason"] == "binding:fixed10 backoff fixed define mismatch"))
    altered = copy.deepcopy(jobs[6])
    next(r for r in altered["cases"] if r["case_id"] == "1001")["status"] = "verify-not-certified"
    result = target_result(altered, "1001", jobs[0]["pin"])
    checks.append(("verify status", result["verdict"] == "disqualified"))
    for name, passed in checks:
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(passed for _, passed in checks) else 1


def process(files: list[Path], original_dir: Path, out: Path) -> int:
    jobs, aggregate = originals(original_dir)
    if len(files) != 3:
        raise ValueError("exactly three new job files required")
    inputs = [(path, load(path)) for path in files]
    if sorted(p.get("job") for _, p in inputs) != sorted(TARGETS.values()):
        raise ValueError("new files must contain jobs 0, 1, 6 exactly once")
    original_keys = {(p.get("hostname"), p.get("started_at")) for p in jobs}
    new_keys = Counter((p.get("hostname"), p.get("started_at")) for _, p in inputs)
    new_common = {json.dumps(common(p), sort_keys=True) for _, p in inputs}
    output = {"schema_version": R.SCHEMA, "targets": [], "jobs": [], "input_sha256": {}}
    old_by_job = {p["job"]: p for p in jobs}
    old_comps = {c["case_id"]: c for c in aggregate["comparisons"]}
    for path, p in inputs:
        cid = next(cid for cid, job in TARGETS.items() if job == p["job"])
        key = (p.get("hostname"), p.get("started_at"))
        cross_error = None
        if len(new_common) != 1:
            cross_error = "new schema/PIN/toolchain/workload mismatch"
        if key in original_keys or new_keys[key] != 1:
            cross_error = "hostname/started_at duplicated"
        result = target_result(p, cid, C.PIN, old_by_job[p["job"]], original_keys)
        if cross_error is not None:
            prior = result["verdict_reason"]
            if prior is None or cross_error not in prior:
                result.update(verdict="indeterminate", verdict_reason=
                              (prior + "; " if prior else "binding:") + cross_error)
        result["original_best_ref_ratio"] = old_comps[cid]["best_ref_ratio"]
        output["targets"].append(result)
        output["jobs"].append({"job": p["job"], **{k: p.get(k) for k in
            ("hostname", "started_at", "finished_at", "pin", "repo_commit")}, "has_error": "error" in p})
        output["input_sha256"][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    output["targets"].sort(key=lambda r: r["job"])
    output["jobs"].sort(key=lambda r: r["job"])
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-check-original", type=Path)
    mode.add_argument("--self-check-negatives", type=Path)
    mode.add_argument("--new", nargs="+", type=Path)
    parser.add_argument("--original-dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not args.repo_root.is_absolute():
        parser.error("--repo-root must be absolute")
    sys.path.insert(0, str(args.repo_root))
    global R, C, IR
    from orchestrator.campaign import silo_policy_recon as R
    from orchestrator.campaign import silo_policy_coverage as C
    from orchestrator.campaign import silo_policy_ir as IR
    try:
        if args.self_check_original:
            return self_check_original(args.self_check_original)
        if args.self_check_negatives:
            return self_check_negatives(args.self_check_negatives)
        if not args.original_dir or not args.out:
            parser.error("--new requires --original-dir and --out")
        return process(args.new, args.original_dir, args.out)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print(f"input error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1 if args.self_check_original or args.self_check_negatives else 2


if __name__ == "__main__":
    sys.exit(main())
```
