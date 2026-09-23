"""Fixture-only checks for the frozen transfer analysis."""
import math
import hashlib
import subprocess
from types import SimpleNamespace

import pytest

from orchestrator.campaign.t2851_transfer_analysis import (
    DELTA, analyze, bonferroni_quantile, classify,
)
from orchestrator.campaign import t2851_transfer_runner as runner


def comparison(cell="wh-base", candidate="K", reference="R1", **extra):
    result = dict(protocol="silo", cell=cell, anchor="wh-base", candidate=candidate,
                  reference=reference, kind="primary", series=[["task", "method", "1"]])
    result.update(extra)
    return result


def freeze(*comparisons, workload="ycsb", stage=None, m=100):
    result = dict(workload=workload, m_by_family={stage or "ycsb": m},
                  comparisons=list(comparisons))
    if stage:
        result["stage"] = stage
    return result


def job(cell="wh-base", cohort=1, ratios=None, *, candidate="K", reference="R1",
        attempt=1, complete=32, separate=True, solo=True, stage=None):
    if ratios is None:
        ratios = [math.exp(0.10)] * 32
    blocks = [dict(block=i + 1, runs={candidate: {"tps": ratio * 100 if ratio is not None else None},
                                      reference: {"tps": 100}}) for i, ratio in enumerate(ratios)]
    return dict(stage=stage, cohort=cohort, protocol="silo", cell=cell, attempt=attempt,
                isolation_start=solo, isolation_end=solo, completed_blocks=complete,
                within_retry_limit=True, separate_allocation=separate, blocks=blocks)


def certified(*cells, candidate="K", reference="R1", stage=None):
    return [dict(stage=stage, protocol="silo", cell=cell, identity=identity,
                 status="certified") for cell in cells for identity in (candidate, reference)]


def run_one(ratios=None, *, m=100, jobs=None, verifications=None):
    return analyze(freeze(comparison(), m=m),
                   jobs if jobs is not None else [job(ratios=ratios), job(cohort=2, ratios=ratios)],
                   verifications if verifications is not None else certified("wh-base"))["primary_rows"][0]


def test_quantiles_and_strict_classification_boundaries():
    assert bonferroni_quantile(1) == pytest.approx(2.0395, abs=0.0002)
    assert bonferroni_quantile(100) == pytest.approx(3.887, abs=0.003)
    assert classify(DELTA, DELTA + 0.01) == "undetermined"
    assert classify(math.nextafter(DELTA, math.inf), DELTA + 0.01) == "superior"
    assert classify(-0.1, -DELTA) == "undetermined"
    assert classify(-0.1, math.nextafter(-DELTA, -math.inf)) == "regression"
    assert classify(-DELTA, DELTA / 2) == "undetermined"
    assert classify(math.nextafter(-DELTA, math.inf), math.nextafter(DELTA, -math.inf)) == "equivalent"
    assert classify(-DELTA / 2, DELTA) == "undetermined"


def test_bonferroni_m_is_frozen_and_changes_interval():
    logs = [0.04 + (i % 2) * 0.04 for i in range(32)]
    ratios = [math.exp(x) for x in logs]
    wide = run_one(ratios, m=100)
    narrow = run_one(ratios, m=1)
    assert wide["cohorts"][1]["upper"] - wide["cohorts"][1]["lower"] > (
        narrow["cohorts"][1]["upper"] - narrow["cohorts"][1]["lower"])
    missing = run_one(ratios, m=100, jobs=[job(ratios=ratios)])
    assert missing["cohorts"][1]["upper"] == pytest.approx(wide["cohorts"][1]["upper"])
    assert missing["primary_result"] is None


@pytest.mark.parametrize("n", [0, 1, 31, 32])
def test_effective_block_boundaries(n):
    ratios = [math.exp(0.1)] * n + [None] * (32 - n)
    result = run_one(ratios)
    side = result["cohorts"][1]
    assert side["n_eff"] == n
    assert side["qualified"] is (n == 32)
    assert side["mean_log_ratio"] == (pytest.approx(0.1) if n else None)
    if n == 0:
        assert side["lower"] is None
    elif n == 1:
        assert side["upper"] is None
    else:
        assert side["lower"] is not None
    if n < 32:
        assert side["classification"] == "undetermined"
        assert side["interval"] == "descriptive"


