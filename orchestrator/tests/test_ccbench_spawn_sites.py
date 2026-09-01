# -*- coding: utf-8 -*-
"""Structural inventory for production CCBench process spawn sites."""
from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import sys

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from orchestrator.holdout_observation import (  # noqa: E402
    classify_minimal_holdout_signature,
)
from orchestrator.campaign import (  # noqa: E402
    backoff_profile,
    condition_meaning_gate,
    s1_verify_extime_calibration,
    s2_verify_calibration,
    s3_lock_coverage,
)

_PRODUCTION_DIRS = (
    _ROOT / "orchestrator" / "calibrator",
    _ROOT / "orchestrator" / "campaign",
)

_GATEWAY = Counter({("calibrator/runner.py", "<module>.run_once"): 1})

# Direct clients of the bounded run_once gateway are a separate exact
# inventory from the subprocess site itself.  This keeps measurement callers
# visible without misclassifying them as additional raw process launch sites.
_BOUNDED_RUN_ONCE_CLIENTS = Counter({
    ("campaign/b10_backoff_shape_sweep.py", "<module>.measure_performance_cell"): 1,
    ("campaign/backoff_overthrottle.py", "<module>._run_rep"): 1,
})

_DIRECT_SAFE_ALLOWLIST = Counter({
    # Fixed probe binary argv, required measurement-site admission, and a
    # bounded timeout; the probe harness does not accept YCSB ratio flags.
    ("campaign/b10_backoff_shape_sweep.py", "<module>._measure_probe_binary"): 1,
    # Current callers pass only read-only Git worktree identity/status queries;
    # no shell expansion occurs and the argv never names or runs CCBench.
    ("campaign/backoff_extended_sweep.py", "<module>._git_worktree_output"): 1,
    # Production passes CALIBRATION_FLAGS, whose frozen read ratio is rr95.
    ("campaign/s1_verify_extime_calibration.py", "<module>._run_once"): 1,
    # Production passes the module-level S2_FLAGS, fixed at rr50.
    ("campaign/s2_verify_calibration.py", "<module>._run_once"): 1,
    # Both module-level SINGLE_FLAGS and HIGH_FLAGS are fixed at rr50.
    ("campaign/s3_lock_coverage.py", "<module>._run_trace"): 1,
    # Public profile paths runtime-reject protected ratios before build/profile.
    ("campaign/backoff_profile.py", "<module>._profile_run"): 1,
    # Fixed argv, no shell expansion, sanitized env, read-only Git tree query.
    ("campaign/s8b_floor_campaign.py", "<module>._floor_protocol_paths_at_commit"): 1,
})

