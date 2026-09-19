単独段 dispatch: stage=author; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/0a534e2c/tmp/adjudication.md

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/adjudication.md (段 4 裁定と plan v2。§2 が本単位の設計正本、§3 が変異事前登録。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/brief.md (段 1 brief と前提実測。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/0a534e2c/tmp/rulings-verbatim.md (D2148 項 12・D1877・D1936 項 43・F945 冒頭と末尾・DW-S05-A/B/C の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py の 130〜192 行 (`_run_git` / `_repo_is_detached` / `_repo_snapshot`) と 660〜680 行・830〜845 行 (production の呼び出し 2 箇所)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py の 1〜100 行 (import、`REPO_ROOT`、module fixture、autouse fixture) と 605〜650 行 (負例 `test_job_start_requires_manifest_head_detached_and_clean_repository`)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/orchestrator/tests/test_plain_runner_coverage.py (自走 harness の判定条件 `_self_runnable()` と allowlist。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author/orchestrator/tests/s8b_v2_freeze_fixture.py の 1〜40 行 (非 test helper module の先例。読めなければ即停止)

repo root は /work/1/SFC/tanab/izanagi/.codex/worktrees/t2790-u1-author (branch t2790-u1-author、base 8fd1eecf9) である。編集はこの root 内だけ。

# 依頼 — 段 5 実装 U1: t1259 受入 fixture の git 走査 timeout を fixture 局所の候補値 (120 秒) にする。production の 30 秒は不変

## 所有 (これ以外の file を編集しない)
1. `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py`
2. `orchestrator/tests/t1259_scan_bound.py` (新規)
3. `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` (module fixture の 1 行 + import 1 行だけ)
4. `orchestrator/tests/test_t1259_scan_bound.py` (新規)
5. `output/scratch-t2790/scan_sampler.py` と `output/scratch-t2790/junit_scan_survey.py` (新規、計測 script。commit されない)

`orchestrator/tests/conftest.py`、`orchestrator/tests/test_real_repo_serialization.py`、`orchestrator/tests/acceptance_duration_ledger.json`、
`tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs`、docs (`docs/**`、`docs/handoff/**` への file 作成を含む)、`output/insights/**`、他の test file は編集しない。
**`git add` / `git commit` / `git stash` を絶対に実行しない (commit は親が行う)。** 所有外 file を読むのは自由。

## 何を作るか (adjudication.md §2 の逐語が正本。要点)
1. **production probe** (§2.2): `_run_git` と `_repo_is_detached` に keyword-only `git_timeout_seconds: float = 30.0` を足し、
   `subprocess.run(..., timeout=git_timeout_seconds)` にする。`_repo_snapshot(repo_root, *, git_timeout_seconds=30.0)` が 4 呼び出しへ中継する。
   走査 argv 4 種・`GIT_OPTIONAL_LOCKS=0`・返り値 dict の key と値・`ProbeError` 条件・`check=True` は 1 byte も変えない。
   `subprocess.TimeoutExpired` を捕まえて包まない。production の呼び出し 2 箇所 (`before = _repo_snapshot(repository)` /
   `after = _repo_snapshot(repository)`) は引数を足さない。`observe()` の拒否論理・`DRIVER_TIMEOUT_SECONDS`・他関数は触らない。
2. **helper module** `orchestrator/tests/t1259_scan_bound.py` (§2.3): `FIXTURE_GIT_TIMEOUT_SECONDS: float = 120.0` と
   `fixture_repo_snapshot(repo_root) -> dict` (= `probe._repo_snapshot(repo_root, git_timeout_seconds=FIXTURE_GIT_TIMEOUT_SECONDS)` を
   返すだけ。例外を捕まえない、代替 snapshot を返さない)。docstring に D2148 項 12 / F945 を 1 行で引き「production の 30.0 は不変、
   この値は受入 fixture の module snapshot 1 回分にだけ効く」と書く。
3. **module fixture** (§2.4): `test_t1259_qsub_env_delivery_probe.py` の `_clean_detached_source_snapshot_template` 内
   `snapshot = probe._repo_snapshot(REPO_ROOT)` を `snapshot = t1259_scan_bound.fixture_repo_snapshot(REPO_ROOT)` に置き換え、import を
   1 行足す。**それ以外 (77〜79 行の上書き 3 行、autouse fixture、全 test 関数・parametrize・assertion) は 1 byte も変えない。**
   この module に test 関数を追加・改名しない (real-repo golden に当たる)。
4. **正例 test** `orchestrator/tests/test_t1259_scan_bound.py` (§2.5): tmp git repo (`tmp_path` に `git init`、`-c user.name -c user.email`
   で 1 commit、untracked 1 file) を作り、`probe.subprocess.run` を「kwargs を記録してから本物の `subprocess.run` へ委譲する」spy に
   monkeypatch する (stub にしない)。
   - test 1: `probe._repo_snapshot(tmp_repo)` → 記録された git 呼び出し 4 件すべての `timeout == 30.0`、`head` が tmp repo の HEAD、
     `untracked_paths` に作った file が含まれる。
   - test 2: `t1259_scan_bound.fixture_repo_snapshot(tmp_repo)` → 4 件すべて `timeout == FIXTURE_GIT_TIMEOUT_SECONDS` かつ `!= 30.0`、
     snapshot の key 集合と `head` が test 1 と一致。
   - test 3: `probe.subprocess.run` を `subprocess.TimeoutExpired` を raise する代役に差し替え、`fixture_repo_snapshot(tmp_repo)` が
     同じ例外型をそのまま伝播させる (`pytest.raises(subprocess.TimeoutExpired)`)。
   - 実 repo (`REPO_ROOT`) を読まない。`REPO_ROOT` を import しない。
   - 自走 harness: `test_plain_runner_coverage.py` の `_self_runnable()` が緑にする形 (`_run()` / `if __name__ == "__main__":`) を
     既存 test file から写す。allowlist へ逃がさない。
   - 新 nodeid の受入 duration 台帳登録は親が別 step で行う。台帳を手で編集しない。
5. **計測 script 2 本** `output/scratch-t2790/` (§2.6)。標準 library だけ。author は走らせない。
   - `scan_sampler.py`: `--worktree <abs>` `--out <jsonl>` `--interval-seconds N` `--max-samples N` `--stop-file <path>` `--self-tag <str>`。
     1 sample = ISO 時刻、`/proc/loadavg` 3 値、leader 数 (`/proc/*/cmdline` に `dev_wave_wait.py` と ` acceptance` を両方含み
     `--self-tag` を含まない process 数)、worker 数 (`run_tests.py` を含む process 数)、`probe._run_git(worktree, ...)` を production と
     同じ 4 argv で順に `git_timeout_seconds=600.0` で呼んだ各 wall 秒 (`time.monotonic()`) と合計 (`_repo_is_detached` も同じ引数で)、
     probe の 3 file sha256 の所要。worktree へ 1 byte も書かない。1 行 1 JSON で追記。`--stop-file` が現れたら終了。
     `sys.path` に repo root を足して `from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe` で import する
     (`--repo-root <abs>` 引数で与える)。
   - `junit_scan_survey.py`: `--shards-root <abs>` `--since 'YYYY-MM-DD HH:MM'` `--out <md>`。各 session dir の `shard-*/junit.xml` から
     classname に `test_t1259_qsub_env_delivery_probe` を含む testcase を集め、regime (nodeid 末尾 `@real-repo` の有無)、走査回数の代理
     (time ≥ 2.0 秒の test 数)、各走査所要 (同 time)、error 数 (30 秒右打ち切り)、testsuite の `timestamp`/`time`/`hostname` を取る。
     session の走行窓 [timestamp, timestamp+time] の重なりで「同時に走っていた他 session 数」を層にし、regime 別・重なり数別に
     n / p50 / p90 / p95 / p99 / max / error 数の表を Markdown で書く。走行窓は shard-0〜2 の和集合で作る。
     session dir の mtime が `--since` より古いものは除く。

## やってはいけないこと
- production の既定 timeout (30.0) を変える・`_repo_snapshot` の走査対象 argv を減らす・`untracked` 走査を省く・例外を包む・代替 snapshot を返す。
- 既存 test の期待値・parametrize・nodeid を変える。t1259 module に test を足す。`conftest.py`・serialization golden・duration 台帳を触る。
- 検査の省略・stub 化・hold 変更・xfail 化。fixture への現行 hash 差し込みで緑にすること (F27)。依存先を stub すること (F649)。
- docs の編集 (docs/handoff への file 作成を含む)。`git add` / `git commit` / `git stash`。

## 検証 (sandbox では pytest を走らせられない — socket 不可)
- 実走は親が行う。**走らせていない結果を緑と書かない。**
- 最低限、Python で `tools.pegasus.probes.t1259_qsub_env_delivery_probe` と `orchestrator.tests.t1259_scan_bound` を import し、
  `tempfile.mkdtemp()` に作った小さな git repo に対し (i) `probe._repo_snapshot(root)` と (ii) `fixture_repo_snapshot(root)` を直接呼び、
  spy で `timeout` が 30.0 / 120.0 であること、snapshot の内容が一致することを確かめて報告に書け (`DIRECT_CALL_PASS` / 実行不能なら理由)。
  さらに新 test module を import して test 関数 3 本を `tmp_path` を `tempfile.mkdtemp()` で代用して直接呼び、成立を確かめ、
  反実仮想として `FIXTURE_GIT_TIMEOUT_SECONDS` を一時的に 0.0 / `fixture_repo_snapshot` を固定 dict 返却へ変えたとき test 2 が
  赤化する (`DID NOT RAISE` でなく AssertionError) ことを確認して元へ戻し、報告に書け (`git diff` で復元を確認)。
- `python3 -m py_compile` で編集・新規の全 .py を compile。`ast` で `test_t1259_qsub_env_delivery_probe.py` の test 関数名・parametrize が
  変更前と同一 (差分は import 1 行 + fixture 内 1 行のみ) であることを自分で数えて報告に書け。
- `tools/check_docs.py`・焦点走・受入・変異は親が行う。

## 報告 (このファイルの末尾 `## 総括` は必須)
- `## 変更面` (file:line の表。production の呼び出し 2 箇所が既定のままである根拠を行番号で)
- `## 走査対象と例外型の不変性` (argv 4 種・env・返り値・例外が変わっていないことを diff 行で)
- `## 他 caller への波及` (所有外 caller・共有 fixture・consumer test・meta-test の静的列挙。`_repo_snapshot` を monkeypatch する
  test 側 lambda (`lambda _root: ...`) が keyword 追加後も呼び出し互換である根拠を含む)
- `## 直接呼出しの検証結果` (`DIRECT_CALL_PASS` と反実仮想の赤化)
- `## 計測 script の使い方` (引数と出力形式)
- `## 未実走・未確認` (実装済み・未実走の項目を正直に)
- `## 総括` (5 行以内)
