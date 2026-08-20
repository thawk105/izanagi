---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1441-unit3-d574-audit
seq: 2
title: '[T-1441] 段8自己改善候補2件を記録した (docsのみ)'
---

## 本文

- dev-wave docs (core/operations/workers/mutation.md) の3層予算は既知で満杯
  (`dev-wave-docs-compression-breaks-exact-pins`と一致) のため、即時のreference節統合は試みず、
  候補記録のみに留めユーザー裁定へ返す (予算を上げる変更は通常の自己改善に含めない、per
  `docs/skill-self-improvement.md`)。

## 次の一手差分

### 新規

- {{T:dev-wave-acceptance-before-records-ordering}} **P2・新規 (dev-wave改善候補1)**:
  段6完了直後に受入を投入すると、段7の記録commit (worklog/decisions/insight fragment) が
  受入検証済みのtipに含まれず、後から記録commitを足すとlandがrc=23になるリスクがある
  (memory `acceptance-runs-on-final-tip-with-records.md`)。本waveで実際にこの順序を誤りかけ、
  まだlease未取得 (child実行前) だったため安全に取り消して回避した。DW-S06-C
  「親が変異matrixと受入を再走する」という記述が段6の一部として受入投入を示唆する一方、
  記録commitは段7という構成が、順序を曖昧にしている可能性がある。
  `docs/dev-wave/operations.md`のDW-O18近辺、または`docs/dev-wave/core.md`のDW-S07近辺へ
  「受入投入は段7記録commit完了後に行う」という一文を明示する候補 (3層予算満杯のため
  即時統合は見送り)。
- {{T:dev-wave-author-prompt-needs-sokatsu-reminder}} **P2・新規 (dev-wave改善候補2)**:
  段5 author の prompt 作成時、`## 総括` 見出し必須 (`DW-O01`「prompt は `## 総括` 必須。F43」)
  を明記し忘れ、実装内容自体は正確だったにも関わらず `check_codex_output.py` rc=1
  (not_accepted) になった。段2/段3のprompt作成では明記していたが、段5 authorのprompt作成時に
  見落とした。`docs/dev-wave/workers.md`のDW-S05-Cのprompt必須項目リストに、DW-O01が既に
  定める「`## 総括`見出し必須」を明示的に統合する候補 (実害は親の直接検証+再投入1回で解消、
  緊急性は低い、3層予算満杯のため即時統合は見送り)。
