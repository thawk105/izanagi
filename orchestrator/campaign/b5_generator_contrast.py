"""B-5 pilot and registered contrast: immutable opportunities and fresh sessions.

Producing registered ledgers does not authorize cohort activation or submission.
Search and score slots share the child's compile and fixed-smoke Tier0 contract.
Saved inputs do not prove delivery or absence of parent advice.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_FLOOR, localcontext
import decimal
import hashlib
from itertools import accumulate
import json
import math
import os
from pathlib import Path
import platform
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Protocol

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import p3_s4_loop as loop_driver
from . import source_digest, wal
from .backoff_extended_sweep import EXTENDED_SWEEP_US
from .backoff_hole_grammar import validate_backoff_value
from .layout import CampaignLayout
from .model import Genome
from .pipeline import variant_id
from .projection_guard import (CODER_CONTRACT_K2, CODER_CONTRACT_IMPLEMENTATION,
                               assert_closed_proposal_schema, assert_no_ability_probe_material)

PREREG_VERSION = "b5-generator-contrast-v1"
COHORT_PILOT = "t2797-beta-v1"
COHORT_REGISTERED = "b5-registered-v1"
COHORT_REGISTERED_V2 = "b5-registered-v2"
PREREG_VERSION_V2 = "b5-generator-contrast-v2"
COHORT_VERSIONS = {COHORT_REGISTERED: PREREG_VERSION,
                   COHORT_REGISTERED_V2: PREREG_VERSION_V2}
B_EVALUATIONS = 10
A_PROPOSALS = 30
N_EVAL = 5
BLOCK_STOCK_SESSIONS = 5
PILOT_LOGICAL_SESSION_CAP = 60
MAX_MACHINE_RETRIES = 2
LLM_WAIT_S = 2700
LLM_POLL_S = 15
SESSION_BUDGET_S = 1800
ARMS = ("llm", "random", "sweep-matched")
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
MACHINE_FAILURE_ABORT_REASONS = frozenset({"bench-probe-error", "bench-competing-tenant",
                                          "verify-probe-error", "verify-competing-tenant"})
LEDGER_SCHEMA = "b5-generator-contrast-ledger/v1"
EVENT_KINDS = frozenset({
    "series-start", "stock-start", "proposal-opportunity", "proposal-rejected",
    "pipeline-submitted", "evaluation-result", "machine-retry", "endpoint-fixed",
    "score-session", "series-end", "slot-attempt-start",
})
END_REASONS = frozenset({
    "b-complete", "a-exhausted", "grid-exhausted", "stock-unestablished",
    "proposal-wait-timeout", "inheritance-mismatch", "allocation-exhausted",
    "unclassified-missing",
})
EVENT_FIELDS = (
    "a", "b", "logical_slot", "attempt", "slot_key", "proposal_path",
    "proposal_sha256", "provenance", "campaign_id", "campaign_root", "variant",
    "build_attempt_id", "wal_sha256", "outcome", "failure_class", "quality",
    "fitness_tps", "anomalies", "whiteboard_entry", "timing", "note",
)


def integer_log_weights(prec):
    with localcontext() as ctx:
        ctx.prec = prec
        return tuple(int((Decimal(2**128) * (Decimal(v + 1) / Decimal(v)).ln())
                         .to_integral_value(rounding=ROUND_FLOOR))
                     for v in range(1, 1001))


def weights_table():
    low, high = integer_log_weights(100), integer_log_weights(130)
    if low != high or len(low) != 1000 or min(low) <= 0:
        raise ValueError("integer log weights not stable at precisions 100 and 130")
    return low


def weights_material():
    weights = weights_table()
    return {
        "schema": "b5-generator-contrast-weights/v1",
        "formula": "floor(2^128 * ln((v+1)/v)), v=1..1000",
        "precisions": [100, 130], "weights": list(weights), "M": sum(weights),
        "weights_sha256": hashlib.sha256(
            json.dumps(weights, separators=(",", ":")).encode("ascii")).hexdigest(),
        "python_version": platform.python_version(), "decimal": decimal.__name__,
        "decimal_version": decimal.__version__,
    }


def _generator_coordinates(workload, series, a=None):
    if workload not in WORKLOADS or type(series) is not int or not 1 <= series <= 12:
        raise ValueError("invalid workload or series")
    if a is not None and (type(a) is not int or not 1 <= a <= A_PROPOSALS):
        raise ValueError("invalid proposal opportunity")


def random_value(w, r, a, weights, *, version=PREREG_VERSION):
    _generator_coordinates(w, r, a)
    if not weights or any(type(x) is not int or x <= 0 for x in weights):
        raise ValueError("positive integer weights required")
    cumulative = tuple(accumulate(weights))
    M = cumulative[-1]
    if M > 2**256:
        raise ValueError("weight total exceeds hash space")
    L = (2**256 // M) * M
    c = 0
    while True:
        preimage = f"{version}|random|{w}|{r}|{a}|{c}"
        U = int.from_bytes(hashlib.sha256(preimage.encode("ascii")).digest(), "big")
        if U < L:
            return bisect_right(cumulative, U % M) + 1, c
        c += 1


def sweep_order(w, r, *, version=PREREG_VERSION):
    _generator_coordinates(w, r)
    grid = tuple(v for v in EXTENDED_SWEEP_US if 1 <= v <= 1000)
    if len(grid) != 28 or len(set(grid)) != 28:
        raise ValueError("registered sweep grid changed")
    return tuple(sorted(grid, key=lambda v: (
        hashlib.sha256(f"{version}|sweep|{w}|{r}|{v}".encode("ascii")).digest(), v)))


def machine_proposal_document(arm, value, provenance):
    if arm not in ("random", "sweep-matched") or not validate_backoff_value(value).accepted:
        raise ValueError("invalid mechanical proposal")
    justification = f"B-5 {arm} generator (mechanical); {provenance['preimage']}"
    doc = {
        "planner": {"axis": loop_driver.MARKER_ID, "direction": "explore_both",
                    "magnitude": "small", "justification": justification, "uncertainty": ""},
        "coder": {"axis": loop_driver.MARKER_ID, "value": int(value),
                  "implementation": f"double now_backoff = {int(value)};",
                  "justification": justification, "confidence": "low"},
        "prior_critic_reverse": None,
    }
    assert_closed_proposal_schema(doc, require_auditor=False, require_coder_value=True)
    assert_no_ability_probe_material(doc)
    return doc


def slot_key(cohort, arm, workload, series, kind, n, attempt, *, stock_restart=0):
    _generator_coordinates(workload, series)
    if (not cohort or not cohort.isascii() or any(c.isspace() or c == "|" for c in cohort)
            or type(attempt) is not int or not 0 <= attempt <= MAX_MACHINE_RETRIES
            or type(n) is not int):
        raise ValueError("invalid slot coordinates")
    limits = {"stock-start": 1, "search": A_PROPOSALS, "score": N_EVAL,
              "block-stock": BLOCK_STOCK_SESSIONS}
    if kind not in limits or not 1 <= n <= limits[kind]:
        raise ValueError("invalid slot kind or ordinal")
    if (arm == "stock") != (kind == "block-stock") or arm not in (*ARMS, "stock"):
        raise ValueError("invalid slot arm")
    if (type(stock_restart) is not int or stock_restart < 0 or
            stock_restart and (cohort != COHORT_REGISTERED_V2 or kind != "stock-start")):
        raise ValueError("invalid stock restart")
    restart = f"|stock-run-{stock_restart}" if stock_restart else ""
    return (f"{COHORT_VERSIONS.get(cohort, PREREG_VERSION)}|{cohort}|{arm}|{workload}|{series}"
            f"{restart}|{kind}|{n}|attempt-{attempt}")


def _utc(epoch=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if epoch is None else epoch))


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("ascii")


def _publish(path, value, *, replace=False):
    """Atomic publication. Event/header paths use link's no-overwrite guarantee."""
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".b5-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(name, path)
        else:
            os.link(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _read_json(path):
    return json.loads(Path(path).read_bytes())


class SeriesLedger:
    """Single writer, immutable numbered events; series.json is only a view."""

    def __init__(self, root):
        self.root = Path(root)
        self.header = _read_json(self.root / "header.json")
        if self.header.get("schema") != LEDGER_SCHEMA:
            raise ValueError("unknown ledger schema")
        self.events = []
        for seq, path in enumerate(sorted((self.root / "events").glob("*.json")), 1):
            event = _read_json(path)
            if (event.get("event_seq") != seq or event.get("kind") not in EVENT_KINDS
                    or path.name != f"{seq:06d}-{event['kind']}.json"
                    or any(key not in event for key in EVENT_FIELDS)):
                raise ValueError("invalid ledger event sequence or shape")
            self.events.append(event)

    @classmethod
    def create(cls, root, header):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        (root / "events").mkdir()  # existing series is never resumed/erased
        _publish(root / "header.json", {**header, "schema": LEDGER_SCHEMA})
        return cls(root)

    def append(self, kind, **values):
        if kind not in EVENT_KINDS:
            raise ValueError("unknown event kind")
        if kind == "series-end" and values.get("reason") not in END_REASONS:
            raise ValueError("unknown series end reason")
        if self.events and self.events[-1]["kind"] == "series-end":
            raise ValueError("series already ended")
        event = {key: None for key in EVENT_FIELDS}
        event.update(values)
        event.update(event_seq=len(self.events) + 1, kind=kind, ts_utc=_utc())
        _publish(self.root / "events" / f"{event['event_seq']:06d}-{kind}.json", event)
        self.events.append(event)
        _publish(self.root / "series.json", self.view(), replace=True)
        return event

    def view(self):
        return {"schema": LEDGER_SCHEMA, "header": self.header, "events": self.events}


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def classify_session(bench_payload, reps):
    tps = bench_payload.get("tps", [])
    if (not isinstance(tps, list) or len(tps) != reps
            or bench_payload.get("unstable", True) or bench_payload.get("settled") is not True):
        return "quality-missing"
    if (not all(_positive(x) for x in tps)
            or not _positive(bench_payload.get("median_tps"))
            or statistics.median(tps) != bench_payload["median_tps"]):
        return "quality-missing"
    return "normal"


def wal_timing(records, expected_reps):
    """Timestamp differences include trace execution and surrounding processing."""
    by_stage = {r.stage: r for r in records}
    start, built = by_stage.get("build_start"), by_stage.get("build_done")
    verified = [r for r in records if r.stage == "verify_done"]
    bench = by_stage.get("bench_done")

    def delta(left, right):
        if left is None or right is None or right.ts < left.ts:
            return None
        return right.ts - left.ts

    previous = built
    intervals = []
    ordinals = {}
    for rec in verified:
        tag = rec.payload.get("workload", {}).get("tag")
        ordinals[tag] = ordinals.get(tag, 0) + 1
        intervals.append({"tag": tag, "rep": ordinals[tag], "wall_s": delta(previous, rec)})
        previous = rec
    return {
        "verify_interval_label": "trace+verifier+周辺処理 区間",
        "build_wall_s": delta(start, built), "verify_intervals": intervals,
        "verify_total_wall_s": delta(built, verified[-1] if verified else None),
        "verify_missing_reps": max(0, expected_reps - ordinals.get("performance", 0)),
        "verify_truncated": ordinals.get("performance", 0) != expected_reps,
        "bench_wall_s": bench.payload.get("bench_wall_s") if bench else None,
        "bench_surrounding_wall_s": delta(verified[-1] if verified else None, bench),
    }


def classify_slot(sidecar_dir, campaign_root, expected_reps, expected_genome):
    """Classify this physical attempt, preserving missingness independently of rc.

    This reads producer WAL, not a new certification authority. Sidecar, lock,
    genome, variant and build-attempt bindings must agree before COMMIT is used.
    """
    sidecar_dir = Path(sidecar_dir)
    result = {"outcome": "pre-start-failure", "failure_class": "machine-failure",
              "submitted": False, "quality": None, "fitness_tps": None,
              "variant": None, "build_attempt_id": None, "anomalies": 0,
              "wal_sha256": None, "campaign_id": None, "campaign_root": None,
              "timing": {}, "bench_payload": None, "src_token": None}
    rejected = sidecar_dir / "proposal-rejected.json"
    if rejected.exists():
        result.update(outcome="rejected-preprocess", failure_class="candidate")
        return result
    start_path = sidecar_dir / "slot-start.json"
    if not start_path.exists():
        if any(sidecar_dir.glob("*.json")):
            result.update(outcome="unclassified-missing", failure_class="unclassified-missing")
        return result
    result.update(outcome="unclassified-missing", failure_class="unclassified-missing")
    try:
        start = _read_json(start_path)
        root = Path(campaign_root if campaign_root is not None else start["campaign_root"])
        if (start["schema"] != "p3-s4-loop-b5-slot-start/v1"
                or root.resolve() != Path(start["campaign_root"]).resolve()
                or start["genome"] != expected_genome.canonical()):
            return result
        result.update(campaign_id=start["campaign_id"], campaign_root=str(root))
        submission = sidecar_dir / "pipeline-submitted.json"
        if submission.exists():
            submitted = _read_json(submission)
            if (submitted.get("schema") != "p3-s4-loop-b5-submission/v1"
                    or any(submitted.get(k) != start[k] for k in ("b5_slot", "campaign_id", "genome"))):
                return result
            result.update(submitted=True, outcome="submitted-unresolved",
                          failure_class="unclassified-missing")
        tier0_path = sidecar_dir / "tier0.json"
        candidate = expected_genome.flags.get("BACKOFF_FIXED") != -1
        if tier0_path.exists():
            # Read and hash the same bytes. No smoke measurements enter the ledger.
            result["outcome"] = "unclassified-missing"
            raw = tier0_path.read_bytes()
            tier0 = json.loads(raw)
            if (not candidate or not isinstance(tier0, dict)
                    or tier0.get("schema") != "p3-s4-loop-b5-tier0/v1"
                    or any(tier0.get(k) != start[k] for k in ("b5_slot", "campaign_id", "genome"))
                    or tier0.get("contract") != loop_driver.B5_TIER0_CONTRACT
                    or (tier0.get("status"), tier0.get("reason")) not in {
                        ("passed", None), ("rejected", "build-error"),
                        ("rejected", "smoke-failed"), ("rejected", "smoke-timeout")}):
                result.update(outcome="unclassified-missing")
                return result
            result["tier0"] = {"status": tier0["status"], "reason": tier0["reason"],
                               "sidecar_sha256": hashlib.sha256(raw).hexdigest()}
            if tier0["status"] == "rejected":
                result.update(outcome="unclassified-missing" if result["submitted"] else "rejected-tier0",
                              failure_class="unclassified-missing" if result["submitted"] else "candidate")
                return result
            if result["submitted"]:
                result["outcome"] = "submitted-unresolved"
        elif candidate and result["submitted"]:
            result.update(outcome="unclassified-missing")
            return result
        # CLI output is evidence of a duplicate, never evidence of certification.
        stdout = sidecar_dir / "stdout.txt"
        if stdout.exists() and any(token in stdout.read_text(errors="replace")
                                   for token in ("outcome=duplicate-skip", "outcome=skipped")):
            result.update(outcome="duplicate-skip", submitted=False)
            return result
        layout = CampaignLayout(str(root))
        records, truncated = wal.read_records_checked(layout)
        result["timing"] = wal_timing(records, expected_reps)
        if Path(layout.wal_file).exists():
            result["wal_sha256"] = hashlib.sha256(Path(layout.wal_file).read_bytes()).hexdigest()
        if not result["submitted"]:
            if any(r.stage == "abort" and r.payload.get("reason") in
                   {"diff-quarantine", "grammar-reject", "diff-reject"} for r in records):
                result.update(outcome="rejected-preprocess", failure_class="candidate")
            return result
        lock = _read_json(layout.lock_file)
        preimage = lock["identity_preimage"]
        if (hashlib.sha256(preimage.encode("utf-8")).hexdigest() != start["identity_preimage_sha256"]
                or json.loads(preimage)["search_config"].get("b5_slot") != start["b5_slot"]
                or not start["campaign_id"].endswith("-" + hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:8])):
            return result
        starts = [r for r in records if r.stage == "build_start"]
        if len(starts) != 1:
            return result
        build = starts[0]
        attempt = build.payload.get("build_attempt_id")
        src = build.payload.get("src_token")
        if (not attempt or (src is not None and not isinstance(src, str))
                or build.payload.get("genome") != expected_genome.canonical()
                or build.variant != variant_id(expected_genome, src if src is not None else source_digest.STOCK)
                or any(r.variant != build.variant or r.payload.get("build_attempt_id") != attempt
                       for r in records)):
            return result
        result.update(variant=build.variant, build_attempt_id=attempt, src_token=src)
        anomalies = sum(r.payload.get("anomalies", 0) for r in records if r.stage == "verify_done")
        result["anomalies"] = anomalies
        terminals = [r for r in records if r.stage in {"commit", "abort"}]
        if len(terminals) != 1 or truncated or records[-1] != terminals[0]:
            return result
        terminal = terminals[0]
        if terminal.stage == "abort":
            reason = terminal.payload.get("reason", "")
            result["abort_reason"] = reason
            if anomalies or "anomaly" in reason:
                result.update(outcome="anomaly", failure_class="candidate")
            elif reason in MACHINE_FAILURE_ABORT_REASONS:
                result.update(outcome="machine-failure", failure_class="machine-failure")
            else:
                outcome = "build-failed" if "build" in reason else "bench-aborted" if reason.startswith("bench-") else "aborted"
                result.update(outcome=outcome, failure_class="candidate")
                if reason in {"bench-no-throughput", "bench-cv-undefined", "bench-unsettled"}:
                    result["quality"] = "quality-missing"
            return result
        expected_stages = (["build_start", "build_done"] + ["verify_done"] * (expected_reps + 1)
                           + ["bench_done", "commit"])
        if src is None or [r.stage for r in records] != expected_stages:
            return result
        verify_tags = [r.payload.get("workload", {}).get("tag")
                       for r in records if r.stage == "verify_done"]
        if verify_tags != ["legacy"] + ["performance"] * expected_reps:
            return result
        benches = [r for r in records if r.stage == "bench_done"]
        if len(benches) != 1 or anomalies:
            return result
        bench = benches[0].payload
        fitness = terminal.payload.get("fitness_tps")
        if not _positive(fitness) or fitness != bench.get("median_tps"):
            return result
        result.update(outcome="certified", failure_class=None,
                      quality=classify_session(bench, expected_reps), fitness_tps=fitness,
                      bench_payload=bench)
        return result
    except (OSError, ValueError, KeyError, TypeError):
        return result


