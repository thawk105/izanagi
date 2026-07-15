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


def test_autonomous_loop_has_no_screening_wiring():
    source = Path(_ORCH, "campaign", "loop.py").read_text(encoding="utf-8")
    assert "ScreeningConfig" not in source
    assert "screening=" not in source


def _summary(tag):
    return types.SimpleNamespace(
        campaign_id=f"campaign-{tag}", committed=1, aborted=0,
        layout_root=f"/tmp/campaign-{tag}")


def test_backoff_screening_cli_is_default_off_and_explicit_on(monkeypatch):
    calls = []

    def fake_run(tag, workload, log=print, **kwargs):
        calls.append((tag, kwargs))
        return _summary(tag)

    monkeypatch.setattr(B, "run_workload", fake_run)
    assert B.main(["backoff_sweep.py", "balanced"]) == 0
    assert calls[-1][1]["screening_enabled"] is False

    monkeypatch.setattr(B.wal, "replay", lambda _layout: {})
    assert B.main(["backoff_sweep.py", "balanced", "--screening",
                   "--calibration-dir", "/floor"] ) == 0
    assert calls[-1][1] == {"screening_enabled": True, "calibration_dir": "/floor"}


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
