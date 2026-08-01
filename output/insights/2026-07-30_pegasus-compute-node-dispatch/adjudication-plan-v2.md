# 段 4 裁定 + plan v2 — Pegasus では重い処理を計算ノードで最大並列

本書が仕様の正本である。`brief.md` / `plan_v1.md` / `adv_a.md` / `adv_b.md` と食い違う場合は本書が勝つ。

## 0. 実測済みの事実 (推測ではない。request `874129` = 計算ノード probe)

- 計算ノード `bnode114`: `nproc` 48 / affinity 48 / cpuset `0-47` / loadavg 0.59
- `python3` = **3.9.13 (Intel Python)**。`/bin/python3.10` = **3.10.12 実在**
- `python3.10` から **pytest 9.1.1 と xdist が import できる** (`~/.local/lib/python3.10/site-packages`)。
  外部 network 不可でも pip 不要で成立する → adv_a の「未実測」「致命的」は本 probe で解決済み
- **全走が計算ノードで成立**: `-n 48` = 3891 passed / 19 skipped / **205.12s**、
  `-n 32` = 3891 passed / 19 skipped / **206.94s** → 48 と 32 に有意差なし
- nested `python3` 問題は本 probe では発現しなかった (`_build_pytest_command` が `sys.executable` を
  使うため子も 3.10)。ただし PATH 先頭に選定 interpreter の dir を置く保険は入れる
- queue 待ち = **86 秒**、Elapse 421s、`.e` に NQSV 会計サマリ (F49(ii)(c) 充足)
- `g++-13` は**計算ノードにも不在** (`g++-12` は在る)。C++ toolchain 依存の real-build canary は
  計算ノードでも skip される → 移設で検出力は増えない。19 skip vs ログインノード 18 skip の差 1 件は
  受入走行で `-rs` により特定して記録する

## 1. 裁定サマリ (real / refuted / 採否)

| # | 所見 (出所) | 裁定 | 対応 |
|---|---|---|---|
| A1 | cache hit 時に架空の `-j N` を記録する (adv_a critical) | **real** | buildcache の `jobs` 既定は**変えない**。下記 §4 |
| A2 | hostname + PBS だけでは両不変条件を保証できない (adv_a critical) | **real** | 4 状態 + site 裏付け証拠。下記 §2 |
| A3 | task_run 台帳と top-level rc が二つの真実になる (adv_a must-fix) | **real** | 記録は**親が 1 回だけ**。下記 §3 |
| A4 | guard_bash の import bootstrap 欠落・迂回・過剰拒否 (adv_a must-fix) | **real** | 下記 §5 |
| A5 | 明示 `-n1` / `jobs=1` は残るので「全て最大」ではない (adv_a) | **real** | (P4) を「**既定が最大**」へ訂正。明示上書きは尊重し、記録に残す |
| A6 | coverage を `_run()` へ寄せると例外型が変わる (adv_a should-fix) | **real** | `subprocess.run(check=True)` を維持し literal だけ差し替える |
| A7 | `_available_cpus()` は `PermissionError` を捕らえない (adv_a) | **real** | policy 側で修復する |
| A8 | `submission-disabled.json` の恒久ラッチが回復不能になる (adv_a/adv_b) | **real** | (a)(b) 型だけラッチ、(c) 型は猶予付き再取得。下記 §3 |
| B1 | 47 経路中 34 件が止まらない = 「謳うだけの保証」 (adv_b critical) | **real** | 保証の言い方を狭める。下記 §6。加えて AGENTS.md で Codex 面を塞ぐ |
| B2 | queue 待ちが 1 wave で 6〜12 回入る (adv_b critical) | **real (ただし実測 86 秒)** | 1 invocation = 1 batch job を維持。理由は §3。allocation 再利用は裁定パッケージ |
| B3 | 2 時間 walltime は certify からの転用 (adv_b) | **real** | test envelope を導出: 既定 `00:30:00` (実測 205s の約 8.8 倍)。CLI 上書き可 |
| B4 | `HLD` / 親死亡 / `.o` 遅延の状態機械が無い (adv_b) | **real** | 期限付き状態機械 + qdel + 猶予付き収集。下記 §3 |
| B5 | `tools/pegasus/*` の一括許可は広すぎる (`exec_calibrate.py` は汎用 execv) (adv_b) | **real** | sanctioned は**列挙した exact path のみ**。glob 許可しない |
| B6 | `-n48` は `-n16` より 45% 遅い実測がある (adv_b) | **real だが本 probe と非整合** | 現行 suite では 48≈32。受入で `-n 16` 対照も測り正直に記録する |
| B7 | 既存 submitter との重複 (規律5) (adv_b) | **real** | 新規 dispatcher は**既存 submitter を置き換えない**。共通核の抽出は裁定パッケージ |
| B8 | brief が 75 行で DW-S01 の 10〜30 行を超過 (adv_b) | **real (形式)** | 段 8 の自己改善候補に記録。本 wave の成果物は変えない |
| B9 | task_run schema に host / PBS ID / queue 待ちが無い (adv_b) | **real** | 「台帳の実行環境が計算ノードになる」の主張を**撤回**。証拠は dispatcher receipt に置く |
| — | `HOSTNAME` 環境変数偽装で誤判定する | **refuted** (両レンズ一致) | 対応不要 |
| — | 既存 `output/s8b-freeze` bytes が自動で書き変わる | **refuted** | 対応不要 |
| — | 計算ノードで pytest/xdist が import できない | **refuted** (probe 874129) | 対応不要 |

