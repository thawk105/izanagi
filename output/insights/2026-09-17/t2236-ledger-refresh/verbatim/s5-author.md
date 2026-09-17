## 現行挙動と変更後挙動

変更前は、全再生成が全 entry を JUnit 由来の値へ置換し、`--add-only` が既存 entry を保持して非凍結の未登録 node だけを追加していました。不正 JUnit・重複 nodeid・空／全失敗入力は拒否していました。

追加した `--refresh` は凍結既存 entry の値を保持し、非凍結部分を JUnit から置換・追加・削除します。failed/error の非凍結旧 entry も削除します。既存台帳の不在・不正は rc=2、`--add-only` との併用も拒否します。既存 mode とその stdout は維持しています。

## 変更した file と関数 (file:line)

- [tools/update_acceptance_duration_ledger.py:57](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2236-author/tools/update_acceptance_duration_ledger.py:57)：`_parser` に排他 option を追加。`:453` に `_refresh_result`、`:529` の `main` に読込み・refresh・件数表示を追加。
- [orchestrator/tests/test_update_acceptance_duration_ledger.py:712](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2236-author/orchestrator/tests/test_update_acceptance_duration_ledger.py:712)：補助関数と新設 12 test、parameter 展開後 29 node を追加。既存 test・期待値・末尾 harness は変更なし。
- [orchestrator/tests/acceptance_duration_ledger.json:1](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2236-author/orchestrator/tests/acceptance_duration_ledger.json:1)：指定 3 shard を生成器の `--refresh` で再生成。手編集なし。

`git status` の変更はこの 3 file のみ。`git diff --check` は成功しました。

## 台帳再生成の stdout (逐語) と凍結 426 行の照合結果

初回再生成：rc=0。

```text
excluded_failure_or_error=0
mode=refresh
preserved_frozen=426
replaced=22593
added=1360
removed=126
excluded_frozen_suite=615
covered=24361 total=24568 ratio=0.992
```

同じ command に `--check` を追加：rc=0。

```text
excluded_failure_or_error=0
mode=refresh
preserved_frozen=426
replaced=23953
added=0
removed=0
excluded_frozen_suite=615
covered=24361 total=24568 ratio=0.992
```

初回件数は事前計算とすべて一致。再実行では非凍結 23953 件が共通 key なので、同値でも `replaced` に数えます。

照合結果：

```text
reference_frozen_entries=426 matched=426 missing=0
HEAD_frozen_full_lines_including_comma_and_LF=426 byte_differences=0
nodeid_count=24379 canonical_bytes=match
```

参照 file は末尾 comma を省いた entry 表記でした。その 426 行の一致に加え、変更前 HEAD の凍結行と comma・LF を含む完全 bytes も照合しました。

## 実走した test (nodeid と結果)

指定の自走 harness を実行しました。

- 再生成前：**53 passed、0 failed、rc=0**（3.16 秒）。
- 再生成後：**53 passed、0 failed、rc=0**（2.94 秒）。`PYTEST_ADDOPTS=-v` で個別結果も確認。
- T-1574、schema、既存 add-only test は両走とも PASS。

以下は全件 **PASS**。nodeid の共通接頭辞は `orchestrator/tests/test_update_acceptance_duration_ledger.py::` です。

