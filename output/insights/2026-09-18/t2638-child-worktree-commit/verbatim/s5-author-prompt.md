単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s4-adjudication.md` — 段 4 裁定 = **実装の正本** (plan v2 §2、テスト §2.5、変異登録 §3)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s1-brief.md` — 親 brief (背景・不変条件。裁定と食い違う箇所は裁定が優先)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s2-plan.md` — 段 2 plan v1 (file:line の参考。裁定で変更された点は裁定が優先)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/tools/dev_wave_codex.py` — 起動器 (編集対象)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/tools/dev_wave_wait.py` — 待ち手 (編集対象。`_producer_parser`、`_parse_cli`、`wait_for_producer`、`main` の producer 配線だけを読む。4593 行の全文は読まない)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/tools/dev_waves/git_state.py` — helper 追加先 (1〜230 行を読む)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/orchestrator/tests/test_dev_wave_codex.py` — 既存テスト (編集対象)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/orchestrator/tests/test_dev_wave_wait.py` — 既存テスト (編集対象。`_FakeEffects`、`producer` 系 test 4960〜5460 行付近だけ読む)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/orchestrator/tests/test_dev_waves_git_state.py` — 既存テスト (編集対象)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/tools/check_ai_provenance.py` の 60〜95 行 (`IDENT`、`AGENT_VALUE`) と 1495〜1525 行 (`none` 拒否)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-impl/docs/ai-provenance.md` の「必須形式」節。読めなければ即停止。

## 依頼

[T-2638] (D2044 項 16、ユーザー裁定) 実装子 worktree の終端契約を、`s4-adjudication.md` §2 (plan v2) のとおりに実装せよ。
要約: `tools/dev_waves/git_state.py` に `commit_worker_worktree` を 1 関数追加し、起動器 `tools/dev_wave_codex.py` の
launcher 復帰後 (workspace-write ∧ stage author/fix) と待ち手 `tools/dev_wave_wait.py producer` の `--commit-worktree <abs>`
opt-in (producer 死亡確定後) から呼ぶ。作業木の残差 (`git add -A` → staged) を現在 branch へ commit し、
`AI-Agent: product=codex; model=<m>; reasoning=<r>; role=author` trailer を付ける。破棄はしない。

## 所有 (編集してよい file — これ以外は 1 byte も変えない)

- `tools/dev_waves/git_state.py`
- `tools/dev_wave_codex.py`
- `tools/dev_wave_wait.py`
- `orchestrator/tests/test_dev_waves_git_state.py`
- `orchestrator/tests/test_dev_wave_codex.py`
- `orchestrator/tests/test_dev_wave_wait.py`

## 禁止 (各項目を個別に守る)

- **`git add` / `git commit` / `git stash` / `git checkout` / `git reset` を一度も実行しない。commit は親が行う。**
  (この wave の機能そのものが「起動器が終端で commit する」だが、それは親が起動した起動器の仕事であり、本 prompt の子であるお前は commit しない。)
- **docs を編集しない** (`docs/**`、`*.md`、`docs/handoff/` への file 作成を含む)。handoff・worklog・insight を書かない。
- 所有外の file (`tools/codex_worker_launch.py`、`tools/check_docs.py`、`hooks/**`、`.claude/**`、`orchestrator/tests/conftest.py` 等) を編集しない。
- 既存テストの期待値を変えない (反転・緩和・skip・削除・xfail 化を禁ずる)。例外はちょうど 1 つ:
  `test_dev_wave_wait.py::test_producer_cli_surface_has_no_pattern_input` の `expected_options` 集合へ `--commit-worktree` を**追加**すること (surface pin の更新。それ以外の assert は不変)。
- 受理集合を指示外に変えない: flag 無しの `producer`、read-only 子、dry-run、`check-receipt` は挙動・stdout/stderr/rc/receipt bytes とも 1 byte も変えない。
- fixture へ現行 hash を差し込む・実体を stub して緑にする (F27/F649) をしない。helper・死亡判定を monkeypatch しない。失敗注入は既存 `subprocess.run` seam か「identity 無し repo」等の実状態で行う。
- 期待値へ揮発 payload (HEAD sha、mtime) を焼き込まない。
- 新しい保存 framework・台帳・schema・sidecar JSON・汎用 option を作らない。stdout 1 行と commit だけ。
- `git_state._run` の allowlist 判定・例外処理を広げない。`GIT_COMMANDS` へ足すのは裁定 §2.1 の 5 操作だけ。

## 実装の要点 (裁定 §2 を正とし、ここは補足)

- helper の返値は `(status, detail)`: `committed`/sha、`clean`/None、`deferred`/reason、`refused`/reason、`failed`/reason。
  stdout 行 `worktree-commit: ...` は helper が `print(..., flush=True)` で 1 行出す。`refused`/`failed` は stderr にも `NG: worktree-commit ...` を出す。
- 起動器の最終 rc: launcher rc≠0 → そのまま; rc=0 ∧ (committed|clean|deferred) → 0; rc=0 ∧ (refused|failed) → **3**。
  read-only は helper を呼ばず何も出さない。workspace-write ∧ stage∉{author,fix} は `worktree-commit: skipped reason=stage` を出して呼ばない (rc 不変)。dry-run は helper を呼ばない。
- 待ち手: `--commit-worktree` は `Path`、既定 `None`、指定時は絶対 path 必須 (相対は既存の usage rc=2 経路)。`wait_for_producer` に keyword `commit_worktree=None` を足し、
  `_PidState.DEAD` で `break` した直後に helper を 1 回呼ぶ (`actor="waiter"`、`receipt_path=None`、`launcher_rc=None`、wave/job_id/stage は `"unknown"`)。
  既存 outcome が成功で helper が `refused`/`failed` → `_Outcome(RC_FAIL_CLOSED, "producer-commit", detail=...)` (既存の `_attestation_detail` 形式に倣う)。
  check-only は触らない。`_Effects` に新しい field を足す必要があるなら、既存 `run` seam を使う形を優先し、`_FakeEffects` を壊さない (既存テストの `_Effects(...)` 直接構築が壊れないよう default 値を付ける)。
  helper 内の Git 実行は `git_state._run` (subprocess.run) 経由でよい。待ち手の既存 `_Effects.run` を経由させる必要はない (裁定: helper は git_state の関数)。
- provenance: receipt JSON (`receipt_path`) が読めれば `recorded_model`/`recorded_effort` → 空なら `requested_model`/`requested_effort` → それも無ければ `unknown`。正規化は裁定 §2.1。`none` → `unknown`。
  本文の値は改行と `;` を除去して 1 行にする。message file は `tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, dir=None)` で **repo 外** (系の tmp) に作り、`commit -F` 後に unlink する。
- commit は `-c commit.gpgSign=false`。identity は repo-local config に依存 (helper は identity を補わない)。`_git_env` の hardening を維持する。
- timeout: `add-all` と `commit-file` は 120 秒 (`_run(..., timeout_s=120)`)。他は既定。
- `operation-in-progress` の marker: `rev-parse --path-format=absolute --git-path <name>` で `MERGE_HEAD` / `CHERRY_PICK_HEAD` / `REVERT_HEAD` / `rebase-merge` / `rebase-apply` の実在を見る (1 述語)。
- primary-worktree: `rev-parse --path-format=absolute --git-dir` と `--git-common-dir` が同じ path なら主 checkout。

## テスト (裁定 §2.5 の表を実装。実体を名指し、実 git repo は `tmp_path` に `git init` して作る)

- `test_dev_waves_git_state.py`: `test_commit_worker_worktree_records_residue_then_noop`、`test_commit_worker_worktree_provenance_values`、
  `test_commit_worker_worktree_refuses_detached_protected_primary_root` (parametrize)、`test_commit_worker_worktree_defers_merge_in_progress`、
  `test_commit_worker_worktree_failed_keeps_residue`。
  正例では `tools/check_ai_provenance.py` の `AGENT_VALUE` を import して trailer 行を fullmatch し、model/reasoning が `none` でないことを assert する
  (import は `sys.path` に `tools/` を足して `import check_ai_provenance` — 既存 `orchestrator/tests/test_check_ai_provenance.py:24` と同形)。
  また `git diff --cached <base> -- <path>` の出力 bytes が helper commit の前後で一致することを assert する (`<base>` = repo 作成時の初期 commit)。
  linked worktree の検査には `git worktree add` で実 linked worktree を作ってよい (主 checkout 側が `refused primary-worktree`、linked 側が `committed`)。
- `test_dev_wave_codex.py`: `test_workspace_write_author_commits_after_launcher` (parametrize launcher rc 0/7、fake launcher script が worktree に file を書いてから exit)、
  `test_terminal_commit_failure_rc` (rc=0 → 3 + stderr `NG:`; rc=7 → 7)、`test_read_only_and_non_author_never_commit`、`test_dry_run_never_commits`。
  fake launcher は既存テストの手法 (`monkeypatch` で `subprocess.run` を差し替えるか、`--repo-root` の `tools/codex_worker_launch.py` を fake script に置換した tmp repo) のうち
  既存 file の書き方に合わせる。`tools/codex_worker_launch.py` の実物を起動しない。
- `test_dev_wave_wait.py`: `test_producer_commit_worktree_after_death` (実 producer = 短命 `subprocess.Popen(["sleep","0"])` 等の死後、done/artifact 実 file、tmp repo に residue → `committed`)、
  `test_producer_without_commit_flag_preserves_bytes` (同条件で flag 無し → stdout/stderr/rc/receipt raw bytes が residue の有無で不変、HEAD 不変)、
  `test_producer_commit_worktree_requires_absolute_path`、`test_producer_cli_surface_has_no_pattern_input` の集合更新。
- 緑には実走 nodeid・範囲を併記する。**sandbox では pytest を走らせられない (socket 拒否)。** 実走不能なら `closed` と申告せず「実装済み・未実走」と書く。
  最低限、各 test module を import して対象 test 関数を直接呼び出し (`tmp_path` は `tempfile.mkdtemp()` で代用、`monkeypatch`/`capsys` は簡易代役)、fixture が成立するか確かめ、
  さらに実装の対象検査を一時的に外して期待どおり赤化するか (反実仮想) まで確かめて、その結果 (`DIRECT_CALL_PASS` / `DID NOT RAISE` 等) を報告に書け。確認後は実装を元に戻す。
- 制約 meta-test を自ら洗い出す (F42): `test_dev_wave_codex.py` の plain runner (`:638` 付近、引数なしで test を呼ぶ) に新 test が乗るか、
  `test_check_docs.py` の waiter consumer pin (`_check_dev_wave_waiter_consumer_pins`)、`test_dev_waves_isolation_contract.py` 等で `git_state.py` の `GIT_COMMANDS` や
  `dev_wave_wait.py` の CLI surface を pin しているものを grep で探し、影響を報告する。

## 報告 (最終メッセージ本文に全文。見出しはすべて `##`。最後の節は必ず `## 総括` (`#` 2 個)。`### 総括` と書いてはならない)

## 変更 file と関数 (file:line)
## 受理・拒否挙動 (scope 前の現行挙動 → 変更後。flag 無し・read-only・dry-run が不変であることを明記)
## 実走・直接呼び出しの結果 (nodeid、DIRECT_CALL_PASS / 赤化確認)
## 所有外 caller・共有 fixture・consumer test の波及可能性 (静的列挙)
## 期待赤 (親 docs 未 land による赤があれば finding 集合を名指し)
## 総括
