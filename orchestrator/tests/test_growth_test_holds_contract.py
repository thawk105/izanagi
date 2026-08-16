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
    RUN_GROWTH_HELD_TESTS_ENV,
    RUN_GROWTH_HELD_TESTS_TOKEN,
    GrowthTestHold,
    GrowthTestHoldBypassRefused,
    _wrap_held_function,
    _validate_hold_rows,
    enforce_held_functions,
    growth_test_hold_inventory,
    growth_test_hold_key_digest,
)
from tools import run_tests as RT


_EXPECTED_HOLD_COUNT = 59
_EXPECTED_KEY_SHA256 = "30e646a80e6dfc7c04ec2e249462789ac7cb10f1afaa6979491a3312d5d6508c"
_EXPECTED_ROW_CONTRACT_SHA256 = "374d7a990b57e5cd2100be5b74ee31fa285eac2ecb16ed2e11eb25c8bb4bf065"
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


def _guard_binding_errors(source: str, filename: str) -> tuple[str, ...]:
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
        return tuple(errors)

    call = top_level_calls[0]
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
    exact_arguments = (
        len(call.args) == 2
        and len(call.keywords) == 1
        and declared_runner in {"pytest-delegating", "manual", "none"}
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
            "plain_runner=<pytest-delegating|manual|none>)"
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
    return tuple(errors)


def _clean_subprocess_env(*, opt_in: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("IZANAGI_RUN_GROWTH_HELD_TESTS", None)
    if opt_in:
        env["IZANAGI_RUN_GROWTH_HELD_TESTS"] = "explicit-user-command"
    return env


def _run_subprocess(
    argv: list[str],
    *,
    opt_in: bool = False,
    timeout: float = 10.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=ROOT,
        env=_clean_subprocess_env(opt_in=opt_in),
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
    for filename in _held_filenames():
        path = Path(__file__).resolve().parent / filename
        assert path.is_file(), filename
        assert _guard_binding_errors(path.read_text(encoding="utf-8"), filename) == ()


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


def test_noconftest_bypass_is_refused_before_held_body():
    result = _run_subprocess([
        sys.executable,
        "-m",
        "pytest",
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
