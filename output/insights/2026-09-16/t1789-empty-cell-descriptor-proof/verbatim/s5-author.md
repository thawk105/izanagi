## 変更内容

- [s8c_acceptance_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof/orchestrator/campaign/s8c_acceptance_receipt.py:2053)：production変更は2053〜2060行。指定位置にplan v2の判定を逐語追加。
- [test_s8c_acceptance_receipt_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1789-empty-cell-descriptor-proof/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:931)：指定順序で3関数・4 node追加。

## 追加した node

```text
orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_partial_receipt_cannot_claim_complete_without_descriptor_proof_even_with_c02[v2]
orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_partial_receipt_cannot_claim_complete_without_descriptor_proof_even_with_c02[v5]
orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_partial_receipt_cannot_hide_conflicting_descriptor_by_dropping_cells
orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_partial_receipt_with_c02_and_no_cells_passes_current_capability
```

## 自己確認

- **直接呼出し: PASS** — 追加4 nodeと既存のC02欠落テスト、計5件。
- 新判定を無効化した一時コピー：負例3件は期待どおりFAIL（DID NOT RAISE）、正例はPASS。
- AST構文・関数名重複・`git diff --check`：PASS。
- `.t1789-selfcheck/`：削除確認済み。
- pytest、全体テスト、meta-testの実走：未実施。

## 波及の静的列挙

指定3語を`orchestrator/tests/`で検索した該当ファイル：

- `test_s8c_acceptance_receipt_v2.py`：所有テストと既存helper。
- `test_s8c_acceptance_receipt.py`：既存verifier consumer。
- `test_trial_registry.py`：complete受入・build report受入のverifier呼出し。
- `test_layer3_report.py`：共有helper `_verified_non_certifying_receipt`と、そのconsumer 2件。

`receipt-arm-binding`と新文言の所有外一致はありません。production側の間接consumerは`layer3_report.py`の`require_current_verified_receipt`呼出しです。

## 制約 meta-test

- `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`：`_git`のsubprocess呼出し箇所を1件に固定。変更なし。
- `test_plain_runner_coverage.py`：テストファイルの自走harness／allowlist整合。既存harnessを維持。
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`：duration台帳のcollectionカバー率制約。台帳は未変更。
- 対象ファイル固有のnode名・件数固定は検索範囲で見つかりませんでした。

## 総括

plan v2を実装し、直接呼出しと判定無効化の対照確認を完了しました。変更は指定2ファイルのみ。docs編集・worktreeへの禁止Git操作・commitは行っていません。