def test_adopt_first_valid_attempt_and_cohort_two_allocation():
    jobs = [job(ratios=[math.exp(-0.2)] * 32, solo=False, attempt=1),
            job(ratios=[math.exp(0.1)] * 32, attempt=2), job(cohort=2, separate=False)]
    result = run_one(jobs=jobs)
    assert result["cohorts"][1]["adopted_attempt"] == 2
    assert result["cohorts"][1]["classification"] == "superior"
    assert result["cohorts"][2]["qualified"] is False
    assert result["primary_result"] is None
    assert run_one(jobs=[job(complete=31), job(cohort=2)])["cohorts"][1]["qualified"] is False


def test_rejected_attempt_remains_descriptive_even_after_valid_retry():
    failed = job(ratios=[math.exp(-0.2)] * 32, solo=False, attempt=1)
    accepted = job(ratios=[math.exp(0.1)] * 32, attempt=2)
    result = analyze(freeze(comparison()), [failed, accepted, job(cohort=2)],
                     certified("wh-base"))
    assert result["primary_rows"][0]["cohorts"][1]["adopted_attempt"] == 2
    rejected = [r for r in result["descriptive_rows"] if r.get("attempt_only")]
    assert len(rejected) == 1
    assert rejected[0]["mean_log_ratio"] == pytest.approx(-0.2)


def test_disqualification_excludes_all_cells_both_cohorts_and_preserves_m():
    comps = [comparison("wh-base"), comparison("wh-skew09")]
    jobs = [job(cell=cell, cohort=cohort) for cell in ("wh-base", "wh-skew09")
            for cohort in (1, 2)]
    verifications = certified("wh-base", "wh-skew09")
    verifications.append(dict(stage=None, protocol="silo", cell="wh-skew09",
                              identity="K", status="disqualified", attempt=2))
    result = analyze(freeze(*comps, m=100), jobs, verifications)
    assert result["m_by_family"]["ycsb"] == 100
    assert len(result["primary_rows"]) == 2
    assert all(r["claim_excluded"] for r in result["primary_rows"])
    assert all(not side["qualified"] for r in result["primary_rows"]
               for side in r["cohorts"].values())
    assert all(r["primary_result"] is None for r in result["primary_rows"])


def test_reference_disqualification_excludes_its_comparisons():
    verifications = certified("wh-base")
    verifications.append(dict(stage=None, protocol="silo", cell="wh-base", identity="R1",
                              status="disqualified", attempt=2))
    result = run_one(verifications=verifications)
    assert result["claim_excluded"] is True
    assert all(not r["qualified"] for r in result["cohorts"].values())
    assert result["cohorts"][1]["mean_log_ratio"] == pytest.approx(0.1)


def test_indeterminate_verification_is_descriptive_only():
    result = run_one(verifications=[dict(stage=None, protocol="silo", cell="wh-base",
                                           identity="R1", status="certified")])
    assert result["cohorts"][1]["qualified"] is False
    assert result["cohorts"][1]["interval"] == "descriptive"
    assert result["cohorts"][1]["lower"] == pytest.approx(0.1)


def test_same_identity_excluded_even_if_frozen_as_primary():
    result = analyze(freeze(comparison(candidate="R1", reference="R1"),
                            comparison(candidate="K", reference="R1", same_identity=True), m=2),
                     [job(), job(cohort=2)], certified("wh-base"))
    assert result["primary_rows"] == []
    assert result["m_by_family"]["ycsb"] == 2


def test_winner_change_welch_and_independent_stage_family():
    comps = [comparison("wh-base", stage="s1", reference_mode="a"),
             comparison("wh-wh04", stage="s1", reference_mode="a", factor="warehouse", level="wh04")]
    jobs = []
    for cell, center in (("wh-base", 0.12), ("wh-wh04", -0.12)):
        for cohort in (1, 2):
            jobs.append(job(cell, cohort, [math.exp(center + (i % 2) * 0.002)
                                           for i in range(32)], stage="s1"))
    result = analyze(freeze(*comps, workload="tpcc", stage="s1", m=12),
                     jobs, certified("wh-base", "wh-wh04", stage="s1"))
    assert [r["primary_result"] for r in result["primary_rows"]] == ["superior", "regression"]
    assert len(result["winner_changes"]) == 1
    difference = result["winner_changes"][0]["transfer_difference"][1]
    assert difference["difference"] == pytest.approx(-0.24)
    assert difference["lower"] < -0.24 < difference["upper"]
    assert result["m_by_family"] == {"s1": 12}
    assert result["factor_summary"][0]["equal_anchor_mean"] == pytest.approx(-0.119)


