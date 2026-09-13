# -*- coding: utf-8 -*-
"""U3 caller/CLI authority and bounded materializer inventory gates."""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest


pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH.parent))

from orchestrator.campaign import build_admission, pipeline
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign import p3_s4_loop_trigger_gating as TRIGGER
from orchestrator.campaign import s6_sort_sweep as S6
from orchestrator.campaign import wal
from orchestrator.campaign import env_contract
from orchestrator.campaign.auditor_gate import AuditorVerdict

from orchestrator.campaign.build_admission import (
    BuildAdmissionError,
    BuildProvenance,
    GeneratorId,
    add_coder_build_authority_argument,
    add_registered_coder_build_authority_argument,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.materializer_admission import (
    ADMITTED_GATEWAY,
    CODER_ENTRYPOINT,
    CLOSED_CODER_ENTRYPOINT_SITES,
    CLOSED_PYTHON_MATERIALIZER_SITES,
    DIRECT_MATERIALIZER,
    MATERIALIZER_ADMISSION_REGISTRY,
    NON_ADMISSIBLE,
    NON_ADMISSIBLE_MATERIALIZERS,
    non_admissible_materializer,
)
from orchestrator.campaign.source_digest import EMPTY_TRACKED_DIFF_SHA256, STOCK, SourceEvidence
from orchestrator.campaign.layout import CampaignLayout
from orchestrator.campaign.model import Genome
from condition_gate_test_support import (
    SORT_VARIANT_SOURCE,
    TRIGGER_GATING_SOURCE,
    condition_gate_compilers,
    install_condition_gate_build_fixture,
)


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "orchestrator" / "campaign"

EXPECTED_CODER_SITES = frozenset({
    "orchestrator.campaign.p3_kickoff.main",
    "orchestrator.campaign.p3_s4_red.main",
    "orchestrator.campaign.p3_s4_loop.main",
    "orchestrator.campaign.p3_s4_loop_sort.main",
    "orchestrator.campaign.p3_s4_loop_trigger_gating.main",
    "orchestrator.campaign.p3_autonomous_workload_trial.main",
})

_LOW_LEVEL_HELPER = "add_coder_build_authority_argument"
_REGISTERED_HELPER = "add_registered_coder_build_authority_argument"
_AUTHORITY_DYNAMIC_NAMES = frozenset({
    _LOW_LEVEL_HELPER,
    _REGISTERED_HELPER,
    "CoderBuildAuthority",
    "_CoderAuthorityAction",
    "_RegisteredCoderAuthorityAction",
    "build_run_context",
    "coder_build_authority",
})
_STATIC_STRING_VALUE_LIMIT = 32

# Every retained low-level issuer is allowed by exact call site and cardinality.  No file is
# excluded from parsing: a second call in the same function or a call in another function changes
# this inventory and fails the closure audit.
_LOW_LEVEL_ISSUER_ALLOWLIST = frozenset({
    (
        "orchestrator/tests/test_artifact_admission.py",
        "_new_schema_campaign", _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_build_admission.py",
        "_parser_authority", _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_buildcache_v2.py",
        "_all_class_admissions", _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_campaign.py",
        "<module>", _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_p3_autonomous_workload_trial.py",
        "_coder_authority", _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_p3_build_authority_cli.py",
        "test_stock_machine_and_opted_in_coder_paths_remain_accepted",
        _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_p3_build_authority_cli.py",
        "test_dirty_noop_stock_token_enters_coder_admission_namespace",
        _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_p3_exploration_namespace.py",
        "<module>", _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_p3_s4_loop_trigger_gating.py",
        "<module>", _LOW_LEVEL_HELPER, 1,
    ),
    (
        "orchestrator/tests/test_s1_direct_comparison.py",
        "test_pipeline_bench_rounds_default_three_and_opt_in_one",
        _LOW_LEVEL_HELPER, 1,
    ),
    (
        "output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/"
        "smoke_driver.py",
        "main", _LOW_LEVEL_HELPER, 1,
    ),
})

MACHINE_CALLERS = {
    "b10_backoff_static_tail_formal.py": "BACKOFF_SWEEP",
    "backoff_extended_sweep.py": "BACKOFF_SWEEP",
    "backoff_overthrottle.py": "BACKOFF_OVERTHROTTLE",
    "backoff_profile.py": "BACKOFF_PROFILE",
    "backoff_requested_us.py": "BACKOFF_PROFILE",
    "backoff_repro.py": "BACKOFF_REPRO",
    "backoff_sweep.py": "BACKOFF_SWEEP",
    "s1_verify_extime_calibration.py": "S1_EXTIME_CALIBRATION",
}

MANUAL_BUILD_FILES = {
    "b10_backoff_shape_sweep.py",
    "paper_story_a1_paired.py",
    "s2_verify_calibration.py",
    "s3_lock_coverage.py",
    "s3_mocc_lock_coverage.py",
    "s5_permutation_coverage.py",
    "s8a_trigger_coverage.py",
    "s8b_oracle_n_pilot.py",
    "silo_ladder_rung1.py",
    "t152_write_intent_coverage.py",
    "t1998_stock_inline_pair.py",
}

ADMITTED_MANUAL_BUILD_FILES = {"s8a_trigger_coverage.py"}

EXPECTED_NON_ADMISSIBLE = {
    "orchestrator.campaign.b10_backoff_shape_sweep._compile_probe_harnesses",
    "orchestrator.campaign.paper_story_a1_paired._trace0_commands_match",
    "orchestrator.campaign.s2_verify_calibration._broken_build_and_verify",
    "orchestrator.campaign.s3_lock_coverage._build_broken",
    "orchestrator.campaign.s3_mocc_lock_coverage._build_variant",
    "orchestrator.campaign.s3_mocc_lock_coverage._install_dependency",
    "orchestrator.campaign.s5_permutation_coverage._build_broken",
    "orchestrator.campaign.s8b_expected_materialization.produce_expected_materialization_sha256",
    "orchestrator.campaign.s8b_oracle_n_pilot.build_binaries",
    "orchestrator.campaign.t152_write_intent_coverage._build",
    "orchestrator.campaign.t1998_stock_inline_pair._build_dir_from_build",
    "orchestrator.campaign.silo_ladder_rung1._build_variant",
    "orchestrator.campaign.silo_ladder_rung1._correctness_command",
}

_EXPECTED_REPO_STOCK_PIN = "511c953"


def _source(*, stock: bool, ccbench_commit: str = "historical-test-pin") -> SourceEvidence:
    return SourceEvidence(
        schema_version="source-evidence/v1",
        source_root="/tmp/izanagi-u3-source",
        ccbench_commit=ccbench_commit,
        genome_sha256="1" * 64,
        src_token=STOCK if stock else "2" * 64,
        source_bytes_sha256="3" * 64,
        tracked_clean=stock,
        tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256 if stock else "4" * 64,
        tracked_paths=() if stock else ("cc/silo/include/transaction.hh",),
    )


def _tracked_python_paths() -> tuple[str, ...]:
    proc = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.py"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return tuple(
        item.decode("utf-8") for item in proc.stdout.split(b"\0") if item
    )


