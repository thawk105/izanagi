---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2803-provenance-receipt
seq: 3
---

## 再発

### F558

- **再発: 2026-09-20** — [T-2803] wave で、変更 test file の単独走 (計算ノード dispatch、`test_check_ai_provenance.py`) の走行中に親が wave worktree で fix commit を作り
  HEAD を動かした。実 repo の HEAD を読むテスト 23 件が `known provenance violation data HEAD changed while loading: start=4c532aa0b end=00d781372` で赤
  (非帰属)。固定 tip で単独走を取り直して 555 passed。損失は単独走 1 本 (約 1 分)。変異 harness ではなく dispatch した pytest 走でも同型で、
  「走行中は tree だけでなく HEAD も動かさない」を dispatch 全種に適用する必要がある。
