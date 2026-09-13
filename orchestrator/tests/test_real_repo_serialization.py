# -*- coding: utf-8 -*-
"""テストスイート自身の conftest 契約の監査。

- 実 repo / 共有 submodule の xdist group 収集監査と scheduler control
- 一時ディレクトリの置き場ガード (実効 TMPDIR が tmpfs へ戻る退行の検出)
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import inspect
import json
import os
import pickle
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from collections import Counter
from importlib import metadata
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from packaging.version import InvalidVersion, Version
import pytest

HERE = Path(__file__).resolve().parent
ORCHESTRATOR = HERE.parent
ROOT = ORCHESTRATOR.parent

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ORCHESTRATOR.parent))
from skiputil import Skip, skip  # noqa: E402
from orchestrator.tests.growth_test_holds import enforce_held_functions  # noqa: E402
from orchestrator.tests.output_snapshot_ignores import (  # noqa: E402
    git_ignored_output_ancestor_directories,
    git_ignored_output_prefixes,
    git_ignored_output_snapshot_rules,
    is_git_ignored_output_path,
)


# conftest の付与正本から意図的に重複させる独立 oracle。ここを conftest から
# import / 導出すると、正本の node 増減が付与側と期待側へ同時伝播して恒真化する。
_REAL_REPO_CLASSIFIED_NODES_GOLDEN = frozenset({
    "test_s1_known_axes_freeze.py::test_historical_real_artifact_without_live_code_reads",
    "test_s1_known_axes_freeze.py::test_historical_option_keeps_new_document_strict",
    "test_s1_known_axes_freeze.py::test_historical_real_artifact_is_readable",
    "test_s1_known_axes_freeze.py::test_historical_view_does_not_consult_current_semantics_or_head",
    "test_s1_known_axes_freeze.py::test_historical_cli_selects_view",
    "test_s1_known_axes_freeze.py::test_historical_path_identity_uses_original_bytes",
    "test_s1_known_axes_freeze.py::test_historical_input_copy_sha_and_existence_remain_bound",
    "test_s1_known_axes_freeze.py::test_historical_current_use_matches_real_reconstruction",
    "test_s1_known_axes_freeze.py::test_historical_current_use_rejects_single_flags_difference",
    "test_s1_known_axes_freeze.py::test_historical_current_use_preserves_source_key_comparison",
    "test_s1_known_axes_freeze.py::test_historical_measurement_and_calibration_keep_current_semantics",
    "test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics",
    "test_verifier.py::test_current_pin_proof_surfaces_accept_silo_and_reject_mocc_same_trace",
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
    # T1259 probe の module fixture が親 working tree の snapshot を読む reader。
    "test_t1259_qsub_env_delivery_probe.py::test_r1_binds_all_three_explicit_values_and_skips_real_driver",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal",
    "test_t1259_qsub_env_delivery_probe.py::test_r3_records_only_the_observed_ambient_approval_condition",
    "test_t1259_qsub_env_delivery_probe.py::test_r1_projection_follows_observed_approval_not_request_identity",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_unexpected_approval_presence_is_unbound_and_not_green",
    "test_t1259_qsub_env_delivery_probe.py::test_missing_r1_explicit_value_cannot_be_green",
    "test_t1259_qsub_env_delivery_probe.py::test_swapped_r2_hex_values_fail_exact_binding",
    "test_t1259_qsub_env_delivery_probe.py::test_repository_local_evidence_directory_is_rejected",
    "test_t1259_qsub_env_delivery_probe.py::test_submission_source_digests_are_bound_to_runtime_bytes",
    "test_t1259_qsub_env_delivery_probe.py::test_r1_manifest_rejects_approval_that_does_not_equal_nonce",
    "test_t1259_qsub_env_delivery_probe.py::test_r3_manifest_rejects_nonliteral_ambient_approval",
    "test_t1259_qsub_env_delivery_probe.py::test_job_start_requires_manifest_head_detached_and_clean_repository",
    "test_t1259_qsub_env_delivery_probe.py::test_repo_unchanged_claim_compares_target_content_digests",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_timeout_is_not_accepted_as_refusal",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_refusal_rejects_any_driver_argv_mutation",
    "test_t1259_qsub_env_delivery_probe.py::test_atomic_result_publish_is_create_only",
    "test_t1259_qsub_env_delivery_probe.py::test_main_emits_one_prefixed_stdout_line_and_auxiliary_result",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_contract_runs_observer_through_single_result_call_block",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_early_ulimit_failure_emits_one_prefixed_result",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_preserves_one_valid_negative_observer_result",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_replaces_invalid_observer_stdout_with_one_fallback",
    "test_t1259_qsub_env_delivery_probe.py::test_submitter_text_is_outside_execution_inventory",
    "test_t1259_qsub_env_delivery_probe.py::test_submitter_has_exact_three_request_design_and_create_only_witnesses",
    "test_t1259_qsub_env_delivery_probe.py::test_submitter_preflight_parses_gen_s_semantic_state",
    "test_t1259_qsub_env_delivery_probe.py::test_request_receipt_binds_qstat_body_visibility",
    "test_t1259_qsub_env_delivery_probe.py::test_request_receipt_accepts_measured_qstat_layout",
    "test_t1259_qsub_env_delivery_probe.py::test_request_receipt_rejects_wrong_owner_or_non_active_state",
    "test_t1259_qsub_env_delivery_probe.py::test_group_intent_is_create_only_and_has_no_completion_fields",
    # snapshot テストの結線監査 meta-テスト (本ファイル)。実 ROOT で builder を実走し
    # repo tree snapshot を取るため writer の patch 窓と同じ競合面 (D63 列挙漏れの補完)。
    "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",
    # T-080 の子 collection が実履歴、output、共有 submodule を読む reader。
    "test_real_repo_serialization.py::test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default",
    # foreign module の import-time temp 境界と実 output の不変を検査する reader。
    "test_real_repo_serialization.py::test_t080_import_temp_environment_fails_closed_for_foreign_module",
    "test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes",
    "test_real_repo_serialization.py::test_shard_assignment_preserves_live_xdist_group_components_and_split_control",
    "test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order",
    "test_t810_coordinator.py::test_prepare_group_rejects_forged_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_accepts_external_root_with_anchor_union",
    "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",
    "test_campaign.py::test_source_digest_parse_options_defaults",
    "test_campaign.py::test_source_digest_stock_roundtrip",
    "test_campaign.py::test_source_digest_fixed_variant_distinct",
    "test_campaign.py::test_source_digest_failsclosed_on_missing_define",
    "test_campaign.py::test_source_digest_semantic_comment_vs_behavior",
    "test_campaign.py::test_evolve_block_markers_structure_and_inert",
    "test_hooks.py::test_real_submodule_payload_edit",
    "test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control",
    # caller inventory が実 working tree の Python と設計・前提条件正本を列挙・読取する reader。
    "test_calibration_freeze_stage6_candidate_gate.py::test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs",
    "test_s1_9pair_figure_provenance.py::test_p1_independent_real_wal_projection_matches_frozen_report",
    "test_s1_9pair_figure_provenance.py::test_p2_certified_acceptance_rejects_historical_e0_campaign",
    "test_s1_9pair_figure_provenance.py::test_p3_real_provenance_closes_bytes_admission_caption_and_freeze_chain",
    "test_s1_9pair_figure_provenance.py::test_p4_frozen_manifest_remains_23_and_excludes_new_figure",
    "test_s1_9pair_figure_provenance.py::test_p5_test_module_does_not_import_generator_for_expected_values",
    "test_s1_9pair_figure_provenance.py::test_p6_production_ignores_unknown_build_fields_as_data",
    "test_s1_9pair_figure_provenance.py::test_p7_production_load_campaign_pins_admission_calls_and_receipts",
    "test_s1_9pair_figure_provenance.py::test_p8_production_caption_matches_independent_parent_text",
    "test_s1_9pair_figure_provenance.py::test_n3_production_strict_floor_rejects_exact_boundary",
    "test_s1_9pair_figure_provenance.py::test_n4_production_collection_retains_unstable_eighth_sample",
    "test_s1_9pair_figure_provenance.py::test_n9_rejects_any_failed_hard_gate",
    "test_s1_9pair_figure_provenance.py::test_n10_production_stops_judgment_gate_disagreement_and_marker_uses_report",
    "test_s1_9pair_figure_provenance.py::test_n11_spy_pins_artist_values_and_bbox_before_save",
    "test_s1_9pair_figure_provenance.py::test_n12_collects_all_artist_and_legend_text",
    "test_s1_9pair_figure_provenance.py::test_n13_bbox_checker_rejects_overlapping_non_tick_text",
    "test_s1_9pair_figure_provenance.py::test_n14_bbox_checker_pins_ticks_marker_reference_clearance_and_agg",
    "test_s1_9pair_figure_provenance.py::test_n16_bbox_checker_rejects_legacy_bottom_legend_overlap",
    "test_s1_9pair_figure_provenance.py::test_n17_bbox_checker_rejects_missing_bottom_legend",
    "test_s1_9pair_figure_provenance.py::test_n18_bbox_checker_rejects_bottom_legend_excluded_from_tight_bbox",
    "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points",
    "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze",
    "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head",
    "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin",
    # measurement freeze の fixture 消費 node ([T-066] echo 除去後は実材料 reader)。
    "test_s1_measurement_freeze.py::test_generate_builds_registered_cells_comparisons_and_schedule",
    "test_s1_measurement_freeze.py::test_generate_refuses_existing_freeze",
    "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
    "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_workload_flag_tamper",
    "test_s1_measurement_freeze.py::test_verify_rejects_stats_implementation_tamper",
    "test_s1_measurement_freeze.py::test_verify_rejects_known_axes_material_tamper",
    "test_s1_measurement_freeze.py::test_schedule_is_balanced_and_reproducible",
    "test_s1_measurement_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s1_measurement_freeze.py::test_receipt_exists_but_measurement_verify_stays_legacy_strict",
    "test_s1_measurement_freeze.py::test_build_document_rejects_tampered_known_axes_semantics",
    "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control",
    # prepare_cell が実共有 submodule の linked-worktree 管理領域を更新する writer。
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration",
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration",
    "test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2",
    "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
    # module fixture が実 repo / 実 submodule を clone source として読む reader。
    "test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned",
    "test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases",
    "test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure",
    "test_codex_reasoning_ab.py::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested",
    "test_codex_reasoning_ab.py::test_m1_snapshot_head_pin_is_independent",
    "test_codex_reasoning_ab.py::test_m3_snapshot_mode_change",
    "test_codex_reasoning_ab.py::test_m3_symbolic_head_is_required",
    "test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing",
    "test_codex_reasoning_ab.py::test_m3_focus_artifact_directions",
    "test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive",
    "test_codex_reasoning_ab.py::test_pos_neg_submodule_initialization_state_mismatch_is_rejected",
    "test_codex_reasoning_ab.py::test_git_answer_object_reinjection_is_rejected",
    "test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment",
    "test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory",
    "test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment",
    "test_codex_reasoning_ab.py::test_material_replay_rejects_task_manifest_exchange_at_digest_consumers",
    "test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication",
    "test_codex_reasoning_ab.py::test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run",
    "test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch",
    "test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation",
    "test_codex_reasoning_ab.py::test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid",
    # helper が実親 repo と実共有 submodule を clone source として直接読む reader。
    "test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e",
    "test_s8b_floor_campaign.py::test_public_official_preflight_accepts_versioned_protocol",
    "test_s8b_floor_campaign.py::test_public_official_preflight_accepts_legacy_protocol",
    "test_s8b_floor_campaign.py::test_public_official_preflight_rejects_resolved_protocol_byte_drift",
    "test_s8b_floor_campaign.py::test_public_official_preflight_rejects_legacy_byte_drift_after_capture",
    "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification",
    "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
    "test_s8b_oracle_driver.py::test_v2_standalone_gate_check_requires_full_floor_validation",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
    "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight",
})

_REAL_REPO_PARENT_ONLY_NODES_GOLDEN = frozenset({
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
    "test_t1259_qsub_env_delivery_probe.py::test_r1_binds_all_three_explicit_values_and_skips_real_driver",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_binds_explicit_value_over_distinct_ambient_duplicate_and_runs_refusal",
    "test_t1259_qsub_env_delivery_probe.py::test_r3_records_only_the_observed_ambient_approval_condition",
    "test_t1259_qsub_env_delivery_probe.py::test_r1_projection_follows_observed_approval_not_request_identity",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_unexpected_approval_presence_is_unbound_and_not_green",
    "test_t1259_qsub_env_delivery_probe.py::test_missing_r1_explicit_value_cannot_be_green",
    "test_t1259_qsub_env_delivery_probe.py::test_swapped_r2_hex_values_fail_exact_binding",
    "test_t1259_qsub_env_delivery_probe.py::test_repository_local_evidence_directory_is_rejected",
    "test_t1259_qsub_env_delivery_probe.py::test_submission_source_digests_are_bound_to_runtime_bytes",
    "test_t1259_qsub_env_delivery_probe.py::test_r1_manifest_rejects_approval_that_does_not_equal_nonce",
    "test_t1259_qsub_env_delivery_probe.py::test_r3_manifest_rejects_nonliteral_ambient_approval",
    "test_t1259_qsub_env_delivery_probe.py::test_job_start_requires_manifest_head_detached_and_clean_repository",
    "test_t1259_qsub_env_delivery_probe.py::test_repo_unchanged_claim_compares_target_content_digests",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_timeout_is_not_accepted_as_refusal",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_driver_argv_with_extra_tail_is_rejected_by_exact_contract",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_driver_argv_with_approval_flag_is_rejected_after_exact_match",
    "test_t1259_qsub_env_delivery_probe.py::test_r2_refusal_rejects_any_driver_argv_mutation",
    "test_t1259_qsub_env_delivery_probe.py::test_atomic_result_publish_is_create_only",
    "test_t1259_qsub_env_delivery_probe.py::test_main_emits_one_prefixed_stdout_line_and_auxiliary_result",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_contract_runs_observer_through_single_result_call_block",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_early_ulimit_failure_emits_one_prefixed_result",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_preserves_one_valid_negative_observer_result",
    "test_t1259_qsub_env_delivery_probe.py::test_pbs_replaces_invalid_observer_stdout_with_one_fallback",
    "test_t1259_qsub_env_delivery_probe.py::test_submitter_text_is_outside_execution_inventory",
    "test_t1259_qsub_env_delivery_probe.py::test_submitter_has_exact_three_request_design_and_create_only_witnesses",
    "test_t1259_qsub_env_delivery_probe.py::test_submitter_preflight_parses_gen_s_semantic_state",
    "test_t1259_qsub_env_delivery_probe.py::test_request_receipt_binds_qstat_body_visibility",
    "test_t1259_qsub_env_delivery_probe.py::test_request_receipt_accepts_measured_qstat_layout",
    "test_t1259_qsub_env_delivery_probe.py::test_request_receipt_rejects_wrong_owner_or_non_active_state",
    "test_t1259_qsub_env_delivery_probe.py::test_group_intent_is_create_only_and_has_no_completion_fields",
    "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",
    "test_real_repo_serialization.py::test_t080_import_temp_environment_fails_closed_for_foreign_module",
    "test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes",
    "test_real_repo_serialization.py::test_shard_assignment_preserves_live_xdist_group_components_and_split_control",
    "test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order",
    "test_t810_coordinator.py::test_prepare_group_rejects_forged_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_accepts_external_root_with_anchor_union",
    "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",
    "test_calibration_freeze_stage6_candidate_gate.py::test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs",
    "test_s1_9pair_figure_provenance.py::test_p1_independent_real_wal_projection_matches_frozen_report",
    "test_s1_9pair_figure_provenance.py::test_p2_certified_acceptance_rejects_historical_e0_campaign",
    "test_s1_9pair_figure_provenance.py::test_p3_real_provenance_closes_bytes_admission_caption_and_freeze_chain",
    "test_s1_9pair_figure_provenance.py::test_p4_frozen_manifest_remains_23_and_excludes_new_figure",
    "test_s1_9pair_figure_provenance.py::test_p5_test_module_does_not_import_generator_for_expected_values",
    "test_s1_9pair_figure_provenance.py::test_p6_production_ignores_unknown_build_fields_as_data",
    "test_s1_9pair_figure_provenance.py::test_p7_production_load_campaign_pins_admission_calls_and_receipts",
    "test_s1_9pair_figure_provenance.py::test_p8_production_caption_matches_independent_parent_text",
    "test_s1_9pair_figure_provenance.py::test_n3_production_strict_floor_rejects_exact_boundary",
    "test_s1_9pair_figure_provenance.py::test_n4_production_collection_retains_unstable_eighth_sample",
    "test_s1_9pair_figure_provenance.py::test_n9_rejects_any_failed_hard_gate",
    "test_s1_9pair_figure_provenance.py::test_n10_production_stops_judgment_gate_disagreement_and_marker_uses_report",
    "test_s1_9pair_figure_provenance.py::test_n11_spy_pins_artist_values_and_bbox_before_save",
    "test_s1_9pair_figure_provenance.py::test_n12_collects_all_artist_and_legend_text",
    "test_s1_9pair_figure_provenance.py::test_n13_bbox_checker_rejects_overlapping_non_tick_text",
    "test_s1_9pair_figure_provenance.py::test_n14_bbox_checker_pins_ticks_marker_reference_clearance_and_agg",
    "test_s1_9pair_figure_provenance.py::test_n16_bbox_checker_rejects_legacy_bottom_legend_overlap",
    "test_s1_9pair_figure_provenance.py::test_n17_bbox_checker_rejects_missing_bottom_legend",
    "test_s1_9pair_figure_provenance.py::test_n18_bbox_checker_rejects_bottom_legend_excluded_from_tight_bbox",
    "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight",
})
_REAL_REPO_CCBENCH_ONLY_NODES_GOLDEN = frozenset({
    "test_verifier.py::test_current_pin_proof_surfaces_accept_silo_and_reject_mocc_same_trace",
    "test_campaign.py::test_source_digest_parse_options_defaults",
    "test_campaign.py::test_source_digest_stock_roundtrip",
    "test_campaign.py::test_source_digest_fixed_variant_distinct",
    "test_campaign.py::test_source_digest_failsclosed_on_missing_define",
    "test_campaign.py::test_source_digest_semantic_comment_vs_behavior",
    "test_hooks.py::test_real_submodule_payload_edit",
    "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
})
_REAL_REPO_LOCAL_ONLY_NODES_GOLDEN = frozenset({
    "test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification",
    "test_s8b_oracle_driver.py::test_v2_standalone_gate_check_requires_full_floor_validation",
})
_REAL_REPO_CCBENCH_WRITER_NODES_GOLDEN = frozenset({
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration",
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration",
    "test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2",
    "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
})
_REAL_REPO_PROCESS_MEMO_NODES_GOLDEN = frozenset({
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
})


def _real_repo_access_golden() -> dict[str, tuple[str | None, str | None]]:
    result = {}
    for node_id in _REAL_REPO_CLASSIFIED_NODES_GOLDEN:
        if node_id in _REAL_REPO_LOCAL_ONLY_NODES_GOLDEN:
            continue
        parent = (
            None
            if node_id in _REAL_REPO_CCBENCH_ONLY_NODES_GOLDEN
            else "read"
        )
        ccbench = (
            None
            if node_id in _REAL_REPO_PARENT_ONLY_NODES_GOLDEN
            else (
                "write"
                if node_id in _REAL_REPO_CCBENCH_WRITER_NODES_GOLDEN
                else "read"
            )
        )
        result[node_id] = (parent, ccbench)
    return result

# suite で許す xdist group 名の独立 oracle。conftest や marker 定数から導出しない。
_XDIST_GROUP_NAMES_GOLDEN = frozenset({
    "campaign-repository-scan",
    "dev-waves-runtime",
    "p3-b4-material-report",
    "real-repo",
    "s8c-predicate-snapshot",
    "s8c-preregistration-candidate",
})

_S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN = frozenset({
    "test_s8c_preregistration_predicates.py::test_current_repository_c04_rejects_missing_started_trial_preflight",
    "test_s8c_preregistration_predicates.py::test_current_repository_snapshot_has_zero_satisfied_predicates",
    "test_s8c_preregistration_predicates.py::test_current_repository_snapshot_exactly_matches_head",
    "test_s8c_preregistration_predicates.py::test_current_repository_gap_reason_snapshot_requires_cross_wave_review",
})

_S8C_PREREGISTRATION_CANDIDATE_NODES_GOLDEN = frozenset({
    "test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain",
    "test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points",
    "test_s8c_preregistration_invariant.py::test_repository_tip_binds_current_decider_version_without_activation",
    "test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates",
    "test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan",
})

_CAMPAIGN_REPOSITORY_SCAN_NODES_GOLDEN = frozenset({
    "test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels",
    "test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger",
    "test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap",
    "test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command",
    "test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports",
    "test_campaign_import_invariant.py::test_known_exception_ledger_is_unique_rationalized_and_commented",
})

_P3_B4_MATERIAL_REPORT_NODES_GOLDEN = frozenset({
    "test_p3_b4_material_report.py::test_normal_path_assembles_binds_evaluates_and_builds_document",
    "test_p3_b4_material_report.py::test_m01_m02_assembly_rejection_still_reports_201_blocks_and_missing_leaf",
    "test_p3_b4_material_report.py::test_partial_campaign_discovery_fails_closed_for_output_campaigns_path",
    "test_p3_b4_material_report.py::test_partial_campaign_discovery_rejects_recovered_campaign_root_sibling",
    "test_p3_b4_material_report.py::test_complete_projection_preserves_402_sources_fields_and_transcribed_binding",
    "test_p3_b4_material_report.py::test_markdown_provenance_argv_and_required_columns_match_json_rows",
    "test_p3_b4_material_report.py::test_markdown_escape_orders_backslash_pipe_and_normalizes_cr_lf",
    "test_p3_b4_material_report.py::test_artifact_availability_is_frozen_once_per_planned_leaf",
    "test_p3_b4_material_report.py::test_m03_m04_m05_m06_m07_m14_m17_m18_public_builder_rejects_projection_mutations",
    "test_p3_b4_material_report.py::test_input_artifact_projection_rejects_one_byte_rewrite_through_public_builder",
    "test_p3_b4_material_report.py::test_m8_absent_authority_public_bytes_match_pre_change_golden",
    "test_p3_b4_material_report.py::test_present_floor_projects_required_verbatim_non_guarantees",
    "test_p3_b4_material_report.py::test_m9_four_authority_and_assembly_states_project_exactly",
    "test_p3_b4_material_report.py::test_m7_non_sentinel_resolver_failure_never_falls_back_or_calls_evaluator",
    "test_p3_b4_material_report.py::test_m08_floor_absence_runs_existing_evaluator_as_protocol_violation",
    "test_p3_b4_material_report.py::test_m09_renderer_only_future_compatibility_preserves_four_verdict_wire_values",
    "test_p3_b4_material_report.py::test_m10_m11_m12_output_campaign_intersection_three_directions_write_nothing",
    "test_p3_b4_material_report.py::test_m13_lexical_dotdot_alias_reaches_resolved_campaign_comparison",
    "test_p3_b4_material_report.py::test_output_symlink_component_is_rejected_before_any_report_write",
    "test_p3_b4_material_report.py::test_m15_real_issuer_exception_is_wrapped_with_reason_and_writes_nothing",
    "test_p3_b4_material_report.py::test_publication_symlink_alias_remains_rejected_by_existing_loader",
    "test_p3_b4_material_report.py::test_m15_real_ledger_exception_type_is_wrapped_and_writes_nothing",
    "test_p3_b4_material_report.py::test_m16a_existing_pair_is_rejected_before_publication_reload",
    "test_p3_b4_material_report.py::test_m16b_prepublication_race_check_rejects_new_target",
    "test_p3_b4_material_report.py::test_m16c_create_only_link_rejects_collision_without_other_guards",
    "test_p3_b4_material_report.py::test_commit_marker_is_last_and_binds_both_durable_files",
    "test_p3_b4_material_report.py::test_second_link_failure_rolls_back_pair_and_leaves_no_commit_marker",
    "test_p3_b4_material_report.py::test_commit_marker_link_failure_rolls_back_both_staged_artifacts",
    "test_p3_b4_material_report.py::test_rollback_failure_is_reported_instead_of_suppressed",
    "test_p3_b4_material_report.py::test_cli_clean_subprocess_runs_twice_and_refuses_overwrite",
    "test_p3_b4_material_report.py::test_outputs_contain_no_combining_diacritic_codepoints",
})

_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN = {
    "campaign-repository-scan": _CAMPAIGN_REPOSITORY_SCAN_NODES_GOLDEN,
    "p3-b4-material-report": _P3_B4_MATERIAL_REPORT_NODES_GOLDEN,
    "s8c-predicate-snapshot": _S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN,
    "s8c-preregistration-candidate": _S8C_PREREGISTRATION_CANDIDATE_NODES_GOLDEN,
}

# Production matrix から導出しない exact golden。各辺は下の実 fixture / resource
# access literal によって独立に理由付けされる。
_REAL_REPO_GROUP_CONFLICT_EDGES_GOLDEN = frozenset({
    ("campaign-repository-scan", "real-repo"),
    ("campaign-repository-scan", "s8c-predicate-snapshot"),
    ("campaign-repository-scan", "s8c-preregistration-candidate"),
    ("real-repo", "s8c-predicate-snapshot"),
    ("real-repo", "s8c-preregistration-candidate"),
    ("s8c-predicate-snapshot", "s8c-preregistration-candidate"),
})

_T810_LIVE_AUTHORITY_NODES_GOLDEN = frozenset({
    "test_t810_coordinator.py::test_prepare_group_rejects_forged_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_accepts_external_root_with_anchor_union",
})

_NESTED_COLLECTION_NODES_GOLDEN = frozenset({
    "test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes",
    "test_real_repo_serialization.py::test_shard_assignment_preserves_live_xdist_group_components_and_split_control",
    "test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order",
})

_REAL_REPO_FIXTURE_ACCESS_GOLDEN = {
    "test_s8c_preregistration_invariant.py::repository_candidate_commit[module]": {
        "group": "s8c-preregistration-candidate",
        "consumers": _S8C_PREREGISTRATION_CANDIDATE_NODES_GOLDEN,
        "accesses": (("parent", "write"), ("parent", "read")),
    },
    "test_s8c_preregistration_predicates.py::current_commit_snapshot[module]": {
        "group": "s8c-predicate-snapshot",
        "consumers": _S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN,
        "accesses": (("parent", "read"),),
    },
    "test_s8c_preregistration_predicates.py::repository_candidate_commit[function]": {
        # The only consumer shares its file component with this retained group.
        "group": "s8c-predicate-snapshot",
        "consumers": frozenset({
            "test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module",
        }),
        "accesses": (("parent", "write"), ("parent", "read")),
    },
    "test_campaign_import_invariant.py::repository_scan[module]": {
        "group": "campaign-repository-scan",
        "consumers": _CAMPAIGN_REPOSITORY_SCAN_NODES_GOLDEN,
        "accesses": (("parent", "read"), ("ccbench", "read")),
    },
}

_SAME_PROCESS_FIXTURE_MODE_COMPATIBILITY_GOLDEN = ({
    "outer": (
        "test_s8c_preregistration_predicates.py::"
        "current_commit_snapshot[module]"
    ),
    "inner": (
        "test_s8c_preregistration_predicates.py::"
        "repository_candidate_commit[function]"
    ),
    "resource": "parent",
    "outer_mode": "read",
    "inner_mode": "write",
    "effective_mode": "write",
    "restored_mode": "read",
},)

# Independent oracle for the sort-SWO environment consumer registry.  This is
# intentionally a second literal rather than an import/derivation from
# conftest.py, so a registry edit cannot update its expected set in lockstep.
ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN = frozenset({
    "test_sort_swo_oracle.py::test_cpp_e2e_clean_generic_lambda_positive",
    "test_sort_swo_oracle.py::test_cpp_e2e_canonical_fixture_trusted_control_compiles_and_runs",
    "test_sort_swo_oracle.py::test_cpp_e2e_stable_cross_allocation_pointer_positive",
    "test_sort_swo_oracle.py::test_real_ctor_pointer_topology_and_triplicate_have_expected_matrix_meaning",
    "test_sort_swo_oracle.py::test_cpp_e2e_reports_each_axiom_and_exact_indices",
    "test_sort_swo_oracle.py::test_cpp_e2e_high_storage_only_negative_kills_corpus_narrowing",
    "test_sort_swo_oracle.py::test_cpp_e2e_rejects_corpus_mutation_with_dedicated_reason",
    "test_sort_swo_oracle.py::test_cpp_e2e_rejects_same_process_call_count_dependence_with_witness",
    "test_sort_swo_oracle.py::test_real_compile_budget_is_fixed_positive_and_negative_only",
    "test_sort_swo_oracle.py::test_materialized_marker_bytes_are_exact_and_proposal_hash_is_distinct",
    "test_sort_swo_oracle.py::test_phase_marker_runs_immediately_before_first_oracle_subprocess",
    "test_sort_swo_oracle.py::test_scratch_failure_is_unavailable_not_candidate_reject",
    "test_sort_swo_oracle.py::test_candidate_compile_failure_is_reject_not_unavailable",
    "test_sort_swo_oracle.py::test_candidate_compile_failure_with_failing_postflight_is_unavailable",
    "test_sort_swo_oracle.py::test_postflight_unavailable_retains_candidate_finding",
    "test_sort_swo_oracle.py::test_candidate_compile_reject_postflight_control_success_stays_reject",
    "test_sort_swo_oracle.py::test_candidate_artifact_cleanup_failure_preserves_receipt",
    "test_sort_swo_oracle.py::test_candidate_artifact_cleanup_and_postflight_failure_preserve_evidence",
    "test_sort_swo_oracle.py::test_candidate_compile_infrastructure_failure_with_successful_postflight_stays_unavailable",
    "test_sort_swo_oracle.py::test_candidate_compile_infrastructure_and_postflight_failure_uses_postflight_detail",
    "test_sort_swo_oracle.py::test_postflight_source_write_oserror_preserves_receipt",
    "test_sort_swo_oracle.py::test_postflight_cleanup_oserror_preserves_receipt",
    "test_sort_swo_oracle.py::test_postflight_programmer_error_is_not_infrastructure",
    "test_sort_swo_oracle.py::test_trusted_positive_preflight_compile_failure_is_unavailable",
    "test_sort_swo_oracle.py::test_public_api_propagates_exact_evaluator_axiom_finding",
    "test_sort_swo_oracle.py::test_trusted_evaluator_matches_real_tu_for_all_79_ir_values",
})

# conftest の receipt consumer 正本から導出しない独立 oracle。
_RECEIPT_MEMO_CONSUMERS_GOLDEN = frozenset({
    "test_s8b_oracle_driver.py::test_success_wal_order_budget_and_evaluate_contract",
    "test_s8b_oracle_driver.py::test_oracle_pipeline_contract_keyword_is_mandatory_positive_control",
    "test_s8b_oracle_driver.py::test_oracle_evaluate_fn_without_condition_records_cannot_complete",
    "test_s8b_oracle_driver.py::test_build_result_contract_mismatch_aborts_campaign_before_measurement",
    "test_s8b_oracle_driver.py::test_binding_mismatch_refuses_only_that_row_before_evaluate",
    "test_s8b_oracle_driver.py::test_v8_bulk_reservation_unavailable_runs_nothing",
    "test_s8b_oracle_driver.py::test_reservation_envelope_exceeded_is_fail_closed",
    "test_s8b_oracle_driver.py::test_verify_inconclusive_and_unknown_abort_reasons_are_fail_closed",
    "test_s8b_oracle_driver.py::test_probe_error_reason_is_fail_closed_unknown_abort",
    "test_s8b_oracle_driver.py::test_v3_all_rows_binding_refused_is_protocol_violation",
    "test_s8b_oracle_driver.py::test_v3_partial_binding_refused_is_protocol_violation",
    "test_s8b_oracle_driver.py::test_v6_freeze_swap_after_verify_is_not_observed",
    "test_s8b_oracle_driver.py::test_v7_manifest_swap_after_verify_is_not_observed",
    "test_s8b_oracle_driver.py::test_v2_resume_rejected_at_s1_s2_s3_boundaries",
    "test_s8b_oracle_driver.py::test_atomic_one_shot_lock_rejects_second_start",
    "test_s8b_oracle_driver.py::test_resume_wal_lstat_eio_propagates_fail_closed_from_public_driver",
    "test_s8b_oracle_driver.py::test_driver_full_frame_fsync_eio_is_not_folded_or_followed_up",
    "test_s8b_oracle_driver.py::test_v4_marker_fires_across_output_root_change",
    "test_s8b_oracle_driver.py::test_v5_truncated_wal_rejects_resume_even_with_zero_parseable_records",
    "test_s8b_oracle_driver.py::test_official_driver_records_returncodes_through_real_producer_flow",
    "test_s8b_oracle_driver.py::test_unavailable_preflight_creates_bound_measurement_manifest_and_passes_false_kwargs",
    "test_s8b_oracle_driver.py::test_available_preflight_preserves_call_and_artifact_shape",
    "test_s8b_oracle_driver.py::test_probe_error_precedes_claim_marker_wal_and_budget",
    "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_cli_output_root_default_is_none_and_run_block_refuses_without_root",
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_oracle_driver.py::test_run_block_reuses_launch_validated_and_legacy_loader_is_dead",
    "test_s8b_oracle_driver.py::test_run_block_verifies_manifest_once_and_reuses_object",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
    "test_s8b_binding_driftguards.py::test_receipt_memo_delegates_to_production_verifier_exactly_once",
    "test_s8b_binding_driftguards.py::test_receipt_memo_patches_the_driver_module_the_tests_import",
})

_RECEIPT_MEMO_OPTOUT_GOLDEN = frozenset({
    "test_s8b_oracle_driver.py::test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result",
    "test_s8b_oracle_driver.py::test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4",
})


def _load_suite_conftest():
    spec = importlib.util.spec_from_file_location(
        "izanagi_test_suite_conftest", HERE / "conftest.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- 一時ディレクトリの置き場ガード -------------------------------------------------
#
# tmpfs (``/dev/shm`` 等) の使用量はユーザーの memory cgroup へほぼ 1:1 で課金される。
# Pegasus ログインノードのユーザーメモリ枠は 16 GiB (cgroup v2 ``memory.max`` =
# 17179869184) で、受入全走 1 回の tmpfs peak 7.39 GiB (bnode033、request 874750 実測)
# なら 2 回で使い切る。conftest はもう TMPDIR を設定しないが、将来また tmpfs へ
# 向いたらここで赤くなる。skip するのは (a) mountinfo を読めず判定不能なとき、
# (b) TMPDIR 未設定で環境既定 (/tmp) が tmpfs なとき — (b) はユーザーも本 repo も
# 何も選んでいない無過失の赤を避けるため (段 6 レビュー W2 の裁定)。source 上の
# 結線検査 (find_tmpfs_tmpdir_wiring) は環境に依らず常に赤にできる方の歯である。

_TMPFS_FSTYPES = frozenset({"tmpfs", "ramfs", "devtmpfs", "hugetlbfs"})

# TMPDIR へ代入されたら退行と見なす tmpfs 族の慣用パス。実 mount 表を引けない
# source 検査 (find_tmpfs_tmpdir_wiring) 側の判定に使う。
_TMPFS_PATH_ROOTS = (
    "/dev/shm", "/run/shm", "/var/run/shm", "/run/user", "/var/run/user",
)


def _unescape_mountinfo_field(field: str) -> str:
    r"""mountinfo の 8 進エスケープ (\040 空白 / \011 tab / \012 改行 / \134 backslash) を戻す。"""
    out: list[str] = []
    index = 0
    size = len(field)
    while index < size:
        char = field[index]
        if (char == "\\" and index + 3 < size
                and all(c in "01234567" for c in field[index + 1:index + 4])):
            out.append(chr(int(field[index + 1:index + 4], 8)))
            index += 4
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _path_is_within(path: str, mount_point: str) -> bool:
    base = mount_point.rstrip("/")
    return path == mount_point or path == base or path.startswith(base + "/")


def _fs_type(path: str, mountinfo_text: str | None = None,
             *, resolve: bool = True) -> str | None:
    """``path`` を含む mount の fstype を返す。判定不能なら None。

    Python の ``os.statvfs`` は ``f_type`` を公開しないので ``/proc/self/mountinfo``
    を最長前方一致で引く。``mountinfo_text`` を渡すと合成 mount 表で検査できる
    (positive/negative control 用)。``resolve`` は realpath の適用可否で、既定の
    True が本番経路 — symlink 越しに tmpfs を掴むのを取り逃さないために要る。

    campaign/durable_root.py にも mountinfo parser があるが、あちらは mount ID 境界の
    fail-closed 検査専用で fstype を持たない。テスト用ガードのために production の
    契約を広げないので、ここでは読み取り専用の小さな parser を別に置く。
    """
    if mountinfo_text is None:
        try:
            with open("/proc/self/mountinfo", encoding="utf-8") as handle:
                mountinfo_text = handle.read()
        except OSError:
            return None
    target = os.path.realpath(path) if resolve else os.path.abspath(path)
    best_length = -1
    best_type = None
    for line in mountinfo_text.splitlines():
        fields = line.split()
        if "-" not in fields:
            continue
        separator = fields.index("-")
        # 必須 6 field の後に optional field が並び、単独の "-" が終端になる。
        if separator < 6 or separator + 1 >= len(fields):
            continue
        mount_point = _unescape_mountinfo_field(fields[4])
        if not _path_is_within(target, mount_point):
            continue
        # 同じ mount point への overmount では後勝ちなので >= で更新する。
        if len(mount_point) >= best_length:
            best_length = len(mount_point)
            best_type = _unescape_mountinfo_field(fields[separator + 1])
    return best_type


def _tmpdir_verdict(path: str, mountinfo_text: str | None = None,
                    *, resolve: bool = True) -> tuple[str, str | None]:
    """``(status, fstype)`` を返す。status は "ok" / "tmpfs" / "unknown"。"""
    fstype = _fs_type(path, mountinfo_text, resolve=resolve)
    if fstype is None:
        return ("unknown", None)
    if fstype in _TMPFS_FSTYPES:
        return ("tmpfs", fstype)
    return ("ok", fstype)


def _effective_tmpdir_candidates() -> list[tuple[str, bool]]:
    """一時ファイルが実際に落ちる場所と、それが明示 ``TMPDIR`` 由来かの対。

    自プロセス (``tempfile.gettempdir()``) と、env を継承する subprocess (``TMPDIR``)
    の両方を見る。第 2 要素 True は「ユーザーが ``TMPDIR`` で明示的に選んだ場所」で、
    tmpfs なら退行として赤にする。False は環境既定 (``/tmp`` 等) で、ユーザーが何も
    選んでいないので tmpfs でも赤にはせず skip へ倒す (段 6 レビュー W2 の裁定)。
    """
    default_tmpdir = tempfile.gettempdir()
    env_tmpdir = os.environ.get("TMPDIR") or None
    candidates = [(default_tmpdir, env_tmpdir is not None and default_tmpdir == env_tmpdir)]
    if env_tmpdir is not None and env_tmpdir != default_tmpdir:
        candidates.append((env_tmpdir, True))
    return candidates


def _is_tmpfs_path_literal(text: object) -> bool:
    if not isinstance(text, str) or not text.startswith("/"):
        return False
    normalized = os.path.normpath(text)
    return any(normalized == root or normalized.startswith(root + "/")
               for root in _TMPFS_PATH_ROOTS)


def _static_str(node: ast.AST | None, constants: dict[str, str]) -> str | None:
    """AST node から静的に決まる文字列 (前方一致に足る接頭辞) を best-effort で取り出す。"""
    if node is None:
        return None
    if node.__class__.__name__ == "Index":  # Python 3.8 以前の subscript
        return _static_str(node.value, constants)  # type: ignore[attr-defined]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                break  # 動的部分より手前の接頭辞だけで判定する
        return "".join(parts) or None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _static_str(node.left, constants)
    if isinstance(node, ast.Call):
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name in ("join", "expanduser", "normpath", "realpath", "abspath") and node.args:
            return _static_str(node.args[0], constants)
    return None


def _string_constants(tree: ast.AST) -> dict[str, str]:
    """``_SHM = "/dev/shm"`` 形の module 定数を解決表にする (literal 直書き以外を殺すため)。"""
    constants: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        value = node.value
        if (isinstance(target, ast.Name) and isinstance(value, ast.Constant)
                and isinstance(value.value, str)):
            constants[target.id] = value.value
    return constants


def _is_tmpdir_environ_subscript(node: ast.AST, constants: dict[str, str]) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    container = node.value
    name = (container.attr if isinstance(container, ast.Attribute)
            else getattr(container, "id", None))
    if name != "environ":
        return False
    return _static_str(node.slice, constants) == "TMPDIR"


def _is_tempfile_tempdir_target(node: ast.AST) -> bool:
    """``tempfile.tempdir`` への代入 target か (env を経由しない in-process 結線)。

    ``os.environ["TMPDIR"]`` 系だけを見ていると、``tempfile.tempdir = "/dev/shm"``
    という一行で ``tmp_path`` と in-process の ``tempfile.*`` (= tmpfs peak 7.39 GiB の
    主因) がまるごと tmpfs へ戻るのを取り逃す。撤去前の conftest 自身が
    ``tempfile.tempdir = None`` を使っていたので、「速度を戻す」編集が最も自然に
    触る属性でもある (段 6 レビュー N2 が変異で実証)。

    ``import tempfile as tf`` の alias を取り逃さないよう属性名だけで判定する。
    tmpfs リテラル代入だけを hit にするので、無関係な ``x.tempdir`` の誤検出面は
    「tmpfs パスを tempdir 名の属性へ代入する」形に限られる。

    **実行時の ``tempfile.tempdir`` の値では判定してはいけない。** CPython の
    ``gettempdir()`` は初回呼出しで ``tempfile.tempdir`` へ既定値を書き込む
    (CPython 3.10.12 実測で ``None`` → ``/tmp``) ため、明示指定と既定値を実行時の値では
    区別できない。だから source 側で捕まえる。
    """
    return isinstance(node, ast.Attribute) and node.attr == "tempdir"


def find_tmpfs_tmpdir_wiring(source: str) -> list[tuple[int, str]]:
    """source 内で一時領域を tmpfs へ結線している箇所を ``(行, パス)`` で返す。

    対象は ``os.environ["TMPDIR"]`` 系 (subprocess へ継承される env 経路) と
    ``tempfile.tempdir`` 系 (自プロセスの ``tmp_path`` / ``tempfile.*`` を移す
    in-process 経路) の両方。

    単なる文字列 grep ではなく AST を見る — docstring やコメントで ``/dev/shm`` に
    言及するだけの行を誤検出せず、``_SHM = "/dev/shm"`` を経由する間接代入
    (撤去前の conftest が使っていた形) を取り逃さないため。
    """
    tree = ast.parse(source)
    constants = _string_constants(tree)
    hits: set[tuple[int, str]] = set()

    def record(node: ast.AST, value_node: ast.AST | None) -> None:
        text = _static_str(value_node, constants)
        if _is_tmpfs_path_literal(text):
            hits.add((node.lineno, str(text)))

    def is_tmpdir_target(node: ast.AST) -> bool:
        return (_is_tmpdir_environ_subscript(node, constants)
                or _is_tempfile_tempdir_target(node))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if is_tmpdir_target(target):
                    record(node, node.value)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if is_tmpdir_target(node.target):
                record(node, node.value)
        elif isinstance(node, ast.Call):
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else getattr(func, "id", None))
            if name in ("setdefault", "putenv") and len(node.args) >= 2:
                if _static_str(node.args[0], constants) == "TMPDIR":
                    record(node, node.args[1])
            elif name == "update":
                for argument in node.args:
                    if not isinstance(argument, ast.Dict):
                        continue
                    for key, value in zip(argument.keys, argument.values):
                        if _static_str(key, constants) == "TMPDIR":
                            record(node, value)
                for keyword in node.keywords:
                    if keyword.arg == "TMPDIR":
                        record(node, keyword.value)
    return sorted(hits)


def _run_subprocess(argv, *, cwd, env=None):
    return subprocess.run(
        argv, cwd=str(cwd), env=env, capture_output=True, text=True,
    )


def _t080_output_snapshot(root: Path) -> tuple[tuple[object, ...], ...]:
    """Git-visible entry と非 ignore 祖先での一時作成後削除を捉える。

    規則由来 ignore prefix の祖先 directory だけ size / mtime / ctime を正規化する。
    """
    ignored_prefixes, ignored_ancestors = git_ignored_output_snapshot_rules(ROOT)
    entries = [
        root,
        *(
            path for path in root.rglob("*")
            if not is_git_ignored_output_path(
                path.relative_to(root).as_posix(), ignored_prefixes,
            )
        ),
    ]
    snapshot = []
    for path in sorted(entries):
        relative = path.relative_to(root).as_posix() if path != root else "."
        info = path.lstat()
        normalize = (
            stat.S_ISDIR(info.st_mode)
            and ignored_ancestors.contains(relative)
        )
        snapshot.append((
            relative,
            info.st_mode,
            None if normalize else info.st_size,
            None if normalize else info.st_mtime_ns,
            None if normalize else info.st_ctime_ns,
        ))
    return tuple(snapshot)


def test_t080_output_snapshot_detects_git_visible_real_output_changes(tmp_path):
    ignored_prefixes = git_ignored_output_prefixes(ROOT)
    assert not is_git_ignored_output_path("visible", ignored_prefixes)
    control = tmp_path / "visible"
    before = _t080_output_snapshot(tmp_path)
    try:
        control.mkdir()
        (control / "nested").mkdir()
        payload = control / "nested" / "payload.bin"
        payload.write_bytes(b"git-visible t080 snapshot positive control")

        after = _t080_output_snapshot(tmp_path)
        assert after != before
        relative_control = control.relative_to(tmp_path).as_posix()
        relative_payload = payload.relative_to(tmp_path).as_posix()
        assert any(row[0] == relative_control for row in after)
        assert any(row[0] == relative_payload for row in after)
    finally:
        shutil.rmtree(control, ignore_errors=True)


def test_t080_output_snapshot_excludes_git_ignored_real_output_changes(tmp_path):
    ignored_prefixes = git_ignored_output_prefixes(ROOT)
    assert "runs" in ignored_prefixes
    before = _t080_output_snapshot(tmp_path)
    ignored_parent = tmp_path / "runs"
    ignored_parent.mkdir()
    try:
        control = ignored_parent / "snapshot-ignored-t080"
        control.mkdir()
        (control / "nested").mkdir()
        (control / "nested" / "payload.bin").write_bytes(
            b"git-ignored t080 snapshot control"
        )

        assert _t080_output_snapshot(tmp_path) == before

        assert not is_git_ignored_output_path("runs-visible", ignored_prefixes)
        visible_before = _t080_output_snapshot(tmp_path)
        visible = tmp_path / "runs-visible" / "nested"
        visible.mkdir(parents=True)
        (visible / "payload.bin").write_bytes(b"git-visible runs prefix control")
        visible_after = _t080_output_snapshot(tmp_path)
        assert visible_after != visible_before, (
            "rule-derived ignore prefix 'runs' must not hide "
            "Git-visible 'runs-visible'"
        )
    finally:
        shutil.rmtree(ignored_parent, ignore_errors=True)
        shutil.rmtree(tmp_path / "runs-visible", ignore_errors=True)


def test_t080_output_snapshot_observes_git_visible_create_and_delete(tmp_path):
    ignored_ancestors = git_ignored_output_ancestor_directories(ROOT)
    parent = tmp_path / "visible-transient-parent"
    assert not ignored_ancestors.contains(parent.name)
    parent.mkdir()
    before = _t080_output_snapshot(tmp_path)
    transient = parent / "visible-transient"
    transient.mkdir()
    (transient / "payload").write_bytes(b"visible transient")
    shutil.rmtree(transient)
    after = _t080_output_snapshot(tmp_path)
    assert after != before, "Git-visible create-and-delete must remain observable"


def _require_pytest() -> None:
    try:
        __import__("pytest")
    except ImportError:
        skip("pytest 不在 — pytest 依存検査を実行できない")


def _collect_xdist_group_report(
    target: Path, *, cwd: Path, collection_options: tuple[str, ...] = (),
    lastfailed_nodeids: tuple[str, ...] = (),
    cached_nodeids: tuple[str, ...] = (),
) -> list[dict]:
    """temp plugin で collection 後の全 xdist_group marker を取得する。"""
    with tempfile.TemporaryDirectory(prefix="izanagi-real-repo-collect-") as raw_tmp:
        tmp = Path(raw_tmp)
        report_path = tmp / "markers.json"
        plugin_path = tmp / "real_repo_collection_plugin.py"
        plugin_path.write_text(
            textwrap.dedent(
                """
                import json
                import os
                from pathlib import Path

                def shared_fixture_closure(item):
                    fixtureinfo = getattr(item, "_fixtureinfo", None)
                    if fixtureinfo is None:
                        raise TypeError(f"{item.nodeid}: item._fixtureinfo がない")
                    names = getattr(fixtureinfo, "names_closure", None)
                    definitions = getattr(fixtureinfo, "name2fixturedefs", None)
                    if not isinstance(names, (list, tuple)):
                        raise TypeError(
                            f"{item.nodeid}: names_closure の型が不正: {type(names)!r}"
                        )
                    if not isinstance(definitions, dict):
                        raise TypeError(
                            f"{item.nodeid}: name2fixturedefs の型が不正: "
                            f"{type(definitions)!r}"
                        )
                    closure = set()
                    for name in names:
                        if not isinstance(name, str):
                            raise TypeError(
                                f"{item.nodeid}: fixture 名の型が不正: {type(name)!r}"
                            )
                        fixturedefs = definitions.get(name)
                        if fixturedefs is None:
                            continue
                        if not isinstance(fixturedefs, (list, tuple)) or not fixturedefs:
                            raise TypeError(
                                f"{item.nodeid}: {name} の fixturedefs が不正: "
                                f"{type(fixturedefs)!r}"
                            )
                        fixturedef = fixturedefs[-1]
                        scope = getattr(fixturedef, "scope", None)
                        baseid = getattr(fixturedef, "baseid", None)
                        argname = getattr(fixturedef, "argname", None)
                        if not all(isinstance(value, str) for value in (scope, baseid, argname)):
                            raise TypeError(
                                f"{item.nodeid}: {name} の FixtureDef 属性が不正"
                            )
                        # fixture-owned lock の function consumer も C3 の閉包に必要。
                        # 空 baseid の pytest/plugin 組込み fixture だけを除外する。
                        if baseid:
                            closure.add(f"{baseid}::{argname}[{scope}]")
                    return sorted(closure)

                def pytest_collection_finish(session):
                    report = []
                    for item in session.items:
                        marks = list(item.iter_markers(name="xdist_group"))
                        function = (getattr(item, "originalname", None)
                                    or item.name.split("[", 1)[0])
                        node = f"{item.path.name}::{function}"
                        report.append({
                            "nodeid": item.nodeid,
                            "canonical_node": node,
                            "fixture_closure": shared_fixture_closure(item),
                            "real_repo_access": (
                                {
                                    "parent": getattr(
                                        item, "_izanagi_real_repo_access"
                                    ).parent,
                                    "ccbench": getattr(
                                        item, "_izanagi_real_repo_access"
                                    ).ccbench,
                                }
                                if hasattr(item, "_izanagi_real_repo_access")
                                else None
                            ),
                            "marks": [
                                {"args": list(mark.args),
                                 "kwargs": dict(mark.kwargs)}
                                for mark in marks
                            ],
                        })
                    consumers = {}
                    for entry in report:
                        for fixture in entry["fixture_closure"]:
                            consumers.setdefault(fixture, set()).add(
                                entry["canonical_node"]
                            )
                    if report:
                        report[0]["fixture_consumers"] = {
                            fixture: sorted(nodes)
                            for fixture, nodes in sorted(consumers.items())
                        }
                    Path(os.environ["IZANAGI_REAL_REPO_MARK_REPORT"]).write_text(
                        json.dumps(report, sort_keys=True), encoding="utf-8",
                    )
                """
            ),
            encoding="utf-8",
        )
        cache_dir = tmp / "pytest-cache"
        cache_values = cache_dir / "v" / "cache"
        if lastfailed_nodeids or cached_nodeids:
            cache_values.mkdir(parents=True)
        if lastfailed_nodeids:
            (cache_values / "lastfailed").write_text(
                json.dumps(dict.fromkeys(lastfailed_nodeids, True)),
                encoding="utf-8",
            )
        if cached_nodeids:
            (cache_values / "nodeids").write_text(
                json.dumps(list(cached_nodeids)), encoding="utf-8",
            )
        env = os.environ.copy()
        env["IZANAGI_REAL_REPO_MARK_REPORT"] = str(report_path)
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(tmp), env.get("PYTHONPATH", "")) if part
        )
        proc = _run_subprocess(
            [
                sys.executable, "-m", "pytest", "--collect-only", "-q",
                "-o", f"cache_dir={cache_dir}",
                *collection_options,
                "-p", "real_repo_collection_plugin", str(target),
            ],
            cwd=cwd,
            env=env,
        )
        assert proc.returncode == 0, (
            f"collection subprocess failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
        return json.loads(report_path.read_text(encoding="utf-8"))


def _collect_t080_default_execution_report(
        target_module: Path, target_nodeids: set[str]) -> dict[str, object]:
    """全 file collection と対象 node の setup outcome を別走で実測する。"""
    target_module = target_module.resolve()
    target_functions = {
        nodeid.split("::", 1)[1].split("[", 1)[0]
        for nodeid in target_nodeids
    }
    assert all(
        nodeid.startswith(f"{target_module.name}::")
        for nodeid in target_nodeids
    ), target_nodeids
    probe_temp_root = Path(tempfile.gettempdir()).resolve()
    real_output = (ROOT / "output").resolve()
    assert (
        probe_temp_root != real_output
        and not probe_temp_root.is_relative_to(real_output)
    ), (
        "T-080 E2E temp root は実 repo の output/ 配下に置けない: "
        f"{probe_temp_root}"
    )
    with tempfile.TemporaryDirectory(
            prefix="izanagi-t080-default-collect-", dir=probe_temp_root,
            ) as raw_tmp:
        tmp = Path(raw_tmp)
        collect_report_path = tmp / "collect-report.json"
        setup_report_path = tmp / "setup-report.json"
        plugin_path = tmp / "t080_default_execution_plugin.py"
        plugin_path.write_text(
            textwrap.dedent(
                """
                import json
                import os
                from pathlib import Path

                TARGETS = set(json.loads(os.environ["IZANAGI_T080_TARGETS"]))
                REPORT = {
                    "selected": [],
                    "deselected": [],
                    "markers": {},
                    "setup": {},
                }

                def canonical_nodeid(nodeid):
                    path, separator, tail = nodeid.partition("::")
                    if not separator:
                        return nodeid
                    return f"{Path(path).name}::{tail}"

                def target_name(nodeid):
                    canonical = canonical_nodeid(nodeid)
                    return canonical.split("::")[-1].split("[", 1)[0]

                def pytest_collection_finish(session):
                    for item in session.items:
                        name = (getattr(item, "originalname", None)
                                or item.name.split("[", 1)[0])
                        if name not in TARGETS:
                            continue
                        nodeid = canonical_nodeid(item.nodeid)
                        REPORT["selected"].append(nodeid)
                        REPORT["markers"][nodeid] = sorted(
                            marker.name for marker in item.iter_markers()
                        )

                def pytest_deselected(items):
                    for item in items:
                        if target_name(item.nodeid) in TARGETS:
                            REPORT["deselected"].append(
                                canonical_nodeid(item.nodeid)
                            )

                def pytest_runtest_logreport(report):
                    if report.when != "setup" or target_name(report.nodeid) not in TARGETS:
                        return
                    REPORT["setup"][canonical_nodeid(report.nodeid)] = {
                        "outcome": report.outcome,
                        "wasxfail": getattr(report, "wasxfail", None),
                    }

                def pytest_sessionfinish(session, exitstatus):
                    Path(os.environ["IZANAGI_T080_REPORT"]).write_text(
                        json.dumps(REPORT, sort_keys=True), encoding="utf-8",
                    )
                """
            ),
            encoding="utf-8",
        )
        env = os.environ.copy()
        for name in (
            "PYTEST_ADDOPTS",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
            "PYTEST_PLUGINS",
            "IZANAGI_RUN_GROWTH_HELD_TESTS",
            "IZANAGI_T080_E2E",
        ):
            env.pop(name, None)
        env["IZANAGI_T080_TARGETS"] = json.dumps(sorted(target_functions))
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(tmp), env.get("PYTHONPATH", "")) if part
        )

        def run_probe(*args: str, report_path: Path, cache_name: str):
            probe_env = env.copy()
            probe_env["PYTHONDONTWRITEBYTECODE"] = "1"
            probe_env["IZANAGI_T080_REPORT"] = str(report_path)
            return subprocess.run(
                [
                    sys.executable, "-m", "pytest", "-q", "-n0",
                    "-o", f"cache_dir={tmp / cache_name}",
                    "-p", "t080_default_execution_plugin", *args,
                ],
                cwd=ROOT, env=probe_env, check=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True,
            )

        collected = run_probe(
            "--collect-only", str(target_module),
            report_path=collect_report_path, cache_name="collect-cache",
        )
        assert collect_report_path.is_file(), (
            "T-080 collect report が生成されなかった: "
            f"rc={collected.returncode} stderr={collected.stderr}"
        )
        report = json.loads(collect_report_path.read_text(encoding="utf-8"))

        absolute_target_nodeids = [
            str(target_module) + nodeid.removeprefix(target_module.name)
            for nodeid in sorted(target_nodeids)
        ]
        setup = run_probe(
            "--setup-only", *absolute_target_nodeids,
            report_path=setup_report_path, cache_name="setup-cache",
        )
        assert setup_report_path.is_file(), (
            "T-080 setup report が生成されなかった: "
            f"rc={setup.returncode} stderr={setup.stderr}"
        )
        setup_report = json.loads(setup_report_path.read_text(encoding="utf-8"))
        report["setup"] = setup_report["setup"]
        report["diagnostic"] = (
            f"collect_rc={collected.returncode} setup_rc={setup.returncode}"
        )
        return report


def test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default():
    """T-080 E2E 11 node の skip / xfail / deselect / setup skip を実測する。"""
    target_functions = {
        "test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5",
        "test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5",
        "test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5",
        "test_t080_full_valid_history_defects_have_one_baseline_reason_f28",
        "test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28",
        "test_never_issued_generator_tamper_reaches_public_driver_gate_g7",
    }
    expected_nodeids = {
        "test_s8b_oracle_driver.py::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5",
        "test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]",
        "test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]",
        "test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]",
        "test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]",
        "test_s8b_oracle_driver.py::test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5",
        "test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]",
        "test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]",
        "test_s8b_oracle_driver.py::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[modify-revert-receipt.history_mutated]",
        "test_s8b_oracle_driver.py::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28",
        "test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7",
    }

    assert target_functions == {
        nodeid.split("::", 1)[1].split("[", 1)[0]
        for nodeid in expected_nodeids
    }
    report = _collect_t080_default_execution_report(
        HERE / "test_s8b_oracle_driver.py", expected_nodeids,
    )
    assert set(report["selected"]) == expected_nodeids, report
    assert len(report["selected"]) == len(expected_nodeids), report
    assert report["deselected"] == [], report
    forbidden_markers = {"skip", "skipif", "xfail"}
    assert all(
        forbidden_markers.isdisjoint(markers)
        for markers in report["markers"].values()
    ), report
    assert report["setup"] == {
        nodeid: {"outcome": "passed", "wasxfail": None}
        for nodeid in expected_nodeids
    }, report


def test_t080_import_temp_environment_fails_closed_for_foreign_module():
    """foreign module の import-time temp 境界が副作用なしで発火する。"""
    forbidden = ROOT / "output"
    before = _t080_output_snapshot(forbidden)
    import_env = os.environ.copy()
    for name in ("TMPDIR", "TEMP", "TMP"):
        import_env.pop(name, None)
    import_env["TMPDIR"] = str(forbidden)
    import_env["PYTHONDONTWRITEBYTECODE"] = "1"
    imported = subprocess.run(
        [
            sys.executable, "-c",
            "import orchestrator.tests.test_s8b_oracle_driver",
        ],
        cwd=ROOT, env=import_env, check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    assert imported.returncode != 0
    assert "T-080 E2E temp root は実 repo の output/ 配下" in imported.stderr
    assert _t080_output_snapshot(forbidden) == before


def _assert_xdist_group_contract(
    report: list[dict], expected_group_names: set[str] | frozenset[str],
) -> None:
    """全 collected item の marker 個数・表記・group 名閉包を検査する。"""
    actual_group_names = set()
    for entry in report:
        marks = entry["marks"]
        assert len(marks) <= 1, (
            "xdist_group marker は 1 node につき最大 1 個でなければならない: "
            f"nodeid={entry['nodeid']} marks={marks!r}"
        )
        if not marks:
            continue
        mark = marks[0]
        args = mark["args"]
        kwargs = mark["kwargs"]
        assert (
            len(args) == 1
            and isinstance(args[0], str)
            and not kwargs
        ), (
            "xdist_group 名は positional 引数 1 個で与えなければならない: "
            f"nodeid={entry['nodeid']} mark={mark!r}"
        )
        actual_group_names.add(args[0])
    assert actual_group_names == set(expected_group_names), (
        "xdist_group 名集合が独立 golden と不一致: "
        f"missing={sorted(set(expected_group_names) - actual_group_names)} "
        f"extra={sorted(actual_group_names - set(expected_group_names))}"
    )


def _fixture_consumers_from_report(report: list[dict]) -> dict[str, set[str]]:
    """per-item closure と subprocess 側 consumer 集約を相互検査する。"""
    actual: dict[str, set[str]] = {}
    declarations = []
    for entry in report:
        canonical = entry["canonical_node"]
        closure = entry.get("fixture_closure")
        assert isinstance(closure, list) and all(
            isinstance(fixture, str) for fixture in closure
        ), f"fixture_closure の型が不正: node={canonical!r} value={closure!r}"
        for fixture in closure:
            actual.setdefault(fixture, set()).add(canonical)
        if "fixture_consumers" in entry:
            declarations.append(entry["fixture_consumers"])
    assert len(declarations) == 1, (
        f"fixture consumer 集約は report に 1 個必要: count={len(declarations)}"
    )
    declared_raw = declarations[0]
    assert isinstance(declared_raw, dict), "fixture consumer 集約が dict でない"
    declared = {}
    for fixture, consumers in declared_raw.items():
        assert isinstance(fixture, str) and isinstance(consumers, list)
        assert all(isinstance(node, str) for node in consumers)
        declared[fixture] = set(consumers)
    assert declared == actual, (
        "fixture consumer 集約が per-item closure と不一致: "
        f"declared={declared!r} actual={actual!r}"
    )
    return actual


def _assert_long_lived_fixture_group_contract(
    report: list[dict], resource_nodes: set[str] | frozenset[str], suite_conftest,
) -> None:
    """Pin every fixture owner, its consumers, disjointness, and nested modes."""
    actual_by_group = {
        group: {
            entry["canonical_node"]
            for entry in report
            if entry["marks"] and entry["marks"][0]["args"][0] == group
        }
        for group in _LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN
    }
    assert actual_by_group == {
        group: set(nodes)
        for group, nodes in _LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN.items()
    }, (
        "long-lived fixture loadgroup consumers が独立 golden と不一致: "
        f"actual={actual_by_group!r}"
    )
    consumers = _fixture_consumers_from_report(report)
    actual_fixture_consumers = {}
    for fixture, contract in _REAL_REPO_FIXTURE_ACCESS_GOLDEN.items():
        matches = {
            name: nodes for name, nodes in consumers.items()
            if name.endswith(fixture)
        }
        assert len(matches) == 1, (
            f"long-lived fixture literal が collection に一意でない: "
            f"fixture={fixture!r} matches={sorted(matches)!r}"
        )
        actual = next(iter(matches.values()))
        assert actual == set(contract["consumers"]), (
            f"fixture-owned lock consumer 閉包が不一致: fixture={fixture!r} "
            f"actual={sorted(actual)!r} "
            f"expected={sorted(contract['consumers'])!r}"
        )
        actual_fixture_consumers[fixture] = actual

    literal_fixture_nodes = set().union(*(
        set(contract["consumers"])
        for contract in _REAL_REPO_FIXTURE_ACCESS_GOLDEN.values()
    ))
    live_fixture_nodes = set().union(*actual_fixture_consumers.values())
    assert live_fixture_nodes == literal_fixture_nodes, (
        "fixture-owned consumer の literal/live 集合が不一致: "
        f"literal={sorted(literal_fixture_nodes)!r} "
        f"live={sorted(live_fixture_nodes)!r}"
    )
    assert live_fixture_nodes.isdisjoint(resource_nodes), (
        "fixture-owned lock node と node-protocol resource node が重複した: "
        f"overlap={sorted(live_fixture_nodes & set(resource_nodes))!r}"
    )

    for contract in _SAME_PROCESS_FIXTURE_MODE_COMPATIBILITY_GOLDEN:
        outer = contract["outer"]
        inner = contract["inner"]
        assert outer in actual_fixture_consumers and inner in actual_fixture_consumers
        assert outer.partition("::")[0] == inner.partition("::")[0]
        outer_accesses = set(_REAL_REPO_FIXTURE_ACCESS_GOLDEN[outer]["accesses"])
        inner_accesses = set(_REAL_REPO_FIXTURE_ACCESS_GOLDEN[inner]["accesses"])
        assert (contract["resource"], contract["outer_mode"]) in outer_accesses
        assert (contract["resource"], contract["inner_mode"]) in inner_accesses
        holder_modes = Counter({
            (1, contract["outer_mode"]): 1,
            (1, contract["inner_mode"]): 1,
        })
        assert suite_conftest._real_repo_strongest_lock_mode(holder_modes) == (
            contract["effective_mode"]
        )
        del holder_modes[(1, contract["inner_mode"])]
        assert suite_conftest._real_repo_strongest_lock_mode(holder_modes) == (
            contract["restored_mode"]
        )


def _conflict_edges_from_independent_access_literals():
    """Derive a control from fixture/resource literals, never from production edges."""
    accesses: dict[str, set[tuple[str, str]]] = {
        group: set() for group in {
            "real-repo",
            *_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN,
        }
    }
    for parent, ccbench in _real_repo_access_golden().values():
        if parent is not None:
            accesses["real-repo"].add(("parent", parent))
        if ccbench is not None:
            accesses["real-repo"].add(("ccbench", ccbench))
    for contract in _REAL_REPO_FIXTURE_ACCESS_GOLDEN.values():
        accesses[contract["group"]].update(contract["accesses"])

    edges = set()
    groups = sorted(accesses)
    for index, left in enumerate(groups):
        for right in groups[index + 1:]:
            if any(
                left_resource == right_resource
                and "write" in {left_mode, right_mode}
                for left_resource, left_mode in accesses[left]
                for right_resource, right_mode in accesses[right]
            ):
                edges.add((left, right))
    return frozenset(edges)


def _assert_fixture_closure_complete(
    report: list[dict], canonical_nodes: set[str] | frozenset[str],
) -> None:
    """正本を seed とする共有 fixture consumer 閉包が欠けていないことを検査する。"""
    consumers = _fixture_consumers_from_report(report)
    # function scope は consumer ごとに実体を作り直し、consumer 間で共有しない。
    # この共有閉包の候補は、同じ実体を共有する session / module scope に限る。
    shared_consumers = {
        fixture: nodes for fixture, nodes in consumers.items()
        if fixture.endswith(("[session]", "[module]"))
    }
    assert shared_consumers, "共有 fixture consumer 導出結果が空 — detector 退行の疑い"
    for filename, fixture_name in (
        ("test_s1_measurement_freeze.py", "real_known_axes_doc"),
        ("test_codex_reasoning_ab.py", "benchmark_snapshots"),
    ):
        literal = f"{filename}::{fixture_name}[module]"
        matches = [
            nodes for fixture, nodes in shared_consumers.items()
            if fixture.endswith(literal)
        ]
        assert len(matches) == 1, (
            f"既知の共有 fixture literal が導出結果に一意に実在しない: {literal!r}"
        )
        assert len(matches[0]) >= 2, (
            f"既知の共有 fixture consumer が 2 未満: {literal!r} "
            f"consumers={sorted(matches[0])!r}"
        )
    seeded = {
        fixture for fixture, nodes in shared_consumers.items()
        if nodes & set(canonical_nodes)
    }
    missing = {
        fixture: sorted(shared_consumers[fixture] - set(canonical_nodes))
        for fixture in seeded
        if shared_consumers[fixture] - set(canonical_nodes)
    }
    assert not missing, (
        "REAL_REPO_CLASSIFIED_NODES が共有 fixture consumer について閉じていない: "
        f"missing={missing!r}"
    )


def _assert_no_direct_xdist_group_decorators(
    canonical_nodes: set[str] | frozenset[str], sources: dict[str, str],
) -> None:
    """canonical node の関数に手書き xdist_group decorator がないこと。"""
    assert canonical_nodes, "canonical node 集合が空では provenance を監査できない"
    nodes_by_file: dict[str, set[str]] = {}
    for canonical in canonical_nodes:
        filename, separator, function_name = canonical.partition("::")
        assert separator and filename and function_name, (
            f"canonical node が file::function 形でない: {canonical!r}"
        )
        nodes_by_file.setdefault(filename, set()).add(function_name)

    missing_sources = set(nodes_by_file) - set(sources)
    assert not missing_sources, (
        f"canonical node の source がない: {sorted(missing_sources)}"
    )
    missing_functions = []
    handwritten = []
    for filename, function_names in sorted(nodes_by_file.items()):
        module = ast.parse(sources[filename], filename=filename)
        functions = {
            node.name: node
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for function_name in sorted(function_names):
            function = functions.get(function_name)
            if function is None:
                missing_functions.append(f"{filename}::{function_name}")
                continue
            for decorator in function.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                target = decorator.func
                is_xdist_group = (
                    isinstance(target, ast.Attribute)
                    and target.attr == "xdist_group"
                ) or (
                    isinstance(target, ast.Name)
                    and target.id == "xdist_group"
                )
                if is_xdist_group:
                    handwritten.append(
                        f"{filename}::{function_name}:{decorator.lineno}"
                    )

    assert not missing_functions, (
        f"canonical node の関数定義が source にない: {missing_functions}"
    )
    assert not handwritten, (
        "REAL_REPO_RESOURCE_NODES の xdist_group は hook 由来でなければならず、"
        f"手書き decorator を許さない: {handwritten}"
    )


def _assert_real_repo_suffix_contract(report: list[dict]) -> None:
    """Plain collection preserves marker objects without xdist suffixes."""
    exact_mark = [{"args": ["real-repo"], "kwargs": {}}]
    for entry in report:
        assert not entry["nodeid"].endswith("@real-repo"), (
            f"plain collection synthesized xdist suffix: {entry!r}"
        )
        canonical = entry["canonical_node"]
        if canonical not in _REAL_REPO_CLASSIFIED_NODES_GOLDEN:
            continue
        is_resource = canonical not in _REAL_REPO_LOCAL_ONLY_NODES_GOLDEN
        assert (entry["marks"] == exact_mark) is is_resource


def _assert_real_repo_suffix_strip_mutation_killer(suite_conftest) -> None:
    """Exercise suffix stripping with nodeids already materialized by xdist."""

    class SuffixedItem:
        def __init__(self, canonical_node: str) -> None:
            filename, function = canonical_node.split("::", 1)
            self._nodeid = f"orchestrator/tests/{canonical_node}@real-repo"
            self.path = HERE / filename
            self.name = f"{function}@real-repo"
            self.originalname = function

        @property
        def nodeid(self) -> str:
            return self._nodeid

    split_node = "test_campaign.py::test_source_digest_parse_options_defaults"
    split_item = SuffixedItem(split_node)
    assert suite_conftest._strip_real_repo_loadgroup_suffix(split_item) is True
    assert split_item.nodeid == f"orchestrator/tests/{split_node}"

    memo_node = (
        "test_s8b_oracle_driver.py::"
        "test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing"
    )
    memo_item = SuffixedItem(memo_node)
    assert suite_conftest._strip_real_repo_loadgroup_suffix(memo_item) is False
    assert memo_item.nodeid == f"orchestrator/tests/{memo_node}@real-repo"

    local_only_node = (
        "test_s8b_oracle_driver.py::"
        "test_tampered_freeze_fails_source_verification"
    )
    local_only_item = SuffixedItem(local_only_node)
    assert (
        suite_conftest._strip_real_repo_loadgroup_suffix(local_only_item) is False
    )
    assert local_only_item.nodeid == (
        f"orchestrator/tests/{local_only_node}@real-repo"
    )


def test_real_repo_group_collection_exactly_matches_canonical_nodes():
    """全 group marker と real-repo node 集合を独立 golden で監査する。"""
    _require_pytest()
    report = _collect_xdist_group_report(HERE, cwd=ROOT)
    _assert_xdist_group_contract(report, _XDIST_GROUP_NAMES_GOLDEN)

    suite_conftest = _load_suite_conftest()
    golden = set(_REAL_REPO_CLASSIFIED_NODES_GOLDEN)
    golden_access = _real_repo_access_golden()
    resource_golden = set(golden_access)
    configured_access = {
        node_id: (access.parent, access.ccbench)
        for node_id, access in suite_conftest.REAL_REPO_ACCESS_BY_NODE.items()
    }
    assert configured_access == golden_access, (
        "conftest.REAL_REPO_ACCESS_BY_NODE が独立 golden と不一致: "
        f"missing={sorted(resource_golden - set(configured_access))} "
        f"extra={sorted(set(configured_access) - resource_golden)}"
    )
    assert set(suite_conftest.REAL_REPO_CLASSIFIED_NODES) == golden
    assert set(suite_conftest.REAL_REPO_RESOURCE_NODES) == resource_golden
    assert set(suite_conftest.REAL_REPO_LOCAL_ONLY_NODES) == set(
        _REAL_REPO_LOCAL_ONLY_NODES_GOLDEN
    )
    assert set(suite_conftest.REAL_REPO_CCBENCH_WRITER_NODES) == set(
        _REAL_REPO_CCBENCH_WRITER_NODES_GOLDEN
    )
    assert set(suite_conftest.REAL_REPO_PROCESS_MEMO_NODES) == set(
        _REAL_REPO_PROCESS_MEMO_NODES_GOLDEN
    )
    _assert_long_lived_fixture_group_contract(
        report, resource_golden, suite_conftest,
    )
    _assert_real_repo_suffix_strip_mutation_killer(suite_conftest)
    _assert_fixture_closure_complete(report, resource_golden)

    # 系統 1 / 3 の各 fan-out から 1 node を落とすと、正本 seed の閉包検査が赤になる。
    for removed in (
        "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control",
        "test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned",
    ):
        try:
            _assert_fixture_closure_complete(report, resource_golden - {removed})
        except AssertionError as exc:
            assert removed in str(exc), (
                f"欠落 control が意図した node を報告しなかった: {exc}"
            )
        else:
            raise AssertionError(f"共有 fixture consumer 欠落を検出しなかった: {removed}")

    # detector 自身の control: subprocess 側集約が最初の consumer だけを保存する
    # 退行を偽 report で注入し、per-item closure との相互検査が必ず赤になることを示す。
    consumers = _fixture_consumers_from_report(report)
    system1 = (
        "test_s1_measurement_freeze.py::"
        "test_recorded_ccbench_pin_hold_and_release_positive_control"
    )
    fanout_fixture = next(
        fixture for fixture, nodes in consumers.items()
        if system1 in nodes and len(nodes) > 1
    )
    fake_report = json.loads(json.dumps(report))
    declaration = next(
        entry["fixture_consumers"]
        for entry in fake_report if "fixture_consumers" in entry
    )
    declaration[fanout_fixture] = declaration[fanout_fixture][:1]
    try:
        _assert_fixture_closure_complete(fake_report, golden)
    except AssertionError as exc:
        assert "consumer 集約" in str(exc), (
            f"集約 detector control が意図した不変条件で赤にならなかった: {exc}"
        )
    else:
        raise AssertionError("最初の consumer しか保存しない偽 report を拒否しなかった")

    # detector 自身の control: 全 item の closure と集約を空へ壊した偽 report でも、
    # 既知 fixture の独立 control が必ず赤になることを示す。
    empty_report = json.loads(json.dumps(report))
    for entry in empty_report:
        entry["fixture_closure"] = []
        if "fixture_consumers" in entry:
            entry["fixture_consumers"] = {}
    try:
        _assert_fixture_closure_complete(empty_report, golden)
    except AssertionError as exc:
        assert "導出結果が空" in str(exc), (
            f"空 closure control が意図した不変条件で赤にならなかった: {exc}"
        )
    else:
        raise AssertionError("全 item の空 closure 退行を拒否しなかった")

    nodeids = [entry["nodeid"] for entry in report]
    assert len(nodeids) == len(set(nodeids)), (
        "collection report の item.nodeid が重複している"
    )

    exact_mark = [{"args": ["real-repo"], "kwargs": {}}]
    collected_counts = Counter()
    marked_counts = Counter()
    for entry in report:
        nodeid = entry["nodeid"]
        canonical = entry["canonical_node"]
        marks = entry["marks"]
        access = entry["real_repo_access"]
        collected_counts[canonical] += 1
        group_name = marks[0]["args"][0] if marks else None
        if canonical in resource_golden:
            expected_parent, expected_ccbench = golden_access[canonical]
            assert access == {
                "parent": expected_parent,
                "ccbench": expected_ccbench,
            }, (
                f"{nodeid} の runtime access vector が正本と不一致: {access!r}"
            )
            assert marks == exact_mark, (
                f"{nodeid} の shard marker は real-repo 1 個でなければならない: "
                f"{marks!r}"
            )
            marked_counts[canonical] += 1
        elif canonical in _REAL_REPO_LOCAL_ONLY_NODES_GOLDEN:
            assert access is None
            assert marks == [], (
                f"local-only node に real-repo marker がある: {nodeid} {marks!r}"
            )
        else:
            assert access is None, (
                f"golden 外 instance {nodeid} に access vector がある: {access!r}"
            )
            assert group_name != "real-repo", (
                f"golden 外 instance {nodeid} に real-repo marker がある: "
                f"{marks!r}"
            )

    for canonical in sorted(golden):
        assert collected_counts[canonical] > 0, (
            f"golden node が収集されなかった: {canonical}"
        )
        expected_marked = (
            collected_counts[canonical] if canonical in resource_golden else 0
        )
        assert marked_counts[canonical] == expected_marked, (
            f"{canonical} の marker instance 数が不一致: "
            f"collected={collected_counts[canonical]} "
            f"marked={marked_counts[canonical]} expected={expected_marked}"
        )
    _assert_real_repo_suffix_contract(report)


def test_shard_assignment_preserves_live_xdist_group_components_and_split_control():
    """実 collection marker から作る shard 閉包と、意図的 split の殺傷点。"""
    _require_pytest()
    from tools import acceptance_shards

    report = _collect_xdist_group_report(HERE, cwd=ROOT)
    records = []
    for entry in report:
        marks = entry["marks"]
        group = marks[0]["args"][0] if marks else None
        nodeid = entry["nodeid"]
        filename = nodeid.partition("::")[0]
        records.append(acceptance_shards.ItemRecord(nodeid, filename, group))
    records = tuple(sorted(records))
    assignment = acceptance_shards.allocate(records, 3)
    assert acceptance_shards.assignment_closure_gate(records, assignment.selected)
    expected_conflict_component = {
        "campaign-repository-scan",
        "real-repo",
        "s8c-predicate-snapshot",
        "s8c-preregistration-candidate",
    }
    matching_components = [
        component for component in assignment.components
        if set(component["groups"]) == expected_conflict_component
    ]
    assert len(matching_components) == 1, (
        "conflicting runtime groups が同一 shard component に union されていない: "
        f"components={assignment.components!r}"
    )

    suite_conftest = _load_suite_conftest()
    state_records = [
        {
            "nodeid": entry["nodeid"].removesuffix("@real-repo"),
            "file": entry["nodeid"].partition("::")[0],
            "group": entry["marks"][0]["args"][0] if entry["marks"] else None,
        }
        for entry in report
    ]
    valid_config = SimpleNamespace(
        _izanagi_acceptance_shard_spec=object(),
        _izanagi_acceptance_shard_state={"records": state_records},
    )
    suite_conftest._validate_real_repo_shard_state(valid_config)
    try:
        suite_conftest._validate_real_repo_shard_state(SimpleNamespace(
            _izanagi_acceptance_shard_spec=object(),
        ))
    except suite_conftest.pytest.UsageError as exc:
        assert "state" in str(exc)
    else:
        raise AssertionError("missing shard state was accepted")
    corrupted = json.loads(json.dumps(state_records))
    target = next(
        record for record in corrupted
        if suite_conftest._receipt_memo_node_id_from_nodeid(record["nodeid"])
        in suite_conftest.REAL_REPO_RESOURCE_NODES
    )
    target["group"] = None
    try:
        suite_conftest._validate_real_repo_shard_state(SimpleNamespace(
            _izanagi_acceptance_shard_spec=object(),
            _izanagi_acceptance_shard_state={"records": corrupted},
        ))
    except suite_conftest.pytest.UsageError as exc:
        assert "marker 閉包" in str(exc)
    else:
        raise AssertionError("corrupted real-repo marker record was accepted")

    real_repo_nodes = [
        record.nodeid for record in records if record.group == "real-repo"
    ]
    assert len(real_repo_nodes) >= 2, "split positive control に必要な実 group が小さすぎる"
    split = [list(nodeids) for nodeids in assignment.selected]
    first = real_repo_nodes[0]
    source = next(index for index, nodeids in enumerate(split) if first in nodeids)
    destination = (source + 1) % len(split)
    split[source].remove(first)
    split[destination].append(first)
    assert not acceptance_shards.assignment_closure_gate(records, split), (
        "実 real-repo group を跨がせた positive control が拒否されなかった"
    )


def test_xdist_group_audit_rejects_synthetic_negative_controls():
    """kwargs・二重 marker の shape 負例が監査を必ず赤にする。"""
    _require_pytest()
    with tempfile.TemporaryDirectory(prefix="izanagi-xdist-mark-negative-") as raw_tmp:
        tmp = Path(raw_tmp)
        suite = tmp / "test_synthetic_xdist_groups.py"
        suite.write_text(
            textwrap.dedent(
                """
                import pytest

                @pytest.mark.xdist_group("real-repo", name="real_repo")
                def test_kwargs_name():
                    pass

                @pytest.mark.xdist_group("real-repo")
                @pytest.mark.xdist_group("real-repo")
                def test_duplicate_markers():
                    pass
                """
            ),
            encoding="utf-8",
        )
        report = _collect_xdist_group_report(suite, cwd=tmp)

    entries = {entry["canonical_node"]: entry for entry in report}
    controls = (
        (
            ("test_synthetic_xdist_groups.py::test_kwargs_name",),
            {"real-repo"},
            "positional 引数 1 個",
        ),
        (
            ("test_synthetic_xdist_groups.py::test_duplicate_markers",),
            {"real-repo"},
            "最大 1 個",
        ),
    )
    for canonicals, expected_names, expected_error in controls:
        try:
            _assert_xdist_group_contract(
                [entries[canonical] for canonical in canonicals], expected_names,
            )
        except AssertionError as exc:
            assert expected_error in str(exc), (
                f"{canonicals!r} が意図した不変条件で拒否されなかった: {exc}"
            )
        else:
            raise AssertionError(f"合成負例が監査を通過した: {canonicals!r}")


def test_xdist_group_name_set_audit_rejects_isolated_negative_controls():
    """集合だけが不正な underscore・missing-only・extra-only を拒否する。"""
    _require_pytest()
    with tempfile.TemporaryDirectory(prefix="izanagi-xdist-name-negative-") as raw_tmp:
        tmp = Path(raw_tmp)
        suite = tmp / "test_synthetic_xdist_group_names.py"
        suite.write_text(
            textwrap.dedent(
                """
                import pytest

                @pytest.mark.xdist_group("real_repo")
                def test_underscore_name():
                    pass

                @pytest.mark.xdist_group("real-repo")
                def test_missing_only_actual():
                    pass

                @pytest.mark.xdist_group("real-repo")
                def test_extra_only_expected():
                    pass

                @pytest.mark.xdist_group("unexpected-group")
                def test_extra_only_unexpected():
                    pass
                """
            ),
            encoding="utf-8",
        )
        report = _collect_xdist_group_report(suite, cwd=tmp)

    entries = {entry["canonical_node"]: entry for entry in report}
    for entry in entries.values():
        assert len(entry["marks"]) == 1, entry
        mark = entry["marks"][0]
        assert (
            len(mark["args"]) == 1
            and isinstance(mark["args"][0], str)
            and mark["kwargs"] == {}
        ), f"集合負例が marker shape まで壊している: {entry!r}"

    controls = (
        (
            ("test_synthetic_xdist_group_names.py::test_underscore_name",),
            {"real-repo"},
            "missing=['real-repo'] extra=['real_repo']",
        ),
        (
            ("test_synthetic_xdist_group_names.py::test_missing_only_actual",),
            {"missing-group", "real-repo"},
            "missing=['missing-group'] extra=[]",
        ),
        (
            (
                "test_synthetic_xdist_group_names.py::test_extra_only_expected",
                "test_synthetic_xdist_group_names.py::test_extra_only_unexpected",
            ),
            {"real-repo"},
            "missing=[] extra=['unexpected-group']",
        ),
    )
    for canonicals, expected_names, expected_error in controls:
        try:
            _assert_xdist_group_contract(
                [entries[canonical] for canonical in canonicals], expected_names,
            )
        except AssertionError as exc:
            assert expected_error in str(exc), (
                f"{canonicals!r} が集合 assertion だけで拒否されなかった: {exc}"
            )
        else:
            raise AssertionError(f"集合の合成負例が監査を通過した: {canonicals!r}")


def test_canonical_real_repo_nodes_have_no_handwritten_xdist_group_decorator():
    """canonical node の real-repo marker は conftest hook だけが付与する。"""
    configured = set(_load_suite_conftest().REAL_REPO_RESOURCE_NODES)
    filenames = {canonical.partition("::")[0] for canonical in configured}
    sources = {
        filename: (HERE / filename).read_text(encoding="utf-8")
        for filename in filenames
    }
    _assert_no_direct_xdist_group_decorators(configured, sources)


def test_handwritten_xdist_group_decorator_control_is_rejected():
    """canonical node への手書き decorator を AST 監査が実際に拒否する。"""
    canonical = "test_synthetic_canonical.py::test_canonical"
    source = textwrap.dedent(
        """
        import pytest

        @pytest.mark.xdist_group("real-repo")
        def test_canonical():
            pass
        """
    )
    try:
        _assert_no_direct_xdist_group_decorators(
            {canonical}, {"test_synthetic_canonical.py": source},
        )
    except AssertionError as exc:
        assert "手書き decorator を許さない" in str(exc), exc
    else:
        raise AssertionError("手書き xdist_group decorator の合成負例が監査を通過した")


def test_real_repo_priority_order_is_literal_and_writers_follow_barrier(
        tmp_path, monkeypatch):
    """Historical name: RW overlap, exclusion, deadlines, and P→S are pinned."""
    suite_conftest = _load_suite_conftest()
    monkeypatch.setattr(suite_conftest, "_REAL_REPO_LOCK_DIRECTORY", tmp_path)

    repo_link = tmp_path / "repo-link"
    repo_link.symlink_to(ROOT, target_is_directory=True)
    for resource in ("parent", "ccbench"):
        direct = suite_conftest._real_repo_lock_path(resource, repo_root=ROOT)
        linked = suite_conftest._real_repo_lock_path(resource, repo_root=repo_link)
        assert direct.name == linked.name
        assert "session" not in direct.name
    path_probe = textwrap.dedent(
        """
        from orchestrator.tests import conftest
        print(conftest._real_repo_lock_path("parent"))
        print(conftest._real_repo_lock_path("ccbench"))
        """
    )
    probe_cwds = (tmp_path / "session-a", tmp_path / "session-b")
    for probe_cwd in probe_cwds:
        probe_cwd.mkdir()
    probe_outputs = []
    for index, probe_cwd in enumerate(probe_cwds):
        pythonpath = os.pathsep.join(
            part for part in (str(ROOT), os.environ.get("PYTHONPATH", ""))
            if part
        )
        probe_outputs.append(_run_subprocess(
            [sys.executable, "-c", path_probe],
            cwd=probe_cwd,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": pythonpath,
                "PYTEST_XDIST_TESTRUNUID": f"independent-session-{index}",
            },
        ).stdout.splitlines())
    assert probe_outputs[0] == probe_outputs[1]
    assert len(probe_outputs[0]) == 2

    readers_entered = []
    readers_guard = threading.Lock()
    both_readers = threading.Event()
    release_readers = threading.Event()
    writer_attempting = threading.Event()
    writer_entered = threading.Event()
    failures = []

    def reader() -> None:
        try:
            with suite_conftest._real_repo_locks(
                    suite_conftest.RealRepoAccess("read", "read")):
                with readers_guard:
                    readers_entered.append(threading.get_ident())
                    if len(readers_entered) == 2:
                        both_readers.set()
                assert release_readers.wait(5)
        except BaseException as exc:  # surface thread failures in the parent test
            failures.append(exc)

    def writer() -> None:
        try:
            writer_attempting.set()
            with suite_conftest._real_repo_locks(
                    suite_conftest.RealRepoAccess("write", "write")):
                writer_entered.set()
        except BaseException as exc:
            failures.append(exc)

    reader_threads = [threading.Thread(target=reader) for _ in range(2)]
    for thread in reader_threads:
        thread.start()
    assert both_readers.wait(5), "two LOCK_SH holders did not overlap"
    writer_thread = threading.Thread(target=writer)
    writer_thread.start()
    assert writer_attempting.wait(5)
    time.sleep(0.05)
    assert not writer_entered.is_set(), "LOCK_EX overlapped active LOCK_SH holders"
    release_readers.set()
    for thread in (*reader_threads, writer_thread):
        thread.join(5)
        assert not thread.is_alive()
    assert not failures
    assert writer_entered.is_set()

    # Forty-eight staggered SH cohorts keep S continuously occupied for 147
    # simulated seconds.  The production deadline must allow the writer to
    # acquire after the last cohort instead of retaining the old 120 s cutoff.
    cohort_windows = tuple(
        (float(index * 3), float(index * 3 + 6))
        for index in range(48)
    )
    assert all(
        right[0] <= left[1]
        for left, right in zip(cohort_windows, cohort_windows[1:])
    )
    simulated_clock = {"now": 0.0}
    writer_acquired_at = []

    def simulated_monotonic():
        return simulated_clock["now"]

    def simulated_sleep(delay):
        simulated_clock["now"] += delay

    def simulated_flock(_fd, operation):
        if operation == suite_conftest.fcntl.LOCK_UN:
            return
        assert operation == (
            suite_conftest.fcntl.LOCK_EX | suite_conftest.fcntl.LOCK_NB
        )
        active_cohorts = [
            index for index, (start, end) in enumerate(cohort_windows)
            if start <= simulated_clock["now"] < end
        ]
        if active_cohorts:
            raise BlockingIOError(
                suite_conftest.errno.EAGAIN,
                f"reader cohorts active: {active_cohorts!r}",
            )
        writer_acquired_at.append(simulated_clock["now"])

    with mock.patch.object(
            suite_conftest, "_real_repo_legacy_lock_path",
            return_value=tmp_path / "simulated-ccbench-legacy.lock",
            ), mock.patch.object(
                suite_conftest, "_real_repo_lock_path",
                return_value=tmp_path / "simulated-ccbench-common.lock",
            ), mock.patch.object(
                suite_conftest, "_open_real_repo_lock", side_effect=(91, 92),
            ), mock.patch.object(
                suite_conftest.fcntl, "flock", side_effect=simulated_flock,
            ), mock.patch.object(
                suite_conftest.time, "monotonic", side_effect=simulated_monotonic,
            ), mock.patch.object(
                suite_conftest.time, "sleep", side_effect=simulated_sleep,
            ), mock.patch.object(suite_conftest.os, "close"):
        with suite_conftest._real_repo_file_lock(
                "ccbench", "write", retry_interval_s=1.0):
            assert writer_acquired_at == [147.0, 147.0]
    assert 120.0 < writer_acquired_at[0] < (
        suite_conftest._REAL_REPO_LOCK_TIMEOUT_S
    )

    trace = []

    @contextlib.contextmanager
    def traced_lock(resource, mode):
        trace.append(("enter", resource, mode))
        try:
            yield
        finally:
            trace.append(("exit", resource, mode))

    with mock.patch.object(suite_conftest, "_real_repo_file_lock", traced_lock):
        with suite_conftest._real_repo_locks(
                suite_conftest.RealRepoAccess("read", "write")):
            trace.append(("body", None, None))
    assert trace == [
        ("enter", "parent", "read"),
        ("enter", "ccbench", "write"),
        ("body", None, None),
        ("exit", "ccbench", "write"),
        ("exit", "parent", "read"),
    ]

    from orchestrator.campaign import patchharness
    protocol_trace = []

    @contextlib.contextmanager
    def protocol_locks(access):
        protocol_trace.append(("locks-enter", access))
        try:
            yield
        finally:
            protocol_trace.append(("locks-exit", access))

    @contextlib.contextmanager
    def protocol_stamp(node_id, access):
        protocol_trace.append(("stamp-enter", node_id, access))
        try:
            yield
        finally:
            protocol_trace.append(("stamp-exit", node_id, access))

    protocol_node = next(iter(suite_conftest.REAL_REPO_CCBENCH_WRITER_NODES))
    filename, function = protocol_node.split("::", 1)
    protocol_access = suite_conftest.REAL_REPO_ACCESS_BY_NODE[protocol_node]
    protocol_item = SimpleNamespace(
        path=HERE / filename,
        name=function,
        originalname=function,
    )
    setattr(protocol_item, suite_conftest._REAL_REPO_ACCESS_ATTR, protocol_access)
    with mock.patch.object(
            suite_conftest, "_real_repo_locks", protocol_locks,
            ), mock.patch.object(
                patchharness, "_pytest_node_context", protocol_stamp,
            ):
        wrapper = suite_conftest.pytest_runtest_protocol(protocol_item, None)
        assert next(wrapper) is None
        protocol_trace.append(("protocol-body", protocol_node, protocol_access))
        try:
            next(wrapper)
        except StopIteration:
            pass
        else:
            raise AssertionError("pytest_runtest_protocol wrapper did not finish")
    assert protocol_trace == [
        ("locks-enter", protocol_access),
        ("stamp-enter", protocol_node, protocol_access),
        ("protocol-body", protocol_node, protocol_access),
        ("stamp-exit", protocol_node, protocol_access),
        ("locks-exit", protocol_access),
    ]

    negative_trace = []

    @contextlib.contextmanager
    def forbidden_protocol_locks(access):
        negative_trace.append(("locks", access))
        yield

    @contextlib.contextmanager
    def forbidden_protocol_stamp(node_id, access):
        negative_trace.append(("stamp", node_id, access))
        yield

    missing_stamp = object()
    wrong_access = suite_conftest.RealRepoAccess(None, "read")
    for stamped_access in (missing_stamp, wrong_access):
        invalid_item = SimpleNamespace(
            nodeid=f"orchestrator/tests/{protocol_node}@real-repo",
            path=HERE / filename,
            name=f"{function}@real-repo",
            originalname=None,
        )
        if stamped_access is not missing_stamp:
            setattr(
                invalid_item, suite_conftest._REAL_REPO_ACCESS_ATTR,
                stamped_access,
            )
        with mock.patch.object(
                suite_conftest, "_real_repo_locks", forbidden_protocol_locks,
                ), mock.patch.object(
                    patchharness, "_pytest_node_context",
                    forbidden_protocol_stamp,
                ):
            wrapper = suite_conftest.pytest_runtest_protocol(invalid_item, None)
            with suite_conftest.pytest.raises(
                    suite_conftest.pytest.UsageError,
                    match="resource access stamp mismatch; fails-closed",
                    ):
                next(wrapper)
    assert negative_trace == [], (
        "missing/mismatched resource stamps reached an unlocked protocol body"
    )

    legacy_path = suite_conftest._real_repo_legacy_lock_path("parent")
    holder_script = textwrap.dedent(
        """
        import fcntl
        import os
        import sys

        fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            print("ready", flush=True)
            sys.stdin.buffer.read(1)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        """
    )
    holder = subprocess.Popen(
        [sys.executable, "-c", holder_script, os.fspath(legacy_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert holder.stdout is not None and holder.stdin is not None
    resolver_events = []
    original_common_dir = suite_conftest._real_repo_common_dir

    def recording_common_dir(resource, *, repo_root=None):
        resolver_events.append(("resolver", resource))
        return original_common_dir(resource, repo_root=repo_root)

    try:
        assert holder.stdout.readline() == b"ready\n"
        with mock.patch.object(
                suite_conftest, "_real_repo_common_dir", recording_common_dir):
            with suite_conftest.pytest.raises(RuntimeError) as excinfo:
                with suite_conftest._real_repo_file_lock(
                        "parent", "read", timeout_s=0.01,
                        retry_interval_s=0.001):
                    raise AssertionError("contended lock must not be acquired")
        assert resolver_events == [], (
            "legacy EX holder 中に common-dir resolver が呼ばれた"
        )
    finally:
        holder.stdin.write(b"x")
        holder.stdin.close()
        holder.wait(timeout=5)
        if holder.returncode != 0:
            assert holder.stderr is not None
            raise AssertionError(holder.stderr.read().decode("utf-8", "replace"))
    message = str(excinfo.value)
    assert "fails-closed" in message
    assert "resource=parent" in message
    assert "mode=read" in message
    assert "holders=" in message

    with mock.patch.object(
            suite_conftest, "_real_repo_common_dir", recording_common_dir):
        with suite_conftest._real_repo_file_lock(
                "parent", "read", timeout_s=1.0,
                retry_interval_s=0.001):
            resolver_events.append(("body", "parent"))
    assert resolver_events == [
        ("resolver", "parent"),
        ("body", "parent"),
    ], "legacy lock release 後の resolver/body 呼出し順が不正"

    with suite_conftest.pytest.raises(ValueError):
        with suite_conftest._real_repo_file_lock("ccbench", "write"):
            raise ValueError("release control")
    with suite_conftest._real_repo_file_lock("ccbench", "write"):
        pass


def test_protocol_builder_repo_tree_guard_is_wired_to_real_root():
    """SUT が repo-tree helper を実 ROOT に結線していることを実行時に監査する。"""
    _require_pytest()
    from orchestrator.tests import repo_tree_util
    from orchestrator.tests import test_s8b_protocol_builder as sut

    helper_calls = []
    builder_actions = []
    writer_actions = []
    state = {"in_guard_action": False, "action": None}
    original_guard = repo_tree_util.assert_repo_tree_unchanged
    original_builder = sut._build_golden
    original_writer = sut.fc.write_protocol_document

    def recording_wrapper(root, action):
        helper_calls.append((root, action))

        def guarded_action():
            assert not state["in_guard_action"], "repo-tree guard action が入れ子になった"
            state["in_guard_action"] = True
            state["action"] = action
            try:
                return action()
            finally:
                state["action"] = None
                state["in_guard_action"] = False

        return original_guard(root, guarded_action)

    def recording_builder(*args, **kwargs):
        assert state["in_guard_action"], (
            "_build_golden が repo-tree guard action 外で実行された"
        )
        builder_actions.append(state["action"])
        return original_builder(*args, **kwargs)

    def recording_writer(*args, **kwargs):
        assert state["in_guard_action"], (
            "write_protocol_document が repo-tree guard action 外で実行された"
        )
        writer_actions.append(state["action"])
        return original_writer(*args, **kwargs)

    with tempfile.TemporaryDirectory(prefix="izanagi-guard-wiring-") as raw_tmp:
        with mock.patch.object(
                repo_tree_util, "assert_repo_tree_unchanged", recording_wrapper,
        ), mock.patch.object(
                sut, "_build_golden", side_effect=recording_builder,
        ), mock.patch.object(
                sut.fc, "write_protocol_document", side_effect=recording_writer,
        ):
            sut.test_build_and_write_leave_repo_tree_unchanged(
                Path(raw_tmp), Path("protocol.json"),
            )

    assert len(helper_calls) == 1, (
        "protocol builder SUT の repo-tree helper 呼出しは厳密に 1 回でなければならない: "
        f"actual={len(helper_calls)}"
    )
    assert helper_calls[0][0] == ROOT == sut.ROOT, (
        "repo-tree helper の第一引数が実 repo ROOT でない: "
        f"actual={helper_calls[0][0]!r} expected={ROOT!r}"
    )
    guarded_action = helper_calls[0][1]
    assert builder_actions == [guarded_action], (
        "_build_golden は同一 guard action 内で厳密に 1 回実行されなければならない: "
        f"actual={builder_actions!r}"
    )
    assert len(writer_actions) == 2, (
        "write_protocol_document は guard action 内で厳密に 2 回でなければならない: "
        f"actual={len(writer_actions)}"
    )
    assert all(action is guarded_action for action in writer_actions), (
        "2 回の write_protocol_document が同一 guard action 内で実行されていない"
    )


def test_ratified_memo_has_a_real_resolution_payer():
    """direct payer と実 memo consumer がすべて恒久保留へ閉じている。

    `real_repo_ratified_memo` は実 repo の `load_ratified_freeze` (git 39 本・4.4 秒) を
    process 内 1 回へ畳む。D335 後も、明示 opt-in 時の direct payer は memo を使わず、
    実 memo consumer と合わせて保留集合の外へ漏れないことを固定する。
    """
    _require_pytest()
    from orchestrator.tests import test_s8b_binding_driftguards as driftguard_tests
    from orchestrator.tests import test_s8b_oracle_driver as driver_tests
    from orchestrator.tests.growth_test_holds import GROWTH_TEST_HOLDS

    payer = driver_tests.test_nonnull_floor_without_active_generation_is_refused
    payer_node = f"test_s8b_oracle_driver.py::{payer.__name__}"
    assert payer_node in GROWTH_TEST_HOLDS, (
        f"direct payer が恒久保留集合の外にある: {payer_node}"
    )
    payer_source = inspect.getsource(inspect.unwrap(payer))
    for token in ("ratified_memo", "patch_ratified_loader"):
        assert token not in payer_source, (
            f"正本 payer {payer.__name__} が active 世代 memo を使っている: {token}"
        )
    assert "root=ROOT" in payer_source, (
        f"正本 payer {payer.__name__} が実 repo root を渡していない"
    )

    memo_consumers = (
        driver_tests.test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing,
        driver_tests.test_active_resolution_and_manifest_structure_refusals_are_aggregated,
        driftguard_tests.test_run_block_broken_binding_manifest_refuses_and_writes_nothing,
        driftguard_tests.test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal,
    )
    memo_nodes = {
        f"{Path(inspect.getsourcefile(inspect.unwrap(function))).name}::{function.__name__}"
        for function in memo_consumers
    }
    assert memo_nodes == {
        "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
        "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
        "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
        "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    }
    assert memo_nodes <= set(GROWTH_TEST_HOLDS), (
        "実 memo consumer が恒久保留集合の外にある: "
        f"missing={sorted(memo_nodes - set(GROWTH_TEST_HOLDS))!r}"
    )
    for function in memo_consumers:
        assert "patch_ratified_loader" in inspect.getsource(inspect.unwrap(function)), (
            f"memo consumer {function.__name__} が memo を使っていない (配線の取り残し)"
        )


def _qualified_call_name(call: ast.Call) -> str | None:
    target = call.func
    if isinstance(target, ast.Name):
        return target.id
    if (
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
    ):
        return f"{target.value.id}.{target.attr}"
    return None


def _receipt_consumers_from_source(path: Path) -> tuple[set[str], set[str], int]:
    """source から memo consumer、opt-out、parametrize 後 node 数を独立導出する。"""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    consumers: set[str] = set()
    optouts: set[str] = set()
    node_counts: dict[str, int] = {}
    for function in tree.body:
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not function.name.startswith("test_"):
            continue
        calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
        run_calls = [call for call in calls if _qualified_call_name(call) == "_run"]
        has_optout = any(
            any(
                keyword.arg == "memo_receipt"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False
                for keyword in call.keywords
            )
            for call in run_calls
        )
        direct = any(
            _qualified_call_name(call) in {
                "receipt_memo.patch_driver_resolver",
                "receipt_memo.real_repo_receipt",
            }
            for call in calls
        )
        canonical = f"{path.name}::{function.name}"
        if has_optout:
            optouts.add(canonical)
        elif run_calls or direct:
            consumers.add(canonical)

        count = 1
        for decorator in function.decorator_list:
            if not (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "parametrize"
                and len(decorator.args) >= 2
                and isinstance(decorator.args[1], (ast.List, ast.Tuple))
            ):
                continue
            count *= len(decorator.args[1].elts)
        node_counts[canonical] = count
    return consumers, optouts, sum(node_counts[node] for node in consumers)


def _assert_receipt_inventory(configured, consumers, optouts, node_count) -> None:
    assert set(configured) == set(_RECEIPT_MEMO_CONSUMERS_GOLDEN)
    assert set(consumers) == set(_RECEIPT_MEMO_CONSUMERS_GOLDEN)
    assert set(optouts) == set(_RECEIPT_MEMO_OPTOUT_GOLDEN)
    assert len(consumers) == 34
    assert node_count == 37
    assert not set(consumers) & set(optouts)


def test_receipt_memo_consumer_inventory_and_optouts_are_complete():
    suite_conftest = _load_suite_conftest()
    driver_consumers, driver_optouts, driver_nodes = _receipt_consumers_from_source(
        HERE / "test_s8b_oracle_driver.py"
    )
    drift_consumers, drift_optouts, drift_nodes = _receipt_consumers_from_source(
        HERE / "test_s8b_binding_driftguards.py"
    )
    consumers = driver_consumers | drift_consumers
    optouts = driver_optouts | drift_optouts
    _assert_receipt_inventory(
        suite_conftest.RECEIPT_MEMO_CONSUMER_NODES,
        consumers,
        optouts,
        driver_nodes + drift_nodes,
    )

    # 合成負例: 代表 consumer の欠落と opt-out 混入を同じ exact 検査が拒否する。
    representative = next(iter(sorted(_RECEIPT_MEMO_CONSUMERS_GOLDEN)))
    mutated = (set(consumers) - {representative}) | {
        next(iter(sorted(_RECEIPT_MEMO_OPTOUT_GOLDEN)))
    }
    try:
        _assert_receipt_inventory(mutated, consumers, optouts, 35)
    except AssertionError:
        pass
    else:
        raise AssertionError("receipt consumer inventory の合成負例が通過した")


_ORACLE_ENVIRONMENT_EXPLICIT_BINDING_NODE = (
    "test_sort_swo_oracle.py::"
    "test_real_patchharness_checkout_and_resolver_use_explicit_binding"
)


def _oracle_environment_consumers_from_source(path: Path):
    """Derive direct/compiled oracle consumers from the source AST."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    direct: set[str] = set()
    indirect: set[str] = set()
    node_counts: dict[str, int] = {}
    helper_getter_calls = 0
    for function in tree.body:
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if function.name == "_get_compiled_oracle_artifacts":
            helper_getter_calls = sum(
                1
                for call in ast.walk(function)
                if isinstance(call, ast.Call)
                and _qualified_call_name(call) == "_get_oracle_environment"
            )
            continue
        if not function.name.startswith("test_"):
            continue
        calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
        called_names = {
            _qualified_call_name(call)
            for call in calls
            if _qualified_call_name(call) is not None
        }
        canonical = f"{path.name}::{function.name}"
        if "_get_oracle_environment" in called_names:
            direct.add(canonical)
        if "_get_compiled_oracle_artifacts" in called_names:
            indirect.add(canonical)

        count = 1
        for decorator in function.decorator_list:
            if not (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "parametrize"
                and len(decorator.args) >= 2
                and isinstance(decorator.args[1], (ast.List, ast.Tuple))
            ):
                continue
            count *= len(decorator.args[1].elts)
        node_counts[canonical] = count
    consumers = direct | indirect
    return (
        direct,
        indirect,
        consumers,
        sum(node_counts[node] for node in consumers),
        helper_getter_calls,
    )