def _authority_scan_paths() -> tuple[str, ...]:
    """Return the repository-wide tracked Python population for the AST audit."""

    return _tracked_python_paths()


def _dotted_name(node: ast.AST) -> str | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def _static_strings(
    node: ast.AST,
    bindings: dict[str, frozenset[str]],
) -> frozenset[str]:
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return frozenset({node.value})
    if isinstance(node, ast.Name):
        return bindings.get(node.id, frozenset())
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_strings(node.left, bindings)
        right = _static_strings(node.right, bindings)
        values = (a + b for a in left for b in right)
        return frozenset(
            sorted(values, key=lambda value: (len(value), value))[
                :_STATIC_STRING_VALUE_LIMIT
            ]
        )
    return frozenset()


def _resolution_bindings(nodes: tuple[ast.AST, ...]):
    import_module_names = set()
    getattr_names = {"getattr", "builtins.getattr"}
    globals_names = {"globals", "builtins.globals"}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    import_module_names.add(
                        f"{alias.asname or alias.name}.import_module"
                    )
                elif alias.name == "builtins":
                    getattr_names.add(f"{alias.asname or alias.name}.getattr")
                    globals_names.add(f"{alias.asname or alias.name}.globals")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "importlib":
                import_module_names.update(
                    alias.asname or alias.name
                    for alias in node.names if alias.name == "import_module"
                )
            elif node.module == "builtins":
                getattr_names.update(
                    alias.asname or alias.name
                    for alias in node.names if alias.name == "getattr"
                )
                globals_names.update(
                    alias.asname or alias.name
                    for alias in node.names if alias.name == "globals"
                )
    return import_module_names, getattr_names, globals_names


def _simple_assignments(nodes: tuple[ast.AST, ...]):
    for node in nodes:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                yield node.target.id, node.value


def _static_string_dependencies(node: ast.AST) -> frozenset[str]:
    if isinstance(node, ast.Name):
        return frozenset({node.id})
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return (
            _static_string_dependencies(node.left)
            | _static_string_dependencies(node.right)
        )
    return frozenset()


def _static_string_bindings(
    assignments: tuple[tuple[str, ast.AST], ...],
) -> dict[str, frozenset[str]]:
    """Propagate bounded literal/concatenation values without rescanning all assignments."""

    dependencies: dict[str, set[int]] = {}
    assignment_names = []
    for index, (_target, value) in enumerate(assignments):
        names = _static_string_dependencies(value)
        assignment_names.append(names)
        for name in names:
            dependencies.setdefault(name, set()).add(index)

    strings: dict[str, frozenset[str]] = {}
    pending = list(range(len(assignments)))
    queued = set(pending)
    while pending:
        index = pending.pop()
        queued.remove(index)
        target, value = assignments[index]
        # A self-referential runtime update is not a static binding.  Skipping it also keeps the
        # bounded abstraction from manufacturing successively longer synthetic values.
        if target in assignment_names[index]:
            continue
        static_values = _static_strings(value, strings)
        combined = frozenset(
            sorted(
                strings.get(target, frozenset()) | static_values,
                key=lambda item: (len(item), item),
            )[:_STATIC_STRING_VALUE_LIMIT]
        )
        if combined == strings.get(target, frozenset()):
            continue
        strings[target] = combined
        for dependent in dependencies.get(target, set()):
            if dependent not in queued:
                pending.append(dependent)
                queued.add(dependent)
    return strings


