import os
import sys

from types import SimpleNamespace

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import backoff_sweep
from orchestrator.campaign.durable_root import DurableRootPolicy


def _stub_run_workload_dependencies(monkeypatch, captured):
    contract = SimpleNamespace(
        env_tag="test-env",
        clocks_per_us=123,
        numactl=(),
        attestation_mode="none",
    )
    context = SimpleNamespace(policy=object())

    monkeypatch.setattr(backoff_sweep, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        backoff_sweep.p2_2,
        "resolve_site_runtime",
        lambda: ("test-site", contract, object()),
    )
    monkeypatch.setattr(
        backoff_sweep.p2_2,
        "_assert_matches_calibration",
        lambda _contract: None,
    )
    monkeypatch.setattr(backoff_sweep, "genomes", lambda: [object()])
    monkeypatch.setattr(backoff_sweep, "config_for", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        backoff_sweep.p2_2,
        "_campaign_cfg_for_site",
        lambda cfg, _site, _contract: cfg,
    )
    monkeypatch.setattr(
        backoff_sweep,
        "_compilers_for_current_site",
        lambda: ("cc", "cxx"),
    )
    monkeypatch.setattr(
        backoff_sweep.buildcache,
        "observed_toolchain_manifest",
        lambda cc, cxx: {"cc": cc, "cxx": cxx},
    )
    monkeypatch.setattr(backoff_sweep, "build_run_context", lambda **kwargs: context)
    monkeypatch.setattr(
        backoff_sweep.ident,
        "bind_admission_policy",
        lambda cfg, _policy: cfg,
    )

    def capture_run_campaign(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(results=[], committed=0, aborted=0)

    monkeypatch.setattr(backoff_sweep, "run_campaign", capture_run_campaign)


def test_official_output_root_policy_is_passed_to_run_campaign(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setenv("IZANAGI_OFFICIAL_OUTPUT_ROOT", str(tmp_path))
    _stub_run_workload_dependencies(monkeypatch, captured)

    backoff_sweep.run_workload(
        "read-heavy",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
        log=lambda _message: None,
    )

    policy = captured["durable_root_policy"]
    assert isinstance(policy, DurableRootPolicy)
    assert policy.approved_roots == (tmp_path.resolve(),)
    assert policy.forbidden_roots == ()


def test_without_official_output_root_policy_is_omitted(monkeypatch):
    captured = {}
    monkeypatch.delenv("IZANAGI_OFFICIAL_OUTPUT_ROOT", raising=False)
    _stub_run_workload_dependencies(monkeypatch, captured)

    backoff_sweep.run_workload(
        "read-heavy",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
        log=lambda _message: None,
    )

    assert captured["durable_root_policy"] is None


# ---- 素の runner (直接起動でも pytest を実行) ----

def _run():
    import pytest
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
