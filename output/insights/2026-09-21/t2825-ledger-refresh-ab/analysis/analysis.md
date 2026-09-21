# T-2825 A/B measurement

方向一致・閾値以上

ΔW = A−B、ΔO / ΔL / Δ(O−L) = B−A。L の観測規則は shard-0 に適用。

推定開始は worker の first_test_started_epoch_s + 同 worker の JUnit 順先行 time 累積。item 間の空白は未観測。

10% は事前登録の保守基準で D357 からの導出ではない。3/3 一致は有意差ではない。

|量|分岐|判定|副分類|med Δ|med r|条件別中央値差|
|---|---|---|---|---|---|---|
|W_0 一次|(i)|方向一致・閾値以上|—|147.776|0.306|147.776|
|W_max 補助|(i)|方向一致・閾値以上|—|147.776|0.306|147.776|

事前登録した L 伸長の判定条件を満たさない


series_invalid:

有効対=3; 投入=7/12

|条件|測定台帳 hash|集計時の worktree の台帳 hash|警告|
|---|---|---|---|
|A|1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a|1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a|—|
|B|27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f|27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f|—|

|条件|対象走番号|shard|med W|med O|med L|med F|med pre|med post|
|---|---|---|---|---|---|---|---|---|
|A|01, 05, 06|0|482.215|409.508|231.272|73.398|62.758|10.032|
|A|01, 05, 06|1|251.765|185.365|148.008|66.613|62.913|3.600|
|A|01, 05, 06|2|146.057|74.244|60.190|71.840|63.538|4.182|
|B|02, 04, 07|0|334.439|261.287|227.380|73.618|63.496|10.063|
|B|02, 04, 07|1|218.557|151.021|139.244|67.408|63.714|3.581|
|B|02, 04, 07|2|191.105|124.509|124.508|66.262|62.845|3.324|

脚注: 条件別・shard 別中央値は有効対の採用走が対象。偶数個のときは中央 2 値の算術平均、対象 0 件は欠測 (null)。

|slot/attempt|runs|valid|W0 A|W0 B|ΔW|r|D357|ΔO0|ΔL0|Δ(O0−L0)|Wmax A|Wmax B|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1/1|01-A, 02-B|True|482.215|334.439|147.776|0.306||-148.222|7.331|-155.553|482.215|334.439|
|2/1|03-B|False|—|—|—|—|—|—|—|—|—|—|
|2/2|04-B, 05-A|True|511.326|310.663|200.663|0.392||-200.883|-8.972|-191.911|511.326|310.663|
|3/1|06-A, 07-B|True|374.494|344.931|29.563|0.079|1 走比較として変化なし|-29.136|1.133|-30.269|374.494|344.931|

対 1/1:  L 増大を伴う差の縮小

L 交代=True: orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] → orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal

|移動 A→B|件数|time A 和|time B 和|
|---|---|---|---|
|1->2|4679|2188.898|1975.769|
|2->1|5256|1257.496|1298.821|

対 2/1: incomplete/nonadjacent pair, wrong slot/order, or half reuse

対 2/2:

L 交代=True: orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] → orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal

|移動 A→B|件数|time A 和|time B 和|
|---|---|---|---|
|1->2|4679|2075.198|2028.329|
|2->1|5256|1235.146|1323.140|

対 3/1:  L 増大を伴う差の縮小

L 交代=True: orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] → orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal

|移動 A→B|件数|time A 和|time B 和|
|---|---|---|---|
|1->2|4679|2058.890|1960.365|
|2->1|5256|1270.502|1329.945|

## 01-A (A)

valid=True; errors=[]; 測定台帳 hash=1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a; 集計時の worktree の台帳 hash=1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a; 警告=None

投入=2026-09-21T10:04:04+0900; 完了=2026-09-21T10:13:42+0900; leader=1; load1=27.21

W_max=482.215; argmax=[0]

|shard|W|O|L|O−L|F|pre|post|O worker|L worker|P_L|node|job ID|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|482.215|409.508|238.951|170.557|72.707|62.586|10.040|gw37|gw5|0.001|bnode023|0:14750.nqsv|
|1|253.009|186.396|147.010|39.386|66.613|62.913|3.600|gw0|gw2|0.001|bnode020|0:14749.nqsv|
|2|146.084|74.244|60.226|14.018|71.840|63.538|4.182|gw0|gw2|13.715|bnode025|0:14751.nqsv|

|shard|selected count|selected sha256|台帳予測負荷|未登録|worker/item 件数|
|---|---|---|---|---|---|
|0|4149|e34aab9e3433a98da7dbd0875a6f80a509ecdd523729dc598501a6fa7d295410|7749.524|367|gw1:880, gw2:14, gw9:2, gw20:449, gw21:277, gw22:16, gw11:2, gw10:2, gw19:178, gw16:342, gw8:2, gw7:2, gw6:2, gw18:3, gw26:3, gw23:37, gw27:15, gw31:47, gw30:15, gw24:34, gw13:2, gw4:2, gw38:247, gw5:2, gw36:70, gw28:3, gw32:143, gw12:2, gw25:85, gw17:3, gw37:40, gw46:37, gw41:32, gw39:97, gw40:113, gw14:7, gw0:62, gw15:384, gw29:110, gw34:7, gw35:31, gw44:7, gw42:62, gw43:93, gw33:4, gw45:51, gw47:28, gw3:103|
|1|10309|ac5ace0c052c2c25f2eaf02b6246b4cd72c62f32d8953a92c50d9586e53708f0|6350.295|866|gw40:325, gw6:204, gw11:200, gw14:197, gw17:346, gw4:2, gw26:230, gw22:282, gw19:287, gw27:268, gw30:208, gw38:219, gw39:222, gw3:2, gw5:219, gw18:178, gw15:119, gw34:210, gw9:196, gw12:201, gw7:209, gw20:244, gw10:206, gw13:261, gw21:218, gw16:216, gw24:227, gw23:273, gw33:143, gw32:281, gw31:234, gw29:187, gw35:358, gw8:199, gw25:219, gw28:308, gw37:264, gw36:316, gw46:274, gw44:309, gw43:174, gw47:290, gw41:199, gw42:322, gw45:209, gw0:50, gw1:2, gw2:2|
|2|12350|cbd722029024f0362c7b39fc1b1cc4c0f62ee265893d5b9d9fc60d63368403ba|6350.296|1353|gw17:261, gw38:228, gw6:208, gw20:244, gw29:241, gw21:229, gw18:288, gw44:240, gw42:325, gw36:289, gw8:228, gw15:242, gw32:266, gw16:244, gw13:245, gw35:302, gw11:274, gw22:237, gw40:245, gw3:225, gw1:190, gw9:230, gw2:177, gw24:286, gw34:238, gw41:324, gw27:322, gw0:407, gw37:298, gw46:272, gw19:292, gw30:226, gw33:335, gw47:242, gw26:250, gw23:255, gw12:281, gw10:229, gw4:225, gw25:256, gw14:235, gw7:226, gw28:288, gw45:264, gw31:232, gw39:248, gw5:219, gw43:242|

