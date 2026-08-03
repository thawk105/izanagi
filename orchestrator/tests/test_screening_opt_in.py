# -*- coding: utf-8 -*-
"""3 reconnaissance driver の screening CLI は既定off・明示opt-in。"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import backoff_sweep as B                         # noqa: E402
from campaign import s6_sort_sweep as S6                        # noqa: E402
from campaign import s8a_trigger_sweep as S8                    # noqa: E402
from campaign.build_admission import (GeneratorId,               # noqa: E402
                                      build_run_context)


_BUILD_CONTEXT = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)


def test_autonomous_loop_has_no_screening_wiring():
    source = Path(_ORCH, "campaign", "loop.py").read_text(encoding="utf-8")
    assert "ScreeningConfig" not in source
    assert "screening=" not in source


def _summary(tag):
    return types.SimpleNamespace(
        campaign_id=f"campaign-{tag}", committed=1, aborted=0,
        layout_root=f"/tmp/campaign-{tag}", results=[])


def test_backoff_screening_cli_is_default_off_and_explicit_on(monkeypatch):
    calls = []

    def fake_run(tag, workload, log=print, **kwargs):
        calls.append((tag, kwargs))
        return _summary(tag)

    monkeypatch.setattr(B, "run_workload", fake_run)
    assert B.main(["backoff_sweep.py", "balanced"]) == 0
    assert calls[-1][1]["screening_enabled"] is False

    monkeypatch.setattr(
        B.wal, "replay", lambda _layout, *, admission_policy: {},
    )
    assert B.main(["backoff_sweep.py", "balanced", "--screening",
                   "--calibration-dir", "/floor"] ) == 0
    assert calls[-1][1] == {
        "screening_enabled": True, "calibration_dir": "/floor",
        "screening_fixed_us": None, "confirm_each_candidate": False}

    assert B.main(["backoff_sweep.py", "read-heavy", "--screening",
                   "--screening-fixed-us", "100",
                   "--confirm-each-candidate"]) == 0
    assert calls[-1][1] == {
        "screening_enabled": True, "calibration_dir": "",
        "screening_fixed_us": 100, "confirm_each_candidate": True}


def test_backoff_minimal_screening_selection_and_identity():
    tag, workload = B.WORKLOADS[-1]
    full = B.ident.bind_admission_policy(
        B.config_for(tag, workload), _BUILD_CONTEXT.policy,
    )
    minimal = B.ident.bind_admission_policy(
        B.config_for(tag, workload, screening_fixed_us=100),
        _BUILD_CONTEXT.policy,
    )
    assert "screening_fixed_us" not in full.search_config
    assert minimal.search_config["screening_fixed_us"] == 100
    assert str(B.ident.campaign_id(full)) != str(B.ident.campaign_id(minimal))


def test_backoff_minimal_screening_runs_only_baseline_and_selected(monkeypatch):
    seen = {}

    def fake_screened(cfg, gs, perf, workload, calibration_dir, log, **kwargs):
        seen["canonical"] = [g.canonical() for g in gs]
        return _summary("minimal")

    monkeypatch.setattr(B, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(B, "_run_screened_workload", fake_screened)
    B.run_workload("read-heavy", B.WORKLOADS[-1][1], log=lambda *_: None,
                   screening_enabled=True, screening_fixed_us=100)
    assert seen["canonical"] == [
        "silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,"
        "NO_WAIT_OF_TICTOC=0,WAL=0",
        "silo|BACKOFF_FIXED=100,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,"
        "NO_WAIT_OF_TICTOC=0,WAL=0",
    ]


def test_s6_screening_cli_is_default_off_and_explicit_on(monkeypatch):
    calls = []

    def fake_run(tag, **kwargs):
        calls.append((tag, kwargs))
        return {"stock": {"outcome": "certified"}}

    monkeypatch.setattr(S6, "run_sweep", fake_run)
    monkeypatch.setattr(S6, "report", lambda *a, **k: "/report")
    assert S6.main(["balanced"]) == 0
    assert calls[-1][1]["screening_enabled"] is False
    assert S6.main(["balanced", "--screening", "--calibration-dir", "/floor"]) == 0
    assert calls[-1][1]["screening_enabled"] is True
    assert calls[-1][1]["calibration_dir"] == "/floor"


def test_s8a_screening_cli_is_default_off_and_explicit_on(monkeypatch):
    calls = []

    def fake_run(tag, **kwargs):
        calls.append((tag, kwargs))
        return {S8.IDENT_NAME: {"outcome": "certified"}}

    monkeypatch.setattr(S8, "run_sweep", fake_run)
    monkeypatch.setattr(S8, "report", lambda *a, **k: "/report")
    assert S8.main(["balanced"]) == 0
    assert calls[-1][1]["screening_enabled"] is False
    assert S8.main(["balanced", "--screening", "--calibration-dir", "/floor"]) == 0
    assert calls[-1][1]["screening_enabled"] is True
    assert calls[-1][1]["calibration_dir"] == "/floor"
