## 変更点

[test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2620-unit-tests/orchestrator/tests/test_codex_worker_launch.py) のみ変更。

- 1638〜1644 行：読取と field parse を `try` 内へ移し、`except (OSError, ValueError): continue` に変更。
- 4565〜4568 行：timeout 時の回収責任、finally の限界、単回列挙の対象範囲をコメントに明記。

## 実走

指定コマンドで **5 passed, 211 deselected（20.04 秒）**。

以下の nodeid はすべて `orchestrator/tests/test_codex_worker_launch.py::` 接頭辞：

- `test_t2620_orphan_running_is_rejected`
- `test_t2620_orphan_zombie_is_rejected`
- `test_t2620_sigterm_ignore_subreaper_is_rejected`
- `test_t2620_orphan_mixed_is_rejected`
- `test_t2620_check_receipt_rejects_residual_only_changes`

`git diff --check` も成功。

## 波及

他 test・helper への変更なし。production 差分ゼロ。期待値・test 名・fake mode・観測 dict の key・1 回の等値 assert を維持。commit 操作なし。

## 総括

実装済み：F1 修正、F2/N2 コメント追記。  
未実走：なし（指定の 5 件は成功）。  
未着手：なし。