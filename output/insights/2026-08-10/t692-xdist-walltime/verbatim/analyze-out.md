[analyze_junit.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/analyze_junit.py) を作成し、次を実行しました。

```bash
python3 analyze_junit.py junit-baseline.xml
```

既定パスでの実行結果とも `cmp` で一致し、冪等性を確認済みです。

<details>
<summary>実際の出力（全量）</summary>

```text
=== 全体 ===
testcase 数: 7705
time 直列総和: 16534.55 秒
testsuite wall: 1407.97 秒
testsuite metadata: tests=7705, failures=0, errors=0, skipped=20, hostname=bnode055

=== 並列効率 ===
直列総和 / wall: 11.74 worker 相当
48 worker に対する利用率: 24.5%

=== group ごとの直列和（降順） ===
real-repo: 1388.80 秒 / 43 testcase (8.4%)
real_repo: 69.45 秒 / 1 testcase (0.4%)
s8c-preregistration-candidate: 58.35 秒 / 3 testcase (0.4%)
dev-waves-runtime: 16.17 秒 / 22 testcase (0.1%)
(group 未指定): 15001.78 秒 / 7636 testcase (90.7%)

=== critical path 下界 ===
最大 group 直列和: 1388.80 秒 (real-repo)
直列総和 / 48: 344.47 秒
下界 max(最大 group, 直列総和 / 48): 1388.80 秒
最大 group (real-repo) を完全に消した場合の下界: 671.55 秒
  内訳: 残存最大 group=69.45 秒, 最大未指定 testcase=671.55 秒, 残余直列総和 / 48=315.54 秒

=== 単体で重い testcase 上位 30 件 ===
 1. 680.23 秒 | group=real-repo | orchestrator.tests.test_s8b_binding_driftguards::test_run_block_broken_binding_manifest_refuses_and_writes_nothing
 2. 671.55 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_oracle_pipeline_contract_keyword_is_mandatory_positive_control
 3. 671.49 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_build_result_contract_mismatch_aborts_campaign_before_measurement
 4. 671.37 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_success_wal_order_budget_and_evaluate_contract
 5. 671.34 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_verify_inconclusive_and_unknown_abort_reasons_are_fail_closed
 6. 671.33 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_probe_error_reason_is_fail_closed_unknown_abort[verify-probe-error]
 7. 671.31 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_v3_all_rows_binding_refused_is_protocol_violation
 8. 671.20 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_probe_error_reason_is_fail_closed_unknown_abort[bench-probe-error]
 9. 671.16 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_reservation_envelope_exceeded_is_fail_closed
10. 671.13 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_run_block_verifies_manifest_once_and_reuses_object
11. 670.39 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_v7_manifest_swap_after_verify_is_not_observed
12. 667.16 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_v2_resume_rejected_at_s1_s2_s3_boundaries
13. 667.15 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_driver_full_frame_fsync_eio_is_not_folded_or_followed_up
14. 667.15 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_resume_wal_lstat_eio_propagates_fail_closed_from_public_driver
15. 667.05 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_v5_truncated_wal_rejects_resume_even_with_zero_parseable_records[multibyte-partial]
16. 663.48 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_atomic_one_shot_lock_rejects_second_start
17. 653.50 秒 | group=real-repo | orchestrator.tests.test_s8b_oracle_driver::test_cli_subprocess_returns_rc_2_on_gate_refused
18. 631.14 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_official_driver_records_returncodes_through_real_producer_flow
19. 240.66 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5
20. 214.79 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]
21. 213.94 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]
22. 213.63 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]
23. 201.62 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28
24. 200.51 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]
25. 192.74 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[bad-trailer-receipt.user_commit_trailer]
26. 192.24 秒 | group=(未指定) | orchestrator.tests.test_s8b_oracle_driver::test_t080_full_valid_history_defects_have_one_baseline_reason_f28[extra-r-path-receipt.introduction_diff]
27. 159.82 秒 | group=(未指定) | orchestrator.tests.test_codex_reasoning_ab::test_verify_replays_complete_fake_codex_experiment
28. 99.69 秒 | group=(未指定) | orchestrator.tests.test_codex_reasoning_ab::test_supervisor_launches_pair_and_scrubs_git_environment
29. 97.78 秒 | group=(未指定) | orchestrator.tests.test_codex_reasoning_ab::test_m3_ignored_extra_and_missing
30. 94.97 秒 | group=(未指定) | orchestrator.tests.test_codex_reasoning_ab::test_m3_snapshot_mode_change

=== classname ごとの直列和 上位 20 件 ===
 1. 13069.89 秒 | orchestrator.tests.test_s8b_oracle_driver
 2. 1265.75 秒 | orchestrator.tests.test_codex_reasoning_ab
 3. 680.26 秒 | orchestrator.tests.test_s8b_binding_driftguards
 4. 414.90 秒 | orchestrator.tests.test_s8b_floor_campaign
 5. 144.61 秒 | orchestrator.tests.test_t126_pegasus_tools
 6. 95.30 秒 | orchestrator.tests.test_dev_waves_integration
 7. 90.48 秒 | orchestrator.tests.test_check_docs
 8. 82.70 秒 | orchestrator.tests.test_run_tests_preflight
 9. 75.99 秒 | orchestrator.tests.test_ruleops
10. 75.36 秒 | orchestrator.tests.test_s8b_ratified_verify
11. 61.59 秒 | orchestrator.tests.test_s8c_preregistration_invariant
12. 55.98 秒 | orchestrator.tests.test_check_ai_provenance
13. 40.06 秒 | orchestrator.tests.test_dev_wave_land
14. 35.06 秒 | orchestrator.tests.test_codex_worker_launch
15. 26.25 秒 | orchestrator.tests.test_login_headroom
16. 25.80 秒 | orchestrator.tests.test_codex_agents
17. 24.41 秒 | orchestrator.tests.test_silo_ladder_rung1_evidence
18. 23.57 秒 | orchestrator.tests.test_mutation_harness
19. 18.19 秒 | orchestrator.tests.test_s8b_repo_scan_invariant
20. 11.86 秒 | orchestrator.tests.test_reflux_origin_ledger

=== 最大 group の内訳（秒の降順、最大 60 件） ===
group=real-repo | 全 43 件中 43 件表示 | 合計 1388.80 秒
 1. 680.23 秒 | orchestrator.tests.test_s8b_binding_driftguards::test_run_block_broken_binding_manifest_refuses_and_writes_nothing
 2. 653.50 秒 | orchestrator.tests.test_s8b_oracle_driver::test_cli_subprocess_returns_rc_2_on_gate_refused
 3. 18.85 秒 | orchestrator.tests.test_s8b_oracle_driver::test_real_freeze_gate_lists_floor_and_budget_null
 4. 18.19 秒 | orchestrator.tests.test_s8b_repo_scan_invariant::test_real_repository_scan_matches_known_hits_and_has_positive_control
 5. 5.70 秒 | orchestrator.tests.test_real_repo_serialization::test_protocol_builder_repo_tree_guard_is_wired_to_real_root
 6. 2.26 秒 | orchestrator.tests.test_s8b_protocol_builder::test_build_and_write_leave_repo_tree_unchanged[nested]
 7. 2.08 秒 | orchestrator.tests.test_s8b_protocol_builder::test_build_and_write_leave_repo_tree_unchanged[top-level]
 8. 1.57 秒 | orchestrator.tests.test_s8b_oracle_driver::test_v2_standalone_gate_check_requires_full_floor_validation
 9. 1.40 秒 | orchestrator.tests.test_s8b_oracle_driver::test_nonnull_floor_without_active_generation_is_refused
10. 0.85 秒 | orchestrator.tests.test_s1_measurement_freeze::test_verify_rejects_one_byte_freeze_tamper
11. 0.61 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_build_document_is_self_consistent_and_detects_tamper
12. 0.43 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_verify_rejects_non_ancestor_head
13. 0.39 秒 | orchestrator.tests.test_s1_measurement_freeze::test_receipt_exists_but_measurement_verify_stays_legacy_strict
14. 0.35 秒 | orchestrator.tests.test_s1_measurement_freeze::test_generate_builds_registered_cells_comparisons_and_schedule
15. 0.26 秒 | orchestrator.tests.test_s1_measurement_freeze::test_schedule_is_balanced_and_reproducible
16. 0.25 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_verify_rejects_foreign_ccbench_pin
17. 0.23 秒 | orchestrator.tests.test_s1_measurement_freeze::test_s1b_pairing_rejects_mismatched_flags
18. 0.21 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_verify_rejects_one_byte_freeze_tamper
19. 0.19 秒 | orchestrator.tests.test_s1_measurement_freeze::test_verify_rejects_one_byte_workload_flag_tamper
20. 0.14 秒 | orchestrator.tests.test_s1_measurement_freeze::test_generate_refuses_existing_freeze
21. 0.14 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_verify_rejects_generator_sha_tamper
22. 0.14 秒 | orchestrator.tests.test_s1_measurement_freeze::test_verify_rejects_stats_implementation_tamper
23. 0.13 秒 | orchestrator.tests.test_s1_measurement_freeze::test_verify_rejects_known_axes_material_tamper
24. 0.12 秒 | orchestrator.tests.test_s1_measurement_freeze::test_build_document_rejects_tampered_known_axes_semantics
25. 0.10 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_generate_selects_registered_expected_points
26. 0.10 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_generate_refuses_existing_freeze
27. 0.09 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_s1b_pairing_rejects_mismatched_flags
28. 0.07 秒 | orchestrator.tests.test_s1_known_axes_freeze::test_verify_rejects_tampered_source_copy
29. 0.04 秒 | orchestrator.tests.test_s8b_oracle_driver::test_tampered_freeze_fails_source_verification
30. 0.03 秒 | orchestrator.tests.test_s8b_oracle_driver::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing
31. 0.02 秒 | orchestrator.tests.test_campaign::test_source_digest_parse_options_defaults
32. 0.02 秒 | orchestrator.tests.test_campaign::test_source_digest_stock_roundtrip
33. 0.02 秒 | orchestrator.tests.test_s8b_binding_driftguards::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal
34. 0.02 秒 | orchestrator.tests.test_s8b_oracle_driver::test_active_resolution_and_manifest_structure_refusals_are_aggregated
35. 0.01 秒 | orchestrator.tests.test_p3_s4_loop_sort::test_drive_iteration_checkpoint_survives_across_calls
36. 0.01 秒 | orchestrator.tests.test_campaign::test_evolve_block_markers_structure_and_inert
37. 0.01 秒 | orchestrator.tests.test_p3_s4_loop::test_drive_iteration_checkpoint_survives_across_calls
38. 0.01 秒 | orchestrator.tests.test_p3_s4_loop_trigger_gating::test_drive_iteration_writes_entry_and_checkpoint
39. 0.01 秒 | orchestrator.tests.test_campaign::test_source_digest_fixed_variant_distinct
40. 0.01 秒 | orchestrator.tests.test_p3_s4_loop_trigger_gating::test_drive_iteration_entry_failure_blocks_checkpoint
41. 0.00 秒 | orchestrator.tests.test_campaign::test_source_digest_failsclosed_on_missing_define
42. 0.00 秒 | orchestrator.tests.test_campaign::test_source_digest_semantic_comment_vs_behavior
43. 0.00 秒 | orchestrator.tests.test_hooks::test_real_submodule_payload_edit
```

