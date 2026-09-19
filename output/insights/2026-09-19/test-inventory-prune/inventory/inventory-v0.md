# Static test inventory

判定は仮説。削除確定には意味確認と変異検査が必要。分類間は重複する。

Each category sums each matching function once (categories overlap); lines include decorators through end_lineno; nodeids count collect-file entries; seconds sum ledger lookup per entry with missing=0; file lines are whole-file splitlines counts.

対象 333 files / 510327 file lines; 除外 30 files / 67920 lines.

|範囲|関数|行|nodeids|台帳秒|台帳欠落 nodeids|
|---|---:|---:|---:|---:|---:|
|全対象|14416|345321|21882|15587.593000|949|
|protected|634|21114|918|4969.357000|230|
|A including_protected|384|13096|608|654.531000|57|
|A excluding_protected|381|12806|605|654.504000|57|
|B including_protected|63|959|312|185.028000|1|
|B excluding_protected|62|947|311|185.028000|0|
|C including_protected|1|16|1|0.002000|0|
|C excluding_protected|1|16|1|0.002000|0|
|D including_protected|297|10397|362|296.410000|12|
|D excluding_protected|291|10099|356|225.392000|12|

## A: 台帳秒上位30件（protected含む）

|関数|行|nodeids|台帳秒|protected|証拠種別|
|---|---:|---:|---:|---:|---|
|orchestrator/tests/test_p3_b4_producer_auth_experiment.py::test_wave_mutant_kills_exactly_one_registered_node:1136|48|8|513.000000|False|path-missing|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_s8c_living_doc_reference_negative_controls:723|23|1|43.000000|False|path-missing|
|orchestrator/tests/test_official_perf_closure.py::test_outer_perf_file_mutations_are_not_tautologies:920|16|1|25.000000|False|path-missing|
|orchestrator/tests/test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches:8014|187|1|8.400000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_rejects_tampered_acceptance_receipt:1318|66|22|6.510000|False|path-missing|
|orchestrator/tests/test_dev_waves_integration.py::test_dedicated_provenance_and_code_dirty_reasons_are_wired:760|35|2|3.000000|False|path-missing|
|orchestrator/tests/test_official_perf_closure.py::test_closure_inventory_mutations_are_not_tautologies:871|37|1|2.800000|False|path-missing|
|orchestrator/tests/test_check_branch_rescue.py::test_real_checker_unlanded_spool_details:1782|52|2|2.500000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_git_operation_surface_is_read_only_except_sha_ff_merge:8275|36|1|2.200000|False|flag-missing|
|orchestrator/tests/test_s8b_oracle_report.py::test_build_observations_historical_resolver_fails_closed_without_current_fallback:3531|100|7|1.990000|False|path-missing|
|orchestrator/tests/test_s8c_preregistration_core.py::test_filtered_history_preserves_rejections_after_unrelated_commits:2027|109|1|1.800000|False|docs-heading-missing|
|orchestrator/tests/test_dev_waves_integration.py::test_active_check_failure_occurs_only_after_passive_gates:731|27|1|1.700000|False|path-missing|
|orchestrator/tests/test_audit_dangling_commits.py::test_pattern_owners_complete_for_large_shared_ancestor_population:3286|23|1|1.600000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_runner_entry_shape_is_permanent_rejection:1873|46|3|1.140000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_m10_bootstrap_rejects_locked_main_with_launcher:1227|42|1|0.870000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_active_transaction_recovery_completes_with_provenance_red:7652|78|1|0.860000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_folds_rotation_inside_lock:6767|126|1|0.780000|False|docs-heading-missing, flag-missing, path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_real_waiter_receipt_is_consumed_by_real_land_end_to_end:2193|118|1|0.760000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_real_waiter_executes_main_when_tip_runner_differs_and_land_accepts:2313|156|1|0.740000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_folds_failure_supersede_inside_lock:6895|100|1|0.730000|False|docs-heading-missing, flag-missing, path-missing|
|orchestrator/tests/test_axis_b5_search_executor.py::test_registration_rejects_path_module_mode_and_byte_mismatches:451|35|1|0.670000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_nested_untracked_under_foreign_handoff_directory:2620|28|1|0.660000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_d987_two_stage_chain_accepts_final_net_runner_restore:8590|43|1|0.650000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_fold_gate_failure_and_main_pending_race_both_stop_before_ff:11373|39|1|0.640000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_target_collision_with_foreign_control_artifact_is_rejected:2849|24|1|0.610000|False|path-missing|
|orchestrator/tests/test_growth_test_holds_contract.py::test_noconftest_bypass_is_refused_before_held_body:2440|18|1|0.600000|False|path-missing|
|orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip:2534|20|1|0.600000|False|path-missing|
|orchestrator/tests/test_audit_dangling_commits.py::test_cli_include_regenerable_artifacts_is_independent_from_fold_flag:1812|52|4|0.491000|False|path-missing|
|orchestrator/tests/test_s8c_preregistration_predicates.py::test_c12_rejects_conservative_local_binding_forms:2635|63|7|0.473000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_main_untracked_archive_closure_race_stops_before_ff:11730|35|1|0.450000|False|path-missing|

