import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from orchestrator.tests.test_p3_s4_loop_job_contract import (
    JOB, _run_actual_job_body_through_driver, _read_driver_environment,
    _run_actual_job_to_k2_preflight,
)


def environment(tmp_path, mode="series"):
    fields = {"MODE": mode, "COHORT": "cohort with spaces", "COHORT_ROOT": str(tmp_path / "cohort dir"),
              "WORKLOAD": "balanced", "BLOCK": "2", "N_EVAL": "3"}
    fields.update({"ARM": "llm", "SERIES": "4", "A_LIMIT": "12", "B_LIMIT": "6"}
                  if mode == "series" else {"BLOCK_STOCK_SESSIONS": "5"})
    return {"IZANAGI_S4_T2849_" + k: v for k, v in fields.items()}


def test_harness_bench_lock(tmp_path):
    _run_actual_job_body_through_driver(tmp_path, environment(tmp_path))
    scratch = tmp_path / "scratch-base/0_945411.nqsv"
    assert _read_driver_environment(tmp_path) == [{"TMPDIR": str(scratch), "IZANAGI_BENCH_LOCK": str(scratch / "bench.lock")}]


@pytest.mark.parametrize("mode", ["series", "block-controls"])
@pytest.mark.parametrize("driver_rc", [0, 7])
def test_harness_single_driver(tmp_path, mode, driver_rc):
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path, environment(tmp_path, mode), driver_rcs=(driver_rc, 99))
    expected = ["-B", "-m", "orchestrator.campaign.t2849_comparison_harness", "run-" + mode,
                "--cohort", "cohort with spaces", "--cohort-root", str(tmp_path / "cohort dir"),
                "--workload", "balanced", "--block", "2", "--n-eval", "3",
                "--fetchcontent-prebuild-receipt", str(tmp_path / "evidence/masstree-prebuild-receipt.json")]
    expected += (["--arm", "llm", "--series", "4", "--a-limit", "12", "--b-limit", "6"]
                 if mode == "series" else ["--block-stock-sessions", "5"])
    assert history == [expected]
    assert rc == result["driver_rc"] == driver_rc


def test_mocc_protocol_env_only_changes_mocc_driver_argv(tmp_path):
    baseline, _, _ = _run_actual_job_body_through_driver(tmp_path / "silo", environment(tmp_path / "silo"))
    env = environment(tmp_path / "mocc")
    env["IZANAGI_S4_T2849_PROTOCOL"] = "mocc"
    mocc, _, _ = _run_actual_job_body_through_driver(tmp_path / "mocc", env)
    assert "--protocol" not in baseline[0]
    assert mocc[0][-2:] == ["--protocol", "mocc"] or mocc[0][mocc[0].index("--protocol"):] == [
        "--protocol", "mocc", "--arm", "llm", "--series", "4", "--a-limit", "12", "--b-limit", "6"]


@pytest.mark.parametrize("key,value", [("IZANAGI_S4_B5_MODE", "series"),
    ("IZANAGI_S4_PROPOSAL_PATH", "/proposal.json"), ("IZANAGI_S4_FIXTURE_VALUE", "20"),
    ("IZANAGI_S4_STOCK_CONTROL", "1"), ("IZANAGI_S4_KNOWLEDGE_MANIFEST", "/knowledge.json")])
def test_exclusive_before_prebuild(tmp_path, key, value):
    env = environment(tmp_path)
    env[key] = value
    completed, evidence, sentinels = _run_actual_job_to_k2_preflight(tmp_path, env)
    assert completed.returncode == 2
    assert "T-2849" in completed.stderr
    assert not any(p.exists() for p in sentinels)
    assert not list(evidence.iterdir())


@pytest.mark.parametrize("mode", ["", "other"])
def test_invalid_mode(tmp_path, mode):
    env = environment(tmp_path)
    env["IZANAGI_S4_T2849_MODE"] = mode
    completed, _, _ = _run_actual_job_to_k2_preflight(tmp_path, env)
    assert completed.returncode == 2


def test_partial_environment(tmp_path):
    completed, _, _ = _run_actual_job_to_k2_preflight(tmp_path, {"IZANAGI_S4_T2849_ARM": "llm"})
    assert completed.returncode == 2


def test_prebuild_precedes_harness():
    body = JOB.read_text()
    driver = '"$PY" -B -m orchestrator.campaign.t2849_comparison_harness'
    assert body.count(driver) == 1
    assert body.index('sync "$prebuild_receipt"') < body.index(driver)


def _run():
    from tools.run_tests import main
    return main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
