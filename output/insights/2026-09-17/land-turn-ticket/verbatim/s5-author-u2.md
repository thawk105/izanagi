## 変更前の受理・拒否挙動

現行は `_dry_run_candidates` で全体 prune の候補を読み、候補 directory が存在すれば停止、それ以外は `git worktree prune --expire=now` を実行していました。argv allowlist は dry-run・実 prune の両方を許可していました。

## 実装の要約 (関数・行)

指定の 2 ファイルだけを編集しました。commit は作成していません。

- `tools/dev_wave_cleanup.py:801` `_bind_admin`：common・registry・admin の FD と inode、backpointer、commondir を束縛。
- `:994` `_preflight`：live / stale とも admin 対応の一意性を要求。
- `:893` `_recheck_admin`：binding、lock、wave 不在、HEAD、reflog 到達可能性を再検査。
- `:945` `_remove_admin`：registry FD から相対操作で自 admin だけを撤去。
- `:847` `_load_admin_recovery`：common 配下の wave 別撤去記録から再入。残存 bytes / inode の変化は拒否。
- `:1201` `_mutate`：撤去後の record 不在確認を維持し、途中失敗では branch 削除へ進まない。

`_dry_run_candidates`、`_PRUNE_LINE_RE`、prune の許可形を削除しました。

## M10 の anchor

`tools/dev_wave_cleanup.py` の `_mutate`、**1249〜1252 行**：

```python
phase = "admin-recheck"
snapshot = _recheck_admin(args, common, admin)
phase = "admin-remove"
_remove_admin(args, common, admin, snapshot)
```

全体 prune への置換対象です。argv 禁止側は `_validate_git_argv:208`。変異実走は未了で、KILLED は主張しません。

## 実走した test と結果

**pytest は起動できていません。**

以下を `tools/run_tests.py` 経由で起動しましたが、いずれも子プロセス開始前に rc=16：

- `orchestrator/tests/test_dev_wave_cleanup.py -q`
- `orchestrator/tests/test_pytest_collection_config.py orchestrator/tests/test_plain_runner_coverage.py -q`

診断：

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
child_started=false
```

`py_compile`（編集した両ファイル）と `git diff --check` は終了コード 0 でした。

## 既存 test の期待値変更

- 全体 prune の候補による停止を、外国 wave の live / stale directory・admin・branch 保持へ変更。
- a〜e の再入では prune 呼出しを禁止し、自 admin の不在を確認。
- prune argv を明示禁止。
- phase 注入を `admin-recheck` / `admin-remove` に変更。
- HEAD / gitdir / admin directory 撤去後の再入と、残骸改変時の拒否を追加。
- 一意性、lock、symlink、binding・inode・HEAD・reflog 変更の負例を追加。
- `test_real_occupancy_scan_rejects_live_process_cwd` は改名していません。

## 所有外 caller と波及

静的検索で以下を確認しました。

- `tools/check_docs.py:631` と `docs/dev-wave/operations.md:215`：DW-O28 の CLI literal は変更不要。
- `orchestrator/tests/test_check_docs.py:192,920`：CLI literal・helper 存在の consumer。
- `orchestrator/test_selection_contract.py:41`：test path 契約を維持。
- `test_pytest_collection_config.py:51,389,484`：ファイル名・指定 node 名を維持。
- `test_plain_runner_coverage.py`：既存の `pytest.main` 自走入口を維持。
- `test_branch_rescue_ledger.py:340`：DW-O28 helper への文書参照を維持。

## 未了・赤の内訳

cleanup suite、consumer meta-test、M10 は未実走です。構文検査の成功を機能テストの緑には数えていません。

直接 pytest も PreToolUse hook に拒否されました。拒否理由は「Pegasus ログインノードでは pytest を実行できず、qsub または qlogin が必要」です。迂回はしていません。

## 総括

**実装済み・機能テスト未実走**です。保証対象は「他 wave の admin を削除しない」までで、resolver による他 admin の backpointer 読取りは残しています。
