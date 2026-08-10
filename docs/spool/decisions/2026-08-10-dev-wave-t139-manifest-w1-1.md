---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t139-manifest-w1
seq: 1
---

## {{D:erratum-registry-membership-is-not-approval}}. erratum の「検査可能性」と「承認」を独立 2 軸で持ち、D263 の「第 2 erratum は既に承認済み」を前向きに失効させる

**決定:** 凍結 core への erratum の状態を、**排他的な 3 値ではなく独立した 2 軸**として型と
機械検査で区別する。

```text
軸 1 validator:  unregistered | registered   erratum_id 別 registry に固有 validator が居るか
軸 2 approval:   draft_unapproved | approved  承認 manifest の approved_errata に属するか
```

2 軸は独立でなく、次の含意だけを課す — **`approved` ならば必ず `registered`** である
(検査方法の定まらない文書を承認できない)。逆は成り立たない。
`registered ∧ draft_unapproved` は正当な状態であり、本決定を書いた時点の第 2 erratum が
まさにそれである。

**「registered を第 3 の状態として draft / approved と並べてはならない。」**
並べると、後続 resolver が「approved は registered とは別状態」と読み、
承認済み erratum の固有 validator を飛ばすか、逆に承認済み文書を拒否する。

**registry への登録は承認ではない。** registry は「この ID の文書をどう検査するか」だけを定め、
「適用してよいか」は定めない。承認集合を問う経路は draft を返してはならない。

あわせて D263 の理由節にある「実際、同じ core に対する第 2 の erratum が既に承認済みである」を
**前向きに失効させる。** その erratum 文書は当該決定の時点で存在しておらず、承認されていたのは
第 2 erratum を当てるという**方向**であって文書ではない。D263 の決定本文
(固有不変条件を `erratum_id` 別 validator に持たせ、未知 ID を fail-closed にする) は有効なまま残す。

**理由:**

- 承認済み erratum の resolver 契約は「resolver は approval manifest から
  `approval_fold_commit` と blob identity を取得する。caller の引数や受領証の自己申告からは
  取らない」を課す。registry membership を承認と読む実装は、この trust root を
  **コード側の import 可能性**へすり替える。erratum を 1 枚足して registry へ登録するだけで
  受理述語が動く経路になる。
- 実際に本 wave は未承認の第 2 erratum を起草した。三値の区別が無ければ、
  その validator を登録した瞬間に「承認済み」と読める状態になる。
- 逆に、誤記を保守側へ読んだ実装は第 2 erratum を永久に拒否する。どちらへ倒れても
  受理集合が実装依存になる。

**却下した選択肢:**

- 誤記を「説明文だから無視してよい」として放置する — canonical decision を根拠に
  実装を書く後続 wave が、承認集合を 2 通りに解釈する。無視ではなく上書き記録が要る。
- D263 全体を失効させる — 決定本文 (固有検査の分離と未知 ID の fail-closed) は正しく、
  実装済みで機能している。失効させるのは事実文 1 つでよい。
- 承認状態を文書の frontmatter だけで表す — 文書は producer 側が書けるので trust root にならない。
  承認集合は manifest 側にしか置けない。
- registered / draft / approved を排他的な 3 値として並べる — 実装上すべての approved と draft は
  同時に registered であり、3 値は排他にならない。排他でないものを排他として書くと、
  後続実装が「approved は registered でない」と読む余地を残す。

**本決定が主張しないこと:**

- **承認が機械的に強制されている、とは主張しない。** 本決定の時点で承認集合を問う関数に
  production caller は無く、参照束縛の純関数 (`compose_core` 相当) は登録済みでさえあれば
  未承認 erratum も合成できる。これは「純関数は投入 gate ではない」という D264 の境界どおりであり
  fail-open ではないが、**承認の強制は投入 gate を実装する wave の責務として残る。**
  本決定を「承認検査が入った」と読んではならない。
