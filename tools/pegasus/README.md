# Pegasus env contract 登録用ジョブ資材

このディレクトリは、Pegasus の計算ノードを実測し、certification calibration の provenance を
`output/env/pegasus/` に create-only で残すための資材である。重い処理はすべて PBS 計算ノードで
行い、ログインノードは投入前確認・qsub・終了後収集だけに使う。

手順連鎖は次の 3 段で固定する。

1. login node で submit receipt を作って qsub する
2. compute node job が allocation/build/calibration receipt とログを staging へ作る
3. login node で `.o<ID>` / `.e<ID>` と staging を final receipt に束縛する

途中のファイルは上書きしない。同じ job ID / nonce の再利用、欠落、ID・hash 不一致は非 0 で停止する。

**silo_ladder_rung1 系** (`silo_ladder_rung1.sh` / `submit_silo_ladder_rung1.sh`) は
[T-139] 劣化梯子 rung 1 の characterization 専用資材で、同じ 3 段連鎖に従う
(correctness → submit → 計測 → collect)。手順と受理条件の正本 =
`orchestrator/campaign/silo_ladder_rung1.py` の CLI と
`output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md`。ability-probe 専用であり
calibration / floor の系列とは独立。third-party 依存 (masstree 等) は submitter が
login で pinned staging する (計算ノードは外部 network 不可 — runbook §7.1)。

## 1. smoke を 3 配分以上取る

まず、certification の前提を小さい job で確認する。

```bash
cd /path/to/izanagi
qsub tools/pegasus/smoke_probe.sh
```

結果は job ごとに次へ保存される。

```text
output/env/pegasus/smoke/<PBS_JOBID>/
```

少なくとも 3 配分を取り、各 directory の `manifest.json` と次を確認する。

- `qstat_job.*`: 計算ノードから先頭の subrequest index `0:` を除いた ID で `qstat -f` が使えるか。rc と raw stdout/stderr
- `qstat_jobs.*` / `qstat_all_detail.*`: 同一 host の他 allocation を scheduler 情報から照会できるか
- `qstat_queue_detail.*`: `gen_S` の walltime 上限を含む queue 詳細が取得できるか
- `module_list.*` / `module_avail.*`: module の出力 stream と exact version 名
- `toolchain_which.*` / `toolchain_versions.*` / `toolchain_realpaths.*`: system gcc/g++/cmake の lookup、version 先頭行、実体 path
- `proc_*` / `proc2_comm.*`: `/proc` の mount options、hidepid、host PID namespace 指標 (`kthreadd`)。
  `/proc/2/comm` は namespace 内 process が comm を詐称できるため暗号学的な証明ではなく、
  reservation・単独性検査と組み合わせる運用指標である
- `numactl_hardware.*` / `lscpu.*` / `cpuinfo.*`: NUMA・CPU topology の全文
- `observation.json`: `env_attestation.probe()` の構造化観測
- `loadavg.*` / `pressure_*` / `process_overview.*`: load・PSI・稼働 process 概況
- `scratch.*`: `/scr` の存在・書込 canary と job 開始時の `TMPDIR`

`qstat -f` の assigned host / scheduler start field、qsub 応答 ID と raw `$PBS_JOBID` の表記、他 job の
同一 host 照会可否は実機でしか確定できない。いずれかを確定できなければ certification を投入しない。
3 配分の effective clock 分布から tolerance を親が凍結し、次段へ数値で渡す。

## 2. certification を submit する

smoke 実測では gcc/cmake module は存在しないため、certification は既定環境の system
`gcc` / `g++` / `cmake` を直接使う。job は module 状態を変更せず、実際の `module -t list`
(smoke 時の既定は `intelpython/2022.3.1`) を provenance として receipt に保存する。

投入前に superproject が clean であり、W3 を含む commit が HEAD になっている必要がある。

```bash
tools/pegasus/submit_certify.sh \
  --effective-clock-tolerance-pct '<3配分から凍結した値>'
```

この wrapper は `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` の rc と raw output、source
commit、job script SHA-256、queue/project/node/walltime を nonce staging に保存する。その後だけ qsub
を実行し、応答 request ID を `submit-receipt.json` に追加する。job は nonce を受け取り、この receipt
が現れるまで最大 60 秒待ってから source・script・request ID を再照合する。

qsub を実行せず、生成するコマンドだけ確認する場合は `--dry-run` を付ける。

```bash
tools/pegasus/submit_certify.sh \
  --effective-clock-tolerance-pct '<凍結値>' \
  --dry-run
```

certification job は 1 node・2 時間で、次の順に fail-closed で進む。

1. `TMPDIR=/scr/$PBS_JOBID` を create-only で作る
2. qstat assigned host、hostname、cpuset、HT、reservation binding を保存する
3. build 前の静的 attestation を取る
4. 既定 module list を記録し、system compiler/cmake の実体・version を保存する
5. CCBench の superproject gitlink・HEAD・tracked-clean を照合する
6. `/scr` の detached worktree と fresh build directory で trace-disabled binary を作る
7. binary SHA-256 と build argv を保存し、build 子孫終了を確認する
8. build 後 profile と W0 exact `AcquisitionReceipt` を作り、calibrator 内の凍結 cooldown と
   dynamic pre-attestation を fatal gate として通す
