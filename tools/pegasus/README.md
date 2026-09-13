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

rr95/rr80/rr20/rr5 の certification・計測・collector・登録は、**dev-wave が所有する実行**である。
`rulings` は裁定と tooling の準備・main land を担うだけで、この手順を直接 qsub しない。

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
| `tools/pegasus/p3_s4_loop_pegasus.sh` | `qsub-job-body` | `dispatch-required` |
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

この login-side submitter は dev-wave の実行段から呼び出す。rulings session の手動実行を意味しない。

```bash
# admission-site: login-direct
tools/pegasus/submit_certify.sh --rratio 80   # H1 / rr80
tools/pegasus/submit_certify.sh --rratio 20   # H2 / rr20
tools/pegasus/submit_certify.sh --rratio 95   # read-heavy / rr95
tools/pegasus/submit_certify.sh --rratio 5    # write-heavy / rr5
tools/pegasus/submit_certify.sh --protocol mocc --rratio 50
```

この wrapper は `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` の rc と raw output、source
commit、job script SHA-256、queue/project/node/walltime を nonce staging に保存する。その後だけ qsub
を実行し、応答 request ID、選択した `ycsb_rratio` (5 / 20 / 50 / 80 / 95 の固定 whitelist)、実効 protocol を
`submit-receipt.json` に追加する。job は nonce と同じ workload / protocol binding を受け取り、
この receipt が現れるまで最大 60 秒待ってから source・script・request ID・workload・protocol を
再照合する。

`--rratio` を省略した場合は既存互換の rr50 になる。rr95/rr80/rr20/rr5 の calibration はこの引数を
指定すれば人間が JSON を編集・登録する必要はなく、compute-node job の certification が
既存の schema / acquisition receipt / 自己比較 / create-only publish を通った場合だけ
`output/env/pegasus/calibration/registered/` へ自動登録する。

`--protocol` の受理集合は `silo / mocc / tictoc` ちょうどで、省略時は既存互換の `silo` になる。
`cicada` は、探索軸 `INLINE_VERSION_OPT` と実際の CMake cache 名
`CCBENCH_INLINE_VERSION_OPT_CICADA` が食い違い、汎用名では値が compiler へ届かないため受理しない。
現行の軸名のまま届いていない値を genome として記録しないための除外である。

認定較正は stock を対象とする。D1936 項 6 により、供給されていない BACKOFF_FIXED=-1 の指定と専用
condition gate を取り下げた。現行 CCBench pin に macro が無いため、configure argv にも genome にも
この指定を載せない。silo / mocc / tictoc のいずれにも広げない。

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
   t48 / 選択した `skew0p9_rr{5|20|50|80|95}_rmw0` calibration を実行する
