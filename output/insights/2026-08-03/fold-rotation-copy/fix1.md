## 総括

- fix 1 — **closed**: 正規 rotation path を regular file から symlink へ typechange する fixture に変更し、`T` 対照 assert と `path-status` 期待を維持しました。[test_dev_waves_git_state.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:348)
- fix 2 — **closed**: single-dash option を `-r/-m/-z` に限定し、`-zM/-zC/-zB` を拒否。長形式の禁止と `--no-renames` の許可も維持しました。[test_dev_waves_git_state.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:75)
- fix 3 — **closed**: land 後に rotation basename の archive README 掲載と、worklog の 900-byte 閾値以下を検査します。[test_dev_wave_land.py:1641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1641)、[同:1741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1741)

pytest は走らせていません。したがって、次の対象 nodeid の緑は主張しません。

- `test_commit_diff_disables_move_detection_by_contract`
- `test_declared_fold_rejects_typechange_status`
- `test_land_folds_rotation_inside_lock`

Pegasus `pegasus02` のログインノード規律と既知の dispatch 認証失敗に従い、迂回実行はしていません。submodule index lock 由来の赤も発生していません。

静的検査は以下が成功しました。

- `python3 -m py_compile`：編集対象 2 ファイル
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

mutation spec の `old` を本体コードへ逐語照合し、M01、M02、M03、M04、M05、M06、M07、M08、M09、P01 はすべて各 **1 回**でした。

静的な波及可能性:

- 本体 caller は `tools/dev_wave_land.py`、`tools/dev_waves/checker.py`、`tools/dev_waves/daemon.py`。本体を変更していないため実挙動は不変ですが、親の全走対象です。
- 共有 fixture `_fold_commit`、`_wave_fragment_commit`、両テストファイルの `_repo` は未変更です。
- mutation harness と `test_plain_runner_coverage.py` は親側での再検証対象です。
- テスト名は変更していません。

未解決・停止項目は pytest／変異本走の未実施です。また、M01/P01 の mutation spec 修正は指示どおり親担当として `output/` に触れていません。docs、本体、stage、commit も変更していません。