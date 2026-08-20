---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t989-realrepo-worker-diag
seq: 3
title: '[T-989] 段8自己改善候補2件を記録した (docsのみ、branch worktree-dev-wave-t989-realrepo-worker-diag)'
---

## 本文

- 段8自己改善候補2件を発見。dev-wave docs (core/operations/workers/mutation.md)
  の3層予算は既知で満杯 (`dev-wave-docs-compression-breaks-exact-pins` と一致)
  のため、即時の統合は試みず候補記録のみに留めユーザー裁定へ返す。
  1. **`--reasoning`のstage別拘束をDW-C01へ追加する案。** `--lane`の隣に
     「`--reasoning`はplan/consultだけ必須、review/focus/author/fixで指定すると
     rc=2 (docs権威導出)」の1行を試作したが、`docs/dev-wave/core.md`のDW-C01節が
     1105 bytes (単節予算1000 bytes) になりexact契約とも不一致となったため revert
     した (`python3 tools/check_docs.py`で実測確認)。本waveは段2 plan投入で
     `--reasoning`未指定によりrc=2を1回踏んでから学習した。他waveの参考に
     ここへ記録する。
  2. **codex prompt の `## 総括` 必須+目安bytes数(500以上)をplan/consult以外
     (author/fix/focus) にも一貫してテンプレート化する案。** DW-O01は既に
     「prompt は `## 総括` 必須」と全段共通で明記しているが、本wave中に
     author×1・fix×1・fix(revert)×1で見出し欠落または500 bytes未満により
     `check_codex_output.py`不採用を計3回踏んだ (実装自体は毎回正しく、報告のみ
     の軽量再投入で解消)。docs文言に不足は無く、prompt作成時のチェック項目
     として次セッション/次waveが意識すべき運用上の教訓として記録する
     (docs変更は提案しない — 既存文言で足りている)。

## 次の一手差分
