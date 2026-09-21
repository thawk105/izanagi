legacy mode は絶対 cache path・PIN に一致する policy・compiler digest 一致を要求し、従来どおり出力 path の追加制限なく受理します。この受理・拒否挙動は変更していません。

# 変更

所有する 3 file だけを変更しました。

- `orchestrator/campaign/s3_mocc_lock_coverage.py`: **157 行追加**。候補識別の純関数と Git wrapper、build 前の blob 束縛、C 上の 6 走、BASE/C の TRACE=0 比較、候補 JSON、旧 JSON path 拒否を追加。
- `orchestrator/tests/test_mocc_xp_pin_candidate.py`: **330 行新設、5 node**。固定期待値、source 契約、論理行比較、識別の拒否対照、実 Git を使う配線検査、JSON consumer を実装。
- `patches/README.md`: **21 行追加**。C の OID・branch、再現資料としての位置付け、旧計装との差 3 箇所、実走の命題と保証限界を記載。

既存 helper の signature と本文は保持しました（変更した既存関数は `_parser` と `main` の分岐追加だけ）。`PIN`・`CHECK_KEYS`・`INSTRUMENTATION_PATCH`、旧 test、旧計装 patch、候補 patch は不変です。

# 検査の argv と出力

実行場所は `pegasus02`。以下は自走 harness の実測です。

```text
PYTHONPATH=. python3 orchestrator/tests/test_mocc_xp_pin_candidate.py

PASS test_candidate_identity_checks
ERROR test_candidate_json_is_bound: FileNotFoundError: [Errno 2] No such file or directory: '/work/1/SFC/tanab/izanagi/.codex/worktrees/t2844-author-b/output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json'
PASS test_candidate_mode_source_routing
PASS test_candidate_source_contract
PASS test_candidate_trace0_logical_rows

4 passed, 1 failed
```

exit code = **1**。node 5 の独立した正常 fixture と 7 個の一文字改変拒否対照は、JSON 読み込み前に実行済みです。

```text
PYTHONPATH=. python3 orchestrator/tests/test_mocc_proof_surface.py

PASS test_broken_mocc_early_unlock_patch_unlocks_after_entry_and_relocks_before_publish
PASS test_broken_mocc_lockskip_patch_guards_validation_lock
PASS test_broken_mocc_patches_have_unique_production_condition_witnesses
PASS test_broken_mocc_permutation_patch_pops_between_sort_and_trace_check
PASS test_compute_positive_control_json_is_all_pass_and_bound
PASS test_driver_check_keys_are_exact
PASS test_driver_compute_checks_is_input_derived_per_key
PASS test_driver_resolve_toolchain_accepts_bound_versions_and_fails_closed
PASS test_driver_trace0_build_directory_names_are_equal_length
PASS test_driver_verify_passes_mocc_protocol_and_given_root
PASS test_e9e477ca_materialization_fails_closed_when_object_is_missing
PASS test_instr_patch_applies_to_e9e477ca_and_rejects_511c9538
PASS test_instr_patch_keeps_trace0_preprocess_identical
PASS test_instr_patch_names_cll_lock_pointer_predicate
PASS test_mocc_clean_fixture_is_certified_with_patched_snapshot
PASS test_mocc_p_fixture_routes_to_permutation_indeterminate
PASS test_mocc_x_fixture_routes_to_lock_coverage_indeterminate
PASS test_mocc_x_p_proof_surfaces_are_present_only_after_instr_patch

18 passed, 0 failed
```

exit code = **0**。

```text
PYTHONPATH=. python3 orchestrator/tests/test_p3_build_authority_cli.py

PASS test_all_six_registered_sites_issue_site_bound_opaque_authority
PASS test_authority_ast_audit_ignores_unrelated_local_same_leaf_function
PASS test_authority_ast_audit_rejects_dict_storage_and_subscript_call
PASS test_authority_ast_audit_rejects_dynamic_resolution
PASS test_authority_ast_audit_rejects_globals_subscript_lookup
PASS test_authority_ast_audit_rejects_helper_passed_as_argument
PASS test_authority_ast_audit_rejects_import_alias_and_multistage_name_alias
PASS test_authority_ast_audit_rejects_tuple_storage_and_subscript_call
PASS test_authorityless_trigger_coder_is_rejected_before_build_spy
PASS test_dirty_noop_stock_token_enters_coder_admission_namespace
PASS test_low_level_issuer_allowlist_rejects_extra_call_and_function
PASS test_low_level_issuer_allowlist_rejects_prefix_and_nested_paths
PASS test_machine_callers_use_closed_generator_receipts
PASS test_python_ccbench_manual_materializers_are_explicitly_non_admissible
PASS test_registry_declares_intentionally_unclosed_surfaces
PASS test_single_registry_has_typed_compatible_projections
PASS test_stock_machine_and_opted_in_coder_paths_remain_accepted
PASS test_tracked_python_coder_authority_ast_closure_is_exact
PASS test_unregistered_site_is_rejected_before_token_build_or_wal
```

