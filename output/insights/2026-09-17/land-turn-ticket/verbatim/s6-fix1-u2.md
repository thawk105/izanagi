## 所見対応表 (closed / partial / regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| A1 | partial | 安全確認時点の snapshot を固定し、集合・kind・inode・内容の等価性を要求。実走未了 |
| B1 / A2 | partial | 一時 file の fsync → 上書き禁止 rename → 親 dir fsync を実装。死亡・不完全 final のテスト追加、実走未了 |
| B2 / A3 | closed | 通常 file を長さ＋SHA-256 に変更。意味検査用4種だけ生 bytes を保持。反復読込みの負荷は残存 |
| A8 / B4 | partial | stale admin の bytes・inode 保持検査を確認し、直接 prune の変異 anchor を確定。KILLED 未確認 |
| B3 | partial | 未公開一時 file は無視。放棄 journal 全般の回収運用は今回の範囲外 |

## 変更の要約 (関数・行)

`tools/dev_wave_cleanup.py`：

- `AdminBinding:728`、`_bind_admin:813`：基準 snapshot を保持。state `c` は bind 時点で固定。正規 unlock で除去する `locked` だけ除外。
- `_mutate:1236`：live の基準を安全再確認直後、1276行で固定。
- `_recheck_admin:910`：基準後の変更を `ValueError` で拒否。
- `_admin_content:773`、`_admin_snapshot:780`、`_remove_admin_entries:943`：長さ・SHA-256 比較へ変更。既存 subset 検査も同形式を比較。
- `_load_admin_recovery:861`：空・不完全 JSON の final を理由付き拒否。
- `_rename_journal:964`、`_remove_admin:976`：`renameat2(RENAME_NOREPLACE)` で原子的公開。未対応環境では削除前に停止。

既存テストの期待値、docs、CLI knob は変更していません。commit も作成していません。

## 追加 test と実走結果

共通 prefix：`orchestrator/tests/test_dev_wave_cleanup.py::`

- `test_admin_baseline_rejects_index_change[bytes-a/bytes-b/bytes-c/inode-a/inode-b/inode-c]`
- `test_unpublished_admin_journal_reenters[write/publish]`
- `test_incomplete_final_admin_journal_rejected`
- `test_admin_journal_publication_never_overwrites_final`

追加は計10ケースです。

焦点 suite と consumer の `test_pytest_collection_config.py`、`test_plain_runner_coverage.py` を runner 経由で起動しましたが、いずれも次の基盤障害で未実走です。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
child_started=false
rc=16
```

テスト assertion の赤ではありません。構文検査と `git diff --check` は成功しました。

## M10 の anchor

`tools/dev_wave_cleanup.py:1290`、`_mutate` の `admin-remove` 段：

```python
_remove_admin(args, common, admin, snapshot)
```

この1行を次へ置換します。

```python
subprocess.run(
    ["git", "worktree", "prune", "--expire=now"],
    cwd=args.main_worktree, check=True,
)
```

対象 node は `test_cleanup_preserves_foreign_stale_admin[stale]`。既存テストは他 wave directory を実際に撤去し、admin 全体の bytes・inode 保持を比較しています。静的には foreign admin 消失で失敗する構造です。変異未実走のため **KILLED は未認定**です。

## 波及

- `tools/check_docs.py:631,662`、`docs/dev-wave/operations.md:215`：CLI literal・exact pin は不変。
- `test_check_docs.py:192,920`、`test_branch_rescue_ledger.py:340`：参照先・文書契約は不変。
- `orchestrator/test_selection_contract.py:41`、`test_pytest_collection_config.py:51,389,484`：file path と指定 occupancy node 名を維持。
- `test_plain_runner_coverage.py`：自走入口を維持。
- `tools/*.py` の静的検索では、変更した private helper の所有外 caller はありません。
- journal 内部形式は変更されています。旧 hex 形式の完全 journal の移行互換は追加していません。

## 総括

**指定2ファイルに実装済み・機能テスト未実走です。** 完了判定には焦点 suite、consumer テスト、M10 単独変異走の再実行が必要です。
