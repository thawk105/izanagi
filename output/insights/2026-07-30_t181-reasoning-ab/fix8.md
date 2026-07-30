## 総括

分類名 `zero_component_total_only` を導入しました。[実装](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py) と [テスト](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py) の2ファイルだけを編集し、docs・ledger・commit には触れていません。

非 fatal になるのは、`last_token_usage` の input・cached input・cache write・output・reasoning がすべて厳密に0で、`total_tokens` だけが正の場合に限定しました。receipt は分類名、`count`、該当 `indexes` を常時出力します。aggregate は総件数と max/high × POS/NEG の件数を公開し、count・index・usage source の欠落や不整合を fail-closed で拒否します。原因や CLI の性質は断定していません。

構成要素が非ゼロの identity mismatch は従来どおり rc=25 です。`total_token_usage` には例外を適用せず、最後の累積値が同じ形でも rc=25 を維持しました。`cli_reported` の導出方法も変更していません。total も0の all-zero usage は本分類に含めず、既存の正トークン消費 gate で拒否されます。

追加した test node は次の9件です。

- `test_zero_component_total_only_per_turn_is_nonfatal_and_reported`
- `test_nonzero_component_last_usage_identity_mismatch_remains_fatal`
- `test_final_cumulative_zero_component_total_only_remains_fatal`
- `test_all_null_token_info_is_rejected`
- `test_final_cumulative_usage_null_is_rejected`
- `test_non_object_rollout_row_is_rejected`
- `test_all_zero_usage_is_distinct_and_rejected`
- `test_zero_component_total_only_aggregate_counts_by_arm_and_case`
- `test_zero_component_total_only_count_is_required_for_aggregate`

`python3 -m py_compile` と `git diff --check` は rc=0 でした。ユーザー指示に従い pytest、`tools/run_tests.py`、実 snapshot build、`supervise-pair` は一切実行していません。したがって、既存180 test や追加テストについて緑とは主張しません。実測は親の計算ノード実行が必要です。