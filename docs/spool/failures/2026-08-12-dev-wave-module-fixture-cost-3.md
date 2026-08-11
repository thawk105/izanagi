---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-module-fixture-cost
seq: 3
---

## 新規

### {{F:expected-nodes-stale-after-fix}}. 変異の期待 node を fix 前の構成で登録し 4 件 MISMATCH にした [手順漏れ]

- 事象: 変異 9 件のうち V1 / V2 / V3 / V9 が MISMATCH。いずれも
  **missing 0 / extra のみ** (登録 2 → 観測 14、2 → 6、2 → 18、1 → 2) で、
  検出力が予測を下回った変異は皆無だった。1 走 (10 run / 約 33 分) を再走に費やした。
- 根本原因: 期待 node を**段 5 時点のテスト構成**で導出したが、段 6 の敵対レビューが
  検出力の穴を 5 件指摘し、fix がテスト 5 本を追加した。追加分も同じ分岐を守るため、
  同じ変異がより広い node を落とすようになった。DW-M07 の「fix 後の最終 commit で期待 node を
  再検証してから本走する」を、anchor の一意性検査だけで済ませ、node 集合の再導出を怠った。
- 恒久対応: 変異 spec の生成を、fix 後の実観測 ledger から完全集合を再構成する形にした
  (`regen_spec_from_observed.py`)。再登録時に **missing が 1 件でもあれば停止**する
  (検出力が予測を下回る場合は自動再登録しない)。
- 再発検知: 初回走を probe と明記して erratum を残し、実観測で再登録した v2 spec で 9/9 KILLED を
  確認する手順を wave 手順に含める。parametrize を含む期待 node は特に、
  fix がテストを増やした後に必ず再導出する。
