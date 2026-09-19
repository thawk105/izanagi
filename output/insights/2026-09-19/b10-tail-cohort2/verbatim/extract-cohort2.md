## 4.1 権威 bytes
| t2500-backoff-static-tail-formal.json | `932f6cccbf1a4be2ccbd4c11af31fe2a402b26fc352eb05e22b87b14cef504fd` |
| t2500-backoff-static-tail-formal.dat | `15b99944b8429c0c2bb0d36d4498c7ab2a57d3f90c97d2430f34838905881fd6` |
| t2500-backoff-static-tail-formal-complete.json | `934211874c779c7bfbffd9a596ef9b7094b7bfa2f7a660203065759abf59420c` |
complete.artifacts: {"t2500-backoff-static-tail-formal.dat": "15b99944b8429c0c2bb0d36d4498c7ab2a57d3f90c97d2430f34838905881fd6", "t2500-backoff-static-tail-formal.json": "932f6cccbf1a4be2ccbd4c11af31fe2a402b26fc352eb05e22b87b14cef504fd"}
complete.spec_sha256: 08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
complete.preregistrations: [{"preregistration_commit": "8737cacb4bd286eb3e0784d16dba6eb85e5d6eab", "preregistration_document_blob_sha256": "8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e", "spec_sha256": "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"}, {"preregistration_commit": "8737cacb4bd286eb3e0784d16dba6eb85e5d6eab", "preregistration_document_blob_sha256": "8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e", "spec_sha256": "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"}, {"preregistration_commit": "8737cacb4bd286eb3e0784d16dba6eb85e5d6eab", "preregistration_document_blob_sha256": "8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e", "spec_sha256": "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"}]
submit receipt: schema=b10-backoff-grid-submit-event/v1 job_script_sha256=8422011d985ec1eef24fe94d0f5f3f50b12715a1dc008e10d3fec763d197783b nonce=bfcc6e5c66a9aefb1c67cf5985c8b5c2

## top
schema_version: "t2500-backoff-static-tail-formal-report/v1"
run_kind: "t2500-tail-formal"
verdict: "not-observed-in-any-workload"
failures: []
performance_certified: false
spec_sha256: "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"

## 1.1 / 1.3 campaigns
- write-heavy: campaign_id=t2500-backoff-static-tail-formal-silo-write-heavy-sweep-45feee64 job=0:10752.nqsv start_jst=2026-09-19 22:15:37 host=bnode084 sweep_elapsed_s=822.1359462738037 job_elapsed_s=834.6721301078796 status=complete admission=admitted verification=not-evaluated-by-overlay
    prereg_commit=8737cacb4bd286eb3e0784d16dba6eb85e5d6eab blob=8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e spec=08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
    lock_sha256=5503fb0181efe38022beeb08c85775076f3cd1c3d90b5135daf21d40e156cfa7 wal_sha256=d59b2c7f1ef7855b06dba9fc3d17ec236f6fe9923ce15871bb74fcc330f72927 lock_digest=5503fb0181efe38022beeb08c85775076f3cd1c3d90b5135daf21d40e156cfa7
    ccbench_src=db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba pin=511c953 env=pegasus calib={'path': 'output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json', 'sha256': '753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49'} envc=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
    toolchain: cc=x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cxx=x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cmake=cmake version 3.22.1
    records=1000000 threads=48 extime_s=3 perf_reps=5 corr_reps=5 scale=t2500-backoff-static-tail-formal time_budget={'pbs_walltime_s': 18000, 'reduce_grid_or_reps_on_timeout': False, 'sweep_cap_s': 11700}
    order=[2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070] wc={'measurement_order_us': [2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070], 'measurement_seed': 11599877, 'name': 'write-heavy', 'ycsb_max_ope': '10', 'ycsb_rmw': '0', 'ycsb_rratio': '5', 'ycsb_zipf_skew': '0.9'}
    correctness_mode=legacy flags={'extime': '1', 'thread_num': '4', 'ycsb_max_ope': '5', 'ycsb_rmw': 'true', 'ycsb_rratio': '50', 'ycsb_tuple_num': '200', 'ycsb_zipf_skew': '0.9'}
    freeze_trees_sha256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3 completion.status=complete pbs_jobid=0:10752.nqsv
    ccbench worktree: gitlink=511c9538e4e8efa54b45cda62e72389ed3b706ec head=511c9538e4e8efa54b45cda62e72389ed3b706ec clean=True
    perf_bin_sha256 distinct=8/8 use_perf={False} perf_claim={'perf_required': 'unsupported', 'throughput': 'eligible'} preflight_available=False
    correctness records=40 certified=40 anomalies_total=0 verdicts=['serializable'] src=['trace_enabled'] run_kind=['t2500-tail-formal']
    perf reps=40 src=['trace_disabled'] run_kind=['t2500-tail-formal']
