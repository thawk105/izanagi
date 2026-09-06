# [T-2232] 段 4 裁定 — 段 4 loop 用 Pegasus job body と登録簿の同期 (2026-09-05、base 97ee3cd3a)

段 2 プラン (`codex/.../s2-plan.md`) と段 3 レンズ A (環境注入・規律 1/2)、レンズ B (登録簿同期・contract テスト恒真性) の所見を、親がコードで裏取りして裁定した。裁定 ID は C 番号。**plan v2 節と変異表がそのまま実装契約である。**

## C0 — 親 brief の訂正

- P1「事前構築は無害な死んだ経路」は**誤り**。プランどおり hydrate 済み source root の中で `masstree_build` を走らせると、durable な staged source に `config.h`・archive が生成され汚れる (レンズ A 所見 4、`ThirdParty.cmake:57-78`)。訂正: 3 source を scratch へ `cp -a` してから SOURCE_DIR に渡す (A-2 の `cp -a "$dependency_source"/. "$dependency_prefix"/` と同型)。「現行 `p3_s4_loop.py` に消費 seam が無い」の部分は正しい (`p3_s4_loop.py:171-190, 1525-1539`、親が再確認)。
- P4 の「専用 detached checkout」は README 契約に留めず、job body が **`/.claude/worktrees/` または `/.codex/worktrees/` を含む REPO_ROOT を rc=2 で拒否**する (`layout._reject_worktree_container` と同じ判定基準を shell で写す)。detached かどうかは検査しない。
- 「登録簿 bytes を pin する golden は無い」は「固定 hash・凍結 blob が無い」の意味に限定する。`test_hooks.py:3446-3449` の literal golden と `check_codex_hooks.py` の HEAD blob 束縛 (未 commit の登録簿編集で段 6 の子が起動できない) は実効 pin である (レンズ B)。→ C14。
- 「shim まで置いて 5,226 passed」は既存 test dispatch の実測であり、本 job の動作を一般化しない (レンズ A)。brief から根拠として外す。

## C1 — reservation 束縛と claim root (レンズ A 所見 1): real、採用

`pegasus` 契約は `single_process=True` なので `loop._authorize_measurement` (`loop.py:198-213`) が build より前に `IZANAGI_RESERVATION_*` 8 変数 (`reservation.py:_ENV_FIELDS`) を要求し、`<output root>/env/pegasus/claims` が directory として事前 provisioning 済みでなければ `ExecutionGuardError` で停止する。これはコードで確定した決定的な関門であり「未実測の障害」ではない。**job body は A-2 job body 123〜228 行の reservation block を逐語で写し** (`qstat -f "${PBS_JOBID#0:}"` → started epoch と requested_s、`boot_id`、job script の sha256、`IZANAGI_RESERVATION_NONCE="$PBS_JOBID"`)、`reservation.json` を evidence root へ create-only で書き、`<REPO_ROOT>/output/env/pegasus/claims` を `mkdir -p -m 0700` で provisioning する (exploration の output root は `IZANAGI_EXPLORATION_OUTPUT_ROOT` 不在なら `<repo>/output`、`layout.py:41-47, 384-395`)。
**attestation の exact 照合 (`env_attestation.load_verified_calibration`) には触れない** (ユーザー引数)。

## C2 — FetchContent の依存 identity 未束縛 (レンズ A 所見 2): real、scope 外

mimalloc の tag が可変、clone した source manifest が build identity に入らない — `buildcache.py` / `p3_s4_loop.py` 所有で全 site 共通の既存挙動。本 wave では実装せず裁定パッケージ候補へ (§裁定パッケージ)。job は proxy literal を export する (P2 採用、実接続は未実測)。

## C3 — 環境 sanitize の集合 (レンズ A 所見 3): 一部採用

unset 集合に `CONFIG_SITE` を足す (Autoconf が読む)。プランの集合 (`CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS LD_PRELOAD LD_LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH COMPILER_PATH GCC_EXEC_PREFIX CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE CMAKE_GENERATOR* CMAKE_PROJECT_INCLUDE* CMAKE_PROJECT_TOP_LEVEL_INCLUDES CMAKE_*_COMPILER_LAUNCHER PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS IZANAGI_OFFICIAL_OUTPUT_ROOT IZANAGI_EXPLORATION_OUTPUT_ROOT IZANAGI_B10_BINARY_PATH_POLICY` + `GIT_* CCACHE_* SCCACHE_* DISTCC_* ICECC_*`) に加える。`make`/`ar`/`git` の identity 束縛は buildcache 所有で scope 外。

