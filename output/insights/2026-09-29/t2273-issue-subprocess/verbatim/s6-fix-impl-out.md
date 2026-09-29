## 修正

[s8b_holdout_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/campaign/s8b_holdout_freeze.py:504) の共通判定 cache に判定時の text object を保持し、現在の text と `is` で一致するときだけ結果を再利用するよう修正しました。[正例 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1026) は proxy の背後を書き換えた後の別式で hit と reference との report bytes 一致を確認します。

## test

対象 file 全体は **169 passed、2 skipped**。関連する oracle test も 1 passed でした。既存 test の期待値は変更していません。

## 変異の確認

M7 は新 test の [hit assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1043) だけで赤になりました。M1〜M6 も各登録番人で赤、P0 は対象 file 全体で **169 passed、2 skipped** でした。全変異を復元済みです。M6 の通常時の共通判定回数は **2** のままです。

## 実走

変更 2 ファイルの自己汚染検査は両 holdout とも conjunction **0 件**。`check_codex_agents.py`、`check_docs.py`、`git diff --check` も通過しました。

## 未実走・懸念

関連 suite の全件実走はしていません。追加 node の所要時間台帳への登録は所有 path 外のため未実施です。既存 growth hold の 2 件は指示どおり skip のままです。

## 総括

変更は指定された 2 ファイルのみで、commit は作成していません。