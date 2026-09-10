## 付けた ID の一覧

### `test_backlog_guard_carry_candidate_parse_break_is_positive_control`

| 旧 ID | 新 ID |
|---|---|
| `[T-999] (073)` | `leading-zero` |
| `[T-999] (73 )` | `trailing-space` |
| `[T-999] 変わらず ( (73) 参照)` | `legacy-inner-space` |

### `test_backlog_guard_carry_target_index_states_are_distinct`

| 旧 ID | 新 ID |
|---|---|
| `missing-missing-索引 key 不在-key 不在-absent_labels0-absent_details0` | `index-key-missing` |
| `none-None-索引値 None-値 None (section 抽出対象外)-absent_labels1-absent_details1` | `index-value-none` |
| `empty-target_value2-索引値空集合-空集合 (次の一手が空)-absent_labels2-absent_details2` | `index-value-empty` |

### `test_backlog_guard_carry_index_failures_count_every_occurrence`

| 旧 ID | 新 ID |
|---|---|
| `missing-参照先不在-全域番号 universe に実在しない` | `target-missing` |
| `key-索引 key 不在-次の一手索引が key 不在` | `index-key-missing` |
| `none-索引値 None-値 None (section 抽出対象外)` | `index-value-none` |
| `empty-索引値空集合-空集合 (次の一手が空)` | `index-value-empty` |

## 値を変えていない根拠

各 case を同じ値・同じ順番のまま `pytest.param(..., id="<ascii-id>")` で包んだだけです。差分上、assertion、期待値、被覆、case 数は変更されていません。変更は対象ファイルの上記10個の表示 ID のみです。

## 実走した検査

- `git diff --check -- orchestrator/tests/test_check_docs.py`: 成功
- 指定3関数、計10 case: 未実走。`tools/run_tests.py` が Pegasus queue preflight の `qstat -Q` で `rc=16` となり、`child_started=false` で停止しました。
- 全552件: 未実走
- commit、index 操作は実施していません。

## 総括

指定された10 caseへ英小文字・数字・ハイフンだけの明示 ID を追加しました。  
パラメータ値、assertion、case 数はすべて維持しています。  
同 wave のほかの新設 parametrized test に非 ASCII の自動 ID はありませんでした。  
変更ファイルは [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1219-carry-same-id/orchestrator/tests/test_check_docs.py:11091) のみです。