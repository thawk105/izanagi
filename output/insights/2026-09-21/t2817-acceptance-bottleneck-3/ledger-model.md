固定所要 list-scheduling の model 値であり実 wall の予測ではない。D2107 の refresh 入力でも採用案でもない

| 案 | O_max_model | L | O_max_model − L | L worker 占有 |
| --- | --- | --- | --- | --- |
| a_current_ledger | 253.264000 | 233.739000 | 19.525000 | 233.739000 |
| b_missing_with_junit_medians | 233.739000 | 233.739000 | 0.000000 | 233.739000 |

(a) − (b) = 19.525000 秒 (model)。rank は 0 起点。

## a_current_ledger
既定 cost = 9.600000

maximum_worker: worker 42, occupancy=253.264000

| rank | scope | cost | 所要 | start | end | nodes |
| --- | --- | --- | --- | --- | --- | --- |
| 42 | orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e | 35.0 | 36.867 | 0.0 | 36.867 | ['orchestrator/tests/test_s8b_floor_campaign.py::test_real_seal_protocol_to_floor_official_core_e2e'] |
| 120 | orchestrator/tests/test_p3_s4_loop.py::test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty | 12.0 | 11.698 | 36.867 | 48.565 | ['orchestrator/tests/test_p3_s4_loop.py::test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty'] |
| 135 | orchestrator/tests/test_s8b_oracle_driver.py::test_v2_store_hash_mismatch_is_refused | 11.0 | 3.739 | 48.565 | 52.303999999999995 | ['orchestrator/tests/test_s8b_oracle_driver.py::test_v2_store_hash_mismatch_is_refused'] |
| 144 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_cardinality_infeasible_fails_closed | 9.6 | 0.006 | 52.303999999999995 | 52.309999999999995 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_cardinality_infeasible_fails_closed'] |
| 145 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_collection_is_worker_count_independent | 9.6 | 0.011 | 52.309999999999995 | 52.321 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_collection_is_worker_count_independent'] |
| 146 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_holds_shard_selection_and_real_repo_suffix_survive | 9.6 | 0.007 | 52.321 | 52.327999999999996 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_holds_shard_selection_and_real_repo_suffix_survive'] |
| 147 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[0] | 9.6 | 0.005 | 52.327999999999996 | 52.333 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[0]'] |
| 148 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[] | 9.6 | 0.005 | 52.333 | 52.338 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[]'] |
| 149 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[off] | 9.6 | 0.006 | 52.338 | 52.344 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[off]'] |
| 150 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[t2766-min-cost-partners] | 9.6 | 0.006 | 52.344 | 52.35 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_legacy_env_cannot_disable_pairing_or_change_item_state[t2766-min-cost-partners]'] |
| 151 | orchestrator/tests/test_acceptance_schedule_order.py::test_g12_live_junit_witness_includes_skips_and_execution_worker | 9.6 | 1.081 | 52.35 | 53.431000000000004 | ['orchestrator/tests/test_acceptance_schedule_order.py::test_g12_live_junit_witness_includes_skips_and_execution_worker'] |
| 161 | orchestrator/tests/test_campaign.py::test_source_digest_toplevel_macro_directives_change_identity | 9.6 | 0.25 | 53.431000000000004 | 53.681000000000004 | ['orchestrator/tests/test_campaign.py::test_source_digest_toplevel_macro_directives_change_identity'] |
| 162 | orchestrator/tests/test_campaign.py::test_source_digest_toplevel_trace_directives_change_identity | 9.6 | 0.445 | 53.681000000000004 | 54.126000000000005 | ['orchestrator/tests/test_campaign.py::test_source_digest_toplevel_trace_directives_change_identity'] |
| 175 | orchestrator/tests/test_p3_s4_loop.py::test_agent_critic_fenced_only_rejected[```] | 9.6 | 0.003 | 54.126000000000005 | 54.129000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_critic_fenced_only_rejected[```]'] |
| 177 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_duplicate[False] | 9.6 | 0.004 | 54.129000000000005 | 54.133 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_duplicate[False]'] |
| 179 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[campaign-digest-critic-digest_sha256] | 9.6 | 0.003 | 54.133 | 54.136 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[campaign-digest-critic-digest_sha256]'] |
| 181 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[critic-duplicate-critic-exactly once] | 9.6 | 0.003 | 54.136 | 54.139 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[critic-duplicate-critic-exactly once]'] |
| 182 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[critic-missing-critic-exactly once] | 9.6 | 0.003 | 54.139 | 54.142 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[critic-missing-critic-exactly once]'] |
| 183 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[digest-critic-digest_sha256] | 9.6 | 0.003 | 54.142 | 54.145 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[digest-critic-digest_sha256]'] |
| 184 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[digest-missing-critic---agent-digest] | 9.6 | 0.003 | 54.145 | 54.148 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[digest-missing-critic---agent-digest]'] |
| 185 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[empty-wal-planner-empty] | 9.6 | 0.003 | 54.148 | 54.151 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[empty-wal-planner-empty]'] |
| 186 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[env-planner-env_tag] | 9.6 | 0.003 | 54.151 | 54.154 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[env-planner-env_tag]'] |
| 187 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[input-array-planner-object] | 9.6 | 0.003 | 54.154 | 54.157000000000004 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[input-array-planner-object]'] |
| 188 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[input-missing-planner-input missing] | 9.6 | 0.003 | 54.157000000000004 | 54.160000000000004 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[input-missing-planner-input missing]'] |
| 189 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[knowledge-coder-knowledge_manifest_sha256] | 9.6 | 0.097 | 54.160000000000004 | 54.257000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[knowledge-coder-knowledge_manifest_sha256]'] |
| 196 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[ref-planner-WAL ref] | 9.6 | 0.003 | 54.257000000000005 | 54.260000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[ref-planner-WAL ref]'] |
| 197 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[stage-key-planner-mismatch] | 9.6 | 0.003 | 54.260000000000005 | 54.263000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[stage-key-planner-mismatch]'] |
| 198 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[variant-critic-variant absent] | 9.6 | 0.003 | 54.263000000000005 | 54.266000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[variant-critic-variant absent]'] |
| 199 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[variant-missing-critic---agent-variant] | 9.6 | 0.003 | 54.266000000000005 | 54.269000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_invalid_bindings[variant-missing-critic---agent-variant]'] |
| 200 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra0] | 9.6 | 0.003 | 54.269000000000005 | 54.272000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra0]'] |
| 201 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra10] | 9.6 | 0.003 | 54.272000000000006 | 54.275000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra10]'] |
| 202 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra11] | 9.6 | 0.003 | 54.275000000000006 | 54.278000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra11]'] |
| 203 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra12] | 9.6 | 0.003 | 54.278000000000006 | 54.281000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra12]'] |
| 204 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra13] | 9.6 | 0.003 | 54.281000000000006 | 54.284000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra13]'] |
| 205 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra14] | 9.6 | 0.003 | 54.284000000000006 | 54.287000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra14]'] |
| 206 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra15] | 9.6 | 0.003 | 54.287000000000006 | 54.290000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra15]'] |
| 207 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra16] | 9.6 | 0.003 | 54.290000000000006 | 54.293000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra16]'] |
| 208 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra17] | 9.6 | 0.003 | 54.293000000000006 | 54.29600000000001 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra17]'] |
| 209 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra18] | 9.6 | 0.003 | 54.29600000000001 | 54.29900000000001 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra18]'] |
| 210 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra19] | 9.6 | 0.003 | 54.29900000000001 | 54.30200000000001 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra19]'] |
| 212 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra2] | 9.6 | 0.003 | 54.30200000000001 | 54.30500000000001 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra2]'] |
| 214 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra4] | 9.6 | 0.003 | 54.30500000000001 | 54.30800000000001 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra4]'] |
| 216 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra6] | 9.6 | 0.003 | 54.30800000000001 | 54.31100000000001 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra6]'] |
| 218 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra8] | 9.6 | 0.003 | 54.31100000000001 | 54.31400000000001 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_rejects_evaluation_options[extra8]'] |
| 220 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_role_file[coder] | 9.6 | 0.099 | 54.31400000000001 | 54.413000000000004 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_role_file[coder]'] |
| 224 | orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_uncommitted_variant[critic] | 9.6 | 0.004 | 54.413000000000004 | 54.417 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_ingest_uncommitted_variant[critic]'] |
| 226 | orchestrator/tests/test_p3_s4_loop.py::test_agent_input_ast_isolation_and_mutant[_prepare_knowledge_campaign] | 9.6 | 0.082 | 54.417 | 54.499 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_input_ast_isolation_and_mutant[_prepare_knowledge_campaign]'] |
| 232 | orchestrator/tests/test_p3_s4_loop.py::test_agent_live_append_failure_propagates | 9.6 | 0.002 | 54.499 | 54.501000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_live_append_failure_propagates'] |
| 233 | orchestrator/tests/test_p3_s4_loop.py::test_agent_live_main[False-False-False] | 9.6 | 0.464 | 54.501000000000005 | 54.965 | ['orchestrator/tests/test_p3_s4_loop.py::test_agent_live_main[False-False-False]'] |
| 258 | orchestrator/tests/test_p3_s4_loop.py::test_default_cli_preserves_preimage_bytes | 9.6 | 1.577 | 54.965 | 56.542 | ['orchestrator/tests/test_p3_s4_loop.py::test_default_cli_preserves_preimage_bytes'] |
| 283 | orchestrator/tests/test_p3_s4_loop.py::test_stock_control_rejects_non_stock_certified_source[True] | 9.6 | 1.134 | 56.542 | 57.676 | ['orchestrator/tests/test_p3_s4_loop.py::test_stock_control_rejects_non_stock_certified_source[True]'] |
| 306 | orchestrator/tests/test_p3_s4_loop.py::test_t2783_builder_rejects_scope[wrong_projection] | 9.6 | 0.017 | 57.676 | 57.693000000000005 | ['orchestrator/tests/test_p3_s4_loop.py::test_t2783_builder_rejects_scope[wrong_projection]'] |
| 309 | orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_bad_critic_before_receipt[fenced] | 9.6 | 0.021 | 57.693000000000005 | 57.714000000000006 | ['orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_bad_critic_before_receipt[fenced]'] |
| 311 | orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_bad_critic_before_receipt[utf8] | 9.6 | 0.022 | 57.714000000000006 | 57.736000000000004 | ['orchestrator/tests/test_p3_s4_loop.py::test_t2783_cli_rejects_bad_critic_before_receipt[utf8]'] |
| 321 | orchestrator/tests/test_p3_s4_loop_sort.py::test_b4_sort_certified_receipt_advances_through_shared_gate | 9.6 | 0.528 | 57.736000000000004 | 58.264 | ['orchestrator/tests/test_p3_s4_loop_sort.py::test_b4_sort_certified_receipt_advances_through_shared_gate'] |
| 357 | orchestrator/tests/test_real_repo_serialization.py::test_early_memo_publication_wait_is_explicit_bounded_and_fail_closed | 9.6 | 0.023 | 58.264 | 58.287000000000006 | ['orchestrator/tests/test_real_repo_serialization.py::test_early_memo_publication_wait_is_explicit_bounded_and_fail_closed'] |
| 360 | orchestrator/tests/test_real_repo_serialization.py::test_early_memo_success_checks_shared_deadline_after_io | 9.6 | 0.161 | 58.287000000000006 | 58.44800000000001 | ['orchestrator/tests/test_real_repo_serialization.py::test_early_memo_success_checks_shared_deadline_after_io'] |
| 395 | orchestrator/tests/test_real_repo_serialization.py::test_real_repo_closure_mutations[parent-key-uses-worktree-root] | 9.6 | 0.024 | 58.44800000000001 | 58.47200000000001 | ['orchestrator/tests/test_real_repo_serialization.py::test_real_repo_closure_mutations[parent-key-uses-worktree-root]'] |
| 404 | orchestrator/tests/test_real_repo_serialization.py::test_real_repo_gate_timeout_closes_fds[gate-timeout] | 9.6 | 0.273 | 58.47200000000001 | 58.74500000000001 | ['orchestrator/tests/test_real_repo_serialization.py::test_real_repo_gate_timeout_closes_fds[gate-timeout]'] |
| 410 | orchestrator/tests/test_real_repo_serialization.py::test_real_repo_writer_drains_overlapping_reader_stream[common] | 9.6 | 0.607 | 58.74500000000001 | 59.35200000000001 | ['orchestrator/tests/test_real_repo_serialization.py::test_real_repo_writer_drains_overlapping_reader_stream[common]'] |
| 419 | orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_rejects_synthetic_chain_artifacts[candidate] | 9.6 | 0.388 | 59.35200000000001 | 59.74000000000001 | ['orchestrator/tests/test_s8b_floor_campaign.py::test_clean_scan_rejects_synthetic_chain_artifacts[candidate]'] |
| 424 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt | 9.6 | 193.524 | 59.74000000000001 | 253.264 | ['orchestrator/tests/test_s8b_oracle_driver.py::test_t080_active_v2_delegation_accepts_full_receipt'] |

