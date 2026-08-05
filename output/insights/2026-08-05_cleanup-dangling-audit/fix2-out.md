## 総括

- **方式:** 自走 harness を採用。既存テストと同じ `pytest.main(["-q", str(Path(__file__).resolve())])` 形式で、fixture を含む全 node を実行します。allowlist と README は変更していません。
- **変更範囲:** `orchestrator/tests/test_audit_dangling_commits.py` のみ。commit・stage・docs 編集なし。
- **静的検査:**
  - `python3 -m py_compile ...`: 成功
  - `_HARNESS_SIGNALS` 相当の構造検査: 成功
  - `git diff --check`: 成功
  - 対象内のテスト関数: 8 件
- **指定された実走検査:** 現在地が Pegasus ログインノード `pegasus02` のため、上位規律に従い pytest および自走 harness は未実走。
  - `test_every_test_file_is_self_runnable_or_allowlisted`: 未実走
  - `test_audit_dangling_commits.py`: 未実走（期待 8 passed）
  - 自走 harness: 実行 0 件（未実走。実装上は全 8 node を指定）
- **波及:** pytest 通常収集の受理集合・既存期待値・監査ツール挙動は不変。素の runner が「0 件・exit 0」ではなく pytest を起動するようになります。
- **状態:** 実装済み・未実走。親による計算ノード上の指定 3 検査が残っています。