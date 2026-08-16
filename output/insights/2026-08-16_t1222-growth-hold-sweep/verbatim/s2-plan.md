## 総括

- 静的全件走査の母数は top-level test 8,018 件、既存 2 台帳の和集合外は 7,941 件。そのうち成長比例は 31 family・230 function node だった。
- 登録推奨は 74 件: `test_check_docs.py` 3、`test_codex_agents.py` 21、`test_dev_waves_checker.py` 10、`test_dev_waves_integration.py` 40。
- 上記 74 件は同じ防壁を標準 land / wave checker / static-check が既定実行するため D451 を満たし、4 file とも standalone 自己読込がない。
- 148 件は比例自体は真だが、同じ防壁の独立した既定走行を file:line で確定できず、D451 により登録しない。
- `test_s8b_floor_campaign.py` の 2 件は比例だが、同 file を `spec_from_file_location` で再読込する正規 consumer があるため guard binding 不可で登録しない。
- T-080 stub-free E2E 6 function（展開後 11 node）は比例だが、既に `IZANAGI_T080_E2E=1` 必須の既定 skip なので追加登録しない。
- P1 は **refuted**。ratified-verify は固定量だが、silo 2 件中 1 件と copytree 群は親が間接経路・構造比例を見落としている。
- P2 は **refuted**。D451 の結論は正しいが、比例 node は名指し 1 件でなく session fixture の consumer 3 件すべて。
- P3 は **real（強化）**。`test_real_repo_clean` だけでなく、実 `check_docs.py` を起動する 3 件すべてが登録可能。
- P4 は **real**。未名指し候補が本体であり、特に 70-node calibration copy/scan、40-node dev-wave integration、23-node T126 群が大きい。

## 判定基準

D335 は現時点の秒数ではなく構造で判定する。正本は `docs/decisions.md:14957-14979`、特に「file 数・台帳やアーカイブ量への比例」と「個別秒数でなく構造で塞ぐ」が `:14959-14974` にある。

D451 は `docs/decisions.md:18866-18886`。以下の記号を使う。

- `R`: 登録。D451 の独立した既定経路あり、guard 可、pin 閉包確認済み。
- `N`: 比例は真だが D451 不成立。登録しない。
- `G`: guard binding 不可。登録しない。
- `S`: 既に既定 skip。追加登録しない。

## 全件走査

### 実際に使った検索式と全件数

`head` の出力をゼロ件根拠には使っていない。位置表示を絞る前に、次の全件数を取った。

```text
rg --files orchestrator/tests -g '*.py' | wc -l
# 226

rg -n --glob '*.py' '(?:\.glob|\.rglob|\.iterdir)\s*\(|os\.(?:walk|scandir)\s*\(' orchestrator/tests | wc -l
# 266

rg -n --glob '*.py' '(?:shutil\.)?(?:copytree|copy2)\s*\(|distutils(?:\.|\s+import)' orchestrator/tests | wc -l
# 99

rg -n --glob '*.py' '(?:shutil\.)?copytree\s*\(' orchestrator/tests | wc -l
# 34

rg -n --glob '*.py' "(?:[\"']git[\"']|[\"'](?:clone|rev-list|log|ls-files|ls-tree|status|grep)[\"'])" orchestrator/tests | wc -l
# 1589

rg -n --glob '*.py' '\b(?:enumerate_repository_files|search_repository|holdout_conjunction_hits|repository_scan)\b' orchestrator/tests | wc -l
# 78

rg -n --glob '*.py' '(?:check_docs|check_ai_provenance)\.py' orchestrator/tests | wc -l
# 154

rg -n --glob '*.py' '\b(?:ROOT|_ROOT|REPO|_REPO|REAL_REPO|REAL_ROOT|REPO_ROOT|_REPOSITORY_ROOT)\b' orchestrator/tests | wc -l
# 1390

rg -n --glob '*.py' '(?:read_text|read_bytes|open)\s*\(' orchestrator/tests | wc -l
# 2753

rg -n --glob '*.py' '(?:subprocess\.(?:run|call|Popen|check_output)|_git\(|_run_git\()' orchestrator/tests | wc -l
# 2328

rg -n --glob '*.py' '(?:@pytest\.mark\.parametrize|pytest\.parametrize)' orchestrator/tests | wc -l
# 998

rg -n --glob '*.py' '(?:pytest\.fixture|@pytest\.fixture)' orchestrator/tests | wc -l
# 50

rg -n --glob '*.py' '(?:spec_from_file_location|runpy\.|run_path\(|run_module\()' orchestrator/tests | wc -l
# 70
```

AST で top-level `test_*`、両台帳、fixture 依存、同 module helper call を閉包化した結果は次のとおり。

