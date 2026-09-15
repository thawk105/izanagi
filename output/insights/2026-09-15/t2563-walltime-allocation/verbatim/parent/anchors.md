# 段 1 別紙 — 実アンカー表 (行番号は main 0600887d9 時点)

## A. 予約式そのもの (編集面)

| # | file:line | 現物 | 種別 |
|---|---|---|---|
| A1 | `tools/pegasus/certify_calibration.sh:4` | `#PBS -l elapstim_req=02:00:00` | live |
| A2 | `tools/pegasus/certify_calibration.sh:6-11` | 冒頭の予約式 comment。`build_cap(CCBench=900 + gflags=60 + glog=120)(1080)` と `finalize_reserve(600) = 6610。要求 7200 秒はこれを上回る。` | live |
| A3 | `tools/pegasus/certify_calibration.sh:770` | `frozen_required_s = 10 + 1200 + 5 * 3 * 120 + 10 * 120 + 2 * 3 * 120 + 1080 + int(reserve_s)` | live (receipt へ凍結) |
| A4 | `tools/pegasus/certify_calibration.sh:771-775` | `walltime_formula = ("TSC(10)+cooldown_max(1200)+...build_cap(CCBench=900+gflags=60+glog=120)(1080)+finalize_reserve(600)=6610")` | live (receipt へ凍結) |
| A5 | `tools/pegasus/policies/calibration_v1.json:5-6` | `"certify_walltime": "02:00:00"` / `"certify_walltime_s": 7200` | live |
| A6 | `tools/pegasus/policy.json:7-8` | 同 2 key の複製 (registry 移設の残り、D5432 周辺) | live |

## B. 上の bytes を pin する側 (同じ変更で整合が要る)

| # | file:line | 検査内容 |
|---|---|---|
| B1 | `orchestrator/tests/test_pegasus_tools.py:214` | `assert "5 * 3 * 120 + 10 * 120 + 2 * 3 * 120 + 1080" in source` |
| B2 | `orchestrator/tests/test_pegasus_tools.py:215` | `assert "build_cap(CCBench=900+gflags=60+glog=120)(1080)" in source` |
| B3 | `orchestrator/tests/test_pegasus_tools.py:216` | `assert "finalize_reserve(600)=6610" in source` |
| B4 | `orchestrator/tests/test_pegasus_tools.py:149-152` | `certify["-l"] == "elapstim_req=" + calibration_policy["certify_walltime"]` |
| B5 | `orchestrator/tests/test_pegasus_tools.py:157-160` | `_hms_seconds(certify_walltime) == certify_walltime_s` |
| B6 | `orchestrator/tests/test_pegasus_tools.py:162-171` | 式中の全 `finalize_reserve(N)` が policy の `finalize_reserve_s` と一致し、それが `certify_walltime_s` 未満 |
| B7 | `orchestrator/tests/test_pegasus_tools.py:213` | `assert '"required_s": frozen_required_s' in source` |

## C. 読むだけ・変えない (受理集合の境界)

| # | file:line | 内容 |
|---|---|---|
| C1 | `orchestrator/calibrator/cli.py:63-66` | `COOLDOWN_TIMEOUT_S=1200` / `BENCH_TIMEOUT_S=120` / `TSC_BUDGET_S=10` / `FINALIZE_RESERVE_S=60` |
| C2 | `orchestrator/calibrator/cli.py:69-72` | `RESERVATION_FORMULA` (CLI 側の文言。意味を変えない) |
| C3 | `orchestrator/calibrator/cli.py:220-240` | `reservation_budget()`。`required_s` = 10+1200+points*3*120+10*120+2*3*120+60 = **4990** (points=5) |
| C4 | `orchestrator/calibrator/cli.py:726-731` | 受理判定。`budget.required_s + walltime.reserve_s > walltime.required_s` → `reservation-mismatch`、`walltime.required_s > qsub.elapstim_req_s` → `reservation-qsub-mismatch` |
| C5 | `tools/pegasus/certify_calibration.sh:817-822` | `remaining = DEADLINE_EPOCH - now - FINALIZE_RESERVE_S`。`<= 0` だけを fatal にしている (計測予算に足りるかは見ていない) |
| C6 | `tools/pegasus/certify_calibration.sh:924` | `timeout --signal=TERM "$remaining" exec_calibrate.py`。窓が足りなければ rc≠0 → attempt 失敗 (fail-closed) |
| C7 | `tools/pegasus/submit_certify.sh:92,188` | policy の `certify_walltime_s` を読んで `elapstim_req_s` に載せる。policy 追従なので独自の literal 無し |

## D. 現行 script の `timeout` 上限 (実測、copy はループ 3 回)

