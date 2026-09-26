"""B-5 producer contracts, with physical sidecar/WAL fixtures at the runner seam."""
from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import b5_generator_contrast as B
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign.model import Genome, WalRecord
from orchestrator.campaign.pipeline import variant_id
from orchestrator.campaign.projection_guard import assert_closed_proposal_schema, assert_no_ability_probe_material

ROOT = Path(__file__).resolve().parents[2]


def test_integer_log_weights_independent_floor_and_table_hash():
    # Independent atanh series: ln((v+1)/v)=2*sum((1/(2v+1))**(2n+1)/(2n+1)).
    # 400 terms, Decimal precision 155, gave the following SHA; no implementation
    # function or ln() participated in deriving this constant.
    expected_sha = "876b1b4798fbf79dfefaffd9ccefceaf0beb16cb8561cc5ea4e28745bbd20bdd"
    expected_first = 235865763225513294137944142764154484399
    with localcontext() as ctx:
        ctx.prec = 100
        assert int(Decimal("0.6931471805599453094172321214581765680755") * Decimal(2**128)) == expected_first
    weights = B.weights_table()
    assert len(weights) == 1000 and weights[0] == expected_first
    assert hashlib.sha256(json.dumps(weights, separators=(",", ":")).encode("ascii")).hexdigest() == expected_sha
    material = B.weights_material()
    assert material["weights"] == list(weights)
    assert material["weights_sha256"] == expected_sha
    assert material["precisions"] == [100, 130]
    assert material["M"] == sum(weights)
    assert material["decimal"] == "decimal"


def test_random_value_independent_known_vector():
    # [2,3,5] partitions residues as [0,2), [2,5), [5,10).
    U = int.from_bytes(hashlib.sha256(b"b5-generator-contrast-v1|random|write-heavy|1|1|0").digest(), "big")
    assert U % 10 == 6  # independently pinned residue -> value 3
    assert B.random_value("write-heavy", 1, 1, (2, 3, 5)) == (3, 0)
    U2 = int.from_bytes(hashlib.sha256(b"b5-generator-contrast-v1|random|write-heavy|1|2|0").digest(), "big")
    assert U2 % 10 == 1
    assert B.random_value("write-heavy", 1, 2, (2, 3, 5)) == (1, 0)


def test_random_value_rejects_exact_L_without_hash_stub():
    # Choose M=U0>2**255, hence floor(2**256/M)=1 and L=U0 exactly.
    # This exercises equality with the actual hash, not a replacement RNG.
    U0 = int.from_bytes(hashlib.sha256(b"b5-generator-contrast-v1|random|write-heavy|1|3|0").digest(), "big")
    U1 = int.from_bytes(hashlib.sha256(b"b5-generator-contrast-v1|random|write-heavy|1|3|1").digest(), "big")
    assert U0 == 105733628255731662194573769123048327502436925210351633031407637047021002757997
    assert 2**255 < U0 < 2**256 and 0 < U1 < U0
    assert B.random_value("write-heavy", 1, 3, (U0,)) == (1, 1)


def test_sweep_order_independent_hashes():
    grid = (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50,
            75, 100, 150, 200, 250, 300, 400, 500, 560, 600, 700, 800, 900, 1000)
    expected = tuple(sorted(grid, key=lambda v: (
        hashlib.sha256(("b5-generator-contrast-v1|sweep|balanced|7|" + str(v)).encode("ascii")).digest(), v)))
    assert expected != grid
    assert B.sweep_order("balanced", 7) == expected


@pytest.mark.parametrize("arm", ["random", "sweep-matched"])
@pytest.mark.parametrize("value", [1, 20, 1000])
def test_machine_proposal_real_schema_and_loader(tmp_path, arm, value):
    doc = B.machine_proposal_document(arm, value, {"preimage": "fixed-generator-input"})
    assert_closed_proposal_schema(doc, require_auditor=False, require_coder_value=True)
    assert_no_ability_probe_material(doc)
    path = tmp_path / "proposal.json"
    path.write_text(json.dumps(doc))
    planner, coder, prior = L.load_proposal_file(str(path))
    assert coder.value == value and coder.implementation == f"double now_backoff = {value};"
    assert planner.direction == "explore_both" and prior is None
    L.assert_value_literal_consistent(coder)


@pytest.mark.parametrize("value", [0, -1, 1001, True, 1.5, "20"])
def test_machine_proposal_rejects_outside_grammar(value):
    with pytest.raises(ValueError):
        B.machine_proposal_document("random", value, {"preimage": "x"})


def test_slot_keys_separate_physical_attempt_and_logical_kind():
    prefix = "b5-generator-contrast-v1|t2797-beta-v1|random|balanced|2|search|3|attempt-"
    assert [B.slot_key("t2797-beta-v1", "random", "balanced", 2, "search", 3, t)
            for t in range(3)] == [prefix + str(t) for t in range(3)]
    assert B.slot_key("t2797-beta-v1", "stock", "balanced", 1, "block-stock", 5, 0).endswith("|block-stock|5|attempt-0")
    with pytest.raises(ValueError):
        B.slot_key("t2797-beta-v1", "random", "balanced", 2, "score", 6, 0)


def _bench(**overrides):
    return {"tps": [100., 100., 100., 100., 100.], "median_tps": 100.,
            "unstable": False, "settled": True, "rounds": 1, "cv": 0.,
            "bench_wall_s": 15., "leading_indicators": {"abort_rate": 0.07}, **overrides}


@pytest.mark.parametrize("change", [{"tps": [100.] * 4}, {"unstable": True}, {"settled": None}])
def test_quality_each_single_condition_is_missing(change):
    assert B.classify_session(_bench(), 5) == "normal"
    assert B.classify_session(_bench(**change), 5) == "quality-missing"


@pytest.mark.parametrize("change", [{"median_tps": float("nan")}, {"tps": [0.] * 5},
                                      {"median_tps": 101.}, {"tps": None}])
def test_quality_rejects_invalid_numeric_evidence(change):
    assert B.classify_session(_bench(**change), 5) == "quality-missing"


def _genome(value):
    return Genome("silo", {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0,
                           "WAL": 0, "BACK_OFF": 1, "BACKOFF_FIXED": value})


def _write_tier0(sidecar, start, *, status="passed", reason=None):
    payload = {k: start[k] for k in ("b5_slot", "campaign_id", "genome", "ts_utc")}
    payload.update(schema="p3-s4-loop-b5-tier0/v1", contract=L.B5_TIER0_CONTRACT,
                   status=status, reason=reason, error=None,
                   build={"trace": False, "binary": "/fixture/perf", "bin_sha256": "a" * 64,
                          "cached": False},
                   smoke={"flags": [*L.B5_TIER0_CONTRACT["smoke_flags"], "--clocks_per_us=2100"],
                          "timeout_s": 32, "returncode": 0, "wall_s": 1., "commits": 987654321,
                          "aborts": 123456789, "throughput_positive": True})
    L._write_b5_sidecar(sidecar, "tier0.json", payload)


