単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-fix1

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-reviewA-1.md` — 段 6 レビュー A (所見 1・3・4 と推奨 fix 1・3・4 が本 fix の対象)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-reviewB-1.md` — 段 6 レビュー B (「テスト所見」の赤 1 件の最小是正案が本 fix の対象)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s4-adjudication.md` — 段 4 裁定 (実装の正本。§2 plan v2、§2.5 テスト)。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s5-focus-run.log` — 親の焦点走 log (461 passed / 1 failed、赤の本文は 75〜124 行)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-fix1/tools/dev_waves/git_state.py` の 229〜330 行 (`commit_worker_worktree`、編集対象)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-fix1/orchestrator/tests/test_dev_waves_git_state.py` の 1300〜1470 行 (helper テスト、編集対象)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-fix1/orchestrator/tests/test_dev_wave_wait.py` の 5087〜5240 行 (待ち手テスト、編集対象)。全文 (10k 行) は読まない。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2638-fix1/tools/dev_wave_wait.py` の 1720〜1830 行 (`_initial_start_time`・`_pid_state`・stderr 診断の出所。読むだけ、編集しない)。読めなければ即停止。

## 依頼

[T-2638] 段 6 の fix。前巡の実装 (commit d8e512556、この worktree の HEAD fe1e6662e に含まれる) に対し、レビュー 2 本が一致した must-fix 2 件と nit 1 件を直せ。それ以外は変えない。

1. **`test_producer_commit_worktree_after_death` の stderr 期待 (must-fix、レビュー A 所見 1 / B テスト所見):**
   現行 `assert captured.err == ""` は、待ち手の既存 stderr 診断「`producer: /proc/<pid>/stat を読めないため pid-only へ縮退します`」
   (producer 回収後の再観測で消滅済み `/proc/<pid>/stat` を読むときに出る、実装は変えない) を拒んで赤になった。
   レビュー B の最小是正案どおりに置き換える — 任意の stderr を許さず、当該 PID の既存診断だけを許す:
   ```python
   assert "NG:" not in captured.err
   assert "producer-commit" not in captured.err
   assert captured.err in (
       "",
       f"producer: /proc/{producer.pid}/stat を読めないため pid-only へ縮退します\n",
   )
   ```
   診断の逐語は `tools/dev_wave_wait.py` の実装から取り、推測しない。`RC_OK`、stdout 完全一致、commit 数、`HEAD:residue`、trailer、receipt 成功の assert はすべて維持する。
   sleep seam 内の「生存中は HEAD == base」assert も維持する (変異 M13 の検出に必要)。
2. **message file の置き場 (must-fix、レビュー A 所見 3):** `tempfile.NamedTemporaryFile(dir=None)` は `TMPDIR` 次第で repo 内になりうる。
   `git-dir` (helper が既に `rev-parse --path-format=absolute --git-dir` で得ている path、linked worktree なら `.git/worktrees/<name>/`) の直下に
   固定名 `izanagi-worker-commit.msg` で書き、`commit -F` 後 (失敗時も `finally`) に削除する。git-dir は作業木の外なので `add -A` に拾われない。
   `tempfile` import が不要になれば外す。テスト `test_commit_worker_worktree_records_residue_then_noop` に「commit 後に `<git-dir>/izanagi-worker-commit.msg` が不在」と
   「作業木の `git status --porcelain --untracked-files=all` が空」の assert を足し、`test_commit_worker_worktree_failed_keeps_residue` にも同 path 不在の assert を足す。
3. **`<base>` patch 比較の範囲 (nit、レビュー A 所見 4):** 同テストの `patch_bytes()` を `git diff --cached <base>` (path 限定なし、`git add -A` 後) にして、
   tracked 編集・削除・untracked 追加を含む全所有差分の bytes が helper commit の前後で一致することを固定する。前処理の `git add tracked` を `git add -A` にしてよい
   (helper 側の `add -A` が冪等であることの確認にもなる)。

## 所有 (編集してよい file — これ以外は 1 byte も変えない)

- `tools/dev_waves/git_state.py` (`commit_worker_worktree` の message file 部分だけ)
- `orchestrator/tests/test_dev_waves_git_state.py`
- `orchestrator/tests/test_dev_wave_wait.py`

## 禁止 (各項目を個別に守る)

- **`git add` / `git commit` / `git stash` / `git checkout` / `git reset` を一度も実行しない。commit は親が行う。**
- **docs を編集しない** (`docs/**`、`*.md`、`docs/handoff/` への file 作成を含む)。handoff・worklog・insight を書かない。
- 所有外の file (`tools/dev_wave_codex.py`、`tools/dev_wave_wait.py`、`tools/codex_worker_launch.py`、`hooks/**` 等) を編集しない。
- **既存テストの期待値を変えない** (反転・緩和・skip・削除・xfail 化を禁ずる)。tracked の既存テストとは HEAD fe1e6662e に含まれる全テストを指し、
  前巡で追加した本 wave のテストも含む。本 fix で触ってよい期待値は上記 1〜3 に名指した箇所だけ。赤なら実装側が誤りとし、期待値が誤りと考えるなら実装を変えず報告して止める。
- 受理集合を指示外に変えない。read-only 子・dry-run・flag 無しの待ち手・check-only の挙動は不変。
- 代役 (test double) の signature/入力の修正は上記 1 の範囲で許す。production を代役に合わせて緩めない。fixture へ現行 hash を差し込まない (F27)。
- 期待値へ揮発 payload (HEAD sha、mtime) を焼き込まない。
- 新しい保存 framework・台帳・schema・汎用 option を作らない。

## 検査・報告 (最終メッセージ本文に全文。見出しはすべて `##`。最後の節は必ず `## 総括` (`#` 2 個)。`### 総括` と書いてはならない)

sandbox では pytest を走らせられない (socket 拒否)。実走不能なら `closed` と申告せず「実装済み・未実走」と書く。
最低限、変更した test 関数を直接呼び出し (`tmp_path` は `tempfile.mkdtemp()`、`capsys` は簡易代役) fixture が成立するか確かめ、
さらに (a) 実装の message file 置き場を一時的に `dir=None` へ戻して新 assert が赤化するか、(b) 待ち手テストで `"NG:"` を stderr に混ぜると赤化するか、の反実仮想を確かめて結果を書け。確認後は実装を元に戻す。
制約 meta-test (`test_dev_wave_codex.py` の plain runner、`GIT_COMMANDS` 禁止 verb 検査) への影響を静的に列挙する。

## 変更 file と関数 (file:line)
## 受理・拒否挙動 (変更前 → 変更後。不変であるものを明記)
## 実走・直接呼び出しの結果 (nodeid、DIRECT_CALL_PASS / 赤化確認)
## 波及可能性 (静的列挙)
## 総括
