---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1434-adjudication-oracle
seq: 2
---

## {{D:oracle-ledger-vs-binding-separation}}. 独立 oracle 台帳の不在は、装置側の task 別 oracle 束縛の実装を止めない

**決定:** `tools/codex_reasoning_ab.py` の adjudication 層が task ごとの oracle 契約
(`known_finding_ids` と `oracle_kind`) を束縛する機構は、事前登録 §8 の独立 oracle ledger が
未作成であっても実装する。両者は別の対象である — ledger は人手で作る finding の**内容**、
束縛は装置の**機構**である。

ただし、この実装をもって §8 が閉じたとは記録しない。事前登録 §5.2 の到達度は `実装済み` ではなく
`部分実装` とし、閉じていない面 (ledger の作成・凍結、その固有 hash 契約、finding schema、
task 固有 acceptance、§8 の記述的 coverage の集計) を名指しする。

**あわせて、機構の存在と機構の発火を書き分ける。** 組込み `TASK_MANIFEST` は POS/NEG の双方へ
同じ `known_finding_ids` を入れるため、task 別集合と manifest 全体 union が同一集合になる。
したがってこの束縛は組込み manifest の入力では 1 度も union より狭い受理集合を作らない。
到達度に「機構は着地」と書くとき、それは存在の主張であって発火の主張ではない。

**理由:**
- §8 の逐語は ledger を実験開始前に作ることとその内容を要求するが、generic な consumer の実装前に
  ledger が存在しなければならないとは書いていない。段 3 の敵対レンズが §8 本文から独立に
  同じ結論へ達した。
- 同じ文書の §5.3 が既に「着地したのは現行 task manifest の中にある oracle 契約、すなわち
  `oracle_kind` と `known_finding_ids` とその consumer であって機構は着地」と記録しており、
  `_aggregate_verified` は同じ per-task 検査を実装済みだった。adjudication 層だけが union の
  ままである状態は、文書の中で整合していなかった。
- 束縛の実装は受理集合を**狭める**向きである。task 別集合は manifest 全体 union の部分集合であり、
  広げる経路を含まない。D931 が「交換できる対象には verdict の受理集合 (`known_finding_ids`) と
  positive/negative の分類が含まれる。これは正しさゲートの受理集合そのもの」と書いた向きと
  同じ側である。
- 発火の有無を書き分けないと、「機構は着地」という記録が「この実験の入力でその機構が働いている」と
  誤読される。実際には現行の組込み入力では 1 度も働かない。

**却下した選択肢:**
- ledger が揃うまで adjudication を union のまま残す — その間、外部 v3 manifest を使う経路は
  task A の finding ID を task B の verdict へ書いても受理し続ける。ledger の完成時期は
  §13 の lock 手続きが power simulation の段で停止しているため未定である。
- 到達度を `実装済み` と書く — 独立 ledger と acceptance が存在しないまま、certified report の
  参照元があるかのように読める。§5.2 の語彙規定は `部分実装` に「閉じていない面を必ず名指しする」
  ことを課しており、名指しできるので `部分実装` が正しい語である。
- 本 wave で §8 の ledger 本体を作る — 台帳の内容は task の acceptance criteria、再現可能な bug、
  固定された最終状態、独立 reviewer の確認から作るものであって、装置の実装で代替できない。
- 組込み `TASK_MANIFEST` の POS/NEG へ異なる `known_finding_ids` を入れて発火させる —
  manifest の canonical bytes を変えると `task_manifest_sha256` の連鎖が動く。凍結された
  T-181 の provenance 値を、機構を発火させたいという理由で書き換えてはならない。

## {{D:oracle-kind-hash-binding}}. oracle 分類は combined verdict の hash へ入れ、集計側の再照合は独立ゲートと呼ばない

**決定:** adjudication が返す combined verdict へ、schedule 由来の `oracle_kind` を
`combined_verdict_sha256` の計算**前**に入れる。あわせて `_aggregate_verified` が
verdict 側の `oracle_kind` を schedule 由来の値と exact 比較し、値の不一致と欠落の双方を拒否する。
ただし、この比較を「第 2 の独立ゲート」と呼ばない。**in-memory handoff の冗長 invariant** と記述する。

分類と集計の authority は引き続き schedule と manifest 由来の値であり、verdict 側の値を
authority にしない。

**理由:**
- hash より前に入れることで、記録済み judgment 行がその slot の oracle 分類へ束縛される。
  後から足すと `judgments[].combined_verdict_sha256` が oracle 分類を覆わない。
- live 経路では adjudication が schedule 由来の値を verdict へ入れ、集計側が同じ slots と
  同じ manifest から再導出する。**同一の authority の再計算**であって、独立した情報源の照合ではない。
  段 6 のレビューが実コードでこれを示した。保証の参照数を水増ししないため、記述を正した。
- それでも比較を残すのは、`_aggregate_verified` が内部 API として replay 以外の caller からも
  呼ばれうるためである。verdict を直接組み立てて渡す負例がこの層を実効 gate にする。
- 既存の凍結成果物を 1 つも壊さない。`output/` に `judgments` / `combined_verdict_sha256` を持つ
  生成済み material manifest は 1 件も存在しないことを実測した。

**却下した選択肢:**
- `oracle_kind` を hash の外に置く — 束縛が記録へ残らず、謳うだけで発火しない保証になる。
- 集計側の比較を省く — 内部 API 経路が無検査のまま残る。
- 集計側の比較を「独立照合」と記録する — 同じ authority の再計算を独立と数えることになり、
  実際の保証より強い主張になる。
