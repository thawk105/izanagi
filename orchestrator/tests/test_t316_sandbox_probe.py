# -*- coding: utf-8 -*-
"""T316 sandbox probe の副作用なし verdict 核に対する negative tests。"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


_REPO = Path(__file__).resolve().parents[2]
_MODULE_PATH = _REPO / "tools/pegasus/probes/t316_sandbox_backend_probe.py"
_SPEC = importlib.util.spec_from_file_location("t316_sandbox_backend_probe", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
probe = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = probe
_SPEC.loader.exec_module(probe)


def _good_s3() -> dict[str, dict[str, bool]]:
    observations = {
        category: {"attempted": True, "outside_success": True, "inside_blocked": True}
        for category in probe.S3_CATEGORIES
    }
    observations["scratch_write"] = {"attempted": True, "inside_success": True}
    return observations


def _good_s5() -> dict[str, dict[str, bool]]:
    return {
        category: {"attempted": True, "outside_success": True, "inside_blocked": True}
        for category in probe.S5_CATEGORIES
    }


@pytest.mark.parametrize("category", probe.S3_CATEGORIES)
def test_s3_failed_positive_control_is_inconclusive(category: str) -> None:
    observations = _good_s3()
    observations[category]["outside_success"] = False

    verdict = probe.verdict_s3(observations)

    assert verdict.verdict == "inconclusive"
    assert verdict.verdict != "go"
    assert any(reason.endswith("POSITIVE_CONTROL_FAILED") for reason in verdict.reason_codes)


@pytest.mark.parametrize("category", probe.S5_CATEGORIES)
def test_s5_failed_positive_control_is_inconclusive(category: str) -> None:
    observations = _good_s5()
    observations[category]["outside_success"] = False

    verdict = probe.verdict_s5(observations)

    assert verdict.verdict == "inconclusive"
    assert verdict.verdict != "go"
    assert any(reason.endswith("POSITIVE_CONTROL_FAILED") for reason in verdict.reason_codes)


@pytest.mark.parametrize("category", probe.S3_CATEGORIES)
def test_s3_unattempted_containment_is_blocked(category: str) -> None:
    observations = _good_s3()
    observations[category] = {"attempted": False}

    verdict = probe.verdict_s3(observations)

    assert verdict.verdict == "blocked"
    assert verdict.verdict != "go"
    assert any(reason.endswith("NOT_ATTEMPTED") for reason in verdict.reason_codes)


@pytest.mark.parametrize("category", probe.S5_CATEGORIES)
def test_each_s5_containment_failure_is_no_go(category: str) -> None:
    observations = _good_s5()
    observations[category]["inside_blocked"] = False

    verdict = probe.verdict_s5(observations)

    assert verdict.verdict == "no-go"
    assert any(reason.endswith("CONTAINMENT_FAILED") for reason in verdict.reason_codes)


def test_overall_no_go_cannot_be_go() -> None:
    verdicts = [
        probe.StageVerdict(f"S{index}", "go", (f"S{index}_OK",))
        for index in range(1, 8)
    ]
    verdicts[4] = probe.StageVerdict("S5", "no-go", ("S5_NETWORK_CONTAINMENT_FAILED",))

    overall = probe.aggregate_verdicts(verdicts)

    assert overall.verdict == "no-go"
    assert overall.verdict != "go"
