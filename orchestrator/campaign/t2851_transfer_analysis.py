"""T-2851 frozen transfer analysis; no dependency on the execution runner.

Minimum JSON fields read from A (all identities are strings):
freeze: workload ('ycsb'|'tpcc'), stage (TPC-C 's1'|'s2'),
  m_by_family {family: positive integer}, comparisons [{protocol, cell,
  anchor, candidate, reference, kind ('primary'|'descriptive'|'known_separate'),
  task, method, independent_search, factor?, level?, same_identity?}].
  family is 'ycsb' or the TPC-C stage. Each comparison is one frozen series;
  repeated identities share measurement, but remain separate method series.
  same_identity records a deliberately excluded comparison.
  series? [{stage?, task, method, independent_search, selected_identity? |
  selection_failure?}] lists frozen searches, including failures for summaries.
jobs: [{stage?, cohort (1|2), protocol, cell, attempt (integer, starts at 1),
  solo_start, solo_end, complete_blocks (integer), within_retry_limit,
  separate_allocation (cohort 2), blocks [{block (1..32), tps {identity: positive
  finite throughput or null}}]}]. The first qualifying attempt is adopted.
verify: [{stage?, protocol, cell, identity, status
  ('certified'|'disqualified'|'indeterminate'), attempt?}]. The latest
  verification for a cell/identity resolves uncertainty; any disqualification
  is permanent. Missing verification is indeterminate; R0 needs none.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import statistics

from orchestrator.campaign.b10_backoff_static_tail_formal import student_t_quantile

DELTA = math.log(1.03)
BLOCKS = 32


def classify(lower: float | None, upper: float | None) -> str:
    if lower is None or upper is None:
        return "undetermined"
    if lower > DELTA:  # M8: unique strict superiority expression
        return "superior"
    if upper < -DELTA:
        return "regression"
    if -DELTA < lower and upper < DELTA:
        return "equivalent"
    return "undetermined"


def bonferroni_quantile(m: int) -> float:
    if not isinstance(m, int) or m < 1:
        raise ValueError("frozen family M must be positive")
    return student_t_quantile(1 - 0.025 / m, 31)  # M9: unique adjustment


def _usable(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _effect(job: dict | None, candidate: str, reference: str) -> dict:
    differences = []
    if job is not None:
        for block in job.get("blocks", []):
            tps = block.get("tps", {})
            k, r = tps.get(candidate), tps.get(reference)
            if _usable(k) and _usable(r):
                differences.append(math.log(k) - math.log(r))
    n = len(differences)
    mean = statistics.mean(differences) if n else None
    sd = statistics.stdev(differences) if n > 1 else None
    return {"n_eff": n, "unusable_blocks": BLOCKS - n, "mean_log_ratio": mean,
            "sample_sd": sd, "differences": differences}


def _interval(effect: dict, quantile: float | None) -> tuple[float | None, float | None]:
    n = effect["n_eff"]
    if n < 2 or quantile is None:
        return None, None
    half = quantile * effect["sample_sd"] / math.sqrt(n)
    return effect["mean_log_ratio"] - half, effect["mean_log_ratio"] + half


def _qualified(effect: dict, job: dict | None, statuses: dict, key: tuple,
               globally_disqualified: set) -> bool:
    stage, protocol, cell, candidate, reference = key
    return (effect["n_eff"] == BLOCKS  # M10: unique complete-pair requirement
            and job is not None
            and (job["cohort"] == 1 or job.get("separate_allocation") is True)
            and candidate not in globally_disqualified.get((stage, protocol), set())
            and reference not in globally_disqualified.get((stage, protocol), set())
            and all(statuses.get((stage, protocol, cell, identity)) == "certified"
                    for identity in (candidate, reference) if identity != "R0"))


def _adopt_jobs(jobs: list[dict]) -> dict:
    grouped = defaultdict(list)
    for job in jobs:
        grouped[(job.get("stage"), job["cohort"], job["protocol"], job["cell"])].append(job)
    adopted = {}
    for key, attempts in grouped.items():
        attempts.sort(key=lambda j: j["attempt"])
        for job in attempts:
            if (job.get("within_retry_limit") is True and job.get("solo_start") is True
                    and job.get("solo_end") is True and job.get("complete_blocks") == BLOCKS):
                adopted[key] = job
                break
        if key not in adopted:
            eligible = [j for j in attempts if j.get("within_retry_limit") is True]
            if eligible:
                adopted[key] = eligible[-1]  # descriptive values only
    return adopted


def _verification_status(records: list[dict]) -> tuple[dict, dict]:
    grouped = defaultdict(list)
    disqualified = defaultdict(set)
    for record in records:
        key = (record.get("stage"), record["protocol"], record["cell"], record["identity"])
        grouped[key].append(record)
        if record["status"] == "disqualified":
            disqualified[key[:2]].add(key[3])  # M11: global protocol/stage exclusion
    statuses = {}
    for key, attempts in grouped.items():
        attempts.sort(key=lambda r: r.get("attempt", 1))
        statuses[key] = ("disqualified" if any(r["status"] == "disqualified" for r in attempts)
                         else attempts[-1]["status"])
    return statuses, disqualified


def _welch(left: dict, right: dict) -> dict | None:
    if left["n_eff"] < 2 or right["n_eff"] < 2:
        return None
    a = left["sample_sd"] ** 2 / left["n_eff"]
    b = right["sample_sd"] ** 2 / right["n_eff"]
    diff = left["mean_log_ratio"] - right["mean_log_ratio"]
    if a + b == 0:
        return {"difference": diff, "df": None, "lower": diff, "upper": diff}
    df = (a + b) ** 2 / (a * a / (left["n_eff"] - 1) + b * b / (right["n_eff"] - 1))
    half = student_t_quantile(0.975, df) * math.sqrt(a + b)
    return {"difference": diff, "df": df, "lower": diff - half, "upper": diff + half}


def analyze(freeze: dict, jobs: list[dict], verify: list[dict]) -> dict:
    family = freeze["stage"] if freeze["workload"] == "tpcc" else "ycsb"
    m_by_family = dict(freeze["m_by_family"])
    m = m_by_family.get(family, 0)
    quantile = bonferroni_quantile(m) if m else None
    adopted = _adopt_jobs(jobs)
    statuses, disqualified = _verification_status(verify)
    rows = {"primary": [], "descriptive": [], "known_separate": []}
    measured = {}
    for comparison in freeze["comparisons"]:
        stage = comparison.get("stage", freeze.get("stage"))
        protocol, cell = comparison["protocol"], comparison["cell"]
        candidate, reference = comparison["candidate"], comparison["reference"]
        if candidate == reference or comparison.get("same_identity") is True:  # M12: sole identity exclusion
            continue
        kind = comparison["kind"]
        if freeze["workload"] == "ycsb" and protocol == "silo" and cell == "bal-rmw1":
            kind = "known_separate"
        if reference == "R0" or comparison.get("comparison_type") == "reference_pair":
            kind = "descriptive" if kind != "known_separate" else kind
        if freeze["workload"] == "tpcc" and comparison.get("reference_mode") != "a":
            kind = "descriptive"
        key = (stage, protocol, cell, candidate, reference)
        result = {k: v for k, v in comparison.items() if k != "same_identity"}
        result["kind"] = kind
        result["cohorts"] = {}
        for cohort in (1, 2):
            job = adopted.get((stage, cohort, protocol, cell))
            effect = _effect(job, candidate, reference)
            qualified = (kind == "primary" and m > 0
                         and _qualified(effect, job, statuses, key, disqualified)
                         and job.get("complete_blocks") == BLOCKS
                         and job.get("solo_start") is True and job.get("solo_end") is True)
            q = quantile if qualified else (student_t_quantile(0.975, effect["n_eff"] - 1)
                                           if effect["n_eff"] >= 2 else None)
            lower, upper = _interval(effect, q)
            entry = {k: v for k, v in effect.items() if k != "differences"}
            entry.update(lower=lower, upper=upper,
                         classification=classify(lower, upper) if qualified or kind != "primary" else "undetermined",
                         qualified=qualified, interval="simultaneous" if qualified else "descriptive",
                         adopted_attempt=job["attempt"] if job else None)
            result["cohorts"][cohort] = entry
            measured[(key, cohort)] = effect
        one, two = result["cohorts"][1], result["cohorts"][2]
        result["primary_result"] = (one["classification"] if kind == "primary" and
                                    one["qualified"] and two["qualified"] and
                                    one["classification"] == two["classification"] and
                                    one["classification"] != "undetermined" else None)
        result["followup_disagreement"] = (kind == "primary" and one["qualified"] and
                                            two["qualified"] and one["classification"] != two["classification"])
        result["claim_excluded"] = (candidate in disqualified.get((stage, protocol), set()) or
                                     reference in disqualified.get((stage, protocol), set()))
        rows[kind].append(result)
    winners = []
    all_rows = [r for values in rows.values() for r in values]
    by_key = {(r.get("stage", freeze.get("stage")), r["protocol"], r["cell"],
                       r["candidate"], r["reference"], r.get("independent_search")): r
              for r in all_rows}
    for row in all_rows:
        row["transfer_difference"] = None
        if row["cell"] == row["anchor"]:
            continue
        stage = row.get("stage", freeze.get("stage"))
        anchor = by_key.get((stage, row["protocol"], row["anchor"], row["candidate"],
                             row["reference"], row.get("independent_search")))
        if anchor:
            key = (stage, row["protocol"], row["cell"], row["candidate"], row["reference"])
            base_key = (stage, row["protocol"], row["anchor"], row["candidate"], row["reference"])
            row["transfer_difference"] = {
                cohort: _welch(measured[(key, cohort)], measured[(base_key, cohort)])
                for cohort in (1, 2)}
    for row in rows["primary"]:
        if row["primary_result"] != "regression" or row["cell"] == row["anchor"]:
            continue
        stage = row.get("stage", freeze.get("stage"))
        anchor = by_key.get((stage, row["protocol"], row["anchor"], row["candidate"],
                             row["reference"], row.get("independent_search")))
        if anchor and anchor["primary_result"] == "superior":
            key = (stage, row["protocol"], row["cell"], row["candidate"], row["reference"])
            winners.append({"comparison": key, "anchor": row["anchor"],
                            "transfer_difference": row["transfer_difference"]})
    factors = defaultdict(list)
    methods = defaultdict(list)
    for kind, values in rows.items():
        for row in values:
            stage = row.get("stage", freeze.get("stage"))
            method_key = (stage, row.get("task"), row.get("method"))
            methods[method_key].append(row)
            if row.get("factor") and not row["claim_excluded"]:
                factors[(stage, row["protocol"], row["factor"], row.get("level"),
                         row["candidate"], row["reference"])].append(row)
    factor_summary = []
    for key, values in factors.items():
        for cohort in (1, 2):
            by_anchor = defaultdict(list)
            for row in values:
                mean = row["cohorts"][cohort]["mean_log_ratio"]
                if mean is not None:
                    by_anchor[row["anchor"]].append(mean)
            anchor_means = {a: statistics.mean(v) for a, v in by_anchor.items()}
            factor_summary.append({"key": key, "cohort": cohort, "by_anchor": anchor_means,
                                   "equal_anchor_mean": statistics.mean(anchor_means.values())
                                   if anchor_means else None, "descriptive": True})
    method_summary = []
    frozen_series = defaultdict(set)
    failed_series = defaultdict(set)
    for series in freeze.get("series", []):
        key = (series.get("stage", freeze.get("stage")), series["task"], series["method"])
        identifier = series["independent_search"]
        frozen_series[key].add(identifier)
        if series.get("selection_failure"):
            failed_series[key].add(identifier)
    for key in frozen_series:
        methods.setdefault(key, [])
    for key, values in methods.items():
        series = defaultdict(list)
        for row in values:
            series[row.get("independent_search")].append(row)
        for cohort in (1, 2):
            series_means, counts = [], Counter()
            for series_rows in series.values():
                means = [r["cohorts"][cohort]["mean_log_ratio"] for r in series_rows
                         if r["cohorts"][cohort]["mean_log_ratio"] is not None]
                if means:
                    series_means.append(statistics.mean(means))
                counts.update(r["cohorts"][cohort]["classification"] for r in series_rows)
            counts["selection_failure"] += len(failed_series[key])
            method_summary.append({"key": key, "cohort": cohort,
                                   "series_count": len(frozen_series[key] or series),
                                   "classification_counts": dict(counts), "series_means": series_means,
                                   "descriptive": True})
    attempt_rows = []
    for job in jobs:
        job_key = (job.get("stage"), job["cohort"], job["protocol"], job["cell"])
        if job is adopted.get(job_key):
            continue
        for comparison in freeze["comparisons"]:
            if (comparison.get("stage", freeze.get("stage")), comparison["protocol"],
                    comparison["cell"]) != (job.get("stage"), job["protocol"], job["cell"]):
                continue
            candidate, reference = comparison["candidate"], comparison["reference"]
            if candidate == reference or comparison.get("same_identity") is True:
                continue
            effect = _effect(job, candidate, reference)
            q = student_t_quantile(0.975, effect["n_eff"] - 1) if effect["n_eff"] >= 2 else None
            lower, upper = _interval(effect, q)
            attempt_rows.append({"stage": job.get("stage"), "protocol": job["protocol"],
                                 "cell": job["cell"], "cohort": job["cohort"],
                                 "candidate": candidate, "reference": reference,
                                 "attempt": job["attempt"], "attempt_only": True,
                                 "n_eff": effect["n_eff"], "unusable_blocks": effect["unusable_blocks"],
                                 "mean_log_ratio": effect["mean_log_ratio"],
                                 "lower": lower, "upper": upper,
                                 "classification": classify(lower, upper), "interval": "descriptive"})
    return {"primary_rows": rows["primary"], "descriptive_rows": rows["descriptive"] + attempt_rows,
            "known_separate_rows": rows["known_separate"], "winner_changes": winners,
            "factor_summary": factor_summary, "method_summary": method_summary,
            "disqualified": {str(k): sorted(v) for k, v in disqualified.items()},
            "m_by_family": m_by_family}
