# [T-088] 段階 1 floor 専用 PBS wrapper — 逐語 (2026-07-25)

本 wave の子エージェント出力の逐語。実行環境 = `codex exec -m gpt-5.6-sol`、
プラン/相談/レビューは `model_reasoning_effort=max` + `-s read-only`、
実装/fix は `model_reasoning_effort=high` + `-s workspace-write`。
親 (claude-opus-5) の brief・裁定・変異台帳は材料レポート `2026-07-25_t088-floor-wrapper.md` を正本とする。

---

## brief

# 段 1 brief — [T-088] 段階 1: floor 専用 PBS wrapper (wrapper-only wave)

基準 commit: `e9b6f69` / worktree branch: `worktree-dev-wave-t088-floor-wrapper`
正本: D86 (decisions.md) と `output/insights/2026-07-25_t088-official-unlock-design.md` §4。

## scope
D86(2) の順序「wrapper-only wave 先行 → 実 artifact 確認 → admission 再裁定」の**第 1 段だけ**を実装する。
成果は (a) login node 用 floor submit wrapper、(b) PBS floor job script、(c) その静的・dry-run テスト、
(d) `tools/pegasus/README.md` の floor 節。admission predicate と CLI 固定拒否は**本 wave では触らない**。

## 確定済みユーザー裁定 (D86)
U-1 承認 (guard を期限つき activation lock と再分類) / U-2=(a) wrapper 先行 / U-3=(a) 明示 `qsub` +
job-scoped submission artifact・**新 Git receipt を作らない** / U-4 一括延期 (selector helper 抽出、
certificate v2、ratified 追加、resume authorization、private permit + AST pin、完全 negative matrix)。

## 防壁変更の再確認 (D86(1) の義務、本 brief で履行)
本 wave は `_assert_official_permitted` と CLI 拒否の bytes を 1 行も変えない。したがって official の
受理集合は**空集合のまま**であり、規律 2 に対する変更は発生しない。再分類の実装は次 wave に属する。

## 不変条件
- I1: `orchestrator/campaign/s8b_floor_campaign.py` を編集しない (guard・CLI・core とも)。
- I2: 凍結 bytes 不変 (`FROZEN_MANIFEST` 23 件はすべて `output/`、`tools/` の pin は 0 件 — 実測済み)。
- I3: **環境変数同士の一致を authorization gate に数えない** (D86 設計制約)。wrapper は
  `IZANAGI_RESERVATION_*` を export するが、本 wave では gate を新設しない。
- I4: 新しい Git receipt・新しい commit 型 attestation を作らない (U-3(a))。
- I5: **AI は qsub を実行しない**。人間の明示 `qsub` が authorization そのものであるため。
  AI の検証は `--dry-run` と静的検査までとする。
- I6: 既存 `submit_certify.sh` / `certify_calibration.sh` / `smoke_probe.sh` の挙動を変えない。
- I7: driver は `claims/` を作らない (`s8b_floor_campaign.py:2823-2829`) ため、投入前 provisioning は
  wrapper 側の責務とする。

## 成果物の形
1. `tools/pegasus/submit_floor.sh` — `submit_certify.sh` 同型: policy 読み → HEAD 40hex + tracked-clean →
   job script sha256 → nonce → create-only submission staging → 4 preflight capture
   (`qstat -Q`/`pegasusinfo`/`rbudgetcheck`/`check_quota`) → `claims/` provisioning → `qsub` (または
   `--dry-run`) → `pre-submit.json` + `submit-receipt.json`。
2. `tools/pegasus/floor_campaign.sh` — `certify_calibration.sh` 同型の PBS job script:
   PBS directives + 予約式コメント → `TMPDIR=/scr/$PBS_JOBID` create-only → job staging create-only →
   nonce/submit-receipt 束縛 (最大 60 秒待ち) → source commit・clean・script blob 再照合 →
   qstat 由来 assigned host / scheduler start → `IZANAGI_RESERVATION_*` 8 値 export →
   floor driver 起動 (`--mode official --protocol output/s8b-freeze/floor_protocol.json`) →
   rc と結果を `job-result.json` に忠実記録。
3. テスト — 新規 `orchestrator/tests/test_pegasus_floor_tools.py` (既存 `test_pegasus_tools.py` は不変)。
4. `tools/pegasus/README.md` に floor 節を追加。

## 親の provisional 裁定 (すべて攻撃対象)
- (P1) scope は上記 4 点。admission・CLI・certificate・ratified・resume は次 wave。
- (P2) 本 wave の完了判定は「wrapper path 実在 + `--dry-run` で submission artifact が生成される」まで。
  実 job ID を伴う DW-G04 発火条件充足は**人間 qsub 後**であり、次 wave の入口条件として繰り越す。
- (P3) submission artifact は `output/env/pegasus/floor/attempts/submissions/<nonce>/` に置き、schema は
  `pegasus-floor-pre-submit/v1` / `pegasus-floor-submit-receipt/v1` として calibration v1 と分ける。
- (P4) job script は driver を `--mode official` で起動する。現時点では guard により rc≠0 で落ちるのが
  期待挙動であり、job script は rc を偽らず `job-result.json` に記録して非 0 終了する。
- (P5) `policy.json` に `floor_walltime`/`floor_walltime_s` を追加する。既存 key は不変。
- (P6) `claims/` provisioning は `submit_floor.sh` が `output/claims` を mode 0700 で作る
  (既存なら symlink でない directory かつ mode を検査するだけ)。
- (P7) 実装子は 2 本: A = login 側 (`submit_floor.sh` + `policy.json` + 新規テストファイル)、
  B = job 側 (`floor_campaign.sh`)。README は親が段 7 で書く (子は docs 編集禁止)。
- (P8) reservation の `REQUESTED_S` は policy の floor walltime、`SCHEDULER_STARTED_EPOCH`/host は
  qstat 由来とし (`certify_calibration.sh:320-337` 同型)、driver の要求秒数に合わせて作り直さない。

## 前提実測 (一次資料、模擬でない)
- `--mode official` 実行 → `{"status":"refused"}` rc=2 (CLI 拒否が生存)。core guard は `:193-203` に現存。
- `output/claims/` 未存在。`FROZEN_MANIFEST` に `tools/` の pin なし。
- baseline `pytest orchestrator/tests/test_pegasus_tools.py` = 52 passed。
- 何も模擬していない (guard の実削除は本 wave の scope 外であり、実施していない)。

---

## ruling-v2

# 段 4 裁定 + プラン v2 (親) — [T-088] 段階 1 wrapper-only wave

両レンズ NO-GO (A: BLOCKER 7 + MUST 5 / B: BLOCKER 2 + MUST 6 + SHOULD 3)。
**実装は行う**が、scope・完了条件・walltime・所有分割・防壁の呼称を改訂する。
この文書が段 5 実装子への **interface pin** であり、plan.md より優先する。

---

## 0. 最重要の改訂 — 完了条件 (A-05 / B-01 を採用、P2 を否定)

**本 wave は「[T-088] 段階 1 完了」を主張しない。** dry-run の synthetic ID は DW-G04 の
発火条件ではない。本 wave の成果は「wrapper と job script の実装 + 静的/動的検査」までであり、
段階 1 は **人間が実 `qsub` を実行し `dry_run:false` の実 job ID を確認するまで OPEN** とする。
worklog・README には「実装済み・実 artifact 未確認」と分けて書く (B-13)。

## 1. 所見の裁定

### 採用して本 wave で実装する (scope 内)

| ID | 裁定 | 実装する対処 |
|---|---|---|
| A-05 / B-01 | real・採用 | §0。完了条件の改訂。dry-run を完了根拠にしない |
| A-02 | real・**部分採用** | job が **実行中の bytes** を `sha256sum "$0"` で hash し、receipt の `job_script_sha256` と一致を要求する。repo blob の hash とも二重照合。scheduler 側 record との独立取得は段階 3 へ |
| A-03 | real・採用 | driver を `python3 -E -s -B` で起動し、`PYTHONPATH`/`PYTHONHOME`/`PYTHONSTARTUP` を unset。interpreter の realpath と `--version` を job-staging に記録。**親が実測済み** (`-E -s -B` でも rc=2 拒否が正常動作) |
| A-07 / P8 | real・採用 | `REQUESTED_S` の出所を **policy 自己申告から scheduler 実値へ変える**。qstat の `(Per-Req) Elapse Time Limit = Max: <N>S` を parse し、policy の `floor_walltime_s` と一致しなければ fail-closed。`Remaining Elapse` も記録する (両 field は実 job 成果物 `job-staging/0:867874.nqsv/qstat-f.stdout:57,74` に実在 — 親が確認) |
| A-09 | real・採用 | staging・claims の **全 path component** を symlink 検査し、`realpath` が repo `output/` 配下であることを要求。raw capture も truncate でなく create-only にする |
| A-01 | real・**縮小採用** | 非 dry-run では `--repo-root` / `--attempts-root` / `--job-script` の override を**拒否**し、script 自身の `../..` に固定する。「承認済み revision 束縛」本体は既裁定の別 gate (worklog 次の一手 2「実行 revision 束縛」) であり scope 外 |
| A-04 | real・**記録で対処** | submission record を **authorization と呼ばない**。schema key・README・worklog で「これは submission 記録であり人間性の証明ではない」と明記する。D86(3) の文言がこの限界より強い点は §5 の裁定パッケージへ (親は D86 を独断で書き換えない) |
| A-10 | real・採用 | receipt の `job_id` と実 `$PBS_JOBID` の normalized 一致を必須化 (古い receipt の replay 遮断) |
| A-11 | real・採用 | **最終 exit rc は driver rc とする**。record writer の失敗が rc を上書きしてはならない。writer 失敗は別 stage の failure として記録する |
| B-02 | real・**部分採用** | walltime を **36000 s (10:00:00)** へ引き上げる (§2)。driver 定数が hard cap でない件は I1 により本 wave で直せない → §5 の次の一手へ |
| B-10 | real・採用 | 一時 repo での動的 dry-run テスト、sentinel stub (呼ばれたら検出)、実 qstat fixture、stub driver の rc 0/2/7 伝播テスト |
| B-09 | real・採用 | 意図的重複を許容。移植した各ブロックの先頭に**出典コメント** (`certify_calibration.sh:<行範囲> @ e9b6f69`) を必ず置く |
| B-11 / P7 | real・採用 | 所有分割を **逐次 B → A** に改める (§4) |
| **親独自** | real・採用 | **gflags/glog 依存 build と `CMAKE_PREFIX_PATH` export を job script に含める** (§3) |

### scope 外 (real だが本 wave では実装しない)

- **A-01 本体** (承認済み revision への束縛) — 既裁定の別 gate。
- **A-02 残余** (scheduler spool bytes の独立取得) — 設計正本 §4 の admission 制約。段階 3。
- **A-06 一般** (自己整合検査の一掃) — 本 wave では「gate と呼ばない」記録対処に留める。
- **A-12** (production consumer 層での発火) — 現 CLI が rc=2 で止まる以上、段階 3 でしか発火しない。
- **B-02 の driver 定数修正** — `s8b_floor_campaign.py` の編集は I1 違反。独立 prerequisite wave。
- **B-04** (予算換算) — 閾値判定は入れず `rbudgetcheck` の raw を記録するだけ。人間が qsub 前に判断。
- floor 専用 final receipt collector (B-08)、共通 module 化、汎用 schema。

### 訂正 (親の記述の過大主張)

- **A-08 を受けて親 brief の表現を訂正する**: 「28800 秒ちょうどでは**必ず**落ちる」は厳密には偽で、
  `reservation.py` の判定は strict `>` のため `Δ=0` なら通る。実運用では receipt 待ち・qstat・git・
  hash 処理で必ず `Δ>0` になるため結論 (28800 では不足) は維持するが、「必ず」は撤回する。

## 2. walltime の確定値 (P5 を否定して改訂)

**`floor_walltime_s = 36000` / `floor_walltime = "10:00:00"`。**

```text
driver required_s                    = 12 * (900 + (8+2) * (5*5 + 120)) = 28200
driver finalize reserve              =   600
driver が要求する capacity           = 28800
job prologue (gflags/glog build・qstat・git・hash) 見積          ≈  900
driver 定数が hard cap でないことへの余裕 (B-02)                 ≈ 6300
PBS request                          = 36000  (= 10:00:00, gen_S 上限 86400 の範囲内)
```

A-08 の中間再検査式 `reservation-lost iff E > REQUESTED_S - 600 - 145*(P+U)` に代入すると、
初回測定前 (P+U=120) の許容経過は `36000 - 600 - 17400 = 18000 s`。build cap 合計 10800 s に対し
7200 s の余裕がある (29400 案では 600 s しかなかった)。

## 3. 親独自の BLOCKER — build 依存 (両レンズとも未検出)

**事実 (親が実測)**: floor driver は 12 セルを `buildcache.build_v2` で build する
(`s8b_floor_campaign.py:962-981`)。その configure argv (`buildcache.py:335-352`) に
`-DCMAKE_PREFIX_PATH` は**無い**。一方 CCBench は `find_package(gflags REQUIRED)` /
`find_package(glog REQUIRED)` を要求する (`external/ccbench/CMakeLists.txt:33-34`)。
`certify_calibration.sh:464,503` が gflags/glog を自前 build して明示的に prefix を渡している事実が、
**計算ノードにこれらが存在しない**ことの一次証拠である。

**親の実測**: CMake は環境変数 `CMAKE_PREFIX_PATH` を尊重する。fake package config を用いた最小 project で、
env 無しでは `find_package(... REQUIRED)` が失敗し、env 有りでは `Configuring done` になることを確認した。

**裁定**: job script に gflags/glog の build/install と `CMAKE_PREFIX_PATH` export を**含める**。
理由 = これは条件付き機能ではなく job の必須 prologue であり、欠けると解禁後の初回実走が build 失敗で
10 時間の allocation を捨てる。実装は `certify_calibration.sh:376-510` からの出典明記つき移植とし、
pin (`gflags_expected_head` / `glog_expected_head`) と clean 検査も同型で持つ。

## 4. 所有と順序 (P7 を否定して改訂)

**逐次 2 単位。並列にしない** (A のテストが B の成果物を読むため)。

| 順 | owner | 編集してよいファイル |
|---|---|---|
| 1 | 実装子 B | `tools/pegasus/floor_campaign.sh` (新規) のみ |
| 2 | 実装子 A | `tools/pegasus/submit_floor.sh` (新規)、`tools/pegasus/policy.json`、`orchestrator/tests/test_pegasus_floor_tools.py` (新規) のみ |
| — | 親 | `tools/pegasus/README.md`、docs、commit (段 7) |

実装子は docs を編集せず commit しない (DW-S05-B)。

## 5. ユーザーへ返す裁定パッケージ (実装しない)

1. **D86(3) の文言 vs 実体 (A-04)**: 「人間の明示 qsub を authorization とする」は、生成物が
   AI 実行と byte-level で区別不能なため、**authorization ではなく submission 記録**である。
   D86(3) の再確認または文言修正が要る。
2. **driver 予算定数が hard cap でない (B-02)**: `buildcache` は configure と build に**各々** 900 s を
   適用し (`buildcache.py:500-501`)、測定は rep ごと 120 s × 5 rep (`runner.py:398,434`)。
   driver の envelope (900/セル・145/attempt) は見積であって上限ではない。
   独立 prerequisite wave で driver 側を直すか、walltime を厚く取り続けるかの裁定が要る。
3. **A-01 本体・A-02 残余・A-12**: 実行 revision 束縛と spool bytes 独立照合は段階 3 の入力。

## 6. 変異事前登録 (DW-M01。実装後に anchor を再検証する)

