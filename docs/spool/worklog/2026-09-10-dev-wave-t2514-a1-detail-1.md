---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2514-a1-detail
seq: 1
title: [T-2514] A-1条件関門の拒否時arm detail保存を実装する (branch worktree-dev-wave-t2514-a1-detail)
---

## 本文

- D1936項4・D1912を当該A-1だけに適用。既存生成済み全arm recordとadmissionを検証済workload raw_rootへ保存する。
- 保存Exceptionは元拒否へ追記するだけ。受理集合・reason code・成功経路を維持し、依存供給/source根治・attempt-0004は行わない。
- 起動時に同名/後続A-1の稼働所有なしを照合。T-2581のp3_s4_loop.pyは参照のみ。
- 別Codex authorで実装し独立レビュー2本はmust-fixなし。consumer赤で同一build sinkの行番号参照2か所を追従、焦点レビューで意味不変を確認。
- A-1単独196 passed、修正後sink単独44 passed、commit後consumer1204 passed/4 skipped。変異は基準走3 passed、M2/M3の挙動kill2件とM1のdiagnostic sensitivity pin1件、全期待node一致、復元rc0。
- authorのsandbox qstat拒否と親local capによる未完走は緑に数えず、親の計算ノード再走で確認した。no-touch赤はcommit後に解消し、期待値を緩めていない。
- 詳細・逐語・変異raw = `output/insights/2026-09-10_t2514-a1-detail/README.md`。
- dev-wave改善候補1件をhandoffに記録し同insightへ吸収。read-only worker artifact増加とbounded local fallbackの衝突を避ける手順明確化候補。改善実装・次wave・pushは行わない。

## 次の一手差分

### 完了

- [T-2514] A-1の既存条件関門が拒否したときの全arm record/detailとadmission保存を実装し、拒否不変・成功無副作用・保存失敗時の元拒否保持を検査した。
  remaining: none
  base: fcaef3c9f7bd352d62ab8118398403da9c7bf14983081c06f570e3b0b8aa2037