| 集合 | 件数 |
|---|---:|
| `test_*.py` | 209 file |
| top-level test function | 8,018 |
| `REAL_REPO_SERIAL_NODES` | 66 |
| `GROWTH_TEST_HOLDS` | 56 |
| 両台帳の交差 | 45 |
| 両台帳の和集合外 | 7,941 |
| 和集合外で比例が真 | 230 |
| 台帳 key が実在 test function でないもの | 0 |

広い scope の fixture は 8 件を全 consumer closure まで追った。

- `repository_scan` (`test_campaign_import_invariant.py:1074`): consumer はすべて既存 hold。
- `benchmark_snapshots` (`test_codex_reasoning_ab.py:351`): consumer は serial / hold。
- `real_known_axes_doc` (`test_s1_measurement_freeze.py:45`): consumer は hold。
- `repository_candidate_commit` (`test_s8c_preregistration_invariant.py:119`): 和集合外 3 件すべて比例。
- `fixed_decisions_bytes`、`canonical_decisions_blob`: 履歴 commit の固定 blob で、現行 repo 成長には比例しない。
- `compiled_oracle_artifacts`、`failure_digest_e2e`: 実 repo 全件列挙へ到達しない。

## 成長比例 family 台帳

各 family の全 node は次節で展開する。

| ID | node 数 | 到達経路 file:line | 比例軸・根拠 | 既定 skip | 結論 |
|---|---:|---|---|---|---|
| A01 artifact admission | 4 | `test_artifact_admission.py:738-816` | `ls-tree -r`、Git diff、campaign lock glob、campaign directory 列挙。`output_artifacts` | no | N |
| A02 calibration contract | 70 | `_synthetic_repository` `test_calibration_freeze_authority_contract.py:59-64`; real case glob `calibration_freeze_authority_contract.py:994` | fixture subtree の全 copy / case 列挙。`tracked_files` | no | N |
| A03 campaign | 2 | production AST walk `test_campaign.py:4650-4696`; real `orchestrator` copytree `certified_writer_fixtures.py:279-305` | `tracked_files` | no | N |
| A04 CCBench spawn inventory | 2 | `test_ccbench_spawn_sites.py:246-258` | 2 production subtree の全 `rglob("*.py")` と parse | no | N |
| A05 check-docs | 3 | `test_check_docs.py:7282-7289,7462-7471,9433-9441` | 実 `tools/check_docs.py` 全実行。`docs_bytes` | no | **R** |
| A06 Codex agents | 21 | `_fixture` `test_codex_agents.py:37-53`; direct glob `:159-161` | 3 実 subtree の copytree。`tracked_files` | no | **R** |
| A07 Codex worker ledger | 1 | `test_codex_worker_ledger.py:1986-2000` | real fixture tree 全 `rglob` × before/after。`tracked_files` | no | N |
| A08 dev-wave wait | 1 | `test_dev_wave_wait.py:1151-1199` | 実 index への `ls-files`。`tracked_files` | no | N |
| A09 dev-wave checker | 10 | `_fixture` `test_dev_waves_checker.py:60-70` | 実 `tools/task_runs` 全 copytree | no | **R** |
| A10 dev-wave integration | 40 | `_copy_task_run_surface` `test_dev_waves_integration.py:160-185` | 各 node が実 `tools/task_runs` を copytree | no | **R** |
| A11 env activation | 7 | Git archive/copy `test_env_contract_activation.py:298-327,1574-1604`; real authority enumeration `:243-253,2423-2536` | `tracked_files` | no | N |
| A12 hooks | 1 | `test_hooks.py:3700-3726` | 実 `tools/pegasus` を `os.walk` し全候補を読む | no | N |
| A13 login headroom | 2 | `test_login_headroom.py:1602-1643` | 全 `git ls-files`、production Python 全 rglob/read | no | N |
| A14 P3 build authority | 2 | `test_p3_build_authority_cli.py:181-197,617-647,1177-1194` | tracked Python 全件、campaign Python 全件 | no | N |
| A15 P3 S4 loop | 1 | `test_p3_s4_loop.py:2233-2267` | real patch corpus 全 glob/read | no | N |
| A16 Pegasus dispatch | 1 | `test_pegasus_dispatch_compute.py:1554-1567` | production Python 全 rglob/read | no | N |
| A17 Pegasus policy | 2 | `_tracked_paths` `test_pegasus_policy_registry.py:47-58`; consumers `:354-493` | 全 `ls-files` と tracked production source 読込 | no | N |
| A18 Pegasus tools | 3 | registered calibration glob `test_pegasus_tools.py:635-664`; copytree `:1229-1259` | `output_artifacts` / `tracked_files` | no | N |
| A19 reflux IR | 1 | `test_reflux_ir.py:274-298` | real production Python 全 rglob/read | no | N |
| A20 known-axes helper | 1 | `test_s1_known_axes_freeze.py:450-475` | campaign Python 全 glob/read | no | N |
| A21 floor campaign | 2 | `test_s8b_floor_campaign.py:940-963,3632-3675` | production Python 全 rglob/read | no | **G** |
| A22a T-080 stub-free | 6 | copy helpers `test_s8b_oracle_driver.py:528-698`; consumer pin `:609-677` | 全 `orchestrator` と Git-visible output の複製 | **yes** | S |
| A22b oracle receipt | 2 | consumers `test_s8b_oracle_driver.py:3757-3887`; real resolver `real_repo_receipt_memo.py:73-75,145-163` | commit/provenance chain | no | N |
| A23 oracle manifest | 3 | production scan helper `test_s8b_oracle_manifest_contract.py:39-84`; output rglob `:130-146` | `tracked_files` / `output_artifacts` | no | N |
| A24 ratified freeze | 1 | `test_s8b_ratified_freeze.py:2013-2023` | campaign Python 全 glob/read | no | N |
| A25 S8c preregistration | 3 | shared fixture `_candidate_commit` `test_s8c_preregistration_invariant.py:76-121`; scan `:206-228` | `git add -A` / full holdout scan。`tracked_files` | no | N |
| A26 silo driver | 1 | `test_silo_ladder_rung1_driver.py:927-957` | production binding glob/rglob | no | N |
| A27 silo evidence | 1 | consumer `test_silo_ladder_rung1_evidence.py:1216-1274`; production enumerator `silo_ladder_rung1.py:262-296` | `tracked_files` / `provenance-chain` | no | N |
| A28 spool fold | 8 | archive scans `test_spool_fold.py:566-599,3778-3847`; consumers `:1752-1788,3865-3960` | `docs_bytes` / archive file count | no | N |
| A29 T126 | 23 | fixed path Git check `test_t126_pegasus_tools.py:1485-1502`; `_submit_fixture` `:3158-3165` | real `orchestrator` copytree / Git index | no | N |
| A30 T793 report | 4 | tests `test_t793_report.py:33-77,132-142`; production HEAD decisions read/scan `publication/report.py:75-111,114-180` | `docs_bytes` | no | N |
| A31 verifier fixture | 1 | `test_verifier.py:229-239` | real trace fixture corpus の `os.walk` | no | N |

