## 総括

- F11: **closed** — 外部 temp root 化・`PYTHONPATH` 設定・SHA-256 一致検査は [test_pytest_failure_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:488)、終了形は同ファイル:510、E2E は同ファイル:615。
- E2E は `-p` 強制ロードなしの通常 conftest discovery を維持。F11 対応で monkeypatch は不使用。
- 実走 argv: `python3 -m pytest orchestrator/tests/test_pytest_failure_digest.py orchestrator/tests/test_plain_runner_coverage.py orchestrator/tests/test_real_repo_serialization.py`
- 実走結果: **26 passed in 11.09s**。
- 前後の `git status --porcelain`: ともに `MM orchestrator/tests/conftest.py`、`AM orchestrator/tests/test_pytest_failure_digest.py` で完全一致。
- 残る赤: **なし（指定された3ファイル同時実走の範囲）**。