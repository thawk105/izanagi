---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-acceptance-runtime-opt
seq: 6
---

## 再発

### F3

- **再発: 2026-08-23** — 単独性を確認しないまま混雑下で取った per-test duration
  (`test_real_repo_priority_order_is_literal_and_writers_follow_barrier` = 87.46 秒) が、
  機構の構造的費用として扱われ、テストを既定 skip にする裁定の根拠になった。翌日に
  専有に近い計算ノードで測り直すと 27.65 秒で、除外の効果は均等配分モデルでも wall 0.576 秒
  しかなかった。外乱で膨らんだ 1 走の値は、測り直すまで設計の前提にしない。
  正本 = {{D:acceptance-wall-measured-on-dedicated-node}}。
