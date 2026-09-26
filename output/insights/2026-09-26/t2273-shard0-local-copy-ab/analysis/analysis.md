# T-2273 A/B measurement

land_condition: not-met; reasons: ['not all three pair deltas are positive', 'median pair rate below 10%']
five_minute_goal: {'status': 'not-met', 'median_B_W_max_s': 348.387, 'threshold_s': 300}

有効対: 3/3; series_invalid: []

対差中央値: 19.11099999999999 秒; 対率中央値: 0.05200300409798146

|slot/attempt|runs|valid|W_0 A|W_0 B|Δi|ri|B 追加 node shard|E1 理由|
|---|---|---|---|---|---|---|---|---|
|1/1|01-A|False|—|—|—|—|[]|[]|
|1/2|02-A|False|—|—|—|—|[]|[]|
|1/3|03-A, 04-B|False|—|—|—|—|[]|[]|
|1/4|05-A, 06-B|True|367.498|348.387|19.111|0.052|[0]|[]|
|2/1|07-B, 08-A|True|344.833|325.154|19.679|0.057|[0]|[]|
|3/1|09-A, 10-B|True|353.559|357.900|-4.341|-0.012|[0]|[]|

|run|valid|W_0|W_1|W_2|W_max|argmax|O_max|O worker/items|L|L worker/nodeid|O_max−L|pre|post|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|01-A|False|—|—|—|—|—|—|—|—|—|—|—|—|
|02-A|False|—|—|—|—|—|—|—|—|—|—|—|—|
|03-A|True|427.783|264.901|222.709|427.783|[0]|349.359|gw2/10|331.462|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|17.897|68.141|10.060|
|04-B|False|—|—|—|—|—|—|—|—|—|—|—|—|
|05-A|True|367.498|225.581|229.286|367.498|[0]|292.981|gw2/10|270.133|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|22.848|64.430|10.028|
|06-B|True|348.387|232.539|229.819|348.387|[0]|272.250|gw1/11|251.443|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|20.807|65.874|10.066|
|07-B|True|325.154|226.731|217.032|325.154|[0]|250.699|gw40/2|250.698|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0.001|64.402|10.027|
|08-A|True|344.833|224.458|219.137|344.833|[0]|270.367|gw2/10|252.920|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|17.447|64.347|10.062|
|09-A|True|353.559|225.331|217.679|353.559|[0]|278.627|gw2/10|261.753|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|16.874|64.800|10.063|
|10-B|True|357.900|226.482|218.398|357.900|[0]|283.506|gw1/11|264.877|gw40/orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|18.629|64.274|10.063|

## 01-A

valid=False; errors=['rc/copy_ok']

## 02-A

valid=False; errors=['rc/copy_ok']

## 03-A

valid=True; errors=[]

O_max=349.359204729; L=331.462; O_max−L=17.89720472900001

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
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|320.303|96|7|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|24.714|98|8|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|4.339|100|9|

## 04-B

valid=False; errors=['rc/copy_ok']

## 05-A

valid=True; errors=[]

O_max=292.981240058; L=270.133; O_max−L=22.848240058000044

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
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|259.108|96|7|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_valid_auditor_pass_digest_echo_cannot_reverse_host_effect_rejects|2.363|97|8|
|orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[replay]|31.506|99|9|

## 06-B

valid=True; errors=[]

O_max=272.250455005; L=251.443; O_max−L=20.80745500499998

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
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|239.874|96|8|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|27.120|98|9|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|5.253|100|10|

## 07-B

valid=True; errors=[]

O_max=250.69907129; L=250.698; O_max−L=0.0010712899999987258

最大占有 worker gw40 の item 列

|nodeid|time|rank|worker_order|
|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|250.698|40|0|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_loader_schema_unicode_and_top_level_fail_soft[{"schema_version":1,"unit":"seconds","nodeid_count":1,"duration_seconds_by_nodeid":{"node":11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111}}]|0.002|84|1|

## 08-A

valid=True; errors=[]

O_max=270.367159542; L=252.92; O_max−L=17.447159542000037

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
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|241.566|96|7|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|24.613|98|8|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|4.185|100|9|

## 09-A

valid=True; errors=[]

O_max=278.626823174; L=261.753; O_max−L=16.873823173999995

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
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|249.973|96|7|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|24.348|98|8|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|4.303|100|9|

## 10-B

valid=True; errors=[]

O_max=283.505718108; L=264.877; O_max−L=18.628718107999987

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
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|253.788|96|8|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|25.489|98|9|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|4.225|100|10|

## 限界

固定 2 tree は同一 node・同一 allocation ではない。同時刻性は隣接逐次投入による。
投入台帳は launcher が追記専用で扱う通常ファイル。台帳自身の改竄・削除（RUN と同時の削除を含む）や外部の同時変更は防げない。追記後の異常終了は自動修復せず拒否する。
