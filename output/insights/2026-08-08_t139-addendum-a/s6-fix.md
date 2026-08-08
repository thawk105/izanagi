# [T-139] 追補 A 起草 — 段 6 fix 対応表 (親)

```text
authority: none
default_effect: no-state-change
```

段 6 の敵対レビュー 2 本 (レビュー A = 統計・推論、レビュー B = 運用・規律) は
**いずれも NO-GO**、blocker は A が 6 件・B が 7 件の計 13 件。
docs-only の wave なので親が本文を直した (コード・テストは 1 行も足していない)。

対応は `closed` (本文で閉じた) / `escalated` (ユーザー裁定へ返した) / `partial` に分ける。

## レビュー A

| # | 所見 | 区分 | 判定 | 対応 |
|---|---|---|---|---|
| A-1 | LFC は core §6 の「共同信頼集合上の最悪検出力」を満たさない | blocker | **real** | **closed。**LFC を廃止し、**相関に依存しない union bound** に差し替えた。成分 `k` の受理事象は非心 `t` の周辺事象なので相関に依存せず、`Θ` 上の最悪値は `δ⁻_k = √J·μ⁻_k/√Σ⁺_kk` で取れる。`L_J = max(0, 1 − Σ_k p_k(J))` は **`Θ` 全体に対する認証された下界**であり、core §6 の要求を満たす |
| A-2 | `a10` が同じ pilot から同じ `J` を再現できない | blocker | **real** | **closed。**A-1 の差し替えにより Monte Carlo・seed・Wishart 極値分位点・branch-and-bound がすべて不要になった。`L_J` は非心 `t` の CDF・`F` 分位点・`χ²` 分位点だけの閉形式で、丸め方向 (`p_k` 上向き / `L_J` 下向き、小数第 9 位) も固定した。跨ぎ規則の矛盾も、区間が消えたので消滅した |
| A-3 | 単調性補題の分散方向は `μ_k ≥ 0` を欠く | minor | **real** | **closed。**補題ごと削除した (union bound は単調性を使わない) |
| A-4 | `a12` の呼び替えは core §7 の「較正」義務を消していない | blocker | **real** | **escalated (R2)。**`a12` に「core §7 の義務を満たしたと扱ってはならない」と明記し、R2 の選択肢へ「core §7 へ第 2 の erratum」「独立 cluster データの先行取得」を追加。推奨を (a) へ差し替えた |
| A-5 | `a13` は root を名指しただけで ordinal の一意性を強制しない | blocker | **real** | **partial + escalated (R3)。**`a13` に「予約は caller が選べない canonical 台帳で原子的に行い、本書の宣言は自己申告であって権威ではない」と明記し、`record-items.md` に予約証拠の field を必須化した。台帳の実体化は producer 実装 wave |
| A-6 | A8 の primary 反例は成立しないが、偽の同値を残す理由にならない | major | **real** | **escalated (R5)。**推奨を「実害なしなので当てない」から **「公表側に正分母 guard を課す」** へ差し替えた |
| A-7 | 「受理集合は狭い側」は逆である | blocker | **real** | **closed。**erratum §4 を全面訂正した — literal な core の受理集合は `∅` であり、erratum は `∅ → R13` の**受理拡大**である。「集合として互いに素なのは追補文書のクラスであって key 集合ではない」も明記した |
| A-8 | `record-items.md` は closed schema を名乗れる閉包を持たない | blocker | **real** | **partial + escalated (R6)。**§3.1 を新設し、「本書は schema が満たすべき要件を定める文書であって schema 本体ではない」「完全な機械可読 schema を pilot 前に 1 枚の blob として発行し digest を binding へ固定する」と明記した |
| A-9 | 非保証リストが model 条件と Monte Carlo 誤判定を漏らす | major | **real** | **closed。**`addendum-a.md` 末尾と `README.md` に「有限標本保証は iid 正規 planning model 条件付き」「`L_J` は保守側の下界」「`a12` の pass は familywise `1 − δ_MC` の主張」「compiler bytes は未 pin」を追加した |
| A-10 | R1〜R5 の選択肢が網羅的でなく推奨も導けない | major | **real** | **closed。**R1 に (b) 明示引数案、R2 に (a)(c)、R3 に (a) の台帳予約と (b)、R4 に閾値導出写像の事前凍結と (d) 中止、R5 に (a) 公表側 guard を追加。R6 を新設した |

## レビュー B

