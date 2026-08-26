from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import (
    backoff_extended_sweep as M,
    backoff_extended_sweep_report as R,
    backoff_overthrottle as O,
    build_admission,
    env_contract,
    ident,
    loop,
    p2_2,
    site_policy,
)
from orchestrator.calibrator import perf_preflight


def _stub_patch_and_prebuild(monkeypatch, events=None):
    observed = [] if events is None else events

    @contextmanager
    def applied(patch_path, pin_commit, ccbench_dir):
        observed.append(("patch-enter", patch_path, pin_commit, ccbench_dir))
        try:
            yield ["cmake/Options.cmake", "include/backoff.hh"]
        finally:
            observed.append(("patch-exit",))

    monkeypatch.setattr(M.patchharness, "applied", applied)
    monkeypatch.setattr(
        M, "_assert_backoff_fixed_materialized",
        lambda _ccbench_dir: observed.append(("patch-materialized",)),
    )
    monkeypatch.setattr(
        M, "_prebuild_backoff_binaries",
        lambda *_args, **_kwargs: observed.append(("prebuild",)) or {},
    )
    return observed


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


def test_applied_tree_contains_the_backoff_fixed_build_surface(tmp_path):
    cmake = tmp_path / "cmake"
    include = tmp_path / "include"
    cmake.mkdir()
    include.mkdir()
    (cmake / "Options.cmake").write_text(
        "set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING fixture)\n"
        "BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}\n",
        encoding="utf-8",
    )
    backoff = include / "backoff.hh"
    backoff.write_text(
        "#ifndef BACKOFF_FIXED\n#endif\n#if BACKOFF_FIXED >= 0\n#endif\n",
        encoding="utf-8",
    )
    M._assert_backoff_fixed_materialized(str(tmp_path))

    backoff.write_text("#ifndef BACKOFF_FIXED\n#endif\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="patch is not materialized"):
        M._assert_backoff_fixed_materialized(str(tmp_path))


def test_distinct_backoff_fixed_amounts_produce_distinct_build_results(monkeypatch):
    points = [
        M.Genome("silo", {"BACK_OFF": 1, "BACKOFF_FIXED": amount})
        for amount in (5, 10)
    ]
    build_events = []

    def resolve_evidence(genome, *_args, **_kwargs):
        return SimpleNamespace(
            src_token=f"source-{genome.flags['BACKOFF_FIXED']}",
        )

    def build_v2(genome, **kwargs):
        amount = genome.flags["BACKOFF_FIXED"]
        build_events.append((amount, kwargs["trace"]))
        return M.buildcache.BuildResult(
            genome=genome, trace=kwargs["trace"], binary=f"/bin/fixed-{amount}",
            bin_sha256=hashlib.sha256(f"binary-{amount}".encode()).hexdigest(),
            build_dir=f"/build/fixed-{amount}", cached=False,
        )

    monkeypatch.setattr(M.source_digest, "resolve_evidence", resolve_evidence)
    monkeypatch.setattr(M, "derive_build_admission", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(M.buildcache, "build_v2", build_v2)
    built = M._prebuild_backoff_binaries(
        points,
        contract=object(),
        cache_root="/cache",
        ccbench_dir="/ccbench",
        resolved_cc="cc",
        resolved_cxx="c++",
        expected_toolchain_manifest={},
        build_context=object(),
        capability_resolver=lambda _evidence: object(),
        trace_modes=(False,),
    )
    hashes = [built[(point.canonical(), False)].bin_sha256 for point in points]
    assert build_events == [(5, False), (10, False)]
    assert len(set(hashes)) == 2


def test_duplicate_static_binary_hash_stops_before_campaign(monkeypatch):
    points = [
        M.Genome("silo", {"BACK_OFF": 1, "BACKOFF_FIXED": amount})
        for amount in (5, 10)
    ]
    shared_sha256 = hashlib.sha256(b"same-binary").hexdigest()
    monkeypatch.setattr(
        M.source_digest, "resolve_evidence",
        lambda genome, *_args, **_kwargs: SimpleNamespace(
            src_token=f"source-{genome.flags['BACKOFF_FIXED']}",
        ),
    )
    monkeypatch.setattr(M, "derive_build_admission", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(
        M.buildcache, "build_v2",
        lambda genome, **kwargs: M.buildcache.BuildResult(
            genome=genome, trace=kwargs["trace"], binary="/bin/shared",
            bin_sha256=shared_sha256, build_dir="/build/shared", cached=False,
        ),
    )
    with pytest.raises(RuntimeError, match="produced the same binary"):
        M._prebuild_backoff_binaries(
            points,
            contract=object(),
            cache_root="/cache",
            ccbench_dir="/ccbench",
            resolved_cc="cc",
            resolved_cxx="c++",
            expected_toolchain_manifest={},
            build_context=object(),
            capability_resolver=lambda _evidence: object(),
            trace_modes=(False,),
        )


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
    events = _stub_patch_and_prebuild(monkeypatch)
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
        events.append(("campaign",))
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
    assert [event[0] for event in events] == [
        "patch-enter", "patch-materialized", "prebuild", "campaign", "patch-exit",
    ]
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
    _stub_patch_and_prebuild(monkeypatch)
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
    required_commands = job.split("for command_name in ", 1)[1].split("; do", 1)[0].split()
    required_commands = [name for name in required_commands if name != "\\"]
    assert "gnuplot" not in required_commands
    assert "gnuplot" not in job
    assert required_commands == [
        "git", "cmake", "cc", "c++", "make", "timeout", "qstat", "sha256sum",
        "hostname", "mkdir", "realpath", "tr", "date",
    ]
    report_call = job.split(
        '"$REPO_ROOT/orchestrator/campaign/backoff_extended_sweep_report.py"', 1,
    )[1].split("CURRENT_STAGE=finalize", 1)[0]
    assert '"$WORKLOAD" --output-root "$OUTPUT_ROOT" --defer-plot' in report_call
    assert "gnuplot" not in report_call
    assert job.count('--cache-root "$B10_BUILD_CACHE_ROOT"') == 2
    assert job.count("http://10.120.96.1:8080") == 1
    assert "BUILD_NETWORK_PROXY_URL=http://10.120.96.1:8080" in job
    assert 'export http_proxy="$BUILD_NETWORK_PROXY_URL"' in job
    assert 'export https_proxy="$BUILD_NETWORK_PROXY_URL"' in job
    assert '"external_fetch_via_proxy": True' in job
    assert '"dependency_revisions": "sha-pinned"' in job


def test_deferred_report_writes_plot_inputs_and_records_missing_png(
        tmp_path, monkeypatch):
    layout = SimpleNamespace(reports_dir=str(tmp_path), root=str(tmp_path / "campaign-id"))
    normal = [{
        "kind": "static", "backoff_us": 10, "median_tps": 123.0,
        "abort_rate": 0.25, "latency_ns": 456.0, "cv": 0.01,
    }]
    verdict = {
        **R.CLAIM_BOUNDARY,
        "status": "complete",
        "peak": None,
        "onset": None,
        "mechanism": {"trace_disabled_table": [], "add_analysis_table": []},
    }
    monkeypatch.setattr(
        R, "load_normal_points", lambda *_args: (normal, "available", layout),
    )
    monkeypatch.setattr(R, "load_aa_records", lambda *_args: [])
    monkeypatch.setattr(R, "evaluate_workload", lambda *_args, **_kwargs: verdict)

    def forbidden_renderer(*_args, **_kwargs):
        raise AssertionError("measurement job must not start the plot renderer")

    monkeypatch.setattr(R, "make_plot", forbidden_renderer)
    result = R.report_workload(
        "balanced", str(tmp_path), log=lambda *_args: None, render_plot=False,
    )

    stem = tmp_path / "b10-backoff-grid-balanced"
    recorded = json.loads(Path(result["verdict_path"]).read_text(encoding="utf-8"))
    assert Path(f"{stem}.dat").is_file()
    assert Path(f"{stem}.plt").is_file()
    assert not Path(f"{stem}.png").exists()
    assert recorded["plot_artifact"] == {
        "status": "deferred",
        "reason": "measurement_host_plotting_prohibited",
        "renderer": "gnuplot",
        "renderer_invoked": False,
        "dat": "b10-backoff-grid-balanced.dat",
        "script": "b10-backoff-grid-balanced.plt",
        "png": {
            "path": "b10-backoff-grid-balanced.png",
            "status": "not_generated_on_measurement_host",
        },
    }
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert "Plot status: `deferred`." in report
    assert "PNG was not generated" in report
    assert "![balanced]" not in report


@pytest.mark.parametrize(
    ("extra_args", "expected_render"),
    [([], True), (["--defer-plot"], False)],
)
def test_report_cli_preserves_default_render_and_allows_measurement_deferral(
        monkeypatch, extra_args, expected_render):
    observed = []

    def report(tag, output_root, *, render_plot=True):
        observed.append((tag, output_root, render_plot))
        return {"verdict": {"status": "complete"}}

    monkeypatch.setattr(R, "report_workload", report)
    assert R.main(["balanced", "--output-root", "/outside/root", *extra_args]) == 0
    assert observed == [("balanced", "/outside/root", expected_render)]


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
