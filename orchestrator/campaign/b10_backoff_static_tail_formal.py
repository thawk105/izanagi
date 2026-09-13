"""Preregistered static tail: byte binding, formal WAL consumer and inference.

Exploration contributes only its recorded correctness mode. Numerical inputs
come exclusively from the committed attempts of the admitted formal campaigns.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import buildcache, campaign_lock, ident, p2_2, patchharness, pin, wal
from . import backoff_extended_sweep as family
from .artifact_admission import (
    CampaignReadPurpose, require_admitted_campaign, require_certified_campaign_view,
)
from .backoff_sweep import _BASE, _official_durable_root_policy
from .build_admission import GeneratorId, attest_generator_output, build_run_context
from .loop import run_campaign
from .model import CampaignConfig, Genome
from .pipeline import CorrectnessWorkload, PerfConfig
from ..calibrator import perf_preflight

DOCUMENT_PATH = "docs/b10-backoff-static-tail-preregistration.md"
_BEGIN = b"<!-- IZANAGI-B10-STATIC-TAIL-SPEC-BEGIN -->\n"
_END = b"<!-- IZANAGI-B10-STATIC-TAIL-SPEC-END -->"
_SPEC_BLOCK_RE = re.compile(
    rb"^<!-- IZANAGI-B10-STATIC-TAIL-SPEC-BEGIN -->\n"
    rb"(?P<inner>.*?)^<!-- IZANAGI-B10-STATIC-TAIL-SPEC-END -->(?:\n|\Z)",
    re.MULTILINE | re.DOTALL,
)
_SECTIONS = frozenset("schema_version preregistration study disclosed_exploration grid workloads measurement_order_rule execution analysis_input_contract variability analysis correctness binary_identity provenance cohort_identity failure_conditions future_driver_binding".split())


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _finite(value, *, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (not positive or value > 0)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def extract_spec_bytes(raw: bytes) -> bytes:
    _require(type(raw) is bytes, "document must be bytes")
    matches = list(_SPEC_BLOCK_RE.finditer(raw))
    # Count complete marker lines independently: stray/extra markers are errors.
    lines = raw.split(b"\n")
    _require(lines.count(_BEGIN[:-1]) == 1 and lines.count(_END) == 1
             and len(matches) == 1, "exactly one marker pair required")
    inner = matches[0]["inner"]
    _require(inner.startswith(b"```json\n") and inner.endswith(b"```\n"),
             "spec fence lines differ")
    data = inner[len(b"```json\n"):-len(b"```\n")]
    _require(b"\r" not in data and data.endswith(b"\n")
             and not data.endswith(b"\n\n"), "spec requires LF and one trailing newline")
    data.decode("utf-8")
    return data


@dataclass(frozen=True)
class StaticTailSpec:
    data: dict
    spec_bytes: bytes
    encoding_offset: int
    equivalence_width: float
    effect_span: float
    minimum_persistent_intervals: int

    @property
    def spec_sha256(self):
        return _sha(self.spec_bytes)

    def __getitem__(self, key):
        return self.data[key]


@dataclass(frozen=True)
class PreregistrationBinding:
    spec: StaticTailSpec
    commit: str
    document_blob_sha256: str

    @property
    def spec_sha256(self):
        return self.spec.spec_sha256

    def coordinates(self):
        return {"preregistration_commit": self.commit,
                "preregistration_document_blob_sha256": self.document_blob_sha256,
                "spec_sha256": self.spec_sha256}


def _match(pattern, value, name):
    _require(type(value) is str, f"{name}: expected string")
    match = re.fullmatch(pattern, value)
    _require(match is not None, f"unsupported {name}")
    return match


def parse_preregistration(raw: bytes) -> StaticTailSpec:
    data = extract_spec_bytes(raw)
    doc = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    _require(type(doc) is dict and set(doc) == _SECTIONS, "top-level section set differs")
    _validate_shape(doc, _SPEC_SHAPE)
    _require(doc["schema_version"] == "izanagi-b10-backoff-static-tail-preregistration/v1", "unknown schema")
    _require(doc["preregistration"]["document_path"] == DOCUMENT_PATH, "noncanonical document path")
    driver = doc["future_driver_binding"]
    for key, literal in (("run_kind", "t2500-tail-formal"),
                         ("report_schema", "t2500-backoff-static-tail-formal-report/v1"),
                         ("artifact_stem", "t2500-backoff-static-tail-formal")):
        _require(driver[key] == literal, f"unsupported {key}")
    grid, execution, analysis = doc["grid"], doc["execution"], doc["analysis"]
    rule = _match(r"b_k = round\((\d+) / (\d+)\^\(k/(\d+)\)\) for k in \[([0-9,]+)\], keep b_k > (\d+)", grid["generation_rule"], "generation_rule")
    cap, base, divisor = map(int, rule.group(1, 2, 3))
    indices = [int(k) for k in rule[4].split(",")]
    lower = int(rule[5])
    _require(base > 1 and divisor > 0 and len(set(indices)) == len(indices), "grid generation inputs")
    tail = [math.floor(cap / base ** (k / divisor) + 0.5) for k in indices]
    tail = [b for b in tail if b > lower]
    _require(tail == sorted(set(tail)) == grid["formal_tail_values_us"], "regenerated tail differs")
    _require(cap == grid["representation_cap_us"] == doc["study"]["physical_domain_us"]["upper"]
             and lower == doc["study"]["physical_domain_us"]["lower"], "domain differs")
    _require(grid["regular_ratio"] == base ** (1 / divisor), "regular ratio differs")
    offset = int(_match(r"raw = physical_us \+ (\d+) for every registered point", grid["encoding_rule"], "encoding_rule")[1])
    points = grid["boundary_reference_values_us"] + tail
    _require(points == sorted(set(points)) == grid["analysis_values_us"], "analysis grid differs")
    _require(grid["encoded_static_points"] == [dict(physical_us=b, backoff_fixed_raw=b + offset) for b in points], "raw encoding differs")
    hole = grid["forbidden_raw_range"]
    _require(all(not hole["lower"] <= b + offset <= hole["upper"] for b in points), "raw hole")
    counts = grid["point_counts"]
    _require((counts["boundary_references_per_workload"], counts["formal_tail_points_per_workload"], counts["total_points_per_workload"], counts["saturation_intervals_per_workload"]) == (len(points)-len(tail), len(tail), len(points), len(tail)-1), "point counts differ")
    for key in ("records", "threads", "extime_s", "performance_reps_per_cell", "correctness_reps_per_cell"):
        _require(type(execution[key]) is int and execution[key] > 0, f"execution {key}")
    reps = execution["performance_reps_per_cell"]
    _require(reps == doc["variability"]["rep_count"] == execution["correctness_reps_per_cell"] == doc["correctness"]["verify_records_per_cell"], "rep counts differ")
    _require(doc["variability"]["sample_standard_deviation_ddof"] == 1 and reps > 1, "unsupported ddof")
    _require(0 < doc["variability"]["maximum_cv_exclusive"] < 1, "CV threshold")
    names = [w["name"] for w in doc["workloads"]]
    _require(names == doc["cohort_identity"]["workload_rules"]["the_three_workload_names_must_cover_the_registered_set_exactly_once"], "workload set differs")
    _require(len(names) == len(set(names)) == execution["jobs"] == analysis["workload_count"], "workload counts")
    _require(execution["cells_per_workload"] == len(points) and execution["total_cells"] == len(points)*len(names), "cell counts")
    _require(execution["expected_performance_rep_observations"] == execution["total_cells"]*reps and execution["expected_correctness_rep_observations"] == execution["total_cells"]*execution["correctness_reps_per_cell"], "total reps")
    _require(analysis["adjacent_intervals_per_workload"] == len(tail)-1 and analysis["simultaneous_intervals"] == (len(tail)-1)*len(names), "interval counts")
    limits = analysis["simultaneous_one_sided_limit_count"]
    _require(limits == analysis["simultaneous_intervals"]*analysis["one_sided_limits_per_interval"] and analysis["one_sided_limits_per_interval"] == 2, "limit count")
    _require(analysis["per_limit_one_sided_alpha"] == analysis["familywise_alpha"]/limits, "alpha differs")
    formula = analysis["formulas"]
    _require(int(_match(r"m_i = sum\(a_i_r\) / (\d+)", formula["abort_mean"], "abort_mean")[1]) == reps, "mean divisor")
    _require(int(_match(r"v_i = cv_i\^2 / (\d+)", formula["variance_term"], "variance_term")[1]) == reps, "variance divisor")
    df = _match(r"nu_i = \(v_i \+ v_prev\)\^2 / \(v_i\^2 / (\d+) \+ v_prev\^2 / (\d+)\)", formula["welch_df"], "welch_df")
    _require(int(df[1]) == int(df[2]) == reps-1, "Welch denominators")
    quantile = _match(r"t_i = t_quantile\(1 - ([0-9.]+)/(\d+), nu_i\)", formula["t_quantile"], "t_quantile")
    _require(float(quantile[1]) == analysis["familywise_alpha"] and int(quantile[2]) == limits, "quantile alpha")
    span = float(_match(r"U_i = 1 - exp\(qL_i \* log\(([0-9.]+)\)\)", formula["maximum_abort_reduction_per_doubling"], "effect span")[1])
    _require(formula["minimum_abort_reduction_per_doubling"] == f"L_i = 1 - exp(qU_i * log({span:g}))" and span > 1, "effect span differs")
    rules = analysis["interval_classification"]["rules"]
    _require([r["state"] for r in rules] == ["saturated", "declining", "indeterminate", "saturated", "declining", "indeterminate"], "classification order")
    width = float(_match(r"qhat_i <= 0 and U_i <= ([0-9.]+)", rules[3]["definition"], "saturation definition")[1])
    _require(float(_match(r"L_i > ([0-9.]+)", rules[4]["definition"], "decline definition")[1]) == width and 0 < width < 1, "equivalence width differs")
    location = analysis["saturation_location"]
    persistence = _match(r"smallest j such that intervals I_j\.\.I_(\d+) are all saturated and the run length is at least (\d+)", location["rule"], "persistence")
    _require(int(persistence[1]) == len(tail)-1, "persistent endpoint")
    _require(location["tail_point_indexing"] == ", ".join(f"b_{i}={b}" for i,b in enumerate(tail, 1)), "tail indexing")
    _require(location["leftmost_two_sided_bracketable_location_us"] == tail[1], "leftmost bracket")
    _require(doc["binary_identity"]["physical_amounts_us"] == points and doc["binary_identity"]["expected_trace_disabled_build_results_per_workload"] == len(points), "binary set")
    spec = StaticTailSpec(doc, data, offset, width, span, int(persistence[2]))
    for name in names:
        registered_points(spec, name)
    return spec


def _validate_shape(value, shape, path="spec"):
    if isinstance(shape, tuple):
        _require(type(value) is type(shape[1]) and value == shape[1], f"{path}: unsupported rule")
    elif isinstance(shape, dict):
        _require(type(value) is dict and set(value) == set(shape), f"{path}: key set differs")
        for k, child in shape.items():
            _validate_shape(value[k], child, f"{path}.{k}")
    elif isinstance(shape, list):
        _require(type(value) is list and len(value) == len(shape), f"{path}: array shape differs")
        for i, (item, child) in enumerate(zip(value, shape)):
            _validate_shape(item, child, f"{path}[{i}]")
    elif shape == "number":
        _require(_finite(value), f"{path}: finite number required")
    else:
        _require(type(value).__name__ == shape, f"{path}: expected {shape}")


def _git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    _require(result.returncode == 0, f"git {' '.join(args)}: {result.stderr.decode(errors='replace')}")
    return result.stdout


def load_preregistration(repo_root, commit, *, document_path=DOCUMENT_PATH):
    root = Path(repo_root).absolute()
    _require(document_path == DOCUMENT_PATH, "noncanonical document path")
    path = root / document_path
    _require(not any(p.is_symlink() for p in (path, *path.parents)), "symlink preregistration path")
    _require(root == Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()), "noncanonical repository root")
    resolved = _git(root, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
    _git(root, "merge-base", "--is-ancestor", resolved, "HEAD")
    raw = path.read_bytes()
    _require(raw == _git(root, "show", f"{resolved}:{DOCUMENT_PATH}"), "preregistration blob mismatch")
    return PreregistrationBinding(parse_preregistration(raw), resolved, _sha(raw))


def registered_points(spec, workload):
    row = next((w for w in spec["workloads"] if w["name"] == workload), None)
    _require(row is not None, "unregistered workload")
    physical = list(spec["grid"]["analysis_values_us"])
    random.Random(row["measurement_seed"]).shuffle(physical)
    _require(physical == row["measurement_order_us"], "measurement order differs")
    return [(b, Genome("silo", {**_BASE, "BACK_OFF": 1, "BACKOFF_FIXED": b + spec.encoding_offset})) for b in physical]


def performance_config(spec, workload):
    row = next(w for w in spec["workloads"] if w["name"] == workload)
    execution = spec["execution"]
    return PerfConfig(records=execution["records"], threads=execution["threads"],
                      extime=execution["extime_s"], reps=execution["performance_reps_per_cell"],
                      workload={k: v for k,v in row.items() if k.startswith("ycsb_")})


def config_for(spec, binding, workload, *, contract, ccbench_source_digest, toolchain, correctness_mode):
    _require(spec.spec_sha256 == binding.spec_sha256, "spec/binding mismatch")
    _require(correctness_mode == "legacy", "existing correctness engine supports legacy mode")
    points = registered_points(spec, workload)
    row = next(w for w in spec["workloads"] if w["name"] == workload)
    execution = spec["execution"]
    driver = spec["future_driver_binding"]
    search = {
        "scale": driver["artifact_stem"], "run_kind": driver["run_kind"],
        "workload": workload, "workload_coordinates": row,
        "measurement_order_us": [b for b,g in points],
        "grid": [{"backoff_us": b, "canonical_genome": g.canonical()} for b,g in points],
        "ccbench_source_digest": ccbench_source_digest, "toolchain": toolchain,
        "environment_contract_identity": contract.contract_sha256,
        "calibration_identity": {"path": contract.calibration_ref.path, "sha256": contract.calibration_ref.sha256},
        **binding.coordinates(),
        **{k: execution[k] for k in ("records", "threads", "extime_s", "performance_reps_per_cell", "correctness_reps_per_cell")},
        "correctness_mode": correctness_mode,
        "correctness_flags": CorrectnessWorkload().flags,
        "time_budget": execution["time_budget"],
    }
    cfg = CampaignConfig(spec_slug=f'{driver["artifact_stem"]}-silo-{workload}',
                         search_tag="sweep", spec_content=spec.spec_bytes.decode(),
                         ccbench_commit=pin.CURRENT_PIN, search_config=search,
                         trial=driver["artifact_stem"])
    return ident.bind_environment_contract(cfg, contract)


def require_complete_static_builds(spec, builds):
    expected = {g.canonical() for b,g in registered_points(spec, spec["workloads"][0]["name"])}
    performance = {canonical: result for (canonical,trace),result in builds.items() if trace is False}
    _require(set(performance) == expected, "incomplete performance build set")
    hashes = []
    for canonical, result in performance.items():
        _require(type(result) is buildcache.BuildResult and result.trace is False and result.genome.canonical() == canonical, "performance build binding")
        _require(re.fullmatch(r"[0-9a-f]{64}", result.bin_sha256 or "") is not None, "full performance binary SHA-256 required")
        hashes.append(result.bin_sha256)
    _require(len(set(hashes)) == len(expected), "performance binaries not distinct")


def performance_reps(spec, payload):
    reps, tps = payload.get("reps"), payload.get("tps")
    n = spec["execution"]["performance_reps_per_cell"]
    _require(isinstance(reps, (list, tuple)) and len(reps) == n and isinstance(tps, (list, tuple)) and len(tps) == n, "performance rep count")
    indices = [r.get("rep_index") for r in reps]
    _require(all(type(i) is int for i in indices) and indices == list(range(n)), "rep_index duplicate/missing/order")
    result = []
    for i, rep in enumerate(reps):
        _require(set(rep) == {"rep_index", "abort_counts_", "commit_counts_", "throughput_tps"}, "rep key set")
        a, c = rep["abort_counts_"], rep["commit_counts_"]
        _require(type(a) is int and type(c) is int and a >= 0 and c >= 0 and a+c > 0, "integer counter range")
        _require(_finite(tps[i], positive=True) and _finite(rep["throughput_tps"], positive=True), "throughput finite positive")
        _require(rep["throughput_tps"] == tps[i], "authoritative throughput mismatch")
        rate = a/(a+c)
        _require(0 <= rate <= 1, "abort rate range")
        result.append({**rep, "abort_rate_recomputed": rate})
    return result


def correctness_records(spec, records, expected_mode):
    _require(len(records) == spec["correctness"]["verify_records_per_cell"], "correctness rep count")
    for record in records:
        payload = record.payload
        _require(payload.get("certified") is True, "correctness not certified")
        _require(type(payload.get("anomalies")) is int and payload["anomalies"] == spec["correctness"]["maximum_anomalies_per_rep"], "correctness anomaly")
        _require(payload.get("workload", {}).get("tag") == expected_mode, "correctness mode mismatch")


def load_explore_correctness_mode(campaign):
    view = require_admitted_campaign(campaign, purpose=CampaignReadPurpose.HISTORICAL_RAW)
    lock = campaign_lock.decode_historical_campaign_lock_bytes(Path(view.lock_file).read_bytes())
    _require(lock.identity["search_config"].get("run_kind") == "t2418-explore", "mode source must be exploration")
    records = [r for r in view.records if r.stage == "verify_done"]
    modes = {r.payload.get("workload", {}).get("tag") for r in records}
    _require(len(modes) == 1 and all(isinstance(m, str) and m for m in modes), "exploration mode missing/mixed")
    return modes.pop()


def _plain(value):
    if isinstance(value, Mapping):
        return {k:_plain(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)):
        return [_plain(v) for v in value]
    return value


def _record_value(record):
    return {k: _plain(getattr(record,k)) for k in ("variant", "stage", "env_tag", "ts", "payload")}


def _snapshot(view):
    lock_raw = Path(view.lock_file).read_bytes()
    wal_raw = Path(view.wal_file).read_bytes()
    _require(_sha(lock_raw) == view.decision.campaign_lock_sha256 and _sha(wal_raw) == view.decision.wal_sha256, "admitted snapshot changed")
    _require(wal_raw.endswith(b"\n"), "unterminated WAL")
    frames = [line+b"\n" for line in wal_raw.split(b"\n")[:-1]]
    _require(len(frames) == len(view.records), "WAL physical line count")
    digests = {}
    for frame, admitted in zip(frames, view.records):
        parsed = wal.parse_line(frame.decode("utf-8"))
        _require(_record_value(parsed) == _record_value(admitted), "WAL ordered record mismatch")
        digests[id(admitted)] = _sha(frame)
    return campaign_lock.decode_campaign_lock_bytes(lock_raw), digests


def load_formal_campaign(spec, binding, campaign, *, correctness_mode):
    # Refuse exploration before certified admission; no report-based fallback.
    path = Path(campaign.root if hasattr(campaign, "root") else campaign)
    initial = campaign_lock.decode_campaign_lock_bytes((path/"campaign.lock").read_bytes())
    _require(initial.identity["search_config"].get("run_kind") == spec["future_driver_binding"]["run_kind"], "source run kind is not formal")
    view = require_certified_campaign_view(require_admitted_campaign(path, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE))
    lock, digests = _snapshot(view)
    search = _plain(lock.identity["search_config"])
    campaign_id = Path(view.layout.root).name
    _require(campaign_id == view.decision.campaign_id, "campaign id differs")
    _require(search.get("run_kind") == spec["future_driver_binding"]["run_kind"], "source run kind is not formal")
    for k,v in binding.coordinates().items():
        _require(search.get(k) == v, f"preregistration binding: {k}")
    workload = search["workload"]
    expected = {g.canonical():b for b,g in registered_points(spec, workload)}
    points = []
    for variant,state in wal.replay_admitted_records(view.records).items():
        _require(state.committed, "incomplete/aborted cell")
        start, bench = state.committed_build_start, state.committed_bench
        builds = [r for r in view.records if r.variant == variant
                  and r.stage == "build_done"
                  and r.payload.get("build_attempt_id") == state.committed_attempt_id]
        _require(len(builds) == 1, "committed build record missing/duplicated")
        build = builds[0]
        _require(start is not None and bench is not None and build is not None, "attempt-bound records missing")
        canonical = start.payload.get("genome")
        _require(canonical in expected, "unregistered canonical genome")
        attempt = build.payload.get("build_attempt_id")
        _require(isinstance(attempt,str) and attempt, "attempt id missing")
        verifies = state.committed_verify
        correctness_records(spec, verifies, correctness_mode)
        perf_preflight.validate_perf_observation(
            bench.payload.get("perf_observation"),
            run_cmd=bench.payload.get("run_cmd"),
            leading_indicators=bench.payload.get("leading_indicators"),
        )
        _require(all(r.payload.get("build_attempt_id") == attempt for r in [start,bench,*verifies]), "attempt mismatch")
        _require(all(view.records.index(r) < view.records.index(bench) for r in verifies), "performance preceded correctness")
        def provenance(record, index):
            return dict(source_run_kind=search["run_kind"], campaign_id=campaign_id,
                        campaign_lock_digest=view.decision.campaign_lock_sha256,
                        attempt_id=attempt, rep_index=index, wal_record_digest=digests[id(record)],
                        canonical_genome=canonical,
                        source_measurement={"bench_done":"trace_disabled", "verify_done":"trace_enabled"}[record.stage])
        reps = [{**r, **provenance(bench,r["rep_index"])} for r in performance_reps(spec,bench.payload)]
        points.append(dict(backoff_us=expected[canonical], canonical_genome=canonical,
                           reps=reps, tps=_plain(bench.payload["tps"]),
                           correctness=[{"payload":_plain(r.payload), **provenance(r,i)} for i,r in enumerate(verifies)],
                           perf_bin_sha256=build.payload.get("perf_bin_sha256")))
    _require(len(points) == len(expected) and {p["canonical_genome"] for p in points} == set(expected), "complete unique point set required")
    committed_order = [next(p["canonical_genome"] for p in points
                            if p["reps"][0]["attempt_id"] == r.payload.get("build_attempt_id"))
                       for r in view.records if r.stage == "bench_done"]
    _require(committed_order == [g.canonical() for b,g in registered_points(spec,workload)], "measurement order differs")
    # Completion is an execution receipt, bound to the exact WAL and lock bytes.
    completion = json.loads((path/"reports"/(spec["future_driver_binding"]["artifact_stem"]+"-execution.json")).read_bytes())
    _require(completion["wal_sha256"] == view.decision.wal_sha256 and completion["campaign_lock_sha256"] == view.decision.campaign_lock_sha256, "completion snapshot differs")
    return dict(campaign_id=campaign_id, campaign_lock_digest=view.decision.campaign_lock_sha256,
                identity=search, workload=workload, points=points, completion=completion,
                admission=view.decision.as_receipt())


# Regularized incomplete beta by a convergent continued fraction. Numerical
# convergence tolerance is confined to quadrature, never a decision threshold.
def _beta_fraction(a, b, x):
    qab, qap, qam = a+b, a+1, a-1
    c, d = 1.0, 1-qab*x/qap
    tiny = 1e-300
    if abs(d) < tiny:
        d = tiny
    d = 1/d
    h = d
    for m in range(1, 10001):
        m2 = 2*m
        for aa in (m*(b-m)*x/((qam+m2)*(a+m2)), -(a+m)*(qab+m)*x/((a+m2)*(qap+m2))):
            d = 1+aa*d
            c = 1+aa/c
            if abs(d) < tiny:
                d = tiny
            if abs(c) < tiny:
                c = tiny
            d = 1/d
            delta = d*c
            h *= delta
        if abs(delta-1) < 2e-15:
            return h
    raise ArithmeticError("incomplete beta did not converge")


def _beta(a,b,x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    term = math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    if x < (a+1)/(a+b+2):
        return term*_beta_fraction(a,b,x)/a
    return 1-term*_beta_fraction(b,a,1-x)/b


def student_t_quantile(probability, df):
    _require(0.5 < probability < 1 and _finite(df,positive=True), "Student t domain")
    tail = 1-probability
    low, high = 0.0, 1.0
    def survival(t):
        return 0.5*_beta(df/2,0.5,df/(df+t*t))
    while survival(high) > tail:
        high *= 2
    for _ in range(100):
        mid = (low+high)/2
        if survival(mid) > tail:
            low = mid
        else:
            high = mid
    return (low+high)/2


def cell_statistics(spec, rates, tps):
    n = spec["variability"]["rep_count"]
    _require(len(rates) == len(tps) == n, "statistics rep count")
    mean = statistics.mean(rates)
    sd = statistics.stdev(rates)
    cv = sd/mean if mean else spec["variability"]["all_zero_abort_cell_cv"]
    throughput_cv = statistics.stdev(tps)/statistics.mean(tps)
    return dict(mean=mean, sample_sd=sd, median=statistics.median(rates), abort_rate_cv=cv,
                throughput_tps_cv=throughput_cv, throughput_tps_mean=statistics.mean(tps),
                variance_term=cv*cv/n,
                gate_passed=cv < spec["variability"]["maximum_cv_exclusive"] and throughput_cv < spec["variability"]["maximum_cv_exclusive"])


def analyze_interval(spec, left_us, right_us, left, right):
    result = dict(left_us=left_us, right_us=right_us,
                  **{key:None for key in ("qhat","qL","qU","U","L","U_flat","se","nu","t")})
    m0,m1 = left["mean"],right["mean"]
    _require(not (m0 == 0 and m1 > 0), "zero-to-positive interval")
    if m0 == m1 == 0:
        result.update(state="saturated", reason="both-adjacent-cells-all-zero-abort",
                      **{k:0.0 for k in ("qhat","qL","qU","U","L","U_flat")})
        return result
    if m1 == 0:
        result.update(state="declining", reason="complete-reduction")
        return result
    h = math.log(right_us/left_us)
    qhat = math.log(m1/m0)/h
    result["qhat"] = qhat
    v0,v1 = left["variance_term"],right["variance_term"]
    if v0+v1 == 0:
        result.update(state="indeterminate", reason="zero-pooled-dispersion")
        return result
    n = spec["variability"]["rep_count"]
    nu = (v0+v1)**2/(v0*v0/(n-1)+v1*v1/(n-1))
    t = student_t_quantile(1-spec["analysis"]["per_limit_one_sided_alpha"],nu)
    se = math.sqrt(v0+v1)/h
    qL,qU = qhat-t*se,qhat+t*se
    U,L = -math.expm1(qL*math.log(spec.effect_span)), -math.expm1(qU*math.log(spec.effect_span))
    U_flat = -math.expm1(-t*se*math.log(spec.effect_span))
    state = "saturated" if qhat <= 0 and U <= spec.equivalence_width else "declining" if L > spec.equivalence_width else "indeterminate"
    result.update(state=state, qL=qL,qU=qU,U=U,L=L,U_flat=U_flat,se=se,nu=nu,t=t,
                  confirmed_nonmonotonicity=qL > 0, upward_wiggle=qhat > 0 and qL <= 0)
    return result


def analyze_cohort(spec, campaigns):
    failures, results = [], []
    names = [w["name"] for w in spec["workloads"]]
    try:
        _require(len(campaigns) == len(names) and sorted(c["workload"] for c in campaigns) == sorted(names), "workload coverage")
        _require(len({c["campaign_id"] for c in campaigns}) == len(names), "duplicate campaigns")
        for field in spec["cohort_identity"]["must_match_across_all_three_campaign_locks"]:
            _require(all(field in c["identity"] for c in campaigns) and all(c["identity"][field] == campaigns[0]["identity"][field] for c in campaigns), f"cohort identity: {field}")
    except (ValueError,KeyError,TypeError) as exc:
        failures.append(str(exc))
    for campaign in campaigns:
        try:
            identity = campaign["identity"]
            name = campaign["workload"]
            _require(identity["run_kind"] == spec["future_driver_binding"]["run_kind"], "source run kind is not formal")
            row = next(w for w in spec["workloads"] if w["name"] == name)
            _require(identity["workload_coordinates"] == row, "workload coordinates differ")
            for key in ("records","threads","extime_s","performance_reps_per_cell","correctness_reps_per_cell"):
                _require(identity[key] == spec["execution"][key], f"execution literal: {key}")
            _require(identity["spec_sha256"] == spec.spec_sha256, "analysis spec binding differs")
            points = campaign["points"]
            expected = {b:g.canonical() for b,g in registered_points(spec,name)}
            _require(len(points) == len(expected) and {p["backoff_us"] for p in points} == set(expected), "complete unique point set")
            hashes = [p["perf_bin_sha256"] for p in points]
            _require(all(isinstance(h,str) and re.fullmatch(r"[0-9a-f]{64}",h) for h in hashes) and len(set(hashes)) == len(expected), "performance binary digest set")
            completion = campaign["completion"]
            _require(completion["status"] == "complete", "job incomplete")
            for key,limit in (("sweep_elapsed_s","sweep_cap_s"),("job_elapsed_s","pbs_walltime_s")):
                _require(_finite(completion[key]) and 0 <= completion[key] <= spec["execution"]["time_budget"][limit], f"time budget: {key}")
            stats = {}
            for point in points:
                _require(point["canonical_genome"] == expected[point["backoff_us"]], "point genome mismatch")
                reps = point["reps"]
                parsed = performance_reps(spec, {"reps":[{k:r[k] for k in ("rep_index","abort_counts_","commit_counts_","throughput_tps")} for r in reps],"tps":point["tps"]})
                verifies = point["correctness"]
                _require(len(verifies) == spec["correctness"]["verify_records_per_cell"], "correctness rep count")
                for i,v in enumerate(verifies):
                    _require(v["payload"].get("certified") is True and type(v["payload"].get("anomalies")) is int and v["payload"]["anomalies"] == 0, "correctness not certified/anomaly")
                    _require(v["payload"].get("workload",{}).get("tag") == identity["correctness_mode"], "correctness mode mismatch")
                    _require(v["rep_index"] == i, "correctness rep order")
                for record in [*reps,*verifies]:
                    _require(all(k in record for k in spec["provenance"]["required_per_observation_fields"]), "missing provenance")
                    _require(record["source_run_kind"] == identity["run_kind"] and record["campaign_id"] == campaign["campaign_id"] and record["campaign_lock_digest"] == campaign["campaign_lock_digest"] and record["canonical_genome"] == point["canonical_genome"], "provenance mismatch")
                _require(len({r["attempt_id"] for r in [*reps,*verifies]}) == 1, "mixed attempts")
                observed = cell_statistics(spec,[r["abort_rate_recomputed"] for r in parsed],point["tps"])
                stats[point["backoff_us"]] = observed
                if not observed["gate_passed"]:
                    failures.append(f'{name}/{point["backoff_us"]}: CV gate')
            tail = spec["grid"]["formal_tail_values_us"]
            intervals = [analyze_interval(spec,l,r,stats[l],stats[r]) for l,r in zip(tail,tail[1:])]
            if any(i.get("confirmed_nonmonotonicity") for i in intervals):
                failures.append(f"{name}: confirmed nonmonotonicity")
            onset = next((j for j in range(len(intervals)) if len(intervals)-j >= spec.minimum_persistent_intervals and all(i["state"] == "saturated" for i in intervals[j:])),None)
            location = None if onset is None else dict(location=spec["analysis"]["saturation_location"]["reported_location_when_j_equals_1"] if onset == 0 else tail[onset], bracket=None if onset == 0 else [tail[onset-1],tail[onset]], left_censored=onset == 0)
            state = "indeterminate" if any(i["state"] == "indeterminate" for i in intervals) else "saturated" if onset is not None else "not-observed"
            results.append(dict(workload=name,state=state,intervals=intervals,statistics=stats,saturation_location=location,
                                local_flat_intervals=[i for i in intervals if i["state"] == "saturated"]))
        except (ValueError,KeyError,TypeError,StopIteration,ArithmeticError) as exc:
            failures.append(f'{campaign.get("workload")}: {exc}')
    states = [r["state"] for r in results]
    conditions = [bool(failures), "indeterminate" in states, all(s == "saturated" for s in states), all(s == "not-observed" for s in states), True]
    verdict = next(rule["verdict"] for rule,condition in zip(spec["analysis"]["aggregate_verdict"]["rules"],conditions) if condition)
    return dict(schema_version=spec["future_driver_binding"]["report_schema"], run_kind=spec["future_driver_binding"]["run_kind"], verdict=verdict, failures=failures, workloads=results, campaigns=_plain(campaigns), performance_certified=False, spec_sha256=spec.spec_sha256)


def _create_json(path, value):
    with Path(path).open("x",encoding="utf-8") as stream:
        json.dump(value,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
        stream.write("\n")


def materialize_report(spec, campaigns, output_dir):
    report = analyze_cohort(spec,campaigns)
    root = Path(output_dir)
    root.mkdir(parents=True,exist_ok=True)
    stem = spec["future_driver_binding"]["artifact_stem"]
    paths = [root/(stem+suffix) for suffix in (".json",".dat","-complete.json")]
    _require(not any(p.exists() or p.is_symlink() for p in paths), "report is create-only")
    _create_json(paths[0],report)
    with paths[1].open("x",encoding="utf-8") as stream:
        stream.write("# workload backoff_us rep aborts commits abort_rate throughput_tps\n")
        for campaign in campaigns:
            for point in campaign["points"]:
                for rep in point["reps"]:
                    a,c = rep["abort_counts_"],rep["commit_counts_"]
                    stream.write(f'{campaign["workload"]} {point["backoff_us"]} {rep["rep_index"]} {a} {c} {a/(a+c):.17g} {rep["throughput_tps"]}\n')
    _create_json(paths[2],dict(schema_version=report["schema_version"], run_kind=report["run_kind"], verdict=report["verdict"], spec_sha256=spec.spec_sha256, preregistrations=[{k:c["identity"][k] for k in ("preregistration_commit","preregistration_document_blob_sha256","spec_sha256")} for c in campaigns], artifacts={p.name:_sha(p.read_bytes()) for p in paths[:2]}))
    return report


class SweepDeadline(BaseException):
    """Not swallowed by run_campaign's per-variant Exception recovery."""


