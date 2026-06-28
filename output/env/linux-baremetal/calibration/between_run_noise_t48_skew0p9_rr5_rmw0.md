# between-run noise floor — linux-baremetal / write-heavy (skew0p9_rr5_rmw0)

> A2 (orchestrator/campaign/between_run_floor)。計測は trace-disabled build (規律1)・単一テナント直列 (規律4)。既存 calibration JSON は不可侵で本ファイルは別出力。

- genome (baseline): `silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0`
- 動作点: records=1,000,000 / threads=48 / clocks_per_us=1800 / skew0p9_rr5_rmw0
- abort_rate: 82%

## noise floor (用途が違う 2 値を併記)

| 種別 | 構成 | CV | median tps | 用途 |
|---|---|---:|---:|---|
| within-run | 10 reps × 1 session | 2.19% | 1,867,627 | その 1 測定の品質 (remeasure 品質ゲート) |
| between-run | 8 sessions × 5 reps | 0.67% | 1,878,768 | 差が信用できるかの下限 (compare の丸め閾値) |

between-run は session-median の散らばり。settle は admission (独立性でない) ため cold-boot/温度ドリフト未含 = **下限**。wired する floor は cross-campaign の genuine な between データと突き合わせ保守側に採る (worklog 2026-06-28)。

**再現:**

```bash
numactl --interleave=all perf stat -e LLC-load-misses,LLC-loads,instructions,cycles -- /home/tanab/github/izanagi/external/ccbench/build-variants/silo_25d7d1bc89_t0/cc/silo/ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=1800 -ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0
```
