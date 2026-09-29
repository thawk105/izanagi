## 総括

対象テストで、実行後に `ContrastLedger(ledger.root)` を読み直すよう修正しました。stock だけに `slot-start` があり、seed には無いことに加え、`series-end` の理由が `stock-unestablished` であることを検査します。

## 変更 file と行数

- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_p3_s4_loop_policy.py:128)：3 行追加

## 実装した interface

変更なし。driver は変更していません。

## テスト

`test_job1_stops_before_seed_slots_when_stock_is_not_certified` を `tools/run_tests.py` で起動しましたが、`qstat -Q` の事前確認で dispatch が失敗しました（rc=16、子プロセス未起動）。**実装済み・未実走**です。

## 所有外への波及

所有外の caller、共有 fixture、consumer test、inventory への変更なし。

## 未解決・報告して止めたこと

テストの実走結果は未確認です。