"""T-471 restore observation driver の純関数と凍結した静的契約。"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_DRIVER_DIR = _REPO / "output" / "insights" / "2026-08-05_t471-restore-bound" / "driver"
_ANALYSIS_PATH = _DRIVER_DIR / "restore_bound_analysis.py"
_DRIVER_PATH = _DRIVER_DIR / "measure_restore_bound.py"
_PBS_PATH = _DRIVER_DIR / "restore_bound.pbs"
_FROZEN_ARMS = {
    "A-e0": {"case": "C2", "n": 2, "P": 1, "E_by_parent": [0], "cache_temperature_label": "absent", "synthetic": False},
    "A-e143-fresh": {"case": "C2", "n": 2, "P": 1, "E_by_parent": [143], "cache_temperature_label": "fresh-hot", "synthetic": False},
    "A-e143-aged": {"case": "C2", "n": 2, "P": 1, "E_by_parent": [143], "cache_temperature_label": "aged-from-attempt-start", "synthetic": False},
    "A-b240-n1": {"case": "C1", "n": 1, "P": 1, "E_by_parent": [143], "cache_temperature_label": "fresh-hot", "synthetic": False},
    "A-p2-synth": {"case": "C2", "n": 2, "P": 2, "E_by_parent": [143, 97], "cache_temperature_label": "fresh-hot", "synthetic": True},
}


def _load_analysis():
    spec = importlib.util.spec_from_file_location("t471_analysis_under_test", _ANALYSIS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYSIS = _load_analysis()


def _load_driver():
    spec = importlib.util.spec_from_file_location("t471_driver_under_test", _DRIVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DRIVER = _load_driver()


def _registered_profile() -> dict[str, object]:
    return {"n": 2, "B_original_total": 69_659, "B_mutated_total": 69_679, "target_existence_states": ["regular-file", "regular-file"], "P": 2, "E_by_parent": [143, 97], "E_total": 240, "cache_temperature_label": "fresh-hot"}


def _restore_import_flow_violations(source: str) -> list[str]:
    """本物の source path から唯一の restore call までの束縛を追う。"""

    tree = ast.parse(source)
    errors: list[str] = []
    forbidden = {"_restore_targets", "_purge_pycache", "_verify_originals"}
    definitions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if definitions & forbidden:
        errors.append("restore implementation was redefined")
    path_bindings = []
    harness_bindings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                names = [item.id for item in ast.walk(target) if isinstance(item, ast.Name)]
                if "harness_path" in names:
                    path_bindings.append(node.value)
                if "harness" in names:
                    harness_bindings.append(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "harness":
            harness_bindings.append(node.value)
    path_ok = len(path_bindings) == 1 and isinstance(path_bindings[0], ast.Call) and isinstance(path_bindings[0].func, ast.Name) and path_bindings[0].func.id == "_head_bytes"
    if not path_ok:
        errors.append("harness_path is not uniquely bound from HEAD bytes")
    load_ok = len(harness_bindings) == 1 and isinstance(harness_bindings[0], ast.Call) and isinstance(harness_bindings[0].func, ast.Name) and harness_bindings[0].func.id == "_load_source" and bool(harness_bindings[0].args) and isinstance(harness_bindings[0].args[0], ast.Name) and harness_bindings[0].args[0].id == "harness_path"
    if not load_ok:
        errors.append("harness is not uniquely bound from harness_path")
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_restore_targets"]
    if len(calls) != 1 or not isinstance(calls[0].func.value, ast.Name) or calls[0].func.value.id != "harness":
        errors.append("restore call is not unique on harness")
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"setattr", "monkeypatch"} for node in ast.walk(tree)):
        errors.append("runtime rebinding helper found")
    if any(isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and any(isinstance(target, ast.Attribute) and target.attr == "_restore_targets" for target in (node.targets if isinstance(node, ast.Assign) else [node.target])) for node in ast.walk(tree)):
        errors.append("restore attribute overwritten")
    return errors


def test_summarize_preserves_raw_max():
    summary = ANALYSIS.summarize_elapsed_ns([*range(1, 101), 10_000])
    assert summary["max_ns"] == 10_000
    assert summary["p99_ns"] == 100
    assert summary["max_ns"] != summary["p99_ns"]
    assert summary["p50_ns"] == 51
    assert summary["quantile_method"] == "nearest-rank"


@pytest.mark.parametrize("bad", [[], [True], [0], [-1], [1.5]])
def test_summarize_rejects_invalid_samples(bad):
    with pytest.raises((TypeError, ValueError)):
        ANALYSIS.summarize_elapsed_ns(bad)


def test_validate_arm_profile_accepts_registered_profile():
    profile = _registered_profile()
    assert ANALYSIS.validate_arm_profile(profile, dict(profile)) == {"valid": True, "reasons": []}


def test_validate_arm_profile_rejects_out_of_profile_case():
    profile = _registered_profile()
    result = ANALYSIS.validate_arm_profile(profile, {**profile, "E_by_parent": [143, 98], "E_total": 241})
    assert result["valid"] is False
    assert any("E_by_parent mismatch" in reason for reason in result["reasons"])


def test_validate_arm_profile_does_not_accept_bool_as_int():
    profile = _registered_profile()
    result = ANALYSIS.validate_arm_profile(profile, {**profile, "n": True})
    assert result["valid"] is False
    assert any("observed.n" in reason for reason in result["reasons"])


def test_any_failed_trial_invalidates_attempt():
    trials = [{"sequence": 0, "success": True, "restore_call_count": 1}, {"sequence": 1, "success": False, "restore_call_count": 1}, {"sequence": 2, "success": True, "restore_call_count": 1}]
    result = ANALYSIS.attempt_validity(trials)
    assert result["valid"] is False
    assert result["reasons"] == ["trials[1] did not succeed"]


def test_attempt_rejects_missing_sequence():
    trials = [{"success": True, "restore_call_count": 1}, {"success": True, "restore_call_count": 1}]
    result = ANALYSIS.attempt_validity(trials)
    assert result["valid"] is False
    assert result["reasons"] == ["trials[0].sequence must be a non-negative exact int", "trials[1].sequence must be a non-negative exact int"]


@pytest.mark.parametrize("call_count", [None, 0, 2, True, 1.0])
def test_attempt_rejects_bad_success_call_count(call_count):
    result = ANALYSIS.attempt_validity([{"sequence": 0, "success": True, "restore_call_count": call_count}])
    assert result["valid"] is False
    assert "restore_call_count" in result["reasons"][0]


def test_attempt_rejects_noncontiguous_sequence():
    trials = [{"sequence": 0, "success": True, "restore_call_count": 1}, {"sequence": 2, "success": True, "restore_call_count": 1}]
    result = ANALYSIS.attempt_validity(trials)
    assert result["valid"] is False
    assert result["reasons"] == ["trial sequences must be unique and contiguous from zero"]


def test_planning_allowance_applies_floor():
    assert ANALYSIS.planning_allowance_ns(1) == 1_000_000_001


def test_planning_allowance_uses_ceiling_half():
    assert ANALYSIS.planning_allowance_ns(3_000_000_001) == 4_500_000_002


def test_driver_calls_imported_restore_only():
    assert _restore_import_flow_violations(_DRIVER_PATH.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "fake_source",
    [
        "def _restore_targets(*x): pass\nharness_path=_head_bytes(repo, 'x')\nharness=_load_source(harness_path, raw, 'h')\nharness._restore_targets(root, originals)",
        "harness_path=_head_bytes(repo, 'x')\nharness=_load_source(harness_path, raw, 'h')\nharness=type('H',(),{})()\nharness._restore_targets(root, originals)",
        "harness_path=repo/'tools/mutation_harness.py'\nharness=_load_source(harness_path, raw, 'h')\nharness._restore_targets(root, originals)",
        "harness_path=_head_bytes(repo, 'x')\nharness=_load_source(other_path, raw, 'h')\nharness._restore_targets(root, originals)",
        "harness_path=_head_bytes(repo, 'x')\nharness=_load_source(harness_path, raw, 'h')\nharness._restore_targets(root, originals)\nharness._restore_targets(root, originals)",
    ],
)
def test_restore_import_flow_detector_rejects_fake_sources(fake_source):
    assert _restore_import_flow_violations(fake_source)


def test_driver_measurement_interval_wraps_only_restore_call():
    tree = ast.parse(_DRIVER_PATH.read_text(encoding="utf-8"))
    measure = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_measure_restore_call")
    expected = ast.parse(
        """started = time.perf_counter_ns()
