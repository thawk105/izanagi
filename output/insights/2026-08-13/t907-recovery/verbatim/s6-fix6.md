## 総括

- 変更箇所:
  - [tools/dev_wave_wait.py:1395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:1395)
  - [orchestrator/tests/test_dev_wave_wait.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:443)
  - [orchestrator/tests/test_dev_wave_wait.py:1559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:1559)

- `collections` は list、各要素は dict、6 key の exact 集合を要求します。`path`・`source` は `str`、残る4 key は `str | None` としました。根拠は checker の型定義 [tools/check_acceptance_reds.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/check_acceptance_reds.py:68) と書き込み処理 [tools/check_acceptance_reds.py:1455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/check_acceptance_reds.py:1455) です。

- 回帰テストを追加:
  - `collections` 欠落を拒否
  - 要素内の未知 key を拒否
  - 現行 schema の正常 receipt を受理
  - 既存 fake 2 箇所も現行 schema に更新

- 受理集合は緩めていません。top-level exact 一致、checker rc、status、hash・tip・schema、非空 nodes、`non-attributable` 分類の検査は維持されています。[tools/dev_wave_wait.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:1387)

- 検査:
  - `py_compile.compile(..., doraise=True)`: 成功
  - `git diff --check`: 成功
  - `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py -q`: rc=16。`qstat -Q` preflight が rc=1 のため pytest 本体は未実走
  - Pegasus 規律に従い直接 pytest は起動していません。したがって、実装済み・未実走です。

commit・docs 編集は行っていません。既存の `test_dev_wave_land.py` 差分にも触れていません。