from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.campaign.freeze_verification_hold import (
    HELD_CHECK_ID_COUNT,
    HELD_CHECK_IDS,
    HELD_CHECK_IDS_SHA256,
)
from orchestrator.tests import conftest as suite_conftest
from orchestrator.tests.growth_test_holds import GROWTH_TEST_HOLDS
from tools.hold_inventory import hold_inventory, main
from tools.pegasus.dispatch_compute import TASKS


EXPECTED_LAYER_IDS = {"production", "test"}
EXPECTED_TOP_LEVEL_KEYS = {"schema", "completeness", "layers"}
EXPECTED_TEST_RULING = "2026-08-12 rulings \u7b2c 3 \u675f"
EXPECTED_TEST_HOLD_GROUPS = (
    (
        {
            "test_campaign_import_invariant.py::test_known_exception_ledger_is_unique_rationalized_and_commented",
        },
        "tracked_files",
        (
            "Consumes the session-scoped repository_scan fixture; holding only "
            "five consumers leaves the full source scan running while removing "
            "its detection power."
        ),
    ),
    (
        {
            "test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap",
            "test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports",
            "test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command",
            "test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger",
            "test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels",
        },
        "tracked_files",
        "Parses the real operational source and documentation tree.",
    ),
    (
        {
            "test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory",
            "test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch",
            "test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure",
            "test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation",
            "test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases",
            "test_codex_reasoning_ab.py::test_m1_snapshot_head_pin_is_independent",
            "test_codex_reasoning_ab.py::test_m3_focus_artifact_directions",
            "test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing",
            "test_codex_reasoning_ab.py::test_m3_snapshot_mode_change",
            "test_codex_reasoning_ab.py::test_m3_symbolic_head_is_required",
            "test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned",
            "test_codex_reasoning_ab.py::test_pos_neg_submodule_initialization_state_mismatch_is_rejected",
            "test_codex_reasoning_ab.py::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested",
            "test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment",
        },
        "output_artifacts",
        (
            "Constructs the shared real snapshot fixture by recursively "
            "enumerating the real Codex session corpus, so cost grows with "
            "output artifacts."
        ),
    ),
    (
        {
            "test_codex_reasoning_ab.py::test_m2_production_golden_requires_both_routes",
            "test_codex_reasoning_ab.py::test_prompt_replacement_count_zero_expected_and_excess",
        },
        "output_artifacts",
        (
            "Recursively enumerates the real Codex session corpus, so cost "
            "grows with output artifacts."
        ),
    ),
    (
        {
            "test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies",
        },
        "output_artifacts",
        "Recursively reads the real Pegasus probe corpus.",
    ),
    (
        {
            "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight",
        },
        "tracked_files",
        "Scans the real checkout, so cost grows with tracked files.",
    ),
    (
        {
            "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
        },
        "commits",
        (
            "Runs the real repository binding/history gate whose cost grows "
            "with commit history."
        ),
    ),
    (
        {
            "test_s8b_holdout_freeze.py::test_verify_cli_accepts_active_t080_receipt_exact_match",
            "test_s8b_holdout_freeze.py::test_verify_direct_cli_accepts_active_t080_receipt_exact_match",
        },
        "tracked_files",
        "Searches the real repository, so cost grows with tracked files.",
    ),
    (
        {
            "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
            "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
        },
        "commits",
        (
            "Runs the real repository freeze/history gate whose cost grows "
            "with commit history."
        ),
    ),
    (
        {
            "test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control",
        },
        "tracked_files",
        "Scans the real checkout, so cost grows with tracked files.",
    ),
    (
        {
            "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper",
            "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze",
            "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points",
            "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
            "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin",
            "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper",
            "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head",
            "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
            "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
        },
        "output_artifacts",
        (
            "Builds or verifies the real known-axes freeze by globbing and "
            "parsing campaign artifacts, so cost grows with output artifacts."
        ),
    ),
    (
        {
            "test_s1_measurement_freeze.py::test_build_document_rejects_tampered_known_axes_semantics",
            "test_s1_measurement_freeze.py::test_generate_builds_registered_cells_comparisons_and_schedule",
            "test_s1_measurement_freeze.py::test_generate_refuses_existing_freeze",
            "test_s1_measurement_freeze.py::test_receipt_exists_but_measurement_verify_stays_legacy_strict",
            "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control",
            "test_s1_measurement_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
            "test_s1_measurement_freeze.py::test_schedule_is_balanced_and_reproducible",
            "test_s1_measurement_freeze.py::test_verify_rejects_known_axes_material_tamper",
            "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
            "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_workload_flag_tamper",
            "test_s1_measurement_freeze.py::test_verify_rejects_stats_implementation_tamper",
        },
        "output_artifacts",
        (
            "Consumes the module-scoped real known-axes fixture, which globs "
            "and parses campaign artifacts, so cost grows with output artifacts."
        ),
    ),
    (
        {
            "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
            "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
            "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
            "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
        },
        "commits",
        (
            "Runs real-repository receipt and active-generation history "
            "resolution over the reachable commit graph, so cost grows with "
            "commit history."
        ),
    ),
    (
        {
            "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",
            "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
        },
        "tracked_files",
        (
            "Runs full real-repository git status snapshots before and after "
            "the action, so cost grows with tracked files."
        ),
    ),
    (
        {
            "test_check_docs.py::test_real_repo_clean",
            "test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract",
            "test_check_docs.py::test_normative_exact_section_pins_accept_real_repo",
        },
        "docs_bytes",
        (
            "Runs the real tools/check_docs.py with no arguments across a variable "
            "input set: enumerated living docs, the rotating docs/archive worklog "
            "set, the handoff directory, and discovered skill, command, reference, "
            "and provenance files. Its cost therefore grows with docs bytes."
        ),
    ),
)
_SHARED_FIXTURE_COLLATERAL = (
    "Holding this node also prevents the shared module fixture from starting, "
    "so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent "
    "golden, and K.verify_document stop too."
)