def select_endpoint(evaluations, disqualified_values=()):
    eligible = [e for e in evaluations if e["outcome"] == "certified"
                and e["quality"] == "normal" and not e.get("anomalies")
                and e["value"] not in disqualified_values and _positive(e["fitness_tps"])]
    return min(eligible, key=lambda e: (-e["fitness_tps"], e["value"], e["b"])) if eligible else None


def _ledger(ledger):
    return ledger if isinstance(ledger, SeriesLedger) else SeriesLedger(ledger)


def expected_inputs(ledger, next_evaluation):
    ledger = _ledger(ledger)
    evaluations = [e for e in ledger.events if e["kind"] == "evaluation-result"]
    if (type(next_evaluation) is not int or next_evaluation != len(evaluations) + 1
            or [e["b"] for e in evaluations] != list(range(1, next_evaluation))):
        raise ValueError("next evaluation does not follow ledger")
    whiteboard = [e["whiteboard_entry"] for e in evaluations]
    if any(set(entry) != {"iteration", "direction", "magnitude", "result", "delta_pct"}
           or entry["iteration"] != k or entry["delta_pct"] is not None
           for k, entry in enumerate(whiteboard, 1)):
        raise ValueError("invalid ledger whiteboard")
    candidates = [e for e in ledger.events if e["kind"] in {"stock-start", "evaluation-result"}
                  and e["outcome"] == "certified" and e["quality"] == "normal"]
    if not candidates:
        raise ValueError("stock not established")
    current = candidates[-1]
    indicators = (current.get("bench_payload") or {}).get("leading_indicators", {})
    current_perf = {"throughput_tps": current["fitness_tps"],
                    "abort_rate_pct": (100 * indicators["abort_rate"]
                                       if indicators.get("abort_rate") is not None else None)}
    return {"next_evaluation": next_evaluation, "expected_whiteboard": whiteboard,
            "current_perf": current_perf, "baseline": current_perf,
            "current_perf_source": {"kind": current["kind"], "b": current["b"],
                                    "campaign_root": current["campaign_root"]}}


