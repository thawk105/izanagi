# 到達不能 commit 分類

## reachable-again: 0

日時: なし ～ なし

## rescue-body: 23

日時: 2026-09-21T01:41:51+09:00 ～ 2026-09-26T21:09:02+09:00

- 0f40207b09 2026-09-21T08:09:41+09:00 tools/gate_wait_probe.py
- 1bd414c07a 2026-09-23T21:09:22+09:00 output/insights/2026-09-23/t2797-b5-main-run/scripts/calibration.sh
- 2a1b833399 2026-09-26T20:43:21+09:00 tools/t2273_replica_analyze.py, tools/t2273_replica_plugin.py, tools/t2273_replica_runner.py
- 2ebf25e246 2026-09-26T20:32:17+09:00 tools/t2273_replica_analyze.py, tools/t2273_replica_plugin.py, tools/t2273_replica_runner.py
- 31894443ef 2026-09-21T14:33:42+09:00 tools/t2826_modify_timing_aggregate.py, tools/t2826_modify_timing_probe.sh, tools/t2826_probe_plugin.py
## rescue-scratch-output: 40

日時: 2026-09-21T21:59:30+09:00 ～ 2026-09-30T15:42:20+09:00

- 012af146ca 2026-09-30T14:25:47+09:00 md32-scratch/README.md
- 059d3b0f0b 2026-09-29T15:11:38+09:00 genopt_gl_scratch/patches/broken-silo-b1-unregistered-first-read.patch, genopt_gl_scratch/patches/fix-silo-intra-txn-values.patch, genopt_gl_scratch/patches/instr-silo-gate-witness.patch
- 09ef9a61ed 2026-09-30T12:44:40+09:00 wave-probe/README.md
- 0eaf6c6dab 2026-09-30T12:52:30+09:00 md32-scratch/README.md, md32-scratch/diag-counters.patch, md32-scratch/v-ronly-nopromo.patch, md32-scratch/v-uaf-reorder.patch, md32-scratch/v-update-keep.patch
- 0ee3239770 2026-09-27T00:01:41+09:00 scratch/t2797-v2-mutation/README.md
## discard-scratch: 59

日時: 2026-09-19T07:40:12+09:00 ～ 2026-09-30T16:09:31+09:00

- 0935923842 2026-09-29T07:37:21+09:00 probe-t2273is/t2273is_ab_analyze.py
- 0e6d41d303 2026-09-30T00:01:49+09:00 verify-target/launch_cicada_run_target.py
- 0f75362db6 2026-09-30T00:14:17+09:00 .gcfix-ci/run_ci_build.sh
- 13cafb065c 2026-09-23T21:55:42+09:00 t2851_anchor_smoke.py
- 17f0e5e73e 2026-09-29T16:08:09+09:00 .cicada-launcher/launch_cicada_run.py

捨てた場合に失うもの (最上位 dir 別 notmain pair 数): {"probe-t2273is": 6, "verify-target": 2, ".gcfix-ci": 1, "t2851_anchor_smoke.py": 6, ".cicada-launcher": 6, "t2786_probe": 13, "scratch": 8, "verify-scratch": 3, "tmp-verify": 5, "md7-probe": 1, "t2825-probe": 6, ".t2847-launcher": 4, "md32-scratch": 2, "t2847_capacity": 2, "wave-probe": 1, "t2872_probe": 1, "t2847_launch": 2, "genopt_gl_scratch": 1, "probe": 2, "scratch-output-pruning": 15, "t2868_probe": 1}

捨てた場合に失うもの (拡張子別 notmain pair 数): {".conf": 1, ".json": 5, ".py": 73, ".sh": 9}

## discard-extra: 1

日時: 2026-09-21T11:09:25+09:00 ～ 2026-09-21T11:09:25+09:00

- b3de31e09e 2026-09-21T11:09:25+09:00 T-2840 が追記対象に指定した T-2344 の amend 前の reflog 専用版。変更 path はすべて main に既存のため監査は報告しない。後継 ae0764eae が main に在り、38 file 中 33 が同一・2 件は fold 済み fragment・3 件は着地版が後の修正を含む差 (T-2840 の記載)

捨てた場合に失うもの (最上位 dir 別 notmain pair 数): {}

## discard-landed: 30

日時: 2026-09-21T01:38:44+09:00 ～ 2026-09-29T23:48:25+09:00

- 134d7856c4 2026-09-29T16:47:50+09:00 .cicada-launcher/launch_cicada_run.py
- 15eccc8675 2026-09-27T15:44:21+09:00 probe-t2273pi/t2273pi_ab_analyze.py
- 199c8a67a2 2026-09-29T23:48:25+09:00 tools/strip_claude_session_trailers.sh
- 1df428f401 2026-09-21T20:47:53+09:00 tools/t2826_modify_timing_aggregate.py, tools/t2826_probe_plugin.py
- 22e361d9cb 2026-09-23T09:16:40+09:00 tools/t2273_replica_runner.py

捨てた場合に失うもの (最上位 dir 別 notmain pair 数): {}

