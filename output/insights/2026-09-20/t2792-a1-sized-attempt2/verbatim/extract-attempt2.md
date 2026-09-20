## leaf files
| `README.md` | `034cd1fd2f5004b1faac27d7e5e629a88c29f1e89dfd5fd1af9e6eadc50b53a1` | 3284 |
| `receipt.json` | `98c35cca4fe0e9f12559b8f9dc3acb4c6c5c4c597e5f5cc01a6449533918ecbf` | 19393 |
| `result.json` | `b7e0518e197500f2daf875e841acabf63f5eddb82bc14e072dd28e3431fe5f74` | 269786 |
| `.complete.json` | `7ad34232eaf920babd783140c47018b5c9d2f7665635872d4c2ee3be6f464fb3` | 1407 |
complete.files: {"README.md": "034cd1fd2f5004b1faac27d7e5e629a88c29f1e89dfd5fd1af9e6eadc50b53a1", "receipt.json": "98c35cca4fe0e9f12559b8f9dc3acb4c6c5c4c597e5f5cc01a6449533918ecbf", "result.json": "b7e0518e197500f2daf875e841acabf63f5eddb82bc14e072dd28e3431fe5f74"}
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
- measurement_source_commit: fec4a818741e5464fffcd11e4b094c125dfe5280
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
| write-heavy | `13220.nqsv` | bnode035 | 18:11:23 | 18:11:23 | 18:28:53 | 1050.02 | 9080.502 | 21600 | `3c2b734d9c71caca…` |
| balanced | `13221.nqsv` | bnode039 | 18:16:47 | 18:16:47 | 18:22:08 | 321.32 | 9081.926 | 21600 | `3c2b734d9c71caca…` |
| read-heavy | `13222.nqsv` | bnode040 | 18:11:23 | 18:11:23 | 18:25:31 | 847.45 | 9108.688 | 21600 | `3c2b734d9c71caca…` |
receipt keys: ['formal', 'job_executions', 'materialization', 'policy', 'promotion_prohibited', 'recorded_epoch', 'result', 'roots', 'route', 'scheduler_completion_receipt', 'schema_version', 'source_binding', 'study_id', 'submission_receipt']
receipt.submission_receipt: {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/receipts/submission.json", "sha256": "7fb0ebd66652d4d91cf399d2fa5b523b90615f0c493c4275f089ba1a8561aeb6"}
receipt.scheduler_completion_receipt: {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/receipts/completion.json"}
receipt.recorded_epoch: 1789896605 2026-09-20 18:30:05
receipt.materialization: {"destination": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/submit-tree/output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002", "job_terminal": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/raw/job-terminal.json", "sha256": "a9bc5f9a150533fd3900140bd2dea1b307c9706e2862158a3a98499a6af6cb38"}, "raw_receipt": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/raw/results/receipt.json", "sha256": "f06a2bc811b55ec720bb0224c673b1b086593cebb554d9d1b844b3834eedb355"}, "raw_result": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/raw/results/result.json", "sha256": "c9031faa9442974af344b54c6b700c58f5decb4d1447e4fb6bc16e6373bbee96"}, "scheduler_completion_receipt": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/receipts/completion.json", "sha256": "11202bf73f4ad15c84bf46047c0f990b0c5f5f9cb3631819bd301e7d38c648ea"}}
receipt.route: direct-qsub-workload-fanout policy: {"path": "orchestrator/campaign/paper_story_a1_paired.v3-sized.json", "sha256": "a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a"}

## §2.1 statistics (逐語)
| workload | contrast | n | mean | h | interval | B | baseline mean | sample sd | planned sigma | classification | breach |
| write-heavy | `fixed10` − `no-backoff` | 30 | `1538451.4666666666` | `41434.211082207854` | `[1497017.2555844588, 1579885.6777488743]` | `72952.12299999999` | `2431737.433333333` | `80148.43644687126` | `66403.45210801972` | `resolved-above-floor` | `true` |
| balanced | `fixed5` − `no-backoff` | 30 | `548138.2333333333` | `25552.384438113106` | `[522585.8488952202, 573690.6177714464]` | `110832.746` | `3694424.8666666667` | `49427.359824489315` | `56697.43571357468` | `resolved-above-floor` | `false` |
| read-heavy | `fixed2` − `no-backoff` | 30 | `-560565.6` | `41746.744315864176` | `[-602312.3443158641, -518818.8556841358]` | `305064.861` | `10168828.7` | `80752.98639149407` | `74668.48956627495` | `resolved-above-floor` | `true` |
- write-heavy: k=2.8315526875186725 df=29 floor_fraction=0.03 pairing_design=balanced-a5b5-b5a5-v1 contrast=variant-minus-baseline terminal_result={"classification": "resolved-above-floor", "status": "valid"} valid=True errors=[] campaign_id=paper-story-a1-write-heavy-paired-ec74e1c8
- balanced: k=2.8315526875186725 df=29 floor_fraction=0.03 pairing_design=balanced-a5b5-b5a5-v1 contrast=variant-minus-baseline terminal_result={"classification": "resolved-above-floor", "status": "valid"} valid=True errors=[] campaign_id=paper-story-a1-balanced-paired-fdd1cb88
- read-heavy: k=2.8315526875186725 df=29 floor_fraction=0.03 pairing_design=balanced-a5b5-b5a5-v1 contrast=variant-minus-baseline terminal_result={"classification": "resolved-above-floor", "status": "valid"} valid=True errors=[] campaign_id=paper-story-a1-read-heavy-paired-9912d892

## §2.1 検算 (30 対から再計算)
- write-heavy: diff一致=True raw一致=True n=30 mean=1538451.4666666666 (記録 1538451.4666666666) sd=80148.43644687126 (記録 80148.43644687126) h=41434.211082207854 (記録 41434.211082207854) B=72952.12299999999 (記録 72952.12299999999) bmean=2431737.433333333 分類=resolved-above-floor (記録 resolved-above-floor) sd/sigma=1.207 mean/bmean=+0.633 整数標本=True
- balanced: diff一致=True raw一致=True n=30 mean=548138.2333333333 (記録 548138.2333333333) sd=49427.359824489315 (記録 49427.359824489315) h=25552.384438113106 (記録 25552.384438113106) B=110832.746 (記録 110832.746) bmean=3694424.8666666667 分類=resolved-above-floor (記録 resolved-above-floor) sd/sigma=0.872 mean/bmean=+0.148 整数標本=True
- read-heavy: diff一致=True raw一致=True n=30 mean=-560565.6 (記録 -560565.6) sd=80752.98639149408 (記録 80752.98639149407) h=41746.744315864176 (記録 41746.744315864176) B=305064.861 (記録 305064.861) bmean=10168828.7 分類=resolved-above-floor (記録 resolved-above-floor) sd/sigma=1.081 mean/bmean=-0.055 整数標本=True

## §2.2 pairs (3 列 × 10 行)
write-heavy (`fixed10_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff | # | fixed10 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3995893 | 2730303 | 1265590 | 10 | 4003998 | 2419332 | 1584666 | 20 | 3911864 | 2460634 | 1451230 |
| 1 | 3974394 | 2522961 | 1451433 | 11 | 3940048 | 2473584 | 1466464 | 21 | 3960681 | 2390900 | 1569781 |
| 2 | 4006410 | 2487814 | 1518596 | 12 | 3971369 | 2367937 | 1603432 | 22 | 3949564 | 2326624 | 1622940 |
| 3 | 3994803 | 2506498 | 1488305 | 13 | 3963727 | 2351978 | 1611749 | 23 | 3976064 | 2366401 | 1609663 |
| 4 | 3973721 | 2463883 | 1509838 | 14 | 3972163 | 2371776 | 1600387 | 24 | 3963872 | 2388189 | 1575683 |
| 5 | 3977639 | 2465694 | 1511945 | 15 | 3968288 | 2371244 | 1597044 | 25 | 3907069 | 2472573 | 1434496 |
| 6 | 3956407 | 2513015 | 1443392 | 16 | 3988924 | 2338593 | 1650331 | 26 | 3969820 | 2385373 | 1584447 |
| 7 | 4011881 | 2348734 | 1663147 | 17 | 3987553 | 2434821 | 1552732 | 27 | 3977494 | 2462272 | 1515222 |
| 8 | 3968043 | 2389408 | 1578635 | 18 | 3963401 | 2407680 | 1555721 | 28 | 3982925 | 2457223 | 1525702 |
| 9 | 3971399 | 2448596 | 1522803 | 19 | 3951830 | 2420290 | 1531540 | 29 | 3964423 | 2407793 | 1556630 |

balanced (`fixed5_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff | # | fixed5 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4266248 | 3839305 | 426943 | 10 | 4267886 | 3692540 | 575346 | 20 | 4238081 | 3636991 | 601090 |
| 1 | 4299728 | 3809857 | 489871 | 11 | 4234281 | 3675444 | 558837 | 21 | 4261385 | 3695365 | 566020 |
| 2 | 4287973 | 3827709 | 460264 | 12 | 4216400 | 3681928 | 534472 | 22 | 4238034 | 3688031 | 550003 |
| 3 | 4220740 | 3794193 | 426547 | 13 | 4238945 | 3637186 | 601759 | 23 | 4219884 | 3662701 | 557183 |
| 4 | 4280154 | 3784769 | 495385 | 14 | 4233314 | 3636034 | 597280 | 24 | 4213926 | 3634864 | 579062 |
| 5 | 4262007 | 3704651 | 557356 | 15 | 4231465 | 3719180 | 512285 | 25 | 4201613 | 3660731 | 540882 |
| 6 | 4284367 | 3710110 | 574257 | 16 | 4215761 | 3629000 | 586761 | 26 | 4264831 | 3651730 | 613101 |
| 7 | 4196713 | 3654921 | 541792 | 17 | 4262605 | 3675613 | 586992 | 27 | 4216717 | 3665513 | 551204 |
| 8 | 4245262 | 3682865 | 562397 | 18 | 4251757 | 3655718 | 596039 | 28 | 4224122 | 3716884 | 507238 |
| 9 | 4225692 | 3702883 | 522809 | 19 | 4245020 | 3658778 | 586242 | 29 | 4231982 | 3647252 | 584730 |

read-heavy (`fixed2_tps`, `no-backoff_tps`, `signed_difference_tps`):

| # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff | # | fixed2 | no-backoff | diff |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 9643112 | 10591731 | -948619 | 10 | 9633739 | 10158988 | -525249 | 20 | 9584380 | 10150430 | -566050 |
| 1 | 9721704 | 10234922 | -513218 | 11 | 9623978 | 10147882 | -523904 | 21 | 9575531 | 10129168 | -553637 |
| 2 | 9676249 | 10286507 | -610258 | 12 | 9614795 | 10134634 | -519839 | 22 | 9594491 | 10099378 | -504887 |
| 3 | 9648460 | 10188137 | -539677 | 13 | 9614667 | 10146126 | -531459 | 23 | 9582219 | 10145912 | -563693 |
| 4 | 9618108 | 10206272 | -588164 | 14 | 9638830 | 10196588 | -557758 | 24 | 9502119 | 10116236 | -614117 |
| 5 | 9661991 | 10172584 | -510593 | 15 | 9579939 | 10143617 | -563678 | 25 | 9591746 | 10115792 | -524046 |
| 6 | 9668916 | 10159708 | -490792 | 16 | 9607334 | 10126829 | -519495 | 26 | 9559084 | 10106564 | -547480 |
| 7 | 9658097 | 10168649 | -510552 | 17 | 9598621 | 10152730 | -554109 | 27 | 9497031 | 10083958 | -586927 |
| 8 | 9594208 | 10164129 | -569921 | 18 | 9591807 | 10155298 | -563491 | 28 | 9588564 | 10085779 | -497215 |
| 9 | 9622207 | 10174751 | -552544 | 19 | 9548396 | 10166462 | -618066 | 29 | 9607570 | 10155100 | -547530 |

## §2.3 arms (派生 mean/min/max、WAL median/cv)
| workload | arm | mean tps (派生) | min / max tps (派生) | median tps (WAL) | cv (WAL) | unstable | rounds | attempts |
| write-heavy | fixed10 | 3,970,188.90 | 3,907,069 / 4,011,881 | 3971384.0 | 0.005909141675769404 | false | 1 | 1 |
| write-heavy | no-backoff | 2,431,737.43 | 2,326,624 / 2,730,303 | 2419811.0 | 0.0322747605417099 | false | 1 | 1 |
| balanced | fixed5 | 4,242,563.10 | 4,196,713 / 4,299,728 | 4238057.5 | 0.006212946185814447 | false | 1 | 1 |
| balanced | no-backoff | 3,694,424.87 | 3,629,000 / 3,839,305 | 3678770.5 | 0.01604910310303968 | false | 1 | 1 |
| read-heavy | fixed2 | 9,608,263.10 | 9,497,031 / 9,721,704 | 9607452.0 | 0.00495579129695054 | false | 1 | 1 |
| read-heavy | no-backoff | 10,168,828.70 | 10,083,958 / 10,591,731 | 10153915.0 | 0.008868175408282646 | false | 1 | 1 |
- write-heavy/fixed10: variant=a7f8486e1116 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- write-heavy/no-backoff: variant=84319b1127a6 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- balanced/fixed5: variant=93c62227a2d3 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- balanced/no-backoff: variant=84319b1127a6 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- read-heavy/fixed2: variant=82ea3a7b8618 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=2,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
- read-heavy/no-backoff: variant=84319b1127a6 expected_reps=30 observed_reps=30 unstable=False valid=True errors=[] rep_notes=[] high_variance(commit)=False verify_configs=['legacy'] correctness_evidence.certified=[True] verify_configs=['legacy'] frames=1 genome=silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0

## §2.4 verify_done
| workload | arm (variant id) | commits | aborts | anomalies | certified | verdict | check config |
| write-heavy | fixed10 (`a7f8486e1116`) | 458889 | 105711 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 458889}
| write-heavy | no-backoff (`84319b1127a6`) | 510621 | 197048 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 510621}
| balanced | fixed5 (`93c62227a2d3`) | 481088 | 133860 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 481088}
| balanced | no-backoff (`84319b1127a6`) | 509412 | 194033 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 509412}
| read-heavy | fixed2 (`82ea3a7b8618`) | 471051 | 166197 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 471051}
| read-heavy | no-backoff (`84319b1127a6`) | 523733 | 200282 | 0 | true | serializable | `legacy` | proof={"I": "evidence-absent", "P": "evidence-present", "X": "evidence-present", "protocol": "silo"} witness={"batch_commit_counts": 0, "commit_counts": 523733}