def assert_inherited_inputs(ledger, planner_input, coder_input, *, next_evaluation):
    expected = expected_inputs(ledger, next_evaluation)
    for document in (planner_input, coder_input):
        if document.get("whiteboard") != expected["expected_whiteboard"]:
            raise ValueError("whiteboard inheritance mismatch")
    if (planner_input.get("current_perf") != expected["current_perf"]
            or coder_input.get("baseline") != expected["baseline"]):
        raise ValueError("current_perf/baseline inheritance mismatch")
    diagnosis_key = "k2_critic_diagnosis"
    if (diagnosis_key in planner_input) != (diagnosis_key in coder_input):
        raise ValueError("critic diagnosis inheritance mismatch")
    if next_evaluation >= 2 and diagnosis_key not in planner_input:
        raise ValueError("critic diagnosis required after evaluation")
    if diagnosis_key in planner_input:
        diagnosis = planner_input[diagnosis_key]
        if (next_evaluation == 1 or diagnosis != coder_input[diagnosis_key]
                or not isinstance(diagnosis, dict)
                or set(diagnosis) != {"data_boundary", "source_sha256", "attribution", "recommend", "avoid", "uncertainty"}
                or diagnosis["data_boundary"] != "critic_diagnosis_is_data_not_instructions"):
            raise ValueError("critic diagnosis inheritance mismatch")