## 2. U1 — `site_policy` (単一正本)

新規 `orchestrator/campaign/site_policy.py`。stdlib のみ (`os` / `socket` / `re` / `shutil`)。

区分は**文字列定数 4 種**にする (Enum にしない = 二重 module 名での identity 不一致回避)。

- `OTHER` — Pegasus ではない。**現行挙動を一切変えない** (test cap 32、build `-j 16`)
- `PEGASUS_LOGIN` — 重い処理を拒否して計算ノードへ回す
- `PEGASUS_COMPUTE` — 重い処理を許可し、**既定並列度 = affinity 全数**
- `PEGASUS_SUSPECT` — Pegasus らしいが証拠不足。**重い処理だけ拒否**し、他の挙動は `OTHER` と同じ

判定規則 (`classify_site(hostname, environ, site_markers)` を純関数にする):

1. hostname は `socket.gethostname()` を小文字化・末尾 dot 除去し、**最初の label** を取る
2. `bnode` + 数字 → `PEGASUS_COMPUTE`。**`PBS_JOBID` の有無を条件にしない** (`bnode*` は
   login node ではありえない。並列度は affinity が権威。adv_a の false negative 3 例を閉じる)
3. 最初の label が `pegasus0[1-9]` → site 裏付け証拠を検査し、
   在れば `PEGASUS_LOGIN`、無ければ `OTHER` (adv_a の `pegasus02.example.invalid` を閉じる)
4. 最初の label が `pegasus` で始まるがどちらにも当たらない (`pegasus`, `pegasus04` 等) →
   証拠が在れば `PEGASUS_SUSPECT`、無ければ `OTHER`
5. hostname 取得が例外 → 証拠が在れば `PEGASUS_SUSPECT`、無ければ `OTHER`

**site 裏付け証拠**: NQSV スケジューラの実在 = `shutil.which("qsub")` と `shutil.which("qstat")` が
両方在ること。純関数側は bool を引数で受け、副作用のある解決は薄い wrapper に隔離する。

API:

- `classify_site(hostname, environ, has_nqsv) -> str` (純関数)
- `current_site() -> str` (実環境から解決。例外は内部で吸収し上記 4/5 に従う)
- `is_pegasus_login(site)` / `is_pegasus_compute(site)` / `refuses_heavy_work(site)`
  (`refuses_heavy_work` は LOGIN と SUSPECT が True)
- `available_cpus() -> int` — `os.process_cpu_count` → `os.sched_getaffinity` → `os.cpu_count` の順。
  **`sched_getaffinity` は `AttributeError` だけでなく `OSError` (含 `PermissionError`) も捕らえる** (A7)