</details>

## 総括

- 標準ライブラリのみの JUnit 解析スクリプトを作成し、指定 XML に対して実行しました。7705 testcase、直列総和 16534.55 秒、wall 1407.97 秒、実効並列度 11.74 worker、48 worker 利用率 24.5% でした。
- wall 1408 秒の律速は、worker 数でも単独 test 一件でもなく、`real-repo` group の直列鎖です。直列和 1388.80 秒で wall の 98.6% に達し、48 分割の理想下界 344.47 秒を大幅に上回ります。
- `real-repo` 内では 680.23 秒と653.50 秒の2件だけで1333.73秒、group 全体の96.0%を占めます。同じ group のため、この2件が直列実行されることが直接の律速です。
- 最大 group を完全に消すという仮定でも、未指定の分割不能 test が最大671.55秒残ります。したがって新 wall の下界は671.55秒、現状からの短縮上界は736.42秒（52.3%）です。残余総和÷48だけなら315.54秒ですが、単体 test の下界を無視するため実現不能です。
- XML から実際に検出された group は4種類でした。`real-repo` と `real_repo` が別 group として混在しており、命名揺れが疑わしい点です。
- 約663～672秒の未指定 testcase が多数集中し、ほぼ同じ所要時間を示しています。タイムアウトや共通の待機条件を疑うべき外れ値ですが、XML の値をそのまま報告しています。
- パラメータ名 `[@args.rsp]` 内にも `@` がありました。これは group ではないため、既知 group の列挙には頼らず「角括弧外の末尾 `@suffix`」のみを group として抽出しています。