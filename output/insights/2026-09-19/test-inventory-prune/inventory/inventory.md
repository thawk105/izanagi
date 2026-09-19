# Static test inventory

判定は仮説。削除確定には意味確認と変異検査が必要。分類間は重複する。

Each category sums each matching function once (categories overlap); lines include decorators through end_lineno; nodeids count collect-file entries; seconds sum ledger lookup per entry with missing=0; file lines are whole-file splitlines counts. Suppression counts evidence entries and affected functions; production target counts each unprotected A/B/C function once per target (targets overlap); empty targets counted separately.

対象 333 files / 510327 file lines; 除外 30 files / 67920 lines.

|範囲|関数|行|nodeids|台帳秒|台帳欠落 nodeids|
|---|---:|---:|---:|---:|---:|
|全対象|14416|345321|21882|15587.593000|949|
|protected|634|21114|918|4969.357000|230|
|A including_protected|114|3045|155|49.991000|28|
|A excluding_protected|112|2961|153|49.964000|28|
|B including_protected|36|431|148|125.970000|1|
|B excluding_protected|35|419|147|125.970000|0|
|C including_protected|1|16|1|0.002000|0|
|C excluding_protected|1|16|1|0.002000|0|
|D including_protected|297|10397|362|296.410000|12|
|D excluding_protected|291|10099|356|225.392000|12|

## A: 台帳秒上位30件（protected含む）

|関数|行|nodeids|台帳秒|protected|証拠種別|
|---|---:|---:|---:|---:|---|
|orchestrator/tests/test_official_perf_closure.py::test_outer_perf_file_mutations_are_not_tautologies:920|16|1|25.000000|False|path-missing|
|orchestrator/tests/test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches:8014|187|1|8.400000|False|path-missing|
|orchestrator/tests/test_official_perf_closure.py::test_closure_inventory_mutations_are_not_tautologies:871|37|1|2.800000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_git_operation_surface_is_read_only_except_sha_ff_merge:8275|36|1|2.200000|False|flag-missing|
|orchestrator/tests/test_audit_dangling_commits.py::test_pattern_owners_complete_for_large_shared_ancestor_population:3286|23|1|1.600000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_d987_two_stage_chain_accepts_final_net_runner_restore:8590|43|1|0.650000|False|flag-missing|
|orchestrator/tests/test_growth_test_holds_contract.py::test_noconftest_bypass_is_refused_before_held_body:2440|18|1|0.600000|False|path-missing|
|orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip:2534|20|1|0.600000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_d987_rejects_final_runner_change_before_provenance_rc16:1602|67|1|0.440000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_active_forward_fold_d987_rejection_retains_lease_and_main:9266|68|1|0.430000|False|flag-missing, path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_d987_runner_lookup_process_failure_is_retryable:8635|37|1|0.430000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_d987_two_stage_chain_rejects_change_only_in_last_main:8557|31|1|0.430000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_accepts_non_attributable_receipt_and_emits_red_nodeids:1486|20|1|0.420000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_accepts_flake_only_and_emits_flake_nodeids:1508|25|1|0.410000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_accepts_mixed_red_and_flake_nodeids_without_merging_sets:1535|21|1|0.360000|False|path-missing|
|orchestrator/tests/test_related_work_search.py::test_cli_exposes_only_required_axis3_phases:1585|18|1|0.350000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_child_green_runner_path_absence_is_permanent_rejection:1836|28|1|0.340000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_runner_path_absence_is_permanent_rejection:1804|30|1|0.340000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_child_green_runner_lookup_process_failure_is_retryable:1959|37|1|0.320000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_runner_lookup_process_failure_is_retryable:1926|31|1|0.290000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_provenance_receipt_rejects_tip_that_moves_during_audit:5624|23|1|0.270000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_internal_fold_planning_interrupt_is_never_release_safe:9890|32|1|0.250000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_missing_recovery_gate_receipt_returns_rc31_before_main_change:11347|24|1|0.250000|False|path-missing|
|orchestrator/tests/test_mutation_harness.py::test_match_key_preserves_real_parametrize_ids_containing_at:1051|26|4|0.242000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_post_provenance_head_change_preserves_provenance_rejection_order:5649|37|1|0.240000|False|flag-missing|
|orchestrator/tests/test_dev_wave_land.py::test_standalone_origin_state_is_not_auto_recovered:7979|35|1|0.230000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_candidate_fold_plan_failure_happens_before_ff:6515|18|1|0.210000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_generated_docs_declares_exact_active_transaction:6739|26|1|0.200000|False|path-missing|
|orchestrator/tests/test_dev_wave_land.py::test_land_runner_gate_uses_tested_main_after_main_reaches_tip:1998|32|1|0.200000|False|flag-missing|
|orchestrator/tests/test_t139_approval_payload.py::test_duplicate_d282_heading_is_rejected:178|8|1|0.150000|False|docs-heading-missing|

