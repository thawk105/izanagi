# [T-2698] T-2650 の config.h 供給修正を載せた main から official 床値 campaign を再投入し、cell build 段を越えて完走した — official 床値の実値と試行台帳側 gate の実値域を初めて取得した

branch `worktree-dev-wave-t2698-official-floor-resubmit`、base `8f17db5981a689789916fcc56ccf373b10347e1a`
(着手直前の local main)。実装面の差分はゼロ — `tools/pegasus/floor_campaign.sh` /
`submit_floor.sh` / orchestrator / test はいずれも無編集で、本 wave の成果物は実機走行の記録だけである。

**official 床値 campaign は cell build 段を越え、96 attempt すべてを計測して `driver_rc=0` で完走した。**
2026-09-09 の初回 official (`988501.nqsv`、起動証明書で停止) と T-1851 の 3 走行
(`998882` / `999039` / `999102`、いずれも cell build 段の condition gate で停止) を含め、
**official 床値が計測段へ到達したのはこれが初めて**である。得られたのは
(a) official 床値の実値 (§3)、(b) 試行台帳 (attempt registry) 側 gate の実値域 (§4)、
(c) 共有 admission root の実消費 (§5) である。

**本 wave は床値を発効させていない。** result は producer 自身が「floor 案 (何も発効させていない)」と
書くとおりで、freeze への書込み・freeze v2 再凍結は本 wave の scope 外である (§7)。

---

## 1. 何をしたか

[T-2650] (D2059 / D2060) が着地した main `8f17db598` から、
`tools/pegasus/submit_floor.sh --confirm-official-floor-run` で official 床値 campaign を **1 回**投入した。
承認は D926 の submission nonce 束縛で運び、`qsub -v` を自作する経路は使っていない。

| # | request ID | nonce | source commit | driver_rc | Elapse |
|---|---|---|---|---:|---:|
| 1 | `1818.nqsv` | `eb2759286496ac320307d0b3c3064e18` | `8f17db598…` | **0** | 4769 秒 |

- job script sha256 = `9a7cd1f80ccec6a15b6f0e3fd842e4e5a9ad382907d4fbb5d4fdf1c94af6c62d`。
  T-1851 の 3 走行および 2026-09-09 の初回 official と同一。`floor_campaign.sh` は T-1851 以後 main で
  1 byte も変わっていない (main 現物の blob で実測)。`job-result.json` の `executing_script_sha256` も同値。
- T-1851 の 3 回目の走行時 commit `c185b9fd4` と本 base `8f17db598` の差分のうち本走行に効くのは
  `orchestrator/campaign/s8b_floor_campaign.py` (+18/-1、T-2650 の config.h 供給) と
  `orchestrator/campaign/s1_direct_comparison.py` (+7/-2) だけで、
  `output/s8b-freeze/holdout_freeze.json` / `floor_protocol.json` / `floor-protocols/` /
  `tools/pegasus/policy.json` / `policies/floor_v1.json` / `submit_floor.sh` は差分ゼロ。
  **停止していた走行と完走した走行の差は T-2650 の供給修正だけ**であり、T-2650 §9 が
  「本 wave では確認していない」と残した実機通過が本走行で閉じた。
- 投入は背景 job セッションの Bash tool から行った (F49 (ii) の許可経路)。投入直後の 3 点検査は
  (a) 計算ノード側 marker `checkpoint.jsonl` の実在 (起動後 20:19 JST に確認)、
  (b) `qstat` で request 可視 (`PRR` → `RUN`)、(c) 会計痕跡
  (`Started Request Time: 20:19:02` / `Ended Request Time: 21:38:27` / `Elapse: 4769S`、
  `evidence/1818-scheduler-accounting.txt`) のすべてが成立した。
- 投入元は wave worktree。third-party 3 source は投入前に `fetch_third_party.py hydrate` で永続 cache から
  staging へ複製した (masstree `b3c5d054…` / mimalloc `02a2f5df…` / googletest `f8d7d77c…`、rc=0)。
