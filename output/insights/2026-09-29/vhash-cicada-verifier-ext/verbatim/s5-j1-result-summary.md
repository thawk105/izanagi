# J1 の結果 — job j1-a (35507.nqsv、bnode101、2026-09-29 16:15:38〜16:17:10 JST、dispatch rc=0)

原本: `runs/j1-a/result-J1-TPCC.json`、判定器 JSON は `runs/j1-a/raw/J1-TPCC/*.trace.verifier.json`、診断は同 dir の `*.stderr`。wave commit `984125afb` (計測木 cicvext-m-j1)、起動器 sha256 `12de8bd7…3d`。cell は裁定 R9 (R2 = 43 / 4 / 0 / 20、M = 43 / 0 / 0 / 0、warehouse 1、extime 1)、base = C1' + instr + tpcc 重ね patch (+ 壊し patch)、TRACE=1。

| run | 判定器 rc | verdict | 巡回 | orphan_reads | 他の integrity 数値項目・existence | C 行 = commit | READ_WTS_MISMATCH | 分類 (起動器) |
|---|---|---|---|---|---|---|---|---|
| stock R2 t4 | 3 | indeterminate | 0 | 0 | 全 0 | 30,766 = 30,766 | 0 | 対照 合格 |
| stock M t4 | 3 | indeterminate | 0 | 0 | 全 0 | 42,543 = 42,543 | 0 | 対照 合格 |
| β insert-past-ts R2 t4 | 1 | non-serializable | 1 | 1,144,962 | 全 0 | 28,562 = 28,562 | 0 | 期待した経路で検出 |
| α skip-read-recheck M t4 | 1 | non-serializable | 2,135 | 0 | 全 0 | 18,253 = 18,253 | 0 | 期待した経路で検出 |

## β (insert の版の時刻を壊した版)

- 発火診断: reached 140,384 / changed 140,137 / committed 130,612 (事象行 130,612)。
- 帰属 (裁定 R4): 起動器が raw trace から数え直した orphan (R の (表, key, 版) に一致する W が無い非 genesis の読み) = 1,144,962 件で、判定器の `orphan_reads` 1,144,962 と一致。その全件 (一致 1,144,962 / 不一致 0) が β の事象の (表, key, 公開した版 a_wts) と一致した。例: txid 41 が表 8 (OrderLine) の key `00010700000bba00` を版 (9237366, 365312255) で読み、これは事象 tx_wts=39674186567266562 の a_wts=39674185236494591 に一致。
- 巡回 1 件 (事前登録では期待していない観測値): G2、cycle [5, 397]。5 (tx_type 1 = NewOrder) → 397 (tx_type 5 = StockLevel) の wr 辺 (表 10 = Stock の 5 key)、397 → 5 の rw 辺 (表 8 = OrderLine の key `00010300000bba00`〜`…04`、u_ver = (9237302, 3800210177)、v_ver = (9237366, 833065218))。親が stderr で照合: `CICADA_BREAK_EVENT slug=insert-past-ts tx_wts=39674185704247554 table=8 key=00010300000bba00 a_wts=39673913793485569 …` があり、u_ver = a_wts (39673913793485569)、v_ver = tx_wts (39674185704247554)。StockLevel は NewOrder の Stock 更新を読んだ (後ろに直列化) のに、同じ NewOrder が insert した OrderLine を、β が付けた過去の版で読んだため、判定器には「insert より前の版を読んだ」rw 辺として現れた。巡回の辺も壊した insert に帰属する。

## α (既存 skip-read-recheck を TPC-C に重ねた版)

- 発火診断: reached 81,143 / changed 3,610 / committed 3,604。
- 帰属: 判定器の代表 witness 20 件 (`anomaly_count` 20、総巡回 2,135) のうち、起動器の規則 (事象の txn から事象の key 上の rw 辺、読んだ版 = a_wts) を満たす witness が 20 件 (`witness_count` 20。起動器は例を 3 件だけ出力)。例: cycle [18242, 18243] で 18243 → 18242 の rw 辺、表 0 (Warehouse) key `0000000000000001`、u_ver (9240627, 2254554369) = 事象 a_wts。