def _build_admission_bindings(tree: ast.AST):
    helpers: dict[str, str] = {}
    modules: set[str] = set()
    helper_namespaces: set[str] = set()
    star_imports = []
    nodes = tuple(ast.walk(tree))
    resolution_bindings = _resolution_bindings(nodes)
    import_module_names, getattr_names, _globals_names = resolution_bindings
    for node in nodes:
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
                "build_admission"):
            for alias in node.names:
                if alias.name == "*":
                    star_imports.append(node.lineno)
                elif alias.name in {_LOW_LEVEL_HELPER, _REGISTERED_HELPER}:
                    helpers[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported = f"{node.module}.{alias.name}" if node.module else alias.name
                if alias.name == "build_admission" and imported.endswith(
                        ".build_admission"):
                    modules.add(alias.asname or alias.name)
                if imported.startswith("orchestrator.campaign."):
                    helper_namespaces.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith("build_admission"):
                    modules.add(alias.asname or alias.name)
                if alias.name.startswith("orchestrator.campaign."):
                    helper_namespaces.add(alias.asname or alias.name)

    assignments = tuple(_simple_assignments(nodes))
    strings = _static_string_bindings(assignments)
    changed = True
    while changed:
        changed = False
        for target, value in assignments:
            helper = _resolved_helper_name(
                value, helpers, modules, helper_namespaces,
            )
            dotted = _dotted_name(value)
            if helper is not None:
                # Conflicting static assignments remain fail-closed: a low-level possibility
                # dominates a registered-helper possibility, and the mapping changes monotonically.
                current = helpers.get(target)
                resolved = (
                    _LOW_LEVEL_HELPER
                    if _LOW_LEVEL_HELPER in {current, helper}
                    else helper
                )
                if current != resolved:
                    helpers[target] = resolved
                    changed = True
            elif dotted in modules and target not in modules:
                modules.add(target)
                changed = True
            elif dotted in helper_namespaces and target not in helper_namespaces:
                helper_namespaces.add(target)
                changed = True
            elif isinstance(value, ast.Call):
                callable_name = _dotted_name(value.func)
                module_names = (
                    _static_strings(value.args[0], strings)
                    if value.args else frozenset()
                )
                if (
                    callable_name in import_module_names
                    and any(name.endswith("build_admission") for name in module_names)
                    and target not in modules
                ):
                    modules.add(target)
                    changed = True
                if callable_name in getattr_names and len(value.args) >= 2:
                    getattr_target = _dotted_name(value.args[0])
                    attributes = _static_strings(value.args[1], strings)
                    authority_attributes = attributes & {
                        _LOW_LEVEL_HELPER,
                        _REGISTERED_HELPER,
                    }
                    if (
                        getattr_target in modules
                        and authority_attributes
                    ):
                        current = helpers.get(target)
                        attribute = (
                            _LOW_LEVEL_HELPER
                            if _LOW_LEVEL_HELPER in authority_attributes
                            else _REGISTERED_HELPER
                        )
                        resolved = (
                            _LOW_LEVEL_HELPER
                            if _LOW_LEVEL_HELPER in {current, attribute}
                            else attribute
                        )
                        if current != resolved:
                            helpers[target] = resolved
                            changed = True
    return (
        helpers,
        modules,
        helper_namespaces,
        strings,
        star_imports,
        resolution_bindings,
        nodes,
    )


def _resolved_helper_name(
    func: ast.AST,
    helpers: dict[str, str],
    modules: set[str],
    helper_namespaces: set[str],
) -> str | None:
    dotted = _dotted_name(func)
    if dotted is None:
        return None
    if dotted in helpers:
        return helpers[dotted]
    namespace, separator, leaf = dotted.rpartition(".")
    if (
        separator
        and leaf in {_LOW_LEVEL_HELPER, _REGISTERED_HELPER}
        and (namespace in modules or namespace in helper_namespaces)
    ):
        return leaf
    return None


class _AuthorityCallVisitor(ast.NodeVisitor):
    def __init__(
        self,
        helpers: dict[str, str],
        modules: set[str],
        helper_namespaces: set[str],
    ) -> None:
        self._helpers = helpers
        self._modules = modules
        self._helper_namespaces = helper_namespaces
        self._function_stack: list[str] = []
        self._allowed_low_level_loads: set[int] = set()
        self.calls: list[tuple[str, ast.Call, tuple[str, ...]]] = []
        self.violations: list[tuple[int, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        helper = _resolved_helper_name(
            node.func,
            self._helpers,
            self._modules,
            self._helper_namespaces,
        )
        if helper is not None:
            self.calls.append((helper, node, tuple(self._function_stack)))
            if helper == _LOW_LEVEL_HELPER:
                self._allowed_low_level_loads.add(id(node.func))
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if (
            isinstance(node.ctx, ast.Load)
            and id(node) not in self._allowed_low_level_loads
            and _resolved_helper_name(
                node, self._helpers, self._modules, self._helper_namespaces,
            )
            == _LOW_LEVEL_HELPER
        ):
            self.violations.append(
                (node.lineno, "low-level helper binding used outside direct Call.func")
            )

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if (
            isinstance(node.ctx, ast.Load)
            and id(node) not in self._allowed_low_level_loads
            and _resolved_helper_name(
                node, self._helpers, self._modules, self._helper_namespaces,
            )
            == _LOW_LEVEL_HELPER
        ):
            self.violations.append(
                (node.lineno, "low-level helper binding used outside direct Call.func")
            )
        self.generic_visit(node)


def _dynamic_authority_resolution_violations(
    nodes: tuple[ast.AST, ...],
    *,
    build_admission_modules: set[str],
    string_bindings: dict[str, frozenset[str]],
    resolution_bindings: tuple[set[str], set[str], set[str]],
) -> list[tuple[int, str]]:
    """Reject dynamic resolution on the authority route; unrelated ``getattr`` stays valid."""

    import_module_names, getattr_names, globals_names = resolution_bindings
    violations = []
    for node in nodes:
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Call):
            globals_call = _dotted_name(node.value.func)
            attributes = _static_strings(node.slice, string_bindings)
            if globals_call in globals_names and attributes & _AUTHORITY_DYNAMIC_NAMES:
                violations.append((node.lineno, "dynamic globals lookup on coder-authority route"))
            continue
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted_name(node.func)
        imported_modules = (
            _static_strings(node.args[0], string_bindings)
            if node.args else frozenset()
        )
        if (
            dotted in import_module_names
            and any(name.endswith("build_admission") for name in imported_modules)
        ):
            violations.append((node.lineno, "dynamic import on authority-sensitive module"))
            continue
        if dotted not in getattr_names:
            continue
        target = _dotted_name(node.args[0]) if node.args else None
        attributes = (
            _static_strings(node.args[1], string_bindings)
            if len(node.args) >= 2 else frozenset()
        )
        if target in build_admission_modules or attributes & _AUTHORITY_DYNAMIC_NAMES:
            violations.append((node.lineno, "dynamic getattr on coder-authority route"))
    return violations


def _module_name(relative_path: str) -> str:
    path = Path(relative_path)
    return ".".join(path.with_suffix("").parts)


def _audit_authority_source(relative_path: str, source: str):
    tree = ast.parse(source, filename=relative_path)
    (
        helpers,
        modules,
        helper_namespaces,
        strings,
        star_imports,
        resolution_bindings,
        nodes,
    ) = _build_admission_bindings(tree)
    visitor = _AuthorityCallVisitor(helpers, modules, helper_namespaces)
    visitor.visit(tree)
    dynamic = _dynamic_authority_resolution_violations(
        nodes,
        build_admission_modules=modules,
        string_bindings=strings,
        resolution_bindings=resolution_bindings,
    )
    return visitor.calls, sorted(visitor.violations + dynamic), star_imports


def _enclosing_function(enclosing: tuple[str, ...]) -> str:
    return ".".join(enclosing) if enclosing else "<module>"


def _low_level_call_inventory(relative_path: str, calls):
    return Counter(
        (relative_path, _enclosing_function(enclosing), helper)
        for helper, _call, enclosing in calls
        if helper == _LOW_LEVEL_HELPER
    )


def _low_level_allowlist_violations(relative_path: str, calls):
    actual = _low_level_call_inventory(relative_path, calls)
    expected = {
        (path, function, helper): count
        for path, function, helper, count in _LOW_LEVEL_ISSUER_ALLOWLIST
        if path == relative_path
    }
    return [
        (*key, actual.get(key, 0), expected.get(key, 0))
        for key in sorted(set(actual) | set(expected))
        if actual.get(key, 0) != expected.get(key, 0)
    ]


def test_tracked_python_coder_authority_ast_closure_is_exact():
    """M10 is structural coverage, not evidence of unregistered-issuer runtime denial.

    The M9 unregistered-caller negative is the runtime-denial evidence; this repository-wide AST
    equality check is supplemental and kills M10 structurally through scan-root equality.
    """

    tracked = set(_tracked_python_paths())
    scanned = set(_authority_scan_paths())
    assert scanned == tracked
    allowlisted_paths = {item[0] for item in _LOW_LEVEL_ISSUER_ALLOWLIST}
    assert allowlisted_paths <= scanned

    low_level_calls = Counter()
    registered_calls = []
    dynamic_violations = []
    star_imports = []
    for relative_path in sorted(scanned):
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        calls, dynamic, stars = _audit_authority_source(relative_path, source)
        dynamic_violations.extend(
            (relative_path, line, reason) for line, reason in dynamic
        )
        star_imports.extend((relative_path, line) for line in stars)
        for helper, call, enclosing in calls:
            if helper == _LOW_LEVEL_HELPER:
                low_level_calls.update(
                    _low_level_call_inventory(relative_path, [(helper, call, enclosing)])
                )
            elif relative_path.startswith("orchestrator/campaign/"):
                registered_calls.append((relative_path, call, enclosing))

    expected_low_level_calls = {
        (path, function, helper): count
        for path, function, helper, count in _LOW_LEVEL_ISSUER_ALLOWLIST
    }
    assert low_level_calls == expected_low_level_calls
    assert dynamic_violations == []
    assert star_imports == []
    assert len(registered_calls) == len(CLOSED_CODER_ENTRYPOINT_SITES)

    actual_sites = set()
    for relative_path, call, enclosing in registered_calls:
        assert enclosing and enclosing[-1] == "main", relative_path
        actual_site = f"{_module_name(relative_path)}.main"
        values = [
            keyword.value for keyword in call.keywords
            if keyword.arg == "coder_entrypoint_site"
        ]
        assert len(values) == 1, actual_site
        value = values[0]
        assert isinstance(value, ast.Constant), actual_site
        assert type(value.value) is str, actual_site
        assert value.value == actual_site
        actual_sites.add(actual_site)
    assert actual_sites == set(CLOSED_CODER_ENTRYPOINT_SITES)
    assert actual_sites == set(EXPECTED_CODER_SITES)


def test_low_level_issuer_allowlist_rejects_prefix_and_nested_paths():
    """M11 reaches the real matcher; neither direction of prefix matching is exact."""

    path = (
        "output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/"
        "smoke_driver.py"
    )
    source = (
        "from campaign.build_admission import "
        "add_coder_build_authority_argument\n"
        "def main():\n    add_coder_build_authority_argument(parser)\n"
    )
    calls, violations, stars = _audit_authority_source(path, source)
    assert violations == [] and stars == []
    assert _low_level_allowlist_violations(path, calls) == []

    prefix_decoy = path.removesuffix(".py")
    calls, violations, stars = _audit_authority_source(prefix_decoy, source)
    assert violations == [] and stars == []
    assert _low_level_allowlist_violations(prefix_decoy, calls) == [
        (prefix_decoy, "main", _LOW_LEVEL_HELPER, 1, 0),
    ]

    for decoy_path in (path + ".copy.py", path + "/nested.py"):
        calls, violations, stars = _audit_authority_source(decoy_path, source)
        assert violations == [] and stars == []
        assert _low_level_allowlist_violations(decoy_path, calls) == [
            (decoy_path, "main", _LOW_LEVEL_HELPER, 1, 0),
        ]


def test_low_level_issuer_allowlist_rejects_extra_call_and_function():
    """Exact call-site cardinality rejects same-function and new-function issuers."""

    path = (
        "output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/"
        "smoke_driver.py"
    )
    prefix = (
        "from campaign.build_admission import "
        "add_coder_build_authority_argument\n"
    )
    allowed = prefix + "def main():\n    add_coder_build_authority_argument(parser)\n"
    calls, dynamic, stars = _audit_authority_source(path, allowed)
    assert dynamic == [] and stars == []
    assert _low_level_allowlist_violations(path, calls) == []

    second_call = allowed + "    add_coder_build_authority_argument(parser)\n"
    calls, _, _ = _audit_authority_source(path, second_call)
    assert _low_level_allowlist_violations(path, calls) == [
        (path, "main", _LOW_LEVEL_HELPER, 2, 1),
    ]

    other_function = allowed + (
        "def issue_again():\n    add_coder_build_authority_argument(parser)\n"
    )
    calls, _, _ = _audit_authority_source(path, other_function)
    assert _low_level_allowlist_violations(path, calls) == [
        (path, "issue_again", _LOW_LEVEL_HELPER, 1, 0),
    ]


def test_authority_ast_audit_rejects_import_alias_and_multistage_name_alias():
    source = (
        "from orchestrator.campaign.build_admission import "
        "add_coder_build_authority_argument as imported_issuer\n"
        "issuer = imported_issuer\n"
        "second = issuer\n"
        "def issue():\n    second(parser)\n"
    )
    path = "synthetic/alias_issuer.py"
    calls, violations, stars = _audit_authority_source(path, source)
    assert violations == [
        (2, "low-level helper binding used outside direct Call.func"),
        (3, "low-level helper binding used outside direct Call.func"),
    ]
    assert stars == []
    assert [(helper, enclosing) for helper, _call, enclosing in calls] == [
        (_LOW_LEVEL_HELPER, ("issue",)),
    ]
    assert _low_level_allowlist_violations(path, calls) == [
        (path, "issue", _LOW_LEVEL_HELPER, 1, 0),
    ]


def test_authority_ast_audit_rejects_tuple_storage_and_subscript_call():
    source = (
        "from orchestrator.campaign.build_admission import "
        "add_coder_build_authority_argument as helper\n"
        "(helper,)[0](parser)\n"
    )
    path = "synthetic/tuple_issuer.py"
    calls, violations, stars = _audit_authority_source(path, source)
    assert calls == [] and stars == []
    assert violations == [
        (2, "low-level helper binding used outside direct Call.func"),
    ]


def test_authority_ast_audit_rejects_dict_storage_and_subscript_call():
    source = (
        "from orchestrator.campaign.build_admission import "
        "add_coder_build_authority_argument as helper\n"
        "{'x': helper}['x'](parser)\n"
    )
    path = "synthetic/dict_issuer.py"
    calls, violations, stars = _audit_authority_source(path, source)
    assert calls == [] and stars == []
    assert violations == [
        (2, "low-level helper binding used outside direct Call.func"),
    ]


def test_authority_ast_audit_rejects_helper_passed_as_argument():
    source = (
        "from orchestrator.campaign.build_admission import "
        "add_coder_build_authority_argument as helper\n"
        "pass_helper(helper)\n"
    )
    path = "synthetic/argument_issuer.py"
    calls, violations, stars = _audit_authority_source(path, source)
    assert calls == [] and stars == []
    assert violations == [
        (2, "low-level helper binding used outside direct Call.func"),
    ]


def test_authority_ast_audit_rejects_globals_subscript_lookup():
    source = "globals()['add_coder_build_authority_argument'](parser)\n"
    path = "synthetic/globals_issuer.py"
    calls, violations, stars = _audit_authority_source(path, source)
    assert calls == [] and stars == []
    assert violations == [
        (1, "dynamic globals lookup on coder-authority route"),
    ]


def test_authority_ast_audit_rejects_dynamic_resolution():
    getattr_source = (
        "from orchestrator.campaign import build_admission as admission\n"
        "getattr(admission, 'add_registered_coder_build_authority_argument')\n"
    )
    _, violations, _ = _audit_authority_source("fixture_getattr.py", getattr_source)
    assert violations == [(2, "dynamic getattr on coder-authority route")]

    import_source = (
        "from orchestrator.campaign.build_admission import "
        "add_registered_coder_build_authority_argument\n"
        "import importlib\n"
        "importlib.import_module('orchestrator.campaign.build_admission')\n"
    )
    _, violations, _ = _audit_authority_source("fixture_import.py", import_source)
    assert violations == [(3, "dynamic import on authority-sensitive module")]

    statically_bound_dynamic_source = (
        "import importlib\n"
        "module_name = 'orchestrator.campaign.' + 'build_admission'\n"
        "attribute_name = 'add_coder_' + 'build_authority_argument'\n"
        "admission = importlib.import_module(module_name)\n"
        "issuer = getattr(admission, attribute_name)\n"
        "issuer(parser)\n"
    )
    path = "synthetic/statically_bound_dynamic_issuer.py"
    calls, violations, stars = _audit_authority_source(
        path, statically_bound_dynamic_source,
    )
    assert stars == []
    assert [(helper, enclosing) for helper, _call, enclosing in calls] == [
        (_LOW_LEVEL_HELPER, ()),
    ]
    assert _low_level_allowlist_violations(path, calls) == [
        (path, "<module>", _LOW_LEVEL_HELPER, 1, 0),
    ]
    assert violations == [
        (4, "dynamic import on authority-sensitive module"),
        (5, "dynamic getattr on coder-authority route"),
    ]


def test_authority_ast_audit_ignores_unrelated_local_same_leaf_function():
    source = (
        "def add_coder_build_authority_argument(parser):\n    return parser\n"
        "add_coder_build_authority_argument(parser)\n"
    )
    path = "synthetic/unrelated_same_leaf.py"
    calls, violations, stars = _audit_authority_source(path, source)
    assert calls == []
    assert violations == []
    assert stars == []


def _pipeline_admission(source, context, *, capability_resolver=None):
    contract = env_contract.lookup("linux-baremetal")
    authorization = env_contract.authorize("linux-baremetal")
    genome = Genome("silo", {"BACK_OFF": 1})
    source = replace(
        source,
        genome_sha256=hashlib.sha256(
            genome.canonical().encode("utf-8")
        ).hexdigest(),
    )
    root = tempfile.mkdtemp(prefix="izanagi_p3_admission_positive_")
    layout = CampaignLayout(root=root).ensure()
    seen = []

    def stop_at_build(_genome, _commit, trace, **kwargs):
        assert trace is True
        seen.append(kwargs["admission"].provenance)
        raise RuntimeError("stop after public pipeline admission")

    try:
        with mock.patch.object(
                pipeline.source_digest, "resolve_evidence",
                lambda *_args, **_kwargs: source), mock.patch.object(
                    pipeline.buildcache, "build", stop_at_build):
            result = pipeline.evaluate(
                genome, layout, contract.env_tag, source.ccbench_commit,
                pipeline.PerfConfig(records=1, threads=1), contract.clocks_per_us,
                numactl=contract.numactl,
                do_bench=False, log=lambda *_args: None,
                authorization_contract=authorization,
                build_context=context,
                capability_resolver=capability_resolver,
                src_token=source.src_token,
            )
        records = wal.read_records(layout)
        return result, seen, records
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_all_six_registered_sites_issue_site_bound_opaque_authority():
    for site in sorted(EXPECTED_CODER_SITES):
        parser = argparse.ArgumentParser()
        add_registered_coder_build_authority_argument(
            parser,
            coder_entrypoint_site=site,
        )
        authority = parser.parse_args([
            "--allow-coder-derived-build"
        ]).coder_build_authority
        assert authority._coder_entrypoint_site == site
        context = build_run_context(
            generator_id=GeneratorId.BACKOFF_SWEEP,
            coder_authority=authority,
        )
        assert context._coder_entrypoint_site == site
        result, seen, records = _pipeline_admission(_source(stock=False), context)
        assert result.aborted
        assert seen == [BuildProvenance.CODER_AUTHORED]
        assert [record.stage for record in records] == ["build_start", "abort"]


def test_unregistered_site_is_rejected_before_token_build_or_wal():
    """M9 runtime evidence: an unregistered caller is denied before token/build/WAL."""

    site = "orchestrator.campaign.unregistered_driver.main"
    parser = argparse.ArgumentParser()
    add_registered_coder_build_authority_argument(
        parser,
        coder_entrypoint_site=site,
    )
    token_spy = []
    build_spy = []
    wal_spy = []

    def token_hex(_size):
        token_spy.append("token")
        return "9" * 64

    denied = None
    with mock.patch.object(build_admission.secrets, "token_hex", token_hex):
        try:
            authority = parser.parse_args([
                "--allow-coder-derived-build"
            ]).coder_build_authority
        except BuildAdmissionError as exc:
            denied = str(exc)
        else:  # mutation control: an M9 pass-through reaches the real public pipeline seam.
            context = build_run_context(
                generator_id=GeneratorId.BACKOFF_SWEEP,
                coder_authority=authority,
            )
            _result, build_seen, records = _pipeline_admission(
                _source(stock=False), context,
            )
            build_spy.extend(build_seen)
            wal_spy.extend(records)

    assert denied == f"unregistered coder entry point: {site}"
    assert token_spy == []
    assert build_spy == []
    assert wal_spy == []


def _public_s6_machine_admission():
    root = tempfile.mkdtemp(prefix="izanagi_p3_s6_public_")
    ccbench = os.path.join(root, "external", "ccbench")
    install_condition_gate_build_fixture(ccbench)
    Path(ccbench, "cc", "silo", "transaction.cc").write_text(
        SORT_VARIANT_SOURCE, encoding="utf-8",
    )
    compilers = condition_gate_compilers()
    if compilers is None:
        pytest.skip("condition gate fixture requires real compilers and CMake")
    layout = CampaignLayout(root=os.path.join(root, "campaign")).ensure()
    machine_name = S6.CANDIDATES[0][0]
    seen = []
    passed = SimpleNamespace(passed=True)

    def evidence_for(genome, commit, source_root):
        assert commit == _EXPECTED_REPO_STOCK_PIN == S6.PIN
        return SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.abspath(source_root),
            ccbench_commit=_EXPECTED_REPO_STOCK_PIN,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token="6" * 64,
            source_bytes_sha256="7" * 64,
            tracked_clean=False,
            tracked_diff_sha256="8" * 64,
            tracked_paths=("cc/silo/transaction.cc",),
        )

    def resolve(genome, commit, ccbench_dir="", **_kwargs):
        return evidence_for(genome, commit, ccbench_dir).src_token

    def resolve_evidence(genome, commit, *, ccbench_dir="", **_kwargs):
        return evidence_for(genome, commit, ccbench_dir)

    def stop_at_build(_genome, _commit, trace, **kwargs):
        assert trace is True
        seen.append(kwargs["admission"].provenance)
        raise RuntimeError("stop after public S6 admission")

    def run_through_pipeline(cfg, genomes, perf, env_tag, clocks_per_us, **kwargs):
        result = pipeline.evaluate(
            genomes[0], layout, env_tag, cfg.ccbench_commit, perf,
            clocks_per_us, do_bench=False, log=lambda *_args: None,
            numactl=kwargs["numactl"],
            authorization_contract=kwargs["authorization_contract"],
            ccbench_dir=kwargs["ccbench_dir"],
            cache_root=kwargs["cache_root"],
            build_context=kwargs["build_context"],
            capability_resolver=kwargs["capability_resolver"],
        )
        return SimpleNamespace(results=[result])

    try:
        from orchestrator.campaign import patchharness
        with contextlib.ExitStack() as stack:
            for target, name, value in (
                    (S6, "_assert_single_tenant", lambda: None),
                    (S6, "_repo_root", lambda: root),
                    (S6, "campaign_layout", lambda _campaign_id: layout),
                    (patchharness, "assert_pinned_clean", lambda *_args: None),
                    (patchharness, "applied",
                     lambda *_args, **_kwargs: contextlib.nullcontext()),
                    (L, "quarantine", lambda *_args, **_kwargs: (passed, "", "", "")),
                    (S6.buildcache, "DEFAULT_CXX", compilers[1]),
                    (S6.source_digest, "resolve", resolve),
                    (pipeline.source_digest, "resolve_evidence", resolve_evidence),
                    (pipeline.buildcache, "build", stop_at_build),
                    (S6, "run_campaign", run_through_pipeline)):
                stack.enter_context(mock.patch.object(target, name, value))
            S6.run_sweep(
                "balanced", names=[machine_name], isolate=False,
                log=lambda *_args: None,
            )
        return seen
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_stock_machine_and_opted_in_coder_paths_remain_accepted():
    stock_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    stock_result, stock_seen, _ = _pipeline_admission(
        _source(stock=True, ccbench_commit=_EXPECTED_REPO_STOCK_PIN),
        stock_context,
    )
    assert stock_result.aborted and stock_seen == [BuildProvenance.STOCK_BASELINE]

    assert _public_s6_machine_admission() == [BuildProvenance.MACHINE_GENERATED]

    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    authority = parser.parse_args(["--allow-coder-derived-build"]).coder_build_authority
    coder_context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP, coder_authority=authority,
    )
    coder_result, coder_seen, _ = _pipeline_admission(
        _source(stock=False), coder_context,
    )
    assert coder_result.aborted and coder_seen == [BuildProvenance.CODER_AUTHORED]
    assert "nonce" not in repr(coder_context.policy.as_preimage()).lower()


