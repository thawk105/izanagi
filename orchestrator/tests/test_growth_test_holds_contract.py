"""Non-tautological contract tests for repository-growth test holds."""
from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import orchestrator.tests.conftest as CONF
from orchestrator.tests.growth_test_holds import (
    GROWTH_TEST_HOLDS,
    GuardMode,
    RUN_GROWTH_HELD_TESTS_ENV,
    RUN_GROWTH_HELD_TESTS_TOKEN,
    GrowthTestHold,
    GrowthTestHoldBypassRefused,
    _GUARD_MODES,
    _pytest_drives_current_import,
    _wrap_held_function,
    _validate_hold_rows,
    enforce_held_functions,
    growth_test_hold_inventory,
    growth_test_hold_key_digest,
)
from tools import run_tests as RT


_EXPECTED_HOLD_COUNT = 45
_EXPECTED_KEY_SHA256 = "5a5f7a4f918684cbde6b9267d5535455974d441fa847ab8f070cc8b2e77d3429"
_EXPECTED_ROW_CONTRACT_SHA256 = "8cf20b5f685a38bd9aee4e306792a509d5ebc0314a436a1e16c0fc129466d945"
_HELD_SERIAL_NODE = (
    "test_s8b_repo_scan_invariant.py::"
    "test_real_repository_scan_matches_known_hits_and_has_positive_control"
)
_META_NODE = (
    "test_growth_test_holds_contract.py::test_contract_module_is_not_held"
)
_SHARED_FIXTURE_COLLATERAL = (
    "Holding this node also prevents the shared module fixture from starting, "
    "so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent "
    "golden, and K.verify_document stop too."
)


def _fixture_collateral(detail: str) -> str:
    return f"{_SHARED_FIXTURE_COLLATERAL} {detail}"


_EXPECTED_COLLATERAL_NOTES = {
    "test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract": (
        "Holding this node removes the fixed-size positive check that the current "
        "dev-wave model pins do not over-reject the real repository. Land's "
        "_validate_generated_docs calls the checker with "
        "--expect-active-transaction after a non-noop fold; a noop fold returns "
        "before the check. The wave checker requires check-docs to be specified "
        "exactly once, but executes it in an isolated checkout only for a completed, "
        "passive-green run; incomplete or passive-failing runs do not execute it. "
        "A no-argument tools/check_docs.py invocation remains mandatory for class "
        "2/3 completion; it is not required for other task classes."
    ),
    "test_check_docs.py::test_normative_exact_section_pins_accept_real_repo": (
        "Holding this node removes the fixed-size positive check that normative "
        "section pins do not over-reject the real repository. Land's "
        "_validate_generated_docs calls the checker with "
        "--expect-active-transaction after a non-noop fold; a noop fold returns "
        "before the check. The wave checker requires check-docs to be specified "
        "exactly once, but executes it in an isolated checkout only for a completed, "
        "passive-green run; incomplete or passive-failing runs do not execute it. "
        "A no-argument tools/check_docs.py invocation remains mandatory for class "
        "2/3 completion; it is not required for other task classes."
    ),
    "test_check_docs.py::test_real_repo_clean": (
        "Holding this node removes its fixed-size assertions that the real checker "
        "returns rc=0, reports no violations, and has zero Pegasus admission drift "
        "findings. Land's _validate_generated_docs calls the checker with "
        "--expect-active-transaction after a non-noop fold; a noop fold returns "
        "before the check. The wave checker requires check-docs to be specified "
        "exactly once, but executes it in an isolated checkout only for a completed, "
        "passive-green run; incomplete or passive-failing runs do not execute it. "
        "A no-argument tools/check_docs.py invocation remains mandatory for class "
        "2/3 completion; it is not required for other task classes."
    ),
    "test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies": (
        "Holding this node also removes fixed-size checks for corpus count 48, "
        "disjoint success/failure sets, and the complete JSON-pair partition."
    ),
    "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight": (
        "Holding this node also removes fixed-size checks for the maximum "
        "package, MAX_CANDIDATES/MAX_QUERY_COUNT/MAX_SIGNAL_TOKENS, independent "
        "inspect/pickaxe evidence, and the 45/60-second preflight boundaries."
    ),
    "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper": (
        "Holding this node removes its fixed self-consistency and single-field "
        "tamper rejection checks."
    ),
    "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze": (
        "Holding this node removes its fixed create-only refusal check."
    ),
    "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points": (
        "Holding this node removes its fixed golden checks for registered P2, "
        "backoff, and sort selections."
    ),
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags": (
        "Holding this node removes its fixed S-1b mismatched-flags rejection check."
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin": (
        "Holding this node removes its fixed held/released ccbench-pin positive control."
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper": (
        "Holding this node removes its fixed generator-hash tamper rejection check."
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head": (
        "Holding this node removes its fixed non-ancestor HEAD rejection check."
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper": (
        "Holding this node removes its fixed one-byte freeze tamper rejection check."
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy": (
        "Holding this node removes its fixed copied-source hash tamper rejection check."
    ),
    "test_s1_measurement_freeze.py::test_build_document_rejects_tampered_known_axes_semantics": _fixture_collateral(
        "The node's fixed known-axes semantic tamper rejection check stops too."
    ),
    "test_s1_measurement_freeze.py::test_generate_builds_registered_cells_comparisons_and_schedule": _fixture_collateral(
        "The node's fixed checks for 18 cells, 12 comparisons, schedule shape, seeds, and operating-point flags stop too."
    ),
    "test_s1_measurement_freeze.py::test_generate_refuses_existing_freeze": _fixture_collateral(
        "The node's fixed measurement create-only refusal check stops too."
    ),
    "test_s1_measurement_freeze.py::test_receipt_exists_but_measurement_verify_stays_legacy_strict": _fixture_collateral(
        "The node's fixed legacy-verifier isolation from the T-080 adapter stops too."
    ),
    "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control": _fixture_collateral(
        "The node's fixed recorded-pin hold and release positive control stops too."
    ),
    "test_s1_measurement_freeze.py::test_s1b_pairing_rejects_mismatched_flags": _fixture_collateral(
        "The node's fixed measurement S-1b mismatched-flags rejection check stops too."
    ),
    "test_s1_measurement_freeze.py::test_schedule_is_balanced_and_reproducible": _fixture_collateral(
        "The node's fixed schedule balance and reproducibility checks stop too."
    ),
    "test_s1_measurement_freeze.py::test_verify_rejects_known_axes_material_tamper": _fixture_collateral(
        "The node's fixed known-axes material-hash tamper rejection check stops too."
    ),
    "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_freeze_tamper": _fixture_collateral(
        "The node's fixed one-byte measurement freeze tamper rejection check stops too."
    ),
    "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_workload_flag_tamper": _fixture_collateral(
        "The node's fixed one-byte workload-flag tamper rejection check stops too."
    ),
    "test_s1_measurement_freeze.py::test_verify_rejects_stats_implementation_tamper": _fixture_collateral(
        "The node's fixed statistics-implementation hash tamper rejection check stops too."
    ),
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal": (
        "Holding this node also removes the fixed-size binding-manifest schema refusal aggregation check."
    ),
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated": (
        "Holding this node also removes the fixed-size independent-refusal aggregation and zero-side-effect checks."
    ),
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused": (
        "Holding this node also removes the fixed-size no-active error translation, no-prepare, no-evaluate, and no-write checks."
    ),
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing": (
        "Holding this node also removes fixed-size refusal, no-prepare, no-evaluate, and zero-output checks."
    ),
    "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root": (
        "Holding this node also removes fixed-size checks for exact ROOT wiring, single guard invocation, and builder/writer execution inside that guard."
    ),
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged": (
        "Holding this node also removes fixed-size top-level and nested writer checks and the frozen-output refusal check."
    ),
}


class _Item:
    def __init__(self, node_id: str):
        filename, function = node_id.split("::", 1)
        self.path = Path("/synthetic") / filename
        self.name = function
        self.originalname = function
        self.user_properties: list[tuple[str, object]] = []
        self._markers = []

    def add_marker(self, marker, append: bool = True) -> None:
        mark = getattr(marker, "mark", marker)
        if append:
            self._markers.append(mark)
        else:
            self._markers.insert(0, mark)

    def iter_markers(self, name: str | None = None):
        return (
            marker for marker in self._markers
            if name is None or marker.name == name
        )


class _Terminal:
    def __init__(self):
        self.lines: list[str] = []

    def write_line(self, line: str) -> None:
        self.lines.append(line)