## C4 — 事前構築の source 汚染と receipt (レンズ A 所見 4): real、採用

C0 のとおり scratch へ複製してから構築する。複製前に各 source の `git rev-parse HEAD` と tracked clean を確認し、複製後の masstree に `config.h` が**無い**ことを確認してから構築する (既存生成物による no-op を排除)。receipt `masstree-prebuild-receipt.json` (`p3-s4-loop-masstree-prebuild/v1`) の field: `fetchcontent_base_dir`、`source_root` (scratch 複製)、`sources` (3 本の `{name, head_commit}`)、`config_h_path`、`config_h_sha256`、`configure_argv`、`build_argv`、`toolchain_manifest` (`observed_toolchain_manifest` の戻り値)、`pbs_jobid`。hydrate receipt hash の束縛は scope 外。

## C5 — exploration output root (レンズ A 所見 5): real、採用

`IZANAGI_EXPLORATION_OUTPUT_ROOT` を unset する (C3 の集合に含めた)。campaign 成果物は REPO_ROOT の `output/exploration/...` へ落ちる (P4)。

## C6 — interpreter identity (レンズ A 所見 6): 採用

`PYTHONNOUSERSITE=1` を export する。compute-result に `python_realpath` と `python_sha256` を足す (schema `p3-s4-loop-compute-result/v1` の field: `schema_version, driver_rc, pbs_jobid, python_realpath, python_sha256`)。

## C7 — shim dir の閉集合 (レンズ A 所見 7): 採用

job body は shim dir を作った直後に「entry が `python3` の 1 本だけ」を runtime 検査し、違えば rc=2。contract テストの負例は `cmake c++ gcc cc g++ make git nm` の 8 本を shim dir へ足す変異を各々拒否する。

## C8 — `bash -n` の guard 拒否 (レンズ B 所見 2): real、採用

login node では `bash -n tools/pegasus/<job>` が guard に拒否される。構文検査は contract テスト内で source を stdin に与える形 (`test_paper_story_a1_job_contract.py:1125-1131`) にし、親の短走はその test node を焦点走する。

## C9 — `qsub` 不在検査の token 化 (レンズ B 所見 3): 採用

A-2 の `"q"+"sub" in source` は写さず、A-1 の `_shell_submitter_violations` (`test_paper_story_a1_job_contract.py:1105-1180`、heredoc 除去 + shlex + 間接呼出し検出) を新 test file へ複製して使う。正例: `qstat -f` と comment 中の語は違反にならない。負例: 直接・`command`・絶対 path・変数間接の 4 型。

## C10 — login 拒否 harness の恒真回避 (レンズ B 所見 4): real、採用

stub `hostname` は marker file を書いてから `pegasus01` を出す。stub `git` / `cmake` / `python3.10` / `qstat` は marker を書いて rc=99 で死ぬ sentinel とする。harness は rc=2・compute-only 文言・hostname marker **有**・sentinel marker **無**・scratch/receipt/compute-result 非生成を全て要求する。job body の host gate は PATH sanitize より**前**に置き、順序を静的契約で固定する。

## C11 — resolver harness の旧 python3 負例 (レンズ B 所見 5): 採用

harness は 2 dir を作る: `old-bin/python3` (呼ばれたら `OLD-PYTHON3` を stderr に出し rc=1) と `good-bin/python3.10` (`sys.executable` への symlink)。production の resolver + shim 部分を snippet として実行し (候補 list と bootstrap PATH literal を harness が置換する — A-2 harness と同じ限界)、`command -v python3` が shim を指し、`python3 -c` が 3.10 で動くことを要求する。

## C12 — fragment 削除以外の変異 (レンズ B 所見 6): 一部採用

静的契約に順序検査 (host gate < trap < resolver < shim < pin gate < prebuild < receipt < driver) と、`exit 2` の literal を各 gate 文言と対で固定する検査を足す。条件反転の全数被覆は求めない (限界として記録)。

## C13 — plain runner の `__main__` (レンズ B 所見 7): 採用

新 test file は `_run()` と `if __name__ == "__main__": raise SystemExit(_run())` を持つ。焦点走に `orchestrator/tests/test_plain_runner_coverage.py` と file 集合列挙のメタテストを含める。

## C14 — 統合 commit の順序 (レンズ B scope 外所見): 採用