def _assert_oracle_environment_inventory(
    configured, direct, indirect, consumers, node_count, helper_getter_calls,
    *, golden=ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN,
) -> None:
    configured_for_exact = set(configured) - {
        _ORACLE_ENVIRONMENT_EXPLICIT_BINDING_NODE,
    }
    assert configured_for_exact == set(golden), (
        "oracle consumer registry (ORACLE_ENVIRONMENT_CONSUMER_NODES) と独立 golden が不一致: "
        f"missing={sorted(set(golden) - configured_for_exact)} "
        f"extra={sorted(configured_for_exact - set(golden))}"
    )
    assert set(consumers) == set(golden), (
        "sort_swo_oracle.py AST inventory と独立 golden が不一致: "
        f"missing={sorted(set(golden) - set(consumers))} "
        f"extra={sorted(set(consumers) - set(golden))}"
    )
    assert configured_for_exact == set(consumers), (
        "ORACLE_ENVIRONMENT_CONSUMER_NODES と source-derived AST inventory が不一致: "
        f"missing={sorted(set(consumers) - configured_for_exact)} "
        f"extra={sorted(configured_for_exact - set(consumers))}"
    )
    assert len(direct) == 17
    assert len(indirect) == 9
    assert len(consumers) == 26
    assert node_count == 29
    assert not set(direct) & set(indirect)
    assert helper_getter_calls == 1, (
        "compiled oracle helper が memo getter を厳密に 1 回呼ばない: "
        f"calls={helper_getter_calls}"
    )


