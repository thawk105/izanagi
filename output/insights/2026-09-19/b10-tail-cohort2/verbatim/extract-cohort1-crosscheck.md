## 4.1 権威 bytes
| t2500-backoff-static-tail-formal.json | `5f426ecbc16132048cf0c73eaf6960a395ec821a9f48cc04a83a787dceec8b28` |
| t2500-backoff-static-tail-formal.dat | `758b3121cebf7562315a8a70d1f305ced678f90b393fc3cd2a4af87ca0c71c44` |
| t2500-backoff-static-tail-formal-complete.json | `7192d1da0b4a032251a0e270ec60910a118a5f75844dc9276a6fba00a682d08c` |
complete.artifacts: {"t2500-backoff-static-tail-formal.dat": "758b3121cebf7562315a8a70d1f305ced678f90b393fc3cd2a4af87ca0c71c44", "t2500-backoff-static-tail-formal.json": "5f426ecbc16132048cf0c73eaf6960a395ec821a9f48cc04a83a787dceec8b28"}
complete.spec_sha256: 08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
complete.preregistrations: [{"preregistration_commit": "cad6f46d86ae4dc31edadfbdfad39c65ed73d70a", "preregistration_document_blob_sha256": "8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a", "spec_sha256": "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"}, {"preregistration_commit": "cad6f46d86ae4dc31edadfbdfad39c65ed73d70a", "preregistration_document_blob_sha256": "8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a", "spec_sha256": "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"}, {"preregistration_commit": "cad6f46d86ae4dc31edadfbdfad39c65ed73d70a", "preregistration_document_blob_sha256": "8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a", "spec_sha256": "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"}]
submit receipt: schema=b10-backoff-grid-submit-event/v1 job_script_sha256=c0635ef3c1fa7a589a2c08d079e9ade844e3d100367916f1460026df905b4e5c nonce=e3dd2884d0f0ff82d20ec825d3141ca6

## top
schema_version: "t2500-backoff-static-tail-formal-report/v1"
run_kind: "t2500-tail-formal"
verdict: "not-observed-in-any-workload"
failures: []
performance_certified: false
spec_sha256: "08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef"

## 1.1 / 1.3 campaigns
- write-heavy: campaign_id=t2500-backoff-static-tail-formal-silo-write-heavy-sweep-9cda88f0 job=0:998865.nqsv start_jst=2026-09-15 15:19:06 host=? sweep_elapsed_s=823.3052554130554 job_elapsed_s=836.440798997879 status=complete admission=admitted verification=not-evaluated-by-overlay
    prereg_commit=cad6f46d86ae4dc31edadfbdfad39c65ed73d70a blob=8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a spec=08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
    lock_sha256=1953e0fbe2b6448c4e2a7db2a8f18cf586d9813efa7b03fca3b2d279fde02d37 wal_sha256=ce3247c39b238b026fd83416f713a0ff1249467c492b9644e690530b90763cb5 lock_digest=1953e0fbe2b6448c4e2a7db2a8f18cf586d9813efa7b03fca3b2d279fde02d37
    ccbench_src=db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba pin=511c953 env=pegasus calib={'path': 'output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json', 'sha256': '753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49'} envc=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
    toolchain: cc=x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cxx=x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cmake=cmake version 3.22.1
    records=1000000 threads=48 extime_s=3 perf_reps=5 corr_reps=5 scale=t2500-backoff-static-tail-formal time_budget={'pbs_walltime_s': 18000, 'reduce_grid_or_reps_on_timeout': False, 'sweep_cap_s': 11700}
    order=[2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070] wc={'measurement_order_us': [2500, 3535, 1250, 1000, 1768, 9999, 5000, 7070], 'measurement_seed': 11599877, 'name': 'write-heavy', 'ycsb_max_ope': '10', 'ycsb_rmw': '0', 'ycsb_rratio': '5', 'ycsb_zipf_skew': '0.9'}
    correctness_mode=legacy flags={'extime': '1', 'thread_num': '4', 'ycsb_max_ope': '5', 'ycsb_rmw': 'true', 'ycsb_rratio': '50', 'ycsb_tuple_num': '200', 'ycsb_zipf_skew': '0.9'}
    freeze_trees_sha256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3 completion.status=complete pbs_jobid=0:998865.nqsv
    ccbench worktree: gitlink=511c9538e4e8efa54b45cda62e72389ed3b706ec head=511c9538e4e8efa54b45cda62e72389ed3b706ec clean=True
    perf_bin_sha256 distinct=8/8 use_perf={False} perf_claim={'perf_required': 'unsupported', 'throughput': 'eligible'} preflight_available=False
    correctness records=40 certified=40 anomalies_total=0 verdicts=['serializable'] src=['trace_enabled'] run_kind=['t2500-tail-formal']
    perf reps=40 src=['trace_disabled'] run_kind=['t2500-tail-formal']
