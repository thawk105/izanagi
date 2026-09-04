## 変更

[orchestrator/tests/test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_a2_certification.py:444) の末尾に指定の自走 harness を追加しました。allowlist は変更していません。

## 検証

- `_self_runnable` 判定: `True`
- `git diff --check`: 成功
- tracked 差分: 対象1ファイルのみ
- allowlist 非掲載かつ README 未変更のため、`test_allowlist_has_no_stale_or_self_runnable_entries` への悪影響なし

## テスト

実行ラッパー経由で指定の2ファイルを試みましたが、Pegasus の `qstat -Q` 事前確認が失敗しました。

- 結果: `rc=16`
- 子プロセス: 未起動
- 実走 nodeid: なし
- 実走件数: 0件
- 状態: 実装済み・未実走

ラッパーが診断 receipt を `output/pegasus-dispatch/19123b7f8fb17ac13daf45957a3be636/receipt.json` に自動保存しています。

## 総括

- 変更ファイル: `orchestrator/tests/test_plot_a2_certification.py`
- 現在行数: 447行
- 差分: 4行追加、削除なし
- commit: 未実施
- 未対応事項: インフラ復旧後の2テストファイル実走のみ