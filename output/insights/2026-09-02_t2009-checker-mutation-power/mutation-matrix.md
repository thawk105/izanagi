# 変異 matrix — [T-2009] 検査器の弱体化に対する既存テストの検出力

- 固定 commit: `28ebff456b9f57a927854950b5030fa77aec6529`
- spec sha256: `1112651ebf939d79c0d17cfff621dc7e667fed8832115af3f559cb8a5f708661`
- probe spec sha256: `e73abef87f0e3751401260cb9f019f823990dbe42d6d8bd3d5366d34c745012f`
- 走行日: 2026-09-01T19:35:44.262726+00:00
- baseline: `PASSED` (失敗 node 0 件)
- 集計: {"KILLED": 6, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 1, "TIMEOUT": 0, "completed": 7, "matching": 7, "recorded": 7, "registered": 7}

## 分母 (estimand)

```
orchestrator/tests/test_verifier.py
orchestrator/tests/test_t1286_commit_receipt.py
orchestrator/tests/test_campaign.py
orchestrator/tests/test_s1_direct_comparison.py
orchestrator/tests/test_silo_ladder_rung1_driver.py
```

709 passed / 3 skipped / 27.73 秒 (login node、変異なしの実測)。

本走ではこのうち**冗長 gate 53 node** を `--deselect` した。その集合は下記「冗長 gate」の実測で決めた。

## 結果

| id | 変異 | 機械結果 | 期待一致 | 挙動 node | 注入実在 |
|---|---|---|---|---|---|
| `M1-CLASSIFIER-ALWAYS-G2` | 分類器が常に G2 を返す | KILLED | 一致 | 1 | 0:1 |
| `M2-VERSION-ORDER-IGNORES-EPOCH` | 版比較が epoch を無視し tid だけを見る | KILLED | 一致 | 2 | 0:1, 1:1, 2:1, 3:1 |
| `M3-IGNORE-CYCLES-OF-LENGTH-4-OR-MORE` | 長さ 4 以上の最短巡回を持つ SCC を無視する | KILLED | 一致 | 1 | 0:1 |
| `M4-FRAMING-DROPPED-FROM-CLEAN-GATE` | framing violation 項を受理判定 Integrity.clean() から外す | KILLED | 一致 | 5 | 0:1 |
| `M5-ANSWER-BY-INPUT-PROVENANCE` | fixture directory 外の入力を検証せず serializable と答える | KILLED | 一致 | 40 | 0:1 |
| `P1-DROP-RW-ANTI-DEPENDENCY` | rw (anti-dependency) 辺を張らない | KILLED | 一致 | 19 | 0:1 |
| `E1-EQUIVALENT-NOT-EQUAL` | u != v を not (u == v) に書き換える (等価) | SURVIVED | 一致 | 0 | 0:1 |

`注入実在` は replacement ごとの一致箇所数で、すべて 1 = 一意置換である。

## 失敗 node の完全集合 (本走)

### M1-CLASSIFIER-ALWAYS-G2 — KILLED

- `orchestrator/tests/test_verifier.py::test_classify_branches`

### M2-VERSION-ORDER-IGNORES-EPOCH — KILLED

- `orchestrator/tests/test_verifier.py::test_epoch_rw_successor_order_g2`
- `orchestrator/tests/test_verifier.py::test_epoch_version_order_g2`

### M3-IGNORE-CYCLES-OF-LENGTH-4-OR-MORE — KILLED

- `orchestrator/tests/test_verifier.py::test_nonlatest_read_caught_via_ww_transitivity`

### M4-FRAMING-DROPPED-FROM-CLEAN-GATE — KILLED

- `orchestrator/tests/test_verifier.py::test_characterization_txn_tail_loss_is_indeterminate`
- `orchestrator/tests/test_verifier.py::test_declared_read_and_write_counts_must_match`
- `orchestrator/tests/test_verifier.py::test_duplicate_end_is_indeterminate`
- `orchestrator/tests/test_verifier.py::test_missing_end_is_indeterminate`
- `orchestrator/tests/test_verifier.py::test_new_commit_before_end_records_missing_end`

### M5-ANSWER-BY-INPUT-PROVENANCE — KILLED

