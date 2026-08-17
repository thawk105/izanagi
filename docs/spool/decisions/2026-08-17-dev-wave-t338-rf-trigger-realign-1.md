---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t338-rf-trigger-realign
seq: 1
---

## {{D:rf-trigger-pilot-realignment}}. RF 発火条件 (ii) の評価領域を承認済み receipt へ束縛して attestation の重複列挙を外し、pilot 投入を公表層から切り離す — 解禁ではなく依存の分離である

**背景:** D162 決定 (10) は独立 validator の機械化を 3 条件の連言に懸けた。2026-08-16 の再監査は、
成立しているのは条件 (i) だけであり、(ii) は 4 項のうち環境タグと attestation の 2 項が artifact
全文検索で 0 file hit、(iii) は RF 判定を読む consumer が 0 件であることを項目単位で実測した。
(ii)(iii) を成立させる唯一の計測は D229 決定 (6) が設計した pilot であるが、その pilot は D291 の
運用状態が置いた依存辺により、公表層実装の完了を待つ位置に置かれていた。公表層の残り実装は
D320 により保留終端である。したがって RF 系列全体が、D320 が「論文主張に不要」と裁定した領域に
無期限で待たされていた。一次資料 = `output/insights/2026-08-16_t338-rf-validator-trigger-audit/`
および `output/insights/2026-08-17_t338-rf-trigger-realign/`。ユーザー裁定 (2026-08-16) は
発火条件からの attestation 除去と pilot 解禁条件からの公表層切り離しを先に確定させ、そのうえで
producer から consumer までを 1 scope へ戻すこととした。

**決定 (1): D162 決定 (10) の発火条件 (ii) の評価領域を、D282 が承認 payload で pin した
receipt schema に適合する pilot receipt に束縛する。** (ii) は「その計測が環境タグ・測定 checkout・
pin を持つこと」の 3 項の連言とし、attestation は列挙から外す。条件 (i) と (iii) は改訂しない。
D162 本文は編集せず、本 D が (ii) の現行版を持つ。

**これは証拠水準の引き下げではなく、重複列挙の削除である。** D282 が pin した receipt schema
(`output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json`、sha256
`d541ccd5919c7c3545c04a806ca7f9cf04e6391cdf1791d7b9273317199b047e`) は `environment` を必須にし、
その `required` に `attestation_mode` と `attestations` を持ち、前者は `{"const": "required"}`、
後者は `minItems: 2` の配列である。すなわち評価領域を束縛した時点で attestation は receipt 側で
引き続き必須であり、(ii) の列挙から外しても受理される計測の集合は 1 つも増えない。
束縛を書かずに列挙だけを外せば、attestation を持たない計測が発火証拠として新たに受理される。
本 D は前者を選ぶ。

**決定 (2): 3 項は「存在」ではなく「照合できること」を要求する。** 環境タグ・測定 checkout・pin の
各項は、artifact の当該 field が実在するだけでは (ii) を満たさない。**producer の自己申告以外の
経路で、計測時の実環境・実 checkout・実 pin と照合できること**を要求する。schema 適合は
これらの field の存在を保証するため、存在だけを要求する読み方では (ii) は何も拒否しない。
2026-08-16 の監査が (ii) を項目単位で照合したのと同じ粒度を、以後の (ii) 判定にも課す。

**決定 (3): 環境タグは落とさない。受理集合も緩めない。** D320 は「測定の公正 (環境契約タグ)」を
対象外 (不変) と明記している。`orchestrator/qualification/contract.py` の Pegasus 環境契約
(`env_tag` / `attestation_mode`) は本 D の対象外であり 1 byte も変更しない。本 D が動かすのは
D162 の**機械化発火条件**だけであって、qualification / admission の受理条件ではない。

**決定 (4): D291 の `operational_state_on_fold.addendum_p_freeze_precondition` の
最終文「pilot もそれまで投入しない。」だけを前向きに失効させる。**

- **失効の対象:** 引用した 1 文だけである。同 field の前 2 文
  (「公表台帳の実体が確定していること。」「実体の同定は公表層実装 wave の裁定事項であり、
  それが済むまで追補 P を凍結してはならない。」) は**追補 P の凍結条件として維持する**。
- **発効時点:** 本 D が canonical 台帳へ fold された後の将来の pilot 試行に対してのみ適用する。
  遡及効果は持たない。
- **保存する範囲:** D291 の bytes、承認 payload、承認済み三つ組、値射影、exact closure、
  `operational_state_on_fold` の他の全 field を保存する。本 D は D282 / D322 と同じく、後続
  decision が射程を限定して前向きに失効させる形だけを使う。D291 の payload は固定 commit の blob
  から読まれ、`operational_state_on_fold` を含む各節は sha256 で pin されているため、
  本 D の追記は resolver が読む bytes を 1 byte も変えない。