- balanced: campaign_id=t2500-backoff-static-tail-formal-silo-balanced-sweep-1c8d08f7 job=0:998866.nqsv start_jst=2026-09-15 15:19:07 host=? sweep_elapsed_s=820.903146982193 job_elapsed_s=833.0822699069977 status=complete admission=admitted verification=not-evaluated-by-overlay
    prereg_commit=cad6f46d86ae4dc31edadfbdfad39c65ed73d70a blob=8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a spec=08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
    lock_sha256=9ed76b03987b26ac09b8033523b7c0eaec1754c1a2f12748571ef149ef9c9a18 wal_sha256=c472dfc8b4e1b27ed95b0458f235c86b61a076a775a0671ab7c6327e01c780e0 lock_digest=9ed76b03987b26ac09b8033523b7c0eaec1754c1a2f12748571ef149ef9c9a18
    ccbench_src=db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba pin=511c953 env=pegasus calib={'path': 'output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json', 'sha256': '753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49'} envc=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
    toolchain: cc=x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cxx=x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cmake=cmake version 3.22.1
    records=1000000 threads=48 extime_s=3 perf_reps=5 corr_reps=5 scale=t2500-backoff-static-tail-formal time_budget={'pbs_walltime_s': 18000, 'reduce_grid_or_reps_on_timeout': False, 'sweep_cap_s': 11700}
    order=[1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999] wc={'measurement_order_us': [1250, 5000, 1000, 7070, 3535, 1768, 2500, 9999], 'measurement_seed': 11599952, 'name': 'balanced', 'ycsb_max_ope': '10', 'ycsb_rmw': '0', 'ycsb_rratio': '50', 'ycsb_zipf_skew': '0.9'}
    correctness_mode=legacy flags={'extime': '1', 'thread_num': '4', 'ycsb_max_ope': '5', 'ycsb_rmw': 'true', 'ycsb_rratio': '50', 'ycsb_tuple_num': '200', 'ycsb_zipf_skew': '0.9'}
    freeze_trees_sha256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3 completion.status=complete pbs_jobid=0:998866.nqsv
    ccbench worktree: gitlink=511c9538e4e8efa54b45cda62e72389ed3b706ec head=511c9538e4e8efa54b45cda62e72389ed3b706ec clean=True
    perf_bin_sha256 distinct=8/8 use_perf={False} perf_claim={'perf_required': 'unsupported', 'throughput': 'eligible'} preflight_available=False
    correctness records=40 certified=40 anomalies_total=0 verdicts=['serializable'] src=['trace_enabled'] run_kind=['t2500-tail-formal']
    perf reps=40 src=['trace_disabled'] run_kind=['t2500-tail-formal']
