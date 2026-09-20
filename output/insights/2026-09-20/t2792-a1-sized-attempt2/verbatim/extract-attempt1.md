## leaf files
| `README.md` | `880919db73901d44ed3f8e6508239267d1acc15c2be997603edbe2b7c6db2d88` | 3282 |
| `receipt.json` | `a2039dc1457cf34828714a98955faf3df68d335c0442d144122686f4e177e930` | 19343 |
| `result.json` | `372f199e674cce28d46e2aeeed90b0f5b6c06e894bca63bcb779b580a8bb75a0` | 269649 |
| `.complete.json` | `0b1f177944f6cab5c5eed5aa94a34beda11a06fcd8e94c1018d35c4e5e212a1e` | 1392 |
complete.files: {"README.md": "880919db73901d44ed3f8e6508239267d1acc15c2be997603edbe2b7c6db2d88", "receipt.json": "a2039dc1457cf34828714a98955faf3df68d335c0442d144122686f4e177e930", "result.json": "372f199e674cce28d46e2aeeed90b0f5b6c06e894bca63bcb779b580a8bb75a0"}
complete.schema: paper-story-a1-paired-materialization-complete/v1 publish: {"guarantees": ["A destination present at the fallback existence check is refused without publication.", "Cooperating A-1 publishers cannot hold the same exclusive sibling claim.", "Every materialized file and the completion marker exist in staging before publish.", "No file is written below destina

## top-level
- schema_version: "paper-story-a1-paired-result/v3"
- study_id: "paper-story-a1-20260901-balanced5-sized-v1"
- policy_sha256: "a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a"
- authority: "exploratory"
- formal: false
- promotion_prohibited: true
- complete: true
- all_workloads_terminal: true
- measurement_error: null
- workload_reps: {"balanced": 30, "read-heavy": 30, "write-heavy": 30}
- pairing_design: "balanced-a5b5-b5a5-v1"
- measurement_source_commit: d2ebef7a407dc6be61622ed596cf08b8b518f606
- evidence_level: source-routed-trace0 artifact_standalone_proof: False
- source files:
  - "orchestrator/calibrator/runner.py"
  - "orchestrator/campaign/paper_story_a1_paired.py"
  - "orchestrator/campaign/paper_story_a1_paired.v3-sized.json"
  - "orchestrator/campaign/paper_story_a1_source.py"
  - "orchestrator/campaign/paper_story_a1_source.v2.json"
  - "orchestrator/campaign/pipeline.py"
  - "output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md"
  - "patches/silo-backoff-fixed.patch"
  - "tools/pegasus/paper_story_a1_paired.sh"
- limitations:
  - The estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state direct effect.
  - Pilot observations are sizing inputs and are ineligible for the final estimate.
  - Source-routed trace0 evidence is not an artifact-standalone proof.
  - No cross-workload conclusion is produced.
  - EINVAL publish fallback is not atomic no-replace against a non-cooperating destination writer.

## §1.4 job table (receipt.job_executions)
| workload | request | host | scheduler start (JST) | job start (JST) | job end (JST) | elapsed s | CPU total s | requested_s | script sha |
| write-heavy | `4939.nqsv` | bnode107 | 06:30:45 | 06:30:45 | 06:39:59 | 553.96 | 9121.249 | 21600 | `3c2b734d9c71caca…` |
| balanced | `4940.nqsv` | bnode108 | 06:30:45 | 06:30:45 | 06:43:20 | 755.30 | 9121.098 | 21600 | `3c2b734d9c71caca…` |
| read-heavy | `4941.nqsv` | bnode109 | 06:31:13 | 06:31:13 | 06:36:37 | 323.80 | 9118.327 | 21600 | `3c2b734d9c71caca…` |
receipt keys: ['formal', 'job_executions', 'materialization', 'policy', 'promotion_prohibited', 'recorded_epoch', 'result', 'roots', 'route', 'scheduler_completion_receipt', 'schema_version', 'source_binding', 'study_id', 'submission_receipt']
receipt.submission_receipt: {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/receipts/submission.json", "sha256": "0a86dec922ff0a77bc2798cda466c646e2d29fdb4cf84c013a933ae271f3ddb4"}
receipt.scheduler_completion_receipt: {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/receipts/completion.json"}
receipt.recorded_epoch: 1789681458 2026-09-18 06:44:18
receipt.materialization: {"destination": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1505-a1-sized-submit/submit-tree/output/insights/2026-09-13/paper-story-a1-balanced5-sized", "job_terminal": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/raw/job-terminal.json", "sha256": "c46ae55cd9be5866956d5ffdefe5b86326de5899e8aa611725d6cf51631bbd15"}, "raw_receipt": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/raw/results/receipt.json", "sha256": "7de00bf5515d56a2e6fc791acaa0f505476db60ec7ecacab3dbc15d8ed6b32cb"}, "raw_result": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/raw/results/result.json", "sha256": "b080d755f5c6e3df1961d7355fffce923d23827547c9f711eaf7c2986450ace2"}, "scheduler_completion_receipt": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/receipts/completion.json", "sha256": "d26c4852150ba5e76f528790aa7e39e3ea155f6d2c43619dd561fcb55193d98f"}}
receipt.route: direct-qsub-workload-fanout policy: {"path": "orchestrator/campaign/paper_story_a1_paired.v3-sized.json", "sha256": "a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a"}

## §2.1 statistics (逐語)
| workload | contrast | n | mean | h | interval | B | baseline mean | sample sd | planned sigma | classification | breach |
| write-heavy | `fixed10` − `no-backoff` | 30 | `1591948.5` | `23911.502943472762` | `[1568036.9970565273, 1615860.0029434727]` | `68795.219` | `2293173.966666667` | `46253.31396347129` | `66403.45210801972` | `resolved-above-floor` | `false` |
| balanced | `fixed5` − `no-backoff` | 30 | `448830.1666666667` | `28351.599461068836` | `[420478.5672055979, 477181.7661277355]` | `115876.89600000001` | `3862563.2` | `54842.032905228465` | `56697.43571357468` | `resolved-above-floor` | `false` |
| read-heavy | `fixed2` − `no-backoff` | 30 | `-576749.7666666667` | `32963.69867738655` | `[-609713.4653440532, -543786.0679892802]` | `310204.40199999994` | `10340146.733333332` | `63763.46597396226` | `74668.48956627495` | `resolved-above-floor` | `false` |
- write-heavy: k=2.8315526875186725 df=29 floor_fraction=0.03 pairing_design=balanced-a5b5-b5a5-v1 contrast=variant-minus-baseline terminal_result={"classification": "resolved-above-floor", "status": "valid"} valid=True errors=[] campaign_id=paper-story-a1-write-heavy-paired-ec74e1c8
- balanced: k=2.8315526875186725 df=29 floor_fraction=0.03 pairing_design=balanced-a5b5-b5a5-v1 contrast=variant-minus-baseline terminal_result={"classification": "resolved-above-floor", "status": "valid"} valid=True errors=[] campaign_id=paper-story-a1-balanced-paired-fdd1cb88
- read-heavy: k=2.8315526875186725 df=29 floor_fraction=0.03 pairing_design=balanced-a5b5-b5a5-v1 contrast=variant-minus-baseline terminal_result={"classification": "resolved-above-floor", "status": "valid"} valid=True errors=[] campaign_id=paper-story-a1-read-heavy-paired-9912d892

## §2.1 検算 (30 対から再計算)
- write-heavy: diff一致=True raw一致=True n=30 mean=1591948.5 (記録 1591948.5) sd=46253.31396347129 (記録 46253.31396347129) h=23911.502943472762 (記録 23911.502943472762) B=68795.219 (記録 68795.219) bmean=2293173.966666667 分類=resolved-above-floor (記録 resolved-above-floor) sd/sigma=0.697 mean/bmean=+0.694 整数標本=True
- balanced: diff一致=True raw一致=True n=30 mean=448830.1666666667 (記録 448830.1666666667) sd=54842.03290522846 (記録 54842.032905228465) h=28351.599461068836 (記録 28351.599461068836) B=115876.89600000001 (記録 115876.89600000001) bmean=3862563.2 分類=resolved-above-floor (記録 resolved-above-floor) sd/sigma=0.967 mean/bmean=+0.116 整数標本=True
- read-heavy: diff一致=True raw一致=True n=30 mean=-576749.7666666667 (記録 -576749.7666666667) sd=63763.465973962266 (記録 63763.46597396226) h=32963.69867738656 (記録 32963.69867738655) B=310204.40199999994 (記録 310204.40199999994) bmean=10340146.733333332 分類=resolved-above-floor (記録 resolved-above-floor) sd/sigma=0.854 mean/bmean=-0.056 整数標本=True

## §2.2 pairs (3 列 × 10 行)
write-heavy (`fixed10_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3926656 | 2481442 | 1445214 | 10 | 3882434 | 2285777 | 1596657 | 20 | 3882354 | 2272458 | 1609896 |
| 1 | 3929996 | 2365221 | 1564775 | 11 | 3888281 | 2253680 | 1634601 | 21 | 3850724 | 2224397 | 1626327 |
| 2 | 3916390 | 2407240 | 1509150 | 12 | 3878410 | 2346151 | 1532259 | 22 | 3881145 | 2264264 | 1616881 |
| 3 | 3918147 | 2276044 | 1642103 | 13 | 3899804 | 2325755 | 1574049 | 23 | 3872280 | 2294309 | 1577971 |
| 4 | 3906234 | 2309222 | 1597012 | 14 | 3858848 | 2277190 | 1581658 | 24 | 3862447 | 2298790 | 1563657 |
| 5 | 3888481 | 2326735 | 1561746 | 15 | 3869692 | 2292397 | 1577295 | 25 | 3870225 | 2326580 | 1543645 |
| 6 | 3911088 | 2286334 | 1624754 | 16 | 3842760 | 2251860 | 1590900 | 26 | 3827850 | 2248395 | 1579455 |
| 7 | 3916988 | 2280104 | 1636884 | 17 | 3831594 | 2203616 | 1627978 | 27 | 3883667 | 2200172 | 1683495 |
| 8 | 3931043 | 2294703 | 1636340 | 18 | 3881225 | 2280571 | 1600654 | 28 | 3874270 | 2270283 | 1603987 |
| 9 | 3892826 | 2313058 | 1579768 | 19 | 3883187 | 2287548 | 1595639 | 29 | 3894628 | 2250923 | 1643705 |

balanced (`fixed5_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4334831 | 4063471 | 271360 | 10 | 4307511 | 3858116 | 449395 | 20 | 4300638 | 3850903 | 449735 |
| 1 | 4312415 | 3971107 | 341308 | 11 | 4319967 | 3883242 | 436725 | 21 | 4311693 | 3776752 | 534941 |
| 2 | 4346490 | 3867152 | 479338 | 12 | 4318241 | 3830979 | 487262 | 22 | 4311261 | 3848680 | 462581 |
| 3 | 4357394 | 3981753 | 375641 | 13 | 4266203 | 3860745 | 405458 | 23 | 4295880 | 3832275 | 463605 |
| 4 | 4322303 | 3858817 | 463486 | 14 | 4297481 | 3844141 | 453340 | 24 | 4285548 | 3795857 | 489691 |
| 5 | 4334030 | 3912345 | 421685 | 15 | 4316059 | 3869901 | 446158 | 25 | 4283546 | 3829388 | 454158 |
| 6 | 4334403 | 3873261 | 461142 | 16 | 4293161 | 3791349 | 501812 | 26 | 4299755 | 3800446 | 499309 |
| 7 | 4350699 | 3849766 | 500933 | 17 | 4288795 | 3933144 | 355651 | 27 | 4288170 | 3861696 | 426474 |
| 8 | 4335013 | 3878068 | 456945 | 18 | 4296386 | 3792192 | 504194 | 28 | 4307154 | 3829792 | 477362 |
| 9 | 4333271 | 3883709 | 449562 | 19 | 4299540 | 3852899 | 446641 | 29 | 4293963 | 3794950 | 499013 |

read-heavy (`fixed2_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 9850761 | 10605597 | -754836 | 10 | 9789429 | 10318105 | -528676 | 20 | 9761860 | 10264166 | -502306 |
| 1 | 9788490 | 10493554 | -705064 | 11 | 9769050 | 10329274 | -560224 | 21 | 9712352 | 10258699 | -546347 |
| 2 | 9779977 | 10472470 | -692493 | 12 | 9771090 | 10251908 | -480818 | 22 | 9737516 | 10336986 | -599470 |
| 3 | 9876628 | 10498728 | -622100 | 13 | 9764019 | 10355122 | -591103 | 23 | 9743014 | 10269106 | -526092 |
| 4 | 9756813 | 10315828 | -559015 | 14 | 9804220 | 10347940 | -543720 | 24 | 9695636 | 10308313 | -612677 |
| 5 | 9804611 | 10377673 | -573062 | 15 | 9827892 | 10359622 | -531730 | 25 | 9712880 | 10275959 | -563079 |
| 6 | 9800338 | 10309199 | -508861 | 16 | 9768523 | 10265695 | -497172 | 26 | 9730775 | 10345615 | -614840 |
| 7 | 9763660 | 10375610 | -611950 | 17 | 9690999 | 10350494 | -659495 | 27 | 9706841 | 10263100 | -556259 |
| 8 | 9731806 | 10326936 | -595130 | 18 | 9764561 | 10334679 | -570118 | 28 | 9732940 | 10269295 | -536355 |
| 9 | 9784457 | 10383227 | -598770 | 19 | 9760163 | 10283097 | -522934 | 29 | 9720608 | 10258405 | -537797 |

## §2.3 arms (派生 mean/min/max、WAL median/cv)
| workload | arm | mean tps (派生) | min / max tps (派生) | median tps (WAL) | cv (WAL) | unstable | rounds | attempts |
| write-heavy | fixed10 | 3,885,122.47 | 3,827,850 / 3,931,043 | 3882810.5 | 0.007025408387754655 | false | 1 | 1 |
| write-heavy | no-backoff | 2,293,173.97 | 2,200,172 / 2,481,442 | 2286055.5 | 0.024522075963025195 | false | 1 | 1 |
| balanced | fixed5 | 4,311,393.37 | 4,266,203 / 4,357,394 | 4309386.0 | 0.005103266632077728 | false | 1 | 1 |
| balanced | no-backoff | 3,862,563.20 | 3,776,752 / 4,063,471 | 3855507.5 | 0.015976453757935626 | false | 1 | 1 |
| read-heavy | fixed2 | 9,763,396.97 | 9,690,999 / 9,876,628 | 9763839.5 | 0.004486330231750992 | false | 1 | 1 |
| read-heavy | no-backoff | 10,340,146.73 | 10,251,908 / 10,605,597 | 10328105.0 | 0.008054510418980403 | false | 1 | 1 |
- write-heavy/fixed10: variant=a7f8486e1116 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- write-heavy/no-backoff: variant=84319b1127a6 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- balanced/fixed5: variant=93c62227a2d3 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- balanced/no-backoff: variant=84319b1127a6 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- read-heavy/fixed2: variant=82ea3a7b8618 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=2,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- read-heavy/no-backoff: variant=84319b1127a6 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0

## §2.4 verify_done
| workload | arm (variant id) | commits | aborts | anomalies | certified | verdict | check config |
| write-heavy | fixed10 (`a7f8486e1116`) | 459238 | 107049 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 459238}
| write-heavy | no-backoff (`84319b1127a6`) | 544423 | 209963 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 544423}
| balanced | fixed5 (`93c62227a2d3`) | 466561 | 130497 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 466561}
| balanced | no-backoff (`84319b1127a6`) | 483318 | 185235 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 483318}
| read-heavy | fixed2 (`82ea3a7b8618`) | 516607 | 181083 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 516607}
| read-heavy | no-backoff (`84319b1127a6`) | 515988 | 196776 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 515988}

## WAL (raw) ts / sha / size と bench_done.run_cmd / perf
- write-heavy: path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/jobs/write-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-write-heavy-paired-ec74e1c8/runs/wal.jsonl
  recorded sha=43b02eef2a1c16978f6351e591864f4a4d72601f42f76dfa71a6bb469051cd4f size=17933 env_tag=pegasus line_issues=[] truncated_tail=False records=10
  actual   sha=43b02eef2a1c16978f6351e591864f4a4d72601f42f76dfa71a6bb469051cd4f size=17933
  1789680702.9514682 build_start a7f8486e1116
  1789680720.8105001 build_done a7f8486e1116 trace_bin_sha256=992235d57f0b… perf_bin_sha256=2abb126826fe… perf_cached=False trace_cached=False
  1789680732.4211507 verify_done a7f8486e1116
  1789680735.448016 build_start 84319b1127a6
  1789680753.1679933 build_done 84319b1127a6 trace_bin_sha256=24d490f29ea3… perf_bin_sha256=be54eefadc7d… perf_cached=False trace_cached=False
  1789680767.218418 verify_done 84319b1127a6
  1789681198.239825 bench_done a7f8486e1116 bench_wall_s=100.66245822014753 use_perf=False counter_status=not_required
  run_cmd: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/jobs/write-heavy/cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/a46bf5b56529587749dae77a1fb9755daf532d018677b9c5064a54869ceda0cc/cc/silo/ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0 -ycsb_max_ope=10
  1789681198.2444258 bench_done 84319b1127a6 bench_wall_s=100.81620592728723 use_perf=False counter_status=not_required
  1789681198.2485318 commit a7f8486e1116
  1789681198.253626 commit 84319b1127a6
  campaign.lock recorded sha=3d3b094e5082147eb83a03ece85067b608beba07a52c965562dbb323f77c2bf6 size=5463 actual sha=3d3b094e5082147eb83a03ece85067b608beba07a52c965562dbb323f77c2bf6 size=5463
  schedule receipt recorded sha=137b0cc6d263d51db5196f3367f1d77b19e3ec66b6a3d590b8329c55d3cfa28d size=12942 path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/jobs/write-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-write-heavy-paired-ec74e1c8/balanced-schedule-receipt.json actual sha=137b0cc6d263d51db5196f3367f1d77b19e3ec66b6a3d590b8329c55d3cfa28d size=12942
- balanced: path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/jobs/balanced/raw/campaign-output/exploration/campaigns/paper-story-a1-balanced-paired-fdd1cb88/runs/wal.jsonl
  recorded sha=e2530dfec7ed43b30bda282cf1a2d41527f9c68363a90c4aed39fbfafa824511 size=17863 env_tag=pegasus line_issues=[] truncated_tail=False records=10
  actual   sha=e2530dfec7ed43b30bda282cf1a2d41527f9c68363a90c4aed39fbfafa824511 size=17863
  1789680703.004831 build_start 93c62227a2d3
  1789680720.7093995 build_done 93c62227a2d3 trace_bin_sha256=60535d9f3804… perf_bin_sha256=e56d406c4119… perf_cached=False trace_cached=False
  1789680732.5302727 verify_done 93c62227a2d3
  1789680735.3331158 build_start 84319b1127a6
  1789680752.9672358 build_done 84319b1127a6 trace_bin_sha256=f27311d4731b… perf_bin_sha256=35bca45c3e1a… perf_cached=False trace_cached=False
  1789680765.1427794 verify_done 84319b1127a6
  1789681399.3661873 bench_done 93c62227a2d3 bench_wall_s=100.3603473448893 use_perf=False counter_status=not_required
  1789681399.3712914 bench_done 84319b1127a6 bench_wall_s=100.57728348101955 use_perf=False counter_status=not_required
  1789681399.3750386 commit 93c62227a2d3
  1789681399.3804276 commit 84319b1127a6
  campaign.lock recorded sha=3fb0688713962867c6fcd5005b77e81317b61424bf91d718f7b552c5e10f9c1a size=5433 actual sha=3fb0688713962867c6fcd5005b77e81317b61424bf91d718f7b552c5e10f9c1a size=5433
  schedule receipt recorded sha=2ebe5c4f59a42817e4eb41ee3136d87c540b120c0739257d35d69dbb5b326a2b size=12895 path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/jobs/balanced/raw/campaign-output/exploration/campaigns/paper-story-a1-balanced-paired-fdd1cb88/balanced-schedule-receipt.json actual sha=2ebe5c4f59a42817e4eb41ee3136d87c540b120c0739257d35d69dbb5b326a2b size=12895
- read-heavy: path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/jobs/read-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-read-heavy-paired-9912d892/runs/wal.jsonl
  recorded sha=4001e27c10008eeb98a45ffa8295d209cc3595cd7c5f6e68ed93f6fde2dbb87c size=17940 env_tag=pegasus line_issues=[] truncated_tail=False records=10
  actual   sha=4001e27c10008eeb98a45ffa8295d209cc3595cd7c5f6e68ed93f6fde2dbb87c size=17940
  1789680729.3986197 build_start 82ea3a7b8618
  1789680747.506141 build_done 82ea3a7b8618 trace_bin_sha256=54f616c1902e… perf_bin_sha256=ad92da12cd8b… perf_cached=False trace_cached=False
  1789680760.598947 verify_done 82ea3a7b8618
  1789680763.7497816 build_start 84319b1127a6
  1789680781.8763578 build_done 84319b1127a6 trace_bin_sha256=5ac0eeff1a9e… perf_bin_sha256=b6e3d99dc010… perf_cached=False trace_cached=False
  1789680794.9999816 verify_done 84319b1127a6
  1789680996.618997 bench_done 82ea3a7b8618 bench_wall_s=100.66387323499657 use_perf=False counter_status=not_required
  1789680996.6242151 bench_done 84319b1127a6 bench_wall_s=100.6553309020237 use_perf=False counter_status=not_required
  1789680996.6282427 commit 82ea3a7b8618
  1789680996.6338978 commit 84319b1127a6
  campaign.lock recorded sha=32a213246ed2d8b542df43a82323aa890147caea4fd37deb187bd0515dcf6775 size=5447 actual sha=32a213246ed2d8b542df43a82323aa890147caea4fd37deb187bd0515dcf6775 size=5447
  schedule receipt recorded sha=9b2541ae294cd15afb73b40021b169a69f2a909dacf6cd2b480b58f3c0d2518a size=13005 path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/jobs/read-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-read-heavy-paired-9912d892/balanced-schedule-receipt.json actual sha=9b2541ae294cd15afb73b40021b169a69f2a909dacf6cd2b480b58f3c0d2518a size=13005

## attempt root receipts / raw
- raw/results/result.json: sha=b080d755f5c6e3df1961d7355fffce923d23827547c9f711eaf7c2986450ace2 size=263360 mtime=2026-09-18 06:44:18
- raw/results/receipt.json: sha=7de00bf5515d56a2e6fc791acaa0f505476db60ec7ecacab3dbc15d8ed6b32cb size=18112 mtime=2026-09-18 06:44:18
- raw/job-terminal.json: sha=c46ae55cd9be5866956d5ffdefe5b86326de5899e8aa611725d6cf51631bbd15 size=3010 mtime=2026-09-18 06:44:28
- receipts/submission.json: sha=0a86dec922ff0a77bc2798cda466c646e2d29fdb4cf84c013a933ae271f3ddb4 size=12949 mtime=2026-09-18 06:30:38
- receipts/completion.json: sha=d26c4852150ba5e76f528790aa7e39e3ea155f6d2c43619dd561fcb55193d98f size=5096 mtime=2026-09-18 06:44:28
- attempt-0001.intent.json: sha=0c3aadaea83f0fe1c7a31777d26bf992fbd46d64f6e1ed12a2de2cc6f67923d2 size=14100 mtime=2026-09-18 06:30:36
- barrier/ready/write-heavy.json: mtime=2026-09-18 06:32:47 sha=241e6f69cfa1cdcc…
- barrier/bench-start/write-heavy.json: mtime=2026-09-18 06:33:15 sha=7e79951059d4c1eb…
- jobs/write-heavy/job-terminal.json: mtime=2026-09-18 06:40:02 sha=1362eb5c7b5fc75c…
- barrier/ready/balanced.json: mtime=2026-09-18 06:32:45 sha=d43d98fc4c25ab9c…
- barrier/bench-start/balanced.json: mtime=2026-09-18 06:33:15 sha=7c933aedec381b85…
- jobs/balanced/job-terminal.json: mtime=2026-09-18 06:43:24 sha=9f0449ffdd16079d…
- barrier/ready/read-heavy.json: mtime=2026-09-18 06:33:15 sha=9a66feb9797b9b52…
- barrier/bench-start/read-heavy.json: mtime=2026-09-18 06:33:15 sha=ef51dc78eaa0084c…
- jobs/read-heavy/job-terminal.json: mtime=2026-09-18 06:36:41 sha=f499923359d95550…
- barrier/bench-go.json: mtime=2026-09-18 06:33:15
- job-terminal write-heavy: {"driver_rc": 0, "shell_rc": 0, "status": "finished", "request_id": null, "host": null}
- job-terminal balanced: {"driver_rc": 0, "shell_rc": 0, "status": "finished", "request_id": null, "host": null}
- job-terminal read-heavy: {"driver_rc": 0, "shell_rc": 0, "status": "finished", "request_id": null, "host": null}
- submission: schema paper-story-a1-paired-group-submission/v1 route direct-qsub-workload-fanout intent_sha256 7eb404861e9a5336c6169445885a7083c12f801ade5068e9b1ad09ad025a2750
  job: {"workload": "write-heavy", "request_id": "4939.nqsv", "qstat_visibility": null, "queue": null}
  job: {"workload": "balanced", "request_id": "4940.nqsv", "qstat_visibility": null, "queue": null}
  job: {"workload": "read-heavy", "request_id": "4941.nqsv", "qstat_visibility": null, "queue": null}
- completion: schema paper-story-a1-paired-group-completion/v1 keys ['attempt_root', 'group_terminal', 'jobs', 'schema_version', 'source_commit', 'study_id', 'submission_receipt']
   {"group_terminal": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001/raw/job-terminal.json", "sha256": "c46ae55cd9be5866956d5ffdefe5b86326de5899e8aa611725d6cf51631bbd15"}, "scheduler_terminal": null, "recorded_epoch": null}
