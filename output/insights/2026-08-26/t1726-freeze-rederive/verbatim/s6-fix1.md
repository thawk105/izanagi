F1〜F3を指定 2 ファイル内で修正しました。既存テストの期待値は変更していません。

- F1: resolver 出力を H1=80、H2=20、swapped 反転、off=50、skew=0.9、rmw=0、records=1,000,000、threads=48 の独立 literal に照合。
- F2: lazy import・loader・resolver の予期しない例外を `[receipt-freeze-arm-binding]` の `AcceptanceReceiptError` に変換。既存の `AcceptanceReceiptError` はそのまま伝播。
- F3: clean interpreter cold-import test と AST test を追加し、test module の authority import も関数ローカル化。

静的検査は以下を通過しました。

- 対象 2 ファイルの AST 構文解析
- production 単体 cold-import probe。指定 4 module は `sys.modules` に出現せず
- `git diff --check`
- `git status --short`: 指定 2 ファイルのみ、staged 変更なし

動的 test は実装済み・未実走です。以下の 5 nodeid を runner 経由で要求しましたが、Pegasus の `qstat -Q` preflight が `rc=1`、`child_started=false` で終了しました。

- `test_receipt_import_is_cold_for_arm_authority_modules`
- `test_arm_authority_imports_are_function_local`
- `test_lazy_authority_import_failure_is_acceptance_receipt_error`
- `test_resolver_exception_contract_is_fail_closed`
- `test_v2_producer_equivalent_full_verify_drops_only_c02`

波及可能性の静的確認:

- `layer3_report` は `AcceptanceReceiptError` を捕捉するため、F2で再検証 API の契約が整合。
- `trial_registry` 発行物を検証する既存正例は v2/v3 再導出の影響対象。未実走。
- `test_s8c_acceptance_receipt.py` と `test_layer3_report.py` の実 verifier fixture は v1 のため、新 gate 対象外。
- reflux baseline は serialized bytes を比較し、schema・発行 bytes は今回変更していない。
- target-local `_fixture` の全利用箇所に literal assertion が波及し、resolver drift を意図どおり早期検出する。

## 総括

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | resolver 非依存の固定 authority literal assertion を fixture に追加 |
| F2 | closed | 予期しない例外を fail-closed 変換し、既存 `AcceptanceReceiptError` は再変換せず伝播 |
| F3 | closed | clean interpreter test、AST test、test-side local import 化を追加 |

変更ファイル:

- [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/campaign/s8c_acceptance_receipt.py:696)
- [test_s8c_acceptance_receipt_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1726-freeze-rederive/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:76)

実走状況: nodeid の緑 0 件。runner infrastructure failure により実装済み・未実走です。残った test 赤は観測されていませんが、動的結果は未確定です。`git add`、`git commit` は行っていません。