def _config(*, complete: bool = False, terminal=None):
    root = Path(CONF.__file__).resolve().parent
    pluginmanager = SimpleNamespace(
        get_plugin=lambda name: terminal if name == "terminalreporter" else None,
    )
    return SimpleNamespace(
        args=[str(root if complete else root / "test_growth_test_holds_contract.py")],
        invocation_params=SimpleNamespace(args=()),
        pluginmanager=pluginmanager,
        option=SimpleNamespace(numprocesses=None),
    )


def _run_collection_hook(config, items) -> None:
    wrapper = CONF.pytest_collection_modifyitems(config, items)
    next(wrapper)
    with pytest.raises(StopIteration):
        next(wrapper)


def _literal_hold(**changes) -> GrowthTestHold:
    hold = GrowthTestHold(
        hold_axis="commits",
        ruling="2026-08-12 rulings 第 3 束",
        reason="synthetic valid reason",
        correctness_gate=True,
        release_condition="explicit-user-command-only",
        measured_seconds=None,
    )
    return replace(hold, **changes)


def _row_contract_digest() -> str:
    payload = json.dumps(
        [
            [key, hold.hold_axis, hold.ruling, hold.correctness_gate]
            for key, hold in sorted(GROWTH_TEST_HOLDS.items())
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_inventory_count_and_key_digest_are_independently_pinned():
    assert len(GROWTH_TEST_HOLDS) == _EXPECTED_HOLD_COUNT
    assert growth_test_hold_key_digest(GROWTH_TEST_HOLDS) == _EXPECTED_KEY_SHA256
    assert _row_contract_digest() == _EXPECTED_ROW_CONTRACT_SHA256


def test_registry_rows_preserve_current_wave_contract():
    assert {hold.ruling for hold in GROWTH_TEST_HOLDS.values()} == {
        "2026-08-12 rulings 第 3 束",
    }
    assert all(hold.correctness_gate is True for hold in GROWTH_TEST_HOLDS.values())
    assert all(hold.measured_seconds is None for hold in GROWTH_TEST_HOLDS.values())
    assert all(
        hold.release_condition == "explicit-user-command-only"
        for hold in GROWTH_TEST_HOLDS.values()
    )
    assert not any(
        key.startswith("test_s8b_ratified_verify.py::")
        or key.startswith("test_silo_ladder_rung1_evidence.py::")
        for key in GROWTH_TEST_HOLDS
    )
    assert (
        "test_s8b_oracle_driver.py::"
        "test_nonnull_floor_without_active_generation_is_refused"
    ) in GROWTH_TEST_HOLDS
    assert {
        "test_codex_reasoning_ab.py::test_git_answer_object_reinjection_is_rejected",
        "test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive",
        "test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment",
    }.isdisjoint(GROWTH_TEST_HOLDS)


@pytest.mark.parametrize(
    ("key", "hold"),
    [
        ("test_file.py::test_name", _literal_hold(correctness_gate="false")),
        ("test_file.py::test_name", _literal_hold(release_condition="automatic")),
        ("test_file.py:test_name_typo", _literal_hold()),
        ("test_file.py::test_name", _literal_hold(reason=" ")),
        ("test_file.py::test_name", _literal_hold(ruling="\t")),
        ("test_file.py::test_name", _literal_hold(hold_axis="repository_size")),
        ("test_file.py::test_name", _literal_hold(measured_seconds=float("inf"))),
        ("test_file.py::test_name", _literal_hold(measured_seconds=-0.1)),
        ("test_file.py::test_name", _literal_hold(measured_seconds=False)),
        ("test_file.py::test_name", _literal_hold(collateral_note=" \t")),
        ("test_file.py::test_name", _literal_hold(collateral_note=0)),
    ],
)
def test_schema_negative_controls_are_rejected(key, hold):
    with pytest.raises(ValueError):
        _validate_hold_rows(((key, hold),))


def test_empty_and_duplicate_registries_are_rejected():
    with pytest.raises(ValueError):
        _validate_hold_rows(())
    row = ("test_file.py::test_name", _literal_hold())
    with pytest.raises(ValueError):
        _validate_hold_rows((row, row))


def test_collection_hook_attaches_skip_metadata_and_prints_early_summary(monkeypatch):
    monkeypatch.delenv(RUN_GROWTH_HELD_TESTS_ENV, raising=False)
    terminal = _Terminal()
    config = _config(terminal=terminal)
    item = _Item(_HELD_SERIAL_NODE)

    _run_collection_hook(config, [item])

    skip_marks = list(item.iter_markers(name="skip"))
    assert len(skip_marks) == 1
    reason = skip_marks[0].kwargs["reason"]
    assert reason.startswith("IZANAGI_GROWTH_HOLD_V1 ")
    payload = json.loads(reason.split(" ", 1)[1])
    assert payload["node_id"] == _HELD_SERIAL_NODE
    assert payload["hold_axis"] == "tracked_files"
    assert payload["correctness_gate"] is True
    assert payload["release_condition"] == "explicit-user-command-only"
    assert [mark.args for mark in item.iter_markers(name="xdist_group")] == [
        ("real-repo",),
    ]
    assert dict(item.user_properties) == {
        "growth_hold_node_id": _HELD_SERIAL_NODE,
        "growth_hold_axis": "tracked_files",
        "growth_hold_correctness_gate": True,
        "growth_hold_release_condition": "explicit-user-command-only",
    }

    session = SimpleNamespace(config=config)
    CONF.pytest_sessionfinish(session, 0)
    assert terminal.lines[0].startswith("IZANAGI_GROWTH_HOLD_SUMMARY_V1 ")
    assert terminal.lines[1] == reason


def test_collection_hook_opt_in_keeps_real_repo_serialization_without_skip(monkeypatch):
    monkeypatch.setenv(RUN_GROWTH_HELD_TESTS_ENV, RUN_GROWTH_HELD_TESTS_TOKEN)
    item = _Item(_HELD_SERIAL_NODE)

    _run_collection_hook(_config(), [item])

    assert list(item.iter_markers(name="skip")) == []
    assert [mark.args for mark in item.iter_markers(name="xdist_group")] == [
        ("real-repo",),
    ]


def test_collection_hook_rejects_opt_in_typo(monkeypatch):
    monkeypatch.setenv(RUN_GROWTH_HELD_TESTS_ENV, "explicit-user-commnad")
    wrapper = CONF.pytest_collection_modifyitems(_config(), [_Item(_HELD_SERIAL_NODE)])
    with pytest.raises(pytest.UsageError):
        next(wrapper)


def test_complete_collection_rejects_valid_shape_function_typo(monkeypatch):
    typo = (
        "test_s8b_repo_scan_invariant.py::"
        "test_real_repository_scan_matches_known_hits_and_has_positive_control_typo"
    )
    monkeypatch.delenv(RUN_GROWTH_HELD_TESTS_ENV, raising=False)
    monkeypatch.setattr(CONF, "GROWTH_TEST_HOLDS", {typo: _literal_hold()})
    wrapper = CONF.pytest_collection_modifyitems(
        _config(complete=True), [_Item(_HELD_SERIAL_NODE)],
    )
    with pytest.raises(pytest.UsageError, match="missing from complete collection"):
        next(wrapper)


def test_contract_module_is_not_held():
    assert _META_NODE not in GROWTH_TEST_HOLDS
    assert not any(
        key.startswith("test_growth_test_holds_contract.py::")
        for key in GROWTH_TEST_HOLDS
    )


def test_inventory_output_is_sorted_exact_and_marks_correctness_gates():
    first = growth_test_hold_inventory()
    second = growth_test_hold_inventory()
    assert first == second
    keys = sorted(GROWTH_TEST_HOLDS)
    assert first["count"] == _EXPECTED_HOLD_COUNT
    assert first["key_sha256"] == _EXPECTED_KEY_SHA256
    assert first["correctness_gate_keys"] == keys
    assert [row["node_id"] for row in first["holds"]] == keys
    assert all(row["correctness_gate"] is True for row in first["holds"])
    rows = {row["node_id"]: row for row in first["holds"]}
    assert all("collateral_note" in row for row in rows.values())
    assert {
        key: row["collateral_note"]
        for key, row in rows.items()
        if row["collateral_note"] is not None
    } == _EXPECTED_COLLATERAL_NOTES


def test_opt_in_changes_only_suite_identity_not_acceptance_shape(monkeypatch):
    assert RT._RUN_GROWTH_HELD_TESTS_ENV == RUN_GROWTH_HELD_TESTS_ENV
    assert RT._RUN_GROWTH_HELD_TESTS_TOKEN == RUN_GROWTH_HELD_TESTS_TOKEN
    regular = RT._suite_identity([], "", run_growth_held_tests=False)
    opted_in = RT._suite_identity([], "", run_growth_held_tests=True)
    assert regular == ("full", "pytest-orchestrator-full")
    assert opted_in == ("full", "pytest-orchestrator-full-growth-held-opt-in")
    targeted_regular = RT._suite_identity(["test_file.py"], "", run_growth_held_tests=False)
    targeted_opted_in = RT._suite_identity(
        ["test_file.py"], "", run_growth_held_tests=True,
    )
    assert targeted_regular[0] == targeted_opted_in[0] == "targeted"
    assert targeted_regular[1] != targeted_opted_in[1]

    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv(RUN_GROWTH_HELD_TESTS_ENV, raising=False)
    before = (
        RT._is_full_suite([], ""),
        RT._has_no_execution_flag([]),
        RT._has_dispatch_exempt_flag([]),
        RT._is_acceptance_run([]),
    )
    monkeypatch.setenv(RUN_GROWTH_HELD_TESTS_ENV, RUN_GROWTH_HELD_TESTS_TOKEN)
    after = (
        RT._is_full_suite([], ""),
        RT._has_no_execution_flag([]),
        RT._has_dispatch_exempt_flag([]),
        RT._is_acceptance_run([]),
    )
    assert after == before


def _held_filenames() -> tuple[str, ...]:
    return tuple(sorted({node_id.split("::", 1)[0] for node_id in GROWTH_TEST_HOLDS}))


def _is_main_guard(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    comparison = node.test
    return (
        isinstance(comparison.left, ast.Name)
        and comparison.left.id == "__name__"
        and len(comparison.ops) == 1
        and isinstance(comparison.ops[0], ast.Eq)
        and len(comparison.comparators) == 1
        and isinstance(comparison.comparators[0], ast.Constant)
        and comparison.comparators[0].value == "__main__"
    )


def _plain_runner_for_tree(tree: ast.Module) -> str:
    main_guards = [node for node in tree.body if _is_main_guard(node)]
    if not main_guards:
        return "none"
    if len(main_guards) != 1 or not main_guards[0].body:
        return "manual"

    terminal = main_guards[0].body[-1]
    exit_call = None
    if (
        isinstance(terminal, ast.Raise)
        and isinstance(terminal.exc, ast.Call)
        and isinstance(terminal.exc.func, ast.Name)
        and terminal.exc.func.id == "SystemExit"
        and len(terminal.exc.args) == 1
        and not terminal.exc.keywords
    ):
        exit_call = terminal.exc
    elif (
        isinstance(terminal, ast.Expr)
        and isinstance(terminal.value, ast.Call)
        and isinstance(terminal.value.func, ast.Attribute)
        and isinstance(terminal.value.func.value, ast.Name)
        and terminal.value.func.value.id == "sys"
        and terminal.value.func.attr == "exit"
        and len(terminal.value.args) == 1
        and not terminal.value.keywords
    ):
        exit_call = terminal.value

    delegated = exit_call.args[0] if exit_call is not None else None
    return (
        "pytest-delegating"
        if isinstance(delegated, ast.Call)
        and isinstance(delegated.func, ast.Attribute)
        and isinstance(delegated.func.value, ast.Name)
        and delegated.func.value.id == "pytest"
        and delegated.func.attr == "main"
        else "manual"
    )


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }


def _scope_for(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST:
    current = node
    while not isinstance(
        current,
        (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
    ):
        current = parents[current]
    return current


def _static_context(tree: ast.Module):
    parents = _parent_map(tree)
    assignments: dict[ast.AST, dict[str, list[ast.AST]]] = {}
    aliases: dict[ast.AST, dict[str, str | None]] = {tree: {}}

    # Loader APIs count only when an import in the active scope establishes the
    # name.  A same-scope assignment or definition makes the binding ambiguous
    # and therefore unusable for an import-permission decision.
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".", 1)[0]
                aliases[tree][local_name] = (
                    alias.name if alias.asname else local_name
                )
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for alias in node.names:
                if alias.name != "*":
                    aliases[tree][alias.asname or alias.name] = (
                        f"{node.module}.{alias.name}"
                    )

    for node in ast.walk(tree):
        scope = _scope_for(node, parents)
        values = assignments.setdefault(scope, {})
        shadowed_names = set()
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values.setdefault(target.id, []).append(node.value)
                shadowed_names.update(
                    candidate.id for candidate in ast.walk(target)
                    if isinstance(candidate, ast.Name)
                )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                values.setdefault(node.target.id, []).append(node.value)
            shadowed_names.add(node.target.id)
        elif isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
            values.setdefault(node.target.id, []).append(node.value)
            shadowed_names.add(node.target.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node is not tree:
                binding_scope = _scope_for(parents[node], parents)
                aliases.setdefault(binding_scope, {})[node.name] = None
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            shadowed_names.update(
                candidate.id for candidate in ast.walk(node.target)
                if isinstance(candidate, ast.Name)
            )
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            shadowed_names.update(
                candidate.id
                for item in node.items if item.optional_vars is not None
                for candidate in ast.walk(item.optional_vars)
                if isinstance(candidate, ast.Name)
            )
        elif isinstance(node, ast.ExceptHandler) and node.name is not None:
            shadowed_names.add(node.name)

        for name in shadowed_names:
            aliases.setdefault(scope, {})[name] = None

        if isinstance(node, (ast.Import, ast.ImportFrom)) and parents[node] is not tree:
            scope_aliases = aliases.setdefault(scope, {})
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local_name = alias.asname or alias.name.split(".", 1)[0]
                    scope_aliases[local_name] = (
                        alias.name if alias.asname else local_name
                    )
            elif node.module is not None:
                for alias in node.names:
                    if alias.name != "*":
                        scope_aliases[alias.asname or alias.name] = (
                            f"{node.module}.{alias.name}"
                        )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_aliases = aliases.setdefault(node, {})
            arguments = (
                node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            )
            if node.args.vararg is not None:
                arguments.append(node.args.vararg)
            if node.args.kwarg is not None:
                arguments.append(node.args.kwarg)
            for argument in arguments:
                function_aliases[argument.arg] = None
    return parents, assignments, aliases


def _scope_chain(scope: ast.AST, parents: dict[ast.AST, ast.AST]):
    current = scope
    while True:
        yield current
        if isinstance(current, ast.Module):
            return
        current = _scope_for(parents[current], parents)


def _resolve_name(
    name: str,
    scope: ast.AST,
    parents: dict[ast.AST, ast.AST],
    assignments: dict[ast.AST, dict[str, list[ast.AST]]],
) -> tuple[ast.AST, ast.AST] | None:
    for candidate_scope in _scope_chain(scope, parents):
        values = assignments.get(candidate_scope, {}).get(name)
        if values is not None:
            return (values[0], candidate_scope) if len(values) == 1 else None
    return None


def _dotted_name(node: ast.AST) -> str | None:
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def _qualified_name(
    node: ast.AST,
    scope: ast.AST,
    parents: dict[ast.AST, ast.AST],
    aliases: dict[ast.AST, dict[str, str | None]],
) -> str | None:
    dotted = _dotted_name(node)
    if dotted is None:
        return None
    first, separator, suffix = dotted.partition(".")
    for candidate_scope in _scope_chain(scope, parents):
        scope_aliases = aliases.get(candidate_scope, {})
        if first in scope_aliases:
            replacement = scope_aliases[first]
            if replacement is None:
                return None
            return replacement + (separator + suffix if separator else "")
    return dotted if first in {"exec", "open", "str"} else None


def _canonical_test_path(filename: str) -> Path:
    path = Path(filename)
    return path.resolve() if path.is_absolute() else (
        Path(__file__).resolve().parent / path.name
    )


def _static_path(
    node: ast.AST,
    filename: str,
    scope: ast.AST,
    context,
    seen: frozenset[str] = frozenset(),
) -> Path | None:
    parents, assignments, aliases = context
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return _canonical_test_path(filename)
        if node.id in seen:
            return None
        resolved = _resolve_name(node.id, scope, parents, assignments)
        if resolved is None:
            return None
        value, value_scope = resolved
        return _static_path(
            value, filename, value_scope, context, seen | {node.id},
        )
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        path = Path(node.value)
        return path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _static_path(node.left, filename, scope, context, seen)
        if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return None if left is None else (left / node.right.value).resolve()
        return None
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parents"
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, int)
    ):
        base = _static_path(node.value.value, filename, scope, context, seen)
        if base is None:
            return None
        try:
            return base.parents[node.slice.value]
        except IndexError:
            return None
    if isinstance(node, ast.Attribute):
        if node.attr == "parent":
            base = _static_path(node.value, filename, scope, context, seen)
            return None if base is None else base.parent
    if isinstance(node, ast.Call):
        qualified = _qualified_name(node.func, scope, parents, aliases)
        if qualified in {"str", "os.fspath", "pathlib.Path", "Path"} and len(node.args) == 1:
            return _static_path(node.args[0], filename, scope, context, seen)
        if qualified in {"os.path.join", "posixpath.join"} and node.args:
            path = _static_path(node.args[0], filename, scope, context, seen)
            if path is None:
                return None
            for component in node.args[1:]:
                if not (
                    isinstance(component, ast.Constant)
                    and isinstance(component.value, str)
                ):
                    return None
                path = path / component.value
            return path.resolve()
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"resolve", "absolute"}:
            path = _static_path(node.func.value, filename, scope, context, seen)
            return None if path is None else path.resolve()
    return None


def _terminal_basename(
    node: ast.AST,
    scope: ast.AST,
    context,
    seen: frozenset[str] = frozenset(),
) -> str | None:
    parents, assignments, aliases = context
    if isinstance(node, ast.Name):
        if node.id in seen:
            return None
        resolved = _resolve_name(node.id, scope, parents, assignments)
        if resolved is None:
            return None
        value, value_scope = resolved
        return _terminal_basename(value, value_scope, context, seen | {node.id})
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return Path(node.value).name or None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _terminal_basename(node.right, scope, context, seen)
    if isinstance(node, ast.Call):
        qualified = _qualified_name(node.func, scope, parents, aliases)
        if qualified in {"str", "os.fspath", "pathlib.Path", "Path"} and len(node.args) == 1:
            return _terminal_basename(node.args[0], scope, context, seen)
        if qualified in {"os.path.join", "posixpath.join"} and node.args:
            return _terminal_basename(node.args[-1], scope, context, seen)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"resolve", "absolute"}:
            return _terminal_basename(node.func.value, scope, context, seen)
    return None


