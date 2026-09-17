## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| must-fix 1：link 後停止で再入不能 | partial | 回復処理と回帰テストを実装。基盤障害で未実走 |
| 全 admin file の nlink 検査維持 | closed | `_read_admin_file` の `nlink == 1` 要求は変更なし |
| 偽装 temporary による誤受理 | partial | 別 inode の temporary と nlink 2 の final を拒否するテストを追加。未実走 |

## 変更の要約 (関数・行)

- `tools/dev_wave_cleanup.py:860` `_load_admin_recovery`：final の種類・所有者・権限を確認し、同 dir の自 wave の `<journal>.tmp-*` から、final と `st_dev`・`st_ino` が一致する名前だけを unlink・dir fsync。その後、既存の厳格な読取り検査へ進みます。別 inode の残骸は無視します。
- 同ファイル `:977` `_rename_journal`：停止後の回復処理を docstring に反映。

既存ケースの期待値、CLI、journal 形式は維持。変更 helper の所有外 caller は検索上ありません。consumer の参照名・文書契約も不変です。docs 編集・commit はしていません。

## 追加 test

共通 prefix：`orchestrator/tests/test_dev_wave_cleanup.py::`

- `test_unpublished_admin_journal_reenters[linked]`（1240行）：実際の link 後、unlink 前に停止を注入。再入による cleanup 完了と一時名消失を検査。
- `test_admin_journal_unrelated_temporary_does_not_allow_hardlink`（1297行）：別 inode の temporary があっても、nlink 2 の final を繰り返し rc20 で拒否し、admin・branch を保持することを検査。

## M10 の anchor

`tools/dev_wave_cleanup.py:1301`、`_mutate` の `admin-remove` 段へ移動しています。

```python
_remove_admin(args, common, admin, snapshot)
```

直接 `subprocess.run(["git", "worktree", "prune", "--expire=now"], cwd=args.main_worktree, check=True)` へ置換する位置です。対象 node は `test_cleanup_preserves_foreign_stale_admin[stale]`。変異未実走で、KILLED は未認定です。

## 実走結果

runner 経由で以下を試行しました。

- cleanup 全テスト
- consumer：`test_pytest_collection_config.py`、`test_plain_runner_coverage.py`

いずれも `qstat -Q preflight rc=1`、`child_started=false`、rc16 でテスト本体未起動です。AST 構文検査と `git diff --check` は成功しました。

## 総括

**指定2ファイルに実装済み・機能テスト未実走です。** must-fix 1 の完了判定には、基盤復旧後の焦点テスト実走が残ります。
