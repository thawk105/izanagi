# [T-139] 凍結事前登録 core §15 の exact-key 誤記に対する erratum (案)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / core_erratum
document_kind: preregistration_core_erratum
erratum_id: t139-core-s15-exactkey-v1
```

## 0. 本書は何であって何でないか

本書は、凍結事前登録 core の**特定の 1 blob** に対する **one-off の exact replacement** である。

- **core の bytes を一切変更しない。** core を編集すると §15 要件 3 (「`core_ref.sha256` が
  承認済み core の digest と一致する」) が破れ、凍結そのものが壊れるためである。
- **一般の errata registry ではない。** 本書は下記の三つ組に束縛され、他の core・他の study・
  将来の版へは適用されない。
- **追補ではない。** 本書は追補 A の `fields` の一部ではなく、`a14` 相当の 14 番目の field でもない。
  文書型 (`document_kind`) が異なる。

## 1. 対象 (この三つ組以外には適用しない)

```yaml
target_core:
  path:   output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256: ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

`commit` は限定例外の決定 (D234) を canonical 台帳へ fold した commit `F` である。
resolver は `(path, commit, sha256)` の**三つ組が exact 一致**した場合にだけ本書を適用する。
1 つでも異なれば適用しない (適用の可否を path だけで判定してはならない)。

## 2. 事実 — core は同じ閉集合を 2 通りに書いている

- **§14 の閉集合の表**は追補 A を **`a01` から `a13` までの 13 行**として列挙する。
  `a13` は「**primary 系列に割り当てる有意水準**。`q` はここから導くので、追補 B では動かせない」である。
  §14 の「越えてはならない線」も「`a11` と `a13` は `q` の導出規則と primary 系列の有意水準を固定する」と書く。
- **§15 の投入 gate の要件 5** と、その直後の**「通る正例」**は、**`a01`〜`a12`** を
  exact-key の基準として書く。

exact-key は「欠落も余剰も解決失敗」なので `{a01..a12}` と `{a01..a13}` は**互いに素**であり、
包含関係にない。どちらを実装しても、他方を満たす追補 A は resolver に拒否される。

`a01`〜`a12` を採ると、有意水準を含む追補 A が**余剰**として拒否され、
primary の有意水準を pilot 前に固定する経路が閉じる (pilot の後に有意水準を選べる状態が残り、
絶対規律 3 に抵触する)。

## 3. supersede する箇所 — 構造化された exact 2 operation

**本節は散文ではなく、要素数がちょうど 2 の置換 operation 配列である。**
resolver はこの配列だけを読み、本書の他の節を受理述語の入力にしてはならない。
配列の長さが 2 でない erratum、または `old_sha256` が対象 core の当該行と一致しない erratum は
**解決失敗**とする。

`old_sha256` は、対象 core の当該行の **bytes (行末 LF を含む) の SHA-256** である。

```yaml
operations:
  - index: 1
    locator:
      section: "15"
      anchor: "投入 gate の禁止条件 要件 5 の第 1 行"
      line_number_at_target_commit: 404
    old_sha256: 6e87b981b2d3550ea56278a50f9544a86bab575d18de3ea7f3984abdeca5681e
    old_text: |
      5. `addendum_a` が §14 の閉集合 `a01`〜`a12` を **exact-key で満たす** — 全件が存在し、
    new_text: |
      5. `addendum_a` が §14 の閉集合 `a01`〜`a13` を **exact-key で満たす** — 全件が存在し、
  - index: 2
    locator:
      section: "15"
      anchor: "通る正例 (1 つ) の該当行"
      line_number_at_target_commit: 424
    old_sha256: b5e2c7b290c1c21aff84f4b520468df551c9d0e4bd76d2102ace3208b3e1b7d1
    old_text: |
      存在し `h2 = SHA-256(B2)`、`B2` が従属先として `(P, C, h)` を記し `a01`〜`a12` だけを設定しており、
    new_text: |
      存在し `h2 = SHA-256(B2)`、`B2` が従属先として `(P, C, h)` を記し `a01`〜`a13` だけを設定しており、
```