- 完了待ちは `tools/dev_wave_wait.py compute` (done = `job-result.json`、会計 = `scheduler.stderr`) を
  detach 起動した 1 本で行い、`.done` の rc=0 と `job-result.json` の実在で終端を検算した
  (`evidence/1818-compute-receipt.json`、`done_evidence: true`)。

## 2. 走行の到達段 — すべて通過

| 段 (checkpoint / journal) | 時刻 (JST) | 備考 |
|---|---|---|
| job 起動 (`bootstrap`) | 20:19:02 | 実行ノード `bnode004` (Intel Xeon Platinum 8468、48 core、SMT off) |
| `static-admission` → `source-identity` → `allocation-reservation` | 20:19:02〜20:19:09 | `reservation.json`: requested 36000 秒、deadline epoch 1789593542 |
| `gflags-build` / `glog-build` | 20:19:10〜20:19:21 | |
| `protocol-resolution` | 20:19:21 | resolved protocol sha256 `2c8cf9be…` (T-1851 と同一) |
| `floor-driver` entered / `launch-start` | 20:19:22 / 20:19:25 | **起動証明書を発行** (`clean_scan_digest` `f730e1b6…`、`v1_freeze_sha256` `315b1eb8…`) |
| driver `run-linked` | 20:20:12 | run_dir `…/s8b-floor-official/20260916T111925Z-2c8cf9be` |
| perf-preflight | 20:20 台 | `available: false`、`reason: nonzero-rc` (この機体では perf 不要、既裁定) |
| 環境契約 execution receipt | 20:19:23 | 契約 `e576e9cd…` (pegasus 第 1 世代)、比較 21 項目すべて `pass` |
| **cell build 段 (prebuild + 12 cell)** | 20:19:25〜20:26:43 | **7 分 18 秒で通過。T-1851 の 3 走行はここで停止していた** |
| `campaign-start` / round 1 開始 | 20:26:43 | |
| round 1〜8 (12 cell × 8 = 96 session) | 20:26:43〜21:38:07 | 71 分 24 秒 |
| journal `terminal` | 21:38 | `{"event": "terminal", "status": "completed"}` |
| `job-result` | 21:38:27 | `driver_rc: 0`、`failure.json` なし |

driver stderr (`floor-driver.stderr`、207 bytes) に載ったのは凍結 hold
`IZANAGI_FREEZE_HOLD {"check_id": "s8b-floor.protocol-bytes-expected-pin", "decision": "freeze-verification-hold", …}`
の 1 行だけで、これは T-1851 §9 が記録した `status=held` の marker と同じ (走行を止めない)。
condition gate の拒否 (`BACKOFF_FIXED:supply-effectuation:preprocess-failed`) は 1 行も出ていない。

## 3. official 床値の実値 (floor 案、未発効)

`result.json` (schema `s8b-floor-result/v5`、formula `s8b-floor-stats/v2`、mode `official`、
`n_sessions` 8、`reps` 5、stock `stock_common`、`wired_min_rel_floor` 0.03、
`scale_adequacy_rel_tolerance` 0.10、ccbench pin `511c9538…`、freeze `315b1eb8…`、protocol `2c8cf9be…`、
manifest `50af60db…`)。原本は run_dir に置いたまま (§9)。三軸 literal を含まない射影を
`evidence/20260916T111925Z-2c8cf9be-result-floors-extract.json` に置いた。

| holdout | `scale_ref` (stock median) | `scalar_alt` = 全 pair の floor | floor / scale_ref | machine anomaly cell |
|---|---:|---:|---:|---|
| rr20 | 1,193,931.5 | **35,817.945** | 0.0300 | なし |
| rr80 | 1,535,526.0 | **46,065.78** | 0.0300 | なし |

- **両 holdout とも floor は `wired_min_rel_floor` (0.03) × `scale_ref` に一致する。** 各 pair の
  `u_noise` (session median の散らばりから来る項) は rr20 で 15,859〜28,966、rr80 で 20,843〜27,543 で、
  いずれも配線済み下限 (35,818 / 46,066) を下回る。つまり**この走行では床は実測 noise ではなく
  配線下限で決まっている**。
