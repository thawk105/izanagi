# GC-PROBE の結果 — job gc-a (35506.nqsv、bnode046、2026-09-29 16:15:38〜16:16:28 JST、dispatch rc=0)

原本: `runs/gc-a/result-GC-PROBE.json`。wave commit `984125afb` (計測木 cicvext-m-l0)、起動器 sha256 `12de8bd7…3d`。裁定 R9 項 1 の事前登録どおり、F cell (`tpcc_perc_payment / order_status / delivery / stock_level` = 43 / 4 / 4 / 4、warehouse 1、extime 1) × thread 4 を build ごとに 5 回。

| build | 構成 | 5 回の結果 | stderr |
|---|---|---|---|
| STOCK_TPCC_TRACE0 | pin C 無 patch、TRACE=0 | 5 回とも benchmark rc=1 | 5 回とも `ERROR: Success` と `… cc/cicada/transaction.cc  853  gc_records` |
| STOCK_TPCC | C1' + instr + tpcc 重ね patch、TRACE=1 | 5 回とも benchmark rc=1 | 5 回とも同じ 2 行 (+ `CICADA_TRACE_INITIAL_WTS=`・`CICADA_TRACE_READ_WTS_MISMATCH n=0`) |

L0 (l0-a) の F t4 1 回を合わせると、F × thread 4 は 11 走行中 11 回が `gc_records()` の `ERR` で止まった。trace の有無 (TRACE=0 の pin C 無 patch でも起きる) に依らないので、stock Cicada (CCBench pin C) の delete 経路の欠陥であって観測者効果ではない (R9 項 1 の事前登録の書き方)。F × thread 1 (L0) は完走し合格した。

機序は親の静的な読みで、未実証: 同じ NewOrder 行を 2 本の Delivery が削除し合うと、wts の大きい側は commit 済みの削除版 D1 の上に自分の削除版 D2 を install (`validation()` の install は DELETE で最新版の wts だけを見る) した後、read set 再検査か (b) の deleted 検査で abort し、`writeSetClean()` が D2 を `aborted` にする。D2 は tuple の最新版に残り、D1 側の `gc_records()` が最新版の状態を deleted でないと見て `ERR` する。