**検査可能性。** 「2 箇所だけ」は自己記述ではなく次で機械的に判定できる。

1. `operations` の要素数が `== 2` であること。
2. 各 `old_sha256` が、対象 core の当該行の bytes の SHA-256 と一致すること。
3. 対象 core 全体で、文字列 `a01`〜`a12` の出現が**ちょうど 2 件**であり、
   その 2 件が `operations` の 2 行に一致すること (親が実測: 出現は 404 行と 424 行の 2 件のみ)。
4. `new_text` と `old_text` の差分が `a12` → `a13` の 1 トークンだけであること。

**上記 2 operation 以外の core の bytes・文言・受理条件・閉集合・投入順序・commit/blob 束縛を、
変更または supersede しない。**本書の他の節 (§0 §1 §2 §4 §5 §6 §7) は説明であって
受理述語ではなく、**「解釈」「補足」の名目で第 3 の受理条件を追加する経路を持たない。**
特に次は本書の射程外である。

- §4 の Fieller 同値の文言 (負分母枝を除外していない点)。
- §14 の閉集合の表そのもの (もともと `a01`〜`a13` であり、訂正を要しない)。
- 追補 B の閉集合 `b01`〜`b03` を基準にする検査。
- §9 の失敗分類、§5 の状態表、§6 の標本数規則。

## 4. 受理集合はどちらへ動くか — **拡大である**

段 6 の敵対レビュー 2 本が独立に、本節の初版 (「狭い側へしか動かない」) が**偽**であることを
指摘した。訂正した記述を正とする。

`R12 = { fields が exact に {a01..a12} }`、`R13 = { fields が exact に {a01..a13} }` と置く。
exact-key なので `R12 ∩ R13 = ∅` であり、どちらも他方の部分集合ではない
(**集合として互いに素なのは追補文書のクラスであって、key 集合ではない** —
key 集合としては `{a01..a12} ⊂ {a01..a13}` である)。

- **literal な core** は §14 で exact 13、§15 で exact 12 を**同時に**要求するので、
  両方を満たす追補は存在しない。すなわち現在の受理集合は **`∅`** である。
- 本書の適用後、受理集合は **`R13`** になる。

したがって本書は **`∅` から `R13` への受理拡大**である。
「単調な狭化」ではなく、「矛盾した literal 仕様を一意な `R13` へ置換して空集合を解消する」変更である。
**この事実を安全性の根拠に使ってはならない** — 承認は「拡大を承認する」ものとして扱う。

拡大の中身は「有意水準を含む追補だけを受理する」ことであり、
含まない追補 (`R12`) は受理されなくなる。**pilot の後に有意水準を選べる経路は本書の適用後に閉じる。**

## 5. 発効点と機械配線の契約

**発効点。** 本書は、本書を承認する決定を canonical 台帳へ fold した commit `F_e` 以後にのみ効力を持つ。
`F_e` より前の checkout から得た cluster を適格として扱わない。

**resolver の契約 (producer 実装 wave が実装する。本書はコードを追加しない):**

**trust root。** 承認の正本は **canonical 台帳へ fold された one-off approval manifest** とする。
manifest は、承認対象の追補 A と erratum の `(path, commit, sha256)` を逐語で持つ。
**resolver はこの manifest から `approval_fold_commit` と blob identity を取得する** —
caller の引数や受領証の自己申告からは取らない。これが無いと、
producer が exact 13 key を持つ**未承認の追補 A′** (待機秒数や閾値だけ差し替えたもの) を
`measurement_head` の祖先に置くだけで D234 の (iv)〜(vi) を満たしてしまう。

