---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1909-probe-closure
seq: 3
---

## 新規

### {{F:symmetric-looking-negative-controls-missed-one}}. 同型に並んだ 3 本の負例のうち 1 本だけ拘束が欠けていた [テスト代表性] [恒真ゲート]

- 事象: 非標本 probe の遮断目録は 3 つの権威点からの逆到達閉包で導く。権威点ごとに
  「その権威点を種から外すと対象が目録から落ちる」負例が 1 本ずつ並んでいたが、
  第一権威点の 1 本だけが**権威点自身の在籍を検査せず**、下流の 1 関数だけを見ていた。
  第一権威点を目録から落とす変異は、この 3 本にも実 producer 直接呼出しの 9 本にも
  証拠 schema 検査にも掛からず生存する。3 本が同型に見えるため、目視では欠落が分からない。
  同じ file で、構成上必ず成立する一致を runtime import 閉包の被覆と称する検査名も見つかった
  ({{D:probe-generation-scope-matches-derivation}} と同じ wave の敵対レビューが検出)。
- 根本原因: 同型に並ぶ検査群を、名前と並びの対称性で「同じ拘束が掛かっている」と読んだ。
  中身の assert を 1 本ずつ照合していない。恒真な検査名の側も、名前が主張する内容と
  assert が実際に測る内容を照合していない。
- 恒久対応: 第一権威点の負例へ、権威点自身が baseline 目録に在ること・種を外すと落ちることの
  assert を足した (`orchestrator/tests/test_p3_b4_wiring_probe.py` の
  `test_anchor_seed_alone_load_bears_pipeline_evaluate`)。恒真な検査は名前と docstring を
  実際に検査している内容へ狭めた。
- 再発検知: 変異事前登録 MWA (`_build_inventory` で第一権威点だけを目録から落とす) を
  KILLED 期待で登録し、修正前 HEAD では SURVIVED になることを同じ wave で実測した。
