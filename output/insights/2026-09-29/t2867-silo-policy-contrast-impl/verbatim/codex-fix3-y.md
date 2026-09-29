## 総括

N4 の台帳側を修正しました。job 1 の stock の最後の attempt が `certified` でも `machine-failure` でもなければ、seed の結果を待たずに `stock-unestablished` で終了し、その後の `next_unit` は `None` を返します。既存テストの期待値は変更していません。

## 変更 file と行数

- [silo_policy_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/orchestrator/campaign/silo_policy_contrast.py:150): 5 行追加、4 行削除
- [test_silo_policy_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-y/orchestrator/tests/test_silo_policy_contrast.py:97): 14 行追加

## 実装した interface

`close_series_if_done(ledger) -> str | None` の終了条件を変更しました。終了時に既存の `series-end` event へ `reason='stock-unestablished'` を記録します。signature と event 名は変更していません。

## テスト

`test_stock_unestablished_closes_without_seed_results` を追加し、stock の再試行後に seed 結果なしで終了することを検査します。`python3 tools/run_tests.py orchestrator/tests/test_silo_policy_contrast.py` は試しましたが、dispatch 前の `qstat -Q` が失敗したため**未実走**です。`git diff --check` は通過しました。

## 所有外への波及

所有外の caller・fixture は変更していません。指定された inventory 系テストを静的に検索し、今回の2ファイルを列挙する項目は見つかりませんでした。

## 未解決・報告して止めたこと

テストの実行結果は未確認です。dispatch 基盤が利用可能になった後に実走が必要です。