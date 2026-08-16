# Pegasus env contract 登録用ジョブ資材

このディレクトリは、Pegasus の計算ノードを実測し、certification calibration の provenance を
`output/env/pegasus/` に create-only で残すための資材である。**job body の重い処理はすべて PBS
計算ノードで行い**、ログインノードは投入前確認・qsub・結果確認だけに使う。
**ただし login 側が完全に軽いわけではない** — 例えば `submit_silo_ladder_rung1.sh` は login で
外部 3 repo を clone する (入力量に上限が無く、分類上は `unknown` 相当。§0 の grandfather を見よ)。

手順連鎖は次の 3 段である。

1. login node で submit receipt を作って qsub する
2. compute node job が allocation/build/calibration receipt とログを staging へ作る
3. 確保した計算ノードで `.o<ID>` / `.e<ID>` と staging を final receipt に束縛する
   — **この 3 段目は現在 blocked かつ未実証である。** collector を login で直接実行する従来手順は
   §0 の admission により拒否され、計算ノードで実行する経路の実 artifact はまだ無い (§3)。

## 0. 実行体と admission (機械検査対象)

本 README が言及する `tools/pegasus/` の実行体と、その**手順上の実行 site**、および
`tools/pegasus/admission_registry.json` (正本) の class を次に宣言する。
`tools/check_docs.py` が正本との一致と、本文に現れる実行体がこの表に載っていることを検査する
([T-522])。site は `login-direct` / `qsub-job-body` / `compute-only` の 3 値で、
`login-direct` は class が `local-ok` のときにだけ書ける。

| path | 手順上の実行 site | registry class |
|---|---|---|
| `tools/pegasus/collect_receipt.py` | `compute-only` | `unknown` |
| `tools/pegasus/fetch_third_party.py` | `login-direct` | `local-ok` |
| `tools/pegasus/smoke_probe.sh` | `qsub-job-body` | `dispatch-required` |
| `tools/pegasus/submit_certify.sh` | `login-direct` | `local-ok` |
| `tools/pegasus/submit_floor.sh` | `login-direct` | `local-ok` |

`login-direct` の 3 本のうち実測済みは `fetch_third_party.py` だけで、残る submitter 2 本は
`legacy-admitted (未実測)` である (2026-08-05 のユーザー裁定で grandfather を追認。
[T-520] の測定経路が確定したら実測して昇格するか再裁定する)。詳細は
`docs/pegasus-runbook.md` §7.0。

**実行対象の path を変数や command substitution で組み立ててはならない**
(`tools/pegasus/...` の literal が消えると、検査も hook も対象を認識できなくなる)。

**上の実行体を含む fenced block には、先頭行に site タグを書く。**

```text
# admission-site: <login-direct | qsub-job-body | compute-only>
```

`tools/check_docs.py` は、タグ付き block に現れる実行体の site が宣言表と一致することを検査する。
**この検査が保証しないこと**: 平文 (fence の外) に書かれた手順、basename だけの言及
(`submit_certify.sh` のような書き方)、変数で組み立てた path は、site の一致を検査できない。
規範となる手順は必ずタグ付き block に書く。

途中のファイルは上書きしない。同じ job ID / nonce の再利用、欠落、ID・hash 不一致は非 0 で停止する。

**予約設定 file の所在は `policies/registry_v1.json` が唯一の索引である** (所在 inventory であって、
「その run を支配した設定」の再導出元ではない。正本は D115)。task 固有の予約設定は
`policies/<task>_v1.json` へ置き、registry へ登録する。共有 `policy.json` は複数タスクの committed
evidence が bytes を pin しているので**原則編集しない** — 複数タスクが共有する値
(`project` / `queue` / `nodes` / CPU / 依存 pin / perf 候補) だけがそこに残る。
やむを得ず編集するときは D96 に従い、新しい設計判断と境界テストを同じ変更単位で更新する。
**凍結 evidence の binding は書き換えず**、歴史値として現行 bytes から分離する。
`orchestrator/tests/test_pegasus_policy_registry.py` が `policies/` 直下の閉集合一致、
全 entry の実在・非 symlink・tracked、registry 本体の tracked を検査する。

