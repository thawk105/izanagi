# T-1403: walltime 打ち切りで NQSV が SIGTERM を配送する構成を実測した

## 発見

`elapstim_req="max,warn"` (warn < max) + `--warning-signal=elapstim:SIGTERM` +
`--accept-sigterm=yes` の "mitigation leg" (D139 決定4 で存在が未実測とされていた構成) を
実際に計算ノードで走らせたところ、**NQSV は SIGKILL ではなく SIGTERM を配送した。**

D139 (2026-08-04) が実測した既定構成 (`--accept-sigterm` 省略、`elapstim_req` に警告値なし) では
walltime 超過時に SIGKILL が直送され、grace は無かった (3 層とも受信ゼロ)。今回の mitigation leg
構成ではこれと異なり、warn 境界で SIGTERM が配送され、probe の signal handler がこれを実際に
catch して正常終了した。

## 再現条件

- 環境: Pegasus `gen_S`、`pegasus02` login node から `qsub` で直接投入 (dispatch_compute.py 経由ではない)。
- request: `927684.nqsv`、2026-08-20 23:43:21 JST 開始、23:45:26 JST 終了。
- PBS directive (`tools/pegasus/probes/t1403_walltime_sigterm_probe.pbs`):
  ```
  #PBS -A SFC
  #PBS -q gen_S
  #PBS -b 1
  #PBS -l elapstim_req="00:03:00,00:02:00"
  #PBS --warning-signal=elapstim:SIGTERM
  #PBS --accept-sigterm=yes
  ```
  (max=180s, warn=120s、workload は `time.sleep(360)` — max を確実に超える)
- probe 本体: `tools/pegasus/probes/t1403_walltime_sigterm_probe.py` (`run_workload`)。
  SIGTERM handler は受信直後に off-repo checkpoint (JSONL、O_APPEND+fsync 相当の durable write) を
  書いてから正常終了する。

## 実測値

- NQSV 自身のログ (job stderr):
  `%NQSV(INFO): Batch job received signal SIGTERM. (Exceeded per-req elapse time limit)`
  `Elapse: 129S` / `Remaining Elapse: 51S` (max=180S に対して 129+51=180 で符合)。
- probe 自身の checkpoint (`checkpoint.jsonl`):
  `sigterm_received_at` は job 開始から **119.03 秒** (warn 境界 120s の約 0.97 秒前 — job 内部時計と
  NQSV 会計の起点差はおそらく bash prologue の分)。
- probe 自身の最終 stdout JSON: SIGTERM 受信から **約 1.6 ミリ秒後**に正常終了 (`clean_exit_at`)。
- `reconcile_observation` + `compute_verdict` (テスト済み純関数、
  `tools/pegasus/probes/t1403_walltime_sigterm_probe.py`) による最終 verdict:
  **`SIGTERM_CAUGHT_CLEAN_EXIT`、`grace_seconds=9.97`**
  (NQSV 会計の `Elapse=129S` を clean-exit の代理値として使うため、probe 自身の 1.6ms より大きい —
  scheduler 側の job 終端・会計確定オーバーヘッドを含む値。両方の数値をここに残す)。
- final receipt: `/work/1/SFC/tanab/izanagi-job-evidence/pegasus/0:927684.nqsv/t1403-walltime-sigterm/final-receipt.json`
  (repo 外、D546 決定3/4 の診断書込み off-repo 方針を踏襲)。

## 該当コード

- `tools/pegasus/probes/t1403_walltime_sigterm_probe.pbs` (PBS directive、workload)
- `tools/pegasus/probes/t1403_walltime_sigterm_probe.py`
  (`run_workload`, `reconcile_observation`, `compute_verdict`, `parse_nqsv_output`)

## D139 / D546 との関係

- D139 決定4「捕捉可能な構成の有無は未解決である」を実測で解決した。mitigation leg は実在し、
  実際に catch 可能な SIGTERM を配送する。
- D546 決定2「`--accept-sigterm=yes` 単独では walltime 打ち切りで SIGTERM が送られる保証にならない
  ...実測するまで結論しない」に対する回答: **`--accept-sigterm=yes` 単独 (現行 `floor_campaign.sh`
  の構成) では未実測のまま。** 今回実測したのは `elapstim_req="max,warn"` +
  `--warning-signal=elapstim:SIGTERM` を**追加**した構成であり、`floor_campaign.sh` の現行構成
  そのものではない。詳細は decisions.md の新規決定 (このwaveのworklogが参照する) を参照。

## 射程の限定

- 測定した exact host (`bnode` 番号は job stdout に記録が無く未確認)・queue (`gen_S`)・
  当日の kernel/NQSV version に限る。D140 と同様、gen_S 全体・他 queue へ一般化しない。
- 試行 1 回のみ。D139 は同種の測定を複数回行っていない一方、今回も単発である。反復測定・
  分散 (grace の variance) は本 wave の scope 外。
- floor_campaign.sh・dispatch_compute.py の production 設定は変更していない (本 wave の不変条件)。
  この構成を実際に production へ適用するかは別途裁定が要る。

## 還元判断

CCBench 還元は非該当 (NQSV/Pegasus scheduler の挙動であり CCBench 本体と無関係)。
izanagi 自身のインフラ知見として `docs/decisions.md` の新規決定に格上げする。
