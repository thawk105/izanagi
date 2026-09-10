# [T-1871] 段階 B の逐語 — 読む前に

`docs/axis-onboarding.md` 段階 B (D41 型) の一次資料。裁定と結論は
`../2026-09-01_t1871-nonenum-axis-stage-b-package.md` が正本で、ここは逐語の保存だけを担う。

| ファイル | 段 | レンズ | verdict |
|---|---|---|---|
| `stage2-plan.md` | 2 | プラン起草 (read-only) | — |
| `stage3-lens-a-correctness.md` | 3 | 正しさ・reward hack・未定義動作 | reject |
| `stage3-lens-b-effectiveness.md` | 3 | 実効性・非列挙性・既裁定整合 | adopt-with-conditions |
| `stage6-lens1-correctness.md` | 6 | 正しさ・reward hack・未定義動作 | reject |
| `stage6-lens2-nonenumerability.md` | 6 | 非列挙性・軸適格性 | reject |
| `stage6-lens3-discipline.md` | 6 | リーク制御・既裁定整合・scope 規律 | reject |

段 3 の 2 本は**撤回済みの初版** (生の `Tidword` word を許す案) を検査している。
段 6 の 3 本は第 2 版 (派生 boolean + 骨格所有の連続 abort 数) を検査している。

## 取り扱い (リーク制御)

**本ディレクトリの内容を coder / planner の入力へ射影してはならない。**
逐語には具体的な述語構成のヒント (低位 bit の使い方、record 世代の分割、
トランザクション種別の近似、閾値の置き方) が含まれる。D45 の「文書経由リーク」型に当たる。

軸の生死は二値 (生きている) としてのみ引用してよい。偵察の勝ち候補・利得数値・順位は
本ディレクトリにも `../2026-09-01_t1871-nonenum-axis-stage-b-package.md` にも転記していない。
