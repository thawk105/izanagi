`orchestrator/tests/test_hold_inventory.py` の期待 golden を更新しました。

- 再導入された 14 node を期待表から削除
- 残存 2 node の reason を現 registry と完全一致する literal に更新
- assertion、skip、registry、他ファイルは変更なし
- commit、stage、docs 編集なし
- 失敗した dispatch が生成した一時ディレクトリ 2 件は削除済み

### 検出力

期待値は引き続き独立した literal です。registry から reason や node 集合を生成する形にはしていません。既存の完全集合 assertion が余分・不足 node を検出し、literal reason と実 inventory の完全比較が文言 drift を検出するため、検出力は低下していません。

### 所見対応表

| 所見 | 対応 | 状態 |
|---|---|---|
| 旧 16 件の独立 golden が現 registry と不一致 | 14 件を削除し、残存 2 件の reason を現 registry から正確に転記 | **partial**。実装と非 pytest 完全一致 probe は成功したが、必須 pytest は child 未起動 |

### 検査結果

`pegasus02` のため、pytest は規律どおり `tools/run_tests.py` 経由で試行しました。

- `orchestrator/tests/test_hold_inventory.py`
  - 結果: 未実走
  - `qstat -Q` が `NQSconnect ... Can't create socket` で失敗
  - runner `rc=16`、`child_started=false`
  - 指定された 2 node を含め、pytest nodeid は一つも開始されていません

- `orchestrator/tests/test_growth_test_holds_contract.py`
  - 結果: 未実走
  - 同じ dispatch infrastructure failure
  - runner `rc=16`、`child_started=false`

補助確認は成功しています。

- `git diff --check`: PASS
- `_expected_inventory()` と `hold_inventory()` の完全一致 probe: PASS、45 holds
- 作業ツリーの変更は既存の段 5 の 3 ファイルと、今回の [test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:48) のみ

## 総括

古い期待表の root cause は修正済みですが、必須 pytest 2 本は Pegasus queue 接続障害により実装済み・未実走です。したがって所見は `closed` ではなく `partial` とします。