def test_authorityless_trigger_coder_is_rejected_before_build_spy():
    root = tempfile.mkdtemp(prefix="izanagi_p3_trigger_negative_")
    layout = CampaignLayout(root=os.path.join(root, "campaign")).ensure()
    sub = os.path.join(root, "ccbench")
    install_condition_gate_build_fixture(sub)
    Path(sub, TRIGGER.SOURCE_REL).write_text(
        TRIGGER_GATING_SOURCE, encoding="utf-8",
    )
    compilers = condition_gate_compilers()
    if compilers is None:
        pytest.skip("condition gate fixture requires real compilers and CMake")
    context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    contract = env_contract.lookup(TRIGGER.ENV_TAG)
    seen = []

    def dirty_evidence(genome, commit, *, ccbench_dir="", **_kwargs):
        assert commit == _EXPECTED_REPO_STOCK_PIN == TRIGGER.PIN
        return SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.abspath(ccbench_dir),
            ccbench_commit=_EXPECTED_REPO_STOCK_PIN,
            genome_sha256=hashlib.sha256(
                genome.canonical().encode("utf-8")
            ).hexdigest(),
            src_token="2" * 64,
            source_bytes_sha256="3" * 64,
            tracked_clean=False,
            tracked_diff_sha256="4" * 64,
            tracked_paths=("cc/silo/transaction.cc",),
        )

    def build_spy(*_args, **_kwargs):
        seen.append(_kwargs)
        raise AssertionError("authorityless trigger source reached build")

    def run_through_pipeline(cfg, genomes, perf, env_tag, clocks_per_us, **kwargs):
        result = pipeline.evaluate(
            genomes[0], layout, env_tag, cfg.ccbench_commit, perf,
            clocks_per_us, do_bench=False, log=lambda *_args: None,
            numactl=kwargs["numactl"],
            authorization_contract=kwargs["authorization_contract"],
            ccbench_dir=kwargs["ccbench_dir"],
            cache_root=kwargs["cache_root"],
            build_context=kwargs["build_context"],
            trigger_gate_binding=kwargs["trigger_gate_binding"],
        )
        return SimpleNamespace(results=[result], skipped=0)

    planner = L.PlannerProposal(
        axis=TRIGGER.MARKER_ID, direction="explore_both", magnitude="small",
    )
    coder = TRIGGER.CoderProposalTriggerGating(
        axis=TRIGGER.MARKER_ID,
        wire="11111",
    )
    auditor = AuditorVerdict(verdict="pass", diff_digest="fixture")
    try:
        from orchestrator.campaign import patchharness
        with contextlib.ExitStack() as stack:
            for target, name, value in (
                    (TRIGGER, "_current_site", lambda: TRIGGER.site_policy.OTHER),
                    (TRIGGER, "_lookup", lambda _env_tag: contract),
                    (TRIGGER, "exploration_campaign_layout", lambda _cid: layout),
                    (TRIGGER, "_assert_resume_allowed", lambda *_args: None),
                    (TRIGGER, "_quarantine_and_audit", lambda *_args, **_kwargs: None),
                    (TRIGGER.buildcache, "compilers_for_current_site",
                     lambda: compilers),
                    (patchharness, "applied",
                     lambda *_args, **_kwargs: contextlib.nullcontext()),
                    (pipeline.source_digest, "resolve_evidence", dirty_evidence),
                    (pipeline.buildcache, "build", build_spy),
                    (TRIGGER, "run_campaign", run_through_pipeline)):
                stack.enter_context(mock.patch.object(target, name, value))
            outcome = TRIGGER.run_one_iteration(
                TRIGGER.default_cfg(), TRIGGER.default_perf(), planner, coder,
                auditor, L.LoopState(start_wall=0.0), sub, do_build=True,
                layout=layout, log=lambda *_args: None, build_context=context,
            )
        records = wal.read_records(layout)
        assert outcome["outcome"] == "aborted"
        assert seen == []
        assert [record.stage for record in records] == ["trigger_binding", "build_start", "abort"]
        assert records[-1].payload["reason"] == "admission-error"
        assert records[-1].payload["error"].startswith("BuildAdmissionError:")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dirty_noop_stock_token_enters_coder_admission_namespace():
    parser = argparse.ArgumentParser()
    add_coder_build_authority_argument(parser)
    context = build_run_context(
        generator_id=GeneratorId.BACKOFF_SWEEP,
        coder_authority=parser.parse_args(
            ["--allow-coder-derived-build"]
        ).coder_build_authority,
    )
    dirty_noop = replace(_source(stock=False), src_token=STOCK)
    assert derive_build_admission(
        context, dirty_noop,
    ).provenance is BuildProvenance.CODER_AUTHORED