## B: 台帳秒上位30件（protected含む）

|関数|行|nodeids|台帳秒|protected|証拠種別|
|---|---:|---:|---:|---:|---|
|orchestrator/tests/test_s8b_holdout_freeze.py::test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility:2381|36|3|100.000000|False|duplicate-parametrize-row|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete:623|12|1|21.000000|False|identical-body-and-decorators|
|orchestrator/tests/test_reflux_origin_binding.py::test_store_scope_type_and_closed_values_are_rejected:744|4|4|2.390000|False|duplicate-parametrize-row|
|orchestrator/tests/test_paper_story_a1_paired.py::test_m_nc07_decoded_noncertifying_lock_scopes_collector_anomaly_gate:3878|25|5|1.500000|False|duplicate-parametrize-row|
|orchestrator/tests/test_paper_story_a1_paired.py::test_materializer_requires_exact_zero_driver_and_shell_rc:3307|50|3|0.640000|False|duplicate-parametrize-row|
|orchestrator/tests/test_paper_story_a1_paired.py::test_v3_sized_statistics_reject_invalid_decimal_values:1254|18|26|0.290000|False|duplicate-parametrize-row|
|orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_coder_proposal_rejects_invalid_wire_corpus:2001|13|15|0.016000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t1434_t1222_science_slice.py::test_pinned_jobs_guard_skips_when_root_exists_but_one_file_is_missing:452|14|1|0.014000|False|identical-body-and-decorators|
|orchestrator/tests/test_s8c_result_judge.py::test_invalid_params_are_preregistration_not_effective:548|28|10|0.010000|False|duplicate-parametrize-row|
|orchestrator/tests/test_codex_reasoning_ab.py::test_bound_price_rejects_numeric_stage_type_confusion:7338|13|2|0.008000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t1434_t1222_science_slice.py::test_pinned_jobs_guard_does_not_skip_for_complete_input_set:468|7|1|0.008000|False|identical-body-and-decorators|
|orchestrator/tests/test_t189_oracle_wiring_slice.py::test_pinned_jobs_guard_skips_when_root_exists_but_one_file_is_missing:154|14|1|0.008000|False|identical-body-and-decorators|
|orchestrator/tests/test_trigger_gate_binding.py::test_mask_rejects_non_exact_int_and_out_of_range:91|13|7|0.008000|False|duplicate-parametrize-row|
|orchestrator/tests/test_campaign_lock_codec.py::test_v2_rejects_non_positive_or_non_exact_activation_serial:402|8|7|0.007000|False|duplicate-parametrize-row|
|orchestrator/tests/test_env_contract.py::test_rejects_bad_attestation_mode:191|4|7|0.007000|False|duplicate-parametrize-row|
|orchestrator/tests/test_env_contract.py::test_generation_entry_rejects_nonpositive_or_non_int_generation:325|4|6|0.006000|False|duplicate-parametrize-row|
|orchestrator/tests/test_p3_s4_loop.py::test_coder_proposal_value_domain_accepts_declared_integral_boundaries:3248|13|6|0.006000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t471_restore_bound.py::test_attempt_rejects_bad_success_call_count:136|5|5|0.005000|False|duplicate-parametrize-row|
|orchestrator/tests/test_p3_autonomous_workload_trial.py::test_origin_campaign_run_rejects_non_exact_query_ordinal:10511|12|4|0.004000|False|duplicate-parametrize-row|
|orchestrator/tests/test_p3_s4_loop.py::test_planner_context_payload_rejects_non_string_policy_hint:6434|9|4|0.004000|False|duplicate-parametrize-row|
|orchestrator/tests/test_plot_b10_extended_backoff.py::test_pinned_measurement_requirements_are_exact:354|3|1|0.004000|False|identical-body-and-decorators|
|orchestrator/tests/test_s8a_trigger_sweep.py::test_condition_gate_preflight_dominates_candidate_evaluation:86|3|1|0.004000|False|identical-body-and-decorators|
|orchestrator/tests/test_s8b_descriptor.py::test_policy_hint_requires_exact_string:77|7|4|0.004000|False|duplicate-parametrize-row|
|orchestrator/tests/test_s8b_oracle_artifacts.py::test_exploration_package_rejects_invalid_hint:91|14|4|0.004000|False|duplicate-parametrize-row|
|orchestrator/tests/test_s8c_generation_projection.py::test_gating_spec_snapshot_requires_exact_str:573|4|4|0.004000|False|duplicate-parametrize-row|
|orchestrator/tests/test_s6_sort_sweep.py::test_condition_gate_preflight_dominates_candidate_evaluation:79|3|1|0.003000|False|identical-body-and-decorators|
|orchestrator/tests/test_s8b_selector_output.py::test_type_coercion_is_not_performed:309|12|3|0.003000|False|duplicate-parametrize-row|
|orchestrator/tests/test_s8c_generation_projection.py::test_apply_critic_feedback_rejects_invalid_source_generation:307|10|3|0.003000|False|duplicate-parametrize-row|
|orchestrator/tests/test_t189_oracle_wiring_slice.py::test_pinned_jobs_guard_does_not_skip_for_complete_input_set:170|7|1|0.003000|False|identical-body-and-decorators|
|orchestrator/tests/test_codex_reasoning_ab.py::test_all_null_numeric_equivalent_stage_remains_accepted:7613|13|2|0.002000|False|duplicate-parametrize-row|

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