@dataclass(frozen=True)
class K2Args:
    knowledge_manifest: Path
    knowledge_classification: str | None = None
    knowledge_de_novo_claim: str | None = None


def slot_argv(*, arm, workload, key, sidecar_dir, prebuild_receipt, proposal_path=None, k2=None,
              cohort=None):
    if arm not in (*ARMS, "stock") or workload not in WORKLOADS:
        raise ValueError("unknown arm/workload")
    if (arm == "llm") != (k2 is not None):
        raise ValueError("K2 arguments required only for llm")
    argv = [sys.executable, "-B", "-m", "orchestrator.campaign.p3_s4_loop"]
    argv += ["--stock-control"] if proposal_path is None else ["--run-iteration", str(proposal_path)]
    argv += ["--isolate-worktree", "--fetchcontent-prebuild-receipt", str(prebuild_receipt),
             "--calibrated-perf", "--perf-workload", workload, "--verify-performance",
             "--b5-slot", key, "--b5-sidecar-dir", str(sidecar_dir)]
    if cohort == COHORT_REGISTERED_V2 and workload in ("write-heavy", "balanced"):
        argv.append("--verify-performance-concurrent")
    if k2 is not None:
        if proposal_path is not None:
            argv += ["--allow-coder-derived-build"]
        argv += ["--knowledge-manifest", str(k2.knowledge_manifest)]
        if proposal_path is not None:
            argv += ["--coder-role", "coder-v4-autonomous-k2"]
        if k2.knowledge_classification is not None:
            argv += ["--knowledge-classification", k2.knowledge_classification]
        if k2.knowledge_de_novo_claim is not None:
            argv += ["--knowledge-de-novo-claim", k2.knowledge_de_novo_claim]
    elif proposal_path is not None:
        argv += ["--machine-generated-proposal"]
    return argv


