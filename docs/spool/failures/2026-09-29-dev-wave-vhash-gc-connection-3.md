---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-gc-connection
seq: 3
---

## 再発

### F273

- **再発: 2026-09-29** — VHash GC 接続の小モデル wave (dev-wave-vhash-gc-connection) で、親が fix3 の commit 後の full-history provenance 監査 (計算ノードへ自動 dispatch する) と、新 test file の所要計測の run_tests dispatch を同一 worktree からほぼ同時に投入し、監査の qsub 中の pending orphan hold (`phase: pending-qsub`) を所要計測が検知して rc=16 (`child_started=false`、`reason=orphan-hold`) になった (`DW-C00` の「同一 worktree の dispatch は全種直列」違反、親の操作ミス)。監査は request 34686.nqsv で走り切り rc=0、hold は監査の終端で自然に解除、所要計測は単独の再投入で 28 passed。qdel も hold の手動削除もしていない。既存恒久対応に修正すべき新事実はない。
