単位 A の実装を追加しました。既存ファイル・docs は変更せず、commit していません。

- [silo_policy_ir.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-a/orchestrator/campaign/silo_policy_ir.py)：型付き IR、検証、入口状態の保存と同時更新、決定的描画、16 点列挙、parity 割付、正式検査 CLI。
- [test_silo_policy_ir.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-a/orchestrator/tests/test_silo_policy_ir.py)：構造・型境界、全点 grammar／compile、飽和演算・状態更新・因子の実行検査。

単位 B 向け interface は `enumerate_recon() -> tuple[ReconCase, ...]`。各要素は `case_id`、LSRM 順の `factors`、`ir` を持ちます。`next_state=None` は全 field 保持です。

**実走結果**

指定の login 正式検査を pegasus02 で **1 回実行し rc=0**。結果は [ir-check.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2863-unit-a/ir-check.json)（commit 対象外）です。

| 検査 | 結果 |
|---|---|
| grammar／単独 TU compile | 各 17/17 受理 |
| UBSan | 20/20 通過（17 方策＋負対照 3 種） |
| harness 呼出し | 各方策 1,904 回 |
| compiler | GCC 12.3.0 |
| Python 構文検査・Codex agents・docs | rc=0 |

**pytest は実装済み・未実走です。** 以下を `tools/run_tests.py` 経由で起動しましたが、すべて `qstat -Q preflight rc=1` により runner rc=16、子未起動でした。緑の pytest nodeid はありません。

- `orchestrator/tests/test_silo_policy_ir.py` 全件。
- `orchestrator/tests/test_plain_runner_coverage.py` 全件。
- `orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
- `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`

後者 3 件は、test file 集合・登録・所要台帳への波及を `rg` で調べて選びました。

静的な波及先は、単位 B の新 caller、既存 compile helper、上記メタテストです。共有 fixture、grammar、4 段検査、骨格上限、既存 subprocess 登録は変更していません。abort0 は定数出力だけで局所変数が不要なため、既存 `abort0.cpp` との **bytes 一致**を期待するテストにしました（未実走）。

## 総括

- 変更：所有する新規 Python 2 ファイルのみ。commit なし。
- 正式検査：rc=0、17 点受理、UBSan 20/20 通過。
- 記録：`ir-check.json` を親へ引継ぎ。
- 未実走：新規 pytest と列挙したメタテスト。dispatch インフラ失敗。
- リスク：飽和境界・同時更新の専用実行テストは未確認。
- 単位 A は実装済みですが、検査完了・closed とはしていません。