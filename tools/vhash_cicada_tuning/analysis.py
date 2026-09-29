"""Pure reductions of diagnostic raw run records; never a comparison gate."""
from __future__ import annotations

import math
import statistics as st
from collections import defaultdict
from typing import Mapping, Sequence

from orchestrator.calibrator.analyze import find_saturation
from orchestrator.calibrator.model import PerfCounters, ScalePoint

from .model import CONTROL, WORKLOADS, canonical


def rss_lower_bound(points: Sequence[Mapping], l3_bytes: int) -> int | None:
    if l3_bytes <= 0:
        raise ValueError("L3 must be positive")
    eligible = [int(p["records"]) for p in points if p.get("maxrss_kb") is not None
                and int(p["maxrss_kb"]) * 1024 >= 4 * l3_bytes]
    return min(eligible, default=None)


def choose_records(points: Sequence[Mapping], l3_bytes: int) -> dict:
    if not points:
        return {"records": None, "reason": "undetermined"}
    if all(p.get("miss_rate") is not None for p in points):
        scales = []
        for p in points:
            counters = PerfCounters(llc_loads=1_000_000,
                                    llc_load_misses=round(float(p["miss_rate"]) * 1_000_000))
            scales.append(ScalePoint(records=int(p["records"]), threads=48,
                                     counters=counters, maxrss_kb=p.get("maxrss_kb")))
        result = find_saturation(scales, l3_bytes=l3_bytes)
        if result.saturated:
            return {"records": result.records, "reason": "observed_saturation_candidate"}
        if result.lower_bound_selected:
            return {"records": result.records, "reason": "D15_RSS_lower_bound"}
    rss = rss_lower_bound(points, l3_bytes)
    return {"records": rss, "reason": "D15_RSS_lower_bound_perf_unavailable" if rss else
            "undetermined"}


def wait_alive(normal: Sequence[float], delayed: Sequence[float]) -> dict:
    if len(normal) != 3 or len(delayed) != 3 or min(normal + delayed) <= 0:
        raise ValueError("wait smoke requires three positive reps per build")
    ratio = st.median(delayed) / st.median(normal)
    return {"ratio": ratio, "alive": ratio < 0.75}


def sample_cv(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = st.mean(values)
    if mean <= 0 or not math.isfinite(mean):
        return None
    return st.stdev(values) / mean


def _valid(rows: Sequence[Mapping], stages: set[str]) -> list[Mapping]:
    return [r for r in rows if r.get("stage") in stages and r.get("perf") is False
            and r.get("exit_code") == 0 and math.isfinite(float(r["throughput_tps"]))]


def _median(rows: Sequence[Mapping]) -> float:
    if not rows:
        raise ValueError("missing runs")
    return st.median(float(r["throughput_tps"]) for r in rows)


def select_j1(rows: Sequence[Mapping], k: int = 3) -> dict[str, list[str]]:
    valid = _valid(rows, {"j1"})
    result = {}
    for workload in ("W1", "W2", "W3", "W4"):
        candidate = defaultdict(list)
        for r in valid:
            if r["workload"] != workload or r["genome"] == canonical(CONTROL):
                continue
            key = (r["job_id"], r["gc_inter_us"])
            control = [c for c in valid if c["workload"] == workload and
                       c["job_id"] == key[0] and c["gc_inter_us"] == key[1] and
                       c["genome"] == canonical(CONTROL)]
            if control:
                candidate[(r["genome"], r["gc_inter_us"])].append(
                    float(r["throughput_tps"]) / _median(control))
        scores = defaultdict(list)
        for (genome, gc), ratios in candidate.items():
            scores[genome].append(st.median(ratios))
        ranked = sorted(scores, key=lambda g: (-max(scores[g]), g))
        result[workload] = ranked[:k]
    return result


def control_cv(rows: Sequence[Mapping], workload: str, records: int) -> dict:
    sessions = defaultdict(list)
    hosts = set()
    clusters = set()
    for r in _valid(rows, {"j0_within", "j1", "j2"}):
        if (r["workload"] == workload and r["records"] == records and
                r["gc_inter_us"] == 10 and r["genome"] == canonical(CONTROL)):
            sessions[r["job_id"]].append(r)
            hosts.add(r["host"])
            clusters.add(r.get("submission_cluster", r["job_id"]))
    medians = [_median(group) for group in sessions.values()]
    return {"cv": sample_cv(medians), "session_count": len(medians),
            "job_count": len(sessions), "cluster_count": len(clusters),
            "host_count": len(hosts), "control": canonical(CONTROL)}


def j2_best(rows: Sequence[Mapping], workload: str, cv: float | None,
            expected: Sequence[tuple[str, int]], session_count: int,
            records: int | None = None, expected_reps: int = 3) -> dict:
    valid = [r for r in _valid(rows, {"j2"}) if r["workload"] == workload
             and (records is None or r["records"] == records)]
    scores = {}
    for genome, gc in expected:
        candidates = [r for r in valid if r["genome"] == genome and r["gc_inter_us"] == gc]
        if len(candidates) != expected_reps:
            return {"status": "undetermined", "reason": "candidate_missing"}
        ratios = []
        for r in candidates:
            control = [c for c in valid if c["job_id"] == r["job_id"] and
                       c["genome"] == canonical(CONTROL) and c["gc_inter_us"] == 10]
            if len(control) != expected_reps:
                return {"status": "undetermined", "reason": "control_missing"}
            ratios.append(float(r["throughput_tps"]) / _median(control))
        scores[(genome, gc)] = st.median(ratios)
    best = min(scores, key=lambda key: (-scores[key], key))
    result = {"status": "descriptive_only", "best": best, "best_score": scores[best],
              "scores": {f"{g}|{gc}": score for (g, gc), score in scores.items()}}
    if cv is None or session_count < 3:
        return {**result, "observed_control_cv_width_candidates": None,
                "candidate_status": "undetermined",
                "candidate_reason": "control_cv_or_sessions_missing"}
    members = sorted(key for key, value in scores.items()
                     if value >= scores[best] * (1 - cv))
    return {**result, "observed_control_cv_width_candidates": members}


def estimate_walltime(spec: Mapping, costs: Mapping) -> int:
    """Minutes, rounded up after the fixed 1.5 safety factor."""
    builds = spec["builds"]
    workers = int(spec.get("build_parallelism", 1))
    if workers < 1:
        raise ValueError("build_parallelism must be positive")
    durations = sorted((float(costs["build_wait_s" if b["wait"] else "build_normal_s"])
                        for b in builds), reverse=True)
    lanes = [0.0] * workers
    for duration in durations:
        lanes[lanes.index(min(lanes))] += duration
    total = float(costs["dependencies_s"]) + max(lanes, default=0.0)
    total += sum(float(costs["run_s"][r["workload"]]) for r in spec["runs"])
    return math.ceil(total * 1.5 / 60)
