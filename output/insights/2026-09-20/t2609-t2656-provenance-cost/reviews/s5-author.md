## 総括

**実装済み・pytest 未実走です。** 変更は指定の 2 ファイルのみ。docs 編集・commit はしていません。

- [tools/check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2609-unit-impl/tools/check_ai_provenance.py:1470)：親表検証、non-merge 一括取得、設定 gate 付き merge 親番号別取得、trailer 値共有を実装。
- [orchestrator/tests/test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2609-unit-impl/orchestrator/tests/test_check_ai_provenance.py:8316)：26 テスト関数を追加。

変更した既存関数・型は `validate_message`、`validate_implementation_author`、`_commit_paths`、`_Ancestry`、`_build_ancestry`、`_normal_commit_audit`、`_audit_history`。追加 helper は `_parse_path_batch`、`_batch_nonmerge_paths`、`_merge_path_batch_enabled`、`_batch_merge_parent_paths` です。

現行の trailer 欠落・形式違反、実装面の Codex author 要件、waiver、merge の intersection → `--cc` 判定を維持する実装です。既存テスト全関数の AST が不変であることを確認しました。指定された `test_batch_subprocess_counts_and_selected_order` も変更していません。

**検査結果**

- `check_codex_agents.py`：成功。
- `check_docs.py`：違反なし。
- 構文検査、`git diff --check`：成功。
- 焦点 pytest：`tools/run_tests.py` 経由で試行しましたが、`qstat -Q preflight rc=1`、runner rc=16、`child_started=false`。実走 nodeid はありません。
- 変異試験・固定全史の旧新版比較・性能測定：未実施。

**追加 test 名一覧**（すべて `test_` 接頭辞）

```text
ancestry_parent_rows_match_show_parents
parent_cache_invalid_rows_fall_back
range_and_oracle_keep_legacy_parent_acquisition
batch_nonmerge_always_emits_empty_headers
batch_nonmerge_paths_equal_legacy_in_order
batch_nonmerge_hex_paths_discard_entire_batch
batch_nonmerge_invalid_output_restores_public_result
batch_merge_parent_sets_equal_legacy
batch_merge_parent_slots_and_headers
batch_merge_keeps_combined_diff_contract
batch_merge_late_failure_discards_all_parent_batches
batch_merge_ignore_submodules_uses_legacy_verdict
merge_path_batch_config_gate
normal_audit_reuses_agent_values_once
agent_values_none_and_empty_are_distinct
shared_agent_values_preserve_validator_results
shared_agent_values_stay_with_their_commit
path_batch_subprocess_counts_and_selected_order
shared_values_parser_failure_precedes_paths
path_batches_follow_receipt_final_selection
path_batches_follow_correction_full_history_fallback
range_path_batches_stay_disabled_at_repository_boundaries
path_cache_misses_and_empty_root_keep_distinct_contracts
merge_path_batch_config_failure_disables_optimization
path_batch_does_not_swallow_interrupt
shared_values_leave_message_file_and_waiver_calls_unchanged
```

**変異対応表：期待 kill。赤は未実証です。**
各 nodeid の共通接頭辞は `orchestrator/tests/test_check_ai_provenance.py::`。

| 変異 | 赤になる想定の test nodeid 末尾 | 種別・赤理由 |
|---|---|---|
| M-1 | `test_ancestry_parent_rows_match_show_parents` | 呼び出し契約：2／4 親の tuple が `%P` と不一致 |
| M-2 | `test_parent_cache_invalid_rows_fall_back[outside]` | 呼び出し契約：親表破棄・`%P` fallback が欠落 |
| M-3 | `test_batch_nonmerge_always_emits_empty_headers` | 呼び出し契約：exact argv・空差分見出しが不一致 |
| M-4 | `test_batch_nonmerge_invalid_output_restores_public_result[missing]` | 判定差：部分辞書により先頭の Codex author 違反が消失 |
| M-5 | `test_batch_nonmerge_hex_paths_discard_entire_batch` | 呼び出し契約：末尾を含む hex path で全体 fallback が欠落 |
| M-6 | `test_batch_merge_ignore_submodules_uses_legacy_verdict` | 判定差：ignore 設定下の gitlink merge が拒否へ変化 |
| M-7 | `test_batch_merge_late_failure_discards_all_parent_batches` | 判定差＋呼び出し契約：違反消失・全親 legacy 取得が欠落 |
| M-8 | `test_shared_agent_values_stay_with_their_commit` | 判定差：混在 message の欠落／author finding が変化 |
| M-9 | `test_agent_values_none_and_empty_are_distinct` | 呼び出し契約：取得済み `[]` を再 parse |

**静的に確認した波及・制約**

- 共有 fixture `_init_repo`、`_batch_raw_commit`、registry helper、既存 merge fixture は変更せず再利用。
- 制約として、既存 message subprocess 計数、公開出力比較、policy／waiver literal、parser の cwd・divider、warm receipt canary・correction 再選択を確認。新規テストで path 計数と authoritative 公開出力比較を追加。
- 所有外 caller：`dev_wave_land.py`、`dev_wave_wait.py`、`task_run_check.py`、Pegasus dispatcher は CLI・rc 契約に依存。`main` は不変です。`mutation_harness.py` の共通契約、`codex_reasoning_ab.py` の歴史的 hash／numstat fixture も変更していません。
- 指定 consumer tests：`test_dev_wave_land.py`、`test_dev_wave_wait.py`、`test_pegasus_dispatch_compute.py`、`test_t2337_dispatch_timeout_overrides.py` は実行・dispatch 契約、`test_hooks.py`／`test_check_docs.py` は sanctioned path・literal pin、`test_codex_reasoning_ab.py` は固定比較 fixture、`test_dev_waves_git_state.py` は trailer 正規表現、`test_resume_gate_acceptance_boundary.py` は CLI fixture に依存します。静的確認のみで、consumer test は未実走です。

未完了は、追加・既存テストの実走、M-1〜M-9 の実測 kill、親担当の固定全史比較と性能測定です。したがって判定・公開出力の完全一致や速度改善は、まだ実証済みとはしていません。
