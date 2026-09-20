---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2802-floor-attempt-recovery
seq: 3
---

## 再発

### F333

- **再発: 2026-09-20** — T-2802 の A/B 測定 (直接投入の受入 shard 走) で、03-A の shard-2 が計算ノード側の xdist
  INTERNALERROR で rc=16 になり、親 `run_tests.py` が shard-0/1 の dispatcher を SIGTERM した後、request 12235 / 12236 が
  scheduler に残って base worktree に hold が立った。qstat で終端を確認してから `output/pegasus-dispatch/orphan-holds/12235.nqsv.json`
  と `12236.nqsv.json` の 2 file だけを消し、root の `orphan-hold.json` (dispatcher が参照する単数形) を残したため、次の 04-A は
  3 shard とも `child_started=false / "reason":"orphan-hold"` で未投入のまま rc=16 になり、測定走 1 走分 (投入上限 12 走のうち 1) を失った。
  F333 の恒久対応 (`find output/pegasus-dispatch -maxdepth 2 -name "*hold*"` で全 path を列挙し、dispatcher log が名指しする path を読む)
  を撤去前に実行しておらず、記憶の hook (`runbook §7.6 の hold file は root の単数形`) も無かった。是正は root latch の削除 (写しを
  `output/insights/2026-09-20/t2802-floor-attempt-recovery/runs/03-A/orphan-hold-root.json` に保存) と裁定 erratum 5、
  memory `compute-node-discipline` への追記。
