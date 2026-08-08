テストのみ最小修正しました。実装済み・未実走です。

- `_prepare_campaign_identity` の spy を配線し、実際の `site`・`contract`・生成された `cfg` を記録。
- layout factory の spy で実際に生成された `layout` を記録。
- 対照 identity は元関数を直接呼び、観測値の上書きを防止。
- PEGASUS / OTHER は同一 helper を使用するため、両正例へ同じ配線が適用されます。
- 既存 assert は削除・緩和していません。
- `git diff --check` と AST parse は成功。pytest は指示どおり未実行です。

触った箇所は [test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_p3_autonomous_workload_trial.py:384) の以下です。

- 384行: `observed` の初期化を spy 配線前へ移動
- 397–415行: `_prepare_campaign_identity` spy の追加
- 418–421行、426行: layout spy の追加と既存 lambda の置換
- 480行: 対照 identity を保存済み元関数から生成

## 総括

テストファイル1件だけを変更しました。  
production・docs は変更していません。  
commit は作成していません。  
pytest は未実走です。