def _path_identity(
    node: ast.AST,
    filename: str,
    scope: ast.AST,
    context,
) -> str | None:
    path = _static_path(node, filename, scope, context)
    if path is not None:
        return "self" if path == _canonical_test_path(filename) else "foreign"
    basename = _terminal_basename(node, scope, context)
    if basename is not None and basename != Path(filename).name:
        return "foreign"
    return None


def _static_text(
    node: ast.AST,
    filename: str,
    scope: ast.AST,
    context,
    seen: frozenset[str] = frozenset(),
) -> str | None:
    parents, assignments, aliases = context
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in seen:
            return None
        resolved = _resolve_name(node.id, scope, parents, assignments)
        if resolved is None:
            return None
        value, value_scope = resolved
        return _static_text(value, filename, value_scope, context, seen | {node.id})
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_text(node.left, filename, scope, context, seen)
        right = _static_text(node.right, filename, scope, context, seen)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
                continue
            if not isinstance(value, ast.FormattedValue):
                return None
            if _path_identity(value.value, filename, scope, context) != "self":
                return None
            sentinel = str(_canonical_test_path(filename))
            parts.append(repr(sentinel) if value.conversion == ord("r") else sentinel)
        return "".join(parts)
    if isinstance(node, ast.Call):
        qualified = _qualified_name(node.func, scope, parents, aliases)
        if qualified == "textwrap.dedent" and len(node.args) == 1:
            value = _static_text(node.args[0], filename, scope, context, seen)
            return None if value is None else textwrap.dedent(value)
    return None