- **同時に保存する公表側の禁止:** pilot が将来実走可能になっても、公表 core の分析 admission が
  追補 P を要求すること、追補 P の blob が未承認であること、`p03` が未確定であること、
  および pilot 産物を公表台帳へ投入することの禁止は、いずれも維持する。

**決定 (5): 本 D は pilot 投入の解禁ではない。** `pilot_submission = forbidden` と
`main_submission = forbidden` は維持される。D292 が定めた「禁止を解除できるのは canonical 台帳へ
fold された decision だけである」という解除権威も維持する。本 D が変えるのは、**将来の解除
decision が公表層実装の完了を必要条件としない**という 1 点だけであり、**現在の状態遷移は無い**。
本 D、worklog、実装完了報告、manifest、handoff のいずれも投入権限を付与しない。deny-only 公表
report の直値 (`submission_authority = not_granted` / `pilot_submission = forbidden` /
`main_submission = forbidden`) も変更しない。

**決定 (6): 解除条件の中身は本 D でも定めない。** D292 は解除条件を意図的に未定義に保ち、その理由を
「未実装・未検証の gate の合格条件を中身を見ずに凍結すると、実装が条件に合わないとき条件側を
緩める圧力が生まれる」と書いた。本 D はこの境界を動かさない。以下は**非網羅的な実装 backlog**
であって、解除の必要条件でも十分条件でもない。

- RF producer と attempt registry の実体 (raw receipt を出す producer が存在しない限り、
  validator は合成 fixture しか読めない)。
- D282 が pin した record-items / receipt schema を強制する producer と、その semantic validator の
  実装。**記録項目そのものは D282 で承認済みであり、未確定ではない。**
- exact 環境契約の下での pilot 実走。

D162 決定 (10) の条件 (iii) (判定を読む consumer の実 hook) は validator / consumer 段で満たす
残件であり、pilot の解除条件ではない。

**決定 (7): `producer → pilot → validator/consumer` を 1 つの task scope へ戻す。**
これは原子的実装や並列実装を意味しない。D229 決定 (6) の全順序
`producer → pilot → validator/consumer → 本走` は保存し、pilot 自身を発火条件の充足計測にする
設計も保存する。**D229 決定 (6) の「D162 を supersede しない」は D229 自身についての非 supersede
宣言であり、後続 canonical decision が D162 を改訂することを禁じるものではない。** 本 D の
決定 (1) はその後続改訂であって、D229 の順序を動かさない。本走が validator / consumer より
後であることも、本走の投入禁止も変わらない。

**却下した選択肢:**

- 環境タグも (ii) から落とす — D320 が対象外 (不変) と明記した測定の公正に触る。
- 評価領域を束縛せずに attestation の列挙だけを外す — attestation を持たない計測が発火証拠として
  新たに受理される。受理拡大であり絶対規律 2 が禁じる方向。
- `attestation_mode` を optional にする、または環境契約を緩める — 同上。発火条件の証拠水準と
  受理条件は別であり、後者は本 D の対象外である。
- D291 を直接書き換える — 同 D の節は sha256 で pin され、payload は固定 commit の blob から
  読まれる。bytes を変えれば承認経路が壊れる。
- 本 D を pilot 解禁として扱う、または解除条件を完全リストとして先に凍結する — D292 の解除権威と、
  同 D が名指しした「条件側を緩める圧力」の禁止に反する。
- validator を pilot より先に置く — raw receipt を出す producer が 0 件のため、合成 fixture だけで
  緑になる未結線 leaf になる。D147 決定 (3) / D163 決定 (1) が却下した型であり、D229 決定 (6) が
  「残る risk」として名指しした事象そのものである。
- D229 決定 (6) の 4 段階を 2 段階へ縮める — pilot の記録項目が validator の要求を取りこぼしたとき
  pilot ごとやり直しになる。記録項目の確定を単独 gate にした費用はこの risk に見合っている。

**研究状態への影響:** certified 選択の値、材料レポート、proof chain、凍結 bytes、既存 gate、
受理集合はいずれも**不変**である。実装差分はゼロであり、producer・pilot artifact・
validator / consumer のいずれも本 D では生成しない。**変わる executable output は 2 つだけである** —
deny-only 公表 report の `supersession_scan.decision_ids` に本 D の ID が 1 件加わること
(`status` は追記前から `possible_supersession` であり変わらない)、および台帳の D 採番が 1 つ進むこと。
条文として変わるのは、発火条件 (ii) の評価領域と列挙、pilot と公表層の間の依存辺、
そして RF 系列の task ownership の 3 点である。
