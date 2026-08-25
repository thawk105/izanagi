---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1291-t1282-layer3-holes
seq: 2
---

## {{D:layer3-runs-widening-holds-version}}. 層 3 の `runs.items` を広げても `schema_version` は据え置き、前方互換は保証しない

**決定:** `layer3_schema.json` の `runs.items.properties` へ optional property を足す変更では
`schema_version` を上げない。`required` も変更しない。**旧 checkout の reader が新しい document を
読めること (前方互換) は保証しない。** 保証するのは後方互換 — 新しい reader が既存の
v1 / v2 / v3 artifact を読めることだけである。

**理由:**
- 先例が 2 件あり、どちらも版を据え置いて同じ場所へ足している。`rep_returncodes` は
  `067f4b1f` (2026-07-20) で `schema_version` を v2 のまま追加、`perf_observation` は
  `f383d75d` (2026-08-17) で v3 のまま追加した。
- 版を上げると reader が v2 / v3 / v4 の 3 経路になる。現行 reader は v3 schema を変異させて
  v2 reader を導いており、この導出鎖が複雑になるほど**後方互換を壊しやすくなる**。
  守るべき性質を守るために、守らない性質のために構造を複雑化しない。
- report は `meta.generator.sha256` で生成器へ束縛されており、版文字列だけが document の
  同一性を担うわけではない。

**却下した選択肢:**
- 新規発行を v4 にし v3 schema を凍結する — 段 3 の 2 レンズが揃って主張した。論点は
  「新 checkout が出した v3 document を旧 checkout の v3 reader が読めない」= 前方互換であり、
  この repo が一度も保証していない性質である。上記のとおり後方互換を守る側の負担が増える。

## {{D:layer3-material-report-projects-producer-values}}. 層 3 の材料レポートは producer が出した値を view 側で消さない

**決定:** producer が payload へ入れた key の値が schema に合わないとき、
**view (`_view_row`) 側で値を正規化・削除して schema へ合わせてはならない。**
schema の側を producer の実測値域へ合わせる。

**理由:**
- `layer3_report.py` の docstring が材料レポートを「campaign を読み取り専用で完全射影する」ものと
  定義している。producer が出した key を view で落とすと、この契約を正面から破る。
- 具体的には `settled` の `null` を「key 不在」へ正規化する案が出たが、それは
  「静定が不明」と「そもそも settled を記録しなかった」を区別不能にし、forensic 情報を失う。
- schema 側を広げるのが受理集合の緩和に当たるかは、**その field が関門かどうか**と
  **不在が既に許容されているか**で決まる。`settled` は `required` に無く不在が実測で 54 件あり、
  producer の comment どおり fails-closed の一次ゲートは別 (`competing_bench_pids`) である。
  したがって明示 `null` を受けるのは実質的な拡大ではなく、不在より情報の多い形を受け取るだけである。

**却下した選択肢:**
- view 側で正規化する — 上記のとおり完全射影の契約を破る。加えて生成器ファイルの編集を要し、
  その sha256 は生成 report に埋まるため凍結面へ波及する。

## {{D:producer-consumer-key-closure-derives-from-producer}}. producer と consumer の key 閉包は producer のコードから導出する

**決定:** 「producer が出しうる key の集合」を検査で固定するとき、
**手書きの定数を正本にしてはならない。** producer のコードから機械的に導出した集合と
照合する検査を置き、さらに実際に producer を呼んで emit された値の key 集合も検査する。

**理由:**
- 手書き定数だけを正本にすると、producer 側の代入を削除しても定数・positive control・
  schema 一致・runtime 検査・手作りの正例がすべて緑のまま通り、実 producer だけが
  その key を出さなくなる。本 wave の変異検査で実際にこの経路を確認した。
- 静的導出 (AST) だけでも足りない。guard 後の `update` / `setdefault` / alias 経由の再束縛・
  `for` / `while` / `try` / `with` の中の代入など、素通しする書き方が複数ある。
  静的導出には「許可外の mutator・alias・再束縛を拒否する」負例を対で置き、
  加えて実行時の emit を実測する。
- 件数だけの gate にしない。母集合が空でも緑になるため、期待母数と positive control を対にする。