- read-heavy: campaign_id=t2500-backoff-static-tail-formal-silo-read-heavy-sweep-9064a9e0 job=0:998867.nqsv start_jst=2026-09-15 15:19:07 host=? sweep_elapsed_s=825.3133578300476 job_elapsed_s=837.4671545028687 status=complete admission=admitted verification=not-evaluated-by-overlay
    prereg_commit=cad6f46d86ae4dc31edadfbdfad39c65ed73d70a blob=8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a spec=08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef
    lock_sha256=484f3acf20c39d6570a0501fc65af0b6886fff1d0925d2873484b209f698f4ed wal_sha256=5f9ebe362115ac1320d9531a226b6984845fcf84a872c3ea94af0d0a2ac4fde2 lock_digest=484f3acf20c39d6570a0501fc65af0b6886fff1d0925d2873484b209f698f4ed
    ccbench_src=db2b585b99811542981b0be70d432aee47b889bce23cfc4bce17d0430a9fc1ba pin=511c953 env=pegasus calib={'path': 'output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json', 'sha256': '753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49'} envc=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
    toolchain: cc=x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cxx=x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | cmake=cmake version 3.22.1
    records=1000000 threads=48 extime_s=3 perf_reps=5 corr_reps=5 scale=t2500-backoff-static-tail-formal time_budget={'pbs_walltime_s': 18000, 'reduce_grid_or_reps_on_timeout': False, 'sweep_cap_s': 11700}
    order=[3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000] wc={'measurement_order_us': [3535, 1250, 7070, 2500, 1768, 5000, 9999, 1000], 'measurement_seed': 11600021, 'name': 'read-heavy', 'ycsb_max_ope': '10', 'ycsb_rmw': '0', 'ycsb_rratio': '95', 'ycsb_zipf_skew': '0.9'}
    correctness_mode=legacy flags={'extime': '1', 'thread_num': '4', 'ycsb_max_ope': '5', 'ycsb_rmw': 'true', 'ycsb_rratio': '50', 'ycsb_tuple_num': '200', 'ycsb_zipf_skew': '0.9'}
    freeze_trees_sha256=c405c742f60e19b4f96b4fa9922f9bfe37ebd23389ed4598d707bfeb09abf2f3 completion.status=complete pbs_jobid=0:998867.nqsv
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
| 1250 → 1768 | `declining` | −0.5437 | −0.5601 | −0.5273 | 0.3062 | 0.3217 | 0.0113 |
| 1768 → 2500 | `declining` | −0.5518 | −0.5800 | −0.5237 | 0.3044 | 0.3310 | 0.0193 |
| 2500 → 3535 | `declining` | −0.5625 | −0.5904 | −0.5346 | 0.3097 | 0.3358 | 0.0191 |
| 3535 → 5000 | `declining` | −0.5771 | −0.6018 | −0.5525 | 0.3182 | 0.3411 | 0.0169 |
| 5000 → 7070 | `declining` | −0.5907 | −0.6151 | −0.5663 | 0.3247 | 0.3471 | 0.0168 |
| 7070 → 9999 | `declining` | −0.6137 | −0.6632 | −0.5642 | 0.3237 | 0.3685 | 0.0337 |
L range 0.3044..0.3247; U_flat range 0.0113..0.0337; qhat first/last -0.5437/-0.6137

**balanced**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.5355 | −0.5586 | −0.5123 | 0.2989 | 0.3210 | 0.0159 |
| 1768 → 2500 | `declining` | −0.5542 | −0.5859 | −0.5225 | 0.3038 | 0.3338 | 0.0217 |
| 2500 → 3535 | `declining` | −0.5896 | −0.6247 | −0.5545 | 0.3191 | 0.3514 | 0.0240 |
| 3535 → 5000 | `declining` | −0.6265 | −0.6593 | −0.5938 | 0.3374 | 0.3668 | 0.0225 |
| 5000 → 7070 | `declining` | −0.6602 | −0.6992 | −0.6212 | 0.3499 | 0.3841 | 0.0267 |
| 7070 → 9999 | `declining` | −0.7110 | −0.7543 | −0.6676 | 0.3704 | 0.4072 | 0.0296 |
L range 0.2989..0.3704; U_flat range 0.0159..0.0296; qhat first/last -0.5355/-0.7110

**read-heavy**

| 区間 (マイクロ秒) | 分類 | `qhat` | `qL` | `qU` | `L` | `U` | `U_flat` |
|---|---|---:|---:|---:|---:|---:|---:|
| 1250 → 1768 | `declining` | −0.4844 | −0.5073 | −0.4616 | 0.2738 | 0.2965 | 0.0157 |
| 1768 → 2500 | `declining` | −0.4964 | −0.5237 | −0.4690 | 0.2776 | 0.3044 | 0.0188 |
| 2500 → 3535 | `declining` | −0.5068 | −0.5372 | −0.4764 | 0.2812 | 0.3109 | 0.0208 |
| 3535 → 5000 | `declining` | −0.5208 | −0.5539 | −0.4877 | 0.2868 | 0.3188 | 0.0227 |
| 5000 → 7070 | `declining` | −0.5193 | −0.5499 | −0.4887 | 0.2873 | 0.3169 | 0.0210 |
| 7070 → 9999 | `declining` | −0.5518 | −0.6102 | −0.4934 | 0.2896 | 0.3449 | 0.0397 |
L range 0.2738..0.2896; U_flat range 0.0157..0.0397; qhat first/last -0.4844/-0.5518

## DAT header: ['workload', 'backoff_us', 'rep', 'aborts', 'commits', 'abort_rate', 'throughput_tps']; rows=120
abort_rate == aborts/(aborts+commits) mismatches: 0; cells=24; reps/cell=[5]
points.tps vs reps vs DAT mismatches: 0