- balanced: campaign_id=t2500-backoff-static-tail-formal-silo-balanced-sweep-d7cbfe58 job=0:10753.nqsv start_jst=2026-09-19 22:15:37 host=bnode107 sweep_elapsed_s=820.4259231090546 job_elapsed_s=831.9612014293671 status=complete admission=admitted verification=not-evaluated-by-overlay
    prereg_commit=8737cacb4bd286eb3e0784d16dba6eb85e5d6eab blob=8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e spec=08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
    lock_sha256=7c975f4715ccf20b73311e8aa8e199f87ddcd9271204735b02c466d108d83d71 wal_sha256=3986d1ad9116fe09aa8fe7ed1fd9443506e68122403c467d7ed4f4f680fad23c lock_digest=7c975f4715ccf20b73311e8aa8e199f87ddcd9271204735b02c466d108d83d71
    ccbench_src=db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba pin=511c953 env=pegasus calib={'path': 'output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json', 'sha256': '753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49'} envc=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
    toolchain: cc=x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cxx=x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cmake=cmake version 3.22.1
    records=1000000 threads=48 extime_s=3 perf_reps=5 corr_reps=5 scale=t2500-backoff-static-tail-formal time_budget={'pbs_walltime_s': 18000, 'reduce_grid_or_reps_on_timeout': False, 'sweep_cap_s': 11700}
    order=[1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999] wc={'measurement_order_us': [1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999], 'measurement_seed': 11599952, 'name': 'balanced', 'ycsb_max_ope': '10', 'ycsb_rmw': '0', 'ycsb_rratio': '50', 'ycsb_zipf_skew': '0.9'}
    correctness_mode=legacy flags={'extime': '1', 'thread_num': '4', 'ycsb_max_ope': '5', 'ycsb_rmw': 'true', 'ycsb_rratio': '50', 'ycsb_tuple_num': '200', 'ycsb_zipf_skew': '0.9'}
    freeze_trees_sha256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3 completion.status=complete pbs_jobid=0:10753.nqsv
    ccbench worktree: gitlink=511c9538e4e8efa54b45cda62e72389ed3b706ec head=511c9538e4e8efa54b45cda62e72389ed3b706ec clean=True
    perf_bin_sha256 distinct=8/8 use_perf={False} perf_claim={'perf_required': 'unsupported', 'throughput': 'eligible'} preflight_available=False
    correctness records=40 certified=40 anomalies_total=0 verdicts=['serializable'] src=['trace_enabled'] run_kind=['t2500-tail-formal']
    perf reps=40 src=['trace_disabled'] run_kind=['t2500-tail-formal']