## B1 group 7c6d2ef3453a6694cf2717efceb423baaf116d5daeb542fe2f338ccce6ae7227

|file:line qualname|protected|referenced_by|台帳秒|
|---|---|---|---:|
|orchestrator/tests/test_s6_sort_sweep.py:79 test_condition_gate_preflight_dominates_candidate_evaluation|False|False|0.003000|
|orchestrator/tests/test_s8a_trigger_sweep.py:86 test_condition_gate_preflight_dominates_candidate_evaluation|False|False|0.004000|

## B1 group 7c988232a6763287b6a86195979306dfebe538d3ab4df65dc92fed5526d08e67

|file:line qualname|protected|referenced_by|台帳秒|
|---|---|---|---:|
|orchestrator/tests/test_paper_story_a1_headline.py:1366 test_self_run_harness_rejects_invalid_test_sets_before_execution|False|False|0.001000|
|orchestrator/tests/test_paper_story_a1_headline_sizing.py:2074 test_self_run_harness_rejects_invalid_test_sets_before_execution|False|False|0.001000|

## B1 group 8ff4623b0a9fb64c44cc1d7c99786867c2a74548c020a1f992fb982659050404

|file:line qualname|protected|referenced_by|台帳秒|
|---|---|---|---:|
|orchestrator/tests/test_b10_extended_figure_provenance.py:891 test_pinned_measurement_requirements_are_exact|False|False|0.001000|
|orchestrator/tests/test_plot_b10_extended_backoff.py:354 test_pinned_measurement_requirements_are_exact|False|False|0.004000|

## B1 group c8c8f5483b4f9a55803ceab4f538c8afb4b282718405079eb5cb057cfa1a35a4

