## 追加した負例

[指定テストファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2288-impl/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:1430)に、期待 spec の1つを1窓・3窓にする2ケースを追加しました。公開APIの停止 code を `aggregate_window_count_error` と照合します。

## 窓数検査まで到達する理由

spec の hash、summary の参照 hash、窓・campaign・層・標本・drop 件数を更新しています。環境・workload・threads は変更しないため、既存の較正 seam が引き続き整合します。

公開API呼び出し前に、producer による spec 受理、summary 読込、閉包一致検査を行う構成です。実行による確認は未了です。

## 変異 M3 が赤になる説明

1・3とも `< 1` は偽なので、M3では窓数検査を通過します。後続処理には窓数の再検査がなく、整合した入力から発行が成功するため、`pytest.raises` が「例外なし」で失敗する構成です。

## 実走結果 (nodeid と範囲)

対象ファイル全体を次のコマンドで試行しました。

```bash
PYTHONPATH=. python3 -m pytest orchestrator/tests/test_p3_b4_floor_artifact_issuer.py -q
```

追加 nodeid（同ファイル内）：

- `test_aggregate_public_rejects_non_two_window_spec[one-window]`
- `test_aggregate_public_rejects_non_two_window_spec[three-windows]`

PreToolUse hook が「Pegasus ログインノードでは pytest を実行できない」と拒否したため、**未実走**です。`git diff --check` は通過しました。

## 波及の静的列挙

- 指定テストファイルのみ70行追加。
- 既存テスト・fixture・期待値への変更なし。
- 本体・docs・duration ledger への変更なし。
- commit・git add なし。

## 未実走・未完了

通常テストとM3変異の実測は未了です。親での実走確認が必要です。

## 総括

指定の2負例を追加しました。
変更範囲は指定ファイルだけです。
実走はhookに拒否され、成功を確認できていません。