- `orchestrator/tests/test_campaign.py::test_pipeline_tail_loss_witness_reaches_verifier`
- `orchestrator/tests/test_campaign.py::test_pipeline_write_intent_violation_aborts_without_commit`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_attempt_two_bundle_isolated_and_each_subtree_sealed`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_collect_fixture_bundle_publishes_without_self_rejection`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_raw_bundle_major_predicates_are_recomputed_from_files`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_raw_bundle_rejects_duplicate_ycsb_target_compile_entry`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_silo_raw_clock_wiring_moves_with_policy_and_uses_exact_keys`
- `orchestrator/tests/test_verifier.py::test_abort_reason_tally_parsed_not_verdict`
- `orchestrator/tests/test_verifier.py::test_characterization_tail_txid_gap_is_indeterminate_with_commit_witness`
- `orchestrator/tests/test_verifier.py::test_characterization_txn_tail_loss_is_indeterminate`
- `orchestrator/tests/test_verifier.py::test_commit_below_genesis_indeterminate`
- `orchestrator/tests/test_verifier.py::test_commit_count_witness_detects_removed_trace_file`
- `orchestrator/tests/test_verifier.py::test_commit_count_witness_result_is_structured`
- `orchestrator/tests/test_verifier.py::test_cycle_verdict_takes_priority_over_framing_violation`
- `orchestrator/tests/test_verifier.py::test_declared_read_and_write_counts_must_match`
- `orchestrator/tests/test_verifier.py::test_dup_txid_indeterminate`
- `orchestrator/tests/test_verifier.py::test_duplicate_end_is_indeterminate`
- `orchestrator/tests/test_verifier.py::test_empty_trace_indeterminate_not_certified`
- `orchestrator/tests/test_verifier.py::test_known_tag_prefixes_are_not_accepted_as_record_tags`
- `orchestrator/tests/test_verifier.py::test_lock_coverage_malformed_key_flagged`
- `orchestrator/tests/test_verifier.py::test_lock_coverage_reasons_parsed`
- `orchestrator/tests/test_verifier.py::test_lock_coverage_violation_indeterminate`
- `orchestrator/tests/test_verifier.py::test_malformed_key_indeterminate`
- `orchestrator/tests/test_verifier.py::test_matching_commit_witness_does_not_mask_existing_integrity_failure`
- `orchestrator/tests/test_verifier.py::test_missing_end_is_indeterminate`
- `orchestrator/tests/test_verifier.py::test_missing_txid_gap_indeterminate`
- `orchestrator/tests/test_verifier.py::test_negative_txid_is_rejected_before_gap_math_can_cancel_it`
- `orchestrator/tests/test_verifier.py::test_new_commit_before_end_records_missing_end`
- `orchestrator/tests/test_verifier.py::test_nonascii_wrapped_as_parse_error`
- `orchestrator/tests/test_verifier.py::test_permutation_violation_between_txn_blocks`
- `orchestrator/tests/test_verifier.py::test_permutation_violation_details_bound_large_known_sample`
- `orchestrator/tests/test_verifier.py::test_permutation_violation_details_follow_parse_verify_report_path`
- `orchestrator/tests/test_verifier.py::test_permutation_violation_indeterminate`
- `orchestrator/tests/test_verifier.py::test_permutation_violation_reasons_parsed`
- `orchestrator/tests/test_verifier.py::test_unknown_tag_still_parse_error_after_a`
- `orchestrator/tests/test_verifier.py::test_write_intent_malformed_key_flagged`
- `orchestrator/tests/test_verifier.py::test_write_intent_reasons_parsed_and_summarized`
- `orchestrator/tests/test_verifier.py::test_write_intent_unknown_reason_counted_and_indeterminate`
- `orchestrator/tests/test_verifier.py::test_write_intent_violation_indeterminate_and_reports_json_text`
- `orchestrator/tests/test_verifier.py::test_write_version_mismatch_indeterminate`

### P1-DROP-RW-ANTI-DEPENDENCY — KILLED

- `orchestrator/tests/test_campaign.py::test_pipeline_extra_correctness_second_pass_red_aborts_with_workload_tag`
- `orchestrator/tests/test_t1286_commit_receipt.py::test_uncertified_verifier_capability_cannot_issue_receipt[r1_write_skew]`
- `orchestrator/tests/test_t1286_commit_receipt.py::test_uncertified_verifier_capability_cannot_issue_receipt[r2_lost_update]`
- `orchestrator/tests/test_verifier.py::test_broken_silo_norw_fixture_contract`
- `orchestrator/tests/test_verifier.py::test_broken_silo_norw_structured_report_is_exact`
- `orchestrator/tests/test_verifier.py::test_cycle3_g2`
- `orchestrator/tests/test_verifier.py::test_cycle_verdict_takes_priority_over_framing_violation`
- `orchestrator/tests/test_verifier.py::test_epoch_rw_successor_order_g2`
- `orchestrator/tests/test_verifier.py::test_epoch_version_order_g2`
- `orchestrator/tests/test_verifier.py::test_g4_has_rw_edge_but_no_cycle`
- `orchestrator/tests/test_verifier.py::test_lost_update_g2`
- `orchestrator/tests/test_verifier.py::test_mixed_cycle_g2_all_three_edge_types`
- `orchestrator/tests/test_verifier.py::test_nonlatest_read_caught_via_ww_transitivity`
- `orchestrator/tests/test_verifier.py::test_real_silo_edge_type_combinations_are_exact`
- `orchestrator/tests/test_verifier.py::test_real_silo_serializable`
- `orchestrator/tests/test_verifier.py::test_silo_serial_1thread_fixture_contract`
- `orchestrator/tests/test_verifier.py::test_structured_report_has_edge_detail`
- `orchestrator/tests/test_verifier.py::test_total_cycles_survives_witness_cap`
- `orchestrator/tests/test_verifier.py::test_write_skew_g2`

### E1-EQUIVALENT-NOT-EQUAL — SURVIVED

失敗 node なし (生存)。

## 冗長 gate (同一性層) の実測

probe 走 (分母を絞らず全 node を収集) では、**等価変異 E1 が 53 node を赤にした**。
赤の理由はすべて同一で、
`orchestrator.campaign.ident.IdentityMismatch: contract-loader-drift: disk bytes が記録 commit blob と不一致: orchestrator/verifier/dsg.py` である。

| id | probe の赤 node 総数 | うち同一性層 | 挙動 node |
|---|---|---|---|
| `M1-CLASSIFIER-ALWAYS-G2` | 54 | 53 | 1 |
| `M2-VERSION-ORDER-IGNORES-EPOCH` | 55 | 53 | 2 |
| `M3-IGNORE-CYCLES-OF-LENGTH-4-OR-MORE` | 54 | 53 | 1 |
| `M4-FRAMING-DROPPED-FROM-CLEAN-GATE` | 58 | 53 | 5 |
| `M5-ANSWER-BY-INPUT-PROVENANCE` | 93 | 53 | 40 |
| `P1-DROP-RW-ANTI-DEPENDENCY` | 72 | 53 | 19 |
| `E1-EQUIVALENT-NOT-EQUAL` | 53 | 53 | 0 |

同一性層は、検査器を骨抜きにする `P1` と、意味を一切変えない `E1` を
**同じ 53 node で**赤にする。P1 の赤 72 件のうち 53 件がこの層である。

### 同一性層の node 完全集合

- `orchestrator/tests/test_campaign.py::test_ensure_campaign_identity_uses_atomic_lock_and_loser_only_verifies`
- `orchestrator/tests/test_campaign.py::test_exploration_available_perf_preserves_measurement_behavior`
- `orchestrator/tests/test_campaign.py::test_exploration_claim_uses_environment_output_root_and_single_identity`
- `orchestrator/tests/test_campaign.py::test_exploration_no_perf_completes_bench_and_records_not_required`
- `orchestrator/tests/test_campaign.py::test_identity_mismatch_guard`
- `orchestrator/tests/test_campaign.py::test_linux_baremetal_skips_reservation_and_claim_for_non_single_process`
- `orchestrator/tests/test_campaign.py::test_loop_dedup_identical_genome_in_one_run`
- `orchestrator/tests/test_campaign.py::test_loop_dedup_uses_src_token_id`
- `orchestrator/tests/test_campaign.py::test_loop_does_not_append_abort_after_wal_io_error`
- `orchestrator/tests/test_campaign.py::test_loop_enables_s2_extra_correctness_via_search_config`
- `orchestrator/tests/test_campaign.py::test_loop_identity_error_is_retryable_after_repair`
- `orchestrator/tests/test_campaign.py::test_loop_identity_error_retryable_survives_inflight_crash`
- `orchestrator/tests/test_campaign.py::test_loop_identity_skip_is_visible_when_stock_id_terminal`
- `orchestrator/tests/test_campaign.py::test_loop_isolates_failing_genome`
- `orchestrator/tests/test_campaign.py::test_loop_isolates_identity_error`
- `orchestrator/tests/test_campaign.py::test_loop_omits_extra_correctness_without_verify_search_config`
- `orchestrator/tests/test_campaign.py::test_loop_probe_error_is_retryable_after_recovery`
- `orchestrator/tests/test_campaign.py::test_loop_recovery_skips_committed_src_token_variant`
- `orchestrator/tests/test_campaign.py::test_loop_resume_recovery_aborts_real_pipeline_crash_after_start`
- `orchestrator/tests/test_campaign.py::test_loop_resume_repairs_tail_before_replay_and_surfaces_receipt`
- `orchestrator/tests/test_campaign.py::test_m12_loop_compute_uses_gxx_and_forwards_only_contract_and_prefix`
- `orchestrator/tests/test_campaign.py::test_official_rejects_perf_preflight_seam_while_exploration_accepts_it`
- `orchestrator/tests/test_campaign.py::test_p1_run_campaign_accepts_registered_contract`
- `orchestrator/tests/test_campaign.py::test_replay_accepts_matching_contract_bound_commit_and_skips_evaluation`
- `orchestrator/tests/test_campaign.py::test_required_contract_is_attested_once_at_run_campaign_sink`
- `orchestrator/tests/test_campaign.py::test_resumable_wal_rejects_truncated_tail_with_active_attempt_before_repair`
- `orchestrator/tests/test_campaign.py::test_run_campaign_declared_use_class_does_not_change_campaign_id`
- `orchestrator/tests/test_campaign.py::test_run_campaign_exploration_namespace_reaches_lock_wal_and_pipeline`
- `orchestrator/tests/test_campaign.py::test_run_campaign_forwards_only_non_none_holdout_observation_admission`
- `orchestrator/tests/test_campaign.py::test_run_campaign_wires_nondefault_bench_max_rounds_to_evaluate`
- `orchestrator/tests/test_campaign.py::test_screening_driver_probe_error_is_retryable_after_recovery`
- `orchestrator/tests/test_campaign.py::test_trigger_campaign_epoch_never_writes_pre_t428_paths`
- `orchestrator/tests/test_s1_direct_comparison.py::test_budget_preflight_uses_conservative_upper_bound`
- `orchestrator/tests/test_s1_direct_comparison.py::test_budget_shortage_does_not_start_session`
- `orchestrator/tests/test_s1_direct_comparison.py::test_completed_campaign_resume_does_not_evaluate_again`
- `orchestrator/tests/test_s1_direct_comparison.py::test_develop_calls_legacy_plus_s2_without_bench_18_times`
- `orchestrator/tests/test_s1_direct_comparison.py::test_driver_uses_workload_flags_from_freeze`
- `orchestrator/tests/test_s1_direct_comparison.py::test_injected_evaluate_fn_certified_result_without_condition_records_is_refused`
- `orchestrator/tests/test_s1_direct_comparison.py::test_injected_prepare_cell_without_condition_records_is_refused`
- `orchestrator/tests/test_s1_direct_comparison.py::test_prepare_freeze_contract_error_aborts_without_retry`
- `orchestrator/tests/test_s1_direct_comparison.py::test_prepare_transient_failure_retries_twice_then_succeeds`
- `orchestrator/tests/test_s1_direct_comparison.py::test_resume_repairs_tail_before_retry_and_session_result`
- `orchestrator/tests/test_s1_direct_comparison.py::test_retry_limit_abandons_session_and_continues`
- `orchestrator/tests/test_s1_direct_comparison.py::test_run_role_available_perf_keeps_evaluate_call_shape_exact`
- `orchestrator/tests/test_s1_direct_comparison.py::test_run_role_partial_wal_write_eio_preserves_error_and_stops_followup`
- `orchestrator/tests/test_s1_direct_comparison.py::test_run_role_unavailable_perf_passes_degraded_kwargs_from_one_probe`
- `orchestrator/tests/test_s1_direct_comparison.py::test_s1_oracle_reject_is_distinct_terminal_and_resume_does_not_prepare`
- `orchestrator/tests/test_s1_direct_comparison.py::test_s1_oracle_unavailable_is_recorded_as_attempt_infra_before_retry`
- `orchestrator/tests/test_s1_direct_comparison.py::test_schedule_mutation_refused_and_deviation_recorded`
- `orchestrator/tests/test_s1_direct_comparison.py::test_trace_timeout_retries_but_verify_payload_does_not`
- `orchestrator/tests/test_s1_direct_comparison.py::test_unknown_status_is_redacted_from_exception_deviation_and_budget`
- `orchestrator/tests/test_s1_direct_comparison.py::test_verifier_red_in_one_campaign_blocks_other_campaign`
- `orchestrator/tests/test_s1_direct_comparison.py::test_verifier_red_stops_without_retry`