- `default_test_jobs(site, *, cap=32) -> int` — COMPUTE は `available_cpus()`、他は `min(cpus, cap)`
- `heavy_work_refusal(site, what) -> str` — 拒否理由と準拠経路を書いた日本語メッセージ
- `LOGIN_FALLBACK_RE` — guard_bash が import 失敗時に使う `^pegasus0[1-9]$`。
  **`classify_site` との整合を meta-test で機械照合する** (重複をドリフトさせない条件で許可)

## 3. U2 — `run_tests.py` の gate と dispatcher

### run_tests.py

- rc 定数へ `_PEGASUS_DISPATCH_RC = 16` を追加 (13/14/15 は既存 preflight)
- `main()` の既存 preflight (13→15→14) の**直後、xdist 準備より前**に dispatch gate を挿す
- `main(argv=None, *, site=None, dispatch_fn=None)` の keyword-only seam を足す (テスト注入用)
- **dispatch 免除は次の閉集合だけ** (`_NO_EXECUTION_FLAGS` は既存 gate が使うので変更しない):
  `--collect-only` / `--co` / `--help` / `--version` / `--markers` / `--fixtures` /
  `--fixtures-per-test` / `--trace-config` / `--setup-plan`。
  **`--setup-only` と `--setup-show` は免除しない** (autouse fixture と実材料構築が走る。adv_a)
- それ以外は件数・selector を問わず dispatch する
- `PEGASUS_SUSPECT` は dispatch せず **rc=16 で拒否**し、`heavy_work_refusal()` を印字する
- `PEGASUS_COMPUTE` では dispatch せず、`default_test_jobs()` で cap を外す。
  `_ensure_xdist()` の pip 経路は**呼ばない**。xdist 不在または `<2.5` は直列 fallback せず rc=16
- `OTHER` は完全に現行どおり (回帰テストで固定する)

### task_run 台帳 (A3 = 一つの真実)

- 親は子へ `IZANAGI_TASK_RUN_ID` を**渡さない**。子は台帳を書かない
- 親が dispatch 完了後に**ただ 1 回**記録する。`exit_status` = 最終 rc (子 rc、infra 失敗なら 16)。
  suite identity は親の argv から既存経路で算出する。`duration_s` は親側の実測 wall とし、
  queue 待ちを含む旨を dispatcher receipt に書く
- **schema は変更しない** (B9)。host / PBS job ID / queue 待ちは dispatcher receipt 側に持つ

### dispatcher (`tools/pegasus/dispatch_compute.py`)

既存 submitter を置き換えず、dev-harness 専用の薄い経路とする (B7)。

- 投入 root は **`output/pegasus-dispatch/<nonce>/`** とし、`.gitignore` へ
  `output/pegasus-dispatch/` を足す (先例 = `output/env/pegasus/silo_ladder_rung1/job-staging/`)。
  **repo の clean 状態を壊さないこと**が必須条件
- queue `gen_S` / `-b 1` / 既定 walltime **`00:30:00`** (B3)。`--walltime` で上書き可
- 投入前 preflight は `qstat -Q` のみ (毎回 4 種の会計 call を打たない。B2/adv_b §4)
- **job 内の fail-closed assert (F46: 記録ではなく assert)**:
  1. interpreter 候補 (`python3.10` → `/usr/bin/python3.10` → `/bin/python3.10`) から
     **version >= 3.10 かつ `pytest` / `xdist` / `packaging` が import できる**実体を選ぶ。
     全滅なら `stage=interpreter` で fail-closed (pip は絶対に呼ばない)
  2. 選んだ interpreter の dir を `PATH` 先頭へ置く (nested `python3` の保険)
  3. `hostname` が `bnode*` であること
  4. cwd を repo root にする (DW-O18)。`$PBS_O_WORKDIR` は submission dir なので使わない
  5. 子の rc を `result.json` へ書き、`/scr` を使う場合は `${PBS_JOBID//:/_}` で `:` を除去