9. 凍結 CLI (`--certify`, `--receipt-json`, `--binary-sha256`,
   `--effective-clock-tolerance-pct`) で t48 / `skew0p9_rr50_rmw0` calibration を実行する
10. 成功時だけ post-attestation と `job-result.json` を作る

numactl 方針は calibrator が attestation の NUMA node 数から自動導出する (1 node はなし、複数は
interleave-all)。job wrapper から CLI override は渡さない。

予約式は job script 冒頭の C3-7 コメントと receipt に同じ文字列・値で保存する。JSON、receipt、
build/calibration log の唯一コピーは repo の `output/` に置き、`/scr` は source/build/helper の
使い捨てに限る。build cache は使わない。

## 3. 終了後に final receipt を collect する

job 終了後、ログインノードの投入 directory に返った `.o<ID>` / `.e<ID>` を明示して collector を
実行する。

```bash
python3 tools/pegasus/collect_receipt.py \
  --attempt-dir "output/env/pegasus/calibration/attempts/<PBS_JOBID>" \
  --job-staging "output/env/pegasus/calibration/job-staging/<PBS_JOBID>" \
  --stdout "certify_calibration.sh.o<ID>" \
  --stderr "certify_calibration.sh.e<ID>"
```

`attempts/<PBS_JOBID>` は calibrator 自身の create-only namespace、`job-staging/<PBS_JOBID>` は PBS
wrapper の allocation/build/log namespace である。collector は submit receipt、allocation receipt、job result の job ID を相互照合し、両 staging の全 file と
scheduler stdout/stderr の size・SHA-256、stderr 内の NQSV 会計 summary 生行を
`final-receipt.json` へ create-only で束縛する。stderr は module や会計情報を含み得るため、空である
ことを成功条件にしない。必要ファイル、会計 summary、ID のいずれかが欠ければ final receipt を作らず
非 0 で終了する。

final receipt ができても calibration の採用を意味しない。`quality.status=accepted`、全 rep、単独性、
pre/post attestation、CV 等の C3 検収を親が行い、1 項でも欠ければ別 allocation で attempt 全体を
取り直す。rejected attempt のファイルを修正・上書きして再利用しない。

## 4. floor / oracle 実走前の durable claim と reservation

required-mode の floor / oracle job は、承認済み durable `out_root` の直下に `claims/` を
**投入前に** mode 0700 で作成する。driver はこの directory を作らず、欠落・symlink・非 directory
なら claim/WAL/marker より前に fail-closed で停止する。floor と oracle の双方が同じ規則を使う。
複数 clone/worktree を跨ぐ排他を必要とする oracle job は、clone 間で同一 `out_root` を共有する。

さらに PBS wrapper は job 内で次の値を `IZANAGI_RESERVATION_*` として export してから driver を
起動する。値は scheduler receipt と同じ raw reservation に由来し、driver の要求秒数に合わせて
その場で作り直さない。

- `JOB_ID`, `REQUESTED_S`, `SCHEDULER_STARTED_EPOCH`, `DEADLINE_EPOCH`
- `HOST`, `BOOT_ID`, `SCRIPT_SHA256`, `NONCE`
- 現在の raw job identity として `PBS_JOBID`

floor job ではセル数・schedule・build/verify cap から導出した `required_s` と finalize margin を
journal の `reservation-preflight` に記録する。oracle job も凍結済み最大 attempt envelope を各行前に
monotonic 再検査する。

## 5. floor 専用 wrapper (2026-07-25 実装、実 artifact 未確認)

`submit_floor.sh` (ログインノード) と `floor_campaign.sh` (計算ノード) が floor 実走の資材である。
`submit_certify.sh` / `certify_calibration.sh` と同型で、移植ブロックには出典コメントを付けている。
`collect_receipt.py` は calibration 固有の入力を必須とするため floor では使わない。

```bash
tools/pegasus/submit_floor.sh --dry-run   # scheduler を一切呼ばない。副作用あり (下記)
tools/pegasus/submit_floor.sh             # 人間が明示的に実行する。内部で qsub する
```

- `--repo-root` / `--attempts-root` / `--job-script` の override は `--dry-run` 専用で、実投入では拒否する。
- dry-run でも submission staging と `output/claims` (mode 0700) を作る。副作用ゼロではない。
- 生成物: `output/env/pegasus/floor/attempts/submissions/<nonce>/` (pre-submit / submit-receipt) と
  `output/env/pegasus/floor/job-staging/<PBS_JOBID>/` (reservation・qstat raw・job-result・failure)。
- walltime は policy の `floor_walltime_s` (36000 = 10:00:00)。driver が導出する envelope
  (required 28200 + finalize 600 = 28800) を上回る値であり、job は qstat の
  `(Per-Req) Elapse Time Limit` と policy の一致を fail-closed で検査する。
- job は gflags/glog を pin + clean 検査つきで build し `CMAKE_PREFIX_PATH` を export してから
  driver を起動する。floor driver の build 経路は `-DCMAKE_PREFIX_PATH` を渡さないため、
  この環境変数が依存を渡す唯一の seam である。
- **submit receipt は submission の記録であり、人間性の証明ではない。** 実行者が人間か AI かは
  生成物から区別できない。authorization として扱ってはならない。
- **現時点では driver が official guard により必ず rc=2 で拒否する。** wrapper はこの rc を
  `job-result.json` と `failure.json` に忠実に記録し、同じ rc で終了する。成功と偽らない。
