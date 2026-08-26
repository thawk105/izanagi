from __future__ import annotations

import hashlib
import random
from pathlib import Path
from types import SimpleNamespace

from orchestrator.campaign import (
    backoff_extended_sweep as M,
    backoff_overthrottle as O,
    env_contract,
    p2_2,
    site_policy,
)


def test_mu1_extended_grid_semantic_golden_except_registered_upper_endpoint():
    assert tuple(M.EXTENDED_SWEEP_US[:-1]) == (
        1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 100,
        150, 250, 400, 560, 680,
    )


def test_mu2_grid_upper_endpoint_matches_adaptive_range():
    assert M.EXTENDED_SWEEP_US[-1] == 1000


def test_mu4_workload_literal_oracle_reaches_config_diagnostic_and_argv():
    oracle = {
        "write-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "5", "ycsb_rmw": "0"},
        "balanced": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
        "read-heavy": {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
    }
    contract = SimpleNamespace(clocks_per_us=2100)
    assert M.WORKLOAD_BY_TAG == oracle
    for tag, workload in oracle.items():
        assert M.config_for(tag, workload).search_config["ycsb"] == workload
        argv = O._flags(workload, contract)
        assert f"-ycsb_rratio={workload['ycsb_rratio']}" in argv


def test_mu11_measurement_order_is_the_registered_seeded_permutation():
    seeds = {
        "write-heavy": 0xB10005,
        "balanced": 0xB10050,
        "read-heavy": 0xB10095,
    }
    labels = ["none", "adaptive", *[f"fixed-{amount}us" for amount in M.EXTENDED_SWEEP_US]]
    for tag, seed in seeds.items():
        expected = list(labels)
        random.Random(seed).shuffle(expected)
        assert M.measurement_order(tag) == expected
        assert M.config_for(tag, M.WORKLOAD_BY_TAG[tag]).search_config["measurement_order"] == expected
        assert expected != labels


def test_mu13_run_path_uses_the_calibration_bound_records(monkeypatch):
    contract = p2_2._legacy_linux_contract()
    authorization = env_contract.authorize(contract.env_tag)
    observed = {}
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        M.p2_2,
        "resolve_site_runtime",
        lambda: (site_policy.OTHER, contract, authorization),
    )

    def calibration(candidate):
        observed["calibration_contract"] = candidate

    monkeypatch.setattr(M.p2_2, "_assert_matches_calibration", calibration)
    monkeypatch.setattr(M.buildcache, "compilers_for_current_site", lambda: ("cc", "c++"))
    monkeypatch.setattr(M.buildcache, "observed_toolchain_manifest", lambda *_args: {"cc": {}, "cxx": {}})

    def run_campaign(*args, **_kwargs):
        observed["config"] = args[0]
        observed["perf"] = args[2]
        return SimpleNamespace(committed=24, aborted=0, campaign_id="cid")

    monkeypatch.setattr(M, "run_campaign", run_campaign)
    M.run_workload("balanced", M.WORKLOAD_BY_TAG["balanced"], log=lambda *_args: None)
    assert observed["calibration_contract"] is contract
    assert observed["perf"].records == p2_2.RECORDS == 1_000_000
    assert observed["config"].search_config["records"] == 1_000_000
    argv = O._flags(M.WORKLOAD_BY_TAG["balanced"], contract)
    assert "-ycsb_tuple_num=1000000" in argv


def test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    submit = (root / "tools/pegasus/submit_b10_backoff_grid.sh").read_text(encoding="utf-8")
    assert "#PBS -q gen_S" in job
    assert "#PBS -A SFC" in job
    assert "#PBS -b 1" in job
    assert "#PBS -l elapstim_req=04:00:00" in job
    assert "SWEEP_CAP_S=9000" in job
    assert "AA_CAP_S=3000" in job
    assert "REPORT_CAP_S=300" in job
    assert "FINALIZE_CAP_S=300" in job
    assert (
        "EXPECTED_FREEZE_TREES_SHA256="
        "c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3"
    ) in job
    assert "WORKLOADS=(write-heavy balanced read-heavy)" in submit
    assert submit.count("job_id=$(qsub") == 1
    assert "B10_WORKLOAD=$workload" in submit
    assert "QUEUE_STATE=$(qstat -Q)" in submit
    assert "ENABLE(?:D)?" in submit and "ACT|ACTIVE" in submit


def test_b10_freeze_tree_bytes_match_the_wave_local_gate():
    root = Path(__file__).resolve().parents[2]
    digest = hashlib.sha256()
    paths = [
        path
        for relative in ("output/s1-freeze", "output/s8b-freeze")
        for path in (root / relative).rglob("*")
        if path.is_file()
    ]
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    assert digest.hexdigest() == (
        "c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3"
    )