def _fixture_collateral(detail: str) -> str:
    return f"{_SHARED_FIXTURE_COLLATERAL} {detail}"


def _node_collateral(detail: str) -> str:
    return f"Holding this node removes {detail}."


EXPECTED_TEST_COLLATERAL_NOTES = {
    "test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies": (
        "Holding this node also removes fixed-size checks for corpus count 48, "
        "disjoint success/failure sets, and the complete JSON-pair partition."
    ),
    "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight": (
        "Holding this node also removes fixed-size checks for the maximum "
        "package, MAX_CANDIDATES/MAX_QUERY_COUNT/MAX_SIGNAL_TOKENS, independent "
        "inspect/pickaxe evidence, and the 45/60-second preflight boundaries."
    ),
    "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper": _node_collateral(
        "its fixed self-consistency and single-field tamper rejection checks"
    ),
    "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze": _node_collateral(
        "its fixed create-only refusal check"
    ),
    "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points": _node_collateral(
        "its fixed golden checks for registered P2, backoff, and sort selections"
    ),
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags": _node_collateral(
        "its fixed S-1b mismatched-flags rejection check"
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin": _node_collateral(
        "its fixed held/released ccbench-pin positive control"
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper": _node_collateral(
        "its fixed generator-hash tamper rejection check"
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head": _node_collateral(
        "its fixed non-ancestor HEAD rejection check"
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper": _node_collateral(
        "its fixed one-byte freeze tamper rejection check"
    ),
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy": _node_collateral(
        "its fixed copied-source hash tamper rejection check"
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
    "test_check_docs.py::test_real_repo_clean": (
        "Holding this node removes its fixed-size assertions that the real "
        "checker returns rc=0, reports no violations, and has zero Pegasus "
        "admission drift findings. Land's _validate_generated_docs calls the "
        "checker with --expect-active-transaction after a non-noop fold; a noop "
        "fold returns before the check. The wave checker requires check-docs to "
        "be specified exactly once, but executes it in an isolated checkout only "
        "for a completed, passive-green run; incomplete or passive-failing runs "
        "do not execute it. A no-argument tools/check_docs.py invocation remains "
        "mandatory for class 2/3 completion; it is not required for other task "
        "classes."
    ),
    "test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract": (
        "Holding this node removes the fixed-size positive check that the "
        "current dev-wave model pins do not over-reject the real repository. Land's "
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
}