def test_machine_callers_use_closed_generator_receipts():
    for filename, enum_name in MACHINE_CALLERS.items():
        source = (CAMPAIGN / filename).read_text(encoding="utf-8")
        assert "attest_generator_output(" in source, filename
        assert f"GeneratorId.{enum_name}" in source, filename
        assert "BuildProvenance" not in source, filename
    coverage = (CAMPAIGN / "s8a_trigger_coverage.py").read_text(encoding="utf-8")
    assert "GeneratorId.S8A_TRIGGER_SWEEP" in coverage
    assert "attest_generator_output(" in coverage
    assert "require_build_admission(" in coverage
    frequency = (CAMPAIGN / "s8a_trigger_freq.py").read_text(encoding="utf-8")
    assert "admission_receipts=result[\"build_admissions\"]" in frequency


def test_python_ccbench_manual_materializers_are_explicitly_non_admissible():
    actual_manual_files = {
        path.name for path in CAMPAIGN.glob("*.py")
        if "--build" in path.read_text(encoding="utf-8")
        and path.name != "buildcache.py"
    }
    assert actual_manual_files == MANUAL_BUILD_FILES
    for filename in ADMITTED_MANUAL_BUILD_FILES:
        assert "require_build_admission(" in (CAMPAIGN / filename).read_text(
            encoding="utf-8"
        )
    assert set(NON_ADMISSIBLE_MATERIALIZERS) == EXPECTED_NON_ADMISSIBLE
    for materializer in EXPECTED_NON_ADMISSIBLE:
        classification = non_admissible_materializer(materializer)
        assert set(classification) == {"admission_status", "materializer", "reason"}
        assert classification["admission_status"] == NON_ADMISSIBLE
        assert classification["materializer"] == materializer
        assert classification["reason"]


