# [T-139] 公表 — 事前登録 追補 P (草案。凍結対象ではない)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / publication_study / addendum_p
document_kind: preregistration_addendum_p
```

## 0. 本書の位置づけ

本書は公表手続きの core (以下「本 core」) が §9 で閉集合として列挙する **追補 P** の**草案**である。
本 core の文章を一切変更しない。本 core が `p01`〜`p03` として名前だけ固定した数値と要件を確定する。

**発効点。** 本書は、本書を承認する決定を canonical 台帳へ fold した commit 以後にのみ効力を持つ。
**ユーザーの承認発話それ自体では発効しない。**発効前に公表表を生成してはならず、
resolver・producer・validator・消費側が本書を契約として読んではならない。
本書は自分自身の digest を本文へ書かない (自己参照の禁止)。

**本書は本 wave の凍結承認対象ではない。**理由は次の一点である。

> **従属先の三つ組をまだ書けない。**先行する追補 A・追補 B はいずれも `core_ref.commit` を
> 「その core を承認する決定を canonical 台帳へ **fold した commit `F`**」と定義しており、
> source core §15 の resolver 契約も `core_ref.commit` を `F` またはその子孫に限定する。
> すなわち `core_ref.commit` は**承認 fold commit** であって、文書を repo へ置いた内容 commit ではない。
> 本 core (`publication-core-v2.md`) の承認 fold commit は、ユーザーの凍結承認とその fold の後に
> しか存在しない。**承認より前の内容 commit をここへ書けば、意味のすり替えになる** —
> 既存意味の resolver は本書を永続的に解決失敗させ、内容 commit 意味へ緩めた resolver は
> 未承認 bytes を受理する集合を新たに開く。どちらも受け入れられない。

**従属先 core (三つ組。`commit` と `sha256` は未確定):**

```yaml
core_ref:
  path:   output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md
  commit: __UNRESOLVED_APPROVAL_FOLD_COMMIT__
  sha256: __UNRESOLVED__
```

`commit` には、本 core を承認する決定を canonical 台帳へ fold した commit `F_p` を入れる。
`sha256` には、その `F_p` の tree にある本 core blob の SHA-256 を入れる。
**この 2 値が確定するまで本書を凍結してはならない。**上の 2 つの literal は
「未確定であること」を機械的に検出可能にするための marker であり、値ではない。
**この marker を含む blob を承認・発効させてはならない。**

本書の `fields` は `{p01, p02, p03}` を**過不足なく**設定する (exact-key。欠落も余剰も解決失敗)。

**envelope の grammar (追補 A・追補 B と同一。変更しない):**

```text
envelope := metadata (先頭の fence) , preamble (§0) , fields , disclaimers (末尾節)
fields   := "## fields" の直後から、次の "## " 見出しまでの範囲
key      := fields の範囲内に現れる "### " 見出しの、先頭の空白なしトークン
```

**field key はこの規則で得た 3 個だけである。**§0 の `core_ref`、metadata の key、
本文中や末尾節に現れる `pNN` 形の文字列 (相互参照) は field ではない。
**全文を grep して `pNN` を集める形の解決を禁じる。**

**名前空間。**`p01`〜`p03` は source study の追補 A (`a01`〜`a13`) および追補 B (`b01`〜`b03`) と
**二義化しない。**本書は source study の追補 A / B の文書を継承・参照・合成しない
(本 core §9)。以下の値は source study の追補 B が同種の量について持つ値と一致するが、
それは **B4 (a)「引き継げるのは値であって文書ではない」** に従って**独立に再記述**した結果であり、
参照関係ではない。**本書から追補 B を読みに行ってはならず、追補 B が将来変わっても本書は変わらない。**

## fields

### p01 — 公表系列の候補数上限と許容 ordinal

```yaml
candidate_cap: 1
admissible_ordinals: [1]
immutable_in_this_addendum: true
```

本 core §8.1 が定める正規の根に属する公表候補の数の上限を `K_pub = 1` とする。
許容される候補 ordinal は `{1}` だけであり、ordinal `2` 以降を公表系列へ投入してはならない。
上限を超える ordinal の要求は、公表表を生成する**前**の admission deny とする。

**`K_pub = 1` は本 core・観測のいずれからも導出された値ではなく、governance の提案値である。**
本 core §9 は `p01` を「資源と governance の裁定であり、統計量から導けない」と明記している。
したがって**本 field の値はユーザー裁定の対象であり、承認パッケージで明示的に問う。**
根拠は、公表対象が source study の 1 候補ぶんの本走結果だけであり、
第 2 候補は新しいデータを要するため別途の資源裁定を要することに尽きる。

**本 field の値は本追補の中では不変である。**上限を引き上げる場合は、本追補を書き換えるのではなく、
同じ根と同じ `p02` の schedule を継承する新しい study と新しい追補を、
その候補のデータを 1 点も見る前に承認する。

**本 field は候補を数える時点を定めない。**候補が上限を消費する時点、および失敗後にそれが
復元しないことは、公表台帳の予約の側 (本 core §8.2 と `p03`) が決める。

### p02 — 公表系列の累積 spending 関数の数値割当て

```yaml
familywise_alpha: 0.05
spending:
  domain: k = 1, 2, 3, …
  alpha_pub_k: 0.05 / (k * (k + 1))