```text
test_g7a_join_generates_canonical_nodeids_and_check_passes
test_g7a_each_invalid_input_is_rejected_with_fixed_signature[shifted-module-class-boundary-cases0-0]
test_g7a_each_invalid_input_is_rejected_with_fixed_signature[duplicate-nodeid-cases1-0]
test_g7a_each_invalid_input_is_rejected_with_fixed_signature[missing-duration-cases2-0]
test_g7a_each_invalid_input_is_rejected_with_fixed_signature[negative-duration-cases3-0]
test_g7a_each_invalid_input_is_rejected_with_fixed_signature[nan-duration-cases4-0]
test_g7a_each_invalid_input_is_rejected_with_fixed_signature[infinite-duration-cases5-0]
test_g7a_duplicate_nodeid_across_shards_is_rejected
test_f5_ambiguous_module_prefix_lengths_are_rejected
test_f9_disjoint_junit_shards_are_merged
test_g7a_check_difference_returns_one_without_writing
test_g7b_second_input_failure_leaves_existing_output_byte_exact
test_g7c_group_suffix_guard_preserves_at_inside_parametrize_value
test_g7d_quantization_is_byte_deterministic_and_absorbs_small_jitter
test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations
test_t1574_changed_suite_ledger_node_delta_is_exact
test_g7f_coverage_reports_complete_and_missing_nodeids
test_f8_coverage_normalizes_relative_path_and_group_suffix
test_g7g_failed_and_error_cases_are_excluded_but_skipped_is_included
test_add_only_preserves_existing_entry_bytes_and_excludes_frozen_nodes
test_f6_failed_case_is_excluded_before_duration_validation
test_f6_error_case_with_invalid_classname_is_discarded
test_f11_atomic_write_fsyncs_file_then_parent_directory
test_g7h_all_failed_and_empty_junit_have_distinct_rejections
test_refresh_replaces_nonfrozen_entries_and_removes_old_names[9.9]
test_refresh_replaces_nonfrozen_entries_and_removes_old_names[0.5]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_critic.py::]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_p3_exploration_namespace.py::]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_p3_s4_loop_sort.py::]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_real_repo_serialization.py::]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_s1_direct_comparison.py::]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_s8b_materialization.py::]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_s8b_sort_swo_receipt.py::]
test_refresh_preserves_frozen_entry_bytes_and_values[orchestrator/tests/test_sort_swo_oracle.py::]
test_refresh_excludes_all_frozen_junit_nodes
test_refresh_frozen_prefixes_cover_removed_nodes_and_writer_base_key
test_refresh_renders_canonical_bytes
test_refresh_canonicalizes_noncanonical_frozen_number_spelling
test_refresh_and_add_only_are_mutually_exclusive
test_refresh_requires_existing_ledger
test_refresh_rejects_invalid_existing_ledger_without_writing[broken-json]
test_refresh_rejects_invalid_existing_ledger_without_writing[schema]
test_refresh_rejects_invalid_existing_ledger_without_writing[unit]
test_refresh_rejects_invalid_existing_ledger_without_writing[count]
test_refresh_rejects_invalid_existing_ledger_without_writing[bool]
test_refresh_rejects_invalid_existing_ledger_without_writing[negative]
test_refresh_rejects_invalid_existing_ledger_without_writing[nan]
test_refresh_rejects_invalid_existing_ledger_without_writing[infinite]
test_refresh_check_and_coverage_use_refreshed_nodeids
test_refresh_drops_failed_and_error_nonfrozen_entries
test_refresh_rejects_unusable_junit_without_writing[empty]
test_refresh_rejects_unusable_junit_without_writing[all-failed]
test_refresh_rejects_unusable_junit_without_writing[duplicate-shards]
```

## 波及の静的列挙

| 所有外の対象 | 波及 |
|---|---|
| `conftest.py:1520,1560` の validator／loader | schema は同じ。更新値が collection の順序へ反映される可能性があります。 |
| `tools/acceptance_shards.py:381` の `allocate` | 更新値が component の重量・LPT 割付に反映されます。group suffix fallback と未登録 1.0 秒 fallback は不変です。 |
| `test_acceptance_schedule_order.py:660` の被覆 gate | 新設 29 node は指定の旧 JUnit に含まれません。今回の 24361/24568 は指定基準 collection の被覆であり、変更後 collection の gate 実走結果ではありません。閾値 0.90 は不変です。 |
| `test_paper_story_a1_headline.py:1232` の non-touch manifest | 台帳を manifest に含み、working tree の非空を拒否します。現在は未 commit のため、親の commit 後に焦点検査が必要です。 |

これらの file は変更していません。

## 未実走・未完了・気づいた問題

- consumer の焦点検査、受入全走、after wall 測定、事前登録した変異 matrix は未実走です。性能改善は主張しません。
- commit は親の担当として未実施です。禁止された Git 操作、docs 編集、所有外の実装変更は行っていません。
- 任意の非 canonical 入力では凍結値の数値を保持しつつ表記を canonical 化します。`5.890 → 5.89` は test で確認済みです。今回の実台帳の凍結行には byte 差がありません。

## 総括

author 担当の実装・追加 test・台帳再生成・再生成後 harness・凍結 426 行照合は完了しました。台帳は **24379 entry**、指定基準 collection の被覆は **24361/24568**。親の commit・焦点検査・受入検査へ引き渡せる状態です。

追加の「実台帳の非凍結全値を JUnit 由来 map と再照合する」読取り script は、自動 PreToolUse hook が保護対象 path と heredoc の併用を分類不能として拒否しました。この追加検算は未実走です。