## WAL (raw) ts / sha / size と bench_done.run_cmd / perf
- write-heavy: path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/jobs/write-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-write-heavy-paired-ec74e1c8/runs/wal.jsonl
  recorded sha=173a0060ccc20ab1092790b193a6e0c805277ae72c1119d57de7590a79f7228e size=17942 env_tag=pegasus line_issues=[] truncated_tail=False records=10
  actual   sha=173a0060ccc20ab1092790b193a6e0c805277ae72c1119d57de7590a79f7228e size=17942
  1789895539.9079428 build_start a7f8486e1116
  1789895557.7757032 build_done a7f8486e1116 trace_bin_sha256=3442e8a0cf31… perf_bin_sha256=2643ffcd756a… perf_cached=False trace_cached=False
  1789895568.9282496 verify_done a7f8486e1116
  1789895572.078299 build_start 84319b1127a6
  1789895589.8847122 build_done 84319b1127a6 trace_bin_sha256=d857eb674aaa… perf_bin_sha256=8bc6f91d6ec1… perf_cached=False trace_cached=False
  1789895602.2004094 verify_done 84319b1127a6
  1789896532.0052657 bench_done a7f8486e1116 bench_wall_s=100.87483183294535 use_perf=False counter_status=not_required
  run_cmd: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/jobs/write-heavy/cache/contracts/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/1c16da39be13b3d1894564bac15a9c18c1f88314e4d7579a597afde14c8d4a10/cc/silo/ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=2100 -ycsb_zipf_skew=0.9 -ycsb_rratio=5 -ycsb_rmw=0 -ycsb_max_ope=10
  1789896532.0101228 bench_done 84319b1127a6 bench_wall_s=101.06330358411651 use_perf=False counter_status=not_required
  1789896532.0152395 commit a7f8486e1116
  1789896532.0207036 commit 84319b1127a6
  campaign.lock recorded sha=0ec558982139d68cbfb03372ee1d854b6236ff497d2d05f36cef8f28d19f6716 size=5463 actual sha=0ec558982139d68cbfb03372ee1d854b6236ff497d2d05f36cef8f28d19f6716 size=5463
  schedule receipt recorded sha=cbd853fc34da4383f5d9c7ee0890e3f104ed405224a2971a6528b343f0a6b606 size=12943 path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/jobs/write-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-write-heavy-paired-ec74e1c8/balanced-schedule-receipt.json actual sha=cbd853fc34da4383f5d9c7ee0890e3f104ed405224a2971a6528b343f0a6b606 size=12943