| # | 変異位置 (anchor) | 期待 kill | 単一理由性の確認方法 |
|---|---|---|---|
| M1 | `policy.json` の `floor_walltime_s` を 28800 へ | `test_floor_policy_covers_derived_reservation_envelope` | envelope 導出は純関数。手前に同入力を拒否する検査なし |
| M2 | `floor_campaign.sh` の `#PBS -l elapstim_req=` を `08:00:00` へ | `test_floor_pbs_directives_match_policy` | directive 文字列は 1 箇所 |
| M3 | job の `sha256sum "$0"` 照合を削除 | `test_floor_job_binds_executing_script_bytes` | repo blob 照合とは別 assert に分ける |
| M4 | job の qstat `Elapse Time Limit` 照合を削除 | `test_floor_job_binds_scheduler_elapse_limit` | policy 照合とは別 assert |
| M5 | driver 起動を `python3` (裸) へ戻す | `test_floor_job_hardens_interpreter` | argv 構築は 1 箇所 |
| M6 | driver rc 2 を 0 へ変換する分岐を追加 | `test_floor_driver_failure_propagates_rc` | stub driver で rc を注入 |
| M7 | `qsub -v` に `IZANAGI_RESERVATION_REQUESTED_S` を追加 | `test_submit_floor_qsub_exports_nonce_only` | export_spec は 1 箇所 |
| M8 | claims の symlink 拒否を削除 | `test_submit_floor_rejects_unsafe_existing_claim_root[symlink]` | provisioning 関数は 1 箇所 |
| M9 | gflags/glog の `CMAKE_PREFIX_PATH` export を削除 | `test_floor_job_exports_build_prefix_path` | export は 1 箇所 |
| M10 | 非 dry-run の `--repo-root` override 拒否を削除 | `test_submit_floor_rejects_overrides_in_real_submission` | 引数検証は 1 箇所 |

## 7. 本 wave の不変条件 (再掲・追加)

- I1: `orchestrator/campaign/s8b_floor_campaign.py` を 1 byte も編集しない。
- I2: 凍結 bytes 不変。`output/s8b-freeze/` へ書かない。
- I3: **環境変数同士の一致を authorization gate と呼ばない**。`SCRIPT_SHA256` も同様。
- I4: 新しい Git receipt を作らない。
- I5: AI は `qsub` しない。検証は `--dry-run` と一時 repo テストまで。
- I6: 既存 `submit_certify.sh` / `certify_calibration.sh` / `smoke_probe.sh` を編集しない。
- I7: `output/claims` の provisioning は wrapper が行う (driver は作らない)。
- I8 (新): **本 wave の実 repo `output/` へ副作用を残さない**。テストは一時 repo だけで行う。

---

## plan

基準 commit は `e9b6f69ceb875b150b3c1f9d3e000c09146e585f` と一致する。以下は実装せずに起草したプランである。新規 3 ファイルは未存在なので、その対象行番号は捏造せず、同型元の実在行と新規ファイル内の anchor 名で示す。

## 1. `tools/pegasus/submit_floor.sh`

### 段構成

| 新規 anchor | 同型元・根拠 | 実装内容 |
|---|---|---|
| `usage()` / 引数 parse | `tools/pegasus/submit_certify.sh:5-30` | `--dry-run`、`--repo-root PATH`、`--attempts-root PATH`、`--job-script PATH`、`-h/--help`。floor 固有の数値引数、`--mode`、`--protocol`、walltime override は設けない。protocol 数値は凍結 JSON、walltime は policy の単一源とする。 |
| policy 読込 | `submit_certify.sh:50-73`、`tools/pegasus/policy.json:2-8` | `project`、`queue`、`nodes`、`floor_walltime_s` を読む。既存 key は不変。 |
| source identity | `submit_certify.sh:75-91`、job 側の output 除外作法 `certify_calibration.sh:174-181` | 永続 directory を作る前に `HEAD` を取得し、小文字 40 hex を要求。全 tracked bytes は `HEAD` と一致させ、untracked は `output/` 配下だけ許す。 |
| submission staging | `submit_certify.sh:93-101` | 既定は `output/env/pegasus/floor/attempts/submissions/<nonce>/`。親だけ `mkdir -p`、nonce leaf は `mkdir` 一回のみ。 |
| 4 preflight | `submit_certify.sh:103-125` | `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` をすべて実行し、各 `stdout`、`stderr`、整数 rc を保存。1 件でも失敗すれば `pre-submit.json` を残して qsub 前に rc 3。 |
| pre-submit JSON | `submit_certify.sh:127-163` | 下記の閉じた schema を mode `x` で作る。 |
| claim root provisioning | driver `s8b_floor_campaign.py:2805-2833`、README `tools/pegasus/README.md:121-125` | preflight 成功後、qsub 前に固定 path `REPO_ROOT/output/claims` を準備する。 |
| qsub / receipt | `submit_certify.sh:170-237` | qsub raw output/rc、request ID parse、submit receipt の create-only 作成。 |

### 引数の境界

- `--attempts-root` は hermetic dry-run テスト用とし、非 dry-run では既定 path 以外を拒否する。実 job は固定 namespace から receipt を探すため、任意 path を scheduler job へ渡さない。
- `--job-script` も dry-run fixture 用。非 dry-run では repo 内の tracked、非 symlink regular file `tools/pegasus/floor_campaign.sh` と一致しなければ拒否する。
- `--repo-root` は clone/worktree または一時 repo の指定に使える。実 qsub は `(cd "$REPO_ROOT" && qsub ...)` とし、job が依存する `PBS_O_WORKDIR` を repo root に固定する。
- floor 固有引数は不要。driver CLI は `--mode`、`--protocol`、任意の `--resume` しか持たないが (`s8b_floor_campaign.py:3382-3391`)、submit 側にこれらの override 面を出さない。

### policy の追加値

`tools/pegasus/policy.json:8` の後へ、暫定 pin として次を追加する。

```json
"floor_walltime": "08:10:00",
"floor_walltime_s": 29400
```

根拠は実 protocol の 12 cells、8 sessions、2 retry slots、`extime_s=5`、`reps=5` (`output/s8b-freeze/floor_protocol.json:1`) と driver の式 (`s8b_floor_campaign.py:165-175,640-677`) である。

```text
driver required = 12 * (900 + (8 + 2) * (5 * 5 + 120)) = 28200
driver finalize margin = 600
driver が要求する合計 = 28800
wrapper/startup reserve = 600
PBS request = 29400 = 08:10:00
```

28800 秒ちょうどでは scheduler start 後の wrapper 処理時間により `check_reservation()` が必ず不足する (`reservation.py:253-259`)。600 秒の startup reserve は実測前の policy pin なので、§6 の確認対象とする。既存 smoke の実 queue dumpでは上限 86400 秒だった (`output/env/pegasus/smoke/0:867861.nqsv/qstat_queue_detail.stdout:130-136`)。

### source clean の正確な意味と位置

`submit_certify.sh:75-84` と同じく、policy と引数の検証後、nonce・staging・claims の作成前に行う。ただし floor は dry-run artifact と durable claims を `output/` に残した後も再投入できる必要があるため、単純な full-untracked clean にはしない。

- `git diff --quiet HEAD --` と `git diff --cached --quiet HEAD --` で、`output/s8b-freeze/` を含む全 tracked bytes の変更を拒否。
- `git status --porcelain --untracked-files=all -- . ':(exclude)output'` で、`output/` 外の tracked/untracked 変更を拒否。
- これにより receipt/claim の untracked output は許す一方、凍結成果物の tracked 改変は拒否する。
- job script は `git ls-files --error-unmatch` でも tracked であることを確認してから SHA-256 を取る。

### dry-run と 4 capture

`submit_certify.sh:112-125` をそのまま踏襲する。

- 4 command は一切起動しない。
- 各 `<name>.stdout` は exact `"not run (--dry-run)\n"`。
- `<name>.stderr` は空 bytes。
- `<name>.rc` は `"0\n"`。
- `qsub.stdout` は `"dry-run: qsub was not executed\n"`、stderr は空、rc は 0。
- synthetic `job_id` は `dry-run-<nonce>`。`dry_run: true` のため authorization や実 job artifact として扱わない。
- dry-run でも submission staging と `output/claims` は作る。したがってテストは一時 repo だけで行う。

### `claims/` provisioning

正確な path は、CLI main が `repo_output_root()` を `out_root` にすること (`s8b_floor_campaign.py:3443-3452`) と `repo_output_root()` の定義 (`layout.py:36-48`) から、`<repo>/output/claims` である。

- 不存在時: `output/` 自体が非 symlink directory であることを確認し、`output/claims` を mode `0700` で一度だけ作る。
- 既存時: `lstat` で symlink でなく directory、かつ `stat.S_IMODE(st_mode) == 0o700` を要求する。
- mode 不一致を `chmod` で修復しない。file/symlink を削除・置換しない。
- driver 自身の受理条件は「非 symlink directory」+ durable root policy のみで、mode は検査していない (`s8b_floor_campaign.py:2823-2833`)。0700 exact 検査は wrapper/runbook 側の追加 fail-closed 条件である。
- wrapper は claim file を作らない。driver が開始時刻と protocol hash から identity を生成し (`s8b_floor_campaign.py:2816-2820`)、`claims/<identity>.claim` を O_EXCL で作る (`campaign_claim.py:98-103,167-205`)。

### qsub export

```text
qsub -v IZANAGI_SUBMISSION_NONCE=<32 lowercase hex> tools/pegasus/floor_campaign.sh
```

渡す独自変数は nonce だけとする。

- source commit、script hash、request は receipt から再読する。
- `IZANAGI_RESERVATION_*` は login node から渡さず、compute job が scheduler/qstat/boot 情報から上書き生成する。
- nonce と receipt の一致は staging transport の束縛であり、authorization gate として数えない。
- qsub 応答 ID は `submit_certify.sh:191-205` と同じ `Request <id> submitted`、または単一 token だけを受理する。

### JSON schema

設計正本が要求する `source_commit/job_script_path/job_script_sha256/job_id/nonce/submitted_at` (`2026-07-25_t088-official-unlock-design.md:103-105`) を top-level に置く。校正用 schema の `qsub.request_id` と重複させない。

`pre-submit.json` の exact top-level keys:

| key | 型・制約 |
|---|---|
| `schema_version` | str、literal `pegasus-floor-pre-submit/v1` |
| `source_commit` | str、小文字 40 hex |
| `job_script_path` | str、repo-relative POSIX path。実投入は `tools/pegasus/floor_campaign.sh` |
| `job_script_sha256` | str、小文字 64 hex |
| `nonce` | str、小文字 hex 32 桁 |
| `prepared_at` | bool ではない正整数 Unix epoch |
| `request` | 下記 object |
| `preflight` | 下記 object |
| `dry_run` | bool |

`submit-receipt.json` の exact top-level keys:

| key | 型・制約 |
|---|---|
| `schema_version` | str、literal `pegasus-floor-submit-receipt/v1` |
| `source_commit` | pre-submit と同じ str |
| `job_script_path` | pre-submit と同じ str |
| `job_script_sha256` | pre-submit と同じ str |
| `job_id` | 非空 str。実投入は qsub 応答 ID |
| `nonce` | pre-submit と同じ str |
| `submitted_at` | qsub 起動直前に取得した、bool ではない正整数 Unix epoch |
| `request` | pre-submit と同一 object |
| `preflight` | pre-submit と同一 object |
| `dry_run` | bool |

`request` の exact keys は `project: str`、`queue: str`、`nodes: int`、`elapstim_req_s: int`。初期値は `SFC`、`gen_S`、`1`、`29400`。

`preflight` の exact keys は `qstat_Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota`。各値は exact keys `rc: int`、`stdout_raw: str`、`stderr_raw: str` を持つ。job 側の parser は duplicate JSON key、余剰 key、bool-as-int も拒否する。

## 2. `tools/pegasus/floor_campaign.sh`

### PBS header と予約式

`certify_calibration.sh:1-13` と同型にする。

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=08:10:00
#PBS -b 1
```

直後のコメントに以下を literal で残す。

```text
floor driver envelope:
12 * (build_cap_per_cell=900
      + (scheduled_attempts_per_cell=8 + retry_slots_per_cell=2)
        * (extime_s=5 * reps=5 + verify_cap_per_attempt=120))
