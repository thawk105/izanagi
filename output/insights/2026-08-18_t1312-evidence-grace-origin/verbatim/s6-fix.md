F-1 / F-2 を実装しましたが、pytest が開始できなかったため、両方とも `partial` です。docs 編集・commit はしていません。

| 所見 | 状態 | 判定根拠 |
|---|---|---|
| F-1 | `partial` | 旧 help を前方 prefix として復元し、新語句を独立 chunk として末尾へ配置しました。[tools/dev_wave_codex.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/dev_wave_codex.py:99)。新設 assertion と既存 assertion は維持されています。[test_dev_wave_codex.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_dev_wave_codex.py:598) |
| F-2 | `partial` | `no_rollout` の2テストへ receipt の session 非空 assertion を追加しました。[test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:4377)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:6143)。`no_thread` は変更していません。[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:6154) |

変更したのは次の2ファイルです。

- `tools/dev_wave_codex.py:99-104`
- `orchestrator/tests/test_codex_worker_launch.py:4377-4381, 6143`

段5由来の未commit差分4ファイルは維持し、`max_wall_clock_s`、schema、receipt field 集合、既存期待値には触れていません。

F-2 で使用した receipt field は `attempts[].session_ids` です。許可 field 集合への実在は [codex_worker_launch.py:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:102)、receipt への生成は [codex_worker_launch.py:1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:1638) で確認しました。

静的な波及確認:

- CLI caller への差は help 表示だけです。既定値導出・検証・launcher argv 転送は不変です。
- 共有 helper `_help_option_block`、`_base_command`、`_run_case`、`_run_main_in_process` は今回変更していません。
- `no_rollout` consumer 2本だけを強化し、空 session が検査対象の `no_thread` は維持しました。
- test node の新設・改名はないため、収集 meta-test や node pin の更新は不要です。

検証結果:

- `git diff --check`: 成功
- 変更4ファイルの AST parse: 成功
- help 正規化 probe: 成功。初回 probe は indentation を潰さない誤実装で赤、テストと同じ正規化へ直して成功
- `check_codex_agents.py`: 成功
- `check_docs.py`: 成功
- 焦点3 node: `tools/run_tests.py` が `qstat -Q preflight rc=1`、`rc=16` で開始前停止。テスト結果はありません

## 総括

F-1 と F-2 は実装済み・pytest 未実走です。  
両所見は `partial` であり、`closed` とは申告しません。  
docs 編集、commit、既存期待値の変更は行っていません。