## 総括

job 1 で stock の結果が `certified` 以外なら、その `slot-result` を記録して単位を終えるようにしました。残りの seed slot は開始せず、既存の `close_series_if_done` 呼び出しへ進みます。既存テストの期待値は変更していません。

## 変更 file と行数

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/campaign/p3_s4_loop_policy.py:871): 2 行追加
- [test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-x/orchestrator/tests/test_p3_s4_loop_policy.py:101): 32 行追加

## 実装した interface

`run_contrast_unit(...)` の signature は変更していません。stock 不成立時は `stock-0` の `slot-start` と `slot-result` を記録し、`seed-*` の `slot-start` を書かずに終了判定を呼びます。

## テスト

`test_job1_stops_before_seed_slots_when_stock_is_not_certified` を追加しました。`measure_slot` を計算実行の seam として差し替え、stock 不成立時に seed が開始されないことを検査します。`run_tests.py` は Pegasus の `qstat -Q` preflight で `rc=16` となり、**テスト本体は未実走**です。両変更 file の構文解析と `git diff --check` は成功しました。

## 所有外への波及

終了理由 `stock-unestablished` の記録条件は所有外の `silo_policy_contrast.py` に依存します。関連する既存の inventory test 群を静的に確認し、今回の変更による caller や file 集合の追加はありません。

## 未解決・報告して止めたこと

Pegasus dispatch 障害により、追加テストの実走結果はありません。現時点の台帳実装は stock だけの結果では `stock-unestablished` を記録しないため、その条件変更は所有外の担当に必要です。