---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-t2183-knowledge-provenance
seq: 2
---

## {{D:knowledge-provenance-rides-policy-hint-path}}. 知識 provenance の材料レポート記録は policy_hint の経路と同型にし、schema 版を上げない

**決定:** 材料レポートへ知識水準と知識源を記録する欄は、既存 `policy_hint` の記録経路と**同型**に
する。campaign lock の `search_config` 由来の値を top-level の名前付き欄に置き、schema の
`properties` へ追加するが top-level `required` には入れず、producer は知識非対応 campaign でも
`null` を必ず出す。`SCHEMA_VERSION` は据え置く。

D1429 が要求する「材料レポートの proof chain」は、この 1 欄で満たす。欄の中身は
`knowledge_level` / `knowledge_manifest_sha256` / `declared_sources` / `injected_sources` の 4 つで、
nested 側は `additionalProperties: false` と 4 欄すべての `required` で締める。source の
本文は載せず identity と digest だけを射影する。

**理由:**

- `policy_hint` を材料レポートへ追加した commit `627c5019e` は `SCHEMA_VERSION` を上げていない。
  現行 schema の top-level property 21 個に対し `required` は 16 個で、必須でない 5 個
  (`acceptance_receipt`、`certifying_input`、`campaign_verifier_epoch`、
  `current_verifier_conformance`、`policy_hint`) は「legacy 文書では欠落しうるが producer は
  常に出す」という確立した型である。同じ形の追加に別の型を導入する理由がない。
- `policy_hint` の欄そのものは schema 上 `string` または `null` の単一スカラであり、2 段の
  source 集合を載せられない。**欄は相乗りできないが経路は相乗りできる**というのが実測の結論である。
- 版を上げる案は、非知識 campaign の既存期待値まで一斉に書き換えることになり、本 wave が
  「既存テストの期待値を変更しない」を守れなくなる。

**既知限界 (解決したと書かない):**

- 古い schema file を別に持つ repo 外の読み手は、同じ版 literal の新欄を
  `additionalProperties: false` により拒否しうる。これは `policy_hint` 追加時から同型で存在する
  性質であり、本決定が新たに作る欠陥ではない。
- 本 schema は producer の保証より緩く、単独で改竄検知の境界にはならない。canonical path、
  identity の一意性、digest との整合は内側の試行台帳側の検査が担う。`workload` を無制約 object に
  している現行設計と同型の割り切りである。

**却下した選択肢:**

- **版を上げて欄を必須にする** — 契約としては明快だが、既存期待値の一斉変更を伴い、本 wave の
  不変条件と両立しない。repo 外の読み手のために版交渉が必要になった時点で改めて判断する。
- **欄を足さず、既存の無制約 object と生の台帳 event に載っている値を相乗り経路と呼ぶ** —
  値は確かに既に載っているが、schema が何も制約せず何にも束縛されないため、
  「分けて記録する」「proof chain に結ぶ」という要求を満たさない。
- **schema の後段に semantic validator を新設する** — 指摘された入力は内側の層が既に拒否しており
  冗長である。効果が未実証の段階で分類機構を足すのは D1429 が却下した方向である。

## {{D:two-tier-knowledge-record-projects-existing-receipt-fields}}. 2 段の知識源は受領証の既存 2 欄から射影し、一致の保証は既存検査に委ねる

**決定:** 「参照を許した範囲」は受領証の `canonical_manifest.sources`、「実際に投入した知識源」は
受領証の検証済み `sources` から、**それぞれ独立に**射影する。両者の一致を確かめる新しい検査は
足さない。受領証読み出しは同じ read の raw digest も返し、材料レポートの参照一覧に載る同 path の
digest と一致しなければ停止する。

**理由:**

- 試行台帳側の受領証読み出しは、検証済み source 集合と canonical manifest の source 集合が
  一致しないことを既に fail-closed で拒否している。**現行 producer では 2 段は必ず同じ集合になる。**
  この一致を新しい述語で確かめても恒真であり、保護として数えられない。
- 一方で、2 段を同じ配列の複製として書くと、各欄がどちらの出所由来かを実装から独立に監査できず、
  将来その一致検査が外れたときに別名だけが残る。出所を分けることには意味がある。
- 独立に抽出した投入集合を新たに作る案は、既存の一致検査を迂回しなければ差が出せない。
  迂回は正しさゲートの弱体化であり、採らない。
- 受領証を検証する read と参照一覧が digest を取る read が別のままだと、間で差し替えたときに
  「ある受領証の知識源」と「別の受領証の digest」を同時に載せた自己矛盾したレポートが作れる。
  同じ read の digest を束縛するのは、既存の lock・試行台帳の再 hash 検査と同型の措置である。

**主張の境界:** 記録されるのは harness が解決・検証して role 入力へ投影した source 集合であって、
モデルが実際にそれを読んだ証明でも、context の書込みが成功した証明でもない。この限界は
記録に明示し、機構では埋めない。

**却下した選択肢:**

- **投入集合を実際に emit された payload から独立抽出する** — 同じ projection を渡して同じ
  projection から取り出す形になり照合が恒真になる。受領証発行が書込みより先だと、書込みが
  失敗した走行でも「投入済み」の受領証だけが残る。
- **投入集合の独立 digest を campaign identity へ加える** — 同じ集合を別形式で再 hash するだけで、
  既存の知識対応 campaign と識別子が分断される副作用だけが残る。
- **受領証の新しい世代を作る** — 記録される source identity は現行世代と同じである。

## {{D:legacy-knowledge-report-comparison-not-patched}}. 知識対応 legacy レポートの比較補正は、発火する成果物が現れるまで実装しない

**決定:** 材料レポート全体を再生成物と照合する完全性検査に、新欄を持たない**知識対応**レポートの
ための補正は入れない。非知識レポートの欠落補正だけを入れる。

**理由:**

- 発火集合が空である。実測したところ、知識水準を宣言した campaign は成果物ツリーに 1 件も
  存在しない。唯一の走行は repo 外の探索ツリーにあり、そのレポート出力先は空である。
  発火条件を満たす既存 artifact path を書けない機能は設計メモに留める。
- 提案された是正 (persisted 側に欄が無ければ両側から欄を除外する) は、provenance を持たない
  知識対応レポートを完全性検査で黙って通すことになる。落ちる現在の挙動のほうが D1429 の要求に
  忠実である。
- 本決定以降に生成されるレポートはすべて欄を持つため、この隙間は自然に閉じる。

**再裁定の条件:** 新欄を持たない知識対応レポートが実在した時点で、上の 2 番目の理由と
併せて改めて判断する。存在しないうちに機構を足さない。
