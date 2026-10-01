# Figure 10: separate attempt comparison

Each input is read separately with the unchanged generator's full load_evidence checks. No pooling, between-attempt difference or ratio, or combined verdict is computed.

| attempt | workload | request | host (reservation) | source commit | CCBench pin | nodes (policy / allocation receipt) | effect (fraction) | floor CV (fraction) | recorded floor judgment | outer status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original: b7f5-20260919a | rr5 | 10807.nqsv | bnode051 | c18a80967ed3d9a901b395116c23f90d6a554b36 | 511c953 | policy 5; receipt 5 (bnode051, bnode060, bnode107, bnode108, bnode132) | 0.6789675418265144 | 0.009536033056996148 | no-regression | reject |
| original: b7f5-20260919a | rr50 | 10808.nqsv | bnode060 | c18a80967ed3d9a901b395116c23f90d6a554b36 | 511c953 | policy 5; receipt 5 (bnode021, bnode060, bnode107, bnode108, bnode112) | 0.12671651401806727 | 0.00725042525457718 | no-regression | reject |
| original: b7f5-20260919a | rr95 | 10809.nqsv | bnode084 | c18a80967ed3d9a901b395116c23f90d6a554b36 | 511c953 | policy 5; receipt 5 (bnode007, bnode022, bnode084, bnode126, bnode130) | -0.11378696258180376 | 0.0022283754708938273 | regression | reject |
| R2: b7f5-r2-20261001a | rr5 | 40685.nqsv | bnode034 | db710338dd443d30a5b7c06da2e2a06afb092175 | 6810666 | policy 5; receipt 5 (bnode034, bnode069, bnode073, bnode079, bnode080) | 0.6239734604583511 | 0.009536033056996148 | no-regression | reject |
| R2: b7f5-r2-20261001a | rr50 | 40686.nqsv | bnode081 | db710338dd443d30a5b7c06da2e2a06afb092175 | 6810666 | policy 5; receipt 5 (bnode081, bnode082, bnode083, bnode084, bnode085) | 0.1389998460596873 | 0.00725042525457718 | no-regression | reject |
| R2: b7f5-r2-20261001a | rr95 | 40687.nqsv | bnode086 | db710338dd443d30a5b7c06da2e2a06afb092175 | 6810666 | policy 5; receipt 5 (bnode086, bnode087, bnode088, bnode089, bnode090) | -0.11449452408913763 | 0.0022283754708938273 | regression | reject |

Host/allocation are supplemental reservation metadata; allocation receipt path and SHA-256 are checked against that reservation. Execution Hosts are counted across the entire section, including multiple hosts on one line. Missing receipts are reported as unknown.

| attempt | cell | role | 5 trace-disabled TPS samples | median TPS | mean TPS ± t 95% CI half-width (df=4) | representative abort rate | correctness | anomaly |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original: b7f5-20260919a | rr5-stock | stock | 2328992.0, 2423324.0, 2354846.0, 2347564.0, 2371395.0 | 2354846.0 | 2365224.2 ± 44535.891143272296 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| original: b7f5-20260919a | rr5-fixed5 | adopted | 4049702.0, 3954525.0, 3731893.0, 3942414.0, 3953710.0 | 3953710.0 | 3926448.8 ± 145372.34880405208 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| original: b7f5-20260919a | rr50-stock | stock | 4135929.0, 3769412.0, 3813768.0, 3878461.0, 3832768.0 | 3832768.0 | 3886067.6 ± 180111.0435709283 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| original: b7f5-20260919a | rr50-fixed5 | adopted | 4378198.0, 4318443.0, 4308209.0, 4333385.0, 4306001.0 | 4318443.0 | 4328847.2 ± 36793.00291443732 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| original: b7f5-20260919a | rr95-stock | stock | 10680928.0, 10171152.0, 10334445.0, 10334945.0, 10351729.0 | 10334945.0 | 10374639.8 ± 231409.62093962898 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| original: b7f5-20260919a | rr95-fixed5 | adopted | 9282678.0, 9137295.0, 9158963.0, 9119021.0, 9190899.0 | 9158963.0 | 9177771.2 ± 80040.22939705364 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| R2: b7f5-r2-20261001a | rr5-stock | stock | 2688859.0, 2541285.0, 2521822.0, 2516911.0, 2496722.0 | 2521822.0 | 2553119.8 ± 96252.05651495342 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| R2: b7f5-r2-20261001a | rr5-fixed5 | adopted | 4207721.0, 4152503.0, 4095372.0, 4068650.0, 4066885.0 | 4095372.0 | 4118226.2 ± 75528.11320832008 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| R2: b7f5-r2-20261001a | rr50-stock | stock | 4006501.0, 3754702.0, 3622265.0, 3743909.0, 3755777.0 | 3754702.0 | 3776630.8 ± 174116.07082908566 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| R2: b7f5-r2-20261001a | rr50-fixed5 | adopted | 4396895.0, 4248262.0, 4276605.0, 4301120.0, 4271456.0 | 4276605.0 | 4298867.6 ± 71926.51632447114 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| R2: b7f5-r2-20261001a | rr95-stock | stock | 10550235.0, 10287147.0, 10031996.0, 10253434.0, 10287587.0 | 10287147.0 | 10282079.8 ± 228383.247438221 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |
| R2: b7f5-r2-20261001a | rr95-fixed5 | adopted | 9348620.0, 9133531.0, 9093970.0, 9109325.0, 9040000.0 | 9109325.0 | 9145089.2 ± 147562.7278061443 | not returned by generator | certified; 1 legacy + 5 performance traces | none in checked serializable traces (not a stored count) |

Correctness is from separate trace-enabled runs; it is not performance certification. The generator does not return representative abort rates or numeric anomaly counts; abort rates are not reconstructed. Mean CI describes samples, not effects or floor judgments.

Generator: `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/tools/plotting/plot_b7_fixed5_regression.py` (SHA-256 `f78da66d4666455dec4da843f51c2c3ea5e7b10fbac2e91ede3d680f480b795f`).
R2 record: `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/r2-record.json` (SHA-256 `0a060c638d6bd84d4f85ef1f498a42841e79220b58f66d4763ba121e84f2d72b`).
R2 scope: `output/insights/2026-10-01/t2853-r2-fig10/README.md`.

original measurement root: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a`.
certification: `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json` (SHA-256 `b6493e4eed17e23cbe10682af72e7c06b805ced1e13a329ffd13df896f4d5431`).
raw_manifest: `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/raw-manifest.json` (SHA-256 `be8163da33416020de3bfdca136ceaff5430e0878c46abe90681e6b0d954f6ac`).

R2 measurement root: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-r2-20261001a`.
certification: `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/collect-root/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json` (SHA-256 `88a3a6bbd2eddecd95f715c00618612d676224811d0e53d15d3edd219284d2f0`).
raw_manifest: `/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/collect-root/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/raw-manifest.json` (SHA-256 `7918298a24d5124018b59ea8dd6c0a6bd67731209390ff351c4a73242a68ff8f`).

Reproduction (cwd /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10):

```sh
/usr/bin/python3.10 -B /work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/tools/t2853_r2_fig10_plot.py --generator /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/tools/plotting/plot_b7_fixed5_regression.py table --original-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a --r2-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-r2-20261001a --r2-certification /work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/collect-root/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json --r2-raw-manifest /work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/collect-root/output/insights/2026-09-19_t1998-b7-fixed5-three-workload/raw-manifest.json --r2-record /work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/r2-record.json --results-document output/insights/2026-10-01/t2853-r2-fig10/README.md --out /work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig10-20261001/figure/fig10_comparison.md
```