|file:line qualname|protected|referenced_by|台帳秒|
|---|---|---|---:|
|orchestrator/tests/test_real_repo_serialization.py:894 test_t080_output_snapshot_observes_git_visible_create_and_delete|True|False|0.000000|
|orchestrator/tests/test_s8b_oracle_driver.py:623 test_t080_output_snapshot_observes_git_visible_create_and_delete|False|False|21.000000|

## B1 group e19800cece07780471a51c11610e27831bb581bc3e7a570b21a7e0726ea1ac29

|file:line qualname|protected|referenced_by|台帳秒|
|---|---|---|---:|
|orchestrator/tests/test_t1434_t1222_science_slice.py:468 test_pinned_jobs_guard_does_not_skip_for_complete_input_set|False|False|0.008000|
|orchestrator/tests/test_t189_oracle_wiring_slice.py:170 test_pinned_jobs_guard_does_not_skip_for_complete_input_set|False|False|0.003000|

## B1 group e524a80036688919257f1d51cc80ddb1964cfe822a882c567ee82d9ec8b2afad

|file:line qualname|protected|referenced_by|台帳秒|
|---|---|---|---:|
|orchestrator/tests/test_t1434_t1222_science_slice.py:452 test_pinned_jobs_guard_skips_when_root_exists_but_one_file_is_missing|False|False|0.014000|
|orchestrator/tests/test_t189_oracle_wiring_slice.py:154 test_pinned_jobs_guard_skips_when_root_exists_but_one_file_is_missing|False|False|0.008000|

## B1 group ff7040743647e71df8705e67efb1ca8efc300680f5a53165c107925436cec26c

|file:line qualname|protected|referenced_by|台帳秒|
|---|---|---|---:|
|orchestrator/tests/test_s6_sort_sweep.py:297 test_perf_is_p2_2_operating_point|False|False|0.001000|
|orchestrator/tests/test_s8a_trigger_sweep.py:387 test_perf_is_p2_2_operating_point|False|False|0.001000|

## B2 重複 row 全件

