# -*- coding: utf-8 -*-
"""S-1 検証相 extime 校正の純ロジックテスト (subprocess 実走なし)。"""
from __future__ import annotations

import ast
import contextlib
import json
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import s1_verify_extime_calibration as M  # noqa: E402
from campaign import t080_freeze_migration as T080  # noqa: E402


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


def test_build_target_prefilter_rejects_before_patch_without_source_leak(
        tmp_path, monkeypatch):
    target = dict(M._constructed_target())
    predicate = "\nizanagi_gate_pass = true; SECRET_CANARY\n"
    target["gate_predicate"] = predicate
    monkeypatch.setattr(M, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        M,
        "applied",
        lambda *a, **k: pytest.fail("patch application reached after prefilter reject"),
    )
    with pytest.raises(M.CalibrationError, match="invalid-character") as caught:
        M._build_target(target)
    assert predicate not in str(caught.value)
    assert "SECRET_CANARY" not in repr(caught.value)


def test_build_target_binds_actual_source_receipt_to_build(tmp_path, monkeypatch):
    calls = []
    target = M._constructed_target()
    evidence = SimpleNamespace(src_token="trigger-source-token")
    sealed_receipt = object()
    admission = object()

    @contextlib.contextmanager
    def fake_applied(*args, **kwargs):
        calls.append("applied")
        yield

    def fake_quarantine(*args, **kwargs):
        calls.append("quarantine")
        return SimpleNamespace(passed=True), "base", "edited", "diff"

    def fake_resolve(*args, **kwargs):
        calls.append("resolve")
        return evidence

    def fake_issue(actual, *, genome):
        calls.append("issue")
        assert actual is evidence
        assert genome is target["genome"]
        return sealed_receipt

    def fake_attest(context, actual, *, generator_input_sha256):
        calls.append("attest")
        assert actual is evidence and len(generator_input_sha256) == 64
        return "capability"

    def fake_derive(context, actual, **kwargs):
        calls.append("derive")
        assert actual is evidence
        assert kwargs == {
            "generator_receipt": "capability",
            "trigger_gate_receipt": sealed_receipt,
        }
        return admission

    def fake_build(*args, **kwargs):
        calls.append("build")
        assert kwargs["source_evidence"] is evidence
        assert kwargs["admission"] is admission
        return SimpleNamespace(
            binary="/tmp/ycsb_silo.exe",
            bin_hash="a" * 16,
            cached=False,
            configure_cmd="configure",
            build_cmd="build",
        )

    monkeypatch.setattr(M, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(M, "applied", fake_applied)
    monkeypatch.setattr(M.p3_s4_loop, "quarantine", fake_quarantine)
    monkeypatch.setattr(M.source_digest, "resolve_evidence", fake_resolve)
    monkeypatch.setattr(M, "issue_trigger_gate_receipt", fake_issue)
    monkeypatch.setattr(M, "attest_generator_output", fake_attest)
    monkeypatch.setattr(M, "derive_build_admission", fake_derive)
    monkeypatch.setattr(M.buildcache, "build", fake_build)

    result = M._build_target(target)
    assert result["src_token"] == "trigger-source-token"
    assert calls == [
        "applied", "quarantine", "resolve", "issue", "attest", "derive", "build",
    ]


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


def test_receipt_exists_but_calibration_target_stays_legacy_strict(
        tmp_path, monkeypatch):
    receipt = tmp_path / T080.RECEIPT_REL
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(T080, "ROOT", tmp_path)

    def adapter_must_not_run(*_args, **_kwargs):
        pytest.fail("calibration legacy 経路が T-080 adapter を呼んだ")

    monkeypatch.setattr(T080, "verify_receipt", adapter_must_not_run)
    monkeypatch.setattr(T080, "static_gate_adapter", adapter_must_not_run)
    assert (T080.ROOT / T080.RECEIPT_REL).is_file()

    with M.s1_known_axes_freeze.FREEZE_PATH.open(encoding="utf-8") as stream:
        freeze = json.load(stream)
    verified = []
    target = M.validated_target(
        freeze, verify_fn=lambda document: verified.append(document),
    )
    assert verified == [freeze]
    assert target["name"] == M.GATE_NAME


def test_calibration_production_module_does_not_import_t080_adapter():
    source = Path(M.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
            imports.extend(alias.name for alias in node.names)
    assert not [name for name in imports if "t080_freeze_migration" in name]
    assert "verify_receipt" not in source and "static_gate_adapter" not in source
