実装済み・未実走です。[対象テスト関数](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2417-recovery-author/orchestrator/tests/test_t2187_adaptive_const_probe.py:4530)だけを修正しました。

局所diffの要点:

```diff
- result path名だけを24件用意
- rowsなし、thread/seed軸なしのgroup
- _validate_published_group(..., [], ...)
+ 既存の正常なCERT_TUNED_CELLを使用
+ 3 workload x 8 slotの24 result fileと24 rowsを生成
+ thread=48、既存claim、genome、patch、source、execution identityを設定
+ _validate_published_group(..., result_files, ...)
```

両経路の期待値 `performance-artifact-contract-rejected` は変更していません。

| 確認対象 | 状態 | 根拠 |
|---|---|---|
| 古いfixtureによる先行 `group-receipt-collision` | partial | 正常group前提へ局所修正済み。親の実走待ち |
| 両公開経路の期待値維持 | closed | assert文字列、productionコードとも変更なし |
| 受理集合やgateの緩和 | closed | production、stub、hash、skipへの変更なし |
| 回帰 | regressedなし | 構文確認済み。実走結果は未取得 |

静的な波及範囲:

- caller: `_group_receipt_payload` と `_validate_published_group` の呼び出し形は不変です。
- 共有fixture: 変更なし。既存の認証定数と `tmp_path` のみを利用します。
- consumer test: 他テストへの共有状態はなく、生成物は当該テスト固有の一時領域内です。
- meta-test: 関数名とnodeidは不変です。duration ledgerの既存entryにも変更不要です。
- 他file、production、docs、台帳は変更していません。

確認結果:

- Python AST構文確認: 成功
- 当該関数内のU+0300からU+036F: 検出なし
- pytest、`run_tests.py`、build、qsub、qstat: 指示どおり未実行

## 総括

正常な24-request certification groupをfixtureで成立させ、未認証のT-2417性能成果物だけが両公開経路で拒否される形へ修正しました。実装済み・未実走であり、最終的なclosed判定は親のテスト実走後です。