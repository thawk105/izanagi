単位 B の実装は完了しました。変更は隔離 worktree `dev-wave-t750-impl-b` の所有4ファイルだけで、commit は作成していません。ただし pytest は Pegasus の実行基盤で開始前停止したため、受入状態は「実装済み・未実走」です。

### 実装内容

- [s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-impl-b/orchestrator/campaign/s8b_oracle_manifest.py:1031)
  - `verify_manifest` に freeze の holdout別 configuration 集合との exact cell-product 検査を追加。
  - 一様な1 configuration subset は拒否。
  - `build_manifest` は snapshot core の wrapper にしたが、既存の受理集合は維持。
  - `build_manifest_from_ratified` は active snapshotを再読込せず使用。
  - `build-approved --output` CLI と、dirfd・`O_NOFOLLOW`・`O_EXCL`・candidate root限定 writerを追加。
  - `no-active` だけを `no-active-ratified-freeze` に写像し、`namespace-dirty` は保持。

- [s8b_oracle_spec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-impl-b/orchestrator/campaign/s8b_oracle_spec.py:22)
  - top-level 8 keys、schedule_parameters 5 keys、run_contract exact keysを検証。
  - schedule再生成、独立hash照合、campaign／binding／generator／excluded reasonを検証。
  - strict canonical bytes・末尾LFなしを要求。
  - `APPROVED_SPEC_SHA256: Optional[str] = None`。`None` は常に `no-approved-spec`。
  - approval writer、Git trailer認可、既定補完は未実装。

- [test_s8b_oracle_manifest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-impl-b/orchestrator/tests/test_s8b_oracle_manifest.py:289)
  - generic builderがsubsetを引き続き受理し、`verify_manifest`だけが拒否するMU-1テスト。
  - reviewed spec、pin、canonical bytes、独立schedule hash literal、全禁止argv、safe writer、CLI正負例を追加。
  - 既存期待値の変更・削除・skip・緩和はゼロ。

- [test_s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-impl-b/orchestrator/tests/test_s8b_ratified_freeze.py:1319)
  - real loaderによるno-active写像と、namespace-dirty非丸めを追加。

### 検査結果と赤の内訳

- `py_compile`：成功。
- `git diff --check`：成功。
- `python3 tools/check_codex_agents.py`：成功。
- `python3 tools/check_docs.py`：成功。
- 手動CLI smoke：
  - 正規argv：`rc=2`, `refused: no-active-ratified-freeze`
  - `--schedule forbidden`：argparse `rc=2`
  - いずれもspec／manifest出力なし。
- pytest：実行 nodeid 0件。以下はすべて `qstat -Q preflight rc=1 / rc=16` で開始前停止し、キュー投入なし。
  - `test_s8b_oracle_manifest.py`
  - owned 2 test filesのcollection-only
  - meta-test `test_plain_runner_coverage.py`
- 親docs未landに伴う事前期待赤：0件。
- pytest assertionの赤：0件観測。ただし未実走なので緑・closedとは申告しません。

### 所有外への静的波及

- caller：
  - `s8b_oracle_driver.py` の standalone gate と `run-block`
  - `s8b_oracle_report.py` のofficial CLI
  - `s8b_oracle_judge.py` は直接verifyしないが、縮小scheduleがreportへ到達しなくなる下流consumer
- 共有fixture：`s8b_v2_freeze_fixture.py` はimportのみ。変更なし。
- `s8b_oracle_driver.py`／report／judge／floor campaign／docs／freeze producerは変更なし。
- 現行driver・report・manifest fixtureの6 configurationはfreezeとexact一致するため、既存nodeの期待赤は0です。

B-1の保守的な既存回帰面は次のとおりです。

<details>
<summary>manifest既存13 node</summary>

`test_campaign_config_preimage_hash_is_bound_and_tampering_is_rejected`,
`test_generator_hash_must_match_real_root_file_at_build_and_verify`,
`test_generator_path_must_match_key_canonical_binding_at_build_and_verify`,
`test_generator_versions_exact_five_canonical_paths_and_hashes_verify`,
`test_generator_versions_extra_key_is_rejected_at_build_and_verify`,
`test_generator_versions_missing_required_key_is_rejected_at_build_and_verify`,
`test_v1_two_block_manifest_is_rejected_at_build_and_verify`,
`test_verified_manifest_sealed_constructor_rejects_non_lowercase_hash`,
`test_verify_detects_freeze_byte_tampering`,
`test_verify_detects_manifest_tampering`,
`test_verify_manifest_requires_freeze_document`,
`test_verify_rehashes_each_canonical_generator_in_supplied_root`,
`test_write_is_create_only_and_valid_manifest_verifies`

</details>

<details>
<summary>driver caller到達52 node</summary>

