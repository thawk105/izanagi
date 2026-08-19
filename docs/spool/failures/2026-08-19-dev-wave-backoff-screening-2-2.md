---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-backoff-screening-2
seq: 2
---

## 再発

### F221

- **再発: 2026-08-19** — `backoff_sweep.py --screening` (D58 初回 ablation) の実際の Pegasus
  計算ノード実行 (bnode009/021/029、3件並列 qsub) で同型の `g++-13` fails-closed (D23) を直接
  踏んだ。今回は段2プランの手順漏れではなく、親が brief 前提測 (`DW-S01`) の一環として実測した
  結果として判明した。D293 (2026-08-11) の「compiler 差は backoff 級の差を容易に上回る」という
  理由により、system compiler への shim/route-around は採用せず、cygnus 到達手段または
  D293 と同型の site 依存 compiler 解決 + toolchain 束縛検査の実装を前提条件として記録した
  (worklog 参照)。
