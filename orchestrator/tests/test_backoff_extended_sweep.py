from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import (
    backoff_extended_sweep as M,
    backoff_overthrottle as O,
    build_admission,
    env_contract,
    ident,
    loop,
    p2_2,
    site_policy,
)
from orchestrator.calibrator import perf_preflight


def test_mu1_extended_grid_semantic_golden_except_registered_upper_endpoint():
    adaptive_states_literal = {0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000}
    assert tuple(
        amount for amount in M.EXTENDED_SWEEP_US
        if amount not in adaptive_states_literal
    ) == (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 35, 50, 75, 150, 250, 560)


def test_mu2_grid_upper_endpoint_matches_adaptive_range():
    assert M.EXTENDED_SWEEP_US[-1] == 1000


def test_mu15_all_adaptive_discrete_states_have_independent_literal_coverage():
    adaptive_states_literal = (0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
    assert set(adaptive_states_literal) <= set(M.EXTENDED_SWEEP_US)


def test_fixed_zero_and_none_are_distinct_genomes():
    points = M.genomes("balanced")
    assert len(M.EXTENDED_SWEEP_US) == len(set(M.EXTENDED_SWEEP_US))
    assert len(points) == len(M.EXTENDED_SWEEP_US) + 2
    none = next(genome for genome in points if genome.flags["BACK_OFF"] == 0)
    fixed_zero = next(
        genome for genome in points
        if genome.flags["BACK_OFF"] == 1 and genome.flags["BACKOFF_FIXED"] == 0
    )
    assert none.flags["BACKOFF_FIXED"] == -1
    assert fixed_zero.flags["BACKOFF_FIXED"] == 0
    assert none.canonical() != fixed_zero.canonical()


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
        assert f"-ycsb_zipf_skew={workload['ycsb_zipf_skew']}" in argv
        assert f"-ycsb_rratio={workload['ycsb_rratio']}" in argv
        assert f"-ycsb_rmw={workload['ycsb_rmw']}" in argv


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


def test_measurement_seed_changes_the_real_campaign_id(monkeypatch):
    context = build_admission.build_run_context(
        generator_id=build_admission.GeneratorId.BACKOFF_SWEEP,
    )
    workload = M.WORKLOAD_BY_TAG["balanced"]
    first = ident.bind_admission_policy(M.config_for("balanced", workload), context.policy)
    first_id = ident.campaign_id(first)
    monkeypatch.setitem(M.MEASUREMENT_SEEDS, "balanced", M.MEASUREMENT_SEEDS["balanced"] + 1)
    second = ident.bind_admission_policy(M.config_for("balanced", workload), context.policy)
    second_id = ident.campaign_id(second)
    assert first_id != second_id


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
        observed["cache_root"] = _kwargs["cache_root"]
        return SimpleNamespace(committed=31, aborted=0, campaign_id="cid")

    monkeypatch.setattr(M, "run_campaign", run_campaign)
    M.run_workload(
        "balanced", M.WORKLOAD_BY_TAG["balanced"], log=lambda *_args: None,
        cache_root="/tmp/b10-test-cache",
    )
    assert observed["calibration_contract"] is contract
    assert observed["perf"].records == p2_2.RECORDS == 1_000_000
    assert observed["config"].search_config["records"] == 1_000_000
    assert observed["cache_root"] == "/tmp/b10-test-cache"
    argv = O._flags(M.WORKLOAD_BY_TAG["balanced"], contract)
    assert "-ycsb_tuple_num=1000000" in argv


def test_all_genomes_must_be_committed_and_none_aborted(monkeypatch):
    total = len(M.genomes("balanced"))
    argv = [
        "balanced", "--output-root", "/outside/root",
        "--cache-root", "/tmp/b10-cache",
    ]
    for committed, aborted, expected in (
        (total, 0, 0), (total - 1, 0, 1), (total, 1, 1), (total + 1, 0, 1),
    ):
        monkeypatch.setattr(
            M, "run_workload",
            lambda *_args, _committed=committed, _aborted=aborted, **_kwargs:
                SimpleNamespace(
                    committed=_committed, aborted=_aborted, campaign_id="cid",
                ),
        )
        assert M.main(argv) == expected


def _probe_error_receipt():
    def raising(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["perf"], 1)
    return perf_preflight.probe_perf_availability(
        perf_candidates=(), subprocess_runner=raising,
    )


def test_probe_error_receipt_is_durable_before_loop_raises(tmp_path):
    receipt = _probe_error_receipt()
    path = tmp_path / "perf-preflight.json"
    with pytest.raises(perf_preflight.PerfPreflightError, match="判定不能"):
        loop._perform_perf_preflight(
            lambda **_kwargs: receipt, receipt_path=str(path),
        )
    assert json.loads(path.read_text(encoding="utf-8")) == receipt


def test_probe_error_driver_materializes_typed_stop_receipt(tmp_path, monkeypatch):
    contract = p2_2._legacy_linux_contract()
    authorization = env_contract.authorize(contract.env_tag)
    monkeypatch.setattr(M.p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        M.p2_2, "resolve_site_runtime",
        lambda: (site_policy.OTHER, contract, authorization),
    )
    monkeypatch.setattr(M.p2_2, "_assert_matches_calibration", lambda _contract: None)
    monkeypatch.setattr(M.buildcache, "compilers_for_current_site", lambda: ("cc", "c++"))
    monkeypatch.setattr(
        M.buildcache, "observed_toolchain_manifest", lambda *_args: {"cc": {}, "cxx": {}},
    )
    receipt = _probe_error_receipt()

    def stopped_campaign(*_args, **kwargs):
        path = Path(kwargs["perf_preflight_receipt_path"])
        path.write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        raise perf_preflight.PerfPreflightError("判定不能")

    monkeypatch.setattr(M, "run_campaign", stopped_campaign)
    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    with pytest.raises(M.PreflightStop, match="before measurement"):
        M.run_workload(
            "balanced", M.WORKLOAD_BY_TAG["balanced"],
            output_root=str(tmp_path), cache_root=str(cache_root),
            log=lambda *_args: None,
        )
    stop = json.loads((
        tmp_path / "b10-backoff-grid-balanced-preflight-stop.json"
    ).read_text(encoding="utf-8"))
    assert stop["status"] == "preflight-error-no-verdict"
    assert stop["perf_preflight_receipt"]["status"] == "probe_error"

    def typed_stop(*_args, **_kwargs):
        raise M.PreflightStop("typed preflight stop")

    monkeypatch.setattr(M, "run_workload", typed_stop)
    assert M.main([
        "balanced", "--output-root", str(tmp_path),
        "--cache-root", str(cache_root),
    ]) == 2


def test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    submit = (root / "tools/pegasus/submit_b10_backoff_grid.sh").read_text(encoding="utf-8")
    assert "#PBS -q gen_S" in job
    assert "#PBS -A SFC" in job
    assert "#PBS -b 1" in job
    assert "#PBS -l elapstim_req=05:00:00" in job
    assert "SWEEP_CAP_S=11700" in job
    assert "AA_CAP_S=3900" in job
    assert "REPORT_CAP_S=300" in job
    assert "FINALIZE_CAP_S=300" in job
    assert "EXPECTED_WALLTIME_S=18000" in job
    assert "11700 + 3900 + 300 + 300 = 16200" in job
    assert (
        "EXPECTED_FREEZE_TREES_SHA256="
        "c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3"
    ) in job
    assert "WORKLOADS=(write-heavy balanced read-heavy)" in submit
    assert (
        "for command_name in qstat qsub pegasusinfo check_quota sha256sum; do"
        in submit
    )
    assert "\ncheck_quota >/dev/null\n" in submit
    assert "\nquota -s >/dev/null\n" not in submit
    assert submit.count("job_id=$(qsub") == 1
    assert "B10_WORKLOAD=$workload" in submit
    assert "B10_SUBMISSION_NONCE=$SUBMISSION_NONCE" in submit
    assert "QUEUE_STATE=$(qstat -Q)" in submit
    assert "ENABLE(?:D)?" in submit and "ACT|ACTIVE" in submit
    assert '[[ "$HOSTNAME_SHORT" =~ ^bnode[0-9]+([.].*)?$ ]]' in job
    assert 'timeout 30 qstat -f "$QSTAT_JOBID"' in job
    assert 'export IZANAGI_RESERVATION_SCRIPT_SHA256="$SCRIPT_SHA256"' in job
    assert job.count('--cache-root "$B10_BUILD_CACHE_ROOT"') == 2


def test_failure_and_submission_receipts_cover_partial_progress():
    root = Path(__file__).resolve().parents[2]
    job = (root / "tools/pegasus/b10_backoff_grid.sh").read_text(encoding="utf-8")
    submit = (root / "tools/pegasus/submit_b10_backoff_grid.sh").read_text(encoding="utf-8")
    assert 'base.glob("campaigns/*/runs/wal.jsonl")' in job
    assert '"last_committed": committed' in job
    assert 'base.glob("campaigns/*/reports/b10-backoff-overthrottle-*.jsonl")' in job
    assert 'base.glob("campaigns/*/reports/*")' in job
    assert 'fail 2 "freeze trees changed during the job"' in job
    append = submit.index("append_submission_event submitted")
    display = submit.index("printf '%s\\n' \"$job_id\"")
    assert append < display
    assert "append_submission_event failed" in submit


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


def _run():
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