## 2.3 throughput mean
| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 993,106.4 | 718,264.8 | 1,703,577.8 |
| 1250 | 905,601.2 | 659,017.0 | 1,545,212.0 |
| 1768 | 787,038.8 | 570,909.6 | 1,322,901.2 |
| 2500 | 684,422.6 | 496,833.6 | 1,133,420.6 |
| 3535 | 595,824.8 | 436,522.8 | 971,805.2 |
| 5000 | 520,175.6 | 387,841.6 | 834,521.0 |
| 7070 | 455,649.6 | 347,912.8 | 715,417.0 |
| 9999 | 401,697.6 | 317,246.2 | 618,689.8 |

## 2.3 abort rate mean
| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.042344 | 0.058753 | 0.023749 |
| 1250 | 0.037662 | 0.051936 | 0.021324 |
| 1768 | 0.031191 | 0.043137 | 0.018027 |
| 2500 | 0.025764 | 0.035602 | 0.015179 |
| 3535 | 0.021202 | 0.029024 | 0.012735 |
| 5000 | 0.017357 | 0.023357 | 0.010631 |
| 7070 | 0.014145 | 0.018582 | 0.008881 |
| 9999 | 0.011435 | 0.014523 | 0.007335 |

## 2.3 CV (throughput / abort rate)
| backoff (µs) | write-heavy | balanced | read-heavy |
|---:|---:|---:|---:|
| 1000 (境界参照) | 0.14% / 0.18% | 0.39% / 0.37% | 0.26% / 0.25% |
| 1250 | 0.22% / 0.21% | 0.24% / 0.23% | 0.27% / 0.30% |
| 1768 | 0.23% / 0.21% | 0.41% / 0.33% | 0.15% / 0.10% |
| 2500 | 0.39% / 0.40% | 0.43% / 0.45% | 0.26% / 0.35% |
| 3535 | 0.26% / 0.26% | 0.47% / 0.45% | 0.40% / 0.42% |
| 5000 | 0.34% / 0.35% | 0.37% / 0.37% | 0.44% / 0.43% |
| 7070 | 0.22% / 0.23% | 0.57% / 0.56% | 0.22% / 0.24% |
| 9999 | 0.65% / 0.66% | 0.53% / 0.56% | 0.78% / 0.76% |
CV ranges: throughput 0.14..0.78%, abort 0.10..0.76%
ratio 9999/1250 of mean throughput: write-heavy 0.444, balanced 0.481, read-heavy 0.400

