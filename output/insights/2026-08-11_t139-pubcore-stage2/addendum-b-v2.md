# [T-139] 本走 — 事前登録 追補 B 再発行版 (案。ユーザー承認前は発効しない)

> **本書は初版 `output/insights/2026-08-09_t139-addendum-b/addendum-b.md` の再発行版である。**
> 再発行の根拠は裁定 **C-2b (a)** であって `authority: none` そのものではない。
> 初版は歴史記録として不変のまま残し、本書がそれを置き換える。
> **本書の blob には初版とは別の承認が要る。**初版を承認した事実は本書へ引き継がれない。
> 変更は `b03` の縮小 1 点だけであり、`b01`・`b02` は初版の逐語をそのまま保つ。

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / addendum_b
document_kind: preregistration_addendum_b
```

## 0. 本書の位置づけ

本書は凍結事前登録 core が §14 で閉集合として列挙する **追補 B** の**草案**である。
core の文章を一切変更しない。core が `b01`〜`b03` として名前だけ固定した数値と手続きを確定する。

**発効点。** 本書は、本書を承認する決定を canonical 台帳へ fold した commit 以後にのみ効力を持つ。
**ユーザーの承認発話それ自体では発効しない。**発効前に本走を投入してはならず、
resolver・producer・validator・消費側が本書を契約として読んではならない。
本書は自分自身の digest を本文へ書かない (自己参照の禁止)。

**従属先 core (path・commit・blob digest の三つ組):**

```yaml
core_ref:
  path:   output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256: ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

`commit` は限定例外の決定 (D234) を canonical 台帳へ fold した commit `F` である。
**本書はこの三つ組を静的に記載するだけであり、`F` が将来の測定 checkout の祖先であることを
主張しない。**祖先性は投入時に resolver が `repository_root` の実 checkout から導出した
`measurement_head` に対して検査する (core §15)。

本書の `fields` は `{b01, b02, b03}` を**過不足なく**設定する (exact-key。欠落も余剰も解決失敗)。

**envelope の grammar (追補 A と同一。変更しない):**

```text
envelope := metadata (先頭の fence) , preamble (§0) , fields , disclaimers (末尾節)
fields   := "## fields" の直後から、次の "## " 見出しまでの範囲
key      := fields の範囲内に現れる "### " 見出しの、先頭の空白なしトークン
```

**field key はこの規則で得た 3 個だけである。**§0 の `core_ref`、metadata の key、
本文中や末尾節に現れる `bNN` 形の文字列 (相互参照) は field ではない。
全文を grep して `bNN` を集める形の解決を禁じる。
**本書は fields 範囲内の fenced block に `## ` / `### ` で始まる行を置かない** —
grammar は fence を除外しないため、置くと key の解決が一意でなくなる (追補 A も同じ規律で書かれており、
同文書の fields 範囲内に該当行は 1 件も無い)。

**本書は追補 A の field へ要件を足さない。**追補 A が固定した primary 系列の有意水準・根・ordinal・
予約契約 (`a13`)、臨界値の導出規則 (`a11`)、標本数と資源内訳 (`a10`) は本書の対象外であり、
本書はそれらを参照するだけである。

**本書は core の admission 述語を狭めない。**core は `pilot_admission: requires_addendum_a`、
`main_admission: requires_addendum_a_and_b` と定める。本書が拒否を課すのは
**`submit_main` の投入前**だけであり、pilot の受理条件を追加しない。

---

## fields

### b01 — 候補数上限

```yaml
candidate_cap: 1
admissible_ordinals: [1]
reservation_mode: create_only
release_on_failure: false
immutable_in_this_addendum: true
```

正規の根に属する候補数上限を `K = 1` とする。許容される候補 ordinal は `{1}` だけであり、
ordinal `2` 以降を投入してはならない。上限を超える ordinal の投入要求は、
`submit_main` の投入**前**の admission deny とする。

候補は canonical な予約 entry が create-only で確保された時点で 1 件と数える。
**失敗・中断・未公表でも ordinal を解放、再利用、付け替えしない。**
同一候補について事前登録済みの予備割当てを使うことは新しい候補に数えないが、全 attempt を保持する。

**`K = 1` は core・追補 A・観測のいずれからも導出された値ではなく、governance の提案値である。**
根拠は、承認済みの総ポイント上限が 26 割当て相当 (裁定 U10) であり、
その内訳 — 追補 A の `a10` が確定した
`検証割当て 1 + pilot 8 + pilot 予備 2 + 本走 J_max 13 + 本走 予備 2 = 26` —
がちょうど候補 1 本分であることに尽きる。第 2 候補は別途の資源裁定を要する。
**「候補の exact bytes が 1 本だから上限も 1」という導出は成立しない** —
現在の候補 identity 数と、系列全体の将来 ordinal 上限は別の量である。

**本 field の値は本追補の中では不変である。**上限を引き上げる場合は、本追補を書き換えるのではなく、
**同じ `b03` の正規の根と同じ `b02` の schedule を継承する新しい study と新しい追補を、
その候補のデータを 1 点も見る前に承認する。**本追補の blob と、本追補に束縛された過去の結果は
不変のまま残し、resolver は結果の記録が参照する三つ組で effective な追補を決める。

