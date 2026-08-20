---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1141-spec-single-block
seq: 2
title: [T-1141] 段8自己改善候補1件を記録した (docsのみ、branch worktree-dev-wave-t1141-spec-single-block)
---

## 本文

**dev-wave改善候補 (段8裁定):** 受入 (`tools/dev_wave_wait.py acceptance`) の自動main取り込みは、
main側とwave側が同一実装fileの**非重複行域**を変更しただけ (競合なし・意味的にも清潔) でも
`merge-message-provenance` (rc=70) で受入前に終端拒否されうる。本waveで実測 (積集合3file、
`--owned-path`除去後もこの終端で1回失敗)。復旧は受入コマンドに任せず、手動
`git merge --no-ff --no-commit main` → 焦点走 → Codex `role=author`合成監査
(意味的整合の検査、本waveでは main側が追加したdocstring内のstale識別子参照2箇所を検出・修正) →
暫定messageでcommit → amendで確定、という手順が要る。memory
`implementation-merge-needs-codex-author-audit`・`predict-merge-provenance-violation` (直近の
別セッションが独立に実測・記録) と合わせて独立2例目以上となり、DW-G03の族一般化条件を満たす。
`docs/dev-wave/operations.md`のDW-O01近辺への統合が候補だが、dev-wave docs 3層の予算は既知で
満杯 (`dev-wave-docs-compression-breaks-exact-pins`) のため、即時のreference節統合は試みず
候補記録のみに留めユーザー裁定へ返す (既存の同種docs予算超過候補群と合流させてよい)。

## 次の一手差分