## 2.5 raw samples
| workload | backoff (µs) | throughput (5 rep) | aborts / commits (5 rep) |
|---|---:|---|---|
| write-heavy | 1000 | 994,152, 991,352, 994,382, 991,750, 993,896 | 131,584 / 2,982,456, 131,774 / 2,974,058, 131,749 / 2,983,147, 131,788 / 2,975,252, 131,774 / 2,981,690 |
| write-heavy | 1250 | 904,835, 903,320, 906,101, 908,608, 905,142 | 106,326 / 2,714,505, 106,310 / 2,709,961, 106,344 / 2,718,305, 106,303 / 2,725,826, 106,332 / 2,715,428 |
| write-heavy | 1768 | 789,960, 786,123, 785,218, 786,888, 787,005 | 76,034 / 2,369,882, 75,941 / 2,358,369, 76,035 / 2,355,655, 76,037 / 2,360,666, 76,037 / 2,361,017 |
| write-heavy | 2500 | 683,586, 681,797, 687,747, 686,694, 682,289 | 54,307 / 2,050,758, 54,314 / 2,045,392, 54,285 / 2,063,242, 54,287 / 2,060,084, 54,297 / 2,046,868 |
| write-heavy | 3535 | 594,226, 594,141, 596,851, 596,491, 597,415 | 38,730 / 1,782,678, 38,716 / 1,782,424, 38,713 / 1,790,554, 38,717 / 1,789,473, 38,718 / 1,792,245 |
| write-heavy | 5000 | 522,442, 518,772, 518,772, 519,181, 521,711 | 27,560 / 1,567,326, 27,573 / 1,556,318, 27,574 / 1,556,316, 27,552 / 1,557,544, 27,561 / 1,565,134 |
| write-heavy | 7070 | 455,963, 454,165, 456,929, 455,710, 455,481 | 19,615 / 1,367,889, 19,621 / 1,362,495, 19,616 / 1,370,787, 19,612 / 1,367,132, 19,600 / 1,366,445 |
| write-heavy | 9999 | 400,579, 399,120, 400,830, 405,973, 401,986 | 13,944 / 1,201,739, 13,943 / 1,197,362, 13,930 / 1,202,490, 13,934 / 1,217,919, 13,942 / 1,205,958 |
| balanced | 1000 | 716,775, 715,615, 721,207, 721,331, 716,396 | 134,516 / 2,150,326, 134,477 / 2,146,846, 134,473 / 2,163,621, 134,515 / 2,163,993, 134,533 / 2,149,190 |
| balanced | 1250 | 658,543, 661,297, 659,441, 658,957, 656,847 | 108,292 / 1,975,629, 108,313 / 1,983,893, 108,314 / 1,978,324, 108,305 / 1,976,871, 108,304 / 1,970,542 |
| balanced | 1768 | 573,718, 570,174, 572,629, 567,723, 570,304 | 77,240 / 1,721,156, 77,238 / 1,710,524, 77,246 / 1,717,888, 77,083 / 1,703,170, 77,251 / 1,710,913 |
| balanced | 2500 | 496,768, 499,925, 495,151, 494,626, 497,698 | 55,035 / 1,490,304, 55,032 / 1,499,776, 55,053 / 1,485,453, 55,049 / 1,483,880, 54,942 / 1,493,095 |
| balanced | 3535 | 435,034, 435,725, 435,561, 440,089, 436,205 | 39,164 / 1,305,104, 39,162 / 1,307,176, 39,092 / 1,306,683, 39,146 / 1,320,269, 39,161 / 1,308,617 |
| balanced | 5000 | 385,968, 386,923, 389,232, 387,803, 389,282 | 27,832 / 1,157,905, 27,824 / 1,160,769, 27,826 / 1,167,696, 27,826 / 1,163,410, 27,823 / 1,167,846 |
| balanced | 7070 | 347,103, 346,136, 349,072, 346,421, 350,832 | 19,745 / 1,041,309, 19,762 / 1,038,408, 19,765 / 1,047,217, 19,771 / 1,039,264, 19,764 / 1,052,497 |
| balanced | 9999 | 315,867, 316,293, 319,358, 315,912, 318,801 | 14,027 / 947,601, 14,033 / 948,879, 14,016 / 958,074, 14,028 / 947,738, 14,025 / 956,403 |
| read-heavy | 1000 | 1,710,270, 1,704,454, 1,704,126, 1,698,979, 1,700,060 | 124,358 / 5,130,810, 124,330 / 5,113,363, 124,405 / 5,112,380, 124,416 / 5,096,939, 124,117 / 5,100,182 |
| read-heavy | 1250 | 1,541,237, 1,541,650, 1,549,685, 1,549,806, 1,543,682 | 100,998 / 4,623,711, 101,055 / 4,624,950, 100,956 / 4,649,056, 100,968 / 4,649,418, 101,034 / 4,631,047 |
| read-heavy | 1768 | 1,325,125, 1,320,334, 1,322,610, 1,321,873, 1,324,564 | 72,883 / 3,975,376, 72,738 / 3,961,004, 72,896 / 3,967,830, 72,879 / 3,965,620, 72,887 / 3,973,694 |
| read-heavy | 2500 | 1,137,537, 1,133,564, 1,130,120, 1,134,771, 1,131,111 | 52,298 / 3,412,611, 52,433 / 3,400,692, 52,423 / 3,390,361, 52,431 / 3,404,313, 52,448 / 3,393,334 |
| read-heavy | 3535 | 969,631, 970,537, 972,025, 968,471, 978,362 | 37,613 / 2,908,894, 37,616 / 2,911,611, 37,594 / 2,916,075, 37,611 / 2,905,413, 37,592 / 2,935,088 |
| read-heavy | 5000 | 838,325, 834,745, 830,215, 837,917, 831,403 | 26,896 / 2,514,976, 26,909 / 2,504,235, 26,884 / 2,490,646, 26,901 / 2,513,753, 26,913 / 2,494,211 |
| read-heavy | 7070 | 713,215, 715,761, 714,746, 717,584, 715,779 | 19,236 / 2,139,647, 19,225 / 2,147,283, 19,230 / 2,144,238, 19,229 / 2,152,752, 19,233 / 2,147,337 |
| read-heavy | 9999 | 620,573, 624,050, 615,853, 611,814, 621,159 | 13,715 / 1,861,720, 13,713 / 1,872,150, 13,721 / 1,847,561, 13,704 / 1,835,444, 13,714 / 1,863,479 |

## statistics gate
- write-heavy: gate_passed all=True max abort cv=0.006567 max tps cv=0.006469
- balanced: gate_passed all=True max abort cv=0.005600 max tps cv=0.005731
- read-heavy: gate_passed all=True max abort cv=0.007626 max tps cv=0.007823