### b02 — 個別公表系列の累積 spending 関数の数値割当て

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
affects_primary_q: false
```

```text
Σ_{k≥1} 0.05 / [ k(k+1) ] = 0.05
```

したがって**候補数上限の値に依存せず**、上限を後から引き上げても、個別公表系列全体に配分される
familywise level の総和は `0.05` を超えない。未使用の tail は捨て、既存候補へ戻さない。
本 study は `k = 1` を占め、その個別公表 familywise level は `alpha_pub_1 = 0.025` である。

**第 1 候補へ `0.05` 全額を割り当てる形は採らない。**全額を使い切ると、次の候補は必ず新しい根の下で
系列を立て直すことになり、そこで `0.05` を再取得できてしまう。独立な 2 候補がともに真の帰無なら、
少なくとも一方で偽の公表をする確率は `1 − 0.95² = 0.0975` となり、累積制御が空文になる。

**本 field が定めるのは配分の数値だけである。**本 field は次のいずれも定めない。

- 個別公表 family を構成するセルの identity
- 公表用の検定統計量、帰無分布、未調整 `p` 値の構成
- 多重性の調整方式 (Holm / closed testing のいずれを採るか、その適用順序)
- 公表する同時区間の構成、および区間と棄却判定の対応関係

これらは core §10・§16 と裁定 Q7 が属する**公表手続き**の側にあり、追補 B の閉集合の外である。
`alpha_pub_k` は、その公表手続きが確定したときに、その family へ与える familywise level として使う。

**参照 (非規範。本 field はこれらを固定し直さない):**
core §10 は個別公表を primary の成否にかかわらず 6 セル全件の固定表で行うと定め、
core §16 は調整済み `p` 値と同時区間の公表を求める。追補 A の `a10` は
`k = 1..6` を `(N_W1, H_W1, G_W1, N_W2, H_W2, G_W2)` と列挙し、
`T_k = √J · μ̂_k / s_k` を定義している (ただしそれは標本数設計のための planning 統計量として定義された)。
裁定 Q7 は個別公表に Holm または closed testing を、裁定 R5 (a) は `RF` を載せる表への
正分母 guard (`qualification_status` の併記) を定めた。

`alpha_pub_k` は個別公表系列だけの量である。**primary 系列の有意水準 `α_k`、臨界値 `q` の導出規則、
受理条件、標本数の入力として使用してはならない。**両者は数値が一致することがあっても
別 namespace の別量であり、消費側が alias してはならない。

> **本 field だけでは公表表を生成できない。**上に列挙した公表手続きが未確定である以上、
> `alpha_pub_1 = 0.025` は適用先を持たない。この欠落を追補 B で埋めることは閉集合の違反であり、
> どこで埋めるか (新しい core を起こすか、他の経路か) は `package.md` の裁定が扱う。

### b03 — 累積台帳を束縛する正規の根の同定方法

```yaml
publication_family_root:
  fold_commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  ledger_kind: individual_publication