|shard|L nodeid|L rank|L partner|O_L|
|---|---|---|---|---|
|0|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|5|0|238.952|
|1|orchestrator/tests/test_p3_b4_raw_record_producer.py::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings|2|0|147.011|
|2|orchestrator/tests/test_dev_wave_wait.py::test_producer_waiter_kill_requires_later_check_only_receipt[sigterm]|2|0|73.941|

shard-0 worker gw37 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_s8c_living_doc_reference_negative_controls|0|gw37|37|0|42.412|37|0.000|1789952740.525|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_loader_schema_unicode_and_top_level_fail_soft[{"schema_version":2,"unit":"seconds","nodeid_count":0,"duration_seconds_by_nodeid":{}}]|0|gw37|81|1|0.001|174|42.412|1789952782.937|
|orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_coverage_denied|0|gw37|167|0|0.003|175|42.413|1789952782.938|
|orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_script_denied|0|gw37|168|0|0.001|176|42.416|1789952782.941|
|orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_nonexecuting_and_light_allowed|0|gw37|169|0|0.031|177|42.417|1789952782.942|
|orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_nonrefusing_sites_unchanged|0|gw37|170|0|0.012|179|42.448|1789952782.973|
|orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_deep_nesting_has_no_stack_limit|0|gw37|172|0|2.538|180|42.460|1789952782.985|
|orchestrator/tests/test_hooks.py::test_bash_login_executor_recursion_precedes_sanctioned_allow|0|gw37|173|0|0.004|265|44.998|1789952785.523|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_builder_rejects_scope[K0]|0|gw37|258|0|0.019|267|45.002|1789952785.527|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_builder_rejects_scope[B4]|0|gw37|260|0|0.020|269|45.021|1789952785.546|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_builder_rejects_scope[no_projection]|0|gw37|262|0|0.018|271|45.041|1789952785.566|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_builder_rejects_scope[unbound_projection]|0|gw37|264|0|0.019|273|45.059|1789952785.584|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_bad_critic_before_receipt[duplicate]|0|gw37|266|0|0.024|275|45.078|1789952785.603|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_bad_critic_before_receipt[utf8]|0|gw37|268|0|0.022|277|45.102|1789952785.627|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_scope[run]|0|gw37|270|0|0.002|281|45.124|1789952785.649|
|orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_scope[ingest]|0|gw37|274|0|0.002|284|45.126|1789952785.651|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_reaches_campaign_under_applied_template|0|gw37|277|0|1.015|287|45.128|1789952785.653|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_cli_rejects_conflicting_modes[extra0-run-iteration]|0|gw37|280|0|0.002|290|46.143|1789952786.668|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_cli_rejects_conflicting_modes[extra4-coder-role]|0|gw37|284|0|0.002|291|46.145|1789952786.670|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_cli_rejects_conflicting_modes[extra5-b4-reflux-ablation]|0|gw37|285|0|0.002|292|46.147|1789952786.672|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_cli_rejects_conflicting_modes[extra6-allow-coder-derived-build]|0|gw37|286|0|0.002|293|46.149|1789952786.674|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_cli_rejects_conflicting_modes[extra7-isolate-worktree]|0|gw37|287|0|0.002|295|46.151|1789952786.676|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_rejects_non_stock_certified_source[False]|0|gw37|289|0|0.803|297|46.153|1789952786.678|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_control_reports_skipped_without_restore[None]|0|gw37|291|0|0.881|309|46.956|1789952787.481|
|orchestrator/tests/test_p3_s4_loop.py::test_default_cli_preserves_preimage_bytes|0|gw37|302|0|1.296|314|47.837|1789952788.362|
|orchestrator/tests/test_p3_s4_loop.py::test_perf_cli_rejects_partial_and_invalid_options[args1-must be supplied together]|0|gw37|306|0|0.002|326|49.133|1789952789.658|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_perf_cli_ingestion_exclusion[extra1]|0|gw37|318|0|0.003|327|49.135|1789952789.660|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_perf_cli_ingestion_exclusion[extra2]|0|gw37|319|0|0.003|328|49.138|1789952789.663|
|orchestrator/tests/test_p3_s4_loop.py::test_stock_perf_cli_ingestion_exclusion[extra3]|0|gw37|320|0|0.003|329|49.141|1789952789.666|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_slot_changes_identity_and_default_kwargs_stay_exact|0|gw37|321|0|2.777|330|49.144|1789952789.669|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_cli_invalid_combinations_rejected[args0]|0|gw37|322|0|0.002|359|51.921|1789952792.446|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_string_preflight_rejection_uses_wal_and_rc0|0|gw37|352|0|2.784|360|51.923|1789952792.448|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_rejection_sidecar_mutant_m20|0|gw37|353|0|0.008|428|54.707|1789952795.232|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_waits_for_peer_after_exception[xdist_node_collection_finished-receipt]|0|gw37|422|0|0.059|429|54.715|1789952795.240|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_waits_for_peer_after_exception[xdist_node_collection_finished-oracle]|0|gw37|423|0|0.059|435|54.774|1789952795.299|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_returns_only_after_both_complete[xdist_node_collection_finished-receipt]|0|gw37|428|0|0.058|451|54.833|1789952795.358|
|orchestrator/tests/test_real_repo_serialization.py::test_early_memo_success_checks_shared_deadline_after_io|0|gw37|444|0|0.158|459|54.891|1789952795.416|
|orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_rejects_synthetic_chain_artifacts[both]|0|gw37|453|0|0.391|464|55.049|1789952795.574|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_unactivated_chain_hit_is_invalid|0|gw37|458|0|202.978|466|55.440|1789952795.965|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw37|460|0|151.091|4146|258.418|1789952998.943|