- 親側の状態機械 (B4): `QUE` / `RUN` / `HLD` / 終了 を polling し、
  **queue 待ち上限** (既定 900 秒) と**全体上限** (walltime + 猶予) を持つ。上限超過・SIGINT・SIGTERM・
  例外の全経路で正規化 request ID へ `qdel` を best-effort し、receipt を残す
- F49(ii) の機械化と失敗の型分け (A8):
  - **(a) 出力 dir が実 FS に永続 / (b) `qstat` で request が可視** — 投入直後に検査。
    どちらか欠ければ **F47 型 = 不永続 sandbox** と判定し、`submission-disabled.json` を
    create-only でラッチし、ユーザー端末への引き渡しを印字する
  - **(c) 終了後の会計痕跡 (`.e` の NQSV サマリ)** — 猶予付き再取得 (既定 60 秒 / 5 秒間隔)。
    それでも無ければ **その invocation だけ rc=16** とし、**ラッチしない** (瞬断で全 wave を
    恒久停止させない)
- `.o` / `.e` の収集は**サイズ上限付き** (既定 2 MiB、超過分は tail を残して省略を明記)。全文
  `read_text()` をしない
- 子 rc は会計照合が済んでから**そのまま**返す。infra 失敗は 16 に畳む

## 4. U3 — build の gate と並列度 (A1 により縮小)

- **`buildcache` の `jobs` 既定は 16 のまま変えない。** 理由: cache hit 時に
  `BuildResult.build_argv` が呼出時の値で再構成され、v2 completion manifest には build コマンドが
  無い (`schema_version` / `completion_marker` / `full_build_digest` / `contract_sha256` /
  `preimage` / `toolchain` / `binary` のみ) ため、実際は `-j 16` で作られた binary を `-j 48` と
  記録しうる。これは WAL・floor manifest・ratified `floor_source` へ流れる **provenance の偽り**である。
  正直に上げるには completion manifest へ actual build argv を足す schema 変更が必要で、別 wave の
  裁定事項とする (裁定パッケージ §7)
- **実 cmake build のログインノード拒否は実装する。** `buildcache` が実際に cmake を起動する直前
  (legacy / v2 の両経路) で `refuses_heavy_work(site)` なら fail-closed。
  `site=None` の正規注入 seam を足し、境界テストは site を直接渡す (DW-O14。monkeypatch しない)。
  cache hit と `_run` を stub する既存単体テストは拒否しない位置に置く
- 実 `cmake --build` を呼ぶ既存 nodeid 3 件 (`test_s8b_floor_campaign.py` の
  `test_slow_real_prepare_cell_to_buildcache_canary_one_configuration` /
  `..._v2_canary_one_configuration`、`test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`)
  は計算ノードでは通り、ログインノードでは拒否になる。**skip 化しない**
- coverage 4 モジュール (`s2_verify_calibration` / `s3_lock_coverage` / `s5_permutation_coverage` /
  `s8a_trigger_coverage`) の literal `-j 16`:
  - `subprocess.run(..., check=True)` の**呼び方は変えない** (A6: 例外型を変えない)
  - **その build コマンドが成果物へ記録されていないことを file:line で確認**してから
    `-j` を `default_build_jobs(site)` 相当へ差し替える。記録されていれば literal 16 を維持し、
    gate だけ足して理由を報告する
  - 実 cmake 起動の直前に同じ login 拒否 gate を置く
- `silo_ladder_rung1.py` / `t152_write_intent_coverage.py` / `exec_calibrate.py` は**本 wave の scope 外**。
  裁定パッケージへ回す (adv_a/adv_b の scope 外 real)

## 5. U4 — `guard_bash` の第二防壁

- `decide(command, repo_root="", *, site=None)` にする。`site=None` は `OTHER` と同義に扱い、
  既存単体テストの受理集合を 1 bit も変えない。production `main()` だけが `current_site()` を注入する
