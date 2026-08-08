# [T-139] 追補 A 起草 — 段 6 fix 対応表 (2 巡目。焦点再レビューへの応答)

```text
authority: none
default_effect: no-state-change
```

焦点再レビュー (`s6-refocus.md`) は **NO-GO**、blocker 10 件。
1 巡目の 21 件の再判定 (`closed` 5 / `partial` 8 / `still-open` 3 / `regressed` 3) も返した。
**`regressed` 3 件はいずれも親が 1 巡目の fix で作り込んだものである。**

`DW-O16` に従い、2 巡目の fix と、残る所見の real/refuted 裁定を本書で閉じる。

## 1. 焦点再レビューの所見への対応

| # | 所見 | 区分 | 判定 | 対応 |
|---|---|---|---|---|
| 1 | `a10` の `T_k` が本文上未定義 | blocker | **real** | **closed。**`s_k = sqrt((Ŝ_J)_kk)` (不偏、分母 `J−1`)、`T_k = √J·μ̂_k/s_k`、成分 6 個の並び、`s_GG = s_DD + s_NN − 2s_ND` を逐語で定義した。**受理条件 `P_W1 ∧ P_W2` が `∩_k {T_k > q}` と一致すること**も明記した (レビュアーが独立に検算し「書いてよい」と確認済み) |
| 2 | `p_k` の「上向き丸め」は認証された上界でない | blocker | **real** | **closed。**認証区間 `[p_k^L, p_k^U]` (幅 `≤ 1e-9`、外向き丸め) へ改め、`L_J^cert = 1 − Σ p_k^U`、`U_J^cert = 1 − Σ p_k^L` とした。`q` も認証区間で求め **上端**を `p_k` の評価に使う。`[L^cert, U^cert]` が `0.80` を跨ぐ候補が 1 つでもあれば `design_not_feasible`。reference vector の発行も要求した |
| 3 | `d⁻` の等式は gate 通過枝に限る / 確率層の記号 | 明確化 | **real** | **closed。**「`μ⁻_k ≥ 0` の枝でのみ infimum と一致する。無条件の infimum として引用してはならない」を明記し、planning の不確実性を `β_plan = 0.05`、本走の型 I 誤りを `α₁ = 0.025` と別記号にした |
| 4 | core §7 の較正義務は明示的に未達 | blocker | **real** | **escalated (R2)。**`a12` 本文と README の「主張しないこと」に明記済み。凍結しない |
| 5 | alpha ordinal の権威がまだ存在しない | blocker | **real** | **escalated (R3)。**`a13` は台帳予約を要件化済み。台帳の実体化は producer 実装 wave |
| 6 | R1 の singleton erratum と R2/R5 の追加 erratum が共存不能 | blocker | **real** | **closed。**erratum §5 の契約を「一致件数 `== 1`」から **承認済み erratum の exact set** へ改めた (適用順序・locator の非重複・合成後 digest を要求)。`package.md` の R1(a) も同じ形へ改めた。**これは親が 1 巡目で作り込んだ回帰である** |
| 7 | 初回観測窓が preflight cap と実行遷移に閉じていない | blocker | **real** | **closed。**preflight の sub-cap を逐語で配分した (`[0,150)` 準備 / `[150,160)` 観測 / `[160,165)` 判定 / `[165,170)` marker)。観測終了から exec までを `Δ_max = 5` 秒とし、以後の 35 run にも同じ `Δ_max` を課した。観測窓と exec の間に他作業・任意待機を挟まない |
| 8 | `a04` の「外部証拠」は trust root になっていない | blocker | **real** | **closed (保守側へ倒すことで) + escalated (R7)。**job の stdout / scheduler 出力を書くのは producer 自身なので trust root にならない、という指摘は正しい。したがって `a04` の既定を **「`a03` の不成立は位置を問わず開始後の失敗へ写し、予備で置換しない」** へ改めた。§9 の分類は増やさず、より保守的な写像を選んだだけである。緩和 (exec broker の新設) は裁定 R7 へ返した |
| 9 | `a08` の最終 configure argv が内部矛盾し probe とも不一致 | blocker | **real** | **closed。**template から `-DCMAKE_CXX_FLAGS` を除き、`-DCCBENCH_TRACE={0\|1}` を probe の `COMMON` と同じ 3 番目の位置へ置いた。結合規則を「共通部分 + `ADD_ANALYSIS` + `CXX_FLAGS`」= probe の `COMMON[@] + extra[@]` と同型に直し、`stock` でも `-DCMAKE_CXX_FLAGS=` を空で必ず渡すこと、6 通りの最終 argv を逐語で受領証へ残すことを要求した。**これも親が 1 巡目で作り込んだ回帰である** |
| 10 | 6 build を集約したが 1500 秒 cap が閉じない | blocker | **real** | **closed。**build phase (1440) と build 後処理 phase (360) を分離し、検証割当ての小計を `2640`、contingency を `660` に組み直した (internal deadline 3300・walltime 3600 は不変)。**これも親が 1 巡目で作り込んだ回帰である** |
| 11 | R6 へ送った schema 要件自体に記録不能な失敗経路がある | blocker | **real** | **closed。**`a03` の観測を `actual_runs[]` から **`attempts[].environment_observations[]`** へ移した (観測不成立で run が実行されない場合の記録先を作るため)。8 列未満の raw も可変長 pointer (`*_raw`) で保存する。文書の呼称を「closed schema」から**「受領証 schema の要件文書」**へ改めた |
| 12 | erratum の 2 行は target core と逐語一致する | 確認 | — | 変更不要 (レビュアーが `88d68f91` の 404 / 424 行の LF 込み hash を独立に再計算して一致を確認) |
| 13 | README と対応表が修正後の限界を過大申告する | major | **real** | **closed。**README の「主張しないこと」に model 条件・`L_J` の保守性・`δ_MC`・compiler 未 pin を揃え、「結論」節を敵対検証 5 本の実績と残存事項へ書き換えた |

