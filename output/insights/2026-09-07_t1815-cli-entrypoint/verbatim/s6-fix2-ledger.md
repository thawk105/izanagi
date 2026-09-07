## 台帳の更新内容

`nodeid_count`: **19517 → 19521**

追加 entry:

- `...[gate-module]`: `0.34`
- `...[gate-path]`: `0.34`
- `...[prereg-module]`: `0.34`
- `...[prereg-path]`: `0.36`

更新器は `--add-only` 付きで実行し、rc=0、`added=4` でした。

## 既存 entry 不変の確認

更新前に台帳が Git 差分なしであることを確認しました。更新後の `git diff --unified=0` は、上記4 entry の追加と `nodeid_count` の更新だけでした。既存 duration entry の変更は **0件**です。`git diff --check` も rc=0 です。

## 実走結果 (nodeid と rc)

- `orchestrator/tests/test_update_acceptance_duration_ledger.py`
  - 24 passed
  - rc=0
- `orchestrator/tests/test_acceptance_schedule_order.py`
  - 79 passed
  - rc=0
  - `PytestAssertRewriteWarning` 1件

未実走項目はありません。

## 残った懸念・親へ返す判断

台帳更新に関する懸念はありません。commit は作成していません。

変更ファイルは [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/acceptance_duration_ledger.json) のみです。

差分行数: **+5 / -1（計6変更行）**

## 総括

JUnit XML の実測値から新規4 nodeを所要台帳へ追加し、既存 entry の byte-exact 不変と両テスト群の通過を確認しました。