## 全 node_id

以下は `file.py::function@definition-line`。`@line` は node ID には含めない。

### A01–A05

```text
test_artifact_admission.py::
  test_trusted_snapshot_campaign_corpus_is_fully_enumerated@738
  test_existing_campaign_tracked_bytes_match_git_head@761
  test_existing_campaign_lock_corpus_is_exactly_32_v1_locks@785
  test_existing_campaign_classification_exact_mapping@806

test_campaign.py::
  test_certified_writer_authorization_caller_inventory_is_closed@4163
  test_m8_preflight_rejects_fail_open_domain_module_drift@4997

test_ccbench_spawn_sites.py::
  test_reviewed_process_launch_inventory_is_recursive_and_exact@265
  test_reviewed_ccbench_measurement_launches_use_bounded_sites@275

test_check_docs.py::
  test_dev_wave_model_pins_accept_current_docs_contract@7282
  test_normative_exact_section_pins_accept_real_repo@7462
  test_real_repo_clean@9433
```

### A02 calibration contract — 70 node

```text
test_calibration_freeze_authority_contract.py::
  test_real_repository_contract_is_consistent_but_incomplete@135
  test_current_repository_is_rejected_as_stage0_incomplete@172
  test_stage0_remains_incomplete_after_r1_r2_r3_projection@268
  test_design_row_removed_is_rejected@309
  test_declared_design_row_removed_is_rejected@322
  test_orphan_case_file_is_rejected@335
  test_manifest_entry_without_case_file_is_rejected@343
  test_manifest_raw_sha256_literal_tamper_is_rejected@351
  test_case_file_bytes_tamper_with_manifest_unchanged_is_rejected@362
  test_case_and_manifest_hash_tamper_together_is_rejected@380
  test_false_pending_count_is_rejected@411
  test_unresolved_binding_in_row_coverage_is_rejected@424
  test_executable_binding_without_positive_control_is_rejected@437
  test_pending_binding_with_positive_control_is_rejected@453
  test_adjudicated_rollback_cannot_regress_to_unresolved@472
  test_adjudicated_revocation_cannot_regress_to_unresolved@490
  test_adjudicated_xf_position_cannot_regress_to_unresolved@508
  test_adjudicated_u_a1_cannot_regress_to_unresolved@526
  test_deferred_seal_ruling_cannot_be_resolved@544
  test_rejected_post_activation_lease_is_rejected@562
  test_s2_profile_without_not_applicable_guarantee_is_rejected@580
  test_manifest_status_cannot_claim_complete_while_gates_remain@597
  test_required_gate_removed_is_rejected@609
  test_r1_revocation_record_required_gate_removed_is_rejected@628
  test_r4_cancellation_record_required_gate_removed_is_rejected@647
  test_stage6_policy_gate_cannot_be_resolved_early@666
  test_required_gate_owner_changed_is_rejected@685
  test_required_gate_resolved_without_evidence_is_rejected@702
  test_required_gate_reorder_with_refreshed_manifest_hash_is_rejected@721
  test_fixture_entries_sha256_is_independent_self_consistency_check@742
  test_ruling_profile_order_drift_is_rejected@757
  test_design_selection_column_matches_selection_enums@774
  test_design_literals_hidden_in_html_comment_are_not_authoritative@793
  test_design_fenced_decoy_is_not_authoritative@817
  test_design_revocation_table_only_in_tilde_fence_is_rejected@890
  test_design_revocation_table_only_in_long_backtick_fence_is_rejected@902
  test_design_stage6_row_only_in_tilde_fence_is_rejected@914
  test_design_stage6_row_only_in_long_backtick_fence_is_rejected@926
  test_design_unclosed_fence_is_rejected@938
  test_design_long_fence_is_not_closed_by_shorter_marker@949
  test_design_fence_is_not_closed_by_different_marker@962
  test_design_invalid_backtick_info_decoy_is_rejected@975
  test_design_tab_indented_fence_decoy_is_rejected@999
  test_design_tilde_fence_info_may_contain_backtick@1029
  test_design_longer_fence_closer_is_accepted@1040
  test_design_tab_indented_fence_closer_is_rejected@1051
  test_design_three_space_indented_fence_closer_is_accepted@1067
  test_design_fence_closer_with_non_whitespace_suffix_is_rejected@1080
  test_design_fence_closer_without_suffix_is_accepted@1096
  test_design_space_tab_indented_fence_opener_is_rejected@1107
  test_design_three_space_indented_fence_opener_is_accepted@1125
  test_design_crlf_unclosed_fence_is_rejected@1138
  test_design_crlf_fence_is_accepted@1152
  test_design_short_fence_closer_with_trailing_spaces_is_rejected@1163
  test_design_fence_closer_with_trailing_spaces_is_accepted@1179
  test_design_revocation_constraint_relaxation_is_rejected@1193
  test_design_revocation_key_substitution_is_rejected@1211
  test_design_stage6_live_tip_relaxation_is_rejected@1227
  test_design_stage6_contradictory_control_suffix_is_rejected@1241
  test_design_stage6_execution_boundary_tail_drift_is_rejected@1260
  test_design_stage6_policy_gate_id_drift_is_rejected@1287
  test_design_stage_scope_matches_fixture_assignment_gate_id@1307
  test_not_applicable_outside_applicability_rule_is_rejected@1323
  test_resolved_ruling_without_design_selection_enum_is_rejected@1343
  test_duplicate_json_key_is_rejected@1363
  test_non_finite_json_constant_is_rejected@1371
  test_unknown_case_key_is_rejected@1381
  test_placeholder_string_is_rejected@1391
  test_bool_is_not_accepted_as_integer@1401
  test_noncanonical_record_bytes_are_rejected@1410
```