- 12 cell すべて `valid`、`n_valid` 8/8、cell CV は 0.0023〜0.0124 (上限 `cell_cv_max` 0.15)。
  除外 session 0 件、retry 0 件、exec 失敗 0 件、machine anomaly 0 件。
- pair ごとの床が同値なのは formula v2 の定義 (pair の floor が `max(u_noise, wired_min × scale_ref)`
  型で下限が支配) によるもので、pair 間の性能差 (cell median は 1.17M〜7.31M と 6 倍の幅) を
  床が均しているわけではない。
- `eligible_for_refreeze: true` は **producer の自己申告**であり、D488 のとおり信頼根にしない。
  発効の可否は本 wave で判断していない (§7)。
- holdout の workload 定義は `output/s8b-freeze/holdout_freeze.json` を参照する
  (本文に三軸の値を逐語で並べない — F39 / D88 の clean scan 不変条件)。

## 4. 試行台帳 (attempt registry) 側 gate の実値域

C3b (`output/insights/2026-09-09/t1851-unit-c3b-floor-range/README.md` §7) の 4 分類を、
本走行で埋め直す。registry の原本は共有 admission root
`<git-common-dir>/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/315b1eb8…/2c8cf9be…/registry.jsonl`
(481 行、sha256 `8975bf3a…`) で、複製を `evidence/attempt-registry-315b1eb8-2c8cf9be-registry.jsonl` に置いた。

### (1) 動的に観測した値

| 述語 / gate | 消費 field | 観測値 |
|---|---|---|
| submission nonce 束縛 (D926) | `IZANAGI_SUBMISSION_NONCE` / `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` | 両者 exact 一致 `eb275928…`、approval bit が立った |
| source identity | `executing_script_sha256` / `job_script_sha256` / committed blob | 3 者一致 `9a7cd1f8…` |
| reservation preflight | `requested_s` / `scheduler_started_epoch` / `deadline_epoch` / `host` / `boot_id` | `36000` / `1789557542` / `1789593542` / `bnode004` / `4013e08b-…` |
| scheduler elapse 照合 | `policy_floor_walltime_s` / `scheduler_elapse_limit_s` / `policy_match` | `36000` / `36000` / `true` |
| protocol resolution | resolved path と canonical sha256 | versioned path / `2c8cf9be…` |
| launch certificate | `clean_scan_digest` / `v1_freeze_sha256` / `protocol_sha256` | `f730e1b6…` / `315b1eb8…` / `2c8cf9be…` — **発行され、走行を止めていない** |
| 凍結 hold | `check_id` / `decision` / `release_condition` | `s8b-floor.protocol-bytes-expected-pin` / `freeze-verification-hold` / `explicit-user-command-only` (held marker のみ) |
| condition gate (cell build) | reason code | **拒否なし** (T-1851 で 3 回止めた `preprocess-failed` は出ていない) |
| registry genesis (`freeze` event) | `slots` / `max_consumptions_per_budget_key` / `retryable_failure_reasons` / `recovery_policy_sha256` / `schedule_sha256` | **288 slot が実体化** (12 cell × 8 rep × (planned 1 + retry 2)) / `10` / 4 種 (`measurement_dispersion_exceeded`, `measurement_environment_conflict`, `measurement_execution_unavailable`, `measurement_sample_incomplete`) / `6ac1b69b…` / `53470678…` |
| attempt ごとの event 鎖 | `start` → `pre-observation-seal` → `classification` → `observation-start` → `terminal` | 96 attempt × 5 event = 480 行 + freeze 1 行 = 481 行。`previous_event_sha256` 鎖は 481 件すべて distinct、chain head `142efdf7…` (result.json の `attempt_registry.chain_head_sha256` と一致) |
| classification authority | `authority_id` / `authority_policy_sha256` / `external_evidence_sha256` | `s8b-floor-attempt-launcher/pre-output-classification/v1` / `f9a4dc7d…` / `cfadaa41…` (96 件すべて同一 — probe 4 値が全 attempt で同一だったため) |
| `pre_observation_failure_reason` | | 96 件すべて `null` |
| `terminal_status` / `failure_reason` / `measurement_retry_reason` | | 96 件すべて `observed` / `null` / `null` |
| `attempt_ordinal` / `measurement_ordinal` / `repetition` | | `0` のみ / `0` のみ / `0`〜`7` (各 12 件) |
| `probe_before` / `probe_after` の 4 値 | `rc` / `stdout` / `stderr` / `competing` | 96 session すべて `1` / `''` / `''` / `false` (両 probe とも) — C3b が「1 件も観測していない」と書いた 4 key を初めて観測した |
| process identity | `execution_uuid` / `pid` / `starttime` | `90e8768d…` / `490952` / `16287864` (481 行で単一の process) |
| `primary_value` | session median | 96 件 distinct、1.164M〜7.341M |
| holdout admission receipt | `admission_row_count` / `attempt_row_count` / `ledger_projection_sha256` | `12` / `96` / `0d680d37…` |

