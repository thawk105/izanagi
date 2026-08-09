F12〜F15をすべて実装し、指定3ファイルの組み合わせ実走は `rc=0、26 passed` でした。既存の受理集合・exit code・緑走行の無出力は変更していません。

今回追加した monkeypatch はありません。既存F9の relay 定数検査用 monkeypatch はそのまま維持しています。裁定外の nested session 束縛化と2-byte安全余裕は未実装です。commit、add、stash、docs編集も行っていません。

## 総括

- F12: `closed` — repo外assert、全subprocessのbytecode抑止、repo外basetemp。[test_pytest_failure_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:478)
- F13: `closed` — 恒真hash assertを撤去し、実走後byte一致とmarkerによる自動discovery証明へ変更。[test_pytest_failure_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:542)
- F14: `closed` — 64文字placeholderで探索し、確定後manifest計算を1回に限定。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:601)、回数検査は [test_pytest_failure_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:424)
- F15: `closed` — repo外cwd、`PYTHONPATH`除去、`ModuleNotFoundError(name="tools")` 経路を実証。[test_pytest_failure_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:294)
- 実走 argv: `python3 -m pytest orchestrator/tests/test_pytest_failure_digest.py orchestrator/tests/test_plain_runner_coverage.py orchestrator/tests/test_real_repo_serialization.py`
- 実走結果: `rc=0、26 passed in 12.85s`
- 直前・直後 status: 完全一致（`MM conftest.py`、`AM test_pytest_failure_digest.py` の2行のみ）
- `find . -type d -name __pycache__ -newer <repo外基準ファイル> -print`: 出力0件。新規 `__pycache__` なし
- 残る赤: なし。裁定外所見は未実装・裁定外。