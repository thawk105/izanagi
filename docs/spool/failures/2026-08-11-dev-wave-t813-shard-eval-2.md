---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t813-shard-eval
seq: 2
---

## 再発

### F136

- **再発: 2026-08-11** — 受入全走が 1 本も無い場面で同型を踏んだ。[T-813] の評価 probe で、
  同じ worktree から 5 本の dispatch (全 file 1 job + 4 分割) を同時投入したところ、
  `test_s8b_floor_campaign.py` の `_real_output_snapshot()` 系が 8 件赤になった。
  差分の実体は**互いの** `output/pegasus-dispatch/<nonce>/result.json` である。
  control arm (単独走の baseline) 側でも同じ 8 件が出たため、**比較の基準まで汚染された**。
  既存の恒久対応は「受入全走の最中に投入しない」と書いてあり、受入を含まない probe 同士の
  同時投入を止めなかった。**規律の射程は「同じ作業木から dispatch を伴う走行を 2 本以上
  同時に投入しない」である** (受入の有無を条件にしない)。
  memory `no-concurrent-dispatch-during-acceptance` を同じ射程へ広げた。
  なお `dispatch_compute.dispatch()` には repo 外へ receipt を逃がす `output_root` seam があり、
  `run_tests._default_dispatch` が渡していないだけである — 並走が要る測定ではこの seam を使う。
