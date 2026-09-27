## 総括

**NO-GO。静的検査のみで、テスト・計算ノード実走は行っていません。**

- fix 1 は F1 の変数上書きと RA1 の fixture 欠落をコード上で修正しています。
- `_prepare_evaluation_core` では、反復変数に上書きされた後の `workload` を build・bench 用に参照する箇所は残っていません。
- **must-fix:** driver の `evaluate` は `numactl` を渡さず、既定値 `None` が認可ゲートで必ず拒否されます。期待する trace reject の WAL まで到達しません。
- `authorization.contract.numactl` を渡し、計算ノードで `trace-witness-unsupported-workload`、COMMIT 不在、bench 未起動を実測してください。
- job・verify・bench・probe の照合は追加されていますが、実機依存の結果は未確認です。

## 対応表

| 所見 ID | 判定 | 根拠 file:line | 残る作業 |
|---|---|---|---|
| F1 | closed | [pipeline.py:1744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:1744)、[pipeline.py:2736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:2736)、[pipeline.py:2813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:2813) | 実測テスト。上書き後の `workload` 参照は correctness pass の処理と `workload.reps` のみ。build 3 箇所、screening、prepared は保存した別名を使用。 |
| RA1 | closed | [test_campaign.py:13734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/tests/test_campaign.py:13734) | fixture の実測テスト。`workload="ycsb"` が追加され、期待値変更はありません。 |
| RA2 / RB1 | partial | [smoke_driver_d.py:195](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:195)、[smoke_driver_d.py:332](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:332) | evaluate と WAL 照合は追加済み。ただし下記 FA1 を直して実走が必要。 |
| RA3 | closed | [smoke_driver_d.py:257](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:257)、[smoke_driver_d.py:261](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:261)、[smoke_driver_d.py:301](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:301) | 裁定で認めた HEAD・clean status・再取得手順を記録し、verify を checkout 生存中に実行する構成。 |
| RA4 / RB2 | partial | [smoke_driver_d.py:293](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:293)、[smoke_driver_d.py:303](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:303)、[smoke_driver_d.py:311](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:311)、[smoke_driver_d.py:339](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:339) | 指定された結果照合と非 0 終了は実装済み。evaluate の到達不能を修正し、実機結果で確認。 |
| RA5 | partial | [smoke_driver_d.py:123](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:123)、[smoke_driver_d.py:144](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:144) | composite 単独成功・既知 PID・前後の `_probe` を照合する構成。PATH と実行中プロセスに依存するため実機確認が必要。 |

fix 1 の差分では、YCSB の build/bench 引数と成果物 payload の条件を変えておらず、既存テストの期待値変更も見当たりません。

## 新規所見

| ID | 重大度 | 根拠 | 放置時の影響 | 修正案 |
|---|---|---|---|---|
| FA1 | **must-fix** | [smoke_driver_d.py:195](/work/SFC/tanab/tmp/dev-wave-t2866-2026-09-27/smoke_driver_d.py:195) は `numactl` を省略。[pipeline.py:3075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/pipeline.py:3075) の既定値は `None`、[execution_guard.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2866-tpcc-campaign/orchestrator/campaign/execution_guard.py:125) は list/tuple を必須とする。 | 計算ノードでも認可ゲートで例外となり、期待する TPC-C trace reject の WAL を生成できない。 | `pipeline.evaluate(..., numactl=authorization.contract.numactl, ...)` とし、実機で照合する。 |