静的レビューではmust-fix、regressedともに未検出です。実行による確認が必要な所見はpartialとします。

| 所見 | 判定 | 根拠 |
|---|---|---|
| 改行を跨ぐ巨大なangle偽リンク | partial | `link_targets`がCR/LFと内部の山括弧を除外。bare候補へのフォールバックも防止し、後続の正常リンクを残す回帰テストを追加 |
| 不正候補だけの無視 | partial | NUL・URL解析の`ValueError`を候補単位で除外。リンク先の`stat`では`ENOENT`・`ENOTDIR`・`ENAMETOOLONG`だけを無視 |
| 正常リンクの保護 | partial | 移動前後の解決先比較と保留の反復判定を維持。inline・image・reference・HTMLについて内部移動と外向き保留のテストを追加 |
| 真の読取・権限エラー | partial | その他の`OSError`は再送出し、読取時のエラーも`reference scan failed`として失敗。読取／リンク先statの権限拒否テストを追加 |
| 既存正例・負例の期待値 | closed | fix開始時の読取記録と現行ファイルを照合し、既存テスト252行が全行一致。追加は末尾の4関数・9ケースのみ |

確認箇所は`tools/insights_date_layout.py:83,110,201`と`orchestrator/tests/test_insights_date_layout.py:255`以降です。

## 総括

局所修正は報告された原因に対応し、既存テストの緩和もありません。編集なし、テスト・実repo planは未実走です。親の並行実行結果も未確認のため、実動作の合格・原因の完全解消とは判定していません。