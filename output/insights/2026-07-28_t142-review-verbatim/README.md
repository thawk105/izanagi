# [T-142] dev-wave 逐語 (2026-07-28)

テスト価値の二層化 wave (段 1〜4、実装なし裁定) の子エージェント成果物の逐語凍結。
裁定と要約の正本 = `output/insights/2026-07-28_t142-tiering-ruling-package.md`。

- `parent-brief.md` — 親の段 1 brief (P1〜P4 の provisional 裁定を含む。P2/P3/P4 は段 3 で攻撃成立)
- `plan-tiering.md` — 段 2 プラン起草 (codex gpt-5.6-sol, reasoning=max, read-only)。案 A/A′/B/C の
  比較と案 B 推奨、親 brief の誤り 2 件 (AND helper 誤認・base driver legacy-only) の検出を含む
- `consult-a-acceptance-set.md` — 段 3 敵対相談レンズ 1 (正しさ境界・受理集合)。所見 12 件
- `consult-b-efficacy-scope.md` — 段 3 敵対相談レンズ 2 (実効性・整合・scope)。所見 11 件
- `count_abort_reasons.py` / `count_frontier.py` — 親の独立実測スクリプト (WAL 読取のみ)。
  bench-fail 0/78、S2 中央値 117.3 s (n=111)、new-best 12% (省略上限 88%) の再現手順

凍結時の機械検査: LITERAL_PLACEHOLDERS (D88) 0 hit、s8b holdout 三軸語 (rr80/rr20 系) 0 hit。
defang 不要のため原文 hash 併記は省略 (D88 (6) は hit 時の手順)。
