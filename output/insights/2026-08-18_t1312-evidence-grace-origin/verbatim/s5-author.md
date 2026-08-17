実装済みです。commit・docs 編集はしていません。

### 変更内容

- [tools/codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1793)
  - `spawn_completed_ns` を診断条件外で一度だけ取得。
  - 診断境界と evidence deadline が同じサンプルを使用。
  - `state.started_ns`、`max_wall_clock_s`、schema・field 集合は変更なし。
- [orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:1543)
  - `_base_command` に keyword-only `evidence_grace: str = "1.0"` を追加。
  - 行 3514–3611: preflight `0.10`、実在する `read_pid_identity` seam で spawn `0.02`、poll `0.01` を注入し、3 phase を exact 検査。
  - 行 3590–3611: `max_attempts=2`、`FAKE_SEQUENCE="retry_reject,no_rollout"` の attempt 2 回帰を追加。
  - 行 4271–4361: `diagnostics=None` の直接 `_attempt_loop` 回帰を追加し、5 poll 後の強制停止を検査。
  - 行 4364–4370、6123–6159: 既存 evidence 関門テスト3本を `evidence_grace="0.3"` に変更。
- [tools/dev_wave_codex.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/dev_wave_codex.py:94)
  - help に「子の起動完了時を起点とする」を明記。
- [orchestrator/tests/test_dev_wave_codex.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_dev_wave_codex.py:598)
  - 既存 help block assertion に新文言を追加。

### 新設 nodeid

- `orchestrator/tests/test_codex_worker_launch.py::test_evidence_grace_starts_at_spawn_completed`
- `orchestrator/tests/test_codex_worker_launch.py::test_evidence_grace_starts_at_spawn_completed_on_retry`
- `orchestrator/tests/test_codex_worker_launch.py::test_evidence_deadline_origin_is_diagnostics_independent`

### 静的な波及確認

- `_attempt_loop` の production caller は同一 launcher 内の1箇所です。全 attempt が新起点を使い、診断なしでも成立します。
- `_base_command` は当該 test file 内だけの keyword-only fixture です。既存 caller は既定 `"1.0"` のため互換です。既存3本のみ `"0.3"`、新設2本のみ `"0.05"` を指定します。
- 待機時間へ波及し得る consumer は、既存の incomplete-evidence 診断、unknown residual、rollout missing、thread missing の各テストです。後者3本は hardening 済みです。
- 既存の exact phase wiring テストが、deadline 用に別の時計サンプルを取る変異を引き続き検出します。
- `dev_wave_codex` の既定値導出・検証・launcher argv 転送には変更がなく、CLI consumer への機能差は help 文言だけです。
- meta-test は確認済みです。新規 test file ではないため `test_plain_runner_coverage.py` の file 集合更新は不要です。新 node は growth-hold 対象でなく、node pin 更新も不要です。

### 検証状況

pytest は未実走です。指定10 nodeを `tools/run_tests.py` で実行し、続いて collect-only も試みましたが、どちらも headroom 判定後に計算ノードへ dispatch され、`qstat -Q preflight rc=1`、runner `rc=16` でテスト開始前に停止しました。

- 観測されたテスト赤: 0件
- infrastructure failure: 2回
- 静的検査: 変更4ファイルの AST parse 成功、`git diff --check` 成功
- worktree の tracked 差分: 上記4ファイルのみ

### 受理・拒否挙動の差

変更前は evidence deadline が attempt 作成時から始まり、preflight と spawn の所要が猶予を消費するため、起動直後の子を evidence 不足として拒否し得ました。変更後は `Popen` と PID identity 読取後の `spawn_completed` から公称猶予全体を与え、その満了時に evidence が欠けていれば従来どおり拒否します。`max_wall_clock_s` は従来の起点と判定を維持し、先に発火すれば従来どおり停止します。

### plan v2 対応

- v2-1: 実装済み。同一 spawn サンプルを診断と deadline に使用。
- v2-2: 実装済み。3区間をそれぞれ `0.10`、`0.02`、`0.05` で exact 検査。
- v2-3: 実装済み。attempt 2 の旧起点変異を判別。
- v2-4: 実装済み。fixture kwarg追加と既存3本の `0.3` 化。
- v2-5: 実装済み。help と assertion を更新。
- 診断なし経路: 実装済み。5 poll と `evidence_forced_stop` を検査。

## 総括

- evidence 猶予の起点を子の起動完了時へ移し、wall-clock と schema は維持しました。
- attempt 1、attempt 2、診断なしの各経路を判別するテストを追加しました。
- 実装と静的検査は完了していますが、pytest は Pegasus dispatch 障害により未実走です。
- 親段で関連 node と受入全走の実走が必要です。