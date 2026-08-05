実装済み・未実走です。docs 編集・commit は行っていません。

## 対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| R2-01 | `partial` | [`_write_exclusive`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:291) を HEAD と同一の旧実装へ復元。publish の書込み失敗は削除せず path 付き `publish-temporary-write-failed` として記録し、unlink は正常書込み後の rename 失敗時だけに限定。pytest 未実走のため `closed` とはしていない |

追加・更新した検査:

- 既存 file / symlink 衝突時の保存を維持。
- fsync 失敗時に orphan が残り、reason にその path が入ることを固定。
- rename 失敗時に完成済み temp が削除されることを追加。
- 非 publish caller の `rejection.json` が従来どおり書込み失敗ファイルを残すことを追加。
- R2-02 の fsync fixture と nodeid は変更していません。

## `_write_exclusive` の全 caller

| caller | 本 wave 以前との比較 |
|---|---|
| `rejection.json` | 同一。失敗時の helper cleanup なし |
| `candidate.json` / rejected `calibration.json` | 同一。helper の書込み・fsync・例外伝播を復元 |
| `calibration.md` | 同一 |
| `window-probes.json` | 同一 |
| `.publish-*.tmp` | helper は同一。正常 return 後の rename 失敗時だけ cleanup。書込み失敗は意図的に orphan＋構造化 reason |
| `published-self-comparison.json` | 本 wave 新設のため過去 caller はないが、旧 helper semantics をそのまま使用 |
| `publish.json` | 同一 |
| fallback `calibration.json` | 同一 |

HEAD に存在した既存テストの期待値は **0件変更**です。fix2 で新設された R2-01 用期待だけを今回の正本へ更新しました。

静的検査は成功しています。

- `git diff --check`
- 指定4ファイルの `python3 -m py_compile`
- 変更対象は許可された4ファイルのみ

Pegasus ログインノード `pegasus02` のため pytest は未実走です。親の 667 passed / 2 skipped を今回の緑とは主張しません。未実走 nodeid:

- `test_cli_publish_temp_write_failure_removes_partial_file`
- `test_cli_publish_temp_cleanup_failure_is_structured`
- `test_cli_publish_rename_failure_cleans_completed_temp`
- `test_write_rejection_preserves_legacy_exclusive_write_failure_behavior`
- `test_cli_publish_temp_collision_preserves_existing_path[file]`
- `test_cli_publish_temp_collision_preserves_existing_path[symlink]`

## 総括

- `_write_exclusive` を本 wave 前の実装へ完全に戻した。
- helper 内の `stat` / `unlink` と全 caller への cleanup 拡大を除去した。
- publish 書込み失敗は orphan path 付き reason として残す。
- rename 失敗時だけ、従来条件で temp を掃除する。
- 残る risk は、申告された orphan の運用上の蓄積と、歴史的 rename cleanup の path-based unlink。
- R2-02、NR-01、NR-03、scope 外ファイルには触れていない。
- 静的検査済み、pytest は実装済み・未実走。