## 2. 1 巡目の再判定に対する裁定

焦点再レビューが `partial` / `still-open` とした 11 件のうち、
**`escalated` (R2 / R3 / R6 / R7) が本質であるものは、本 wave の docs-only scope では閉じない。**
これは欠陥ではなく設計どおりである — 本 wave の終端は
`package.md` §6 の**段階 1 (承認待ち)** であり、機械配線と実測は後続 wave の責務である
(D234 実装境界、`DW-G04`)。

| 再判定 | 件数 | 本 wave での扱い |
|---|---|---|
| `closed` | 5 | 変更なし |
| `regressed` | 3 | **2 巡目で全件修正した** (所見 6 / 9 / 10) |
| `still-open` | 3 | A-4 → R2、A-6 → R5、B-6 → R7 へ escalate (いずれも本文では書けない) |
| `partial` | 10 | 本文で書ける部分は 2 巡目で閉じ、残りは R1 / R3 / R6 / R7 |

## 3. 巡回の終端 (`DW-O16`)

`DW-O16` は「NO-GO が続く場合は fix を重ねず 3 巡を上限とし、親が残る所見を real/refuted に
裁定して閉じる」と定める。本 wave は **fix 2 巡**で終える。理由は次のとおり。

- **焦点再レビューの 10 blocker のうち 7 件を本文で閉じた** (所見 1・2・3・6・7・9・10・11 = 8 件、
  うち 3 件は親の回帰)。
- **残る 3 件 (所見 4・5・8) は、いずれも「ユーザー裁定または機械配線が要る」ものであり、
  本文をどう書いても閉じない。**これらは `package.md` の R2 / R3 / R7 として返す。
- 3 巡目を回しても、閉じられるのは同じ 3 件ではなく新しい文言の指摘だけになる見込みが高い。
  **実装差分ゼロの wave なので変異による裏取りは射程外**であり (`DW-S04` 免除)、
  代わりに親が一次資料で直接検算した (`s4-adjudication.md` §0 と本書 §1)。

**refuted は 0 件。**焦点再レビューの 10 blocker はすべて real である。

## 4. 本 wave の終端判定

敵対検証 5 本 (段 3 の 2 レンズ、段 6 の 2 レビュー、焦点再レビュー) はいずれも **NO-GO** であり、
その判定は**「追補 A・erratum・schema 案の凍結、承認 fold、pilot 投入へ進めない」**である。

**これは本 wave の終端と一致する。**本 wave は凍結せず、
`package.md` の 7 問 (R1〜R7) と併せてユーザー承認へ返す。
NO-GO は成果物の否定ではなく、**「承認前である」という状態の確認**である。