def _expected_test_holds() -> list[dict[str, object]]:
    details = {}
    for node_ids, hold_axis, reason in EXPECTED_TEST_HOLD_GROUPS:
        assert not set(details).intersection(node_ids)
        details.update(
            {node_id: (hold_axis, reason) for node_id in node_ids}
        )
    assert set(details) == set(GROWTH_TEST_HOLDS)
    return [
        {
            "node_id": node_id,
            "reason": details[node_id][1],
            "ruling": EXPECTED_TEST_RULING,
            "release_condition": "explicit-user-command-only",
            "hold_axis": details[node_id][0],
            "correctness_gate": True,
            "measured_seconds": None,
            "collateral_note": EXPECTED_TEST_COLLATERAL_NOTES.get(node_id),
        }
        for node_id in sorted(GROWTH_TEST_HOLDS)
    ]


def _expected_inventory() -> dict[str, object]:
    check_ids = sorted(HELD_CHECK_IDS)
    node_ids = sorted(GROWTH_TEST_HOLDS)
    return {
        "schema": "izanagi-hold-inventory/v1",
        "completeness": "registered-layers-only",
        "layers": [
            {
                "id": "production",
                "what": {
                    "kind": "check-id-set",
                    "check_ids": check_ids,
                    "count": HELD_CHECK_ID_COUNT,
                    "sha256": HELD_CHECK_IDS_SHA256,
                },
                "ruling": "rulings-4th-batch-2026-08-12",
                "reason": {
                    "authority": "user",
                    "decision": "freeze-verification-hold",
                    "release": (
                        "\u30e6\u30fc\u30b6\u30fc\u306e\u660e\u793a\u547d\u4ee4\u306e\u307f"
                    ),
                    "release_condition": "explicit-user-command-only",
                    "ruled_on": "2026-08-12",
                    "ruling": "rulings-4th-batch-2026-08-12",
                },
                "release": {
                    "condition": "explicit-user-command-only",
                    "mechanism": "manual-source-edit",
                    "target": (
                        "orchestrator/campaign/"
                        "freeze_verification_hold.py:HELD"
                    ),
                },
                "configured_status": "held",
                "effective_status": "held",
                "effective_status_assumption": (
                    "source flag is authoritative for registered consumers"
                ),
                "bypass_surface": [],
            },
            {
                "id": "test",
                "what": {
                    "kind": "node-id-set",
                    "node_ids": node_ids,
                    "count": len(node_ids),
                    "sha256": hashlib.sha256(
                        "\n".join(node_ids).encode("utf-8")
                    ).hexdigest(),
                    "holds": _expected_test_holds(),
                },
                "ruling": EXPECTED_TEST_RULING,
                "reason": (
                    "Repository-growth-proportional tests are held by ruling."
                ),
                "release": {
                    "condition": "explicit-user-command-only",
                    "mechanism": "environment-exact-token",
                    "target": "IZANAGI_RUN_GROWTH_HELD_TESTS",
                    "env": "IZANAGI_RUN_GROWTH_HELD_TESTS",
                    "token": "explicit-user-command",
                },
                "configured_status": "held-by-default",
                "effective_status": "held",
                "effective_status_assumption": (
                    "pytest runner loads orchestrator/tests/conftest.py"
                ),
                "bypass_surface": [
                    {
                        "id": "plain-python-runner",
                        "classification": "known-unresolved-bypass",
                        "command_pattern": "python3 test_*.py",
                        "effect": "bypasses-test-hold",
                        "reason": (
                            "pytest conftest collection hook is not invoked"
                        ),
                        "tracking": "T-930",
                    },
                    {
                        "id": "pytest-noconftest",
                        "classification": "known-unresolved-bypass",
                        "option": "--noconftest",
                        "effect": "bypasses-test-hold",
                        "reason": "pytest suite conftest is not loaded",
                        "tracking": "T-930",
                    },
                    {
                        "id": "pytest-confcutdir-below-suite",
                        "classification": "known-unresolved-bypass",
                        "option_pattern": (
                            "--confcutdir=<path-below-orchestrator/tests>"
                        ),
                        "effect": "bypasses-test-hold",
                        "reason": (
                            "pytest stops conftest discovery below suite root"
                        ),
                        "tracking": "T-930",
                    },
                    {
                        "id": "direct-test-function-call",
                        "classification": "known-unresolved-bypass",
                        "invocation": (
                            "import-test-module-and-call-function"
                        ),
                        "effect": "bypasses-test-hold",
                        "reason": (
                            "pytest collection hook is not invoked"
                        ),
                        "tracking": "T-930",
                    },
                    {
                        "id": "pegasus-dispatch-env-allowlist",
                        "classification": "release-transport",
                        "effect": "transports-test-release-opt-in",
                        "env": "IZANAGI_RUN_GROWTH_HELD_TESTS",
                        "target": (
                            "tools/pegasus/dispatch_compute.py:"
                            "tests.env_allowlist"
                        ),
                    },
                    {
                        "id": "pegasus-pytest-addopts-transport",
                        "classification": "bypass-transport",
                        "effect": (
                            "transports-conftest-suppression-options"
                        ),
                        "env": "PYTEST_ADDOPTS",
                        "options": ["--noconftest", "--confcutdir"],
                        "target": (
                            "tools/pegasus/dispatch_compute.py:"
                            "tests.env_allowlist"
                        ),
                    },
                ],
            },
        ],
    }


