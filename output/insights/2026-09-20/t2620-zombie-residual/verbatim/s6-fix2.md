## 変更点

[test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2620-unit-tests/orchestrator/tests/test_codex_worker_launch.py:4607) の4607〜4615行で `unknown_sources_seen` を指定の真偽値に正規化し、理由を3行コメントで記載。4631行の期待値を `True` に変更しました。他フィールドの厳密比較と単一の等値 assert は維持しています。

## 実走

指定コマンドで **5 passed、211 deselected（19.84秒）**。`git diff --check` も成功しました。

実走 nodeid（共通接頭辞：`orchestrator/tests/test_codex_worker_launch.py::`）：

- `test_t2620_orphan_running_is_rejected`
- `test_t2620_orphan_zombie_is_rejected`
- `test_t2620_sigterm_ignore_subreaper_is_rejected`
- `test_t2620_orphan_mixed_is_rejected`
- `test_t2620_check_receipt_rejects_residual_only_changes`

## 波及

変更は指定ファイルの専用 helper 内だけです。他 test・共有 helper・fake mode・harness への変更なし。production 差分ゼロ。禁止された Git 操作は実行していません。

## 総括

実装済み：fix2 全項目、焦点5本成功。  
未実走：ファイル全体の並列走・変異再走。  
未着手：なし（本依頼の範囲）。