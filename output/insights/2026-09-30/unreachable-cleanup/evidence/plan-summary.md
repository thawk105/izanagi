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
## discard-scratch: 99

日時: 2026-09-19T07:40:12+09:00 ～ 2026-09-30T16:09:31+09:00

- 012af146ca 2026-09-30T14:25:47+09:00 md32-scratch/README.md, md32-scratch/launch_promo_confirm.py
- 059d3b0f0b 2026-09-29T15:11:38+09:00 genopt_gl_scratch/fmt_check.py, genopt_gl_scratch/gate_check.py, genopt_gl_scratch/launch_gate_liveness.py, genopt_gl_scratch/make_patches.py, genopt_gl_scratch/mutation_check.py
- 0935923842 2026-09-29T07:37:21+09:00 probe-t2273is/t2273is_ab_analyze.py
- 09ef9a61ed 2026-09-30T12:44:40+09:00 wave-probe/README.md, wave-probe/bench_abab.py, wave-probe/equiv_fixtures.py, wave-probe/equiv_plugin.py, wave-probe/equiv_real.py
- 0e6d41d303 2026-09-30T00:01:49+09:00 verify-target/launch_cicada_run_target.py

捨てた場合に失うもの (最上位 dir 別 notmain pair 数): {"md32-scratch": 30, "genopt_gl_scratch": 19, "probe-t2273is": 6, "wave-probe": 6, "verify-target": 2, "scratch": 74, ".gcfix-ci": 2, ".gcfix-launcher": 3, ".gcfix-work": 5, "t2851_anchor_smoke.py": 6, ".cicada-launcher": 8, "t2786_probe": 13, "scratch-acp": 6, "verify-scratch": 3, "tmp-verify": 5, "md7-probe": 1, "t2825-probe": 6, ".t2847-launcher": 4, "t2847_capacity": 2, "t2872_probe": 14, "t2847_launch": 2, "probe": 2, "scratch-output-pruning": 15, "probe-fig15-fix": 2, "t2868_probe": 1}

## discard-landed: 30

日時: 2026-09-21T01:38:44+09:00 ～ 2026-09-29T23:48:25+09:00

- 134d7856c4 2026-09-29T16:47:50+09:00 .cicada-launcher/launch_cicada_run.py
- 15eccc8675 2026-09-27T15:44:21+09:00 probe-t2273pi/t2273pi_ab_analyze.py
- 199c8a67a2 2026-09-29T23:48:25+09:00 tools/strip_claude_session_trailers.sh
- 1df428f401 2026-09-21T20:47:53+09:00 tools/t2826_modify_timing_aggregate.py, tools/t2826_probe_plugin.py
- 22e361d9cb 2026-09-23T09:16:40+09:00 tools/t2273_replica_runner.py

捨てた場合に失うもの (最上位 dir 別 notmain pair 数): {}

## discard-extra: 1

日時: 2026-09-21T11:09:25+09:00 ～ 2026-09-21T11:09:25+09:00

- b3de31e09e 2026-09-21T11:09:25+09:00 T-2840 が追記対象に指定した T-2344 の amend 前の reflog 専用版。変更 path はすべて main に既存のため監査は報告しない。後継 ae0764eae が main に在り、38 file 中 33 が同一・2 件は fold 済み fragment・3 件は着地版が後の修正を含む差 (T-2840 の記載)

捨てた場合に失うもの (最上位 dir 別 notmain pair 数): {}

