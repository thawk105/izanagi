## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| DW-O16：Lustre で公開不能 | partial | `renameat2` を `os.link` に置換済み。機能テストは基盤障害で未実走 |
| 既存 final の上書き防止 | partial | `FileExistsError` を伝播する実装。既存テストの期待値は維持 |
| link/unlink 間の安全性 | closed | `st_nlink == 2` による読取り拒否と admin flock の関係を docstring に明記 |

## 変更の要約 (関数・行)

- `tools/dev_wave_cleanup.py:963` の `_rename_journal`：同一 dir FD の `os.link(..., follow_symlinks=False)` → 一時名の `os.unlink` に変更。`OSError` は捕捉せず、admin 削除前に停止。
- `import ctypes` を削除。
- `_remove_admin:972` の一時 file fsync と、公開後の親 dir fsync（997行）は維持。
- `_load_admin_recovery:860`、テスト、期待値は変更なし。

波及は内部公開処理のみ。所有外 caller は検索上なし。CLI・journal 形式は不変。M10 anchor は `_mutate:1286` の `_remove_admin(args, common, admin, snapshot)`。

## 実走結果

runner 経由で焦点 suite と consumer 2ファイルを試行しましたが、いずれも次の基盤障害でテスト本体未起動です。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
child_started=false
rc=16
```

構文検査と `git diff --check` は成功。追加テストなし。

## 総括

**実装済み・機能テスト未実走です。** 今回の編集は `tools/dev_wave_cleanup.py` のみ。Lustre 上での動作確認は未了です。
