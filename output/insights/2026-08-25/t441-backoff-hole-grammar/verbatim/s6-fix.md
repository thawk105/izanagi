実装には着手せず停止しました。F1〜F3 の要求と「既存テスト期待値を変更しない。例外は F7 の nesting 境界だけ」が両立しないためです。

具体的な衝突は次のとおりです。

- [test_p3_s4_loop.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:182) は `double now_backoff = 20.0;` の受理を固定していますが、F3 は拒否を要求します。
- [test_p3_s4_loop.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:302) は `1e2`、`001`、`20.0f` と宣言後の `helper(now_backoff)` の受理を固定していますが、F2/F3 は拒否を要求します。
- [test_p3_s4_loop.py:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t441-backoff-hole-grammar/orchestrator/tests/test_p3_s4_loop.py:322) は `001`、`1.0f`、`1..0`、`20_backoff` が帰属検査と grammar を通ることを固定していますが、F1/F3 は fail-closed を要求します。

続行には、これら F1〜F3 と直接衝突する期待値も変更可能とする明示的な例外が必要です。worktree は clean で、編集・`git add`・commit は行っていません。

## 総括

| 所見 | 状態 | 現状 |
|---|---|---|
| F1 | partial | pp-number の接頭辞一致が未修正 |
| F2 | partial | 直接代入だけを検出し、宣言後の全出現拒否は未実装 |
| F3 | regressed | 非正準数値表記を受理する期待値と衝突 |
| F4 | partial | 括弧付き declarator が未修正 |
| F5 | partial | 入れ子宣言・attribute 付き label が未修正 |
| F6 | regressed | Unicode 空白を separator として受理 |
| F7 | partial | raw byte cap は存在するが token・nesting・code point 条件が未是正 |
| F8 | regressed | production preflight が例外終了する |
| F9 | regressed | critic loader が rule ID を失う |
| F10 | partial |候補内容の一部だけ否定 assert があり、入力長まで固定されていない |
| F11 | partial | 合成経路・優先順位・境界検査が不足 |
| F12 | partial | 32 形の形別期待値コーパスが未実装 |
| F13 | partial | 別名・関数値経由と positive control が未実装 |

- 実走 nodeid: なし。停止条件に従いテスト未実走。
- 未解決: F1〜F13 全件。特に F1〜F3 は現行期待値との指示衝突。
- 独自判断: なし。
- 静的な波及先:
  - `validate_backoff_implementation` と `assert_value_literal_consistent` の合成経路
  - `quarantine` および backoff の `run_one_iteration`
  - reject WAL、`load_diff_rejections`、`render_rejections`
  - campaign 配下の coder text materialization 閉包検査
  - trigger/sort caller は exact marker 分岐のため本来非影響対象
  - 共有 fixture `_TEMPLATE` と既存 backoff grammar/resource tests