- **import bootstrap を明示する** (A4): repo root を `sys.path` へ入れて
  `from orchestrator.campaign import site_policy` を try で囲む。**失敗時は fail-open しない** —
  `LOGIN_FALLBACK_RE` (`^pegasus0[1-9]$`) で hostname を見て LOGIN 相当の拒否だけ行う。
  `classify_site` との整合は meta-test で機械照合する
- 判定は root 確定後・既存 `_MENTION_RE` fast path より前。`_MENTION_RE` / `_LEAF_RE` /
  `_BUILDERS` / `_INTERP` の既存定数は**変更しない** (非 Pegasus の受理集合を動かさない)
- **拒否する形** (LOGIN / SUSPECT のときだけ):
  - head の basename が `pytest` / `py.test` (venv・別 dir・symlink 名も basename で捕らえる)
  - **任意の python 実体**の `-m pytest` (`python` / `python3` / `python3.x` / 絶対パス /
    `.venv/bin/python` を含む。`python3.10` 限定にしない)
  - `cmake` の `--build` (ただし `--help` / `--version` のみは許可)
  - `make` の `-j` / `-jN` / `--jobs` / `--jobs=N` (ただし `-n` / `--dry-run` 同居なら許可)
  - `ninja` の実行 (`-t` / `--tool` の introspection、`--help`、`--version` は**許可**)
  - `ctest` の実行 (`-N` / `--show-only` / `--help` / `--version` は許可)
  - `perf` の `stat` / `record`、`build-variants` 配下の実行体、basename `ycsb_*.exe`
  - `bash` / `sh` / `zsh` の `-c` / `-lc` / `-ic` の内側を**深さ 2 まで再 tokenize**して同判定
  - `sudo` / `env` / `nice` 等の wrapper は**オプション値を正しく飛ばして**実 head を取る
    (`sudo -u tanab pytest -q` を捕らえる)
- **sanctioned (許可) は exact path 列挙のみ** (B5。`tools/pegasus/*` の glob 許可はしない):
  `tools/run_tests.py`、`tools/pegasus/dispatch_compute.py`、`tools/pegasus/submit_certify.sh`、
  `tools/pegasus/submit_floor.sh`、`tools/pegasus/submit_silo_ladder_rung1.sh`、head `qsub` / `qdel` / `qstat`
- 複合コマンドは segment 単位で判定する (`python3 tools/run_tests.py && pytest -q` は 2 番目を拒否)
- **既知の限界を docstring に明記**する: script file 越し、変数展開、`eval`、`python3 -c`、
  Codex subprocess (hook 未配線)、ユーザー端末・IDE。**「全経路を機械保証する」と書いてはならない**

## 6. 保証の言い方 (B1。docs は親が書く)

- 一次強制 = sanctioned entry point (`run_tests.py` / buildcache の実 build) の fail-closed
- 二次防壁 = guard_bash の直接 literal コマンド拒否 (Claude の Bash surface のみ)
- prompt 規律 = `AGENTS.md` (Codex 子) と runbook。**Codex には hook 未配線**
- 機械保証できない面 = script 越し・変数展開・`python3 -c`・他 AI・ユーザー端末・IDE・cron
- したがって成果物の主張は「**sanctioned 経路では機械強制し、それ以外は規律で塞ぐ**」に狭める

## 7. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. `buildcache` の campaign build を site 由来並列にする ⇔ v2 completion manifest へ actual
   build argv を足す schema 変更 (+ pin 閉包・consumer 改修)
2. `silo_ladder_rung1.py` (直接 cmake) / `t152_write_intent_coverage.py` (`DEFAULT_JOBS=MAX_JOBS=8`、
   成果物へ `host_role: login-node` を記録) の扱い
3. `tools/pegasus/exec_calibrate.py` が任意 argv を `os.execv` する汎用トランポリンである点
4. queue 待ちを 1 回に圧縮する allocation 再利用 (resident qlogin / resident batch worker)
5. 既存 submitter 4 本と新 dispatcher の共通 submission 核の抽出 (規律5)
6. `task_run` schema へ host / PBS job ID / queue 待ちを足すか
7. Codex への hook 配線 (hooks/README で BLOCKED 済み)