### A06 Codex agents — 21 node

```text
test_codex_agents.py::
  test_current_sources_render_byte_exact_and_native_is_empty@159
  test_any_native_discovery_toml_is_rejected@252
  test_project_config_native_role_is_rejected_and_globals_are_allowed@266
  test_write_mode_does_not_create_native_or_adapter_files@291
  test_adapter_inventory_missing_extra_and_symlink_are_rejected@306
  test_adapter_byte_drift_and_runtime_claim_injection_are_rejected@325
  test_claude_body_or_description_drift_requires_independent_ledger_review@338
  test_claude_tools_model_and_effort_must_match_manifest@367
  test_unquoted_and_leading_hash_description_are_rejected@391
  test_manifest_and_claude_role_inventory_must_be_bijective@408
  test_capability_mapping_omission_and_wrong_lowering_are_rejected@421
  test_codex_model_and_effort_cannot_be_omitted_or_inherited@440
  test_verifier_codex_mapping_is_explicitly_pinned@459
  test_full_role_manifest_pin_rejects_semantic_contract_weakening@475
  test_runtime_activation_is_blocked_on_uncontrollable_additional_tools@524
  test_auditor_output_schema_requires_diff_digest_for_consumer@1108
  test_all_role_manifest_schema_and_adapter_weakening_hits_independent_ledgers@1134
  test_consumer_required_field_drift_is_detected_from_source_ast@1186
  test_duplicate_manifest_key_is_rejected@1269
  test_nonfinite_manifest_json_constants_are_rejected@1286
  test_lockstep_role_deletion_is_rejected_by_absolute_count_floor@1312
```

