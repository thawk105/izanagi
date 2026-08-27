# [T-1908] Pegasus write-heavy / balanced floor scoping 再取得

authority: none
default_effect: no-state-change

## 結論

現行 source pin と current Pegasus activation で、既存 driver だけを使った 2 workload の
same-window 再取得を完了した。取得量は D145 の
`same-submission-cohort-allocation-session-median-cv` であり、正式な between-run floor ではない。
両 JSON は `time_window_clusters=1`、`eligible_for_compare=false` を保持する。
B-10 事前登録、`external-floor-derived-reference-width`、判定閾値、consumer は変更していない。

| workload | within-run CV | same-cohort between-session CV | abort rate | 判定 |
|---|---:|---:|---:|---|
| write-heavy | 2.8641% | 1.2410% | 80.73% | scoping 値として採用 |
| balanced | 2.1585% | 0.5706% | 69.42% | scoping 値として採用 |

両点とも `high_variance=false`。same-cohort 値が within-run 値より小さいことを、環境が安定している証明や
採否 floor の縮小根拠に使わない。cold-boot、時間ドリフト、時間窓間 common-mode を含まないためである。

## 束縛と再現情報

- request: `953495.nqsv`、queue `gen_S`、compute node `bnode006`
- 実行時刻: 2026-08-28 01:10:06〜01:16:48 JST、elapsed 406 秒、qwait rc=0
- source commit: `f34e19be94a3608099773ac6c1a12a98ae992048`
- CCBench source pin: `511c953`、tracked clean、source bytes SHA-256
  `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6`
- driver: `orchestrator/campaign/pegasus_floor_scoping.py` SHA-256
  `356f7c14c7f879879ba1daa5195db2d175e5897f1e621ecabaa94acfef5c499c`
- job script: `tools/pegasus/floor_scoping.sh` SHA-256
  `ec0e53a7daed8a2602fcc21224adeb4698d3e35303bde278e3f7c94f8b927166`
- current activation: serial 1、state SHA-256
  `f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed`、Pegasus g1
- registered calibration: `calibration-753f535a8d024727.json`、SHA-256
  `753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49`
- 動作点: records 1,000,000、threads 48、clock 2100、trace-disabled stock baseline、
  within 10 reps、between 8 sessions × 5 reps、各 rep 3 秒
- toolchain: Python 3.10.12、GCC/G++ 11、perf 5.15.143
- repo 外 raw/provenance root:
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1908-pegasus-floor/scoping-run-20260828-0029-f34e19be`

tracked copy の SHA-256 は write-heavy
`5e225f05a127d77f574c5f395864a257a1618137a9ab32e6da1224d0f769d92e`、balanced
`fe50fb45ff6f2396d2a2f75974230286a551ad25b75c32e4c488012aa1b3f3eb`。
再現コマンドは各 JSON の `run_cmd` に保存した。外部 root の provenance には git HEAD、実行 script hash、
qstat start snapshot、hostname、interpreter、compiler、perf、依存 source head を保存している。

## 採用検査と限界

- T-1905 は別 prereg / driver / output root で稼働し、本 run との所有重複は無い。
- queue state は投入直前に利用可能。job 内 qstat は running / 48 CPU / bnode006 / rc=0。
- driver の registered calibration 照合、単一テナント検査、clean source admission は通過した。
- job stderr は scheduler の正常 summary だけ。CMake configure の unused C compiler warning は
  gflags/glog が C++ project であるためで、build/install は rc=0、他 stderr と dependency status は空。
- scoping driver は formal/official consumer ではなく、current activation の full attestation receipt を
  artifact に発行しない。したがって本値を formal floor、certified evidence、環境同一性の完全証明へ昇格しない。
- read-heavy、追加時間窓、真正 floor framework、診断計装は本 wave の scope 外であり取得していない。
  T-1942 は read-heavy と判定器 / 成果物への版束縛を含むため、本結果で完了させない。