### (2) 静的に宣言された closure → 本走行で実体化した

C3b が「宣言値であって観測値ではない」とした 288 slot は、`freeze` event の `slots` 配列として
実体化し、そのうち planned 96 slot が `start`〜`terminal` まで消費された。retry slot 192 件は
未消費のまま (retry が 1 件も発火しなかったため)。

### (3) artifact に所在が無い入力 → 間接証拠だけが得られた

封印 pre-probe の exact type、issuer state membership、owner identity、post-probe origin seal、
one-shot `used` は依然として直接観測できない。本走行で得られたのは「96 attempt すべてで
`classification` と `terminal(observed)` が成立した」という**間接証拠**だけである。
C3b の判定 (原理的に直接観測不能) は変わらない。

### (4) 未発火の枝 → 依然として未観測

- `probe_before.competing = true` と `probe_after = null` (競合分岐): 96 件とも `competing=false` で未発火。
- `retry_ordinal = 1..2`: retry が 0 件なので未発火。
- cut-6 replay 系 (resume 経路): fresh run なので適用域外。
- `attempt_ordinal > 0`: production gate が拒否する値であり、当然 0 件。

**未観測を到達不能と読んではならない** (C3b と同じ)。ただし「正常経路の全 field が実値で埋まった」
ことは本走行が初めて示した。

## 5. 台帳消費 — 投入前後 snapshot の差分

共有 admission root の投入前 snapshot は T-1851 の走行後 snapshot と bytes 一致していた
(ledger 72 行 `2b2c5121…` / attempt-ledger 516 行 `bbb63cad…`、directory 10 種の件数、
registry namespace 1 件)。走行後との差分は次のとおり (`evidence/admission-snapshot-{presubmit,postsubmit}.txt`)。

| 対象 | 投入前 | 走行後 | 差 |
|---|---:|---:|---|
| `ledger.jsonl` | 72 行 | 84 行 | +12 (`admit` event、cell ごと 1 行、各 `attempt_count` 10 = planned 8 + retry 2) |
| `attempt-ledger.jsonl` | 516 行 | 612 行 | +96 (`consume` event、planned attempt ごと 1 行、schema `s8b-holdout-measurement-generation-attempt-consumption/v1`) |
| `measurement-generation-claims/` | 36 | 48 | +12 |
| `measurement-generation-consumed/` | 288 | 384 | +96 |
| `floor-attempt-registries/` | 1 namespace | 2 namespace | +1 (`315b1eb8…/2c8cf9be…/registry.jsonl`、481 行、sha256 `8975bf3a…`) |
| `claims/` / `consumed/` | 36 / 228 | 36 / 228 | 変化なし |
| 旧 fixture namespace `db07b575…/d388477f…` | | | sha256 不変 (`7d0231a1…` / `1ab0d222…`) |

計測枠の上限 120 (planned 96 + cell retry 24) のうち **96 を消費し、retry 24 は 1 枠も焼いていない**。
T-1851 §9 が書いた「消費済み slot は recovery でも戻らない」不可逆性は、本走行で初めて実際に効いた。
**列挙した数量と bytes/hash の一致・差分に限定した主張**であり、同件数の内容変更をこの観測は弁別しない。