**silo_ladder_rung1 系** (`silo_ladder_rung1.sh` / `submit_silo_ladder_rung1.sh`) は
[T-139] 劣化梯子 rung 1 の characterization 専用資材で、同じ 3 段連鎖に従う
(correctness → submit → 計測 → collect)。手順と受理条件の正本 =
`orchestrator/campaign/silo_ladder_rung1.py` の CLI と
`output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md`。ability-probe 専用であり
calibration / floor の系列とは独立。third-party 依存 (masstree 等) は submitter が
login で pinned staging する (計算ノードは**直接の外部 network 不可**。HTTP(S) proxy は在るが
git clone / FetchContent / pip が honor するかは未確定 — 訂正済みの事実は runbook §7.1)。

## 1. smoke を 3 配分以上取る

まず、certification の前提を小さい job で確認する。

```bash
# admission-site: qsub-job-body
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
effective clock の許容幅は
`orchestrator/calibrator/effective_clock_policy.py` の単一定数が権威であり、shell から渡さない。

## 2. certification を submit する

smoke 実測では gcc/cmake module は存在しないため、certification は既定環境の system
`gcc` / `g++` / `cmake` を直接使う。job は module 状態を変更せず、実際の `module -t list`
(smoke 時の既定は `intelpython/2022.3.1`) を provenance として receipt に保存する。

投入前に superproject が clean であり、W3 を含む commit が HEAD になっている必要がある。

```bash
# admission-site: login-direct
tools/pegasus/submit_certify.sh
```

この wrapper は `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` の rc と raw output、source
commit、job script SHA-256、queue/project/node/walltime を nonce staging に保存する。その後だけ qsub
を実行し、応答 request ID を `submit-receipt.json` に追加する。job は nonce を受け取り、この receipt
が現れるまで最大 60 秒待ってから source・script・request ID を再照合する。

qsub を実行せず、生成するコマンドだけ確認する場合は `--dry-run` を付ける。

```bash
# admission-site: login-direct
tools/pegasus/submit_certify.sh --dry-run
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
9. 凍結 CLI (`--certify`, `--receipt-json`, `--binary-sha256`) で
   t48 / `skew0p9_rr50_rmw0` calibration を実行する
10. 成功時だけ post-attestation と `job-result.json` を作る

numactl 方針は calibrator が attestation の NUMA node 数から自動導出する (1 node はなし、複数は
interleave-all)。job wrapper から CLI override は渡さない。

予約式は job script 冒頭の C3-7 コメントと receipt に同じ文字列・値で保存する。JSON、receipt、
build/calibration log の唯一コピーは repo の `output/` に置き、`/scr` は source/build/helper の
使い捨てに限る。build cache は使わない。

## 3. 終了後に final receipt を collect する

job 終了後、投入 directory に返った `.o<ID>` / `.e<ID>` を明示して collector を実行する。
argv は `--attempt-dir "output/env/pegasus/calibration/attempts/<PBS_JOBID>"`、
`--job-staging "output/env/pegasus/calibration/job-staging/<PBS_JOBID>"`、
`--stdout "certify_calibration.sh.o<ID>"`、`--stderr "certify_calibration.sh.e<ID>"` である。

**この collector をログインノードで直接実行してはならない。** `tools/pegasus/collect_receipt.py` は
scheduler stderr と JSON を全読みし `rglob` を全件 materialize するため、入力サイズに上限が無く
`docs/pegasus-runbook.md` §7.0 の分類では `unknown` である。registry も `unknown` で、
`hooks/guard_bash.py` は login / suspect で拒否する。**以前この節が書いていた login 直実行の手順は
誤りだった** (F122。規範に忠実だったのは拒否する hook の方である)。

正規経路は `qlogin` / `qsub` で計算ノードを確保し、その中で collector を実行することである
(自動 dispatch の task enum には無いので、確保できなければ**走らせずに止める**)。
**この経路はまだ実 artifact で確認していない** — 実行するのは
入力 cap ([T-482]) と測定経路 ([T-520]) の裁定を踏まえた後になる。

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
# admission-site: login-direct
tools/pegasus/submit_floor.sh --dry-run   # scheduler を一切呼ばない。副作用あり (下記)
tools/pegasus/submit_floor.sh             # 人間が明示的に実行する。内部で qsub する
tools/pegasus/submit_floor.sh --confirm-irreversible-pilot-holdout  # 床値 pilot を実際に走らせる
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
- **床値 pilot の不可逆承認は投入引数で渡す。** `--confirm-irreversible-pilot-holdout` を付けない
  投入では job は driver へ承認 flag を渡さず、driver が pilot を拒否する。承認時は `qsub -v` へ
  `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=<submission nonce>` が載り、job が submission nonce との
  exact 一致を確認してから driver argv へ flag を 1 個足す。値が固定 literal でなく nonce なのは、
  投入者の環境に残った同名変数だけで全投入が承認済みにならないようにするためである。
  設定済みで不一致 (空文字を含む) なら build と driver より前に `submit_binding` で停止する。
  **これは明示 token を要求する運用 gate であって、承認主体の人間性の証明ではない** (D356)。