| 行 | 上限 | 対象 | 計測前/後 |
|---:|---:|---|---|
| 252 | 30 | `qstat -f` | 前 |
| 383 | 120 | static attestation probe | 前 |
| 475/481/487 | 60×3=180 | gflags configure / build / install | 前 |
| 540/546/552 | 120×3=360 | glog configure / build / install | 前 |
| 587 | 120×3=360 | third-party copy (masstree / mimalloc / googletest) | 前 |
| 598 | 120 | pristine source 検証 | 前 |
| 681/682 | 900×2=1800 | CCBench configure / build | 前 |
| 685 | 60 | `sha256sum` | 前 |
| 687 | 60 | `nm -C` (規律 1 の trace symbol 検査) | 前 |
| 729 | 120 | pre attestation probe | 前 |
| 858/863 | 10×2=20 | perf 実体 smoke | 前 |
| 924 | `remaining` | 計測本体 | — |
| 929 | 120 | post attestation probe | 後 |

- **計測前の直列和 = 3230 秒**、計測後 = 120 秒、合計 3350 秒。
- 凍結式の `build_cap(1080)` はこの 3230 を **2150 秒過小申告**している。
  項の取りこぼし: CCBench は 2 command (900 でなく 1800)、gflags は 3 command (60 でなく 180)、
  glog は 3 command (120 でなく 360)、copy 360 / pristine 検証 120 / probe 240 / qstat 30 /
  hash+nm 120 / perf 20 は式に存在しない。
- 真値 = 3230 + 計測予算 + finalize_reserve(600)。計測予算を CLI の `required_s`(4990) で積むと
  **8820 秒**、CLI 内蔵 reserve 60 を除いた 4930 で積むと **8760 秒**。いずれも要求 7200 を超える。
- 最悪経路では計測窓が 7200-3230-600 = **3370 秒**しか残らず、必要な 4930 秒に届かない。
  ただし窓不足は `timeout --signal=TERM` の rc≠0 → attempt 失敗であり、誤認定は生じない
  (規律 2 は破れていない。これは「保証の嘘」であって「受理の穴」ではない)。

## E. repo 内に既にある同型の正しい書き方 (一般化はしない。形の前例としてだけ示す)

| # | 場所 | 形 |
|---|---|---|
| E1 | `tools/pegasus/policy.json` `silo_ladder_rung1.walltime_formula` | 段ごとの上限を列挙し `...+finalize=600<=7200` と外側を明示 |
| E2 | `tools/pegasus/policy.json` `ss2pl_lock_study.walltime_formula` | 同形 + `each sum is strictly below 10800` |
| E3 | `output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh` (`orchestrator/tests/test_backoff_requested_us.py:1111-1116` が pin) | job 自身が `TOTAL_BUDGET_SECONDS < WALLTIME_SECONDS` を実行時に検査する |

## F. gen_S の要求時間の前例 (要求枠を上げる案の実行可能性)

`b10_backoff_shape_campaign.sh` 24:00:00 / `t126_qualification.sh` 10:00:00 /
`floor_campaign.sh` 10:00:00 / `paper_story_a1_paired.sh`・`a2` 06:00:00 /
`b10_backoff_grid.sh` 05:00:00 / `acceptance_nproc_study.sh` 04:00:00 /
`p3_s4_loop_pegasus.sh`・`floor_scoping.sh`・`ss2pl_lock_study.sh`・`t141_region_profile.sh` 03:00:00。
→ 7200 超は queue 上の障害にならない。実消費は 186 秒なので資源は余分に食わない。
費用は queue 待ちが伸びうる点だけ (1461 実測: 7 秒 と 525 秒 の 2 標本しかない)。

## G. pin 閉包で「無い」ことを実測した項目

- `tools/pegasus/policies/calibration_v1.json` の **bytes を sha256 で pin する test は無い**。
  `orchestrator/tests/test_claude_transport.py:164-186` が byte pin を張るのは `transport_v1.json`
  だけで、`calibration_v1.json` は `registry_v1.json` の path 一覧に載るのみ。
- `orchestrator/tests/test_pegasus_policy_registry.py:27-30` は key の**存在**を検査し、値は見ない。
- `orchestrator/tests/conftest.py:161` の `requested_s = 7200` は合成 fixture で、policy を読まない。
  certify policy の consumer ではない (同 file の docstring どおり「内部整合な 1 例」)。
- `orchestrator/tests/test_backoff_requested_us.py:1112` の `WALLTIME_SECONDS=7200` は
  `output/insights/2026-08-28_t1941-.../job-body.sh` (別 job の凍結成果物) に対する pin。本件と無関係。
- **未確認 (段 2 で閉じること):** `output/env/pegasus/calibration/attempts/**` の既存 receipt を
  現行式で再検算する consumer が居ないか。居るなら過去 receipt は歴史記録として据え置く。
