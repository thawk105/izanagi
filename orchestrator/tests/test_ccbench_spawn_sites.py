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

_GATEWAY = Counter({("calibrator/runner.py", "<module>.run_once"): 1})

_DIRECT_SAFE_ALLOWLIST = Counter({
    # Production passes CALIBRATION_FLAGS, whose frozen read ratio is rr95.
    ("campaign/s1_verify_extime_calibration.py", "<module>._run_once"): 1,
    # Production passes the module-level S2_FLAGS, fixed at rr50.
    ("campaign/s2_verify_calibration.py", "<module>._run_once"): 1,
    # Both module-level SINGLE_FLAGS and HIGH_FLAGS are fixed at rr50.
    ("campaign/s3_lock_coverage.py", "<module>._run_trace"): 1,
    # Public profile paths runtime-reject protected ratios before build/profile.
    ("campaign/backoff_profile.py", "<module>._profile_run"): 1,
})

_DIRECT_CCBENCH_DIAGNOSTIC_SITES = Counter({
    # Correctness trace witness owned by pipeline's verifier path.
    ("campaign/pipeline.py", "<module>._run_trace"): 1,
    # Fixed rr50 permutation-coverage correctness trace.
    ("campaign/s5_permutation_coverage.py", "<module>._run_trace"): 1,
    # Fixed rr50 trigger-coverage correctness trace.
    ("campaign/s8a_trigger_coverage.py", "<module>._run_trace"): 1,
    # Fixed diagnostic points used only to tally trace abort reasons.
    ("campaign/s8a_trigger_freq.py", "<module>._run_freq"): 1,
})