- **wrapper は driver を固定 `--mode pilot` で起動する** ([T-748] 裁定 (c))。mode を環境変数・argv・
  `eval` から受け取る口は持たない。`job-result.json` には driver rc と `"mode": "pilot"` を記録する。
  **official の受理集合は空のままである** — driver 側の CLI / core による official の二重拒否は
  変更していない。将来 official を開くには wrapper・job-result・失敗文言・guard・手順書を
  改めて変更して**別の source commit と script hash で再投入**する必要があり、
  現行の pilot job をそのまま official と解釈することはできない。
- **pilot の成果物は `eligible_for_refreeze=false` であり、再凍結・oracle・certified の証拠にはできない。**
  測定値としてのみ使う。
- driver が非 zero を返したとき、wrapper は `failure.json` へ
  `pilot floor driver returned nonzero` の記録を試み、同じ rc で終了する。
- **`failure.json` は best-effort であり、存在も内容も保証しない。** 実装は次のとおり。
  - 記録は**最初の失敗 1 件だけ** (`failure_written` guard)。job-result の書込み失敗が先に起きた
    場合、後続の driver 失敗文言は**記録されない**。
  - failure writer 自身が失敗しても、その rc は握られて呼出しは成功扱いになる。
- **既知の穴 (裁定待ち): `job-result.json` の書込みに失敗しても、driver が成功していれば
  wrapper は rc=0 で終わる。**
  **したがって rc だけを見て受理してはならない。** 受理判定では `job-result.json` の実在を確かめる。

## 6. third-party source を取得して worktree へ供給する (2026-08-04 実装、[T-340])

masstree / mimalloc / googletest は CCBench の FetchContent 依存で、計算ノードには network が
無いのでログインノードで取得して渡す。取得先を repo の中に置くと **worktree を畳んだ時点で
実体が消える**ため、cache は repo の外に置く。cache root の機体固有値は
`docs/pegasus-runbook.md` §6 が正本である。

```bash
# admission-site: login-direct
export IZANAGI_PEGASUS_THIRDPARTY_CACHE=<永続 cache root の絶対パス>

python3 tools/pegasus/fetch_third_party.py fetch        # 欠けている source だけ clone (network 要)
python3 tools/pegasus/fetch_third_party.py hydrate      # cache から worktree の staging へ (offline)
python3 tools/pegasus/fetch_third_party.py verify       # cache の 3 本を検査 (offline)
python3 tools/pegasus/fetch_third_party.py verify-deps  # policy の gflags/glog を検査 (offline)
```

- `--cache-root` か `IZANAGI_PEGASUS_THIRDPARTY_CACHE` の**どちらかが必須**。policy から導出しない。
  repo 配下を cache root にすると rc=2 で拒否する。
- `hydrate` は `submit_silo_ladder_rung1.sh` が使う staging path をそのまま埋めるので、submit 側は
  clone 分岐を通らない。**submit 自身の pin/clean 検査はそのまま走る** (2026-08-04 に
  `--prepare-third-party-only` を実走して rc=0 を確認)。
- consumer (`IZANAGI_THIRDPARTY_SOURCE_ROOT`) へ渡してよいのは **`hydrate` の出力 JSON の
  `.source_root`** だけである。`cache_root` は診断用で、`git status` に出ない ignored な
  ビルド生成物を含みうる。
- 既存 clone を fetch / pull しない。pin が変わったら人間が cache を作り直す。
- shallow / alternates / promisor / replace refs / grafts / commondir / config.worktree /
  sparse checkout / assume-unchanged / skip-worktree を fail-closed で拒否する。
- **この CLI は任意の operator preflight であり、取得の権威ではない。** 最終判定は
  `submit_silo_ladder_rung1.sh` と `silo_ladder_rung1.sh` の pin/clean 検査のままで、
  取得経路は submit receipt にも evidence にも値として現れない。