## 6. その他の観測 (診断であって欠陥の主張ではない)

- **session 所要と round 間オーバーヘッドが attempt 数に線形に増える。** session `duration_s` は
  seq 0 の 26.95 秒から seq 95 の 33.09 秒へ単調増加 (約 +0.064 秒/attempt)、round の壁時計は
  377 / 420 / 465 / 510 / 564 / 606 / 658 / 700 秒で、session 所要の和を引いた残り
  (49 / 83 / 119 / 155 / 198 / 232 / 274 / 308 秒) は round ごとに約 37 秒ずつ増える。
  96 attempt の合計 71 分は walltime 36000 秒に対して問題にならないが、attempt 数を増やす設計では
  O(n) の項が効く。原因の特定は本 wave の scope 外 (仮想リスク向けの検査を足さない)。
- registry の `start` event の `started_at` は 96 件すべて `2026-09-16T11:26:43.191055+00:00`
  (campaign-start と同時刻) で、attempt 固有の時刻は `classification.classified_at` と
  `terminal.finished_at` (各 96 件 distinct) が持つ。field の意味を確かめたわけではなく、
  値域の事実として記す。
- 環境契約の execution receipt は 21 項目すべて `pass` (cpu vendor / family / model / model name /
  cores physical・logical・SMT・affinity / cache topology / numa / tsc 5 項 / effective clock 3 項 /
  visibility 3 項)。

## 7. 到達範囲と非保証

- **床値は発効していない。** result は「floor 案」であり、`holdout_freeze.json` への floor 書込み・
  freeze v2 再凍結 (`docs/phase3-8b-restart-runbook.md` の第 2 段) は本 wave の scope 外で、
  次の一手として裁定へ残す。本 insight を根拠に freeze を書き換えてはならない。
- `eligible_for_refreeze: true` は producer 自己申告 (D488)。発効判定の入力にはなるが根拠にはならない。
- 床が配線下限で決まったことは**この 1 走行の事実**であり、別 run 間の変動 (between-run) を
  含まない (result.md 冒頭の producer 注記と同じ)。
- 凍結 hold `s8b-floor.protocol-bytes-expected-pin` の効力は本走行でも証明していない
  (T-1851 §9 と同じ — どちらの比較も通ったので走行を止めていない)。
- **T-2699 (非 sort 単独の床値 campaign に残る `config.h` 欠落) は本走行では触れていない。**
  本走行の cell 集合は `sort_best` 2 cell を含む 12 cell で、T-2650 §3 の prebuild 発火条件が成立する
  構成である。非 sort 単独構成の実機通過はこの結果から言えない。
- 3 点検査 (c) の会計痕跡は `Elapse` と `Remaining Elapse` だけで CPU 時間を含まない
  (この機体の `qstat` に履歴 option が無い)。
- 走行中の実行ノードの単独性は `cpuset 0-47` の割当てと execution receipt の visibility 3 項
  (`hidepid` / pid namespace) を通過したことで確認したが、pgrep による同時刻の外乱検査は
  job body 側の既存 probe (`probe_before/after.competing=false` × 96) に任せた。
- 敵対子は起動していない (軽量版)。設計択一・防壁・受理集合に触れない記録 wave であるため。