def _write_attempt(sidecar, *, key="b5-generator-contrast-v1|fixture", value=20,
                   outcome="certified", bench=None, abort_reason="build-error", src=None):
    """Synthetic producer bytes at the subprocess boundary, never a WAL reader stub."""
    sidecar = Path(sidecar)
    root = sidecar / "campaign"
    (root / "runs").mkdir(parents=True)
    genome = _genome(value)
    src = src if src is not None else "stock" if value == -1 else "d" * 64
    variant = variant_id(genome, src)
    preimage = json.dumps({"search_config": {"b5_slot": key}}, separators=(",", ":"))
    digest = hashlib.sha256(preimage.encode()).hexdigest()
    start = {"schema": "p3-s4-loop-b5-slot-start/v1", "b5_slot": key,
             "campaign_id": "test-b5-" + digest[:8], "campaign_root": str(root),
             "genome": genome.canonical(), "identity_preimage_sha256": digest, "ts_utc": "2026-01-01T00:00:00Z"}
    (sidecar / "slot-start.json").write_text(json.dumps(start))
    (root / "campaign.lock").write_text(json.dumps({"identity_preimage": preimage}))
    if outcome == "unclassified-missing":
        return root
    if value != -1 and outcome != "rejected-preprocess":
        _write_tier0(sidecar, start, status="rejected" if outcome == "rejected-tier0" else "passed",
                     reason="smoke-failed" if outcome == "rejected-tier0" else None)
    if outcome == "rejected-tier0":
        return root
    if outcome != "rejected-preprocess":
        submitted = {k: start[k] for k in ("b5_slot", "campaign_id", "genome", "ts_utc")}
        submitted["schema"] = "p3-s4-loop-b5-submission/v1"
        (sidecar / "pipeline-submitted.json").write_text(json.dumps(submitted))
    records = []

    def emit(stage, ts, **payload):
        records.append(asdict(WalRecord(variant, stage, "linux-baremetal", float(ts),
                                       {"build_attempt_id": "physical-test-attempt", **payload})))

    if outcome == "rejected-preprocess":
        emit("abort", 1, reason="diff-quarantine")
    elif outcome != "submitted-unresolved":
        emit("build_start", 1, genome=genome.canonical(), src_token=src)
        if outcome == "certified":
            emit("build_done", 3)
            emit("verify_done", 4, workload={"tag": "legacy"}, anomalies=0)
            for i in range(5):
                emit("verify_done", 6 + i * 2, workload={"tag": "performance"}, anomalies=0)
            measured = _bench() if bench is None else bench
            emit("bench_done", 30, **measured)
            emit("commit", 31, fitness_tps=measured["median_tps"])
        else:
            if outcome == "anomaly":
                emit("verify_done", 4, workload={"tag": "performance"}, anomalies=1)
            emit("abort", 5, reason=abort_reason)
    (root / "runs/wal.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    return root


@pytest.mark.parametrize("outcome,reason,expected,submitted", [
    ("certified", "", "certified", True),
    ("abort", "build-error", "build-failed", True),
    ("abort", "bench-no-throughput", "bench-aborted", True),
    ("anomaly", "verify-red", "anomaly", True),
    ("abort", "bench-probe-error", "machine-failure", True),
    ("abort", "bench-competing-tenant", "machine-failure", True),
    ("abort", "walltime", "aborted", True),
    ("submitted-unresolved", "", "submitted-unresolved", True),
    ("unclassified-missing", "", "unclassified-missing", False),
    ("rejected-preprocess", "", "rejected-preprocess", False),
])
def test_classify_slot_actual_wal_and_submission(tmp_path, outcome, reason, expected, submitted):
    root = _write_attempt(tmp_path, outcome=outcome, abort_reason=reason)
    observed = B.classify_slot(tmp_path, root, 5, _genome(20))
    assert observed["outcome"] == expected
    assert observed["submitted"] is submitted


def test_classify_pre_start_and_duplicate_are_not_success(tmp_path):
    assert B.classify_slot(tmp_path, None, 5, _genome(20))["outcome"] == "pre-start-failure"
    root = _write_attempt(tmp_path)
    (tmp_path / "stdout.txt").write_text("ran=True outcome=duplicate-skip variant=None")
    observed = B.classify_slot(tmp_path, root, 5, _genome(20))
    assert observed["outcome"] == "duplicate-skip" and observed["submitted"] is False
    assert observed["fitness_tps"] is None


@pytest.mark.parametrize("tamper", ["genome", "submission", "attempt", "variant", "preimage", "truncated"])
def test_classify_rejects_mixed_or_incomplete_evidence(tmp_path, tamper):
    root = _write_attempt(tmp_path)
    if tamper in {"genome", "submission"}:
        path = tmp_path / ("slot-start.json" if tamper == "genome" else "pipeline-submitted.json")
        d = json.loads(path.read_text()); d["genome"] = "another-genome"
        path.write_text(json.dumps(d))
    elif tamper == "preimage":
        (root / "campaign.lock").write_text(json.dumps({"identity_preimage": "{}"}))
    else:
        path = root / "runs/wal.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if tamper == "attempt":
            rows[-1]["payload"]["build_attempt_id"] = "other"
        elif tamper == "variant":
            rows[-1]["variant"] = "other"
        path.write_text("\n".join(json.dumps(r) for r in rows) + ("" if tamper == "truncated" else "\n"))
    assert B.classify_slot(tmp_path, root, 5, _genome(20))["outcome"] != "certified"


def test_timing_uses_adjacent_verify_differences(tmp_path):
    root = _write_attempt(tmp_path)
    timing = B.classify_slot(tmp_path, root, 5, _genome(20))["timing"]
    assert timing["build_wall_s"] == 2
    assert [x["wall_s"] for x in timing["verify_intervals"]] == [1, 2, 2, 2, 2, 2]
    assert [x["tag"] for x in timing["verify_intervals"]] == ["legacy"] + ["performance"] * 5
    assert timing["verify_total_wall_s"] == 11
    assert timing["bench_surrounding_wall_s"] == 16 and timing["bench_wall_s"] == 15
    assert timing["verify_interval_label"] == "trace+verifier+周辺処理 区間"
    assert timing["verify_missing_reps"] == 0


def test_endpoint_tie_is_lower_value_then_earlier_slot():
    def e(value, slot, **kw):
        return {"value": value, "b": slot, "fitness_tps": 900., "outcome": "certified", "quality": "normal", **kw}
    candidates = [e(30, 1), e(20, 3), e(20, 2), e(10, 4, quality="quality-missing"), e(1, 5, outcome="anomaly")]
    assert B.select_endpoint(candidates)["b"] == 2
    assert B.select_endpoint(candidates, {20})["value"] == 30


class FakeRunner:
    """Only external evaluation is replaced; all producer logic runs for real."""

    def __init__(self, policy=None, before=None):
        self.calls = []
        self.policy = policy or (lambda kind, n, attempt: {})
        self.before = before

    def __call__(self, argv, *, cwd):
        assert cwd == ROOT
        key = argv[argv.index("--b5-slot") + 1]
        pieces = key.split("|")
        kind, n, attempt = pieces[-3], int(pieces[-2]), int(pieces[-1].removeprefix("attempt-"))
        sidecar = Path(argv[argv.index("--b5-sidecar-dir") + 1])
        proposal = Path(argv[argv.index("--run-iteration") + 1]) if "--run-iteration" in argv else None
        value = -1
        if proposal:
            doc = json.loads(proposal.read_text())
            coder = doc["coder"]
            value = coder.get("value", coder.get("proposal", {}).get("value"))
        call = {"key": key, "kind": kind, "n": n, "attempt": attempt,
                "value": value, "proposal_bytes": proposal.read_bytes() if proposal else None, "argv": argv}
        self.calls.append(call)
        if self.before:
            self.before(call, sidecar)
        behavior = dict(self.policy(kind, n, attempt))
        outcome = behavior.pop("outcome", "certified")
        if outcome == "pre-start-failure":
            return subprocess.CompletedProcess(argv, 1, "", "not started")
        if outcome == "duplicate-skip":
            _write_attempt(sidecar, key=key, value=value)
            return subprocess.CompletedProcess(argv, 1, "outcome=duplicate-skip", "")
        _write_attempt(sidecar, key=key, value=value, outcome=outcome, **behavior)
        return subprocess.CompletedProcess(argv, 0 if outcome == "certified" else 1, "", "")


def _series(tmp_path, runner, arm="random", **kwargs):
    return B.run_series(arm, "write-heavy", 1, 1, ledger_root=tmp_path / "ledger",
                        prebuild_receipt=tmp_path / "receipt", repo_root=ROOT, runner=runner, **kwargs)


def _events(result, kind):
    return [e for e in result["events"] if e["kind"] == kind]


def _v2_step(tmp_path, runner, step, arm="random", **kwargs):
    return B.run_series_step(arm, "write-heavy", 1, 1, step=step,
                             ledger_root=tmp_path / "ledger", prebuild_receipt=tmp_path / "receipt",
                             repo_root=ROOT, runner=runner, **kwargs)


@pytest.mark.parametrize("arm", ["random", "sweep-matched"])
def test_v2_first_job_has_stock_and_one_evaluation_and_later_job_one(tmp_path, arm):
    runner = FakeRunner()
    result = _v2_step(tmp_path, runner, "stock-evaluation-1", arm)
    assert [call["kind"] for call in runner.calls] == ["stock-start", "search"]
    assert [call["n"] for call in runner.calls] == [1, 1]
    assert B.next_series_action(tmp_path / "ledger") == ("proposal", 2)
    ledger = B.SeriesLedger(tmp_path / "ledger")
    proposal, provenance = B._v2_machine_proposal(ledger, 2)
    B._v2_proposal(ledger, 2, 1, proposal, provenance)
    result = _v2_step(tmp_path, runner, "evaluation-2", arm)
    assert [call["kind"] for call in runner.calls] == ["stock-start", "search", "search"]
    assert len(_events(result, "evaluation-result")) == 2
    assert "--verify-performance-concurrent" in runner.calls[-1]["argv"]


def test_v2_step_mismatch_refuses_before_session(tmp_path):
    runner = FakeRunner()
    _v2_step(tmp_path, runner, "stock-evaluation-1")
    with pytest.raises(ValueError, match="differs"):
        _v2_step(tmp_path, runner, "score")
    assert len(runner.calls) == 2


def test_v2_unsettled_slot_attempt_stops_only_its_series(tmp_path):
    ledger = B.SeriesLedger.create(tmp_path / "ledger", {"cohort": B.COHORT_REGISTERED_V2,
                          "arm": "random", "workload": "write-heavy", "series": 1, "block": 1})
    ledger.append("series-start", a=0, b=0)
    ledger.append("slot-attempt-start", a=0, b=0, logical_slot="stock-start-1", attempt=0)
    assert B.next_series_action(ledger) == ("interrupted-slot", ("stock-start-1", 0))


def test_v2_concurrent_verify_write_heavy_and_balanced():
    options = dict(arm="random", key="key", sidecar_dir="sidecar", prebuild_receipt="receipt")
    assert "--verify-performance-concurrent" in B.slot_argv(
        workload="write-heavy", cohort=B.COHORT_REGISTERED_V2, **options)
    assert "--verify-performance-concurrent" in B.slot_argv(
        workload="balanced", cohort=B.COHORT_REGISTERED_V2, **options)
    assert "--verify-performance-concurrent" not in B.slot_argv(
        workload="write-heavy", cohort=B.COHORT_REGISTERED, **options)
    assert "--verify-performance-concurrent" not in B.slot_argv(
        workload="balanced", cohort=B.COHORT_REGISTERED, **options)


def test_v2_random_seed_preimage_uses_v2_version():
    weights = (2, 3, 5)
    U = int.from_bytes(hashlib.sha256(
        b"b5-generator-contrast-v2|random|write-heavy|1|1|0").digest(), "big")
    expected = 1 if U % 10 < 2 else 2 if U % 10 < 5 else 3
    assert B.random_value("write-heavy", 1, 1, weights, version=B.PREREG_VERSION_V2) == (expected, 0)
    assert B.slot_key(B.COHORT_REGISTERED_V2, "random", "write-heavy", 1,
                      "search", 1, 0).startswith(B.PREREG_VERSION_V2 + "|")


def test_v2_llm_first_job_has_stock_and_one_evaluation(tmp_path, monkeypatch):
    def publish(_seconds):
        directory = tmp_path / "ledger/handshake"
        request = json.loads((directory / "request-1.json").read_text())
        planner_input = {"whiteboard": [], "current_perf": request["current_perf"]}
        coder_input = {"whiteboard": [], "baseline": request["baseline"]}
        (directory / "inputs-1.json").write_text(json.dumps({"planner_input": planner_input,
                                                            "coder_input": coder_input}))
        doc = {"planner": {"axis": L.MARKER_ID, "direction": "decrease", "magnitude": "small"},
               "coder": {"proposal": {"axis": L.MARKER_ID, "value": 20,
                           "implementation": "double now_backoff = 20;", "justification": "fixture",
                           "confidence": "low"}, "knowledge_use": [], "classification": "de_novo",
                         "data_boundary_report": {"instruction_like_content_detected": False,
                                                  "details": "fixture"}},
               "prior_critic_reverse": True}
        (directory / "proposal-1.json").write_text(json.dumps(doc))
        B._v2_proposal(B.SeriesLedger(tmp_path / "ledger"), 1, 0,
                       directory / "proposal-1.json", {"arm": "llm"})
    monkeypatch.setattr(B.time, "sleep", publish)
    runner = FakeRunner()
    result = _v2_step(tmp_path, runner, "stock-evaluation-1", "llm", k2=B.K2Args(Path("manifest")))
    assert [call["kind"] for call in runner.calls] == ["stock-start", "search"]
    assert len(_events(result, "proposal-opportunity")) == 1
    assert len(_events(result, "evaluation-result")) == 1


def test_v2_outage_restarts_stock_and_same_request_a(tmp_path, monkeypatch):
    requests = []
    def outage(_seconds):
        request = json.loads((tmp_path / "ledger/handshake/request-1.json").read_text())
        requests.append(request)
        (tmp_path / "ledger/handshake/outage-1.json").write_text('{"api_error_status":429}')
    monkeypatch.setattr(B.time, "sleep", outage)
    runner = FakeRunner()
    first = _v2_step(tmp_path, runner, "stock-evaluation-1", "llm", k2=B.K2Args(Path("manifest")))
    assert len(_events(first, "stock-start")) == 1
    assert not _events(first, "proposal-opportunity") and not _events(first, "evaluation-result")
    assert B.next_series_action(tmp_path / "ledger") == ("stock-evaluation-1", None)
    second = _v2_step(tmp_path, runner, "stock-evaluation-1", "llm", k2=B.K2Args(Path("manifest")))
    assert len(_events(second, "stock-start")) == 2
    assert [call["kind"] for call in runner.calls] == ["stock-start", "stock-start"]
    assert len(requests) == 2 and all(row["a"] == 1 for row in requests)
    assert requests[0]["current_perf_source"]["campaign_root"] != requests[1]["current_perf_source"]["campaign_root"]


def test_series_scores_fresh_sessions_after_endpoint_fix(tmp_path):
    def before(call, directory):
        if call["kind"] == "score":
            ledger = B.SeriesLedger(directory.parents[1])
            assert [e for e in ledger.events if e["kind"] != "slot-attempt-start"][-1]["kind"] in {"endpoint-fixed", "score-session"}
            assert len([e for e in ledger.events if e["kind"] == "endpoint-fixed"]) == 1

    def policy(kind, n, attempt):
        median = 1000. if kind == "search" else float(10 * n)
        return {"bench": _bench(tps=[median] * 5, median_tps=median)}

    runner = FakeRunner(policy, before)
    result = _series(tmp_path, runner)
    assert [c["kind"] for c in runner.calls] == ["stock-start"] + ["search"] * 10 + ["score"] * 5
    assert len({c["key"] for c in runner.calls}) == 16
    end = result["events"][-1]
    assert (end["a"], end["b"], end["score"], end["reason"]) == (10, 10, 30., "b-complete")
    assert end["score_sessions"] == [10., 20., 30., 40., 50.]
    endpoint = _events(result, "endpoint-fixed")[0]["endpoint"]
    score_bytes = {c["proposal_bytes"] for c in runner.calls if c["kind"] == "score"}
    assert score_bytes == {Path(endpoint["proposal_path"]).read_bytes()}
    assert result["header"]["allocation_deadline_status"] == "unknown"
    assert result["header"]["tier0_status"] == "implemented"


def test_submitted_abort_consumes_B_and_history_does_not_stop_next_slot(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "abort", "abort_reason": "build-error"}
                        if kind == "search" else {})
    result = _series(tmp_path, runner)
    assert len(_events(result, "evaluation-result")) == 10
    assert [e["b"] for e in _events(result, "evaluation-result")] == list(range(1, 11))
    assert result["events"][-1]["b"] == 10
    assert len(runner.calls) == 11
    assert all(e["outcome"] == "build-failed" for e in _events(result, "evaluation-result"))