try:
    harness._restore_targets(prepared[\"root\"], prepared[\"originals\"])
except BaseException as exc:
    return None, time.perf_counter_ns() - started, exc
return time.perf_counter_ns() - started, None, None
"""
    ).body
    assert [ast.dump(node, include_attributes=False) for node in measure.body] == [
        ast.dump(node, include_attributes=False) for node in expected
    ]


def test_driver_preregisters_interleaved_five_by_one_hundred_trials():
    tree = ast.parse(_DRIVER_PATH.read_text(encoding="utf-8"))
    assignments = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"ARM_ORDER", "ARM_LAYOUTS", "TRIALS_PER_ARM"}}
    assert assignments["ARM_ORDER"] == tuple(_FROZEN_ARMS)
    assert assignments["ARM_LAYOUTS"] == _FROZEN_ARMS
    assert assignments["TRIALS_PER_ARM"] == 100
    attempt = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_attempt")
    outer = next(node for node in attempt.body if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "index" and any(isinstance(child, ast.For) and isinstance(child.target, ast.Name) and child.target.id == "arm" for child in node.body))
    inner = next(node for node in outer.body if isinstance(node, ast.For))
    assert isinstance(inner.target, ast.Name) and inner.target.id == "arm"
    assert isinstance(inner.iter, ast.Name) and inner.iter.id == "ARM_ORDER"


def test_driver_is_disposable_and_literal():
    source = _DRIVER_PATH.read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 300
    assert all(token not in source for token in ("argparse", "rglob(", "glob(", "_select_restore_case", "planning_allowance"))
    assert "MX4-MX6-both-layers" in source and '"G1"' in source


def test_aged_profile_does_not_enumerate_cache_before_measurement():
    tree = ast.parse(_DRIVER_PATH.read_text(encoding="utf-8"))
    observed = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_observed")
    assert not any(isinstance(node, ast.Attribute) and node.attr == "iterdir" for node in ast.walk(observed))
    assert "ARM_LAYOUTS" not in ast.unparse(observed)
    attempt = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_attempt")
    aged_loop = next(node for node in attempt.body if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "index")
    aged_prepare = next(node for node in ast.walk(aged_loop) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_prepare")
    layout_call = next(node for node in ast.walk(attempt) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_layout")
    assert ast.literal_eval(aged_prepare.args[1]) == "A-e143-aged"
    assert ast.literal_eval(aged_prepare.args[4]) == "attempt-start"
    assert aged_loop.lineno < layout_call.lineno


def test_layout_is_taken_only_from_replica_tree():
    tree = ast.parse(_DRIVER_PATH.read_text(encoding="utf-8"))
    attempt = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_attempt")
    calls = [node for node in ast.walk(attempt) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_layout"]
    assert len(calls) == 1
    assert isinstance(calls[0].args[0], ast.Name) and calls[0].args[0].id == "replica"


def test_driver_evidence_excludes_planning_allowance():
    source = _DRIVER_PATH.read_text(encoding="utf-8")
    assert "planning_allowance" not in source


def test_required_layout_failure_is_fail_closed():
    assert DRIVER._layout_complete({"tag": {"available": True, "stdout": "stripe"}}) is True
    assert DRIVER._layout_complete({"tag": {"available": False, "stdout": ""}}) is False
    assert DRIVER._layout_complete({"tag": {"available": True, "stdout": ""}}) is False
    assert DRIVER._layout_complete({}) is False


def test_aged_setup_failure_preserves_actual_elapsed():
    record = DRIVER._trial(7, "A-e143-aged", 1, (RuntimeError("setup"), 123), Path("/unused"), {}, None, None)
    assert record["sequence"] == 7
    assert record["success"] is False
    assert record["restore_call_count"] == 0
    assert record["elapsed_until_error_ns"] == 123
    assert record["exception_type"] == "RuntimeError"


def test_pbs_uses_environment_interface_and_compute_guards():
    source = _PBS_PATH.read_text(encoding="utf-8")
    assert "#PBS -q gen_S" in source and "#PBS -b 1" in source
    assert "#PBS -l elapstim_req=00:30:00" in source
    assert '[[ "$node_name" =~ ^bnode[0-9]+$ ]]' in source
    assert '${PBS_JOBID:?' in source and '[[ "$scratch_fs" == lustre ]]' in source
    assert "(( $# == 0 ))" in source
    assert all(token not in source for token in ("$1", "${1", "$2", "${2", "$@", "$*"))
    assert 'mkdir "$attempt_root"' in source and 'mkdir "$evidence_dir"' in source
    assert "reject_symlink_chain" in source and "realpath -e" in source


def test_pbs_rechecks_five_arm_schema_and_required_layouts():
    source = _PBS_PATH.read_text(encoding="utf-8")
    for arm in _FROZEN_ARMS:
        assert arm in source
    assert "len(trials)==500" in source
    assert 'x.get("available") is True' in source
    assert 'd.get("R_restore_observed_by_arm",{})' in source


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-x"]))
