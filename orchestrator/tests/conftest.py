"""orchestrator/tests 共通 pytest 設定 — TMPDIR は設定しない。

かつてここは TMPDIR を tmpfs (``/dev/shm``) へ向けていたが撤去した。tmpfs の
使用量はユーザーの memory cgroup へほぼ 1:1 で課金され、Pegasus ログインノード
のユーザーメモリ枠 16 GiB (cgroup v2 ``memory.max`` = 17179869184) を直接削る。
受入全走 1 回の tmpfs peak は 7.39 GiB (計算ノード bnode033、request 874750 実測)
なので、ログインノードで 2 回走らせれば枠を使い切る。

代替の TMPDIR 注入は置かない。TMPDIR 未設定なら環境既定 (``/tmp``) を使う。
実ディスクにした代償は場所で大きく違う。断定を避けて実測値を分けて書く。

- **計算ノードでは小さい。** 300 回の write+fsync が ``/tmp`` で 0.026 秒、
  ``/dev/shm`` で 0.001 秒、Lustre (``/home``) で 0.42 秒 (bnode021、loadavg 0.29、
  3 走同値)。計算ノード bnode041 の ``/tmp`` の fstype は xfs (magic 58465342)
- **ログインノード直叩きでは大きい。** 共有・loadavg 高の pegasus02 では 300 回の
  write+fsync が ``/tmp`` 8.7〜9.4 秒、``/dev/shm`` 0.002 秒、``/home`` (Lustre)
  0.435〜0.447 秒。テストスイート実測でも ``orchestrator/tests/test_campaign.py``
  (168 node) が ``TMPDIR=/dev/shm`` で 2.21 秒、``TMPDIR=/tmp`` で 12.33 秒 (5.6 倍)

fsync を呼ぶコード経路は変えていない (検査は弱めない) — tmpfs 上で no-op だった
バリアが実バリアに戻るだけである。上の 168 node 実測でも fsync 回数は両方とも
620 回で完全に一致した。遅さが気になる場所ではディスク上の速い TMPDIR を明示せよ。

- 明示的な TMPDIR はユーザー指定として尊重し、ここでは何もしない (元から不干渉)
- 一時 dir を速い局所ディスクへ置きたい場合は TMPDIR を明示的に与える。ただし
  tmpfs を選んではいけない — 実効 TMPDIR の fstype は
  ``test_real_repo_serialization.py`` の回帰ガードが検査して赤にする
- 素の python3 実行 (二重 runner) は元から conftest を経由しない
"""
import contextlib
import errno
import fcntl
import hashlib
import json
import math
import os
import shutil
import stat
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType, SimpleNamespace
from typing import Callable, Iterable, Mapping, Sequence

import pytest

try:
    from orchestrator import test_selection_contract as _SELECTION_CONTRACT
except ModuleNotFoundError as exc:
    # failure-digest の plain-import probe は repo root を sys.path へ足さない。
    if exc.name not in {"orchestrator", "orchestrator.test_selection_contract"}:
        raise
    _SELECTION_CONTRACT = None


try:
    from orchestrator.tests.growth_test_holds import (
        GROWTH_TEST_HOLDS,
        RUN_GROWTH_HELD_TESTS_ENV,
        RUN_GROWTH_HELD_TESTS_TOKEN,
        mark_pytest_session_enforcing,
        unmark_pytest_session_enforcing,
    )
except ModuleNotFoundError as exc:
    # failure-digest の plain-import probe は repo root を sys.path へ足さずに
    # この conftest だけを読む。pytest hook を使わないその経路では、保留機構の
    # package import を遅延し、digest の fail-open 契約を保つ。
    if exc.name != "orchestrator":
        raise
    GROWTH_TEST_HOLDS = None
    RUN_GROWTH_HELD_TESTS_ENV = None
    RUN_GROWTH_HELD_TESTS_TOKEN = None
    mark_pytest_session_enforcing = None
    unmark_pytest_session_enforcing = None


def _ensure_growth_test_holds_loaded() -> None:
    """Load the hold contract before any pytest hook consumes it."""
    global GROWTH_TEST_HOLDS
    global RUN_GROWTH_HELD_TESTS_ENV
    global RUN_GROWTH_HELD_TESTS_TOKEN
    global mark_pytest_session_enforcing
    global unmark_pytest_session_enforcing

    if GROWTH_TEST_HOLDS is not None:
        return
    from orchestrator.tests.growth_test_holds import (
        GROWTH_TEST_HOLDS as holds,
        RUN_GROWTH_HELD_TESTS_ENV as env_name,
        RUN_GROWTH_HELD_TESTS_TOKEN as env_token,
        mark_pytest_session_enforcing as mark_enforcing,
        unmark_pytest_session_enforcing as unmark_enforcing,
    )

    GROWTH_TEST_HOLDS = holds
    RUN_GROWTH_HELD_TESTS_ENV = env_name
    RUN_GROWTH_HELD_TESTS_TOKEN = env_token
    mark_pytest_session_enforcing = mark_enforcing
    unmark_pytest_session_enforcing = unmark_enforcing


try:
    from orchestrator.tests.flaky_test_holds import (
        FLAKY_TEST_HOLDS,
        FLAKY_TEST_HOLD_NODE_IDS,
        FLAKY_TEST_HOLDS_SHA256,
        flaky_test_hold_registry_sha256,
    )
except ModuleNotFoundError as exc:
    # Keep the plain-import probe below the package root lazy, just like the
    # existing growth-hold registry.  A normal pytest collection imports the
    # package and therefore validates the registry before collection starts.
    if exc.name != "orchestrator":
        raise
    FLAKY_TEST_HOLDS = None
    FLAKY_TEST_HOLD_NODE_IDS = None
    FLAKY_TEST_HOLDS_SHA256 = None
    flaky_test_hold_registry_sha256 = None


def _ensure_flaky_test_holds_loaded() -> None:
    """Load and validate the flaky-node registry before a pytest hook uses it."""
    global FLAKY_TEST_HOLDS
    global FLAKY_TEST_HOLD_NODE_IDS
    global FLAKY_TEST_HOLDS_SHA256
    global flaky_test_hold_registry_sha256

    if FLAKY_TEST_HOLDS is not None:
        return
    from orchestrator.tests.flaky_test_holds import (
        FLAKY_TEST_HOLDS as holds,
        FLAKY_TEST_HOLD_NODE_IDS as node_ids,
        FLAKY_TEST_HOLDS_SHA256 as registry_sha256,
        flaky_test_hold_registry_sha256 as digest,
    )

    FLAKY_TEST_HOLDS = holds
    FLAKY_TEST_HOLD_NODE_IDS = node_ids
    FLAKY_TEST_HOLDS_SHA256 = registry_sha256
    flaky_test_hold_registry_sha256 = digest


@pytest.fixture
def _detect_site_under_test():
    """Allow site-policy unit tests to exercise the real detector explicitly."""


@pytest.fixture
def ratified_enforcement_source() -> None:
    """Compatibility fixture: closure ratification has been retired."""


@pytest.fixture
def valid_reservation_environment() -> dict[str, str]:
    """Return one live, internally consistent Pegasus reservation binding."""
    requested_s = 7200
    scheduler_started_epoch = time.time() - 60
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(
        encoding="ascii"
    ).strip()
    return {
        "PBS_JOBID": "987654.pegasus",
        "IZANAGI_RESERVATION_JOB_ID": "987654.pegasus",
        "IZANAGI_RESERVATION_REQUESTED_S": str(requested_s),
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(
            scheduler_started_epoch
        ),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(
            scheduler_started_epoch + requested_s
        ),
        "IZANAGI_RESERVATION_HOST": "test-host",
        "IZANAGI_RESERVATION_BOOT_ID": boot_id,
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "a" * 64,
        "IZANAGI_RESERVATION_NONCE": "fixture-nonce",
    }


@pytest.fixture
def _activate_synthetic_env_authority(monkeypatch):
    """合成契約を registry と activation record の正規経路で認可する。"""
    from orchestrator.campaign import env_contract as ec
    from orchestrator.campaign import env_contract_activation as activation

    def activate(contract, *, repo_root: Path, authority_dir: Path):
        root = Path(repo_root).resolve()
        directory = Path(authority_dir).resolve()
        entry = ec.GenerationEntry(generation=1, contract=contract)
        generations = MappingProxyType({contract.env_tag: (entry,)})
        ec.validate_generations(generations)
        catalog = MappingProxyType({
            contract.env_tag: ((1, contract.contract_sha256),),
        })
        record = activation.build_activation_record(
            activation_serial=1,
            previous_activation_state_sha256=None,
            active_contracts=(activation.ActiveContract(
                env_tag=contract.env_tag,
                generation=1,
                contract_sha256=contract.contract_sha256,
            ),),
        )
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "00000001.json").write_bytes(
            activation.canonical_record_bytes(record) + b"\n"
        )

        monkeypatch.setattr(ec, "GENERATIONS", generations)
        monkeypatch.setattr(ec, "_REGISTERED_CONTRACT_CATALOG", catalog)
        monkeypatch.setattr(
            ec, "_CONTRACT_SHA256_INDEX",
            ec._build_contract_sha256_index(generations),
        )
        monkeypatch.setattr(
            ec, "_ACTIVATION_DIRECTORY",
            PurePosixPath(directory.as_posix()),
        )
        monkeypatch.setattr(ec, "_ACTIVATION_HEAD_SERIAL", 1)
        monkeypatch.setattr(
            ec, "_ACTIVATION_HEAD_STATE_SHA256",
            record["activation_state_sha256"],
        )
        monkeypatch.setattr(ec, "_repository_root", lambda: root)
        ec._clear_authority_cache_for_tests()
        authorization = ec.authorize(contract.env_tag)
        assert authorization.contract is contract
        return authorization

    yield activate
    # monkeypatch 復元後の初回参照が production authority を再 load するよう cache を残さない。
    from orchestrator.campaign import env_contract as ec
    ec._clear_authority_cache_for_tests()


@pytest.fixture(autouse=True)
def _declare_default_test_site(request, monkeypatch):
    """Make ambient machine identity irrelevant unless a test declares a site.

    Test modules are imported before fixture setup, so patch the canonical module
    when present.  Keep ``current_site`` itself intact and neutralize only its inputs.
    A test's own monkeypatch/direct replacement runs later and therefore wins for
    explicit login/compute/suspect cases.
    """
    if "_detect_site_under_test" in request.fixturenames:
        return
    module = sys.modules.get("orchestrator.campaign.site_policy")
    if module is not None:
        monkeypatch.setattr(
            module, "socket", SimpleNamespace(gethostname=lambda: "test-host")
        )
        monkeypatch.setattr(module, "_has_nqsv", lambda: False)


# 親 working tree (P) と共有 ccbench (S) に触る node の分類正本。値は
# ``test_file.py::test_function``（parametrize suffix なし）で固定する。
_REAL_REPO_NODE_INVENTORY = frozenset({
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
    # X/P/I assessment の現行 pin 正負対は共有 CCBench source を読む。
    "test_verifier.py::test_current_pin_proof_surfaces_accept_silo_and_reject_mocc_same_trace",
    # 親 working tree の tracked + untracked snapshot。
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
    # T1259 probe test は module fixture で親 working tree の HEAD、tracked status、
    # untracked paths、source digest を一度取得し、全 consumer がその template を読む。
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
    # 上記 snapshot テストの結線監査 meta-テスト。実 ROOT で builder を実走し repo tree
    # snapshot を取るため、writer の patch 窓と同じ競合面にある (D63 列挙漏れの補完)。
    "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",
    # T-080 の子 collection が実履歴、output、共有 submodule を読む reader。
    "test_real_repo_serialization.py::test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default",
    # foreign module の import-time temp 境界と実 output の不変を検査する reader。
    "test_real_repo_serialization.py::test_t080_import_temp_environment_fails_closed_for_foreign_module",
    # suite 全体を subprocess collect する meta-test。inner collect は node protocol を
    # 発火しないため、外側 node が親 common-dir reader lock を所有する。
    "test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes",
    "test_real_repo_serialization.py::test_shard_assignment_preserves_live_xdist_group_components_and_split_control",
    "test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order",

    # T810 live-authority は親 common-dir の linked-worktree registry を読む。
    "test_t810_coordinator.py::test_prepare_group_rejects_forged_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_rejects_self_consistent_foreign_git_identity_before_any_mkdir",
    "test_t810_coordinator.py::test_prepare_group_accepts_external_root_with_anchor_union",

    # 実資源依存の reader。現行 test は applied() を nullcontext へ差し替えるが、
    # over-approximation として実 repo 直列群に残置する。
    "test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_sort.py::test_drive_iteration_checkpoint_survives_across_calls",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_writes_entry_and_checkpoint",
    "test_p3_s4_loop_trigger_gating.py::test_drive_iteration_entry_failure_blocks_checkpoint",

    # writer の patch 窓にある実 source を読む reader。
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

    # known-axes の生成/検証が実 ccbench source path を読む reader。
    "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points",
    "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze",
    "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head",
    "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin",

    # measurement freeze は module fixture で実 known-axes 材料 (共有 submodule source
    # 含む) から K.build_document を実走する reader ([T-066] echo 除去後)。
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

    # module fixture が実共有 submodule source を読むため、その全 consumer を閉じる。
    "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control",

    # prepare_cell が実共有 submodule の linked-worktree 管理領域を更新する writer。
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration",
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration",
    "test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2",
    "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
    # module fixture が実 repo を clone し、実 submodule を local source として読む reader。
    "test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static",
    "test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore",
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

    # root=実 repo の oracle gate が known-axes verify を間接呼出しする reader。
    "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification",
    "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
    "test_s8b_oracle_driver.py::test_v2_standalone_gate_check_requires_full_floor_validation",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
    # RuleOps inventory が親 working tree と実履歴を読む reader ([T-438])。
    "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight",
})


@dataclass(frozen=True)
class RealRepoAccess:
    """One node's access to the parent tree and shared ccbench repository."""

    parent: str | None
    ccbench: str | None