- read-heavy: campaign_id=t2500-backoff-static-tail-formal-silo-read-heavy-sweep-ed0b204e job=0:10754.nqsv start_jst=2026-09-19 22:15:37 host=bnode108 sweep_elapsed_s=822.6369950771332 job_elapsed_s=834.673654794693 status=complete admission=admitted verification=not-evaluated-by-overlay
    prereg_commit=8737cacb4bd286eb3e0784d16dba6eb85e5d6eab blob=8511d47964977b89b549e0161c3aa6e0785a73bcbfa5ceab06715af833f86e9e spec=08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
    lock_sha256=4af8d0a2d6f1d6c395556f80fc685ee85cfb792b91126a33023aa1ab3a6fedc8 wal_sha256=942445f90c2c7970f7b72f83eb210697b6f14542381a09433ec2ffe66073e043 lock_digest=4af8d0a2d6f1d6c395556f80fc685ee85cfb792b91126a33023aa1ab3a6fedc8
    ccbench_src=db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba pin=511c953 env=pegasus calib={'path': 'output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json', 'sha256': '753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49'} envc=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
    toolchain: cc=x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cxx=x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cmake=cmake version 3.22.1
    records=1000000 threads=48 extime_s=3 perf_reps=5 corr_reps=5 scale=t2500-backoff-static-tail-formal time_budget={'pbs_walltime_s': 18000, 'reduce_grid_or_reps_on_timeout': False, 'sweep_cap_s': 11700}
    order=[3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000] wc={'measurement_order_us': [3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000], 'measurement_seed': 11600021, 'name': 'read-heavy', 'ycsb_max_ope': '10', 'ycsb_rmw': '0', 'ycsb_rratio': '95', 'ycsb_zipf_skew': '0.9'}
    correctness_mode=legacy flags={'extime': '1', 'thread_num': '4', 'ycsb_max_ope': '5', 'ycsb_rmw': 'true', 'ycsb_rratio': '50', 'ycsb_tuple_num': '200', 'ycsb_zipf_skew': '0.9'}
    freeze_trees_sha256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3 completion.status=complete pbs_jobid=0:10754.nqsv
    ccbench worktree: gitlink=511c9538e4e8efa54b45cda62e72389ed3b706ec head=511c9538e4e8efa54b45cda62e72389ed3b706ec clean=True
    perf_bin_sha256 distinct=8/8 use_perf={False} perf_claim={'perf_required': 'unsupported', 'throughput': 'eligible'} preflight_available=False
    correctness records=40 certified=40 anomalies_total=0 verdicts=['serializable'] src=['trace_enabled'] run_kind=['t2500-tail-formal']
    perf reps=40 src=['trace_disabled'] run_kind=['t2500-tail-formal']

## 2.1 workloads
- write-heavy: state=not-observed saturation_location=None local_flat=[] intervals=['declining', 'declining', 'declining', 'declining', 'declining', 'declining'] nonmono=[False, False, False, False, False, False] wiggle=[False, False, False, False, False, False]
- balanced: state=not-observed saturation_location=None local_flat=[] intervals=['declining', 'declining', 'declining', 'declining', 'declining', 'declining'] nonmono=[False, False, False, False, False, False] wiggle=[False, False, False, False, False, False]
- read-heavy: state=not-observed saturation_location=None local_flat=[] intervals=['declining', 'declining', 'declining', 'declining', 'declining', 'declining'] nonmono=[False, False, False, False, False, False] wiggle=[False, False, False, False, False, False]

## 2.2 interval tables

**write-heavy**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.5475 | −0.5618 | −0.5331 | 0.3090 | 0.3226 | 0.0099 |
| 1768 → 2500 | `declining` | −0.5445 | −0.5593 | −0.5297 | 0.3073 | 0.3214 | 0.0102 |
| 2500 → 3535 | `declining` | −0.5690 | −0.6027 | −0.5354 | 0.3100 | 0.3415 | 0.0230 |
| 3535 → 5000 | `declining` | −0.5735 | −0.6068 | −0.5402 | 0.3123 | 0.3434 | 0.0228 |
| 5000 → 7070 | `declining` | −0.5965 | −0.6230 | −0.5699 | 0.3264 | 0.3507 | 0.0182 |
| 7070 → 9999 | `declining` | −0.6194 | −0.6591 | −0.5797 | 0.3309 | 0.3667 | 0.0271 |
L range 0.3073..0.3309; U_flat range 0.0099..0.0271; qhat first/last -0.5475/-0.6194