```

個別公表系列の累積台帳を束縛する**正規の根**は、上の `publication_family_root` の literal から
導出する。**caller の引数、受領証の申告値、親系列 ID、試行 ID を入力にしない。**
`fold_commit` は限定例外の決定 (D234) を canonical 台帳へ fold した commit `F` である。
新しい正規の根を作れるのは、新しい study を承認する canonical なユーザー裁定だけであり、
**候補数上限の引き上げは新しい根を作る理由にならない** (`b01`)。

**別台帳である。**個別公表台帳は primary 台帳とは別の canonical 台帳とし、累積量・entry・ordinal を
混合しない。**本書は primary 台帳へ書かず、`a13` が固定した primary 側の予約契約へ要件を足さない。**
本 field は primary 側の予約 entry を公表側の受理条件にしない (裁定 B5 は不採用で終端しており、
`b03` に primary 台帳への参照を置かない。将来この参照を復活させてはならない)。

**本 field が定めるのは根の同定方法までである。**公表台帳の予約 — 台帳実体の同定、原子性、
create-only、`(root, ordinal)` の一意性、ordinal の非解放 — は本 field の範囲外であり、
**本 field はそれらを定めない**。この縮小は裁定 C-2b (a) による。予約の正本がどこにあるかは
本書の閉集合の外にあり、**本書はその所在を名指ししない** (本書は自分の従属先 core 以外の文書を
参照・継承・合成しないため)。

**本 field は core §12 の必須記録項目を増やさず、validator の受理条件を追加しない。**
core §12 が列挙する必須項目に、公表台帳の path・予約 entry の digest・予約 commit は含まれていない。
これらを受領証の必須記録に加えることは、必須 schema と受理集合を変える **core の変更**である。
core §12 は producer が宣言できる閉集合の種別について「field 名は実装 wave の新 D で確定する」と
定めており、`b03` はその決定を先取りしない。**受領証にどの field を置くか、validator がどの照合を
行うかは producer 実装 wave の責務である。**追加の受領証 schema が必要になったなら、
それは新しい core を伴う**別 study** の裁定対象とする (core §14)。

**失敗分類を増やさない。**本 field は core §9 の attempt failure 分類を 1 つも増やさない。
性能測定の**開始後**に根の同定に関する不一致が判明した場合は core §9 の既存分類へのみ写し、
**予備割当てによる置換・新しい失敗分類の作成を行わない。**
開始後の失敗を開始前の infra failure へ写さない (core §13 の否定検査 8、§14 の線)。

> **本書だけでは閉じない。** 「根を自己申告でリセットできない」という規範は、根の値が固定 literal
> であることで**本書の内部だけで閉じる** — 根は caller の入力を 1 つも取らないため、
> 呼び手が別の根を名乗る経路は存在しない。
> **一方、同じ根のまま台帳の実体を取り替えて累積をやり直す経路は、本 field では塞がらない。**
> それは台帳実体の同定の問題であり、`b03` の範囲外である (上記の縮小を参照)。
> 台帳の実体化・所有者・予約操作・digest の bytes は producer 実装 wave の責務であり、
> 本書はコードを追加しない。
> **本 field は規範であって、現時点で発火する active gate ではない。**
> なお本 field は恒真な deny ではない — 固定 literal から導出した根をそのまま使う正経路が存在し、
> それを通れば解決は成功する。

---

## 本書が主張しないこと

- **本書が投入 gate を機械的に実装した、とは主張しない。**本書は文書上の値と規則だけを定める。
  resolver・producer・validator・消費側・台帳・投入 script は producer 実装 wave の責務である。
- **本書が受領証 schema や validator の受理集合を定めた、とは主張しない。**`b03` の規範範囲は
  正規の根の同定方法 (固定 literal からの導出と caller 非選択) までであり、core §12 の
  必須記録項目を 1 つも増やさない。台帳の実体化と照合手順は producer 実装 wave の責務である。
- **本書が公表台帳の予約を定めた、とは主張しない。**初版 (`2026-08-09_t139-addendum-b/addendum-b.md`)
  の `b03` が持っていた次の 5 つは、裁定 C-2b (a) により本再発行で**落ちた** — (i) `current_study.ordinal`
  と `reservation` / `separate_ledger` の yaml、(ii)「producer が選べない canonical な台帳で原子的に」、
  (iii)「`(publication_family_root, ordinal)` は一意でなければならない」、
  (iv)「失敗・中断・未公表でも ordinal を解放または再利用しない」、
  (v)「この一意性が成立しないまま本走を投入してはならない」。
  **(v) は投入前 admission であったため、本再発行によって本走の投入 gate が 1 つ減る。**
  この帰結は承認パッケージで明示的にユーザーへ返した。
- **本書が公表手続きの正本である、とは主張しない。**公表セルの identity、検定統計量、`p` 値の構成、
  多重性の調整方式、同時区間の構成は本書の閉集合の外にあり、**現時点でどの凍結文書にも
  一意には定まっていない。**この欠落を本書は解消しない。
- **公表手続きが有限標本で妥当である、とは主張しない。**追補 A が `a11`・`a12` について明示したのと
  同じ限界がここにも及ぶ — cluster 代表値の分布が正規から外れると、`t` / Hotelling に基づく
  被覆も型 I 誤りも保証されない。段 6 のレビューは、`E[Z] = 0` の混合分布で `J ≤ 13` の
  周辺 `t` 検定が名目水準を破る構成を示した。**この限界は primary 側にも等しく及び、本書が
  作り出したものではない。**
- **core §7 の weak null 較正義務が満たされた、とは主張しない。**裁定 R2 (a) は同義務を
  「事前固定 stress check」へ置換すると定めたが、**その erratum 文書は本書の作成時点で未発行である。**
- **`K = 1` が科学的に導出された値である、とは主張しない。**承認済み資源上限に対応する
  governance の提案値である。
- **`F` が将来の測定 checkout の祖先である、とは主張しない。**§0 の三つ組は本書の作成時点の
  checkout に対する静的な記載であり、祖先性は投入時に resolver が毎回導出して検査する。
- **凍結成果物の pin 面をすべて列挙した、とは主張しない。**`FROZEN_MANIFEST`・generator source
  hash・role 名を key とする review ledger・key→canonical path 束縛を検索して本 study の
  事前登録族への hit は無かったが、未知の key 側 pin が無いことは示していない。
- **本書が pilot・本走のデータを 1 点も見ずに凍結された、とは主張しない。**主張できるのは
  「本書の 3 field はいずれも候補の通し番号と固定定数だけの関数であり、測定値を入力に取らない」
  ことだけである。**時点の独立性は本書の文面からは検証できず**、承認決定の fold commit、
  pilot 1 本目の外部 submission receipt、公表側 ordinal の予約 commit の前後関係によってのみ
  裏付けられる。本書はその前後関係を主張しない。
