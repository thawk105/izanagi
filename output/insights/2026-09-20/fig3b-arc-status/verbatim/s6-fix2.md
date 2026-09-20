## 変更

[test_plot_arc_status.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig3b-unit-impl/orchestrator/tests/test_plot_arc_status.py:230) の指定2点だけを修正しました。

- 230行: `_cli` の環境辞書に `"PYTHONDONTWRITEBYTECODE": "1"` を追加。
- 273〜274行: 指定どおりの `__main__` harness を追加。

## 検査

- (a) bytecode guard checker: **rc=0**。
- (b) `_self_runnable`: **True**。`test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` も直接実行し、**1件成功**。
- (c) 指定の `probe-fig3b/run_tests_direct.py`: **30件成功、6.760秒**。実走 nodeid は `orchestrator/tests/test_plot_arc_status.py::test_t1_*`〜`test_t8_*`（T3の22ケース、T5の`[overlap]`・`[escape]`を含む）。描画は合計7回。
- `git diff --check`: 成功。

## 総括

指定の修正・検査は完了しました。期待値・node名は変更せず、変更ファイルは所有pathの1本だけです。commit は作成していません。