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

from orchestrator.campaign import backoff_sweep, p2_2  # noqa: E402


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