shard-0 worker gw5 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw5|5|0|238.951|28|0.000|1789952740.522|
|orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases|0|gw5|49|1|0.000|4144|238.951|1789952979.473|

T-2724

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity|0|gw46|455|0|0.005|462|54.911|1789952795.443|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt|0|gw46|456|0|203.140|463|54.916|1789952795.448|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v1_gate_does_not_delegate_with_active_v2|0|gw35|459|0|208.090|467|55.200|1789952796.124|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw34|462|0|205.871|469|55.278|1789952796.193|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw46|457|0|47.045|4145|258.056|1789952998.588|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw37|460|0|151.091|4146|258.418|1789952998.943|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rejects_late_hit_file|0|gw34|463|0|43.699|4147|261.149|1789953002.064|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[changed]|0|gw35|461|0|38.043|4148|263.290|1789953004.214|

固定した旧 L 候補 (全 parametrize)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]|0|gw9|9|0|214.556|3|0.000|1789952740.522|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]|0|gw8|8|0|214.611|11|0.000|1789952740.522|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]|0|gw6|6|0|220.137|13|0.000|1789952740.522|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw5|5|0|238.951|28|0.000|1789952740.522|

## 02-B (B)

valid=True; errors=[]; 測定台帳 hash=27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f; 集計時の worktree の台帳 hash=27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f; 警告=None

投入=2026-09-21T10:22:18+0900; 完了=2026-09-21T10:43:42+0900; leader=1; load1=9.14

W_max=334.439; argmax=[0]

|shard|W|O|L|O−L|F|pre|post|O worker|L worker|P_L|node|job ID|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|334.439|261.287|246.282|15.005|73.152|63.029|10.066|gw2|gw40|0.002|bnode021|0:14766.nqsv|
|1|216.164|150.391|139.244|11.147|65.773|62.083|3.582|gw0|gw2|-0.000|bnode013|0:14765.nqsv|
|2|191.105|124.509|124.508|0.001|66.596|63.185|3.324|gw1|gw1|0.001|bnode023|0:14767.nqsv|

|shard|selected count|selected sha256|台帳予測負荷|未登録|worker/item 件数|
|---|---|---|---|---|---|
|0|4149|e34aab9e3433a98da7dbd0875a6f80a509ecdd523729dc598501a6fa7d295410|6877.901|132|gw8:2, gw5:2, gw6:2, gw22:183, gw29:4, gw12:2, gw47:14, gw32:8, gw24:4, gw39:325, gw2:10, gw4:2, gw23:167, gw25:6, gw18:2, gw15:2, gw45:233, gw31:268, gw35:185, gw41:2, gw44:2, gw40:2, gw13:2, gw16:2, gw33:12, gw30:249, gw14:2, gw20:137, gw9:2, gw27:174, gw28:4, gw11:2, gw7:2, gw1:16, gw42:265, gw26:105, gw17:2, gw21:29, gw10:2, gw46:178, gw36:174, gw34:91, gw37:137, gw43:14, gw0:383, gw19:195, gw38:276, gw3:267|
|1|10886|f1c047cdefbb05d800fc15e739e9afbdd618252ed4e492caffac375b4c51a0b8|4677.000|86|gw24:287, gw4:252, gw38:255, gw9:239, gw21:299, gw3:2, gw26:254, gw45:241, gw32:292, gw17:250, gw14:173, gw18:250, gw12:228, gw10:257, gw11:263, gw5:232, gw8:303, gw23:292, gw22:257, gw25:253, gw34:249, gw41:249, gw13:245, gw16:248, gw40:259, gw6:221, gw15:249, gw33:242, gw7:172, gw46:249, gw29:322, gw37:245, gw36:237, gw19:161, gw20:216, gw27:288, gw39:251, gw42:237, gw47:278, gw28:252, gw44:220, gw31:252, gw43:155, gw35:233, gw30:223, gw0:50, gw1:2, gw2:2|
|2|11773|283ea597eaac0c3fe479e19bce43deeb8acf1647dbc98aba5892373fe783ee5a|4676.998|2|gw11:263, gw13:241, gw18:234, gw7:234, gw21:260, gw27:249, gw26:259, gw29:260, gw31:204, gw36:259, gw34:264, gw35:269, gw39:263, gw41:262, gw47:262, gw5:254, gw25:258, gw43:269, gw2:176, gw4:237, gw17:263, gw15:244, gw9:232, gw6:240, gw14:179, gw8:232, gw16:257, gw44:236, gw38:262, gw20:258, gw28:263, gw23:247, gw24:249, gw30:252, gw33:258, gw45:264, gw10:238, gw1:2, gw42:263, gw40:235, gw19:245, gw32:250, gw0:424, gw22:269, gw46:243, gw37:239, gw3:187, gw12:265|

|shard|L nodeid|L rank|L partner|O_L|
|---|---|---|---|---|
|0|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|40|0|246.284|
|1|orchestrator/tests/test_p3_b4_raw_record_producer.py::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings|2|0|139.244|
|2|orchestrator/tests/test_p3_b4_producer_auth_experiment.py::test_case_failure_records_aborted_and_remaining_cases_continue|1|0|124.509|

shard-0 worker gw2 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain|0|gw2|2|0|0.000|10|0.000|1789954238.130|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points|0|gw2|2|0|0.000|11|0.000|1789954238.130|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_repository_tip_binds_current_decider_version_without_activation|0|gw2|2|0|0.000|12|0.000|1789954238.130|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates|0|gw2|2|0|0.000|13|0.000|1789954238.130|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan|0|gw2|2|0|0.000|47|0.000|1789954238.130|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception0]|0|gw2|92|1|0.001|49|0.000|1789954238.130|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception1]|0|gw2|93|1|0.001|51|0.001|1789954238.131|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw2|96|0|237.047|53|0.002|1789954238.132|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|0|gw2|98|0|20.222|4144|237.049|1789954475.179|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|0|gw2|100|0|4.014|4148|257.271|1789954495.401|

shard-0 worker gw40 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw40|40|0|246.282|24|0.000|1789954238.131|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_loader_schema_unicode_and_top_level_fail_soft[{"schema_version":1,"unit":"seconds","nodeid_count":1,"duration_seconds_by_nodeid":{"node":11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111}}]|0|gw40|84|1|0.002|4147|246.282|1789954484.413|

