## 実行した command

- 指定 producer を更新モードで 1 回実行: rc 0
- 指定の `--add-only --check` を 1 回実行: rc 0
- 更新前後を読み取り専用スクリプトで比較
- 検算用の一時ファイルは削除済み

## 検算

- 追加 nodeid: 54 件
- 総 entry 数: 22177 → 22231
- 既存 entry: 22177/22177 行が byte exact
- 既存値の変更: 0 件
- 既存 entry の削除: 0 件
- 追加内訳:
  - `test_axis_b5_search_executor.py`: 34 件
  - `test_axis_b5_search_parsers.py`: 20 件
- 上記以外の追加 nodeid: 0 件
- `--check` は生成 bytes の一致を確認し、rc 0
  - `added=0`
  - `skipped_existing=54`
  - `excluded_failure_or_error=0`

## 未実走・未実装

追加の test suite は依頼範囲外のため未実走です。未実装事項はありません。

## 総括

[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-ledger/orchestrator/tests/acceptance_duration_ledger.json) に producer 出力の 54 件を追加しました。今回、他の repository file は編集せず、commit、git 状態変更操作、外部 network 利用も行っていません。