**balanced**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.5380 | −0.5546 | −0.5214 | 0.3033 | 0.3192 | 0.0115 |
| 1768 → 2500 | `declining` | −0.5649 | −0.5828 | −0.5469 | 0.3155 | 0.3323 | 0.0124 |
| 2500 → 3535 | `declining` | −0.5885 | −0.6184 | −0.5586 | 0.3210 | 0.3486 | 0.0205 |
| 3535 → 5000 | `declining` | −0.6143 | −0.6450 | −0.5836 | 0.3327 | 0.3605 | 0.0211 |
| 5000 → 7070 | `declining` | −0.6766 | −0.7133 | −0.6399 | 0.3583 | 0.3901 | 0.0251 |
| 7070 → 9999 | `declining` | −0.7126 | −0.7512 | −0.6740 | 0.3732 | 0.4059 | 0.0264 |
L range 0.3033..0.3732; U_flat range 0.0115..0.0264; qhat first/last -0.5380/-0.7126

**read-heavy**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.4900 | −0.5051 | −0.4749 | 0.2805 | 0.2954 | 0.0104 |
| 1768 → 2500 | `declining` | −0.4956 | −0.5127 | −0.4784 | 0.2822 | 0.2991 | 0.0118 |
| 2500 → 3535 | `declining` | −0.5087 | −0.5394 | −0.4779 | 0.2820 | 0.3120 | 0.0211 |
| 3535 → 5000 | `declining` | −0.5074 | −0.5443 | −0.4704 | 0.2782 | 0.3143 | 0.0253 |
| 5000 → 7070 | `declining` | −0.5298 | −0.5725 | −0.4872 | 0.2866 | 0.3275 | 0.0291 |
| 7070 → 9999 | `declining` | −0.5340 | −0.5750 | −0.4930 | 0.2895 | 0.3287 | 0.0280 |
L range 0.2782..0.2895; U_flat range 0.0104..0.0291; qhat first/last -0.4900/-0.5340

## DAT header: ['workload', 'backoff_us', 'rep', 'aborts', 'commits', 'abort_rate', 'throughput_tps']; rows=120
abort_rate == aborts/(aborts+commits) mismatches: 0; cells=24; reps/cell=[5]
points.tps vs reps vs DAT mismatches: 0

## 2.3 throughput mean
| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 992,686.2 | 719,938.2 | 1,704,680.0 |
| 1250 | 905,498.2 | 657,520.8 | 1,544,381.8 |
| 1768 | 787,963.4 | 570,451.4 | 1,324,328.0 |
| 2500 | 683,409.0 | 498,175.2 | 1,134,612.0 |
| 3535 | 596,273.8 | 437,637.6 | 973,173.6 |
| 5000 | 519,930.4 | 386,980.0 | 832,181.8 |
| 7070 | 456,397.6 | 349,144.4 | 715,848.0 |
| 9999 | 403,188.2 | 318,499.4 | 615,347.8 |

## 2.3 abort rate mean
| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.042370 | 0.058623 | 0.023743 |
| 1250 | 0.037671 | 0.052048 | 0.021342 |
| 1768 | 0.031158 | 0.043191 | 0.018008 |
| 2500 | 0.025802 | 0.035514 | 0.015167 |
| 3535 | 0.021186 | 0.028965 | 0.012716 |
| 5000 | 0.017365 | 0.023408 | 0.010665 |
| 7070 | 0.014124 | 0.018517 | 0.008877 |
| 9999 | 0.011395 | 0.014464 | 0.007377 |