T-2724

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rejects_late_hit_file|0|gw41|41|0|242.285|22|0.000|1789954238.131|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v1_gate_does_not_delegate_with_active_v2|0|gw44|44|0|239.358|23|0.000|1789954238.131|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw40|40|0|246.282|24|0.000|1789954238.131|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw16|16|0|237.055|26|0.000|1789954238.130|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt|0|gw14|14|0|233.980|29|0.000|1789954238.130|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[changed]|0|gw17|17|0|237.052|43|0.000|1789954238.130|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw2|96|0|237.047|53|0.002|1789954238.132|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity|0|gw45|2312|0|0.005|2346|149.677|1789954387.808|

固定した旧 L 候補 (全 parametrize)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]|0|gw8|8|0|206.088|0|0.000|1789954238.130|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]|0|gw6|6|0|211.619|2|0.000|1789954238.130|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw4|4|0|230.582|14|0.000|1789954238.130|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]|0|gw9|9|0|206.279|31|0.000|1789954238.130|

## 03-B (B)

valid=False; errors=['rc/copy_ok']; 測定台帳 hash=None; 集計時の worktree の台帳 hash=None; 警告=None

投入=2026-09-21T10:59:26+0900; 完了=2026-09-21T11:25:05+0900; leader=1; load1=16.85

W_max=None; argmax=None

|shard|W|O|L|O−L|F|pre|post|O worker|L worker|P_L|node|job ID|
|---|---|---|---|---|---|---|---|---|---|---|---|---|

|shard|selected count|selected sha256|台帳予測負荷|未登録|worker/item 件数|
|---|---|---|---|---|---|

|shard|L nodeid|L rank|L partner|O_L|
|---|---|---|---|---|

T-2724

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|

固定した旧 L 候補 (全 parametrize)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|

## 04-B (B)

valid=True; errors=[]; 測定台帳 hash=27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f; 集計時の worktree の台帳 hash=27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f; 警告=None

投入=2026-09-21T11:52:51+0900; 完了=2026-09-21T12:16:20+0900; leader=1; load1=13.65

W_max=310.663; argmax=[0]

|shard|W|O|L|O−L|F|pre|post|O worker|L worker|P_L|node|job ID|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|310.663|237.045|222.300|14.745|73.618|63.496|10.063|gw2|gw40|0.001|bnode015|0:14997.nqsv|
|1|218.557|151.021|138.445|12.576|67.536|63.847|3.580|gw0|gw2|-0.000|bnode004|0:14996.nqsv|
|2|195.168|129.152|129.152|0.000|66.016|62.584|3.309|gw1|gw1|0.000|bnode023|0:14998.nqsv|

|shard|selected count|selected sha256|台帳予測負荷|未登録|worker/item 件数|
|---|---|---|---|---|---|
|0|4149|e34aab9e3433a98da7dbd0875a6f80a509ecdd523729dc598501a6fa7d295410|6877.901|132|gw1:15, gw2:10, gw28:4, gw25:402, gw39:526, gw41:2, gw47:39, gw14:2, gw15:2, gw31:43, gw18:2, gw12:2, gw29:440, gw30:472, gw27:62, gw32:4, gw35:41, gw5:2, gw16:2, gw8:2, gw10:2, gw40:2, gw44:2, gw4:2, gw45:21, gw13:2, gw11:2, gw33:3, gw17:2, gw23:28, gw22:25, gw6:2, gw42:354, gw9:2, gw26:15, gw7:2, gw20:100, gw21:506, gw46:56, gw24:64, gw0:62, gw37:14, gw34:141, gw36:17, gw19:27, gw43:435, gw38:31, gw3:156|
|1|10886|f1c047cdefbb05d800fc15e739e9afbdd618252ed4e492caffac375b4c51a0b8|4677.000|86|gw17:314, gw32:181, gw25:258, gw15:252, gw33:246, gw21:339, gw24:249, gw6:249, gw18:247, gw14:151, gw11:241, gw40:260, gw38:251, gw5:245, gw13:235, gw10:248, gw45:220, gw9:283, gw7:233, gw23:251, gw16:223, gw26:248, gw34:256, gw22:257, gw41:258, gw8:219, gw3:2, gw4:201, gw12:243, gw39:260, gw37:248, gw27:281, gw29:193, gw46:242, gw19:262, gw20:321, gw36:313, gw47:305, gw42:227, gw31:236, gw44:253, gw43:247, gw28:177, gw35:253, gw30:154, gw0:50, gw1:2, gw2:2|
|2|11773|283ea597eaac0c3fe479e19bce43deeb8acf1647dbc98aba5892373fe783ee5a|4676.998|2|gw0:316, gw17:231, gw32:260, gw10:240, gw30:261, gw11:207, gw31:263, gw16:265, gw42:259, gw39:256, gw43:255, gw44:268, gw12:212, gw21:256, gw19:244, gw2:233, gw7:239, gw25:246, gw46:270, gw29:265, gw1:2, gw15:252, gw23:240, gw20:252, gw26:257, gw28:251, gw9:252, gw6:247, gw34:259, gw33:262, gw36:264, gw24:218, gw40:266, gw38:266, gw14:244, gw18:265, gw45:268, gw4:236, gw3:246, gw5:237, gw8:242, gw35:264, gw27:255, gw37:256, gw13:232, gw41:236, gw47:251, gw22:207|

|shard|L nodeid|L rank|L partner|O_L|
|---|---|---|---|---|
|0|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|40|0|222.301|
|1|orchestrator/tests/test_p3_b4_raw_record_producer.py::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings|2|0|138.445|
|2|orchestrator/tests/test_p3_b4_producer_auth_experiment.py::test_case_failure_records_aborted_and_remaining_cases_continue|1|0|129.152|

shard-0 worker gw2 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain|0|gw2|2|0|0.000|1|0.000|1789960318.232|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_batch_is_bounded_by_frozen_touch_points|0|gw2|2|0|0.000|3|0.000|1789960318.232|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_repository_tip_binds_current_decider_version_without_activation|0|gw2|2|0|0.000|4|0.000|1789960318.232|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates|0|gw2|2|0|0.000|5|0.000|1789960318.232|
|orchestrator/tests/test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan|0|gw2|2|0|0.000|47|0.000|1789960318.232|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception0]|0|gw2|92|1|0.001|49|0.000|1789960318.232|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception1]|0|gw2|93|1|0.001|51|0.001|1789960318.233|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw2|96|0|212.968|53|0.002|1789960318.234|
|orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e|0|gw2|98|0|20.208|4143|212.970|1789960531.202|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_output_snapshot_observes_git_visible_create_and_delete|0|gw2|100|0|3.867|4148|233.178|1789960551.410|