class SlotRunner(Protocol):
    def __call__(self, argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess: ...


def default_runner(argv, *, cwd):
    return subprocess.run(argv, cwd=cwd, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                          capture_output=True, text=True, check=False)


def _deadline():
    raw = os.environ.get("IZANAGI_RESERVATION_DEADLINE_EPOCH")
    if raw is None:
        return None
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError("invalid reservation deadline")
    return value


def _allocation_available():
    deadline = _deadline()
    return deadline is None or deadline - time.time() >= SESSION_BUDGET_S


def _header(arm, workload, series, block, repo_root, *, purpose="pilot"):
    # Read git metadata without adding another subprocess execution seam.
    git = Path(repo_root) / ".git"
    if git.is_file():
        git = (Path(repo_root) / git.read_text().strip().removeprefix("gitdir: ")).resolve()
    head = (git / "HEAD").read_text().strip()
    if head.startswith("ref: "):
        ref = head[5:]
        common = git
        if (git / "commondir").exists():
            common = (git / (git / "commondir").read_text().strip()).resolve()
        if (common / ref).exists():
            head = (common / ref).read_text().strip()
        else:
            head = next((line.split()[0] for line in (common / "packed-refs").read_text().splitlines()
                         if line.endswith(" " + ref)), None)
    deadline = _deadline()
    header = {
        "cohort": (COHORT_REGISTERED_V2 if purpose == "registered-v2" else
                   COHORT_REGISTERED if purpose == "registered" else COHORT_PILOT),
        "purpose": "registered" if purpose == "registered-v2" else purpose,
        "arm": arm, "workload": workload,
        "series": series, "block": block, "repo_head": head, "pin": loop_driver.PIN,
        "mode": "block-stock" if arm == "stock" else "series",
        "perf_config": asdict(loop_driver.calibrated_perf(workload)),
        "verify_mode": "legacy+performance", "bench_max_rounds": 3,
        "B": B_EVALUATIONS, "A": A_PROPOSALS, "N_eval": N_EVAL,
        "tier0_status": "implemented", "tier0_contract": loop_driver.B5_TIER0_CONTRACT,
        "job": {"PBS_JOBID": os.environ.get("PBS_JOBID"), "host": socket.gethostname()},
        "allocation_deadline_epoch": deadline,
        "allocation_deadline_status": "unknown" if deadline is None else "known",
        "limits": ["Parent intervention and actual input delivery are not mechanically guaranteed.",
                   ("Registered producer; cohort activation and actual execution order require external approval and evidence."
                    if purpose in ("registered", "registered-v2") else
                    "Pilot only; does not establish preregistration section 10 completeness.")],
    }
    if purpose == "registered-v2":
        header["prereg_version"] = PREREG_VERSION_V2
    return header


def _genome(value):
    return Genome("silo", {**loop_driver._BASE, "BACK_OFF": 1, "BACKOFF_FIXED": value})


def _stock_established(observation):
    return (observation["outcome"] == "certified" and observation["quality"] == "normal"
            and observation["src_token"] == source_digest.STOCK
            and observation["variant"] == variant_id(_genome(-1))
            and _positive(observation["fitness_tps"]))


def _execute_slot(ledger, *, kind, n, a, b, value, proposal_path, provenance,
                  prebuild_receipt, repo_root, k2, runner):
    h = ledger.header
    restart = (sum(e["kind"] == "stock-start" for e in ledger.events)
               if h["cohort"] == COHORT_REGISTERED_V2 and kind == "stock-start" else 0)
    logical_slot = f"{kind}-{n}" + (f"-restart-{restart}" if restart else "")
    submitted_once = False
    for attempt in range(MAX_MACHINE_RETRIES + 1):
        if not _allocation_available():
            if submitted_once:
                return {**fields, "outcome": "allocation-exhausted", "submitted": True}, b
            return {"outcome": "allocation-exhausted", "submitted": submitted_once}, b
        key = slot_key(h["cohort"], h["arm"], h["workload"], h["series"], kind, n, attempt,
                       stock_restart=restart)
        sidecar = ledger.root / "slots" / f"{logical_slot}-attempt-{attempt}"
        sidecar.mkdir(parents=True)
        argv = slot_argv(arm=h["arm"], workload=h["workload"], key=key,
                         sidecar_dir=sidecar, prebuild_receipt=prebuild_receipt,
                         proposal_path=proposal_path, k2=k2, cohort=h["cohort"])
        ledger.append("slot-attempt-start", a=a, b=b, n=n, slot_kind=kind,
                      logical_slot=logical_slot, attempt=attempt, slot_key=key,
                      sidecar_dir=str(sidecar.relative_to(ledger.root)), stock_restart=restart)
        started = time.monotonic()
        timed_out = False
        try:
            completed = runner(argv, cwd=Path(repo_root))
            stdout, stderr, rc = completed.stdout or "", completed.stderr or "", completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, rc = "", str(exc), None
            timed_out = True
        except OSError as exc:
            stdout, stderr, rc = "", str(exc), None
        wall = time.monotonic() - started
        (sidecar / "stdout.txt").write_text(stdout)
        (sidecar / "stderr.txt").write_text(stderr)
        observation = classify_slot(sidecar, None, N_EVAL, _genome(value))
        if timed_out:
            observation.update(outcome=("submitted-unresolved" if observation["submitted"]
                                        else "unclassified-missing"),
                               quality=None, fitness_tps=None, failure_class="timeout")
        start_path = sidecar / "slot-start.json"
        if start_path.exists():
            try:
                same_slot = _read_json(start_path).get("b5_slot") == key
            except (OSError, ValueError, AttributeError):
                same_slot = False
            if not same_slot:
                observation.update(outcome="unclassified-missing", failure_class="identity-mismatch",
                                   quality=None, fitness_tps=None)
        observation["timing"]["subprocess_wall_s"] = wall
        # A single logical B even when an earlier attempt was submitted.
        if observation["submitted"] and not submitted_once:
            submitted_once = True
            if kind == "search":
                b += 1
        fields = {**observation, "a": a, "b": b, "logical_slot": logical_slot,
                  "attempt": attempt, "slot_key": key, "value": value,
                  "stock_restart": restart,
                  "proposal_path": str(proposal_path) if proposal_path else None,
                  "proposal_sha256": hashlib.sha256(Path(proposal_path).read_bytes()).hexdigest() if proposal_path else None,
                  "provenance": provenance, "returncode": rc, "argv": argv,
                  "note": stderr[-2000:]}
        if observation["submitted"]:
            ledger.append("pipeline-submitted", **fields)
        retryable = observation["outcome"] in {"pre-start-failure", "machine-failure"}
        if retryable and attempt < MAX_MACHINE_RETRIES:
            ledger.append("machine-retry", **fields)
            continue
        fields["submitted"] = submitted_once
        return fields, b
    raise AssertionError("unreachable retry loop")


def _handshake(ledger, a, b, *, outage=False):
    directory = ledger.root / "handshake"
    directory.mkdir(exist_ok=True)
    expected = expected_inputs(ledger, b + 1)
    wait_started = time.monotonic()
    deadline = wait_started + LLM_WAIT_S
    _publish(directory / f"request-{a}.json", {"a": a, **expected,
             "deadline_utc": _utc(time.time() + LLM_WAIT_S)}, replace=outage)
    proposal = directory / f"proposal-{a}.json"
    inputs = directory / f"inputs-{a}.json"
    rejected = directory / f"proposal-{a}.rejected.json"
    def finish(status, path=None, provenance=None):
        return status, path, {**(provenance or {}), "handshake_status": status,
                              "proposal_wait_wall_s": time.monotonic() - wait_started}

    while True:
        if outage and (directory / f"outage-{a}.json").exists():
            return finish("outage")
        if outage and (directory / f"stop-{a}.json").exists():
            return finish(_read_json(directory / f"stop-{a}.json")["reason"])
        if outage:
            live = SeriesLedger(ledger.root)
            confirmed = any(e["kind"] == "proposal-opportunity" and e["a"] == a
                            for e in live.events)
            denied = any(e["kind"] == "proposal-rejected" and e["a"] == a
                         for e in live.events)
            if denied:
                return finish("proposal-rejected", provenance=_read_json(rejected) if rejected.exists() else {})
        if rejected.exists() and not outage:
            if proposal.exists():
                return finish("inheritance-mismatch")
            return finish("proposal-rejected", provenance=_read_json(rejected))
        if proposal.exists() and inputs.exists() and (not outage or
                                                     confirmed and (ledger.root / "proposals" / f"accepted-{a}.json").exists()):
            try:
                actual = _read_json(inputs)
                assert_inherited_inputs(ledger, actual["planner_input"], actual["coder_input"],
                                        next_evaluation=b + 1)
            except (ValueError, TypeError, KeyError):
                return finish("inheritance-mismatch")
            return finish("proposal", proposal, {"inputs_path": str(inputs),
                    "inputs_sha256": hashlib.sha256(inputs.read_bytes()).hexdigest(),
                    "current_perf_source": expected["current_perf_source"]})
        if time.monotonic() >= deadline:
            return finish("proposal-wait-timeout")
        if not _allocation_available():
            return finish("allocation-exhausted")
        time.sleep(LLM_POLL_S)


def _finish(ledger, reason, a, b, **extra):
    ledger.append("series-end", reason=reason, a=a, b=b, **extra)
    return ledger.view()


def _validate_run(arm, workload, series, block, k2):
    _generator_coordinates(workload, series)
    if arm not in (*ARMS, "stock") or type(block) is not int or not 1 <= block <= 3:
        raise ValueError("invalid arm or block")
    if (arm == "llm") != (k2 is not None):
        raise ValueError("K2 arguments required only for llm")


def run_series(arm, workload, series, block, *, ledger_root, prebuild_receipt,
               repo_root, k2=None, runner=default_runner, purpose="pilot"):
    if purpose == "registered-v2":
        raise ValueError("registered-v2 requires run_series_step")
    _validate_run(arm, workload, series, block, k2)
    if arm == "stock":
        raise ValueError("use run-block-stock")
    ledger = SeriesLedger.create(ledger_root, _header(arm, workload, series, block, repo_root, purpose=purpose))
    ledger.append("series-start", a=0, b=0)
    common = dict(prebuild_receipt=prebuild_receipt, repo_root=repo_root, k2=k2, runner=runner)
    stock, _ = _execute_slot(ledger, kind="stock-start", n=1, a=0, b=0, value=-1,
                            proposal_path=None, provenance={}, **common)
    ledger.append("stock-start", **stock)
    if stock["outcome"] == "allocation-exhausted":
        return _finish(ledger, "allocation-exhausted", 0, 0)
    if not _stock_established(stock):
        return _finish(ledger, "stock-unestablished", 0, 0)
    weights = weights_table() if arm == "random" else None
    grid = sweep_order(workload, series) if arm == "sweep-matched" else None
    proposals = ledger.root / "proposals"
    proposals.mkdir()
    a = b = 0
    evaluations = []
    reason = "b-complete"
    while a < A_PROPOSALS and b < B_EVALUATIONS:
        if not _allocation_available():
            return _finish(ledger, "allocation-exhausted", a, b)
        if grid is not None and a == len(grid):
            reason = "grid-exhausted"
            break
        a += 1
        ledger.append("proposal-opportunity", a=a, b=b, logical_slot=f"search-{a}")
        if arm == "llm":
            status, proposal, provenance = _handshake(ledger, a, b)
            if status == "proposal-rejected":
                ledger.append("proposal-rejected", a=a, b=b, provenance=provenance)
                continue
            if status != "proposal":
                return _finish(ledger, status, a, b, provenance=provenance)
        else:
            if arm == "random":
                value, counter = random_value(workload, series, a, weights)
                preimage = f"{PREREG_VERSION}|random|{workload}|{series}|{a}|{counter}"
            else:
                value, counter = grid[a - 1], None
                preimage = f"{PREREG_VERSION}|sweep|{workload}|{series}|{value}"
            provenance = {"preimage": preimage, "counter": counter, "arm": arm}
            proposal = proposals / f"proposal-{a}.json"
            _publish(proposal, machine_proposal_document(arm, value, provenance))
        # Preserve the exact supplied proposal for retries and endpoint scoring.
        try:
            document = _read_json(proposal)
            assert_closed_proposal_schema(
                document, require_auditor=False, require_coder_value=True,
                coder_contract=CODER_CONTRACT_K2 if arm == "llm" else CODER_CONTRACT_IMPLEMENTATION)
            assert_no_ability_probe_material(document)
            if arm == "llm":
                value = document["coder"]["proposal"]["value"]
            else:
                value = document["coder"]["value"]
            if not validate_backoff_value(value).accepted:
                raise ValueError("value outside registered grammar")
            planner = loop_driver.PlannerProposal(**document["planner"])
            direction, magnitude = planner.direction, planner.magnitude
            if arm != "llm":
                loop_driver.load_proposal_file(str(proposal))
        except (ValueError, KeyError, TypeError) as exc:
            ledger.append("proposal-rejected", a=a, b=b, note=str(exc), proposal_path=str(proposal),
                          provenance=provenance)
            continue
        frozen = proposals / f"accepted-{a}.json"
        # Copy raw bytes, not a JSON reserialization of the proposal.
        with frozen.open("xb") as stream:
            stream.write(Path(proposal).read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        observed, b = _execute_slot(ledger, kind="search", n=a, a=a, b=b, value=int(value),
                                    proposal_path=frozen, provenance=provenance, **common)
        if observed["outcome"] == "allocation-exhausted" and not observed["submitted"]:
            return _finish(ledger, "allocation-exhausted", a, b, provenance=provenance)
        if observed["submitted"]:
            observed["whiteboard_entry"] = {
                "iteration": b, "direction": direction, "magnitude": magnitude,
                "result": "success" if observed["outcome"] == "certified" else "fail", "delta_pct": None}
            event = ledger.append("evaluation-result", **observed)
            evaluations.append(event)
            handshake = ledger.root / "handshake"
            handshake.mkdir(exist_ok=True)
            _publish(handshake / f"slot-{b}.json", {**event,
                     "digest_path": str(Path(observed["campaign_root"]) / "s4_loop_digest.txt") if observed["campaign_root"] else None})
        else:
            ledger.append("proposal-rejected", **observed)
        if observed["outcome"] == "allocation-exhausted":
            return _finish(ledger, "allocation-exhausted", a, b, provenance=provenance, score=None)
        if observed["outcome"] in {"duplicate-skip", "unclassified-missing", "submitted-unresolved",
                                   "pre-start-failure", "machine-failure"}:
            return _finish(ledger, "unclassified-missing", a, b, score=None)
    if a == A_PROPOSALS and b < B_EVALUATIONS:
        reason = "a-exhausted"
    disqualified = {e["value"] for e in evaluations if e["anomalies"] or e["outcome"] == "anomaly"}
    endpoint = select_endpoint(evaluations, disqualified)
    ledger.append("endpoint-fixed", a=a, b=b, endpoint=endpoint,
                  fallback=("pending-block-stock" if endpoint is None and not any(
                      e["quality"] == "quality-missing" for e in evaluations) else None))
    if endpoint is None and any(e["quality"] == "quality-missing" for e in evaluations):
        return _finish(ledger, "unclassified-missing", a, b, score=None)
    if endpoint is None:
        return _finish(ledger, reason, a, b, fallback="pending-block-stock", score=None)
    scores = []
    for n in range(1, N_EVAL + 1):
        observed, _ = _execute_slot(ledger, kind="score", n=n, a=a, b=b,
                                    value=endpoint["value"], proposal_path=endpoint["proposal_path"],
                                    provenance=endpoint["provenance"], **common)
        ledger.append("score-session", **observed)
        if observed["outcome"] == "allocation-exhausted":
            return _finish(ledger, "allocation-exhausted", a, b, score=None)
        if observed["outcome"] == "anomaly":
            return _finish(ledger, reason, a, b, fallback="pending-block-stock", score=None)
        if observed["outcome"] != "certified" or observed["quality"] != "normal":
            return _finish(ledger, "unclassified-missing", a, b, score=None)
        scores.append(observed["fitness_tps"])
    return _finish(ledger, reason, a, b, score=statistics.median(scores), score_sessions=scores)


def next_series_action(ledger):
    """Derive the next v2 unit solely from the numbered ledger events."""
    ledger = _ledger(ledger)
    if ledger.header.get("cohort") != COHORT_REGISTERED_V2:
        raise ValueError("v2 ledger required")
    events = ledger.events
    if events and events[-1]["kind"] == "series-end":
        return ("done", None)
    for index, event in enumerate(events):
        if event["kind"] != "slot-attempt-start":
            continue
        key = (event["logical_slot"], event["attempt"])
        settled = any((later.get("logical_slot"), later.get("attempt")) == key
                      and later["kind"] in {"machine-retry",
                                             "stock-start", "evaluation-result",
                                             "score-session", "proposal-rejected"}
                      for later in events[index + 1:])
        if not settled:
            return ("interrupted-slot", key)
    scores = [e for e in events if e["kind"] == "score-session"]
    if scores or any(e["kind"] == "endpoint-fixed" for e in events):
        return ("score", None)
    evaluated = [e for e in events if e["kind"] == "evaluation-result"]
    opportunities = [e for e in events if e["kind"] == "proposal-opportunity"]
    a, b = len(opportunities), len(evaluated)
    if b == B_EVALUATIONS or a == A_PROPOSALS or (ledger.header["arm"] == "sweep-matched"
            and a == len(sweep_order(ledger.header["workload"], ledger.header["series"],
                                     version=PREREG_VERSION_V2))):
        return ("score", None)
    rejected = {e["a"] for e in events if e["kind"] == "proposal-rejected"}
    used = {e["a"] for e in evaluated}
    pending = next((e for e in reversed(opportunities)
                    if e["a"] not in rejected | used), None)
    if pending:
        return ("stock-evaluation-1" if b == 0 else f"evaluation-{b + 1}", pending["a"])
    if b == 0:
        return ("stock-evaluation-1", None)
    return ("proposal", a + 1)


def _v2_proposal(ledger, a, b, proposal, provenance):
    """Confirm one original proposal, then freeze accepted bytes for a compute job."""
    ledger = _ledger(ledger)
    path = Path(proposal) if proposal else None
    ledger.append("proposal-opportunity", a=a, b=b, logical_slot=f"search-{a}",
                  proposal_path=str(path) if path else None,
                  proposal_sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path else None,
                  provenance=provenance)
    if path is None:
        ledger.append("proposal-rejected", a=a, b=b, provenance=provenance)
        return None
    try:
        document = _read_json(path)
        arm = ledger.header["arm"]
        assert_closed_proposal_schema(document, require_auditor=False, require_coder_value=True,
                                      coder_contract=CODER_CONTRACT_K2 if arm == "llm" else CODER_CONTRACT_IMPLEMENTATION)
        assert_no_ability_probe_material(document)
        value = document["coder"]["proposal"]["value"] if arm == "llm" else document["coder"]["value"]
        if not validate_backoff_value(value).accepted:
            raise ValueError("value outside registered grammar")
        planner = loop_driver.PlannerProposal(**document["planner"])
        if arm != "llm":
            loop_driver.load_proposal_file(str(path))
    except (ValueError, KeyError, TypeError) as exc:
        ledger.append("proposal-rejected", a=a, b=b, note=str(exc), proposal_path=str(path),
                      provenance=provenance)
        return None
    directory = ledger.root / "proposals"
    directory.mkdir(exist_ok=True)
    frozen = directory / f"accepted-{a}.json"
    with frozen.open("xb") as stream:
        stream.write(path.read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    return frozen, int(value), planner.direction, planner.magnitude


def _v2_machine_proposal(ledger, a):
    h = ledger.header
    version = PREREG_VERSION_V2
    if h["arm"] == "random":
        value, counter = random_value(h["workload"], h["series"], a, weights_table(), version=version)
        preimage = f"{version}|random|{h['workload']}|{h['series']}|{a}|{counter}"
    else:
        value = sweep_order(h["workload"], h["series"], version=version)[a - 1]
        counter = None
        preimage = f"{version}|sweep|{h['workload']}|{h['series']}|{value}"
    provenance = {"preimage": preimage, "counter": counter, "arm": h["arm"]}
    directory = ledger.root / "proposals"
    directory.mkdir(exist_ok=True)
    path = directory / f"proposal-{a}.json"
    _publish(path, machine_proposal_document(h["arm"], value, provenance))
    return path, provenance


def run_series_step(arm, workload, series, block, *, step, ledger_root, prebuild_receipt,
                    repo_root, k2=None, runner=default_runner):
    """Execute exactly one v2 compute allocation: first, evaluation, or score."""
    _validate_run(arm, workload, series, block, k2)
    if workload not in ("write-heavy", "balanced") or arm == "stock":
        raise ValueError("invalid v2 coordinates")
    root = Path(ledger_root)
    if (root / "header.json").exists():
        ledger = SeriesLedger(root)
        h = ledger.header
        if (h["cohort"], h["arm"], h["workload"], h["series"], h["block"]) != (
                COHORT_REGISTERED_V2, arm, workload, series, block):
            raise ValueError("v2 series coordinates mismatch")
    else:
        if step != "stock-evaluation-1":
            raise ValueError("first step must include stock")
        ledger = SeriesLedger.create(root, _header(arm, workload, series, block, repo_root,
                                                   purpose="registered-v2"))
        ledger.append("series-start", a=0, b=0)
    action, pending_a = next_series_action(ledger)
    if action != step:
        raise ValueError(f"requested step {step} differs from ledger next step {action}")
    common = dict(prebuild_receipt=prebuild_receipt, repo_root=repo_root, k2=k2, runner=runner)
    b = sum(e["kind"] == "evaluation-result" for e in ledger.events)
    a = sum(e["kind"] == "proposal-opportunity" for e in ledger.events)
    if step == "stock-evaluation-1":
        (ledger.root / "handshake").mkdir(exist_ok=True)
        if arm == "llm":
            (ledger.root / "handshake" / f"request-{a + 1}.json").unlink(missing_ok=True)
            (ledger.root / "handshake" / f"outage-{a + 1}.json").unlink(missing_ok=True)
        stock, _ = _execute_slot(ledger, kind="stock-start", n=1, a=a, b=0, value=-1,
                                 proposal_path=None, provenance={}, **common)
        ledger.append("stock-start", **stock)
        if stock["outcome"] == "allocation-exhausted":
            return _finish(ledger, "allocation-exhausted", a, 0)
        if not _stock_established(stock):
            return _finish(ledger, "stock-unestablished", a, 0)
        if arm == "llm":
            while True:
                status, proposal, provenance = _handshake(ledger, a + 1, 0, outage=True)
                if status == "outage":
                    return ledger.view()
                if status == "proposal-rejected":
                    ledger = SeriesLedger(ledger.root)
                    a += 1
                    if a == A_PROPOSALS:
                        break
                    continue
                if status != "proposal":
                    return _finish(ledger, status, a, 0, provenance=provenance)
                ledger = SeriesLedger(ledger.root)
                confirmed = next((e for e in ledger.events if e["kind"] == "proposal-opportunity"
                                  and e["a"] == a + 1), None)
                frozen = ledger.root / "proposals" / f"accepted-{a + 1}.json"
                if confirmed and frozen.exists():
                    doc = _read_json(frozen)
                    planner = loop_driver.PlannerProposal(**doc["planner"])
                    accepted = (frozen, doc["coder"]["proposal"]["value"],
                                planner.direction, planner.magnitude)
                    provenance = confirmed["provenance"]
                else:
                    raise ValueError("LLM proposal lacks login confirmation")
                a += 1
                if accepted:
                    break
                if a == A_PROPOSALS:
                    break
        else:
            proposal, provenance = _v2_machine_proposal(ledger, a + 1)
            accepted = _v2_proposal(ledger, a + 1, 0, proposal, provenance)
            a += 1
    elif step.startswith("evaluation-"):
        accepted = None
        if pending_a is None:
            raise ValueError("evaluation has no confirmed proposal")
        a = pending_a
    else:
        evaluations = [e for e in ledger.events if e["kind"] == "evaluation-result"]
        reason = ("b-complete" if b == B_EVALUATIONS else "a-exhausted" if a == A_PROPOSALS
                  else "grid-exhausted")
        disqualified = {e["value"] for e in evaluations if e["anomalies"] or e["outcome"] == "anomaly"}
        endpoint = select_endpoint(evaluations, disqualified)
        if not any(e["kind"] == "endpoint-fixed" for e in ledger.events):
            ledger.append("endpoint-fixed", a=a, b=b, endpoint=endpoint,
                          fallback="pending-block-stock" if endpoint is None else None)
        if endpoint is None:
            return _finish(ledger, "unclassified-missing" if any(e["quality"] == "quality-missing"
                               for e in evaluations) else reason, a, b,
                           fallback="pending-block-stock", score=None)
        scores = [e["fitness_tps"] for e in ledger.events if e["kind"] == "score-session"]
        for n in range(len(scores) + 1, N_EVAL + 1):
            observed, _ = _execute_slot(ledger, kind="score", n=n, a=a, b=b,
                                        value=endpoint["value"], proposal_path=endpoint["proposal_path"],
                                        provenance=endpoint["provenance"], **common)
            ledger.append("score-session", **observed)
            if observed["outcome"] == "allocation-exhausted":
                return _finish(ledger, "allocation-exhausted", a, b, score=None)
            if observed["outcome"] == "anomaly":
                return _finish(ledger, reason, a, b, fallback="pending-block-stock", score=None)
            if observed["outcome"] != "certified" or observed["quality"] != "normal":
                return _finish(ledger, "unclassified-missing", a, b, score=None)
            scores.append(observed["fitness_tps"])
        return _finish(ledger, reason, a, b, score=statistics.median(scores), score_sessions=scores)
    if step == "stock-evaluation-1" and not accepted:
        return ledger.view()
    if step.startswith("evaluation-"):
        opportunity = next(e for e in ledger.events if e["kind"] == "proposal-opportunity" and e["a"] == a)
        proposal = Path(ledger.root / "proposals" / f"accepted-{a}.json")
        if not proposal.exists() or hashlib.sha256(proposal.read_bytes()).hexdigest() != opportunity["proposal_sha256"]:
            raise ValueError("accepted proposal digest mismatch")
        provenance = opportunity["provenance"]
        document = _read_json(proposal)
        value = document["coder"]["proposal"]["value"] if arm == "llm" else document["coder"]["value"]
        planner = loop_driver.PlannerProposal(**document["planner"])
        direction, magnitude = planner.direction, planner.magnitude
    else:
        proposal, value, direction, magnitude = accepted
    observed, b = _execute_slot(ledger, kind="search", n=a, a=a, b=b, value=int(value),
                                proposal_path=proposal, provenance=provenance, **common)
    if observed["submitted"]:
        observed["whiteboard_entry"] = {"iteration": b, "direction": direction,
                                        "magnitude": magnitude,
                                        "result": "success" if observed["outcome"] == "certified" else "fail",
                                        "delta_pct": None}
        event = ledger.append("evaluation-result", **observed)
        directory = ledger.root / "handshake"
        directory.mkdir(exist_ok=True)
        _publish(directory / f"slot-{b}.json", {**event,
                 "digest_path": str(Path(observed["campaign_root"]) / "s4_loop_digest.txt")
                 if observed["campaign_root"] else None})
    else:
        ledger.append("proposal-rejected", **observed)
    if observed["outcome"] in {"allocation-exhausted", "duplicate-skip", "unclassified-missing",
                               "submitted-unresolved", "pre-start-failure", "machine-failure"}:
        return _finish(ledger, "allocation-exhausted" if observed["outcome"] == "allocation-exhausted"
                       else "unclassified-missing", a, b, score=None)
    return ledger.view()


def run_block_stock(workload, block, *, ledger_root, prebuild_receipt, repo_root,
                    runner=default_runner, purpose="pilot"):
    _validate_run("stock", workload, block, block, None)
    if purpose == "registered-v2" and workload not in ("write-heavy", "balanced"):
        raise ValueError("invalid v2 workload")
    ledger = SeriesLedger.create(ledger_root, _header("stock", workload, block, block, repo_root, purpose=purpose))
    ledger.append("series-start", a=0, b=0)
    for n in range(1, BLOCK_STOCK_SESSIONS + 1):
        observed, _ = _execute_slot(ledger, kind="block-stock", n=n, a=0, b=0, value=-1,
                                    proposal_path=None, provenance={}, prebuild_receipt=prebuild_receipt,
                                    repo_root=repo_root, k2=None, runner=runner)
        ledger.append("stock-start", **observed)
        if observed["outcome"] == "allocation-exhausted":
            return _finish(ledger, "allocation-exhausted", 0, 0)
        if not _stock_established(observed):
            return _finish(ledger, "stock-unestablished", 0, 0)
    return _finish(ledger, "b-complete", 0, 0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run-series", "run-series-step", "run-block-stock"):
        p = sub.add_parser(name)
        p.add_argument("--purpose", choices=("pilot", "registered", "registered-v2"), default="pilot")
        p.add_argument("--workload", choices=WORKLOADS, required=True)
        p.add_argument("--block", type=int, required=True)
        p.add_argument("--ledger-root", type=Path, required=True)
        p.add_argument("--fetchcontent-prebuild-receipt", type=Path, required=True)
        if name in ("run-series", "run-series-step"):
            p.add_argument("--arm", choices=ARMS, required=True)
            p.add_argument("--series", type=int, required=True)
            if name == "run-series-step":
                p.add_argument("--step", required=True)
            p.add_argument("--knowledge-manifest", type=Path)
            p.add_argument("--knowledge-classification")
            p.add_argument("--knowledge-de-novo-claim", choices=("true", "false"))
    p = sub.add_parser("weights-material")
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("expected-inputs")
    p.add_argument("--ledger-root", type=Path, required=True)
    p.add_argument("--next-evaluation", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "weights-material":
        _publish(args.out, weights_material())
        return 0
    if args.command == "expected-inputs":
        _publish(args.out, expected_inputs(args.ledger_root, args.next_evaluation))
        return 0
    options = dict(purpose=args.purpose, ledger_root=args.ledger_root.resolve(),
                   prebuild_receipt=args.fetchcontent_prebuild_receipt.resolve(),
                   repo_root=Path(__file__).resolve().parents[2])
    if args.command in ("run-series", "run-series-step"):
        supplied = any(getattr(args, key) is not None for key in
                       ("knowledge_manifest", "knowledge_classification", "knowledge_de_novo_claim"))
        if ((args.arm == "llm" and not all(getattr(args, key) for key in
                    ("knowledge_manifest", "knowledge_classification", "knowledge_de_novo_claim")))
                or (args.arm != "llm" and supplied)):
            parser.error("K2 arguments required only for llm")
        k2 = K2Args(args.knowledge_manifest.resolve(), args.knowledge_classification,
                    args.knowledge_de_novo_claim) if args.arm == "llm" else None
        try:
            _validate_run(args.arm, args.workload, args.series, args.block, k2)
        except ValueError as exc:
            parser.error(str(exc))
        if args.command == "run-series-step":
            if args.purpose != "registered-v2":
                parser.error("run-series-step requires registered-v2")
            result = run_series_step(args.arm, args.workload, args.series, args.block,
                                     step=args.step, k2=k2, **{k: v for k, v in options.items()
                                                                 if k != "purpose"})
        else:
            if args.purpose == "registered-v2":
                parser.error("registered-v2 requires run-series-step")
            result = run_series(args.arm, args.workload, args.series, args.block, k2=k2, **options)
    else:
        try:
            _validate_run("stock", args.workload, args.block, args.block, None)
        except ValueError as exc:
            parser.error(str(exc))
        result = run_block_stock(args.workload, args.block, **options)
    end = result["events"][-1]
    if args.command == "run-series-step" and end["kind"] != "series-end":
        return 0
    return 0 if end["reason"] in {"b-complete", "a-exhausted", "grid-exhausted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
