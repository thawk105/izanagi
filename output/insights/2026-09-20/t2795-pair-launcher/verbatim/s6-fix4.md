## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| red 1 | partial | 合計 pin は解消。後続の既存 assert が `2 == 1` で失敗。 |

## 変更の要約

`orchestrator/tests/test_campaign.py:5413` の `== 21` だけを `== 22` に変更しました。`campaign.pipeline.evaluate` の合計 `== 5` は維持しています。

## 実走結果

指定コマンドで実行しました。

- nodeid: `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- 件数: 選択1件、失敗1件
- rc: `1`
- `git diff --check`: 成功

## 未了・懸念

同テストの後続の `expected_run_calls` に `"p3_s4_loop.py": 1` が残り、5493行で実際の呼出し数2と不一致になっています。今回の編集範囲外のため変更していません。

## 総括

指定の1箇所の更新と実走は完了しました。red 1 は後続 pin の不整合により partial です。docs の変更、`git add`／`git commit` は行っていません。