### A07–A09

```text
test_codex_worker_ledger.py::
  test_tool_does_not_change_fixture_file_list_or_mtime@1986

test_dev_wave_wait.py::
  test_floor_job_staging_is_ignored_while_submissions_remain_tracked@1151

test_dev_waves_checker.py::
  test_fully_valid_wave_runs_active_checks_in_isolated_checkout@171
  test_any_passive_failure_prevents_every_active_subprocess@182
  test_first_reason_is_worker_even_when_later_passive_gates_also_fail@193
  test_trust_root_change_blocks_checks_without_being_masked_by_code_digest@207
  test_landed_run_tests_runner_tamper_is_trust_root_changed@252
  test_landed_task_run_check_runner_tamper_is_trust_root_changed@256
  test_completed_receipt_requires_main_landed_last_commit_and_branch_tip_equal@260
  test_task_run_terminal_outcome_must_be_completed@282
  test_check_docs_must_appear_exactly_once@294
  test_active_check_side_effect_on_main_is_found_by_reobservation@320
```

### A10 dev-wave integration — 40 node

```text
test_dev_waves_integration.py::
  test_one_wave_success_accepts_exact_fake_receipt_and_landing@468
  test_fold_success_scenario_declares_a_verified_direct_child_fold@492
  test_fake_manifest_run_id_is_bound_to_path_namespace@542
  test_fake_manifest_wave_index_is_bound_to_wNNN_namespace@546
  test_three_wave_success_uses_distinct_pid_start_and_session_markers_without_transcript_carryover@550
  test_child_failure_injection_stops_before_next_wave@577
  test_cancel_running_child_persists_signal_prepare_then_observe@621
  test_shutdown_running_child_uses_same_prepared_signal_path@646
  test_fake_handshake_failure_persists_exact_terminal_reason@670
  test_malformed_child_output_is_output_invalid@692
  test_valid_receipt_with_wrong_binding_is_receipt_invalid@713
  test_independent_gate_failure_stops_next_wave@743
  test_same_request_id_and_digest_returns_same_run_after_disconnect_and_restart@755
  test_second_distinct_submit_is_busy_while_run_active@774
  test_active_check_failure_occurs_only_after_passive_gates@827
  test_dedicated_provenance_and_code_dirty_reasons_are_wired@861
  test_resume_never_duplicates_child_or_land@900
  test_real_daemon_sigkill_restart_closes_recovery_gate_at_three_points@947
  test_real_daemon_sigkill_after_accepted_reconciles_without_child_rerun@987
  test_accepted_reconciliation_rejects_dirty_repo_without_child_rerun@1024
  test_accepted_reconciliation_rebinds_repo_identity_and_main_branch@1068
  test_invalid_request_audit_has_capacity_and_creates_no_run@1120
  test_linked_worktree_repo_root_resolves_common_identity_and_runtime_main@2170
  test_nested_environment_rejects_serve_and_resume_but_client_can_connect@2187
  test_settings_strict_parse_and_required_hook_wiring_fail_closed@2199
  test_budget_accumulates_across_waves_and_deadline_boundary_is_clipped@2245
  test_max_run_bytes_counts_wal_and_all_artifacts_but_excludes_git_worktree@2278
  test_vanished_rewrite_scratch_is_skipped_but_lost_artifact_fails_closed@2328
  test_capacity_gate_stays_closed_when_an_artifact_vanishes_mid_measure@2362
  test_artifact_aggregate_cap_stops_before_next_wave_side_effect@2380
  test_expired_deadline_prevents_next_real_artifact_side_effect@2403
  test_each_outcome_has_one_terminal_mapping_and_never_starts_next_child@2441
  test_blocked_receipt_with_main_move_is_failed_not_blocked@2457
  test_spawn_identity_read_failure_kills_and_reaps_exact_popen@2469
  test_cancel_identity_mismatch_records_ambiguous_not_signalled@2496
  test_wal_partial_tail_validate_is_fail_closed@2536
  test_supervisor_wal_fsync_failure_orders_real_worker_spawn_side_effect@2553
  test_auto_unavailable_or_permission_abort_never_rebuilds_dangerous_argv@2631
  test_wait_idle_is_bound_to_the_run_thread_and_reports_timeout_without_raising@2654
  test_terminal_state_precedes_quiescence_and_wait_idle_leaves_no_run_thread@2689
```

### A11–A21