current_study:
  k: 1
  alpha_pub: 0.025
unspent_tail:
  reclaim: false
  redistribute: false
affects_primary_alpha: false
```

```text
Σ_{k≥1} 0.05 / [ k(k+1) ] = 0.05
```

したがって**候補数上限の値に依存せず**、上限を後から引き上げても、公表系列全体に配分される
familywise level の総和は `0.05` を超えない。未使用の tail は捨て、既存候補へ戻さない。
本 study は `k = 1` を占め、その公表 familywise level は `alpha_pub = 0.025` である。

**第 1 候補へ `0.05` 全額を割り当てる形は採らない。**全額を使い切ると、次の候補は必ず新しい根の下で
系列を立て直すことになり、そこで `0.05` を再取得できてしまう。独立な 2 候補がともに真の帰無なら、
少なくとも一方で偽の公表をする確率は `1 − 0.95² = 0.0975` となり、累積制御が空文になる。

**本 core §5.3 の条件判定 (本 field の義務)。**本 core §5.3 は、source study の primary が pass する枝で
同時下限と Holm の非整合が起こらない条件を `α_pub > α*` と定め、`α*` を
`c_B(13, α*) = q(13, 0.025)` の解として等式で与える。**判定は丸めた閾値ではなく等式で行う。**

```text
α*      = 6 · [ 1 − F_{t,12}( q(13, 0.025) ) ]
        = 0.014415014982840…
α_pub   = 0.025
判定     α_pub > α*  →  真 (0.025 > 0.014415014982840…)
```

**本 study の `α_pub = 0.025` はこの条件を満たす。**したがって公表表に
「primary が pass しても同時下限が 0 を含みうる」旨の併記は要らない。
`α*` を切り捨てた値を閾値にすると `α_pub = 0.01441501` のような値を誤って合格させるため、
丸めた閾値で機械判定するなら切り上げた `0.0144151` 以上を要求する (保守側)。

**`alpha_pub_k` は公表系列だけの量である。**source study の primary の有意水準、臨界値 `q` の
導出規則、受理条件、標本数の入力として使用してはならない。両者は数値が一致することがあっても
別 namespace の別量であり、消費側が alias してはならない。

**本 core §9 は `p02` を「familywise 予算の配分はユーザー裁定である」と明記している。**
したがって**本 field の値はユーザー裁定の対象であり、承認パッケージで明示的に問う。**

### p03 — 公表台帳の予約規則の実装契約 (台帳の同定・原子性の要件)

```yaml
requirements:
  ledger_not_chosen_by_caller: true
  reservation_mode: create_only
  reservation_atomic: true
  root_ordinal_unique: true
  release_on_failure: false
  ordinal_reuse: forbidden
