T1・T2・T3 の修正を U-A 所有4ファイルに実装しました。試験を起動できなかったため、契約に従い **closed ではなく partial（実装済み・未実走）** と報告します。

| 所見 | 状態 | 修正内容 |
|---|---|---|
| T1 | partial | campaign ID ごとに fixture の layout を分け、異なる config 間で lock を共有しない |
| T2 | partial | 実際に評価へ渡す context の authority だけを検査。既存 `default_cfg()` は変更なし |
| T3 | partial | zstd 起動専用関数を抽出し、障害注入を限定。spawn inventory も追従 |

production の受理・拒否条件は変更していません。試験では、T1 の誤った lock 衝突、T2 の初期 context への誤要求、T3 の Git 起動への誤注入を除きました。

実走した nodeid は **なし**です。試行したコマンドは以下です。

```bash
PYTHONPATH=. timeout 300 python3 -m pytest -q -p no:cacheprovider -rf orchestrator/tests/test_t2849_loop_entry.py orchestrator/tests/test_t2853_trace_preservation.py
python3 tools/run_tests.py -q -p no:cacheprovider orchestrator/tests/test_ccbench_spawn_sites.py
```

前者は PreToolUse hook が拒否。後者は `qstat -Q` preflight 失敗で rc=16、child 未起動でした。`git diff --check` は成功しています。

## 総括

- 差分：production **+7/−2行**、test **+15/−9行**。新規ファイル・commit なし。
- 所有外への波及：共有 fixture の変更なし。検索で確認した spawn inventory は所有範囲内で更新済み。所有外の必要変更なし。
- 未実走：対象2ファイル、spawn inventory、変異 M1〜M7。親の焦点走で確認が必要です。

変異対応は以下のとおりです。すべて **kill 未実測**です。`E` は `orchestrator/tests/test_t2849_loop_entry.py`、`P` は `orchestrator/tests/test_t2853_trace_preservation.py` を示します。

| 変異 | 登録位置の関数 | FAIL 期待 nodeid |
|---|---|---|
| M1 | `main` | `E::test_harness_machine_slot_accepted[True/False]` |
| M2 | `_run_stock_control_resolved` | `E::test_read_heavy_reference_exact_flags[read-heavy/balanced/write-heavy]` |
| M3 | `main` | `E::test_reference_rejected_outside_harness[b5]` |
| M4 | `_run_one_repetition` | `P::test_archive_before_cleanup` |
| M5 | `_run_one_repetition` | `P::test_failure_retains_original[spawn/nonzero/inventory/relative]` |
| M6 | `_run_one_repetition` | `P::test_preservation_error_does_not_replace_result` |
| M7 | `_run_one_repetition` | `P::test_unset_env_unchanged` |

実行制約：自動 PreToolUse hook は、Pegasus ログインノードでの直接 pytest 起動を重量処理として拒否しました。回避実行はしていません。