1. `resolve_effective_preregistration` は `core_ref` を §15 要件 1〜3 のとおり解決する。
2. 解決した `(core_ref.path, core_ref.commit, core_ref.sha256)` を exact key として、
   approval manifest から**承認済み erratum の exact set** を引く。
   manifest が列挙する集合と、解決できた erratum の集合が**完全一致**しなければ解決失敗とする
   (欠落も余剰も失敗。「先頭の 1 件を採る」実装を禁じる)。
   集合の要素が 2 つ以上ある場合は、manifest が定める**適用順序**に従い、
   全 operation の `locator` が**互いに重ならない**ことを検査し、
   合成後の core bytes の digest が manifest の `composed_sha256` と一致することを要求する。

   > **初版の誤り (段 6 の焦点再レビューが検出)。** 初版は「一致件数が `== 1` でなければ失敗」と
   > 書いていた。しかし `package.md` の R2(a) と R5(b) はいずれも**同じ core に対する
   > 第 2 の erratum** を選択肢に持つ。singleton 契約のままだと、R1(a) と R2(a) を同時に裁定した
   > 時点で resolver が**必ず**失敗する。したがって契約を exact set へ改める。
   > 本 erratum (`erratum_id: t139-core-s15-exactkey-v1`) は、その集合の 1 要素である。
3. その erratum blob が実在し digest が manifest と一致すること、および
   `approval_fold_commit` が `measurement_head` の祖先であることを検査する。
4. erratum の `operations` について §3 の検査 1〜4 をすべて行う。1 つでも失敗したら解決失敗。
5. **追補 A の blob digest が同じ manifest の承認値と一致する**ことを検査する。
6. 以上を通ったときにだけ、追補 A の exact-key の期待集合を `{a01, …, a13}` とする。
7. 検査に 1 つでも失敗したら、**期待集合を §14 基準へ緩和せず解決失敗とする** (fail-closed)。

**`PreregBinding` と受領証。** 解決した erratum の
`(path, commit, sha256, approval_fold_commit)` を `PreregBinding` に含め、
受領証の `preregistration.errata[]` へ記録する (top-level key は増やさない)。
受領証の値は**照合対象**であって権威ではない —
権威は manifest 側である。`verify_receipt` は投入後にこの四つ組と `measurement_head` の一致を確認する。

> **本書はこの manifest を実体化しない。** approval manifest の形式・置き場・fold 手順は
> `package.md` の裁定 R1 が扱う。manifest が存在しない状態で本 erratum を適用してはならない。

**禁止。** 文書全体を grep して `aNN` を集める形の解決を禁じる。
文書型と `fields` object を分離し、erratum が追補 A の field として数えられる経路を作らない。

## 6. 通る正例 (1 つ)

`F` を D234 を fold した commit、`F_e` を本 erratum を承認する決定を fold した commit とする。
core が `F` の path `P` に blob `B` (`h = SHA-256(B)`) として存在し、
本 erratum が commit `C_e` の path `P_e` に blob `B_e` (`h_e = SHA-256(B_e)`) として存在し、
`B_e` が対象として `(P, F, h)` を記し supersede 箇所が §3 の 2 箇所だけであり、
追補 A が commit `C2` の path `P2` に blob `B2` として存在し `a01`〜`a13` **だけ**を設定し
従属先として `(P, F, h)` を記しており、`F`・`F_e`・`C_e`・`C2` がすべて実 checkout の HEAD の
祖先であるとき、`resolve_effective_preregistration` は成功し、
他の admission 条件を満たせば `submit_pilot` へ進める。

**この正例は現時点では成立しない** — 本 erratum も追補 A もまだ承認されておらず、
`F_e` が存在せず、resolver も実装されていない。

## 7. 本書が主張しないこと

- **本書が投入 gate を機械的に実装した、とは主張しない。**
- **core の他の誤記が無い、とは主張しない。** 本書が扱うのは §15 の 2 箇所だけである。
- **本書の適用によって pilot が投入可能になる、とは主張しない** —
  resolver・producer・validator・consumer が未実装であり、追補 A も未承認である。