@pytest.mark.parametrize("arm,count,reason", [("random", 30, "a-exhausted"), ("sweep-matched", 28, "grid-exhausted")])
def test_preprocess_reject_advances_candidates_to_registered_cap(tmp_path, arm, count, reason):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "rejected-preprocess"} if kind == "search" else {})
    result = _series(tmp_path, runner, arm)
    assert len(_events(result, "proposal-opportunity")) == count
    assert result["events"][-1]["reason"] == reason
    assert result["events"][-1]["b"] == 0
    if arm == "sweep-matched":
        assert [c["value"] for c in runner.calls[1:]] == list(B.sweep_order("write-heavy", 1))


@pytest.mark.parametrize("failure", ["pre-start-failure", "machine-failure"])
def test_retry_same_logical_slot_fresh_attempt_without_AB_increment(tmp_path, failure):
    def policy(kind, n, attempt):
        if kind == "search" and n == 1 and attempt < 2:
            return {"outcome": "abort", "abort_reason": "bench-probe-error"} if failure == "machine-failure" else {"outcome": failure}
        return {}
    runner = FakeRunner(policy)
    result = _series(tmp_path, runner)
    attempts = [c for c in runner.calls if c["kind"] == "search" and c["n"] == 1]
    assert [c["attempt"] for c in attempts] == [0, 1, 2]
    assert len({c["proposal_bytes"] for c in attempts}) == 1
    assert len({c["key"] for c in attempts}) == 3
    assert len(_events(result, "machine-retry")) == 2
    assert result["events"][-1]["a"] == result["events"][-1]["b"] == 10


def test_machine_retry_exhaustion_is_missing_without_fallback(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "abort", "abort_reason": "bench-competing-tenant"}
                        if kind == "search" else {})
    result = _series(tmp_path, runner)
    assert len(runner.calls) == 4
    assert result["events"][-1]["reason"] == "unclassified-missing"
    assert result["events"][-1]["b"] == 1
    assert "fallback" not in result["events"][-1]


def test_duplicate_skip_ends_series_without_B_or_retry(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "duplicate-skip"} if kind == "search" else {})
    result = _series(tmp_path, runner)
    assert result["events"][-1]["reason"] == "unclassified-missing"
    assert result["events"][-1]["a"] == 1 and result["events"][-1]["b"] == 0
    assert not _events(result, "machine-retry") and not _events(result, "score-session")


