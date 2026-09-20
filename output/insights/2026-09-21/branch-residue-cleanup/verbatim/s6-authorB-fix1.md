## 変更一覧

- `tools/check_docs.py:286`: 予算を `TextLimit(7_058, 110)` に更新。
- `orchestrator/tests/test_check_docs.py:7188,7193`: anchor を「他へ引き渡さない」、変異後を「他へ引き渡してよい」に更新。
- `orchestrator/tests/test_check_docs.py:9958,9973`: 予算の期待値を 7,058、超過メッセージを `7059 bytes > 予算 7058 bytes` に更新。

## 検証

- worktree root で `python3 tools/check_docs.py` 実走：**rc 0、違反なし**。
- `git diff --check`：rc 0。
- pytest：**実装済み・未実走**。

## 総括

指定の 2 ファイル、計 5 行を修正しました。
fixture 本文、本文長 7,055 bytes、超過用 padding は維持しています。
commit・branch 操作・push は行っていません。