- balanced: path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/jobs/balanced/raw/campaign-output/exploration/campaigns/paper-story-a1-balanced-paired-fdd1cb88/runs/wal.jsonl
  recorded sha=8cc4bc23c5c64ea8a992a5d95c734c5863e7335b1a1c0d20c134339968e89065 size=17871 env_tag=pegasus line_issues=[] truncated_tail=False records=10
  actual   sha=8cc4bc23c5c64ea8a992a5d95c734c5863e7335b1a1c0d20c134339968e89065 size=17871
  1789895862.4185896 build_start 93c62227a2d3
  1789895880.3790505 build_done 93c62227a2d3 trace_bin_sha256=478d443749ca… perf_bin_sha256=69678432745d… perf_cached=False trace_cached=False
  1789895891.9397807 verify_done 93c62227a2d3
  1789895895.011204 build_start 84319b1127a6
  1789895912.532299 build_done 84319b1127a6 trace_bin_sha256=9f7fcfed750c… perf_bin_sha256=7facbe104e4d… perf_cached=False trace_cached=False
  1789895924.828919 verify_done 84319b1127a6
  1789896127.5533025 bench_done 93c62227a2d3 bench_wall_s=101.20577729295474 use_perf=False counter_status=not_required
  1789896127.5585594 bench_done 84319b1127a6 bench_wall_s=101.23983995203162 use_perf=False counter_status=not_required
  1789896127.5625174 commit 93c62227a2d3
  1789896127.5676017 commit 84319b1127a6
  campaign.lock recorded sha=e68c85ce44e628b4a6645b1b413cdb5968a399bfc6e4c8e488c036d1c9ed74b6 size=5433 actual sha=e68c85ce44e628b4a6645b1b413cdb5968a399bfc6e4c8e488c036d1c9ed74b6 size=5433
  schedule receipt recorded sha=bc65d939927d43691a0c915183fcb14cff8fe6948757676b1acbf50e1ee96052 size=12907 path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/jobs/balanced/raw/campaign-output/exploration/campaigns/paper-story-a1-balanced-paired-fdd1cb88/balanced-schedule-receipt.json actual sha=bc65d939927d43691a0c915183fcb14cff8fe6948757676b1acbf50e1ee96052 size=12907