`test_active_resolution_and_manifest_structure_refusals_are_aggregated`,
`test_atomic_one_shot_lock_rejects_second_start`,
`test_binding_mismatch_refuses_only_that_row_before_evaluate`,
`test_build_result_contract_mismatch_aborts_campaign_before_measurement`,
`test_driver_full_frame_fsync_eio_is_not_folded_or_followed_up`,
`test_never_issued_generator_tamper_reaches_public_driver_gate_g7`,
`test_nonnull_floor_without_active_generation_is_refused`,
`test_official_driver_records_returncodes_through_real_producer_flow`,
`test_oracle_pipeline_contract_keyword_is_mandatory_positive_control`,
`test_probe_error_reason_is_fail_closed_unknown_abort`,
`test_real_freeze_gate_lists_floor_and_budget_null`,
`test_required_binding_missing_refuses_at_production_entry_without_side_effects`,
`test_required_existing_claim_refuses_production_entry_without_new_side_effects`,
`test_required_missing_preprovisioned_oracle_claim_root_is_fail_closed`,
`test_required_oracle_claim_root_outside_durable_approval_is_fail_closed`,
`test_required_recheck_real_receipt_validation_catches_midcampaign_drift`,
`test_required_recheck_real_reservation_shortfall_writes_aborted_terminal`,
`test_required_secondary_calibration_identity_recheck_fires_with_monkeypatched_loader`,
`test_required_v1_receipt_refuses_at_production_entry_without_side_effects`,
`test_required_verified_calibration_from_other_contract_is_refused_without_side_effects`,
`test_reservation_envelope_exceeded_is_fail_closed`,
`test_resume_wal_lstat_eio_propagates_fail_closed_from_public_driver`,
`test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing`,
`test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4`,
`test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result`,
`test_run_block_reuses_launch_validated_and_legacy_loader_is_dead`,
`test_run_block_verifies_manifest_once_and_reuses_object`,
`test_success_wal_order_budget_and_evaluate_contract`,
`test_t080_gate_hermetic_primary_states_exact`,
`test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`,
`test_tampered_freeze_fails_source_verification`,
`test_transient_prepare_failure_retries_once`,
`test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome`,
`test_v2_completed_driver_adapter_campaign_is_accepted_by_report`,
`test_v2_contract_sha256_mismatch_is_refused`,
`test_v2_floor_disk_swap_after_launch_uses_same_validated_object`,
`test_v2_freeze_bytes_not_active_generation_is_refused`,
`test_v2_gate_happy_path_completes_and_binds_env_store_receipt`,
`test_v2_launch_validate_failure_is_refused`,
`test_v2_launch_validate_non_ratified_error_is_refused`,
`test_v2_resume_rejected_at_s1_s2_s3_boundaries`,
`test_v2_standalone_gate_check_requires_full_floor_validation`,
`test_v2_store_hash_mismatch_is_refused`,
`test_v2_store_missing_is_refused`,
`test_v3_all_rows_binding_refused_is_protocol_violation`,
`test_v3_partial_binding_refused_is_protocol_violation`,
`test_v4_marker_fires_across_output_root_change`,
`test_v5_truncated_wal_rejects_resume_even_with_zero_parseable_records`,
`test_v6_freeze_swap_after_verify_is_not_observed`,
`test_v7_manifest_swap_after_verify_is_not_observed`,
`test_v8_bulk_reservation_unavailable_runs_nothing`,
`test_verify_inconclusive_and_unknown_abort_reasons_are_fail_closed`

</details>

<details>
<summary>report直接verify/helper到達90 node＋official CLI 2 node</summary>