def test_single_registry_has_typed_compatible_projections():
    coder_sites = {
        site for site, registration in MATERIALIZER_ADMISSION_REGISTRY.items()
        if registration.site_kind is CODER_ENTRYPOINT
    }
    direct_sites = {
        site for site, registration in MATERIALIZER_ADMISSION_REGISTRY.items()
        if registration.site_kind is DIRECT_MATERIALIZER
    }
    assert coder_sites == set(EXPECTED_CODER_SITES)
    assert coder_sites == set(CLOSED_CODER_ENTRYPOINT_SITES)
    assert direct_sites.isdisjoint(coder_sites)
    assert set(CLOSED_PYTHON_MATERIALIZER_SITES) == {
        f"{site.rsplit('.', 1)[0].replace('.', '/')}.py:{site.rsplit('.', 1)[1]}"
        for site in direct_sites
    }
    assert {
        registration.admission_status
        for registration in MATERIALIZER_ADMISSION_REGISTRY.values()
    } == {NON_ADMISSIBLE, ADMITTED_GATEWAY}
    assert set(NON_ADMISSIBLE_MATERIALIZERS) == EXPECTED_NON_ADMISSIBLE


def test_registry_declares_intentionally_unclosed_surfaces():
    doc = __import__(
        "orchestrator.campaign.materializer_admission", fromlist=["__doc__"]
    ).__doc__ or ""
    assert "tools/pegasus/*.sh" in doc
    assert "arbitrary binary path" in doc
    assert "does not by itself reject a build downstream" in doc


def _run():
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # noqa: BLE001 - plain-runner result aggregation
            failures += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run())
