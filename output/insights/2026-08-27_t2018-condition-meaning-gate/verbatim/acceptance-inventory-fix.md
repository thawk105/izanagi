## 総括

受入赤の原因だった未分類 process site を、explicit non-CCBench inventory へ exact 1 件追加しました。

## Fix

[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2018-acceptance-inventory-fix/orchestrator/tests/test_ccbench_spawn_sites.py:99) に `_run_process` を登録し、固定 compiler argv／生成 decoder argv、shell なし、120 秒 timeout の分類理由を記録しました。

## 受理と拒否

既存 site 集合を保持したまま、condition meaning gate の 1 site を受理します。未分類の新規 process site は引き続き両テストで拒否されます。

## 検査

指定 2 node は実装済み・未実走です。`tools/run_tests.py` の通常経路と `--force-dispatch` 経路を試しましたが、双方とも `qstat -Q preflight rc=1`、`rc=16`、child 未起動でした。直接 pytest には迂回していません。

## 所有

手動編集は指定されたテストファイル 1 件のみです。production、docs、fixture、driver、commit、git add、merge、rebase は変更・実行していません。指定 runner は失敗時の dispatch receipt を `output/pegasus-dispatch/` に自動生成しました。
