## 変更 file と関数 (file:line)

- `tools/dev_waves/git_state.py:231` — `commit_worker_worktree`：message file を git-dir 直下の固定名へ変更。`finally` の削除を維持し、不要な `tempfile` import を削除。
- `orchestrator/tests/test_dev_waves_git_state.py:1341` — `test_commit_worker_worktree_records_residue_then_noop`：全差分の patch bytes 比較、message file 不在、untracked を含む clean 検証。
- 同ファイル `:1448` — `test_commit_worker_worktree_failed_keeps_residue`：失敗後の message file 不在を検証。
- `orchestrator/tests/test_dev_wave_wait.py:5120` — `test_producer_commit_worktree_after_death`：指定どおり stderr 期待を修正。

## 受理・拒否挙動

- stderr 空のみ → 空または当該 PID の既存診断1行のみを許容。`NG:`・`producer-commit`・未知の診断は拒否。
- message file は環境依存の一時ディレクトリ → git-dir 直下。成功・失敗時とも削除。
- patch 比較は tracked 1ファイル → 編集・削除・追加の全差分。
- 生存中 HEAD、RC_OK、stdout、commit 数、residue、trailer、receipt の検証は維持。
- read-only、dry-run、flag 無し、check-only、production の受理・拒否分類は不変。

## 実走・直接呼び出しの結果

以下はすべて **DIRECT_CALL_PASS**：

- `orchestrator/tests/test_dev_waves_git_state.py::test_commit_worker_worktree_records_residue_then_noop`
- `orchestrator/tests/test_dev_waves_git_state.py::test_commit_worker_worktree_failed_keeps_residue`
- `orchestrator/tests/test_dev_wave_wait.py::test_producer_commit_worktree_after_death`

待ち手には `tempfile.mkdtemp()` と簡易 capsys を使用。

- stderr に `NG:` を追加：**赤化確認**。
- メモリ上で旧 `dir=None` 実装へ戻し、作業木内を一時ディレクトリに指定：helper 2テストとも **SURVIVED**。削除後の assert では使用中の配置先を検出できません。
- 反実仮想後は復元済み。`git diff --check` 成功。
- pytest は sandbox 制約により未実走。

## 波及可能性

- `test_dev_wave_codex.py` の plain runner：関数追加・signature 変更なし。収集・呼出し方式への変更なし。
- `GIT_COMMANDS` 禁止 verb 検査：コマンド表・禁止集合とも変更なし。
- helper 利用元への変更は message file の配置先のみ。呼出し契約・rc 合成・receipt 処理は不変。
- 差分は所有3ファイルのみ。docs 編集・作業ブランチへの commit は未実施。

## 総括

**実装済み・未実走**。直接呼び出し3件は成功しました。`dir=None` の反実仮想は赤化せず、指定 assert の検出限界が残ります。closed とは扱いません。