def test_submitted_unresolved_consumes_B_without_retry(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "submitted-unresolved"} if kind == "search" else {})
    result = _series(tmp_path, runner)
    assert result["events"][-1]["reason"] == "unclassified-missing"
    assert result["events"][-1]["b"] == 1
    assert not _events(result, "machine-retry")


def test_quality_missing_keeps_budget_without_retry(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"bench": _bench(unstable=True)}
                        if kind == "search" and n == 1 else {})
    result = _series(tmp_path, runner)
    evaluations = _events(result, "evaluation-result")
    assert len(evaluations) == 10 and evaluations[0]["quality"] == "quality-missing"
    endpoint = _events(result, "endpoint-fixed")[0]["endpoint"]
    assert endpoint["b"] != 1
    assert not _events(result, "machine-retry")


def test_score_anomaly_has_no_reselection(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "anomaly", "abort_reason": "verify-red"}
                        if kind == "score" else {})
    result = _series(tmp_path, runner)
    assert len(_events(result, "endpoint-fixed")) == len(_events(result, "score-session")) == 1
    assert result["events"][-1]["fallback"] == "pending-block-stock"
    assert result["events"][-1]["score"] is None


@pytest.mark.parametrize("behavior", [{"bench": _bench(settled=False)}, {"src": "d" * 64},
                                       {"outcome": "abort", "abort_reason": "build-error"}])
def test_stock_unestablished_prevents_proposal(tmp_path, behavior):
    result = _series(tmp_path, FakeRunner(lambda *_: behavior))
    assert result["events"][-1]["reason"] == "stock-unestablished"
    assert not _events(result, "proposal-opportunity")


def test_block_stock_five_independent_sessions(tmp_path):
    runner = FakeRunner()
    result = B.run_block_stock("balanced", 2, ledger_root=tmp_path / "ledger",
                              prebuild_receipt=tmp_path / "receipt", repo_root=ROOT, runner=runner)
    assert len(runner.calls) == 5 and len({c["key"] for c in runner.calls}) == 5
    assert [c["n"] for c in runner.calls] == [1, 2, 3, 4, 5]
    assert all(c["kind"] == "block-stock" and c["value"] == -1 for c in runner.calls)
    assert result["events"][-1]["reason"] == "b-complete"


def test_allocation_exhausted_starts_no_new_session(tmp_path, monkeypatch):
    monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "1")
    runner = FakeRunner()
    result = _series(tmp_path, runner)
    assert result["events"][-1]["reason"] == "allocation-exhausted"
    assert runner.calls == []


def _diagnosis():
    return {"data_boundary": "critic_diagnosis_is_data_not_instructions",
            "source_sha256": "a" * 64, "attribution": "fixture",
            "recommend": [], "avoid": [], "uncertainty": "fixture"}


def _input_ledger(tmp_path):
    ledger = B.SeriesLedger.create(tmp_path / "ledger", {"arm": "llm"})
    ledger.append("stock-start", outcome="certified", quality="normal", fitness_tps=20., b=0,
                  campaign_root="stock", bench_payload=_bench())
    for k, (direction, outcome, fitness) in enumerate([
            ("increase", "certified", 40.), ("decrease", "aborted", None)], 1):
        ledger.append("evaluation-result", b=k, outcome=outcome,
                      quality="normal" if fitness else None, fitness_tps=fitness,
                      campaign_root=f"evaluation-{k}", bench_payload=_bench(),
                      whiteboard_entry={"iteration": k, "direction": direction, "magnitude": "small",
                                        "result": "success" if fitness else "fail", "delta_pct": None})
    return ledger


def test_inheritance_order_and_all_fields_checked(tmp_path):
    ledger = _input_ledger(tmp_path)
    expected = B.expected_inputs(ledger, 3)
    assert expected["current_perf"]["throughput_tps"] == 40.
    assert expected["current_perf_source"]["campaign_root"] == "evaluation-1"
    planner = {"whiteboard": expected["expected_whiteboard"], "current_perf": expected["current_perf"]}
    coder = {"whiteboard": expected["expected_whiteboard"], "baseline": expected["baseline"]}
    planner["k2_critic_diagnosis"] = coder["k2_critic_diagnosis"] = _diagnosis()
    B.assert_inherited_inputs(ledger, planner, coder, next_evaluation=3)
    reversed_board = list(reversed(expected["expected_whiteboard"]))
    with pytest.raises(ValueError, match="whiteboard"):
        B.assert_inherited_inputs(ledger, {**planner, "whiteboard": reversed_board},
                                  {**coder, "whiteboard": reversed_board}, next_evaluation=3)
    for key, wrong in [("delta_pct", 0.), ("magnitude", "large"), ("extra", None)]:
        board = [{**expected["expected_whiteboard"][0], key: wrong}, expected["expected_whiteboard"][1]]
        with pytest.raises(ValueError, match="whiteboard"):
            B.assert_inherited_inputs(ledger, {**planner, "whiteboard": board}, coder, next_evaluation=3)
    with pytest.raises(ValueError, match="baseline"):
        B.assert_inherited_inputs(ledger, planner, {**coder, "baseline": {"throughput_tps": 20.}}, next_evaluation=3)
    with pytest.raises(ValueError, match="diagnosis"):
        B.assert_inherited_inputs(ledger, {**planner, "k2_critic_diagnosis": {}}, coder, next_evaluation=3)