```text
test_env_contract_activation.py::
  test_production_loader_rejects_tail_deletion_with_source_head_unchanged@1574
  test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart@1595
  test_historical_calibration_is_verified_only_when_resolved_in_source_stage@1892
  test_import_performs_no_open_or_stat_io_in_worktree_or_archive_source_stage@1959
  test_issue_main_rejects_generation_skip_at_last_of_65_envs_without_publishing@2392
  test_issue_main_rejects_invalid_successor_at_last_of_65_changed_envs_without_publishing@2443
  test_issue_main_accepts_65_env_plus_one_and_publishes@2499

test_hooks.py::
  test_bash_pegasus_execution_inventory_is_synchronized@3700

test_login_headroom.py::
  test_ceiling_numeric_literal_occurs_only_in_login_headroom_module@1602
  test_local_budget_constants_are_defined_only_in_login_headroom_leaf@1625

test_p3_build_authority_cli.py::
  test_tracked_python_coder_authority_ast_closure_is_exact@617
  test_python_ccbench_manual_materializers_are_explicitly_non_admissible@1177

test_p3_s4_loop.py::
  test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted@2233

test_pegasus_dispatch_compute.py::
  test_best_effort_qdel_production_caller_is_only_fresh_gate@1554

test_pegasus_policy_registry.py::
  test_pegasus_policy_registry_is_complete_and_tracked@354
  test_direct_shared_policy_reads_of_moved_keys_are_a_best_effort_tripwire@434

test_pegasus_tools.py::
  test_known_values_cpu_check_rejects_nearby_sku@693
  test_acquisition_candidate_rejects_schema_valid_duplicate_probe_key@713
  test_submit_dry_run_does_not_resolve_cluster_commands@1229

test_reflux_ir.py::
  test_golden_has_no_production_import_and_production_has_no_golden_consumer@274

test_s1_known_axes_freeze.py::
  test_goldens_helper_is_independent_of_production@450

test_s8b_floor_campaign.py::
  test_production_use_perf_keyword_call_sites_are_a_closed_set@940
  test_materializer_registry_covers_all_python_build_launches@3632
```

### A22–A28

```text
test_s8b_oracle_driver.py::
  test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5@1024
  test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5@1107
  test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5@1170
  test_t080_full_valid_history_defects_have_one_baseline_reason_f28@1403
  test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28@1430
  test_never_issued_generator_tamper_reaches_public_driver_gate_g7@3417
  test_run_block_reuses_launch_validated_and_legacy_loader_is_dead@3757
  test_run_block_verifies_manifest_once_and_reuses_object@3824

test_s8b_oracle_manifest_contract.py::
  test_loader_production_consumer_sets_are_pinned_for_spec_reverification@87
  test_verify_manifest_production_consumer_set_is_auxiliary_pin@99
  test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec@130

test_s8b_ratified_freeze.py::
  test_no_production_module_constructs_ratified_freeze_directly@2013

test_s8c_preregistration_invariant.py::
  test_candidate_freeze_matches_contract_and_generation_chain@125
  test_candidate_is_not_effective_and_has_zero_satisfied_predicates@190
  test_wave_files_do_not_contaminate_production_holdout_scan@206

test_silo_ladder_rung1_driver.py::
  test_runtime_binding_covers_all_execution_semantics_modules@927

test_silo_ladder_rung1_evidence.py::
  test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head@1216

test_spool_fold.py::
  test_boundary_constant_shift_is_detected_by_real_corpus_sentinel@566
  test_real_corpus_sentinel_rejects_missing_boundary_date@588
  test_failure_supersede_real_f1_boundary_without_blank_line_is_byte_exact@1752
  test_failure_supersede_real_f196_f197_boundary_is_byte_exact@1766
  test_failure_supersede_real_final_entry_eof_is_byte_exact@1782
  test_fixture_tools_imports_uses_fixture_restores_state_and_propagates_exceptions@3865
  test_n37_real_repo_canonical_family_requires_archive_active_history@3918
  test_real_worklog_105_to_106_next_action_is_byte_exact_golden@3953
```

### A29–A31