## B: 台帳秒上位30件（protected含む）

|関数|行|nodeids|台帳秒|protected|証拠種別|
|---|---:|---:|---:|---:|---|
|orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility:2381|36|3|100.000000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t126_pegasus_tools.py::test_submit_rejects_each_single_layer_equal_float_type_drift:3570|28|5|27.900000|False|identical-body|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete:623|12|1|21.000000|False|identical-body|
|orchestrator/tests/test_t126_pegasus_tools.py::test_submit_rejects_overdetermined_reservation_policy_type_drift:3624|27|3|14.100000|False|identical-body|
|orchestrator/tests/test_t126_pegasus_tools.py::test_submit_rejects_each_mapping_masked_equal_float_type_drift:3600|22|2|12.500000|False|identical-body|
|orchestrator/tests/test_reflux_origin_binding.py::test_store_scope_type_and_closed_values_are_rejected:744|4|4|2.390000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t671_source_binding.py::test_pre_t1287_exact_fourteen_misses_but_exact_twenty_four_rejects_receipt_face:425|11|5|2.190000|False|identical-body|
|orchestrator/tests/test_paper_story_a1_paired.py::test_m_nc07_decoded_noncertifying_lock_scopes_collector_anomaly_gate:3878|25|5|1.500000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t671_source_binding.py::test_pre_t1287_exact_fourteen_misses_but_exact_twenty_four_rejects_s8c_face:412|11|3|1.460000|False|identical-body|
|orchestrator/tests/test_paper_story_a1_paired.py::test_materializer_requires_exact_zero_driver_and_shell_rc:3307|50|3|0.640000|False|duplicate-parametrize-row|
|orchestrator/tests/test_paper_story_a1_paired.py::test_v3_sized_statistics_reject_invalid_decimal_values:1254|18|26|0.290000|False|duplicate-parametrize-row|
|orchestrator/tests/test_s8b_prediction_runner.py::test_claude_headless_rejects_invalid_envelope:939|14|6|0.200000|False|identical-body|
|orchestrator/tests/test_t793_approval_d291.py::test_approved_value_comparison_units_reject_mismatch:184|20|4|0.177000|False|identical-body|
|orchestrator/tests/test_s8b_prediction_runner.py::test_claude_headless_rejects_invalid_provenance_measurements:955|15|4|0.167000|False|identical-body|
|orchestrator/tests/test_t793_approval_d291.py::test_document_relations_entire_section_is_exact:163|19|3|0.121000|False|identical-body|
|orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py::test_each_analysis_invalid_literal_mutation_is_rejected:128|7|12|0.085000|False|identical-body|
|orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py::test_each_registry_violation_literal_mutation_is_rejected:137|7|5|0.035000|False|identical-body|
|orchestrator/tests/test_schema_v2.py::test_acquisition_receipt_rejects_each_bad_field:273|34|27|0.027000|False|identical-body|
|orchestrator/tests/test_schema_v2.py::test_attestation_profile_rejects_each_bad_field:205|34|27|0.027000|False|identical-body|
|orchestrator/tests/test_codex_reasoning_ab.py::test_f176_preserves_legitimate_opposite_mentions:13611|61|10|0.016000|False|identical-body|
|orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_coder_proposal_rejects_invalid_wire_corpus:2001|13|15|0.016000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t1434_t1222_science_slice.py::test_pinned_jobs_guard_skips_when_root_exists_but_one_file_is_missing:452|14|1|0.014000|False|identical-body|
|orchestrator/tests/test_s8c_result_judge.py::test_invalid_params_are_preregistration_not_effective:548|28|10|0.010000|False|duplicate-parametrize-row|
|orchestrator/tests/test_codex_reasoning_ab.py::test_bound_price_rejects_numeric_stage_type_confusion:7338|13|2|0.008000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t1434_t1222_science_slice.py::test_pinned_jobs_guard_does_not_skip_for_complete_input_set:468|7|1|0.008000|False|identical-body|
|orchestrator/tests/test_t189_oracle_wiring_slice.py::test_pinned_jobs_guard_skips_when_root_exists_but_one_file_is_missing:154|14|1|0.008000|False|identical-body|
|orchestrator/tests/test_trigger_gate_binding.py::test_mask_rejects_non_exact_int_and_out_of_range:91|13|7|0.008000|False|duplicate-parametrize-row|
|orchestrator/tests/test_campaign_lock_codec.py::test_v2_rejects_non_positive_or_non_exact_activation_serial:402|8|7|0.007000|False|duplicate-parametrize-row|
|orchestrator/tests/test_coder_effect_gate.py::test_identifier_substrings_strings_and_comments_do_not_match:53|14|7|0.007000|False|identical-body|
|orchestrator/tests/test_env_contract.py::test_rejects_bad_attestation_mode:191|4|7|0.007000|False|duplicate-parametrize-row|

## C: 台帳秒上位30件（protected含む）

