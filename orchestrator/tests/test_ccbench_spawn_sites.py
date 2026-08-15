# -*- coding: utf-8 -*-
"""Structural inventory for production CCBench process spawn sites."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
import sys

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from orchestrator.holdout_observation import (  # noqa: E402
    classify_minimal_holdout_signature,
)
from orchestrator.campaign import (  # noqa: E402
    backoff_profile,
    s1_verify_extime_calibration,
    s2_verify_calibration,
    s3_lock_coverage,
)

_PRODUCTION_DIRS = (
    _ROOT / "orchestrator" / "calibrator",
    _ROOT / "orchestrator" / "campaign",
)

_GATEWAY = Counter({("calibrator/runner.py", "run_once"): 1})

_DIRECT_SAFE_ALLOWLIST = Counter({
    # Production passes CALIBRATION_FLAGS, whose frozen read ratio is rr95.
    ("campaign/s1_verify_extime_calibration.py", "_run_once"): 1,
    # Production passes the module-level S2_FLAGS, fixed at rr50.
    ("campaign/s2_verify_calibration.py", "_run_once"): 1,
    # Both module-level SINGLE_FLAGS and HIGH_FLAGS are fixed at rr50.
    ("campaign/s3_lock_coverage.py", "_run_trace"): 1,
    # Production main reaches _profile_run only through POINTS (rr5 and rr50).
    ("campaign/backoff_profile.py", "_profile_run"): 1,
})

# These binary-argument subprocesses are correctness/diagnostic paths rather
# than throughput observation sites.  Keeping them in the candidate inventory
# still makes additions or moves fail until they receive an explicit review.
_NON_OBSERVATION_SITES = Counter({
    # Executes nm against a caller-supplied binary; it does not execute CCBench.
    ("calibrator/cli.py", "_assert_trace_disabled_binary"): 1,
    # Correctness trace witness owned by pipeline's verifier path.
    ("campaign/pipeline.py", "_run_trace"): 1,
    # Fixed rr50 permutation-coverage correctness trace.
    ("campaign/s5_permutation_coverage.py", "_run_trace"): 1,
    # Fixed rr50 trigger-coverage correctness trace.
    ("campaign/s8a_trigger_coverage.py", "_run_trace"): 1,
    # Fixed diagnostic points used only to tally trace abort reasons.
    ("campaign/s8a_trigger_freq.py", "_run_freq"): 1,
    # Executes nm against the binary; it does not execute CCBench.
    ("campaign/buildcache.py", "_assert_no_trace_symbols"): 1,
})


def _references_binary(
    node: ast.AST,
    assignments: dict[str, list[ast.AST]],
    seen: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(node, ast.Name):
        if node.id == "binary":
            return True
        if node.id in seen:
            return False
        return any(
            _references_binary(value, assignments, seen | {node.id})
            for value in assignments.get(node.id, [])
        )
    return any(_references_binary(child, assignments, seen)
               for child in ast.iter_child_nodes(node))


def _binary_spawn_candidates() -> Counter[tuple[str, str]]:
    sites: Counter[tuple[str, str]] = Counter()
    for directory in _PRODUCTION_DIRS:
        prefix = directory.name
        for path in sorted(directory.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for function in (
                node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ):
                positional = [*function.args.posonlyargs, *function.args.args]
                positional_defaults = [None] * (
                    len(positional) - len(function.args.defaults)
                ) + list(function.args.defaults)
                defaults = {
                    argument.arg: default
                    for argument, default in zip(positional, positional_defaults)
                    if default is not None
                }
                defaults.update({
                    argument.arg: default
                    for argument, default in zip(
                        function.args.kwonlyargs, function.args.kw_defaults
                    )
                    if default is not None
                })
                subprocess_runner_names = {
                    name for name, default in defaults.items()
                    if isinstance(default, ast.Attribute)
                    and isinstance(default.value, ast.Name)
                    and default.value.id == "subprocess"
                    and default.attr in {"run", "Popen", "check_call", "check_output"}
                }
                assignments: dict[str, list[ast.AST]] = {}
                for node in ast.walk(function):
                    if isinstance(node, (ast.Assign, ast.AnnAssign)):
                        value = node.value
                        targets = (node.targets if isinstance(node, ast.Assign)
                                   else [node.target])
                        for target in targets:
                            if isinstance(target, ast.Name) and value is not None:
                                assignments.setdefault(target.id, []).append(value)
                for call in (node for node in ast.walk(function)
                             if isinstance(node, ast.Call) and node.args):
                    is_direct = (
                        isinstance(call.func, ast.Attribute)
                        and isinstance(call.func.value, ast.Name)
                        and call.func.value.id == "subprocess"
                        and call.func.attr in {"run", "Popen", "check_call", "check_output"}
                    )
                    is_injected_runner = (
                        isinstance(call.func, ast.Name)
                        and call.func.id in subprocess_runner_names
                    )
                    if ((is_direct or is_injected_runner)
                            and _references_binary(call.args[0], assignments)):
                        sites[(f"{prefix}/{path.name}", function.name)] += 1
    return sites


def _flags(mapping) -> list[str]:
    return [f"-{key}={value}" for key, value in mapping.items()]


def test_production_binary_spawn_inventory_is_closed():
    expected = _GATEWAY + _DIRECT_SAFE_ALLOWLIST + _NON_OBSERVATION_SITES
    assert _binary_spawn_candidates() == expected


def test_every_throughput_spawn_uses_gateway_or_safe_constant_allowlist():
    observed = _binary_spawn_candidates() - _NON_OBSERVATION_SITES
    assert observed == _GATEWAY + _DIRECT_SAFE_ALLOWLIST


def test_direct_spawn_allowlist_constants_cannot_reach_protected_ratios():
    assert classify_minimal_holdout_signature(
        _flags(s1_verify_extime_calibration.CALIBRATION_FLAGS)
    ) is None
    assert classify_minimal_holdout_signature(
        _flags(s2_verify_calibration.S2_FLAGS)
    ) is None
    assert classify_minimal_holdout_signature(
        _flags(s3_lock_coverage.SINGLE_FLAGS)
    ) is None
    assert classify_minimal_holdout_signature(
        _flags(s3_lock_coverage.HIGH_FLAGS)
    ) is None
    assert {
        point[1]["ycsb_rratio"] for point in backoff_profile.POINTS
    } == {"5", "50"}
    assert all(
        classify_minimal_holdout_signature(_flags(workload)) is None
        for _name, workload in backoff_profile.POINTS
    )


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