def test_descriptive_r0_known_separate_and_uncertain_verification():
    comps = [comparison(reference="R0"), comparison("bal-rmw1"),
             comparison("bal-rmw1", candidate="M", reference="R2", protocol="mocc")]
    jobs = [job(cohort=cohort, reference="R0") for cohort in (1, 2)]
    jobs += [job("bal-rmw1", cohort) for cohort in (1, 2)]
    result = analyze(freeze(*comps), jobs, certified("bal-rmw1"))
    assert len(result["descriptive_rows"]) == 1
    assert len(result["known_separate_rows"]) == 1
    assert len(result["primary_rows"]) == 1  # MOCC bal-rmw1 remains in family
    assert result["descriptive_rows"][0]["cohorts"][1]["interval"] == "descriptive"
    assert result["primary_rows"][0]["cohorts"][1]["qualified"] is False


def test_method_series_include_selection_failures_without_duplicate_measurements():
    first = comparison()
    second = comparison(series=[["task", "method", "2"]])
    frozen = freeze(first, second)
    frozen["series"] = [dict(task="task", method="method", independent_search="1",
                             selected_identity="K"),
                        dict(task="task", method="method", independent_search="2",
                             selected_identity="K"),
                        dict(task="task", method="method", independent_search="3",
                             selection_failure="no candidate")]
    result = analyze(frozen, [job(), job(cohort=2)], certified("wh-base"))
    assert result["method_summary"][0]["series_count"] == 3
    assert result["method_summary"][0]["classification_counts"]["selection_failure"] == 1
    assert result["method_summary"][0]["series_means"] == pytest.approx([0.1, 0.1])


def test_runner_outputs_flow_into_analysis_without_schema_adapter(tmp_path, monkeypatch):
    binary = tmp_path / "binary"
    binary.write_bytes(b"fixture")
    pair = dict(perf_path=str(binary), perf_sha256=hashlib.sha256(b"fixture").hexdigest(),
                trace_path=str(binary), trace_sha256=hashlib.sha256(b"fixture").hexdigest())
    record = dict(workload="ycsb", selection_rule="frozen", binaries={i: dict(pair)
                  for i in ("R0", "R1", "R2", "K")},
                  references={"silo": {a: {"R0": "R0", "R1": "R1", "R2": "R2"}
                                       for a in ("wh-base", "bal-base", "rh-base")}},
                  search_groups=[dict(task="t", method="m", learning_cells=["wh-base"],
                                      independent_searches=["1"], reachability=False)],
                  series=[dict(task="t", method="m", independent_search="1", protocol="silo",
                               anchor="wh-base", selected_identity="K")])
    frozen = runner.freeze_candidates(record)
    monkeypatch.setattr(runner, "_probe", lambda *a, **kw: True)
    def process(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="throughput[tps]:\t100\n", stderr="")
    observed = runner.run_job(dict(freeze=frozen, cohort=1, protocol="silo", cell="wh-base"),
                              subprocess_runner=process)
    def trace(*args, **kwargs):
        return SimpleNamespace(returncode=0, trace_c_lines=0, abort_counts={"abort": 0},
                               commit_count_witness=1, batch_commit_count_witness=0)
    def verifier(*args, **kwargs):
        raise AssertionError("empty trace reached verifier")
    checked = runner.verify_candidate(dict(freeze=frozen, protocol="silo", cell="wh-base",
                                            identity="K"), trace_runner=trace, verifier=verifier)
    result = analyze(frozen, [observed], [checked])
    assert result["m_by_family"] == {"ycsb": 18}
    primary = next(r for r in result["primary_rows"] if r["cell"] == "wh-base"
                   and r["candidate"] == "K" and r["reference"] == "R1")
    assert primary["cohorts"][1]["n_eff"] == 32
    assert primary["cohorts"][1]["adopted_attempt"] == observed["attempt"] == 1
    assert primary["cohorts"][1]["qualified"] is False
    assert primary["primary_result"] is None
    descriptive = next(r for r in result["descriptive_rows"] if r["cell"] == "wh-base"
                       and r["candidate"] == "K" and r["reference"] == "R0")
    assert descriptive["cohorts"][1]["n_eff"] == 32
    assert checked["status"] == "indeterminate" and checked["attempt"] == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
