## 総括

指定された1件のみを修正しました。[codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:674) では prune 後、root と初期化済み submodule の各 object storeについて `objects/info` 配下を除去します。対象は単一 `commit-graph`、split graph の `commit-graphs/`、`packs`、alternates を含む派生情報です。commit-graph は再生成せず、閉包 manifest に存在有無、検証結果、対象パス、rc、stderr先頭行を記録します。prune済み commitを参照する graph は `git commit-graph verify exited <rc>: ...` で拒否します。

`fsck` 診断は分離しました。非ゼロrcは `git fsck exited <rc>: <stderr先頭行>`、stdoutの到達不能objectは `git object store contains unreachable objects (<件数>)` となり、同じ理由へ畳みません。`9b26b3b`／`08a7e5f2` の不可視性、期待branch一本、focus1/focus2履歴なしの検査は維持しています。

追加したテストnodeは次の5件です。

- `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure`
- `test_object_info_derived_caches_are_removed_for_root_and_submodule`
- `test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested`
- `test_fsck_nonzero_reason_is_not_mislabeled_as_unreachable_objects`
- `test_fsck_unreachable_stdout_reports_count_independently`

ユーザー指示どおり `pytest`、snapshot build、`tools/run_tests.py` 等は実行しておらず、緑は主張しません。許可された `python3 -m py_compile` と `git diff --check` のみ成功しています。docs編集・commitは行わず、既存の別差分も保持しました。