shard-0 worker gw40 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw40|40|0|222.300|28|0.000|1789960318.235|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_loader_schema_unicode_and_top_level_fail_soft[{"schema_version":1,"unit":"seconds","nodeid_count":1,"duration_seconds_by_nodeid":{"node":11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111}}]|0|gw40|84|1|0.002|4147|222.300|1789960540.535|

T-2724

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rejects_late_hit_file|0|gw41|41|0|218.618|8|0.000|1789960318.235|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt|0|gw14|14|0|210.579|10|0.000|1789960318.233|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw16|16|0|212.882|21|0.000|1789960318.233|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw40|40|0|222.300|28|0.000|1789960318.235|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v1_gate_does_not_delegate_with_active_v2|0|gw44|44|0|215.538|29|0.000|1789960318.235|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[changed]|0|gw17|17|0|213.535|35|0.000|1789960318.233|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw2|96|0|212.968|53|0.002|1789960318.234|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity|0|gw39|2312|0|0.005|2315|83.974|1789960402.209|

固定した旧 L 候補 (全 parametrize)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]|0|gw8|8|0|182.838|22|0.000|1789960318.233|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw4|4|0|207.694|30|0.000|1789960318.233|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]|0|gw6|6|0|188.753|38|0.000|1789960318.233|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]|0|gw9|9|0|183.343|40|0.000|1789960318.233|

## 05-A (A)

valid=True; errors=[]; 測定台帳 hash=1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a; 集計時の worktree の台帳 hash=1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a; 警告=None

投入=2026-09-21T12:19:14+0900; 完了=2026-09-21T12:39:51+0900; leader=1; load1=11.94

W_max=511.326; argmax=[0]

|shard|W|O|L|O−L|F|pre|post|O worker|L worker|P_L|node|job ID|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|511.326|437.928|231.272|206.656|73.398|62.758|10.027|gw1|gw5|-0.000|bnode026|0:15019.nqsv|
|1|251.621|184.636|149.138|35.498|66.985|63.284|3.600|gw0|gw2|0.001|bnode027|0:15020.nqsv|
|2|145.398|73.207|60.190|13.017|72.191|63.640|4.320|gw0|gw1|12.725|bnode015|0:15018.nqsv|

|shard|selected count|selected sha256|台帳予測負荷|未登録|worker/item 件数|
|---|---|---|---|---|---|
|0|4149|e34aab9e3433a98da7dbd0875a6f80a509ecdd523729dc598501a6fa7d295410|7749.524|367|gw1:28, gw5:2, gw9:2, gw28:7, gw20:73, gw10:2, gw24:4, gw18:3, gw30:263, gw19:214, gw12:2, gw31:241, gw4:2, gw25:4, gw16:185, gw7:2, gw8:2, gw32:4, gw11:2, gw21:46, gw13:2, gw36:26, gw17:69, gw22:93, gw23:3, gw27:4, gw40:300, gw41:41, gw2:152, gw37:82, gw6:2, gw39:403, gw38:52, gw26:16, gw46:35, gw14:284, gw44:78, gw42:5, gw0:227, gw15:270, gw29:40, gw34:285, gw35:187, gw43:11, gw45:210, gw33:7, gw47:18, gw3:159|
|1|10309|ac5ace0c052c2c25f2eaf02b6246b4cd72c62f32d8953a92c50d9586e53708f0|6350.295|866|gw6:218, gw9:201, gw15:210, gw12:204, gw19:198, gw20:257, gw26:208, gw30:151, gw32:241, gw4:2, gw36:267, gw34:136, gw38:305, gw33:266, gw22:212, gw8:217, gw5:207, gw3:2, gw13:256, gw7:212, gw16:246, gw11:270, gw14:113, gw18:276, gw21:256, gw23:263, gw29:205, gw28:312, gw35:267, gw39:248, gw10:207, gw17:337, gw25:200, gw37:350, gw27:269, gw24:231, gw40:341, gw31:171, gw43:219, gw45:286, gw41:236, gw46:314, gw44:220, gw42:191, gw47:257, gw0:50, gw1:2, gw2:2|
|2|12350|cbd722029024f0362c7b39fc1b1cc4c0f62ee265893d5b9d9fc60d63368403ba|6350.296|1353|gw17:246, gw22:250, gw15:235, gw7:222, gw18:275, gw38:273, gw8:237, gw32:279, gw35:269, gw34:247, gw39:253, gw45:239, gw10:228, gw14:218, gw6:208, gw13:249, gw26:251, gw25:271, gw24:308, gw44:240, gw2:196, gw23:239, gw4:222, gw5:229, gw28:272, gw19:334, gw29:289, gw11:277, gw40:257, gw31:249, gw37:273, gw41:236, gw0:390, gw9:223, gw33:388, gw42:282, gw46:228, gw16:233, gw27:338, gw3:222, gw20:234, gw30:220, gw12:247, gw36:295, gw21:317, gw1:183, gw47:216, gw43:263|

|shard|L nodeid|L rank|L partner|O_L|
|---|---|---|---|---|
|0|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|5|0|231.272|
|1|orchestrator/tests/test_p3_b4_raw_record_producer.py::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings|2|0|149.139|
|2|orchestrator/tests/test_dev_wave_wait.py::test_producer_waiter_kill_requires_later_check_only_receipt[sigkill]|1|0|72.915|