10. 成功時だけ post-attestation を作り、calibrator の成否にかかわらず `job-result.json` を作る

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
tools/pegasus/submit_floor.sh --confirm-official-floor-run   # 床値 official を実際に走らせる
```

- **実投入は `--confirm-official-floor-run` を必須とする** ([T-2324]、方式は D926)。引数が無い
  実投入は、submission staging root の検査・`SUBMISSION_DIR` の作成・payload staging・
  `output/claims` の作成・`qsub` のいずれよりも前に rc=2 で止まる。`--dry-run` は免除する。
- `--repo-root` / `--attempts-root` / `--job-script` の override は `--dry-run` 専用で、実投入では拒否する。
- dry-run でも submission staging と `output/claims` (mode 0700) を作る。副作用ゼロではない。
- **dry-run は third-party payload staging を飛ばすので、緑を投入可能性の証拠にしない。**
  新規 worktree では dry-run が rc=0 でも実投入が
  `floor third-party source root is missing or unsafe` で qsub 前に落ちる。先に §6 の
  `fetch_third_party.py hydrate` で永続 cache から供給する (2026-09-01、2 session が独立に実測)。
- 生成物: `output/env/pegasus/floor/attempts/submissions/<nonce>/` (pre-submit / submit-receipt) と
  `output/env/pegasus/floor/job-staging/<PBS_JOBID>/` (reservation・qstat raw・job-result・failure)。
- scheduler への walltime 要求宣言は job script の `10:00:00` (36000 秒)。policy の
  `floor_walltime_s=36000` は期待値・submit receipt 値で、job は qstat の実効
  `(Per-Req) Elapse Time Limit` との一致を fail-closed で検査する。現行 driver の
  minimum envelope は required 30000 (12-cell subtotal 28200 + shared prebuild 1800) +
  finalize reserve 600 = 30600 秒である。
- job は gflags/glog を pin + clean 検査つきで build し `CMAKE_PREFIX_PATH` を export してから
  driver を起動する。floor driver の build 経路は `-DCMAKE_PREFIX_PATH` を渡さないため、
  この環境変数が依存を渡す唯一の seam である。
- **submit receipt は submission の記録であり、人間性の証明ではない。** 実行者が人間か AI かは
  生成物から区別できない。authorization として扱ってはならない。
- **測定の反復そのものに承認は要らない** (D1124)。性能測定の反復を機械的に拒否する関門は撤去済みで、
  **測定ごとに新しい測定世代を発行して台帳へ追記する**ため同じ cell を何度でも測ってよい。
  official 走行に要るのは D926 の承認束縛だけである。**official の予算承認 (結果を freeze へ
  昇格させる段の閂) は別物で、`output/s8b-freeze-budget-approvals/` が正本** (D1161 / D1398)。
- **承認は submission nonce へ束ねて運ぶ** (D926)。`--confirm-official-floor-run` を渡した実投入は
  `qsub -v` へ `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN=<submission nonce>` を足す。job script は
  `IZANAGI_SUBMISSION_NONCE` との exact 一致を確かめ、一致したときだけ driver argv の末尾へ
  `--confirm-official-floor-run` を 1 個 append する。**設定済みで空文字または不一致なら、
  build と driver より前に `submit_binding` で fail-closed** (それぞれ別の文言)。未設定なら flag を
  渡さず、driver 側の CLI / core が拒否する。承認 env は driver 起動前に export 属性を外すので、
  子 process へ ambient 値として渡らない。
- **この束縛が保証するのは「標準投入経路で、その source commit と script blob を明示承認して
  起動した」までである** (D926)。承認者が人間であること (D356)、raw `qsub`・driver 直接起動・
  Python API 直接呼出しを含む全経路、床値の科学的妥当性は保証しない。
- **wrapper は driver を固定 `--mode official` で起動する** ([T-2324]。D323 の「mode の受け口を
  作らない」は不変)。mode を環境変数・argv・`eval` から受け取る口は持たない。`job-result.json` には
  driver rc と `"mode": "official"` を記録する。**pilot 経路は標準投入から外れた** — pilot API
  そのものは driver 側に残るが、この wrapper からは起動できない。
- **official でも `eligible_for_refreeze` が真になるのは fresh かつ非既定 seam ゼロのときだけである。**
  判定式と 18 名の不適格 seam 集合は変更していない。pilot の成果物は従来どおり
  `eligible_for_refreeze=false` で、再凍結・oracle・certified の証拠にはできない。
- driver が非 zero を返したとき、wrapper は `failure.json` へ
  `official floor driver returned nonzero` の記録を試み、同じ rc で終了する。
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

## 7. P3 段 4 loop の job body を投入する (2026-09-05 実装、[T-2232]。初回投入 2026-09-07 job `981655.nqsv` は masstree 事前構築の `Could NOT find gflags` で停止し、[T-2406] で gflags/glog の供給経路を足した)

`tools/pegasus/p3_s4_loop_pegasus.sh` は親が直接 `qsub` する compute-only の job body であり、
投入器ではない (A-1 `paper_story_a1_paired.sh` と同じ型)。job body の義務は次のとおりで、
契約は `orchestrator/tests/test_p3_s4_loop_job_contract.py` が固定する。

- `bnode` 以外の host、必須環境変数の欠落、repo 内の evidence root、`.claude/worktrees/` /
  `.codex/worktrees/` 配下の checkout は rc=2 で拒否する
- `python3.10` を解決し、`python3` → 3.10 の shim (interpreter のみ) を PATH 先頭に置く。
  `cmake` / compiler の wrapper・launcher は置かない (F813、D1517)
- `tools/pegasus/policy.json` の pin (`gflags_source_path` / `gflags_expected_head` /
  `glog_source_path` / `glog_expected_head`) に exact 一致し clean な gflags / glog を `$TMPDIR`
  (job 別 scratch) へ configure / build / install し、この 2 install prefix だけを
  `CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` として masstree 事前構築の前から
  driver 本走まで保持する (`floor_scoping.sh` の prologue の移植、D1773)。事前構築の
  `configure_argv` にも同じ 2 prefix を `-DCMAKE_PREFIX_PATH=` で残す。別の provenance file は
  作らない。契約テストはこの exact 1 行以外の `CMAKE_PREFIX_PATH` 代入と、export 後の unset を拒否する
- expected HEAD、superproject の tracked clean (submodule 除外)、CCBench の `p3_s4_loop.PIN` 一致を検査する
- `qstat -f` から reservation 束縛 (`IZANAGI_RESERVATION_*`) を組み、`<REPO_ROOT>/output/env/pegasus/claims`
  を provisioning する
- hydrate 済み third-party source 3 本を `/scr` の scratch へ `<base>/<name>-src` の形で複製し、
  masstree の `config.h` を `buildcache.prepare_masstree_fetchcontent` で事前構築して receipt に
  束縛する。`-src` の配置と base の一致は選択ではない — `buildcache` は dependency receipt 付き
  build で実効 masstree source root が `<base>/masstree-src` と exact 一致することを要求する
- driver はこの receipt を `--fetchcontent-prebuild-receipt` で受け取り、base・source dir 3 本・
  `{masstree_head, config_sha256}` の 2 key receipt を共有 measurement pipeline
  (`run_campaign` → `pipeline.evaluate` → `buildcache.build_v2`) へ通す。configure には
  `-DFETCHCONTENT_BASE_DIR=` と `-DFETCHCONTENT_SOURCE_DIR_*` が入る (T-2356、D1524 / D1689)
- K2 走行では `IZANAGI_S4_KNOWLEDGE_MANIFEST` と `IZANAGI_S4_CODER_ROLE` を all-or-none の
  非空対とし、`IZANAGI_S4_PROPOSAL_PATH` も必須とする。どちらか一方だけ、設定済み空値、または
  proposal path 欠落は repository path 解決と `trap` より前に rc=2 で拒否し、
  `compute-result.json` を作らない
- `IZANAGI_S4_KNOWLEDGE_CLASSIFICATION` と `IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM` は任意で、
  設定時だけ非空を要求して転送する。shell は role・classification・de novo の値域を複製せず、
  driver の CLI・parser・K2 consumer を最終判定とする
- `p3_s4_loop` を `--allow-coder-derived-build --isolate-worktree
  --fetchcontent-prebuild-receipt <EVIDENCE_ROOT>/masstree-prebuild-receipt.json` で起動する。
  `IZANAGI_S4_PROPOSAL_PATH` があれば `--run-iteration`、無ければ fixture `--value`。K2 の
  `--knowledge-manifest` / `--coder-role` と、設定された場合だけの
  `--knowledge-classification` / `--knowledge-de-novo-claim` は proposal 分岐だけへ渡す。
  K2 env 未設定時は proposal-only と fixture の既存 argv を変えない

投入は login node から次の形で行う。`REPO_ROOT` は固定 SHA の専用 checkout (primary worktree や
`.claude/worktrees/` 配下は不可)、`THIRDPARTY_SOURCE_ROOT` は §6 の `hydrate` 出力 JSON の
`.source_root`、`EVIDENCE_ROOT` はどの repository の配下でもない場所とする。同じ attempt directory は
再利用しない。`-o` / `-e` を省くと標準出力・標準エラーが投入時 directory へ落ちて作業ツリーを汚す。

```bash
# admission-site: qsub-job-body
REPO_ROOT=/absolute/path/to/dedicated-checkout
EXPECTED_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD)
THIRDPARTY_SOURCE_ROOT=/absolute/path/from-hydrate-source_root
EVIDENCE_ROOT=/absolute/path/outside-all-repositories
ATTEMPT=unique-attempt-id
PROPOSAL_PATH=/absolute/path/to/proposal.json
KNOWLEDGE_MANIFEST=/absolute/path/to/knowledge-manifest.json
CODER_ROLE=coder-v4-autonomous-k2
KNOWLEDGE_CLASSIFICATION=reproduction_or_selection
KNOWLEDGE_DE_NOVO_CLAIM=false
mkdir -m 0700 "$EVIDENCE_ROOT/$ATTEMPT"
qsub -v IZANAGI_S4_REPO_ROOT="$REPO_ROOT",IZANAGI_S4_EXPECTED_HEAD="$EXPECTED_HEAD",IZANAGI_S4_EVIDENCE_ROOT="$EVIDENCE_ROOT/$ATTEMPT",IZANAGI_S4_THIRDPARTY_SOURCE_ROOT="$THIRDPARTY_SOURCE_ROOT",IZANAGI_S4_PROPOSAL_PATH="$PROPOSAL_PATH",IZANAGI_S4_KNOWLEDGE_MANIFEST="$KNOWLEDGE_MANIFEST",IZANAGI_S4_CODER_ROLE="$CODER_ROLE",IZANAGI_S4_KNOWLEDGE_CLASSIFICATION="$KNOWLEDGE_CLASSIFICATION",IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM="$KNOWLEDGE_DE_NOVO_CLAIM" -o "$EVIDENCE_ROOT/$ATTEMPT/job.stdout" -e "$EVIDENCE_ROOT/$ATTEMPT/job.stderr" tools/pegasus/p3_s4_loop_pegasus.sh
```

上の fence は任意の宣言 2 値も明示した K2 正例である。driver の既定を使う場合は
`IZANAGI_S4_KNOWLEDGE_CLASSIFICATION` と `IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM` を `-v` から
両方または個別に省ける。非 K2 proposal は proposal path だけを足し、fixture 経路は proposal path と
K2 env をすべて省く。fixture は `IZANAGI_S4_FIXTURE_VALUE` 無指定時に 20 を使う。

**同じ `REPO_ROOT` へ同じ fixture 値で 2 度目を投入すると、事前構築は消費されない。** campaign WAL に
同じ variant の terminal record が既にあると `run_campaign` は build より前に skip するので、receipt を
渡しても configure まで到達しない。事前構築を実際に通す走行には、まだ terminal になっていない候補
(別の fixture 値、または別 campaign) が要る。塞ぐには campaign identity か duplicate の意味論を
変える必要があり、裁定待ちである (T-2356)。

**実測済みと未実測の境界。** 初回投入 (2026-09-07、job `981655.nqsv`、固定 SHA の専用 checkout から
投入) で、host gate・環境 sanitize・`python3.10` shim・reservation 束縛・claim root・third-party
複製までは通り、masstree 事前構築の configure で止まった (一次資料は
`output/insights/2026-09-07_t2232-s4-loop-first-dispatch/README.md`)。gflags/glog prologue 以後
(prologue 自体の build 時間、事前構築 receipt を通した build の成立、attestation の exact 照合、
walltime 03:00:00 の充足) は未実測である。`compute-result.json` の `driver_rc` は driver だけでなく
job body 全体の終了 rc であり、prologue や事前構築で止まった場合もその生の rc (timeout なら 124)
が入る。seam は login node の probe で「production `_v2_commands` の configure argv まで
5 値が届く」ところまで確認した (`output/insights/2026-09-05_t2232-s4-loop-pegasus-job-script/README.md`)。
