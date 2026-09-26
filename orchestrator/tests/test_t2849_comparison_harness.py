"""Harness tests at the physical runner seam, with real sidecar/WAL readers."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import t2849_comparison_harness as H
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign.model import WalRecord
from orchestrator.campaign.pipeline import variant_id
from tools import t2849_llm_round as T

ROOT = Path(__file__).resolve().parents[2]

def _bench(**changes):
    return {"tps": [100.] * 5, "median_tps": 100., "settled": True, "unstable": False, **changes}

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
                   outcome="certified", bench=None, abort_reason="build-error", src=None, genome=None):
    """Synthetic producer bytes at the subprocess boundary, never a WAL reader stub."""
    sidecar = Path(sidecar)
    root = sidecar / "campaign"
    (root / "runs").mkdir(parents=True)
    genome = genome or H._genome(value)
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
    if genome.flags.get("BACKOFF_FIXED", -1) != -1 and outcome != "rejected-preprocess":
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


class Runner:
    def __init__(self, outcomes=None):
        self.calls = []
        self.outcomes = outcomes or {}

    def __call__(self, argv, *, cwd):
        self.calls.append(argv)
        key = argv[argv.index("--b5-slot")+1]
        fields = key.split("|")
        kind, n, attempt = fields[5], int(fields[6]), int(fields[7].split("-")[-1])
        sidecar = Path(argv[argv.index("--b5-sidecar-dir")+1])
        value = -1
        if "--run-iteration" in argv:
            value = json.loads(Path(argv[argv.index("--run-iteration")+1]).read_bytes())["coder"]["value"]
        genome = (H.reference_genome(fields[3]) if "--reference-genome" in argv else
                  H._genome(value, "mocc") if "--protocol" in argv else None)
        defaults = {"bench": _bench(tps=[50.]*5, median_tps=50.)} if kind == "search" else {}
        changes = self.outcomes.get((kind, n, attempt), self.outcomes.get(kind, defaults))
        _write_attempt(sidecar, key=key, value=value, genome=genome, **changes)
        return subprocess.CompletedProcess(argv, 0, "", "")


def run(tmp_path, arm="random", runner=None, **changes):
    options = dict(cohort="unit", cohort_root=tmp_path, a_limit=2, b_limit=2, n_eval=1,
                   prebuild_receipt=tmp_path / "receipt", repo_root=ROOT, runner=runner or Runner())
    options.update(changes)
    return H.run_series(arm, "balanced", 1, 1, **options)


def events(result, kind):
    return [e for e in result["events"] if e["kind"] == kind]


def test_initial_outside_b(tmp_path):
    result = run(tmp_path)
    initial = [e for e in events(result, "evaluation-result") if e["slot_kind"] == "initial"]
    assert [e["value"] for e in initial] == [5, 10]
    assert [(e["a"], e["b"], e["whiteboard_entry"]) for e in initial] == [(0, 0, None)]*2
    assert result["events"][-1]["b"] == 2


def test_retry_counts_b_once(tmp_path):
    runner = Runner({("search", 1, 0): {"outcome": "abort", "abort_reason": "bench-probe-error"}})
    result = run(tmp_path, runner=runner, a_limit=1, b_limit=1)
    assert result["events"][-1]["b"] == 1
    retry = events(result, "machine-retry")[0]
    evaluated = [e for e in events(result, "evaluation-result") if e["slot_kind"] == "search"][0]
    assert retry["proposal_sha256"] == evaluated["proposal_sha256"]
    assert retry["slot_key"] != evaluated["slot_key"]
    assert len(runner.calls) == 6


def test_initial_can_be_endpoint(tmp_path):
    runner = Runner({"search": {"bench": _bench(tps=[50.]*5, median_tps=50.)}})
    result = run(tmp_path, runner=runner)
    endpoint = events(result, "endpoint-fixed")[0]["endpoint"]
    assert endpoint["slot_kind"] == "initial" and endpoint["value"] == 5


def test_n_eval_independent_of_reps(tmp_path):
    result = run(tmp_path, n_eval=2)
    assert len(events(result, "score-session")) == 2
    assert result["events"][-1]["score"] == 100
    assert result["header"]["session_reps"] == 5


def test_llm_slot_argv_k0():
    options = dict(arm="llm", workload="balanced", key="t2849-harness-v1|fixture",
                   sidecar_dir="sidecar", prebuild_receipt="receipt", proposal_path="proposal")
    argv = H.slot_argv(**options)
    assert "--allow-coder-derived-build" in argv and "--machine-generated-proposal" not in argv
    assert "--coder-role" not in argv and "--knowledge-manifest" not in argv
    initial_score = H.slot_argv(**options, proposal_origin="machine")
    assert "--machine-generated-proposal" in initial_score
    assert "--allow-coder-derived-build" not in initial_score


def test_mocc_slot_argv_and_classification(tmp_path):
    runner = Runner()
    result = run(tmp_path, runner=runner, protocol="mocc", a_limit=1, b_limit=1)
    assert result["header"]["protocol"] == "mocc"
    assert all(argv[-2:] == ["--protocol", "mocc"] or
               argv[argv.index("--protocol"):] == ["--protocol", "mocc", "--machine-generated-proposal"]
               for argv in runner.calls)
    assert result["events"][-1]["reason"] == "b-complete"
    assert any(e["outcome"] == "certified" for e in events(result, "evaluation-result"))


def test_mocc_stock_established_only_for_mocc_variant():
    observation = {"outcome": "certified", "quality": "normal", "src_token": "stock",
                   "variant": variant_id(H._genome(-1, "mocc")), "fitness_tps": 100.}
    assert H._stock_established(observation, "mocc")
    assert not H._stock_established(observation, "silo")
    observation["variant"] = variant_id(H._genome(-1, "silo"))
    assert not H._stock_established(observation, "mocc")


def test_mocc_k0_header_request_context_proposal_and_classified_slot(tmp_path, monkeypatch):
    original_publish = H._publish
    contexts = []
    def publish(path, value, **kwargs):
        original_publish(path, value, **kwargs)
        if not path.name.startswith("request-"):
            return
        assert value["protocol"] == "mocc"
        a = value["a"]
        materials = tmp_path / "materials"
        (materials / "verbatim").mkdir(parents=True, exist_ok=True)
        tool = T.RoundTool(path.parent.parent, materials)
        assert tool.header["protocol"] == "mocc"
        tool.cmd_inputs(a)
        context = T.load(tool.directory(a) / "coder-input-skeleton.json")["leakproof_context"]
        contexts.append(context)
        assert "BACK_OFF=1、KEY_SORT=0、TEMPERATURE_RESET_OPT=1" in context
        assert "NO_WAIT_LOCKING_IN_VALIDATION=1" not in context
        doc = H.machine_proposal_document("llm", 12, {})
        doc["planner"]["uncertainty"] = "observed noise"
        T.dump(materials / "verbatim" / f"planner-{a}.json", {"proposal": doc["planner"]})
        tool.cmd_coder(a)
        T.dump(materials / "verbatim" / f"coder-{a}.json", {"proposal": doc["coder"]})
        tool.cmd_proposal(a)
    monkeypatch.setattr(H, "_publish", publish)
    runner = Runner()
    result = run(tmp_path, arm="llm", runner=runner, protocol="mocc", a_limit=1, b_limit=1)
    assert contexts
    assert result["events"][-1]["reason"] == "b-complete"
    assert any(e["slot_kind"] == "search" and e["outcome"] == "certified"
               for e in events(result, "evaluation-result"))
    assert all("--protocol" in argv for argv in runner.calls)


def test_k0_uses_latest_normal(tmp_path):
    runner = Runner({("initial", 1, 0): {"bench": _bench(tps=[300.]*5, median_tps=300.)},
                     "search": {"outcome": "rejected-tier0"}})
    run(tmp_path, runner=runner)
    expected = H.expected_inputs(tmp_path / "balanced/random/series-1", 1)
    assert expected["current_perf"]["throughput_tps"] == 100
    assert "|initial|2|" in expected["current_perf_source"]["slot_key"]
    assert expected["expected_whiteboard"] == []
    assert expected["t2849_prior_observations"]["rejected_opportunities"] == [
        {"a": 1, "reject_class": "tier0"}, {"a": 2, "reject_class": "tier0"}]


def test_rejection_does_not_advance_whiteboard(tmp_path):
    run(tmp_path, runner=Runner({("search", 1, 0): {"outcome": "rejected-tier0"}}))
    expected = H.expected_inputs(tmp_path / "balanced/random/series-1", 2)
    assert len(expected["expected_whiteboard"]) == 1
    assert expected["expected_whiteboard"][0]["iteration"] == 1
    with pytest.raises(ValueError):
        H.expected_inputs(tmp_path / "balanced/random/series-1", 3)


def test_role_costs_recorded(tmp_path, monkeypatch):
    # Publish in response to the real request; leave handshake and validators intact.
    published = H._publish
    costs = {"role_calls": [{"role": "planner", "count": 1, "wall_s": 2, "reported_tokens": None}],
             "human_interventions": []}
    def publish(path, value, **kwargs):
        published(path, value, **kwargs)
        if path.name.startswith("request-"):
            a = value["a"]
            d = path.parent
            published(d / f"role-costs-{a}.json", costs)
            if a == 1:
                published(d / f"proposal-{a}.rejected.json", {"reason": "role output invalid"})
            else:
                planner = {"whiteboard": value["expected_whiteboard"], "current_perf": value["current_perf"],
                           "t2849_prior_observations": value["t2849_prior_observations"]}
                coder = {"whiteboard": value["expected_whiteboard"], "baseline": value["baseline"],
                         "t2849_prior_observations": value["t2849_prior_observations"]}
                published(d / f"inputs-{a}.json", {"planner_input": planner, "coder_input": coder})
                published(d / f"proposal-{a}.json", H.machine_proposal_document("llm", 50, {}))
    monkeypatch.setattr(H, "_publish", publish)
    result = run(tmp_path, arm="llm", b_limit=1)
    consumed = [e for e in result["events"] if e["kind"] == "proposal-rejected"
                or (e["kind"] == "evaluation-result" and e["slot_kind"] == "search")]
    assert len(consumed) == 2
    for e in consumed:
        assert e["provenance"]["role_calls"] == costs["role_calls"]
        assert e["provenance"]["human_interventions"] == []
    assert result["events"][-1]["b"] == 1


@pytest.mark.parametrize("workload", H.B.WORKLOADS)
def test_reference_exact_genome_and_real_wal(tmp_path, workload):
    genome = H.reference_genome(workload)
    assert genome.flags == {"BACK_OFF": 0, "NO_WAIT_LOCKING_IN_VALIDATION": int(workload != "read-heavy"),
                            "NO_WAIT_OF_TICTOC": int(workload == "read-heavy"), "WAL": 0}
    root = _write_attempt(tmp_path, value=-1, genome=genome)
    assert not (tmp_path / "tier0.json").exists()
    assert H.classify_reference_slot(tmp_path, root, 5, genome)["outcome"] == "certified"


def test_reference_genome_mismatch_not_certified(tmp_path):
    genome = H.reference_genome("read-heavy")
    root = _write_attempt(tmp_path, value=-1, genome=genome)
    assert H.classify_reference_slot(tmp_path, root, 5, H.reference_genome("balanced"))["outcome"] != "certified"
    # Isolate the sidecar genome binding: WAL remains a valid reference run.
    for name in ("slot-start.json", "pipeline-submitted.json"):
        path = tmp_path / name
        record = json.loads(path.read_bytes())
        record["genome"] = H.reference_genome("balanced").canonical()
        path.write_text(json.dumps(record))
    assert H.classify_reference_slot(tmp_path, root, 5, genome)["outcome"] != "certified"
    # Isolate the WAL build genome binding: both sidecars and variants match.
    sidecar = tmp_path / "wal-only"
    root = _write_attempt(sidecar, value=-1, genome=genome)
    path = root / "runs/wal.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["payload"]["genome"] = H.reference_genome("balanced").canonical()
    path.write_text("".join(json.dumps(row)+"\n" for row in rows))
    assert H.classify_reference_slot(sidecar, root, 5, genome)["outcome"] != "certified"


@pytest.mark.parametrize("workload", H.B.WORKLOADS)
def test_reference_nonstock_source_not_certified(tmp_path, workload):
    genome = H.reference_genome(workload)
    # Exact genome, complete verify/bench evidence and self-consistent variants.
    root = _write_attempt(tmp_path, value=-1, genome=genome, src="d" * 64)
    assert H.classify_reference_slot(tmp_path, root, 5, genome)["outcome"] != "certified"


@pytest.mark.parametrize("tamper", ["performance", "anomaly", "identity", "terminal"])
def test_reference_incomplete_or_anomalous_not_certified(tmp_path, tamper):
    genome = H.reference_genome("balanced")
    root = _write_attempt(tmp_path, value=-1, genome=genome)
    path = root / "runs/wal.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if tamper == "performance":
        del rows[3]
    elif tamper == "anomaly":
        rows[3]["payload"]["anomalies"] = 1
    elif tamper == "identity":
        rows[0]["payload"]["genome"] = H._genome(-1).canonical()
    else:
        rows.pop()
    path.write_text("".join(json.dumps(row)+"\n" for row in rows))
    assert H.classify_reference_slot(tmp_path, root, 5, genome)["outcome"] != "certified"


@pytest.mark.parametrize("arm", ["random", "sweep", "bo", "evolution"])
def test_machine_arms_fresh_slots(tmp_path, arm):
    runner = Runner()
    result = run(tmp_path, arm=arm, runner=runner)
    keys = [argv[argv.index("--b5-slot")+1] for argv in runner.calls]
    assert len(keys) == len(set(keys)) == 6
    assert result["events"][-1]["b"] == 2
    with pytest.raises(FileExistsError):
        run(tmp_path, arm=arm)


@pytest.mark.parametrize("outcomes,reason", [
    ({"initial": {"outcome": "anomaly"}, "search": {"outcome": "rejected-tier0"}}, "a-exhausted"),
    ({"initial": {"bench": _bench(unstable=True)}, "search": {"bench": _bench(unstable=True)}}, "unclassified-missing"),
    ({"search": {"outcome": "abort", "abort_reason": "bench-probe-error"}}, "unclassified-missing")])
def test_failure_endings(tmp_path, outcomes, reason):
    result = run(tmp_path, runner=Runner(outcomes))
    assert result["events"][-1]["reason"] == reason
    assert result["events"][-1]["score"] is None


def test_derived_ledger_paths_and_cli_rejects_override(tmp_path):
    with pytest.raises(SystemExit):
        H.main(["run-series", "--ledger-root", str(tmp_path)])
    run(tmp_path)
    assert (tmp_path / "balanced/random/series-1/header.json").exists()


def test_inheritance_exact_prior_and_diagnosis(tmp_path):
    run(tmp_path, a_limit=1, b_limit=1)
    path = tmp_path / "balanced/random/series-1"
    expected = H.expected_inputs(path, 2)
    diagnosis = L.k2_critic_diagnosis_from_bytes(
        b"## attribution\nobservation\n## recommend\ntry\n## avoid\nunknown\n## uncertainty\nnoise\n")
    planner = {"whiteboard": expected["expected_whiteboard"], "current_perf": expected["current_perf"],
               "t2849_prior_observations": expected["t2849_prior_observations"], "k2_critic_diagnosis": diagnosis}
    coder = {"whiteboard": expected["expected_whiteboard"], "baseline": expected["baseline"],
             "t2849_prior_observations": expected["t2849_prior_observations"], "k2_critic_diagnosis": diagnosis}
    H.assert_inherited_inputs(path, planner, coder, next_evaluation=2)
    for key in coder:
        with pytest.raises(ValueError):
            H.assert_inherited_inputs(path, planner, {k: v for k, v in coder.items() if k != key}, next_evaluation=2)


def test_grid_exhaustion_and_all_arm_a_cap(tmp_path):
    result = run(tmp_path, arm="sweep", a_limit=100, b_limit=100,
                 runner=Runner({"search": {"outcome": "rejected-tier0"}}))
    assert result["events"][-1]["reason"] == "grid-exhausted"
    assert result["events"][-1]["a"] == 26 and result["events"][-1]["b"] == 0


def test_sweep_initial_order_in_generator_wall(tmp_path, monkeypatch):
    now, calls = [0.], []
    order = H.G.sweep_order
    def timed_order(*args):
        calls.append(args)
        result = order(*args)
        now[0] += 7.
        return result
    monkeypatch.setattr(H.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(H.G, "sweep_order", timed_order)
    result = run(tmp_path, arm="sweep")
    search = [e for e in events(result, "evaluation-result") if e["slot_kind"] == "search"]
    assert calls == [("balanced", 1)]
    assert [e["timing"]["generator_wall_s"] for e in search] == [7., 0.]
    ledger = H.SeriesLedger(tmp_path / "balanced/sweep/series-1")
    assert H._costs(ledger)["generator_wall_s"] == 7.


def test_initial_machine_failure_ends_before_search(tmp_path):
    result = run(tmp_path, runner=Runner({"initial": {"outcome": "abort", "abort_reason": "bench-probe-error"}}))
    assert result["events"][-1]["reason"] == "unclassified-missing"
    assert not events(result, "proposal-opportunity") and not events(result, "endpoint-fixed")
    assert len(events(result, "machine-retry")) == 2


def test_allocation_exhaustion_records_initial_without_tell_crash(tmp_path, monkeypatch):
    runner = Runner()
    def finish_stock(argv, *, cwd):
        result = runner(argv, cwd=cwd)
        monkeypatch.setattr(H, "_allocation_available", lambda: False)
        return result
    result = run(tmp_path, arm="bo", runner=finish_stock)
    assert result["events"][-1]["reason"] == "allocation-exhausted"
    assert len(runner.calls) == 1


def test_ledger_immutable_and_reconstructable(tmp_path):
    result = run(tmp_path)
    root = tmp_path / "balanced/random/series-1"
    assert H.SeriesLedger(root).view() == result
    with pytest.raises(ValueError):
        H.SeriesLedger(root).append("proposal-opportunity", a=3)
    path = next((root / "events").glob("*.json"))
    with pytest.raises(FileExistsError):
        H._publish(path, {})


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