def _module_is_self(
    node: ast.AST,
    filename: str,
    scope: ast.AST,
    context,
    seen: frozenset[str] = frozenset(),
) -> bool | None:
    parents, assignments, _aliases = context
    own_module = f"orchestrator.tests.{Path(filename).stem}"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value == own_module
    if isinstance(node, ast.Name):
        if node.id == "__name__":
            return True
        if node.id in seen:
            return None
        resolved = _resolve_name(node.id, scope, parents, assignments)
        if resolved is None:
            return None
        value, value_scope = resolved
        return _module_is_self(
            value, filename, value_scope, context, seen | {node.id},
        )
    return None


def _is_statically_unreachable(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, ast.If) and isinstance(parent.test, ast.Constant):
            active_branch = parent.body if bool(parent.test.value) else parent.orelse
            if current not in active_branch:
                return True
        if (
            isinstance(parent, ast.While)
            and isinstance(parent.test, ast.Constant)
            and not bool(parent.test.value)
            and current in parent.body
        ):
            return True
        current = parent
    return False


def _nested_imports_self(tree: ast.Module, filename: str) -> bool:
    own_stem = Path(filename).stem
    own_module = f"orchestrator.tests.{own_stem}"
    parents = _parent_map(tree)
    for node in ast.walk(tree):
        if _is_statically_unreachable(node, parents):
            continue
        if isinstance(node, ast.Import) and any(
            alias.name == own_module for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (
            node.module == own_module
            or (
                node.module == "orchestrator.tests"
                and any(alias.name == own_stem for alias in node.names)
            )
        ):
            return True
    return False


def _spec_loader_call(
    node: ast.AST,
    scope: ast.AST,
    context,
    seen: frozenset[str] = frozenset(),
) -> tuple[ast.Call, ast.AST] | None:
    parents, assignments, aliases = context
    if isinstance(node, ast.Name):
        if node.id in seen:
            return None
        resolved = _resolve_name(node.id, scope, parents, assignments)
        if resolved is None:
            return None
        value, value_scope = resolved
        return _spec_loader_call(
            value, value_scope, context, seen | {node.id},
        )
    if isinstance(node, ast.Attribute) and node.attr == "loader":
        spec = node.value
        spec_scope = scope
        if isinstance(spec, ast.Name):
            if spec.id in seen:
                return None
            resolved = _resolve_name(spec.id, scope, parents, assignments)
            if resolved is None:
                return None
            spec, spec_scope = resolved
        if (
            isinstance(spec, ast.Call)
            and _qualified_name(spec.func, spec_scope, parents, aliases)
            == "importlib.util.spec_from_file_location"
        ):
            return spec, spec_scope
    return None


def _self_load_analysis(
    tree: ast.Module,
    filename: str,
    *,
    inspect_subprocess: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    context = _static_context(tree)
    parents, assignments, aliases = context
    errors = []
    self_load = False

    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        if _is_statically_unreachable(call, parents):
            continue
        scope = _scope_for(call, parents)
        qualified = _qualified_name(call.func, scope, parents, aliases)
        path_argument = None
        path_scope = scope
        if isinstance(call.func, ast.Attribute) and call.func.attr == "exec_module":
            spec_loader = _spec_loader_call(call.func.value, scope, context)
            if spec_loader is None:
                errors.append("self-load loader is not statically resolvable")
            else:
                spec_call, path_scope = spec_loader
                if len(spec_call.args) < 2:
                    errors.append("self-load loader path is missing")
                else:
                    path_argument = spec_call.args[1]
        elif qualified == "runpy.run_path" and call.args:
            path_argument = call.args[0]
        elif qualified == "runpy.run_module" and call.args:
            module_match = _module_is_self(call.args[0], filename, scope, context)
            if module_match is None:
                errors.append("self-load module name is not statically resolvable")
            self_load = self_load or module_match is True
            continue
        elif qualified == "exec" and call.args:
            payload = call.args[0]
            if (
                isinstance(payload, ast.Call)
                and isinstance(payload.func, ast.Attribute)
                and payload.func.attr == "read"
                and isinstance(payload.func.value, ast.Call)
                and _qualified_name(payload.func.value.func, scope, parents, aliases) == "open"
                and payload.func.value.args
            ):
                path_argument = payload.func.value.args[0]

        if path_argument is not None:
            identity = _path_identity(path_argument, filename, path_scope, context)
            if identity is None:
                errors.append("self-load path is not statically resolvable")
            elif identity == "self":
                self_load = True

        if not inspect_subprocess or qualified not in {
            "subprocess.run",
            "subprocess.Popen",
            "subprocess.call",
            "subprocess.check_call",
            "subprocess.check_output",
        } or not call.args:
            continue
        argv_node = call.args[0]
        if isinstance(argv_node, ast.Name):
            resolved = _resolve_name(argv_node.id, scope, parents, assignments)
            if resolved is not None:
                argv_node, scope = resolved
        if not isinstance(argv_node, (ast.List, ast.Tuple)) or not argv_node.elts:
            continue
        executable = _qualified_name(argv_node.elts[0], scope, parents, aliases)
        if executable != "sys.executable":
            continue
        command_index = next(
            (
                index for index, value in enumerate(argv_node.elts[:-1])
                if isinstance(value, ast.Constant) and value.value == "-c"
            ),
            None,
        )
        if command_index is None:
            continue
        script_node = argv_node.elts[command_index + 1]
        rendered_script_node = script_node
        if isinstance(script_node, ast.Name):
            resolved = _resolve_name(script_node.id, scope, parents, assignments)
            if resolved is not None:
                rendered_script_node, _rendered_scope = resolved
        script = _static_text(script_node, filename, scope, context)
        if script is None:
            rendered = ast.unparse(rendered_script_node)
            if any(token in rendered for token in (
                "spec_from_file_location",
                "run_path",
                "run_module",
                f"orchestrator.tests.{Path(filename).stem}",
            )):
                errors.append("nested loader source is not statically resolvable")
            continue
        try:
            nested_tree = ast.parse(script, filename=f"{filename}:subprocess-c")
        except SyntaxError:
            errors.append("nested loader source is not statically parseable")
            continue
        if _nested_imports_self(nested_tree, filename):
            self_load = True
        nested_self, nested_errors = _self_load_analysis(
            nested_tree, filename, inspect_subprocess=False,
        )
        self_load = self_load or nested_self
        errors.extend(nested_errors)
    return self_load, tuple(errors)


class _ImportTimeHeldReferenceFinder(ast.NodeVisitor):
    def __init__(self, held_names: set[str]) -> None:
        self.held_names = held_names
        self.found = False

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and node.id in self.held_names:
            self.found = True

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and node.value in self.held_names:
            self.found = True

    def _visit_function_definition(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        arguments = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
            node.args.vararg,
            node.args.kwarg,
        )
        for argument in arguments:
            if argument is not None and argument.annotation is not None:
                self.visit(argument.annotation)
        if node.returns is not None:
            self.visit(node.returns)
        for type_parameter in getattr(node, "type_params", ()):
            self.visit(type_parameter)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_definition(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        for type_parameter in getattr(node, "type_params", ()):
            self.visit(type_parameter)
        for statement in node.body:
            self.visit(statement)


def _pre_guard_import_time_references_held_function(
    tree: ast.Module,
    call: ast.Call,
    filename: str,
) -> bool:
    held_names = {
        node_id.split("::", 1)[1]
        for node_id in GROWTH_TEST_HOLDS
        if node_id.split("::", 1)[0] == Path(filename).name
    }
    finder = _ImportTimeHeldReferenceFinder(held_names)
    for statement in tree.body:
        if statement.lineno >= call.lineno:
            break
        finder.visit(statement)
    return finder.found


def _guard_binding_analysis(
    source: str,
    filename: str,
) -> tuple[tuple[str, ...], bool]:
    tree = ast.parse(source, filename=filename)
    imports = [
        alias
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "orchestrator.tests.growth_test_holds"
        for alias in node.names
        if alias.name == "enforce_held_functions" and alias.asname is None
    ]
    all_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "enforce_held_functions"
    ]
    top_level_calls = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "enforce_held_functions"
    ]
    errors = []
    if len(imports) != 1:
        errors.append(f"import count is {len(imports)}, expected 1")
    if len(all_calls) != 1:
        errors.append(f"call count is {len(all_calls)}, expected 1")
    if len(top_level_calls) != 1:
        errors.append(f"top-level call count is {len(top_level_calls)}, expected 1")
        return tuple(errors), False

    call = top_level_calls[0]
    self_load, self_load_errors = _self_load_analysis(tree, filename)
    errors.extend(self_load_errors)
    globals_call = call.args[0] if call.args else None
    runner_keywords = [
        keyword for keyword in call.keywords if keyword.arg == "plain_runner"
    ]
    declared_runner = (
        runner_keywords[0].value.value
        if len(runner_keywords) == 1
        and isinstance(runner_keywords[0].value, ast.Constant)
        and isinstance(runner_keywords[0].value.value, str)
        else None
    )
    mode_keywords = [
        keyword for keyword in call.keywords if keyword.arg == "guard_mode"
    ]
    declared_mode = (
        mode_keywords[0].value.value
        if len(mode_keywords) == 1
        and isinstance(mode_keywords[0].value, ast.Constant)
        and isinstance(mode_keywords[0].value.value, str)
        else None
    )
    keyword_names = tuple(keyword.arg for keyword in call.keywords)
    expected_keywords = (
        ("plain_runner", "guard_mode") if self_load else ("plain_runner",)
    )
    exact_arguments = (
        len(call.args) == 2
        and keyword_names == expected_keywords
        and declared_runner in {"pytest-delegating", "manual", "none"}
        and (
            declared_mode == "call-only" if self_load else not mode_keywords
        )
        and isinstance(globals_call, ast.Call)
        and isinstance(globals_call.func, ast.Name)
        and globals_call.func.id == "globals"
        and not globals_call.args
        and not globals_call.keywords
        and isinstance(call.args[1], ast.Name)
        and call.args[1].id == "__file__"
    )
    if not exact_arguments:
        errors.append(
            "call must declare enforce_held_functions(globals(), __file__, "
            "plain_runner=<pytest-delegating|manual|none>) and add exact trailing "
            "guard_mode='call-only' only for canonical self-load"
        )

    if (
        declared_mode == "call-only"
        and _pre_guard_import_time_references_held_function(tree, call, filename)
    ):
        errors.append(
            "call-only binding must not preserve a pre-guard held-function "
            "alias/reference evaluated at import time"
        )

    test_definitions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    if test_definitions and call.lineno <= max(
        node.end_lineno or node.lineno for node in test_definitions
    ):
        errors.append("call must follow every top-level test definition")
    main_guards = [node for node in tree.body if _is_main_guard(node)]
    if main_guards and call.lineno >= min(node.lineno for node in main_guards):
        errors.append("call must precede the __main__ guard")
    expected_runner = _plain_runner_for_tree(tree)
    if declared_runner != expected_runner:
        errors.append(
            f"plain_runner {declared_runner!r} does not match AST runner "
            f"{expected_runner!r}"
        )
    return tuple(errors), self_load


def _guard_binding_errors(source: str, filename: str) -> tuple[str, ...]:
    return _guard_binding_analysis(source, filename)[0]


def _clean_subprocess_env(
    *,
    opt_in: bool = False,
    repo_on_pythonpath: bool = False,
) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("IZANAGI_RUN_GROWTH_HELD_TESTS", None)
    env["NO_COLOR"] = "1"
    if opt_in:
        env["IZANAGI_RUN_GROWTH_HELD_TESTS"] = "explicit-user-command"
    if repo_on_pythonpath:
        inherited_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(ROOT), inherited_pythonpath) if part
        )
    return env