`test_abort_workload_tag_must_match_verify_frontier`,
`test_aborted_terminal_status_alone_hides_fully_covered_completed_rows`,
`test_aborted_terminal_with_later_record_keeps_position_and_status_reasons`,
`test_allowed_excluded_reason_row_stays_reported_and_judges_unknown`,
`test_attempt_gap_has_one_lifecycle_reason`,
`test_attempt_one_two_three_chain_has_one_lifecycle_reason`,
`test_attempt_physical_order_must_match_numeric_order`,
`test_bench_failed_accepts_closed_abort_reason`,
`test_bench_failed_duplicate_abort_remains_protocol_violation`,
`test_bench_failed_rejects_invalid_abort_reason_without_crashing`,
`test_bench_returncodes_are_strict_and_do_not_publish_tps`,
`test_binary_mismatch_wal_stays_observable_and_judges_indeterminate`,
`test_blank_line_between_valid_records_is_unconditional_violation`,
`test_build_observations_accepts_actual_verify_manifest_result`,
`test_build_observations_rejects_verified_document_hash_drift`,
`test_campaign_start_after_completed_terminal_is_one_position_reason`,
`test_campaign_terminal_rejects_extra_top_level_key`,
`test_committed_bench_requires_exact_manifest_reps`,
`test_complete_invalid_raw_final_line_is_rejected`,
`test_complete_json_without_newline_after_terminal_is_one_protocol_reason`,
`test_correctness_red_abort_reason_must_equal_sole_red_verdict`,
`test_correctness_red_with_excluded_reason_is_protocol_violation`,
`test_definitive_red_survives_later_committed_retry_as_protocol_violation`,
`test_duplicate_retry_has_one_lifecycle_reason`,
`test_duplicate_trial_result_is_not_bijective`,
`test_excluded_reason_outside_allowed_list_is_protocol_violation`,
`test_expected_cells_keep_deleted_holdout_indeterminate`,
`test_failure_outcomes_remain_as_completed_observation_rows`,
`test_foreign_known_stage_is_inert_record_protocol_violation`,
`test_global_issue_composes_row_local_assessment_reason`,
`test_global_issue_does_not_mask_definitive_correctness_red`,
`test_global_orphan_retry_does_not_mask_other_definitive_red`,
`test_historical_receipt_derivation_failure_invalidates_all_campaign_rows_g2`,
`test_huge_integer_tps_is_row_level_protocol_violation`,
`test_impossible_declared_outcome_histories_are_protocol_violations`,
`test_invalid_line_after_terminal_cannot_hide_its_physical_position`,
`test_invalid_line_does_not_mask_definitive_correctness_red`,
`test_invalid_nested_abort_workload_is_an_independent_issue`,
`test_malformed_t080_envelope_is_fail_closed`,
`test_non_mapping_payload_and_missing_terminal_are_both_reported`,
`test_non_mapping_pipeline_payload_is_shared_wal_protocol_violation`,
`test_only_manifest_campaign_is_read_and_missing_owned_campaign_is_reported`,
`test_orphan_retry_for_schedule_outside_is_global_lifecycle_violation`,
`test_pipeline_physical_order_remains_an_independent_guard`,
`test_post_r_missing_key_is_single_reason_and_makes_judge_indeterminate`,
`test_post_r_null_is_protocol_violation_for_every_campaign_row`,
`test_pre_r_campaign_start_absent_or_null_is_allowed`,
`test_receipt_mismatch_is_protocol_violation`,
`test_report_reads_outcome_stage_contract_leaf`,
`test_report_rejects_campaign_symlink_to_exploration_namespace`,
`test_report_rejects_exploration_namespace_and_symlink_alias`,
`test_report_reuses_resolved_output_root_after_namespace_check`,
`test_report_session_issuer_alias_and_identity_use_model_authority`,
`test_resultful_window_retry_is_unbound_for_one_reason`,
`test_retry_absent_double_attempt_has_one_lifecycle_reason`,
`test_retry_after_terminal_result_is_row_scoped_tail_for_one_reason`,
`test_retry_attempt_one_rejects_pipeline_record_for_one_reason`,
`test_retry_before_first_start_is_unbound_for_one_reason`,
`test_retry_payload_next_attempt_must_be_exactly_two`,
`test_retry_payload_schedule_index_must_match_row`,
`test_retry_successor_identity_must_match_predecessor`,
`test_retry_successor_must_be_physically_adjacent`,
`test_reversed_verify_sequences_are_protocol_violations`,
`test_row_scoped_session_event_after_trial_result_is_rejected`,
`test_screen_marker_is_protocol_violation`,
`test_session_identity_checks_non_boundary_trial_record`,
`test_session_identity_issuer_is_only_protocol_trigger_without_terminal`,
`test_session_identity_rejection_preserves_malformed_t080_issue`,
`test_session_identity_rejection_taints_t080_report_observation`,
`test_session_identity_wrong_issuer_rejects_completed_campaign_only_for_issuer`,
`test_session_identity_wrong_v2_env_rejects_only_manifest_mismatch`,
`test_session_non_object_payload_before_terminal_is_unconditional_violation`,
`test_single_attempt_99_is_not_aliased_to_schedule_default`,
`test_success_uses_real_manifest_and_binds_physical_trial_intervals`,
`test_terminal_all_or_nothing_rejects_every_row_and_hides_all_numbers`,
`test_terminal_missing_makes_every_row_campaign_incomplete`,
`test_terminal_outcomes_accept_closed_abort_reason`,
`test_terminal_outcomes_reject_invalid_abort_reason_without_crashing`,
`test_terminal_scheduled_rows_mismatch_alone_hides_all_rows`,
`test_terminated_json_syntax_issue_does_not_mask_definitive_correctness_red`,
`test_timeout_and_verify_inconclusive_accept_both_verify_frontiers`,
`test_trial_result_after_campaign_terminal_remains_rejected_regression_pin`,
`test_trial_result_attempt_must_match_owning_start`,
`test_trial_result_before_first_start_is_not_silently_ignored`,
`test_trial_result_must_follow_all_pipeline_evidence`,
`test_trial_window_with_phantom_schedule_index_is_protocol_violation`,
`test_truncated_raw_tail_after_completed_terminal_is_one_protocol_reason`,
`test_truncated_tail_does_not_mask_definitive_correctness_red`,
`test_valid_prepare_retry_uses_attempt_two_and_records_retried_summary`,
`test_verify_inconclusive_wal_stays_observable_and_judges_indeterminate`,
`test_cli_official_resolves_ratified_freeze_and_verifies`,
`test_cli_verify_failure_returns_two_without_output`

</details>

## 総括

- choke pointのcell-product封鎖、reviewed spec pin、approved manifest CLIを所有範囲内で実装した。
- generic builder／旧writerの受理集合、凍結pin、transition table、既存期待値は変更していない。
- 実repoのspec・manifest・freeze成果物は作成せず、queue投入・実走・commitも行っていない。
- 残存リスクはpytest 0 node実走であり、親側で関連node＋meta-testを再実走するまでclosedではない。