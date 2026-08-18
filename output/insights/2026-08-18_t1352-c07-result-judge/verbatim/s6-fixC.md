実装しました。commit は作成していません。docs は編集していません。

| 対象 | 状態 | 対応 |
|---|---|---|
| receipt 未消費 | closed（実装） | 3 表の metadata へ出所情報を接続 |
| 追加テスト | partial | pytest 未実走。親が実測 |
| regressed | なし（未実測） | AST parse・diff check のみ確認 |

編集範囲:

- [s8c_result_judge.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/campaign/s8c_result_judge.py:1265)（1265–1276、1340–1353、1446–1462）
- [test_s8c_result_judge.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/tests/test_s8c_result_judge.py:229)（229–237、801–902）

追加 nodeid:

- `test_publish_embeds_verified_floor_provenance_in_each_table`
- `test_publish_provenance_follows_another_ratified_freeze_receipt`
- `test_publish_floor_provenance_does_not_copy_floor_values`

`judge` の signature と `_JudgeResult` に床 receipt はなく、receipt は `publish_result_table` 内でのみ検証・metadata化されます。床値・threshold・raw measurement は表へ渡していません。既存の床値不変テストも変更していません。pytest は未実走です。

## 総括

- 検証済み receipt を公開表へ結び付けた。
- 3 表すべてに 6 種の出所情報を記録する。
- 別 freeze の receipt への追随をテスト化した。
- 床値の漏洩がないことをテスト化した。
- AST parse と `git diff --check` は通過した。
- 親による pytest 実測待ち。