```text
test_t126_pegasus_tools.py::
  test_every_required_identity_path_is_tracked_in_this_repo@1485
  test_submit_rejects_compensating_cap_drift_before_scheduler_calls@3305
  test_submit_rejects_nul_in_walltime_before_scheduler_calls@3325
  test_submit_rejects_each_single_layer_equal_float_type_drift@3356
  test_submit_rejects_each_mapping_masked_equal_float_type_drift@3380
  test_submit_rejects_overdetermined_reservation_policy_type_drift@3405
  test_submit_reservation_reader_rejects_python_failure_after_complete_output@3425
  test_submit_resume_rejects_boolean_invocation_retry_index@3448
  test_fake_qsub_qstat_exact_visibility_and_durable_receipt@3498
  test_duplicate_initial_is_rejected_before_any_additional_qsub@3517
  test_dry_run_does_not_consume_series_before_real_submit@3527
  test_m8c_qsub_nonzero_is_accepted_unknown_and_never_resubmitted@3544
  test_qsub_visibility_mismatch_leaves_intent_binding_but_no_receipt@3575
  test_post_qsub_receipt_write_failure_is_durably_bound_and_fail_closed@3629
  test_m8b_post_qsub_prebinding_crash_never_uses_raw_stdout_authority@3649
  test_binding_publish_before_ledger_bind_is_exactly_recoverable@3678
  test_binding_staging_without_canonical_never_authorizes_resubmit@3694
  test_submit_receipt_hard_crash_recovers_without_second_qsub@3730
  test_one_authorized_retry_submit_collector_chain_is_accepted_once@3748
  test_submit_rejects_symlink_component_hidden_drift_and_unsupported_perf@3805
  test_submit_untracked_scan_failure_is_fail_closed_before_qsub@3847
  test_m8a_create_only_invocation_claim_serializes_parallel_submit@3867
  test_invocation_claim_short_write_is_completed_and_bound@3924

test_t793_report.py::
  test_deny_only_report_contains_authority_and_both_submission_denials@33
  test_authority_none_is_bound_to_d291_without_rewriting_documents@53
  test_actual_head_d292_reference_is_reported_fail_closed@65
  test_cli_json_is_deterministic_and_deny_only@132

test_verifier.py::
  test_all_v2_fixture_files_have_clean_framing@229
```

## P1〜P4

| 裁定 | 判定 | 根拠 |
|---|---|---|
| P1 | **refuted** | `test_s8b_ratified_verify.py` は `_REAL_V1` 1 file (`:44,448-451,1130`) だけで、この部分は親が正しい。silo の最初の node (`test_silo_ladder_rung1_evidence.py:1202-1213`) も固定量。しかし 2 本目は `runtime_modules_binding(ROOT)` (`:1274`) から production の glob/rglob/hash closure (`silo_ladder_rung1.py:262-296`) へ到達する。copytree は現在 7/13 file・数 msでも、追加 file ごとにコピー量が増えるため D335 上は比例。 |
| P2 | **refuted** | 名指し node の D451 見送り自体は正しい。しかし `_candidate_commit` は `git read-tree`、`git add -A`、`write-tree`、`commit-tree` (`test_s8c_preregistration_invariant.py:76-100`) を session fixture (`:119-121`) で 3 consumer に提供する。したがって比例 node は `:125,:190,:206` の 3 件。最後だけはさらに全 repo scan (`:216-227`) を払う。3 件を保留すると holdout / candidate-generation 防壁の既定 node がゼロ、部分保留では shared fixture 費が残る。 |
| P3 | **real（強化）** | `test_real_repo_clean` のほか `:7282` と `:7462` も実 checker 全起動。land は `_validate_generated_docs` で同 checker を起動 (`tools/dev_wave_land.py:2211-2237`) し、fold 後に必ず呼ぶ (`:2335-2342`)。wave checker は check-docs を exactly-once で選別 (`tools/dev_waves/checker.py:351-361,643-645`) し isolated checkout で実行 (`:678-688`)。 |
| P4 | **real** | 230 件中、親名指し外が大半。最大は calibration 70、integration 40、T126 23、Codex agents 21。 |

P2 の比例源を contained に除去するには、`git add -A` と全 `search_repository` の双方を bounded input に変える必要がある。しかし後者は「wave file が実 repository の holdout scan に混入しない」こと自体が検査対象で、入力を縮めると受理集合が変わる。現 scope 内に安全な置換はない。

## D451・guard・pin 閉包

### 登録推奨 74 件

- A05: land と wave checker が同じ `check_docs.py` を既定実行する。
- A06: default checks が `static-check` を含む (`tools/dev_waves/cli.py:188-195`)。`tools/task_run_check.py:15-20,52-64` が実 `tools/check_codex_agents.py` を起動する。
- A09/A10: production CLI が standard supervisor を起動 (`tools/dev_waves/cli.py:362-377`) し、daemon が同じ `verify_wave` を呼ぶ (`tools/dev_waves/daemon.py:294,1305`)。

これ以外は、同じ closed-set、negative mutation、fixture immutability、歴史 golden を再検査する独立した既定経路を確定できない。production 関数が存在するだけでは D451 の「他の走行」と数えなかった。

### Guard binding

loader 全件検索は 70 hit / 48 file。候補 test file の自己読込は次の 1 件だけだった。

- `test_s8b_floor_campaign.py:7079-7093`: subprocess source 内の `spec_from_file_location(..., Path(__file__))`。ここへ新たな guard を置くと `test_deterministic_artifacts_across_roots_and_subprocess_environments` が import 時に拒否される。A21 は登録不可。

登録推奨 4 file には自己 `spec_from_file_location` / runpy consumer がない。binding はそれぞれ次の plain-runner 契約にする。

