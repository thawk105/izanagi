## 読んだ資料

基準 root: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space`

読めた file は次の 75 件。

- `orchestrator/campaign/genome.py`
- `external/ccbench/cc/tictoc/`: `CMakeLists.txt`, `transaction.cc`, `util.cc`, `ycsb_tictoc.cc`, `tpcc_tictoc.cc`, `bomb_tictoc.cc`, `sbomb_tictoc.cc`
- `external/ccbench/cc/tictoc/include/`: `atomic_tool.hh`, `common.hh`, `result.hh`, `scan_callback.hh`, `tictoc_op_element.hh`, `transaction.hh`, `tuple.hh`, `util.hh`
- `external/ccbench/include/`: `atomic_wrapper.hh`, `backoff.hh`, `bomb.hh`, `bomb_pessimistic.hh`, `bomb_static.hh`, `cache_line_size.hh`, `check.hh`, `compiler.hh`, `config.hh`, `cpu.hh`, `dbomb_deterministic.hh`, `debug.hh`, `delay.hh`, `fence.hh`, `fileio.hh`, `heap_object.hh`, `inline.hh`, `int64byte.hh`, `lock.hh`, `masstree_wrapper.hh`, `op_element.hh`, `procedure.hh`, `queue.hh`, `random.hh`, `result.hh`, `rwlock.hh`, `sbomb_deterministic.hh`, `status.hh`, `string.hh`, `tpcc.hh`, `trace.hh`, `transaction_status.hh`, `tsc.hh`, `tuple_body.hh`, `tx_executor_concept.hh`, `util.hh`, `workload.hh`, `ycsb.hh`, `zipf.hh`
- `external/ccbench/include/tpcc/`: `tpcc_common.hh`, `tpcc_initializer.hh`, `tpcc_query.hh`, `tpcc_tables.hh`, `tpcc_tx_delivery.hh`, `tpcc_tx_neworder.hh`, `tpcc_tx_orderstatus.hh`, `tpcc_tx_payment.hh`, `tpcc_tx_stocklevel.hh`, `tpcc_util.hh`
- `external/ccbench/common/`: `result.cc`, `runner.hh`, `util.cc`
- `external/ccbench/cc/cicada/`: `CMakeLists.txt`, `ycsb_cicada.cc`, `tpcc_cicada.cc`, `bomb_cicada.cc`, `sbomb_cicada.cc`, `util.cc`, `transaction.cc`

読めなかった file: なし。

## 主張 1 の検証

走査した file は上記のうち次の 67 件。

- tictoc の `CMakeLists.txt`、protocol source 2 件、workload source 4 件
- tictoc 専用 header 8 件
- `external/ccbench/include/` 配下の全 header 49 件
- 共通実装 `common/result.cc`, `common/runner.hh`, `common/util.cc`

`PARTITION_TABLE` の出現箇所は [tictoc/CMakeLists.txt:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/tictoc/CMakeLists.txt:7) の定義供給 entry 1 件だけだった。

```cmake
PARTITION_TABLE=${CCBENCH_PARTITION_TABLE}
```

これを指定どおり除外すると、コンパイル対象コード内の live site は全件検索で 0 件。`#if`、`#ifdef`、式、印字を含め、tictoc 側には参照がない。したがって [genome.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py:159) の notes と一致する。

## 主張 2 の検証

[tictoc/CMakeLists.txt:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/tictoc/CMakeLists.txt:4) 以下の `OPTIONS` は全 6 entry。

- `NO_WAIT_LOCKING_IN_VALIDATION=${CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION}`
- `NO_WAIT_OF_TICTOC=${CCBENCH_NO_WAIT_OF_TICTOC}`
- `PARTITION_TABLE=${CCBENCH_PARTITION_TABLE}`
- `SLEEP_READ_PHASE=${CCBENCH_SLEEP_READ_PHASE}`
- `PREEMPTIVE_ABORTS=${CCBENCH_PREEMPTIVE_ABORTS}`
- `TIMESTAMP_HISTORY=${CCBENCH_TIMESTAMP_HISTORY}`

すべて `NAME=${VAR}` 形式。bare define は 0 件。

## 主張 3 の検証

[cicada/CMakeLists.txt:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/CMakeLists.txt:4) 以下の `OPTIONS` は全 9 entry。

- `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_CICADA}`
- `INLINE_VERSION_PROMOTION=${CCBENCH_INLINE_VERSION_PROMOTION}`
- `REUSE_VERSION=${CCBENCH_REUSE_VERSION}`
- `SINGLE_EXEC=${CCBENCH_SINGLE_EXEC}`
- `WRITE_LATEST_ONLY=${CCBENCH_WRITE_LATEST_ONLY}`
- `WORKER1_INSERT_DELAY_RPHASE=${CCBENCH_WORKER1_INSERT_DELAY_RPHASE}`
- `PARTITION_TABLE=${CCBENCH_PARTITION_TABLE}`
- `INSERT_READ_DELAY_MS=${CCBENCH_INSERT_READ_DELAY_MS}`
- `INSERT_BATCH_DELAY_MS=${CCBENCH_INSERT_BATCH_DELAY_MS}`

すべて `NAME=${VAR}` 形式。bare define は 0 件。

## 主張 4 の検証

workload source 4 件を末尾まで全件検索した結果:

- `ycsb_cicada.cc`: `SINGLE_EXEC` 0 件、`WRITE_LATEST_ONLY` 0 件
- `tpcc_cicada.cc`: 0 件、0 件
- `bomb_cicada.cc`: 0 件、0 件
- `sbomb_cicada.cc`: 0 件、0 件

合計はいずれも 0 件。workload source に別の live siteは隠れておらず、`transaction.cc` に基づく判定の前提を変える参照はない。

## 判定

- 主張 1: 一致
- 主張 2: 一致
- 主張 3: 一致
- 主張 4: 一致

## 総括

- 射影対象はすべて読み取り可能で、走査不能な file はなかった。
- tictoc の `PARTITION_TABLE` は CMake の定義供給以外に出現せず、live site は 0 件。
- tictoc と cicada の `OPTIONS` に bare define はない。
- cicada の workload source に `SINGLE_EXEC` または `WRITE_LATEST_ONLY` の参照はない。
- read-only の静的再レビューであり、テストやビルドは実行していない。