|関数|行|nodeids|台帳秒|protected|証拠種別|
|---|---:|---:|---:|---:|---|
|orchestrator/tests/test_campaign.py::test_exploration_output_root_env_resolves_worktree_container_before_ensure:10615|16|1|0.002000|False|withdrawn-reference|

## D: 台帳秒上位30件（protected含む）

|関数|行|nodeids|台帳秒|protected|証拠種別|
|---|---:|---:|---:|---:|---|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_s8c_living_doc_reference_negative_controls:723|23|1|43.000000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_two_phase_finalize_crash_injection_recovers_at_all_four_boundaries:10679|76|4|25.300000|False|docs-pin|
|orchestrator/tests/test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing:3745|28|1|22.000000|True|docs-pin|
|orchestrator/tests/test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure:2559|39|1|17.000000|True|docs-pin|
|orchestrator/tests/test_s8b_ratified_freeze.py::test_production_emitter_staged_builder_is_git_deterministic_across_roots:1923|13|1|17.000000|False|docs-pin|
|orchestrator/tests/test_spool_fold.py::test_n37_real_repo_canonical_family_requires_archive_active_history:4257|33|1|17.000000|True|docs-pin|
|orchestrator/tests/test_spool_fold.py::test_phase3_real_canonical_plan_accepts_unique_and_rejects_generated_duplicate_id:4080|98|1|15.000000|True|docs-pin|
|orchestrator/tests/test_spool_fold.py::test_failure_supersede_real_f1_boundary_without_blank_line_is_byte_exact:1753|12|1|13.000000|False|docs-pin|
|orchestrator/tests/test_spool_fold.py::test_failure_supersede_real_final_entry_eof_is_byte_exact:1783|14|1|13.000000|False|docs-pin|
|orchestrator/tests/test_spool_fold.py::test_failure_supersede_real_f196_f197_boundary_is_byte_exact:1767|14|1|12.000000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_finalize_pending_resume_rejects_tampered_published_result:10638|23|1|6.200000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_resume_runner_produces_one_retry_from_admission_selected_recovery:13196|112|1|6.100000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_idempotent_finalization_after_result_json_crash:10431|29|1|6.000000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_result_json_stays_hidden_when_publish_stops_after_markdown:10520|85|1|6.000000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_perf_available_records_receipt_and_preserves_perf_shape:1466|27|1|5.900000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_perf_unavailable_continues_and_records_one_run_receipt:1163|40|1|5.800000|False|docs-pin|
|orchestrator/tests/test_s8b_floor_campaign.py::test_result_json_records_per_attempt_duration_and_no_absolute_monotonic:11334|32|1|5.800000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_foreign_handoff_of_any_shape_is_protected_from_target_collision:2592|26|1|5.500000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_fold_is_called_under_land_lock_and_committed_with_message_file:6535|91|1|4.100000|False|docs-pin|
|orchestrator/tests/test_spool_fold.py::test_boundary_constant_shift_is_detected_by_real_corpus_sentinel:567|20|1|3.300000|False|docs-pin|
|orchestrator/tests/test_codex_worker_launch.py::test_failure_class_enum_and_receipt_recomputation_are_closed:3412|67|1|2.900000|False|docs-pin|
|orchestrator/tests/test_check_branch_rescue.py::test_real_checker_unlanded_spool_details:1782|52|2|2.500000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_post_land_is_not_failed_by_foreign_handoff_activity:8244|29|1|2.400000|False|docs-pin|
|orchestrator/tests/test_spool_fold.py::test_real_corpus_sentinel_rejects_missing_boundary_date:589|12|1|2.400000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_main_fold_resync_reaches_no_fold_and_declared_fold_consumers:9403|62|1|1.800000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_forward_merge_fold_recovery_uses_landing_tip_state_boundary:9199|65|1|0.930000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_active_transaction_recovery_completes_with_provenance_red:7652|78|1|0.860000|False|docs-pin|
|orchestrator/tests/test_plot_a2_certification.py::test_default_legacy_cli_provenance_argv_and_axis_labels:1471|51|1|0.830000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_land_folds_rotation_inside_lock:6767|126|1|0.780000|False|docs-pin|
|orchestrator/tests/test_dev_wave_land.py::test_land_folds_failure_supersede_inside_lock:6895|100|1|0.730000|False|docs-pin|

## 別枠・errors

always-skipped: 0; unresolved evidence: 5215; unevaluable rows: 1198; unevaluable containers: 133; unmatched collect functions: 0; errors: 0.

```json
[]
```

## 限界

動的 import・path 組立・fixture/helper 経由・継承 test・再代入 alias は追跡しない。from-import の属性/関数の存在は検査しない。AST同一でも global binding/fixture/mark は異なり得る。parametrize の非literal容器は行数不明。保護参照は literal 内の file.py::function 形を保守的に関数単位へ広げる。class/module の skip mark は追跡しない。撤回参照は指定見出しと取り消し線の直接参照だけ。docs-pin は静的特徴の共起であり意味を保証しない。