shard-0 worker gw1 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels|0|gw1|1|0|0.000|0|0.000|1789961203.598|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger|0|gw1|1|0|0.000|1|0.000|1789961203.598|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap|0|gw1|1|0|0.000|8|0.000|1789961203.598|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command|0|gw1|1|0|0.000|9|0.000|1789961203.598|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports|0|gw1|1|0|0.000|10|0.000|1789961203.598|
|orchestrator/tests/test_campaign_import_invariant.py::test_known_exception_ledger_is_unique_rationalized_and_commented|0|gw1|1|0|0.000|36|0.000|1789961203.598|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g2_overflowed_unit_sum_is_unknown_not_infinite_priority|0|gw1|92|1|0.002|37|0.000|1789961203.598|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g3_splitter_exactly_matches_loadgroup_scheduler[orchestrator/tests/test_plain.py::test_plain]|0|gw1|93|1|0.001|45|0.002|1789961203.600|
|orchestrator/tests/test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory|0|gw1|96|0|22.993|106|0.003|1789961203.601|
|orchestrator/tests/test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing|0|gw1|98|0|10.034|127|22.996|1789961226.594|
|orchestrator/tests/test_codex_reasoning_ab.py::test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run|0|gw1|99|0|9.356|143|33.030|1789961236.628|
|orchestrator/tests/test_s8b_floor_campaign.py::test_deterministic_artifacts_across_roots_and_subprocess_environments|0|gw1|116|0|5.674|171|42.386|1789961245.984|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v2_completed_driver_adapter_campaign_is_accepted_by_report|0|gw1|132|0|4.131|304|48.060|1789961251.658|
|orchestrator/tests/test_campaign.py::test_source_digest_same_value_source_redefine_changes_identity|0|gw1|164|0|0.250|332|52.191|1789961255.789|
|orchestrator/tests/test_p3_s4_loop.py::test_calibrated_perf_uses_p2_constants_and_exact_workload[write-heavy]|0|gw1|297|0|0.001|350|52.441|1789961256.039|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_cli_invalid_combinations_rejected[args2]|0|gw1|324|0|0.003|351|52.442|1789961256.040|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_stock_submission_precedes_campaign_exception|0|gw1|342|0|1.026|352|52.445|1789961256.043|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_sidecar_no_overwrite|0|gw1|343|0|0.002|356|53.471|1789961257.069|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_candidate_rejection_sidecar_rc3_m20[schema-schema]|0|gw1|344|0|0.003|357|53.473|1789961257.071|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_candidate_rejection_sidecar_rc3_m20[probe-probe-material]|0|gw1|348|0|0.007|358|53.476|1789961257.074|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_candidate_rejection_sidecar_rc3_m20[k2-k2-semantic]|0|gw1|349|0|0.097|360|53.483|1789961257.081|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_candidate_rejection_sidecar_rc3_m20[k2-schema-schema]|0|gw1|350|0|0.087|361|53.580|1789961257.178|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_string_preflight_rejection_uses_wal_and_rc0|0|gw1|352|0|2.401|362|53.667|1789961257.265|
|orchestrator/tests/test_p3_s4_loop.py::test_b5_rejection_sidecar_mutant_m20|0|gw1|353|0|0.008|466|56.068|1789961259.666|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_sort_condition_gate_precedes_run_campaign|0|gw1|354|0|0.006|468|56.076|1789961259.674|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_unactivated_chain_hit_is_invalid|0|gw1|458|0|191.661|469|56.082|1789961259.680|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw1|460|0|152.410|4144|247.743|1789961451.341|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[changed]|0|gw1|461|0|37.776|4148|400.153|1789961603.751|

shard-0 worker gw5 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw5|5|0|231.272|2|0.000|1789961203.598|
|orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases|0|gw5|49|1|0.000|4143|231.272|1789961434.870|

T-2724

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw47|457|0|204.059|467|56.113|1789961260.115|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw33|462|0|194.793|471|56.238|1789961260.280|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity|0|gw14|455|0|0.004|474|56.496|1789961260.095|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt|0|gw36|456|0|191.565|476|56.755|1789961260.354|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw1|460|0|152.410|4144|247.743|1789961451.341|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rejects_late_hit_file|0|gw33|463|0|42.935|4146|251.031|1789961455.073|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v1_gate_does_not_delegate_with_active_v2|0|gw47|459|0|40.317|4147|260.172|1789961464.174|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[changed]|0|gw1|461|0|37.776|4148|400.153|1789961603.751|

固定した旧 L 候補 (全 parametrize)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw5|5|0|231.272|2|0.000|1789961203.598|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]|0|gw9|9|0|206.758|3|0.000|1789961203.598|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]|0|gw8|8|0|206.864|20|0.000|1789961203.598|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]|0|gw6|6|0|212.416|39|0.000|1789961203.598|

## 06-A (A)

valid=True; errors=[]; 測定台帳 hash=1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a; 集計時の worktree の台帳 hash=1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a; 警告=None

投入=2026-09-21T12:42:13+0900; 完了=2026-09-21T13:04:28+0900; leader=1; load1=9.75

W_max=374.494; argmax=[0]

|shard|W|O|L|O−L|F|pre|post|O worker|L worker|P_L|node|job ID|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|374.494|299.598|226.247|73.351|74.896|64.372|10.032|gw33|gw5|-0.000|bnode015|0:15026.nqsv|
|1|251.765|185.365|148.008|37.357|66.400|62.673|3.597|gw0|gw2|0.000|bnode026|0:15027.nqsv|
|2|146.057|74.537|60.186|14.351|71.520|62.942|4.120|gw44|gw2|13.925|bnode029|0:15028.nqsv|