| file | 挿入位置 | `plain_runner` |
|---|---|---|
| `test_check_docs.py` | `_run` 後、main guard 前 (`:9613-9641`) | `"manual"` |
| `test_codex_agents.py` | `_run` 後、main guard 前 (`:1338-1352`) | `"manual"` |
| `test_dev_waves_checker.py` | `_run` 後、main guard 前 (`:329-348`) | `"manual"` |
| `test_dev_waves_integration.py` | `_run` 後、main guard 前 (`:2718-2725`) | `"pytest-delegating"` |

guard 本体の契約は `growth_test_holds.py:558-604`。import と top-level call の独立検査は `test_growth_test_holds_contract.py:475-520`。

### Pin 閉包

- path key: live source上の明示的 pin は hold registry / contract mirror、T-080 consumer set (`test_s8b_oracle_driver.py:630-677`)、silo 非登録 assertion (`test_growth_test_holds_contract.py:244-247`)。
- identifier key: 230 node は AST で両台帳と照合済みで、現在はいずれも和集合外。
- current bytes SHA-256: `.git` / bytecode cache を除く 13,059 file を対象に候補 31 test file の現行 SHA-256 literal を検索し、match は 0。
- 加工後 hash の source-side 検索でも、`sha256/hash` と `test_*.py` を同時に持つ live Python 行は 0。
- 例外は歴史 pin。`tools/codex_reasoning_ab.py:97-101` の `test_check_docs.py` は `38675b06…`、現行 bytes は `098f3dfd…`。既に不一致なので今回の guard 追加では発火せず、更新してはいけない。
- 台帳側の現行 pin は `test_growth_test_holds_contract.py:39-41`。独立 filename mirror は `:589-603`。

## 段 5 実装手順

1. `orchestrator/tests/growth_test_holds.py:99-463` に A05/A06/A09/A10 の 74 row を追加する。既存 56 row は一切変更しない。追加後 count は 130。axis は A05=`docs_bytes`、残り=`tracked_files`、release condition は既存 `_hold` の `explicit-user-command-only`、`correctness_gate=True`、`measured_seconds=None` を維持する。

2. 4 test file に `enforce_held_functions` の正規 import と上表の top-level binding を追加する。全 test 定義と `_run` の後、`if __name__ == "__main__"` の直前に 1 回だけ置く。

3. `test_growth_test_holds_contract.py:39-41` を同じ patch で更新する。

   - `_EXPECTED_HOLD_COUNT = 130`
   - `_EXPECTED_KEY_SHA256`: 追加後の `growth_test_hold_key_digest(GROWTH_TEST_HOLDS)`
   - `_EXPECTED_ROW_CONTRACT_SHA256`: `:216-225` と同じ `[key, axis, ruling, correctness_gate]` JSON recipe で再計算

   値を手計算・途中状態から転記せず、74 rowと4 guardが揃った最終 treeから一度だけ算出する。

4. 独立ミラーを同時更新する。

   - `_held_filenames()` の exact tuple (`:589-603`) に、辞書順で `test_check_docs.py`、`test_codex_agents.py`、`test_dev_waves_checker.py`、`test_dev_waves_integration.py` を追加する。
   - 新 row に `collateral_note` を置く場合は `_EXPECTED_COLLATERAL_NOTES` (`:60-150`) に同じ 74 keyを同時追加する。片側だけ更新しない。
   - inventory の count/key/correctness mirror (`:363-379`) は3 pinを介して同時に変わることを確認する。
   - silo 非登録 assertion (`:244-247`) は、比例 refutation ではなく D451 見送りとして意味を読み替えるが、assertion 自体は維持する。

5. `output/insights/2026-08-16_t1222-growth-hold-sweep/` に次を記録する。

   - 7,941-node 母集合と検索式・件数
   - 230 candidate の本回答と同じ exact inventory
   - `registered=74 / d451_not_registered=148 / guard_blocked=2 / already_default_skipped=6`
   - P1〜P4
   - `test_s8b_ratified_verify.py`、最初の silo node、固定 historical blob、tmp-root scan などの refuted 集合

6. worklog / decisions spool fragmentへ、74 件の恒久保留と、登録しなかった 156 件の理由を分けて記録する。D451 見送りを「非比例」と書かない。

7. 段 5/6 の実走は親が行う。直接 pytest は使わず、対象テストも `tools/run_tests.py` を通す。その後 `tools/check_codex_agents.py`、`tools/check_docs.py`、commit 後の `tools/check_ai_provenance.py` を repo 規律どおり実行する。本段ではいずれも実行しておらず、緑は主張しない。

最終 adjudication で74件についても production route が D451 の独立経路ではないと覆された場合は、台帳・3 pin・guardを一切変更しない。その場合でも inventory、`registered=[]` の提示資料、worklog/decision spool が段5の必須成果物になる。