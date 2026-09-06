# -*- coding: utf-8 -*-
"""T-1416 の campaign-level toolchain binding 配線を固定する。"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import (  # noqa: E402
    backoff_sweep, buildcache, env_contract, ident, loop, p2_2, pipeline,
    site_policy,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
)
from orchestrator.campaign.layout import campaign_layout  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.pipeline import PerfConfig  # noqa: E402
from orchestrator.campaign.source_digest import SourceEvidence  # noqa: E402
from orchestrator.verifier.model import VerifyResult  # noqa: E402
from condition_gate_test_support import (  # noqa: E402
    condition_gate_compilers,
    install_backoff_condition_gate_roots,
)


def _manifest() -> dict[str, dict[str, str]]:
    return {
        role: {
            "requested": f"test-{role}",
            "realpath": f"/fixture/test-{role}",
            "version_first_line": f"{role} version A",
            "version": f"{role} version A",
        }
        for role in ("cc", "cxx", "cmake")
    }


def _expected_contract(site: str):
    """site fixture から独立に組み立てる reviewed runtime contract。"""
    if site == site_policy.OTHER:
        return env_contract.ExecutionEnvironmentContract(
            env_tag="linux-baremetal",
            clocks_per_us=1800,
            numactl=("numactl", "--interleave=all"),
            attestation_mode="none",
            isolation_policy=env_contract.IsolationPolicy(
                single_process=False, allow_resume=True,
            ),
            calibration_ref=env_contract.CalibrationRef(
                path=(
                    "output/env/linux-baremetal/calibration/"
                    "calibration_t48_skew0p9_rr50_rmw0.json"
                ),
                sha256=(
                    "751304772367418806eb6e63c9715cd430315066420e9e3e4c91bf356195eef5"
                ),
            ),
        )
    if site == site_policy.PEGASUS_COMPUTE:
        return env_contract.lookup("pegasus")
    raise AssertionError(site)


@pytest.mark.parametrize(
    ("module", "runner"),
    [(backoff_sweep, "backoff"), (p2_2, "p2")],
)
def test_campaign_resolves_once_and_forwards_expected_toolchain(
        module, runner, monkeypatch, tmp_path):
    site = site_policy.OTHER
    expected_contract = _expected_contract(site)
    manifest = _manifest()
    observed = []
    captured = []
    masstree_prepare_calls = []
    expected_compilers = ("site-cc", "site-cxx")
    if runner == "backoff":
        resolved = condition_gate_compilers()
        if resolved is None:
            pytest.skip("condition gate fixture requires real compilers and CMake")
        expected_compilers = resolved
        patched_root, stock_root = install_backoff_condition_gate_roots(
            tmp_path / "condition-gate",
        )

        @contextlib.contextmanager
        def checkout(*_args, **_kwargs):
            yield str(stock_root)

        monkeypatch.setattr(
            module.buildcache, "_ccbench_dir", lambda: str(patched_root),
        )
        monkeypatch.setattr(module.patchharness, "checkout", checkout)
        monkeypatch.setattr(
            module.patchharness, "applied",
            lambda *_args, **_kwargs: contextlib.nullcontext(),
        )
        monkeypatch.setattr(
            module.buildcache,
            "prepare_masstree_fetchcontent",
            lambda **kwargs: masstree_prepare_calls.append(kwargs),
        )

    monkeypatch.setattr(module, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(p2_2.site_policy, "current_site", lambda: site)
    monkeypatch.setattr(
        p2_2, "_assert_matches_calibration", lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        module.buildcache, "compilers_for_current_site",
        lambda: expected_compilers,
    )
    if runner == "backoff":
        monkeypatch.setattr(
            module, "_compilers_for_current_site",
            lambda: expected_compilers,
        )
    monkeypatch.setattr(
        module.buildcache, "observed_toolchain_manifest",
        lambda cc, cxx: observed.append((cc, cxx)) or manifest,
    )

    def fake_run_campaign(*args, **kwargs):
        captured.append((args, kwargs))
        return SimpleNamespace(
            campaign_id="fixture-campaign", layout_root="/fixture/layout",
            total=len(args[1]), skipped=0, results=[], committed=0, aborted=0,
        )

    monkeypatch.setattr(module, "run_campaign", fake_run_campaign)

    if runner == "backoff":
        module.run_workload(
            "balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50"},
            log=lambda *_args: None,
        )
    else:
        module.run_workload(
            "balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50",
                           "ycsb_rmw": "0"},
            log=lambda *_args: None,
        )

    assert observed == [expected_compilers]
    assert len(captured) == 1
    kwargs = captured[0][1]
    assert captured[0][0][3] == expected_contract.env_tag
    assert captured[0][0][4] == expected_contract.clocks_per_us
    assert kwargs["numactl"] == list(expected_contract.numactl)
    assert kwargs["authorization_contract"].contract == expected_contract
    assert kwargs["env_contract"] == expected_contract
    assert kwargs["expected_toolchain_manifest"] is manifest
    assert kwargs["declared_use_class"] == "official"
    if runner == "backoff":
        assert len(masstree_prepare_calls) == 1
        prepare = masstree_prepare_calls[0]
        assert Path(prepare["ccbench_dir"]).resolve() == patched_root.resolve()
        assert Path(prepare["fetchcontent_base_dir"]).is_absolute()


def test_screened_workload_forwards_expected_toolchain_to_baseline_and_candidate(
        monkeypatch, tmp_path):
    site = site_policy.OTHER
    expected_contract = _expected_contract(site)
    manifest = _manifest()
    observed = []
    calls = []
    source_calls = []
    prepare_calls = []
    masstree_prepare_calls = []
    compilers = condition_gate_compilers()
    if compilers is None:
        pytest.skip("condition gate fixture requires real compilers and CMake")
    patched_root, stock_root = install_backoff_condition_gate_roots(
        tmp_path / "condition-gate",
    )

    @contextlib.contextmanager
    def checkout(*_args, **_kwargs):
        yield str(stock_root)

    monkeypatch.setattr(
        backoff_sweep.buildcache, "_ccbench_dir", lambda: str(patched_root),
    )
    monkeypatch.setattr(backoff_sweep.patchharness, "checkout", checkout)
    monkeypatch.setattr(
        backoff_sweep.patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )

    monkeypatch.setattr(backoff_sweep, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(p2_2.site_policy, "current_site", lambda: site)
    captured_calibrations = []
    monkeypatch.setattr(
        p2_2, "_assert_matches_calibration",
        lambda contract: captured_calibrations.append(contract),
    )
    monkeypatch.setattr(
        backoff_sweep, "_compilers_for_current_site",
        lambda: compilers,
    )
    monkeypatch.setattr(
        backoff_sweep.buildcache, "observed_toolchain_manifest",
        lambda cc, cxx: observed.append((cc, cxx)) or manifest,
    )
    monkeypatch.setattr(
        backoff_sweep.buildcache,
        "prepare_masstree_fetchcontent",
        lambda **kwargs: masstree_prepare_calls.append(kwargs),
    )

    def fake_source_resolve(_genome, _commit, *, cxx):
        source_calls.append(cxx)
        return SimpleNamespace(src_token="fixture-source")

    monkeypatch.setattr(
        backoff_sweep.source_digest, "resolve", fake_source_resolve,
    )

    def fake_evaluate_candidate(*args, **kwargs):
        calls.append((args, kwargs))
        genome = args[2]
        return SimpleNamespace(
            genome=genome, fitness_tps=100.0, cv=0.0, unstable=False,
            aborted=False, certified=True, verdict="", notes=[],
        )

    monkeypatch.setattr(
        backoff_sweep.screening_driver,
        "evaluate_candidate",
        fake_evaluate_candidate,
    )

    def fake_prepare_screening_campaign(
            cfg, _workload, _baseline_ref, measure_baseline, **_kwargs):
        prepare_calls.append(_kwargs)
        layout = SimpleNamespace(root="/fixture/screening-layout")
        measure_baseline(cfg, layout)
        return SimpleNamespace(
            cfg=cfg, layout=layout, screening=SimpleNamespace(name="screening"),
        )

    monkeypatch.setattr(
        backoff_sweep.screening_driver,
        "prepare_screening_campaign",
        fake_prepare_screening_campaign,
    )

    backoff_sweep.run_workload(
        "balanced",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
        screening_enabled=True,
        screening_fixed_us=5,
        log=lambda *_args: None,
    )

    assert observed == [compilers]
    assert captured_calibrations == [expected_contract]
    assert len(prepare_calls) == 1
    assert prepare_calls[0]["protocol"] == "silo"
    assert prepare_calls[0]["env_tag"] == expected_contract.env_tag
    assert prepare_calls[0]["clocks_per_us"] == expected_contract.clocks_per_us
    assert prepare_calls[0]["numactl"] == list(expected_contract.numactl)
    assert prepare_calls[0]["authorization_contract"].contract == expected_contract
    assert source_calls == ["test-cxx"]
    assert len(calls) == 2
    assert [call[0][4] for call in calls] == [
        expected_contract.env_tag, expected_contract.env_tag,
    ]
    assert [call[0][5] for call in calls] == [
        expected_contract.clocks_per_us, expected_contract.clocks_per_us,
    ]
    assert [call[1]["numactl"] for call in calls] == [
        list(expected_contract.numactl), list(expected_contract.numactl),
    ]
    assert [call[1]["authorization_contract"].contract for call in calls] == [
        expected_contract, expected_contract,
    ]
    assert [call[1]["env_contract"] for call in calls] == [
        expected_contract, expected_contract,
    ]
    assert [call[1]["declared_use_class"] for call in calls] == [
        "official", "official",
    ]
    assert [call[1]["expected_toolchain_manifest"] for call in calls] == [
        manifest, manifest,
    ]
    assert calls[0][1]["expected_toolchain_manifest"] is manifest
    assert calls[1][1]["expected_toolchain_manifest"] is manifest
    assert calls[0][1]["screening"] is None
    assert calls[1][1]["screening"].name == "screening"
    assert len(masstree_prepare_calls) == 1
    prepare = masstree_prepare_calls[0]
    assert Path(prepare["ccbench_dir"]).resolve() == patched_root.resolve()
    assert Path(prepare["fetchcontent_base_dir"]).is_absolute()


def test_run_campaign_forwards_expected_toolchain_to_evaluate_for_each_genome(
        tmp_path, monkeypatch):
    manifest = _manifest()
    workload = {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0",
    }
    cfg = backoff_sweep.config_for("balanced", workload)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    contract = _expected_contract(site_policy.OTHER)
    authorization = env_contract.authorize(contract.env_tag)
    genomes = [
        Genome("silo", {"BACK_OFF": 0}),
        Genome("silo", {"BACK_OFF": 1}),
    ]
    evaluate_calls = []
    source_calls = []

    def fake_authorize(bound_cfg, _authorization_contract, **_kwargs):
        return loop._AuthorizationResult(
            authorized_contract=contract,
            execution_receipt=None,
            bound_cfg=bound_cfg,
            campaign_identity=str(loop.ident.campaign_id(bound_cfg)),
        )

    monkeypatch.setattr(loop, "_authorize_measurement", fake_authorize)
    monkeypatch.setattr(
        loop.ident, "ensure_resumable_wal",
        lambda *_args, **_kwargs: SimpleNamespace(status="clean"),
    )
    monkeypatch.setattr(loop.wal, "replay", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        loop.buildcache, "toolchain_compilers_from_manifest",
        lambda received: ("expected-cc", "expected-cxx")
        if received is manifest else pytest.fail("manifest identity was lost"),
    )
    monkeypatch.setattr(
        loop, "_compilers_for_current_site",
        lambda: ("wrong-cc", "wrong-cxx"),
    )
    monkeypatch.setattr(
        loop.source_digest, "resolve_evidence",
        lambda genome, *_args, **kwargs: (
            source_calls.append((genome, kwargs))
            or SimpleNamespace(src_token=f"token-{genome.flags['BACK_OFF']}")
        ),
    )

    def fake_evaluate(*args, **kwargs):
        evaluate_calls.append((args, kwargs))
        return SimpleNamespace(
            genome=args[0], fitness_tps=None, aborted=False, certified=True,
        )

    monkeypatch.setattr(loop, "evaluate", fake_evaluate)

    summary = loop.run_campaign(
        cfg, genomes, PerfConfig(records=1, threads=1),
        contract.env_tag, contract.clocks_per_us, numactl=contract.numactl,
        do_bench=False, output_root=str(tmp_path),
        env_contract=contract, expected_toolchain_manifest=manifest,
        authorization_contract=authorization, build_context=build_context,
        declared_use_class="official",
    )

    assert summary.evaluated == len(genomes)
    assert len(evaluate_calls) == len(genomes)
    assert [call[1]["expected_toolchain_manifest"] for call in evaluate_calls] == [
        manifest, manifest,
    ]
    assert all(
        call[1]["expected_toolchain_manifest"] is manifest
        for call in evaluate_calls
    )
    assert [kwargs["cxx"] for _, kwargs in source_calls] == [
        "expected-cxx", "expected-cxx",
    ]


def test_pegasus_v2_evaluate_binds_contract_and_toolchain_provenance(
        tmp_path, monkeypatch):
    """実 pipeline.evaluate の v2 build 境界で Pegasus contract を検査する。"""
    site = site_policy.PEGASUS_COMPUTE
    contract = _expected_contract(site)
    authorization = env_contract.authorize(contract.env_tag)
    manifest = _manifest()
    manifest_sha256 = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    genome = Genome("silo", {"BACK_OFF": 1})
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    commit = backoff_sweep.CCBENCH_COMMIT
    source = SourceEvidence(
        schema_version="source-evidence/v1",
        source_root=os.path.realpath(str(tmp_path / "ccbench")),
        ccbench_commit=commit,
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
        src_token="stock",
        source_bytes_sha256=hashlib.sha256(b"stock").hexdigest(),
        tracked_clean=True,
        tracked_diff_sha256=hashlib.sha256(b"").hexdigest(),
        tracked_paths=(),
    )
    cfg = p2_2._campaign_cfg_for_site(
        backoff_sweep.config_for(
            "balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50"},
            contract=contract,
        ),
        site,
        contract,
    )
    cfg = ident.bind_admission_policy(cfg, context.policy)
    layout = campaign_layout(
        str(ident.campaign_id(cfg)), str(tmp_path / "output"),
    ).ensure()
    build_calls = []
    build_results = []

    def fake_build_v2(genome_value, **kwargs):
        build_calls.append((genome_value, kwargs))
        assert kwargs["contract"] is contract
        assert kwargs["expected_toolchain_manifest"] is manifest
        assert kwargs["declared_use_class"] == "official"
        assert kwargs["cc"] == "test-cc"
        assert kwargs["cxx"] == "test-cxx"
        build_result = buildcache.BuildResult(
            genome=genome_value,
            trace=kwargs["trace"],
            binary="/fixture/ycsb_silo.exe",
            bin_sha256=("a" if kwargs["trace"] else "b") * 64,
            build_dir=str(tmp_path / "build"),
            cached=True,
            contract_sha256=contract.contract_sha256,
            toolchain=manifest,
            toolchain_manifest=manifest,
            toolchain_manifest_sha256=manifest_sha256,
        )
        build_results.append(build_result)
        return build_result

    monkeypatch.setattr(site_policy, "current_site", lambda: site)
    monkeypatch.setattr(pipeline, "_resolve_site", lambda _site: site)
    monkeypatch.setattr(pipeline.buildcache, "_ccbench_dir", lambda: str(tmp_path))
    monkeypatch.setattr(pipeline.source_digest, "resolve_evidence", lambda *args, **kwargs: source)
    monkeypatch.setattr(pipeline.buildcache, "build_v2", fake_build_v2)
    monkeypatch.setattr(
        pipeline,
        "_run_trace",
        lambda *_args, **_kwargs: pipeline._TraceRunResult(1, 0, 0, 1, 0),
    )
    monkeypatch.setattr(
        pipeline,
        "verify_trace_dir_with_capability",
        lambda *_args, **_kwargs: (
            VerifyResult(trace_dir="/fixture/trace", serializable=False, n_txns=1),
            None,
        ),
    )

    result = pipeline.evaluate(
        genome,
        layout,
        contract.env_tag,
        commit,
        PerfConfig(records=1, threads=1),
        contract.clocks_per_us,
        numactl=contract.numactl,
        do_bench=False,
        do_settle=False,
        src_token=source.src_token,
        env_contract=contract,
        expected_toolchain_manifest=manifest,
        declared_use_class="official",
        authorization_contract=authorization,
        build_context=context,
        log=lambda *_args: None,
    )

    assert result.aborted is True
    assert result.certified is False
    assert [kwargs["trace"] for _, kwargs in build_calls] == [True, False]
    assert all(kwargs["contract"] is contract for _, kwargs in build_calls)
    assert all(
        kwargs["expected_toolchain_manifest"] is manifest
        for _, kwargs in build_calls
    )
    assert all(kwargs["declared_use_class"] == "official" for _, kwargs in build_calls)
    assert [built.trace for built in build_results] == [True, False]
    assert all(built.contract_sha256 == contract.contract_sha256 for built in build_results)
    assert all(built.toolchain is manifest for built in build_results)
    assert all(built.toolchain_manifest_sha256 == manifest_sha256 for built in build_results)

if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