= required_s 28200
+ driver finalize reserve 600
= driver capacity 28800
+ wrapper/startup reserve 600
= PBS request 29400 seconds
```

PBS directive と policy の一致はテストで固定する。`REQUESTED_S` は 29400 のままであり、driver が導出する 28200 や 28800 に作り直さない。

### job の段構成

1. **PBS identity / TMPDIR**

   `certify_calibration.sh:15-31` と同じく `PBS_JOBID`、`PBS_O_WORKDIR` を必須化し、job ID を安全な文字集合へ閉じる。CMake path の colon 問題を避けるため `TMPDIR=/scr/${PBS_JOBID//:/_}` を leaf `mkdir` で create-only 作成する。raw job ID は receipt path では保持する。

2. **固定 root と job staging**

   `certify_calibration.sh:33-44` の calibration namespace を floor に置換する。

   ```text
   ATTEMPTS_ROOT=<repo>/output/env/pegasus/floor/attempts
   JOB_STAGING_ROOT=<repo>/output/env/pegasus/floor/job-staging
   ATTEMPT_DIR=<job-staging>/<raw PBS_JOBID>
   ```

   親のみ `mkdir -p`、`ATTEMPT_DIR` は `mkdir` 一回だけ。既存時は非 0。

3. **failure trap**

   `certify_calibration.sh:46-93` を再利用する。`failure.json` は first-writer-only、schema は既存の汎用 literal `pegasus-job-failure/v1` とする。

   Exact keys は `schema_version: str`、`pbs_jobid: str`、`rc: int`、`stage: str`、`message: str`、`recorded_epoch: int`。

4. **policy 読込**

   `certify_calibration.sh:105-141` の先頭部分と同型で `project`、`queue`、`nodes`、`floor_walltime_s` を取得し、`REQUESTED_S=29400` とする。

5. **nonce → receipt 束縛**

   `certify_calibration.sh:143-172` を踏襲する。

   - nonce は exact `[0-9a-f]{32}`。
   - `attempts/submissions/$IZANAGI_SUBMISSION_NONCE/submit-receipt.json` を最大 60 回、1 秒間隔で待つ。
   - symlink でない regular file のみを job staging へコピー。
   - timeout は `write_failure 2 submit_binding ...` 後 rc 2。
   - receipt の `schema_version`、閉じた key set、`dry_run is False`、`nonce`、policy request、job ID を strict 検査する。
   - qsub ID と `$PBS_JOBID` は既存の狭い `normalize_request_id()` を使う (`certify_calibration.sh:188-207`)。

6. **source・tracked-clean・script blob 再照合**

   `certify_calibration.sh:174-208` の位置で行う。

   - 現在の HEAD が小文字 40 hex で、receipt の `source_commit` と一致。
   - submit 側と同じ「全 tracked bytes clean + `output/` 外に untracked なし」検査。
   - receipt の `job_script_path` が exact `tools/pegasus/floor_campaign.sh`。
   - repo 上の同 file が tracked、非 symlink regular file。
   - SHA-256 を再計測し receipt と一致。
   - これらは submission integrity の再照合であり、`IZANAGI_RESERVATION_SCRIPT_SHA256` と同じ値になること自体を authorization と呼ばない。

7. **qstat allocation**

   `certify_calibration.sh:210-318` の parser を同型で持つ。

   - `QSTAT_JOBID=${PBS_JOBID#0:}`。
   - `timeout 30 qstat -f "$QSTAT_JOBID"` の raw stdout/stderr/rc を保存。
   - assigned host は `exec_host`、`exec_vnode`、`assigned_host`、`vnode`、NQSV の `Execution Hosts(JSVNO)` の順に読む (`certify_calibration.sh:248-276`)。
   - start は `stime`、`start_time`、`start`、`Started Request Time` を読む (`:277-293`)。
   - host は qstat 値と `hostname` または `hostname -f` の exact match が必要 (`:311-318`)。
   - 不明時は `allocation-unavailable.json` と `failure.json` を残して rc 2。

8. **reservation 8 値**

   `_ENV_FIELDS` の exact 集合 (`reservation.py:120-129`) を export する。

   | 環境変数 suffix | 値の唯一の出所 |
   |---|---|
   | `JOB_ID` | scheduler が与えた raw `$PBS_JOBID` |
   | `REQUESTED_S` | policy の `floor_walltime_s` = 29400 |
   | `SCHEDULER_STARTED_EPOCH` | qstat の start field |
   | `DEADLINE_EPOCH` | `SCHEDULER_STARTED_EPOCH + REQUESTED_S` |
   | `HOST` | qstat assigned host と exact 一致した `hostname` / `hostname -f` |
   | `BOOT_ID` | `/proc/sys/kernel/random/boot_id` |
   | `SCRIPT_SHA256` | job 冒頭で再計測した repo 上の `floor_campaign.sh` |
   | `NONCE` | qsub `-v` の nonce。receipt の nonce と transport 照合済み |

   `certify_calibration.sh:320-340` と同じ lowercase record + `recorded_epoch` を `reservation.json` として create-only 保存する。

9. **driver argv**

   固定 argv は次だけとする。`--resume`、pilot、env 由来の mode/protocol は入れない。

   ```bash
   python3 "$REPO_ROOT/orchestrator/campaign/s8b_floor_campaign.py" \
     --mode official \
     --protocol "$REPO_ROOT/output/s8b-freeze/floor_protocol.json"
   ```

   protocol の実 field は `output/s8b-freeze/floor_protocol.json:1` の 18 keys であり、`cells` と `schedule` は存在しない。driver が freeze から 12 cells を列挙し、8 rounds × 12 = 96 rows を導出する (`s8b_floor_campaign.py:2763-2768`)。

10. **rc と結果**

    driver stdout/stderr は `floor-driver.stdout` / `floor-driver.stderr` に保存し、`|| driver_rc=$?` で ERR trap の早期終了を避ける。`job-result.json` は driver 起動後なら成功・失敗を問わず作る。

    Exact schema:

    | key | 型・値 |
    |---|---|
    | `schema_version` | str、literal `pegasus-floor-job-result/v1` |
    | `pbs_jobid` | str |
    | `driver_rc` | int |
    | `mode` | str、literal `official` |
    | `protocol_path` | str、literal `output/s8b-freeze/floor_protocol.json` |
    | `source_commit` | str、再照合済み 40 hex |
    | `job_script_sha256` | str、再照合済み 64 hex |
    | `nonce` | str、32 hex |
    | `completed_epoch` | int |

    `driver_rc != 0` なら `write_failure "$driver_rc" floor_driver ...` を呼び、同じ rc で shell を終了する。成功時だけ rc 0。

### 現時点の official 拒否

現在は CLI が protocol load より先に official を rc 2 で拒否する (`s8b_floor_campaign.py:3432-3441`)。core の lock も残る (`:193-203`)。したがって現 wave の実 job は次になる。

```text
job-result.json.driver_rc = 2
failure.json.rc = 2
failure.json.stage = "floor_driver"
PBS job exit status = 2
```

rc 2 を「wrapper 成功」へ変換する分岐、`|| true`、期待失敗を理由にした `exit 0` は置かない。次 wave で admission が解禁された場合も、この job script 自体は変更せず正常経路へ進める形にする。

### final receipt の判断

既存 `collect_receipt.py` は `acquisition-receipt.json`、calibrator attempt、`calibrate_rc` を必須とする (`collect_receipt.py:107-141`)。floor job にはいずれも存在しないため、本 wave で流用しない。新しい floor collector も scope に加えない。

submission receipt、reservation、job-result、failure、qstat raw は残るが、scheduler stdout/stderr を final receipt に束縛する仕組みは未実装のままである。admission wave が scheduler spool/script bytes の独立照合を必要とすると再裁定した場合に限り、floor 専用 collector を別 scope で設計する。

## 3. テスト — `orchestrator/tests/test_pegasus_floor_tools.py`

### 静的・hermetic job-tail 検査

| nodeid | 検査内容 |
|---|---|
| `...::test_floor_shell_syntax[submit_floor.sh]` | `bash -n` |
| `...::test_floor_shell_syntax[floor_campaign.sh]` | `bash -n` |
| `...::test_floor_pbs_directives_match_policy` | `-A/-q/-b/-l` が policy と一致し、重複・late・commented-out directive がない |
| `...::test_floor_policy_covers_derived_reservation_envelope` | protocol/freeze から `(28200,600)` を純粋導出し、policy 秒と時刻表記が一致、startup slack が 600 |
| `...::test_floor_protocol_derives_twelve_cells_and_ninety_six_schedule_rows` | protocol に `cells/schedule` がなく、driver 純粋関数が 12/96 を導出 |
| `...::test_submit_floor_static_contract` | fixed staging、32 hex nonce、4 captures、create-only JSON、tracked job script、claims path/mode |
| `...::test_submit_floor_qsub_exports_nonce_only` | `qsub -v` の独自変数が nonce だけ。reservation、mode、protocol の export がない |
| `...::test_floor_job_submission_rebind_is_fail_closed` | 60 秒待ち、dry-run 拒否、source/path/hash/request/job ID の全照合 |
| `...::test_floor_job_qstat_parser_accepts_nqsv_section_fields` | `Execution Hosts(JSVNO)` と `Started Request Time` の小 fixture を parser が処理 |
| `...::test_floor_job_exports_exact_reservation_fields` | `reservation._ENV_FIELDS` と shell の export 集合が exact 8 件、各 origin anchor が存在 |
| `...::test_floor_job_invokes_fixed_official_cli_without_bypass` | fixed official/protocol、`--resume`・pilot・`eval`・env mode/protocol がない |
| `...::test_floor_job_create_only_namespaces_and_json` | TMPDIR/job staging/JSON に `mkdir`/mode `x` を使い、leaf の `mkdir -p` や truncate がない |
| `...::test_floor_driver_failure_writes_both_records_and_propagates_rc` | driver stub rc 2/7 で job-result と failure を作り、同じ rc を返す |
| `...::test_floor_driver_success_writes_result_without_failure` | driver stub rc 0 で job-result のみ、shell rc 0 |

### 一時 repo での dry-run

| nodeid | 検査内容 |
|---|---|
| `...::test_submit_floor_dry_run_is_scheduler_free_and_writes_exact_receipts` | clean temp git repo。qstat/pegasusinfo/rbudgetcheck/check_quota/qsub は sentinel stub とし、どれも呼ばれないこと、両 JSON の exact key/type/schema、hash/path/request、4 dry-run captures、claims 0700 を検査 |
| `...::test_submit_floor_second_dry_run_allows_prior_untracked_output` | 同じ temp repo で 2 回 dry-run し、異なる nonce の create-only receipt が 2 件残る |
| `...::test_submit_floor_dirty_source_fails_before_side_effects` | tracked source を変更し、submission/claims が作られる前に拒否 |
| `...::test_submit_floor_tracked_output_mutation_fails_before_side_effects` | tracked `output/` fixture を変更し、単純な output 除外で見逃さないことを検査 |
| `...::test_submit_floor_rejects_unsafe_existing_claim_root[symlink]` | symlink を拒否、submit receipt/qsub なし |
| `...::test_submit_floor_rejects_unsafe_existing_claim_root[regular-file]` | file を拒否 |
| `...::test_submit_floor_rejects_unsafe_existing_claim_root[mode-0755]` | mode 不一致を chmod せず拒否 |
| `...::test_submit_floor_rejects_real_attempts_root_override_before_qsub` | 非 dry-run で alternate attempts root を拒否し qsub sentinel が未実行 |
| `...::test_submit_floor_rejects_real_job_script_override_before_qsub` | 非 dry-run の alternate/symlink job script を拒否 |

既存 `test_pegasus_tools.py:90-166,1005-1033` と shell syntax、PBS parser、dry-run の型が一部重複する。新ファイルで再掲する理由は、既存 parametrization が legacy 3 script に固定されており (`:114-133`)、I6 により同ファイルを編集せず floor 専用 nodeid・mutation owner を独立させるためである。

## 4. 所有分割

親案は編集ファイル素集合として成立する。

| owner | 編集ファイル | 注意 |
|---|---|---|
| A | `tools/pegasus/submit_floor.sh`、`tools/pegasus/policy.json`、`orchestrator/tests/test_pegasus_floor_tools.py` | policy/schema/qsub export/test の owner |
| B | `tools/pegasus/floor_campaign.sh` | job 側だけを編集 |
| 親 | `tools/pegasus/README.md` | 子の docs 禁止を維持 |

A のテストは B の script を読むため統合依存はあるが、編集競合はない。着手前に次を interface pin として両者へ同文で渡す必要がある。

- walltime `08:10:00` / `29400`
- schema と exact keys
- `qsub -v` は nonce のみ
- fixed receipt/staging/claims path
- driver argv
- job-result/failure の rc 伝播
- planned anchor 名

親は `tools/pegasus/README.md:121-139` を更新し、「wrapper は次 wave」を次へ置換する。

- dry-run と人間 qsub の command
- submission/job-staging/claims の paths
- 29400 秒の根拠
- dry-run receipt は authorization でないこと
- 現時点の実 job は rc 2 を忠実記録すること
- `collect_receipt.py` は floor には使わないこと

重要な完了境界として、コード受入は dry-run まで可能だが、設計正本の「実 submit artifact ID を 1 度確認」 (`official-unlock-design.md:99-105`) は synthetic dry-run ID では満たさない。wrapper-only wave の artifact gate 完了は、マージ後に人間が qsub し、`dry_run:false` の実 `job_id` を確認した時点である。AI はその qsub を行わない。

## 5. 変異候補

新規 script は未存在なので、行番号ではなく実装時に固定する anchor で示す。

| 変異 | anchor | 赤くなるべきテスト |
|---|---|---|
| `floor_walltime_s` を 28800 または 29399 にする | `tools/pegasus/policy.json` の `floor_walltime_s` | `test_floor_policy_covers_derived_reservation_envelope` |
| PBS directive を `08:00:00` にする | `floor_campaign.sh` の `#PBS -l elapstim_req=` | `test_floor_pbs_directives_match_policy` |
| qsub export に `IZANAGI_RESERVATION_REQUESTED_S` や mode を追加 | `submit_floor.sh` の `export_spec=` | `test_submit_floor_qsub_exports_nonce_only` |
| dry-run branch で qstat または qsub を起動 | `if [[ "$DRY_RUN" -eq 1 ]]` | `test_submit_floor_dry_run_is_scheduler_free_and_writes_exact_receipts` |
| source clean を staging/claims 作成後へ移す | comment anchor `# source identity` | `test_submit_floor_dirty_source_fails_before_side_effects` |
| tracked `output/` を clean 検査から除外 | `git diff --quiet HEAD --` | `test_submit_floor_tracked_output_mutation_fails_before_side_effects` |
| 既存 claims mode 0755 を許す、または chmod で直す | anchor `provision_claim_root` | `test_submit_floor_rejects_unsafe_existing_claim_root[mode-0755]` |
| submit receipt から `job_script_path` または `nonce` を落とす | schema literal `pegasus-floor-submit-receipt/v1` | dry-run exact receipt test、`test_floor_job_submission_rebind_is_fail_closed` |
| job 側の source commit または script hash 比較を削る | anchor `# source identity recheck` | `test_floor_job_submission_rebind_is_fail_closed` |
| NQSV section fallback を削る | qstat parser の `Execution Hosts(JSVNO)` | `test_floor_job_qstat_parser_accepts_nqsv_section_fields` |
| `REQUESTED_S` を driver の 28200/28800 に作り直す | `export IZANAGI_RESERVATION_REQUESTED_S=` | `test_floor_job_exports_exact_reservation_fields` |
| driver argv を pilot、可変 protocol、`--resume` 付きにする | `driver_argv=(` | `test_floor_job_invokes_fixed_official_cli_without_bypass` |
| driver rc 2 を 0 に変換する | `if [[ "$driver_rc" -ne 0 ]]` | `test_floor_driver_failure_writes_both_records_and_propagates_rc` |
| job staging leaf を `mkdir -p` にする | `ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"` | `test_floor_job_create_only_namespaces_and_json` |
| receipt 待ちを無制限化、または 60 秒超へ変える | `for _ in $(seq 1 60)` | `test_floor_job_submission_rebind_is_fail_closed` |

## 6. risks / 未確定

- **walltime の operational reserve:** 28800 秒は driver の必要量であり PBS 要求には使えない。提案の追加 600 秒で receipt wait 60 秒、qstat timeout 30 秒、git/hash/setup を吸収できるかは実測が要る。600 秒を超えるなら policy と PBS directive を同じ commit で増やす。
- **queue policy:** 保存済み実測では `gen_S` の上限は 86400 秒だが、投入時点の設定変更はあり得る。人間 qsub 前に `qstat -Q` に加えて手動 `qstat -Qf gen_S` で 29400 秒を受けることを確認する。
- **qstat field 名:** 現物は `Execution Hosts(JSVNO)` / `Started Request Time` だったが、scheduler version により key・折返し・timezone 表記が変わり得る。parser が取得不能なら推測せず allocation failure。
- **host 表記:** qstat が scheduler alias、FQDN、複数 host 表記を返す場合、現案の exact `hostname`/`hostname -f` 一致は拒否する。単一 node 以外へ縮退しない。
- **request ID:** qsub 応答形式と raw `$PBS_JOBID` の `0:` prefix は実装済み同型を使うが、別 prefix や配列 job 表記は拒否される。
- **`PBS_O_WORKDIR`:** wrapper を repo root へ `cd` して qsub する設計が、NQSV で期待どおり `$PBS_O_WORKDIR` に反映されるか要確認。
- **`/scr` lifecycle:** scheduler が同名 directory を先に作る、または過去 job の directory を残す環境では create-only TMPDIR が拒否する。既存物を削除・再利用しない。
- **filesystem semantics:** claim の O_EXCL/fsync は Lustre/NFSv4 前提で、NFSv3 は対象外 (`campaign_claim.py:167-173`)。mode 0700 でも ACL による追加権限までは検査しない。
- **claim mode の二層差:** driver は mode 0700 を検査しない。wrapper から driver 起動までの置換・mode 変更は、driver の symlink/directory/durable-root 検査だけが残る。本 wave で新 authorization gate は加えない。
- **script SHA の限界:** reservation の script SHA は環境変数から読まれ、形式しか検査されない (`reservation.py:159-175,218-270`)。receipt と env の一致を独立 attestation と呼ばない。scheduler spool bytes との独立照合は admission wave の再裁定事項 (`official-unlock-design.md:114-120`)。
- **current official 実行:** current CLI は rc 2 で protocol/reservation consumer/claim acquisition より前に止まる。そのため実 qsub で wrapper の qstat/export/job-result は測れるが、driver 内 reservation/claim の production 消費はまだ発火しない。
- **final receipt 不在:** floor 専用 final collector は本 scope にない。scheduler stdout/stderr と job staging の hash 束縛が admission に必要と判断された場合は別 wave。
- **scope 外:** `_assert_official_permitted` (`s8b_floor_campaign.py:193-203`) と CLI 固定拒否 (`:3434-3441`) は 1 byte も変えない。単一 admission predicate、CLI rc 翻訳、certificate/ratified/resume は段階 3・4であり本プランに含めない。

sandbox が read-only のため pytest は実行しておらず、緑は主張しない。
---

## lensA

BLOCKER 7 件、MUST 5 件です。現行 HEAD を正規の interpreter で実行する限り CLI rc=2 は残りますが、プランはその前提を機械的に閉じていません。実装着手・完了判定とも不可です。

前提として、HEAD は `e9b6f69ceb875b150b3c1f9d3e000c09146e585f`、worktree は clean、予定する新規 3 ファイルは未存在でした。したがって以下はプランと同型元・現行 driver の静的監査であり、実 wrapper の動作確認ではありません。pytest は実行していません。

## 所見

### A-01 / BLOCKER

**主張:** `--repo-root` が非 dry-run でも任意の clean clone/worktree を受け入れるため、source identity は「承認済み revision」ではなく「その HEAD と自己一致する revision」にすぎない。guard を削除した clean commit、private core を呼ぶ clean commit、freeze と pin を同時変更した clean commitも通る。

**一次証拠:** [plan.md:20–23](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:20)、[plan.md:46–53](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:46)、現行 guard は [s8b_floor_campaign.py:193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:193)、public wrapper は [同:2639](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:2639)、private core は [同:2682](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:2682)。

**放置時:** wrapper が受け入れる revision 集合に guard 無効 revision が入り、official 受理集合が非空化し、`eligible_for_refreeze` が真の result を生成できる。

### A-02 / BLOCKER

**主張:** job が再 hash するのは「実行中の PBS spool bytes」ではなく repo 上の `floor_campaign.sh` である。hash 後〜qsub 間の script 差し替え、job recheck 後〜driver 起動間の source 差し替えを閉じない。

**一次証拠:** job は repo file の hash を使う案 [plan.md:196–205](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:196)、reservation SHA の出所も repo file [同:230](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:230)。プラン自身が spool bytes 未束縛を認める [同:387](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:387)。設計正本は scheduler record/spool bytes/committed blob の独立照合を要求する [設計正本:114–118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/output/insights/2026-07-25_t088-official-unlock-design.md:114)。現行 clean scan にも content TOCTOU の既知限界がある [s8b_floor_campaign.py:1606](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1606)。

**放置時:** 悪性 spool script が private coreを呼ぶ、または `job-result.json` を偽造しても、receipt と reservation は正常な repo blob hash を掲げられる。

### A-03 / BLOCKER

**主張:** 「固定 argv」は固定 executable を意味しない。bare `python3`、PATH、`PYTHONPATH`/`sitecustomize`、imported bash function を閉じていない。job 環境に残れば、現行 test seam と同じ monkeypatch が production 起動前に可能である。

**一次証拠:** driver 起動は bare `python3` [plan.md:235–243](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:235)。qsub が明示 export するのは nonce だけだが、環境消去・interpreter pin はない [同:77–87](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:77)。テスト案も mode/protocol/eval の文字面しか対象にしない [同:298–302](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:298)。実 test seam は guard を monkeypatch している [test_s8b_floor_campaign.py:612–620](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_s8b_floor_campaign.py:612)。

**放置時:** 悪性 interpreter/site customization が guard を無効化、private core を実行、または rc=0 と ledger を偽造できる。

### A-04 / BLOCKER

**主張:** 人間と AI が同じ `qsub` を実行した場合、生成物は byte-level で区別不能である。したがって submission artifact は human authorization ではなく、単なる submission 記録である。

**一次証拠:** D86 は「人間の明示 qsub」を authorization とする [decisions.md:3730–3732](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/decisions.md:3730)。しかし receipt の exact fields に actor、credential、署名、対話証拠はない [plan.md:108–125](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:108)。さらに qsub 自体も PATH 上の bare command で、同型元は return code と文字列だけから ID を受理する [submit_certify.sh:170–205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_certify.sh:170)。

**放置時:** AI 実行または fake `qsub` が作った `dry_run:false` record を、後続 admission が「人間認可」と誤受理する。

### A-05 / BLOCKER

**主張:** P2 の dry-run 完了条件は恒真化しており、設計正本および plan 自身と矛盾する。

**一次証拠:** brief は dry-run artifact 生成までで wave 完了とする [brief.md:48–49](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/brief.md:48)。dry-run は全 preflight rc=0 と synthetic job ID を自作する [plan.md:55–65](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:55)。一方、設計正本は実 submit artifact ID を要求する [設計正本:99–105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/output/insights/2026-07-25_t088-official-unlock-design.md:99)し、plan 自身も dry-run では満たさないと認める [plan.md:352](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:352)。

**放置時:** scheduler・job・reservation・rc 伝播を一度も発火させずに DW-G04 完了扱いとなり、phantom artifact を入口に admission wave が進む。

### A-06 / MUST

**主張:** 新設予定の「検査」には、独立保証でない自己整合検査が混在している。

| 検査 | 実態 |
|---|---|
| dry-run preflight/qsub | 実行せず rc=0 と ID を生成する |
| preflight in receipt | pre-submit の同じ object をコピーするだけ |
| source commit/script hash | submit と job が同じ mutable repo を二度読む時間差検査。承認済み revision/spool の証明ではない |
| request object | policy から作り、job が同じ policy と比較する |
| `SCRIPT_SHA256` | repo hash を env に export。driver は64hex形式しか検査しない |
| `DEADLINE_EPOCH` | job が `start + policy秒` で作り、driver が同じ等式を確認する |
| `reservation.json` | 8 env 値をそのままコピーする |

**一次証拠:** [plan.md:59–65](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:59)、[同:119–125](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:119)、[同:193–205](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:193)、[同:223–233](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:223)。driver の SHA 検査は形式のみ [reservation.py:49–54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/reservation.py:49)、env 読取は [同:159–175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/reservation.py:159)。

**放置時:** provenance 台帳は内部整合するが、実 scheduler reservation・実行 script・人間認可との参照は偽のまま成立する。

続行経路については、4 preflight の失敗収集、qstat rc capture、driver rc captureはいずれも後で非0終了する設計なので、それ自体は fail-open ではない。一方 `write_failure` は記録失敗を `|| true` で隠す [certify_calibration.sh:55](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/certify_calibration.sh:55)。

### A-07 / BLOCKER

**主張:** reservation は PBS が実際に割り当てた walltime へ束縛されない。`REQUESTED_S` は policy 自己申告で、qstat parser は host/start しか読まない。

**一次証拠:** plan の唯一の出所表 [plan.md:223–231](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:223)。qstat parser 対象も host/start のみ [同:211–216](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:211)。保存済み実 qstat には独立な `Remaining Elapse = 7199S` と `Elapse Time Limit = 7200S` が存在する [qstat-f.stdout:56](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/output/env/pegasus/calibration/job-staging/0:867874.nqsv/qstat-f.stdout:56>)、[同:73](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/output/env/pegasus/calibration/job-staging/0:867874.nqsv/qstat-f.stdout:73>)。driver は渡された binding の算術だけを検査する [reservation.py:218–259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/reservation.py:218)。

**放置時:** scheduler の実 limit が policy より短くても driver は長い deadline を信じ、PBS kill により result・report・台帳終端を失う。

### A-08 / MUST

**主張:** `28200 + 600 = 28800` の導出は正しいが、brief の「28800なら境界で必ず落ちる」は厳密には過大主張であり、29400も無条件には足りない。

**一次証拠:** 定数と式 [s8b_floor_campaign.py:165–175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:165)、実計算 [同:640–677](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:640)、容量判定は strict `>` [reservation.py:210–215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/reservation.py:210)、途中再検査 [s8b_floor_campaign.py:2002–2032](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:2002)。

静的導出は次のとおりです。

```text
attempt_cap = 5*5 + 120 = 145
required    = 12 * (900 + (8+2)*145) = 28200
margin      = 600
total       = 28800
```

scheduler start から初回検査までを `Δ` とすると、

```text
T=28800: pass iff Δ <= 0
T=29400: pass iff Δ <= 600
```

`Δ=0` の完全一致ではコード上は通るため「必ず」は偽です。ただし実 job は receipt/qstat/git/hash 処理後なので通常 `Δ>0` となり、28800が実運用で落ちる結論自体は妥当です。これは実 floor job の実測ではなく、コードと凍結入力からの導出です。

途中再検査で、初回 realtime/monotonic 対応からの経過量を `E`、未開始 planned 数を `P`、未消費 retry 枠を `U` とすると、

```text
reservation-lost iff
E > 29400 - 600 - max(1, 145*(P+U))
```

最初の measurement 前は `P=96`, `U=24` なので、`E > 11400` で失う。build cap 合計が10800秒のため、wrapper・driver preflight・store・manifest 等に使える全 slack は600秒だけである。build が cap 近くまで掛かれば、追加 overhead 一つで落ちる。

さらに再検査の `ReservationError` は terminal `reservation-lost` を書いた後そのまま再送出され、CLI の `FloorCampaignError` catch 対象外である [s8b_floor_campaign.py:2023–2032](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:2023)、[同:3453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:3453)。

**放置時:** campaign は `reservation-lost` で numeric values を無効化し、certified 選択・report を生成できず、job 側には想定外の driver rc が記録される。

### A-09 / BLOCKER

**主張:** create-only は leaf にしか掛からず、staging の祖先 component を symlink-safe に検証しない。`output/` 内の untracked symlink は source-clean が許す。

**一次証拠:** parent は `mkdir -p`、nonce leaf だけ `mkdir` [plan.md:11–13](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:11)。source clean は untracked `output/` を除外する [同:48–52](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:48)。job staging も親 `mkdir -p`、leaf のみ create-only [同:163–174](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:163)。同型元の raw capture は shell `>` で既存 leaf を truncate する [certify_calibration.sh:211–215](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/certify_calibration.sh:211)。

例えば `output/env/pegasus/floor/attempts` を `output/s8b-freeze` への symlink として事前配置すれば、submission leaf は freeze namespace 内に作られる。現行 official clean scan は未知 file を拒否する [s8b_floor_campaign.py:1536–1568](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:1536)。同一 UID の race で raw log 名を frozen file への symlink にすれば、`>` が frozen bytes を truncate し得る。

通常の解決済み path では、23件の frozen bytes を直接編集する計画はない。この部分の brief I2 は支持できる。23件の実集合は [test_frozen_artifacts.py:38–85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_frozen_artifacts.py:38)。ただし上記 containment は未防御である。

**放置時:** freeze namespace に未知 file が入り official preflight が恒久拒否するか、frozen bytes/hash chain が壊れ、selector/oracle/certified report の参照が失効する。

### A-10 / MUST

**主張:** nonce/job ID の通常衝突は fail-closed だが、qsub成功とreceipt作成の間に原子的境界がなく、orphan・重複投入・古いreceipt replayが可能である。

**一次証拠:** qsub 後に receipt を作る順序 [submit_certify.sh:181–234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_certify.sh:181)。job は最大60秒待つ [plan.md:185–194](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:185)が、`submitted_at` と scheduler start の時間関係を検査する契約はない。ID normalization は `0:` 一つを除くだけ [schema_v2.py:310–316](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/calibrator/schema_v2.py:310)。

- nonce collision: submission leaf `mkdir` が拒否するので安全。
- 同じ raw job ID: TMPDIR/job-staging leaf が拒否するので安全。
- qsub成功後のID parse/receipt書込失敗: job は既に存在し、再実行すると別nonceの二重投入になる。
- 古いnonce＋再利用されたnormalized job ID: freshness束縛がないため古いreceiptを再利用可能。
- `claims/` は既存0700 directoryの内容を検査しないため、事前配置claimによる拒否・DoSは可能。

**放置時:** 同一 campaign 意図に複数 job、または古い submission record に束縛された job が生じ、台帳の job ID・nonce・authorization 参照が一意でなくなる。

### A-11 / MUST

**主張:** honest shell 経路では driver rc を同じ値で返す設計だが、「忠実記録」は保証されない。failure writer は失敗を隠し、final receiptもない。

**一次証拠:** plan は `|| driver_rc=$?` 後に同 rc で終了する [plan.md:247–265](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:247)。一方、再利用予定の `write_failure` は writer 自身の失敗を `|| true` で無視し、書込み前に latch を立てる [certify_calibration.sh:46–75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/certify_calibration.sh:46)。floor collectorを作らず scheduler stdout/stderr・exit statusとの束縛もない [plan.md:280–284](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:280)。

`open(..., "x")` は初回作成の上書きを防ぐだけで、その後の改変・fsync・scheduler exitとの一致を証明しない。job-result writerが失敗した場合、ERR trap が返すのは writer側rcであり元のdriver rcではない。

**放置時:** driver rc=2 の jobが failure/result欠落、別rc、または後編集されたrcとして残り、台帳が実 scheduler 終了状態を忠実に表さない。

### A-12 / MUST

**主張:** DW-S03 の層被覆が不足する。preflightで新設する条件の一部が、実際に効くjob/driver層で再検査されない。

| 条件 | submit | job/driver | 欠落 |
|---|---|---|---|
| claims mode 0700 | 検査 | driverはsymlink/dirだけ | mode変更TOCTOU |
| script SHA | repo fileをhash | 同じrepo fileをhash | spool bytes不在 |
| walltime | policy値 | policy値をenv化 | scheduler実limit不在 |
| 4 preflight | login時のみ | 再検査なし | queue/budget/quota変化 |
| reservation/claim production consumer | 静的テスト | 現CLI rc=2で到達不能 | 本waveでは発火しない |

**一次証拠:** driver が claims mode を検査しないことをplan自身が明記 [plan.md:71–75](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:71)、TOCTOUリスクも認識済み [同:386](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/plan.md:386)。実 driver は directory/symlinkしか見る [s8b_floor_campaign.py:2823–2833](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:2823)。現CLIは protocol/reservation/claimより前にrc=2 [同:3432–3444](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/campaign/s8b_floor_campaign.py:3432)。

**放置時:** wrapper artifact は生成できても、claims・reservation・script bindingがproduction consumerで効くことを一度も確認せず、次waveの admission 入力として扱われる。

## 親 brief P1〜P8 の裁定

| 項目 | 裁定 | 攻撃結果 |
|---|---|---|
| P1 | **支持（scope境界のみ）** | wrapper-only、admission/CLI/certificate/resume延期はD86どおり。ただしA-01〜A-12はwrapper scope内の欠陥であり、段階3/4を実装せよという指摘ではない。 |
| P2 | **否定** | dry-run完了は設計正本の実job ID条件と矛盾し、恒真化している。 |
| P3 | **否定（現案）** | schema分離自体は妥当だが、ancestor symlink、後編集、replay、actor不在によりjob-scoped authorization artifactとして成立しない。 |
| P4 | **否定（無条件主張として）** | honest current codeならrc=2伝播案は妥当。しかしspool/PATH/interpreterを閉じず、record writer失敗も隠すため「必ず忠実記録」は成立しない。 |
| P5 | **否定（29400の確定pin）** | 算術上は初回 `Δ≤600` なら通るが、startup/driver overheadの実測保証がなく、scheduler実limitにも束縛されない。 |
| P6 | **否定** | mode0700はsubmit層だけ、内容・owner・ACL・ancestor・raceを閉じず、driver層でmode再検査しない。 |
| P7 | **支持（編集競合の観点のみ）** | ファイル所有は素集合。ただしAがproducer・policy・testを同時所有し、B scriptとの統合依存があるため独立保証には数えられない。 |
| P8 | **否定** | start/hostはqstat由来だが、最重要の`REQUESTED_S`はscheduler実値でなくpolicy自己申告。途中recheckも29400の残時間を無条件には保証しない。 |

段階3の admission predicate、段階4のCLI変更は本裁定では要求していません。必要なのは、wrapper-only wave自身の実行bytes・実scheduler値・create-only containment・replay/rc境界を閉じ、dry-runを完了条件から外すことです。

**総合判定: NO-GO**
---

## lensB

# 総合判定: NO-GO

算術そのものは合っています。しかし、`floor_walltime_s=29400` を正当化する「900 秒/セル」「145 秒/attempt」が実装上のハード上限ではありません。また親 brief の P2 は、設計正本が要求する実 qsub artifact を次 wave に先送りしています。

したがって、wrapper の実装着手は可能でも、現案のまま「段階 1 完了」と判定することはできません。今回テストは実行しておらず、以下はソースと既存実 smoke/calibration 成果物の静的監査です。

## 所見

### B-01 / BLOCKER

主張: 親 brief の P2 は設計正本の段階 1 完了条件を弱めています。dry-run の synthetic ID は DW-G04 の発火根拠にならず、実 qsub と job-scoped artifact の確認を次 wave に送ってはいけません。

一次証拠:

- `brief.md:48-49` は dry-run submission artifact だけで完了し、実 qsub を次 wave に送る。
- `plan.md:352` 自身も、実 qsub artifact が人間実行 gate だと認める。
- `output/insights/2026-07-25_t088-official-unlock-design.md:99-105` は、wrapper path と実 submit artifact ID が一度生成・確認されることを段階 1 の完了条件とする。
- `docs/dev-wave/core.md:51-54` は、既存 artifact path/measurement ID を名指せない条件付き機能を発火させない DW-G04 を定める。
- `docs/decisions.md:3726-3732` も wrapper-first の後に人間の明示 qsub と job-scoped artifact を要求する。

成果物影響: synthetic submission を実在 artifact と扱うと、後続の受理集合・台帳が存在しない PBS job ID と reservation 参照を持ち、official accepted set の根拠が壊れます。

### B-02 / BLOCKER

主張: `29400 s` は数式上は正しい一方、現実の hard envelope ではありません。プランが前提にする build 900 秒/セルと attempt 145 秒は、実装上の timeout 構造と一致しません。

一次証拠:

- `plan.md:34-44` は `28200 + 600 + 600 = 29400` を導出する。
- `orchestrator/campaign/s8b_floor_campaign.py:165-175` は build 900、verify 120、finalize 600 を定数化する。
- `orchestrator/campaign/s8b_floor_campaign.py:640-677` はセル当たり build 900 を一回、attempt 当たり `5*5+120=145` として計上する。
- `orchestrator/campaign/s8b_floor_campaign.py:962-981` は build cache に `timeout_s=900` を渡す。
- しかし `orchestrator/campaign/buildcache.py:498-503` は configure と build の各 subprocess に個別に 900 秒を適用する。つまり build 部分だけでほぼ 1800 秒になり得る。
- `orchestrator/calibrator/runner.py:395-405` の既定 timeout は 120 秒で、`orchestrator/calibrator/runner.py:434-450` はこれを rep ごとに最大 5 回繰り返す。
- `orchestrator/campaign/s8b_floor_campaign.py:731-756` の pre/post probe も各 120 秒である。

成果物影響: PBS walltime kill により `job-result.json`、final record、trial ledger が欠落し、certified 選択が生存セルだけに偏るか、受理集合が空のままになります。

### B-03 / MUST

主張: 予約境界の算術は、初回 preflight と途中再検査の双方でぎりぎりです。`29400` なら scheduler start から初回検査まで 600 秒以内でなければならず、その 600 秒は未実測です。途中検査も B-02 の過小な attempt cap に依存しています。

一次証拠:

- `orchestrator/campaign/reservation.py:210-215` は `required_s + finalize_margin_s` を要求する。
- `orchestrator/campaign/reservation.py:253-259` は予約開始からの実 wallclock を差し引く。
- `orchestrator/campaign/s8b_floor_campaign.py:2771-2791` が開始直後の検査を行う。
- `orchestrator/campaign/s8b_floor_campaign.py:2002-2022` が途中の `_recheck_reservation_before_measurement` を行う。
- `orchestrator/campaign/s8b_floor_campaign.py:2034-2037` は session ごとにその再検査を呼ぶ。

検算:

- 1セル: `900 + 10*(25+120) = 2350 s`
- 12セル: `2350*12 = 28200 s`
- finalize reserve 込み: `28800 s`
- requested `29400 s` との差: `600 s`

成果物影響: 起動・staging・build が想定より長い場合、初回または途中で reservation-lost となり、その後の値・trial record・受理対象が生成されません。

### B-04 / MUST

主張: REMAIN `437.95` だけでは 8時間10分の予算妥当性を証明できません。ポイント単位と gen_S の node-hour 課金率が一次資料にありません。

一次証拠:

- `output/env/pegasus/calibration/attempts/submissions/5875-38d28f18d032/rbudgetcheck.stdout:1-4` に `REMAIN 437.95` がある。
- `output/insights/2026-07-18_env-contract-pegasus-consultations.md:712-716` は、残ポイントだけでは足りず、gen_S 課金則、最大 walltime、build cap、retry budget が必要だと記録する。
- 現行 preflight は `tools/pegasus/submit_certify.sh:120-124` のようにコマンド成功を確認するだけで、残量閾値を判定しない。

仮に 1 point/node-hour なら `1*8.1667 = 8.1667 points` で十分ですが、この換算は未確認です。さらに retry 回数を含める必要があります。

成果物影響: 途中で予算不足になると再試行不能になり、欠落 trial や未完了 ledger を残したまま certified 選択が止まります。

### B-05 / NIT

主張: `qstat -f` の実フィールドは存在します。ただし一次資料で確認できる表記は NQSV 固有の `Execution Hosts(JSVNO)` と `Started Request Time` です。別名候補は互換 fallback としてのみ扱うべきです。

一次証拠:

- `output/env/pegasus/smoke/0:867860.nqsv/qstat_job.stdout:34` に `Started Request Time`。
- 同 `:50-51` に `Execution Hosts(JSVNO):` と `bnode003(3)`。
- `output/env/pegasus/smoke/0:867861.nqsv/qstat_job.stdout:34,50-51` と `0:867862.nqsv/...` にも同型記録がある。
- `tools/pegasus/certify_calibration.sh:248-293` はこの NQSV 表記を解析し、`tools/pegasus/certify_calibration.sh:295-318` で fail closed する。
- `plan.md:207-216` は複数 alias を列挙している。

成果物影響: 実表記を検査せず alias の文字列テストだけにすると、reservation の host/start が空になり、job-scoped 成果物を受理できません。

### B-06 / SHOULD

主張: `PBS_JOBID`、`PBS_O_WORKDIR`、`/scr` は実 smoke で確認済みです。`boot_id` は smoke ではなく実 calibration 成果物でのみ確認できます。親 brief はこの証拠の区別を維持すべきです。

一次証拠:

- `output/env/pegasus/smoke/0:867860.nqsv/scratch.stdout:1-6` に `PBS_JOBID=0:867860.nqsv`、実 worktree の `PBS_O_WORKDIR`、`/scr` の exists/dir/writable がある。
- `tools/pegasus/smoke_probe.sh:88-107` は `/scr` write canary を作成・削除する。
- `tools/pegasus/certify_calibration.sh:15-31` は PBS 変数を必須化し、colon-free の `/scr/<jobid>` を作る。
- `output/env/pegasus/calibration/job-staging/0:867874.nqsv/reservation.json:2-10` は実 `boot_id`、host、job ID、requested walltime、start epoch を持つ。
- producer は `tools/pegasus/certify_calibration.sh:320-340`、consumer は `orchestrator/campaign/reservation.py:178-187,237-251`。

成果物影響: `boot_id` を「smoke 確認済み」と誤記すると証明参照が誤り、再起動跨ぎを拒否した reservation の由来を台帳から追えなくなります。

### B-07 / MUST

主張: floor policy key は現在まだ存在しません。一方、floor protocol/freeze field は実在し、12 cells/96 schedule の導出も既存テストにあります。policy の追加は両 wrapper とテストを同一 commit で揃える必要があります。

一次証拠:

- `tools/pegasus/policy.json:1-20` に `floor_walltime`、`floor_walltime_s` はない。
- `plan.md:27-32` が両 key の新設を提案する。
- `output/s8b-freeze/floor_protocol.json:1` は 18 field を持つ。
- `orchestrator/campaign/s8b_floor_contract.py:34-41,104-125` が exact key set を検査する。
- セルと schedule の導出は `orchestrator/campaign/s8b_floor_contract.py:309-355,380-395`。
- 既存テスト `orchestrator/tests/test_s8b_floor_campaign.py:757-781` が 12 cells/96 schedule を既に検査する。

成果物影響: policy の string/seconds が submit/job 間でずれると PBS request と reservation が異なる値を持ち、job ID に結びつく受理根拠が失われます。

### B-08 / SHOULD

主張: 本 wave で作るべきでないものは、floor final receipt collector、新共通 module、汎用 schema、selector/certification/resume、admission predicate、CLI 変更です。逆に欠かせないのは real-qsub acceptance、claims provisioning、job-scoped result/failure、qstat/reservation の動的検査です。

一次証拠:

- `plan.md:280-284` は floor collector を作らない。
- `tools/pegasus/collect_receipt.py:107-141` は calibration 固有の attempt/acquisition/`calibrate_rc` を要求し、floor には流用できない。
- `brief.md:17-18` と `brief.md:21-30` は official guard/CLI/既存3 script を変えない。
- `docs/decisions.md:3737-3739` は大きな共通機構を延期する。
- `plan.md:295-296` の 12/96 テストは既存の `orchestrator/tests/test_s8b_floor_campaign.py:757-781` と重複する。

成果物影響: 汎用化を混ぜると既存 calibration の受理集合まで変更し得ます。反対に real-qsub acceptance を欠くと、floor 用参照 ID が台帳に一件も存在しません。

段階 3 admission predicate と段階 4 CLI は明確に scope 外です。B-02 の driver budget 修正も本 wrapper wave に混ぜず、段階 3 前の独立 prerequisite とするべきです。

### B-09 / SHOULD

主張: 今回は `certify_calibration.sh` との意図的重複を許容すべきです。現時点で共通化すると I6 違反か、floor しか使わない新 module のどちらかになります。

一次証拠:

- `certify_calibration.sh` は 768 行、30,345 bytes。
- `plan.md:159-233` が参照する PBS/staging/failure/policy/source-binding/qstat/reservation の範囲は合計 309 行、11,574 bytes、元 script の約40.2% LOCです。
- 対象実装は `tools/pegasus/certify_calibration.sh:15-93,105-208,210-340`。
- `brief.md:28-29` の I6 は既存3 script の挙動を変えない。

判断: 今回はコピーを許容し、コピー元 commit/range のコメントと実 qstat fixture による差分テストを置くべきです。実 floor artifact が一件でき、二つ目の生きた consumer になった後に共通化を再検討します。

成果物影響: 出典なしのコピーは将来 parser が分岐し、同じ PBS job が calibration では受理、floor では拒否される保守負債になります。

### B-10 / MUST

主張: プランの static anchor テストだけでは恒真化しやすく、dry-run も副作用ゼロではありません。一時 repo の成立条件を明示した動的テストが必要です。

一次証拠:

- `plan.md:297-303` は主要 shell fragment を文字列で確認するテストを多く提案する。
- `plan.md:65` は dry-run でも submission staging と claims を作る契約である。
- 既存の一時 repo パターンは `orchestrator/tests/test_pegasus_tools.py:1005-1033` にあり、git init、identity、add/commit、`--repo-root`、外部 attempts-root を設定する。
- 現在 `output/claims` は存在せず、`tools/pegasus/README.md:121-125` は事前 provision と mode 0700 を要求する。
- driver は `orchestrator/campaign/s8b_floor_campaign.py:2821-2844` で claims dir の存在を要求し、自らは作らない。

必要条件:

- temp repo に `output/` 自体を事前作成する。
- 新 script と policy を tracked・executable にする。
- sentinel `qsub/qstat/rbudgetcheck` を置き、dry-run で呼ばれないことを動的に確認する。
- 実 `qstat_job.stdout` fixture から host/start/reservation を生成する。
- stub driver の rc 0/2/7 を job-result/failure/PBS exit に伝播させる。
- 全書き込み先が temp 配下であることを検査する。

成果物影響: 文字列だけの緑では qsub 抑止、receipt 順序、rc 伝播が壊れた実装を通し、存在しない submission 参照をレポートへ持ち込みます。

### B-11 / MUST

主張: P7 の編集ファイル集合は衝突しませんが、独立並行 ownership としては成立しません。A のテストが B の job script を必要とし、B の PBS directive が A の policy 値を消費します。

一次証拠:

- `brief.md:57-58` は A/B 分割を提案する。
- `plan.md:323-352` は A に submit/policy/test、B に job script を割り当てる。
- `plan.md:127-155` の job header は policy walltime を固定して生成する設計である。
- `plan.md:286-321` の統合テストは両 script を検査する。

成立する依存順序は、親による interface/walltime 固定 → B の job script → A の submit/policy → 親または A の統合テスト、です。A は B が存在する前に「完了」できません。

成果物影響: 順序を無視すると policy と PBS directive の不一致を含む commit が生まれ、receipt の requested walltime と scheduler request が異なります。

### B-12 / MUST

主張: 現時点の実 qsub は無意味ではありません。ただし確認できるのは wrapper plumbing だけであり、floor campaign 実行や 8時間 envelope の証明にはなりません。

一次証拠:

- official CLI は `orchestrator/campaign/s8b_floor_campaign.py:3432-3441` で protocol load より前に rc 2 で拒否する。
- protocol load/run は同 `:3443-3452`。
- core guard は同 `:193-203`。
- `plan.md:267-278` は rc 2 を期待される failure として記録する。

実 qsub で確認できるもの:

- qsub response と raw PBS job ID
- PBS identity、`PBS_O_WORKDIR`、`/scr`
- pre-submit receipt の先行作成
- qstat host/start parser
- reservation export
- source hash
- rc 2 の job-result/failure/PBS exit 伝播

確認できないもの:

- protocol load、reservation consumer
- claim acquisition
- build・measurement
- 12 cells/96 schedule
- `29400 s` の実効性

成果物影響: rc 2 job を「floor 実行成功」と表示すると、accepted set は空なのにレポートや台帳だけが成功を主張します。

### B-13 / MUST

主張: README、phase doc、worklog は実装済みと実 artifact 確認済みを分けて更新すべきです。過去 entry は変更禁止です。

一次証拠:

- `tools/pegasus/README.md:121-139` は claims 契約と現在の「次 wave」状態を記す。
- `docs/phase3.md:100-102` は wrapper 未実装と artifact 条件を現在 checkpoint として記す。
- `docs/worklog.md:12-20` は過去 entry の凍結規則を定める。
- `docs/worklog.md:1088-1093` は現在の次手を記録する。
- `output/insights/2026-07-25_t088-official-unlock-design.md:60-74` の B-11 も docs の同期を要求する。

更新箇所:

- `tools/pegasus/README.md` §4: dry-run、実 submit、生成 path、rc 2 の意味、`collect_receipt.py` 非使用を追記。
- `docs/phase3.md:100-102`: wrapper 実装済み／実 artifact 未確認、または確認済みを事実に応じて更新。
- `docs/worklog.md`: 末尾へ新規 entry を追加。wrapper commit と human qsub artifact を別項にする。
- 過去 worklog entry と凍結済み insight/decision 本文は書き換えない。

成果物影響: docs を先に「完了」にすると、存在しない job ID・receipt path が正式な受理参照として後続作業へ伝播します。

## 親 brief P1〜P8 の裁定

| 裁定 | 支持/否定 | 理由 |
|---|---|---|
| P1 | 否定 | 4成果物と scope 除外は概ね妥当だが、実 qsub acceptance が欠け、12/96 テストが重複する。 |
| P2 | 否定 | BLOCKER。dry-run だけで段階 1 を閉じるのは設計正本と DW-G04 に反する。 |
| P3 | 支持 | calibration collector を流用せず、floor 固有 schema/path に限定する判断は正しい。汎用 schema 化しないこと。 |
| P4 | 条件付き支持 | rc 2 を忠実に記録することは wrapper smoke として有効。ただし campaign 成功・walltime 検証とは表示しない。 |
| P5 | 否定 | key 追加は必要だが、`29400` の根拠が hard cap になっていない。値を production envelope として凍結できない。 |
| P6 | 支持 | claims は driver が自作しないため必須。0700 provision は運用契約に合う。 |
| P7 | 否定 | ファイル衝突はないが、B → A統合テストの依存があり、独立完了可能な分割ではない。 |
| P8 | 条件付き支持 | `REQUESTED_S` は policy の scheduler request をそのまま使うべきで、qstat host/start も実在する。ただし値は P5 解決後に固定する。 |

## 人間が実際に行う順序

まず wrapper-only 実装と dry-run テストを終えます。AI が確認できるのは temp repo 上の dry-run、fixture を使う parser/rc 伝播、shell syntax、静的検査までです。

Pegasus 上では人間が次を実行します。

```bash
cd /home/SFC/tanab/github/izanagi

git rev-parse HEAD
git status --porcelain --untracked-files=all -- . ':(exclude)output'

qstat -Q
qstat -Q -f gen_S
pegasusinfo
rbudgetcheck
check_quota

tools/pegasus/submit_floor.sh --dry-run
```

`--dry-run` も staging/claims を作るため、副作用ゼロではありません。AI テストでは必ず一時 repo を使います。

dry-run の receipt、policy 値、claims mode を確認した後、人間が明示的に scheduler action を承認します。

```bash
tools/pegasus/submit_floor.sh
```

生の `qsub tools/pegasus/floor_campaign.sh` は pre-submit receipt を迂回するため使いません。人間による submit wrapper の実行が、内部 qsub の明示承認です。

表示された ID を使って確認します。

```bash
request_id='867xxx.nqsv'
raw_job_id="0:${request_id}"

qstat -f "${request_id}"
```

終了後に、wrapper が表示した nonce/path を用いて以下を確認します。

```bash
python3 -m json.tool \
  "output/env/pegasus/floor/attempts/submissions/${nonce}/submit-receipt.json"

python3 -m json.tool \
  "output/env/pegasus/floor/job-staging/${raw_job_id}/reservation.json"

python3 -m json.tool \
  "output/env/pegasus/floor/job-staging/${raw_job_id}/job-result.json"

python3 -m json.tool \
  "output/env/pegasus/floor/job-staging/${raw_job_id}/failure.json"
```

期待値は driver rc 2 と official guard failure です。これを段階 1 の wrapper smoke artifact として記録した後、B-02 の budget/envelope 修正を独立 prerequisite wave で扱い、その後に scope 外の段階 3 admission、さらに段階 4 CLI へ進む順序が妥当です。
---

## implB

実装子 B の担当を完了しました。

- 作成: [tools/pegasus/floor_campaign.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:1)
- 872 行、mode `0755`
- 所有外ファイルの変更なし
- `git add` / `git commit` / `qsub` は未実行

### 検査

- `bash -n tools/pegasus/floor_campaign.sh`: 成功（対象範囲: 全 872 行）
- floor 専用 pytest nodeid: なし（実装子 A のテスト未作成につき 0 件）
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `shellcheck`: 環境に存在しないため未実行

### 裁定 v2 対応

| 項目 | 実装行 |
|---|---|
| A-02 | 実行 bytes と receipt: [387–401](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:387)、repo bytes の独立照合: 403–410、HEAD/clean: 413–430 |
| A-03 | env unset・interpreter realpath/version・固定 `-E -s -B` argv: [810–826](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:810) |
| A-07 | qstat raw、host/start、実 limit/remaining parse・記録・policy 照合: [433–589](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:433) |
| A-09 | output containment・全 component symlink 検査・create-only staging: [33–102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:33)、receipt path/copy: 224–281 |
| A-10 | strict receipt と normalized `job_id` / `PBS_JOBID` 照合: [284–369](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:284) |
| A-11 | failure writer の rc 保全: [104–157](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:104)、job-result と driver rc 忠実伝播: 821–872 |
| §3 | compiler 記録、pinned-clean gflags→glog static/PIC build、prefix 上書き記録/export: [632–809](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:632) |

### 所有外への静的波及

- `tools/pegasus/submit_floor.sh`: nonce のみを渡し、実装した exact receipt schemaを生成する必要あり。
- `tools/pegasus/policy.json`: 実装子 A による `floor_walltime_s=36000` 等の追加前は、job は policy 段で fail-closed。
- `orchestrator/tests/test_pegasus_floor_tools.py`: 実装子 A が caller、qstat fixture、rc 0/2/7、変異点を検査する予定。
- `orchestrator/campaign/reservation.py`: export した exact 8 環境変数の consumer。
- `orchestrator/campaign/s8b_floor_campaign.py` と凍結 protocol: 固定 argv の consumer/input。変更なし。
- 親所有の README・phase・worklog・handoffは指示どおり未変更。

B の担当範囲内で未実装項目はありません。実投入・統合テストは、A の policy/caller/test 作成後および人間による `qsub` 手番に残ります。
---

## implA

実装完了です。official driver の受理集合は空集合のまま変更していません。guard／CLI／campaign は未編集で、wrapper 側に fail-closed 条件だけを追加しました。

### 変更ファイル

- [submit_floor.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:1) — 新規 417行、mode 0755
- [policy.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/policy.json:9) — 22行、指定の2 keyのみ追加
- [test_pegasus_floor_tools.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1) — 新規 639行

実装子 B の [floor_campaign.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:1) は読み取り・検査のみで、編集していません。docs、campaign、既存テストも未変更です。

### テスト結果

- `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_shell_syntax[submit_floor.sh]` ～ `::test_floor_driver_failure_propagates_rc[rc-7]`
  - 全32 nodeid: **32 passed**
- `orchestrator/tests/test_pegasus_tools.py::*`
  - 既存全52 nodeid: **52 passed**
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- 両 shell の `bash -n`: 成功
- `git diff --check`: 成功

中間実走では `test_floor_job_exports_exact_reservation_fields` が1件赤でした。テスト側 regex が `SCRIPT_SHA256` の数字を許していなかったためで、期待赤でも製品回帰でもないテスト実装不備です。修正後の最終結果は上記の全件緑です。

### 所有外への静的波及面

- `policy.json` の既存 consumer は `submit_certify.sh`、`certify_calibration.sh`、既存 `test_pegasus_tools.py`。いずれも named key 読みで、key 追加による exact-key 破壊はありません。
- floor receipt の直接 consumer は `floor_campaign.sh`。schema、nonce、job ID、source、requestを再照合します。
- reservation export は `reservation._ENV_FIELDS` の8件と exact 一致させています。
- freeze/protocol と `s8b_floor_campaign.py` の純関数はテストからread-only利用しています。
- README／phase／worklog の更新と、実 `dry_run:false` artifact の確認は親・人間手番です。
- 将来の admission consumer は、この成果物を authorization ではなく submission record として扱う必要があります。

### 変異 M1〜M10

| 変異 | killする nodeid |
|---|---|
| M1 | `test_floor_policy_covers_derived_reservation_envelope` |
| M2 | `test_floor_pbs_directives_match_policy` |
| M3 | `test_floor_job_binds_executing_script_bytes` |
| M4 | `test_floor_job_binds_scheduler_elapse_limit` |
| M5 | `test_floor_job_hardens_interpreter` |
| M6 | `test_floor_driver_failure_propagates_rc[rc-0/rc-2/rc-7]` |
| M7 | `test_submit_floor_qsub_exports_nonce_only` |
| M8 | `test_submit_floor_rejects_unsafe_existing_claim_root[symlink]` |
| M9 | `test_floor_job_exports_build_prefix_path` |
| M10 | `test_submit_floor_rejects_overrides_in_real_submission[repo-root]` |

割当 scope 内の未実装項目はありません。裁定どおり実 `qsub` は実行しておらず、段階1は実 artifact 確認まで OPEN です。`git add`／`git commit` も実行しておらず、実 repository の `output/` への書き込みもありません。
---

## rev1

## 所見

### R1-01 / must-fix

**主張:** 非 dry-run の固定 root と「実 qsub」の双方を caller の command namespace から迂回できる。`BASH_SOURCE[0]` 自体を realpath・regular-file 検証せず、上書き可能な `dirname`/`pwd` から root を作るため、別 repo 内の tracked symlink や exported function で任意 repo を既定 root にできる。さらに `qsub` も PATH/function 解決なので、fake が rc=0 と単一 ID を返せば scheduler job がなくても `dry_run:false` receipt ができる。これは authorization 化の要求ではなく、submission record の事実性の欠陥である。

**一次証拠:** [submit_floor.sh:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:14)、[submit_floor.sh:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:60)、[submit_floor.sh:348](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:348)、[submit_floor.sh:360](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:360)、[submit_floor.sh:400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:400)

**成果物影響:** submission 台帳の `source_commit`、`job_script_sha256`、`job_id`、`dry_run=false` が任意値になり、実 PBS job が存在しない記録が残る。

### R1-02 / must-fix

**主張:** A-02 の「repo blob 二重照合」は未実装。両側とも working-tree file を hash しており、Git object を一度も読んでいない。`ls-files` は追跡有無しか示さない。`assume-unchanged` / `skip-worktree` を付けた job script を改変すれば、clean 判定、receipt hash、`$0` hash、repo hash がすべて改変 bytes で一致する。

**一次証拠:** [submit_floor.sh:166](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:166)、[submit_floor.sh:185](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:185)、[submit_floor.sh:189](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:189)、[floor_campaign.sh:382](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:382)、[floor_campaign.sh:387](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:387)、[floor_campaign.sh:403](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:403)

**成果物影響:** receipt が示す commit blob と異なる script が report/job-result を生成でき、選択値や台帳値を未レビュー code 由来に差し替えられる。

### R1-03 / must-fix

**主張:** A-03 の硬化が遅すぎる。`unset` より前に多数の裸 `python3` を実行し、receipt validation、qstat parse、reservation 記録まで任せている。`PYTHONPATH` の `sitecustomize.py` や fake `python3` が先に実行されるため、後段の `-E -s -B` は既に破られた検査を救わない。さらに `$PY` 自体も ambient PATH から選び、version を記録するだけで信頼済み実体と照合しない。

**一次証拠:** [floor_campaign.sh:285](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:285)、[floor_campaign.sh:445](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:445)、[floor_campaign.sh:787](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:787)、[floor_campaign.sh:810](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:810)、[floor_campaign.sh:811](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:811)、[floor_campaign.sh:822](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:822)

**成果物影響:** real driver/guardを一度も起動せず `driver_rc=0` や任意 report を捏造でき、同権限で frozen bytes まで改変できる。

### R1-04 / must-fix

**主張:** A-07 は qstat の文字列表記を検査するだけで、「scheduler 実値」の出所を束縛していない。`timeout`、`qstat`、`hostname`、parser 内の `date` は ambient PATH 由来。fake qstat が host・start・`Max: 36000S`・remaining を返せば、実 allocation が別値でも全条件を通る。

**一次証拠:** [floor_campaign.sh:436](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:436)、[floor_campaign.sh:445](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:445)、[floor_campaign.sh:491](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:491)、[floor_campaign.sh:575](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:575)、[floor_campaign.sh:589](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:589)

**成果物影響:** `reservation_requested_s` と deadline が実 scheduler 値でなく 36000 と記録され、短い allocation では途中 kill により report/台帳が欠落・部分化する。

### R1-05 / must-fix

**主張:** A-09 の component 検査は TOCTOU。`-L` と `realpath` を pathname で検査した後、directory fd を保持せず `mkdir -p`、redirection、Python `open()` を行う。新規 0700 leaf を最終検査後に同一 uid が symlink へ交換すれば、`noclobber`/`"x"` は leaf file の上書きしか防げず、親 symlink を追う。

**一次証拠:** [floor_campaign.sh:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:51)、[floor_campaign.sh:80](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:80)、[floor_campaign.sh:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:93)、[floor_campaign.sh:259](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:259)、[submit_floor.sh:210](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:210)、[submit_floor.sh:232](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:232)、[submit_floor.sh:248](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:248)

**成果物影響:** receipt/job-staging 台帳を containment 外へ出せるほか、`output/s8b-freeze/` に未知 record を追加して launch clean-scan の受理集合を空にできる。

### R1-06 / must-fix

**主張:** 防壁テストが壊れた実装を緑にする。

- `test_floor_job_binds_repo_blob_hash` は Git blob でなく working-tree `sha256sum` を正解としている。
- M8 fixture の symlink target は現環境 umask `0022` では 0755。symlink 検査を削除しても production の mode 検査で rc=2 になり、test は拒否理由を見ないため緑のまま。
- qstat fixture は 7200 を期待するため、parser を 7200 固定にしても parser test と presence test が通り、実 floor job だけが 36000 不一致で落ちる。
- `_driver_tail()` は receipt/A-10 より後だけを切り出すため、job ID 一致検査を削除しても動的 rc test は通る。
- gflags/glog test は export 文字列だけを見る。build block 全体を削っても静的 test は通り、実 job は未定義変数または dependency 不在で落ちる。

**一次証拠:** [test_pegasus_floor_tools.py:217](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:217)、[test_pegasus_floor_tools.py:251](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:251)、[test_pegasus_floor_tools.py:462](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:462)、[test_pegasus_floor_tools.py:472](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:472)、[test_pegasus_floor_tools.py:560](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:560)、[test_pegasus_floor_tools.py:585](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:585)、[floor_campaign.sh:328](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:328)

**成果物影響:** stale job receipt・symlink claims・固定 7200 parser・dependency 無し job がテストを通過し、台帳の job ID/claim path が誤るか floor report が生成されない。

### R1-07 / nit

**主張:** A-11 の通常 rc 捕捉とは別に、driver 起動前の redirection failure も `driver_rc` として記録する。また INT/TERM/HUP をすべて rc=128へ潰している。

**一次証拠:** [floor_campaign.sh:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:149)、[floor_campaign.sh:152](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:152)、[floor_campaign.sh:821](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:821)、[floor_campaign.sh:852](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:852)

**成果物影響:** driver 未実行でも `driver_rc=1`、TERM/HUP/INT でも failure 台帳の `rc=128` となり、失敗分類値が実際とずれる。

### R1-08 / backlog

**主張:** job 側 clean check は `git status` の実行失敗を clean と扱う。command substitution の rc は `[[ -n ... ]]` に捨てられる。これは A-01 の承認 revision 束縛本体に属するため must-fix には数えない。

**一次証拠:** [floor_campaign.sh:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:428)

**成果物影響:** Git index/read error 時に dirty driver bytes が receipt の commit 下で動き、report の選択値が別 source 由来になりうる。

### R1-09 / nit

**主張:** 新規 test file は自走 harness を持たず、pytest-only allowlist にもない。素の `python3 test_pegasus_floor_tools.py` は 0 test 成功になり、既存 meta-test 規律上の offender である。

**一次証拠:** 新規ファイル末尾 [test_pegasus_floor_tools.py:639](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:639)、既存規律 [test_plain_runner_coverage.py:60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_plain_runner_coverage.py:60)

**成果物影響:** 直接の成果物値変更はないが、素の runner の検査証拠が 0 件実行のまま成功になる。

## 境界確認

- `policy.json` は 2 key 追加だけで、既存 `submit_certify.sh` / `certify_calibration.sh` / `test_pegasus_tools.py` は named-key 読み。既存 key 破壊は見当たらない。
- 現差分は FROZEN_MANIFEST 23 件や既存 Pegasus scripts を変更していない。ただし実行時には R1-03/R1-05 の経路から凍結領域を壊せる。
- 新規 tests の書込み先は source audit 上 `tmp_path` 配下で、実 repo `output/` への直接 write は見当たらない。
- A-10 の normalized 比較、A-11 の通常 driver rc 伝播、gflags/glog build と `CMAKE_PREFIX_PATH` export の文字列自体は存在するが、上記 bypass と偽緑を解消していない。
- 段階 3 admission、段階 4 CLI、floor collector、driver 定数修正など scope 外項目は must-fix にしていない。
- pytest は指示どおり未実行。緑は主張しない。ファイル変更も行っていない。

**総合判定: NO-GO — must-fix 6 件。**
---

## rev2

# 総合判定

**NO-GO — must-fix 6件。**

pytest、wrapper、qsub は実行していない。以下の「赤になる／生存する」は、実装とテスト分岐を追跡したコード判定であり、変異実測ではない。

## M1〜M10 検出力

| 変異 | コード判定 | 根拠 |
|---|---|---|
| M1 `floor_walltime_s=28800` | 赤になる | `test_...envelope`: `28800 > 28200+600` が偽。さらに時分秒との一致検査も落ちる。test:204–205 |
| M2 PBSを08:00:00へ | 赤になる | directiveをpolicyの10:00:00とexact比較。test:177–186 |
| M3 `$0` hash照合削除 | exact削除なら赤。ただし文字列presenceのみ | test:208–214。分岐を`false && [[ ... ]]`にして文字列を残せば生存する。 |
| M4 scheduler limit照合削除 | exact削除なら赤。ただし文字列presenceのみ | test:225–232。parser fixtureは照合分岐を実行しない。 |
| M5 裸の`python3`へ | exact置換なら赤。ただし主にpresence | test:243–248。汚染した`PYTHONPATH`等を注入する動的負例はない。 |
| M6 rc 2→0 | 赤になる | rc 0/2/7を実際のstub driverから注入し、shell rcとJSONを検査。test:590–638 |
| M7 qsub export追加 | exact追加なら赤。ただしpresence | test:294–300。元の行を残して`qsub_cmd+=(-v ...)`を追加する同義変異は生存する。 |
| M8 claims symlink拒否削除 | **赤にならない** | symlink component検査を消しても、GNU `stat`を`-L`なしでsymlinkへ掛けるためmodeは700にならず、別のmode拒否でrc=2のまま。test:462–482 |
| M9 prefix export削除 | exact削除なら赤。ただしpresence | test:251–255。直後の`unset CMAKE_PREFIX_PATH`等は生存する。 |
| M10 real override拒否削除 | 赤になる | 拒否を消すとstub preflightへ進みrc=3となり、期待rc=2・診断・副作用なしの各assertが落ちる。test:485–505 |

## 所見

### R2-01 / must-fix — M8は等価変異であり、killできない

claims symlink検査は共通path検査の[`submit_floor.sh:99`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:99)にあるが、これを削除しても[`submit_floor.sh:328`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:328)の`stat -c '%a'`がsymlink自身を検査し、700以外として拒否する。テストは[`test_pegasus_floor_tools.py:462`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:462)で理由を検査せずrc=2だけを見るため、M8を入れても全assertが成立する。

**成果物影響:** 変異レポートの「M8 kill」が偽となり、本waveの検出力台帳・受入判定を誤る。

### R2-02 / must-fix — non-dry-run成功経路が一度も試験されない

成功試験は[`test_pegasus_floor_tools.py:317`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:317)のdry-runだけ。non-dry-run試験はoverride早期拒否か、[`test_pegasus_floor_tools.py:508`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:508)のpreflight失敗で止まる。

例えばreceipt writerの[`submit_floor.sh:409`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:409)を常に`"dry_run": True`とする変異は全既存テストを通るが、実jobは[`floor_campaign.sh:323`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:323)で全件拒否する。qsub応答ID parsing、実引数、qsub時cwdも未試験。

**成果物影響:** real submissionがすべてreceipt検証で停止し、`job-result.json`、floorレポート、試行台帳が生成されない。

### R2-03 / must-fix — submit-receipt producerとjob側validatorが結合試験されていない

job側のstrict validatorは[`floor_campaign.sh:284`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:284)から始まるが、動的テストはqstat parserとdriver tailだけで、ここを実行しない。

したがって、[`floor_campaign.sh:321`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:321)のschema literalを1文字変える変異や、[`floor_campaign.sh:331`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:331)のjob ID照合を削除するA-10回帰は生存する。

**成果物影響:** 前者は正当なreal jobを全拒否し、後者は別jobのsubmission recordを受理集合へ加えてレポートのjob provenanceを誤る。

### R2-04 / must-fix — M3/M4/M5/M7/M9は機能ではなくソース文字列を検査している

[`test_pegasus_floor_tools.py:208`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:208)からの検査は、比較式・診断・起動文字列・export文字列が存在することしか見ない。以下は受理集合または実行結果を変えるが生存する。

- M3/M4の比較を`false && [[ ... ]]`にする。
- M7のexact行を残してqsub配列へ追加の`-v`をappendする。
- M9のexport直後にunsetする。
- hardened invocationを未使用関数へ残し、実起動だけ裸のPythonにする。

同様に[`test_pegasus_floor_tools.py:312`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:312)の`open(...,"x")`件数検査は、特定writerを`w`へ変えても総数に余裕があり検出しない。

**成果物影響:** 不一致script・不一致walltimeを受理するか、Python汚染／依存欠落／上書きでfloorレポートと台帳を欠落・汚染させる。

### R2-05 / must-fix — record writer失敗時のdriver rc保全が未試験

動的rc試験では[`test_pegasus_floor_tools.py:623`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:623)のjob-result writerが常に成功する。製品側の重要分岐は[`floor_campaign.sh:866`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:866)。writer失敗時だけ`exit "$job_result_writer_rc"`へ戻すA-11回帰は検出されない。

**成果物影響:** scheduler最終rcがdriver rcではなくwriter rcとなり、failure台帳がcampaignの真の拒否値を失う。

### R2-06 / must-fix — job-result.jsonとreservation.jsonのexact schemaが未固定

`job-result.json`は[`floor_campaign.sh:849`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:849)で11 keyを書くが、テストは[`test_pegasus_floor_tools.py:628`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:628)で4値しか見ない。`schema_version`、`pbs_jobid`、hash、nonce、epochのkey・型・literalは未検査。

`reservation.json`は[`floor_campaign.sh:610`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:610)で生成するが、テストはexport名集合だけを[`test_pegasus_floor_tools.py:258`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:258)で見る。JSON key・型は一切読まない。

**成果物影響:** 1文字のkey/literal回帰を検出せず、job-result／reservation台帳をconsumerが解釈不能または誤解釈する。

### R2-07 / backlog — 移植出典が不完全でparser分岐が固定化している

[`floor_campaign.sh:643`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:643)は出典を`376-510`とするが、直後のgflags存在・HEAD検査は実際には`certify_calibration.sh@e9b6f69:359-375`由来。`set -Eeuo pipefail`／`umask`の[`floor_campaign.sh:14`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:14)にもblock先頭の出典がない。PBS blockの出典コメントもblock後のline 6にある。

qstat parserはfloorの[`floor_campaign.sh:445`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:445)とcalibrationの`certify_calibration.sh:248`で既に別実装になっている。共通module化は裁定上scope外なのでmust-fixにはしない。

**成果物影響:** 将来NQSV表記へ片方だけ追随すると、同じallocationから異なるstart/deadlineを記録するか、一方だけレポート生成を拒否する。

### R2-08 / nit — 診断変更で赤になるassertと恒真な重複assertがある

次は受理集合を変えない診断文言だけの変更で赤になる。

- [`floor_campaign.sh:399`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:399) → test:214
- [`floor_campaign.sh:576`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:576) → test:232
- [`submit_floor.sh:62`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:62) → test:502

またtest:300の「reservation文字列なし」は直前のexact equalityから論理的に自明、test:346–347の型assertも直前の文字列literal equalityから自明。

**成果物影響:** 受理集合・レポート・台帳値は変わらず、保守時の偽回帰だけが増える。

### R2-09 / backlog — A-04検査はstdout一面しか見ない

レビュー対象内でsubmission recordをauthorizationと呼ぶ実箇所は**0件**。唯一の該当文字列は[`test_pegasus_floor_tools.py:388`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:388)の不在assertで、誤称ではない。

ただしこのassertはstdoutだけで、コメント、stderr、変数名、test名、schema keyを検査しない。

**成果物影響:** 現行成果物への影響はないが、将来のadmission consumerがsubmission recordを認可証拠として扱う呼称回帰を検出できない。

## schema exact照合

現行bytesには、submit-receipt producerとjob consumer間の1文字不一致は見つからなかった。

- `pre-submit.json`:  
  `schema_version, source_commit, job_script_path, job_script_sha256, nonce, prepared_at, request, preflight, dry_run`。producerとdry-runテストは一致。

- `submit-receipt.json`:  
  `schema_version, source_commit, job_script_path, job_script_sha256, job_id, nonce, submitted_at, request, preflight, dry_run`。producer、job側`top_keys`、テスト定数が一致。literalは`pegasus-floor-submit-receipt/v1`。

- `request`:  
  `project:str, queue:str, nodes:int, elapstim_req_s:int`で三者一致。

- `preflight`:  
  `qstat_Q, pegasusinfo, rbudgetcheck, check_quota`、各値は`rc:int, stdout_raw:str, stderr_raw:str`で一致。

- `job-result.json`:  
  現行writerは`pegasus-floor-job-result/v1`を含む11 keyだが、テストは4値のみ。

- `reservation.json`:  
  `job_id, requested_s, scheduler_started_epoch, deadline_epoch, host, boot_id, script_sha256, nonce, recorded_epoch`。環境変数名は`reservation._ENV_FIELDS`と一致するが、JSON schemaのexact検査はない。

## 運用実効性と人間のコマンド列

現在の未コミット状態では、`submit_floor.sh --dry-run`は成功しない。観測したstatusはpolicy変更＋3未追跡ファイルで、[`submit_floor.sh:166`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:166)のdirty検査が最初にrc=2を返す。stagingやclaims作成前に止まる。

commit後、人間が打つ列は次になる。

```bash
cd /home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper

git status --short
git submodule status -- external/ccbench
git -C /home/SFC/tanab/github/gflags rev-parse HEAD
git -C /home/SFC/tanab/github/gflags status --porcelain --untracked-files=all
git -C /home/SFC/tanab/github/glog rev-parse HEAD
git -C /home/SFC/tanab/github/glog status --porcelain --untracked-files=all

qstat -Q
qstat -Qf gen_S
pegasusinfo
rbudgetcheck
check_quota

tools/pegasus/submit_floor.sh --dry-run
# 表示された submission record を jq 等で確認する

tools/pegasus/submit_floor.sh
qstat -f '<表示された request ID>'
```

詰まり得る箇所は以下。

- real submissionに`--repo-root`等を付けると、同じworktreeを指定しても即rc=2。対象worktree内のwrapperをoverrideなしで実行する必要がある。
- dry-runはscheduler/preflightを一切実行せず、4 captureへ`not run`を書く。10時間分のポイント判断は上記コマンドで人間が先に行う必要がある。
- real qsubは[`submit_floor.sh:361`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:361)でrepo rootへ`cd`して実行され、jobは[`floor_campaign.sh:34`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:34)で`PBS_O_WORKDIR`をrepo rootにする。この組合せ自体はworktree投入を不能にしていない。
- jobは`/scr/<PBS_JOBID>`、10:00:00、`gen_S`、gflags/glogの固定path・pin・clean、qstatの実fieldを前提とする。どれかが欠けるとdriver前に停止する。
- claimsはdry-runでも`output/claims`を0700で作る。現在は未存在。
- 現行official CLIは裁定どおりrc=2で拒否するため、real qsub後もcertified選択やfloor reportは作られない。期待される本wave成果は`dry_run:false`のsubmission/job artifactまでである。

## 副作用監査

I8違反はコード上見つからなかった。

- 書込みrepoは[`test_pegasus_floor_tools.py:96`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:96)の`tmp_path/repo`。
- 実repoの`output/`はprotocol/freezeを読み取るだけ。
- Git設定は`git -C <tmp repo> config`でlocalのみ。`--global`なし。
- PATHは[`test_pegasus_floor_tools.py:137`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:137)で子process用envのcopyだけを書き換え、親processへ漏らさない。
- `~`への明示的書込みなし。

裁定がscope外としたdriver hard-cap化、budget閾値判定、floor final collector、共通parser module化、段階3/4のadmission変更はmust-fixに数えていない。
---

## fixB

実装完了しました。編集は [floor_campaign.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh) のみです。commit、`git add`、`qsub` は実行していません。

## 対応表

| 項目 | 対応 |
|---|---|
| F-B1 | PBS identity 検査直後の 27–39 行へ環境変数 unset と Python 実体解決を移動。全 Python 呼出しを `"$PY" -E -s -B` に統一。実体/version は 180–181 行で staging へ記録 |
| F-B2 | 411–425 行の実行中 bytes 検査を独立維持。443–459 行で `git cat-file blob "$CURRENT_COMMIT:$SCRIPT_RELATIVE_PATH"` を取得し、rc を明示検査してから SHA-256 照合 |
| F-B3 | 84–90 行で resolved path が `output/s8b-freeze/`・`output/campaigns/` 配下なら拒否 |
| F-B4 | 461–470 行で `git status` の出力と rc を別々に捕捉。非 0 は fail-closed |
| F-B5 | 850–869 行で stdout/stderr FD を driver 起動前に create-only で確保し、失敗を `floor_driver_setup` として分離。launch marker を作成。168–178 行で INT=130、TERM=143、HUP=129 を記録・返却 |

裸の `python3` 実行はありません。残る `python3` 文字列は `command -v python3`、診断文、staging ファイル名だけです。

## 検査結果

- `bash -n tools/pegasus/floor_campaign.sh`: 成功
- `python3 -m pytest orchestrator/tests/test_pegasus_floor_tools.py -q -rf`:
  - 32 件中 30 passed / 2 failed
  - 期待赤:
    - `test_floor_job_binds_repo_blob_hash`
      - 旧 working-tree `sha256sum "$REPO_SCRIPT"` を要求。A' が Git blob 検査へ追随する対象
    - `test_floor_job_qstat_parser_accepts_real_nqsv_fields`
      - helper が裸の `python3` marker を検索。A' が hardened invocation へ追随する対象
  - B' 回帰は検出されませんでした。driver rc 動的検査 `test_floor_driver_failure_propagates_rc[rc-0/rc-2/rc-7]` は全件成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功

## 所有外への静的波及

- `submit_floor.sh`: clean commit では receipt hash と commit blob hashが一致し互換。隠蔽された working-tree 改変は job 側で拒否される
- `test_pegasus_floor_tools.py`: 上記2箇所の旧 presence/helper marker は A' の更新が必要
- `reservation.py`: `IZANAGI_RESERVATION_SCRIPT_SHA256` は commit blob hashになるが、フィールド名・型は不変
- `s8b_floor_campaign.py`: argv・公式モード・rc 伝播は不変
- job staging: `floor-driver.launch-attempted` が新たに追加され、起動前 redirection 失敗と launch attempt を区別可能

## 実装しなかったもの

裁定どおり、fake `qsub`/`qstat`・PATH 一般への新規 gate、path TOCTOU 一般、共通 module 化、段階3/4 admission、driver 予算定数は変更していません。所有外の scripts、policy、tests、docs、`orchestrator/`、凍結領域にも触れていません。公式受理集合も拡大・縮小していません。
---

## fixA

実装完了です。編集は許可された 2 ファイルのみで、`floor_campaign.sh`・policy・docs は変更していません。workspace の `git add` / `git commit`、実 `qsub` は未実行です。

### 変更行

- [submit_floor.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:14)
  - snapshot 比: 46 行追加 / 6 行削除
  - 自己パス解決、固定位置、protected namespace、Git blob hash、claims mode 検査を修正
- [test_pegasus_floor_tools.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:18)
  - snapshot 比: 556 行追加 / 16 行削除
  - 44 nodeid、自走 harness と動的結合・schema テストを実装

### F-A1〜F-A9

| 項目 | 対応 |
|---|---|
| F-A1 | `_run()` + `__main__` を追加。直接実行時の import path も補正し、素の runner で 44 tests を実行 |
| F-A2 | `git cat-file blob "$SOURCE_COMMIT:$JOB_SCRIPT_RELATIVE"` の rc を捕捉して hash 化。working-tree hash は独立照合として維持 |
| F-A3 | resolved path で `output/s8b-freeze/`・`output/campaigns/` を拒否。両 namespace の動的負例を追加 |
| F-A4 | `BASH_SOURCE[0]` を `realpath -e` で先に解決し、symlink・非 regular file を拒否。非 dry-run は repo 固定位置のみ許可 |
| F-A5 | Git blob hidden-drift、0700 symlink target、36000 qstat policy 経路、receipt job-ID 結合、gflags/glog build block 実行を動的検査。claims の mode 検査は `stat -L` とし、symlink gate 削除変異を等価でなくした |
| F-A6 | stub preflight/qsub の非 dry-run 成功経路を実行。`dry_run:false`、job ID、nonce-only `-v`、qsub cwd、claims 0700 を検査 |
| F-A7 | submit が生成した実 receipt を job strict validator に投入。正しい job ID は通過、別 job ID は拒否 |
| F-A8 | `job-result.json` を事前作成して writer を失敗させ、最終 shell rc が driver rc=7 のままなのを確認 |
| F-A9 | `job-result.json` と `reservation.json` の exact key set・型・literal を固定 |

### 検査結果

指定コマンド:

```text
orchestrator/tests/test_pegasus_floor_tools.py::*   44 passed
orchestrator/tests/test_pegasus_tools.py::*         52 passed
orchestrator/tests/test_plain_runner_coverage.py::*  3 passed
合計                                             99 passed in 3.45s
```

主要追加 nodeid は、Git blob、non-dry-run、protected namespace、qstat policy、receipt round-trip、reservation schema、driver rc、writer failure の各 `test_*`。parameterized nodeid を含め全 44 件成功しています。

追加検査:

- `python3 orchestrator/tests/test_pegasus_floor_tools.py`: 44 passed
- `bash -n tools/pegasus/submit_floor.sh`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: 問題なし

初期赤は次の 3 nodeidでした。

- `test_floor_job_binds_repo_blob_hash`
- `test_floor_job_qstat_parser_accepts_real_nqsv_fields`
- `test_every_test_file_is_self_runnable_or_allowlisted`

途中、自走実行で `ModuleNotFoundError: orchestrator` が 1 件発覚し、import path 補正後に解消。最終赤は 0 件です。

### 所有外への波及

- `floor_campaign.sh` の strict validator・Git blob 契約と整合。bytes は未変更
- `test_pegasus_tools.py` の既存 52 nodeid は全緑
- clean tree では receipt hash 値は従来と同じ。hidden working-tree drift のみ新たに早期拒否
- `stat -L` は先行 symlink gate 後に実行されるため、現行の通常 directory 受理集合は不変
- テスト書込みはすべて `tmp_path`。実 repo の `output/` に副作用なし
- 一時 fixture 内では必要な Git commit と stub `qsub` を実行したが、workspace commit・実 scheduler 投入は未実行

### 実装しなかったもの

裁定どおり、fake qsub/PATH 一般への新 gate、一般 TOCTOU 対策、共通 module 化、段階 3/4、driver 定数、scheduler spool bytes 照合は実装していません。docs/handoff・worklog も編集禁止に従い未更新です。
---

## rerev

対象は clean な HEAD `b2b6e5c49f955c8ddf4ff2501d5e70bc42d19bc3` と一致していた。ファイル変更・pytest 実行はしておらず、緑は主張しない。変異については既存 ledger と注入コードを検査した。

## 任務 1 — 初回所見の対応表

| ID | 判定 | 一次証拠・理由 |
|---|---|---|
| R1-01 | partial | script 自身は `realpath -e` と symlink/fixed-position 検査を得た（[submit_floor.sh:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:14)、[同:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:83)）。一方、`qsub` は依然 PATH 解決（[同:387](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:387)、[同:400](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:400)）。後者は裁定 scope 外。 |
| R1-02 | closed | submit 側は commit blob hash と working-tree hashを照合（[submit_floor.sh:211](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:211)、[同:225](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:225)）。job 側も実行 bytes・receipt・commit blob を照合（[floor_campaign.sh:411](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:411)、[同:443](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:443)）。ただし検出テストの欠陥は R3-04。 |
| R1-03 | partial | 全 Python 呼出し前へ unset/realpath を移した点は修正（[floor_campaign.sh:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:27)）。ただし executable は ambient PATH 選択で、`-E -s -B` も isolated mode ではない。R3-01/R3-02。 |
| R1-04 | not-addressed (裁定で scope 外) | `timeout`、`qstat`、`hostname`、parser 内 `date` は依然 ambient PATH（[floor_campaign.sh:474](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:474)、[同:479](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:479)、[同:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:525)）。 |
| R1-05 | partial | `s8b-freeze/`・`campaigns/` 除外は実装（[submit_floor.sh:121](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:121)、[floor_campaign.sh:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:87)）。検査後に pathname で `mkdir` する一般 TOCTOU は残る（[submit_floor.sh:244](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:244)、[同:250](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:250)）が裁定 scope 外。 |
| R1-06 | partial | qstat policy、receipt round-trip、claims fixture は動的化された（[test:918](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:918)、[同:971](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:971)、[同:719](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:719)）。しかし blob 検査削除と build no-op の偽緑が残る。R3-04/R3-05。 |
| R1-07 | closed | setup FD failureを `floor_driver_setup` として driver rc から分離し、signal rc も 130/143/129（[floor_campaign.sh:168](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:168)、[同:850](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:850)）。検査不足は R3-03。 |
| R1-08 | closed | job 側 `git status` の出力と rc を別捕捉し、非ゼロを拒否（[floor_campaign.sh:461](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:461)）。submit 側の同型欠陥は R3-06。 |
| R1-09 | closed | self-run harness が追加済み（[test:1174](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1174)）。 |
| R2-01 | closed | 初回 M8 の SURVIVED を隠さず、二箇所変異へ再照準している。現実装は pre/post guard（[submit_floor.sh:359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:359)、[同:379](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:379)）と `stat -Lc`（[同:368](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:368)）。解釈上の限定は後述。 |
| R2-02 | closed | stub preflight/qsub を通る non-dry-run 成功経路が追加され、`dry_run:false`、ID、argv、cwd、claims mode を確認（[test:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:608)、[同:621](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:621)）。 |
| R2-03 | closed | 実 producer receipt を job validator fragment へ渡し、正 ID／別 ID を試験（[test:971](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:971)、[同:979](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:979)）。 |
| R2-04 | partial | qstat、qsub、receipt、build の一部は動的化されたが、interpreter と実行 script hash は依然 source presence 中心（[test:264](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:264)、[同:357](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:357)）。R3-03〜R3-05。 |
| R2-05 | closed | preexisting `job-result.json` で writer を失敗させ、最終 rc=7 を確認（[test:1132](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1132)、[同:1167](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1167)）。failure writer の test double 差異は R3-08。 |
| R2-06 | closed | job-result と reservation の exact key set・型・literal を固定（[test:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:57)、[同:1021](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1021)、[同:1105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1105)）。 |
| R2-07 | not-addressed (裁定で scope 外) | `set`/`umask` に block 出典なし（[floor_campaign.sh:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:14)）、build 出典範囲も粗い（[同:683](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:683)）。 |
| R2-08 | not-addressed (裁定で scope 外) | 診断文言 presence assert が残る（[test:270](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:270)、[同:346](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:346)）。 |
| R2-09 | not-addressed (裁定で scope 外) | `"authorization"` 不在検査は依然 stdout だけ（[test:585](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:585)）。 |

## 任務 2 — 新規・残存所見

### R3-01 / must-fix — interpreter 硬化は依然 bypass 可能

`PY` は `command -v python3` という ambient PATH の結果を realpath 化しただけで、信頼済み executable との照合がない（[floor_campaign.sh:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:27)）。さらに `-E -s -B -` で working directory を import path から除外せず、receipt validator は source clean 検査より前に working-tree module を import する（[同:190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:190)、[同:309](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:309)、[同:461](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:461)）。

read-only introspection では `python3 -E -s -B` は `isolated=0`、`sys.path[0]=""` だった。A-03 の裁定は不十分であり、R1-03 は閉じていない。

放置時の成果物影響: fake interpreter／current-directory module が receipt 検証や driver を差し替え、任意の `job-result.json`・report、または凍結領域への変更を生成できる。

### R3-02 / must-fix — 早期 interpreter 失敗は failure record を書けない

Python 解決は [floor_campaign.sh:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:27) で失敗・exit するが、`ATTEMPT_DIR` 作成は [同:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:107)、`write_failure` 定義は [同:125](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:125)。しかも writer 自身が `$PY` に依存する（[同:132](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:132)）。循環は実在する。

放置時の成果物影響: Python 不在・realpath 失敗時は `job-staging/<jobid>/failure.json` 自体がなく、実 job の失敗理由を構造化台帳へ残せない。

### R3-03 / must-fix — FD setup failureと launch marker の契約が未試験

実装は stdout/stderr FD の rc を分離し、両方成功後に marker を作る（[floor_campaign.sh:850](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:850)）。現行コードの rc 処理自体に誤りは見つからない。しかし動的 test は毎回空の attempt directory を作るだけで（[test:1077](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1077)）、preexisting stdout/stderr、setup rc、marker 不在を一度も検査しない（[同:1099](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1099)）。

放置時の成果物影響: setup rc を潰す回帰や marker 前倒しが緑になり、driver 未起動なのに「launch-attempted」または誤った driver rc が台帳へ残る。

### R3-04 / must-fix — job 側 blob 検査を全削除しても blob test が通る

テストは hidden working-tree drift 下で fragment の rc=0を期待するだけ（[test:280](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:280)、[同:331](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:331)）。製品の blob 取得・比較 [floor_campaign.sh:443](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:443)〜459 を削除しても、executing bytes、receipt commit、assume-unchanged status はすべて通るため、結果は同じ rc=0になる。

放置時の成果物影響: A-02 の job 側 commit-blob 再照合が消失しても検出されず、job provenance の必須証拠が欠落する。

### R3-05 / must-fix — dependency test は build command の実行を固定していない

`git`/`cmake`/`timeout` stub は call log を持たず（[test:385](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:385)〜403）、最終的に rc と export 値だけを見る（[同:422](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:422)〜440）。configure/build/install 各呼出しを `:` にしても通る。

放置時の成果物影響: gflags/glog が一度も build/install されず、実 allocation が driver build failure で report・試行台帳を生成しない回帰を検出できない。

### R3-06 / must-fix — submit 側 untracked 検査が Git failure を clean と扱う

`git ls-files --others` は process substitution 内にあり、その rc を検査していない（[submit_floor.sh:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:196)〜206）。read-only shell probeでも、process substitution が rc=73でも loop rc は0になった。

放置時の成果物影響: `ls-files` error 時に untracked codeを見落とした `dry_run:false` receipt と qsub が作られ、source identity が偽になる。

### R3-07 / must-fix — test の `~`／外部副作用は保証されていない

明示的な書込み先は `tmp_path` で、実 repo の `output/` は [test:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:28)、[同:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:247) の read のみだった。一方、Git helper は環境を隔離せず（[同:113](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:113)）、`git init` と `git commit` を実行する（[同:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:135)〜139）。global `core.hooksPath`、template、system/global config を継承するため、configured commit hook の外部書込みを防げない。実際に副作用が起きたとは主張しない。

放置時の成果物影響: test 実行だけで hook が `~`、実 repo/output、または外部台帳を変更し、I8 の検査証拠を汚染しうる。

### R3-08 / backlog — writer failure test double が production の one-shot record を再現しない

production `write_failure` は最初の1回で `failure_written=1` にする（[floor_campaign.sh:124](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:124)〜157）。job-result writer failureを先に記録した後の driver failure は無視される（[同:909](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:909)〜914）。テストの stub は全呼出しを append し、2行あることを期待する（[test:1156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:1156)〜1171）。

放置時の成果物影響: 同時失敗時の `failure.json` には writer rc しか残らず、driver rc は scheduler exit にしか残らない。

## 重点経路の確認

- `git cat-file blob` の linked-worktree 経路は実測で成功した。detached HEAD は実測していないが、branch 名を使わず `rev-parse HEAD` の40桁値を使うためコード上は対応している（[submit_floor.sh:183](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:183)、[同:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:213)）。
- `external/ccbench` の gitlinkを `blob` として読む probe は rc=128だった。submit/job とも非ゼロを fail-closed にする（[submit_floor.sh:217](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:217)、[floor_campaign.sh:447](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:447)）。既定 target は superproject 内の通常 blob なので正常経路には影響しない。
- containment 除外が拒否するのは resolved `output/s8b-freeze` と `output/campaigns` だけ。正当な `output/env/pegasus/floor/...` は比較上通り、non-dry-run fixture もその既定 path を使う（[test:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:608)〜618）。誤拒否は見つからなかった。

## 任務 3 — 変異結果の妥当性

| 変異 | 判定 |
|---|---|
| M1/M2/M4/M7/M10 | ledger の KILLED とコードは整合。M4/M7は動的経路でも受理集合が変わる。 |
| M3 | KILLED ラベル自体は正しいが、変異先 `$JOB_SCRIPT_REPO_PATH` は製品に存在せず、`set -u` failureも導入する（[mutation_harness.py:34](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t088-wrapper/mutation_harness.py:34)）。単一理由性は弱い。 |
| M5 | KILLED は正しいが、主な kill は source文字列検査。PATH 汚染に対する実効性を証明しない。 |
| M6 | 初回 anchor 0件の `ANCHOR-NOT-UNIQUE` は正しい。FD anchor へ移した reaim は KILLED と整合。 |
| M8 | 初回 SURVIVED は正しい。正確には「第1 call-siteだけの除去」が rc/受理集合上等価。 |
| M9 | 初回 `RED-ELSEWHERE` は expected nodeid stale による分類で正しい。reaim の KILLED も actual failing node と整合。 |

M8では、第1 guardを消すと `stat -Lc` が0700 symlink targetを追って通過するが、第2 guardが同じ symlink predicateを再評価して拒否する。したがって初回変異は test の観測範囲で等価である。ただし「単層変異一般が等価」は誤りである。実際の symlink 検査は共通関数の一箇所（[submit_floor.sh:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:116)）に集約されており、ここを一度変異すれば pre/post の両 call が同時に無効になる。二 call-site同時変異は機械的には KILLED だが、最小の一階変異ではない。

同型の mask は次に残る。

- blob test は「成功」を期待するため、blob 検査全削除を maskする。
- build test の no-op stub は、build/install 呼出し削除を maskする。
- writer failure testの複数行 stubは、production の one-shot failure recordを maskする。
- FD setup failure branchは fixture自体がなく、変異が未到達になる。

### 次に撃つべき変異 3件

1. `submit_floor.sh:116` の共通 `[[ ! -L "$current" ]] || return 1` を `:` にする単一-site M8。期待 killは `...[symlink]`。これは現コード上 KILLED 予測だが未実測。
2. `floor_campaign.sh:443-459` を `JOB_SCRIPT_SHA256="$RECEIPT_SCRIPT_SHA256"` に置換し、job側 `cat-file` を完全 bypass。現テストは SURVIVED 予測。
3. `floor_campaign.sh:852` の `|| driver_setup_rc=$?` を `|| driver_setup_rc=0` にし、`floor-driver.stdout` を事前作成した fixtureで、setup rc・marker不在・job-result不在・failure stageを固定する。現テストだけでは SURVIVED 予測。

## 裁定への反論

- A-03を「実装済み」とする裁定は誤り。realpath は PATH 選択された executable を信頼済みに変えず、`-E -s -B` も unsafe import pathを消さない。
- R1-06/R2-04を閉じた扱いにはできない。Git blob削除と dependency build no-op の偽緑が残る。
- M8の「単層は等価」は第1 call-site変異に限定すれば正しいが、共通 predicate 一箇所の変異には当てはまらない。
- 「test は tmp_path のみなので副作用なし」は直接 pathについては正しいが、global Git hook/config 継承まで含めると成立しない。

段階3/4、driver hard-cap、collector、admission変更は must-fix に含めていない。

## 総合判定

**NO-GO — must-fix 7件。**
---

## fix2

実装完了です。許可された3ファイルのみ変更し、commit・git add・qsub・docs編集は行っていません。official 受理集合も変更していません。

### 変更行

- [floor_campaign.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/floor_campaign.sh:27)
  - Python全14呼出しを `-I -B` 化。
  - attempt作成・`write_failure` 定義後へ interpreter 解決を移動。
  - 解決失敗時の `failure-interpreter.txt` をshellだけで記録。
- [submit_floor.sh](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/pegasus/submit_floor.sh:135)
  - Python全5呼出しを `-I -B` 化。
  - untracked一覧をNUL区切りの一時ファイルへ取得し、Git rcを明示検査。
- [test_pegasus_floor_tools.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_pegasus_floor_tools.py:113)
  - Git環境隔離、blob負例、build argv exact検査、interpreter失敗、FD setup失敗などを追加。

### F2-1〜F2-7

| 項目 | 対応 |
|---|---|
| F2-1 | floor側14件・submit側5件をすべて `-I -B` に変更。旧 `-E -s -B` は0件 |
| F2-2 | `ATTEMPT_DIR`作成 → `write_failure`定義 → Python解決の順序へ変更。失敗時はplain-text markerをcreate-onlyで記録 |
| F2-3 | `git ls-files --others` のrcを捕捉し、非0をそのrcでfail-closed。rc=73負例を追加 |
| F2-4 | working-tree/spooled bytesとcommit blobが異なる場合にrc=2で拒否するnegative testを追加 |
| F2-5 | git/cmake/timeout stubをNUL区切りで記録し、gflags/glog各configure/build/installの全6 argvをexact検査 |
| F2-6 | stdout FD setup失敗時に`floor_driver_setup`を記録し、launch marker・job-result・driver実行がないことを検査 |
| F2-7 | `HOME=<tmp>`、global/system config無効化、`GIT_CONFIG_NOSYSTEM=1`、空`core.hooksPath`を全Git実行へ適用。外部hook負例も追加 |

### 検査結果

指定nodeid範囲：

- `orchestrator/tests/test_pegasus_floor_tools.py`: 49 passed
- `orchestrator/tests/test_pegasus_tools.py`: 52 passed
- `orchestrator/tests/test_plain_runner_coverage.py`: 3 passed
- 合計: **104 passed in 3.60s**

追加・重点8 nodeidも個別実走し、8 passedでした。両scriptの `bash -n` はともにrc=0です。

共通検査：

- `tools/check_codex_agents.py`: rc=0
- `tools/check_docs.py`: 違反なし
- `git diff --check`: rc=0

赤の内訳：

- 必須全走の初回・2回目は各 `103 passed / 1 failed`。いずれも新しい悉皆assertの誤りで、`"$PY"`の記録処理を起動と誤認した件と、起動件数を13と数えた件です。製品コードの回帰ではなく、assertを正して最終104件全緑を確認しました。
- それ以前に検索コマンドの引用符ミスが1回ありましたが、テスト実行前のshell構文エラーです。

### 所有外への波及可能性

- human submit callerとPBS jobはPython isolated modeになる。
- Git untracked検査エラー時は、従来の偽cleanではなくsubmission前に拒否される。
- receipt/reservation/job-result schema、qsub argv、driver CLI argvは不変。
- Git隔離helperは本テストファイル内の一時repoだけに影響する。
- テスト書込みは`tmp_path`のみ。実repoの`output/`と`~`への書込みはない。
- `orchestrator/campaign/`、既存3 script、policy、docs、凍結bytesは未変更。

### 実装しなかった項目

裁定どおり、PATH由来ツール実体の信頼検証、一般TOCTOU、共通module化、段階3/4 admission、driver定数、R3-08 one-shot意味論はscope外として未実装です。docs/handoff/worklog、commit、qsubも明示禁止に従い実施していません。
