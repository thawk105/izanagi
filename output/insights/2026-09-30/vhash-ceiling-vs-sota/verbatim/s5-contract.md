# 段 5 の単位間契約 (親が固定、2026-09-30 22:4x JST)

単位 A (patch と条件 gate) と単位 B (driver・作図器・test) はこの契約だけを介して依存する。変更が要るなら実装せず報告して止まる。

## 1. macro と実行時 flag
- macro: `IZANAGI_CICADA_CEILING_WORKLOAD` (真偽 0/1、未定義・0 は pin と同じ前処理結果 = inert)。owner TU は `cc/cicada/ycsb_cicada.cc`、companion header は `include/ycsb.hh` (owner TU が include する範囲)。
- 長い読み手: 既存 flag `--batch_th_num` (0 か 1) と `--batch_max_ope=1000`。batch worker (thid ≥ `FLAGS_thread_num`) は新しい手続きごとに 1,000 個の READ だけの手続きを作り、read-only commit 経路 (`tx.is_ronly_ = true`) に乗る。retry では手続きを作り直さない。
- ro 指定率: 新 flag `--izanagi_ceiling_ronly_pct` (int、0〜100、既定 0)。通常 worker の新しい手続きごとに、この確率で全操作を READ にして read-only にする。read-only にならない手続きは少なくとも 1 操作を write にする。乱数は YCSB の既存系列を乱さない別系列。
- 0 のとき (macro=1 でも ronly_pct=0・batch_th_num=0 なら) 通常 worker の手続き生成は YCSB の既定と同じ分布。

## 2. 出力行 (計測窓の後、ちょうど 1 行)
`IZANAGI_CICADA_CEILING_WORKLOAD_V1 {"schema":1,"thread_num":<通常 worker 数>,"batch_threads":<batch_th_num>,"batch_ops":<batch_max_ope>,"ronly_pct":<int>,"normal_commits":<通常 worker の commit 合計>,"batch_commits":<batch worker の commit 合計>}`
- 値は既存の per-thread の commit 数 (`local_commit_counts_`) を runner の join の後に読むだけ。hot path に計数を足さない。
- CCBench 本来の throughput 出力は変えない。性能値の throughput は driver が `normal_commits / extime` で出す。

## 3. 木 (patch の適用順、各段 1 patch 1 回の `git apply`、fuzz なし)
| 木 | 適用順 | 用途 |
|---|---|---|
| base | pin → cicada-ro-gcflag-variant → cicada-ceiling-workload | S (RO_GCFLAG なし)・R (RO_GCFLAG=1) の perf |
| hot | pin → V → cicada-vhash-hot-block-variant → cicada-vhash-hot-block-post → W | R+hot K=1・K=8 の perf (CICADA_VHASH_K=1/8 + RO_GCFLAG=1) |
| fwd | pin → V → cicada-forwarding-variant → W | R+C-min の perf (CICADA_FWD_ENABLE=1 + RO_GCFLAG=1、実行時 --cicada_fwd_k=1、policy c) |
| igc | pin → V → cicada-interval-gc-variant → W | R+区間 GC の perf (CICADA_INTERVAL_GC=1 + RO_GCFLAG=1、実行時 --cicada_igc_debug_mode=1/3) |
| diag-base | pin → instr-cicada-version-lifetime → V → W | S・R の診断 (IZANAGI_CICADA_VLIFE=1 + 必要なら RO_GCFLAG_COUNT)。当たらなければ報告 |
| diag-hot | hot の木 + cicada-vhash-hot-block-count-v2 | hot の診断 (CICADA_VHASH_COUNT=1) |
| diag-fwd / diag-igc | fwd / igc の木 | CICADA_FWD_COUNT=1 / CICADA_INTERVAL_COUNT=1 |
| trace-* | pin → instr-cicada-trace → (上の各木の残り) | 正しさ (TRACE=1 + witness 用の計数 macro) |
| trace-igc-broken | trace-igc の木 + broken-cicada-interval-gc-overprune | 壊し正例 |
(V = cicada-ro-gcflag-variant、W = cicada-ceiling-workload。W はどの木でも最後。親が git apply で確認済み: pin→V→hot variant→post、pin→V→FWD、pin→V→IGC、pin→trace→V→(hot variant→post | FWD | IGC)。W を足した形は未確認。)

## 4. genome
全木 `B0 O1 P0 R1 W0` (`orchestrator/campaign/vhash_cicada_vlife.py` の TUNED_GENOME) を `verify_genome_commands` で束縛。