|file:decorator 行 / 関数|row位置 (0-based)|一致するrow|値 repr|
|---|---:|---|---|
|orchestrator/tests/test_campaign_lock_codec.py:402 test_v2_rejects_non_positive_or_non_exact_activation_serial|2|[1]|0|
|orchestrator/tests/test_campaign_lock_codec.py:402 test_v2_rejects_non_positive_or_non_exact_activation_serial|4|[0]|1.0|
|orchestrator/tests/test_codex_reasoning_ab.py:7338 test_bound_price_rejects_numeric_stage_type_confusion|1|[0]|1.0|
|orchestrator/tests/test_codex_reasoning_ab.py:7613 test_all_null_numeric_equivalent_stage_remains_accepted|1|[0]|1.0|
|orchestrator/tests/test_env_contract.py:191 test_rejects_bad_attestation_mode|3|[2]|0|
|orchestrator/tests/test_env_contract.py:325 test_generation_entry_rejects_nonpositive_or_non_int_generation|3|[0]|False|
|orchestrator/tests/test_env_contract.py:325 test_generation_entry_rejects_nonpositive_or_non_int_generation|4|[2]|1.0|
|orchestrator/tests/test_p3_autonomous_workload_trial.py:10511 test_origin_campaign_run_rejects_non_exact_query_ordinal|3|[2]|1.0|
|orchestrator/tests/test_p3_s4_loop.py:3248 test_coder_proposal_value_domain_accepts_declared_integral_boundaries|1|[0]|1.0|
|orchestrator/tests/test_p3_s4_loop.py:3248 test_coder_proposal_value_domain_accepts_declared_integral_boundaries|3|[2]|20.0|
|orchestrator/tests/test_p3_s4_loop.py:3248 test_coder_proposal_value_domain_accepts_declared_integral_boundaries|5|[4]|1000.0|
|orchestrator/tests/test_p3_s4_loop.py:6434 test_planner_context_payload_rejects_non_string_policy_hint|2|[1]|1|
|orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2001 test_coder_proposal_rejects_invalid_wire_corpus|3|[2]|0|
|orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2001 test_coder_proposal_rejects_invalid_wire_corpus|4|[1]|1|
|orchestrator/tests/test_paper_story_a1_paired.py:1255 test_v3_sized_statistics_reject_invalid_decimal_values|6|[1]|0|
|orchestrator/tests/test_paper_story_a1_paired.py:3307 test_materializer_requires_exact_zero_driver_and_shell_rc|1|[0]|('driver_rc', 1)|
|orchestrator/tests/test_paper_story_a1_paired.py:3878 test_m_nc07_decoded_noncertifying_lock_scopes_collector_anomaly_gate|4|[3]|(1, False)|
|orchestrator/tests/test_reflux_origin_binding.py:744 test_store_scope_type_and_closed_values_are_rejected|3|[1]|True|
|orchestrator/tests/test_s8b_descriptor.py:77 test_policy_hint_requires_exact_string|2|[1]|1|
|orchestrator/tests/test_s8b_holdout_freeze.py:2381 test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility|2|[0]|True|
|orchestrator/tests/test_s8b_oracle_artifacts.py:91 test_exploration_package_rejects_invalid_hint|3|[2]|('reps', 0)|
|orchestrator/tests/test_s8b_selector_output.py:309 test_type_coercion_is_not_performed|1|[0]|({'choice_id': True}, 'choice_id_type')|
|orchestrator/tests/test_s8c_generation_projection.py:307 test_apply_critic_feedback_rejects_invalid_source_generation|1|[0]|1.0|
|orchestrator/tests/test_s8c_generation_projection.py:573 test_gating_spec_snapshot_requires_exact_str|2|[1]|True|
|orchestrator/tests/test_s8c_result_judge.py:548 test_invalid_params_are_preregistration_not_effective|1|[0]|('n', True)|
|orchestrator/tests/test_t471_restore_bound.py:136 test_attempt_rejects_bad_success_call_count|4|[3]|1.0|
|orchestrator/tests/test_trigger_gate_binding.py:91 test_mask_rejects_non_exact_int_and_out_of_range|4|[2]|1.0|

## C 全件

|関数|参照|根拠|protected|台帳秒|
|---|---|---|---|---:|
|orchestrator/tests/test_campaign.py::test_exploration_output_root_env_resolves_worktree_container_before_ensure:10615|D158|docs/decisions.md:25647 ## D641. official campaign の出力 root を repo 外へ強制し、D158 の「official は env を参照しない」記述の該当部分を supersede する (2026-08-22)|False|0.002000|

## D pin先別 上位30件（台帳秒順）

各pin先で関数を一度集計。複数pin先を持つ関数は表の行間で重複する。

|pin先|関数|行|台帳秒|
|---|---:|---:|---:|
|result.md|9|437|84.100000|
|docs/definitely-missing-s8c-negative-control.md|1|23|43.000000|
|phase3-8c-preregistration.md:1|1|23|43.000000|
|docs/failures.md|17|738|40.343000|
|docs/spool/FOLDED.md|38|1760|32.928000|
|docs/worklog.md|40|1478|27.897000|
|docs/archive|3|65|22.700000|
|worklog-*.md|3|65|22.700000|
|/focus1.md|1|28|22.000000|
|docs/phase3.md|20|934|17.699000|
|focus1.md|3|57|17.007000|
|focus2.md|2|47|17.006000|
|docs/spool/worklog/|1|33|17.000000|
|/incoming.md|1|26|5.500000|
|docs/ruleops-candidates.json|23|690|3.824000|
|docs/spool/worklog/2026-08-25-topic-1.md|12|476|3.615000|
|accepted-invalid-output.md|1|67|2.900000|
|post-land.md|1|29|2.400000|
|docs/decisions.md|12|700|2.017000|
|docs/archive/README.md|5|559|1.936000|
|README.md|11|198|1.180000|
|docs/spool/worklog/2026-08-03-test-wave-1.md|2|262|1.110000|
|.md|11|740|0.986000|
|docs/handoff/README.md|3|69|0.973000|
|output/insights/report.md|6|158|0.964000|
|docs/dev-wave/operations.md|2|200|0.940000|
|docs/spool/decisions/2026-08-25-topic-1.md|8|150|0.905000|
|docs/paper-story/results/2026-09-07-a2-certification-reject.md|2|72|0.853000|
|output/insights/source.md|5|179|0.816000|
|docs/spool/worklog/synthetic.md|4|145|0.800000|

