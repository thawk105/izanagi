---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t2048-floor-budget-drift
seq: 1
title: [T-2048] floor予約予算driftを現行authorityへ揃えた (コード + docs、branch worktree-dev-wave-t2048-floor-budget-drift、変異matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- schedulerへ渡る要求宣言はPBS directiveの36000秒、policyは期待値・receipt値、qstatはdriverが束縛する実効limitだった。driver calculatorは12-cell subtotal 28200へ共有dependency prebuild 1800を加えて`required_s=30000`、finalize reserve 600込みのminimum envelope 30600を要求する。shell/runbookの旧28200/28800だけが[T-1128]以前のdriftだった。
- D87の歴史値、scheduler/policy/calculator/protocol/freeze/official guardは変更していない。R33 pinはoracle/n-pilotの別2ファイルで、本項は正式測定の凍結契約を変更しない。shell bytes変更後の将来投入は新しいscript hash/receipt/測定世代になる。
- 段6 reviewで説明変異を既存runtime testが観測しない欠陥をreal/must-fixとして採用し、D95 Codex fixが既存floor-tools testへfocused oracleを追加した。初回baseline赤はblock終端が後続実行行を含むtest bugで、fix round 2が値・受理意味を変えず閉じた。
- 変異matrixは固定commit `57348d7a6`でbaseline 2/2 passed、KILLED 3、SURVIVED/MISMATCH/TIMEOUT 0。pre-record受入全走は18248 collected、18187 passed、61 skipped、赤0、`child-green` (tested main `254b0f506`、tested tip `b6a373575`)。
- 実装commit `02a0d5218`、test fix `57348d7a6`、受入前main取込 `b6a373575`。`check_docs.py` rc=0、各実装commit後の全履歴provenanceは新規違反なし。正本とraw receiptは `output/insights/2026-08-28_t2048-floor-budget-drift/README.md` が索引する。
- エージェント工数: Codex子9本 (plan 1、consult 2、author 1、review 2、fix 2、focus 1)。親がauthority再導出、裁定、統合、変異、受入、記録を担当した。

## 次の一手差分

### 完了

- [T-2048] floor予約予算のdriftを、scheduler request 36000とdriver minimum envelope 30600の役割を分けた現行authorityへ揃え、focused oracleと変異3件で固定した。
  remaining: none
  base: e3587b882edd59afaff27d7a9e7f6310d06fe1c954ba43439ecff4e477de3de3