@contextmanager
def _deadline(seconds):
    def expired(_sig,_frame):
        raise SweepDeadline("preregistered sweep deadline exceeded")
    previous = signal.signal(signal.SIGALRM,expired)
    timer = signal.setitimer(signal.ITIMER_REAL,seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,*timer)
        signal.signal(signal.SIGALRM,previous)


def scheduler_coordinates():
    job_id = os.environ.get("PBS_JOBID")
    _require(job_id, "PBS job identity missing")
    result = subprocess.run(["qstat","-f","-F","json",job_id],capture_output=True,text=True,check=False)
    _require(result.returncode == 0, "scheduler query failed")
    job = json.loads(result.stdout)["Jobs"][job_id]
    hours,minutes,seconds = map(int,job["Resource_List"]["walltime"].split(":"))
    return dict(job_id=job_id, job_start_epoch=float(job["stime"]), reserved_walltime_s=hours*3600+minutes*60+seconds)


def run_workload(binding, workload, *, explore_campaign, output_root, cache_root, ccbench_dir=None, log=print):
    spec = binding.spec
    mode = load_explore_correctness_mode(explore_campaign)
    ccbench_dir = family._resolve_ccbench_dir(ccbench_dir)
    p2_2._assert_single_tenant()
    site,contract,authorization = p2_2.resolve_site_runtime()
    p2_2._assert_matches_calibration(contract)
    scheduler = scheduler_coordinates()
    _require(scheduler["reserved_walltime_s"] == spec["execution"]["time_budget"]["pbs_walltime_s"], "PBS reservation differs")
    cc,cxx = buildcache.compilers_for_current_site()
    toolchain = buildcache.observed_toolchain_manifest(cc,cxx)
    points = registered_points(spec,workload)
    genomes = [g for b,g in points]
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    def capability_resolver(evidence):
        return attest_generator_output(context,evidence,generator_input_sha256=_sha((spec.spec_sha256+"|"+evidence.genome_sha256).encode()))
    started = time.time()
    receipt = Path(output_root)/(spec["future_driver_binding"]["artifact_stem"]+f"-{workload}-perf-preflight.json")
    with _deadline(min(spec["execution"]["time_budget"]["sweep_cap_s"], scheduler["job_start_epoch"]+scheduler["reserved_walltime_s"]-started)):
        with patchharness.checkout(pin.CURRENT_PIN,base_dir=ccbench_dir) as stock:
            with patchharness.applied(str(Path(__file__).resolve().parents[2]/family.TEMPLATE_PATCH),pin.CURRENT_PIN,ccbench_dir):
                family._assert_backoff_fixed_materialized(ccbench_dir)
                with tempfile.TemporaryDirectory(prefix="izanagi-static-tail-condition-") as base:
                    buildcache.prepare_masstree_fetchcontent(ccbench_dir=ccbench_dir,fetchcontent_base_dir=base,expected_toolchain_manifest=toolchain,configure_timeout_s=900,target_timeout_s=900,site=site)
                    family._require_condition_gate_before_measurement(ccbench_dir,stock_root=stock,points=genomes,cxx=cxx,configure_args=(f"-DFETCHCONTENT_BASE_DIR={base}",),physical_grid=spec["grid"]["analysis_values_us"])
                builds = family._prebuild_backoff_binaries(genomes,contract=contract,cache_root=cache_root,ccbench_dir=ccbench_dir,resolved_cc=cc,resolved_cxx=cxx,expected_toolchain_manifest=toolchain,build_context=context,capability_resolver=capability_resolver)
                require_complete_static_builds(spec,builds)
                from . import source_digest
                source = source_digest.resolve_evidence(
                    genomes[0], pin.CURRENT_PIN, ccbench_dir=ccbench_dir, cxx=cxx,
                ).src_token
                cfg = p2_2._campaign_cfg_for_site(config_for(spec,binding,workload,contract=contract,ccbench_source_digest=source,toolchain=toolchain,correctness_mode=mode),site,contract)
                summary = run_campaign(cfg,genomes,performance_config(spec,workload),contract.env_tag,contract.clocks_per_us,numactl=list(contract.numactl),output_root=output_root,log=log,ccbench_dir=ccbench_dir,cache_root=cache_root,authorization_contract=authorization,env_contract=contract,expected_toolchain_manifest=toolchain,build_context=context,declared_use_class="official",capability_resolver=capability_resolver,perf_preflight_receipt_path=str(receipt),durable_root_policy=_official_durable_root_policy(Path(output_root)),bench_max_rounds=1,correctness=CorrectnessWorkload(reps=spec["execution"]["correctness_reps_per_cell"]),record_rep_integer_counters=True)
    from .replay import discover_campaign_dir
    view = require_certified_campaign_view(discover_campaign_dir(
        cfg.spec_slug, cfg.search_tag, output_root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ))
    completion = dict(status="complete" if summary.committed == len(genomes) and summary.aborted == 0 else "incomplete",
                      sweep_elapsed_s=time.time()-started,
                      job_elapsed_s=time.time()-scheduler["job_start_epoch"],
                      scheduler=scheduler, **binding.coordinates(),
                      wal_sha256=view.decision.wal_sha256,
                      campaign_lock_sha256=view.decision.campaign_lock_sha256)
    _create_json(Path(view.root)/"reports"/(spec["future_driver_binding"]["artifact_stem"]+"-execution.json"), completion)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--preregistration-commit",required=True)
    sub = parser.add_subparsers(dest="command",required=True)
    run = sub.add_parser("run")
    run.add_argument("workload")
    run.add_argument("--explore-campaign",required=True)
    run.add_argument("--output-root",required=True)
    run.add_argument("--cache-root",required=True)
    run.add_argument("--ccbench-dir")
    report = sub.add_parser("report")
    report.add_argument("campaigns",nargs=3)
    report.add_argument("--explore-campaign",required=True)
    report.add_argument("--output-root",required=True)
    args = parser.parse_args(argv)
    binding = load_preregistration(args.repo_root,args.preregistration_commit)
    if args.command == "run":
        summary = run_workload(binding,args.workload,explore_campaign=args.explore_campaign,output_root=args.output_root,cache_root=args.cache_root,ccbench_dir=args.ccbench_dir)
        return 0 if summary.committed == binding.spec["execution"]["cells_per_workload"] and summary.aborted == 0 else 1
    mode = load_explore_correctness_mode(args.explore_campaign)
    campaigns = [load_formal_campaign(binding.spec,binding,p,correctness_mode=mode) for p in args.campaigns]
    result = materialize_report(binding.spec,campaigns,args.output_root)
    return int(result["verdict"] == "invalid")


