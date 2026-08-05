# [T-522] Pegasus admission registry を data 正本へ移す wave — 逐語と変異台帳

2026-08-06。branch `worktree-dev-wave-t522-admission-registry`。
worklog エントリと `docs/decisions.md` の当該 D が正本で、ここは**逐語の凍結**である。

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (scope・不変条件・provisional 裁定・段 1 実測) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only) |
| `s3-lens-a.md` | 段 3 敵対相談 レンズ A (正しさ境界・受理集合) |
| `s3-lens-b.md` | 段 3 敵対相談 レンズ B (射程・整合・運用実効性) |
| `s4-ruling.md` | 段 4 裁定 (real/refuted・plan v2・変異事前登録・裁定パッケージ) |
| `s5-impl-a.md` | 段 5 実装 A (registry JSON + loader + hook) |
| `s5-impl-b.md` | 段 5 実装 B (check_docs の投影検査) |
| `s6-review-a.md` | 段 6 敵対レビュー A (防壁側) |
| `s6-review-b.md` | 段 6 敵対レビュー B (検査実効性と docs の正しさ) |
| `s6-fix-a.md` / `s6-fix-b.md` | 段 6 fix 1 巡目 |
| `s6-refocus.md` | 段 6 焦点再レビュー (所見ごとの closed/partial/regressed 対応表) |
| `s6-fix2-a.md` / `s6-fix2-b.md` | 段 6 fix 2 巡目 |
| `s9-merge-verify.md` | 段 9 の merge 統合結果の検証 (F125 の恒久対応。auto-merge した 2 file の意味検査) |
| `mutation-spec.json` | 変異事前登録 11 本 |
| `mutation-ledger.json` | 変異本走の台帳 (KILLED 9 / MISMATCH 2 / SURVIVED 0 / TIMEOUT 0) |

## 読むときの注意

- 子の出力は**その時点の主張**であり、親が real/refuted を裁定した結果は `s4-ruling.md` と
  worklog エントリが正本である。子が blocker と書いた所見のうち、親が scope 外・refuted と
  裁定したものがある。
- `mutation-ledger.json` の MISMATCH 2 本 (M10 / M11) は、**事前登録した赤がすべて実際に赤になった
  上で予測しなかった層も赤くなった**もので、検出漏れではない。期待値は結果に合わせて書き換えていない。
