## 総括

- 削除行: `assert policy.forbidden_roots == (Path("/tmp"), Path("/scr"))`
  - [test_b10_backoff_shape_sweep.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-formal-run/orchestrator/tests/test_b10_backoff_shape_sweep.py:1583)（削除前）
  - 同ファイル `:1607`（削除前）
- 差分は上記2行の削除のみ（追加0・削除2）。両テストの残りの検査は1文字も変更していません。
- 指定2 nodeidを起動しましたが、Pegasus `qstat -Q` preflight失敗（runner `rc=16`）により子テストは未開始です。**実装済み・未実走**。
- `check_codex_agents.py`、`check_docs.py`、`git diff --check` は成功しました。
- tracked file の差分は指定ファイルだけです。既存の未追跡 `output/insights/.../README.md` には触れていません。テストrunnerが一時生成したdispatch receipt類は削除済みです。
- commit、add、stash等は実行していません。