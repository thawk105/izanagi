---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-floor-campaign-speed
seq: 2
---

## 再発

### F101

- **再発: 2026-08-12** — 受入全走が 2 failed / 9127 passed になり、赤が
  `test_t793_report.py` の 2 node だけだった。親は帰属 (main 由来) と再現性 (単独再走で
  同じ 2 node) までは実測したが、**F101 の恒久対応である「停止判断の前に local main の
  worklog を赤 node 名で検索し、成立している waiver / 既知赤の裁定が無いかを確認する」を
  実施せず**に `DW-STOP` で停止し、そのまま報告した。ユーザーの「既存の赤は免除リストに
  入れて」で是正し、検索を実施して**現時点で有効な既知赤 waiver は無い** (W1 は `[T-407]`
  の land で失効済み) ことを確認したうえで、ユーザー裁定により既知赤 waiver W2 を新設して
  land した。前回 (F101 本体) は「waiver が有るのに引かなかった」、今回は「waiver の
  有無を調べずに停止した」であり、**欠けた段は同一**である。