## 抑制・未解決の内訳

synthetic-fixture: 273 functions / 510 evidence entries

```json
{
  "suppressed_by_kind": {
    "docs-heading-missing": 31,
    "flag-missing": 90,
    "path-missing": 389
  },
  "unresolved_by_kind": {
    "flag-source-unresolved": 3880,
    "non-path-shaped-literal": 4,
    "unevaluable-parametrize-container": 133,
    "unevaluable-parametrize-row": 1198
  },
  "abc_production_targets_excluding_protected": {
    "orchestrator/campaign/campaign_lock.py": 3,
    "orchestrator/campaign/claude_transport.py": 1,
    "orchestrator/campaign/env_contract.py": 2,
    "orchestrator/campaign/layout.py": 2,
    "orchestrator/campaign/p3_autonomous_workload_trial.py": 1,
    "orchestrator/campaign/p3_b4_wiring_probe.py": 1,
    "orchestrator/campaign/p3_s4_loop.py": 2,
    "orchestrator/campaign/p3_s4_loop_trigger_gating.py": 2,
    "orchestrator/campaign/paper_story_a1_paired.py": 2,
    "orchestrator/campaign/reflux_ir.py": 1,
    "orchestrator/campaign/reflux_origin_binding.py": 1,
    "orchestrator/campaign/s6_sort_sweep.py": 2,
    "orchestrator/campaign/s8a_trigger_sweep.py": 2,
    "orchestrator/campaign/s8b_descriptor.py": 1,
    "orchestrator/campaign/s8b_holdout_freeze.py": 1,
    "orchestrator/campaign/s8b_materialization.py": 1,
    "orchestrator/campaign/s8b_oracle_artifacts.py": 1,
    "orchestrator/campaign/s8b_oracle_exploration.py": 1,
    "orchestrator/campaign/s8c_generation_projection.py": 2,
    "orchestrator/campaign/s8c_result_judge.py": 1,
    "orchestrator/campaign/trigger_gate_binding.py": 1,
    "orchestrator/preregistration/addendum_envelope.py": 3,
    "orchestrator/preregistration/approval_payload.py": 3,
    "orchestrator/publication/addendum_p_envelope.py": 3,
    "orchestrator/publication/report.py": 4,
    "orchestrator/related_work_search.py": 2,
    "orchestrator/tests/flaky_test_holds.py": 2,
    "orchestrator/tests/output_snapshot_ignores.py": 1,
    "tools/dev_waves/git_state.py": 4
  },
  "abc_without_production_targets_excluding_protected": 101
}
```

## 別枠・errors

always-skipped: 0; unresolved evidence: 5215; unevaluable rows: 1198; unevaluable containers: 133; unmatched collect functions: 0; errors: 0.

```json
[]
```

## 限界

動的 import・path 組立・fixture/helper 経由・継承 test・再代入 alias は追跡しない。from-import の属性/関数の存在は検査しない。本文・decorator AST同一でも global binding/fixture/class・module mark は異なり得る。合成指標は関数単位の保守的抑制で真の不在も落とし得る。module-missing は抑制対象外。production_targets は直下importと本文の名前参照のみで、shadowing・helper経由は追跡しない。parametrize の非literal容器は行数不明。保護参照は literal 内の file.py::function 形を保守的に関数単位へ広げる。class/module の skip mark は追跡しない。撤回参照は指定見出しと取り消し線の直接参照だけ。docs-pin は静的特徴の共起であり意味を保証しない。
