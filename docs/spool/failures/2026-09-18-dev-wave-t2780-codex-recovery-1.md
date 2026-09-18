---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2780-codex-recovery
seq: 1
---

## supersede 追記

- F1027 **supersede: 2026-09-18** — T-2780でHYDRATE_PYの選択と実呼出配線、契約testを実装した。job5905はhydrate・patched build・verifier・discriminator finalizationを終端accounting付きで完走しno-g2/rc0。正式変異job6360で素のpython3への差戻しを検出し、version比較削除とrejected記録削除はsensitivityとして区別した。証拠はoutput/insights/2026-09-18/t2780-mocc-pilot-discriminator/。