def _layers_by_id(inventory: dict[str, object]) -> dict[str, dict[str, object]]:
    layers = inventory["layers"]
    assert isinstance(layers, list)
    by_id = {layer["id"]: layer for layer in layers}
    assert set(by_id) == EXPECTED_LAYER_IDS
    assert len(layers) == len(EXPECTED_LAYER_IDS)
    return by_id


def test_inventory_projects_exact_registered_source_sets(monkeypatch):
    monkeypatch.delenv("IZANAGI_RUN_GROWTH_HELD_TESTS", raising=False)
    inventory = hold_inventory()
    assert inventory == _expected_inventory()
    layers = _layers_by_id(inventory)
    expected_layer_fields = {
        "id",
        "what",
        "ruling",
        "reason",
        "release",
        "configured_status",
        "effective_status",
        "effective_status_assumption",
        "bypass_surface",
    }
    assert set(inventory) == EXPECTED_TOP_LEVEL_KEYS
    assert all(set(layer) == expected_layer_fields for layer in layers.values())

    production_what = layers["production"]["what"]
    assert set(production_what["check_ids"]) == set(HELD_CHECK_IDS)
    assert production_what["count"] == HELD_CHECK_ID_COUNT
    assert production_what["count"] == len(production_what["check_ids"])
    assert production_what["sha256"] == HELD_CHECK_IDS_SHA256
    assert production_what["sha256"] == hashlib.sha256(
        "\n".join(sorted(production_what["check_ids"])).encode("utf-8")
    ).hexdigest()

    test_what = layers["test"]["what"]
    assert set(test_what["node_ids"]) == set(GROWTH_TEST_HOLDS)
    assert test_what["count"] == len(GROWTH_TEST_HOLDS)
    assert {row["node_id"] for row in test_what["holds"]} == set(
        GROWTH_TEST_HOLDS
    )

    assert inventory["schema"] == "izanagi-hold-inventory/v1"
    assert inventory["completeness"] == "registered-layers-only"
    assert layers["production"]["effective_status_assumption"] == (
        "source flag is authoritative for registered consumers"
    )
    assert layers["test"]["effective_status_assumption"] == (
        "pytest runner loads orchestrator/tests/conftest.py"
    )
    production_release = layers["production"]["release"]
    assert production_release == {
        "condition": "explicit-user-command-only",
        "mechanism": "manual-source-edit",
        "target": "orchestrator/campaign/freeze_verification_hold.py:HELD",
    }
    test_release = layers["test"]["release"]
    assert test_release == {
        "condition": "explicit-user-command-only",
        "mechanism": "environment-exact-token",
        "target": "IZANAGI_RUN_GROWTH_HELD_TESTS",
        "env": "IZANAGI_RUN_GROWTH_HELD_TESTS",
        "token": "explicit-user-command",
    }
    assert test_release["target"] == test_release["env"]
    bypass_by_id = {
        surface["id"]: surface for surface in layers["test"]["bypass_surface"]
    }
    assert set(bypass_by_id) == {
        "plain-python-runner",
        "pytest-noconftest",
        "pytest-confcutdir-below-suite",
        "direct-test-function-call",
        "pegasus-dispatch-env-allowlist",
        "pegasus-pytest-addopts-transport",
    }
    assert bypass_by_id["plain-python-runner"] == {
        "id": "plain-python-runner",
        "classification": "known-unresolved-bypass",
        "command_pattern": "python3 test_*.py",
        "effect": "bypasses-test-hold",
        "reason": "pytest conftest collection hook is not invoked",
        "tracking": "T-930",
    }
    assert bypass_by_id["pytest-noconftest"] == {
        "id": "pytest-noconftest",
        "classification": "known-unresolved-bypass",
        "option": "--noconftest",
        "effect": "bypasses-test-hold",
        "reason": "pytest suite conftest is not loaded",
        "tracking": "T-930",
    }
    assert bypass_by_id["pytest-confcutdir-below-suite"] == {
        "id": "pytest-confcutdir-below-suite",
        "classification": "known-unresolved-bypass",
        "option_pattern": "--confcutdir=<path-below-orchestrator/tests>",
        "effect": "bypasses-test-hold",
        "reason": "pytest stops conftest discovery below suite root",
        "tracking": "T-930",
    }
    assert bypass_by_id["direct-test-function-call"] == {
        "id": "direct-test-function-call",
        "classification": "known-unresolved-bypass",
        "invocation": "import-test-module-and-call-function",
        "effect": "bypasses-test-hold",
        "reason": "pytest collection hook is not invoked",
        "tracking": "T-930",
    }
    assert bypass_by_id["pegasus-dispatch-env-allowlist"] == {
        "id": "pegasus-dispatch-env-allowlist",
        "classification": "release-transport",
        "effect": "transports-test-release-opt-in",
        "env": "IZANAGI_RUN_GROWTH_HELD_TESTS",
        "target": "tools/pegasus/dispatch_compute.py:tests.env_allowlist",
    }
    assert bypass_by_id["pegasus-pytest-addopts-transport"] == {
        "id": "pegasus-pytest-addopts-transport",
        "classification": "bypass-transport",
        "effect": "transports-conftest-suppression-options",
        "env": "PYTEST_ADDOPTS",
        "options": ["--noconftest", "--confcutdir"],
        "target": "tools/pegasus/dispatch_compute.py:tests.env_allowlist",
    }
    assert bypass_by_id["pegasus-dispatch-env-allowlist"]["env"] == (
        test_release["env"]
    )
    assert "IZANAGI_RUN_GROWTH_HELD_TESTS" in TASKS["tests"].env_allowlist
    assert "PYTEST_ADDOPTS" in TASKS["tests"].env_allowlist


