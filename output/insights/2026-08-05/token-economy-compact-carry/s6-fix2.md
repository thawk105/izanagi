## 総括

- [test_spool_fold.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1932): archive bytes と rotation 後 current bytes の合計が 320 超である assertion に変更。
- rotation 前相当の総量と rotation 後 current サイズを別々に検査し、`> 320` と `<= 320` の自己矛盾を解消。
- `py_compile` と `git diff --check`: rc=0。
- `pytest --collect-only`: `pegasus02` ログインノードでは pytest 全般禁止のため未実施。pytest 緑は主張しない。