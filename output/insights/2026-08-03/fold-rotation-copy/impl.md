## 総括

実装を完了し、指定された 3 ファイルだけに未コミット差分を残しました。

- [git_state.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:90)
  - `commit-diff` の `-M -C` を逐語どおり `--no-renames` に変更。
- [git_state.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:763)
  - 冗長な R/C 特判だけを削除。
- `_landed_fold_output_path` と `_diff_entries` は変更していません。
- [test_dev_waves_git_state.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:75)
  - 指定名のテストを 8 本追加。C100 対照、2 archive、README 単独、typechange、D+A/R、R/C parser を固定。
- [test_dev_wave_land.py:1641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1641)
  - 実 `spool_fold.plan_fold/apply_fold` を使う lock 内 rotation 統合テストを追加。

現行の M/D/A 閉集合、path allowlist、rotation 最大 1 件、README 結合、minimum shape は変更していません。valid rotation の Git 表示だけが C から A/M へ正規化されます。

テスト実走:

- 次の範囲を `tools/run_tests.py` で計算ノードへ dispatch しましたが、テスト開始前に rc=16 で停止しました。
  - `orchestrator/tests/test_dev_waves_git_state.py` 全体
  - `orchestrator/tests/test_dev_wave_land.py::test_land_folds_rotation_inside_lock`
  - `orchestrator/tests/test_plain_runner_coverage.py` 全体
- 原因は `qstat -Q` の `NQSconnect: [API EACCTAUTH] Unknown user-id (uid: 31609)` です。
- したがって、新規 9 nodeid、既存テスト、meta-testはいずれも「走らせていない」扱いで、緑は主張しません。

静的検査結果:

- `python3 -m py_compile`：3 ファイル成功
- `git diff --check`：成功
- expected nodeid の AST 実在検査：11/11、重複なし
- `python3 tools/check_codex_agents.py`：成功
- `python3 tools/check_docs.py`：成功

変異 spec の逐語照合:

- M01=1、M02=1、M03=1、M04=1、M05=1
- M06=1、M07=1、M08=1、M09=1、P01=1
- 各 `old` anchor は対象実装に逐語一致し、それぞれちょうど 1 回存在します。

静的な波及:

- `tools/dev_wave_land.py`: valid rotation fold が rollback せず `landed` へ進む。null-fold、D+A fragment rename、reason/API は不変。
- `tools/dev_waves/checker.py`: valid rotation receipt の `fold-commit` が pass になる。
- `tools/dev_waves/daemon.py`: valid rotation recovery が受理される。
- 共有 fixture `_fold_commit`、`_seed_pending`、`_wave_fragment_commit`、`_repo` は変更せず再利用しています。既定挙動への変更はありません。
- checker/daemon の consumer test は直接変更しておらず、親の全走での確認が必要です。

未解決・停止項目:

- Pegasus scheduler 認証によりテストとmeta-testを実走できていません。親環境での独立再走が必要です。
- docs、`output/`、stage/index は変更しておらず、`git add`・commit も実行していません。
- 既存の未追跡 `output/insights/2026-08-03_fold-rotation-copy/` は親所有物として非接触です。