# [T-987] 床値 v2 再測定の束縛 — 実装せず裁定パッケージへ返した wave の逐語

2026-08-17 / branch `worktree-dev-wave-t987-floor-rebind` / base `699c9cae` / 実装差分ゼロ

## 結論

確定済みユーザー裁定 (2026-08-16 /rulings 全件 第 3 回) は
「再測定は世代移行 wave と同一 chain でのみ実施する」を記録基準へ緩めよと定めていた。
**そのとおり実装しても裁定の目的 (現 gitlink で床値を再測定して v2 を作る) は達成できない。**
阻んでいるのは緩和対象の束縛ではなく、`official` mode の無条件拒否
(理由 = §8 承認束縛方式が未裁定) と、v2 再凍結 consumer の固定 legacy protocol 束縛である。
加えて one-shot key に `mode` が入らないため、裁定どおり pilot を実施すると
[T-750] が必要とする権利を焼く。

裁定パッケージ (択 α/β/γ/δ と親の推奨) は `verbatim/s4-adjudication.md` §4。
worklog の [T-987] 項にも同じ択を載せた。

## ファイル

| path | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。provisional 前提 P1〜P3 を含む |
| `verbatim/s2-plan.md` | 段 2 プラン (codex plan、read-only、reasoning=max)。P1 を偽と断定 |
| `verbatim/s3-lensA.md` | 段 3 敵対レンズ A (sol)。正しさゲート侵食・受理集合。**NO-GO**、blocker 5 件 |
| `verbatim/s3-lensB.md` | 段 3 敵対レンズ B (luna)。記録の実質・前提の陳腐化・scope |
| `verbatim/s4-adjudication.md` | 段 4 裁定 (親)。所見の real/refuted、実装しない根拠、裁定パッケージ |
| `verbatim/parent-measurements.md` | 親の生の実測値 M1〜M10。訂正 1 件を含む |
| `verbatim/parent-alternative.md` | 段 2 案に対する親の最小変更対案 (不採用、記録のみ) |

## 実測で覆した裁定の前提

1. 「sanctioned な発行経路が存在しない」→ 偽。`reseal-protocol` CLI が実在する。
2. 「待つ相手が保留確定・事実上の無期限凍結」→ 偽。世代移行は 2026-08-17 に稼働中
   (wave `dev-wave-t657-activation-rebuild`)。

## 親の誤りと訂正

親は段 1 で「`reseal_protocol()` の production caller はゼロ」と書いたが偽。
呼び手検索を `grep -v` で自 file ごと除外していた。段 3 レンズ B が refuted し、
親が再確認して確定。F370 と同型のため同エントリへ再発として記録した。