- read-heavy: path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/jobs/read-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-read-heavy-paired-9912d892/runs/wal.jsonl
  recorded sha=eb1f3234ae5ea61326e310b6cfc4b3e292f89f25d6a9bdfebcb4ac83085aed7b size=17953 env_tag=pegasus line_issues=[] truncated_tail=False records=10
  actual   sha=eb1f3234ae5ea61326e310b6cfc4b3e292f89f25d6a9bdfebcb4ac83085aed7b size=17953
  1789895539.9556124 build_start 82ea3a7b8618
  1789895557.8882923 build_done 82ea3a7b8618 trace_bin_sha256=531df817c3ea… perf_bin_sha256=8c343ee4e616… perf_cached=False trace_cached=False
  1789895569.3627627 verify_done 82ea3a7b8618
  1789895572.5048866 build_start 84319b1127a6
  1789895590.3339105 build_done 84319b1127a6 trace_bin_sha256=87a4cb0660e7… perf_bin_sha256=9480e962c58f… perf_cached=False trace_cached=False
  1789895602.9228923 verify_done 84319b1127a6
  1789896329.8783987 bench_done 82ea3a7b8618 bench_wall_s=101.02933081798255 use_perf=False counter_status=not_required
  1789896329.883348 bench_done 84319b1127a6 bench_wall_s=101.12654735601973 use_perf=False counter_status=not_required
  1789896329.897055 commit 82ea3a7b8618
  1789896329.9029677 commit 84319b1127a6
  campaign.lock recorded sha=b814513dbc274090abc57329864d3a1b197331b5542ade373c8753068319333d size=5447 actual sha=b814513dbc274090abc57329864d3a1b197331b5542ade373c8753068319333d size=5447
  schedule receipt recorded sha=a2d5d037648beb1b34d438a0ce7ff9f8ebe15493000d50902e98bb9fbaba8632 size=13004 path=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/jobs/read-heavy/raw/campaign-output/exploration/campaigns/paper-story-a1-read-heavy-paired-9912d892/balanced-schedule-receipt.json actual sha=a2d5d037648beb1b34d438a0ce7ff9f8ebe15493000d50902e98bb9fbaba8632 size=13004

