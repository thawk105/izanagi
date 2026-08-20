# -*- coding: utf-8 -*-
"""T-1444 p2/backoff の site-aware runtime contract 境界。"""
from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import (  # noqa: E402
    backoff_sweep,
    env_contract,
    p2_2,
    site_policy,
)


def _expected_contract(site: str):
    """resolver の内部値を参照せず、site fixture から期待値を組み立てる。"""
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
        # The site fixture supplies the expected tag; lookup is independent of
        # resolve_site_runtime() and follows the active reviewed generation.
        return env_contract.lookup("pegasus")
    raise AssertionError(site)


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


@pytest.mark.parametrize("site", [site_policy.OTHER, site_policy.PEGASUS_COMPUTE])
def test_p2_2_site_runtime_matches_independent_contract(site, monkeypatch):
    expected = _expected_contract(site)
    monkeypatch.setattr(p2_2.site_policy, "current_site", lambda: site)

    resolved_site, contract, authorization = p2_2.resolve_site_runtime()

    assert resolved_site == site
    assert contract == expected
    assert contract.contract_sha256 == expected.contract_sha256
    assert authorization.contract == expected
    assert authorization.contract.contract_sha256 == expected.contract_sha256


def test_p2_2_compute_campaign_identity_contains_measurement_env(monkeypatch):
    site = site_policy.PEGASUS_COMPUTE
    expected = _expected_contract(site)
    cfg = p2_2.config_for(
        "balanced", {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50"},
    )

    bound = p2_2._campaign_cfg_for_site(cfg, site, expected)

    assert bound.search_config["measurement_env"] == expected.env_tag
    assert bound.bound_environment_contract == expected
    with pytest.raises(ValueError, match="measurement_env"):
        p2_2._campaign_cfg_for_site(
            replace(
                cfg,
                search_config={**cfg.search_config, "measurement_env": "linux-baremetal"},
            ),
            site,
            expected,
        )


@pytest.mark.parametrize(
    "site", [site_policy.PEGASUS_LOGIN, site_policy.PEGASUS_SUSPECT, "UNKNOWN_SITE"],
)
def test_p2_2_login_suspect_and_unknown_sites_are_rejected(site, monkeypatch):
    monkeypatch.setattr(p2_2.site_policy, "current_site", lambda: site)

    with pytest.raises(RuntimeError, match="site"):
        p2_2.resolve_site_runtime()


def test_p2_2_assert_matches_registered_v2_by_calibration_ref(monkeypatch):
    expected = _expected_contract(site_policy.PEGASUS_COMPUTE)
    reads = []
    original_read_bytes = Path.read_bytes

    def tracked_read_bytes(path):
        reads.append(path)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", tracked_read_bytes)
    p2_2._assert_matches_calibration(expected)

    assert len(reads) == 1
    assert reads[0].as_posix().endswith(expected.calibration_ref.path)


def test_p2_2_legacy_linux_calibration_remains_supported(monkeypatch):
    expected = _expected_contract(site_policy.OTHER)
    reads = []
    original_read_bytes = Path.read_bytes

    def tracked_read_bytes(path):
        reads.append(path)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", tracked_read_bytes)
    p2_2._assert_matches_calibration(expected)

    assert len(reads) == 1
    assert reads[0].as_posix().endswith(expected.calibration_ref.path)


@pytest.mark.parametrize("field", ["records", "threads", "env_tag", "clocks_per_us"])
def test_p2_2_calibration_value_mismatch_fails_closed(field, monkeypatch):
    expected = _expected_contract(site_policy.OTHER)
    parsed = {
        "env_tag": expected.env_tag,
        "threads": p2_2.THREADS,
        "clocks_per_us": expected.clocks_per_us,
        "saturation": {"records": p2_2.RECORDS},
    }
    if field == "records":
        parsed["saturation"]["records"] += 1
    elif field == "threads":
        parsed["threads"] += 1
    elif field == "env_tag":
        parsed["env_tag"] = "foreign-site"
    else:
        parsed["clocks_per_us"] += 1
    monkeypatch.setattr(
        p2_2,
        "_load_calibration_once",
        lambda _contract: p2_2._LoadedCalibration(
            raw=b"verified-by-fixture",
            verified=object(),
            parsed=parsed,
        ),
    )

    with pytest.raises(RuntimeError, match="不一致"):
        p2_2._assert_matches_calibration(expected)


def test_p2_2_missing_or_wrong_hash_calibration_fails_closed():
    expected = _expected_contract(site_policy.OTHER)
    missing = replace(
        expected,
        calibration_ref=env_contract.CalibrationRef(
            path="output/env/linux-baremetal/calibration/missing.json",
            sha256=expected.calibration_ref.sha256,
        ),
    )
    with pytest.raises(RuntimeError, match="読み込めない"):
        p2_2._assert_matches_calibration(missing)

    wrong_hash = replace(
        expected,
        calibration_ref=env_contract.CalibrationRef(
            path=expected.calibration_ref.path,
            sha256="0" * 64,
        ),
    )
    with pytest.raises(RuntimeError, match="sha256"):
        p2_2._assert_matches_calibration(wrong_hash)


def test_p2_2_invalid_v2_schema_fails_closed(monkeypatch):
    expected = _expected_contract(site_policy.PEGASUS_COMPUTE)
    raw = b"{}"
    invalid = replace(
        expected,
        calibration_ref=env_contract.CalibrationRef(
            path=expected.calibration_ref.path,
            sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    monkeypatch.setattr(Path, "read_bytes", lambda _path: raw)

    with pytest.raises(RuntimeError, match="schema"):
        p2_2._assert_matches_calibration(invalid)


def test_p2_2_run_campaign_receives_one_contract_for_all_runtime_arguments(monkeypatch):
    site = site_policy.PEGASUS_COMPUTE
    expected = _expected_contract(site)
    manifest = _manifest()
    resolver_calls = []
    calibration_calls = []
    captured = []

    monkeypatch.setattr(p2_2.site_policy, "current_site", lambda: site)
    real_resolver = p2_2.resolve_site_runtime

    def tracked_resolver():
        resolver_calls.append(True)
        return real_resolver()

    monkeypatch.setattr(p2_2, "resolve_site_runtime", tracked_resolver)
    monkeypatch.setattr(p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        p2_2, "_assert_matches_calibration",
        lambda contract: calibration_calls.append(contract),
    )
    monkeypatch.setattr(
        p2_2.buildcache, "compilers_for_current_site",
        lambda: ("site-cc", "site-cxx"),
    )
    monkeypatch.setattr(
        p2_2.buildcache, "observed_toolchain_manifest",
        lambda _cc, _cxx: manifest,
    )

    def fake_run_campaign(*args, **kwargs):
        captured.append((args, kwargs))
        return SimpleNamespace(
            campaign_id="fixture-campaign", layout_root="/fixture/layout",
            total=len(args[1]), skipped=0, results=[], committed=0, aborted=0,
        )

    monkeypatch.setattr(p2_2, "run_campaign", fake_run_campaign)
    p2_2.run_workload(
        "balanced",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "50", "ycsb_rmw": "0"},
        log=lambda *_args: None,
    )

    assert resolver_calls == [True]
    assert calibration_calls == [expected]
    assert len(captured) == 1
    args, kwargs = captured[0]
    assert args[3:5] == (expected.env_tag, expected.clocks_per_us)
    assert kwargs["numactl"] == list(expected.numactl)
    assert kwargs["authorization_contract"].contract == expected
    assert kwargs["env_contract"] == expected
    assert kwargs["expected_toolchain_manifest"] is manifest
    assert kwargs["declared_use_class"] == "official"


def test_backoff_sweep_screening_reuses_one_resolved_runtime(monkeypatch):
    site = site_policy.PEGASUS_COMPUTE
    expected = _expected_contract(site)
    manifest = _manifest()
    compiler_sites = []
    resolver_calls = []
    calibration_calls = []
    compiler_observations = []
    prepare_calls = []
    evaluate_calls = []

    monkeypatch.setattr(p2_2.site_policy, "current_site", lambda: site)
    runtime = p2_2.resolve_site_runtime()
    monkeypatch.setattr(
        p2_2,
        "resolve_site_runtime",
        lambda: resolver_calls.append(True) or runtime,
    )
    monkeypatch.setattr(backoff_sweep, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        p2_2,
        "_assert_matches_calibration",
        lambda contract: calibration_calls.append(contract),
    )
    monkeypatch.setattr(
        backoff_sweep,
        "_compilers_for_current_site",
        lambda: compiler_sites.append(p2_2.site_policy.current_site())
        or ("gcc", "g++"),
    )
    monkeypatch.setattr(
        backoff_sweep.buildcache,
        "observed_toolchain_manifest",
        lambda cc, cxx: compiler_observations.append((cc, cxx)) or manifest,
    )
    monkeypatch.setattr(
        backoff_sweep.source_digest,
        "resolve",
        lambda _genome, _commit, *, cxx: SimpleNamespace(src_token=f"source-{cxx}"),
    )

    def fake_evaluate_candidate(*args, **kwargs):
        evaluate_calls.append((args, kwargs))
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
            cfg, _workload, _baseline_ref, measure_baseline, **kwargs):
        prepare_calls.append((cfg, kwargs))
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

    assert resolver_calls == [True]
    assert calibration_calls == [expected]
    assert compiler_sites == [site]
    assert compiler_observations == [("gcc", "g++")]
    assert len(prepare_calls) == 1
    prepare_cfg, prepare_kwargs = prepare_calls[0]
    assert prepare_cfg.bound_environment_contract == expected
    assert prepare_kwargs["env_tag"] == expected.env_tag
    assert prepare_kwargs["clocks_per_us"] == expected.clocks_per_us
    assert prepare_kwargs["numactl"] == list(expected.numactl)
    assert prepare_kwargs["authorization_contract"].contract == expected
    assert len(evaluate_calls) == 2
    for args, kwargs in evaluate_calls:
        assert args[4:6] == (expected.env_tag, expected.clocks_per_us)
        assert kwargs["numactl"] == list(expected.numactl)
        assert kwargs["authorization_contract"].contract == expected
        assert kwargs["env_contract"] == expected
        assert kwargs["expected_toolchain_manifest"] is manifest
        assert kwargs["declared_use_class"] == "official"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