def _expected_human(inventory: dict[str, object]) -> str:
    canonical_layers = _layers_by_id(_expected_inventory())
    lines = [
        "現行 2 層の snapshot であり, 未知の保留層の自動発見は保証しない",
        "schema: izanagi-hold-inventory/v1",
        "completeness: registered-layers-only",
    ]
    for layer_id in ("production", "test"):
        layer = _layers_by_id(inventory)[layer_id]
        canonical = canonical_layers[layer_id]
        lines.extend((
            "",
            f"layer: {layer_id}",
            f"configured_status: {canonical['configured_status']}",
            f"effective_status: {canonical['effective_status']}",
            (
                "effective_status_assumption: "
                f"{canonical['effective_status_assumption']}"
            ),
            f"ruling: {canonical['ruling']}",
            "reason: " + json.dumps(
                canonical["reason"], ensure_ascii=False, sort_keys=True,
            ),
            "release: " + json.dumps(
                layer["release"], ensure_ascii=False, sort_keys=True,
            ),
            "bypass_surface: " + json.dumps(
                layer["bypass_surface"], ensure_ascii=False, sort_keys=True,
            ),
        ))
        what = canonical["what"]
        if layer_id == "production":
            lines.extend(f"check_id: {value}" for value in what["check_ids"])
            continue
        lines.append("observed_seconds_note: observation only; not hold rationale")
        for hold in what["holds"]:
            lines.append(
                "node_id: {node_id} | reason: {reason} | ruling: {ruling} | "
                "release_condition: {release_condition} | "
                "hold_axis: {hold_axis} | "
                "correctness_gate: {correctness_gate} | "
                "observed_seconds: {measured_seconds} | "
                "collateral_note: {collateral_note}".format(**hold)
            )
    return "\n".join(lines) + "\n"


