# [T-147] 段 1 brief + 敵対レビュー・焦点再レビューの逐語 (凍結、2026-07-28)

親の裁定・要約は `../2026-07-28_t147-budget-restructure-package.md` が正本。ここは逐語のみ。

| ファイル | 役 | レンズ / 巡 | sha256 (凍結時) |
|---|---|---|---|
| `parent-brief.md` | 段 1 brief (親) | — | `4cf37fcf1cfae697d0e5bd141557b6712c2a0129107ef8e961e908f7aeaa595d` |
| `review-a-meaning-preservation.md` | 敵対レビュー A | 意味保存・安全義務弱化 | `aa4c5849222465273804a9faa5f8a72e452810d4269d99ac655772215998d1c6` |
| `review-b1-broken-artifact.md` | 敵対レビュー B 初回 | (成果物破損・不採用) | `b6f389e7c9716d3cca28b8d8332afc49c2cd7286d57697e107c6969b6ae1cc3a` |
| `review-b2-dispatch-closure.md` | 敵対レビュー B2 再投 | dispatch 閉包・正本整合 | `1c5d0ab93164349a1b096627416758a5c29fe62c367123150a55d1160c1991d4` |
| `review-c1-focused.md` | 焦点再レビュー 1 巡目 | 対応表 + 横断 | `ab63684b1f019b7a6cfec8f99b0f29a0e25f56e04849dea97d2005902b3a52ae` |
| `review-c2-focused-round2.md` | 焦点再レビュー 2 巡目 | 残 2 所見限定 | `50527db644ad7a70abff6dfd9ad3e3efa485e5bd6f27a09c5cf6b70e369c210c` |

レビュー 5 本は `codex exec -m gpt-5.6-sol -c model_reasoning_effort="high" -s read-only`
(`DW-O01`)。いずれも静的検査のみで pytest を走らせていない (`DW-O05`) — 逐語中に「緑」の
記述があってもテスト結果として読んではならない (テスト実測はすべて親)。

**`review-b1-broken-artifact.md` は成果物として不採用** — exit 0 だが最終メッセージが出力書式の
推敲メモ断片のみで、レビュー本文が失われた (near-miss、failures F43)。同一 prompt の再投が
`review-b2-dispatch-closure.md`。破損の証拠として原文のまま凍結する。

defang は施していない (検出語 gate は clean — 凍結後の `check_docs` rc=0 で機械確認)。