def test_handshake_timeout_ends_without_retry(tmp_path, monkeypatch):
    # Time is an external boundary. Advance it without changing LLM_WAIT_S.
    clock = [0.]
    monkeypatch.setattr(B.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(B.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    runner = FakeRunner()
    result = _series(tmp_path, runner, "llm", k2=B.K2Args(Path("manifest")))
    assert result["events"][-1]["reason"] == "proposal-wait-timeout"
    assert clock[0] == 2700
    assert len(runner.calls) == 1 and not _events(result, "machine-retry")
    assert result["events"][-1]["a"] == 1 and result["events"][-1]["b"] == 0
    assert (tmp_path / "ledger/handshake/request-1.json").exists()


def test_handshake_rejection_consumes_A_then_next_request(tmp_path, monkeypatch):
    seen = []
    def parent_reply(seconds):
        root = tmp_path / "ledger/handshake"
        requests = sorted(root.glob("request-*.json"), key=lambda p: int(p.stem.split("-")[-1]))
        request = json.loads(requests[-1].read_text())
        a = request["a"]
        seen.append(a)
        (root / f"proposal-{a}.rejected.json").write_text('{"reason":"empty output"}')
    monkeypatch.setattr(B.time, "sleep", parent_reply)
    result = _series(tmp_path, FakeRunner(), "llm", k2=B.K2Args(Path("manifest")))
    assert seen == list(range(1, 31))
    assert result["events"][-1]["reason"] == "a-exhausted"
    assert result["events"][-1]["b"] == 0


def test_handshake_mismatched_inputs_end_before_evaluation(tmp_path, monkeypatch):
    def parent_reply(seconds):
        root = tmp_path / "ledger/handshake"
        (root / "proposal-1.json").write_text("{}")
        (root / "inputs-1.json").write_text('{"planner_input":{"whiteboard":[{}]},"coder_input":{}}')
    monkeypatch.setattr(B.time, "sleep", parent_reply)
    runner = FakeRunner()
    result = _series(tmp_path, runner, "llm", k2=B.K2Args(Path("manifest")))
    assert result["events"][-1]["reason"] == "inheritance-mismatch"
    assert len(runner.calls) == 1


def test_ledger_events_are_immutable_and_view_rebuildable(tmp_path):
    ledger = B.SeriesLedger.create(tmp_path, {"arm": "random"})
    ledger.append("series-start", a=0, b=0)
    original = (tmp_path / "events/000001-series-start.json").read_bytes()
    with pytest.raises(FileExistsError):
        B._publish(tmp_path / "events/000001-series-start.json", {})
    assert (tmp_path / "events/000001-series-start.json").read_bytes() == original
    (tmp_path / "series.json").unlink()
    assert B.SeriesLedger(tmp_path).view() == ledger.view()
    ledger.append("series-end", a=0, b=0, reason="a-exhausted")
    with pytest.raises(ValueError):
        ledger.append("series-start")
    with pytest.raises(FileExistsError):
        B.SeriesLedger.create(tmp_path, {})


@pytest.mark.parametrize("arm", ["random", "sweep-matched", "llm"])
@pytest.mark.parametrize("stock", [False, True])
def test_slot_argv_literal_contract(arm, stock):
    k2 = B.K2Args(Path("M"), "reproduction_or_selection", "false") if arm == "llm" else None
    actual = B.slot_argv(arm=arm, workload="balanced", key="KEY", sidecar_dir="D",
                         prebuild_receipt="R", proposal_path=None if stock else "P", k2=k2)
    expected = [sys.executable, "-B", "-m", "orchestrator.campaign.p3_s4_loop"]
    expected += ["--stock-control"] if stock else ["--run-iteration", "P"]
    expected += ["--isolate-worktree", "--fetchcontent-prebuild-receipt", "R", "--calibrated-perf",
                 "--perf-workload", "balanced", "--verify-performance", "--b5-slot", "KEY", "--b5-sidecar-dir", "D"]
    if arm == "llm":
        if not stock:
            expected += ["--allow-coder-derived-build"]
        expected += ["--knowledge-manifest", "M"]
        if not stock:
            expected += ["--coder-role", "coder-v4-autonomous-k2"]
        expected += ["--knowledge-classification", "reproduction_or_selection", "--knowledge-de-novo-claim", "false"]
    elif not stock:
        expected += ["--machine-generated-proposal"]
    assert actual == expected


@pytest.mark.parametrize("arm,extra", [("random", ["--knowledge-manifest", "M"]),
                                       ("sweep-matched", ["--knowledge-classification", "x"]),
                                       ("llm", [])])
def test_cli_rejects_cross_arm_knowledge_options(tmp_path, arm, extra):
    with pytest.raises(SystemExit) as exc:
        B.main(["run-series", "--arm", arm, "--workload", "balanced", "--series", "1", "--block", "1",
                "--ledger-root", str(tmp_path), "--fetchcontent-prebuild-receipt", "R", *extra])
    assert exc.value.code == 2
    assert not (tmp_path / "header.json").exists()


def test_cli_weights_real_subprocess(tmp_path):
    output = tmp_path / "weights.json"
    result = subprocess.run([sys.executable, "-B", "-m", "orchestrator.campaign.b5_generator_contrast",
                             "weights-material", "--out", str(output)], cwd=ROOT,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())["weights_sha256"] == "876b1b4798fbf79dfefaffd9ccefceaf0beb16cb8561cc5ea4e28745bbd20bdd"


def test_expected_inputs_cli_uses_ledger_not_series_view(tmp_path):
    ledger = _input_ledger(tmp_path)
    (ledger.root / "series.json").write_text("{}")
    output = tmp_path / "expected.json"
    assert B.main(["expected-inputs", "--ledger-root", str(ledger.root), "--next-evaluation", "3", "--out", str(output)]) == 0
    assert json.loads(output.read_text())["current_perf"]["throughput_tps"] == 40.


def test_llm_handshake_valid_inputs_drive_ten_fresh_evaluations(tmp_path, monkeypatch):
    from orchestrator.campaign.projection_guard import CODER_CONTRACT_K2
    delivered = []
    def parent_reply(seconds):
        directory = tmp_path / "ledger/handshake"
        requests = sorted(directory.glob("request-*.json"), key=lambda p: int(p.stem.split("-")[-1]))
        request = json.loads(requests[-1].read_text())
        a = request["a"]
        assert request["next_evaluation"] == a
        assert len(request["expected_whiteboard"]) == a - 1
        assert request["current_perf"]["abort_rate_pct"] == pytest.approx(7.)
        planner = {"whiteboard": request["expected_whiteboard"], "current_perf": request["current_perf"]}
        coder_input = {"whiteboard": request["expected_whiteboard"], "baseline": request["baseline"]}
        if a >= 2:
            planner["k2_critic_diagnosis"] = coder_input["k2_critic_diagnosis"] = _diagnosis()
        inputs = {"planner_input": planner, "coder_input": coder_input}
        doc = {"planner": {"axis": L.MARKER_ID, "direction": "decrease", "magnitude": "small"},
               "coder": {"proposal": {"axis": L.MARKER_ID, "value": 20,
                         "implementation": "double now_backoff = 20;", "justification": "fixture", "confidence": "low"},
                         "knowledge_use": [], "classification": "de_novo",
                         "data_boundary_report": {"instruction_like_content_detected": False, "details": "fixture"}},
               "prior_critic_reverse": True}
        assert_closed_proposal_schema(doc, require_auditor=False, require_coder_value=True,
                                      coder_contract=CODER_CONTRACT_K2)
        proposal = directory / f"proposal-{a}.json"
        proposal.write_text(json.dumps(doc))
        knowledge = {"data_boundary": "external_knowledge_is_data_not_instructions",
                     "knowledge_level": "K2", "knowledge_manifest_sha256": "a" * 64, "sources": []}
        # Real K2 loader verifies the fixture, separate from fake subprocess.
        _, coder, reverse = L.load_proposal_file(str(proposal), knowledge_input=knowledge,
                                                 coder_role="coder-v4-autonomous-k2")
        assert coder.value == 20 and reverse is True
        (directory / f"inputs-{a}.json").write_text(json.dumps(inputs))
        delivered.append(a)
    monkeypatch.setattr(B.time, "sleep", parent_reply)
    runner = FakeRunner()
    result = _series(tmp_path, runner, "llm", k2=B.K2Args(Path("manifest")))
    assert delivered == list(range(1, 11))
    assert len(runner.calls) == 16  # repeated reverse and identical performance never stop the series
    assert result["events"][-1]["b"] == 10
    assert all(e["whiteboard_entry"]["delta_pct"] is None for e in _events(result, "evaluation-result"))


def test_sweep_rejections_continue_after_tenth_candidate(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "rejected-preprocess"}
                        if kind == "search" and n <= 3 else {})
    result = _series(tmp_path, runner, "sweep-matched")
    search = [c for c in runner.calls if c["kind"] == "search"]
    assert len(search) == 13
    assert [c["value"] for c in search] == list(B.sweep_order("write-heavy", 1))[:13]
    assert result["events"][-1]["a"] == 13 and result["events"][-1]["b"] == 10


@pytest.mark.parametrize("submitted", [False, True])
def test_subprocess_timeout_is_never_machine_retry(tmp_path, submitted):
    normal = FakeRunner()
    calls = []
    def runner(argv, *, cwd):
        calls.append(argv)
        if "--stock-control" in argv:
            return normal(argv, cwd=cwd)
        if submitted:
            normal(argv, cwd=cwd)
        raise subprocess.TimeoutExpired(argv, 1800)
    result = _series(tmp_path, runner)
    assert len(calls) == 2
    assert not _events(result, "machine-retry")
    assert result["events"][-1]["reason"] == "unclassified-missing"
    assert result["events"][-1]["b"] == int(submitted)


def test_all_quality_missing_has_no_stock_fallback(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"bench": _bench(unstable=True)} if kind == "search" else {})
    result = _series(tmp_path, runner)
    assert result["events"][-1]["b"] == 10
    assert result["events"][-1]["reason"] == "unclassified-missing"
    assert not result["events"][-1].get("fallback")
    assert not _events(result, "endpoint-fixed")[0].get("fallback")
    assert not _events(result, "score-session")


def test_score_quality_missing_is_not_fallback_or_retry(tmp_path):
    runner = FakeRunner(lambda kind, n, t: {"bench": _bench(settled=None)} if kind == "score" else {})
    result = _series(tmp_path, runner)
    assert len(_events(result, "score-session")) == 1
    assert result["events"][-1]["reason"] == "unclassified-missing"
    assert not result["events"][-1].get("fallback")
    assert not _events(result, "machine-retry")


def test_allocation_is_checked_between_sessions(tmp_path, monkeypatch):
    count = []
    def before(call, directory):
        count.append(call)
        if call["kind"] == "search":
            monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "1")
    result = _series(tmp_path, FakeRunner(before=before))
    assert [c["kind"] for c in count] == ["stock-start", "search"]
    assert result["events"][-1]["reason"] == "allocation-exhausted"
    assert result["events"][-1]["b"] == 1


def test_default_runner_uses_repo_cwd_and_no_bytecode(monkeypatch):
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, "", "")
    monkeypatch.setattr(B.subprocess, "run", run)
    argv = B.slot_argv(arm="random", workload="balanced", key="KEY", sidecar_dir="D",
                       prebuild_receipt="R", proposal_path="P")
    B.default_runner(argv, cwd=ROOT)
    assert calls[0][0][:4] == [sys.executable, "-B", "-m", "orchestrator.campaign.p3_s4_loop"]
    assert calls[0][1]["cwd"] == ROOT
    assert calls[0][1]["env"]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_registered_budgets_and_no_cli_overrides():
    assert (B.A_PROPOSALS, B.B_EVALUATIONS, B.N_EVAL, B.BLOCK_STOCK_SESSIONS) == (30, 10, 5, 5)
    assert 3 * (1 + B.B_EVALUATIONS + B.N_EVAL) + B.BLOCK_STOCK_SESSIONS == 53
    assert B.PILOT_LOGICAL_SESSION_CAP == 60
    assert (B.MAX_MACHINE_RETRIES, B.LLM_WAIT_S, B.LLM_POLL_S, B.SESSION_BUDGET_S) == (2, 2700, 15, 1800)
    with pytest.raises(SystemExit) as exc:
        B.main(["run-series", "--B", "11"])
    assert exc.value.code == 2