## 8. 事前登録変異 (DW-M01。親が統合 commit 後に本走する)

| ID | 変異 (単一理由) | 期待 kill |
|---|---|---|
| M1 | `classify_site` の `PEGASUS_LOGIN` 枝を `OTHER` に落とす | login で dispatch されず実走する赤 |
| M2 | `default_test_jobs` の COMPUTE 分岐を消し cap を常に適用 | compute で全コアにならない赤 |
| M3 | `available_cpus` の `OSError` 捕捉を削除 | `PermissionError` fallback の赤 |
| M4 | `refuses_heavy_work` から `PEGASUS_SUSPECT` を外す | 証拠不足 host で重い処理が通る赤 |
| M5 | dispatcher の interpreter 版数 assert を「記録のみ」に変える (F46 型) | 3.9 を選んでしまう赤 |
| M6 | 投入直後の `qstat` 可視性検査を削除 | F49(a)(b) 検査の赤 |
| M7 | 子へ `IZANAGI_TASK_RUN_ID` を渡す (二重記録) | 台帳 1 回性の赤 |
| M8 | guard_bash の `-m pytest` 判定を `python3.10` 限定へ戻す | `python3 -m pytest` が通る赤 |
| M9 | guard_bash の wrapper オプション値スキップを削除 | `sudo -u tanab pytest` が通る赤 |
| M10 | guard_bash の `-lc` / 再帰を削除 | `bash -lc 'pytest -q'` が通る赤 |
| M11 | 実 cmake 直前の login 拒否 gate を削除 | login で実 build が走る赤 |
| M12 | guard_bash の import 失敗 fallback を allow へ変える | fallback 拒否の赤 |
| M13 (**正例**) | `classify_site` が非 Pegasus hostname を `PEGASUS_LOGIN` にする | 非 Pegasus 現行挙動 (cap 32 / `-j 16`) の赤 |
| M14 (**正例**) | guard_bash が `ninja -t targets` / `make -n -j48` / `ctest -N` を拒否するよう広げる | 過剰拒否検出の赤 |

各変異は「その位置より前に同じ入力を拒否する検査が無い」ことを実装子が確認し、赤理由が一つに
絞れる fixture を用意する。M13/M14 は受理集合の**過剰縮小**を検出する正例である (DW-M01)。

## 9. 受入と環境

- 受入全走は **Pegasus 計算ノード (gen_S) で qsub** して行う (本依頼の dogfood)。
  `-rs` を付けて skip 19 件の内訳を記録し、ログインノード 18 件との差 1 件を特定する
- 対照として `-n 16` も 1 回測り、B6 の「48 は 16 より遅い」を現行 suite で検証する
- 記録には PBS job ID / queue 待ち / assigned host / interpreter 実体 / worker 数を残す
- docs 検査 (`check_docs.py`) と静的検査はログインノードで行う (重い処理ではない)

## 10. 実装単位 (所有が素集合)

| Unit | 所有 |
|---|---|
| U1 (先行) | `orchestrator/campaign/site_policy.py` (新)、`orchestrator/tests/test_site_policy.py` (新) |
| U2 | `tools/run_tests.py`、`tools/pegasus/dispatch_compute.py` (新)、`.gitignore`、`orchestrator/tests/test_run_tests_nproc.py`、`test_run_tests_preflight.py`、`test_run_tests_task_run.py`、`orchestrator/tests/test_pegasus_dispatch_compute.py` (新) |
| U3 | `orchestrator/campaign/buildcache.py`、coverage 4 モジュール、`orchestrator/tests/test_build_site_gate.py` (新) |
| U4 | `hooks/guard_bash.py`、`orchestrator/tests/test_hooks.py` |
| 親 | docs (`docs/pegasus-runbook.md`、`AGENTS.md`、`docs/decisions.md`、`docs/worklog.md`)、commit、受入、変異 |

新規テストファイルは **`__main__` + `_run()` の自走 harness を必須**とする (F42 の meta-test)。
`test_plain_runner_coverage.py` と、テストを新設・改名する単位の meta-test も走らせる (DW-S05-C)。