# Wire shape only; experimental values are consumed from the parsed spec.
_SPEC_SHAPE = {'schema_version': ('literal', 'izanagi-b10-backoff-static-tail-preregistration/v1'),
 'preregistration': {'document_path': ('literal', 'docs/b10-backoff-static-tail-preregistration.md'),
                     'stage_of_d1813': 'int',
                     'formal_run_must_record_containing_commit': ('literal', True),
                     'formal_run_must_record_document_blob_sha256': ('literal', True),
                     'formal_run_must_record_spec_sha256': ('literal', True),
                     'post_result_edits_count_as_preregistration': ('literal', False),
                     'prospective_scope': ('literal', 'formal-cohort-measurement-and-decision-rules-only'),
                     'not_prospective': [('literal', 'grid-position-and-spacing-choice'),
                                         ('literal', 'five-percent-equivalence-width-choice'),
                                         ('literal', 'two-percent-cv-quality-gate-choice'),
                                         ('literal',
                                          'inclusion-of-in-domain-non-saturation-as-a-valid-outcome')],
                     'document_blob_sha256_covers': ('literal', 'raw file bytes without any git blob header'),
                     'spec_sha256_covers': ('literal',
                                            'the utf-8 bytes between the marker lines with the opening and '
                                            'closing code fence lines removed, lf newlines, one trailing '
                                            'newline, no json canonicalization'),
                     'extracted_spec_bytes_must_parse_as_json': ('literal', True),
                     'binding_status_at_v1': ('literal',
                                              'normative-and-time-evidence-only-no-consumer-exists'),
                     'formal_submission_blocked_until_consumer_verified': ('literal', True)},
 'study': {'formal': ('literal', True),
           'claim_scope': ('literal',
                           'descriptive-static-backoff-right-tail-abort-saturation-with-throughput-cost'),
           'mechanism_claim': ('literal', False),
           'performance_certification_claim': ('literal', False),
           'physical_domain_us': {'lower': 'int',
                                  'lower_inclusive': ('literal', False),
                                  'upper': 'int',
                                  'upper_inclusive': ('literal', True)},
           'upper_bound_is_representational_not_physical': ('literal', True),
           'exploration_measurements_in_formal_estimation': ('literal', False),
           'measure_all_points_before_analysis': ('literal', True),
           'early_measurement_stop_allowed': ('literal', False),
           'falsifiable_claim': ('literal', 'a-registered-saturation-location-exists-in-every-workload'),
           'outcome_disjunction_is_classification_not_hypothesis': ('literal', True)},
 'disclosed_exploration': {'run_kind': ('literal', 't2418-explore'),
                           'physical_values_us': ['int', 'int', 'int'],
                           'reps': 'int',
                           'abort_rate_reps_as_printed': {'write-heavy': {'2000': ['number',
                                                                                   'number',
                                                                                   'number',
                                                                                   'number',
                                                                                   'number'],
                                                                          '4000': ['number',
                                                                                   'number',
                                                                                   'number',
                                                                                   'number',
                                                                                   'number'],
                                                                          '9999': ['number',
                                                                                   'number',
                                                                                   'number',
                                                                                   'number',
                                                                                   'number']},
                                                          'balanced': {'2000': ['number',
                                                                                'number',
                                                                                'number',
                                                                                'number',
                                                                                'number'],
                                                                       '4000': ['number',
                                                                                'number',
                                                                                'number',
                                                                                'number',
                                                                                'number'],
                                                                       '9999': ['number',
                                                                                'number',
                                                                                'number',
                                                                                'number',
                                                                                'number']},
                                                          'read-heavy': {'2000': ['number',
                                                                                  'number',
                                                                                  'number',
                                                                                  'number',
                                                                                  'number'],
                                                                         '4000': ['number',
                                                                                  'number',
                                                                                  'number',
                                                                                  'number',
                                                                                  'number'],
                                                                         '9999': ['number',
                                                                                  'number',
                                                                                  'number',
                                                                                  'number',
                                                                                  'number']}},
                           'throughput_tps_reps': {'write-heavy': {'2000': ['int',
                                                                            'int',
                                                                            'int',
                                                                            'int',
                                                                            'int'],
                                                                   '4000': ['int',
                                                                            'int',
                                                                            'int',
                                                                            'int',
                                                                            'int'],
                                                                   '9999': ['int',
                                                                            'int',
                                                                            'int',
                                                                            'int',
                                                                            'int']},
                                                   'balanced': {'2000': ['int', 'int', 'int', 'int', 'int'],
                                                                '4000': ['int', 'int', 'int', 'int', 'int'],
                                                                '9999': ['int', 'int', 'int', 'int', 'int']},
                                                   'read-heavy': {'2000': ['int', 'int', 'int', 'int', 'int'],
                                                                  '4000': ['int', 'int', 'int', 'int', 'int'],
                                                                  '9999': ['int',
                                                                           'int',
                                                                           'int',
                                                                           'int',
                                                                           'int']}},
                           'abort_rate_printed_decimal_places': 'int',
                           'maximum_reported_throughput_cv_static_points': 'number',
                           'maximum_recomputed_abort_cv_from_quantized_rates_static_points': 'number',
                           'abort_cv_from_quantized_rates_is_not_a_precision_basis': ('literal', True),
                           'the_cv_field_of_the_existing_report_is_the_throughput_cv': ('literal', True),
                           'exploration_abort_reduction_per_doubling_point_estimate_range': ('literal',
                                                                                             '0.298-to-0.371'),
                           'observed_abort_direction': ('literal',
                                                        'strictly-decreasing-at-all-three-workloads'),
                           'observed_throughput_direction': ('literal',
                                                             'strictly-decreasing-at-all-three-workloads'),
                           'observed_saturation_status': ('literal',
                                                          'exploratory-interpretation-not-a-formal-verdict'),
                           'observed_saturation_summary': ('literal', 'not-observed-through-9999us'),
                           'grid_selection_timing': ('literal', 'after-exploration-before-formal-run'),
                           'exploration_abscissae_reused_in_formal_grid_us': ['int'],
                           'formal_remeasurement_required_at_reused_abscissae': ('literal', True),
                           'exploration_sample_reuse_allowed': ('literal', False)},
 'grid': {'generation_rule': 'str',
          'anchor': ('literal', 'representation-cap'),
          'regular_ratio': 'number',
          'representation_cap_us': 'int',
          'authoritative_values': ('literal', 'analysis_values_us'),
          'boundary_reference_values_us': ['int'],
          'boundary_reference_in_saturation_intervals': ('literal', False),
          'formal_tail_values_us': ['int', 'int', 'int', 'int', 'int', 'int', 'int'],
          'analysis_values_us': ['int', 'int', 'int', 'int', 'int', 'int', 'int', 'int'],
          'encoding_rule': 'str',
          'encoded_static_points': [{'physical_us': 'int', 'backoff_fixed_raw': 'int'},
                                    {'physical_us': 'int', 'backoff_fixed_raw': 'int'},
                                    {'physical_us': 'int', 'backoff_fixed_raw': 'int'},
                                    {'physical_us': 'int', 'backoff_fixed_raw': 'int'},
                                    {'physical_us': 'int', 'backoff_fixed_raw': 'int'},
                                    {'physical_us': 'int', 'backoff_fixed_raw': 'int'},
                                    {'physical_us': 'int', 'backoff_fixed_raw': 'int'},
                                    {'physical_us': 'int', 'backoff_fixed_raw': 'int'}],
          'forbidden_raw_range': {'lower': 'int',
                                  'upper': 'int',
                                  'reason': ('literal', 'falls into shape branches quotient-1-and-2')},
          'all_registered_raw_values_use_constant_branch': ('literal', True),
          'excluded_context_references': [('literal', 'none'), ('literal', 'adaptive')],
          'point_counts': {'boundary_references_per_workload': 'int',
                           'formal_tail_points_per_workload': 'int',
                           'total_points_per_workload': 'int',
                           'saturation_intervals_per_workload': 'int'}},
 'workloads': [{'name': ('literal', 'write-heavy'),
                'ycsb_zipf_skew': 'str',
                'ycsb_rratio': 'str',
                'ycsb_rmw': 'str',
                'ycsb_max_ope': 'str',
                'measurement_seed': 'int',
                'measurement_order_us': ['int', 'int', 'int', 'int', 'int', 'int', 'int', 'int']},
               {'name': ('literal', 'balanced'),
                'ycsb_zipf_skew': 'str',
                'ycsb_rratio': 'str',
                'ycsb_rmw': 'str',
                'ycsb_max_ope': 'str',
                'measurement_seed': 'int',
                'measurement_order_us': ['int', 'int', 'int', 'int', 'int', 'int', 'int', 'int']},
               {'name': ('literal', 'read-heavy'),
                'ycsb_zipf_skew': 'str',
                'ycsb_rratio': 'str',
                'ycsb_rmw': 'str',
                'ycsb_max_ope': 'str',
                'measurement_seed': 'int',
                'measurement_order_us': ['int', 'int', 'int', 'int', 'int', 'int', 'int', 'int']}],
 'measurement_order_rule': ('literal',
                            'single random.Random(measurement_seed).shuffle over the ascending label list'),
 'execution': {'records': 'int',
               'threads': 'int',
               'extime_s': 'int',
               'performance_reps_per_cell': 'int',
               'correctness_reps_per_cell': 'int',
               'performance_trace_enabled': ('literal', False),
               'correctness_trace_enabled': ('literal', True),
               'jobs': 'int',
               'one_workload_per_job': ('literal', True),
               'cells_per_workload': 'int',
               'total_cells': 'int',
               'expected_performance_rep_observations': 'int',
               'expected_correctness_rep_observations': 'int',
               'shared_execution_constants_are_authoritative': ('literal', False),
               'static_meaning_witness_status': ('literal',
                                                 'unestablished_for_positive_backoff_fixed_as_in_existing_sweep'),
               'new_pointwise_meaning_witness_gate_required': ('literal', False),
               'time_budget': {'sweep_cap_s': 'int',
                               'pbs_walltime_s': 'int',
                               'reduce_grid_or_reps_on_timeout': ('literal', False)}},
 'analysis_input_contract': {'abort_rate_source': ('literal', 'recomputed-from-integer-counters'),
                             'abort_rate_formula': ('literal', 'aborts / (aborts + commits)'),
                             'required_per_rep_integer_fields': [('literal', 'abort_counts_'),
                                                                 ('literal', 'commit_counts_')],
                             'printed_abort_rate_is_not_an_analysis_input': ('literal', True),
                             'fallback_to_printed_abort_rate_allowed': ('literal', False),
                             'counters_currently_persisted_by_campaign_wal': ('literal', False),
                             'field_names_are_normalized_and_do_not_yet_exist_in_the_current_producer': ('literal',
                                                                                                         True),
                             'each_field_must_declare_its_source': ('literal', True),
                             'fields': [{'name': ('literal', 'backoff_us'),
                                         'type': ('literal', 'integer'),
                                         'unit': ('literal', 'microseconds'),
                                         'wal_stage': ('literal', 'build_start'),
                                         'payload_key': ('literal', 'genome'),
                                         'source': ('literal',
                                                    'parse BACKOFF_FIXED out of the canonical genome string '
                                                    'and decode it with the registered encoding rule; the '
                                                    'decoded value must equal one registered grid value')},
                                        {'name': ('literal', 'per_rep_records'),
                                         'type': ('literal', 'array[5] of object'),
                                         'unit': ('literal', 'record'),
                                         'wal_stage': ('literal', 'bench_done'),
                                         'payload_key': ('literal', 'reps'),
                                         'source': ('literal',
                                                    'the formal driver must persist this array; the current '
                                                    'bench_done payload does not have it. Each element has '
                                                    'exactly the keys rep_index, abort_counts_, '
                                                    'commit_counts_, throughput_tps')},
                                        {'name': ('literal', 'abort_counts_reps'),
                                         'type': ('literal', 'array[5] of nonnegative integer'),
                                         'unit': ('literal', 'count'),
                                         'wal_stage': ('literal', 'bench_done'),
                                         'payload_key': ('literal', 'reps[].abort_counts_'),
                                         'source': ('literal', 'bench stdout key abort_counts_ of that rep')},
                                        {'name': ('literal', 'commit_counts_reps'),
                                         'type': ('literal', 'array[5] of nonnegative integer'),
                                         'unit': ('literal', 'count'),
                                         'wal_stage': ('literal', 'bench_done'),
                                         'payload_key': ('literal', 'reps[].commit_counts_'),
                                         'source': ('literal',
                                                    'bench stdout key commit_counts_ of that rep')},
                                        {'name': ('literal', 'abort_rate_reps_recomputed'),
                                         'type': ('literal', 'array[5] of number in [0,1]'),
                                         'unit': ('literal', 'dimensionless'),
                                         'wal_stage': ('literal', 'derived'),
                                         'payload_key': 'NoneType',
                                         'source': ('literal',
                                                    'aborts/(aborts+commits) from the two counter arrays; '
                                                    'never the printed abort_rate, and never the single '
                                                    'leading_indicators.abort_rate of bench_done')},
                                        {'name': ('literal', 'throughput_tps_reps'),
                                         'type': ('literal', 'array[5] of finite positive number'),
                                         'unit': ('literal', 'transactions-per-second'),
                                         'wal_stage': ('literal', 'bench_done'),
                                         'payload_key': ('literal', 'tps'),
                                         'source': ('literal',
                                                    'the existing per-rep throughput array of the bench_done '
                                                    'payload; this array is authoritative for throughput, '
                                                    'and reps[i].throughput_tps must equal tps[i] for every '
                                                    'i')},
                                        {'name': ('literal', 'abort_rate_cv'),
                                         'type': ('literal', 'number'),
                                         'unit': ('literal', 'dimensionless'),
                                         'wal_stage': ('literal', 'derived'),
                                         'payload_key': 'NoneType',
                                         'source': ('literal', 'computed from abort_rate_reps_recomputed')},
                                        {'name': ('literal', 'throughput_tps_cv'),
                                         'type': ('literal', 'number'),
                                         'unit': ('literal', 'dimensionless'),
                                         'wal_stage': ('literal', 'bench_done'),
                                         'payload_key': ('literal', 'cv'),
                                         'source': ('literal',
                                                    'the existing throughput cv of the bench_done payload; '
                                                    'this is the field the report surfaces as cv')},
                                        {'name': ('literal', 'rep_index'),
                                         'type': ('literal', 'integer in 0..4'),
                                         'unit': ('literal', 'index'),
                                         'wal_stage': ('literal', 'bench_done'),
                                         'payload_key': ('literal', 'reps[].rep_index'),
                                         'source': ('literal',
                                                    'an explicit field written by the runner in rep order, '
                                                    'not a positional guess made at read time')},
                                        {'name': ('literal', 'correctness_verify_records'),
                                         'type': ('literal', 'array[5] of record'),
                                         'unit': ('literal', 'verdict'),
                                         'wal_stage': ('literal', 'verify_done'),
                                         'payload_key': ('literal', 'certified'),
                                         'source': ('literal',
                                                    'verify_done records of the admitted wal whose '
                                                    'payload.build_attempt_id equals the committed attempt')},
                                        {'name': ('literal', 'correctness_anomalies'),
                                         'type': ('literal', 'integer'),
                                         'unit': ('literal', 'count'),
                                         'wal_stage': ('literal', 'verify_done'),
                                         'payload_key': ('literal', 'anomalies'),
                                         'source': ('literal', 'must be 0 for every record')},
                                        {'name': ('literal', 'correctness_mode_coordinate'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'mode'),
                                         'wal_stage': ('literal', 'verify_done'),
                                         'payload_key': ('literal', 'workload.tag'),
                                         'source': ('literal',
                                                    'must equal the same coordinate recorded by the '
                                                    't2418-explore run of this family')},
                                        {'name': ('literal', 'trace_disabled_binary_sha256'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'lowercase-hex-64'),
                                         'wal_stage': ('literal', 'build_done'),
                                         'payload_key': ('literal', 'perf_bin_sha256'),
                                         'source': ('literal',
                                                    'the performance (trace-disabled) binary digest; the '
                                                    'trace-enabled digest is a different key and must not be '
                                                    'substituted')},
                                        {'name': ('literal', 'canonical_genome'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'genome'),
                                         'wal_stage': ('literal', 'build_start'),
                                         'payload_key': ('literal', 'genome'),
                                         'source': ('literal',
                                                    'canonical genome string of the admitted wal record')},
                                        {'name': ('literal', 'attempt_id'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'identifier'),
                                         'wal_stage': ('literal', 'build_done'),
                                         'payload_key': ('literal', 'build_attempt_id'),
                                         'source': ('literal',
                                                    'the committed attempt; every observation of a cell must '
                                                    'carry the same value')},
                                        {'name': ('literal', 'source_run_kind'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'identifier'),
                                         'wal_stage': ('literal', 'campaign-envelope'),
                                         'payload_key': 'NoneType',
                                         'source': ('literal',
                                                    'derived from the formal campaign envelope and its lock, '
                                                    'not from an observation payload')},
                                        {'name': ('literal', 'campaign_id'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'identifier'),
                                         'wal_stage': ('literal', 'campaign-envelope'),
                                         'payload_key': 'NoneType',
                                         'source': ('literal',
                                                    'derived from the formal campaign envelope and matched '
                                                    'exactly against the trusted campaign lock')},
                                        {'name': ('literal', 'campaign_lock_digest'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'lowercase-hex-64'),
                                         'wal_stage': ('literal', 'campaign-lock'),
                                         'payload_key': 'NoneType',
                                         'source': ('literal',
                                                    'the trusted campaign lock of this workload job')},
                                        {'name': ('literal', 'wal_record_digest'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'lowercase-hex-64'),
                                         'wal_stage': ('literal', 'derived'),
                                         'payload_key': 'NoneType',
                                         'source': ('literal',
                                                    'sha-256 over the exact stored bytes of the wal jsonl '
                                                    'line the observation was reconstructed from, without '
                                                    're-serializing the json')},
                                        {'name': ('literal', 'source_measurement'),
                                         'type': ('literal', 'string'),
                                         'unit': ('literal', 'identifier'),
                                         'wal_stage': ('literal', 'derived'),
                                         'payload_key': 'NoneType',
                                         'source': ('literal',
                                                    'trace_disabled for observations reconstructed from '
                                                    'bench_done, trace_enabled for records reconstructed '
                                                    'from verify_done')}],
                             'campaign_lock_digest_covers': ('literal',
                                                             'sha-256 over the raw bytes of the campaign '
                                                             'lock file'),
                             'any_field_without_a_resolvable_source_invalidates_the_cohort': ('literal',
                                                                                              True),
                             'correctness_authority': ('literal',
                                                       'certified-field-of-each-committed-verify-record-in-the-formal-campaign-wal'),
                             'point_level_certified_field_is_not_the_correctness_authority': ('literal',
                                                                                              True),
                             'report_level_verdicts_are_not_authoritative': ('literal', True),
                             'existing_report_field_cv_is_throughput_cv': ('literal', True)},
 'variability': {'metrics': [('literal', 'abort_rate_recomputed'), ('literal', 'throughput_tps')],
                 'rep_count': 'int',
                 'sample_standard_deviation_ddof': 'int',
                 'cv_formula': ('literal', 'sample-standard-deviation-divided-by-arithmetic-mean'),
                 'maximum_cv_exclusive': 'number',
                 'all_zero_abort_cell_cv': 'number',
                 'failure_action': ('literal', 'invalidate-entire-formal-cohort')},
 'analysis': {'primary_metric': ('literal', 'abort_rate_recomputed'),
              'throughput_role': ('literal', 'mandatory-cost-context-not-part-of-saturation-predicate'),
              'abort_rate_point_estimator': ('literal', 'arithmetic-mean-of-five-reps'),
              'also_report_median': ('literal', True),
              'interval_axis': ('literal', 'adjacent-formal-tail-values-us'),
              'slope_scale': ('literal', 'log-abort-rate-per-log-backoff-us'),
              'canonical_effect_span': ('literal', 'one-backoff-doubling'),
              'familywise_alpha': 'number',
              'adjacent_intervals_per_workload': 'int',
              'workload_count': 'int',
              'simultaneous_intervals': 'int',
              'one_sided_limits_per_interval': 'int',
              'simultaneous_one_sided_limit_count': 'int',
              'multiplicity_correction': ('literal', 'bonferroni'),
              'per_limit_one_sided_alpha': 'number',
              'confidence_method': ('literal', 'delta-log-ratio-with-welch-satterthwaite-t'),
              'formulas': {'abort_mean': 'str',
                           'abort_cv': ('literal', 'cv_i = sample_sd(a_i_r) / m_i'),
                           'variance_term': 'str',
                           'log_slope': ('literal', 'qhat_i = log(m_i / m_prev) / log(b_i / b_prev)'),
                           'log_slope_se': ('literal', 'se_i = sqrt(v_i + v_prev) / log(b_i / b_prev)'),
                           'welch_df': 'str',
                           't_quantile': 'str',
                           'simultaneous_lower_slope': ('literal', 'qL_i = qhat_i - t_i * se_i'),
                           'simultaneous_upper_slope': ('literal', 'qU_i = qhat_i + t_i * se_i'),
                           'maximum_abort_reduction_per_doubling': 'str',
                           'minimum_abort_reduction_per_doubling': 'str',
                           'flat_case_detectability_diagnostic': ('literal',
                                                                  'U_flat_i = U_i evaluated with qhat_i set '
                                                                  'to 0 and observed cv values kept')},
              'preconditions_checked_before_taking_logs': {'counters_are_nonnegative_exact_integers': ('literal',
                                                                                                       True),
                                                           'abort_plus_commit_greater_than_zero': ('literal',
                                                                                                   True),
                                                           'throughput_finite_and_positive': ('literal',
                                                                                              True),
                                                           'recomputed_abort_rate_within_unit_interval': ('literal',
                                                                                                          True),
                                                           'rep_index_is_exactly_zero_through_four_without_duplicates': ('literal',
                                                                                                                         True),
                                                           'all_zero_left_cell_with_positive_right_cell': ('literal',
                                                                                                           'invalid-cohort-before-any-log')},
              'interval_classification': {'evaluation_order': ('literal', 'first-match-wins'),
                                          'single_table_no_separate_zero_abort_table': ('literal', True),
                                          'rules': [{'state': ('literal', 'saturated'),
                                                     'reason': ('literal',
                                                                'both-adjacent-cells-all-zero-abort'),
                                                     'definition': 'str',
                                                     'no_logarithm_taken': ('literal', True),
                                                     'diagnostics': ('literal',
                                                                     'qhat=qL=qU=0, U=L=0, U_flat=0')},
                                                    {'state': ('literal', 'declining'),
                                                     'reason': ('literal', 'positive-to-all-zero'),
                                                     'definition': 'str',
                                                     'no_logarithm_taken': ('literal', True),
                                                     'diagnostics': ('literal',
                                                                     'qhat, qL, qU, U, L and U_flat are all '
                                                                     'null with the reason '
                                                                     'complete-reduction recorded')},
                                                    {'state': ('literal', 'indeterminate'),
                                                     'reason': ('literal', 'zero-pooled-dispersion'),
                                                     'definition': 'str',
                                                     'treating_se_as_zero_is_forbidden': ('literal', True),
                                                     'observed_in_existing_artifacts': ('literal', True),
                                                     'diagnostics': ('literal',
                                                                     'qL, qU, U, L and U_flat are all null '
                                                                     'with the reason recorded')},
                                                    {'state': ('literal', 'saturated'), 'definition': 'str'},
                                                    {'state': ('literal', 'declining'), 'definition': 'str'},
                                                    {'state': ('literal', 'indeterminate'),
                                                     'reason': ('literal',
                                                                'cannot-distinguish-flat-from-declining'),
                                                     'definition': 'str'}],
                                          'u_flat_is_reported_but_not_used_for_classification': ('literal',
                                                                                                 True),
                                          'states_are_mutually_exclusive_and_exhaustive': ('literal', True),
                                          'all_zero_left_cell_with_positive_right_cell_is_handled_by_the_preconditions': ('literal',
                                                                                                                          True)},
              'saturation_location': {'requires_persistence_to_the_representation_cap': ('literal', True),
                                      'tail_point_indexing': 'str',
                                      'interval_indexing': ('literal', 'I_i = (b_i, b_(i+1)) for i in 1..6'),
                                      'rule': 'str',
                                      'reported_location_when_j_at_least_2': ('literal', 'b_j'),
                                      'reported_bracket_when_j_at_least_2': ('literal', '[b_(j-1), b_j]'),
                                      'reported_location_when_j_equals_1': ('literal',
                                                                            'at-or-below-1250us-left-censored'),
                                      'reported_bracket_when_j_equals_1': ('literal', 'no-lower-endpoint'),
                                      'reporting_j_equals_1_as_the_point_1250_is_forbidden': ('literal',
                                                                                              True),
                                      'leftmost_two_sided_bracketable_location_us': 'int',
                                      'local_flat_pairs_that_do_not_persist': ('literal',
                                                                               'disclosed-as-local-flat-region-not-a-saturation-location')},
              'per_workload_state': {'rules': [{'state': ('literal', 'indeterminate'), 'definition': 'str'},
                                               {'state': ('literal', 'saturated'), 'definition': 'str'},
                                               {'state': ('literal', 'not-observed'), 'definition': 'str'}],
                                     'conditions_are_mutually_exclusive_without_relying_on_order': ('literal',
                                                                                                    True),
                                     'indeterminate_is_not_evidence_of_non_saturation': ('literal', True)},
              'aggregate_verdict': {'evaluation_order': ('literal', 'first-match-wins'),
                                    'rules': [{'verdict': ('literal', 'invalid'), 'definition': 'str'},
                                              {'verdict': ('literal', 'indeterminate-in-region'),
                                               'definition': 'str'},
                                              {'verdict': ('literal', 'saturated-in-all-workloads'),
                                               'definition': 'str'},
                                              {'verdict': ('literal', 'not-observed-in-any-workload'),
                                               'definition': 'str'},
                                              {'verdict': ('literal',
                                                           'not-observed-in-at-least-one-workload'),
                                               'definition': 'str'}],
                                    'exactly_one_verdict_applies': ('literal', True)},
              'no_saturation_wording': ('literal',
                                        'no-preregistered-saturation-observed-within-the-representable-domain-through-9999us'),
              'stopping_rule_kind': ('literal', 'reporting-rule-after-full-grid-not-measurement-early-stop')},
 'correctness': {'separate_trace_enabled_build_required': ('literal', True),
                 'required_verdict': ('literal', 'certified'),
                 'verdict_location': ('literal',
                                      'committed-verify-record-payload-in-the-formal-campaign-wal'),
                 'maximum_anomalies_per_rep': 'int',
                 'all_reps_for_all_cells_required': ('literal', True),
                 'failed_cell_may_reach_performance_measurement': ('literal', False),
                 'reduce_correctness_reps_for_time': ('literal', False),
                 'correctness_mode_must_be_recorded': ('literal', True),
                 'correctness_mode_coordinate': ('literal', 'verify_done payload workload.tag'),
                 'correctness_mode_must_equal_the_t2418_explore_value_of_that_coordinate': ('literal', True),
                 'this_document_does_not_invent_a_mode_name': ('literal', True),
                 'verify_records_per_cell': 'int',
                 'current_family_emits_one_verify_record_per_cell': ('literal', True),
                 'emitting_five_is_a_precondition_not_an_assumption': ('literal', True),
                 'failure_action': ('literal', 'invalidate-entire-formal-cohort')},
 'binary_identity': {'physical_amounts_us': ['int', 'int', 'int', 'int', 'int', 'int', 'int', 'int'],
                     'expected_trace_disabled_build_results_per_workload': 'int',
                     'digest_is_the_trace_disabled_performance_binary': ('literal', True),
                     'trace_enabled_binary_digest_must_not_be_substituted': ('literal', True),
                     'require_exact_build_result_type': ('literal', True),
                     'require_canonical_genome_binding': ('literal', True),
                     'require_full_lowercase_sha256': ('literal', True),
                     'require_complete_amount_set_equality': ('literal', True),
                     'require_all_binary_sha256_values_distinct': ('literal', True),
                     'generic_helper_that_passes_on_fewer_than_two_amounts_may_not_be_the_only_check': ('literal',
                                                                                                        True),
                     'failure_action': ('literal', 'invalidate-entire-formal-cohort')},
 'provenance': {'required_per_observation_fields': [('literal', 'source_run_kind'),
                                                    ('literal', 'campaign_id'),
                                                    ('literal', 'campaign_lock_digest'),
                                                    ('literal', 'attempt_id'),
                                                    ('literal', 'rep_index'),
                                                    ('literal', 'wal_record_digest'),
                                                    ('literal', 'canonical_genome'),
                                                    ('literal', 'source_measurement')],
                'derived_from': ('literal', 'admitted-wal-envelope-of-the-formal-campaign'),
                'self_declared_observation_payload_is_not_trusted': ('literal', True),
                'campaign_id_and_lock_digest_must_match_the_trusted_campaign_lock_exactly': ('literal', True),
                'source_run_kind_must_equal_the_formal_run_kind': ('literal', True),
                'analysis_reconstructed_from': ('literal', 'admitted-wal-of-the-formal-campaign'),
                'input_report_verdicts_are_not_authoritative': ('literal', True)},
 'cohort_identity': {'scope': ('literal', 'the three workload jobs form one cohort and must agree'),
                     'must_match_across_all_three_campaign_locks': [('literal', 'ccbench_source_digest'),
                                                                    ('literal', 'toolchain'),
                                                                    ('literal',
                                                                     'environment_contract_identity'),
                                                                    ('literal', 'calibration_identity'),
                                                                    ('literal', 'preregistration_commit'),
                                                                    ('literal',
                                                                     'preregistration_document_blob_sha256'),
                                                                    ('literal', 'spec_sha256'),
                                                                    ('literal', 'records'),
                                                                    ('literal', 'threads'),
                                                                    ('literal', 'extime_s'),
                                                                    ('literal', 'performance_reps_per_cell'),
                                                                    ('literal', 'correctness_reps_per_cell')],
                     'workload_coordinates_must_not_match_across_jobs': ('literal', True),
                     'workload_rules': {'each_lock_must_equal_its_own_registered_row': ('literal', True),
                                        'the_three_workload_names_must_cover_the_registered_set_exactly_once': [('literal',
                                                                                                                 'write-heavy'),
                                                                                                                ('literal',
                                                                                                                 'balanced'),
                                                                                                                ('literal',
                                                                                                                 'read-heavy')]},
                     'mismatch_action': ('literal', 'invalidate-entire-formal-cohort'),
                     'existing_submission_time_conditions_are_not_relaxed': ('literal', True)},
 'failure_conditions': {'scope': ('literal',
                                  'any-failure-invalidates-the-entire-formal-cohort-for-the-preregistered-claim'),
                        'items': [('literal',
                                   'any-of-24-cells-lacks-five-certified-correctness-reps-or-has-any-anomaly'),
                                  ('literal', 'a-correctness-failing-cell-reaches-performance-measurement'),
                                  ('literal', 'integer-abort-and-commit-counters-are-not-persisted-per-rep'),
                                  ('literal', 'analysis-uses-the-printed-four-decimal-abort-rate'),
                                  ('literal',
                                   'the-eight-trace-disabled-build-results-are-incomplete-mis-bound-truncated-or-not-all-distinct'),
                                  ('literal',
                                   'any-workload-point-or-rep-is-missing-duplicated-nonfinite-or-out-of-registered-range'),
                                  ('literal', 'any-cell-abort-or-throughput-cv-is-at-or-above-0.02'),
                                  ('literal', 'any-adjacent-interval-has-qL-greater-than-zero'),
                                  ('literal',
                                   'the-sweep-exceeds-11700-seconds-or-the-job-does-not-reach-completion-within-18000-seconds'),
                                  ('literal',
                                   'a-job-is-interrupted-and-resumed-without-identical-campaign-identity-preregistration-commit-spec-sha-source-and-toolchain'),
                                  ('literal',
                                   'exploration-samples-enter-formal-reps-cv-intervals-or-verdicts'),
                                  ('literal',
                                   'the-preregistration-commit-blob-sha256-or-spec-sha256-is-unrecorded-or-mismatched'),
                                  ('literal',
                                   'a-counter-is-negative-non-integer-or-abort-plus-commit-is-zero'),
                                  ('literal', 'a-throughput-value-is-non-positive-or-non-finite'),
                                  ('literal', 'a-recomputed-abort-rate-falls-outside-the-unit-interval'),
                                  ('literal',
                                   'rep-indices-are-not-exactly-zero-through-four-without-duplicates'),
                                  ('literal',
                                   'an-interval-has-an-all-zero-left-cell-and-a-positive-right-cell'),
                                  ('literal',
                                   'a-required-provenance-field-is-missing-or-disagrees-with-the-wal-envelope'),
                                  ('literal', 'source-run-kind-is-not-the-formal-run-kind'),
                                  ('literal',
                                   'an-execution-literal-measurement-order-workload-coordinate-or-label-physical-raw-genome-correspondence-differs-from-the-registered-value'),
                                  ('literal',
                                   'the-three-campaign-locks-disagree-on-any-cohort-identity-field'),
                                  ('literal',
                                   'the-correctness-mode-is-unrecorded-or-differs-from-the-t2418-explore-mode'),
                                  ('literal',
                                   'the-trace-enabled-binary-digest-is-used-in-place-of-the-trace-disabled-one'),
                                  ('literal',
                                   'a-per-rep-throughput-value-disagrees-with-the-same-index-of-the-authoritative-tps-array')],
                        'confirmed_nonmonotonicity': {'definition': 'str',
                                                      'action': ('literal',
                                                                 'invalidate-saturation-and-no-saturation-claims')},
                        'unconfirmed_upward_wiggle': {'definition': 'str',
                                                      'action': ('literal',
                                                                 'report-and-do-not-count-that-interval-as-saturated')},
                        'cross_campaign_cell_pooling_allowed': ('literal', False),
                        'failure_reporting': ('literal',
                                              'report-all-observed-values-and-the-failure-reason-as-descriptive-only')},
 'future_driver_binding': {'must_parse_entire_spec': ('literal', True),
                           'code_constants_may_override_spec': ('literal', False),
                           'run_kind': ('literal', 't2500-tail-formal'),
                           'report_schema': ('literal', 't2500-backoff-static-tail-formal-report/v1'),
                           'artifact_stem': ('literal', 't2500-backoff-static-tail-formal'),
                           'forbidden_existing_run_kinds': [('literal', 'extended'),
                                                            ('literal', 't2266-tail'),
                                                            ('literal', 't2418-explore')],
                           'campaign_identity_must_be_disjoint_from_existing_series': ('literal', True),
                           'existing_series_acceptance_sets_may_change': ('literal', False),
                           'existing_series_artifacts_may_change': ('literal', False),
                           'existing_series_report_schemas_may_change': ('literal', False),
                           'extended_sweep_us_constant_may_change': ('literal', False),
                           'exploration_artifacts_may_be_consumed_as_formal_samples': ('literal', False),
                           'preconditions_before_formal_submission': [('literal',
                                                                       'a-consumer-parses-this-spec-and-its-firing-is-demonstrated'),
                                                                      ('literal',
                                                                       'per-rep-integer-abort-and-commit-counters-of-the-performance-run-are-persisted-in-the-wal-and-verified'),
                                                                      ('literal',
                                                                       'per-observation-provenance-fields-are-emitted-and-derivable-from-the-wal-envelope'),
                                                                      ('literal',
                                                                       'five-verify-records-per-cell-are-actually-emitted-the-current-family-emits-one'),
                                                                      ('literal',
                                                                       'the-correctness-mode-coordinate-is-recorded-and-comparable-to-the-t2418-explore-value')],
                           'preconditions_cannot_be_satisfied-by-documentation-alone': ('literal', True)}}

if __name__ == "__main__":
    sys.exit(main())