author 完了 → 親が登録簿を含む統合 commit → 段 6 review 子起動。未 commit の登録簿編集では review 子が起動できない (HEAD blob 束縛)。

## C15 — walltime と job 名 (P3): 採用、限界を明記

`03:00:00` / `izs4loop`。loop の 3600 s 判定は iteration 境界でしか効かず、build に timeout は無い。walltime 超過は NQSV の kill であり、compute-result は残らない (残存リスク)。

## C16 — pin と clean 検査 (プラン P4 条件): 採用

superproject は `git status --porcelain --untracked-files=no --ignore-submodules=all` が空、CCBench は `p3_s4_loop.PIN` (`028f34d`) に対して A-2 と同型の exact 検査 (HEAD^{commit}、`${PIN}^{commit}`、full SHA 一致、literal prefix、tracked clean)。現行 gitlink `511c953` と異なることは親が確認済み。pin は `"$PY" -B -c 'from orchestrator.campaign.p3_s4_loop import PIN; print(PIN)'` で取る。

## C17 — `--isolate-worktree` と argv: 採用

`"$PY" -B -m orchestrator.campaign.p3_s4_loop --allow-coder-derived-build --isolate-worktree` + (`--run-iteration "$IZANAGI_S4_PROPOSAL_PATH"` | `--value "${IZANAGI_S4_FIXTURE_VALUE:-20}"`)。`--no-build` 禁止。

## 不採用・refuted

- レンズ A 所見 2 の「proxy literal は identity の証明ではない」: 正しいが本 wave の主張ではない。job は proxy を export するだけで identity を主張しない。
- レンズ B 親 brief 指摘「T-1458 型の 320 件連鎖赤」: `test_check_docs.py` の fixture は独立 5 entry で、登録簿の純増では発火しない (レンズ B 自身が反証)。

## plan v2 (実装契約)

1. `tools/pegasus/p3_s4_loop_pegasus.sh` (新規、executable):
   - PBS directive 5 行 (`-A SFC` / `-q gen_S` / `-b 1` / `-l elapstim_req=03:00:00` / `-N izs4loop`)、冒頭 comment「親が直接投入する compute-only job body であり投入器ではない」、`set -Eeuo pipefail`、`umask 077`。
   - `refuse()` (stderr `p3 S4 loop job refused: <msg>`、rc=2)。必須 env 検査 (`PBS_JOBID PBS_NODEFILE PBS_O_WORKDIR IZANAGI_S4_REPO_ROOT IZANAGI_S4_EXPECTED_HEAD IZANAGI_S4_EVIDENCE_ROOT IZANAGI_S4_THIRDPARTY_SOURCE_ROOT`)。
   - compute-only gate (`hostname` が `^bnode[0-9]+([.].*)?$`) — **PATH sanitize より前**。
   - 環境 sanitize (C3)、bootstrap PATH `/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin`、proxy export、`PYTHONNOUSERSITE=1`、`PYTHONDONTWRITEBYTECODE=1`。
   - path 確定: `repo`、`evidence_root`、`thirdparty_root` を `pwd -P`。evidence root が repo または git common repo 配下なら拒否。REPO_ROOT が `/.claude/worktrees/` / `/.codex/worktrees/` を含めば拒否。`compute-result.json` 既存なら拒否。`pbs_jobid_path_component=${PBS_JOBID//:/_}`。EXIT trap `finish()` が compute-result を `ln` で create-only publish。
   - `resolve_python()` (候補 `python3.10 /usr/bin/python3.10 /bin/python3.10`、3.10 exact + `import orchestrator.campaign.p3_s4_loop`、realpath)、scratch `/scr/$USER/p3-s4-loop-pegasus/<jobid>` create-only、`TMPDIR=$scratch`、shim dir に `python3` 1 本、閉集合 runtime 検査 (C7)、final PATH。
   - repo gate: expected HEAD 40 hex 一致、superproject clean (`--ignore-submodules=all`)、CCBench pin exact (C16)。
   - reservation block (C1、A-2 逐語形)、`reservation.json` create-only、claim root provisioning。
   - masstree 事前構築 (C4): source 3 本を scratch へ `cp -a`、fresh 確認、`prepare_masstree_fetchcontent(...)` を inline Python で呼び、receipt create-only。
   - driver 起動 (C17)。