L_worker: worker 5, occupancy=233.739000

| rank | scope | cost | 所要 | start | end | nodes |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 240.0 | 233.739 | 0.0 | 233.739 | ['orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]'] |

## b_missing_with_junit_medians
既定 cost = 11.000000

maximum_worker: worker 5, occupancy=233.739000

| rank | scope | cost | 所要 | start | end | nodes |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 240.0 | 233.739 | 0.0 | 233.739 | ['orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]'] |

L_worker: worker 5, occupancy=233.739000

| rank | scope | cost | 所要 | start | end | nodes |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current] | 240.0 | 233.739 | 0.0 | 233.739 | ['orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]'] |

## 限界

- 元 collection index は report に無く未再現。selected の保存順を unit index とし、同値はその index 順。
- real-repo suffix 除去は author 時 conftest registry の literal snapshot。将来の registry 変更は追随しない。
- 動的 xdist の先読み・共有 base 相互作用・setup 重複は再現しない。指定の空き worker への list scheduling。
- 同時に空いた worker は番号順。L が同値なら queue 上の最初を表示。
- 所要は両案で固定。JUnit と ledger の両方に無い node は (a) の既定 cost を共用。
- (b) 未収載のうち JUnit 中央値なしは未補完: 1 node

JUnit 未対応 testcase: 279