def _assert_oracle_fixture_bindings_removed(path: Path, consumers) -> None:
    """The moved consumers must not retain either removed fixture contract."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    definitions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in {"oracle_environment", "compiled_oracle_artifacts"}
    }
    assert not definitions, f"legacy oracle fixture definition remains: {sorted(definitions)}"
    for function in tree.body:
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        canonical = f"{path.name}::{function.name}"
        if canonical not in consumers:
            continue
        arguments = {
            argument.arg
            for argument in (*function.args.posonlyargs, *function.args.args,
                             *function.args.kwonlyargs)
        }
        assert not arguments & {"oracle_environment", "compiled_oracle_artifacts"}, (
            f"{canonical}: legacy oracle fixture binding remains: "
            f"{sorted(arguments & {'oracle_environment', 'compiled_oracle_artifacts'})}"
        )


def test_oracle_environment_consumer_inventory_and_registry_are_complete():
    """The moved registry is independently exact and source-derived."""
    suite_conftest = _load_suite_conftest()
    direct, indirect, consumers, node_count, helper_getter_calls = _oracle_environment_consumers_from_source(
        HERE / "test_sort_swo_oracle.py"
    )
    _assert_oracle_environment_inventory(
        suite_conftest.ORACLE_ENVIRONMENT_CONSUMER_NODES,
        direct,
        indirect,
        consumers,
        node_count,
        helper_getter_calls,
    )
    _assert_oracle_fixture_bindings_removed(
        HERE / "test_sort_swo_oracle.py", consumers,
    )

    # Mutation-1 control: removing one registry entry is rejected by this
    # completeness contract, while the source inventory and golden remain intact.
    representative = next(iter(sorted(ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN)))
    try:
        _assert_oracle_environment_inventory(
            set(suite_conftest.ORACLE_ENVIRONMENT_CONSUMER_NODES) - {representative},
            direct,
            indirect,
            consumers,
            node_count,
            helper_getter_calls,
        )
    except AssertionError as exc:
        assert "registry" in str(exc), exc
    else:
        raise AssertionError("oracle consumer registry の欠落 control が通過した")

    # Mutation-2 control: a one-node registry/golden offset is rejected by
    # the exact-match assertion before the source-derived checks run.
    shifted = (set(ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN) - {representative}) | {
        "test_sort_swo_oracle.py::__synthetic_registry_shift__",
    }
    try:
        _assert_oracle_environment_inventory(
            shifted,
            direct,
            indirect,
            consumers,
            node_count,
            helper_getter_calls,
            golden=ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN,
        )
    except AssertionError as exc:
        assert "registry" in str(exc), exc
    else:
        raise AssertionError("oracle consumer registry/golden のずれ control が通過した")


def test_oracle_environment_explicit_binding_node_is_not_a_consumer():
    """The explicit checkout/resolver binding is a deliberate boundary node."""
    suite_conftest = _load_suite_conftest()
    direct, indirect, consumers, _node_count, _helper_getter_calls = _oracle_environment_consumers_from_source(
        HERE / "test_sort_swo_oracle.py"
    )
    configured = set(suite_conftest.ORACLE_ENVIRONMENT_CONSUMER_NODES)
    assert _ORACLE_ENVIRONMENT_EXPLICIT_BINDING_NODE not in configured, (
        "明示 binding node を oracle environment consumer registry に混入させている"
    )
    assert _ORACLE_ENVIRONMENT_EXPLICIT_BINDING_NODE not in consumers
    assert _ORACLE_ENVIRONMENT_EXPLICIT_BINDING_NODE not in direct
    assert _ORACLE_ENVIRONMENT_EXPLICIT_BINDING_NODE not in indirect


def test_real_repo_writers_do_not_materialize_oracle_environment_candidates(
        tmp_path, monkeypatch, ratified_enforcement_source,
):
    """Current real-repo writers stay away from every resolver candidate path.

    The slow floor canaries remain the authoritative compute-node execution of the
    complete build, but this audit also runs the production writer seams that can
    be exercised in a disposable checkout.  In particular, the FetchContent
    preparation path is run with a real subprocess (a tiny fixture cmake) rather
    than inferred only from test-source spelling.
    """
    suite_conftest = _load_suite_conftest()
    writer_nodes = {
        "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration",
        "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration",
        "test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2",
        _ORACLE_ENVIRONMENT_EXPLICIT_BINDING_NODE,
    }
    reader_control_nodes = {
        "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
        "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",
        "test_hooks.py::test_real_submodule_payload_edit",
    }
    assert writer_nodes == set(suite_conftest.REAL_REPO_CCBENCH_WRITER_NODES), (
        "実 ccbench writer の独立 golden と access map が不一致: "
        f"configured={sorted(suite_conftest.REAL_REPO_CCBENCH_WRITER_NODES)}"
    )
    assert all(
        suite_conftest.REAL_REPO_ACCESS_BY_NODE[node].ccbench != "write"
        for node in reader_control_nodes
    ), (
        "reader control を ccbench writer へ過剰分類している"
    )

    # Source-level guard: retain a cheap tripwire for new writer spellings, but
    # compare evaluated string constants.  Comparing ast.unparse() output is
    # brittle because its quote style is not part of the AST contract.
    writer_files = {
        node.split("::", 1)[0]
        for node in writer_nodes | reader_control_nodes
    }
    write_methods = {
        "mkdir", "mkdirs", "touch", "write_text", "write_bytes", "open",
        "replace", "rename", "copy", "copy2", "copytree", "move",
    }
    forbidden_environment_values = frozenset({
        "IZANAGI_SORT_SWO_CXX", "IZANAGI_SORT_SWO_MASSTREE_ROOT", "CXX", "g++",
    })
    for filename in sorted(writer_files):
        tree = ast.parse(
            (HERE / filename).read_text(encoding="utf-8"),
            filename=filename,
        )
        constants = _string_constants(tree)
        for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
            target = call.func
            method = target.attr if isinstance(target, ast.Attribute) else None
            if method not in write_methods:
                continue
            values = {
                node.value
                for node in ast.walk(call)
                if isinstance(node, ast.Constant) and type(node.value) is str
            }
            values.update(
                constants[node.id]
                for node in ast.walk(call)
                if isinstance(node, ast.Name) and node.id in constants
            )
            direct_build_dependency = {"build", "_deps", "masstree-src"} <= values
            direct_ancestor_cache = {"-thirdparty-cache", "masstree"} <= values
            environment_binding = bool(values & forbidden_environment_values)
            assert not (
                direct_build_dependency or direct_ancestor_cache or environment_binding
            ), (
                f"{filename}: writer が resolver candidate を直接 materialize している: "
                f"constants={sorted(values & (forbidden_environment_values | {'build', '_deps', 'masstree-src', '-thirdparty-cache', 'masstree'}))}"
            )

    # Use a disposable checkout-shaped tree for every executable probe.  Keep
    # the retired build/ancestor locations in the writer audit even though the
    # fail-closed resolver no longer inspects them.
    from orchestrator.campaign import sort_swo_oracle as oracle
    from orchestrator.campaign import site_policy

    probe_root = tmp_path / "writer-probe"
    ccbench = probe_root / "external" / "ccbench"
    ccbench.mkdir(parents=True)
    compiler = probe_root / "compiler-candidate"
    cxx = probe_root / "cxx-candidate"
    gxx = probe_root / "g++-candidate"
    dependency = probe_root / "environment-masstree"
    monkeypatch.setenv("IZANAGI_SORT_SWO_CXX", str(compiler))
    monkeypatch.setenv("CXX", str(cxx))
    monkeypatch.setenv("IZANAGI_SORT_SWO_MASSTREE_ROOT", str(dependency))
    real_which = shutil.which
    monkeypatch.setattr(
        oracle.shutil, "which",
        lambda name: str(gxx) if name == "g++" else real_which(name),
    )

    candidate_paths = [
        compiler,
        cxx,
        gxx,
        dependency,
        ccbench / "build" / "_deps" / "masstree-src",
    ]
    ancestor_candidates = [
        ancestor.parent / f"{ancestor.name}-thirdparty-cache" / "masstree"
        for ancestor in tuple(ccbench.parents)[:8]
    ]
    candidate_paths.extend(ancestor_candidates)
    candidate_paths = list(dict.fromkeys(candidate_paths))

    def candidate_state(path: Path):
        """Return a bounded, non-content-leaking identity of a candidate path."""
        try:
            info = path.lstat()
        except FileNotFoundError:
            return ("absent",)
        except OSError as exc:
            return ("unreadable", type(exc).__name__, getattr(exc, "errno", None))
        if stat.S_ISLNK(info.st_mode):
            try:
                target = os.readlink(path)
            except OSError as exc:
                return ("symlink-unreadable", type(exc).__name__, getattr(exc, "errno", None))
            return ("symlink", target, info.st_mtime_ns)
        if stat.S_ISDIR(info.st_mode):
            children = []
            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        child = entry.stat(follow_symlinks=False)
                        children.append((
                            entry.name, child.st_mode, child.st_size,
                            child.st_mtime_ns, child.st_ctime_ns,
                        ))
                        if len(children) > 512:
                            children = [("<over-512>",)]
                            break
            except OSError as exc:
                return ("directory-unreadable", type(exc).__name__, getattr(exc, "errno", None))
            return (
                "directory", info.st_mode, info.st_mtime_ns, info.st_ctime_ns,
                tuple(sorted(children)),
            )
        return (
            "file", info.st_mode, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns,
        )

    before = {path: candidate_state(path) for path in candidate_paths}

    # Execute the production writer seams behind the canonical real-repo nodes.
    # These calls deliberately write only under tmp_path; the slow compute-node
    # canaries are represented by the same buildcache FetchContent seam below.
    probed_nodes = set()

    from orchestrator.campaign import s8b_floor_campaign as floor_campaign
    raw_protocol = b"{}"
    built_protocol = floor_campaign.BuiltProtocol(
        {}, raw_protocol, hashlib.sha256(raw_protocol).hexdigest(),
    )
    floor_campaign.write_protocol_document(
        probe_root / "protocol-output" / "protocol.json",
        built_protocol, root=probe_root,
    )
    probed_nodes.add(
        "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged"
    )

    # The three loop nodes exercise their real drive/checkpoint/WAL writers;
    # their fixture proposals reject before any build or oracle subprocess.
    from orchestrator.tests import test_p3_s4_loop as backoff_loop_tests
    from orchestrator.tests import test_p3_s4_loop_sort as sort_loop_tests
    from orchestrator.tests import test_p3_s4_loop_trigger_gating as trigger_loop_tests
    backoff_loop_tests.test_drive_iteration_checkpoint_survives_across_calls(
        ratified_enforcement_source,
    )
    sort_loop_tests.test_drive_iteration_checkpoint_survives_across_calls()
    trigger_loop_tests.test_drive_iteration_writes_entry_and_checkpoint(monkeypatch)
    trigger_loop_tests.test_drive_iteration_entry_failure_blocks_checkpoint(monkeypatch)
    probed_nodes.update({
        "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
        "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",
    })

    # The hook node is a real guard decision against a disposable path.  It is
    # intentionally not mistaken for a production file writer.
    from orchestrator.tests import test_hooks as hook_tests
    hook_target = probe_root / "hook-probe" / "backoff.hh"
    hook_target.parent.mkdir(parents=True)
    hook_target.write_text("old\n", encoding="utf-8")
    allowed, _reason = hook_tests.GW.decide(
        "Edit",
        {
            "file_path": str(hook_target),
            "old_string": "old",
            "new_string": "new",
        },
        repo_root=str(probe_root),
    )
    assert isinstance(allowed, bool)
    probed_nodes.add("test_hooks.py::test_real_submodule_payload_edit")

    # Run the actual buildcache FetchContent writer with a subprocess fixture.
    # It creates the job-local base/masstree-src tree, which is distinct from
    # every resolver candidate and therefore catches accidental default-path use.
    from orchestrator.campaign import buildcache
    fake_cmake = probe_root / "fake-cmake"
    fake_cmake.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "if '-B' in args:\n"
        "    build = Path(args[args.index('-B') + 1])\n"
        "    build.mkdir(parents=True, exist_ok=True)\n"
        "for arg in args:\n"
        "    if arg.startswith('-DFETCHCONTENT_BASE_DIR='):\n"
        "        base = Path(arg.split('=', 1)[1])\n"
        "        (base / 'masstree-src').mkdir(parents=True, exist_ok=True)\n"
        "        break\n"
        "if '--build' in args:\n"
        "    build = Path(args[args.index('--build') + 1])\n"
        "    build.mkdir(parents=True, exist_ok=True)\n"
        "    (build / 'fake-target-built').write_text('ok\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    fake_cmake.chmod(0o755)
    tool_manifest = {
        role: {
            "requested": role,
            "realpath": str(fake_cmake),
            "version_first_line": f"fixture-{role}",
            "version": f"fixture-{role}",
        }
        for role in ("cc", "cxx", "cmake")
    }
    fetch_base = probe_root / "job-local-fetchcontent"
    fetch_base.mkdir()
    preparation = buildcache.prepare_masstree_fetchcontent(
        ccbench_dir=str(ccbench),
        fetchcontent_base_dir=str(fetch_base),
        expected_toolchain_manifest=tool_manifest,
        configure_timeout_s=30,
        target_timeout_s=30,
        site=site_policy.OTHER,
    )
    assert Path(preparation.fetchcontent_base_dir) == fetch_base.resolve()
    assert (fetch_base / "masstree-src").is_dir()

    # Exercise both production build-cache writers with their normal admission
    # and manifest machinery.  Only the external compiler/CMake process is a
    # fixture; buildcache itself performs the real cache-directory writes.
    from orchestrator.tests import test_buildcache_v2 as buildcache_tests
    buildcache_tests._install_toolchain(probe_root, monkeypatch)
    buildcache_tests._fake_build_environment(
        monkeypatch, probe_root, payload=b"writer-build",
    )
    genome = buildcache_tests.Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = buildcache_tests._admission_bundle(
        genome, "a" * 40, str(ccbench),
    )
    legacy = buildcache.build(
        genome, "a" * 40, False,
        cache_root=str(probe_root / "legacy-cache"),
        ccbench_dir=str(ccbench), cc="test-cc", cxx="test-cxx", jobs=1,
        admission=admission, build_context=context, source_evidence=evidence,
    )
    assert Path(legacy.binary).is_file()
    v2 = buildcache_tests._build(
        probe_root, buildcache_tests._contract(1), trace=False,
        ccbench_dir=str(ccbench),
    )
    assert Path(v2.binary).is_file()
    v2_fetch_base = probe_root / "v2-fetchcontent"
    v2_fetch_base.mkdir()
    v2_receipt = buildcache_tests._write_fetchcontent_dependency(v2_fetch_base)
    v2_fetch = buildcache_tests._build(
        probe_root, buildcache_tests._contract(1), trace=True,
        ccbench_dir=str(ccbench), fetchcontent_base_dir=str(v2_fetch_base),
        fetchcontent_dependency_receipt=v2_receipt,
    )
    assert Path(v2_fetch.binary).is_file()
    probed_nodes.update({
        "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration",
        "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration",
        "test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2",
    })

    # Exercise the production worktree writer on a synthetic git repository;
    # no real shared submodule is touched by this probe.
    from orchestrator.campaign import patchharness
    checkout_base = probe_root / "checkout-base"
    checkout_base.mkdir()
    subprocess.run(
        ["git", "init", "-q"], cwd=str(checkout_base), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    (checkout_base / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "tracked.txt"], cwd=str(checkout_base), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi fixture",
            "-c", "user.email=izanagi-fixture@example.invalid",
            "commit", "-qm", "fixture",
        ], cwd=str(checkout_base), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(checkout_base), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()
    with patchharness.checkout(head, base_dir=str(checkout_base)) as checked:
        assert Path(checked).is_dir()
    probed_nodes.add(
        "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding"
    )

    expected_probed_nodes = writer_nodes | reader_control_nodes
    assert probed_nodes == expected_probed_nodes, (
        "real-repo writer/reader control probe が不足: "
        f"missing={sorted(expected_probed_nodes - probed_nodes)} "
        f"extra={sorted(probed_nodes - expected_probed_nodes)}"
    )

    after_writers = {path: candidate_state(path) for path in candidate_paths}
    assert before == after_writers, (
        "production writer 実行後に resolver candidate path が変化した: "
        f"changed={sorted(str(path) for path in candidate_paths if before[path] != after_writers[path])}"
    )

    # Resolve only after all writer probes.  The resolver itself must also stay
    # read-only, so take a second post-resolution snapshot.
    resolution = oracle.resolve_oracle_environment(ccbench)
    assert type(resolution) is oracle.OracleEnvironmentResolutionFailure
    assert [item.origin for item in resolution.compiler_candidates] == [
        "environment:IZANAGI_SORT_SWO_CXX",
        "environment:CXX",
        "path:g++",
    ]
    assert [item.path for item in resolution.compiler_candidates] == [
        compiler, cxx, gxx,
    ]
    assert [item.origin for item in resolution.dependency_candidates] == [
        "environment:IZANAGI_SORT_SWO_MASSTREE_ROOT",
    ]
    assert [item.path for item in resolution.dependency_candidates] == [
        dependency,
    ]
    after_resolution = {path: candidate_state(path) for path in candidate_paths}
    assert after_writers == after_resolution, (
        "resolver が candidate path を materialize した: "
        f"changed={sorted(str(path) for path in candidate_paths if after_writers[path] != after_resolution[path])}"
    )
    assert before[compiler] == ("absent",)
    assert before[cxx] == ("absent",)
    assert before[gxx] == ("absent",)
    assert before[dependency] == ("absent",)
    assert before[ccbench / "build" / "_deps" / "masstree-src"] == ("absent",)


def test_oracle_environment_memo_roundtrip_and_getter_are_fail_closed(tmp_path):
    """The union wire schema is lossless and a getter miss never resolves."""
    from orchestrator.campaign import sort_swo_oracle as oracle
    from orchestrator.tests import sort_swo_oracle_receipt_memo as memo

    candidate = oracle.OracleEnvironmentCandidate(
        "environment:IZANAGI_SORT_SWO_CXX", Path(tmp_path / "cxx"), "missing",
    )
    failure = oracle.OracleEnvironmentResolutionFailure(
        "oracle-environment-compiler-unresolved",
        (candidate,),
        (oracle.OracleEnvironmentCandidate(
            "ccbench-build-dependency", None, "config-h-missing",
        ),),
    )
    success = oracle.OracleEnvironment(
        Path(tmp_path / "cxx"), Path(tmp_path / "ccbench"),
        Path(tmp_path / "masstree"),
    )
    for index, resolution in enumerate((success, failure)):
        assert memo._cache_resolution(memo._cache_document(resolution)) == resolution
        cache_path = tmp_path / f"oracle-resolution-{index}.json"
        memo._cache_store(cache_path, resolution)
        assert memo._cache_load(
            cache_path,
            run_id=f"roundtrip-{index}",
            head="b" * 40,
            prewarm=False,
            process_prewarmed=False,
        ) == resolution

    calls = []

    def forbidden_resolve():
        calls.append("resolver")
        raise AssertionError("consumer getter invoked the production resolver")

    with mock.patch.object(memo, "_repo_head", return_value="c" * 40), \
            mock.patch.object(memo.tempfile, "gettempdir", return_value=str(tmp_path)), \
            mock.patch.dict(
                os.environ,
                {
                    memo._RUN_ID_ENV: "oracle-roundtrip-run",
                    memo._SESSION_NONCE_ENV: "oracle-roundtrip-session",
                },
                clear=False,
            ):
        writer = memo._make_oracle_environment_memo(resolve=lambda: success)
        assert writer.prewarm(
            run_id="oracle-roundtrip-run",
            session_id="oracle-roundtrip-session",
        ) == success
        cache_reader = memo._make_oracle_environment_memo(
            resolve=forbidden_resolve,
        )
        assert cache_reader.get() == success
        assert cache_reader.process_prewarmed is False

    reader = memo._make_oracle_environment_memo(resolve=forbidden_resolve)
    with mock.patch.object(memo, "_repo_head", return_value="b" * 40), \
            mock.patch.object(memo.tempfile, "gettempdir", return_value=str(tmp_path)), \
            mock.patch.dict(
                os.environ,
                {
                    memo._RUN_ID_ENV: "oracle-fail-closed-run",
                    memo._SESSION_NONCE_ENV: "oracle-fail-closed-session",
                },
                clear=False,
            ):
        try:
            reader.get()
        except memo.OracleEnvironmentMemoError as exc:
            assert exc.payload["reason"] == "cache-missing"
        else:
            raise AssertionError("oracle getter miss was not fail-closed")
    assert calls == []


def test_oracle_environment_prewarm_hook_exception_is_not_fail_open():
    """A controller prewarm error remains visible and cleans memo state."""
    suite_conftest = _load_suite_conftest()
    consumer = next(iter(sorted(ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN)))
    config = _ReceiptHookConfig({"collectonly": False})
    setattr(
        config,
        suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
        "oracle-session-test",
    )
    prewarm_error = RuntimeError("oracle prewarm failed")
    fake_module = SimpleNamespace(
        prewarm_oracle_environment=mock.Mock(side_effect=prewarm_error),
        finish_oracle_environment_session=mock.Mock(),
    )
    try:
        with mock.patch.object(
            suite_conftest,
            "_oracle_environment_memo_module",
            return_value=fake_module,
        ):
            suite_conftest.pytest_collection_finish(SimpleNamespace(
                config=config, items=[_receipt_hook_item(consumer)],
            ))
    except RuntimeError as exc:
        assert exc is prewarm_error
    else:
        raise AssertionError("oracle prewarm exception was swallowed")
    assert not getattr(
        config, suite_conftest._ORACLE_ENVIRONMENT_MEMO_PREWARMED_ATTR, False,
    )
    fake_module.finish_oracle_environment_session.assert_called_once_with(
        session_id="oracle-session-test",
    )


def test_oracle_environment_memo_prewarm_wiring_is_controller_only_and_lazy():
    """Both collection barriers pay once, while workers and unrelated nodes do not."""
    suite_conftest = _load_suite_conftest()
    consumer = next(iter(sorted(ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN)))
    calls = []
    fake_module = SimpleNamespace(
        prewarm_oracle_environment=lambda **kwargs: calls.append(kwargs),
        finish_oracle_environment_session=mock.Mock(),
    )

    worker_config = _ReceiptHookConfig(
        {"collectonly": False, "testrunuid": "ci-job-42"}, worker=True,
    )
    setattr(
        worker_config,
        suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
        "oracle-session-test",
    )
    worker_config.workerinput[
        suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR
    ] = "oracle-session-test"
    worker_session = SimpleNamespace(
        config=worker_config, items=[_receipt_hook_item(consumer)],
    )
    controller_config = _ReceiptHookConfig(
        {"collectonly": False, "testrunuid": "ci-job-42"},
    )
    setattr(
        controller_config,
        suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
        "oracle-session-test",
    )
    controller_node = SimpleNamespace(
        config=controller_config,
        workerinput={"testrunuid": "ci-job-42"},
    )
    with mock.patch.object(
        suite_conftest, "_oracle_environment_memo_module", return_value=fake_module,
    ):
        suite_conftest.pytest_collection_finish(worker_session)
        assert calls == []
        suite_conftest.pytest_xdist_node_collection_finished(
            controller_node, [consumer + "@oracle-environment"],
        )
        suite_conftest.pytest_xdist_node_collection_finished(
            controller_node, [consumer + "@oracle-environment"],
        )
        suite_conftest._finish_oracle_environment_memo_session(controller_config)
    assert calls == [{
        "run_id": "ci-job-42", "session_id": "oracle-session-test",
    }]
    fake_module.finish_oracle_environment_session.assert_called_once_with(
        session_id="oracle-session-test",
    )
    assert not getattr(
        controller_config,
        suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ACTIVE_ATTR,
        False,
    )

    serial_calls = []
    serial_module = SimpleNamespace(
        prewarm_oracle_environment=lambda **kwargs: serial_calls.append(kwargs),
    )
    serial_config = _ReceiptHookConfig({"collectonly": False})
    setattr(
        serial_config,
        suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
        "oracle-session-serial",
    )
    with mock.patch.object(
        suite_conftest, "_oracle_environment_memo_module", return_value=serial_module,
    ):
        suite_conftest.pytest_collection_finish(SimpleNamespace(
            config=serial_config, items=[_receipt_hook_item(consumer)],
        ))
    assert serial_calls == [{
        "run_id": None, "session_id": "oracle-session-serial",
    }]

    unrelated_config = _ReceiptHookConfig({"collectonly": False})
    with mock.patch.object(
        suite_conftest,
        "_oracle_environment_memo_module",
        side_effect=AssertionError("unrelated selection imported oracle memo"),
    ) as lazy_import:
        suite_conftest.pytest_collection_finish(SimpleNamespace(
            config=unrelated_config,
            items=[_receipt_hook_item("test_example.py::test_unrelated")],
        ))
    assert lazy_import.call_count == 0


def test_oracle_environment_memo_nonce_is_propagated_to_workers_and_restored():
    """Controller and worker use one oracle session nonce without env leakage."""
    suite_conftest = _load_suite_conftest()
    with mock.patch.dict(
        os.environ,
        {suite_conftest._ORACLE_ENVIRONMENT_MEMO_NONCE_ENV: "outer-oracle-nonce"},
        clear=False,
    ):
        controller = _ReceiptHookConfig()
        worker = None
        suite_conftest._configure_oracle_environment_memo_session(controller)
        controller_nonce = getattr(
            controller, suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
        )
        assert isinstance(controller_nonce, str) and controller_nonce
        assert os.environ[suite_conftest._ORACLE_ENVIRONMENT_MEMO_NONCE_ENV] == controller_nonce
        try:
            node = SimpleNamespace(
                config=controller, workerinput={"testrunuid": "ci-job-42"},
            )
            suite_conftest.pytest_configure_node(node)
            assert node.workerinput[
                suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR
            ] == controller_nonce

            worker = SimpleNamespace(workerinput=dict(node.workerinput))
            suite_conftest._configure_oracle_environment_memo_session(worker)
            assert getattr(
                worker, suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
            ) == controller_nonce
            suite_conftest._restore_oracle_environment_memo_nonce(worker)
            assert os.environ[suite_conftest._ORACLE_ENVIRONMENT_MEMO_NONCE_ENV] == controller_nonce
        finally:
            if worker is not None:
                suite_conftest._restore_oracle_environment_memo_nonce(worker)
            suite_conftest._restore_oracle_environment_memo_nonce(controller)
        assert os.environ[suite_conftest._ORACLE_ENVIRONMENT_MEMO_NONCE_ENV] == "outer-oracle-nonce"


def _receipt_error(call, memo_module, expected_reason):
    try:
        call()
    except memo_module.ReceiptMemoError as exc:
        assert exc.payload["reason"] == expected_reason, exc.payload
        raw = str(exc).removeprefix(memo_module._ERROR_PREFIX)
        assert str(exc).startswith(memo_module._ERROR_PREFIX)
        assert raw == json.dumps(
            exc.payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
        )
        assert set((
            "reason", "cache_path", "run_id", "head", "prewarm",
            "process_prewarmed",
        )) <= set(exc.payload)
        return exc
    raise AssertionError(f"structured receipt error が無い: {expected_reason}")


def test_receipt_memo_l1_to_l5_are_fail_closed_and_uid_is_hashed():
    from orchestrator.tests import real_repo_receipt_memo as memo_module

    resolution = memo_module.migration.ReceiptResolution(
        "never-issued", (), None, "c" * 40,
    )
    calls = []

    def resolve():
        calls.append("resolve")
        return resolution

    serial = memo_module._make_receipt_memo(resolve=resolve)
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop(memo_module._RUN_ID_ENV, None)
        error = _receipt_error(
            serial.get, memo_module, "cache-path-unavailable",
        )
        assert error.payload["prewarm"] is False and calls == []
        assert serial.prewarm(run_id=None) is resolution
        assert serial.prewarm(run_id=None) is resolution
        assert serial.get() is resolution and calls == ["resolve"]

    head = "a" * 40
    run_id = "ci-job-42 / arbitrary UID"
    with tempfile.TemporaryDirectory(prefix="receipt-memo-test-") as raw_tmp, \
            mock.patch.object(memo_module, "_repo_head", return_value=head), \
            mock.patch.object(memo_module.tempfile, "gettempdir", return_value=raw_tmp):
        session_id = "session-l1"
        path = memo_module._cache_path_for(run_id, head, session_id)
        assert run_id not in path.name
        assert path == memo_module._cache_path_for(run_id, head, session_id)
        assert path != memo_module._cache_path_for(run_id + "x", head, session_id)
        assert path != memo_module._cache_path_for(run_id, head, "session-l2")
        with mock.patch.dict(
            os.environ,
            {
                memo_module._RUN_ID_ENV: "",
                memo_module._SESSION_NONCE_ENV: session_id,
            },
        ):
            assert memo_module._session_cache_path() == (
                memo_module._cache_path_for("", head, session_id)
            )
        with mock.patch.dict(
            os.environ, {memo_module._SESSION_NONCE_ENV: ""}, clear=False,
        ):
            assert memo_module._session_cache_path(
                run_id=run_id, head=head,
            ) is None
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(memo_module._SESSION_NONCE_ENV, None)
            assert memo_module._session_cache_path(
                run_id=run_id, head=head,
            ) is None
        nonce_missing = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.dict(
            os.environ,
            {
                memo_module._RUN_ID_ENV: run_id,
                memo_module._SESSION_NONCE_ENV: "",
            },
        ):
            _receipt_error(
                nonce_missing.get, memo_module, "cache-path-unavailable",
            )
        assert calls == ["resolve"]

        pathless = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.object(
            memo_module, "_session_cache_path", return_value=None,
        ):
            _receipt_error(
                lambda: pathless.prewarm(run_id=run_id),
                memo_module,
                "cache-path-unavailable",
            )
            with mock.patch.dict(os.environ, {memo_module._RUN_ID_ENV: run_id}):
                _receipt_error(
                    pathless.get, memo_module, "cache-path-unavailable",
                )
        assert calls == ["resolve"]

        lock_failed = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.object(
            memo_module, "open", side_effect=OSError(13, "denied"), create=True,
        ):
            error = _receipt_error(
                lambda: lock_failed.prewarm(
                    run_id=run_id, session_id=session_id,
                ),
                memo_module,
                "lock-open-failed",
            )
        assert error.payload["exception_type"] == "PermissionError"
        assert error.payload["errno"] == 13 and calls == ["resolve"]
        lock_reader = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.object(
            memo_module, "open", side_effect=OSError(13, "denied"), create=True,
        ), mock.patch.dict(os.environ, {memo_module._RUN_ID_ENV: run_id}):
            error = _receipt_error(
                lock_reader.get, memo_module, "lock-open-failed",
            )
        assert error.payload["prewarm"] is False and calls == ["resolve"]

        missing = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.dict(os.environ, {memo_module._RUN_ID_ENV: run_id}):
            _receipt_error(missing.get, memo_module, "cache-missing")
        assert calls == ["resolve"]

        path.write_bytes(b"not json")
        corrupt = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.dict(
            os.environ,
            {
                memo_module._RUN_ID_ENV: run_id,
                memo_module._SESSION_NONCE_ENV: session_id,
            },
        ):
            _receipt_error(corrupt.get, memo_module, "cache-json-decode-failed")
        assert calls == ["resolve"]
        path.write_bytes(json.dumps({"wrong": "type"}).encode("utf-8"))
        wrong_type = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.dict(
            os.environ,
            {
                memo_module._RUN_ID_ENV: run_id,
                memo_module._SESSION_NONCE_ENV: session_id,
            },
        ):
            _receipt_error(wrong_type.get, memo_module, "cache-schema-invalid")
        assert calls == ["resolve"]
        path.unlink()

        path.write_bytes(b"stale session")
        preexisting = memo_module._make_receipt_memo(resolve=resolve)
        _receipt_error(
            lambda: preexisting.prewarm(
                run_id=run_id, session_id=session_id,
            ),
            memo_module,
            "cache-preexists-before-prewarm",
        )
        assert calls == ["resolve"]
        path.unlink()

        controller = memo_module._make_receipt_memo(resolve=resolve)
        assert controller.prewarm(
            run_id=run_id, session_id=session_id,
        ) is resolution
        worker = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.dict(
            os.environ,
            {
                memo_module._RUN_ID_ENV: run_id,
                memo_module._SESSION_NONCE_ENV: session_id,
            },
        ):
            loaded = worker.get()
            assert loaded == resolution and worker.get() is loaded
        assert calls == ["resolve", "resolve"]
        path.unlink()

        # 実 _cache_store の replace を directory 宛てにして失敗させる。
        path.mkdir()
        store_tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        try:
            memo_module._cache_store(path, resolution)
        except IsADirectoryError:
            pass
        else:
            raise AssertionError("実 _cache_store が replace 失敗を握り潰した")
        assert path.is_dir()
        assert not store_tmp.exists()
        path.rmdir()

        store_failed = memo_module._make_receipt_memo(resolve=resolve)
        store_error = OSError(28, "no space")
        with mock.patch.object(memo_module, "_cache_store", side_effect=store_error):
            error = _receipt_error(
                lambda: store_failed.prewarm(
                    run_id=run_id, session_id=session_id,
                ),
                memo_module,
                "cache-store-failed",
            )
        assert error.payload["errno"] == 28
        assert error.payload["process_prewarmed"] is False
        assert calls == ["resolve", "resolve", "resolve"]
        with mock.patch.dict(
            os.environ,
            {
                memo_module._RUN_ID_ENV: run_id,
                memo_module._SESSION_NONCE_ENV: session_id,
            },
        ):
            _receipt_error(store_failed.get, memo_module, "cache-missing")
        assert calls == ["resolve", "resolve", "resolve"]

        # 合成 fail-open consumer は resolver count 0 の control を破る。
        fail_open_calls = []

        def synthetic_fail_open():
            try:
                return memo_module._make_receipt_memo(resolve=resolve).get()
            except memo_module.ReceiptMemoError:
                fail_open_calls.append("fallback")
                return resolve()

        try:
            _receipt_error(synthetic_fail_open, memo_module, "cache-path-unavailable")
        except AssertionError:
            pass
        else:
            raise AssertionError("L1 fail-open 合成負例が structured error 検査を通過した")
        assert fail_open_calls == ["fallback"]


def test_receipt_memo_reader_rejects_cache_from_other_invocation(tmp_path):
    """別 invocation の reader が stale cache を誤読せず fail-closed になる。"""
    from orchestrator.tests import real_repo_receipt_memo as memo_module

    head = "d" * 40
    run_id = "same-run-id"
    session_a = "invocation-a"
    session_b = "invocation-b"
    calls = []
    resolution = memo_module.migration.ReceiptResolution(
        "never-issued", (), None, head,
    )

    def resolve():
        calls.append("resolve")
        return resolution

    with mock.patch.object(memo_module, "_repo_head", return_value=head), \
            mock.patch.object(memo_module.tempfile, "gettempdir", return_value=str(tmp_path)):
        controller = memo_module._make_receipt_memo(resolve=resolve)
        controller.prewarm(run_id=run_id, session_id=session_a)
        path_a = memo_module._cache_path_for(run_id, head, session_a)
        with mock.patch.dict(
            os.environ,
            {
                memo_module._RUN_ID_ENV: run_id,
                memo_module._SESSION_NONCE_ENV: session_b,
            },
        ):
            _receipt_error(
                memo_module._make_receipt_memo(resolve=resolve).get,
                memo_module,
                "cache-missing",
            )

        assert path_a.exists()
        assert calls == ["resolve"]


def test_receipt_memo_json_cache_rejects_pickle_and_invalid_json_without_resolve(tmp_path):
    """攻撃 payload、schema 不一致、duplicate key、NaN/Infinity を fail-closed にする。"""
    from orchestrator.tests import real_repo_receipt_memo as memo_module

    head = "e" * 40
    run_id = "json-attack-run"
    session_id = "json-attack-session"
    marker = tmp_path / "pickle-marker"
    calls = []

    class _PicklePayload:
        def __reduce__(self):
            expression = (
                "__import__('pathlib').Path(%r).write_text('executed')"
                % str(marker)
            )
            return (eval, (expression,))

    def resolve():
        calls.append("resolve")
        return memo_module.migration.ReceiptResolution("never-issued", (), None, head)

    with mock.patch.object(memo_module, "_repo_head", return_value=head), \
            mock.patch.object(memo_module.tempfile, "gettempdir", return_value=str(tmp_path)), \
            mock.patch.dict(
                os.environ,
                {
                    memo_module._RUN_ID_ENV: run_id,
                    memo_module._SESSION_NONCE_ENV: session_id,
                },
            ):
        path = memo_module._cache_path_for(run_id, head, session_id)
        path.write_bytes(pickle.dumps(_PicklePayload()))
        _receipt_error(
            memo_module._make_receipt_memo(resolve=resolve).get,
            memo_module,
            "cache-json-decode-failed",
        )
        assert calls == []
        assert not marker.exists()

        path.write_text('{"wrong":"type"}', encoding="utf-8")
        _receipt_error(
            memo_module._make_receipt_memo(resolve=resolve).get,
            memo_module,
            "cache-schema-invalid",
        )
        assert calls == []

        valid_document = memo_module._cache_document(
            memo_module.migration.ReceiptResolution("never-issued", (), None, head)
        )
        valid_members = []
        for key, value in valid_document.items():
            member = (
                json.dumps(key, ensure_ascii=False, separators=(",", ":"))
                + ":"
                + json.dumps(
                    value,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            valid_members.append(member)
            if key == "state":
                valid_members.append(member)
        duplicate_state = ("{" + ",".join(valid_members) + "}").encode("utf-8")
        for raw in (
            duplicate_state,
            b'{"wrong":NaN}',
            b'{"wrong":Infinity}',
            b'{"wrong":-Infinity}',
        ):
            path.write_bytes(raw)
            _receipt_error(
                memo_module._make_receipt_memo(resolve=resolve).get,
                memo_module,
                "cache-json-decode-failed",
            )
        assert calls == []
        assert not marker.exists()

        path.write_bytes(b"12345")
        with mock.patch.object(memo_module, "_CACHE_MAX_BYTES", 4):
            _receipt_error(
                memo_module._make_receipt_memo(resolve=resolve).get,
                memo_module,
                "cache-size-limit",
            )
        assert calls == []

        path.unlink()
        writer = memo_module._make_receipt_memo(resolve=resolve)
        with mock.patch.object(memo_module, "_CACHE_MAX_BYTES", 4):
            _receipt_error(
                lambda: writer.prewarm(
                    run_id=run_id, session_id=session_id,
                ),
                memo_module,
                "cache-store-failed",
            )
        assert calls == ["resolve"]
        assert not path.exists()


def test_receipt_memo_public_endpoints_reject_all_xdist_reader_faults():
    """公開 2 endpoint は UID 下の miss・破損・lock 不能でも実解決しない。"""
    from orchestrator.tests import real_repo_receipt_memo as memo_module

    calls = []

    def production_resolve(*, root):
        calls.append(Path(root))
        return object()

    head = "b" * 40
    run_id = "public-fail-closed"
    with tempfile.TemporaryDirectory(prefix="receipt-public-test-") as raw_tmp, \
            mock.patch.object(memo_module, "_repo_head", return_value=head), \
            mock.patch.object(memo_module.tempfile, "gettempdir", return_value=raw_tmp), \
            mock.patch.object(
                memo_module, "_PRODUCTION_RESOLVE", production_resolve,
            ), mock.patch.dict(
                os.environ,
                {
                    memo_module._RUN_ID_ENV: run_id,
                    memo_module._SESSION_NONCE_ENV: "public-session",
                },
                clear=False,
            ):
        path = memo_module._cache_path_for(run_id, head, "public-session")
        cases = (
            ("cache-missing", None),
            ("cache-json-decode-failed", b"not json"),
            ("lock-open-failed", b"unused"),
        )
        for reason, cache_bytes in cases:
            for endpoint_name in ("real_repo_receipt", "memo_resolver"):
                if path.exists():
                    path.unlink()
                if cache_bytes is not None:
                    path.write_bytes(cache_bytes)
                memo = memo_module._make_receipt_memo()
                with mock.patch.object(memo_module, "_RECEIPT_MEMO", memo):
                    if endpoint_name == "real_repo_receipt":
                        call = memo_module.real_repo_receipt
                    else:
                        call = lambda: memo_module.memo_resolver(root=memo_module.ROOT)
                    if reason == "lock-open-failed":
                        with mock.patch.object(
                            memo_module, "open",
                            side_effect=OSError(13, "denied"), create=True,
                        ):
                            error = _receipt_error(call, memo_module, reason)
                    else:
                        error = _receipt_error(call, memo_module, reason)
                assert error.payload["run_id"] == run_id
                assert error.payload["prewarm"] is False
                assert calls == []


def test_receipt_memo_process_state_is_scoped_to_pytest_session():
    """反復 session は旧 snapshot を捨て、入れ子終了時は外側だけを復元する。"""
    from orchestrator.tests import real_repo_receipt_memo as memo_module

    first = object()
    second = object()
    snapshots = iter((first, second))
    calls = []

    def resolve():
        value = next(snapshots)
        calls.append(value)
        return value

    memo = memo_module._make_receipt_memo(resolve=resolve)
    assert memo.prewarm(run_id=None, session_id="session-a") is first
    assert memo.get() is first
    assert memo.prewarm(run_id=None, session_id="session-a") is first
    assert memo.prewarm(run_id=None, session_id="session-b") is second
    assert memo.get() is second
    memo.finish_session(session_id="session-b")
    assert memo.get() is first
    memo.finish_session(session_id="session-a")
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop(memo_module._RUN_ID_ENV, None)
        _receipt_error(memo.get, memo_module, "cache-path-unavailable")
    assert calls == [first, second]


def test_receipt_memo_prune_keeps_locks_and_current_session_key():
    from orchestrator.tests import real_repo_receipt_memo as memo_module

    with tempfile.TemporaryDirectory(prefix="receipt-prune-test-") as raw_tmp:
        directory = Path(raw_tmp)
        current = directory / f"{memo_module._CACHE_PREFIX}current.json"
        stale = directory / f"{memo_module._CACHE_PREFIX}stale.json"
        lock = directory / f"{memo_module._CACHE_PREFIX}stale.json.lock"
        for path in (current, stale, lock):
            path.write_bytes(b"x")
            os.utime(path, (time.time() - memo_module._CACHE_STALE_S - 10,) * 2)
        memo_module._prune_stale_caches(directory, current_path=current)
        assert current.exists() and lock.exists() and not stale.exists()

        legacy = directory / f"{memo_module._CACHE_PREFIX}legacy.pickle"
        legacy_lock = directory / f"{memo_module._CACHE_PREFIX}legacy.pickle.lock"
        for path in (legacy, legacy_lock):
            path.write_bytes(b"x")
            os.utime(path, (time.time() - memo_module._CACHE_STALE_S - 10,) * 2)
        memo_module._prune_stale_caches(directory, current_path=current)
        assert not legacy.exists() and not legacy_lock.exists()

        # 合成旧 prune は lock と current の両方を消し、この契約を満たせない。
        def synthetic_old_prune():
            for entry in directory.glob(f"{memo_module._CACHE_PREFIX}*"):
                entry.unlink()

        synthetic_old_prune()
        try:
            assert current.exists() and lock.exists()
        except AssertionError:
            pass
        else:
            raise AssertionError("prune の合成負例が lock/current 保護を通過した")


_OPTION_UNDECLARED = object()


class _ReceiptHookConfig:
    def __init__(self, options=None, *, worker=False):
        self._options = dict(options or {})
        self.option = SimpleNamespace(**self._options)
        self._izanagi_receipt_memo_session_id = "session-test"
        if worker:
            self.workerinput = {
                "testrunuid": self._options.get("testrunuid"),
                "_izanagi_receipt_memo_session_id": self._options.get(
                    "session_nonce", "session-test",
                ),
            }

    def getoption(self, name, default=_OPTION_UNDECLARED):
        if name in self._options:
            return self._options[name]
        if default is _OPTION_UNDECLARED:
            raise ValueError(f"no option named {name!r}")
        return default


def _receipt_hook_item(nodeid):
    filename, function = nodeid.split("::", 1)
    return SimpleNamespace(
        path=HERE / filename, name=function, originalname=function,
    )


def _fixture_body(function):
    body = inspect.unwrap(function)
    assert callable(body) and body is not function, (
        f"実 fixture function を unwrap できない: {function!r}"
    )
    return body


def _recorded_actual_fixture_execution(case: str, temporary: Path):
    """Execute the named production fixture body under a recording real lock."""
    suite_conftest = _load_suite_conftest()
    events = []
    active = []

    @contextlib.contextmanager
    def recorded_locks(access):
        vector = (access.parent, access.ccbench)
        events.append(("enter", vector))
        active.append(vector)
        try:
            yield
        finally:
            assert active.pop() == vector
            events.append(("exit", vector))

    tmp_factory = SimpleNamespace(mktemp=lambda _name: temporary)
    with mock.patch.object(suite_conftest, "_real_repo_locks", recorded_locks):
        lock_factory = _fixture_body(
            suite_conftest.real_repo_fixture_lock
        )()

        if case == "invariant-candidate":
            from orchestrator.tests import test_s8c_preregistration_invariant as sut

            def build(_path):
                events.append(("builder", tuple(active)))
                assert active == [("write", None)]
                return "a" * 40

            patchers = (mock.patch.object(sut, "_candidate_commit", build),)
            fixture = _fixture_body(sut.repository_candidate_commit)
            arguments = (tmp_factory, lock_factory)
            expected = "a" * 40
        elif case == "predicate-candidate":
            from orchestrator.tests import test_s8c_preregistration_predicates as sut

            def build(_path):
                events.append(("builder", tuple(active)))
                assert active == [("write", None)]
                return "b" * 40

            patchers = (
                mock.patch.object(sut, "_candidate_commit_with_worktree", build),
            )
            fixture = _fixture_body(sut.repository_candidate_commit)
            arguments = (tmp_factory, lock_factory)
            expected = "b" * 40
        elif case == "campaign-scan":
            from orchestrator.tests import test_campaign_import_invariant as sut

            expected = object()

            def scan(root):
                events.append(("read", root, tuple(active)))
                assert root == sut.REPOSITORY
                assert active == [("read", "read")]
                return expected

            patchers = (mock.patch.object(sut, "scan_repository", scan),)
            fixture = _fixture_body(sut.repository_scan)
            arguments = (lock_factory,)
        elif case == "current-commit-snapshot":
            from orchestrator.tests import test_s8c_preregistration_predicates as sut

            expected = (temporary, "c" * 40, ("evaluated",), "d" * 40, ("actual",))

            def snapshot(_path):
                events.append(("read", "snapshot", tuple(active)))
                assert active == [("read", None)]
                return temporary, "c" * 40, "d" * 40, ("actual",)

            def evaluate(head, *, repo_root):
                events.append(("read", "evaluate", tuple(active)))
                assert active == [("read", None)]
                assert head == "c" * 40 and repo_root == temporary
                return ("evaluated",)

            registry = SimpleNamespace(evaluate_all=evaluate)
            patchers = (
                mock.patch.object(sut, "_snapshot_current_commit", snapshot),
                mock.patch.object(sut.M, "get_registry", return_value=registry),
            )
            fixture = _fixture_body(sut.current_commit_snapshot)
            arguments = (tmp_factory, lock_factory)
        else:
            raise AssertionError(f"unknown actual fixture case: {case}")

        with contextlib.ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            generator = fixture(*arguments)
            value = next(generator)
            events.append(("yield", tuple(active)))
            assert value == expected
            with pytest.raises(StopIteration):
                next(generator)
    assert active == []
    return events


def test_current_commit_snapshot_actual_fixture_owns_parent_reader_context():
    with tempfile.TemporaryDirectory(prefix="izanagi-current-snapshot-lock-") as raw:
        events = _recorded_actual_fixture_execution(
            "current-commit-snapshot", Path(raw),
        )
    assert events == [
        ("enter", ("read", None)),
        ("read", "snapshot", (("read", None),)),
        ("read", "evaluate", (("read", None),)),
        ("yield", (("read", None),)),
        ("exit", ("read", None)),
    ]


def test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture(
        tmp_path):
    """実 fixture の SH 寿命中に同じ fd を EX へ昇格し SH へ戻す。"""
    suite_conftest = _load_suite_conftest()
    from orchestrator.tests import test_s8c_preregistration_predicates as sut

    tmp_factory = SimpleNamespace(mktemp=lambda _name: tmp_path)
    events = []
    outer_fds = None

    def parent_states():
        return tuple(sorted(
            (path.name, state.fd, state.mode, sum(state.holders.values()))
            for (resource, path), state in (
                suite_conftest._REAL_REPO_PROCESS_LOCKS.items()
            )
            if resource == "parent"
        ))

    def snapshot(_path):
        events.append(("snapshot", tuple(row[2] for row in parent_states())))
        return tmp_path, "a" * 40, "b" * 40, ("actual",)

    def build(_path):
        current = parent_states()
        events.append(("candidate-build", tuple(row[2] for row in current)))
        assert outer_fds is not None
        assert {row[1] for row in current} == outer_fds
        return "c" * 40

    registry = SimpleNamespace(
        evaluate_all=lambda head, *, repo_root: ("evaluated",),
    )
    with mock.patch.object(
            suite_conftest, "_REAL_REPO_LOCK_DIRECTORY", tmp_path,
            ), mock.patch.object(
                suite_conftest, "_REAL_REPO_LOCK_TIMEOUT_S", 2.0,
            ), mock.patch.object(
                suite_conftest, "_REAL_REPO_LOCK_RETRY_INTERVAL_S", 0.002,
            ), mock.patch.object(
                sut, "_snapshot_current_commit", snapshot,
            ), mock.patch.object(
                sut.M, "get_registry", return_value=registry,
            ), mock.patch.object(
                sut, "_candidate_commit_with_worktree", build,
            ):
        lock_factory = _fixture_body(
            suite_conftest.real_repo_fixture_lock
        )()
        snapshot_fixture = _fixture_body(sut.current_commit_snapshot)(
            tmp_factory, lock_factory,
        )
        snapshot_value = next(snapshot_fixture)
        assert snapshot_value[1] == "a" * 40
        outer_state = parent_states()
        assert tuple(row[2] for row in outer_state) == ("read", "read")
        outer_fds = {row[1] for row in outer_state}

        started = time.monotonic()
        candidate_fixture = _fixture_body(sut.repository_candidate_commit)(
            tmp_factory, lock_factory,
        )
        assert next(candidate_fixture) == "c" * 40
        assert time.monotonic() - started < 2.0
        assert tuple(row[2] for row in parent_states()) == ("read", "read")
        with pytest.raises(StopIteration):
            next(candidate_fixture)
        assert tuple(row[2] for row in parent_states()) == ("read", "read")
        with pytest.raises(StopIteration):
            next(snapshot_fixture)

    assert events == [
        ("snapshot", ("read", "read")),
        ("candidate-build", ("write", "write")),
    ]
    assert suite_conftest._REAL_REPO_PROCESS_LOCKS == {}


_REAL_REPO_CLOSURE_MUTATION_IDS = (
    "t810-live-reader-unregistered",
    "invariant-candidate-write-downgraded",
    "predicate-candidate-lock-removed",
    "campaign-scan-lock-removed",
    "parent-key-uses-worktree-root",
    "legacy-key-not-acquired",
    "conflict-edge-removed",
    "prewarm-lock-removed",
    "nested-collection-node-unregistered",
)


@pytest.mark.parametrize(
    "mutation_id",
    _REAL_REPO_CLOSURE_MUTATION_IDS,
    ids=_REAL_REPO_CLOSURE_MUTATION_IDS,
)
def test_real_repo_closure_mutations(mutation_id, tmp_path):
    """One direct gate per preregistered closure mutation, without fallback gates."""
    suite_conftest = _load_suite_conftest()

    if mutation_id == "t810-live-reader-unregistered":
        actual = {
            node: suite_conftest.REAL_REPO_ACCESS_BY_NODE.get(node)
            for node in _T810_LIVE_AUTHORITY_NODES_GOLDEN
        }
        assert actual == {
            node: suite_conftest.RealRepoAccess("read", None)
            for node in _T810_LIVE_AUTHORITY_NODES_GOLDEN
        }, f"T810 live-authority parent reader missing: {actual!r}"
        return

    if mutation_id == "invariant-candidate-write-downgraded":
        events = _recorded_actual_fixture_execution(
            "invariant-candidate", tmp_path,
        )
        assert events == [
            ("enter", ("write", None)),
            ("builder", (("write", None),)),
            ("exit", ("write", None)),
            ("enter", ("read", None)),
            ("yield", (("read", None),)),
            ("exit", ("read", None)),
        ], f"invariant candidate fixture lock phases changed: {events!r}"
        return

    if mutation_id == "predicate-candidate-lock-removed":
        events = _recorded_actual_fixture_execution(
            "predicate-candidate", tmp_path,
        )
        assert events == [
            ("enter", ("write", None)),
            ("builder", (("write", None),)),
            ("exit", ("write", None)),
            ("enter", ("read", None)),
            ("yield", (("read", None),)),
            ("exit", ("read", None)),
        ], f"predicate candidate fixture lock phases changed: {events!r}"
        return

    if mutation_id == "campaign-scan-lock-removed":
        events = _recorded_actual_fixture_execution("campaign-scan", tmp_path)
        assert events == [
            ("enter", ("read", "read")),
            ("read", Path(ROOT), (("read", "read"),)),
            ("yield", (("read", "read"),)),
            ("exit", ("read", "read")),
        ], f"campaign repository_scan fixture lock phases changed: {events!r}"
        return

    if mutation_id == "parent-key-uses-worktree-root":
        repository = tmp_path / "repository"
        linked = tmp_path / "linked"
        repository.mkdir()
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(repository)], check=True,
        )
        subprocess.run(
            ["git", "-C", str(repository), "config", "user.name", "fixture"],
            check=True,
        )
        subprocess.run(
            [
                "git", "-C", str(repository), "config", "user.email",
                "fixture@example.invalid",
            ],
            check=True,
        )
        (repository / "tracked").write_text("fixture\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(repository), "add", "tracked"], check=True,
        )
        subprocess.run(
            ["git", "-C", str(repository), "commit", "-qm", "fixture"],
            check=True,
        )
        subprocess.run(
            [
                "git", "-C", str(repository), "worktree", "add", "-q",
                "--detach", str(linked), "HEAD",
            ],
            check=True,
        )
        with mock.patch.dict(
            os.environ,
            {
                "GIT_COMMON_DIR": str(tmp_path / "poison-common.git"),
                "GIT_DIR": str(tmp_path / "poison.git"),
                "GIT_INDEX_FILE": str(tmp_path / "poison.index"),
                "GIT_WORK_TREE": str(tmp_path / "poison-worktree"),
            },
            clear=False,
        ):
            direct = suite_conftest._real_repo_lock_path(
                "parent", repo_root=repository,
            )
            sibling = suite_conftest._real_repo_lock_path(
                "parent", repo_root=linked,
            )
            from tools import acceptance_shards
            assert acceptance_shards._git_common_dir(repository) == (
                repository / ".git"
            ).resolve()
        assert direct == sibling, (
            "sibling worktrees did not share the parent common-dir lock key"
        )
        assert suite_conftest._real_repo_legacy_lock_path(
            "parent", repo_root=repository,
        ) != suite_conftest._real_repo_legacy_lock_path(
            "parent", repo_root=linked,
        )
        return

    if mutation_id == "legacy-key-not-acquired":
        legacy = tmp_path / "legacy.lock"
        common = tmp_path / "common.lock"
        events = []

        @contextlib.contextmanager
        def record_path(resource, mode, path, *, deadline, retry_interval_s):
            events.append(("enter", resource, mode, path))
            try:
                yield
            finally:
                events.append(("exit", resource, mode, path))

        with mock.patch.object(
            suite_conftest, "_real_repo_legacy_lock_path", return_value=legacy,
        ), mock.patch.object(
            suite_conftest, "_real_repo_lock_path", return_value=common,
        ), mock.patch.object(
            suite_conftest, "_real_repo_lock_path_context", record_path,
        ):
            with suite_conftest._real_repo_file_lock("parent", "write"):
                events.append(("body",))
        assert events == [
            ("enter", "parent", "write", legacy),
            ("enter", "parent", "write", common),
            ("body",),
            ("exit", "parent", "write", common),
            ("exit", "parent", "write", legacy),
        ], f"legacy/common key acquisition order or mode changed: {events!r}"

        entered = threading.Event()
        failures = []

        def acquire_new_reader():
            try:
                with suite_conftest._real_repo_file_lock(
                    "parent", "read", timeout_s=2.0, retry_interval_s=0.01,
                ):
                    entered.set()
            except BaseException as exc:
                failures.append(exc)

        legacy_fd = suite_conftest._open_real_repo_lock(legacy)
        suite_conftest.fcntl.flock(legacy_fd, suite_conftest.fcntl.LOCK_EX)
        try:
            with mock.patch.object(
                suite_conftest, "_real_repo_legacy_lock_path", return_value=legacy,
            ), mock.patch.object(
                suite_conftest, "_real_repo_lock_path", return_value=common,
            ):
                thread = threading.Thread(target=acquire_new_reader)
                thread.start()
                time.sleep(0.05)
                assert not entered.is_set(), (
                    "legacy EX holder did not block the dual-key reader"
                )
                suite_conftest.fcntl.flock(
                    legacy_fd, suite_conftest.fcntl.LOCK_UN,
                )
                thread.join(2.0)
                assert not thread.is_alive()
        finally:
            try:
                suite_conftest.fcntl.flock(
                    legacy_fd, suite_conftest.fcntl.LOCK_UN,
                )
            finally:
                suite_conftest.os.close(legacy_fd)
        assert not failures
        assert entered.is_set()
        return

    if mutation_id == "conflict-edge-removed":
        from tools import acceptance_shards
        # C1: exact matrix is the first gate.  The controls below cannot hide
        # an edge deletion by deriving their expectation from production.
        assert (
            acceptance_shards.REAL_REPO_GROUP_CONFLICT_EDGES
            == _REAL_REPO_GROUP_CONFLICT_EDGES_GOLDEN
        ), "real-repo shard conflict matrix differs from independent exact golden"
        assert (
            _conflict_edges_from_independent_access_literals()
            == _REAL_REPO_GROUP_CONFLICT_EDGES_GOLDEN
        ), "fixture/resource access literals do not justify the edge golden"
        records = (
            acceptance_shards.ItemRecord(
                next(iter(sorted(_CAMPAIGN_REPOSITORY_SCAN_NODES_GOLDEN))),
                "orchestrator/tests/test_campaign_import_invariant.py",
                "campaign-repository-scan",
            ),
            acceptance_shards.ItemRecord(
                next(iter(sorted(_T810_LIVE_AUTHORITY_NODES_GOLDEN))),
                "orchestrator/tests/test_t810_coordinator.py",
                "real-repo",
            ),
            acceptance_shards.ItemRecord(
                next(iter(sorted(_S8C_PREDICATE_SNAPSHOT_NODES_GOLDEN))),
                "orchestrator/tests/test_s8c_preregistration_predicates.py",
                "s8c-predicate-snapshot",
            ),
            acceptance_shards.ItemRecord(
                next(iter(sorted(_S8C_PREREGISTRATION_CANDIDATE_NODES_GOLDEN))),
                "orchestrator/tests/test_s8c_preregistration_invariant.py",
                "s8c-preregistration-candidate",
            ),
        )
        components = acceptance_shards._components(records)
        assert len(components) == 1
        assert set(components[0]["groups"]) == {
            "campaign-repository-scan",
            "real-repo",
            "s8c-predicate-snapshot",
            "s8c-preregistration-candidate",
        }
        return

    if mutation_id == "prewarm-lock-removed":
        cases = (
            (
                "receipt",
                suite_conftest._prewarm_receipt_memo,
                suite_conftest._receipt_memo_module,
                "_receipt_memo_module",
                "prewarm_real_repo_receipt",
                "finish_real_repo_receipt_session",
                next(iter(sorted(_RECEIPT_MEMO_CONSUMERS_GOLDEN))),
                suite_conftest._RECEIPT_MEMO_SESSION_ID_ATTR,
            ),
            (
                "oracle",
                suite_conftest._prewarm_oracle_environment_memo,
                suite_conftest._oracle_environment_memo_module,
                "_oracle_environment_memo_module",
                "prewarm_oracle_environment",
                "finish_oracle_environment_session",
                next(iter(sorted(ORACLE_ENVIRONMENT_CONSUMERS_GOLDEN))),
                suite_conftest._ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
            ),
        )
        for (
            label, prewarm, _module_owner, module_attr, endpoint_attr,
            finish_attr, consumer, session_attr,
        ) in cases:
            active = []
            events = []

            @contextlib.contextmanager
            def locks(access):
                vector = (access.parent, access.ccbench)
                active.append(vector)
                events.append(("enter", vector))
                try:
                    yield
                finally:
                    assert active.pop() == vector
                    events.append(("exit", vector))

            def endpoint(**_kwargs):
                events.append(("endpoint", tuple(active)))
                assert active == [("read", None)]

            config = _ReceiptHookConfig({"collectonly": False})
            setattr(config, session_attr, f"{label}-session")
            fake_module = SimpleNamespace(**{
                endpoint_attr: endpoint,
                finish_attr: mock.Mock(),
            })
            with mock.patch.object(suite_conftest, "_real_repo_locks", locks), \
                    mock.patch.object(
                        suite_conftest, module_attr, return_value=fake_module,
                    ):
                prewarm(config, [consumer], run_id=None)
            assert events == [
                ("enter", ("read", None)),
                ("endpoint", (("read", None),)),
                ("exit", ("read", None)),
            ], f"{label} prewarm endpoint escaped parent SH: {events!r}"
        return

    if mutation_id == "nested-collection-node-unregistered":
        actual = {
            node: suite_conftest.REAL_REPO_ACCESS_BY_NODE.get(node)
            for node in _NESTED_COLLECTION_NODES_GOLDEN
        }
        assert actual == {
            node: suite_conftest.RealRepoAccess("read", None)
            for node in _NESTED_COLLECTION_NODES_GOLDEN
        }, f"nested whole-suite collection parent reader missing: {actual!r}"
        return

    raise AssertionError(f"unhandled real-repo closure mutation id: {mutation_id}")


def test_receipt_memo_configure_node_wires_nonce_and_restores_nested_env():
    import pytest

    suite_conftest = _load_suite_conftest()
    with mock.patch.dict(
        os.environ,
        {suite_conftest._RECEIPT_MEMO_NONCE_ENV: "outer-nonce"},
        clear=False,
    ):
        controller = _ReceiptHookConfig()
        worker = None
        suite_conftest._configure_receipt_memo_session(controller)
        controller_nonce = getattr(
            controller, suite_conftest._RECEIPT_MEMO_SESSION_ID_ATTR,
        )
        assert isinstance(controller_nonce, str) and controller_nonce
        assert os.environ[suite_conftest._RECEIPT_MEMO_NONCE_ENV] == controller_nonce
        try:
            node = SimpleNamespace(
                config=controller, workerinput={"testrunuid": "ci-job-42"},
            )
            suite_conftest.pytest_configure_node(node)
            assert node.workerinput == {
                "testrunuid": "ci-job-42",
                suite_conftest._RECEIPT_MEMO_SESSION_ID_ATTR: controller_nonce,
            }

            worker = SimpleNamespace(workerinput=dict(node.workerinput))
            suite_conftest._configure_receipt_memo_session(worker)
            assert getattr(
                worker, suite_conftest._RECEIPT_MEMO_SESSION_ID_ATTR,
            ) == controller_nonce
            assert os.environ[suite_conftest._RECEIPT_MEMO_NONCE_ENV] == controller_nonce
            suite_conftest._restore_receipt_memo_nonce(worker)
            assert os.environ[suite_conftest._RECEIPT_MEMO_NONCE_ENV] == controller_nonce

            missing = SimpleNamespace(workerinput={})
            with pytest.raises(pytest.UsageError):
                suite_conftest._configure_receipt_memo_session(missing)
            assert os.environ[suite_conftest._RECEIPT_MEMO_NONCE_ENV] == controller_nonce
        finally:
            if worker is not None:
                suite_conftest._restore_receipt_memo_nonce(worker)
            suite_conftest._restore_receipt_memo_nonce(controller)
        assert os.environ[suite_conftest._RECEIPT_MEMO_NONCE_ENV] == "outer-nonce"


def test_receipt_memo_nonce_cleanup_preserves_unconfigure_exception():
    suite_conftest = _load_suite_conftest()
    config = SimpleNamespace()
    original = RuntimeError("original pytest failure")
    with mock.patch.dict(
        os.environ,
        {suite_conftest._RECEIPT_MEMO_NONCE_ENV: "outer-nonce"},
        clear=False,
    ):
        suite_conftest._configure_receipt_memo_session(config)
        wrapper = suite_conftest.pytest_unconfigure(config)
        next(wrapper)
        with mock.patch.object(suite_conftest, "unmark_pytest_session_enforcing", None), \
                mock.patch.object(
                    suite_conftest, "_emit_effective_scheduler_marker",
                    return_value=None,
                ):
            try:
                wrapper.throw(original)
            except RuntimeError as exc:
                assert exc is original
            else:
                raise AssertionError("pytest_unconfigure が元例外を握り潰した")
        assert os.environ[suite_conftest._RECEIPT_MEMO_NONCE_ENV] == "outer-nonce"


def test_memo_cleanup_runs_oracle_after_receipt_cleanup_error():
    """A receipt cleanup failure must not skip the independent oracle cleanup."""
    suite_conftest = _load_suite_conftest()
    config = SimpleNamespace()
    calls = []
    receipt_error = RuntimeError("receipt cleanup failed")

    def finish_receipt(_config):
        calls.append("receipt")
        raise receipt_error

    def finish_oracle(_config):
        calls.append("oracle")

    wrapper = suite_conftest.pytest_unconfigure(config)
    next(wrapper)
    with mock.patch.object(suite_conftest, "unmark_pytest_session_enforcing", None), \
            mock.patch.object(
                suite_conftest, "_emit_effective_scheduler_marker", return_value=None,
            ), mock.patch.object(
                suite_conftest, "_finish_receipt_memo_session", side_effect=finish_receipt,
            ), mock.patch.object(
                suite_conftest, "_finish_oracle_environment_memo_session",
                side_effect=finish_oracle,
            ):
        try:
            next(wrapper)
        except RuntimeError as exc:
            assert exc is receipt_error
        else:
            raise AssertionError("receipt cleanup failure was swallowed")
    assert calls == ["receipt", "oracle"]


def test_receipt_memo_prewarm_wiring_is_controller_only_and_lazy():
    suite_conftest = _load_suite_conftest()
    consumer = (
        "test_s8b_oracle_driver.py::"
        "test_success_wal_order_budget_and_evaluate_contract"
    )
    calls = []
    fake_module = SimpleNamespace(
        prewarm_real_repo_receipt=(
            lambda *, run_id, session_id: calls.append(run_id)
        ),
    )

    worker_config = _ReceiptHookConfig(
        {"collectonly": False, "testrunuid": "ci-job-42"}, worker=True,
    )
    worker_session = SimpleNamespace(
        config=worker_config, items=[_receipt_hook_item(consumer)],
    )
    controller_config = _ReceiptHookConfig(
        {"collectonly": False, "testrunuid": "ci-job-42"},
    )
    controller_node = SimpleNamespace(
        config=controller_config,
        workerinput={"testrunuid": "ci-job-42"},
    )
    events = []
    with mock.patch.object(
        suite_conftest, "_receipt_memo_module", return_value=fake_module,
    ):
        events.append("worker-hook")
        suite_conftest.pytest_collection_finish(worker_session)
        assert calls == []
        events.append("controller-hook")
        suite_conftest.pytest_xdist_node_collection_finished(
            controller_node, [consumer + "@real-repo"],
        )
        suite_conftest.pytest_xdist_node_collection_finished(
            controller_node, [consumer + "@real-repo"],
        )
    assert events == ["worker-hook", "controller-hook"]
    assert calls == ["ci-job-42"]

    # serial controller は run_id=None で一回だけ prewarm する。
    serial_calls = []
    serial_module = SimpleNamespace(
        prewarm_real_repo_receipt=(
            lambda *, run_id, session_id: serial_calls.append(run_id)
        ),
    )
    serial_config = _ReceiptHookConfig({"collectonly": False})
    serial_session = SimpleNamespace(
        config=serial_config, items=[_receipt_hook_item(consumer)],
    )
    with mock.patch.object(
        suite_conftest, "_receipt_memo_module", return_value=serial_module,
    ):
        suite_conftest.pytest_collection_finish(serial_session)
    assert serial_calls == [None]

    # conftest の inventory に consumer が無い選択では lazy import seam へ到達しない。
    # consumer file 自体を collect すれば、その module-scope import は別に発生する。
    no_consumer = "test_example.py::test_unrelated"
    with mock.patch.object(
        suite_conftest, "_receipt_memo_module",
        side_effect=AssertionError("consumer なしで memo import"),
    ) as lazy_import:
        suite_conftest.pytest_collection_finish(SimpleNamespace(
            config=_ReceiptHookConfig({"collectonly": False}),
            items=[_receipt_hook_item(no_consumer)],
        ))
    assert lazy_import.call_count == 0

    # prewarm 例外は隣接する task-run stats の握り潰しへ入らず、そのまま伝播する。
    from orchestrator.tests import real_repo_receipt_memo as memo_module

    broken_config = _ReceiptHookConfig({"collectonly": False})
    prewarm_error = memo_module.ReceiptMemoError(
        "resolver-failed", cache_path=None, run_id=None, head=None,
        prewarm=True, process_prewarmed=False,
    )
    broken = SimpleNamespace(
        prewarm_real_repo_receipt=mock.Mock(side_effect=prewarm_error),
        finish_real_repo_receipt_session=mock.Mock(),
    )
    with mock.patch.object(
        suite_conftest, "_receipt_memo_module", return_value=broken,
    ):
        try:
            suite_conftest.pytest_collection_finish(SimpleNamespace(
                config=broken_config, items=[_receipt_hook_item(consumer)],
            ))
        except memo_module.ReceiptMemoError as exc:
            assert exc is prewarm_error
        else:
            raise AssertionError("prewarm 例外が collection hook に握り潰された")
    assert not getattr(
        broken_config, suite_conftest._RECEIPT_MEMO_PREWARMED_ATTR, False,
    )
    broken.finish_real_repo_receipt_session.assert_called_once_with(
        session_id="session-test",
    )

    # 合成 worker payer trace は controller-only assertion が拒否する。
    synthetic_trace = ["worker-hook", "worker-prewarm", "controller-hook"]
    try:
        assert synthetic_trace == ["worker-hook", "controller-hook"]
    except AssertionError:
        pass
    else:
        raise AssertionError("worker prewarm の合成負例が順序検査を通過した")


def test_receipt_memo_optout_only_selection_does_not_prewarm():
    """opt-out 2 関数だけの node 集合は memo import も prewarm もしない。"""
    suite_conftest = _load_suite_conftest()
    optouts = sorted(_RECEIPT_MEMO_OPTOUT_GOLDEN)
    config = _ReceiptHookConfig({"collectonly": False})
    session = SimpleNamespace(
        config=config,
        items=[_receipt_hook_item(nodeid) for nodeid in optouts],
    )
    with mock.patch.object(
        suite_conftest, "_receipt_memo_module",
        side_effect=AssertionError("opt-out only で memo import"),
    ) as lazy_import:
        suite_conftest.pytest_collection_finish(session)
    assert lazy_import.call_count == 0
    assert not getattr(
        config, suite_conftest._RECEIPT_MEMO_PREWARMED_ATTR, False,
    )

    # 合成退行: opt-out を consumer inventory へ混ぜると prewarm が発火する。
    calls = []
    fake_module = SimpleNamespace(
        prewarm_real_repo_receipt=lambda **kwargs: calls.append(kwargs),
    )
    mutated_config = _ReceiptHookConfig({"collectonly": False})
    with mock.patch.object(
        suite_conftest, "RECEIPT_MEMO_CONSUMER_NODES",
        suite_conftest.RECEIPT_MEMO_CONSUMER_NODES | set(optouts),
    ), mock.patch.object(
        suite_conftest, "_receipt_memo_module", return_value=fake_module,
    ):
        suite_conftest.pytest_collection_finish(SimpleNamespace(
            config=mutated_config,
            items=[_receipt_hook_item(nodeid) for nodeid in optouts],
        ))
    assert calls == [{"run_id": None, "session_id": "session-test"}]


def test_receipt_memo_both_worker_guards_are_required_as_redundant_defense():
    """outer/helper 両 guard を同時に外す source 変異は worker payer を再発させる。"""
    suite_conftest = _load_suite_conftest()
    source = (HERE / "conftest.py").read_text(encoding="utf-8")
    inner_guard = (
        "    # pytest_collection_finish の外側 guard と意図的に冗長な defense-in-depth。\n"
        "    # worker payer は両 guard が同時に失われない限り再発しない。\n"
        '    if hasattr(config, "workerinput"):\n'
        "        return\n"
    )
    outer_guard = (
        '    if not hasattr(session.config, "workerinput"):\n'
        "        _prewarm_receipt_memo(\n"
        "            session.config,\n"
        "            (_real_repo_node_id(item) for item in session.items),\n"
        "            run_id=None,\n"
        "        )\n"
    )
    outer_mutant = (
        "    _prewarm_receipt_memo(\n"
        "        session.config,\n"
        "        (_real_repo_node_id(item) for item in session.items),\n"
        "        run_id=None,\n"
        "    )\n"
    )
    assert source.count(inner_guard) == 1
    assert source.count(outer_guard) == 1
    mutated = source.replace(
        inner_guard,
        "    # synthetic mutation: inner worker guard removed\n",
        1,
    ).replace(
        outer_guard, outer_mutant, 1,
    )
    tree = ast.parse(mutated)
    selected = [
        statement for statement in tree.body
        if isinstance(statement, ast.FunctionDef)
        and statement.name in {
            "_prewarm_receipt_memo", "pytest_collection_finish",
        }
    ]
    assert {statement.name for statement in selected} == {
        "_prewarm_receipt_memo", "pytest_collection_finish",
    }
    namespace = dict(vars(suite_conftest))
    exec(compile(ast.Module(body=selected, type_ignores=[]), "mutant", "exec"), namespace)

    consumer = next(iter(sorted(_RECEIPT_MEMO_CONSUMERS_GOLDEN)))
    calls = []
    namespace["_receipt_memo_module"] = lambda: SimpleNamespace(
        prewarm_real_repo_receipt=lambda **kwargs: calls.append(kwargs),
    )
    namespace["pytest_collection_finish"](SimpleNamespace(
        config=_ReceiptHookConfig(
            {"collectonly": False, "testrunuid": "ci-job-42"}, worker=True,
        ),
        items=[_receipt_hook_item(consumer)],
    ))
    try:
        assert calls == []
    except AssertionError:
        pass
    else:
        raise AssertionError("worker guard 両層同時変異が payer 0 検査を通過した")
    assert calls == [{"run_id": None, "session_id": "session-test"}]


_RECEIPT_ORDER_WORKER_HOOK_SOURCE = textwrap.dedent(
    """\
    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_collection_finish(session):
        if hasattr(session.config, "workerinput"):
            record("worker-hook")
        yield
    """
)


def _receipt_order_pluggy_trace(worker_hook_source: str) -> list[str]:
    """実 xdist probe と同じ worker hook を pluggy の一段で順序実行する。"""
    import pluggy

    hookspec = pluggy.HookspecMarker("pytest")
    hookimpl = pluggy.HookimplMarker("pytest")

    class Spec:
        @hookspec
        def pytest_collection_finish(self, session):
            """Minimal collection-finish hook specification."""

    trace: list[str] = []
    namespace = {
        "pytest": SimpleNamespace(hookimpl=hookimpl),
        "record": trace.append,
    }
    exec(compile(worker_hook_source, "receipt-order-worker", "exec"), namespace)
    worker = SimpleNamespace(
        pytest_collection_finish=namespace["pytest_collection_finish"],
    )

    class Controller:
        @hookimpl
        def pytest_collection_finish(self, session):
            trace.append("controller-hook")

    manager = pluggy.PluginManager("pytest")
    manager.add_hookspecs(Spec)
    manager.register(worker, name="worker")
    manager.register(Controller(), name="controller")
    manager.hook.pytest_collection_finish(
        session=SimpleNamespace(config=SimpleNamespace(workerinput={})),
    )
    return trace


def test_receipt_memo_worker_hook_order_mechanism_rejects_both_mutants():
    """hookwrapper と yield 前記録のどちらを失っても相対順検査を通さない。"""
    decorator = "@pytest.hookimpl(hookwrapper=True, tryfirst=True)\n"
    pre_yield = (
        '    if hasattr(session.config, "workerinput"):\n'
        '        record("worker-hook")\n'
        "    yield\n"
    )
    post_yield = (
        "    yield\n"
        '    if hasattr(session.config, "workerinput"):\n'
        '        record("worker-hook")\n'
    )
    assert _RECEIPT_ORDER_WORKER_HOOK_SOURCE.count(decorator) == 1
    assert _RECEIPT_ORDER_WORKER_HOOK_SOURCE.count(pre_yield) == 1

    def assert_worker_first(source: str) -> None:
        trace = _receipt_order_pluggy_trace(source)
        assert trace.count("worker-hook") == 1, trace
        assert trace.count("controller-hook") == 1, trace
        assert trace.index("worker-hook") < trace.index("controller-hook"), trace

    assert_worker_first(_RECEIPT_ORDER_WORKER_HOOK_SOURCE)
    mutants = {
        "decorator removed": _RECEIPT_ORDER_WORKER_HOOK_SOURCE.replace(
            decorator, "", 1,
        ),
        "record moved after yield": _RECEIPT_ORDER_WORKER_HOOK_SOURCE.replace(
            pre_yield, post_yield, 1,
        ),
    }
    for label, mutant in mutants.items():
        try:
            assert_worker_first(mutant)
        except AssertionError:
            continue
        raise AssertionError(f"{label} mutant が worker-first 検査を通過した")


def test_receipt_memo_real_xdist_order_has_no_worker_payer():
    """実 xdist 順序を worker collection hook から controller hook まで固定する。"""
    _require_loadgroup_capability()
    with tempfile.TemporaryDirectory(prefix="receipt-xdist-order-") as raw_tmp:
        directory = Path(raw_tmp)
        events = directory / "events.log"
        (directory / "test_s8b_oracle_driver.py").write_text(
            "def test_success_wal_order_budget_and_evaluate_contract():\n"
            "    pass\n",
            encoding="utf-8",
        )
        plugin_source = f"""
                import os
                from pathlib import Path

                import pytest

                EVENTS = Path({str(events)!r})

                def record(value):
                    with EVENTS.open("a", encoding="utf-8") as handle:
                        handle.write(value + "\\n")

                class FakeMemo:
                    @staticmethod
                    def prewarm_real_repo_receipt(*, run_id, session_id):
                        side = "worker" if os.environ.get("PYTEST_XDIST_WORKER") else "controller"
                        record(f"prewarm-{{side}}")

                    @staticmethod
                    def finish_real_repo_receipt_session(*, session_id):
                        record("finish-controller")

                def pytest_sessionstart(session):
                    from orchestrator.tests import conftest as suite_conftest
                    suite_conftest._receipt_memo_module = lambda: FakeMemo

                __WORKER_HOOK__

                def pytest_xdist_node_collection_finished(node, ids):
                    record("controller-hook")
                """
        plugin_source = plugin_source.replace(
            "                __WORKER_HOOK__",
            textwrap.indent(
                _RECEIPT_ORDER_WORKER_HOOK_SOURCE.rstrip(), "                ",
            ),
        )
        (directory / "receipt_order_plugin.py").write_text(
            textwrap.dedent(plugin_source),
            encoding="utf-8",
        )
        env = os.environ.copy()
        for name in (
            "PYTEST_XDIST_WORKER", "PYTEST_XDIST_WORKER_COUNT",
            "PYTEST_XDIST_TESTRUNUID", "IZANAGI_RECEIPT_MEMO_NONCE",
        ):
            env.pop(name, None)
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in (
                str(directory), str(ROOT), env.get("PYTHONPATH", ""),
            ) if part
        )
        result = _run_subprocess(
            [
                sys.executable, "-m", "pytest", "-n", "1", "-q",
                "-p", "orchestrator.tests.conftest",
                "-p", "receipt_order_plugin",
                str(directory / "test_s8b_oracle_driver.py"),
            ],
            cwd=ROOT,
            env=env,
        )
        assert result.returncode == 0, (
            f"xdist order probe failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )
        trace = events.read_text(encoding="utf-8").splitlines()
    assert trace.count("worker-hook") == 1, trace
    assert trace.count("controller-hook") == 1, trace
    assert trace.count("prewarm-controller") == 1, trace
    assert trace.count("finish-controller") == 1, trace
    assert "prewarm-worker" not in trace, trace
    assert trace.index("worker-hook") < trace.index("controller-hook"), trace

    # 合成 worker payer を加えると exact payer assertion が赤になる。
    mutated = [*trace, "prewarm-worker"]
    try:
        assert "prewarm-worker" not in mutated
    except AssertionError:
        pass
    else:
        raise AssertionError("実順序 trace の worker payer 合成負例が通過した")


def test_receipt_memo_uid_configuration_respects_xdist_and_no_xdist():
    suite_conftest = _load_suite_conftest()
    first_session = _ReceiptHookConfig({})
    second_session = _ReceiptHookConfig({})
    try:
        suite_conftest._configure_receipt_memo_session(first_session)
        suite_conftest._configure_receipt_memo_session(second_session)
        first_token = getattr(
            first_session, suite_conftest._RECEIPT_MEMO_SESSION_ID_ATTR,
        )
        second_token = getattr(
            second_session, suite_conftest._RECEIPT_MEMO_SESSION_ID_ATTR,
        )
        assert len(first_token) == 32 and len(second_token) == 32
        assert first_token != second_token
    finally:
        suite_conftest._restore_receipt_memo_nonce(second_session)
        suite_conftest._restore_receipt_memo_nonce(first_session)

    explicit = _ReceiptHookConfig({
        "numprocesses": 4, "testrunuid": "ci-job-42",
    })
    suite_conftest._configure_receipt_memo_run_id(explicit)
    assert explicit.option.testrunuid == "ci-job-42"

    generated = _ReceiptHookConfig({"numprocesses": 4})
    suite_conftest._configure_receipt_memo_run_id(generated)
    assert len(generated.option.testrunuid) == 32
    assert all(char in "0123456789abcdef" for char in generated.option.testrunuid)

    no_xdist = _ReceiptHookConfig({})
    suite_conftest._configure_receipt_memo_run_id(no_xdist)
    assert not hasattr(no_xdist.option, "testrunuid")

    # 実 Config と同じく、default を省略した未宣言 option は ValueError。
    try:
        no_xdist.getoption("testrunuid")
    except ValueError:
        pass
    else:
        raise AssertionError("未宣言 xdist option が ValueError にならなかった")

    # 合成回帰: 明示 UID を上書きする configure は exact 値 assertion で赤になる。
    overwritten = "0" * 32
    try:
        assert overwritten == "ci-job-42"
    except AssertionError:
        pass
    else:
        raise AssertionError("testrunuid 上書きの合成負例が通過した")


def _receipt_call_owners(source: str) -> set[str]:
    """production resolver へ到達できる call の top-level owner を返す。"""
    tree = ast.parse(source)
    owners = set()
    candidates = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            candidates.append((None, statement))
        elif isinstance(statement, ast.ClassDef):
            candidates.extend(
                (statement.name, child)
                for child in statement.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
    for parent_class, function in candidates:
        resolver_names = {
            "_resolve_now", "_PRODUCTION_RESOLVE", "_resolve_t080_receipt",
        }

        def target_names(target):
            if isinstance(target, ast.Name):
                return {target.id}
            if isinstance(target, (ast.Tuple, ast.List)):
                return set().union(*(target_names(item) for item in target.elts))
            return set()

        def resolver_reference(node):
            if isinstance(node, ast.Name):
                return node.id in resolver_names
            if isinstance(node, ast.Attribute):
                return node.attr in {
                    "_resolve_now", "_PRODUCTION_RESOLVE", "_resolve_t080_receipt",
                }
            if not isinstance(node, ast.Call):
                return False
            if not (
                isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in {
                    "_resolve_now", "_PRODUCTION_RESOLVE", "_resolve_t080_receipt",
                }
            ):
                return False
            return True

        # 別名束縛は転送を含めて閉包にする。順序には依存させず保守的に検出する。
        assignments = []
        for node in ast.walk(function):
            if isinstance(node, ast.Assign):
                assignments.extend((target, node.value) for target in node.targets)
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                assignments.append((node.target, node.value))
            elif isinstance(node, ast.NamedExpr):
                assignments.append((node.target, node.value))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in resolver_names:
                        resolver_names.add(alias.asname or alias.name)
        changed = True
        while changed:
            changed = False
            for target, value in assignments:
                if resolver_reference(value):
                    before = len(resolver_names)
                    resolver_names.update(target_names(target))
                    changed = changed or len(resolver_names) != before

        if any(
            isinstance(node, ast.Call) and resolver_reference(node.func)
            for node in ast.walk(function)
        ):
            owners.add(
                f"{parent_class}.{function.name}"
                if parent_class else function.name
            )
    return owners


def _module_scope_receipt_imports(source: str) -> list[int]:
    class Scanner(ast.NodeVisitor):
        def __init__(self):
            self.lines = set()
            self.importlib_names = {"importlib"}
            self.import_module_names = {"import_module"}

        def visit_FunctionDef(self, node):
            return None

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef
        visit_Lambda = visit_FunctionDef

        def visit_Import(self, node):
            for alias in node.names:
                if alias.name.endswith("real_repo_receipt_memo"):
                    self.lines.add(node.lineno)
                if alias.name == "importlib":
                    self.importlib_names.add(alias.asname or alias.name)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                if alias.name == "real_repo_receipt_memo":
                    self.lines.add(node.lineno)
                if node.module == "importlib" and alias.name == "import_module":
                    self.import_module_names.add(alias.asname or alias.name)

        def visit_Assign(self, node):
            if (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id in self.importlib_names
                and node.value.attr == "import_module"
            ):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.import_module_names.add(target.id)
            self.generic_visit(node)

        def visit_Call(self, node):
            loader = False
            if isinstance(node.func, ast.Name):
                loader = (
                    node.func.id == "__import__"
                    or node.func.id in self.import_module_names
                )
            elif isinstance(node.func, ast.Attribute):
                loader = (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id in self.importlib_names
                    and node.func.attr == "import_module"
                )
            if (
                loader
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value.endswith("real_repo_receipt_memo")
            ):
                self.lines.add(node.lineno)
            self.generic_visit(node)

    scanner = Scanner()
    scanner.visit(ast.parse(source))
    return sorted(scanner.lines)


def test_receipt_memo_module_identity_and_resolver_caller_are_fixed():
    import importlib

    suite_conftest = _load_suite_conftest()
    canonical = importlib.import_module(
        "orchestrator.tests.real_repo_receipt_memo"
    )
    driver_tests = importlib.import_module(
        "orchestrator.tests.test_s8b_oracle_driver"
    )
    drift_tests = importlib.import_module(
        "orchestrator.tests.test_s8b_binding_driftguards"
    )
    identities = (
        suite_conftest._receipt_memo_module(),
        driver_tests.receipt_memo,
        drift_tests.receipt_memo,
    )
    assert all(module is canonical for module in identities)
    assert "real_repo_receipt_memo" not in sys.modules

    memo_source = (HERE / "real_repo_receipt_memo.py").read_text(encoding="utf-8")
    assert _receipt_call_owners(memo_source) == {
        "_resolve_now", "_ReceiptMemo.prewarm",
    }
    conftest_source = (HERE / "conftest.py").read_text(encoding="utf-8")
    assert _module_scope_receipt_imports(conftest_source) == []

    # 合成 identity 分裂と consumer-side resolver call は同じ guards が拒否する。
    split = (canonical, object(), canonical)
    try:
        assert all(module is canonical for module in split)
    except AssertionError:
        pass
    else:
        raise AssertionError("memo module identity 分裂の合成負例が通過した")
    synthetic_calls = {
        "alias": (
            "def real_repo_receipt():\n"
            "    alias = _PRODUCTION_RESOLVE\n"
            "    return alias(root=ROOT)\n"
        ),
        "getattr": (
            "def real_repo_receipt():\n"
            "    return getattr(module, '_PRODUCTION_RESOLVE')(root=ROOT)\n"
        ),
        "module-attribute": (
            "def real_repo_receipt():\n"
            "    return driver._resolve_t080_receipt(root=ROOT)\n"
        ),
        "direct": (
            "def real_repo_receipt():\n"
            "    return _PRODUCTION_RESOLVE(root=ROOT)\n"
        ),
    }
    for label, synthetic in synthetic_calls.items():
        assert _receipt_call_owners(synthetic) == {"real_repo_receipt"}, label
    eager_import = "from orchestrator.tests import real_repo_receipt_memo\n"
    assert _module_scope_receipt_imports(eager_import) == [1]
    dynamic_imports = {
        "importlib": (
            "import importlib\n"
            "memo = importlib.import_module("
            "'orchestrator.tests.real_repo_receipt_memo')\n"
        ),
        "alias": (
            "from importlib import import_module as load\n"
            "memo = load('orchestrator.tests.real_repo_receipt_memo')\n"
        ),
        "dunder": "memo = __import__('orchestrator.tests.real_repo_receipt_memo')\n",
    }
    for label, synthetic in dynamic_imports.items():
        assert _module_scope_receipt_imports(synthetic), label


def test_receipt_memo_consumers_do_not_resolve_during_collection():
    """2 consumer file の実 collect-only 中は production resolver を呼ばない。"""
    _require_pytest()
    script = textwrap.dedent(
        f"""
        import pytest
        from orchestrator.campaign import s8b_oracle_driver as driver

        calls = []
        def fake_resolver(*, root):
            calls.append(str(root))
            return object()
        driver._resolve_t080_receipt = fake_resolver
        rc = pytest.main([
            "--collect-only", "-q",
            {str(HERE / 'test_s8b_oracle_driver.py')!r},
            {str(HERE / 'test_s8b_binding_driftguards.py')!r},
        ])
        collected_calls = len(calls)
        from orchestrator.tests import real_repo_receipt_memo as memo
        control = memo._make_receipt_memo(resolve=lambda: fake_resolver(root=memo.ROOT))
        control.prewarm(run_id=None)
        print(f"RECEIPT_COLLECTION_CALLS={{collected_calls}} CONTROL={{len(calls) - collected_calls}}")
        raise SystemExit(rc)
        """
    )
    result = _run_subprocess(
        [sys.executable, "-c", script], cwd=ROOT, env=os.environ.copy(),
    )
    assert result.returncode == 0, (
        f"consumer collection probe failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "RECEIPT_COLLECTION_CALLS=0 CONTROL=1" in result.stdout, result.stdout


def test_sort_swo_oracle_does_not_resolve_during_collection():
    """sort SWO oracle の collect-only 中は production resolver を呼ばない。"""
    _require_pytest()
    script = textwrap.dedent(
        f"""
        import pytest
        from orchestrator.campaign import sort_swo_oracle as oracle

        calls = []
        def fake_resolver(*args, **kwargs):
            calls.append((args, kwargs))
            return object()
        oracle.resolve_oracle_environment = fake_resolver
        rc = pytest.main([
            "--collect-only", "-q",
            {str(HERE / "test_sort_swo_oracle.py")!r},
        ])
        collected_calls = len(calls)
        oracle.resolve_oracle_environment("positive-control")
        print(
            f"SORT_SWO_COLLECTION_CALLS={{collected_calls}} "
            f"CONTROL={{len(calls) - collected_calls}}"
        )
        raise SystemExit(rc)
        """
    )
    result = _run_subprocess(
        [sys.executable, "-c", script], cwd=ROOT, env=os.environ.copy(),
    )
    assert result.returncode == 0, (
        f"sort SWO collection probe failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "SORT_SWO_COLLECTION_CALLS=0 CONTROL=1" in result.stdout, result.stdout


def _require_loadgroup_capability() -> None:
    _require_pytest()
    try:
        version = metadata.version("pytest-xdist")
    except metadata.PackageNotFoundError:
        skip("pytest-xdist 不在 — live loadgroup scheduler control を実行できない")
    try:
        supported = Version(version) >= Version("2.5")
    except InvalidVersion:
        supported = False
    if not supported:
        skip(f"pytest-xdist {version} は loadgroup 非対応 (<2.5)")


def _worker_evidence(path: Path) -> tuple[str, str]:
    return (
        (path / "a.worker").read_text(encoding="utf-8"),
        (path / "b.worker").read_text(encoding="utf-8"),
    )


def test_loadgroup_scheduler_keeps_same_group_on_one_worker_and_control_detects_absence():
    """loadgroup の同一 worker 証拠と、option 無しなら歯が発火する対照を実走する。"""
    _require_loadgroup_capability()
    with tempfile.TemporaryDirectory(prefix="izanagi-loadgroup-live-") as raw_tmp:
        tmp = Path(raw_tmp)
        suite = tmp / "test_group_probe.py"
        suite.write_text(
            textwrap.dedent(
                """
                import os
                from pathlib import Path
                import pytest

                def _record(name):
                    out = Path(os.environ["IZANAGI_GROUP_PROBE_OUT"])
                    out.mkdir(parents=True, exist_ok=True)
                    (out / f"{name}.worker").write_text(
                        os.environ["PYTEST_XDIST_WORKER"], encoding="utf-8",
                    )

                @pytest.mark.xdist_group("probe")
                def test_group_a():
                    _record("a")
                    out = Path(os.environ["IZANAGI_GROUP_PROBE_OUT"])
                    (out / "fifo.sentinel").write_text("a", encoding="utf-8")

                @pytest.mark.xdist_group("probe")
                def test_group_b():
                    out = Path(os.environ["IZANAGI_GROUP_PROBE_OUT"])
                    if os.environ.get("IZANAGI_ENFORCE_GROUP_FIFO"):
                        assert (out / "fifo.sentinel").read_text(
                            encoding="utf-8",
                        ) == "a"
                    _record("b")
                """
            ),
            encoding="utf-8",
        )

        grouped_out = tmp / "grouped"
        grouped_env = os.environ.copy()
        grouped_env["IZANAGI_GROUP_PROBE_OUT"] = str(grouped_out)
        grouped_env["IZANAGI_ENFORCE_GROUP_FIFO"] = "1"
        grouped = _run_subprocess(
            [
                sys.executable, "-m", "pytest", "-q", "-n", "2",
                "--dist", "loadgroup", str(suite),
            ],
            cwd=tmp,
            env=grouped_env,
        )
        assert grouped.returncode == 0, (
            f"loadgroup probe failed:\nstdout={grouped.stdout}\nstderr={grouped.stderr}"
        )
        grouped_workers = _worker_evidence(grouped_out)
        assert grouped_workers[0] == grouped_workers[1], grouped_workers

        # Negative control: --dist loadgroup だけを外す。同じ 2 node が別 worker に
        # 分かれ、worker 証拠比較が実際に不一致を検出できることを固定する。
        control_out = tmp / "control"
        control_env = os.environ.copy()
        control_env["IZANAGI_GROUP_PROBE_OUT"] = str(control_out)
        control_env.pop("IZANAGI_ENFORCE_GROUP_FIFO", None)
        control = _run_subprocess(
            [sys.executable, "-m", "pytest", "-q", "-n", "2", str(suite)],
            cwd=tmp,
            env=control_env,
        )
        assert control.returncode == 0, (
            f"load scheduler control failed:\nstdout={control.stdout}\n"
            f"stderr={control.stderr}"
        )
        control_workers = _worker_evidence(control_out)
        assert control_workers[0] != control_workers[1], (
            "negative control が worker 分離を検出しなかった: "
            f"{control_workers!r}"
        )


def test_effective_tempdir_is_not_tmpfs():
    """実効一時ディレクトリが tmpfs 族に無いこと (tmpfs はメモリ枠を直接食う)。

    ``tempfile.gettempdir()`` は自プロセス (pytest の ``tmp_path`` を含む) の置き場、
    ``TMPDIR`` は env を継承する subprocess の置き場。片方だけ健全でも足りない。
    fstype を 1 つも判定できないときだけ skip する (skip 条件を反転させない)。

    tmpfs を掴んだときの倒し方を 2 つに分ける (段 6 レビュー W2 の裁定):

    - **明示 ``TMPDIR`` が tmpfs → 赤。** ユーザーまたは結線が選んだ結果なので退行。
    - **``TMPDIR`` 未設定で環境既定が tmpfs → skip。** ``/tmp`` が tmpfs な distro
      (systemd 既定構成) では本 repo が何もしなくてもそうなる。無過失の赤にしない。

    **この分岐で落ちる検出力 (正直な記述)**: ``TMPDIR`` 未設定の環境では、既定の
    一時領域が tmpfs でも本 node は赤にならない。つまり「conftest が TMPDIR を
    設定しない」という本 repo の選択が、そういう distro で結果的にメモリ枠を
    食う構成になる事象は、本 node では捕まえられず skip 理由として出るだけである。
    捕まえるのは (1) 明示 ``TMPDIR`` が tmpfs な場合と、(2) source 上の結線
    (``test_suite_conftest_does_not_wire_tmpdir_to_tmpfs``、こちらは環境に依らず
    常に赤にできる) の 2 面で、M1 (conftest 末尾に ``setdefault("TMPDIR", "/dev/shm")``)
    のような結線退行は (2) が環境非依存で殺す。
    """
    checked = []
    offenders = []
    default_tmpfs = []
    for path, explicit in _effective_tmpdir_candidates():
        status, fstype = _tmpdir_verdict(path)
        if status == "unknown":
            continue
        checked.append((path, fstype))
        if status != "tmpfs":
            continue
        if explicit:
            offenders.append((path, fstype))
        else:
            default_tmpfs.append((path, fstype))
    if not checked:
        skip("/proc/self/mountinfo から実効一時ディレクトリの fstype を判定できない")
    assert not offenders, (
        "明示された TMPDIR が tmpfs 族にある — 使用量がユーザーの memory cgroup へ "
        "1:1 で課金される (Pegasus ログインノードの枠は 16 GiB、受入全走 1 回の "
        f"tmpfs peak は 7.39 GiB 実測): offenders={offenders!r} checked={checked!r}"
    )
    if default_tmpfs:
        detail = ", ".join(
            f"{path} (realpath={os.path.realpath(path)}, fstype={fstype})"
            for path, fstype in default_tmpfs
        )
        skip(
            "環境既定の一時領域が tmpfs である。ディスク上の TMPDIR を明示せよ "
            f"(tmpfs はユーザーの memory cgroup へ 1:1 で課金される): {detail}"
        )


def test_suite_conftest_does_not_wire_tmpdir_to_tmpfs():
    """conftest が一時領域を tmpfs へ結線していないこと (撤去した誘導の再発検出)。

    ``TMPDIR`` (env、subprocess へ継承) と ``tempfile.tempdir`` (in-process、``tmp_path``
    と ``tempfile.*``) の両方を見る。後者は env に出ないので実効 fstype 検査からは
    「環境既定」に見えてしまい、source 検査だけが殺せる (段 6 レビュー N2)。
    """
    source = (HERE / "conftest.py").read_text(encoding="utf-8")
    hits = find_tmpfs_tmpdir_wiring(source)
    assert not hits, (
        "conftest.py が一時領域を tmpfs へ向けている (メモリ枠へ課金される): "
        f"{hits!r}"
    )


def test_tmpdir_fstype_lookup_positive_and_negative_control():
    """合成 mount 表で ``_tmpdir_verdict`` の正負両方向と realpath 依存を固定する。

    合成表だけでは ``mountinfo_text`` を必ず明示で渡すため、実 ``/proc/self/mountinfo``
    を読む枝 (``mountinfo_text is None``) に一度も対照が掛からない。その枝が壊れると
    実効 fstype 検査は赤ではなく skip へ化けるので、実経路の対照を先に置く (段 6 MX2)。
    """
    # 実経路の対照: Linux では `/` の fstype は必ず判定できる。ここが None に落ちる
    # 実装は、実効 fstype 検査を「判定不能 → skip」で無言に通してしまう。
    if sys.platform.startswith("linux"):
        assert _fs_type("/") is not None, (
            "実 /proc/self/mountinfo 経路が判定不能に落ちている — この状態では "
            "test_effective_tempdir_is_not_tmpfs が赤ではなく skip へ化ける"
        )
    # 実経路の tmpfs 正例 (段 6 レビュー N3)。上の "None でない" 対照は、実読取枝が
    # tmpfs 行だけを落とす部分劣化を素通りする — 最長前方一致が `/` の実ディスクへ
    # 落ちるので "unknown" にすらならず、明示 tmpfs TMPDIR が偽緑で通る。
    if os.path.isdir("/dev/shm"):
        assert _fs_type("/dev/shm") in _TMPFS_FSTYPES, (
            "実 /proc/self/mountinfo 経路が tmpfs を tmpfs と判定できていない — "
            "この状態では明示 tmpfs TMPDIR が偽緑で通る: "
            f"actual={_fs_type('/dev/shm')!r}"
        )
    mountinfo = textwrap.dedent(
        """\
        30 1 9:0 / / rw,relatime shared:1 - xfs /dev/md0 rw,noquota
        26 30 0:5 / /dev rw,nosuid - devtmpfs devtmpfs rw,size=4096k
        32 26 0:27 / /dev/shm rw,nosuid,nodev shared:4 - tmpfs tmpfs rw,inode64
        41 26 0:33 / /dev/hugepages rw,relatime shared:17 - hugetlbfs hugetlbfs rw,pagesize=2M
        44 28 0:44 / /run/user/31609 rw,nosuid,nodev - tmpfs tmpfs rw,size=13421772k
        55 30 0:55 / /odd\\040name rw - tmpfs tmpfs rw
        60 30 0:60 / /scr rw,relatime - xfs /dev/sdb1 rw
        """
    )
    # 赤にできること (tmpfs 族を実際に検出する)。最長前方一致と 8 進エスケープ込み。
    tmpfs_cases = (
        ("/dev/shm", "tmpfs"),
        ("/dev/shm/sub/dir", "tmpfs"),
        ("/run/user/31609/x", "tmpfs"),
        ("/dev", "devtmpfs"),
        # 計算ノード bnode041 に実在する hugetlbfs (/dev/hugepages)。これもメモリ実体。
        ("/dev/hugepages/x", "hugetlbfs"),
        ("/odd name/x", "tmpfs"),
    )
    for path, expected in tmpfs_cases:
        assert _tmpdir_verdict(path, mountinfo, resolve=False) == ("tmpfs", expected), path
    # 過剰拒否しないこと (実ディスクを tmpfs と誤判定しない)。
    disk_cases = (
        ("/tmp", "xfs"),
        ("/scr/874750", "xfs"),
        ("/home/u/x", "xfs"),
        ("/dev-shm", "xfs"),
        ("/run/user-data", "xfs"),
        ("/odd nameish", "xfs"),
    )
    for path, expected in disk_cases:
        assert _tmpdir_verdict(path, mountinfo, resolve=False) == ("ok", expected), path
    # 判定不能は "unknown" (ここでだけ skip してよい状態)。
    assert _tmpdir_verdict("/tmp", "not a mountinfo table") == ("unknown", None)
    assert _tmpdir_verdict("/tmp", "") == ("unknown", None)

    # realpath が load-bearing であることの対照: symlink 越しの tmpfs を取り逃さない。
    base = os.path.realpath(tempfile.mkdtemp(prefix="izanagi-fstype-control-"))
    try:
        real = os.path.join(base, "real")
        link = os.path.join(base, "link")
        os.mkdir(real)
        os.symlink(real, link)
        synthetic = (
            f"70 1 0:70 / {base} rw - xfs /dev/sdc1 rw\n"
            f"71 70 0:71 / {real} rw - tmpfs tmpfs rw\n"
        )
        assert _tmpdir_verdict(link, synthetic) == ("tmpfs", "tmpfs")
        assert _tmpdir_verdict(link, synthetic, resolve=False) == ("ok", "xfs")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_tmpfs_tmpdir_wiring_scanner_positive_and_negative_control():
    """``find_tmpfs_tmpdir_wiring`` が結線を実際に捕まえ、無関係な記述を誤検出しない。"""
    # 赤にできること。撤去前の conftest が使っていた「定数経由の間接代入」を含む。
    positives = (
        'import os\nos.environ["TMPDIR"] = "/dev/shm"\n',
        'import os\nos.environ.setdefault("TMPDIR", "/dev/shm")\n',
        'import os\n_SHM = "/dev/shm"\nos.environ["TMPDIR"] = _SHM\n',
        'import os\nos.environ["TMPDIR"] = "/run/user/31609/izanagi"\n',
        'import os\nos.putenv("TMPDIR", "/run/shm")\n',
        'import os\nos.environ.update({"TMPDIR": "/dev/shm"})\n',
        'import os\nos.environ.update(TMPDIR="/dev/shm")\n',
        'import os\njob = "1"\nos.environ["TMPDIR"] = f"/dev/shm/izanagi-{job}"\n',
        'from os import environ\nenviron["TMPDIR"] = "/dev/shm"\n',
        # env を経由しない in-process 結線 (段 6 レビュー N2)。これを見ないと
        # tmp_path と tempfile.* がまるごと tmpfs へ戻る変異が全緑で通る。
        'import tempfile\ntempfile.tempdir = "/dev/shm"\n',
        'import tempfile as tf\ntf.tempdir = "/run/shm"\n',
        'import tempfile\n_SHM = "/dev/shm"\ntempfile.tempdir = _SHM\n',
        'import tempfile\ntempfile.tempdir: str = "/dev/shm/izanagi"\n',
    )
    for source in positives:
        assert find_tmpfs_tmpdir_wiring(source), source
    # 過剰拒否しないこと。
    negatives = (
        '"""/dev/shm へは向けない、という説明だけの docstring。"""\n',
        'import os\n# os.environ["TMPDIR"] = "/dev/shm"  # 撤去済み\n',
        'import os\nos.environ["TMPDIR"] = "/scr/874750"\n',
        'import os\nos.environ["OTHER"] = "/dev/shm"\n',
        'import os\nshm = os.environ.get("TMPDIR", "/dev/shm")\n',
        'import os\nos.environ.setdefault("TMPDIR", "/tmp")\n',
        # 撤去前の conftest が実際に使っていた形。既定へ戻すだけなので hit にしない。
        'import tempfile\ntempfile.tempdir = None\n',
        'import tempfile\ntempfile.tempdir = "/scr/874750"\n',
        'import tempfile\nsaved = tempfile.tempdir\n',
    )
    for source in negatives:
        assert find_tmpfs_tmpdir_wiring(source) == [], source
    # 現行 conftest は negative 側であること (本番 source での対照)。
    # test_suite_conftest_does_not_wire_tmpdir_to_tmpfs と検査内容は重なるが、あちらは
    # 「conftest が汚れたら赤」、こちらは「scanner が本番 source で誤検出しない」の対照。
    conftest_hits = find_tmpfs_tmpdir_wiring(
        (HERE / "conftest.py").read_text(encoding="utf-8"))
    assert conftest_hits == [], (
        "本番 source (conftest.py) に対する scanner の対照が hit した — conftest が "
        "TMPDIR を tmpfs へ結線したか、scanner が誤検出している: "
        f"{conftest_hits!r}"
    )


# tmpfs 回帰ガード node と、その node 内で load-bearing な token。関数の外に置くのは
# 自己適用を恒真にしないため — 関数内の dict リテラルだと、自分自身の token 検査が
# 「dict にその文字列が書いてあるから通る」だけになる。
_TMPFS_GUARD_TOKENS = {
    "test_effective_tempdir_is_not_tmpfs": (
        "_tmpdir_verdict(", "assert not offenders",
    ),
    "test_suite_conftest_does_not_wire_tmpdir_to_tmpfs": (
        "find_tmpfs_tmpdir_wiring(", "assert not hits",
    ),
    "test_tmpdir_fstype_lookup_positive_and_negative_control": (
        # '_fs_type("/dev/shm")' は実 mountinfo 経路の tmpfs 正例 (段 6 レビュー N3)。
        # "None でない" だけの対照は tmpfs 行を落とす部分劣化を素通りする。
        "_tmpdir_verdict(", '_fs_type("/")', '_fs_type("/dev/shm")',
    ),
    "test_tmpfs_tmpdir_wiring_scanner_positive_and_negative_control": (
        # "tempfile.tempdir" は env を経由しない in-process 結線の対照 (段 6 レビュー N2)。
        "find_tmpfs_tmpdir_wiring(", "tempfile.tempdir",
    ),
    # 自己適用: この node 自身が「述語を実行する positive control」を持つこと。
    # "PYTEST_CURRENT_TEST" は分類器の対照 (段 6 レビュー N1) — これを失うと本 node が
    # pytest 下で無言に SKIP へ化け、以降の control が自動経路で一度も走らなくなる。
    "test_tmpdir_guards_are_present_and_load_bearing": (
        "_run_and_classify(", "_patched_module_attr(", "PYTEST_CURRENT_TEST",
    ),
}


def _patched_module_attr(name: str, replacement):
    """本 module の属性を差し替える (ガード node が参照する述語の注入口)。"""
    return mock.patch.object(sys.modules[__name__], name, replacement)


def _skip_exception_types() -> tuple[type[BaseException], ...]:
    """``skiputil.skip`` が投げうる例外型を実行環境に応じて集める。

    ``skiputil.skip`` は ``PYTEST_CURRENT_TEST`` があると ``pytest.skip`` を呼ぶ。その
    ``_pytest.outcomes.Skipped`` の MRO は ``Skipped → OutcomeException → BaseException``
    で **``Exception`` 派生ではない**。``except Skip`` にも ``except Exception`` にも
    掛からないので、捕り漏らすと注入した control の skip が呼出し側を貫通し、
    **ガード node 自身が pytest 下で必ず SKIP へ化ける** (= control (2) 以降が自動経路で
    一度も走らない)。段 6 レビュー N1 が受入全走の 4202/19 → 4201/20 で実証した退行。

    pytest 不在環境 (素の runner) でも壊れないよう遅延 import で解決し、無ければ
    ``Skip`` だけを対象にする。
    """
    types: list[type[BaseException]] = [Skip]
    try:
        import pytest
    except ImportError:
        return tuple(types)
    skipped = getattr(pytest.skip, "Exception", None)
    if isinstance(skipped, type) and issubclass(skipped, BaseException):
        types.append(skipped)
    return tuple(types)


def _run_and_classify(function) -> str:
    """テスト関数を実行し ``"pass"`` / ``"fail"`` / ``"skip"`` のどれかを返す。"""
    try:
        function()
    except _skip_exception_types():
        return "skip"
    except AssertionError:
        return "fail"
    return "pass"


def test_tmpdir_guards_are_present_and_load_bearing():
    """tmpfs 回帰ガードが実際に赤くできることを、述語を注入して実行し固定する。

    文字列 pin だけでは意味的な骨抜きを通す — 要求 token を全部残したまま
    ``offenders.append`` を殺すと 5 node 全緑のまま実効ガードだけが死ぬ (段 6 レビューが
    変異ハーネスで実証、MX3)。そこで tmpfs を返す述語を注入してガード node を実際に
    実行し、赤 (明示 TMPDIR) と skip (環境既定、W2 の分岐) に倒れることを検査する。
    文字列 pin は削除・素朴な恒真化を早期に名指しするための補助として残す。

    自己適用: 本 node 自身も ``_TMPFS_GUARD_TOKENS`` に載せ、positive control を捨てて
    文字列 pin だけへ戻す退行を検出する。ただし 5 node を**同時に**全部消す変異は、
    検出する側もろとも消えるのでここでは捕まえられない
    (``test_plain_runner_coverage.py`` の自己適用 node と同じ限界)。
    """
    source_text = Path(__file__).resolve().read_text(encoding="utf-8")
    for name, tokens in sorted(_TMPFS_GUARD_TOKENS.items()):
        function = globals().get(name)
        assert callable(function), f"tmpfs 回帰ガード node が消えている: {name}"
        assert f"def {name}(" in source_text, (
            f"tmpfs 回帰ガード node が本ファイルの定義として存在しない: {name}"
        )
        source = inspect.getsource(function)
        for token in tokens:
            assert token in source, (
                f"{name} の load-bearing な検査が失われている (恒真化): {token!r}"
            )
    # skip 条件の反転禁止: 判定不能のときだけ skip する形であること。
    effective = inspect.getsource(globals()["test_effective_tempdir_is_not_tmpfs"])
    assert 'status == "unknown"' in effective and "if not checked:" in effective, (
        "実効 fstype 検査の skip 条件が『判定不能のときだけ』でなくなっている"
    )

    # --- 述語を実行する positive control (文字列 pin では殺せない骨抜き用) -------------
    # (0) 分類器そのものの対照。(1)〜(4) は注入した述語が ``skiputil.skip`` を呼ぶ経路を
    #     通るが、pytest 下ではそれが ``Exception`` 派生でない ``Skipped`` になる。
    #     ``_run_and_classify`` が捕り漏らすと本 node 自身が SKIP へ化け、以降の control が
    #     一度も実行されない (段 6 レビュー N1 が受入全走で実証)。ここで先に殺す。
    def raises_suite_skip():
        skip("classifier control")

    try:
        import pytest as pytest_for_control
    except ImportError:
        pytest_for_control = None
    if pytest_for_control is not None:
        with mock.patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "control (call)"}):
            try:
                outcome = _run_and_classify(raises_suite_skip)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as exc:  # noqa: BLE001
                # 貫通をここで捕らえて赤へ変換する。捕らえないと本 node ごと SKIP へ
                # 化けて退行が無言になる (N1 の退行そのものの再現になってしまう)。
                outcome = f"escaped:{type(exc).__name__}"
        assert outcome == "skip", (
            "_run_and_classify が pytest 経路の skip を skip として分類できていない — "
            "この状態では本 node が pytest 下で必ず SKIP になり、以下の control が "
            f"自動経路で一度も実行されない: {outcome}"
        )

    def tmpfs_verdict(*args, **kwargs):
        return ("tmpfs", "tmpfs")

    def disk_verdict(*args, **kwargs):
        return ("ok", "xfs")

    def wiring_hit(source):
        return [(1, "/dev/shm")]

    def wiring_clean(source):
        return []

    # (1) 明示 TMPDIR が tmpfs 判定 → 赤。offenders 収集や assert を殺すとここが落ちる。
    with mock.patch.dict(os.environ, {"TMPDIR": "/dev/shm"}), \
            _patched_module_attr("_tmpdir_verdict", tmpfs_verdict):
        outcome = _run_and_classify(test_effective_tempdir_is_not_tmpfs)
    assert outcome == "fail", (
        f"実効 fstype 検査が明示 TMPDIR の tmpfs 入力で赤にならない (恒真化): {outcome}"
    )

    # (2) TMPDIR 未設定 + 環境既定が tmpfs → skip (W2 の分岐が生きていること)。
    with mock.patch.dict(os.environ), \
            _patched_module_attr("_tmpdir_verdict", tmpfs_verdict):
        os.environ.pop("TMPDIR", None)
        outcome = _run_and_classify(test_effective_tempdir_is_not_tmpfs)
    assert outcome == "skip", (
        f"環境既定が tmpfs のとき W2 の skip 分岐が働いていない: {outcome}"
    )

    # (3) 実ディスク判定なら緑 (恒真に赤くして「検出している」と見せる形の排除)。
    with mock.patch.dict(os.environ, {"TMPDIR": "/scr/izanagi"}), \
            _patched_module_attr("_tmpdir_verdict", disk_verdict):
        outcome = _run_and_classify(test_effective_tempdir_is_not_tmpfs)
    assert outcome == "pass", (
        f"実効 fstype 検査が実ディスクの入力で緑にならない (過剰拒否): {outcome}"
    )

    # (4) conftest 結線検査: hit があれば赤、無ければ緑。hits 判定を殺すと (4a) が落ちる。
    with _patched_module_attr("find_tmpfs_tmpdir_wiring", wiring_hit):
        outcome = _run_and_classify(test_suite_conftest_does_not_wire_tmpdir_to_tmpfs)
    assert outcome == "fail", (
        f"conftest 結線検査が hit 入力で赤にならない (恒真化): {outcome}"
    )
    with _patched_module_attr("find_tmpfs_tmpdir_wiring", wiring_clean):
        outcome = _run_and_classify(test_suite_conftest_does_not_wire_tmpdir_to_tmpfs)
    assert outcome == "pass", (
        f"conftest 結線検査が hit 無しの入力で緑にならない (過剰拒否): {outcome}"
    )


def _run() -> int:
    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


enforce_held_functions(globals(), __file__, plain_runner="manual")


if __name__ == "__main__":
    sys.exit(_run())