_DIRECT_CCBENCH_DIAGNOSTIC_SITES = Counter({
    # Fixed balanced argv under the compute-site bench lock, shell disabled,
    # and a mandatory timeout; stdout is diagnostic-only requested-us data.
    ("campaign/backoff_requested_us.py", "<module>._run_rep"): 1,
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
    # Fixed Git argv with a sanitized environment; these probes only bind the
    # registered B10 preregistration/current repository state.
    ("campaign/b10_backoff_shape_sweep.py", "<module>._git"): 1,
    ("campaign/b10_backoff_shape_sweep.py", "<module>.load_preregistration"): 1,
    # Builds and identifies the standalone probe harness/toolchain only; the
    # realized-wait measurement binary is launched at the reviewed site above.
    ("campaign/b10_backoff_shape_sweep.py", "<module>._run_probe_command"): 1,
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
    # Non-CCBench standalone condition-meaning compiler/decoder: fixed compiler
    # argv or a generated decoder binary argv, no shell, 120-second timeout.
    ("campaign/condition_meaning_gate.py", "<module>._run_process"): 1,
    ("campaign/contract_loader_binding.py", "<module>._run_git"): 1,
    ("campaign/floor_liveness.py", "<module>.classify"): 1,
    ("campaign/layer3_report.py", "<module>._git_head"): 1,
    # Fixed OpenSSL Ed25519 signature verification for an external pin;
    # its argv cannot name or execute CCBench.
    ("campaign/mocc_trace_pair_anchor.py", "<module>._verify_ed25519_signature"): 1,
    ("campaign/patchharness.py", "<module>._git"): 1,
    ("campaign/patchharness.py", "<module>._git_repository_identity"): 1,
    # Read-only Git HEAD/status/blob probes bind the A-1 measurement source.
    ("campaign/paper_story_a1_paired.py", "<module>._run_git"): 1,
    # Fixed `git -C <checkout> rev-parse/status` argv, no shell expansion,
    # exact 10-second timeout; this metadata gate never executes CCBench.
    (
        "campaign/pipeline.py",
        "<module>._require_canonical_build_source_state._git",
    ): 1,
    # Exact scheduler submission argv; CCBench remains compute-job-owned.
    ("campaign/paper_story_a1_paired.py", "<module>._run_qsub"): 1,
    # Login-side qstat observations never name a CCBench binary.
    ("campaign/paper_story_a1_paired.py", "<module>._observe_qstat_visibility"): 1,
    ("campaign/paper_story_a1_paired.py", "<module>._observe_scheduler_terminal"): 1,
    # Read-only Git HEAD/status probes bind the driver worktree; neither
    # command names or executes a CCBench binary.
    ("campaign/paper_story_a2_certification.py", "<module>.compute_preflight"): 2,
    # Login-side terminal qstat observation; it never names a CCBench binary.
    ("campaign/paper_story_a2_certification.py", "<module>.finish_group"): 1,
    # Exact scheduler submission argv; CCBench remains compute-job-owned.
    ("campaign/paper_story_a2_certification.py", "<module>.exact_qsub"): 1,
    # Read-only Git HEAD resolve, canonical pin resolve, and tracked-status
    # probes bind the delegated source tree; none executes CCBench.
    ("campaign/paper_story_a2_certification.py", "<module>.run_workload"): 3,
    # Fixed Git executable and fixed allow-list environment run read-only
    # repository-binding queries; argv never names or executes CCBench.
    ("campaign/p3_b4_admission_record.py", "<module>._git_call"): 1,
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
    # Sanitized read-only `git ... ls-tree -z ...` and `git ... cat-file blob`
    # bind the lineage blob; neither argv names nor executes CCBench.
    ("campaign/s8b_floor_campaign.py", "<module>._head_blob_100644"): 2,
    # Sanitized read-only `git ... rev-parse --verify HEAD^{commit}` binds the
    # lineage commit; its argv neither names nor executes CCBench.
    ("campaign/s8b_floor_campaign.py", "<module>._head_commit_oid"): 1,
    ("campaign/s8b_floor_campaign.py", "<module>._observe_floor_tool"): 1,
    ("campaign/s8b_floor_campaign.py", "<module>._pre_oracle_blob"): 2,
    ("campaign/s8b_floor_campaign.py", "<module>._verify_floor_oracle_dependency_source"): 1,
    # Sanitized read-only Git identity/status probes for staged dependencies;
    # neither command names nor executes CCBench.
    ("campaign/s8b_floor_campaign.py", "<module>._verify_pristine_floor_dependency_sources"): 2,
    # Fixed pgrep competition probe; argv cannot name or execute CCBench.
    ("campaign/s8b_floor_attempt_launcher.py", "<module>._owned_post_probe"): 1,
    ("campaign/s8b_holdout_admission.py", "<module>._run_git"): 1,
    ("campaign/s8b_holdout_freeze.py", "<module>._run_git"): 1,
    ("campaign/s8b_holdout_freeze.py", "<module>._run_git_bytes"): 1,
    ("campaign/s8b_holdout_freeze.py", "<module>._run_git_z"): 1,
    # Read-only git identity queries; argv cannot name or execute CCBench.
    ("campaign/s8b_oracle_n_pilot.py", "<module>._git_output"): 1,
    # Observes compiler and CMake versions only; never invokes a CCBench binary.
    ("campaign/s8b_oracle_n_pilot.py", "<module>._observe_toolchain"): 1,
    ("campaign/s8b_prediction_runner.py", "<module>._git_bytes"): 1,
    ("campaign/s8b_ratified_freeze.py", "<module>._git"): 1,
    ("campaign/s8b_ratified_freeze.py", "<module>._git_ok"): 1,
    ("campaign/s8b_selector_freeze.py", "<module>._verify_commit_pin"): 1,
    ("campaign/s8c_acceptance_receipt.py", "<module>._git"): 1,
    ("campaign/s8c_preregistration.py", "<module>._git"): 1,
    ("campaign/silo_ladder_rung1.py", "<module>._run"): 2,
    # Sanitized read-only Git root/HEAD and tracked-path queries; neither argv
    # names nor executes CCBench.
    ("campaign/sort_swo_dependency_material.py", "<module>._run_git"): 1,
    ("campaign/sort_swo_oracle.py", "<module>._compile"): 1,
    ("campaign/sort_swo_oracle.py", "<module>._compiler_version"): 1,
    # Compiler -M scan only emits dependencies; -I paths do not run CCBench.
    ("campaign/sort_swo_oracle.py", "<module>._dependency_manifest_closure"): 1,
    ("campaign/sort_swo_oracle.py", "<module>._run_matrix"): 1,
    # Read-only Git metadata queries use fixed argv and a sanitized environment.
    ("campaign/source_digest.py", "<module>._checkout_gitlink_oid"): 2,
    ("campaign/source_digest.py", "<module>._cpp_normalize"): 1,
    ("campaign/source_digest.py", "<module>._dump_macros"): 1,
    ("campaign/source_digest.py", "<module>._git_show"): 1,
    ("campaign/source_digest.py", "<module>._git_tree_entries"): 1,
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


class _BoundedRunOnceClientVisitor(ast.NodeVisitor):
    """Enumerate direct clients of calibrator.runner.run_once."""

    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.aliases: set[str] = set()
        self.scopes = ["<module>"]
        self.sites: Counter[tuple[str, str]] = Counter()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module not in {"calibrator.runner", "orchestrator.calibrator.runner"}:
            return
        for alias in node.names:
            if alias.name == "run_once":
                self.aliases.add(alias.asname or alias.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scopes.append(node.name)
        self.generic_visit(node)
        self.scopes.pop()

    def _visit_function(self, node) -> None:
        self.scopes.append(node.name)
        self.generic_visit(node)
        self.scopes.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in self.aliases:
            self.sites[(self.relative_path, ".".join(self.scopes))] += 1
        self.generic_visit(node)


def _bounded_run_once_client_sites(
    directories: tuple[Path, ...] = _PRODUCTION_DIRS,
    *, orchestrator_root: Path = _ROOT / "orchestrator",
) -> Counter[tuple[str, str]]:
    sites: Counter[tuple[str, str]] = Counter()
    for directory in directories:
        for path in sorted(directory.rglob("*.py")):
            relative = path.relative_to(orchestrator_root).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            visitor = _BoundedRunOnceClientVisitor(relative)
            visitor.visit(tree)
            sites.update(visitor.sites)
    return sites


_CALIBRATION_ISSUER_MODULE = "orchestrator.holdout_observation"
_CALIBRATION_ISSUER_NAME = (
    "_issue_calibration_observation_capability_from_receipt"
)


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return None if parent is None else parent + "." + node.attr
    return None


class _CalibrationIssuerVisitor(ast.NodeVisitor):
    """Find direct issuer imports/calls without changing spawn inventory.

    Dynamic paths, including assignment-based alias tracking and
    ``getattr``/``importlib``/``eval`` access (変数代入等を含む), are outside this
    visitor's scope.  This is limited to partial detection of accidental
    production call-site inclusion, not a complete dynamic call-graph check.
    """

    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.scopes = ["<module>"]
        self.issuer_aliases: set[str] = set()
        self.module_aliases: dict[str, str] = {}
        self.calls: Counter[tuple[str, str]] = Counter()
        self.imports: Counter[tuple[str, str]] = Counter()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound = alias.asname or alias.name.split(".", 1)[0]
            self.module_aliases[bound] = alias.name
            if alias.name == _CALIBRATION_ISSUER_MODULE:
                self.imports[(self.relative_path, ".".join(self.scopes))] += 1

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "orchestrator":
            for alias in node.names:
                if alias.name == "holdout_observation":
                    self.module_aliases[alias.asname or alias.name] = (
                        _CALIBRATION_ISSUER_MODULE
                    )
        if node.module != _CALIBRATION_ISSUER_MODULE:
            return
        for alias in node.names:
            if alias.name == _CALIBRATION_ISSUER_NAME:
                self.issuer_aliases.add(alias.asname or alias.name)
                self.imports[(self.relative_path, ".".join(self.scopes))] += 1

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scopes.append(node.name)
        self.generic_visit(node)
        self.scopes.pop()

    def _visit_function(self, node) -> None:
        self.scopes.append(node.name)
        self.generic_visit(node)
        self.scopes.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    def _is_issuer_call(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self.issuer_aliases
        if not isinstance(node, ast.Attribute) or node.attr != _CALIBRATION_ISSUER_NAME:
            return False
        qualified = _qualified_name(node.value)
        if qualified == _CALIBRATION_ISSUER_MODULE:
            return True
        if qualified is None:
            return False
        for alias, module in self.module_aliases.items():
            if qualified == alias and module == _CALIBRATION_ISSUER_MODULE:
                return True
            if (module == "orchestrator"
                    and qualified == alias + ".holdout_observation"):
                return True
        return False

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_issuer_call(node.func):
            self.calls[(self.relative_path, ".".join(self.scopes))] += 1
        self.generic_visit(node)


def _calibration_issuer_sites(
    directories: tuple[Path, ...] = _PRODUCTION_DIRS,
    *, orchestrator_root: Path = _ROOT / "orchestrator",
) -> tuple[Counter[tuple[str, str]], Counter[tuple[str, str]]]:
    calls: Counter[tuple[str, str]] = Counter()
    imports: Counter[tuple[str, str]] = Counter()
    for directory in directories:
        for path in sorted(directory.rglob("*.py")):
            relative = path.relative_to(orchestrator_root).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            visitor = _CalibrationIssuerVisitor(relative)
            visitor.visit(tree)
            calls.update(visitor.calls)
            imports.update(visitor.imports)
    return calls, imports


def _flags(mapping) -> list[str]:
    return [f"-{key}={value}" for key, value in mapping.items()]


_PATCH_DIR = _ROOT / "patches"
_BUILD_SCAN_PATHS = (
    _ROOT / "orchestrator" / "campaign",
    _ROOT / "tools" / "pegasus",
)
_BUILD_BACKEND_PATHS = frozenset({
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/condition_meaning_gate.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
})
_DEFINE_TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9_]*\b")
_CACHE_TO_TU_RE = re.compile(
    r"\b([A-Z][A-Z0-9_]*)\s*=\s*\$\{(CCBENCH_[A-Z0-9_]+)\}"
)
_CMAKE_INTERFACE_RE = re.compile(
    r"\b(?:set|option|get_filename_component)\s*\(\s*"
    r"(CCBENCH_[A-Z0-9_]+)\b"
)
_PREPROCESSOR_CONDITION_RE = re.compile(
    r"^\s*#\s*(?:if|ifdef|ifndef|elif)\b(.*)$"
)
_CMAKE_LITERAL_VALUE_RE = re.compile(
    r"\bset\s*\([^\n)]*\s([A-Z][A-Z0-9_]*)\s*\)"
)
_CMAKE_INTERNAL_DEFINE_RE = re.compile(
    r"\btarget_compile_definitions\s*\((.*?)\)", re.DOTALL,
)


def _patch_added_define_interfaces(
    patch_dir: Path = _PATCH_DIR,
) -> tuple[dict[str, frozenset[str]], frozenset[str]]:
    """Derive externally supplied TU defines from patch additions.

    Cache-option interfaces are discovered from the CMake cache-to-TU
    assignment shape.  Bare conditional interfaces are discovered from new
    preprocessor conditions; patch-internal target definitions and CMake
    marker values are removed structurally.  No DEFINE_SPECS key participates
    in candidate discovery.
    """

    patch_paths = sorted(patch_dir.glob("*.patch"))
    global_prior_tokens: set[str] = set()
    for path in patch_paths:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                continue
            if raw_line.startswith((
                "---", "@@", "diff ", "index ", "new file ",
                "deleted file ", "similarity ", "rename ",
            )):
                continue
            line = raw_line[1:] if raw_line.startswith((" ", "-")) else raw_line
            global_prior_tokens.update(_DEFINE_TOKEN_RE.findall(line))

    sources: dict[str, set[str]] = {}
    non_tu_interfaces: set[str] = set()
    for path in patch_paths:
        added: list[str] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                added.append(raw_line[1:])

        patch_rel = path.relative_to(_ROOT).as_posix()
        added_text = "\n".join(added)
        mapped: dict[str, str] = {
            macro: cache_name
            for macro, cache_name in _CACHE_TO_TU_RE.findall(added_text)
        }
        for macro in mapped:
            sources.setdefault(macro, set()).add(patch_rel)

        internal_defines: set[str] = set()
        for block in _CMAKE_INTERNAL_DEFINE_RE.findall(added_text):
            internal_defines.update(_DEFINE_TOKEN_RE.findall(block))
        cmake_marker_values = set(
            _CMAKE_LITERAL_VALUE_RE.findall(added_text)
        )
        for line in added:
            match = _PREPROCESSOR_CONDITION_RE.match(line)
            if match is None:
                continue
            for macro in _DEFINE_TOKEN_RE.findall(match.group(1)):
                if (
                    macro not in global_prior_tokens
                    and macro not in internal_defines
                    and macro not in cmake_marker_values
                ):
                    sources.setdefault(macro, set()).add(patch_rel)

        declared_cache = set(_CMAKE_INTERFACE_RE.findall(added_text))
        non_tu_interfaces.update(
            declared_cache.difference(mapped.values())
        )

    return (
        {macro: frozenset(paths) for macro, paths in sources.items()},
        frozenset(non_tu_interfaces),
    )


@dataclass(frozen=True, order=True)
class _BuildSink:
    relative_path: str
    scope: str
    lineno: int
    kind: str


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return node.attr if parent is None else f"{parent}.{node.attr}"
    return None


class _BenchmarkBuildSinkVisitor(ast.NodeVisitor):
    """Enumerate benchmark build boundaries without consulting defines."""

    _INJECTABLE_NAMES = frozenset({
        "build_fn", "evaluate_fn", "prepare_cell_fn",
    })

    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.scopes = ["<module>"]
        self.injected = [set()]
        self.module_aliases: dict[str, str] = {}
        self.callable_aliases: dict[str, str] = {}
        self.cmake_target_argv = [set()]
        self.sinks: set[_BuildSink] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.module_aliases[alias.asname or alias.name.split(".")[0]] = (
                alias.name
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            bound = alias.asname or alias.name
            canonical = f"{module}.{alias.name}" if module else alias.name
            if alias.name in {"buildcache", "pipeline"}:
                self.module_aliases[bound] = canonical
            else:
                self.callable_aliases[bound] = canonical

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scopes.append(node.name)
        self.generic_visit(node)
        self.scopes.pop()

    def _visit_function(self, node) -> None:
        arguments = {
            argument.arg
            for argument in (
                *node.args.posonlyargs, *node.args.args,
                *node.args.kwonlyargs,
            )
        }
        self.scopes.append(node.name)
        self.injected.append(
            self.injected[-1] | (arguments & self._INJECTABLE_NAMES)
        )
        self.cmake_target_argv.append(set(self.cmake_target_argv[-1]))
        self.generic_visit(node)
        self.cmake_target_argv.pop()
        self.injected.pop()
        self.scopes.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    @staticmethod
    def _is_cmake_target_argv(node: ast.AST) -> bool:
        strings = {
            item.value
            for item in ast.walk(node)
            if isinstance(item, ast.Constant)
            and isinstance(item.value, str)
        }
        return "--build" in strings and "--target" in strings

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._is_cmake_target_argv(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.cmake_target_argv[-1].add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if (
            node.value is not None
            and isinstance(node.target, ast.Name)
            and self._is_cmake_target_argv(node.value)
        ):
            self.cmake_target_argv[-1].add(node.target.id)
        self.generic_visit(node)

    def _canonical_call_name(self, node: ast.AST) -> str:
        name = _call_name(node) or ""
        if isinstance(node, ast.Name):
            return self.callable_aliases.get(name, name)
        root, separator, rest = name.partition(".")
        if separator and root in self.module_aliases:
            return f"{self.module_aliases[root]}.{rest}"
        return name

    def visit_Call(self, node: ast.Call) -> None:
        name = self._canonical_call_name(node.func)
        strings = {
            item.value
            for item in ast.walk(node)
            if isinstance(item, ast.Constant)
            and isinstance(item.value, str)
        }
        kind: str | None = None
        if (
            name.endswith((".build", ".build_v2"))
            and "buildcache" in name
        ):
            kind = "buildcache"
        elif name == "run_campaign" or name.endswith(".run_campaign"):
            kind = "campaign"
        elif name.endswith("pipeline.evaluate"):
            kind = "campaign"
        elif isinstance(node.func, ast.Name) and node.func.id in self.injected[-1]:
            kind = f"injected-{node.func.id}"
        elif (
            ("--build" in strings and "--target" in strings)
            or any(
                isinstance(argument, ast.Name)
                and argument.id in self.cmake_target_argv[-1]
                for argument in node.args
            )
        ):
            # This also sees an argv assembled for a later bounded runner.
            # Discovery therefore does not depend on a particular subprocess
            # wrapper or on the target being a literal at this call site.
            kind = "direct-cmake-target"
        if kind is not None:
            self.sinks.add(_BuildSink(
                self.relative_path, ".".join(self.scopes), node.lineno, kind,
            ))
        self.generic_visit(node)


_SHELL_FUNCTION_RE = re.compile(
    r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{"
)


def _shell_build_sinks(relative_path: str, source: str) -> set[_BuildSink]:
    sinks: set[_BuildSink] = set()
    scopes = ["<module>"]
    depth = 0
    for lineno, line in enumerate(source.splitlines(), 1):
        function = _SHELL_FUNCTION_RE.match(line)
        if function is not None:
            scopes.append(function.group(1))
            depth = 1
        elif len(scopes) > 1:
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                scopes.pop()
                depth = 0
        if (
            re.search(r"\bcmake\s+--build\b", line)
            and "--target" in line
            and re.search(r"\bycsb_[A-Za-z0-9_.-]+", line)
        ):
            sinks.add(_BuildSink(
                relative_path, ".".join(scopes), lineno,
                "shell-cmake-target",
            ))
    return sinks


def _production_build_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    for directory in _BUILD_SCAN_PATHS:
        for path in sorted(directory.rglob("*")):
            if path.suffix not in {".py", ".sh", ".json"} or not path.is_file():
                continue
            relative = path.relative_to(_ROOT).as_posix()
            if relative in _BUILD_BACKEND_PATHS:
                continue
            sources[relative] = path.read_text(encoding="utf-8")
    return sources


def _benchmark_build_sinks(sources: dict[str, str]) -> set[_BuildSink]:
    sinks: set[_BuildSink] = set()
    for relative_path, source in sources.items():
        if relative_path.endswith(".py"):
            visitor = _BenchmarkBuildSinkVisitor(relative_path)
            visitor.visit(ast.parse(source, filename=relative_path))
            sinks.update(visitor.sinks)
        elif relative_path.endswith(".sh"):
            sinks.update(_shell_build_sinks(relative_path, source))
    return sinks


@dataclass(frozen=True)
class _DeferredGateMember:
    relative_path: str
    owner: str
    reason: str
    sink_kind: str
    sink_scope: str
    sink_lineno: int


_DEFERRED_GATE_MEMBERS = (
    _DeferredGateMember(
        "orchestrator/campaign/b10_backoff_shape_sweep.py",
        "wave t1905",
        "active wave owns this driver",
        "buildcache",
        "<module>._build_binary",
        2501,
    ),
    _DeferredGateMember(
        "orchestrator/campaign/b10_backoff_shape_sweep.py",
        "wave t1905",
        "active wave owns this driver",
        "campaign",
        "<module>.run_formal",
        2873,
    ),
    _DeferredGateMember(
        "orchestrator/campaign/paper_story_a1_paired.py",
        "wave t1819",
        "active wave owns this driver",
        "campaign",
        "<module>.run_measurement",
        5067,
    ),
    _DeferredGateMember(
        "orchestrator/campaign/s8b_floor_campaign.py",
        "wave t2027",
        "active wave owns the build_fn injection seam",
        "injected-build_fn",
        "<module>.build_cells.invoke_build",
        4495,
    ),
    _DeferredGateMember(
        "orchestrator/campaign/s8b_floor_campaign.py",
        "wave t2027",
        "稼働 wave t2027 の所有面。動的 protocol 経由の campaign sink",
        "campaign",
        "<module>.main",
        8409,
    ),
    _DeferredGateMember(
        "orchestrator/campaign/s8b_oracle_driver.py",
        "wave t1999",
        (
            "実行時は require_returned_condition_evidence(prepared, ...) が支配するが、"
            "閉包検査は with ... as (..., prepared) の束縛を追えず、"
            "campaign kind の sink に対する支配的な返却物検査を"
            "被覆として数えられない。検査側の射程を広げる後続タスクで解消する"
        ),
        "campaign",
        "<module>.run_block",
        1788,
    ),
    _DeferredGateMember(
        "orchestrator/campaign/s8b_oracle_n_pilot.py",
        "protocol-r33 preregistration",
        (
            "output/insights/2026-08-16_t1142-n-pilot-prereg/"
            "protocol-r33.json binds driver_sha256"
        ),
        "injected-build_fn",
        "<module>.build_binaries",
        944,
    ),
)


def _deferred_member(sink: _BuildSink) -> _DeferredGateMember | None:
    matches = [
        item for item in _DEFERRED_GATE_MEMBERS
        if item.relative_path == sink.relative_path
        and item.sink_kind == sink.kind
        and item.sink_scope == sink.scope
        and item.sink_lineno == sink.lineno
    ]
    assert len(matches) <= 1
    return matches[0] if matches else None


def _function_bodies(tree: ast.AST) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _walk_without_nested_functions(node: ast.AST):
    pending = [node]
    while pending:
        current = pending.pop()
        yield current
        pending.extend(
            child for child in ast.iter_child_nodes(current)
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        )


def _gate_components(node: ast.AST) -> frozenset[str]:
    components: set[str] = set()
    for item in _walk_without_nested_functions(node):
        if isinstance(item, ast.Call):
            name = _call_name(item.func) or ""
            if name.endswith("evaluate_define_supply_effectuation"):
                components.add("supply")
            elif name.endswith("evaluate_define_runtime_meaning"):
                components.add("meaning")
            elif name.endswith("require_condition_gate_family"):
                components.add("admission")
        elif isinstance(item, ast.Attribute):
            if item.attr == "condition_supply_records":
                components.add("supply")
            elif item.attr == "condition_meaning_records":
                components.add("meaning")
        elif isinstance(item, ast.Constant) and isinstance(item.value, str):
            if item.value == "condition_supply_records":
                components.add("supply")
            elif item.value == "condition_meaning_records":
                components.add("meaning")
    return frozenset(components)


def _complete_gate_function_names(
    sources: dict[str, str],
) -> dict[str, frozenset[str]]:
    parsed: dict[str, ast.AST] = {
        path: ast.parse(source, filename=path)
        for path, source in sources.items()
        if path.endswith(".py")
        and any(marker in source for marker in (
            "condition_gate",
            "condition_meaning_gate",
            "condition_supply_records",
            "condition_meaning_records",
            "require_returned_condition_evidence",
        ))
    }
    by_module = {
        path.removesuffix(".py").replace("/", "."): path
        for path in parsed
    }
    bodies: dict[tuple[str, str], ast.AST] = {}
    local_names: dict[str, set[str]] = {}
    for path, tree in parsed.items():
        local_names[path] = set(_function_bodies(tree))
        bodies.update(
            ((path, name), body)
            for name, body in _function_bodies(tree).items()
        )

    imported_callables: dict[str, dict[str, tuple[str, str]]] = {
        path: {} for path in parsed
    }
    imported_modules: dict[str, dict[str, str]] = {
        path: {} for path in parsed
    }
    for path, tree in parsed.items():
        package = path.removesuffix(".py").split("/")[:-1]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = by_module.get(alias.name)
                    if target is not None:
                        imported_modules[path][
                            alias.asname or alias.name.split(".", 1)[0]
                        ] = target
                continue
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level:
                base = package[:len(package) - node.level + 1]
                module_parts = node.module.split(".") if node.module else []
                module = ".".join((*base, *module_parts))
            else:
                module = node.module or ""
            target = by_module.get(module)
            if target is not None:
                for alias in node.names:
                    imported_callables[path][alias.asname or alias.name] = (
                        target, alias.name,
                    )
            elif node.level and node.module is None:
                for alias in node.names:
                    child_module = ".".join((*base, alias.name))
                    child = by_module.get(child_module)
                    if child is not None:
                        imported_modules[path][alias.asname or alias.name] = child

    def resolve_call(path: str, node: ast.AST) -> tuple[str, str] | None:
        if isinstance(node, ast.Name):
            if node.id in local_names[path]:
                return path, node.id
            return imported_callables[path].get(node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            module_path = imported_modules[path].get(node.value.id)
            if module_path is not None:
                return module_path, node.attr
        return None

    called: dict[tuple[str, str], set[tuple[str, str]]] = {}
    complete: set[tuple[str, str]] = set()
    for identity, body in bodies.items():
        path, _name = identity
        called[identity] = {
            target
            for item in _walk_without_nested_functions(body)
            if isinstance(item, ast.Call)
            if (target := resolve_call(path, item.func)) is not None
        }
        if _gate_components(body) == {"supply", "meaning", "admission"}:
            complete.add(identity)
    while True:
        wrappers = {
            identity for identity, calls in called.items()
            if calls & complete
        }
        enlarged = complete | wrappers
        if enlarged == complete:
            break
        complete = enlarged

    callable_names: dict[str, set[str]] = {path: set() for path in parsed}
    for path, name in complete:
        callable_names[path].add(name)
    for path, aliases in imported_callables.items():
        callable_names[path].update(
            alias for alias, target in aliases.items() if target in complete
        )
    for path, aliases in imported_modules.items():
        for alias, module_path in aliases.items():
            callable_names[path].update(
                f"{alias}.{name}"
                for complete_path, name in complete
                if complete_path == module_path
            )
    return {
        path: frozenset(names) for path, names in callable_names.items()
    }


_FULL_GATE_COMPONENTS = frozenset({"supply", "meaning", "admission"})


@dataclass(frozen=True)
class _GateFlowState:
    covered_macros: frozenset[str] = frozenset()
    components: frozenset[str] = frozenset()


def _intersect_gate_states(states: list[_GateFlowState]) -> _GateFlowState:
    assert states
    covered = set(states[0].covered_macros)
    components = set(states[0].components)
    for state in states[1:]:
        covered.intersection_update(state.covered_macros)
        components.intersection_update(state.components)
    return _GateFlowState(frozenset(covered), frozenset(components))


class _QualifiedFunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.scope = ["<module>"]
        self.bodies: dict[str, ast.AST] = {}
        self.node_scopes: dict[int, str] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _visit_function(self, node) -> None:
        self.scope.append(node.name)
        qualified = ".".join(self.scope)
        self.bodies[qualified] = node
        self.node_scopes[id(node)] = qualified
        self.generic_visit(node)
        self.scope.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function


class _PythonGateFlow:
    """Conservative structured-flow proof that a gate covers one build sink."""

    def __init__(
        self,
        relative_path: str,
        source: str,
        *,
        complete_names: frozenset[str],
        patch_macros: frozenset[str],
        source_macros: frozenset[str],
    ):
        self.relative_path = relative_path
        self.source = source
        self.tree = ast.parse(source, filename=relative_path)
        functions = _QualifiedFunctionVisitor()
        functions.visit(self.tree)
        self.bodies = {"<module>": self.tree, **functions.bodies}
        self.node_scopes = functions.node_scopes
        self.module_assignments: dict[str, ast.AST] = {}
        for statement in self.tree.body:
            if isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        self.module_assignments[target.id] = statement.value
            elif (
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.value is not None
            ):
                self.module_assignments[statement.target.id] = statement.value
        self.complete_names = complete_names
        self.patch_macros = patch_macros
        self.source_macros = source_macros
        self.call_states: dict[tuple[str, int], list[_GateFlowState]] = {}
        self.local_incoming: dict[
            str, list[tuple[str, frozenset[str]]]
        ] = {scope: [] for scope in self.bodies}
        self.definition_incoming: dict[
            str, tuple[str, frozenset[str]]
        ] = {}
        self.returned_evidence_checks: dict[
            str, list[tuple[int, str | None]]
        ] = {}
        for scope, body in self.bodies.items():
            statements = body.body
            self._flow_block(statements, _GateFlowState(), scope)
        self.entry_coverage = self._derive_entry_coverage()

    def _resolve_local_scope(self, scope: str, name: str) -> str | None:
        parts = scope.split(".")
        for length in range(len(parts), 0, -1):
            candidate = ".".join((*parts[:length], name))
            if candidate in self.bodies:
                return candidate
        candidate = f"<module>.{name}"
        return candidate if candidate in self.bodies else None

    def _explicit_call_macros(
        self, scope: str, call: ast.Call,
    ) -> frozenset[str]:
        def tokens(node: ast.AST, visiting: frozenset[str] = frozenset()) -> set[str]:
            found: set[str] = set()
            for item in ast.walk(node):
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    found.update(_DEFINE_TOKEN_RE.findall(item.value))
                elif (
                    isinstance(item, ast.Name)
                    and item.id not in visiting
                    and item.id in self.module_assignments
                ):
                    found.update(tokens(
                        self.module_assignments[item.id], visiting | {item.id},
                    ))
            return found & set(self.patch_macros)

        name = _call_name(call.func)
        target_body = None
        if name is not None and "." not in name:
            target = self._resolve_local_scope(scope, name)
            if target is not None:
                target_body = self.bodies[target]
        if isinstance(target_body, (ast.FunctionDef, ast.AsyncFunctionDef)):
            positional = [
                *target_body.args.posonlyargs, *target_body.args.args,
            ]
            macro_parameters = {
                argument.arg for argument in (
                    *positional, *target_body.args.kwonlyargs,
                )
                if "macro" in argument.arg
            }
            if macro_parameters:
                bound: dict[str, ast.AST] = {
                    argument.arg: value
                    for argument, value in zip(positional, call.args)
                }
                bound.update({
                    keyword.arg: keyword.value
                    for keyword in call.keywords if keyword.arg is not None
                })
                supplied = [
                    bound[parameter]
                    for parameter in macro_parameters if parameter in bound
                ]
                explicit = set().union(*(tokens(item) for item in supplied))
                if explicit:
                    return frozenset(explicit)
                if supplied:
                    return self.source_macros
        explicit = tokens(call)
        if target_body is not None:
            explicit.update(tokens(target_body))
            if any(
                isinstance(item, ast.Name)
                and item.id.endswith(("_MACRO", "_DEFINE"))
                for item in ast.walk(target_body)
            ):
                explicit.update(self.source_macros)
        return frozenset(explicit)

    def _record_expression(
        self, expression: ast.AST | None, state: _GateFlowState, scope: str,
    ) -> _GateFlowState:
        if expression is None:
            return state
        calls = sorted(
            (item for item in ast.walk(expression) if isinstance(item, ast.Call)),
            key=lambda item: (item.lineno, item.col_offset),
        )
        current = state
        for call in calls:
            self.call_states.setdefault((scope, call.lineno), []).append(current)
            name = _call_name(call.func) or ""
            if "." not in name:
                target = self._resolve_local_scope(scope, name)
                if target is not None:
                    self.local_incoming[target].append(
                        (scope, current.covered_macros)
                    )
            if name.endswith("require_returned_condition_evidence"):
                result_name = None
                if call.args and isinstance(call.args[0], ast.Name):
                    result_name = call.args[0].id
                self.returned_evidence_checks.setdefault(scope, []).append(
                    (call.lineno, result_name)
                )
            component = None
            if name.endswith("evaluate_define_supply_effectuation"):
                component = "supply"
            elif name.endswith("evaluate_define_runtime_meaning"):
                component = "meaning"
            elif name.endswith("require_condition_gate_family"):
                component = "admission"
            components = set(current.components)
            if component is not None:
                components.add(component)
            covered = set(current.covered_macros)
            if name in self.complete_names:
                explicit = self._explicit_call_macros(scope, call)
                covered.update(explicit or self.source_macros)
            if _FULL_GATE_COMPONENTS.issubset(components):
                covered.update(self.source_macros)
            current = _GateFlowState(
                frozenset(covered), frozenset(components),
            )
        return current

    def _flow_block(
        self, statements: list[ast.stmt], state: _GateFlowState, scope: str,
    ) -> tuple[_GateFlowState, bool]:
        current = state
        for statement in statements:
            current, continues = self._flow_statement(statement, current, scope)
            if not continues:
                return current, False
        return current, True

    def _flow_statement(
        self, statement: ast.stmt, state: _GateFlowState, scope: str,
    ) -> tuple[_GateFlowState, bool]:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            child = self.node_scopes[id(statement)]
            self.definition_incoming[child] = (
                scope, state.covered_macros,
            )
            return state, True
        if isinstance(statement, ast.ClassDef):
            return state, True
        if isinstance(statement, ast.If):
            tested = self._record_expression(statement.test, state, scope)
            exits: list[_GateFlowState] = []
            body_state, body_continues = self._flow_block(
                statement.body, tested, scope,
            )
            if body_continues:
                exits.append(body_state)
            if statement.orelse:
                else_state, else_continues = self._flow_block(
                    statement.orelse, tested, scope,
                )
                if else_continues:
                    exits.append(else_state)
            else:
                exits.append(tested)
            if not exits:
                return tested, False
            return _intersect_gate_states(exits), True
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            entered = self._record_expression(statement.iter, state, scope)
            self._flow_block(statement.body, entered, scope)
            exits = [entered]
            if statement.orelse:
                else_state, else_continues = self._flow_block(
                    statement.orelse, entered, scope,
                )
                if else_continues:
                    exits.append(else_state)
            return _intersect_gate_states(exits), True
        if isinstance(statement, ast.While):
            tested = self._record_expression(statement.test, state, scope)
            self._flow_block(statement.body, tested, scope)
            exits = [tested]
            if statement.orelse:
                else_state, else_continues = self._flow_block(
                    statement.orelse, tested, scope,
                )
                if else_continues:
                    exits.append(else_state)
            return _intersect_gate_states(exits), True
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            entered = state
            for item in statement.items:
                entered = self._record_expression(
                    item.context_expr, entered, scope,
                )
            return self._flow_block(statement.body, entered, scope)
        if isinstance(statement, ast.Try) or type(statement).__name__ == "TryStar":
            body_state, body_continues = self._flow_block(
                statement.body, state, scope,
            )
            exits: list[_GateFlowState] = []
            if body_continues:
                if statement.orelse:
                    else_state, else_continues = self._flow_block(
                        statement.orelse, body_state, scope,
                    )
                    if else_continues:
                        exits.append(else_state)
                else:
                    exits.append(body_state)
            for handler in statement.handlers:
                handler_state, handler_continues = self._flow_block(
                    handler.body, state, scope,
                )
                if handler_continues:
                    exits.append(handler_state)
            if not statement.handlers:
                exits.append(state)
            merged = _intersect_gate_states(exits) if exits else state
            if statement.finalbody:
                return self._flow_block(statement.finalbody, merged, scope)
            return merged, bool(exits)
        if isinstance(statement, ast.Match):
            matched = self._record_expression(statement.subject, state, scope)
            exits = [matched]
            for case in statement.cases:
                case_state, case_continues = self._flow_block(
                    case.body, matched, scope,
                )
                if case_continues:
                    exits.append(case_state)
            return _intersect_gate_states(exits), True

        expressions: list[ast.AST] = []
        if isinstance(statement, ast.Expr):
            expressions = [statement.value]
        elif isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = getattr(statement, "value", None)
            if value is not None:
                expressions = [value]
        elif isinstance(statement, ast.Return):
            expressions = [statement.value] if statement.value is not None else []
        elif isinstance(statement, ast.Raise):
            expressions = [
                item for item in (statement.exc, statement.cause)
                if item is not None
            ]
        elif isinstance(statement, ast.Assert):
            expressions = [statement.test]
            if statement.msg is not None:
                expressions.append(statement.msg)
        current = state
        for expression in expressions:
            current = self._record_expression(expression, current, scope)
        terminates = isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue))
        return current, not terminates

    def _derive_entry_coverage(self) -> dict[str, frozenset[str]]:
        entry = {scope: frozenset() for scope in self.bodies}
        while True:
            updated = dict(entry)
            for scope in self.bodies:
                if scope == "<module>":
                    continue
                definition = self.definition_incoming.get(scope)
                definition_coverage = frozenset()
                if definition is not None:
                    parent, local = definition
                    definition_coverage = local | entry[parent]
                arrivals = [
                    local | entry[caller] | definition_coverage
                    for caller, local in self.local_incoming[scope]
                ]
                if arrivals:
                    common = set(arrivals[0])
                    for arrival in arrivals[1:]:
                        common.intersection_update(arrival)
                    updated[scope] = frozenset(common)
                else:
                    updated[scope] = definition_coverage
            if updated == entry:
                return entry
            entry = updated

    def _injected_result_name(self, sink: _BuildSink) -> str | None:
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if (
                        isinstance(item.context_expr, ast.Call)
                        and item.context_expr.lineno == sink.lineno
                        and isinstance(item.optional_vars, ast.Name)
                    ):
                        return item.optional_vars.id
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if not isinstance(value, ast.Call) or value.lineno != sink.lineno:
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if len(targets) == 1 and isinstance(targets[0], ast.Name):
                    return targets[0].id
        return None

    def _effective_sink_line(self, sink: _BuildSink) -> int:
        if sink.kind != "direct-cmake-target":
            return sink.lineno
        body = self.bodies.get(sink.scope)
        if body is None:
            return sink.lineno
        at_anchor = [
            item for item in ast.walk(body)
            if isinstance(item, ast.Call) and item.lineno == sink.lineno
        ]
        if any("run" in (_call_name(call.func) or "").lower() for call in at_anchor):
            return sink.lineno
        executions = [
            item.lineno for item in ast.walk(body)
            if isinstance(item, ast.Call)
            and item.lineno > sink.lineno
            and "run" in (_call_name(item.func) or "").lower()
            and any(
                isinstance(argument, ast.Name)
                and argument.id in {"argv", "build_argv", "cmd", "command"}
                for argument in item.args
            )
        ]
        return min(executions, default=sink.lineno)

    def coverage_for_sink(
        self, sink: _BuildSink, sibling_sinks: set[_BuildSink],
    ) -> frozenset[str]:
        effective_line = self._effective_sink_line(sink)
        states = self.call_states.get((sink.scope, effective_line), [])
        local = _intersect_gate_states(states).covered_macros if states else frozenset()
        coverage = local | self.entry_coverage.get(sink.scope, frozenset())
        if not sink.kind.startswith("injected-"):
            return coverage

        result_name = self._injected_result_name(sink)
        next_lines = [
            other.lineno for other in sibling_sinks
            if other.scope == sink.scope
            and other.kind.startswith("injected-")
            and other.lineno > sink.lineno
        ]
        boundary = min(next_lines, default=10 ** 9)
        matching_checks = [
            line for line, checked_name in self.returned_evidence_checks.get(
                sink.scope, []
            )
            if sink.lineno < line < boundary
            and result_name is not None
            and checked_name == result_name
        ]
        if matching_checks:
            # The validator compares the returned record macro set with the
            # concrete injected request.  Its dynamic coverage is therefore
            # exact even when the macro token is not lexical in this file.
            return coverage | self.patch_macros
        return coverage


def _shell_gate_coverage(
    source: str, sink: _BuildSink, source_macros: frozenset[str],
) -> frozenset[str]:
    if "orchestrator.campaign.condition_meaning_gate" not in source:
        return frozenset()
    module_gate_lines: list[int] = []
    function_gate_lines: list[int] = []
    function_calls: list[int] = []
    function_name = sink.scope.rsplit(".", 1)[-1]
    current_scope = "<module>"
    depth = 0
    for lineno, line in enumerate(source.splitlines(), 1):
        function = _SHELL_FUNCTION_RE.match(line)
        if function is not None:
            current_scope = f"<module>.{function.group(1)}"
            depth = 1
        elif current_scope != "<module>":
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                current_scope = "<module>"
                depth = 0
        executes_gate = bool(
            re.match(r"^\s*run_condition_gate(?:\s|$)", line)
            or (
                "condition_gate_argv[@]" in line
                and "condition_gate_argv+=" not in line
            )
        )
        if executes_gate:
            if current_scope == "<module>":
                module_gate_lines.append(lineno)
            elif current_scope == sink.scope:
                function_gate_lines.append(lineno)
        if (
            current_scope == "<module>"
            and re.match(rf"^\s*{re.escape(function_name)}(?:\s|$)", line)
        ):
            function_calls.append(lineno)
    if sink.scope == "<module>":
        gated = any(line < sink.lineno for line in module_gate_lines)
    else:
        gated = (
            any(line < sink.lineno for line in function_gate_lines)
            or bool(function_calls)
            and all(any(gate < call for gate in module_gate_lines) for call in function_calls)
        )
    return source_macros if gated else frozenset()


def _source_macro_inventory(
    all_sources: dict[str, str],
    patch_macros: frozenset[str],
    *,
    root_paths: set[str] | None = None,
) -> dict[str, frozenset[str]]:
    denied_producers = {
        "buildcache.py", "condition_meaning_gate.py", "model.py",
        "pipeline.py",
    }
    by_module = {
        path.removesuffix(".py").replace("/", "."): path
        for path in all_sources
        if path.endswith(".py")
    }
    by_basename: dict[str, set[str]] = {}
    for path in all_sources:
        by_basename.setdefault(Path(path).name, set()).add(path)

    direct: dict[str, set[str]] = {}
    parsed: dict[str, ast.AST] = {}
    assigned_tokens: dict[str, dict[str, set[str]]] = {}
    for path, text in all_sources.items():
        tokens = set(_DEFINE_TOKEN_RE.findall(text)) & set(patch_macros)
        for option in re.findall(r"-D([A-Z][A-Z0-9_]*)", text):
            macro = option.removeprefix("CCBENCH_")
            if macro in patch_macros:
                tokens.add(macro)
        direct[path] = tokens
        assigned_tokens[path] = {}
        for line in text.splitlines():
            assignment = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line,
            )
            if assignment is None:
                continue
            assigned_tokens[path][assignment.group(1)] = (
                set(_DEFINE_TOKEN_RE.findall(assignment.group(2)))
                & set(patch_macros)
            )
        if path.endswith(".py") and (
            root_paths is None or path in root_paths
        ):
            tree = ast.parse(text, filename=path)
            parsed[path] = tree

    reachable = {path: set(tokens) for path, tokens in direct.items()}
    for path, tree in parsed.items():
        package = path.removesuffix(".py").split("/")[:-1]
        module_aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level:
                base = package[:len(package) - node.level + 1]
                module_parts = node.module.split(".") if node.module else []
                module = ".".join((*base, *module_parts))
            else:
                module = node.module or ""
            target_path = by_module.get(module)
            if target_path is not None:
                if Path(target_path).name in denied_producers:
                    continue
                for alias in node.names:
                    reachable[path].update(
                        assigned_tokens.get(target_path, {}).get(
                            alias.name, set(),
                        )
                    )
            elif node.level and node.module is None:
                for alias in node.names:
                    child_module = ".".join((*base, alias.name))
                    child = by_module.get(child_module)
                    if child is not None and Path(child).name not in denied_producers:
                        module_aliases[alias.asname or alias.name] = child
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in module_aliases
            ):
                continue
            reachable[path].update(
                assigned_tokens.get(module_aliases[node.value.id], {}).get(
                    node.attr, set(),
                )
            )
        for json_name in re.findall(r"[A-Za-z0-9_./-]+\.json", all_sources[path]):
            candidates = by_basename.get(Path(json_name).name, set())
            if len(candidates) == 1:
                reachable[path].update(direct[next(iter(candidates))])
    return {
        path: frozenset(tokens) for path, tokens in reachable.items()
    }


def _source_macro_tokens(
    relative_path: str,
    source: str,
    patch_macros: frozenset[str],
    all_sources: dict[str, str],
) -> frozenset[str]:
    assert all_sources[relative_path] == source
    return _source_macro_inventory(
        all_sources, patch_macros, root_paths={relative_path},
    )[relative_path]


def _sink_configuration_expression(
    source: str, sink: _BuildSink,
) -> tuple[ast.AST, ast.AST] | None:
    tree = ast.parse(source, filename=sink.relative_path)
    functions = _QualifiedFunctionVisitor()
    functions.visit(tree)
    body = {"<module>": tree, **functions.bodies}.get(sink.scope)
    if body is None:
        return None
    calls = [
        item for item in ast.walk(body)
        if isinstance(item, ast.Call) and item.lineno == sink.lineno
    ]
    if len(calls) != 1:
        return None
    call = calls[0]
    name = _call_name(call.func) or ""
    argument_index = 0
    if sink.kind == "campaign" and not name.endswith("pipeline.evaluate"):
        argument_index = 1
    if len(call.args) <= argument_index:
        return None
    return body, call.args[argument_index]


def _expression_depends_on_scope_parameter(
    body: ast.AST, expression: ast.AST, *, before_line: int,
) -> bool:
    parameters: set[str] = set()
    if isinstance(body, (ast.FunctionDef, ast.AsyncFunctionDef)):
        parameters = {
            argument.arg
            for argument in (
                *body.args.posonlyargs, *body.args.args, *body.args.kwonlyargs,
            )
        }
        if body.args.vararg is not None:
            parameters.add(body.args.vararg.arg)
        if body.args.kwarg is not None:
            parameters.add(body.args.kwarg.arg)
    assignments: dict[str, ast.AST] = {}
    for node in ast.walk(body):
        if getattr(node, "lineno", before_line) >= before_line:
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                assignments[node.target.id] = node.value
        elif isinstance(node, (ast.For, ast.AsyncFor)) and isinstance(node.target, ast.Name):
            assignments[node.target.id] = node.iter

    opaque_calls = {
        "input", "getenv", "load", "loads", "load_protocol", "parse_args",
        "read_text", "read_bytes",
    }

    def depends(node: ast.AST, visiting: frozenset[str] = frozenset()) -> bool:
        if isinstance(node, ast.Name):
            if node.id in parameters:
                return True
            if node.id in visiting or node.id not in assignments:
                return False
            return depends(assignments[node.id], visiting | {node.id})
        if isinstance(node, ast.Call):
            name = (_call_name(node.func) or "").rsplit(".", 1)[-1]
            if name in opaque_calls or name.startswith(("load_", "parse_", "read_")):
                return True
            return any(depends(item, visiting) for item in (
                *node.args,
                *(keyword.value for keyword in node.keywords),
            ))
        return any(depends(child, visiting) for child in ast.iter_child_nodes(node))

    return depends(expression)


def _expression_macro_inventory(
    source: str,
    body: ast.AST,
    expression: ast.AST,
    patch_macros: frozenset[str],
    *,
    before_line: int,
) -> frozenset[str]:
    tree = ast.parse(source)
    module_assignments: dict[str, ast.AST] = {}
    functions: dict[str, ast.AST] = {}
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions[statement.name] = statement
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    module_assignments[target.id] = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if statement.value is not None:
                module_assignments[statement.target.id] = statement.value
    local_assignments: dict[str, ast.AST] = {}
    for node in ast.walk(body):
        if getattr(node, "lineno", before_line) >= before_line:
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    local_assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                local_assignments[node.target.id] = node.value

    def collect(node: ast.AST, visiting: frozenset[str] = frozenset()) -> set[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return set(_DEFINE_TOKEN_RE.findall(node.value)) & set(patch_macros)
        if isinstance(node, ast.Name):
            if node.id in visiting:
                return set()
            value = local_assignments.get(node.id, module_assignments.get(node.id))
            if value is None:
                return set()
            return collect(value, visiting | {node.id})
        if isinstance(node, ast.Call):
            tokens: set[str] = set()
            for item in (*node.args, *(keyword.value for keyword in node.keywords)):
                tokens.update(collect(item, visiting))
            name = _call_name(node.func) or ""
            if "." not in name and name in functions and name not in visiting:
                for item in _walk_without_nested_functions(functions[name]):
                    if isinstance(item, ast.Return) and item.value is not None:
                        tokens.update(collect(item.value, visiting | {name}))
            return tokens
        tokens: set[str] = set()
        for child in ast.iter_child_nodes(node):
            tokens.update(collect(child, visiting))
        return tokens

    return frozenset(collect(expression))


def _sink_macro_inventory(
    source: str,
    sink: _BuildSink,
    patch_macros: frozenset[str],
    source_macros: frozenset[str],
) -> frozenset[str]:
    if sink.kind not in {"buildcache", "campaign"}:
        return source_macros
    configuration = _sink_configuration_expression(source, sink)
    if configuration is None:
        return source_macros
    body, expression = configuration
    explicit = _expression_macro_inventory(
        source,
        body,
        expression,
        patch_macros,
        before_line=sink.lineno,
    )
    if explicit:
        return explicit
    if _expression_depends_on_scope_parameter(
        body, expression, before_line=sink.lineno,
    ):
        return source_macros
    return frozenset()


def _sink_macro_reachability(
    source: str,
    sink: _BuildSink,
    macro: str,
    source_macros: frozenset[str],
) -> str:
    if macro in source_macros:
        return "reachable"
    if sink.kind.startswith("injected-"):
        return "unresolved"
    if source_macros:
        # The inventory is not just a token search in this file: it closes over
        # imported assigned values and uniquely referenced JSON.  Once that
        # independently derived input surface contains at least one domain
        # interface, absence of this different interface is a negative proof,
        # rather than an empty-candidate shortcut.
        return "proven-unreachable"
    if sink.kind in {"direct-cmake-target", "shell-cmake-target"}:
        # These scanners inspect the configure/build source itself, including
        # imported constants and referenced JSON.  With no injected callable,
        # absence from that closed input inventory proves this particular
        # define cannot be introduced at the enumerated build boundary.
        return "proven-unreachable"
    configuration = _sink_configuration_expression(source, sink)
    if configuration is None:
        return "unresolved"
    body, expression = configuration
    if _expression_depends_on_scope_parameter(
        body, expression, before_line=sink.lineno,
    ):
        return "unresolved"
    return "proven-unreachable"


def _define_sink_cross_product_failures(
    sources: dict[str, str],
    patch_macros: frozenset[str],
) -> list[tuple[str, _BuildSink, str]]:
    """Return reachable or unresolved cross-product cells lacking both arms."""

    sinks = _benchmark_build_sinks(sources)
    complete_functions = _complete_gate_function_names(sources)
    macro_inventory = _source_macro_inventory(
        sources,
        patch_macros,
        root_paths={sink.relative_path for sink in sinks},
    )
    sinks_by_path: dict[str, set[_BuildSink]] = {}
    for sink in sinks:
        sinks_by_path.setdefault(sink.relative_path, set()).add(sink)
    python_flows = {
        path: _PythonGateFlow(
            path,
            sources[path],
            complete_names=complete_functions.get(path, frozenset()),
            patch_macros=patch_macros,
            source_macros=macro_inventory[path],
        )
        for path in sinks_by_path
        if path.endswith(".py")
    }
    sink_analysis = {
        sink: (
            _sink_macro_inventory(
                sources[sink.relative_path],
                sink,
                patch_macros,
                macro_inventory[sink.relative_path],
            ),
            (
                python_flows[sink.relative_path].coverage_for_sink(
                    sink, sinks_by_path[sink.relative_path],
                )
                if sink.relative_path.endswith(".py")
                else _shell_gate_coverage(
                    sources[sink.relative_path], sink,
                    macro_inventory[sink.relative_path],
                )
            ),
        )
        for sink in sinks
    }
    failures: list[tuple[str, _BuildSink, str]] = []
    for macro in sorted(patch_macros):
        for sink in sorted(sinks):
            source_macros, gate_coverage = sink_analysis[sink]
            reachability = _sink_macro_reachability(
                sources[sink.relative_path], sink, macro, source_macros,
            )
            if reachability == "proven-unreachable":
                continue
            if macro in gate_coverage:
                continue
            if _deferred_member(sink) is not None:
                continue
            failures.append((macro, sink, reachability))
    return failures


def test_reviewed_process_launch_inventory_is_recursive_and_exact():
    expected = (
        _GATEWAY
        + _DIRECT_SAFE_ALLOWLIST
        + _DIRECT_CCBENCH_DIAGNOSTIC_SITES
        + _EXPLICIT_NON_CCBENCH_PROCESS_SITES
    )
    assert _process_launch_sites() == expected


def test_patch_define_inventory_matches_condition_gate_registry():
    patch_sources, non_tu_interfaces = _patch_added_define_interfaces()
    assert frozenset(patch_sources) == frozenset(
        condition_meaning_gate.DEFINE_SPECS
    )
    assert non_tu_interfaces == {
        "CCBENCH_BUILD_SS2PL_TESTS",
        "CCBENCH_SOURCE_DIR",
    }
    assert {
        macro: spec.patch_rel
        for macro, spec in condition_meaning_gate.DEFINE_SPECS.items()
        if spec.patch_rel not in patch_sources[macro]
    } == {}


def test_define_sink_cross_product_has_no_unreviewed_ungated_member():
    patch_sources, _non_tu_interfaces = _patch_added_define_interfaces()
    failures = _define_sink_cross_product_failures(
        _production_build_sources(), frozenset(patch_sources),
    )
    assert failures == []


def test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink():
    assert {
        (
            item.relative_path, item.owner, item.sink_kind,
            item.sink_scope, item.sink_lineno,
        )
        for item in _DEFERRED_GATE_MEMBERS
    } == {
        (
            "orchestrator/campaign/b10_backoff_shape_sweep.py",
            "wave t1905", "buildcache", "<module>._build_binary", 2501,
        ),
        (
            "orchestrator/campaign/b10_backoff_shape_sweep.py",
            "wave t1905", "campaign", "<module>.run_formal", 2873,
        ),
        (
            "orchestrator/campaign/paper_story_a1_paired.py",
            "wave t1819", "campaign", "<module>.run_measurement", 5067,
        ),
        (
            "orchestrator/campaign/s8b_floor_campaign.py",
            "wave t2027", "injected-build_fn",
            "<module>.build_cells.invoke_build", 4495,
        ),
        (
            "orchestrator/campaign/s8b_floor_campaign.py",
            "wave t2027", "campaign", "<module>.main", 8409,
        ),
        (
            "orchestrator/campaign/s8b_oracle_driver.py",
            "wave t1999", "campaign", "<module>.run_block", 1788,
        ),
        (
            "orchestrator/campaign/s8b_oracle_n_pilot.py",
            "protocol-r33 preregistration", "injected-build_fn",
            "<module>.build_binaries", 944,
        ),
    }
    assert all(item.reason for item in _DEFERRED_GATE_MEMBERS)
    assert all(
        item.sink_kind and item.sink_scope
        for item in _DEFERRED_GATE_MEMBERS
    )
    sources = _production_build_sources()
    sinks = _benchmark_build_sinks(sources)
    matched_sinks: set[_BuildSink] = set()
    for item in _DEFERRED_GATE_MEMBERS:
        matches = [
            sink for sink in sinks
            if sink.relative_path == item.relative_path
            and sink.kind == item.sink_kind
            and sink.scope == item.sink_scope
            and sink.lineno == item.sink_lineno
        ]
        assert len(matches) == 1
        assert _deferred_member(matches[0]) == item
        matched_sinks.add(matches[0])
    assert len(matched_sinks) == len(_DEFERRED_GATE_MEMBERS)


def test_deferred_gate_ledger_does_not_match_a_new_sink_in_the_same_file():
    new_sink = _BuildSink(
        "orchestrator/campaign/b10_backoff_shape_sweep.py",
        "<module>.future_build",
        99999,
        "buildcache",
    )
    assert _deferred_member(new_sink) is None


def test_define_sink_cross_product_rejects_synthetic_member_without_gate():
    patch_sources, _non_tu_interfaces = _patch_added_define_interfaces()
    relative = "orchestrator/campaign/synthetic_missing_gate.py"
    sources = {relative: (
        "import subprocess\n"
        "def build(source, out):\n"
        "    configure = ['cmake', '-S', source, '-B', out, "
        "'-DCMAKE_CXX_FLAGS=-DIZANAGI_BREAK_PERMUTATION=1']\n"
        "    subprocess.run(configure, check=True)\n"
        "    subprocess.run(['cmake', '--build', out, '--target', "
        "'ycsb_silo.exe'], check=True)\n"
    )}
    failures = _define_sink_cross_product_failures(
        sources, frozenset(patch_sources),
    )
    assert failures == [(
        "IZANAGI_BREAK_PERMUTATION",
        _BuildSink(
            relative, "<module>.build", 5, "direct-cmake-target",
        ),
        "reachable",
    )]


def test_define_sink_cross_product_rejects_gate_with_only_one_arm():
    patch_sources, _non_tu_interfaces = _patch_added_define_interfaces()
    relative = "orchestrator/campaign/synthetic_one_arm.py"
    sources = {
        "orchestrator/campaign/complete_elsewhere.py": (
            "def _require_condition_gate(captured, request):\n"
            "    supply = gate.evaluate_define_supply_effectuation(\n"
            "        captured, request=request, cxx='c++', cmake='cmake')\n"
            "    meaning = gate.evaluate_define_runtime_meaning(\n"
            "        captured, request=request, declaration=None, cxx='c++')\n"
            "    gate.require_condition_gate_family(\n"
            "        [supply], [meaning], use_class='raw-measurement')\n"
        ),
        relative: (
        "from orchestrator.campaign import condition_meaning_gate as gate\n"
        "def _require_condition_gate(captured, request):\n"
        "    supply = gate.evaluate_define_supply_effectuation(\n"
        "        captured, request=request, cxx='c++', cmake='cmake')\n"
        "    gate.require_condition_gate_family(\n"
        "        [supply], [], use_class='raw-measurement')\n"
        "def build(source, out, captured, request):\n"
        "    _require_condition_gate(captured, request)\n"
        "    flags = '-DIZANAGI_BREAK_PERMUTATION=1'\n"
        "    run(['cmake', '-S', source, '-B', out, flags])\n"
        "    run(['cmake', '--build', out, '--target', 'ycsb_silo.exe'])\n"
        ),
    }
    failures = _define_sink_cross_product_failures(
        sources, frozenset(patch_sources),
    )
    assert [(macro, reachability) for macro, _sink, reachability in failures] == [
        ("IZANAGI_BREAK_PERMUTATION", "reachable"),
    ]


def test_define_sink_cross_product_does_not_defer_unlisted_member():
    patch_sources, _non_tu_interfaces = _patch_added_define_interfaces()
    relative = "orchestrator/campaign/not_in_deferred_ledger.py"
    sources = {relative: (
        "def build(build_fn, genome):\n"
        "    marker = 'BACKOFF_FIXED'\n"
        "    return build_fn(genome)\n"
    )}
    failures = _define_sink_cross_product_failures(
        sources, frozenset(patch_sources),
    )
    assert (
        "BACKOFF_FIXED",
        _BuildSink(
            relative, "<module>.build", 3, "injected-build_fn",
        ),
        "reachable",
    ) in failures
    assert all(_deferred_member(sink) is None for _macro, sink, _state in failures)


def test_define_sink_cross_product_requires_gate_to_dominate_each_sink():
    relative = "orchestrator/campaign/synthetic_two_builds.py"
    sources = {relative: (
        "from orchestrator.campaign import buildcache\n"
        "def _gate(captured, request):\n"
        "    marker = 'BACKOFF_FIXED'\n"
        "    supply = gate.evaluate_define_supply_effectuation(captured, request)\n"
        "    meaning = gate.evaluate_define_runtime_meaning(captured, request)\n"
        "    gate.require_condition_gate_family([supply], [meaning])\n"
        "def gated_build(genome, captured, request):\n"
        "    _gate(captured, request)\n"
        "    return buildcache.build(genome)\n"
        "def ungated_build(genome):\n"
        "    return buildcache.build(genome)\n"
    )}
    failures = _define_sink_cross_product_failures(
        sources, frozenset({"BACKOFF_FIXED"}),
    )
    assert failures == [(
        "BACKOFF_FIXED",
        _BuildSink(
            relative, "<module>.ungated_build", 11, "buildcache",
        ),
        "reachable",
    )]


def test_define_sink_cross_product_marks_opaque_nonlexical_cell_unresolved():
    relative = "orchestrator/campaign/synthetic_dynamic_genome.py"
    sources = {relative: (
        "from orchestrator.campaign import buildcache\n"
        "def build(genome):\n"
        "    return buildcache.build(genome)\n"
    )}
    failures = _define_sink_cross_product_failures(
        sources, frozenset({"BACKOFF_FIXED"}),
    )
    assert failures == [(
        "BACKOFF_FIXED",
        _BuildSink(relative, "<module>.build", 3, "buildcache"),
        "unresolved",
    )]


def test_define_sink_cross_product_does_not_reuse_gate_for_another_macro():
    relative = "orchestrator/campaign/synthetic_wrong_macro_gate.py"
    sources = {relative: (
        "from orchestrator.campaign import buildcache\n"
        "def _gate(captured, request):\n"
        "    marker = 'BACKOFF_FIXED'\n"
        "    supply = gate.evaluate_define_supply_effectuation(captured, request)\n"
        "    meaning = gate.evaluate_define_runtime_meaning(captured, request)\n"
        "    gate.require_condition_gate_family([supply], [meaning])\n"
        "def build(genome, captured, request):\n"
        "    _gate(captured, request)\n"
        "    requested = 'BACKOFF_NOINLINE'\n"
        "    return buildcache.build(genome)\n"
    )}
    failures = _define_sink_cross_product_failures(
        sources, frozenset({"BACKOFF_FIXED", "BACKOFF_NOINLINE"}),
    )
    assert failures == [(
        "BACKOFF_NOINLINE",
        _BuildSink(relative, "<module>.build", 10, "buildcache"),
        "reachable",
    )]


def test_calibration_capability_issuer_has_one_certify_call_site():
    calls, imports = _calibration_issuer_sites()
    assert calls == Counter({
        ("calibrator/cli.py", "<module>._certify_main"): 1,
    })
    assert imports == Counter({
        ("calibrator/cli.py", "<module>"): 1,
    })


def test_reviewed_ccbench_measurement_launches_use_bounded_sites():
    observed = (
        _process_launch_sites()
        - _EXPLICIT_NON_CCBENCH_PROCESS_SITES
        - _DIRECT_CCBENCH_DIAGNOSTIC_SITES
    )
    assert observed == _GATEWAY + _DIRECT_SAFE_ALLOWLIST
    assert _bounded_run_once_client_sites() == _BOUNDED_RUN_ONCE_CLIENTS


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


def test_exact_anchor_exclusion_keeps_an_unreviewed_launch_visible():
    sources = {
        "campaign/mocc_trace_pair_anchor.py": (
            "import subprocess\n"
            "def _verify_ed25519_signature():\n"
            "    subprocess.run([\"openssl\", \"pkeyutl\"])\n"
        ),
        "campaign/unreviewed.py": (
            "import subprocess\n"
            "def launch():\n"
            "    subprocess.run([\"unexpected\"])\n"
        ),
    }
    observed: Counter[tuple[str, str]] = Counter()
    for relative_path, source in sources.items():
        visitor = _ProcessLaunchVisitor(relative_path)
        visitor.visit(ast.parse(source))
        observed.update(visitor.sites)
    assert observed - _EXPLICIT_NON_CCBENCH_PROCESS_SITES == Counter({
        ("campaign/unreviewed.py", "<module>.launch"): 1,
    })


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
