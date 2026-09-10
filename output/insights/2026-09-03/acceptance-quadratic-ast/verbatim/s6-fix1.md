## 所見の対応表

| 所見 | 状態 | 変更箇所 |
|---|---|---|
| 修正 1 | partial（実装済み・未実走） | [test_p3_b4_wiring_probe.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:319)、`:321-350` |
| 修正 2 | partial（実装済み・未実走） | [test_p3_b4_wiring_probe.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-quadratic-ast/orchestrator/tests/test_p3_b4_wiring_probe.py:238) |

## 実走したもの

- `test_source_segment_helper_matches_stdlib_at_boundaries`: 実装済み・未実走
- `test_analyze_source_splits_each_module_exactly_once`: 実装済み・未実走

`tools/run_tests.py` は dispatch infrastructure failure（rc=16、`child_started=false`）で停止しました。対象ファイルの構文解析と `git diff --check` は成功しています。

## 受理集合への影響

受理集合は広げていません。修正 1 は全4回の helper 入力が唯一の splitter 返却 object と同一であることを固定し、修正 2 は三つの非改行文字を stdlib 比較へ追加しました。既存 assert は維持しています。

## 総括

- 指定された二修正を対象テストファイルだけに実装しました。
- 製品コードへの書き込みは行っていません。
- 期待値の変更、緩和、skip、削除はありません。
- commit と index 操作は行っていません。