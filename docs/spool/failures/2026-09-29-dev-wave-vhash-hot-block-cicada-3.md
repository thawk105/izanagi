---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-hot-block-cicada
seq: 3
---

## 再発

### F139

- **再発: 2026-09-29** — md_23 wave (VHash の hot block を Cicada に入れる) で、login の静的検査と前処理比較を通った patch が計算ノードの smoke1 (36580.nqsv、101 s) で条件 gate に拒否された。`CICADA_VHASH_COUNT` の分岐 20 site のうち 12 が `#if CICADA_VHASH_K` の内側にあり、gate の meaning の probe は K 未定義で owner TU を前処理するので 8 site しか観測できなかった。先例 (md_6 の `CICADA_FWD_COUNT` は companion `CICADA_FWD_ENABLE=1`) に答えがあり、段 4 の macro 設計で予見できた。companion `CICADA_VHASH_K=1` を固定して smoke2 で通った。実害は smoke 1 回分の時間だけ。恒久対応は F139 のまま (条件 gate に載せる macro は、他の macro の #if の内側に分岐を置くなら companion を設計の段で決める)。

### F273

- **再発: 2026-09-29** — md_23 wave で、親が同じ detached 計測木から本走 6 job (perf 3・count 1・trace 2) を detach script で同時に投げ、1 本目の pending orphan hold を検知して 5 本が rc 16 (`child_started=false`、`reason=orphan-hold`) になった (親の操作ミス)。1 本目 (36631.nqsv) は走り切り、残り 5 本は同じ木から 1 本ずつ流す chain で通した。qdel も hold の手動削除もしていない。`DW-C00` の「同一 worktree の dispatch は全種直列」の読み落としで、既存の恒久対応に直すべき新事実はない。並列にしたい計測は、計測木を job の数だけ作ってから投げる。