def _run_subprocess(
    argv: list[str],
    *,
    opt_in: bool = False,
    repo_on_pythonpath: bool = False,
    timeout: float = 10.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=ROOT,
        env=_clean_subprocess_env(
            opt_in=opt_in,
            repo_on_pythonpath=repo_on_pythonpath,
        ),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def test_every_held_module_has_exact_top_level_guard_binding():
    assert _held_filenames() == (
        "test_campaign_import_invariant.py",
        "test_check_docs.py",
        "test_codex_reasoning_ab.py",
        "test_env_attestation.py",
        "test_real_repo_serialization.py",
        "test_ruleops.py",
        "test_s1_known_axes_freeze.py",
        "test_s1_measurement_freeze.py",
        "test_s8b_binding_driftguards.py",
        "test_s8b_holdout_freeze.py",
        "test_s8b_oracle_driver.py",
        "test_s8b_protocol_builder.py",
        "test_s8b_repo_scan_invariant.py",
    )
    analyses = {}
    for filename in _held_filenames():
        path = Path(__file__).resolve().parent / filename
        assert path.is_file(), filename
        errors, self_load = _guard_binding_analysis(
            path.read_text(encoding="utf-8"), filename,
        )
        analyses[filename] = (errors, self_load)
        assert errors == (), filename
        assert self_load is False, filename
    assert analyses["test_check_docs.py"] == ((), False)


def _synthetic_binding_source(
    runner: str,
    *,
    loader_path: str = "__file__",
    keywords: str = 'plain_runner="none", guard_mode="call-only"',
    alias_line: str = "",
) -> str:
    main_guard = {
        "none": "",
        "manual": "\nif __name__ == '__main__':\n    raise SystemExit(0)\n",
        "pytest-delegating": (
            "\nif __name__ == '__main__':\n"
            "    raise SystemExit(pytest.main([__file__]))\n"
        ),
    }[runner]
    pytest_import = "import pytest\n" if runner == "pytest-delegating" else ""
    return (
        "import importlib.util as importlib_util\n"
        f"{pytest_import}"
        "from orchestrator.tests.growth_test_holds import enforce_held_functions\n\n"
        "def test_real_repository_scan_matches_known_hits_and_has_positive_control():\n"
        f"    spec = importlib_util.spec_from_file_location('self', {loader_path})\n"
        "    module = importlib_util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(module)\n\n"
        f"{alias_line}"
        f"enforce_held_functions(globals(), __file__, {keywords})\n"
        f"{main_guard}"
    )


@pytest.mark.parametrize("runner", ["none", "manual", "pytest-delegating"])
def test_guard_binding_requires_call_only_exactly_for_canonical_self_load(runner):
    filename = "test_s8b_repo_scan_invariant.py"
    accepted = _synthetic_binding_source(
        runner,
        keywords=f'plain_runner="{runner}", guard_mode="call-only"',
    )
    assert _guard_binding_errors(accepted, filename) == ()

    self_load_without_mode = _synthetic_binding_source(
        runner, keywords=f'plain_runner="{runner}"',
    )
    assert _guard_binding_errors(self_load_without_mode, filename) != ()

    foreign_default = _synthetic_binding_source(
        runner,
        loader_path="'tools/check_docs.py'",
        keywords=f'plain_runner="{runner}"',
    )
    assert _guard_binding_errors(foreign_default, filename) == ()
    for mode in ("call-only", "import-and-call"):
        foreign_explicit_mode = _synthetic_binding_source(
            runner,
            loader_path="'tools/check_docs.py'",
            keywords=f'plain_runner="{runner}", guard_mode="{mode}"',
        )
        assert _guard_binding_errors(foreign_explicit_mode, filename) != ()

    rejected_keywords = (
        f'plain_runner="{runner}", guard_mode="import-and-call"',
        f'plain_runner="{runner}", guard_mode="unknown"',
        f'guard_mode="call-only", plain_runner="{runner}"',
        f'plain_runner="{runner}", unknown="call-only"',
        f'plain_runner="{runner}", guard_mode=True',
        f'plain_runner="{runner}", **{{"guard_mode": "call-only"}}',
    )
    for keywords in rejected_keywords:
        assert _guard_binding_errors(
            _synthetic_binding_source(runner, keywords=keywords), filename,
        ) != (), keywords

    third_positional = _synthetic_binding_source(
        runner,
        keywords=f'"extra", plain_runner="{runner}", guard_mode="call-only"',
    )
    assert _guard_binding_errors(third_positional, filename) != ()

    duplicate = _synthetic_binding_source(
        runner,
        keywords=(
            f'plain_runner="{runner}", plain_runner="{runner}", '
            'guard_mode="call-only"'
        ),
    )
    assert _guard_binding_errors(duplicate, filename) != ()


def test_call_only_binding_rejects_pre_guard_alias_with_post_guard_control():
    filename = "test_s8b_repo_scan_invariant.py"
    held_name = (
        "test_real_repository_scan_matches_known_hits_and_has_positive_control"
    )
    pre_guard_references = (
        f"saved = {held_name}\n",
        f"saved = globals()[{held_name!r}]\n",
        f"class Holder:\n    saved = globals()[{held_name!r}]\n",
        f"def escape(fn={held_name}):\n    return fn\n",
        f"escape = lambda fn={held_name}: fn\n",
        f"setattr(type('Holder', (), {{}}), 'held', {held_name})\n",
        f"holders = []\nholders.append(__import__('functools').partial({held_name}))\n",
        (
            "import pytest\n"
            "@pytest.fixture\n"
            f"def escaped(fn={held_name}):\n    return fn\n"
        ),
    )
    for reference in pre_guard_references:
        rejected = _synthetic_binding_source("none", alias_line=reference)
        assert "pre-guard held-function alias" in " ".join(
            _guard_binding_errors(rejected, filename)
        ), reference

    alias = f"saved = {held_name}\n"
    accepted = _synthetic_binding_source("none") + alias
    assert _guard_binding_errors(accepted, filename) == ()


def test_call_only_binding_accepts_actual_deferred_manual_runner_reference():
    filename = "test_s8b_repo_scan_invariant.py"
    path = Path(__file__).resolve().parent / filename
    source = path.read_text(encoding="utf-8")
    source = source.replace("import sys\n", "import importlib.util\nimport sys\n", 1)
    source = source.replace(
        "def _run() -> int:\n",
        "def _run() -> int:\n"
        "    spec = importlib.util.spec_from_file_location('self', __file__)\n"
        "    module = importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(module)\n",
        1,
    )
    source = source.replace(
        'enforce_held_functions(globals(), __file__, plain_runner="manual")',
        'enforce_held_functions(\n'
        '    globals(), __file__, plain_runner="manual", guard_mode="call-only",\n'
        ')',
        1,
    )
    assert _guard_binding_analysis(source, filename) == ((), True)


def test_self_load_detection_handles_real_nested_consumers():
    consumers = {
        "test_s8b_floor_campaign.py": (
            "# Shape copied from orchestrator/tests/test_s8b_floor_campaign.py:7896.\n"
            "import subprocess\n"
            "import sys\n"
            "import textwrap\n"
            "from pathlib import Path\n"
            "script = textwrap.dedent(f'''\n"
            "import importlib.util\n"
            "spec = importlib.util.spec_from_file_location(\n"
            "    'floor_test_helper', {str(Path(__file__))!r},\n"
            ")\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "''')\n"
            "subprocess.run([sys.executable, '-c', script])\n"
        ),
        "test_dev_waves_integration.py": (
            "# Shape copied from orchestrator/tests/test_dev_waves_integration.py:2050.\n"
            "import subprocess\n"
            "import sys\n"
            "script = (\n"
            "    'from orchestrator.tests import _dev_waves_serve_child as target;'\n"
            "    'raise SystemExit(target._serve_child_main())'\n"
            ")\n"
            "subprocess.Popen([sys.executable, '-c', script])\n"
        ),
    }
    expected = {
        "test_s8b_floor_campaign.py": (True, ()),
        "test_dev_waves_integration.py": (False, ()),
    }
    for filename, source in consumers.items():
        assert _self_load_analysis(ast.parse(source), filename) == expected[filename]


@pytest.mark.parametrize(
    "source",
    [
        (
            "import importlib.util\n"
            "spec: object = importlib.util.spec_from_file_location('self', __file__)\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
        ),
        (
            "import importlib.util\n"
            "spec = importlib.util.spec_from_file_location('self', __file__)\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "loader = spec.loader\n"
            "loader.exec_module(module)\n"
        ),
    ],
)
def test_self_load_detection_resolves_spec_and_loader_assignment_forms(source):
    filename = "test_s8b_repo_scan_invariant.py"
    assert _self_load_analysis(ast.parse(source), filename) == (True, ())


@pytest.mark.parametrize(
    "source",
    [
        (
            "class runpy:\n"
            "    @staticmethod\n"
            "    def run_path(path):\n"
            "        return path\n"
            "runpy.run_path(__file__)\n"
        ),
        "import runpy\nif False:\n    runpy.run_path(__file__)\n",
    ],
)
def test_self_load_detection_ignores_shadowed_or_unreachable_loader_names(source):
    filename = "test_s8b_repo_scan_invariant.py"
    assert _self_load_analysis(ast.parse(source), filename) == (False, ())


@pytest.mark.parametrize(
    ("self_source", "foreign_source"),
    [
        (
            "import runpy\nrunpy.run_path(__file__)\n",
            "import runpy\nrunpy.run_path('tools/check_docs.py')\n",
        ),
        (
            "from runpy import run_module as load\n"
            "load('orchestrator.tests.test_s8b_repo_scan_invariant')\n",
            "from runpy import run_module as load\nload('tools.check_docs')\n",
        ),
        (
            "exec(open(__file__).read())\n",
            "exec(open('tools/check_docs.py').read())\n",
        ),
    ],
)
def test_self_load_detection_pairs_each_loader_with_foreign_control(
    self_source, foreign_source,
):
    filename = "test_s8b_repo_scan_invariant.py"
    assert _self_load_analysis(ast.parse(self_source), filename) == (True, ())
    assert _self_load_analysis(ast.parse(foreign_source), filename) == (False, ())


@pytest.mark.parametrize(
    "source",
    [
        "def consumer():\n    import runpy\n    runpy.run_path(__file__)\n",
        (
            "def consumer():\n"
            "    from runpy import run_path as load\n"
            "    load(__file__)\n"
        ),
    ],
)
def test_self_load_detection_resolves_function_local_imports(source):
    filename = "test_s8b_repo_scan_invariant.py"
    assert _self_load_analysis(ast.parse(source), filename) == (True, ())


def test_self_load_detection_compares_full_path_not_only_basename():
    filename = "test_s8b_repo_scan_invariant.py"
    source = (
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location(\n"
        "    'foreign', '/tmp/test_s8b_repo_scan_invariant.py',\n"
        ")\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
    )
    assert _self_load_analysis(ast.parse(source), filename) == (False, ())


def test_self_load_detection_fails_closed_for_unresolved_loader_path():
    source = (
        "import runpy\n"
        "def load(path):\n"
        "    runpy.run_path(path)\n"
    )
    self_load, errors = _self_load_analysis(
        ast.parse(source), "test_s8b_repo_scan_invariant.py",
    )
    assert self_load is False
    assert errors == ("self-load path is not statically resolvable",)


def test_self_load_detection_fails_closed_for_unresolved_exec_module_binding():
    source = (
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location('self', __file__)\n"
        "loader = choose_loader(spec.loader)\n"
        "loader.exec_module(object())\n"
    )
    assert _self_load_analysis(
        ast.parse(source), "test_s8b_repo_scan_invariant.py",
    ) == (False, ("self-load loader is not statically resolvable",))


def test_nested_loader_resolution_has_positive_and_unrelated_negative_controls():
    filename = "test_s8b_repo_scan_invariant.py"
    unresolved_loader = (
        "import subprocess, sys\n"
        "def run(path):\n"
        "    script = f'import runpy; runpy.run_path({path!r})'\n"
        "    subprocess.run([sys.executable, '-c', script])\n"
    )
    assert _self_load_analysis(ast.parse(unresolved_loader), filename) == (
        False,
        ("nested loader source is not statically resolvable",),
    )

    unrelated_dynamic = (
        "import subprocess, sys\n"
        "def run(script):\n"
        "    subprocess.run([sys.executable, '-c', script])\n"
    )
    assert _self_load_analysis(ast.parse(unrelated_dynamic), filename) == (False, ())


def test_guard_binding_negative_control_detects_removed_call():
    filename = "test_s8b_repo_scan_invariant.py"
    path = Path(__file__).resolve().parent / filename
    valid_source = path.read_text(encoding="utf-8")
    assert _guard_binding_errors(valid_source, filename) == ()
    removed_source = valid_source.replace(
        'enforce_held_functions(globals(), __file__, plain_runner="manual")\n',
        "",
        1,
    )
    assert removed_source != valid_source
    assert _guard_binding_errors(removed_source, filename) != ()

    delegating_filename = "test_env_attestation.py"
    delegating_path = Path(__file__).resolve().parent / delegating_filename
    delegating_source = delegating_path.read_text(encoding="utf-8")
    mismatched_source = delegating_source.replace(
        'plain_runner="pytest-delegating"', 'plain_runner="manual"', 1,
    )
    assert mismatched_source != delegating_source
    assert "does not match AST runner" in " ".join(
        _guard_binding_errors(mismatched_source, delegating_filename)
    )


@pytest.mark.parametrize(
    "main_body",
    [
        "    if False:\n        pytest.main([__file__])\n    sys.exit(_run())\n",
        "    def delegate():\n        return pytest.main([__file__])\n    sys.exit(_run())\n",
        "    sys.exit(getattr(pytest, 'main')([__file__]))\n",
        "    sys.exit(pytest_entry([__file__]))\n",
    ],
)
def test_plain_runner_ast_rejects_nonterminal_or_indirect_pytest_calls(main_body):
    source = "if __name__ == '__main__':\n" + main_body
    assert _plain_runner_for_tree(ast.parse(source)) == "manual"


def test_all_registered_nodes_are_call_time_wrapped(monkeypatch):
    monkeypatch.delenv("IZANAGI_RUN_GROWTH_HELD_TESTS", raising=False)
    for node_id in GROWTH_TEST_HOLDS:
        filename, function_name = node_id.split("::", 1)
        module = importlib.import_module(f"orchestrator.tests.{filename[:-3]}")
        function = getattr(module, function_name)
        assert hasattr(function, "__wrapped__"), node_id
        with pytest.raises(GrowthTestHoldBypassRefused) as caught:
            function()
        message = str(caught.value)
        assert message.startswith("IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1 ")
        payload = json.loads(message.split(" ", 1)[1])
        assert payload == {
            "node_id": node_id,
            "release_env": "IZANAGI_RUN_GROWTH_HELD_TESTS",
            "release_token": "explicit-user-command",
        }


def test_enforcement_signature_pins_independent_guard_mode_default():
    signature = inspect.signature(enforce_held_functions)
    assert tuple(signature.parameters) == (
        "namespace",
        "module_file",
        "plain_runner",
        "guard_mode",
    )
    assert signature.parameters["guard_mode"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["guard_mode"].default == "import-and-call"
    assert GuardMode.__args__ == ("import-and-call", "call-only")
    assert _GUARD_MODES == frozenset({"import-and-call", "call-only"})


@pytest.mark.parametrize("guard_mode", ["unknown", True, None])
def test_guard_mode_rejects_unknown_literal(guard_mode):
    function_name = (
        "test_real_repository_scan_matches_known_hits_and_has_positive_control"
    )
    with pytest.raises(ValueError, match="invalid growth-test guard mode"):
        enforce_held_functions(
            {function_name: lambda: None},
            "test_s8b_repo_scan_invariant.py",
            plain_runner="manual",
            guard_mode=guard_mode,
        )


def test_pytest_driver_detection_fails_closed_without_frame_introspection(
    monkeypatch,
):
    monkeypatch.setattr(inspect, "currentframe", lambda: None)
    assert _pytest_drives_current_import() is True


def test_enforcement_rejects_misplacement_and_missing_functions():
    with pytest.raises(ValueError, match="no growth-test holds registered"):
        enforce_held_functions({}, "test_not_held.py", plain_runner="none")
    with pytest.raises(ValueError, match="held functions missing"):
        enforce_held_functions(
            {}, "test_s8b_repo_scan_invariant.py", plain_runner="manual",
        )
    function_name = "test_real_repository_scan_matches_known_hits_and_has_positive_control"
    with pytest.raises(ValueError, match="held names are not callable"):
        enforce_held_functions(
            {function_name: object()},
            "test_s8b_repo_scan_invariant.py",
            plain_runner="manual",
        )


def test_refusal_diagnostic_is_canonical_ascii_json(monkeypatch):
    monkeypatch.delenv("IZANAGI_RUN_GROWTH_HELD_TESTS", raising=False)
    wrapped = _wrap_held_function(lambda: None, "test_日.py::test_name")
    with pytest.raises(GrowthTestHoldBypassRefused) as caught:
        wrapped()
    assert str(caught.value) == (
        "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1 "
        '{"node_id":"test_\\u65e5.py::test_name",'
        '"release_env":"IZANAGI_RUN_GROWTH_HELD_TESTS",'
        '"release_token":"explicit-user-command"}'
    )


def test_exact_token_is_the_only_release_for_lightweight_body(monkeypatch):
    calls = []

    def lightweight_body(value):
        calls.append(value)
        return value + 1

    lightweight_body.pytestmark = [pytest.mark.parametrize("value", [7])]
    original_signature = inspect.signature(lightweight_body)
    function_name = "test_real_repository_scan_matches_known_hits_and_has_positive_control"
    namespace = {function_name: lightweight_body}
    monkeypatch.setenv("IZANAGI_RUN_GROWTH_HELD_TESTS", "explicit-user-command")
    assert enforce_held_functions(
        namespace,
        "test_s8b_repo_scan_invariant.py",
        plain_runner="manual",
    ) == (function_name,)
    wrapped = namespace[function_name]
    assert inspect.signature(wrapped) == original_signature
    assert wrapped.pytestmark == lightweight_body.pytestmark

    for refused_value in ("", "explicit-user-command-typo"):
        monkeypatch.setenv("IZANAGI_RUN_GROWTH_HELD_TESTS", refused_value)
        with pytest.raises(
            GrowthTestHoldBypassRefused,
            match="^IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1 ",
        ):
            wrapped(7)
    assert calls == []

    monkeypatch.setenv("IZANAGI_RUN_GROWTH_HELD_TESTS", "explicit-user-command")
    assert wrapped(7) == 8
    assert calls == [7]


def test_opt_in_runs_held_fixture_and_parametrize_shape(tmp_path):
    synthetic = tmp_path / "test_s8b_repo_scan_invariant.py"
    synthetic.write_text(
        "import pytest\n"
        "from orchestrator.tests.growth_test_holds import enforce_held_functions\n\n"
        "@pytest.fixture\n"
        "def fixture_value():\n"
        "    return 40\n\n"
        "@pytest.mark.parametrize('offset', [1, 2])\n"
        "def test_real_repository_scan_matches_known_hits_and_has_positive_control("
        "fixture_value, offset):\n"
        "    assert fixture_value + offset in (41, 42)\n\n"
        "enforce_held_functions(globals(), __file__, plain_runner='none')\n",
        encoding="utf-8",
    )
    result = _run_subprocess(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "--noconftest",
            "-p",
            "no:cacheprovider",
            "-q",
            str(synthetic),
        ],
        opt_in=True,
    )
    output = _combined_output(result)
    assert result.returncode == 0, output
    assert "2 passed" in output


def _write_call_only_module(
    tmp_path: Path,
    *,
    cost_markers: bool = False,
) -> Path:
    synthetic = tmp_path / "test_s8b_repo_scan_invariant.py"
    fixture = (
        "import pytest\n\n"
        "@pytest.fixture(autouse=True)\n"
        "def eager_fixture():\n"
        "    print('FIXTURE_RAN', flush=True)\n\n"
        if cost_markers else ""
    )
    module_tail = (
        "print('MODULE_AFTER_GUARD_RAN', flush=True)\n"
        if cost_markers else ""
    )
    synthetic.write_text(
        fixture
        + (
            "from orchestrator.tests.growth_test_holds import enforce_held_functions\n\n"
            "def test_real_repository_scan_matches_known_hits_and_has_positive_control():\n"
            "    print('BODY_RAN', flush=True)\n\n"
            "enforce_held_functions(\n"
            "    globals(), __file__, plain_runner='none', guard_mode='call-only',\n"
            ")\n"
        )
        + module_tail,
        encoding="utf-8",
    )
    return synthetic


def test_call_only_mode_allows_import_but_refuses_held_call(tmp_path):
    synthetic = _write_call_only_module(tmp_path)
    script = (
        "import importlib.util; "
        f"spec=importlib.util.spec_from_file_location('synthetic', {str(synthetic)!r}); "
        "module=importlib.util.module_from_spec(spec); "
        "spec.loader.exec_module(module); print('IMPORT_OK', flush=True); "
        "module.test_real_repository_scan_matches_known_hits_and_has_positive_control()"
    )
    result = _run_subprocess(
        [sys.executable, "-c", script],
        repo_on_pythonpath=True,
    )
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IMPORT_OK" in output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "BODY_RAN" not in output


def test_call_only_mode_allows_package_import_but_refuses_held_call(tmp_path):
    package = tmp_path / "synthetic_package"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    _write_call_only_module(package)
    script = (
        "import sys; "
        f"sys.path.insert(0, {str(tmp_path)!r}); "
        "from synthetic_package import test_s8b_repo_scan_invariant as module; "
        "print('IMPORT_OK', flush=True); "
        "module.test_real_repository_scan_matches_known_hits_and_has_positive_control()"
    )
    result = _run_subprocess(
        [sys.executable, "-c", script],
        repo_on_pythonpath=True,
    )
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IMPORT_OK" in output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "BODY_RAN" not in output


def test_call_only_mode_still_rejects_noconftest_pytest_import(tmp_path):
    synthetic = _write_call_only_module(tmp_path, cost_markers=True)
    result = _run_subprocess(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "--noconftest",
            "-p",
            "no:cacheprovider",
            "-q",
            str(synthetic),
        ],
        repo_on_pythonpath=True,
    )
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "MODULE_AFTER_GUARD_RAN" not in output
    assert "FIXTURE_RAN" not in output
    assert "BODY_RAN" not in output
    assert "passed" not in output


def test_call_only_mode_still_rejects_confcutdir_pytest_import(tmp_path):
    synthetic = _write_call_only_module(tmp_path, cost_markers=True)
    result = _run_subprocess(
        [
            sys.executable,
            "-m",
            "pytest",
            "--color=no",
            "--confcutdir",
            str(tmp_path),
            "-p",
            "no:cacheprovider",
            "-q",
            str(synthetic),
        ],
        repo_on_pythonpath=True,
    )
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "MODULE_AFTER_GUARD_RAN" not in output
    assert "FIXTURE_RAN" not in output
    assert "BODY_RAN" not in output
    assert "passed" not in output


def test_call_only_mode_still_rejects_non_delegating_main(tmp_path):
    synthetic = _write_call_only_module(tmp_path)
    result = _run_subprocess(
        [sys.executable, str(synthetic)],
        repo_on_pythonpath=True,
    )
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "BODY_RAN" not in output


def test_noconftest_bypass_is_refused_before_held_body():
    result = _run_subprocess([
        sys.executable,
        "-m",
        "pytest",
        "--color=no",
        "--noconftest",
        "-p",
        "no:cacheprovider",
        "-q",
        "orchestrator/tests/test_campaign_import_invariant.py::"
        "test_repository_scan_set_is_nonempty_and_contains_sentinels",
    ])
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "1 failed" not in output
    assert "passed" not in output


@pytest.mark.parametrize(
    "release_value",
    ["explicit-typo", "explicit-user-command-extra"],
)
def test_import_guard_rejects_nonempty_nonexact_release_token(release_value):
    env = _clean_subprocess_env()
    env["IZANAGI_RUN_GROWTH_HELD_TESTS"] = release_value
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import orchestrator.tests.test_s8b_repo_scan_invariant",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10.0,
        check=False,
    )
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "PASS " not in output
    assert "passed" not in output


def test_plain_runner_bypass_is_refused_before_held_body():
    result = _run_subprocess([
        sys.executable,
        "orchestrator/tests/test_campaign_import_invariant.py",
    ])
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output
    assert "PASS " not in output
    assert "passed" not in output


def test_imported_conftest_does_not_enable_runpy_bypass():
    result = _run_subprocess([
        sys.executable,
        "-c",
        (
            "import orchestrator.tests.conftest; import runpy; "
            "runpy.run_path("
            "'orchestrator/tests/test_s8b_repo_scan_invariant.py', "
            "run_name='__main__')"
        ),
    ])
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output


def test_direct_import_and_call_bypass_is_refused():
    result = _run_subprocess([
        sys.executable,
        "-c",
        (
            "import os; "
            "os.environ['IZANAGI_RUN_GROWTH_HELD_TESTS']='explicit-user-command'; "
            "from orchestrator.tests.test_s8b_repo_scan_invariant import "
            "test_real_repository_scan_matches_known_hits_and_has_positive_control "
            "as held; "
            "os.environ.pop('IZANAGI_RUN_GROWTH_HELD_TESTS'); held()"
        ),
    ])
    output = _combined_output(result)
    assert result.returncode != 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" in output


def test_regular_pytest_path_keeps_single_hold_skip():
    result = _run_subprocess([
        sys.executable,
        "-m",
        "pytest",
        "--color=no",
        "-p",
        "no:cacheprovider",
        "-q",
        "orchestrator/tests/test_s8b_repo_scan_invariant.py::"
        "test_real_repository_scan_matches_known_hits_and_has_positive_control",
    ])
    output = _combined_output(result)
    assert result.returncode == 0, output
    assert "1 skipped" in output
    assert "IZANAGI_GROWTH_HOLD_V1" in output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" not in output


def test_plain_pytest_delegating_runner_is_not_over_rejected():
    result = _run_subprocess([
        sys.executable,
        "orchestrator/tests/test_env_attestation.py",
    ])
    output = _combined_output(result)
    assert result.returncode == 0, output
    assert "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1" not in output
    assert "1 skipped" in output
    passed = re.search(r"(?m)(\d+) passed(?:,| in )", output)
    assert passed is not None, output
    assert int(passed.group(1)) >= 1


def _run() -> int:
    """Run fixture and parametrized nodes without a plain-runner false green."""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