|shard|selected count|selected sha256|台帳予測負荷|未登録|worker/item 件数|
|---|---|---|---|---|---|
|0|4149|e34aab9e3433a98da7dbd0875a6f80a509ecdd523729dc598501a6fa7d295410|7749.524|367|gw1:448, gw2:14, gw32:681, gw36:52, gw38:12, gw41:20, gw7:2, gw19:79, gw30:10, gw6:2, gw4:2, gw8:2, gw9:2, gw31:127, gw27:329, gw5:2, gw20:207, gw11:2, gw12:2, gw26:21, gw28:3, gw23:25, gw24:604, gw37:87, gw17:4, gw39:45, gw10:2, gw22:3, gw25:103, gw46:42, gw13:2, gw18:159, gw40:98, gw21:30, gw16:17, gw14:29, gw0:62, gw35:13, gw15:3, gw44:181, gw34:20, gw42:5, gw29:4, gw47:36, gw43:413, gw45:38, gw33:12, gw3:93|
|1|10309|ac5ace0c052c2c25f2eaf02b6246b4cd72c62f32d8953a92c50d9586e53708f0|6350.295|866|gw18:187, gw17:289, gw23:311, gw4:2, gw34:217, gw37:275, gw7:175, gw3:2, gw5:125, gw40:404, gw15:223, gw13:214, gw8:210, gw32:171, gw26:223, gw22:146, gw27:307, gw30:124, gw12:209, gw25:222, gw16:311, gw33:220, gw14:287, gw11:209, gw19:217, gw21:217, gw31:216, gw20:270, gw10:206, gw28:262, gw24:309, gw6:139, gw9:220, gw39:356, gw36:203, gw29:281, gw38:338, gw35:231, gw44:273, gw45:241, gw41:249, gw43:223, gw46:196, gw42:263, gw47:282, gw0:50, gw1:2, gw2:2|
|2|12350|cbd722029024f0362c7b39fc1b1cc4c0f62ee265893d5b9d9fc60d63368403ba|6350.296|1353|gw24:244, gw23:275, gw26:246, gw5:222, gw33:378, gw6:208, gw28:314, gw39:250, gw14:224, gw42:324, gw8:223, gw10:219, gw12:245, gw11:239, gw18:216, gw15:223, gw21:253, gw13:261, gw3:228, gw1:197, gw2:201, gw7:223, gw44:231, gw25:260, gw47:250, gw30:343, gw31:230, gw40:239, gw38:250, gw9:227, gw0:407, gw37:264, gw41:275, gw17:280, gw20:232, gw22:276, gw4:230, gw46:232, gw19:257, gw27:331, gw34:243, gw35:322, gw43:274, gw16:241, gw36:299, gw29:242, gw32:276, gw45:226|

|shard|L nodeid|L rank|L partner|O_L|
|---|---|---|---|---|
|0|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|5|0|226.247|
|1|orchestrator/tests/test_p3_b4_raw_record_producer.py::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings|2|0|148.008|
|2|orchestrator/tests/test_dev_wave_wait.py::test_producer_waiter_kill_requires_later_check_only_receipt[sigterm]|2|0|74.111|

shard-0 worker gw33 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment|0|gw33|33|0|55.044|101|0.000|1789962623.771|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_loader_filters_only_invalid_entries|0|gw33|77|1|0.001|372|55.044|1789962678.815|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_require_sort_oracle_contract_accepts_only_running_contract|0|gw33|366|0|0.001|373|55.045|1789962678.816|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_sort_driver_forwards_producer_contract_to_run_campaign|0|gw33|367|0|0.001|374|55.046|1789962678.817|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_sort_oracle_contract_call_seams_are_keyword_only_default_none|0|gw33|368|0|0.001|375|55.047|1789962678.818|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_resolved_src_token_rejects_both_bindings|0|gw33|369|0|0.001|376|55.048|1789962678.819|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_run_campaign_forwards_one_sort_contract_to_resolver_and_evaluate|0|gw33|370|0|1.206|377|55.049|1789962678.820|
|orchestrator/tests/test_p3_s4_loop_sort.py::test_pipeline_forwards_one_sort_contract_to_resolver_and_selected_build_api[legacy]|0|gw33|371|0|0.265|406|56.255|1789962680.026|
|orchestrator/tests/test_real_repo_serialization.py::test_current_snapshot_reader_upgrades_for_same_process_candidate_fixture|0|gw33|400|0|0.399|425|56.520|1789962680.291|
|orchestrator/tests/test_real_repo_serialization.py::test_memo_barrier_waits_for_peer_after_exception[collection_finish-receipt]|0|gw33|420|0|0.058|464|56.919|1789962680.690|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw33|457|0|202.147|465|56.977|1789962680.748|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v1_gate_does_not_delegate_with_active_v2|0|gw33|459|0|40.473|4148|259.124|1789962882.895|

shard-0 worker gw5 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw5|5|0|226.247|20|0.000|1789962623.320|
|orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases|0|gw5|49|1|0.000|4144|226.247|1789962849.567|

T-2724

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity|0|gw35|455|0|0.004|462|56.920|1789962680.686|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt|0|gw35|456|0|189.982|463|56.924|1789962680.690|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw33|457|0|202.147|465|56.977|1789962680.748|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw37|460|0|191.992|468|57.452|1789962680.773|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[changed]|0|gw34|461|0|192.683|469|57.356|1789962681.127|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw37|462|0|38.868|4146|249.444|1789962872.765|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rejects_late_hit_file|0|gw34|463|0|43.808|4147|250.039|1789962873.810|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v1_gate_does_not_delegate_with_active_v2|0|gw33|459|0|40.473|4148|259.124|1789962882.895|

固定した旧 L 候補 (全 parametrize)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]|0|gw6|6|0|207.445|14|0.000|1789962623.320|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]|0|gw8|8|0|201.940|16|0.000|1789962623.320|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]|0|gw9|9|0|202.015|17|0.000|1789962623.320|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw5|5|0|226.247|20|0.000|1789962623.320|

## 07-B (B)

valid=True; errors=[]; 測定台帳 hash=27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f; 集計時の worktree の台帳 hash=27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f; 警告=None

投入=2026-09-21T13:07:13+0900; 完了=2026-09-21T13:31:17+0900; leader=0; load1=12.68

W_max=344.931; argmax=[0]

|shard|W|O|L|O−L|F|pre|post|O worker|L worker|P_L|node|job ID|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0|344.931|270.462|227.380|43.082|74.469|64.379|10.029|gw1|gw40|0.002|bnode015|0:15036.nqsv|
|1|218.885|151.477|139.331|12.146|67.408|63.714|3.581|gw0|gw2|0.001|bnode004|0:15035.nqsv|
|2|190.109|123.847|123.846|0.001|66.262|62.845|3.351|gw1|gw1|0.001|bnode019|0:15037.nqsv|

