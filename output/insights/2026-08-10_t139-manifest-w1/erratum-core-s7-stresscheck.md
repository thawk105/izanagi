# [T-139] 凍結事前登録 core §7 の較正義務に対する第 2 erratum (案)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / core_erratum
document_kind: preregistration_core_erratum
erratum_id: t139-core-s7-stresscheck-v1
approval_status: draft_unapproved
```

## 0. 本書は何であって何でないか

本書は、凍結事前登録 core の**特定の 1 blob** に対する **one-off の exact replacement** である。
承認済み第 1 erratum (`t139-core-s15-exactkey-v1`) の兄弟であり、置換の対象節が異なる。

- **core の bytes を一切変更しない。** core を編集すると §15 要件 3 が破れ凍結が壊れる。
- **一般の errata registry ではない。** 本書は §1 の三つ組に束縛される。
- **追補ではない。** 追補 A の `fields` の一部ではなく `a14` 相当でもない。
- **本書はまだ承認されていない。** `approval_status: draft_unapproved` である。
  ユーザー裁定 §58 (Q-B) は「次の manifest wave が同梱起草し、**発効まで pilot を機械的に停止する**」
  と定めた。本書は起草にあたる。**承認は別途の canonical な裁定と、それを台帳へ fold する
  commit を要する。**registry へ validator が登録されていることは承認ではない。

## 1. 対象 (この三つ組以外には適用しない)

```yaml
target_core:
  path:   output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256: ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

`commit` は限定例外の決定 (D234) を canonical 台帳へ fold した commit `F` である。
resolver は `(path, commit, sha256)` の**三つ組が exact 一致**した場合にだけ本書を適用する。

## 2. 事実 — core §7 は保証していない性質を「較正する」と書いている

core §7 の末尾は次を課す (`F` 時点の 219〜221 行目)。

```text
**帰無仮説は weak mean null を primary とし** (estimand が平均 contrast のため)、
sharp null は副次感度分析とする。weak null の型 I 誤りは、同じ許容 schedule 集合を使う
事前 simulation で較正する。
```

この「較正する」は、**cluster level の型 I 誤りを較正したという主張として読める。**
ところが利用可能な raw は J=1 screen の 1 割当て分 (2 workload × 3 arm × 5 反復 = 30 行) だけで、
**割当て間 (cluster 間) の変動は 1 点も観測されていない** (core §17)。

追補 A パッケージ段 3 のレンズ A が示した反例 — 未観測の cluster 効果
`P(U = a) = 0.99`, `P(U = −99a) = 0.01` を加えると `E[U] = 0` で weak mean null を満たすが、
`J ≤ 13` の全 cluster が正側になる確率は `0.99¹³ ≈ 0.878` あり、片側下限は高確率で正になる。
**この cluster 効果は J=1 データから識別できない。**

したがって現行の逐語は、絶対規律 3 が禁じる「保証していない性質を保証したと書く」に該当する。
追補 A の `a12` は既に「事前固定した stress model のもとで名目を超えないことの確認」という
限定を明記しているが、**追補は core の意味を変えられない** (D234)。
core 側の逐語を置換しない限り義務は未達のまま残る。

これは追補 A パッケージの裁定 R2 で **(a) が承認された方向**である
(§47、2026-08-08「推奨通りで」) — ただし承認されたのは方向であり、本書という文書ではない。

## 3. supersede する箇所 — 構造化された exact 1 operation

**本節は散文ではなく、要素数がちょうど 1 の置換 operation 配列である。**
resolver はこの配列だけを読み、本書の他の節を受理述語の入力にしてはならない。
配列の長さが 1 でない erratum、または `old_sha256` が対象 core の当該行と一致しない erratum は
**解決失敗**とする。

`old_sha256` は、対象 core の当該行の **bytes (行末 LF を含む) の SHA-256** である。

```yaml
operations:
  - index: 1
    locator:
      section: "7"
      anchor: "帰無仮説の段落の最終行"
      line_number_at_target_commit: 221
    old_sha256: 225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89
    old_text: |
      事前 simulation で較正する。
    new_text: |
      事前固定した stress model のもとで名目水準を超えないことを事前 simulation で確認する。
```

**検査可能性。** 「1 箇所だけ」は自己記述ではなく次で機械的に判定できる。

1. `operations` の要素数が `== 1` であること。
2. `old_sha256` が、対象 core の当該行の bytes の SHA-256 と一致すること。
3. 対象 core 全体で、文字列 `事前 simulation で較正する` の出現が**ちょうど 1 件**であり、
   それが `operations` の 1 行に一致すること (親が実測: 出現は 221 行の 1 件のみ。
   なお `較正する` 単独は 333 行 = §14 の `a12` 行にもあるが、本 operation の対象ではない)。