def test_main_dispatches_human_and_json(monkeypatch, capsys):
    monkeypatch.delenv("IZANAGI_RUN_GROWTH_HELD_TESTS", raising=False)
    expected = hold_inventory()

    assert main(["--format", "human"]) == 0
    human = capsys.readouterr().out
    assert human == _expected_human(expected)

    assert main(["--format", "json"]) == 0
    json_output = capsys.readouterr().out
    assert json.loads(json_output) == expected
    assert set(json.loads(json_output)) == EXPECTED_TOP_LEVEL_KEYS


def test_effective_status_tracks_exact_test_opt_in(monkeypatch):
    monkeypatch.delenv("IZANAGI_RUN_GROWTH_HELD_TESTS", raising=False)
    layers = _layers_by_id(hold_inventory())
    assert layers["production"]["effective_status"] == "held"
    assert layers["test"]["configured_status"] == "held-by-default"
    assert layers["test"]["effective_status"] == "held"

    monkeypatch.setenv(
        "IZANAGI_RUN_GROWTH_HELD_TESTS", "explicit-user-command",
    )
    layers = _layers_by_id(hold_inventory())
    assert layers["test"]["effective_status"] == (
        "released-by-explicit-user-command"
    )

    monkeypatch.setenv("IZANAGI_RUN_GROWTH_HELD_TESTS", "yes")
    layers = _layers_by_id(hold_inventory())
    assert layers["test"]["effective_status"] == "invalid-opt-in-rejected"


def test_effective_status_matches_suite_conftest_decision(monkeypatch):
    monkeypatch.delenv("IZANAGI_RUN_GROWTH_HELD_TESTS", raising=False)
    assert suite_conftest._growth_holds_opted_in() is False
    assert _layers_by_id(hold_inventory())["test"]["effective_status"] == "held"

    monkeypatch.setenv("IZANAGI_RUN_GROWTH_HELD_TESTS", "")
    assert suite_conftest._growth_holds_opted_in() is False
    assert _layers_by_id(hold_inventory())["test"]["effective_status"] == "held"

    monkeypatch.setenv(
        "IZANAGI_RUN_GROWTH_HELD_TESTS", "explicit-user-command",
    )
    assert suite_conftest._growth_holds_opted_in() is True
    assert _layers_by_id(hold_inventory())["test"]["effective_status"] == (
        "released-by-explicit-user-command"
    )

    monkeypatch.setenv("IZANAGI_RUN_GROWTH_HELD_TESTS", "other-nonempty-value")
    with pytest.raises(pytest.UsageError):
        suite_conftest._growth_holds_opted_in()
    assert _layers_by_id(hold_inventory())["test"]["effective_status"] == (
        "invalid-opt-in-rejected"
    )


def test_script_and_module_entrypoints_match_without_pythonpath():
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    script = subprocess.run(
        [sys.executable, "tools/hold_inventory.py", "--format", "json"],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    module = subprocess.run(
        [sys.executable, "-m", "tools.hold_inventory", "--format", "json"],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert (script.returncode, script.stderr) == (0, "")
    assert (module.returncode, module.stderr) == (0, "")
    assert script.stdout == module.stdout
    assert json.loads(script.stdout) == hold_inventory()


def test_output_does_not_claim_unknown_layer_completeness(monkeypatch, capsys):
    monkeypatch.delenv("IZANAGI_RUN_GROWTH_HELD_TESTS", raising=False)
    assert main(["--format", "human"]) == 0
    human = capsys.readouterr().out
    assert "registered-layers-only" in human

    assert main(["--format", "json"]) == 0
    json_output = capsys.readouterr().out
    combined = (human + json_output).lower()
    for forbidden_claim in (
        "all hold layers",
        "automatic discovery of unknown hold layers is guaranteed",
        "complete hold inventory",
        "completeness-guaranteed",
        "\u5b8c\u5168\u6027\u3092\u4fdd\u8a3c",
        "\u5168\u4fdd\u7559\u5c64",
    ):
        assert forbidden_claim not in combined
    assert json.loads(json_output)["completeness"] == "registered-layers-only"


def _run() -> int:
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
