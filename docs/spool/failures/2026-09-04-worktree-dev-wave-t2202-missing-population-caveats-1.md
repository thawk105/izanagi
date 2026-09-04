---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: worktree-dev-wave-t2202-missing-population-caveats
seq: 1
---

## 再発

### F333

- **再発: 2026-09-04** — [T-2202] の受入全走 attempt 1 (背景投入、`tools/dev_wave_wait.py acceptance`)
  が `stage=acceptance-command rc=70 source_rc=16 reason=dispatch-attestation-missing` で戻り、
  テストは 1 件も走らなかった。3 shard のうち 1 本が既定 900 秒の `queue-wait-timeout`、起動済みの
  2 本は launcher の `signal-abort` で、shard-1 の request `977101.nqsv` が
  `state-not-cancellable` のまま孤児として走り続けた (hold は
  `output/pegasus-dispatch/orphan-holds/977101.nqsv.json` と `output/pegasus-dispatch/orphan-hold.json`
  の 2 path)。既載の型どおり qdel せず終端を待ち、clean tree と HEAD を確認してから両 path を
  撤去し、D612 の上書き (queue-wait 3600 / grace 600) を付けて attempt 2 を投入した。
  **本件が足す事実: 前景 timeout ではなく、shard 間の queue 待ちのばらつきだけで同じ孤児が生まれる。**
  gen_S が混む時間帯の受入全走は、最初から D612 の上書きを付けて投入する方が 1 走分安い。
