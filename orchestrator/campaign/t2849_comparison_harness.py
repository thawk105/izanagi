"""S1 R0 comparison harness. Fresh sessions, immutable events, derived reports.

B-5's physical-attempt classification is reproduced for exact reference genomes
without candidate Tier0; candidate classification and endpoint selection call B-5.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

from . import b5_generator_contrast as B
from . import t2849_generators as G
from .b5_generator_contrast import (
    EVENT_FIELDS, EVENT_KINDS, END_REASONS, MAX_MACHINE_RETRIES,
    LLM_WAIT_S, LLM_POLL_S, MACHINE_FAILURE_ABORT_REASONS,
    _publish, _read_json, _utc, _positive, _allocation_available,
    classify_session, wal_timing, default_runner, loop_driver,
    CampaignLayout, Genome, source_digest, variant_id, wal,
    assert_closed_proposal_schema, assert_no_ability_probe_material,
    validate_backoff_value,
)

LEDGER_SCHEMA = "t2849-harness-ledger/v1"
INITIAL_VALUES = (5, 10)
SESSION_REPS = 5
ARMS = ("random", "sweep", "bo", "evolution", "llm")
UNRESOLVED = {"duplicate-skip", "unclassified-missing", "submitted-unresolved",
              "pre-start-failure", "machine-failure"}


def _genome(value, protocol="silo"):
    return loop_driver.backoff_genome(protocol, value)


def _stock_established(observation, protocol="silo"):
    return (observation["outcome"] == "certified" and observation["quality"] == "normal"
            and observation["src_token"] == source_digest.STOCK
            and observation["variant"] == variant_id(_genome(-1, protocol))
            and _positive(observation["fitness_tps"]))


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
        root.mkdir(parents=True, exist_ok=False)
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
        # Freeze nested payloads before callers add timing to later events.
        event = json.loads(json.dumps(event))
        _publish(self.root / "events" / f"{event['event_seq']:06d}-{kind}.json", event)
        self.events.append(event)
        _publish(self.root / "series.json", self.view(), replace=True)
        return event

    def view(self):
        return {"schema": LEDGER_SCHEMA, "header": self.header, "events": self.events}




def classify_reference_slot(sidecar_dir, campaign_root, expected_reps, expected_genome):
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
        if (not attempt or src != source_digest.STOCK
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




def _execute_slot(ledger, *, kind, n, a, b, value, proposal_path, provenance,
                  prebuild_receipt, repo_root, runner, proposal_origin="machine", reference_path=None):
    h = ledger.header
    logical_slot = f"{kind}-{n}"
    submitted_once = False
    for attempt in range(MAX_MACHINE_RETRIES + 1):
        if not _allocation_available():
            if submitted_once:
                return {**fields, "outcome": "allocation-exhausted", "submitted": True}, b
            return {"outcome": "allocation-exhausted", "submitted": submitted_once,
                    "slot_kind": kind, "n": n, "a": a, "b": b, "value": value,
                    "quality": None, "fitness_tps": None, "provenance": provenance}, b
        arm = "reference" if kind == "block-reference" else h["arm"]
        key = slot_key(h["cohort"], arm, h["workload"], h["series"], kind, n, attempt)
        sidecar = ledger.root / "slots" / f"{logical_slot}-attempt-{attempt}"
        sidecar.mkdir(parents=True)
        argv = slot_argv(arm=arm, workload=h["workload"], key=key,
                         sidecar_dir=sidecar, prebuild_receipt=prebuild_receipt,
                         proposal_path=proposal_path, proposal_origin=proposal_origin,
                         reference_path=reference_path, protocol=h.get("protocol", "silo"))
        ledger.append("slot-attempt-start", a=a, b=b, n=n, slot_kind=kind,
                      logical_slot=logical_slot, attempt=attempt, slot_key=key,
                      sidecar_dir=str(sidecar.relative_to(ledger.root)))
        started_utc = _utc()
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
        genome = reference_genome(h["workload"]) if reference_path else _genome(value, h.get("protocol", "silo"))
        classifier = classify_reference_slot if reference_path else B.classify_slot
        observation = classifier(sidecar, None, SESSION_REPS, genome)
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
        observation["timing"].update(subprocess_wall_s=wall, started_utc=started_utc,
                                     ended_utc=_utc(), available_utc=_utc())
        # A single logical B even when an earlier attempt was submitted.
        if observation["submitted"] and not submitted_once:
            submitted_once = True
            if kind == "search":
                b += 1
        fields = {**observation, "a": a, "b": b, "logical_slot": logical_slot,
                  "attempt": attempt, "slot_key": key, "value": value,
                  "proposal_path": str(proposal_path) if proposal_path else None,
                  "proposal_sha256": hashlib.sha256(Path(proposal_path).read_bytes()).hexdigest() if proposal_path else None,
                  "provenance": provenance, "returncode": rc, "argv": argv,
                  "slot_kind": kind, "n": n, "proposal_origin": proposal_origin,
                  "genome": genome.canonical(),
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


def _handshake(ledger, a, b):
    directory = ledger.root / "handshake"
    directory.mkdir(exist_ok=True)
    expected = expected_inputs(ledger, b + 1)
    wait_started = time.monotonic()
    deadline = wait_started + LLM_WAIT_S
    request = {"a": a, **expected, "deadline_utc": _utc(time.time() + LLM_WAIT_S)}
    if ledger.header.get("protocol") == "mocc":
        request["protocol"] = "mocc"
    _publish(directory / f"request-{a}.json", request)
    proposal = directory / f"proposal-{a}.json"
    inputs = directory / f"inputs-{a}.json"
    rejected = directory / f"proposal-{a}.rejected.json"
    def finish(status, path=None, provenance=None):
        cost_path = directory / f"role-costs-{a}.json"
        costs = _read_json(cost_path) if cost_path.exists() else {}
        return status, path, {**(provenance or {}),
                              "role_calls": costs.get("role_calls"),
                              "human_interventions": costs.get("human_interventions"),
                              "handshake_status": status,
                              "proposal_wait_wall_s": time.monotonic() - wait_started}

    while True:
        if rejected.exists():
            if proposal.exists():
                return finish("inheritance-mismatch")
            return finish("proposal-rejected", provenance=_read_json(rejected))
        if proposal.exists() and inputs.exists():
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


def slot_key(cohort, arm, workload, series, kind, n, attempt):
    G.coordinates(workload, series, n)
    if (not cohort or not cohort.isascii() or any(c.isspace() or c in "|/\\" for c in cohort)
            or type(attempt) is not int or not 0 <= attempt <= MAX_MACHINE_RETRIES):
        raise ValueError("invalid slot coordinates")
    if (kind not in {"stock-start", "initial", "search", "score", "block-stock", "block-reference"}
            or arm not in (*ARMS, "stock", "reference")
            or (arm == "stock") != (kind == "block-stock")
            or (arm == "reference") != (kind == "block-reference")):
        raise ValueError("invalid slot arm/kind")
    return f"{G.NAMESPACE}|{cohort}|{arm}|{workload}|{series}|{kind}|{n}|attempt-{attempt}"


def slot_argv(*, arm, workload, key, sidecar_dir, prebuild_receipt,
              proposal_path=None, proposal_origin=None, reference_path=None, protocol="silo"):
    if arm not in (*ARMS, "stock", "reference") or workload not in B.WORKLOADS:
        raise ValueError("unknown arm/workload")
    if reference_path is not None and (arm != "reference" or proposal_path is not None):
        raise ValueError("reference must be stock-only")
    argv = [sys.executable, "-B", "-m", "orchestrator.campaign.p3_s4_loop"]
    argv += ["--stock-control"] if proposal_path is None else ["--run-iteration", str(proposal_path)]
    argv += ["--isolate-worktree", "--fetchcontent-prebuild-receipt", str(prebuild_receipt),
             "--calibrated-perf", "--perf-workload", workload, "--verify-performance",
             "--b5-slot", key, "--b5-sidecar-dir", str(sidecar_dir)]
    if workload == "write-heavy":
        argv.append("--verify-performance-concurrent")
    if protocol == "mocc":
        argv += ["--protocol", "mocc"]
    if reference_path is not None:
        argv += ["--reference-genome", str(reference_path)]
    if proposal_path is not None:
        origin = proposal_origin or ("llm" if arm == "llm" else "machine")
        argv += ["--allow-coder-derived-build" if origin == "llm" else "--machine-generated-proposal"]
    return argv


def reference_genome(workload):
    if workload not in B.WORKLOADS:
        raise ValueError("unknown workload")
    read = workload == "read-heavy"
    return Genome("silo", {"BACK_OFF": 0, "NO_WAIT_LOCKING_IN_VALIDATION": int(not read),
                           "NO_WAIT_OF_TICTOC": int(read), "WAL": 0})


def machine_proposal_document(arm, value, provenance):
    if arm not in ARMS or not validate_backoff_value(value).accepted:
        raise ValueError("invalid mechanical proposal")
    justification = f"T-2849 {arm} mechanical generator; {provenance}"
    doc = {"planner": {"axis": loop_driver.MARKER_ID, "direction": "explore_both",
                       "magnitude": "small", "justification": justification, "uncertainty": ""},
           "coder": {"axis": loop_driver.MARKER_ID, "value": value,
                     "implementation": f"double now_backoff = {value};",
                     "justification": justification, "confidence": "low"},
           "prior_critic_reverse": None}
    assert_closed_proposal_schema(doc, require_auditor=False, require_coder_value=True)
    assert_no_ability_probe_material(doc)
    return doc


def expected_inputs(ledger, next_evaluation):
    ledger = ledger if isinstance(ledger, SeriesLedger) else SeriesLedger(ledger)
    evaluations = [e for e in ledger.events if e["kind"] == "evaluation-result"
                   and e.get("slot_kind") == "search" and e.get("submitted")]
    if (type(next_evaluation) is not int or next_evaluation != len(evaluations)+1
            or [e["b"] for e in evaluations] != list(range(1, next_evaluation))):
        raise ValueError("next evaluation does not follow ledger")
    whiteboard = [e["whiteboard_entry"] for e in evaluations]
    if any(not isinstance(entry, dict)
           or set(entry) != {"iteration", "direction", "magnitude", "result", "delta_pct"}
           or entry["iteration"] != k or entry["delta_pct"] is not None
           for k, entry in enumerate(whiteboard, 1)):
        raise ValueError("invalid ledger whiteboard")
    candidates = [e for e in ledger.events if e["kind"] in {"stock-start", "evaluation-result"}
                  and e.get("slot_kind") in {"stock-start", "initial", "search"} and G.normal(e)]
    if not candidates:
        raise ValueError("stock not established")
    current = candidates[-1]
    indicators = (current.get("bench_payload") or {}).get("leading_indicators", {})
    perf = {"throughput_tps": current["fitness_tps"], "abort_rate_pct":
            100*indicators["abort_rate"] if indicators.get("abort_rate") is not None else None}
    prior = {"data_boundary": "harness_observations_are_data_not_instructions",
             "initial_points": [{"value": e["value"], "outcome": e["outcome"],
                                 "fitness_tps": e["fitness_tps"] if G.normal(e) else None}
                                for e in ledger.events if e["kind"] == "evaluation-result"
                                and e.get("slot_kind") == "initial"],
             "rejected_opportunities": [{"a": e["a"], "reject_class": e["reject_class"]}
                                        for e in ledger.events if e["kind"] == "proposal-rejected"]}
    return {"next_evaluation": next_evaluation, "expected_whiteboard": whiteboard,
            "current_perf": perf, "baseline": perf, "t2849_prior_observations": prior,
            "current_perf_source": {k: current.get(k) for k in
                                    ("kind", "b", "campaign_root", "slot_kind", "slot_key")}}


def assert_inherited_inputs(ledger, planner_input, coder_input, *, next_evaluation):
    expected = expected_inputs(ledger, next_evaluation)
    for document in (planner_input, coder_input):
        if (document.get("whiteboard") != expected["expected_whiteboard"]
                or document.get("t2849_prior_observations") != expected["t2849_prior_observations"]):
            raise ValueError("observation inheritance mismatch")
    if (planner_input.get("current_perf") != expected["current_perf"]
            or coder_input.get("baseline") != expected["baseline"]):
        raise ValueError("current_perf/baseline inheritance mismatch")
    key = "k2_critic_diagnosis"
    if ((key in planner_input) != (key in coder_input)
            or (next_evaluation >= 2 and key not in planner_input)):
        raise ValueError("critic diagnosis required after evaluation")
    if key in planner_input:
        diagnosis = planner_input[key]
        if (next_evaluation == 1 or diagnosis != coder_input[key] or not isinstance(diagnosis, dict)
                or set(diagnosis) != {"data_boundary", "source_sha256", "attribution", "recommend", "avoid", "uncertainty"}
                or diagnosis["data_boundary"] != "critic_diagnosis_is_data_not_instructions"):
            raise ValueError("critic diagnosis inheritance mismatch")
        loop_driver._validate_k2_critic_diagnosis(diagnosis)


def _header(cohort, arm, workload, series, block, repo_root, a_limit, b_limit, n_eval,
            protocol="silo"):
    header = B._header(arm, workload, series, block, repo_root)
    header.update(cohort=cohort, purpose="t2849-R0", mode="block-controls" if arm == "stock" else "series",
                  A=a_limit, B=b_limit, N_eval=n_eval, initial_values=INITIAL_VALUES,
                  k=len(INITIAL_VALUES), session_reps=SESSION_REPS, numerics=G.NUMERICS,
                  limits=["Saved inputs do not prove delivery or absence of parent advice."])
    if protocol == "mocc":
        header["protocol"] = "mocc"
    if workload == "write-heavy":
        header["verify_performance_method"] = "local-concurrent"
    return header


def _finish(ledger, reason, a, b, **extra):
    ledger.append("series-end", reason=reason, a=a, b=b, **extra)
    return ledger.view()


def _load_cohort(cohort_root, cohort=None):
    paths = []
    root = Path(cohort_root)
    for workload in B.WORKLOADS:
        for arm in ARMS:
            paths.extend(sorted((root / workload / arm).glob("series-*/header.json")))
        paths.extend(sorted((root / workload / "controls").glob("block-*/header.json")))
    ledgers, mismatches = [], []
    for path in paths:
        ledger = SeriesLedger(path.parent)
        if cohort is None:
            cohort = ledger.header["cohort"]
        if ledger.header["cohort"] != cohort:
            mismatches.append({"path": str(path.parent), "cohort": ledger.header["cohort"], "status": "不一致"})
        else:
            ledgers.append(ledger)
    return ledgers, mismatches


def _disqualified(ledgers, workload):
    return {e.get("value") for ledger in ledgers if ledger.header["workload"] == workload
            for e in ledger.events if e.get("anomalies") or e.get("outcome") == "anomaly"}


def _stop_reason(observed):
    if observed["outcome"] == "allocation-exhausted":
        return "allocation-exhausted"
    if observed["outcome"] in UNRESOLVED:
        return "unclassified-missing"
    return None


def run_series(arm, workload, series, block, *, cohort, cohort_root, a_limit, b_limit, n_eval,
               prebuild_receipt, repo_root, runner=default_runner, protocol="silo"):
    slot_key(cohort, arm, workload, series, "stock-start", 1, 0)
    if any(type(v) is not int or v < 1 for v in (block, a_limit, b_limit, n_eval)):
        raise ValueError("positive budgets and block required")
    root = Path(cohort_root) / workload / arm / f"series-{series}"
    ledger = SeriesLedger.create(root, _header(cohort, arm, workload, series, block, repo_root,
                                              a_limit, b_limit, n_eval, protocol))
    ledger.append("series-start", a=0, b=0)
    common = dict(prebuild_receipt=prebuild_receipt, repo_root=repo_root, runner=runner)
    stock, _ = _execute_slot(ledger, kind="stock-start", n=1, a=0, b=0, value=-1,
                            proposal_path=None, provenance={}, **common)
    ledger.append("stock-start", **stock)
    if stock["outcome"] == "allocation-exhausted":
        return _finish(ledger, "allocation-exhausted", 0, 0, score=None)
    if not _stock_established(stock, protocol):
        return _finish(ledger, "stock-unestablished", 0, 0, score=None)
    proposals = root / "proposals"
    proposals.mkdir()
    generator = (G.BOGenerator(workload, series) if arm == "bo" else
                 G.EvolutionGenerator(workload, series) if arm == "evolution" else None)
    evaluations = []
    for n, value in enumerate(INITIAL_VALUES, 1):
        proposal = proposals / f"initial-{n}.json"
        _publish(proposal, machine_proposal_document(arm, value, {"initial": n}))
        observed, _ = _execute_slot(ledger, kind="initial", n=n, a=0, b=0, value=value,
                                    proposal_path=proposal, provenance={"initial": n}, **common)
        event = ledger.append("evaluation-result", **observed)
        evaluations.append(event)
        if generator:
            generator.tell(event)
        if _stop_reason(observed):
            return _finish(ledger, _stop_reason(observed), 0, 0, score=None)
    grid = None
    a = b = 0
    reason = "b-complete"
    while a < a_limit and b < b_limit:
        if not _allocation_available():
            return _finish(ledger, "allocation-exhausted", a, b, score=None)
        if grid is not None and a == len(grid):
            reason = "grid-exhausted"
            break
        a += 1
        ledger.append("proposal-opportunity", a=a, b=b, logical_slot=f"search-{a}")
        timing = {}
        if arm == "llm":
            status, proposal, provenance = _handshake(ledger, a, b)
            timing["proposal_wait_wall_s"] = provenance["proposal_wait_wall_s"]
            if status == "proposal-rejected":
                ledger.append("proposal-rejected", a=a, b=b, reject_class="role-output",
                              provenance=provenance, timing=timing)
                continue
            if status != "proposal":
                return _finish(ledger, status, a, b, provenance=provenance, timing=timing, score=None)
        else:
            started = time.monotonic()
            if arm == "random":
                value, counter = G.random_value(workload, series, a)
                provenance = {"preimage": f"{G.NAMESPACE}|random|{workload}|{series}|{a}|{counter}"}
            elif arm == "sweep":
                if grid is None:
                    grid = G.sweep_order(workload, series)
                value = grid[a-1]
                provenance = {"preimage": f"{G.NAMESPACE}|sweep|{workload}|{series}|{value}"}
            else:
                value = generator.ask(a)
                provenance = {"arm": arm, "a": a, "namespace": G.NAMESPACE}
            timing["generator_wall_s"] = time.monotonic()-started
            proposal = proposals / f"proposal-{a}.json"
            _publish(proposal, machine_proposal_document(arm, value, provenance))
        reject_class = "schema"
        try:
            raw = Path(proposal).read_bytes()
            document = json.loads(raw)
            assert_closed_proposal_schema(document, require_auditor=False, require_coder_value=True)
            assert_no_ability_probe_material(document)
            value = document["coder"]["value"]
            reject_class = "grammar"
            if not validate_backoff_value(value).accepted:
                raise ValueError("value outside grammar")
            planner, _, _ = loop_driver.load_proposal_file(str(proposal))
        except (ValueError, KeyError, TypeError) as exc:
            ledger.append("proposal-rejected", a=a, b=b, reject_class=reject_class, note=str(exc),
                          provenance=provenance, timing=timing, proposal_path=str(proposal))
            continue
        frozen = proposals / f"accepted-{a}.json"
        with frozen.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        origin = "llm" if arm == "llm" else "machine"
        observed, b = _execute_slot(ledger, kind="search", n=a, a=a, b=b, value=value,
                                    proposal_path=frozen, provenance=provenance,
                                    proposal_origin=origin, **common)
        observed.setdefault("timing", {}).update(timing)
        observed["duplicate_of"] = next((e["slot_key"] for e in evaluations if e.get("value") == value), None)
        if observed["submitted"]:
            observed["whiteboard_entry"] = {"iteration": b, "direction": planner.direction,
                                           "magnitude": planner.magnitude, "delta_pct": None,
                                           "result": "success" if observed["outcome"] == "certified" else "fail"}
            event = ledger.append("evaluation-result", **observed)
            evaluations.append(event)
            handshake = root / "handshake"
            handshake.mkdir(exist_ok=True)
            _publish(handshake / f"slot-{b}.json", {**event, "digest_path":
                     str(Path(observed["campaign_root"]) / "s4_loop_digest.txt") if observed.get("campaign_root") else None})
        else:
            observed["reject_class"] = "tier0" if observed["outcome"] == "rejected-tier0" else "preprocess"
            ledger.append("proposal-rejected", **observed)
        if generator:
            generator.tell(observed)
        if _stop_reason(observed):
            return _finish(ledger, _stop_reason(observed), a, b, score=None)
    if a == a_limit and b < b_limit:
        reason = "a-exhausted"
    ledgers, _ = _load_cohort(cohort_root, cohort)
    endpoint = B.select_endpoint(evaluations, _disqualified(ledgers, workload))
    ledger.append("endpoint-fixed", a=a, b=b, endpoint=endpoint)
    if endpoint is None:
        quality_missing = any(e.get("quality") == "quality-missing" for e in evaluations)
        return _finish(ledger, "unclassified-missing" if quality_missing else reason, a, b,
                       score=None, fallback=None if quality_missing else "pending-block-stock")
    scores = []
    for n in range(1, n_eval+1):
        observed, _ = _execute_slot(ledger, kind="score", n=n, a=a, b=b,
                                    value=endpoint["value"], proposal_path=endpoint["proposal_path"],
                                    provenance=endpoint["provenance"],
                                    proposal_origin=endpoint["proposal_origin"], **common)
        ledger.append("score-session", **observed)
        if observed["outcome"] == "anomaly":
            return _finish(ledger, reason, a, b, score=None, fallback="pending-block-stock")
        if not G.normal(observed):
            return _finish(ledger, _stop_reason(observed) or "unclassified-missing", a, b, score=None)
        scores.append(observed["fitness_tps"])
    return _finish(ledger, reason, a, b, score=statistics.median(scores), score_sessions=scores)


def run_block_controls(workload, block, *, cohort, cohort_root, n_eval, block_stock_sessions,
                       prebuild_receipt, repo_root, runner=default_runner, protocol="silo"):
    slot_key(cohort, "stock", workload, block, "block-stock", 1, 0)
    if any(type(v) is not int or v < 1 for v in (n_eval, block_stock_sessions)):
        raise ValueError("positive session counts required")
    root = Path(cohort_root) / workload / "controls" / f"block-{block}"
    header = _header(cohort, "stock", workload, block, block, repo_root, 0, 0, n_eval, protocol)
    header["block_stock_sessions"] = block_stock_sessions
    ledger = SeriesLedger.create(root, header)
    ledger.append("series-start", a=0, b=0)
    reference_path = None
    if protocol == "silo":
        reference = reference_genome(workload)
        reference_path = root / "reference-genome.json"
        _publish(reference_path, {"protocol": reference.protocol, "flags": reference.flags})
    controls = (("block-stock", block_stock_sessions),) if protocol == "mocc" else (
        ("block-stock", block_stock_sessions), ("block-reference", n_eval))
    for kind, count in controls:
        for n in range(1, count+1):
            observed, _ = _execute_slot(ledger, kind=kind, n=n, a=0, b=0,
                                        value=-1 if kind == "block-stock" else None,
                                        proposal_path=None, provenance={}, prebuild_receipt=prebuild_receipt,
                                        repo_root=repo_root, runner=runner,
                                        reference_path=reference_path if kind == "block-reference" else None)
            ledger.append("stock-start" if kind == "block-stock" else "score-session", **observed)
            if _stop_reason(observed):
                return _finish(ledger, _stop_reason(observed), 0, 0)
    return _finish(ledger, "b-complete", 0, 0)


def _control_median(ledger, kind, count):
    events = [e for e in ledger.events if e.get("slot_kind") == kind
              and e["kind"] in {"stock-start", "score-session"}]
    if len(events) != count or not all(G.normal(e) for e in events):
        return None
    if kind == "block-stock" and not all(_stock_established(e, ledger.header.get("protocol", "silo")) for e in events):
        return None
    return statistics.median(e["fitness_tps"] for e in events)


def _costs(ledger):
    # Physical attempt records occur in submission/retry/result; count each once.
    slots, opportunities = {}, {}
    for event in ledger.events:
        if event.get("slot_key") and (event.get("timing") or {}).get("subprocess_wall_s") is not None:
            slots[event["slot_key"]] = event
        if event.get("a") and (event["kind"] in {"evaluation-result", "proposal-rejected"}
                               or event["kind"] == "series-end" and event.get("provenance")):
            opportunities[event["a"]] = event
    roles, interventions = [], []
    for event in opportunities.values():
        provenance = event.get("provenance") or {}
        if ledger.header["arm"] == "llm":
            roles.append(provenance.get("role_calls"))
            interventions.append(provenance.get("human_interventions"))
    critic_paths = set((ledger.root / "handshake").glob("critic-costs-*.json"))
    if ledger.header["arm"] == "llm":
        critic_paths.update(ledger.root / "handshake" / f"critic-costs-{e['b']}.json"
                            for e in ledger.events if e["kind"] == "evaluation-result"
                            and e.get("slot_kind") == "search" and e.get("submitted"))
    critics = [_read_json(p) if p.exists() else {} for p in sorted(critic_paths)]
    roles.extend(c.get("role_calls") for c in critics)
    interventions.extend(c.get("human_interventions") for c in critics)
    return {"subprocess_wall_s": sum(e["timing"]["subprocess_wall_s"] for e in slots.values()),
            "physical_attempts": len(slots),
            "generator_wall_s": sum((e.get("timing") or {}).get("generator_wall_s", 0) for e in opportunities.values()),
            "proposal_wait_wall_s": sum((e.get("timing") or {}).get("proposal_wait_wall_s", 0) for e in opportunities.values()),
            "role_calls": roles, "human_interventions": interventions}


def aggregate(cohort_root, job_costs):
    ledgers, mismatches = _load_cohort(cohort_root)
    job_costs = _read_json(job_costs) if isinstance(job_costs, (str, Path)) else job_costs
    controls = {(l.header["workload"], l.header["block"]): l for l in ledgers
                if l.header["mode"] == "block-controls"}
    rows = []
    at = _utc()
    for ledger in ledgers:
        h, events = ledger.header, ledger.events
        if h["mode"] != "series":
            continue
        control = controls.get((h["workload"], h["block"]))
        stock = _control_median(control, "block-stock", control.header["block_stock_sessions"]) if control else None
        reference = (_control_median(control, "block-reference", control.header["N_eval"])
                     if control and h.get("protocol", "silo") == "silo" else None)
        starts = [e for e in events if e["kind"] == "stock-start"]
        evaluations = [e for e in events if e["kind"] == "evaluation-result"]
        scores = [e for e in events if e["kind"] == "score-session"]
        fixed = next((e for e in events if e["kind"] == "endpoint-fixed"), None)
        endpoint = fixed.get("endpoint") if fixed else None
        end = events[-1] if events and events[-1]["kind"] == "series-end" else {}
        disqualified = _disqualified(ledgers, h["workload"])
        # Re-evaluate eligibility, never replace a previously fixed endpoint.
        final_eligible = B.select_endpoint(evaluations, disqualified)
        corrected = endpoint is not None and endpoint["value"] in disqualified
        score, status = None, "score-missing"
        search_missing = any(_stop_reason(e) for e in events
                             if e["kind"] in {"evaluation-result", "proposal-rejected"}
                             and e.get("slot_kind") in {"initial", "search"})
        if stock is None or len(starts) != 1 or not _stock_established(starts[0], h.get("protocol", "silo")):
            status = "stock-unestablished"
        elif search_missing or not end or not fixed:
            status = "machine-missing"
        elif endpoint is None:
            if any(e.get("quality") == "quality-missing" for e in evaluations):
                status = "quality-missing"
            else:
                score, status = stock, "fallback-candidate-rejected"
        elif any(e.get("outcome") == "anomaly" or e.get("anomalies") for e in scores):
            score, status = stock, "fallback-score-anomaly"
        elif len(scores) != h["N_eval"] or not all(G.normal(e) for e in scores):
            status = "score-missing"
        elif corrected:
            score, status = stock, "fallback-disqualified"
        else:
            score, status = statistics.median(e["fitness_tps"] for e in scores), "scored"
        initial = [e["fitness_tps"] for e in evaluations if e.get("slot_kind") == "initial" and G.normal(e)]
        search = [e for e in evaluations if e.get("slot_kind") == "search"]
        search_fitness = [e["fitness_tps"] for e in search if G.normal(e)]
        values = [e["value"] for e in evaluations]
        rows.append({"path": str(ledger.root), "arm": h["arm"], "workload": h["workload"],
                     "series": h["series"], "block": h["block"], "status": status, "score": score,
                     "stock": stock, "reference": reference,
                     "stock_ratio": score/stock if score is not None and stock is not None else None,
                     "reference_ratio": score/reference if score is not None and reference is not None else None,
                     "endpoint": endpoint, "final_eligible_slot": final_eligible.get("slot_key") if final_eligible else None,
                     "correction": {"at_utc": at, "reason": "cross-series-anomaly", "value": endpoint["value"]} if corrected else None,
                     "endpoint_is_initial": endpoint.get("slot_kind") == "initial" if endpoint else None,
                     "search_exceeded_initial": max(search_fitness) > max(initial) if initial and search_fitness else None,
                     "unique_candidates": len(set(values)),
                     "duplicate_rate": 1-len(set(values))/len(values) if values else None,
                     "a": end.get("a"), "b": end.get("b"), "costs": _costs(ledger)})
    jobs = {l.header["job"]["PBS_JOBID"] for l in ledgers}
    known_jobs = {job: job_costs.get(job) for job in sorted(j for j in jobs if j is not None)}
    complete = None not in jobs and all(v is not None and v.get("elapse_s") is not None for v in known_jobs.values())
    return {"at_utc": at, "cohort": ledgers[0].header["cohort"] if ledgers else None,
            "mismatches": mismatches, "series": rows, "jobs": known_jobs,
            "job_elapse_s": sum(v["elapse_s"] for v in known_jobs.values()) if complete else None,
            "shared_controls": [{"path": str(l.root), "costs": _costs(l)} for l in controls.values()]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("run-series", "run-block-controls"):
        p = sub.add_parser(command)
        p.add_argument("--cohort", required=True)
        p.add_argument("--cohort-root", type=Path, required=True)
        p.add_argument("--workload", choices=B.WORKLOADS, required=True)
        p.add_argument("--protocol", choices=("silo", "mocc"), default="silo")
        p.add_argument("--block", type=int, required=True)
        p.add_argument("--n-eval", type=int, required=True)
        p.add_argument("--fetchcontent-prebuild-receipt", type=Path, required=True)
        if command == "run-series":
            p.add_argument("--arm", choices=ARMS, required=True)
            p.add_argument("--series", type=int, required=True)
            p.add_argument("--a-limit", type=int, required=True)
            p.add_argument("--b-limit", type=int, required=True)
        else:
            p.add_argument("--block-stock-sessions", type=int, required=True)
    p = sub.add_parser("aggregate")
    p.add_argument("--cohort-root", type=Path, required=True)
    p.add_argument("--job-costs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "aggregate":
        _publish(args.out, aggregate(args.cohort_root, args.job_costs), replace=True)
        return 0
    options = vars(args).copy()
    command = options.pop("command")
    options["cohort_root"] = options["cohort_root"].resolve()
    options["prebuild_receipt"] = options.pop("fetchcontent_prebuild_receipt").resolve()
    options["repo_root"] = Path(__file__).resolve().parents[2]
    result = run_series(**options) if command == "run-series" else run_block_controls(**options)
    return 0 if result["events"][-1]["reason"] in {"b-complete", "a-exhausted", "grid-exhausted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