exit code = **0**、19 node。

```text
PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py

PASS test_allowlist_has_no_stale_or_self_runnable_entries
PASS test_every_test_file_is_self_runnable_or_allowlisted
PASS test_this_metatest_is_itself_self_runnable

3 passed, 0 failed, 0 skipped
```

exit code = **0**。

```text
PYTHONPATH=. python3 orchestrator/tests/test_mocc_mutation_proof.py

PASS test_mocc_hot_unlock_has_unique_condition_witness
PASS test_mocc_hot_unlock_is_balanced_on_commit_and_abort
PASS test_mocc_mutation_check_keys_are_exact
PASS test_mocc_mutation_checks_are_input_derived
PASS test_mocc_mutation_condition_gate_uses_new_driver_id
PASS test_mocc_mutation_matrix_is_exact
PASS test_mocc_mutation_proof_json_is_complete_and_bound
PASS test_mocc_mutation_run_records_failure_and_timeout
PASS test_mocc_mutation_trace0_logical_rows_are_input_derived
PASS test_mocc_mutation_u_trace_counts_reads
PASS test_mocc_mutation_verify_binds_protocol_root_and_timeout

11 passed, 0 failed
```

exit code = **0**。

```text
PYTHONPATH=. python3 orchestrator/tests/test_mocc_template_proof.py

PASS test_mocc_auditor_definition_items_are_item_scoped
PASS test_mocc_auditor_projection_rejects_performance_fields
PASS test_mocc_mutation_surface_requires_auditor_live
PASS test_mocc_temperature_axis_contract
PASS test_mocc_template_checks_are_input_derived
PASS test_mocc_template_condition_gate_uses_new_driver_id
PASS test_mocc_template_consumer_binding_controls
PASS test_mocc_template_gate_activation_controls
PASS test_mocc_template_instrumentation_logical_rows
PASS test_mocc_template_instrumentation_preserves_body
PASS test_mocc_template_off_matches_stock_and_on_is_distinct
PASS test_mocc_template_proof_json_is_complete_and_bound
PASS test_mocc_template_quarantine_controls
13 passed, 0 failed
```

exit code = **0**。

```text
python3 -m py_compile orchestrator/campaign/s3_mocc_lock_coverage.py orchestrator/tests/test_mocc_xp_pin_candidate.py
```

出力なし、exit code = **0**。

```text
git diff --check
```

出力なし、exit code = **0**。

# 波及の静的確認

- **既存 caller**: `s3_mocc_mutation_proof.py` と `s3_mocc_template_proof.py` が参照する定数・helper は不変。両 consumer の自走検査も緑。
- **共有 helper / fixture**: `test_mocc_proof_surface.py` を module alias で再利用。既存 test 関数の再収集や共有 fixture の変更なし。
- **spawn inventory**: driver に新しい `subprocess.run` / `Popen` site なし。Git は既存 `_run_checked` 経由。新 test は production directory の走査対象外。
- **materializer / build authority**: `"--build"` を含む関数は `_build_variant` と `_install_dependency` のまま。登録簿変更なし。
- **condition gate / patch 走査**: 新 macro なし。既存 3 macro・broken patch を使用。`test_p3_s4_loop.py` の裸 macro 走査に新しい登録対象を追加しない。
- **template 目録**: 候補 patch に temperature axis marker を追加していない。patch 集合を走査する `test_mocc_template_gate_activation_controls` を含め、自走全緑。
- **bytecode guard**: 新 test の直接 subprocess は Git のみ。Python subprocess 起動は追加していない。
- **plain runner 目録**: 新 file は 5 node を収集する `_run()` を持ち、目録検査は全緑。

配線 test は一時 repository に BASE の子 commit を作成し、checkout・clean 確認・patch 適用・識別を実行します。build、benchmark、verifier subprocess 等の外部境界を差し替えており、実 C の benchmark 成功を示すものではありません。

# 未実走

以下は pytest 経由のため、今回未実走です。

- `test_ccbench_spawn_sites.py`
- `test_s8b_floor_campaign.py`（materializer exact 閉包を含む）
- `test_check_subprocess_bytecode_guard.py`
- `test_p3_s4_loop.py` の patch 走査 test

候補 mode の実 build・benchmark 6 走・実 binary の TRACE=0 比較、最終 C の D297、段 4 の変異工程は未実走です。node 5 の実 JSON consumer は**実装済み・候補 JSON 不在で検査未完了**です。

## 総括

期待赤は **node 5 の候補 JSON 不在だけ**で、それ以外の赤はありません。自走結果は **68 node 緑、1 node 期待赤**です。

所有 3 file のみ変更し、作業用一時 repository と編集した Python 2 file の bytecode は削除済みです。commit は作成していません。この子の検査は親の全走を代替しません。