def test_new_cli_static_bootstrap_and_import_contract():
    from orchestrator.tests import test_campaign_import_invariant as I
    path = "orchestrator/campaign/b5_generator_contrast.py"
    assert I.scan_campaign_shape(path, (ROOT / path).read_text()) == ()



def test_registered_thousand_weights_end_to_end_fixed_vector():
    weights = B.weights_table()
    assert weights[0] == 235865763225513294137944142764154484399
    assert weights[-1] == 340112339079931042622455095438973892
    assert sum(weights) == 2350927428781729131458637903205781083070
    assert B.weights_material()["weights_sha256"] == "876b1b4798fbf79dfefaffd9ccefceaf0beb16cb8561cc5ea4e28745bbd20bdd"
    assert [B.random_value("write-heavy", 1, a, weights) for a in range(1, 5)] == [
        (698, 0), (1, 0), (5, 0), (364, 0)]
    assert list(B.sweep_order("write-heavy", 1)[:10]) == [8, 25, 600, 50, 100, 200, 12, 250, 150, 2]


def test_wal_diff_quarantine_without_rejection_sidecar_continues(tmp_path):
    normal = FakeRunner()
    rejected_keys = []

    def runner(argv, *, cwd):
        key = argv[argv.index("--b5-slot") + 1]
        if "|search|1|" not in key:
            return normal(argv, cwd=cwd)
        rejected_keys.append(key)
        sidecar = Path(argv[argv.index("--b5-sidecar-dir") + 1])
        proposal = json.loads(Path(argv[argv.index("--run-iteration") + 1]).read_text())
        genome = _genome(proposal["coder"]["value"])
        root = _write_attempt(sidecar, key=key, value=proposal["coder"]["value"],
                              outcome="unclassified-missing")
        records = [
            WalRecord("diffq-fixture", "build_start", "linux-baremetal", 1., {
                "build_attempt_id": "diffq-attempt", "genome": genome.canonical(), "src_token": ""}),
            WalRecord("diffq-fixture", "abort", "linux-baremetal", 2., {
                "build_attempt_id": "diffq-attempt", "genome": genome.canonical(),
                "reason": "diff-quarantine",
                "diff_quarantine": {"rule_id": "backoff-grammar.raw-size.v1"}}),
        ]
        (root / "runs/wal.jsonl").write_text(
            "".join(json.dumps(asdict(record)) + "\n" for record in records))
        assert (sidecar / "slot-start.json").is_file()
        assert not (sidecar / "proposal-rejected.json").exists()
        assert not (sidecar / "pipeline-submitted.json").exists()
        observed = B.classify_slot(sidecar, None, 5, genome)
        assert (observed["outcome"], observed["failure_class"], observed["submitted"]) == (
            "rejected-preprocess", "candidate", False)
        assert observed["wal_sha256"]
        return subprocess.CompletedProcess(argv, 0, "outcome=rejected", "")

    result = _series(tmp_path, runner)
    assert len(rejected_keys) == 1 and not _events(result, "machine-retry")
    rejection, = _events(result, "proposal-rejected")
    assert (rejection["a"], rejection["b"], rejection["returncode"]) == (1, 0, 0)
    assert (result["events"][-1]["a"], result["events"][-1]["b"]) == (11, 10)
    assert result["events"][-1]["reason"] == "b-complete"


@pytest.mark.parametrize("with_start", [False, True])
def test_rejected_sidecar_advances_without_retry_m21(tmp_path, with_start):
    normal = FakeRunner()
    rejected_keys = []
    def runner(argv, *, cwd):
        key = argv[argv.index("--b5-slot") + 1]
        if "|search|1|" not in key:
            return normal(argv, cwd=cwd)
        rejected_keys.append(key)
        sidecar = Path(argv[argv.index("--b5-sidecar-dir") + 1])
        proposal = json.loads(Path(argv[argv.index("--run-iteration") + 1]).read_text())
        coder = L.CoderProposal(**{**proposal["coder"], "implementation": "double now_backoff = 30;"})
        with pytest.raises(L.AttributionMismatch) as error:
            L._check_attribution_before_quarantine(coder)
        if with_start:
            _write_attempt(sidecar, key=key, value=coder.value, outcome="unclassified-missing")
        L._b5_proposal_rejected(sidecar, key, error.value)
        observed = B.classify_slot(sidecar, None, 5, _genome(coder.value))
        assert (observed["outcome"], observed["failure_class"], observed["submitted"]) == (
            "rejected-preprocess", "candidate", False)
        return subprocess.CompletedProcess(argv, 3, "", "")
    result = _series(tmp_path, runner)
    assert len(rejected_keys) == 1 and not _events(result, "machine-retry")
    rejection, = _events(result, "proposal-rejected")
    assert (rejection["a"], rejection["b"]) == (1, 0)
    assert (result["events"][-1]["a"], result["events"][-1]["b"]) == (11, 10)


@pytest.mark.parametrize("reason", ["verify-probe-error", "verify-competing-tenant"])
@pytest.mark.parametrize("exhausted", [False, True])
def test_verify_machine_retry_and_exhaustion_m22(tmp_path, reason, exhausted):
    runner = FakeRunner(lambda kind, n, t: {"outcome": "abort", "abort_reason": reason}
                        if kind == "search" and n == 1 and (exhausted or t == 0) else {})
    result = _series(tmp_path, runner)
    retries = _events(result, "machine-retry")
    assert len(retries) == (2 if exhausted else 1)
    assert all(e["outcome"] == "machine-failure" and e["b"] == 1 for e in retries)
    end = result["events"][-1]
    if exhausted:
        assert (end["reason"], end["b"], end["score"]) == ("unclassified-missing", 1, None)
        assert not end.get("fallback") and not _events(result, "endpoint-fixed")
    else:
        assert (end["reason"], end["b"]) == ("b-complete", 10)
    assert "indeterminate" not in B.MACHINE_FAILURE_ABORT_REASONS


def test_attempt_start_durable_before_runner_exception_m23(tmp_path):
    def runner(argv, *, cwd):
        ledger = B.SeriesLedger(tmp_path / "ledger")
        event = ledger.events[-1]
        assert event["kind"] == "slot-attempt-start"
        assert (event["slot_kind"], event["n"], event["a"], event["b"], event["attempt"]) == (
            "stock-start", 1, 0, 0, 0)
        assert event["logical_slot"] == "stock-start-1"
        assert event["slot_key"] == argv[argv.index("--b5-slot") + 1]
        assert ledger.root / event["sidecar_dir"] == Path(argv[argv.index("--b5-sidecar-dir") + 1])
        raise RuntimeError("driver killed")
    with pytest.raises(RuntimeError, match="driver killed"):
        _series(tmp_path, runner)
    assert B.SeriesLedger(tmp_path / "ledger").events[-1]["kind"] == "slot-attempt-start"


def test_both_critic_diagnoses_required_m27(tmp_path):
    ledger = _input_ledger(tmp_path)
    expected = B.expected_inputs(ledger, 3)
    planner = {"whiteboard": expected["expected_whiteboard"], "current_perf": expected["current_perf"]}
    coder = {"whiteboard": expected["expected_whiteboard"], "baseline": expected["baseline"]}
    with pytest.raises(ValueError, match="diagnosis"):
        B.assert_inherited_inputs(ledger, planner, coder, next_evaluation=3)
    planner["k2_critic_diagnosis"] = coder["k2_critic_diagnosis"] = _diagnosis()
    B.assert_inherited_inputs(ledger, planner, coder, next_evaluation=3)


@pytest.mark.parametrize("missing", ["manifest", "classification", "de-novo-claim"])
def test_cli_llm_requires_complete_k2_bundle(tmp_path, missing):
    options = {"manifest": "M", "classification": "de_novo", "de-novo-claim": "true"}
    extra = [arg for key, value in options.items() if key != missing for arg in ("--knowledge-" + key, value)]
    with pytest.raises(SystemExit) as error:
        B.main(["run-series", "--arm", "llm", "--workload", "write-heavy", "--series", "1",
                "--block", "1", "--ledger-root", str(tmp_path), "--fetchcontent-prebuild-receipt", "R", *extra])
    assert error.value.code == 2
    assert not (tmp_path / "header.json").exists()


@pytest.mark.parametrize("status", ["proposal", "proposal-rejected", "inheritance-mismatch",
                                    "proposal-wait-timeout", "allocation-exhausted"])
