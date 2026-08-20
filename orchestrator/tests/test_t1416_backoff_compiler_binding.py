# -*- coding: utf-8 -*-
"""T-1416 の campaign-level toolchain binding 配線を固定する。"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import backoff_sweep, env_contract, loop, p2_2  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.pipeline import PerfConfig  # noqa: E402


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


@pytest.mark.parametrize(
    ("module", "runner"),
    [(backoff_sweep, "backoff"), (p2_2, "p2")],
)
def test_campaign_resolves_once_and_forwards_expected_toolchain(
        module, runner, monkeypatch):
    manifest = _manifest()
    observed = []
    captured = []

    monkeypatch.setattr(module, "_assert_single_tenant", lambda: None)
    if runner == "p2":
        monkeypatch.setattr(module, "_assert_matches_calibration", lambda: None)
    monkeypatch.setattr(
        module.buildcache, "compilers_for_current_site",
        lambda: ("site-cc", "site-cxx"),
    )
    if runner == "backoff":
        monkeypatch.setattr(
            module, "_compilers_for_current_site",
            lambda: ("site-cc", "site-cxx"),
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

    assert observed == [("site-cc", "site-cxx")]
    assert len(captured) == 1
    kwargs = captured[0][1]
    assert kwargs["env_contract"] == module.env_contract.lookup(module.ENV_TAG)
    assert kwargs["expected_toolchain_manifest"] is manifest
    assert kwargs["declared_use_class"] == "official"


def test_screened_workload_forwards_expected_toolchain_to_baseline_and_candidate(
        monkeypatch):
    manifest = _manifest()
    observed = []
    calls = []
    source_calls = []

    monkeypatch.setattr(backoff_sweep, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        backoff_sweep, "_compilers_for_current_site",
        lambda: ("site-cc", "site-cxx"),
    )
    monkeypatch.setattr(
        backoff_sweep.buildcache, "observed_toolchain_manifest",
        lambda cc, cxx: observed.append((cc, cxx)) or manifest,
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

    assert observed == [("site-cc", "site-cxx")]
    assert source_calls == ["test-cxx"]
    assert len(calls) == 2
    assert [call[1]["expected_toolchain_manifest"] for call in calls] == [
        manifest, manifest,
    ]
    assert calls[0][1]["expected_toolchain_manifest"] is manifest
    assert calls[1][1]["expected_toolchain_manifest"] is manifest
    assert calls[0][1]["screening"] is None
    assert calls[1][1]["screening"].name == "screening"


def test_run_campaign_forwards_expected_toolchain_to_evaluate_for_each_genome(
        tmp_path, monkeypatch):
    manifest = _manifest()
    workload = {
        "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0",
    }
    cfg = backoff_sweep.config_for("balanced", workload)
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    contract = env_contract.lookup(backoff_sweep.ENV_TAG)
    authorization = env_contract.authorize(backoff_sweep.ENV_TAG)
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
