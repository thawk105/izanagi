# -*- coding: utf-8 -*-
"""S-1 検証相 extime 校正の純ロジックテスト (subprocess 実走なし)。"""
from __future__ import annotations

import json
import math
import os
import sys
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import s1_verify_extime_calibration as M  # noqa: E402


def _candidate(extime: int, wall: float, *, verdict: str = "serializable",
               certified: bool = True) -> dict:
    return {
        "extime": extime,
        "run_walltime_s": float(extime),
        "trace_files": 48,
        "trace_bytes": extime * 100,
        "trace_lines": extime * 10,
        "verifier_walltime_s": wall,
        "maxrss_gb": 8.0,
        "txns": 100,
        "edges": 200,
        "verdict": verdict,
        "certified": certified,
    }


def _results(walls) -> list[dict]:
    return [_candidate(extime, wall)
            for extime, wall in zip(M.EXTIME_CANDIDATES, walls)]


@pytest.mark.parametrize(
    "walls, expected",
    [([141, 280, 470], 10), ([141, 280, 650], 6), ([141, 650], 3)],
)
def test_choose_extime_uses_largest_measured_pass(walls, expected):
    assert M.choose_extime(_results(walls), 600) == expected


def test_calibration_stops_after_first_walltime_excess():
    calls = []
    walls = {3: 141, 6: 650, 10: 470}

    def measure(extime):
        calls.append(extime)
        return _candidate(extime, walls[extime])

    results, chosen = M.calibrate_candidates(measure)
    assert chosen == 3
    assert [result["extime"] for result in results] == [3, 6]
    assert calls == [3, 6]


def test_choose_extime_rejects_when_extime_three_exceeds_limit():
    with pytest.raises(M.CalibrationError, match="候補なし"):
        M.choose_extime(_results([650]), 600)


@pytest.mark.parametrize("results", [[], _results([math.nan]), _results([math.inf])])
def test_choose_extime_rejects_empty_or_nonfinite(results):
    with pytest.raises(M.CalibrationError):
        M.choose_extime(results, 600)


def test_calibration_rejects_nonserializable_verdict_from_injected_measure():
    def measure(extime):
        return _candidate(extime, 141, verdict="non-serializable", certified=False)

    with pytest.raises(M.CalibrationError, match="verifier anomaly"):
        M.calibrate_candidates(measure)


def test_validated_target_rejects_freeze_and_constructed_gate_mismatch():
    verified = []
    freeze = {
        "entries": {"read-heavy": {"system_gate": {
            "name": "g_rl", "flags": {"BACK_OFF": 1},
            "gate_predicate": "expected;",
        }}},
    }

    def verify(doc):
        verified.append(doc)

    def build_target():
        return {
            "name": "g_rl", "flags": {"BACK_OFF": 0},
            "gate_predicate": "expected;", "genome": SimpleNamespace(),
        }

    with pytest.raises(M.CalibrationError, match="known_axes_freeze"):
        M.validated_target(freeze, verify_fn=verify, target_builder=build_target)
    assert verified == [freeze]


def test_constructed_target_matches_frozen_read_heavy_gate_without_subprocess():
    with M.s1_known_axes_freeze.FREEZE_PATH.open(encoding="utf-8") as f:
        freeze = json.load(f)
    target = M.validated_target(freeze, verify_fn=lambda _doc: None)
    assert target["name"] == "g_rl"


def test_measure_candidate_removes_trace_when_verifier_fails(monkeypatch):
    removed = []
    monkeypatch.setattr(M, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(M, "_run_once", lambda *_args, **_kwargs: {
        "run_walltime_s": 1.0, "trace_files": 1, "trace_bytes": 1,
        "trace_lines": 1, "_trace_dir": "/tmp/fake-s1-trace",
    })

    def verifier_fail(_trace_dir):
        raise M.CalibrationError("mock verifier failure")

    monkeypatch.setattr(M, "_verifier_run", verifier_fail)
    monkeypatch.setattr(M.shutil, "rmtree",
                        lambda path, ignore_errors: removed.append((path, ignore_errors)))
    with pytest.raises(M.CalibrationError, match="mock verifier failure"):
        M._measure_candidate("/nonexistent/ycsb.exe", 3)
    assert removed == [("/tmp/fake-s1-trace", True)]
