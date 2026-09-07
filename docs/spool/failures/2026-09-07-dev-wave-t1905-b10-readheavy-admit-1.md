---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t1905-b10-readheavy-admit
seq: 1
---

## 新規

### {{F:two-stage-predicate-mutation-masked-by-sibling}}. 二段述語の片側だけを変異させると、もう片側が負例を先に捕まえ、赤くなるのは行番号 pin の冗長 gate だけになる [テスト代表性] [手順漏れ]

- 事象: read-heavy 限定受理の変異事前登録 m08 は `execution_host` の**非空検査だけ**を削る形だった。
  probe で観測された赤 node は `test_ccbench_spawn_sites.py` の行番号 pin 3 件だけで、
  意図した semantic 負例 (`...semantic_gates_reject_mutated_digest_injected[execution-host-missing]`)
  は 1 件も発火しなかった。probe を「期待 node の収集」としか見ていなければ、この 3 node を
  期待値に焼いて本走で KILLED と記録し、**何も守っていない節を防壁として数えるところだった。**
- 根本原因: 述語が `type(row.get("execution_host")) is not str` と `not row.get("execution_host")` の
  二段で、負例が作る値が「キー欠落 (= `None`)」だったため、残した型検査が先に捕まえた。
  非空検査が単独で守る値域 (空文字列) を撃つ負例が存在しなかった。
  さらに、行数を変える変異はすべて行番号 pin を赤にするため、**冗長 gate の赤が
  「kill された」という見かけを作る**。この 2 つが重なると帰属不成立が緑の顔で通過する。
- 恒久対応: memory `mutation-probe-must-check-attribution-not-just-nodes` —
  probe 台帳を読むとき変異ごとに冗長 gate の node を引き、残りが空なら帰属不成立として
  `DW-M01` に従い実効 gate へ再照準する。本件は host 検査 2 行をまとめて削る形へ再照準し、
  単独 probe で semantic 負例の発火を実測してから本走へ登録した (15 / 15 KILLED、期待 node 完全一致)。
  初回 probe の台帳は `DW-M02` に従い
  `output/insights/2026-09-07_t1905-b10-readheavy-admit/mutation-ledger-probe.json` に残す。
- 再発検知: probe 台帳の `failed_nodes` から行番号 pin 3 node を引いた残りが空である変異。
  この差し引きは probe の読み取り手順そのものであり、走らせれば必ず目に入る。
