---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2622-compute-job-exit-hang
seq: 1
---

## supersede 追記

- F853 **supersede: 2026-09-16** — 計算ノードで 4 条件の分離実験を行った結果、根本原因欄の「孫が job の stdout / stderr を掴んだまま残るため」は機序として確定できない。子が出力 fd を即座に (または 30 秒後に) 手放しても、子が 75 秒生きる間 job の会計終了は遅れた (`E − J` = 69.731 / 69.586 / 69.870 秒、子孫なしの統制は -0.076 秒、request 558/559/560/568.nqsv、bnode013)。**fd の保持は遅延の必要条件ではない。** ただし当時の機序 (FIFO で block した孫) は再現していないので反証ではなく、NQSV が session / process group / 追跡集合のどれを見ているかも未特定である (全記録で `sid == pgid`)。**D1684 の是正は撤回しない** — 所属分離と子孫終了を同時に変えており各要素の寄与は未分離である。一次資料は `output/insights/2026-09-16/t2622-compute-job-exit-hang/`。
