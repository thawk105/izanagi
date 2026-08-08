`_t428_descriptor_campaign_id` の build context を、production と同一の `A.build_run_context` / `A.GeneratorId` 経路へ修正しました。

| 状態 | 対応 |
|---|---|
| closed | ycsb-a / b / c の3件。同一クラス実体を渡すよう修正 |
| partial | なし |
| regressed | 静的確認上なし。production・期待値は未変更 |

今巡・前巡の追加テスト差分も検索し、同型箇所が他にないことを確認しました。`git diff --check` は通過しています。

## 総括

- 変更: [test_autonomous_trial_completeness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_autonomous_trial_completeness.py:178) の2行のみ
- production の型検査は維持
- docs 編集なし
- commit なし
- pytest は指示どおり未実走
- 実装済み・未実走です