2. `orchestrator/tests/test_p3_s4_loop_job_contract.py` (新規): 静的契約 (`_assert_static_job_contract`)、順序検査、load-bearing mutant tests (fragment 削除・shim 注入 8 本・`--no-build` 注入・`qsub` 4 型・evidence root 検査削除)、resolver harness (C11)、login 拒否 harness (C10)、PBS_JOBID 写像、登録簿 exact entry (dict 逐語)、README タグ付き fence (`-o` / `-e` が evidence 側 path)、executable bit、stdin `bash -n` (C8)、`_run()` + `__main__`。
3. `tools/pegasus/admission_registry.json`: `paper_story_a1_paired.sh` の直前へ次を挿入。
   `"tools/pegasus/p3_s4_loop_pegasus.sh": {"class": "dispatch-required", "reason": "PBS P3 stage 4 loop build, verification, and benchmark job body", "primary_gate": "PBS allocation and job-body site preflight", "evidence": "static job-body classification"}`
4. `orchestrator/tests/test_hooks.py`: `_PEGASUS_EXPECTED_CLASSES` と `_PEGASUS_EXPECTED_ENTRIES` の同位置へ同内容を挿入 (この 2 箇所以外は触らない)。
5. docs (親): runbook §7.0 投影表 1 行、README §0 宣言表 1 行 + 新節「P3 段 4 loop job body を投入する」(タグ付き fence、`-o`/`-e`、専用 checkout・worktree container 禁止・hydrate `.source_root`・attempt 非再利用)。

## 変異事前登録 (DW-M01、実装前)

| # | 変異 | 殺す層 (単一理由の期待) |
|---|---|---|
| M1 | host regex を `^(bnode|pegasus)[0-9]+` へ緩める | login 拒否 harness (rc=0 か sentinel marker 有) |
| M2 | expected HEAD 比較行を削除 | 静的契約 fragment `expected-head` |
| M3 | superproject clean 検査を削除 | 静的契約 fragment `clean-tree` |
| M4 | CCBench pin を `pin.CURRENT_PIN` から取る | 静的契約 fragment `campaign-pin-import` |
| M5 | `${PBS_JOBID//:/_}` を `$PBS_JOBID` へ | PBS_JOBID 写像 test |
| M6 | evidence root の repo 配下拒否を削除 | 静的契約 fragment `evidence-outside-repo` |
| M7 | shim を作らず bare `python3` を PATH 先頭に残す | resolver harness (旧 python3 が拾われる) |
| M8 | shim dir へ `cmake` symlink を足す | 静的契約 negative (shim 閉集合) |
| M9 | `cp -a` を省き hydrate root を SOURCE_DIR に直接渡す | 静的契約 fragment `prebuild-scratch-copy` |
| M10 | receipt の `open(..., "x")` を `"w"` へ | 静的契約 fragment `receipt-create-only` |
| M11 | `--allow-coder-derived-build` を `--no-build` へ | 静的契約 negative (`--no-build` 禁止) |
| M12 | job body へ `qsub job.sh` 行を足す | token 化 qsub 検査 |
| M13 | 登録簿 class を `local-ok` へ | 登録簿 exact entry test (+ test_hooks golden、冗長 gate と明記) |
| M14 | host gate を PATH sanitize の後ろへ移す | 順序検査 + login harness の hostname marker 無 |
| M15 | reservation block の `IZANAGI_RESERVATION_DEADLINE_EPOCH` export を削除 | 静的契約 fragment `reservation` |
| M16 | claim root の provisioning 行を削除 | 静的契約 fragment `claim-root` |

M13 は test_hooks の golden も同時に反応する冗長 gate。他は単一理由を実装後に確認し、絞れなければ登録から外す。

## 裁定パッケージ候補 (scope 外の real 所見、実装せず)

1. FetchContent の依存 identity (mimalloc tag、clone manifest、`$HOME` の git config) が build identity に入らない (レンズ A 所見 2、`buildcache.py` 所有)。
2. `make` / `ar` / `git` / `nm` の tool identity が toolchain manifest 外 (レンズ A 所見 3・7)。
3. `p3_s4_loop` CLI が condition gate record を durable artifact に残さない (レンズ A、T-2199 §段 3 所見 2 と同型)。
4. `--isolate-worktree` の生成先 `TMPDIR` の所有・symlink 検査 (レンズ A)。
5. 事前構築の成果を `p3_s4_loop.py` が消費する seam (T-2320 と同型の後続 wave)。

## 段 5 分割

author 1 単位 (workspace-write、`--max-model-calls 600`)。編集 file は plan v2 の 1〜4 だけ。docs は親。
