---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1539-insights-retention
seq: 1
title: [T-1539] output/insights retention棚卸しを判定不能precheckで安全停止した (record-only、branch worktree-dev-wave-t1539-insights-retention、削除0)
---

## 本文

- audit pin `402a5752` の母集合は8,963 files / 67,219,393 bytes。元裁定の8,928 files / 66,186,605 bytesから35 files増えた。
- RuleOpsは7,971 itemsを出したが、非UTF-8 992 pathsを一覧から落とす。candidate=0、human_approved=falseは削除安全でも全件KEEPでもない。
- 実KEEP controlは、receiptがpath/digest/sizeをpinする0-byte rawと、現行phaseが直接参照するbacklog正本。実DELETE controlは得られなかった。
- 起動時のClaude 7/Codex 5 worktreeを照合し、branch固有insightを持つClaude 2本を含め全稼働成果物を除外した。監査中にも全registryとbranch固有pathはdriftした。
- 段3の2レンズは、親の「全8,963件KEEP / DELETE 0」という過大分類と、承認をpath述語へ混ぜた循環を独立にrealとした。裁定は「削除適格と立証済みexact path 0、全件未分類のため非変更」へ修正した。
- persistent checker/scriptは実DELETE入力が0でtrue側を検証できず、DW-O13を満たさないため作らなかった。実装面・削除・移動・gzip置換は0、変異matrixは実装しない裁定により免除した。
- T-1547、branch削除、active artifact内容、paper/raw/verbatim個別判断、非UTF-8 992 paths分類はscope外のまま状態変更していない。
- 分類表、controls、不足条件、履歴対照の一次資料は`output/insights/2026-08-24_t1539-insights-retention-precheck/README.md`。

## 次の一手差分

### 完了

- [T-1539] retention規則の機械判定可能性をprecheckし、判定不能のため推測削除を行わず分類表と不足条件を記録した。
  remaining: none
  base: 5d6c63c8388f9fe5f72350bf599c59570e3cb96762308d46b7f7118144c6b766