def test_handshake_all_exit_statuses_record_elapsed(tmp_path, monkeypatch, status):
    ledger = B.SeriesLedger.create(tmp_path / "ledger", {"arm": "llm"})
    ledger.append("stock-start", outcome="certified", quality="normal", fitness_tps=100., b=0,
                  bench_payload=_bench(), campaign_root="stock")
    clock = [0.]
    monkeypatch.setattr(B.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(B, "_allocation_available", lambda: status != "allocation-exhausted" or clock[0] == 0)
    def reply(seconds):
        clock[0] += seconds
        directory = ledger.root / "handshake"
        if status == "proposal-rejected":
            (directory / "proposal-1.rejected.json").write_text('{"reason":"empty"}')
        elif status in {"proposal", "inheritance-mismatch"}:
            expected = B.expected_inputs(ledger, 1)
            (directory / "proposal-1.json").write_text("{}")
            (directory / "inputs-1.json").write_text(json.dumps({
                "planner_input": {"whiteboard": [], "current_perf": expected["current_perf"]},
                "coder_input": {"whiteboard": [], "baseline": expected["baseline"] if status == "proposal" else {}}}))
    monkeypatch.setattr(B.time, "sleep", reply)
    actual, _, provenance = B._handshake(ledger, 1, 0)
    assert actual == provenance["handshake_status"] == status
    assert provenance["proposal_wait_wall_s"] == (2700 if status == "proposal-wait-timeout" else 15)

def test_retry_allocation_exhaustion_retains_submitted_evaluation(tmp_path, monkeypatch):
    from orchestrator.campaign import b5_generator_contrast_report as report
    def before(call, sidecar):
        if call["kind"] == "search":
            monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "1")
    runner = FakeRunner(lambda kind, n, t: {"outcome": "abort", "abort_reason": "verify-probe-error"}
                        if kind == "search" else {}, before)
    result = _series(tmp_path, runner)
    assert (result["events"][-1]["reason"], result["events"][-1]["b"]) == ("allocation-exhausted", 1)
    assert len(_events(result, "evaluation-result")) == 1
    consumed = report.build_report([tmp_path / "ledger"], purpose="pilot")
    assert not consumed["invalid"]
    assert consumed["series"][0]["score"] is None


@pytest.mark.parametrize("mutation", ["M21", "M22", "M23", "M27"])
def test_fix2_producer_mutants_killed(tmp_path, monkeypatch, mutation):
    import types
    source = Path(B.__file__).read_text()
    if mutation == "M21":
        source = source.replace('if rejected.exists():', 'if False and rejected.exists():', 1)
    elif mutation == "M22":
        source = source.replace('"verify-probe-error", "verify-competing-tenant"', '')
    elif mutation == "M23":
        start = source.index('        ledger.append("slot-attempt-start"')
        end = source.index('        started = time.monotonic()', start)
        block = source[start:end]
        source = source[:start] + source[end:]
        boundary = '            completed = runner(argv, cwd=Path(repo_root))\n'
        source = source.replace(boundary, boundary + ''.join('    ' + line for line in block.splitlines(True)))
    else:
        source = source.replace('if next_evaluation >= 2 and diagnosis_key not in planner_input:',
                                'if False and diagnosis_key not in planner_input:')
    mutant = types.ModuleType("orchestrator.campaign.b5_fix2_mutant")
    mutant.__package__, mutant.__file__ = "orchestrator.campaign", B.__file__
    monkeypatch.setitem(sys.modules, mutant.__name__, mutant)
    exec(compile(source, B.__file__, "exec"), mutant.__dict__)
    monkeypatch.setitem(globals(), "B", mutant)
    with pytest.raises((AssertionError, pytest.fail.Exception)):
        if mutation == "M21":
            test_rejected_sidecar_advances_without_retry_m21(tmp_path, False)
        elif mutation == "M22":
            test_verify_machine_retry_and_exhaustion_m22(tmp_path, "verify-probe-error", False)
        elif mutation == "M23":
            test_attempt_start_durable_before_runner_exception_m23(tmp_path)
        else:
            test_both_critic_diagnoses_required_m27(tmp_path)


@pytest.mark.parametrize("arm,count,reason", [("random", 30, "a-exhausted"),
                                             ("sweep-matched", 28, "grid-exhausted")])
def test_tier0_rejection_consumes_A_only_without_retry(tmp_path, arm, count, reason):
    runner = FakeRunner(lambda kind, n, attempt: {"outcome": "rejected-tier0"}
                        if kind == "search" else {})
    result = _series(tmp_path, runner, arm)
    end = result["events"][-1]
    assert (end["a"], end["b"], end["reason"]) == (count, 0, reason)
    assert len(runner.calls) == count + 1
    assert [c["attempt"] for c in runner.calls] == [0] * (count + 1)
    assert _events(result, "machine-retry") == []
    assert _events(result, "evaluation-result") == []
    rejected = _events(result, "proposal-rejected")
    assert len(rejected) == count
    for event in rejected:
        assert (event["outcome"], event["submitted"], event["failure_class"]) == (
            "rejected-tier0", False, "candidate")
        assert set(event["tier0"]) == {"status", "reason", "sidecar_sha256"}
        assert event["tier0"]["status"] == "rejected"


def test_retry_then_tier0_reject_retains_B(tmp_path):
    def policy(kind, n, attempt):
        if kind == "search":
            return ({"outcome": "abort", "abort_reason": "bench-probe-error"}
                    if attempt == 0 else {"outcome": "rejected-tier0"})
        return {}
    runner = FakeRunner(policy)
    result = _series(tmp_path, runner)
    assert (result["events"][-1]["a"], result["events"][-1]["b"]) == (10, 10)
    assert len(_events(result, "machine-retry")) == 10
    assert len(runner.calls) == 21
    evaluations = _events(result, "evaluation-result")
    assert [e["b"] for e in evaluations] == list(range(1, 11))
    assert [(e["outcome"], e["submitted"], e["tier0"]["status"]) for e in evaluations] == [
        ("rejected-tier0", True, "rejected")] * 10


def test_score_tier0_reject_stops_without_fallback(tmp_path):
    runner = FakeRunner(lambda kind, n, attempt: {"outcome": "rejected-tier0"}
                        if kind == "score" else {})
    result = _series(tmp_path, runner)
    end = result["events"][-1]
    assert (end["a"], end["b"], end["reason"], end["score"]) == (10, 10, "unclassified-missing", None)
    assert not end.get("fallback")
    assert len(_events(result, "endpoint-fixed")) == len(_events(result, "score-session")) == 1
    assert _events(result, "machine-retry") == []
    assert len(runner.calls) == 12


@pytest.mark.parametrize("tamper", ["missing", "json", "list", "schema", "b5_slot",
                                    "campaign_id", "genome", "contract", "rejected", "status"])
def test_submitted_requires_valid_passed_tier0(tmp_path, tamper):
    root = _write_attempt(tmp_path)
    path = tmp_path / "tier0.json"
    if tamper == "missing":
        path.unlink()
    elif tamper == "json":
        path.write_text("{")
    elif tamper == "list":
        path.write_text("[]")
    else:
        doc = json.loads(path.read_text())
        if tamper == "rejected":
            doc.update(status="rejected", reason="smoke-failed")
        else:
            doc[tamper] = "invalid"
        path.write_text(json.dumps(doc))
    observed = B.classify_slot(tmp_path, root, 5, _genome(20))
    assert (observed["outcome"], observed["submitted"], observed["failure_class"], observed["fitness_tps"]) == (
        "unclassified-missing", True, "unclassified-missing", None)


def test_missing_tier0_stops_series_with_B_retained(tmp_path):
    base = FakeRunner()
    def runner(argv, *, cwd):
        done = base(argv, cwd=cwd)
        sidecar = Path(argv[argv.index("--b5-sidecar-dir") + 1])
        if base.calls[-1]["kind"] == "search":
            (sidecar / "tier0.json").unlink()
        return done
    result = _series(tmp_path, runner)
    end = result["events"][-1]
    assert (end["a"], end["b"], end["reason"]) == (1, 1, "unclassified-missing")
    assert len(base.calls) == 2
    assert _events(result, "endpoint-fixed") == _events(result, "machine-retry") == []


def test_stock_with_tier0_is_unclassified(tmp_path):
    root = _write_attempt(tmp_path, value=-1)
    _write_tier0(tmp_path, json.loads((tmp_path / "slot-start.json").read_text()))
    observed = B.classify_slot(tmp_path, root, 5, _genome(-1))
    assert (observed["outcome"], observed["submitted"], observed["fitness_tps"]) == (
        "unclassified-missing", True, None)


@pytest.mark.parametrize("reason", ["build-error", "smoke-failed", "smoke-timeout"])
def test_tier0_rejected_evidence_without_submission(tmp_path, reason):
    root = _write_attempt(tmp_path, outcome="unclassified-missing")
    start = json.loads((tmp_path / "slot-start.json").read_text())
    _write_tier0(tmp_path, start, status="rejected", reason=reason)
    observed = B.classify_slot(tmp_path, root, 5, _genome(20))
    assert (observed["outcome"], observed["submitted"], observed["failure_class"], observed["fitness_tps"]) == (
        "rejected-tier0", False, "candidate", None)
    assert observed["tier0"] == {
        "status": "rejected", "reason": reason,
        "sidecar_sha256": hashlib.sha256((tmp_path / "tier0.json").read_bytes()).hexdigest()}


