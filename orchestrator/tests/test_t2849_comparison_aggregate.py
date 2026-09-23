"""Derived reports preserve missingness and propagate workload-local anomalies."""
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.campaign import t2849_comparison_harness as H
from orchestrator.tests.test_t2849_comparison_harness import Runner, ROOT, run, _bench


def controls(root, runner=None, workload="balanced"):
    return H.run_block_controls(workload, 1, cohort="unit", cohort_root=root, n_eval=2,
                               block_stock_sessions=3, prebuild_receipt=root / "receipt",
                               repo_root=ROOT, runner=runner or Runner())


def report(root):
    return H.aggregate(root, {})["series"]


@pytest.mark.parametrize("source", ["initial", "search", "score"])
def test_cross_series_disqualification(tmp_path, source):
    controls(tmp_path)
    run(tmp_path, arm="random")
    # Evolution's deterministic initial best is 5; score observes the same value.
    if source == "search":
        # A separate ledger records a producer-observed anomaly at v=5.
        h = H._header("unit", "llm", "balanced", 2, 1, ROOT, 1, 1, 1)
        l = H.SeriesLedger.create(tmp_path / "balanced/llm/series-2", h)
        l.append("evaluation-result", slot_kind="search", value=5, outcome="anomaly", anomalies=1)
    else:
        run(tmp_path, arm="evolution", runner=Runner({source: {"outcome": "anomaly"}}))
    row = next(r for r in report(tmp_path) if r["arm"] == "random")
    assert row["endpoint"]["value"] == 5
    assert row["status"] == "fallback-disqualified"
    assert row["correction"]["value"] == 5 and row["correction"]["at_utc"]
    # No replacement by the next eligible initial or search point.
    assert row["score"] == row["stock"]


@pytest.mark.parametrize("outcomes,status", [
    ({"initial": {"bench": _bench(unstable=True)}, "search": {"outcome": "rejected-tier0"}}, "quality-missing"),
    ({"initial": {"outcome": "anomaly"}, "search": {"outcome": "rejected-tier0"}}, "fallback-candidate-rejected"),
    ({"search": {"outcome": "abort", "abort_reason": "bench-probe-error"}}, "machine-missing"),
    ({"score": {"outcome": "anomaly"}}, "fallback-score-anomaly"),
    ({"score": {"bench": _bench(unstable=True)}}, "score-missing"),
    ({"stock-start": {"outcome": "anomaly"}}, "stock-unestablished")])
def test_missingness_precedence(tmp_path, outcomes, status):
    controls(tmp_path)
    run(tmp_path, runner=Runner(outcomes))
    row = report(tmp_path)[0]
    assert row["status"] == status
    assert (row["score"] == 100) if status.startswith("fallback") else (row["score"] is None)


def test_reference_missing_not_stock_imputed(tmp_path):
    controls(tmp_path, Runner({"block-reference": {"outcome": "anomaly"}}))
    run(tmp_path)
    row = report(tmp_path)[0]
    assert row["stock_ratio"] == 1
    assert row["reference"] is None and row["reference_ratio"] is None


def test_cross_workload_and_cohort_do_not_contaminate(tmp_path):
    controls(tmp_path)
    run(tmp_path)
    for workload, cohort in [("read-heavy", "unit"), ("balanced", "other")]:
        h = H._header(cohort, "sweep", workload, 2, 1, ROOT, 1, 1, 1)
        l = H.SeriesLedger.create(tmp_path / workload / "sweep/series-2", h)
        l.append("evaluation-result", value=5, anomalies=1, outcome="anomaly")
    result = H.aggregate(tmp_path, {})
    row = next(r for r in result["series"] if r["arm"] == "random")
    assert row["status"] == "scored" and row["correction"] is None
    assert len(result["mismatches"]) == 1


def test_job_cost_deduplicated_initial_retry_and_critic_retained(tmp_path, monkeypatch):
    monkeypatch.setenv("PBS_JOBID", "job-1")
    controls(tmp_path)
    run(tmp_path, runner=Runner({("initial", 1, 0): {"outcome": "abort", "abort_reason": "bench-probe-error"}}))
    run(tmp_path, arm="sweep")
    path = tmp_path / "balanced/random/series-1/handshake/critic-costs-1.json"
    cost = {"role_calls": [{"role": "critic", "count": 1, "wall_s": 3, "reported_tokens": None}],
            "human_interventions": [{"at_utc": "fixture", "action": "restart", "note": "fixture"}]}
    path.write_text(json.dumps(cost))
    result = H.aggregate(tmp_path, {"job-1": {"elapse_s": 123, "queue_wait_s": 30, "source": "scheduler"}})
    assert result["job_elapse_s"] == 123 and len(result["jobs"]) == 1
    row = next(r for r in result["series"] if r["arm"] == "random")
    assert row["costs"]["physical_attempts"] == 7
    assert row["costs"]["role_calls"] == [cost["role_calls"]]
    assert row["costs"]["human_interventions"] == [cost["human_interventions"]]
    assert row["costs"]["generator_wall_s"] >= 0
    assert row["endpoint_is_initial"] is True


def test_block_control_session_counts_and_exact_reference_argv(tmp_path):
    runner = Runner()
    controls(tmp_path, runner)
    assert len(runner.calls) == 5
    reference_calls = [a for a in runner.calls if "--reference-genome" in a]
    assert len(reference_calls) == 2
    for argv in reference_calls:
        assert "--stock-control" in argv and "--machine-generated-proposal" not in argv
    with pytest.raises(FileExistsError):
        controls(tmp_path)


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
