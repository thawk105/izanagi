---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2780-codex-recovery
seq: 1
---

## 再発

### F47

- **再発: 2026-09-18** — T-2780引継ぎで親が全史監査job6403をQUE中にqdelした。ローカル実行可能という再観測を理由にしたが、runbook §7.6の「手動qdelは最後の手段」「解除はユーザー手番」の帰結を操作前に確認しなかった。dispatcherはcompute-marker-not-observedでsubmission-disabled.jsonを作成した。ラッチを保持し、最終受入・land・清掃は人間による確認後へ止める。既存の禁止・解除契約を変えない。

## supersede 追記

- F1027 **supersede: 2026-09-18** — T-2780でHYDRATE_PYの選択と実呼出配線、契約testを実装した。job5905はhydrate・patched build・verifier・discriminator finalizationを終端accounting付きで完走しno-g2/rc0。正式変異job6360で素のpython3への差戻しを検出し、version比較削除とrejected記録削除はsensitivityとして区別した。証拠はoutput/insights/2026-09-18/t2780-mocc-pilot-discriminator/。