## 8. 検査

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode fresh --forbid-worktree-handoff --external-handoff` | rc=0 |
| `fetch_third_party.py hydrate` (投入前) | rc=0 (3 source の HEAD = pin) |
| `submit_floor.sh --confirm-official-floor-run` | rc=0、request `1818.nqsv` |
| `dev_wave_wait.py compute` | rc=0、`done_evidence: true` |
| 投入後の 3 点検査 (marker / qstat / 会計) | すべて成立 |
| 三軸 conjunction 走査 (`s8b_holdout_freeze search`)、wave worktree | rc=1 — hit は rr20 / rr80 とも **untracked の run_dir 原本 3 file だけ** (`journal.jsonl` / `manifest.json` / `result.json`)。26,397 file 走査、陽性対照 181 件。insight の evidence 複製に hit なし |
| 同走査、同 tip の clean な別 worktree | 記録 commit 後に実走、結果は worklog エントリに書く |
| `tools/check_docs.py` | 記録 commit 前に実走、結果は worklog エントリに書く |
| 変異 matrix | 実装面の差分ゼロにつき `DW-S04` の免除 |
| 受入全走 | land 前に 1 回投入し、結果は worklog エントリに書く (本 insight の作成時点では未実施) |

## 9. 収録物

- `evidence/admission-snapshot-presubmit.txt` / `evidence/admission-snapshot-postsubmit.txt`
  — 共有 admission root の投入前後 snapshot (件数・行数・sha256)
- `evidence/1818-submit-receipt.json` — 投入器の receipt (preflight 4 種の raw を含む)
- `evidence/1818-scheduler-accounting.txt` — PBS 会計 (`Started` / `Ended` / `Elapse 4769S`)
- `evidence/1818-job-result.json` — job 終端記録 (`driver_rc: 0`)
- `evidence/1818-reservation.json` / `evidence/1818-scheduler-elapse.json` — 予約 preflight の実値
- `evidence/1818-checkpoint.jsonl` — 計算ノード側 marker (repo 外 evidence root からの複製)
- `evidence/1818-compute-receipt.json` — 待ち手の受領証
- `evidence/20260916T111925Z-2c8cf9be-launch_certificate.json` — 発行された起動証明書
- `evidence/20260916T111925Z-2c8cf9be-result-floors-extract.json` — result.json の三軸 literal を含まない射影
  (floors / attempt_registry / holdout_admission / perf_preflight)
- `evidence/attempt-registry-315b1eb8-2c8cf9be-registry.jsonl` — 試行台帳 registry の複製 (481 行)
- `evidence/MANIFEST.json` — 各 file の複製元 path・bytes・sha256

**repo へ複製していない原本** (三軸 literal を含むため、clean scan 不変条件により置かない):
- `<wave worktree>/output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/result.json`
  (sha256 `b111831e9d002b523b57b0096a04bf03bb86b9b01fb5418511909f8ed4075620`)、同 `result.md`、
  同 `journal.jsonl` (213 行)、同 `manifest.json`
- `<wave worktree>/output/env/pegasus/floor/job-staging/0:1818.nqsv/` (phase-build / phase-preflight /
  sort-swo-oracle 等の receipt 群、`floor-driver.stderr`)
- `<wave worktree>/output/env/pegasus/binaries/<sha256>` × 12 (content-addressed binary store。
  result / manifest が `store_path` で参照する測定 binary)

**repo 外への退避 bundle** (runbook `docs/phase3-8b-restart-runbook.md` W-2 の「run directory だけでは
足りない」に従い、run directory / binary store 12 本 / submission receipt / job staging / claim を
1 bundle にまとめ、各 file の bytes と sha256 を `MANIFEST.json` に残した):
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2698-official-floor-resubmit/run-backup/` (108 file)。
wave worktree 側の原本は撤去まで残す。**v2 candidate 生成時には official result が repo 相対 path に
在る必要がある** (同 W-2) ので、退避と再配置の順序は後続 (床値 result の退避順序を扱う
`dev-wave-t2386-floor-evac-order`、本 wave 時点で未着地) の着地規則に従う。

## erratum (2026-09-20 19:25 JST): wave worktree 側の原本は撤去済み — 退避 bundle `run-backup/` が唯一の repo 外原本になった

本文「wave worktree 側の原本は撤去まで残す」の wave worktree (`.claude/worktrees/dev-wave-t2698-official-floor-resubmit`) は
2026-09-20 19:25 JST の cleanup で撤去された (引き渡し script の退避 tar は空だったが、本 wave が作った
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2698-official-floor-resubmit/run-backup/` (109 file、`MANIFEST.json` に bytes と sha256) が
run directory・binary store 12 本・submission receipt・job staging・claim を含むため実害なし)。worktree に在った `output/s8b-build-cache/` は
再生成可能で退避していない。本文の値・結論は変えない。事故の記録は `output/insights/2026-09-20/cleanup-backup-loss-record/README.md`。
