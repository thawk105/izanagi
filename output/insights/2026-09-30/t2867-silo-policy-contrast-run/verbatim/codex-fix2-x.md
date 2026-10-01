## 総括

再起動時の系列照合を、順序に依存しない重複なしの集合比較へ修正しました。既存の 12 試験の期待値は変更していません。

## 変更 file と行数

- [contrast_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/contrast_runner.py:140): 1 行変更
- [test_contrast_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-run-author-x/scratch/t2867_contrast_runner/test_contrast_runner.py:128): 17 行追加

## 対応

追加試験: `test_restart_accepts_unsorted_schedule_and_rejects_different_series`。辞書順でない schedule から保存した state は同じ config での再起動時に受理され、処理順も schedule どおりです。系列名の集合が異なる config は拒否されます。

## 試験

`python3 scratch/t2867_contrast_runner/test_contrast_runner.py -v`: **13 試験すべて成功**（7.548 秒）。

## 未解決・報告して止めたこと

なし。