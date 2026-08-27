# backoff profile — pegasus / balanced (skew0p9_rr50)

> BACKOFF_NOINLINE=1 diagnostic only; headline throughput に使用不可。

## provenance と限界

- site: `PEGASUS_COMPUTE`
- contract_sha256: `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
- calibration_ref: `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`
- calibration_sha256: `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`
- hostname: `bnode125`
- pbs_jobid: `None`
- ccbench_commit: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- gflags_pin: `e171aa2d15ed9eb17054558e0b3a6a413bb01067`
- glog_pin: `8f9ccfe770add9e4c64e9b25c102658e3c763b73`
- dependency_prefix: `/scr/tanab/izanagi-b10-balanced-profile-b10bal-20260827-06/dependency-prefix`
- build_cache_root: `/scr/tanab/izanagi-b10-balanced-profile-b10bal-20260827-06/ccbench-cache`
- dependency_build_log: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-balanced-profile/output/insights/2026-08-26_b10-balanced-profile/job-logs/b10bal-20260827-06`
- perf_executable: `/usr/lib/linux-tools-5.15.0-135/perf`
- clocks_per_us: `2100`
- comparison: `output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.json` sha256 `e99932213a571561c87f5ac253e19f59a81382718bb0cf08a9c64ea64281d184`
- comparison_confounds: `environment`, `ccbench_commit`
- backoff_time_live_verified: `false` — requested us は contract-calibrated であり実時間は未検証。
- dependency_prefix_cache_identity_bound: `false` — legacy buildcache.build は dependency prefix を cache identity へ束縛しない。job 専用 cache root で既存 cache の継承を避ける緩和に留まる。

## 事前登録した判定

- 評価帯 S: `backoff_us <= 10`。既存 write-heavy 成果物から固定し、この実測から選ばない。
- 散布: `(max - min) / mean`。replication bar は `0.044`。
- total_ipc の散布 (S) = **57.0%**
- useful_ipc の散布 (S) = **4.3%**
- 判定: 事前登録した判定2の条件を満たす。balanced の total IPC 低下は spin 希釈で説明できる。
- balanced の headline 利得そのものを説明したとは言わない。

## 有用 IPC と spin

- total_ipc の散布 (全域) = **124.9%**
- useful_ipc の散布 (全域) = **14.2%**

| backoff us | tps (median) | abort% | spin cyc% | spin instr% | total IPC | useful IPC | K_total | K_useful |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0(none) | 4,044,953 | 66.9 | 0.0 | 0.0 | 1.933 | 1.933 | 6,318,089 | 6,318,089 |
| 2 | 4,510,108 | 54.6 | 22.6 | 2.7 | 1.607 | 2.019 | 6,177,466 | 4,916,953 |
| 5 | 4,336,086 | 45.6 | 37.6 | 5.5 | 1.322 | 2.002 | 6,034,278 | 3,985,190 |
| 10 | 3,859,665 | 38.5 | 49.6 | 8.7 | 1.085 | 1.967 | 5,780,681 | 3,190,039 |
| 25 | 3,022,782 | 29.2 | 63.5 | 15.0 | 0.802 | 1.866 | 5,325,823 | 2,289,390 |
| 50 | 2,382,936 | 22.9 | 72.3 | 20.9 | 0.650 | 1.858 | 4,756,893 | 1,663,439 |
| 100 | 1,829,445 | 17.5 | 78.8 | 28.6 | 0.520 | 1.748 | 4,262,837 | 1,268,396 |

残るもの: 既存値との環境/source 交絡、同一 env/source の stock-inline 対照、実効 TSC の live 検証、dependency prefix の cache identity 束縛。

> BACKOFF_NOINLINE=1 diagnostic only; headline throughput に使用不可。