## 2.3 CV (throughput / abort rate)
| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.24% / 0.23% | 0.30% / 0.27% | 0.21% / 0.22% |
| 1250 | 0.18% / 0.19% | 0.14% / 0.15% | 0.16% / 0.18% |
| 1768 | 0.18% / 0.18% | 0.24% / 0.24% | 0.22% / 0.21% |
| 2500 | 0.20% / 0.20% | 0.23% / 0.22% | 0.23% / 0.23% |
| 3535 | 0.45% / 0.46% | 0.41% / 0.42% | 0.41% / 0.43% |
| 5000 | 0.37% / 0.38% | 0.35% / 0.36% | 0.48% / 0.51% |
| 7070 | 0.23% / 0.24% | 0.51% / 0.52% | 0.54% / 0.58% |
| 9999 | 0.56% / 0.55% | 0.47% / 0.46% | 0.31% / 0.31% |
CV ranges: throughput 0.14..0.56%, abort 0.15..0.58%
ratio 9999/1250 of mean throughput: write-heavy 0.445, balanced 0.484, read-heavy 0.398

## 2.5 raw samples
| workload | backoff (µs) | throughput (5 rep) | aborts / commits (5 rep) |
|---|---:|---|---|
| write-heavy | 1000 | 992,053, 995,149, 994,970, 989,654, 991,605 | 131,802 / 2,976,159, 131,728 / 2,985,448, 131,759 / 2,984,911, 131,733 / 2,968,964, 131,793 / 2,974,817 |
| write-heavy | 1250 | 904,186, 908,206, 905,133, 904,414, 905,552 | 106,339 / 2,712,559, 106,307 / 2,724,619, 106,359 / 2,715,399, 106,359 / 2,713,242, 106,336 / 2,716,657 |
| write-heavy | 1768 | 785,904, 789,006, 787,173, 789,207, 788,527 | 76,041 / 2,357,713, 76,025 / 2,367,019, 76,021 / 2,361,519, 76,022 / 2,367,621, 76,010 / 2,365,583 |
| write-heavy | 2500 | 685,684, 682,546, 683,314, 682,083, 683,418 | 54,304 / 2,057,053, 54,298 / 2,047,640, 54,295 / 2,049,942, 54,310 / 2,046,249, 54,295 / 2,050,254 |
| write-heavy | 3535 | 597,902, 599,285, 592,794, 594,322, 597,066 | 38,716 / 1,793,708, 38,705 / 1,797,855, 38,733 / 1,778,383, 38,721 / 1,782,968, 38,710 / 1,791,199 |
| write-heavy | 5000 | 517,177, 520,704, 522,468, 519,659, 519,644 | 27,571 / 1,551,531, 27,566 / 1,562,112, 27,558 / 1,567,405, 27,559 / 1,558,977, 27,568 / 1,558,932 |
| write-heavy | 7070 | 456,313, 454,878, 456,395, 457,848, 456,554 | 19,614 / 1,368,939, 19,618 / 1,364,635, 19,617 / 1,369,187, 19,611 / 1,373,546, 19,614 / 1,369,662 |
| write-heavy | 9999 | 401,342, 406,474, 401,396, 404,525, 402,204 | 13,939 / 1,204,028, 13,941 / 1,219,423, 13,943 / 1,204,189, 13,942 / 1,213,575, 13,941 / 1,206,612 |
| balanced | 1000 | 718,772, 721,322, 720,062, 722,488, 717,047 | 134,523 / 2,156,318, 134,504 / 2,163,968, 134,463 / 2,160,186, 134,521 / 2,167,465, 134,489 / 2,151,143 |
| balanced | 1250 | 655,992, 657,731, 658,013, 657,396, 658,472 | 108,324 / 1,967,977, 108,312 / 1,973,193, 108,271 / 1,974,040, 108,303 / 1,972,188, 108,312 / 1,975,417 |
| balanced | 1768 | 572,139, 571,401, 568,644, 570,331, 569,742 | 77,242 / 1,716,419, 77,240 / 1,714,205, 77,250 / 1,705,933, 77,268 / 1,710,994, 77,259 / 1,709,227 |
| balanced | 2500 | 497,369, 496,741, 499,106, 499,506, 498,154 | 55,026 / 1,492,108, 55,039 / 1,490,223, 55,036 / 1,497,320, 55,035 / 1,498,519, 55,021 / 1,494,462 |
| balanced | 3535 | 438,497, 436,097, 437,347, 440,297, 435,950 | 39,158 / 1,315,492, 39,173 / 1,308,291, 39,163 / 1,312,043, 39,149 / 1,320,893, 39,167 / 1,307,851 |
| balanced | 5000 | 387,990, 387,774, 388,166, 385,577, 385,393 | 27,830 / 1,163,971, 27,819 / 1,163,324, 27,824 / 1,164,498, 27,828 / 1,156,732, 27,832 / 1,156,180 |
| balanced | 7070 | 349,978, 349,901, 350,707, 346,151, 348,985 | 19,757 / 1,049,935, 19,760 / 1,049,703, 19,756 / 1,052,122, 19,766 / 1,038,453, 19,766 / 1,046,957 |
| balanced | 9999 | 316,201, 317,947, 319,573, 319,947, 318,829 | 14,022 / 948,603, 14,025 / 953,841, 14,023 / 958,719, 14,022 / 959,842, 14,025 / 956,489 |
| read-heavy | 1000 | 1,705,581, 1,709,860, 1,705,535, 1,701,971, 1,700,453 | 124,341 / 5,116,744, 124,378 / 5,129,582, 124,375 / 5,116,605, 124,363 / 5,105,915, 124,424 / 5,101,361 |
| read-heavy | 1250 | 1,545,127, 1,545,144, 1,544,732, 1,540,162, 1,546,744 | 100,993 / 4,635,383, 101,048 / 4,635,432, 101,074 / 4,634,198, 101,060 / 4,620,486, 101,016 / 4,640,232 |
| read-heavy | 1768 | 1,320,691, 1,327,113, 1,324,955, 1,326,895, 1,321,986 | 72,841 / 3,962,073, 72,875 / 3,981,341, 72,835 / 3,974,866, 72,858 / 3,980,687, 72,872 / 3,965,959 |
| read-heavy | 2500 | 1,137,265, 1,134,488, 1,136,860, 1,130,889, 1,133,558 | 52,418 / 3,411,796, 52,398 / 3,403,466, 52,430 / 3,410,580, 52,427 / 3,392,667, 52,429 / 3,400,675 |
| read-heavy | 3535 | 967,985, 978,019, 971,473, 976,385, 972,006 | 37,624 / 2,903,956, 37,594 / 2,934,059, 37,601 / 2,914,419, 37,599 / 2,929,157, 37,599 / 2,916,020 |
| read-heavy | 5000 | 830,154, 827,885, 838,195, 834,033, 830,642 | 26,919 / 2,490,464, 26,917 / 2,483,657, 26,900 / 2,514,585, 26,906 / 2,502,101, 26,920 / 2,491,928 |
| read-heavy | 7070 | 722,286, 716,371, 712,179, 714,427, 713,977 | 19,219 / 2,166,858, 19,231 / 2,149,115, 19,240 / 2,136,538, 19,240 / 2,143,281, 19,237 / 2,141,931 |
| read-heavy | 9999 | 617,053, 612,177, 616,298, 615,160, 616,051 | 13,717 / 1,851,159, 13,720 / 1,836,533, 13,720 / 1,848,896, 13,721 / 1,845,481, 13,717 / 1,848,154 |

## statistics gate
- write-heavy: gate_passed all=True max abort cv=0.005479 max tps cv=0.005570
- balanced: gate_passed all=True max abort cv=0.005228 max tps cv=0.005102
- read-heavy: gate_passed all=True max abort cv=0.005811 max tps cv=0.005442