# Every other reviewed launch is an explicit non-CCBench exclusion.  This is
# intentionally a site inventory, not a command-expression heuristic: a new
# launch must be classified in review before this test can pass.
_EXPLICIT_NON_CCBENCH_PROCESS_SITES = Counter({
    ("calibrator/cli.py", "<module>._assert_trace_disabled_binary"): 1,
    ("calibrator/perf_preflight.py", "<module>.probe_perf_availability"): 1,
    ("calibrator/runner.py", "<module>.competing_bench_pids"): 1,
    ("calibrator/runner.py", "<module>.composite_competing_probe"): 2,
    ("calibrator/tsc.py", "<module>._build_helper"): 1,
    ("calibrator/tsc.py", "<module>.measure_tsc"): 1,
    ("campaign/artifact_admission.py", "<module>._git_snapshot_sha256"): 1,
    ("campaign/backoff_profile.py", "<module>._profile_run"): 1,
    ("campaign/buildcache.py", "<module>._assert_no_trace_symbols"): 1,
    ("campaign/buildcache.py", "<module>._run"): 1,
    ("campaign/buildcache.py", "<module>._tool_version"): 1,
    ("campaign/buildcache.py", "<module>._tool_version_full"): 1,
    # Runs only `git ... rev-parse --show-toplevel --verify HEAD` to bind the
    # FetchContent dependency receipt; argv cannot name or execute CCBench.
    ("campaign/buildcache.py", "<module>._observe_fetchcontent_dependency_receipt"): 1,
    ("campaign/buildcache.py", "<module>._verify_ccbench_commit"): 1,
    ("campaign/certified_writer_admission.py", "<module>._git"): 1,
    ("campaign/certified_writer_preflight.py", "<module>._committed_blob"): 1,
    ("campaign/contract_loader_binding.py", "<module>._run_git"): 1,
    ("campaign/floor_liveness.py", "<module>.classify"): 1,
    ("campaign/layer3_report.py", "<module>._git_head"): 1,
    ("campaign/patchharness.py", "<module>._git"): 1,
    ("campaign/patchharness.py", "<module>._git_repository_identity"): 1,
    ("campaign/queue_state.py", "<module>._run_qstat_bounded"): 1,
    ("campaign/reflux_origin_ledger.py", "<module>._git"): 1,
    ("campaign/reflux_source_closure.py", "<module>._git"): 1,
    ("campaign/s1_known_axes_freeze.py", "<module>._run_git"): 1,
    ("campaign/s1_measurement_freeze.py", "<module>._run_git"): 1,
    ("campaign/s1_report.py", "<module>._git_head"): 1,
    ("campaign/s1_verify_extime_calibration.py", "<module>._verifier_run"): 1,
    ("campaign/s2_verify_calibration.py", "<module>._broken_build_and_verify"): 1,
    ("campaign/s2_verify_calibration.py", "<module>._run_cmake_build"): 1,
    ("campaign/s2_verify_calibration.py", "<module>._verifier_run"): 1,
    ("campaign/s3_lock_coverage.py", "<module>._build_broken"): 1,
    ("campaign/s3_lock_coverage.py", "<module>._run_cmake_build"): 1,
    ("campaign/s3_lock_coverage.py", "<module>._verify"): 1,
    ("campaign/s5_permutation_coverage.py", "<module>._build_broken"): 1,
    ("campaign/s5_permutation_coverage.py", "<module>._run_cmake_build"): 1,
    ("campaign/s5_permutation_coverage.py", "<module>._verify"): 1,
    ("campaign/s6_canary_rename.py", "<module>.export_stock"): 3,
    ("campaign/s6_canary_rename.py", "<module>.git_apply"): 1,
    ("campaign/s6_canary_rename.py", "<module>.normalize_cxx"): 1,
    ("campaign/s6_canary_rename.py", "<module>.verify"): 1,
    ("campaign/s6_proposal_rounds.py", "<module>.call_headless"): 1,
    ("campaign/s6_proposal_rounds.py", "<module>.cmd_freeze"): 1,
    ("campaign/s6_proposal_rounds.py", "<module>.freshness_check"): 2,
    ("campaign/s8a_trigger_coverage.py", "<module>._build"): 1,
    ("campaign/s8a_trigger_coverage.py", "<module>._run_cmake_build"): 1,
    ("campaign/s8a_trigger_coverage.py", "<module>._verify"): 1,
    ("campaign/s8a_trigger_freq.py", "<module>._run_freq"): 1,
    ("campaign/s8b_floor_campaign.py", "<module>._ccbench_gitlink"): 1,
    ("campaign/s8b_floor_campaign.py", "<module>._default_probe_fn"): 1,
    ("campaign/s8b_floor_campaign.py", "<module>._observe_floor_tool"): 1,
    ("campaign/s8b_floor_campaign.py", "<module>._pre_oracle_blob"): 2,
    ("campaign/s8b_floor_campaign.py", "<module>._verify_floor_oracle_dependency_source"): 1,
    ("campaign/s8b_holdout_admission.py", "<module>._run_git"): 1,
    ("campaign/s8b_holdout_freeze.py", "<module>._run_git"): 1,
    ("campaign/s8b_holdout_freeze.py", "<module>._run_git_bytes"): 1,
    ("campaign/s8b_holdout_freeze.py", "<module>._run_git_z"): 1,
    ("campaign/s8b_prediction_runner.py", "<module>._git_bytes"): 1,
    ("campaign/s8b_ratified_freeze.py", "<module>._git"): 1,
    ("campaign/s8b_ratified_freeze.py", "<module>._git_ok"): 1,
    ("campaign/s8b_selector_freeze.py", "<module>._verify_commit_pin"): 1,
    ("campaign/s8c_acceptance_receipt.py", "<module>._git"): 1,
    ("campaign/s8c_preregistration.py", "<module>._git"): 1,
    ("campaign/silo_ladder_rung1.py", "<module>._run"): 2,
    ("campaign/sort_swo_oracle.py", "<module>._compile"): 1,
    ("campaign/sort_swo_oracle.py", "<module>._compiler_version"): 1,
    ("campaign/sort_swo_oracle.py", "<module>._run_matrix"): 1,
    ("campaign/source_digest.py", "<module>._cpp_normalize"): 1,
    ("campaign/source_digest.py", "<module>._dump_macros"): 1,
    ("campaign/source_digest.py", "<module>._git_show"): 1,
    ("campaign/source_digest.py", "<module>._tracked_diff_sha256"): 1,
    ("campaign/source_digest.py", "<module>._tracked_status_paths"): 1,
    ("campaign/t080_freeze_migration.py", "<module>._git"): 1,
    ("campaign/t080_freeze_migration.py", "<module>._git_rc"): 1,
    ("campaign/t152_write_intent_coverage.py", "<module>._run_process"): 1,
    ("campaign/t152_write_intent_coverage.py", "<module>._verify"): 1,
    ("campaign/t810_validator.py", "<module>._git"): 1,
    ("campaign/trial_registry.py", "<module>._git"): 1,
})


_PROCESS_APIS = {
    "subprocess": {
        "run", "Popen", "call", "check_call", "check_output",
        "getoutput", "getstatusoutput",
    },
    "asyncio": {"create_subprocess_exec", "create_subprocess_shell"},
    "os": {
        "system", "popen", "spawnl", "spawnle", "spawnlp", "spawnlpe",
        "spawnv", "spawnve", "spawnvp", "spawnvpe",
    },
}


