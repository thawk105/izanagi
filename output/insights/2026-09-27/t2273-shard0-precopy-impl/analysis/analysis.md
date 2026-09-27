# T-2273 A/B measurement

record_category: land-5min-not-met-next-b; land: met; 5min: not-met
land_condition: met; reasons: []
five_minute_goal: {'status': 'not-met', 'median_B_W_max_s': 317.194, 'threshold_s': 300, 'B_runs': [{'run': '02-B', 'W_max_s': 296.137, 'excess_s': -3.863, 'exceeds_300_s': False}, {'run': '03-B', 'W_max_s': 317.194, 'excess_s': 17.194, 'exceeds_300_s': True}, {'run': '06-B', 'W_max_s': 336.973, 'excess_s': 36.973, 'exceeds_300_s': True}]}

B W_max excess over 300 s by run: [{'run': '02-B', 'W_max_s': 296.137, 'excess_s': -3.863, 'exceeds_300_s': False}, {'run': '03-B', 'W_max_s': 317.194, 'excess_s': 17.194, 'exceeds_300_s': True}, {'run': '06-B', 'W_max_s': 336.973, 'excess_s': 36.973, 'exceeds_300_s': True}]

有効対: 3/3; series_invalid: []

対差中央値: 47.74000000000001 秒; 対率中央値: 0.12665647930175244

|slot/attempt|runs|valid|W_0 A|W_0 B|Δi|ri|B 追加 node shard|E1 理由|
|---|---|---|---|---|---|---|---|---|
|1/1|01-A, 02-B|True|351.492|296.137|55.355|0.157|[{'nodeid': 'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_visible_output_snapshot_starts_once_and_preserves_copy', 'shard': 0}]|[]|
|2/1|03-B, 04-A|True|363.195|317.194|46.001|0.127|[{'nodeid': 'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_visible_output_snapshot_starts_once_and_preserves_copy', 'shard': 0}]|[]|
|3/1|05-A, 06-B|True|384.713|336.973|47.740|0.124|[{'nodeid': 'orchestrator/tests/test_s8b_oracle_driver.py::test_t080_visible_output_snapshot_starts_once_and_preserves_copy', 'shard': 0}]|[]|

|run|valid|W_0|W_1|W_2|W_max|argmax|O_max|O worker/items|L|L worker/nodeid|O_max−L|pre|post|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|01-A|True|351.492|228.606|219.000|351.492|[0]|275.859|gw40/2|275.857|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0.002|65.579|10.029|
|02-B|True|296.137|232.923|221.254|296.137|[0]|218.429|gw1/11|200.767|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|17.662|67.448|10.069|
|03-B|True|317.194|312.981|222.917|317.194|[0]|219.901|gw2/11|190.547|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|29.354|77.170|10.028|
|04-A|True|363.195|229.669|220.804|363.195|[0]|287.317|gw2/10|269.360|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|17.957|65.755|10.065|
|05-A|True|384.713|230.841|219.956|384.713|[0]|308.140|gw2/10|266.411|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|41.729|66.488|10.025|
|06-B|True|336.973|267.803|225.250|336.973|[0]|234.535|gw19/39|209.986|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|24.549|72.923|10.028|

## 01-A

valid=True; errors=[]

O_max=275.858793811; L=275.857; O_max−L=0.0017938109999704466

最大占有 worker gw40 の item 列

|nodeid|time|rank|worker_order|
|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|275.857|40|0|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_loader_schema_unicode_and_top_level_fail_soft[{"schema_version":1,"unit":"seconds","nodeid_count":1,"duration_seconds_by_nodeid":{"node":11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111}}]|0.002|84|1|

## 02-B

valid=True; errors=[]

O_max=218.429067831; L=200.767; O_max−L=17.662067831

最大占有 worker gw1 の item 列

|nodeid|time|rank|worker_order|
|---|---|---|---|
|orchestrator/tests/test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels|0.000|1|0|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger|0.000|1|1|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap|0.000|1|2|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command|0.000|1|3|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports|0.000|1|4|
|orchestrator/tests/test_campaign_import_invariant.py::test_known_exception_ledger_is_unique_rationalized_and_commented|0.000|1|5|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception0]|0.001|92|6|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception1]|0.001|93|7|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|189.074|96|8|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|25.196|98|9|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|4.156|100|10|

## 03-B

valid=True; errors=[]

O_max=219.900954343; L=190.547; O_max−L=29.353954342999998

最大占有 worker gw2 の item 列

|nodeid|time|rank|worker_order|
|---|---|---|---|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain|0.000|2|0|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points|0.000|2|1|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_repository_tip_binds_current_decider_version_without_activation|0.001|2|2|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates|0.000|2|3|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan|0.000|2|4|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception0]|0.001|92|5|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception1]|0.001|93|6|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|178.544|96|7|
|orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[replay]|33.581|99|8|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|6.921|100|9|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_live_hook_chain_preserves_collection_identity[unknown-mixed-<lambda>-expected4]|0.851|620|10|

## 04-A

valid=True; errors=[]

O_max=287.316555239; L=269.36; O_max−L=17.95655523900001

最大占有 worker gw2 の item 列

|nodeid|time|rank|worker_order|
|---|---|---|---|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain|0.000|2|0|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points|0.000|2|1|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_repository_tip_binds_current_decider_version_without_activation|0.000|2|2|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates|0.000|2|3|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan|0.000|2|4|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception0]|0.001|92|5|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception1]|0.001|93|6|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|257.571|96|7|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|25.518|98|8|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|4.225|100|9|

## 05-A

valid=True; errors=[]

O_max=308.139738254; L=266.411; O_max−L=41.72873825400001

最大占有 worker gw2 の item 列