def test_passed_without_submission_is_unresolved(tmp_path):
    root = _write_attempt(tmp_path)
    (tmp_path / "pipeline-submitted.json").unlink()
    observed = B.classify_slot(tmp_path, root, 5, _genome(20))
    assert (observed["outcome"], observed["submitted"], observed["fitness_tps"]) == (
        "unclassified-missing", False, None)


def test_tier0_pass_does_not_replace_anomaly_gate(tmp_path):
    runner = FakeRunner(lambda kind, n, attempt: {"outcome": "anomaly", "abort_reason": "verify-red"}
                        if kind == "search" and n == 1 else {})
    result = _series(tmp_path, runner)
    first = _events(result, "evaluation-result")[0]
    assert (first["outcome"], first["b"], first["submitted"], first["fitness_tps"]) == (
        "anomaly", 1, True, None)
    assert first["tier0"]["status"] == "passed"
    endpoint = _events(result, "endpoint-fixed")[0]["endpoint"]
    assert endpoint["value"] != first["value"]
    assert endpoint["outcome"] == "certified"


def test_smoke_numbers_never_enter_events_inputs_or_endpoint(tmp_path):
    result = _series(tmp_path, FakeRunner())
    ledger = B.SeriesLedger(tmp_path / "ledger")
    inputs = B.expected_inputs(ledger, 11)
    assert inputs["current_perf"]["throughput_tps"] == 100.
    assert _events(result, "endpoint-fixed")[0]["endpoint"]["fitness_tps"] == 100.
    for event in result["events"]:
        if "tier0" in event:
            assert set(event["tier0"]) == {"status", "reason", "sidecar_sha256"}
    text = json.dumps([result["events"], inputs])
    assert "987654321" not in text and "123456789" not in text
    assert '"smoke"' not in text and '"throughput_positive"' not in text
    for path in (tmp_path / "ledger/handshake").glob("slot-*.json"):
        assert set(json.loads(path.read_text())["tier0"]) == {"status", "reason", "sidecar_sha256"}


def test_llm_tier0_rejection_preserves_expected_inputs(tmp_path):
    ledger = _input_ledger(tmp_path)
    before = B.expected_inputs(ledger, 3)
    sidecar = tmp_path / "rejection"
    root = _write_attempt(sidecar, outcome="rejected-tier0")
    observed = B.classify_slot(sidecar, root, 5, _genome(20))
    ledger.append("proposal-rejected", a=3, b=2, **observed)
    assert observed["outcome"] == "rejected-tier0"
    assert B.expected_inputs(ledger, 3) == before


def test_header_declares_shared_tier0_contract():
    h = B._header("random", "write-heavy", 1, 1, ROOT)
    assert h["tier0_status"] == "implemented"
    assert h["tier0_contract"] == L.B5_TIER0_CONTRACT
    assert h["tier0_contract"]["contract_id"] == "b5-tier0/v1"
    assert h["tier0_contract"]["applies_to"] == ["search", "score"]
    assert h["tier0_contract"]["timeout_s"] == 32
    assert h["tier0_contract"]["build"]["trace"] is False


def test_registered_header_consumed_by_existing_report(tmp_path, monkeypatch):
    from orchestrator.campaign import b5_generator_contrast_report as report
    # Actual producer -> on-disk ledger -> unchanged consumer. Expiry avoids
    # external evaluation, leaving a valid, explicitly missing series.
    monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "0")
    result = _series(tmp_path, FakeRunner(), purpose="registered")
    assert result["events"][-1]["reason"] == "allocation-exhausted"
    consumed = report.build_report([tmp_path / "ledger"], purpose="registered")
    assert consumed["invalid"] == []
    assert consumed["purpose"] == "registered"
    assert consumed["registered_judgment"] == "see-comparisons"
    assert len(consumed["series"]) == 1
    assert len(consumed["comparisons"]) == 6
    assert {c["judgment"] for c in consumed["comparisons"]} == {"indeterminate-missing"}
    wrong_purpose = report.build_report([tmp_path / "ledger"], purpose="pilot")
    assert [(i["category"], i["detail"]) for i in wrong_purpose["invalid"]] == [
        ("schema-inconsistent", "header contract")]
    assert wrong_purpose["registered_judgment"] == "not-applicable-pilot"
    assert "comparisons" not in wrong_purpose


@pytest.mark.parametrize("purpose,cohort", [("pilot", "t2797-beta-v1"), ("registered", "b5-registered-v1")])
def test_purpose_cohort_mapping(purpose, cohort):
    h = B._header("random", "balanced", 6, 2, ROOT, purpose=purpose)
    assert (h["purpose"], h["cohort"]) == (purpose, cohort)


def test_pilot_header_bytes_unchanged(tmp_path, monkeypatch):
    # Frozen Git HEAD, host, job and deadline; expected dictionary is the
    # pre-change header, not a second call through the changed producer.
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".git/HEAD").write_text("a" * 40 + "\n")
    monkeypatch.setattr(B.socket, "gethostname", lambda: "fixed-host")
    monkeypatch.setenv("PBS_JOBID", "fixed-job")
    monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "1234567890")
    expected = {
        "schema": "b5-generator-contrast-ledger/v1",
        "cohort": "t2797-beta-v1", "purpose": "pilot", "arm": "random", "workload": "write-heavy",
        "series": 1, "block": 1, "repo_head": "a" * 40, "pin": L.PIN,
        "mode": "series", "perf_config": asdict(L.calibrated_perf("write-heavy")),
        "verify_mode": "legacy+performance", "bench_max_rounds": 3,
        "B": 10, "A": 30, "N_eval": 5,
        "tier0_status": "implemented", "tier0_contract": L.B5_TIER0_CONTRACT,
        "job": {"PBS_JOBID": "fixed-job", "host": "fixed-host"},
        "allocation_deadline_epoch": 1234567890.0, "allocation_deadline_status": "known",
        "limits": ["Parent intervention and actual input delivery are not mechanically guaranteed.",
                   "Pilot only; does not establish preregistration section 10 completeness."],
    }
    expected_bytes = (json.dumps(expected, sort_keys=True, ensure_ascii=True, allow_nan=False,
                                 separators=(",", ":")) + "\n").encode("ascii")
    for kwargs in ({}, {"purpose": "pilot"}):
        actual = B._header("random", "write-heavy", 1, 1, repo, **kwargs)
        assert B._json_bytes({**actual, "schema": B.LEDGER_SCHEMA}) == expected_bytes


def test_registered_block_stock_header(tmp_path, monkeypatch):
    from orchestrator.campaign import b5_generator_contrast_report as report
    monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "0")
    result = B.run_block_stock("read-heavy", 3, ledger_root=tmp_path / "stock",
                               prebuild_receipt=tmp_path / "receipt", repo_root=ROOT,
                               runner=FakeRunner(), purpose="registered")
    h = result["header"]
    assert (h["purpose"], h["cohort"], h["series"], h["block"], h["mode"]) == (
        "registered", "b5-registered-v1", 3, 3, "block-stock")
    assert report.build_report([tmp_path / "stock"], purpose="registered")["invalid"] == []


def test_registered_producer_leaves_allocation_validation_to_report(tmp_path, monkeypatch):
    from orchestrator.campaign import b5_generator_contrast_report as report
    monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "0")
    B.run_series("random", "balanced", 12, 1, ledger_root=tmp_path / "ledger",
                 prebuild_receipt=tmp_path / "receipt", repo_root=ROOT,
                 runner=FakeRunner(), purpose="registered")
    consumed = report.build_report([tmp_path / "ledger"], purpose="registered")
    assert [(i["category"], i["detail"]) for i in consumed["invalid"]] == [
        ("schema-inconsistent", "allocation mismatch")]


@pytest.mark.parametrize("command", ["run-series", "run-block-stock"])
@pytest.mark.parametrize("purpose", [None, "pilot", "registered"])
def test_purpose_cli_reaches_real_producer(tmp_path, monkeypatch, command, purpose):
    monkeypatch.setenv("IZANAGI_RESERVATION_DEADLINE_EPOCH", "0")
    argv = [command, "--workload", "balanced", "--block", "2", "--ledger-root", str(tmp_path / "ledger"),
            "--fetchcontent-prebuild-receipt", str(tmp_path / "receipt")]
    if command == "run-series":
        argv += ["--arm", "random", "--series", "5"]
    if purpose is not None:
        argv += ["--purpose", purpose]
    assert B.main(argv) == 1
    h = B.SeriesLedger(tmp_path / "ledger").header
    assert h["purpose"] == (purpose or "pilot")
    assert h["cohort"] == ("b5-registered-v1" if purpose == "registered" else "t2797-beta-v1")


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