| # | 所見 | 区分 | 判定 | 対応 |
|---|---|---|---|---|
| B-1 | `fields` の境界 grammar がなく exact-key を一意に検査できない | blocker | **real** | **closed。**§0 に envelope grammar を明記した (`## fields` の直後から次の `## ` までの範囲の `### ` 見出しだけが key)。全文 grep で `aNN` を集める解決を明示的に禁じた |
| B-2 | erratum の「2 箇所だけ」は自己記述を信じる恒真検査 | blocker | **real** | **closed。**§3 を**要素数ちょうど 2 の構造化 operation 配列**へ書き換え、各要素に対象行の `old_sha256` (実測: `6e87b981…` / `b5e2c7b2…`)・行番号・`old_text` / `new_text` を持たせた。判定手順 4 段を明記し、承認一致件数は `== 1` (0 件でも 2 件以上でも解決失敗) とした |
| B-3 | `approval_fold_commit` と承認済み blob の trust root が無い | blocker | **real** | **partial + escalated (R1)。**erratum §5 に approval manifest を要求する契約を書き、「resolver は manifest から取得し、caller 引数・受領証からは取らない」「追補 A の blob digest も manifest の承認値と照合する」と明記した。manifest の実体化は R1 の裁定対象 |
| B-4 | 「受理集合は狭い側」は偽 | major | **real** | **closed。**A-7 と同一。2 本が独立に指摘した |
| B-5 | `a03` は恒真でないが最初の run に観測窓が無い | blocker | **real** | **closed。**最初の run の観測窓を **preflight phase の末尾 10 秒**とし `a01` の preflight cap に算入した (観測窓は 36 run に対しちょうど 36 個)。malformed counter (8 列未満 / 負差分 / `total ≤ 0` / 窓長逸脱) を fail-closed で `a04` の写像へ送る規則も追加した。`gen_S` 限定は R4 の選択肢へ反映 |
| B-6 | marker と raw を両方消せば開始前へ写せる | blocker | **real** | **closed。**`a04` を「marker の不在」ではなく **「性能 process を 1 つも起動していない外部証拠の存在」** を開始前の要件へ変えた。証拠の欠落・矛盾は保守側 (開始後・非置換) へ倒す。marker と外部証拠は producer が書き換えられない append-only 領域に置く |
| B-7 | grace 契約が cap を 10 秒超過する | major | **real** | **closed。**`TERM_at = cap − 10`、`KILL_at = cap` に固定し、cap は phase 単位であることも明記した |
| B-8 | `a08` の token 展開規則と compiler identity が未確定 | blocker | **real** | **closed + escalated (R4)。**`realpath` による解決、最終 argv の連結順序、compiler の realpath / `--version` / bytes digest を検証割当てで記録し以後 exact 一致を要求する契約を追加した。digest の数値 pin は計算ノード実測が要るので R4 の probe へ含めた |
| B-9 | nested schema が closed schema になっていない | blocker | **real** | **partial + escalated (R6)。**A-8 と同一。加えて `actual_runs[].argv_raw` と `compile_commands.json` の raw pointer を必須化した (`argv_sha256` だけでは exact 比較を再計算できない) |
| B-10 | 性能 build の生成元が二義的 | major | **real** | **closed。**検証割当てを**唯一の生成元**と定め、「割当て外 build」= 「性能 cluster 割当ての外」と定義を固定した。同じ nominal 構成の性能 build を 2 度作らない |
| B-11 | R4(a) 後の承認単位が未定義 | major | **real** | **closed。**既定を「3 本すべて段階 1 に留め、新しい追補 A と整合確認済みの erratum・schema を一括で再提出」と明記した |

## 親が直さなかったもの

無し。**13 blocker のうち real でないものは 0 件**である
(レビュー A の A-6 は「primary の悪用は refuted」を確認したうえで、
「公表文言に偽の同値を残す」ことを major として指摘しており、その部分は real)。

`escalated` としたもの (R1 の manifest 実体化、R2 の core §7、R3 の台帳、R4 の実測、
R5 の公表規則、R6 の schema 本体) は、いずれも **本 wave の docs-only scope の外**
(機械配線・core の逐語・計算ノードでの実測) であり、`package.md` で裁定を求める。

## 新規に導入した構成の未検証点 (正直な申告)

`a10` の union bound は本 fix で新設したものであり、**段 3・段 6 のどのレンズも検査していない**。
親の検算は次の 3 点である。

1. `T_k = √J·μ̂_k / s_k` が自由度 `J−1`・非心度 `δ_k = √J·μ_k/√Σ_kk` の非心 `t` に従うこと
   (planning model のもとで `μ̂_k` と `s_k` が独立な正規・χ であるため)。これは周辺分布なので
   成分間の相関に依存しない。
2. Bonferroni `P(∩E_k) ≥ 1 − Σ P(E_k^c)` は任意の従属構造で成立すること。
3. 非心 `t` の CDF は非心度について非増加なので、`Θ` 上の上限は `δ⁻_k` で取れること。

**この 3 点は段 6 の焦点再レビューで独立に裏取りする。**
