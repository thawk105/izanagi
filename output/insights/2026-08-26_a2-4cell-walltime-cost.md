# A-2 4 cell の実コストと 6 時間 walltime の可否 (T-1683)

2026-08-26 実測。Pegasus 計算ノード、ccbench pin `511c953`、GCC 11、
`clocks_per_us=2100`、numactl 無し (pegasus の env contract 由来)。
一次資料は次の 2 つで、どちらも本 wave の実走で得た。

- `output/env/pegasus/calibration/a2_perf_verify_cost_t48_skew0p9_rr5_rmw0.json`
  (PBS request 947700、339 秒で完走)
- `output/env/pegasus/calibration/a2_perf_verify_cost_t48_skew0p9_rr50_rmw0.json`
  (PBS request 947734、529 秒で完走)

測った構成は A-2 policy の `performance_common` と各 workload に一致する。
`ycsb_tuple_num=1000000` / `thread_num=48` / `ycsb_zipf_skew=0.9` / `ycsb_rmw=0` /
`ycsb_max_ope=10` / `extime=3`。genome は 4 cell の定義そのもの。

## 実測値 (1 反復あたり)

| cell | trace bytes | trace 行数 | run 秒 | verifier 秒 | verifier ピーク RSS | abort 率 |
|---|---|---|---|---|---|---|
| rr5-stock | 903.1 MB | 28,715,742 | 3.34 | 161.55 | 12.02 GB | 0.8828 |
| rr5-fixed10 | 396.5 MB | 12,865,398 | 3.34 | 72.24 | 5.26 GB | 0.4770 |
| rr50-stock | 1536.2 MB | 49,850,198 | 3.35 | 332.32 | 20.29 GB | 0.7972 |
| rr50-fixed5 | 570.4 MB | 18,862,887 | 3.37 | 116.44 | 7.86 GB | 0.2549 |

trace file 数はいずれも 48 (thread 数と一致)。
4 cell とも verdict は `serializable`、`certified` は真、`total_cycles` は 0。

## 6 時間 walltime の可否

A-2 は cell ごとに、小構成の correctness 1 回に加えて **perf 完全同一構成の
trace-enabled correctness を 5 回**要求する
(`paper_story_a2_certification.py` の `VERIFY_MODE = "legacy+performance"`、
`_classify_verify` が `len(statuses) == expected_reps` を要求し、
`_classify_verify_repetition` は `trace_enabled` が真でない記録を不確定として弾く)。

1 反復あたりの 4 cell 合計 = 164.89 + 75.58 + 335.67 + 119.81 = **695.95 秒**。
5 反復では **3479.75 秒 = 約 58 分**。

これに乗るもの:

- trace 無しの性能測定 20 回 (1 回 3.3 秒台) = 約 70 秒
- ビルド一式。本 wave の実走では、gflags/glog の static build と ccbench 2 面の
  cold build を合わせて 2 cell あたり 73〜98 秒だった
- 小構成 (tuple200/thread4) の correctness 4 回。**本 wave では測っていない**

合計はおよそ 1 時間で、6 時間 (21600 秒) に対して 5 倍以上の余裕がある。
**4 cell は 6 時間に収まる。**

## 想定が外れていた点

- **最も重い cell は rr5 ではなく rr50-stock だった。** 起票時の見立ては
  「write-heavy の rr5 が律速」だったが、balanced のほうが commit が多く残るため
  trace 行数がそのまま増え、trace bytes・verifier 秒・ピーク RSS のいずれも
  4 cell 中の最大になる。abort は trace を増やすが、commit も同じくらい増やす。
- **余裕が薄いのは walltime ではなく RSS である。** rr50-stock のピーク 20.29 GB は
  既存の判定閾値 32 GB の 63% に達する。walltime の余裕 5 倍に対し、RSS は 1.6 倍しかない。
  記録数や extime を上げる変更は、walltime より先に RSS 側の天井に当たる。
- **backoff の有無が verifier 時間を 2〜3 倍動かす。** rr50 で 2.9 倍、rr5 で 2.2 倍。
  stock (backoff 無し) 側が常に重い。

## 既存の参照値が使えなかった理由

起票時の根拠だった 539MB / 16.9M 行 / verifier 141 秒は
`s2_verify_calibration.py` が産んだ値で、次の 2 点で A-2 へ転移しない。

- 同 driver は ccbench pin を `dff0f1e` に固定している。A-2 の現行 pin は `511c953`。
- env tag が `linux-baremetal` であり、A-2 が走る `pegasus` とは
  `clocks_per_us` (1800 対 2100) も numactl の有無 (前置する対 しない) も違う。

比で外挿していれば、最も重い cell を rr5 と誤認したまま判定していた。

## この計測の限界

- 各 cell 1 反復ずつしか測っていない。5 反復への換算は同一条件の反復回数を掛けただけで、
  反復間のばらつきは測っていない。
- 反復間の cooldown / settle を A-2 が挟むなら、その分は上記に含まれない。
- 小構成の correctness 4 回分は測っていない。
- 5 反復分の trace を保持したまま走らせる場合、1 cell あたり最大 7.7 GB
  (rr50-stock)、4 cell で 16.6 GB を要する。実走時の空きは 5464 GB だった。