_REAL_REPO_PARENT_ONLY_NODES = frozenset({
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
_REAL_REPO_CCBENCH_ONLY_NODES = frozenset({
    "test_verifier.py::test_current_pin_proof_surfaces_accept_silo_and_reject_mocc_same_trace",
    "test_campaign.py::test_source_digest_parse_options_defaults",
    "test_campaign.py::test_source_digest_stock_roundtrip",
    "test_campaign.py::test_source_digest_fixed_variant_distinct",
    "test_campaign.py::test_source_digest_failsclosed_on_missing_define",
    "test_campaign.py::test_source_digest_semantic_comment_vs_behavior",
    "test_hooks.py::test_real_submodule_payload_edit",
    "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
})
_REAL_REPO_LOCAL_ONLY_NODES = frozenset({
    "test_s8b_oracle_driver.py::test_tampered_freeze_fails_source_verification",
    "test_s8b_oracle_driver.py::test_v2_standalone_gate_check_requires_full_floor_validation",
})
_REAL_REPO_CCBENCH_WRITER_NODES_LITERAL = frozenset({
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration",
    "test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration",
    "test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2",
    "test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
})
_REAL_REPO_BOTH_READER_NODES = frozenset({
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
    "test_campaign.py::test_evolve_block_markers_structure_and_inert",
    "test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory",
    "test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch",
    "test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure",
    "test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation",
    "test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases",
    "test_codex_reasoning_ab.py::test_git_answer_object_reinjection_is_rejected",
    "test_codex_reasoning_ab.py::test_m1_snapshot_head_pin_is_independent",
    "test_codex_reasoning_ab.py::test_m3_focus_artifact_directions",
    "test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing",
    "test_codex_reasoning_ab.py::test_m3_snapshot_mode_change",
    "test_codex_reasoning_ab.py::test_m3_symbolic_head_is_required",
    "test_codex_reasoning_ab.py::test_material_replay_rejects_task_manifest_exchange_at_digest_consumers",
    "test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned",
    "test_codex_reasoning_ab.py::test_pos_neg_submodule_initialization_state_mismatch_is_rejected",
    "test_codex_reasoning_ab.py::test_replay_forwards_only_successful_snapshot_evidence_to_adjudication",
    "test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static",
    "test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_reject_swap_restore",
    "test_codex_reasoning_ab.py::test_snapshot_submodule_object_store_is_recursive",
    "test_codex_reasoning_ab.py::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested",
    "test_codex_reasoning_ab.py::test_supervisor_launches_pair_and_scrubs_git_environment",
    "test_codex_reasoning_ab.py::test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid",
    "test_codex_reasoning_ab.py::test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run",
    "test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment",
    "test_real_repo_serialization.py::test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default",
    "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper",
    "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze",
    "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points",
    "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
    "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin",
    "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head",
    "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
    "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
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
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e",
    "test_s8b_floor_campaign.py::test_public_official_preflight_accepts_versioned_protocol",
    "test_s8b_floor_campaign.py::test_public_official_preflight_accepts_legacy_protocol",
    "test_s8b_floor_campaign.py::test_public_official_preflight_rejects_resolved_protocol_byte_drift",
    "test_s8b_floor_campaign.py::test_public_official_preflight_rejects_legacy_byte_drift_after_capture",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
    "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
    "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control",
})


def _build_real_repo_access_map() -> Mapping[str, RealRepoAccess]:
    ccbench_reader_nodes = (
        _REAL_REPO_CCBENCH_ONLY_NODES
        - _REAL_REPO_CCBENCH_WRITER_NODES_LITERAL
    )
    both_writer_nodes = (
        _REAL_REPO_CCBENCH_WRITER_NODES_LITERAL
        - _REAL_REPO_CCBENCH_ONLY_NODES
    )
    ccbench_writer_nodes = (
        _REAL_REPO_CCBENCH_WRITER_NODES_LITERAL
        & _REAL_REPO_CCBENCH_ONLY_NODES
    )
    access_groups = (
        (_REAL_REPO_PARENT_ONLY_NODES, RealRepoAccess("read", None)),
        (ccbench_reader_nodes, RealRepoAccess(None, "read")),
        (_REAL_REPO_BOTH_READER_NODES, RealRepoAccess("read", "read")),
        (both_writer_nodes, RealRepoAccess("read", "write")),
        (ccbench_writer_nodes, RealRepoAccess(None, "write")),
    )
    classified_groups = tuple(nodes for nodes, _access in access_groups) + (
        _REAL_REPO_LOCAL_ONLY_NODES,
    )
    for index, left in enumerate(classified_groups):
        for right in classified_groups[index + 1:]:
            overlap = left & right
            if overlap:
                raise RuntimeError(
                    f"real-repo access partitions overlap: {sorted(overlap)!r}"
                )
    union = frozenset().union(*classified_groups)
    if union != _REAL_REPO_NODE_INVENTORY:
        raise RuntimeError(
            "real-repo access partitions do not match inventory: "
            f"missing={sorted(_REAL_REPO_NODE_INVENTORY - union)!r} "
            f"extra={sorted(union - _REAL_REPO_NODE_INVENTORY)!r}"
        )
    classified: dict[str, RealRepoAccess] = {}
    for nodes, access in access_groups:
        for node_id in nodes:
            classified[node_id] = access
    expected = _REAL_REPO_NODE_INVENTORY - _REAL_REPO_LOCAL_ONLY_NODES
    if set(classified) != set(expected):
        raise RuntimeError("real-repo access map is incomplete")
    return MappingProxyType(classified)


REAL_REPO_ACCESS_BY_NODE = _build_real_repo_access_map()
REAL_REPO_CLASSIFIED_NODES = _REAL_REPO_NODE_INVENTORY
REAL_REPO_LOCAL_ONLY_NODES = _REAL_REPO_LOCAL_ONLY_NODES
REAL_REPO_RESOURCE_NODES = frozenset(REAL_REPO_ACCESS_BY_NODE)
REAL_REPO_CCBENCH_WRITER_NODES = frozenset(
    node_id
    for node_id, access in REAL_REPO_ACCESS_BY_NODE.items()
    if access.ccbench == "write"
)
REAL_REPO_PROCESS_MEMO_NODES = frozenset({
    "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
    "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
    "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
})
if not REAL_REPO_PROCESS_MEMO_NODES <= REAL_REPO_RESOURCE_NODES:
    raise RuntimeError("real-repo process memo nodes must be resource nodes")

# The sort-SWO environment is resolved once at collection time and consumed by
# these nodes through sort_swo_oracle_receipt_memo.  This registry deliberately
# does not carry the real-repo marker: its lifecycle is a separate correctness
# barrier from the shared-worktree serial group above.
ORACLE_ENVIRONMENT_CONSUMER_NODES = frozenset({
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

# production receipt memo を test body 内で読む関数の完全 inventory。parametrize suffix と
# loadgroup suffix は除いた ``file::function`` 形で固定する。34 関数 / 37 node。
RECEIPT_MEMO_CONSUMER_NODES = frozenset({
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

# 意図的な除外（正本リストの境界）:
# - test_s1_measurement_freeze.py のうち fixture 非利用 3 node (AST import 検査 +
#   hermetic seam 2 件) は実 repo / 共有 submodule を読まない。fixture 消費 node は
#   [T-066] echo 除去後は実材料 reader なので上記に列挙済み。
# - test_campaign.py::test_patchharness_* は tmp repo だけを対象にする。
# - source_digest allowlist は subprocess を fake 化しており、lock-path gate は実 output
#   だけを読む。実 output / snapshot 系もこの reader/writer 競合面には含めない。


@pytest.fixture(autouse=True)
def _isolate_task_run_recording_env(monkeypatch):
    """外側 run が task-run 記録付きでも、テスト自身は記録 env を観測しない。

    wrapper (tools/run_tests.py) は pytest 起動前に env を読むため記録は影響を受けない。
    テストが記録経路を検査するときは自分で env を設定する (dogfooding で実測した汚染の隔離)。
    """
    for name in (
        "IZANAGI_TASK_RUN_ID",
        "IZANAGI_TASK_RUNS_ROOT",
        "IZANAGI_TASK_RUN_SIDECAR",
        "IZANAGI_TEST_TRIGGER",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def _isolate_exploration_output_root_env(monkeypatch):
    """Exploration root selection and its process pin never leak across tests."""
    monkeypatch.delenv("IZANAGI_EXPLORATION_OUTPUT_ROOT", raising=False)
    module = sys.modules.get("orchestrator.campaign.layout")
    if module is not None:
        module._reset_exploration_output_root_pin_for_tests()
    yield
    module = sys.modules.get("orchestrator.campaign.layout")
    if module is not None:
        module._reset_exploration_output_root_pin_for_tests()


@pytest.fixture(autouse=True)
def _isolate_official_output_root_env(monkeypatch):
    """Official root selection and its process pin never leak across tests."""
    monkeypatch.delenv("IZANAGI_OFFICIAL_OUTPUT_ROOT", raising=False)
    module = sys.modules.get("orchestrator.campaign.layout")
    if module is not None:
        module._reset_official_output_root_pin_for_tests()
    yield
    module = sys.modules.get("orchestrator.campaign.layout")
    if module is not None:
        module._reset_official_output_root_pin_for_tests()


def _real_repo_node_id(item) -> str:
    """Collected item を正本の ``module::function`` 形へ正規化する。"""
    nodeid = getattr(item, "nodeid", None)
    if isinstance(nodeid, str):
        registered = _receipt_memo_node_id_from_nodeid(nodeid)
        if registered in REAL_REPO_CLASSIFIED_NODES:
            return registered
    function = getattr(item, "originalname", None) or item.name.split("[", 1)[0]
    function = function.removesuffix("@real-repo")
    return f"{os.path.basename(str(item.path))}::{function}"


def _receipt_memo_node_id_from_nodeid(nodeid: str) -> str | None:
    parts = nodeid.split("::")
    if len(parts) < 2:
        return None
    function = parts[1].split("[", 1)[0].split("@", 1)[0]
    return f"{os.path.basename(parts[0])}::{function}"


def _receipt_memo_module():
    """consumer 検出後にだけ canonical memo module を import する。"""
    from orchestrator.tests import real_repo_receipt_memo

    return real_repo_receipt_memo


def _oracle_environment_memo_node_id_from_nodeid(nodeid: str) -> str | None:
    """Normalize an xdist collection id for the oracle consumer registry."""
    parts = nodeid.split("::")
    if len(parts) < 2:
        return None
    function = parts[1].split("[", 1)[0].split("@", 1)[0]
    return f"{os.path.basename(parts[0])}::{function}"


def _oracle_environment_memo_module():
    """Import the oracle memo only after a registered consumer is collected."""
    from orchestrator.tests import sort_swo_oracle_receipt_memo

    return sort_swo_oracle_receipt_memo


_RECEIPT_MEMO_PREWARMED_ATTR = "_izanagi_receipt_memo_prewarmed"
_RECEIPT_MEMO_RUN_ID_ATTR = "_izanagi_receipt_memo_run_id"
_RECEIPT_MEMO_SESSION_ID_ATTR = "_izanagi_receipt_memo_session_id"
_RECEIPT_MEMO_SESSION_ACTIVE_ATTR = "_izanagi_receipt_memo_session_active"
_RECEIPT_MEMO_NONCE_ENV = "IZANAGI_RECEIPT_MEMO_NONCE"
_RECEIPT_MEMO_NONCE_PREVIOUS_ATTR = "_izanagi_receipt_memo_nonce_previous"
_RECEIPT_MEMO_NONCE_ACTIVE_ATTR = "_izanagi_receipt_memo_nonce_active"
_RECEIPT_MEMO_ENV_UNSET = object()

_ORACLE_ENVIRONMENT_MEMO_PREWARMED_ATTR = (
    "_izanagi_oracle_environment_memo_prewarmed"
)
_ORACLE_ENVIRONMENT_MEMO_RUN_ID_ATTR = "_izanagi_oracle_environment_memo_run_id"
_ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR = (
    "_izanagi_oracle_environment_memo_session_id"
)
_ORACLE_ENVIRONMENT_MEMO_SESSION_ACTIVE_ATTR = (
    "_izanagi_oracle_environment_memo_session_active"
)
_ORACLE_ENVIRONMENT_MEMO_NONCE_ENV = "IZANAGI_ORACLE_ENVIRONMENT_MEMO_NONCE"
_ORACLE_ENVIRONMENT_MEMO_NONCE_PREVIOUS_ATTR = (
    "_izanagi_oracle_environment_memo_nonce_previous"
)
_ORACLE_ENVIRONMENT_MEMO_NONCE_ACTIVE_ATTR = (
    "_izanagi_oracle_environment_memo_nonce_active"
)
_ORACLE_ENVIRONMENT_MEMO_ENV_UNSET = object()


# Each barrier job marks actual work only after all skip/identity checks.
_MEMO_PREWARM_TIMING = threading.local()


def _prewarm_receipt_memo(config, nodeids, *, run_id: str | None, early: bool = False) -> None:
    """Prewarm once for collected consumers or an explicitly selected early job."""
    # pytest_collection_finish の外側 guard と意図的に冗長な defense-in-depth。
    # worker payer は両 guard が同時に失われない限り再発しない。
    if hasattr(config, "workerinput"):
        return
    nodeids = tuple(nodeids)
    if not early and not _receipt_memo_prewarm_prerequisites(config, nodeids):
        return
    if getattr(config, _RECEIPT_MEMO_PREWARMED_ATTR, False):
        previous = getattr(config, _RECEIPT_MEMO_RUN_ID_ATTR, None)
        if previous != run_id:
            raise pytest.UsageError(
                "receipt memo prewarm の xdist run ID が worker 間で不一致: "
                f"first={previous!r} current={run_id!r}"
            )
        return
    session_id = getattr(config, _RECEIPT_MEMO_SESSION_ID_ATTR, None)
    if session_id is None:
        raise pytest.UsageError("receipt memo prewarm に pytest session ID が無い")
    _MEMO_PREWARM_TIMING.started = time.monotonic()
    memo_module = _receipt_memo_module()
    try:
        with _real_repo_locks(RealRepoAccess("read", None)):
            memo_module.prewarm_real_repo_receipt(
                run_id=run_id,
                session_id=session_id,
            )
    except BaseException:
        # 入れ子 pytest.main() の内側 prewarm が失敗しても外側 snapshot を戻す。
        memo_module.finish_real_repo_receipt_session(session_id=session_id)
        raise
    setattr(config, _RECEIPT_MEMO_SESSION_ACTIVE_ATTR, True)
    setattr(config, _RECEIPT_MEMO_RUN_ID_ATTR, run_id)
    setattr(config, _RECEIPT_MEMO_PREWARMED_ATTR, True)


def _receipt_memo_prewarm_prerequisites(config, nodeids) -> bool:
    """prewarm 前提を読めない pytest 以外の hook 引数は安全側で無視する。"""
    try:
        getoption = getattr(config, "getoption", None)
        if not callable(getoption):
            return False
        if getoption("collectonly", False):
            return False
        return _receipt_memo_consumer_selected(nodeids)
    except Exception:
        return False


def _receipt_memo_consumer_selected(nodeids) -> bool:
    return any(
        _receipt_memo_node_id_from_nodeid(nodeid) in RECEIPT_MEMO_CONSUMER_NODES
        for nodeid in nodeids
    )


def _prewarm_oracle_environment_memo(config, nodeids, *, run_id: str | None, early: bool = False) -> None:
    """Prewarm the oracle environment once before any consumer is scheduled."""
    # Keep the guard inside the helper as well as at each hook call site.  A
    # worker must never become a resolver payer through a hook refactor.
    if hasattr(config, "workerinput"):
        return
    nodeids = tuple(nodeids)
    if not early and not _oracle_environment_memo_prewarm_prerequisites(config, nodeids):
        return
    if getattr(config, _ORACLE_ENVIRONMENT_MEMO_PREWARMED_ATTR, False):
        previous = getattr(config, _ORACLE_ENVIRONMENT_MEMO_RUN_ID_ATTR, None)
        if previous != run_id:
            raise pytest.UsageError(
                "oracle environment memo prewarm の xdist run ID が worker 間で不一致: "
                f"first={previous!r} current={run_id!r}"
            )
        return
    session_id = getattr(config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR, None)
    if session_id is None:
        raise pytest.UsageError(
            "oracle environment memo prewarm に pytest session ID が無い"
        )
    _MEMO_PREWARM_TIMING.started = time.monotonic()
    memo_module = _oracle_environment_memo_module()
    try:
        with _real_repo_locks(RealRepoAccess("read", None)):
            memo_module.prewarm_oracle_environment(
                run_id=run_id,
                session_id=session_id,
            )
    except BaseException:
        memo_module.finish_oracle_environment_session(session_id=session_id)
        raise
    setattr(config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ACTIVE_ATTR, True)
    setattr(config, _ORACLE_ENVIRONMENT_MEMO_RUN_ID_ATTR, run_id)
    setattr(config, _ORACLE_ENVIRONMENT_MEMO_PREWARMED_ATTR, True)


def _oracle_environment_memo_prewarm_prerequisites(config, nodeids) -> bool:
    """Ignore unreadable/non-pytest hook options safely, but never guess a payer."""
    try:
        getoption = getattr(config, "getoption", None)
        if not callable(getoption):
            return False
        if getoption("collectonly", False):
            return False
        return _oracle_environment_memo_consumer_selected(nodeids)
    except Exception:
        return False


def _oracle_environment_memo_consumer_selected(nodeids) -> bool:
    return any(
        _oracle_environment_memo_node_id_from_nodeid(nodeid)
        in ORACLE_ENVIRONMENT_CONSUMER_NODES
        for nodeid in nodeids
    )


_GROWTH_HOLD_IDS_ATTR = "_izanagi_collected_growth_hold_ids"
_FLAKY_HOLD_MATCHED_IDS_ATTR = "_izanagi_collected_flaky_hold_ids"
_FLAKY_HOLD_SKIPPED_IDS_ATTR = "_izanagi_skipped_flaky_hold_ids"
_FLAKY_HOLD_COLLECTION_WORKERS_ATTR = "_izanagi_flaky_hold_collection_workers"
_REAL_REPO_ACCESS_ATTR = "_izanagi_real_repo_access"
_ACCEPTANCE_DURATION_LEDGER_REPO_ROOT = Path(__file__).resolve().parents[2]
_ACCEPTANCE_DURATION_LEDGER_PATH = (
    _ACCEPTANCE_DURATION_LEDGER_REPO_ROOT
    / "orchestrator/tests/acceptance_duration_ledger.json"
)
# The current ledger is about 1.77 MiB.  Sixteen MiB leaves ample growth room
# while bounding one untrusted JSON read and parse before collection starts.
_ACCEPTANCE_DURATION_LEDGER_MAX_BYTES = 16 * 1024 * 1024
_ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR = (
    "_izanagi_acceptance_duration_seconds_by_nodeid"
)
_ACCEPTANCE_LEDGER_RELATIVE_PATH_CACHE: dict[str, str] = {}
_ACCEPTANCE_DURATION_LEDGER_WORKERINPUT_KEY = (
    "izanagi_acceptance_duration_ledger_v1"
)
# loadscope.schedule() synchronously gives 48 workers one unit and then one
# prefetched unit via _reschedule(), so the initial distribution window is 96.
_ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS = 48 * 2
_COLLECTION_NARROWING_OPTIONS = frozenset({"--ignore", "--ignore-glob", "--pyargs"})
_RUNNER_EXCLUSION_ENV = (
    None if _SELECTION_CONTRACT is None
    else _SELECTION_CONTRACT.RUNNER_EXCLUSION_ENV
)
_SELECTION_RECEIPT_PREFIX = (
    None if _SELECTION_CONTRACT is None
    else _SELECTION_CONTRACT.SELECTION_RECEIPT_PREFIX
)
_EFFECTIVE_SCHEDULER_PREFIX = "IZANAGI_EFFECTIVE_SCHEDULER_V1 "
_EFFECTIVE_SCHEDULER_ATTR = "_izanagi_effective_scheduler"
_FLAKY_HOLD_SUMMARY_PREFIX = "IZANAGI_FLAKY_HOLD_SUMMARY_V1 "

_REAL_REPO_LOCK_DIRECTORY = Path("/tmp")
# 245 s = the 5-minute acceptance ceiling minus the observed longest resource
# cohort (11.80 s setup + 43.22 s call = 55.02 s), rounded to one second.
_REAL_REPO_LOCK_TIMEOUT_S = 245.0
_REAL_REPO_LOCK_RETRY_INTERVAL_S = 0.05
_REAL_REPO_LOCK_RESOURCES = ("parent", "ccbench")
_REAL_REPO_LOCK_MODE_RANK = {"read": 0, "write": 1}
_REAL_REPO_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)


@dataclass
class _RealRepoProcessLockState:
    """One process-owned fd and the live requests that determine its mode."""

    fd: int
    holders: Counter[tuple[int, str]]
    mode: str | None
    gate_fd: int | None = None


_REAL_REPO_PROCESS_LOCK_CONDITION = threading.Condition(threading.RLock())
_REAL_REPO_PROCESS_LOCKS: dict[tuple[str, Path], _RealRepoProcessLockState] = {}
_REAL_REPO_PROCESS_LOCK_PID = os.getpid()


def _real_repo_git_environment() -> dict[str, str]:
    """Return a closed, read-only Git environment for lock identity probes."""
    env = {
        key: os.environ[key]
        for key in _REAL_REPO_GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


def _real_repo_worktree_root(repo_root: Path | str | None = None) -> Path:
    return Path(os.path.realpath(os.fspath(
        _ACCEPTANCE_DURATION_LEDGER_REPO_ROOT
        if repo_root is None
        else repo_root
    )))


def _real_repo_resource_root(
    resource: str, *, repo_root: Path | str | None = None,
) -> Path:
    if resource not in _REAL_REPO_LOCK_RESOURCES:
        raise ValueError(f"unknown real-repo lock resource: {resource!r}")
    worktree_root = _real_repo_worktree_root(repo_root)
    return (
        worktree_root
        if resource == "parent"
        else worktree_root / "external" / "ccbench"
    )


def _real_repo_common_dir(
    resource: str, *, repo_root: Path | str | None = None,
) -> Path:
    """Resolve one resource's Git common-dir without ambient Git authority."""
    root = _real_repo_resource_root(resource, repo_root=repo_root)
    executable = shutil.which("git")
    if executable is None:
        raise RuntimeError("real-repo common-dir resolver requires git")
    try:
        completed = subprocess.run(
            [
                executable,
                "-C",
                os.fspath(root),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=_real_repo_git_environment(),
            timeout=30.0,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "real-repo common-dir resolution failed closed: "
            f"resource={resource} error={type(exc).__name__}"
        ) from exc
    lines = completed.stdout.splitlines()
    if completed.returncode != 0 or len(lines) != 1 or not lines[0]:
        raise RuntimeError(
            "real-repo common-dir resolution failed closed: "
            f"resource={resource} rc={completed.returncode} lines={len(lines)}"
        )
    common_dir = Path(lines[0])
    if not common_dir.is_absolute():
        raise RuntimeError(
            "real-repo common-dir is not absolute: "
            f"resource={resource} path={common_dir}"
        )
    try:
        resolved = common_dir.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(
            "real-repo common-dir cannot be resolved strictly: "
            f"resource={resource} path={common_dir}"
        ) from exc
    if not resolved.is_dir():
        raise RuntimeError(
            "real-repo common-dir is not a directory: "
            f"resource={resource} path={resolved}"
        )
    return resolved


def _real_repo_legacy_lock_path(
    resource: str, *, repo_root: Path | str | None = None,
) -> Path:
    """Return the pre-common-dir worktree-root key during migration."""
    if resource not in _REAL_REPO_LOCK_RESOURCES:
        raise ValueError(f"unknown real-repo lock resource: {resource!r}")
    digest = hashlib.sha256(
        os.fsencode(_real_repo_worktree_root(repo_root))
    ).hexdigest()
    return _REAL_REPO_LOCK_DIRECTORY / (
        f"izanagi-real-repo-{digest}-{resource}.lock"
    )


def _real_repo_lock_path(
    resource: str, *, repo_root: Path | str | None = None,
) -> Path:
    """Return the Git-common-dir key shared by sibling worktrees.

    The guarantee is limited to sessions that see the same host and filesystem;
    it does not claim coordination across hosts or different filesystem views.
    """
    common_dir = _real_repo_common_dir(resource, repo_root=repo_root)
    digest = hashlib.sha256(os.fsencode(common_dir)).hexdigest()
    return _REAL_REPO_LOCK_DIRECTORY / (
        f"izanagi-real-repo-{digest}-{resource}.lock"
    )


def _real_repo_lock_holder_info(fd: int) -> str:
    """Return bounded kernel holder details for a timed-out flock."""
    try:
        lock_stat = os.fstat(fd)
        raw_lines = Path("/proc/locks").read_text(
            encoding="ascii", errors="replace"
        ).splitlines()
    except OSError as exc:
        return f"unavailable:{type(exc).__name__}:{getattr(exc, 'errno', None)}"
    holders = []
    for line in raw_lines:
        fields = line.split()
        if len(fields) < 6 or fields[1] != "FLOCK":
            continue
        try:
            device, inode_text = fields[5].rsplit(":", 1)
            major_text, minor_text = device.split(":", 1)
            matches = (
                int(major_text, 16) == os.major(lock_stat.st_dev)
                and int(minor_text, 16) == os.minor(lock_stat.st_dev)
                and int(inode_text) == lock_stat.st_ino
            )
        except (ValueError, IndexError):
            continue
        if matches:
            holders.append(f"pid={fields[4]},mode={fields[3]}")
            if len(holders) >= 16:
                holders.append("more")
                break
    return ",".join(holders) if holders else "kernel-holder-unavailable"


def _open_real_repo_lock(path: Path) -> int:
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        lock_stat = os.fstat(fd)
        if not stat.S_ISREG(lock_stat.st_mode):
            raise RuntimeError(f"real-repo lock is not a regular file: {path}")
        if lock_stat.st_uid != os.getuid():
            raise RuntimeError(
                f"real-repo lock owner mismatch: {path} uid={lock_stat.st_uid}"
            )
        if stat.S_IMODE(lock_stat.st_mode) & 0o077:
            raise RuntimeError(
                f"real-repo lock permissions are too broad: {path} "
                f"mode={stat.S_IMODE(lock_stat.st_mode):04o}"
            )
        return fd
    except BaseException:
        os.close(fd)
        raise


def _real_repo_strongest_lock_mode(
    holders: Counter[tuple[int, str]],
) -> str | None:
    live_modes = {
        mode for (_owner, mode), count in holders.items() if count > 0
    }
    return (
        max(live_modes, key=_REAL_REPO_LOCK_MODE_RANK.__getitem__)
        if live_modes
        else None
    )


def _real_repo_flock_until(
    resource: str,
    access_mode: str,
    path: Path,
    fd: int,
    *,
    deadline: float,
    retry_interval_s: float,
) -> None:
    """Set one process-owned fd to a mode using bounded nonblocking retries."""
    operations = {"read": fcntl.LOCK_SH, "write": fcntl.LOCK_EX}
    try:
        operation = operations[access_mode]
    except KeyError as exc:
        raise ValueError(f"invalid real-repo access mode: {access_mode!r}") from exc
    while True:
        try:
            fcntl.flock(fd, operation | fcntl.LOCK_NB)
            return
        except OSError as exc:
            if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                holders = _real_repo_lock_holder_info(fd)
                raise RuntimeError(
                    "real-repo lock deadline exceeded; fails-closed: "
                    f"resource={resource} mode={access_mode} "
                    f"path={path} holders={holders}"
                ) from exc
            time.sleep(min(retry_interval_s, remaining))


def _reset_real_repo_process_locks_after_fork() -> None:
    """Drop inherited manager fds before the child creates process-local state."""
    global _REAL_REPO_PROCESS_LOCK_PID
    pid = os.getpid()
    if pid == _REAL_REPO_PROCESS_LOCK_PID:
        return
    for state in _REAL_REPO_PROCESS_LOCKS.values():
        os.close(state.fd)
        if state.gate_fd is not None:
            os.close(state.gate_fd)
    _REAL_REPO_PROCESS_LOCKS.clear()
    _REAL_REPO_PROCESS_LOCK_PID = pid


def _real_repo_same_process_request_is_compatible(
    state: _RealRepoProcessLockState,
    owner: int,
    access_mode: str,
) -> bool:
    """Keep concurrent threads compatible while permitting same-thread upgrade."""
    other_modes = {
        mode
        for (holder, mode), count in state.holders.items()
        if holder != owner and count > 0
    }
    if not other_modes:
        return True
    return access_mode == "read" and "write" not in other_modes


@contextlib.contextmanager
def _real_repo_lock_path_context(
    resource: str,
    access_mode: str,
    path: Path,
    *,
    deadline: float,
    retry_interval_s: float,
):
    """Acquire one key through its process-local fd and mode-refcount manager."""
    if access_mode not in _REAL_REPO_LOCK_MODE_RANK:
        raise ValueError(f"invalid real-repo access mode: {access_mode!r}")
    key = (resource, Path(path))
    owner = threading.get_ident()
    holder = (owner, access_mode)
    state = None
    condition = _REAL_REPO_PROCESS_LOCK_CONDITION
    with condition:
        _reset_real_repo_process_locks_after_fork()
        while True:
            state = _REAL_REPO_PROCESS_LOCKS.get(key)
            if state is None or _real_repo_same_process_request_is_compatible(
                    state, owner, access_mode):
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(
                    "real-repo lock deadline exceeded; fails-closed: "
                    f"resource={resource} mode={access_mode} path={path} "
                    "holders=same-process-incompatible-thread"
                )
            condition.wait(timeout=min(retry_interval_s, remaining))

        created = state is None
        if created:
            state = _RealRepoProcessLockState(
                fd=_open_real_repo_lock(path), holders=Counter(), mode=None,
            )
            _REAL_REPO_PROCESS_LOCKS[key] = state
        assert state is not None
        requested = state.holders.copy()
        requested[holder] += 1
        target_mode = _real_repo_strongest_lock_mode(requested)
        assert target_mode is not None
        try:
            if target_mode != state.mode:
                # Writers hold the gate only while acquiring main; fresh readers
                # probe all gates before holding any main lock to avoid cycles.
                if target_mode == "write":
                    gate_path = Path(f"{path}.gate")
                    state.gate_fd = _open_real_repo_lock(gate_path)
                try:
                    if state.gate_fd is not None:
                        if state.mode == "read":
                            fcntl.flock(state.fd, fcntl.LOCK_UN)
                        _real_repo_flock_until(
                            resource, "write", gate_path, state.gate_fd,
                            deadline=deadline,
                            retry_interval_s=retry_interval_s,
                        )
                    _real_repo_flock_until(
                        resource,
                        target_mode,
                        path,
                        state.fd,
                        deadline=deadline,
                        retry_interval_s=retry_interval_s,
                    )
                finally:
                    if state.gate_fd is not None:
                        try:
                            fcntl.flock(state.gate_fd, fcntl.LOCK_UN)
                        finally:
                            os.close(state.gate_fd)
                            state.gate_fd = None
        except BaseException:
            if created:
                del _REAL_REPO_PROCESS_LOCKS[key]
                os.close(state.fd)
                condition.notify_all()
            raise
        state.holders = requested
        state.mode = target_mode

    try:
        yield
    finally:
        with condition:
            current = _REAL_REPO_PROCESS_LOCKS.get(key)
            if current is not state or state.holders[holder] <= 0:
                raise RuntimeError(
                    "real-repo process lock manager state mismatch; fails-closed: "
                    f"resource={resource} mode={access_mode} path={path}"
                )
            state.holders[holder] -= 1
            if state.holders[holder] == 0:
                del state.holders[holder]
            target_mode = _real_repo_strongest_lock_mode(state.holders)
            if target_mode is None:
                try:
                    fcntl.flock(state.fd, fcntl.LOCK_UN)
                finally:
                    os.close(state.fd)
                    del _REAL_REPO_PROCESS_LOCKS[key]
                    condition.notify_all()
            else:
                if target_mode != state.mode:
                    _real_repo_flock_until(
                        resource,
                        target_mode,
                        path,
                        state.fd,
                        deadline=time.monotonic() + _REAL_REPO_LOCK_TIMEOUT_S,
                        retry_interval_s=retry_interval_s,
                    )
                state.mode = target_mode
                condition.notify_all()


@contextlib.contextmanager
def _real_repo_file_lock(
    resource: str,
    access_mode: str,
    *,
    timeout_s: float | None = None,
    retry_interval_s: float | None = None,
):
    """Acquire legacy before resolving and acquiring the common-dir key."""
    timeout = _REAL_REPO_LOCK_TIMEOUT_S if timeout_s is None else timeout_s
    retry = (
        _REAL_REPO_LOCK_RETRY_INTERVAL_S
        if retry_interval_s is None
        else retry_interval_s
    )
    if timeout < 0 or retry <= 0:
        raise ValueError("real-repo lock timeout/retry interval must be bounded")
    deadline = time.monotonic() + timeout
    legacy = _real_repo_legacy_lock_path(resource)
    with _real_repo_lock_path_context(
        resource,
        access_mode,
        legacy,
        deadline=deadline,
        retry_interval_s=retry,
    ):
        common = _real_repo_lock_path(resource)
        if legacy == common:
            raise RuntimeError(
                "real-repo legacy/common lock namespaces unexpectedly coincide: "
                f"resource={resource} path={legacy}"
            )
        with _real_repo_lock_path_context(
            resource,
            access_mode,
            common,
            deadline=deadline,
            retry_interval_s=retry,
        ):
            yield


@contextlib.contextmanager
def _real_repo_locks(access: RealRepoAccess | None):
    """Acquire P then S for one node and release them in reverse order."""
    if access is None:
        yield
        return
    requests = tuple(
        (resource, mode)
        for resource, mode in (
            ("parent", access.parent), ("ccbench", access.ccbench),
        )
        if mode is not None
    )
    deadline = time.monotonic() + _REAL_REPO_LOCK_TIMEOUT_S
    with _REAL_REPO_PROCESS_LOCK_CONDITION:
        _reset_real_repo_process_locks_after_fork()
        if not _REAL_REPO_PROCESS_LOCKS:
            for resource, mode in requests:
                if mode != "read":
                    continue
                for path in (
                    _real_repo_legacy_lock_path(resource),
                    _real_repo_lock_path(resource),
                ):
                    gate_path = Path(f"{path}.gate")
                    gate_fd = _open_real_repo_lock(gate_path)
                    try:
                        _real_repo_flock_until(
                            resource, "read", gate_path, gate_fd,
                            deadline=deadline,
                            retry_interval_s=_REAL_REPO_LOCK_RETRY_INTERVAL_S,
                        )
                    finally:
                        try:
                            fcntl.flock(gate_fd, fcntl.LOCK_UN)
                        finally:
                            os.close(gate_fd)
    with contextlib.ExitStack() as stack:
        for index, (resource, mode) in enumerate(requests):
            if index == 0:
                stack.enter_context(_real_repo_file_lock(
                    resource, mode,
                    timeout_s=max(0.0, deadline - time.monotonic()),
                ))
            else:
                stack.enter_context(_real_repo_file_lock(resource, mode))
        yield


def _acceptance_epoch_now() -> float | None:
    try:
        value = time.time()
        if type(value) not in {int, float}:
            return None
        value = float(value)
    except Exception:
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return value


@contextlib.contextmanager
def _acceptance_timed_real_repo_locks(config, access: RealRepoAccess | None):
    if (
        config is None
        or access is None
        or getattr(config, "_izanagi_acceptance_shard_spec", None) is None
    ):
        with _real_repo_locks(access):
            yield
        return

    with _real_repo_locks(access):
        acquired = _acceptance_epoch_now()
        yield
    released = _acceptance_epoch_now()
    if acquired is None or released is None:
        return
    from tools import acceptance_shards

    acceptance_shards.record_real_repo_lock_interval(
        config, acquired, released,
    )


@contextlib.contextmanager
def _real_repo_fixture_lock_context(
    parent: str | None,
    ccbench: str | None,
):
    """Expose fixture-owned access without exposing lock implementation details."""
    with _real_repo_locks(RealRepoAccess(parent, ccbench)):
        yield


@pytest.fixture(scope="session")
def real_repo_fixture_lock():
    """Return the process-managed context factory for real-repo fixtures."""
    return _real_repo_fixture_lock_context


def _validate_acceptance_duration_ledger_document(document) -> dict[str, float]:
    """Return individually validated durations, or an empty no-ledger view."""
    if not isinstance(document, dict):
        return {}
    schema_version = document.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or schema_version != 1
        or document.get("unit") != "seconds"
    ):
        return {}
    durations = document.get("duration_seconds_by_nodeid")
    nodeid_count = document.get("nodeid_count")
    if (
        not isinstance(durations, dict)
        or isinstance(nodeid_count, bool)
        or not isinstance(nodeid_count, int)
        or nodeid_count < 0
        or nodeid_count != len(durations)
    ):
        return {}

    validated: dict[str, float] = {}
    for nodeid, value in durations.items():
        if (
            not isinstance(nodeid, str)
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        ):
            continue
        try:
            duration = float(value)
        except OverflowError:
            continue
        if math.isfinite(duration):
            validated[nodeid] = duration
    return validated


def _load_acceptance_duration_ledger(
    path: Path = _ACCEPTANCE_DURATION_LEDGER_PATH,
) -> dict[str, float]:
    """Load a bounded ledger fail-softly without hiding programming errors."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(_ACCEPTANCE_DURATION_LEDGER_MAX_BYTES + 1)
    except OSError:
        return {}
    if len(raw) > _ACCEPTANCE_DURATION_LEDGER_MAX_BYTES:
        return {}
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        return {}
    try:
        document = json.loads(text)
    except (ValueError, RecursionError):
        # JSONDecodeError is a ValueError subclass.  MemoryError and process
        # control exceptions deliberately remain visible.
        return {}
    return _validate_acceptance_duration_ledger_document(document)


def _acceptance_duration_worker_payload(durations) -> dict[str, object]:
    """Build a serialization-safe controller snapshot for xdist workers."""
    if not isinstance(durations, dict):
        raise pytest.UsageError("acceptance duration ledger controller snapshot 型が不正")
    return {
        "schema_version": 1,
        "duration_seconds_by_nodeid": dict(durations),
    }


def _acceptance_durations_from_worker_payload(payload) -> dict[str, float]:
    """Reject broken worker wiring instead of treating it as a file failure."""
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise pytest.UsageError("acceptance duration ledger worker payload 型が不正")
    durations = payload.get("duration_seconds_by_nodeid")
    if not isinstance(durations, dict):
        raise pytest.UsageError("acceptance duration ledger worker durations 型が不正")
    validated: dict[str, float] = {}
    for nodeid, value in durations.items():
        if (
            not isinstance(nodeid, str)
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        ):
            raise pytest.UsageError("acceptance duration ledger worker entry 型が不正")
        try:
            duration = float(value)
        except OverflowError as exc:
            raise pytest.UsageError(
                "acceptance duration ledger worker entry 型が不正"
            ) from exc
        if not math.isfinite(duration):
            raise pytest.UsageError("acceptance duration ledger worker entry 型が不正")
        validated[nodeid] = duration
    return validated


def _configure_acceptance_duration_ledger(config) -> None:
    """Read once on the controller and consume only workerinput on workers."""
    if hasattr(config, "workerinput"):
        workerinput = config.workerinput
        if not isinstance(workerinput, dict):
            raise pytest.UsageError("xdist workerinput が acceptance ledger を受け取れない")
        if _ACCEPTANCE_DURATION_LEDGER_WORKERINPUT_KEY in workerinput:
            durations = _acceptance_durations_from_worker_payload(
                workerinput[_ACCEPTANCE_DURATION_LEDGER_WORKERINPUT_KEY]
            )
        else:
            if _acceptance_reordering_enabled(config):
                raise pytest.UsageError(
                    "xdist workerinput に acceptance ledger snapshot が無い"
                )
            durations = {}
    else:
        durations = (
            _load_acceptance_duration_ledger(_ACCEPTANCE_DURATION_LEDGER_PATH)
            if _acceptance_controller_should_load_duration_ledger(config)
            else {}
        )
    setattr(config, _ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR, durations)


def _acceptance_loadgroup_scope(nodeid: str) -> str:
    """Match LoadGroupScheduling._split_scope exactly."""
    if nodeid.rfind("@") > nodeid.rfind("]"):
        return nodeid.split("@")[-1]
    return nodeid


def _acceptance_ledger_nodeid(item) -> str | None:
    """Return the resolved repo-relative nodeid without an xdist group suffix."""
    try:
        nodeid = str(item.nodeid)
        if nodeid.rfind("@") > nodeid.rfind("]"):
            nodeid = nodeid[:nodeid.rfind("@")]
        path_key = os.fspath(item.path)
        if not isinstance(path_key, str):
            raise TypeError("item.path must resolve to str")
        relative_path = _ACCEPTANCE_LEDGER_RELATIVE_PATH_CACHE.get(path_key)
        if relative_path is None:
            relative_path = Path(path_key).resolve(strict=False).relative_to(
                _ACCEPTANCE_DURATION_LEDGER_REPO_ROOT
            ).as_posix()
            _ACCEPTANCE_LEDGER_RELATIVE_PATH_CACHE[path_key] = relative_path
        _original_path, separator, suffix = nodeid.partition("::")
        return relative_path if not separator else f"{relative_path}::{suffix}"
    except (ValueError, OSError, RuntimeError, TypeError):
        return None


def _acceptance_duration_for_item(item, durations) -> float | None:
    """Resolve canonical and historical xdist-suffixed ledger keys."""
    base_nodeid = _acceptance_ledger_nodeid(item)
    if base_nodeid is None:
        return None
    duration = durations.get(base_nodeid)
    if duration is not None:
        return duration
    try:
        group_names = tuple(
            mark.args[0]
            for mark in item.iter_markers(name="xdist_group")
            if len(mark.args) == 1 and isinstance(mark.args[0], str)
        )
    except (AttributeError, TypeError):
        group_names = ()
    for group_name in group_names:
        duration = durations.get(f"{base_nodeid}@{group_name}")
        if duration is not None:
            return duration
    return None


def _replace_acceptance_items(items, reordered) -> None:
    """Replace only a verified identity multiset; this remains active under -O."""
    before_count = len(items)
    before_identities = Counter(id(item) for item in items)
    if (
        len(reordered) != before_count
        or Counter(id(item) for item in reordered) != before_identities
    ):
        raise pytest.UsageError(
            "acceptance duration reorder が item identity multiset を変更した"
        )
    items[:] = reordered
    if (
        len(items) != before_count
        or Counter(id(item) for item in items) != before_identities
    ):
        raise pytest.UsageError(
            "acceptance duration reorder 後の item identity multiset が不正"
        )


def _reorder_acceptance_items_by_duration(items, durations) -> bool:
    """Order loadgroup work units by descending known or policy-default cost."""
    if not durations:
        return False

    units: list[dict[str, object]] = []
    unit_by_scope: dict[str, dict[str, object]] = {}
    for item in items:
        scope = _acceptance_loadgroup_scope(str(item.nodeid))
        unit = unit_by_scope.get(scope)
        if unit is None:
            unit = {"index": len(units), "items": []}
            unit_by_scope[scope] = unit
            units.append(unit)
        unit["items"].append(item)

    known_costs: list[float] = []
    for unit in units:
        cost = 0.0
        known = True
        for item in unit["items"]:
            duration = _acceptance_duration_for_item(item, durations)
            if duration is None:
                known = False
                break
            cost += duration
            if not math.isfinite(cost):
                known = False
                break
        unit["known"] = known
        unit["cost"] = cost
        if known:
            known_costs.append(cost)

    if not known_costs:
        return False
    known_costs.sort(reverse=True)
    unknown_cost = known_costs[
        min(_ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS, len(known_costs)) - 1
    ]
    ordered_units = sorted(
        units,
        key=lambda unit: (
            -(unit["cost"] if unit["known"] else unknown_cost),
            unit["index"],
        ),
    )
    reordered = [item for unit in ordered_units for item in unit["items"]]
    _replace_acceptance_items(items, reordered)
    return True


def _acceptance_options_allow_reordering(option) -> bool:
    """Return whether parsed options preserve ordinary execution ordering."""
    if getattr(option, "maxfail", 0) not in (None, 0):
        return False
    disabled_booleans = (
        "stepwise",
        "stepwise_skip",
        "stepwise_reset",
        "failedfirst",
        "newfirst",
        "lf",
        "collectonly",
        "setuponly",
        "setupplan",
        "showfixtures",
        "show_fixtures_per_test",
        "trace",
    )
    if any(bool(getattr(option, name, False)) for name in disabled_booleans):
        return False
    if getattr(option, "cacheshow", None) is not None:
        return False
    if getattr(option, "loadscopereorder", True) is False:
        return False
    return True


def _acceptance_controller_should_load_duration_ledger(config) -> bool:
    """Load only for an enabled controller-side loadgroup invocation."""
    try:
        option = config.option
        return (
            option.dist == "loadgroup"
            and _acceptance_options_allow_reordering(option)
        )
    except (AttributeError, ValueError, TypeError):
        return False


def _acceptance_reordering_enabled(config) -> bool:
    """Use parsed pytest options, never argv text, to preserve run semantics."""
    try:
        if not config.getvalue("loadgroup"):
            return False
        option = config.option
        return _acceptance_options_allow_reordering(option)
    except (AttributeError, ValueError, TypeError):
        return False


def _growth_holds_opted_in() -> bool:
    _ensure_growth_test_holds_loaded()
    assert RUN_GROWTH_HELD_TESTS_ENV is not None
    assert RUN_GROWTH_HELD_TESTS_TOKEN is not None
    value = os.environ.get(RUN_GROWTH_HELD_TESTS_ENV)
    if value in (None, ""):
        return False
    if value != RUN_GROWTH_HELD_TESTS_TOKEN:
        raise pytest.UsageError(
            f"{RUN_GROWTH_HELD_TESTS_ENV} must be exactly "
            f"{RUN_GROWTH_HELD_TESTS_TOKEN!r}, empty, or unset"
        )
    return True


def _growth_hold_reason(node_id, hold) -> str:
    payload = {
        "correctness_gate": hold.correctness_gate,
        "hold_axis": hold.hold_axis,
        "node_id": node_id,
        "reason": hold.reason,
        "release_condition": hold.release_condition,
        "ruling": hold.ruling,
    }
    return "IZANAGI_GROWTH_HOLD_V1 " + json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
    )


def _flaky_hold_reason(node_id, hold) -> str:
    payload = {
        "cause": hold.cause,
        "evidence_id": hold.evidence_id,
        "failure_signature": hold.failure_signature,
        "known_failure_node_ids": sorted(hold.known_failure_node_ids),
        "node_id": node_id,
        "reintroduction_task_id": hold.reintroduction_task_id,
    }
    return "IZANAGI_FLAKY_HOLD_V1 " + json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True,
    )


def _note_growth_hold(config, node_id: str) -> None:
    held = getattr(config, _GROWTH_HOLD_IDS_ATTR, None)
    if held is None:
        held = set()
        setattr(config, _GROWTH_HOLD_IDS_ATTR, held)
    held.add(node_id)


def _note_flaky_hold(config, node_id: str, *, skipped: bool) -> None:
    matched = getattr(config, _FLAKY_HOLD_MATCHED_IDS_ATTR, None)
    if matched is None:
        matched = set()
        setattr(config, _FLAKY_HOLD_MATCHED_IDS_ATTR, matched)
    matched.add(node_id)
    if skipped:
        skipped_ids = getattr(config, _FLAKY_HOLD_SKIPPED_IDS_ATTR, None)
        if skipped_ids is None:
            skipped_ids = set()
            setattr(config, _FLAKY_HOLD_SKIPPED_IDS_ATTR, skipped_ids)
        skipped_ids.add(node_id)


def _growth_hold_id_from_nodeid(nodeid: str) -> str | None:
    parts = nodeid.split("::")
    if len(parts) < 2:
        return None
    function = parts[1].split("[", 1)[0].split("@", 1)[0]
    return f"{os.path.basename(parts[0])}::{function}"


def _flaky_hold_id_from_nodeid(nodeid: str) -> str | None:
    """Match complete node IDs literally; no basename or family fallback."""
    _ensure_flaky_test_holds_loaded()
    assert FLAKY_TEST_HOLDS is not None
    return nodeid if nodeid in FLAKY_TEST_HOLDS else None


def _normalize_collection_path(path) -> Path:
    """Use one path contract for every complete-collection predicate."""
    if _SELECTION_CONTRACT is None:
        return Path(path).resolve(strict=False)
    return _SELECTION_CONTRACT.normalize_path(path)


def _collection_narrowing_is_runner_owned(config) -> bool:
    """Allow only the authenticated runner exclusion in a complete run."""
    invocation_params = getattr(config, "invocation_params", None)
    argv = getattr(invocation_params, "args", None)
    if argv is None:
        return False
    argv = tuple(argv)
    owned_entries = _runner_owned_exclusion_payload(config)
    owned_tokens = []
    if owned_entries is not None and _SELECTION_CONTRACT is not None:
        owned_tokens.extend(
            _SELECTION_CONTRACT.exclusion_tokens(owned_entries)
        )
    for token in argv:
        if token in owned_tokens:
            owned_tokens.remove(token)
            continue
        if token.split("=", 1)[0] in _COLLECTION_NARROWING_OPTIONS:
            return False
    return not owned_tokens


def _is_complete_growth_hold_collection(config) -> bool:
    numprocesses = getattr(getattr(config, "option", None), "numprocesses", None)
    if (
        not hasattr(config, "workerinput")
        and numprocesses not in (None, 0, "0")
    ):
        # xdist controller does not own the workers' complete item collection.
        return False
    if len(config.args) != 1:
        return False
    try:
        target = _normalize_collection_path(config.args[0])
        suite_root = _normalize_collection_path(__file__).parent
    except (OSError, TypeError, ValueError):
        return False
    if target != suite_root:
        return False
    return _collection_narrowing_is_runner_owned(config)


def _runner_owned_exclusion_payload(config) -> tuple[object, ...] | None:
    """認証済み runner exclusion entries だけを collection 防壁から除く。

    env を継承した入れ子 pytest は runner の narrowing token を持たないため、
    runner 所有の除外なしとして扱う。narrowing token が存在する場合だけ、
    payload と token の契約 drift を UsageError にする。
    """

    raw = (
        None if _RUNNER_EXCLUSION_ENV is None
        else os.environ.get(_RUNNER_EXCLUSION_ENV)
    )
    if raw is None:
        return None
    try:
        argv = tuple(getattr(config.invocation_params, "args", ()))
    except AttributeError as exc:
        raise pytest.UsageError(
            "runner exclusion token を検査できる pytest invocation がありません"
        ) from exc
    observed_tokens = tuple(
        token for token in argv
        if token.split("=", 1)[0] in _COLLECTION_NARROWING_OPTIONS
    )
    if not observed_tokens:
        return None
    if _SELECTION_CONTRACT is None:
        raise pytest.UsageError(
            "runner exclusion env は共有 selection contract を import できないため拒否します"
        )
    entries = _SELECTION_CONTRACT.canonicalize_sanctioned_exclusion_set(
        _SELECTION_CONTRACT.SANCTIONED_EXCLUSIONS
    )
    if entries is None or len(entries) != 1:
        raise pytest.UsageError(
            "runner exclusion contract は canonical exactly-one ではありません"
        )
    expected_payload = _SELECTION_CONTRACT.serialize_payload(
        entries
    )
    if raw != expected_payload:
        raise pytest.UsageError(
            "runner exclusion payload が共有 selection contract と一致しません"
        )
    expected_tokens = _SELECTION_CONTRACT.exclusion_tokens(
        entries
    )
    if observed_tokens != expected_tokens:
        raise pytest.UsageError(
            "runner exclusion token が共有 selection contract と一致しません"
        )
    return entries


def _emit_runner_exclusion_receipt(config) -> None:
    entries = _runner_owned_exclusion_payload(config)
    if entries is None or hasattr(config, "workerinput"):
        return
    assert _SELECTION_CONTRACT is not None
    print(
        _SELECTION_CONTRACT.selection_receipt_line(entries),
        file=sys.stderr,
        flush=True,
    )


def _is_un_narrowed_flaky_hold_collection(config) -> bool:
    """Return whether the invocation requests the whole tests suite root."""
    args = getattr(config, "args", None)
    invocation_params = getattr(config, "invocation_params", None)
    if args is None or invocation_params is None:
        # Some hook contract tests use a deliberately small synthetic config.
        # Missing invocation metadata must be treated as a narrowed/unknown
        # collection so stale-registry validation stays on the safe side.
        return False
    try:
        if len(args) != 1:
            return False
        target = _normalize_collection_path(args[0])
        suite_root = _normalize_collection_path(__file__).parent
    except (OSError, TypeError, ValueError):
        return False
    if target != suite_root:
        return False
    return _collection_narrowing_is_runner_owned(config)


def _is_complete_flaky_hold_collection(config) -> bool:
    """Return whether this process owns a complete, un-narrowed collection."""
    dsession = None
    if not hasattr(config, "workerinput"):
        try:
            dsession = config.pluginmanager.get_plugin("dsession")
        except AttributeError:
            # Small synthetic configs may not provide a plugin manager.  In
            # that case there is no xdist hook owner to delegate to.
            pass
    if dsession is not None:
        # The xdist controller receives worker collections through the
        # xdist-specific hook below, not through its local item list.
        return False
    return _is_un_narrowed_flaky_hold_collection(config)


def _check_flaky_hold_collection_complete(config, seen_ids) -> None:
    _ensure_flaky_test_holds_loaded()
    assert FLAKY_TEST_HOLDS is not None
    missing = sorted(set(FLAKY_TEST_HOLDS) - set(seen_ids))
    if missing:
        raise pytest.UsageError(
            "flaky-test hold keys missing from complete collection: "
            f"{missing!r}"
        )


def _validate_real_repo_shard_state(config) -> None:
    """Require shard closure to observe every resource marker before stripping."""
    if getattr(config, "_izanagi_acceptance_shard_spec", None) is None:
        return
    state = getattr(config, "_izanagi_acceptance_shard_state", None)
    if not isinstance(state, dict):
        raise pytest.UsageError(
            "acceptance shard state が real-repo suffix strip 前に確定していない"
        )
    records = state.get("records")
    if not isinstance(records, list):
        raise pytest.UsageError("acceptance shard records が real-repo 検査に使えない")
    observed: dict[str, set[object]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise pytest.UsageError("acceptance shard record の shape が不正")
        node_id = _receipt_memo_node_id_from_nodeid(str(record.get("nodeid", "")))
        if node_id in REAL_REPO_RESOURCE_NODES:
            observed.setdefault(node_id, set()).add(record.get("group"))
    missing = sorted(REAL_REPO_RESOURCE_NODES - set(observed))
    wrong = {
        node_id: sorted(repr(group) for group in groups)
        for node_id, groups in observed.items()
        if groups != {"real-repo"}
    }
    if missing or wrong:
        raise pytest.UsageError(
            "acceptance shard が real-repo marker 閉包を確定できない: "
            f"missing={missing!r} wrong={wrong!r}"
        )


def _strip_real_repo_loadgroup_suffix(item) -> bool:
    """Strip xdist's suffix except from exact process-memo work units."""
    node_id = _real_repo_node_id(item)
    if node_id not in REAL_REPO_RESOURCE_NODES:
        return False
    current = str(getattr(item, "nodeid", ""))
    suffix = "@real-repo"
    if node_id in REAL_REPO_PROCESS_MEMO_NODES:
        return False
    if not current.endswith(suffix):
        return False
    stripped = current[:-len(suffix)]
    if hasattr(item, "_nodeid"):
        item._nodeid = stripped
    else:
        item.nodeid = stripped
    return True


def _xdist_flaky_collection_is_complete(config) -> bool:
    """Check whether all xdist workers have reported their collections."""
    if getattr(config, "_izanagi_acceptance_shard_spec", None) is not None:
        # Shard workers validate the full collection before the shard plugin
        # deselects.  Their controller sees only the selected subset.
        return False
    if not _is_un_narrowed_flaky_hold_collection(config):
        return False
    try:
        dsession = config.pluginmanager.get_plugin("dsession")
        scheduler = getattr(dsession, "sched", None)
        expected = getattr(scheduler, "numnodes", None)
    except Exception:
        return False
    if not isinstance(expected, int) or expected < 1:
        return False
    finished = getattr(config, _FLAKY_HOLD_COLLECTION_WORKERS_ATTR, set())
    return len(finished) >= expected


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Attach shard markers, then split real-repo runtime work units."""
    _ensure_flaky_test_holds_loaded()
    opted_in = _growth_holds_opted_in()
    seen_hold_ids: set[str] = set()
    seen_flaky_hold_ids: set[str] = set()
    source_paths: dict[str, set[str]] = {}
    for item in items:
        node_id = _real_repo_node_id(item)
        access = REAL_REPO_ACCESS_BY_NODE.get(node_id)
        if access is not None:
            setattr(item, _REAL_REPO_ACCESS_ATTR, access)
        if node_id in REAL_REPO_RESOURCE_NODES:
            # xdist は複数 group 名を結合するため、二個目は足さない。
            if not list(item.iter_markers(name="xdist_group")):
                item.add_marker(pytest.mark.xdist_group("real-repo"))

        flaky_node_id = _flaky_hold_id_from_nodeid(
            str(getattr(item, "nodeid", ""))
        )
        if flaky_node_id is not None:
            flaky_hold = FLAKY_TEST_HOLDS[flaky_node_id]
            seen_flaky_hold_ids.add(flaky_node_id)
            _note_flaky_hold(config, flaky_node_id, skipped=True)
            item.add_marker(
                pytest.mark.skip(
                    reason=_flaky_hold_reason(flaky_node_id, flaky_hold)
                ),
                append=False,
            )
            item.user_properties.extend((
                ("flaky_hold_node_id", flaky_node_id),
                ("flaky_hold_evidence_id", flaky_hold.evidence_id),
                ("flaky_hold_reintroduction_task_id", flaky_hold.reintroduction_task_id),
            ))

        hold = GROWTH_TEST_HOLDS.get(node_id)
        if hold is None:
            continue
        seen_hold_ids.add(node_id)
        source_paths.setdefault(node_id, set()).add(str(Path(item.path).resolve()))
        _note_growth_hold(config, node_id)
        if not opted_in:
            item.add_marker(
                pytest.mark.skip(reason=_growth_hold_reason(node_id, hold)),
                append=False,
            )
        item.user_properties.extend((
            ("growth_hold_node_id", node_id),
            ("growth_hold_axis", hold.hold_axis),
            ("growth_hold_correctness_gate", hold.correctness_gate),
            ("growth_hold_release_condition", hold.release_condition),
        ))

    ambiguous = {
        node_id: sorted(paths)
        for node_id, paths in source_paths.items()
        if len(paths) > 1
    }
    if ambiguous:
        raise pytest.UsageError(f"ambiguous growth-test hold keys: {ambiguous!r}")
    if _is_complete_growth_hold_collection(config):
        missing = sorted(set(GROWTH_TEST_HOLDS) - seen_hold_ids)
        if missing:
            raise pytest.UsageError(
                f"growth-test hold keys missing from complete collection: {missing!r}"
            )
    if _is_complete_flaky_hold_collection(config):
        _check_flaky_hold_collection_complete(config, seen_flaky_hold_ids)
    yield
    _validate_real_repo_shard_state(config)
    for item in items:
        _strip_real_repo_loadgroup_suffix(item)
    if _acceptance_reordering_enabled(config):
        durations = getattr(
            config, _ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR, None,
        )
        if not isinstance(durations, dict):
            raise pytest.UsageError(
                "acceptance duration ledger が collection hook に配線されていない"
            )
        _reorder_acceptance_items_by_duration(items, durations)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    """Hold P/S locks and the access stamp across setup/call/teardown."""
    from orchestrator.campaign import patchharness

    node_id = _real_repo_node_id(item)
    expected_access = REAL_REPO_ACCESS_BY_NODE.get(node_id)
    stamped_access = getattr(item, _REAL_REPO_ACCESS_ATTR, None)
    if expected_access is not None and stamped_access != expected_access:
        raise pytest.UsageError(
            "real-repo resource access stamp mismatch; fails-closed: "
            f"node={node_id} expected={expected_access!r} "
            f"stamped={stamped_access!r}"
        )
    access = expected_access
    config = getattr(item, "config", None)
    with _acceptance_timed_real_repo_locks(config, access):
        with patchharness._pytest_node_context(node_id, access):
            return (yield)


_EARLY_MEMO_JOB_ATTR = "_izanagi_early_memo_job"
_EARLY_MEMO_INPUT_KEY = "izanagi_early_memo_paths"
_EARLY_MEMO_NARROWING_OPTIONS = (
    "keyword", "markexpr", "deselect", "lf", "failedfirst", "stepwise",
    "stepwise_skip", "ignore", "ignore_glob", "pyargs", "override_ini",
)


def _early_memo_selected(config) -> bool:
    """Parsed options include ini/addopts and environment selectors."""
    if (
        hasattr(config, "workerinput")
        or getattr(config, "_izanagi_acceptance_shard_spec", None) is None
    ):
        return False
    option = getattr(config, "option", None)
    if option is None or getattr(option, "collectonly", False):
        return False
    # last_failed is a defensive compatibility attribute, not a pytest destination.
    if getattr(option, "last_failed", False):
        return False
    # Append options retain empty arguments as [""], which is truthy. Empty
    # keyword/markexpr strings and absent append options do not narrow collection.
    if any(getattr(option, name, False) for name in _EARLY_MEMO_NARROWING_OPTIONS):
        return False
    return _is_un_narrowed_flaky_hold_collection(config)


def _start_early_memo_job(node) -> None:
    config = node.config
    job = getattr(config, _EARLY_MEMO_JOB_ATTR, None)
    if job is None:
        run_id = node.workerinput.get("testrunuid")
        if run_id is None:
            raise pytest.UsageError("early memo prewarm に testrunuid が無い")
        modules = (_receipt_memo_module(), _oracle_environment_memo_module())
        sessions = (
            getattr(config, _RECEIPT_MEMO_SESSION_ID_ATTR),
            getattr(config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR),
        )
        paths = []
        for module, session in zip(modules, sessions):
            head = module._repo_head()
            if head is None:
                raise pytest.UsageError("early memo cache HEAD が無い")
            path = module._session_cache_path(
                run_id=run_id, head=head, session_id=session,
            )
            if path is None:
                raise pytest.UsageError("early memo cache path が無い")
            paths.append(path)
        job = {"paths": tuple(map(str, paths)), "error": None, "thread": None,
               "run_id": run_id}
        # Publish every pending marker before any writer thread can start.
        created = []
        try:
            for path in paths:
                pending = path.with_name(f"{path.name}.pending")
                with pending.open("x"):
                    pass
                created.append(pending)
        except BaseException:
            for pending in created:
                pending.replace(pending.with_suffix(".failed"))
            raise
        setattr(config, _EARLY_MEMO_JOB_ATTR, job)

        def endpoint(index, prewarm):
            path = paths[index]
            pending = path.with_name(f"{path.name}.pending")
            try:
                prewarm(config, (), run_id=run_id, early=True)
                # Includes resolver, atomic store, unlock/close and repo-lock exit.
                pending.unlink()
            except BaseException:
                pending.replace(path.with_name(f"{path.name}.failed"))
                raise

        def run():
            try:
                _run_memo_prewarm_barrier(
                    lambda: endpoint(0, _prewarm_receipt_memo),
                    lambda: endpoint(1, _prewarm_oracle_environment_memo),
                    hook="configure_node",
                )
            except BaseException as exc:
                job["error"] = exc
                # Also covers thread startup failures before an endpoint ran.
                for path in paths:
                    pending = path.with_name(f"{path.name}.pending")
                    if pending.exists():
                        pending.replace(path.with_name(f"{path.name}.failed"))

        thread = threading.Thread(target=run, daemon=False)
        try:
            thread.start()
        except BaseException as exc:
            job["error"] = exc
            for path in paths:
                path.with_name(f"{path.name}.pending").replace(
                    path.with_name(f"{path.name}.failed"),
                )
            raise
        job["thread"] = thread
    if node.workerinput.get("testrunuid") != job["run_id"]:
        raise pytest.UsageError("early memo prewarm の run ID が worker 間で不一致")
    node.workerinput[_EARLY_MEMO_INPUT_KEY] = job["paths"]


def _wait_early_memo_job(config) -> None:
    workerinput = getattr(config, "workerinput", {})
    if _EARLY_MEMO_INPUT_KEY not in workerinput:
        return
    paths = workerinput[_EARLY_MEMO_INPUT_KEY]
    if not isinstance(paths, (list, tuple)) or len(paths) != 2 or any(
        not isinstance(path, str) or not path for path in paths
    ):
        raise pytest.UsageError("early memo job identity が不正")
    receipt = _receipt_memo_module()
    oracle = _oracle_environment_memo_module()
    # One shared budget for both memos; no resolver capability is exercised.
    deadline = time.monotonic() + min(
        receipt._EARLY_WAIT_TIMEOUT_S, oracle._EARLY_WAIT_TIMEOUT_S,
    )
    receipt._make_receipt_memo().get(early_job=paths[0], deadline=deadline)
    oracle._make_oracle_environment_memo().get(early_job=paths[1], deadline=deadline)


def _finish_early_memo_job(config) -> None:
    job = getattr(config, _EARLY_MEMO_JOB_ATTR, None)
    if job is None:
        return
    if job["thread"] is not None:
        job["thread"].join()
    if job["error"] is not None:
        raise job["error"]


def _run_memo_prewarm_barrier(receipt, oracle, *, hook: str) -> None:
    """Join both non-daemon jobs before returning or propagating either failure."""
    durations = [None, None]
    errors = [None, None]

    def timed(index, prewarm):
        _MEMO_PREWARM_TIMING.started = None
        try:
            prewarm()
        except BaseException as exc:
            errors[index] = exc
        finally:
            started = _MEMO_PREWARM_TIMING.started
            if started is not None:
                durations[index] = time.monotonic() - started

    started = time.monotonic()
    threads = [
        threading.Thread(target=timed, args=(0, receipt), daemon=False),
        threading.Thread(target=timed, args=(1, oracle), daemon=False),
    ]
    started_threads = []
    try:
        for thread in threads:
            thread.start()
            started_threads.append(thread)
    finally:
        for thread in started_threads:
            thread.join()
    elapsed = time.monotonic() - started
    if any(duration is not None for duration in durations):
        print(
            "IZANAGI_MEMO_PREWARM_V1 " + json.dumps({
                "hook": hook,
                "receipt_memo_s": durations[0],
                "oracle_environment_memo_s": durations[1],
                "barrier_s": elapsed,
            }, ensure_ascii=True, separators=(",", ":"), sort_keys=True),
            file=sys.stderr,
            flush=True,
        )
    receipt_error, oracle_error = errors
    if receipt_error is not None:
        if oracle_error is not None:
            # Explicit chaining retains both tracebacks; receipt is primary.
            raise receipt_error from oracle_error
        raise receipt_error
    if oracle_error is not None:
        raise oracle_error


@pytest.hookimpl(tryfirst=True)
def pytest_collection_finish(session) -> None:
    """Prewarm process memos and collect optional task-run stats."""
    # xdist worker もこの hook を通る。内側 helper guard と意図的に冗長な
    # defense-in-depth で、実解決を controller hook だけに限定する。
    def receipt():
        if not hasattr(session.config, "workerinput"):
            _prewarm_receipt_memo(
                session.config,
                (_real_repo_node_id(item) for item in session.items),
                run_id=None,
            )

    def oracle():
        if not hasattr(session.config, "workerinput"):
            _prewarm_oracle_environment_memo(
                session.config,
                (_real_repo_node_id(item) for item in session.items),
                run_id=None,
            )

    _wait_early_memo_job(session.config)
    _run_memo_prewarm_barrier(receipt, oracle, hook="collection_finish")
    if not os.environ.get("IZANAGI_TASK_RUN_SIDECAR"):
        return
    try:
        from tools.task_runs import pytest_stats

        pytest_stats.note_collection(session)
    except Exception:
        pass


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node) -> None:
    """controller の session nonce を xdist workerinput へ wire する。"""
    if hasattr(node.config, "workerinput"):
        return
    session_id = getattr(node.config, _RECEIPT_MEMO_SESSION_ID_ATTR, None)
    if not isinstance(session_id, str) or not session_id:
        raise pytest.UsageError("receipt memo controller session nonce が無い")
    workerinput = getattr(node, "workerinput", None)
    if not isinstance(workerinput, dict):
        raise pytest.UsageError("xdist workerinput が receipt memo nonce を受け取れない")
    workerinput[_RECEIPT_MEMO_SESSION_ID_ATTR] = session_id
    durations = getattr(
        node.config, _ACCEPTANCE_DURATION_LEDGER_CONFIG_ATTR, None,
    )
    if (
        isinstance(durations, dict)
        and _acceptance_controller_should_load_duration_ledger(node.config)
    ):
        workerinput[_ACCEPTANCE_DURATION_LEDGER_WORKERINPUT_KEY] = (
            _acceptance_duration_worker_payload(durations)
        )
    if hasattr(node.config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR):
        oracle_session_id = getattr(
            node.config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR, None,
        )
        if not isinstance(oracle_session_id, str) or not oracle_session_id:
            raise pytest.UsageError(
                "oracle environment memo controller session nonce が無い"
            )
        workerinput[_ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR] = oracle_session_id
    if _early_memo_selected(node.config):
        _start_early_memo_job(node)


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node, ids) -> None:
    """Collect controller-visible node IDs without persisting their names."""
    _ensure_flaky_test_holds_loaded()
    ids = tuple(ids)
    for nodeid in ids:
        hold_id = _growth_hold_id_from_nodeid(nodeid)
        if hold_id in GROWTH_TEST_HOLDS:
            _note_growth_hold(node.config, hold_id)
        flaky_hold_id = _flaky_hold_id_from_nodeid(nodeid)
        if flaky_hold_id is not None:
            _note_flaky_hold(node.config, flaky_hold_id, skipped=True)
    if not hasattr(node.config, "workerinput"):
        worker_key = getattr(getattr(node, "gateway", None), "id", None)
        if worker_key is None:
            worker_key = id(node)
        workers = getattr(node.config, _FLAKY_HOLD_COLLECTION_WORKERS_ATTR, None)
        if workers is None:
            workers = set()
            setattr(node.config, _FLAKY_HOLD_COLLECTION_WORKERS_ATTR, workers)
        workers.add(worker_key)
        if _xdist_flaky_collection_is_complete(node.config):
            _check_flaky_hold_collection_complete(
                node.config,
                getattr(node.config, _FLAKY_HOLD_MATCHED_IDS_ATTR, ()),
            )
    def receipt():
        if (
            not hasattr(node.config, "workerinput")
            and _receipt_memo_prewarm_prerequisites(node.config, ids)
        ):
            run_id_available = True
            try:
                run_id = getattr(node, "workerinput", {}).get("testrunuid")
                if run_id is None:
                    run_id = node.config.getoption("testrunuid", None)
            except Exception:
                run_id = None
                run_id_available = False
            if run_id_available and run_id is None:
                raise pytest.UsageError("xdist receipt memo consumer に testrunuid が無い")
            if run_id_available:
                _prewarm_receipt_memo(node.config, ids, run_id=run_id)

    def oracle():
        if (
            not hasattr(node.config, "workerinput")
            and _oracle_environment_memo_prewarm_prerequisites(node.config, ids)
        ):
            run_id_available = True
            try:
                run_id = getattr(node, "workerinput", {}).get("testrunuid")
                if run_id is None:
                    run_id = node.config.getoption("testrunuid", None)
            except Exception:
                run_id = None
                run_id_available = False
            if run_id_available and run_id is None:
                raise pytest.UsageError(
                    "xdist oracle environment memo consumer に testrunuid が無い"
                )
            if run_id_available:
                _prewarm_oracle_environment_memo(node.config, ids, run_id=run_id)

    if getattr(node.config, _EARLY_MEMO_JOB_ATTR, None) is None:
        _run_memo_prewarm_barrier(
            receipt, oracle, hook="xdist_node_collection_finished",
        )
    if not os.environ.get("IZANAGI_TASK_RUN_SIDECAR"):
        return
    try:
        from tools.task_runs import pytest_stats

        pytest_stats.note_xdist_collection(node, ids)
    except Exception:
        pass


def _effective_scheduler(config) -> str:
    """Classify the scheduler object actually retained by xdist's DSession."""
    try:
        dsession = config.pluginmanager.get_plugin("dsession")
    except Exception:
        return "unknown"
    if dsession is None:
        return "serial"
    try:
        sched = dsession.sched
        from xdist.scheduler import LoadGroupScheduling

        if type(sched) is LoadGroupScheduling:
            return "loadgroup"
    except Exception:
        pass
    return "unknown"


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtestloop(session):
    """Freeze the controller scheduler immediately after xdist has used it."""
    controller = not hasattr(session.config, "workerinput")
    result = yield
    if controller and not hasattr(session.config, _EFFECTIVE_SCHEDULER_ATTR):
        setattr(
            session.config,
            _EFFECTIVE_SCHEDULER_ATTR,
            _effective_scheduler(session.config),
        )
    return result


def _emit_effective_scheduler_marker(config) -> None:
    pluginmanager = getattr(config, "pluginmanager", None)
    if pluginmanager is None or not callable(getattr(pluginmanager, "get_plugin", None)):
        return
    scheduler = getattr(config, _EFFECTIVE_SCHEDULER_ATTR, None)
    if scheduler is None:
        scheduler = _effective_scheduler(config)
    payload = json.dumps(
        {"effective_scheduler": scheduler},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    marker = _EFFECTIVE_SCHEDULER_PREFIX + payload
    print(marker, flush=True)


def pytest_sessionfinish(session, exitstatus) -> None:
    """Create the private aggregate sidecar on the controller only."""
    if not hasattr(session.config, "workerinput"):
        _ensure_flaky_test_holds_loaded()
        terminal = session.config.pluginmanager.get_plugin("terminalreporter")
        held_ids = sorted(getattr(session.config, _GROWTH_HOLD_IDS_ATTR, ()))
        if terminal is not None and held_ids:
            opted_in = _growth_holds_opted_in()
            summary = json.dumps({
                "collected_hold_functions": len(held_ids),
                "opted_in": opted_in,
            }, separators=(",", ":"), sort_keys=True)
            terminal.write_line(f"IZANAGI_GROWTH_HOLD_SUMMARY_V1 {summary}")
            for node_id in held_ids:
                terminal.write_line(_growth_hold_reason(
                    node_id, GROWTH_TEST_HOLDS[node_id],
                ))
        if terminal is not None:
            assert FLAKY_TEST_HOLDS is not None
            matched_ids = set(getattr(
                session.config, _FLAKY_HOLD_MATCHED_IDS_ATTR, ()
            )) & set(FLAKY_TEST_HOLDS)
        if terminal is not None and (
            matched_ids
            or (
                not FLAKY_TEST_HOLDS
                and getattr(session.config, "invocation_params", None) is not None
            )
        ):
            skipped_ids = set(getattr(
                session.config, _FLAKY_HOLD_SKIPPED_IDS_ATTR, ()
            )) & set(FLAKY_TEST_HOLDS)
            summary = {
                "registered_node_count": len(FLAKY_TEST_HOLDS),
                "matched_node_count": len(matched_ids),
                "skipped_node_count": len(skipped_ids),
                "registry_sha256": FLAKY_TEST_HOLDS_SHA256,
            }
            terminal.write_line(
                _FLAKY_HOLD_SUMMARY_PREFIX + json.dumps(
                    summary, ensure_ascii=True, separators=(",", ":")
                )
            )
    if not os.environ.get("IZANAGI_TASK_RUN_SIDECAR"):
        return
    try:
        from tools.task_runs import pytest_stats

        pytest_stats.write_session_stats(session)
    except Exception:
        pass


# pytest 完走時に failure 本体を relay の末尾へ残す bounded digest。relay 定数は
# plain runner の conftest import を壊さないよう、failure 検出後にだけ lazy import する。
_FAILURE_DIGEST_START = "=== IZANAGI FAILURE DIGEST v1 BEGIN ==="
_FAILURE_DIGEST_END = "=== IZANAGI FAILURE DIGEST v1 END ==="
_FAILURE_DIGEST_NUMERATOR = 3
_FAILURE_DIGEST_DENOMINATOR = 4
_FAILURE_EXCERPT_MAX_BYTES = 4 * 1024
_FAILURE_ENTRY_MAX_BYTES = 5 * 1024
_FAILURE_FRAME_ACCOUNT_RESERVE_BYTES = 1024
_FAILURE_NODEID_DISPLAY_MAX_BYTES = 256
_FAILURE_MANIFEST_PLACEHOLDER = "0" * 64


@dataclass(frozen=True)
class _StashedFailure:
    category: str
    report: object


@dataclass(frozen=True)
class _FailureDigestItem:
    category: str
    nodeid: str
    when: str
    source: str
    source_bytes: int
    sha256: str

    @property
    def source_file(self) -> str:
        return self.nodeid.split("::", 1)[0]


# pytest_runtest_logreport / pytest_collectreport は Config を受け取らないため、process
# local な session stash を使う。xdist controller/worker は別 process であり、逐次の
# pytest.main() 再入では configure ごとに初期化して前 session の report を持ち越さない。
# 同一 process の入れ子 session は内側 configure が外側 stash を消す現行制約を持つ。
_FAILURE_REPORTS: list[_StashedFailure] = []


def _configure_receipt_memo_run_id(config) -> None:
    """xdist NodeManager が読む前に controller の UID を確定する。"""
    if hasattr(config, "workerinput"):
        return
    numprocesses = config.getoption("numprocesses", None)
    if numprocesses in (None, 0, "0"):
        return
    run_id = config.getoption("testrunuid", None)
    if run_id is None:
        config.option.testrunuid = uuid.uuid4().hex


def _configure_receipt_memo_session(config) -> None:
    """Config ごとに nonce を保存し、worker は controller nonce を再利用する。"""
    previous = os.environ.get(
        _RECEIPT_MEMO_NONCE_ENV, _RECEIPT_MEMO_ENV_UNSET,
    )
    setattr(config, _RECEIPT_MEMO_NONCE_PREVIOUS_ATTR, previous)
    setattr(config, _RECEIPT_MEMO_NONCE_ACTIVE_ATTR, True)
    try:
        if hasattr(config, "workerinput"):
            session_id = getattr(config, "workerinput", {}).get(
                _RECEIPT_MEMO_SESSION_ID_ATTR,
            )
            if not isinstance(session_id, str) or not session_id:
                raise pytest.UsageError(
                    "receipt memo worker に controller session nonce が無い"
                )
        else:
            session_id = uuid.uuid4().hex
        setattr(config, _RECEIPT_MEMO_SESSION_ID_ATTR, session_id)
        os.environ[_RECEIPT_MEMO_NONCE_ENV] = session_id
    except BaseException:
        try:
            _restore_receipt_memo_nonce(config)
        except BaseException:
            # The configure failure is the useful exception and must remain primary.
            pass
        raise


def _restore_receipt_memo_nonce(config) -> None:
    """Config ごとの旧 env 値を、入れ子・例外経路を含めて一度だけ戻す。"""
    if not getattr(config, _RECEIPT_MEMO_NONCE_ACTIVE_ATTR, False):
        return
    previous = getattr(
        config, _RECEIPT_MEMO_NONCE_PREVIOUS_ATTR, _RECEIPT_MEMO_ENV_UNSET,
    )
    try:
        if previous is _RECEIPT_MEMO_ENV_UNSET:
            os.environ.pop(_RECEIPT_MEMO_NONCE_ENV, None)
        else:
            os.environ[_RECEIPT_MEMO_NONCE_ENV] = previous
    finally:
        setattr(config, _RECEIPT_MEMO_NONCE_ACTIVE_ATTR, False)


def _finish_receipt_memo_session(config) -> None:
    """終了 Config の memo state を破棄し、入れ子なら外側 state を復元する。"""
    if not getattr(config, _RECEIPT_MEMO_SESSION_ACTIVE_ATTR, False):
        return
    session_id = getattr(config, _RECEIPT_MEMO_SESSION_ID_ATTR, None)
    _receipt_memo_module().finish_real_repo_receipt_session(
        session_id=session_id,
    )
    setattr(config, _RECEIPT_MEMO_SESSION_ACTIVE_ATTR, False)


def _configure_oracle_environment_memo_session(config) -> None:
    """Create a per-Config nonce and propagate it to xdist workers."""
    previous = os.environ.get(
        _ORACLE_ENVIRONMENT_MEMO_NONCE_ENV,
        _ORACLE_ENVIRONMENT_MEMO_ENV_UNSET,
    )
    setattr(config, _ORACLE_ENVIRONMENT_MEMO_NONCE_PREVIOUS_ATTR, previous)
    setattr(config, _ORACLE_ENVIRONMENT_MEMO_NONCE_ACTIVE_ATTR, True)
    try:
        if hasattr(config, "workerinput"):
            session_id = getattr(config, "workerinput", {}).get(
                _ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR,
            )
            if not isinstance(session_id, str) or not session_id:
                raise pytest.UsageError(
                    "oracle environment memo worker に controller session nonce が無い"
                )
        else:
            session_id = uuid.uuid4().hex
        setattr(config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR, session_id)
        os.environ[_ORACLE_ENVIRONMENT_MEMO_NONCE_ENV] = session_id
    except BaseException:
        try:
            _restore_oracle_environment_memo_nonce(config)
        except BaseException:
            pass
        raise


def _restore_oracle_environment_memo_nonce(config) -> None:
    """Restore the outer oracle memo nonce exactly once."""
    if not getattr(config, _ORACLE_ENVIRONMENT_MEMO_NONCE_ACTIVE_ATTR, False):
        return
    previous = getattr(
        config,
        _ORACLE_ENVIRONMENT_MEMO_NONCE_PREVIOUS_ATTR,
        _ORACLE_ENVIRONMENT_MEMO_ENV_UNSET,
    )
    try:
        if previous is _ORACLE_ENVIRONMENT_MEMO_ENV_UNSET:
            os.environ.pop(_ORACLE_ENVIRONMENT_MEMO_NONCE_ENV, None)
        else:
            os.environ[_ORACLE_ENVIRONMENT_MEMO_NONCE_ENV] = previous
    finally:
        setattr(config, _ORACLE_ENVIRONMENT_MEMO_NONCE_ACTIVE_ATTR, False)


def _finish_oracle_environment_memo_session(config) -> None:
    """Discard a successful oracle memo session, preserving nested sessions."""
    if not getattr(config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ACTIVE_ATTR, False):
        return
    session_id = getattr(config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ID_ATTR, None)
    _oracle_environment_memo_module().finish_oracle_environment_session(
        session_id=session_id,
    )
    setattr(config, _ORACLE_ENVIRONMENT_MEMO_SESSION_ACTIVE_ATTR, False)


def _finish_memo_sessions(config, *, suppress_errors: bool) -> None:
    """Finish receipt and oracle sessions independently, preserving first error."""
    first_error: BaseException | None = None
    first_traceback = None
    for finish in (_finish_early_memo_job, _finish_receipt_memo_session, _finish_oracle_environment_memo_session):
        try:
            finish(config)
        except BaseException as exc:
            if first_error is None:
                first_error = exc
                first_traceback = exc.__traceback__
    if first_error is not None and not suppress_errors:
        raise first_error.with_traceback(first_traceback)


def pytest_configure(config) -> None:
    _emit_runner_exclusion_receipt(config)
    try:
        _configure_acceptance_duration_ledger(config)
        _configure_receipt_memo_session(config)
        _configure_oracle_environment_memo_session(config)
        _configure_receipt_memo_run_id(config)
        _growth_holds_opted_in()
        if mark_pytest_session_enforcing is not None:
            mark_pytest_session_enforcing(config)
        _FAILURE_REPORTS.clear()
    except BaseException:
        try:
            _restore_receipt_memo_nonce(config)
        except BaseException:
            # Preserve the configure failure instead of replacing it with cleanup.
            pass
        try:
            _restore_oracle_environment_memo_nonce(config)
        except BaseException:
            pass
        raise


def pytest_runtest_logreport(report) -> None:
    if report.failed:
        category = "failed" if getattr(report, "when", "") == "call" else "error"
        _FAILURE_REPORTS.append(_StashedFailure(category, report))


def pytest_collectreport(report) -> None:
    if report.failed:
        _FAILURE_REPORTS.append(_StashedFailure("error", report))


def _canonical_ascii(value: str) -> str:
    r"""非 ASCII、C0、DEL、backslash を一意な ASCII 表現へ escape する。"""
    rendered: list[str] = []
    for char in value:
        codepoint = ord(char)
        if char == "\\":
            rendered.append(r"\x5c")
        elif 0x20 <= codepoint < 0x7f:
            rendered.append(char)
        elif codepoint <= 0xff:
            rendered.append(f"\\x{codepoint:02x}")
        elif codepoint <= 0xffff:
            rendered.append(f"\\u{codepoint:04x}")
        else:
            rendered.append(f"\\U{codepoint:08x}")
    return "".join(rendered)


def _bounded_rendered_tail(value: str, max_bytes: int) -> tuple[str, int]:
    """escape 後 byte 枠に収まる Unicode code point 境界の source tail を返す。"""
    selected: list[tuple[str, str]] = []
    used = 0
    for char in reversed(value):
        escaped = _canonical_ascii(char)
        width = len(escaped.encode("ascii"))
        if used + width > max_bytes:
            break
        selected.append((char, escaped))
        used += width
    selected.reverse()
    return (
        "".join(escaped for _char, escaped in selected),
        len("".join(char for char, _escaped in selected).encode("utf-8")),
    )


def _render_failure_lines(value: str) -> str:
    """論理 LF を物理行へ戻し、consumer が剥がさない prefix を全行へ付ける。"""
    lines = value.split("\n")
    if value.endswith("\n"):
        lines.pop()
    if not lines:
        lines = [""]
    rendered: list[str] = []
    for line in lines:
        escaped = _canonical_ascii(line)
        if escaped.startswith("FAILED "):
            escaped = "! " + escaped
        rendered.append(f"> {escaped}\n")
    return "".join(rendered)


def _bounded_failure_excerpt_tail(value: str, max_bytes: int) -> tuple[str, int]:
    """全物理行の frame を含む byte 枠に収まる source tail を返す。"""
    selected_reversed: list[str] = []
    retained_bytes = 0
    # 空 source でも ``> \n`` を出す。末尾 LF はこの終端改行と共有できる。
    used = len("> \n")
    have_selected = False
    first_line_prefix = ""
    first_line_neutralized = False
    for char in reversed(value):
        if char == "\n":
            width = len("\n> ") if have_selected else 0
            next_prefix = ""
            next_neutralized = False
        else:
            next_prefix = (char + first_line_prefix)[:len("FAILED ")]
            next_neutralized = next_prefix == "FAILED "
            width = len(_canonical_ascii(char).encode("ascii"))
            if next_neutralized and not first_line_neutralized:
                width += len("! ")
            elif first_line_neutralized and not next_neutralized:
                width -= len("! ")
        if used + width > max_bytes:
            break
        selected_reversed.append(char)
        retained_bytes += len(char.encode("utf-8"))
        used += width
        have_selected = True
        first_line_prefix = next_prefix
        first_line_neutralized = next_neutralized
    selected_reversed.reverse()
    selected = "".join(selected_reversed)
    excerpt = _render_failure_lines(selected)
    assert len(excerpt.encode("ascii")) == used
    return excerpt, retained_bytes


def _render_failure_excerpt(item: _FailureDigestItem) -> tuple[str, int]:
    excerpt, retained_bytes = _bounded_failure_excerpt_tail(
        item.source, _FAILURE_EXCERPT_MAX_BYTES,
    )
    assert len(excerpt.encode("ascii")) <= _FAILURE_EXCERPT_MAX_BYTES
    return excerpt, retained_bytes


def _render_nodeid(nodeid: str) -> tuple[str, int, int]:
    source_bytes = len(nodeid.encode("utf-8"))
    rendered, retained_bytes = _bounded_rendered_tail(
        nodeid, _FAILURE_NODEID_DISPLAY_MAX_BYTES,
    )
    return rendered, source_bytes, source_bytes - retained_bytes


def _item_sort_key(item: _FailureDigestItem) -> tuple[object, ...]:
    return (-item.source_bytes, item.nodeid, item.when, item.sha256)


def _stable_failure_order(
    items: Sequence[_FailureDigestItem],
) -> list[_FailureDigestItem]:
    """xdist 到着順に依存しない error/failed・source representative 順。"""
    ordered: list[_FailureDigestItem] = []
    for category in ("error", "failed"):
        category_items = sorted(
            (item for item in items if item.category == category),
            key=_item_sort_key,
        )
        representatives: list[_FailureDigestItem] = []
        remaining: list[_FailureDigestItem] = []
        seen_sources: set[str] = set()
        for item in category_items:
            if item.source_file not in seen_sources:
                seen_sources.add(item.source_file)
                representatives.append(item)
            else:
                remaining.append(item)
        ordered.extend(sorted(representatives, key=_item_sort_key))
        ordered.extend(sorted(remaining, key=_item_sort_key))
    return ordered


def _digest_items(stashed: Iterable[_StashedFailure]) -> list[_FailureDigestItem]:
    items: list[_FailureDigestItem] = []
    for stashed_failure in stashed:
        report = stashed_failure.report
        source = str(report.longreprtext)
        source_raw = source.encode("utf-8")
        items.append(_FailureDigestItem(
            category=stashed_failure.category,
            nodeid=str(report.nodeid),
            when=str(getattr(report, "when", "collect")),
            source=source,
            source_bytes=len(source_raw),
            sha256=hashlib.sha256(source_raw).hexdigest(),
        ))
    return _stable_failure_order(items)


def _render_failure_block(
    item: _FailureDigestItem, rank: int,
) -> tuple[str, int]:
    excerpt, retained_bytes = _render_failure_excerpt(item)
    nodeid, nodeid_bytes, nodeid_omitted_bytes = _render_nodeid(item.nodeid)
    header = (
        f"IZANAGI_FAILURE rank={rank} category={item.category} when={_canonical_ascii(item.when)} "
        f"nodeid={json.dumps(nodeid, ensure_ascii=True, separators=(',', ':'))} "
        f"nodeid_bytes={nodeid_bytes} nodeid_omitted_bytes={nodeid_omitted_bytes} "
        f"source_bytes={item.source_bytes} retained_bytes={retained_bytes} "
        f"omitted_bytes={item.source_bytes - retained_bytes} "
        f"rendered_excerpt_bytes={len(excerpt.encode('ascii'))} sha256={item.sha256}\n"
    )
    block = (
        header
        + f"--- IZANAGI FAILURE EXCERPT rank={rank} BEGIN ---\n"
        + excerpt
        + f"--- IZANAGI FAILURE EXCERPT rank={rank} END ---\n"
    )
    if len(block.encode("ascii")) > _FAILURE_ENTRY_MAX_BYTES:
        raise ValueError("failure digest entry が byte 予算を超えました")
    return block, retained_bytes


def _omitted_manifest_sha256(items: Sequence[_FailureDigestItem]) -> str:
    if not items:
        return "-"
    ordered = sorted(
        items,
        key=lambda item: (
            item.nodeid, item.when, item.source_bytes, item.sha256,
        ),
    )
    canonical = "".join(
        json.dumps(
            {
                "nodeid": item.nodeid,
                "when": item.when,
                "source_bytes": item.source_bytes,
                "sha256": item.sha256,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
        for item in ordered
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _compose_failure_digest(
    items: Sequence[_FailureDigestItem],
    selected_count: int,
    budget_bytes: int,
    rendered_blocks: Sequence[str],
    retained_bytes: int,
    omitted_manifest: str,
) -> str:
    omitted = items[selected_count:]
    source_bytes = sum(item.source_bytes for item in items)
    failed = sum(item.category == "failed" for item in items)
    errors = len(items) - failed
    rendered_bytes = -1
    for _attempt in range(10):
        account = (
            "IZANAGI_FAILURE_DIGEST_ACCOUNT "
            f"failures={len(items)} failed={failed} errors={errors} "
            f"selected={selected_count} omitted_failures={len(omitted)} "
            f"source_bytes={source_bytes} retained_bytes={retained_bytes} "
            f"omitted_bytes={source_bytes - retained_bytes} budget_bytes={budget_bytes} "
            f"rendered_bytes={rendered_bytes} "
            f"omitted_manifest_sha256={omitted_manifest}\n"
        )
        digest = (
            _FAILURE_DIGEST_START + "\n"
            + "".join(rendered_blocks)
            + account
            + _FAILURE_DIGEST_END + "\n"
        )
        actual_bytes = len(digest.encode("ascii"))
        if actual_bytes == rendered_bytes:
            return digest
        rendered_bytes = actual_bytes
    raise RuntimeError("failure digest rendered_bytes が収束しません")


def _render_failure_digest(
    items: Sequence[_FailureDigestItem], selected_count: int, budget_bytes: int,
) -> str:
    rendered_blocks: list[str] = []
    retained_bytes = 0
    for rank, item in enumerate(items[:selected_count], start=1):
        block, retained = _render_failure_block(item, rank)
        rendered_blocks.append(block)
        retained_bytes += retained
    return _compose_failure_digest(
        items,
        selected_count,
        budget_bytes,
        rendered_blocks,
        retained_bytes,
        _omitted_manifest_sha256(items[selected_count:]),
    )


def _build_failure_digest(
    stashed: Sequence[_StashedFailure],
    budget_bytes: int,
    *,
    block_renderer: Callable[[_FailureDigestItem, int], tuple[str, int]] = _render_failure_block,
    manifest_renderer: Callable[
        [Sequence[_FailureDigestItem]], str
    ] = _omitted_manifest_sha256,
) -> str:
    items = _digest_items(stashed)
    empty_manifest = _FAILURE_MANIFEST_PLACEHOLDER if items else "-"
    empty = _compose_failure_digest(
        items, 0, budget_bytes, (), 0, empty_manifest,
    )
    if len(empty.encode("ascii")) > _FAILURE_FRAME_ACCOUNT_RESERVE_BYTES:
        raise ValueError("failure digest frame/account 予約を超えました")

    best_selected_count = 0
    best_retained_bytes = 0
    rendered_blocks: list[str] = []
    retained_bytes = 0
    for rank, item in enumerate(items, start=1):
        block, retained = block_renderer(item, rank)
        rendered_blocks.append(block)
        retained_bytes += retained
        # omitted manifest は実 hash と同じ 64 bytes の placeholder で予算を
        # 判定する。omitted なしの `-` は既存表現を保つ。
        omitted_manifest = (
            _FAILURE_MANIFEST_PLACEHOLDER if rank < len(items) else "-"
        )
        candidate = _compose_failure_digest(
            items,
            rank,
            budget_bytes,
            rendered_blocks,
            retained_bytes,
            omitted_manifest,
        )
        if len(candidate.encode("ascii")) > budget_bytes:
            break
        best_selected_count = rank
        best_retained_bytes = retained_bytes

    omitted_manifest = manifest_renderer(items[best_selected_count:])
    return _compose_failure_digest(
        items,
        best_selected_count,
        budget_bytes,
        rendered_blocks[:best_selected_count],
        best_retained_bytes,
        omitted_manifest,
    )


def _load_failure_digest_budget() -> int:
    from tools.pegasus.dispatch_compute import DEFAULT_FAILURE_RELAY_LIMIT_BYTES

    return (
        DEFAULT_FAILURE_RELAY_LIMIT_BYTES
        * _FAILURE_DIGEST_NUMERATOR
        // _FAILURE_DIGEST_DENOMINATOR
    )


def _write_failure_digest(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def _write_failure_digest_error(writer: Callable[[str], None], exc: Exception) -> None:
    error_line = (
        "=== IZANAGI FAILURE DIGEST v1 ERROR exception="
        f"{_canonical_ascii(type(exc).__name__)} ===\n"
    )
    try:
        writer(error_line)
    except Exception:
        pass


def _emit_failure_digest(
    stashed: Sequence[_StashedFailure],
    *,
    budget_loader: Callable[[], int] = _load_failure_digest_budget,
    builder: Callable[[Sequence[_StashedFailure], int], str] = _build_failure_digest,
    writer: Callable[[str], None] = _write_failure_digest,
) -> None:
    # 緑走行では lazy import・builder・writer のすべてを呼ばない。
    if not stashed:
        return
    try:
        budget_bytes = budget_loader()
    except ModuleNotFoundError as exc:
        if exc.name == "tools":
            return
        _write_failure_digest_error(writer, exc)
        return
    except ImportError as exc:
        _write_failure_digest_error(writer, exc)
        return
    except Exception as exc:
        _write_failure_digest_error(writer, exc)
        return
    try:
        writer(builder(stashed, budget_bytes))
    except Exception as exc:
        # digest は表示専用。通常例外で pytest の元 exit code を変えない。
        _write_failure_digest_error(writer, exc)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_unconfigure(config):
    inner_exception: BaseException | None = None
    try:
        yield
    except BaseException as exc:
        inner_exception = exc
        raise
    finally:
        cleanup_exception: BaseException | None = None
        try:
            if unmark_pytest_session_enforcing is not None:
                unmark_pytest_session_enforcing(config)
            memo_cleanup_exception = None
            try:
                _finish_memo_sessions(
                    config, suppress_errors=inner_exception is not None,
                )
            except BaseException as exc:
                memo_cleanup_exception = exc
            stashed = tuple(_FAILURE_REPORTS)
            _FAILURE_REPORTS.clear()
            # finally 内で return すると inner hook の例外を StopIteration で消すため、
            # worker/green とも条件分岐だけで通過する。
            if not hasattr(config, "workerinput"):
                if inner_exception is None:
                    _emit_effective_scheduler_marker(config)
                else:
                    try:
                        _emit_effective_scheduler_marker(config)
                    except BaseException:
                        pass
            if not hasattr(config, "workerinput") and stashed:
                if inner_exception is None:
                    _emit_failure_digest(stashed)
                else:
                    # inner hook の元例外を最優先する。digest は試みるが、同時に
                    # emitter が投げた BaseException も含めて元例外を置換させない。
                    try:
                        _emit_failure_digest(stashed)
                    except BaseException:
                        pass
            if memo_cleanup_exception is not None:
                raise memo_cleanup_exception
        except BaseException as exc:
            cleanup_exception = exc
            raise
        finally:
            try:
                _restore_receipt_memo_nonce(config)
            except BaseException:
                # yield または cleanup の元例外を env cleanup で隠さない。
                if inner_exception is not None or cleanup_exception is not None:
                    pass
                else:
                    raise
            try:
                _restore_oracle_environment_memo_nonce(config)
            except BaseException:
                if inner_exception is not None or cleanup_exception is not None:
                    pass
                else:
                    raise
