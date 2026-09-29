---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-cicada-verifier-ext
seq: 3
---

## 再発

### F139

- **再発: 2026-09-29** — md_17 wave (Cicada の TPC-C trace) で、Codex author が重ね patch の `tpcc_cicada.cc` の `#else` 側に `#line 31` を書いた (正しくは 30。`#line N` は次の行を N にするので、元の 31 行目の文の前は 30)。同じ repo の既存計装 (`patches/instr-cicada-trace.patch` の ycsb hunk、元の 30 行目の前に `#line 29`) に答えがあった。`ERR` → `NNN` の `__LINE__` が `fprintf` の即値になるので、TRACE=0 の命令列比較を赤にする形だった。親が計算ノードへ投げる前の静的レビューで見つけ、fix 1 回で直した (実害なし、直した後の比較は 12 TU で一致)。恒久対応は F139 のまま (実機の書式は先例の実装で確かめてから書く)。
