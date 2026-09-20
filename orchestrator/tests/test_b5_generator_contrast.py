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


def test_series_scores_fresh_sessions_after_endpoint_fix(tmp_path):
    def before(call, directory):
        if call["kind"] == "score":
            ledger = B.SeriesLedger(directory.parents[1])
            assert ledger.events[-1]["kind"] in {"endpoint-fixed", "score-session"}
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
    assert result["header"]["tier0_status"] == "not-implemented"


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


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