|nodeid|time|rank|worker_order|
|---|---|---|---|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain|0.000|2|0|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points|0.000|2|1|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_repository_tip_binds_current_decider_version_without_activation|0.000|2|2|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates|0.000|2|3|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan|0.000|2|4|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception0]|0.001|92|5|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception3]|0.001|95|6|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|254.615|96|7|
|orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[replay]|31.154|99|8|
|orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed|22.368|101|9|

## 06-B

valid=True; errors=[]

O_max=234.535130968; L=209.986; O_max−L=24.549130968000014

最大占有 worker gw19 の item 列

|nodeid|time|rank|worker_order|
|---|---|---|---|
|orchestrator/tests/test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics|166.235|19|0|
|orchestrator/tests/test_s1_measurement_freeze.py::test_verify_rejects_one_byte_freeze_tamper|0.005|63|1|
|orchestrator/tests/test_campaign.py::test_authorization_session_rechecks_prewrite_validator|0.015|167|2|
|orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_records_each_outcome[aborted]|0.464|185|3|
|orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_skips_stock_and_entry_stop[True]|0.681|210|4|
|orchestrator/tests/test_p3_s4_loop.py::test_pair_cli_rejects_conflicts_before_layout_or_claim[extra3]|0.003|246|5|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_b4_sort_cli_receipt_is_continuation_only|0.002|279|6|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_require_sort_oracle_contract_accepts_only_running_contract|0.001|280|7|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_sort_driver_forwards_producer_contract_to_run_campaign|0.001|281|8|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_sort_oracle_contract_call_seams_are_keyword_only_default_none|0.001|282|9|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_resolved_src_token_rejects_both_bindings|0.001|283|10|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate|0.721|284|11|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_pipeline_forwards_one_sort_contract_to_resolver_and_selected_build_api[legacy]|0.156|285|12|
|orchestrator/tests/test_real_repo_serialization.py::test_real_repo_closure_mutations[t810-live-reader-unregistered]|0.006|315|13|
|orchestrator/tests/test_real_repo_serialization.py::test_real_repo_closure_mutations[prewarm-lock-removed]|0.006|322|14|
|orchestrator/tests/test_real_repo_serialization.py::test_real_repo_closure_mutations[nested-collection-node-unregistered]|0.005|323|15|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_calls_both_named_endpoints_once[collection_finish]|0.006|324|16|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_calls_both_named_endpoints_once[xdist_node_collection_finished]|0.006|325|17|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_propagates_single_exception[collection_finish-RuntimeError-receipt]|0.006|326|18|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_propagates_single_exception[xdist_node_collection_finished-RuntimeError-receipt]|0.006|330|19|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_waits_for_peer_after_exception[collection_finish-receipt]|0.057|334|20|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_waits_for_peer_after_exception[xdist_node_collection_finished-receipt]|0.057|336|21|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_both_failures_keep_receipt_primary[xdist_node_collection_finished]|0.006|347|22|
|orchestrator/tests/test_real_repo_serialization.py::test_early_memo_unlock_failure_never_publishes_ready|0.022|360|23|
|orchestrator/tests/test_real_repo_serialization.py::test_early_memo_close_failure_and_lock_contention_are_fail_closed|0.031|362|24|
|orchestrator/tests/test_sort_swo_oracle.py::test_sort_ir_admission_allows_only_ascii_token_whitespace_variation|0.002|367|25|
|orchestrator/tests/test_sort_swo_oracle.py::test_sort_ir_admission_rejects_translation_phase_aliases[raw-string]|0.001|370|26|
|orchestrator/tests/test_sort_swo_oracle.py::test_sort_ir_admission_rejects_translation_phase_aliases[ucn]|0.001|371|27|
|orchestrator/tests/test_sort_swo_oracle.py::test_sort_ir_admission_rejects_translation_phase_aliases[alternative-token]|0.001|372|28|
|orchestrator/tests/test_sort_swo_oracle.py::test_public_oracle_rejects_non_ir_before_environment[generic-lambda]|0.001|373|29|
|orchestrator/tests/test_sort_swo_oracle.py::test_public_oracle_rejects_non_ir_before_environment[body-call]|0.001|374|30|
|orchestrator/tests/test_sort_swo_oracle.py::test_public_oracle_rejects_non_ir_before_environment[unknown-field]|0.001|375|31|
|orchestrator/tests/test_sort_swo_oracle.py::test_public_oracle_rejects_non_ir_before_environment[duplicate-field]|0.001|376|32|
|orchestrator/tests/test_sort_swo_oracle.py::test_public_oracle_rejects_non_ir_before_environment[additional-statement]|0.001|377|33|
|orchestrator/tests/test_sort_swo_oracle.py::test_public_oracle_rejects_non_ir_before_environment[json-string]|0.001|378|34|
|orchestrator/tests/test_sort_swo_oracle.py::test_validate_single_sort_statement_is_renderer_postcondition_only|0.001|379|35|
|orchestrator/tests/test_sort_swo_oracle.py::test_compiled_relation_mismatch_is_unavailable_not_pass|0.015|380|36|
|orchestrator/tests/test_sort_swo_oracle.py::test_trusted_evaluator_matches_real_tu_for_all_79_ir_values|65.937|381|37|
|orchestrator/tests/test_sort_swo_oracle.py::test_production_dependency_verifier_rejects_manifest_boundary_mutations[symlink]|0.069|386|38|

## 限界

固定 2 tree は同一 node・同一 allocation ではない。同時刻性は隣接逐次投入による。
投入台帳は launcher が追記専用で扱う通常ファイル。台帳自身の改竄・削除（RUN と同時の削除を含む）や外部の同時変更は防げない。追記後の異常終了は自動修復せず拒否する。
