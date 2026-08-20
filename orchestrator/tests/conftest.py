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
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType, SimpleNamespace
from typing import Callable, Iterable, Sequence

import pytest


_RATIFICATION_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)

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


@pytest.fixture
def _detect_site_under_test():
    """Allow site-policy unit tests to exercise the real detector explicitly."""


def _ratification_fixture_git(repo: Path, *args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        pytest.fail("ratified enforcement-source fixture requires git")
    env = {
        key: os.environ[key]
        for key in _RATIFICATION_GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    completed = subprocess.run(
        [executable, "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
        timeout=30,
    )
    if completed.returncode != 0:
        pytest.fail(
            "ratified enforcement-source fixture git failed: "
            f"args={args!r} "
            f"stderr={completed.stderr.decode(errors='replace')!r}"
        )
    return completed.stdout


@pytest.fixture
def ratified_enforcement_source(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
):
    """Opt in to a committed temporary ledger for the current exact closure."""
    from orchestrator.campaign import contract_loader_binding
    from orchestrator.campaign import enforcement_source_ratification as ratification

    binding = contract_loader_binding.capture_contract_loader_binding()
    digest = ratification.closure_digest_sha256(
        binding.contract_loader_blob_sha256s
    )
    repo = tmp_path_factory.mktemp("ratified-enforcement-source") / "repo"
    repo.mkdir()
    _ratification_fixture_git(repo, "init", "-q")
    marker = repo / "marker"
    marker.write_text("ratification fixture\n", encoding="ascii")
    _ratification_fixture_git(repo, "add", "--", "marker")
    identity = (
        "-c", "user.email=ratification-fixture@example.invalid",
        "-c", "user.name=Ratification fixture",
    )
    _ratification_fixture_git(
        repo, *identity, "commit", "-q", "-m", "initialize fixture",
    )
    ledger = repo / ratification.RATIFICATION_LEDGER_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_bytes(
        json.dumps(
            {"schema_version": 1, "closure_digest_sha256": digest},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii") + b"\n"
    )
    _ratification_fixture_git(
        repo, "add", "--", ratification.RATIFICATION_LEDGER_RELATIVE_PATH,
    )
    _ratification_fixture_git(
        repo, *identity, "commit", "-q", "-m", "record ratification",
    )
    monkeypatch.setattr(ratification, "_REPO_ROOT", repo)
    return digest


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


# 単一 pytest runner invocation 内で、親 repo status と共有 ccbench worktree の
# reader/writer を同じ xdist loadgroup に閉じ込める正本。値は
# ``test_file.py::test_function``（parametrize suffix なし）で固定する。
REAL_REPO_SERIAL_NODES = frozenset({
    # 親 working tree の tracked + untracked snapshot。
    "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
    # 上記 snapshot テストの結線監査 meta-テスト。実 ROOT で builder を実走し repo tree
    # snapshot を取るため、writer の patch 窓と同じ競合面にある (D63 列挙漏れの補完)。
    "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",

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
    "test_sort_swo_oracle.py::test_cpp_e2e_clean_generic_lambda_positive",
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

    # module fixture が実 repo を clone し、実 submodule を local source として読む reader。
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
    "test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch",
    "test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation",

    # helper が実親 repo と実共有 submodule を clone source として直接読む reader。
    "test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e",

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

# real-repo worker の先頭で独立 CLI 解決を開始し、旧 lazy payer node の優先順を保つ。
# receipt cache の correctness barrier は test scheduling 前の prewarm hook が担う。
# この 2 node 以外は collection 時点の相対順を維持する。
REAL_REPO_EXECUTION_PRIORITY = (
    "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
    "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
)

# production receipt memo を test body 内で読む関数の完全 inventory。parametrize suffix と
# loadgroup suffix は除いた ``file::function`` 形で固定する。32 関数 / 35 node。
RECEIPT_MEMO_CONSUMER_NODES = frozenset({
    "test_s8b_oracle_driver.py::test_success_wal_order_budget_and_evaluate_contract",
    "test_s8b_oracle_driver.py::test_oracle_pipeline_contract_keyword_is_mandatory_positive_control",
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


def _real_repo_node_id(item) -> str:
    """Collected item を正本の ``module::function`` 形へ正規化する。"""
    function = getattr(item, "originalname", None) or item.name.split("[", 1)[0]
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


_RECEIPT_MEMO_PREWARMED_ATTR = "_izanagi_receipt_memo_prewarmed"
_RECEIPT_MEMO_RUN_ID_ATTR = "_izanagi_receipt_memo_run_id"
_RECEIPT_MEMO_SESSION_ID_ATTR = "_izanagi_receipt_memo_session_id"
_RECEIPT_MEMO_SESSION_ACTIVE_ATTR = "_izanagi_receipt_memo_session_active"
_RECEIPT_MEMO_NONCE_ENV = "IZANAGI_RECEIPT_MEMO_NONCE"
_RECEIPT_MEMO_NONCE_PREVIOUS_ATTR = "_izanagi_receipt_memo_nonce_previous"
_RECEIPT_MEMO_NONCE_ACTIVE_ATTR = "_izanagi_receipt_memo_nonce_active"
_RECEIPT_MEMO_ENV_UNSET = object()


def _prewarm_receipt_memo(config, nodeids, *, run_id: str | None) -> None:
    """consumer がある controller/serial collection だけを一度 prewarm する。"""
    # pytest_collection_finish の外側 guard と意図的に冗長な defense-in-depth。
    # worker payer は両 guard が同時に失われない限り再発しない。
    if hasattr(config, "workerinput"):
        return
    nodeids = tuple(nodeids)
    if not _receipt_memo_prewarm_prerequisites(config, nodeids):
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
    memo_module = _receipt_memo_module()
    try:
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


_GROWTH_HOLD_IDS_ATTR = "_izanagi_collected_growth_hold_ids"
_REAL_REPO_SERIAL_NODE_ATTR = "_izanagi_real_repo_serial_node"
_COLLECTION_NARROWING_OPTIONS = frozenset({"--ignore", "--ignore-glob", "--pyargs"})
_EFFECTIVE_SCHEDULER_PREFIX = "IZANAGI_EFFECTIVE_SCHEDULER_V1 "
_EFFECTIVE_SCHEDULER_ATTR = "_izanagi_effective_scheduler"


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


def _note_growth_hold(config, node_id: str) -> None:
    held = getattr(config, _GROWTH_HOLD_IDS_ATTR, None)
    if held is None:
        held = set()
        setattr(config, _GROWTH_HOLD_IDS_ATTR, held)
    held.add(node_id)


def _growth_hold_id_from_nodeid(nodeid: str) -> str | None:
    parts = nodeid.split("::")
    if len(parts) < 2:
        return None
    function = parts[1].split("[", 1)[0]
    return f"{os.path.basename(parts[0])}::{function}"


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
        target = Path(config.args[0]).resolve(strict=False)
        suite_root = Path(__file__).resolve().parent
    except (OSError, TypeError, ValueError):
        return False
    if target != suite_root:
        return False
    argv = tuple(getattr(config.invocation_params, "args", ()))
    return not any(
        token.split("=", 1)[0] in _COLLECTION_NARROWING_OPTIONS
        for token in argv
    )


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Attach serial/hold metadata before selection hooks can narrow items."""
    opted_in = _growth_holds_opted_in()
    seen_hold_ids: set[str] = set()
    source_paths: dict[str, set[str]] = {}
    for item in items:
        node_id = _real_repo_node_id(item)
        if node_id in REAL_REPO_SERIAL_NODES:
            setattr(item, _REAL_REPO_SERIAL_NODE_ATTR, node_id)
            # xdist は複数 group 名を結合するため、二個目は足さない。
            if not list(item.iter_markers(name="xdist_group")):
                item.add_marker(pytest.mark.xdist_group("real-repo"))

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
    yield


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    """setup から teardown まで、正本由来の実資源アクセス印を伝播する。"""
    from orchestrator.campaign import patchharness

    node_id = _real_repo_node_id(item)
    stamped = getattr(item, _REAL_REPO_SERIAL_NODE_ATTR, None) == node_id
    with patchharness._pytest_node_context(node_id, stamped):
        return (yield)


def _prioritize_real_repo_items(items) -> None:
    """collection 確定後の real-repo slots へ優先順を適用する。"""
    priority = {
        node: index for index, node in enumerate(REAL_REPO_EXECUTION_PRIORITY)
    }
    serial_positions = [
        index for index, item in enumerate(items)
        if _real_repo_node_id(item) in REAL_REPO_SERIAL_NODES
    ]
    serial_items = [items[index] for index in serial_positions]
    serial_items.sort(
        key=lambda item: priority.get(
            _real_repo_node_id(item), len(REAL_REPO_EXECUTION_PRIORITY),
        ),
    )
    for index, item in zip(serial_positions, serial_items):
        items[index] = item


@pytest.hookimpl(tryfirst=True)
def pytest_collection_finish(session) -> None:
    """cacheprovider の後で順序を固定し、任意の task-run stats を収集する。"""
    # collection_finish は --ff / --nf の post-yield より後に来るため、最終順を固定できる。
    _prioritize_real_repo_items(session.items)
    # xdist worker もこの hook を通る。内側 helper guard と意図的に冗長な
    # defense-in-depth で、実解決を controller hook だけに限定する。
    if not hasattr(session.config, "workerinput"):
        _prewarm_receipt_memo(
            session.config,
            (_real_repo_node_id(item) for item in session.items),
            run_id=None,
        )
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


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_node_collection_finished(node, ids) -> None:
    """Collect controller-visible node IDs without persisting their names."""
    ids = tuple(ids)
    for nodeid in ids:
        hold_id = _growth_hold_id_from_nodeid(nodeid)
        if hold_id in GROWTH_TEST_HOLDS:
            _note_growth_hold(node.config, hold_id)
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


def pytest_configure(config) -> None:
    try:
        _configure_receipt_memo_session(config)
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
            if inner_exception is None:
                _finish_receipt_memo_session(config)
            else:
                try:
                    _finish_receipt_memo_session(config)
                except BaseException:
                    pass
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
