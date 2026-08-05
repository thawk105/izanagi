---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t492-freeze-semantic-membership
seq: 2
---

## {{D:freeze-semantic-membership-at-schema}}. known 軸凍結の意味検査は schema 検証点に置く

**決定:** `s1_known_axes_freeze` の trigger 述語 semantic membership は、生成層
`_trigger_entries()` と**検証層 `_validate_schema()`** の 2 箇所で検査する。`verify_document()`
の内側だけに置かない。

**理由:**
- T-080 移行 receipt が active なとき、公開 oracle gate は static adapter へ委譲し、
  legacy `verify()` も `build_document()` も呼ばない。その経路が known 文書に対して通る
  意味検査の合流点は `_validate_schema()` だけである。
- 生成層だけでは、既に発行された文書を受理する側を守れない。検証層だけでは、
  producer が非正準文書を書き出すのを止められない (`generate()` は schema 検証を呼ばない)。
- 権威は既存の正準述語 index をそのまま使い、freeze 層で新しい正規化を作らない。
  受理集合は従来の受理集合との積へ狭まるだけで、拡大しない。

**却下した選択肢:**
- `verify_document()` 限定 — active 移行経路を素通りする。
- 生成層 1 箇所のみ — 受理側と、再構成を経ない移行 gate を覆えない。
- consumer 側 sink だけを増やす — 非正準凍結物の生成自体は止まらない (先行 wave の限界)。

## {{D:freeze-generator-self-hash-boundary}}. 自己 hash される generator の編集境界を定義する

**決定:** 凍結物の generator 自身を編集する変更では、不変条件を次の 2 つで書く。
(1) 凍結済み artifact の bytes を編集せず再発行しない。
(2) `generator_sha` を明示して射影した文書構築では、受理される入力に対し非 metadata field
(top-level field、挿入順、entry の name / flags / 述語、source 記録の要素数と内容) が完全に不変である。
「文書構築の出力を一切変えない」とは書かない。

**理由:**
- generator の自己 hash は生成器の bytes から作られるため、生成器を 1 byte でも編集すれば
  既定引数の構築結果はその 1 セルだけ必ず変わる。AST 不変や規則不変は値不変の証明にならない。
- 下流の影響は限定できる。移行 receipt の active 検証は generator セルを静的再構成比較から
  除外し、metadata 照合も移行基準 commit の blob と行うため、live 編集で壊れない。
  一方 legacy 検証は live の生成器 bytes を直接 hash するため、既存凍結物に対する
  拒否理由と診断順が変わる。この差を記録しないと「bytes 不変」と「全検証経路の受理性不変」を
  取り違える。

**却下した選択肢:**
- 生成器を編集せずに済ませる — 検査の呼び出しは同じファイルに要るため不可能。
- 同じ wave で再凍結する — 移行 receipt が旧 raw hash を定数で固定しており、
  再凍結は世代移行の設計を要する別作業になる。
