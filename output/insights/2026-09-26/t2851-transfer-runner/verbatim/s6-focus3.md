## 総括

**GO。** G-1 は **closed**。凍結入力から実 verifier まで CCBench source root が渡され、verifier の認定条件は変更されていません。実機 smoke の再走は未実施です。

## 対応表

| 対象 | 判定 | 根拠 |
|---|---|---|
| G-1 | closed | `trace_ccbench_root` は必須の絶対 path で、`binaries` とともに凍結 hash の対象です。[runner:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/campaign/t2851_transfer_runner.py:199)、[runner:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/campaign/t2851_transfer_runner.py:261)。verify 記録に写し、`ccbench_root` として渡します。[runner:489](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/campaign/t2851_transfer_runner.py:489)、[runner:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/campaign/t2851_transfer_runner.py:525)。verifier の `clean`・`certified` 条件に差分はありません。[model:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/verifier/model.py:501)、[model:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/verifier/model.py:570)。 |
| 正負例 | 妥当 | 新 test は trace 生成だけを fixture 化し、`verify_candidate` の既定の実 verifier を通します。[test:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/tests/test_t2851_transfer_runner.py:270)、[runner:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/campaign/t2851_transfer_runner.py:474)。同じ trace・binary・witness で source root だけを変更し、正例は `certified`、存在しない path の負例は `indeterminate` を確認しています。[test:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/tests/test_t2851_transfer_runner.py:284)。 |
| compile 元との一致 | nit | runner は path と binary の対応までは証明しません。誤った source tree を指定すると認定結果を誤らせ得ますが、発効束 §13.1 の CCBench pin・patch・configure の固定で担える運用上の束縛です。[runner:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/campaign/t2851_transfer_runner.py:199)、[runner:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-unseen-transfer-runner/orchestrator/campaign/t2851_transfer_runner.py:312)。 |

## 新規所見

fix3 によって主要表の値・分類・受理集合へ影響する must-fix／should の新規欠陥は見つかりませんでした。