|shard|selected count|selected sha256|台帳予測負荷|未登録|worker/item 件数|
|---|---|---|---|---|---|
|0|4149|e34aab9e3433a98da7dbd0875a6f80a509ecdd523729dc598501a6fa7d295410|6877.901|132|gw1:11, gw2:15, gw20:71, gw30:429, gw13:2, gw15:2, gw29:4, gw39:72, gw32:129, gw11:2, gw42:17, gw16:2, gw9:2, gw26:225, gw24:151, gw6:2, gw5:2, gw18:2, gw14:2, gw41:2, gw28:101, gw40:2, gw12:2, gw21:31, gw35:392, gw4:2, gw46:25, gw44:2, gw25:123, gw7:2, gw45:256, gw27:165, gw10:2, gw8:2, gw47:55, gw31:85, gw17:2, gw33:365, gw22:32, gw23:218, gw43:6, gw37:124, gw34:70, gw36:163, gw0:63, gw19:89, gw38:112, gw3:514|
|1|10886|f1c047cdefbb05d800fc15e739e9afbdd618252ed4e492caffac375b4c51a0b8|4677.000|86|gw11:155, gw14:258, gw17:229, gw7:235, gw15:263, gw23:294, gw3:2, gw24:235, gw25:264, gw34:245, gw38:263, gw40:249, gw5:173, gw32:301, gw6:238, gw16:283, gw18:280, gw10:268, gw9:248, gw13:160, gw22:143, gw26:278, gw33:255, gw41:315, gw21:271, gw12:262, gw4:242, gw8:282, gw45:244, gw19:249, gw39:250, gw20:226, gw37:256, gw36:243, gw46:300, gw27:179, gw29:242, gw42:249, gw47:253, gw28:258, gw35:224, gw43:252, gw31:238, gw44:268, gw0:50, gw30:210, gw1:2, gw2:2|
|2|11773|283ea597eaac0c3fe479e19bce43deeb8acf1647dbc98aba5892373fe783ee5a|4676.998|2|gw41:217, gw31:267, gw30:252, gw32:264, gw34:263, gw40:264, gw37:259, gw0:423, gw43:271, gw44:252, gw17:230, gw18:253, gw11:257, gw42:196, gw2:224, gw5:243, gw6:246, gw7:236, gw10:239, gw4:224, gw1:2, gw8:236, gw3:243, gw15:247, gw9:249, gw26:257, gw23:153, gw16:251, gw29:262, gw24:253, gw19:259, gw28:254, gw36:261, gw20:251, gw22:196, gw35:261, gw25:261, gw14:255, gw33:269, gw21:244, gw39:252, gw45:245, gw46:245, gw13:244, gw27:273, gw38:256, gw47:258, gw12:256|

|shard|L nodeid|L rank|L partner|O_L|
|---|---|---|---|---|
|0|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|40|0|227.382|
|1|orchestrator/tests/test_p3_b4_raw_record_producer.py::test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings|2|0|139.332|
|2|orchestrator/tests/test_p3_b4_producer_auth_experiment.py::test_case_failure_records_aborted_and_remaining_cases_continue|1|0|123.847|

shard-0 worker gw1 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels|0|gw1|1|0|0.000|0|0.000|1789964779.375|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger|0|gw1|1|0|0.000|1|0.000|1789964779.375|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap|0|gw1|1|0|0.000|12|0.000|1789964779.375|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command|0|gw1|1|0|0.000|13|0.000|1789964779.375|
|orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports|0|gw1|1|0|0.000|14|0.000|1789964779.375|
|orchestrator/tests/test_campaign_import_invariant.py::test_known_exception_ledger_is_unique_rationalized_and_commented|0|gw1|1|0|0.000|47|0.000|1789964779.375|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception2]|0|gw1|94|1|0.001|50|0.000|1789964779.375|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_ledger_nodeid_path_failures_are_unknown[exception3]|0|gw1|95|1|0.001|52|0.001|1789964779.376|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw1|96|0|217.982|54|0.002|1789964779.377|
|orchestrator/tests/test_codex_reasoning_ab.py::test_schedule_authenticated_bytes_accept_static[replay]|0|gw1|99|0|31.060|4146|217.984|1789964997.359|
|orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed|0|gw1|101|0|21.417|4148|249.044|1789965028.419|

shard-0 worker gw40 全 item (JUnit 順)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw40|40|0|227.380|28|0.000|1789964779.376|
|orchestrator/tests/test_acceptance_schedule_order.py::test_g1_loader_schema_unicode_and_top_level_fail_soft[{"schema_version":1,"unit":"seconds","nodeid_count":1,"duration_seconds_by_nodeid":{"node":11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111}}]|0|gw40|84|1|0.002|4147|227.380|1789965006.756|

T-2724

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_preserves_nonlayer2_receipt_refusal|0|gw16|16|0|217.178|18|0.000|1789964779.375|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt|0|gw14|14|0|214.865|25|0.000|1789964779.375|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rejects_late_hit_file|0|gw41|41|0|223.601|26|0.000|1789964779.376|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal|0|gw40|40|0|227.380|28|0.000|1789964779.376|
|orchestrator/tests/test_s8b_oracle_driver.py::test_v1_gate_does_not_delegate_with_active_v2|0|gw44|44|0|220.394|34|0.000|1789964779.376|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[changed]|0|gw17|17|0|218.358|43|0.000|1789964779.375|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_delegated_campaign_start_rechecks_receipt[missing]|0|gw1|96|0|217.982|54|0.002|1789964779.377|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity|0|gw26|2312|0|0.004|2311|103.592|1789964882.967|

固定した旧 L 候補 (全 parametrize)

|nodeid|shard|worker|rank|partner|time|junit_order|estimated_start_offset_s|estimated_start_epoch_s|
|---|---|---|---|---|---|---|---|---|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[unknownness-layer2-holdout.unknownness_layer2]|0|gw9|9|0|185.917|19|0.000|1789964779.375|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[known-artifact-known_axes.artifact_bytes]|0|gw6|6|0|192.268|22|0.000|1789964779.375|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]|0|gw4|4|0|210.759|32|0.000|1789964779.375|
|orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[holdout-artifact-holdout.artifact_bytes]|0|gw8|8|0|185.680|40|0.000|1789964779.375|

## 赤

条件別赤走数: {'A': 0, 'B': 1}

全赤の testcase 本文・child log・分類は analysis.json の runs に保存。

## 参考値 (判定に使わない)

|量|秒|出所|
|---|---|---|
|model 差|19.500|T-2817 §5 (a): 未収載333 node 全部更新の固定所要 model|
|O_max−L 中央値|62.700|T-2817: 21 session の O_max − L 中央値|
|Job B|65.000|T-2817 Job B|

## 限界

投入台帳は launcher が追記専用で扱う通常ファイル。台帳自身の改竄・削除（RUN と同時の削除を含む）や外部の同時変更は防げない。追記後の異常終了は自動修復せず拒否する。

別 tree / node / page cache の差は残る。入力 1 走の190秒群・40秒群がBの順位を決める。
copy 配置・builder/waiter の因果や役割は所要だけでは断定しない。