ledger_identity:
  status: undetermined_by_this_addendum
```

本 field は公表台帳の予約が満たすべき**要件**だけを定める。

1. **台帳は呼び手が選べない。**予約先の台帳実体は、公表表を生成しようとする producer が
   引数・環境・checkout の選択によって変えられてはならない。
   **同じ根のまま台帳の実体を取り替えて累積をやり直す経路を閉じるのは、本 field の責務である。**
2. **予約は create-only かつ原子的である。**entry の作成だけを許し、更新・削除を許さない。
3. **`(publication_family_root, ordinal)` は一意である。**
4. **失敗・中断・未公表でも entry を削除せず、ordinal を解放または再利用しない。**
5. **宣言は権威ではない。**本 core §8.2 のとおり、台帳側の予約が無い、または重複しているなら
   公表表を生成しない。

**本 field は台帳の実体を同定しない。**台帳の path、所有者、bytes の serialization、
予約 operation の実装、transaction 境界は**本 field の外**にある。
本 core §9 は `p03` を「呼び手が選べない台帳の**実体が決まらないと確定しない**」と書いており、
裁定 **C-5 (a)** は機械執行を既存 producer 実装 wave 系列へ送っている。
**したがって台帳実体の同定は producer 実装 wave の裁定に残る。**

> **順序が閉じていない (承認パッケージへ返した事実)。**本 core §10.1 は追補 P を
> 「source study の pilot 1 本目の投入より前」に凍結せよと要求する。一方 §9 は本 field を
> 「台帳の実体が決まらないと確定しない」とし、C-5 (a) は実体の決定を producer 実装 wave へ送る。
> producer 実装 wave が pilot より後になるなら、この 3 つは順序として閉じない。
> 本書はこの矛盾を自分の側で一方的に解決しない。

**本 field は core §12 の必須記録項目を増やさず、validator の受理条件を追加しない。**
受領証にどの field を置くか、validator がどの照合を行うかは producer 実装 wave の責務である。

## 本書が主張しないこと

- **本書が凍結された、とは主張しない。**本書は草案であり、`core_ref` の 2 値が未確定である。
  この状態の blob を承認・発効させてはならない。
- **本書が投入 gate を機械的に実装した、とは主張しない。**resolver・producer・validator・
  消費側・公表台帳・投入 script はいずれも存在せず、producer 実装 wave の責務である。
  現在の exact-key 検査は source study の `a01`〜`a13` 専用であり、`p01`〜`p03` を検査しない。
- **本書が受領証 schema や validator の受理集合を定めた、とは主張しない。**
- **`K_pub = 1` と `α_pub = 0.025` が科学的に導出された値である、とは主張しない。**
  前者は承認済み資源上限に対応する governance の提案値、後者は familywise 予算の配分であり、
  いずれも本 core §9 がユーザー裁定と明記している。**本書はユーザー裁定の候補値を書いたにすぎない。**
- **公表手続きが有限標本で妥当である、とは主張しない。**cluster 代表値の分布が正規から外れると、
  `t` に基づく被覆も型 I 誤りも保証されない。この限界は本 core §7.1 が明示しており、
  本書が作り出したものではない。
- **本書が source study の追補 B を継承・参照・合成した、とは主張しない。**値の一致は
  B4 (a) に従う独立再記述の結果であり、参照関係ではない。
- **本書が pilot・本走のデータを 1 点も見ずに凍結された、とは主張しない。**主張できるのは
  「本書の 3 field はいずれも候補の通し番号と固定定数だけの関数であり、測定値を入力に取らない」
  ことだけである。時点の独立性は本書の文面からは検証できず、承認決定の fold commit、
  pilot 1 本目の外部 submission receipt、公表側 ordinal の予約 commit の前後関係によってのみ
  裏付けられる。本書はその前後関係を主張しない。