4. `new_text` が `old_text` と同じ 1 行であり (行数不変)、置換後も当該行が
   「事前 simulation」への言及を保つこと。

**上記 1 operation 以外の core の bytes・文言・受理条件・閉集合・投入順序・commit/blob 束縛を、
変更または supersede しない。**本書の他の節 (§0 §1 §2 §4 §5 §6) は説明であって受理述語ではなく、
**「解釈」「補足」の名目で第 2 の受理条件を追加する経路を持たない。**
特に次は本書の射程外である。

- §15 の exact-key (第 1 erratum の管轄。本書の locator 221 行と重ならない)。
- §7 の pairing・順序均衡・trace 分離・validator 権威の各条 (219〜221 行の外)。
- `a11` の `q(J, α_k)` と `a13` の有意水準 (追補 A の管轄)。
- §4 の Fieller 同値、§9 の失敗分類、§6 の標本数規則。

## 4. 受理集合はどちらへ動くか — **変わらない**

第 1 erratum (`∅ → R13` の拡大) と違い、本書は**投入 gate の受理述語を動かさない。**

- §15 の要件 1〜7 は本書の置換後も逐語が同一である (locator 221 行は §7 に属し §15 に属さない)。
- 追補 A の exact-key 期待集合も、`q` の導出も、`α₁` も変わらない。
- 変わるのは**解析時に何を主張してよいか**である。置換前は「cluster level の型 I 誤りを
  較正した」と読めたが、置換後に主張できるのは「事前固定した stress model のもとで
  名目水準を超えないことを確認した」だけになる。

したがって本書は**受理集合に対して中立であり、主張の強さを弱める方向にだけ効く。**
**この事実を「だから安全なので承認不要」の根拠に使ってはならない** — core の逐語を変える
行為であり、明示の裁定を要する。

## 5. 発効点と機械配線の契約

**発効点。** 本書は、本書を承認する決定を canonical 台帳へ fold した commit 以後にのみ効力を持つ。
その commit を `F_s` と呼ぶ。`F_s` より前の checkout から得た cluster に本書を適用しない。
**本書の起草時点で `F_s` は存在しない。**

**承認集合への membership。** 本書が承認 manifest の `approved_errata` に入るのは `F_s` の後だけである。
それまでは `draft_errata` に置く。
**`erratum_id` 別 validator registry (D263) への登録は、承認とは独立である** —
registry は「この ID の文書をどう検査するか」を定めるだけで、「適用してよいか」は定めない。
D263 の理由節が本書を「既に承認済み」と記す箇所は事実誤りであり、本 wave の新 decision が
前向きに supersede する。

**pilot の停止。** 本書が未承認である間、pilot は投入できない。
これは新たな gate の作為によってではなく、**T-139 の投入 API が 1 つも実装されておらず、
D264 が `resolve_effective_preregistration` / `PreregBinding` / `submit_pilot` / `verify_receipt`
の非 export を機械検査で固定していること**によって成立している。
将来 gate を実装する wave は、**その gate の受理条件に「core §7 の較正義務が
承認済み erratum によって解決済みであること」を含めなければならない。**
含めない実装は、本書が未承認のまま pilot を通してしまう。

## 6. 通る正例 (1 つ)

`F` を D234 を fold した commit、`F_s` を本 erratum を承認する決定を fold した commit とする。
core が `F` の path `P` に blob `B` (`h = SHA-256(B)`) として存在し、
本 erratum が commit `C_s` の path `P_s` に blob `B_s` として存在し、
`B_s` が対象として `(P, F, h)` を記し supersede 箇所が §3 の 1 箇所だけであり、
承認 manifest の `approved_errata` が本書を含み、`F`・`F_s`・`C_s` がすべて実 checkout の
HEAD の祖先であるとき、本書は解決に成功し、第 1 erratum と合成できる。

このとき第 1 erratum (locator 404 / 424) と本書 (locator 221) の locator は**重ならない**ので、
合成は順序に依らず定義される。**合成後の digest は第 1 erratum 単独の
`d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82` とは異なる値になる。**

**この正例は現時点では成立しない** — 本書は未承認であり、`F_s` が存在せず、
承認 manifest も resolver も実装されていない。

## 7. 本書が主張しないこと

- **本書が承認された、とは主張しない。** `approval_status: draft_unapproved` である。
- **本書が pilot 停止 gate を実装した、とは主張しない。** 停止は §5 の既存事実による。
- **core §7 の他の条項に誤りが無い、とは主張しない。** 本書が扱うのは 221 行の 1 箇所だけである。
- **置換後の逐語が cluster level の型 I 誤りを制御する、とは主張しない。**
  制御は `a11` の planning model のもとでの Hotelling / t / 非心 t が与えるものであり、
  simulation は事前固定 stress model のもとでの確認に留まる。
  **cluster 間変動は依然として未観測である。**