## attempt root receipts / raw
- raw/results/result.json: sha=c9031faa9442974af344b54c6b700c58f5decb4d1447e4fb6bc16e6373bbee96 size=263459 mtime=2026-09-20 18:30:05
- raw/results/receipt.json: sha=f06a2bc811b55ec720bb0224c673b1b086593cebb554d9d1b844b3834eedb355 size=18147 mtime=2026-09-20 18:30:05
- raw/job-terminal.json: sha=a9bc5f9a150533fd3900140bd2dea1b307c9706e2862158a3a98499a6af6cb38 size=3013 mtime=2026-09-20 18:30:06
- receipts/submission.json: sha=7fb0ebd66652d4d91cf399d2fa5b523b90615f0c493c4275f089ba1a8561aeb6 size=12982 mtime=2026-09-20 18:11:16
- receipts/completion.json: sha=11202bf73f4ad15c84bf46047c0f990b0c5f5f9cb3631819bd301e7d38c648ea size=5102 mtime=2026-09-20 18:30:06
- attempt-0002.intent.json: sha=5a66484d6c65e15d22544cd54c9116547e9fee0418df33d88d69332a191ff3db size=14124 mtime=2026-09-20 18:11:15
- attempt-0002.authorization.json: sha=8204f9759e51fc2b357fbad5d7edaf5464974fc1cee2e4862749d4598c43d685 size=501 mtime=2026-09-20 18:10:34
- barrier/ready/write-heavy.json: mtime=2026-09-20 18:13:22 sha=ce6d895da2e55ad8…
- barrier/bench-start/write-heavy.json: mtime=2026-09-20 18:18:44 sha=834664c83c4d1b50…
- jobs/write-heavy/job-terminal.json: mtime=2026-09-20 18:28:57 sha=450d62d8071ffb1b…
- barrier/ready/balanced.json: mtime=2026-09-20 18:18:44 sha=515a5138a8358195…
- barrier/bench-start/balanced.json: mtime=2026-09-20 18:18:44 sha=5bb8c45aa80c2c8c…
- jobs/balanced/job-terminal.json: mtime=2026-09-20 18:22:12 sha=17ec81ace87c572e…
- barrier/ready/read-heavy.json: mtime=2026-09-20 18:13:22 sha=99ec66c507559eea…
- barrier/bench-start/read-heavy.json: mtime=2026-09-20 18:18:44 sha=75dc3c07bd5fcfbc…
- jobs/read-heavy/job-terminal.json: mtime=2026-09-20 18:25:34 sha=a817c5795dc59b71…
- barrier/bench-go.json: mtime=2026-09-20 18:18:44
- job-terminal write-heavy: {"driver_rc": 0, "shell_rc": 0, "status": "finished", "request_id": null, "host": null}
- job-terminal balanced: {"driver_rc": 0, "shell_rc": 0, "status": "finished", "request_id": null, "host": null}
- job-terminal read-heavy: {"driver_rc": 0, "shell_rc": 0, "status": "finished", "request_id": null, "host": null}
- submission: schema paper-story-a1-paired-group-submission/v1 route direct-qsub-workload-fanout intent_sha256 6bc38262ad4d309154808c234ad601394e4872c2e87f224c91b684c868c897ea
  job: {"workload": "write-heavy", "request_id": "13220.nqsv", "qstat_visibility": null, "queue": null}
  job: {"workload": "balanced", "request_id": "13221.nqsv", "qstat_visibility": null, "queue": null}
  job: {"workload": "read-heavy", "request_id": "13222.nqsv", "qstat_visibility": null, "queue": null}
- completion: schema paper-story-a1-paired-group-completion/v1 keys ['attempt_root', 'group_terminal', 'jobs', 'schema_version', 'source_commit', 'study_id', 'submission_receipt']
   {"group_terminal": {"path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/raw/job-terminal.json", "sha256": "a9bc5f9a150533fd3900140bd2dea1b307c9706e2862158a3a98499a6af6cb38"}, "scheduler_terminal": null, "recorded_epoch": null}