def _is_process_callable(
    node: ast.AST,
    imported: set[str],
    module_aliases: dict[str, str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in imported
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.attr in _PROCESS_APIS.get(
            module_aliases.get(node.value.id, node.value.id), set(),
        )
    )


class _ProcessLaunchVisitor(ast.NodeVisitor):
    """Enumerate reviewed process APIs before deciding whether they run CCBench."""

    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.imported: set[str] = set()
        self.module_aliases: dict[str, str] = {}
        self.scopes = ["<module>"]
        self.injected = [set()]
        self.sites: Counter[tuple[str, str]] = Counter()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name in _PROCESS_APIS:
                self.module_aliases[alias.asname or alias.name] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module in _PROCESS_APIS:
            for alias in node.names:
                if alias.name in _PROCESS_APIS[node.module]:
                    self.imported.add(alias.asname or alias.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scopes.append(node.name)
        self.generic_visit(node)
        self.scopes.pop()

    def _visit_function(self, node) -> None:
        positional = [*node.args.posonlyargs, *node.args.args]
        positional_defaults = [None] * (
            len(positional) - len(node.args.defaults)
        ) + list(node.args.defaults)
        defaults = [
            (argument.arg, default)
            for argument, default in zip(positional, positional_defaults)
            if default is not None
        ]
        defaults.extend(
            (argument.arg, default)
            for argument, default in zip(
                node.args.kwonlyargs, node.args.kw_defaults,
            )
            if default is not None
        )
        local_injected = set(self.injected[-1])
        local_injected.update(
            name for name, default in defaults
            if _is_process_callable(default, self.imported, self.module_aliases)
        )
        self.scopes.append(node.name)
        self.injected.append(local_injected)
        self.generic_visit(node)
        self.injected.pop()
        self.scopes.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    def visit_Call(self, node: ast.Call) -> None:
        is_injected = (
            isinstance(node.func, ast.Name)
            and node.func.id in self.injected[-1]
        )
        if (_is_process_callable(
                node.func, self.imported, self.module_aliases)
                or is_injected):
            self.sites[(self.relative_path, ".".join(self.scopes))] += 1
        self.generic_visit(node)


def _process_launch_sites(
    directories: tuple[Path, ...] = _PRODUCTION_DIRS,
    *, orchestrator_root: Path = _ROOT / "orchestrator",
) -> Counter[tuple[str, str]]:
    sites: Counter[tuple[str, str]] = Counter()
    for directory in directories:
        for path in sorted(directory.rglob("*.py")):
            relative = path.relative_to(orchestrator_root).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            visitor = _ProcessLaunchVisitor(relative)
            visitor.visit(tree)
            sites.update(visitor.sites)
    return sites


def _flags(mapping) -> list[str]:
    return [f"-{key}={value}" for key, value in mapping.items()]


def test_reviewed_process_launch_inventory_is_recursive_and_exact():
    expected = (
        _GATEWAY
        + _DIRECT_SAFE_ALLOWLIST
        + _DIRECT_CCBENCH_DIAGNOSTIC_SITES
        + _EXPLICIT_NON_CCBENCH_PROCESS_SITES
    )
    assert _process_launch_sites() == expected


def test_reviewed_ccbench_measurement_launches_use_bounded_sites():
    observed = (
        _process_launch_sites()
        - _EXPLICIT_NON_CCBENCH_PROCESS_SITES
        - _DIRECT_CCBENCH_DIAGNOSTIC_SITES
    )
    assert observed == _GATEWAY + _DIRECT_SAFE_ALLOWLIST


def test_process_inventory_catches_nested_exe_attribute_and_hardcoded_shapes(
    tmp_path,
):
    nested = tmp_path / "campaign" / "nested"
    nested.mkdir(parents=True)
    fixture = nested / "driver.py"
    fixture.write_text(
        "import subprocess as sp\n"
        "def launch(exe, cfg):\n"
        "    sp.run([exe, '--ycsb_rratio=80'])\n"
        "    sp.Popen([cfg.binary, '--ycsb_rratio=80'])\n"
        "    sp.check_call(['/opt/ccbench/ycsb_silo', "
        "'--ycsb_rratio=80'])\n",
        encoding="utf-8",
    )
    assert _process_launch_sites(
        (tmp_path / "campaign",), orchestrator_root=tmp_path,
    ) == Counter({("campaign/nested/driver.py", "<module>.launch"): 3})


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


@pytest.mark.parametrize("ratio", ["20", "80"])
def test_backoff_profile_public_path_rejects_protected_ratio_before_build(
    monkeypatch, ratio,
):
    effects = []
    monkeypatch.setattr(
        backoff_profile, "_genome",
        lambda *_args, **_kwargs: effects.append("genome"),
    )
    with pytest.raises(RuntimeError, match="admission required"):
        backoff_profile.profile_point(
            2,
            {
                "ycsb_rratio": ratio,
            },
        )
    assert effects == []


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
